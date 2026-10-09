# app/services/url_activa.py
"""
Lee la URL real de la barra de direcciones del navegador activo
usando UI Automation de Windows. NO usa el historial.
"""
import win32gui

try:
    import uiautomation as auto
    _UIA = True
except ImportError:
    _UIA = False
    print("[URL] ⚠️ uiautomation no instalado. pip install uiautomation")


_TITULOS = ("Brave", "Chrome", "Edge", "Firefox", "Opera", "Vivaldi")

# Nombres/IDs conocidos de la barra de direcciones
_NOMBRES = (
    "Address and search bar",
    "Barra de direcciones y de búsqueda",
    "Search or enter address",
    "Search with Google or enter address",
    "Buscar con Google o introducir dirección",
    "Address", "Dirección", "URL",
)
_IDS = ("addressEditBox", "omnibox", "urlbar-input")


def url_navegador_activo() -> str | None:
    """Devuelve la URL de la barra de direcciones, o None."""
    if not _UIA:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        titulo = win32gui.GetWindowText(hwnd) or ""
        if not any(n in titulo for n in _TITULOS):
            return None

        ventana = auto.ControlFromHandle(hwnd)
        if not ventana:
            return None

        # Intento 1: por nombre
        for nombre in _NOMBRES:
            try:
                edit = ventana.EditControl(searchDepth=20, Name=nombre)
                if edit.Exists(0.3, 0.05):
                    try:
                        v = edit.GetValuePattern().Value
                        if v and v.strip():
                            return v.strip()
                    except Exception:
                        pass
            except Exception:
                continue

        # Intento 2: por AutomationId
        for aid in _IDS:
            try:
                edit = ventana.EditControl(searchDepth=20, AutomationId=aid)
                if edit.Exists(0.3, 0.05):
                    try:
                        v = edit.GetValuePattern().Value
                        if v and v.strip():
                            return v.strip()
                    except Exception:
                        pass
            except Exception:
                continue

        # Intento 3: cualquier EditControl con valor tipo URL
        try:
            for c in ventana.GetChildren(True, 10):
                if c.ControlTypeName != "EditControl":
                    continue
                try:
                    v = c.GetValuePattern().Value or ""
                    if v.startswith("http") or (v and "." in v and " " not in v[:60]):
                        return v.strip()
                except Exception:
                    continue
        except Exception:
            pass

        return None
    except Exception as e:
        print(f"[URL] Error: {e}")
        return None