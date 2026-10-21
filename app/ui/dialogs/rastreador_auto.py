from datetime import datetime, date
from app.services.pdf_export import exportar_informe_pdf
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QColor, QBrush, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QSizePolicy, QAbstractItemView, QSplitter, QFileDialog,
    QMessageBox,
)
from app.services.websocket_client import RastreadorWebSocket
from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_INPUT_BG, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_HEADER_SEMANA, RADIO_INPUT, RADIO_BOTON,
)
from app.utils.workers import ApiWorker


def _generar_excel_exportacion(
    ruta,
    registros,
    grupo,
    fecha_str,
    iniciado_texto,
    finalizado_texto,
    duracion_texto,
    usuario,
):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Registros detallados"

    fuente_header = Font(bold=True, color="FFFFFF", size=11)
    fondo_header = PatternFill("solid", fgColor="1F4E78")
    alineacion = Alignment(horizontal="left", vertical="center")
    borde = Border(
        left=Side(style="thin", color="CCCCCC"),
        right=Side(style="thin", color="CCCCCC"),
        top=Side(style="thin", color="CCCCCC"),
        bottom=Side(style="thin", color="CCCCCC"),
    )

    ws["A1"] = "Rastreador automático"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Fecha: {fecha_str}"
    nombre_usuario = (
        f"{usuario.get('nombre', '')} {usuario.get('apellido', '')}".strip()
        or "(sin nombre)"
    )
    ws["A3"] = f"Usuario: {nombre_usuario}"
    ws["A4"] = f"Email: {usuario.get('email') or '(sin email)'}"
    ws["A5"] = f"Iniciado: {iniciado_texto}"
    ws["A6"] = f"Finalizado: {finalizado_texto}"
    ws["A7"] = f"Duración total: {duracion_texto}"
    ws["A8"] = f"Total registros: {len(registros)}"

    fila_header = 10
    cabeceras = [
        "Aplicación", "Descripción", "URL",
        "Hora de inicio", "Hora de final", "Duración",
        "Inactividad", "Agregar como",
    ]
    for col, titulo in enumerate(cabeceras, start=1):
        celda = ws.cell(row=fila_header, column=col, value=titulo)
        celda.font = fuente_header
        celda.fill = fondo_header
        celda.alignment = alineacion
        celda.border = borde

    for i, reg in enumerate(registros, start=fila_header + 1):
        valores = [
            reg.get("app", ""),
            reg.get("descripcion", ""),
            reg.get("url", ""),
            reg.get("hora_inicio", ""),
            reg.get("hora_fin", ""),
            reg.get("duracion", ""),
            f"{int((reg.get('inactividad') or 0) * 100)}%",
            "+",
        ]
        for col, valor in enumerate(valores, start=1):
            celda = ws.cell(row=i, column=col, value=valor)
            celda.border = borde

    for col, ancho in enumerate([18, 35, 50, 14, 14, 12, 12, 14], start=1):
        letra = ws.cell(row=1, column=col).column_letter
        ws.column_dimensions[letra].width = ancho
    ws.freeze_panes = f"A{fila_header + 1}"

    ws2 = wb.create_sheet("Vista de grupo")
    ws2["A1"] = "Vista de grupo"
    ws2["A1"].font = Font(bold=True, size=14)
    ws2["A2"] = f"Fecha: {fecha_str}"

    fila_h2 = 4
    for col, titulo in enumerate(["Aplicación", "Uso (%)", "Total"], start=1):
        celda = ws2.cell(row=fila_h2, column=col, value=titulo)
        celda.font = fuente_header
        celda.fill = fondo_header
        celda.alignment = alineacion
        celda.border = borde

    for i, item in enumerate(grupo, start=fila_h2 + 1):
        valores = [
            item.get("app", ""),
            item.get("uso_pct", 0),
            item.get("total_str", ""),
        ]
        for col, valor in enumerate(valores, start=1):
            celda = ws2.cell(row=i, column=col, value=valor)
            celda.border = borde

    ws2.column_dimensions["A"].width = 25
    ws2.column_dimensions["B"].width = 12
    ws2.column_dimensions["C"].width = 14
    ws2.freeze_panes = f"A{fila_h2 + 1}"
    wb.save(ruta)
    return ruta


def _generar_pdf_exportacion(ruta, usuario, fecha_str, registros, grupo):
    ok = exportar_informe_pdf(
        ruta_salida=ruta,
        usuario=usuario,
        fecha_iso=fecha_str,
        registros=registros,
        grupo=grupo,
    )
    if not ok:
        raise RuntimeError("El generador PDF indicó un error.")
    return ruta


# ============================================================
# QSS GLOBAL
# ============================================================
QSS_VISOR = f"""
QWidget#raizRastreador {{ background-color: {COLOR_FONDO}; }}

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
QLineEdit#buscador:focus {{ border: 1px solid {COLOR_ACENTO}; }}

/* Botones de acción — gris azulado formal, un solo color */
QPushButton#btnAccion,
QPushButton#btnAccionPrimario {{
    background-color: #37474f;
    color: #e6edf3;
    border: none;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    min-height: 22px;
    max-height: 22px;
}}
QPushButton#btnAccion:hover,
QPushButton#btnAccionPrimario:hover {{
    background-color: #455a64;
    color: #ffffff;
}}
QPushButton#btnAccion:pressed,
QPushButton#btnAccionPrimario:pressed {{
    background-color: #263238;
}}
QPushButton#btnAccion:disabled,
QPushButton#btnAccionPrimario:disabled {{
    background-color: #2a3b47;
    color: #5d6b76;
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
QPushButton#btnNav:hover {{ color: {COLOR_ACENTO}; }}

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


def _etiqueta_info(texto):
    lbl = QLabel(texto)
    lbl.setObjectName("etiquetaInfo")
    return lbl


def _valor_info(texto):
    lbl = QLabel(texto)
    lbl.setObjectName("valorInfo")
    return lbl


# ============================================================
# BARRA DE INFORMACIÓN
# ============================================================
class BarraInfo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("barraInfo")
        self.setAttribute(Qt.WA_StyledBackground, True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(24)

        # ---- Bloque izquierdo: LOGO ----
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedHeight(38)
        self.lbl_logo.setStyleSheet("background: transparent;")

        try:
            from pathlib import Path as _Path
            from PySide6.QtGui import QPixmap

            base = _Path(__file__).resolve().parents[2]
            ruta_logo = base / "assets" / "logo-mg.png"

            if ruta_logo.exists():
                pix = QPixmap(str(ruta_logo))
                if not pix.isNull():
                    self.lbl_logo.setPixmap(
                        pix.scaledToHeight(38, Qt.SmoothTransformation)
                    )
                    print(f"[VISOR] ✓ Logo cargado: {ruta_logo}")
                else:
                    self.lbl_logo.setText("GM")
                    print(f"[VISOR] Pixmap nulo: {ruta_logo}")
            else:
                self.lbl_logo.setText("GM")
                print(f"[VISOR] Logo no encontrado: {ruta_logo}")
        except Exception as e:
            print(f"[VISOR] Error cargando logo: {e}")
            self.lbl_logo.setText("GM")

        lay.addWidget(self.lbl_logo, 0, Qt.AlignVCenter)
        lay.addSpacing(16)
        lay.addStretch(1)

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

        # ---- Derecha: Hoy / fecha / nav ----
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

        der.addWidget(self.btn_hoy)
        der.addWidget(self.fecha)
        der.addWidget(self.btn_prev)
        der.addWidget(self.btn_next)
        lay.addLayout(der)

    def _bloque_centro(self, etiqueta, valor):
        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(_etiqueta_info(etiqueta))
        lay.addWidget(_valor_info(valor))
        return lay

    def set_resumen(self, iniciado, finalizado, duracion):
        self.lbl_iniciado.itemAt(1).widget().setText(iniciado)
        self.lbl_finalizado.itemAt(1).widget().setText(finalizado)
        self.lbl_duracion.itemAt(1).widget().setText(duracion)


# ============================================================
# LÍNEA DE TIEMPO
# ============================================================
class LineaTiempo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("lineaTiempo")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(48)
        self._bloques = []

    def set_bloques(self, bloques):
        self._bloques = bloques or []
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, h - 20, w, 4, QColor("#1c2a33"))

        for ini, fin, color in self._bloques:
            x1 = int((ini / 24.0) * w)
            x2 = int((fin / 24.0) * w)
            p.fillRect(x1, h - 22, max(2, x2 - x1), 8, QColor(color))

        fuente = QFont()
        fuente.setPointSize(8)
        p.setFont(fuente)
        p.setPen(QPen(QColor(COLOR_TEXTO_SECUNDARIO)))
        for hh in range(0, 24):
            x = int((hh / 24.0) * w)
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
        lay.setSpacing(8)

        # Buscador (izquierda)
        self.buscador = QLineEdit()
        self.buscador.setObjectName("buscador")
        self.buscador.setPlaceholderText("Buscar aplicación, descripción o URL…")
        self.buscador.setFixedWidth(280)

        lay.addWidget(self.buscador)

        lay.addStretch()

        # Botón Actualizar
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setObjectName("btnAccion")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setToolTip("Forzar actualización ahora")
        lay.addWidget(self.btn_refresh)

        # Botón Exportar Excel
        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.setObjectName("btnAccionPrimario")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setToolTip("Guardar los registros en un archivo .xlsx")
        lay.addWidget(self.btn_export)
        # Botón Exportar PDF
        self.btn_pdf = QPushButton("Exportar PDF")
        self.btn_pdf.setObjectName("btnAccionPrimario")
        self.btn_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_pdf.setToolTip("Generar informe en PDF")
        lay.addWidget(self.btn_pdf)


# ============================================================
# VENTANA PRINCIPAL
# ============================================================
class VentanaRastreadorAuto(QDialog):
    """
    Uso:
        v = VentanaRastreadorAuto(
            parent=tracker,
            cargar_datos_cb=tracker.obtener_registros_rastreador,
        )
        v.exec()

    `cargar_datos_cb(fecha_iso: str) -> (registros, grupo)`
    """

    def __init__(
        self,
        parent=None,
        cargar_datos_cb=None,
        registros=None,
        grupo=None,
        usuario_id=None,
        usuario=None,
    ):
        super().__init__(parent)
        self._cargar_datos_cb = cargar_datos_cb
        self._registros = []
        self._grupo = []
        self._ultima_actualizacion = "—"
        self._pagina_actual = 1
        self._total_paginas = 1
        self._registros_por_pagina = 50
        self._total_registros = 0
        self._total_iniciado = 0
        self._total_finalizado = 0
        self._total_duracion = "—"
        self._hora_inicio_dia = None
        self._hora_fin_dia = None
        self._usuario_id = usuario_id
        self._usuario = usuario or {}
        self._workers = []
        self._carga_en_curso = False
        self._carga_pendiente = False
        self.setWindowTitle("Rastreador automático")
        self.setModal(False)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(1000, 620)
        self.resize(1180, 720)
        self.setStyleSheet(QSS_VISOR)

        self._armar_ui()

        # Carga inicial
        if registros is not None or grupo is not None:
            self.cargar_datos(registros or [], grupo or [])
        else:
            self._recargar_fecha(QDate.currentDate())

        QTimer.singleShot(500, self._ir_a_ultima_pagina)

        # ⏱️ Auto-refresh cada 5 segundos
        self._timer_refresh = QTimer(self)
        self._timer_refresh.timeout.connect(self._auto_refresh)
        self._timer_refresh.start(5000)
        print(f"[VISOR] QTimer arrancado — activo={self._timer_refresh.isActive()}")

        # ============================================================
        # RECEPTOR WEBSOCKET PARA TIEMPO REAL
        # ============================================================
        self.ws_live = None
        if self._usuario_id and self.parent() and hasattr(self.parent(), 'client'):
            client_padre = self.parent().client
            self.ws_live = RastreadorWebSocket(
                base_url="https://backendcontrolasistenciagm.onrender.com",
                token=client_padre.token,
                usuario_id_vigilar=self._usuario_id,
                parent=self
            )
            self.ws_live.datos_recibidos.connect(self._on_datos_en_vivo)
            self.ws_live.conectar()
            print(f"[VISOR] WebSocket conectado para ver en vivo al usuario {self._usuario_id}")

    def _on_datos_en_vivo(self, data):
        """Recibe los datos del WebSocket y actualiza la tabla al instante."""
        if data.get("tipo") == "nueva_actividad":
            print(f"[VISOR] 🟢 Datos en vivo recibidos: {len(data.get('registros', []))} registros")
            filas_nuevas = False

            for reg in data.get("registros", []):
                reg_id = reg.get("id")

                def coincide_con_existente(existente):
                    existente_id = existente.get("id")
                    if reg_id is not None and existente_id is not None:
                        return reg_id == existente_id
                    return (
                        existente.get("app", ""),
                        existente.get("hora_inicio", ""),
                        existente.get("descripcion", ""),
                        existente.get("url") or "",
                    ) == (
                        reg.get("app", ""),
                        reg.get("hora_inicio", ""),
                        reg.get("descripcion", ""),
                        reg.get("url") or "",
                    )

                if any(coincide_con_existente(existente) for existente in self._registros):
                    continue

                if self.tabla.rowCount() >= self._registros_por_pagina:
                    self.tabla.removeRow(0)
                    if self._registros:
                        self._registros.pop(0)

                fila = self.tabla.rowCount()
                self.tabla.insertRow(fila)
                
                # App
                item_app = QTableWidgetItem(reg.get("app", ""))
                color = reg.get("color") or "#2196f3"
                item_app.setForeground(QBrush(QColor(color)))
                self.tabla.setItem(fila, 0, item_app)
                
                # Descripción
                self.tabla.setItem(fila, 1, QTableWidgetItem(reg.get("descripcion", "")))
                
                # URL
                url = reg.get("url") or "—"
                item_url = QTableWidgetItem(url)
                if reg.get("url"):
                    item_url.setForeground(QBrush(QColor(COLOR_ACENTO)))
                    item_url.setToolTip(reg["url"])
                self.tabla.setItem(fila, 2, item_url)
                
                # Horas y duración
                self.tabla.setItem(fila, 3, QTableWidgetItem(reg.get("hora_inicio", "")))
                hora_fin = reg.get("hora_fin")
                en_curso = (
                    hora_fin is None
                    or not str(hora_fin).strip()
                    or str(hora_fin).strip().lower() == "en curso"
                )
                item_hora_fin = QTableWidgetItem(
                    "en curso" if en_curso else str(hora_fin)
                )
                self.tabla.setItem(fila, 4, item_hora_fin)
                self.tabla.setItem(fila, 5, QTableWidgetItem(reg.get("duracion", "")))
                self.tabla.setItem(fila, 6, QTableWidgetItem("0%"))
                self.tabla.setItem(fila, 7, QTableWidgetItem("+"))

                if en_curso:
                    for columna in range(self.tabla.columnCount()):
                        item = self.tabla.item(fila, columna)
                        if item:
                            item.setForeground(QBrush(QColor("#10a878")))
                            fuente = QFont(item.font())
                            fuente.setBold(True)
                            item.setFont(fuente)

                # Añadir a la lista interna
                self._registros.append(reg)
                filas_nuevas = True

            if filas_nuevas:
                self._actualizar_resumen()
                self._actualizar_linea_tiempo()
                self._actualizar_seleccion()
    # ------------------------------------------------------------
    def _get_cb(self):
        """Devuelve el callback válido, recuperándolo del padre si hace falta."""
        cb = self._cargar_datos_cb
        if cb is not None:
            return cb
        p = self.parent()
        while p is not None:
            cb = getattr(p, "obtener_registros_rastreador", None)
            if cb is not None:
                self._cargar_datos_cb = cb
                print("[VISOR] ✓ Callback recuperado del padre")
                return cb
            p = p.parent() if hasattr(p, "parent") else None
        return None

    # ------------------------------------------------------------
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(
            self,
            "Rastreador automático",
            mostrar_maximizar=True,
            mostrar_minimizar=True,
        )
        root.addWidget(self.title_bar)

        raiz = QWidget()
        raiz.setObjectName("raizRastreador")
        raiz.setAttribute(Qt.WA_StyledBackground, True)
        root.addWidget(raiz, 1)

        lay = QVBoxLayout(raiz)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 1) Barra info
        self.barra_info = BarraInfo()
        self.barra_info.btn_hoy.clicked.connect(self._ir_hoy)
        self.barra_info.fecha.dateChanged.connect(self._recargar_fecha)
        self.barra_info.btn_prev.clicked.connect(lambda: self._mover_dia(-1))
        self.barra_info.btn_next.clicked.connect(lambda: self._mover_dia(1))
        lay.addWidget(self.barra_info)

        # 2) Línea de tiempo
        self.linea = LineaTiempo()
        lay.addWidget(self.linea)

        # 3) Barra de herramientas
        self.toolbar = BarraHerramientas()
        self.toolbar.buscador.textChanged.connect(self._filtrar)
        self.toolbar.btn_refresh.clicked.connect(self._refresh_manual)
        self.toolbar.btn_export.clicked.connect(
            lambda checked=False: self._exportar_excel()
        )
        self.toolbar.btn_pdf.clicked.connect(
            lambda checked=False: self._exportar_pdf()
        )
        lay.addWidget(self.toolbar)

        # 4) Split
        split = QSplitter(Qt.Horizontal)
        split.setHandleWidth(1)
        split.setStyleSheet(f"QSplitter::handle {{ background-color: {COLOR_BORDE}; }}")

        # Izquierda
        izq = QWidget()
        izq_lay = QVBoxLayout(izq)
        izq_lay.setContentsMargins(0, 0, 0, 0)
        izq_lay.setSpacing(0)
        izq_lay.addWidget(self._titulo_bloque("Registros detallados"))
        self.tabla = self._crear_tabla_detalle()
        izq_lay.addWidget(self.tabla, 1)

        # Derecha
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

        self.lbl_actualizado = QLabel("Actualizado —")
        self.lbl_actualizado.setObjectName("textoInferior")

        self.lbl_total = QLabel("Total 0h 0m")
        self.lbl_total.setObjectName("textoInferior")

        inf_lay.addWidget(self.lbl_seleccion)
        inf_lay.addStretch()
        inf_lay.addWidget(self.lbl_actualizado)
        inf_lay.addWidget(self.lbl_total)
            # --- Botones de Paginación ---
        self.btn_prev_page = QPushButton("‹ Anterior")
        self.btn_prev_page.setObjectName("btnAccion")
        self.btn_prev_page.clicked.connect(self._pagina_anterior)
        self.btn_prev_page.setEnabled(False)

        self.lbl_pagina = QLabel("Página 1 de 1")
        self.lbl_pagina.setObjectName("textoInferior")

        self.btn_next_page = QPushButton("Siguiente ›")
        self.btn_next_page.setObjectName("btnAccion")
        self.btn_next_page.clicked.connect(self._pagina_siguiente)
        self.btn_next_page.setEnabled(False)

        inf_lay.addWidget(self.btn_prev_page)
        inf_lay.addWidget(self.lbl_pagina)
        inf_lay.addWidget(self.btn_next_page)
        lay.addWidget(inferior)

    # ------------------------------------------------------------
    def _titulo_bloque(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("tituloBloque")
        return lbl

    def _crear_tabla_detalle(self):
        t = QTableWidget()
        cols = [
            "Aplicación", "Descripción", "URL",
            "Hora de inicio", "Hora de final",
            "Duración (h:m:s)",      
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

        h = t.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Aplicación
        h.setSectionResizeMode(1, QHeaderView.Stretch)           # Descripción
        h.setSectionResizeMode(2, QHeaderView.Stretch)           # URL
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Inicio
        h.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Fin
        h.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Duración
        h.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Inactividad
        h.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Agregar como

        t.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        return t

    def _crear_tabla_grupo(self):
        t = QTableWidget()
        cols = ["Aplicación", "Uso", "Total"]
        t.setColumnCount(len(cols))
        t.setHorizontalHeaderLabels(cols)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)

        h = t.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)           # Aplicación
        h.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Uso
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Total
        return t

    # ------------------------------------------------------------
    def cargar_datos(self, registros, grupo):
        """Carga los datos tal como llegan del callback (sin reordenar)."""
        self._registros = registros or []
        self._grupo = grupo or []

        print(f"[VISOR] cargar_datos — {len(self._registros)} regs")

        self._pintar_tabla_detalle(self._registros)
        self._pintar_tabla_grupo(self._grupo)
        self._actualizar_resumen()
        self._actualizar_linea_tiempo()
        self._actualizar_seleccion()

    def _pintar_tabla_detalle(self, registros):
        t = self.tabla
        t.setRowCount(0)
        for reg in registros:
            fila = t.rowCount()
            t.insertRow(fila)

            item_app = QTableWidgetItem(reg.get("app", ""))
            color = reg.get("color") or "#2196f3"
            item_app.setForeground(QBrush(QColor(color)))
            t.setItem(fila, 0, item_app)

            t.setItem(fila, 1, QTableWidgetItem(reg.get("descripcion", "")))

            url = reg.get("url") or "—"
            item_url = QTableWidgetItem(url)
            if reg.get("url"):
                item_url.setForeground(QBrush(QColor(COLOR_ACENTO)))
                item_url.setToolTip(reg["url"])
            t.setItem(fila, 2, item_url)

            hora_fin = reg.get("hora_fin")
            en_curso = (
                hora_fin is None
                or not str(hora_fin).strip()
                or str(hora_fin).strip().lower() == "en curso"
            )
            t.setItem(fila, 3, QTableWidgetItem(reg.get("hora_inicio", "")))
            t.setItem(
                fila,
                4,
                QTableWidgetItem("en curso" if en_curso else str(hora_fin)),
            )
            t.setItem(fila, 5, QTableWidgetItem(reg.get("duracion", "")))
            t.setItem(fila, 6, QTableWidgetItem(
                f"{int((reg.get('inactividad') or 0) * 100)}%"
            ))
            t.setItem(fila, 7, QTableWidgetItem("+"))

            if en_curso:
                for columna in range(t.columnCount()):
                    item = t.item(fila, columna)
                    if item:
                        item.setForeground(QBrush(QColor("#10a878")))
                        fuente = QFont(item.font())
                        fuente.setBold(True)
                        item.setFont(fuente)

    def _pintar_tabla_grupo(self, grupo):
        t = self.tabla_grupo
        t.setRowCount(0)
        for g in grupo:
            fila = t.rowCount()
            t.insertRow(fila)

            item_app = QTableWidgetItem(g.get("app", ""))
            if g.get("color"):
                item_app.setForeground(QBrush(QColor(g["color"])))
            t.setItem(fila, 0, item_app)

            t.setItem(fila, 1, QTableWidgetItem(f"{g.get('uso_pct', 0):.1f} %"))
            t.setItem(fila, 2, QTableWidgetItem(g.get("total_str", "")))

    @classmethod
    def _formatear_total_duracion(cls, valor, fallback_segundos=0):
        if valor is None:
            total_seg = fallback_segundos
        elif isinstance(valor, str):
            texto = valor.strip()
            if not texto or texto == "—":
                total_seg = fallback_segundos
            elif ":" in texto:
                return texto
            else:
                try:
                    total_seg = int(float(texto))
                except ValueError:
                    return texto
        else:
            total_seg = int(float(valor))

        horas, resto = divmod(max(0, total_seg), 3600)
        minutos, segundos = divmod(resto, 60)
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    # ------------------------------------------------------------
    def _actualizar_resumen(self):
        if (
            not self._registros
            and self._hora_inicio_dia in (None, "")
            and self._hora_fin_dia in (None, "")
            and self._total_duracion in (None, "", "—")
        ):
            self.barra_info.set_resumen("—", "—", "—")
            self.lbl_total.setText("Total 0h 0m")
            return

        inicios = [r["hora_inicio"] for r in self._registros
                   if r["hora_inicio"] not in ("", "—")]
        fines = [r["hora_fin"] for r in self._registros
                 if r["hora_fin"] not in ("", "—", "en curso")]

        inicio = (
            self._hora_inicio_dia
            if self._hora_inicio_dia not in (None, "")
            else (min(inicios) if inicios else "—")
        )
        fin = (
            self._hora_fin_dia
            if self._hora_fin_dia not in (None, "")
            else (max(fines) if fines else "—")
        )

        total_pagina_seg = sum(
            self._parse_duracion(r.get("duracion", ""))
            for r in self._registros
        )
        dur_humano = self._formatear_total_duracion(
            self._total_duracion,
            fallback_segundos=total_pagina_seg,
        )

        self.barra_info.set_resumen(str(inicio), str(fin), dur_humano)
        self.lbl_total.setText(f"Total {dur_humano}")

    def _actualizar_linea_tiempo(self):
        bloques = []
        for r in self._registros:
            ini = self._hora_a_decimal(r.get("hora_inicio"))
            fin = self._hora_a_decimal(r.get("hora_fin"))
            if ini is None or fin is None:
                continue
            if fin < ini:
                fin = 24.0
            color = r.get("color") or "#2196f3"
            bloques.append((ini, fin, color))
        self.linea.set_bloques(bloques)

    def _actualizar_seleccion(self):
        total = self.tabla.rowCount()
        sm = self.tabla.selectionModel()
        sel = len(sm.selectedRows()) if sm else 0
        self.lbl_seleccion.setText(f"Detalles : Seleccionado {sel}/{total}")

    # ------------------------------------------------------------
    def _on_seleccion_cambiada(self):
        self._actualizar_seleccion()

    def _filtrar(self, texto):
        texto = (texto or "").strip().lower()
        for fila in range(self.tabla.rowCount()):
            if not texto:
                self.tabla.setRowHidden(fila, False)
                continue
            visible = False
            for col in (0, 1, 2):
                item = self.tabla.item(fila, col)
                if item and texto in item.text().lower():
                    visible = True
                    break
            self.tabla.setRowHidden(fila, not visible)

    # ------------------------------------------------------------
    def _recargar_fecha(self, qdate: QDate):
        """Se dispara al cambiar la fecha. Pide datos reales paginados."""
        self._solicitar_carga(qdate)

    def _solicitar_carga(self, qdate: QDate):
        cb = self._get_cb()
        if cb is None:
            print("[VISOR] ⚠️  No hay callback para recargar")
            return

        if self._carga_en_curso:
            self._carga_pendiente = True
            return

        fecha_iso = qdate.toString("yyyy-MM-dd")
        kwargs = {
            "page": self._pagina_actual,
            "limit": self._registros_por_pagina,
        }
        if self._usuario_id:
            kwargs["usuario_id_objetivo"] = self._usuario_id

        self._workers = [worker for worker in self._workers if worker.isRunning()]
        worker = ApiWorker(cb, fecha_iso, **kwargs)
        worker.exito.connect(self._on_datos_cargados)
        worker.error.connect(self._on_error_carga)
        self._workers.append(worker)
        self._carga_en_curso = True
        worker.start()

    def _on_datos_cargados(self, datos):
        try:
            if isinstance(datos, dict):
                self._registros = datos.get("registros", [])
                self._grupo = datos.get("grupo", [])
                self._total_registros = datos.get("total", 0)
                self._total_paginas = datos.get("total_pages", 1)
                print(
                    f"[DEBUG] Totales: {datos.get('total_iniciado')}, "
                    f"{datos.get('total_finalizado')}, "
                    f"{datos.get('total_duracion')}"
                )
                self._total_iniciado = datos.get("total_iniciado", 0)
                self._total_finalizado = datos.get("total_finalizado", 0)
                self._total_duracion = datos.get("total_duracion", "—")
                self._hora_inicio_dia = datos.get("hora_inicio_dia")
                self._hora_fin_dia = datos.get("hora_fin_dia")
            else:
                self._registros, self._grupo = datos
                self._total_registros = len(self._registros)
                self._total_paginas = 1
                self._total_iniciado = 0
                self._total_finalizado = 0
                self._total_duracion = "—"
                self._hora_inicio_dia = None
                self._hora_fin_dia = None

            self._actualizar_label_pagina()
            self.cargar_datos(self._registros, self._grupo)
            self._ultima_actualizacion = datetime.now().strftime("%H:%M:%S")
            self._actualizar_label_actualizado()
        except Exception as e:
            print(f"[Rastreador] Error cargando datos: {e}")
        finally:
            self._finalizar_carga()

    def _on_error_carga(self, mensaje):
        print(f"[Rastreador] Error cargando datos: {mensaje}")
        self._finalizar_carga()

    def _finalizar_carga(self):
        self._carga_en_curso = False
        if self._carga_pendiente:
            self._carga_pendiente = False
            self._solicitar_carga(self.barra_info.fecha.date())

    def _refresh_manual(self):
        print("[VISOR]  Refresh manual solicitado")
        self._solicitar_carga(self.barra_info.fecha.date())

    def _auto_refresh(self):
        """Recarga silenciosamente los datos si estamos en el día de hoy."""
        qdate = self.barra_info.fecha.date()
        if qdate != QDate.currentDate():
            return

        self._solicitar_carga(qdate)

    def _actualizar_label_actualizado(self):
        """Actualiza el label de la barra inferior con la hora del último refresh."""
        if hasattr(self, "lbl_actualizado"):
            self.lbl_actualizado.setText(f"● Actualizado {self._ultima_actualizacion}")

    def _ir_hoy(self):
        self.barra_info.fecha.setDate(QDate.currentDate())

    def _mover_dia(self, delta):
        self.barra_info.fecha.setDate(self.barra_info.fecha.date().addDays(delta))

    def _solicitar_datos_exportacion(self, formato, ruta, fecha_str, usuario=None):
        cb = self._get_cb()
        if cb is None:
            print("[VISOR] ⚠️  No hay callback para exportar")
            QMessageBox.critical(
                self,
                "Error",
                "No se pudo generar el reporte:\nNo hay callback para consultar los datos.",
            )
            return

        kwargs = {"page": 1, "limit": 10000}
        if self._usuario_id:
            kwargs["usuario_id_objetivo"] = self._usuario_id

        self._workers = [worker for worker in self._workers if worker.isRunning()]
        worker = ApiWorker(cb, fecha_str, **kwargs)
        worker.exito.connect(
            lambda datos: self._on_datos_exportacion_cargados(
                datos, formato, ruta, fecha_str, usuario or self._usuario
            )
        )
        worker.error.connect(
            lambda mensaje: self._on_error_exportacion(mensaje)
        )
        self._workers.append(worker)
        worker.start()

    def _on_datos_exportacion_cargados(
        self, datos, formato, ruta, fecha_str, usuario
    ):
        if isinstance(datos, dict):
            registros = datos.get("registros", [])
            grupo = datos.get("grupo", [])
        else:
            registros, grupo = datos

        if not registros:
            print("[VISOR] ⚠️  No hay registros para exportar")
            self.lbl_actualizado.setText("● No hay registros para exportar")
            QMessageBox.warning(
                self, "Sin datos", "No hay registros para exportar."
            )
            return

        if formato == "excel":
            self._exportar_excel(
                ruta, registros, grupo, datos, fecha_str, usuario
            )
        else:
            self._exportar_pdf(ruta, registros, grupo, fecha_str, usuario)

    def _iniciar_worker_exportacion(self, funcion, ruta, *args):
        self._workers = [worker for worker in self._workers if worker.isRunning()]
        worker = ApiWorker(funcion, ruta, *args)
        worker.exito.connect(self._on_exportacion_exitosa)
        worker.error.connect(self._on_error_exportacion)
        self._workers.append(worker)
        self.lbl_actualizado.setText("● Generando reporte...")
        worker.start()

    def _mostrar_mensaje_exportacion(self, icono, titulo, mensaje):
        dialogo = QMessageBox(icono, titulo, mensaje, QMessageBox.Ok, self)
        dialogo.setAttribute(Qt.WA_DeleteOnClose)
        dialogo.open()

    def _on_exportacion_exitosa(self, ruta):
        print(f"[VISOR] Reporte exportado a: {ruta}")
        self.lbl_actualizado.setText(f"● Reporte exportado: {ruta}")
        self._mostrar_mensaje_exportacion(
            QMessageBox.Information,
            "Éxito",
            f"Reporte exportado a:\n{ruta}",
        )

    def _on_error_exportacion(self, mensaje):
        print(f"[VISOR] Error al procesar la exportación: {mensaje}")
        self.lbl_actualizado.setText("● Error al generar reporte")
        self._mostrar_mensaje_exportacion(
            QMessageBox.Critical,
            "Error",
            f"No se pudo generar el reporte:\n{mensaje}",
        )

    # ------------------------------------------------------------
    def _exportar_excel(
        self,
        ruta=None,
        registros=None,
        grupo=None,
        datos=None,
        fecha_str=None,
        usuario=None,
    ):
        """Exporta los registros actuales a un archivo .xlsx."""
        if registros is None and not self._registros and not self._total_registros:
            print("[VISOR] ⚠️  No hay registros para exportar")
            QMessageBox.warning(
                self, "Sin datos", "No hay registros para exportar."
            )
            return

        fecha_str = fecha_str or self.barra_info.fecha.date().toString("yyyy-MM-dd")

        if ruta is None:
            usuario = self._usuario or {}
            nombre_usuario = usuario.get("nombre", "") or ""
            apellido = usuario.get("apellido", "") or ""
            nombre_usuario = f"{nombre_usuario} {apellido}".strip()

            if nombre_usuario:
                nombre_limpio = (
                    nombre_usuario.strip()
                    .lower()
                    .replace(" ", "_")
                    .replace("á", "a").replace("é", "e")
                    .replace("í", "i").replace("ó", "o")
                    .replace("ú", "u").replace("ñ", "n")
                )
                for c in '\\/:*?"<>|':
                    nombre_limpio = nombre_limpio.replace(c, "")
                nombre_default = f"rastreador_{nombre_limpio}_{fecha_str}.xlsx"
            else:
                nombre_default = f"rastreador_{fecha_str}.xlsx"
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar registros como Excel",
                nombre_default,
                "Excel (*.xlsx);;Todos los archivos (*)",
            )
            if not ruta:
                return
            if not ruta.lower().endswith(".xlsx"):
                ruta += ".xlsx"
            self._solicitar_datos_exportacion("excel", ruta, fecha_str)
            return

        registros = registros if registros is not None else self._registros
        grupo = grupo if grupo is not None else self._grupo
        iniciado = datos.get("total_iniciado") if isinstance(datos, dict) else None
        finalizado = datos.get("total_finalizado") if isinstance(datos, dict) else None
        duracion = datos.get("total_duracion") if isinstance(datos, dict) else None
        iniciado_texto = str(
            iniciado
            if iniciado not in (None, "")
            else self.barra_info.lbl_iniciado.itemAt(1).widget().text()
        )
        finalizado_texto = str(
            finalizado
            if finalizado not in (None, "")
            else self.barra_info.lbl_finalizado.itemAt(1).widget().text()
        )
        duracion_texto = (
            self._formatear_total_duracion(duracion)
            if duracion is not None
            else self.barra_info.lbl_duracion.itemAt(1).widget().text()
        )
        self._iniciar_worker_exportacion(
            _generar_excel_exportacion,
            ruta,
            registros,
            grupo,
            fecha_str,
            iniciado_texto,
            finalizado_texto,
            duracion_texto,
            usuario or self._usuario or {},
        )

    # ------------------------------------------------------------
    def _exportar_pdf(
        self, ruta=None, registros=None, grupo=None, fecha_str=None, usuario=None
    ):
        """Exporta los registros actuales a un PDF con plantilla."""
        if registros is None and not self._registros and not self._total_registros:
            print("[VISOR] ⚠️  No hay registros para exportar")
            QMessageBox.warning(
                self, "Sin datos", "No hay registros para exportar."
            )
            return

        fecha_str = fecha_str or self.barra_info.fecha.date().toString("yyyy-MM-dd")

        # Nombre de archivo sugerido
        usuario = usuario or self._usuario or {}

        nombre_limpio = (
            f"{usuario.get('nombre', 'usuario')}_{usuario.get('apellido', '')}"
            .strip()
            .lower()
            .replace(" ", "_")
        )
        for c in '\\/:*?"<>|':
            nombre_limpio = nombre_limpio.replace(c, "")
        nombre_default = f"informe_rastreador_{nombre_limpio}_{fecha_str}.pdf"

               
        from pathlib import Path
        import os
        
        carpeta_documentos = Path(os.path.expanduser("~")) / "Documents"
        carpeta_documentos.mkdir(parents=True, exist_ok=True)
        ruta_sugerida = carpeta_documentos / nombre_default
        if ruta is None:
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar informe como PDF",
                str(ruta_sugerida),
                "PDF (*.pdf);;Todos los archivos (*)",
            )
            if not ruta:
                return
            if not ruta.lower().endswith(".pdf"):
                ruta += ".pdf"
            self._solicitar_datos_exportacion("pdf", ruta, fecha_str, usuario)
            return

        registros = registros if registros is not None else self._registros
        grupo = grupo if grupo is not None else self._grupo

        self._iniciar_worker_exportacion(
            _generar_pdf_exportacion,
            ruta,
            usuario,
            fecha_str,
            registros,
            grupo,
        )
    def closeEvent(self, event):
        """Detiene el auto-refresh al cerrar el visor."""
        if hasattr(self, "_timer_refresh"):
            self._timer_refresh.stop()
        
        if hasattr(self, 'ws_live') and self.ws_live:
            self.ws_live.desconectar()
            # Damos un pequeño margen para que el socket se cierre limpiamente
            # sin que Python se queje del QThread
            from PySide6.QtCore import QTimer
            QTimer.singleShot(200, lambda: None)
        
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "_timer_refresh"):
            self._timer_refresh.start(5000)

    def hideEvent(self, event):
        if hasattr(self, "_timer_refresh"):
            self._timer_refresh.stop()
        super().hideEvent(event)

    # ------------------------------------------------------------
    @staticmethod
    def _parse_duracion(texto):
        try:
            partes = [int(p) for p in str(texto).split(":")]
        except (ValueError, TypeError):
            return 0
        if len(partes) == 3:
            return partes[0] * 3600 + partes[1] * 60 + partes[2]
        if len(partes) == 2:
            return partes[0] * 3600 + partes[1] * 60
        return 0

    @staticmethod
    def _hora_a_decimal(texto):
        try:
            hh, mm = str(texto).split(":")[:2]
            return int(hh) + int(mm) / 60.0
        except (ValueError, AttributeError):
            return None
    def _actualizar_label_pagina(self):
        if hasattr(self, "lbl_pagina"):
            self.lbl_pagina.setText(f"Página {self._pagina_actual} de {self._total_paginas} (Total: {self._total_registros})")
        if hasattr(self, "btn_prev_page"):
            self.btn_prev_page.setEnabled(self._pagina_actual > 1)
        if hasattr(self, "btn_next_page"):
            self.btn_next_page.setEnabled(self._pagina_actual < self._total_paginas)

    def _pagina_anterior(self):
        if self._pagina_actual > 1:
            self._pagina_actual -= 1
            self._recargar_fecha(self.barra_info.fecha.date())

    def _ir_a_ultima_pagina(self):
        if self._total_paginas > 1:
            self._pagina_actual = self._total_paginas
            self._recargar_fecha(self.barra_info.fecha.date())

    def _pagina_siguiente(self):
        if self._pagina_actual < self._total_paginas:
            self._pagina_actual += 1
            self._recargar_fecha(self.barra_info.fecha.date())