import json
import logging
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtWebSockets import QWebSocket

logger = logging.getLogger(__name__)

class RastreadorWebSocket(QObject):
    # Señales que emitirá hacia la interfaz
    conectado = Signal()
    desconectado = Signal()
    datos_recibidos = Signal(dict) # Recibe el JSON con la nueva actividad
    error = Signal(str)

    def __init__(self, base_url: str, token: str, usuario_id_vigilar: int, parent=None):
        super().__init__(parent)
        self.ws = QWebSocket()
        self.ws.connected.connect(self._on_connected)
        self.ws.disconnected.connect(self._on_disconnected)
        self.ws.textMessageReceived.connect(self._on_message)
        self.ws.errorOccurred.connect(self._on_error)
        
        # Construimos la URL del WebSocket
        # Ej: wss://backendcontrolasistenciagm.onrender.com/rastreador/ws/rastreador/6?token=abc
        ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        self.url = f"{ws_url}/rastreador/ws/rastreador/{usuario_id_vigilar}?token={token}"
        
        self._usuario_id = usuario_id_vigilar

    def conectar(self):
        logger.info(f"Conectando WebSocket a: {self.url}")
        self.ws.open(QUrl(self.url))

    def desconectar(self):
        self.ws.close()

    def _on_connected(self):
        logger.info("✅ WebSocket Conectado")
        self.conectado.emit()

    def _on_disconnected(self):
        logger.info("❌ WebSocket Desconectado")
        self.desconectado.emit()

    def _on_message(self, message: str):
        try:
            data = json.loads(message)
            self.datos_recibidos.emit(data)
        except json.JSONDecodeError:
            logger.error(f"Error decodificando JSON: {message}")

    def _on_error(self, error):
        logger.error(f"Error de WebSocket: {error}")
        self.error.emit(str(error))