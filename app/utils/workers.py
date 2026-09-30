# app/utils/workers.py
from PySide6.QtCore import QThread, Signal
import atexit


_threads_activos = []


def _registrar(thread):
    _threads_activos.append(thread)
    thread.finished.connect(lambda: _remover(thread))


def _remover(thread):
    try:
        _threads_activos.remove(thread)
    except ValueError:
        pass


def detener_todos_los_threads():
    for t in list(_threads_activos):
        try:
            if t.isRunning():
                t.quit()
                if not t.wait(1500):
                    t.terminate()
                    t.wait(500)
        except Exception:
            pass
    _threads_activos.clear()


atexit.register(detener_todos_los_threads)


def formatear_duracion(segundos: int) -> str:
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class ApiWorker(QThread):
    exito = Signal(object)
    error = Signal(str)

    def __init__(self, funcion, *args, **kwargs):
        super().__init__()
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs
        _registrar(self)

    def run(self):
        try:
            resultado = self.funcion(*self.args, **self.kwargs)
            self.exito.emit(resultado)
        except Exception as e:
            self.error.emit(str(e))