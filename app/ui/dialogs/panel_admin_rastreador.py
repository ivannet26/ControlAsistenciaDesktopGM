# app/ui/dialogs/panel_admin_rastreador.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget
)
from app.ui.dialogs.rastreador_auto import VentanaRastreadorAuto
from app.ui.custom_title_bar import CustomTitleBar


class PanelAdminRastreador(QDialog):
    ALTO_FILA = 48
    ANCHO_ACCIONES = 210

    def __init__(self, client, parent=None, tracker_window=None):
        super().__init__(parent)
        self.client = client
        self.tracker_window = tracker_window  
        self._ventanas_vivo = {}

        self.setWindowTitle("Panel de Administración - Monitoreo en Vivo")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(900, 600)


        self.setStyleSheet("""
            QDialog {
                background-color: #0d181f;
                border: 1px solid #22323d;
                border-radius: 8px;
            }
            QWidget#contenido {
                background-color: #0d181f;
            }
            QLabel {
                color: #e6edf3;
                font-size: 13px;
            }
            QLabel#titulo {
                font-size: 18px;
                font-weight: bold;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #0d181f;
                alternate-background-color: #111f28;
                color: #e6edf3;
                border: 1px solid #22323d;
                font-size: 13px;
                outline: 0;
            }
            QTableWidget::item {
                padding-left: 10px;
                border-bottom: 1px solid #1a2933;
            }
            QTableWidget::item:selected {
                background-color: #1b3a4b;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #16232c;
                color: #8ea0af;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-bottom: 1px solid #22323d;
                padding: 10px;
            }
            QPushButton#btnVivo {
    background-color: #0f2a3d;
    color: #2eb8ff;
    border: 1px solid #1e6fa8;
    border-radius: 4px;
    padding: 0px 12px;
    font-weight: bold;
    font-size: 12px;
    min-height: 30px;
}
QPushButton#btnVivo:hover {
    background-color: #153a54;
    border-color: #2eb8ff;
    color: #ffffff;
}
QPushButton#btnVivo:pressed {
    background-color: #0b2233;
}
            QScrollBar:vertical {
                background: #0d181f;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #2a3a45;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #3a4a55; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = CustomTitleBar(
            self, "Monitoreo en Vivo - Administrador",
            mostrar_maximizar=True, mostrar_minimizar=True
        )
        layout.addWidget(self.title_bar)

        # Contenedor (objectName para que su estilo NO se propague a los hijos)
        contenido_widget = QWidget()
        contenido_widget.setObjectName("contenido")
        contenido = QVBoxLayout(contenido_widget)
        contenido.setContentsMargins(20, 20, 20, 20)
        contenido.setSpacing(12)

        lbl_titulo = QLabel("Usuarios en el sistema")
        lbl_titulo.setObjectName("titulo")
        contenido.addWidget(lbl_titulo)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Acciones"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(self.ALTO_FILA)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setFocusPolicy(Qt.NoFocus)          # quita el recuadro punteado
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        h = self.tabla.horizontalHeader()
        h.setHighlightSections(False)
        h.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        self.tabla.setColumnWidth(0, 60)
        self.tabla.setColumnWidth(3, self.ANCHO_ACCIONES)

        contenido.addWidget(self.tabla)
        layout.addWidget(contenido_widget)

        self._cargar_usuarios()

    def _crear_item(self, texto, centrado=False):
        item = QTableWidgetItem(texto)
        alineacion = Qt.AlignCenter if centrado else (Qt.AlignLeft | Qt.AlignVCenter)
        item.setTextAlignment(alineacion)
        return item

    def _cargar_usuarios(self):
        """Hace una petición al backend para obtener la lista de usuarios."""
        try:
            usuarios = self.client.listar_usuarios()
        except AttributeError:
            print("[ADMIN] ⚠️ El ApiClient no tiene el método 'listar_usuarios'")
            usuarios = []
        except Exception as e:
            print(f"[ADMIN] ❌ Error cargando usuarios: {e}")
            usuarios = []

        self.tabla.setRowCount(0)
        for u in usuarios:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setRowHeight(fila, self.ALTO_FILA)

            nombre_completo = f"{u.get('nombre', '')} {u.get('apellido', '')}".strip()
            self.tabla.setItem(fila, 0, self._crear_item(str(u.get("id", ""))))
            self.tabla.setItem(fila, 1, self._crear_item(nombre_completo))
            self.tabla.setItem(fila, 2, self._crear_item(u.get("email", "")))

            # Botón dentro de un contenedor con márgenes => centrado y sin cortarse
            btn = QPushButton("Visualizar Rastreador")
            btn.setObjectName("btnVivo")
            btn.setCursor(Qt.PointingHandCursor)
            usuario = {
                campo: u.get(campo)
                for campo in ("id", "nombre", "apellido", "email")
            }
            btn.clicked.connect(
                lambda checked=False, uid=u.get("id"), nombre=u.get("nombre"), datos=usuario:
                self._abrir_monitor(uid, nombre, datos)
            )

            contenedor = QWidget()
            lay = QHBoxLayout(contenedor)
            lay.setContentsMargins(10, 6, 10, 6)
            lay.addWidget(btn)
            self.tabla.setCellWidget(fila, 3, contenedor)

    def _abrir_monitor(self, usuario_id, nombre, usuario=None):
        """Abre la ventana del rastreador conectada al WebSocket de este usuario."""
        if usuario_id in self._ventanas_vivo and self._ventanas_vivo[usuario_id].isVisible():
            self._ventanas_vivo[usuario_id].raise_()
            self._ventanas_vivo[usuario_id].activateWindow()
            return

        print(f"[ADMIN] Abriendo monitor en vivo para {nombre} (ID: {usuario_id})")
        
        # --- USAMOS LA REFERENCIA QUE GUARDAMOS EN EL __init__ ---
        cb = None
        if self.tracker_window and hasattr(self.tracker_window, "obtener_registros_rastreador"):
            cb = self.tracker_window.obtener_registros_rastreador
            print("[ADMIN] ✓ Callback encontrado")
        else:
            print("[ADMIN] ⚠️ No se encontró el TrackerWindow")

        # Creamos la ventana SIN parent (independiente) pero CON callback
        ventana = VentanaRastreadorAuto(
            parent=None,                  
            cargar_datos_cb=cb,           
            usuario_id=usuario_id,
            registros=[],  
            grupo=[],
            usuario=usuario or {},
        )
        ventana.setWindowTitle(f"Monitoreo en Vivo: {nombre}")
        
        self._ventanas_vivo[usuario_id] = ventana
        ventana.show()