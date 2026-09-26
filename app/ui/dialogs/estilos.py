# app/ui/dialogs/estilos.py
"""
Estilos y paleta de colores reutilizables para diálogos.
"""

# ============================================================
# PALETA
# ============================================================

COLOR_FONDO = "#24343d"
COLOR_TARJETA = "#17242c"
COLOR_BORDE = "#263943"
COLOR_ACENTO = "#10a5f5"
COLOR_ACENTO_HOVER = "#0c94dc"
COLOR_TEXTO = "#e8f0f5"
COLOR_TEXTO_SECUNDARIO = "#8ea0af"
COLOR_HEADER_SEMANA = "#0a1218"
COLOR_HEADER_DIA = "#0d171d"
COLOR_PUNTO_VERDE = "#10a878"
COLOR_ERROR = "#ff5c5c"
COLOR_ERROR_HOVER = "#d94c4c"
COLOR_EXITO = "#7cd87c"


# ============================================================
# ESTILO BASE PARA QMessageBox
# ============================================================

ESTILO_MESSAGEBOX = f"""
    QMessageBox {{
        background-color: {COLOR_FONDO};
        color: {COLOR_TEXTO};
        border: 1px solid {COLOR_BORDE};
    }}

    QMessageBox QLabel {{
        color: {COLOR_TEXTO};
        font-size: 13px;
        background: transparent;
        border: none;
    }}

    QMessageBox QLabel#qt_msgbox_informativelabel {{
        color: {COLOR_TEXTO_SECUNDARIO};
        font-size: 12px;
        padding-top: 6px;
    }}

    QMessageBox QPushButton {{
        background-color: {COLOR_ACENTO};
        color: white;
        border: none;
        padding: 8px 20px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 3px;
        min-width: 110px;
    }}

    QMessageBox QPushButton:hover {{
        background-color: {COLOR_ACENTO_HOVER};
    }}

    QMessageBox QPushButton:pressed {{
        background-color: #0a7cbb;
    }}
"""


# ============================================================
# ESTILO CON BOTÓN ROJO (para eliminar)
# ============================================================

ESTILO_MESSAGEBOX_PELIGRO = ESTILO_MESSAGEBOX + f"""
    QMessageBox QPushButton:first-child {{
        background-color: {COLOR_ERROR};
    }}
    QMessageBox QPushButton:first-child:hover {{
        background-color: {COLOR_ERROR_HOVER};
    }}
    QMessageBox QPushButton:last-child {{
        background-color: transparent;
        border: 1px solid {COLOR_BORDE};
        color: {COLOR_TEXTO};
    }}
    QMessageBox QPushButton:last-child:hover {{
        background-color: #1a2831;
    }}
"""