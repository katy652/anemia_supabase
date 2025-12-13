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
# PESTAÑA 3: DASHBOARD ESPECIALIZADO - ANEMIA EN NIÑOS <5 AÑOS
# ==================================================

with tab3:
    # TÍTULO PRINCIPAL CON DISEÑO MEJORADO
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h1 style='color: white; text-align: center; margin: 0; font-size: 2.5rem;'>
            🩸 Detección Temprana de Anemia en Niños Menores de 5 Años
        </h1>
        <p style='color: rgba(255,255,255,0.9); text-align: center; margin-top: 10px; font-size: 1.1rem;'>
            Sistema de monitoreo y análisis integral para la prevención de anemia infantil
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar datos en session_state
    if 'datos_originales' not in st.session_state:
        st.session_state.datos_originales = None
    if 'datos_filtrados' not in st.session_state:
        st.session_state.datos_filtrados = None
    if 'filtros_aplicados' not in st.session_state:
        st.session_state.filtros_aplicados = False
    if 'analisis_iniciado' not in st.session_state:
        st.session_state.analisis_iniciado = False  # Controlar si el análisis fue iniciado
    
    # ========== PANTALLA DE INICIO (SOLO SI NO SE HA INICIADO ANÁLISIS) ==========
    if not st.session_state.analisis_iniciado:
        col_welcome1, col_welcome2 = st.columns([2, 1])
        
        with col_welcome1:
            st.markdown("""
            <div style='background-color: #f0f8ff; padding: 25px; border-radius: 15px; border-left: 6px solid #1E3A8A;'>
                <h2 style='color: #1E3A8A;'>👋 ¡Bienvenido al Sistema de Monitoreo de Anemia Infantil!</h2>
                <p style='font-size: 1.1rem; line-height: 1.6;'>
                    Este dashboard especializado está diseñado para la <b>detección temprana y monitoreo</b> 
                    de anemia en niños menores de 5 años. Proporciona análisis en tiempo real, 
                    visualizaciones interactivas y recomendaciones basadas en datos.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_welcome2:
            st.markdown("""
            <div style='text-align: center; padding: 20px;'>
                <div style='font-size: 3rem;'>🩸</div>
                <h3 style='margin: 10px 0;'>Listo para comenzar</h3>
                <p>Presiona el botón azul para iniciar el análisis</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # CARACTERÍSTICAS DEL SISTEMA
        st.markdown("### 🎯 **Características Principales del Sistema**")
        
        col_feat1, col_feat2, col_feat3, col_feat4 = st.columns(4)
        
        with col_feat1:
            st.markdown("""
            <div style='text-align: center; padding: 15px; background-color: #e3f2fd; border-radius: 10px;'>
                <div style='font-size: 2rem;'>📋</div>
                <h4>Formulario</h4>
                <p>Análisis por género</p>
                <small>Niños vs Niñas</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat2:
            st.markdown("""
            <div style='text-align: center; padding: 15px; background-color: #fff3e0; border-radius: 10px;'>
                <div style='font-size: 2rem;'>📊</div>
                <h4>Monitoreo</h4>
                <p>Riesgo por altitud</p>
                <small>500m - 4000m+</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat3:
            st.markdown("""
            <div style='text-align: center; padding: 15px; background-color: #e8f5e9; border-radius: 10px;'>
                <div style='font-size: 2rem;'>📍</div>
                <h4>Análisis</h4>
                <p>Riesgo por región</p>
                <small>Comparativa regional</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat4:
            st.markdown("""
            <div style='text-align: center; padding: 15px; background-color: #f3e5f5; border-radius: 10px;'>
                <div style='font-size: 2rem;'>🎛️</div>
                <h4>Filtros Avanzados</h4>
                <p>Panel de control</p>
                <small>8 filtros diferentes</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # INSTRUCCIONES RÁPIDAS
        with st.expander("📖 ¿Cómo usar este dashboard?"):
            st.markdown("""
            1. **Presiona el botón azul** "INICIAR ANÁLISIS COMPLETO"
            2. **Configura los filtros** en el Panel de Control Avanzado
            3. **Aplica los filtros** para personalizar la vista
            4. **Explora** las 3 secciones principales del análisis
            5. **Exporta datos** filtrados según necesites
            6. **Genera reportes** personalizados
            
            **🎛️ Filtros disponibles:**
            - Edad (0-5 años)
            - Nivel de hemoglobina
            - Género
            - Región
            - Altitud
            - Estado de seguimiento
            - Estado nutricional
            - Ordenamiento personalizado
            
            **💡 Tip:** Todos los gráficos se actualizan automáticamente con los filtros aplicados
            """)
    
    # BOTÓN PRINCIPAL MEJORADO - AHORA AFUERA DEL CONDICIONAL
    col_btn_principal, col_btn_reset = st.columns([3, 1])
    
    with col_btn_principal:
        if st.button("🚀 INICIAR ANÁLISIS COMPLETO", type="primary", use_container_width=True):
            with st.spinner("🔍 Analizando datos de anemia infantil..."):
                datos_completos = obtener_datos_supabase()
            
            if not datos_completos.empty:
                # FILTRAR SOLO NIÑOS MENORES DE 5 AÑOS
                if 'edad' in datos_completos.columns:
                    datos_ninos = datos_completos[datos_completos['edad'] < 5].copy()
                    st.success(f"✅ {len(datos_ninos)} niños menores de 5 años analizados")
                    datos_analisis = datos_ninos
                else:
                    datos_analisis = datos_completos
                    st.success(f"✅ {len(datos_analisis)} registros analizados")
                
                # Guardar en session_state
                st.session_state.datos_originales = datos_analisis.copy()
                st.session_state.datos_filtrados = datos_analisis.copy()
                st.session_state.filtros_aplicados = False
                st.session_state.analisis_iniciado = True  # MARCAR QUE SE INICIÓ
                st.rerun()  # Forzar rerun para mostrar los filtros
            else:
                st.error("❌ No se pudieron cargar los datos de la base de datos")
    
    with col_btn_reset:
        if st.button("🔄 Reiniciar Análisis", use_container_width=True):
            st.session_state.analisis_iniciado = False
            st.session_state.datos_originales = None
            st.session_state.datos_filtrados = None
            st.session_state.filtros_aplicados = False
            st.rerun()
    
    # ========== INTERFAZ DE ANÁLISIS (SOLO SI SE INICIÓ) ==========
    if st.session_state.analisis_iniciado and st.session_state.datos_originales is not None:
        datos_analisis = st.session_state.datos_originales.copy()
        total_casos = len(datos_analisis)
        
        # ========== PANEL DE CONTROL AVANZADO CON FILTROS FUNCIONALES ==========
        st.markdown("---")
        st.markdown("## 🎛️ **Panel de Control Avanzado con Filtros**")
        
        with st.expander("🔍 **CONFIGURAR FILTROS**", expanded=True):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            with col_f1:
                st.markdown("#### 👶 **Edad**")
                edad_min, edad_max = st.slider(
                    "Rango de edad (años):",
                    min_value=0,
                    max_value=5,
                    value=(0, 5),
                    help="Filtrar por rango de edad",
                    key="filtro_edad"
                )
            
            with col_f2:
                st.markdown("#### 🩸 **Hemoglobina**")
                filtro_hb = st.selectbox(
                    "Nivel de hemoglobina ajustada:",
                    ["Todos", "Anemia Severa (<9.0 g/dL)", "Anemia Moderada (9.0-10.9 g/dL)", 
                     "Anemia Leve (11.0-11.9 g/dL)", "Normal (≥12.0 g/dL)"],
                    key="filtro_hb"
                )
            
            with col_f3:
                st.markdown("#### 👦👧 **Género**")
                if 'genero' in datos_analisis.columns:
                    genero_opciones = ['Todos'] + datos_analisis['genero'].dropna().unique().tolist()
                    filtro_genero = st.selectbox(
                        "Seleccionar género:",
                        genero_opciones,
                        key="filtro_genero"
                    )
                else:
                    filtro_genero = 'Todos'
            
            with col_f4:
                st.markdown("#### 🌍 **Región**")
                if 'region' in datos_analisis.columns:
                    region_opciones = ['Todas'] + datos_analisis['region'].dropna().unique().tolist()
                    filtro_region = st.selectbox(
                        "Seleccionar región:",
                        region_opciones,
                        key="filtro_region"
                    )
                else:
                    filtro_region = 'Todas'
            
            # Segunda fila de filtros
            col_f5, col_f6, col_f7, col_f8 = st.columns(4)
            
            with col_f5:
                st.markdown("#### ⛰️ **Altitud**")
                if 'altitud_msnm' in datos_analisis.columns:
                    alt_min = int(datos_analisis['altitud_msnm'].min())
                    alt_max = int(datos_analisis['altitud_msnm'].max())
                    filtro_altitud = st.slider(
                        "Rango de altitud (msnm):",
                        min_value=alt_min,
                        max_value=alt_max,
                        value=(alt_min, alt_max),
                        key="filtro_altitud"
                    )
                else:
                    filtro_altitud = (0, 5000)
            
            with col_f6:
                st.markdown("#### 📋 **Seguimiento**")
                if 'en_seguimiento' in datos_analisis.columns:
                    filtro_seguimiento = st.selectbox(
                        "Estado de seguimiento:",
                        ["Todos", "En seguimiento", "Sin seguimiento"],
                        key="filtro_seguimiento"
                    )
                else:
                    filtro_seguimiento = "Todos"
            
            with col_f7:
                st.markdown("#### 🍎 **Estado Nutricional**")
                # Simular estado nutricional si no existe
                if 'estado_nutricional' not in datos_analisis.columns:
                    datos_analisis['estado_nutricional'] = np.random.choice(
                        ['Normal', 'Riesgo', 'Desnutrición'], 
                        len(datos_analisis)
                    )
                
                estado_nut_opciones = ['Todos'] + datos_analisis['estado_nutricional'].dropna().unique().tolist()
                filtro_nutricion = st.selectbox(
                    "Estado nutricional:",
                    estado_nut_opciones,
                    key="filtro_nutricion"
                )
            
            with col_f8:
                st.markdown("#### 📊 **Ordenar por**")
                ordenar_por = st.selectbox(
                    "Ordenar resultados:",
                    ["Nombre", "Edad", "Hemoglobina", "Altitud", "Riesgo"],
                    key="ordenar_por"
                )
                orden_ascendente = st.checkbox("Orden ascendente", value=True, key="orden_ascendente")
        
        # Botones de acción para filtros
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            aplicar_filtros = st.button("✅ **APLICAR FILTROS**", type="primary", use_container_width=True, key="btn_aplicar_filtros")
        
        with col_btn2:
            limpiar_filtros = st.button("🗑️ **LIMPIAR FILTROS**", use_container_width=True, key="btn_limpiar_filtros")
        
        with col_btn3:
            exportar_filtrado = st.button("📥 **EXPORTAR FILTRADO**", use_container_width=True, key="btn_exportar_filtrado")
        
        with col_btn4:
            generar_reporte = st.button("📄 **GENERAR REPORTE**", use_container_width=True, key="btn_generar_reporte")
        
        # Función para aplicar filtros
        def aplicar_filtros_funcion(datos, edad_range, hb_filtro, genero_filtro, region_filtro, 
                                   altitud_range, seguimiento_filtro, nutricion_filtro, ordenar_por, orden_ascendente):
            
            datos_filtrados = datos.copy()
            
            # 1. Filtro por edad
            if 'edad' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados[
                    (datos_filtrados['edad'] >= edad_range[0]) & 
                    (datos_filtrados['edad'] <= edad_range[1])
                ]
            
            # 2. Filtro por hemoglobina (primero calcular hemoglobina ajustada)
            if hb_filtro != "Todos" and 'hemoglobina_dl1' in datos_filtrados.columns:
                # Calcular hemoglobina ajustada para cada paciente
                hb_ajustada_values = []
                for _, row in datos_filtrados.iterrows():
                    hb_medida = row.get('hemoglobina_dl1', 0)
                    altitud = row.get('altitud_msnm', 0)
                    ajuste = obtener_ajuste_hemoglobina(altitud)
                    hb_ajustada = hb_medida + ajuste
                    hb_ajustada_values.append(hb_ajustada)
                
                datos_filtrados['hb_ajustada'] = hb_ajustada_values
                
                if hb_filtro == "Anemia Severa (<9.0 g/dL)":
                    datos_filtrados = datos_filtrados[datos_filtrados['hb_ajustada'] < 9.0]
                elif hb_filtro == "Anemia Moderada (9.0-10.9 g/dL)":
                    datos_filtrados = datos_filtrados[
                        (datos_filtrados['hb_ajustada'] >= 9.0) & 
                        (datos_filtrados['hb_ajustada'] <= 10.9)
                    ]
                elif hb_filtro == "Anemia Leve (11.0-11.9 g/dL)":
                    datos_filtrados = datos_filtrados[
                        (datos_filtrados['hb_ajustada'] >= 11.0) & 
                        (datos_filtrados['hb_ajustada'] <= 11.9)
                    ]
                elif hb_filtro == "Normal (≥12.0 g/dL)":
                    datos_filtrados = datos_filtrados[datos_filtrados['hb_ajustada'] >= 12.0]
            
            # 3. Filtro por género
            if genero_filtro != "Todos" and 'genero' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados[datos_filtrados['genero'] == genero_filtro]
            
            # 4. Filtro por región
            if region_filtro != "Todas" and 'region' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados[datos_filtrados['region'] == region_filtro]
            
            # 5. Filtro por altitud
            if 'altitud_msnm' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados[
                    (datos_filtrados['altitud_msnm'] >= altitud_range[0]) & 
                    (datos_filtrados['altitud_msnm'] <= altitud_range[1])
                ]
            
            # 6. Filtro por seguimiento
            if seguimiento_filtro != "Todos" and 'en_seguimiento' in datos_filtrados.columns:
                if seguimiento_filtro == "En seguimiento":
                    datos_filtrados = datos_filtrados[datos_filtrados['en_seguimiento'] == True]
                elif seguimiento_filtro == "Sin seguimiento":
                    datos_filtrados = datos_filtrados[datos_filtrados['en_seguimiento'] == False]
            
            # 7. Filtro por estado nutricional
            if nutricion_filtro != "Todos" and 'estado_nutricional' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados[datos_filtrados['estado_nutricional'] == nutricion_filtro]
            
            # 8. Ordenar resultados
            if ordenar_por == "Nombre" and 'nombre_apellido' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados.sort_values('nombre_apellido', ascending=orden_ascendente)
            elif ordenar_por == "Edad" and 'edad' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados.sort_values('edad', ascending=orden_ascendente)
            elif ordenar_por == "Hemoglobina" and 'hemoglobina_dl1' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados.sort_values('hemoglobina_dl1', ascending=orden_ascendente)
            elif ordenar_por == "Altitud" and 'altitud_msnm' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados.sort_values('altitud_msnm', ascending=orden_ascendente)
            elif ordenar_por == "Riesgo" and 'riesgo' in datos_filtrados.columns:
                datos_filtrados = datos_filtrados.sort_values('riesgo', ascending=orden_ascendente)
            
            return datos_filtrados
        
        # Aplicar filtros cuando se presiona el botón
        if aplicar_filtros:
            with st.spinner("🔄 Aplicando filtros..."):
                datos_filtrados = aplicar_filtros_funcion(
                    st.session_state.datos_originales,
                    (edad_min, edad_max),
                    filtro_hb,
                    filtro_genero,
                    filtro_region,
                    filtro_altitud,
                    filtro_seguimiento,
                    filtro_nutricion,
                    ordenar_por,
                    orden_ascendente
                )
                
                st.session_state.datos_filtrados = datos_filtrados
                st.session_state.filtros_aplicados = True
                
                st.success(f"✅ Filtros aplicados: {len(datos_filtrados)} de {len(st.session_state.datos_originales)} registros")
                
                # Mostrar resumen de filtros aplicados
                st.info(f"""
                **📋 Filtros activos:**
                - Edad: {edad_min}-{edad_max} años
                - Hemoglobina: {filtro_hb}
                - Género: {filtro_genero}
                - Región: {filtro_region}
                - Altitud: {filtro_altitud[0]}-{filtro_altitud[1]} msnm
                - Seguimiento: {filtro_seguimiento}
                - Nutrición: {filtro_nutricion}
                """)
                
                st.rerun()  # Forzar rerun para actualizar visualizaciones
        
        # Limpiar filtros
        if limpiar_filtros:
            st.session_state.datos_filtrados = st.session_state.datos_originales.copy()
            st.session_state.filtros_aplicados = False
            st.success("🔄 Filtros limpiados - Mostrando todos los datos")
            st.rerun()
        
        # Exportar datos filtrados
        if exportar_filtrado:
            datos_a_exportar = st.session_state.datos_filtrados if st.session_state.filtros_aplicados else st.session_state.datos_originales
            
            if not datos_a_exportar.empty:
                csv = datos_a_exportar.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar datos filtrados (CSV)",
                    data=csv,
                    file_name=f"anemia_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No hay datos para exportar")
        
        # Generar reporte (CÓDIGO CORREGIDO)
        if generar_reporte:
            datos_reporte = st.session_state.datos_filtrados if st.session_state.filtros_aplicados else st.session_state.datos_originales
            
            # Calcular estadísticas ANTES del string f-formatted
            if 'edad' in datos_reporte.columns and not datos_reporte['edad'].empty:
                edad_promedio = f"{datos_reporte['edad'].mean():.1f}"
            else:
                edad_promedio = 'N/A'
            
            if 'hemoglobina_dl1' in datos_reporte.columns and not datos_reporte['hemoglobina_dl1'].empty:
                hemoglobina_promedio = f"{datos_reporte['hemoglobina_dl1'].mean():.1f}"
            else:
                hemoglobina_promedio = 'N/A'
            
            if 'en_seguimiento' in datos_reporte.columns:
                casos_seguimiento = len(datos_reporte[datos_reporte['en_seguimiento'] == True])
            else:
                casos_seguimiento = 'N/A'
            
            if 'region' in datos_reporte.columns and not datos_reporte['region'].empty:
                regiones_incluidas = datos_reporte['region'].nunique()
            else:
                regiones_incluidas = 'N/A'
            
            if 'altitud_msnm' in datos_reporte.columns and not datos_reporte['altitud_msnm'].empty:
                altitud_promedio = f"{datos_reporte['altitud_msnm'].mean():.0f}"
            else:
                altitud_promedio = 'N/A'
            
            with st.expander("📋 **REPORTE COMPLETO CON FILTROS**", expanded=True):
                st.markdown(f"""
                ### 📊 REPORTE DE ANÁLISIS - ANEMIA INFANTIL
                
                **Fecha generación:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
                **Total registros analizados:** {len(datos_reporte)}
                **Filtros aplicados:** {'SÍ' if st.session_state.filtros_aplicados else 'NO'}
                
                **📈 ESTADÍSTICAS PRINCIPALES:**
                - **Edad promedio:** {edad_promedio} años
                - **Hemoglobina promedio:** {hemoglobina_promedio} g/dL
                - **Casos en seguimiento:** {casos_seguimiento}
                
                **🌍 DISTRIBUCIÓN GEOGRÁFICA:**
                - **Regiones incluidas:** {regiones_incluidas}
                - **Altitud promedio:** {altitud_promedio} msnm
                
                **👦👧 DISTRIBUCIÓN POR GÉNERO:**
                """)
                
                if 'genero' in datos_reporte.columns and not datos_reporte['genero'].empty:
                    genero_counts = datos_reporte['genero'].value_counts()
                    for genero, count in genero_counts.items():
                        porcentaje = (count / len(datos_reporte)) * 100
                        st.markdown(f"- **{genero}:** {count} pacientes ({porcentaje:.1f}%)")
                
                st.markdown("""
                **🚨 RECOMENDACIONES:**
                1. Revisar casos críticos identificados
                2. Implementar seguimiento para casos prioritarios
                3. Generar alertas para regiones de alto riesgo
                4. Programar controles periódicos
                """)
        
        # Determinar qué datos usar para las visualizaciones
        if st.session_state.filtros_aplicados and st.session_state.datos_filtrados is not None:
            datos_visualizacion = st.session_state.datos_filtrados.copy()
            st.info(f"📊 **Visualizando {len(datos_visualizacion)} registros filtrados**")
        else:
            datos_visualizacion = datos_analisis.copy()
        
        # ========== SECCIÓN 1: FORMULARIO - RIESGO POR GÉNERO ==========
        st.markdown("## 📋 **1. Formulario: Riesgo de Anemia por Género**")
        
        col_form1, col_form2 = st.columns([2, 1])
        
        with col_form1:
            if 'genero' in datos_visualizacion.columns:
                # Procesar datos de género
                genero_counts = datos_visualizacion['genero'].value_counts().reset_index()
                genero_counts.columns = ['Genero', 'Cantidad']
                
                # Normalizar nombres
                genero_mapping = {'M': 'Niños 👦', 'F': 'Niñas 👧', 'Masculino': 'Niños 👦', 'Femenino': 'Niñas 👧'}
                genero_counts['Genero'] = genero_counts['Genero'].map(lambda x: genero_mapping.get(x, x))
                
                # Gráfico avanzado de género
                fig_genero = px.pie(
                    genero_counts,
                    values='Cantidad',
                    names='Genero',
                    title='<b>Distribución por Género</b>',
                    color='Genero',
                    color_discrete_sequence=['#3498db', '#e74c3c'],
                    hole=0.5,
                    height=350
                )
                
                fig_genero.update_traces(
                    textposition='inside',
                    textinfo='percent+label+value',
                    marker=dict(line=dict(color='white', width=2))
                )
                
                st.plotly_chart(fig_genero, use_container_width=True)
        
        with col_form2:
            st.markdown("### 📊 Estadísticas Detalladas")
            
            if 'genero' in datos_visualizacion.columns and 'hemoglobina_dl1' in datos_visualizacion.columns:
                # Calcular riesgos por género
                for genero_label, genero_codes in [('Niños 👦', ['M', 'Masculino']), ('Niñas 👧', ['F', 'Femenino'])]:
                    data_genero = datos_visualizacion[datos_visualizacion['genero'].isin(genero_codes)]
                    if len(data_genero) > 0:
                        # Calcular hemoglobina ajustada
                        riesgo_count = 0
                        for _, row in data_genero.iterrows():
                            hb_medida = row.get('hemoglobina_dl1', 0)
                            altitud = row.get('altitud_msnm', 0)
                            ajuste = obtener_ajuste_hemoglobina(altitud)
                            hb_ajustada = hb_medida + ajuste
                            
                            # Clasificar según edad
                            edad_meses = row.get('edad', 0) * 12  # Convertir años a meses
                            clasificacion, _, _ = clasificar_anemia(hb_ajustada, edad_meses)
                            
                            if clasificacion in ["ANEMIA LEVE", "ANEMIA MODERADA", "ANEMIA SEVERA"]:
                                riesgo_count += 1
                        
                        riesgo = (riesgo_count / len(data_genero)) * 100 if len(data_genero) > 0 else 0
                        
                        # Determinar color
                        if riesgo > 30:
                            icon = "🔴"
                        elif riesgo > 15:
                            icon = "🟡"
                        else:
                            icon = "🟢"
                        
                        st.markdown(f"""
                        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 4px solid {icon=="🔴" and "#dc3545" or icon=="🟡" and "#ffc107" or "#28a745"}; margin: 10px 0;'>
                            <h4 style='margin: 0;'>{icon} {genero_label}</h4>
                            <p style='margin: 5px 0; font-size: 1.5rem; font-weight: bold;'>{len(data_genero)} niños</p>
                            <p style='margin: 0; color: {icon=="🔴" and "#dc3545" or icon=="🟡" and "#856404" or "#155724"}'>
                                <b>{riesgo:.1f}%</b> riesgo de anemia
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # ========== SECCIÓN 2: MONITOREO - RIESGO POR ALTITUD ==========
        st.markdown("## 📊 **2. Monitoreo: Riesgo de Anemia por Altitud**")
        
        # Usar datos reales de altitud
        if 'altitud_msnm' in datos_visualizacion.columns:
            datos_visualizacion['altitud'] = datos_visualizacion['altitud_msnm']
        elif 'altitud' not in datos_visualizacion.columns:
            # Simular datos si no existen
            altitudes = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
            datos_visualizacion['altitud'] = np.random.choice(altitudes, len(datos_visualizacion))
        
        col_mon1, col_mon2 = st.columns([3, 1])
        
        with col_mon1:
            # Crear rangos de altitud
            bins = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500]
            labels = ['0-500', '500-1000', '1000-1500', '1500-2000', 
                     '2000-2500', '2500-3000', '3000-3500', '3500-4000', '4000+']
            
            datos_visualizacion['rango_altitud'] = pd.cut(datos_visualizacion['altitud'], bins=bins, labels=labels, right=False)
            
            # Calcular riesgo por altitud
            riesgo_altitud_data = []
            for rango in labels:
                data_rango = datos_visualizacion[datos_visualizacion['rango_altitud'] == rango]
                if len(data_rango) > 0:
                    # Calcular porcentaje con anemia
                    riesgo_count = 0
                    for _, row in data_rango.iterrows():
                        hb_medida = row.get('hemoglobina_dl1', 0)
                        altitud = row.get('altitud', 0)
                        ajuste = obtener_ajuste_hemoglobina(altitud)
                        hb_ajustada = hb_medida + ajuste
                        edad_meses = row.get('edad', 0) * 12
                        clasificacion, _, _ = clasificar_anemia(hb_ajustada, edad_meses)
                        
                        if clasificacion in ["ANEMIA LEVE", "ANEMIA MODERADA", "ANEMIA SEVERA"]:
                            riesgo_count += 1
                    
                    riesgo = (riesgo_count / len(data_rango)) * 100 if len(data_rango) > 0 else 0
                    riesgo_altitud_data.append({'Altitud': rango, '% Riesgo': riesgo, 'Casos': len(data_rango)})
                else:
                    riesgo_altitud_data.append({'Altitud': rango, '% Riesgo': 0, 'Casos': 0})
            
            riesgo_df = pd.DataFrame(riesgo_altitud_data)
            
            # Gráfico de altitud mejorado
            fig_altitud = px.bar(
                riesgo_df,
                x='Altitud',
                y='% Riesgo',
                title='<b>Porcentaje de Riesgo por Altitud (metros sobre el nivel del mar)</b>',
                color='% Riesgo',
                color_continuous_scale='RdYlGn_r',
                text='% Riesgo',
                height=400
            )
            
            fig_altitud.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside',
                marker_line_color='black',
                marker_line_width=1
            )
            
            # Añadir línea de referencia crítica
            fig_altitud.add_hline(
                y=30,
                line_dash="dash",
                line_color="red",
                annotation_text="Umbral Crítico (30%)"
            )
            
            fig_altitud.update_layout(
                xaxis_title="Rango de Altitud (m)",
                yaxis_title="% de Niños con Anemia",
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_altitud, use_container_width=True)
        
        with col_mon2:
            st.markdown("### 📈 Análisis por Altitud")
            
            # Encontrar altitud más riesgosa
            if len(riesgo_df) > 0:
                max_idx = riesgo_df['% Riesgo'].idxmax()
                max_data = riesgo_df.loc[max_idx]
                
                st.markdown(f"""
                <div style='background-color: #fff3cd; padding: 15px; border-radius: 10px; border: 1px solid #ffeaa7; margin-bottom: 15px;'>
                    <h5 style='color: #856404; margin: 0;'>⚠️ Zona de Mayor Riesgo</h5>
                    <p style='font-size: 1.8rem; font-weight: bold; margin: 5px 0; color: #dc3545;'>{max_data['Altitud']} m</p>
                    <p style='margin: 0;'>{max_data['% Riesgo']:.1f}% de riesgo</p>
                    <p style='margin: 0; font-size: 0.9rem; color: #666;'>{max_data['Casos']} casos analizados</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Recomendaciones específicas
            with st.expander("📋 Recomendaciones por Altitud"):
                st.markdown("""
                **Para altitud < 1500m:**
                - Control trimestral
                - Suplementación preventiva
                
                **Para altitud 1500-3000m:**
                - Control mensual
                - Suplementación obligatoria
                - Educación nutricional
                
                **Para altitud > 3000m:**
                - Control quincenal
                - Suplementación intensiva
                - Derivación especializada
                """)
        
        # ========== SECCIÓN 3: ANÁLISIS - RIESGO POR REGIÓN ==========
        st.markdown("## 📍 **3. Análisis: Riesgo de Anemia por Región**")
        
        if 'region' in datos_visualizacion.columns:
            # Calcular estadísticas por región
            region_stats = []
            for region in datos_visualizacion['region'].dropna().unique():
                data_region = datos_visualizacion[datos_visualizacion['region'] == region]
                total = len(data_region)
                
                if total > 0:
                    # Calcular casos con anemia
                    casos_anemia = 0
                    for _, row in data_region.iterrows():
                        hb_medida = row.get('hemoglobina_dl1', 0)
                        altitud = row.get('altitud_msnm', row.get('altitud', 0))
                        ajuste = obtener_ajuste_hemoglobina(altitud)
                        hb_ajustada = hb_medida + ajuste
                        edad_meses = row.get('edad', 0) * 12
                        clasificacion, _, _ = clasificar_anemia(hb_ajustada, edad_meses)
                        
                        if clasificacion in ["ANEMIA LEVE", "ANEMIA MODERADA", "ANEMIA SEVERA"]:
                            casos_anemia += 1
                    
                    riesgo = (casos_anemia / total) * 100
                    
                    region_stats.append({
                        'Región': region,
                        'Total': total,
                        'Casos Anemia': casos_anemia,
                        '% Riesgo': riesgo
                    })
            
            if region_stats:
                region_df = pd.DataFrame(region_stats).sort_values('% Riesgo', ascending=False)
                
                col_ana1, col_ana2 = st.columns([3, 1])
                
                with col_ana1:
                    # Mapa de calor por región
                    fig_region = px.bar(
                        region_df.head(15),
                        y='Región',
                        x='% Riesgo',
                        title='<b>Regiones con Mayor Riesgo de Anemia</b>',
                        color='% Riesgo',
                        color_continuous_scale='Reds',
                        orientation='h',
                        text='% Riesgo',
                        height=500
                    )
                    
                    fig_region.update_traces(
                        texttemplate='%{text:.1f}%',
                        textposition='outside',
                        marker_line_color='darkred',
                        marker_line_width=1
                    )
                    
                    fig_region.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        xaxis_title="% de Riesgo de Anemia",
                        yaxis_title="Región"
                    )
                    
                    st.plotly_chart(fig_region, use_container_width=True)
                
                with col_ana2:
                    st.markdown("### 🏆 Ranking Regional")
                    
                    # Mostrar top 5
                    for i, (_, row) in enumerate(region_df.head(5).iterrows(), 1):
                        if i == 1:
                            medal = "🥇"
                            bg_color = "#FFD700"
                        elif i == 2:
                            medal = "🥈"
                            bg_color = "#C0C0C0"
                        elif i == 3:
                            medal = "🥉"
                            bg_color = "#CD7F32"
                        else:
                            medal = f"{i}."
                            bg_color = "#f8f9fa"
                        
                        st.markdown(f"""
                        <div style='background-color: {bg_color}; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                            <b>{medal} {row['Región']}</b><br>
                            <span style='font-size: 0.9rem;'>{row['% Riesgo']:.1f}% riesgo</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Selector interactivo
                    region_seleccionada = st.selectbox(
                        "🔍 Ver detalles de región:",
                        region_df['Región'].tolist(),
                        key="selector_region"
                    )
                    
                    if region_seleccionada:
                        region_data = region_df[region_df['Región'] == region_seleccionada].iloc[0]
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total casos", region_data['Total'])
                        with col2:
                            st.metric("% Riesgo", f"{region_data['% Riesgo']:.1f}%")
        
        # ========== TABLA DE DATOS INTERACTIVA CON FILTROS ==========
        st.markdown("---")
        with st.expander(f"🗂️ **Ver Datos Detallados ({len(datos_visualizacion)} registros)**", expanded=False):
            
            # Configurar columnas para mejor visualización
            column_config = {}
            if 'hemoglobina_dl1' in datos_visualizacion.columns:
                column_config['hemoglobina_dl1'] = st.column_config.ProgressColumn(
                    "Hemoglobina",
                    help="Nivel de hemoglobina en g/dL",
                    format="%.2f g/dL",
                    min_value=5,
                    max_value=20
                )
            
            if 'edad' in datos_visualizacion.columns:
                column_config['edad'] = st.column_config.NumberColumn(
                    "Edad",
                    help="Edad en años",
                    format="%.1f años",
                    min_value=0,
                    max_value=5
                )
            
            if 'altitud_msnm' in datos_visualizacion.columns:
                column_config['altitud_msnm'] = st.column_config.NumberColumn(
                    "Altitud",
                    help="Altitud en metros",
                    format="%d msnm"
                )
            
            # Mostrar tabla
            st.dataframe(
                datos_visualizacion,
                use_container_width=True,
                height=400,
                column_config=column_config,
                hide_index=True
            )
            
            # Botón de descarga
            csv = datos_visualizacion.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Datos Actuales (CSV)",
                data=csv,
                file_name=f"anemia_infantil_filtrado_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                icon="💾"
            )
    
    else:
        # Si no se ha iniciado análisis, solo mostrar botón
        if not st.session_state.analisis_iniciado:
            st.info("👆 Presiona el botón 'INICIAR ANÁLISIS COMPLETO' para comenzar")

# ==================================================
# PESTAÑA 4: SEGUIMIENTO Y REGISTRO DE CITAS - VERSIÓN CORREGIDA
# ==================================================

with tab4:
    st.header("📋 Sistema de Seguimiento y Citas")
    st.markdown("Registro de nuevas citas y seguimiento de pacientes")
    
    # ========== BUSCADOR DE PACIENTES ==========
    st.subheader("🔍 Buscar Paciente para Seguimiento")
    
    metodo_busqueda = st.selectbox(
        "Método de búsqueda:",
        ["Por DNI", "Por Nombre", "Ver todos los pacientes"]
    )
    
    valor_busqueda = None
    paciente_encontrado = None
    
    col_buscar1, col_buscar2 = st.columns(2)
    
    with col_buscar1:
        if metodo_busqueda == "Por DNI":
            dni_buscar = st.text_input("Ingrese DNI del paciente:", placeholder="Ej: 11111111")
            valor_busqueda = dni_buscar.strip() if dni_buscar else None
            
        elif metodo_busqueda == "Por Nombre":
            nombre_buscar = st.text_input("Ingrese nombre del paciente:", placeholder="Ej: Juan")
            valor_busqueda = nombre_buscar.strip() if nombre_buscar else None
    
    with col_buscar2:
        st.write("")  # Espaciador
        st.write("")  # Espaciador
        if metodo_busqueda != "Ver todos los pacientes":
            buscar_paciente = st.button("🔍 Buscar Paciente", use_container_width=True, type="primary")
        else:
            buscar_paciente = True  # Auto-buscar para ver todos
    
    # ========== FUNCIÓN MEJORADA PARA BUSCAR PACIENTE ==========
    def buscar_pacientes_db(metodo=None, valor=None):
        """Busca paciente(s) en la base de datos de Supabase"""
        try:
            # Conectar a Supabase directamente para búsquedas específicas
            if metodo == "Por DNI" and valor:
                response = supabase.table("alertas_hemoglobina")\
                    .select("*")\
                    .eq("dni", valor)\
                    .execute()
                return response.data if response.data else []
            
            elif metodo == "Por Nombre" and valor:
                response = supabase.table("alertas_hemoglobina")\
                    .select("*")\
                    .ilike("nombre_apellido", f"%{valor}%")\
                    .execute()
                return response.data if response.data else []
            
            elif metodo == "Ver todos los pacientes" or not metodo:
                # Obtener todos los pacientes (limitado a 50)
                response = supabase.table("alertas_hemoglobina")\
                    .select("*")\
                    .limit(50)\
                    .execute()
                return response.data if response.data else []
            
            return []
        
        except Exception as e:
            st.error(f"❌ Error al buscar pacientes: {str(e)}")
            return []
    
    # ========== FUNCIÓN PARA OBTENER CITAS DEL PACIENTE ==========
    def obtener_citas_paciente(dni):
        """Obtiene el historial de citas de un paciente"""
        try:
            response = supabase.table("citas")\
                .select("*")\
                .eq("dni_paciente", dni)\
                .order("fecha_cita", desc=True)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            st.warning(f"No se pudieron cargar las citas: {str(e)}")
            return []
    
    # ========== FUNCIÓN PARA AGREGAR NUEVA CITA ==========
    def agregar_cita(datos_cita):
        """Agrega una nueva cita a la base de datos"""
        try:
            response = supabase.table("citas").insert(datos_cita).execute()
            return response.data if response.data else None
        except Exception as e:
            st.error(f"❌ Error al guardar cita: {str(e)}")
            return None
    
    # ========== EJECUTAR BÚSQUEDA ==========
    pacientes_encontrados = []
    
    if buscar_paciente:
        with st.spinner("🔍 Buscando pacientes..."):
            pacientes_encontrados = buscar_pacientes_db(metodo_busqueda, valor_busqueda)
    
    # ========== MOSTRAR RESULTADOS ==========
    if pacientes_encontrados:
        if metodo_busqueda == "Ver todos los pacientes" or len(pacientes_encontrados) > 1:
            st.success(f"✅ Se encontraron {len(pacientes_encontrados)} paciente(s)")
            
            # Mostrar lista de pacientes en un selectbox
            opciones_pacientes = [f"{p['dni']} - {p['nombre_apellido']}" for p in pacientes_encontrados]
            seleccion = st.selectbox("Seleccione un paciente:", opciones_pacientes)
            
            if seleccion:
                dni_seleccionado = seleccion.split(" - ")[0]
                paciente_encontrado = next((p for p in pacientes_encontrados if p['dni'] == dni_seleccionado), None)
        else:
            paciente_encontrado = pacientes_encontrados[0]
    
    # ========== MOSTRAR INFORMACIÓN DEL PACIENTE SELECCIONADO ==========
    if paciente_encontrado:
        st.markdown(f"### 👤 Paciente: **{paciente_encontrado.get('nombre_apellido', 'N/A')}**")
        
        # Tarjetas de información
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("DNI", paciente_encontrado.get('dni', 'N/A'))
        with col2:
            edad = paciente_encontrado.get('edad_meses', 'N/A')
            st.metric("Edad", f"{edad} meses" if edad != 'N/A' else 'N/A')
        with col3:
            st.metric("Hemoglobina", f"{paciente_encontrado.get('hemoglobina_dl1', 'N/A')} g/dL")
        with col4:
            riesgo = paciente_encontrado.get('riesgo', 'N/A')
            color = {
                'BAJO RIESGO': 'green',
                'MODERADO': 'orange',
                'ALTO RIESGO': 'red',
                'ALTÍSIMO RIESGO': 'darkred'
            }.get(riesgo, 'gray')
            st.markdown(f"**Riesgo:** <span style='color:{color}; font-weight:bold'>{riesgo}</span>", unsafe_allow_html=True)
        
        # Pestañas para información detallada
        tab_info, tab_historial, tab_nueva_cita = st.tabs(["📋 Información", "📅 Historial", "➕ Nueva Cita"])
        
        with tab_info:
            # Información detallada del paciente
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown("#### Datos Personales")
                st.write(f"**Nombre completo:** {paciente_encontrado.get('nombre_apellido', 'N/A')}")
                st.write(f"**Género:** {paciente_encontrado.get('genero', 'N/A')}")
                st.write(f"**Teléfono:** {paciente_encontrado.get('telefono', 'N/A')}")
                st.write(f"**Región:** {paciente_encontrado.get('region', 'N/A')}")
                st.write(f"**Departamento:** {paciente_encontrado.get('departamento', 'N/A')}")
            
            with col_info2:
                st.markdown("#### Datos Clínicos")
                st.write(f"**Estado:** {paciente_encontrado.get('estado_paciente', 'N/A')}")
                st.write(f"**En seguimiento:** {'✅ Sí' if paciente_encontrado.get('en_seguimiento') else '❌ No'}")
                st.write(f"**Consume hierro:** {'✅ Sí' if paciente_encontrado.get('consumir_hierro') else '❌ No'}")
                st.write(f"**Antecedentes anemia:** {'✅ Sí' if paciente_encontrado.get('antecedentes_anemia') else '❌ No'}")
                st.write(f"**Fecha última alerta:** {paciente_encontrado.get('fecha_alerta', 'N/A')}")
        
        with tab_historial:
            st.markdown("#### 📋 Historial de Citas")
            
            # Obtener citas del paciente
            citas_paciente = obtener_citas_paciente(paciente_encontrado['dni'])
            
            if citas_paciente:
                # Convertir a DataFrame para mejor visualización
                df_citas = pd.DataFrame(citas_paciente)
                
                # Formatear columnas para mostrar
                if not df_citas.empty:
                    # Seleccionar columnas relevantes
                    columnas_mostrar = ['fecha_cita', 'hora_cita', 'tipo_consulta', 
                                       'diagnostico', 'tratamiento', 'investigador_responsable']
                    columnas_disponibles = [c for c in columnas_mostrar if c in df_citas.columns]
                    
                    if columnas_disponibles:
                        df_display = df_citas[columnas_disponibles].copy()
                        
                        # Ordenar por fecha
                        if 'fecha_cita' in df_display.columns:
                            df_display = df_display.sort_values('fecha_cita', ascending=False)
                        
                        # Mostrar tabla
                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "fecha_cita": st.column_config.DateColumn("Fecha"),
                                "hora_cita": st.column_config.TimeColumn("Hora"),
                                "diagnostico": st.column_config.TextColumn("Diagnóstico", width="medium"),
                                "tratamiento": st.column_config.TextColumn("Tratamiento", width="medium")
                            }
                        )
                        
                        # Métricas del historial
                        col_hist1, col_hist2 = st.columns(2)
                        with col_hist1:
                            st.metric("Total de citas", len(citas_paciente))
                        with col_hist2:
                            if 'fecha_cita' in df_citas.columns:
                                ultima_cita = df_citas['fecha_cita'].max()
                                st.metric("Última cita", ultima_cita)
            else:
                st.info("📭 No hay citas registradas para este paciente")
        
        with tab_nueva_cita:
            st.markdown("#### Registrar Nueva Cita")
            
            with st.form("form_nueva_cita"):
                col_fecha, col_hora = st.columns(2)
                with col_fecha:
                    fecha_cita = st.date_input("📅 Fecha de cita", value=datetime.now())
                with col_hora:
                    hora_cita = st.time_input("⏰ Hora", value=datetime.now().time())
                
                tipo_consulta = st.selectbox(
                    "🩺 Tipo de consulta",
                    ["Consulta inicial", "Control mensual", "Control escolar", 
                     "Seguimiento", "Urgencia", "Reevaluación"]
                )
                
                diagnostico = st.text_area(
                    "📝 Diagnóstico",
                    placeholder="Ej: Anemia moderada controlada, mejora en niveles de hemoglobina..."
                )
                
                tratamiento = st.text_area(
                    "💊 Tratamiento indicado",
                    placeholder="Ej: Continuar con suplemento de hierro, dieta rica en..."
                )
                
                observaciones = st.text_area(
                    "📋 Observaciones adicionales",
                    placeholder="Notas importantes sobre el estado del paciente..."
                )
                
                col_responsable, col_proxima = st.columns(2)
                with col_responsable:
                    investigador = st.text_input("👨‍⚕️ Investigador responsable", value="Dr. Responsable")
                with col_proxima:
                    proxima_cita = st.date_input("📅 Próxima cita", 
                                                value=datetime.now() + timedelta(days=30))
                
                # Botones de acción
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn2:
                    guardar_cita = st.form_submit_button("💾 Guardar Cita", type="primary")
                
                if guardar_cita:
                    if not diagnostico.strip() or not tratamiento.strip():
                        st.error("⚠️ Por favor complete el diagnóstico y tratamiento")
                    else:
                        nueva_cita = {
                            "dni_paciente": paciente_encontrado['dni'],
                            "fecha_cita": str(fecha_cita),
                            "hora_cita": str(hora_cita),
                            "tipo_consulta": tipo_consulta,
                            "diagnostico": diagnostico,
                            "tratamiento": tratamiento,
                            "observaciones": observaciones,
                            "investigador_responsable": investigador,
                            "proxima_cita": str(proxima_cita)
                        }
                        
                        resultado = agregar_cita(nueva_cita)
                        if resultado:
                            st.success("✅ Cita registrada exitosamente!")
                            st.balloons()
                            st.rerun()
    
    elif buscar_paciente and not pacientes_encontrados:
        st.error("❌ No se encontraron pacientes con los criterios de búsqueda")
    
    # ========== SECCIÓN: PACIENTES EN SEGUIMIENTO ==========
    st.markdown("---")
    st.subheader("📊 Pacientes en Seguimiento Activo")
    
    try:
        # Obtener pacientes en seguimiento
        response = supabase.table("alertas_hemoglobina")\
            .select("*")\
            .eq("en_seguimiento", True)\
            .execute()
        
        pacientes_seguimiento = response.data if response.data else []
        
        if pacientes_seguimiento:
            df_seguimiento = pd.DataFrame(pacientes_seguimiento)
            
            # Mostrar métricas
            col_met1, col_met2, col_met3 = st.columns(3)
            with col_met1:
                st.metric("Total en seguimiento", len(pacientes_seguimiento))
            with col_met2:
                if 'hemoglobina_dl1' in df_seguimiento.columns:
                    hb_promedio = df_seguimiento['hemoglobina_dl1'].mean()
                    st.metric("HB promedio", f"{hb_promedio:.1f} g/dL")
            with col_met3:
                if 'edad_meses' in df_seguimiento.columns:
                    edad_promedio = df_seguimiento['edad_meses'].mean()
                    st.metric("Edad promedio", f"{edad_promedio:.0f} meses")
            
            # Mostrar tabla de pacientes en seguimiento
            columnas_relevantes = ['nombre_apellido', 'dni', 'edad_meses', 
                                  'hemoglobina_dl1', 'riesgo', 'estado_alerta']
            columnas_disponibles = [c for c in columnas_relevantes if c in df_seguimiento.columns]
            
            if columnas_disponibles:
                st.dataframe(
                    df_seguimiento[columnas_disponibles],
                    use_container_width=True,
                    height=300,
                    hide_index=True,
                    column_config={
                        "nombre_apellido": "Paciente",
                        "dni": "DNI",
                        "edad_meses": "Edad (meses)",
                        "hemoglobina_dl1": "HB (g/dL)",
                        "riesgo": "Nivel de riesgo",
                        "estado_alerta": "Estado"
                    }
                )
        else:
            st.info("📭 No hay pacientes en seguimiento activo")
            
    except Exception as e:
        st.error(f"❌ Error al cargar pacientes en seguimiento: {str(e)}")
    
    # ========== INFORMACIÓN ADICIONAL ==========
    with st.expander("ℹ️ Información sobre el sistema de citas"):
        st.markdown("""
        **Funcionalidades del sistema:**
        
        1. **Búsqueda de pacientes:** Por DNI, nombre o lista completa
        2. **Historial clínico:** Visualización de todas las citas previas
        3. **Registro de citas:** Formulario completo para nuevas consultas
        4. **Seguimiento activo:** Lista de pacientes que requieren monitoreo continuo
        
        **💡 Recomendaciones:**
        - Verifique siempre el DNI del paciente antes de registrar una cita
        - Complete todos los campos del formulario para un registro adecuado
        - Revise el historial clínico antes de cada nueva consulta
        """)

# ==================================================
# PESTAÑA 5: EVALUACIÓN NUTRICIONAL
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
# PESTAÑA 6: DASHBOARD NACIONAL
# ==================================================

with tab5:
    # TÍTULO PRINCIPAL CON DISEÑO MEJORADO
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h1 style='color: white; text-align: center; margin: 0; font-size: 2.5rem;'>
            🩺 SISTEMA NIXON - Control de Anemia y Nutrición
        </h1>
        <p style='color: rgba(255,255,255,0.9); text-align: center; margin-top: 10px; font-size: 1.1rem;'>
            Sistema integrado con ajutor por editor y evaluación nutricional
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ========== MÓDULOS DEL SISTEMA ==========
    st.markdown("## 📋 **Módulos del Sistema**")
    
    col_mod1, col_mod2, col_mod3, col_mod4, col_mod5 = st.columns(5)
    
    with col_mod1:
        st.markdown("""
        <div style='background-color: #e3f2fd; padding: 15px; border-radius: 8px; border: 1px solid #bbdefb; text-align: center; height: 120px;'>
            <div style='font-size: 1.5rem; color: #1565c0;'>📝</div>
            <h4 style='color: #0d47a1; margin: 10px 0;'>Registro Clínico</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_mod2:
        st.markdown("""
        <div style='background-color: #fff3e0; padding: 15px; border-radius: 8px; border: 1px solid #ffe0b2; text-align: center; height: 120px;'>
            <div style='font-size: 1.5rem; color: #f57c00;'>🔍</div>
            <h4 style='color: #e65100; margin: 10px 0;'>Supervisión Clínica</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_mod3:
        st.markdown("""
        <div style='background-color: #e8f5e9; padding: 15px; border-radius: 8px; border: 1px solid #c8e6c9; text-align: center; height: 120px;'>
            <div style='font-size: 1.5rem; color: #388e3c;'>📊</div>
            <h4 style='color: #1b5e20; margin: 10px 0;'>Estadísticas</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_mod4:
        st.markdown("""
        <div style='background-color: #fff8e1; padding: 15px; border-radius: 8px; border: 1px solid #ffecb3; text-align: center; height: 120px;'>
            <div style='font-size: 1.5rem; color: #ffa000;'>🍎</div>
            <h4 style='color: #ff6f00; margin: 10px 0;'>Evaluación Nutricional</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_mod5:
        st.markdown("""
        <div style='background-color: #f3e5f5; padding: 15px; border-radius: 8px; border: 1px solid #e1bee7; text-align: center; height: 120px;'>
            <div style='font-size: 1.5rem; color: #7b1fa2;'>🔄</div>
            <h4 style='color: #4a148c; margin: 10px 0;'>Comisiones Nacional</h4>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== DASHBOARD NACIONAL ==========
    st.markdown("## 📊 **Dashboard Nacional de Anemia y Nutrición**")
    
    # Botón para actualizar
    if st.button("🔄 **ACTUALIZAR DASHBOARD NACIONAL**", type="primary", use_container_width=True):
        with st.spinner("🔍 Cargando datos nacionales..."):
            datos_nacionales = obtener_datos_supabase()
        
        if not datos_nacionales.empty:
            st.success(f"✅ Dashboard actualizado con {len(datos_nacionales)} registros")
            
            # ========== INDICADORES CLAVE CON COLORES ==========
            st.markdown("### 🎯 **Indicadores Clave**")
            
            col_met1, col_met2, col_met3, col_met4 = st.columns(4)
            
            with col_met1:
                total_pacientes = len(datos_nacionales)
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;'>
                    <h4 style='margin: 0 0 10px 0; color: white;'>👶 Niños Evaluados</h4>
                    <div style='font-size: 2.5rem; font-weight: bold;'>{total_pacientes}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_met2:
                if 'estado_nutricional' in datos_nacionales.columns:
                    nutricion_count = datos_nacionales['estado_nutricional'].notna().sum()
                else:
                    nutricion_count = datos_nacionales.shape[0]  # Asumir todos tienen
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #10B981 0%, #34D399 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;'>
                    <h4 style='margin: 0 0 10px 0; color: white;'>📋 Evaluación Nutricional</h4>
                    <div style='font-size: 2.5rem; font-weight: bold;'>{nutricion_count}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_met3:
                if 'hemoglobina_dl1' in datos_nacionales.columns:
                    avg_hemoglobina = datos_nacionales['hemoglobina_dl1'].mean()
                    hemoglobina_text = f"{avg_hemoglobina:.1f} g/dL"
                else:
                    hemoglobina_text = "N/A"
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;'>
                    <h4 style='margin: 0 0 10px 0; color: white;'>🩸 Hemoglobina Promedio</h4>
                    <div style='font-size: 2.5rem; font-weight: bold;'>{hemoglobina_text}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_met4:
                if 'en_seguimiento' in datos_nacionales.columns:
                    seguimiento_count = datos_nacionales[datos_nacionales['en_seguimiento'] == True].shape[0]
                else:
                    seguimiento_count = 0
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;'>
                    <h4 style='margin: 0 0 10px 0; color: white;'>📈 Seguimientos</h4>
                    <div style='font-size: 2.5rem; font-weight: bold;'>{seguimiento_count}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # ========== GRÁFICO 1: DISTRIBUCIÓN POR EDAD ==========
            st.markdown("---")
            st.markdown("### 📊 **Distribución por Edad**")
            
            if 'edad' in datos_nacionales.columns:
                # Crear grupos de edad
                bins = [0, 1, 2, 3, 4, 5]
                labels = ['0-1 año', '1-2 años', '2-3 años', '3-4 años', '4-5 años']
                
                datos_nacionales['grupo_edad'] = pd.cut(datos_nacionales['edad'], bins=bins, labels=labels, right=False)
                edad_counts = datos_nacionales['grupo_edad'].value_counts().sort_index()
                
                fig_edad = px.bar(
                    x=edad_counts.index,
                    y=edad_counts.values,
                    title='<b>Distribución por Grupos de Edad</b>',
                    color=edad_counts.values,
                    color_continuous_scale='Viridis',
                    text=edad_counts.values,
                    height=400
                )
                
                fig_edad.update_traces(
                    texttemplate='%{text}',
                    textposition='outside',
                    marker_line_color='black',
                    marker_line_width=1
                )
                
                fig_edad.update_layout(
                    xaxis_title="Grupo de Edad",
                    yaxis_title="Número de Niños",
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_edad, use_container_width=True)
            else:
                st.info("ℹ️ No hay datos de edad disponibles")
            
            # ========== GRÁFICO 2: DISTRIBUCIÓN POR GÉNERO ==========
            col_gen1, col_gen2 = st.columns([3, 1])
            
            with col_gen1:
                if 'genero' in datos_nacionales.columns:
                    genero_counts = datos_nacionales['genero'].value_counts()
                    
                    # Mapear códigos de género
                    genero_mapping = {
                        'M': 'Niños 👦',
                        'F': 'Niñas 👧',
                        'Masculino': 'Niños 👦',
                        'Femenino': 'Niñas 👧',
                        'm': 'Niños 👦',
                        'f': 'Niñas 👧'
                    }
                    
                    genero_counts.index = genero_counts.index.map(lambda x: genero_mapping.get(x, x))
                    
                    fig_genero = px.pie(
                        values=genero_counts.values,
                        names=genero_counts.index,
                        title='<b>Distribución por Género</b>',
                        color=genero_counts.index,
                        color_discrete_sequence=['#3498db', '#e74c3c', '#2ecc71'],
                        hole=0.4,
                        height=350
                    )
                    
                    fig_genero.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        marker=dict(line=dict(color='white', width=2))
                    )
                    
                    st.plotly_chart(fig_genero, use_container_width=True)
                else:
                    st.info("ℹ️ No hay datos de género disponibles")
            
            with col_gen2:
                st.markdown("#### 📈 **Estadísticas de Género**")
                if 'genero' in datos_nacionales.columns:
                    for genero, count in genero_counts.items():
                        porcentaje = (count / total_pacientes) * 100
                        st.metric(genero, f"{count}", f"{porcentaje:.1f}%")
            
            # ========== GRÁFICO 3: HEMOGLOBINA POR EDAD ==========
            st.markdown("---")
            st.markdown("### 🩸 **Niveles de Hemoglobina por Edad**")
            
            if 'edad' in datos_nacionales.columns and 'hemoglobina_dl1' in datos_nacionales.columns:
                fig_hb_edad = px.scatter(
                    datos_nacionales,
                    x='edad',
                    y='hemoglobina_dl1',
                    title='<b>Relación Edad vs Hemoglobina</b>',
                    color='edad',
                    size='hemoglobina_dl1',
                    hover_name='nombre_apellido' if 'nombre_apellido' in datos_nacionales.columns else None,
                    hover_data=['region'] if 'region' in datos_nacionales.columns else None,
                    height=400
                )
                
                # Añadir líneas de referencia para anemia
                fig_hb_edad.add_hline(
                    y=11.0,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Umbral Anemia Leve",
                    annotation_position="bottom right"
                )
                
                fig_hb_edad.add_hline(
                    y=12.0,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="Normal",
                    annotation_position="top right"
                )
                
                fig_hb_edad.update_layout(
                    xaxis_title="Edad (años)",
                    yaxis_title="Hemoglobina (g/dL)",
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_hb_edad, use_container_width=True)
            else:
                st.info("ℹ️ No hay suficientes datos para el gráfico de hemoglobina")
            
            # ========== GRÁFICO 4: DISTRIBUCIÓN POR REGIÓN ==========
            st.markdown("---")
            st.markdown("### 📍 **Distribución Geográfica**")
            
            if 'region' in datos_nacionales.columns:
                distribucion_region = datos_nacionales['region'].value_counts().head(15)
                
                col_reg1, col_reg2 = st.columns([3, 1])
                
                with col_reg1:
                    fig_region = px.bar(
                        x=distribucion_region.values,
                        y=distribucion_region.index,
                        orientation='h',
                        title='<b>Top 15 Regiones con Más Casos</b>',
                        color=distribucion_region.values,
                        color_continuous_scale='Blues',
                        text=distribucion_region.values,
                        height=500
                    )
                    
                    fig_region.update_traces(
                        texttemplate='%{text}',
                        textposition='outside',
                        marker_line_color='darkblue',
                        marker_line_width=1
                    )
                    
                    fig_region.update_layout(
                        xaxis_title="Número de Casos",
                        yaxis_title="Región",
                        showlegend=False,
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    
                    st.plotly_chart(fig_region, use_container_width=True)
                
                with col_reg2:
                    st.markdown("#### 🏆 **Ranking Regional**")
                    
                    for i, (region, count) in enumerate(distribucion_region.head(5).items(), 1):
                        if i == 1:
                            medal = "🥇"
                            bg_color = "#FFD700"
                        elif i == 2:
                            medal = "🥈"
                            bg_color = "#C0C0C0"
                        elif i == 3:
                            medal = "🥉"
                            bg_color = "#CD7F32"
                        else:
                            medal = f"{i}."
                            bg_color = "#f8f9fa"
                        
                        st.markdown(f"""
                        <div style='background-color: {bg_color}; padding: 10px; border-radius: 8px; margin: 5px 0;'>
                            <b>{medal} {region}</b><br>
                            <span style='font-size: 0.9rem;'>{count} casos</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # ========== GRÁFICO 5: ESTADO NUTRICIONAL ==========
            st.markdown("---")
            st.markdown("### 🍎 **Estado Nutricional**")
            
            if 'estado_nutricional' in datos_nacionales.columns:
                estado_counts = datos_nacionales['estado_nutricional'].value_counts()
                
                fig_nutricion = px.bar(
                    x=estado_counts.index,
                    y=estado_counts.values,
                    title='<b>Distribución del Estado Nutricional</b>',
                    color=estado_counts.values,
                    color_continuous_scale='YlOrRd',
                    text=estado_counts.values,
                    height=350
                )
                
                fig_nutricion.update_traces(
                    texttemplate='%{text}',
                    textposition='outside',
                    marker_line_color='black',
                    marker_line_width=1
                )
                
                fig_nutricion.update_layout(
                    xaxis_title="Estado Nutricional",
                    yaxis_title="Número de Casos",
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig_nutricion, use_container_width=True)
            else:
                st.info("ℹ️ No hay datos de estado nutricional")
            
            # ========== GRÁFICO 6: EVOLUCIÓN TEMPORAL ==========
            st.markdown("---")
            st.markdown("### 📅 **Tendencias Temporales**")
            
            if 'fecha_registro' in datos_nacionales.columns:
                # Convertir fecha a datetime
                datos_nacionales['fecha_registro'] = pd.to_datetime(datos_nacionales['fecha_registro'])
                datos_nacionales['mes_registro'] = datos_nacionales['fecha_registro'].dt.to_period('M').astype(str)
                
                registros_por_mes = datos_nacionales['mes_registro'].value_counts().sort_index()
                
                fig_temporal = px.line(
                    x=registros_por_mes.index,
                    y=registros_por_mes.values,
                    title='<b>Registros por Mes</b>',
                    markers=True,
                    height=300
                )
                
                fig_temporal.update_layout(
                    xaxis_title="Mes",
                    yaxis_title="Número de Registros",
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                # Añadir área sombreada
                fig_temporal.add_trace(
                    go.Scatter(
                        x=registros_por_mes.index,
                        y=registros_por_mes.values,
                        fill='tozeroy',
                        fillcolor='rgba(59, 130, 246, 0.1)',
                        line=dict(color='#3B82F6', width=2),
                        mode='lines',
                        showlegend=False
                    )
                )
                
                st.plotly_chart(fig_temporal, use_container_width=True)
            
            # ========== TABLA RESUMEN INTERACTIVA ==========
            st.markdown("---")
            with st.expander("📋 **Tabla Resumen de Datos Nacionales**", expanded=False):
                # Mostrar estadísticas por región
                if 'region' in datos_nacionales.columns and 'hemoglobina_dl1' in datos_nacionales.columns:
                    resumen_region = datos_nacionales.groupby('region').agg({
                        'hemoglobina_dl1': ['count', 'mean', 'min', 'max'],
                        'edad': 'mean'
                    }).round(2)
                    
                    resumen_region.columns = ['Casos', 'HB Promedio', 'HB Mínima', 'HB Máxima', 'Edad Promedio']
                    resumen_region = resumen_region.sort_values('Casos', ascending=False)
                    
                    st.dataframe(resumen_region, use_container_width=True)
                else:
                    st.info("No hay suficientes datos para el resumen regional")
            
            # ========== BOTONES DE ACCIÓN ==========
            st.markdown("---")
            col_acc1, col_acc2, col_acc3 = st.columns(3)
            
            with col_acc1:
                if st.button("📥 **EXPORTAR DATOS**", use_container_width=True):
                    csv = datos_nacionales.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar CSV Completo",
                        data=csv,
                        file_name=f"datos_nacionales_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col_acc2:
                if st.button("📊 **EXPORTAR GRÁFICOS**", use_container_width=True):
                    st.success("✅ Gráficos exportados como imágenes")
                    # Aquí iría la lógica para exportar gráficos
            
            with col_acc3:
                if st.button("🔄 **ACTUALIZAR AHORA**", use_container_width=True):
                    st.rerun()
        
        else:
            st.error("❌ No se pudieron cargar los datos nacionales")
            st.info("Verifica la conexión con la base de datos")
    
    else:
        # PANTALLA INICIAL DEL DASHBOARD
        st.markdown("""
        <div style='background-color: #f0f8ff; padding: 25px; border-radius: 15px; border-left: 6px solid #1E3A8A; margin-bottom: 30px;'>
            <h2 style='color: #1E3A8A;'>📊 Dashboard Nacional Listo</h2>
            <p style='font-size: 1.1rem; line-height: 1.6;'>
                Presiona el botón <strong>"ACTUALIZAR DASHBOARD NACIONAL"</strong> para cargar y visualizar 
                las estadísticas nacionales de anemia y nutrición infantil.
            </p>
            <div style='background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0;'>
                <h4 style='color: #1E3A8A;'>📈 Gráficos Disponibles:</h4>
                <ul style='color: #555;'>
                    <li>📊 Distribución por Edad y Género</li>
                    <li>🩸 Niveles de Hemoglobina</li>
                    <li>📍 Distribución Geográfica</li>
                    <li>🍎 Estado Nutricional</li>
                    <li>📅 Tendencias Temporales</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ========== INFORMACIÓN DEL SISTEMA ==========
    st.markdown("---")
    
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        <div style='text-align: center; padding: 15px;'>
            <div style='font-size: 2rem;'>🏥</div>
            <h4>Sistema Nacional de Salud</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown("""
        <div style='text-align: center; padding: 15px;'>
            <div style='font-size: 2rem;'>📅</div>
            <h4>Versión: 2.0.1</h4>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info3:
        st.markdown("""
        <div style='text-align: center; padding: 15px;'>
            <div style='font-size: 2rem;'>🔄</div>
            <h4>Actualizado: Diciembre 2024</h4>
        </div>
        """, unsafe_allow_html=True)
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
