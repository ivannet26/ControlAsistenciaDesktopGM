# main.py
import sys

from PySide6.QtWidgets import QApplication

from app.services.api_client import ApiClient
from app.ui.login_window import LoginWindow
from app.ui.tracker_window import TrackerWindow


def main():
    app = QApplication(sys.argv)
    client = ApiClient()

    estado = {
        "login": None,
        "tracker": None,
    }

    # ------------------------------------------------------------
    # Abrir tracker (desde login)
    # ------------------------------------------------------------
    def abrir_tracker(usuario: dict):
        if estado["login"]:
            estado["login"].close()
            estado["login"] = None

        tracker = TrackerWindow(client, usuario)
        tracker.cerrar_sesion.connect(volver_al_login)
        estado["tracker"] = tracker
        tracker.show()

    # ------------------------------------------------------------
    # Volver al login (desde tracker)
    # ------------------------------------------------------------
    def volver_al_login():
        # Cerrar tracker si existe
        if estado["tracker"]:
            estado["tracker"].close()
            estado["tracker"] = None

        # Limpiar sesión del cliente
        client.logout()

        # Abrir login
        login = LoginWindow(client)
        login.login_exitoso.connect(abrir_tracker)
        estado["login"] = login
        login.show()

    # ------------------------------------------------------------
    # Arranque: mostrar login
    # ------------------------------------------------------------
    login_inicial = LoginWindow(client)
    login_inicial.login_exitoso.connect(abrir_tracker)
    estado["login"] = login_inicial
    login_inicial.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()