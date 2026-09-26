# app/ui/dialogs/__init__.py
"""
Módulo de diálogos personalizados con tema oscuro.
"""

from .alerta import (
    confirmar_eliminar,
    alerta_error,
    alerta_info,
    alerta_exito,
)

# Cuando crees el modal de entrada, descomenta:
# from .modal_entrada import ModalEntradaTiempo


__all__ = [
    "confirmar_eliminar",
    "alerta_error",
    "alerta_info",
    "alerta_exito",
    # "ModalEntradaTiempo",
]