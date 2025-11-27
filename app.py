def insertar_datos_minimos(datos):
    """Inserta solo las columnas que SEGURO existen"""
    try:
        if not supabase:
            return None
            
        # SOLO columnas que sabemos que existen
        datos_minimos = {
            'dni': datos.get('dni', ''),
            'nombre': datos.get('nombre_completo', ''),
            'hemoglobina': datos.get('hemoglobina_g_dL', 0.0),
            'riesgo': datos.get('nivel_riesgo', ''),
            'fecha_alerta': datos.get('fecha_alerta', datetime.now().isoformat()),
            'estado': datos.get('estado_recomendado', ''),
            'sugerencias': datos.get('sugerencias_texto', ''),
            'region': datos.get('region', 'NO ESPECIFICADO')
        }
        # ¡NO INCLUIR 'edad'!
        
        st.info(f"🔧 Insertando en {len(datos_minimos)} columnas: {list(datos_minimos.keys())}")
        
        response = supabase.table(TABLE_NAME).insert(datos_minimos).execute()
        
        if hasattr(response, 'error') and response.error:
            st.error(f"Error: {response.error}")
            return None
            
        return response.data[0] if response.data else None
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None
