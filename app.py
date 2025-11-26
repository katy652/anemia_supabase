import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
import os
import time

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Sistema de Predicción de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar CSS para mejorar la estética y adaptabilidad (SIMULACIÓN MÓVIL/TABLET)
st.markdown("""
<style>
    /* Estilo general para un diseño más moderno */
    .stApp {
        background-color: #f0f2f6;
    }
    /* Estilo de los contenedores (columnas) para añadir sombra y bordes redondeados */
    .st-emotion-cache-1jri6hr, .st-emotion-cache-lgl293 {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 20px;
        background-color: white;
    }
    /* Encabezados y títulos */
    h1, h2, h3 {
        color: #2c3e50;
    }
    /* Mejorar la apariencia en móvil (menos margen interno en contenedores) */
    @media (max-width: 600px) {
        .st-emotion-cache-1jri6hr, .st-emotion-cache-lgl293 {
            padding: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN DIRECTA DE SUPABASE ---
TABLE_NAME = "alertas"
MODEL_PATH = "modelo_columns.joblib"

# TUS CREDENCIALES CORREGIDAS DE SUPABASE - VERIFICA ESTA URL
SUPABASE_URL = "https://kwsuszkblbejvliniggd.supabase.co"  # Tu URL correcta
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2MjU0MzMsImV4cCI6MjA1MDIwMTQzM30.DpWyb9LfXqiZBlmuSWfgIw_O2-LDm2b"

# Lista de regiones (departamentos de Perú) para el SelectBox
PERU_REGIONS = [
    "NO ESPECIFICADO", "AMAZONAS", "ÁNCASH", "APURÍMAC", "AREQUIPA", "AYACUCHO", 
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUÁNUCO", "ICA", "JUNÍN", 
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", 
    "PASCO", "PIURA", "PUNO", "SAN MARTÍN", "TACNA", "TUMBES", "UCAYALI"
]

# Inicializar y cachear el modelo de ML - VERSIÓN SIMPLIFICADA
@st.cache_resource
def load_anemia_model(path):
    """Carga el modelo de Machine Learning usando joblib."""
    if not os.path.exists(path):
        st.error(f"❌ Error: El archivo del modelo '{path}' no fue encontrado.")
        st.info("💡 Asegúrate de que 'modelo_columns.joblib' esté en la misma carpeta que tu aplicación")
        return None
    try:
        model = joblib.load(path)
        
        # Verificación más robusta del modelo
        if hasattr(model, 'predict'):
            st.success("✅ Modelo ML cargado correctamente")
            return model
        elif isinstance(model, (list, tuple)) and len(model) > 0:
            st.warning("⚠️ El archivo contiene una lista/tupla. Buscando modelo dentro...")
            # Buscar algún objeto que tenga método predict
            for item in model:
                if hasattr(item, 'predict'):
                    st.success("✅ Modelo ML encontrado dentro del archivo")
                    return item
        else:
            st.error(f"❌ Error: El objeto cargado no es un modelo ML válido.")
            st.info("💡 El archivo joblib debe contener un modelo de scikit-learn con método 'predict'")
            return None
            
    except Exception as e:
        st.error(f"❌ Error al cargar el modelo joblib: {e}")
        return None

# Inicializar y cachear el cliente de Supabase - CONEXIÓN SIMPLIFICADA
@st.cache_resource(ttl=3600)
def init_supabase() -> Client:
    """
    Inicializa y retorna el cliente de Supabase con conexión directa.
    """
    try:
        # CONEXIÓN DIRECTA CON TUS CREDENCIALES
        url = SUPABASE_URL
        key = SUPABASE_KEY
        
        if not url or not key:
            st.error("❌ Error: Las credenciales de Supabase no están configuradas.")
            return None
            
        st.info(f"🔗 Conectando a Supabase...")
        client = create_client(url, key)
        
        # Verificación simple de conexión
        try:
            # Intentar una operación simple
            response = client.from_(TABLE_NAME).select("count", count="exact").limit(1).execute()
            st.success("✅ Conexión a Supabase establecida correctamente")
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "API key" in error_msg:
                st.error("❌ Error de autenticación: API Key inválida")
                st.info("💡 Verifica tu SUPABASE_KEY en el código")
            elif "404" in error_msg or "not found" in error_msg:
                st.warning("⚠️ Tabla no encontrada, pero conexión establecida")
            else:
                st.warning(f"⚠️ Conexión establecida, pero error al acceder a datos: {e}")
        
        return client
        
    except Exception as e:
        st.error(f"❌ Error fatal al conectar con Supabase: {e}")
        return None

# Carga el modelo y el cliente de Supabase
model = load_anemia_model(MODEL_PATH)
supabase = init_supabase()

# --- FUNCIONES DE INTERACCIÓN CON SUPABASE ---

def insert_data_to_supabase(data_to_insert: dict):
    """Inserta una nueva fila de datos en la tabla de Supabase."""
    if supabase is None:
        st.error("❌ Fallo en la inserción: Cliente Supabase no inicializado.")
        return False
    
    try:
        # Añadir timestamp automáticamente
        data_to_insert['fecha_alerta'] = pd.Timestamp.now().isoformat()
        
        response = supabase.table(TABLE_NAME).insert(data_to_insert).execute()
        
        if response.data:
            get_data_from_supabase.clear() 
            return response.data[0]
        else:
            st.error("❌ Fallo en la inserción: Supabase no devolvió datos.")
            return False
            
    except Exception as e:
        st.error(f"❌ Error al insertar datos: {e}")
        get_data_from_supabase.clear() 
        return False

@st.cache_data(ttl=600)
def get_data_from_supabase():
    """Obtiene y procesa todos los datos de la tabla para visualización."""
    if supabase is None:
        return pd.DataFrame()
        
    try:
        response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).limit(5000).execute()
        data = response.data
        if not data:
            return pd.DataFrame()
             
        df = pd.DataFrame(data)
        
        # Procesamiento de columnas
        if 'fecha_alerta' in df.columns:
            try:
                df['Time'] = pd.to_datetime(df['fecha_alerta'])
            except Exception as e:
                st.warning(f"No se pudo convertir 'fecha_alerta' a datetime: {e}")
                
        # Convertir columnas numéricas
        numeric_cols = ['Hb', 'MCH', 'MCHC', 'MCV', 'age', 'hemoglobina', 'edad']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos desde Supabase: {e}")
        return pd.DataFrame()

# --- LÓGICA DE PREDICCIÓN MEJORADA ---
def make_prediction(Hb, MCH, MCHC, MCV, sex, age, model):
    """
    Usa el modelo de Machine Learning cargado para predecir si hay anemia.
    """
    if model is None:
        return "ERROR_MODELO_NO_CARGADO"
    
    try:
        # Preparar datos de entrada
        sex_code = sex[0].upper() 
        sex_F = 1 if sex_code == "F" else 0 
        sex_M = 1 if sex_code == "M" else 0

        # Crear array de entrada
        X = np.array([[Hb, MCH, MCHC, MCV, age, sex_F, sex_M]]) 
        
        # Realizar predicción
        prediction = model.predict(X)
        prediction_result = str(prediction[0]).lower()
        
        return prediction_result
        
    except Exception as e:
        st.error(f"❌ Error en la predicción: {e}")
        return "ERROR_PREDICCION"

# --- FUNCIONES DE VISUALIZACIÓN (MANTENIDAS) ---
def plot_histogram(df, column, title):
    color_map = {
        "RIESGO INDEFINIDO (¡A DESHABILITAD...)": "red", 
        "REGISTRADO": "green", 
        "ANEMIA": "red", 
        "NORMAL": "green",
        "DESCONOCIDO": "orange"
    }
    color_col = 'riesgo' 
    if color_col not in df.columns: 
        return go.Figure()

    fig = px.histogram(
        df, 
        x=column, 
        color=color_col, 
        marginal="box", 
        nbins=20,
        title=f'Histograma de {title}',
        template="plotly_white",
        color_discrete_map=color_map 
    )
    fig.update_layout(bargap=0.1)
    return fig

def plot_boxplot(df, column, title):
    color_map = {
        "RIESGO INDEFINIDO (¡A DESHABILITAD...)": "red", 
        "REGISTRADO": "green", 
        "ANEMIA": "red", 
        "NORMAL": "green",
        "DESCONOCIDO": "orange"
    }
    color_col = 'riesgo' 
    if color_col not in df.columns: 
        return go.Figure()

    fig = px.box(
        df, 
        y=column, 
        color=color_col, 
        title=f'Diagrama de Caja de {title}',
        template="plotly_white",
        color_discrete_map=color_map
    )
    return fig

# --- VISTA PRINCIPAL DE LA APLICACIÓN ---
st.title("🩸 Sistema de Detección y Predicción de Anemia")
st.markdown("---")

# Estado de las dependencias
st.subheader("Estado de Conexión y Modelo:")

col1, col2 = st.columns(2)
with col1:
    if model:
        st.success("✅ Modelo ML: Cargado")
    else:
        st.error("❌ Modelo ML: Error - Verifica el archivo modelo_columns.joblib")

with col2:
    if supabase:
        st.success("✅ Supabase: Conectado")
    else:
        st.error("❌ Supabase: Error de conexión")

# Columnas principales
col_form, col_data = st.columns([1, 1])

# --- Columna del Formulario ---
with col_form:
    st.header("1. Ingreso de Parámetros")
    st.markdown("Introduce los valores hematológicos y demográficos.")

    with st.form(key='anemia_prediction_form'):
        st.subheader("Datos del Paciente")
        
        nombre_paciente = st.text_input('Nombre y Apellido', placeholder="Ej: Juan Pérez")
        edad_paciente = st.number_input('Edad (años)', min_value=1, max_value=120, value=35, step=1)
        sex_paciente = st.selectbox('Sexo', options=["Femenino", "Masculino"])
        region_paciente = st.selectbox('Región/Ciudad', options=PERU_REGIONS, index=0)

        st.subheader("Valores Hematológicos")
        hb_modelo = st.number_input('Hemoglobina (Hb g/dL)', min_value=0.0, max_value=25.0, value=12.5, step=0.1)
        mch_modelo = st.number_input('MCH (pg)', min_value=15.0, max_value=40.0, value=28.0, step=0.1)
        mchc_modelo = st.number_input('MCHC (g/dL)', min_value=25.0, max_value=40.0, value=33.0, step=0.1)
        mcv_modelo = st.number_input('MCV (fL)', min_value=60.0, max_value=120.0, value=90.0, step=0.1)

        submit_button = st.form_submit_button(label='Obtener Predicción y Guardar', type="primary")

    if submit_button:
        if not model:
            st.error("❌ No se puede realizar la predicción: Modelo no cargado")
        elif not supabase:
            st.error("❌ No se pueden guardar datos: Conexión a Supabase fallida")
        else:
            # Realizar predicción
            prediction_result = make_prediction(hb_modelo, mch_modelo, mchc_modelo, mcv_modelo, sex_paciente, edad_paciente, model)
            
            if "error" not in prediction_result.lower():
                # Mapear resultado
                if prediction_result == "anemia":
                    riesgo_supa = "RIESGO INDEFINIDO (¡A DESHABILITAD...)" 
                    sugerencia_supa = "¡Alerta! Posible estado de anemia. Consulta con un médico especialista."
                elif prediction_result == "normal":
                    riesgo_supa = "REGISTRADO" 
                    sugerencia_supa = "Resultados normales. Mantener dieta balanceada."
                else:
                    riesgo_supa = "DESCONOCIDO" 
                    sugerencia_supa = "Resultado atípico. Revisar datos ingresados."
                    
                # Preparar datos para Supabase
                new_record = {
                    "nombre_apellido": nombre_paciente,
                    "edad": edad_paciente,
                    "hemoglobina": hb_modelo, 
                    "riesgo": riesgo_supa,
                    "sugerencia": sugerencia_supa,
                    "region": region_paciente,
                    "Hb": hb_modelo, "MCH": mch_modelo, "MCHC": mchc_modelo, "MCV": mcv_modelo,
                    "sex": sex_paciente[0].upper(), 
                    "prediction": prediction_result, 
                }
                
                # Insertar en Supabase
                inserted_data = insert_data_to_supabase(new_record)
                
                if inserted_data:
                    st.success("✅ ¡Datos guardados en Supabase con éxito!")
                    st.markdown("### Resultado de la Predicción:")
                    if prediction_result == "anemia":
                        st.error("**ANEMIA** 🛑")
                        st.warning(sugerencia_supa)
                    elif prediction_result == "normal":
                        st.success("**NORMAL** ✅")
                        st.info(sugerencia_supa)
                else:
                    st.error("❌ Error al guardar en Supabase")

# --- Columna de Visualización de Datos ---
with col_data:
    st.header("2. Análisis de Registros Históricos")
    
    if st.button("🔄 Actualizar Datos", help="Recargar datos desde Supabase"):
        get_data_from_supabase.clear()
        st.rerun()

    df_data = get_data_from_supabase()

    if not df_data.empty:
        st.markdown(f"**Total de registros:** `{len(df_data)}`")
        
        tab_data, tab_stats = st.tabs(["📊 Datos", "📈 Gráficos"])
        
        with tab_data:
            st.subheader("Registros Históricos")
            display_cols = ['Time', 'nombre_apellido', 'edad', 'hemoglobina', 'riesgo', 'region']
            available_cols = [col for col in display_cols if col in df_data.columns]
            if available_cols:
                st.dataframe(df_data[available_cols], use_container_width=True)
            
            if 'riesgo' in df_data.columns:
                st.subheader("Distribución de Resultados")
                counts = df_data['riesgo'].value_counts().reset_index()
                counts.columns = ['Resultado', 'Cantidad']
                
                fig_pie = px.pie(
                    counts, 
                    names='Resultado', 
                    values='Cantidad',
                    title='Distribución de Resultados'
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        with tab_stats:
            st.subheader("Análisis de Variables")
            
            hematology_cols = ['hemoglobina', 'MCH', 'MCHC', 'MCV']
            
            for col_name in hematology_cols:
                if col_name in df_data.columns and 'riesgo' in df_data.columns:
                    st.markdown(f"**{col_name}**")
                    fig_hist = plot_histogram(df_data, col_name, col_name)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
    else:
        st.info("No hay datos históricos para mostrar. Ingresa el primer registro usando el formulario.")
