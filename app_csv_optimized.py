"""Sherpa - CSV Edition (Optimized)

Una aplicación Streamlit para analizar y visualizar subnets de Bittensor utilizando
un archivo CSV local como fuente de datos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os

# Ruta al archivo CSV de datos - Ahora en directorio protegido
CSV_PATH = os.path.join("instance", "subnets.csv")

def load_subnets_from_csv(csv_path=CSV_PATH):
    """
    Cargar datos de subnets desde un archivo CSV local
    
    Args:
        csv_path (str): Ruta al archivo CSV
        
    Returns:
        pd.DataFrame: DataFrame con información de subnets
    """
    try:
        # Intentar leer con el formato esperado (separador ';' y decimal ',')
        df = pd.read_csv(csv_path, sep=';', decimal=',')
        return df
    except Exception as e:
        st.error(f"Error al cargar datos desde CSV: {str(e)}")
        return pd.DataFrame()

def set_page_config():
    """Configurar página de Streamlit"""
    st.set_page_config(
        page_title="Sherpa - Bittensor Subnet Evaluation",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # Ocultar el menú de Streamlit y elementos de depuración
    hide_elements = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    </style>
    """
    st.markdown(hide_elements, unsafe_allow_html=True)
    
    # Añadir CSS personalizado con optimizaciones para móviles
    st.markdown("""
    <style>
    /* CSS para detección de dispositivos */
    html, body, [data-testid="stAppViewContainer"] {
        max-width: 100vw;
        overflow-x: hidden;
    }
    
    /* Variables CSS */
    :root {
        --main-color: #FF4B4B;
        --secondary-color: #7E2553;
        --tertiary-color: #41a358;
        --text-color: #4a4a4a;
        --background-dark: rgba(0, 0, 0, 0.9);
    }
    
    /* Estilos principales adaptables */
    .main-header {
        font-size: calc(2rem + 1.5vw);
        font-weight: 700;
        color: var(--main-color);
    }
    
    .section-header {
        font-size: calc(1.2rem + 0.6vw);
        font-weight: 600;
        color: var(--text-color);
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    .subsection-header {
        font-size: calc(1rem + 0.3vw);
        font-weight: 600;
        color: var(--text-color);
    }
    
    /* Clases de tier eliminadas ya que no se utilizan */
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
    
    /* Fondo oscuro para Plotly */
    .js-plotly-plot, .plotly, .plot-container {
        background-color: var(--background-dark) !important;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        max-width: 100% !important;
        overflow-x: auto !important;
    }
    
    /* Ocultar el panel de inspección de Plotly */
    .js-plotly-plot .plotly .modebar-container,
    .js-plotly-plot .plotly .modebar,
    .js-plotly-plot .plotly [data-title],
    .plotly-notifier {
        display: none !important;
    }
    
    /* Ocultar panel lateral de desarrollo */
    .stDev, .stDebugger, div[data-testid="stDebugger"] {
        display: none !important;
    }
    
    /* Texto responsivo en la página de inicio */
    .home-text {
        font-size: calc(1rem + 0.45vw);
    }
    
    .home-text h2 {
        font-size: calc(1.3rem + 0.65vw);
    }
    
    .home-text li {
        font-size: calc(1rem + 0.45vw);
        margin-bottom: 0.5rem;
    }
    
    /* Estilos personalizados para botones */
    button[kind="primary"][data-testid="baseButton-primary"]:nth-of-type(1) {
        background-color: var(--main-color) !important;
        border-color: var(--main-color) !important;
    }
    
    button[kind="primary"][data-testid="baseButton-primary"]:nth-of-type(2) {
        background-color: var(--secondary-color) !important;
        border-color: var(--secondary-color) !important;
    }
    
    button[kind="primary"][data-testid="baseButton-primary"]:nth-of-type(3) {
        background-color: var(--tertiary-color) !important;
        border-color: var(--tertiary-color) !important;
    }
    
    /* Mejoras para móviles */
    @media (max-width: 768px) {
        /* Ajustar sidebar en mobile */
        [data-testid="stSidebar"] {
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Ajustar contenido principal */
        .stApp {
            overflow-x: hidden;
        }
        
        /* Ajustar tamaño del gráfico en móviles */
        .js-plotly-plot {
            height: 80vh !important;
            max-height: 500px !important;
        }
        
        /* Hacer que las imágenes sean responsivas */
        img {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* Ajustes para la tabla de datos en móviles */
        .stDataFrame {
            overflow-x: auto !important;
        }
        
        /* Reducir padding en móviles */
        .stApp [data-testid="stVerticalBlock"] {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        /* Ajustar controles de selección en móviles */
        .big-checkbox label {
            font-size: 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def navigation():
    """Create lateral navigation menu"""
    with st.sidebar:
        # Display Sherpa logo if it exists
        logo_path = "assets/sherpa_logo.png"
        
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True)
        else:
            st.markdown("<h1 style='font-size: 2.8rem; font-weight: bold; color: #FF4B4B;'>Sherpa</h1>", unsafe_allow_html=True)
            
        st.markdown("---")  # Separator
        
        # Navigation menu
        st.markdown("<h3>Navigation</h3>", unsafe_allow_html=True)
        
        # Navigation control with buttons
        if 'page' not in st.session_state:
            st.session_state['page'] = 'home'
        
        # Check if there are subnets
        subnets_df = load_subnets_from_csv()
        has_subnets = not subnets_df.empty
        
        # Home button
        if st.button("Home", key="nav_home", 
                    type="primary" if st.session_state['page'] == 'home' else "secondary",
                    use_container_width=True):
            st.session_state['page'] = 'home'
            st.rerun()
        
        # Visualization button
        vis_disabled = not has_subnets
        if st.button("Visualization", key="nav_vis", 
                    type="primary" if st.session_state['page'] == 'visualization' else "secondary",
                    disabled=vis_disabled,
                    use_container_width=True):
            st.session_state['page'] = 'visualization'
            st.rerun()
            
        # Sherpa's Framework button
        if st.button("Sherpa's Framework", key="nav_framework", 
                    type="primary" if st.session_state['page'] == 'framework' else "secondary",
                    use_container_width=True):
            st.session_state['page'] = 'framework'
            st.rerun()
        
        # Add spacer to push the logo to the bottom
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        
        # Add 'pushin'τ by' text and Synergy logo at the bottom
        st.markdown("<div style='margin-top: 50px; text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.1rem; margin-bottom: 5px; color: white; font-weight: 500;'>pushin'τ by</p>", unsafe_allow_html=True)
        synergy_logo = "assets/synergy-logo.png"
        if os.path.exists(synergy_logo):
            st.image(synergy_logo, width=150)
        st.markdown("</div>", unsafe_allow_html=True)

def home_page():
    """Display home page"""
    st.markdown('<h1 class="main-header" style="color: #FF4B4B;">Sherpa</h1>', unsafe_allow_html=True)
    
    # Single column for introduction content
    st.markdown("""
    <div class="home-text">
    Welcome to Sherpa, a personal framework designed to help analyze and categorize Bittensor subnets 
    to guide your investment research and decision-making process.
    
    <p>Sherpa aims to provide an initial framework for understanding subnet characteristics and potential, 
    offering a starting point for where to begin investing or researching. This is a personal approach that anyone 
    is free to copy, improve, and share.</p>
    
    This framework helps you:
    <ul>
    <li>Categorize subnets in the Service-Research and Intelligence-Resource spectrum for easier comparison</li>
    <li>Visualize subnet positioning to identify investment opportunities aligned with your strategy</li>
    <li>Compare potential strengths and weaknesses across different subnets</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Display Key Concepts first
    st.markdown("""
    <div class="home-text">
    <h2>Key Concepts</h2>
    
    <p>The Ecosystem Mapping chart shows:</p>
    <ul>
    <li><strong>X-Axis</strong> - The spectrum from Service (left) to Research (right)</li>
    <li><strong>Y-Axis</strong> - The spectrum from Resource (bottom) to Intelligence (top)</li>
    <li><strong>Bubble Size</strong> - Proportional to the evaluation score. Note: always subjective and based in public information at the time of evaluation for each subnet</li>
    <li><strong>Color</strong> - Indicates relative quality (from red to green)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Se eliminó la sección de Data Preview para simplificar la interfaz
    
    # Getting Started section
    st.markdown("""
    <div class="home-text">
    <h2>Getting Started</h2>
    
    <p>To start using Sherpa:</p>
    <ol>
    <li>Navigate to the Visualization page using the sidebar menu</li>
    <li>Read how Sherpa's framework works</li>
    <li>Explore the subnet map</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

def create_subnet_plot(subnet_data):
    """
    Crear gráfico de cuadrante similar al mostrado en el script Python proporcionado
    
    Args:
        subnet_data (pd.DataFrame): DataFrame con datos de subnets
        
    Returns:
        plotly.graph_objects.Figure: Figura de Plotly
    """
    # Preparar datos
    fig = go.Figure()
    
    # Calcular tamaño y color basados en custom-eval
    # Aumentar el tamaño de las burbujas para que sean más visibles en el gráfico más grande
    sizes = subnet_data['custom-eval'] * 18
    norm_values = (subnet_data['custom-eval'] - subnet_data['custom-eval'].min()) / \
                  (subnet_data['custom-eval'].max() - subnet_data['custom-eval'].min()) \
                  if subnet_data['custom-eval'].max() != subnet_data['custom-eval'].min() else 0.5
    
    # Mapear norm_values a colores (de rojo a verde)
    bubble_colors = []
    # Comprobar si norm_values es un escalar o una serie
    if isinstance(norm_values, float):
        # Si es un escalar, crear un solo color (rojo a verde)
        val = norm_values
        r = max(0, min(255, int(255 * (1 - val))))
        g = max(0, min(255, int(255 * val)))
        b = 0
        bubble_colors = [f'rgb({r},{g},{b})'] * len(subnet_data)
    else:
        # Si es una serie, crear un color para cada valor
        for val in norm_values:
            # Cambiar de rojo a verde
            r = max(0, min(255, int(255 * (1 - val))))
            g = max(0, min(255, int(255 * val)))
            b = 0
            bubble_colors.append(f'rgb({r},{g},{b})')
    
    # Preparar el texto para el hover que incluya notas personales si existen
    hovertemplate = []
    for i, row in subnet_data.iterrows():
        template = f"<b>{row['Name']}</b><br>Service-Research: {row['Service-Research']:.2f}<br>Intelligence-Resource: {row['Intelligence-Resource']:.2f}<br>Score: {row['custom-eval']:.1f}"
        # Añadir notas personales solo si están disponibles, con fuente 3 veces más grande
        if 'personal-notes' in subnet_data.columns and pd.notna(row.get('personal-notes', None)) and row['personal-notes'].strip() != '':
            template += f"<br><br><span style='font-size: 18px; font-style: italic;'><b>Notes:</b> {row['personal-notes']}</span>"
        template += "<extra></extra>"
        hovertemplate.append(template)
        
    # Añadir las líneas sigmoideas (y = 20/(1+exp(-0.4*(x+z)))-11.9) con diferentes valores de z
    z_values = [6, 9, 12, 15, 18]
    line_colors = ['rgba(255, 255, 255, 0.8)', 'rgba(255, 255, 255, 0.8)', 'rgba(255, 255, 255, 0.8)', 'rgba(255, 255, 255, 0.8)', 'rgba(255, 255, 255, 0.8)']
    line_dashes = ['dash', 'dot', 'dashdot', 'longdash', 'longdashdot']
    line_widths = [2.0, 2.2, 1.8, 2.1, 1.9]
    names = ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5']
    time_labels = ['6 months', '12 months', '18 months', '24 months', '30 months']
    
    x_range = np.linspace(-10, 10, 200)  # Crear 200 puntos para una curva suave
    
    for i, (z, color, dash, width, name, time_label) in enumerate(zip(z_values, line_colors, line_dashes, line_widths, names, time_labels)):
        # Calcular la función sigmoidea para cada valor de x
        y_values = [20 / (1 + np.exp(-0.4 * (x + z))) - 11.9 for x in x_range]
        
        # Añadir la línea al gráfico
        fig.add_trace(go.Scatter(
            x=x_range,
            y=y_values,
            mode='lines+text',
            line=dict(color=color, width=width, dash=dash),  # Diferentes estilos de línea para cada curva
            name=name,
            text=[time_label if i == 0 else '' for i in range(len(x_range))],  # Solo mostrar el texto al inicio (x=-10)
            textposition='middle left',  # Posición del texto a la izquierda de la línea
            textfont=dict(size=18, color=color, family='Arial, sans-serif'),  # Formato del texto con tamaño aumentado
            hovertemplate=f"<b>Estimated time:</b> {time_label}<extra></extra>"
        ))
        
    # Añadir puntos al gráfico (sobre las líneas para que queden visibles)
    fig.add_trace(go.Scatter(
        x=subnet_data['Service-Research'],
        y=subnet_data['Intelligence-Resource'],
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=bubble_colors,
            opacity=0.7,
            line=dict(width=1, color='white'),
        ),
        # Solo mostrar el nombre de la subnet dentro de la burbuja, sin las coordenadas
        text=subnet_data['Name'],  # Eliminar las coordenadas que aparecían antes
        textposition='middle center',  # Texto en el centro de la burbuja
        textfont=dict(size=18, color='white', family='Arial, sans-serif'),  # Tamaño de texto más grande y en blanco
        hovertemplate=hovertemplate,
    ))
    
    # Configurar diseño del gráfico
    fig.update_layout(
        title='',
        xaxis=dict(
            title='Service → Research',
            title_font=dict(size=28),  # Título del eje X con fuente 2 veces más grande
            range=[-10, 10],
            gridcolor='rgba(128, 128, 128, 0.5)',  # Cuadrícula más visible
            zerolinecolor='rgba(255, 255, 255, 0.8)',  # Línea cero más visible
            zeroline=True,
            showgrid=True,  # Mostrar cuadrícula
            gridwidth=1,    # Ancho de línea de cuadrícula
            dtick=5,        # Mostrar líneas cada 5 unidades
        ),
        yaxis=dict(
            title='Resource → Intelligence',  # Invertido el orden como solicitado
            title_font=dict(size=28),  # Título del eje Y con fuente 2 veces más grande
            range=[-10, 10],
            gridcolor='rgba(128, 128, 128, 0.5)',  # Cuadrícula más visible
            zerolinecolor='rgba(255, 255, 255, 0.8)',  # Línea cero más visible
            zeroline=True,
            showgrid=True,  # Mostrar cuadrícula
            gridwidth=1,    # Ancho de línea de cuadrícula
            dtick=5,        # Mostrar líneas cada 5 unidades
        ),
        plot_bgcolor='rgba(0, 0, 0, 0.9)',
        paper_bgcolor='rgba(0, 0, 0, 0.0)',
        font=dict(color='white'),
        width=1400,
        height=1100,
        showlegend=False,
        modebar_remove=['sendDataToCloud', 'select2d', 'lasso2d', 'resetScale2d', 'toImage', 'zoom2d', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d'],
        modebar_orientation='v',
        modebar_bgcolor='rgba(0,0,0,0)',
    )
    
    # Añadir escala de color (colorbar)
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(
            colorscale=[[0, 'rgb(255,0,0)'], [0.5, 'rgb(255,255,0)'], [1, 'rgb(0,255,0)']],  # Rojo a amarillo a verde
            showscale=True,
            cmin=subnet_data['custom-eval'].min(),
            cmax=subnet_data['custom-eval'].max(),
            colorbar=dict(
                title='Evaluation Score',
                titleside='right',
            ),
        ),
        hoverinfo='none',
        showlegend=False,
    ))
    
    return fig

def visualization_page():
    """Page for visualizing subnet data"""
    st.markdown('<h1 class="main-header" style="color: #FF8C00;">Subnet Visualization</h1>', unsafe_allow_html=True)
    
    # Load subnet data
    subnets_df = load_subnets_from_csv()
    
    if subnets_df.empty:
        st.warning(f"No data found to visualize. Please make sure the file {CSV_PATH} exists and contains valid data.")
        return
    
    # Initialize session state for subnet selection if it doesn't exist
    if 'selected_subnets' not in st.session_state:
        st.session_state['selected_subnets'] = {row['Name']: True for _, row in subnets_df.iterrows()}
    
    # Subnet selection section
    
    # Add "Select all" and "Deselect all" buttons
    st.markdown("""
    <style>
    /* Clase select-all-buttons eliminada ya que no se utiliza */
    .big-checkbox label {
        font-size: 1.15rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize states for checkboxes if they don't exist
    if 'select_all_checked' not in st.session_state:
        st.session_state['select_all_checked'] = False
    if 'deselect_all_checked' not in st.session_state:
        st.session_state['deselect_all_checked'] = False
        
    # Functions to handle checkbox state changes
    def on_select_all_change():
        # If "Select All" is activated, deactivate "Deselect All"
        if st.session_state['select_all']:
            st.session_state['deselect_all_checked'] = False
            # Mark all subnets as selected
            for name in subnets_df['Name'].tolist():
                st.session_state['selected_subnets'][name] = True
        st.session_state['select_all_checked'] = st.session_state['select_all']
    
    def on_deselect_all_change():
        # If "Deselect All" is activated, deactivate "Select All"
        if st.session_state['deselect_all']:
            st.session_state['select_all_checked'] = False
            # Mark all subnets as not selected
            for name in subnets_df['Name'].tolist():
                st.session_state['selected_subnets'][name] = False
        st.session_state['deselect_all_checked'] = st.session_state['deselect_all']
    
    # Buttons to select/deselect all
    select_all_col1, select_all_col2 = st.columns(2)
    
    with select_all_col1:
        st.markdown('<div class="big-checkbox">', unsafe_allow_html=True)
        st.checkbox("✓ Select All", key="select_all", value=st.session_state['select_all_checked'], on_change=on_select_all_change)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with select_all_col2:
        st.markdown('<div class="big-checkbox">', unsafe_allow_html=True)
        st.checkbox("✗ Deselect All", key="deselect_all", value=st.session_state['deselect_all_checked'], on_change=on_deselect_all_change)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)
    
    # Distribute subnet checkboxes across three columns
    col1, col2, col3 = st.columns(3)
    subnet_names = subnets_df['Name'].tolist()
    
    # Divide subnets into 3 groups for visual distribution
    n = len(subnet_names)
    per_col = n // 3 + (1 if n % 3 > 0 else 0)
    
    for i, col in enumerate([col1, col2, col3]):
        with col:
            # Removed group headers as requested
            start_idx = i * per_col
            end_idx = min((i + 1) * per_col, n)
            
            for name in subnet_names[start_idx:end_idx]:
                st.session_state['selected_subnets'][name] = st.checkbox(
                    name, value=st.session_state['selected_subnets'].get(name, True), key=f"cb_{name}"
                )
    
    # Apply filter based on selections
    selected_subnets = [name for name, selected in st.session_state['selected_subnets'].items() if selected]
    filtered_df = subnets_df[subnets_df['Name'].isin(selected_subnets)]
    
    if filtered_df.empty:
        st.warning("No subnets selected to visualize. Please select at least one.")
        return
    
    # Add more space between sections
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
    
    # Create chart with selected subnets
    fig = create_subnet_plot(filtered_df)
    
    # Display chart directly without container
    st.plotly_chart(fig, use_container_width=True)
    
    # Display detailed data table for selected subnets
    st.markdown("<h3>Detailed Data</h3>", unsafe_allow_html=True)
    
    # Add custom CSS to increase font size in the dataframe and adjust column widths
    # Con optimizaciones para móviles
    st.markdown("""
    <style>
    /* Estilos base de la tabla de datos */
    .stDataFrame {
        overflow-x: auto !important;
        max-width: 100% !important;
    }
    
    .stDataFrame td, .stDataFrame th {
        font-size: calc(0.9rem + 0.7vw) !important;
        padding: 0.5rem !important;
    }
    
    /* Ocultar la primera y segunda columna (índice y columna más a la izquierda) */
    .stDataFrame [data-testid="column_header"]:nth-child(1),
    .stDataFrame [data-testid="data-cell"]:nth-child(1),
    .stDataFrame [data-testid="column_header"]:nth-child(2),
    .stDataFrame [data-testid="data-cell"]:nth-child(2) {
        display: none !important;
    }
    
    /* Hacer que las columnas 2, 3, 4 y 5 (después de ocultar la primera) sean más estrechas */
    .stDataFrame [data-testid="column_header"]:nth-child(n+2):nth-child(-n+5),
    .stDataFrame [data-testid="data-cell"]:nth-child(n+2):nth-child(-n+5) {
        width: 100px !important;
        min-width: 100px !important;
        max-width: 100px !important;
    }
    
    /* Hacer que la columna personal-notes sea el doble de grande */
    .stDataFrame [data-testid="column_header"]:nth-child(6),
    .stDataFrame [data-testid="data-cell"]:nth-child(6) {
        width: 400px !important;
        min-width: 400px !important;
    }
    
    /* Optimizaciones para móviles */
    @media (max-width: 768px) {
        .stDataFrame td, .stDataFrame th {
            font-size: 0.85rem !important;
            padding: 0.4rem !important;
        }
        
        /* Hacer que todas las columnas se ajusten mejor en móviles */
        .stDataFrame [data-testid="column_header"],
        .stDataFrame [data-testid="data-cell"] {
            min-width: 80px !important;
        }
        
        /* Ajustar la columna de notas para que no sea tan ancha en móviles */
        .stDataFrame [data-testid="column_header"]:nth-child(6),
        .stDataFrame [data-testid="data-cell"]:nth-child(6) {
            width: 180px !important;
            min-width: 180px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(
        filtered_df,
        use_container_width=True,
    )

def framework_page():
    """Display the Sherpa's Framework page"""
    st.markdown('<h1 class="main-header" style="color: #41a358;">Sherpa\'s Framework</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="home-text">
    <h3>Framework Dimensions</h3>
    <ul>
        <li><strong>Service vs Research Orientation</strong>: Measures whether a subnet is primarily focused on providing services or conducting research.</li>
        <li><strong>Intelligence vs Resource Emphasis</strong>: Evaluates whether a subnet prioritizes computational intelligence or resource availability.</li>
        <li><strong>Quality Assessment</strong>: Indicated by color and size, representing the overall quality and effectiveness of the subnet implementation at the time it was evaluated.</li>
    </ul>
    <p style="font-size: 1.3rem; margin-top: 1rem; margin-bottom: 1rem;">Note: quadrant framework concept inspired by the report created by Crucible Labs - <a href="https://cruciblelabs.com/a-framework-for-classifying-bittensor-subnets/" target="_blank" style="font-weight: 500;">A Framework for Classifying Bittensor Subnets</a></p>
    
    <div style="background-color: rgba(255, 191, 0, 0.1); border-left: 4px solid #ffbf00; padding: 10px; margin: 15px 0;">
        <p style="margin: 0; font-weight: bold;">⚠️ Warning:</p>
        <ul style="margin-top: 5px; margin-bottom: 0;">
            <li>The evaluation is developed with the information available at the time of assessment, and many values are assigned subjectively based on the author's analysis. Evaluations may vary as more information becomes available or as subnet projects evolve.</li>
            <li>The Sherpa framework is not an absolute truth, and it is shared only because its cautious use allows less experienced users to better manage risk in their investments.</li>
            <li>The framework has already shown some inconsistencies when evaluating certain subnets. It will continue to improve, and all feedback is welcome.</li>
        </ul>
    </div>
    
    </div>
    """, unsafe_allow_html=True)
    
    # Crear columnas con proporción 1:1 (50% cada una) para PC
    # En móviles se convierte automáticamente en una sola columna
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Uso la imagen directamente desde Streamlit para asegurar que se muestre
        # Al ocupar la mitad del ancho de la pantalla, será aproximadamente 400px
        st.image("attached_assets/image_1746461783974.png", use_column_width=True)
    
    with col2:
        # Texto responsivo que se adapta al tamaño de pantalla
        st.markdown("""
        <div style="padding: 15px; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <h3 style="margin-top: 0; font-size: calc(1.2rem + 1vw); margin-bottom: 15px;">Investment Horizon Reference Lines</h3>
            <p style="font-size: calc(1rem + 0.8vw); line-height: 1.4; margin-bottom: 15px; font-weight: 400;">
                We reference the different lines that determine the desired investment horizon based on whether it's 6 months, 12, 18, etc.
            </p>
            <p style="font-size: calc(1rem + 0.8vw); line-height: 1.4; font-weight: 400;">
                Ideally, subnets should evolve over time toward the upper part of the chart. They can also compensate for their lack of vertical progress with a move toward the service quadrant.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Espacio entre la imagen y los criterios
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Evaluation criteria section
    st.markdown("""
    <div class="home-text">
    
    <h3>1. Quadrant Positioning Criteria</h3>
    <p>Each subnet is positioned in the Service-Research and Intelligence-Resource quadrants based on specific sets of weighted questions:</p>
    
    <h4>Service ↔ Research Axis</h4>
    <p><strong>Questions for SERVICE orientation:</strong></p>
    <div style="overflow-x: auto;">
    <table style="width:100%; border-collapse: collapse; margin-bottom: 15px; font-size: calc(0.7rem + 0.2vw);">
        <tr>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Question</th>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Weight</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is there already a working product or service?<br><em>Evaluates whether the subnet has a working product that users can interact with</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.75</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does it offer clear, immediate utility?<br><em>Evaluates whether users or other systems can already benefit from its outputs</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.75</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is there a current and obvious revenue model?<br><em>Assesses if the project is already making money or has a monetization plan</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">1.5</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Are there real-world use cases already implemented by third parties?<br><em>Validates if outside developers or businesses are actually using the subnet</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Are there measurable usage or adoption metrics?<br><em>Seeks evidence that people are actually using the service</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">0.5</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is the documentation geared toward implementation?<br><em>Checks if the docs are practical and help others build or integrate quickly</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">0.5</td>
        </tr>
    </table>
    </div>
    
    <p><strong>Questions for RESEARCH orientation:</strong></p>
    <div style="overflow-x: auto;">
    <table style="width:100%; border-collapse: collapse; margin-bottom: 15px; font-size: calc(0.7rem + 0.2vw);">
        <tr>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Question</th>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Weight</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Are they solving deep problems that don't have clear solutions yet?<br><em>Evaluates whether the subnet is focused on frontier exploration, not application</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">3.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does it conduct open research with public results?<br><em>Assesses if research findings and developments are shared publicly</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is the team's background more academic or research-heavy?<br><em>Assesses if the core contributors have experience in science or R&D</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does the roadmap prioritize breakthroughs over monetization?<br><em>Looks at whether the focus is progress and discovery, not short-term revenue</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">1.5</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Are they working on emerging or experimental technologies?<br><em>Evaluates how cutting-edge or exploratory the project is</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">1.5</td>
        </tr>
    </table>
    
    <h4>Intelligence ↔ Resource Axis</h4>
    <p><strong>Questions for INTELLIGENCE orientation:</strong></p>
    <div style="overflow-x: auto;">
    <table style="width:100%; border-collapse: collapse; margin-bottom: 15px; font-size: calc(0.7rem + 0.2vw);">
        <tr>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Question</th>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Weight</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is its main value in intelligent processing?<br><em>Evaluates if the computational tasks require significant AI or algorithmic intelligence</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.5</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does it take real expertise to join and contribute?<br><em>Assesses how much skill or knowledge is needed to be useful in the subnet</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">3.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is it generating new knowledge or insights?<br><em>Evaluates whether it creates value by solving or learning, not just running tasks</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">1.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does it facilitate emergent intelligence?<br><em>Evaluates if the subnet enables new forms of intelligence to emerge from interactions</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">0.5</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does the system learn, adapt, or improve over time?<br><em>Checks for dynamic, self-improving capabilities in the subnet</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">3.0</td>
        </tr>
    </table>
    
    <p><strong>Questions for RESOURCE orientation:</strong></p>
    <div style="overflow-x: auto;">
    <table style="width:100%; border-collapse: collapse; margin-bottom: 15px; font-size: calc(0.7rem + 0.2vw);">
        <tr>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Question</th>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Weight</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is it resource-efficient relative to its purpose?<br><em>Evaluates if the subnet uses computational resources efficiently</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does it have high hardware requirements?<br><em>Assesses the level of hardware needed to participate</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is it more of a utility than a brainy system?<br><em>Checks whether the subnet is about availability and throughput, not intelligence</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Does location matter a lot for performance?<br><em>Assesses if physical placement (latency, jurisdiction) affects the subnet</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">1.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is there a direct correlation between provided resources and rewards?<br><em>Looks for subnets where more hardware equals more TAO</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">2.0</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Is distributed availability or redundancy a core feature?<br><em>Evaluates if reliability and uptime are one of the subnet's selling point</em></td>
            <td style="border: 1px solid #ddd; padding: 6px;">1.0</td>
        </tr>
    </table>
    
    <h3>2. Quality Assessment Criteria</h3>
    <p>Each subnet's quality and effectiveness are evaluated using the following criteria that impact the subnet's size and color in the visualization. The criteria values can range from negative to positive (typically -2.0 to +2.0), where negative values indicate detrimental aspects and positive values indicate beneficial aspects:</p>
    
    <div style="overflow-x: auto;">
    <table style="width:100%; border-collapse: collapse; margin-bottom: 15px; font-size: calc(0.7rem + 0.2vw);">
        <tr>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Criterion</th>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Weight</th>
            <th style="border: 1px solid #ddd; padding: 6px; text-align: left; background-color: rgba(65, 163, 88, 0.2);">Impact</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Current Revenue</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates existing monetization</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Revenue Prospects (6 months)</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±1.0</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses short-term financial viability</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Team Quantifiable</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±0.7</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Measures team size and composition transparency</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Team Track Record</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±0.7</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates team's experience in the field and specifically within the Bittensor ecosystem</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Competitive Viability</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±1.0</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses market position against competitors</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Total Addressable Market (TAM)</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+1.0</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates market size and growth potential</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Roadmap Quality</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.2</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses clarity and feasibility of development plans</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Documentation Quality</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.1</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Measures completeness and clarity of technical documentation</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">UI/UX Quality</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates user interface design and experience</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Token Economics</td>
            <td style="border: 1px solid #ddd; padding: 6px;">-2.0</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses additional token usage (negative impact)</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">GitHub Activity</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±0.1</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Measures development pace and community engagement</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Twitter Activity</td>
            <td style="border: 1px solid #ddd; padding: 6px;">±0.1</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates social presence and communication</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">dTAO Visibility</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.3</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses proper promotion to dTAO</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Third-party Integration Quality</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates quality of external integrations</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Established Project Partnerships</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses alliances with recognized projects</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Subnet Uniqueness</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates differentiation from other subnets</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">EVM Leverage</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+1.0</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses utilization of Ethereum Virtual Machine</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Miner Rewards Structure</td>
            <td style="border: 1px solid #ddd; padding: 6px;">-0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates if miners' rewards are slashed (negative impact)</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Cross-subnet Integration Potential</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+1.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Assesses ability to integrate with and improve other subnets</td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 6px;">Validator Incentivization</td>
            <td style="border: 1px solid #ddd; padding: 6px;">+0.5</td>
            <td style="border: 1px solid #ddd; padding: 6px;">Evaluates encouragement for running validators</td>
        </tr>

    </table>
    
    <h4>Additional Criteria Under Consideration</h4>
    <p>We are exploring the following additional criteria for future evaluations:</p>
    <ul style="margin-bottom: 20px;">
        <li><strong>On-chain Miner Activity</strong>: Analysis of miner registrations, activity patterns, and competitiveness metrics from on-chain data.</li>
        <li><strong>Source Code Quality Analysis</strong>: Comprehensive evaluation of codebase structure, documentation standards, development practices, and technical sustainability.</li>
        <li><strong>Alpha token utility</strong>: Assessment of utility and value creation mechanisms related to subnet-specific Alpha tokens.</li>
    </ul>
    
    <p style="font-style: italic; margin-bottom: 20px;">Have suggestions for additional evaluation criteria? We welcome your input to further enhance our framework.</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    # Configure page
    set_page_config()
    
    # Initialize state variables if they don't exist
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
            
    # Show navigation for other pages
    navigation()
    
    # Show selected page
    if st.session_state.get('page') == 'home':
        home_page()
    elif st.session_state.get('page') == 'visualization':
        visualization_page()
    elif st.session_state.get('page') == 'framework':
        framework_page()
    else:
        home_page()  # Default

if __name__ == "__main__":
    main()