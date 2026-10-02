# app/services/navegador_historial.py
"""
Lector directo del historial de navegadores Chromium.

NO usa `browser-history` porque no detecta Brave correctamente.
Lee las BD SQLite directamente, copiando el archivo primero
para evitar bloqueos mientras el navegador está abierto.
"""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, date, timedelta
from pathlib import Path


# ============================================================
# RUTAS DE NAVEGADORES (Windows)
# ============================================================
def _base_local() -> Path:
    return Path(os.getenv("LOCALAPPDATA") or Path.home())


def _base_roaming() -> Path:
    return Path(os.getenv("APPDATA") or Path.home())


def _rutas_navegadores():
    """Devuelve dict: {nombre: ruta_al_archivo_History}"""
    loc = _base_local()
    roi = _base_roaming()
    rutas = {
        "brave":   loc / "BraveSoftware" / "Brave-Browser" / "User Data" / "Default" / "History",
        "chrome":  loc / "Google" / "Chrome" / "User Data" / "Default" / "History",
        "edge":    loc / "Microsoft" / "Edge" / "User Data" / "Default" / "History",
        "opera":   roi / "Opera Software" / "Opera Stable" / "History",
        "vivaldi": loc / "Vivaldi" / "User Data" / "Default" / "History",
    }
    return rutas


# Alias para mostrar en el visor
NOMBRES_BONITOS = {
    "brave":   "Brave",
    "chrome":  "Google Chrome",
    "edge":    "Microsoft Edge",
    "firefox": "Firefox",
    "opera":   "Opera",
    "vivaldi": "Vivaldi",
}

COLORES_NAVEGADOR = {
    "brave":   "#fb542b",
    "chrome":  "#4285f4",
    "edge":    "#0078d4",
    "firefox": "#ff7139",
    "opera":   "#ff1b2d",
    "vivaldi": "#ef3939",
}


# ============================================================
# CONVERSIÓN DE FECHAS
# ============================================================
# Chromium guarda timestamps en microsegundos desde 1601-01-01 UTC.
# Diferencia en segundos entre 1601-01-01 y 1970-01-01 (epoch Unix):
_EPOCA_CHROMIUM_A_UNIX = 11644473600


def _chromium_a_datetime(ts: int) -> datetime:
    """
    Convierte un timestamp de Chromium (microsegundos desde 1601 UTC)
    a datetime en hora LOCAL del sistema.
    """
    if not ts:
        return None
    try:
        # 1. Microsegundos → segundos desde 1601
        segundos_desde_1601 = int(ts) / 1_000_000.0
        # 2. Restar diferencia → segundos desde 1970 (Unix)
        segundos_unix = segundos_desde_1601 - _EPOCA_CHROMIUM_A_UNIX
        # 3. datetime.fromtimestamp interpreta como hora local
        return datetime.fromtimestamp(segundos_unix)
    except (ValueError, OverflowError, OSError, TypeError):
        return None


def _datetime_a_chromium(dt: datetime) -> int:
    """
    Convierte un datetime (interpretado como hora local) a timestamp
    de Chromium (microsegundos desde 1601 UTC).
    """
    # dt.timestamp() devuelve segundos Unix (con conversión a UTC correcta)
    segundos_unix = dt.timestamp()
    segundos_desde_1601 = segundos_unix + _EPOCA_CHROMIUM_A_UNIX
    return int(segundos_desde_1601 * 1_000_000)


# ============================================================
# LECTURA DIRECTA DE CHROMIUM
# ============================================================
def _leer_historial_chromium(ruta_history: Path, nombre: str, desde: datetime, hasta: datetime):
    """
    Lee el historial de un navegador Chromium entre dos fechas.
    Copia el archivo primero (porque el navegador lo bloquea).
    """
    if not ruta_history.exists():
        return []

    tmp = None
    try:
        # Copiar a temp para no bloquearnos con el navegador abierto
        fd, tmp = tempfile.mkstemp(suffix=".db", prefix=f"hist_{nombre}_")
        os.close(fd)
        shutil.copy2(str(ruta_history), tmp)

        con = sqlite3.connect(tmp)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Convertir rango local a timestamps de Chromium
        ts_desde = _datetime_a_chromium(desde)
        ts_hasta = _datetime_a_chromium(hasta)

        cur.execute("""
            SELECT
                v.visit_time AS visit_time,
                u.url        AS url,
                u.title      AS title
            FROM visits v
            JOIN urls u ON u.id = v.url
            WHERE v.visit_time >= ? AND v.visit_time < ?
            ORDER BY v.visit_time ASC
        """, (ts_desde, ts_hasta))

        resultado = []
        for row in cur.fetchall():
            dt = _chromium_a_datetime(row["visit_time"])
            if dt is None:
                continue
            resultado.append({
                "fecha": dt,
                "url": row["url"] or "",
                "titulo": row["title"] or "",
                "navegador": nombre,
            })

        con.close()
        return resultado

    except Exception as e:
        print(f"[Historial] Error leyendo {nombre}: {e}")
        return []
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# ============================================================
# API PÚBLICA
# ============================================================
def disponible() -> bool:
    """True si al menos un navegador tiene BD de historial."""
    for ruta in _rutas_navegadores().values():
        if ruta.exists():
            return True
    return False


def color_para(navegador: str) -> str:
    return COLORES_NAVEGADOR.get((navegador or "").lower(), "#2196f3")


def obtener_historial(fecha=None, navegadores=None):
    """
    Devuelve lista de dicts con las visitas del día indicado:

        {
            "fecha":     datetime,
            "url":       str,
            "titulo":    str,
            "navegador": str,   # "brave", "chrome", ...
        }
    """
    # Rango [desde, hasta) en HORA LOCAL
    if fecha is None:
        desde = datetime.combine(date.today(), datetime.min.time())
    elif isinstance(fecha, datetime):
        desde = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        desde = datetime.combine(fecha, datetime.min.time())

    hasta = desde + timedelta(days=1)

    todas = []
    rutas = _rutas_navegadores()

    for nombre, ruta in rutas.items():
        if navegadores and nombre not in navegadores:
            continue
        visitas = _leer_historial_chromium(ruta, nombre, desde, hasta)
        todas.extend(visitas)

    # Ordenar por fecha
    todas.sort(key=lambda x: x["fecha"])
    return todas


def obtener_historial_dia_actual(navegadores=None):
    return obtener_historial(fecha=None, navegadores=navegadores)


# ============================================================
# DEBUG: ejecutable directo
# ============================================================
if __name__ == "__main__":
    print("Navegadores detectados:")
    for nombre, ruta in _rutas_navegadores().items():
        marca = "✓" if ruta.exists() else "✗"
        print(f"  {marca} {nombre:10s} → {ruta}")
    print()

    visitas = obtener_historial_dia_actual()
    print(f"Visitas hoy: {len(visitas)}")
    for v in visitas[:20]:
        print(f"  {v['fecha'].strftime('%H:%M:%S')} | {v['navegador']:10s} | "
              f"{v['titulo'][:40]:40s} | {v['url'][:60]}")