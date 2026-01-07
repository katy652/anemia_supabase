import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import time
from datetime import datetime, timedelta
from fpdf import FPDF

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
# ESTILOS CSS MEJORADOS (se agregan estilos para mostrar info del usuario)
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
    
    /* Resto de estilos... (mantener todos los estilos existentes) */
    
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
# OBTENER INFORMACIÓN DEL USUARIO LOGUEADO
# ==================================================

user_info = st.session_state.user_info
current_user = st.session_state.current_username

# ==================================================
# CONFIGURACIÓN SUPABASE - CORREGIDA
# ==================================================

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://kwsuszkblbejvliniggd.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw")

@st.cache_resource
def init_supabase():
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Prueba de conexión simple
        test = supabase_client.table("alertas_hemoglobina").select("*").limit(1).execute()
        return supabase_client
    except Exception as e:
        st.error(f"❌ Error conectando a Supabase: {str(e)[:200]}")
        return None

supabase = init_supabase()

# ==================================================
# FUNCIONES PARA TABLA SEGUIMIENTO_CLINICO - CORREGIDAS
# ==================================================

def crear_tabla_seguimiento_clinico():
    """Función para crear o verificar la tabla seguimiento_clinico"""
    try:
        # Intentar insertar un registro de prueba
        test_data = {
            "dni_paciente": "TEST123",
            "fecha_seguimiento": "2024-01-01",
            "tipo_seguimiento": "Prueba",
            "observaciones": "Registro de prueba"
        }
        
        response = supabase.table("seguimiento_clinico").insert(test_data).execute()
        
        if response.data:
            # Eliminar el registro de prueba
            supabase.table("seguimiento_clinico").delete().eq("dni_paciente", "TEST123").execute()
            return True
        return False
        
    except Exception as e:
        error_msg = str(e)
        if "column" in error_msg and "does not exist" in error_msg:
            # Intentar agregar columnas faltantes
            try:
                # Esta es una sugerencia - en realidad necesitarías ejecutar SQL directamente
                st.warning("⚠️ La tabla 'seguimiento_clinico' necesita columnas adicionales")
                st.info("""
                **Ejecuta este SQL en Supabase:**
                ```sql
                ALTER TABLE seguimiento_clinico 
                ADD COLUMN IF NOT EXISTS proximo_control DATE,
                ADD COLUMN IF NOT EXISTS fecha_control DATE DEFAULT CURRENT_DATE,
                ADD COLUMN IF NOT EXISTS peso_control NUMERIC(5,2),
                ADD COLUMN IF NOT EXISTS talla_control NUMERIC(5,2),
                ADD COLUMN IF NOT EXISTS hemoglobina_control NUMERIC(5,2),
                ADD COLUMN IF NOT EXISTS estado_nutricional TEXT,
                ADD COLUMN IF NOT EXISTS tratamiento_actual TEXT;
                ```
                """)
                return False
            except:
                return False
        return False

def guardar_seguimiento_clinico_corregido(datos):
    """Guarda un seguimiento clínico con estructura CORREGIDA"""
    try:
        # Asegurar que todos los campos requeridos existan
        datos_completos = {
            "dni_paciente": datos.get("dni_paciente", ""),
            "fecha_seguimiento": datos.get("fecha_seguimiento", datetime.now().strftime('%Y-%m-%d')),
            "tipo_seguimiento": datos.get("tipo_seguimiento", "Control rutinario"),
            "observaciones": datos.get("observaciones", ""),
            "usuario_responsable": datos.get("usuario_responsable", user_info.get('nombre', 'Usuario')),
            "hemoglobina_control": datos.get("hemoglobina_control"),
            "peso_control": datos.get("peso_control"),
            "talla_control": datos.get("talla_control"),
            "estado_nutricional": datos.get("estado_nutricional"),  # ← ESTE ES EL CAMPO CORRECTO
            "tratamiento_actual": datos.get("tratamiento_actual"),
            "proximo_control": datos.get("proximo_control")
        }
        
        # Eliminar campos None para evitar errores
        datos_finales = {k: v for k, v in datos_completos.items() if v is not None}
        
        response = supabase.table("seguimiento_clinico").insert(datos_finales).execute()
        
        if response.data:
            return True, response.data[0]['id']
        else:
            return False, "Error al guardar"
            
    except Exception as e:
        error_msg = str(e)
        if "estado_mutricional" in error_msg:
            return False, "ERROR: Se está usando 'estado_mutricional' pero la columna se llama 'estado_nutricional'"
        else:
            return False, f"Error: {str(e)[:100]}"

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
                {'edad_meses': 9, 'peso_min_ninas': 7.2, 'peso_promedio_ninas': 8.9, 'peso_max_ninas': 10.8, 'peso_min_ninos': 7.8, 'peso_promedio_ninos': 9.2, 'peso_max_ninos': 11.2, 'talla_min_ninas': 65.0, 'talla_promedio_ninas': 70.0, 'talla_max_ninas': 75.0, 'talla_min_ninos': 68.0, 'talla_promedio_ninos': 72.0, 'talla_max_ninos': 77.0},
                {'edad_meses': 12, 'peso_min_ninas': 8.0, 'peso_promedio_ninas': 9.5, 'peso_max_ninas': 11.5, 'peso_min_ninos': 8.6, 'peso_promedio_ninos': 10.2, 'peso_max_ninos': 12.3, 'talla_min_ninas': 69.0, 'talla_promedio_ninas': 74.0, 'talla_max_ninas': 79.5, 'talla_min_ninos': 71.0, 'talla_promedio_ninos': 76.0, 'talla_max_ninos': 81.5},
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
# FUNCIONES DE BASE DE DATOS
# ==================================================

TABLE_NAME = "alertas_hemoglobina"

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
# FUNCIONES DE CÁLCULO
# ==================================================

def obtener_ajuste_hemoglobina(altitud):
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
    
    for ajuste in AJUSTE_HEMOGLOBINA:
        if ajuste["altitud_min"] <= altitud <= ajuste["altitud_max"]:
            return ajuste["ajuste"]
    return 0.0

def calcular_hemoglobina_ajustada(hemoglobina_medida, altitud):
    ajuste = obtener_ajuste_hemoglobina(altitud)
    return hemoglobina_medida + ajuste

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

def evaluar_estado_nutricional(edad_meses, peso_kg, talla_cm, genero):
    """Evalúa el estado nutricional basado en tablas de referencia OMS"""
    referencia_df = obtener_referencia_crecimiento()
    
    if referencia_df.empty or edad_meses == 0:
        return "Sin datos referencia", "Sin datos referencia", "NUTRICIÓN NO EVALUADA"
    
    referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_meses]
    
    if referencia_edad.empty:
        # Encontrar la edad más cercana
        edades_disponibles = referencia_df['edad_meses'].values
        edad_cercana = min(edades_disponibles, key=lambda x: abs(x - edad_meses))
        referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_cercana]
    
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

# ==================================================
# PESTAÑAS PRINCIPALES
# ==================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Registro Completo", 
    "🔍 Seguimiento Clínico", 
    "📈 Dashboard Nacional",
    "📋 Sistema de Citas"
])

# ==================================================
# PESTAÑA 1: REGISTRO COMPLETO
# ==================================================

with tab1:
    st.markdown('<div class="section-title-blue">📝 Registro Completo de Paciente</div>', unsafe_allow_html=True)
    
    with st.form("formulario_completo", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">👤 Datos Personales</div>', unsafe_allow_html=True)
            
            dni = st.text_input("DNI*", placeholder="Ej: 87654321")
            nombre_apellido = st.text_input("Nombre Completo*", placeholder="Ej: Ana García Pérez")
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
            peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1)
            talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1)
            genero = st.selectbox("Género*", GENEROS)
            telefono = st.text_input("Teléfono*", placeholder="Ej: 987654321")
            estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE)
        
        with col2:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">🌍 Datos Geográficos</div>', unsafe_allow_html=True)
            region = st.selectbox("Región*", PERU_REGIONS)
            departamento = st.text_input("Departamento/Distrito", placeholder="Ej: Lima Metropolitana")
            altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, 500)
            
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">💰 Factores Socioeconómicos del Apoderado</div>', unsafe_allow_html=True)
            nivel_educativo = st.selectbox("Nivel Educativo del Apoderado", NIVELES_EDUCATIVOS)
            acceso_agua_potable = st.checkbox("Acceso a agua potable")
            tiene_servicio_salud = st.checkbox("Tiene servicio de salud")
        
        st.markdown("---")
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">🩺 Parámetros Clínicos</div>', unsafe_allow_html=True)
            hemoglobina_medida = st.number_input("Hemoglobina medida (g/dL)*", 5.0, 20.0, 11.0, 0.1)
            
            # Calcular hemoglobina ajustada
            ajuste_hb = obtener_ajuste_hemoglobina(altitud_msnm)
            hemoglobina_ajustada = calcular_hemoglobina_ajustada(hemoglobina_medida, altitud_msnm)
            
            # Clasificar anemia
            clasificacion, recomendacion, tipo_alerta = clasificar_anemia(hemoglobina_ajustada, edad_meses)
            
            # Mostrar clasificación
            st.info(f"**Clasificación:** {clasificacion}")
            st.info(f"**Recomendación:** {recomendacion}")
            st.info(f"**Hemoglobina ajustada:** {hemoglobina_ajustada:.1f} g/dL (Ajuste: {ajuste_hb:+.1f})")
            
            en_seguimiento = st.checkbox("Marcar para seguimiento activo", value=hemoglobina_ajustada < 11.0)
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
            
            FACTORES_SOCIALES = [
                "Bajo nivel educativo de padres",
                "Ingresos familiares reducidos",
                "Hacinamiento en vivienda",
                "Acceso limitado a agua potable",
                "Zona rural o alejada",
                "Trabajo informal o precario"
            ]
            
            st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">🏥 Factores Clínicos</div>', unsafe_allow_html=True)
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS)
            
            st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">💰 Factores Socioeconómicos del Apoderado</div>', unsafe_allow_html=True)
            factores_sociales = st.multiselect("Seleccione factores socioeconómicos:", FACTORES_SOCIALES)
        
        # Botón de guardar
        submit = st.form_submit_button("💾 GUARDAR PACIENTE", use_container_width=True, type="primary")
        
        if submit:
            # Validaciones básicas
            if not dni or not nombre_apellido or not telefono:
                st.error("❌ Complete los campos obligatorios (*)")
            else:
                # Preparar datos para guardar
                paciente_data = {
                    "dni": dni,
                    "nombre_apellido": nombre_apellido,
                    "edad_meses": edad_meses,
                    "peso_kg": peso_kg,
                    "talla_cm": talla_cm,
                    "genero": genero,
                    "telefono": telefono,
                    "estado_paciente": estado_paciente,
                    "region": region,
                    "departamento": departamento,
                    "altitud_msnm": altitud_msnm,
                    "nivel_educativo": nivel_educativo,
                    "acceso_agua_potable": acceso_agua_potable,
                    "tiene_servicio_salud": tiene_servicio_salud,
                    "hemoglobina_dl1": hemoglobina_medida,
                    "en_seguimiento": en_seguimiento,
                    "consumir_hierro": consume_hierro,
                    "tipo_suplemento_hierro": tipo_suplemento_hierro if consume_hierro else None,
                    "frecuencia_suplemento": frecuencia_suplemento if consume_hierro else None,
                    "antecedentes_anemia": antecedentes_anemia,
                    "enfermedades_cronicas": enfermedades_cronicas,
                    "riesgo": "ALTO" if hemoglobina_ajustada < 10.0 else "MODERADO" if hemoglobina_ajustada < 11.0 else "BAJO",
                    "fecha_alerta": datetime.now().strftime("%Y-%m-%d"),
                    "estado_alerta": "URGENTE" if hemoglobina_ajustada < 9.0 else "PRIORITARIO" if hemoglobina_ajustada < 10.0 else "VIGILANCIA",
                    "sugerencias": recomendacion
                }
                
                # Guardar en Supabase
                resultado = insertar_datos_supabase(paciente_data)
                
                if resultado:
                    if isinstance(resultado, dict) and resultado.get("status") == "duplicado":
                        st.error(f"❌ El DNI {dni} ya existe en la base de datos")
                    else:
                        st.success("✅ Paciente registrado exitosamente")
                        st.balloons()
                else:
                    st.error("❌ Error al guardar el paciente")

# ==================================================
# PESTAÑA 2: SEGUIMIENTO CLÍNICO - VERSIÓN CORREGIDA
# ==================================================

with tab2:
    st.markdown('<div class="section-title-green">🔬 SISTEMA DE SEGUIMIENTO CLÍNICO</div>', unsafe_allow_html=True)
    
    # Inicializar estados
    if 'seguimiento_paciente_seleccionado' not in st.session_state:
        st.session_state.seguimiento_paciente_seleccionado = None
    
    if 'seguimiento_historial' not in st.session_state:
        st.session_state.seguimiento_historial = []
    
    # Función para cargar pacientes
    def cargar_pacientes_para_seguimiento():
        try:
            response = supabase.table("alertas_hemoglobina").select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    # Crear pestañas internas
    tab_seg1, tab_seg2, tab_seg3 = st.tabs([
        "🔍 Buscar Paciente", 
        "📝 Nuevo Seguimiento", 
        "📋 Historial"
    ])
    
    # Pestaña 1: Buscar Paciente
    with tab_seg1:
        st.header("🔍 BUSCAR PACIENTE PARA SEGUIMIENTO")
        
        if st.button("🔄 Cargar Pacientes", type="primary"):
            pacientes_df = cargar_pacientes_para_seguimiento()
            st.session_state.pacientes_disponibles = pacientes_df
        
        if 'pacientes_disponibles' in st.session_state and not st.session_state.pacientes_disponibles.empty:
            pacientes_df = st.session_state.pacientes_disponibles
            
            # Buscar
            buscar = st.text_input("Buscar por nombre, DNI o región:", placeholder="Ej: 'Juan' o '87654321'")
            
            if buscar:
                mask = (pacientes_df['nombre_apellido'].astype(str).str.contains(buscar, case=False, na=False) |
                       pacientes_df['dni'].astype(str).str.contains(buscar, na=False) |
                       pacientes_df['region'].astype(str).str.contains(buscar, case=False, na=False))
                pacientes_filtrados = pacientes_df[mask]
            else:
                pacientes_filtrados = pacientes_df
            
            if not pacientes_filtrados.empty:
                st.write(f"📊 **{len(pacientes_filtrados)} pacientes encontrados**")
                
                # Mostrar en tabla
                columnas_mostrar = ['nombre_apellido', 'dni', 'edad_meses', 'hemoglobina_dl1', 'region', 'riesgo']
                columnas_disponibles = [c for c in columnas_mostrar if c in pacientes_filtrados.columns]
                
                if columnas_disponibles:
                    df_mostrar = pacientes_filtrados[columnas_disponibles].copy()
                    df_mostrar = df_mostrar.fillna('N/A')
                    
                    # Renombrar columnas
                    nombres_columnas = {
                        'nombre_apellido': 'Nombre',
                        'dni': 'DNI',
                        'edad_meses': 'Edad (meses)',
                        'hemoglobina_dl1': 'Hb (g/dL)',
                        'region': 'Región',
                        'riesgo': 'Riesgo'
                    }
                    
                    nombres_columnas_filtrados = {k: v for k, v in nombres_columnas.items() if k in df_mostrar.columns}
                    df_mostrar = df_mostrar.rename(columns=nombres_columnas_filtrados)
                    
                    # Mostrar tabla
                    st.dataframe(
                        df_mostrar,
                        use_container_width=True,
                        height=300
                    )
                    
                    # Seleccionar paciente
                    pacientes_lista = df_mostrar['Nombre'] + " - DNI: " + df_mostrar['DNI']
                    paciente_seleccionado = st.selectbox(
                        "Seleccionar paciente para seguimiento:",
                        pacientes_lista
                    )
                    
                    if paciente_seleccionado:
                        # Extraer DNI del paciente seleccionado
                        dni_seleccionado = paciente_seleccionado.split("DNI: ")[1].strip() if "DNI: " in paciente_seleccionado else ""
                        
                        if dni_seleccionado:
                            paciente_info = pacientes_filtrados[pacientes_filtrados['dni'] == dni_seleccionado]
                            
                            if not paciente_info.empty:
                                paciente_dict = paciente_info.iloc[0].to_dict()
                                
                                if st.button("✅ Seleccionar este paciente", use_container_width=True):
                                    st.session_state.seguimiento_paciente_seleccionado = paciente_dict
                                    st.success(f"✅ Paciente seleccionado: {paciente_dict['nombre_apellido']}")
                                    
                                    # Cargar historial del paciente
                                    try:
                                        response = supabase.table("seguimiento_clinico")\
                                            .select("*")\
                                            .eq("dni_paciente", dni_seleccionado)\
                                            .order("fecha_seguimiento", desc=True)\
                                            .execute()
                                        
                                        if response.data:
                                            st.session_state.seguimiento_historial = response.data
                                        else:
                                            st.session_state.seguimiento_historial = []
                                    except:
                                        st.session_state.seguimiento_historial = []
                                    
                                    # Redirigir a la pestaña de nuevo seguimiento
                                    st.markdown("""
                                    <script>
                                    setTimeout(() => {
                                        const tabs = document.querySelectorAll('button[role="tab"]');
                                        if (tabs.length >= 4) {
                                            tabs[5].click(); // Índice de la pestaña Nuevo Seguimiento
                                        }
                                    }, 1000);
                                    </script>
                                    """, unsafe_allow_html=True)
    
    # Pestaña 2: Nuevo Seguimiento - VERSIÓN CORREGIDA
    with tab_seg2:
        st.header("📝 NUEVO SEGUIMIENTO CLÍNICO")
        
        if not st.session_state.seguimiento_paciente_seleccionado:
            st.warning("⚠️ Primero seleccione un paciente en la pestaña 'Buscar Paciente'")
        else:
            paciente = st.session_state.seguimiento_paciente_seleccionado
            
            # Mostrar información del paciente
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown(f"""
                <div style="background: #dbeafe; padding: 1rem; border-radius: 10px;">
                    <h4 style="margin: 0 0 10px 0; color: #1e40af;">📋 PACIENTE SELECCIONADO</h4>
                    <p><strong>Nombre:</strong> {paciente.get('nombre_apellido', 'N/A')}</p>
                    <p><strong>DNI:</strong> {paciente.get('dni', 'N/A')}</p>
                    <p><strong>Edad:</strong> {paciente.get('edad_meses', 'N/A')} meses</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info2:
                st.markdown(f"""
                <div style="background: #d1fae5; padding: 1rem; border-radius: 10px;">
                    <h4 style="margin: 0 0 10px 0; color: #059669;">📊 DATOS CLÍNICOS</h4>
                    <p><strong>Hb actual:</strong> {paciente.get('hemoglobina_dl1', 'N/A')} g/dL</p>
                    <p><strong>Región:</strong> {paciente.get('region', 'N/A')}</p>
                    <p><strong>Estado:</strong> {paciente.get('estado_paciente', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Formulario de seguimiento - VERSIÓN SIMPLIFICADA Y CORREGIDA
            with st.form("form_seguimiento_simple"):
                st.subheader("📊 Datos del Control")
                
                col_fecha, col_tipo = st.columns(2)
                with col_fecha:
                    fecha_control = st.date_input("Fecha del control", datetime.now().date())
                with col_tipo:
                    tipo_seguimiento = st.selectbox(
                        "Tipo de seguimiento",
                        ["Control rutinario", "Seguimiento por anemia", "Control nutricional", 
                         "Evaluación de tratamiento", "Consulta de urgencia"]
                    )
                
                col_hb, col_peso, col_talla = st.columns(3)
                with col_hb:
                    hemoglobina = st.number_input(
                        "Hemoglobina (g/dL)", 
                        value=float(paciente.get('hemoglobina_dl1', 11.0)),
                        min_value=0.0, 
                        max_value=20.0, 
                        step=0.1
                    )
                with col_peso:
                    peso = st.number_input(
                        "Peso (kg)", 
                        value=float(paciente.get('peso_kg', 12.0)),
                        min_value=0.0, 
                        max_value=50.0, 
                        step=0.1
                    )
                with col_talla:
                    talla = st.number_input(
                        "Talla (cm)", 
                        value=float(paciente.get('talla_cm', 85.0)),
                        min_value=0.0, 
                        max_value=150.0, 
                        step=0.1
                    )
                
                # Evaluar estado nutricional
                estado_peso, estado_talla, estado_nutricional = evaluar_estado_nutricional(
                    paciente.get('edad_meses', 24),
                    peso,
                    talla,
                    paciente.get('genero', 'F')
                )
                
                st.info(f"**Estado nutricional:** {estado_nutricional}")
                st.caption(f"📏 **Peso:** {estado_peso} | **Talla:** {estado_talla}")
                
                observaciones = st.text_area(
                    "Observaciones clínicas", 
                    placeholder="Describa el estado del paciente, síntomas, evolución, respuesta al tratamiento...",
                    height=100
                )
                
                tratamiento = st.text_input(
                    "Tratamiento actual o prescrito", 
                    placeholder="Ej: Sulfato ferroso 15 mg/día, suplemento vitamínico..."
                )
                
                proximo_control = st.date_input(
                    "Próximo control sugerido",
                    value=datetime.now().date() + timedelta(days=30)
                )
                
                # Botón de guardar
                submit = st.form_submit_button("💾 GUARDAR SEGUIMIENTO", use_container_width=True)
                
                if submit:
                    # Preparar datos para guardar - VERSIÓN CORREGIDA
                    datos_seguimiento = {
                        "dni_paciente": str(paciente.get('dni', '')),
                        "fecha_seguimiento": fecha_control.strftime('%Y-%m-%d'),
                        "tipo_seguimiento": tipo_seguimiento,
                        "observaciones": observaciones,
                        "usuario_responsable": user_info.get('nombre', 'Usuario'),
                        "hemoglobina_control": hemoglobina,
                        "peso_control": peso,
                        "talla_control": talla,
                        "estado_nutricional": estado_nutricional,  # ← CAMPO CORRECTO
                        "tratamiento_actual": tratamiento,
                        "proximo_control": proximo_control.strftime('%Y-%m-%d'),
                        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Guardar usando la función corregida
                    success, result = guardar_seguimiento_clinico_corregido(datos_seguimiento)
                    
                    if success:
                        st.success("✅ Seguimiento guardado correctamente")
                        st.balloons()
                        
                        # Actualizar hemoglobina en el paciente principal
                        try:
                            supabase.table("alertas_hemoglobina")\
                                .update({"hemoglobina_dl1": hemoglobina})\
                                .eq("dni", paciente.get('dni'))\
                                .execute()
                        except:
                            pass
                        
                        # Actualizar historial en session state
                        datos_seguimiento['id'] = result
                        if 'seguimiento_historial' not in st.session_state:
                            st.session_state.seguimiento_historial = []
                        st.session_state.seguimiento_historial.insert(0, datos_seguimiento)
                        
                    else:
                        if "estado_mutricional" in result:
                            st.error("❌ ERROR: El campo 'estado_mutricional' no existe. Debe ser 'estado_nutricional'")
                        else:
                            st.error(f"❌ Error al guardar: {result}")
    
    # Pestaña 3: Historial
    with tab_seg3:
        st.header("📋 HISTORIAL CLÍNICO")
        
        if not st.session_state.seguimiento_paciente_seleccionado:
            st.warning("⚠️ Seleccione un paciente primero")
        else:
            paciente = st.session_state.seguimiento_paciente_seleccionado
            
            # Mostrar información del paciente
            st.markdown(f"""
            <div style="background: #f3e8ff; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;">
                <h3 style="margin: 0 0 10px 0; color: #5b21b6;">📊 HISTORIAL DE: {paciente.get('nombre_apellido', 'N/A')}</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                    <div><strong>DNI:</strong> {paciente.get('dni', 'N/A')}</div>
                    <div><strong>Edad:</strong> {paciente.get('edad_meses', 'N/A')} meses</div>
                    <div><strong>Región:</strong> {paciente.get('region', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón para actualizar historial
            if st.button("🔄 Actualizar Historial", type="primary"):
                try:
                    response = supabase.table("seguimiento_clinico")\
                        .select("*")\
                        .eq("dni_paciente", paciente.get('dni', ''))\
                        .order("fecha_seguimiento", desc=True)\
                        .execute()
                    
                    if response.data:
                        st.session_state.seguimiento_historial = response.data
                        st.success(f"✅ Historial actualizado: {len(response.data)} controles")
                    else:
                        st.session_state.seguimiento_historial = []
                        st.info("📭 No hay controles registrados")
                except:
                    st.error("❌ Error al cargar historial")
            
            # Mostrar historial
            historial = st.session_state.get('seguimiento_historial', [])
            
            if historial:
                # Crear DataFrame
                df_historial = pd.DataFrame(historial)
                
                # Ordenar por fecha
                if 'fecha_seguimiento' in df_historial.columns:
                    df_historial['fecha_seguimiento'] = pd.to_datetime(df_historial['fecha_seguimiento'])
                    df_historial = df_historial.sort_values('fecha_seguimiento', ascending=False)
                
                # Mostrar métricas
                col_met1, col_met2, col_met3 = st.columns(3)
                with col_met1:
                    st.metric("Total controles", len(df_historial))
                with col_met2:
                    if 'hemoglobina_control' in df_historial.columns:
                        hb_prom = df_historial['hemoglobina_control'].mean()
                        st.metric("Hb promedio", f"{hb_prom:.1f} g/dL")
                with col_met3:
                    if 'fecha_seguimiento' in df_historial.columns:
                        ultima = df_historial['fecha_seguimiento'].max().strftime('%d/%m/%Y')
                        st.metric("Último control", ultima)
                
                # Mostrar tabla
                st.markdown("#### 📋 Controles Registrados")
                
                # Columnas disponibles
                columnas_posibles = ['fecha_seguimiento', 'tipo_seguimiento', 
                                    'hemoglobina_control', 'peso_control', 'talla_control', 
                                    'estado_nutricional', 'observaciones', 'tratamiento_actual',
                                    'usuario_responsable', 'proximo_control']
                
                columnas_disponibles = [c for c in columnas_posibles if c in df_historial.columns]
                
                if columnas_disponibles:
                    st.dataframe(
                        df_historial[columnas_disponibles],
                        use_container_width=True,
                        height=400
                    )
                else:
                    st.info("No hay datos suficientes para mostrar en la tabla")
                
                # Botón para exportar
                if st.button("📥 Exportar Historial (CSV)", use_container_width=True):
                    csv = df_historial.to_csv(index=False)
                    st.download_button(
                        label="📤 Descargar CSV",
                        data=csv,
                        file_name=f"historial_{paciente.get('dni', 'paciente')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("📭 No hay controles registrados para este paciente")

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
# PESTAÑA 4: SISTEMA DE CITAS (SIMPLIFICADA)
# ==================================================

with tab4:
    st.markdown('<div class="section-title-purple">📅 SISTEMA DE CITAS Y RECORDATORIOS</div>', unsafe_allow_html=True)
    
    st.info("""
    **📋 Funcionalidades del sistema de citas:**
    
    1. **Citas automáticas** según nivel de anemia
    2. **Recordatorios** de citas próximas
    3. **Calendario de seguimiento** por paciente
    4. **Historial completo** de citas
    
    ⚠️ *Esta sección requiere configuración adicional en Supabase.*
    """)
    
    # Verificar si existe la tabla citas
    try:
        response = supabase.table("citas").select("*").limit(1).execute()
        st.success("✅ Tabla 'citas' disponible")
        
        # Mostrar estadísticas básicas
        if response.data:
            total_citas = len(supabase.table("citas").select("*").execute().data)
            st.metric("Total citas registradas", total_citas)
    except:
        st.warning("⚠️ La tabla 'citas' no está disponible")
        
        with st.expander("📝 Instrucciones para crear la tabla"):
            st.markdown("""
            **Ejecuta este SQL en Supabase SQL Editor:**
            
            ```sql
            CREATE TABLE IF NOT EXISTS citas (
                id BIGSERIAL PRIMARY KEY,
                dni_paciente TEXT REFERENCES alertas_hemoglobina(dni),
                fecha_cita DATE NOT NULL,
                hora_cita TIME,
                tipo_consulta TEXT,
                diagnostico TEXT,
                tratamiento TEXT,
                observaciones TEXT,
                investigador_responsable TEXT,
                proxima_cita DATE,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            ```
            
            **Luego crea políticas de seguridad:**
            
            ```sql
            -- Permitir todo (para desarrollo)
            ALTER TABLE citas ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Permitir todo" ON citas;
            CREATE POLICY "Permitir todo" ON citas
                FOR ALL USING (true);
            ```
            """)
    
    # Sección para crear cita manual simple
    st.markdown("---")
    st.markdown("### ➕ Crear Cita Manual")
    
    with st.form("form_cita_simple"):
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # Buscar paciente
            try:
                pacientes_response = supabase.table("alertas_hemoglobina").select("dni, nombre_apellido").limit(50).execute()
                if pacientes_response.data:
                    pacientes_opciones = [f"{p['nombre_apellido']} (DNI: {p['dni']})" for p in pacientes_response.data]
                    paciente_seleccionado = st.selectbox("Paciente:", pacientes_opciones)
                    
                    # Extraer DNI
                    import re
                    dni_match = re.search(r'DNI:\s*(\d+)', paciente_seleccionado)
                    dni_paciente = dni_match.group(1) if dni_match else ""
                else:
                    dni_paciente = st.text_input("DNI del paciente:", placeholder="Ej: 87654321")
            except:
                dni_paciente = st.text_input("DNI del paciente:", placeholder="Ej: 87654321")
        
        with col_c2:
            fecha_cita = st.date_input("Fecha de la cita", min_value=datetime.now())
            hora_cita = st.time_input("Hora de la cita", value=datetime.now().time())
            tipo_consulta = st.selectbox("Tipo de consulta", 
                                        ["Control", "Seguimiento", "Urgencia", "Reevaluación"])
        
        diagnostico = st.text_input("Diagnóstico", placeholder="Ej: Anemia leve")
        observaciones = st.text_area("Observaciones", placeholder="Observaciones adicionales...")
        
        submit_cita = st.form_submit_button("💾 GUARDAR CITA", use_container_width=True)
        
        if submit_cita and dni_paciente:
            try:
                cita_data = {
                    "dni_paciente": dni_paciente,
                    "fecha_cita": fecha_cita.strftime('%Y-%m-%d'),
                    "hora_cita": hora_cita.strftime('%H:%M:%S'),
                    "tipo_consulta": tipo_consulta,
                    "diagnostico": diagnostico,
                    "observaciones": observaciones,
                    "investigador_responsable": user_info.get('nombre', 'Usuario'),
                    "proxima_cita": (fecha_cita + timedelta(days=30)).strftime('%Y-%m-%d')
                }
                
                response = supabase.table("citas").insert(cita_data).execute()
                
                if response.data:
                    st.success("✅ Cita guardada exitosamente")
                else:
                    st.error("❌ Error al guardar la cita")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)[:100]}")

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
