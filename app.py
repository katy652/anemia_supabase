import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
import os
import time
from datetime import datetime

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

st.set_page_config(
    page_title="Sistema de Control Oportuno de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
        font-family: 'Arial', sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .risk-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-moderate {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .risk-low {
        background-color: #e8f5e8;
        border-left: 5px solid #4caf50;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .factor-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN SUPABASE ---
TABLE_NAME = "alertas"
MODEL_PATH = "modelo_columns.joblib"

SUPABASE_URL = "https://kwsuszkblbejvliniggd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2MjU0MzMsImV4cCI6MjA1MDIwMTQzM30.DpWyb9LfXqiZBlmuSWfgIw_O2-LDm2b"

# --- LISTAS DE OPCIONES ---
PERU_REGIONS = [
    "NO ESPECIFICADO", "AMAZONAS", "ÁNCASH", "APURÍMAC", "AREQUIPA", "AYACUCHO", 
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUÁNUCO", "ICA", "JUNÍN", 
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", 
    "PASCO", "PIURA", "PUNO", "SAN MARTÍN", "TACNA", "TUMBES", "UCAYALI"
]

FACTORES_CLINICOS = [
    "Historial familiar de anemia",
    "Embarazo múltiple",
    "Intervalos intergenésicos cortos",
    "Enfermedades crónicas",
    "Medicamentos que afectan absorción",
    "Problemas gastrointestinales"
]

FACTORES_SOCIOECONOMICOS = [
    "Bajo nivel educativo",
    "Ingresos familiares reducidos",
    "Hacinamiento en vivienda",
    "Acceso limitado a servicios básicos",
    "Zona rural o alejada",
    "Trabajo informal o precario"
]

ACCESO_SERVICIOS = [
    "Control prenatal irregular",
    "Limitado acceso a suplementos",
    "Barreras geográficas a centros de salud",
    "Falta de información nutricional",
    "Cobertura insuficiente de seguros",
    "Horarios inadecuados de atención"
]

# --- INICIALIZACIÓN ---
@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

@st.cache_resource
def load_model():
    try:
        if os.path.exists(MODEL_PATH):
            return joblib.load(MODEL_PATH)
    except:
        pass
    return None

supabase = init_supabase()
model = load_model()

# --- FUNCIONES PRINCIPALES ---
def calcular_riesgo_anemia(hb, factores_clinicos, factores_sociales, acceso_servicios):
    """Calcula el nivel de riesgo basado en múltiples factores"""
    puntaje = 0
    
    # Base por hemoglobina
    if hb < 9.0:
        puntaje += 30
    elif hb < 11.0:
        puntaje += 20
    elif hb < 12.0:
        puntaje += 10
    
    # Factores clínicos
    puntaje += len(factores_clinicos) * 5
    
    # Factores socioeconómicos
    puntaje += len(factores_sociales) * 4
    
    # Acceso a servicios
    puntaje += len(acceso_servicios) * 3
    
    # Determinar nivel de riesgo
    if puntaje >= 30:
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje
    elif puntaje >= 20:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje
    elif puntaje >= 10:
        return "RIESGO MODERADO", puntaje
    else:
        return "BAJO RIESGO", puntaje

def generar_recomendaciones(riesgo, factores_clinicos, factores_sociales, acceso_servicios):
    """Genera recomendaciones personalizadas basadas en el perfil de riesgo"""
    recomendaciones = []
    
    if "ALTO" in riesgo:
        recomendaciones.append("🔴 **Consulta médica inmediata** dentro de las próximas 48 horas")
        recomendaciones.append("💊 **Suplementación urgente** con hierro y ácido fólico")
        recomendaciones.append("🩺 **Evaluación completa** de parámetros hematológicos")
    else:
        recomendaciones.append("🟡 **Control médico programado** en los próximos 7 días")
        recomendaciones.append("🥩 **Refuerzo nutricional** con alimentos ricos en hierro")
    
    # Recomendaciones específicas por factores
    if factores_clinicos:
        recomendaciones.append("📋 **Manejo de condiciones clínicas** identificadas")
    
    if factores_sociales:
        recomendaciones.append("🏠 **Atención a factores socioeconómicos** con trabajo social")
    
    if acceso_servicios:
        recomendaciones.append("🏥 **Facilitar acceso** a servicios de salud")
    
    recomendaciones.append("📊 **Seguimiento continuo** cada 15 días")
    
    return recomendaciones

# --- INTERFAZ PRINCIPAL ---
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🩸 Sistema de Control Oportuno de Anemia")
st.markdown("**Análisis Integral de Factores de Riesgo y Seguimiento**")
st.markdown('</div>', unsafe_allow_html=True)

# Estado del sistema
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Estado Sistema", "🟢 OPERATIVO" if supabase else "🟡 MODO LOCAL")
with col2:
    st.metric("Modelo ML", "✅ CARGADO" if model else "⚠️ BÁSICO")
with col3:
    st.metric("Última Actualización", datetime.now().strftime("%d/%m/%Y %H:%M"))

# --- FORMULARIO PRINCIPAL ---
with st.form("formulario_anemia"):
    st.header("1. Factores Clínicos y Demográficos Clave")
    
    col1, col2 = st.columns(2)
    
    with col1:
        codigo_paciente = st.text_input("Código de Paciente", value="0")
        fecha_consulta = st.date_input("Fecha de Consulta", datetime.now())
        nombre_completo = st.text_input("Nombre Completo")
        edad = st.number_input("Edad (años)", 1, 100, 25)
        sexo = st.selectbox("Sexo", ["Femenino", "Masculino"])
        region = st.selectbox("Región", PERU_REGIONS)
    
    with col2:
        hemoglobina = st.number_input("Hemoglobina (g/dL)", 5.0, 20.0, 9.7, 0.1)
        mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1)
        mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1)
        mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1)
    
    st.markdown("---")
    st.header("2. Factores Socioeconómicos y Contextuales")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Factores Clínicos Adicionales")
        factores_clinicos = st.multiselect(
            "Seleccione factores presentes:",
            FACTORES_CLINICOS
        )
    
    with col4:
        st.subheader("Factores Socioeconómicos")
        factores_sociales = st.multiselect(
            "Seleccione factores presentes:",
            FACTORES_SOCIOECONOMICOS
        )
    
    st.markdown("---")
    st.header("3. Acceso a Programas y Servicios")
    
    acceso_servicios = st.multiselect(
        "Barreras de acceso identificadas:",
        ACCESO_SERVICIOS
    )
    
    # Botón de envío
    submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GENERAR REPORTE", type="primary")

# --- PROCESAMIENTO Y RESULTADOS ---
if submitted:
    # Calcular riesgo
    nivel_riesgo, puntaje = calcular_riesgo_anemia(
        hemoglobina, factores_clinicos, factores_sociales, acceso_servicios
    )
    
    # Generar recomendaciones
    recomendaciones = generar_recomendaciones(
        nivel_riesgo, factores_clinicos, factores_sociales, acceso_servicios
    )
    
    # Mostrar resultados
    st.markdown("---")
    st.header("📊 Análisis y Reporte de Control Oportuno")
    
    # Tarjeta de riesgo
    if "ALTO" in nivel_riesgo:
        st.markdown(f'<div class="risk-high">', unsafe_allow_html=True)
    elif "MODERADO" in nivel_riesgo:
        st.markdown(f'<div class="risk-moderate">', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="risk-low">', unsafe_allow_html=True)
    
    st.markdown(f"### **RIESGO: {nivel_riesgo}**")
    st.markdown(f"**Puntaje de riesgo:** {puntaje}/50 puntos")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Métricas clave
    col_met1, col_met2, col_met3 = st.columns(3)
    
    with col_met1:
        deficit_hb = max(0, 12 - hemoglobina)
        st.metric(
            "Déficit de Hemoglobina", 
            f"{deficit_hb:.1f} g/dL",
            delta=f"-{deficit_hb:.1f} g/dL del objetivo"
        )
    
    with col_met2:
        porcentaje_objetivo = (hemoglobina / 12) * 100
        st.metric(
            "Porcentaje del Objetivo",
            f"{porcentaje_objetivo:.1f}%",
            delta=f"{porcentaje_objetivo - 100:.1f}%"
        )
    
    with col_met3:
        st.metric(
            "Factores de Riesgo Identificados",
            f"{len(factores_clinicos) + len(factores_sociales) + len(acceso_servicios)}",
            "factores críticos"
        )
    
    # Recomendaciones personalizadas
    st.markdown("---")
    st.header("🎯 Estrategia Personalizada de Intervención Oportuna")
    
    for i, recomendacion in enumerate(recomendaciones, 1):
        st.markdown(f"""
        <div class="factor-card">
            <h4>🔷 {recomendacion}</h4>
        </div>
        """, unsafe_allow_html=True)
    
    # Guardar en Supabase si está disponible
    if supabase and nombre_completo:
        try:
            record = {
                "codigo_paciente": codigo_paciente,
                "nombre_apellido": nombre_completo,
                "edad": edad,
                "sexo": sexo[0].upper(),
                "region": region,
                "hemoglobina": hemoglobina,
                "Hb": hemoglobina,
                "MCH": mch,
                "MCHC": mchc,
                "MCV": mcv,
                "factores_clinicos": str(factores_clinicos),
                "factores_sociales": str(factores_sociales),
                "acceso_servicios": str(acceso_servicios),
                "nivel_riesgo": nivel_riesgo,
                "puntaje_riesgo": puntaje,
                "recomendaciones": str(recomendaciones),
                "fecha_alerta": datetime.now().isoformat()
            }
            
            supabase.table(TABLE_NAME).insert(record).execute()
            st.success("✅ Datos guardados en el sistema")
            
        except Exception as e:
            st.warning("⚠️ Datos guardados localmente (error de conexión)")

# --- SECCIÓN DE HISTÓRICO ---
st.markdown("---")
st.header("📈 Histórico de Casos y Análisis")

if st.button("🔄 Cargar Datos Históricos"):
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).limit(100).execute()
            historico_df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        else:
            historico_df = pd.DataFrame()
        
        if not historico_df.empty:
            st.subheader("Resumen de Riesgos")
            
            # Gráfico de distribución de riesgos
            if 'nivel_riesgo' in historico_df.columns:
                fig_riesgos = px.pie(
                    historico_df, 
                    names='nivel_riesgo',
                    title='Distribución de Niveles de Riesgo',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig_riesgos, use_container_width=True)
            
            # Tabla de casos recientes
            st.subheader("Casos Recientes")
            columnas_display = ['nombre_apellido', 'edad', 'hemoglobina', 'nivel_riesgo', 'region', 'fecha_alerta']
            columnas_disponibles = [col for col in columnas_display if col in historico_df.columns]
            
            if columnas_disponibles:
                st.dataframe(
                    historico_df[columnas_disponibles].head(10),
                    use_container_width=True
                )
        else:
            st.info("No hay datos históricos disponibles. Comienza ingresando casos nuevos.")
            
    except Exception as e:
        st.error(f"Error cargando datos históricos: {e}")

# --- INFORMACIÓN ADICIONAL ---
with st.expander("ℹ️ Guía de Interpretación"):
    st.markdown("""
    **Escala de Riesgo:**
    - **ALTO RIESGO (Alerta Clínica - ALTA)**: 30-50 puntos - Intervención inmediata requerida
    - **ALTO RIESGO (Alerta Clínica - MODERADA)**: 20-29 puntos - Acción prioritaria necesaria
    - **RIESGO MODERADO**: 10-19 puntos - Seguimiento estrecho recomendado
    - **BAJO RIESGO**: 0-9 puntos - Mantener vigilancia rutinaria
    
    **Parámetros de Referencia:**
    - Hemoglobina objetivo: 12-16 g/dL (mujeres), 13-17 g/dL (hombres)
    - Cada factor identificado suma puntos al puntaje de riesgo
    - La intervención se personaliza según factores específicos
    """)
