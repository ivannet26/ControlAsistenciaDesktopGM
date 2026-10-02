from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QCheckBox, QComboBox, QScrollArea,
    QSizePolicy, QButtonGroup, QStackedWidget,
)
from app.ui.dialogs.panel_control_tiempo import PanelControlTiempo

from app.utils import autostart
from app.utils import preferencias_store as PS
from app.styles.colors import (
    COLOR_FONDO, COLOR_PANEL, COLOR_BORDE, COLOR_BORDE_INPUT,
    COLOR_INPUT_BG, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, COLOR_TEXTO_TERCIARIO,
    COLOR_ACENTO, COLOR_ACENTO_HOVER, COLOR_ACENTO_PRESSED,
    COLOR_HEADER_SEMANA,
    RADIO_INPUT, RADIO_BOTON,
)


# ============================================================
# TOGGLE SWITCH (estilo iOS)
# ============================================================
class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.isChecked():
            color_fondo = QColor(COLOR_ACENTO)
            color_bola = QColor("#ffffff")
        else:
            color_fondo = QColor("#2a3b47")
            color_bola = QColor("#6c7a86")

        painter.setBrush(QBrush(color_fondo))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 11, 11)

        bola_x = self.width() - 19 if self.isChecked() else 3
        painter.setBrush(QBrush(color_bola))
        painter.drawEllipse(bola_x, 3, 16, 16)

        painter.end()


# ============================================================
# TAB BUTTON
# ============================================================
class TabButton(QPushButton):
    def __init__(self, texto, parent=None):
        super().__init__(texto, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(34)
        self.setFocusPolicy(Qt.NoFocus)
        self._actualizar_estilo()

    def setChecked(self, checked):
        super().setChecked(checked)
        self._actualizar_estilo()

    def _actualizar_estilo(self):
        if self.isChecked():
            color = COLOR_ACENTO
            borde = f"border-bottom: 2px solid {color};"
        else:
            color = COLOR_TEXTO_SECUNDARIO
            borde = "border-bottom: 2px solid transparent;"

        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                border: none;
                {borde}
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 600;
                text-align: center;
            }}
            QPushButton:hover {{
                color: {COLOR_TEXTO};
            }}
        """)


# ============================================================
# FILA DE AJUSTE
# ============================================================
class FilaAjuste(QWidget):
    def __init__(self, etiqueta, control, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(12)

        self.label = QLabel(etiqueta)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"color: {COLOR_TEXTO}; font-size: 12px; "
            "background: transparent; border: none;"
        )
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.label, 1)

        layout.addWidget(control, 0, Qt.AlignVCenter)


# ============================================================
# DIÁLOGO DE PREFERENCIAS
# ============================================================
class DialogoPreferencias(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencias")
        self.setModal(True)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Tamaño estándar fijo. Si el contenido es más alto,
        # el QScrollArea interno muestra la barra de scroll.
        self.setFixedSize(440, 620)

        self._tab_buttons = []
        self._stack = None

        self._armar_ui()

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            p_geo = self.parent().geometry()
            self.move(
                p_geo.center().x() - self.width() // 2,
                p_geo.center().y() - self.height() // 2,
            )

    # ============================================================
    def _armar_ui(self):
        from app.ui.custom_title_bar import CustomTitleBar

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar(
            self,
            "Preferencias",
            mostrar_maximizar=False,
            mostrar_minimizar=False,
        )
        root.addWidget(self.title_bar)

        contenido = QWidget()
        contenido.setObjectName("contenidoPrefs")
        contenido.setAttribute(Qt.WA_StyledBackground, True)
        contenido.setStyleSheet(
            f"QWidget#contenidoPrefs {{ background-color: {COLOR_FONDO}; }}"
        )
        contenido_layout = QVBoxLayout(contenido)
        contenido_layout.setContentsMargins(0, 0, 0, 0)
        contenido_layout.setSpacing(0)

        tabs_widget = self._crear_tabs()
        contenido_layout.addWidget(tabs_widget)

        divisor = QFrame()
        divisor.setFixedHeight(1)
        divisor.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        contenido_layout.addWidget(divisor)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(
            f"QStackedWidget {{ background-color: {COLOR_FONDO}; border: none; }}"
        )
        es_admin = getattr(self.parent(), "es_admin", False)
        self.tab_control = PanelControlTiempo(es_admin=es_admin)
        self._stack.addWidget(self._tab_general())
        self._stack.addWidget(self.tab_control)
        self._stack.addWidget(self._tab_rastreador_auto())
        self._stack.addWidget(self._tab_cuenta())

        contenido_layout.addWidget(self._stack, 1)

        root.addWidget(contenido)

    # ============================================================
    def _crear_tabs(self):
        w = QWidget()
        w.setFixedHeight(40)
        w.setStyleSheet(
            f"background-color: {COLOR_HEADER_SEMANA}; border: none;"
        )

        layout = QHBoxLayout(w)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(2)

        grupo = QButtonGroup(self)
        grupo.setExclusive(True)

        titulos = [
            "General",
            "Control de tiempo",
            "Rastreador automático",
            "Cuenta",
        ]

        for i, titulo in enumerate(titulos):
            btn = TabButton(titulo)
            btn.clicked.connect(lambda _, idx=i: self._cambiar_tab(idx))
            grupo.addButton(btn, i)
            self._tab_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        self._tab_buttons[0].setChecked(True)

        return w

    def _cambiar_tab(self, idx):
        self._stack.setCurrentIndex(idx)

        for i, btn in enumerate(self._tab_buttons):
            btn.setChecked(i == idx)
            btn._actualizar_estilo()

        # Ya NO se redimensiona ni se recentra la ventana.
        # El scroll interno de cada pestaña se encarga del resto.

    # ============================================================
    # TAB 1 — GENERAL
    # ============================================================
    def _tab_general(self):
        contenido = QWidget()
        contenido.setStyleSheet(
            f"background-color: {COLOR_FONDO}; border: none;"
        )
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(0)

        # ---- Título ----
        layout.addWidget(self._titulo_grande("Configuración general"))
        layout.addSpacing(12)

        # ---- Configuración ----
        layout.addWidget(self._subtitulo("Configuración"))
        layout.addSpacing(4)

        layout.addWidget(FilaAjuste(
            "Mantener la aplicación siempre visible",
            ToggleSwitch(),
        ))

        # 🆕 Auto-inicio: el registro de Windows es la fuente de verdad
        self.toggle_autostart = ToggleSwitch()
        self.toggle_autostart.setChecked(autostart.esta_habilitado())
        self.toggle_autostart.toggled.connect(self._on_autostart_cambiado)
        layout.addWidget(FilaAjuste(
            "Abrir la aplicación al encender la computadora",
            self.toggle_autostart,
        ))

        # 🆕 Mostrar la app al arrancar con Windows
        self.toggle_mostrar = ToggleSwitch()
        self.toggle_mostrar.setChecked(PS.get_bool(PS.KEY_MOSTRAR_AL_INICIAR, True))
        self.toggle_mostrar.toggled.connect(self._on_mostrar_al_iniciar_cambiado)
        layout.addWidget(FilaAjuste(
            "Mostrar la ventana automáticamente",
            self.toggle_mostrar,
        ))

        layout.addWidget(FilaAjuste(
            "Forzar sin conexión",
            ToggleSwitch(),
        ))

        layout.addSpacing(12)
        layout.addWidget(self._divisor())
        layout.addSpacing(10)

        # ---- Actualizaciones ----
        layout.addWidget(self._subtitulo("Actualizaciones"))
        layout.addSpacing(2)
        layout.addWidget(self._descripcion("Versión de la aplicación 2.3.1"))

        layout.addSpacing(12)
        layout.addWidget(self._divisor())
        layout.addSpacing(10)

        # ---- Tema ----
        layout.addWidget(self._subtitulo("Tema"))
        layout.addSpacing(4)
        layout.addWidget(self._crear_combo([
            "Tema oscuro", "Tema claro", "Auto (sistema)"
        ]))

        layout.addSpacing(12)
        layout.addWidget(self._divisor())
        layout.addSpacing(10)

        # ---- Idioma ----
        layout.addWidget(self._subtitulo("Idioma"))
        layout.addSpacing(4)
        layout.addWidget(self._crear_combo(["Español", "English", "Português"]))

        layout.addSpacing(8)
        layout.addStretch()

        return self._con_scroll(contenido)

    # ============================================================
    # TAB 2 — CONTROL DE TIEMPO
    # ============================================================
    def _tab_control_tiempo(self):
        contenido = QWidget()
        contenido.setStyleSheet(
            f"background-color: {COLOR_FONDO}; border: none;"
        )
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(0)

        layout.addWidget(self._titulo_grande("Control de tiempo"))
        layout.addSpacing(12)

        layout.addWidget(self._subtitulo("Comportamiento del temporizador"))
        layout.addSpacing(4)
        layout.addWidget(FilaAjuste(
            "Iniciar un nuevo temporizador al detener el actual",
            ToggleSwitch(),
        ))
        layout.addWidget(FilaAjuste(
            "Preguntar antes de detener el temporizador",
            ToggleSwitch(),
        ))
        layout.addWidget(FilaAjuste(
            "Redondear al minuto más cercano",
            ToggleSwitch(),
        ))

        layout.addSpacing(12)
        layout.addWidget(self._divisor())
        layout.addSpacing(10)

        layout.addWidget(self._subtitulo("Recordatorios"))
        layout.addSpacing(4)
        layout.addWidget(FilaAjuste(
            "Recordarme si olvidé iniciar el temporizador",
            ToggleSwitch(),
        ))
        layout.addWidget(FilaAjuste(
            "Notificar cada hora que el temporizador está activo",
            ToggleSwitch(),
        ))

        layout.addSpacing(8)
        layout.addStretch()

        return self._con_scroll(contenido)

    # ============================================================
    # TAB 3 — RASTREADOR AUTOMÁTICO
    # ============================================================
    def _tab_rastreador_auto(self):
        contenido = QWidget()
        contenido.setStyleSheet(
            f"background-color: {COLOR_FONDO}; border: none;"
        )
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(0)

        layout.addWidget(self._titulo_grande("Rastreador automático"))
        layout.addSpacing(12)

        layout.addWidget(self._subtitulo("Actividad a rastrear"))
        layout.addSpacing(4)
        layout.addWidget(FilaAjuste(
            "Activar rastreador automático",
            ToggleSwitch(),
        ))
        layout.addWidget(FilaAjuste(
            "Rastrear solo aplicaciones específicas",
            ToggleSwitch(),
        ))
        layout.addWidget(FilaAjuste(
            "Ignorar inactividad menor a 5 minutos",
            ToggleSwitch(),
        ))

        layout.addSpacing(12)
        layout.addWidget(self._divisor())
        layout.addSpacing(10)

        layout.addWidget(self._subtitulo("Intervalo de captura"))
        layout.addSpacing(4)
        layout.addWidget(self._crear_combo([
            "Cada 30 segundos", "Cada 1 minuto", "Cada 5 minutos"
        ]))

        layout.addSpacing(8)
        layout.addStretch()

        return self._con_scroll(contenido)

    # ============================================================
    # TAB 4 — CUENTA
    # ============================================================
    def _tab_cuenta(self):
        contenido = QWidget()
        contenido.setStyleSheet(
            f"background-color: {COLOR_FONDO}; border: none;"
        )
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(0)

        layout.addWidget(self._titulo_grande("Cuenta"))
        layout.addSpacing(12)

        layout.addWidget(self._subtitulo("Datos personales"))
        layout.addSpacing(6)
        layout.addWidget(self._campo_texto("Nombre completo", "Frank corilla"))
        layout.addSpacing(6)
        layout.addWidget(self._campo_texto("Correo electrónico", "frankcorilla2015@gmail.com"))

        layout.addSpacing(12)
        layout.addWidget(self._divisor())
        layout.addSpacing(10)

        layout.addWidget(self._subtitulo("Seguridad"))
        layout.addSpacing(6)

        btn_password = QPushButton("Cambiar contraseña")
        btn_password.setCursor(Qt.PointingHandCursor)
        btn_password.setFixedHeight(32)
        btn_password.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_ACENTO};
                border: 1px solid {COLOR_ACENTO};
                border-radius: {RADIO_BOTON}px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(33, 150, 243, 0.12);
            }}
            QPushButton:pressed {{
                background-color: rgba(33, 150, 243, 0.25);
            }}
        """)
        layout.addWidget(btn_password, 0, Qt.AlignLeft)

        layout.addSpacing(8)
        layout.addStretch()

        return self._con_scroll(contenido)

    def _on_autostart_cambiado(self, activo: bool):
        ok = autostart.aplicar(activo)
        if not ok:
            self.toggle_autostart.blockSignals(True)
            self.toggle_autostart.setChecked(not activo)
            self.toggle_autostart.blockSignals(False)
            print("[Prefs] No se pudo cambiar el auto-inicio")

    def _on_mostrar_al_iniciar_cambiado(self, activo: bool):
        PS.set_bool(PS.KEY_MOSTRAR_AL_INICIAR, activo)

    # ============================================================
    # HELPERS
    # ============================================================
    def _titulo_grande(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXTO}; font-size: 18px; font-weight: 700; "
            "background: transparent; border: none;"
        )
        return lbl

    def _subtitulo(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXTO}; font-size: 13px; font-weight: 700; "
            "background: transparent; border: none;"
        )
        return lbl

    def _descripcion(self, texto):
        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px; "
            "background: transparent; border: none;"
        )
        return lbl

    def _divisor(self):
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background-color: {COLOR_BORDE}; border: none;")
        return d

    def _crear_combo(self, opciones):
        combo = QComboBox()
        combo.addItems(opciones)
        combo.setFixedHeight(34)
        combo.setMinimumWidth(160)
        combo.setCursor(Qt.PointingHandCursor)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                color: {COLOR_TEXTO};
                padding: 4px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{
                border: 1px solid {COLOR_ACENTO};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLOR_TEXTO_SECUNDARIO};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDE};
                color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO};
                selection-color: white;
                outline: none;
                padding: 4px;
            }}
        """)
        return combo

    def _crear_par_boton(self, texto_placeholder, texto_boton):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(texto_placeholder)
        lbl.setFixedHeight(30)
        lbl.setMinimumWidth(140)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_INPUT_BG};
                color: {COLOR_TEXTO_TERCIARIO};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                padding: 0 10px;
                font-size: 11px;
            }}
        """)
        layout.addWidget(lbl)

        btn = QPushButton(texto_boton)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(30)
        btn.setMinimumWidth(80)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLOR_INPUT_BG};
                border: 1px solid {COLOR_ACENTO};
            }}
            QPushButton:pressed {{
                background-color: rgba(33, 150, 243, 0.15);
            }}
        """)
        layout.addWidget(btn)

        return w

    def _campo_texto(self, etiqueta, valor):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        lbl = QLabel(etiqueta)
        lbl.setStyleSheet(
            f"color: {COLOR_TEXTO_SECUNDARIO}; font-size: 11px; "
            "background: transparent; border: none;"
        )
        layout.addWidget(lbl)

        campo = QLabel(valor)
        campo.setFixedHeight(34)
        campo.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_INPUT_BG};
                color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE_INPUT};
                border-radius: {RADIO_INPUT}px;
                padding: 0 10px;
                font-size: 12px;
            }}
        """)
        layout.addWidget(campo)

        return w

    def _con_scroll(self, contenido_widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLOR_FONDO};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {COLOR_FONDO};
            }}
            QScrollBar:vertical {{
                background: {COLOR_FONDO};
                width: 10px;
                margin: 0;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #2a3a45;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #3a4a55;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        scroll.setWidget(contenido_widget)
        return scroll