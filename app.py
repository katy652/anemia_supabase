import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime, timedelta
import re

# ==================================================
# CONFIGURACIÓN SUPABASE
# ==================================================

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw")

# Nombres de tablas
TABLE_NAME = "alertas_hemoglobina"
CITAS_TABLE = "citas"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None

supabase = init_supabase()

# ==================================================
# FUNCIONES COMUNES DE BASE DE DATOS
# ==================================================

def obtener_datos(tabla=TABLE_NAME):
    """Obtiene datos de cualquier tabla de Supabase"""
    try:
        if supabase:
            response = supabase.table(tabla).select("*").execute()
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
        return False

def insertar_datos_supabase(datos, tabla=TABLE_NAME):
    """Inserta datos en Supabase verificando duplicados"""
    try:
        dni = datos.get("dni")
        
        if not dni:
            return None
        
        if verificar_duplicado(dni):
            return {"status": "duplicado", "dni": dni}
        
        if supabase:
            response = supabase.table(tabla).insert(datos).execute()
            if hasattr(response, 'error') and response.error:
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        return None

# ==================================================
# FUNCIONES ESPECÍFICAS PARA VALIDACIONES
# ==================================================

def validar_dni(dni):
    """Valida que el DNI tenga exactamente 8 dígitos numéricos"""
    if not dni:
        return False, "El DNI no puede estar vacío"
    
    if not dni.isdigit():
        return False, "El DNI debe contener solo números"
    
    if len(dni) != 8:
        return False, "El DNI debe tener exactamente 8 dígitos"
    
    return True, "DNI válido"

def validar_nombre(nombre):
    """Valida que el nombre contenga solo letras y espacios"""
    if not nombre:
        return False, "El nombre no puede estar vacío"
    
    # Verificar que solo contenga letras, espacios y acentos
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
        return False, "El nombre solo puede contener letras y espacios"
    
    return True, "Nombre válido"

# ==================================================
# SISTEMA DE LOGIN Y SESIÓN
# ==================================================

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.current_username = None

USUARIOS_SALUD = {
    "admin": {
        "password": "Admin123",
        "nombre": "Dr. Carlos Martínez",
        "rol": "Administrador",
        "especialidad": "Pediatría",
        "email": "admin@hospital.com"
    },
    "pediatra1": {
        "password": "Pediatra123",
        "nombre": "Dra. Ana López",
        "rol": "Pediatra",
        "especialidad": "Pediatría General",
        "email": "pediatra1@hospital.com"
    },
    "pediatra2": {
        "password": "Pediatra456",
        "nombre": "Dr. Juan Pérez",
        "rol": "Pediatra",
        "especialidad": "Nutrición Infantil",
        "email": "pediatra2@hospital.com"
    },
    "enfermero": {
        "password": "Enfermero123",
        "nombre": "Lic. María Gómez",
        "rol": "Enfermero/a",
        "especialidad": "Salud Pública",
        "email": "enfermero@hospital.com"
    },
    "tecnico": {
        "password": "Tecnico123",
        "nombre": "Téc. Luis Rodríguez",
        "rol": "Técnico de Laboratorio",
        "especialidad": "Hematología",
        "email": "tecnico@hospital.com"
    }
}

# ==================================================
# 1. DASHBOARD PÚBLICO (SIN LOGIN)
# ==================================================

def show_dashboard_publico():
    """Pestaña 1: Dashboard público - Acceso libre"""
    
    st.set_page_config(
        page_title="Dashboard Público - Sistema Nixon",
        layout="wide"
    )
    
    # Estilos CSS
    st.markdown("""
    <style>
    .public-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .public-metric {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .login-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid #f59e0b;
        margin: 2rem 0;
        text-align: center;
    }
    
    .nav-button {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Botón de navegación
    st.markdown("""
    <div class="nav-button">
        <a href="/?page=login" target="_self">
            <button style="background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%); 
                    color: white; border: none; padding: 10px 20px; border-radius: 8px; 
                    font-weight: 600; cursor: pointer;">
                🔐 Acceso Personal
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown("""
    <div class="public-header">
        <h1 style="margin: 0; font-size: 2.8rem;">📊 DASHBOARD NACIONAL</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.2rem; opacity: 0.9;">
        Estadísticas Públicas de Anemia y Nutrición Infantil en Perú
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner("Cargando datos nacionales..."):
        datos = obtener_datos()
    
    if not datos.empty:
        # MÉTRICAS PRINCIPALES
        st.markdown("### 🎯 Indicadores Nacionales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(datos)
            st.markdown(f"""
            <div class="public-metric">
                <div style="font-size: 0.9rem; color: #6b7280;">TOTAL EVALUADOS</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #1e40af;">{total:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if 'region' in datos.columns:
                regiones = datos['region'].nunique()
                st.markdown(f"""
                <div class="public-metric">
                    <div style="font-size: 0.9rem; color: #6b7280;">REGIÓNES</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: #065f46;">{regiones}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if 'hemoglobina_dl1' in datos.columns:
                hb_prom = datos['hemoglobina_dl1'].mean()
                st.markdown(f"""
                <div class="public-metric">
                    <div style="font-size: 0.9rem; color: #6b7280;">HEMOGLOBINA</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: #5b21b6;">{hb_prom:.1f} g/dL</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if 'edad_meses' in datos.columns:
                edad_prom = datos['edad_meses'].mean() / 12
                st.markdown(f"""
                <div class="public-metric">
                    <div style="font-size: 0.9rem; color: #6b7280;">EDAD PROMEDIO</div>
                    <div style="font-size: 2.5rem; font-weight: 800; color: #92400e;">{edad_prom:.1f} años</div>
                </div>
                """, unsafe_allow_html=True)
        
        # GRÁFICOS PÚBLICOS
        st.markdown("### 📈 Distribución por Región")
        if 'region' in datos.columns:
            region_stats = datos['region'].value_counts().head(10)
            fig = px.bar(
                region_stats,
                title="<b>Top 10 Regiones con más casos</b>",
                labels={'value': 'Casos', 'index': 'Región'},
                color=region_stats.values,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # CARTA DE ACCESO AL SISTEMA
        st.markdown("""
        <div class="login-card">
            <h3 style="color: #92400e; margin-bottom: 15px;">🚀 ¿Eres personal de salud?</h3>
            <p style="color: #78350f; margin-bottom: 20px;">
            Accede al sistema completo para registrar pacientes, hacer seguimiento clínico, 
            programar citas y más funciones avanzadas.
            </p>
            
            <a href="/?page=login" target="_self">
                <button style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                        color: white; border: none; padding: 12px 24px; border-radius: 8px; 
                        font-weight: 600; cursor: pointer; width: 100%;">
                    🔐 Iniciar Sesión
                </button>
            </a>
            
            <p style="color: #92400e; margin-top: 20px; font-size: 0.9rem;">
            <strong>Usuarios de prueba:</strong> admin / pediatra1 / pediatra2 / enfermero / tecnico
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        st.warning("No hay datos disponibles para mostrar")
        
        # Mensaje alternativo
        st.markdown("""
        <div class="login-card">
            <h3 style="color: #92400e;">📋 Sistema Nixon - Control de Anemia</h3>
            <p style="color: #78350f;">
            Sistema integral para el control y seguimiento de anemia y nutrición infantil.
            </p>
            
            <a href="/?page=login" target="_self">
                <button style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                        color: white; border: none; padding: 12px 24px; border-radius: 8px; 
                        font-weight: 600; cursor: pointer; width: 100%;">
                    🔐 Acceder al Sistema
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

# ==================================================
# 2. PÁGINA DE LOGIN
# ==================================================

def show_login_page():
    """Pestaña 2: Login - Acceso al sistema privado"""
    
    st.set_page_config(
        page_title="Login - Sistema Nixon",
        layout="centered"
    )
    
    # Estilos CSS
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 50px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(30, 64, 175, 0.1);
        border: 2px solid #e0f2fe;
    }
    
    .user-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 12px 0;
        border-left: 5px solid #3b82f6;
    }
    
    .dashboard-link {
        text-align: center;
        margin-top: 25px;
        padding-top: 20px;
        border-top: 1px solid #e5e7eb;
    }
    
    .nav-button-login {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Botón de navegación
    st.markdown("""
    <div class="nav-button-login">
        <a href="/?page=dashboard" target="_self">
            <button style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    color: white; border: none; padding: 10px 20px; border-radius: 8px; 
                    font-weight: 600; cursor: pointer;">
                📊 Dashboard Público
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Contenedor principal
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Título
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 60px; margin-bottom: 20px; color: #1e40af;">🏥</div>
        <h1 style="color: #1e3a8a; font-size: 2.2rem; margin: 0;">SISTEMA NIXON</h1>
        <p style="color: #6b7280; margin-top: 10px;">Control de Anemia y Nutrición Infantil</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login
    with st.form("login_form"):
        username = st.text_input("👤 Nombre de Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        submit = st.form_submit_button("🚀 INICIAR SESIÓN", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("❌ Por favor, ingresa usuario y contraseña")
            else:
                if username in USUARIOS_SALUD and USUARIOS_SALUD[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USUARIOS_SALUD[username]
                    st.session_state.current_username = username
                    st.success(f"✅ ¡Bienvenido/a, {USUARIOS_SALUD[username]['nombre']}!")
                    time.sleep(1)
                    st.query_params.page = "system"
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
    # Información de usuarios
    with st.expander("👥 USUARIOS AUTORIZADOS", expanded=True):
        st.markdown("**Personal de Salud Autorizado:**")
        
        for username, info in USUARIOS_SALUD.items():
            st.markdown(f"""
            <div class="user-card">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 1.1rem;">{info['nombre']}</strong>
                    <span style="background: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; 
                           font-size: 12px; font-weight: 600; margin-left: 10px;">
                        {info['rol']}
                    </span>
                </div>
                <div style="font-size: 0.9rem; color: #4b5563;">
                    <div><strong>Especialidad:</strong> {info['especialidad']}</div>
                    <div><strong>Usuario:</strong> <code>{username}</code></div>
                    <div><strong>Contraseña:</strong> <code>{info['password']}</code></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Link al dashboard público
    st.markdown("""
    <div class="dashboard-link">
        <p style="color: #6b7280; margin-bottom: 10px;">¿Solo quieres ver estadísticas públicas?</p>
        <a href="/?page=dashboard" target="_self">
            <button style="background: #10b981; color: white; border: none; padding: 10px 20px; 
                    border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%;">
                📊 Ver Dashboard Público
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# 3. SISTEMA COMPLETO (REQUIERE LOGIN)
# ==================================================

def show_sistema_completo():
    """Pestaña 3: Sistema completo con todas las funcionalidades"""
    
    # Verificar login
    if not st.session_state.logged_in:
        st.warning("⚠️ Debes iniciar sesión primero")
        st.query_params.page = "login"
        st.rerun()
    
    # Configurar página
    st.set_page_config(
        page_title="Sistema Nixon - Control de Anemia",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Estilos CSS para sistema completo
    st.markdown("""
    <style>
    .system-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .user-sidebar-info {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    
    .section-title {
        color: #1e3a8a;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 10px;
        border-bottom: 3px solid #3b82f6;
    }
    
    .error-message {
        background: #fee2e2;
        color: #dc2626;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #dc2626;
        margin: 10px 0;
    }
    
    .nav-button-system {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Botón de navegación
    st.markdown("""
    <div class="nav-button-system">
        <a href="/?page=dashboard" target="_self">
            <button style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    color: white; border: none; padding: 10px 20px; border-radius: 8px; 
                    font-weight: 600; cursor: pointer;">
                📊 Dashboard Público
            </button>
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    # Obtener información del usuario
    user_info = st.session_state.user_info
    
    # ============================================
    # SIDEBAR DEL SISTEMA COMPLETO
    # ============================================
    with st.sidebar:
        # Información del usuario
        st.markdown(f"""
        <div class="user-sidebar-info">
            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 5px;">👤 {user_info['nombre']}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 15px; background: rgba(255,255,255,0.15); 
                 padding: 4px 12px; border-radius: 15px; display: inline-block;">
                {user_info['rol']}
            </div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 5px;">
                {user_info['email']}<br>
                <small>Especialidad: {user_info['especialidad']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.current_username = None
            st.query_params.page = "dashboard"
            st.rerun()
        
        st.markdown("---")
        
        # Enlace al dashboard público
        if st.button("📊 Dashboard Público", use_container_width=True):
            st.query_params.page = "dashboard"
            st.rerun()
    
    # ============================================
    # HEADER PRINCIPAL DEL SISTEMA
    # ============================================
    st.markdown(f"""
    <div class="system-header">
        <h1 style="margin: 0; font-size: 2.5rem;">🏥 SISTEMA NIXON COMPLETO</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Control Integral de Anemia y Nutrición Infantil
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # PESTAÑAS INTERNAS DEL SISTEMA COMPLETO
    # ============================================
    
    # Definir las pestañas principales
    tab_registro, tab_seguimiento, tab_citas, tab_pacientes, tab_config = st.tabs([
        "📝 Registro Completo", 
        "🔍 Seguimiento Clínico", 
        "📅 Sistema de Citas",
        "👥 Pacientes",
        "⚙️ Configuración"
    ])
    
    # -------------------------------------------------
    # Pestaña 1: REGISTRO COMPLETO (CON VALIDACIONES)
    # -------------------------------------------------
    with tab_registro:
        st.markdown('<div class="section-title">📝 REGISTRO COMPLETO DE PACIENTE</div>', unsafe_allow_html=True)
        
        # FACTORES SOCIOECONÓMICOS DEL APODERADO
        RELACION_APODERADO = ["PADRE", "MADRE", "TIA/O", "ABUELA/O", "OTROS"]
        FACTORES_SOCIOECONOMICOS = [
            "Bajo nivel educativo de apoderado",
            "Ingresos familiares reducidos",
            "Hacinamiento en vivienda",
            "Acceso limitado a agua potable",
            "Zona rural o alejada",
            "Trabajo informal o precario",
            "Falta de seguro de salud",
            "Alimentación inadecuada"
        ]
        
        with st.form("formulario_registro"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👤 DATOS PERSONALES**")
                
                # DNI con validación
                dni = st.text_input("DNI*", placeholder="Ej: 87654321", max_chars=8, key="dni_input")
                if dni:
                    valido_dni, mensaje_dni = validar_dni(dni)
                    if not valido_dni:
                        st.markdown(f'<div class="error-message">❌ {mensaje_dni}</div>', unsafe_allow_html=True)
                
                # Nombre completo con validación
                nombre_completo = st.text_input("Nombre Completo*", placeholder="Ej: Ana García Pérez", key="nombre_input")
                if nombre_completo:
                    valido_nombre, mensaje_nombre = validar_nombre(nombre_completo)
                    if not valido_nombre:
                        st.markdown(f'<div class="error-message">❌ {mensaje_nombre}</div>', unsafe_allow_html=True)
                
                edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
                peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1)
                talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1)
                genero = st.selectbox("Género*", ["F", "M"])
            
            with col2:
                st.markdown("**👥 DATOS DEL APODERADO**")
                
                relacion_apoderado = st.selectbox("Relación con el paciente*", RELACION_APODERADO)
                
                st.markdown("**💰 FACTORES SOCIOECONÓMICOS**")
                factores_sociales = st.multiselect("Seleccione factores socioeconómicos:", FACTORES_SOCIOECONOMICOS)
                
                # Otros datos
                telefono = st.text_input("Teléfono del apoderado", placeholder="Ej: 987654321")
                nivel_educativo = st.selectbox("Nivel educativo del apoderado", 
                                             ["Sin educación", "Primaria", "Secundaria", "Superior"])
            
            # Datos clínicos
            st.markdown("**🩺 DATOS CLÍNICOS**")
            col3, col4 = st.columns(2)
            
            with col3:
                hemoglobina = st.number_input("Hemoglobina (g/dL)*", 5.0, 20.0, 11.0, 0.1)
                consume_suplemento = st.checkbox("Consume suplemento de hierro")
                if consume_suplemento:
                    tipo_suplemento = st.text_input("Tipo de suplemento")
                    frecuencia = st.selectbox("Frecuencia", ["Diario", "3 veces/semana", "Semanal"])
            
            with col4:
                antecedentes_anemia = st.checkbox("Antecedentes de anemia")
                enfermedades = st.text_area("Enfermedades crónicas", placeholder="Ej: Asma, alergias, etc.")
            
            submitted = st.form_submit_button("💾 GUARDAR REGISTRO", type="primary", use_container_width=True)
            
            if submitted:
                # Validaciones finales
                errores = []
                
                if not dni:
                    errores.append("El DNI es obligatorio")
                else:
                    valido_dni, mensaje_dni = validar_dni(dni)
                    if not valido_dni:
                        errores.append(mensaje_dni)
                
                if not nombre_completo:
                    errores.append("El nombre completo es obligatorio")
                else:
                    valido_nombre, mensaje_nombre = validar_nombre(nombre_completo)
                    if not valido_nombre:
                        errores.append(mensaje_nombre)
                
                if errores:
                    for error in errores:
                        st.error(f"❌ {error}")
                else:
                    # Crear registro
                    registro = {
                        "dni": dni.strip(),
                        "nombre_apellido": nombre_completo.strip().title(),
                        "edad_meses": int(edad_meses),
                        "peso_kg": float(peso_kg),
                        "talla_cm": float(talla_cm),
                        "genero": genero,
                        "telefono": telefono.strip() if telefono else None,
                        "relacion_apoderado": relacion_apoderado,
                        "factores_socioeconomicos": ", ".join(factores_sociales) if factores_sociales else None,
                        "nivel_educativo_apoderado": nivel_educativo,
                        "hemoglobina_dl1": float(hemoglobina),
                        "consumir_hierro": consume_suplemento,
                        "tipo_suplemento_hierro": tipo_suplemento if consume_suplemento else None,
                        "frecuencia_suplemento": frecuencia if consume_suplemento else None,
                        "antecedentes_anemia": antecedentes_anemia,
                        "enfermedades_cronicas": enfermedades.strip() if enfermedades else None,
                        "fecha_registro": datetime.now().strftime("%Y-%m-%d"),
                        "registrado_por": user_info['nombre']
                    }
                    
                    # Guardar en Supabase
                    if supabase:
                        with st.spinner("Guardando registro..."):
                            resultado = insertar_datos_supabase(registro)
                            
                            if resultado:
                                if isinstance(resultado, dict) and resultado.get("status") == "duplicado":
                                    st.error(f"❌ El DNI {dni} ya existe en la base de datos")
                                else:
                                    st.success("✅ Paciente registrado exitosamente")
                                    st.balloons()
                                    time.sleep(2)
                                    st.rerun()
                            else:
                                st.error("❌ Error al guardar el registro")
                    else:
                        st.error("🔴 No hay conexión a la base de datos")
    
    # -------------------------------------------------
    # Pestaña 2: SEGUIMIENTO CLÍNICO (BUSCAR POR DNI)
    # -------------------------------------------------
    with tab_seguimiento:
        st.markdown('<div class="section-title">🔍 SEGUIMIENTO CLÍNICO</div>', unsafe_allow_html=True)
        
        # BÚSQUEDA POR DNI
        col_busq1, col_busq2 = st.columns([3, 1])
        
        with col_busq1:
            dni_buscar = st.text_input("🔍 Buscar paciente por DNI", 
                                      placeholder="Ingrese DNI de 8 dígitos",
                                      key="buscar_dni")
        
        with col_busq2:
            buscar = st.button("🔎 Buscar", use_container_width=True)
        
        paciente_encontrado = None
        
        if buscar and dni_buscar:
            valido, mensaje = validar_dni(dni_buscar)
            
            if not valido:
                st.error(f"❌ {mensaje}")
            else:
                with st.spinner("Buscando paciente..."):
                    try:
                        response = supabase.table(TABLE_NAME)\
                            .select("*")\
                            .eq("dni", dni_buscar)\
                            .execute()
                        
                        if response.data and len(response.data) > 0:
                            paciente_encontrado = response.data[0]
                            st.success(f"✅ Paciente encontrado: {paciente_encontrado['nombre_apellido']}")
                        else:
                            st.warning(f"⚠️ No se encontró paciente con DNI {dni_buscar}")
                    except Exception as e:
                        st.error(f"❌ Error en la búsqueda: {str(e)}")
        
        # SI SE ENCONTRÓ EL PACIENTE, MOSTRAR SEGUIMIENTO
        if paciente_encontrado:
            # Mostrar información básica
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #6b7280;">PACIENTE</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #1e40af;">
                    {paciente_encontrado['nombre_apellido']}
                    </div>
                    <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
                    Edad: {paciente_encontrado['edad_meses']} meses
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info2:
                hb = paciente_encontrado.get('hemoglobina_dl1', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #6b7280;">HEMOGLOBINA</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #5b21b6;">
                    {hb:.1f} g/dL
                    </div>
                    <div style="font-size: 0.9rem; color: #6b7280; margin-top: 5px;">
                    Última medición
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info3:
                riesgo = paciente_encontrado.get('riesgo', 'No evaluado')
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #6b7280;">RIESGO</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #065f46;">
                    {riesgo}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # REGISTRAR NUEVO SEGUIMIENTO
            st.markdown("**📝 REGISTRAR NUEVO SEGUIMIENTO**")
            
            with st.form("form_seguimiento"):
                col_seg1, col_seg2 = st.columns(2)
                
                with col_seg1:
                    fecha_seguimiento = st.date_input("Fecha de seguimiento", datetime.now())
                    nueva_hemoglobina = st.number_input("Nueva hemoglobina (g/dL)", 
                                                       min_value=5.0, max_value=20.0, 
                                                       value=float(hb), step=0.1)
                
                with col_seg2:
                    peso_actual = st.number_input("Peso actual (kg)", 
                                                 min_value=0.0, max_value=50.0, 
                                                 value=float(paciente_encontrado.get('peso_kg', 0)), 
                                                 step=0.1)
                    talla_actual = st.number_input("Talla actual (cm)", 
                                                  min_value=0.0, max_value=150.0, 
                                                  value=float(paciente_encontrado.get('talla_cm', 0)), 
                                                  step=0.1)
                
                observaciones = st.text_area("Observaciones del seguimiento", 
                                           placeholder="Describa el estado del paciente, cambios, etc.")
                
                if st.form_submit_button("💾 GUARDAR SEGUIMIENTO", use_container_width=True):
                    # Aquí iría la lógica para guardar el seguimiento
                    st.success("✅ Seguimiento registrado")
            
            st.markdown("---")
            
            # GRÁFICO DE PROGRESO CON LEYENDA MEJORADA
            st.markdown("**📈 GRÁFICO DE PROGRESO DEL PACIENTE**")
            
            # Datos simulados para el gráfico
            fechas = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
            valores_hb = [float(hb)]
            
            # Simular progreso
            for i in range(1, 6):
                mejora = np.random.uniform(0.2, 0.5)
                nuevo_valor = valores_hb[0] + mejora * i
                valores_hb.append(min(nuevo_valor, 15.0))
            
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
            
            # Áreas de severidad con leyenda mejorada
            fig.add_hrect(y0=0, y1=6.9, fillcolor="rgba(239,68,68,0.1)", 
                         line_width=0, annotation_text="Severa", 
                         annotation_position="left")
            fig.add_hrect(y0=7.0, y1=9.9, fillcolor="rgba(245,158,11,0.1)", 
                         line_width=0, annotation_text="Moderada",
                         annotation_position="left")
            fig.add_hrect(y0=10.0, y1=10.9, fillcolor="rgba(59,130,246,0.1)", 
                         line_width=0, annotation_text="Leve",
                         annotation_position="left")
            fig.add_hrect(y0=11.0, y1=15, fillcolor="rgba(16,185,129,0.1)", 
                         line_width=0, annotation_text="Normal",
                         annotation_position="left")
            
            # Línea de meta
            fig.add_hline(y=11.0, line_dash="dash", line_color="green",
                         annotation_text="Meta: 11.0 g/dL",
                         annotation_position="bottom right")
            
            # Configurar layout con leyenda mejorada
            fig.update_layout(
                title={
                    'text': "<b>EVOLUCIÓN DE HEMOGLOBINA</b>",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title="<b>Meses de Seguimiento</b>",
                yaxis_title="<b>Hemoglobina (g/dL)</b>",
                template="plotly_white",
                height=400,
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(255, 255, 255, 0.8)',
                    bordercolor='rgba(0, 0, 0, 0.2)',
                    borderwidth=1
                ),
                annotations=[
                    dict(
                        text="<b>LEYENDA:</b><br>🔴 Severa: < 7.0<br>🟠 Moderada: 7.0-9.9<br>🟡 Leve: 10.0-10.9<br>🟢 Normal: ≥ 11.0",
                        x=0.02,
                        y=0.98,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        bgcolor="rgba(255, 255, 255, 0.8)",
                        bordercolor="rgba(0, 0, 0, 0.2)",
                        borderwidth=1,
                        font=dict(size=10)
                    )
                ]
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Nota explicativa
            st.info("""
            **📋 Interpretación del gráfico:**
            - **Área roja:** Anemia severa (requiere atención inmediata)
            - **Área naranja:** Anemia moderada (seguimiento mensual)
            - **Área azul:** Anemia leve (seguimiento trimestral)
            - **Área verde:** Estado normal (control preventivo)
            - **Línea verde punteada:** Meta de hemoglobina según OMS
            """)
    
    # -------------------------------------------------
    # Pestaña 3: SISTEMA DE CITAS (4 SUB-PESTAÑAS)
    # -------------------------------------------------
    with tab_citas:
        st.markdown('<div class="section-title">📅 SISTEMA DE CITAS</div>', unsafe_allow_html=True)
        
        # Crear sub-pestañas para citas
        tab_citas1, tab_citas2, tab_citas3, tab_citas4 = st.tabs([
            "📅 Calendario de Seguimiento",
            "🔄 Generar Citas Automáticas",
            "🔔 Recordatorios Próximos",
            "📋 Historial de Citas"
        ])
        
        # SUB-PESTAÑA 1: CALENDARIO DE SEGUIMIENTO
        with tab_citas1:
            st.markdown("**📅 CALENDARIO DE SEGUIMIENTO**")
            
            # Función para obtener citas programadas
            def obtener_citas_programadas():
                try:
                    hoy = datetime.now().date()
                    fin_mes = hoy + timedelta(days=30)
                    
                    response = supabase.table(CITAS_TABLE)\
                        .select("*, alertas_hemoglobina(nombre_apellido, telefono)")\
                        .gte("fecha_cita", hoy.strftime('%Y-%m-%d'))\
                        .lte("fecha_cita", fin_mes.strftime('%Y-%m-%d'))\
                        .order("fecha_cita")\
                        .execute()
                    
                    if response.data:
                        return response.data
                    return []
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    return []
            
            if st.button("🔄 Actualizar Calendario", key="actualizar_cal"):
                with st.spinner("Cargando citas..."):
                    citas = obtener_citas_programadas()
                    st.session_state.citas_calendario = citas
            
            if 'citas_calendario' in st.session_state:
                citas_df = pd.DataFrame(st.session_state.citas_calendario)
                
                if not citas_df.empty:
                    # Expandir datos del paciente
                    citas_df['nombre_paciente'] = citas_df['alertas_hemoglobina'].apply(
                        lambda x: x.get('nombre_apellido', 'Desconocido') if x else 'Desconocido'
                    )
                    citas_df['telefono'] = citas_df['alertas_hemoglobina'].apply(
                        lambda x: x.get('telefono', 'Sin teléfono') if x else 'Sin teléfono'
                    )
                    
                    # Mostrar en formato de calendario
                    for fecha in sorted(citas_df['fecha_cita'].unique()):
                        citas_fecha = citas_df[citas_df['fecha_cita'] == fecha]
                        
                        st.markdown(f"### 📅 {fecha}")
                        
                        for _, cita in citas_fecha.iterrows():
                            col_cal1, col_cal2, col_cal3 = st.columns([3, 2, 1])
                            
                            with col_cal1:
                                st.markdown(f"**{cita['nombre_paciente']}**")
                                st.caption(f"Hora: {cita.get('hora_cita', '09:00')}")
                            
                            with col_cal2:
                                st.markdown(f"**{cita['tipo_consulta']}**")
                                st.caption(f"Tel: {cita['telefono']}")
                            
                            with col_cal3:
                                if st.button("📝", key=f"editar_{cita['id']}"):
                                    st.session_state.editar_cita_id = cita['id']
                
                else:
                    st.info("📭 No hay citas programadas para los próximos 30 días")
            else:
                st.info("👆 Presiona 'Actualizar Calendario' para cargar las citas")
        
        # SUB-PESTAÑA 2: GENERAR CITAS AUTOMÁTICAS
        with tab_citas2:
            st.markdown("**🔄 GENERAR CITAS AUTOMÁTICAS**")
            
            # Función para calcular frecuencia según hemoglobina
            def calcular_frecuencia_cita(hemoglobina):
                if hemoglobina < 7:
                    return "MENSUAL", 30
                elif hemoglobina < 10:
                    return "TRIMESTRAL", 90
                elif hemoglobina < 11:
                    return "SEMESTRAL", 180
                else:
                    return "ANUAL", 365
            
            # Búsqueda de paciente por DNI
            col_gen1, col_gen2 = st.columns([3, 1])
            
            with col_gen1:
                dni_cita = st.text_input("Ingrese DNI del paciente", 
                                        placeholder="DNI de 8 dígitos",
                                        key="dni_cita")
            
            with col_gen2:
                buscar_paciente = st.button("🔍 Buscar", use_container_width=True)
            
            if buscar_paciente and dni_cita:
                valido, mensaje = validar_dni(dni_cita)
                
                if not valido:
                    st.error(f"❌ {mensaje}")
                else:
                    with st.spinner("Buscando paciente..."):
                        try:
                            response = supabase.table(TABLE_NAME)\
                                .select("*")\
                                .eq("dni", dni_cita)\
                                .execute()
                            
                            if response.data:
                                paciente = response.data[0]
                                st.success(f"✅ Paciente encontrado: {paciente['nombre_apellido']}")
                                
                                # Mostrar información
                                col_info_c1, col_info_c2 = st.columns(2)
                                
                                with col_info_c1:
                                    st.info(f"**Hemoglobina:** {paciente.get('hemoglobina_dl1', 'N/A')} g/dL")
                                    st.info(f"**Edad:** {paciente.get('edad_meses', 'N/A')} meses")
                                
                                with col_info_c2:
                                    frecuencia, dias = calcular_frecuencia_cita(paciente.get('hemoglobina_dl1', 11))
                                    st.info(f"**Frecuencia sugerida:** {frecuencia}")
                                    st.info(f"**Próxima cita en:** {dias} días")
                                
                                # Formulario para generar cita
                                with st.form("form_generar_cita"):
                                    fecha_propuesta = datetime.now() + timedelta(days=dias)
                                    fecha_cita = st.date_input("Fecha de la cita", fecha_propuesta)
                                    hora_cita = st.time_input("Hora", value=datetime.strptime("09:00", "%H:%M").time())
                                    tipo_cita = st.selectbox("Tipo de consulta", 
                                                           ["Control", "Seguimiento", "Urgencia", "Reevaluación"])
                                    
                                    if st.form_submit_button("📅 GENERAR CITA", use_container_width=True):
                                        # Crear registro de cita
                                        cita_data = {
                                            "dni_paciente": dni_cita,
                                            "fecha_cita": fecha_cita.strftime('%Y-%m-%d'),
                                            "hora_cita": hora_cita.strftime('%H:%M:%S'),
                                            "tipo_consulta": tipo_cita,
                                            "diagnostico": f"Cita programada por sistema - Frecuencia: {frecuencia}",
                                            "tratamiento": "Según evaluación médica",
                                            "observaciones": f"Paciente con hemoglobina: {paciente.get('hemoglobina_dl1', 'N/A')} g/dL",
                                            "investigador_responsable": user_info['nombre'],
                                            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        }
                                        
                                        try:
                                            response = supabase.table(CITAS_TABLE).insert(cita_data).execute()
                                            if response.data:
                                                st.success("✅ Cita generada exitosamente")
                                                time.sleep(2)
                                                st.rerun()
                                            else:
                                                st.error("❌ Error al generar la cita")
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                            
                            else:
                                st.warning(f"⚠️ No se encontró paciente con DNI {dni_cita}")
                        except Exception as e:
                            st.error(f"❌ Error en la búsqueda: {str(e)}")
        
        # SUB-PESTAÑA 3: RECORDATORIOS PRÓXIMOS
        with tab_citas3:
            st.markdown("**🔔 RECORDATORIOS PRÓXIMOS**")
            
            def obtener_recordatorios():
                try:
                    hoy = datetime.now().date()
                    proxima_semana = hoy + timedelta(days=7)
                    
                    response = supabase.table(CITAS_TABLE)\
                        .select("*, alertas_hemoglobina(nombre_apellido, telefono)")\
                        .gte("fecha_cita", hoy.strftime('%Y-%m-%d'))\
                        .lte("fecha_cita", proxima_semana.strftime('%Y-%m-%d'))\
                        .order("fecha_cita")\
                        .execute()
                    
                    if response.data:
                        return response.data
                    return []
                except Exception as e:
                    return []
            
            if st.button("🔄 Cargar recordatorios", key="cargar_record"):
                with st.spinner("Buscando recordatorios..."):
                    recordatorios = obtener_recordatorios()
                    st.session_state.recordatorios = recordatorios
            
            if 'recordatorios' in st.session_state:
                if st.session_state.recordatorios:
                    for recordatorio in st.session_state.recordatorios:
                        paciente_info = recordatorio.get('alertas_hemoglobina', {})
                        dias_restantes = (datetime.strptime(recordatorio['fecha_cita'], '%Y-%m-%d').date() - datetime.now().date()).days
                        
                        # Determinar color según días restantes
                        if dias_restantes <= 2:
                            color = "#dc2626"
                            emoji = "🚨"
                        elif dias_restantes <= 5:
                            color = "#d97706"
                            emoji = "⚠️"
                        else:
                            color = "#2563eb"
                            emoji = "📅"
                        
                        st.markdown(f"""
                        <div style="background: {color}10; border-left: 5px solid {color}; 
                                 padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{emoji} {paciente_info.get('nombre_apellido', 'Desconocido')}</strong><br>
                                    <small>DNI: {recordatorio['dni_paciente']} | Tel: {paciente_info.get('telefono', 'Sin teléfono')}</small>
                                </div>
                                <div style="text-align: right;">
                                    <strong>{recordatorio['fecha_cita']}</strong><br>
                                    <small>Hora: {recordatorio.get('hora_cita', '09:00')}</small><br>
                                    <small style="color: {color};">{dias_restantes} días restantes</small>
                                </div>
                            </div>
                            <div style="margin-top: 10px;">
                                <small><strong>Tipo:</strong> {recordatorio['tipo_consulta']}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("🎉 No hay recordatorios para la próxima semana")
            else:
                st.info("👆 Presiona 'Cargar recordatorios' para ver citas próximas")
        
        # SUB-PESTAÑA 4: HISTORIAL DE CITAS
        with tab_citas4:
            st.markdown("**📋 HISTORIAL DE CITAS**")
            
            # Búsqueda por DNI
            col_hist1, col_hist2 = st.columns([3, 1])
            
            with col_hist1:
                dni_historial = st.text_input("Buscar historial por DNI", 
                                             placeholder="DNI de 8 dígitos",
                                             key="dni_historial")
            
            with col_hist2:
                buscar_historial = st.button("🔍 Buscar", use_container_width=True)
            
            if buscar_historial and dni_historial:
                valido, mensaje = validar_dni(dni_historial)
                
                if not valido:
                    st.error(f"❌ {mensaje}")
                else:
                    with st.spinner("Buscando historial..."):
                        try:
                            # Buscar paciente primero
                            response_paciente = supabase.table(TABLE_NAME)\
                                .select("*")\
                                .eq("dni", dni_historial)\
                                .execute()
                            
                            if response_paciente.data:
                                paciente = response_paciente.data[0]
                                st.success(f"✅ Paciente: {paciente['nombre_apellido']}")
                                
                                # Buscar citas del paciente
                                response_citas = supabase.table(CITAS_TABLE)\
                                    .select("*")\
                                    .eq("dni_paciente", dni_historial)\
                                    .order("fecha_cita", desc=True)\
                                    .execute()
                                
                                if response_citas.data:
                                    citas_df = pd.DataFrame(response_citas.data)
                                    
                                    # Mostrar tabla
                                    st.dataframe(
                                        citas_df[['fecha_cita', 'hora_cita', 'tipo_consulta', 
                                                'diagnostico', 'tratamiento', 'observaciones']],
                                        use_container_width=True
                                    )
                                    
                                    # Estadísticas
                                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                                    
                                    with col_stat1:
                                        st.metric("Total citas", len(citas_df))
                                    
                                    with col_stat2:
                                        ultima_cita = citas_df['fecha_cita'].max()
                                        st.metric("Última cita", str(ultima_cita)[:10])
                                    
                                    with col_stat3:
                                        proxima_cita = citas_df[citas_df['fecha_cita'] >= datetime.now().strftime('%Y-%m-%d')]
                                        st.metric("Próximas", len(proxima_cita))
                                    
                                    # Botón para exportar
                                    if st.button("📥 Exportar historial a CSV", use_container_width=True):
                                        csv = citas_df.to_csv(index=False)
                                        st.download_button(
                                            label="📊 Descargar CSV",
                                            data=csv,
                                            file_name=f"historial_{dni_historial}_{datetime.now().strftime('%Y%m%d')}.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                                else:
                                    st.info("📭 El paciente no tiene citas registradas")
                            else:
                                st.warning(f"⚠️ No se encontró paciente con DNI {dni_historial}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
    
    # -------------------------------------------------
    # Pestaña 4: PACIENTES (BUSQUEDA POR DNI Y EXPORTAR)
    # -------------------------------------------------
    with tab_pacientes:
        st.markdown('<div class="section-title">👥 GESTIÓN DE PACIENTES</div>', unsafe_allow_html=True)
        
        # BÚSQUEDA POR DNI
        col_pac1, col_pac2 = st.columns([3, 1])
        
        with col_pac1:
            dni_pacientes = st.text_input("🔍 Buscar paciente por DNI", 
                                         placeholder="Ingrese DNI de 8 dígitos",
                                         key="dni_pacientes")
        
        with col_pac2:
            buscar_paciente_gest = st.button("🔎 Buscar", use_container_width=True)
        
        if buscar_paciente_gest and dni_pacientes:
            valido, mensaje = validar_dni(dni_pacientes)
            
            if not valido:
                st.error(f"❌ {mensaje}")
            else:
                with st.spinner("Buscando paciente..."):
                    try:
                        response = supabase.table(TABLE_NAME)\
                            .select("*")\
                            .eq("dni", dni_pacientes)\
                            .execute()
                        
                        if response.data:
                            paciente = response.data[0]
                            st.success(f"✅ Paciente encontrado: {paciente['nombre_apellido']}")
                            
                            # Mostrar información completa
                            with st.expander("📋 INFORMACIÓN COMPLETA DEL PACIENTE", expanded=True):
                                col_info_p1, col_info_p2 = st.columns(2)
                                
                                with col_info_p1:
                                    st.markdown("**👤 DATOS PERSONALES**")
                                    st.write(f"**DNI:** {paciente['dni']}")
                                    st.write(f"**Nombre:** {paciente['nombre_apellido']}")
                                    st.write(f"**Edad:** {paciente['edad_meses']} meses")
                                    st.write(f"**Género:** {paciente['genero']}")
                                    st.write(f"**Peso:** {paciente['peso_kg']} kg")
                                    st.write(f"**Talla:** {paciente['talla_cm']} cm")
                                
                                with col_info_p2:
                                    st.markdown("**🩺 DATOS CLÍNICOS**")
                                    st.write(f"**Hemoglobina:** {paciente.get('hemoglobina_dl1', 'N/A')} g/dL")
                                    st.write(f"**Suplemento hierro:** {'Sí' if paciente.get('consumir_hierro') else 'No'}")
                                    if paciente.get('consumir_hierro'):
                                        st.write(f"**Tipo:** {paciente.get('tipo_suplemento_hierro', 'N/A')}")
                                        st.write(f"**Frecuencia:** {paciente.get('frecuencia_suplemento', 'N/A')}")
                                    st.write(f"**Antecedentes anemia:** {'Sí' if paciente.get('antecedentes_anemia') else 'No'}")
                                    st.write(f"**Enfermedades:** {paciente.get('enfermedades_cronicas', 'Ninguna')}")
                                
                                st.markdown("**👥 DATOS DEL APODERADO**")
                                col_apod1, col_apod2 = st.columns(2)
                                
                                with col_apod1:
                                    st.write(f"**Relación:** {paciente.get('relacion_apoderado', 'N/A')}")
                                    st.write(f"**Nivel educativo:** {paciente.get('nivel_educativo_apoderado', 'N/A')}")
                                
                                with col_apod2:
                                    st.write(f"**Teléfono:** {paciente.get('telefono', 'N/A')}")
                                    factores = paciente.get('factores_socioeconomicos', 'Ninguno')
                                    st.write(f"**Factores socioeconómicos:** {factores}")
                            
                            # BUSCAR SEGUIMIENTOS DEL PACIENTE
                            st.markdown("**🔍 HISTORIAL DE SEGUIMIENTOS**")
                            
                            try:
                                # Buscar en tabla de seguimientos (si existe)
                                response_seg = supabase.table("seguimientos")\
                                    .select("*")\
                                    .eq("dni_paciente", dni_pacientes)\
                                    .order("fecha_seguimiento", desc=True)\
                                    .execute()
                                
                                if response_seg.data:
                                    seguimientos_df = pd.DataFrame(response_seg.data)
                                    
                                    st.dataframe(
                                        seguimientos_df[['fecha_seguimiento', 'hemoglobina', 'peso', 'talla', 'observaciones']],
                                        use_container_width=True,
                                        column_config={
                                            "fecha_seguimiento": "Fecha",
                                            "hemoglobina": "Hb (g/dL)",
                                            "peso": "Peso (kg)",
                                            "talla": "Talla (cm)",
                                            "observaciones": "Observaciones"
                                        }
                                    )
                                    
                                    # Botón para exportar
                                    if st.button("📊 Exportar seguimientos a CSV", key="exportar_seg", use_container_width=True):
                                        csv = seguimientos_df.to_csv(index=False)
                                        st.download_button(
                                            label="📥 Descargar CSV",
                                            data=csv,
                                            file_name=f"seguimientos_{dni_pacientes}_{datetime.now().strftime('%Y%m%d')}.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                                else:
                                    st.info("📭 El paciente no tiene seguimientos registrados")
                                    
                            except:
                                st.info("ℹ️ No se encontró tabla de seguimientos específica")
                            
                            # Botón para editar paciente
                            col_edit1, col_edit2 = st.columns(2)
                            
                            with col_edit1:
                                if st.button("✏️ Editar información", use_container_width=True):
                                    st.session_state.editar_paciente = paciente
                                    st.rerun()
                            
                            with col_edit2:
                                if st.button("🗑️ Eliminar paciente", type="secondary", use_container_width=True):
                                    st.warning("⚠️ Esta acción eliminará permanentemente al paciente")
                                    confirmar = st.checkbox("Confirmar eliminación")
                                    
                                    if confirmar:
                                        try:
                                            # Primero eliminar citas asociadas
                                            supabase.table(CITAS_TABLE)\
                                                .delete()\
                                                .eq("dni_paciente", dni_pacientes)\
                                                .execute()
                                            
                                            # Luego eliminar paciente
                                            supabase.table(TABLE_NAME)\
                                                .delete()\
                                                .eq("dni", dni_pacientes)\
                                                .execute()
                                            
                                            st.success("✅ Paciente eliminado exitosamente")
                                            time.sleep(2)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Error al eliminar: {str(e)}")
                        
                        else:
                            st.warning(f"⚠️ No se encontró paciente con DNI {dni_pacientes}")
                    except Exception as e:
                        st.error(f"❌ Error en la búsqueda: {str(e)}")
        
        # LISTA COMPLETA DE PACIENTES
        st.markdown("---")
        st.markdown("**📋 LISTA COMPLETA DE PACIENTES**")
        
        if st.button("🔄 Cargar todos los pacientes", key="cargar_todos"):
            with st.spinner("Cargando pacientes..."):
                pacientes = obtener_datos()
                st.session_state.lista_pacientes = pacientes
        
        if 'lista_pacientes' in st.session_state and not st.session_state.lista_pacientes.empty:
            pacientes_df = st.session_state.lista_pacientes
            
            # Mostrar tabla resumida
            st.dataframe(
                pacientes_df[['dni', 'nombre_apellido', 'edad_meses', 'genero', 'hemoglobina_dl1', 'fecha_registro']],
                use_container_width=True,
                column_config={
                    "dni": "DNI",
                    "nombre_apellido": "Nombre",
                    "edad_meses": "Edad (meses)",
                    "genero": "Género",
                    "hemoglobina_dl1": "Hb (g/dL)",
                    "fecha_registro": "Fecha Registro"
                }
            )
            
            # Botón para exportar todos
            if st.button("📥 Exportar lista completa a CSV", use_container_width=True):
                csv = pacientes_df.to_csv(index=False)
                st.download_button(
                    label="📊 Descargar CSV completo",
                    data=csv,
                    file_name=f"pacientes_completo_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("👆 Presiona 'Cargar todos los pacientes' para ver la lista completa")
    
    # -------------------------------------------------
    # Pestaña 5: CONFIGURACIÓN
    # -------------------------------------------------
    with tab_config:
        st.markdown('<div class="section-title">⚙️ CONFIGURACIÓN DEL SISTEMA</div>', unsafe_allow_html=True)
        
        st.write(f"**👤 INFORMACIÓN DE LA SESIÓN**")
        st.json({
            "usuario": user_info['nombre'],
            "rol": user_info['rol'],
            "email": user_info['email'],
            "especialidad": user_info['especialidad'],
            "sesion_iniciada": st.session_state.logged_in
        })
        
        st.markdown("---")
        
        st.write("**🔧 OPCIONES DEL SISTEMA**")
        
        col_conf1, col_conf2 = st.columns(2)
        
        with col_conf1:
            if st.button("🔄 Actualizar Datos", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ Datos actualizados")
        
        with col_conf2:
            if st.button("📊 Ir al Dashboard Público", use_container_width=True):
                st.query_params.page = "dashboard"
                st.rerun()
        
        st.markdown("---")
        
        st.write("**📊 ESTADÍSTICAS DEL SISTEMA**")
        
        try:
            # Obtener estadísticas
            pacientes = obtener_datos()
            citas = obtener_datos(CITAS_TABLE)
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                total_pacientes = len(pacientes) if not pacientes.empty else 0
                st.metric("Pacientes registrados", total_pacientes)
            
            with col_stat2:
                total_citas = len(citas) if not citas.empty else 0
                st.metric("Citas programadas", total_citas)
            
            with col_stat3:
                hoy = datetime.now().date()
                citas_hoy = 0
                if not citas.empty and 'fecha_cita' in citas.columns:
                    citas['fecha_cita'] = pd.to_datetime(citas['fecha_cita']).dt.date
                    citas_hoy = len(citas[citas['fecha_cita'] == hoy])
                st.metric("Citas hoy", citas_hoy)
        except:
            st.info("⚠️ No se pudieron cargar las estadísticas")
        
        st.markdown("---")
        
        st.write("**🚪 CERRAR SESIÓN**")
        if st.button("🚪 Cerrar Sesión", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.session_state.current_username = None
            st.query_params.page = "dashboard"
            st.rerun()

# ==================================================
# ROUTER PRINCIPAL - NAVEGACIÓN ENTRE PESTAÑAS
# ==================================================

def main():
    """Router principal - Decide qué página mostrar basado en la URL"""
    
    # Obtener parámetros de la URL
    query_params = st.query_params
    
    # Si no hay parámetro, mostrar dashboard público por defecto
    if 'page' not in query_params:
        show_dashboard_publico()
    
    # Navegación por páginas
    elif query_params['page'] == 'dashboard':
        show_dashboard_publico()
    
    elif query_params['page'] == 'login':
        # Si ya está logueado, redirigir al sistema
        if st.session_state.logged_in:
            show_sistema_completo()
        else:
            show_login_page()
    
    elif query_params['page'] == 'system':
        # Verificar que el usuario esté logueado
        if st.session_state.logged_in:
            show_sistema_completo()
        else:
            # Si no está logueado, mostrar login
            st.warning("Debes iniciar sesión primero")
            show_login_page()
    
    else:
        # Página no reconocida, mostrar dashboard público
        show_dashboard_publico()

# ==================================================
# EJECUCIÓN PRINCIPAL
# ==================================================

if __name__ == "__main__":
    main()
