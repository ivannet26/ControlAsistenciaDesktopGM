from datetime import date, datetime, timedelta

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QScrollArea, QMessageBox, QFrame, QSizePolicy,
    QMenu, QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtGui import QAction

from app.services.api_client import ApiClient
from app.ui.common import ApiWorker, formatear_duracion


# ============================================================
# PALETA DE COLORES
# ============================================================

COLOR_FONDO = "#24343d"
COLOR_TARJETA = "#17242c"
COLOR_BORDE = "#263943"
COLOR_ACENTO = "#10a5f5"
COLOR_TEXTO = "#e8f0f5"
COLOR_TEXTO_SECUNDARIO = "#8ea0af"
COLOR_HEADER_SEMANA = "#0a1218"
COLOR_HEADER_DIA = "#0d171d"
COLOR_PUNTO_VERDE = "#10a878"
COLOR_ERROR = "#ff5c5c"
COLOR_EXITO = "#7cd87c"


# ============================================================
# HELPERS DE FECHAS
# ============================================================

def lunes_de_semana(fecha: date) -> date:
    return fecha - timedelta(days=fecha.weekday())


def nombre_dia(fecha: date) -> str:
    dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{dias[fecha.weekday()]}, {fecha.day} {meses[fecha.month - 1]}"


def etiqueta_dia(fecha: date) -> str:
    hoy = date.today()
    if fecha == hoy:
        return "HOY"
    if fecha == hoy - timedelta(days=1):
        return "AYER"
    if fecha == hoy - timedelta(days=2):
        return "ANTEAYER"
    return nombre_dia(fecha).upper()


def etiqueta_semana(lunes: date) -> str:
    hoy = date.today()
    lunes_actual = lunes_de_semana(hoy)
    lunes_anterior = lunes_actual - timedelta(days=7)

    if lunes == lunes_actual:
        return "ESTA SEMANA"
    if lunes == lunes_anterior:
        return "LA SEMANA PASADA"

    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"SEMANA DEL {lunes.day} {meses[lunes.month - 1].upper()}"


class TrackerWindow(QWidget):
    def __init__(self, client: ApiClient, usuario: dict):
        super().__init__()
        self.client = client
        self.usuario = usuario
        self.registro_activo = None
        self.segundos_transcurridos = 0
        self._workers = []

        # Lista de etiquetas seleccionadas (objetos completos {id, nombre, color})
        self.etiquetas_seleccionadas = []

        self.setWindowTitle(f"Control de Asistencia - {usuario.get('nombre', '')}")
        self.resize(560, 820)
        self.setStyleSheet(f"background-color: {COLOR_FONDO};")

        self._armar_ui()

        self.reloj = QTimer(self)
        self.reloj.timeout.connect(self._tick)

        self._cargar_proyectos()
        self._cargar_etiquetas()
        self._revisar_temporizador_activo()
        self._cargar_historial()

    # ================= UI =================
    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # -------- Mensaje de error/éxito integrado --------
        self.label_mensaje = QLabel("")
        self.label_mensaje.setVisible(False)
        self.label_mensaje.setWordWrap(True)
        layout.addWidget(self.label_mensaje)

        # -------- Fila: Descripción + Botón "+" --------
        fila_desc = QHBoxLayout()
        fila_desc.setSpacing(8)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("¿En qué estás trabajando?")
        self.descripcion_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 10px 12px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
        """)
        fila_desc.addWidget(self.descripcion_input, 1)

        # Botón "+" para crear tarea o etiqueta
        self.boton_agregar = QPushButton("+")
        self.boton_agregar.setFixedSize(42, 42)
        self.boton_agregar.setCursor(Qt.PointingHandCursor)
        self.boton_agregar.setToolTip("Crear nueva tarea o etiqueta")
        self.boton_agregar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO_SECUNDARIO};
                border: 1px solid {COLOR_BORDE};
                border-radius: 2px;
                font-size: 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {COLOR_ACENTO};
                border: 1px solid {COLOR_ACENTO};
            }}
        """)
        self.boton_agregar.clicked.connect(self._abrir_menu_crear)
        fila_desc.addWidget(self.boton_agregar)

        layout.addLayout(fila_desc)

        # -------- Proyecto --------
        self.combo_proyecto = QComboBox()
        self.combo_proyecto.addItem("Aún no hay proyecto", None)
        self.combo_proyecto.currentIndexChanged.connect(self._on_proyecto_seleccionado)
        self._estilizar_combo(self.combo_proyecto)
        layout.addWidget(self.combo_proyecto)

        # -------- Tarea --------
        self.combo_tarea = QComboBox()
        self.combo_tarea.addItem("Buscar tarea", None)
        self.combo_tarea.setEnabled(False)
        self._estilizar_combo(self.combo_tarea)
        layout.addWidget(self.combo_tarea)

        # -------- Selector de etiquetas (chips) --------
        self._armar_selector_etiquetas(layout)

        # -------- Fila del timer --------
        fila_timer = QHBoxLayout()
        fila_timer.setSpacing(12)

        self.label_tiempo = QLabel("00:00:00")
        self.label_tiempo.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            font-size: 30px;
            font-weight: 600;
        """)
        fila_timer.addWidget(self.label_tiempo)
        fila_timer.addStretch()

        self.boton_play = QPushButton("▶")
        self.boton_play.setFixedSize(48, 48)
        self.boton_play.setCursor(Qt.PointingHandCursor)
        self.boton_play.clicked.connect(self._on_play_stop)
        self._estilizar_boton_play(False)
        fila_timer.addWidget(self.boton_play)

        layout.addLayout(fila_timer)

        # -------- Separador --------
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"color: {COLOR_BORDE}; background-color: {COLOR_BORDE};")
        linea.setFixedHeight(1)
        layout.addWidget(linea)

        # -------- Scroll del historial --------
        self.scroll_historial = QScrollArea()
        self.scroll_historial.setWidgetResizable(True)
        self.scroll_historial.setFrameShape(QFrame.NoFrame)
        self.scroll_historial.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {COLOR_TARJETA};
                width: 5px;
                border-radius: 2px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #4a5c66;
                border-radius: 2px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLOR_ACENTO};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)

        self.contenedor_historial = QWidget()
        self.contenedor_historial.setStyleSheet(f"background-color: {COLOR_FONDO};")
        self.layout_historial = QVBoxLayout(self.contenedor_historial)
        self.layout_historial.setContentsMargins(0, 0, 0, 0)
        self.layout_historial.setSpacing(4)
        self.layout_historial.addStretch()

        self.scroll_historial.setWidget(self.contenedor_historial)
        layout.addWidget(self.scroll_historial, 1)

    def _armar_selector_etiquetas(self, layout):
        """Panel de selección múltiple de etiquetas."""
        contenedor = QWidget()
        contenedor.setStyleSheet(f"""
            QWidget {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                border-radius: 2px;
            }}
        """)
        layout_interno = QVBoxLayout(contenedor)
        layout_interno.setContentsMargins(8, 6, 8, 6)
        layout_interno.setSpacing(4)

        # Fila con el label + combo para agregar
        fila_agregar = QHBoxLayout()
        fila_agregar.setSpacing(6)

        label = QLabel("Etiquetas:")
        label.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            border: none;
        """)
        fila_agregar.addWidget(label)

        self.combo_etiqueta = QComboBox()
        self.combo_etiqueta.addItem("Agregar etiqueta...", None)
        self.combo_etiqueta.currentIndexChanged.connect(self._on_etiqueta_seleccionada_combo)
        self.combo_etiqueta.setStyleSheet(f"""
            QComboBox {{
                background-color: transparent;
                border: none;
                color: {COLOR_TEXTO};
                padding: 4px;
                font-size: 12px;
                min-width: 200px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLOR_TEXTO_SECUNDARIO};
            }}
            QComboBox QAbstractItemView {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO};
                selection-color: white;
                outline: none;
            }}
        """)
        fila_agregar.addWidget(self.combo_etiqueta, 1)
        layout_interno.addLayout(fila_agregar)

        # Contenedor donde se muestran los chips de etiquetas seleccionadas
        self.chips_container = QWidget()
        self.chips_container.setStyleSheet("background: transparent; border: none;")
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 4, 0, 0)
        self.chips_layout.setSpacing(4)
        self.chips_layout.addStretch()
        self.chips_container.setVisible(False)
        layout_interno.addWidget(self.chips_container)

        layout.addWidget(contenedor)

    def _estilizar_combo(self, combo: QComboBox):
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 12px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QComboBox:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QComboBox:disabled {{
                color: {COLOR_TEXTO_SECUNDARIO};
                background-color: #0a1218;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLOR_TEXTO_SECUNDARIO};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO};
                selection-color: white;
                outline: none;
            }}
        """)

    def _estilizar_boton_play(self, corriendo: bool):
        color = "#e53935" if corriendo else COLOR_ACENTO
        hover = "#c62828" if corriendo else "#0c94dc"
        texto = "■" if corriendo else "▶"
        self.boton_play.setText(texto)
        self.boton_play.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 24px;
                font-size: 16px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """)

    # ================= MANEJO DE MENSAJES =================
    def _mostrar_mensaje(self, texto: str, tipo: str = "error"):
        self.label_mensaje.setText(texto)
        if tipo == "error":
            self.label_mensaje.setStyleSheet(f"""
                background-color: #5a1f1f;
                color: #ffffff;
                border: 1px solid {COLOR_ERROR};
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 3px;
            """)
        else:  # success
            self.label_mensaje.setStyleSheet(f"""
                background-color: #1f4a1f;
                color: #ffffff;
                border: 1px solid {COLOR_EXITO};
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 3px;
            """)
        self.label_mensaje.setVisible(True)
        QTimer.singleShot(4000, lambda: self.label_mensaje.setVisible(False))

    # ================= CARGA DE DATOS =================
    def _lanzar(self, funcion, on_exito, *args, **kwargs):
        worker = ApiWorker(funcion, *args, **kwargs)
        worker.exito.connect(on_exito)
        worker.error.connect(self._on_error_worker)
        self._workers.append(worker)
        worker.start()

    def _on_error_worker(self, mensaje: str):
        self._mostrar_mensaje(mensaje, "error")

    def _cargar_proyectos(self):
        self._lanzar(self.client.listar_proyectos, self._on_proyectos_cargados)

    def _on_proyectos_cargados(self, proyectos):
        self.combo_proyecto.clear()
        self.combo_proyecto.addItem("Aún no hay proyecto", None)
        for p in proyectos or []:
            nombre = p.get("nombre", f"Proyecto {p.get('id')}")
            cliente = p.get("nombre_cliente")
            texto = f"{nombre} · {cliente}" if cliente else nombre
            self.combo_proyecto.addItem(texto, p.get("id"))

    def _on_proyecto_seleccionado(self, index):
        proyecto_id = self.combo_proyecto.itemData(index)

        self.combo_tarea.clear()
        self.combo_tarea.addItem("Buscar tarea", None)

        if proyecto_id is None:
            self.combo_tarea.setEnabled(False)
            return

        self.combo_tarea.setEnabled(True)
        self._lanzar(
            self.client.listar_tareas,
            self._on_tareas_cargadas,
            proyecto_id=proyecto_id,
        )

    def _on_tareas_cargadas(self, tareas):
        self.combo_tarea.clear()
        self.combo_tarea.addItem("Buscar tarea", None)
        for t in tareas or []:
            nombre = t.get("titulo", f"Tarea {t.get('id')}")
            self.combo_tarea.addItem(nombre, t.get("id"))

    def _cargar_etiquetas(self):
        self._lanzar(self.client.listar_etiquetas, self._on_etiquetas_cargadas)

    def _on_etiquetas_cargadas(self, etiquetas):
        self.combo_etiqueta.clear()
        self.combo_etiqueta.addItem("Agregar etiqueta...", None)
        for e in etiquetas or []:
            nombre = e.get("nombre", f"Etiqueta {e.get('id')}")
            self.combo_etiqueta.addItem(nombre, e)

    # ================= ETIQUETAS MÚLTIPLES =================
    def _on_etiqueta_seleccionada_combo(self, index):
        if index <= 0:
            return

        etiqueta = self.combo_etiqueta.itemData(index)
        if not etiqueta:
            return

        # Evitar duplicados
        ids_actuales = [e["id"] for e in self.etiquetas_seleccionadas]
        if etiqueta.get("id") not in ids_actuales:
            self.etiquetas_seleccionadas.append(etiqueta)

        # Resetear combo
        self.combo_etiqueta.blockSignals(True)
        self.combo_etiqueta.setCurrentIndex(0)
        self.combo_etiqueta.blockSignals(False)

        self._renderizar_chips()

    def _quitar_etiqueta(self, etiqueta_id: int):
        self.etiquetas_seleccionadas = [
            e for e in self.etiquetas_seleccionadas if e["id"] != etiqueta_id
        ]
        self._renderizar_chips()

    def _renderizar_chips(self):
        # Limpiar layout anterior
        while self.chips_layout.count() > 1:
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.etiquetas_seleccionadas:
            self.chips_container.setVisible(False)
            return

        self.chips_container.setVisible(True)

        for e in self.etiquetas_seleccionadas:
            chip = QPushButton(f"{e.get('nombre', '')}  ✕")
            chip.setCursor(Qt.PointingHandCursor)
            chip.setStyleSheet(f"""
                QPushButton {{
                    background-color: #24343d;
                    border: 1px solid {COLOR_BORDE};
                    color: #cbd5db;
                    padding: 3px 10px;
                    font-size: 11px;
                    border-radius: 2px;
                }}
                QPushButton:hover {{
                    background-color: #2f3f48;
                    color: {COLOR_ERROR};
                }}
            """)
            chip.clicked.connect(lambda _, eid=e["id"]: self._quitar_etiqueta(eid))
            self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)

    # ================= CREAR TAREA / ETIQUETA =================
    def _abrir_menu_crear(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background-color: {COLOR_ACENTO};
                color: white;
            }}
        """)

        accion_tarea = QAction("+ Nueva Tarea", self)
        accion_tarea.triggered.connect(self._abrir_dialogo_tarea)
        menu.addAction(accion_tarea)

        accion_etiqueta = QAction("+ Nueva Etiqueta", self)
        accion_etiqueta.triggered.connect(self._abrir_dialogo_etiqueta)
        menu.addAction(accion_etiqueta)

        pos = self.boton_agregar.mapToGlobal(
            self.boton_agregar.rect().bottomLeft()
        )
        menu.exec(pos)

    def _abrir_dialogo_tarea(self):
        proyecto_id = self.combo_proyecto.currentData()
        if proyecto_id is None:
            self._mostrar_mensaje("Selecciona un proyecto primero para crear la tarea", "error")
            return

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Nueva Tarea")
        dialogo.setMinimumWidth(380)
        dialogo.setStyleSheet(f"""
            QDialog {{ background-color: {COLOR_FONDO}; }}
            QLabel {{ color: {COLOR_TEXTO}; font-size: 13px; }}
        """)

        form = QFormLayout(dialogo)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        input_titulo = QLineEdit()
        input_titulo.setPlaceholderText("Título de la tarea")
        input_titulo.setStyleSheet(f"""
            QLineEdit {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 10px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
        """)
        form.addRow("Título:", input_titulo)

        combo_prioridad = QComboBox()
        combo_prioridad.addItems(["BAJA", "MEDIA", "ALTA"])
        combo_prioridad.setCurrentText("MEDIA")
        combo_prioridad.setStyleSheet(f"""
            QComboBox {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 10px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO};
            }}
        """)
        form.addRow("Prioridad:", combo_prioridad)

        botones = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        botones.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                padding: 6px 16px;
                border: none;
                border-radius: 2px;
                font-size: 12px;
                min-width: 80px;
            }}
            QPushButton:hover {{ background-color: #0c94dc; }}
        """)
        form.addRow(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        titulo = input_titulo.text().strip()
        if not titulo:
            self._mostrar_mensaje("El título no puede estar vacío", "error")
            return

        prioridad = combo_prioridad.currentText()

        self._lanzar(
            self.client.crear_tarea,
            self._on_tarea_creada,
            titulo=titulo,
            proyecto_id=proyecto_id,
            prioridad=prioridad,
        )

    def _on_tarea_creada(self, tarea):
        self._mostrar_mensaje(f"Tarea '{tarea.get('titulo', '')}' creada", "success")
        self._on_proyecto_seleccionado(self.combo_proyecto.currentIndex())

    def _abrir_dialogo_etiqueta(self):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Nueva Etiqueta")
        dialogo.setMinimumWidth(380)
        dialogo.setStyleSheet(f"""
            QDialog {{ background-color: {COLOR_FONDO}; }}
            QLabel {{ color: {COLOR_TEXTO}; font-size: 13px; }}
        """)

        form = QFormLayout(dialogo)
        form.setContentsMargins(20, 20, 20, 20)
        form.setSpacing(12)

        input_nombre = QLineEdit()
        input_nombre.setPlaceholderText("Nombre de la etiqueta")
        input_nombre.setStyleSheet(f"""
            QLineEdit {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 10px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
        """)
        form.addRow("Nombre:", input_nombre)

        input_color = QLineEdit()
        input_color.setText("#10a5f5")
        input_color.setPlaceholderText("#10a5f5")
        input_color.setStyleSheet(f"""
            QLineEdit {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 10px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
        """)
        form.addRow("Color (hex):", input_color)

        botones = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        botones.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                padding: 6px 16px;
                border: none;
                border-radius: 2px;
                font-size: 12px;
                min-width: 80px;
            }}
            QPushButton:hover {{ background-color: #0c94dc; }}
        """)
        form.addRow(botones)

        if dialogo.exec() != QDialog.Accepted:
            return

        nombre = input_nombre.text().strip()
        if not nombre:
            self._mostrar_mensaje("El nombre no puede estar vacío", "error")
            return

        color = input_color.text().strip() or "#10a5f5"

        self._lanzar(
            self.client.crear_etiqueta,
            self._on_etiqueta_creada,
            nombre=nombre,
            color=color,
        )

    def _on_etiqueta_creada(self, etiqueta):
        self._mostrar_mensaje(f"Etiqueta '{etiqueta.get('nombre', '')}' creada", "success")
        self._cargar_etiquetas()

    # ================= CARGA DEL HISTORIAL =================
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

        # Cargar etiquetas del registro activo
        self.etiquetas_seleccionadas = registro.get("etiquetas") or []
        self._renderizar_chips()

        self.label_tiempo.setText(formatear_duracion(self.segundos_transcurridos))
        self._set_estado_corriendo(True)
        self.reloj.start(1000)

    def _cargar_historial(self):
        hace_21_dias = (date.today() - timedelta(days=21)).isoformat()
        self._lanzar(
            self.client.historial_tiempos,
            self._on_historial_cargado,
            fecha_desde=hace_21_dias,
        )

    def _on_historial_cargado(self, registros):
        while self.layout_historial.count() > 1:
            item = self.layout_historial.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        registros = registros or []

        if not registros:
            vacio = QLabel("No hay entradas registradas.")
            vacio.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; padding: 20px; font-size: 13px;")
            vacio.setAlignment(Qt.AlignCenter)
            self.layout_historial.insertWidget(0, vacio)
            return

        grupos_dia = {}
        for r in registros:
            try:
                fecha = datetime.fromisoformat(r["inicio"]).date()
            except Exception:
                continue
            grupos_dia.setdefault(fecha, []).append(r)

        grupos_semana = {}
        for fecha, regs in grupos_dia.items():
            lunes = lunes_de_semana(fecha)
            grupos_semana.setdefault(lunes, {})[fecha] = regs

        semanas_ordenadas = sorted(grupos_semana.keys(), reverse=True)

        indice = 0
        for lunes in semanas_ordenadas:
            dias = grupos_semana[lunes]

            total_semana = sum(
                r.get("duracion_segundos", 0)
                for regs in dias.values()
                for r in regs
            )

            header_semana = self._crear_header_semana(lunes, total_semana)
            self.layout_historial.insertWidget(indice, header_semana)
            indice += 1

            fechas_ordenadas = sorted(dias.keys(), reverse=True)
            for fecha in fechas_ordenadas:
                regs = dias[fecha]
                total_dia = sum(r.get("duracion_segundos", 0) for r in regs)

                header_dia = self._crear_header_dia(fecha, total_dia)
                self.layout_historial.insertWidget(indice, header_dia)
                indice += 1

                for r in regs:
                    tarjeta = self._crear_tarjeta_registro(r)
                    self.layout_historial.insertWidget(indice, tarjeta)
                    indice += 1

    def _crear_header_semana(self, lunes: date, total_seg: int) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {COLOR_HEADER_SEMANA};
            border-radius: 2px;
            border: 1px solid {COLOR_BORDE};
        """)
        header.setFixedHeight(36)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 12, 0)

        label = QLabel(etiqueta_semana(lunes))
        label.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: none;
        """)
        layout.addWidget(label)
        layout.addStretch()

        label_total = QLabel(f"Total semanal: {formatear_duracion(total_seg)}")
        label_total.setStyleSheet(f"""
            color: {COLOR_ACENTO};
            font-size: 12px;
            font-weight: 600;
            border: none;
        """)
        layout.addWidget(label_total)

        return header

    def _crear_header_dia(self, fecha: date, total_seg: int) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {COLOR_HEADER_DIA};
            border-radius: 2px;
        """)
        header.setFixedHeight(30)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 12, 0)

        label = QLabel(etiqueta_dia(fecha))
        label.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            border: none;
        """)
        layout.addWidget(label)
        layout.addStretch()

        label_total = QLabel(f"Total: {formatear_duracion(total_seg)}")
        label_total.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            font-size: 12px;
            font-weight: 600;
            border: none;
        """)
        layout.addWidget(label_total)

        return header

    def _crear_tarjeta_registro(self, registro: dict) -> QWidget:
        tarjeta = QWidget()
        tarjeta.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_TARJETA};
                border-radius: 2px;
                border: 1px solid {COLOR_BORDE};
            }}
        """)
        tarjeta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout_principal = QVBoxLayout(tarjeta)
        layout_principal.setContentsMargins(12, 8, 12, 8)
        layout_principal.setSpacing(3)

        # -------- Fila 1: descripción + duración + botones --------
        fila1 = QHBoxLayout()
        fila1.setSpacing(8)

        descripcion = registro.get("descripcion") or "(sin descripción)"
        label_desc = QLabel(descripcion)
        label_desc.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            font-size: 13px;
            font-weight: 500;
            border: none;
        """)
        label_desc.setWordWrap(True)
        fila1.addWidget(label_desc, 1)

        duracion = formatear_duracion(registro.get("duracion_segundos", 0))
        label_duracion = QLabel(duracion)
        label_duracion.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            font-size: 13px;
            font-weight: 600;
            border: none;
        """)
        fila1.addWidget(label_duracion)

        # Botón ▶ (reanudar)
        btn_play = QPushButton("▶")
        btn_play.setFixedSize(26, 26)
        btn_play.setCursor(Qt.PointingHandCursor)
        btn_play.setToolTip("Reanudar esta actividad")
        btn_play.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_ACENTO};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: white; }}
        """)
        btn_play.clicked.connect(lambda _, r=registro: self._reanudar_registro(r))
        fila1.addWidget(btn_play)

        # Botón ✕ (eliminar)
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(26, 26)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Eliminar esta actividad")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO_SECUNDARIO};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: {COLOR_ERROR}; }}
        """)
        btn_del.clicked.connect(lambda _, rid=registro.get("id"): self._eliminar_registro(rid))
        fila1.addWidget(btn_del)

        layout_principal.addLayout(fila1)

        # -------- Fila 2: proyecto · tarea | hora inicio - fin --------
        fila2 = QHBoxLayout()
        fila2.setSpacing(8)

        proyecto = registro.get("nombre_proyecto") or "Sin proyecto"
        tarea = registro.get("titulo_tarea") or ""
        color_proyecto = registro.get("color_proyecto") or COLOR_PUNTO_VERDE

        label_proyecto = QLabel(f"● {proyecto}" + (f" - {tarea}" if tarea else ""))
        label_proyecto.setStyleSheet(f"""
            color: {color_proyecto};
            font-size: 11px;
            border: none;
        """)
        fila2.addWidget(label_proyecto, 1)

        try:
            inicio_dt = datetime.fromisoformat(registro["inicio"])
            fin_str = registro.get("fin")
            hora_texto = inicio_dt.strftime("%I:%M %p")
            if fin_str:
                fin_dt = datetime.fromisoformat(fin_str)
                hora_texto += f" - {fin_dt.strftime('%I:%M %p')}"
        except Exception:
            hora_texto = ""

        label_hora = QLabel(hora_texto)
        label_hora.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            border: none;
        """)
        fila2.addWidget(label_hora)

        layout_principal.addLayout(fila2)

        # -------- Fila 3: etiquetas --------
        etiquetas = registro.get("etiquetas") or []
        if etiquetas:
            fila3 = QHBoxLayout()
            fila3.setSpacing(4)
            fila3.setContentsMargins(0, 3, 0, 0)
            for e in etiquetas:
                nombre = e.get("nombre", "")
                chip = QLabel(nombre)
                chip.setStyleSheet(f"""
                    background-color: #24343d;
                    border: 1px solid {COLOR_BORDE};
                    color: #cbd5db;
                    padding: 2px 8px;
                    font-size: 10px;
                    border-radius: 2px;
                """)
                fila3.addWidget(chip)
            fila3.addStretch()
            layout_principal.addLayout(fila3)

        return tarjeta

    # ================= REANUDAR / ELIMINAR =================
    def _reanudar_registro(self, registro: dict):
        """Precarga los datos del registro y arranca el temporizador."""
        if self.registro_activo:
            self._mostrar_mensaje("Ya tienes un temporizador activo. Deténlo primero.", "error")
            return

        self.descripcion_input.setText(registro.get("descripcion") or "")

        proyecto_id = registro.get("proyecto_id")
        if proyecto_id is not None:
            idx = self.combo_proyecto.findData(proyecto_id)
            if idx >= 0:
                self.combo_proyecto.setCurrentIndex(idx)

        tarea_id = registro.get("tarea_id")
        self._tarea_pendiente_id = tarea_id

        self.etiquetas_seleccionadas = registro.get("etiquetas") or []
        self._renderizar_chips()

        QTimer.singleShot(400, self._iniciar)

    def _eliminar_registro(self, registro_id: int):
        if not registro_id:
            return

        respuesta = QMessageBox.question(
            self,
            "Eliminar actividad",
            "¿Estás seguro de eliminar esta actividad? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if respuesta != QMessageBox.Yes:
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
        self.label_tiempo.setText(formatear_duracion(self.segundos_transcurridos))

    def _set_estado_corriendo(self, corriendo: bool):
        self._estilizar_boton_play(corriendo)
        if corriendo:
            self.descripcion_input.setEnabled(False)
            self.combo_proyecto.setEnabled(False)
            self.combo_tarea.setEnabled(False)
            self.combo_etiqueta.setEnabled(False)
            self.boton_agregar.setEnabled(False)
        else:
            self.descripcion_input.setEnabled(True)
            self.combo_proyecto.setEnabled(True)
            if self.combo_proyecto.currentData() is not None:
                self.combo_tarea.setEnabled(True)
            self.combo_etiqueta.setEnabled(True)
            self.boton_agregar.setEnabled(True)

    def _on_play_stop(self):
        if self.registro_activo:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        if self.registro_activo:
            return

        # Validación de descripción
        descripcion = self.descripcion_input.text().strip()
        if not descripcion:
            self._mostrar_mensaje("Escribe en qué estás trabajando antes de iniciar", "error")
            return

        # Validación de proyecto
        proyecto_id = self.combo_proyecto.currentData()
        if proyecto_id is None:
            self._mostrar_mensaje("Selecciona un proyecto antes de iniciar", "error")
            return

        # Validación de tarea
        tarea_id = self.combo_tarea.currentData()
        if tarea_id is None:
            self._mostrar_mensaje("Selecciona una tarea antes de iniciar", "error")
            return

        # Validación de etiquetas
        if not self.etiquetas_seleccionadas:
            self._mostrar_mensaje("Agrega al menos una etiqueta antes de iniciar", "error")
            return

        # Aplicar tarea pendiente (si venía de reanudar)
        if hasattr(self, "_tarea_pendiente_id") and self._tarea_pendiente_id is not None:
            idx = self.combo_tarea.findData(self._tarea_pendiente_id)
            if idx >= 0:
                self.combo_tarea.setCurrentIndex(idx)
                tarea_id = self._tarea_pendiente_id
            self._tarea_pendiente_id = None

        etiquetas_ids = [e["id"] for e in self.etiquetas_seleccionadas]

        self._lanzar(
            self.client.iniciar_temporizador,
            self._on_iniciado,
            proyecto_id=proyecto_id,
            descripcion=descripcion,
            tarea_id=tarea_id,
            etiquetas_ids=etiquetas_ids,
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
        self.etiquetas_seleccionadas = []
        self._renderizar_chips()
        self.combo_tarea.setCurrentIndex(0)
        self._cargar_historial()