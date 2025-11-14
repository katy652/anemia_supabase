# Modificaciones para corregir el AttributeError en la columna de fecha.

import streamlit as st
from supabase import create_client, Client
import pandas as pd
import random
import uuid
from datetime import datetime
import time

# --- CONFIGURACIÓN Y CONEXIÓN A SUPABASE ---

@st.cache_resource(ttl=3600)
def init_supabase() -> Client:
    """Inicializa y retorna el cliente de Supabase."""
    # Lee las credenciales del archivo .streamlit/secrets.toml
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        client = create_client(url, key)
        st.session_state.db = client # Guarda el cliente en session_state
        return client
    except Exception as e:
        st.error(f"Error al inicializar Supabase. Asegúrate de que .streamlit/secrets.toml es correcto. Error: {e}")
        return None

# --- CONSTANTES ---
TABLA_ALERTAS = "alertas_anemia"
TABLA_MODELO = "modelo_anemia"
TABLA_HISTORICO = "historico_casos"
VOZ_TTS = "Leda"

# --- FUNCIONES DE ALERTA Y DIAGNÓSTICO ---

def obtener_alertas_pendientes_o_seguimiento(supabase_client: Client):
    """
    Obtiene los casos de alerta pendientes o en seguimiento (estado 'ALERTA' o 'SEGUIMIENTO').
    
    Corrige la columna de fecha para evitar el AttributeError.
    """
    st.subheader("1. Casos de Monitoreo Activo (Pendientes y En Seguimiento) - (Simulación)")
    st.info("Intentando obtener y formatear fechas...")
    
    # 1. Obtener datos
    try:
        response = supabase_client.table(TABLA_ALERTAS).select("*").in_('estado', ['ALERTA', 'SEGUIMIENTO']).execute()
        data = response.data
        
        if not data:
            st.warning("No hay alertas pendientes o en seguimiento actualmente.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        
        # 2. CONVERSIÓN CRÍTICA DE FECHA (CORRECCIÓN)
        # El error ocurre porque la columna debe ser de tipo datetime antes de usar .dt.strftime().
        # La columna 'fecha Alerta' viene como string desde Supabase, aunque parezca una fecha.
        
        # Primero, intenta convertir la columna a tipo datetime.
        df['fecha Alerta'] = pd.to_datetime(df['fecha Alerta'], errors='coerce')

        # Se simula una columna con fecha en formato string para mostrar el proceso de corrección
        # Esto es solo para ilustración y puede ser ignorado si la columna 'fecha Alerta' ya se limpió arriba.
        # df['Fecha Alerta Str'] = df['fecha Alerta'].astype(str)
        # st.dataframe(df[['_Paciente', 'Fecha Alerta Str']])
        
        # Ahora que la columna es tipo datetime, se puede usar .dt.strftime()
        df['Fecha Formateada'] = df['fecha Alerta'].dt.strftime('%d-%m-%Y')
        
        st.success("✅ Columna 'fecha Alerta' convertida correctamente a formato datetime.")
        st.dataframe(df[['_Paciente', 'fecha Alerta', 'Fecha Formateada']].head(3))
        
        # Simulación de otros datos necesarios para el diagnóstico
        df['Hemoglobina'] = [10.5, 9.2, 9.8] # Datos simulados
        
        st.subheader("Resultado después del Formato")
        st.dataframe(df[['_Paciente', 'Hemoglobina', 'fecha Alerta', 'Fecha Formateada']])
        
        return df
    
    except Exception as e:
        st.error(f"Error al obtener o procesar alertas: {e}")
        return pd.DataFrame()


# --- FUNCIÓN PRINCIPAL DEL MONITOR ---

def vista_monitoreo(supabase_client: Client):
    """Muestra la vista de Monitoreo y Gestión de Alertas."""
    st.title("🏥 Monitoreo y Gestión de Alertas (Supabase Simulada)")

    # Si el cliente no está inicializado, no continuar.
    if not supabase_client:
        st.warning("La conexión a Supabase no está lista.")
        return

    # Obtener y mostrar alertas (usando la función corregida)
    df_monitoreo = obtener_alertas_pendientes_o_seguimiento(supabase_client)

    if not df_monitoreo.empty:
        st.subheader("2. Resumen de Alertas Activas")
        st.write(f"Total de casos en monitoreo: **{len(df_monitoreo)}**")
        st.dataframe(df_monitoreo[['_Paciente', 'Hemoglobina', 'Fecha Formateada', 'estado']])


# --- FUNCIÓN PRINCIPAL DE LA APLICACIÓN ---

def main():
    """Función principal que ejecuta la aplicación Streamlit."""
    
    # Inicializar cliente Supabase (usa el recurso en caché)
    supabase_client = init_supabase()

    # Si la inicialización fue exitosa y tenemos un cliente
    if supabase_client:
        vista_monitoreo(supabase_client)
    else:
        st.error("No se pudo establecer la conexión con la base de datos. Por favor, revisa tus credenciales.")


if __name__ == '__main__':
    main()
