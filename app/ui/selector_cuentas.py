import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QUrl, Signal, QPoint
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMenu, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


def _activar_barra_titulo_oscura(widget) -> None:
    """Activa el modo oscuro de la barra de título en Windows."""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
        valor = ctypes.c_int(1)
        for atributo in (20, 19):
            try:
                resultado = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    atributo,
                    ctypes.byref(valor),
                    ctypes.sizeof(valor),
                )
                if resultado == 0:
                    break
            except Exception:
                continue

        try:
            color_fondo = ctypes.c_uint(0x002C2316)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                35,
                ctypes.byref(color_fondo),
                ctypes.sizeof(color_fondo),
            )
        except Exception:
            pass

        try:
            color_texto = ctypes.c_uint(0x00FFFFFF)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                36,
                ctypes.byref(color_texto),
                ctypes.sizeof(color_texto),
            )
        except Exception:
            pass
    except Exception:
        pass


class _MessageBoxOscuro(QMessageBox):
    def showEvent(self, event):
        super().showEvent(event)
        _activar_barra_titulo_oscura(self)


class TarjetaCuenta(QWidget):
    """Widget de una cuenta con botón de '...' flotante para remover."""
    cuenta_seleccionada = Signal(dict)
    cuenta_removida = Signal(dict)

    def __init__(
        self,
        cuenta: dict,
        client,
        network: QNetworkAccessManager,
        ancho: int = 140,
        alto: int = 190,
        parent=None,
    ):
        super().__init__(parent)
        self._cuenta = cuenta
        self._client = client
        self._network = network
        self._ancho = ancho
        self._alto = alto
        self._alto_foto = alto - 34
        self._escala = ancho / 140

        self.setFixedSize(ancho, alto)
        self.setAttribute(Qt.WA_Hover)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Botón principal (avatar)
        self.btn_avatar = QPushButton()
        self.btn_avatar.setFixedSize(ancho, self._alto_foto)
        self.btn_avatar.setCursor(Qt.PointingHandCursor)
        self.btn_avatar.setStyleSheet("""
            QPushButton {
                background-color: #16232c;
                border: 1px solid #22323d;
                border-radius: 10px;
            }
            QPushButton:hover { border: 1px solid #2eb8ff; }
        """)
        self.btn_avatar.clicked.connect(lambda: self.cuenta_seleccionada.emit(self._cuenta))
        layout.addWidget(self.btn_avatar)

        # Nombre debajo
        nombre = QLabel(cuenta.get("nombre") or "Usuario")
        nombre.setStyleSheet(
            "color: #e6edf3; "
            f"font-size: {max(9, int(12 * self._escala))}px; "
            "font-weight: 600;"
        )
        nombre.setAlignment(Qt.AlignCenter)
        nombre.setWordWrap(True)
        nombre.setFixedHeight(28)
        nombre.setToolTip(cuenta.get("nombre") or "Usuario")
        layout.addWidget(nombre)

        # Botón "..." flotante
        self.btn_menu = QPushButton("...", self)
        self.btn_menu.setFixedSize(24, 24)
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        self.btn_menu.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 170);
                color: white;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2eb8ff;
                border: 1px solid #2eb8ff;
            }
        """)
        self.btn_menu.move(ancho - 28, self._alto_foto - 28)
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
            self.btn_avatar.setStyleSheet(
                self.btn_avatar.styleSheet()
                + f"font-size: {max(28, int(48 * self._escala))}px; "
                "color: #2eb8ff;"
            )

    def _on_avatar_descargado(self, reply: QNetworkReply):
        try:
            if reply.error() != QNetworkReply.NoError:
                return
            pix = QPixmap()
            if not pix.loadFromData(bytes(reply.readAll())):
                return

            ancho = self._ancho
            alto_foto = self._alto_foto
            scaled = pix.scaled(
                QSize(ancho, alto_foto),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            left = (scaled.width() - ancho) // 2
            top = (scaled.height() - alto_foto) // 2
            recortado = scaled.copy(left, top, ancho, alto_foto)

            self.btn_avatar.setIcon(recortado)
            self.btn_avatar.setIconSize(QSize(ancho, alto_foto))
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
        self.setFixedWidth(700)
        self.setStyleSheet("QDialog { background-color: #0d181f; }")

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(40, 18, 40, 18)
        self.root.setSpacing(2)

        # Logo
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        base = Path(__file__).resolve().parents[2]
        ruta_logo = base / "assets" / "logo-mg.png"
        if ruta_logo.exists():
            pix = QPixmap(str(ruta_logo))
            if not pix.isNull():
                logo.setPixmap(pix.scaledToHeight(40, Qt.SmoothTransformation))
        self.root.addWidget(logo)

        # Título
        titulo = QLabel("Seleccionar cuenta")
        titulo.setStyleSheet("font-size: 20px; font-weight: 700; color: #ffffff;")
        titulo.setAlignment(Qt.AlignCenter)
        self.root.addWidget(titulo)

        # Subtítulo
        subtitulo = QLabel("Elige una cuenta para continuar")
        subtitulo.setStyleSheet("color: #8ea0af; font-size: 12px;")
        subtitulo.setAlignment(Qt.AlignCenter)
        self.root.addWidget(subtitulo)

        # Separación compacta entre subtítulo y tarjetas.
        self.root.addSpacing(10)

        self._tarjetas_widget = None
        self._renderizar_tarjetas()

    def _renderizar_tarjetas(self):
        if self._tarjetas_widget is not None:
            self.root.removeWidget(self._tarjetas_widget)
            self._tarjetas_widget.hide()
            self._tarjetas_widget.deleteLater()
            self._tarjetas_widget = None

        total = len(self._cuentas) + 1
        columnas = min(4, max(1, total))
        if total <= 4:
            ancho, alto = 140, 190
        else:
            ancho, alto = 110, 150
        filas = (total + columnas - 1) // columnas
        spacing = 18

        contenedor = QWidget()
        contenedor.setStyleSheet("background: transparent;")
        grid = QGridLayout(contenedor)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(spacing)
        grid.setAlignment(Qt.AlignCenter)

        for indice, cuenta in enumerate(self._cuentas):
            tarjeta = TarjetaCuenta(
                cuenta, self._client, self._network, ancho, alto
            )
            tarjeta.cuenta_seleccionada.connect(self.cuenta_seleccionada.emit)
            tarjeta.cuenta_removida.connect(self._on_remover_cuenta)
            grid.addWidget(
                tarjeta, indice // columnas, indice % columnas, Qt.AlignCenter
            )

        indice_add = len(self._cuentas)
        grid.addWidget(
            self._crear_boton_agregar(ancho, alto),
            indice_add // columnas,
            indice_add % columnas,
            Qt.AlignCenter,
        )

        ancho_grid = columnas * ancho + (columnas - 1) * spacing
        alto_grid = filas * alto + (filas - 1) * spacing
        contenedor.setFixedSize(ancho_grid, alto_grid)

        filas_visibles = min(filas, 3)
        alto_dialogo = (
            140 + filas_visibles * alto + (filas_visibles - 1) * spacing
        )
        self.setFixedHeight(max(300, alto_dialogo))

        if filas <= 3:
            self.root.addWidget(contenedor, 0, Qt.AlignHCenter)
            self._tarjetas_widget = contenedor
            return

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.viewport().setAutoFillBackground(False)
        scroll.setWidget(contenedor)
        scroll.setFixedHeight(3 * alto + 2 * spacing)
        self.root.addWidget(scroll)
        self._tarjetas_widget = scroll

    def _crear_boton_agregar(self, ancho: int, alto: int) -> QWidget:
        alto_foto = alto - 34
        contenedor = QWidget()
        contenedor.setFixedSize(ancho, alto)
        contenedor.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        btn = QPushButton("+")
        btn.setFixedSize(ancho, alto_foto)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #16232c;
                border: 1px solid #22323d;
                border-radius: 10px;
                color: #8ea0af;
                font-size: {max(28, int(48 * ancho / 140))}px;
                font-weight: 300;
            }}
            QPushButton:hover {{
                border: 1px solid #2eb8ff;
                color: #2eb8ff;
                background-color: rgba(33, 150, 243, 0.08);
            }}
        """)
        btn.clicked.connect(self._on_agregar_cuenta)
        layout.addWidget(btn)

        texto = QLabel("Añadir cuenta")
        texto.setStyleSheet(
            "color: #e6edf3; "
            f"font-size: {max(9, int(12 * ancho / 140))}px; "
            "font-weight: 600;"
        )
        texto.setAlignment(Qt.AlignCenter)
        texto.setWordWrap(True)
        texto.setFixedHeight(28)
        layout.addWidget(texto)

        return contenedor

    def _confirmar_descarte(self, nombre: str) -> bool:
        caja = _MessageBoxOscuro(self)
        caja.setWindowTitle("Descartar cuenta")
        caja.setIcon(QMessageBox.Warning)
        caja.setTextFormat(Qt.PlainText)
        caja.setText(f"¿Descartar la cuenta de {nombre}?")
        caja.setInformativeText(
            "Se borrarán sus datos guardados en este equipo."
        )
        caja.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        caja.setDefaultButton(QMessageBox.No)

        botones = caja.findChild(QDialogButtonBox)
        if botones is not None:
            botones.setCenterButtons(True)

        btn_si = caja.button(QMessageBox.Yes)
        btn_no = caja.button(QMessageBox.No)
        btn_si.setText("Sí")
        btn_no.setText("No")
        btn_si.setObjectName("btnSi")
        btn_no.setObjectName("btnNo")
        for boton in (btn_si, btn_no):
            boton.setFixedSize(64, 28)
            boton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        caja.setStyleSheet("""
            QMessageBox {
                background-color: #0d181f;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QDialogButtonBox {
                background: transparent;
            }
            QMessageBox QPushButton {
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 600;
                padding: 0px 10px;
            }
            QMessageBox QPushButton#btnSi {
                background-color: #2196f3;
                border: 1px solid #2196f3;
            }
            QMessageBox QPushButton#btnSi:hover {
                background-color: #42a5f5;
                border: 1px solid #42a5f5;
            }
            QMessageBox QPushButton#btnNo {
                background-color: #263238;
                border: 1px solid #37474f;
            }
            QMessageBox QPushButton#btnNo:hover {
                background-color: #37474f;
                border: 1px solid #455a64;
            }
        """)

        return caja.exec() == QMessageBox.Yes

    def _on_remover_cuenta(self, cuenta: dict):
        email = (cuenta.get("email") or "").strip()
        if not email:
            return
        nombre = cuenta.get("nombre") or email
        if not self._confirmar_descarte(nombre):
            return
        self._cuentas = [
            c for c in self._cuentas
            if (c.get("email") or "").strip().casefold() != email.casefold()
        ]
        self.cuenta_removida.emit(cuenta)
        self._renderizar_tarjetas()  # Volver a pintar sin la cuenta eliminada

    def _on_agregar_cuenta(self):
        self.hide()
        self.agregar_cuenta.emit()

    def showEvent(self, event):
        super().showEvent(event)
        _activar_barra_titulo_oscura(self)

    def closeEvent(self, event):
        self.cerrado.emit()
        super().closeEvent(event)