from PySide6.QtCore import QThread, Signal

from app.services.api_client import ApiError


def formatear_duracion(segundos: int) -> str:
    segundos = max(0, int(segundos))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class ApiWorker(QThread):
    """Worker genérico para no bloquear la UI con llamadas HTTP."""
    exito = Signal(object)
    error = Signal(str)

    def __init__(self, funcion, *args, **kwargs):
        super().__init__()
        self.funcion = funcion
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            resultado = self.funcion(*self.args, **self.kwargs)
            self.exito.emit(resultado)
        except ApiError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Error inesperado: {e}")
