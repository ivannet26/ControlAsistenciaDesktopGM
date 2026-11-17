# app/ui/dialogs/panel_admin_rastreador.py
from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QLineEdit, QFrame
)
from app.ui.dialogs.rastreador_auto import VentanaRastreadorAuto
from app.ui.custom_title_bar import CustomTitleBar

# ── Índices de columnas ──────────────────────────────────────────
COL_ID      = 0
COL_NOMBRE  = 1
COL_EMAIL   = 2
COL_ROL     = 3
COL_ACCIONES = 4


class PanelAdminRastreador(QDialog):
    ALTO_FILA    = 52
    ANCHO_ID     = 64
    ANCHO_ROL    = 110
    ANCHO_ACCIONES = 200

    def __init__(self, client, parent=None, tracker_window=None):
        super().__init__(parent)
        self.client = client
        self.tracker_window = tracker_window
        self._ventanas_vivo  = {}
        self._todos_usuarios = []
        self._orden_col      = None   # columna actualmente ordenada
        self._orden_asc      = True   # dirección del orden

        # Email del admin logueado (para resaltarlo en la tabla)
        self._email_propio = ""
        if tracker_window and hasattr(tracker_window, "usuario"):
            self._email_propio = tracker_window.usuario.get("email", "")

        self.setWindowTitle("Panel de Administración - Monitoreo en Vivo")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1020, 660)

        self._aplicar_estilos()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Barra de título ──────────────────────────────────────
        self.title_bar = CustomTitleBar(
            self, "Monitoreo en Vivo - Administrador",
            mostrar_maximizar=True, mostrar_minimizar=True
        )
        layout.addWidget(self.title_bar)

        # ── Contenedor principal ─────────────────────────────────
        contenido_widget = QWidget()
        contenido_widget.setObjectName("contenido")
        contenido = QVBoxLayout(contenido_widget)
        contenido.setContentsMargins(24, 20, 24, 20)
        contenido.setSpacing(0)

        # ── Título + contador ────────────────────────────────────
        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(12)

        lbl_titulo = QLabel("Usuarios en el sistema")
        lbl_titulo.setObjectName("titulo")

        self.lbl_contador = QLabel("")
        self.lbl_contador.setObjectName("contador")
        self.lbl_contador.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        fila_titulo.addWidget(lbl_titulo)
        fila_titulo.addWidget(self.lbl_contador)
        fila_titulo.addStretch()
        contenido.addLayout(fila_titulo)
        contenido.addSpacing(16)

        # ── Buscador + Recargar ──────────────────────────────────
        fila_busqueda = QHBoxLayout()
        fila_busqueda.setSpacing(10)

        self.buscador = QLineEdit()
        self.buscador.setObjectName("buscador")
        self.buscador.setPlaceholderText("🔍  Buscar por nombre, email o rol…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setFixedHeight(40)

        self._timer_busqueda = QTimer(self)
        self._timer_busqueda.setSingleShot(True)
        self._timer_busqueda.setInterval(200)
        self._timer_busqueda.timeout.connect(self._aplicar_filtro)
        self.buscador.textChanged.connect(lambda: self._timer_busqueda.start())

        btn_recargar = QPushButton("↻  Recargar")
        btn_recargar.setObjectName("btnRecargar")
        btn_recargar.setFixedHeight(40)
        btn_recargar.setCursor(Qt.PointingHandCursor)
        btn_recargar.clicked.connect(self._recargar)

        fila_busqueda.addWidget(self.buscador, 1)
        fila_busqueda.addWidget(btn_recargar)
        contenido.addLayout(fila_busqueda)
        contenido.addSpacing(16)

        # ── Separador ────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("separador")
        sep.setFrameShape(QFrame.HLine)
        contenido.addWidget(sep)
        contenido.addSpacing(12)

        # ── Tabla ────────────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Email", "Rol", "Acciones"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(self.ALTO_FILA)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.setShowGrid(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        h = self.tabla.horizontalHeader()
        h.setHighlightSections(False)
        h.setDefaultAlignment(Qt.AlignCenter)
        h.setFixedHeight(42)
        h.setStretchLastSection(False)
        h.setSectionResizeMode(COL_ID,       QHeaderView.Fixed)
        h.setSectionResizeMode(COL_NOMBRE,   QHeaderView.Stretch)
        h.setSectionResizeMode(COL_EMAIL,    QHeaderView.Stretch)
        h.setSectionResizeMode(COL_ROL,      QHeaderView.Fixed)
        h.setSectionResizeMode(COL_ACCIONES, QHeaderView.Fixed)
        self.tabla.setColumnWidth(COL_ID,       self.ANCHO_ID)
        self.tabla.setColumnWidth(COL_ROL,      self.ANCHO_ROL)
        self.tabla.setColumnWidth(COL_ACCIONES, self.ANCHO_ACCIONES)

        # Ordenamiento al clic en header (solo columnas de texto)
        h.sectionClicked.connect(self._ordenar_por_columna)
        h.setCursor(Qt.PointingHandCursor)

        contenido.addWidget(self.tabla)
        layout.addWidget(contenido_widget)

        self._cargar_usuarios()

    # ──────────────────────────────────────────────────────────────
    #  Estilos
    # ──────────────────────────────────────────────────────────────

    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0d181f;
                border: 1px solid #22323d;
                border-radius: 10px;
            }
            QWidget#contenido { background-color: #0d181f; }

            /* ── Título ── */
            QLabel#titulo {
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
            }
            /* ── Contador ── */
            QLabel#contador {
                font-size: 12px;
                color: #8ea0af;
            }
            /* ── Buscador ── */
            QLineEdit#buscador {
                background-color: #111f28;
                color: #e6edf3;
                border: 1px solid #2a3b47;
                border-radius: 8px;
                padding: 8px 14px 8px 36px;
                font-size: 13px;
                selection-background-color: #1e6fa8;
            }
            QLineEdit#buscador:focus { border-color: #2196f3; }
            QLineEdit#buscador::placeholder { color: #4a6070; }

            /* ── Botón recargar ── */
            QPushButton#btnRecargar {
                background-color: #111f28;
                color: #8ea0af;
                border: 1px solid #2a3b47;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                min-width: 110px;
            }
            QPushButton#btnRecargar:hover {
                background-color: #1a2e3d;
                color: #e6edf3;
                border-color: #2196f3;
            }
            QPushButton#btnRecargar:pressed { background-color: #0d181f; }

            /* ── Separador ── */
            QFrame#separador {
                background-color: #1a2933;
                border: none;
                max-height: 1px;
            }

            /* ── Tabla ── */
            QTableWidget {
                background-color: #0d181f;
                alternate-background-color: #0f1e28;
                color: #e6edf3;
                border: 1px solid #1a2933;
                border-radius: 8px;
                font-size: 13px;
                outline: 0;
                gridline-color: transparent;
            }
            QTableWidget::item {
                padding-left: 12px;
                border-bottom: 1px solid #111e28;
            }
            QTableWidget::item:selected {
                background-color: #163347;
                color: #ffffff;
            }
            QTableWidget::item:hover { background-color: #122a3a; }

            /* ── Header con cursor de ordenamiento ── */
            QHeaderView::section {
                background-color: #111f28;
                color: #8ea0af;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 0.5px;
                border: none;
                border-bottom: 2px solid #1e6fa8;
                padding: 0px 12px;
                height: 42px;
            }
            QHeaderView::section:hover {
                background-color: #162535;
                color: #c8d8e4;
            }

            /* ── Badge de rol (admin) ── */
            QLabel#badgeAdmin {
                background-color: #1a3a1a;
                color: #4caf50;
                border: 1px solid #2e7d32;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            /* ── Badge de rol (usuario) ── */
            QLabel#badgeUsuario {
                background-color: #1a2a3a;
                color: #8ea0af;
                border: 1px solid #2a3b4f;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            /* ── Badge tú mismo ── */
            QLabel#badgeYo {
                background-color: #1a2e1a;
                color: #69f06b;
                border: 1px solid #388e3c;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }

            /* ── Botón acción ── */
            QPushButton#btnVivo {
                background-color: #0f2a3d;
                color: #2eb8ff;
                border: 1px solid #1e6fa8;
                border-radius: 6px;
                padding: 0px 14px;
                font-weight: bold;
                font-size: 12px;
                min-height: 32px;
            }
            QPushButton#btnVivo:hover {
                background-color: #153a54;
                border-color: #2eb8ff;
                color: #ffffff;
            }
            QPushButton#btnVivo:pressed { background-color: #0b2233; }

            /* ── Scrollbar ── */
            QScrollBar:vertical {
                background: #0d181f;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #2a3a45;
                min-height: 30px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #3a5060; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0; background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

    # ──────────────────────────────────────────────────────────────
    #  Helpers de celda
    # ──────────────────────────────────────────────────────────────

    def _crear_item(self, texto, centrado=False, negrita=False):
        item = QTableWidgetItem(str(texto))
        alineacion = Qt.AlignCenter if centrado else (Qt.AlignLeft | Qt.AlignVCenter)
        item.setTextAlignment(alineacion)
        if negrita:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
        return item

    def _crear_badge_rol(self, rol: str, es_propio: bool) -> QWidget:
        """Devuelve un widget con un label pill para el rol del usuario."""
        rol_norm = str(rol).lower()
        es_admin = rol_norm in ("admin", "administrador")

        contenedor = QWidget()
        lay = QHBoxLayout(contenedor)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setAlignment(Qt.AlignCenter)

        lbl = QLabel()
        lbl.setFixedHeight(24)
        lbl.setAlignment(Qt.AlignCenter)

        if es_propio:
            lbl.setObjectName("badgeYo")
            lbl.setText("Tú (Admin)")
        elif es_admin:
            lbl.setObjectName("badgeAdmin")
            lbl.setText("Admin")
        else:
            lbl.setObjectName("badgeUsuario")
            lbl.setText("Usuario")

        lay.addWidget(lbl)
        return contenedor

    def _actualizar_contador(self, visibles, total):
        if visibles == total:
            self.lbl_contador.setText(f"({total} usuario{'s' if total != 1 else ''})")
        else:
            self.lbl_contador.setText(f"({visibles} de {total} usuarios)")

    # ──────────────────────────────────────────────────────────────
    #  Carga, filtrado y ordenamiento
    # ──────────────────────────────────────────────────────────────

    def _cargar_usuarios(self):
        """Pide la lista al backend y guarda una copia en memoria."""
        try:
            usuarios = self.client.listar_usuarios()
        except AttributeError:
            print("[ADMIN] ⚠️ El ApiClient no tiene el método 'listar_usuarios'")
            usuarios = []
        except Exception as e:
            print(f"[ADMIN] ❌ Error cargando usuarios: {e}")
            usuarios = []

        self._todos_usuarios = usuarios if isinstance(usuarios, list) else []
        self._orden_col = None
        self._orden_asc = True
        self.buscador.clear()
        self._poblar_tabla(self._todos_usuarios)

    def _recargar(self):
        """Limpia el buscador y vuelve a pedir la lista al servidor."""
        self.tabla.setRowCount(0)
        self.lbl_contador.setText("")
        self._cargar_usuarios()

    def _aplicar_filtro(self):
        """Filtra la lista en memoria según el texto del buscador."""
        texto = self.buscador.text().strip().lower()
        if not texto:
            filtrados = self._todos_usuarios
        else:
            filtrados = [
                u for u in self._todos_usuarios
                if texto in f"{u.get('nombre', '')} {u.get('apellido', '')}".lower()
                or texto in u.get("email", "").lower()
                or texto in str(u.get("rol", "")).lower()
            ]
        # Mantener el orden actual al filtrar
        if self._orden_col is not None:
            filtrados = self._ordenar_lista(filtrados, self._orden_col, self._orden_asc)
        self._poblar_tabla(filtrados)

    def _ordenar_por_columna(self, col_index: int):
        """Ordena la tabla al hacer clic en un header. Alterna asc/desc."""
        # La columna Acciones y Rol (badge) no se pueden ordenar con lógica de texto
        if col_index == COL_ACCIONES:
            return

        if self._orden_col == col_index:
            self._orden_asc = not self._orden_asc
        else:
            self._orden_col = col_index
            self._orden_asc = True

        # Actualizar el indicador visual en el header
        self._actualizar_header_orden()

        # Obtener la lista visible actual y reordenarla
        texto = self.buscador.text().strip().lower()
        if not texto:
            base = list(self._todos_usuarios)
        else:
            base = [
                u for u in self._todos_usuarios
                if texto in f"{u.get('nombre', '')} {u.get('apellido', '')}".lower()
                or texto in u.get("email", "").lower()
                or texto in str(u.get("rol", "")).lower()
            ]

        ordenados = self._ordenar_lista(base, self._orden_col, self._orden_asc)
        self._poblar_tabla(ordenados)

    def _ordenar_lista(self, lista: list, col: int, ascendente: bool) -> list:
        """Devuelve la lista ordenada según la columna indicada."""
        def clave(u):
            if col == COL_ID:
                return u.get("id") or 0
            elif col == COL_NOMBRE:
                return f"{u.get('nombre', '')} {u.get('apellido', '')}".strip().lower()
            elif col == COL_EMAIL:
                return u.get("email", "").lower()
            elif col == COL_ROL:
                return str(u.get("rol", "")).lower()
            return ""

        return sorted(lista, key=clave, reverse=not ascendente)

    def _actualizar_header_orden(self):
        """Actualiza las etiquetas del header para mostrar la flecha de orden."""
        etiquetas_base = ["ID", "Nombre", "Email", "Rol", "Acciones"]
        for i, etiqueta in enumerate(etiquetas_base):
            if i == self._orden_col:
                flecha = " ▲" if self._orden_asc else " ▼"
                self.tabla.horizontalHeaderItem(i).setText(etiqueta + flecha)
            else:
                self.tabla.horizontalHeaderItem(i).setText(etiqueta)

    # ──────────────────────────────────────────────────────────────
    #  Renderizado de la tabla
    # ──────────────────────────────────────────────────────────────

    def _poblar_tabla(self, usuarios: list):
        """Renderiza la lista de usuarios en la tabla."""
        self.tabla.setRowCount(0)

        for u in usuarios:
            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)
            self.tabla.setRowHeight(fila, self.ALTO_FILA)

            nombre_completo = f"{u.get('nombre', '')} {u.get('apellido', '')}".strip()
            email           = u.get("email", "")
            rol             = u.get("rol", "usuario")
            es_propio       = bool(self._email_propio and email == self._email_propio)

            # ── Columna ID ──
            self.tabla.setItem(fila, COL_ID, self._crear_item(str(u.get("id", "")), centrado=True))

            # ── Columna Nombre (negrita si es el propio admin) ──
            self.tabla.setItem(fila, COL_NOMBRE, self._crear_item(nombre_completo, negrita=es_propio))

            # ── Columna Email ──
            self.tabla.setItem(fila, COL_EMAIL, self._crear_item(email))
            # ── Columna Rol (badge visual) ──
            self.tabla.setCellWidget(fila, COL_ROL, self._crear_badge_rol(rol, es_propio))

            # ── Columna Acciones ──
            btn = QPushButton("Visualizar Rastreador")
            btn.setObjectName("btnVivo")
            btn.setCursor(Qt.PointingHandCursor)
            datos_usuario = {campo: u.get(campo) for campo in ("id", "nombre", "apellido", "email")}
            btn.clicked.connect(
                lambda checked=False, uid=u.get("id"), nombre=u.get("nombre"), datos=datos_usuario:
                self._abrir_monitor(uid, nombre, datos)
            )
            contenedor_btn = QWidget()
            lay_btn = QHBoxLayout(contenedor_btn)
            lay_btn.setContentsMargins(10, 8, 10, 8)
            lay_btn.addWidget(btn)
            self.tabla.setCellWidget(fila, COL_ACCIONES, contenedor_btn)

            # ── Resaltar toda la fila si es el admin logueado ──
            if es_propio:
                color_fila = QColor("#0e2b1a")
                for col in range(self.tabla.columnCount()):
                    item = self.tabla.item(fila, col)
                    if item:
                        item.setBackground(color_fila)

        self._actualizar_contador(len(usuarios), len(self._todos_usuarios))

    # ──────────────────────────────────────────────────────────────
    #  Abrir monitor de rastreador
    # ──────────────────────────────────────────────────────────────

    def _abrir_monitor(self, usuario_id, nombre, usuario=None):
        """Abre la ventana del rastreador para ese usuario."""
        if usuario_id in self._ventanas_vivo and self._ventanas_vivo[usuario_id].isVisible():
            self._ventanas_vivo[usuario_id].raise_()
            self._ventanas_vivo[usuario_id].activateWindow()
            return

        print(f"[ADMIN] Abriendo monitor en vivo para {nombre} (ID: {usuario_id})")

        cb = None
        if self.tracker_window and hasattr(self.tracker_window, "obtener_registros_rastreador"):
            cb = self.tracker_window.obtener_registros_rastreador
            print("[ADMIN] ✓ Callback encontrado")
        else:
            print("[ADMIN] ⚠️ No se encontró el TrackerWindow")

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
