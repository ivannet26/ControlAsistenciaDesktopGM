# app/styles/tracker.py
"""Estilos del TrackerWindow, alineados con la estética del Login."""

from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_INPUT_BG, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_ERROR, COLOR_EXITO, COLOR_PELIGRO, COLOR_PELIGRO_HOVER,
    RADIO_INPUT, RADIO_BOTON, RADIO_CARD, RADIO_CHIP,
)

# ============================================================
# VENTANA
# ============================================================
QSS_TRACKER_WINDOW = f"background-color: {COLOR_FONDO};"

# ============================================================
# HEADER
# ============================================================
QSS_HEADER_TITULO = f"""
    color: {COLOR_TEXTO};
    font-size: 13px;
    font-weight: 600;
    border: none;
"""
QSS_HEADER_USUARIO = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    border: none;
"""
QSS_HEADER_LOGO_FALLBACK = f"""
    color: {COLOR_ACENTO};
    font-size: 13px;
    font-weight: 700;
"""
QSS_SEPARADOR = f"background-color: {COLOR_BORDE}; border: none;"

# ============================================================
# INPUTS
# ============================================================
QSS_INPUT = f"""
    QLineEdit {{
        background-color: {COLOR_INPUT_BG};
        border: 1px solid {COLOR_BORDE_INPUT};
        color: {COLOR_TEXTO};
        padding: 8px 12px;
        font-size: 12px;
        border-radius: {RADIO_INPUT}px;
    }}
    QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
    QLineEdit:disabled {{
        color: {COLOR_TEXTO_TERCIARIO};
        background-color: {COLOR_FONDO};
    }}
    QLineEdit::placeholder {{ color: {COLOR_TEXTO_TERCIARIO}; }}
"""

def qss_combo() -> str:
    return f"""
    QComboBox {{
        background-color: {COLOR_INPUT_BG};
        border: 1px solid {COLOR_BORDE_INPUT};
        color: {COLOR_TEXTO};
        padding: 8px 12px;
        font-size: 12px;
        border-radius: {RADIO_INPUT}px;
        outline: none;
    }}
    QComboBox:focus {{ border: 1px solid {COLOR_ACENTO}; }}
    QComboBox:disabled {{
        color: {COLOR_TEXTO_TERCIARIO};
        background-color: {COLOR_FONDO};
        border: 1px solid {COLOR_BORDE};
    }}
    QComboBox::drop-down {{ border: none; background: transparent; width: 0px; }}
    QComboBox::down-arrow {{ image: none; width: 0px; height: 0px; }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDE};
        border-radius: {RADIO_INPUT}px;
        color: {COLOR_TEXTO};
        selection-background-color: {COLOR_ACENTO};
        selection-color: white;
        outline: none;
        padding: 4px;
    }}
    """

# ============================================================
# BOTONES
# ============================================================
QSS_BOTON_AGREGAR = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLOR_TEXTO_SECUNDARIO};
        border: 1px solid {COLOR_BORDE_INPUT};
        border-radius: {RADIO_INPUT}px;
        font-size: 18px;
        font-weight: 500;
        outline: none;
    }}
    QPushButton:hover {{
        color: {COLOR_ACENTO};
        border: 1px solid {COLOR_ACENTO};
        background-color: rgba(33, 150, 243, 0.08);
    }}
    QPushButton:focus {{ outline: none; }}
    QPushButton:disabled {{
        color: {COLOR_TEXTO_TERCIARIO};
        border: 1px solid {COLOR_BORDE};
    }}
"""

def qss_boton_play(corriendo: bool) -> str:
    if corriendo:
        color, hover, pressed = COLOR_PELIGRO, COLOR_PELIGRO_HOVER, "#a81e1e"
    else:
        color, hover, pressed = COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED
    return f"""
    QPushButton {{
        background-color: {color};
        color: white;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 700;
        border: none;
        outline: none;
    }}
    QPushButton:hover   {{ background-color: {hover}; }}
    QPushButton:pressed {{ background-color: {pressed}; }}
    QPushButton:focus {{ outline: none; }}
    """

# ============================================================
# TIMER
# ============================================================
QSS_LABEL_TIEMPO = f"""
    color: {COLOR_TEXTO};
    font-size: 22px;
    font-weight: 600;
    font-family: 'Consolas', 'Courier New', monospace;
    letter-spacing: 1px;
"""

# ============================================================
# MENSAJES
# ============================================================
def qss_mensaje(tipo: str) -> str:
    if tipo == "error":
        return f"""
            background-color: rgba(229, 57, 53, 0.15);
            color: #ff8a80;
            border: 1px solid {COLOR_ERROR};
            padding: 8px 12px;
            font-size: 11px;
            font-weight: 500;
            border-radius: {RADIO_INPUT}px;
        """
    return f"""
        background-color: rgba(124, 216, 124, 0.12);
        color: #b9f6ca;
        border: 1px solid {COLOR_EXITO};
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 500;
        border-radius: {RADIO_INPUT}px;
    """

# ============================================================
# SCROLL
# ============================================================
QSS_SCROLL = f"""
    QScrollArea {{ background-color: transparent; border: none; }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
        margin: 2px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDE_INPUT};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {COLOR_ACENTO}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
"""

# ============================================================
# MENÚ CONTEXTUAL (botón +)
# ============================================================
QSS_MENU_CREAR = f"""
    QMenu {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDE};
        border-radius: {RADIO_INPUT}px;
        color: {COLOR_TEXTO};
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 20px;
        font-size: 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {COLOR_ACENTO};
        color: white;
    }}
"""