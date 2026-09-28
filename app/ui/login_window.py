# app/ui/login_window.py
import os

from PySide6.QtCore import Qt, QThread, Signal, QTimer, QRectF, QSize, QEvent
from PySide6.QtGui import (
    QPixmap, QColor, QIcon, QPainter, QPen, QBrush, QPainterPath,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect,
    QCheckBox, QDialog, QToolButton,
)

from app.services.api_client import ApiClient, ApiError
from app.services.sesion import guardar_credenciales, cargar_credenciales
from app.styles import login as L
from app.ui.dialogs.registro import DialogoRegistro
from app.ui.dialogs.alerta import alerta_error, alerta_exito

LOGO_MAX_W = 150
LOGO_MAX_H = 36


# ============================================================
# WORKER LOGIN
# ============================================================
class LoginWorker(QThread):
    exito = Signal(dict)
    error = Signal(str)

    def __init__(self, client: ApiClient, email: str, password: str):
        super().__init__()
        self.client = client
        self.email = email
        self.password = password

    def run(self):
        try:
            usuario = self.client.login(self.email, self.password)
            self.exito.emit(usuario)
        except ApiError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}")


# ============================================================
# WORKER REGISTRO
# ============================================================
class RegistroWorker(QThread):
    exito = Signal(dict)
    error = Signal(str)

    def __init__(self, client: ApiClient, nombre, apellido, email, password):
        super().__init__()
        self.client = client
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.password = password

    def run(self):
        try:
            usuario = self.client.registrar(
                nombre=self.nombre,
                apellido=self.apellido,
                email=self.email,
                password=self.password,
            )
            self.exito.emit(usuario)
        except ApiError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}")


# ============================================================
# LOGIN WINDOW
# ============================================================
class LoginWindow(QWidget):
    login_exitoso = Signal(dict)

    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client
        self.worker = None
        self.worker_registro = None

        self._password_visible = False

        self.setWindowTitle("Control de Asistencia - Iniciar sesión")
        self.setWindowFlag(Qt.FramelessWindowHint)
        # ✅ Elimina el borde fantasma de Windows
        self.setAttribute(Qt.WA_TranslucentBackground)
        # ❌ NO aplicar setStyleSheet aquí: taparía la barra blanca

        self._armar_ui()
        self._cargar_credenciales_guardadas()

        QTimer.singleShot(0, self._ajustar_tamano)

    def _ajustar_tamano(self):
        self.layout().activate()
        self.adjustSize()
        self.setFixedSize(self.size())
        QTimer.singleShot(0, self._posicionar_boton_ojo)

    # -------------------- UI --------------------
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barra personalizada (blanca, sin bordes fantasma)
        self.title_bar = CustomTitleBar(
            self,
            "Control de Asistencia",
            mostrar_maximizar=False,
        )
        root.addWidget(self.title_bar)

        # Contenedor con el fondo oscuro
        contenido = QWidget()
        contenido.setObjectName("contenidoLogin")
        # ✅ Necesario para que el background-color del QSS se pinte
        contenido.setAttribute(Qt.WA_StyledBackground, True)
        contenido.setStyleSheet(
            f"QWidget#contenidoLogin {{ background-color: {L.LOGIN_BG_RIGHT}; }}"
        )
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(24, 24, 24, 24)
        contenido_layout.setSpacing(0)
        contenido_layout.addWidget(self._construir_card())
        root.addWidget(contenido)

    def _construir_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(360)
        card.setStyleSheet(L.QSS_CARD)

        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(30)
        sombra.setColor(QColor(0, 0, 0, 130))
        sombra.setOffset(0, 8)
        card.setGraphicsEffect(sombra)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(0)

        # ---- Logo ----
        layout.addLayout(self._construir_logo())
        layout.addSpacing(18)

        # ---- Título ----
        titulo = QLabel("Iniciar sesión")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(L.QSS_TITULO_SESION)
        layout.addWidget(titulo)
        layout.addSpacing(22)

        # ---- Correo ----
        label_correo = QLabel("Correo")
        label_correo.setStyleSheet(L.QSS_LABEL_FIELD)
        layout.addWidget(label_correo)
        layout.addSpacing(6)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ingrese su correo")
        self.email_input.setStyleSheet(L.QSS_INPUT)
        self.email_input.setFixedHeight(40)
        layout.addWidget(self.email_input)
        layout.addSpacing(12)

        # ---- Contraseña ----
        label_pass = QLabel("Contraseña")
        label_pass.setStyleSheet(L.QSS_LABEL_FIELD)
        layout.addWidget(label_pass)
        layout.addSpacing(6)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)

        qss_pass = L.QSS_INPUT + f"""
            QLineEdit {{
                padding-right: 42px;
            }}
        """
        self.password_input.setStyleSheet(qss_pass)
        self.password_input.installEventFilter(self)

        # ---- Botón flotante del ojo ----
        self.btn_ver_pass = QToolButton(self.password_input)
        self.btn_ver_pass.setCursor(Qt.PointingHandCursor)
        self.btn_ver_pass.setIcon(self._crear_icono_ojo_icon(False))
        self.btn_ver_pass.setIconSize(QSize(18, 18))
        self.btn_ver_pass.setFixedSize(32, 32)
        self.btn_ver_pass.setToolTip("Mostrar contraseña")
        self.btn_ver_pass.setFocusPolicy(Qt.NoFocus)
        self.btn_ver_pass.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 0;
                margin: 0;
            }
            QToolButton:hover {
                background-color: rgba(33, 150, 243, 0.15);
            }
            QToolButton:pressed {
                background-color: rgba(33, 150, 243, 0.30);
            }
        """)
        self.btn_ver_pass.clicked.connect(self._toggle_password)
        self.btn_ver_pass.show()

        layout.addWidget(self.password_input)
        layout.addSpacing(12)

        # ---- Checkbox ----
        self.check_recordar = QCheckBox("Recordar credenciales")
        self.check_recordar.setCursor(Qt.PointingHandCursor)
        self.check_recordar.setStyleSheet(f"""
            QCheckBox {{
                color: {L.COLOR_TEXTO_SECUNDARIO};
                font-size: 11px;
                spacing: 6px;
                border: none;
                background: transparent;
                padding: 0;
            }}
            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
                border-radius: 2px;
                border: 1px solid {L.COLOR_BORDE_INPUT};
                background-color: {L.COLOR_INPUT_BG};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {L.COLOR_ACENTO};
            }}
            QCheckBox::indicator:checked {{
                background-color: {L.COLOR_ACENTO};
                border: 1px solid {L.COLOR_ACENTO};
            }}
        """)
        self.check_recordar.setChecked(True)
        layout.addWidget(self.check_recordar)
        layout.addSpacing(16)

        # ---- Botón Ingresar ----
        self.boton_login = QPushButton("Ingresar")
        self.boton_login.setCursor(Qt.PointingHandCursor)
        self.boton_login.setStyleSheet(L.QSS_BOTON)
        self.boton_login.setFixedHeight(42)
        self.boton_login.clicked.connect(self._on_login_click)
        layout.addWidget(self.boton_login)
        layout.addSpacing(14)

        # ---- Footer ----
        footer = QHBoxLayout()
        footer.setSpacing(2)
        footer.addStretch()

        texto = QLabel("¿No tienes cuenta?")
        texto.setStyleSheet(L.QSS_FOOTER_TEXTO)
        footer.addWidget(texto)

        self.boton_registrar = QPushButton("Registrarse")
        self.boton_registrar.setCursor(Qt.PointingHandCursor)
        self.boton_registrar.setFlat(True)
        self.boton_registrar.setStyleSheet(L.QSS_FOOTER_LINK)
        self.boton_registrar.clicked.connect(self._on_registrar)
        footer.addWidget(self.boton_registrar)

        footer.addStretch()
        layout.addLayout(footer)

        # Atajos
        self.password_input.returnPressed.connect(self._on_login_click)
        self.email_input.returnPressed.connect(
            lambda: self.password_input.setFocus()
        )

        return card

    def _construir_logo(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_logo = os.path.join(base_dir, "assets", "logo-mg.png")
        pixmap = QPixmap(ruta_logo)

        if not pixmap.isNull():
            dpr = self.devicePixelRatioF()
            pixmap = pixmap.scaled(
                int(LOGO_MAX_W * dpr), int(LOGO_MAX_H * dpr),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            pixmap.setDevicePixelRatio(dpr)

            label_logo = QLabel()
            label_logo.setPixmap(pixmap)
            label_logo.setAlignment(Qt.AlignCenter)
            label_logo.setStyleSheet(
                "background: transparent; border: none; padding: 0;"
            )
            layout.addWidget(label_logo, 0, Qt.AlignCenter)

        return layout

    # ============================================================
    # Reposicionar el botón del ojo
    # ============================================================
    def eventFilter(self, obj, event):
        if obj is self.password_input and event.type() == QEvent.Resize:
            self._posicionar_boton_ojo()
        return super().eventFilter(obj, event)

    def _posicionar_boton_ojo(self):
        if not hasattr(self, "btn_ver_pass"):
            return
        x = self.password_input.width() - self.btn_ver_pass.width() - 4
        y = (self.password_input.height() - self.btn_ver_pass.height()) // 2
        self.btn_ver_pass.move(x, y)

    # ============================================================
    # Icono del ojo
    # ============================================================
    def _crear_icono_ojo_icon(self, abierto: bool) -> QIcon:
        gris = "#8ea0af"
        claro = "#ffffff"
        azul = "#2196f3"

        icon = QIcon()
        icon.addPixmap(
            self._crear_pixmap_ojo(abierto, 18, gris),
            QIcon.Normal, QIcon.Off,
        )
        icon.addPixmap(
            self._crear_pixmap_ojo(abierto, 18, claro),
            QIcon.Active, QIcon.Off,
        )
        icon.addPixmap(
            self._crear_pixmap_ojo(abierto, 18, azul),
            QIcon.Selected, QIcon.Off,
        )
        return icon

    def _crear_pixmap_ojo(self, abierto: bool, size: int, color: str) -> QPixmap:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(color))
        pen.setWidthF(1.5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        path = QPainterPath()
        path.moveTo(2, size / 2)
        path.quadTo(size / 2, 2, size - 2, size / 2)
        path.quadTo(size / 2, size - 2, 2, size / 2)
        painter.drawPath(path)

        r = size / 6.5
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(
            QRectF(size / 2 - r, size / 2 - r, r * 2, r * 2)
        )

        if not abierto:
            pen2 = QPen(QColor(color))
            pen2.setWidthF(1.7)
            pen2.setCapStyle(Qt.RoundCap)
            painter.setPen(pen2)
            painter.drawLine(3, size - 3, size - 3, 3)

        painter.end()
        return pixmap

    def _toggle_password(self):
        self._password_visible = not self._password_visible

        if self._password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.btn_ver_pass.setIcon(self._crear_icono_ojo_icon(True))
            self.btn_ver_pass.setToolTip("Ocultar contraseña")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.btn_ver_pass.setIcon(self._crear_icono_ojo_icon(False))
            self.btn_ver_pass.setToolTip("Mostrar contraseña")

    # -------------------- Credenciales --------------------
    def _cargar_credenciales_guardadas(self):
        email, password, recordar = cargar_credenciales()
        if recordar:
            self.email_input.setText(email)
            self.password_input.setText(password)
            self.check_recordar.setChecked(True)
            self.boton_login.setFocus()
        else:
            self.check_recordar.setChecked(False)
            self.email_input.setFocus()

    # -------------------- Acciones: LOGIN --------------------
    def _on_login_click(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(
                self, "Datos incompletos",
                "Ingresa tu correo y contraseña."
            )
            return

        self.boton_login.setEnabled(False)
        self.boton_login.setText("Ingresando...")

        self.worker = LoginWorker(self.client, email, password)
        self.worker.exito.connect(self._on_login_ok)
        self.worker.error.connect(self._on_login_error)
        self.worker.start()

    def _on_login_ok(self, usuario: dict):
        self.boton_login.setEnabled(True)
        self.boton_login.setText("Ingresar")

        guardar_credenciales(
            email=self.email_input.text().strip(),
            password=self.password_input.text(),
            recordar=self.check_recordar.isChecked(),
        )

        from app.services.sesion import guardar_token
        guardar_token(self.client.token or "")

        self.login_exitoso.emit(usuario)

    def _on_login_error(self, mensaje: str):
        self.boton_login.setEnabled(True)
        self.boton_login.setText("Ingresar")
        QMessageBox.critical(self, "Error al iniciar sesión", mensaje)

    # -------------------- Acciones: REGISTRO --------------------
    def _on_registrar(self):
        self.hide()

        dlg = DialogoRegistro(self)
        dlg.ir_a_login.connect(self._volver_al_login)

        resultado = dlg.exec()

        self.show()
        self.raise_()
        self.activateWindow()

        if resultado != QDialog.Accepted:
            return

        nombre, apellido, email, password = dlg.datos()

        self.boton_registrar.setEnabled(False)
        self.boton_registrar.setText("Creando...")

        self.worker_registro = RegistroWorker(
            self.client, nombre, apellido, email, password
        )
        self.worker_registro.exito.connect(
            lambda _: self._on_registro_ok(email, password)
        )
        self.worker_registro.error.connect(self._on_registro_error)
        self.worker_registro.start()

    def _volver_al_login(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.email_input.setFocus()

    def _on_registro_ok(self, email: str, password: str):
        self.boton_registrar.setEnabled(True)
        self.boton_registrar.setText("Registrarse")

        self.email_input.setText(email)
        self.password_input.setText(password)
        self.password_input.setFocus()

        alerta_exito(
            padre=self,
            titulo="Cuenta creada",
            mensaje="Tu cuenta se creó correctamente.\n"
                    "Ya puedes iniciar sesión.",
        )

    def _on_registro_error(self, mensaje: str):
        self.boton_registrar.setEnabled(True)
        self.boton_registrar.setText("Registrarse")

        alerta_error(
            padre=self,
            titulo="Error al registrar",
            mensaje=mensaje,
        )