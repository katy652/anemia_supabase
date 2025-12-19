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

# ==================================================
# ESTILOS CSS MEJORADOS
# ==================================================
st.markdown("""
<style>
    /* TÍTULOS CON MEJOR VISUALIZACIÓN */
    .main-title {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(30, 58, 138, 0.2);
    }
    
    .section-title-blue {
        color: #1e3a8a;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 3px solid #3b82f6;
    }
    
    .section-title-green {
        color: #065f46;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 3px solid #10b981;
    }
    
    .section-title-red {
        color: #7f1d1d;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 3px solid #ef4444;
    }
    
    .section-title-purple {
        color: #5b21b6;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 3px solid #8b5cf6;
    }
    
    /* TARJETAS DE COLORES */
    .metric-card-blue {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    
    .metric-card-green {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #10b981;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }
    
    .metric-card-red {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #ef4444;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
    }
    
    .metric-card-yellow {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #f59e0b;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
    }
    
    .metric-card-purple {
        background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #8b5cf6;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
    }
    
    /* NÚMEROS DESTACADOS */
    .highlight-number {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .highlight-blue { color: #1e40af; }
    .highlight-green { color: #065f46; }
    .highlight-red { color: #7f1d1d; }
    .highlight-yellow { color: #92400e; }
    .highlight-purple { color: #5b21b6; }
    
    /* ETIQUETAS */
    .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* ESTADOS DE ANEMIA */
    .severity-critical {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #dc2626;
        margin: 1rem 0;
    }
    
    .severity-moderate {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #d97706;
        margin: 1rem 0;
    }
    
    .severity-mild {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2563eb;
        margin: 1rem 0;
    }
    
    .severity-normal {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #16a34a;
        margin: 1rem 0;
    }
    
    /* BOTONES MEJORADOS */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* MEJORAS EN FORMULARIOS */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        transition: border-color 0.3s;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* TABLAS MEJORADAS */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
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
# FUNCIONES PARA TABLA CITAS - VERSIÓN SIMPLIFICADA Y CORREGIDA
# ==================================================

def crear_tabla_citas_simple():
    """Crea la tabla citas de forma simple - VERSIÓN CORREGIDA"""
    try:
        st.sidebar.info("🛠️ Configurando tabla 'citas'...")
        
        # Intentar crear una cita de prueba simple
        test_cita = {
            "dni_paciente": "99988877",
            "fecha_cita": "2024-12-14",
            "hora_cita": "10:00:00",
            "tipo_consulta": "Prueba de sistema"
        }
        
        response = supabase.table("citas").insert(test_cita).execute()
        
        if response.data:
            st.sidebar.success("✅ Tabla 'citas' accesible")
            # Limpiar la prueba
            supabase.table("citas").delete().eq("dni_paciente", "99988877").execute()
            return True
        else:
            st.sidebar.warning("⚠️ Puede que la tabla necesite configuración en Supabase")
            
            # Instrucciones para crear manualmente
            st.sidebar.markdown("""
            **📝 Si falla, crea la tabla manualmente en Supabase:**
            
            1. Ve a **Table Editor**
            2. Crea nueva tabla llamada **"citas"**
            3. Agrega estas columnas:
               - `id` (bigint, autoincrement, primary key)
               - `dni_paciente` (text)
               - `fecha_cita` (date)
               - `hora_cita` (time)
               - `tipo_consulta` (text)
               - `diagnostico` (text)
               - `tratamiento` (text)
               - `observaciones` (text)
               - `investigador_responsable` (text)
               - `proxima_cita` (date)
               - `created_at` (timestamptz, default: now())
            4. En **Authentication → Policies**, crea política:
               - `allow_all` (para todas las operaciones)
            """)
            return False
            
    except Exception as e:
        st.sidebar.error(f"❌ Error: {str(e)[:100]}")
        return False

def probar_guardado_directo():
    """Prueba directa de guardado - VERSIÓN SIMPLIFICADA"""
    with st.sidebar:
        st.markdown("### 🧪 Prueba Directa")
        
        try:
            pacientes = supabase.table("alertas_hemoglobina").select("dni").limit(5).execute()
            
            if pacientes.data and len(pacientes.data) > 0:
                dni_real = pacientes.data[0]["dni"]
                st.info(f"📋 Usando DNI real: {dni_real}")
            else:
                dni_real = "12345678"
                st.warning("⚠️ No hay pacientes, usando DNI de prueba")
                
        except:
            dni_real = "12345678"
        
        test_cita = {
            "dni_paciente": dni_real,
            "fecha_cita": "2024-12-14",
            "hora_cita": "09:00:00",
            "tipo_consulta": "Consulta de prueba",
            "diagnostico": "Paciente de prueba para verificar sistema",
            "tratamiento": "Observación",
            "observaciones": "Esta es una prueba del sistema de citas",
            "investigador_responsable": "Dr. Prueba"
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Enviar prueba", type="primary", key="enviar_prueba"):
                try:
                    with st.spinner("Enviando a Supabase..."):
                        result = supabase.table("citas").insert(test_cita).execute()
                    
                    if result.data:
                        st.success(f"✅ ¡ÉXITO! Guardado correctamente")
                        st.info(f"ID generado: {result.data[0].get('id', 'N/A')}")
                    else:
                        st.warning("⚠️ Respuesta inesperada del servidor")
                        
                except Exception as e:
                    st.error(f"🔥 Error: {str(e)[:200]}")
        
        with col2:
            if st.button("🗑️ Limpiar pruebas", key="limpiar_pruebas"):
                try:
                    supabase.table("citas").delete().eq("dni_paciente", dni_real).execute()
                    st.success("✅ Pruebas limpiadas")
                except Exception as e:
                    st.info(f"ℹ️ {str(e)[:100]}")

# ==================================================
# FUNCIONES DE BASE DE DATOS
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
        
        if verificar_duplicado(dni):
            st.error(f"❌ El DNI {dni} ya existe en la base de datos")
            return {"status": "duplicado", "dni": dni}
        
        if supabase:
            response = supabase.table(tabla).insert(datos).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"❌ Error Supabase al insertar: {response.error}")
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        st.error(f"Error insertando datos: {e}")
        return None

def upsert_datos_supabase(datos, tabla=TABLE_NAME):
    """Inserta o actualiza datos si ya existen"""
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
    
    # EVALUAR FERRITINA
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
    
    # EVALUAR CHCM
    if chcm < 32:
        interpretacion += "🚨 **HIPOCROMÍA SEVERA** - Deficiencia avanzada de hierro. "
        severidad = "CRITICO" if severidad != "CRITICO" else severidad
    elif chcm >= 32 and chcm <= 36:
        interpretacion += "✅ **NORMOCROMÍA** - Estado normal. "
    else:
        interpretacion += "🔄 **HIPERCROMÍA** - Posible esferocitosis. "
    
    # EVALUAR RETICULOCITOS
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
    
    # CLASIFICACIÓN DE ANEMIA
    clasificacion_hb, _, _ = clasificar_anemia(hemoglobina_ajustada, edad_meses)
    interpretacion += f"📊 **CLASIFICACIÓN HEMOGLOBINA: {clasificacion_hb}**"
    
    # GENERAR RECOMENDACIÓN
    if severidad == "CRITICO":
        recomendacion = "🚨 **INTERVENCIÓN INMEDIATA**: Suplementación con hierro elemental 3-6 mg/kg/día + Control en 15 días + Evaluación médica urgente"
        codigo_color = "#DC2626"
    elif severidad == "MODERADO":
        recomendacion = "⚠️ **ACCIÓN PRIORITARIA**: Iniciar suplementación con hierro + Control mensual + Educación nutricional"
        codigo_color = "#D97706"
    elif severidad == "LEVE":
        recomendacion = "🔄 **VIGILANCIA ACTIVA**: Suplementación preventiva + Modificación dietética + Control cada 3 meses"
        codigo_color = "#2563EB"
    else:
        recomendacion = "✅ **SEGUIMIENTO RUTINARIO**: Mantener alimentación balanceada + Control preventivo cada 6 meses"
        codigo_color = "#16A34A"
    
    return {
        "interpretacion": interpretacion,
        "severidad": severidad,
        "recomendacion": recomendacion,
        "codigo_color": codigo_color,
        "clasificacion_hemoglobina": clasificacion_hb
    }

def generar_parametros_hematologicos(hemoglobina_ajustada, edad_meses):
    """Genera parámetros hematológicos simulados"""
    
    if hemoglobina_ajustada < 9.0:
        ferritina = np.random.uniform(5, 15)
        chcm = np.random.uniform(28, 31)
        reticulocitos = np.random.uniform(0.5, 1.0)
        transferrina = np.random.uniform(350, 450)
    elif hemoglobina_ajustada < 11.0:
        ferritina = np.random.uniform(15, 50)
        chcm = np.random.uniform(31, 33)
        reticulocitos = np.random.uniform(1.0, 1.8)
        transferrina = np.random.uniform(300, 400)
    else:
        ferritina = np.random.uniform(80, 150)
        chcm = np.random.uniform(33, 36)
        reticulocitos = np.random.uniform(0.8, 1.5)
        transferrina = np.random.uniform(200, 350)
    
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
# CLASIFICACIÓN DE ANEMIA
# ==================================================

def clasificar_anemia(hemoglobina_ajustada, edad_meses):
    """Clasifica la anemia según estándares OMS"""
    
    if edad_meses < 24:
        if hemoglobina_ajustada >= 11.0:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 10.0 <= hemoglobina_ajustada < 11.0:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 9.0 <= hemoglobina_ajustada < 10.0:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"
    
    elif 24 <= edad_meses < 60:
        if hemoglobina_ajustada >= 11.5:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 10.5 <= hemoglobina_ajustada < 11.5:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 9.5 <= hemoglobina_ajustada < 10.5:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"
    
    else:
        if hemoglobina_ajustada >= 12.0:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 11.0 <= hemoglobina_ajustada < 12.0:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 10.0 <= hemoglobina_ajustada < 11.0:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"

def necesita_seguimiento_automatico(hemoglobina_ajustada, edad_meses):
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
    
    referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_meses]
    
    if referencia_edad.empty:
        return "Edad sin referencia", "Edad sin referencia", "NO EVALUABLE"
    
    ref = referencia_edad.iloc[0]
    
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
    
    if peso_kg < peso_min:
        estado_peso = "BAJO PESO"
    elif peso_kg > peso_max:
        estado_peso = "SOBREPESO"
    else:
        estado_peso = "PESO NORMAL"
    
    if talla_cm < talla_min:
        estado_talla = "TALLA BAJA"
    elif talla_cm > talla_max:
        estado_talla = "TALLA ALTA"
    else:
        estado_talla = "TALLA NORMAL"
    
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
        return "RIESGO MODERADO", puntaje, "EN SEGUIMENTO"
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
# INTERFAZ PRINCIPAL CON TÍTULOS MEJORADOS
# ==================================================

# TÍTULO PRINCIPAL CON ESTILO MEJORADO
st.markdown("""
<div class="main-title">
    <h1 style="margin: 0; font-size: 2.8rem;">🏥 SISTEMA NIXON - Control de Anemia y Nutrición</h1>
    <p style="margin: 10px 0 0 0; font-size: 1.2rem; opacity: 0.9;">
    Sistema integrado con ajuste por altitud y evaluación nutricional
    </p>
</div>
""", unsafe_allow_html=True)

# ESTADO DE CONEXIÓN
if supabase:
    st.markdown("""
    <div style="background: #d1fae5; padding: 1rem; border-radius: 8px; border-left: 5px solid #10b981; margin-bottom: 2rem;">
        <p style="margin: 0; color: #065f46; font-weight: 500;">
        ✅ <strong>CONECTADO A SUPABASE</strong> - Sistema operativo
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE")

# PESTAÑAS PRINCIPALES
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registro Completo", 
    "🔍 Seguimiento Clínico", 
    "📈 Dashboard Nacional",
    "📋 Sistema de Citas",
    "⚙️ Configuración"
])

# ==================================================
# PESTAÑA 1: REGISTRO COMPLETO
# ==================================================

with tab1:
    st.markdown('<div class="section-title-blue">📝 Registro Completo de Paciente</div>', unsafe_allow_html=True)
    
    with st.form("formulario_completo"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">👤 Datos Personales</div>', unsafe_allow_html=True)
            dni = st.text_input("DNI*", placeholder="Ej: 87654321")
            nombre_completo = st.text_input("Nombre Completo*", placeholder="Ej: Ana García Pérez")
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
            peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1)
            talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1)
            genero = st.selectbox("Género*", GENEROS)
            telefono = st.text_input("Teléfono", placeholder="Ej: 987654321")
            estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE)
        
        with col2:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">🌍 Datos Geográficos</div>', unsafe_allow_html=True)
            region = st.selectbox("Región*", PERU_REGIONS)
            departamento = st.text_input("Departamento/Distrito", placeholder="Ej: Lima Metropolitana")
            
            if region in ALTITUD_REGIONES:
                altitud_info = ALTITUD_REGIONES[region]
                altitud_auto = altitud_info["altitud_promedio"]
                
                st.markdown(f"""
                <div class="metric-card-purple">
                    <h4 style="margin: 0 0 10px 0; color: #5b21b6;">🏔️ Altitud {region}</h4>
                    <p style="margin: 5px 0;"><strong>Rango:</strong> {altitud_info['altitud_min']} - {altitud_info['altitud_max']} msnm</p>
                    <p style="margin: 5px 0;"><strong>Promedio:</strong> {altitud_info['altitud_promedio']} msnm</p>
                </div>
                """, unsafe_allow_html=True)
                
                altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, altitud_auto)
            else:
                altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, 500)
            
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">💰 Factores Socioeconómicos</div>', unsafe_allow_html=True)
            nivel_educativo = st.selectbox("Nivel Educativo", NIVELES_EDUCATIVOS)
            acceso_agua_potable = st.checkbox("Acceso a agua potable")
            tiene_servicio_salud = st.checkbox("Tiene servicio de salud")
        
        st.markdown("---")
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">🩺 Parámetros Clínicos</div>', unsafe_allow_html=True)
            hemoglobina_medida = st.number_input("Hemoglobina medida (g/dL)*", 5.0, 20.0, 11.0, 0.1)
            
            ajuste_hb = obtener_ajuste_hemoglobina(altitud_msnm)
            hemoglobina_ajustada = calcular_hemoglobina_ajustada(hemoglobina_medida, altitud_msnm)
            
            clasificacion, recomendacion, tipo_alerta = clasificar_anemia(hemoglobina_ajustada, edad_meses)
            
            # Mostrar clasificación con estilo y COLORES CORRECTOS
            if tipo_alerta == "error" or "SEVERA" in clasificacion.upper():
                st.markdown(f"""
                <div class="severity-critical">
                    <h4 style="margin: 0 0 10px 0; color: #dc2626;">🔴 {clasificacion}</h4>
                    <p style="margin: 0; color: #dc2626;">{recomendacion}</p>
                </div>
                """, unsafe_allow_html=True)
            elif tipo_alerta == "warning" or "MODERADA" in clasificacion.upper():
                st.markdown(f"""
                <div class="severity-moderate">
                    <h4 style="margin: 0 0 10px 0; color: #d97706;">🟠 {clasificacion}</h4>
                    <p style="margin: 0; color: #d97706;">{recomendacion}</p>
                </div>
                """, unsafe_allow_html=True)
            elif "LEVE" in clasificacion.upper():
                st.markdown(f"""
                <div class="severity-mild">
                    <h4 style="margin: 0 0 10px 0; color: #2563eb;">🔵 {clasificacion}</h4>
                    <p style="margin: 0; color: #2563eb;">{recomendacion}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="severity-normal">
                    <h4 style="margin: 0 0 10px 0; color: #16a34a;">🟢 {clasificacion}</h4>
                    <p style="margin: 0; color: #16a34a;">{recomendacion}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Métrica con estilo AZUL
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label" style="color: #1e40af;">HEMOGLOBINA AJUSTADA</div>
                <div class="highlight-number" style="color: #1d4ed8; font-size: 2rem;">{hemoglobina_ajustada:.1f} g/dL</div>
                <div style="font-size: 0.9rem; color: #4b5563;">
                Ajuste por altitud: {ajuste_hb:+.1f} g/dL
                </div>
            </div>
            """, unsafe_allow_html=True)
            
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
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">📋 Factores de Riesgo</div>', unsafe_allow_html=True)
            
            st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">🏥 Factores Clínicos</div>', unsafe_allow_html=True)
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS)
            
            st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">💰 Factores Socioeconómicos</div>', unsafe_allow_html=True)
            factores_sociales = st.multiselect("Seleccione factores sociales:", FACTORES_SOCIOECONOMICOS)
        
        submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GUARDAR", type="primary", use_container_width=True)
    
    if submitted:
        if not dni or not nombre_completo:
            st.error("❌ Complete DNI y nombre del paciente")
        else:
            # Cálculos
            nivel_riesgo, puntaje, estado = calcular_riesgo_anemia(
                hemoglobina_ajustada,
                edad_meses,
                factores_clinicos,
                factores_sociales
            )
            
            sugerencias = generar_sugerencias(nivel_riesgo, hemoglobina_ajustada, edad_meses)
            
            estado_peso, estado_talla, estado_nutricional = evaluar_estado_nutricional(
                edad_meses, peso_kg, talla_cm, genero
            )
            
            parametros_simulados = generar_parametros_hematologicos(hemoglobina_ajustada, edad_meses)
            interpretacion_auto = interpretar_analisis_hematologico(
                parametros_simulados['ferritina'],
                parametros_simulados['chcm'],
                parametros_simulados['reticulocitos'], 
                parametros_simulados['transferrina'],
                hemoglobina_ajustada,
                edad_meses
            )
            
            # Mostrar resultados con COLORES CORRECTOS
            st.markdown("---")
            st.markdown('<div class="section-title-green" style="color: #059669; font-size: 1.5rem;">📊 EVALUACIÓN INTEGRAL DEL PACIENTE</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            # ESTADO DE ANEMIA - IZQUIERDA
            with col1:
                st.markdown('<div class="section-title-blue" style="font-size: 1.2rem; color: #1e40af;">🩺 ESTADO DE ANEMIA</div>', unsafe_allow_html=True)

                # Clasificación OMS con COLORES DIFERENTES
                if clasificacion == "ANEMIA SEVERA":
                    st.markdown(f"""
                    <div style="background-color: #fee2e2; border-left: 5px solid #dc2626; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #dc2626;">🔴 {clasificacion}</h4>
                        <p style="margin: 0;"><strong>Hemoglobina:</strong> {hemoglobina_ajustada:.1f} g/dL</p>
                        <p style="margin: 5px 0;"><strong>Edad:</strong> {edad_meses} meses</p>
                        <p style="margin: 5px 0; color: #dc2626;"><strong>⚠️ {recomendacion}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                elif clasificacion == "ANEMIA MODERADA":
                    st.markdown(f"""
                    <div style="background-color: #fef3c7; border-left: 5px solid #d97706; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #d97706;">🟠 {clasificacion}</h4>
                        <p style="margin: 0;"><strong>Hemoglobina:</strong> {hemoglobina_ajustada:.1f} g/dL</p>
                        <p style="margin: 5px 0;"><strong>Edad:</strong> {edad_meses} meses</p>
                        <p style="margin: 5px 0; color: #d97706;"><strong>⚠️ {recomendacion}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                elif clasificacion == "ANEMIA LEVE":
                    st.markdown(f"""
                    <div style="background-color: #dbeafe; border-left: 5px solid #2563eb; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #2563eb;">🔵 {clasificacion}</h4>
                        <p style="margin: 0;"><strong>Hemoglobina:</strong> {hemoglobina_ajustada:.1f} g/dL</p>
                        <p style="margin: 5px 0;"><strong>Edad:</strong> {edad_meses} meses</p>
                        <p style="margin: 5px 0; color: #2563eb;"><strong>⚠️ {recomendacion}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #d1fae5; border-left: 5px solid #16a34a; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <h4 style="margin: 0 0 10px 0; color: #16a34a;">🟢 {clasificacion}</h4>
                        <p style="margin: 0;"><strong>Hemoglobina:</strong> {hemoglobina_ajustada:.1f} g/dL</p>
                        <p style="margin: 5px 0;"><strong>Edad:</strong> {edad_meses} meses</p>
                        <p style="margin: 5px 0; color: #16a34a;"><strong>✅ {recomendacion}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)

                # NIVEL DE RIESGO con COLORES DIFERENTES
                st.markdown("---")
                st.markdown('<div class="section-title-blue" style="font-size: 1.2rem; color: #1e40af;">📈 NIVEL DE RIESGO</div>', unsafe_allow_html=True)

                if "ALTO" in nivel_riesgo:
                    st.markdown(f"""
                    <div style="background-color: #fee2e2; border: 2px solid #dc2626; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center;">
                        <div style="font-size: 1.2rem; color: #dc2626; font-weight: bold; margin-bottom: 10px;">
                        🚨 RIESGO DE ANEMIA
                        </div>
                        <div style="font-size: 2rem; color: #dc2626; font-weight: bold;">
                        {nivel_riesgo}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 10px;">
                        Puntaje: {puntaje}/60 | Estado: {estado}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif "MODERADO" in nivel_riesgo:
                    st.markdown(f"""
                    <div style="background-color: #fef3c7; border: 2px solid #d97706; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center;">
                        <div style="font-size: 1.2rem; color: #d97706; font-weight: bold; margin-bottom: 10px;">
                        ⚠️ RIESGO DE ANEMIA
                        </div>
                        <div style="font-size: 2rem; color: #d97706; font-weight: bold;">
                        {nivel_riesgo}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 10px;">
                        Puntaje: {puntaje}/60 | Estado: {estado}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #d1fae5; border: 2px solid #16a34a; padding: 20px; border-radius: 10px; margin: 10px 0; text-align: center;">
                        <div style="font-size: 1.2rem; color: #16a34a; font-weight: bold; margin-bottom: 10px;">
                        ✅ RIESGO DE ANEMIA
                        </div>
                        <div style="font-size: 2rem; color: #16a34a; font-weight: bold;">
                        {nivel_riesgo}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 10px;">
                        Puntaje: {puntaje}/60 | Estado: {estado}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ESTADO NUTRICIONAL - DERECHA
            with col2:
                st.markdown("---")
                st.markdown('<div class="section-title-blue" style="font-size: 1.2rem; color: #1e40af;">🍎 ESTADO NUTRICIONAL</div>', unsafe_allow_html=True)
                
                # Verificar si tenemos datos para evaluar
                if edad_meses > 0 and peso_kg > 0 and talla_cm > 0:
                    # Mostrar datos básicos
                    col_nut1, col_nut2, col_nut3 = st.columns(3)
                    
                    with col_nut1:
                        st.markdown(f"""
                        <div style="background-color: #dbeafe; border-radius: 8px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.9rem; color: #1e40af; font-weight: bold;">EDAD</div>
                            <div style="font-size: 1.5rem; color: #1d4ed8; font-weight: bold;">{edad_meses}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">meses</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_nut2:
                        st.markdown(f"""
                        <div style="background-color: #d1fae5; border-radius: 8px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.9rem; color: #059669; font-weight: bold;">PESO</div>
                            <div style="font-size: 1.5rem; color: #10b981; font-weight: bold;">{peso_kg:.1f}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">kg</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_nut3:
                        st.markdown(f"""
                        <div style="background-color: #f3e8ff; border-radius: 8px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.9rem; color: #6d28d9; font-weight: bold;">TALLA</div>
                            <div style="font-size: 1.5rem; color: #7c3aed; font-weight: bold;">{talla_cm:.1f}</div>
                            <div style="font-size: 0.8rem; color: #6b7280;">cm</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Mostrar evaluación nutricional con COLORES según severidad
                    if "DESNUTRICIÓN" in estado_nutricional.upper() or "SEVER" in estado_nutricional.upper():
                        color_fondo = "#fee2e2"
                        color_borde = "#dc2626"
                        color_texto = "#dc2626"
                        icono = "🔴"
                    elif "BAJO PESO" in estado_nutricional.upper() or "RIESGO" in estado_nutricional.upper():
                        color_fondo = "#fef3c7"
                        color_borde = "#d97706"
                        color_texto = "#d97706"
                        icono = "🟠"
                    elif "SOBREPESO" in estado_nutricional.upper() or "OBESIDAD" in estado_nutricional.upper():
                        color_fondo = "#fef3c7"
                        color_borde = "#d97706"
                        color_texto = "#d97706"
                        icono = "🟠"
                    else:
                        color_fondo = "#d1fae5"
                        color_borde = "#16a34a"
                        color_texto = "#16a34a"
                        icono = "🟢"
                    
                    st.markdown(f"""
                    <div style="background-color: {color_fondo}; border-left: 5px solid {color_borde}; padding: 15px; border-radius: 8px; margin-top: 1rem;">
                        <div style="font-size: 1.1rem; color: {color_texto}; font-weight: bold; margin-bottom: 10px;">
                        {icono} EVALUACIÓN NUTRICIONAL
                        </div>
                        <div style="font-size: 1.5rem; color: {color_texto}; font-weight: bold; text-align: center;">
                        {estado_nutricional}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 10px;">
                        <strong>Peso para la edad:</strong> {estado_peso}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
                        <strong>Talla para la edad:</strong> {estado_talla}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
                        <strong>Género:</strong> {genero}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mostrar alerta si hay problemas nutricionales
                    if estado_nutricional not in ["Normal", "Adecuado", "Saludable", "NORMAL"]:
                        st.warning(f"⚠️ **ALERTA NUTRICIONAL**: Se recomienda evaluación por especialista en nutrición pediátrica.")
                
                else:
                    # Datos incompletos
                    st.warning("⚠️ **DATOS NUTRICIONALES INCOMPLETOS**")
                    st.info("Complete edad, peso y talla para evaluación nutricional")
            
            # SUGERENCIAS - ANCHO COMPLETO
            st.markdown('<div class="section-title-green" style="color: #059669; font-size: 1.3rem; margin-top: 20px;">💡 PLAN DE ACCIÓN Y RECOMENDACIONES</div>', unsafe_allow_html=True)
            
            # Contenedor para sugerencias con color AMARILLO suave
            st.markdown(f"""
            <div style="background-color: #fef3c7; border: 2px solid #d97706; padding: 20px; border-radius: 10px; margin: 10px 0;">
                <div style="font-size: 1.2rem; color: #92400e; font-weight: bold; margin-bottom: 15px;">
                📋 RECOMENDACIONES ESPECÍFICAS
                </div>
                <div style="color: #78350f; line-height: 1.6;">
                {sugerencias.replace(chr(10), '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # GUARDAR EN SUPABASE
            if supabase:
                with st.spinner("Verificando y guardando datos..."):
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
# PESTAÑA 2: SEGUIMIENTO CLÍNICO COMPLETO
# ==================================================

with tab2:
    st.markdown("""
    <div class="main-title" style="background: linear-gradient(135deg, #10b981 0%, #047857 100%); padding: 2rem;">
        <h2 style="margin: 0; color: white;">🔬 SEGUIMIENTO CLÍNICO COMPLETO</h2>
        <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">
        Sistema paso a paso basado en hemoglobina inicial y biomarcadores específicos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # PASO 1: SELECCIÓN DE PACIENTE EXISTENTE
    # ============================================
    st.markdown("""
    <div class="section-title-blue" style="margin-top: 0;">
        👤 PASO 1: Seleccionar Paciente para Seguimiento
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener lista de pacientes
    pacientes_df = obtener_datos_supabase()
    
    if not pacientes_df.empty:
        # Crear lista para selector
        pacientes_lista = [f"{row['nombre_apellido']} (DNI: {row['dni']})" 
                          for _, row in pacientes_df.iterrows()]
        
        # Selector de paciente
        paciente_seleccionado = st.selectbox(
            "Seleccione un paciente del sistema:",
            pacientes_lista,
            index=0,
            help="Seleccione un paciente ya registrado para iniciar seguimiento"
        )
        
        # Extraer DNI del seleccionado
        if paciente_seleccionado:
            dni_seleccionado = paciente_seleccionado.split("DNI: ")[1].split(")")[0]
            paciente_data = pacientes_df[pacientes_df['dni'] == dni_seleccionado].iloc[0]
            
            # Mostrar resumen del paciente
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.markdown(f"""
                <div class="metric-card-blue">
                    <div class="metric-label">PACIENTE</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #1e40af;">
                    {paciente_data['nombre_apellido']}
                    </div>
                    <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
                    Edad: {paciente_data['edad_meses']} meses
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info2:
                hb_original = paciente_data.get('hemoglobina_dl1', 0)
                hb_ajustada = calcular_hemoglobina_ajustada(
                    hb_original, 
                    paciente_data.get('altitud_msnm', 0)
                )
                
                st.markdown(f"""
                <div class="metric-card-purple">
                    <div class="metric-label">HEMOGLOBINA</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #5b21b6;">
                    {hb_ajustada:.1f} g/dL
                    </div>
                    <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
                    Original: {hb_original:.1f} g/dL
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info3:
                riesgo_actual = paciente_data.get('riesgo', 'No evaluado')
                color_riesgo = {
                    'ALTO RIESGO': 'highlight-red',
                    'RIESGO MODERADO': 'highlight-yellow',
                    'BAJO RIESGO': 'highlight-green'
                }.get(riesgo_actual, 'highlight-blue')
                
                st.markdown(f"""
                <div class="metric-card-green">
                    <div class="metric-label">RIESGO ACTUAL</div>
                    <div class="highlight-number {color_riesgo}">
                    {riesgo_actual}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ============================================
            # PASO 2: FILTRO RÁPIDO DE HEMOGLOBINA (DECISIÓN)
            # ============================================
            st.markdown("""
            <div class="section-title-green">
                🩸 PASO 2: Filtro Rápido de Hemoglobina - Decisión Clínica
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar clasificación actual
            clasificacion, recomendacion, tipo_alerta = clasificar_anemia(
                hb_ajustada, 
                paciente_data['edad_meses']
            )
            
            # Tarjeta de clasificación
            if tipo_alerta == "error":
                st.markdown(f"""
                <div class="severity-critical">
                    <h3 style="margin: 0 0 10px 0; color: #dc2626;">🔴 {clasificacion}</h3>
                    <p style="margin: 0; font-size: 1.1rem;"><strong>Seguimiento:</strong> {recomendacion}</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #6b7280;">
                    ⚠️ <em>Según OMS: Hb {"< 7.0" if hb_ajustada < 7.0 else "7.0-9.9" if hb_ajustada < 10.0 else "10.0-10.9"} g/dL</em>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            elif tipo_alerta == "warning":
                st.markdown(f"""
                <div class="severity-moderate">
                    <h3 style="margin: 0 0 10px 0; color: #d97706;">🟠 {clasificacion}</h3>
                    <p style="margin: 0; font-size: 1.1rem;"><strong>Seguimiento:</strong> {recomendacion}</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #6b7280;">
                    📋 <em>Según OMS: Hb {"< 7.0" if hb_ajustada < 7.0 else "7.0-9.9" if hb_ajustada < 10.0 else "10.0-10.9"} g/dL</em>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            elif tipo_alerta == "success":
                st.markdown(f"""
                <div class="severity-normal">
                    <h3 style="margin: 0 0 10px 0; color: #16a34a;">🟢 {clasificacion}</h3>
                    <p style="margin: 0; font-size: 1.1rem;"><strong>Seguimiento:</strong> {recomendacion}</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9rem; color: #6b7280;">
                    ✅ <em>Según OMS: Hb ≥ 11.0 g/dL</em>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # ============================================
            # DECISIÓN: ¿QUÉ TIPO DE SEGUIMIENTO?
            # ============================================
            st.markdown("""
            <div class="section-title-blue">
                📋 PASO 3: Decisión - Tipo de Seguimiento Requerido
            </div>
            """, unsafe_allow_html=True)
            
            # Lógica según clasificación
            if clasificacion in ["ANEMIA SEVERA", "ANEMIA MODERADA"]:
                st.warning("""
                **🚨 REQUIERE ANÁLISIS COMPLETO DE BIOMARCADORES**
                
                **Protocolo activado:**
                1. Análisis de biomarcadores específicos
                2. Diagnóstico etiológico
                3. Tratamiento personalizado
                4. Seguimiento intensivo
                """)
                
                # Botón para ir a análisis completo
                if st.button("🧪 INICIAR ANÁLISIS DE BIOMARCADORES", 
                           type="primary",
                           use_container_width=True):
                    st.session_state['analisis_completo'] = True
                    st.session_state['paciente_actual'] = paciente_data.to_dict()
                    st.rerun()
            
            elif clasificacion == "ANEMIA LEVE":
                st.info("""
                **🟡 SEGUIMIENTO NUTRICIONAL BÁSICO**
                
                **Protocolo activado:**
                1. Suplemento de hierro según edad
                2. Recomendaciones alimentarias
                3. Control cada 6 meses
                4. Educación nutricional
                """)
                
                # Botón para seguimiento nutricional
                if st.button("🍎 INICIAR SEGUIMIENTO NUTRICIONAL",
                           type="secondary",
                           use_container_width=True):
                    st.session_state['seguimiento_nutricional'] = True
                    st.session_state['paciente_actual'] = paciente_data.to_dict()
                    st.rerun()
            
            else:
                st.success("""
                **🟢 SEGUIMIENTO RUTINARIO**
                
                **Protocolo activado:**
                1. Educación preventiva
                2. Control anual
                3. Monitoreo de crecimiento
                """)
                
                st.button("📝 REGISTRAR CONTROL RUTINARIO",
                         use_container_width=True)
            
            st.markdown("---")
            
            # ============================================
            # SECCIÓN CONDICIONAL: ANÁLISIS COMPLETO
            # ============================================
            if st.session_state.get('analisis_completo', False) and \
               st.session_state.get('paciente_actual', {}).get('dni') == dni_seleccionado:
                
                st.markdown("""
                <div class="section-title-red">
                    🧪 ANÁLISIS COMPLETO DE BIOMARCADORES
                </div>
                
                <div style="background: #fef2f2; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <p style="color: #7f1d1d; margin: 0;">
                    ⚠️ <strong>Nota importante:</strong> Como se menciona en la literatura, 
                    la deficiencia de hierro no es la única causa de anemia. Se deben 
                    considerar otros biomarcadores para evaluar completamente el estado del paciente.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # FORMULARIO DE BIOMARCADORES
                with st.form("form_biomarcadores_completos"):
                    st.markdown("""
                    <div class="section-title-blue" style="font-size: 1.4rem;">
                        🔬 Biomarcadores Específicos (Según Evidencia Científica)
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_bio1, col_bio2 = st.columns(2)
                    
                    with col_bio1:
                        st.markdown("**🩸 CONTENIDO DE HIERRO CORPORAL**")
                        hierro_serico = st.number_input("Hierro sérico (µg/dL)", 
                                                       min_value=0.0, max_value=500.0, value=60.0)
                        ferritina = st.number_input("Ferritina (ng/mL)", 
                                                   min_value=0.0, max_value=1000.0, value=15.0)
                        transferrina = st.number_input("Transferrina (mg/dL)", 
                                                      min_value=0.0, max_value=800.0, value=250.0)
                        saturacion_transferrina = st.number_input("Saturación de transferrina (%)", 
                                                                 min_value=0.0, max_value=100.0, value=20.0)
                    
                    with col_bio2:
                        st.markdown("**🦠 CONTRIBUCIÓN INFLAMATORIA**")
                        pcr = st.number_input("Proteína C Reactiva (mg/dL)", 
                                             min_value=0.0, max_value=50.0, value=0.3, step=0.1)
                        vsg = st.number_input("VSG (mm/h)", 
                                             min_value=0.0, max_value=100.0, value=15.0)
                        leucocitos = st.number_input("Leucocitos (x10³/µL)", 
                                                    min_value=0.0, max_value=50.0, value=8.0)
                        
                        st.markdown("**💊 OTROS NUTRIENTES**")
                        folato = st.number_input("Folato (ng/mL)", 
                                                min_value=0.0, max_value=50.0, value=6.0)
                        vitamina_b12 = st.number_input("Vitamina B12 (pg/mL)", 
                                                      min_value=0.0, max_value=2000.0, value=300.0)
                        vitamina_a = st.number_input("Vitamina A - Retinol (µg/dL)", 
                                                    min_value=0.0, max_value=200.0, value=25.0)
                    
                    # Fecha de análisis
                    fecha_analisis = st.date_input("Fecha del análisis de biomarcadores")
                    
                    submit_biomarcadores = st.form_submit_button(
                        "🎯 GENERAR DIAGNÓSTICO ETIOLÓGICO",
                        type="primary",
                        use_container_width=True
                    )
                
                if submit_biomarcadores:
                    # ============================================
                    # DIAGNÓSTICO AUTOMÁTICO
                    # ============================================
                    st.markdown("---")
                    st.markdown("""
                    <div class="section-title-green">
                        🎯 DIAGNÓSTICO ETIOLÓGICO AUTOMÁTICO
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Evaluar cada posible causa
                    causas = []
                    
                    # 1. Deficiencia de Hierro
                    if ferritina < 15 or hierro_serico < 50:
                        causas.append({
                            "causa": "DEFICIENCIA DE HIERRO",
                            "severidad": "🔴 SEVERA" if ferritina < 15 else "🟠 MODERADA",
                            "evidencia": f"Ferritina: {ferritina} ng/mL, Hierro: {hierro_serico} µg/dL",
                            "recomendacion": "Suplementación con hierro elemental 3-6 mg/kg/día"
                        })
                    
                    # 2. Inflamación/Infección
                    if pcr > 0.5 or vsg > 20:
                        causas.append({
                            "causa": "ANEMIA INFLAMATORIA/INFECCIOSA",
                            "severidad": "🟠 MODERADA",
                            "evidencia": f"PCR: {pcr} mg/dL, VSG: {vsg} mm/h",
                            "recomendacion": "Tratar proceso inflamatorio/infeccioso primero"
                        })
                    
                    # 3. Deficiencia de Folato
                    if folato < 5.4:
                        causas.append({
                            "causa": "DEFICIENCIA DE FOLATO",
                            "severidad": "🟡 LEVE",
                            "evidencia": f"Folato: {folato} ng/mL",
                            "recomendacion": "Suplemento de folato 100-200 µg/día"
                        })
                    
                    # 4. Deficiencia de Vitamina B12
                    if vitamina_b12 < 200:
                        causas.append({
                            "causa": "DEFICIENCIA DE VITAMINA B12",
                            "severidad": "🟡 LEVE",
                            "evidencia": f"Vitamina B12: {vitamina_b12} pg/mL",
                            "recomendacion": "Suplemento de B12 1-2 µg/kg/día"
                        })
                    
                    # 5. Deficiencia de Vitamina A
                    if vitamina_a < 20:
                        causas.append({
                            "causa": "DEFICIENCIA DE VITAMINA A",
                            "severidad": "🟡 LEVE",
                            "evidencia": f"Vitamina A: {vitamina_a} µg/dL",
                            "recomendacion": "Suplemento de vitamina A 100,000 UI (dosis única)"
                        })
                    
                    # Mostrar diagnóstico
                    if causas:
                        st.success("**🔍 SE IDENTIFICARON LAS SIGUIENTES CAUSAS:**")
                        
                        for i, causa in enumerate(causas, 1):
                            with st.expander(f"{i}. {causa['severidad']} {causa['causa']}", expanded=True):
                                col_diag1, col_diag2 = st.columns([2, 1])
                                
                                with col_diag1:
                                    st.markdown(f"""
                                    **Evidencia:** {causa['evidencia']}
                                    
                                    **Recomendación:** {causa['recomendacion']}
                                    """)
                                
                                with col_diag2:
                                    if "HIERRO" in causa['causa']:
                                        st.button("💊 Calcular dosis de hierro", 
                                                 key=f"hierro_{i}",
                                                 use_container_width=True)
                                    elif "INFLAMATORIA" in causa['causa']:
                                        st.button("🦠 Ver protocolo antiinflamatorio",
                                                 key=f"inflam_{i}",
                                                 use_container_width=True)
                    else:
                        st.info("**✅ NO SE IDENTIFICARON DEFICIENCIAS ESPECÍFICAS**")
                        st.markdown("""
                        **Posibles causas adicionales a considerar:**
                        - Anemia hemolítica
                        - Anemia aplásica
                        - Enfermedades crónicas
                        - Factores genéticos
                        """)
                    
                    # ============================================
                    # BOTÓN DE CONSUMO DE HIERRO
                    # ============================================
                    st.markdown("---")
                    st.markdown("""
                    <div class="section-title-blue">
                        ✅ SEGUIMIENTO DE CONSUMO DE HIERRO
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.form("form_consumo_hierro"):
                        st.markdown("**¿El paciente está consumiendo suplemento de hierro?**")
                        
                        col_cons1, col_cons2 = st.columns(2)
                        
                        with col_cons1:
                            consumiendo = st.radio(
                                "Estado actual:",
                                ["Sí, regularmente", "Sí, irregularmente", "No"],
                                horizontal=True
                            )
                            
                            if "Sí" in consumiendo:
                                dosis = st.number_input("Dosis actual (mg/día)", 
                                                       min_value=1, max_value=100, value=15)
                                frecuencia = st.selectbox("Frecuencia", 
                                                         ["Diario", "3 veces/semana", "Semanal", "Otra"])
                        
                        with col_cons2:
                            fecha_inicio = st.date_input("Fecha de inicio de suplementación")
                            proximo_control = st.date_input("Próximo control recomendado")
                            adherencia = st.slider("Adherencia estimada (%)", 0, 100, 80)
                        
                        efectos_adversos = st.text_area("Efectos adversos observados", 
                                                       placeholder="Ej: Náuseas leves, estreñimiento...")
                        
                        submit_consumo = st.form_submit_button(
                            "💾 GUARDAR SEGUIMIENTO DE HIERRO",
                            use_container_width=True
                        )
                    
                    if submit_consumo:
                        # Mostrar mensaje de éxito
                        st.success("✅ Seguimiento de hierro guardado")
                        
                        # Mostrar recomendaciones
                        st.markdown("---")
                        st.markdown("""
                        <div class="section-title-green">
                            🍎 RECOMENDACIONES ALIMENTARIAS ESPECÍFICAS
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Recomendaciones según deficiencias
                        recomendaciones_alimentarias = []
                        
                        for causa in causas:
                            if "HIERRO" in causa['causa']:
                                recomendaciones_alimentarias.append("""
                                **🍖 Alimentos ricos en hierro HEMO:**
                                - Carnes rojas magras (3-4 veces/semana)
                                - Hígado (1 vez/semana)
                                - Pollo y pescado
                                
                                **🥦 Alimentos ricos en hierro NO HEMO:**
                                - Lentejas, frijoles, garbanzos
                                - Espinacas, acelgas
                                - Cereales fortificados
                                
                                **🍊 Potenciadores de absorción:**
                                - Vitamina C: naranja, kiwi, pimiento
                                - Combinar carne + vegetales
                                """)
                            
                            if "FOLATO" in causa['causa']:
                                recomendaciones_alimentarias.append("""
                                **🥬 Alimentos ricos en folato:**
                                - Espinacas, brócoli, espárragos
                                - Legumbres: lentejas, garbanzos
                                - Aguacate, naranja
                                - Cereales fortificados
                                """)
                            
                            if "B12" in causa['causa']:
                                recomendaciones_alimentarias.append("""
                                **🥩 Alimentos ricos en vitamina B12:**
                                - Carnes rojas
                                - Pescado (salmón, atún)
                                - Huevos
                                - Lácteos fortificados
                                """)
                            
                            if "VITAMINA A" in causa['causa']:
                                recomendaciones_alimentarias.append("""
                                **🥕 Alimentos ricos en vitamina A:**
                                - Zanahorias, batatas
                                - Espinacas, kale
                                - Pimiento rojo
                                - Hígado
                                - Mango, melón
                                """)
                        
                        # Mostrar recomendaciones
                        if recomendaciones_alimentarias:
                            for i, rec in enumerate(recomendaciones_alimentarias, 1):
                                st.markdown(f"**{i}. Recomendación específica:**")
                                st.markdown(rec)
                        else:
                            st.info("**🍽️ RECOMENDACIONES GENERALES DE ALIMENTACIÓN SALUDABLE**")
                            st.markdown("""
                            - Dieta variada y balanceada
                            - Incluir todos los grupos alimenticios
                            - Evitar alimentos ultraprocesados
                            - Mantener buena hidratación
                            """)
                    
                    # ============================================
                    # GRÁFICO DE PROGRESO CORREGIDO
                    # ============================================
                    st.markdown("---")
                    st.markdown("""
                    <div class="section-title-blue">
                        📈 GRÁFICO DE PROGRESO DEL PACIENTE
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Datos simulados para el gráfico
                    fechas = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
                    valores_hb = [hb_ajustada]
                    
                    # Simular progreso basado en tratamiento
                    for i in range(1, 6):
                        mejora = np.random.uniform(0.2, 0.8) if "Sí" in consumiendo else np.random.uniform(0.0, 0.3)
                        nuevo_valor = valores_hb[0] + mejora * i
                        valores_hb.append(min(nuevo_valor, 15.0))
                    
                    # SOLO MOSTRAR GRÁFICO SI HAY DATOS REALES
                    if len(valores_hb) >= 2:
                        # Crear gráfico
                        fig = go.Figure()
                        
                        # Línea principal
                        fig.add_trace(go.Scatter(
                            x=fechas,
                            y=valores_hb,
                            mode='lines+markers',
                            name='Hemoglobina',
                            line=dict(color='#3b82f6', width=4),
                            marker=dict(size=10, color='#1e40af')
                        ))
                        
                        # Áreas de severidad
                        fig.add_hrect(y0=0, y1=6.9, fillcolor="rgba(239,68,68,0.1)", 
                                     line_width=0, annotation_text="Severa")
                        fig.add_hrect(y0=7.0, y1=9.9, fillcolor="rgba(245,158,11,0.1)", 
                                     line_width=0, annotation_text="Moderada")
                        fig.add_hrect(y0=10.0, y1=10.9, fillcolor="rgba(59,130,246,0.1)", 
                                     line_width=0, annotation_text="Leve")
                        fig.add_hrect(y0=11.0, y1=15, fillcolor="rgba(16,185,129,0.1)", 
                                     line_width=0, annotation_text="Normal")
                        
                        # Línea de meta
                        fig.add_hline(y=11.0, line_dash="dash", line_color="green",
                                     annotation_text="Meta: 11.0 g/dL")
                        
                        # Configurar layout
                        fig.update_layout(
                            title="<b>Evolución de Hemoglobina Ajustada</b>",
                            xaxis_title="<b>Meses de Seguimiento</b>",
                            yaxis_title="<b>Hemoglobina (g/dL)</b>",
                            template="plotly_white",
                            height=400,
                            showlegend=True,
                            legend=dict(
                                yanchor="top",
                                y=0.99,
                                xanchor="left",
                                x=0.01
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Resumen del progreso
                        col_prog1, col_prog2, col_prog3 = st.columns(3)
                        
                        with col_prog1:
                            variacion = valores_hb[-1] - valores_hb[0]
                            st.metric("Cambio total", f"{variacion:+.1f} g/dL")
                        
                        with col_prog2:
                            if valores_hb[-1] >= 11.0:
                                st.metric("Estado actual", "🟢 NORMAL", delta="Alcanzado")
                            elif valores_hb[-1] >= 10.0:
                                st.metric("Estado actual", "🟡 LEVE", 
                                         delta=f"{11.0 - valores_hb[-1]:.1f} para meta")
                            else:
                                st.metric("Estado actual", "🔴 SEVERA/MODERADA", 
                                         delta="Requiere atención")
                        
                        with col_prog3:
                            if len(valores_hb) > 1:
                                promedio_mensual = np.mean(np.diff(valores_hb))
                                st.metric("Mejora mensual", f"{promedio_mensual:+.2f} g/dL/mes")
                            else:
                                st.metric("Mejora mensual", "N/A", delta="Sin datos suficientes")
                    else:
                        st.warning("📊 **Se necesitan al menos 2 mediciones para mostrar el gráfico de progreso**")
                        st.info("Por favor, ingrese mediciones anteriores en la sección de Laboratorio del paciente")
                    
            # ============================================
            # SECCIÓN CONDICIONAL: SEGUIMIENTO NUTRICIONAL
            # ============================================
            elif st.session_state.get('seguimiento_nutricional', False) and \
                 st.session_state.get('paciente_actual', {}).get('dni') == dni_seleccionado:
                
                st.markdown("""
                <div class="section-title-green">
                    🍎 SEGUIMIENTO NUTRICIONAL BÁSICO
                </div>
                
                <div style="background: #f0fdf4; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
                    <p style="color: #065f46; margin: 0;">
                    📋 <strong>Protocolo para anemia leve:</strong> 
                    Seguimiento cada 6 meses con enfoque en nutrición y suplementación preventiva.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Suplementación según edad
                edad_meses = paciente_data['edad_meses']
                
                if edad_meses <= 24:
                    dosis = 3.0
                    formulacion = "Gotas pediátricas"
                else:
                    dosis = 2.0
                    formulacion = "Jarabe o comprimidos masticables"
                
                # Mostrar recomendaciones
                col_nut1, col_nut2 = st.columns(2)
                
                with col_nut1:
                    st.markdown(f"""
                    <div class="metric-card-blue">
                        <div class="metric-label">SUPLEMENTACIÓN</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1e40af;">
                        {dosis} mg/kg/día
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 10px;">
                        <strong>Formulación:</strong> {formulacion}<br>
                        <strong>Duración:</strong> 3 meses mínimo<br>
                        <strong>Control:</strong> Cada 6 meses
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_nut2:
                    st.markdown(f"""
                    <div class="metric-card-green">
                        <div class="metric-label">PRÓXIMO CONTROL</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #065f46;">
                        {datetime.now() + timedelta(days=180):%d/%m/%Y}
                        </div>
                        <div style="font-size: 0.9rem; color: #6b7280; margin-top: 10px;">
                        <strong>En 6 meses:</strong><br>
                        • Reevaluar hemoglobina<br>
                        • Ajustar suplementación<br>
                        • Evaluar crecimiento
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # BOTÓN DE CONSUMO DE HIERRO (versión simplificada)
                st.markdown("---")
                st.markdown("**✅ Control de Consumo de Suplemento**")
                
                with st.form("form_control_nutricional"):
                    consume_hierro = st.radio(
                        "¿El paciente consume suplemento de hierro actualmente?",
                        ["Sí", "No", "Interrumpido"]
                    )
                    
                    if consume_hierro == "Sí":
                        col_control1, col_control2 = st.columns(2)
                        
                        with col_control1:
                            dosis_actual = st.number_input("Dosis actual (mg/día)", 1, 100, 15)
                            frecuencia = st.selectbox("Frecuencia", 
                                                     ["Diario", "3 veces/semana", "Semanal"])
                        
                        with col_control2:
                            adherencia = st.slider("Adherencia (%)", 0, 100, 80)
                            efectos = st.multiselect("Efectos adversos", 
                                                    ["Ninguno", "Náuseas", "Estreñimiento", 
                                                     "Dolor abdominal", "Vómitos"])
                    
                    observaciones = st.text_area("Observaciones del control nutricional")
                    
                    if st.form_submit_button("💾 GUARDAR CONTROL NUTRICIONAL"):
                        st.success("✅ Control nutricional registrado")
    else:
        st.info("📝 No hay pacientes registrados en el sistema")
        st.markdown("""
        **Primero registre pacientes en la pestaña "Registro Completo"**
        
        Una vez registrados, podrá:
        1. Seleccionarlos para seguimiento
        2. Evaluar su hemoglobina
        3. Determinar tipo de seguimiento necesario
        4. Registrar biomarcadores específicos
        5. Hacer seguimiento de consumo de hierro
        6. Ver gráficos de progreso
        """)

# ==================================================
# PESTAÑA 3: DASHBOARD NACIONAL
# ==================================================

with tab3:
    st.markdown('<div class="section-title-blue">📊 Dashboard Nacional de Anemia y Nutrición</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Cargar Datos Nacionales", type="primary"):
        with st.spinner("Cargando datos nacionales..."):
            datos_nacionales = obtener_datos_supabase()
            
            if not datos_nacionales.empty:
                st.session_state.datos_nacionales = datos_nacionales
                st.success(f"✅ {len(datos_nacionales)} registros nacionales cargados")
            else:
                st.error("❌ No se pudieron cargar datos nacionales")
    
    if 'datos_nacionales' in st.session_state and not st.session_state.datos_nacionales.empty:
        datos = st.session_state.datos_nacionales
        
        # MÉTRICAS NACIONALES
        st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">🎯 Indicadores Nacionales</div>', unsafe_allow_html=True)
        
        col_nac1, col_nac2, col_nac3, col_nac4 = st.columns(4)
        
        with col_nac1:
            total_nacional = len(datos)
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label">TOTAL EVALUADOS</div>
                <div class="highlight-number highlight-blue">{total_nacional}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_nac2:
            if 'region' in datos.columns:
                regiones_unicas = datos['region'].nunique()
                st.markdown(f"""
                <div class="metric-card-green">
                    <div class="metric-label">REGIÓNES</div>
                    <div class="highlight-number highlight-green">{regiones_unicas}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_nac3:
            if 'hemoglobina_dl1' in datos.columns:
                hb_nacional = datos['hemoglobina_dl1'].mean()
                st.markdown(f"""
                <div class="metric-card-purple">
                    <div class="metric-label">HEMOGLOBINA NACIONAL</div>
                    <div class="highlight-number highlight-purple">{hb_nacional:.1f} g/dL</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col_nac4:
            if 'en_seguimiento' in datos.columns:
                seguimiento_nacional = datos['en_seguimiento'].sum()
                st.markdown(f"""
                <div class="metric-card-yellow">
                    <div class="metric-label">EN SEGUIMIENTO</div>
                    <div class="highlight-number highlight-yellow">{seguimiento_nacional}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # MAPA DE CALOR POR REGIÓN
        st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">📍 Mapa de Calor por Región</div>', unsafe_allow_html=True)
        
        if 'region' in datos.columns and 'hemoglobina_dl1' in datos.columns:
            region_stats = datos.groupby('region').agg({
                'hemoglobina_dl1': ['mean', 'count', 'min', 'max']
            }).round(2)
            
            region_stats.columns = ['hb_promedio', 'casos', 'hb_min', 'hb_max']
            region_stats = region_stats.reset_index()
            region_stats = region_stats.sort_values('hb_promedio', ascending=False)
            
            st.dataframe(region_stats, use_container_width=True)
            
            fig_region_heat = px.bar(
                region_stats,
                y='region',
                x='hb_promedio',
                color='hb_promedio',
                color_continuous_scale='RdYlGn',
                title='<b>Hemoglobina Promedio por Región</b>',
                text='hb_promedio',
                orientation='h',
                height=500
            )
            
            fig_region_heat.update_traces(
                texttemplate='%{text:.1f}',
                textposition='outside'
            )
            
            fig_region_heat.update_layout(
                xaxis_title="Hemoglobina Promedio (g/dL)",
                yaxis_title="Región",
                yaxis={'categoryorder': 'total ascending'}
            )
            
            st.plotly_chart(fig_region_heat, use_container_width=True)
        
        # TENDENCIAS
        st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">📈 Tendencias y Análisis</div>', unsafe_allow_html=True)
        
        col_tend1, col_tend2 = st.columns(2)
        
        with col_tend1:
            if 'edad_meses' in datos.columns:
                datos['edad_años'] = datos['edad_meses'] / 12
                fig_edad_dist = px.histogram(
                    datos,
                    x='edad_años',
                    nbins=10,
                    title='<b>Distribución por Edad</b>',
                    color_discrete_sequence=['#3498db'],
                    height=300
                )
                st.plotly_chart(fig_edad_dist, use_container_width=True)
        
        with col_tend2:
            if 'genero' in datos.columns:
                genero_counts = datos['genero'].value_counts()
                fig_genero_dist = px.pie(
                    values=genero_counts.values,
                    names=genero_counts.index.map({'M': 'Niños', 'F': 'Niñas'}).fillna('Otro'),
                    title='<b>Distribución por Género</b>',
                    color_discrete_sequence=['#e74c3c', '#3498db'],
                    height=300
                )
                st.plotly_chart(fig_genero_dist, use_container_width=True)
        
        # ANÁLISIS DE RIESGO
        st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">⚠️ Análisis de Riesgo Nacional</div>', unsafe_allow_html=True)
        
        if 'riesgo' in datos.columns:
            riesgo_counts = datos['riesgo'].value_counts()
            
            col_ries1, col_ries2 = st.columns([3, 1])
            
            with col_ries1:
                fig_riesgo = px.bar(
                    x=riesgo_counts.index,
                    y=riesgo_counts.values,
                    title='<b>Distribución de Niveles de Riesgo</b>',
                    color=riesgo_counts.values,
                    color_continuous_scale='Reds',
                    text=riesgo_counts.values,
                    height=400
                )
                
                fig_riesgo.update_traces(
                    texttemplate='%{text}',
                    textposition='outside'
                )
                
                st.plotly_chart(fig_riesgo, use_container_width=True)
            
            with col_ries2:
                for riesgo, count in riesgo_counts.items():
                    porcentaje = (count / total_nacional) * 100
                    st.markdown(f"""
                    <div class="metric-card-blue" style="margin-bottom: 10px;">
                        <div class="metric-label">{riesgo}</div>
                        <div class="highlight-number highlight-blue">{count}</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">{porcentaje:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # EXPORTAR REPORTE
        st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">📥 Exportar Reporte Nacional</div>', unsafe_allow_html=True)
        
        with st.expander("📥 **Exportar Reporte Completo**", expanded=False):
            csv = datos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 **Descargar CSV Completo**",
                data=csv,
                file_name=f"reporte_nacional_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="secondary"
            )
    
    else:
        st.info("👆 Presiona el botón 'Cargar Datos Nacionales' para ver el dashboard nacional")

# ==================================================
# PESTAÑA 4: SISTEMA DE CITAS MEJORADO Y CORREGIDO
# ==================================================

with tab4:
    st.markdown("""
    <div class="main-title" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 2rem;">
        <h2 style="margin: 0; color: white;">📅 SISTEMA DE CITAS Y RECORDATORIOS</h2>
        <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">
        Citas automáticas según nivel de anemia + Recordatorios + Calendario de seguimiento
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # FUNCIONES ESPECÍFICAS PARA CITAS AUTOMÁTICAS - VERSIÓN CORREGIDA
    # ============================================
    
    def calcular_frecuencia_cita(hemoglobina, edad_meses):
        """Calcula la frecuencia de citas según nivel de anemia"""
        if hemoglobina < 7:
            return "MENSUAL", 30  # Anemia severa
        elif hemoglobina < 10:
            return "TRIMESTRAL", 90  # Anemia moderada
        elif hemoglobina < 11:
            return "SEMESTRAL", 180  # Anemia leve
        else:
            return "ANUAL", 365  # Normal
    
    def crear_cita_automatica(dni_paciente, hemoglobina, edad_meses, tipo="CONTROL"):
        """Crea una cita automática según el nivel de anemia - VERSIÓN CORREGIDA CON MANEJO DE ERROR 11"""
        try:
            # INTENTAR 3 VECES CON PAUSA PARA ERRORES TEMPORALES
            for intento in range(3):
                try:
                    # Obtener información del paciente
                    response = supabase.table("alertas_hemoglobina")\
                        .select("*")\
                        .eq("dni", dni_paciente)\
                        .execute()
                    
                    if not response.data:
                        return False, "Paciente no encontrado"
                    
                    paciente = response.data[0]
                    
                    # Calcular fecha de próxima cita
                    frecuencia, dias = calcular_frecuencia_cita(hemoglobina, edad_meses)
                    fecha_cita = datetime.now() + timedelta(days=dias)
                    
                    # Determinar tipo de consulta según gravedad
                    if hemoglobina < 7:
                        tipo_consulta = "URGENCIA - Anemia Severa"
                        diagnostico = "Anemia severa requiere seguimiento intensivo"
                        tratamiento = "Suplementación inmediata + Control semanal"
                    elif hemoglobina < 10:
                        tipo_consulta = "SEGUIMIENTO - Anemia Moderada"
                        diagnostico = "Anemia moderada en tratamiento"
                        tratamiento = "Suplementación continua + Control mensual"
                    elif hemoglobina < 11:
                        tipo_consulta = "CONTROL - Anemia Leve"
                        diagnostico = "Anemia leve en vigilancia"
                        tratamiento = "Suplementación preventiva"
                    else:
                        tipo_consulta = "CONTROL PREVENTIVO"
                        diagnostico = "Estado normal, seguimiento preventivo"
                        tratamiento = "Mantenimiento nutricional"
                    
                    # Crear datos de la cita
                    cita_data = {
                        "dni_paciente": dni_paciente,
                        "fecha_cita": fecha_cita.strftime('%Y-%m-%d'),
                        "hora_cita": "09:00:00",
                        "tipo_consulta": tipo_consulta,
                        "diagnostico": diagnostico,
                        "tratamiento": tratamiento,
                        "observaciones": f"Cita automática generada por sistema. Frecuencia: {frecuencia}",
                        "investigador_responsable": "Sistema Automático",
                        "severidad_anemia": "SEVERA" if hemoglobina < 7 else "MODERADA" if hemoglobina < 10 else "LEVE" if hemoglobina < 11 else "NORMAL",
                        "suplemento_hierro": paciente.get('tipo_suplemento_hierro', 'Sulfato ferroso'),
                        "frecuencia_suplemento": paciente.get('frecuencia_suplemento', 'Diario'),
                        "proxima_cita": (fecha_cita + timedelta(days=dias)).strftime('%Y-%m-%d'),
                        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Insertar en Supabase
                    response = supabase.table("citas").insert(cita_data).execute()
                    
                    if response.data:
                        return True, f"Cita creada para {fecha_cita.strftime('%d/%m/%Y')} - Frecuencia: {frecuencia}"
                    else:
                        return False, "Error al crear cita"
                        
                except Exception as e:
                    error_str = str(e)
                    if ("Resource temporarily unavailable" in error_str or "Error 11" in error_str) and intento < 2:
                        time.sleep(1)  # Esperar 1 segundo y reintentar
                        continue
                    else:
                        raise e  # Relanzar el error si no es temporal
            
            return False, "Error después de múltiples intentos"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def obtener_recordatorios_pendientes():
        """Obtiene recordatorios de citas próximas"""
        try:
            hoy = datetime.now().date()
            proxima_semana = hoy + timedelta(days=7)
            
            response = supabase.table("citas")\
                .select("*, alertas_hemoglobina(*)")\
                .eq("alertas_hemoglobina.estado_paciente", "Activo")\
                .gte("fecha_cita", hoy.strftime('%Y-%m-%d'))\
                .lte("fecha_cita", proxima_semana.strftime('%Y-%m-%d'))\
                .execute()
            
            if response.data:
                recordatorios = []
                for cita in response.data:
                    paciente_info = cita.get('alertas_hemoglobina', {})
                    dias_restantes = (datetime.strptime(cita['fecha_cita'], '%Y-%m-%d').date() - hoy).days
                    
                    recordatorios.append({
                        'dni': paciente_info.get('dni', 'N/A'),
                        'nombre': paciente_info.get('nombre_apellido', 'Desconocido'),
                        'telefono': paciente_info.get('telefono', 'Sin teléfono'),
                        'fecha_cita': cita['fecha_cita'],
                        'hora_cita': cita.get('hora_cita', '09:00'),
                        'tipo_consulta': cita['tipo_consulta'],
                        'dias_restantes': dias_restantes,
                        'hemoglobina': paciente_info.get('hemoglobina_dl1', 'N/A'),
                        'prioridad': 'URGENTE' if dias_restantes <= 2 else 'PRÓXIMO' if dias_restantes <= 5 else 'PROGRAMADO'
                    })
                
                return recordatorios
            return []
            
        except Exception as e:
            st.error(f"Error obteniendo recordatorios: {str(e)}")
            return []
    
    def obtener_calendario_seguimiento():
        """Obtiene el calendario de seguimiento organizado por nivel de anemia"""
        try:
            # Obtener pacientes con anemia
            response = supabase.table("alertas_hemoglobina")\
                .select("*")\
                .or_("hemoglobina_dl1.lt.11,en_seguimiento.eq.true")\
                .execute()
            
            if not response.data:
                return []
            
            calendario = []
            
            for paciente in response.data:
                hemoglobina = paciente['hemoglobina_dl1']
                edad_meses = paciente['edad_meses']
                
                # Clasificar anemia
                if hemoglobina < 7:
                    nivel = "SEVERA"
                    frecuencia, dias = "MENSUAL", 30
                    emoji = "🔴"
                elif hemoglobina < 10:
                    nivel = "MODERADA"
                    frecuencia, dias = "TRIMESTRAL", 90
                    emoji = "🟡"
                elif hemoglobina < 11:
                    nivel = "LEVE"
                    frecuencia, dias = "SEMESTRAL", 180
                    emoji = "🟢"
                else:
                    nivel = "NORMAL"
                    frecuencia, dias = "ANUAL", 365
                    emoji = "✅"
                
                # Obtener última cita
                citas_response = supabase.table("citas")\
                    .select("fecha_cita, proxima_cita")\
                    .eq("dni_paciente", paciente['dni'])\
                    .order("fecha_cita", desc=True)\
                    .limit(1)\
                    .execute()
                
                ultima_cita = None
                proxima_cita = None
                
                if citas_response.data:
                    ultima_cita = citas_response.data[0].get('fecha_cita')
                    proxima_cita = citas_response.data[0].get('proxima_cita')
                
                # Si no tiene próxima cita, calcular automáticamente
                if not proxima_cita and paciente['en_seguimiento']:
                    if ultima_cita:
                        ultima_fecha = datetime.strptime(ultima_cita, '%Y-%m-%d')
                        proxima_fecha = ultima_fecha + timedelta(days=dias)
                    else:
                        proxima_fecha = datetime.now() + timedelta(days=30)
                    
                    proxima_cita = proxima_fecha.strftime('%Y-%m-%d')
                
                if proxima_cita:
                    dias_restantes = (datetime.strptime(proxima_cita, '%Y-%m-%d').date() - datetime.now().date()).days
                    
                    calendario.append({
                        'dni': paciente['dni'],
                        'nombre': paciente['nombre_apellido'],
                        'nivel_anemia': nivel,
                        'emoji': emoji,
                        'hemoglobina': hemoglobina,
                        'frecuencia': frecuencia,
                        'proxima_cita': proxima_cita,
                        'dias_restantes': dias_restantes,
                        'telefono': paciente.get('telefono', 'Sin teléfono'),
                        'prioridad': '🚨 URGENTE' if dias_restantes <= 7 else '⚠️ PRÓXIMO' if dias_restantes <= 30 else '📅 PROGRAMADO'
                    })
            
            # Ordenar por prioridad y fecha
            calendario.sort(key=lambda x: (x['dias_restantes'], -x['hemoglobina']))
            return calendario
            
        except Exception as e:
            st.error(f"Error obteniendo calendario: {str(e)}")
            return []
    
    # ============================================
    # INTERFAZ PRINCIPAL DEL SISTEMA DE CITAS
    # ============================================
    
    # Crear pestañas dentro de Sistema de Citas
    tab_citas1, tab_citas2, tab_citas3, tab_citas4 = st.tabs([
        "📅 Calendario de Seguimiento",
        "🔄 Generar Citas Automáticas",
        "🔔 Recordatorios Próximos",
        "📋 Historial de Citas"
    ])
    
    # ============================================
    # TAB 1: CALENDARIO DE SEGUIMIENTO
    # ============================================
    with tab_citas1:
        st.markdown('<div class="section-title-purple">📅 CALENDARIO DE SEGUIMIENTO POR NIVEL DE ANEMIA</div>', unsafe_allow_html=True)
        
        if st.button("🔄 Actualizar Calendario", key="actualizar_calendario"):
            with st.spinner("Cargando calendario..."):
                calendario = obtener_calendario_seguimiento()
                st.session_state.calendario_seguimiento = calendario
        
        if 'calendario_seguimiento' in st.session_state and st.session_state.calendario_seguimiento:
            calendario_df = pd.DataFrame(st.session_state.calendario_seguimiento)
            
            # Mostrar por nivel de anemia
            niveles = ["SEVERA", "MODERADA", "LEVE", "NORMAL"]
            
            for nivel in niveles:
                pacientes_nivel = calendario_df[calendario_df['nivel_anemia'] == nivel]
                
                if not pacientes_nivel.empty:
                    emoji = {"SEVERA": "🔴", "MODERADA": "🟡", "LEVE": "🟢", "NORMAL": "✅"}[nivel]
                    frecuencia = {"SEVERA": "MENSUAL", "MODERADA": "TRIMESTRAL", "LEVE": "SEMESTRAL", "NORMAL": "ANUAL"}[nivel]
                    
                    st.markdown(f"""
                    <div class="section-title-purple" style="font-size: 1.4rem; margin-top: 1.5rem;">
                        {emoji} ANEMIA {nivel} - Control {frecuencia}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for _, paciente in pacientes_nivel.iterrows():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            st.markdown(f"**{paciente['nombre']}**")
                            st.caption(f"DNI: {paciente['dni']} | Tel: {paciente['telefono']}")
                        
                        with col2:
                            st.markdown(f"**{paciente['hemoglobina']} g/dL**")
                            st.caption(f"Próxima: {paciente['proxima_cita']}")
                        
                        with col3:
                            if paciente['dias_restantes'] <= 0:
                                st.error(f"⚠️ VENCIDO {abs(paciente['dias_restantes'])} días")
                            elif paciente['dias_restantes'] <= 7:
                                st.warning(f"⏰ {paciente['dias_restantes']} días")
                            else:
                                st.info(f"📅 {paciente['dias_restantes']} días")
                        
                        with col4:
                            if st.button("📝", key=f"cita_{paciente['dni']}"):
                                st.session_state.crear_cita_paciente = paciente['dni']
                                st.rerun()
        else:
            st.info("👆 Presiona 'Actualizar Calendario' para cargar el calendario de seguimiento")
    
    # ============================================
    # TAB 2: GENERAR CITAS AUTOMÁTICAS
    # ============================================
    with tab_citas2:
        st.markdown('<div class="section-title-purple">🔄 GENERAR CITAS AUTOMÁTICAS POR NIVEL DE ANEMIA</div>', unsafe_allow_html=True)
        
        # Obtener pacientes que necesitan citas
        try:
            response = supabase.table("alertas_hemoglobina")\
                .select("*")\
                .or_("hemoglobina_dl1.lt.11,en_seguimiento.eq.true")\
                .execute()
            
            if response.data:
                pacientes_necesitan = []
                
                for paciente in response.data:
                    # Verificar si ya tiene cita próxima
                    citas_response = supabase.table("citas")\
                        .select("proxima_cita")\
                        .eq("dni_paciente", paciente['dni'])\
                        .gte("proxima_cita", datetime.now().strftime('%Y-%m-%d'))\
                        .execute()
                    
                    if not citas_response.data:
                        pacientes_necesitan.append({
                            'dni': paciente['dni'],
                            'nombre': paciente['nombre_apellido'],
                            'hemoglobina': paciente['hemoglobina_dl1'],
                            'edad_meses': paciente['edad_meses'],
                            'en_seguimiento': paciente['en_seguimiento'],
                            'riesgo': paciente.get('riesgo', 'N/A')
                        })
                
                if pacientes_necesitan:
                    st.info(f"📋 **{len(pacientes_necesitan)} pacientes necesitan cita programada**")
                    
                    # Crear tabla de pacientes
                    df_pacientes_citas = pd.DataFrame(pacientes_necesitan)
                    df_pacientes_citas['frecuencia'] = df_pacientes_citas['hemoglobina'].apply(
                        lambda x: "MENSUAL" if x < 7 else "TRIMESTRAL" if x < 10 else "SEMESTRAL" if x < 11 else "ANUAL"
                    )
                    
                    # Mostrar tabla
                    edited_df = st.data_editor(
                        df_pacientes_citas[['nombre', 'dni', 'hemoglobina', 'frecuencia', 'riesgo']],
                        column_config={
                            "nombre": "Paciente",
                            "dni": "DNI",
                            "hemoglobina": st.column_config.NumberColumn("Hb (g/dL)", format="%.1f"),
                            "frecuencia": "Frecuencia",
                            "riesgo": "Riesgo"
                        },
                        use_container_width=True
                    )
                    
                    # Botón para generar citas automáticas
                    col_gen1, col_gen2 = st.columns(2)
                    
                    with col_gen1:
                        if st.button("🎯 Generar Citas Seleccionadas", type="primary", use_container_width=True):
                            with st.spinner("Generando citas..."):
                                resultados = []
                                for _, paciente in df_pacientes_citas.iterrows():
                                    success, message = crear_cita_automatica(
                                        paciente['dni'],
                                        paciente['hemoglobina'],
                                        paciente['edad_meses']
                                    )
                                    resultados.append({
                                        'paciente': paciente['nombre'],
                                        'exito': success,
                                        'mensaje': message
                                    })
                                
                                # Mostrar resultados
                                st.success(f"✅ Citas generadas: {len([r for r in resultados if r['exito']])}/{len(resultados)}")
                                
                                for resultado in resultados:
                                    if resultado['exito']:
                                        st.info(f"✅ {resultado['paciente']}: {resultado['mensaje']}")
                                    else:
                                        st.error(f"❌ {resultado['paciente']}: {resultado['mensaje']}")
                    
                    with col_gen2:
                        if st.button("📋 Generar Todas las Citas", type="secondary", use_container_width=True):
                            with st.spinner("Generando todas las citas..."):
                                contador = 0
                                for _, paciente in df_pacientes_citas.iterrows():
                                    success, _ = crear_cita_automatica(
                                        paciente['dni'],
                                        paciente['hemoglobina'],
                                        paciente['edad_meses']
                                    )
                                    if success:
                                        contador += 1
                                
                                st.success(f"✅ {contador} citas generadas automáticamente")
                                time.sleep(2)
                                st.rerun()
                else:
                    st.success("🎉 Todos los pacientes ya tienen citas programadas")
                    
            else:
                st.info("📝 No hay pacientes que requieran seguimiento")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
        
        # Sección para crear cita manual
        st.markdown("---")
        st.markdown('<div class="section-title-purple" style="font-size: 1.2rem;">➕ CREAR CITA MANUAL</div>', unsafe_allow_html=True)
        
        with st.form("form_cita_manual"):
            col_man1, col_man2 = st.columns(2)
            
            with col_man1:
                # Buscar paciente
                pacientes_response = supabase.table("alertas_hemoglobina").select("dni, nombre_apellido").execute()
                
                if pacientes_response.data:
                    opciones_pacientes = {f"{p['nombre_apellido']} (DNI: {p['dni']})": p['dni'] 
                                         for p in pacientes_response.data}
                    
                    paciente_seleccionado = st.selectbox("Seleccionar paciente:", list(opciones_pacientes.keys()))
                    dni_paciente = opciones_pacientes[paciente_seleccionado]
                    
                    # Obtener datos del paciente
                    paciente_data_response = supabase.table("alertas_hemoglobina")\
                        .select("*")\
                        .eq("dni", dni_paciente)\
                        .execute()
                    
                    if paciente_data_response.data:
                        paciente_data = paciente_data_response.data[0]
                        st.info(f"**Hb actual:** {paciente_data['hemoglobina_dl1']} g/dL")
                        st.info(f"**Riesgo:** {paciente_data.get('riesgo', 'N/A')}")
            
            with col_man2:
                fecha_cita = st.date_input("Fecha de la cita", min_value=datetime.now())
                hora_cita = st.time_input("Hora de la cita", value=datetime.now().time())
                tipo_consulta = st.selectbox("Tipo de consulta", 
                                            ["Control", "Seguimiento", "Urgencia", "Reevaluación", "Vacunación"])
                
                # Sugerir frecuencia según hemoglobina
                if 'paciente_data' in locals():
                    hemoglobina = paciente_data['hemoglobina_dl1']
                    frecuencia_sugerida = "MENSUAL" if hemoglobina < 7 else "TRIMESTRAL" if hemoglobina < 10 else "SEMESTRAL" if hemoglobina < 11 else "ANUAL"
                    st.info(f"**Frecuencia sugerida:** {frecuencia_sugerida}")
            
            diagnostico = st.text_area("Diagnóstico", placeholder="Ej: Anemia leve por deficiencia de hierro")
            tratamiento = st.text_area("Tratamiento prescrito", placeholder="Ej: Sulfato ferroso 15 mg/día")
            observaciones = st.text_area("Observaciones", placeholder="Observaciones adicionales...")
            
            submit_cita = st.form_submit_button("💾 GUARDAR CITA MANUAL", use_container_width=True)
            
            if submit_cita and 'dni_paciente' in locals():
                try:
                    cita_data = {
                        "dni_paciente": dni_paciente,
                        "fecha_cita": fecha_cita.strftime('%Y-%m-%d'),
                        "hora_cita": hora_cita.strftime('%H:%M:%S'),
                        "tipo_consulta": tipo_consulta,
                        "diagnostico": diagnostico,
                        "tratamiento": tratamiento,
                        "observaciones": observaciones,
                        "investigador_responsable": "Usuario Manual",
                        "proxima_cita": (fecha_cita + timedelta(days=30)).strftime('%Y-%m-%d'),
                        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    response = supabase.table("citas").insert(cita_data).execute()
                    
                    if response.data:
                        st.success("✅ Cita manual guardada exitosamente")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar la cita")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # ============================================
    # TAB 3: RECORDATORIOS PRÓXIMOS - VERSIÓN CORREGIDA (SIN EMAIL/SMS)
    # ============================================
    with tab_citas3:
        st.markdown('<div class="section-title-purple">🔔 RECORDATORIOS DE CITAS PRÓXIMAS</div>', unsafe_allow_html=True)
        
        if st.button("🔄 Cargar Recordatorios", key="cargar_recordatorios"):
            with st.spinner("Buscando citas próximas..."):
                recordatorios = obtener_recordatorios_pendientes()
                st.session_state.recordatorios_pendientes = recordatorios
        
        if 'recordatorios_pendientes' in st.session_state:
            recordatorios_df = pd.DataFrame(st.session_state.recordatorios_pendientes)
            
            if not recordatorios_df.empty:
                # Mostrar por prioridad
                for prioridad in ['URGENTE', 'PRÓXIMO', 'PROGRAMADO']:
                    recordatorios_prioridad = recordatorios_df[recordatorios_df['prioridad'] == prioridad]
                    
                    if not recordatorios_prioridad.empty:
                        color = {
                            'URGENTE': '#dc2626',
                            'PRÓXIMO': '#d97706', 
                            'PROGRAMADO': '#2563eb'
                        }[prioridad]
                        
                        emoji = {
                            'URGENTE': '🚨',
                            'PRÓXIMO': '⚠️',
                            'PROGRAMADO': '📅'
                        }[prioridad]
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, {color}10 0%, {color}20 100%); 
                                 padding: 1rem; border-radius: 10px; border-left: 5px solid {color}; 
                                 margin: 1rem 0;">
                            <h4 style="margin: 0 0 10px 0; color: {color};">
                                {emoji} {prioridad} ({len(recordatorios_prioridad)} citas)
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for _, recordatorio in recordatorios_prioridad.iterrows():
                            col_rec1, col_rec2, col_rec3, col_rec4 = st.columns([3, 2, 2, 1])
                            
                            with col_rec1:
                                st.markdown(f"**{recordatorio['nombre']}**")
                                st.caption(f"DNI: {recordatorio['dni']}")
                            
                            with col_rec2:
                                st.markdown(f"**{recordatorio['fecha_cita']}**")
                                st.caption(f"Hora: {recordatorio['hora_cita']}")
                            
                            with col_rec3:
                                st.markdown(f"**{recordatorio['tipo_consulta']}**")
                                st.caption(f"Hb: {recordatorio['hemoglobina']} g/dL")
                            
                            with col_rec4:
                                if st.button("📞", key=f"llamar_{recordatorio['dni']}"):
                                    st.info(f"📞 Llamar al: {recordatorio['telefono']}")
                
                # Botones de acción - VERSIÓN CORREGIDA (SOLO LISTA)
                st.markdown("---")
                col_acc1, col_acc2 = st.columns(2)
                
                with col_acc1:
                    if st.button("📄 Generar lista de llamadas", use_container_width=True):
                        csv = recordatorios_df[['nombre', 'telefono', 'fecha_cita', 'hora_cita']].to_csv(index=False)
                        st.download_button(
                            label="📥 Descargar lista",
                            data=csv,
                            file_name=f"recordatorios_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col_acc2:
                    st.info("📞 Recordatorios por teléfono (modo manual)")
                    st.caption("Funcionalidad automática en desarrollo")
                        
            else:
                st.success("🎉 No hay recordatorios pendientes para la próxima semana")
        else:
            st.info("👆 Presiona 'Cargar Recordatorios' para ver citas próximas")
    
    # ============================================
    # TAB 4: HISTORIAL DE CITAS - VERSIÓN CORREGIDA
    # ============================================
    with tab_citas4:
        st.markdown('<div class="section-title-purple">📋 HISTORIAL COMPLETO DE CITAS</div>', unsafe_allow_html=True)
        
        # Función para obtener citas con información de anemia
        def obtener_citas_con_info_anemia():
            try:
                response_citas = supabase.table("citas").select("*").order("fecha_cita", desc=True).execute()
                citas = response_citas.data if response_citas.data else []
                
                if not citas:
                    return []
                
                citas_con_info = []
                
                for cita in citas:
                    dni = cita.get('dni_paciente')
                    if dni:
                        response_paciente = supabase.table("alertas_hemoglobina")\
                            .select("*")\
                            .eq("dni", dni)\
                            .execute()
                        
                        info_anemia = response_paciente.data[0] if response_paciente.data else {}
                        
                        cita_completa = {
                            **cita,
                            "info_anemia": info_anemia,
                            "nombre_paciente": info_anemia.get('nombre_apellido', 'Desconocido'),
                            "hemoglobina": info_anemia.get('hemoglobina_dl1', 'N/A'),
                            "clasificacion_anemia": clasificar_anemia_simple(
                                info_anemia.get('hemoglobina_dl1', 0),
                                info_anemia.get('edad_meses', 0)
                            ),
                            "riesgo": info_anemia.get('riesgo', 'N/A'),
                            "en_seguimiento": info_anemia.get('en_seguimiento', False)
                        }
                        citas_con_info.append(cita_completa)
                    else:
                        citas_con_info.append({
                            **cita,
                            "nombre_paciente": "Sin información",
                            "hemoglobina": "N/A",
                            "clasificacion_anemia": "N/A",
                            "riesgo": "N/A",
                            "en_seguimiento": False
                        })
                
                return citas_con_info
                
            except Exception as e:
                st.error(f"❌ Error al obtener citas: {str(e)}")
                return []
        
        def clasificar_anemia_simple(hemoglobina, edad_meses):
            if hemoglobina == 'N/A' or not hemoglobina:
                return "Sin datos"
            
            if edad_meses < 60:
                if hemoglobina >= 11.0:
                    return "Normal"
                elif hemoglobina >= 10.0:
                    return "Leve"
                elif hemoglobina >= 9.0:
                    return "Moderada"
                else:
                    return "Severa"
            else:
                if hemoglobina >= 12.0:
                    return "Normal"
                elif hemoglobina >= 11.0:
                    return "Leve"
                elif hemoglobina >= 10.0:
                    return "Moderada"
                else:
                    return "Severa"
        
        def obtener_color_anemia(clasificacion):
            colores = {
                "Normal": "🟢",
                "Leve": "🟡",
                "Moderada": "🟠",
                "Severa": "🔴",
                "Sin datos": "⚪"
            }
            return colores.get(clasificacion, "⚪")
        
        # Mostrar citas existentes
        if st.button("🔄 Cargar historial completo", key="cargar_historial"):
            with st.spinner("Cargando historial..."):
                citas_vinculadas = obtener_citas_con_info_anemia()
                st.session_state.citas_historial = citas_vinculadas
        
        if 'citas_historial' in st.session_state and st.session_state.citas_historial:
            citas_df = pd.DataFrame(st.session_state.citas_historial)
            citas_df['anemia_icono'] = citas_df['clasificacion_anemia'].apply(obtener_color_anemia)
            citas_df['anemia_mostrar'] = citas_df['anemia_icono'] + " " + citas_df['clasificacion_anemia']
            
            # Filtros
            col_filt1, col_filt2, col_filt3 = st.columns(3)
            
            with col_filt1:
                filtro_tipo = st.multiselect(
                    "Filtrar por tipo",
                    citas_df['tipo_consulta'].unique(),
                    default=citas_df['tipo_consulta'].unique()
                )
            
            with col_filt2:
                filtro_anemia = st.multiselect(
                    "Filtrar por anemia",
                    citas_df['clasificacion_anemia'].unique(),
                    default=citas_df['clasificacion_anemia'].unique()
                )
            
            with col_filt3:
                fecha_min = st.date_input("Desde", value=datetime.now() - timedelta(days=30))
                fecha_max = st.date_input("Hasta", value=datetime.now())
            
            # Aplicar filtros
            citas_filtradas = citas_df[
                (citas_df['tipo_consulta'].isin(filtro_tipo)) &
                (citas_df['clasificacion_anemia'].isin(filtro_anemia)) &
                (pd.to_datetime(citas_df['fecha_cita']).dt.date >= fecha_min) &
                (pd.to_datetime(citas_df['fecha_cita']).dt.date <= fecha_max)
            ]
            
            st.dataframe(
                citas_filtradas[['fecha_cita', 'hora_cita', 'nombre_paciente', 'dni_paciente',
                               'anemia_mostrar', 'hemoglobina', 'tipo_consulta', 'diagnostico', 'riesgo']],
                use_container_width=True,
                height=400,
                column_config={
                    "fecha_cita": "Fecha",
                    "hora_cita": "Hora",
                    "nombre_paciente": "Paciente",
                    "dni_paciente": "DNI",
                    "anemia_mostrar": st.column_config.TextColumn("Estado Anemia", width="small"),
                    "hemoglobina": st.column_config.NumberColumn("Hb (g/dL)", format="%.1f"),
                    "tipo_consulta": "Tipo Consulta",
                    "diagnostico": st.column_config.TextColumn("Diagnóstico", width="large"),
                    "riesgo": "Riesgo"
                }
            )
            
            # ESTADÍSTICAS DEL HISTORIAL - VERSIÓN CORREGIDA
            st.markdown('<div class="section-title-purple" style="font-size: 1.2rem;">📊 ESTADÍSTICAS DEL HISTORIAL</div>', unsafe_allow_html=True)
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                total_citas = len(citas_filtradas)
                st.metric("Total citas", total_citas)
            
            with col_stat2:
                # CORRECCIÓN: Cambiar "con_anaeia" por "con_anemia"
                con_anemia = len(citas_filtradas[citas_filtradas['clasificacion_anemia'].isin(["Leve", "Moderada", "Severa"])])
                st.metric("Con anemia", con_anemia)  # ← CORREGIDO
            
            with col_stat3:
                severas = len(citas_filtradas[citas_filtradas['clasificacion_anemia'] == "Severa"])
                st.metric("Anemia severa", severas)
            
            with col_stat4:
                ultima_cita = citas_filtradas['fecha_cita'].max() if not citas_filtradas.empty else "N/A"
                st.metric("Última cita", str(ultima_cita)[:10])
            
            # Exportar
            st.markdown("---")
            if st.button("📥 Exportar historial completo", use_container_width=True):
                csv = citas_df.to_csv(index=False)
                st.download_button(
                    label="📊 Descargar CSV",
                    data=csv,
                    file_name=f"historial_citas_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# ==================================================
# PESTAÑA 5: CONFIGURACIÓN
# ==================================================

with tab5:
    st.markdown('<div class="section-title-blue">⚙️ Configuración del Sistema</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">🛠️ Configuración de Tablas</div>', unsafe_allow_html=True)
    
    col_config1, col_config2 = st.columns(2)
    
    with col_config1:
        if st.button("📋 Configurar Tabla 'citas'", use_container_width=True, type="primary"):
            crear_tabla_citas_simple()
    
    with col_config2:
        if st.button("🔍 Verificar Conexión Supabase", use_container_width=True, type="secondary"):
            try:
                with st.spinner("Verificando conexión..."):
                    test = supabase.table("alertas_hemoglobina").select("*").limit(1).execute()
                    if test.data:
                        st.success("✅ Conexión a Supabase establecida correctamente")
                    else:
                        st.warning("⚠️ Conexión OK pero no hay datos")
            except Exception as e:
                st.error(f"❌ Error de conexión: {str(e)}")
    
    # Pruebas de guardado
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">🧪 Pruebas del Sistema</div>', unsafe_allow_html=True)
    probar_guardado_directo()
    
    # Información del sistema
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">📊 Información del Sistema</div>', unsafe_allow_html=True)
    
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        try:
            response = supabase.table("alertas_hemoglobina").select("*").execute()
            total_pacientes = len(response.data) if response.data else 0
            
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label">PACIENTES REGISTRADOS</div>
                <div class="highlight-number highlight-blue">{total_pacientes}</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
            <div class="metric-card-blue">
                <div class="metric-label">PACIENTES REGISTRADOS</div>
                <div class="highlight-number highlight-blue">0</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown(f"""
        <div class="metric-card-green">
            <div class="metric-label">VERSIÓN DEL SISTEMA</div>
            <div class="highlight-number highlight-green">2.0</div>
            <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
            Última actualización: {datetime.now().strftime('%d/%m/%Y')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==================================================
# SIDEBAR CON TÍTULOS MEJORADOS
# ==================================================

with st.sidebar:
    st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">📋 Sistema de Referencia</div>', unsafe_allow_html=True)
    
    tab_sidebar1, tab_sidebar2, tab_sidebar3 = st.tabs(["🎯 Ajustes Altitud", "📊 Crecimiento", "🔬 Hematología"])
    
    with tab_sidebar1:
        st.markdown('<div style="color: #1e40af; font-weight: 600; margin-bottom: 10px;">Tabla de Ajustes por Altitud</div>', unsafe_allow_html=True)
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
        st.markdown('<div style="color: #1e40af; font-weight: 600; margin-bottom: 10px;">Tablas de Crecimiento OMS</div>', unsafe_allow_html=True)
        referencia_df = obtener_referencia_crecimiento()
        if not referencia_df.empty:
            st.dataframe(referencia_df, use_container_width=True, height=300)
        else:
            st.info("Cargando tablas de referencia...")
    
    with tab_sidebar3:
        st.markdown('<div style="color: #1e40af; font-weight: 600; margin-bottom: 10px;">Criterios de Interpretación</div>', unsafe_allow_html=True)
        
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
        """)
    
    st.markdown("---")
    
    st.markdown('<div style="color: #1e40af; font-weight: 600; margin-bottom: 10px;">💡 Sistema Integrado</div>', unsafe_allow_html=True)
    st.markdown("""
    - ✅ Ajuste automático por altitud
    - ✅ Clasificación OMS de anemia
    - ✅ Seguimiento por gravedad
    - ✅ Dashboard nacional
    - ✅ Sistema de citas
    - ✅ Interpretación automática
    - ✅ Manejo de duplicados
    """)
    
    # Inicialización de datos de prueba
    if supabase:
        try:
            response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
            if not response.data:
                st.info("🔄 Base de datos vacía. Ingrese pacientes desde 'Registro Completo'")
                
                if st.button("➕ Insertar paciente de prueba", use_container_width=True):
                    with st.spinner("Insertando..."):
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
                            st.success("✅ Paciente de prueba insertado")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Error al insertar paciente de prueba")
        except Exception as e:
            st.warning(f"⚠️ Error verificando datos: {e}")

# ==================================================
# PIE DE PÁGINA CON ESTILO MEJORADO
# ==================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 10px;">
    <h4 style="color: #1e3a8a; margin: 0 0 10px 0;">🏥 SISTEMA NIXON</h4>
    <p style="color: #475569; margin: 5px 0;">Control de Anemia y Nutrición Infantil</p>
    <p style="color: #64748b; font-size: 0.9rem; margin: 5px 0;">Versión 2.0 | {}</p>
    <p style="color: #94a3b8; font-size: 0.8rem; margin-top: 15px;">
    ⚠️ <em>Para uso médico profesional. Consulte siempre con especialistas.</em>
    </p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y")), unsafe_allow_html=True)
