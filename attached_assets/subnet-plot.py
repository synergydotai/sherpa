import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap

# Basado en el script original subnet-plot.py citeturn0file0
def create_red_green_colormap():
    # Define los colores para el degradado (rojo a verde)
    colors = [
        (0.8, 0.1, 0.1),    # Rojo
        (0.8, 0.8, 0.1),    # Amarillo
        (0.1, 0.8, 0.1)     # Verde
    ]
    return LinearSegmentedColormap.from_list('custom_diverging', colors, N=256)


def load_subnet_data(filename='datos.csv'):
    # Leer CSV con separador ';' y decimal ','
    df = pd.read_csv(filename, sep=';', decimal=',')
    return df


def create_subnet_plot(subnet_data):
    # Estilo y fondo oscuro
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('#000000')
    ax.set_facecolor('#000000')

    # Configurar ejes en escala lineal de -10 a 10
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)

    # Definir ticks en los ejes
    ticks = [-10, -5, 0, 5, 10]
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)

    # Título y etiquetas
    plt.title('Mapping the Bittensor Subnet Ecosystem', pad=40, fontsize=16, color='white')

    # Líneas centrales en (0,0)
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax.axvline(x=0, color='gray', linestyle='-', alpha=0.3)

    # Grid
    ax.grid(True, linestyle='--', alpha=0.3)

    # Etiquetas de ejes
    fig.text(0.02, 0.95, 'Intelligence', ha='left', va='top', color='white')
    fig.text(0.02, 0.05, 'Resource', ha='left', va='bottom', color='white')
    fig.text(0.05, 0.02, 'Service → Research', ha='left', va='bottom', color='white')

    # Tamaño de burbujas según custom-eval
    size_scale = 500
    sizes = subnet_data['custom-eval'] * size_scale

    # Colormap y normalización
    cmap = create_red_green_colormap()
    norm_values = (subnet_data['custom-eval'] - subnet_data['custom-eval'].min()) / \
                  (subnet_data['custom-eval'].max() - subnet_data['custom-eval'].min())

    # Scatter plot usando los valores de Service-Research e Intelligence-Resource
    scatter = ax.scatter(
        subnet_data['Service-Research'],
        subnet_data['Intelligence-Resource'],
        c=norm_values,
        cmap=cmap,
        s=sizes,
        alpha=0.7
    )

    # Barra de color
    cbar = plt.colorbar(scatter)
    cbar.set_label('Evaluation Score', color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')

    # Anotar nombres y valores
    for idx, row in subnet_data.iterrows():
        label = f"{row['Name']}\n({row['custom-eval']:.1f})"
        ax.annotate(
            label,
            (row['Service-Research'], row['Intelligence-Resource']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            color='white',
            path_effects=[pe.withStroke(linewidth=2, foreground='black')]
        )

    plt.subplots_adjust(left=0.15, bottom=0.15, right=0.95, top=0.9)
    return fig, ax


if __name__ == "__main__":
    try:
        subnet_data = load_subnet_data()
        fig, ax = create_subnet_plot(subnet_data)
        plt.show()
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'datos.csv'")
        print("Asegúrate de que el archivo existe en el mismo directorio que el script")

