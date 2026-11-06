"""Estilo deliberadamente mínimo: tema predeterminado y controles estándar."""
from tkinter import ttk

CONFIG = {
    'titulo': 'FIUFIU - Básico',
    'decorado': False,
    'archivo': 'datos_basico.json',  # Ruta histórica, solo para migración.
    'fondo': '#f0f0f0',
    'cabecera': '#f0f0f0',
    'titulo_color': '#000000',
    'subtitulo': '#000000',
    'tarjeta': '#f0f0f0',
    'borde': '#f0f0f0',
    'texto_secundario': '#000000',
    'destacado': '#000000',
    'pie': '#f0f0f0',
    'pie_texto': '#000000',
}


def preparar_estilos(ventana):
    """Conserva controles, márgenes y fuentes por defecto de Tkinter."""
    estilo = ttk.Style(ventana)
    # No hay paleta de marca: solo los estilos requeridos por formularios existentes.
    estilo.configure('Seccion.TLabel', font=('TkDefaultFont', 10, 'bold'))
    estilo.configure('Secundaria.TLabel', font=('TkDefaultFont', 9))
    estilo.configure('Principal.TButton')
