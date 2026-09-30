# main.py
import sys
import os
import signal
import atexit

from PySide6.QtGui import QIcon, QCursor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

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


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("app/assets/favicon.png")))

    from app.utils.workers import detener_todos_los_threads
    app.aboutToQuit.connect(detener_todos_los_threads)
    atexit.register(detener_todos_los_threads)

    client = ApiClient()

    # 🆕 Preferencias y modo de arranque
    lanzado_por_windows = "--autostart" in sys.argv
    mostrar_al_iniciar = PS.get_bool(PS.KEY_MOSTRAR_AL_INICIAR, True)

    # 🆕 "silencioso" = arrancó Windows y el usuario pidió no ver la app
    estado = {
        "login": None,
        "tracker": None,
        "silencioso": lanzado_por_windows and not mostrar_al_iniciar,
    }

    # ------------------------------------------------------------
    def abrir_tracker(usuario: dict):
        if estado["login"]:
            estado["login"].close()
            estado["login"] = None

        tracker = TrackerWindow(client, usuario)
        tracker.cerrar_sesion.connect(volver_al_login)
        estado["tracker"] = tracker

        # 🆕 Solo el primer arranque de Windows respeta "no mostrar"
        if estado["silencioso"]:
            estado["silencioso"] = False
            tracker.showMinimized()
        else:
            centrar_en_pantalla(tracker)
            tracker.show()
            tracker.raise_()
            tracker.activateWindow()

    # ------------------------------------------------------------
    def volver_al_login():
        estado["silencioso"] = False   # 🆕 después de cerrar sesión, siempre visible

        if estado["tracker"]:
            estado["tracker"].close()
            estado["tracker"] = None

        client.logout()

        login = LoginWindow(client)
        login.login_exitoso.connect(abrir_tracker)
        estado["login"] = login

        centrar_en_pantalla(login)
        login.show()
        login.raise_()
        login.activateWindow()

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

    # 🆕 Si el auto-login falla, hay que mostrar el formulario sí o sí
    login_inicial.auto_login_fallido.connect(mostrar_ventana_login)

    def mostrar_login_inicial():
        try:
            # 🆕 Intentar auto-login primero (sin mostrar ventana)
            if login_inicial.auto_login_si_hay_credenciales():
                return  # _on_login_ok → login_exitoso → abrir_tracker

            # Sin credenciales guardadas: login normal
            if mostrar_al_iniciar or not lanzado_por_windows:
                mostrar_ventana_login()
            else:
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

    app._signal_timer = QTimer()
    app._signal_timer.timeout.connect(lambda: None)
    app._signal_timer.start(200)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()