import logging
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QUrl, Signal, QPoint
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QMenu,
)

logger = logging.getLogger(__name__)


class TarjetaCuenta(QWidget):
    """Widget de una cuenta con botón de '...' flotante para remover."""
    cuenta_seleccionada = Signal(dict)
    cuenta_removida = Signal(dict)

    def __init__(self, cuenta: dict, client, network: QNetworkAccessManager, parent=None):
        super().__init__(parent)
        self._cuenta = cuenta
        self._client = client
        self._network = network

        self.setFixedSize(140, 190)
        self.setAttribute(Qt.WA_Hover)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Botón principal (avatar)
        self.btn_avatar = QPushButton()
        self.btn_avatar.setFixedSize(140, 160)
        self.btn_avatar.setCursor(Qt.PointingHandCursor)
        self.btn_avatar.setStyleSheet("""
            QPushButton {
                background-color: #16232c;
                border: 1px solid #22323d;
                border-radius: 8px;
            }
            QPushButton:hover { border: 1px solid #2eb8ff; }
        """)
        self.btn_avatar.clicked.connect(lambda: self.cuenta_seleccionada.emit(self._cuenta))
        layout.addWidget(self.btn_avatar)

        # Nombre debajo
        nombre = QLabel(cuenta.get("nombre") or "Usuario")
        nombre.setStyleSheet("color: #e6edf3; font-size: 12px; font-weight: 600;")
        nombre.setAlignment(Qt.AlignCenter)
        layout.addWidget(nombre)

        # Botón "..." flotante
        self.btn_menu = QPushButton("...", self)
        self.btn_menu.setFixedSize(24, 24)
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        self.btn_menu.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2eb8ff; }
        """)
        self.btn_menu.move(110, 130)
        self.btn_menu.hide()
        self.btn_menu.clicked.connect(self._mostrar_menu)

        self._cargar_avatar()

    def _cargar_avatar(self):
        avatar_url = self._cuenta.get("avatar_url")
        if avatar_url:
            url = self._client.construir_url_avatar(avatar_url)
            if url:
                reply = self._network.get(QNetworkRequest(QUrl(url)))
                reply.finished.connect(lambda r=reply: self._on_avatar_descargado(r))
        else:
            self.btn_avatar.setText((self._cuenta.get("nombre") or "?")[:1].upper())
            self.btn_avatar.setStyleSheet(self.btn_avatar.styleSheet() + "font-size: 48px; color: #2eb8ff;")

    def _on_avatar_descargado(self, reply: QNetworkReply):
        try:
            if reply.error() != QNetworkReply.NoError:
                return
            pix = QPixmap()
            if not pix.loadFromData(bytes(reply.readAll())):
                return

            scaled = pix.scaled(QSize(140, 160), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            left = (scaled.width() - 140) // 2
            top = (scaled.height() - 160) // 2
            recortado = scaled.copy(left, top, 140, 160)

            self.btn_avatar.setIcon(recortado)
            self.btn_avatar.setIconSize(QSize(140, 160))
            self.btn_avatar.setText("")
        finally:
            reply.deleteLater()

    def enterEvent(self, event):
        self.btn_menu.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.btn_menu.hide()
        super().leaveEvent(event)

    def _mostrar_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #16232c;
                color: #e6edf3;
                border: 1px solid #22323d;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2eb8ff;
                color: white;
            }
        """)
        accion_remover = QAction("Remover cuenta", self)
        accion_remover.triggered.connect(lambda: self.cuenta_removida.emit(self._cuenta))
        menu.addAction(accion_remover)
        menu.exec(self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height())))


class SelectorCuentas(QDialog):
    cuenta_seleccionada = Signal(dict)
    agregar_cuenta = Signal()
    cerrado = Signal()
    cuenta_removida = Signal(dict)

    def __init__(self, cuentas: list[dict], client, parent=None):
        super().__init__(parent)
        self._client = client
        self._network = QNetworkAccessManager(self)
        self._cuentas = cuentas

        self.setWindowTitle("Seleccionar cuenta")
        self.setFixedSize(700, 450)
        self.setStyleSheet("QDialog { background-color: #0d181f; }")

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(40, 30, 40, 30)
        self.root.setSpacing(20)

        # Logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        base = Path(__file__).resolve().parents[2]
        ruta_logo = base / "assets" / "logo-mg.png"
        if ruta_logo.exists():
            pix = QPixmap(str(ruta_logo))
            if not pix.isNull():
                logo.setPixmap(pix.scaledToHeight(55, Qt.SmoothTransformation))
        self.root.addWidget(logo)

        # Título
        titulo = QLabel("Seleccionar cuenta")
        titulo.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff;")
        titulo.setAlignment(Qt.AlignCenter)
        self.root.addWidget(titulo)

        # Subtítulo
        subtitulo = QLabel("Elige una cuenta para continuar")
        subtitulo.setStyleSheet("color: #8ea0af; font-size: 13px;")
        subtitulo.setAlignment(Qt.AlignCenter)
        self.root.addWidget(subtitulo)

        self.root.addStretch(1)

        # Contenedor de tarjetas
        self._tarjetas_layout = QHBoxLayout()
        self._tarjetas_layout.setSpacing(24)
        self._tarjetas_layout.addStretch()
        self.root.addLayout(self._tarjetas_layout)

        self.root.addStretch(1)

        self._renderizar_tarjetas()

    def _renderizar_tarjetas(self):
        # Limpiar layout
        while self._tarjetas_layout.count():
            item = self._tarjetas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._tarjetas_layout.addStretch()

        # Tarjetas de cuentas
        for cuenta in self._cuentas:
            tarjeta = TarjetaCuenta(cuenta, self._client, self._network)
            tarjeta.cuenta_seleccionada.connect(self.cuenta_seleccionada.emit)
            tarjeta.cuenta_removida.connect(self._on_remover_cuenta)
            self._tarjetas_layout.addWidget(tarjeta)

        # Botón "+"
        self._tarjetas_layout.addWidget(self._crear_boton_agregar())
        self._tarjetas_layout.addStretch()

    def _on_remover_cuenta(self, cuenta: dict):
        # Eliminar de la lista local
        self._cuentas = [c for c in self._cuentas if c.get("email") != cuenta.get("email")]
        self.cuenta_removida.emit(cuenta)
        self._renderizar_tarjetas()  # Volver a pintar sin la cuenta eliminada

    def _crear_boton_agregar(self) -> QWidget:
        contenedor = QWidget()
        contenedor.setFixedSize(140, 190)
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        btn = QPushButton("+")
        btn.setFixedSize(140, 160)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #16232c;
                border: 1px solid #22323d;
                border-radius: 8px;
                color: #8ea0af;
                font-size: 48px;
                font-weight: 300;
            }
            QPushButton:hover { border: 1px solid #2eb8ff; color: #2eb8ff; }
        """)
        btn.clicked.connect(self._on_agregar_cuenta)
        layout.addWidget(btn)

        texto = QLabel("Añadir cuenta")
        texto.setStyleSheet("color: #e6edf3; font-size: 12px; font-weight: 600;")
        texto.setAlignment(Qt.AlignCenter)
        layout.addWidget(texto)

        return contenedor

    def _on_agregar_cuenta(self):
        self.hide()
        self.agregar_cuenta.emit()

    def closeEvent(self, event):
        self.cerrado.emit()
        super().closeEvent(event)