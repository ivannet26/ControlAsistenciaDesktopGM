# app/ui/tracker_window.py
from datetime import date, datetime, timedelta
from app.utils import preferencias_store as PS
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QDialog, QSizePolicy,
)
from app.styles.colors import RADIO_CHIP

from app.services.api_client import ApiClient
from app.services.inactividad import MonitorInactividad
from app.ui.dialogs import (
    confirmar_eliminar,
    ModalInactividad,
)
from app.ui.dialogs.modal_entrada import ModalEntrada
from app.ui.widgets import (
    HeaderWidget,
    EntradaBox,
    HistorialView,
)
from app.utils.workers import ApiWorker, formatear_duracion
from app.styles import tracker as S


# Límites de chips
ANCHO_MAX_CHIP = 180
MAX_CHARS_CHIP = 24

# Heartbeat: consulta al servidor cada 5 s
INTERVALO_HEARTBEAT_MS = 5000


class TrackerWindow(QWidget):
    cerrar_sesion = Signal()

    def __init__(self, client: ApiClient, usuario: dict):
        super().__init__()
        self.client = client
        self.usuario = usuario
        self.registro_activo = None
        self.segundos_transcurridos = 0
        self._workers = []
        self._entrada_actual = None

        # Estado del heartbeat / cierre
        self._ocupado = False          # True mientras hay una acción local en curso
        self._hb_en_curso = False      # evita consultas solapadas
        self._cerrando_real = False    # True solo al cerrar sesión o "Salir"

        # Cache
        self._proyectos = []
        self._etiquetas = []
        self._tareas_por_proyecto = {}

        self.setWindowTitle(f"Control de Asistencia - {usuario.get('nombre', '')}")
        self.setWindowFlag(Qt.FramelessWindowHint)
        # ✅ Elimina el borde fantasma de Windows
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(420, 600)
        self.setMinimumWidth(380)
        self.setMinimumHeight(480)
        # ❌ NO aplicar setStyleSheet aquí

        self._armar_ui()

        self.reloj = QTimer(self)
        self.reloj.timeout.connect(self._tick)

        self._revisar_temporizador_activo()
        self._cargar_historial()

        self._precargar_proyectos()
        self._precargar_etiquetas()

        self.monitor_inactividad = MonitorInactividad(umbral_segundos=300, padre=self)
        self.monitor_inactividad.inactividad_detectada.connect(self._on_inactividad_detectada)
        self.monitor_inactividad.actividad_reanudada.connect(self._on_actividad_reanudada)

        # Heartbeat: detecta timers iniciados/detenidos desde la web.
        # Arranca aquí (no en showEvent) para correr aunque la ventana esté oculta.
        self.heartbeat = QTimer(self)
        self.heartbeat.timeout.connect(self._heartbeat)
        self.heartbeat.start(INTERVALO_HEARTBEAT_MS)

    # ================= UI =================
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra personalizada (blanca)
        self.title_bar = CustomTitleBar(
            self,
            f"Control de Asistencia - {self.usuario.get('nombre', '')}",
            mostrar_maximizar=True,
        )
        layout.addWidget(self.title_bar)

        # Contenedor con fondo oscuro del tracker
        contenido = QWidget()
        contenido.setObjectName("contenidoTracker")
        contenido.setAttribute(Qt.WA_StyledBackground, True)
        # Extraer solo el background del QSS del tracker
        contenido.setStyleSheet(
            "QWidget#contenidoTracker { background-color: #0d181f; }"
        )
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(14, 14, 14, 14)
        contenido_layout.setSpacing(10)

        self.header = HeaderWidget(self.usuario.get("nombre", ""))
        self.header.cerrar_sesion.connect(self._on_cerrar_sesion)
        contenido_layout.addWidget(self.header)
        contenido_layout.addWidget(self._separador())

        self.label_mensaje = QLabel("")
        self.label_mensaje.setVisible(False)
        self.label_mensaje.setWordWrap(True)
        contenido_layout.addWidget(self.label_mensaje)

        self.entrada_box = EntradaBox()
        self.entrada_box.abrir_modal.connect(self._abrir_modal_entrada)
        self.entrada_box.play_clicked.connect(self._on_play_stop)
        contenido_layout.addWidget(self.entrada_box)

        self.preview_container = QWidget()
        self.preview_container.setVisible(False)
        self.preview_container.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(4, 0, 4, 0)
        self.preview_layout.setSpacing(6)
        contenido_layout.addWidget(self.preview_container)

        contenido_layout.addWidget(self._separador())

        self.historial = HistorialView()
        self.historial.reanudar.connect(self._reanudar_registro)
        self.historial.eliminar.connect(self._eliminar_registro)
        contenido_layout.addWidget(self.historial, 1)

        layout.addWidget(contenido)

    def _separador(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(S.QSS_SEPARADOR)
        linea.setFixedHeight(1)
        return linea

    # ================= PREVIEW =================
    def _renderizar_preview(self):
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._entrada_actual:
            self.preview_container.setVisible(False)
            self.entrada_box.set_descripcion("")
            self.entrada_box.set_estado(EntradaBox.ESTADO_VACIO)
            return

        self.entrada_box.set_descripcion(
            self._entrada_actual.get("descripcion", "")
        )

        proy = self._entrada_actual.get("proyecto_nombre", "")
        if proy:
            color = self._entrada_actual.get("color_proyecto") or "#10a878"
            chip = self._crear_chip(
                f"● {proy}",
                self._qss_chip_proyecto(color),
                texto_completo=proy,
            )
            self.preview_layout.addWidget(chip)

        etiquetas = self._entrada_actual.get("etiquetas", [])
        max_visibles = 3
        visibles = etiquetas[:max_visibles]
        ocultas = etiquetas[max_visibles:]

        for e in visibles:
            nombre = e.get("nombre", "")
            chip = self._crear_chip(
                nombre,
                self._qss_chip_preview("#90caf9"),
                texto_completo=nombre,
            )
            self.preview_layout.addWidget(chip)

        if ocultas:
            nombres_ocultas = "\n".join(
                f"• {e.get('nombre', '')}" for e in ocultas
            )
            badge = QLabel(f"+{len(ocultas)}")
            badge.setStyleSheet(self._qss_chip_badge())
            badge.setToolTip(f"Etiquetas ocultas:\n{nombres_ocultas}")
            badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            self.preview_layout.addWidget(badge)

        self.preview_layout.addStretch()
        self.preview_container.setVisible(True)

        if not self.registro_activo:
            self.entrada_box.set_estado(EntradaBox.ESTADO_LISTO)

    # -------- Helpers de chips --------
    def _crear_chip(self, texto: str, qss: str, texto_completo: str = "") -> QLabel:
        label = QLabel(self._acortar(texto))
        label.setStyleSheet(qss)
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        label.setMaximumWidth(ANCHO_MAX_CHIP)
        if texto_completo:
            label.setToolTip(texto_completo)
        return label

    def _acortar(self, texto: str) -> str:
        texto = texto or ""
        if len(texto) <= MAX_CHARS_CHIP:
            return texto
        return texto[:MAX_CHARS_CHIP - 1].rstrip() + "…"

    def _qss_chip_proyecto(self, color_hex: str) -> str:
        r, g, b = self._hex_to_rgb(color_hex)
        return f"""
            background-color: rgba({r}, {g}, {b}, 0.18);
            border: 1px solid rgba({r}, {g}, {b}, 0.55);
            color: {color_hex};
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 700;
            border-radius: {RADIO_CHIP}px;
        """

    def _qss_chip_preview(self, color: str) -> str:
        return f"""
            background-color: rgba(33, 150, 243, 0.12);
            border: 1px solid rgba(33, 150, 243, 0.30);
            color: {color};
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 500;
            border-radius: {RADIO_CHIP}px;
        """

    def _qss_chip_badge(self) -> str:
        return f"""
            background-color: rgba(33, 150, 243, 0.25);
            border: 1px solid rgba(33, 150, 243, 0.55);
            color: #bbdefb;
            padding: 3px 10px;
            font-size: 10px;
            font-weight: 700;
            border-radius: {RADIO_CHIP}px;
        """

    def _hex_to_rgb(self, hex_color: str):
        h = (hex_color or "#10a878").lstrip("#")
        if len(h) != 6:
            return (16, 168, 120)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return (16, 168, 120)

    # ================= Modal Entrada =================
    def _abrir_modal_entrada(self):
        if self.registro_activo:
            return

        dlg = ModalEntrada(
            client=self.client,
            padre=self,
            datos_iniciales=self._entrada_actual or {},
            proyectos=self._proyectos,
            etiquetas=self._etiquetas,
            tareas_por_proyecto=self._tareas_por_proyecto,
        )
        dlg.datos_actualizados.connect(self._refrescar_cache)

        if dlg.exec() != QDialog.Accepted or not dlg.resultado:
            return

        self._entrada_actual = dlg.resultado
        self._renderizar_preview()

    # ================= MENSAJES =================
    def _mostrar_mensaje(self, texto: str, tipo: str = "error"):
        self.label_mensaje.setText(texto)
        self.label_mensaje.setStyleSheet(S.qss_mensaje(tipo))
        self.label_mensaje.setVisible(True)
        QTimer.singleShot(4000, lambda: self.label_mensaje.setVisible(False))

    # ================= CARGA DE DATOS =================
    def _limpiar_workers(self):
        """Quita de la lista los workers ya terminados (el heartbeat crea uno cada 5 s)."""
        self._workers = [w for w in self._workers if not w.isFinished()]

    def _lanzar(self, funcion, on_exito, *args, **kwargs):
        self._limpiar_workers()
        worker = ApiWorker(funcion, *args, **kwargs)
        worker.exito.connect(on_exito)
        worker.error.connect(self._on_error_worker)
        self._workers.append(worker)
        worker.start()

    def _on_error_worker(self, mensaje: str):
        self._ocupado = False
        self._mostrar_mensaje(mensaje, "error")

    # ================= CACHE =================
    def _precargar_proyectos(self):
        self._lanzar(
            self.client.listar_proyectos,
            self._on_proyectos_cache,
        )

    def _on_proyectos_cache(self, proyectos):
        self._proyectos = proyectos or []
        for p in self._proyectos:
            pid = p.get("id")
            if pid is None:
                continue
            self._lanzar(
                self.client.listar_tareas,
                lambda tareas, pid=pid: self._on_tareas_cache(pid, tareas),
                proyecto_id=pid,
            )

    def _on_tareas_cache(self, proyecto_id, tareas):
        self._tareas_por_proyecto[proyecto_id] = tareas or []

    def _precargar_etiquetas(self):
        self._lanzar(
            self.client.listar_etiquetas,
            self._on_etiquetas_cache,
        )

    def _on_etiquetas_cache(self, etiquetas):
        self._etiquetas = etiquetas or []

    def _refrescar_cache(self):
        self._tareas_por_proyecto = {}
        self._precargar_proyectos()
        self._precargar_etiquetas()

    # ================= HISTORIAL =================
    def _revisar_temporizador_activo(self):
        self._lanzar(
            self.client.obtener_temporizador_activo,
            self._on_temporizador_activo,
        )

    def _on_temporizador_activo(self, registro):
        if not registro:
            return
        self.registro_activo = registro
        inicio = datetime.fromisoformat(registro["inicio"])
        ahora = datetime.now(inicio.tzinfo) if inicio.tzinfo else datetime.now()
        self.segundos_transcurridos = int((ahora - inicio).total_seconds())

        self._entrada_actual = {
            "descripcion": registro.get("descripcion") or "",
            "proyecto_id": registro.get("proyecto_id"),
            "proyecto_nombre": registro.get("nombre_proyecto") or "",
            "color_proyecto": registro.get("color_proyecto") or "#10a878",
            "tarea_id": registro.get("tarea_id"),
            "etiquetas": registro.get("etiquetas") or [],
            "etiquetas_ids": [e["id"] for e in (registro.get("etiquetas") or [])],
        }
        self._renderizar_preview()

        self.entrada_box.set_tiempo(formatear_duracion(self.segundos_transcurridos))
        self.entrada_box.set_estado(EntradaBox.ESTADO_CORRIENDO)
        self.reloj.start(1000)
        self.monitor_inactividad.iniciar()

    def _cargar_historial(self):
        hace_21_dias = (date.today() - timedelta(days=21)).isoformat()
        self._lanzar(
            self.client.historial_tiempos,
            self._on_historial_cargado,
            fecha_desde=hace_21_dias,
        )

    def _on_historial_cargado(self, registros):
        self.historial.cargar(registros)

    # ================= REANUDAR / ELIMINAR =================
    def _reanudar_registro(self, registro: dict):
        if self.registro_activo:
            self._mostrar_mensaje("Ya tienes un temporizador activo.", "error")
            return
        self._entrada_actual = {
            "descripcion": registro.get("descripcion") or "",
            "proyecto_id": registro.get("proyecto_id"),
            "proyecto_nombre": registro.get("nombre_proyecto") or "",
            "color_proyecto": registro.get("color_proyecto") or "#10a878",
            "tarea_id": registro.get("tarea_id"),
            "etiquetas": registro.get("etiquetas") or [],
            "etiquetas_ids": [e["id"] for e in (registro.get("etiquetas") or [])],
        }
        self._renderizar_preview()
        QTimer.singleShot(200, self._iniciar)

    def _eliminar_registro(self, registro_id: int):
        if not registro_id:
            return
        if not confirmar_eliminar(
            padre=self,
            titulo="Eliminar actividad",
            mensaje="¿Estás seguro de eliminar esta actividad?",
            subtitulo="Esta acción no se puede deshacer.",
        ):
            return
        self._lanzar(
            self.client.eliminar_registro,
            self._on_registro_eliminado,
            registro_id=registro_id,
        )

    def _on_registro_eliminado(self, _):
        self._mostrar_mensaje("Actividad eliminada", "success")
        self._cargar_historial()

    # ================= TIMER =================
    def _tick(self):
        self.segundos_transcurridos += 1
        self.entrada_box.set_tiempo(
            formatear_duracion(self.segundos_transcurridos)
        )

    def _on_play_stop(self):
        if self.registro_activo:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        if self.registro_activo:
            return

        if not self._entrada_actual:
            self._abrir_modal_entrada()
            if not self._entrada_actual:
                return

        descripcion = self._entrada_actual.get("descripcion", "").strip()
        if not descripcion:
            self._mostrar_mensaje("Escribe en qué estás trabajando.", "error")
            return

        proyecto_id = self._entrada_actual.get("proyecto_id")
        if proyecto_id is None:
            self._mostrar_mensaje("Selecciona un proyecto.", "error")
            return

        self._ocupado = True   # el heartbeat no interfiere mientras se inicia
        self._lanzar(
            self.client.iniciar_temporizador,
            self._on_iniciado,
            proyecto_id=proyecto_id,
            descripcion=descripcion,
            tarea_id=self._entrada_actual.get("tarea_id"),
            etiquetas_ids=self._entrada_actual.get("etiquetas_ids", []),
        )

    def _on_iniciado(self, registro):
        self._ocupado = False
        self.registro_activo = registro
        self.segundos_transcurridos = 0
        self.entrada_box.set_tiempo("00:00:00")
        self.entrada_box.set_estado(EntradaBox.ESTADO_CORRIENDO)
        self.reloj.start(1000)
        self.monitor_inactividad.iniciar()

    def _detener(self):
        self._ocupado = True   # el heartbeat no interfiere mientras se detiene
        self.reloj.stop()
        self._lanzar(self.client.detener_temporizador, self._on_detenido)

    def _on_detenido(self, registro):
        self._ocupado = False
        self.reloj.stop()   # necesario cuando se detiene desde la web
        self.monitor_inactividad.detener()
        self.registro_activo = None
        self.segundos_transcurridos = 0
        self.entrada_box.set_tiempo("00:00:00")
        self.entrada_box.set_estado(EntradaBox.ESTADO_VACIO)

        self._entrada_actual = None
        self._renderizar_preview()
        self._cargar_historial()

    # ================= HEARTBEAT =================
    def _heartbeat(self):
        if self._ocupado or self._hb_en_curso or self._cerrando_real:
            return
        self._hb_en_curso = True
        self._limpiar_workers()
        worker = ApiWorker(self.client.obtener_temporizador_activo)
        worker.exito.connect(self._on_heartbeat)
        worker.error.connect(self._on_heartbeat_error)
        self._workers.append(worker)
        worker.start()

    def _on_heartbeat_error(self, _mensaje):
        # Sin red o servidor dormido: se reintenta en el próximo ciclo, sin avisos
        self._hb_en_curso = False

    def _on_heartbeat(self, registro):
        self._hb_en_curso = False
        if self._ocupado:
            return

        activo_id = self.registro_activo.get("id") if self.registro_activo else None

        if registro and registro.get("id") != activo_id:
            # Timer iniciado (o cambiado) desde la web
            self._on_temporizador_activo(registro)
            # Solo mostrar la ventana si el usuario lo permite
            if PS.get_bool(PS.KEY_MOSTRAR_AL_INICIAR, True):
                self._traer_al_frente()
        elif not registro and self.registro_activo:
            # Timer detenido desde la web
            self._on_detenido(None)
            self._mostrar_mensaje("Temporizador detenido desde la web.", "success")

    def _traer_al_frente(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
        self.showNormal()
        self.raise_()
        self.activateWindow()
        QApplication.alert(self, 0)   # parpadea en la barra si Windows no da foco

    # ================= INACTIVIDAD =================
    def _on_inactividad_detectada(self, segundos_inactivo: int):
        import time
        self._ocupado = True   # pausa el heartbeat mientras el modal está abierto
        self.reloj.stop()
        self._inicio_inactividad = self.monitor_inactividad.ultima_actividad
        minutos = max(1, int(round(segundos_inactivo / 60)))

        desc = ""
        if self._entrada_actual:
            desc = self._entrada_actual.get("descripcion", "")

        modal = ModalInactividad(
            padre=self,
            minutos_inactivo=minutos,
            actividad=desc or "(sin descripción)",
            segundos_inactivo_inicial=segundos_inactivo,
        )
        modal.exec()

        segundos_totales = int(time.time() - self._inicio_inactividad)

        if self.registro_activo:
            # _ocupado se libera en _on_tiempo_ajustado o en _on_error_worker
            self._lanzar(
                self.client.ajustar_tiempo,
                self._on_tiempo_ajustado,
                registro_id=self.registro_activo.get("id"),
                segundos_descontar=segundos_totales,
            )
        else:
            self._ocupado = False
            self.reloj.start(1000)

    def _on_tiempo_ajustado(self, registro_actualizado):
        self._ocupado = False
        if not registro_actualizado:
            return
        self.registro_activo = registro_actualizado
        inicio = datetime.fromisoformat(registro_actualizado["inicio"])
        ahora = datetime.now(inicio.tzinfo) if inicio.tzinfo else datetime.now()
        self.segundos_transcurridos = max(0, int((ahora - inicio).total_seconds()))
        self.entrada_box.set_tiempo(
            formatear_duracion(self.segundos_transcurridos)
        )
        self.reloj.start(1000)
        self._mostrar_mensaje(
            "Tiempo de inactividad descontado correctamente", "success"
        )

    def _on_actividad_reanudada(self, segundos_inactivo: int):
        pass

    # ================= CIERRE =================
    def closeEvent(self, event):
        # La X solo oculta: la app sigue en la bandeja con el heartbeat activo
        if not self._cerrando_real:
            event.ignore()
            self.hide()
            return

        # Cierre real (cerrar sesión o "Salir" de la bandeja)
        if hasattr(self, "heartbeat"):
            self.heartbeat.stop()
        if hasattr(self, "monitor_inactividad"):
            self.monitor_inactividad.detener()
        if hasattr(self, "reloj"):
            self.reloj.stop()
        for worker in self._workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(500)
        event.accept()

    def _on_cerrar_sesion(self):
        if self.registro_activo:
            self._mostrar_mensaje("Detén el temporizador antes de cerrar sesión.", "error")
            return

        self.cerrar_sesion.emit()