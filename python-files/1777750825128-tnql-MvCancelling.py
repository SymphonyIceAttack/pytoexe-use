import time
import threading
import pygetwindow as gw
import psutil
import os
import sys
from pynput.keyboard import Key, Controller, Listener

keyboard = Controller()
enabled = False
space_held = False
last_key = None

def check_steam_version():
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if proc.info['name'].lower() == 'hl.exe':
                game_exe = proc.info['exe']
                if game_exe:
                    game_path = os.path.dirname(game_exe)
                    steam_api = os.path.join(game_path, "steam_api.dll")
                    if os.path.exists(steam_api):
                        return True
                    else:
                        print("\n[!] ERRROR: Non-Steam Version has been detected. Script will turn off.")
                        sys.exit()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def is_cs_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'].lower() == 'hl.exe':
            return True
    return False

def is_cs_focused():
    try:
        active_window = gw.getActiveWindow()
        return active_window and ("Counter-Strike" in active_window.title or "hl" in active_window.title.lower())
    except:
        return False

def on_press(key):
    global enabled, space_held, last_key
    
    if key == Key.insert:
        if is_cs_running():
            if check_steam_version():
                enabled = not enabled
                print(f"INSERT: {'On' if enabled else 'Off'} |", end="\r")
        else:
            print("Waiting: Please connect to Counter-Strike to activate the script! |", end="\r")
        return

    if key == Key.delete:
        print("\n[X] Clossing the script...")
        return False

    if not enabled or not is_cs_focused():
        return

    if key == Key.space:
        space_held = True

    if space_held:
        try:
            if hasattr(key, 'char'):
                k = key.char.lower()
                if k == 'a':
                    keyboard.release('d')
                    last_key = 'a'
                elif k == 'd':
                    keyboard.release('a')
                    last_key = 'd'
        except:
            pass

def on_release(key):
    global space_held, last_key
    if key == Key.space:
        space_held = False
        keyboard.release('a')
        keyboard.release('d')
    
    if hasattr(key, 'char'):
        k = key.char.lower()
        if k in ['a', 'd']:
            last_key = None

print("Counter-Strike 1.6 Movement Cancelling")

if not is_cs_running():
    print("Status: The game has not detected. Please turn on the game.")

with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()