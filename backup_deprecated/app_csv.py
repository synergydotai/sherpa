"""
Sherpa - CSV Edition

Una aplicación Streamlit para analizar y visualizar subnets de Bittensor utilizando
un archivo CSV local como fuente de datos.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
from PIL import Image
import io

# Rutas de archivos
CSV_PATH = "subnets.csv"
BACKUP_DIR = "backups"

def load_subnets_from_csv(csv_path=CSV_PATH):
    """
    Cargar datos de subnets desde un archivo CSV local
    
    Args:
        csv_path (str): Ruta al archivo CSV
        
    Returns:
        pd.DataFrame: DataFrame con información de subnets
    """
    try:
        if not os.path.exists(csv_path):
            st.warning(f"No se encontró el archivo CSV en {csv_path}. Por favor, sube uno nuevo.")
            return pd.DataFrame()
            
        # Leer CSV con separador ';' y decimal ','
        df = pd.read_csv(csv_path, sep=';', decimal=',')
        
        # Verificar si tiene las columnas mínimas necesarias
        required_columns = ['Name', 'Service-Research', 'Intelligence-Resource', 'custom-eval']
        
        if all(col in df.columns for col in required_columns):
            return df
        else:
            missing = [col for col in required_columns if col not in df.columns]
            st.warning(f"El archivo CSV no tiene el formato esperado. Faltan columnas: {', '.join(missing)}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error al cargar datos desde CSV: {str(e)}")
        return pd.DataFrame()

def backup_csv_file(csv_path=CSV_PATH):
    """
    Hacer una copia de seguridad del archivo CSV actual con marca de tiempo
    
    Args:
        csv_path (str): Ruta al archivo CSV a respaldar
        
    Returns:
        str: Ruta al archivo de respaldo o None si falla
    """
    try:
        if not os.path.exists(csv_path):
            return None
            
        # Crear directorio de backups si no existe
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        # Generar nombre de archivo con marca de tiempo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(csv_path)
        backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}.csv"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Copiar archivo actual a backup
        import shutil
        shutil.copy2(csv_path, backup_path)
        
        return backup_path
    except Exception as e:
        st.error(f"Error al crear copia de seguridad: {str(e)}")
        return None

def save_subnets_to_csv(subnets_df, csv_path=CSV_PATH, create_backup=True):
    """
    Guardar datos de subnets a un archivo CSV local
    
    Args:
        subnets_df (pd.DataFrame): DataFrame con información de subnets
        csv_path (str): Ruta al archivo CSV
        create_backup (bool): Si es True, crea una copia de seguridad del archivo existente
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Crear backup del archivo actual si existe y se solicita
        if create_backup and os.path.exists(csv_path):
            backup_path = backup_csv_file(csv_path)
            if backup_path:
                st.success(f"Copia de seguridad creada en: {backup_path}")
        
        # Guardar a CSV con separador ';' y decimal ','
        subnets_df.to_csv(csv_path, sep=';', decimal=',', index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar datos en CSV: {str(e)}")
        return False

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
    /* Fondo oscuro para los gráficos de tipo cuadrante */
    .dark-bg-plot {
        background-color: #111111;
        border-radius: 0.5rem;
        padding: 1rem;
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
        
        # Control de navegación con botones
        if 'page' not in st.session_state:
            st.session_state['page'] = 'home'
        
        # Comprobar si hay subnets
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
        
        # El botón de Admin solo estará visible si el usuario está logueado
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
            
        if st.session_state.get('logged_in', False):
            if st.button("Panel Admin", key="nav_admin", 
                        type="primary" if st.session_state['page'] == 'admin' else "secondary",
                        use_container_width=True):
                st.session_state['page'] = 'admin'
                st.rerun()
                
            if st.button("Cerrar sesión", key="nav_logout", 
                        type="secondary",
                        use_container_width=True):
                st.session_state['logged_in'] = False
                st.session_state['page'] = 'home'
                st.success("Sesión cerrada correctamente")
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
    <li>Categorizar subnets en el espectro Service-Research e Intelligence-Resource</li>
    <li>Visualizar el posicionamiento y relaciones entre subnets</li>
    <li>Comparar el rendimiento y capacidades de diferentes subnets</li>
    <li>Identificar tendencias y patrones en el ecosistema de subnets</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar datos básicos
    st.markdown("<h2>Vista previa de datos</h2>", unsafe_allow_html=True)
    
    # Cargar subnets
    subnets_df = load_subnets_from_csv()
    
    if not subnets_df.empty:
        # Mostrar las primeras 6 filas
        st.dataframe(subnets_df.head(6), use_container_width=True)
    else:
        st.info("No hay datos disponibles para mostrar. Por favor, utiliza la sección Admin para subir un archivo CSV.")
    
    st.markdown("""
    <div class="home-text">
    <h2>Conceptos Clave</h2>
    
    <p>El gráfico de Ecosystem Mapping muestra:</p>
    <ul>
    <li><strong>Eje X</strong> - El espectro desde Service (izquierda) hasta Research (derecha)</li>
    <li><strong>Eje Y</strong> - El espectro desde Resource (abajo) hasta Intelligence (arriba)</li>
    <li><strong>Tamaño de burbuja</strong> - Proporcional a la puntuación de evaluación</li>
    <li><strong>Color</strong> - Indica la calidad relativa (de rojo a verde)</li>
    </ul>
    
    <h2>Comenzando</h2>
    
    <p>Para comenzar a utilizar Sherpa:</p>
    <ol>
    <li>Navega a la página de Visualización utilizando el menú lateral</li>
    <li>Explora el mapa del ecosistema de subnets</li>
    <li>Selecciona las subnets específicas que deseas analizar</li>
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
    # Reducir el tamaño de las burbujas al 10% del original
    sizes = subnet_data['custom-eval'] * 10
    norm_values = (subnet_data['custom-eval'] - subnet_data['custom-eval'].min()) / \
                  (subnet_data['custom-eval'].max() - subnet_data['custom-eval'].min()) \
                  if subnet_data['custom-eval'].max() != subnet_data['custom-eval'].min() else 0.5
    
    # Mapear norm_values a colores (de rojo a verde)
    colors = []
    # Comprobar si norm_values es un escalar o una serie
    if isinstance(norm_values, float):
        # Si es un escalar, crear un solo color
        val = norm_values
        r = max(0, min(255, int(255 * (1 - val))))
        g = max(0, min(255, int(255 * val)))
        b = 0
        colors = [f'rgb({r},{g},{b})'] * len(subnet_data)
    else:
        # Si es una serie, crear un color para cada valor
        for val in norm_values:
            r = max(0, min(255, int(255 * (1 - val))))
            g = max(0, min(255, int(255 * val)))
            b = 0
            colors.append(f'rgb({r},{g},{b})')
    
    # Preparar el texto para el hover que incluya notas personales si existen
    hovertemplate = []
    for i, row in subnet_data.iterrows():
        template = f"<b>{row['Name']}</b><br>Service-Research: {row['Service-Research']:.2f}<br>Intelligence-Resource: {row['Intelligence-Resource']:.2f}<br>Score: {row['custom-eval']:.1f}"
        # Añadir notas personales solo si están disponibles, con fuente 3 veces más grande
        if 'personal-notes' in subnet_data.columns and pd.notna(row.get('personal-notes', None)) and row['personal-notes'].strip() != '':
            template += f"<br><br><span style='font-size: 18px; font-style: italic;'><b>Notes:</b> {row['personal-notes']}</span>"
        template += "<extra></extra>"
        hovertemplate.append(template)
        
    # Añadir puntos al gráfico
    fig.add_trace(go.Scatter(
        x=subnet_data['Service-Research'],
        y=subnet_data['Intelligence-Resource'],
        mode='markers+text',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.7,
            line=dict(width=1, color='white'),
        ),
        # Solo mostrar el nombre de la subnet dentro de la burbuja, sin las coordenadas
        text=subnet_data['Name'],  # Eliminar las coordenadas que aparecían antes
        textposition='middle center',  # Texto en el centro de la burbuja
        textfont=dict(size=14, color='white', family='Arial, sans-serif'),  # Texto más grande y en blanco
        hovertemplate=hovertemplate,
    ))
    
    # Configurar diseño del gráfico
    fig.update_layout(
        title='Mapping the Bittensor Subnet Ecosystem',
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
        width=800,
        height=600,
        showlegend=False,
    )
    
    # Añadir escala de color (colorbar)
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(
            colorscale='RdYlGn',
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
    """Página para visualizar datos de subnet"""
    st.markdown('<h1 class="main-header">Visualización de Subnets</h1>', unsafe_allow_html=True)
    
    # Cargar datos de subnets
    subnets_df = load_subnets_from_csv()
    
    if subnets_df.empty:
        st.warning("No se encontraron datos para visualizar. Por favor, utiliza la sección Admin para subir un archivo CSV.")
        return
    
    # Inicializar estado de sesión para selección de subnets si no existe
    if 'selected_subnets' not in st.session_state:
        st.session_state['selected_subnets'] = {row['Name']: True for _, row in subnets_df.iterrows()}
    
    # Selección de subnets a mostrar
    st.markdown('<h3>Seleccionar Subnets para Visualizar</h3>', unsafe_allow_html=True)
    
    # Añadir botones de "Seleccionar todos" y "Deseleccionar todos"
    st.markdown("""
    <style>
    .select-all-buttons {
        display: flex;
        gap: 20px;
        margin-bottom: 15px;
    }
    .big-checkbox label {
        font-size: 1.15rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializar estados para los checkboxes si no existen
    if 'select_all_checked' not in st.session_state:
        st.session_state['select_all_checked'] = False
    if 'deselect_all_checked' not in st.session_state:
        st.session_state['deselect_all_checked'] = False
        
    # Funciones para manejar los cambios de estado de los checkboxes
    def on_select_all_change():
        # Si se activa "Seleccionar Todos", desactivar "Deseleccionar Todos"
        if st.session_state['select_all']:
            st.session_state['deselect_all_checked'] = False
            # Marcar todas las subnets como seleccionadas
            for name in subnets_df['Name'].tolist():
                st.session_state['selected_subnets'][name] = True
        st.session_state['select_all_checked'] = st.session_state['select_all']
    
    def on_deselect_all_change():
        # Si se activa "Deseleccionar Todos", desactivar "Seleccionar Todos"
        if st.session_state['deselect_all']:
            st.session_state['select_all_checked'] = False
            # Marcar todas las subnets como no seleccionadas
            for name in subnets_df['Name'].tolist():
                st.session_state['selected_subnets'][name] = False
        st.session_state['deselect_all_checked'] = st.session_state['deselect_all']
    
    # Botones para seleccionar/deseleccionar todos
    select_all_col1, select_all_col2 = st.columns(2)
    
    with select_all_col1:
        st.markdown('<div class="big-checkbox">', unsafe_allow_html=True)
        st.checkbox("✓ Seleccionar Todos", key="select_all", value=st.session_state['select_all_checked'], on_change=on_select_all_change)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with select_all_col2:
        st.markdown('<div class="big-checkbox">', unsafe_allow_html=True)
        st.checkbox("✗ Deseleccionar Todos", key="deselect_all", value=st.session_state['deselect_all_checked'], on_change=on_deselect_all_change)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)
    
    # Filtrar dataframe según las subnets seleccionadas
    col1, col2, col3 = st.columns(3)
    subnet_names = subnets_df['Name'].tolist()
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
    filtered_df = subnets_df[subnets_df['Name'].isin(selected_names)]
    
    if filtered_df.empty:
        st.warning("Por favor, selecciona al menos una subnet para visualizar.")
        return
    
    # Crear visualización principal
    st.markdown('<h2 class="section-header">Mapa del Ecosistema de Subnets</h2>', unsafe_allow_html=True)
    
    # Contenedor con fondo oscuro para el gráfico
    with st.container():
        st.markdown('<div class="dark-bg-plot">', unsafe_allow_html=True)
        fig = create_subnet_plot(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-top: 1rem; font-size: 0.9rem; color: #888888;">
        Este gráfico muestra la posición de cada subnet en el ecosistema Bittensor:
        <ul>
            <li>El eje horizontal representa el espectro desde <b>Service</b> (izquierda) hasta <b>Research</b> (derecha)</li>
            <li>El eje vertical representa el espectro desde <b>Resource</b> (abajo) hasta <b>Intelligence</b> (arriba)</li>
            <li>El tamaño de cada burbuja es proporcional a su puntuación de evaluación</li>
            <li>El color indica la calidad relativa: rojo (inferior) a verde (superior)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Tabla de datos
    st.markdown('<h2 class="section-header">Datos de Subnets</h2>', unsafe_allow_html=True)
    st.dataframe(
        filtered_df.sort_values(by='custom-eval', ascending=False),
        column_config={
            'Name': st.column_config.TextColumn('Subnet'),
            'Service-Research': st.column_config.NumberColumn('Service-Research', format="%.2f"),
            'Intelligence-Resource': st.column_config.NumberColumn('Intelligence-Resource', format="%.2f"),
            'custom-eval': st.column_config.NumberColumn('Evaluation Score', format="%.2f"),
        },
        use_container_width=True,
    )

def login_page():
    """Página de inicio de sesión para el panel de administración"""
    # Configuraciones para el login
    valid_username = "xerpa"
    valid_password = "sherpa2024"
    
    st.markdown('<h1 class="main-header">Iniciar Sesión</h1>', unsafe_allow_html=True)
    
    # Añadir información sobre cómo acceder
    st.info("Accedes a través de: `/?route=xerpa` | Usuario: `xerpa` | Contraseña: `sherpa2024`")
    
    # Estilo para la página de login
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor de login
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="login-header">Panel de Administración</h2>', unsafe_allow_html=True)
    
    # Inicializar valores en el session_state si no existen
    if 'username' not in st.session_state:
        st.session_state['username'] = ''
    if 'password' not in st.session_state:
        st.session_state['password'] = ''
    if 'login_error' not in st.session_state:
        st.session_state['login_error'] = False
        
    # Función para manejar la autenticación
    def authenticate():
        if (st.session_state['username'] == valid_username and 
            st.session_state['password'] == valid_password):
            st.session_state['logged_in'] = True
            st.session_state['page'] = 'admin'
            st.session_state['login_error'] = False
            return True
        else:
            st.session_state['login_error'] = True
            return False
    
    # Formulario de login
    with st.form(key='login_form'):
        username = st.text_input("Usuario", key='username')
        password = st.text_input("Contraseña", type="password", key='password')
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("Iniciar sesión", use_container_width=True)
        
        with col2:
            if st.form_submit_button("Volver", use_container_width=True):
                st.session_state['page'] = 'home'
                st.rerun()
    
    # Mostrar mensaje de error si las credenciales son incorrectas
    if st.session_state['login_error']:
        st.error("Usuario o contraseña incorrectos")
    
    # Procesar autenticación cuando se envía el formulario
    if submitted:
        if authenticate():
            st.success("Has iniciado sesión correctamente. Redirigiendo...")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def admin_page():
    """Página de administración para gestionar el archivo CSV de subnets"""
    # Verificar si el usuario está logueado
    if not st.session_state.get('logged_in', False):
        login_page()
        return
    
    st.markdown('<h1 class="main-header">Panel de Administración</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="custom-info-box">
    <h3>Gestión de datos</h3>
    <p>En esta sección puedes subir un nuevo archivo CSV de subnets o descargar el actual.</p>
    <p>El archivo CSV debe tener las siguientes columnas:</p>
    <ul>
        <li><b>Name</b>: Nombre de la subnet</li>
        <li><b>Service-Research</b>: Valor en el eje X (uso de coma decimal)</li>
        <li><b>Intelligence-Resource</b>: Valor en el eje Y (uso de coma decimal)</li>
        <li><b>custom-eval</b>: Puntuación de evaluación (uso de coma decimal)</li>
        <li><b>personal-notes</b>: (Opcional) Notas personales que se mostrarán al pasar el cursor sobre la subnet</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Subir archivo CSV")
        uploaded_file = st.file_uploader("Selecciona un archivo CSV", type=["csv"])
        
        if uploaded_file is not None:
            try:
                # Intentar leer el archivo CSV
                try:
                    df = pd.read_csv(uploaded_file, sep=';', decimal=',')
                except:
                    # Intentar con otros separadores comunes si falla
                    try:
                        df = pd.read_csv(uploaded_file, sep=',', decimal='.')
                    except:
                        df = pd.read_csv(uploaded_file)
                
                # Verificar columnas requeridas
                required_columns = ['Name', 'Service-Research', 'Intelligence-Resource', 'custom-eval']
                missing = [col for col in required_columns if col not in df.columns]
                
                if missing:
                    st.error(f"El archivo CSV debe contener las columnas: {', '.join(required_columns)}. Faltan: {', '.join(missing)}")
                else:
                    # Hacer backup del archivo actual antes de sobrescribirlo
                    if os.path.exists(CSV_PATH):
                        backup_path = backup_csv_file()
                        if backup_path:
                            st.info(f"Se ha creado una copia de seguridad en: {backup_path}")
                    
                    # Guardar el archivo con el formato correcto
                    # Usar nuestra función que ahora gestiona las copias de seguridad
                    if save_subnets_to_csv(df):
                        st.success(f"Archivo CSV guardado correctamente")
                    
                    # Reiniciar estado para reflejar cambios
                    if 'selected_subnets' in st.session_state:
                        del st.session_state['selected_subnets']
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")
    
    with col2:
        st.markdown("### Descargar archivo CSV actual")
        
        if os.path.exists(CSV_PATH):
            # Preparar para descarga
            with open(CSV_PATH, 'r') as f:
                csv_str = f.read()
                
            st.download_button(
                label="Descargar archivo CSV",
                data=csv_str,
                file_name="subnets_export.csv",
                mime="text/csv"
            )
            
            # Mostrar una vista previa del CSV
            st.markdown("### Vista previa del CSV actual")
            df = pd.read_csv(CSV_PATH, sep=';', decimal=',')
            st.dataframe(df)
        else:
            st.warning("No hay archivo CSV disponible para descargar.")
    
    # Botón para restaurar el CSV de ejemplo original
    st.markdown("### Restaurar CSV original")
    
    if st.button("Restaurar datos de ejemplo originales"):
        try:
            # Hacer backup del archivo actual antes de restaurar
            if os.path.exists(CSV_PATH):
                backup_path = backup_csv_file()
                if backup_path:
                    st.info(f"Se ha creado una copia de seguridad en: {backup_path}")
            
            # Crear un CSV con el formato exacto requerido
            csv_content = """Name;Service-Research;Intelligence-Resource;custom-eval;personal-notes
pτn;-6,5;9;6,1;
chutes;-8,5;-1,75;8,3;
templar;9,5;7,5;2,55;I would like to understand Templar could be monetized.
dataverse;-5,2;2,5;5,75;
gradients;-3,7;7,4;4,7;
score;2,75;3,9;1,2;I want to see benchmarks compared to other centralized solutions.
3gen;-4,3;2,5;4,5;I wish 404 was more open in their developments and their roadmap.
targon;-6,7;-4,25;4,95;
nineteen;-6,3;-4,75;4,55;
bitmind;0,2;7,5;4,15;
vidaio;2,25;6,05;2,55;Will re-evaluate after 90 days.
staking;1,5;4,25;2,8;Will re-evaluate after 90 days."""
            
            # Escribir directamente al archivo
            with open(CSV_PATH, 'w') as f:
                f.write(csv_content)
            
            st.success(f"Archivo CSV original restaurado en {CSV_PATH}")
            
            # Mostrar lista de copias de seguridad disponibles
            backup_files = [f for f in os.listdir(BACKUP_DIR) if f.startswith('subnets_') and f.endswith('.csv')]
            if backup_files:
                st.markdown("### Copias de seguridad disponibles")
                st.markdown("Estas copias se han creado automáticamente al subir o restaurar archivos.")
                for backup in sorted(backup_files, reverse=True):
                    st.markdown(f"- `{backup}`")
            
            # Reiniciar estado para reflejar cambios
            if 'selected_subnets' in st.session_state:
                del st.session_state['selected_subnets']
                
        except Exception as e:
            st.error(f"Error al restaurar CSV original: {str(e)}")

def main():
    """Punto de entrada principal de la aplicación"""
    # Configurar página
    set_page_config()
    
    # Inicializar variables de estado si no existen
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    # Verificar URL para login directo
    # Para acceder al login, usar: /?route=xerpa
    # Usar st.query_params en lugar de la versión experimental que está obsoleta
    route = ''
    if 'route' in st.query_params:
        # Obtener el valor del parámetro route
        route = st.query_params['route']
    
    if route == 'xerpa':
        # No mostrar navegación en la página de login
        login_page()
        return
    elif route == 'admin':
        # Redirigir a xerpa si no está logueado
        if not st.session_state.get('logged_in', False):
            login_page()
            return
        else:
            st.session_state['page'] = 'admin'
            
    # Mostrar navegación para otras páginas
    navigation()
    
    # Mostrar la página seleccionada
    if st.session_state.get('page') == 'home':
        home_page()
    elif st.session_state.get('page') == 'visualization':
        visualization_page()
    elif st.session_state.get('page') == 'admin':
        # Verificar si está logueado antes de mostrar la página de admin
        if not st.session_state.get('logged_in', False):
            st.warning("Debes iniciar sesión para acceder al panel de administración")
            login_page()
        else:
            admin_page()
    else:
        home_page()  # Por defecto

if __name__ == "__main__":
    main()
