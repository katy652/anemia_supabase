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

# ==================================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
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
    .risk-high { background-color: #ffebee; border-left: 5px solid #f44336; }
    .risk-moderate { background-color: #fff3e0; border-left: 5px solid #ff9800; }
    .risk-low { background-color: #e8f5e8; border-left: 5px solid #4caf50; }
    .factor-card { background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; }
    .metric-card { background: white; padding: 1rem; border-radius: 8px; text-align: center; }
    .climate-card { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 2. CONFIGURACIÓN SUPABASE
# ==================================================

TABLE_NAME = "alertas_hemoglobina"
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw")

@st.cache_resource
def init_supabase():
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        test_response = supabase_client.table(TABLE_NAME).select("*").limit(1).execute()
        st.success("✅ Conexión a Supabase establecida")
        return supabase_client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None

supabase = init_supabase()

# ==================================================
# 3. DATOS PERSONALES
# ==================================================

def mostrar_seccion_datos_personales():
    st.header("👤 Datos Personales del Paciente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        dni = st.text_input("DNI*", key="dni_personal")
        nombre_completo = st.text_input("Nombre Completo*", key="nombre_personal")
        edad_meses = st.number_input("Edad (meses)*", 1, 240, 24, key="edad_personal")
        peso_kg = st.number_input("Peso (kg)", 0.0, 50.0, 12.5, 0.1, key="peso_personal")
        
    with col2:
        talla_cm = st.number_input("Talla (cm)", 0.0, 150.0, 85.0, 0.1, key="talla_personal")
        genero = st.selectbox("Género*", ["M", "F", "Otro"], key="genero_personal")
        telefono = st.text_input("Teléfono", key="telefono_personal")
        estado_paciente = st.selectbox("Estado del Paciente*", 
                                     ["Activo", "En seguimiento", "Dado de alta", "Inactivo"], 
                                     key="estado_personal")
    
    return {
        'dni': dni,
        'nombre_completo': nombre_completo,
        'edad_meses': edad_meses,
        'peso_kg': peso_kg,
        'talla_cm': talla_cm,
        'genero': genero,
        'telefono': telefono,
        'estado_paciente': estado_paciente
    }

# ==================================================
# 4. FACTORES DEMOGRÁFICOS
# ==================================================

PERU_REGIONS = [
    "LIMA", "AREQUIPA", "CUSCO", "PUNO", "ICA", "LORETO", "SAN MARTÍN", 
    "LA LIBERTAD", "ANCASH", "JUNÍN", "PIURA", "LAMBAYEQUE", "OTRO"
]

CLIMA_POR_REGION = {
    "LIMA": {"clima": "Desértico subtropical", "temp_promedio": "21°C", "humedad": "85%"},
    "AREQUIPA": {"clima": "Semiárido", "temp_promedio": "18°C", "humedad": "45%"},
    "CUSCO": {"clima": "Templado subhúmedo", "temp_promedio": "14°C", "humedad": "65%"},
    "PUNO": {"clima": "Frío de altura", "temp_promedio": "8°C", "humedad": "55%"},
    "OTRO": {"clima": "No especificado", "temp_promedio": "N/A", "humedad": "N/A"}
}

def mostrar_seccion_demograficos():
    st.header("🌍 Factores Demográficos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        region = st.selectbox("Región*", PERU_REGIONS, key="region_demo")
        departamento = st.text_input("Departamento/Distrito", key="depto_demo")
        altitud_msnm = st.number_input("Altitud (msnm)", 0, 5000, 150, key="altitud_demo")
        
    with col2:
        # Mostrar información climática
        clima_info = CLIMA_POR_REGION.get(region, CLIMA_POR_REGION["OTRO"])
        st.markdown(f"""
        <div class="climate-card" style="padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <h4>🌤️ Clima {region}</h4>
            <p><strong>{clima_info['clima']}</strong></p>
            <p>🌡️ Temp: {clima_info['temp_promedio']} | 💧 Humedad: {clima_info['humedad']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    return {
        'region': region,
        'departamento': departamento,
        'altitud_msnm': altitud_msnm,
        'clima_info': clima_info
    }

# ==================================================
# 5. FACTORES SOCIOECONÓMICOS
# ==================================================

FACTORES_SOCIOECONOMICOS = [
    "Bajo nivel educativo de padres",
    "Ingresos familiares reducidos",
    "Hacinamiento en vivienda",
    "Acceso limitado a agua potable",
    "Zona rural o alejada",
    "Trabajo informal o precario",
    "Desnutrición familiar",
    "Falta de saneamiento básico"
]

def mostrar_seccion_socioeconomicos():
    st.header("💰 Factores Socioeconómicos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_educativo = st.selectbox("Nivel Educativo Familiar", 
                                     ["Sin educación", "Primaria", "Secundaria", "Superior"], 
                                     key="educacion_socio")
        acceso_agua_potable = st.checkbox("Acceso a agua potable", key="agua_socio")
        tiene_servicio_salud = st.checkbox("Tiene servicio de salud", key="salud_socio")
        
    with col2:
        st.subheader("Factores de Riesgo Social")
        factores_sociales = st.multiselect(
            "Seleccione factores presentes:",
            FACTORES_SOCIOECONOMICOS,
            help="Condiciones sociales que afectan la salud",
            key="factores_socio"
        )
    
    return {
        'nivel_educativo': nivel_educativo,
        'acceso_agua_potable': acceso_agua_potable,
        'tiene_servicio_salud': tiene_servicio_salud,
        'factores_sociales': factores_sociales
    }

# ==================================================
# 6. FACTORES CLÍNICOS
# ==================================================

FACTORES_CLINICOS = [
    "Historial familiar de anemia",
    "Bajo peso al nacer (<2500g)",
    "Prematurez (<37 semanas)",
    "Infecciones recurrentes",
    "Parasitosis intestinal",
    "Enfermedades crónicas",
    "Problemas gastrointestinales",
    "Medicamentos que afectan absorción"
]

ACCESO_SERVICIOS = [
    "Control prenatal irregular",
    "Limitado acceso a suplementos",
    "Barreras geográficas a centros de salud",
    "Falta de información nutricional",
    "Cobertura insuficiente de seguros"
]

def mostrar_seccion_clinicos():
    st.header("🏥 Factores Clínicos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parámetros Hematológicos")
        hemoglobina_dl1 = st.number_input("Hemoglobina (g/dL)*", 5.0, 20.0, 9.7, 0.1, key="hemo_clinico")
        mch = st.number_input("MCH (pg)", 15.0, 40.0, 28.0, 0.1, key="mch_clinico")
        mchc = st.number_input("MCHC (g/dL)", 25.0, 40.0, 33.0, 0.1, key="mchc_clinico")
        mcv = st.number_input("MCV (fL)", 60.0, 120.0, 90.0, 0.1, key="mcv_clinico")
        
    with col2:
        st.subheader("Estado y Seguimiento")
        en_seguimiento = st.checkbox("En seguimiento activo", key="seguimiento_clinico")
        consume_hierro = st.checkbox("Consume suplemento de hierro", key="hierro_clinico")
        tipo_suplemento = st.text_input("Tipo de suplemento", key="tipo_clinico")
        frecuencia_suplemento = st.selectbox("Frecuencia", 
                                           ["Diario", "3 veces/semana", "Semanal", "Otra"], 
                                           key="frecuencia_clinico")
    
    st.subheader("Factores Clínicos de Riesgo")
    col3, col4 = st.columns(2)
    
    with col3:
        factores_clinicos = st.multiselect(
            "Factores Clínicos:",
            FACTORES_CLINICOS,
            key="factores_clinicos"
        )
        antecedentes_anemia = st.checkbox("Antecedentes de anemia", key="antecedentes_clinico")
        enfermedades_cronicas = st.text_area("Enfermedades crónicas", key="cronicas_clinico")
    
    with col4:
        acceso_servicios = st.multiselect(
            "Barreras de Acceso:",
            ACCESO_SERVICIOS,
            key="acceso_clinico"
        )
    
    return {
        'hemoglobina_dl1': hemoglobina_dl1,
        'mch': mch,
        'mchc': mchc,
        'mcv': mcv,
        'en_seguimiento': en_seguimiento,
        'consume_hierro': consume_hierro,
        'tipo_suplemento': tipo_suplemento,
        'frecuencia_suplemento': frecuencia_suplemento,
        'factores_clinicos': factores_clinicos,
        'antecedentes_anemia': antecedentes_anemia,
        'enfermedades_cronicas': enfermedades_cronicas,
        'acceso_servicios': acceso_servicios
    }

# ==================================================
# 7. CÁLCULO DE RIESGO
# ==================================================

def calcular_riesgo_anemia(hb, edad_meses, factores_clinicos, factores_sociales, acceso_servicios, clima_region):
    puntaje = 0
    
    # Base por hemoglobina según edad
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

# ==================================================
# 8. INTERFAZ PRINCIPAL CON PESTAÑAS
# ==================================================

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia")
st.markdown("**Sistema integrado de monitoreo y alertas tempranas**")
st.markdown('</div>', unsafe_allow_html=True)

# Crear pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Registro Completo", 
    "🔍 Casos en Seguimiento", 
    "📊 Parámetros Hematológicos", 
    "📈 Estadísticas"
])

# Pestaña 1: REGISTRO COMPLETO
with tab1:
    st.header("📝 Registro Completo de Paciente")
    
    with st.form("formulario_completo"):
        # 1. Datos Personales
        datos_personales = mostrar_seccion_datos_personales()
        st.markdown("---")
        
        # 2. Factores Demográficos
        datos_demograficos = mostrar_seccion_demograficos()
        st.markdown("---")
        
        # 3. Factores Socioeconómicos
        datos_socioeconomicos = mostrar_seccion_socioeconomicos()
        st.markdown("---")
        
        # 4. Factores Clínicos
        datos_clinicos = mostrar_seccion_clinicos()
        
        submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GUARDAR", type="primary")
    
    if submitted:
        # Validar campos obligatorios
        if not datos_personales['dni'] or not datos_personales['nombre_completo']:
            st.error("❌ Complete DNI y nombre del paciente")
        else:
            # Calcular riesgo
            nivel_riesgo, puntaje, estado = calcular_riesgo_anemia(
                datos_clinicos['hemoglobina_dl1'],
                datos_personales['edad_meses'],
                datos_clinicos['factores_clinicos'],
                datos_socioeconomicos['factores_sociales'],
                datos_clinicos['acceso_servicios'],
                datos_demograficos['clima_info']['clima']
            )
            
            # Mostrar resultados
            st.success(f"✅ Análisis completado: {nivel_riesgo}")

# Pestaña 2: CASOS EN SEGUIMIENTO
with tab2:
    st.header("🔍 Casos en Seguimiento")
    # Aquí iría la lógica para mostrar pacientes en seguimiento

# Pestaña 3: PARÁMETROS HEMATOLÓGICOS
with tab3:
    st.header("📊 Parámetros Hematológicos")
    # Aquí irían análisis específicos de parámetros de sangre

# Pestaña 4: ESTADÍSTICAS
with tab4:
    st.header("📈 Estadísticas y Reportes")
    
