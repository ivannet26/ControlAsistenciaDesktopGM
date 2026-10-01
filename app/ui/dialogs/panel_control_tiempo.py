# app/ui/dialogs/panel_control_tiempo.py

from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.recordatorios import (
    guardar,
    guardar_dias,
    leer_bool,
    leer_dias,
    leer_int,
    leer_str,
)


DIAS = ["L", "M", "M", "J", "V", "S", "D"]


QSS = """
QLabel {
    color: #e6edf3;
    background: transparent;
    font-size: 12px;
}

QLabel#titulo {
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
}

QLabel#seccion {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#nota {
    color: #8ea0af;
    font-size: 11px;
    padding-top: 6px;
}

QFrame#linea {
    background: #22323d;
    max-height: 1px;
    min-height: 1px;
    border: none;
}

QSpinBox,
QTimeEdit {
    background: #16232c;
    color: #e6edf3;
    border: 1px solid #22323d;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 80px;
    min-height: 22px;
}

QSpinBox:disabled,
QTimeEdit:disabled {
    color: #5d6b76;
}

QPushButton#dia {
    background: #16232c;
    color: #8ea0af;
    border: 1px solid #22323d;
    border-radius: 4px;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
}

QPushButton#dia:checked {
    background: #2196f3;
    color: #ffffff;
    border-color: #2196f3;
}

QPushButton#dia:disabled {
    color: #5d6b76;
}
"""


# ------------------------------------------------------------------
# Lectura para el monitor de inactividad
# ------------------------------------------------------------------
def leer_umbral_seg() -> int:
    """Segundos sin actividad antes de avisar."""
    return max(1, leer_int("inact_umbral_min")) * 60


def leer_limite_seg() -> int:
    """Segundos sin responder antes de detener el temporizador."""
    return max(1, leer_int("inact_limite_min")) * 60


class Switch(QAbstractButton):
    def __init__(self, marcado: bool = False, parent=None):
        super().__init__(parent)

        self.setCheckable(True)
        self.setChecked(marcado)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(40, 22)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)

        p.setBrush(
            QColor("#2196f3" if self.isChecked() else "#3a4651")
        )
        p.drawRoundedRect(self.rect(), 11, 11)

        p.setBrush(QColor("#ffffff"))

        x = self.width() - 20 if self.isChecked() else 2
        p.drawEllipse(x, 2, 18, 18)

        p.end()


class PanelControlTiempo(QWidget):
    """
    Contenido de la pestaña 'Control de tiempo'.
    Guarda al instante cada cambio.
    """

    cambiada = Signal()

    def __init__(self, es_admin: bool = False, parent=None):
        super().__init__(parent)

        self.setStyleSheet(QSS)
        self._switch_rec = None

        # ==========================================================
        # CONTENEDOR GENERAL CON SCROLL INVISIBLE
        # ==========================================================
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        # Barra invisible, pero el scroll sigue funcionando
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollArea > QWidget {
                background: transparent;
            }

            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        self.contenido = QWidget()

        raiz = QVBoxLayout(self.contenido)
        raiz.setContentsMargins(32, 20, 32, 20)
        raiz.setSpacing(12)

        self.scroll.setWidget(self.contenido)
        layout_principal.addWidget(self.scroll)

        # ==========================================================
        # TÍTULO
        # ==========================================================
        titulo = QLabel("Control de tiempo")
        titulo.setObjectName("titulo")
        raiz.addWidget(titulo)

        # ==========================================================
        # COMPORTAMIENTO
        # ==========================================================
        raiz.addWidget(
            self._seccion("Comportamiento del temporizador")
        )

        raiz.addLayout(
            self._fila_switch(
                "Iniciar el temporizador cuando se inicia la aplicación",
                "iniciar_con_app",
            )
        )

        raiz.addLayout(
            self._fila_switch(
                "Detener el temporizador si la pantalla se bloquea",
                "detener_bloqueo",
            )
        )

        raiz.addLayout(
            self._fila_switch(
                "Detener el temporizador si el ordenador entra en reposo",
                "detener_reposo",
            )
        )

        raiz.addLayout(
            self._fila_switch(
                "Detener el temporizador si el ordenador se apaga",
                "detener_apagado",
            )
        )

        raiz.addWidget(self._linea())

        # ==========================================================
        # RECORDATORIO
        # ==========================================================
        raiz.addWidget(
            self._seccion("Recordatorio")
        )

        raiz.addLayout(
            self._fila_switch(
                "Recuérdame rastrear el tiempo",
                "rec_activo",
            )
        )

        self.bloque_rec = QWidget()

        lb = QVBoxLayout(self.bloque_rec)
        lb.setContentsMargins(0, 6, 0, 6)
        lb.setSpacing(0)

        # ----------------------------------------------------------
        # Frecuencia
        # ----------------------------------------------------------
        self.spin_cada = self._spin(
            "rec_cada_min",
            1,
            480,
        )

        fila_cada = QHBoxLayout()
        fila_cada.setContentsMargins(0, 0, 0, 0)
        fila_cada.setSpacing(12)

        lbl_cada = QLabel(
            "Recuérdame rastrear el tiempo cada"
        )

        fila_cada.addWidget(lbl_cada, 1)
        fila_cada.addWidget(self.spin_cada)

        lb.addLayout(fila_cada)
        lb.addSpacing(12)

        # ----------------------------------------------------------
        # Hora de inicio
        # ----------------------------------------------------------
        self.hora_inicio = self._time_edit(
            "rec_inicio",
            "08:00",
        )

        fila_inicio = QHBoxLayout()
        fila_inicio.setContentsMargins(0, 0, 0, 0)
        fila_inicio.setSpacing(12)

        lbl_inicio = QLabel(
            "Empieza a recordarme a la(s)"
        )

        fila_inicio.addWidget(lbl_inicio, 1)
        fila_inicio.addWidget(self.hora_inicio)

        lb.addLayout(fila_inicio)
        lb.addSpacing(12)

        # ----------------------------------------------------------
        # Hora final
        # ----------------------------------------------------------
        self.hora_fin = self._time_edit(
            "rec_fin",
            "18:00",
        )

        fila_fin = QHBoxLayout()
        fila_fin.setContentsMargins(0, 0, 0, 0)
        fila_fin.setSpacing(12)

        lbl_fin = QLabel(
            "Deja de recordarme a la(s)"
        )

        fila_fin.addWidget(lbl_fin, 1)
        fila_fin.addWidget(self.hora_fin)

        lb.addLayout(fila_fin)
        lb.addSpacing(16)

        # ----------------------------------------------------------
        # Días
        # ----------------------------------------------------------
        lbl_dias = QLabel(
            "Recuérdame los días"
        )

        lb.addWidget(lbl_dias)
        lb.addSpacing(8)

        fila_dias = QHBoxLayout()
        fila_dias.setContentsMargins(0, 0, 0, 0)
        fila_dias.setSpacing(8)

        activos = leer_dias()
        self.botones_dias = []

        for i, letra in enumerate(DIAS):
            b = QPushButton(letra)

            b.setObjectName("dia")
            b.setCheckable(True)
            b.setChecked(i in activos)
            b.setCursor(Qt.PointingHandCursor)

            b.toggled.connect(
                self._dias_cambiaron
            )

            self.botones_dias.append(b)
            fila_dias.addWidget(b)

        fila_dias.addStretch()

        lb.addLayout(fila_dias)
        lb.addSpacing(10)

        # ----------------------------------------------------------
        # Nota
        # ----------------------------------------------------------
        nota = QLabel(
            "El aviso aparece como notificación de tu computadora."
        )

        nota.setObjectName("nota")

        lb.addWidget(nota)

        raiz.addWidget(self.bloque_rec)

        self.bloque_rec.setEnabled(
            leer_bool("rec_activo")
        )

        if self._switch_rec is not None:
            self._switch_rec.toggled.connect(
                self.bloque_rec.setEnabled
            )

        # ==========================================================
        # INACTIVIDAD
        # ==========================================================
        if es_admin:
            raiz.addWidget(
                self._linea()
            )

            raiz.addWidget(
                self._seccion(
                    "Tiempo de inactividad (administrador)"
                )
            )

            self.spin_umbral = self._spin(
                "inact_umbral_min",
                1,
                120,
            )

            raiz.addLayout(
                self._fila_campo(
                    "Avisar tras este tiempo sin actividad",
                    self.spin_umbral,
                )
            )

            self.spin_limite = self._spin(
                "inact_limite_min",
                1,
                480,
            )

            raiz.addLayout(
                self._fila_campo(
                    "Detener el temporizador si no responde en",
                    self.spin_limite,
                )
            )

        # Mantiene el contenido arriba
        raiz.addStretch()

    # ==============================================================
    # HELPERS
    # ==============================================================

    def _seccion(self, texto: str) -> QLabel:
        l = QLabel(texto)
        l.setObjectName("seccion")
        return l

    def _linea(self) -> QFrame:
        f = QFrame()
        f.setObjectName("linea")
        return f

    def _guardar(self, clave, valor):
        guardar(clave, valor)
        self.cambiada.emit()

    def _spin(
        self,
        clave: str,
        minimo: int,
        maximo: int,
    ) -> QSpinBox:

        sp = QSpinBox()

        sp.setRange(
            minimo,
            maximo,
        )

        sp.setValue(
            leer_int(clave)
        )

        sp.setSuffix(" min")

        sp.setKeyboardTracking(False)

        sp.valueChanged.connect(
            lambda v, c=clave: self._guardar(c, v)
        )

        return sp

    def _fila_switch(
        self,
        texto: str,
        clave: str,
    ) -> QHBoxLayout:

        fila = QHBoxLayout()

        fila.addWidget(
            QLabel(texto),
            1,
        )

        sw = Switch(
            leer_bool(clave)
        )

        sw.toggled.connect(
            lambda v, c=clave: self._guardar(c, v)
        )

        fila.addWidget(sw)

        if clave == "rec_activo":
            self._switch_rec = sw

        return fila

    def _fila_campo(
        self,
        texto: str,
        campo: QWidget,
    ) -> QHBoxLayout:

        fila = QHBoxLayout()

        fila.addWidget(
            QLabel(texto),
            1,
        )

        fila.addWidget(campo)

        return fila

    def _time_edit(
        self,
        clave: str,
        defecto: str,
    ) -> QTimeEdit:

        valor = leer_str(clave) or defecto

        te = QTimeEdit(
            QTime.fromString(
                valor,
                "HH:mm",
            )
        )

        te.setDisplayFormat("HH:mm")
        te.setKeyboardTracking(False)

        te.timeChanged.connect(
            lambda t, c=clave:
            self._guardar(
                c,
                t.toString("HH:mm"),
            )
        )

        return te

    def _dias_cambiaron(self, _):
        guardar_dias(
            [
                i
                for i, b in enumerate(self.botones_dias)
                if b.isChecked()
            ]
        )

        self.cambiada.emit()