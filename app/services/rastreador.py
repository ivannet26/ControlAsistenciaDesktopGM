import os
import sqlite3
from datetime import datetime, date
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal

# Dependencias opcionales (solo se activan en Windows)
try:
    import win32gui
    import win32process
    import psutil
    _WIN_AVAILABLE = True
except ImportError:
    _WIN_AVAILABLE = False


# ============================================================
# RUTA DE LA BASE DE DATOS
# ============================================================
def _directorio_datos() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home())
    d = Path(base) / "ControlAsistencia"
    d.mkdir(parents=True, exist_ok=True)
    return d


DB_PATH = _directorio_datos() / "rastreador.db"


# ============================================================
# NAVEGADORES Y COLORES CONOCIDOS
# ============================================================
NAVEGADORES_CONOCIDOS = {
    "chrome.exe":  "Google Chrome",
    "msedge.exe":  "Microsoft Edge",
    "firefox.exe": "Firefox",
    "brave.exe":   "Brave",
    "opera.exe":   "Opera",
    "vivaldi.exe": "Vivaldi",
}

COLORES_POR_APP = {
    "chrome.exe":  "#4285f4",
    "msedge.exe":  "#0078d4",
    "firefox.exe": "#ff7139",
    "brave.exe":   "#fb542b",
    "opera.exe":   "#ff1b2d",
    "vivaldi.exe": "#ef3939",
    "dota2.exe":   "#b71c1c",
    "code.exe":    "#007acc",
    "explorer.exe": "#f7b733",
}
COLOR_POR_DEFECTO = "#4b5563"

# Apps que NO queremos rastrear (la propia app, etc.)
APPS_IGNORADAS = {"python.exe", "pythonw.exe"}


# ============================================================
# BASE DE DATOS
# ============================================================
class RastreadorDB:
    """Capa de acceso a la BD SQLite del rastreador."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._crear_tablas()

    def _conexion(self):
        con = sqlite3.connect(self.db_path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def _crear_tablas(self):
        con = self._conexion()
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript("""
                CREATE TABLE IF NOT EXISTS segmentos (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    app          TEXT    NOT NULL,
                    titulo       TEXT,
                    descripcion  TEXT,
                    url          TEXT,
                    inicio       TEXT    NOT NULL,
                    fin          TEXT,
                    duracion_seg INTEGER DEFAULT 0,
                    activo       INTEGER DEFAULT 1,
                    fecha        TEXT    NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_segmentos_fecha
                    ON segmentos(fecha);
                CREATE INDEX IF NOT EXISTS idx_segmentos_activo
                    ON segmentos(activo);
            """)
            con.commit()
        finally:
            con.close()

    # ---------- Escritura ----------
    def cerrar_segmento_activo(self, fin_iso=None):
        if fin_iso is None:
            fin_iso = datetime.now().isoformat(timespec="seconds")
        con = self._conexion()
        try:
            con.execute("""
                UPDATE segmentos
                SET fin = ?,
                    duracion_seg = CAST(
                        (julianday(?) - julianday(inicio)) * 86400 AS INTEGER
                    ),
                    activo = 0
                WHERE activo = 1
            """, (fin_iso, fin_iso))
            con.commit()
        finally:
            con.close()

    def crear_segmento(self, app, titulo, descripcion="", url=""):
        ahora = datetime.now()
        con = self._conexion()
        try:
            cur = con.execute("""
                INSERT INTO segmentos
                    (app, titulo, descripcion, url, inicio, activo, fecha)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                app, titulo or "", descripcion or "", url or "",
                ahora.isoformat(timespec="seconds"),
                ahora.date().isoformat(),
            ))
            con.commit()
            return cur.lastrowid
        finally:
            con.close()

    def actualizar_duracion_activa(self):
        ahora = datetime.now().isoformat(timespec="seconds")
        con = self._conexion()
        try:
            con.execute("""
                UPDATE segmentos
                SET duracion_seg = CAST(
                    (julianday(?) - julianday(inicio)) * 86400 AS INTEGER
                )
                WHERE activo = 1
            """, (ahora,))
            con.commit()
        finally:
            con.close()

    # ---------- Lectura ----------
    def obtener_segmentos(self, fecha_iso):
        con = self._conexion()
        try:
            cur = con.execute("""
                SELECT * FROM segmentos
                WHERE fecha = ?
                ORDER BY inicio ASC
            """, (fecha_iso,))
            return [dict(r) for r in cur.fetchall()]
        finally:
            con.close()

    def eliminar_segmentos(self, ids):
        if not ids:
            return
        marcadores = ",".join("?" * len(ids))
        con = self._conexion()
        try:
            con.execute(
                f"DELETE FROM segmentos WHERE id IN ({marcadores})",
                list(ids),
            )
            con.commit()
        finally:
            con.close()


# ============================================================
# DETECCIÓN DE VENTANA ACTIVA
# ============================================================
def _ventana_activa():
    """
    Devuelve (app_exe, titulo) de la ventana que tiene el FOCO del teclado.

    Windows solo da foco a UNA ventana a la vez, incluso con varias pantallas.
    Esa ventana es la que el usuario está usando activamente (teclado + clics).

    Funciona bien en multi-monitor porque:
      - Si tecleas en DeepSeek (pantalla 1), esa ventana tiene el foco.
      - Si tecleas en Spotify (pantalla 2), esa ventana tiene el foco.

    ⚠️  La única limitación: si NO interactúas con ninguna ventana
    (solo miras y escuchas música), se registra la última que tuvo el foco.
    """
    if not _WIN_AVAILABLE:
        return None, None

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None

        titulo = win32gui.GetWindowText(hwnd) or ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            app = (psutil.Process(pid).name() or "").lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            app = ""

        return app, titulo
    except Exception:
        return None, None


# ============================================================
# SERVICIO PRINCIPAL
# ============================================================
class RastreadorAuto(QObject):
    """
    Servicio de rastreo automático.

    Uso típico (desde TrackerWindow):

        self.rastreador = RastreadorAuto(intervalo_seg=5)
        self.rastreador.iniciar()   # arranca el QTimer
        ...
        self.rastreador.detener()   # cierra el último segmento y para

    Señales:
        segmento_cerrado(dict)  → cada vez que se cierra un segmento
        error(str)              → si falla algo irrecuperable
    """

    segmento_cerrado = Signal(dict)
    error = Signal(str)

    def __init__(self, intervalo_seg=5, parent=None):
        super().__init__(parent)
        self.db = RastreadorDB()
        self.intervalo_seg = max(1, int(intervalo_seg))
        self._activo = False
        self._app_actual = None
        self._titulo_actual = None
        self._id_segmento = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._muestrear)

    # ---------- Control ----------
    @property
    def activo(self) -> bool:
        return self._activo

    def iniciar(self):
        if self._activo:
            return
        if not _WIN_AVAILABLE:
            self.error.emit(
                "Faltan dependencias: instala 'pywin32' y 'psutil'."
            )
            return
        # Cerramos cualquier segmento huérfano de una sesión anterior
        self.db.cerrar_segmento_activo()
        self._activo = True
        self._muestrear()                       # primer muestreo inmediato
        self._timer.start(self.intervalo_seg * 1000)

    def detener(self):
        if not self._activo:
            return
        self._activo = False
        self._timer.stop()
        self.db.cerrar_segmento_activo()
        self._app_actual = None
        self._titulo_actual = None
        self._id_segmento = None

    def set_intervalo(self, seg: int):
        self.intervalo_seg = max(1, int(seg))
        if self._activo:
            self._timer.start(self.intervalo_seg * 1000)

    # ---------- Muestreo ----------
    def _muestrear(self):
        app, titulo = _ventana_activa()

        # DEBUG: ver qué ve realmente el rastreador
        print(f"[Rastreador] app={app!r} | titulo={titulo!r} | prev={self._app_actual!r}")

        if not app:
            return

        # ─── Caso: app ignorada (el propio visor) ───
        if app in APPS_IGNORADAS:
            # Cerramos el segmento activo para que no crezca mientras
            # miras tu propia app. Cuando vuelvas a otra, se abrirá uno nuevo.
            if self._id_segmento is not None:
                print(f"[Rastreador] IGNORADA → cerrando segmento {self._id_segmento}")
                self.db.cerrar_segmento_activo()
                try:
                    self.segmento_cerrado.emit({"id": self._id_segmento})
                except Exception:
                    pass
                self._app_actual = None
                self._titulo_actual = None
                self._id_segmento = None
            return

        # ─── Sin cambio → solo refrescamos duración ───
        if app == self._app_actual and titulo == self._titulo_actual:
            self.db.actualizar_duracion_activa()
            return

        # ─── Cambio → cerramos anterior y abrimos nuevo ───
        if self._id_segmento is not None:
            self.db.cerrar_segmento_activo()
            try:
                self.segmento_cerrado.emit({"id": self._id_segmento})
            except Exception:
                pass

        descripcion = self._descripcion_amigable(app, titulo)
        self._app_actual = app
        self._titulo_actual = titulo
        self._id_segmento = self.db.crear_segmento(
            app=app,
            titulo=titulo,
            descripcion=descripcion,
            url="",
        )
        print(f"[Rastreador] NUEVO segmento {self._id_segmento} → {app} | {titulo[:50]}")

    def _descripcion_amigable(self, app: str, titulo: str) -> str:
        """'chrome.exe' + 'Instagram - Google Chrome' → 'Instagram'."""
        if app in NAVEGADORES_CONOCIDOS:
            navegador = NAVEGADORES_CONOCIDOS[app]
            limpio = titulo or ""
            for sufijo in (
                f" - {navegador}",
                f" — {navegador}",
                f" - {navegador} (",
                " - Google Chrome",
                " - Microsoft Edge",
                " - Brave",
                " - Mozilla Firefox",
            ):
                if sufijo in limpio:
                    limpio = limpio.split(sufijo)[0].strip()
            return limpio or navegador
        return titulo or app

    # ---------- Utilidades públicas ----------
    def color_para(self, app: str) -> str:
        return COLORES_POR_APP.get(app, COLOR_POR_DEFECTO)

    def es_navegador(self, app: str) -> bool:
        return app in NAVEGADORES_CONOCIDOS

    def registros_por_dia(self, fecha_iso=None):
        if fecha_iso is None:
            fecha_iso = date.today().isoformat()
        return self.db.obtener_segmentos(fecha_iso)