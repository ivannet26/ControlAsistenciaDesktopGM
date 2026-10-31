# main.py
import sys
import os
import signal
import atexit
import logging

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QCursor
from PySide6.QtCore import Qt, QTimer

from app.services.api_client import (
    ApiClient,
    ApiError,
    NetworkError,
    SessionExpired,
)
from app.services import cuentas_store, sesion
from app.ui.login_window import LoginWindow
from app.ui.selector_cuentas import SelectorCuentas
from app.ui.tracker_window import TrackerWindow
from app.utils import preferencias_store as PS
from app.utils.workers import ApiWorker

logger = logging.getLogger(__name__)


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


_AVISOS_ABIERTOS = []


def _aviso_no_bloqueante(titulo, mensaje):
    caja = QMessageBox(
        QMessageBox.Warning,
        titulo,
        mensaje,
        QMessageBox.Ok,
    )
    caja.setWindowModality(Qt.NonModal)
    caja.setAttribute(Qt.WA_DeleteOnClose)
    _AVISOS_ABIERTOS.append(caja)
    caja.finished.connect(
        lambda _=None: _AVISOS_ABIERTOS.remove(caja)
        if caja in _AVISOS_ABIERTOS
        else None
    )
    caja.show()


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("app/assets/favicon.png")))

    # Cerrar la ventana NO termina la app: sigue en la bandeja
    app.setQuitOnLastWindowClosed(False)

    from app.utils.workers import detener_todos_los_threads
    app.aboutToQuit.connect(detener_todos_los_threads)
    atexit.register(detener_todos_los_threads)

    client = ApiClient()

    try:
        sesion.limpiar_credenciales_huerfanas()
    except Exception:
        logger.exception("No se pudieron limpiar credenciales viejas")

    # Preferencias y modo de arranque
    lanzado_por_windows = "--autostart" in sys.argv
    mostrar_al_iniciar = PS.get_bool(PS.KEY_MOSTRAR_AL_INICIAR, True)
    hay_bandeja = QSystemTrayIcon.isSystemTrayAvailable()

    estado = {
        "login": None,
        "selector": None,
        "tracker": None,
        "cuenta_actual_email": None,
        "validacion_cuenta_en_curso": False,
        "worker_validacion_cuenta": None,
        # arrancó Windows y el usuario pidió no ver la app
        "silencioso": lanzado_por_windows and not mostrar_al_iniciar,
        # True mientras se cambia de ventana (evita salir sin querer)
        "transicion": False,
    }

    # ------------------------------------------------------------
    # Bandeja del sistema
    # ------------------------------------------------------------
    def mostrar_app():
        traer_al_frente(
            estado["tracker"] or estado["login"] or estado["selector"]
        )

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
        if (
            estado["tracker"] is None
            and estado["login"] is None
            and estado["selector"] is None
            and not estado["transicion"]
        ):
            QApplication.quit()

    app.lastWindowClosed.connect(al_cerrar_ultima_ventana)

    # ------------------------------------------------------------
    def eliminar_cuenta_guardada(cuenta: dict):
        email = (cuenta.get("email") or "").strip()
        if not email:
            return

        try:
            cuentas_store.eliminar_cuenta(email)
        except Exception as exc:
            logger.exception("No se pudo descartar la cuenta")
            _aviso_no_bloqueante(
                "No se pudo descartar",
                f"No se pudo borrar la cuenta guardada:\n{exc}",
            )
            return

        try:
            sesion.limpiar_credenciales_cuenta(email)
        except Exception:
            logger.exception(
                "No se pudieron limpiar las credenciales de la cuenta"
            )

        if (estado.get("cuenta_actual_email") or "").casefold() == email.casefold():
            estado["cuenta_actual_email"] = None

    def mostrar_selector():
        try:
            cuentas = cuentas_store.listar_cuentas()
        except Exception as exc:
            logger.exception("No se pudieron cargar las cuentas guardadas")
            QMessageBox.critical(
                None,
                "Error al cargar cuentas",
                f"No se pudieron leer las cuentas guardadas:\n{exc}",
            )
            cuentas = []

        if not cuentas:
            abrir_login()
            return

        selector = SelectorCuentas(cuentas, client)
        selector.cuenta_seleccionada.connect(abrir_cuenta)
        selector.cuenta_removida.connect(eliminar_cuenta_guardada)
        selector.agregar_cuenta.connect(abrir_login)
        selector.cerrado.connect(
            lambda selector=selector: al_cerrar_selector(selector)
        )
        estado["selector"] = selector
        centrar_en_pantalla(selector)
        selector.show()
        selector.raise_()
        selector.activateWindow()

    def al_cerrar_selector(selector):
        if estado["selector"] is selector:
            estado["selector"] = None

    def abrir_login(email: str | None = None):
        if estado["selector"] is not None:
            estado["selector"].hide()

        login = LoginWindow(client, email=email)
        estado["login"] = login
        login.login_exitoso.connect(abrir_tracker)
        login.cerrado.connect(lambda login=login: al_cerrar_login(login))
        centrar_en_pantalla(login)
        login.show()
        login.raise_()
        login.activateWindow()

    def al_cerrar_login(login):
        if estado["login"] is not login:
            return
        estado["login"] = None
        if estado["selector"] is not None and estado["tracker"] is None:
            estado["transicion"] = False
            estado["selector"].show()
            traer_al_frente(estado["selector"])

    def _preparar_cuenta():
        try:
            if client.refresh_token:
                client.refresh(forzar=True)
            return ("ok", client.obtener_temporizador_activo())
        except SessionExpired as exc:
            return ("sesion", str(exc))
        except NetworkError as exc:
            return ("red", str(exc))
        except ApiError as exc:
            if exc.status_code in (401, 403):
                return ("sesion", str(exc))
            return ("error", str(exc))
        except Exception as exc:
            return ("error", str(exc))

    def _resultado_validacion_cuenta(cuenta: dict, usuario: dict, resultado):
        tipo, valor = resultado
        estado["validacion_cuenta_en_curso"] = False
        estado["worker_validacion_cuenta"] = None

        if tipo == "ok":
            _cuenta_validada(usuario)
            return
        if tipo == "sesion":
            _error_validando_cuenta(cuenta, valor)
            return
        if tipo == "red":
            _aviso_no_bloqueante(
                "Sin conexión",
                "No se pudo conectar con el servidor. "
                "Revisa tu conexión e inténtalo de nuevo.",
            )
            return
        _aviso_no_bloqueante("Error", valor)

    def abrir_cuenta(cuenta: dict):
        if estado["validacion_cuenta_en_curso"]:
            return

        usuario = dict(cuenta.get("usuario") or {})
        usuario.update({
            clave: cuenta[clave]
            for clave in ("id", "nombre", "apellido", "email", "correo", "rol", "avatar_url")
            if clave in cuenta
        })
        client.cargar_tokens(cuenta["token"], cuenta.get("refresh_token"))
        client.usuario = usuario
        estado["cuenta_actual_email"] = cuenta.get("email")

        estado["validacion_cuenta_en_curso"] = True
        worker = ApiWorker(_preparar_cuenta)
        estado["worker_validacion_cuenta"] = worker
        worker.exito.connect(
            lambda resultado, cuenta=cuenta, usuario=usuario:
                _resultado_validacion_cuenta(cuenta, usuario, resultado)
        )
        worker.error.connect(
            lambda mensaje, cuenta=cuenta, usuario=usuario:
                _resultado_validacion_cuenta(
                    cuenta, usuario, ("error", mensaje)
                )
        )
        worker.start()

    def _cuenta_validada(usuario: dict):
        estado["validacion_cuenta_en_curso"] = False
        estado["worker_validacion_cuenta"] = None
        abrir_tracker(usuario)

    def _error_validando_cuenta(cuenta: dict, _mensaje: str):
        estado["validacion_cuenta_en_curso"] = False
        estado["worker_validacion_cuenta"] = None
        estado["transicion"] = True
        try:
            selector = estado["selector"]
            if selector is not None:
                estado["selector"] = None
                selector.close()

            client.logout()
            abrir_login(email=cuenta.get("email") or "")
        finally:
            estado["transicion"] = False

    def abrir_tracker(usuario: dict):
        estado["transicion"] = True
        try:
            usuario = dict(usuario or {})
            login_activo = estado["login"]
            if not usuario.get("email") and login_activo is not None:
                usuario["email"] = login_activo.email_input.text().strip()

            if client.token:
                try:
                    cuentas_store.guardar_cuenta(
                        usuario, client.token, client.refresh_token
                    )
                except Exception as exc:
                    logger.exception("No se pudo guardar la cuenta")
                    QMessageBox.warning(
                        None,
                        "Cuenta no guardada",
                        f"Se inició sesión, pero no se pudo guardar la cuenta:\n{exc}",
                    )
            estado["cuenta_actual_email"] = usuario.get("email")

            if estado["login"]:
                login = estado["login"]
                estado["login"] = None
                login.close()

            if estado["selector"] is not None:
                selector = estado["selector"]
                estado["selector"] = None
                selector.close()

            tracker = TrackerWindow(client, usuario)
            tracker.cerrar_sesion.connect(volver_al_login)
            estado["tracker"] = tracker

            # --- Recordatorios: enlazar con la bandeja ---
                        # --- Recordatorios: enlazar con la bandeja ---
            tracker.recordatorios.set_tray(tray)

            anterior = estado.get("handler_bandeja")
            if anterior is not None:
                try:
                    tray.messageClicked.disconnect(anterior)
                except (TypeError, RuntimeError):
                    pass

            estado["handler_bandeja"] = tracker._traer_al_frente
            tray.messageClicked.connect(estado["handler_bandeja"])
            # ----------------------------------------------
            # Quitar la conexión de un tracker anterior (tras cerrar sesión)
            try:
                tray.messageClicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            tray.messageClicked.connect(tracker._traer_al_frente)
            # ----------------------------------------------

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
            estado["cuenta_actual_email"] = None

            # Al cerrar sesión: dejar de recordar el correo.
            try:
                email, _ = sesion.cargar_credenciales()
                sesion.guardar_credenciales(
                    email=email or "", recordar=False
                )
            except Exception:
                logger.exception("No se pudieron limpiar las credenciales")

            mostrar_selector()
        finally:
            estado["transicion"] = False

    # ------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------
    try:
        cuentas_guardadas = cuentas_store.listar_cuentas()
    except Exception as exc:
        logger.exception("No se pudieron cargar las cuentas guardadas")
        QMessageBox.critical(
            None,
            "Error al cargar cuentas",
            f"No se pudieron leer las cuentas guardadas:\n{exc}",
        )
        cuentas_guardadas = []

    if cuentas_guardadas:
        if estado["silencioso"]:
            abrir_cuenta(cuentas_guardadas[-1])
        else:
            mostrar_selector()
    else:
        login_inicial = LoginWindow(client)
        estado["login"] = login_inicial
        login_inicial.login_exitoso.connect(abrir_tracker)

        def mostrar_ventana_login():
            estado["silencioso"] = False
            centrar_en_pantalla(login_inicial)
            login_inicial.show()
            login_inicial.raise_()
            login_inicial.activateWindow()

        login_inicial.cerrado.connect(
            lambda: al_cerrar_login(login_inicial)
        )

        def mostrar_login_inicial():
            try:
                visible = mostrar_al_iniciar or not lanzado_por_windows
                if visible:
                    mostrar_ventana_login()
                else:
                    login_inicial.showMinimized()
            except Exception:
                logger.exception("[Login inicial] Error")
                login_inicial.show()

        QTimer.singleShot(150, mostrar_login_inicial)

    # ------------------------------------------------------------
    # Ctrl+C handler
    # ------------------------------------------------------------
    def manejador_sigint(sig, frame):
        logger.info("Cerrando la aplicación")
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