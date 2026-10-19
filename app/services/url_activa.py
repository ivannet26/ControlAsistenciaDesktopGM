import logging
import os
import re
from pathlib import Path
import win32gui

_dir = Path(os.getenv("LOCALAPPDATA") or Path.home()) / "ControlAsistencia"
_dir.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("ca.url")
if not log.handlers:
    _h = logging.FileHandler(_dir / "url.log", encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)
    log.propagate = False

try:
    import uiautomation as auto
    _UIA = True
    log.info("uiautomation importado OK")
except Exception as e:
    _UIA = False
    log.error("uiautomation NO disponible: %r", e)


_TITULOS = ("Brave", "Chrome", "Edge", "Firefox", "Opera", "Vivaldi")

# Nombres/IDs conocidos (Añadidos específicos para Opera y Brave)
_NOMBRES = (
    "Address and search bar", "Barra de direcciones y de búsqueda",
    "Search or enter address", "Search with Google or enter address",
    "Buscar con Google o introducir dirección", "Address", "Dirección", "URL",
    "Barra de direcciones", "Escribe una dirección web",
    "Type search or URL", "Enter search or URL", "Buscar o introducir dirección",
    "Search or type URL", "Buscar o escribir URL"
)
_IDS = ("addressEditBox", "omnibox", "urlbar-input", "TextBox", "address-bar", "url-input")

_ya_logueado = set()

def _una_vez(clave, msg):
    if clave not in _ya_logueado:
        _ya_logueado.add(clave)
        log.warning(msg)

def _limpiar_url(url: str) -> str:
    """Limpia y valida la URL extraída."""
    if not url:
        return ""
    url = url.strip()
    
    # Si tiene espacios, probablemente sea texto de búsqueda, no una URL
    if " " in url and not url.startswith(("http://", "https://")):
        return ""
        
    # Si no tiene protocolo, se lo añadimos
    if not url.startswith(("http://", "https://", "file://")):
        url = "https://" + url
    return url

def url_navegador_activo() -> str | None:
    """Devuelve la URL de la barra de direcciones, o None."""
    if not _UIA:
        return None
    
    try:
        hwnd = win32gui.GetForegroundWindow()
        titulo = win32gui.GetWindowText(hwnd) or ""
        
        # 1. Verificar que sea un navegador
        if not any(n in titulo for n in _TITULOS):
            return None

        # 2. UI Automation
        ventana = auto.ControlFromHandle(hwnd)
        if ventana:
            # Intento 1: Por nombre exacto
            for nombre in _NOMBRES:
                try:
                    edit = ventana.EditControl(searchDepth=25, Name=nombre)
                    if edit.Exists(0.2, 0.05):
                        v = edit.GetValuePattern().Value
                        if v and v.strip():
                            url_limpia = _limpiar_url(v)
                            if url_limpia: return url_limpia
                except Exception:
                    pass

            # Intento 2: Por AutomationId
            for aid in _IDS:
                try:
                    edit = ventana.EditControl(searchDepth=25, AutomationId=aid)
                    if edit.Exists(0.2, 0.05):
                        v = edit.GetValuePattern().Value
                        if v and v.strip():
                            url_limpia = _limpiar_url(v)
                            if url_limpia: return url_limpia
                except Exception:
                    pass

            # Intento 3: BÚSQUEDA A CIEGAS (Mejorada para Brave/Opera)
            # Busca CUALQUIER EditControl que contenga "://" o termine en dominios comunes
            try:
                for c in ventana.GetChildren(True, 15): # Aumentamos profundidad a 15
                    if c.ControlTypeName == "EditControl":
                        try:
                            v = c.GetValuePattern().Value or ""
                            # Validación estricta: debe tener pinta de URL real
                            if "://" in v or (v.endswith((".com", ".org", ".net", ".es", ".io")) and " " not in v):
                                url_limpia = _limpiar_url(v)
                                if url_limpia: return url_limpia
                        except Exception:
                            continue
            except Exception as e:
                _una_vez("error_listado", f"Error listando EditControls: {e!r}")

        # 3. Fallback por Título (Si todo lo anterior falla)
        match = re.search(r'(https?://[^\s]+)', titulo)
        if match:
            return match.group(1)

        # Si no se encontró nada, registrar para depuración
        _una_vez(
            titulo[-25:],
            f"No se halló la barra. Ventana='{titulo[-40:]}' "
        )
        return None

    except Exception:
        log.exception("Error en url_navegador_activo")
        return None