# app/ui/dialogs/registro.py
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox,
)

from app.styles.colors import (
    COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT, COLOR_INPUT_BG,
    COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    RADIO_INPUT,
)


ANCHO_DIALOGO = 400
ALTO_INPUT = 34
ALTO_BOTON = 30
LOGO_MAX_W = 130
LOGO_MAX_H = 32


class DialogoRegistro(QDialog):
    """Diálogo para crear una cuenta nueva."""

    ir_a_login = Signal()   # ⬅️ FIX: indentación correcta

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear cuenta")
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_PANEL}; }}")

        self._armar_ui()
        self._ajustar_altura()

    def showEvent(self, event):
        super().showEvent(event)
        self._ajustar_altura()

    def _ajustar_altura(self):
        self.layout().invalidate()
        self.layout().activate()
        self.setFixedSize(
            ANCHO_DIALOGO, max(self.layout().sizeHint().height(), 200)
        )

    # ============================================================
    # UI
    # ============================================================
    def _armar_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---------- Header: logo + título ----------
        header = QVBoxLayout()
        header.setContentsMargins(18, 18, 18, 14)
        header.setSpacing(8)

        label_logo = self._crear_logo()
        if label_logo is not None:
            header.addWidget(label_logo, 0, Qt.AlignCenter)

        titulo = QLabel("Crear cuenta")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(f"""
            color: {COLOR_TEXTO};
            font-size: 15px;
            font-weight: 600;
            border: none;
            background: transparent;
        """)
        header.addWidget(titulo)

        layout.addLayout(header)
        layout.addWidget(self._separador())

        # ---------- Contenido ----------
        cont = QVBoxLayout()
        cont.setContentsMargins(18, 14, 18, 18)
        cont.setSpacing(6)

        cont.addWidget(self._label("Nombre"))
        self.input_nombre = self._input("Tu nombre")
        cont.addWidget(self.input_nombre)

        cont.addWidget(self._label("Apellido", top=6))
        self.input_apellido = self._input("Tu apellido")
        cont.addWidget(self.input_apellido)

        cont.addWidget(self._label("Correo", top=6))
        self.input_email = self._input("tucorreo@ejemplo.com")
        cont.addWidget(self.input_email)

        cont.addWidget(self._label("Contraseña", top=6))
        self.input_password = self._input("Mínimo 6 caracteres", password=True)
        cont.addWidget(self.input_password)

        cont.addWidget(self._label("Confirmar contraseña", top=6))
        self.input_confirm = self._input("Repite la contraseña", password=True)
        cont.addWidget(self.input_confirm)

        layout.addLayout(cont)
        layout.addWidget(self._separador())

        # ---------- Footer botones ----------
                # ---------- Footer botones ----------
        footer = QHBoxLayout()
        footer.setContentsMargins(18, 10, 18, 12)
        footer.addStretch()

        btn_guardar = QPushButton("Registrarse")
        btn_guardar.setCursor(Qt.PointingHandCursor)
        btn_guardar.setFixedHeight(38)
        btn_guardar.setMinimumWidth(180)
        btn_guardar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACENTO};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0 24px;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover    {{ background-color: {COLOR_ACENTO_HOVER}; }}
            QPushButton:pressed  {{ background-color: {COLOR_ACENTO_PRESSED}; }}
        """)
        btn_guardar.clicked.connect(self._on_guardar)
        footer.addWidget(btn_guardar)

        footer.addStretch()
        layout.addLayout(footer)

        # ---------- Link "¿Ya tienes una cuenta?" ----------
        footer_login = QHBoxLayout()
        footer_login.setContentsMargins(18, 0, 18, 16)
        footer_login.setSpacing(2)
        footer_login.addStretch()

        texto_ya = QLabel("¿Ya tienes una cuenta?")
        texto_ya.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            background: transparent;
            border: none;
        """)
        footer_login.addWidget(texto_ya)

        btn_ir_login = QPushButton("Iniciar sesión")
        btn_ir_login.setCursor(Qt.PointingHandCursor)
        btn_ir_login.setFlat(True)
        btn_ir_login.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {COLOR_ACENTO};
                font-size: 11px;
                font-weight: 600;
                padding: 0 2px;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {COLOR_ACENTO_HOVER};
                text-decoration: underline;
            }}
        """)
        btn_ir_login.clicked.connect(self._on_ir_login)
        footer_login.addWidget(btn_ir_login)

        footer_login.addStretch()
        layout.addLayout(footer_login)

        # ---------- Atajos ----------
        self.input_nombre.returnPressed.connect(lambda: self.input_apellido.setFocus())
        self.input_apellido.returnPressed.connect(lambda: self.input_email.setFocus())
        self.input_email.returnPressed.connect(lambda: self.input_password.setFocus())
        self.input_password.returnPressed.connect(lambda: self.input_confirm.setFocus())
        self.input_confirm.returnPressed.connect(self._on_guardar)
        self.input_nombre.setFocus()

    # ============================================================
    # Logo
    # ============================================================
    def _crear_logo(self):
        """Devuelve un QLabel con el logo o None si no se encuentra."""
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        ruta_logo = os.path.join(base_dir, "assets", "logo-mg.png")
        pixmap = QPixmap(ruta_logo)

        if pixmap.isNull():
            return None

        dpr = self.devicePixelRatioF()
        pixmap = pixmap.scaled(
            int(LOGO_MAX_W * dpr),
            int(LOGO_MAX_H * dpr),
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
        return label_logo

    # ============================================================
    # Helpers
    # ============================================================
    def _separador(self):
        l = QFrame()
        l.setFrameShape(QFrame.HLine)
        l.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        l.setFixedHeight(1)
        return l

    def _label(self, texto, top=0):
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            border: none;
            background: transparent;
            margin-top: {top}px;
        """)
        return lbl

    def _input(self, placeholder, password=False):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        if password:
            inp.setEchoMode(QLineEdit.Password)
        inp.setFixedHeight(ALTO_INPUT)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QLineEdit::placeholder {{ color: {COLOR_TEXTO_TERCIARIO}; }}
        """)
        return inp

    # ============================================================
    # Acciones
    # ============================================================
    def _on_ir_login(self):
        """Cierra el diálogo y avisa que se quiere ir al login."""
        self.ir_a_login.emit()
        self.reject()

    # ============================================================
    # Guardar
    # ============================================================
    def _on_guardar(self):
        nombre = self.input_nombre.text().strip()
        apellido = self.input_apellido.text().strip()
        email = self.input_email.text().strip()
        password = self.input_password.text()
        confirm = self.input_confirm.text()

        if not nombre or not apellido:
            QMessageBox.warning(self, "Datos incompletos",
                                "Ingresa tu nombre y apellido.")
            return

        if not email or "@" not in email:
            QMessageBox.warning(self, "Correo inválido",
                                "Ingresa un correo válido.")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Contraseña corta",
                                "Mínimo 6 caracteres.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Contraseñas no coinciden",
                                "Verifica que sean iguales.")
            return

        self.accept()

    def datos(self) -> tuple[str, str, str, str]:
        return (
            self.input_nombre.text().strip(),
            self.input_apellido.text().strip(),
            self.input_email.text().strip(),
            self.input_password.text(),
        )