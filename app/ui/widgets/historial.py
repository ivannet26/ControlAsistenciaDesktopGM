# app/ui/widgets/historial.py
from datetime import date, datetime

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
)

from app.styles import tracker as S
from app.styles import historial as H
from app.utils.fechas import lunes_de_semana, etiqueta_dia, etiqueta_semana
from app.utils.workers import formatear_duracion
from app.ui.widgets.registro_card import RegistroCard


class HistorialView(QScrollArea):
    reanudar = Signal(dict)
    eliminar = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.viewport().setStyleSheet("background: transparent;")
        self.setStyleSheet(S.QSS_SCROLL)

        self.contenedor = QWidget()
        self.contenedor.setStyleSheet(H.QSS_HISTORIAL_CONTENEDOR)

        self.layout = QVBoxLayout(self.contenedor)
        self.layout.setContentsMargins(0, 0, 6, 0)
        self.layout.setSpacing(6)
        # Sin setAlignment: el addStretch() final empuja el contenido arriba.

        self.setWidget(self.contenedor)

        # Qt avisa cuando el rango real de scroll cambia; solo ahí
        # decidimos si mostrar u ocultar la barra (sin medir a mano).
        self.verticalScrollBar().rangeChanged.connect(self._on_rango_cambiado)

    # ------------------------------------------------------------------
    # Scrollbar
    # ------------------------------------------------------------------
    def _on_rango_cambiado(self, minimo: int, maximo: int):
        politica = (
            Qt.ScrollBarAsNeeded if maximo > 0 else Qt.ScrollBarAlwaysOff
        )
        if self.verticalScrollBarPolicy() != politica:
            self.setVerticalScrollBarPolicy(politica)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def _limpiar(self):
        """Elimina widgets y stretches del layout de inmediato."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)  # deja de contar ya en el layout
                w.deleteLater()

    def cargar(self, registros: list[dict]):
        self._limpiar()
        registros = registros or []

        if not registros:
            vacio = QLabel("No hay entradas registradas.")
            vacio.setStyleSheet(H.QSS_HISTORIAL_VACIO)
            vacio.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(vacio)
            self.layout.addStretch(1)
            self.verticalScrollBar().setValue(0)
            return

        # Agrupar por día
        grupos_dia: dict[date, list] = {}
        for r in registros:
            try:
                fecha = datetime.fromisoformat(r["inicio"]).date()
            except Exception:
                continue
            grupos_dia.setdefault(fecha, []).append(r)

        # Agrupar por semana
        grupos_semana: dict[date, dict] = {}
        for fecha, regs in grupos_dia.items():
            lunes = lunes_de_semana(fecha)
            grupos_semana.setdefault(lunes, {})[fecha] = regs

        semanas = sorted(grupos_semana.keys(), reverse=True)

        for lunes in semanas:
            dias = grupos_semana[lunes]
            total_semana = sum(
                r.get("duracion_segundos", 0)
                for regs in dias.values() for r in regs
            )
            self.layout.addWidget(self._header_semana(lunes, total_semana))

            for fecha in sorted(dias.keys(), reverse=True):
                regs = dias[fecha]
                total_dia = sum(r.get("duracion_segundos", 0) for r in regs)
                self.layout.addWidget(self._header_dia(fecha, total_dia))

                for r in regs:
                    card = RegistroCard(r)
                    card.reanudar.connect(self.reanudar)
                    card.eliminar.connect(self.eliminar)
                    self.layout.addWidget(card)

        # Ocupa el espacio sobrante y mantiene todo pegado arriba
        self.layout.addStretch(1)
        self.verticalScrollBar().setValue(0)
        QTimer.singleShot(200, self._debug)  # TEMPORAL

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------
    def _header_semana(self, lunes: date, total_seg: int) -> QWidget:
        w = QWidget()
        w.setStyleSheet(H.QSS_HEADER_SEMANA_WIDGET)
        w.setFixedHeight(30)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 0, 12, 0)

        label = QLabel(etiqueta_semana(lunes))
        label.setStyleSheet(H.QSS_HEADER_SEMANA_LABEL)
        lay.addWidget(label)
        lay.addStretch()

        total = QLabel(formatear_duracion(total_seg))
        total.setStyleSheet(H.QSS_HEADER_SEMANA_TOTAL)
        lay.addWidget(total)
        return w

    def _header_dia(self, fecha: date, total_seg: int) -> QWidget:
        w = QWidget()
        w.setStyleSheet(H.QSS_HEADER_DIA_WIDGET)
        w.setFixedHeight(26)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 0, 12, 0)

        label = QLabel(etiqueta_dia(fecha))
        label.setStyleSheet(H.QSS_HEADER_DIA_LABEL)
        lay.addWidget(label)
        lay.addStretch()

        total = QLabel(formatear_duracion(total_seg))
        total.setStyleSheet(H.QSS_HEADER_DIA_TOTAL)
        lay.addWidget(total)
        return w

    # ------------------------------------------------------------------
    # DEBUG TEMPORAL (borrar cuando encontremos el problema)
    # ------------------------------------------------------------------
    def _debug(self):
        print("viewport h:", self.viewport().height())
        print("contenedor h:", self.contenedor.height())
        print("layout sizeHint:", self.layout.sizeHint())
        print("contenedor minSizeHint:", self.contenedor.minimumSizeHint())
        print("scroll max:", self.verticalScrollBar().maximum())
        ultimo = None
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w:
                ultimo = w
        if ultimo:
            print(
                "ultimo widget bottom:", ultimo.geometry().bottom(),
                "| card h:", ultimo.height(),
                "| minH:", ultimo.minimumHeight(),
            )