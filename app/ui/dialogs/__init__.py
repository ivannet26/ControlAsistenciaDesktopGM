# app/ui/dialogs/__init__.py
"""Paquete de diálogos. Re-exporta la API pública."""

from .alerta import (
    confirmar_eliminar,
    alerta_error,
    alerta_exito,
    alerta_info,
)
from .modal_inactividad import ModalInactividad
from .modal_entrada import ModalEntrada
from .nueva_tarea import DialogoNuevaTarea
from .nueva_etiqueta import DialogoNuevaEtiqueta
from .registro import DialogoRegistro
__all__ = [
    "confirmar_eliminar",
    "alerta_error",
    "alerta_exito",
    "alerta_info",
    "ModalInactividad",
    "ModalEntrada",
    "DialogoNuevaTarea",
    "DialogoNuevaEtiqueta",
    "DialogoRegistro",
]