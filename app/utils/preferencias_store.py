# app/utils/preferencias_store.py
"""Guarda y carga preferencias del usuario con QSettings."""
from PySide6.QtCore import QSettings


ORGANIZACION = "GM Ingenieros"
APLICACION = "ControlAsistencia"


def _settings() -> QSettings:
    return QSettings(ORGANIZACION, APLICACION)


# ============================================================
# CLAVES
# ============================================================
# General
KEY_AUTOSTART = "general/autostart"
KEY_SIEMPRE_VISIBLE = "general/siempre_visible"
KEY_FORZAR_OFFLINE = "general/forzar_offline"
KEY_TEMA = "general/tema"
KEY_IDIOMA = "general/idioma"
KEY_MOSTRAR_AL_INICIAR = "general/mostrar_al_iniciar"

# Control de tiempo
KEY_NUEVO_AL_DETENER = "tiempo/nuevo_al_detener"
KEY_PREGUNTAR_DETENER = "tiempo/preguntar_detener"
KEY_REDONDEAR = "tiempo/redondear"
KEY_RECORDAR_INICIO = "tiempo/recordar_inicio"
KEY_NOTIFICAR_HORA = "tiempo/notificar_hora"

# Rastreador automático
KEY_AUTO_ACTIVAR = "auto/activar"
KEY_AUTO_SOLO_APPS = "auto/solo_apps"
KEY_AUTO_IGNORAR_INACTIVIDAD = "auto/ignorar_inactividad"
KEY_AUTO_INTERVALO = "auto/intervalo"


# ============================================================
# API
# ============================================================
def get_bool(key: str, default: bool = False) -> bool:
    valor = _settings().value(key, default)
    if isinstance(valor, str):
        return valor.lower() in ("true", "1", "yes")
    return bool(valor)


def set_bool(key: str, valor: bool):
    _settings().setValue(key, valor)


def get_str(key: str, default: str = "") -> str:
    return str(_settings().value(key, default))


def set_str(key: str, valor: str):
    _settings().setValue(key, valor)