 import os
import shutil
import tempfile
import ctypes
import time
import shutil as sh
import msvcrt
import subprocess
import threading

# ====== HANDLE DE CONSOLA ======
kernel32 = ctypes.windll.kernel32
handle = kernel32.GetStdHandle(-11)

# Códigos de color: rojo, verde, amarillo
colores = [12, 10, 14]

# ====== HILO PARA CICLO DE COLORES ======
def ciclo_colores():
    while True:
        for color in colores:
            kernel32.SetConsoleTextAttribute(handle, color)
            time.sleep(2)

threading.Thread(target=ciclo_colores, daemon=True).start()

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

def unlink_fivem():
    procesos = ["FiveM.exe", "FiveM_b2189_GTAProcess.exe", "SocialClubHelper.exe", "Launcher.exe", "RockstarService.exe"]
    for proc in procesos:
        subprocess.run(f"taskkill /f /im {proc} >nul 2>&1", shell=True)
    
    rutas = [
        os.path.expandvars(r"%AppData%\CitizenFX"),
        os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\cache\priv"),
        os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\cache\servers"),
        os.path.expandvars(r"%LocalAppData%\Rockstar Games"),
        os.path.join(os.path.expanduser("~"), "Documents", "Rockstar Games", "Social Club"),
        os.path.join(os.path.expanduser("~"), "Documents", "Rockstar Games", "Launcher")
    ]
    
    for r in rutas:
        if os.path.exists(r):
            shutil.rmtree(r, ignore_errors=True)

def limpiar_steam():
    print("\n--- Iniciando Desvinculación de Steam ---")
    local_appdata = os.getenv('LOCALAPPDATA')
    
    subprocess.run("taskkill /f /im Steam.exe /t", shell=True, capture_output=True)
    subprocess.run("taskkill /f /im FiveM.exe /t", shell=True, capture_output=True)

    rutas = [
        os.path.join(local_appdata, "DigitalEntitlements"),
        os.path.join(local_appdata, "FiveM", "FiveM.app", "cache", "priv"),
        os.path.join(local_appdata, "FiveM", "FiveM.app", "cache", "servers")
    ]

    for ruta in rutas:
        if os.path.exists(ruta):
            try:
                shutil.rmtree(ruta)
                print(f"[OK] Eliminado: {ruta}")
            except:
                print(f"[ERROR] No se pudo borrar: {ruta}")

    os.system('reg delete "HKEY_CURRENT_USER\\Software\\Valve\\Steam" /v "AutoLoginUser" /f >nul 2>&1')
    print("[!] Steam desvinculado correctamente.")

def limpiar_xbox():
    os.system('powershell -Command "Get-AppxPackage xboxapp | Remove-AppxPackage" >nul 2>&1')
    print("[!] Rastros de Xbox/Social Club eliminados.")

# ====== LOGO ASCII ======
cols = sh.get_terminal_size().columns
lines, _ = os.get_terminal_size()

logo_arriba = [
"███████╗ ██████╗ ███╗   ███╗██████╗ ██╗███████╗",
"╚══███╔╝██╔═══██╗████╗ ████║██╔══██╗██║╚══███╔╝",
"  ███╔╝ ██║   ██║██╔████╔██║██████╔╝██║  ███╔╝ ",
" ███╔╝  ██║   ██║██║╚██╔╝██║██╔══██╗██║ ███╔╝  ",
"███████╗╚██████╔╝██║ ╚═╝ ██║██████╔╝██║███████╗",
"╚══════╝ ╚═════╝ ╚═╝     ╚╝╚═════╝ ╚╝╚══════╝",
""
]

subtextos = [
"           CLEANER  &  MULTI-UNLINKER",
"       Creador Discord / dimezombie",
"               YMDZ",
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
    for line in logo_arriba:
        print(line.center(cols))
    threading.Thread(target=zombie_marquee, daemon=True).start()
    for line in subtextos:
        print(line.center(cols))
    for i in range(lines - (len(logo_arriba) + len(subtextos) + 2)):
        print()
    print("YVMPO MODZ")

# ====== ANIMACIÓN PROCESANDO ======
def trabajando_animacion(duracion=4):
    puntos = ["", ".", "..", "..."]
    end_time = time.time() + duracion
    i = 0
    while time.time() < end_time:
        print(f"\rProcesando{puntos[i % len(puntos)]}   ", end="", flush=True)
        time.sleep(0.5)
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

# ====== MENÚ PRINCIPAL ======
def menu():
    mostrar_logo()
    while True:
        print("\n[1] Limpieza de Temporales (PC Speed)")
        print("[2] Desvincular FiveM / Rockstar")
        print("[3] Desvincular Steam")
        print("[4] Limpiar rastros Xbox / Social Club")
        print("[5] Salir")
        opcion = input("Selecciona una opción: ")

        if opcion == "1":
            for p in paths_general:
                clean_path(p)
            trabajando_animacion()
        elif opcion == "2":
            unlink_fivem()
            trabajando_animacion()
            print("\n[!] FiveM desvinculado correctamente.")
        elif opcion == "3":
            limpiar_steam()
            input("\nPresiona Enter para volver al menú...")
        elif opcion == "4":
            limpiar_xbox()
            input("\nPresiona Enter para volver al menú...")
        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")
            input("\nPresiona Enter para intentar de nuevo...")

    print("\nPROCESO COMPLETADO")
    print("Presiona cualquier tecla para salir...")
    msvcrt.getch()

# ====== EJECUCIÓN CORREGIDA ======
if _name_ == "_main_":
    menu()