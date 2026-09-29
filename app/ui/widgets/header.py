# app/ui/widgets/header.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QMenu,
    QSizePolicy, QWidgetAction,
)

from app.styles import tracker as S


NOMBRE_ORGANIZACION = "GM INGENIEROS Y CONSULTORES"
TITULO_SISTEMA = "Sistema de Control de Asistencia"

COLOR_ORG = "#8ea0af"      # gris azulado, sobrio
COLOR_TITULO = "#ffffff"
COLOR_LINEA = "#2196f3"    # acento discreto

VERSION_APP = "2.3.1"


class HeaderWidget(QWidget):
    cerrar_sesion = Signal()
    abrir_preferencias = Signal()   # 🆕 para comunicar al TrackerWindow

    def __init__(self, nombre_usuario: str, parent=None, email: str = ""):
        super().__init__(parent)
        self.nombre_usuario = nombre_usuario
        self.email_usuario = email or f"{nombre_usuario.lower().replace(' ', '.')}@gmail.com"

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(52)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ============================================================
        # MARCA INSTITUCIONAL
        # ============================================================
        self.contenedor_titulo = QFrame()
        self.contenedor_titulo.setObjectName("contenedorTitulo")
        self.contenedor_titulo.setStyleSheet(
            "QFrame#contenedorTitulo { background: transparent; border: none; }"
        )
        lay_titulo = QVBoxLayout(self.contenedor_titulo)
        lay_titulo.setContentsMargins(0, 0, 0, 0)
        lay_titulo.setSpacing(2)

        # Nombre de la organización
        label_org = QLabel(NOMBRE_ORGANIZACION)
        fuente_org = QFont("Segoe UI", 8, QFont.DemiBold)
        fuente_org.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        label_org.setFont(fuente_org)
        label_org.setStyleSheet(
            f"color: {COLOR_ORG}; background: transparent; border: none; padding: 0; margin: 0;"
        )

        # Línea fina de separación
        linea = QFrame()
        linea.setFixedHeight(2)
        linea.setFixedWidth(40)
        linea.setStyleSheet(f"background: {COLOR_LINEA}; border: none;")

        # Título del sistema
        label_titulo = QLabel(TITULO_SISTEMA)
        fuente_titulo = QFont("Segoe UI", 12, QFont.DemiBold)
        fuente_titulo.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        label_titulo.setFont(fuente_titulo)
        label_titulo.setStyleSheet(
            f"color: {COLOR_TITULO}; background: transparent; border: none; padding: 0; margin: 0;"
        )

        lay_titulo.addWidget(label_org)
        lay_titulo.addWidget(linea)
        lay_titulo.addWidget(label_titulo)

        layout.addWidget(self.contenedor_titulo, alignment=Qt.AlignVCenter)
        layout.addStretch()

        # ============================================================
        # USUARIO + MENÚ (chip clicable con avatar)
        # ============================================================
        self.btn_usuario = QPushButton()
        self.btn_usuario.setObjectName("btnUsuario")
        self.btn_usuario.setCursor(Qt.PointingHandCursor)
        self.btn_usuario.setFixedHeight(32)
        self.btn_usuario.setToolTip("Opciones de cuenta")
        self.btn_usuario.setStyleSheet(f"""
            QPushButton#btnUsuario {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid #22323d;
                border-radius: 6px;
                outline: none;
            }}
            QPushButton#btnUsuario:hover {{
                background: rgba(33, 150, 243, 0.12);
                border-color: {COLOR_LINEA};
            }}
            QPushButton#btnUsuario:pressed {{
                background: rgba(33, 150, 243, 0.20);
            }}
        """)

        lay_u = QHBoxLayout(self.btn_usuario)
        lay_u.setContentsMargins(5, 0, 8, 0)
        lay_u.setSpacing(6)

        # Avatar con la inicial
        inicial = (nombre_usuario.strip()[:1] or "?").upper()
        avatar = QLabel(inicial)
        avatar.setFixedSize(22, 22)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {COLOR_LINEA};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            padding: 0; margin: 0;
        """)

        # Nombre recortado
        fuente_nombre = QFont("Segoe UI", 9, QFont.DemiBold)
        fm = QFontMetrics(fuente_nombre)
        texto_nombre = fm.elidedText(nombre_usuario, Qt.ElideRight, 110)
        label_nombre = QLabel(texto_nombre)
        label_nombre.setFont(fuente_nombre)
        label_nombre.setStyleSheet(
            "color: #e6edf3; background: transparent; border: none; padding: 0; margin: 0;"
        )

        flecha = QLabel("▾")
        flecha.setStyleSheet(
            f"color: {COLOR_ORG}; background: transparent; border: none; "
            "font-size: 10px; padding: 0; margin: 0;"
        )

        for w in (avatar, label_nombre, flecha):
            w.setAttribute(Qt.WA_TransparentForMouseEvents)
            lay_u.addWidget(w, alignment=Qt.AlignVCenter)

        ancho = 5 + 22 + 6 + fm.horizontalAdvance(texto_nombre) + 6 + 10 + 8 + 4
        self.btn_usuario.setFixedWidth(ancho)

        self.btn_usuario.clicked.connect(self._abrir_menu)
        layout.addWidget(self.btn_usuario, alignment=Qt.AlignVCenter)

    # ============================================================
    # ABRIR MENÚ
    # ============================================================
    def _abrir_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #16232c;
                border: 1px solid #22323d;
                color: #ffffff;
                padding: 6px;
                border-radius: 8px;
                min-width: 240px;
            }
            QMenu::item {
                padding: 9px 22px 9px 40px;
                font-size: 12px;
                border-radius: 6px;
                margin: 1px 2px;
            }
            QMenu::item:selected {
                background-color: rgba(33, 150, 243, 0.18);
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #8ea0af;
                font-size: 11px;
            }
            QMenu::separator {
                height: 1px;
                background: #22323d;
                margin: 6px 12px;
            }
            QMenu::icon {
                padding-left: 14px;
            }
        """)

        # ---- Cabecera: avatar grande + nombre + email ----
        header_widget = self._crear_header_menu()
        wa_header = QWidgetAction(menu)
        wa_header.setDefaultWidget(header_widget)
        menu.addAction(wa_header)
        menu.addSeparator()

        # ---- Workspace ----
        acc_ws = QAction("  🏢   SistemasGM", self)
        acc_ws.triggered.connect(lambda: print("[Menú] Workspace"))
        menu.addAction(acc_ws)

        menu.addSeparator()

        # ---- Opciones rápidas ----
        acc_actualizar = QAction("  🔄   Actualizar", self)
        acc_actualizar.triggered.connect(self._on_actualizar)
        menu.addAction(acc_actualizar)

        acc_mini = QAction("  ⛶   Usar mini temporizador", self)
        acc_mini.triggered.connect(lambda: print("[Menú] Mini temporizador"))
        menu.addAction(acc_mini)

        acc_auto = QAction("  ⏱   Rastreador automático", self)
        acc_auto.triggered.connect(lambda: print("[Menú] Rastreador automático"))
        menu.addAction(acc_auto)

        acc_pref = QAction("  ⚙   Preferencias", self)
        acc_pref.triggered.connect(self._abrir_preferencias)
        menu.addAction(acc_pref)

        menu.addSeparator()

        # ---- Informes y ayuda ----
        acc_info = QAction("  📊   Informes", self)
        acc_info.triggered.connect(lambda: print("[Menú] Informes"))
        menu.addAction(acc_info)

        acc_ayuda = QAction("  ❓   Ayuda de GM", self)
        acc_ayuda.triggered.connect(lambda: print("[Menú] Ayuda"))
        menu.addAction(acc_ayuda)

        menu.addSeparator()

        # ---- Versión + feedback ----
        acc_version = QAction(f"  ℹ   Versión de aplicación          {VERSION_APP}", self)
        acc_version.setEnabled(False)
        menu.addAction(acc_version)

        acc_feedback = QAction("  💬   Compartir feedback", self)
        acc_feedback.triggered.connect(lambda: print("[Menú] Feedback"))
        menu.addAction(acc_feedback)

        # ---- Cerrar sesión ----
        acc_cerrar = QAction("  →   Cerrar sesión", self)
        acc_cerrar.triggered.connect(self.cerrar_sesion.emit)
        menu.addAction(acc_cerrar)

        menu.addSeparator()

        # ---- Salir ----
        acc_salir = QAction("  ✕   Salir", self)
        acc_salir.triggered.connect(self._salir_app)
        menu.addAction(acc_salir)

        # Posicionar el menú alineado a la derecha
        ancho_menu = menu.sizeHint().width()
        pos = self.btn_usuario.mapToGlobal(self.btn_usuario.rect().bottomRight())
        pos.setX(pos.x() - ancho_menu)
        pos.setY(pos.y() + 6)
        menu.exec(pos)

    # ============================================================
    # HEADER DEL MENÚ (avatar grande + nombre + email)
    # ============================================================
    def _crear_header_menu(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(64)
        w.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(w)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        # Avatar grande
        inicial = (self.nombre_usuario.strip()[:1] or "?").upper()
        avatar = QLabel(inicial)
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(33, 150, 243, 0.20);
                color: {COLOR_LINEA};
                border: 1px solid rgba(33, 150, 243, 0.40);
                border-radius: 20px;
                font-size: 17px;
                font-weight: 700;
            }}
        """)
        layout.addWidget(avatar)

        # Nombre + email
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(2)

        lbl_nombre = QLabel(self.nombre_usuario or "Usuario")
        lbl_nombre.setStyleSheet(
            "color: #ffffff; font-size: 13px; font-weight: 700; "
            "background: transparent; border: none;"
        )
        col.addWidget(lbl_nombre)

        lbl_email = QLabel(self.email_usuario)
        lbl_email.setStyleSheet(
            "color: #8ea0af; font-size: 11px; "
            "background: transparent; border: none;"
        )
        col.addWidget(lbl_email)

        layout.addLayout(col)
        layout.addStretch()

        return w

    # ============================================================
    # ACCIONES DEL MENÚ
    # ============================================================
    def _abrir_preferencias(self):
        """Abre el diálogo de preferencias."""
        from app.ui.dialogs.preferencias import DialogoPreferencias
        dlg = DialogoPreferencias(self.window())
        dlg.exec()

    def _on_actualizar(self):
        """Recarga los datos del tracker (historial, proyectos, etc.)."""
        # Buscamos la TrackerWindow padre y llamamos a su método
        ventana = self.window()
        if hasattr(ventana, "_cargar_historial"):
            ventana._cargar_historial()
        if hasattr(ventana, "_refrescar_cache"):
            ventana._refrescar_cache()

    # ============================================================
    # SALIR DE LA APP
    # ============================================================
    def _salir_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()