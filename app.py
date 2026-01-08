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

def generar_pdf_fpdf(paciente, historial):
    """
    Genera PDF usando FPDF (sin caracteres especiales problemáticos)
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Configurar fuentes estándar
        pdf.set_font("Arial", "B", 16)
        
        # Título
        pdf.cell(0, 10, "SISTEMA NIXON - HISTORIAL CLINICO", 0, 1, "C")
        pdf.ln(5)
        
        # Fecha
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")
        pdf.ln(10)
        
        # Información del paciente
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "INFORMACION DEL PACIENTE", 0, 1)
        pdf.set_font("Arial", "", 10)
        
        # Limpiar caracteres especiales
        def limpiar_texto(texto):
            if not texto:
                return "N/A"
            # Reemplazar caracteres problemáticos
            texto = str(texto)
            reemplazos = {
                '•': '-',
                '–': '-',
                '—': '-',
                '‘': "'",
                '’': "'",
                '“': '"',
                '”': '"',
                '…': '...',
                'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
                'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
                'ñ': 'n', 'Ñ': 'N',
                'ü': 'u', 'Ü': 'U'
            }
            for char_orig, char_reemplazo in reemplazos.items():
                texto = texto.replace(char_orig, char_reemplazo)
            return texto
        
        datos = [
            f"Nombre: {limpiar_texto(paciente.get('nombre_apellido', 'N/A'))}",
            f"DNI: {paciente.get('dni', 'N/A')}",
            f"Edad: {paciente.get('edad_meses', 'N/A')} meses",
            f"Genero: {limpiar_texto(paciente.get('genero', 'N/A'))}",
            f"Region: {limpiar_texto(paciente.get('region', 'N/A'))}",
            f"Telefono: {paciente.get('telefono', 'N/A')}",
            f"Hemoglobina actual: {paciente.get('hemoglobina_dl1', 'N/A')} g/dL",
            f"Estado: {limpiar_texto(paciente.get('estado_paciente', 'N/A'))}",
            f"Riesgo: {limpiar_texto(paciente.get('riesgo', 'N/A'))}"
        ]
        
        for dato in datos:
            pdf.cell(0, 8, limpiar_texto(dato), 0, 1)
        
        pdf.ln(10)
        
        # Historial de controles
        if historial and len(historial) > 0:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"HISTORIAL DE CONTROLES ({len(historial)} registros)", 0, 1)
            pdf.ln(5)
            
            # Tabla
            pdf.set_font("Arial", "B", 10)
            # Encabezados
            col_widths = [30, 25, 20, 35, 30, 30]
            headers = ["Fecha", "Tipo", "Hb", "Clasificacion", "Responsable", "Proximo"]
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, "C")
            pdf.ln()
            
            # Datos
            pdf.set_font("Arial", "", 9)
            for idx, control in enumerate(historial[:25]):
                # Alternar color de fondo
                if idx % 2 == 0:
                    pdf.set_fill_color(240, 240, 240)
                else:
                    pdf.set_fill_color(255, 255, 255)
                
                # Obtener y limpiar datos
                fecha = control.get('fecha_seguimiento', 'N/A')[:10] if control.get('fecha_seguimiento') else 'N/A'
                tipo = limpiar_texto(control.get('tipo_seguimiento', 'N/A'))[:10]
                hb = control.get('hemoglobina_actual', 'N/A')
                if isinstance(hb, (int, float)):
                    hb = f"{hb:.1f}"
                clasif = limpiar_texto(control.get('clasificacion_actual', 'N/A'))[:10]
                responsable = limpiar_texto(control.get('usuario_responsable', 'N/A'))[:10]
                proximo = control.get('proximo_control', 'N/A')[:10] if control.get('proximo_control') else 'N/A'
                
                # Agregar fila
                datos_fila = [fecha, tipo, hb, clasif, responsable, proximo]
                for i, dato in enumerate(datos_fila):
                    pdf.cell(col_widths[i], 8, limpiar_texto(dato), 1, 0, "C", 1)
                pdf.ln()
            
            pdf.ln(10)
            
            # Estadísticas
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 10, "ESTADISTICAS", 0, 1)
            pdf.set_font("Arial", "", 10)
            
            valores_hb = []
            for control in historial:
                hb = control.get('hemoglobina_actual')
                if isinstance(hb, (int, float)):
                    valores_hb.append(hb)
            
            if valores_hb:
                promedio = sum(valores_hb) / len(valores_hb)
                primera = valores_hb[0]
                ultima = valores_hb[-1]
                minimo = min(valores_hb)
                maximo = max(valores_hb)
                
                # Usar guión en lugar de bullet point
                pdf.cell(0, 8, f"- Promedio de hemoglobina: {promedio:.1f} g/dL", 0, 1)
                pdf.cell(0, 8, f"- Primera medicion: {primera:.1f} g/dL", 0, 1)
                pdf.cell(0, 8, f"- Ultima medicion: {ultima:.1f} g/dL", 0, 1)
                pdf.cell(0, 8, f"- Rango: {minimo:.1f} - {maximo:.1f} g/dL", 0, 1)
                
                if len(valores_hb) >= 2:
                    cambio = ultima - primera
                    if cambio > 0.5:
                        tendencia = f'Mejoria significativa (+{cambio:.1f} g/dL)'
                    elif cambio > 0:
                        tendencia = f'Ligera mejoria (+{cambio:.1f} g/dL)'
                    elif cambio < -0.5:
                        tendencia = f'Empeoramiento significativo ({cambio:+.1f} g/dL)'
                    elif cambio < 0:
                        tendencia = f'Ligero empeoramiento ({cambio:+.1f} g/dL)'
                    else:
                        tendencia = 'Estable'
                    
                    pdf.cell(0, 8, f"- Tendencia: {tendencia}", 0, 1)
        
        else:
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 10, "No hay controles registrados para este paciente.", 0, 1)
        
        # Pie de página
        pdf.set_y(-30)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 5, "Sistema Nixon v2.0 - Control de Anemia Infantil", 0, 1, "C")
        pdf.cell(0, 5, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")
        pdf.cell(0, 5, "(c) 2024 - Uso medico profesional", 0, 1, "C")
        
        # OPCIÓN 1: Usar latin-1 con texto limpio
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
        
    except Exception as e:
        # Si falla, crear un PDF de error simple SIN caracteres especiales
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "ERROR AL GENERAR PDF", 0, 1, "C")
            pdf.set_font("Arial", "", 12)
            error_msg = str(e)[:100].replace('•', '-').replace('–', '-').replace('—', '-')
            pdf.multi_cell(0, 10, f"Error: {error_msg}")
            return pdf.output(dest='S').encode('latin-1', errors='ignore')
        except:
            # Si todo falla, devolver PDF mínimo
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "PDF GENERADO", 0, 1, "C")
                return pdf.output(dest='S').encode('latin-1', errors='ignore')
            except:
                return b"PDF_ERROR"
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
# FUNCIONES PARA TABLA CITAS
# ==================================================

def crear_tabla_citas_simple():
    """Crea la tabla citas de forma simple"""
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
    """Prueba directa de guardado"""
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
# INTERFAZ PRINCIPAL CON INFORMACIÓN DEL USUARIO
# ==================================================

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
# PESTAÑA 1: REGISTRO COMPLETO (CON VALIDACIÓN EN PYTHON)
# ==================================================

with tab1:
    st.markdown('<div class="section-title-blue">📝 Registro Completo de Paciente</div>', unsafe_allow_html=True)
    
    # Variables para mostrar errores
    error_dni = None
    error_nombre = None
    error_telefono = None
    
    # Variable para controlar si se mostró el resultado
    resultado_mostrado = False
    
    # Inicializar session state para limpiar
    if 'limpiar_formulario' not in st.session_state:
        st.session_state.limpiar_formulario = False
    
    # Función para limpiar formulario - VERSIÓN SIMPLIFICADA Y SEGURA
    def limpiar_formulario():
        """Limpia el formulario estableciendo valores predeterminados"""
        try:
            # Solo limpiar los datos analizados, NO los inputs
            if 'datos_analizados' in st.session_state:
                del st.session_state.datos_analizados
            
            # Mostrar mensaje de éxito
            st.success("✅ Formulario listo para nuevo registro")
            
            # NO hacer rerun aquí - eso causaba el error
            return True
            
        except Exception as e:
            st.error(f"Error al limpiar: {e}")
            return False
    
    # Crear el formulario
    with st.form("formulario_completo", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">👤 Datos Personales</div>', unsafe_allow_html=True)
            
            # DNI: solo números, 8 dígitos - CON VALIDACIÓN EN PYTHON
            dni_input = st.text_input(
                "DNI*", 
                placeholder="Ej: 87654321 (solo 8 números)", 
                key="dni_input", 
                max_chars=8,
                help="Ingrese 8 dígitos numéricos"
            )
            
            # Validar DNI cuando el usuario presiona Enter o termina de escribir
            if dni_input:
                # FILTRAR: solo números
                dni_input = ''.join(filter(str.isdigit, dni_input))
                
                if not dni_input:
                    error_dni = "❌ Solo se permiten números"
                    st.markdown(f'<div style="color: #dc2626; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fee2e2; padding: 5px; border-radius: 4px;">{error_dni}</div>', unsafe_allow_html=True)
                elif len(dni_input) != 8:
                    error_dni = f"⚠️ Necesita {8 - len(dni_input)} dígito(s) más (8 en total)"
                    st.markdown(f'<div style="color: #d97706; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fef3c7; padding: 5px; border-radius: 4px;">{error_dni}</div>', unsafe_allow_html=True)
                else:
                    # Validar que no sea un DNI repetido
                    if 'verificar_duplicado' in globals() and verificar_duplicado(dni_input):
                        error_dni = "⚠️ Este DNI ya existe en la base de datos"
                        st.markdown(f'<div style="color: #d97706; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fef3c7; padding: 5px; border-radius: 4px;">{error_dni}</div>', unsafe_allow_html=True)
            
            # Nombre completo: solo letras y espacios - CON VALIDACIÓN EN PYTHON
            nombre_input = st.text_input(
                "Nombre Completo*", 
                placeholder="Ej: Ana García Pérez (solo letras)", 
                key="nombre_input",
                help="Ingrese solo letras, espacios y caracteres del español"
            )
            
            # Validación de nombre EN TIEMPO REAL
            if nombre_input:
                import re
                # FILTRAR: solo letras, espacios y caracteres especiales del español
                # Permitir letras, espacios, tildes, ñ, puntos, comas, guiones
                nombre_input = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-\.\,]', '', nombre_input)
                
                # Buscar números en el nombre (por si acaso)
                if re.search(r'\d', nombre_input):
                    error_nombre = "❌ No se permiten números en el nombre"
                    st.markdown(f'<div style="color: #dc2626; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fee2e2; padding: 5px; border-radius: 4px;">{error_nombre}</div>', unsafe_allow_html=True)
                elif len(nombre_input.strip().split()) < 2:
                    error_nombre = "⚠️ Ingrese al menos nombre y apellido"
                    st.markdown(f'<div style="color: #d97706; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fef3c7; padding: 5px; border-radius: 4px;">{error_nombre}</div>', unsafe_allow_html=True)
            
            # Edad, peso, talla
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24, key="edad_input")
            peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1, key="peso_input")
            talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1, key="talla_input")
            genero = st.selectbox("Género*", GENEROS, key="genero_input")
            
            # Teléfono: solo números, 9 dígitos - CON VALIDACIÓN EN PYTHON
            telefono_input = st.text_input(
                "Teléfono (9 dígitos)*", 
                placeholder="Ej: 987654321 (solo 9 números)", 
                key="telefono_input", 
                max_chars=9,
                help="Ingrese 9 dígitos numéricos"
            )
            
            # Validación de teléfono EN TIEMPO REAL
            if telefono_input:
                # FILTRAR: solo números
                telefono_input = ''.join(filter(str.isdigit, telefono_input))
                
                if not telefono_input:
                    error_telefono = "❌ Solo se permiten números"
                    st.markdown(f'<div style="color: #dc2626; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fee2e2; padding: 5px; border-radius: 4px;">{error_telefono}</div>', unsafe_allow_html=True)
                elif len(telefono_input) != 9:
                    error_telefono = f"⚠️ Necesita {9 - len(telefono_input)} dígito(s) más (9 en total)"
                    st.markdown(f'<div style="color: #d97706; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fef3c7; padding: 5px; border-radius: 4px;">{error_telefono}</div>', unsafe_allow_html=True)
                elif not telefono_input.startswith('9'):
                    error_telefono = "⚠️ Los números peruanos generalmente empiezan con 9"
                    st.markdown(f'<div style="color: #d97706; font-size: 0.9rem; margin-top: -15px; margin-bottom: 15px; background: #fef3c7; padding: 5px; border-radius: 4px;">{error_telefono}</div>', unsafe_allow_html=True)
            
            estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE, key="estado_input")
        
        with col2:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">🌍 Datos Geográficos</div>', unsafe_allow_html=True)
            region = st.selectbox("Región*", PERU_REGIONS, key="region_input")
            departamento = st.text_input("Departamento/Distrito", placeholder="Ej: Lima Metropolitana", key="departamento_input")
            
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
                
                altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, altitud_auto, key="altitud_input")
            else:
                altitud_msnm = st.number_input("Altitud (msnm)*", 0, 5000, 500, key="altitud_input")
            
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">💰 Factores Socioeconómicos del Apoderado</div>', unsafe_allow_html=True)
            nivel_educativo = st.selectbox("Nivel Educativo del Apoderado", NIVELES_EDUCATIVOS, key="nivel_input")
            acceso_agua_potable = st.checkbox("Acceso a agua potable", key="agua_input")
            tiene_servicio_salud = st.checkbox("Tiene servicio de salud", key="salud_input")
        
        st.markdown("---")
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">🩺 Parámetros Clínicos</div>', unsafe_allow_html=True)
            hemoglobina_medida = st.number_input("Hemoglobina medida (g/dL)*", 5.0, 20.0, 11.0, 0.1, key="hemoglobina_input")
            
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
            
            necesita_seguimiento = necesita_seguimiento_automatico(hemoglobina_ajustada, edad_meses)
            en_seguimiento = st.checkbox("Marcar para seguimiento activo", value=necesita_seguimiento, key="seguimiento_input")
            
            consume_hierro = st.checkbox("Consume suplemento de hierro", key="hierro_input")
            if consume_hierro:
                tipo_suplemento_hierro = st.text_input("Tipo de suplemento de hierro", placeholder="Ej: Sulfato ferroso", key="tipo_suplemento_input")
                frecuencia_suplemento = st.selectbox("Frecuencia de suplemento", FRECUENCIAS_SUPLEMENTO, key="frecuencia_input")
            else:
                tipo_suplemento_hierro = ""
                frecuencia_suplemento = ""
            
            antecedentes_anemia = st.checkbox("Antecedentes de anemia", key="antecedentes_input")
            enfermedades_cronicas = st.text_area("Enfermedades crónicas", placeholder="Ej: Asma, alergias, etc.", key="enfermedades_input")
        
        with col4:
            st.markdown('<div class="section-title-blue" style="font-size: 1.4rem;">📋 Factores de Riesgo</div>', unsafe_allow_html=True)
            
            st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">🏥 Factores Clínicos</div>', unsafe_allow_html=True)
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS, key="factores_clinicos_input")
            
            st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">💰 Factores Socioeconómicos del Apoderado</div>', unsafe_allow_html=True)
            factores_sociales = st.multiselect("Seleccione factores socioeconómicos:", [
                "Bajo nivel educativo del apoderado",
                "Ingresos familiares reducidos",
                "Hacinamiento en vivienda",
                "Acceso limitado a agua potable",
                "Zona rural o alejada",
                "Trabajo informal o precario del apoderado",
                "Falta de acceso a servicios básicos"
            ], key="factores_sociales_input")
    # ============================================
    # AGREGAR AQUÍ: PROGRAMA NACIONAL DE ALIMENTACIÓN
    # ============================================
    st.markdown('<div style="color: #1e40af; font-weight: 600; margin: 10px 0;">🍎 Programa Nacional de Alimentación</div>', unsafe_allow_html=True)
    programas_alimentacion = st.multiselect("Seleccione programa(s) de alimentación:", [
        "Cuna Más",
        "Qali Warma",
        "Otro programa social",
        "No participa en programas"
    ], key="programas_alimentacion_input")

    
        # Mostrar resumen de validación
        st.markdown("---")
        
        # Panel de estado de validación
        col_val1, col_val2, col_val3 = st.columns(3)
        
        with col_val1:
            if dni_input:
                if len(dni_input) == 8 and dni_input.isdigit():
                    st.success("✅ DNI válido")
                else:
                    st.error("❌ DNI inválido")
            else:
                st.info("ℹ️ Ingrese DNI")
        
        with col_val2:
            if nombre_input:
                import re
                if (not re.search(r'\d', nombre_input) and 
                    len(nombre_input.strip().split()) >= 2):
                    st.success("✅ Nombre válido")
                else:
                    st.error("❌ Nombre inválido")
            else:
                st.info("ℹ️ Ingrese nombre")
        
        with col_val3:
            if telefono_input:
                if len(telefono_input) == 9 and telefono_input.isdigit():
                    st.success("✅ Teléfono válido")
                else:
                    st.error("❌ Teléfono inválido")
            else:
                st.info("ℹ️ Ingrese teléfono")
        
        # Tres botones en una fila: Limpiar, Analizar, Guardar
        st.markdown("---")
        col_b1, col_b2, col_b3, col_b4 = st.columns([1, 1, 1, 2])
        
        with col_b1:
            btn_limpiar = st.form_submit_button(
                "🧹 Limpiar", 
                type="secondary", 
                use_container_width=True
            )
        
        with col_b2:
            # Deshabilitar botón Analizar si hay errores
            tiene_errores = any([error_dni, error_nombre, error_telefono])
            
            btn_analizar = st.form_submit_button(
                "📊 Analizar Riesgo", 
                type="primary", 
                use_container_width=True,
                disabled=tiene_errores
            )
        
        with col_b3:
            btn_guardar = st.form_submit_button(
                "💾 Guardar", 
                type="primary", 
                use_container_width=True,
                disabled=tiene_errores
            )



    
    # ============================================
    # ACCIONES FUERA DEL FORMULARIO
    # ============================================
    
    # Acción 1: Limpiar formulario
    if btn_limpiar:
        # Limpiar solo los datos analizados, no los campos del formulario
        if 'datos_analizados' in st.session_state:
            del st.session_state.datos_analizados
        st.success("✅ Datos analizados limpiados. Puede llenar un nuevo formulario.")
        # Opcional: puedes agregar un botón para recargar la página
        if st.button("🔄 Recargar formulario"):
            st.rerun()
    
    # Acción 2: Analizar Riesgo
    if btn_analizar:
        # Validar todos los campos primero
        errores_finales = []
        
        # Validar DNI
        if not dni_input:
            errores_finales.append("❌ El DNI es obligatorio")
        elif len(dni_input) != 8 or not dni_input.isdigit():
            errores_finales.append("❌ El DNI debe tener 8 dígitos exactos")
        
        # Validar Nombre
        if not nombre_input:
            errores_finales.append("❌ El nombre completo es obligatorio")
        elif any(char.isdigit() for char in nombre_input):
            errores_finales.append("❌ El nombre no debe contener números")
        elif len(nombre_input.strip().split()) < 2:
            errores_finales.append("❌ Ingrese al menos nombre y apellido")
        
        # Validar Teléfono
        if not telefono_input:
            errores_finales.append("❌ El teléfono es obligatorio")
        elif len(telefono_input) != 9 or not telefono_input.isdigit():
            errores_finales.append("❌ El teléfono debe tener 9 dígitos exactos")
        
        # Validar peso y talla razonables
        if peso_kg < 1.0:
            errores_finales.append("❌ El peso debe ser mayor a 1.0 kg")
        if talla_cm < 30.0:
            errores_finales.append("❌ La talla debe ser mayor a 30.0 cm")
        
        # Mostrar todos los errores si los hay
        if errores_finales:
            st.error("### ❌ Errores encontrados:")
            for error in errores_finales:
                st.error(error)
        else:
            # Si no hay errores, proceder con los cálculos
            try:
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
                
                # Guardar en session state para usar en el botón Guardar
                st.session_state.datos_analizados = {
                    "nivel_riesgo": nivel_riesgo,
                    "puntaje": puntaje,
                    "estado": estado,
                    "sugerencias": sugerencias,
                    "estado_peso": estado_peso,
                    "estado_talla": estado_talla,
                    "estado_nutricional": estado_nutricional,
                    "interpretacion_auto": interpretacion_auto,
                    "parametros_simulados": parametros_simulados
                }
                
                st.success("✅ Análisis completado. Puede guardar los datos.")
                resultado_mostrado = True
                    
            except Exception as e:
                st.error(f"❌ Error al procesar los datos: {str(e)}")
    
    # Acción 3: Guardar en Supabase
    if btn_guardar:
        # Verificar si se hizo el análisis primero
        if 'datos_analizados' not in st.session_state:
            st.error("⚠️ Primero debe hacer el análisis de riesgo antes de guardar")
        else:
            # Validar todos los campos primero
            errores_finales = []
            
            # Validar DNI
            if not dni_input:
                errores_finales.append("❌ El DNI es obligatorio")
            elif len(dni_input) != 8 or not dni_input.isdigit():
                errores_finales.append("❌ El DNI debe tener 8 dígitos exactos")
            
            # Validar Nombre
            if not nombre_input:
                errores_finales.append("❌ El nombre completo es obligatorio")
            elif any(char.isdigit() for char in nombre_input):
                errores_finales.append("❌ El nombre no debe contener números")
            elif len(nombre_input.strip().split()) < 2:
                errores_finales.append("❌ Ingrese al menos nombre y apellido")
            
            # Validar Teléfono
            if not telefono_input:
                errores_finales.append("❌ El teléfono es obligatorio")
            elif len(telefono_input) != 9 or not telefono_input.isdigit():
                errores_finales.append("❌ El teléfono debe tener 9 dígitos exactos")
            
            # Validar peso y talla razonables
            if peso_kg < 1.0:
                errores_finales.append("❌ El peso debe ser mayor a 1.0 kg")
            if talla_cm < 30.0:
                errores_finales.append("❌ La talla debe ser mayor a 30.0 cm")
            
            # Mostrar todos los errores si los hay
            if errores_finales:
                st.error("### ❌ Errores encontrados:")
                for error in errores_finales:
                    st.error(error)
            else:
                # GUARDAR EN SUPABASE
                if supabase:
                    with st.spinner("Verificando y guardando datos..."):
                        datos = st.session_state.datos_analizados
                        
                        record = {
                            "dni": dni_input.strip(),
                            "nombre_apellido": nombre_input.strip(),
                            "edad_meses": int(edad_meses),
                            "peso_kg": float(peso_kg),
                            "talla_cm": float(talla_cm),
                            "genero": genero,
                            "telefono": telefono_input.strip(),
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
                            "interpretacion_hematologica": datos["interpretacion_auto"]['interpretacion'],
                            "politicas_de_ris": region,
                            "riesgo": datos["nivel_riesgo"],
                            "fecha_alerta": datetime.now().strftime("%Y-%m-%d"),
                            "estado_alerta": datos["estado"],
                            "sugerencias": datos["sugerencias"],
                            "severidad_interpretacion": datos["interpretacion_auto"]['severidad']
                        }
                        
                        resultado = insertar_datos_supabase(record)
                        
                        if resultado:
                            if isinstance(resultado, dict) and resultado.get("status") == "duplicado":
                                st.error(f"❌ El DNI {dni_input} ya existe en la base de datos")
                                st.info("Por favor, use un DNI diferente o edite el registro existente")
                            else:
                                st.success("✅ Datos guardados en Supabase correctamente")
                                st.balloons()
                                
                                # Opción para limpiar después de guardar
                                col_clean1, col_clean2 = st.columns(2)
                                with col_clean1:
                                    if st.button("🧹 Limpiar y nuevo registro"):
                                        if 'datos_analizados' in st.session_state:
                                            del st.session_state.datos_analizados
                                        st.rerun()
                                with col_clean2:
                                    if st.button("📝 Continuar con mismo paciente"):
                                        st.info("Puede modificar los datos y guardar nuevamente")
                        else:
                            st.error("❌ Error al guardar en Supabase")
                else:
                    st.error("🔴 No hay conexión a Supabase")
# ==================================================
# PESTAÑA 2: SEGUIMIENTO CLÍNICO - VERSIÓN CORREGIDA
# ==================================================

with tab2:
    st.markdown('<div class="section-title-green">🔬 SISTEMA DE SEGUIMIENTO CLÍNICO COMPLETO</div>', unsafe_allow_html=True)
    
    # ============================================
    # INICIALIZACIÓN DE ESTADOS
    # ============================================
    
    if 'seguimiento_paciente' not in st.session_state:
        st.session_state.seguimiento_paciente = None
    
    if 'seguimiento_datos_pacientes' not in st.session_state:
        st.session_state.seguimiento_datos_pacientes = pd.DataFrame()
    
    if 'seguimiento_historial' not in st.session_state:
        st.session_state.seguimiento_historial = []
    
    # ============================================
    # FUNCIONES CORREGIDAS
    # ============================================
    
    def cargar_todos_pacientes():
        """Carga todos los pacientes desde Supabase"""
        try:
            with st.spinner("🔄 Cargando pacientes..."):
                response = supabase.table("alertas_hemoglobina").select("*").execute()
                
                if response.data:
                    df = pd.DataFrame(response.data)
                    
                    # Asegurar que las columnas necesarias existan
                    columnas_necesarias = ['dni', 'nombre_apellido', 'edad_meses', 'hemoglobina_dl1', 'region']
                    for col in columnas_necesarias:
                        if col not in df.columns:
                            df[col] = None
                    
                    st.session_state.seguimiento_datos_pacientes = df
                    return True
                else:
                    st.error("❌ No se encontraron pacientes en la base de datos")
                    return False
                    
        except Exception as e:
            st.error(f"❌ Error al cargar pacientes: {str(e)[:100]}")
            return False
    
    # ============================================
    # CREAR 3 PESTAÑAS INTERNAS
    # ============================================
    
    tab_seg1, tab_seg2, tab_seg3 = st.tabs([
        "🔍 Buscar Paciente", 
        "📝 Nuevo Seguimiento", 
        "📋 Historial Completo"
    ])
    
    # ============================================
    # PESTAÑA 1: BUSCAR PACIENTE - VERSIÓN CORREGIDA
    # ============================================
    
    with tab_seg1:
        st.header("🔍 BUSCAR PACIENTE PARA SEGUIMIENTO")
        
        # Botón para cargar pacientes
        if st.button("🔄 Cargar Todos los Pacientes", type="primary", use_container_width=True, key="btn_cargar_pacientes_seg1"):
            cargar_todos_pacientes()
        
        # Verificar si hay datos cargados
        if not st.session_state.seguimiento_datos_pacientes.empty:
            df = st.session_state.seguimiento_datos_pacientes
            
            # Búsqueda por DNI, nombre o región
            buscar = st.text_input("🔎 Buscar por nombre, DNI o región:", 
                                 placeholder="Ej: 'Mia' o '10096525' o 'LIMA'",
                                 key="buscar_paciente_input")
            
            if buscar:
                # Convertir a string para búsqueda
                mask = (
                    df['nombre_apellido'].astype(str).str.contains(buscar, case=False, na=False) |
                    df['dni'].astype(str).str.contains(buscar, na=False) |
                    df['region'].astype(str).str.contains(buscar, case=False, na=False)
                )
                df_filtrado = df[mask]
                
                # Si no hay resultados con búsqueda normal, intentar búsqueda exacta por DNI
                if df_filtrado.empty and buscar.isdigit():
                    mask_exact = df['dni'].astype(str) == buscar
                    df_filtrado = df[mask_exact]
            else:
                df_filtrado = df
            
            # Mostrar resultados
            if not df_filtrado.empty:
                st.write(f"📊 **{len(df_filtrado)} pacientes encontrados**")
                
                # Crear lista de selección
                opciones = []
                for _, row in df_filtrado.iterrows():
                    nombre = row.get('nombre_apellido', 'N/A')
                    dni = row.get('dni', 'N/A')
                    edad = row.get('edad_meses', 'N/A')
                    hb = row.get('hemoglobina_dl1', 'N/A')
                    
                    opcion_text = f"{nombre} - DNI: {dni} - Edad: {edad} meses - Hb: {hb} g/dL"
                    opciones.append((opcion_text, dni))
                
                # Selector
                if opciones:
                    opcion_seleccionada = st.selectbox(
                        "Seleccione un paciente:",
                        options=[op[0] for op in opciones],
                        placeholder="Elija un paciente de la lista...",
                        key="select_paciente_seguimiento"
                    )
                    
                    # Encontrar DNI seleccionado
                    dni_seleccionado = None
                    for opcion_text, dni in opciones:
                        if opcion_text == opcion_seleccionada:
                            dni_seleccionado = dni
                            break
                    
                    if dni_seleccionado:
                        paciente_info = df_filtrado[df_filtrado['dni'] == dni_seleccionado].iloc[0]
                        
                        # Mostrar información del paciente
                        st.markdown("---")
                        col_show1, col_show2 = st.columns(2)
                        
                        with col_show1:
                            st.markdown(f"""
                            <div style="background: #dbeafe; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                                <h4 style="margin: 0 0 10px 0; color: #1e40af;">👤 DATOS PERSONALES</h4>
                                <p><strong>Paciente:</strong> {paciente_info['nombre_apellido']}</p>
                                <p><strong>DNI:</strong> {paciente_info['dni']}</p>
                                <p><strong>Edad:</strong> {paciente_info['edad_meses']} meses</p>
                                <p><strong>Género:</strong> {paciente_info.get('genero', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_show2:
                            st.markdown(f"""
                            <div style="background: #d1fae5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                                <h4 style="margin: 0 0 10px 0; color: #059669;">🩺 DATOS CLÍNICOS</h4>
                                <p><strong>Hemoglobina:</strong> {paciente_info['hemoglobina_dl1']} g/dL</p>
                                <p><strong>Región:</strong> {paciente_info['region']}</p>
                                <p><strong>Estado:</strong> {paciente_info.get('estado_paciente', 'N/A')}</p>
                                <p><strong>Riesgo:</strong> {paciente_info.get('riesgo', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Botón para seleccionar
                        col_btn_sel1, col_btn_sel2 = st.columns(2)
                        
                        with col_btn_sel1:
                            if st.button("✅ Seleccionar este paciente", 
                                       use_container_width=True, 
                                       type="primary",
                                       key=f"btn_seleccionar_{dni_seleccionado}"):
                                
                                st.session_state.seguimiento_paciente = paciente_info.to_dict()
                                
                                # Cargar historial
                                try:
                                    response = supabase.table("seguimientos")\
                                        .select("*")\
                                        .eq("dni_paciente", str(dni_seleccionado))\
                                        .order("fecha_seguimiento", desc=True)\
                                        .execute()
                                    
                                    if response.data:
                                        st.session_state.seguimiento_historial = response.data
                                        cantidad = len(response.data)
                                    else:
                                        st.session_state.seguimiento_historial = []
                                        cantidad = 0
                                        
                                except Exception as e:
                                    st.session_state.seguimiento_historial = []
                                    cantidad = 0
                                    st.warning(f"⚠️ No se pudo cargar historial: {str(e)[:100]}")
                                
                                st.success(f"✅ Paciente seleccionado: {paciente_info['nombre_apellido']}")
                                st.info(f"📋 Se cargaron {cantidad} controles previos")
                                
                                time.sleep(1)
                                st.rerun()
                        
                        with col_btn_sel2:
                            if st.button("📋 Ver detalles completos", 
                                       use_container_width=True, 
                                       type="secondary",
                                       key=f"btn_detalles_{dni_seleccionado}"):
                                with st.expander("📄 Detalles completos del paciente", expanded=True):
                                    st.json(paciente_info.to_dict())
            else:
                st.info("🔍 No se encontraron pacientes con los criterios de búsqueda")
        else:
            st.info("👆 Presiona 'Cargar Todos los Pacientes' para buscar pacientes")

    # ============================================
    # PESTAÑA 2: NUEVO SEGUIMIENTO - VERSIÓN CORREGIDA
    # ============================================
    
    with tab_seg2:
        st.header("📝 NUEVO SEGUIMIENTO CLÍNICO")
        
        # Variable para controlar si se guardó exitosamente
        seguimiento_guardado = False
        
        # Verificar si hay paciente seleccionado
        if not st.session_state.seguimiento_paciente:
            st.warning("""
            ⚠️ **Primero debe seleccionar un paciente**
            
            Pasos:
            1. Ve a la pestaña **🔍 Buscar Paciente**
            2. Cargue los pacientes
            3. Seleccione un paciente de la lista
            4. Regrese aquí para crear el seguimiento
            """)
            
            if st.button("🔍 Ir a Buscar Paciente", 
                        use_container_width=True, 
                        key="btn_ir_buscar_paciente_seg2"):
                st.markdown("""
                <script>
                setTimeout(() => {
                    const tabs = document.querySelectorAll('button[role="tab"]');
                    if (tabs.length >= 2) {
                        tabs[1].click();
                    }
                }, 500);
                </script>
                """, unsafe_allow_html=True)
                st.rerun()
        else:
            paciente = st.session_state.seguimiento_paciente
            
            # Mostrar información del paciente
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown(f"""
                <div style="background: #dbeafe; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 10px 0; color: #1e40af;">📋 PACIENTE SELECCIONADO</h4>
                    <p><strong>Nombre:</strong> {paciente.get('nombre_apellido', 'N/A')}</p>
                    <p><strong>DNI:</strong> {paciente.get('dni', 'N/A')}</p>
                    <p><strong>Edad:</strong> {paciente.get('edad_meses', 'N/A')} meses</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_info2:
                st.markdown(f"""
                <div style="background: #d1fae5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 10px 0; color: #059669;">📊 DATOS CLÍNICOS</h4>
                    <p><strong>Hb actual:</strong> {paciente.get('hemoglobina_dl1', 'N/A')} g/dL</p>
                    <p><strong>Región:</strong> {paciente.get('region', 'N/A')}</p>
                    <p><strong>Estado:</strong> {paciente.get('estado_paciente', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Formulario de seguimiento CORREGIDO
            with st.form("form_seguimiento_corregido", clear_on_submit=True):
                st.subheader("📊 Datos del Control")
                
                # SOLO FECHA - SIN HORA
                fecha = st.date_input("Fecha del control*", 
                                     datetime.now().date(),
                                     key="fecha_seguimiento_corregida")
                
                col_hb, col_peso, col_talla = st.columns(3)
                with col_hb:
                    hemoglobina = st.number_input(
                        "Hemoglobina (g/dL)*", 
                        value=float(paciente.get('hemoglobina_dl1', 11.0)),
                        min_value=0.0, 
                        max_value=20.0, 
                        step=0.1,
                        key="hemoglobina_seguimiento_corregida"
                    )
                with col_peso:
                    peso = st.number_input(
                        "Peso (kg)*", 
                        value=float(paciente.get('peso_kg', 12.0)),
                        min_value=0.0, 
                        max_value=50.0, 
                        step=0.1,
                        key="peso_seguimiento_corregida"
                    )
                with col_talla:
                    talla = st.number_input(
                        "Talla (cm)*", 
                        value=float(paciente.get('talla_cm', 85.0)),
                        min_value=0.0, 
                        max_value=150.0, 
                        step=0.1,
                        key="talla_seguimiento_corregida"
                    )
                
                # Evaluar estado nutricional
                edad_paciente = paciente.get('edad_meses', 24)
                genero_paciente = paciente.get('genero', 'F')
                
                estado_peso, estado_talla, estado_nutricional = evaluar_estado_nutricional(
                    edad_paciente, peso, talla, genero_paciente
                )
                
                # Mostrar estado nutricional
                if estado_nutricional in ["DESNUTRICIÓN CRÓNICA", "DESNUTRICIÓN AGUDA"]:
                    st.error(f"**Estado nutricional:** {estado_nutricional}")
                elif estado_nutricional == "SOBREPESO":
                    st.warning(f"**Estado nutricional:** {estado_nutricional}")
                else:
                    st.success(f"**Estado nutricional:** {estado_nutricional}")
                
                st.caption(f"📏 **Peso:** {estado_peso} | **Talla:** {estado_talla}")
                
                # Campo NUEVO: Médico/Especialista responsable
                medico_responsable = st.text_input(
                    "Médico/Especialista responsable*",
                    placeholder="Nombre del médico que realiza el seguimiento",
                    key="medico_responsable_input"
                )
                
                tipo_seguimiento = st.selectbox(
                    "Tipo de seguimiento*",
                    ["Control rutinario", "Seguimiento por anemia", "Control nutricional", 
                     "Evaluación de tratamiento", "Consulta de urgencia", "Control de crecimiento"],
                    key="tipo_seguimiento_select_corregida"
                )
                
                observaciones = st.text_area(
                    "Observaciones clínicas*", 
                    placeholder="Describa el estado del paciente, síntomas, evolución, respuesta al tratamiento...",
                    height=100,
                    key="observaciones_seguimiento_corregida"
                )
                
                tratamiento = st.text_input(
                    "Tratamiento actual o prescrito", 
                    placeholder="Ej: Sulfato ferroso 15 mg/día, suplemento vitamínico...",
                    key="tratamiento_seguimiento_corregida"
                )
                
                proximo_control = st.date_input(
                    "Próximo control sugerido",
                    value=datetime.now().date() + timedelta(days=30),
                    key="proximo_control_input_corregida"
                )
                
                # Botones DENTRO del formulario (CORRECTOS)
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    submit = st.form_submit_button(
                        "💾 GUARDAR SEGUIMIENTO", 
                        type="primary", 
                        use_container_width=True,
                        key="btn_guardar_seguimiento_corregido"
                    )
                with col_btn2:
                    limpiar = st.form_submit_button(
                        "🧹 LIMPIAR FORMULARIO", 
                        type="secondary", 
                        use_container_width=True,
                        key="btn_limpiar_seguimiento_corregido"
                    )
                with col_btn3:
                    cancelar = st.form_submit_button(
                        "❌ CANCELAR", 
                        type="secondary", 
                        use_container_width=True,
                        key="btn_cancelar_seguimiento_corregido"
                    )
                
                # Procesar guardado - VERSIÓN CORREGIDA
                if submit:
                    # Validaciones
                    if not medico_responsable.strip():
                        st.error("⚠️ El médico responsable es obligatorio")
                    elif not observaciones.strip():
                        st.error("⚠️ Las observaciones clínicas son obligatorias")
                    else:
                        # PREPARAR DATOS CORRECTAMENTE
                        hemoglobina_ajustada = hemoglobina  # Puedes ajustar esta fórmula
                        
                        # Crear observaciones completas
                        observaciones_completas = f"""{observaciones}

DATOS ADICIONALES:
- Peso: {peso} kg ({estado_peso})
- Talla: {talla} cm ({estado_talla})
- Estado nutricional: {estado_nutricional}
- Frecuencia control sugerida: {proximo_control.strftime('%d/%m/%Y')}"""
                        
                        # CORRECCIÓN: Usar los nombres de columna correctos
                        datos = {
                            "dni_paciente": str(paciente.get('dni', '')),
                            "fecha_seguimiento": fecha.strftime('%Y-%m-%d'),  # SOLO FECHA
                            "tipo_seguimiento": tipo_seguimiento,
                            "hemoglobina_actual": hemoglobina,
                            "hemoglobina_ajustada": hemoglobina_ajustada,
                            "clasificacion_actual": estado_nutricional,
                            "observaciones": observaciones_completas,
                            "tratamiento_actual": tratamiento,
                            "usuario_responsable": medico_responsable,  # CORREGIDO: usar campo del formulario
                            "proximo_control": proximo_control.strftime('%Y-%m-%d'),
                            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # Guardar en Supabase
                        try:
                            response = supabase.table("seguimientos").insert(datos).execute()
                            
                            if response.data:
                                st.success("✅ Seguimiento guardado correctamente")
                                seguimiento_guardado = True
                                
                                # Actualizar historial en session state
                                if 'seguimiento_historial' not in st.session_state:
                                    st.session_state.seguimiento_historial = []
                                st.session_state.seguimiento_historial.insert(0, datos)
                                
                                # Actualizar hemoglobina en tabla principal
                                try:
                                    supabase.table("alertas_hemoglobina")\
                                        .update({"hemoglobina_dl1": hemoglobina})\
                                        .eq("dni", paciente.get('dni'))\
                                        .execute()
                                    st.info("🔄 Hemoglobina actualizada en registro principal")
                                except Exception as update_error:
                                    st.warning(f"⚠️ No se pudo actualizar hemoglobina: {str(update_error)[:50]}")
                                
                                st.balloons()
                                
                                # Mostrar resumen DENTRO del formulario (esto está permitido)
                                st.markdown("---")
                                col_res1, col_res2, col_res3 = st.columns(3)
                                with col_res1:
                                    st.metric("📅 Fecha", fecha.strftime('%d/%m/%Y'))
                                with col_res2:
                                    st.metric("🩺 Hb", f"{hemoglobina} g/dL")
                                with col_res3:
                                    st.metric("⚖️ Peso", f"{peso} kg")
                                
                                # Redirección automática con JavaScript
                                st.info("📋 Redirigiendo al historial en 3 segundos...")
                                
                                # Script para cambiar de pestaña automáticamente
                                st.markdown("""
                                <script>
                                setTimeout(() => {
                                    const tabs = document.querySelectorAll('button[role="tab"]');
                                    if (tabs.length >= 4) {
                                        tabs[3].click();
                                    }
                                }, 3000);
                                </script>
                                """, unsafe_allow_html=True)
                                
                            else:
                                st.error("❌ Error al guardar el seguimiento - Respuesta vacía del servidor")
                                
                        except Exception as e:
                            error_msg = str(e)
                            st.error(f"❌ Error al guardar: {error_msg[:200]}")
                            if "tratamiento_actual" in error_msg or "usuario_responsable" in error_msg:
                                st.error("⚠️ Problema con columnas de la base de datos. Ejecuta el ALTER TABLE en Supabase.")
                
                if limpiar:
                    st.info("🧹 Formulario limpiado")
                    time.sleep(1)
                    st.rerun()
                
                if cancelar:
                    st.info("❌ Seguimiento cancelado")
                    time.sleep(1)
                    st.rerun()
            
            # ============================================
            # BOTÓN FUERA DEL FORMULARIO (para redirección manual)
            # ============================================
            
            # Solo mostrar este botón si se guardó exitosamente
            if seguimiento_guardado:
                st.markdown("---")
                col_manual1, col_manual2 = st.columns(2)
                
                with col_manual1:
                    if st.button("📋 Ir al Historial Ahora", 
                               use_container_width=True, 
                               type="primary",
                               key="btn_ir_historial_manualmente"):
                        # Cambiar a pestaña de Historial usando JavaScript
                        st.markdown("""
                        <script>
                        setTimeout(() => {
                            const tabs = document.querySelectorAll('button[role="tab"]');
                            if (tabs.length >= 4) {
                                tabs[3].click();
                            }
                        }, 100);
                        </script>
                        """, unsafe_allow_html=True)
                        st.rerun()
                
                with col_manual2:
                    if st.button("📝 Crear otro seguimiento", 
                               use_container_width=True, 
                               type="secondary",
                               key="btn_otro_seguimiento"):
                        st.info("🔄 Limpiando formulario...")
                        time.sleep(1)
                        st.rerun()
# ==================================================
# PESTAÑA 3: DASHBOARD NACIONAL - SOLO AQUÍ DEBE ESTAR ESTE CÓDIGO
# ==================================================

with tab3:
    st.markdown("""
    <div class="main-title" style="background: linear-gradient(135deg, #059669 0%, #10b981 100%); padding: 2rem;">
        <h2 style="margin: 0; color: white;">📈 DASHBOARD NACIONAL DE ANEMIA</h2>
        <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9);">
        Análisis nacional, mapa interactivo por regiones, prevalencia y seguimiento
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============================================
    # FUNCIONES ESPECIALES PARA EL DASHBOARD
    # ============================================
    
    def calcular_indicadores_anemia(datos):
        """Calcula indicadores específicos de anemia"""
        if datos.empty:
            return {}
        
        # Asegurar que tenemos las columnas necesarias
        if 'hemoglobina_dl1' not in datos.columns:
            datos['hemoglobina_dl1'] = 11.0
        
        # Clasificar pacientes por nivel de anemia
        condiciones = [
            (datos['hemoglobina_dl1'] < 7.0),
            (datos['hemoglobina_dl1'] < 10.0),
            (datos['hemoglobina_dl1'] < 11.0),
            (datos['hemoglobina_dl1'] >= 11.0)
        ]
        
        categorias = ['SEVERA', 'MODERADA', 'LEVE', 'NORMAL']
        datos['nivel_anemia'] = np.select(condiciones, categorias, default='NORMAL')
        
        # Calcular indicadores nacionales
        total = len(datos)
        con_anemia = len(datos[datos['nivel_anemia'].isin(['SEVERA', 'MODERADA', 'LEVE'])])
        
        indicadores = {
            'total_pacientes': total,
            'con_anemia': con_anemia,
            'prevalencia_nacional': round((con_anemia / total * 100), 1) if total > 0 else 0,
            'severa': len(datos[datos['nivel_anemia'] == 'SEVERA']),
            'moderada': len(datos[datos['nivel_anemia'] == 'MODERADA']),
            'leve': len(datos[datos['nivel_anemia'] == 'LEVE']),
            'normal': len(datos[datos['nivel_anemia'] == 'NORMAL']),
            'en_seguimiento': datos['en_seguimiento'].sum() if 'en_seguimiento' in datos.columns else 0,
            'tasa_seguimiento': 0,
            'hb_promedio_nacional': datos['hemoglobina_dl1'].mean() if 'hemoglobina_dl1' in datos.columns else 0
        }
        
        # Calcular tasa de seguimiento
        if con_anemia > 0:
            anemia_df = datos[datos['nivel_anemia'].isin(['SEVERA', 'MODERADA', 'LEVE'])]
            if len(anemia_df) > 0:
                indicadores['tasa_seguimiento'] = round((anemia_df['en_seguimiento'].sum() / len(anemia_df)) * 100, 1)
        
        # Calcular por región
        if 'region' in datos.columns:
            region_stats = {}
            for region in datos['region'].unique():
                region_df = datos[datos['region'] == region]
                total_region = len(region_df)
                con_anemia_region = len(region_df[region_df['nivel_anemia'].isin(['SEVERA', 'MODERADA', 'LEVE'])])
                
                prevalencia_region = 0
                if total_region > 0:
                    prevalencia_region = round((con_anemia_region / total_region * 100), 1)
                
                region_stats[region] = {
                    'total': total_region,
                    'con_anemia': con_anemia_region,
                    'prevalencia': prevalencia_region,
                    'hb_promedio': region_df['hemoglobina_dl1'].mean() if 'hemoglobina_dl1' in region_df.columns else 0,
                    'severa': len(region_df[region_df['nivel_anemia'] == 'SEVERA']),
                    'moderada': len(region_df[region_df['nivel_anemia'] == 'MODERADA']),
                    'leve': len(region_df[region_df['nivel_anemia'] == 'LEVE']),
                    'en_seguimiento': region_df['en_seguimiento'].sum() if 'en_seguimiento' in region_df.columns else 0
                }
            
            indicadores['por_region'] = region_stats
        
        return indicadores
    
    def crear_mapa_peru(indicadores):
        """Crea un mapa del Perú con colores según prevalencia de anemia"""
        
        # Datos geográficos básicos de las regiones del Perú
        peru_geojson = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {"region": "AMAZONAS"}, "geometry": {"type": "Point", "coordinates": [-78.5, -5.2]}},
                {"type": "Feature", "properties": {"region": "ANCASH"}, "geometry": {"type": "Point", "coordinates": [-77.5, -9.5]}},
                {"type": "Feature", "properties": {"region": "APURIMAC"}, "geometry": {"type": "Point", "coordinates": [-72.9, -13.6]}},
                {"type": "Feature", "properties": {"region": "AREQUIPA"}, "geometry": {"type": "Point", "coordinates": [-71.5, -16.4]}},
                {"type": "Feature", "properties": {"region": "AYACUCHO"}, "geometry": {"type": "Point", "coordinates": [-74.2, -13.2]}},
                {"type": "Feature", "properties": {"region": "CAJAMARCA"}, "geometry": {"type": "Point", "coordinates": [-78.5, -7.2]}},
                {"type": "Feature", "properties": {"region": "CALLAO"}, "geometry": {"type": "Point", "coordinates": [-77.1, -12.0]}},
                {"type": "Feature", "properties": {"region": "CUSCO"}, "geometry": {"type": "Point", "coordinates": [-71.9, -13.5]}},
                {"type": "Feature", "properties": {"region": "HUANCAVELICA"}, "geometry": {"type": "Point", "coordinates": [-75.0, -12.8]}},
                {"type": "Feature", "properties": {"region": "HUANUCO"}, "geometry": {"type": "Point", "coordinates": [-76.2, -9.9]}},
                {"type": "Feature", "properties": {"region": "ICA"}, "geometry": {"type": "Point", "coordinates": [-75.7, -14.1]}},
                {"type": "Feature", "properties": {"region": "JUNIN"}, "geometry": {"type": "Point", "coordinates": [-75.0, -11.5]}},
                {"type": "Feature", "properties": {"region": "LA LIBERTAD"}, "geometry": {"type": "Point", "coordinates": [-79.0, -8.1]}},
                {"type": "Feature", "properties": {"region": "LAMBAYEQUE"}, "geometry": {"type": "Point", "coordinates": [-79.9, -6.7]}},
                {"type": "Feature", "properties": {"region": "LIMA"}, "geometry": {"type": "Point", "coordinates": [-77.0, -12.0]}},
                {"type": "Feature", "properties": {"region": "LORETO"}, "geometry": {"type": "Point", "coordinates": [-73.2, -3.7]}},
                {"type": "Feature", "properties": {"region": "MADRE DE DIOS"}, "geometry": {"type": "Point", "coordinates": [-69.2, -12.6]}},
                {"type": "Feature", "properties": {"region": "MOQUEGUA"}, "geometry": {"type": "Point", "coordinates": [-70.9, -17.2]}},
                {"type": "Feature", "properties": {"region": "PASCO"}, "geometry": {"type": "Point", "coordinates": [-76.2, -10.7]}},
                {"type": "Feature", "properties": {"region": "PIURA"}, "geometry": {"type": "Point", "coordinates": [-80.6, -5.2]}},
                {"type": "Feature", "properties": {"region": "PUNO"}, "geometry": {"type": "Point", "coordinates": [-70.0, -15.8]}},
                {"type": "Feature", "properties": {"region": "SAN MARTIN"}, "geometry": {"type": "Point", "coordinates": [-76.1, -6.5]}},
                {"type": "Feature", "properties": {"region": "TACNA"}, "geometry": {"type": "Point", "coordinates": [-70.2, -18.0]}},
                {"type": "Feature", "properties": {"region": "TUMBES"}, "geometry": {"type": "Point", "coordinates": [-80.5, -3.6]}},
                {"type": "Feature", "properties": {"region": "UCAYALI"}, "geometry": {"type": "Point", "coordinates": [-73.4, -8.4]}}
            ]
        }
        
        # Crear DataFrame para el mapa
        map_data = []
        if 'por_region' in indicadores:
            for region, stats in indicadores.get('por_region', {}).items():
                map_data.append({
                    'region': region,
                    'prevalencia': stats['prevalencia'],
                    'total_pacientes': stats['total'],
                    'con_anemia': stats['con_anemia'],
                    'hb_promedio': stats['hb_promedio'],
                    'lat': 0,
                    'lon': 0
                })
        
        # Asignar coordenadas desde el GeoJSON
        for feature in peru_geojson['features']:
            region_name = feature['properties']['region']
            coords = feature['geometry']['coordinates']
            
            for item in map_data:
                if item['region'] == region_name:
                    item['lon'] = coords[0]
                    item['lat'] = coords[1]
                    break
        
        return pd.DataFrame(map_data)
    
    # ============================================
    # INTERFAZ PRINCIPAL DEL DASHBOARD
    # ============================================
    
    # Botón para cargar datos
    col_btn1, col_btn2 = st.columns([2, 1])
    
    with col_btn1:
        if st.button("🔄 CARGAR DATOS NACIONALES", 
                    type="primary", 
                    use_container_width=True,
                    key="btn_cargar_datos_nacionales_tab3"):
            with st.spinner("Cargando datos nacionales..."):
                datos_nacionales = obtener_datos_supabase()
                
                if not datos_nacionales.empty:
                    # Calcular indicadores
                    indicadores = calcular_indicadores_anemia(datos_nacionales)
                    mapa_data = crear_mapa_peru(indicadores)
                    
                    st.session_state.datos_nacionales = datos_nacionales
                    st.session_state.indicadores_anemia = indicadores
                    st.session_state.mapa_peru = mapa_data
                    
                    st.success(f"✅ {len(datos_nacionales)} registros cargados - {indicadores['prevalencia_nacional']}% de prevalencia")
                else:
                    st.error("❌ No se pudieron cargar datos nacionales")
    
    with col_btn2:
        if st.button("🗺️ VER SOLO MAPA", 
                    type="secondary", 
                    use_container_width=True,
                    key="btn_ver_mapa_solo_tab3"):
            if 'mapa_peru' in st.session_state:
                st.session_state.modo_mapa = True
    
    # ============================================
    # MOSTRAR DASHBOARD SI HAY DATOS
    # ============================================
    
    if 'indicadores_anemia' in st.session_state and st.session_state.indicadores_anemia:
        indicadores = st.session_state.indicadores_anemia
        datos = st.session_state.datos_nacionales
        
        # ============================================
        # MÉTRICAS PRINCIPALES
        # ============================================
        
        st.markdown("""
        <div class="section-title-blue" style="font-size: 1.3rem;">
            🎯 INDICADORES NACIONALES DE ANEMIA
        </div>
        """, unsafe_allow_html=True)
        
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        
        with col_met1:
            prevalencia = indicadores['prevalencia_nacional']
            color = "#ef4444" if prevalencia >= 40 else "#f59e0b" if prevalencia >= 20 else "#10b981"
            emoji = "🔴" if prevalencia >= 40 else "🟡" if prevalencia >= 20 else "🟢"
            
            st.markdown(f"""
            <div class="metric-card-red" style="background: linear-gradient(135deg, {color}20 0%, {color}10 100%); border-left: 5px solid {color};">
                <div class="metric-label">PREVALENCIA NACIONAL</div>
                <div class="highlight-number" style="color: {color}; font-size: 2.5rem;">{emoji} {prevalencia}%</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                {indicadores['con_anemia']}/{indicadores['total_pacientes']} pacientes
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_met2:
            hb_promedio = indicadores['hb_promedio_nacional']
            hb_color = "#ef4444" if hb_promedio < 10 else "#f59e0b" if hb_promedio < 11 else "#10b981"
            hb_estado = "CRÍTICO" if hb_promedio < 10 else "RIESGO" if hb_promedio < 11 else "ADECUADO"
            
            st.markdown(f"""
            <div class="metric-card-purple" style="background: linear-gradient(135deg, {hb_color}20 0%, {hb_color}10 100%); border-left: 5px solid {hb_color};">
                <div class="metric-label">HEMOGLOBINA NACIONAL</div>
                <div class="highlight-number" style="color: {hb_color}; font-size: 2.5rem;">{hb_promedio:.1f} g/dL</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                Estado: {hb_estado}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_met3:
            tasa_seg = indicadores['tasa_seguimiento']
            seg_color = "#10b981" if tasa_seg >= 70 else "#f59e0b" if tasa_seg >= 40 else "#ef4444"
            seg_emoji = "✅" if tasa_seg >= 70 else "⚠️" if tasa_seg >= 40 else "❌"
            
            st.markdown(f"""
            <div class="metric-card-green" style="background: linear-gradient(135deg, {seg_color}20 0%, {seg_color}10 100%); border-left: 5px solid {seg_color};">
                <div class="metric-label">TASA SEGUIMIENTO</div>
                <div class="highlight-number" style="color: {seg_color}; font-size: 2.5rem;">{seg_emoji} {tasa_seg}%</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                {indicadores['en_seguimiento']} pacientes en control
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_met4:
            casos_severos = indicadores['severa']
            severo_color = "#dc2626" if casos_severos > 10 else "#f59e0b" if casos_severos > 5 else "#10b981"
            severo_porcentaje = (casos_severos / indicadores['con_anemia'] * 100) if indicadores['con_anemia'] > 0 else 0
            
            st.markdown(f"""
            <div class="metric-card-yellow" style="background: linear-gradient(135deg, {severo_color}20 0%, {severo_color}10 100%); border-left: 5px solid {severo_color};">
                <div class="metric-label">CASOS SEVEROS</div>
                <div class="highlight-number" style="color: {severo_color}; font-size: 2.5rem;">🚨 {casos_severos}</div>
                <div style="font-size: 0.9rem; color: #6b7280;">
                {severo_porcentaje:.1f}% de los casos
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # ============================================
        # MAPA INTERACTIVO DEL PERÚ + ESTADÍSTICO DE REGIÓN
        # ============================================
        
        st.markdown("""
        <div class="section-title-blue" style="font-size: 1.3rem;">
            🗺️ MAPA DE PREVALENCIA DE ANEMIA EN EL PERÚ
        </div>
        """, unsafe_allow_html=True)
        
        if 'mapa_peru' in st.session_state and not st.session_state.mapa_peru.empty:
            mapa_df = st.session_state.mapa_peru
            
            # ESTADÍSTICO: REGIÓN CON MÁS ANEMIA
            if not mapa_df.empty and 'prevalencia' in mapa_df.columns:
                # Encontrar la región con mayor prevalencia
                region_max_anemia = mapa_df.loc[mapa_df['prevalencia'].idxmax()]
                region_min_anemia = mapa_df.loc[mapa_df['prevalencia'].idxmin()]
                
                # Mostrar estadístico en columnas
                col_stat1, col_stat2, col_stat3 = st.columns([2, 1, 2])
                
                with col_stat1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #dc262620 0%, #dc262610 100%); 
                                padding: 1rem; border-radius: 10px; border-left: 5px solid #dc2626;">
                        <div style="font-weight: 600; color: #dc2626; margin-bottom: 0.5rem;">⚠️ MAYOR PREVALENCIA</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #dc2626;">
                        {region_max_anemia['region']}
                        </div>
                        <div style="font-size: 1rem; color: #6b7280;">
                        {region_max_anemia['prevalencia']}% de anemia
                        </div>
                        <div style="font-size: 0.9rem; color: #9ca3af;">
                        {region_max_anemia['con_anemia']}/{region_max_anemia['total_pacientes']} pacientes
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_stat2:
                    st.markdown("""
                    <div style="text-align: center; padding: 1rem;">
                        <div style="font-size: 2rem;">📊</div>
                        <div style="font-size: 0.9rem; color: #6b7280;">vs</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_stat3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #10b98120 0%, #10b98110 100%); 
                                padding: 1rem; border-radius: 10px; border-left: 5px solid #10b981;">
                        <div style="font-weight: 600; color: #10b981; margin-bottom: 0.5rem;">✅ MENOR PREVALENCIA</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #10b981;">
                        {region_min_anemia['region']}
                        </div>
                        <div style="font-size: 1rem; color: #6b7280;">
                        {region_min_anemia['prevalencia']}% de anemia
                        </div>
                        <div style="font-size: 0.9rem; color: #9ca3af;">
                        {region_min_anemia['con_anemia']}/{region_min_anemia['total_pacientes']} pacientes
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # MAPA INTERACTIVO
            fig_mapa = px.scatter_mapbox(
                mapa_df,
                lat="lat",
                lon="lon",
                color="prevalencia",
                size="total_pacientes",
                hover_name="region",
                hover_data={
                    "prevalencia": ":.1f%",
                    "total_pacientes": True,
                    "con_anemia": True,
                    "hb_promedio": ":.1f"
                },
                color_continuous_scale="RdYlGn_r",
                range_color=[0, 100],
                size_max=30,
                zoom=4.5,
                center={"lat": -9.19, "lon": -75.0},
                title="<b>Prevalencia de Anemia por Región</b>",
                mapbox_style="carto-positron"
            )
            
            fig_mapa.update_layout(
                height=500, 
                margin={"r":0,"t":40,"l":0,"b":0},
                coloraxis_colorbar=dict(
                    title="Prevalencia (%)",
                    ticksuffix="%"
                )
            )
            
            st.plotly_chart(fig_mapa, use_container_width=True)
            
            # Leyenda del mapa
            col_leg1, col_leg2, col_leg3 = st.columns(3)
            with col_leg1:
                st.markdown("""
                <div style="background: #d73027; color: white; padding: 10px; border-radius: 8px; text-align: center; margin: 5px;">
                    🔴 Alta prevalencia (>40%)
                </div>
                """, unsafe_allow_html=True)
            with col_leg2:
                st.markdown("""
                <div style="background: #fdae61; color: black; padding: 10px; border-radius: 8px; text-align: center; margin: 5px;">
                    🟡 Media prevalencia (20-40%)
                </div>
                """, unsafe_allow_html=True)
            with col_leg3:
                st.markdown("""
                <div style="background: #a6d96a; color: black; padding: 10px; border-radius: 8px; text-align: center; margin: 5px;">
                    🟢 Baja prevalencia (<20%)
                </div>
                """, unsafe_allow_html=True)
        
        # ============================================
        # GRÁFICOS DE DISTRIBUCIÓN
        # ============================================
        
        st.markdown("""
        <div class="section-title-blue" style="font-size: 1.3rem;">
            📈 DISTRIBUCIÓN Y TENDENCIAS
        </div>
        """, unsafe_allow_html=True)
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            # Gráfico de niveles de anemia
            niveles_data = {
                'SEVERA': indicadores['severa'],
                'MODERADA': indicadores['moderada'],
                'LEVE': indicadores['leve'],
                'NORMAL': indicadores['normal']
            }
            
            fig_niveles = px.bar(
                x=list(niveles_data.keys()),
                y=list(niveles_data.values()),
                title='<b>Distribución por Nivel de Anemia</b>',
                color=list(niveles_data.keys()),
                color_discrete_map={
                    'SEVERA': '#dc2626',
                    'MODERADA': '#f59e0b',
                    'LEVE': '#3b82f6',
                    'NORMAL': '#10b981'
                },
                text=list(niveles_data.values())
            )
            
            fig_niveles.update_traces(
                texttemplate='%{y}',
                textposition='outside'
            )
            
            fig_niveles.update_layout(
                xaxis_title="Nivel de Anemia",
                yaxis_title="Número de Pacientes",
                showlegend=False,
                height=350
            )
            
            st.plotly_chart(fig_niveles, use_container_width=True)
        
        with col_graf2:
            # Gráfico SIMPLE de género - SOLO cuenta F y M
            if 'genero' in datos.columns:
                # Limpiar datos: solo tomar F y M exactos
                datos_genero = datos['genero'].astype(str).str.upper().str.strip()
                
                # Filtrar SOLO F y M exactos
                genero_filtrado = datos_genero[datos_genero.isin(['F', 'M'])]
                
                # Contar
                conteo_genero = genero_filtrado.value_counts()
                
                # Asegurar que aparezcan ambos géneros aunque sea 0
                if 'M' not in conteo_genero:
                    conteo_genero['M'] = 0
                if 'F' not in conteo_genero:
                    conteo_genero['F'] = 0
                
                # Ordenar: M primero, F después
                conteo_genero = conteo_genero.reindex(['M', 'F'])
                
                # Crear gráfico de pastel
                labels = ['Niños 👦', 'Niñas 👧']
                valores = [conteo_genero.get('M', 0), conteo_genero.get('F', 0)]
                
                fig_genero = px.pie(
                    values=valores,
                    names=labels,
                    title='<b>Distribución por Género</b><br><sub>Contando solo F y M exactos</sub>',
                    color_discrete_sequence=['#3b82f6', '#ef4444'],
                    height=350
                )
                
                # Agregar total en el centro
                total_genero = sum(valores)
                fig_genero.update_layout(
                    annotations=[
                        dict(
                            text=f'Total: {total_genero}',
                            x=0.5, y=0.5,
                            font_size=14,
                            showarrow=False,
                            font=dict(color='gray')
                        )
                    ]
                )
                
                st.plotly_chart(fig_genero, use_container_width=True)
                
                # Mostrar métricas simples
                col_gen1, col_gen2 = st.columns(2)
                with col_gen1:
                    niños = conteo_genero.get('M', 0)
                    porcentaje_niños = (niños/total_genero*100) if total_genero > 0 else 0
                    st.metric("Niños 👦", niños, delta=f"{porcentaje_niños:.1f}%")
                
                with col_gen2:
                    niñas = conteo_genero.get('F', 0)
                    porcentaje_niñas = (niñas/total_genero*100) if total_genero > 0 else 0
                    st.metric("Niñas 👧", niñas, delta=f"{porcentaje_niñas:.1f}%")
                
                # Mostrar info si hay pacientes sin F/M
                pacientes_sin_fm = len(datos) - total_genero
                if pacientes_sin_fm > 0:
                    st.caption(f"ℹ️ {pacientes_sin_fm} paciente(s) no tienen 'F' o 'M' en la columna 'genero'")
            
            else:
                st.info("📊 La columna 'genero' no está presente en los datos")

        # ============================================
        # TABLA DE REGIONES
        # ============================================
        
        st.markdown("""
        <div class="section-title-blue" style="font-size: 1.3rem;">
            📊 RANKING DE REGIONES POR PREVALENCIA
        </div>
        """, unsafe_allow_html=True)
        
        if 'por_region' in indicadores and indicadores['por_region']:
            # Crear DataFrame para ranking
            ranking_data = []
            for region, stats in indicadores['por_region'].items():
                if stats['total'] > 0:
                    tasa_seguimiento_region = 0
                    if stats['con_anemia'] > 0:
                        tasa_seguimiento_region = round((stats['en_seguimiento'] / stats['con_anemia'] * 100), 1)
                    
                    ranking_data.append({
                        'Región': region,
                        'Prevalencia (%)': stats['prevalencia'],
                        'Total': stats['total'],
                        'Con Anemia': stats['con_anemia'],
                        'Hb Promedio': f"{stats['hb_promedio']:.1f}",
                        'Severa': stats['severa'],
                        'En Seguimiento': stats['en_seguimiento'],
                        'Tasa Seg (%)': tasa_seguimiento_region
                    })
            
            if ranking_data:
                ranking_df = pd.DataFrame(ranking_data)
                ranking_df = ranking_df.sort_values('Prevalencia (%)', ascending=False)
                
                # Mostrar tabla con formato mejorado
                st.dataframe(
                    ranking_df,
                    use_container_width=True,
                    height=300,
                    column_config={
                        "Región": st.column_config.TextColumn("Región", width="medium"),
                        "Prevalencia (%)": st.column_config.NumberColumn("Prevalencia", format="%.1f%%"),
                        "Total": st.column_config.NumberColumn("Total", format="%d"),
                        "Con Anemia": st.column_config.NumberColumn("Con Anemia", format="%d"),
                        "Hb Promedio": st.column_config.NumberColumn("Hb Prom", format="%.1f"),
                        "Severa": st.column_config.NumberColumn("Severa", format="%d"),
                        "Tasa Seg (%)": st.column_config.NumberColumn("Tasa Seg", format="%.1f%%")
                    }
                )

               # ============================================
        # 📊 ESTADÍSTICAS NACIONALES ADICIONALES
        # ============================================
        
        st.markdown("""
        <div class="section-title-blue" style="font-size: 1.3rem;">
            📊 ESTADÍSTICAS NACIONALES ADICIONALES
        </div>
        """, unsafe_allow_html=True)

        # Contenedor para estadísticas
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

        with col_stat1:
            # Estadística: Edad promedio
            if 'edad_meses' in datos.columns:
                edad_prom = datos['edad_meses'].mean()
                st.metric(
                    "👶 Edad Promedio", 
                    f"{edad_prom:.1f} meses",
                    help="Edad promedio de los pacientes registrados"
                )
            else:
                st.metric("👶 Edad Promedio", "N/A")

        with col_stat2:
            # Estadística: Tasa de seguimiento
            tasa_seguimiento = indicadores['tasa_seguimiento']
            st.metric(
                "📋 Tasa Seguimiento", 
                f"{tasa_seguimiento}%",
                delta=f"{indicadores['en_seguimiento']} pacientes"
            )

        with col_stat3:
            # Estadística: Proporción anemia severa
            if indicadores['con_anemia'] > 0:
                prop_severa = (indicadores['severa'] / indicadores['con_anemia']) * 100
                st.metric(
                    "⚠️ Anemia Severa", 
                    f"{prop_severa:.1f}%",
                    help="Proporción de casos severos entre pacientes con anemia"
                )
            else:
                st.metric("⚠️ Anemia Severa", "0%")

        with col_stat4:
            # Estadística: Meta OMS
            meta_oms = 20  # Meta OMS es <20%
            
            # Convertir a número para poder calcular diferencia
            try:
                # Asegurar que prevalencia_nacional sea número
                prevalencia_num = float(indicadores['prevalencia_nacional'])
                diferencia = prevalencia_num - meta_oms
                
                # Formatear correctamente
                valor_formateado = f"{diferencia:+.1f}%"
                
                st.metric(
                    "🎯 Meta OMS", 
                    valor_formateado,
                    help="Diferencia respecto a la meta OMS (<20%). Positivo = sobre la meta"
                )
            except (ValueError, TypeError) as e:
                # Si hay error, mostrar valor simple
                st.metric(
                    "🎯 Meta OMS", 
                    "Error cálculo",
                    help=f"No se pudo calcular: {str(e)[:30]}"
                )

        # Línea separadora
        st.markdown("---")

        # ============================================
        # 📥 EXPORTAR REPORTES CON PDF
        # ============================================
        
        st.markdown("""
        <div class="section-title-blue" style="font-size: 1.3rem;">
            📥 EXPORTAR REPORTES
        </div>
        """, unsafe_allow_html=True)

        # Contenedor para exportación
        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

        # COLUMNA 1: Datos completos
        with col_exp1:
            csv_full = datos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Datos Completos (CSV)",
                data=csv_full,
                file_name=f"datos_anemia_nacional_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary",
                key="btn_download_full_tab3"
            )

        # COLUMNA 2: Indicadores por región
        with col_exp2:
            try:
                if 'por_region' in indicadores and indicadores['por_region']:
                    reporte_data = []
                    for region, stats in indicadores['por_region'].items():
                        reporte_data.append({
                            'Región': region,
                            'Prevalencia (%)': stats['prevalencia'],
                            'Total Pacientes': stats['total'],
                            'Con Anemia': stats['con_anemia'],
                            'Hb Promedio': stats['hb_promedio'],
                            'Anemia Severa': stats['severa'],
                            'Anemia Moderada': stats['moderada'],
                            'Anemia Leve': stats['leve'],
                            'En Seguimiento': stats['en_seguimiento']
                        })
                    
                    if reporte_data:
                        reporte_df = pd.DataFrame(reporte_data)
                        csv_indicadores = reporte_df.to_csv(index=False).encode('utf-8')
                        
                        st.download_button(
                            label="📈 Indicadores (CSV)",
                            data=csv_indicadores,
                            file_name=f"indicadores_anemia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            type="secondary",
                            key="btn_download_indicadores_tab3"
                        )
                else:
                    st.download_button(
                        label="📈 Indicadores (CSV)",
                        data="No hay datos regionales".encode('utf-8'),
                        file_name="sin_datos.csv",
                        mime="text/csv",
                        use_container_width=True,
                        disabled=True,
                        key="btn_no_data_tab3"
                    )
            except Exception as e:
                st.error(f"Error en datos: {str(e)[:50]}")

        # COLUMNA 3: Informe ejecutivo (PDF + CSV)
        with col_exp3:
            col_pdf, col_csv = st.columns(2)
            
            with col_pdf:
                # Botón para generar PDF
                if st.button("📄 Generar PDF",
                            use_container_width=True,
                            type="primary",
                            key="btn_generar_pdf_nacional_tab3"):
                    
                    with st.spinner("Generando informe PDF..."):
                        try:
                            # Verificar que la función existe
                            pdf_bytes = generar_pdf_dashboard_nacional(
                                indicadores=indicadores,
                                datos=datos,
                                mapa_df=st.session_state.get('mapa_peru', None)
                            )
                            
                            # Mostrar botón de descarga
                            st.download_button(
                                label="📥 Descargar PDF",
                                data=pdf_bytes,
                                file_name=f"dashboard_anemia_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="btn_download_pdf_nacional_tab3"
                            )
                            
                        except NameError:
                            st.error("❌ La función 'generar_pdf_dashboard_nacional' no está definida")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)[:100]}")
            
            with col_csv:
                # Crear CSV simple
                informe_csv = f"""INFORME NACIONAL DE ANEMIA
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

RESUMEN NACIONAL
Total Pacientes,{indicadores['total_pacientes']}
Prevalencia Nacional,{indicadores['prevalencia_nacional']}%
Con Anemia,{indicadores['con_anemia']}
Hb Promedio,{indicadores['hb_promedio_nacional']:.1f} g/dL
Tasa Seguimiento,{indicadores['tasa_seguimiento']}%

DISTRIBUCIÓN POR GRAVEDAD
Anemia Severa,{indicadores['severa']}
Anemia Moderada,{indicadores['moderada']}
Anemia Leve,{indicadores['leve']}
Normal,{indicadores['normal']}
"""
                
                # Agregar regiones si existen
                if 'por_region' in indicadores:
                    informe_csv += "\nDATOS POR REGIÓN\nRegion,Prevalencia(%),Total,Con_Anemia,Hb_Promedio\n"
                    for region, stats in indicadores['por_region'].items():
                        informe_csv += f"{region},{stats['prevalencia']}%,{stats['total']},{stats['con_anemia']},{stats['hb_promedio']:.1f}\n"
                
                st.download_button(
                    label="📊 Descargar CSV",
                    data=informe_csv.encode('utf-8'),
                    file_name=f"informe_anemia_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="secondary",
                    key="btn_download_csv_informe_tab3"
                )

        # COLUMNA 4: Resumen para portapapeles
        with col_exp4:
            # Crear texto para portapapeles
            resumen_texto = f"""📊 RESUMEN ANEMIA NACIONAL
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📈 INDICADORES:
• Total: {indicadores['total_pacientes']} pacientes
• Prevalencia: {indicadores['prevalencia_nacional']}%
• Con anemia: {indicadores['con_anemia']}
• Hb promedio: {indicadores['hb_promedio_nacional']:.1f} g/dL
• Tasa seguimiento: {indicadores['tasa_seguimiento']}%

🎯 DISTRIBUCIÓN:
• Severa: {indicadores['severa']}
• Moderada: {indicadores['moderada']}
• Leve: {indicadores['leve']}
• Normal: {indicadores['normal']}

---
Sistema Nacional de Monitoreo de Anemia"""
            
            # Mostrar código para copiar manualmente
            if st.button("📋 Copiar Resumen",
                        use_container_width=True,
                        type="secondary",
                        key="btn_copiar_resumen_tab3"):
                st.code(resumen_texto, language="text")
                st.success("✅ Copia el texto de arriba manualmente")

        # ============================================
        # 📌 INFORMACIÓN ADICIONAL
        # ============================================
        
        with st.expander("📌 **INFORMACIÓN TÉCNICA DEL DASHBOARD**", expanded=False):
            st.markdown("""
            **Definiciones utilizadas:**
            
            **Prevalencia de anemia:** Porcentaje de pacientes con hemoglobina < 11 g/dL (OMS)
            
            **Clasificación por niveles:**
            - **Anemia severa:** Hb < 7 g/dL
            - **Anemia moderada:** Hb 7-9.9 g/dL  
            - **Anemia leve:** Hb 10-10.9 g/dL
            - **Normal:** Hb ≥ 11 g/dL
            
            **Indicadores de seguimiento:**
            - **Tasa de seguimiento:** % de pacientes con anemia que están en control activo
            - **Meta OMS:** Prevalencia < 20% en población infantil
            
            **Interpretación de colores en el mapa:**
            - 🔴 **Rojo:** Prevalencia > 40% (Alta prioridad)
            - 🟡 **Amarillo:** Prevalencia 20-40% (Atención requerida)
            - 🟢 **Verde:** Prevalencia < 20% (Dentro de meta OMS)
            
            **Fuentes de datos:**
            - Sistema Nixon v2.0
            - Base de datos nacional consolidada
            - Criterios OMS para diagnóstico de anemia
            - Coordenadas aproximadas de regiones del Perú
            """)
    
    else:
        # ============================================
        # SIN DATOS CARGADOS
        # ============================================
        
        col_empty1, col_empty2, col_empty3 = st.columns([1, 2, 1])
        
        with col_empty2:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); 
                        border-radius: 15px; border: 2px dashed #cbd5e1; margin: 2rem 0;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🗺️</div>
                <h3 style="color: #1e3a8a; margin-bottom: 1rem;">DASHBOARD NACIONAL DE ANEMIA</h3>
                <p style="color: #64748b; margin-bottom: 2rem;">
                Visualiza la prevalencia de anemia en todo el Perú con mapas interactivos, 
                indicadores regionales y análisis comparativos.
                </p>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem;">
                    <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.5rem;">🗺️</div>
                        <div style="font-weight: 600; color: #1e40af;">Mapa Interactivo</div>
                        <div style="font-size: 0.9rem; color: #64748b;">Visual por regiones</div>
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.5rem;">📊</div>
                        <div style="font-weight: 600; color: #059669;">Indicadores</div>
                        <div style="font-size: 0.9rem; color: #64748b;">Prevalencia y seguimiento</div>
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.5rem;">📈</div>
                        <div style="font-weight: 600; color: #d97706;">Ranking Regional</div>
                        <div style="font-size: 0.9rem; color: #64748b;">Comparativa por región</div>
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0;">
                        <div style="font-size: 1.5rem;">📥</div>
                        <div style="font-weight: 600; color: #7c3aed;">Reportes</div>
                        <div style="font-size: 0.9rem; color: #64748b;">Exportación de datos</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("👆 **Presiona 'CARGAR DATOS NACIONALES' para visualizar el dashboard completo**")
            
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
