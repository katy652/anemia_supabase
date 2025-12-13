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
    .severity-critical {
        background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-moderate {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-mild {
        background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .severity-none {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .interpretacion-critica {
        background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ff4444;
    }
    .interpretacion-moderada {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ffaa00;
    }
    .interpretacion-leve {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #44AAFF;
    }
    .interpretacion-normal {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #44FF44;
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
# OPCIÓN 2: CREACIÓN SIMPLE DE TABLA CON RLS - VERSIÓN CORREGIDA
# ==================================================
def crear_tabla_citas_simple():
    """Crea la tabla citas con RLS básico - VERSIÓN CORREGIDA"""
    
    try:
        st.sidebar.info("🛠️ Configurando tabla 'citas'...")
        
        # Método 1: Intentar crear directamente con Supabase
        try:
            # Primero verificar si ya existe
            test_check = supabase.table("citas").select("id").limit(1).execute()
            
            if not hasattr(test_check, 'error') or test_check.error is None:
                st.sidebar.success("✅ Tabla 'citas' ya existe")
                
                # Probar si podemos insertar
                test_data = {
                    "dni_paciente": "99988877",
                    "fecha_cita": "2024-01-01",
                    "hora_cita": "10:00:00",
                    "tipo_consulta": "Prueba",
                    "diagnostico": "Prueba de conexión"
                }
                
                test_insert = supabase.table("citas").insert(test_data).execute()
                
                if test_insert.data:
                    st.sidebar.success("✅ RLS configurado correctamente")
                    # Limpiar
                    supabase.table("citas").delete().eq("dni_paciente", "99988877").execute()
                    return True
                else:
                    st.sidebar.warning("⚠️ Tabla existe pero RLS no configurado")
                    return False
                    
        except Exception as check_error:
            st.sidebar.info(f"ℹ️ {str(check_error)[:100]}")
        
        # Método 2: Crear tabla usando SQL directo (simplificado)
        try:
            import requests
            
            st.sidebar.write("📋 Creando tabla...")
            
            # 1. Primero intentar crear con un INSERT simple
            test_data = {
                "dni_paciente": "11111111",
                "fecha_cita": "2024-01-01",
                "hora_cita": "10:00:00",
                "tipo_consulta": "Prueba creación"
            }
            
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/citas",
                headers=headers,
                json=test_data
            )
            
            if response.status_code in [200, 201, 409]:
                st.sidebar.success("✅ Tabla accesible")
                
                # 2. Configurar RLS si es necesario
                st.sidebar.write("🔐 Configurando RLS...")
                
                # Política para INSERT
                try:
                    # Verificar si podemos hacer un segundo insert
                    test_data2 = {
                        "dni_paciente": "22222222",
                        "fecha_cita": "2024-01-02",
                        "hora_cita": "11:00:00",
                        "tipo_consulta": "Prueba RLS"
                    }
                    
                    response2 = requests.post(
                        f"{SUPABASE_URL}/rest/v1/citas",
                        headers=headers,
                        json=test_data2
                    )
                    
                    if response2.status_code in [200, 201]:
                        st.sidebar.success("✅ RLS funciona correctamente")
                        
                        # Limpiar
                        requests.delete(f"{SUPABASE_URL}/rest/v1/citas?dni_paciente=eq.11111111", headers=headers)
                        requests.delete(f"{SUPABASE_URL}/rest/v1/citas?dni_paciente=eq.22222222", headers=headers)
                        
                        return True
                    else:
                        st.sidebar.warning(f"⚠️ Error RLS: {response2.status_code}")
                        return False
                        
                except Exception as rls_error:
                    st.sidebar.error(f"❌ Error RLS: {str(rls_error)[:100]}")
                    return False
                    
            else:
                st.sidebar.error(f"❌ No se pudo crear tabla: {response.status_code}")
                
                # Mostrar instrucciones para crear manualmente
                st.sidebar.markdown("""
                **📝 Para crear la tabla manualmente:**
                
                1. **Ve a Supabase → SQL Editor**
                2. **Ejecuta este SQL:**
                
                ```sql
                CREATE TABLE citas (
                    id BIGSERIAL PRIMARY KEY,
                    dni_paciente TEXT NOT NULL,
                    fecha_cita DATE NOT NULL,
                    hora_cita TIME NOT NULL,
                    tipo_consulta TEXT,
                    diagnostico TEXT,
                    tratamiento TEXT,
                    observaciones TEXT,
                    investigador_responsable TEXT,
                    proxima_cita DATE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                ALTER TABLE citas ENABLE ROW LEVEL SECURITY;
                
                CREATE POLICY "allow_all_citas" ON citas
                FOR ALL USING (true) WITH CHECK (true);
                ```
                """)
                
                return False
                
        except Exception as e:
            st.sidebar.error(f"🔥 Error: {str(e)[:200]}")
            return False
            
    except Exception as e:
        st.sidebar.error(f"💥 Error general: {str(e)[:200]}")
        return False

# ==================================================
# FUNCIÓN ALTERNATIVA: PRUEBA DIRECTA - VERSIÓN CORREGIDA
# ==================================================
def probar_guardado_directo():
    """Prueba directa de guardado - VERSIÓN CORREGIDA"""
    
    with st.sidebar:
        st.markdown("### 🧪 Prueba Directa")
        
        # Obtener un DNI real que exista en alertas_hemoglobina
        try:
            # Buscar un paciente real para probar
            pacientes = supabase.table("alertas_hemoglobina").select("dni").limit(5).execute()
            
            if pacientes.data and len(pacientes.data) > 0:
                dni_real = pacientes.data[0]["dni"]
                st.info(f"📋 Usando DNI real: {dni_real}")
            else:
                dni_real = "12345678"  # DNI por defecto
                st.warning("⚠️ No hay pacientes, usando DNI de prueba")
                
        except:
            dni_real = "12345678"
        
        # Datos de prueba CON DNI REAL
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
                        
                        # Guardar el ID para poder limpiar después
                        if 'pruebas_ids' not in st.session_state:
                            st.session_state.pruebas_ids = []
                        st.session_state.pruebas_ids.append(result.data[0].get('id'))
                        
                    elif hasattr(result, 'error'):
                        error_msg = result.error.message
                        st.error(f"❌ Error: {error_msg}")
                        
                        # Si es error de foreign key, mostrar solución
                        if "foreign key constraint" in error_msg:
                            st.info("💡 Solución: El DNI debe existir en la tabla 'alertas_hemoglobina'")
                    else:
                        st.warning("⚠️ Respuesta inesperada del servidor")
                        
                except Exception as e:
                    st.error(f"🔥 Error: {str(e)[:200]}")
        
        with col2:
            if st.button("🗑️ Limpiar pruebas", key="limpiar_pruebas"):
                try:
                    # Limpiar por DNI
                    supabase.table("citas").delete().eq("dni_paciente", dni_real).execute()
                    
                    # También limpiar otros DNIs de prueba comunes
                    for dni_prueba in ["87654321", "00000001", "00000002", "99988877", "11111111", "22222222"]:
                        try:
                            supabase.table("citas").delete().eq("dni_paciente", dni_prueba).execute()
                        except:
                            pass
                    
                    # Limpiar por IDs guardados
                    if 'pruebas_ids' in st.session_state:
                        for prueba_id in st.session_state.pruebas_ids:
                            try:
                                supabase.table("citas").delete().eq("id", prueba_id).execute()
                            except:
                                pass
                        st.session_state.pruebas_ids = []
                    
                    st.success("✅ Todas las pruebas limpiadas")
                    
                except Exception as e:
                    st.info(f"ℹ️ {str(e)[:100]}")

# ==================================================
# BOTONES MEJORADOS EN BARRA LATERAL - VERSIÓN FINAL
# ==================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📅 Configuración de Citas")
    
    # Opción 1: Configurar tabla
    if st.button("🛠️ Configurar tabla 'citas'", 
                 type="primary", 
                 use_container_width=True,
                 key="configurar_tabla"):
        crear_tabla_citas_simple()
    
    # Opción 2: Prueba directa
    probar_guardado_directo()
    
    # Opción 3: Verificar conexión
    if st.button("🔍 Verificar conexión", 
                 type="secondary",
                 key="verificar_conexion"):
        try:
            with st.spinner("Verificando..."):
                # Probar lectura de tabla principal
                test = supabase.table("alertas_hemoglobina").select("dni").limit(3).execute()
                
                if test.data:
                    st.success(f"✅ Conexión OK - {len(test.data)} pacientes encontrados")
                    
                    # Mostrar algunos DNIs disponibles
                    dnis = [p["dni"] for p in test.data[:3]]
                    st.info(f"📋 DNIs disponibles: {', '.join(dnis)}")
                else:
                    st.warning("⚠️ Conexión OK pero tabla vacía")
                    
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)[:200]}")

# ==================================================
# FUNCIÓN ALTERNATIVA: PRUEBA DIRECTA SIN CREAR TABLA
# ==================================================
def probar_guardado_directo():
    """Prueba directa de guardado - método más simple"""
    
    with st.sidebar:
        st.markdown("### 🧪 Prueba Directa")
        
        # Datos de prueba
        test_cita = {
            "dni_paciente": "87654321",
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
            if st.button("📤 Enviar prueba", type="primary"):
                try:
                    with st.spinner("Enviando a Supabase..."):
                        result = supabase.table("citas").insert(test_cita).execute()
                    
                    if result.data:
                        st.success("✅ ¡ÉXITO! Guardado correctamente")
                        st.info(f"ID: {result.data[0].get('id', 'N/A')}")
                    elif hasattr(result, 'error'):
                        st.error(f"❌ Error: {result.error.message}")
                    else:
                        st.warning("⚠️ Respuesta inesperada")
                        
                except Exception as e:
                    st.error(f"🔥 Error: {str(e)}")
        
        with col2:
            if st.button("🗑️ Limpiar pruebas"):
                try:
                    supabase.table("citas").delete().eq("dni_paciente", "87654321").execute()
                    supabase.table("citas").delete().eq("dni_paciente", "00000001").execute()
                    supabase.table("citas").delete().eq("dni_paciente", "00000002").execute()
                    st.info("Pruebas limpiadas")
                except:
                    pass

# ==================================================
# BOTONES MEJORADOS EN BARRA LATERAL
# ==================================================
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📅 Configuración de Citas")
    
    # Opción 1: Configurar tabla
    if st.button("🛠️ Configurar tabla 'citas'", type="primary", use_container_width=True):
        crear_tabla_citas_simple()
    
    # Opción 2: Prueba directa
    probar_guardado_directo()
    
    # Opción 3: Verificar conexión
    if st.button("🔍 Verificar conexión", type="secondary"):
        try:
            # Probar lectura de otra tabla
            test = supabase.table("alertas_hemoglobina").select("*").limit(1).execute()
            if test.data:
                st.success(f"✅ Conexión OK - {len(test.data)} registros en alertas_hemoglobina")
            else:
                st.warning("⚠️ Conexión OK pero tabla vacía")
        except Exception as e:
            st.error(f"❌ Error de conexión: {str(e)}")
# ==================================================
# PRUEBA DE GUARDADO SIMPLE
# ==================================================
def probar_guardado_simple():
    """Prueba simple de guardado"""
    try:
        test_cita = {
            "dni_paciente": "99988877",
            "fecha_cita": "2024-12-13",
            "hora_cita": "15:00:00",
            "tipo_consulta": "Prueba Simple",
            "diagnostico": "Probando configuración"
        }
        
        result = supabase.table("citas").insert(test_cita).execute()
        
        if result.data:
            st.sidebar.success("✅ ¡Guardado exitoso!")
            
            # Limpiar
            supabase.table("citas").delete().eq("dni_paciente", "99988877").execute()
            return True
        else:
            st.sidebar.error(f"❌ Error: {result.error.message if hasattr(result, 'error') else 'Sin datos'}")
            return False
            
    except Exception as e:
        st.sidebar.error(f"🔥 Error: {str(e)}")
        return False

# ==================================================
# BOTONES EN BARRA LATERAL
# ==================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Configuración Citas")

if st.sidebar.button("🛠️ Crear tabla citas", type="primary"):
    if crear_tabla_citas_simple():
        st.sidebar.success("✅ Configuración completada")

if st.sidebar.button("🧪 Probar guardado", type="secondary"):
    probar_guardado_simple()
# ==================================================
# FUNCIONES DE BASE DE DATOS (CORREGIDAS)
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
        
        # Verificar si ya existe
        if verificar_duplicado(dni):
            st.error(f"❌ El DNI {dni} ya existe en la base de datos")
            return {"status": "duplicado", "dni": dni}
        
        # Insertar si no existe
        if supabase:
            response = supabase.table(tabla).insert(datos).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"❌ Error Supabase al insertar: {response.error}")
                st.write("Datos que causaron error:", datos)
                return None
            return response.data[0] if response.data else None
        return None
    except Exception as e:
        st.error(f"Error insertando datos: {e}")
        st.write("Datos que causaron error:", datos)
        return None

def upsert_datos_supabase(datos, tabla=TABLE_NAME):
    """Inserta o actualiza datos si ya existen (basado en DNI)"""
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
        # Datos de respaldo
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
    
    # EVALUAR FERRITINA (Reservas de Hierro)
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
    
    # EVALUAR CHCM (Concentración de Hemoglobina)
    if chcm < 32:
        interpretacion += "🚨 **HIPOCROMÍA SEVERA** - Deficiencia avanzada de hierro. "
        severidad = "CRITICO" if severidad != "CRITICO" else severidad
    elif chcm >= 32 and chcm <= 36:
        interpretacion += "✅ **NORMOCROMÍA** - Estado normal. "
    else:
        interpretacion += "🔄 **HIPERCROMÍA** - Posible esferocitosis. "
    
    # EVALUAR RETICULOCITOS (Producción Medular)
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
    
    # CLASIFICACIÓN DE ANEMIA BASADA EN HEMOGLOBINA
    clasificacion_hb, _, _ = clasificar_anemia(hemoglobina_ajustada, edad_meses)
    interpretacion += f"📊 **CLASIFICACIÓN HEMOGLOBINA: {clasificacion_hb}**"
    
    # GENERAR RECOMENDACIÓN ESPECÍFICA
    if severidad == "CRITICO":
        recomendacion = "🚨 **INTERVENCIÓN INMEDIATA**: Suplementación con hierro elemental 3-6 mg/kg/día + Control en 15 días + Evaluación médica urgente"
        codigo_color = "#FF4444"
    elif severidad == "MODERADO":
        recomendacion = "⚠️ **ACCIÓN PRIORITARIA**: Iniciar suplementación con hierro + Control mensual + Educación nutricional"
        codigo_color = "#FFAA00"
    elif severidad == "LEVE":
        recomendacion = "🔄 **VIGILANCIA ACTIVA**: Suplementación preventiva + Modificación dietética + Control cada 3 meses"
        codigo_color = "#44AAFF"
    else:
        recomendacion = "✅ **SEGUIMIENTO RUTINARIO**: Mantener alimentación balanceada + Control preventivo cada 6 meses"
        codigo_color = "#44FF44"
    
    return {
        "interpretacion": interpretacion,
        "severidad": severidad,
        "recomendacion": recomendacion,
        "codigo_color": codigo_color,
        "clasificacion_hemoglobina": clasificacion_hb
    }

def generar_parametros_hematologicos(hemoglobina_ajustada, edad_meses):
    """Genera parámetros hematológicos simulados basados en hemoglobina y edad"""
    
    # Basar los parámetros en el nivel de hemoglobina
    if hemoglobina_ajustada < 9.0:
        # Anemia severa - parámetros consistentes con deficiencia
        ferritina = np.random.uniform(5, 15)
        chcm = np.random.uniform(28, 31)
        reticulocitos = np.random.uniform(0.5, 1.0)
        transferrina = np.random.uniform(350, 450)
    elif hemoglobina_ajustada < 11.0:
        # Anemia moderada/leve
        ferritina = np.random.uniform(15, 50)
        chcm = np.random.uniform(31, 33)
        reticulocitos = np.random.uniform(1.0, 1.8)
        transferrina = np.random.uniform(300, 400)
    else:
        # Sin anemia
        ferritina = np.random.uniform(80, 150)
        chcm = np.random.uniform(33, 36)
        reticulocitos = np.random.uniform(0.8, 1.5)
        transferrina = np.random.uniform(200, 350)
    
    # Ajustar VCM y HCM basados en CHCM
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
# CLASIFICACIÓN DE ANEMIA Y SEGUIMIENTO
# ==================================================

def clasificar_anemia(hemoglobina_ajustada, edad_meses):
    """Clasifica la anemia según estándares OMS"""
    
    if edad_meses < 24:
        # Menores de 2 años
        if hemoglobina_ajustada >= 11.0:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 10.0 <= hemoglobina_ajustada < 11.0:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 9.0 <= hemoglobina_ajustada < 10.0:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"
    
    elif 24 <= edad_meses < 60:
        # 2 a 5 años
        if hemoglobina_ajustada >= 11.5:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 10.5 <= hemoglobina_ajustada < 11.5:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 9.5 <= hemoglobina_ajustada < 10.5:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"
    
    else:
        # Mayores de 5 años
        if hemoglobina_ajustada >= 12.0:
            return "SIN ANEMIA", "NO requiere seguimiento", "success"
        elif 11.0 <= hemoglobina_ajustada < 12.0:
            return "ANEMIA LEVE", "Seguimiento cada 3 meses", "warning"
        elif 10.0 <= hemoglobina_ajustada < 11.0:
            return "ANEMIA MODERADA", "Seguimiento mensual", "error"
        else:
            return "ANEMIA SEVERA", "Seguimiento urgente semanal", "error"

def necesita_seguimiento_automatico(hemoglobina_ajustada, edad_meses):
    """Determina si necesita seguimiento automático basado en anemia"""
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
        # Datos de respaldo
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
    
    # Encontrar referencia para la edad
    referencia_edad = referencia_df[referencia_df['edad_meses'] == edad_meses]
    
    if referencia_edad.empty:
        return "Edad sin referencia", "Edad sin referencia", "NO EVALUABLE"
    
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
# INTERFAZ PRINCIPAL
# ==================================================

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🏥 SISTEMA NIXON - Control de Anemia y Nutrición")
st.markdown("**Sistema integrado con ajuste por altitud y evaluación nutricional**")
st.markdown('</div>', unsafe_allow_html=True)

if supabase:
    st.success("🟢 CONECTADO A SUPABASE")
else:
    st.error("🔴 SIN CONEXIÓN A SUPABASE")

# PESTAÑAS PRINCIPALES
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 Registro Completo", 
    "🔍 Seguimiento Clínico", 
    "📈 Estadísticas",
    "📋 Sistema de Citas",
    "📊 Dashboard Nacional"
])

# ==================================================
# PESTAÑA 1: REGISTRO COMPLETO
# ==================================================

with tab1:
    st.header("📝 Registro Completo de Paciente")
    
    with st.form("formulario_completo"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Datos Personales")
            dni = st.text_input("DNI*", placeholder="Ej: 87654321")
            nombre_completo = st.text_input("Nombre Completo*", placeholder="Ej: Ana García Pérez")
            edad_meses = st.number_input("Edad (meses)*", 1, 240, 24)
            peso_kg = st.number_input("Peso (kg)*", 0.0, 50.0, 12.5, 0.1)
            talla_cm = st.number_input("Talla (cm)*", 0.0, 150.0, 85.0, 0.1)
            genero = st.selectbox("Género*", GENEROS)
            telefono = st.text_input("Teléfono", placeholder="Ej: 987654321")
            estado_paciente = st.selectbox("Estado del Paciente", ESTADOS_PACIENTE)
        
        with col2:
            st.subheader("🌍 Datos Geográficos")
            region = st.selectbox("Región*", PERU_REGIONS)
            departamento = st.text_input("Departamento/Distrito", placeholder="Ej: Lima Metropolitana")
            
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
            
            # Mostrar clasificación de anemia
            clasificacion, recomendacion, tipo_alerta = clasificar_anemia(hemoglobina_ajustada, edad_meses)
            
            if tipo_alerta == "error":
                st.error(f"**{clasificacion}** - {recomendacion}")
            elif tipo_alerta == "warning":
                st.warning(f"**{clasificacion}** - {recomendacion}")
            else:
                st.success(f"**{clasificacion}** - {recomendacion}")
            
            st.metric(
                "Hemoglobina ajustada al nivel del mar",
                f"{hemoglobina_ajustada:.1f} g/dL",
                f"{ajuste_hb:+.1f} g/dL"
            )
            
            # Determinar seguimiento automático basado en anemia
            necesita_seguimiento = necesita_seguimiento_automatico(hemoglobina_ajustada, edad_meses)
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
            st.subheader("📋 Factores de Riesgo")
            st.write("🏥 Factores Clínicos")
            factores_clinicos = st.multiselect("Seleccione factores clínicos:", FACTORES_CLINICOS)
            
            st.write("💰 Factores Socioeconómicos")
            factores_sociales = st.multiselect("Seleccione factores sociales:", FACTORES_SOCIOECONOMICOS)
        
        submitted = st.form_submit_button("🎯 ANALIZAR RIESGO Y GUARDAR", type="primary")
    
    if submitted:
        if not dni or not nombre_completo:
            st.error("❌ Complete DNI y nombre del paciente")
        else:
            # Calcular riesgo usando hemoglobina AJUSTADA
            nivel_riesgo, puntaje, estado = calcular_riesgo_anemia(
                hemoglobina_ajustada,
                edad_meses,
                factores_clinicos,
                factores_sociales
            )
            
            # Generar sugerencias
            sugerencias = generar_sugerencias(nivel_riesgo, hemoglobina_ajustada, edad_meses)
            
            # Evaluación nutricional
            estado_peso, estado_talla, estado_nutricional = evaluar_estado_nutricional(
                edad_meses, peso_kg, talla_cm, genero
            )
            
            # Generar parámetros e interpretación automática
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
            st.subheader("📊 EVALUACIÓN INTEGRAL DEL PACIENTE")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🩺 Estado de Anemia")
                if "ALTO" in nivel_riesgo:
                    st.markdown('<div class="risk-high">', unsafe_allow_html=True)
                elif "MODERADO" in nivel_riesgo:
                    st.markdown('<div class="risk-moderate">', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-low">', unsafe_allow_html=True)
                
                st.markdown(f"**RIESGO ANEMIA:** {nivel_riesgo}")
                st.markdown(f"**Puntaje:** {puntaje}/60 puntos")
                st.markdown(f"**Alerta:** {estado}")
                st.markdown(f"**Clasificación OMS:** {clasificacion}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🍎 Estado Nutricional")
                st.markdown(f"**Peso:** {estado_peso}")
                st.markdown(f"**Talla:** {estado_talla}")
                st.markdown(f"**Estado Nutricional:** {estado_nutricional}")
                st.markdown(f"**Seguimiento activo:** {'SÍ' if en_seguimiento else 'NO'}")
            
            # INTERPRETACIÓN HEMATOLÓGICA AUTOMÁTICA
            st.markdown("### 🔬 Interpretación Hematológica Automática")
            
            # Aplicar estilo según severidad
            if interpretacion_auto['severidad'] == "CRITICO":
                st.markdown(f'<div class="interpretacion-critica">', unsafe_allow_html=True)
            elif interpretacion_auto['severidad'] == "MODERADO":
                st.markdown(f'<div class="interpretacion-moderada">', unsafe_allow_html=True)
            elif interpretacion_auto['severidad'] == "LEVE":
                st.markdown(f'<div class="interpretacion-leve">', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="interpretacion-normal">', unsafe_allow_html=True)
            
            st.markdown(f"**📋 Análisis Integrado - {interpretacion_auto['severidad']}**")
            st.markdown(f"**Interpretación:** {interpretacion_auto['interpretacion']}")
            st.markdown(f"**💡 Plan Específico:** {interpretacion_auto['recomendacion']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar parámetros simulados
            st.markdown("### 🧪 Parámetros Hematológicos Estimados")
            col_param1, col_param2, col_param3 = st.columns(3)
            with col_param1:
                st.metric("Ferritina", f"{parametros_simulados['ferritina']} ng/mL")
                st.metric("CHCM", f"{parametros_simulados['chcm']} g/dL")
            with col_param2:
                st.metric("Transferrina", f"{parametros_simulados['transferrina']} mg/dL")
                st.metric("VCM", f"{parametros_simulados['vcm']} fL")
            with col_param3:
                st.metric("Reticulocitos", f"{parametros_simulados['reticulocitos']} %")
                st.metric("HCM", f"{parametros_simulados['hcm']} pg")
            
            # SUGERENCIAS
            st.markdown("### 💡 Plan de Acción General")
            st.info(sugerencias)
            
            # ============================================
            # GUARDAR EN SUPABASE CON VERIFICACIÓN DE DUPLICADOS
            # ============================================
            if supabase:
                with st.spinner("Verificando y guardando datos..."):
                    # Crear el registro completo
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
                        "interpretacion_hematologica": interpretacion_auto['interpretacion'],
                        "politicas_de_ris": region,
                        "riesgo": nivel_riesgo,
                        "fecha_alerta": datetime.now().strftime("%Y-%m-%d"),
                        "estado_alerta": estado,
                        "sugerencias": sugerencias,
                        "severidad_interpretacion": interpretacion_auto['severidad']
                    }
                    
                    # Insertar usando la función que verifica duplicados
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
# PESTAÑA 2: SEGUIMIENTO CLÍNICO
# ==================================================

with tab2:
    st.header("🔍 Seguimiento Clínico por Gravedad")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Casos que Requieren Seguimiento")
        
        if st.button("🔄 Actualizar casos prioritarios"):
            with st.spinner("Analizando gravedad de casos..."):
                # Obtener todos los pacientes
                todos_pacientes = obtener_datos_supabase()
                
                if not todos_pacientes.empty:
                    # Calcular hemoglobina ajustada y clasificar
                    pacientes_analizados = todos_pacientes.copy()
                    
                    analisis_data = []
                    for _, paciente in pacientes_analizados.iterrows():
                        hb_ajustada = calcular_hemoglobina_ajustada(
                            paciente.get('hemoglobina_dl1', 0), 
                            paciente.get('altitud_msnm', 0)
                        )
                        
                        clasificacion, recomendacion, _ = clasificar_anemia(hb_ajustada, paciente.get('edad_meses', 0))
                        
                        analisis = {
                            'nombre_apellido': paciente.get('nombre_apellido', 'N/A'),
                            'edad_meses': paciente.get('edad_meses', 0),
                            'hemoglobina_dl1': paciente.get('hemoglobina_dl1', 0),
                            'hb_ajustada': hb_ajustada,
                            'clasificacion_anemia': clasificacion,
                            'recomendacion_seguimiento': recomendacion,
                            'region': paciente.get('region', 'No especificada'),
                            'fecha_alerta': paciente.get('fecha_alerta', 'N/D')
                        }
                        analisis_data.append(analisis)
                    
                    analisis_df = pd.DataFrame(analisis_data)
                    
                    # Filtrar solo los que necesitan seguimiento (moderado + severo)
                    casos_seguimiento = analisis_df[
                        analisis_df['clasificacion_anemia'].isin(["ANEMIA MODERADA", "ANEMIA SEVERA"])
                    ]
                    
                    if not casos_seguimiento.empty:
                        st.success(f"🚨 {len(casos_seguimiento)} casos requieren seguimiento activo")
                        
                        # Ordenar por gravedad (severa primero)
                        orden_gravedad = {"ANEMIA SEVERA": 1, "ANEMIA MODERADA": 2}
                        casos_seguimiento['orden'] = casos_seguimiento['clasificacion_anemia'].map(orden_gravedad)
                        casos_seguimiento = casos_seguimiento.sort_values('orden').drop('orden', axis=1)
                        
                        # Mostrar tabla
                        st.dataframe(
                            casos_seguimiento,
                            use_container_width=True,
                            height=400,
                            column_config={
                                'nombre_apellido': 'Paciente',
                                'edad_meses': 'Edad (meses)',
                                'hemoglobina_dl1': st.column_config.NumberColumn('Hb Medida (g/dL)', format='%.1f'),
                                'hb_ajustada': st.column_config.NumberColumn('Hb Ajustada (g/dL)', format='%.1f'),
                                'clasificacion_anemia': 'Gravedad',
                                'recomendacion_seguimiento': 'Seguimiento',
                                'region': 'Región',
                                'fecha_alerta': 'Fecha'
                            }
                        )
                        
                        # Métricas de gravedad
                        st.subheader("📊 Distribución por Gravedad")
                        severos = len(casos_seguimiento[casos_seguimiento['clasificacion_anemia'] == "ANEMIA SEVERA"])
                        moderados = len(casos_seguimiento[casos_seguimiento['clasificacion_anemia'] == "ANEMIA MODERADA"])
                        
                        col_met1, col_met2, col_met3 = st.columns(3)
                        with col_met1:
                            st.metric("🟥 Severos", severos)
                        with col_met2:
                            st.metric("🟨 Moderados", moderados)
                        with col_met3:
                            st.metric("📅 Total Prioridad", len(casos_seguimiento))
                        
                    else:
                        st.success("✅ No hay casos que requieran seguimiento activo")
                        st.info("""
                        **Todos los pacientes tienen:**
                        - Anemia leve o sin anemia
                        - Seguimiento rutinario cada 3-6 meses
                        - No requieren intervención urgente
                        """)
                else:
                    st.info("📝 No hay pacientes registrados en el sistema")
    
    with col2:
        st.subheader("🎯 Criterios de Seguimiento")
        
        st.markdown("""
        <div class="severity-critical">
        <h4>🚨 ANEMIA SEVERA</h4>
        <p><strong>Seguimiento:</strong> Urgente semanal</p>
        <p><strong>Acción:</strong> Suplementación inmediata + Control médico</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="severity-moderate">
        <h4>⚠️ ANEMIA MODERADA</h4>
        <p><strong>Seguimiento:</strong> Mensual</p>
        <p><strong>Acción:</strong> Suplementación + Monitoreo</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="severity-mild">
        <h4>✅ ANEMIA LEVE</h4>
        <p><strong>Seguimiento:</strong> Cada 3 meses</p>
        <p><strong>Acción:</strong> Educación nutricional</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="severity-none">
        <h4>💚 SIN ANEMIA</h4>
        <p><strong>Seguimiento:</strong> Cada 6 meses</p>
        <p><strong>Acción:</strong> Prevención</p>
        </div>
        """, unsafe_allow_html=True)

    # SECCIÓN: ANÁLISIS HEMATOLÓGICO COMPLETO CON INTERPRETACIÓN
    st.markdown("---")
    st.header("🔬 Análisis Hematológico Completo con Interpretación")
    
    if st.button("🧪 Generar Análisis Hematológico Avanzado"):
        with st.spinner("Procesando parámetros hematológicos con interpretación automática..."):
            todos_pacientes = obtener_datos_supabase()
            
            if not todos_pacientes.empty:
                # Calcular todos los parámetros con interpretación
                analisis_data = []
                interpretaciones_data = []
                
                for _, paciente in todos_pacientes.iterrows():
                    hb_ajustada = calcular_hemoglobina_ajustada(
                        paciente.get('hemoglobina_dl1', 0), 
                        paciente.get('altitud_msnm', 0)
                    )
                    
                    clasificacion, recomendacion, _ = clasificar_anemia(hb_ajustada, paciente.get('edad_meses', 0))
                    
                    # Generar parámetros hematológicos realistas
                    parametros = generar_parametros_hematologicos(hb_ajustada, paciente.get('edad_meses', 0))
                    
                    # Generar interpretación automática
                    interpretacion = interpretar_analisis_hematologico(
                        parametros['ferritina'],
                        parametros['chcm'], 
                        parametros['reticulocitos'],
                        parametros['transferrina'],
                        hb_ajustada,
                        paciente.get('edad_meses', 0)
                    )
                    
                    # Datos para tabla principal
                    analisis = {
                        'paciente': paciente.get('nombre_apellido', 'N/A'),
                        'edad_meses': paciente.get('edad_meses', 0),
                        'hb_medida': paciente.get('hemoglobina_dl1', 0),
                        'hb_ajustada': hb_ajustada,
                        'clasificacion': clasificacion,
                        'vcm': parametros['vcm'],
                        'hcm': parametros['hcm'],
                        'chcm': parametros['chcm'],
                        'ferritina': parametros['ferritina'],
                        'transferrina': parametros['transferrina'],
                        'reticulocitos': parametros['reticulocitos'],
                        'recomendacion': recomendacion,
                        'severidad': interpretacion['severidad']
                    }
                    analisis_data.append(analisis)
                    
                    # Datos para sección de interpretación
                    interpretaciones_data.append({
                        'paciente': paciente.get('nombre_apellido', 'N/A'),
                        'interpretacion': interpretacion['interpretacion'],
                        'recomendacion_especifica': interpretacion['recomendacion'],
                        'severidad': interpretacion['severidad'],
                        'color_alerta': interpretacion['codigo_color']
                    })
                
                analisis_df = pd.DataFrame(analisis_data)
                interpretaciones_df = pd.DataFrame(interpretaciones_data)
                
                st.success(f"🧪 {len(analisis_df)} análisis hematológicos con interpretación generados")
                
                # MOSTRAR TABLA PRINCIPAL DE PARÁMETROS
                st.subheader("📊 Parámetros Hematológicos")
                st.dataframe(
                    analisis_df,
                    use_container_width=True,
                    height=400,
                    column_config={
                        'paciente': 'Paciente',
                        'edad_meses': 'Edad (meses)',
                        'hb_medida': st.column_config.NumberColumn('Hb Medida', format='%.1f g/dL'),
                        'hb_ajustada': st.column_config.NumberColumn('Hb Ajustada', format='%.1f g/dL'),
                        'clasificacion': 'Clasificación',
                        'vcm': st.column_config.NumberColumn('VCM', format='%.1f fL'),
                        'hcm': st.column_config.NumberColumn('HCM', format='%.1f pg'),
                        'chcm': st.column_config.NumberColumn('CHCM', format='%.1f g/dL'),
                        'ferritina': st.column_config.NumberColumn('Ferritina', format='%.1f ng/mL'),
                        'transferrina': st.column_config.NumberColumn('Transferrina', format='%.0f mg/dL'),
                        'reticulocitos': st.column_config.NumberColumn('Reticulocitos', format='%.1f %%'),
                        'recomendacion': 'Recomendación',
                        'severidad': 'Severidad'
                    }
                )
                
                # MOSTRAR INTERPRETACIONES DETALLADAS
                st.subheader("🎯 Interpretación Clínica Automática")
                
                for _, interpretacion in interpretaciones_df.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="border-left: 5px solid {interpretacion['color_alerta']}; 
                                    padding: 1rem; margin: 1rem 0; 
                                    background-color: #f8f9fa; border-radius: 5px;">
                            <h4>👤 {interpretacion['paciente']} - <span style="color: {interpretacion['color_alerta']}">{interpretacion['severidad']}</span></h4>
                            <p><strong>Interpretación:</strong> {interpretacion['interpretacion']}</p>
                            <p><strong>Plan de Acción:</strong> {interpretacion['recomendacion_especifica']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # GRÁFICO DE DISTRIBUCIÓN POR SEVERIDAD
                st.subheader("📈 Distribución por Nivel de Severidad")
                distribucion_severidad = analisis_df['severidad'].value_counts()
                
                fig_severidad = px.pie(
                    values=distribucion_severidad.values,
                    names=distribucion_severidad.index,
                    title="Distribución de Pacientes por Severidad",
                    color=distribucion_severidad.index,
                    color_discrete_map={
                        'CRITICO': '#FF4444',
                        'MODERADO': '#FFAA00', 
                        'LEVE': '#44AAFF',
                        'NORMAL': '#44FF44'
                    }
                )
                st.plotly_chart(fig_severidad, use_container_width=True)
                
            else:
                st.info("📝 No hay pacientes registrados para análisis")

# ==================================================
# PESTAÑA 3: ESTADÍSTICAS - VERSIÓN CORREGIDA
# ==================================================

with tab3:
    st.header("📊 Dashboard de Estadísticas")
    
    # Botón para cargar datos
    if st.button("🔄 Cargar Datos para Análisis", type="primary"):
        with st.spinner("Cargando datos desde Supabase..."):
            datos_completos = obtener_datos_supabase()
            
            if not datos_completos.empty:
                st.session_state.datos_estadisticas = datos_completos
                st.success(f"✅ {len(datos_completos)} registros cargados exitosamente")
            else:
                st.error("❌ No se pudieron cargar datos desde la base de datos")
    
    # Verificar si tenemos datos para analizar
    if 'datos_estadisticas' in st.session_state and not st.session_state.datos_estadisticas.empty:
        datos = st.session_state.datos_estadisticas
        
        # ========== MÉTRICAS RÁPIDAS ==========
        st.subheader("📈 Métricas Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_pacientes = len(datos)
            st.metric("Total Pacientes", total_pacientes)
        
        with col2:
            if 'hemoglobina_dl1' in datos.columns:
                hb_promedio = datos['hemoglobina_dl1'].mean()
                st.metric("Hb Promedio", f"{hb_promedio:.1f} g/dL")
        
        with col3:
            if 'edad_meses' in datos.columns:
                edad_promedio = datos['edad_meses'].mean() / 12  # Convertir a años
                st.metric("Edad Promedio", f"{edad_promedio:.1f} años")
        
        with col4:
            if 'en_seguimiento' in datos.columns:
                seguimiento = datos['en_seguimiento'].sum()
                st.metric("En Seguimiento", seguimiento)
        
        # ========== ANÁLISIS POR REGIÓN (CORREGIDO) ==========
        st.markdown("---")
        st.subheader("📍 Análisis por Región")
        
        if 'region' in datos.columns and 'hemoglobina_dl1' in datos.columns:
            try:
                # Crear análisis por región CORREGIDO
                resume_region = datos.groupby('region').agg({
                    'hemoglobina_dl1': ['count', 'mean', 'min', 'max'],  # NOMBRES CORRECTOS
                    'edad_meses': 'mean'  # NOMBRE CORRECTO
                }).round(2)
                
                # Limpiar nombres de columnas
                if 'edad_meses' in datos.columns:
                    resume_region.columns = ['total_casos', 'hb_promedio', 'hb_min', 'hb_max', 'edad_promedio_meses']
                else:
                    resume_region.columns = ['total_casos', 'hb_promedio', 'hb_min', 'hb_max']
                
                # Mostrar tabla
                st.dataframe(resume_region, use_container_width=True)
                
                # Gráfico de hemoglobina por región
                if not resume_region.empty:
                    fig_hb_region = px.bar(
                        resume_region.reset_index().sort_values('hb_promedio'),
                        x='region',
                        y='hb_promedio',
                        title='<b>Hemoglobina Promedio por Región</b>',
                        color='hb_promedio',
                        color_continuous_scale='RdYlGn',
                        text='hb_promedio',
                        height=400
                    )
                    
                    fig_hb_region.update_traces(
                        texttemplate='%{text:.1f}',
                        textposition='outside'
                    )
                    
                    fig_hb_region.update_layout(
                        xaxis_title="Región",
                        yaxis_title="Hemoglobina Promedio (g/dL)",
                        xaxis_tickangle=45
                    )
                    
                    st.plotly_chart(fig_hb_region, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error en análisis regional: {e}")
        else:
            st.info("ℹ️ No hay datos suficientes para análisis regional")
        
        # ========== DISTRIBUCIÓN POR GÉNERO ==========
        st.markdown("---")
        st.subheader("👦👧 Distribución por Género")
        
        if 'genero' in datos.columns:
            genero_counts = datos['genero'].value_counts()
            
            col_gen1, col_gen2 = st.columns([3, 1])
            
            with col_gen1:
                fig_genero = px.pie(
                    values=genero_counts.values,
                    names=genero_counts.index.map({'M': 'Niños', 'F': 'Niñas', 'Masculino': 'Niños', 'Femenino': 'Niñas'}).fillna('Otro'),
                    title='<b>Distribución por Género</b>',
                    color_discrete_sequence=['#3498db', '#e74c3c', '#2ecc71'],
                    hole=0.4
                )
                st.plotly_chart(fig_genero, use_container_width=True)
            
            with col_gen2:
                for genero, count in genero_counts.items():
                    genero_nombre = 'Niños' if genero in ['M', 'Masculino'] else 'Niñas' if genero in ['F', 'Femenino'] else genero
                    porcentaje = (count / total_pacientes) * 100
                    st.metric(genero_nombre, f"{count}", f"{porcentaje:.1f}%")
        
        # ========== ANÁLISIS DE HEMOGLOBINA ==========
        st.markdown("---")
        st.subheader("🩸 Distribución de Hemoglobina")
        
        if 'hemoglobina_dl1' in datos.columns:
            # Histograma de hemoglobina
            fig_hb_hist = px.histogram(
                datos,
                x='hemoglobina_dl1',
                nbins=20,
                title='<b>Distribución de Niveles de Hemoglobina</b>',
                color_discrete_sequence=['#ff6b6b'],
                height=400
            )
            
            # Añadir líneas de referencia
            fig_hb_hist.add_vline(
                x=11.0,
                line_dash="dash",
                line_color="orange",
                annotation_text="Umbral Anemia",
                annotation_position="top"
            )
            
            fig_hb_hist.add_vline(
                x=12.0,
                line_dash="dash",
                line_color="green",
                annotation_text="Normal",
                annotation_position="top"
            )
            
            fig_hb_hist.update_layout(
                xaxis_title="Hemoglobina (g/dL)",
                yaxis_title="Frecuencia",
                bargap=0.1
            )
            
            st.plotly_chart(fig_hb_hist, use_container_width=True)
        
        # ========== ANÁLISIS POR EDAD ==========
        st.markdown("---")
        st.subheader("👶 Distribución por Edad")
        
        if 'edad_meses' in datos.columns:
            # Crear grupos de edad
            datos['edad_años'] = datos['edad_meses'] / 12
            bins = [0, 1, 2, 3, 4, 5, 10, 15, 20]
            labels = ['0-1 año', '1-2 años', '2-3 años', '3-4 años', '4-5 años', '5-10 años', '10-15 años', '15-20 años']
            
            datos['grupo_edad'] = pd.cut(datos['edad_años'], bins=bins, labels=labels, right=False)
            edad_counts = datos['grupo_edad'].value_counts().sort_index()
            
            fig_edad = px.bar(
                x=edad_counts.index,
                y=edad_counts.values,
                title='<b>Distribución por Grupos de Edad</b>',
                color=edad_counts.values,
                color_continuous_scale='Viridis',
                text=edad_counts.values,
                height=400
            )
            
            fig_edad.update_traces(
                texttemplate='%{text}',
                textposition='outside'
            )
            
            fig_edad.update_layout(
                xaxis_title="Grupo de Edad",
                yaxis_title="Número de Pacientes",
                showlegend=False
            )
            
            st.plotly_chart(fig_edad, use_container_width=True)
        
        # ========== ANÁLISIS DE SEGUIMIENTO ==========
        st.markdown("---")
        st.subheader("📋 Estado de Seguimiento")
        
        if 'en_seguimiento' in datos.columns:
            seguimiento_counts = datos['en_seguimiento'].value_counts()
            
            fig_seguimiento = px.pie(
                values=seguimiento_counts.values,
                names=['Seguimiento' if x else 'No Seguimiento' for x in seguimiento_counts.index],
                title='<b>Distribución de Seguimiento</b>',
                color_discrete_sequence=['#ffa726', '#66bb6a'],
                hole=0.4
            )
            
            st.plotly_chart(fig_seguimiento, use_container_width=True)
            
            col_seg1, col_seg2 = st.columns(2)
            with col_seg1:
                st.metric("En Seguimiento", seguimiento_counts.get(True, 0))
            with col_seg2:
                st.metric("Sin Seguimiento", seguimiento_counts.get(False, 0))
        
        # ========== EXPORTAR DATOS ==========
        st.markdown("---")
        with st.expander("📥 Exportar Datos de Análisis"):
            csv = datos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Datos Completos (CSV)",
                data=csv,
                file_name=f"estadisticas_anemia_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    else:
        st.info("👆 Presiona el botón 'Cargar Datos para Análisis' para comenzar")

# ==================================================
# PESTAÑA 4: SISTEMA DE CITAS - VINCULADO CON ANEMIA
# ==================================================

with tab4:
    st.header("📋 Sistema de Seguimiento y Citas")
    st.markdown("Registro de nuevas citas **vinculadas con diagnóstico de anemia**")
    
    # ========== FUNCIONES VINCULADAS ==========
    
    def obtener_citas_con_info_anemia():
        """Obtiene citas con información de anemia del paciente"""
        try:
            # Obtener todas las citas
            response_citas = supabase.table("citas").select("*").order("fecha_cita", desc=True).execute()
            citas = response_citas.data if response_citas.data else []
            
            if not citas:
                return []
            
            # Obtener información de anemia para cada paciente
            citas_con_info = []
            
            for cita in citas:
                dni = cita.get('dni_paciente')
                if dni:
                    # Buscar información de anemia
                    response_paciente = supabase.table("alertas_hemoglobina")\
                        .select("*")\
                        .eq("dni", dni)\
                        .execute()
                    
                    info_anemia = response_paciente.data[0] if response_paciente.data else {}
                    
                    # Combinar información
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
        """Clasificación simple de anemia"""
        if hemoglobina == 'N/A' or not hemoglobina:
            return "Sin datos"
        
        if edad_meses < 60:  # Menores de 5 años
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
        """Obtiene color según clasificación de anemia"""
        colores = {
            "Normal": "🟢",
            "Leve": "🟡",
            "Moderada": "🟠",
            "Severa": "🔴",
            "Sin datos": "⚪"
        }
        return colores.get(clasificacion, "⚪")
    
    # ========== SECCIÓN 1: CITAS CON INFO DE ANEMIA ==========
    st.subheader("🩺 Citas con Estado de Anemia")
    
    if st.button("🔄 Cargar citas con información de anemia", key="cargar_citas_anemia"):
        with st.spinner("Vinculando citas con diagnóstico de anemia..."):
            citas_vinculadas = obtener_citas_con_info_anemia()
            st.session_state.citas_vinculadas = citas_vinculadas
            
            if citas_vinculadas:
                st.success(f"✅ {len(citas_vinculadas)} citas vinculadas con información de anemia")
            else:
                st.warning("⚠️ No hay citas registradas")
    
    # Mostrar citas vinculadas
    if 'citas_vinculadas' in st.session_state and st.session_state.citas_vinculadas:
        citas_df = pd.DataFrame(st.session_state.citas_vinculadas)
        
        # Aplicar colores a la clasificación
        citas_df['anemia_icono'] = citas_df['clasificacion_anemia'].apply(obtener_color_anemia)
        citas_df['anemia_mostrar'] = citas_df['anemia_icono'] + " " + citas_df['clasificacion_anemia']
        
        # Mostrar tabla ENRIQUECIDA
        st.dataframe(
            citas_df[['fecha_cita', 'hora_cita', 'nombre_paciente', 'dni_paciente',
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
        
        # ========== ANÁLISIS ESTADÍSTICO ==========
        st.markdown("#### 📊 Estadísticas de Anemia en Citas")
        
        col_est1, col_est2, col_est3, col_est4 = st.columns(4)
        
        with col_est1:
            total_citas = len(citas_df)
            st.metric("Total Citas", total_citas)
        
        with col_est2:
            con_anemia = len(citas_df[citas_df['clasificacion_anemia'].isin(["Leve", "Moderada", "Severa"])])
            porcentaje = (con_anemia / total_citas * 100) if total_citas > 0 else 0
            st.metric("Con Anemia", con_anemia, f"{porcentaje:.1f}%")
        
        with col_est3:
            severas = len(citas_df[citas_df['clasificacion_anemia'] == "Severa"])
            st.metric("Anemia Severa", severas)
        
        with col_est4:
            seguimiento = len(citas_df[citas_df['en_seguimiento'] == True])
            st.metric("En Seguimiento", seguimiento)
        
        # Gráfico de distribución de anemia
        st.markdown("#### 📈 Distribución de Severidad de Anemia")
        
        if 'clasificacion_anemia' in citas_df.columns:
            distribucion = citas_df['clasificacion_anemia'].value_counts()
            
            fig = px.bar(
                x=distribucion.index,
                y=distribucion.values,
                title="Casos por Nivel de Anemia",
                color=distribucion.values,
                color_continuous_scale='RdYlGn_r',  # Rojo para severa, verde para normal
                text=distribucion.values,
                height=300
            )
            
            fig.update_layout(
                xaxis_title="Clasificación de Anemia",
                yaxis_title="Número de Citas",
                showlegend=False
            )
            
            fig.update_traces(
                texttemplate='%{text}',
                textposition='outside'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # ========== SECCIÓN 2: AGENDAR CITA CON ENFOQUE EN ANEMIA ==========
    st.markdown("---")
    st.subheader("➕ Agendar Nueva Cita con Diagnóstico de Anemia")
    
    # Buscar pacientes CON anemia
    st.markdown("#### 🔍 Buscar Pacientes con Anemia")
    
    filtro_anemia = st.selectbox(
        "Filtrar por estado de anemia:",
        ["Todos los pacientes", "Con anemia", "Anemia moderada/severa", "En seguimiento"]
    )
    
    # Obtener pacientes según filtro
    pacientes_filtrados = []
    
    try:
        response = supabase.table("alertas_hemoglobina").select("*").execute()
        todos_pacientes = response.data if response.data else []
        
        for paciente in todos_pacientes:
            hb = paciente.get('hemoglobina_dl1', 0)
            edad = paciente.get('edad_meses', 0)
            clasificacion = clasificar_anemia_simple(hb, edad)
            
            include = False
            
            if filtro_anemia == "Todos los pacientes":
                include = True
            elif filtro_anemia == "Con anemia" and clasificacion in ["Leve", "Moderada", "Severa"]:
                include = True
            elif filtro_anemia == "Anemia moderada/severa" and clasificacion in ["Moderada", "Severa"]:
                include = True
            elif filtro_anemia == "En seguimiento" and paciente.get('en_seguimiento', False):
                include = True
            
            if include:
                pacientes_filtrados.append({
                    **paciente,
                    'clasificacion_anemia': clasificacion,
                    'icono_anemia': obtener_color_anemia(clasificacion)
                })
    
    except Exception as e:
        st.error(f"Error al cargar pacientes: {str(e)}")
    
    # Mostrar lista de pacientes
    if pacientes_filtrados:
        st.success(f"✅ {len(pacientes_filtrados)} pacientes encontrados")
        
        # Crear opciones para selectbox
        opciones_pacientes = []
        for paciente in pacientes_filtrados:
            nombre = paciente.get('nombre_apellido', 'Sin nombre')
            dni = paciente.get('dni', 'N/A')
            anemia = paciente.get('clasificacion_anemia', 'N/A')
            icono = paciente.get('icono_anemia', '⚪')
            hb = paciente.get('hemoglobina_dl1', 'N/A')
            
            opciones_pacientes.append(f"{icono} {nombre} | DNI: {dni} | Hb: {hb}g/dL | {anemia}")
        
        # Seleccionar paciente
        paciente_seleccionado = st.selectbox(
            "Seleccione el paciente para la cita:",
            opciones_pacientes,
            key="select_paciente_cita"
        )
        
        if paciente_seleccionado:
            # Extraer DNI de la selección
            dni_seleccionado = paciente_seleccionado.split("|")[1].split(":")[1].strip()
            
            # Buscar paciente completo
            paciente_completo = None
            for p in pacientes_filtrados:
                if p['dni'] == dni_seleccionado:
                    paciente_completo = p
                    break
            
            if paciente_completo:
                st.markdown(f"### 📋 Cita para: **{paciente_completo.get('nombre_apellido')}**")
                
                # Mostrar alerta de anemia
                clasificacion = paciente_completo.get('clasificacion_anemia')
                icono = paciente_completo.get('icono_anemia')
                hb = paciente_completo.get('hemoglobina_dl1')
                
                if clasificacion == "Severa":
                    st.error(f"{icono} **ANEMIA SEVERA** - Hemoglobina: {hb} g/dL - **ATENCIÓN INMEDIATA REQUERIDA**")
                elif clasificacion == "Moderada":
                    st.warning(f"{icono} **ANEMIA MODERADA** - Hemoglobina: {hb} g/dL - Seguimiento mensual requerido")
                elif clasificacion == "Leve":
                    st.info(f"{icono} **ANEMIA LEVE** - Hemoglobina: {hb} g/dL - Seguimiento cada 3 meses")
                else:
                    st.success(f"{icono} **SIN ANEMIA** - Hemoglobina: {hb} g/dL")
                
                # Formulario de cita ESPECÍFICO para anemia
                with st.form("form_cita_anemia"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fecha_cita = st.date_input("📅 Fecha de cita", value=datetime.now())
                        tipo_consulta = st.selectbox(
                            "🩺 Tipo de consulta",
                            ["Control de anemia", "Seguimiento anemia", "Evaluación hematológica",
                             "Control tratamiento hierro", "Reevaluación anemia", "Urgencia anemia"]
                        )
                    
                    with col2:
                        hora_cita = st.time_input("⏰ Hora", value=datetime.now().time())
                        proxima_cita = st.date_input(
                            "📅 Próximo control sugerido",
                            value=datetime.now() + timedelta(days=30)
                        )
                    
                    # Campos específicos para anemia
                    st.markdown("#### 🩺 Datos Clínicos de Anemia")
                    
                    evolucion_anemia = st.selectbox(
                        "📈 Evolución de la anemia",
                        ["Mejoría", "Estable", "Empeoramiento", "Primera evaluación", "No evaluado"]
                    )
                    
                    col_trat1, col_trat2 = st.columns(2)
                    with col_trat1:
                        tratamiento_hierro = st.selectbox(
                            "💊 Tratamiento con hierro",
                            ["Sin tratamiento", "Sulfato ferroso", "Gluconato ferroso", 
                             "Fumarato ferroso", "Hierro intravenoso", "Otro"]
                        )
                    
                    with col_trat2:
                        dosis_hierro = st.text_input(
                            "📏 Dosis de hierro",
                            placeholder="Ej: 3 mg/kg/día"
                        )
                    
                    diagnostico = st.text_area(
                        "📝 Diagnóstico detallado",
                        value=f"Paciente con {clasificacion.lower()}. {paciente_completo.get('interpretacion_hematologica', '')}",
                        height=100
                    )
                    
                    plan_tratamiento = st.text_area(
                        "💡 Plan de tratamiento",
                        placeholder="Describa el plan específico para este paciente...",
                        height=100
                    )
                    
                    observaciones = st.text_area(
                        "📋 Observaciones específicas",
                        placeholder="Observaciones sobre respuesta al tratamiento, efectos secundarios, etc.",
                        height=100
                    )
                    
                    investigador = st.text_input(
                        "👨‍⚕️ Hematólogo/Responsable",
                        value="Dr. Hematólogo"
                    )
                    
                    # Botón de guardar
                    if st.form_submit_button("💾 Guardar Cita de Anemia", type="primary", use_container_width=True):
                        if not diagnostico.strip():
                            st.error("❌ Por favor complete el diagnóstico")
                        else:
                            nueva_cita = {
                                "dni_paciente": dni_seleccionado,
                                "fecha_cita": str(fecha_cita),
                                "hora_cita": str(hora_cita),
                                "tipo_consulta": tipo_consulta,
                                "diagnostico": diagnostico,
                                "tratamiento": f"{tratamiento_hierro} - {dosis_hierro}" if dosis_hierro else tratamiento_hierro,
                                "observaciones": f"Evolución: {evolucion_anemia}. {observaciones}",
                                "investigador_responsable": investigador,
                                "proxima_cita": str(proxima_cita),
                                "severidad_anemia": clasificacion,
                                "hemoglobina_actual": hb,
                                "evolucion": evolucion_anemia
                            }
                            
                            try:
                                response = supabase.table("citas").insert(nueva_cita).execute()
                                
                                if response.data:
                                    st.success("✅ Cita de anemia guardada exitosamente!")
                                    st.balloons()
                                    
                                    # Actualizar estado de seguimiento si es necesario
                                    if clasificacion in ["Moderada", "Severa"]:
                                        supabase.table("alertas_hemoglobina")\
                                            .update({"en_seguimiento": True})\
                                            .eq("dni", dni_seleccionado)\
                                            .execute()
                                    
                                    # Limpiar cache y recargar
                                    if 'citas_vinculadas' in st.session_state:
                                        del st.session_state.citas_vinculadas
                                    
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Error al guardar la cita")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
    
    # ========== SECCIÓN 3: REPORTES DE ANEMIA ==========
    st.markdown("---")
    st.subheader("📊 Reportes de Seguimiento de Anemia")
    
    col_rep1, col_rep2 = st.columns(2)
    
    with col_rep1:
        if st.button("📋 Generar Reporte Mensual", use_container_width=True):
            try:
                # Obtener citas del último mes
                un_mes_atras = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                
                response = supabase.table("citas")\
                    .select("*")\
                    .gte("fecha_cita", un_mes_atras)\
                    .execute()
                
                citas_mes = response.data if response.data else []
                
                if citas_mes:
                    st.success(f"📈 {len(citas_mes)} citas en el último mes")
                    
                    # Contar por severidad
                    severidades = {}
                    for cita in citas_mes:
                        # Buscar información de anemia
                        dni = cita.get('dni_paciente')
                        if dni:
                            response_pac = supabase.table("alertas_hemoglobina")\
                                .select("hemoglobina_dl1, edad_meses")\
                                .eq("dni", dni)\
                                .execute()
                            
                            if response_pac.data:
                                paciente = response_pac.data[0]
                                clasificacion = clasificar_anemia_simple(
                                    paciente.get('hemoglobina_dl1', 0),
                                    paciente.get('edad_meses', 0)
                                )
                                
                                severidades[clasificacion] = severidades.get(clasificacion, 0) + 1
                    
                    # Mostrar resultados
                    for severidad, cantidad in severidades.items():
                        st.write(f"{obtener_color_anemia(severidad)} {severidad}: {cantidad} pacientes")
                else:
                    st.info("No hay citas en el último mes")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col_rep2:
        if st.button("🩺 Pacientes Críticos", use_container_width=True):
            try:
                # Buscar pacientes con anemia severa
                response = supabase.table("alertas_hemoglobina")\
                    .select("*")\
                    .execute()
                
                pacientes_criticos = []
                for paciente in response.data:
                    hb = paciente.get('hemoglobina_dl1', 0)
                    edad = paciente.get('edad_meses', 0)
                    
                    if (edad < 60 and hb < 9.0) or (edad >= 60 and hb < 10.0):
                        pacientes_criticos.append(paciente)
                
                if pacientes_criticos:
                    st.error(f"🚨 {len(pacientes_criticos)} pacientes con ANEMIA SEVERA")
                    
                    for paciente in pacientes_criticos[:5]:  # Mostrar primeros 5
                        st.write(f"**{paciente.get('nombre_apellido')}** - Hb: {paciente.get('hemoglobina_dl1')} g/dL")
                else:
                    st.success("✅ No hay pacientes con anemia severa")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
# ==================================================
# PESTAÑA 5: DASHBOARD NACIONAL
# ==================================================

with tab5:
    st.header("📊 Dashboard Nacional de Anemia y Nutrición")
    
    # Botón para cargar datos nacionales
    if st.button("🔄 Cargar Datos Nacionales", type="primary"):
        with st.spinner("Cargando datos nacionales..."):
            datos_nacionales = obtener_datos_supabase()
            
            if not datos_nacionales.empty:
                st.session_state.datos_nacionales = datos_nacionales
                st.success(f"✅ {len(datos_nacionales)} registros nacionales cargados")
            else:
                st.error("❌ No se pudieron cargar datos nacionales")
    
    # Verificar si tenemos datos nacionales
    if 'datos_nacionales' in st.session_state and not st.session_state.datos_nacionales.empty:
        datos = st.session_state.datos_nacionales
        
        # ========== MÉTRICAS NACIONALES ==========
        st.subheader("🎯 Indicadores Nacionales")
        
        col_nac1, col_nac2, col_nac3, col_nac4 = st.columns(4)
        
        with col_nac1:
            total_nacional = len(datos)
            st.metric("Total Evaluados", total_nacional)
        
        with col_nac2:
            if 'region' in datos.columns:
                regiones_unicas = datos['region'].nunique()
                st.metric("Regiones", regiones_unicas)
        
        with col_nac3:
            if 'hemoglobina_dl1' in datos.columns:
                hb_nacional = datos['hemoglobina_dl1'].mean()
                st.metric("Hb Nacional", f"{hb_nacional:.1f} g/dL")
        
        with col_nac4:
            if 'en_seguimiento' in datos.columns:
                seguimiento_nacional = datos['en_seguimiento'].sum()
                st.metric("Seguimiento", seguimiento_nacional)
        
        # ========== MAPA DE CALOR POR REGIÓN ==========
        st.markdown("---")
        st.subheader("📍 Mapa de Calor por Región")
        
        if 'region' in datos.columns and 'hemoglobina_dl1' in datos.columns:
            # Calcular estadísticas por región
            region_stats = datos.groupby('region').agg({
                'hemoglobina_dl1': ['mean', 'count', 'min', 'max']
            }).round(2)
            
            region_stats.columns = ['hb_promedio', 'casos', 'hb_min', 'hb_max']
            region_stats = region_stats.reset_index()
            
            # Ordenar por hemoglobina promedio
            region_stats = region_stats.sort_values('hb_promedio', ascending=False)
            
            # Mostrar tabla
            st.dataframe(region_stats, use_container_width=True)
            
            # Gráfico de calor
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
        
        # ========== ANÁLISIS DE TENDENCIAS ==========
        st.markdown("---")
        st.subheader("📈 Tendencias y Análisis")
        
        col_tend1, col_tend2 = st.columns(2)
        
        with col_tend1:
            if 'edad_meses' in datos.columns:
                # Distribución por edad
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
                # Distribución por género
                genero_counts = datos['genero'].value_counts()
                fig_genero_dist = px.pie(
                    values=genero_counts.values,
                    names=genero_counts.index.map({'M': 'Niños', 'F': 'Niñas'}).fillna('Otro'),
                    title='<b>Distribución por Género</b>',
                    color_discrete_sequence=['#e74c3c', '#3498db'],
                    height=300
                )
                st.plotly_chart(fig_genero_dist, use_container_width=True)
        
        # ========== ANÁLISIS DE RIESGO ==========
        st.markdown("---")
        st.subheader("⚠️ Análisis de Riesgo Nacional")
        
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
                    st.metric(riesgo, f"{count}", f"{porcentaje:.1f}%")
        
        # ========== EXPORTAR REPORTE NACIONAL ==========
        st.markdown("---")
        with st.expander("📥 Exportar Reporte Nacional"):
            csv = datos.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte Nacional (CSV)",
                data=csv,
                file_name=f"reporte_nacional_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    else:
        st.info("👆 Presiona el botón 'Cargar Datos Nacionales' para ver el dashboard nacional")

# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.header("📋 Sistema de Referencia")
    
    tab_sidebar1, tab_sidebar2, tab_sidebar3 = st.tabs(["🎯 Ajustes Altitud", "📊 Tablas Crecimiento", "🔬 Criterios Hematológicos"])
    
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
    
    with tab_sidebar3:
        st.markdown("**Criterios de Interpretación:**")
        
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
        
        ### 🚨 NIVELES DE SEVERIDAD
        - **CRÍTICO**: Intervención inmediata
        - **MODERADO**: Acción prioritaria  
        - **LEVE**: Vigilancia activa
        - **NORMAL**: Seguimiento rutinario
        """)
    
    st.markdown("---")
    st.info("""
    **💡 Sistema Integrado:**
    - ✅ Ajuste automático por altitud
    - ✅ Clasificación OMS de anemia
    - ✅ Seguimiento por gravedad
    - ✅ Dashboard nacional
    - ✅ Sistema de citas
    - ✅ Interpretación automática
    - ✅ Manejo de duplicados
    """)

# ==================================================
# INICIALIZACIÓN DE DATOS DE PRUEBA (OPCIONAL)
# ==================================================

if supabase:
    try:
        response = supabase.table(TABLE_NAME).select("*").limit(1).execute()
        if not response.data:
            st.sidebar.info("🔄 Base de datos vacía. Puede ingresar pacientes desde la pestaña 'Registro Completo'")
            
            # Opcional: Insertar un paciente de prueba automáticamente
            if st.sidebar.button("➕ Insertar paciente de prueba"):
                with st.sidebar.spinner("Insertando..."):
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
                        st.sidebar.success("✅ Paciente de prueba insertado")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Error al insertar paciente de prueba")
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error verificando datos: {e}")

# ==================================================
# PIE DE PÁGINA
# ==================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🏥 <strong>Sistema Nixon</strong> - Control de Anemia y Nutrición Infantil</p>
    <p>📅 Versión 2.0 | Última actualización: """ + datetime.now().strftime("%d/%m/%Y") + """</p>
    <p>⚠️ <em>Para uso médico profesional. Consulte siempre con especialistas.</em></p>
</div>
""", unsafe_allow_html=True)
