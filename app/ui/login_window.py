from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)

from app.services.api_client import ApiClient, ApiError


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


class LoginWindow(QWidget):
    login_exitoso = Signal(dict)

    def __init__(self, client: ApiClient):
        super().__init__()
        self.client = client
        self.worker = None
        self.setWindowTitle("Control de Asistencia - Iniciar sesión")
        self.setFixedSize(360, 320)
        self._armar_ui()

    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(14)

        titulo = QLabel("Control de Asistencia")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Inicia sesión para empezar a registrar tu tiempo")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet("color: #666;")
        layout.addWidget(subtitulo)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Correo electrónico")
        layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.boton_login = QPushButton("Iniciar sesión")
        self.boton_login.setStyleSheet(
            "background-color: #03a9f4; color: white; padding: 10px; border-radius: 6px; font-weight: 600;"
        )
        self.boton_login.clicked.connect(self._on_login_click)
        layout.addWidget(self.boton_login)

        self.password_input.returnPressed.connect(self._on_login_click)

        layout.addStretch()

    def _on_login_click(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingresa tu correo y contraseña.")
            return

        self.boton_login.setEnabled(False)
        self.boton_login.setText("Ingresando...")

        self.worker = LoginWorker(self.client, email, password)
        self.worker.exito.connect(self._on_login_ok)
        self.worker.error.connect(self._on_login_error)
        self.worker.start()

    def _on_login_ok(self, usuario: dict):
        self.boton_login.setEnabled(True)
        self.boton_login.setText("Iniciar sesión")
        self.login_exitoso.emit(usuario)

    def _on_login_error(self, mensaje: str):
        self.boton_login.setEnabled(True)
        self.boton_login.setText("Iniciar sesión")
        QMessageBox.critical(self, "Error al iniciar sesión", mensaje)
