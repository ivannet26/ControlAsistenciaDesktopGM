# app/styles/login.py
"""Estilos para la pantalla de Login — sin bordes fantasma."""

from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE,
    COLOR_BORDE_INPUT, COLOR_INPUT_BG,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED, COLOR_ACENTO_SUAVE,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    RADIO_INPUT, RADIO_BOTON, RADIO_CARD_GRANDE,
)

# ---------- Hero (por si algún día lo usas) ----------
HERO_BG_FALLBACK = "#0d181f"
HERO_OVERLAY_ALPHA = 160

QSS_HERO_TAG = "color:#ffffff; font-size:11px; font-weight:500; letter-spacing:4px;"
QSS_HERO_TITULO = "color:#ffffff; font-size:34px; font-weight:800;"
QSS_HERO_SUBTITULO = "color:rgba(255,255,255,0.78); font-size:13px;"

# ---------- Panel derecho ----------
LOGIN_BG_RIGHT = COLOR_FONDO
LOGIN_CARD_BG = COLOR_PANEL
LOGIN_CARD_BORDER = COLOR_BORDE
LOGIN_CARD_RADIUS = RADIO_CARD_GRANDE

QSS_CARD = f"""
    QFrame#card {{
        background-color: {LOGIN_CARD_BG};
        border: 1px solid {LOGIN_CARD_BORDER};
        border-radius: {LOGIN_CARD_RADIUS}px;
    }}
"""

# ============================================================
# LABELS (todos sin borde ni fondo)
# ============================================================
QSS_LOGO_TEXTO_1 = """
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
    background: transparent;
    border: none;
    padding: 0;
"""

QSS_LOGO_TEXTO_2 = """
    color: #ffffff;
    font-size: 9px;
    font-weight: 500;
    letter-spacing: 1.2px;
    background: transparent;
    border: none;
    padding: 0;
"""

QSS_TITULO_SESION = f"""
    color: {COLOR_TEXTO};
    font-size: 20px;
    font-weight: 500;
    background: transparent;
    border: none;
    padding: 0;
"""

QSS_LABEL_FIELD = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    background: transparent;
    border: none;
    padding: 0;
"""

QSS_FOOTER_TEXTO = f"""
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    background: transparent;
    border: none;
    padding: 0;
"""

# ============================================================
# INPUTS / BOTONES
# ============================================================
QSS_INPUT = f"""
    QLineEdit {{
        background-color: {COLOR_INPUT_BG};
        border: 1px solid {COLOR_BORDE_INPUT};
        border-radius: {RADIO_INPUT}px;
        color: {COLOR_TEXTO};
        padding: 6px 12px;
        font-size: 12px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLOR_ACENTO};
    }}
    QLineEdit::placeholder {{
        color: {COLOR_TEXTO_TERCIARIO};
    }}
"""

QSS_BOTON = f"""
    QPushButton {{
        background-color: {COLOR_ACENTO};
        color: #ffffff;
        border: none;
        border-radius: {RADIO_BOTON}px;
        padding: 10px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
    QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
    QPushButton:disabled {{
        background-color: {COLOR_BORDE_INPUT};
        color: {COLOR_TEXTO_SECUNDARIO};
    }}
"""

QSS_FOOTER_LINK = f"""
    QPushButton {{
        background: transparent;
        border: none;
        color: {COLOR_ACENTO};
        font-size: 11px;
        font-weight: 500;
        padding: 0px 4px;
        text-align: left;
    }}
    QPushButton:hover {{
        color: {COLOR_ACENTO_SUAVE};
        text-decoration: underline;
    }}
"""