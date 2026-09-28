# main.py
import sys
import os
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.services.api_client import ApiClient
from app.ui.login_window import LoginWindow
from app.ui.tracker_window import TrackerWindow

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("app/assets/favicon.png")))
    client = ApiClient()
    estado = {"login": None, "tracker": None}

    def abrir_tracker(usuario: dict):
        if estado["login"]:
            estado["login"].close()
            estado["login"] = None
        tracker = TrackerWindow(client, usuario)
        tracker.cerrar_sesion.connect(volver_al_login)
        estado["tracker"] = tracker
        tracker.show()

    def volver_al_login():
        if estado["tracker"]:
            estado["tracker"].close()
            estado["tracker"] = None
        client.logout()
        login = LoginWindow(client)
        login.login_exitoso.connect(abrir_tracker)
        estado["login"] = login
        login.show()

    login_inicial = LoginWindow(client)
    login_inicial.login_exitoso.connect(abrir_tracker)
    estado["login"] = login_inicial
    login_inicial.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()