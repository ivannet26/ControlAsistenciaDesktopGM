# app/ui/dialogs/modal_entrada.py
import os

from PySide6.QtCore import Qt, QDate, QTime, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTextEdit, QDateEdit, QTimeEdit, QWidget,
    QMessageBox, QAbstractSpinBox, QCalendarWidget, QToolButton,
)

from app.styles.colors import (
    COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT, COLOR_INPUT_BG,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_ERROR, COLOR_FONDO,
    RADIO_INPUT, RADIO_BOTON, RADIO_CHIP,
)
from app.ui.dialogs.nueva_tarea import DialogoNuevaTarea
from app.ui.dialogs.nueva_etiqueta import DialogoNuevaEtiqueta
from app.ui.dialogs.nuevo_proyecto import DialogoNuevoProyecto


# ---- Medidas compactas ----
ALTO_INPUT = 34
ALTO_TEXTO = 60
ALTO_BOTON = 36
ALTO_CHIP = 20
ANCHO_MODAL = 460
PADDING_LATERAL = 20
ANCHO_BADGE_ESTIMADO = 44
ANCHO_INTERNO = ANCHO_MODAL - (PADDING_LATERAL * 2)   # 420
ALTO_MINIMO_MODAL = 400


class ModalEntrada(QDialog):
    """Modal de entrada de tiempo, compacto y de tamaño fijo."""

    datos_actualizados = Signal()

    def __init__(
        self,
        client,
        padre=None,
        datos_iniciales=None,
        proyectos=None,
        etiquetas=None,
        tareas_por_proyecto=None,
    ):
        super().__init__(padre)
        self.client = client
        self.datos_iniciales = datos_iniciales or {}
        self.resultado = None
        self._etiquetas_seleccionadas = []

        self._proyectos = proyectos or []
        self._etiquetas = etiquetas or []
        self._tareas_por_proyecto = tareas_por_proyecto or {}

        self._cal_popup = None
        self._alto_cache = ALTO_MINIMO_MODAL

        self.setWindowTitle("Nueva Entrada de tiempo")
        self.setModal(True)

        # ✅ Quitar barra nativa de Windows + eliminar borde fantasma
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._armar_ui()
        self._poblar_proyectos()
        self._poblar_etiquetas()
        self._aplicar_iniciales()

        # Se calcula UNA sola vez, con la fila de chips ya reservada
        self._recalcular_y_aplicar()

    # ============================================================
    # Tamaño: calculado una vez, luego solo se reaplica
    # ============================================================
    def showEvent(self, event):
        super().showEvent(event)
        self._aplicar_tamano()
        # 🎯 Centrar respecto al padre
        if self.parent():
            p_geo = self.parent().geometry()
            self.move(
                p_geo.center().x() - self.width() // 2,
                p_geo.center().y() - self.height() // 2,
            )

    def _recalcular_y_aplicar(self):
        """Calcula el alto mínimo real del layout. Llamar solo al inicio."""
        self.layout().activate()
        alto = self.layout().minimumSize().height()
        self._alto_cache = max(alto, ALTO_MINIMO_MODAL)
        self._aplicar_tamano()

    def _aplicar_tamano(self):
        """Aplica el alto cacheado. Seguro después de QMessageBox."""
        self.setFixedSize(ANCHO_MODAL, self._alto_cache)

    # ============================================================
    # UI
    # ============================================================
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------- Barra custom oscura ----------
        self.title_bar = CustomTitleBar(
            self,
            "Nueva Entrada de tiempo",
            mostrar_maximizar=False,
            mostrar_minimizar=False,
        )
        root.addWidget(self.title_bar)

        # ---------- Contenedor con fondo oscuro ----------
        contenido = QWidget()
        contenido.setObjectName("contenidoDialogo")
        contenido.setAttribute(Qt.WA_StyledBackground, True)
        contenido.setStyleSheet(
            f"QWidget#contenidoDialogo {{ background-color: {COLOR_PANEL}; }}"
        )
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(PADDING_LATERAL, 14, PADDING_LATERAL, 16)
        layout.setSpacing(10)

        # Separador inicial
        linea_top = QFrame()
        linea_top.setFrameShape(QFrame.HLine)
        linea_top.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        linea_top.setFixedHeight(1)
        layout.addWidget(linea_top)

        # ---------- Fecha + icono calendario ----------
        fila_fecha = QHBoxLayout()
        fila_fecha.setSpacing(6)

        self.fecha_edit = QDateEdit()
        self.fecha_edit.setCalendarPopup(False)
        self.fecha_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.fecha_edit.setDate(QDate.currentDate())
        self.fecha_edit.setDisplayFormat("dd/MM/yyyy")
        self.fecha_edit.setFixedHeight(ALTO_INPUT)
        self.fecha_edit.setStyleSheet(self._qss_fecha_hora())
        fila_fecha.addWidget(self.fecha_edit, 1)

        self.btn_calendario = QToolButton()
        self.btn_calendario.setFixedSize(ALTO_INPUT, ALTO_INPUT)
        self.btn_calendario.setCursor(Qt.PointingHandCursor)
        self.btn_calendario.setIcon(
            self._crear_icono_calendario(16, COLOR_TEXTO_SECUNDARIO)
        )
        self.btn_calendario.setIconSize(self.btn_calendario.size() / 2)
        self.btn_calendario.clicked.connect(self._abrir_calendario)
        self.btn_calendario.setStyleSheet(f"""
            QToolButton {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
            }}
            QToolButton:hover {{
                border: 1px solid {COLOR_ACENTO};
                background-color: rgba(33, 150, 243, 0.08);
            }}
        """)
        fila_fecha.addWidget(self.btn_calendario)
        layout.addLayout(fila_fecha)

        # ---------- Horas ----------
        fila_horas = QHBoxLayout()
        fila_horas.setSpacing(6)

        ahora = QTime.currentTime()

        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.hora_inicio.setTime(ahora)
        self.hora_inicio.setDisplayFormat("HH:mm")
        self.hora_inicio.setFixedHeight(ALTO_INPUT)
        self.hora_inicio.setStyleSheet(self._qss_fecha_hora())
        self.hora_inicio.timeChanged.connect(self._actualizar_duracion)
        fila_horas.addWidget(self.hora_inicio, 1)

        sep = QLabel("→")
        sep.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; background: transparent;"
            f"border: none; font-size: 13px;"
        )
        sep.setFixedWidth(14)
        sep.setAlignment(Qt.AlignCenter)
        fila_horas.addWidget(sep)

        self.hora_fin = QTimeEdit()
        self.hora_fin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.hora_fin.setTime(ahora)
        self.hora_fin.setDisplayFormat("HH:mm")
        self.hora_fin.setFixedHeight(ALTO_INPUT)
        self.hora_fin.setStyleSheet(self._qss_fecha_hora())
        self.hora_fin.timeChanged.connect(self._actualizar_duracion)
        fila_horas.addWidget(self.hora_fin, 1)

        self.label_duracion = QLabel("00:00:00")
        self.label_duracion.setFixedHeight(ALTO_INPUT)
        self.label_duracion.setFixedWidth(96)
        self.label_duracion.setAlignment(Qt.AlignCenter)
        self.label_duracion.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        fila_horas.addWidget(self.label_duracion)
        layout.addLayout(fila_horas)

        # ---------- Descripción ----------
        self.descripcion = QTextEdit()
        self.descripcion.setPlaceholderText("¿En qué has trabajado?")
        self.descripcion.setFixedHeight(ALTO_TEXTO)
        self.descripcion.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 6px 10px;
                font-size: 12px;
            }}
            QTextEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
        """)
        layout.addWidget(self.descripcion)

        # ---------- Proyecto ----------
        fila_proy = QHBoxLayout()
        fila_proy.setSpacing(6)

        self.combo_proyecto = QComboBox()
        self.combo_proyecto.addItem("Buscar Proyecto o Cliente", None)
        self.combo_proyecto.setFixedHeight(ALTO_INPUT)
        self.combo_proyecto.setStyleSheet(self._qss_combo())
        self.combo_proyecto.currentIndexChanged.connect(self._on_proyecto_change)
        fila_proy.addWidget(self.combo_proyecto, 1)

        btn_add_proy = self._boton_mas()
        btn_add_proy.clicked.connect(self._on_nuevo_proyecto)
        fila_proy.addWidget(btn_add_proy)
        layout.addLayout(fila_proy)

        # ---------- Tarea ----------
        fila_tarea = QHBoxLayout()
        fila_tarea.setSpacing(6)

        self.combo_tarea = QComboBox()
        self.combo_tarea.addItem("Buscar Tarea", None)
        self.combo_tarea.setFixedHeight(ALTO_INPUT)
        self.combo_tarea.setStyleSheet(self._qss_combo())
        self.combo_tarea.setEnabled(False)
        fila_tarea.addWidget(self.combo_tarea, 1)

        btn_add_tarea = self._boton_mas()
        btn_add_tarea.clicked.connect(self._on_nueva_tarea)
        fila_tarea.addWidget(btn_add_tarea)
        layout.addLayout(fila_tarea)

        # ---------- Etiqueta ----------
        fila_etiq = QHBoxLayout()
        fila_etiq.setSpacing(6)

        self.combo_etiqueta = QComboBox()
        self.combo_etiqueta.addItem("Buscar etiqueta", None)
        self.combo_etiqueta.setFixedHeight(ALTO_INPUT)
        self.combo_etiqueta.setStyleSheet(self._qss_combo())
        self.combo_etiqueta.currentIndexChanged.connect(self._on_etiqueta_change)
        fila_etiq.addWidget(self.combo_etiqueta, 1)

        btn_add_etiq = self._boton_mas()
        btn_add_etiq.clicked.connect(self._on_nueva_etiqueta)
        fila_etiq.addWidget(btn_add_etiq)
        layout.addLayout(fila_etiq)

        # ---------- Chips (fila SIEMPRE reservada) ----------
        self.chips_container = QWidget()
        self.chips_container.setFixedSize(ANCHO_INTERNO, ALTO_CHIP)
        self.chips_container.setStyleSheet("background: transparent; border: none;")
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(4)
        self.chips_layout.addStretch()

        # Aunque esté oculto, sigue ocupando su lugar en el layout
        sp = self.chips_container.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.chips_container.setSizePolicy(sp)

        self.chips_container.setVisible(False)
        layout.addWidget(self.chips_container)

        # ---------- Separador ----------
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        linea.setFixedHeight(1)
        layout.addWidget(linea)

        # ---------- Botones ----------
        fila_btn = QHBoxLayout()
        fila_btn.setSpacing(8)
        fila_btn.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setFixedHeight(ALTO_BOTON)
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet(self._qss_btn_secundario())
        fila_btn.addWidget(btn_cancelar)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setFixedHeight(ALTO_BOTON)
        btn_guardar.clicked.connect(self._on_guardar)
        btn_guardar.setStyleSheet(self._qss_btn_primario())
        fila_btn.addWidget(btn_guardar)

        layout.addLayout(fila_btn)

        root.addWidget(contenido)

    # ============================================================
    # Icono de calendario
    # ============================================================
    def _crear_icono_calendario(self, size=16, color="#8ea0af"):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidthF(1.4)
        painter.setPen(pen)

        painter.drawRect(2, 3, size - 5, size - 6)
        painter.drawLine(2, 6, size - 3, 6)
        painter.drawLine(5, 1, 5, 4)
        painter.drawLine(size - 6, 1, size - 6, 4)

        painter.end()
        return QIcon(pixmap)

    # ============================================================
    # Popup del calendario
    # ============================================================
    def _abrir_calendario(self):
        if self._cal_popup is None:
            self._cal_popup = QCalendarWidget(self)
            self._cal_popup.setWindowFlags(Qt.Popup)
            self._cal_popup.setGridVisible(True)
            self._cal_popup.clicked.connect(self._on_fecha_elegida)

        self._cal_popup.setSelectedDate(self.fecha_edit.date())
        pos = self.btn_calendario.mapToGlobal(
            self.btn_calendario.rect().bottomLeft()
        )
        self._cal_popup.move(pos)
        self._cal_popup.show()

    def _on_fecha_elegida(self, qdate):
        self.fecha_edit.setDate(qdate)
        if self._cal_popup:
            self._cal_popup.hide()

    # ============================================================
    # QSS helpers
    # ============================================================
    def _qss_fecha_hora(self):
        return f"""
            QDateEdit, QTimeEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 10px;
                font-size: 12px;
            }}
            QDateEdit:focus, QTimeEdit:focus {{
                border: 1px solid {COLOR_ACENTO};
            }}
            QDateEdit::up-button, QDateEdit::down-button,
            QTimeEdit::up-button, QTimeEdit::down-button {{
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }}
            QDateEdit::drop-down, QTimeEdit::drop-down {{
                width: 0px;
                border: none;
                background: transparent;
            }}
        """

    def _qss_combo(self):
        return f"""
            QComboBox {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 10px;
                font-size: 12px;
                outline: none;
                min-width: 100px;
            }}
            QComboBox:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QComboBox:disabled {{
                color: {COLOR_TEXTO_TERCIARIO};
                background-color: {COLOR_FONDO};
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 0px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO};
                selection-color: white;
                outline: none;
                padding: 4px;
            }}
        """

    def _boton_mas(self):
        btn = QPushButton("+")
        btn.setFixedSize(ALTO_INPUT, ALTO_INPUT)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO_SECUNDARIO};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                font-size: 15px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {COLOR_ACENTO};
                border: 1px solid {COLOR_ACENTO};
                background-color: rgba(33, 150, 243, 0.08);
            }}
        """)
        return btn

    def _qss_btn_primario(self):
        return f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                border: none;
                border-radius: {RADIO_BOTON}px;
                padding: 0 20px;
                font-size: 12px;
                font-weight: 600;
                min-width: 96px;
            }}
            QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
            QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
        """

    def _qss_btn_secundario(self):
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_BOTON}px;
                padding: 0 18px;
                font-size: 12px;
                min-width: 88px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_ACENTO};
            }}
        """

    def _qss_chip(self):
        return f"""
            QPushButton {{
                background-color: rgba(33, 150, 243, 0.15);
                border: 1px solid rgba(33, 150, 243, 0.35);
                color: #90caf9;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 500;
                border-radius: {RADIO_CHIP}px;
            }}
            QPushButton:hover {{
                background-color: rgba(229, 57, 53, 0.18);
                border: 1px solid {COLOR_ERROR};
                color: {COLOR_ERROR};
            }}
        """

    def _qss_badge(self):
        return f"""
            QPushButton {{
                background-color: rgba(33, 150, 243, 0.25);
                border: 1px solid rgba(33, 150, 243, 0.55);
                color: #bbdefb;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
                border-radius: {RADIO_CHIP}px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACENTO};
                border: 1px solid {COLOR_ACENTO};
                color: white;
            }}
        """

    # ============================================================
    # Poblado
    # ============================================================
    def _poblar_proyectos(self):
        self.combo_proyecto.blockSignals(True)
        self.combo_proyecto.clear()
        self.combo_proyecto.addItem("Buscar Proyecto o Cliente", None)
        for p in self._proyectos:
            nombre = p.get("nombre", f"Proyecto {p.get('id')}")
            cliente = p.get("nombre_cliente")
            texto = f"{nombre} · {cliente}" if cliente else nombre
            self.combo_proyecto.addItem(texto, p.get("id"))
        self.combo_proyecto.blockSignals(False)

    def _poblar_etiquetas(self):
        self.combo_etiqueta.blockSignals(True)
        self.combo_etiqueta.clear()
        self.combo_etiqueta.addItem("Buscar etiqueta", None)
        for e in self._etiquetas:
            self.combo_etiqueta.addItem(
                e.get("nombre", f"Etiqueta {e.get('id')}"), e
            )
        self.combo_etiqueta.blockSignals(False)

    # ============================================================
    # Interacciones
    # ============================================================
    def _on_proyecto_change(self, index):
        """Rellena el combo de tareas desde el CACHE (sin HTTP)."""
        proyecto_id = self.combo_proyecto.itemData(index)
        self.combo_tarea.clear()
        self.combo_tarea.addItem("Buscar Tarea", None)
        if proyecto_id is None:
            self.combo_tarea.setEnabled(False)
            return
        self.combo_tarea.setEnabled(True)
        tareas = self._tareas_por_proyecto.get(proyecto_id, [])
        for t in tareas:
            self.combo_tarea.addItem(
                t.get("titulo", f"Tarea {t.get('id')}"), t.get("id")
            )

    def _on_etiqueta_change(self, index):
        if index <= 0:
            return
        etiqueta = self.combo_etiqueta.itemData(index)
        if not etiqueta:
            return
        ids = [e["id"] for e in self._etiquetas_seleccionadas]
        if etiqueta["id"] not in ids:
            self._etiquetas_seleccionadas.append(etiqueta)
        self.combo_etiqueta.blockSignals(True)
        self.combo_etiqueta.setCurrentIndex(0)
        self.combo_etiqueta.blockSignals(False)
        self._renderizar_chips()

    # ============================================================
    # CHIPS con contador "+N"
    # ============================================================
    def _renderizar_chips(self):
        # 1) Limpiar
        while self.chips_layout.count() > 1:
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._etiquetas_seleccionadas:
            self.chips_container.setVisible(False)
            return

        self.chips_container.setVisible(True)

        # 2) Crear TODOS los chips para medir
        chips = []
        for e in self._etiquetas_seleccionadas:
            chip = QPushButton(f"{e.get('nombre', '')} ✕")
            chip.setFixedHeight(ALTO_CHIP)
            chip.setCursor(Qt.PointingHandCursor)
            chip.setStyleSheet(self._qss_chip())
            chip.clicked.connect(
                lambda _, eid=e["id"]: self._quitar_etiqueta(eid)
            )
            chip.ensurePolished()
            chip.adjustSize()
            chips.append((chip, e))

        spacing = self.chips_layout.spacing()

        # 3) ¿Cuántos caben sin badge?
        visibles = 0
        ancho = 0
        for chip, _ in chips:
            w = chip.width() + spacing
            if ancho + w > ANCHO_INTERNO:
                break
            ancho += w
            visibles += 1

        # 4) Si no caben todos → reservar espacio para el badge
        if visibles < len(chips):
            visibles = 0
            ancho = 0
            limite = ANCHO_INTERNO - ANCHO_BADGE_ESTIMADO - spacing
            for chip, _ in chips:
                w = chip.width() + spacing
                if ancho + w > limite:
                    break
                ancho += w
                visibles += 1

        # 5) Añadir visibles
        for i in range(visibles):
            chip, _ = chips[i]
            self.chips_layout.insertWidget(
                self.chips_layout.count() - 1, chip
            )

        # 6) Eliminar los no usados
        for i in range(visibles, len(chips)):
            chip, _ = chips[i]
            chip.deleteLater()

        # 7) Badge "+N"
        ocultas = len(chips) - visibles
        if ocultas > 0:
            badge = QPushButton(f"+{ocultas}")
            badge.setFixedHeight(ALTO_CHIP)
            badge.setCursor(Qt.PointingHandCursor)
            badge.setStyleSheet(self._qss_badge())

            etiquetas_ocultas = [e for _, e in chips[visibles:]]
            nombres = "\n".join(
                f"• {e.get('nombre', '')}" for e in etiquetas_ocultas
            )
            badge.setToolTip(f"Etiquetas ocultas:\n{nombres}")
            badge.clicked.connect(
                lambda: self._mostrar_etiquetas_ocultas(etiquetas_ocultas)
            )
            self.chips_layout.insertWidget(
                self.chips_layout.count() - 1, badge
            )

    def _mostrar_etiquetas_ocultas(self, etiquetas):
        nombres = "\n".join(f"• {e.get('nombre', '')}" for e in etiquetas)
        QMessageBox.information(
            self,
            f"{len(etiquetas)} etiquetas ocultas",
            nombres,
        )
        QTimer.singleShot(0, self._aplicar_tamano)

    def _quitar_etiqueta(self, etiqueta_id):
        self._etiquetas_seleccionadas = [
            e for e in self._etiquetas_seleccionadas
            if e["id"] != etiqueta_id
        ]
        self._renderizar_chips()

    # ============================================================
    # Crear proyecto / tarea / etiqueta
    # ============================================================
    def _on_nuevo_proyecto(self):
        dlg = DialogoNuevoProyecto(self)
        if dlg.exec() != QDialog.Accepted:
            QTimer.singleShot(0, self._aplicar_tamano)
            return
        nombre, descripcion, color = dlg.datos()
        if not nombre:
            return

        try:
            nuevo = self.client.crear_proyecto(
                nombre=nombre,
                descripcion=descripcion or None,
                color=color,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            QTimer.singleShot(0, self._aplicar_tamano)
            return

        if nuevo:
            self._proyectos.append(nuevo)
            self._poblar_proyectos()
            idx = self.combo_proyecto.findData(nuevo.get("id"))
            if idx >= 0:
                self.combo_proyecto.setCurrentIndex(idx)

        self.datos_actualizados.emit()
        QTimer.singleShot(0, self._aplicar_tamano)

    def _on_nueva_tarea(self):
        proyecto_id = self.combo_proyecto.currentData()
        if proyecto_id is None:
            QMessageBox.warning(self, "Falta proyecto",
                                "Selecciona un proyecto primero.")
            QTimer.singleShot(0, self._aplicar_tamano)
            return

        dlg = DialogoNuevaTarea(self)
        if dlg.exec() != QDialog.Accepted:
            QTimer.singleShot(0, self._aplicar_tamano)
            return
        titulo, prioridad = dlg.datos()
        if not titulo:
            return

        try:
            nueva = self.client.crear_tarea(
                titulo=titulo,
                proyecto_id=proyecto_id,
                prioridad=prioridad,
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            QTimer.singleShot(0, self._aplicar_tamano)
            return

        if nueva:
            self._tareas_por_proyecto.setdefault(proyecto_id, []).append(nueva)
            self._on_proyecto_change(self.combo_proyecto.currentIndex())
            idx = self.combo_tarea.findData(nueva.get("id"))
            if idx >= 0:
                self.combo_tarea.setCurrentIndex(idx)

        self.datos_actualizados.emit()
        QTimer.singleShot(0, self._aplicar_tamano)

    def _on_nueva_etiqueta(self):
        dlg = DialogoNuevaEtiqueta(self)
        if dlg.exec() != QDialog.Accepted:
            QTimer.singleShot(0, self._aplicar_tamano)
            return
        nombre, color = dlg.datos()
        if not nombre:
            return
        try:
            nueva = self.client.crear_etiqueta(nombre=nombre, color=color)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            QTimer.singleShot(0, self._aplicar_tamano)
            return
        if nueva:
            self._etiquetas.append(nueva)
            self._poblar_etiquetas()
        self.datos_actualizados.emit()
        QTimer.singleShot(0, self._aplicar_tamano)

    # ============================================================
    # Duración + iniciales
    # ============================================================
    def _actualizar_duracion(self):
        i = self.hora_inicio.time()
        f = self.hora_fin.time()
        seg_i = i.hour() * 3600 + i.minute() * 60
        seg_f = f.hour() * 3600 + f.minute() * 60
        diff = max(0, seg_f - seg_i)
        h, r = divmod(diff, 3600)
        m, s = divmod(r, 60)
        self.label_duracion.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _aplicar_iniciales(self):
        if not self.datos_iniciales:
            self._actualizar_duracion()
            return
        desc = self.datos_iniciales.get("descripcion")
        if desc:
            self.descripcion.setPlainText(desc)
        proy_id = self.datos_iniciales.get("proyecto_id")
        if proy_id is not None:
            idx = self.combo_proyecto.findData(proy_id)
            if idx >= 0:
                self.combo_proyecto.setCurrentIndex(idx)
        tarea_id = self.datos_iniciales.get("tarea_id")
        if tarea_id is not None:
            idx = self.combo_tarea.findData(tarea_id)
            if idx >= 0:
                self.combo_tarea.setCurrentIndex(idx)
        etqs = self.datos_iniciales.get("etiquetas") or []
        self._etiquetas_seleccionadas = list(etqs)
        self._renderizar_chips()
        self._actualizar_duracion()

    # ============================================================
    # Guardar
    # ============================================================
    def _on_guardar(self):
        descripcion = self.descripcion.toPlainText().strip()
        if not descripcion:
            QMessageBox.warning(self, "Falta descripción",
                                "Escribe en qué has trabajado.")
            QTimer.singleShot(0, self._aplicar_tamano)
            return

        proyecto_id = self.combo_proyecto.currentData()
        if proyecto_id is None:
            QMessageBox.warning(self, "Falta proyecto",
                                "Selecciona un proyecto.")
            QTimer.singleShot(0, self._aplicar_tamano)
            return

        color_proyecto = "#10a878"
        for p in self._proyectos:
            if p.get("id") == proyecto_id:
                color_proyecto = p.get("color") or "#10a878"
                break

        self.resultado = {
            "descripcion": descripcion,
            "proyecto_id": proyecto_id,
            "proyecto_nombre": self.combo_proyecto.currentText(),
            "color_proyecto": color_proyecto,
            "tarea_id": self.combo_tarea.currentData(),
            "etiquetas_ids": [e["id"] for e in self._etiquetas_seleccionadas],
            "etiquetas": list(self._etiquetas_seleccionadas),
        }
        self.accept()