import sys

from PySide6.QtWidgets import QApplication

from app.services.api_client import ApiClient
from app.ui.login_window import LoginWindow
from app.ui.tracker_window import TrackerWindow


def main():
    app = QApplication(sys.argv)
    client = ApiClient()

    ventanas = {}

    def abrir_tracker(usuario: dict):
        login_win.close()
        tracker_win = TrackerWindow(client, usuario)
        ventanas["tracker"] = tracker_win
        tracker_win.show()

    login_win = LoginWindow(client)
    login_win.login_exitoso.connect(abrir_tracker)
    login_win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
