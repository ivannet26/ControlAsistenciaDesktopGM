
import os
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class CustomTitleBar(QWidget):
    def __init__(
        self,
        parent,
        titulo="Control de Asistencia",
        mostrar_maximizar=True,
        mostrar_minimizar=True,
    ):
        super().__init__(parent)
        self.parent_window = parent

        self.setFixedHeight(28)
        self.setObjectName("CustomTitleBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget#CustomTitleBar {
                background-color: #0d181f;    /* 🎨 Fondo oscuro de tu app */
                border: none;
            }
            QWidget#CustomTitleBar QLabel {
                background-color: transparent;
                border: none;
                color: #ffffff;
            }
            QWidget#CustomTitleBar QPushButton {
                background: transparent;
                color: #b0bec5;                /* 🎨 Botones gris claro */
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10px;
                font-weight: 600;
            }
            QWidget#CustomTitleBar QPushButton:hover {
                background-color: #1a2b35;     /* 🎨 Hover sutil más claro */
                color: #ffffff;
            }
            QWidget#CustomTitleBar QPushButton#btn_close:hover {
                background-color: #e81123;
                color: #ffffff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(8)

        # ---- Icono ----
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_icono = os.path.join(base_dir, "assets", "favicon.png")
        

        # ---- Título ----
        self.label = QLabel(titulo)
        self.label.setStyleSheet(
    "color: #ffffff; "
    "font-family: 'Segoe UI Semibold', 'Segoe UI', sans-serif; "
    "font-size: 11px; "
    "font-weight: 600; "
    "background: transparent; border: none;"
)

        
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.label)
        layout.addStretch()

        # ---- Botones ----
        if mostrar_minimizar:
            self.btn_min = self._crear_boton("—", "min")
            layout.addWidget(self.btn_min)
            self.btn_min.clicked.connect(self.parent_window.showMinimized)

        if mostrar_maximizar:
            self.btn_max = self._crear_boton("□", "max")
            layout.addWidget(self.btn_max)
            self.btn_max.clicked.connect(self._toggle_max)

        self.btn_close = self._crear_boton("✕", "close")
        self.btn_close.setObjectName("btn_close")
        layout.addWidget(self.btn_close)
        self.btn_close.clicked.connect(self.parent_window.close)

    def _crear_boton(self, texto, tipo):
        btn = QPushButton(texto)
        btn.setFixedSize(32, 26)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFocusPolicy(Qt.NoFocus)
        return btn

    def _toggle_max(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setText("□")
        else:
            self.parent_window.showMaximized()
            self.btn_max.setText("❐")

    # ============================================================
    # 🖱️ Arrastre NATIVO de la ventana (funciona perfecto)
    # ============================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # ✅ Solución nativa: le dice a Windows que arrastre la ventana
            handle = self.parent_window.windowHandle()
            if handle:
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Doble clic en la barra = maximizar/restaurar."""
        if event.button() == Qt.LeftButton:
            self._toggle_max()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)