from datetime import datetime
from PySide6.QtCore import QTimer, Qt, QEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtGui import QFont, QColor
from app.services.api_client import ApiClient


# ---------- Botón de acción con icono + título + subtítulo ----------
class ActionButton(QPushButton):
    def __init__(self, icono, titulo, subtitulo, bg, bg_hover, parent=None):
        super().__init__(parent)
        self._bg = bg
        self._bg_hover = bg_hover
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(54)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 6, 14, 6)
        lay.setSpacing(10)

        self.lbl_icono = QLabel(icono)
        self.lbl_icono.setFont(QFont("Segoe UI Symbol", 12))
        self.lbl_icono.setFixedWidth(22)
        self.lbl_icono.setAlignment(Qt.AlignCenter)

        col = QVBoxLayout()
        col.setSpacing(0)
        col.setAlignment(Qt.AlignVCenter)
        self.lbl_titulo = QLabel(titulo)
        self.lbl_subtitulo = QLabel(subtitulo)
        col.addWidget(self.lbl_titulo)
        col.addWidget(self.lbl_subtitulo)

        lay.addWidget(self.lbl_icono)
        lay.addLayout(col)
        lay.addStretch()

        # Los labels no deben robar el click al botón
        for w in (self.lbl_icono, self.lbl_titulo, self.lbl_subtitulo):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._aplicar_estilo()

    def changeEvent(self, event):
        if event.type() == QEvent.EnabledChange:
            self._aplicar_estilo()
        super().changeEvent(event)

    def _aplicar_estilo(self):
        if self.isEnabled():
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._bg};
                    border: none;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {self._bg_hover};
                }}
            """)
            c_icono, c_titulo, c_sub = "#ffffff", "#ffffff", "rgba(255,255,255,0.78)"
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1a2a33;
                    border: none;
                    border-radius: 4px;
                }
            """)
            c_icono, c_titulo, c_sub = "#3b4b56", "#3b4b56", "#33424c"

        self.lbl_icono.setStyleSheet(f"color: {c_icono}; background: transparent;")
        self.lbl_titulo.setStyleSheet(
            f"color: {c_titulo}; background: transparent; font-size: 11px; font-weight: 600; letter-spacing: 0.4px;"
        )
        self.lbl_subtitulo.setStyleSheet(
            f"color: {c_sub}; background: transparent; font-size: 10px;"
        )


class PanelAsistencia(QDialog):
    def __init__(self, client: ApiClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Marcar Asistencia")
        self.setMinimumSize(540, 400)
        self.resize(600, 430)

        # Datos del día (para calcular la duración en vivo)
        self._entrada = None
        self._inicio_break = None
        self._fin_break = None
        self._salida = None

        self.setStyleSheet("""
            QDialog {
                background-color: #22313a;
            }
            QLabel {
                color: #e6edf3;
                font-family: "Segoe UI", sans-serif;
            }
            QFrame#card {
                background-color: #101b22;
                border: 1px solid #1c2a33;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: transparent;
                color: #e6edf3;
                border: none;
                border-top: 1px solid #1f2d36;
                outline: none;
                font-size: 12px;
            }
            QTableWidget::item {
                padding-left: 10px;
                border-bottom: 1px solid #1f2d36;
            }
            QHeaderView {
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: transparent;
                color: #8ea0af;
                padding: 8px 10px;
                border: none;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.8px;
            }
            QTableCornerButton::section {
                background-color: transparent;
                border: none;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ================= Tarjeta: Hora actual =================
        card_reloj = QFrame()
        card_reloj.setObjectName("card")
        lay_reloj = QVBoxLayout(card_reloj)
        lay_reloj.setContentsMargins(10, 8, 10, 8)
        lay_reloj.setSpacing(2)

        fila_titulo = QHBoxLayout()
        fila_titulo.setAlignment(Qt.AlignCenter)
        fila_titulo.setSpacing(8)
        ico_reloj = QLabel("◷")
        ico_reloj.setStyleSheet("color: #38bdf8; font-size: 13px;")
        lbl_hora_actual = QLabel("HORA ACTUAL")
        lbl_hora_actual.setStyleSheet(
            "color: #8ea0af; font-size: 10px; font-weight: 600; letter-spacing: 1px;"
        )
        fila_titulo.addWidget(ico_reloj)
        fila_titulo.addWidget(lbl_hora_actual)
        lay_reloj.addLayout(fila_titulo)

        self.lbl_reloj = QLabel("00:00:00")
        self.lbl_reloj.setAlignment(Qt.AlignCenter)
        self.lbl_reloj.setStyleSheet(
            "font-size: 28px; font-weight: normal; color: #ffffff; letter-spacing: 1px;"
        )
        lay_reloj.addWidget(self.lbl_reloj)
        root.addWidget(card_reloj)

        # ================= Botones (grid 2x2) =================
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        self.btn_entrada = ActionButton("⇥", "ENTRADA", "Fichar entrada", "#0e8f66", "#10a878")
        self.btn_break_inicio = ActionButton("❚❚", "INICIO DESCANSO", "Iniciar tiempo de break", "#b45309", "#c9640f")
        self.btn_break_fin = ActionButton("►", "FIN DESCANSO", "Terminar tiempo de break", "#4b5563", "#5b6573")
        self.btn_salida = ActionButton("⇤", "SALIDA", "Fichar salida", "#991b1b", "#b02222")

        self.btn_entrada.clicked.connect(lambda: self._marcar("entrada"))
        self.btn_break_inicio.clicked.connect(lambda: self._marcar("break/iniciar"))
        self.btn_break_fin.clicked.connect(lambda: self._marcar("break/terminar"))
        self.btn_salida.clicked.connect(lambda: self._marcar("salida"))

        grid.addWidget(self.btn_entrada, 0, 0)
        grid.addWidget(self.btn_break_inicio, 0, 1)
        grid.addWidget(self.btn_break_fin, 1, 0)
        grid.addWidget(self.btn_salida, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        root.addLayout(grid)

        # ================= Tarjeta: Registros del día =================
        card_tabla = QFrame()
        card_tabla.setObjectName("card")
        lay_tabla = QVBoxLayout(card_tabla)
        lay_tabla.setContentsMargins(0, 0, 0, 0)
        lay_tabla.setSpacing(0)

        cab = QHBoxLayout()
        cab.setContentsMargins(12, 8, 12, 8)
        cab.setSpacing(8)
        lbl_tabla = QLabel("Registros del día")
        lbl_tabla.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        cab.addWidget(lbl_tabla)
        cab.addStretch()

        self.lbl_estado = QLabel("SIN ENTRADA")
        self.lbl_estado.setAlignment(Qt.AlignCenter)
        cab.addWidget(self.lbl_estado)

        self.btn_refrescar = QPushButton("⟳")
        self.btn_refrescar.setToolTip("Actualizar registros")
        self.btn_refrescar.setCursor(Qt.PointingHandCursor)
        self.btn_refrescar.setFixedSize(26, 22)
        self.btn_refrescar.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #2c3d47;
                border-radius: 3px;
                color: #cbd5dc;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1a2a33; }
        """)
        self.btn_refrescar.clicked.connect(self._cargar_estado_y_registros)
        cab.addWidget(self.btn_refrescar)
        lay_tabla.addLayout(cab)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["ENTRADA", "INICIO DESCANSO", "FIN DESCANSO", "DURACIÓN", "SALIDA"]
        )
        hh = self.tabla.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.NoSelection)
        self.tabla.setShowGrid(False)
        self.tabla.setRowCount(0)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(32)
        self.tabla.setFocusPolicy(Qt.NoFocus)
        lay_tabla.addWidget(self.tabla)

        root.addWidget(card_tabla, 1)

        self._aplicar_badge("SIN_ENTRADA")

        # ================= Timer =================
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_reloj)
        self.timer.start(1000)
        self._actualizar_reloj()

        self._cargar_estado_y_registros()

    # ------------------------------------------------------------------
    def _actualizar_reloj(self):
        self.lbl_reloj.setText(datetime.now().strftime("%H:%M:%S"))

    def _calc_duracion(self):
        """Duración del descanso: solo se muestra cuando ya terminó (inicio y fin)."""
        if not (self._inicio_break and self._fin_break):
            return "—"
        fmt = "%H:%M:%S"
        try:
            b0 = datetime.strptime(self._inicio_break, fmt)
            b1 = datetime.strptime(self._fin_break, fmt)
            s = max(int((b1 - b0).total_seconds()), 0)
            return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"
        except Exception:
            return "—"

    def _aplicar_badge(self, estado):
        colores = {
            "SIN_ENTRADA": ("#8ea0af", "rgba(142,160,175,0.10)"),
            "TRABAJANDO": ("#10b981", "rgba(16,185,129,0.12)"),
            "EN_BREAK": ("#f59e0b", "rgba(245,158,11,0.12)"),
            "FINALIZADO": ("#ef4444", "rgba(239,68,68,0.12)"),
        }
        fg, bg = colores.get(estado, colores["SIN_ENTRADA"])
        self.lbl_estado.setText(estado.replace("_", " "))
        self.lbl_estado.setStyleSheet(f"""
            color: {fg};
            background-color: {bg};
            border: 1px solid {fg};
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.8px;
        """)

    def _actualizar_estado_botones(self, estado):
        self._aplicar_badge(estado)
        self.btn_entrada.setEnabled(estado == "SIN_ENTRADA")
        # El descanso solo se puede tomar una vez al día
        ya_tomo_descanso = bool(self._inicio_break)
        self.btn_break_inicio.setEnabled(estado == "TRABAJANDO" and not ya_tomo_descanso)
        self.btn_break_fin.setEnabled(estado == "EN_BREAK")
        self.btn_salida.setEnabled(estado == "TRABAJANDO")

    def _marcar(self, endpoint):
        try:
            if endpoint == "entrada":
                response = self.client.registrar_entrada()
            elif endpoint == "break/iniciar":
                response = self.client.iniciar_break()
            elif endpoint == "break/terminar":
                response = self.client.terminar_break()
            elif endpoint == "salida":
                response = self.client.registrar_salida()
            else:
                response = None

            if response:
                QMessageBox.information(self, "Éxito", "Marcaje registrado correctamente")
                self._cargar_estado_y_registros()
            else:
                QMessageBox.warning(self, "Error", "No se pudo marcar la asistencia. Revisa la conexión.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de conexión: {e}")

    def _cargar_estado_y_registros(self):
        try:
            data = self.client.obtener_asistencia_hoy()
            if not data:
                return

            estado = data.get("estado", "SIN_ENTRADA")

            registros = data.get("registros", [])
            self._entrada = self._inicio_break = self._fin_break = self._salida = None

            for reg in registros:
                tipo = reg.get("tipo")
                hora = reg.get("hora", "")
                hora_str = hora.split("T")[1][:8] if "T" in hora else hora

                if tipo == "ENTRADA":
                    self._entrada = hora_str
                elif tipo == "BREAK_INICIO":
                    self._inicio_break = hora_str
                elif tipo == "BREAK_FIN":
                    self._fin_break = hora_str
                elif tipo == "SALIDA":
                    self._salida = hora_str

            # Ahora que se conocen los registros, ajustar botones
            self._actualizar_estado_botones(estado)

            self.tabla.setRowCount(0)
            self.tabla.insertRow(0)

            valores = [
                self._entrada or "—",
                self._inicio_break or "—",
                self._fin_break or "—",
                self._calc_duracion(),
                self._salida or "—",
            ]
            for col, val in enumerate(valores):
                item = QTableWidgetItem(val)
                if col == 3:  # Duración en azul, como en el diseño web
                    item.setForeground(QColor("#60a5fa"))
                self.tabla.setItem(0, col, item)

        except Exception as e:
            print(f"Error cargando datos: {e}")