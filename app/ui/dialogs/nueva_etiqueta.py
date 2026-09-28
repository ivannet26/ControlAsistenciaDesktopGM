# app/ui/dialogs/nueva_etiqueta.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QWidget,
)

from app.styles.colors import (
    COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT, COLOR_INPUT_BG,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    RADIO_INPUT, RADIO_BOTON,
)


ANCHO_DIALOGO = 380
ALTO_INPUT = 34
ALTO_BOTON = 32
COLOR_POR_DEFECTO = "#2196f3"


class DialogoNuevaEtiqueta(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Añadir nueva etiqueta")
        self.setModal(True)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

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
        alto = self.layout().sizeHint().height()
        if alto < 150:
            alto = 150
        self.setFixedSize(ANCHO_DIALOGO, alto)

    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(
            self, "Añadir nueva etiqueta",
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

        cont = QVBoxLayout()
        cont.setContentsMargins(18, 14, 18, 18)
        cont.setSpacing(6)

        label = QLabel("Cambiar nombre")
        label.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px; border: none; background: transparent;"
        )
        cont.addWidget(label)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre de etiqueta")
        self.input_nombre.setFixedHeight(ALTO_INPUT)
        self.input_nombre.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 10px; font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QLineEdit::placeholder {{ color: {COLOR_TEXTO_TERCIARIO}; }}
        """)
        cont.addWidget(self.input_nombre)
        contenido_layout.addLayout(cont)
        contenido_layout.addWidget(self._separador())

        footer = QHBoxLayout()
        footer.setContentsMargins(18, 10, 18, 14)
        footer.setSpacing(6)
        footer.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.PointingHandCursor)
        btn_cancelar.setFixedHeight(ALTO_BOTON)
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {COLOR_ACENTO}; padding: 0 10px;
                font-size: 12px; font-weight: 600;
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
                border-radius: {RADIO_BOTON}px;
                padding: 0 18px;
                font-size: 11px; font-weight: 700;
                letter-spacing: 0.5px; min-width: 90px;
            }}
            QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
            QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
        """)
        btn_guardar.clicked.connect(self._on_guardar)
        footer.addWidget(btn_guardar)
        contenido_layout.addLayout(footer)
        root.addWidget(contenido)

        self.input_nombre.returnPressed.connect(self._on_guardar)
        self.input_nombre.setFocus()

    def _separador(self):
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        linea.setFixedHeight(1)
        return linea

    def _on_guardar(self):
        if not self.input_nombre.text().strip():
            return
        self.accept()

    def datos(self):
        return (self.input_nombre.text().strip(), COLOR_POR_DEFECTO)