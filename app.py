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
        border-left: 4px solid #667eea;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
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

ESTADOS_PACIENTE = [
    "EN SEGUIMIENTO",
    "PENDIENTE EVALUACIÓN",
    "CON TRATAMIENTO",
    "ALTA MÉDICA",
    "ABANDONO TRATAMIENTO"
]

FACTORES_CLINICOS = [
    "Historial familiar de anemia",
    "Embarazo múltiple",
    "Intervalos intergenésicos cortos",
    "Enfermedades crónicas",
    "Medicamentos que afectan absorción",
    "Problemas gastrointestinales",
    "Bajo peso al nacer",
    "Prematurez",
    "Infecciones recurrentes"
]

FACTORES_SOCIOECONOMICOS = [
    "Bajo nivel educativo",
    "Ingresos familiares reducidos",
    "Hacinamiento en vivienda",
    "Acceso limitado a servicios básicos",
    "Zona rural o alejada",
    "Trabajo informal o precario",
    "Desnutrición familiar",
    "Falta de agua potable"
]

ACCESO_SERVICIOS = [
    "Control prenatal irregular",
    "Limitado acceso a suplementos",
    "Barreras geográficas a centros de salud",
    "Falta de información nutricional",
    "Cobertura insuficiente de seguros",
    "Horarios inadecuados de atención",
    "Listas de espera prolongadas",
    "Costos de transporte elevados"
]

# --- INICIALIZACIÓN ---
@st.cache_resource
def init_supabase():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test de conexión
        client.table(TABLE_NAME).select("count", count="exact").limit(1).execute()
        st.success("✅ Conexión a Supabase establecida")
        return client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {e}")
        return None

@st.cache_resource
def load_model():
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            st.success("✅ Modelo ML cargado correctamente")
            return model
    except Exception as e:
        st.error(f"❌ Error cargando modelo: {e}")
    return None

supabase = init_supabase()
model = load_model()

# --- FUNCIONES PRINCIPALES ---
def calcular_riesgo_anemia(hb, edad_meses, factores_clinicos, factores_sociales, acceso_servicios):
    """Calcula el nivel de riesgo basado en múltiples factores"""
    puntaje = 0
    
    # Base por hemoglobina según edad
    if edad_meses < 12:  # Lactantes
        if hb < 10.0:
            puntaje += 25
        elif hb < 11.0:
            puntaje += 15
    elif edad_meses < 60:  # Preescolares
        if hb < 10.5:
            puntaje += 25
        elif hb < 11.5:
            puntaje += 15
    else:  # Escolares y adolescentes
        if hb < 11.0:
            puntaje += 25
        elif hb < 12.0:
            puntaje += 15
    
    # Factores clínicos (peso alto)
    puntaje += len(factores_clinicos) * 6
    
    # Factores socioeconómicos
    puntaje += len(factores_sociales) * 5
    
    # Acceso a servicios
    puntaje += len(acceso_servicios) * 4
    
    # Determinar nivel de riesgo
    if puntaje >= 35:
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

def generar_sugerencias(riesgo, puntaje, factores_clinicos, factores_sociales, acceso_servicios, hemoglobina):
    """Genera sugerencias personalizadas basadas en el perfil de riesgo"""
    sugerencias = []
    
    # Sugerencias según nivel de riesgo
    if "ALTO" in riesgo and "ALTA" in riesgo:
        sugerencias.append("🔴 **CONSULTA MÉDICA INMEDIATA** - Requiere atención dentro de 24-48 horas")
        sugerencias.append("💊 **SUPLEMENTACIÓN URGENTE** - Iniciar hierro y ácido fólico inmediatamente")
        sugerencias.append("🩺 **EVALUACIÓN COMPLETA** - Hemograma completo y ferritina sérica")
    elif "ALTO" in riesgo:
        sugerencias.append("🟠 **CONSULTA PRIORITARIA** - Programar dentro de 3-5 días")
        sugerencias.append("💊 **SUPLEMENTACIÓN NUTRICIONAL** - Hierro y micronutrientes")
        sugerencias.append("📋 **EVALUACIÓN CLÍNICA** - Valoración integral del estado nutricional")
    else:
        sugerencias.append("🟡 **CONTROL PROGRAMADO** - Seguimiento en 7-10 días")
        sugerencias.append("🥩 **REFUERZO DIETÉTICO** - Alimentos ricos en hierro hemínico")
    
    # Sugerencias específicas por factores clínicos
    if factores_clinicos:
        sugerencias.append("🏥 **MANEJO DE COMORBILIDADES** - Abordar condiciones clínicas identificadas")
    
    # Sugerencias por factores sociales
    if factores_sociales:
        sugerencias.append("🏠 **INTERVENCIÓN SOCIAL** - Derivación a trabajo social y programas de apoyo")
    
    # Sugerencias por acceso a servicios
    if acceso_servicios:
        sugerencias.append("📍 **FACILITAR ACCESO** - Coordinar transporte o consultas móviles")
    
    # Sugerencia nutricional específica
    if hemoglobina < 11.0:
        sugerencias.append("🍖 **DIETA ESPECÍFICA** - Carnes rojas, hígado, legumbres y cítricos")
    
    # Seguimiento
    sugerencias.append("📊 **MONITOREO CONTINUO** - Control cada 15 días hasta normalización")
    
    return sugerencias

# --- INTERFAZ PRINCIPAL ---
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🩸 Sistema de Control Oportuno de Anemia")
st.markdown("**Análisis Integral de Factores de Riesgo y Seguimiento Clínico**")
st.markdown('</div>', unsafe_allow_html=True)

# Estado del sistema
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Estado Sistema", "🟢 OPERATIVO" if supabase else "🟡 MODO LOCAL")
with col2:
    st.metric("Modelo ML", "✅ CARGADO" if model else "⚠️ BÁSICO")
with col3:
    st.metric("Base de Datos", "📊 alertas")
with col4:
    st.metric("Última Actualización", datetime.now().strftime("%H:%M"))

# --- FORMULARIO PRINCIPAL ---
with st.form("formulario_anemia"):
    st.header("1. Factores Clínicos y Demográficos Clave")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dni = st.text_input("DNI del Paciente", placeholder="Ej: 87654321")
        nombre_completo = st.text_input("Nombre Completo", placeholder="Ej: Juan Pérez García")
        edad_meses = st.number_input("Edad (meses)", 1, 240, 36, 1)
        
    with col2:
        hemoglobina_g_dl = st.number_input("Hemoglobina (g/dL)", 5.0, 20.0, 9.7, 0.1)
        estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE, index=0)
        region = st.selectbox("Región", PERU_REGIONS, index=0)
    
    with col3:
        st.subheader("Parámetros Adicionales")
        mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1)
        mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1)
        mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1)
    
    st.markdown("---")
    st.header("2. Factores Socioeconómicos y Contextuales")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.subheader("Factores Clínicos Adicionales")
        factores_clinicos = st.multiselect(
            "Seleccione factores clínicos presentes:",
            FACTORES_CLINICOS,
            help="Factores que aumentan el riesgo de anemia"
        )
    
    with col5:
        st.subheader("Factores Socioeconómicos")
        factores_sociales = st.multiselect(
            "Seleccione factores socioeconómicos:",
            FACTORES_SOCIOECONOMICOS,
            help="Condiciones sociales que afectan la salud"
        )
    
    st.markdown("---")
    st.header("3. Acceso a Programas y Servicios")
    
    acceso_servicios = st.multiselect(
        "Barreras de acceso a servicios de salud:",
        ACCESO_SERVICIOS,
        help="Factores que limitan el acceso a atención médica"
    )
    
    # Botón de envío
    submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GENERAR REPORTE", type="primary")

# --- PROCESAMIENTO Y RESULTADOS ---
if submitted:
    if not dni or not nombre_completo:
        st.error("❌ Por favor complete el DNI y nombre del paciente")
    else:
        # Calcular riesgo
        nivel_riesgo, puntaje, estado_recomendado = calcular_riesgo_anemia(
            hemoglobina_g_dl, edad_meses, factores_clinicos, factores_sociales, acceso_servicios
        )
        
        # Generar sugerencias
        sugerencias = generar_sugerencias(
            nivel_riesgo, puntaje, factores_clinicos, factores_sociales, 
            acceso_servicios, hemoglobina_g_dl
        )
        
        # Mostrar resultados
        st.markdown("---")
        st.header("📊 Análisis y Reporte de Control Oportuno")
        
        # Tarjeta de riesgo
        if "ALTO" in nivel_riesgo and "ALTA" in nivel_riesgo:
            st.markdown('<div class="risk-high">', unsafe_allow_html=True)
        elif "ALTO" in nivel_riesgo:
            st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
        elif "MODERADO" in nivel_riesgo:
            st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
        else:
            st.markdown('<div class="risk-low">', unsafe_allow_html=True)
        
        st.markdown(f"### **RIESGO: {nivel_riesgo}**")
        st.markdown(f"**Puntaje de riesgo:** {puntaje}/60 puntos | **Estado recomendado:** {estado_recomendado}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas clave
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            # Calcular déficit según edad
            if edad_meses < 12:
                objetivo_hb = 11.0
            elif edad_meses < 60:
                objetivo_hb = 11.5
            else:
                objetivo_hb = 12.0
            
            deficit_hb = max(0, objetivo_hb - hemoglobina_g_dl)
            st.metric(
                "Déficit de Hemoglobina", 
                f"{deficit_hb:.1f} g/dL",
                delta=f"Objetivo: {objetivo_hb} g/dL"
            )
        
        with col_met2:
            porcentaje_objetivo = (hemoglobina_g_dl / objetivo_hb) * 100
            st.metric(
                "Porcentaje del Objetivo",
                f"{porcentaje_objetivo:.1f}%",
                delta=f"{porcentaje_objetivo - 100:.1f}%"
            )
        
        with col_met3:
            total_factores = len(factores_clinicos) + len(factores_sociales) + len(acceso_servicios)
            st.metric(
                "Factores de Riesgo",
                f"{total_factores}",
                "factores identificados"
            )
        
        with col_met4:
            st.metric(
                "Edad del Paciente",
                f"{edad_meses} meses",
                f"{(edad_meses/12):.1f} años"
            )
        
        # Sugerencias personalizadas
        st.markdown("---")
        st.header("🎯 Estrategia Personalizada de Intervención Oportuna")
        
        for i, sugerencia in enumerate(sugerencias, 1):
            st.markdown(f"""
            <div class="factor-card">
                <h4>📍 {sugerencia}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        # Guardar en Supabase
        if supabase:
            try:
                record = {
                    "DNI": dni,
                    "nombre_apellido": nombre_completo,
                    "edad_meses": int(edad_meses),
                    "hemoglobina_g_dL": float(hemoglobina_g_dl),
                    "riesgo": nivel_riesgo,
                    "fecha_alerta": datetime.now().isoformat(),
                    "estado": estado_recomendado,
                    "sugerencias": "; ".join(sugerencias),
                    "región": region,
                    "MCH": float(mch),
                    "MCHC": float(mchc),
                    "MCV": float(mcv),
                    "factores_clinicos": ", ".join(factores_clinicos),
                    "factores_sociales": ", ".join(factores_sociales),
                    "acceso_servicios": ", ".join(acceso_servicios),
                    "puntaje_riesgo": int(puntaje)
                }
                
                response = supabase.table(TABLE_NAME).insert(record).execute()
                if response.data:
                    st.success("✅ Datos guardados exitosamente en Supabase")
                else:
                    st.error("❌ Error al guardar en Supabase")
                    
            except Exception as e:
                st.error(f"❌ Error guardando datos: {e}")

# --- SECCIÓN DE HISTÓRICO Y ANÁLISIS ---
st.markdown("---")
st.header("📈 Histórico de Casos y Análisis")

if st.button("🔄 Cargar Datos Históricos", key="load_historical"):
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).limit(100).execute()
            historico_df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        else:
            historico_df = pd.DataFrame()
        
        if not historico_df.empty:
            # Mostrar estadísticas rápidas
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                total_casos = len(historico_df)
                st.metric("Total de Casos", total_casos)
            
            with col_stat2:
                alto_riesgo = len(historico_df[historico_df['riesgo'].str.contains('ALTO', na=False)])
                st.metric("Casos Alto Riesgo", alto_riesgo)
            
            with col_stat3:
                avg_hemoglobina = historico_df['hemoglobina_g_dL'].mean()
                st.metric("Hemoglobina Promedio", f"{avg_hemoglobina:.1f} g/dL")
            
            # Gráfico de distribución de riesgos
            st.subheader("Distribución de Niveles de Riesgo")
            if 'riesgo' in historico_df.columns:
                fig_riesgos = px.pie(
                    historico_df, 
                    names='riesgo',
                    title='Distribución de Riesgos en la Población',
                    color_discrete_sequence=['#ff5252', '#ff9800', '#4caf50', '#2196f3']
                )
                st.plotly_chart(fig_riesgos, use_container_width=True)
            
            # Tabla de casos recientes
            st.subheader("Casos Recientes")
            columnas_display = ['DNI', 'nombre_apellido', 'edad_meses', 'hemoglobina_g_dL', 'riesgo', 'región', 'fecha_alerta']
            columnas_disponibles = [col for col in columnas_display if col in historico_df.columns]
            
            if columnas_disponibles:
                display_df = historico_df[columnas_disponibles].head(15)
                display_df['fecha_alerta'] = pd.to_datetime(display_df['fecha_alerta']).dt.strftime('%d/%m/%Y %H:%M')
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("💡 No hay datos históricos disponibles. Comienza ingresando casos nuevos.")
            
    except Exception as e:
        st.error(f"Error cargando datos históricos: {e}")

# --- PIE DE PÁGINA ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Sistema de Control Oportuno de Anemia v2.0 | Desarrollado para seguimiento clínico integral</p>
</div>
""", unsafe_allow_html=True)
