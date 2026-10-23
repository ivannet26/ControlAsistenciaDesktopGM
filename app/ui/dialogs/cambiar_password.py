from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.styles.colors import (
    COLOR_FONDO,
    COLOR_PANEL,
    COLOR_BORDE_INPUT,
    COLOR_INPUT_BG,
    COLOR_TEXTO,
    COLOR_TEXTO_SECUNDARIO,
    COLOR_ACENTO,
    RADIO_INPUT,
    RADIO_BOTON,
)
from app.utils.workers import ApiWorker


class DialogoCambiarPassword(QDialog):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self._worker = None
        self._workers = []

        self.setWindowTitle("Cambiar contraseña")
        self.setModal(True)
        self.setMinimumWidth(320)  # Reducido de 360 a 320
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_FONDO};
            }}
            QLabel {{
                color: {COLOR_TEXTO};
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 8px;       /* Reducido */
                font-size: 12px;
                min-height: 20px;       /* Reducido de 24 a 20 */
            }}
            QLineEdit:focus {{
                border: 1px solid {COLOR_ACENTO};
            }}
            QPushButton {{
                background-color: {COLOR_PANEL};
                color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_BOTON}px;
                padding: 4px 14px;      /* Reducido */
                font-size: 12px;
                font-weight: 600;
                min-height: 24px;       /* Reducido de 28 a 24 */
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACENTO};
                color: #ffffff;
            }}
            QPushButton#btnGuardar {{
                background-color: {COLOR_ACENTO};
                color: #ffffff;
                border: none;
            }}
            QPushButton#btnGuardar:hover {{
                background-color: #1e9ae0;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)  # Márgenes reducidos
        layout.setSpacing(10)

        formulario = QFormLayout()
        formulario.setSpacing(8)  # Espacio entre filas reducido

        self.password_actual = QLineEdit()
        self.password_actual.setEchoMode(QLineEdit.Password)
        self.password_actual.setObjectName("password_actual")
        formulario.addRow("Contraseña actual:", self.password_actual)

        self.password_nueva = QLineEdit()
        self.password_nueva.setEchoMode(QLineEdit.Password)
        self.password_nueva.setObjectName("password_nueva")
        formulario.addRow("Nueva contraseña:", self.password_nueva)

        self.password_confirmacion = QLineEdit()
        self.password_confirmacion.setEchoMode(QLineEdit.Password)
        self.password_confirmacion.setObjectName("password_confirmacion")
        self.password_confirmacion.returnPressed.connect(self._guardar)
        formulario.addRow("Confirmar contraseña:", self.password_confirmacion)

        layout.addLayout(formulario)

        botones = QHBoxLayout()
        botones.addStretch()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("btnGuardar")
        self.btn_guardar.setDefault(True)
        self.btn_guardar.clicked.connect(self._guardar)
        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_guardar)
        layout.addLayout(botones)

    def _guardar(self):
        password_actual = self.password_actual.text()
        password_nueva = self.password_nueva.text()

        if password_nueva != self.password_confirmacion.text():
            QMessageBox.warning(
                self,
                "Contraseñas distintas",
                "La nueva contraseña y su confirmación no coinciden.",
            )
            return

        if not password_actual or not password_nueva:
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Ingresa la contraseña actual y la nueva contraseña.",
            )
            return

        self.btn_guardar.setEnabled(False)
        self.btn_cancelar.setEnabled(False)
        self._worker = ApiWorker(
            self.client.cambiar_mi_password,
            password_actual,
            password_nueva,
        )
        self._worker.exito.connect(self._on_exito)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(
            lambda worker=self._worker: self._on_worker_finished(worker)
        )
        self._workers.append(self._worker)
        self._worker.start()

    def _on_exito(self, _resultado):
        QMessageBox.information(
            self,
            "Éxito",
            "Contraseña actualizada correctamente",
        )
        self.accept()

    def _on_error(self, mensaje):
        QMessageBox.critical(self, "Error", str(mensaje))
        self.btn_guardar.setEnabled(True)
        self.btn_cancelar.setEnabled(True)

    def _on_worker_finished(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)
        if self._worker is worker:
            self._worker = None
        worker.deleteLater()

    def reject(self):
        if self._worker is not None and self._worker.isRunning():
            return
        super().reject()

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            event.ignore()
            return
        super().closeEvent(event)