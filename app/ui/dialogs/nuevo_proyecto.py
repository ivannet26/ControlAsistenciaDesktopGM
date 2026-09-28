# app/ui/dialogs/nuevo_proyecto.py
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QColorDialog, QWidget,
)

from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT, COLOR_INPUT_BG,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    RADIO_INPUT,
)


ANCHO_DIALOGO = 380
ALTO_INPUT = 34
ALTO_BOTON = 28
COLOR_POR_DEFECTO = "#10a878"


class DialogoNuevoProyecto(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Proyecto")
        self.setModal(True)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._color_actual = COLOR_POR_DEFECTO

        self._armar_ui()
        self._ajustar_altura()

    def showEvent(self, event):
        super().showEvent(event)
        self._ajustar_altura()
        if self.parent():
            p_geo = self.parent().geometry()
            self.move(
                p_geo.center().x() - self.width() // 2,
                p_geo.center().y() - self.height() // 2,
            )

    def _ajustar_altura(self):
        self.layout().invalidate()
        self.layout().activate()
        self.setFixedSize(ANCHO_DIALOGO, max(self.layout().sizeHint().height(), 180))

    # ============================================================
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(
            self, "Crear Proyecto",
            mostrar_maximizar=False,
            mostrar_minimizar=False,
        )
        root.addWidget(self.title_bar)

        contenido = QWidget()
        contenido.setObjectName("contenidoDialogo")
        contenido.setAttribute(Qt.WA_StyledBackground, True)
        contenido.setStyleSheet(
            f"QWidget#contenidoDialogo {{ background-color: {COLOR_PANEL}; }}"
        )
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(0, 0, 0, 0)
        contenido_layout.setSpacing(0)

        # ---------- Contenido ----------
        cont = QVBoxLayout()
        cont.setContentsMargins(18, 14, 18, 18)
        cont.setSpacing(6)

        lbl1 = QLabel("Nombre del proyecto")
        lbl1.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px; border: none; background: transparent;"
        )
        cont.addWidget(lbl1)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del proyecto")
        self.input_nombre.setFixedHeight(ALTO_INPUT)
        self.input_nombre.setStyleSheet(self._qss_input())
        cont.addWidget(self.input_nombre)

        lbl2 = QLabel("Descripción (opcional)")
        lbl2.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px; border: none; background: transparent; margin-top: 6px;"
        )
        cont.addWidget(lbl2)

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Breve descripción")
        self.input_desc.setFixedHeight(ALTO_INPUT)
        self.input_desc.setStyleSheet(self._qss_input())
        cont.addWidget(self.input_desc)

        lbl3 = QLabel("Color del proyecto")
        lbl3.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px; border: none; background: transparent; margin-top: 6px;"
        )
        cont.addWidget(lbl3)

        fila_color = QHBoxLayout()
        fila_color.setSpacing(8)

        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(ALTO_INPUT)
        self.btn_color.setMinimumWidth(160)
        self.btn_color.setCursor(Qt.PointingHandCursor)
        self.btn_color.clicked.connect(self._abrir_color_picker)
        fila_color.addWidget(self.btn_color)
        fila_color.addStretch()
        cont.addLayout(fila_color)

        contenido_layout.addLayout(cont)
        contenido_layout.addWidget(self._separador())

        # ---------- Footer ----------
        footer = QHBoxLayout()
        footer.setContentsMargins(18, 8, 18, 12)
        footer.setSpacing(4)
        footer.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setFixedHeight(ALTO_BOTON)
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {COLOR_ACENTO}; padding: 0 8px;
                font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {COLOR_ACENTO_HOVER}; }}
        """)
        footer.addWidget(btn_cancelar)

        btn_guardar = QPushButton("GUARDAR")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setFixedHeight(ALTO_BOTON)
        btn_guardar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white; border: none;
                border-radius: 4px; padding: 0 14px;
                font-size: 11px; font-weight: 700;
                letter-spacing: 0.5px; min-width: 78px;
            }}
            QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
            QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
        """)
        btn_guardar.clicked.connect(self._on_guardar)
        footer.addWidget(btn_guardar)

        contenido_layout.addLayout(footer)
        root.addWidget(contenido)

        self._actualizar_boton_color()
        self.input_nombre.returnPressed.connect(self._on_guardar)
        self.input_desc.returnPressed.connect(self._on_guardar)
        self.input_nombre.setFocus()

    def _separador(self):
        l = QFrame()
        l.setFrameShape(QFrame.HLine)
        l.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        l.setFixedHeight(1)
        return l

    def _qss_input(self):
        return f"""
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QLineEdit::placeholder {{ color: {COLOR_TEXTO_TERCIARIO}; }}
        """

    def _crear_icono_color(self, color_hex: str, size: int = 18) -> QIcon:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size - 1, size - 1)
        pen = QPen(QColor(255, 255, 255, 90))
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(1, 1, size - 3, size - 3)
        painter.end()
        return QIcon(pixmap)

    def _abrir_color_picker(self):
        dlg = QColorDialog(QColor(self._color_actual), self)
        dlg.setWindowTitle("Selecciona un color")
        dlg.setOption(QColorDialog.DontUseNativeDialog, True)
        dlg.setStyleSheet(self._qss_color_dialog())
        if dlg.exec() == QDialog.Accepted:
            color = dlg.currentColor()
            if color.isValid():
                self._color_actual = color.name()
                self._actualizar_boton_color()

    def _qss_color_dialog(self):
        return f"""
            QColorDialog {{ background-color: {COLOR_PANEL}; }}
            QColorDialog QLabel {{ color: {COLOR_TEXTO}; background: transparent; border: none; font-size: 12px; }}
            QColorDialog QGroupBox {{
                color: {COLOR_TEXTO}; border: 1px solid {COLOR_BORDE};
                border-radius: 4px; margin-top: 10px; padding-top: 8px;
            }}
            QColorDialog QGroupBox::title {{
                color: {COLOR_TEXTO_SECUNDARIO};
                subcontrol-origin: margin; subcontrol-position: top left;
                left: 10px; padding: 0 4px;
            }}
            QColorDialog QPushButton {{
                background-color: {COLOR_INPUT_BG}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT}; border-radius: 4px;
                padding: 5px 16px; font-size: 12px; min-width: 70px;
            }}
            QColorDialog QPushButton:hover {{ background-color: {COLOR_ACENTO}; color: white; border: 1px solid {COLOR_ACENTO}; }}
            QColorDialog QPushButton:pressed {{ background-color: {COLOR_ACENTO_PRESSED}; }}
            QColorDialog QSpinBox, QColorDialog QDoubleSpinBox, QColorDialog QLineEdit {{
                background-color: {COLOR_INPUT_BG}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT}; border-radius: 4px;
                padding: 2px 6px; font-size: 12px;
                selection-background-color: {COLOR_ACENTO}; selection-color: white;
            }}
            QColorDialog QSpinBox:focus, QColorDialog QDoubleSpinBox:focus, QColorDialog QLineEdit:focus {{
                border: 1px solid {COLOR_ACENTO};
            }}
            QColorDialog QComboBox {{
                background-color: {COLOR_INPUT_BG}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT}; border-radius: 4px;
                padding: 2px 6px;
            }}
            QColorDialog QComboBox QAbstractItemView {{
                background-color: {COLOR_PANEL}; color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO}; selection-color: white;
            }}
            QColorDialog QFrame {{ border: none; }}
        """

    def _actualizar_boton_color(self):
        c = self._color_actual
        self.btn_color.setIcon(self._crear_icono_color(c, 18))
        self.btn_color.setIconSize(QSize(18, 18))
        self.btn_color.setText(f"  {c.upper()}")
        self.btn_color.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 0 12px; font-size: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: 600; text-align: left;
            }}
            QPushButton:hover {{ border: 1px solid {COLOR_ACENTO}; }}
        """)

    def _on_guardar(self):
        if not self.input_nombre.text().strip():
            return
        self.accept()

    def datos(self):
        return (
            self.input_nombre.text().strip(),
            self.input_desc.text().strip(),
            self._color_actual,
        )