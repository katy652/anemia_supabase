import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import psycopg2

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Alertas de Hemoglobina",
    page_icon="🩺",
    layout="wide"
)

# Conexión a la base de datos
@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

# Funciones de base de datos
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def get_pacientes():
    return run_query("SELECT * FROM alertas_hemoglobina;")

def insert_paciente(datos):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO alertas_hemoglobina (
                dni, nombre_apellido, edad_meses, peso_kg, talla_cm, genero, telefono, estado_paciente,
                region, departamento, altitud_msnm, nivel_educativo, acceso_agua_potable, tiene_servicio_salud,
                hemoglobina_dl1, en_seguimiento, consume_hierro, tipo_suplemento_hierro, frecuencia_suplemento, 
                antecedentes_anemia, enfermedades_cronicas, riesgo, estado_alerta, sugerencias
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, datos)
        conn.commit()

# Título principal
st.title("🩺 Sistema de Monitoreo de Hemoglobina en Niños")
st.markdown("---")

# Crear pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard Principal", 
    "👥 Registrar Paciente", 
    "🔍 Casos en Seguimiento", 
    "📈 Estadísticas", 
    "👁️ Ver Todos los Pacientes"
])

# Pestaña 1: Dashboard Principal
with tab1:
    st.header("📊 Resumen General")
    
    try:
        pacientes = get_pacientes()
        df = pd.DataFrame(pacientes, columns=[
            'dni', 'nombre_apellido', 'edad_meses', 'peso_kg', 'talla_cm', 'genero', 'telefono', 'estado_paciente',
            'region', 'departamento', 'altitud_msnm', 'nivel_educativo', 'acceso_agua_potable', 'tiene_servicio_salud',
            'hemoglobina_dl1', 'en_seguimiento', 'consume_hierro', 'tipo_suplemento_hierro', 'frecuencia_suplemento',
            'antecedentes_anemia', 'enfermedades_cronicas', 'riesgo', 'fecha_alerta', 'estado_alerta', 'sugerencias'
        ])
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pacientes", len(df))
        with col2:
            st.metric("Alto Riesgo", len(df[df['riesgo'].str.contains('ALTO')]))
        with col3:
            st.metric("En Seguimiento", len(df[df['en_seguimiento'] == True]))
        with col4:
            st.metric("Hemoglobina Promedio", f"{df['hemoglobina_dl1'].mean():.1f} g/dL")
        
        # Gráfico de riesgos
        fig_riesgo = px.pie(df, names='riesgo', title='Distribución por Nivel de Riesgo')
        st.plotly_chart(fig_riesgo, use_container_width=True)
        
        # Gráfico de hemoglobina por edad
        fig_hemo = px.scatter(df, x='edad_meses', y='hemoglobina_dl1', color='riesgo',
                             title='Hemoglobina vs Edad', size='peso_kg', hover_data=['nombre_apellido'])
        st.plotly_chart(fig_hemo, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")

# Pestaña 2: Registrar Nuevo Paciente
with tab2:
    st.header("👥 Registrar Nuevo Paciente")
    
    with st.form("registro_paciente"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Datos Personales")
            dni = st.text_input("DNI*")
            nombre_apellido = st.text_input("Nombre Completo*")
            edad_meses = st.number_input("Edad (meses)*", min_value=0, max_value=120)
            peso_kg = st.number_input("Peso (kg)", min_value=0.0, format="%.2f")
            talla_cm = st.number_input("Talla (cm)", min_value=0.0, format="%.2f")
            genero = st.selectbox("Género", ["M", "F", "Otro"])
            telefono = st.text_input("Teléfono")
            estado_paciente = st.selectbox("Estado del Paciente", ["Activo", "Inactivo", "Dado de alta"])
        
        with col2:
            st.subheader("🌍 Factores Demográficos")
            region = st.selectbox("Región*", ["LIMA", "AREQUIPA", "CUSCO", "PUNO", "JUNIN", "ANCASH", "LA LIBERTAD"])
            departamento = st.text_input("Departamento")
            altitud_msnm = st.number_input("Altitud (msnm)", min_value=0)
            
            st.subheader("💰 Factores Socioeconómicos")
            nivel_educativo = st.selectbox("Nivel Educativo", ["Sin educación", "Primaria", "Secundaria", "Superior"])
            acceso_agua_potable = st.checkbox("Acceso a agua potable")
            tiene_servicio_salud = st.checkbox("Tiene servicio de salud")
        
        st.subheader("🏥 Factores Clínicos")
        col3, col4 = st.columns(2)
        
        with col3:
            hemoglobina_dl1 = st.number_input("Hemoglobina (g/dL)*", min_value=0.0, format="%.1f")
            en_seguimiento = st.checkbox("En seguimiento")
            consume_hierro = st.checkbox("Consume suplemento de hierro")
            tipo_suplemento_hierro = st.text_input("Tipo de suplemento de hierro")
        
        with col4:
            frecuencia_suplemento = st.selectbox("Frecuencia de suplemento", 
                                               ["Diario", "3 veces por semana", "Semanal", "Otra"])
            antecedentes_anemia = st.checkbox("Antecedentes de anemia")
            enfermedades_cronicas = st.text_area("Enfermedades crónicas")
            
            # Calcular riesgo automáticamente
            if hemoglobina_dl1 < 10:
                riesgo = "ALTO RIESGO (Alerta Clínica - ALTA)"
                estado_alerta = "URGENTE"
                sugerencias = "Suplemento de hierro inmediato y control médico urgente"
            elif hemoglobina_dl1 < 11.5:
                riesgo = "ALTO RIESGO (Alerta Clínica - MODERADA)"
                estado_alerta = "PRIORITARIO"
                sugerencias = "Dieta rica en hierro y evaluación médica"
            else:
                riesgo = "RIESGO MODERADO"
                estado_alerta = "EN SEGUIMIENTO"
                sugerencias = "Seguimiento rutinario"
        
        # Mostrar sugerencias automáticas
        st.info(f"**Riesgo calculado:** {riesgo} - {estado_alerta}")
        st.warning(f"**Sugerencias:** {sugerencias}")
        
        submitted = st.form_submit_button("💾 Guardar Paciente")
        if submitted:
            if dni and nombre_apellido and edad_meses and hemoglobina_dl1 and region:
                datos = (
                    dni, nombre_apellido, edad_meses, peso_kg, talla_cm, genero, telefono, estado_paciente,
                    region, departamento, altitud_msnm, nivel_educativo, acceso_agua_potable, tiene_servicio_salud,
                    hemoglobina_dl1, en_seguimiento, consume_hierro, tipo_suplemento_hierro, frecuencia_suplemento,
                    antecedentes_anemia, enfermedades_cronicas, riesgo, estado_alerta, sugerencias
                )
                insert_paciente(datos)
                st.success("✅ Paciente registrado exitosamente!")
                st.rerun()
            else:
                st.error("❌ Por favor complete todos los campos obligatorios (*)")

# Pestaña 3: Casos en Seguimiento
with tab3:
    st.header("🔍 Casos en Seguimiento")
    
    try:
        pacientes_seguimiento = run_query("SELECT * FROM alertas_hemoglobina WHERE en_seguimiento = true;")
        df_seguimiento = pd.DataFrame(pacientes_seguimiento, columns=[
            'dni', 'nombre_apellido', 'edad_meses', 'peso_kg', 'talla_cm', 'genero', 'telefono', 'estado_paciente',
            'region', 'departamento', 'altitud_msnm', 'nivel_educativo', 'acceso_agua_potable', 'tiene_servicio_salud',
            'hemoglobina_dl1', 'en_seguimiento', 'consume_hierro', 'tipo_suplemento_hierro', 'frecuencia_suplemento',
            'antecedentes_anemia', 'enfermedades_cronicas', 'riesgo', 'fecha_alerta', 'estado_alerta', 'sugerencias'
        ])
        
        if len(df_seguimiento) > 0:
            st.metric("Pacientes en Seguimiento", len(df_seguimiento))
            
            # Mostrar tabla de seguimiento
            st.dataframe(df_seguimiento[['nombre_apellido', 'edad_meses', 'hemoglobina_dl1', 'riesgo', 'consume_hierro', 'sugerencias']])
            
            # Gráfico de progreso
            fig_progreso = px.line(df_seguimiento, x='nombre_apellido', y='hemoglobina_dl1', 
                                 title='Niveles de Hemoglobina - Pacientes en Seguimiento')
            st.plotly_chart(fig_progreso, use_container_width=True)
        else:
            st.info("No hay pacientes en seguimiento actualmente.")
            
    except Exception as e:
        st.error(f"Error al cargar casos en seguimiento: {e}")

# Pestaña 4: Estadísticas
with tab4:
    st.header("📈 Estadísticas y Reportes")
    
    try:
        df = pd.DataFrame(get_pacientes(), columns=[
            'dni', 'nombre_apellido', 'edad_meses', 'peso_kg', 'talla_cm', 'genero', 'telefono', 'estado_paciente',
            'region', 'departamento', 'altitud_msnm', 'nivel_educativo', 'acceso_agua_potable', 'tiene_servicio_salud',
            'hemoglobina_dl1', 'en_seguimiento', 'consume_hierro', 'tipo_suplemento_hierro', 'frecuencia_suplemento',
            'antecedentes_anemia', 'enfermedades_cronicas', 'riesgo', 'fecha_alerta', 'estado_alerta', 'sugerencias'
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución por región
            fig_region = px.bar(df['region'].value_counts(), title='Pacientes por Región')
            st.plotly_chart(fig_region, use_container_width=True)
            
            # Consumo de hierro
            fig_hierro = px.pie(df, names='consume_hierro', title='Distribución de Consumo de Hierro')
            st.plotly_chart(fig_hierro, use_container_width=True)
        
        with col2:
            # Hemoglobina por género
            fig_genero = px.box(df, x='genero', y='hemoglobina_dl1', title='Hemoglobina por Género')
            st.plotly_chart(fig_genero, use_container_width=True)
            
            # Acceso a servicios
            fig_servicios = px.pie(df, names='tiene_servicio_salud', title='Acceso a Servicios de Salud')
            st.plotly_chart(fig_servicios, use_container_width=True)
        
        # Reporte detallado
        st.subheader("📋 Reporte Detallado")
        st.dataframe(df.describe())
        
    except Exception as e:
        st.error(f"Error al generar estadísticas: {e}")

# Pestaña 5: Ver Todos los Pacientes
with tab5:
    st.header("👁️ Todos los Pacientes Registrados")
    
    try:
        pacientes = get_pacientes()
        df = pd.DataFrame(pacientes, columns=[
            'dni', 'nombre_apellido', 'edad_meses', 'peso_kg', 'talla_cm', 'genero', 'telefono', 'estado_paciente',
            'region', 'departamento', 'altitud_msnm', 'nivel_educativo', 'acceso_agua_potable', 'tiene_servicio_salud',
            'hemoglobina_dl1', 'en_seguimiento', 'consume_hierro', 'tipo_suplemento_hierro', 'frecuencia_suplemento',
            'antecedentes_anemia', 'enfermedades_cronicas', 'riesgo', 'fecha_alerta', 'estado_alerta', 'sugerencias'
        ])
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_riesgo = st.selectbox("Filtrar por riesgo", ["Todos"] + list(df['riesgo'].unique()))
        with col2:
            filtro_region = st.selectbox("Filtrar por región", ["Todos"] + list(df['region'].unique()))
        with col3:
            filtro_seguimiento = st.selectbox("Filtrar por seguimiento", ["Todos", "En seguimiento", "Sin seguimiento"])
        
        # Aplicar filtros
        df_filtrado = df.copy()
        if filtro_riesgo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['riesgo'] == filtro_riesgo]
        if filtro_region != "Todos":
            df_filtrado = df_filtrado[df_filtrado['region'] == filtro_region]
        if filtro_seguimiento == "En seguimiento":
            df_filtrado = df_filtrado[df_filtrado['en_seguimiento'] == True]
        elif filtro_seguimiento == "Sin seguimiento":
            df_filtrado = df_filtrado[df_filtrado['en_seguimiento'] == False]
        
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Botón de exportación
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Exportar a CSV",
            data=csv,
            file_name=f"pacientes_hemoglobina_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Error al cargar pacientes: {e}")

# Footer
st.markdown("---")
st.markdown("**Sistema de Alertas de Hemoglobina** 🩺 | Desarrollado para el monitoreo de anemia infantil")
