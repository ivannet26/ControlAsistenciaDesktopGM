# app/ui/widgets/registro_card.py
import math
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QSize, QRectF, QPointF
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QPolygonF
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)

from app.styles import historial as H
from app.styles.colors import COLOR_PUNTO_VERDE
from app.utils.workers import formatear_duracion


# ======================================================================
# Utilidades
# ======================================================================
def crear_icono_reanudar(size: int = 14, color: str = "#2196f3") -> QIcon:
    """
    Dibuja una flecha circular (reanudar) nítida, también en pantallas HiDPI.
    El arco va en sentido antihorario y la punta de flecha queda al final,
    apuntando en la dirección del arco.
    """
    escala = 2  # render al doble para que no se vea pixelado
    pixmap = QPixmap(size * escala, size * escala)
    pixmap.setDevicePixelRatio(escala)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    cx = cy = size / 2
    radio = size / 2 - 2.5

    # --- Arco (ángulos de Qt: antihorario, 0° = las 3 en punto) ---
    ang_inicio = 40
    ang_span = 290
    ang_fin = ang_inicio + ang_span  # 330°

    pen = QPen(QColor(color))
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    rect = QRectF(cx - radio, cy - radio, radio * 2, radio * 2)
    painter.drawArc(rect, int(ang_inicio * 16), int(ang_span * 16))

    # --- Punta de flecha al final del arco ---
    a = math.radians(ang_fin)
    px = cx + radio * math.cos(a)
    py = cy - radio * math.sin(a)      # eje Y de pantalla va hacia abajo

    # Tangente en sentido antihorario (coordenadas de pantalla)
    tx, ty = -math.sin(a), -math.cos(a)
    nx, ny = -ty, tx                   # normal

    largo, ancho = 2.8, 2.3
    punta = QPointF(px + tx * largo, py + ty * largo)
    base1 = QPointF(px + nx * ancho, py + ny * ancho)
    base2 = QPointF(px - nx * ancho, py - ny * ancho)

    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(QPolygonF([punta, base1, base2]))

    painter.end()
    return QIcon(pixmap)


class LabelElidido(QLabel):
    """
    QLabel de una sola línea que corta con "…" si no cabe.
    No usa wordWrap, así que su alto mínimo es siempre el de una línea
    y no infla el alto del layout que lo contiene.
    """

    def __init__(self, texto: str = "", parent=None):
        super().__init__(parent)
        self._texto_completo = texto
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setMinimumWidth(0)
        self._elidir()

    def setText(self, texto: str):
        self._texto_completo = texto
        self._elidir()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elidir()

    def _elidir(self):
        ancho = max(self.contentsRect().width(), 0)
        elidido = self.fontMetrics().elidedText(
            self._texto_completo, Qt.ElideRight, ancho
        )
        super().setText(elidido)
        self.setToolTip(
            self._texto_completo if elidido != self._texto_completo else ""
        )


# ======================================================================
# Tarjeta
# ======================================================================
class RegistroCard(QFrame):
    """Tarjeta de un registro, con estilo limpio y bordes suaves."""

    reanudar = Signal(dict)
    eliminar = Signal(int)

    def __init__(self, registro: dict, parent=None):
        super().__init__(parent)
        self.registro = registro

        self.setObjectName("RegistroCard")
        self.setStyleSheet(H.QSS_TARJETA_REGISTRO)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._armar_ui()

    # ============================================================
    # UI
    # ============================================================
    def _armar_ui(self):
        r = self.registro

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # ---------- Fila 1: descripción + duración + acciones ----------
        fila1 = QHBoxLayout()
        fila1.setSpacing(8)

        # Descripción (flexible, una línea con "…")
        desc = r.get("descripcion") or "(sin descripción)"
        label_desc = LabelElidido(desc)
        label_desc.setStyleSheet(H.QSS_TARJETA_DESC)
        fila1.addWidget(label_desc, 1)

        # Duración (fija)
        label_dur = QLabel(formatear_duracion(r.get("duracion_segundos", 0)))
        label_dur.setStyleSheet(H.QSS_TARJETA_DURACION)
        label_dur.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        fila1.addWidget(label_dur)

        # Botón reanudar
        btn_play = QPushButton()
        btn_play.setFixedSize(22, 22)
        btn_play.setCursor(Qt.PointingHandCursor)
        btn_play.setToolTip("Reanudar esta actividad")
        btn_play.setIcon(crear_icono_reanudar(14, "#2196f3"))
        btn_play.setIconSize(QSize(14, 14))
        btn_play.setStyleSheet(H.QSS_TARJETA_BTN_PLAY)
        btn_play.clicked.connect(lambda: self.reanudar.emit(self.registro))
        fila1.addWidget(btn_play)

        # Botón eliminar
        btn_del = QPushButton("✕")
        btn_del.setFixedSize(22, 22)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setToolTip("Eliminar esta actividad")
        btn_del.setStyleSheet(H.QSS_TARJETA_BTN_DEL)
        btn_del.clicked.connect(
            lambda: self.eliminar.emit(self.registro.get("id"))
        )
        fila1.addWidget(btn_del)

        layout.addLayout(fila1)

        # ---------- Fila 2: proyecto · tarea | hora ----------
        fila2 = QHBoxLayout()
        fila2.setSpacing(8)

        proyecto = r.get("nombre_proyecto") or "Sin proyecto"
        tarea = r.get("titulo_tarea") or ""
        color_proyecto = r.get("color_proyecto") or COLOR_PUNTO_VERDE

        texto_proy = f"● {proyecto}"
        if tarea:
            texto_proy += f" · {tarea}"

        label_proy = LabelElidido(texto_proy)
        label_proy.setStyleSheet(
            f"color: {color_proyecto};" + H.QSS_TARJETA_PROYECTO
        )
        fila2.addWidget(label_proy, 1)

        # Hora (24h, compacto)
        try:
            inicio_dt = datetime.fromisoformat(r["inicio"])
            fin_str = r.get("fin")
            hora_texto = inicio_dt.strftime("%H:%M")
            if fin_str:
                fin_dt = datetime.fromisoformat(fin_str)
                hora_texto += f" - {fin_dt.strftime('%H:%M')}"
        except Exception:
            hora_texto = ""

        label_hora = QLabel(hora_texto)
        label_hora.setStyleSheet(H.QSS_TARJETA_HORA)
        label_hora.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        fila2.addWidget(label_hora)

        layout.addLayout(fila2)

        # ---------- Fila 3: etiquetas (una sola línea, máx 3 + badge) ----------
        etiquetas = r.get("etiquetas") or []
        if etiquetas:
            fila3 = QHBoxLayout()
            fila3.setSpacing(4)
            fila3.setContentsMargins(0, 3, 0, 0)

            max_visibles = 3
            for e in etiquetas[:max_visibles]:
                nombre_completo = e.get("nombre", "") or ""
                nombre = nombre_completo[:20]
                if len(nombre_completo) > 20:
                    nombre += "…"
                chip = QLabel(nombre)
                chip.setStyleSheet(H.QSS_TARJETA_CHIP)
                chip.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
                if nombre_completo:
                    chip.setToolTip(nombre_completo)
                fila3.addWidget(chip)

            ocultas = len(etiquetas) - max_visibles
            if ocultas > 0:
                badge = QLabel(f"+{ocultas}")
                badge.setStyleSheet(H.QSS_TARJETA_CHIP)
                badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
                nombres = "\n".join(
                    f"• {x.get('nombre', '')}" for x in etiquetas[max_visibles:]
                )
                badge.setToolTip(nombres)
                fila3.addWidget(badge)

            fila3.addStretch()
            layout.addLayout(fila3)