"""
Sherpa - Google Sheets Edition

Una aplicación Streamlit para analizar y visualizar subnets de Bittensor utilizando
Google Sheets como fuente de datos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime
from PIL import Image
import io
from sheets_client import SheetsClient

# Inicialización y configuración
@st.cache_resource
def init_sheets_client():
    """
    Inicializar el cliente de Google Sheets usando secretos
    
    Returns:
        SheetsClient: Cliente para acceder a Google Sheets
    """
    try:
        # Obtener credenciales desde secretos de Streamlit
        credentials_dict = dict(st.secrets.get("google_sheets", {}).get("credentials", {}))
        spreadsheet_id = st.secrets.get("google_sheets", {}).get("spreadsheet_id", "")
        
        if not credentials_dict or not spreadsheet_id:
            # Usar fallback para pruebas - en producción, siempre se deberían usar secretos
            credentials_path = "google_credentials.json"
            
            if not os.path.exists(credentials_path):
                # No mostrar error al usuario, solo loggear
                print("ERROR: No se encontraron credenciales para Google Sheets")
                return None
                
            # Si no hay credenciales en secretos pero existe el archivo
            spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"  # ID por defecto para pruebas
        else:
            # Guardar credenciales desde secretos a un archivo temporal
            credentials_path = "temp_credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(credentials_dict, f)
        
        # Crear y devolver el cliente
        client = SheetsClient(credentials_path, spreadsheet_id)
        return client
        
    except Exception as e:
        # No mostrar error al usuario, solo loggear
        print(f"ERROR: No se pudo inicializar el cliente de Google Sheets: {str(e)}")
        return None

def get_subnets_from_sheets():
    """
    Obtener subnets desde Google Sheets
    
    Returns:
        pd.DataFrame: DataFrame con información de subnets
    """
    # Obtener datos directamente de la hoja principal
    # En lugar de usar la función de procesamiento complejo
    client = init_sheets_client()
    if not client:
        return pd.DataFrame()
    
    # Para esta versión simplificada, obtener datos directamente de la hoja principal
    df = client.get_raw_data("v2 Main Dashboard")
    
    if not df.empty:
        # Asegurar que tiene las columnas mínimas necesarias
        required_columns = ['ID', 'Name', 'Current Tier']
        if all(col in df.columns for col in required_columns):
            # Renombrar columnas para compatibilidad
            df = df.rename(columns={
                'ID': 'id',
                'Name': 'name',
                'Current Tier': 'tier',
                'Team': 'uid',
                'Notes': 'description'
            })
            
            # Añadir columnas calculadas si no existen
            if 'service_avg' not in df.columns:
                df['service_avg'] = 0.0
            if 'research_avg' not in df.columns:
                df['research_avg'] = 0.0
            if 'intelligence_avg' not in df.columns:
                df['intelligence_avg'] = 0.0
            if 'resource_avg' not in df.columns:
                df['resource_avg'] = 0.0
            if 'total_score' not in df.columns and 'CUSTOM EVAL' in df.columns:
                df['total_score'] = pd.to_numeric(df['CUSTOM EVAL'], errors='coerce')
            elif 'total_score' not in df.columns:
                df['total_score'] = 0.0
                
            # Añadir columnas de puntuaciones como diccionarios vacíos
            for col in ['service_oriented_scores', 'research_oriented_scores', 
                    'intelligence_oriented_scores', 'resource_oriented_scores',
                    'additional_criteria_scores']:
                df[col] = '{}'
            
            return df
    
    return pd.DataFrame()

def get_raw_sheet_data(sheet_name="subnets", max_rows=6, max_cols=6):
    """
    Obtener datos brutos de una hoja de Google Sheets
    
    Args:
        sheet_name (str): Nombre de la hoja
        max_rows (int): Número máximo de filas a mostrar
        max_cols (int): Número máximo de columnas a mostrar
        
    Returns:
        pd.DataFrame: DataFrame con los datos brutos limitados
    """
    client = init_sheets_client()
    if not client:
        return pd.DataFrame()
    
    return client.get_raw_data(sheet_name, max_rows, max_cols)

def get_evaluation_criteria_from_sheets():
    """
    Obtener criterios de evaluación desde Google Sheets
    
    Returns:
        dict: Diccionario con criterios de evaluación
    """
    client = init_sheets_client()
    if not client:
        return {}
    
    return client.get_criteria_definitions()

def set_page_config():
    """Configurar página de Streamlit"""
    st.set_page_config(
        page_title="Sherpa - Bittensor Subnet Evaluation",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Añadir CSS personalizado
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4a4a4a;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #4a4a4a;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .subsection-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #4a4a4a;
    }
    .tier-a {
        color: #3dc5bd;
        font-weight: bold;
    }
    .tier-b {
        color: #5884c5;
        font-weight: bold;
    }
    .tier-c {
        color: #f4be55;
        font-weight: bold;
    }
    .tier-d {
        color: #ff9f64;
        font-weight: bold;
    }
    .custom-info-box {
        background-color: #f6f6f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    /* Estilo para el selectbox activo */
    div[data-baseweb="select"] > div {
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

def navigation():
    """Crear menú de navegación lateral"""
    with st.sidebar:
        # Mostrar logo de Sherpa si existe
        logo_path = "assets/sherpa_logo.png"
        
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True)
        else:
            st.title("Sherpa")
            
        st.markdown("---")  # Separador
        
        # Menú de navegación
        st.markdown("<h3>Navegación</h3>", unsafe_allow_html=True)
        
        # Enlaces de navegación
        pages = {
            "Home": home_page,
            "Visualization": visualization_page
        }
        
        # Comprobar si hay subnets
        subnets_df = get_subnets_from_sheets()
        has_subnets = not subnets_df.empty
        
        # Control de navegación con botones
        # Obtener página actual
        current_page = st.session_state.get('page', 'Home')
        
        for page_name, page_func in pages.items():
            # Deshabilitar botones si no hay subnets disponibles
            disabled = False
            if not has_subnets and page_name in ["Visualization"]:
                disabled = True
            
            # Determinar si este es el botón activo
            is_active = current_page == page_name
            
            # Generar clase para botón activo
            button_type = "primary" if is_active else "secondary"
            
            # Crear botón de navegación
            if st.button(page_name, key=f"nav_{page_name}", type=button_type, disabled=disabled, use_container_width=True):
                st.session_state['page'] = page_name
                st.rerun()

def home_page():
    """Mostrar página de inicio"""
    st.markdown('<h1 class="main-header">Sherpa</h1>', unsafe_allow_html=True)
    
    # Añadir CSS personalizado para aumentar el tamaño de fuente en la página de inicio
    st.markdown("""
    <style>
    /* Aumentar tamaño de fuente para todo el texto en la página de inicio en un 25% */
    .home-text {
        font-size: 1.25rem;
    }
    .home-text h2 {
        font-size: 1.75rem;
    }
    .home-text li {
        font-size: 1.25rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Columna única para el contenido de introducción
    st.markdown("""
    <div class="home-text">
    Bienvenido a Sherpa, una herramienta diseñada para analizar y visualizar subnets de Bittensor 
    basada en sus características y métricas de rendimiento.
    
    Esta plataforma te ayuda a:
    <ul>
    <li>Categorizar subnets en un espectro de Servicio-Investigación e Inteligencia-Recursos</li>
    <li>Puntuar subnets basadas en múltiples criterios ponderados</li>
    <li>Visualizar posicionamiento y relaciones entre subnets</li>
    <li>Comparar rendimiento y capacidades de diferentes subnets</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar datos básicos (6 filas, 6 columnas)
    st.markdown("<h2>Vista previa de datos</h2>", unsafe_allow_html=True)
    st.markdown("Esta es una muestra de los primeros datos disponibles en la hoja principal:")
    
    # Obtener datos brutos limitados a 6 filas y 6 columnas
    raw_data = get_raw_sheet_data("v2 Main Dashboard", 6, 6)
    
    if not raw_data.empty:
        st.dataframe(raw_data, use_container_width=True)
    else:
        st.info("No hay datos disponibles para mostrar.")
    
    st.markdown("""
    <div class="home-text">
    <h2>Conceptos Clave</h2>
    
    <p>La aplicación visualiza:</p>
    <ul>
    <li><strong>Cuadrantes</strong> - Mapas visuales que posicionan las subnets según sus orientaciones principales</li>
    <li><strong>Puntuaciones</strong> - Análisis detallado de cómo se evalúa cada subnet según diversos criterios</li>
    <li><strong>Comparativas</strong> - Herramientas para comparar diferentes subnets entre sí</li>
    </ul>
    
    <h2>Comenzando</h2>
    
    <p>Para comenzar a utilizar Sherpa:</p>
    <ol>
    <li>Navega a la página de Visualización utilizando el menú lateral</li>
    <li>Explora los diferentes cuadrantes y gráficos disponibles</li>
    <li>Selecciona las subnets específicas que deseas analizar</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

def visualization_page():
    """Página para visualizar datos de subnet desde Google Sheets"""
    st.markdown('<h1 class="main-header">Visualización de Subnets</h1>', unsafe_allow_html=True)
    
    # Obtener datos de subnets
    subnets_df = get_subnets_from_sheets()
    
    if subnets_df.empty:
        st.warning("No se encontraron datos para visualizar. Por favor, contacta al administrador del sistema.")
        return
    
    # Procesar DataFrame - convertir columnas JSON a diccionarios
    for col in ['service_oriented_scores', 'research_oriented_scores', 
              'intelligence_oriented_scores', 'resource_oriented_scores',
              'additional_criteria_scores']:
        try:
            subnets_df[col] = subnets_df[col].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
        except Exception as e:
            # Loggear el error sin mostrarlo al usuario
            print(f"Error al procesar columna {col}: {str(e)}")
    
    # Verificar si hay datos para visualizar
    if len(subnets_df) == 0:
        st.warning("No hay datos disponibles para visualizar. Por favor, contacta al administrador del sistema.")
        return
    
    # Inicializar estado de sesión para selección de subnets si no existe
    if 'selected_subnets' not in st.session_state:
        st.session_state['selected_subnets'] = {row['name']: True for _, row in subnets_df.iterrows()}
    
    # Selección de subnets a mostrar
    st.markdown('<h3>Seleccionar Subnets para Visualizar</h3>', unsafe_allow_html=True)
    
    # Crear visualización principal con pestañas
    tabs = st.tabs([
        "Cuadrante Service-Research", 
        "Cuadrante Intelligence-Resource", 
        "Puntuaciones", 
        "Análisis Detallado",
        "Comparación",
        "Matriz de Puntuaciones"
    ])
    
    # Filtrar dataframe según las subnets seleccionadas
    col1, col2, col3 = st.columns(3)
    subnet_names = subnets_df['name'].tolist()
    selected_names = []
    
    # Dividir subnets en 3 columnas para checkbox
    column_size = len(subnet_names) // 3 + (1 if len(subnet_names) % 3 > 0 else 0)
    
    with col1:
        for name in subnet_names[:column_size]:
            if name in st.session_state['selected_subnets']:
                selected = st.checkbox(name, value=st.session_state['selected_subnets'][name], key=f"subnet_{name}_1")
                st.session_state['selected_subnets'][name] = selected
                if selected:
                    selected_names.append(name)
    
    with col2:
        for name in subnet_names[column_size:2*column_size]:
            if name in st.session_state['selected_subnets']:
                selected = st.checkbox(name, value=st.session_state['selected_subnets'][name], key=f"subnet_{name}_2")
                st.session_state['selected_subnets'][name] = selected
                if selected:
                    selected_names.append(name)
    
    with col3:
        for name in subnet_names[2*column_size:]:
            if name in st.session_state['selected_subnets']:
                selected = st.checkbox(name, value=st.session_state['selected_subnets'][name], key=f"subnet_{name}_3")
                st.session_state['selected_subnets'][name] = selected
                if selected:
                    selected_names.append(name)
    
    # Filtrar DataFrame
    filtered_df = subnets_df[subnets_df['name'].isin(selected_names)]
    
    if filtered_df.empty:
        st.warning("Por favor, selecciona al menos una subnet para visualizar.")
        return
    
    # Cuadrante Service-Research
    with tabs[0]:
        st.markdown('<h2 class="section-header">Cuadrante Service-Research</h2>', unsafe_allow_html=True)
        fig = create_quadrant_chart(filtered_df, "service_research")
        st.plotly_chart(fig, use_container_width=True)
    
    # Cuadrante Intelligence-Resource
    with tabs[1]:
        st.markdown('<h2 class="section-header">Cuadrante Intelligence-Resource</h2>', unsafe_allow_html=True)
        fig = create_quadrant_chart(filtered_df, "intelligence_resource")
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de puntuaciones
    with tabs[2]:
        st.markdown('<h2 class="section-header">Puntuaciones de Subnets</h2>', unsafe_allow_html=True)
        
        # Crear una tabla de puntuaciones
        fig = create_score_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla de puntuaciones
        st.markdown('<h3 class="subsection-header">Tabla de Puntuaciones</h3>', unsafe_allow_html=True)
        
        # Crear DataFrame para la tabla
        table_df = filtered_df[['name', 'service_avg', 'research_avg', 'intelligence_avg', 'resource_avg', 'total_score', 'tier']]
        table_df = table_df.sort_values(by='total_score', ascending=False)
        
        # Renombrar columnas para mejor presentación
        table_df = table_df.rename(columns={
            'name': 'Subnet',
            'service_avg': 'Servicio',
            'research_avg': 'Investigación',
            'intelligence_avg': 'Inteligencia',
            'resource_avg': 'Recursos',
            'total_score': 'Puntuación Total',
            'tier': 'Tier'
        })
        
        # Función para resaltar el tier
        def highlight_tier(val):
            if val == "Tier A":
                return 'background-color: rgba(61, 197, 189, 0.2); color: #3dc5bd; font-weight: bold'
            elif val == "Tier B":
                return 'background-color: rgba(88, 132, 197, 0.2); color: #5884c5; font-weight: bold'
            elif val == "Tier C":
                return 'background-color: rgba(244, 190, 85, 0.2); color: #f4be55; font-weight: bold'
            elif val == "Tier D":
                return 'background-color: rgba(255, 159, 100, 0.2); color: #ff9f64; font-weight: bold'
            return ''
        
        # Aplicar estilo y mostrar tabla
        styled_table = table_df.style.map(highlight_tier, subset=['Tier'])
        st.dataframe(styled_table, use_container_width=True)
    
    # Análisis Detallado
    with tabs[3]:
        st.markdown('<h2 class="section-header">Análisis Detallado de Subnet</h2>', unsafe_allow_html=True)
        
        # Selector de subnet
        selected_subnet = st.selectbox(
            "Seleccionar Subnet para Análisis",
            filtered_df['name'].tolist(),
            key="detailed_analysis_subnet"
        )
        
        # Obtener datos de la subnet seleccionada
        subnet_data = filtered_df[filtered_df['name'] == selected_subnet].iloc[0]
        
        # Crear columnas para info de subnet y puntuaciones
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<h3 class="subsection-header">Información de Subnet</h3>', unsafe_allow_html=True)
            
            # Formatear tier con clase apropiada
            tier_class = subnet_data['tier'].lower().replace(' ', '-')
            
            st.markdown(f"""
            <div class="custom-info-box">
                <p><strong>Nombre:</strong> {subnet_data['name']}</p>
                <p><strong>UID:</strong> {subnet_data['uid']}</p>
                <p><strong>Tier:</strong> <span class="{tier_class}">{subnet_data['tier']}</span></p>
                <p><strong>Puntuación Total:</strong> {subnet_data['total_score']:.1f}</p>
                <p><strong>Descripción:</strong> {subnet_data['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown('<h3 class="subsection-header">Desglose de Puntuaciones</h3>', unsafe_allow_html=True)
            
            # Crear gráfico de radar
            fig = create_radar_chart(subnet_data)
            st.plotly_chart(fig, use_container_width=True)
        
        # Crear pestañas para puntuaciones detalladas por criterio
        criteria_tabs = st.tabs(["Servicio", "Investigación", "Inteligencia", "Recursos", "Adicionales"])
        
        # Servicio
        with criteria_tabs[0]:
            create_criteria_scores_table(subnet_data, 'service_oriented_scores', "Criterios de Servicio")
        
        # Investigación
        with criteria_tabs[1]:
            create_criteria_scores_table(subnet_data, 'research_oriented_scores', "Criterios de Investigación")
        
        # Inteligencia
        with criteria_tabs[2]:
            create_criteria_scores_table(subnet_data, 'intelligence_oriented_scores', "Criterios de Inteligencia")
        
        # Recursos
        with criteria_tabs[3]:
            create_criteria_scores_table(subnet_data, 'resource_oriented_scores', "Criterios de Recursos")
        
        # Adicionales
        with criteria_tabs[4]:
            if isinstance(subnet_data['additional_criteria_scores'], dict) and 'scores' in subnet_data['additional_criteria_scores']:
                scores = subnet_data['additional_criteria_scores']['scores']
                weights = subnet_data['additional_criteria_scores'].get('weights', {})
                create_additional_criteria_scores_table(scores, weights, "Criterios de Evaluación Adicionales")
            else:
                st.info("No hay puntuaciones de criterios adicionales disponibles.")
    
    # Comparación
    with tabs[4]:
        st.markdown('<h2 class="section-header">Comparación de Subnets</h2>', unsafe_allow_html=True)
        
        # Multi-select para subnets a comparar
        selected_subnets = st.multiselect(
            "Seleccionar Subnets para Comparar",
            filtered_df['name'].tolist(),
            default=filtered_df['name'].tolist()[:2] if len(filtered_df) >= 2 else filtered_df['name'].tolist(),
            key="comparison_subnets"
        )
        
        if len(selected_subnets) < 2:
            st.warning("Por favor, selecciona al menos 2 subnets para comparar.")
            return
        
        # Filtrar dataframe para subnets seleccionadas
        compare_df = filtered_df[filtered_df['name'].isin(selected_subnets)]
        
        # Crear gráfico de comparación
        fig = create_comparison_chart(compare_df)
        st.plotly_chart(fig, use_container_width=True)
    
    # Matriz de Puntuaciones
    with tabs[5]:
        st.markdown('<h2 class="section-header">Matriz de Puntuaciones</h2>', unsafe_allow_html=True)
        
        # Obtener categorías de criterios
        criteria = get_evaluation_criteria_from_sheets()
        
        # Radio buttons para selección de categoría
        category_options = ["Servicio", "Investigación", "Inteligencia", "Recursos", "Adicionales"]
        selected_category = st.radio("Seleccionar Categoría", category_options, horizontal=True)
        
        # Convertir a clave para diccionario
        category_map = {
            "Servicio": "service",
            "Investigación": "research",
            "Inteligencia": "intelligence",
            "Recursos": "resource",
            "Adicionales": "additional"
        }
        
        category_key = category_map[selected_category]
        scores_key = f"{category_key}_oriented_scores"
        
        # Crear matriz para la categoría seleccionada
        st.markdown(f"<h3 class='subsection-header'>Puntuaciones de Criterios de {selected_category}</h3>", unsafe_allow_html=True)
        
        # Convertir puntuaciones a matriz
        matrix_data = {}
        
        # Primero, obtener todas las claves de criterios usadas
        all_criteria_keys = set()
        
        for _, row in filtered_df.iterrows():
            if scores_key in row and isinstance(row[scores_key], dict):
                for key in row[scores_key].keys():
                    all_criteria_keys.add(key)
        
        # Obtener definiciones de criterios para esta categoría
        criteria_defs = criteria.get(category_key, {})
        
        # Primera columna - nombres de criterios
        matrix_data["Criterio"] = []
        for key in all_criteria_keys:
            if key in criteria_defs and isinstance(criteria_defs[key], dict) and "question" in criteria_defs[key]:
                matrix_data["Criterio"].append(criteria_defs[key]["question"])
            else:
                matrix_data["Criterio"].append(key)
        
        # Añadir columna para cada subnet
        for _, row in filtered_df.iterrows():
            subnet_name = row['name']
            scores = row[scores_key] if scores_key in row and isinstance(row[scores_key], dict) else {}
            
            matrix_data[subnet_name] = []
            for key in all_criteria_keys:
                matrix_data[subnet_name].append(scores.get(key, "N/A"))
        
        # Convertir a DataFrame
        matrix_df = pd.DataFrame(matrix_data)
        
        # Función de color para puntuaciones
        def color_score(val):
            if isinstance(val, (int, float)):
                # Determinar color basado en puntuación (escala 0-10)
                if val >= 7.5:
                    return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
                elif val >= 5:
                    return 'background-color: rgba(200, 200, 0, 0.2); color: #7a7a00'
                elif val >= 2.5:
                    return 'background-color: rgba(255, 165, 0, 0.2); color: #cc5500'
                else:
                    return 'background-color: rgba(255, 0, 0, 0.2); color: #8b0000'
            return ''
        
        # Aplicar estilo a todas las columnas excepto la primera (nombres de criterios)
        styled_matrix = matrix_df.style.map(color_score, subset=[col for col in matrix_df.columns if col != "Criterio"])
        
        # Mostrar matriz estilizada
        st.dataframe(styled_matrix, use_container_width=True)

def create_criteria_scores_table(subnet_data, scores_field, title):
    """Crear tabla de puntuaciones de criterios"""
    st.markdown(f"<h3 class='subsection-header'>{title}</h3>", unsafe_allow_html=True)
    
    scores = subnet_data.get(scores_field, {})
    
    if not scores or len(scores) == 0:
        st.info(f"No hay puntuaciones disponibles para {title.lower()}")
        return
    
    # Obtener definiciones de criterios desde Google Sheets
    criteria = get_evaluation_criteria_from_sheets()
    category = scores_field.split('_')[0]  # Extraer categoría (service, research, etc.)
    
    # Crear DataFrame para la tabla
    data = []
    
    for key, score in scores.items():
        # Intentar obtener nombre y descripción del criterio
        criterion_name = key
        criterion_desc = ""
        
        if category in criteria and key in criteria[category]:
            criterion_info = criteria[category][key]
            if isinstance(criterion_info, dict):
                criterion_name = criterion_info.get("question", key)
                criterion_desc = criterion_info.get("description", "")
        
        data.append({
            "Criterio": criterion_name,
            "Descripción": criterion_desc,
            "Puntuación": float(score) if isinstance(score, (int, float)) else 0
        })
    
    # Convertir a DataFrame y ordenar por puntuación
    df = pd.DataFrame(data)
    df = df.sort_values(by="Puntuación", ascending=False)
    
    # Función para colorear puntuaciones
    def color_score(val):
        if val >= 7.5:
            return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
        elif val >= 5:
            return 'background-color: rgba(200, 200, 0, 0.2); color: #7a7a00'
        elif val >= 2.5:
            return 'background-color: rgba(255, 165, 0, 0.2); color: #cc5500'
        else:
            return 'background-color: rgba(255, 0, 0, 0.2); color: #8b0000'
    
    # Aplicar estilo
    styled_df = df.style.map(color_score, subset=['Puntuación'])
    
    # Mostrar tabla
    st.dataframe(styled_df, use_container_width=True)

def create_additional_criteria_scores_table(scores, weights, title):
    """Crear tabla de puntuaciones para criterios adicionales"""
    st.markdown(f"<h3 class='subsection-header'>{title}</h3>", unsafe_allow_html=True)
    
    if not scores or len(scores) == 0:
        st.info(f"No hay puntuaciones adicionales disponibles")
        return
    
    # Obtener definiciones de criterios desde Google Sheets
    criteria = get_evaluation_criteria_from_sheets()
    
    # Crear DataFrame para la tabla
    data = []
    
    for key, score in scores.items():
        # Obtener peso
        weight = weights.get(key, 1.0)
        
        # Intentar obtener información del criterio
        criterion_name = key
        criterion_desc = ""
        criterion_type = "positive"
        
        if 'additional' in criteria and key in criteria['additional']:
            criterion_info = criteria['additional'][key]
            if isinstance(criterion_info, dict):
                criterion_name = criterion_info.get("question", key)
                criterion_desc = criterion_info.get("description", "")
                criterion_type = criterion_info.get("type", "positive")
        
        data.append({
            "Criterio": criterion_name,
            "Descripción": criterion_desc,
            "Tipo": criterion_type.capitalize(),
            "Peso": float(weight),
            "Puntuación": float(score) if isinstance(score, (int, float)) else 0
        })
    
    # Convertir a DataFrame y ordenar por puntuación
    df = pd.DataFrame(data)
    df = df.sort_values(by="Puntuación", ascending=False)
    
    # Función para colorear puntuaciones
    def color_score(val):
        if val >= 7.5:
            return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
        elif val >= 5:
            return 'background-color: rgba(200, 200, 0, 0.2); color: #7a7a00'
        elif val >= 2.5:
            return 'background-color: rgba(255, 165, 0, 0.2); color: #cc5500'
        else:
            return 'background-color: rgba(255, 0, 0, 0.2); color: #8b0000'
    
    # Función para colorear impacto (peso)
    def color_impact(val):
        if val >= 0.7:
            return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
        elif val >= 0.4:
            return 'background-color: rgba(200, 200, 0, 0.2); color: #7a7a00'
        else:
            return 'background-color: rgba(200, 200, 200, 0.2); color: #444444'
    
    # Función para colorear tipo
    def color_type(val):
        if val == "Positive":
            return 'background-color: rgba(0, 200, 0, 0.2); color: #006400'
        elif val == "Negative":
            return 'background-color: rgba(255, 0, 0, 0.2); color: #8b0000'
        else:  # Bidirectional
            return 'background-color: rgba(0, 150, 200, 0.2); color: #006080'
    
    # Aplicar estilo
    styled_df = df.style.map(color_score, subset=['Puntuación']) \
                        .map(color_impact, subset=['Peso']) \
                        .map(color_type, subset=['Tipo'])
    
    # Mostrar tabla
    st.dataframe(styled_df, use_container_width=True)

# Funciones de visualización
def create_quadrant_chart(df, chart_type):
    """Crear gráfico de cuadrantes"""
    # Configurar datos del gráfico según el tipo
    if chart_type == "service_research":
        x_title = "Orientación a Investigación"
        y_title = "Orientación a Servicio"
        
        # Transformar valores a escala -10 a 10 para el gráfico
        x_values = [(2 * df['research_avg'] - 10).tolist()]
        y_values = [(2 * df['service_avg'] - 10).tolist()]
        
        quadrant_labels = ["Enfocado en Investigación", "Espectro Completo", "Balanceado", "Enfocado en Servicio"]
    else:  # intelligence_resource
        x_title = "Orientación a Recursos"
        y_title = "Orientación a Inteligencia"
        
        # Transformar valores a escala -10 a 10 para el gráfico
        x_values = [(2 * df['resource_avg'] - 10).tolist()]
        y_values = [(2 * df['intelligence_avg'] - 10).tolist()]
        
        quadrant_labels = ["Enfocado en Recursos", "Espectro Completo", "Balanceado", "Enfocado en Inteligencia"]
    
    # Preparar datos para scatter plot
    names = df['name'].tolist()
    tiers = df['tier'].tolist()
    
    # Mapeado de colores para tiers
    color_map = {
        "Tier A": "#3dc5bd",
        "Tier B": "#5884c5",
        "Tier C": "#f4be55", 
        "Tier D": "#ff9f64"
    }
    
    colors = [color_map.get(tier, "#aaaaaa") for tier in tiers]
    
    # Configurar texto hover
    hover_texts = []
    for i, row in df.iterrows():
        hover_text = f"<b>{row['name']}</b><br>"
        hover_text += f"UID: {row['uid']}<br>"
        hover_text += f"Tier: {row['tier']}<br>"
        hover_text += f"Puntuación Total: {row['total_score']:.1f}<br>"
        
        if chart_type == "service_research":
            hover_text += f"Servicio: {row['service_avg']:.1f}<br>"
            hover_text += f"Investigación: {row['research_avg']:.1f}<br>"
        else:
            hover_text += f"Inteligencia: {row['intelligence_avg']:.1f}<br>"
            hover_text += f"Recursos: {row['resource_avg']:.1f}<br>"
        
        hover_text += f"Descripción: {row['description']}"
        hover_texts.append(hover_text)
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir scatter plot
    fig.add_trace(go.Scatter(
        x=x_values[0],
        y=y_values[0],
        mode='markers+text',
        text=names,
        textposition='top center',
        marker=dict(
            size=14,
            color=colors,
            line=dict(width=2, color='white')
        ),
        hoverinfo='text',
        hovertext=hover_texts,
        textfont=dict(
            family="Arial",
            size=11,
        )
    ))
    
    # Añadir líneas de cuadrantes
    fig.add_shape(
        type="line",
        x0=-10, y0=0,
        x1=10, y1=0,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    fig.add_shape(
        type="line",
        x0=0, y0=-10,
        x1=0, y1=10,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    # Añadir etiquetas de cuadrantes
    fig.add_annotation(x=5, y=5, text=quadrant_labels[1], showarrow=False, font=dict(size=12))
    fig.add_annotation(x=-5, y=5, text=quadrant_labels[0], showarrow=False, font=dict(size=12))
    fig.add_annotation(x=-5, y=-5, text=quadrant_labels[2], showarrow=False, font=dict(size=12))
    fig.add_annotation(x=5, y=-5, text=quadrant_labels[3], showarrow=False, font=dict(size=12))
    
    # Actualizar layout
    fig.update_layout(
        title=f"{y_title} vs {x_title}",
        xaxis=dict(
            title=x_title,
            range=[-11, 11],
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='black',
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title=y_title,
            range=[-11, 11],
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='black',
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        height=600,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode='closest'
    )
    
    return fig

def create_score_chart(df):
    """Crear gráfico de barras de puntuaciones de subnets"""
    # Ordenar por puntuación total
    sorted_df = df.sort_values(by='total_score', ascending=False).copy()
    
    # Obtener colores por tier
    tier_colors = {
        "Tier A": "#3dc5bd",
        "Tier B": "#5884c5",
        "Tier C": "#f4be55",
        "Tier D": "#ff9f64"
    }
    
    # Crear lista de colores basados en tiers
    colors = [tier_colors.get(tier, "#aaaaaa") for tier in sorted_df['tier']]
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir barras
    fig.add_trace(go.Bar(
        x=sorted_df['name'],
        y=sorted_df['total_score'],
        marker_color=colors,
        text=[f"{score:.1f}" for score in sorted_df['total_score']],
        textposition='auto',
        hovertemplate="<b>%{x}</b><br>" +
                      "Puntuación Total: %{y:.1f}<br>" +
                      "Tier: %{customdata}<extra></extra>",
        customdata=sorted_df['tier']
    ))
    
    # Añadir regiones de tier
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=8.5, y1=10,
        fillcolor="rgba(61, 197, 189, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=7, y1=8.5,
        fillcolor="rgba(88, 132, 197, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=5.5, y1=7,
        fillcolor="rgba(244, 190, 85, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, x1=len(sorted_df)-0.5, y0=0, y1=5.5,
        fillcolor="rgba(255, 159, 100, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    
    # Añadir etiquetas de tier
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=9.25,
        text="Tier A",
        showarrow=False,
        font=dict(color="#3dc5bd", size=14),
        align="right",
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=7.75,
        text="Tier B",
        showarrow=False,
        font=dict(color="#5884c5", size=14),
        align="right",
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=6.25,
        text="Tier C",
        showarrow=False,
        font=dict(color="#f4be55", size=14),
        align="right",
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(sorted_df)-1,
        y=2.75,
        text="Tier D",
        showarrow=False,
        font=dict(color="#ff9f64", size=14),
        align="right",
        xanchor="right"
    )
    
    # Actualizar layout
    fig.update_layout(
        title="Puntuaciones Totales por Subnet",
        xaxis=dict(
            title="Subnet",
            tickangle=-45,
        ),
        yaxis=dict(
            title="Puntuación Total",
            range=[0, 10],
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        margin=dict(l=40, r=40, t=60, b=80),
    )
    
    return fig

def create_radar_chart(subnet_data):
    """Crear gráfico de radar para una subnet"""
    # Obtener promedios por categoría
    service_avg = subnet_data['service_avg']
    research_avg = subnet_data['research_avg']
    intelligence_avg = subnet_data['intelligence_avg']
    resource_avg = subnet_data['resource_avg']
    
    # Datos para el gráfico de radar
    categories = ['Servicio', 'Investigación', 'Inteligencia', 'Recursos']
    values = [service_avg, research_avg, intelligence_avg, resource_avg]
    
    # Cerrar el polígono repitiendo el primer valor
    categories = categories + [categories[0]]
    values = values + [values[0]]
    
    # Crear figura
    fig = go.Figure()
    
    # Añadir polígono de radar
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(61, 197, 189, 0.2)',
        line=dict(color='#3dc5bd', width=2),
        name=subnet_data['name']
    ))
    
    # Actualizar layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False
    )
    
    return fig

def create_comparison_chart(df):
    """Crear gráfico de radar comparando múltiples subnets"""
    # Definir categorías
    categories = ['Servicio', 'Investigación', 'Inteligencia', 'Recursos']
    
    # Crear figura
    fig = go.Figure()
    
    # Mapeado de colores para tiers
    tier_colors = {
        "Tier A": "#3dc5bd",
        "Tier B": "#5884c5",
        "Tier C": "#f4be55",
        "Tier D": "#ff9f64"
    }
    
    # Añadir una traza por cada subnet
    for i, row in df.iterrows():
        # Obtener valores
        values = [
            row['service_avg'],
            row['research_avg'],
            row['intelligence_avg'],
            row['resource_avg']
        ]
        
        # Cerrar el polígono
        categories_plot = categories + [categories[0]]
        values = values + [values[0]]
        
        # Obtener color según tier
        color = tier_colors.get(row['tier'], "#aaaaaa")
        
        # Añadir traza
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories_plot,
            fill='toself',
            fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)}",
            line=dict(color=color, width=2),
            name=row['name']
        ))
    
    # Actualizar layout
    fig.update_layout(
        title="Comparación de Subnets",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

def main():
    """Punto de entrada principal de la aplicación"""
    try:
        # Configurar página
        set_page_config()
        
        # Ejecutar navegación
        navigation()
        
        # Mostrar página actual
        current_page = st.session_state.get('page', 'Home')
        
        if current_page == 'Home':
            home_page()
        elif current_page == 'Visualization':
            visualization_page()
        else:
            home_page()
            
    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
        # UI básica en caso de error
        st.markdown("## Sherpa - Herramienta de Evaluación de Subnets Bittensor")
        st.markdown("Hubo un error al cargar la aplicación. Por favor, intenta refrescar la página.")

if __name__ == "__main__":
    main()