# app/services/inactividad.py
"""
Monitor de inactividad del usuario.
Detecta cuando no hay movimiento de mouse ni pulsaciones de teclado.
"""

import time

from PySide6.QtCore import QObject, Signal, QTimer

from pynput import mouse, keyboard


class MonitorInactividad(QObject):
    """
    Monitor que detecta inactividad del usuario.

    Señales:
        - inactividad_detectada(segundos): Al superar el umbral (abre modal).
        - actividad_reanudada(segundos_inactivo): Cuando el usuario vuelve
          a interactuar después de la alerta.
    """

    inactividad_detectada = Signal(int)
    actividad_reanudada = Signal(int)

    def __init__(self, umbral_segundos=300, padre=None):
        super().__init__(padre)

        self.umbral = umbral_segundos
        self.ultima_actividad = time.time()
        self.en_alerta = False
        self.activo = False

        # Listeners globales
        self._listener_mouse = None
        self._listener_teclado = None

        # Timer para revisar cada segundo
        self._timer_check = QTimer(self)
        self._timer_check.timeout.connect(self._revisar)
        self._timer_check.setInterval(1000)

    # ========================================================
    # INICIAR / DETENER
    # ========================================================

    def iniciar(self):
        """Empieza a monitorear."""
        if self.activo:
            return

        self.activo = True
        self.ultima_actividad = time.time()
        self.en_alerta = False

        self._listener_mouse = mouse.Listener(
            on_move=self._on_actividad,
            on_click=self._on_actividad,
            on_scroll=self._on_actividad,
        )
        self._listener_mouse.daemon = True
        self._listener_mouse.start()

        self._listener_teclado = keyboard.Listener(
            on_press=self._on_actividad,
        )
        self._listener_teclado.daemon = True
        self._listener_teclado.start()

        self._timer_check.start()

    def detener(self):
        """Detiene el monitoreo."""
        if not self.activo:
            return

        self.activo = False
        self.en_alerta = False

        if self._listener_mouse:
            self._listener_mouse.stop()
            self._listener_mouse = None

        if self._listener_teclado:
            self._listener_teclado.stop()
            self._listener_teclado = None

        self._timer_check.stop()

    # ========================================================
    # CALLBACKS
    # ========================================================

    def _on_actividad(self, *args, **kwargs):
        """
        Se dispara cuando el usuario interactúa (mouse o teclado).
        """
        ahora = time.time()

        # Si estábamos en alerta, el usuario volvió.
        # Emitimos la señal con el tiempo total inactivo.
        if self.en_alerta:
            # Tiempo desde la última actividad REAL hasta ahora
            segundos_inactivo = int(ahora - self.ultima_actividad)

            self.en_alerta = False
            self.actividad_reanudada.emit(segundos_inactivo)

        #  Importante: actualizar al final
        self.ultima_actividad = ahora

    def _revisar(self):
        """Revisa cada segundo si hay inactividad."""
        if not self.activo:
            return

        inactivo_por = int(time.time() - self.ultima_actividad)

    #  DIAGNÓSTICO
        print(f"[MONITOR] inactivo_por={inactivo_por}s | umbral={self.umbral}s | en_alerta={self.en_alerta}")

        if inactivo_por >= self.umbral and not self.en_alerta:
            print(f"[MONITOR] ¡UMBRAL SUPERADO! Emitindo señal...")
            self.en_alerta = True
            self.inactividad_detectada.emit(inactivo_por) 
        


    # ========================================================
    # UTILIDADES
    # ========================================================

    def tiempo_inactivo_actual(self) -> int:
        """
        Devuelve los segundos que lleva inactivo en este momento.
        Útil para calcular el tiempo total cuando el usuario
        cierra el modal.
        """
        if not self.en_alerta:
            return 0
        return int(time.time() - self.ultima_actividad)

    def reiniciar(self):
        """Reinicia el contador de inactividad."""
        self.ultima_actividad = time.time()
        self.en_alerta = False