# app/services/sesion.py
"""
Persistencia del correo recordado con QSettings.
No guarda contraseñas ni tokens.
"""
from PySide6.QtCore import QSettings


ORG = "GM Ingenieros"
APP = "ControlAsistencia"


def _settings() -> QSettings:
    return QSettings(ORG, APP)


# ============================================================
# CREDENCIALES (solo correo)
# ============================================================

def guardar_credenciales(email: str, recordar: bool = True):
    """Guarda o borra el correo recordado. Nunca guarda contraseña."""
    s = _settings()
    s.remove("auth/password")
    s.remove("auth/token")
    if recordar:
        s.setValue("auth/recordar", True)
        s.setValue("auth/email", (email or "").strip())
    else:
        s.setValue("auth/recordar", False)
        s.remove("auth/email")
    s.sync()


def cargar_credenciales() -> tuple[str, bool]:
    """Devuelve (email, recordar). La contraseña no se guarda."""
    s = _settings()
    recordar = s.value("auth/recordar", False, type=bool)
    if not recordar:
        return "", False
    email = (s.value("auth/email", "", type=str) or "").strip()
    return email, True


def borrar_credenciales():
    s = _settings()
    s.remove("auth/email")
    s.remove("auth/password")
    s.remove("auth/token")
    s.setValue("auth/recordar", False)
    s.sync()


def limpiar_credenciales_cuenta(email: str) -> None:
    """Borra las claves de QSettings si pertenecen a ese correo."""
    s = _settings()
    guardado = (s.value("auth/email", "", type=str) or "").strip()
    objetivo = (email or "").strip()
    if not guardado or not objetivo:
        return
    if guardado.casefold() != objetivo.casefold():
        return

    s.remove("auth/email")
    s.remove("auth/password")
    s.remove("auth/token")
    s.setValue("auth/recordar", False)
    s.sync()


def limpiar_credenciales_huerfanas() -> None:
    """Borra SIEMPRE password/token viejos; conserva solo el correo recordado."""
    s = _settings()
    s.remove("auth/password")
    s.remove("auth/token")

    recordar = s.value("auth/recordar", False, type=bool)
    email = (s.value("auth/email", "", type=str) or "").strip()
    if not recordar or not email:
        s.remove("auth/email")
        s.setValue("auth/recordar", False)
    s.sync()
