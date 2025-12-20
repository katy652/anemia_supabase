import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv  # Para manejar variables de entorno

# Cargar variables de entorno
load_dotenv()

# ==================================================
# CONFIGURACIÓN SUPABASE - CON VARIABLES DE ENTORNO
# ==================================================

# Obtener credenciales de entorno (más seguro que hardcode)
SUPABASE_URL = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co"))
SUPABASE_KEY = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw"))

# Configuración de tablas
TABLE_NAME = "alertas_hemoglobina"
ALTITUD_TABLE = "altitud_regiones"
CRECIMIENTO_TABLE = "referencia_crecimiento"
CITAS_TABLE = "citas"  # Tabla para citas

# ==================================================
# INICIALIZACIÓN DE SUPABASE
# ==================================================

@st.cache_resource
def init_supabase():
    """Inicializa la conexión con Supabase"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("❌ Faltan credenciales de Supabase. Configura SUPABASE_URL y SUPABASE_KEY en tus variables de entorno.")
            return None
        
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Verificar conexión
        try:
            test = supabase_client.table(TABLE_NAME).select("*").limit(1).execute()
            st.success("✅ Conexión a Supabase establecida correctamente")
        except Exception as e:
            st.warning(f"⚠️ Puede que la tabla '{TABLE_NAME}' no exista todavía: {str(e)}")
        
        return supabase_client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)}")
        return None

# Inicializar Supabase
supabase = init_supabase()

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
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
    
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
# VERIFICAR SI EL USUARIO ESTÁ LOGUEADO
# ==================================================

if not st.session_state.logged_in:
    show_login_page()
    st.stop()  # Detener la ejecución del resto del código

# ==================================================
# CONFIGURACIÓN E INICIALIZACIÓN (solo se ejecuta si está logueado)
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
    
    /* INFO USUARIO EN SIDEBAR */
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
    
    .user-email {
        font-size: 0.8rem;
        opacity: 0.8;
        margin-top: 5px;
    }
    
    .logout-btn {
        background: rgba(255,255,255,0.2) !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        color: white !important;
        margin-top: 10px !important;
    }
    
    .logout-btn:hover {
        background: rgba(255,255,255,0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Resto de estilos... */
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
</style>
""", unsafe_allow_html=True)

# ==================================================
# OBTENER INFORMACIÓN DEL USUARIO LOGUEADO
# ==================================================

user_info = st.session_state.user_info
current_user = st.session_state.current_username

# ==================================================
# SIDEBAR CON INFORMACIÓN DEL USUARIO
# ==================================================

with st.sidebar:
    # Información del usuario
    st.markdown(f"""
    <div class="user-sidebar-info">
        <div class="user-name">👤 {user_info['nombre']}</div>
        <div class="user-role">{user_info['rol']}</div>
        <div class="user-email">
            {user_info['email']}<br>
            <small>Especialidad: {user_info['especialidad']}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón de logout
    if st.button("🚪 Cerrar Sesión", use_container_width=True, key="logout_btn", 
                type="secondary", help="Cierra la sesión actual"):
        logout()
    
    st.markdown("---")
    
    # Resto del sidebar original
    st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">📋 Sistema de Referencia</div>', unsafe_allow_html=True)
    
    tab_sidebar1, tab_sidebar2, tab_sidebar3 = st.tabs(["🎯 Ajustes Altitud", "📊 Crecimiento", "🔬 Hematología"])
    
    with tab_sidebar1:
        st.markdown('<div style="color: #1e40af; font-weight: 600; margin-bottom: 10px;">Tabla de Ajustes por Altitud</div>', unsafe_allow_html=True)
        
        # Tabla de ajustes por altitud
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
        
        # Función para obtener referencia de crecimiento
        def obtener_referencia_crecimiento():
            return pd.DataFrame([
                {'edad_meses': 0, 'peso_min_ninas': 2.8, 'peso_promedio_ninas': 3.4, 'peso_max_ninas': 4.2, 'peso_min_ninos': 2.9, 'peso_promedio_ninos': 3.4, 'peso_max_ninos': 4.4, 'talla_min_ninas': 47.0, 'talla_promedio_ninas': 50.3, 'talla_max_ninas': 53.6, 'talla_min_ninos': 47.5, 'talla_promedio_ninos': 50.3, 'talla_max_ninos': 53.8},
                {'edad_meses': 3, 'peso_min_ninas': 4.5, 'peso_promedio_ninas': 5.6, 'peso_max_ninas': 7.0, 'peso_min_ninos': 5.0, 'peso_promedio_ninos': 6.2, 'peso_max_ninos': 7.8, 'talla_min_ninas': 55.0, 'talla_promedio_ninas': 59.0, 'talla_max_ninas': 63.5, 'talla_min_ninos': 57.0, 'talla_promedio_ninos': 60.0, 'talla_max_ninos': 64.5},
                {'edad_meses': 6, 'peso_min_ninas': 6.0, 'peso_promedio_ninas': 7.3, 'peso_max_ninas': 9.0, 'peso_min_ninos': 6.5, 'peso_promedio_ninos': 8.0, 'peso_max_ninos': 9.8, 'talla_min_ninas': 61.0, 'talla_promedio_ninas': 65.0, 'talla_max_ninas': 69.5, 'talla_min_ninos': 63.0, 'talla_promedio_ninos': 67.0, 'talla_max_ninos': 71.5},
                {'edad_meses': 24, 'peso_min_ninas': 10.5, 'peso_promedio_ninas': 12.4, 'peso_max_ninas': 15.0, 'peso_min_ninos': 11.0, 'peso_promedio_ninos': 12.9, 'peso_max_ninos': 16.0, 'talla_min_ninas': 81.0, 'talla_promedio_ninas': 86.0, 'talla_max_ninas': 92.5, 'talla_min_ninos': 83.0, 'talla_promedio_ninos': 88.0, 'talla_max_ninos': 94.5}
            ])
        
        referencia_df = obtener_referencia_crecimiento()
        st.dataframe(referencia_df, use_container_width=True, height=300)
    
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

# ==================================================
# TÍTULO PRINCIPAL CON INFORMACIÓN DEL USUARIO
# ==================================================

st.markdown(f"""
<div class="main-title" style="padding: 2rem;">
    <h1 style="margin: 0; font-size: 2.5rem;">🏥 SISTEMA NIXON - Control de Anemia</h1>
    <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
    Usuario: <strong>{user_info['nombre']}</strong> | Rol: <strong>{user_info['rol']}</strong> | Especialidad: <strong>{user_info['especialidad']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# ==================================================
# FUNCIONES PARA LA BASE DE DATOS SUPABASE
# ==================================================

def obtener_datos_supabase(tabla=TABLE_NAME):
    """Obtiene datos de Supabase"""
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

# ==================================================
# TABLAS DE REFERENCIA Y FUNCIONES DE CÁLCULO
# ==================================================

def obtener_altitud_regiones():
    """Obtiene datos de altitud de regiones"""
    try:
        if supabase:
            response = supabase.table(ALTITUD_TABLE).select("*").execute()
            if response.data:
                return {row['region']: row for row in response.data}
        return {
            "LIMA": {"altitud_min": 0, "altitud_max": 4800, "altitud_promedio": 150},
            "AREQUIPA": {"altitud_min": 0, "altitud_max": 5825, "altitud_promedio": 2500},
            "CUSCO": {"altitud_min": 500, "altitud_max": 4800, "altitud_promedio": 3400},
            "PUNO": {"altitud_min": 3800, "altitud_max": 4800, "altitud_promedio": 4100},
            "JUNIN": {"altitud_min": 500, "altitud_max": 4800, "altitud_promedio": 3500}
        }
    except:
        return {}

ALTITUD_REGIONES = obtener_altitud_regiones()

def obtener_ajuste_hemoglobina(altitud):
    """Obtiene ajuste de hemoglobina según altitud"""
    for ajuste in AJUSTE_HEMOGLOBINA:
        if ajuste["altitud_min"] <= altitud <= ajuste["altitud_max"]:
            return ajuste["ajuste"]
    return 0.0

def calcular_hemoglobina_ajustada(hemoglobina_medida, altitud):
    """Calcula hemoglobina ajustada por altitud"""
    ajuste = obtener_ajuste_hemoglobina(altitud)
    return hemoglobina_medida + ajuste

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

# ==================================================
# FUNCIONES DE EVALUACIÓN NUTRICIONAL
# ==================================================

def evaluar_estado_nutricional(edad_meses, peso_kg, talla_cm, genero):
    """Evalúa el estado nutricional basado en tablas de referencia OMS"""
    
    # Datos de referencia simplificados
    referencia_df = obtener_referencia_crecimiento()
    
    if referencia_df.empty:
        return "Sin datos referencia", "Sin datos referencia", "NUTRICIÓN NO EVALUADA"
    
    referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_meses]
    
    if referencia_edad.empty:
        # Interpolación simple si no hay datos exactos
        if edad_meses < 3:
            ref = referencia_df.iloc[0]
        elif edad_meses < 6:
            ref = referencia_df.iloc[1]
        elif edad_meses < 24:
            ref = referencia_df.iloc[2]
        else:
            ref = referencia_df.iloc[3]
    else:
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
# INTERFAZ PRINCIPAL - PESTAÑAS
# ==================================================

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
            
            # Mostrar clasificación con estilo
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
            
            # Métrica con estilo
            st.markdown(f"""
            <div class="metric-card-blue">
                <div class="metric-label" style="color: #1e40af;">HEMOGLOBINA AJUSTADA</div>
                <div class="highlight-number" style="color: #1d4ed8; font-size: 2rem;">{hemoglobina_ajustada:.1f} g/dL</div>
                <div style="font-size: 0.9rem; color: #4b5563;">
                Ajuste por altitud: {ajuste_hb:+.1f} g/dL
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            necesita_seguimiento = hemoglobina_ajustada < 11.0
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
            
            # Mostrar resultados
            st.markdown("---")
            st.markdown('<div class="section-title-green" style="color: #059669; font-size: 1.5rem;">📊 EVALUACIÓN INTEGRAL DEL PACIENTE</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            # ESTADO DE ANEMIA - IZQUIERDA
            with col1:
                st.markdown('<div class="section-title-blue" style="font-size: 1.2rem; color: #1e40af;">🩺 ESTADO DE ANEMIA</div>', unsafe_allow_html=True)

                # Clasificación OMS
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

                # NIVEL DE RIESGO
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
                    
                    # Mostrar evaluación nutricional
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
            
            # Contenedor para sugerencias
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
                        "politicas_de_ris": region,
                        "riesgo": nivel_riesgo,
                        "fecha_alerta": datetime.now().strftime("%Y-%m-%d"),
                        "estado_alerta": estado,
                        "sugerencias": sugerencias
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
# PESTAÑA 2: DASHBOARD NACIONAL
# ==================================================

with tab2:
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
    
    else:
        st.info("👆 Presiona el botón 'Cargar Datos Nacionales' para ver el dashboard nacional")

# ==================================================
# PESTAÑA 3: SISTEMA DE CITAS
# ==================================================

with tab3:
    st.markdown('<div class="section-title-blue">📋 Sistema de Citas y Seguimiento</div>', unsafe_allow_html=True)
    
    # Función para crear tabla de citas si no existe
    def crear_tabla_citas():
        """Crea la tabla de citas si no existe"""
        try:
            # Primero verificar si la tabla ya existe
            try:
                test = supabase.table(CITAS_TABLE).select("*").limit(1).execute()
                st.success("✅ Tabla 'citas' ya existe")
                return True
            except:
                pass
            
            # Crear estructura de datos para cita de prueba
            test_cita = {
                "dni_paciente": "99999999",
                "fecha_cita": "2024-01-01",
                "hora_cita": "10:00:00",
                "tipo_consulta": "Prueba",
                "diagnostico": "Cita de prueba",
                "investigador_responsable": "Sistema"
            }
            
            response = supabase.table(CITAS_TABLE).insert(test_cita).execute()
            
            if response.data:
                st.success("✅ Tabla 'citas' creada exitosamente")
                # Eliminar el registro de prueba
                supabase.table(CITAS_TABLE).delete().eq("dni_paciente", "99999999").execute()
                return True
            return False
            
        except Exception as e:
            st.error(f"❌ Error creando tabla 'citas': {str(e)}")
            return False
    
    # Botón para crear tabla
    if st.button("🛠️ Configurar Tabla de Citas", type="primary"):
        crear_tabla_citas()
    
    st.markdown("---")
    
    # Formulario para crear nueva cita
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">➕ Crear Nueva Cita</div>', unsafe_allow_html=True)
    
    with st.form("form_nueva_cita"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Buscar pacientes existentes
            pacientes_df = obtener_datos_supabase()
            
            if not pacientes_df.empty:
                pacientes_lista = [f"{row['nombre_apellido']} (DNI: {row['dni']})" 
                                  for _, row in pacientes_df.iterrows()]
                
                paciente_seleccionado = st.selectbox("Seleccionar paciente:", pacientes_lista)
                
                if paciente_seleccionado:
                    dni_paciente = paciente_seleccionado.split("DNI: ")[1].split(")")[0]
                    paciente_data = pacientes_df[pacientes_df['dni'] == dni_paciente].iloc[0]
                    
                    st.info(f"**Paciente:** {paciente_data['nombre_apellido']}")
                    st.info(f"**Edad:** {paciente_data['edad_meses']} meses")
                    st.info(f"**Hb actual:** {paciente_data.get('hemoglobina_dl1', 'N/A')} g/dL")
            else:
                st.warning("No hay pacientes registrados. Registre primero un paciente.")
                dni_paciente = st.text_input("DNI del paciente")
        
        with col2:
            fecha_cita = st.date_input("Fecha de la cita", min_value=datetime.now())
            hora_cita = st.time_input("Hora de la cita", value=datetime.now().time())
            tipo_consulta = st.selectbox("Tipo de consulta", 
                                        ["Control", "Seguimiento", "Urgencia", "Reevaluación"])
            
            # Calcular próxima cita según gravedad
            if 'paciente_data' in locals():
                hemoglobina = paciente_data.get('hemoglobina_dl1', 12)
                if hemoglobina < 9:
                    proxima_cita = fecha_cita + timedelta(days=30)  # Mensual
                elif hemoglobina < 11:
                    proxima_cita = fecha_cita + timedelta(days=90)  # Trimestral
                else:
                    proxima_cita = fecha_cita + timedelta(days=180)  # Semestral
                
                st.info(f"**Próxima cita sugerida:** {proxima_cita.strftime('%d/%m/%Y')}")
        
        diagnostico = st.text_area("Diagnóstico", placeholder="Ej: Anemia leve por deficiencia de hierro")
        tratamiento = st.text_area("Tratamiento prescrito", placeholder="Ej: Sulfato ferroso 15 mg/día")
        observaciones = st.text_area("Observaciones", placeholder="Observaciones adicionales...")
        
        submit_cita = st.form_submit_button("💾 GUARDAR CITA", type="primary", use_container_width=True)
        
        if submit_cita and dni_paciente:
            try:
                cita_data = {
                    "dni_paciente": dni_paciente,
                    "fecha_cita": fecha_cita.strftime('%Y-%m-%d'),
                    "hora_cita": hora_cita.strftime('%H:%M:%S'),
                    "tipo_consulta": tipo_consulta,
                    "diagnostico": diagnostico,
                    "tratamiento": tratamiento,
                    "observaciones": observaciones,
                    "investigador_responsable": user_info['nombre'],
                    "proxima_cita": proxima_cita.strftime('%Y-%m-%d') if 'proxima_cita' in locals() else None
                }
                
                response = supabase.table(CITAS_TABLE).insert(cita_data).execute()
                
                if response.data:
                    st.success("✅ Cita guardada exitosamente")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Error al guardar la cita")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.markdown("---")
    
    # Ver citas existentes
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">📅 Citas Programadas</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Cargar Citas", type="secondary"):
        try:
            response = supabase.table(CITAS_TABLE).select("*").order("fecha_cita").execute()
            
            if response.data:
                citas_df = pd.DataFrame(response.data)
                
                if not citas_df.empty:
                    # Filtrar citas futuras
                    hoy = datetime.now().date()
                    citas_df['fecha_cita_date'] = pd.to_datetime(citas_df['fecha_cita']).dt.date
                    citas_futuras = citas_df[citas_df['fecha_cita_date'] >= hoy]
                    
                    if not citas_futuras.empty:
                        st.dataframe(
                            citas_futuras[['fecha_cita', 'hora_cita', 'dni_paciente', 'tipo_consulta', 'diagnostico']],
                            use_container_width=True,
                            height=300
                        )
                    else:
                        st.info("📭 No hay citas futuras programadas")
                else:
                    st.info("📭 No hay citas registradas")
            else:
                st.info("📭 No hay citas registradas")
                
        except Exception as e:
            st.error(f"❌ Error cargando citas: {str(e)}")

# ==================================================
# PESTAÑA 4: SEGUIMIENTO CLÍNICO
# ==================================================

with tab4:
    st.markdown('<div class="section-title-blue">🔍 Seguimiento Clínico de Pacientes</div>', unsafe_allow_html=True)
    
    # Obtener pacientes en seguimiento
    try:
        response = supabase.table(TABLE_NAME).select("*").eq("en_seguimiento", True).execute()
        
        if response.data:
            pacientes_seguimiento = pd.DataFrame(response.data)
            
            st.markdown(f"**📋 Total pacientes en seguimiento: {len(pacientes_seguimiento)}**")
            
            for _, paciente in pacientes_seguimiento.iterrows():
                with st.expander(f"👤 {paciente['nombre_apellido']} - DNI: {paciente['dni']}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"**Edad:** {paciente['edad_meses']} meses")
                        st.markdown(f"**Peso:** {paciente['peso_kg']} kg")
                        st.markdown(f"**Talla:** {paciente['talla_cm']} cm")
                    
                    with col2:
                        hb_original = paciente.get('hemoglobina_dl1', 0)
                        hb_ajustada = calcular_hemoglobina_ajustada(hb_original, paciente.get('altitud_msnm', 0))
                        st.markdown(f"**Hemoglobina:** {hb_original:.1f} g/dL")
                        st.markdown(f"**Hb ajustada:** {hb_ajustada:.1f} g/dL")
                        
                        clasificacion, recomendacion, _ = clasificar_anemia(hb_ajustada, paciente['edad_meses'])
                        st.markdown(f"**Estado:** {clasificacion}")
                    
                    with col3:
                        st.markdown(f"**Riesgo:** {paciente.get('riesgo', 'N/A')}")
                        st.markdown(f"**Última alerta:** {paciente.get('fecha_alerta', 'N/A')}")
                        st.markdown(f"**Teléfono:** {paciente.get('telefono', 'N/A')}")
                    
                    # Botones de acción
                    col_act1, col_act2, col_act3 = st.columns(3)
                    
                    with col_act1:
                        if st.button("📝 Registrar control", key=f"control_{paciente['dni']}"):
                            st.session_state.paciente_control = paciente['dni']
                            st.rerun()
                    
                    with col_act2:
                        if st.button("📅 Agendar cita", key=f"cita_{paciente['dni']}"):
                            st.session_state.paciente_cita = paciente['dni']
                            st.rerun()
                    
                    with col_act3:
                        if st.button("✅ Dar de alta", key=f"alta_{paciente['dni']}"):
                            try:
                                supabase.table(TABLE_NAME)\
                                    .update({"en_seguimiento": False})\
                                    .eq("dni", paciente['dni'])\
                                    .execute()
                                st.success("✅ Paciente dado de alta del seguimiento")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
        else:
            st.info("📭 No hay pacientes en seguimiento activo")
            
    except Exception as e:
        st.error(f"❌ Error cargando seguimiento: {str(e)}")

# ==================================================
# PESTAÑA 5: CONFIGURACIÓN
# ==================================================

with tab5:
    st.markdown('<div class="section-title-blue">⚙️ Configuración del Sistema</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">🛠️ Configuración de Conexión</div>', unsafe_allow_html=True)
    
    col_config1, col_config2 = st.columns(2)
    
    with col_config1:
        st.info(f"**URL Supabase:** {SUPABASE_URL[:30]}...")
    
    with col_config2:
        if supabase:
            st.success("✅ Conexión activa")
        else:
            st.error("🔴 Sin conexión")
    
    st.markdown("---")
    
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">📊 Estadísticas del Sistema</div>', unsafe_allow_html=True)
    
    try:
        response = supabase.table(TABLE_NAME).select("*").execute()
        total_pacientes = len(response.data) if response.data else 0
        
        response_seguimiento = supabase.table(TABLE_NAME).select("*").eq("en_seguimiento", True).execute()
        en_seguimiento = len(response_seguimiento.data) if response_seguimiento.data else 0
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("Total pacientes", total_pacientes)
        
        with col_stat2:
            st.metric("En seguimiento", en_seguimiento)
        
        with col_stat3:
            st.metric("Usuarios activos", 1)
            
    except Exception as e:
        st.error(f"❌ Error obteniendo estadísticas: {str(e)}")
    
    st.markdown("---")
    
    st.markdown('<div class="section-title-blue" style="font-size: 1.2rem;">🔄 Mantenimiento</div>', unsafe_allow_html=True)
    
    if st.button("🧹 Limpiar caché", type="secondary"):
        st.cache_resource.clear()
        st.success("✅ Caché limpiado")
        time.sleep(1)
        st.rerun()

# ==================================================
# PIE DE PÁGINA
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
