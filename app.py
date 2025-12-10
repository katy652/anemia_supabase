import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import time
from datetime import datetime, timedelta

# ==================================================
# CONFIGURACIÓN E INICIALIZACIÓN
# ==================================================

st.set_page_config(
    page_title="Sistema Nixon - Control de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown("""
<style>
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
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card { 
        background: white; 
        padding: 1rem; 
        border-radius: 8px; 
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .climate-card { 
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
        color: white; 
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .altitude-card {
        background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .nutrition-card {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-critical {
        background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-moderate {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-mild {
        background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-none {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .interpretacion-critica {
        background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ff4444;
    }
    .interpretacion-moderada {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ffaa00;
    }
    .interpretacion-leve {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #44AAFF;
    }
    .interpretacion-normal {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #44FF44;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# CONFIGURACIÓN SUPABASE
# ==================================================

TABLE_NAME = "alertas_hemoglobina"
ALTITUD_TABLE = "altitud_regiones"
CRECIMIENTO_TABLE = "referencia_crecimiento"

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw")

@st.cache_resource
def init_supabase():
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase_client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None

supabase = init_supabase()

# ==================================================
# FUNCIONES DE BASE DE DATOS (CORREGIDAS)
# ==================================================

def obtener_datos_supabase(tabla=TABLE_NAME):
    try:
        if supabase:
            response = supabase.table(tabla).select("*").execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Error obteniendo datos: {response.error}")
                return pd.DataFrame()
            return pd.DataFrame(response.data) if response.data else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error obteniendo datos: {e}")
        return pd.DataFrame()

def obtener_casos_seguimiento():
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").eq("en_seguimiento", True).execute()
            if hasattr(response, 'error') and response.error:
                return pd.DataFrame()
            return pd.DataFrame(response.data) if response.data else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def verificar_duplicado(dni):
    """Verifica si un DNI ya existe en la base de datos"""
    try:
        if supabase:
            response = supabase.table(TABLE_NAME)\
                .select("dni")\
                .eq("dni", dni)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return True
            return False
        return False
    except Exception as e:
        st.error(f"Error verificando duplicado: {e}")
        return False

def insertar_datos_supabase(datos, tabla=TABLE_NAME):
    """Inserta datos en Supabase verificando duplicados"""
    try:
        dni = datos.get("dni")
        
        if not dni:
            st.error("❌ El registro no tiene DNI")
            return None
        
        # Verificar si ya existe
        if verificar_duplicado(dni):
            st.error(f"❌ El DNI {dni} ya existe en la base de datos")
            return {"status": "duplicado", "dni": dni}
        
        # Insertar si no existe
        if supabase:
            response = supabase.table(tabla).insert(datos).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"❌ Error Supabase al insertar: {response.error}")
                st.write("Datos que causaron error:", datos)
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        st.error(f"Error insertando datos: {e}")
        st.write("Datos que causaron error:", datos)
        return None

def upsert_datos_supabase(datos, tabla=TABLE_NAME):
    """Inserta o actualiza datos si ya existen (basado en DNI)"""
    try:
        if supabase:
            response = supabase.table(tabla)\
                .upsert(datos, on_conflict='dni')\
                .execute()
            
            if hasattr(response, 'error') and response.error:
                st.error(f"❌ Error Supabase al hacer upsert: {response.error}")
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        st.error(f"Error haciendo upsert: {e}")
        return None

# ==================================================
# TABLAS DE REFERENCIA Y FUNCIONES DE CÁLCULO
# ==================================================

def obtener_altitud_regiones():
    """Obtiene datos de altitud de regiones desde Supabase"""
    try:
        if supabase:
            response = supabase.table(ALTITUD_TABLE).select("*").execute()
            if response.data:
                return {row['region']: row for row in response.data}
        # Datos de respaldo
        return {
            "AMAZONAS": {"altitud_min": 500, "altitud_max": 3500, "altitud_promedio": 1800},
            "ANCASH": {"altitud_min": 0, "altitud_max": 6768, "altitud_promedio": 3000},
            "APURIMAC": {"altitud_min": 2000, "altitud_max": 4500, "altitud_promedio": 3200},
            "AREQUIPA": {"altitud_min": 0, "altitud_max": 5825, "altitud_promedio": 2500},
            "AYACUCHO": {"altitud_min": 1800, "altitud_max": 4500, "altitud_promedio": 2800},
            "CAJAMARCA": {"altitud_min": 500, "altitud_max": 3500, "altitud_promedio": 2700},
            "CALLAO": {"altitud_min": 0, "altitud_max": 50, "altitud_promedio": 5},
            "CUSCO": {"altitud_min": 500, "altitud_max": 4800, "altitud_promedio": 3400},
            "HUANCAVELICA": {"altitud_min": 2000, "altitud_max": 4500, "altitud_promedio": 3600},
            "HUANUCO": {"altitud_min": 200, "altitud_max": 3800, "altitud_promedio": 1900},
            "ICA": {"altitud_min": 0, "altitud_max": 3800, "altitud_promedio": 500},
            "JUNIN": {"altitud_min": 500, "altitud_max": 4800, "altitud_promedio": 3500},
            "LA LIBERTAD": {"altitud_min": 0, "altitud_max": 4200, "altitud_promedio": 1800},
            "LAMBAYEQUE": {"altitud_min": 0, "altitud_max": 3000, "altitud_promedio": 100},
            "LIMA": {"altitud_min": 0, "altitud_max": 4800, "altitud_promedio": 150},
            "LORETO": {"altitud_min": 70, "altitud_max": 220, "altitud_promedio": 120},
            "MADRE DE DIOS": {"altitud_min": 200, "altitud_max": 500, "altitud_promedio": 250},
            "MOQUEGUA": {"altitud_min": 0, "altitud_max": 4500, "altitud_promedio": 1400},
            "PASCO": {"altitud_min": 1000, "altitud_max": 4400, "altitud_promedio": 3200},
            "PIURA": {"altitud_min": 0, "altitud_max": 3500, "altitud_promedio": 100},
            "PUNO": {"altitud_min": 3800, "altitud_max": 4800, "altitud_promedio": 4100},
            "SAN MARTIN": {"altitud_min": 200, "altitud_max": 3000, "altitud_promedio": 600},
            "TACNA": {"altitud_min": 0, "altitud_max": 3500, "altitud_promedio": 600},
            "TUMBES": {"altitud_min": 0, "altitud_max": 500, "altitud_promedio": 20},
            "UCAYALI": {"altitud_min": 100, "altitud_max": 350, "altitud_promedio": 180}
        }
    except:
        return {}

ALTITUD_REGIONES = obtener_altitud_regiones()

AJUSTE_HEMOGLOBINA = [
    {"altitud_min": 0, "altitud_max": 999, "ajuste": 0.0},
    {"altitud_min": 1000, "altitud_max": 1499, "ajuste": -0.2},
    {"altitud_min": 1500, "altitud_max": 1999, "ajuste": -0.5},
    {"altitud_min": 2000, "altitud_max": 2499, "ajuste": -0.8},
    {"altitud_min": 2500, "altitud_max": 2999, "ajuste": -1.3},
    {"altitud_min": 3000, "altitud_max": 3499, "ajuste": -1.9},
    {"altitud_min": 3500, "altitud_max": 3999, "ajuste": -2.7},
    {"altitud_min": 4000, "altitud_max": 4499, "ajuste": -3.5},
    {"altitud_min": 4500, "altitud_max": 10000, "ajuste": -4.5}
]

def obtener_ajuste_hemoglobina(altitud):
    for ajuste in AJUSTE_HEMOGLOBINA:
        if ajuste["altitud_min"] <= altitud <= ajuste["altitud_max"]:
            return ajuste["ajuste"]
    return 0.0

def calcular_hemoglobina_ajustada(hemoglobina_medida, altitud):
    ajuste = obtener_ajuste_hemoglobina(altitud)
    return hemoglobina_medida + ajuste

# ==================================================
# SISTEMA DE INTERPRETACIÓN AUTOMÁTICA
# ==================================================

def interpretar_analisis_hematologico(ferritina, chcm, reticulocitos, transferrina, hemoglobina_ajustada, edad_meses):
    """Sistema de interpretación automática de parámetros hematológicos"""
    
    interpretacion = ""
    severidad = ""
    recomendacion = ""
    codigo_color = ""
    
    # EVALUAR FERRITINA (Reservas de Hierro)
    if ferritina < 15:
        interpretacion += "🚨 **DEFICIT SEVERO DE HIERRO**. "
        severidad = "CRITICO"
    elif ferritina < 30:
        interpretacion += "⚠️ **DEFICIT MODERADO DE HIERRO**. "
        severidad = "MODERADO"
    elif ferritina < 100:
        interpretacion += "🔄 **RESERVAS DE HIERRO LIMITE**. "
        severidad = "LEVE"
    else:
        interpretacion += "✅ **RESERVAS DE HIERRO ADECUADAS**. "
        severidad = "NORMAL"
    
    # EVALUAR CHCM (Concentración de Hemoglobina)
    if chcm < 32:
        interpretacion += "🚨 **HIPOCROMÍA SEVERA** - Deficiencia avanzada de hierro. "
        severidad = "CRITICO" if severidad != "CRITICO" else severidad
    elif chcm >= 32 and chcm <= 36:
        interpretacion += "✅ **NORMOCROMÍA** - Estado normal. "
    else:
        interpretacion += "🔄 **HIPERCROMÍA** - Posible esferocitosis. "
    
    # EVALUAR RETICULOCITOS (Producción Medular)
    if reticulocitos < 0.5:
        interpretacion += "⚠️ **HIPOPROLIFERACIÓN MEDULAR** - Respuesta insuficiente. "
    elif reticulocitos > 1.5:
        interpretacion += "🔄 **HIPERPRODUCCIÓN COMPENSATORIA** - Respuesta aumentada. "
    else:
        interpretacion += "✅ **PRODUCCIÓN MEDULAR NORMAL**. "
    
    # EVALUAR TRANSFERRINA
    if transferrina < 200:
        interpretacion += "⚠️ **SATURACIÓN BAJA** - Transporte disminuido. "
    elif transferrina > 400:
        interpretacion += "🔄 **SATURACIÓN AUMENTADA** - Compensación por deficiencia. "
    else:
        interpretacion += "✅ **TRANSPORTE ADECUADO**. "
    
    # CLASIFICACIÓN DE ANEMIA BASADA EN HEMOGLOBINA
    clasificacion_hb, _, _ = clasificar_anemia(hemoglobina_ajustada, edad_meses)
    interpretacion += f"📊 **CLASIFICACIÓN HEMOGLOBINA: {clasificacion_hb}**"
    
    # GENERAR RECOMENDACIÓN ESPECÍFICA
    if severidad == "CRITICO":
        recomendacion = "🚨 **INTERVENCIÓN INMEDIATA**: Suplementación con hierro elemental 3-6 mg/kg/día + Control en 15 días + Evaluación médica urgente"
        codigo_color = "#FF4444"
    elif severidad == "MODERADO":
        recomendacion = "⚠️ **ACCIÓN PRIORITARIA**: Iniciar suplementación con hierro + Control mensual + Educación nutricional"
        codigo_color = "#FFAA00"
    elif severidad == "LEVE":
        recomendacion = "🔄 **VIGILANCIA ACTIVA**: Suplementación preventiva + Modificación dietética + Control cada 3 meses"
        codigo_color = "#44AAFF"
    else:
        recomendacion = "✅ **SEGUIMIENTO RUTINARIO**: Mantener alimentación balanceada + Control preventivo cada 6 meses"
        codigo_color = "#44FF44"
    
    return {
        "interpretacion": interpretacion,
        "severidad": severidad,
        "recomendacion": recomendacion,
        "codigo_color": codigo_color,
        "clasificacion_hemoglobina": clasificacion_hb
    }

def generar_parametros_hematologicos(hemoglobina_ajustada, edad_meses):
    """Genera parámetros hematológicos simulados basados en hemoglobina y edad"""
    
    # Basar los parámetros en el nivel de hemoglobina
    if hemoglobina_ajustada < 9.0:
        # Anemia severa - parámetros consistentes con deficiencia
        ferritina = np.random.uniform(5, 15)
        chcm = np.random.uniform(28, 31)
        reticulocitos = np.random.uniform(0.5, 1.0)
        transferrina = np.random.uniform(350, 450)
    elif hemoglobina_ajustada < 11.0:
        # Anemia moderada/leve
        ferritina = np.random.uniform(15, 50)
        chcm = np.random.uniform(31, 33)
        reticulocitos = np.random.uniform(1.0, 1.8)
        transferrina = np.random.uniform(300, 400)
    else:
        # Sin anemia
        ferritina = np.random.uniform(80, 150)
        chcm = np.random.uniform(33, 36)
        reticulocitos = np.random.uniform(0.8, 1.5)
        transferrina = np.random.uniform(200, 350)
    
    # Ajustar VCM y HCM basados en CHCM
    vcm = (chcm / 33) * np.random.uniform(75, 95)
    hcm = (chcm / 33) * np.random.uniform(27, 32)
    
    return {
        'vcm': round(vcm, 1),
        'hcm': round(hcm, 1),
        'chcm': round(chcm, 1),
        'ferritina': round(ferritina, 1),
        'transferrina': round(transferrina, 0),
        'reticulocitos': round(reticulocitos, 1)
    }

# ==================================================
# CLASIFICACIÓN DE ANEMIA Y SEGUIMIENTO
# ==================================================

def clasificar_anemia(hemoglobina_ajustada, edad_meses):
    """Clasifica la anemia según estándares OMS"""
    
    if edad_meses < 24:
        # Menores de 2 años
        if hemoglobina_ajustada >= 11.0:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 10.0 <= hemoglobina_ajustada < 11.0:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 9.0 <= hemoglobina_ajustada < 10.0:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"
    
    elif 24 <= edad_meses < 60:
        # 2 a 5 años
        if hemoglobina_ajustada >= 11.5:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 10.5 <= hemoglobina_ajustada < 11.5:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 9.5 <= hemoglobina_ajustada < 10.5:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"
    
    else:
        # Mayores de 5 años
        if hemoglobina_ajustada >= 12.0:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 11.0 <= hemoglobina_ajustada < 12.0:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 10.0 <= hemoglobina_ajustada < 11.0:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"

def necesita_seguimiento_automatico(hemoglobina_ajustada, edad_meses):
    """Determina si necesita seguimiento automático basado en anemia"""
    clasificacion, _, _ = clasificar_anemia(hemoglobina_ajustada, edad_meses)
    return clasificacion in ["ANEMIA MODERADA", "ANEMIA SEVERA"]

# ==================================================
# FUNCIONES DE EVALUACIÓN NUTRICIONAL
# ==================================================

def obtener_referencia_crecimiento():
    """Obtiene la tabla de referencia de crecimiento desde Supabase"""
    try:
        if supabase:
            response = supabase.table(CRECIMIENTO_TABLE).select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
        # Datos de respaldo
        return pd.DataFrame([
            {'edad_meses': 0, 'peso_min_ninas': 2.8, 'peso_promedio_ninas': 3.4, 'peso_max_ninas': 4.2, 'peso_min_ninos': 2.9, 'peso_promedio_ninos': 3.4, 'peso_max_ninos': 4.4, 'talla_min_ninas': 47.0, 'talla_promedio_ninas': 50.3, 'talla_max_ninas': 53.6, 'talla_min_ninos': 47.5, 'talla_promedio_ninos': 50.3, 'talla_max_ninos': 53.8},
            {'edad_meses': 3, 'peso_min_ninas': 4.5, 'peso_promedio_ninas': 5.6, 'peso_max_ninas': 7.0, 'peso_min_ninos': 5.0, 'peso_promedio_ninos': 6.2, 'peso_max_ninos': 7.8, 'talla_min_ninas': 55.0, 'talla_promedio_ninas': 59.0, 'talla_max_ninas': 63.5, 'talla_min_ninos': 57.0, 'talla_promedio_ninos': 60.0, 'talla_max_ninos': 64.5},
            {'edad_meses': 6, 'peso_min_ninas': 6.0, 'peso_promedio_ninas': 7.3, 'peso_max_ninas': 9.0, 'peso_min_ninos': 6.5, 'peso_promedio_ninos': 8.0, 'peso_max_ninos': 9.8, 'talla_min_ninas': 61.0, 'talla_promedio_ninas': 65.0, 'talla_max_ninas': 69.5, 'talla_min_ninos': 63.0, 'talla_promedio_ninos': 67.0, 'talla_max_ninos': 71.5},
            {'edad_meses': 24, 'peso_min_ninas': 10.5, 'peso_promedio_ninas': 12.4, 'peso_max_ninas': 15.0, 'peso_min_ninos': 11.0, 'peso_promedio_ninos': 12.9, 'peso_max_ninos': 16.0, 'talla_min_ninas': 81.0, 'talla_promedio_ninas': 86.0, 'talla_max_ninas': 92.5, 'talla_min_ninos': 83.0, 'talla_promedio_ninos': 88.0, 'talla_max_ninos': 94.5}
        ])
    except:
        return pd.DataFrame()

def evaluar_estado_nutricional(edad_meses, peso_kg, talla_cm, genero):
    """Evalúa el estado nutricional basado en tablas de referencia OMS"""
    referencia_df = obtener_referencia_crecimiento()
    
    if referencia_df.empty:
        return "Sin datos referencia", "Sin datos referencia", "NUTRICIÓN NO EVALUADA"
    
    # Encontrar referencia para la edad
    referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_meses]
    
    if referencia_edad.empty:
        return "Edad sin referencia", "Edad sin referencia", "NO EVALUABLE"
    
    ref = referencia_edad.iloc[0]
    
    # Determinar valores según género
    if genero == 'F':
        peso_min = ref['peso_min_ninas']
        peso_promedio = ref['peso_promedio_ninas']
        peso_max = ref['peso_max_ninas']
        talla_min = ref['talla_min_ninas']
        talla_promedio = ref['talla_promedio_ninas']
        talla_max = ref['talla_max_ninas']
    else:
        peso_min = ref['peso_min_ninos']
        peso_promedio = ref['peso_promedio_ninos']
        peso_max = ref['peso_max_ninos']
        talla_min = ref['talla_min_ninos']
        talla_promedio = ref['talla_promedio_ninos']
        talla_max = ref['talla_max_ninos']
    
    # Evaluar estado de peso
    if peso_kg < peso_min:
        estado_peso = "BAJO PESO"
    elif peso_kg > peso_max:
        estado_peso = "SOBREPESO"
    else:
        estado_peso = "PESO NORMAL"
    
    # Evaluar estado de talla
    if talla_cm < talla_min:
        estado_talla = "TALLA BAJA"
    elif talla_cm > talla_max:
        estado_talla = "TALLA ALTA"
    else:
        estado_talla = "TALLA NORMAL"
    
    # Evaluar estado nutricional general
    if estado_peso == "BAJO PESO" and estado_talla == "TALLA BAJA":
        estado_nutricional = "DESNUTRICIÓN CRÓNICA"
    elif estado_peso == "BAJO PESO":
        estado_nutricional = "DESNUTRICIÓN AGUDA"
    elif estado_peso == "SOBREPESO":
        estado_nutricional = "SOBREPESO"
    else:
        estado_nutricional = "NUTRICIÓN ADECUADA"
    
    return estado_peso, estado_talla, estado_nutricional

# ==================================================
# LISTAS DE OPCIONES
# ==================================================

PERU_REGIONS = [
    "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", 
    "CAJAMARCA", "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO",
    "ICA", "JUNIN", "LA LIBERTAD", "LAMBAYEQUE", "LIMA", 
    "LORETO", "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA",
    "PUNO", "SAN MARTIN", "TACNA", "TUMBES", "UCAYALI"
]

GENEROS = ["F", "M"]
NIVELES_EDUCATIVOS = ["Sin educación", "Primaria", "Secundaria", "Superior"]
FRECUENCIAS_SUPLEMENTO = ["Diario", "3 veces por semana", "Semanal", "Otra"]
ESTADOS_PACIENTE = ["Activo", "En seguimiento", "Dado de alta", "Inactivo"]

FACTORES_CLINICOS = [
    "Historial familiar de anemia",
    "Bajo peso al nacer (<2500g)",
    "Prematurez (<37 semanas)",
    "Infecciones recurrentes",
    "Parasitosis intestinal",
    "Enfermedades crónicas",
    "Problemas gastrointestinales"
]

FACTORES_SOCIOECONOMICOS = [
    "Bajo nivel educativo de padres",
    "Ingresos familiares reducidos",
    "Hacinamiento en vivienda",
    "Acceso limitado a agua potable",
    "Zona rural o alejada",
    "Trabajo informal o precario"
]

# ==================================================
# FUNCIONES DE CÁLCULO DE RIESGO
# ==================================================

def calcular_riesgo_anemia(hb_ajustada, edad_meses, factores_clinicos, factores_sociales):
    puntaje = 0
    
    if edad_meses < 12:
        if hb_ajustada < 9.0: puntaje += 30
        elif hb_ajustada < 10.0: puntaje += 20
        elif hb_ajustada < 11.0: puntaje += 10
    elif edad_meses < 60:
        if hb_ajustada < 9.5: puntaje += 30
        elif hb_ajustada < 10.5: puntaje += 20
        elif hb_ajustada < 11.5: puntaje += 10
    else:
        if hb_ajustada < 10.0: puntaje += 30
        elif hb_ajustada < 11.0: puntaje += 20
        elif hb_ajustada < 12.0: puntaje += 10
    
    puntaje += len(factores_clinicos) * 4
    puntaje += len(factores_sociales) * 3
    
    if puntaje >= 35:
        return "ALTO RIESGO", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

def generar_sugerencias(riesgo, hemoglobina_ajustada, edad_meses):
    clasificacion, recomendacion, _ = clasificar_anemia(hemoglobina_ajustada, edad_meses)
    
    if clasificacion == "ANEMIA SEVERA":
        return "🚨 INTERVENCIÓN URGENTE: Suplementación inmediata con hierro, evaluación médica en 24-48 horas, control semanal de hemoglobina."
    elif clasificacion == "ANEMIA MODERADA":
        return "⚠️ ACCIÓN PRIORITARIA: Iniciar suplementación con hierro, evaluación médica en 7 días, control mensual."
    elif clasificacion == "ANEMIA LEVE":
        return "📋 SEGUIMIENTO: Educación nutricional, dieta rica en hierro, control cada 3 meses."
    else:
        return "✅ PREVENCIÓN: Mantener alimentación balanceada, control preventivo cada 6 meses."

# ==================================================
# INTERFAZ PRINCIPAL
# ==================================================

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia y Nutrición")
st.markdown("**Sistema integrado con ajuste por altitud y evaluación nutricional**")
st.markdown('</div>', unsafe_allow_html=True)

if supabase:
    st.success("🟢 CONECTADO A SUPABASE")
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE")

# PESTAÑAS PRINCIPALES
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registro Completo", 
    "🔍 Seguimiento Clínico", 
    "📈 Estadísticas",
    "🍎 Evaluación Nutricional",
    "📊 Dashboard Nacional"
])

# ==================================================
# PESTAÑA 1: REGISTRO COMPLETO
# ==================================================

with tab1:
    st.header("📝 Registro Completo de Paciente")
    
    with st.form("formulario_completo"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Datos Personales")
            dni = st.text_input("DNI*", placeholder="Ej: 87654321")
            nombre_completo = st.text_input("Nombre Completo*", placeholder="Ej: Ana García Pérez")
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
            peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1)
            talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1)
            genero = st.selectbox("Género*", GENEROS)
            telefono = st.text_input("Teléfono", placeholder="Ej: 987654321")
            estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE)
        
        with col2:
            st.subheader("🌍 Datos Geográficos")
            region = st.selectbox("Región*", PERU_REGIONS)
            departamento = st.text_input("Departamento/Distrito", placeholder="Ej: Lima Metropolitana")
            
            if region in ALTITUD_REGIONES:
                altitud_info = ALTITUD_REGIONES[region]
                altitud_auto = altitud_info["altitud_promedio"]
                
                st.markdown(f"""
                <div class="altitude-card">
                    <h4>🏔️ Altitud {region}</h4>
                    <p><strong>Rango: {altitud_info['altitud_min']} - {altitud_info['altitud_max']} msnm</strong></p>
                    <p>📊 Promedio: {altitud_info['altitud_promedio']} msnm</p>
                </div>
                """, unsafe_allow_html=True)
                
                altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, altitud_auto)
            else:
                altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, 500)
            
            st.subheader("💰 Factores Socioeconómicos")
            nivel_educativo = st.selectbox("Nivel Educativo", NIVELES_EDUCATIVOS)
            acceso_agua_potable = st.checkbox("Acceso a agua potable")
            tiene_servicio_salud = st.checkbox("Tiene servicio de salud")
        
        st.markdown("---")
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("🩺 Parámetros Clínicos")
            hemoglobina_medida = st.number_input("Hemoglobina medida (g/dL)*", 5.0, 20.0, 11.0, 0.1)
            
            # Calcular hemoglobina ajustada
            ajuste_hb = obtener_ajuste_hemoglobina(altitud_msnm)
            hemoglobina_ajustada = calcular_hemoglobina_ajustada(hemoglobina_medida, altitud_msnm)
            
            # Mostrar clasificación de anemia
            clasificacion, recomendacion, tipo_alerta = clasificar_anemia(hemoglobina_ajustada, edad_meses)
            
            if tipo_alerta == "error":
                st.error(f"**{clasificacion}** - {recomendacion}")
            elif tipo_alerta == "warning":
                st.warning(f"**{clasificacion}** - {recomendacion}")
            else:
                st.success(f"**{clasificacion}** - {recomendacion}")
            
            st.metric(
                "Hemoglobina ajustada al nivel del mar",
                f"{hemoglobina_ajustada:.1f} g/dL",
                f"{ajuste_hb:+.1f} g/dL"
            )
            
            # Determinar seguimiento automático basado en anemia
            necesita_seguimiento = necesita_seguimiento_automatico(hemoglobina_ajustada, edad_meses)
            en_seguimiento = st.checkbox("Marcar para seguimiento activo", value=necesita_seguimiento)
            
            consume_hierro = st.checkbox("Consume suplemento de hierro")
            if consume_hierro:
                tipo_suplemento_hierro = st.text_input("Tipo de suplemento de hierro", placeholder="Ej: Sulfato ferroso")
                frecuencia_suplemento = st.selectbox("Frecuencia de suplemento", FRECUENCIAS_SUPLEMENTO)
            else:
                tipo_suplemento_hierro = ""
                frecuencia_suplemento = ""
            
            antecedentes_anemia = st.checkbox("Antecedentes de anemia")
            enfermedades_cronicas = st.text_area("Enfermedades crónicas", placeholder="Ej: Asma, alergias, etc.")
        
        with col4:
            st.subheader("📋 Factores de Riesgo")
            st.write("🏥 Factores Clínicos")
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS)
            
            st.write("💰 Factores Socioeconómicos")
            factores_sociales = st.multiselect("Seleccione factores sociales:", FACTORES_SOCIOECONOMICOS)
        
        submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GUARDAR", type="primary")
    
    if submitted:
        if not dni or not nombre_completo:
            st.error("❌ Complete DNI y nombre del paciente")
        else:
            # Calcular riesgo usando hemoglobina AJUSTADA
            nivel_riesgo, puntaje, estado = calcular_riesgo_anemia(
                hemoglobina_ajustada,
                edad_meses,
                factores_clinicos,
                factores_sociales
            )
            
            # Generar sugerencias
            sugerencias = generar_sugerencias(nivel_riesgo, hemoglobina_ajustada, edad_meses)
            
            # Evaluación nutricional
            estado_peso, estado_talla, estado_nutricional = evaluar_estado_nutricional(
                edad_meses, peso_kg, talla_cm, genero
            )
            
            # Generar parámetros e interpretación automática
            parametros_simulados = generar_parametros_hematologicos(hemoglobina_ajustada, edad_meses)
            interpretacion_auto = interpretar_analisis_hematologico(
                parametros_simulados['ferritina'],
                parametros_simulados['chcm'],
                parametros_simulados['reticulocitos'], 
                parametros_simulados['transferrina'],
                hemoglobina_ajustada,
                edad_meses
            )
            
            # Mostrar resultados
            st.markdown("---")
            st.subheader("📊 EVALUACIÓN INTEGRAL DEL PACIENTE")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🩺 Estado de Anemia")
                if "ALTO" in nivel_riesgo:
                    st.markdown('<div class="risk-high">', unsafe_allow_html=True)
                elif "MODERADO" in nivel_riesgo:
                    st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-low">', unsafe_allow_html=True)
                
                st.markdown(f"**RIESGO ANEMIA:** {nivel_riesgo}")
                st.markdown(f"**Puntaje:** {puntaje}/60 puntos")
                st.markdown(f"**Alerta:** {estado}")
                st.markdown(f"**Clasificación OMS:** {clasificacion}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🍎 Estado Nutricional")
                st.markdown(f"**Peso:** {estado_peso}")
                st.markdown(f"**Talla:** {estado_talla}")
                st.markdown(f"**Estado Nutricional:** {estado_nutricional}")
                st.markdown(f"**Seguimiento activo:** {'SÍ' if en_seguimiento else 'NO'}")
            
            # INTERPRETACIÓN HEMATOLÓGICA AUTOMÁTICA
            st.markdown("### 🔬 Interpretación Hematológica Automática")
            
            # Aplicar estilo según severidad
            if interpretacion_auto['severidad'] == "CRITICO":
                st.markdown(f'<div class="interpretacion-critica">', unsafe_allow_html=True)
            elif interpretacion_auto['severidad'] == "MODERADO":
                st.markdown(f'<div class="interpretacion-moderada">', unsafe_allow_html=True)
            elif interpretacion_auto['severidad'] == "LEVE":
                st.markdown(f'<div class="interpretacion-leve">', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="interpretacion-normal">', unsafe_allow_html=True)
            
            st.markdown(f"**📋 Análisis Integrado - {interpretacion_auto['severidad']}**")
            st.markdown(f"**Interpretación:** {interpretacion_auto['interpretacion']}")
            st.markdown(f"**💡 Plan Específico:** {interpretacion_auto['recomendacion']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar parámetros simulados
            st.markdown("### 🧪 Parámetros Hematológicos Estimados")
            col_param1, col_param2, col_param3 = st.columns(3)
            with col_param1:
                st.metric("Ferritina", f"{parametros_simulados['ferritina']} ng/mL")
                st.metric("CHCM", f"{parametros_simulados['chcm']} g/dL")
            with col_param2:
                st.metric("Transferrina", f"{parametros_simulados['transferrina']} mg/dL")
                st.metric("VCM", f"{parametros_simulados['vcm']} fL")
            with col_param3:
                st.metric("Reticulocitos", f"{parametros_simulados['reticulocitos']} %")
                st.metric("HCM", f"{parametros_simulados['hcm']} pg")
            
            # SUGERENCIAS
            st.markdown("### 💡 Plan de Acción General")
            st.info(sugerencias)
            
            # ============================================
            # GUARDAR EN SUPABASE CON VERIFICACIÓN DE DUPLICADOS
            # ============================================
            if supabase:
                with st.spinner("Verificando y guardando datos..."):
                    # Crear el registro completo
                    record = {
                        "dni": dni.strip(),
                        "nombre_apellido": nombre_completo.strip(),
                        "edad_meses": int(edad_meses),
                        "peso_kg": float(peso_kg),
                        "talla_cm": float(talla_cm),
                        "genero": genero,
                        "telefono": telefono.strip() if telefono else None,
                        "estado_paciente": estado_paciente,
                        "region": region,
                        "departamento": departamento.strip() if departamento else None,
                        "altitud_msnm": int(altitud_msnm),
                        "nivel_educativo": nivel_educativo,
                        "acceso_agua_potable": acceso_agua_potable,
                        "tiene_servicio_salud": tiene_servicio_salud,
                        "hemoglobina_dl1": float(hemoglobina_medida),
                        "en_seguimiento": en_seguimiento,
                        "consumir_hierro": consume_hierro,
                        "tipo_suplemento_hierro": tipo_suplemento_hierro.strip() if consume_hierro and tipo_suplemento_hierro else None,
                        "frecuencia_suplemento": frecuencia_suplemento if consume_hierro else None,
                        "antecedentes_anemia": antecedentes_anemia,
                        "enfermedades_cronicas": enfermedades_cronicas.strip() if enfermedades_cronicas else None,
                        "interpretacion_hematologica": interpretacion_auto['interpretacion'],
                        "politicas_de_ris": region,
                        "riesgo": nivel_riesgo,
                        "fecha_alerta": datetime.now().strftime("%Y-%m-%d"),
                        "estado_alerta": estado,
                        "sugerencias": sugerencias,
                        "severidad_interpretacion": interpretacion_auto['severidad']
                    }
                    
                    # Insertar usando la función que verifica duplicados
                    resultado = insertar_datos_supabase(record)
                    
                    if resultado:
                        if isinstance(resultado, dict) and resultado.get("status") == "duplicado":
                            st.error(f"❌ El DNI {dni} ya existe en la base de datos")
                            st.info("Por favor, use un DNI diferente o edite el registro existente")
                        else:
                            st.success("✅ Datos guardados en Supabase correctamente")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error("❌ Error al guardar en Supabase")
            else:
                st.error("🔴 No hay conexión a Supabase")

# ==================================================
# PESTAÑA 2: SEGUIMIENTO CLÍNICO
# ==================================================

with tab2:
    st.header("🔍 Seguimiento Clínico por Gravedad")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Casos que Requieren Seguimiento")
        
        if st.button("🔄 Actualizar casos prioritarios"):
            with st.spinner("Analizando gravedad de casos..."):
                # Obtener todos los pacientes
                todos_pacientes = obtener_datos_supabase()
                
                if not todos_pacientes.empty:
                    # Calcular hemoglobina ajustada y clasificar
                    pacientes_analizados = todos_pacientes.copy()
                    
                    analisis_data = []
                    for _, paciente in pacientes_analizados.iterrows():
                        hb_ajustada = calcular_hemoglobina_ajustada(
                            paciente.get('hemoglobina_dl1', 0), 
                            paciente.get('altitud_msnm', 0)
                        )
                        
                        clasificacion, recomendacion, _ = clasificar_anemia(hb_ajustada, paciente.get('edad_meses', 0))
                        
                        analisis = {
                            'nombre_apellido': paciente.get('nombre_apellido', 'N/A'),
                            'edad_meses': paciente.get('edad_meses', 0),
                            'hemoglobina_dl1': paciente.get('hemoglobina_dl1', 0),
                            'hb_ajustada': hb_ajustada,
                            'clasificacion_anemia': clasificacion,
                            'recomendacion_seguimiento': recomendacion,
                            'region': paciente.get('region', 'No especificada'),
                            'fecha_alerta': paciente.get('fecha_alerta', 'N/D')
                        }
                        analisis_data.append(analisis)
                    
                    analisis_df = pd.DataFrame(analisis_data)
                    
                    # Filtrar solo los que necesitan seguimiento (moderado + severo)
                    casos_seguimiento = analisis_df[
                        analisis_df['clasificacion_anemia'].isin(["ANEMIA MODERADA", "ANEMIA SEVERA"])
                    ]
                    
                    if not casos_seguimiento.empty:
                        st.success(f"🚨 {len(casos_seguimiento)} casos requieren seguimiento activo")
                        
                        # Ordenar por gravedad (severa primero)
                        orden_gravedad = {"ANEMIA SEVERA": 1, "ANEMIA MODERADA": 2}
                        casos_seguimiento['orden'] = casos_seguimiento['clasificacion_anemia'].map(orden_gravedad)
                        casos_seguimiento = casos_seguimiento.sort_values('orden').drop('orden', axis=1)
                        
                        # Mostrar tabla
                        st.dataframe(
                            casos_seguimiento,
                            use_container_width=True,
                            height=400,
                            column_config={
                                'nombre_apellido': 'Paciente',
                                'edad_meses': 'Edad (meses)',
                                'hemoglobina_dl1': st.column_config.NumberColumn('Hb Medida (g/dL)', format='%.1f'),
                                'hb_ajustada': st.column_config.NumberColumn('Hb Ajustada (g/dL)', format='%.1f'),
                                'clasificacion_anemia': 'Gravedad',
                                'recomendacion_seguimiento': 'Seguimiento',
                                'region': 'Región',
                                'fecha_alerta': 'Fecha'
                            }
                        )
                        
                        # Métricas de gravedad
                        st.subheader("📊 Distribución por Gravedad")
                        severos = len(casos_seguimiento[casos_seguimiento['clasificacion_anemia'] == "ANEMIA SEVERA"])
                        moderados = len(casos_seguimiento[casos_seguimiento['clasificacion_anemia'] == "ANEMIA MODERADA"])
                        
                        col_met1, col_met2, col_met3 = st.columns(3)
                        with col_met1:
                            st.metric("🟥 Severos", severos)
                        with col_met2:
                            st.metric("🟨 Moderados", moderados)
                        with col_met3:
                            st.metric("📅 Total Prioridad", len(casos_seguimiento))
                        
                    else:
                        st.success("✅ No hay casos que requieran seguimiento activo")
                        st.info("""
                        **Todos los pacientes tienen:**
                        - Anemia leve o sin anemia
                        - Seguimiento rutinario cada 3-6 meses
                        - No requieren intervención urgente
                        """)
                else:
                    st.info("📝 No hay pacientes registrados en el sistema")
    
    with col2:
        st.subheader("🎯 Criterios de Seguimiento")
        
        st.markdown("""
        <div class="severity-critical">
        <h4>🚨 ANEMIA SEVERA</h4>
        <p><strong>Seguimiento:</strong> Urgente semanal</p>
        <p><strong>Acción:</strong> Suplementación inmediata + Control médico</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="severity-moderate">
        <h4>⚠️ ANEMIA MODERADA</h4>
        <p><strong>Seguimiento:</strong> Mensual</p>
        <p><strong>Acción:</strong> Suplementación + Monitoreo</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="severity-mild">
        <h4>✅ ANEMIA LEVE</h4>
        <p><strong>Seguimiento:</strong> Cada 3 meses</p>
        <p><strong>Acción:</strong> Educación nutricional</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="severity-none">
        <h4>💚 SIN ANEMIA</h4>
        <p><strong>Seguimiento:</strong> Cada 6 meses</p>
        <p><strong>Acción:</strong> Prevención</p>
        </div>
        """, unsafe_allow_html=True)

    # SECCIÓN: ANÁLISIS HEMATOLÓGICO COMPLETO CON INTERPRETACIÓN
    st.markdown("---")
    st.header("🔬 Análisis Hematológico Completo con Interpretación")
    
    if st.button("🧪 Generar Análisis Hematológico Avanzado"):
        with st.spinner("Procesando parámetros hematológicos con interpretación automática..."):
            todos_pacientes = obtener_datos_supabase()
            
            if not todos_pacientes.empty:
                # Calcular todos los parámetros con interpretación
                analisis_data = []
                interpretaciones_data = []
                
                for _, paciente in todos_pacientes.iterrows():
                    hb_ajustada = calcular_hemoglobina_ajustada(
                        paciente.get('hemoglobina_dl1', 0), 
                        paciente.get('altitud_msnm', 0)
                    )
                    
                    clasificacion, recomendacion, _ = clasificar_anemia(hb_ajustada, paciente.get('edad_meses', 0))
                    
                    # Generar parámetros hematológicos realistas
                    parametros = generar_parametros_hematologicos(hb_ajustada, paciente.get('edad_meses', 0))
                    
                    # Generar interpretación automática
                    interpretacion = interpretar_analisis_hematologico(
                        parametros['ferritina'],
                        parametros['chcm'], 
                        parametros['reticulocitos'],
                        parametros['transferrina'],
                        hb_ajustada,
                        paciente.get('edad_meses', 0)
                    )
                    
                    # Datos para tabla principal
                    analisis = {
                        'paciente': paciente.get('nombre_apellido', 'N/A'),
                        'edad_meses': paciente.get('edad_meses', 0),
                        'hb_medida': paciente.get('hemoglobina_dl1', 0),
                        'hb_ajustada': hb_ajustada,
                        'clasificacion': clasificacion,
                        'vcm': parametros['vcm'],
                        'hcm': parametros['hcm'],
                        'chcm': parametros['chcm'],
                        'ferritina': parametros['ferritina'],
                        'transferrina': parametros['transferrina'],
                        'reticulocitos': parametros['reticulocitos'],
                        'recomendacion': recomendacion,
                        'severidad': interpretacion['severidad']
                    }
                    analisis_data.append(analisis)
                    
                    # Datos para sección de interpretación
                    interpretaciones_data.append({
                        'paciente': paciente.get('nombre_apellido', 'N/A'),
                        'interpretacion': interpretacion['interpretacion'],
                        'recomendacion_especifica': interpretacion['recomendacion'],
                        'severidad': interpretacion['severidad'],
                        'color_alerta': interpretacion['codigo_color']
                    })
                
                analisis_df = pd.DataFrame(analisis_data)
                interpretaciones_df = pd.DataFrame(interpretaciones_data)
                
                st.success(f"🧪 {len(analisis_df)} análisis hematológicos con interpretación generados")
                
                # MOSTRAR TABLA PRINCIPAL DE PARÁMETROS
                st.subheader("📊 Parámetros Hematológicos")
                st.dataframe(
                    analisis_df,
                    use_container_width=True,
                    height=400,
                    column_config={
                        'paciente': 'Paciente',
                        'edad_meses': 'Edad (meses)',
                        'hb_medida': st.column_config.NumberColumn('Hb Medida', format='%.1f g/dL'),
                        'hb_ajustada': st.column_config.NumberColumn('Hb Ajustada', format='%.1f g/dL'),
                        'clasificacion': 'Clasificación',
                        'vcm': st.column_config.NumberColumn('VCM', format='%.1f fL'),
                        'hcm': st.column_config.NumberColumn('HCM', format='%.1f pg'),
                        'chcm': st.column_config.NumberColumn('CHCM', format='%.1f g/dL'),
                        'ferritina': st.column_config.NumberColumn('Ferritina', format='%.1f ng/mL'),
                        'transferrina': st.column_config.NumberColumn('Transferrina', format='%.0f mg/dL'),
                        'reticulocitos': st.column_config.NumberColumn('Reticulocitos', format='%.1f %%'),
                        'recomendacion': 'Recomendación',
                        'severidad': 'Severidad'
                    }
                )
                
                # MOSTRAR INTERPRETACIONES DETALLADAS
                st.subheader("🎯 Interpretación Clínica Automática")
                
                for _, interpretacion in interpretaciones_df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="border-left: 5px solid {interpretacion['color_alerta']}; 
                                    padding: 1rem; margin: 1rem 0; 
                                    background-color: #f8f9fa; border-radius: 5px;">
                            <h4>👤 {interpretacion['paciente']} - <span style="color: {interpretacion['color_alerta']}">{interpretacion['severidad']}</span></h4>
                            <p><strong>Interpretación:</strong> {interpretacion['interpretacion']}</p>
                            <p><strong>Plan de Acción:</strong> {interpretacion['recomendacion_especifica']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # GRÁFICO DE DISTRIBUCIÓN POR SEVERIDAD
                st.subheader("📈 Distribución por Nivel de Severidad")
                distribucion_severidad = analisis_df['severidad'].value_counts()
                
                fig_severidad = px.pie(
                    values=distribucion_severidad.values,
                    names=distribucion_severidad.index,
                    title="Distribución de Pacientes por Severidad",
                    color=distribucion_severidad.index,
                    color_discrete_map={
                        'CRITICO': '#FF4444',
                        'MODERADO': '#FFAA00', 
                        'LEVE': '#44AAFF',
                        'NORMAL': '#44FF44'
                    }
                )
                st.plotly_chart(fig_severidad, use_container_width=True)
                
            else:
                st.info("📝 No hay pacientes registrados para análisis")

# ==================================================
# PESTAÑA 3: ESTADÍSTICAS AVANZADAS CON PLOTLY
# ==================================================

with tab3:
    st.header("📊 Dashboard Estadístico Avanzado")
    
    # Toggle para mostrar explicaciones
    mostrar_explicaciones = st.checkbox("ℹ️ Mostrar explicaciones de métricas", value=True)
    
    if st.button("🚀 Cargar análisis estadístico completo", type="primary"):
        with st.spinner("🔍 Analizando datos y generando visualizaciones..."):
            datos_completos = obtener_datos_supabase()
        
        if not datos_completos.empty:
            st.success(f"✅ {len(datos_completos)} registros analizados")
            
            # ========== KPI PRINCIPALES CON TARJETAS COLORES ==========
            st.subheader("🎯 KPIs Principales")
            
            # Fila 1 de KPIs
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                total_casos = len(datos_completos)
                st.metric(
                    label="Total de Casos",
                    value=f"{total_casos:,}",
                    delta=None,
                    delta_color="normal",
                    help="Número total de pacientes registrados"
                )
                if mostrar_explicaciones:
                    st.caption("👥 Total de registros en la base de datos")
            
            with kpi2:
                if 'en_seguimiento' in datos_completos.columns:
                    en_seguimiento = len(datos_completos[datos_completos['en_seguimiento'] == True])
                    porcentaje_seguimiento = (en_seguimiento / total_casos * 100) if total_casos > 0 else 0
                    
                    # Determinar color del delta
                    delta_color = "normal"
                    if porcentaje_seguimiento < 30:
                        delta_color = "inverse"
                    elif porcentaje_seguimiento > 70:
                        delta_color = "normal"
                    
                    st.metric(
                        label="En Seguimiento",
                        value=en_seguimiento,
                        delta=f"{porcentaje_seguimiento:.1f}%",
                        delta_color=delta_color
                    )
                    if mostrar_explicaciones:
                        st.caption(f"📋 {porcentaje_seguimiento:.1f}% del total")
            
            with kpi3:
                if 'hemoglobina_dl1' in datos_completos.columns:
                    avg_hemoglobina = datos_completos['hemoglobina_dl1'].mean()
                    
                    # Determinar estado
                    if avg_hemoglobina < 1.2:
                        delta_color = "inverse"
                        estado = "🔴 Crítico"
                    elif avg_hemoglobina < 1.5:
                        delta_color = "off"
                        estado = "🟡 Atención"
                    else:
                        delta_color = "normal"
                        estado = "🟢 Normal"
                    
                    st.metric(
                        label="Hb Promedio",
                        value=f"{avg_hemoglobina:.1f} g/dL",
                        delta=estado,
                        delta_color=delta_color
                    )
                    if mostrar_explicaciones:
                        st.caption("📊 Media de hemoglobina en todos los pacientes")
            
            with kpi4:
                if 'riesgo' in datos_completos.columns:
                    alto_riesgo = len(datos_completos[datos_completos['riesgo'].str.contains('ALTO', na=False)])
                    
                    st.metric(
                        label="Alto Riesgo",
                        value=alto_riesgo,
                        delta=f"{(alto_riesgo/total_casos*100):.1f}%",
                        delta_color="inverse" if (alto_riesgo/total_casos*100) > 20 else "normal"
                    )
                    if mostrar_explicaciones:
                        st.caption("⚠️ Pacientes que requieren atención prioritaria")
            
            # Fila 2 de KPIs
            kpi5, kpi6, kpi7, kpi8 = st.columns(4)
            
            with kpi5:
                if 'edad' in datos_completos.columns:
                    avg_edad = datos_completos['edad'].mean()
                    st.metric("Edad Promedio", f"{avg_edad:.1f} años")
                    if mostrar_explicaciones:
                        st.caption("👵👶 Distribución etaria promedio")
            
            with kpi6:
                if 'genero' in datos_completos.columns:
                    mujeres = len(datos_completos[datos_completos['genero'].str.contains('F|Mujer', na=False, case=False)])
                    porcentaje_mujeres = (mujeres / total_casos * 100) if total_casos > 0 else 0
                    st.metric("Mujeres", mujeres, f"{porcentaje_mujeres:.1f}%")
                    if mostrar_explicaciones:
                        st.caption("👩 Distribución por género")
            
            with kpi7:
                # Tasa de anemia (Hb < 1.2)
                if 'hemoglobina_dl1' in datos_completos.columns:
                    tasa_anemia = len(datos_completos[datos_completos['hemoglobina_dl1'] < 1.2]) / total_casos * 100
                    st.metric("Tasa Anemia", f"{tasa_anemia:.1f}%")
                    if mostrar_explicaciones:
                        st.caption("🩸 Porcentaje con Hb < 1.2 g/dL")
            
            with kpi8:
                # Completitud de datos
                completitud = datos_completos.notna().mean().mean() * 100
                st.metric("Calidad Datos", f"{completitud:.1f}%")
                if mostrar_explicaciones:
                    st.caption("📈 Porcentaje de campos completados")
            
            # ========== VISUALIZACIONES CON PLOTLY ==========
            st.subheader("📊 Visualizaciones Avanzadas")
            
            # --- GRÁFICO 1: DISTRIBUCIÓN POR REGIÓN CON PLOTLY ---
            if 'region' in datos_completos.columns:
                distribucion_region = datos_completos['region'].value_counts().reset_index()
                distribucion_region.columns = ['Region', 'Casos']
                
                # Ordenar por cantidad
                distribucion_region = distribucion_region.sort_values('Casos', ascending=True)
                
                import plotly.express as px
                
                fig1 = px.bar(
                    distribucion_region,
                    x='Casos',
                    y='Region',
                    orientation='h',
                    title='<b>📌 Distribución de Casos por Región</b>',
                    color='Casos',
                    color_continuous_scale=px.colors.sequential.Viridis,
                    text='Casos',
                    height=400
                )
                
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=12),
                    xaxis_title="Número de Casos",
                    yaxis_title="Región",
                    showlegend=False
                )
                
                fig1.update_traces(
                    texttemplate='%{text} casos',
                    textposition='outside',
                    marker_line_color='black',
                    marker_line_width=1
                )
                
                st.plotly_chart(fig1, use_container_width=True)
            
            # --- GRÁFICO 2: DISTRIBUCIÓN DE RIESGO CON DONUT CHART ---
            if 'riesgo' in datos_completos.columns:
                distribucion_riesgo = datos_completos['riesgo'].value_counts().reset_index()
                distribucion_riesgo.columns = ['Nivel_Riesgo', 'Cantidad']
                
                # Mapear colores según riesgo
                color_map = {
                    'ALTO': '#FF6B6B',
                    'MEDIO': '#FFD166',
                    'MODERADO': '#FFD166',
                    'BAJO': '#06D6A0'
                }
                
                distribucion_riesgo['Color'] = distribucion_riesgo['Nivel_Riesgo'].apply(
                    lambda x: color_map.get(str(x).upper().split()[0] if isinstance(x, str) else 'OTRO', '#8E8E8E')
                )
                
                fig2 = px.pie(
                    distribucion_riesgo,
                    values='Cantidad',
                    names='Nivel_Riesgo',
                    title='<b>⚠️ Distribución por Nivel de Riesgo</b>',
                    color='Nivel_Riesgo',
                    color_discrete_map={
                        k: v for k, v in color_map.items() 
                        if k in distribucion_riesgo['Nivel_Riesgo'].astype(str).str.upper().values
                    },
                    hole=0.4,  # Donut chart
                    height=400
                )
                
                fig2.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    marker=dict(line=dict(color='white', width=2))
                )
                
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # --- GRÁFICO 3: HISTOGRAMA DE HEMOGLOBINA CON KDE ---
            if 'hemoglobina_dl1' in datos_completos.columns:
                hb_data = datos_completos['hemoglobina_dl1'].dropna()
                
                if len(hb_data) > 0:
                    fig3 = px.histogram(
                        hb_data,
                        x=hb_data,
                        nbins=20,
                        title='<b>🩸 Distribución de Hemoglobina</b>',
                        labels={'x': 'Hemoglobina (g/dL)', 'y': 'Frecuencia'},
                        color_discrete_sequence=['#36A2EB'],
                        opacity=0.8,
                        marginal="box",  # Box plot arriba
                        height=500
                    )
                    
                    # Añadir líneas de referencia
                    fig3.add_vline(
                        x=1.2, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="Umbral Anemia (1.2 g/dL)",
                        annotation_position="top right"
                    )
                    
                    fig3.add_vline(
                        x=hb_data.mean(), 
                        line_dash="dot", 
                        line_color="green",
                        annotation_text=f"Media: {hb_data.mean():.2f} g/dL",
                        annotation_position="top left"
                    )
                    
                    fig3.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(gridcolor='lightgray'),
                        yaxis=dict(gridcolor='lightgray'),
                        bargap=0.1
                    )
                    
                    st.plotly_chart(fig3, use_container_width=True)
            
            # --- GRÁFICO 4: CORRELACIÓN EDAD vs HEMOGLOBINA ---
            if 'edad' in datos_completos.columns and 'hemoglobina_dl1' in datos_completos.columns:
                # Filtrar datos completos
                scatter_data = datos_completos[['edad', 'hemoglobina_dl1']].dropna()
                
                if len(scatter_data) > 10:  # Solo si hay suficientes datos
                    fig4 = px.scatter(
                        scatter_data,
                        x='edad',
                        y='hemoglobina_dl1',
                        title='<b>📈 Correlación: Edad vs Hemoglobina</b>',
                        labels={'edad': 'Edad (años)', 'hemoglobina_dl1': 'Hemoglobina (g/dL)'},
                        trendline="lowess",
                        trendline_color_override="red",
                        color_discrete_sequence=['#FF6384'],
                        height=500
                    )
                    
                    # Añadir línea horizontal de referencia
                    fig4.add_hline(
                        y=1.2,
                        line_dash="dash",
                        line_color="orange",
                        annotation_text="Límite Anemia"
                    )
                    
                    fig4.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(gridcolor='lightgray'),
                        yaxis=dict(gridcolor='lightgray')
                    )
                    
                    st.plotly_chart(fig4, use_container_width=True)
                    
                    # Calcular y mostrar correlación
                    correlacion = scatter_data['edad'].corr(scatter_data['hemoglobina_dl1'])
                    st.metric("Correlación Edad-Hb", f"{correlacion:.3f}")
            
            # --- GRÁFICO 5: EVOLUCIÓN TEMPORAL (si hay fecha) ---
            if 'fecha_registro' in datos_completos.columns:
                try:
                    datos_completos['fecha'] = pd.to_datetime(datos_completos['fecha_registro']).dt.date
                    evolucion = datos_completos.groupby('fecha').size().reset_index()
                    evolucion.columns = ['Fecha', 'Casos']
                    evolucion = evolucion.sort_values('Fecha')
                    
                    if len(evolucion) > 1:
                        fig5 = px.line(
                            evolucion,
                            x='Fecha',
                            y='Casos',
                            title='<b>📅 Evolución Temporal de Casos</b>',
                            markers=True,
                            line_shape='spline',
                            color_discrete_sequence=['#9966FF'],
                            height=400
                        )
                        
                        # Añadir área sombreada
                        fig5.add_scatter(
                            x=evolucion['Fecha'],
                            y=evolucion['Casos'],
                            fill='tozeroy',
                            fillcolor='rgba(153, 102, 255, 0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            showlegend=False
                        )
                        
                        fig5.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(gridcolor='lightgray'),
                            yaxis=dict(gridcolor='lightgray')
                        )
                        
                        st.plotly_chart(fig5, use_container_width=True)
                except:
                    pass
            
            # ========== TABLAS RESUMEN AVANZADAS ==========
            st.subheader("📋 Tablas de Resumen")
            
            # Tabla 1: Estadísticas descriptivas
            if 'hemoglobina_dl1' in datos_completos.columns:
                col_tab1, col_tab2 = st.columns(2)
                
                with col_tab1:
                    st.write("**📊 Estadísticas de Hemoglobina**")
                    
                    stats_hb = {
                        'Estadístico': ['Media', 'Mediana', 'Desviación Estándar', 
                                      'Mínimo', 'Máximo', 'Percentil 25', 'Percentil 75',
                                      'Coef. Variación', 'Rango Intercuartil'],
                        'Valor (g/dL)': [
                            f"{datos_completos['hemoglobina_dl1'].mean():.2f}",
                            f"{datos_completos['hemoglobina_dl1'].median():.2f}",
                            f"{datos_completos['hemoglobina_dl1'].std():.2f}",
                            f"{datos_completos['hemoglobina_dl1'].min():.2f}",
                            f"{datos_completos['hemoglobina_dl1'].max():.2f}",
                            f"{datos_completos['hemoglobina_dl1'].quantile(0.25):.2f}",
                            f"{datos_completos['hemoglobina_dl1'].quantile(0.75):.2f}",
                            f"{(datos_completos['hemoglobina_dl1'].std()/datos_completos['hemoglobina_dl1'].mean()*100):.1f}%" if datos_completos['hemoglobina_dl1'].mean() > 0 else "N/A",
                            f"{(datos_completos['hemoglobina_dl1'].quantile(0.75)-datos_completos['hemoglobina_dl1'].quantile(0.25)):.2f}"
                        ]
                    }
                    
                    stats_hb_df = pd.DataFrame(stats_hb)
                    st.dataframe(stats_hb_df, use_container_width=True, hide_index=True)
                
                with col_tab2:
                    st.write("**📈 Categorías de Hemoglobina**")
                    
                    categorias_hb = {
                        'Categoría': ['Anemia Severa (<1.0)', 'Anemia Moderada (1.0-1.19)', 
                                     'Normal Bajo (1.2-1.49)', 'Normal (≥1.5)'],
                        'Rango (g/dL)': ['< 1.0', '1.0 - 1.19', '1.2 - 1.49', '≥ 1.5'],
                        'Casos': [
                            len(datos_completos[datos_completos['hemoglobina_dl1'] < 1.0]),
                            len(datos_completos[(datos_completos['hemoglobina_dl1'] >= 1.0) & 
                                               (datos_completos['hemoglobina_dl1'] < 1.2)]),
                            len(datos_completos[(datos_completos['hemoglobina_dl1'] >= 1.2) & 
                                               (datos_completos['hemoglobina_dl1'] < 1.5)]),
                            len(datos_completos[datos_completos['hemoglobina_dl1'] >= 1.5])
                        ]
                    }
                    
                    categorias_hb_df = pd.DataFrame(categorias_hb)
                    categorias_hb_df['%'] = (categorias_hb_df['Casos'] / total_casos * 100).round(1).astype(str) + '%'
                    st.dataframe(categorias_hb_df, use_container_width=True, hide_index=True)
            
            # ========== DATOS COMPLETOS CON FILTROS ==========
            st.subheader("🗃️ Datos Completos con Filtros")
            
            # Filtros interactivos
            col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
            
            with col_filtro1:
                if 'riesgo' in datos_completos.columns:
                    riesgo_options = ['Todos'] + list(datos_completos['riesgo'].dropna().unique())
                    filtro_riesgo = st.selectbox("Filtrar por riesgo:", riesgo_options)
            
            with col_filtro2:
                if 'region' in datos_completos.columns:
                    region_options = ['Todas'] + list(datos_completos['region'].dropna().unique())
                    filtro_region = st.selectbox("Filtrar por región:", region_options)
            
            with col_filtro3:
                if 'hemoglobina_dl1' in datos_completos.columns:
                    filtro_hb = st.slider(
                        "Filtrar por hemoglobina mínima:",
                        min_value=float(datos_completos['hemoglobina_dl1'].min()),
                        max_value=float(datos_completos['hemoglobina_dl1'].max()),
                        value=float(datos_completos['hemoglobina_dl1'].min())
                    )
            
            # Aplicar filtros
            datos_filtrados = datos_completos.copy()
            
            if 'riesgo' in datos_completos.columns and filtro_riesgo != 'Todos':
                datos_filtrados = datos_filtrados[datos_filtrados['riesgo'] == filtro_riesgo]
            
            if 'region' in datos_completos.columns and filtro_region != 'Todas':
                datos_filtrados = datos_filtrados[datos_filtrados['region'] == filtro_region]
            
            if 'hemoglobina_dl1' in datos_completos.columns:
                datos_filtrados = datos_filtrados[datos_filtrados['hemoglobina_dl1'] >= filtro_hb]
            
            st.info(f"📊 Mostrando {len(datos_filtrados)} de {len(datos_completos)} registros")
            
            # Botón de descarga
            csv = datos_filtrados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Descargar datos filtrados (CSV)",
                data=csv,
                file_name="datos_filtrados.csv",
                mime="text/csv",
                type="secondary"
            )
            
            # Mostrar datos filtrados
            st.dataframe(
                datos_filtrados,
                use_container_width=True,
                height=400,
                column_config={
                    "hemoglobina_dl1": st.column_config.NumberColumn(
                        "Hemoglobina",
                        help="Nivel de hemoglobina en g/dL",
                        format="%.2f g/dL"
                    ),
                    "edad": st.column_config.NumberColumn(
                        "Edad",
                        help="Edad en años",
                        format="%d años"
                    )
                }
            )
            
            # ========== RESUMEN FINAL ==========
            with st.expander("📝 Resumen Ejecutivo del Análisis"):
                st.write("### 🔍 Hallazgos Principales")
                
                col_res1, col_res2 = st.columns(2)
                
                with col_res1:
                    st.write("**📈 Tendencias Identificadas:**")
                    
                    if 'hemoglobina_dl1' in datos_completos.columns:
                        tasa_anemia = len(datos_completos[datos_completos['hemoglobina_dl1'] < 1.2]) / total_casos * 100
                        
                        if tasa_anemia > 30:
                            st.error(f"🚨 **ALERTA:** Tasa de anemia del {tasa_anemia:.1f}% (supera el 30%)")
                        elif tasa_anemia > 15:
                            st.warning(f"⚠️ **ATENCIÓN:** Tasa de anemia del {tasa_anemia:.1f}% (entre 15-30%)")
                        else:
                            st.success(f"✅ **ESTABLE:** Tasa de anemia del {tasa_anemia:.1f}% (por debajo del 15%)")
                    
                    st.write(f"• **Total de pacientes:** {total_casos:,}")
                    st.write(f"• **En seguimiento:** {en_seguimiento} ({porcentaje_seguimiento:.1f}%)")
                    st.write(f"• **Calidad de datos:** {completitud:.1f}%")
                
                with col_res2:
                    st.write("**🎯 Recomendaciones:**")
                    st.write("1. **Priorizar seguimiento** a pacientes de alto riesgo")
                    st.write("2. **Reforzar recolección** en regiones con menos datos")
                    st.write("3. **Implementar alertas** para Hb < 1.2 g/dL")
                    st.write("4. **Analizar causas** de variación por región")
                    
        else:
            st.warning("📭 No hay datos disponibles para el análisis")
            
            # Mostrar datos de ejemplo
            if st.checkbox("Mostrar datos de ejemplo para probar visualizaciones"):
                # Crear datos de ejemplo
                import numpy as np
                import pandas as pd
                
                np.random.seed(42)
                ejemplo_data = pd.DataFrame({
                    'region': np.random.choice(['Norte', 'Sur', 'Este', 'Oeste'], 100),
                    'hemoglobina_dl1': np.random.normal(1.3, 0.3, 100),
                    'edad': np.random.randint(18, 80, 100),
                    'riesgo': np.random.choice(['ALTO', 'MEDIO', 'BAJO'], 100, p=[0.2, 0.3, 0.5]),
                    'en_seguimiento': np.random.choice([True, False], 100, p=[0.7, 0.3]),
                    'genero': np.random.choice(['M', 'F'], 100)
                })
                
                st.dataframe(ejemplo_data.head(10))
                st.info("Estos son datos de ejemplo para probar las visualizaciones")
    
    else:
        # Pantalla inicial
        st.info("👆 **Presiona el botón azul arriba** para cargar el análisis estadístico completo")
        
        st.markdown("""
        ### 📊 ¿Qué incluye este dashboard?
        
        | Característica | Descripción |
        |----------------|-------------|
        | **🎯 KPIs Coloridos** | Métricas con colores según estado (rojo/amarillo/verde) |
        | **📈 Gráficos Interactivos** | Gráficos que puedes hacer zoom y explorar |
        | **🔄 Filtros en Tiempo Real** | Filtra los datos según tus necesidades |
        | **📊 Análisis Estadístico** | Media, mediana, desviación, correlaciones |
        | **💾 Exportación de Datos** | Descarga los datos filtrados en CSV |
        | **📝 Resumen Ejecutivo** | Hallazgos y recomendaciones automáticas |
        
        ### 🎨 Características Visuales:
        - Colores diferenciados por categoría
        - Gráficos responsivos
        - Indicadores visuales de alerta
        - Tooltips informativos
        - Diseño moderno y profesional
        """)
# ==================================================
# PESTAÑA 4: EVALUACIÓN NUTRICIONAL
# ==================================================

with tab4:
    st.header("🍎 Evaluación Nutricional Individual")
    
    with st.form("evaluacion_nutricional"):
        st.subheader("Datos del Paciente para Evaluación")
        col1, col2 = st.columns(2)
        
        with col1:
            edad_eval = st.number_input("Edad (meses)", 1, 240, 24, key="eval_edad")
            peso_eval = st.number_input("Peso (kg)", 0.0, 50.0, 12.5, 0.1, key="eval_peso")
            talla_eval = st.number_input("Talla (cm)", 0.0, 150.0, 85.0, 0.1, key="eval_talla")
            genero_eval = st.selectbox("Género", GENEROS, key="eval_genero")
        
        with col2:
            hemoglobina_eval = st.number_input("Hemoglobina (g/dL)", 5.0, 20.0, 11.0, 0.1, key="eval_hb")
            altitud_eval = st.number_input("Altitud (msnm)", 0, 5000, 150, key="eval_altitud")
        
        submitted_eval = st.form_submit_button("📊 EVALUAR ESTADO NUTRICIONAL")
    
    if submitted_eval:
        # Calcular hemoglobina ajustada
        ajuste_hb_eval = obtener_ajuste_hemoglobina(altitud_eval)
        hb_ajustada_eval = hemoglobina_eval + ajuste_hb_eval
        
        # Evaluación nutricional
        estado_peso, estado_talla, estado_nutricional = evaluar_estado_nutricional(
            edad_eval, peso_eval, talla_eval, genero_eval
        )
        
        # Clasificación de anemia
        clasificacion, recomendacion, _ = clasificar_anemia(hb_ajustada_eval, edad_eval)
        
        # Generar interpretación automática con parámetros simulados
        parametros_simulados = generar_parametros_hematologicos(hb_ajustada_eval, edad_eval)
        interpretacion_auto = interpretar_analisis_hematologico(
            parametros_simulados['ferritina'],
            parametros_simulados['chcm'],
            parametros_simulados['reticulocitos'], 
            parametros_simulados['transferrina'],
            hb_ajustada_eval,
            edad_eval
        )
        
        # Mostrar resultados
        st.markdown("---")
        st.subheader("📋 Resultados de la Evaluación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🩺 Parámetros Hematológicos")
            st.metric("Hemoglobina medida", f"{hemoglobina_eval:.1f} g/dL")
            st.metric("Ajuste por altitud", f"{ajuste_hb_eval:+.1f} g/dL")
            st.metric("Hemoglobina ajustada", f"{hb_ajustada_eval:.1f} g/dL", delta=f"{ajuste_hb_eval:+.1f}")
            st.metric("Clasificación OMS", clasificacion)
            
            # Mostrar parámetros hematológicos estimados
            st.markdown("#### 🧪 Parámetros Hematológicos Estimados")
            st.metric("Ferritina", f"{parametros_simulados['ferritina']} ng/mL")
            st.metric("CHCM", f"{parametros_simulados['chcm']} g/dL")
            st.metric("Reticulocitos", f"{parametros_simulados['reticulocitos']} %")
        
        with col2:
            st.markdown("### 🍎 Parámetros Nutricionales")
            st.metric("Estado de Peso", estado_peso)
            st.metric("Estado de Talla", estado_talla)
            st.metric("Estado Nutricional", estado_nutricional)
            st.metric("Recomendación", recomendacion)
            
            # Mostrar más parámetros hematológicos
            st.markdown("#### 🔬 Más Parámetros")
            st.metric("VCM", f"{parametros_simulados['vcm']} fL")
            st.metric("HCM", f"{parametros_simulados['hcm']} pg")
            st.metric("Transferrina", f"{parametros_simulados['transferrina']} mg/dL")
        
        # INTERPRETACIÓN AUTOMÁTICA
        st.markdown("### 🎯 Interpretación Hematológica Automática")
        
        # Aplicar estilo según severidad
        if interpretacion_auto['severidad'] == "CRITICO":
            st.markdown(f'<div class="interpretacion-critica">', unsafe_allow_html=True)
        elif interpretacion_auto['severidad'] == "MODERADO":
            st.markdown(f'<div class="interpretacion-moderada">', unsafe_allow_html=True)
        elif interpretacion_auto['severidad'] == "LEVE":
            st.markdown(f'<div class="interpretacion-leve">', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="interpretacion-normal">', unsafe_allow_html=True)
        
        st.markdown(f"**📋 Análisis Integrado - {interpretacion_auto['severidad']}**")
        st.markdown(f"**Interpretación:** {interpretacion_auto['interpretacion']}")
        st.markdown(f"**💡 Plan Específico:** {interpretacion_auto['recomendacion']}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tabla de referencia
        st.subheader("📊 Tablas de Referencia OMS")
        referencia_df = obtener_referencia_crecimiento()
        if not referencia_df.empty:
            st.dataframe(referencia_df, use_container_width=True, height=300)
        else:
            st.info("No se pudieron cargar las tablas de referencia")

# ==================================================
# PESTAÑA 5: DASHBOARD NACIONAL
# ==================================================

with tab5:
    st.header("📊 Dashboard Nacional de Anemia y Nutrición")
    
    if st.button("🔄 Actualizar Dashboard Nacional"):
        with st.spinner("Cargando datos nacionales..."):
            datos_nacionales = obtener_datos_supabase()
        
        if not datos_nacionales.empty:
            st.success(f"✅ Dashboard actualizado con {len(datos_nacionales)} registros")
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_pacientes = len(datos_nacionales)
                st.metric("Total Pacientes", total_pacientes)
            
            with col2:
                # Calcular casos que necesitan seguimiento
                casos_seguimiento = 0
                for _, paciente in datos_nacionales.iterrows():
                    hb_ajustada = calcular_hemoglobina_ajustada(
                        paciente.get('hemoglobina_dl1', 0), 
                        paciente.get('altitud_msnm', 0)
                    )
                    if necesita_seguimiento_automatico(hb_ajustada, paciente.get('edad_meses', 0)):
                        casos_seguimiento += 1
                st.metric("Necesitan Seguimiento", casos_seguimiento)
            
            with col3:
                avg_hemoglobina = datos_nacionales['hemoglobina_dl1'].mean()
                st.metric("Hemoglobina Promedio", f"{avg_hemoglobina:.1f} g/dL")
            
            with col4:
                regiones_activas = datos_nacionales['region'].nunique()
                st.metric("Regiones Activas", regiones_activas)
            
            # Gráficos simples
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución por región
                if 'region' in datos_nacionales.columns:
                    distribucion_region = datos_nacionales['region'].value_counts()
                    st.bar_chart(distribucion_region)
            
            with col2:
                # Distribución por edad
                if 'edad_meses' in datos_nacionales.columns:
                    fig_edad = px.histogram(datos_nacionales, x='edad_meses', title='Distribución por Edad')
                    st.plotly_chart(fig_edad, use_container_width=True)
            
        else:
            st.info("📝 No hay datos suficientes para el dashboard nacional")

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.header("📋 Sistema de Referencia")
    
    tab_sidebar1, tab_sidebar2, tab_sidebar3 = st.tabs(["🎯 Ajustes Altitud", "📊 Tablas Crecimiento", "🔬 Criterios Hematológicos"])
    
    with tab_sidebar1:
        st.markdown("**Tabla de Ajustes por Altitud:**")
        ajustes_df = pd.DataFrame(AJUSTE_HEMOGLOBINA)
        st.dataframe(
            ajustes_df.style.format({
                'altitud_min': '{:.0f}',
                'altitud_max': '{:.0f}', 
                'ajuste': '{:+.1f}'
            }),
            use_container_width=True,
            height=300
        )
    
    with tab_sidebar2:
        st.markdown("**Tablas de Crecimiento OMS:**")
        referencia_df = obtener_referencia_crecimiento()
        if not referencia_df.empty:
            st.dataframe(referencia_df, use_container_width=True, height=300)
        else:
            st.info("Cargando tablas de referencia...")
    
    with tab_sidebar3:
        st.markdown("**Criterios de Interpretación:**")
        
        st.markdown("""
        ### 🩺 FERRITINA (Reservas)
        - **< 15 ng/mL**: 🚨 Deficit severo
        - **15-30 ng/mL**: ⚠️ Deficit moderado  
        - **30-100 ng/mL**: 🔄 Reservas límite
        - **> 100 ng/mL**: ✅ Adecuado
        
        ### 🔬 CHCM (Concentración)
        - **< 32 g/dL**: 🚨 Hipocromía
        - **32-36 g/dL**: ✅ Normocromía
        - **> 36 g/dL**: 🔄 Hipercromía
        
        ### 📈 RETICULOCITOS (Producción)
        - **< 0.5%**: ⚠️ Hipoproliferación
        - **0.5-1.5%**: ✅ Normal
        - **> 1.5%**: 🔄 Hiperproducción
        
        ### 🚨 NIVELES DE SEVERIDAD
        - **CRÍTICO**: Intervención inmediata
        - **MODERADO**: Acción prioritaria  
        - **LEVE**: Vigilancia activa
        - **NORMAL**: Seguimiento rutinario
        """)
    
    st.markdown("---")
    st.info("""
    **💡 Sistema Integrado:**
    - ✅ Ajuste automático por altitud
    - ✅ Clasificación OMS de anemia
    - ✅ Seguimiento por gravedad
    - ✅ Evaluación nutricional
    - ✅ Dashboard nacional
    - ✅ **NUEVO: Interpretación automática**
    - ✅ **CORREGIDO: Manejo de duplicados**
    """)

# ==================================================
# INICIALIZACIÓN DE DATOS DE PRUEBA (OPCIONAL)
# ==================================================

if supabase:
    try:
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        if not response.data:
            st.sidebar.info("🔄 Base de datos vacía. Puede ingresar pacientes desde la pestaña 'Registro Completo'")
            
            # Opcional: Insertar un paciente de prueba automáticamente
            if st.sidebar.button("➕ Insertar paciente de prueba"):
                with st.sidebar.spinner("Insertando..."):
                    paciente_prueba = {
                        "dni": "87654321",
                        "nombre_apellido": "Carlos López Díaz",
                        "edad_meses": 36,
                        "peso_kg": 14.5,
                        "talla_cm": 95.0,
                        "genero": "M",
                        "telefono": "987123456",
                        "estado_paciente": "Activo",
                        "region": "LIMA",
                        "departamento": "Lima Centro",
                        "altitud_msnm": 150,
                        "nivel_educativo": "Secundaria",
                        "acceso_agua_potable": True,
                        "tiene_servicio_salud": True,
                        "hemoglobina_dl1": 10.5,
                        "en_seguimiento": True,
                        "consumir_hierro": True,
                        "tipo_suplemento_hierro": "Sulfato ferroso",
                        "frecuencia_suplemento": "Diario",
                        "antecedentes_anemia": False,
                        "enfermedades_cronicas": "Ninguna",
                        "interpretacion_hematologica": "Anemia leve por deficiencia de hierro",
                        "politicas_de_ris": "LIMA",
                        "riesgo": "RIESGO MODERADO",
                        "fecha_alerta": datetime.now().strftime("%Y-%m-%d"),
                        "estado_alerta": "EN SEGUIMIENTO",
                        "sugerencias": "Suplementación con hierro y control mensual",
                        "severidad_interpretacion": "LEVE"
                    }
                    
                    resultado = insertar_datos_supabase(paciente_prueba)
                    if resultado:
                        st.sidebar.success("✅ Paciente de prueba insertado")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Error al insertar paciente de prueba")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error verificando datos: {e}")

# ==================================================
# PIE DE PÁGINA
# ==================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🏥 <strong>Sistema Nixon</strong> - Control de Anemia y Nutrición Infantil</p>
    <p>📅 Versión 2.0 | Última actualización: """ + datetime.now().strftime("%d/%m/%Y") + """</p>
    <p>⚠️ <em>Para uso médico profesional. Consulte siempre con especialistas.</em></p>
</div>
""", unsafe_allow_html=True)
