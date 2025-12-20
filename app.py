import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import time
from datetime import datetime, timedelta
import urllib.parse

# ==================================================
# CONFIGURACIÓN INICIAL
# ==================================================
st.set_page_config(
    page_title="Sistema Nixon - Control de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# DETECTAR PÁGINA ACTUAL DESDE URL
# ==================================================
query_params = st.query_params

# Obtener página actual de los parámetros de URL
current_page = query_params.get("page", ["dashboard"])[0]

# ==================================================
# SISTEMA DE LOGIN PARA 5 USUARIOS DE SALUD
# ==================================================

# Configurar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.current_username = None

# Diccionario de usuarios (5 profesionales de salud)
USUARIOS_SALUD = {
    "admin": {
        "password": "Admin123",
        "nombre": "Dr. Carlos Martínez",
        "rol": "Administrador",
        "especialidad": "Pediatría",
        "email": "admin@hospital.com",
        "acceso_total": True
    },
    "pediatra1": {
        "password": "Pediatra123",
        "nombre": "Dra. Ana López",
        "rol": "Pediatra",
        "especialidad": "Pediatría General",
        "email": "pediatra1@hospital.com",
        "acceso_total": True
    },
    "pediatra2": {
        "password": "Pediatra456",
        "nombre": "Dr. Juan Pérez",
        "rol": "Pediatra",
        "especialidad": "Nutrición Infantil",
        "email": "pediatra2@hospital.com",
        "acceso_total": True
    },
    "enfermero": {
        "password": "Enfermero123",
        "nombre": "Lic. María Gómez",
        "rol": "Enfermero/a",
        "especialidad": "Salud Pública",
        "email": "enfermero@hospital.com",
        "acceso_total": False
    },
    "tecnico": {
        "password": "Tecnico123",
        "nombre": "Téc. Luis Rodríguez",
        "rol": "Técnico de Laboratorio",
        "especialidad": "Hematología",
        "email": "tecnico@hospital.com",
        "acceso_total": False
    }
}

def verificar_login(username, password):
    """Verifica si el usuario y contraseña son correctos"""
    if username in USUARIOS_SALUD and USUARIOS_SALUD[username]["password"] == password:
        return USUARIOS_SALUD[username]
    return None

def logout():
    """Cierra sesión del usuario"""
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.session_state.current_username = None
    st.query_params.clear()
    st.rerun()

def show_login_page():
    """Muestra la página de login"""
    
    # Estilos CSS para el login
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 80px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(30, 64, 175, 0.1);
        border: 2px solid #e0f2fe;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .hospital-icon {
        font-size: 60px;
        margin-bottom: 20px;
        color: #1e40af;
    }
    
    .login-title {
        color: #1e3a8a;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .login-subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-top: 10px;
        font-weight: 500;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 16px;
        margin-top: 25px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(30, 64, 175, 0.3);
    }
    
    .user-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 12px 0;
        border-left: 5px solid #3b82f6;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
    }
    
    .user-card:hover {
        transform: translateX(5px);
        background: #f0f9ff;
        border-color: #dbeafe;
    }
    
    .test-users {
        margin-top: 30px;
        padding: 20px;
        background: #f0f9ff;
        border-radius: 12px;
        border: 2px solid #dbeafe;
    }
    
    .role-badge {
        background: #3b82f6;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-left: 10px;
        display: inline-block;
    }
    
    .form-label {
        color: #374151;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 8px;
        display: block;
    }
    
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 12px 16px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    .nav-button {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        color: #1e40af;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        text-align: center;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        background: #e0f2fe;
        border-color: #93c5fd;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor principal del login
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Header con icono
    st.markdown("""
    <div class="login-header">
        <div class="hospital-icon">🏥</div>
        <h1 class="login-title">SISTEMA NIXON</h1>
        <p class="login-subtitle">Control de Anemia y Nutrición Infantil</p>
        <div style="height: 3px; width: 80px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); margin: 20px auto; border-radius: 10px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login
    with st.form("login_form"):
        st.markdown('<div class="form-label">👤 Nombre de Usuario</div>', unsafe_allow_html=True)
        username = st.text_input("", placeholder="Ingresa tu usuario", label_visibility="collapsed")
        
        st.markdown('<div class="form-label">🔒 Contraseña</div>', unsafe_allow_html=True)
        password = st.text_input("", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            remember_me = st.checkbox("Recordar sesión", value=True)
        
        submit = st.form_submit_button("🚀 INICIAR SESIÓN", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("❌ Por favor, ingresa usuario y contraseña")
            else:
                usuario_info = verificar_login(username, password)
                if usuario_info:
                    st.session_state.logged_in = True
                    st.session_state.user_info = usuario_info
                    st.session_state.current_username = username
                    st.success(f"✅ ¡Bienvenido/a, {usuario_info['nombre']}!")
                    time.sleep(1)
                    st.query_params["page"] = "system"
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
    # Botón para ir al dashboard público
    st.markdown('<div style="text-align: center; margin-top: 20px;">', unsafe_allow_html=True)
    if st.button("📊 Ver Dashboard Público", use_container_width=True):
        st.query_params["page"] = "dashboard"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Información de usuarios de prueba
    with st.expander("👥 USUARIOS AUTORIZADOS DEL SISTEMA", expanded=True):
        st.markdown('<div class="test-users">', unsafe_allow_html=True)
        st.markdown("**Personal de Salud Autorizado:**")
        
        for username, info in USUARIOS_SALUD.items():
            role_class = info['rol'].lower().replace("á", "a").replace("é", "e")
            st.markdown(f"""
            <div class="user-card">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 1.1rem;">{info['nombre']}</strong>
                    <span class="role-badge">{info['rol']}</span>
                </div>
                <div style="font-size: 0.9rem; color: #4b5563;">
                    <div><strong>Especialidad:</strong> {info['especialidad']}</div>
                    <div><strong>Usuario:</strong> <code>{username}</code></div>
                    <div><strong>Contraseña:</strong> <code>{info['password']}</code></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer del login
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; color: #6b7280; font-size: 14px;">
        <p>© 2024 Sistema Nixon - Control de Anemia Infantil</p>
        <p>Sistema exclusivo para personal de salud autorizado</p>
        <div style="height: 1px; background: #e5e7eb; margin: 20px 0;"></div>
        <p style="font-size: 12px; margin-top: 20px;">
            <strong>🔒 Acceso restringido:</strong> Solo personal médico autorizado<br>
            <strong>📞 Soporte técnico:</strong> soporte@sistemasnixon.com
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# 1. DASHBOARD PÚBLICO (SIN LOGIN)
# ==================================================

def show_public_dashboard():
    """Muestra el dashboard público sin login"""
    
    # Estilos CSS para el dashboard público
    st.markdown("""
    <style>
    .public-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 3rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 15px 35px rgba(30, 64, 175, 0.2);
    }
    
    .public-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    
    .public-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 1.5rem;
    }
    
    .public-metric {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 2px solid #e0f2fe;
    }
    
    .public-metric-title {
        color: #1e40af;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    
    .public-metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e3a8a;
        margin: 10px 0;
    }
    
    .public-metric-desc {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 10px;
    }
    
    .access-button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 18px 30px;
        border-radius: 15px;
        font-weight: 700;
        font-size: 1.2rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        display: block;
        width: 100%;
        margin: 2rem 0;
    }
    
    .access-button:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(16, 185, 129, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown("""
    <div class="public-header">
        <h1 class="public-title">🏥 SISTEMA NACIONAL DE CONTROL DE ANEMIA</h1>
        <p class="public-subtitle">Monitoreo, prevención y tratamiento de anemia infantil en Perú</p>
        <div style="height: 4px; width: 150px; background: white; margin: 0 auto; border-radius: 10px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas nacionales (datos simulados/anónimos)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="public-metric">
            <div class="public-metric-title">Niños Evaluados</div>
            <div class="public-metric-value">15,243</div>
            <div class="public-metric-desc">A nivel nacional</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="public-metric">
            <div class="public-metric-title">Prevalencia Anemia</div>
            <div class="public-metric-value">28.5%</div>
            <div class="public-metric-desc">En menores de 5 años</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="public-metric">
            <div class="public-metric-title">Regiones Activas</div>
            <div class="public-metric-value">24</div>
            <div class="public-metric-desc">De 25 regiones</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="public-metric">
            <div class="public-metric-title">Hb Promedio</div>
            <div class="public-metric-value">10.3 g/dL</div>
            <div class="public-metric-desc">Ajustado por altitud</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Gráfico público (simulado)
    st.markdown("### 📊 Distribución por Región")
    
    # Datos simulados para gráfico
    regiones = ["Lima", "Piura", "Puno", "Cusco", "Loreto", "Arequipa", "La Libertad", "Junín"]
    prevalencias = [25.3, 32.1, 45.6, 38.2, 29.7, 22.4, 27.8, 34.5]
    
    fig = px.bar(
        x=regiones,
        y=prevalencias,
        title="Prevalencia de Anemia por Región (%)",
        color=prevalencias,
        color_continuous_scale="RdYlGn_r",
        labels={'x': 'Región', 'y': 'Prevalencia (%)'},
        height=400
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=12)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sección de acceso al sistema
    st.markdown("---")
    st.markdown("### 🔐 Acceso para Personal de Salud")
    
    col_acc1, col_acc2 = st.columns([2, 1])
    
    with col_acc1:
        st.markdown("""
        <div style="background: #f0f9ff; padding: 2rem; border-radius: 15px; border-left: 5px solid #3b82f6;">
            <h3 style="color: #1e40af; margin-top: 0;">Sistema Completo de Gestión</h3>
            <p style="color: #4b5563;">Accede al sistema completo con todas las funcionalidades:</p>
            <ul style="color: #4b5563;">
                <li>📝 Registro completo de pacientes</li>
                <li>🔍 Seguimiento clínico avanzado</li>
                <li>📅 Sistema de citas y recordatorios</li>
                <li>📊 Dashboard analítico</li>
                <li>⚙️ Configuración del sistema</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_acc2:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        if st.button("🏥 INGRESAR AL SISTEMA", use_container_width=True, type="primary"):
            st.query_params["page"] = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Información adicional
    st.markdown("---")
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        <div style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🎯</div>
            <h4>Objetivos 2024</h4>
            <p style="color: #6b7280;">Reducir la anemia infantil al 20% a nivel nacional</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown("""
        <div style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">📞</div>
            <h4>Contacto</h4>
            <p style="color: #6b7280;">Soporte técnico: soporte@minsa.gob.pe</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info3:
        st.markdown("""
        <div style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🔒</div>
            <h4>Seguridad</h4>
            <p style="color: #6b7280;">Datos anonimizados para estadísticas públicas</p>
        </div>
        """, unsafe_allow_html=True)

# ==================================================
# 2. PÁGINA DE LOGIN
# ==================================================

def show_login_page_only():
    """Muestra solo la página de login"""
    
    # Estilos CSS para el login
    st.markdown("""
    <style>
    .login-only-container {
        max-width: 500px;
        margin: 50px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 15px 35px rgba(30, 64, 175, 0.1);
        border: 2px solid #e0f2fe;
    }
    
    .back-button {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        color: #1e40af;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
        text-align: center;
        margin-bottom: 30px;
        transition: all 0.3s ease;
        display: inline-block;
    }
    
    .back-button:hover {
        background: #e0f2fe;
        border-color: #93c5fd;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Botón para volver al dashboard público
    if st.button("← Volver al Dashboard Público", key="back_to_dashboard"):
        st.query_params["page"] = "dashboard"
        st.rerun()
    
    st.markdown('<div class="login-only-container">', unsafe_allow_html=True)
    
    # Header con icono
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 60px; margin-bottom: 20px; color: #1e40af;">🏥</div>
        <h1 style="color: #1e3a8a; font-size: 2.2rem; font-weight: 800; margin: 0;">
        ACCESO AL SISTEMA
        </h1>
        <p style="color: #6b7280; font-size: 1rem; margin-top: 10px;">
        Ingresa tus credenciales para acceder al sistema completo
        </p>
        <div style="height: 3px; width: 80px; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); margin: 20px auto; border-radius: 10px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de login (mismo que antes)
    with st.form("login_form_page"):
        username = st.text_input("👤 Nombre de Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        submit = st.form_submit_button("🚀 INICIAR SESIÓN", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("❌ Por favor, ingresa usuario y contraseña")
            else:
                usuario_info = verificar_login(username, password)
                if usuario_info:
                    st.session_state.logged_in = True
                    st.session_state.user_info = usuario_info
                    st.session_state.current_username = username
                    st.success(f"✅ ¡Bienvenido/a, {usuario_info['nombre']}!")
                    time.sleep(1)
                    st.query_params["page"] = "system"
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
    # Información de usuarios de prueba
    with st.expander("👥 USUARIOS DE PRUEBA", expanded=True):
        st.markdown("""
        **Personal de Salud Autorizado:**
        
        **Dr. Carlos Martínez** (Administrador)
        - Usuario: `admin`
        - Contraseña: `Admin123`
        
        **Dra. Ana López** (Pediatra)
        - Usuario: `pediatra1`
        - Contraseña: `Pediatra123`
        
        **Dr. Juan Pérez** (Pediatra)
        - Usuario: `pediatra2`
        - Contraseña: `Pediatra456`
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# 3. SISTEMA COMPLETO (REQUIERE LOGIN)
# ==================================================

# Configuración Supabase (solo se inicializa si se necesita)
@st.cache_resource
def init_supabase():
    """Inicializa la conexión a Supabase"""
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw")
        
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase_client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None

def show_system_page():
    """Muestra el sistema completo (requiere login)"""
    
    # Verificar si el usuario está logueado
    if not st.session_state.logged_in:
        st.warning("🔐 Debes iniciar sesión para acceder al sistema")
        if st.button("Ir a la página de login"):
            st.query_params["page"] = "login"
            st.rerun()
        return
    
    # Obtener información del usuario
    user_info = st.session_state.user_info
    
    # Inicializar Supabase
    supabase = init_supabase()
    
    # ==================================================
    # ESTILOS CSS PARA EL SISTEMA COMPLETO
    # ==================================================
    st.markdown("""
    <style>
    .main-title {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(30, 58, 138, 0.2);
    }
    
    .user-sidebar-info {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        text-align: center;
        border: 2px solid rgba(255,255,255,0.1);
    }
    
    .user-name {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .user-role {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 15px;
        background: rgba(255,255,255,0.15);
        padding: 4px 12px;
        border-radius: 15px;
        display: inline-block;
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
    
    .metric-card-blue {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin: 0.5rem 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    
    .highlight-number {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .highlight-blue { color: #1e40af; }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .search-container {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        margin-bottom: 2rem;
    }
    
    .patient-result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .patient-result-card:hover {
        border-color: #93c5fd;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal con información del usuario
    st.markdown(f"""
    <div class="main-title">
        <h1 style="margin: 0; font-size: 2.5rem;">🏥 SISTEMA NIXON - Control de Anemia</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Usuario: <strong>{user_info['nombre']}</strong> | Rol: <strong>{user_info['rol']}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown(f"""
        <div class="user-sidebar-info">
            <div class="user-name">👤 {user_info['nombre']}</div>
            <div class="user-role">{user_info['rol']}</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 5px;">
                {user_info['email']}<br>
                <small>Especialidad: {user_info['especialidad']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            logout()
        
        st.markdown("---")
        
        # Navegación entre pestañas del sistema
        st.markdown("### 📂 Navegación del Sistema")
        
        nav_options = {
            "📝 Registro Completo": "registro",
            "🔍 Seguimiento Clínico": "seguimiento",
            "📋 Sistema de Citas": "citas",
            "⚙️ Configuración": "configuracion"
        }
        
        for option, key in nav_options.items():
            if st.button(option, use_container_width=True, key=f"nav_{key}"):
                st.session_state.current_tab = key
                st.rerun()
        
        # Botón para volver al dashboard público
        if st.button("📊 Volver al Dashboard Público", use_container_width=True):
            st.query_params["page"] = "dashboard"
            st.rerun()
    
    # Inicializar pestaña actual
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "registro"
    
    # ==================================================
    # PESTAÑA 1: REGISTRO COMPLETO
    # ==================================================
    if st.session_state.current_tab == "registro":
        st.markdown('<div class="section-title-blue">📝 Registro Completo de Paciente</div>', unsafe_allow_html=True)
        
        # Aquí iría el formulario de registro completo
        with st.form("form_registro"):
            col1, col2 = st.columns(2)
            
            with col1:
                dni = st.text_input("DNI del Paciente", placeholder="Ej: 87654321")
                nombre = st.text_input("Nombre Completo", placeholder="Ej: Ana García Pérez")
                edad = st.number_input("Edad (meses)", 0, 240, 24)
            
            with col2:
                hemoglobina = st.number_input("Hemoglobina (g/dL)", 5.0, 20.0, 11.0, 0.1)
                peso = st.number_input("Peso (kg)", 0.0, 50.0, 12.5, 0.1)
                talla = st.number_input("Talla (cm)", 0.0, 150.0, 85.0, 0.1)
            
            if st.form_submit_button("💾 Guardar Registro", use_container_width=True):
                if dni and nombre:
                    st.success(f"✅ Paciente {nombre} registrado correctamente")
                else:
                    st.error("❌ Complete los campos obligatorios")
    
    # ==================================================
    # PESTAÑA 2: SEGUIMIENTO CLÍNICO (CON BÚSQUEDA POR DNI)
    # ==================================================
    elif st.session_state.current_tab == "seguimiento":
        st.markdown('<div class="section-title-blue">🔍 Seguimiento Clínico - Búsqueda por DNI</div>', unsafe_allow_html=True)
        
        # Contenedor de búsqueda
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        st.markdown("### 🔎 Buscar Paciente por DNI")
        
        col_search1, col_search2 = st.columns([3, 1])
        
        with col_search1:
            dni_busqueda = st.text_input("Ingrese DNI del paciente", placeholder="Ej: 87654321", key="dni_busqueda")
        
        with col_search2:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar = st.button("🔍 Buscar", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resultados de búsqueda
        if buscar and dni_busqueda:
            if supabase:
                try:
                    with st.spinner("Buscando paciente..."):
                        # Buscar en Supabase
                        response = supabase.table("alertas_hemoglobina")\
                            .select("*")\
                            .eq("dni", dni_busqueda)\
                            .execute()
                        
                        if response.data:
                            paciente = response.data[0]
                            
                            # Mostrar información del paciente
                            st.markdown(f"""
                            <div class="patient-result-card">
                                <h3 style="color: #1e40af; margin-top: 0;">👤 {paciente['nombre_apellido']}</h3>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0;">
                                    <div>
                                        <strong>DNI:</strong> {paciente['dni']}<br>
                                        <strong>Edad:</strong> {paciente['edad_meses']} meses<br>
                                        <strong>Género:</strong> {paciente['genero']}
                                    </div>
                                    <div>
                                        <strong>Hemoglobina:</strong> {paciente['hemoglobina_dl1']} g/dL<br>
                                        <strong>Riesgo:</strong> {paciente.get('riesgo', 'No evaluado')}<br>
                                        <strong>Estado:</strong> {paciente.get('estado_paciente', 'Activo')}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Formulario para seguimiento
                            with st.expander("📝 Registrar Nuevo Seguimiento", expanded=True):
                                with st.form("form_seguimiento"):
                                    fecha_control = st.date_input("Fecha de control", datetime.now())
                                    hemoglobina_control = st.number_input("Hemoglobina actual (g/dL)", 
                                                                        5.0, 20.0, float(paciente['hemoglobina_dl1']), 0.1)
                                    observaciones = st.text_area("Observaciones del control")
                                    
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        if st.form_submit_button("💾 Guardar Seguimiento", use_container_width=True):
                                            st.success("✅ Seguimiento registrado correctamente")
                                    
                                    with col_btn2:
                                        if st.form_submit_button("📅 Programar Próximo Control", use_container_width=True):
                                            st.success("✅ Próximo control programado")
                            
                            # Historial de controles (simulado)
                            st.markdown("### 📋 Historial de Controles")
                            historial_data = {
                                "Fecha": ["2024-01-15", "2024-02-20", "2024-03-25"],
                                "Hemoglobina": [10.5, 11.0, 11.5],
                                "Observaciones": ["Inicio tratamiento", "Mejoría", "Control normal"]
                            }
                            historial_df = pd.DataFrame(historial_data)
                            st.dataframe(historial_df, use_container_width=True)
                            
                        else:
                            st.warning(f"⚠️ No se encontró paciente con DNI: {dni_busqueda}")
                            st.info("¿Desea registrar un nuevo paciente?")
                            if st.button("➕ Registrar Nuevo Paciente"):
                                st.session_state.current_tab = "registro"
                                st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Error en la búsqueda: {str(e)}")
            else:
                st.error("🔴 No hay conexión a la base de datos")
        
        elif buscar and not dni_busqueda:
            st.warning("⚠️ Ingrese un DNI para buscar")
    
    # ==================================================
    # PESTAÑA 3: SISTEMA DE CITAS
    # ==================================================
    elif st.session_state.current_tab == "citas":
        st.markdown('<div class="section-title-blue">📋 Sistema de Citas</div>', unsafe_allow_html=True)
        
        # Crear pestañas para citas
        tab_citas1, tab_citas2, tab_citas3 = st.tabs(["📅 Programar Cita", "📋 Citas Programadas", "🔔 Recordatorios"])
        
        with tab_citas1:
            st.markdown("### 🗓️ Programar Nueva Cita")
            
            with st.form("form_cita"):
                # Buscar paciente
                if supabase:
                    response = supabase.table("alertas_hemoglobina").select("dni, nombre_apellido").limit(50).execute()
                    pacientes = response.data if response.data else []
                    
                    if pacientes:
                        opciones = {f"{p['nombre_apellido']} (DNI: {p['dni']})": p['dni'] for p in pacientes}
                        paciente_sel = st.selectbox("Seleccionar paciente", list(opciones.keys()))
                        dni_paciente = opciones[paciente_sel]
                    else:
                        st.info("No hay pacientes registrados")
                        dni_paciente = ""
                
                col_fecha, col_hora = st.columns(2)
                with col_fecha:
                    fecha_cita = st.date_input("Fecha de la cita", min_value=datetime.now())
                with col_hora:
                    hora_cita = st.time_input("Hora de la cita", value=datetime.now().time())
                
                tipo_cita = st.selectbox("Tipo de consulta", 
                                        ["Control rutinario", "Seguimiento anemia", "Urgencia", "Reevaluación"])
                
                if st.form_submit_button("💾 Programar Cita", use_container_width=True):
                    st.success(f"✅ Cita programada para el {fecha_cita} a las {hora_cita}")
        
        with tab_citas2:
            st.markdown("### 📋 Citas Programadas")
            
            # Datos simulados
            citas_data = {
                "Fecha": ["2024-12-15", "2024-12-16", "2024-12-17"],
                "Hora": ["09:00", "10:30", "14:00"],
                "Paciente": ["Ana García Pérez", "Carlos López Díaz", "María Rodríguez"],
                "Tipo": ["Control", "Seguimiento", "Urgencia"],
                "Estado": ["Confirmada", "Pendiente", "Confirmada"]
            }
            citas_df = pd.DataFrame(citas_data)
            st.dataframe(citas_df, use_container_width=True)
        
        with tab_citas3:
            st.markdown("### 🔔 Recordatorios de Citas")
            st.info("Próximas citas en los próximos 7 días")
            
            # Datos simulados
            recordatorios_data = {
                "Días": ["Hoy", "Mañana", "En 3 días"],
                "Paciente": ["Juan Pérez", "Ana López", "Carlos Martínez"],
                "Hora": ["10:00", "11:30", "09:00"],
                "Acción": ["✅ Confirmada", "🔄 Por confirmar", "📞 Llamar"]
            }
            recordatorios_df = pd.DataFrame(recordatorios_data)
            st.dataframe(recordatorios_df, use_container_width=True)
    
    # ==================================================
    # PESTAÑA 4: CONFIGURACIÓN
    # ==================================================
    elif st.session_state.current_tab == "configuracion":
        st.markdown('<div class="section-title-blue">⚙️ Configuración del Sistema</div>', unsafe_allow_html=True)
        
        # Información del sistema
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label">USUARIO ACTUAL</div>
                <div class="highlight-number highlight-blue">{user_info['nombre'].split()[0]}</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                Rol: {user_info['rol']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info2:
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label">VERSIÓN</div>
                <div class="highlight-number highlight-blue">3.0</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                Sistema Nixon
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info3:
            conexion = "✅ Conectado" if supabase else "🔴 Desconectado"
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label">BASE DE DATOS</div>
                <div class="highlight-number highlight-blue">{conexion}</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                Supabase
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Configuraciones adicionales
        st.markdown("### 🔧 Opciones de Configuración")
        
        with st.expander("📊 Parámetros del Sistema"):
            st.checkbox("Mostrar datos de prueba", value=True)
            st.checkbox("Notificaciones por email", value=False)
            st.checkbox("Recordatorios automáticos", value=True)
        
        with st.expander("👥 Gestión de Usuarios"):
            st.info("Solo visible para administradores")
            if user_info['rol'] == 'Administrador':
                st.button("➕ Agregar Usuario", use_container_width=True)
                st.button("✏️ Editar Usuarios", use_container_width=True)
            else:
                st.warning("⚠️ Solo los administradores pueden gestionar usuarios")
        
        with st.expander("📤 Exportar Datos"):
            st.button("📊 Exportar a Excel", use_container_width=True)
            st.button("📋 Generar Reporte PDF", use_container_width=True)

# ==================================================
# ROUTER PRINCIPAL
# ==================================================

def main():
    """Router principal de la aplicación"""
    
    # Verificar si estamos en la página de login o dashboard público
    if current_page == "dashboard":
        show_public_dashboard()
    
    elif current_page == "login":
        show_login_page_only()
    
    elif current_page == "system":
        # Verificar si el usuario está logueado
        if not st.session_state.logged_in:
            st.warning("🔐 Debes iniciar sesión para acceder al sistema")
            if st.button("Ir a la página de login"):
                st.query_params["page"] = "login"
                st.rerun()
        else:
            show_system_page()
    
    else:
        # Página por defecto: dashboard público
        show_public_dashboard()

# ==================================================
# EJECUTAR LA APLICACIÓN
# ==================================================

if __name__ == "__main__":
    main()
