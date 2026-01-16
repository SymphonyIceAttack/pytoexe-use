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

# ====== LOGO ASCII MINIMALISTA ======
cols = sh.get_terminal_size().columns
lines, _ = os.get_terminal_size()

logo_arriba = [
"███████╗ ██████╗ ███╗   ███╗██████╗ ██╗",
"╚══███╔╝██╔═══██╗████╗ ████║██╔══██╗██║",
"  ███╔╝ ██║   ██║██╔████╔██║██████╔╝██║",
" ███╔╝  ██║   ██║██║╚██╔╝██║██╔══██╗██║",
"███████╗╚██████╔╝██║ ╚═╝ ██║██████╔╝██║",
"╚══════╝ ╚═════╝ ╚═╝     ╚╝╚═════╝ ╚╝╚══",
""
]

subtextos = [
"       CLEANER  Fivem Ready para spoof ",
"       Creador Discord / dimezombie",
"               OWNER Zombie",
"       https://discord.gg/2pmPXjCS4t",
""
]

# ====== ANIMACIÓN ZOMBIEYMDZ ======
def zombie_marquee():
    text = " ZOMBIEYMDZ "
    padding = " " * 50
    scroll_text = padding + text
    while True:
        print(scroll_text[:50].center(cols), end="\r")
        scroll_text = scroll_text[1:] + scroll_text[0]
        time.sleep(0.15)

# ====== MOSTRAR LOGO ======
def mostrar_logo():
    os.system("cls")
    # Logo arriba
    for line in logo_arriba:
        print(line.center(cols))
    # Animación ZombieYMDZ corriendo
    threading.Thread(target=zombie_marquee, daemon=True).start()
    # Subtextos
    for line in subtextos:
        print(line.center(cols))
    # Decoración esquina inferior izquierda
    for i in range(lines - (len(logo_arriba) + len(subtextos) + 2)):
        print()
    print("YVMPO MODZ")  # siempre en esquina inferior izquierda

mostrar_logo()

# ====== MENÚ DE OPCIONES ======
print("\n[1] Limpieza de Temporales (PC Speed)")
print("[2] Desvincular FiveM de Rockstar (Unlink Account)")
print("="*45)
opcion = input("Selecciona una opción Zombie: ")

# ====== PROCESO DE TRABAJO ======
def trabajando_animacion(duracion=4):
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duracion
    i = 0
    while time.time() < end_time:
        print(f"\rZombieYMDZ trabajando... {frames[i % len(frames)]}", end="", flush=True)
        time.sleep(0.15)
        i += 1
    print("\rProceso finalizado correctamente.   ")

# ====== RUTAS DE LIMPIEZA ======
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

# ====== SALIDA ======
print("\nPROCESO COMPLETADO")
print("Presiona cualquier tecla para salir...")
msvcrt.getch()