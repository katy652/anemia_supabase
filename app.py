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
</style>
""", unsafe_allow_html=True)

# ==================================================
# CONFIGURACIÓN SUPABASE
# ==================================================

TABLE_NAME = "alertas_hemoglobina"
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
# TABLA DE ALTITUD Y AJUSTES DE HEMOGLOBINA
# ==================================================

ALTITUD_REGIONES = {
    "AMAZONAS": {"altitud_min": 500, "altitud_max": 3500, "altitud_promedio": 2000},
    "ANCASH": {"altitud_min": 2000, "altitud_max": 4000, "altitud_promedio": 3000},
    "APURIMAC": {"altitud_min": 2500, "altitud_max": 4500, "altitud_promedio": 3500},
    "AREQUIPA": {"altitud_min": 2000, "altitud_max": 3500, "altitud_promedio": 2500},
    "AYACUCHO": {"altitud_min": 2500, "altitud_max": 4000, "altitud_promedio": 3200},
    "CAJAMARCA": {"altitud_min": 1500, "altitud_max": 3500, "altitud_promedio": 2500},
    "CALLAO": {"altitud_min": 0, "altitud_max": 100, "altitud_promedio": 50},
    "CUSCO": {"altitud_min": 3000, "altitud_max": 4500, "altitud_promedio": 3400},
    "HUANCAVELICA": {"altitud_min": 3000, "altitud_max": 4500, "altitud_promedio": 3700},
    "HUANUCO": {"altitud_min": 1000, "altitud_max": 3500, "altitud_promedio": 2000},
    "ICA": {"altitud_min": 0, "altitud_max": 1500, "altitud_promedio": 500},
    "JUNIN": {"altitud_min": 3000, "altitud_max": 4200, "altitud_promedio": 3500},
    "LA LIBERTAD": {"altitud_min": 0, "altitud_max": 3500, "altitud_promedio": 1800},
    "LAMBAYEQUE": {"altitud_min": 0, "altitud_max": 2000, "altitud_promedio": 500},
    "LIMA": {"altitud_min": 0, "altitud_max": 500, "altitud_promedio": 150},
    "LORETO": {"altitud_min": 50, "altitud_max": 300, "altitud_promedio": 150},
    "MADRE DE DIOS": {"altitud_min": 100, "altitud_max": 500, "altitud_promedio": 250},
    "MOQUEGUA": {"altitud_min": 1000, "altitud_max": 3500, "altitud_promedio": 2000},
    "PASCO": {"altitud_min": 2500, "altitud_max": 4000, "altitud_promedio": 3200},
    "PIURA": {"altitud_min": 0, "altitud_max": 2500, "altitud_promedio": 1000},
    "PUNO": {"altitud_min": 3800, "altitud_max": 4500, "altitud_promedio": 4100},
    "SAN MARTIN": {"altitud_min": 200, "altitud_max": 2000, "altitud_promedio": 800},
    "TACNA": {"altitud_min": 500, "altitud_max": 3000, "altitud_promedio": 1500},
    "TUMBES": {"altitud_min": 0, "altitud_max": 200, "altitud_promedio": 50},
    "UCAYALI": {"altitud_min": 100, "altitud_max": 400, "altitud_promedio": 200}
}

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
# FUNCIONES DE BASE DE DATOS
# ==================================================

def obtener_datos_supabase():
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").execute()
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

def insertar_datos_supabase(datos):
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).insert(datos).execute()
            if hasattr(response, 'error') and response.error:
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        return None

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
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

# ==================================================
# CREAR DATOS DE PRUEBA SI LA TABLA ESTÁ VACÍA
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
                    "region": "LIMA", 
                    "altitud_msnm": 150,
                    "hemoglobina_medida": 9.5,
                    "hemoglobina_ajustada": 9.5,
                    "ajuste_altitud": 0.0,
                    "mch": 28.0,
                    "mchc": 33.0,
                    "mcv": 90.0,
                    "en_seguimiento": True,
                    "consume_hierro": True,
                    "factores_clinicos": "Historial familiar de anemia",
                    "factores_sociales": "Bajo nivel educativo de padres",
                    "riesgo": "ALTO RIESGO (Alerta Clínica - ALTA)",
                    "puntaje_riesgo": 35,
                    "estado_alerta": "URGENTE",
                    "fecha_alerta": datetime.now().isoformat()
                },
                {
                    "dni": "87654321", 
                    "nombre_apellido": "Luis Martínez",
                    "edad_meses": 18,
                    "peso_kg": 11.2,
                    "talla_cm": 78.0,
                    "genero": "M",
                    "region": "CUSCO",
                    "altitud_msnm": 3400,
                    "hemoglobina_medida": 10.8,
                    "hemoglobina_ajustada": 8.9,
                    "ajuste_altitud": -1.9,
                    "mch": 26.0,
                    "mchc": 32.0,
                    "mcv": 85.0,
                    "en_seguimiento": True,
                    "consume_hierro": False,
                    "factores_clinicos": "Infecciones recurrentes",
                    "factores_sociales": "Zona rural o alejada, Acceso limitado a agua potable",
                    "riesgo": "ALTO RIESGO (Alerta Clínica - MODERADA)",
                    "puntaje_riesgo": 28,
                    "estado_alerta": "PRIORITARIO",
                    "fecha_alerta": datetime.now().isoformat()
                },
                {
                    "dni": "45678912",
                    "nombre_apellido": "María López",
                    "edad_meses": 36,
                    "peso_kg": 14.0,
                    "talla_cm": 95.0,
                    "genero": "F",
                    "region": "AREQUIPA",
                    "altitud_msnm": 2500,
                    "hemoglobina_medida": 11.5,
                    "hemoglobina_ajustada": 10.2,
                    "ajuste_altitud": -1.3,
                    "mch": 29.0,
                    "mchc": 34.0,
                    "mcv": 92.0,
                    "en_seguimiento": False,
                    "consume_hierro": True,
                    "factores_clinicos": "",
                    "factores_sociales": "",
                    "riesgo": "RIESGO MODERADO",
                    "puntaje_riesgo": 12,
                    "estado_alerta": "EN SEGUIMIENTO",
                    "fecha_alerta": datetime.now().isoformat()
                }
            ]
            
            for dato in datos_prueba:
                supabase.table(TABLE_NAME).insert(dato).execute()
            
            st.success("✅ Base de datos inicializada con 3 pacientes de prueba")
            time.sleep(2)
            st.rerun()
    except Exception as e:
        st.warning(f"⚠️ Error verificando datos: {e}")

# ==================================================
# INTERFAZ PRINCIPAL
# ==================================================

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia")
st.markdown("**Sistema integrado con ajuste por altitud**")
st.markdown('</div>', unsafe_allow_html=True)

if supabase:
    st.success("🟢 CONECTADO A SUPABASE")
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE")

tab1, tab2, tab3 = st.tabs(["📝 Registro Completo", "🔍 Casos en Seguimiento", "📈 Estadísticas"])

# PESTAÑA 1: REGISTRO COMPLETO
with tab1:
    st.header("📝 Registro Completo de Paciente")
    
    with st.form("formulario_completo"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Datos Personales")
            dni = st.text_input("DNI*")
            nombre_completo = st.text_input("Nombre Completo*")
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
            peso_kg = st.number_input("Peso (kg)", 0.0, 50.0, 12.5, 0.1)
            talla_cm = st.number_input("Talla (cm)", 0.0, 150.0, 85.0, 0.1)
            genero = st.selectbox("Género*", GENEROS)
        
        with col2:
            st.subheader("🌍 Datos Geográficos")
            region = st.selectbox("Región*", PERU_REGIONS)
            
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
            
            ajuste_hb = obtener_ajuste_hemoglobina(altitud_msnm)
            st.markdown(f"""
            <div class="climate-card">
                <h4>📊 Ajuste por Altitud</h4>
                <p><strong>Corrección: {ajuste_hb:+.1f} g/dL</strong></p>
                <p>Hb se ajusta automáticamente</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("🩺 Parámetros Hematológicos")
            hemoglobina_medida = st.number_input("Hemoglobina medida (g/dL)*", 5.0, 20.0, 11.0, 0.1)
            
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
            
            mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1)
            mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1)
            mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1)
        
        with col4:
            st.subheader("📋 Estado y Factores")
            en_seguimiento = st.checkbox("Marcar para seguimiento activo", value=True)
            consume_hierro = st.checkbox("Consume suplemento de hierro")
            
            st.subheader("🏥 Factores Clínicos")
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS)
            
            st.subheader("💰 Factores Socioeconómicos")
            factores_sociales = st.multiselect("Seleccione factores sociales:", FACTORES_SOCIOECONOMICOS)
        
        submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GUARDAR", type="primary")
    
    if submitted:
        if not dni or not nombre_completo:
            st.error("❌ Complete DNI y nombre del paciente")
        else:
            nivel_riesgo, puntaje, estado = calcular_riesgo_anemia(
                hemoglobina_ajustada,
                edad_meses,
                factores_clinicos,
                factores_sociales
            )
            
            if "ALTO" in nivel_riesgo and "ALTA" in nivel_riesgo:
                st.markdown('<div class="risk-high">', unsafe_allow_html=True)
            elif "ALTO" in nivel_riesgo:
                st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
            else:
                st.markdown('<div class="risk-low">', unsafe_allow_html=True)
            
            st.markdown(f"### **RIESGO: {nivel_riesgo}**")
            st.markdown(f"**Puntaje:** {puntaje}/60 puntos | **Estado:** {estado}")
            st.markdown(f"**Hemoglobina:** {hemoglobina_medida:.1f} g/dL (medida) → **{hemoglobina_ajustada:.1f} g/dL** (ajustada)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if supabase:
                record = {
                    "dni": dni,
                    "nombre_apellido": nombre_completo,
                    "edad_meses": int(edad_meses),
                    "peso_kg": float(peso_kg),
                    "talla_cm": float(talla_cm),
                    "genero": genero,
                    "region": region,
                    "altitud_msnm": int(altitud_msnm),
                    "hemoglobina_medida": float(hemoglobina_medida),
                    "hemoglobina_ajustada": float(hemoglobina_ajustada),
                    "ajuste_altitud": float(ajuste_hb),
                    "mch": float(mch),
                    "mchc": float(mchc),
                    "mcv": float(mcv),
                    "en_seguimiento": en_seguimiento,
                    "consume_hierro": consume_hierro,
                    "factores_clinicos": ", ".join(factores_clinicos),
                    "factores_sociales": ", ".join(factores_sociales),
                    "riesgo": nivel_riesgo,
                    "puntaje_riesgo": int(puntaje),
                    "estado_alerta": estado,
                    "fecha_alerta": datetime.now().isoformat()
                }
                
                resultado = insertar_datos_supabase(record)
                if resultado:
                    st.success("✅ Datos guardados en Supabase correctamente")
                else:
                    st.error("❌ Error al guardar en Supabase")

# PESTAÑA 2: CASOS EN SEGUIMIENTO
with tab2:
    st.header("🔍 Casos en Seguimiento Activo")
    
    if st.button("🔄 Actualizar lista de seguimiento"):
        with st.spinner("Cargando casos en seguimiento..."):
            casos_seguimiento = obtener_casos_seguimiento()
        
        if not casos_seguimiento.empty:
            st.success(f"✅ {len(casos_seguimiento)} casos en seguimiento encontrados")
            
            columnas_mostrar = ['nombre_apellido', 'edad_meses', 'hemoglobina_ajustada', 'riesgo', 'region', 'fecha_alerta']
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
                    avg_hemoglobina = casos_seguimiento['hemoglobina_ajustada'].mean()
                    st.metric("Hb promedio", f"{avg_hemoglobina:.1f} g/dL")
        else:
            st.info("📝 No hay casos en seguimiento actualmente")

# PESTAÑA 3: ESTADÍSTICAS
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
                avg_hemoglobina = datos_completos['hemoglobina_ajustada'].mean()
                st.metric("Hb promedio ajustada", f"{avg_hemoglobina:.1f} g/dL")
            
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

# SIDEBAR CON TABLA DE AJUSTES
with st.sidebar:
    st.header("📋 Tabla de Ajustes por Altitud")
    st.markdown("**Ajuste de hemoglobina:**")
    
    ajustes_df = pd.DataFrame(AJUSTE_HEMOGLOBINA)
    st.dataframe(
        ajustes_df.style.format({
            'altitud_min': '{:.0f}',
            'altitud_max': '{:.0f}', 
            'ajuste': '{:+.1f}'
        }),
        use_container_width=True,
        height=400
    )
    
    st.markdown("---")
    st.info("""
    **💡 Información:**
    - La hemoglobina se ajusta automáticamente
    - Se usa la altitud promedio de cada región
    - Los cálculos son según estándares OMS
    """)
