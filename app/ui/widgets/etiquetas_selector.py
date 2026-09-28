# app/ui/widgets/etiquetas_selector.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton,
)

from app.styles import etiquetas as E


class EtiquetasSelector(QWidget):
    """Selector de etiquetas múltiples con chips."""

    cambio = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.seleccionadas: list[dict] = []
        self._armar_ui()

    def _armar_ui(self):
        self.setStyleSheet(E.QSS_ETIQUETAS_CONTENEDOR)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        fila = QHBoxLayout()
        fila.setSpacing(6)

        label = QLabel("Etiquetas:")
        label.setStyleSheet(E.QSS_ETIQUETAS_LABEL)
        fila.addWidget(label)

        self.combo = QComboBox()
        self.combo.addItem("Agregar etiqueta...", None)
        self.combo.setFixedHeight(24)
        self.combo.setStyleSheet(E.QSS_ETIQUETAS_COMBO)
        self.combo.currentIndexChanged.connect(self._on_seleccionada)
        fila.addWidget(self.combo, 1)
        layout.addLayout(fila)

        # Contenedor de chips
        self.chips_container = QWidget()
        self.chips_container.setStyleSheet("background: transparent; border: none;")
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 2, 0, 0)
        self.chips_layout.setSpacing(4)
        self.chips_layout.addStretch()
        self.chips_container.setVisible(False)
        layout.addWidget(self.chips_container)

    # ---------- API pública ----------
    def cargar_etiquetas(self, etiquetas: list[dict]):
        self.combo.clear()
        self.combo.addItem("Agregar etiqueta...", None)
        for e in etiquetas or []:
            self.combo.addItem(e.get("nombre", f"Etiqueta {e.get('id')}"), e)

    def set_seleccionadas(self, etiquetas: list[dict]):
        self.seleccionadas = etiquetas or []
        self._renderizar_chips()
        self.cambio.emit()

    def ids(self) -> list[int]:
        return [e["id"] for e in self.seleccionadas]

    def limpiar(self):
        self.seleccionadas = []
        self._renderizar_chips()
        self.cambio.emit()

    def set_enabled(self, valor: bool):
        self.combo.setEnabled(valor)

    # ---------- Internos ----------
    def _on_seleccionada(self, index):
        if index <= 0:
            return
        etiqueta = self.combo.itemData(index)
        if not etiqueta:
            return

        ids_actuales = [e["id"] for e in self.seleccionadas]
        if etiqueta.get("id") not in ids_actuales:
            self.seleccionadas.append(etiqueta)

        self.combo.blockSignals(True)
        self.combo.setCurrentIndex(0)
        self.combo.blockSignals(False)

        self._renderizar_chips()
        self.cambio.emit()

    def _quitar(self, etiqueta_id: int):
        self.seleccionadas = [
            e for e in self.seleccionadas if e["id"] != etiqueta_id
        ]
        self._renderizar_chips()
        self.cambio.emit()

    def _renderizar_chips(self):
        while self.chips_layout.count() > 1:
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.seleccionadas:
            self.chips_container.setVisible(False)
            return

        self.chips_container.setVisible(True)
        for e in self.seleccionadas:
            chip = QPushButton(f"{e.get('nombre', '')} ✕")
            chip.setFixedHeight(20)
            chip.setCursor(Qt.PointingHandCursor)
            chip.setStyleSheet(E.QSS_CHIP)
            chip.clicked.connect(lambda _, eid=e["id"]: self._quitar(eid))
            self.chips_layout.insertWidget(self.chips_layout.count() - 1, chip)