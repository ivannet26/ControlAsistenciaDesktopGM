# app/ui/dialogs/modal_entrada.py
"""
Modal para agregar una entrada de tiempo manual.
Estilo basado en Clockify.
"""

from datetime import datetime, date, time, timedelta

from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDateEdit, QTimeEdit, QTextEdit,
    QFrame, QWidget
)

from .estilos import (
    COLOR_FONDO, COLOR_BORDE, COLOR_ACENTO, COLOR_ACENTO_HOVER,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TARJETA,
    COLOR_ERROR,
)


class ModalEntradaTiempo(QDialog):
    """
    Modal para crear una entrada de tiempo manual.
    """

    def __init__(self, padre=None, client=None):
        super().__init__(padre)
        self.client = client

        self.setWindowTitle("Nueva Entrada de Tiempo")
        self.setMinimumWidth(560)
        self.setModal(True)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_FONDO};
                color: {COLOR_TEXTO};
            }}
        """)

        self._armar_ui()

    # ========================================================
    # CONSTRUCCIÓN DE UI
    # ========================================================

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -------- TÍTULO --------
        titulo = QLabel("Nueva Entrada de Tiempo")
        titulo.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO};
                font-size: 18px;
                font-weight: 600;
                padding-bottom: 8px;
            }}
        """)
        layout.addWidget(titulo)

        # -------- FECHA --------
        label_fecha = QLabel("Fecha")
        label_fecha.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        layout.addWidget(label_fecha)

        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        self._estilizar_input(self.input_fecha)
        layout.addWidget(self.input_fecha)

        # -------- HORA INICIO / FIN --------
        fila_horas = QHBoxLayout()
        fila_horas.setSpacing(12)

        # Hora inicio
        col_inicio = QVBoxLayout()
        label_inicio = QLabel("Hora inicio")
        label_inicio.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        col_inicio.addWidget(label_inicio)

        self.input_hora_inicio = QTimeEdit()
        self.input_hora_inicio.setDisplayFormat("HH:mm")
        self.input_hora_inicio.setTime(QTime(8, 0))
        self._estilizar_input(self.input_hora_inicio)
        col_inicio.addWidget(self.input_hora_inicio)

        fila_horas.addLayout(col_inicio, 1)

        # Flecha ">"
        flecha = QLabel("›")
        flecha.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 20px;")
        flecha.setAlignment(Qt.AlignCenter)
        fila_horas.addWidget(flecha)

        # Hora fin
        col_fin = QVBoxLayout()
        label_fin = QLabel("Hora fin")
        label_fin.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        col_fin.addWidget(label_fin)

        self.input_hora_fin = QTimeEdit()
        self.input_hora_fin.setDisplayFormat("HH:mm")
        self.input_hora_fin.setTime(QTime(9, 0))
        self._estilizar_input(self.input_hora_fin)
        col_fin.addWidget(self.input_hora_fin)

        fila_horas.addLayout(col_fin, 1)

        # Duración
        col_duracion = QVBoxLayout()
        label_duracion = QLabel("Duración")
        label_duracion.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        col_duracion.addWidget(label_duracion)

        self.label_duracion = QLabel("01:00:00")
        self.label_duracion.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO};
                font-size: 14px;
                font-weight: 600;
                background-color: {COLOR_TARJETA};
                border: 1px solid {COLOR_BORDE};
                border-radius: 3px;
                padding: 8px 12px;
            }}
        """)
        col_duracion.addWidget(self.label_duracion)

        fila_horas.addLayout(col_duracion, 1)

        layout.addLayout(fila_horas)

        # Actualizar duración al cambiar horas
        self.input_hora_inicio.timeChanged.connect(self._actualizar_duracion)
        self.input_hora_fin.timeChanged.connect(self._actualizar_duracion)

        # -------- DESCRIPCIÓN --------
        label_desc = QLabel("¿En qué has trabajado?")
        label_desc.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        layout.addWidget(label_desc)

        self.input_descripcion = QTextEdit()
        self.input_descripcion.setPlaceholderText("Descripción del trabajo realizado")
        self.input_descripcion.setFixedHeight(80)
        self.input_descripcion.setStyleSheet(f"""
            QTextEdit {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 10px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QTextEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
        """)
        layout.addWidget(self.input_descripcion)

        # -------- PROYECTO --------
        label_proy = QLabel("Proyecto *")
        label_proy.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        layout.addWidget(label_proy)

        self.combo_proyecto = QComboBox()
        self.combo_proyecto.addItem("Buscar Proyecto o Cliente *", None)
        self._estilizar_input(self.combo_proyecto)
        layout.addWidget(self.combo_proyecto)

        # -------- ETIQUETA --------
        label_etq = QLabel("Etiqueta")
        label_etq.setStyleSheet(f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 12px;")
        layout.addWidget(label_etq)

        self.combo_etiqueta = QComboBox()
        self.combo_etiqueta.addItem("Buscar etiqueta", None)
        self._estilizar_input(self.combo_etiqueta)
        layout.addWidget(self.combo_etiqueta)

        # -------- SEPARADOR --------
        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        linea.setFixedHeight(1)
        layout.addWidget(linea)

        # -------- BOTONES --------
        fila_botones = QHBoxLayout()
        fila_botones.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE};
                padding: 8px 22px;
                font-size: 13px;
                border-radius: 3px;
                min-width: 90px;
            }}
            QPushButton:hover {{
                background-color: #1a2831;
            }}
        """)
        fila_botones.addWidget(self.btn_cancelar)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self._guardar)
        self.btn_guardar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                border: none;
                padding: 8px 22px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 3px;
                min-width: 90px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACENTO_HOVER};
            }}
        """)
        fila_botones.addWidget(self.btn_guardar)

        layout.addLayout(fila_botones)

    # ========================================================
    # HELPERS
    # ========================================================

    def _estilizar_input(self, widget):
        widget.setStyleSheet(f"""
            QComboBox, QDateEdit, QTimeEdit {{
                background-color: #101b22;
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                padding: 8px 12px;
                font-size: 13px;
                border-radius: 2px;
            }}
            QComboBox:focus, QDateEdit:focus, QTimeEdit:focus {{
                border: 1px solid {COLOR_ACENTO};
            }}
            QComboBox::drop-down,
            QDateEdit::drop-down,
            QTimeEdit::drop-down {{
                border: none;
                width: 24px;
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

    def _actualizar_duracion(self):
        t_inicio = self.input_hora_inicio.time()
        t_fin = self.input_hora_fin.time()

        seg_inicio = t_inicio.hour() * 3600 + t_inicio.minute() * 60
        seg_fin = t_fin.hour() * 3600 + t_fin.minute() * 60

        if seg_fin < seg_inicio:
            seg_fin += 86400  # pasa medianoche

        total = seg_fin - seg_inicio
        horas = total // 3600
        mins = (total % 3600) // 60
        segs = total % 60

        self.label_duracion.setText(
            f"{horas:02d}:{mins:02d}:{segs:02d}"
        )

    def _guardar(self):
        """Valida y devuelve los datos."""
        descripcion = self.input_descripcion.toPlainText().strip()

        if not descripcion:
            self.input_descripcion.setStyleSheet(f"""
                QTextEdit {{
                    background-color: #101b22;
                    border: 1px solid {COLOR_ERROR};
                    color: {COLOR_TEXTO};
                    padding: 8px 10px;
                    font-size: 13px;
                    border-radius: 2px;
                }}
            """)
            return

        # TODO: llamar al backend para crear la entrada
        self.accept()

    # ========================================================
    # GETTERS (para leer los valores desde afuera)
    # ========================================================

    def obtener_datos(self):
        """Devuelve un dict con los datos del formulario."""
        return {
            "fecha": self.input_fecha.date().toPython(),
            "hora_inicio": self.input_hora_inicio.time().toPython(),
            "hora_fin": self.input_hora_fin.time().toPython(),
            "descripcion": self.input_descripcion.toPlainText().strip(),
            "proyecto_id": self.combo_proyecto.currentData(),
            "etiqueta_id": self.combo_etiqueta.currentData(),
        }