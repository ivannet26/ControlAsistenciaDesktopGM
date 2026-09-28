# app/ui/dialogs/estilos.py
"""Estilos QSS para QMessageBox, alineados con la estética del Login."""

from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO,
    COLOR_ERROR, COLOR_ERROR_HOVER,
    RADIO_INPUT, RADIO_BOTON,
)

ESTILO_MESSAGEBOX = f"""
    QMessageBox {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDE};
        border-radius: {RADIO_INPUT}px;
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
        padding: 9px 22px;
        font-size: 12px;
        font-weight: 600;
        border-radius: {RADIO_BOTON}px;
        min-width: 110px;
    }}
    QMessageBox QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
    QMessageBox QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
"""

ESTILO_MESSAGEBOX_PELIGRO = ESTILO_MESSAGEBOX + f"""
    QMessageBox QPushButton:first-child {{
        background-color: {COLOR_ERROR};
    }}
    QMessageBox QPushButton:first-child:hover {{
        background-color: {COLOR_ERROR_HOVER};
    }}
    QMessageBox QPushButton:last-child {{
        background-color: transparent;
        border: 1px solid {COLOR_BORDE_INPUT};
        color: {COLOR_TEXTO};
    }}
    QMessageBox QPushButton:last-child:hover {{
        background-color: {COLOR_FONDO};
    }}
"""