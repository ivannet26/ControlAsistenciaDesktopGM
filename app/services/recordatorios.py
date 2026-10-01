# app/services/recordatorios.py
from datetime import datetime, time

from PySide6.QtCore import QObject, QSettings, QTimer
from PySide6.QtWidgets import QSystemTrayIcon

ORG = "GMIngenieros"
APP = "ControlAsistencia"

DEFAULTS = {
    # Comportamiento
    "iniciar_con_app": False,
    "detener_bloqueo": True,
    "detener_reposo": True,
    "detener_apagado": True,
    # Recordatorio
    "rec_activo": True,
    "rec_cada_min": 10,
    "rec_inicio": "08:00",
    "rec_fin": "18:00",
    "rec_dias": "0,1,2,3,4",      # 0 = lunes ... 6 = domingo
    # Inactividad (solo la edita el administrador)
    "inact_umbral_min": 5,
    "inact_limite_min": 30,
}


def _s() -> QSettings:
    return QSettings(ORG, APP)


def leer_bool(clave: str) -> bool:
    return _s().value(clave, DEFAULTS[clave], type=bool)


def leer_int(clave: str) -> int:
    return _s().value(clave, DEFAULTS[clave], type=int)


def leer_str(clave: str) -> str:
    return str(_s().value(clave, DEFAULTS[clave]))


def guardar(clave: str, valor) -> None:
    _s().setValue(clave, valor)


def leer_dias() -> set:
    texto = leer_str("rec_dias")
    return {int(d) for d in texto.split(",") if d.strip().isdigit()}


def guardar_dias(dias) -> None:
    guardar("rec_dias", ",".join(str(d) for d in sorted(dias)))


def _a_hora(texto: str, defecto: time) -> time:
    try:
        h, m = texto.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        return defecto


class ServicioRecordatorios(QObject):
    """Cada 30 s revisa si toca recordar y avisa con la notificación de Windows."""

    def __init__(self, hay_timer_activo, tray=None, parent=None):
        super().__init__(parent)
        self._hay_timer_activo = hay_timer_activo   # callable -> bool
        self._tray = tray
        self._ultimo_aviso = None

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._revisar)
        self._timer.start(30_000)

    def set_tray(self, tray):
        self._tray = tray

    def detener(self):
        self._timer.stop()

    def _revisar(self):
        if not leer_bool("rec_activo"):
            return

        ahora = datetime.now()

        # Con timer corriendo no molesta; el intervalo cuenta desde que se detiene
        if self._hay_timer_activo():
            self._ultimo_aviso = ahora
            return

        if ahora.weekday() not in leer_dias():
            return

        inicio = _a_hora(leer_str("rec_inicio"), time(8, 0))
        fin = _a_hora(leer_str("rec_fin"), time(18, 0))
        if not (inicio <= ahora.time() <= fin):
            return

        cada = max(1, leer_int("rec_cada_min"))
        if self._ultimo_aviso and (ahora - self._ultimo_aviso).total_seconds() < cada * 60:
            return

        self._ultimo_aviso = ahora
        self._notificar()

    def _notificar(self):
        if not self._tray or not self._tray.isVisible():
            return
        self._tray.showMessage(
            "Control de Asistencia",
            "No tienes un temporizador activo. ¿Ya empezaste a trabajar?",
            QSystemTrayIcon.Information,
            10_000,
        )