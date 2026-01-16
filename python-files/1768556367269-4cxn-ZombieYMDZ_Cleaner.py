import os
import shutil
import tempfile
import ctypes
import time
import shutil as sh
import msvcrt
import subprocess
import threading

# ====== COLOR VERDE ======
kernel32 = ctypes.windll.kernel32
handle = kernel32.GetStdHandle(-11)
kernel32.SetConsoleTextAttribute(handle, 10)

# ====== ADMIN CHECK ======
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.user32.MessageBoxW(0, "Ejecuta ZombieYMDZ Cleaner como ADMINISTRADOR", "ZombieYMDZ Cleaner", 0)
    exit()

# ====== FUNCIONES DE LIMPIEZA ======
def clean_path(path):
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)
        except:
            pass

def unlink_accounts():
    procesos = ["FiveM.exe", "FiveM_b2189_GTAProcess.exe", "SocialClubHelper.exe", "Launcher.exe", "RockstarService.exe"]
    for proc in procesos:
        subprocess.run(f"taskkill /f /im {proc} >nul 2>&1", shell=True)
    
    rutas_desvincular = [
        os.path.expandvars(r"%AppData%\CitizenFX"),
        os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\cache\priv"),
        os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\cache\servers"),
        os.path.expandvars(r"%LocalAppData%\Rockstar Games"),
        os.path.join(os.path.expanduser("~"), "Documents", "Rockstar Games", "Social Club"),
        os.path.join(os.path.expanduser("~"), "Documents", "Rockstar Games", "Launcher")
    ]
    
    for r in rutas_desvincular:
        if os.path.exists(r):
            shutil.rmtree(r, ignore_errors=True)

# ====== BIENVENIDA ======
def bienvenida():
    os.system("cls")
    cols = sh.get_terminal_size().columns
    mensaje = "Bienvenidos a ZombieYMDZ"
    print("\n" * 5)
    print(mensaje.center(cols))
    time.sleep(3)
    
    # Flash rápido antes de entrar al Cleaner
    for _ in range(3):
        os.system("cls")
        time.sleep(0.1)
        print("\n" * 5)
        print(mensaje.center(cols))
        time.sleep(0.1)
    os.system("cls")

bienvenida()

# ====== LOGO Y ESTÉTICA ======
cols = sh.get_terminal_size().columns

# Logo ASCII original
logo_arriba = [
"███████╗ ██████╗ ███╗   ███╗██████╗ ██╗███████╗",
"╚══███╔╝██╔═══██╗████╗ ████║██╔══██╗██║╚══███╔╝",
"  ███╔╝ ██║   ██║██╔████╔██║██████╔╝██║  ███╔╝ ",
" ███╔╝  ██║   ██║██║╚██╔╝██║██╔══██╗██║ ███╔╝  ",
"███████╗╚██████╔╝██║ ╚═╝ ██║██████╔╝██║███████╗",
"╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═════╝ ╚═╝╚══════╝",
""
]

# Subtextos fijos
subtextos = [
"           CLEANER  &  LOCAL  UNLINKER",
"       Creador Discord / dimezombie",
"               OWNER †Ｚｏｍｂｉ† ",
"       https://discord.gg/2pmPXjCS4t",
""
]

# ====== FLASH Y MOVIMIENTO ======
def mostrar_logo_flashing_y_zombie_corriendo():
    os.system("cls")
    # Mostrar logo original arriba
    for line in logo_arriba:
        print(line.center(cols))
    
    # Flash continuo de YVMPO MODZ
    def flash_yvmpo():
        while True:
            print(" " * len("YVMPO MODZ").center(cols), end="\r")
            time.sleep(0.3)
            print("YVMPO MODZ".center(cols), end="\r")
            time.sleep(0.3)
    
    threading.Thread(target=flash_yvmpo, daemon=True).start()
    
    # Animación de ZOMBIEYMDZ grande corriendo
    def zombie_marquee():
        text = " ZOMBIEYMDZ "
        padding = " " * 50
        scroll_text = padding + text
        while True:
            print(scroll_text[:50].center(cols), end="\r")
            scroll_text = scroll_text[1:] + scroll_text[0]
            time.sleep(0.15)
    
    threading.Thread(target=zombie_marquee, daemon=True).start()
    
    # Mostrar subtextos fijos debajo
    for line in subtextos:
        print(line.center(cols))

def mostrar_logo():
    mostrar_logo_flashing_y_zombie_corriendo()

mostrar_logo()

# ====== MENÚ DE SELECCIÓN ======
print("\n[1] Limpieza de Temporales (PC Speed)")
print("[2] Desvincular FiveM de Rockstar (Unlink Account)")
print("[3] Limpieza Completa (Todo)")
print("="*45)
opcion = input("Selecciona una opción Zombie: ")

# ====== ANIMACIÓN DE PROCESO ======
def trabajando_animacion(duracion=4):
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duracion
    i = 0
    while time.time() < end_time:
        print(f"\rZombieYMDZ trabajando... {frames[i % len(frames)]}", end="", flush=True)
        time.sleep(0.15)
        i += 1
    print("\rProceso finalizado correctamente.   ")

# ====== RUTAS DE LIMPIEZA GENERAL ======
paths_general = [
    tempfile.gettempdir(),
    os.path.expandvars(r"%LOCALAPPDATA%\Temp"),
    r"C:\Windows\Temp",
    r"C:\Windows\Prefetch",
    os.path.expandvars(r"%LOCALAPPDATA%\NVIDIA\DXCache"),
    os.path.expandvars(r"%LOCALAPPDATA%\D3DSCache")
]

# ====== EJECUCIÓN SEGÚN OPCIÓN ======
if opcion == "1":
    for p in paths_general:
        clean_path(p)
    trabajando_animacion()
elif opcion == "2":
    unlink_accounts()
    trabajando_animacion()
    print("\n[!] FiveM ha sido desvinculado. Debes loguear de nuevo.")
elif opcion == "3":
    for p in paths_general:
        clean_path(p)
    unlink_accounts()
    trabajando_animacion()

# ====== FINALIZAR CON TECLA ======
print("\nPROCESO COMPLETADO")
print("Presiona cualquier tecla para salir...")
msvcrt.getch()