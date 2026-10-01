import sys
import time
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer, Signal, QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication

from app.services.recordatorios import leer_bool

# Mensajes de Windows
WM_QUERYENDSESSION = 0x0011
WM_ENDSESSION = 0x0016
WM_POWERBROADCAST = 0x0218
WM_WTSSESSION_CHANGE = 0x02B1

PBT_APMSUSPEND = 0x0004
WTS_SESSION_LOCK = 0x7
NOTIFY_FOR_THIS_SESSION = 0

# Si entre dos ticks de 1 s pasa más de esto, el equipo estuvo dormido
UMBRAL_SALTO_SEG = 30


class _Filtro(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self._callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type != b"windows_generic_MSG":
            return False, 0
        try:
            msg = wintypes.MSG.from_address(int(message))
            self._callback(msg.message, msg.wParam)
        except Exception as e:
            print(f"[Energia] Error leyendo evento: {e}")
        return False, 0


class MonitorEnergia(QObject):
    # motivo: "bloqueo" | "reposo" | "apagado", segundos perdidos (solo reposo)
    detener = Signal(str, int)

    def __init__(self, hwnd: int = 0, parent=None):
        super().__init__(parent)
        self._hwnd = hwnd
        self._filtro = None
        self._ultimo_tick = time.time()
        self._reposo_avisado = False

        if sys.platform == "win32":
            self._filtro = _Filtro(self._on_mensaje)
            QApplication.instance().installNativeEventFilter(self._filtro)
            if hwnd:
                try:
                    ctypes.windll.wtsapi32.WTSRegisterSessionNotification(
                        wintypes.HWND(hwnd), NOTIFY_FOR_THIS_SESSION
                    )
                except Exception as e:
                    print(f"[Energia] No se pudo registrar bloqueo: {e}")

        # Respaldo: detectar suspensión por salto del reloj
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ---------------- eventos nativos ----------------
    def _on_mensaje(self, mensaje: int, wparam: int):
        if mensaje == WM_WTSSESSION_CHANGE and wparam == WTS_SESSION_LOCK:
            self._emitir("detener_bloqueo", "bloqueo", 0)

        elif mensaje == WM_POWERBROADCAST and wparam == PBT_APMSUSPEND:
            self._reposo_avisado = True
            self._emitir("detener_reposo", "reposo", 0)

        elif mensaje in (WM_QUERYENDSESSION, WM_ENDSESSION):
            self._emitir("detener_apagado", "apagado", 0)

    # ---------------- respaldo por reloj ----------------
    def _tick(self):
        ahora = time.time()
        salto = ahora - self._ultimo_tick
        self._ultimo_tick = ahora

        if salto > UMBRAL_SALTO_SEG:
            if self._reposo_avisado:
                self._reposo_avisado = False   # ya se avisó por el mensaje nativo
            else:
                self._emitir("detener_reposo", "reposo", int(salto))

    # ---------------- util ----------------
    def _emitir(self, clave_pref: str, motivo: str, perdidos: int):
        if leer_bool(clave_pref):
            print(f"[Energia] {motivo} -> detener temporizador")
            self.detener.emit(motivo, perdidos)

    def cerrar(self):
        self._timer.stop()
        if self._filtro is not None:
            QApplication.instance().removeNativeEventFilter(self._filtro)
            self._filtro = None
        if sys.platform == "win32" and self._hwnd:
            try:
                ctypes.windll.wtsapi32.WTSUnRegisterSessionNotification(
                    wintypes.HWND(self._hwnd)
                )
            except Exception:
                pass