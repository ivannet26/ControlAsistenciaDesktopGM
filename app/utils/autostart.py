
import sys
import os
import winreg
from pathlib import Path


APP_NAME = "ControlAsistencia"
RUTA_REGISTRO = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _ruta_ejecutable() -> str:
    """Devuelve la ruta del .exe si está empaquetada, o del python.exe si es dev."""
    if getattr(sys, "frozen", False):
        # Es un .exe empaquetado con PyInstaller
        return f'"{sys.executable}"'
    else:
        # Modo desarrollo: usar pythonw.exe + main.py
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        main_py = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "main.py")
        )
        return f'"{python_exe}" "{main_py}"'


def esta_habilitado() -> bool:
    """Comprueba si el auto-inicio está activado."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUTA_REGISTRO, 0, winreg.KEY_READ
        ) as key:
            try:
                winreg.QueryValueEx(key, APP_NAME)
                return True
            except FileNotFoundError:
                return False
    except Exception as e:
        print(f"[Autostart] Error leyendo registro: {e}")
        return False


def habilitar() -> bool:
    """Activa el auto-inicio en Windows."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUTA_REGISTRO,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(
                key,
                APP_NAME,
                0,
                winreg.REG_SZ,
                _ruta_ejecutable(),
            )
        return True
    except Exception as e:
        print(f"[Autostart] Error escribiendo registro: {e}")
        return False


def deshabilitar() -> bool:
    """Desactiva el auto-inicio."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUTA_REGISTRO,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        return True
    except Exception as e:
        print(f"[Autostart] Error eliminando registro: {e}")
        return False


def aplicar(activar: bool) -> bool:
    """Habilita o deshabilita el auto-inicio según el booleano."""
    if activar:
        return habilitar()
    else:
        return deshabilitar()
def _ruta_ejecutable() -> str:
    """Comando que Windows ejecutará al iniciar sesión."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --autostart'
    else:
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        main_py = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "main.py")
        )
        return f'"{python_exe}" "{main_py}" --autostart'    