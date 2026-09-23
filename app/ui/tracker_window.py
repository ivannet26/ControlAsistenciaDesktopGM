from datetime import date, datetime

from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QListWidget, QListWidgetItem, QMessageBox, QFrame
)

from app.services.api_client import ApiClient, ApiError


def formatear_duracion(segundos: int) -> str:
    segundos = max(0, int(segundos))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class ApiWorker(QThread):
    """Worker genérico para no bloquear la UI con llamadas HTTP."""
    exito = Signal(object)
    error = Signal(str)

    def __init__(self, funcion, *args, **kwargs):
        super().__init__()
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            resultado = self.funcion(*self.args, **self.kwargs)
            self.exito.emit(resultado)
        except ApiError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}")


class TrackerWindow(QWidget):
    def __init__(self, client: ApiClient, usuario: dict):
        super().__init__()
        self.client = client
        self.usuario = usuario
        self.registro_activo = None
        self.segundos_transcurridos = 0
        self._workers = []  # evita que el garbage collector los borre a medio vuelo

        self.setWindowTitle(f"Control de Asistencia - {usuario.get('nombre', '')}")
        self.resize(420, 640)

        self._armar_ui()

        self.reloj = QTimer(self)
        self.reloj.timeout.connect(self._tick)

        self._cargar_proyectos()
        self._revisar_temporizador_activo()
        self._cargar_historial()

    # ================= UI =================
    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("¿En qué estás trabajando?")
        layout.addWidget(self.descripcion_input)

        self.combo_proyecto = QComboBox()
        self.combo_proyecto.addItem("Aún no hay proyecto", None)
        layout.addWidget(self.combo_proyecto)

        fila_timer = QHBoxLayout()
        self.label_tiempo = QLabel("00:00:00")
        self.label_tiempo.setStyleSheet("font-size: 28px; font-weight: 600;")
        fila_timer.addWidget(self.label_tiempo)
        fila_timer.addStretch()

        self.boton_play = QPushButton("▶")
        self.boton_play.setFixedSize(44, 44)
        self.boton_play.setStyleSheet(
            "background-color: #03a9f4; color: white; border-radius: 22px; font-size: 16px;"
        )
        self.boton_play.clicked.connect(self._on_play_stop)
        fila_timer.addWidget(self.boton_play)

        layout.addLayout(fila_timer)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        layout.addWidget(linea)

        titulo_historial = QLabel("HOY")
        titulo_historial.setStyleSheet("font-weight: 600; color: #666;")
        layout.addWidget(titulo_historial)

        self.lista_entradas = QListWidget()
        layout.addWidget(self.lista_entradas, 1)

    # ================= carga de datos =================
    def _lanzar(self, funcion, on_exito, *args, **kwargs):
        worker = ApiWorker(funcion, *args, **kwargs)
        worker.exito.connect(on_exito)
        worker.error.connect(self._mostrar_error)
        self._workers.append(worker)
        worker.start()

    def _cargar_proyectos(self):
        self._lanzar(self.client.listar_proyectos, self._on_proyectos_cargados)

    def _on_proyectos_cargados(self, proyectos):
        self.combo_proyecto.clear()
        self.combo_proyecto.addItem("Aún no hay proyecto", None)
        for p in proyectos or []:
            self.combo_proyecto.addItem(p.get("nombre", f"Proyecto {p.get('id')}"), p.get("id"))

    def _revisar_temporizador_activo(self):
        self._lanzar(self.client.obtener_temporizador_activo, self._on_temporizador_activo)

    def _on_temporizador_activo(self, registro):
        if not registro:
            return
        self.registro_activo = registro
        inicio = datetime.fromisoformat(registro["inicio"])
        ahora = datetime.now(inicio.tzinfo) if inicio.tzinfo else datetime.now()
        self.segundos_transcurridos = int((ahora - inicio).total_seconds())
        self.descripcion_input.setText(registro.get("descripcion") or "")
        self.label_tiempo.setText(formatear_duracion(self.segundos_transcurridos))
        self._set_estado_corriendo(True)
        self.reloj.start(1000)

    def _cargar_historial(self):
        self._lanzar(
            self.client.historial_tiempos,
            self._on_historial_cargado,
            fecha_desde=date.today().isoformat(),
        )

    def _on_historial_cargado(self, registros):
        self.lista_entradas.clear()
        for r in registros or []:
            duracion = formatear_duracion(r.get("duracion_segundos", 0))
            proyecto = r.get("nombre_proyecto") or "Sin proyecto"
            descripcion = r.get("descripcion") or "(sin descripción)"
            texto = f"{descripcion}   ·   {proyecto}   ·   {duracion}"
            self.lista_entradas.addItem(QListWidgetItem(texto))

    # ================= timer =================
    def _tick(self):
        self.segundos_transcurridos += 1
        self.label_tiempo.setText(formatear_duracion(self.segundos_transcurridos))

    def _set_estado_corriendo(self, corriendo: bool):
        if corriendo:
            self.boton_play.setText("■")
            self.boton_play.setStyleSheet(
                "background-color: #e53935; color: white; border-radius: 22px; font-size: 16px;"
            )
            self.descripcion_input.setEnabled(False)
            self.combo_proyecto.setEnabled(False)
        else:
            self.boton_play.setText("▶")
            self.boton_play.setStyleSheet(
                "background-color: #03a9f4; color: white; border-radius: 22px; font-size: 16px;"
            )
            self.descripcion_input.setEnabled(True)
            self.combo_proyecto.setEnabled(True)

    def _on_play_stop(self):
        if self.registro_activo:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        proyecto_id = self.combo_proyecto.currentData()
        if proyecto_id is None:
            QMessageBox.warning(self, "Selecciona un proyecto", "Debes elegir un proyecto antes de iniciar.")
            return

        descripcion = self.descripcion_input.text().strip()
        self._lanzar(
            self.client.iniciar_temporizador,
            self._on_iniciado,
            proyecto_id=proyecto_id,
            descripcion=descripcion,
        )

    def _on_iniciado(self, registro):
        self.registro_activo = registro
        self.segundos_transcurridos = 0
        self.label_tiempo.setText("00:00:00")
        self._set_estado_corriendo(True)
        self.reloj.start(1000)

    def _detener(self):
        self.reloj.stop()
        self._lanzar(self.client.detener_temporizador, self._on_detenido)

    def _on_detenido(self, registro):
        self.registro_activo = None
        self.segundos_transcurridos = 0
        self.label_tiempo.setText("00:00:00")
        self._set_estado_corriendo(False)
        self.descripcion_input.clear()
        self._cargar_historial()

    # ================= errores =================
    def _mostrar_error(self, mensaje: str):
        QMessageBox.critical(self, "Error", mensaje)
