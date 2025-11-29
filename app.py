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
# FUNCIONES DE BASE DE DATOS MEJORADAS
# ==================================================

def obtener_datos_supabase(tabla=TABLE_NAME):
    try:
        if supabase:
            response = supabase.table(tabla).select("*").execute()
            if hasattr(response, 'error') and response.error:
                return pd.DataFrame()
            return pd.DataFrame(response.data) if response.data else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
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

def insertar_datos_supabase(datos, tabla=TABLE_NAME):
    try:
        if supabase:
            response = supabase.table(tabla).insert(datos).execute()
            if hasattr(response, 'error') and response.error:
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        return None

# ==================================================
# TABLAS DE REFERENCIA COMPLETAS
# ==================================================

# Obtener datos de altitud desde Supabase
def obtener_altitud_regiones():
    try:
        if supabase:
            response = supabase.table(ALTITUD_TABLE).select("*").execute()
            if response.data:
                return {row['region']: row for row in response.data}
        return {}
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
# FUNCIONES DE EVALUACIÓN NUTRICIONAL
# ==================================================

def obtener_referencia_crecimiento():
    """Obtiene la tabla de referencia de crecimiento desde Supabase"""
    try:
        if supabase:
            response = supabase.table(CRECIMIENTO_TABLE).select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def evaluar_estado_nutricional(edad_meses, peso_kg, talla_cm, genero):
    """Evalúa el estado nutricional basado en tablas de referencia OMS"""
    referencia_df = obtener_referencia_crecimiento()
    
    if referencia_df.empty:
        return "Sin datos referencia", "Sin datos referencia", "NUTRICIÓN NO EVALUADA", "RIESGO NO EVALUADO"
    
    # Encontrar referencia para la edad
    referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_meses]
    
    if referencia_edad.empty:
        return "Edad sin referencia", "Edad sin referencia", "NO EVALUABLE", "NO EVALUABLE"
    
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
    
    return estado_peso, estado_talla, estado_nutricional, "EVALUADO"

def calcular_riesgo_combinado(hemoglobina_ajustada, estado_nutricional, edad_meses):
    """Calcula riesgo combinado de anemia y estado nutricional"""
    
    # Umbrales de hemoglobina por edad
    if edad_meses < 12:
        umbral_anemia = 11.0
        umbral_severa = 9.5
    elif edad_meses < 60:
        umbral_anemia = 11.0
        umbral_severa = 9.5
    else:
        umbral_anemia = 11.5
        umbral_severa = 10.0
    
    # Puntaje por hemoglobina
    if hemoglobina_ajustada < umbral_severa:
        puntaje_hb = 30
    elif hemoglobina_ajustada < umbral_anemia:
        puntaje_hb = 20
    elif hemoglobina_ajustada < umbral_anemia + 1.0:
        puntaje_hb = 10
    else:
        puntaje_hb = 0
    
    # Puntaje por estado nutricional
    if estado_nutricional == "DESNUTRICIÓN CRÓNICA":
        puntaje_nut = 25
    elif estado_nutricional == "DESNUTRICIÓN AGUDA":
        puntaje_nut = 20
    elif estado_nutricional == "SOBREPESO":
        puntaje_nut = 5
    else:
        puntaje_nut = 0
    
    puntaje_total = puntaje_hb + puntaje_nut
    
    # Determinar riesgo combinado
    if puntaje_total >= 45:
        return "RIESGO MUY ALTO", puntaje_total
    elif puntaje_total >= 30:
        return "RIESGO ALTO", puntaje_total
    elif puntaje_total >= 15:
        return "RIESGO MODERADO", puntaje_total
    else:
        return "RIESGO BAJO", puntaje_total

def generar_sugerencias_combinadas(riesgo_combinado, estado_nutricional, hemoglobina_ajustada):
    """Genera sugerencias integradas para anemia y nutrición"""
    
    if riesgo_combinado == "RIESGO MUY ALTO":
        return (
            "🚨 INTERVENCIÓN URGENTE REQUERIDA:\n"
            "• Suplementación con hierro inmediata\n"
            "• Soporte nutricional intensivo\n"
            "• Evaluación médica URGENTE\n"
            "• Control semanal de hemoglobina\n"
            "• Referencia a especialista"
        )
    elif riesgo_combinado == "RIESGO ALTO":
        return (
            "⚠️ ACCIÓN PRIORITARIA:\n"
            "• Suplementación con hierro\n"
            "• Plan alimentario hipercalórico\n"
            "• Evaluación médica en 7 días\n"
            "• Control quincenal\n"
            "• Educación nutricional"
        )
    elif riesgo_combinado == "RIESGO MODERADO":
        return (
            "📋 SEGUIMIENTO RUTINARIO:\n"
            "• Suplementación preventiva\n"
            "• Educación en alimentación\n"
            "• Control mensual\n"
            "• Monitoreo de crecimiento"
        )
    else:
        return (
            "✅ MANTENIMIENTO:\n"
            "• Alimentación balanceada\n"
            "• Control trimestral\n"
            "• Prevención mediante dieta"
        )

# ==================================================
# LISTAS DE OPCIONES ACTUALIZADAS
# ==================================================

PERU_REGIONS = list(ALTITUD_REGIONES.keys()) if ALTITUD_REGIONES else ["LIMA", "AREQUIPA", "CUSCO", "PUNO", "JUNIN", "ANCASH", "LA LIBERTAD"]
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
# FUNCIONES DE CÁLCULO DE RIESGO ACTUALIZADAS
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
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

def generar_sugerencias(riesgo, hemoglobina_ajustada, edad_meses):
    if "ALTO" in riesgo and "ALTA" in riesgo:
        return "Suplemento de hierro y control mensual urgente"
    elif "ALTO" in riesgo:
        return "Dieta rica en hierro y evaluación médica prioritaria"
    elif "MODERADO" in riesgo:
        return "Seguimiento rutinario y refuerzo nutricional"
    else:
        return "Control preventivo y educación nutricional"

# ==================================================
# INTERFAZ PRINCIPAL ACTUALIZADA
# ==================================================

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia y Nutrición")
st.markdown("**Sistema integrado con ajuste por altitud y evaluación nutricional**")
st.markdown('</div>', unsafe_allow_html=True)

if supabase:
    st.success("🟢 CONECTADO A SUPABASE")
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE")

# PESTAÑAS ACTUALIZADAS CON NUEVAS FUNCIONALIDADES
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registro Completo", 
    "🔍 Casos en Seguimiento", 
    "📈 Estadísticas",
    "🍎 Evaluación Nutricional",
    "📊 Dashboard Nacional"
])

# PESTAÑA 1: REGISTRO COMPLETO (ACTUALIZADA)
with tab1:
    st.header("📝 Registro Completo de Paciente")
    
    with st.form("formulario_completo"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Datos Personales")
            dni = st.text_input("DNI*")
            nombre_completo = st.text_input("Nombre Completo*")
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
            peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1)
            talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1)
            genero = st.selectbox("Género*", GENEROS)
            telefono = st.text_input("Teléfono")
            estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE)
        
        with col2:
            st.subheader("🌍 Datos Geográficos")
            region = st.selectbox("Región*", PERU_REGIONS)
            departamento = st.text_input("Departamento/Distrito")
            
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
            
            st.metric(
                "Hemoglobina ajustada al nivel del mar",
                f"{hemoglobina_ajustada:.1f} g/dL",
                f"{ajuste_hb:+.1f} g/dL"
            )
            
            st.info(f"""
            **Cálculo:**
            - Hb medida: {hemoglobina_medida:.1f} g/dL
            - Ajuste por {altitud_msnm} msnm: {ajuste_hb:+.1f} g/dL  
            - **Hb ajustada: {hemoglobina_ajustada:.1f} g/dL**
            """)
            
            en_seguimiento = st.checkbox("Marcar para seguimiento activo", value=True)
            consume_hierro = st.checkbox("Consume suplemento de hierro")
            tipo_suplemento_hierro = st.text_input("Tipo de suplemento de hierro")
            frecuencia_suplemento = st.selectbox("Frecuencia de suplemento", FRECUENCIAS_SUPLEMENTO)
            antecedentes_anemia = st.checkbox("Antecedentes de anemia")
            enfermedades_cronicas = st.text_area("Enfermedades crónicas")
        
        with col4:
            st.subheader("📋 Factores de Riesgo")
            st.subheader("🏥 Factores Clínicos")
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS)
            
            st.subheader("💰 Factores Socioeconómicos")
            factores_sociales = st.multiselect("Seleccione factores sociales:", FACTORES_SOCIOECONOMICOS)
        
        submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GUARDAR", type="primary")
    
    if submitted:
        if not dni or not nombre_completo:
            st.error("❌ Complete DNI y nombre del paciente")
        else:
            # EVALUACIÓN NUTRICIONAL
            estado_peso, estado_talla, estado_nutricional, _ = evaluar_estado_nutricional(
                edad_meses, peso_kg, talla_cm, genero
            )
            
            # CALCULAR RIESGO COMBINADO
            riesgo_combinado, puntaje_combinado = calcular_riesgo_combinado(
                hemoglobina_ajustada, estado_nutricional, edad_meses
            )
            
            # GENERAR SUGERENCIAS COMBINADAS
            sugerencias_combinadas = generar_sugerencias_combinadas(
                riesgo_combinado, estado_nutricional, hemoglobina_ajustada
            )
            
            # Mostrar resultados
            st.markdown("---")
            st.subheader("📊 EVALUACIÓN INTEGRAL DEL PACIENTE")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🩺 Estado de Anemia")
                nivel_riesgo_anemia, puntaje_anemia, estado_alerta = calcular_riesgo_anemia(
                    hemoglobina_ajustada, edad_meses, factores_clinicos, factores_sociales
                )
                
                if "ALTO" in nivel_riesgo_anemia and "ALTA" in nivel_riesgo_anemia:
                    st.markdown('<div class="risk-high">', unsafe_allow_html=True)
                elif "ALTO" in nivel_riesgo_anemia:
                    st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-low">', unsafe_allow_html=True)
                
                st.markdown(f"**RIESGO ANEMIA:** {nivel_riesgo_anemia}")
                st.markdown(f"**Puntaje:** {puntaje_anemia}/60 puntos")
                st.markdown(f"**Alerta:** {estado_alerta}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🍎 Estado Nutricional")
                st.markdown(f"**Peso:** {estado_peso}")
                st.markdown(f"**Talla:** {estado_talla}")
                st.markdown(f"**Estado Nutricional:** {estado_nutricional}")
                st.markdown(f"**Riesgo Combinado:** {riesgo_combinado}")
                st.markdown(f"**Puntaje Combinado:** {puntaje_combinado}")
            
            # SUGERENCIAS INTEGRADAS
            st.markdown("### 💡 Plan de Acción Integrado")
            st.info(sugerencias_combinadas)
            
            # Guardar en Supabase
            if supabase:
                record = {
                    "dni": dni,
                    "nombre_apellido": nombre_completo,
                    "edad_meses": int(edad_meses),
                    "peso_kg": float(peso_kg),
                    "talla_cm": float(talla_cm),
                    "genero": genero,
                    "telefono": telefono,
                    "estado_paciente": estado_paciente,
                    "region": region,
                    "departamento": departamento,
                    "altitud_msnm": int(altitud_msnm),
                    "nivel_educativo": nivel_educativo,
                    "acceso_agua_potable": acceso_agua_potable,
                    "tiene_servicio_salud": tiene_servicio_salud,
                    "hemoglobina_dl1": float(hemoglobina_medida),
                    "en_seguimiento": en_seguimiento,
                    "consume_hierro": consume_hierro,
                    "tipo_suplemento_hierro": tipo_suplemento_hierro,
                    "frecuencia_suplemento": frecuencia_suplemento,
                    "antecedentes_anemia": antecedentes_anemia,
                    "enfermedades_cronicas": enfermedades_cronicas,
                    "riesgo": nivel_riesgo_anemia,
                    "estado_alerta": estado_alerta,
                    "sugerencias": sugerencias_combinadas,
                    "fecha_alerta": datetime.now().isoformat()
                }
                
                resultado = insertar_datos_supabase(record)
                if resultado:
                    st.success("✅ Datos guardados en Supabase correctamente")
                else:
                    st.error("❌ Error al guardar en Supabase")

# PESTAÑA 2: CASOS EN SEGUIMIENTO (MANTENIDA)
with tab2:
    st.header("🔍 Casos en Seguimiento Activo")
    
    if st.button("🔄 Actualizar lista de seguimiento"):
        with st.spinner("Cargando casos en seguimiento..."):
            casos_seguimiento = obtener_casos_seguimiento()
        
        if not casos_seguimiento.empty:
            st.success(f"✅ {len(casos_seguimiento)} casos en seguimiento encontrados")
            
            columnas_mostrar = ['nombre_apellido', 'edad_meses', 'hemoglobina_dl1', 'riesgo', 'region', 'fecha_alerta']
            columnas_disponibles = [col for col in columnas_mostrar if col in casos_seguimiento.columns]
            
            if columnas_disponibles:
                st.dataframe(
                    casos_seguimiento[columnas_disponibles],
                    use_container_width=True,
                    height=400
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total en seguimiento", len(casos_seguimiento))
                with col2:
                    alto_riesgo = len(casos_seguimiento[casos_seguimiento['riesgo'].str.contains('ALTO', na=False)])
                    st.metric("Alto riesgo", alto_riesgo)
                with col3:
                    if 'hemoglobina_dl1' in casos_seguimiento.columns:
                        avg_hemoglobina = casos_seguimiento['hemoglobina_dl1'].mean()
                        st.metric("Hb promedio", f"{avg_hemoglobina:.1f} g/dL")
        else:
            st.info("📝 No hay casos en seguimiento actualmente")

# PESTAÑA 3: ESTADÍSTICAS (MANTENIDA)
with tab3:
    st.header("📈 Estadísticas del Sistema")
    
    if st.button("📊 Cargar estadísticas actuales"):
        with st.spinner("Calculando estadísticas..."):
            datos_completos = obtener_datos_supabase()
        
        if not datos_completos.empty:
            st.success(f"✅ {len(datos_completos)} registros analizados")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_casos = len(datos_completos)
                st.metric("Total de casos", total_casos)
            
            with col2:
                en_seguimiento = len(datos_completos[datos_completos['en_seguimiento'] == True])
                st.metric("En seguimiento", en_seguimiento)
            
            with col3:
                if 'hemoglobina_dl1' in datos_completos.columns:
                    avg_hemoglobina = datos_completos['hemoglobina_dl1'].mean()
                    st.metric("Hb promedio", f"{avg_hemoglobina:.1f} g/dL")
            
            with col4:
                if 'riesgo' in datos_completos.columns:
                    alto_riesgo = len(datos_completos[datos_completos['riesgo'].str.contains('ALTO', na=False)])
                    st.metric("Casos alto riesgo", alto_riesgo)
            
            st.subheader("📋 Distribución por Región")
            if 'region' in datos_completos.columns:
                distribucion_region = datos_completos['region'].value_counts()
                st.bar_chart(distribucion_region)
            
            st.subheader("📄 Datos Completos")
            st.dataframe(datos_completos, use_container_width=True, height=300)
            
        else:
            st.info("📝 No hay datos disponibles para mostrar estadísticas")

# PESTAÑA 4: EVALUACIÓN NUTRICIONAL (NUEVA)
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
        estado_peso, estado_talla, estado_nutricional, _ = evaluar_estado_nutricional(
            edad_eval, peso_eval, talla_eval, genero_eval
        )
        
        # Riesgo combinado
        riesgo_combinado, puntaje_combinado = calcular_riesgo_combinado(
            hb_ajustada_eval, estado_nutricional, edad_eval
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
        
        with col2:
            st.markdown("### 🍎 Parámetros Nutricionales")
            st.metric("Estado de Peso", estado_peso)
            st.metric("Estado de Talla", estado_talla)
            st.metric("Estado Nutricional", estado_nutricional)
            st.metric("Riesgo Combinado", riesgo_combinado)
        
        # Tabla de referencia
        st.subheader("📊 Tablas de Referencia OMS")
        referencia_df = obtener_referencia_crecimiento()
        if not referencia_df.empty:
            st.dataframe(referencia_df, use_container_width=True, height=300)
        else:
            st.info("No se pudieron cargar las tablas de referencia")

# PESTAÑA 5: DASHBOARD NACIONAL (NUEVA)
with tab5:
    st.header("📊 Dashboard Nacional de Anemia y Nutrición")
    
    if st.button("🔄 Actualizar Dashboard Nacional"):
        with st.spinner("Cargando datos nacionales..."):
            datos_nacionales = obtener_datos_supabase()
            datos_altitud = obtener_datos_supabase(ALTITUD_TABLE)
        
        if not datos_nacionales.empty:
            st.success(f"✅ Dashboard actualizado con {len(datos_nacionales)} registros")
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_pacientes = len(datos_nacionales)
                st.metric("Total Pacientes", total_pacientes)
            
            with col2:
                alto_riesgo = len(datos_nacionales[datos_nacionales['riesgo'].str.contains('ALTO', na=False)])
                st.metric("Alto Riesgo", alto_riesgo)
            
            with col3:
                avg_hemoglobina = datos_nacionales['hemoglobina_dl1'].mean()
                st.metric("Hemoglobina Promedio", f"{avg_hemoglobina:.1f} g/dL")
            
            with col4:
                regiones_activas = datos_nacionales['region'].nunique()
                st.metric("Regiones Activas", regiones_activas)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribución por riesgo
                fig_riesgo = px.pie(
                    datos_nacionales, 
                    names='riesgo',
                    title='Distribución por Nivel de Riesgo',
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                st.plotly_chart(fig_riesgo, use_container_width=True)
            
            with col2:
                # Hemoglobina por región
                fig_hemo = px.box(
                    datos_nacionales,
                    x='region',
                    y='hemoglobina_dl1',
                    title='Hemoglobina por Región'
                )
                st.plotly_chart(fig_hemo, use_container_width=True)
            
            # Mapa de regiones
            st.subheader("🗺️ Mapa de Distribución por Región")
            if not datos_altitud.empty:
                # Crear datos para el mapa
                mapa_data = datos_nacionales.groupby('region').agg({
                    'hemoglobina_dl1': 'mean',
                    'dni': 'count'
                }).rename(columns={'dni': 'pacientes'}).reset_index()
                
                # Unir con datos de altitud
                mapa_data = mapa_data.merge(
                    datos_altitud[['region', 'altitud_promedio']], 
                    on='region', 
                    how='left'
                )
                
                st.dataframe(mapa_data, use_container_width=True)
            
        else:
            st.info("📝 No hay datos suficientes para el dashboard nacional")

# SIDEBAR ACTUALIZADO
with st.sidebar:
    st.header("📋 Sistema de Referencia")
    
    tab_sidebar1, tab_sidebar2 = st.tabs(["🎯 Ajustes Altitud", "📊 Tablas Crecimiento"])
    
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
    
    st.markdown("---")
    st.info("""
    **💡 Sistema Integrado:**
    - ✅ Ajuste automático por altitud
    - ✅ Evaluación nutricional OMS
    - ✅ Riesgo combinado anemia-nutrición
    - ✅ Dashboard nacional
    - ✅ Seguimiento activo
    """)

# ==================================================
# INICIALIZACIÓN DE DATOS DE PRUEBA
# ==================================================

if supabase:
    try:
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        if not response.data:
            st.info("🔄 Inicializando base de datos con datos de prueba...")
            
            datos_prueba = [
                {
                    "dni": "12345678",
                    "nombre_apellido": "Ana García Pérez",
                    "edad_meses": 24,
                    "peso_kg": 12.5,
                    "talla_cm": 85.0,
                    "genero": "F",
                    "telefono": "987654321",
                    "estado_paciente": "Activo",
                    "region": "LIMA",
                    "departamento": "Lima Metropolitana",
                    "altitud_msnm": 150,
                    "nivel_educativo": "Secundaria",
                    "acceso_agua_potable": True,
                    "tiene_servicio_salud": True,
                    "hemoglobina_dl1": 9.5,
                    "en_seguimiento": True,
                    "consume_hierro": True,
                    "tipo_suplemento_hierro": "Sulfato ferroso",
                    "frecuencia_suplemento": "Diario",
                    "antecedentes_anemia": True,
                    "enfermedades_cronicas": "Ninguna",
                    "riesgo": "ALTO RIESGO (Alerta Clínica - ALTA)",
                    "estado_alerta": "URGENTE",
                    "sugerencias": "Suplemento de hierro y control mensual"
                }
            ]
            
            for dato in datos_prueba:
                supabase.table(TABLE_NAME).insert(dato).execute()
            
            st.success("✅ Base de datos inicializada con paciente de prueba")
            time.sleep(2)
            st.rerun()
    except Exception as e:
        st.warning(f"⚠️ Error verificando datos: {e}")
