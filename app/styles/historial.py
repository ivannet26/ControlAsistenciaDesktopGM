# app/styles/historial.py
"""Estilos del historial - estilo limpio tipo Clockify."""

from app.styles.colors import (
    COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO,
    COLOR_ACENTO, COLOR_ACENTO_SUAVE, COLOR_ERROR,
    COLOR_FONDO, RADIO_CARD, RADIO_CHIP,
)

# ============================================================
# CABECERA DE SEMANA (línea superior con título + total)
# ============================================================
QSS_HEADER_SEMANA_WIDGET = f"""
    background-color: transparent;
    border: none;
    border-bottom: 1px solid {COLOR_BORDE};
"""
QSS_HEADER_SEMANA_LABEL = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.8px;
    border: none;
    background: transparent;
"""
QSS_HEADER_SEMANA_TOTAL = f"""
    color: {COLOR_ACENTO};
    font-size: 12px;
    font-weight: 600;
    border: none;
    background: transparent;
"""

# ============================================================
# CABECERA DE DÍA (sub-cabecera)
# ============================================================
QSS_HEADER_DIA_WIDGET = f"""
    background-color: transparent;
    border: none;
"""
QSS_HEADER_DIA_LABEL = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    border: none;
    background: transparent;
"""
QSS_HEADER_DIA_TOTAL = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 10px;
    font-weight: 600;
    border: none;
    background: transparent;
"""

# ============================================================
# TARJETA DE REGISTRO
# ============================================================
QSS_TARJETA_REGISTRO = f"""
    #RegistroCard {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDE};
        border-radius: {RADIO_CARD}px;
    }}
    #RegistroCard:hover {{
        border: 1px solid {COLOR_BORDE_INPUT};
    }}
"""

QSS_TARJETA_DESC = f"""
    color: {COLOR_TEXTO};
    font-size: 12px;
    font-weight: 500;
    border: none;
    background: transparent;
"""

QSS_TARJETA_DURACION = f"""
    color: {COLOR_TEXTO};
    font-size: 12px;
    font-weight: 600;
    font-family: 'Consolas', 'Courier New', monospace;
    border: none;
    background: transparent;
"""

QSS_TARJETA_HORA = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 10px;
    border: none;
    background: transparent;
"""

QSS_TARJETA_PROYECTO = """
    font-size: 10px;
    font-weight: 500;
    border: none;
    background: transparent;
"""

QSS_TARJETA_CHIP = f"""
    background-color: rgba(33, 150, 243, 0.12);
    border: 1px solid rgba(33, 150, 243, 0.30);
    color: #90caf9;
    padding: 2px 8px;
    font-size: 9px;
    font-weight: 500;
    border-radius: {RADIO_CHIP}px;
"""

QSS_TARJETA_BTN_PLAY = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLOR_ACENTO};
        border: none;
        font-size: 11px;
        outline: none;
        border-radius: 11px;
    }}
    QPushButton:hover {{
        background-color: rgba(33, 150, 243, 0.15);
        color: {COLOR_ACENTO_SUAVE};
    }}
    QPushButton:focus {{ outline: none; }}
"""

QSS_TARJETA_BTN_DEL = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLOR_TEXTO_SECUNDARIO};
        border: none;
        font-size: 11px;
        outline: none;
        border-radius: 11px;
    }}
    QPushButton:hover {{
        background-color: rgba(229, 57, 53, 0.15);
        color: {COLOR_ERROR};
    }}
    QPushButton:focus {{ outline: none; }}
"""

QSS_HISTORIAL_VACIO = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    padding: 24px;
    font-size: 12px;
"""

QSS_HISTORIAL_CONTENEDOR = f"background-color: {COLOR_FONDO};"