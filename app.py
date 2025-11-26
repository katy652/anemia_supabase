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

# Aplicar CSS para mejorar la estética
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .st-emotion-cache-1jri6hr, .st-emotion-cache-lgl293 {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 20px;
        background-color: white;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    @media (max-width: 600px) {
        .st-emotion-cache-1jri6hr, .st-emotion-cache-lgl293 {
            padding: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Configuración de Supabase - TU URL ESPECÍFICA
SUPABASE_URL = "https://kwsuszkblbejvliniggd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2MjU0MzMsImV4cCI6MjA1MDIwMTQzM30.DpWyb9LfXqiZBlmuSWfgIw_O2-LDm2b"  

TABLE_NAME = "alertas"
MODEL_PATH = "modelo_columns.joblib"

# Lista de regiones de Perú
PERU_REGIONS = [
    "NO ESPECIFICADO", "AMAZONAS", "ÁNCASH", "APURÍMAC", "AREQUIPA", "AYACUCHO", 
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUÁNUCO", "ICA", "JUNÍN", 
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", 
    "PASCO", "PIURA", "PUNO", "SAN MARTÍN", "TACNA", "TUMBES", "UCAYALI"
]

# Cargar modelo de ML
@st.cache_resource
def load_anemia_model(path):
    """Carga el modelo de Machine Learning usando joblib."""
    if not os.path.exists(path):
        st.error(f"❌ Error: El archivo del modelo '{path}' no fue encontrado.")
        return None
    try:
        model = joblib.load(path)
        if not hasattr(model, 'predict'):
            st.error(f"❌ Error: El objeto cargado no parece ser un modelo ML válido.")
            return None
        return model
    except Exception as e:
        st.error(f"❌ Error al cargar el modelo joblib: {e}")
        return None

# Inicializar cliente de Supabase - VERSIÓN SIMPLIFICADA
@st.cache_resource(ttl=3600)
def init_supabase() -> Client:
    """
    Inicializa y retorna el cliente de Supabase con tus credenciales específicas.
    """
    try:
        # Usar las credenciales directamente definidas
        url = SUPABASE_URL
        key = SUPABASE_KEY

        if not url or not key:
            st.error("❌ Error: Las credenciales de Supabase no están configuradas.")
            return None
            
        st.info(f"🔗 Conectando a: {url}")
        client = create_client(url, key)
        
        # Test de conexión
        try:
            test_response = client.table(TABLE_NAME).select("count", count="exact").limit(1).execute()
            st.success("✅ Conexión a Supabase establecida correctamente")
        except Exception as e:
            st.warning(f"⚠️ Conexión establecida, pero error al acceder a la tabla: {e}")
            
        return client
        
    except Exception as e:
        st.error(f"❌ Error fatal al inicializar Supabase: {e}")
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
        data_to_insert["fecha_alerta"] = pd.Timestamp.now().isoformat()
        
        response = supabase.table(TABLE_NAME).insert(data_to_insert).execute()
        
        if response.data:
            get_data_from_supabase.clear() 
            st.success("✅ Datos insertados correctamente")
            return response.data[0]
        else:
            st.error("❌ Fallo en la inserción: Supabase no devolvió datos.")
            if hasattr(response, 'error') and response.error:
                st.error(f"Error detallado: {response.error}")
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
                cols = ['Time'] + [col for col in df.columns if col != 'Time']
                df = df[cols]
            except Exception as e:
                st.warning(f"No se pudo convertir 'fecha_alerta' a datetime: {e}")
                
        # Convertir columnas numéricas
        numeric_cols = ['Hb', 'MCH', 'MCHC', 'MCV', 'age', 'hemoglobina', 'edad']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
        
    except Exception as e:
        st.error(f"Error al cargar datos desde Supabase: {e}")
        return pd.DataFrame()

# --- LÓGICA DE PREDICCIÓN ---
def make_prediction(Hb, MCH, MCHC, MCV, sex, age, model):
    """Usa el modelo de ML para predecir si hay anemia."""
    
    if model is None or not hasattr(model, 'predict'):
        return "ERROR_MODELO_NO_CARGADO"
    
    sex_code = sex[0].upper() 
    sex_F = 1 if sex_code == "F" else 0 
    sex_M = 1 if sex_code == "M" else 0

    X = np.array([[Hb, MCH, MCHC, MCV, age, sex_F, sex_M]]) 
    
    try:
        prediction_result = str(model.predict(X)[0]).lower() 
        return prediction_result
    except Exception as e:
        st.error(f"❌ Error al ejecutar la predicción: {e}")
        return "ERROR_PREDICCION"

# --- FUNCIONES DE VISUALIZACIÓN ---
def plot_histogram(df, column, title):
    """Genera un histograma para una columna numérica."""
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
    """Genera un diagrama de caja para una columna numérica."""
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
dependency_status = []
if model:
    dependency_status.append(("Modelo ML", "✅ Cargado"))
else:
    dependency_status.append(("Modelo ML", "❌ Error"))

if supabase:
    dependency_status.append(("Supabase", "✅ Conectado"))
else:
    dependency_status.append(("Supabase", "❌ Error"))

st.subheader("Estado de Conexión y Modelo:")
st.table(pd.DataFrame(dependency_status, columns=['Componente', 'Estado']))

# Columnas principales
col_form, col_data = st.columns([1, 1])

# --- Columna del Formulario ---
with col_form:
    st.header("1. Ingreso de Parámetros")
    st.markdown("Introduce los valores hematológicos y demográficos.")

    with st.form(key='anemia_prediction_form'):
        st.subheader("Datos de la Muestra")
        
        nombre_paciente = st.text_input('Nombre y Apellido', help="Necesario para el registro")
        edad_paciente = st.number_input('Edad (años)', min_value=1, max_value=120, value=35, step=1)
        sex_paciente = st.selectbox('Sexo', options=["Femenino", "Masculino"])
        region_paciente = st.selectbox('Región/Ciudad', options=PERU_REGIONS, index=0)

        st.subheader("Valores Hematológicos para Predicción")
        hb_modelo = st.number_input('Hemoglobina (Hb g/dL)', min_value=0.0, max_value=25.0, value=9.0, step=0.1)
        mch_modelo = st.number_input('MCH (pg)', min_value=15.0, max_value=40.0, value=28.0, step=0.1)
        mchc_modelo = st.number_input('MCHC (g/dL)', min_value=25.0, max_value=40.0, value=33.0, step=0.1)
        mcv_modelo = st.number_input('MCV (fL)', min_value=60.0, max_value=120.0, value=90.0, step=0.1)

        submit_button = st.form_submit_button(label='Obtener Predicción y Guardar', type="primary")

    # Lógica al enviar el formulario
    if submit_button:
        if not model or not supabase:
            st.error("❌ No se puede proceder. Verifique la conexión.")
        else:
            # Realizar predicción
            prediction_result = make_prediction(hb_modelo, mch_modelo, mchc_modelo, mcv_modelo, sex_paciente, edad_paciente, model)
            
            if "error" in prediction_result.lower():
                st.error("No se pudo obtener la predicción.")
            else:
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
                    "Hb": hb_modelo, 
                    "MCH": mch_modelo, 
                    "MCHC": mchc_modelo, 
                    "MCV": mcv_modelo,
                    "sex": sex_paciente[0].upper(), 
                    "prediction": prediction_result,
                }
                
                # Insertar en Supabase
                inserted_data = insert_data_to_supabase(new_record)
                
                if inserted_data:
                    st.success("✅ ¡Datos guardados en Supabase con éxito!")
                    st.markdown("### Resultado de la Predicción:")
                    if prediction_result == "anemia":
                        st.error(f"**ANEMIA** 🛑")
                        st.warning(sugerencia_supa)
                    elif prediction_result == "normal":
                        st.success(f"**NORMAL** ✅")
                        st.info(sugerencia_supa)

# --- Columna de Visualización de Datos ---
with col_data:
    st.header(f"2. Análisis de Registros Históricos")
    
    if st.button("🔄 Actualizar Datos Históricos"):
        get_data_from_supabase.clear()
        st.rerun()

    df_data = get_data_from_supabase()

    if not df_data.empty:
        st.markdown(f"**Total de registros:** `{len(df_data)}`")
        
        tab_data, tab_stats = st.tabs(["📊 Datos y Distribución", "📈 Gráficos de Variables"])
        
        with tab_data:
            st.subheader("Registros Históricos")
            display_cols = ['Time', 'nombre_apellido', 'edad', 'hemoglobina', 'riesgo', 'sugerencia', 'region']
            df_display = df_data[[col for col in display_cols if col in df_data.columns]]
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de distribución
            st.subheader("Distribución de Resultados")
            if 'riesgo' in df_data.columns:
                df_cleaned = df_data.dropna(subset=['riesgo'])
                counts = df_cleaned['riesgo'].value_counts().reset_index()
                counts.columns = ['Resultado', 'Cantidad']
                
                color_map_pie = {
                    'RIESGO INDEFINIDO (¡A DESHABILITAD...)': '#E91E63', 
                    'REGISTRADO': '#4CAF50'
                }
                
                fig_pie = px.pie(
                    counts, 
                    names='Resultado', 
                    values='Cantidad',
                    title='Distribución de Resultados',
                    color='Resultado',
                    color_discrete_map=color_map_pie
                )
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

        with tab_stats:
            st.subheader("Análisis de Variables Hematológicas")
            
            hematology_cols = ['hemoglobina', 'MCH', 'MCHC', 'MCV']
            
            for col_name in hematology_cols:
                if col_name in df_data.columns and 'riesgo' in df_data.columns:
                    st.markdown(f"#### {col_name} por Resultado")
                    col_hist, col_box = st.columns(2)
                    
                    with col_hist:
                        fig_hist = plot_histogram(df_data, col_name, col_name)
                        st.plotly_chart(fig_hist, use_container_width=True)
                        
                    with col_box:
                        fig_box = plot_boxplot(df_data, col_name, col_name)
                        st.plotly_chart(fig_box, use_container_width=True)
                
    else:
        st.info("No hay datos históricos para mostrar. Ingresa el primer registro.")
