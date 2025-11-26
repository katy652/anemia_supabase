import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
import os
import time
from datetime import datetime, timedelta

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

st.set_page_config(
    page_title="Sistema Nixon - Control de Anemia",
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
    .dashboard-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
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
    .prediction-badge {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN SUPABASE ---
TABLE_NAME = "alertas"
MODEL_PATH = "modelo_columns.joblib"

SUPABASE_URL = "https://kwsuszkblbejvliniggd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2MjU0MzMsImV4cCI6MjA1MDIwMTQzM30.DpWyb9LfXqiZBlmuSWfgIw_O2-LDm2b"

# --- LISTAS DE OPCIONES MEJORADAS ---
PERU_REGIONS = [
    "NO ESPECIFICADO", "AMAZONAS", "ÁNCASH", "APURÍMAC", "AREQUIPA", "AYACUCHO", 
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUÁNUCO", "ICA", "JUNÍN", 
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS", "MOQUEGUA", 
    "PASCO", "PIURA", "PUNO", "SAN MARTÍN", "TACNA", "TUMBES", "UCAYALI"
]

ESTADOS_PACIENTE = [
    "EN SEGUIMIENTO",
    "PENDIENTE EVALUACIÓN",
    "CON TRATAMIENTO ACTIVO",
    "ALTA MÉDICA",
    "ABANDONO TRATAMIENTO",
    "REFERIDO ESPECIALISTA"
]

# --- FACTORES CLÍNICOS MEJORADOS ---
FACTORES_CLINICOS = [
    "Historial familiar de anemia",
    "Embarazo múltiple",
    "Intervalos intergenésicos cortos",
    "Enfermedades crónicas (renal, hepática)",
    "Medicamentos que afectan absorción",
    "Problemas gastrointestinales crónicos",
    "Bajo peso al nacer (<2500g)",
    "Prematurez (<37 semanas)",
    "Infecciones recurrentes",
    "Parasitosis intestinal",
    "Alergias alimentarias múltiples",
    "Cirugías digestivas previas"
]

# --- FACTORES SOCIOECONÓMICOS MEJORADOS ---
FACTORES_SOCIOECONOMICOS = [
    "Bajo nivel educativo de padres",
    "Ingresos familiares reducidos",
    "Hacinamiento en vivienda (>3 personas/cuarto)",
    "Acceso limitado a agua potable",
    "Zona rural o alejada",
    "Trabajo informal o precario",
    "Desnutrición familiar",
    "Falta de saneamiento básico",
    "Migración reciente",
    "Falta de seguridad alimentaria",
    "Alto índice de pobreza",
    "Limitado acceso a electricidad"
]

# --- ACCESO A SERVICIOS MEJORADOS ---
ACCESO_SERVICIOS = [
    "Control prenatal irregular",
    "Limitado acceso a suplementos",
    "Barreras geográficas a centros de salud",
    "Falta de información nutricional",
    "Cobertura insuficiente de seguros",
    "Horarios inadecuados de atención",
    "Listas de espera prolongadas",
    "Costos de transporte elevados",
    "Falta de personal especializado",
    "Desabastecimiento de medicamentos",
    "Barreras culturales/idiomáticas",
    "Estigma social por anemia"
]

# --- INICIALIZACIÓN ---
@st.cache_resource
def init_supabase():
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test de conexión
        client.table(TABLE_NAME).select("count", count="exact").limit(1).execute()
        return client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {e}")
        return None

@st.cache_resource
def load_model():
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            return model
    except Exception as e:
        st.error(f"❌ Error cargando modelo: {e}")
    return None

supabase = init_supabase()
model = load_model()

# --- FUNCIONES PRINCIPALES MEJORADAS ---
def calcular_predicciones_diarias():
    """Calcula métricas de predicciones por día"""
    try:
        if supabase:
            # Obtener datos de los últimos 7 días
            fecha_limite = (datetime.now() - timedelta(days=7)).isoformat()
            response = supabase.table(TABLE_NAME).select("fecha_alerta, riesgo").gte("fecha_alerta", fecha_limite).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                df['fecha'] = pd.to_datetime(df['fecha_alerta']).dt.date
                predicciones_por_dia = df.groupby('fecha').size()
                return {
                    'promedio_diario': predicciones_por_dia.mean() if not predicciones_por_dia.empty else 0,
                    'total_semana': len(df),
                    'tendencia': '↗️' if len(predicciones_por_dia) > 1 and predicciones_por_dia.iloc[-1] > predicciones_por_dia.iloc[-2] else '↘️'
                }
    except:
        pass
    return {'promedio_diario': 0, 'total_semana': 0, 'tendencia': '➡️'}

def obtener_estadisticas_alertas():
    """Obtiene estadísticas de monitoreo de alertas"""
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("riesgo, fecha_alerta").execute()
            if response.data:
                df = pd.DataFrame(response.data)
                total_casos = len(df)
                alto_riesgo = len(df[df['riesgo'].str.contains('ALTO', na=False)])
                moderado_riesgo = len(df[df['riesgo'].str.contains('MODERADO', na=False)])
                
                return {
                    'total_casos': total_casos,
                    'alto_riesgo': alto_riesgo,
                    'moderado_riesgo': moderado_riesgo,
                    'tasa_alto_riesgo': (alto_riesgo / total_casos * 100) if total_casos > 0 else 0
                }
    except:
        pass
    return {'total_casos': 0, 'alto_riesgo': 0, 'moderado_riesgo': 0, 'tasa_alto_riesgo': 0}

def calcular_riesgo_anemia(hb, edad_meses, factores_clinicos, factores_sociales, acceso_servicios):
    """Calcula el nivel de riesgo basado en múltiples factores"""
    puntaje = 0
    
    # Base por hemoglobina según edad
    if edad_meses < 12:  # Lactantes
        if hb < 9.0: puntaje += 30
        elif hb < 10.0: puntaje += 20
        elif hb < 11.0: puntaje += 10
    elif edad_meses < 60:  # Preescolares
        if hb < 9.5: puntaje += 30
        elif hb < 10.5: puntaje += 20
        elif hb < 11.5: puntaje += 10
    else:  # Escolares y adolescentes
        if hb < 10.0: puntaje += 30
        elif hb < 11.0: puntaje += 20
        elif hb < 12.0: puntaje += 10
    
    # Factores clínicos (peso alto)
    puntaje += len(factores_clinicos) * 4
    
    # Factores socioeconómicos
    puntaje += len(factores_sociales) * 3
    
    # Acceso a servicios
    puntaje += len(acceso_servicios) * 2
    
    # Determinar nivel de riesgo
    if puntaje >= 35:
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

def generar_sugerencias(riesgo, puntaje, factores_clinicos, factores_sociales, acceso_servicios, hemoglobina, edad_meses):
    """Genera sugerencias personalizadas basadas en el perfil de riesgo"""
    sugerencias = []
    
    # Sugerencias según nivel de riesgo
    if "ALTO" in riesgo and "ALTA" in riesgo:
        sugerencias.append("🔴 **CONSULTA MÉDICA INMEDIATA** - Requiere atención dentro de 24-48 horas")
        sugerencias.append("💊 **SUPLEMENTACIÓN URGENTE** - Sulfato ferroso 3-6 mg/kg/día + ácido fólico")
        sugerencias.append("🩺 **EVALUACIÓN COMPLETA** - Hemograma, ferritina, transferrina, VSG")
    elif "ALTO" in riesgo:
        sugerencias.append("🟠 **CONSULTA PRIORITARIA** - Programar dentro de 3-5 días")
        sugerencias.append("💊 **SUPLEMENTACIÓN NUTRICIONAL** - Hierro elemental 2-3 mg/kg/día")
        sugerencias.append("📋 **EVALUACIÓN CLÍNICA** - Valoración integral del estado nutricional")
    else:
        sugerencias.append("🟡 **CONTROL PROGRAMADO** - Seguimiento en 7-10 días")
        sugerencias.append("🥩 **REFUERZO DIETÉTICO** - Alimentos ricos en hierro hemínico y vitamina C")
    
    # Sugerencias específicas por factores clínicos
    if any("infecc" in factor.lower() for factor in factores_clinicos):
        sugerencias.append("🦠 **MANEJO INFECCIOSO** - Evaluar y tratar procesos infecciosos subyacentes")
    
    if any("parasit" in factor.lower() for factor in factores_clinicos):
        sugerencias.append("🐛 **DESPARASITACIÓN** - Administrar antiparasitarios según protocolo")
    
    # Sugerencias por factores sociales
    if factores_sociales:
        sugerencias.append("🏠 **INTERVENCIÓN SOCIAL** - Derivación a trabajo social y programas de apoyo alimentario")
    
    # Sugerencias por acceso a servicios
    if any("barrera" in factor.lower() or "geográf" in factor.lower() for factor in acceso_servicios):
        sugerencias.append("📍 **FACILITAR ACCESO** - Coordinar consultas móviles o transporte subsidiado")
    
    # Sugerencia nutricional específica por edad
    if edad_meses < 24:
        sugerencias.append("🍼 **LACTANCIA Y ALIMENTACIÓN** - Promover lactancia materna y alimentos fortificados")
    else:
        sugerencias.append("🍖 **DIETA ESPECÍFICA** - Carnes rojas, hígado, legumbres, vegetales verdes y cítricos")
    
    # Seguimiento según riesgo
    if "ALTO" in riesgo:
        sugerencias.append("📊 **MONITOREO ESTRECHO** - Control semanal hasta mejoría")
    else:
        sugerencias.append("📊 **SEGUIMIENTO** - Control cada 15 días hasta normalización")
    
    return sugerencias

# --- INTERFAZ PRINCIPAL MEJORADA ---
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia")
st.markdown("**Predicts/day reports • Monitoring de Alertas • Panel de control estadístico**")
st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD SUPERIOR ---
st.header("📊 Dashboard Nixon - Métricas en Tiempo Real")

# Obtener métricas
predicciones_metrics = calcular_predicciones_diarias()
alertas_metrics = obtener_estadisticas_alertas()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Predicts/Day Reports",
        f"{predicciones_metrics['promedio_diario']:.1f}",
        predicciones_metrics['tendencia'],
        help="Promedio de predicciones por día (última semana)"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Total Predictions Week",
        predicciones_metrics['total_semana'],
        help="Total de predicciones en los últimos 7 días"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Monitoring de Alertas",
        alertas_metrics['alto_riesgo'],
        f"{alertas_metrics['tasa_alto_riesgo']:.1f}%",
        help="Casos de alto riesgo activos"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Panel Control Estadístico",
        alertas_metrics['total_casos'],
        f"+{alertas_metrics['moderado_riesgo']} moderados",
        help="Total de casos en el sistema"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- FORMULARIO PRINCIPAL MEJORADO ---
with st.form("formulario_anemia"):
    st.header("1. Factores Clínicos y Demográficos Clave")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        dni = st.text_input("DNI del Paciente", placeholder="Ej: 87654321")
        nombre_completo = st.text_input("Nombre Completo", placeholder="Ej: Juan Pérez García")
        edad_meses = st.number_input("Edad (meses)", 1, 240, 36, 1, help="Edad en meses del paciente")
        
    with col2:
        hemoglobina_g_dl = st.number_input("Hemoglobina (g/dL)", 5.0, 20.0, 9.7, 0.1, 
                                         help="Nivel de hemoglobina en gramos por decilitro")
        estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE, index=0)
        region = st.selectbox("Región", PERU_REGIONS, index=0)
    
    with col3:
        st.subheader("Parámetros Hematológicos")
        mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1, help="Hemoglobina Corpuscular Media")
        mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1, help="Concentración de Hemoglobina Corpuscular Media")
        mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1, help="Volumen Corpuscular Medio")
    
    st.markdown("---")
    st.header("2. Factores Socioeconómicos y Contextuales")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.subheader("🏥 Factores Clínicos Adicionales")
        st.markdown("**Seleccione factores clínicos presentes:**")
        factores_clinicos = st.multiselect(
            "Factores Clínicos:",
            FACTORES_CLINICOS,
            help="Factores médicos que aumentan el riesgo de anemia",
            label_visibility="collapsed"
        )
    
    with col5:
        st.subheader("🏠 Factores Socioeconómicos")
        st.markdown("**Seleccione factores contextuales:**")
        factores_sociales = st.multiselect(
            "Factores Socioeconómicos:",
            FACTORES_SOCIOECONOMICOS,
            help="Condiciones sociales y económicas que afectan la salud",
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    st.header("3. Acceso a Programas y Servicios")
    
    st.markdown("**Identifique barreras de acceso a servicios de salud:**")
    acceso_servicios = st.multiselect(
        "Barreras de Acceso:",
        ACCESO_SERVICIOS,
        help="Factores que limitan el acceso a atención médica y programas de salud",
        label_visibility="collapsed"
    )
    
    # Botón de envío
    submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GENERAR REPORTE NIXON", type="primary")

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
            acceso_servicios, hemoglobina_g_dl, edad_meses
        )
        
        # Mostrar resultados
        st.markdown("---")
        st.header("📊 Análisis y Reporte de Control Oportuno - Nixon System")
        
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
        st.markdown(f"**Puntaje Nixon:** {puntaje}/60 puntos | **Estado recomendado:** {estado_recomendado}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Métricas clave
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            # Calcular déficit según edad
            if edad_meses < 12: objetivo_hb = 11.0
            elif edad_meses < 60: objetivo_hb = 11.5
            else: objetivo_hb = 12.0
            
            deficit_hb = max(0, objetivo_hb - hemoglobina_g_dl)
            st.metric("Déficit de Hb", f"{deficit_hb:.1f} g/dL", f"Objetivo: {objetivo_hb} g/dL")
        
        with col_met2:
            porcentaje_objetivo = (hemoglobina_g_dl / objetivo_hb) * 100
            st.metric("% Objetivo", f"{porcentaje_objetivo:.1f}%", f"{porcentaje_objetivo - 100:.1f}%")
        
        with col_met3:
            total_factores = len(factores_clinicos) + len(factores_sociales) + len(acceso_servicios)
            st.metric("Factores Riesgo", f"{total_factores}", "identificados")
        
        with col_met4:
            st.metric("Edad", f"{edad_meses} meses", f"{(edad_meses/12):.1f} años")
        
        # Sugerencias personalizadas
        st.markdown("---")
        st.header("🎯 Estrategia Nixon - Intervención Oportuna Personalizada")
        
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
                    st.success("✅ Datos guardados en Sistema Nixon")
                else:
                    st.error("❌ Error al guardar en Nixon System")
                    
            except Exception as e:
                st.error(f"❌ Error guardando datos: {e}")

# --- PANEL DE CONTROL ESTADÍSTICO ---
st.markdown("---")
st.header("📈 Panel de Control Estadístico Nixon")

if st.button("🔄 Actualizar Dashboard Nixon", key="load_historical"):
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).limit(200).execute()
            historico_df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        else:
            historico_df = pd.DataFrame()
        
        if not historico_df.empty:
            # Estadísticas Nixon
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                total_casos = len(historico_df)
                st.metric("Total Casos Nixon", total_casos)
            
            with col_stat2:
                alto_riesgo = len(historico_df[historico_df['riesgo'].str.contains('ALTO', na=False)])
                st.metric("Alertas Activas", alto_riesgo)
            
            with col_stat3:
                avg_hemoglobina = historico_df['hemoglobina_g_dL'].mean()
                st.metric("Hb Promedio", f"{avg_hemoglobina:.1f} g/dL")
            
            with col_stat4:
                region_mas_casos = historico_df['región'].mode()[0] if not historico_df['región'].mode().empty else "N/A"
                st.metric("Región Más Afectada", region_mas_casos)
            
            # Gráficos Nixon
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.subheader("📊 Distribución de Riesgos Nixon")
                if 'riesgo' in historico_df.columns:
                    fig_riesgos = px.pie(
                        historico_df, 
                        names='riesgo',
                        title='Distribución de Niveles de Riesgo',
                        color_discrete_sequence=['#ff5252', '#ff9800', '#4caf50', '#2196f3']
                    )
                    st.plotly_chart(fig_riesgos, use_container_width=True)
            
            with col_chart2:
                st.subheader("📈 Tendencia Hemoglobina por Edad")
                if all(col in historico_df.columns for col in ['hemoglobina_g_dL', 'edad_meses']):
                    fig_scatter = px.scatter(
                        historico_df,
                        x='edad_meses',
                        y='hemoglobina_g_dL',
                        color='riesgo',
                        title='Relación Edad vs Hemoglobina',
                        labels={'edad_meses': 'Edad (meses)', 'hemoglobina_g_dL': 'Hemoglobina (g/dL)'}
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Tabla de casos recientes
            st.subheader("🕐 Casos Recientes - Monitoring Nixon")
            columnas_display = ['DNI', 'nombre_apellido', 'edad_meses', 'hemoglobina_g_dL', 'riesgo', 'región', 'fecha_alerta']
            columnas_disponibles = [col for col in columnas_display if col in historico_df.columns]
            
            if columnas_disponibles:
                display_df = historico_df[columnas_disponibles].head(15)
                display_df['fecha_alerta'] = pd.to_datetime(display_df['fecha_alerta']).dt.strftime('%d/%m/%Y %H:%M')
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("💡 Sistema Nixon listo. Comience ingresando el primer caso.")
            
    except Exception as e:
        st.error(f"Error cargando datos Nixon: {e}")

# --- PIE DE PÁGINA NIXON ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <h3>🏥 SISTEMA NIXON v3.0</h3>
    <p>Predicts/day reports • Monitoring de Alertas • Panel de control estadístico</p>
    <p>Desarrollado para el control oportuno y seguimiento integral de anemia</p>
</div>
""", unsafe_allow_html=True)
