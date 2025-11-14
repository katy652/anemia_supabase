import streamlit as st
from supabase import create_client, Client
import pandas as pd
import random
import uuid

# --- CONFIGURACIÓN Y CONEXIÓN A SUPABASE ---
@st.cache_resource(ttl=3600)
def init_supabase() -> Client | None:
    """Inicializa y retorna el cliente de Supabase."""
    try:
        # Lee las credenciales del archivo .streamlit/secrets.toml
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except KeyError:
        # Esto se mostrará si el archivo secrets.toml no está configurado
        st.error("Error: Credenciales de Supabase (url/key) no encontradas.")
        st.info("Por favor, crea un archivo .streamlit/secrets.toml con tu URL y Clave de Supabase.")
        return None
    except Exception as e:
        st.error(f"Error al inicializar Supabase: {e}")
        return None

# Conexión Global
supabase = init_supabase()

# Definición de Tablas
TABLE_PACIENTES = "pacientes"
TABLE_ALERTAS = "alertas_ia"

# --- FUNCIONES DE BASE DE DATOS (CRUD) ---

def registrar_paciente_y_alerta(datos_paciente):
    """
    1. Inserta el paciente.
    2. Simula la predicción IA.
    3. Genera una alerta si el riesgo es alto/medio.
    """
    if not supabase: 
        st.error("Error de conexión: No se puede registrar sin Supabase.")
        return False

    # 1. Insertar el paciente
    try:
        response_paciente = supabase.table(TABLE_PACIENTES).insert(datos_paciente).select("id").execute()
        paciente_id = response_paciente.data[0]['id']
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
             st.error(f"❌ Error: Ya existe un paciente con el DNI {datos_paciente['dni']}. No se puede registrar.")
        else:
             st.error(f"❌ Error al registrar paciente: {e}")
        return False
        
    # 2. Mock de Predicción IA (Simulación simple)
    # ESTA ES LA LÓGICA QUE REEMPLAZAREMOS DESPUÉS CON TU MODELO JOBLIB
    hemoglobina = datos_paciente['hemoglobina']
    if hemoglobina < 11.0: # Simulación de umbral de anemia
        riesgo = random.choices(['ALTO', 'MEDIO'], weights=[0.7, 0.3], k=1)[0]
        probabilidad = round(random.uniform(0.75, 0.99), 2)
    else:
        riesgo = 'BAJO'
        probabilidad = round(random.uniform(0.01, 0.50), 2)

    # 3. Insertar Alerta si el riesgo no es BAJO
    if riesgo in ('ALTO', 'MEDIO'):
        alerta_data = {
            "paciente_id": paciente_id,
            "riesgo_anemia_predicho": riesgo,
            "probabilidad_prediccion": probabilidad,
            "estado_seguimiento": 'PENDIENTE'
        }
        try:
            supabase.table(TABLE_ALERTAS).insert(alerta_data).execute()
            st.toast(f"🚨 ¡ALERTA GENERADA! Riesgo {riesgo} ({probabilidad*100:.0f}%)", icon="🚨")
        except Exception as e:
            st.warning(f"⚠️ Paciente registrado, pero falló la alerta: {e}")
            return False

    return True

@st.cache_data(ttl=10)
def fetch_alertas():
    """Obtiene todas las alertas activas, unidas con la información del paciente."""
    if not supabase: return pd.DataFrame()
    try:
        # Consulta que une la tabla alertas_ia con la información de pacientes (paciente_id)
        # El * en paciente_id(*) trae todas las columnas de la tabla 'pacientes'
        response = supabase.table(TABLE_ALERTAS).select("*, paciente_id(*)").order("fecha_alerta", desc=True).execute()
        
        df_alertas = pd.DataFrame(response.data)
        
        if 'paciente_id' in df_alertas.columns and not df_alertas.empty:
            # Aplanar la información del paciente (json anidado)
            df_pacientes = df_alertas['paciente_id'].apply(pd.Series).rename(
                columns={'dni': 'DNI', 'nombre_apellido': 'Paciente', 'hemoglobina': 'HB'}
            )
            # Concatenar y seleccionar columnas para la vista de monitoreo
            df_alertas = pd.concat([df_alertas.drop(columns=['paciente_id']), df_pacientes], axis=1)
            
            # Formateo de fecha
            df_alertas['Fecha Alerta'] = pd.to_datetime(df_alertas['fecha_alerta']).dt.strftime('%d-%m-%Y %H:%M')
            
            return df_alertas[[
                'DNI', 'Paciente', 'HB', 'riesgo_anemia_predicho', 
                'probabilidad_prediccion', 'estado_seguimiento', 'Fecha Alerta', 'id'
            ]]
            
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al cargar alertas: {e}")
        return pd.DataFrame()
        
def actualizar_estado_alerta(alerta_id, nuevo_estado, comentarios):
    """Actualiza el estado de seguimiento y comentarios de una alerta específica."""
    if not supabase: return False
    try:
        supabase.table(TABLE_ALERTAS).update({
            "estado_seguimiento": nuevo_estado,
            "comentarios_seguimiento": comentarios
        }).eq("id", alerta_id).execute()
        st.toast(f"Estado de alerta actualizado a {nuevo_estado}", icon="🔄")
        fetch_alertas.clear() # Limpiar caché para forzar la recarga
        return True
    except Exception as e:
        st.error(f"Error al actualizar estado: {e}")
        return False

# --- VISTAS DE LA APLICACIÓN ---

def vista_registro():
    """Vista para el registro de nuevos pacientes y la simulación del diagnóstico."""
    st.title("Sistema de Alerta IA")
    st.subheader("Informe Personalizado y Registro de Pacientes")
    st.markdown("---")

    with st.form("registro_paciente_form", clear_on_submit=True):
        st.markdown("### 0. Datos de Identificación y Contacto")
        col1, col2, col3 = st.columns(3)
        with col1:
            dni = st.text_input("DNI del Paciente", max_chars=8, help="Solo 8 dígitos y único", key="dni_input")
        with col2:
            nombre_apellido = st.text_input("Nombre y Apellido", key="nombre_input")
        with col3:
            celular_contacto = st.text_input("Celular de Contacto", key="celular_input")

        st.markdown("---")
        st.markdown("### 1. Factores Clínicos y Demográficos Clave")
        col4, col5, col6, col7 = st.columns(4)
        with col4:
            hemoglobina = st.number_input("Hemoglobina (g/dL)", min_value=0.0, max_value=20.0, value=10.5, step=0.1, key="hb_input")
        with col5:
            edad = st.slider("Edad (meses)", min_value=0, max_value=72, value=30, key="edad_input")
        with col6:
            region = st.selectbox("Región", ["LIMA", "JUNÍN", "PUNO", "LORETO", "OTRA REGIÓN"], key="region_input")
        with col7:
            altitud_asignada = st.number_input("Altitud Asignada (msnm)", min_value=0, value=150, key="altitud_input")

        st.markdown("---")
        st.markdown("### 2. Factores Socioeconómicos y Contextuales")
        col8, col9, col10 = st.columns(3)
        with col8:
            clima_predominante = st.selectbox("Clima Predominante", ["CÁLIDO/SECO", "TEMPLADO", "FRÍO"], key="clima_input")
            nivel_educacion_madre = st.selectbox("Nivel Educ. Madre", ["Secundaria", "Primaria", "Superior", "Sin Estudios"], key="educ_madre_input")
        with col9:
            num_hijos_hogar = st.selectbox("Nro. de Hijos en el Hogar", list(range(1, 11)), key="hijos_input")
            area_residencia = st.selectbox("Área de Residencia", ["Urbana", "Rural"], key="residencia_input")
        with col10:
            ingreso_familiar = st.number_input("Ingreso Familiar (Soles/Mes)", min_value=0.0, value=1500.0, step=100.0, key="ingreso_input")
            sexo = st.selectbox("Sexo", ["Femenino", "Masculino"], key="sexo_input")
            
        st.markdown("---")
        st.markdown("### 3. Acceso a Programas y Servicios")
        col13, col14, col15, col16 = st.columns(4)
        with col13: programa_cuna_mas = st.radio("Programa Cuna Más", ["Sí", "No"], horizontal=True, key="cuna_input")
        with col14: programa_juntos = st.radio("Programa Juntos", ["Sí", "No"], horizontal=True, key="juntos_input")
        with col15: programa_vaso_leche = st.radio("Programa Vaso de Leche", ["Sí", "No"], horizontal=True, key="vaso_input")
        with col16: recibe_suplemento_hierro = st.radio("Recibe Suplemento de Hierro", ["Sí", "No"], horizontal=True, key="hierro_input")
            
        st.markdown("---")
        
        submitted = st.form_submit_button("GENERAR INFORME Y REGISTRAR CASO", type="primary")

        if submitted:
            if not dni.isdigit() or len(dni) != 8:
                st.error("El DNI debe contener exactamente 8 dígitos numéricos.")
            elif not nombre_apellido or not dni:
                st.error("Los campos DNI y Nombre son obligatorios.")
            elif supabase is None:
                st.error("La base de datos no está conectada. No se puede registrar.")
            else:
                datos = {
                    "dni": dni, "nombre_apellido": nombre_apellido, "celular_contacto": celular_contacto,
                    "hemoglobina": hemoglobina, "edad": edad, "region": region, "altitud_asignada": altitud_asignada,
                    "clima_predominante": clima_predominante, "nivel_educacion_madre": nivel_educacion_madre,
                    "num_hijos_hogar": num_hijos_hogar, "ingreso_familiar": ingreso_familiar,
                    "area_residencia": area_residencia, "sexo": sexo,
                    "programa_cuna_mas": programa_cuna_mas, "programa_juntos": programa_juntos,
                    "programa_vaso_leche": programa_vaso_leche, "recibe_suplemento_hierro": recibe_suplemento_hierro
                }
                
                if registrar_paciente_y_alerta(datos):
                    st.success(f"Paciente {nombre_apellido} registrado y diagnóstico completado.")


def vista_monitoreo():
    """Vista para la gestión de alertas y cambio de estado de seguimiento."""
    st.title("Monitoreo y Gestión de Alertas")
    st.subheader("Casos de Monitoreo Activo (Pendientes y En Seguimiento)")
    st.markdown("---")
    
    df_alertas = fetch_alertas()

    if df_alertas.empty:
        st.info("No hay alertas activas en la base de datos.")
        return

    df_monitoreo = df_alertas[df_alertas['estado_seguimiento'].isin(['PENDIENTE', 'EN SEGUIMIENTO'])].copy()

    if df_monitoreo.empty:
        st.info("No hay alertas PENDIENTES o EN SEGUIMIENTO.")
        return

    st.dataframe(
        df_monitoreo.drop(columns=['id', 'probabilidad_prediccion']), 
        use_container_width=True,
        hide_index=True,
        column_order=('Fecha Alerta', 'DNI', 'Paciente', 'HB', 'riesgo_anemia_predicho', 'estado_seguimiento')
    )
    
    st.markdown("---")
    st.subheader("Actualizar Estado de Alerta")

    with st.form("actualizar_alerta_form"):
        col_id, col_estado = st.columns([1, 1])
        
        # Crear un diccionario para mapear la selección del usuario al ID de la alerta (uuid)
        opciones_alerta = {
            f"{row['DNI']} - {row['Paciente']} (Riesgo: {row['riesgo_anemia_predicho']})": row['id']
            for index, row in df_monitoreo.iterrows()
        }
        
        alerta_seleccionada_key = col_id.selectbox(
            "Selecciona la Alerta a Actualizar", 
            list(opciones_alerta.keys())
        )
        
        nuevo_estado = col_estado.selectbox(
            "Nuevo Estado de Seguimiento", 
            ["EN SEGUIMIENTO", "CERRADO"],
            index=0 
        )
        
        comentarios = st.text_area("Comentarios sobre el Seguimiento (Opcional)")
        
        submitted = st.form_submit_button("Actualizar Alerta", type="secondary")
        
        if submitted and alerta_seleccionada_key:
            alerta_id_a_actualizar = opciones_alerta[alerta_seleccionada_key]
            if actualizar_estado_alerta(alerta_id_a_actualizar, nuevo_estado, comentarios):
                st.rerun() # Recargar la data para ver el cambio

# --- NAVEGACIÓN PRINCIPAL ---

st.set_page_config(
    page_title="Sistema de Alerta IA", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
st.sidebar.title("Sistema de Alerta IA")
st.sidebar.markdown("### Navegación")
page = st.sidebar.radio(
    "Selecciona Módulo",
    ["Predicción y Reporte", "Monitoreo de Alertas"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Estado del Sistema")
if supabase:
    st.sidebar.markdown("✅ **Conexión DB Activa** (Supabase)")
else:
    st.sidebar.markdown("❌ **Conexión DB Fallida**")
st.sidebar.markdown("✅ **Modelo IA Cargado (Mock)**") # (Simulado por ahora)


# Renderizar la vista seleccionada
if page == "Predicción y Reporte":
    vista_registro()
elif page == "Monitoreo de Alertas":
    vista_monitoreo()
