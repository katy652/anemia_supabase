import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile

# ==================================================
# CONFIGURACIÓN INICIAL
# ==================================================
st.set_page_config(
    page_title="Sistema Nacional de Control de Anemia",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================================================
# ESTILOS CSS
# ==================================================
st.markdown("""
<style>
    /* Estilos generales */
    .main {
        padding: 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    }
    
    /* Contenedor principal dividido */
    .split-container {
        display: flex;
        min-height: 100vh;
    }
    
    .left-panel {
        flex: 1;
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        color: white;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .right-panel {
        flex: 1;
        background: white;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Estilos del dashboard */
    .dashboard-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
    }
    
    .dashboard-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 2rem;
        color: #dbeafe;
        text-align: center;
    }
    
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        backdrop-filter: blur(10px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.8;
        color: #dbeafe;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        color: white;
        text-align: center;
    }
    
    /* Estilos del login */
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        width: 100%;
    }
    
    .login-title {
        color: #1e3a8a;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .login-subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 2rem;
        text-align: center;
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
        width: 100%;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(30, 64, 175, 0.3);
    }
    
    /* Botón de descarga PDF */
    .pdf-button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 15px 30px;
        border-radius: 10px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        margin-top: 2rem;
        width: 100%;
        text-align: center;
        display: block;
        transition: all 0.3s ease;
    }
    
    .pdf-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
    }
    
    /* Separador */
    .divider {
        height: 2px;
        background: rgba(255, 255, 255, 0.2);
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .split-container {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# FUNCIONES PARA GENERAR PDF
# ==================================================

def create_pdf_report():
    """Crea un reporte PDF del dashboard nacional"""
    
    # Crear un buffer para el PDF
    buffer = BytesIO()
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=30,
        alignment=1  # Centrado
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=20,
        alignment=1
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=15
    )
    
    # Título del reporte
    elements.append(Paragraph("SISTEMA NACIONAL DE CONTROL DE ANEMIA", title_style))
    elements.append(Paragraph(f"Reporte Nacional - {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Métricas nacionales
    elements.append(Paragraph("INDICADORES NACIONALES", section_style))
    
    # Datos para la tabla de métricas
    metric_data = [
        ['INDICADOR', 'VALOR', 'DESCRIPCIÓN'],
        ['Niños Evaluados', '15,243', 'Total a nivel nacional'],
        ['Prevalencia Anemia', '28.5%', 'En menores de 5 años'],
        ['Regiones Activas', '24', 'De 25 regiones'],
        ['Hemoglobina Promedio', '10.3 g/dL', 'Ajustado por altitud'],
        ['Casos en Seguimiento', '3,825', '25.1% del total'],
        ['Meta 2024', '≤20%', 'Reducción de prevalencia']
    ]
    
    metric_table = Table(metric_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 1), (-1, -1), 6),
    ]))
    
    elements.append(metric_table)
    elements.append(Spacer(1, 30))
    
    # Distribución por región
    elements.append(Paragraph("DISTRIBUCIÓN POR REGIÓN", section_style))
    
    # Datos regionales
    region_data = [
        ['REGIÓN', 'CASOS', 'PREVALENCIA', 'ESTADO'],
        ['Puno', '1,245', '45.6%', '🔴 Alto'],
        ['Huancavelica', '987', '42.3%', '🔴 Alto'],
        ['Cusco', '1,089', '38.2%', '🟡 Medio'],
        ['Apurímac', '876', '37.8%', '🟡 Medio'],
        ['Ayacucho', '754', '35.2%', '🟡 Medio'],
        ['Piura', '1,342', '32.1%', '🟡 Medio'],
        ['Loreto', '890', '29.7%', '🟢 Bajo'],
        ['Amazonas', '543', '28.4%', '🟢 Bajo'],
        ['Lima', '2,145', '25.3%', '🟢 Bajo'],
        ['Arequipa', '654', '22.4%', '🟢 Bajo']
    ]
    
    region_table = Table(region_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
    region_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('PADDING', (0, 1), (-1, -1), 5),
    ]))
    
    elements.append(region_table)
    elements.append(Spacer(1, 30))
    
    # Análisis y recomendaciones
    elements.append(Paragraph("ANÁLISIS Y RECOMENDACIONES", section_style))
    
    recommendations = [
        "1. **Fortalecer intervenciones en regiones con alta prevalencia** (Puno, Huancavelica)",
        "2. **Aumentar cobertura de suplementación con hierro** en menores de 3 años",
        "3. **Implementar estrategias de educación nutricional** a nivel familiar",
        "4. **Fortalecer el sistema de monitoreo y seguimiento** de casos",
        "5. **Promover prácticas de alimentación complementaria** adecuada",
        "6. **Incrementar acceso a servicios de salud** en zonas rurales"
    ]
    
    for rec in recommendations:
        elements.append(Paragraph(rec, styles['Normal']))
        elements.append(Spacer(1, 5))
    
    elements.append(Spacer(1, 20))
    
    # Información del reporte
    footer_text = f"""
    <para>
    <font color='#6b7280' size='9'>
    <b>Generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')} | 
    <b>Sistema:</b> Sistema Nacional de Control de Anemia | 
    <b>Contacto:</b> anemia@minsa.gob.pe
    </font>
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Construir el PDF
    doc.build(elements)
    
    # Obtener el PDF del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def get_pdf_download_link(pdf_bytes, filename):
    """Genera un enlace para descargar el PDF"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" class="pdf-button">📥 DESCARGAR REPORTE NACIONAL (PDF)</a>'
    return href

# ==================================================
# SISTEMA DE LOGIN
# ==================================================

# Configurar estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

# Diccionario de usuarios (5 profesionales de salud)
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

def verificar_login(username, password):
    """Verifica si el usuario y contraseña son correctos"""
    if username in USUARIOS_SALUD and USUARIOS_SALUD[username]["password"] == password:
        return USUARIOS_SALUD[username]
    return None

# ==================================================
# DATOS DEL DASHBOARD NACIONAL
# ==================================================

def get_national_data():
    """Obtiene datos para el dashboard nacional"""
    
    # Métricas principales
    metrics = {
        "total_evaluados": "15,243",
        "prevalencia_anemia": "28.5%",
        "regiones_activas": "24",
        "hemoglobina_promedio": "10.3 g/dL",
        "casos_seguimiento": "3,825",
        "meta_2024": "≤20%"
    }
    
    # Datos por región
    region_data = [
        {"region": "Puno", "casos": 1245, "prevalencia": 45.6, "estado": "Alto"},
        {"region": "Huancavelica", "casos": 987, "prevalencia": 42.3, "estado": "Alto"},
        {"region": "Cusco", "casos": 1089, "prevalencia": 38.2, "estado": "Medio"},
        {"region": "Apurímac", "casos": 876, "prevalencia": 37.8, "estado": "Medio"},
        {"region": "Ayacucho", "casos": 754, "prevalencia": 35.2, "estado": "Medio"},
        {"region": "Piura", "casos": 1342, "prevalencia": 32.1, "estado": "Medio"},
        {"region": "Loreto", "casos": 890, "prevalencia": 29.7, "estado": "Bajo"},
        {"region": "Amazonas", "casos": 543, "prevalencia": 28.4, "estado": "Bajo"},
        {"region": "Lima", "casos": 2145, "prevalencia": 25.3, "estado": "Bajo"},
        {"region": "Arequipa", "casos": 654, "prevalencia": 22.4, "estado": "Bajo"}
    ]
    
    # Datos para gráfico
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    casos_mensuales = [1450, 1320, 1280, 1245, 1190, 1150, 1250, 1300, 1275, 1220, 1180, 1145]
    prevalencia_mensual = [30.2, 29.8, 29.1, 28.5, 28.0, 27.6, 28.5, 29.0, 28.8, 28.3, 27.9, 27.5]
    
    return metrics, region_data, meses, casos_mensuales, prevalencia_mensual

# ==================================================
# INTERFAZ PRINCIPAL - DISEÑO DIVIDIDO
# ==================================================

def main():
    """Función principal con diseño dividido"""
    
    # Obtener datos para el dashboard
    metrics, region_data, meses, casos_mensuales, prevalencia_mensual = get_national_data()
    
    # Contenedor principal dividido
    st.markdown('<div class="split-container">', unsafe_allow_html=True)
    
    # ==============================================
    # COLUMNA IZQUIERDA: DASHBOARD NACIONAL
    # ==============================================
    with st.container():
        st.markdown('<div class="left-panel">', unsafe_allow_html=True)
        
        # Título del dashboard
        st.markdown('<h1 class="dashboard-title">SISTEMA NACIONAL DE CONTROL DE ANEMIA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="dashboard-subtitle">Reporte Nacional Consolidado - 2024</p>', unsafe_allow_html=True)
        
        # Métricas principales
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        
        # Métrica 1: Niños Evaluados
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['total_evaluados']}</div>
            <div class="metric-label">Niños Evaluados</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Métrica 2: Prevalencia Anemia
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['prevalencia_anemia']}</div>
            <div class="metric-label">Prevalencia Anemia</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Métrica 3: Regiones Activas
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['regiones_activas']}/25</div>
            <div class="metric-label">Regiones Activas</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Métrica 4: Hemoglobina Promedio
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['hemoglobina_promedio']}</div>
            <div class="metric-label">Hb Promedio</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Cierra metric-grid
        
        # Separador
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Sección: Distribución por Región
        st.markdown('<h2 class="section-title">Distribución por Región</h2>', unsafe_allow_html=True)
        
        # Mostrar las 5 regiones con más casos
        top_regions = sorted(region_data, key=lambda x: x['prevalencia'], reverse=True)[:5]
        
        for region in top_regions:
            # Determinar color según estado
            color = "#ef4444" if region['estado'] == "Alto" else "#f59e0b" if region['estado'] == "Medio" else "#10b981"
            
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{region['region']}</strong>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{region['casos']} casos</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.2rem; font-weight: bold;">{region['prevalencia']}%</div>
                        <div style="font-size: 0.7rem; opacity: 0.8;">Prevalencia</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Separador
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Botón para descargar PDF
        if st.button("📥 DESCARGAR REPORTE NACIONAL (PDF)", key="download_pdf_button"):
            with st.spinner("Generando reporte PDF..."):
                pdf = create_pdf_report()
                filename = f"Reporte_Anemia_Nacional_{datetime.now().strftime('%Y%m%d')}.pdf"
                
                st.markdown(get_pdf_download_link(pdf, filename), unsafe_allow_html=True)
                st.success("✅ Reporte generado. Haz clic en el botón para descargar.")
        
        # Información adicional
        st.markdown("""
        <div style="margin-top: 2rem; font-size: 0.8rem; opacity: 0.7; text-align: center;">
            <p>📊 Datos actualizados al: """ + datetime.now().strftime('%d/%m/%Y') + """</p>
            <p>📞 Contacto: anemia@minsa.gob.pe</p>
            <p>🏥 Ministerio de Salud - Perú</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Cierra left-panel
    
    # ==============================================
    # COLUMNA DERECHA: SISTEMA DE LOGIN
    # ==============================================
    with st.container():
        st.markdown('<div class="right-panel">', unsafe_allow_html=True)
        
        # Contenedor del login
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Icono y título
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; color: #1e40af; margin-bottom: 1rem;">🏥</div>
            <h1 class="login-title">ACCESO AL SISTEMA</h1>
            <p class="login-subtitle">Ingresa tus credenciales para acceder al sistema completo</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulario de login
        with st.form("login_form"):
            # Campo de usuario
            st.markdown('<div class="form-label">👤 Nombre de Usuario</div>', unsafe_allow_html=True)
            username = st.text_input(
                "", 
                placeholder="Ingresa tu usuario",
                label_visibility="collapsed",
                key="username_input"
            )
            
            # Campo de contraseña
            st.markdown('<div class="form-label">🔒 Contraseña</div>', unsafe_allow_html=True)
            password = st.text_input(
                "", 
                type="password", 
                placeholder="Ingresa tu contraseña",
                label_visibility="collapsed",
                key="password_input"
            )
            
            # Checkbox para recordar sesión
            remember_me = st.checkbox("Recordar sesión", value=True, key="remember_checkbox")
            
            # Botón de submit
            submit_button = st.form_submit_button(
                "🚀 INICIAR SESIÓN",
                use_container_width=True,
                type="primary"
            )
            
            # Procesar el login
            if submit_button:
                if not username.strip() or not password.strip():
                    st.error("❌ Por favor, ingresa usuario y contraseña", icon="🚨")
                else:
                    usuario_info = verificar_login(username.strip(), password.strip())
                    if usuario_info:
                        # Guardar en sesión
                        st.session_state.logged_in = True
                        st.session_state.user_info = usuario_info
                        
                        # Mensaje de éxito
                        st.success(f"✅ ¡Bienvenido/a, {usuario_info['nombre']}!", icon="👋")
                        
                        # Redireccionar al sistema completo
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos", icon="🔒")
        
        # Información de usuarios de prueba
        with st.expander("👥 USUARIOS AUTORIZADOS DEL SISTEMA", expanded=True):
            st.markdown("""
            <div style="background: #f0f9ff; padding: 1rem; border-radius: 10px; border: 1px solid #dbeafe;">
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
            
            **Lic. María Gómez** (Enfermera)
            - Usuario: `enfermero`
            - Contraseña: `Enfermero123`
            
            **Téc. Luis Rodríguez** (Laboratorio)
            - Usuario: `tecnico`
            - Contraseña: `Tecnico123`
            </div>
            """)
        
        # Descripción del sistema completo
        st.markdown("""
        <div style="margin-top: 2rem; background: #f8fafc; padding: 1.5rem; border-radius: 10px; border: 1px solid #e2e8f0;">
            <h4 style="color: #1e40af; margin-top: 0;">🏥 Sistema Completo de Gestión</h4>
            <p style="color: #4b5563; margin: 0.5rem 0;">Accede al sistema completo con todas las funcionalidades:</p>
            <ul style="color: #4b5563; margin: 0.5rem 0; padding-left: 1.5rem;">
                <li>📝 <strong>Registro completo</strong> de pacientes</li>
                <li>🔍 <strong>Seguimiento clínico</strong> avanzado</li>
                <li>📅 <strong>Sistema de citas</strong> y recordatorios</li>
                <li>📊 <strong>Dashboard analítico</strong> en tiempo real</li>
                <li>⚙️ <strong>Configuración</strong> del sistema</li>
                <li>📈 <strong>Reportes personalizados</strong></li>
            </ul>
            <p style="color: #6b7280; font-size: 0.9rem; margin-top: 1rem;">
            <em>Exclusivo para personal de salud autorizado</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Información de contacto
        st.markdown("""
        <div style="margin-top: 2rem; font-size: 0.8rem; color: #6b7280; text-align: center;">
            <p>🔒 <strong>Acceso restringido</strong>: Solo personal médico autorizado</p>
            <p>📞 <strong>Soporte técnico</strong>: soporte@sistemasnixon.com</p>
            <p>© 2024 Sistema Nacional de Control de Anemia</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Cierra login-container
        st.markdown('</div>', unsafe_allow_html=True)  # Cierra right-panel
    
    st.markdown('</div>', unsafe_allow_html=True)  # Cierra split-container

# ==================================================
# SISTEMA COMPLETO (después del login)
# ==================================================

def mostrar_sistema_completo():
    """Muestra el sistema completo después del login"""
    
    # Obtener información del usuario
    user_info = st.session_state.user_info
    
    # Configurar página
    st.set_page_config(
        page_title=f"Sistema Nixon - {user_info['nombre']}",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); 
                    color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
            <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 5px;">👤 {user_info['nombre']}</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 15px; 
                       background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 15px;">
                {user_info['rol']}
            </div>
            <div style="font-size: 0.8rem; opacity: 0.8;">
                {user_info['email']}<br>
                <small>Especialidad: {user_info['especialidad']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón de logout
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.success("✅ Sesión cerrada correctamente")
            st.rerun()
        
        st.markdown("---")
        
        # Navegación
        st.markdown("### 📂 Navegación")
        
        opciones = [
            ("📊 Dashboard Nacional", "dashboard"),
            ("📝 Registro de Pacientes", "registro"),
            ("🔍 Seguimiento Clínico", "seguimiento"),
            ("📅 Sistema de Citas", "citas"),
            ("📈 Reportes Avanzados", "reportes"),
            ("⚙️ Configuración", "config")
        ]
        
        for texto, clave in opciones:
            if st.button(texto, use_container_width=True, key=f"nav_{clave}"):
                st.session_state.current_page = clave
                st.rerun()
    
    # Contenido principal
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); 
                padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h1 style="margin: 0; font-size: 2.5rem;">🏥 SISTEMA NIXON COMPLETO</h1>
        <p style="margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Control de Anemia y Nutrición Infantil | Usuario: {user_info['nombre']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar contenido según página seleccionada
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    
    if st.session_state.current_page == "dashboard":
        st.markdown("### 📊 Dashboard del Sistema")
        # Aquí iría el dashboard completo...
        
    elif st.session_state.current_page == "registro":
        st.markdown("### 📝 Registro de Pacientes")
        # Aquí iría el formulario de registro...
        
    # ... (continuar con las otras páginas)

# ==================================================
# EJECUTAR LA APLICACIÓN
# ==================================================

if __name__ == "__main__":
    # Verificar si el usuario está logueado
    if st.session_state.logged_in:
        mostrar_sistema_completo()
    else:
        main()
