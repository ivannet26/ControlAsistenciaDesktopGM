# app/styles/etiquetas.py
"""Estilos del selector de etiquetas (chips + combo)."""

from app.styles.colors import (
    COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_ACENTO, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ERROR, COLOR_INPUT_BG,
    RADIO_INPUT, RADIO_CHIP,
)

QSS_ETIQUETAS_CONTENEDOR = f"""
    QWidget {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDE};
        border-radius: {RADIO_INPUT}px;
    }}
"""
QSS_ETIQUETAS_LABEL = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    border: none;
"""
QSS_ETIQUETAS_COMBO = f"""
    QComboBox {{
        background-color: transparent;
        border: none;
        color: {COLOR_TEXTO};
        padding: 0px;
        font-size: 11px;
        min-width: 150px;
        outline: none;
    }}
    QComboBox::drop-down {{ border: none; width: 16px; }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-top: 4px solid {COLOR_TEXTO_SECUNDARIO};
    }}
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
QSS_CHIP = f"""
    QPushButton {{
        background-color: rgba(33, 150, 243, 0.15);
        border: 1px solid rgba(33, 150, 243, 0.35);
        color: #90caf9;
        padding: 2px 8px;
        font-size: 10px;
        font-weight: 500;
        border-radius: {RADIO_CHIP}px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: rgba(229, 57, 53, 0.18);
        border: 1px solid {COLOR_ERROR};
        color: {COLOR_ERROR};
    }}
    QPushButton:focus {{ outline: none; }}
"""