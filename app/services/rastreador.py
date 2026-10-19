import os
import sqlite3
import time
from datetime import datetime, date
from pathlib import Path
from app.services.url_activa import url_navegador_activo
from PySide6.QtCore import QObject, QTimer, Signal, QThread

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

            # 1) Crear tabla si no existe (sin el índice nuevo todavía)
            con.execute("""
                CREATE TABLE IF NOT EXISTS segmentos (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id   INTEGER DEFAULT 0,
                    app          TEXT    NOT NULL,
                    titulo       TEXT,
                    descripcion  TEXT,
                    url          TEXT,
                    inicio       TEXT    NOT NULL,
                    fin          TEXT,
                    duracion_seg INTEGER DEFAULT 0,
                    activo       INTEGER DEFAULT 1,
                    fecha        TEXT    NOT NULL
                )
            """)

            # 2) Si la tabla ya existía SIN usuario_id, añadirla AHORA
            cols = {r[1] for r in con.execute("PRAGMA table_info(segmentos)")}
            if "usuario_id" not in cols:
                con.execute(
                    "ALTER TABLE segmentos ADD COLUMN usuario_id INTEGER DEFAULT 0"
                )

            # 3) Ahora sí, crear los índices (la columna ya existe)
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_segmentos_fecha
                    ON segmentos(fecha)
            """)
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_segmentos_activo
                    ON segmentos(activo)
            """)
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_segmentos_usuario
                    ON segmentos(usuario_id, fecha)
            """)

            con.commit()
        finally:
            con.close()

    # ---------- Escritura ----------
    def cerrar_segmento_activo(self, usuario_id=None, fin_iso=None):
        if fin_iso is None:
            fin_iso = datetime.now().isoformat(timespec="seconds")
        con = self._conexion()
        try:
            if usuario_id is not None:
                con.execute("""
                    UPDATE segmentos
                    SET fin = ?,
                        duracion_seg = CAST(
                            (julianday(?) - julianday(inicio)) * 86400 AS INTEGER
                        ),
                        activo = 0
                    WHERE activo = 1 AND usuario_id = ?
                """, (fin_iso, fin_iso, int(usuario_id)))
            else:
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

    def crear_segmento(self, usuario_id, app, titulo, descripcion="", url=""):
        ahora = datetime.now()
        con = self._conexion()
        try:
            cur = con.execute("""
                INSERT INTO segmentos
                    (usuario_id, app, titulo, descripcion, url, inicio, activo, fecha)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                int(usuario_id or 0),
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
    def obtener_segmentos(self, usuario_id, fecha_iso):
        con = self._conexion()
        try:
            cur = con.execute("""
                SELECT * FROM segmentos
                WHERE usuario_id = ? AND fecha = ?
                ORDER BY inicio ASC
            """, (int(usuario_id or 0), fecha_iso))
            return [dict(r) for r in cur.fetchall()]
        finally:
            con.close()

    def obtener_segmento_por_id(self, seg_id):
        """Devuelve un segmento por su ID, o None si no existe."""
        con = self._conexion()
        try:
            cur = con.execute(
                "SELECT * FROM segmentos WHERE id = ?", (seg_id,)
            )
            fila = cur.fetchone()
            return dict(fila) if fila else None
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
# HILO PARA LEER URLS (Evita que la interfaz se congele)
# ============================================================
class HiloLectorURL(QThread):
    url_leida = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activo = True
        self._app_actual = ""

    def set_app(self, app):
        self._app_actual = app

    def run(self):
        while self._activo:
            # Solo leer si es un navegador conocido
            if self._app_actual in NAVEGADORES_CONOCIDOS:
                try:
                    # Esta llamada ya NO bloquea la interfaz
                    url = url_navegador_activo() or ""
                    self.url_leida.emit(url)
                except Exception:
                    pass
            
            # Pausa crítica: evita que el hilo consuma 100% CPU
            time.sleep(1) 

    def detener(self):
        self._activo = False
        self.wait()


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
        segmento_cerrado(dict)  → cada vez que se cierra un segmento,
                                   con TODOS los datos del segmento
        error(str)              → si falla algo irrecuperable
    """

    segmento_cerrado = Signal(dict)
    error = Signal(str)

    def __init__(self, usuario_id=None, intervalo_seg=5, parent=None):
        super().__init__(parent)
        self.usuario_id = int(usuario_id or 0)
        self.db = RastreadorDB()
        self.intervalo_seg = max(1, int(intervalo_seg))
        self._activo = False
        self._app_actual = None
        self._titulo_actual = None
        self._id_segmento = None
        self._url_actual = ""

        # Inicializar el hilo de lectura de URLs
        self._hilo_url = HiloLectorURL()
        self._hilo_url.url_leida.connect(self._actualizar_url_desde_hilo)
        self._hilo_url.start()

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
            self.error.emit("Faltan dependencias: instala 'pywin32' y 'psutil'.")
            return
        self.db.cerrar_segmento_activo(self.usuario_id)
        self._activo = True
        self._muestrear()
        self._timer.start(self.intervalo_seg * 1000)

    def detener(self):
        if not self._activo:
            return
        self._activo = False
        self._timer.stop()
        self.db.cerrar_segmento_activo(self.usuario_id)
        self._app_actual = None
        self._titulo_actual = None
        self._id_segmento = None
        self._url_actual = ""
        if hasattr(self, '_hilo_url'):
            self._hilo_url.detener()

    def set_intervalo(self, seg: int):
        self.intervalo_seg = max(1, int(seg))
        if self._activo:
            self._timer.start(self.intervalo_seg * 1000)

    def _actualizar_url_desde_hilo(self, url):
        """Recibe la URL desde el hilo secundario y la guarda."""
        self._url_actual = url

    # ---------- Muestreo ----------
    def _muestrear(self):
        app, titulo = _ventana_activa()
        print(f"[Rastreador] app={app!r} | titulo={titulo!r} | prev={self._app_actual!r}")

        if not app:
            return

        if app in APPS_IGNORADAS:
            if self._id_segmento is not None:
                self.db.cerrar_segmento_activo(self.usuario_id)
                seg = self.db.obtener_segmento_por_id(self._id_segmento)
                if seg:
                    try:
                        self.segmento_cerrado.emit(seg)
                    except Exception as e:
                        print(f"[Rastreador] Error emitiendo: {e}")
                self._app_actual = None
                self._titulo_actual = None
                self._id_segmento = None
                self._url_actual = ""
            return

        # Capturar URL real si es navegador (delegado al hilo)
        if app in NAVEGADORES_CONOCIDOS:
            self._hilo_url.set_app(app)
            url_real = self._url_actual # Usamos la última URL que leyó el hilo
        else:
            self._hilo_url.set_app("")
            url_real = ""

        # Sin cambio
        if (
            app == self._app_actual
            and titulo == self._titulo_actual
            and url_real == self._url_actual
        ):
            self.db.actualizar_duracion_activa()
            return

        # Cambio → cerramos anterior
        if self._id_segmento is not None:
            self.db.cerrar_segmento_activo(self.usuario_id)
            seg = self.db.obtener_segmento_por_id(self._id_segmento)
            if seg:
                try:
                    self.segmento_cerrado.emit(seg)
                except Exception as e:
                    print(f"[Rastreador] Error emitiendo: {e}")

        # Nuevo segmento CON usuario_id
        descripcion = self._descripcion_amigable(app, titulo)
        self._app_actual = app
        self._titulo_actual = titulo
        self._url_actual = url_real
        self._id_segmento = self.db.crear_segmento(
            usuario_id=self.usuario_id,   # 🔑
            app=app,
            titulo=titulo,
            descripcion=descripcion,
            url=url_real,
        )
        print(f"[Rastreador] NUEVO segmento {self._id_segmento} → {app} | {titulo[:40]} | URL={url_real[:60]}")

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
        return self.db.obtener_segmentos(self.usuario_id, fecha_iso)