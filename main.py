# main.py
import sys
import os
import signal
import atexit

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtCore import Qt, QTimer

from app.services.api_client import ApiClient
from app.ui.login_window import LoginWindow
from app.ui.tracker_window import TrackerWindow
from app.utils import preferencias_store as PS


# ------------------------------------------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ------------------------------------------------------------------
def centrar_en_pantalla(ventana):
    """Centra la ventana en la pantalla actual. SEGURO (solo Qt)."""
    try:
        if ventana is None:
            return
        pantalla = QApplication.screenAt(QCursor.pos())
        if pantalla is None:
            pantalla = QApplication.primaryScreen()
        if pantalla is None:
            return
        geo = pantalla.availableGeometry()
        ventana.move(
            geo.center().x() - ventana.width() // 2,
            geo.center().y() - ventana.height() // 2,
        )
    except Exception as e:
        print(f"[Centrar] Error: {e}")


def traer_al_frente(ventana):
    """Restaura y trae una ventana al frente aunque esté oculta o minimizada."""
    if ventana is None:
        return
    ventana.setWindowState(ventana.windowState() & ~Qt.WindowMinimized)
    ventana.showNormal()
    ventana.raise_()
    ventana.activateWindow()
    QApplication.alert(ventana, 0)  # parpadea en la barra si Windows no da foco


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("app/assets/favicon.png")))

    # Cerrar la ventana NO termina la app: sigue en la bandeja
    app.setQuitOnLastWindowClosed(False)

    from app.utils.workers import detener_todos_los_threads
    app.aboutToQuit.connect(detener_todos_los_threads)
    atexit.register(detener_todos_los_threads)

    client = ApiClient()

    # Preferencias y modo de arranque
    lanzado_por_windows = "--autostart" in sys.argv
    mostrar_al_iniciar = PS.get_bool(PS.KEY_MOSTRAR_AL_INICIAR, True)
    hay_bandeja = QSystemTrayIcon.isSystemTrayAvailable()

    estado = {
        "login": None,
        "tracker": None,
        # arrancó Windows y el usuario pidió no ver la app
        "silencioso": lanzado_por_windows and not mostrar_al_iniciar,
        # True mientras se cambia de ventana (evita salir sin querer)
        "transicion": False,
    }

    # ------------------------------------------------------------
    # Bandeja del sistema
    # ------------------------------------------------------------
    def mostrar_app():
        traer_al_frente(estado["tracker"] or estado["login"])

    def salir_de_verdad():
        if estado["tracker"]:
            estado["tracker"]._cerrando_real = True
        tray.hide()
        QApplication.quit()

    tray = QSystemTrayIcon(QIcon(resource_path("app/assets/favicon.png")), app)
    tray.setToolTip("Control de Asistencia")

    menu = QMenu()
    menu.addAction("Abrir Control de Asistencia", mostrar_app)
    menu.addSeparator()
    menu.addAction("Salir", salir_de_verdad)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda motivo: mostrar_app()
        if motivo == QSystemTrayIcon.Trigger else None
    )
    if hay_bandeja:
        tray.show()
    app._tray = tray   # evitar que lo borre el recolector de basura
    app._menu = menu

    # Si el usuario cierra el login con la X (sin tracker abierto), salir
    def al_cerrar_ultima_ventana():
        if estado["tracker"] is None and not estado["transicion"]:
            QApplication.quit()

    app.lastWindowClosed.connect(al_cerrar_ultima_ventana)

    # ------------------------------------------------------------
    def abrir_tracker(usuario: dict):
        estado["transicion"] = True
        try:
            if estado["login"]:
                login = estado["login"]
                estado["login"] = None
                login.close()

            tracker = TrackerWindow(client, usuario)
            tracker.cerrar_sesion.connect(volver_al_login)
            estado["tracker"] = tracker

            # Solo el primer arranque de Windows respeta "no mostrar"
            if estado["silencioso"]:
                estado["silencioso"] = False
                if hay_bandeja:
                    tracker.hide()          # solo en la bandeja, heartbeat activo
                else:
                    tracker.showMinimized()
            else:
                centrar_en_pantalla(tracker)
                tracker.show()
                tracker.raise_()
                tracker.activateWindow()
        finally:
            estado["transicion"] = False

    # ------------------------------------------------------------
    def volver_al_login():
        estado["silencioso"] = False   # tras cerrar sesión, siempre visible
        estado["transicion"] = True
        try:
            if estado["tracker"]:
                tracker = estado["tracker"]
                tracker._cerrando_real = True   # cierre real, no ocultar
                estado["tracker"] = None
                tracker.close()

            client.logout()

            # Al cerrar sesión: olvidar contraseña y desactivar el auto-login
            try:
                from app.services.sesion import (
                    cargar_credenciales, guardar_credenciales,
                )
                email, _, _ = cargar_credenciales()
                guardar_credenciales(
                    email=email or "", password="", recordar=False
                )
            except Exception as e:
                print(f"[Logout] No se pudo limpiar credenciales: {e}")

            login = LoginWindow(client)
            login.login_exitoso.connect(abrir_tracker)
            estado["login"] = login

            centrar_en_pantalla(login)
            login.show()
            login.raise_()
            login.activateWindow()
        finally:
            estado["transicion"] = False

    # ------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------
    login_inicial = LoginWindow(client)
    login_inicial.login_exitoso.connect(abrir_tracker)
    estado["login"] = login_inicial

    def mostrar_ventana_login():
        estado["silencioso"] = False
        centrar_en_pantalla(login_inicial)
        login_inicial.show()
        login_inicial.raise_()
        login_inicial.activateWindow()

    # Si el auto-login falla, hay que mostrar el formulario sí o sí
    login_inicial.auto_login_fallido.connect(mostrar_ventana_login)

    def mostrar_login_inicial():
        try:
            visible = mostrar_al_iniciar or not lanzado_por_windows

            # Mostrar el login (con "Ingresando...") salvo en arranque silencioso
            if visible:
                mostrar_ventana_login()

            hay_credenciales = login_inicial.auto_login_si_hay_credenciales()

            # Sin credenciales y arranque silencioso: dejar el login minimizado
            if not hay_credenciales and not visible:
                login_inicial.showMinimized()
        except Exception as e:
            print(f"[Login inicial] Error: {e}")
            login_inicial.show()

    QTimer.singleShot(150, mostrar_login_inicial)

    # ------------------------------------------------------------
    # Ctrl+C handler
    # ------------------------------------------------------------
    def manejador_sigint(sig, frame):
        print("\n[App] Cerrando limpiamente...")
        detener_todos_los_threads()
        QApplication.quit()

    signal.signal(signal.SIGINT, manejador_sigint)

    # Timer para procesar señales en Windows (guardado en app para no ser GC)
    app._signal_timer = QTimer()
    app._signal_timer.timeout.connect(lambda: None)
    app._signal_timer.start(200)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()