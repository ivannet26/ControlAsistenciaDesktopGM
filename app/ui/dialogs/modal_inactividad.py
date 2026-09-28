# app/ui/dialogs/modal_inactividad.py
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QButtonGroup, QFrame, QRadioButton, QWidget,
)

from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_INPUT_BG, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    RADIO_INPUT, RADIO_BOTON,
)


class ModalInactividad(QDialog):
    def __init__(self, padre=None, minutos_inactivo=5, actividad="", segundos_inactivo_inicial=0):
        super().__init__(padre)
        self.minutos_inactivo = minutos_inactivo
        self.actividad = actividad
        self.accion_seleccionada = "descartar"
        self.inicio_inactividad = time.time() - segundos_inactivo_inicial

        self.setWindowTitle("Has estado inactivo")
        self.setMinimumWidth(500)
        self.setModal(True)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._armar_ui()

        self._timer_contador = QTimer(self)
        self._timer_contador.timeout.connect(self._actualizar_contador)
        self._timer_contador.setInterval(1000)
        self._timer_contador.start()
        self._actualizar_contador()

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            p_geo = self.parent().geometry()
            self.move(
                p_geo.center().x() - self.width() // 2,
                p_geo.center().y() - self.height() // 2,
            )

    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(
            self, "Has estado inactivo",
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
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(28, 20, 28, 26)
        layout.setSpacing(16)

        # -------- DESCRIPCIÓN --------
        descripcion = QLabel(
            f"Has estado inactivo mientras registrabas "
            f"\"{self.actividad}\". "
            f"El tiempo de inactividad será descontado automáticamente."
        )
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 13px; border: none; background: transparent;
            }}
        """)
        layout.addWidget(descripcion)

        # -------- CONTADOR --------
        contador_widget = QFrame()
        contador_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
            }}
        """)
        contador_layout = QHBoxLayout(contador_widget)
        contador_layout.setContentsMargins(16, 12, 16, 12)
        contador_layout.setSpacing(12)

        label_titulo = QLabel("Tiempo inactivo:")
        label_titulo.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 12px; border: none; background: transparent;
            }}
        """)
        contador_layout.addWidget(label_titulo)

        self.label_contador = QLabel("00:00:00")
        self.label_contador.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_ACENTO};
                font-size: 18px; font-weight: 600;
                font-family: 'Consolas', 'Courier New', monospace;
                border: none; background: transparent;
            }}
        """)
        contador_layout.addWidget(self.label_contador)
        contador_layout.addStretch()

        self.label_desglose = QLabel("")
        self.label_desglose.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 11px; border: none; background: transparent;
            }}
        """)
        contador_layout.addWidget(self.label_desglose)
        layout.addWidget(contador_widget)

        # -------- RADIO --------
        self.grupo = QButtonGroup(self)
        qss_radio = f"""
            QRadioButton {{
                color: {COLOR_TEXTO}; font-size: 13px;
                padding: 4px 0; spacing: 10px; border: none;
                background: transparent;
            }}
            QRadioButton::indicator {{
                width: 16px; height: 16px;
                border-radius: 9px;
                border: 2px solid {COLOR_BORDE_INPUT};
                background-color: transparent;
            }}
            QRadioButton::indicator:hover {{ border: 2px solid {COLOR_ACENTO}; }}
            QRadioButton::indicator:checked {{
                border: 2px solid {COLOR_ACENTO};
                background-color: {COLOR_ACENTO};
            }}
        """
        radio_descartar = QRadioButton("Descartar tiempo de inactividad")
        radio_descartar.setProperty("valor", "descartar")
        radio_descartar.setChecked(True)
        radio_descartar.setStyleSheet(qss_radio)
        self.grupo.addButton(radio_descartar)
        layout.addWidget(radio_descartar)

        # Separador
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        linea.setFixedHeight(1)
        layout.addWidget(linea)

        # Botón
        fila_boton = QHBoxLayout()
        fila_boton.addStretch()
        self.btn_continuar = QPushButton("Continuar")
        self.btn_continuar.setCursor(Qt.PointingHandCursor)
        self.btn_continuar.clicked.connect(self._continuar)
        self.btn_continuar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white; border: none;
                padding: 10px 26px; font-size: 13px; font-weight: 600;
                border-radius: {RADIO_BOTON}px;
                min-width: 120px;
            }}
            QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
            QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
        """)
        fila_boton.addWidget(self.btn_continuar)
        layout.addLayout(fila_boton)

        root.addWidget(contenido)

    def _actualizar_contador(self):
        segundos_totales = int(time.time() - self.inicio_inactividad)
        if segundos_totales < 0:
            segundos_totales = 0
        horas = segundos_totales // 3600
        minutos = (segundos_totales % 3600) // 60
        segundos = segundos_totales % 60
        self.label_contador.setText(f"{horas:02d}:{minutos:02d}:{segundos:02d}")
        segundos_umbral = self.minutos_inactivo * 60
        segundos_extra = max(0, segundos_totales - segundos_umbral)
        if segundos_extra > 0:
            self.label_desglose.setText(
                f"({segundos_umbral}s umbral + {segundos_extra}s extra)"
            )
        else:
            self.label_desglose.setText(f"(umbral: {segundos_umbral}s)")

    def _continuar(self):
        self._timer_contador.stop()
        boton = self.grupo.checkedButton()
        if boton:
            self.accion_seleccionada = boton.property("valor")
        self.accept()

    def obtener_accion(self):
        return self.accion_seleccionada

    def obtener_segundos_totales(self):
        return int(time.time() - self.inicio_inactividad)