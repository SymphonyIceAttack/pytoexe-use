import os
import shutil
import tempfile
import ctypes
import time
import random
import shutil as sh
import msvcrt

# ====== COLOR ROJO ======
kernel32 = ctypes.windll.kernel32
handle = kernel32.GetStdHandle(-11)
kernel32.SetConsoleTextAttribute(handle, 12)

# ====== ADMIN CHECK ======
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.user32.MessageBoxW(0, "Ejecuta ZombieYmdz Clener como ADMINISTRADOR", "ZombieYmdz Clener", 0)
    exit()

# ====== LIMPIAR CONSOLA ======
os.system("cls")

# ====== DECORACIÓN ESQUINA ======
cols = sh.get_terminal_size().columns
decoracion = "YVMPO MODZ"
print(" " * (cols - len(decoracion) - 1) + decoracion)

# ====== TEXTO GLITCH ======
def glitch_text(text, intensity=0.35):
    glitch_chars = "!@#$%^&*()_+=-<>?/\\|[]{}ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(
        c if random.random() > intensity else random.choice(glitch_chars)
        for c in text
    )

# ====== LOGO ======
logo = [
"███████╗ ██████╗ ███╗   ███╗██████╗ ██╗███████╗",
"╚══███╔╝██╔═══██╗████╗ ████║██╔══██╗██║╚══███╔╝",
"  ███╔╝ ██║   ██║██╔████╔██║██████╔╝██║  ███╔╝ ",
" ███╔╝  ██║   ██║██║╚██╔╝██║██╔══██╗██║ ███╔╝  ",
"███████╗╚██████╔╝██║ ╚═╝ ██║██████╔╝██║███████╗",
"╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚═╝╚══════╝",
"",
"        ZOMBIEYMDZ  -  CLENER"
]

# ====== ANIMACIÓN GLITCH LOGO ======
def glitch_logo(frames=25, delay=0.05):
    for _ in range(frames):
        os.system("cls")
        print(" " * (cols - len(decoracion) - 1) + decoracion)
        for line in logo:
            print(glitch_text(line))
        time.sleep(delay)

glitch_logo()
os.system("cls")
print(" " * (cols - len(decoracion) - 1) + decoracion)
for line in logo:
    print(line)

# ====== FUNCIONES DE LIMPIEZA ======
def clean_path(path):
    if os.path.exists(path):
        for item in os.listdir(path):
            full = os.path.join(path, item)
            try:
                if os.path.isdir(full):
                    shutil.rmtree(full, ignore_errors=True)
                else:
                    os.remove(full)
            except:
                pass

# ====== RUTAS A LIMPIAR ======
paths = [
    tempfile.gettempdir(),
    os.path.expandvars(r"%LOCALAPPDATA%\Temp"),
    r"C:\Windows\Temp",
    r"C:\Windows\Logs",
    r"C:\Windows\Prefetch",
    os.path.expandvars(r"%LOCALAPPDATA%\FiveM\FiveM.app\data\cache"),
    os.path.expandvars(r"%LOCALAPPDATA%\Rockstar Games\Launcher\logs"),
    os.path.expandvars(r"%LOCALAPPDATA%\Rockstar Games\Launcher\Browser"),
    os.path.expandvars(r"%LOCALAPPDATA%\Rockstar Games\Launcher\Settings"),
    os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA\DXCache"),
    os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA\GLCache"),
    os.path.expandvars(r"%LOCALAPPDATA%\D3DSCache"),
    r"C:\ProgramData\Microsoft\Windows\WER"
]

# ====== ANIMACIÓN “TRABAJANDO” ======
def trabajando_animacion(duracion=6):
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duracion
    i = 0
    while time.time() < end_time:
        while msvcrt.kbhit():  # Ignorar cualquier tecla
            msvcrt.getch()
        print(f"\r🧟‍♂️ ZombieYmdz está haciendo su trabajo... {frames[i % len(frames)]}", end="", flush=True)
        time.sleep(0.15)
        i += 1
    print("\r🧟‍♂️ ZombieYmdz está haciendo su trabajo... ✔")

# ====== LIMPIEZA AUTOMÁTICA ======
for p in paths:
    clean_path(p)

trabajando_animacion()

print("\n[✔] LIMPIEZA COMPLETA")
print("[✔] ZombieYmdz Clener finalizó correctamente")
time.sleep(3)