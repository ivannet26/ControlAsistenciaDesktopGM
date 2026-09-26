# app/ui/dialogs/modal_inactividad.py
"""
Modal que aparece cuando el usuario ha estado inactivo.
Pregunta qué hacer con el tiempo de inactividad.
"""

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QButtonGroup, QFrame, QRadioButton
)

from .estilos import (
    COLOR_FONDO, COLOR_BORDE, COLOR_ACENTO, COLOR_ACENTO_HOVER,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO,
)


class ModalInactividad(QDialog):
    """
    Modal de inactividad.
    Devuelve la acción elegida ('descartar' por defecto).
    """

    def __init__(
        self,
        padre=None,
        minutos_inactivo: int = 5,
        actividad: str = "",
        segundos_inactivo_inicial: int = 0,
    ):
        super().__init__(padre)

        self.minutos_inactivo = minutos_inactivo
        self.actividad = actividad
        self.accion_seleccionada = "descartar"

        # Hora exacta de inicio de la inactividad
        self.inicio_inactividad = time.time() - segundos_inactivo_inicial

        self.setWindowTitle("Has estado inactivo")
        self.setMinimumWidth(500)
        self.setModal(True)

        # No permitir cerrar sin elegir
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_FONDO};
                color: {COLOR_TEXTO};
            }}
        """)

        self._armar_ui()

        # Timer para actualizar el contador cada segundo
        self._timer_contador = QTimer(self)
        self._timer_contador.timeout.connect(self._actualizar_contador)
        self._timer_contador.setInterval(1000)
        self._timer_contador.start()

        self._actualizar_contador()

    # ========================================================
    # UI
    # ========================================================

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -------- TÍTULO --------
        titulo = QLabel("Has estado inactivo")
        titulo.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO};
                font-size: 17px;
                font-weight: 600;
            }}
        """)
        layout.addWidget(titulo)

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
                font-size: 13px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(descripcion)

        # -------- CONTADOR EN VIVO (compacto) --------
        contador_widget = QFrame()
        contador_widget.setStyleSheet(f"""
            QFrame {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                border-radius: 4px;
            }}
        """)
        contador_layout = QHBoxLayout(contador_widget)
        contador_layout.setContentsMargins(14, 10, 14, 10)
        contador_layout.setSpacing(12)

        # Etiqueta izquierda
        label_titulo = QLabel("Tiempo inactivo:")
        label_titulo.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 12px;
                border: none;
                background: transparent;
            }}
        """)
        contador_layout.addWidget(label_titulo)

        # Contador (tamaño medio)
        self.label_contador = QLabel("00:00:00")
        self.label_contador.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_ACENTO};
                font-size: 18px;
                font-weight: 600;
                font-family: 'Consolas', 'Courier New', monospace;
                border: none;
                background: transparent;
            }}
        """)
        contador_layout.addWidget(self.label_contador)

        contador_layout.addStretch()

        # Desglose a la derecha
        self.label_desglose = QLabel("")
        self.label_desglose.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 11px;
                border: none;
                background: transparent;
            }}
        """)
        contador_layout.addWidget(self.label_desglose)

        layout.addWidget(contador_widget)

        # -------- ESPACIO --------
        layout.addSpacing(4)

        # -------- OPCIÓN ÚNICA --------
        self.grupo = QButtonGroup(self)

        radio_descartar = QRadioButton("Descartar tiempo de inactividad")
        radio_descartar.setProperty("valor", "descartar")
        radio_descartar.setChecked(True)
        radio_descartar.setStyleSheet(f"""
      QRadioButton {{
        color: {COLOR_TEXTO};
        font-size: 13px;
        padding: 4px 0;
        spacing: 10px;
      }}
      QRadioButton::indicator {{
        width: 15px;
        height: 15px;
        border-radius: 8px;
        border: 2px solid {COLOR_TEXTO_SECUNDARIO};
        background-color: transparent;
      }}
      QRadioButton::indicator:checked {{
        border: 2px solid {COLOR_ACENTO};
        background-color: {COLOR_ACENTO};
      }}
        """)
        self.grupo.addButton(radio_descartar)
        layout.addWidget(radio_descartar)

        # ------------------------------------------------------
        # OPCIONES DESHABILITADAS (comentadas para uso futuro)
        # ------------------------------------------------------
        # opciones = [
        #     ("descartar_y", "Descartar tiempo de inactividad y continuar"),
        #     ("guardar", "Guardar tiempo de inactividad"),
        #     ("añadir", "Añadir tiempo de inactividad como nueva entrada"),
        # ]
        #
        # for valor, texto in opciones:
        #     radio = QRadioButton(texto)
        #     radio.setProperty("valor", valor)
        #     radio.setStyleSheet(f"""
        #         QRadioButton {{
        #             color: {COLOR_TEXTO};
        #             font-size: 13px;
        #             padding: 4px 0;
        #             spacing: 10px;
        #         }}
        #         QRadioButton::indicator {{
        #             width: 15px;
        #             height: 15px;
        #             border-radius: 8px;
        #             border: 2px solid {COLOR_TEXTO_SECUNDARIO};
        #             background-color: transparent;
        #         }}
        #         QRadioButton::indicator:checked {{
        #             border: 2px solid {COLOR_ACENTO};
        #             background-color: {COLOR_ACENTO};
        #         }}
        #     """)
        #     self.grupo.addButton(radio)
        #     layout.addWidget(radio)

        # -------- SEPARADOR --------
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        linea.setFixedHeight(1)
        layout.addWidget(linea)

        # -------- BOTÓN CONTINUAR --------
        fila_boton = QHBoxLayout()
        fila_boton.addStretch()

        self.btn_continuar = QPushButton("Continuar")
        self.btn_continuar.setCursor(Qt.PointingHandCursor)
        self.btn_continuar.clicked.connect(self._continuar)
        self.btn_continuar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                border: none;
                padding: 9px 24px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 3px;
                min-width: 110px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACENTO_HOVER};
            }}
        """)
        fila_boton.addWidget(self.btn_continuar)

        layout.addLayout(fila_boton)

    # ========================================================
    # CONTADOR EN VIVO
    # ========================================================

    def _actualizar_contador(self):
        """Actualiza el contador cada segundo."""
        segundos_totales = int(time.time() - self.inicio_inactividad)

        if segundos_totales < 0:
            segundos_totales = 0

        horas = segundos_totales // 3600
        minutos = (segundos_totales % 3600) // 60
        segundos = segundos_totales % 60

        self.label_contador.setText(
            f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        )

        segundos_umbral = self.minutos_inactivo * 60
        segundos_extra = max(0, segundos_totales - segundos_umbral)

        if segundos_extra > 0:
            self.label_desglose.setText(
                f"({segundos_umbral}s umbral + {segundos_extra}s extra)"
            )
        else:
            self.label_desglose.setText(
                f"(umbral: {segundos_umbral}s)"
            )

    # ========================================================
    # ACCIONES
    # ========================================================

    def _continuar(self):
        """Guarda la acción elegida y cierra el modal."""
        self._timer_contador.stop()

        boton = self.grupo.checkedButton()
        if boton:
            self.accion_seleccionada = boton.property("valor")
        self.accept()

    def obtener_accion(self) -> str:
        return self.accion_seleccionada

    def obtener_segundos_totales(self) -> int:
        return int(time.time() - self.inicio_inactividad)