import streamlit as st
import pandas as pd
from supabase import create_client, Client 
import plotly.express as px
import plotly.graph_objects as go
import joblib
import numpy as np
import os
# No es necesario importar LabelEncoder a menos que lo uses para la salida,
# pero es una buena práctica si tu modelo lo requiere en alguna parte del pipeline.

# --- CONFIGURACIÓN E INICIALIZACIÓN ---

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Sistema de Predicción de Anemia",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Nombre de la tabla en tu base de datos de Supabase.
TABLE_NAME = "data" 
MODEL_PATH = "modelo_columns.joblib" # Asegúrate de que este nombre coincida EXACTAMENTE con tu archivo.

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
        # Asegúrate de que las credenciales estén en .streamlit/secrets.toml
        # Usamos variables globales para compatibilidad si no se usa st.secrets
        if 'SUPABASE_URL' in os.environ and 'SUPABASE_KEY' in os.environ:
            url = os.environ['SUPABASE_URL']
            key = os.environ['SUPABASE_KEY']
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
        # Aseguramos que solo se insertan las columnas que existen en la tabla
        response = supabase.table(TABLE_NAME).insert(data_to_insert).execute()
        
        if response.data:
            # Limpia la caché para forzar la recarga de la tabla después de insertar
            get_data_from_supabase.clear() 
            return response.data[0]
        else:
            # Si response.data es vacío pero no hubo excepción
            st.error("❌ Fallo en la inserción: Supabase no devolvió datos.")
            return False
            
    except Exception as e:
        # Aquí capturamos errores de schema mismatch (columna inexistente o tipo incorrecto)
        st.error(f"❌ Error al insertar datos. Verifique si la tabla '{TABLE_NAME}' existe y los tipos de columna coinciden: {e}")
        get_data_from_supabase.clear() 
        return False

@st.cache_data(ttl=600)
def get_data_from_supabase():
    """Obtiene y procesa todos los datos de la tabla para visualización."""
    if supabase is None:
        return pd.DataFrame()
        
    try:
        # Se obtiene el máximo de filas para evitar truncamiento
        response = supabase.table(TABLE_NAME).select("*").order("created_at", desc=True).limit(5000).execute()
        data = response.data
        if not data:
             return pd.DataFrame()
             
        df = pd.DataFrame(data)
        
        # --- PROCESAMIENTO CRÍTICO DE COLUMNAS (Manejo de TimeStamp) ---
        time_cols = [col for col in df.columns if 'created_at' in col.lower()]
        if time_cols:
            try:
                # Se renombra a 'Time' usando la primera columna de tiempo encontrada
                df['Time'] = pd.to_datetime(df[time_cols[0]])
                if 'Time' in df.columns:
                    # Mueve 'Time' al inicio para mejor visualización
                    cols = ['Time'] + [col for col in df.columns if col != 'Time']
                    df = df[cols]
            except Exception as e:
                st.warning(f"No se pudo convertir la columna de tiempo a datetime. Error: {e}")
                
        # Asegurar que las columnas numéricas sean float
        numeric_cols = ['Hb', 'MCH', 'MCHC', 'MCV', 'age']
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
    
    ¡CORRECCIÓN CRÍTICA IMPLEMENTADA AQUÍ!
    Se asume que el modelo fue entrenado con 7 características: 
    [Hb, MCH, MCHC, MCV, age, sex_F, sex_M]
    """
    
    if model is None:
        return "ERROR_MODELO_NO_CARGADO"
    
    # 1. Preparar la entrada del modelo
    
    # CORRECCIÓN: Codificación One-Hot para 'sex' (Crea las 2 columnas binarias)
    sex_F = 1 if sex == "F" else 0 # 1 si es Femenino, 0 si es Masculino
    sex_M = 1 if sex == "M" else 0 # 1 si es Masculino, 0 si es Femenino

    # Crear el array de entrada (X). 
    # El orden es FUNDAMENTAL y debe coincidir con el entrenamiento.
    # ORDEN: [Hb, MCH, MCHC, MCV, age, sex_F, sex_M] => 7 COLUMNAS
    X = np.array([[Hb, MCH, MCHC, MCV, age, sex_F, sex_M]]) 
    
    # Realizar la predicción
    try:
        # prediction_result será un array, tomamos el primer elemento [0]
        prediction_result = str(model.predict(X)[0]) 
        return prediction_result
    except Exception as e:
        # Si el error es "expected N features, got M", el problema está en la línea de 'X' arriba.
        st.error(f"❌ Error al ejecutar la predicción: {e}. Confirme que el modelo espera 7 columnas de entrada (features) en este orden.")
        return "ERROR_PREDICCION"


# --- FUNCIONES DE VISUALIZACIÓN ---

def plot_histogram(df, column, title):
    """Genera un histograma para una columna numérica, coloreado por predicción."""
    # Aseguramos que solo haya dos categorías para el color (o las que existan)
    color_map = {"Anemia": "red", "Normal": "green"}
    fig = px.histogram(
        df, 
        x=column, 
        color="prediction", 
        marginal="box", 
        nbins=20,
        title=f'Histograma de {title}',
        template="plotly_white",
        color_discrete_map=color_map 
    )
    fig.update_layout(bargap=0.1)
    return fig

def plot_boxplot(df, column, title):
    """Genera un diagrama de caja para una columna numérica, coloreado por predicción."""
    color_map = {"Anemia": "red", "Normal": "green"}
    fig = px.box(
        df, 
        y=column, 
        color="prediction", 
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
    st.markdown("Introduce los valores hematológicos para obtener la predicción y guardar el registro.")

    # Formulario de Streamlit
    with st.form(key='anemia_prediction_form'):
        st.subheader("Datos de la Muestra")
        
        # Campos de entrada
        Hb = st.number_input('Hemoglobina (Hb g/dL)', min_value=0.0, max_value=25.0, value=13.0, step=0.1, help="Concentración de Hemoglobina en la sangre.")
        MCH = st.number_input('Hemoglobina Corpuscular Media (MCH pg)', min_value=15.0, max_value=40.0, value=28.0, step=0.1, help="Cantidad promedio de Hemoglobina por glóbulo rojo.")
        MCHC = st.number_input('Concentración de Hemoglobina Corpuscular Media (MCHC g/dL)', min_value=25.0, max_value=40.0, value=33.0, step=0.1, help="Concentración promedio de Hemoglobina en un volumen de glóbulos rojos.")
        MCV = st.number_input('Volumen Corpuscular Medio (MCV fL)', min_value=60.0, max_value=120.0, value=90.0, step=0.1, help="Tamaño promedio de los glóbulos rojos.")
        
        st.subheader("Datos Demográficos")
        sex = st.selectbox('Sexo', options=["F", "M"], help="Femenino o Masculino.")
        age = st.number_input('Edad (años)', min_value=1, max_value=120, value=35, step=1)
        
        # Botón para enviar el formulario
        submit_button = st.form_submit_button(label='Obtener Predicción y Guardar')

    # Lógica al enviar el formulario
    if submit_button:
        # 1. Realizar la Predicción usando el modelo real cargado
        prediction_result = make_prediction(Hb, MCH, MCHC, MCV, sex, age, model)
        
        if "ERROR" in prediction_result:
            # El mensaje de error detallado se muestra en la función make_prediction.
            st.error("No se pudo obtener la predicción. Revise los logs en la consola de Streamlit para más detalles sobre el error de 'features'.")
        else:
            # 2. Preparar los datos para Supabase (Aquí se guarda el valor original de 'sex')
            new_record = {
                "Hb": Hb, "MCH": MCH, "MCHC": MCHC, "MCV": MCV,
                "sex": sex, "age": age,
                "prediction": prediction_result,  
            }
            
            # 3. Insertar datos en Supabase
            inserted_data = insert_data_to_supabase(new_record)
            
            if inserted_data:
                # 4. Mostrar el Resultado de la Predicción al usuario
                st.success("✅ ¡Datos guardados en Supabase con éxito!")

                st.markdown("### Resultado de la Predicción:")
                # Aseguramos que la comparación sea en minúsculas
                if prediction_result.lower() == "anemia":
                    st.error(f"Resultado: **{prediction_result}** 🛑")
                    st.warning("Se sugiere revisión médica basada en la predicción del modelo.")
                elif prediction_result.lower() == "normal":
                    st.success(f"Resultado: **{prediction_result}** ✅")
                    st.info("El modelo predice un estado normal.")
                else: 
                    st.warning(f"Resultado: **{prediction_result}** 🟡")
                    st.info("El modelo predice un resultado no-normal o desconocido. Revisar valores.")
            else:
                st.error("❌ Fallo en la inserción de datos. Revise la configuración de Supabase.")


# --- Columna de Visualización de Datos (CARGA Y ANÁLISIS) ---
with col_data:
    st.header(f"2. Análisis de Registros Históricos")
    
    # Carga los datos de la base de datos
    df_data = get_data_from_supabase()

    if not df_data.empty:
        st.markdown(f"**Total de registros:** `{len(df_data)}`")
        
        # Crear pestañas para organizar la visualización
        tab_data, tab_stats = st.tabs(["📊 Datos y Distribución", "📈 Gráficos de Variables"])
        
        # --- Pestaña de Datos y Distribución ---
        with tab_data:
            st.subheader("Registros Históricos (Últimos 5000)")
            # Mostrar solo las columnas relevantes (incluyendo 'Time')
            display_cols = ['Time', 'age', 'sex', 'Hb', 'MCH', 'MCHC', 'MCV', 'prediction']
            df_display = df_data[[col for col in display_cols if col in df_data.columns]]
            st.dataframe(df_display, use_container_width=True)
            
            # Gráfico de Distribución (Pie Chart)
            st.subheader("Distribución de Predicciones Históricas")
            if 'prediction' in df_data.columns:
                df_cleaned = df_data.dropna(subset=['prediction'])
                counts = df_cleaned['prediction'].value_counts().reset_index()
                counts.columns = ['Resultado', 'Cantidad']
                
                # Mapeo de colores más específico
                color_map_pie = {'Anemia': '#E91E63', 'Normal': '#4CAF50'}
                
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
            
            # Variables a analizar
            hematology_cols = ['Hb', 'MCH', 'MCHC', 'MCV']
            
            # Generar Histograma y Boxplot para cada variable
            for col_name in hematology_cols:
                if col_name in df_data.columns and 'prediction' in df_data.columns:
                    st.markdown(f"#### Análisis de {col_name} por Resultado")
                    col_hist, col_box = st.columns(2)
                    
                    with col_hist:
                        fig_hist = plot_histogram(df_data, col_name, col_name)
                        st.plotly_chart(fig_hist, use_container_width=True)
                        
                    with col_box:
                        fig_box = plot_boxplot(df_data, col_name, col_name)
                        st.plotly_chart(fig_box, use_container_width=True)
                
    else:
        st.info("No hay datos históricos para mostrar aún. Usa el formulario de la izquierda para ingresar el primer registro y ver los gráficos estadísticos aquí.")
