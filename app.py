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
    .climate-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN SUPABASE CORREGIDA ---
TABLE_NAME = "alertas"
MODEL_PATH = "modelo_columns.joblib"

# Configuración de Supabase - USAR VARIABLES DE ENTORNO EN PRODUCCIÓN
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw")

# --- CLIMA PREDOMINANTE POR ZONAS DEL PERÚ ---
CLIMA_POR_REGION = {
    "LIMA": {"clima": "Desértico subtropical", "temp_promedio": "21°C", "humedad": "85%", "precipitacion": "10 mm"},
    "AREQUIPA": {"clima": "Semiárido", "temp_promedio": "18°C", "humedad": "45%", "precipitacion": "100 mm"},
    "CUSCO": {"clima": "Templado subhúmedo", "temp_promedio": "14°C", "humedad": "65%", "precipitacion": "700 mm"},
    "PUNO": {"clima": "Frío de altura", "temp_promedio": "8°C", "humedad": "55%", "precipitacion": "600 mm"},
    "ICA": {"clima": "Desértico", "temp_promedio": "22°C", "humedad": "70%", "precipitacion": "5 mm"},
    "LORETO": {"clima": "Tropical húmedo", "temp_promedio": "27°C", "humedad": "85%", "precipitacion": "2800 mm"},
    "SAN MARTÍN": {"clima": "Tropical húmedo", "temp_promedio": "25°C", "humedad": "80%", "precipitacion": "1200 mm"},
    "LA LIBERTAD": {"clima": "Semiárido", "temp_promedio": "20°C", "humedad": "75%", "precipitacion": "200 mm"},
    "ANCASH": {"clima": "Variado de costa y sierra", "temp_promedio": "16°C", "humedad": "70%", "precipitacion": "500 mm"},
    "JUNÍN": {"clima": "Templado frío", "temp_promedio": "12°C", "humedad": "65%", "precipitacion": "800 mm"},
    "PIURA": {"clima": "Semiárido tropical", "temp_promedio": "25°C", "humedad": "70%", "precipitacion": "100 mm"},
    "LAMBAYEQUE": {"clima": "Semiárido", "temp_promedio": "23°C", "humedad": "75%", "precipitacion": "150 mm"},
    "NO ESPECIFICADO": {"clima": "No especificado", "temp_promedio": "N/A", "humedad": "N/A", "precipitacion": "N/A"}
}

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

# --- INICIALIZACIÓN SUPABASE CORREGIDA ---
@st.cache_resource
def init_supabase():
    try:
        # Verificar credenciales
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("❌ Faltan credenciales de Supabase")
            return None
            
        # Crear cliente
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test de conexión simple
        test_response = supabase_client.table(TABLE_NAME).select("*").limit(1).execute()
        
        if hasattr(test_response, 'error') and test_response.error:
            st.error(f"❌ Error en conexión: {test_response.error}")
            return None
            
        st.success("✅ Conexión a Supabase establecida correctamente")
        return supabase_client
        
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None

@st.cache_resource
def load_model():
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            st.success("✅ Modelo ML cargado correctamente")
            return model
        else:
            st.warning("⚠️ Modelo no encontrado, funcionando sin ML")
            return None
    except Exception as e:
        st.error(f"❌ Error cargando modelo: {e}")
        return None

# Inicializar conexiones
supabase = init_supabase()
model = load_model()

# --- FUNCIONES DE DATOS SUPABASE CORREGIDAS ---
def obtener_datos_supabase():
    """Obtiene todos los datos de Supabase"""
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).execute()
            
            # Verificar si hay error en la respuesta
            if hasattr(response, 'error') and response.error:
                st.error(f"Error en consulta: {response.error}")
                return pd.DataFrame()
                
            return pd.DataFrame(response.data) if response.data else pd.DataFrame()
        else:
            st.warning("⚠️ No hay conexión a Supabase")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error obteniendo datos: {e}")
        return pd.DataFrame()

def insertar_datos_supabase(datos):
    """Inserta datos en Supabase"""
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).insert(datos).execute()
            
            if hasattr(response, 'error') and response.error:
                st.error(f"Error insertando datos: {response.error}")
                return None
                
            return response.data[0] if response.data else None
        else:
            st.warning("⚠️ No hay conexión a Supabase")
            return None
    except Exception as e:
        st.error(f"Error insertando datos: {e}")
        return None

def obtener_estadisticas_tiempo_real():
    """Obtiene estadísticas en tiempo real desde Supabase"""
    try:
        if supabase:
            # Obtener datos de los últimos 30 días
            fecha_limite = (datetime.now() - timedelta(days=30)).isoformat()
            response = supabase.table(TABLE_NAME).select("*").gte("fecha_alerta", fecha_limite).execute()
            
            if hasattr(response, 'error') and response.error:
                return {'total_casos': 0, 'alto_riesgo': 0, 'moderado_riesgo': 0, 'tasa_alto_riesgo': 0, 
                        'casos_por_dia': 0, 'total_semana': 0, 'tendencia': '➡️'}
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # Estadísticas básicas
                total_casos = len(df)
                alto_riesgo = len(df[df['riesgo'].str.contains('ALTO', na=False)]) if 'riesgo' in df.columns else 0
                moderado_riesgo = len(df[df['riesgo'].str.contains('MODERADO', na=False)]) if 'riesgo' in df.columns else 0
                
                # Casos por día (últimos 7 días)
                if 'fecha_alerta' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha_alerta']).dt.date
                    ultimos_7_dias = df[df['fecha'] >= (datetime.now().date() - timedelta(days=7))]
                    casos_por_dia = ultimos_7_dias.groupby('fecha').size()
                    
                    return {
                        'total_casos': total_casos,
                        'alto_riesgo': alto_riesgo,
                        'moderado_riesgo': moderado_riesgo,
                        'tasa_alto_riesgo': (alto_riesgo / total_casos * 100) if total_casos > 0 else 0,
                        'casos_por_dia': casos_por_dia.mean() if not casos_por_dia.empty else 0,
                        'total_semana': len(ultimos_7_dias),
                        'tendencia': '↗️' if len(casos_por_dia) > 1 and casos_por_dia.iloc[-1] > casos_por_dia.iloc[-2] else '↘️'
                    }
    except Exception as e:
        st.error(f"Error calculando estadísticas: {e}")
    
    return {'total_casos': 0, 'alto_riesgo': 0, 'moderado_riesgo': 0, 'tasa_alto_riesgo': 0, 
            'casos_por_dia': 0, 'total_semana': 0, 'tendencia': '➡️'}

def obtener_clima_region(region):
    """Obtiene información climática de la región"""
    return CLIMA_POR_REGION.get(region.upper(), CLIMA_POR_REGION["NO ESPECIFICADO"])

# --- FUNCIONES PRINCIPALES MEJORADAS ---
def calcular_riesgo_anemia(hb, edad_meses, factores_clinicos, factores_sociales, acceso_servicios, clima_region):
    """Calcula el nivel de riesgo basado en múltiples factores incluyendo clima"""
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
    
    # Factor clima (zonas tropicales húmedas tienen mayor riesgo de parasitosis)
    if "tropical" in clima_region.lower() or "húmedo" in clima_region.lower():
        puntaje += 5
    
    # Determinar nivel de riesgo
    if puntaje >= 35:
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

def generar_sugerencias(riesgo, puntaje, factores_clinicos, factores_sociales, acceso_servicios, hemoglobina, edad_meses, clima):
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
    
    # Sugerencias por clima
    if "tropical" in clima.lower() or "húmedo" in clima.lower():
        sugerencias.append("🌧️ **VIGILANCIA CLIMÁTICA** - Mayor riesgo de enfermedades parasitarias en zona tropical húmeda")
    
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

# Estado de conexión
if supabase:
    st.success("🟢 CONECTADO A SUPABASE - Sistema operativo")
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE - Modo demostración")

# --- DASHBOARD SUPERIOR CON DATOS REALES ---
st.header("📊 Dashboard Nixon - Métricas en Tiempo Real desde Supabase")

# Obtener métricas en tiempo real
stats = obtener_estadisticas_tiempo_real()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Predicts/Day Reports",
        f"{stats['casos_por_dia']:.1f}",
        stats['tendencia'],
        help="Promedio de casos por día (última semana)"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Total Predictions Week",
        stats['total_semana'],
        help="Total de casos en los últimos 7 días"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Monitoring de Alertas",
        stats['alto_riesgo'],
        f"{stats['tasa_alto_riesgo']:.1f}%",
        help="Casos de alto riesgo activos"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        "Panel Control Estadístico",
        stats['total_casos'],
        f"+{stats['moderado_riesgo']} moderados",
        help="Total de casos en el sistema (30 días)"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- FORMULARIO PRINCIPAL CON CLIMA ---
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
        
        # Mostrar información climática de la región seleccionada
        if region != "NO ESPECIFICADO":
            clima_info = obtener_clima_region(region)
            st.markdown(f"""
            <div class="climate-card">
                <h4>🌤️ Clima {region}</h4>
                <p><strong>{clima_info['clima']}</strong></p>
                <p>Temp: {clima_info['temp_promedio']} | Humedad: {clima_info['humedad']}</p>
                <p>Precipitación: {clima_info['precipitacion']}</p>
            </div>
            """, unsafe_allow_html=True)
    
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
        # Obtener información climática
        clima_info = obtener_clima_region(region)
        
        # Calcular riesgo
        nivel_riesgo, puntaje, estado_recomendado = calcular_riesgo_anemia(
            hemoglobina_g_dl, edad_meses, factores_clinicos, factores_sociales, 
            acceso_servicios, clima_info['clima']
        )
        
        # Generar sugerencias
        sugerencias = generar_sugerencias(
            nivel_riesgo, puntaje, factores_clinicos, factores_sociales, 
            acceso_servicios, hemoglobina_g_dl, edad_meses, clima_info['clima']
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
            st.metric("Clima Zona", clima_info['clima'], f"Temp: {clima_info['temp_promedio']}")
        
        # Sugerencias personalizadas
        st.markdown("---")
        st.header("🎯 Estrategia Nixon - Intervención Oportuna Personalizada")
        
        for i, sugerencia in enumerate(sugerencias, 1):
            st.markdown(f"""
            <div class="factor-card">
                <h4>📍 {sugerencia}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        # Guardar en Supabase solo si hay conexión
        if supabase:
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
                "puntaje_riesgo": int(puntaje),
                "clima_region": clima_info['clima']
            }
            
            resultado = insertar_datos_supabase(record)
            if resultado:
                st.success("✅ Datos guardados en Sistema Nixon - Supabase")
            else:
                st.error("❌ Error al guardar en Nixon System - Supabase")
        else:
            st.warning("⚠️ Datos no guardados - Sin conexión a Supabase")

# --- PANEL DE CONTROL ESTADÍSTICO CON DATOS REALES ---
st.markdown("---")
st.header("📈 Panel de Control Estadístico Nixon - Datos en Tiempo Real")

if st.button("🔄 Actualizar Dashboard Nixon desde Supabase", key="load_historical"):
    with st.spinner("Cargando datos desde Supabase..."):
        datos_reales = obtener_datos_supabase()
    
    if not datos_reales.empty:
        st.success(f"✅ {len(datos_reales)} registros cargados desde Supabase")
        
        # Estadísticas Nixon con datos reales
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            total_casos = len(datos_reales)
            st.metric("Total Casos Nixon", total_casos)
        
        with col_stat2:
            alto_riesgo = len(datos_reales[datos_reales['riesgo'].str.contains('ALTO', na=False)]) if 'riesgo' in datos_reales.columns else 0
            st.metric("Alertas Activas", alto_riesgo)
        
        with col_stat3:
            avg_hemoglobina = datos_reales['hemoglobina_g_dL'].mean() if 'hemoglobina_g_dL' in datos_reales.columns else 0
            st.metric("Hb Promedio", f"{avg_hemoglobina:.1f} g/dL")
        
        with col_stat4:
            if 'región' in datos_reales.columns and not datos_reales['región'].empty:
                region_mas_casos = datos_reales['región'].mode()[0] if not datos_reales['región'].mode().empty else "N/A"
                st.metric("Región Más Afectada", region_mas_casos)
            else:
                st.metric("Región Más Afectada", "N/A")
        
        # Gráficos Nixon con datos reales
        col_chart1, col_chart2 = st.columns(2)
