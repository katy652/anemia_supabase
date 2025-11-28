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
    .stApp { background-color: #f0f2f6; font-family: 'Arial', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;
    }
    .dashboard-card {
        background: white; padding: 1.5rem; border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .risk-high { background-color: #ffebee; border-left: 5px solid #f44336; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .risk-moderate { background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .risk-low { background-color: #e8f5e8; border-left: 5px solid #4caf50; padding: 1rem; border-radius: 5px; margin: 1rem 0; }
    .factor-card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem; border-left: 4px solid #667eea; }
    .metric-card { background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
    .climate-card { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN SUPABASE ---
TABLE_NAME = "alertas_hemoglobina"
SUPABASE_URL = "https://kwsuszkblbejvliniggd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw"

# --- CLIMA POR REGIÓN ---
CLIMA_POR_REGION = {
    "LIMA": {"clima": "Desértico subtropical", "temp_promedio": "21°C", "humedad": "85%", "precipitacion": "10 mm"},
    "AREQUIPA": {"clima": "Semiárido", "temp_promedio": "18°C", "humedad": "45%", "precipitacion": "100 mm"},
    "CUSCO": {"clima": "Templado subhúmedo", "temp_promedio": "14°C", "humedad": "65%", "precipitacion": "700 mm"},
    # ... (el resto de tus regiones)
    "NO ESPECIFICADO": {"clima": "No especificado", "temp_promedio": "N/A", "humedad": "N/A", "precipitacion": "N/A"}
}

# --- LISTAS DE OPCIONES ---
PERU_REGIONS = ["NO ESPECIFICADO", "LIMA", "AREQUIPA", "CUSCO", "PUNO", "ICA", "LORETO", "LA LIBERTAD", "ANCASH", "JUNÍN", "PIURA", "LAMBAYEQUE"]
ESTADOS_PACIENTE = ["EN SEGUIMIENTO", "PENDIENTE EVALUACIÓN", "CON TRATAMIENTO ACTIVO", "ALTA MÉDICA", "ABANDONO TRATAMIENTO", "REFERIDO ESPECIALISTA"]
FACTORES_CLINICOS = ["Historial familiar de anemia", "Embarazo múltiple", "Intervalos intergenésicos cortos", "Enfermedades crónicas", "Medicamentos que afectan absorción"]
FACTORES_SOCIOECONOMICOS = ["Bajo nivel educativo de padres", "Ingresos familiares reducidos", "Hacinamiento en vivienda", "Acceso limitado a agua potable"]
ACCESO_SERVICIOS = ["Control prenatal irregular", "Limitado acceso a suplementos", "Barreras geográficas a centros de salud", "Falta de información nutricional"]

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_supabase():
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        st.success("✅ Conexión a Supabase establecida")
        return supabase_client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {e}")
        return None

# --- FUNCIONES SUPABASE CORREGIDAS ---
def obtener_datos_supabase():
    try:
        if supabase:
            response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).execute()
            if response.data:
                return pd.DataFrame(response.data)
            else:
                return pd.DataFrame()
    except Exception as e:
        st.error(f"Error obteniendo datos: {e}")
    return pd.DataFrame()

def insertar_datos_supabase(datos):
    try:
        if not supabase:
            st.warning("⚠️ No hay conexión a Supabase")
            return None
            
        datos_limpios = {
            "dni": datos.get("dni", ""),
            "nombre_apellido": datos.get("nombre_completo", ""),
            "edad_meses": datos.get("edad_meses", 0),
            "hemoglobina": datos.get("hemoglobina_g_dL", 0.0),  # CORREGIDO: "hemoglobina"
            "riesgo": datos.get("riesgo", ""),
            "fecha_alerta": datos.get("fecha_alerta", datetime.now().isoformat()),
            "estado": datos.get("estado_recomendado", ""),
            "sugerencias": datos.get("sugerencias_texto", ""),
            "region": datos.get("region", "NO ESPECIFICADO")
        }
        
        response = supabase.table(TABLE_NAME).insert(datos_limpios).execute()
        
        if hasattr(response, 'error') and response.error:
            st.error(f"❌ Error insertando: {response.error}")
            return None
            
        st.success("✅ Datos guardados en Supabase!")
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

def obtener_estadisticas_tiempo_real():
    try:
        if supabase:
            fecha_limite = (datetime.now() - timedelta(days=30)).isoformat()
            response = supabase.table(TABLE_NAME).select("*").gte("fecha_alerta", fecha_limite).execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                total_casos = len(df)
                alto_riesgo = len(df[df['riesgo'].str.contains('ALTO', na=False)]) if 'riesgo' in df.columns else 0
                moderado_riesgo = len(df[df['riesgo'].str.contains('MODERADO', na=False)]) if 'riesgo' in df.columns else 0
                
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
    return CLIMA_POR_REGION.get(region.upper(), CLIMA_POR_REGION["NO ESPECIFICADO"])

# --- FUNCIONES DE ANÁLISIS ---
def calcular_riesgo_anemia(hb, edad_meses, factores_clinicos, factores_sociales, acceso_servicios, clima_region):
    puntaje = 0
    
    if edad_meses < 12:
        if hb < 9.0: puntaje += 30
        elif hb < 10.0: puntaje += 20
        elif hb < 11.0: puntaje += 10
    elif edad_meses < 60:
        if hb < 9.5: puntaje += 30
        elif hb < 10.5: puntaje += 20
        elif hb < 11.5: puntaje += 10
    else:
        if hb < 10.0: puntaje += 30
        elif hb < 11.0: puntaje += 20
        elif hb < 12.0: puntaje += 10
    
    puntaje += len(factores_clinicos) * 4
    puntaje += len(factores_sociales) * 3
    puntaje += len(acceso_servicios) * 2
    
    if "tropical" in clima_region.lower() or "húmedo" in clima_region.lower():
        puntaje += 5
    
    if puntaje >= 35:
        return "ALTO RIESGO (Alerta Clínica - ALTA)", puntaje, "URGENTE"
    elif puntaje >= 25:
        return "ALTO RIESGO (Alerta Clínica - MODERADA)", puntaje, "PRIORITARIO"
    elif puntaje >= 15:
        return "RIESGO MODERADO", puntaje, "EN SEGUIMIENTO"
    else:
        return "BAJO RIESGO", puntaje, "VIGILANCIA"

def generar_sugerencias(riesgo, puntaje, factores_clinicos, factores_sociales, acceso_servicios, hemoglobina, edad_meses, clima):
    sugerencias = []
    
    if "ALTO" in riesgo and "ALTA" in riesgo:
        sugerencias.append("🔴 **CONSULTA MÉDICA INMEDIATA** - Requiere atención dentro de 24-48 horas")
        sugerencias.append("💊 **SUPLEMENTACIÓN URGENTE** - Sulfato ferroso 3-6 mg/kg/día + ácido fólico")
    elif "ALTO" in riesgo:
        sugerencias.append("🟠 **CONSULTA PRIORITARIA** - Programar dentro de 3-5 días")
        sugerencias.append("💊 **SUPLEMENTACIÓN NUTRICIONAL** - Hierro elemental 2-3 mg/kg/día")
    else:
        sugerencias.append("🟡 **CONTROL PROGRAMADO** - Seguimiento en 7-10 días")
        sugerencias.append("🥩 **REFUERZO DIETÉTICO** - Alimentos ricos en hierro hemínico y vitamina C")
    
    if any("infecc" in factor.lower() for factor in factores_clinicos):
        sugerencias.append("🦠 **MANEJO INFECCIOSO** - Evaluar y tratar procesos infecciosos")
    
    if any("parasit" in factor.lower() for factor in factores_clinicos):
        sugerencias.append("🐛 **DESPARASITACIÓN** - Administrar antiparasitarios según protocolo")
    
    if factores_sociales:
        sugerencias.append("🏠 **INTERVENCIÓN SOCIAL** - Derivación a trabajo social")
    
    if any("barrera" in factor.lower() for factor in acceso_servicios):
        sugerencias.append("📍 **FACILITAR ACCESO** - Coordinar consultas móviles o transporte subsidiado")
    
    if "tropical" in clima.lower():
        sugerencias.append("🌧️ **VIGILANCIA CLIMÁTICA** - Mayor riesgo de enfermedades parasitarias")
    
    if edad_meses < 24:
        sugerencias.append("🍼 **LACTANCIA Y ALIMENTACIÓN** - Promover lactancia materna")
    else:
        sugerencias.append("🍖 **DIETA ESPECÍFICA** - Carnes rojas, hígado, legumbres, vegetales verdes")
    
    if "ALTO" in riesgo:
        sugerencias.append("📊 **MONITOREO ESTRECHO** - Control semanal hasta mejoría")
    else:
        sugerencias.append("📊 **SEGUIMIENTO** - Control cada 15 días hasta normalización")
    
    return sugerencias

# --- INICIALIZAR CONEXIONES ---
supabase = init_supabase()

# --- INTERFAZ PRINCIPAL ---
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia")
st.markdown("**Predicts/day reports • Monitoring de Alertas • Panel de control estadístico**")
st.markdown('</div>', unsafe_allow_html=True)

if supabase:
    st.success("🟢 CONECTADO A SUPABASE - Sistema operativo")
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE - Modo demostración")

# --- DASHBOARD ---
st.header("📊 Dashboard Nixon - Métricas en Tiempo Real")
stats = obtener_estadisticas_tiempo_real()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Predicts/Day Reports", f"{stats['casos_por_dia']:.1f}", stats['tendencia'])
with col2:
    st.metric("Total Predictions Week", stats['total_semana'])
with col3:
    st.metric("Monitoring de Alertas", stats['alto_riesgo'], f"{stats['tasa_alto_riesgo']:.1f}%")
with col4:
    st.metric("Panel Control Estadístico", stats['total_casos'], f"+{stats['moderado_riesgo']} moderados")

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
        
        if region != "NO ESPECIFICADO":
            clima_info = obtener_clima_region(region)
            st.markdown(f"""
            <div class="climate-card">
                <h4>🌤️ Clima {region}</h4>
                <p><strong>{clima_info['clima']}</strong></p>
                <p>Temp: {clima_info['temp_promedio']} | Humedad: {clima_info['humedad']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.subheader("Parámetros Hematológicos")
        mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1)
        mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1)
        mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1)
    
    st.markdown("---")
    st.header("2. Factores Socioeconómicos y Contextuales")
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.subheader("🏥 Factores Clínicos Adicionales")
        factores_clinicos = st.multiselect("Factores Clínicos:", FACTORES_CLINICOS, label_visibility="collapsed")
    
    with col5:
        st.subheader("🏠 Factores Socioeconómicos")
        factores_sociales = st.multiselect("Factores Socioeconómicos:", FACTORES_SOCIOECONOMICOS, label_visibility="collapsed")
    
    st.markdown("---")
    st.header("3. Acceso a Programas y Servicios")
    acceso_servicios = st.multiselect("Barreras de Acceso:", ACCESO_SERVICIOS, label_visibility="collapsed")
    
    submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GENERAR REPORTE NIXON", type="primary")

# --- PROCESAMIENTO ---
if submitted:
    if not dni or not nombre_completo:
        st.error("❌ Por favor complete el DNI y nombre del paciente")
    else:
        clima_info = obtener_clima_region(region)
        nivel_riesgo, puntaje, estado_recomendado = calcular_riesgo_anemia(
            hemoglobina_g_dl, edad_meses, factores_clinicos, factores_sociales, acceso_servicios, clima_info['clima']
        )
        sugerencias = generar_sugerencias(
            nivel_riesgo, puntaje, factores_clinicos, factores_sociales, acceso_servicios, hemoglobina_g_dl, edad_meses, clima_info['clima']
        )
        
        st.markdown("---")
        st.header("📊 Análisis y Reporte de Control Oportuno - Nixon System")
        
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
        
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1:
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
        
        st.markdown("---")
        st.header("🎯 Estrategia Nixon - Intervención Oportuna Personalizada")
        
        for i, sugerencia in enumerate(sugerencias, 1):
            st.markdown(f"""
            <div class="factor-card">
                <h4>📍 {sugerencia}</h4>
            </div>
            """, unsafe_allow_html=True)
        
        if supabase:
            record = {
                "dni": dni,
                "nombre_completo": nombre_completo,
                "edad_meses": int(edad_meses),
                "hemoglobina_g_dL": float(hemoglobina_g_dl),
                "riesgo": nivel_riesgo,
                "fecha_alerta": datetime.now().isoformat(),
                "estado_recomendado": estado_recomendado,
                "sugerencias_texto": "; ".join(sugerencias),
                "region": region
            }
            
            resultado = insertar_datos_supabase(record)
            if resultado:
                st.success("✅ Datos guardados correctamente en Sistema Nixon!")
                st.balloons()
            else:
                st.error("❌ Error al guardar en Supabase")
        else:
            st.warning("⚠️ Datos no guardados - Sin conexión a Supabase")

# --- PANEL DE CONTROL ---
st.markdown("---")
st.header("📈 Panel de Control Estadístico Nixon - Datos en Tiempo Real")

if st.button("🔄 Actualizar Dashboard Nixon desde Supabase"):
    datos_reales = obtener_datos_supabase()
    
    if not datos_reales.empty:
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("Total Casos Nixon", len(datos_reales))
        with col_stat2:
            alto_riesgo = len(datos_reales[datos_reales['riesgo'].str.contains('ALTO', na=False)])
            st.metric("Alertas Activas", alto_riesgo)
        with col_stat3:
            avg_hemoglobina = datos_reales['hemoglobina'].mean() if 'hemoglobina' in datos_reales.columns else 0
            st.metric("Hb Promedio", f"{avg_hemoglobina:.1f} g/dL")
        with col_stat4:
            region_mas_casos = datos_reales['region'].mode()[0] if not datos_reales['region'].mode().empty else "N/A"
            st.metric("Región Más Afectada", region_mas_casos)
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("📊 Distribución de Riesgos Nixon")
            fig_riesgos = px.pie(datos_reales, names='riesgo', title='Distribución de Niveles de Riesgo')
            st.plotly_chart(fig_riesgos, use_container_width=True)
        
        with col_chart2:
            st.subheader("📈 Tendencia por Región")
            casos_por_region = datos_reales['region'].value_counts().head(10)
            fig_barras = px.bar(x=casos_por_region.index, y=casos_por_region.values, title='Top 10 Regiones con Más Casos')
            st.plotly_chart(fig_barras, use_container_width=True)
        
        st.subheader("🕐 Casos Recientes - Monitoring Nixon")
        st.dataframe(datos_reales.head(15), use_container_width=True)
    else:
        st.info("💡 Sistema Nixon listo. Comience ingresando el primer caso.")
