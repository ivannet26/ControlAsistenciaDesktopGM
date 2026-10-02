# app/ui/dialogs/rastreador_auto.py
"""
Visor del Rastreador automático.
Muestra los registros capturados en dos bloques:
  - Izquierda: registros detallados (App, Descripción, URL, horas, duración…)
  - Derecha:   vista de grupo (App, % uso, total)
"""

from datetime import datetime, date, timedelta

from PySide6.QtCore import Qt, QDate, QTime, Signal
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QSizePolicy, QAbstractItemView, QSplitter,
)

from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_INPUT_BG, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_HEADER_SEMANA, RADIO_INPUT, RADIO_BOTON,
)


# ============================================================
# QSS GLOBAL DEL VISOR
# ============================================================
QSS_VISOR = f"""
QWidget#raizRastreador {{
    background-color: {COLOR_FONDO};
}}

QFrame#barraInfo {{
    background-color: {COLOR_FONDO};
    border-bottom: 1px solid {COLOR_BORDE};
}}

QLabel#etiquetaInfo {{
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    background: transparent;
}}

QLabel#valorInfo {{
    color: {COLOR_TEXTO};
    font-size: 15px;
    font-weight: 700;
    background: transparent;
}}

QFrame#lineaTiempo {{
    background-color: {COLOR_FONDO};
    border-bottom: 1px solid {COLOR_BORDE};
}}

QFrame#barraHerramientas {{
    background-color: {COLOR_FONDO};
    border-bottom: 1px solid {COLOR_BORDE};
}}

QLineEdit#buscador {{
    background-color: {COLOR_INPUT_BG};
    border: 1px solid {COLOR_BORDE_INPUT};
    border-radius: {RADIO_INPUT}px;
    color: {COLOR_TEXTO};
    padding: 4px 10px;
    font-size: 12px;
    min-height: 26px;
}}

QLineEdit#buscador:focus {{
    border: 1px solid {COLOR_ACENTO};
}}

QPushButton#btnHerramienta {{
    background: transparent;
    color: {COLOR_TEXTO_SECUNDARIO};
    border: none;
    padding: 4px 10px;
    font-size: 12px;
    text-align: left;
}}

QPushButton#btnHerramienta:hover {{
    color: {COLOR_TEXTO};
}}

QPushButton#btnHerramienta:disabled {{
    color: {COLOR_TEXTO_TERCIARIO};
}}

QPushButton#btnDia {{
    background: transparent;
    color: {COLOR_TEXTO};
    border: 1px solid {COLOR_BORDE_INPUT};
    border-radius: {RADIO_BOTON}px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}}

QPushButton#btnDia:hover {{
    border: 1px solid {COLOR_ACENTO};
    color: {COLOR_ACENTO};
}}

QDateEdit {{
    background-color: {COLOR_INPUT_BG};
    border: 1px solid {COLOR_BORDE_INPUT};
    border-radius: {RADIO_INPUT}px;
    color: {COLOR_TEXTO};
    padding: 4px 8px;
    font-size: 12px;
    min-height: 24px;
}}

QPushButton#btnNav {{
    background: transparent;
    color: {COLOR_TEXTO_SECUNDARIO};
    border: none;
    font-size: 14px;
    font-weight: 700;
    min-width: 24px;
}}

QPushButton#btnNav:hover {{
    color: {COLOR_ACENTO};
}}

QPushButton#btnEngranaje {{
    background: transparent;
    color: {COLOR_TEXTO_SECUNDARIO};
    border: none;
    font-size: 16px;
    min-width: 28px;
}}

QPushButton#btnEngranaje:hover {{
    color: {COLOR_ACENTO};
}}

QLabel#tituloBloque {{
    color: {COLOR_TEXTO};
    font-size: 12px;
    font-weight: 700;
    background: transparent;
    padding: 4px 8px;
}}

QTableWidget {{
    background-color: {COLOR_FONDO};
    alternate-background-color: #0f1c24;
    border: none;
    color: {COLOR_TEXTO};
    font-size: 12px;
    gridline-color: transparent;
    selection-background-color: rgba(33, 150, 243, 0.18);
    selection-color: {COLOR_TEXTO};
    outline: none;
}}

QTableWidget::item {{
    padding: 6px 8px;
    border: none;
}}

QHeaderView::section {{
    background-color: {COLOR_HEADER_SEMANA};
    color: {COLOR_TEXTO_SECUNDARIO};
    border: none;
    border-bottom: 1px solid {COLOR_BORDE};
    padding: 6px 8px;
    font-size: 11px;
    font-weight: 700;
}}

QTableCornerButton::section {{
    background-color: {COLOR_HEADER_SEMANA};
    border: none;
    border-bottom: 1px solid {COLOR_BORDE};
}}

QFrame#separadorVertical {{
    background-color: {COLOR_BORDE};
    max-width: 1px;
    min-width: 1px;
    border: none;
}}

QFrame#barraInferior {{
    background-color: {COLOR_HEADER_SEMANA};
    border-top: 1px solid {COLOR_BORDE};
}}

QLabel#textoInferior {{
    color: {COLOR_TEXTO_SECUNDARIO};
    font-size: 11px;
    background: transparent;
    padding: 0 12px;
}}

QScrollBar:vertical {{
    background: {COLOR_FONDO};
    width: 10px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #2a3a45;
    min-height: 30px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{ background: #3a4a55; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0; background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: {COLOR_FONDO};
    height: 10px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #2a3a45;
    min-width: 30px;
    border-radius: 5px;
    margin: 2px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0; background: none;
}}
"""


# ============================================================
# WIDGETS AUXILIARES
# ============================================================
def _separador_v():
    f = QFrame()
    f.setObjectName("separadorVertical")
    f.setFrameShape(QFrame.VLine)
    return f


def _etiqueta_info(texto):
    lbl = QLabel(texto)
    lbl.setObjectName("etiquetaInfo")
    return lbl


def _valor_info(texto):
    lbl = QLabel(texto)
    lbl.setObjectName("valorInfo")
    return lbl


# ============================================================
# BARRA DE INFORMACIÓN SUPERIOR
# ============================================================
class BarraInfo(QWidget):
    """
    Fila con: [Grabando… + subtítulo]   [Iniciado] [Finalizado] [Duración]   [Hoy] [fecha] [◀ ▶ ⚙]
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barraInfo")
        self.setAttribute(Qt.WA_StyledBackground, True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(24)

        # ---- Bloque izquierdo: estado ----
        izq = QVBoxLayout()
        izq.setContentsMargins(0, 0, 0, 0)
        izq.setSpacing(2)

        self.lbl_estado = QLabel("Grabando…")
        self.lbl_estado.setStyleSheet(f"""
            color: {COLOR_ACENTO};
            font-size: 12px;
            font-weight: 700;
            background: transparent;
        """)

        self.lbl_sub = QLabel(
            "Solo tú puedes ver la actividad rastreada.\n"
            "Los registros de este día están disponibles por 41 días más."
        )
        self.lbl_sub.setStyleSheet(f"""
            color: {COLOR_TEXTO_SECUNDARIO};
            font-size: 11px;
            background: transparent;
        """)

        izq.addWidget(self.lbl_estado)
        izq.addWidget(self.lbl_sub)

        lay.addLayout(izq, 1)

        # ---- Centro: Iniciado / Finalizado / Duración ----
        centro = QHBoxLayout()
        centro.setContentsMargins(0, 0, 0, 0)
        centro.setSpacing(28)

        self.lbl_iniciado = self._bloque_centro("Iniciado", "—")
        self.lbl_finalizado = self._bloque_centro("Finalizado", "—")
        self.lbl_duracion = self._bloque_centro("Duración", "—")

        centro.addLayout(self.lbl_iniciado)
        centro.addLayout(self.lbl_finalizado)
        centro.addLayout(self.lbl_duracion)

        lay.addLayout(centro)

        # ---- Derecha: Hoy + fecha + nav + engranaje ----
        der = QHBoxLayout()
        der.setContentsMargins(0, 0, 0, 0)
        der.setSpacing(6)

        self.btn_hoy = QPushButton("Hoy")
        self.btn_hoy.setObjectName("btnDia")
        self.btn_hoy.setCursor(Qt.PointingHandCursor)

        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy")
        self.fecha.setDate(QDate.currentDate())

        self.btn_prev = QPushButton("‹")
        self.btn_prev.setObjectName("btnNav")
        self.btn_prev.setCursor(Qt.PointingHandCursor)

        self.btn_next = QPushButton("›")
        self.btn_next.setObjectName("btnNav")
        self.btn_next.setCursor(Qt.PointingHandCursor)

        self.btn_engranaje = QPushButton("⚙")
        self.btn_engranaje.setObjectName("btnEngranaje")
        self.btn_engranaje.setCursor(Qt.PointingHandCursor)
        self.btn_engranaje.setToolTip("Preferencias del rastreador")

        der.addWidget(self.btn_hoy)
        der.addWidget(self.fecha)
        der.addWidget(self.btn_prev)
        der.addWidget(self.btn_next)
        der.addWidget(self.btn_engranaje)

        lay.addLayout(der)

    def _bloque_centro(self, etiqueta, valor):
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(_etiqueta_info(etiqueta))
        lay.addWidget(_valor_info(valor))
        return lay

    def set_resumen(self, iniciado: str, finalizado: str, duracion: str):
        # Los labels dentro del layout están en orden: [label, valor]
        self.lbl_iniciado.itemAt(1).widget().setText(iniciado)
        self.lbl_finalizado.itemAt(1).widget().setText(finalizado)
        self.lbl_duracion.itemAt(1).widget().setText(duracion)


# ============================================================
# LÍNEA DE TIEMPO (0h - 23h)
# ============================================================
class LineaTiempo(QWidget):
    """Barra simple con las 24 horas y bloques coloreados."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("lineaTiempo")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(48)
        self._bloques = []   # lista de (hora_inicio_decimal, hora_fin_decimal, color)

    def set_bloques(self, bloques):
        """bloques: [(hora_inicio_decimal, hora_fin_decimal, color_hex), ...]"""
        self._bloques = bloques or []
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margen_izq = 0

        # Fondo
        p.fillRect(0, h - 20, w, 4, QColor("#1c2a33"))

        # Bloques
        for ini, fin, color in self._bloques:
            x1 = margen_izq + int((ini / 24.0) * (w - margen_izq))
            x2 = margen_izq + int((fin / 24.0) * (w - margen_izq))
            ancho = max(2, x2 - x1)
            p.fillRect(x1, h - 22, ancho, 8, QColor(color))

        # Etiquetas de hora
        fuente = QFont()
        fuente.setPointSize(8)
        p.setFont(fuente)
        p.setPen(QPen(QColor(COLOR_TEXTO_SECUNDARIO)))

        for hh in range(0, 24):
            x = margen_izq + int((hh / 24.0) * (w - margen_izq))
            p.drawText(x + 2, h - 4, f"{hh}h")

        p.end()


# ============================================================
# BARRA DE HERRAMIENTAS
# ============================================================
class BarraHerramientas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barraHerramientas")
        self.setAttribute(Qt.WA_StyledBackground, True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(4)

        self.buscador = QLineEdit()
        self.buscador.setObjectName("buscador")
        self.buscador.setPlaceholderText("Buscar")
        self.buscador.setFixedWidth(220)

        self.btn_anadir = self._btn("＋ Añadir selección")
        self.btn_combinar = self._btn("🔗 Combinar selección")
        self.btn_eliminar = self._btn("🗑 Eliminar selección")

        lay.addWidget(self.buscador)
        lay.addSpacing(12)
        lay.addWidget(self.btn_anadir)
        lay.addWidget(self.btn_combinar)
        lay.addWidget(self.btn_eliminar)
        lay.addStretch()

    def _btn(self, texto):
        b = QPushButton(texto)
        b.setObjectName("btnHerramienta")
        b.setCursor(Qt.PointingHandCursor)
        b.setEnabled(False)   # se habilitan al seleccionar filas
        return b


# ============================================================
# VENTANA PRINCIPAL DEL VISOR
# ============================================================
class VentanaRastreadorAuto(QDialog):
    """
    Visor del Rastreador automático.
    Uso:
        v = VentanaRastreadorAuto(parent=..., registros=[...], grupo=[...])
        v.exec()
    """

    def __init__(self, parent=None, registros=None, grupo=None):
        super().__init__(parent)
        self.setWindowTitle("Rastreador automático")
        self.setModal(True)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setMinimumSize(1000, 620)
        self.resize(1180, 720)

        self.setStyleSheet(QSS_VISOR)

        self._armar_ui()

        # Cargar datos iniciales (si los pasan)
        self.cargar_datos(registros or [], grupo or [])

    # ------------------------------------------------------------
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barra de título personalizada
        self.title_bar = CustomTitleBar(
            self,
            "Rastreador automático",
            mostrar_maximizar=True,
            mostrar_minimizar=True,
        )
        root.addWidget(self.title_bar)

        # Contenedor raíz oscuro
        raiz = QWidget()
        raiz.setObjectName("raizRastreador")
        raiz.setAttribute(Qt.WA_StyledBackground, True)
        root.addWidget(raiz, 1)

        lay = QVBoxLayout(raiz)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 1) Barra de información
        self.barra_info = BarraInfo()
        self.barra_info.btn_hoy.clicked.connect(self._ir_hoy)
        self.barra_info.fecha.dateChanged.connect(self._cambio_fecha)
        self.barra_info.btn_prev.clicked.connect(lambda: self._mover_dia(-1))
        self.barra_info.btn_next.clicked.connect(lambda: self._mover_dia(1))
        self.barra_info.btn_engranaje.clicked.connect(self._abrir_prefs)
        lay.addWidget(self.barra_info)

        # 2) Línea de tiempo
        self.linea = LineaTiempo()
        lay.addWidget(self.linea)

        # 3) Barra de herramientas
        self.toolbar = BarraHerramientas()
        self.toolbar.buscador.textChanged.connect(self._filtrar)
        lay.addWidget(self.toolbar)

        # 4) Split: tabla detalle + vista de grupo
        split = QSplitter(Qt.Horizontal)
        split.setHandleWidth(1)
        split.setStyleSheet(
            f"QSplitter::handle {{ background-color: {COLOR_BORDE}; }}"
        )

        # Bloque izquierdo
        izq = QWidget()
        izq_lay = QVBoxLayout(izq)
        izq_lay.setContentsMargins(0, 0, 0, 0)
        izq_lay.setSpacing(0)
        izq_lay.addWidget(self._titulo_bloque("Registros detallados"))
        self.tabla = self._crear_tabla_detalle()
        izq_lay.addWidget(self.tabla, 1)

        # Bloque derecho
        der = QWidget()
        der_lay = QVBoxLayout(der)
        der_lay.setContentsMargins(0, 0, 0, 0)
        der_lay.setSpacing(0)
        der_lay.addWidget(self._titulo_bloque("Vista de grupo"))
        self.tabla_grupo = self._crear_tabla_grupo()
        der_lay.addWidget(self.tabla_grupo, 1)

        split.addWidget(izq)
        split.addWidget(der)
        split.setStretchFactor(0, 7)
        split.setStretchFactor(1, 3)
        lay.addWidget(split, 1)

        # 5) Barra inferior
        inferior = QFrame()
        inferior.setObjectName("barraInferior")
        inferior.setAttribute(Qt.WA_StyledBackground, True)
        inferior.setFixedHeight(28)

        inf_lay = QHBoxLayout(inferior)
        inf_lay.setContentsMargins(8, 0, 8, 0)
        inf_lay.setSpacing(8)

        self.lbl_seleccion = QLabel("Detalles : Seleccionado 0/0")
        self.lbl_seleccion.setObjectName("textoInferior")

        self.lbl_total = QLabel("Total 0h 0m")
        self.lbl_total.setObjectName("textoInferior")

        inf_lay.addWidget(self.lbl_seleccion)
        inf_lay.addStretch()
        inf_lay.addWidget(self.lbl_total)

        lay.addWidget(inferior)

    # ------------------------------------------------------------
    def _titulo_bloque(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("tituloBloque")
        return lbl

    def _crear_tabla_detalle(self):
        t = QTableWidget()
        cols = [
            "", "Aplicación", "Descripción", "URL",
            "Hora de inicio", "Hora de final", "Duración",
            "Inactividad", "Agregar como",
        ]
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setSortingEnabled(False)

        h = t.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        t.setColumnWidth(0, 28)
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        h.setSectionResizeMode(3, QHeaderView.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(8, QHeaderView.ResizeToContents)

        t.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        return t

    def _crear_tabla_grupo(self):
        t = QTableWidget()
        cols = ["", "Aplicación", "Uso", "Total"]
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)

        h = t.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        t.setColumnWidth(0, 28)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        return t

    # ------------------------------------------------------------
    # API PÚBLICA
    # ------------------------------------------------------------
    def cargar_datos(self, registros, grupo):
        """
        registros: lista de dicts con claves:
            app, descripcion, url, hora_inicio, hora_fin,
            duracion, inactividad (float 0..1), agregar_como
        grupo: lista de dicts con claves:
            app, uso_pct (float), total_str
        """
        self._registros = registros or []
        self._grupo = grupo or []

        self._pintar_tabla_detalle(self._registros)
        self._pintar_tabla_grupo(self._grupo)
        self._actualizar_resumen()
        self._actualizar_linea_tiempo()
        self._actualizar_seleccion()

    # ------------------------------------------------------------
    def _pintar_tabla_detalle(self, registros):
        t = self.tabla
        t.setRowCount(0)
        for reg in registros:
            fila = t.rowCount()
            t.insertRow(fila)

            # checkbox
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            t.setItem(fila, 0, chk)

            # Icono + nombre app
            item_app = QTableWidgetItem(reg.get("app", ""))
            t.setItem(fila, 1, item_app)

            t.setItem(fila, 2, QTableWidgetItem(reg.get("descripcion", "")))

            url = reg.get("url") or "—"
            item_url = QTableWidgetItem(url)
            if reg.get("url"):
                item_url.setForeground(QBrush(QColor(COLOR_ACENTO)))
            t.setItem(fila, 3, item_url)

            t.setItem(fila, 4, QTableWidgetItem(reg.get("hora_inicio", "")))
            t.setItem(fila, 5, QTableWidgetItem(reg.get("hora_fin", "")))
            t.setItem(fila, 6, QTableWidgetItem(reg.get("duracion", "")))
            t.setItem(fila, 7, QTableWidgetItem(
                f"{int(reg.get('inactividad', 0) * 100)}%"
            ))
            t.setItem(fila, 8, QTableWidgetItem("+"))

    def _pintar_tabla_grupo(self, grupo):
        t = self.tabla_grupo
        t.setRowCount(0)
        for g in grupo:
            fila = t.rowCount()
            t.insertRow(fila)

            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk.setCheckState(Qt.Unchecked)
            t.setItem(fila, 0, chk)

            t.setItem(fila, 1, QTableWidgetItem(g.get("app", "")))
            t.setItem(fila, 2, QTableWidgetItem(
                f"{g.get('uso_pct', 0):.1f} %"
            ))
            t.setItem(fila, 3, QTableWidgetItem(g.get("total_str", "")))

    # ------------------------------------------------------------
    def _actualizar_resumen(self):
        if not self._registros:
            self.barra_info.set_resumen("—", "—", "—")
            self.lbl_total.setText("Total 0h 0m")
            return

        inicio = self._registros[0].get("hora_inicio", "—")
        fin = self._registros[-1].get("hora_fin", "—")
        total_seg = 0
        for r in self._registros:
            total_seg += self._parse_duracion(r.get("duracion", "0:0:0"))

        h = total_seg // 3600
        m = (total_seg % 3600) // 60
        self.barra_info.set_resumen(inicio, fin, f"{h:02d}:{m:02d}")
        self.lbl_total.setText(f"Total {h}h {m}m")

    def _actualizar_linea_tiempo(self):
        bloques = []
        for r in self._registros:
            ini = self._hora_a_decimal(r.get("hora_inicio"))
            fin = self._hora_a_decimal(r.get("hora_fin"))
            if ini is None or fin is None:
                continue
            color = r.get("color") or "#2196f3"
            bloques.append((ini, fin, color))
        self.linea.set_bloques(bloques)

    def _actualizar_seleccion(self):
        total = self.tabla.rowCount()
        seleccionadas = len(self.tabla.selectionModel().selectedRows()) \
            if self.tabla.selectionModel() else 0
        self.lbl_seleccion.setText(
            f"Detalles : Seleccionado {seleccionadas}/{total}"
        )

    # ------------------------------------------------------------
    def _on_seleccion_cambiada(self):
        self._actualizar_seleccion()
        hay = len(self.tabla.selectionModel().selectedRows()) > 0 \
            if self.tabla.selectionModel() else False
        self.toolbar.btn_anadir.setEnabled(hay)
        self.toolbar.btn_combinar.setEnabled(hay)
        self.toolbar.btn_eliminar.setEnabled(hay)

    # ------------------------------------------------------------
    def _filtrar(self, texto):
        texto = (texto or "").strip().lower()
        if not texto:
            for fila in range(self.tabla.rowCount()):
                self.tabla.setRowHidden(fila, False)
            return
        for fila in range(self.tabla.rowCount()):
            visible = False
            for col in (1, 2, 3):
                item = self.tabla.item(fila, col)
                if item and texto in item.text().lower():
                    visible = True
                    break
            self.tabla.setRowHidden(fila, not visible)

    # ------------------------------------------------------------
    def _ir_hoy(self):
        self.barra_info.fecha.setDate(QDate.currentDate())

    def _mover_dia(self, delta):
        self.barra_info.fecha.setDate(
            self.barra_info.fecha.date().addDays(delta)
        )

    def _cambio_fecha(self, qdate):
        # Aquí conectarás con tu backend para recargar los registros del día
        # por ahora solo actualizamos etiquetas:
        pass

    def _abrir_prefs(self):
        from app.ui.dialogs.preferencias import DialogoPreferencias
        dlg = DialogoPreferencias(self)
        dlg.exec()

    # ------------------------------------------------------------
    def _parse_duracion(self, texto):
        """Acepta 'HH:MM:SS' o 'HH:MM' o '00:00:51'."""
        try:
            partes = [int(p) for p in str(texto).split(":")]
        except (ValueError, TypeError):
            return 0
        if len(partes) == 3:
            return partes[0] * 3600 + partes[1] * 60 + partes[2]
        if len(partes) == 2:
            return partes[0] * 3600 + partes[1] * 60
        return 0

    def _hora_a_decimal(self, texto):
        """'21:10' -> 21.1666"""
        try:
            hh, mm = str(texto).split(":")[:2]
            return int(hh) + int(mm) / 60.0
        except (ValueError, AttributeError):
            return None