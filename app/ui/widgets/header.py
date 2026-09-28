# app/ui/widgets/header.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QMenu,
    QSizePolicy,
)

from app.styles import tracker as S


NOMBRE_ORGANIZACION = "GM INGENIEROS Y CONSULTORES"
TITULO_SISTEMA = "Sistema de Control de Asistencia"

COLOR_ORG = "#8ea0af"      # gris azulado, sobrio
COLOR_TITULO = "#ffffff"
COLOR_LINEA = "#2196f3"    # acento discreto


class HeaderWidget(QWidget):
    cerrar_sesion = Signal()

    def __init__(self, nombre_usuario: str, parent=None):
        super().__init__(parent)
        self.nombre_usuario = nombre_usuario
        # El header ocupa solo la altura que necesita (no se estira)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(52)  # <- altura del header (ajústala a gusto)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ============================================================
        # MARCA INSTITUCIONAL
        # ============================================================
        self.contenedor_titulo = QFrame()
        self.contenedor_titulo.setObjectName("contenedorTitulo")
        self.contenedor_titulo.setStyleSheet(
            "QFrame#contenedorTitulo { background: transparent; border: none; }"
        )
        lay_titulo = QVBoxLayout(self.contenedor_titulo)
        lay_titulo.setContentsMargins(0, 0, 0, 0)
        lay_titulo.setSpacing(2)

        # Nombre de la organización (pequeño, espaciado, mayúsculas)
        label_org = QLabel(NOMBRE_ORGANIZACION)
        fuente_org = QFont("Segoe UI", 8, QFont.DemiBold)
        fuente_org.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        label_org.setFont(fuente_org)
        label_org.setStyleSheet(
            f"color: {COLOR_ORG}; background: transparent; border: none; padding: 0; margin: 0;"
        )

        # Línea fina de separación
        linea = QFrame()
        linea.setFixedHeight(2)
        linea.setFixedWidth(40)
        linea.setStyleSheet(f"background: {COLOR_LINEA}; border: none;")

        # Título del sistema
        label_titulo = QLabel(TITULO_SISTEMA)
        fuente_titulo = QFont("Segoe UI", 12, QFont.DemiBold)
        fuente_titulo.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        label_titulo.setFont(fuente_titulo)
        label_titulo.setStyleSheet(
            f"color: {COLOR_TITULO}; background: transparent; border: none; padding: 0; margin: 0;"
        )

        lay_titulo.addWidget(label_org)
        lay_titulo.addWidget(linea)
        lay_titulo.addWidget(label_titulo)

        layout.addWidget(self.contenedor_titulo, alignment=Qt.AlignVCenter)
        layout.addStretch()

        # ============================================================
        # USUARIO + MENÚ (chip clicable con avatar)
        # ============================================================
        self.btn_usuario = QPushButton()
        self.btn_usuario.setObjectName("btnUsuario")
        self.btn_usuario.setCursor(Qt.PointingHandCursor)
        self.btn_usuario.setFixedHeight(32)
        self.btn_usuario.setToolTip("Opciones de cuenta")
        self.btn_usuario.setStyleSheet(f"""
            QPushButton#btnUsuario {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid #22323d;
                border-radius: 6px;
                outline: none;
            }}
            QPushButton#btnUsuario:hover {{
                background: rgba(33, 150, 243, 0.12);
                border-color: {COLOR_LINEA};
            }}
            QPushButton#btnUsuario:pressed {{
                background: rgba(33, 150, 243, 0.20);
            }}
        """)

        lay_u = QHBoxLayout(self.btn_usuario)
        lay_u.setContentsMargins(5, 0, 8, 0)
        lay_u.setSpacing(6)

        # Avatar con la inicial
        inicial = (nombre_usuario.strip()[:1] or "?").upper()
        avatar = QLabel(inicial)
        avatar.setFixedSize(22, 22)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {COLOR_LINEA};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            padding: 0; margin: 0;
        """)

        # Nombre (recortado con "…" si es muy largo)
        fuente_nombre = QFont("Segoe UI", 9, QFont.DemiBold)
        fm = QFontMetrics(fuente_nombre)
        texto_nombre = fm.elidedText(nombre_usuario, Qt.ElideRight, 110)
        label_nombre = QLabel(texto_nombre)
        label_nombre.setFont(fuente_nombre)
        label_nombre.setStyleSheet(
            "color: #e6edf3; background: transparent; border: none; padding: 0; margin: 0;"
        )

        flecha = QLabel("▾")
        flecha.setStyleSheet(
            f"color: {COLOR_ORG}; background: transparent; border: none; "
            "font-size: 10px; padding: 0; margin: 0;"
        )

        for w in (avatar, label_nombre, flecha):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay_u.addWidget(w, alignment=Qt.AlignVCenter)

        # El botón no calcula el ancho a partir de su layout: se fija a mano
        ancho = 5 + 22 + 6 + fm.horizontalAdvance(texto_nombre) + 6 + 10 + 8 + 4
        self.btn_usuario.setFixedWidth(ancho)

        self.btn_usuario.clicked.connect(self._abrir_menu)
        layout.addWidget(self.btn_usuario, alignment=Qt.AlignVCenter)

    # ============================================================
    def _abrir_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #16232c;
                border: 1px solid #22323d;
                color: #ffffff;
                padding: 4px;
                border-radius: 6px;
            }
            QMenu::item {
                padding: 7px 18px;
                font-size: 11px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2196f3;
                color: white;
            }
            QMenu::item:disabled {
                color: #8ea0af;
                font-size: 11px;
            }
            QMenu::separator {
                height: 1px;
                background: #22323d;
                margin: 5px 8px;
            }
        """)

        # Encabezado informativo (no clicable)
        acc_info = QAction(f"Sesión: {self.nombre_usuario}", self)
        acc_info.setEnabled(False)
        menu.addAction(acc_info)
        menu.addSeparator()

        acc_cambiar = QAction("Cambiar de cuenta", self)
        acc_cambiar.triggered.connect(self.cerrar_sesion.emit)
        menu.addAction(acc_cambiar)

        acc_salir = QAction("Cerrar sesión", self)
        acc_salir.triggered.connect(self.cerrar_sesion.emit)
        menu.addAction(acc_salir)

        # Alinear el borde derecho del menú con el del botón, justo debajo
        ancho_menu = menu.sizeHint().width()
        pos = self.btn_usuario.mapToGlobal(self.btn_usuario.rect().bottomRight())
        pos.setX(pos.x() - ancho_menu)
        pos.setY(pos.y() + 6)
        menu.exec(pos)