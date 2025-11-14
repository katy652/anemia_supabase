import streamlit as st
import pandas as pd
from supabase import create_client, Client 
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
import os

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Sistema de Predicción de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ¡ADECUACIÓN A TU TABLA! Nombre de la tabla en tu base de datos de Supabase.
TABLE_NAME = "alertas" 
MODEL_PATH = "modelo_columns.joblib" # Asegúrate de que este nombre coincida con tu archivo.

# Inicializar y cachear el modelo de ML
@st.cache_resource
def load_anemia_model(path):
    """Carga el modelo de Machine Learning usando joblib."""
    if not os.path.exists(path):
        st.error(f"❌ Error: El archivo del modelo '{path}' no fue encontrado. Asegúrate de que el archivo exista en la misma carpeta.")
        st.stop()
        return None
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        st.error(f"❌ Error al cargar el modelo joblib: {e}")
        st.stop()
        return None

# Inicializar y cachear el cliente de Supabase
@st.cache_resource(ttl=3600)
def init_supabase() -> Client:
    """Inicializa y retorna el cliente de Supabase usando st.secrets."""
    try:
        # Intenta usar variables de entorno o st.secrets
        if 'SUPABASE_URL' in os.environ and 'SUPABASE_KEY' in os.environ:
           url = "https://kwsuszkblbejvliniggd.supabase.co"
           key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt3c3VzemtibGJlanZsaW5pZ2dkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2ODE0NTUsImV4cCI6MjA3NzI1NzQ1NX0.DQpt-rSNprcUrbOLTgUEEn_0jFIuSX5b0AVuVirk0vw"
        elif "supabase" in st.secrets:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        else:
             st.error("Error: Las credenciales de Supabase no se encontraron en '.streamlit/secrets.toml' o variables de entorno.")
             st.stop()
             return None
             
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error al inicializar Supabase: {e}")
        st.stop()
        return None

# Carga el modelo y el cliente de Supabase
model = load_anemia_model(MODEL_PATH)
supabase = init_supabase()


# --- FUNCIONES DE INTERACCIÓN CON SUPABASE ---

def insert_data_to_supabase(data_to_insert: dict):
    """Inserta una nueva fila de datos en la tabla de Supabase."""
    if supabase is None:
        return False
    
    try:
        # Se inserta en la tabla 'alertas'
        response = supabase.table(TABLE_NAME).insert(data_to_insert).execute()
        
        if response.data:
            # Limpia la caché para forzar la recarga de la tabla después de insertar
            get_data_from_supabase.clear() 
            return response.data[0]
        else:
            st.error("❌ Fallo en la inserción: Supabase no devolvió datos.")
            return False
            
    except Exception as e:
        # Aquí capturamos errores de schema mismatch
        st.error(f"❌ Error al insertar datos. Verifique los nombres y tipos de columna en la tabla '{TABLE_NAME}': {e}")
        get_data_from_supabase.clear() 
        return False

@st.cache_data(ttl=600)
def get_data_from_supabase():
    """Obtiene y procesa todos los datos de la tabla para visualización."""
    if supabase is None:
        return pd.DataFrame()
        
    try:
        # Se obtiene el máximo de filas de la tabla 'alertas'
        response = supabase.table(TABLE_NAME).select("*").order("fecha_alerta", desc=True).limit(5000).execute()
        data = response.data
        if not data:
             return pd.DataFrame()
             
        df = pd.DataFrame(data)
        
        # --- PROCESAMIENTO CRÍTICO DE COLUMNAS (Manejo de TimeStamp) ---
        # Si la columna 'fecha_alerta' existe, la usamos para ordenar y renombrar a 'Time'
        if 'fecha_alerta' in df.columns:
            try:
                df['Time'] = pd.to_datetime(df['fecha_alerta'])
                cols = ['Time'] + [col for col in df.columns if col != 'Time']
                df = df[cols]
            except Exception as e:
                st.warning(f"No se pudo convertir la columna 'fecha_alerta' a datetime. Error: {e}")
                
        # Asegurar que las columnas numéricas sean float
        # Usamos 'hemoglobina' (el nombre de tu columna) y las de ML por si se guardan
        numeric_cols = ['Hb', 'MCH', 'MCHC', 'MCV', 'age', 'hemoglobina', 'edad']
        for col in numeric_cols:
            if col in df.columns:
                 df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
        
    except Exception as e:
        st.error(f"Error al cargar datos existentes desde Supabase. Error: {e}")
        return pd.DataFrame()


# --- LÓGICA DE PREDICCIÓN (FUNCIÓN REAL CON MODELO) ---
def make_prediction(Hb, MCH, MCHC, MCV, sex, age, model):
    """
    Usa el modelo de Machine Learning cargado para predecir si hay anemia.
    Asume que el modelo fue entrenado con 7 características: 
    [Hb, MCH, MCHC, MCV, age, sex_F, sex_M]
    """
    
    if model is None:
        return "ERROR_MODELO_NO_CARGADO"
    
    # 1. Preparar la entrada del modelo
    # Se normaliza la entrada del selector de Streamlit a un código de una letra (F o M)
    sex_code = sex[0].upper() # Obtiene 'F' de 'Femenino' o 'M' de 'Masculino'

    # Codificación One-Hot para 'sex' (Crea las 2 columnas binarias)
    sex_F = 1 if sex_code == "F" else 0 
    sex_M = 1 if sex_code == "M" else 0

    # Crear el array de entrada (X). 
    # ORDEN: [Hb, MCH, MCHC, MCV, age, sex_F, sex_M] => 7 COLUMNAS
    X = np.array([[Hb, MCH, MCHC, MCV, age, sex_F, sex_M]]) 
    
    # Realizar la predicción
    try:
        prediction_result = str(model.predict(X)[0]) 
        return prediction_result
    except Exception as e:
        st.error(f"❌ Error al ejecutar la predicción: {e}. Confirme que el modelo espera 7 columnas de entrada (features) en este orden.")
        return "ERROR_PREDICCION"


# --- FUNCIONES DE VISUALIZACIÓN ---

def plot_histogram(df, column, title):
    """Genera un histograma para una columna numérica, coloreado por columna de riesgo/predicción."""
    # Usamos la columna 'riesgo' (el nombre de tu columna) para el color
    # Mapeo de colores basado en los valores que se ven en tu tabla
    color_map = {
        "RIESGO INDEFINIDO (¡A DESHABILITAD...)": "red", 
        "REGISTRADO": "green", 
        "ANEMIA": "red", # Incluimos estos por si el modelo devuelve un valor limpio
        "NORMAL": "green"
    }
    
    color_col = 'riesgo' # Usamos 'riesgo' ya que es la columna de tu tabla
    
    if color_col not in df.columns:
        return go.Figure()

    fig = px.histogram(
        df, 
        x=column, 
        color=color_col, # Usar la columna de riesgo/predicción para el color
        marginal="box", 
        nbins=20,
        title=f'Histograma de {title}',
        template="plotly_white",
        color_discrete_map=color_map 
    )
    fig.update_layout(bargap=0.1)
    return fig

def plot_boxplot(df, column, title):
    """Genera un diagrama de caja para una columna numérica, coloreado por columna de riesgo/predicción."""
    color_map = {
        "RIESGO INDEFINIDO (¡A DESHABILITAD...)": "red", 
        "REGISTRADO": "green", 
        "ANEMIA": "red", 
        "NORMAL": "green"
    }
    color_col = 'riesgo' # Usamos 'riesgo' ya que es la columna de tu tabla
    
    if color_col not in df.columns:
        return go.Figure()

    fig = px.box(
        df, 
        y=column, 
        color=color_col, # Usar la columna de riesgo/predicción para el color
        title=f'Diagrama de Caja de {title}',
        template="plotly_white",
        color_discrete_map=color_map
    )
    return fig


# --- VISTA PRINCIPAL DE LA APLICACIÓN ---

st.title("🩸 Sistema de Detección y Predicción de Anemia")
st.markdown("---")

# Crea dos columnas principales para el formulario y el estado
col_form, col_data = st.columns([1, 1])

# --- Columna del Formulario (INSERCIÓN DE DATOS) ---
with col_form:
    st.header("1. Ingreso de Parámetros")
    st.markdown("Introduce los valores hematológicos y demográficos.")

    # Formulario de Streamlit
    with st.form(key='anemia_prediction_form'):
        st.subheader("Datos de la Muestra")
        
        # Campos adicionales para la tabla 'alertas'
        nombre_paciente = st.text_input('Nombre y Apellido', help="Necesario para el registro en la tabla 'alertas'")
        edad_paciente = st.number_input('Edad (años)', min_value=1, max_value=120, value=35, step=1)
        # Cambiamos las opciones del selectbox para que sean más descriptivas
        sex_paciente = st.selectbox('Sexo', options=["Femenino", "Masculino"], help="Seleccione el sexo del paciente.")
        region_paciente = st.text_input('Región/Ciudad', value="NO ESPECIFICADO", help="Región del paciente para el registro")

        # Campos de entrada que usa el modelo 
        st.subheader("Valores Hematológicos para Predicción")
        # Los valores de Hb/MCH/MCHC/MCV son la entrada del modelo
        hb_modelo = st.number_input('Hemoglobina (Hb g/dL)', min_value=0.0, max_value=25.0, value=13.0, step=0.1, help="Concentración de Hemoglobina en la sangre.")
        mch_modelo = st.number_input('Hemoglobina Corpuscular Media (MCH pg)', min_value=15.0, max_value=40.0, value=28.0, step=0.1, help="Cantidad promedio de Hemoglobina por glóbulo rojo.")
        mchc_modelo = st.number_input('Concentración de Hemoglobina Corpuscular Media (MCHC g/dL)', min_value=25.0, max_value=40.0, value=33.0, step=0.1, help="Concentración promedio de Hemoglobina en un volumen de glóbulos rojos.")
        mcv_modelo = st.number_input('Volumen Corpuscular Medio (MCV fL)', min_value=60.0, max_value=120.0, value=90.0, step=0.1, help="Tamaño promedio de los glóbulos rojos.")

        # Botón para enviar el formulario
        submit_button = st.form_submit_button(label='Obtener Predicción y Guardar')

    # Lógica al enviar el formulario
    if submit_button:
        # 1. Realizar la Predicción usando el modelo real 
        prediction_result = make_prediction(hb_modelo, mch_modelo, mchc_modelo, mcv_modelo, sex_paciente, edad_paciente, model)
        
        if "ERROR" in prediction_result:
            st.error("No se pudo obtener la predicción. Confirme la estructura de entrada del modelo.")
        else:
            # 2. Mapear la predicción al campo 'riesgo' y establecer 'sugerencia' para Supabase
            if prediction_result.lower() == "anemia":
                # Usamos un valor similar al de tu tabla para 'riesgo' y una sugerencia por defecto
                riesgo_supa = "RIESGO INDEFINIDO (¡A DESHABILITAD...)" 
                sugerencia_supa = "Revisión urgente de historial clínico y hábitos alimenticios." 
            else:
                riesgo_supa = "REGISTRADO" 
                sugerencia_supa = "Recomendaciones Generales de seguimiento." 
                
            # 3. Preparar los datos para Supabase (usando los nombres de columna de tu tabla 'alertas')
            new_record = {
                # Columnas de la tabla 'alertas'
                "nombre_apellido": nombre_paciente,
                "edad": edad_paciente,
                "hemoglobina": hb_modelo, # Mapeado a la columna 'hemoglobina'
                "riesgo": riesgo_supa,
                "sugerencia": sugerencia_supa,
                "region": region_paciente,
                
                # Variables adicionales para análisis (opcional, si estas columnas existen en tu DB)
                "Hb": hb_modelo, "MCH": mch_modelo, "MCHC": mchc_modelo, "MCV": mcv_modelo,
                "sex": sex_paciente[0], # Guardamos F o M
                "prediction": prediction_result, 
            }
            
            # 4. Insertar datos en Supabase
            inserted_data = insert_data_to_supabase(new_record)
            
            if inserted_data:
                # 5. Mostrar el Resultado de la Predicción al usuario
                st.success("✅ ¡Datos guardados en Supabase con éxito!")

                st.markdown("### Resultado de la Predicción del Modelo:")
                if prediction_result.lower() == "anemia":
                    st.error(f"Resultado: **{prediction_result}** 🛑")
                    st.warning("Se sugiere revisión médica basada en la predicción del modelo.")
                elif prediction_result.lower() == "normal":
                    st.success(f"Resultado: **{prediction_result}** ✅")
                    st.info("El modelo predice un estado normal.")
                else: 
                    st.warning(f"Resultado: **{prediction_result}** 🟡")
                    st.info("Resultado desconocido. Revisar valores.")
            else:
                st.error("❌ Fallo en la inserción de datos. Revise la configuración de Supabase.")


# --- Columna de Visualización de Datos (CARGA Y ANÁLISIS) ---
with col_data:
    st.header(f"2. Análisis de Registros Históricos ({TABLE_NAME})")
    
    # Carga los datos de la base de datos
    df_data = get_data_from_supabase()

    if not df_data.empty:
        st.markdown(f"**Total de registros:** `{len(df_data)}`")
        
        # Crear pestañas para organizar la visualización
        tab_data, tab_stats = st.tabs(["📊 Datos y Distribución", "📈 Gráficos de Variables"])
        
        # --- Pestaña de Datos y Distribución ---
        with tab_data:
            st.subheader("Registros Históricos (Últimos 5000)")
            # Muestra las columnas principales de tu tabla
            display_cols = ['Time', 'nombre_apellido', 'edad', 'hemoglobina', 'riesgo', 'sugerencia', 'region']
            df_display = df_data[[col for col in display_cols if col in df_data.columns]]
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de Distribución (Pie Chart)
            st.subheader("Distribución de Resultados Históricos ('riesgo')")
            if 'riesgo' in df_data.columns:
                df_cleaned = df_data.dropna(subset=['riesgo'])
                counts = df_cleaned['riesgo'].value_counts().reset_index()
                counts.columns = ['Resultado', 'Cantidad']
                
                # Mapeo de colores para el gráfico de torta
                color_map_pie = {
                    'RIESGO INDEFINIDO (¡A DESHABILITAD...)': '#E91E63', 
                    'REGISTRADO': '#4CAF50'
                }
                
                fig_pie = px.pie(
                    counts, 
                    names='Resultado', 
                    values='Cantidad',
                    title='Distribución de los Resultados Históricos',
                    color='Resultado',
                    color_discrete_map=color_map_pie
                )
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

        # --- Pestaña de Gráficos de Variables (Histogramas y Boxplots) ---
        with tab_stats:
            st.subheader("Análisis Detallado de Variables Hematológicas")
            
            # Variables a analizar (usamos la columna 'hemoglobina' de tu tabla)
            # Nota: Si las columnas MCH, MCHC, MCV no existen en tu tabla, no se graficarán.
            hematology_cols = ['hemoglobina', 'MCH', 'MCHC', 'MCV']
            
            # Generar Histograma y Boxplot para cada variable
            for col_name in hematology_cols:
                if col_name in df_data.columns and 'riesgo' in df_data.columns:
                    st.markdown(f"#### Análisis de {col_name} por Resultado de Riesgo")
                    col_hist, col_box = st.columns(2)
                    
                    with col_hist:
                        fig_hist = plot_histogram(df_data, col_name, col_name)
                        st.plotly_chart(fig_hist, use_container_width=True)
                        
                    with col_box:
                        fig_box = plot_boxplot(df_data, col_name, col_name)
                        st.plotly_chart(fig_box, use_container_width=True)
                
    else:
        st.info(f"No hay datos históricos en la tabla '{TABLE_NAME}' para mostrar aún. Ingresa el primer registro.")
