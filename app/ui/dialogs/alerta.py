# app/ui/dialogs/alerta.py
"""
Funciones reutilizables para mostrar alertas con tema oscuro.
"""

from PySide6.QtWidgets import QMessageBox, QWidget

from .estilos import (
    ESTILO_MESSAGEBOX,
    ESTILO_MESSAGEBOX_PELIGRO,
    COLOR_ERROR,
)


# ============================================================
# CONFIRMAR ELIMINAR
# ============================================================

def confirmar_eliminar(
    padre: QWidget = None,
    titulo: str = "Eliminar",
    mensaje: str = "¿Estás seguro de eliminar este elemento?",
    subtitulo: str = "Esta acción no se puede deshacer.",
    texto_confirmar: str = "Sí, eliminar",
    texto_cancelar: str = "Cancelar",
) -> bool:
    """
    Muestra un diálogo de confirmación para eliminar.
    Devuelve True si el usuario confirma, False si cancela.
    """

    dialogo = QMessageBox(padre)
    dialogo.setWindowTitle(titulo)
    dialogo.setText(mensaje)
    dialogo.setInformativeText(subtitulo)
    dialogo.setIcon(QMessageBox.Warning)

    boton_si = dialogo.addButton(texto_confirmar, QMessageBox.YesRole)
    boton_no = dialogo.addButton(texto_cancelar, QMessageBox.NoRole)

    dialogo.setDefaultButton(boton_no)

    dialogo.setStyleSheet(ESTILO_MESSAGEBOX_PELIGRO)

    dialogo.exec()

    return dialogo.clickedButton() == boton_si


# ============================================================
# ALERTA DE ERROR
# ============================================================

def alerta_error(
    padre: QWidget = None,
    titulo: str = "Error",
    mensaje: str = "Ha ocurrido un error.",
    subtitulo: str = "",
) -> None:
    """
    Muestra una alerta de error con botón OK.
    """

    dialogo = QMessageBox(padre)
    dialogo.setWindowTitle(titulo)
    dialogo.setText(mensaje)

    if subtitulo:
        dialogo.setInformativeText(subtitulo)

    dialogo.setIcon(QMessageBox.Critical)

    dialogo.addButton("OK", QMessageBox.AcceptRole)

    dialogo.setStyleSheet(ESTILO_MESSAGEBOX)

    dialogo.exec()


# ============================================================
# ALERTA DE ÉXITO
# ============================================================

def alerta_exito(
    padre: QWidget = None,
    titulo: str = "Éxito",
    mensaje: str = "Operación completada.",
    subtitulo: str = "",
) -> None:
    """
    Muestra una alerta de éxito con botón OK.
    """

    dialogo = QMessageBox(padre)
    dialogo.setWindowTitle(titulo)
    dialogo.setText(mensaje)

    if subtitulo:
        dialogo.setInformativeText(subtitulo)

    dialogo.setIcon(QMessageBox.Information)

    dialogo.addButton("OK", QMessageBox.AcceptRole)

    dialogo.setStyleSheet(ESTILO_MESSAGEBOX)

    dialogo.exec()


# ============================================================
# ALERTA INFORMATIVA
# ============================================================

def alerta_info(
    padre: QWidget = None,
    titulo: str = "Información",
    mensaje: str = "",
    subtitulo: str = "",
) -> None:
    """
    Muestra una alerta informativa con botón OK.
    """

    dialogo = QMessageBox(padre)
    dialogo.setWindowTitle(titulo)
    dialogo.setText(mensaje)

    if subtitulo:
        dialogo.setInformativeText(subtitulo)

    dialogo.setIcon(QMessageBox.Information)

    dialogo.addButton("OK", QMessageBox.AcceptRole)

    dialogo.setStyleSheet(ESTILO_MESSAGEBOX)

    dialogo.exec()