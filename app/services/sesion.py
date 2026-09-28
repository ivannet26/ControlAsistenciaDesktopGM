# app/services/sesion.py
"""
Persistencia de credenciales con QSettings.
Guarda el email/password en el registro de Windows (~/.config en Linux/macOS).
Opcionalmente guarda el token para auto-login.
"""
from PySide6.QtCore import QSettings


ORG = "GM Ingenieros"
APP = "ControlAsistencia"


def _settings() -> QSettings:
    return QSettings(ORG, APP)


# ============================================================
# CREDENCIALES (email + password)
# ============================================================

def guardar_credenciales(email: str, password: str, recordar: bool = True):
    """Guarda o borra las credenciales según el checkbox."""
    s = _settings()
    if recordar:
        s.setValue("auth/recordar", True)
        s.setValue("auth/email", email)
        s.setValue("auth/password", password)
    else:
        s.setValue("auth/recordar", False)
        s.remove("auth/email")
        s.remove("auth/password")
    s.sync()


def cargar_credenciales() -> tuple[str, str, bool]:
    """Devuelve (email, password, recordar)."""
    s = _settings()
    recordar = s.value("auth/recordar", False, type=bool)
    if not recordar:
        return "", "", False
    email = s.value("auth/email", "", type=str)
    password = s.value("auth/password", "", type=str)
    return email, password, True


def borrar_credenciales():
    s = _settings()
    s.remove("auth/email")
    s.remove("auth/password")
    s.setValue("auth/recordar", False)
    s.sync()


# ============================================================
# SESIÓN (token para auto-login, opcional)
# ============================================================

def guardar_token(token: str):
    s = _settings()
    s.setValue("auth/token", token or "")
    s.sync()


def cargar_token() -> str | None:
    s = _settings()
    token = s.value("auth/token", "", type=str)
    return token or None


def borrar_sesion():
    """Borra token + credenciales (usar al cerrar sesión)."""
    s = _settings()
    s.remove("auth/token")
    # Ojo: NO borra las credenciales al cerrar sesión,
    # solo el token. Así el login queda precargado.
    s.sync()