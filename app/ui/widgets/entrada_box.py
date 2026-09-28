# app/ui/widgets/entrada_box.py
"""
Caja unificada estilo Clockify (compacta).
El botón cambia según el estado:
  - Sin entrada      → "+"  (abre el modal)
  - Con entrada      → "▶"  (arranca el timer)
  - Timer corriendo  → "■"  (detiene el timer)
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app.styles.colors import (
    COLOR_INPUT_BG, COLOR_BORDE_INPUT,
    COLOR_TEXTO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_PELIGRO, COLOR_PELIGRO_HOVER,
    RADIO_INPUT,
)


class EntradaBox(QFrame):
    abrir_modal = Signal()
    play_clicked = Signal()

    ESTADO_VACIO = "vacio"
    ESTADO_LISTO = "listo"
    ESTADO_CORRIENDO = "corriendo"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EntradaBox")
        self.setFixedHeight(52)         
        self.setStyleSheet(f"""
            #EntradaBox {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
            }}
        """)

        self._estado = self.ESTADO_VACIO

        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)     # ⬅️ antes 4,4,4,4
        layout.setSpacing(4)                       # ⬅️ antes 6

        # ---------- Texto (abre modal) ----------
        self.boton_texto = QPushButton()
        self.boton_texto.setCursor(Qt.PointingHandCursor)
        self.boton_texto.clicked.connect(self.abrir_modal.emit)
        self._aplicar_estilo_texto_vacio()
        layout.addWidget(self.boton_texto, 1)

        # ---------- Timer ----------
        self.label_tiempo = QLabel("00:00:00")
        self.label_tiempo.setStyleSheet(f"""
            QLabel {{
                color: {COLOR_TEXTO};
                font-size: 13px;                    /* ⬅️ antes 15 */
                font-weight: 600;
                font-family: 'Consolas', 'Courier New', monospace;
                border: none;
                background: transparent;
                padding: 0 2px;
            }}
        """)
        layout.addWidget(self.label_tiempo)

        # ---------- Botón acción ----------
        self.boton_accion = QPushButton("+")
        self.boton_accion.setFixedSize(38, 38)     # ⬅️ antes 48,48
        self.boton_accion.setCursor(Qt.PointingHandCursor)
        self.boton_accion.clicked.connect(self._on_accion_click)
        layout.addWidget(self.boton_accion)

        self.set_estado(self.ESTADO_VACIO)

    # ============================================================
    def _on_accion_click(self):
        if self._estado == self.ESTADO_VACIO:
            self.abrir_modal.emit()
        else:
            self.play_clicked.emit()

    # ============================================================
    # API pública
    # ============================================================
    def set_descripcion(self, texto: str):
        if texto:
            self.boton_texto.setText(texto)
            self._aplicar_estilo_texto_lleno()
        else:
            self.boton_texto.setText("¿En qué estás trabajando?")
            self._aplicar_estilo_texto_vacio()

    def set_tiempo(self, texto: str):
        self.label_tiempo.setText(texto)

    def set_estado(self, estado: str):
        self._estado = estado

        if estado == self.ESTADO_VACIO:
            self._estilizar_boton_accion(
                "+", COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED
            )
            self.boton_texto.setEnabled(True)
        elif estado == self.ESTADO_LISTO:
            self._estilizar_boton_accion(
                "▶", COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED
            )
            self.boton_texto.setEnabled(True)
        else:
            self._estilizar_boton_accion(
                "■", COLOR_PELIGRO, COLOR_PELIGRO_HOVER, "#a81e1e"
            )
            self.boton_texto.setEnabled(False)

    # ============================================================
    # Estilos internos
    # ============================================================
    def _estilizar_boton_accion(self, texto, color, hover, pressed):
        self.boton_accion.setText(texto)
        self.boton_accion.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 19px;                /* ⬅️ antes 24 (mitad del ancho) */
                font-size: 15px;                    /* ⬅️ antes 18 */
                font-weight: 700;
                border: none;
                outline: none;
            }}
            QPushButton:hover   {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {pressed}; }}
        """)

    def _aplicar_estilo_texto_vacio(self):
        self.boton_texto.setText("¿En qué estás trabajando?")
        self.boton_texto.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLOR_TEXTO_TERCIARIO};
                text-align: left;
                padding: 0 10px;
                font-size: 12px;                     /* ⬅️ antes 13 */
                font-style: italic;
            }}
            QPushButton:hover {{ color: {COLOR_TEXTO}; }}
            QPushButton:disabled {{ color: {COLOR_TEXTO_TERCIARIO}; }}
        """)

    def _aplicar_estilo_texto_lleno(self):
        self.boton_texto.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLOR_TEXTO};
                text-align: left;
                padding: 0 10px;
                font-size: 12px;                     /* ⬅️ antes 13 */
                font-weight: 500;
                font-style: normal;
            }}
            QPushButton:hover {{ color: {COLOR_ACENTO}; }}
            QPushButton:disabled {{ color: {COLOR_TEXTO}; }}
        """)