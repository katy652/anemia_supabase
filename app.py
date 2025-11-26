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

st.set_page_config(
    page_title="Sistema de Predicción de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# --- CONFIGURACIÓN ---
TABLE_NAME = "alertas"
MODEL_PATH = "modelo_columns.joblib"

# INTENTA CON ESTA CLAVE - SINO USA MODO DEMO
SUPABASE_URL = "https://kwsuszkblbejvliniggd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2MjU0MzMsImV4cCI6MjA1MDIwMTQzM30.DpWyb9LfXqiZBlmuSWfgIw_O2-LDm2b"

PERU_REGIONS = [
    "NO ESPECIFICADO", "AMAZONAS", "ÁNCASH", "APURÍMAC", "AREQUIPA", "AYACUCHO", 
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUÁNUCO", "ICA", "JUNÍN", 
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", 
    "PASCO", "PIURA", "PUNO", "SAN MARTÍN", "TACNA", "TUMBES", "UCAYALI"
]

# --- MODO DEMO (DATOS LOCALES) ---
demo_data = []

# Cargar modelo
@st.cache_resource
def load_anemia_model(path):
    if not os.path.exists(path):
        st.error(f"❌ Archivo '{path}' no encontrado")
        return None
    try:
        loaded_data = joblib.load(path)
        
        # Buscar modelo dentro del archivo
        if hasattr(loaded_data, 'predict'):
            st.success("✅ Modelo ML cargado correctamente")
            return loaded_data
        elif isinstance(loaded_data, (list, tuple, dict)):
            # Buscar cualquier objeto con método predict
            def find_model(obj):
                if hasattr(obj, 'predict'):
                    return obj
                elif isinstance(obj, (list, tuple)):
                    for item in obj:
                        result = find_model(item)
                        if result:
                            return result
                elif isinstance(obj, dict):
                    for value in obj.values():
                        result = find_model(value)
                        if result:
                            return result
                return None
            
            model = find_model(loaded_data)
            if model:
                st.success("✅ Modelo encontrado dentro del archivo")
                return model
        
        st.error("❌ No se encontró un modelo válido en el archivo")
        return None
        
    except Exception as e:
        st.error(f"❌ Error cargando modelo: {e}")
        return None

# Cliente Supabase simplificado
@st.cache_resource
def init_supabase():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test simple
        client.from_(TABLE_NAME).select("count", count="exact").limit(1).execute()
        st.success("✅ Supabase: Conectado")
        return client
    except Exception as e:
        st.warning(f"🔶 Supabase: Usando modo demo ({e})")
        return None

# Cargar componentes
model = load_anemia_model(MODEL_PATH)
supabase = init_supabase()

# --- FUNCIONES CON MODO DEMO ---
def insert_data_to_supabase(data):
    if supabase:
        try:
            data['fecha_alerta'] = pd.Timestamp.now().isoformat()
            response = supabase.table(TABLE_NAME).insert(data).execute()
            if response.data:
                get_data_from_supabase.clear()
                return response.data[0]
        except Exception as e:
            st.error(f"❌ Error insertando en Supabase: {e}")
    
    # MODO DEMO: Guardar localmente
    data['id'] = len(demo_data) + 1
    data['fecha_alerta'] = pd.Timestamp.now().isoformat()
    demo_data.append(data)
    st.info("🔶 Modo demo: Datos guardados localmente")
    return data

@st.cache_data(ttl=600)
def get_data_from_supabase():
    if supabase:
        try:
            response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).limit(5000).execute()
            return pd.DataFrame(response.data) if response.data else pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    
    # MODO DEMO: Devolver datos locales
    return pd.DataFrame(demo_data)

# --- FUNCIONES PRINCIPALES (MANTENIDAS) ---
def make_prediction(Hb, MCH, MCHC, MCV, sex, age, model):
    if not model:
        # Predicción simple basada en hemoglobina si no hay modelo
        if Hb < 12:
            return "anemia"
        else:
            return "normal"
    
    try:
        sex_code = sex[0].upper()
        sex_F = 1 if sex_code == "F" else 0
        sex_M = 1 if sex_code == "M" else 0
        X = np.array([[Hb, MCH, MCHC, MCV, age, sex_F, sex_M]])
        return str(model.predict(X)[0]).lower()
    except Exception as e:
        st.error(f"❌ Error en predicción: {e}")
        return "normal"  # Valor por defecto

def plot_histogram(df, column, title):
    if df.empty or 'riesgo' not in df.columns:
        return go.Figure()
    
    color_map = {
        "RIESGO INDEFINIDO (¡A DESHABILITAD...)": "red", 
        "REGISTRADO": "green"
    }
    
    fig = px.histogram(
        df, x=column, color='riesgo', marginal="box",
        nbins=20, title=f'Histograma de {title}',
        template="plotly_white", color_discrete_map=color_map
    )
    fig.update_layout(bargap=0.1)
    return fig

# --- INTERFAZ PRINCIPAL ---
st.title("🩸 Sistema de Detección de Anemia")
st.markdown("---")

# Estado del sistema
st.subheader("Estado del Sistema")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("**Modelo ML:**", "✅ Cargado" if model else "❌ Error")
with col2:
    st.write("**Base de datos:**", "✅ Supabase" if supabase else "🔶 Modo Demo")
with col3:
    st.write("**Registros:**", f"📊 {len(get_data_from_supabase())}")

# Columnas principales
col_form, col_data = st.columns([1, 1])

# FORMULARIO
with col_form:
    st.header("1. Ingreso de Datos")
    with st.form("prediction_form"):
        st.subheader("Datos del Paciente")
        nombre = st.text_input("Nombre y Apellido")
        edad = st.number_input("Edad (años)", 1, 120, 35)
        sexo = st.selectbox("Sexo", ["Femenino", "Masculino"])
        region = st.selectbox("Región", PERU_REGIONS)
        
        st.subheader("Valores Hematológicos")
        hb = st.number_input("Hemoglobina (g/dL)", 0.0, 25.0, 12.5, 0.1)
        mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1)
        mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1)
        mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1)
        
        if st.form_submit_button("🎯 Obtener Predicción y Guardar"):
            if nombre:
                prediction = make_prediction(hb, mch, mchc, mcv, sexo, edad, model)
                
                riesgo = "RIESGO INDEFINIDO (¡A DESHABILITAD...)" if prediction == "anemia" else "REGISTRADO"
                sugerencia = "¡Alerta! Posible anemia - Consultar médico" if prediction == "anemia" else "Resultados normales"
                
                new_record = {
                    "nombre_apellido": nombre,
                    "edad": edad, "hemoglobina": hb, "riesgo": riesgo,
                    "sugerencia": sugerencia, "region": region,
                    "Hb": hb, "MCH": mch, "MCHC": mchc, "MCV": mcv,
                    "sex": sexo[0].upper(), "prediction": prediction
                }
                
                if insert_data_to_supabase(new_record):
                    st.success("✅ Datos guardados exitosamente")
                    st.metric("Resultado", "ANEMIA 🛑" if prediction == "anemia" else "NORMAL ✅")
                    st.info(sugerencia)
            else:
                st.error("❌ Ingresa el nombre del paciente")

# VISUALIZACIÓN
with col_data:
    st.header("2. Registros Históricos")
    
    if st.button("🔄 Actualizar Datos"):
        get_data_from_supabase.clear()
        st.rerun()
    
    df = get_data_from_supabase()
    
    if not df.empty:
        st.metric("Total de registros", len(df))
        
        tab1, tab2 = st.tabs(["📋 Datos", "📊 Gráficos"])
        
        with tab1:
            st.dataframe(df[['nombre_apellido', 'edad', 'hemoglobina', 'riesgo', 'region']], use_container_width=True)
            
            if 'riesgo' in df.columns:
                fig_pie = px.pie(
                    df, names='riesgo', title='Distribución de Resultados'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab2:
            if 'hemoglobina' in df.columns:
                fig_hist = plot_histogram(df, 'hemoglobina', 'Hemoglobina')
                st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("💡 No hay registros. Usa el formulario para agregar el primero.")

# --- INSTRUCCIONES PARA OBTENER API KEY ---
with st.expander("🔧 Configuración de Supabase"):
    st.markdown("""
    **Para conectar con Supabase:**
    
    1. Ve a [tu proyecto en Supabase](https://supabase.com/dashboard)
    2. Haz clic en **Settings (Configuración)**
    3. Ve a **API** en el menú lateral
    4. Copia la **URL** y la **API Key** (clave anónima public)
    5. Reemplázalas en el código:
    
    ```python
    SUPABASE_URL = "tu_url_de_supabase"
    SUPABASE_KEY = "tu_clave_anonima_public"
    ```
    
    **La API Key debe comenzar con:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
    """)
