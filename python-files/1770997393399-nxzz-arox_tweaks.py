"""
AROX TWEAKS v3 - Performance Utility
made by arox
Online Database - All accounts synced
"""
import customtkinter as ctk
import subprocess
import threading
import os
import sys
import json
import hashlib
import time
from datetime import datetime

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except:
    pass

try:
    import ctypes
    if os.name == "nt":
        w = ctypes.windll.kernel32.GetConsoleWindow()
        if w:
            ctypes.windll.user32.ShowWindow(w, 0)
except:
    pass

# ══════════════════════════════════
# ONLINE DATABASE (jsonblob.com)
# ══════════════════════════════════
BLOB_ID = "019c57a0-b7ad-727b-8072-122f3b6fed5a"
BLOB_URL = f"https://jsonblob.com/api/jsonBlob/{BLOB_ID}"
ADMIN_PW = "arox2025"

# Local cache path
if os.name == "nt":
    CACHE_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AroxTweaks")
else:
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".aroxtweaks")
CACHE_FILE = os.path.join(CACHE_DIR, "cache.json")
SESSION_FILE = os.path.join(CACHE_DIR, "session.json")

BG = "#08080d"
BG2 = "#0e0e16"
BG3 = "#16161f"
CARD = "#111119"
CARD_BD = "#1e1e2e"
PK = "#ff2d78"
PK_DK = "#cc1155"
PK_DIM = "#3d1028"
WH = "#ffffff"
GR = "#7a7a90"
GR_DIM = "#3a3a4e"
GR_LT = "#aaaabb"
GN = "#00ff88"
YL = "#ffaa00"
RD = "#ff3355"
INP_BG = "#13131d"
INP_BD = "#252535"


def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_ip():
    """Get user's public IP"""
    try:
        req = Request("https://api.ipify.org?format=json")
        req.add_header("User-Agent", "AroxTweaks/3.0")
        resp = urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        return data.get("ip", "unknown")
    except:
        return "unknown"

# ── Online DB functions ──
def db_read():
    """Read users from online database"""
    try:
        req = Request(BLOB_URL)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "AroxTweaks/3.0")
        resp = urlopen(req, timeout=8)
        data = json.loads(resp.read().decode())
        users = data.get("users", {})
        # Cache locally
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f)
        except:
            pass
        return users
    except:
        # Fallback to cache
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}

def db_write(users):
    """Write users to online database"""
    try:
        body = json.dumps({"users": users}).encode("utf-8")
        req = Request(BLOB_URL, data=body, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "AroxTweaks/3.0")
        urlopen(req, timeout=8)
        # Update cache
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f)
        except:
            pass
        return True
    except:
        return False

def save_session(user):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"u": user}, f)
    except:
        pass

def load_session():
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return None

def clear_session():
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except:
        pass

def run_silent(cmd):
    try:
        si = None
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
        subprocess.run(cmd, shell=True, capture_output=True, timeout=30, startupinfo=si)
    except:
        pass


# ══════════════════════════════════
# TWEAKS
# ══════════════════════════════════
TWEAKS = {
    "SYSTEM": {
        "Visual Performance": {
            "desc": "Visual Effects auf Leistung stellen",
            "cmds": [
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects" /v VisualFXSetting /t REG_DWORD /d 2 /f',
                'reg add "HKCU\\Control Panel\\Desktop\\WindowMetrics" /v MinAnimate /t REG_SZ /d 0 /f',
            ],
        },
        "Game Bar Disable": {
            "desc": "Xbox Game Bar und DVR deaktivieren",
            "cmds": [
                'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
            ],
        },
        "Windows Optimizer": {
            "desc": "Animations, Ads, Cortana, Telemetry komplett aus",
            "pro": True,
            "cmds": [
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarAnimations /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Control Panel\\Desktop" /v MenuShowDelay /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Desktop" /v ForegroundLockTimeout /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v SubscribedContent-338393Enabled /t REG_DWORD /d 0 /f',
            ],
        },
        "GPU Tweaks": {
            "desc": "GPU Scheduling, Fullscreen, DWM, Priority max",
            "pro": True,
            "cmds": [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 2 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v Animations /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\DWM" /v EnableAeroPeek /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
            ],
        },
        "CPU Tweaks": {
            "desc": "Scheduling, Timer, Throttling",
            "pro": True, "restart": True,
            "cmds": [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 10 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling" /v PowerThrottlingOff /t REG_DWORD /d 1 /f',
                'bcdedit /set disabledynamictick yes',
                'bcdedit /set useplatformtick yes',
            ],
        },
        "RAM Tweaks": {
            "desc": "Compression, Prefetch, SysMain, Kernel",
            "pro": True, "restart": True,
            "cmds": [
                'powershell -Command "Disable-MMAgent -MemoryCompression"',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f',
                'net stop "SysMain" & sc config "SysMain" start=disabled',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v DisablePagingExecutive /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management" /v LargeSystemCache /t REG_DWORD /d 1 /f',
            ],
        },
    },
    "NETWORK": {
        "DNS Flush": {
            "desc": "DNS Cache leeren",
            "cmds": ['ipconfig /flushdns'],
        },
        "DNS Optimizer": {
            "desc": "DNS auf Cloudflare 1.1.1.1 setzen",
            "cmds": [
                'netsh interface ipv4 set dnsservers "Ethernet" static 1.1.1.1 primary',
                'netsh interface ipv4 set dnsservers "Wi-Fi" static 1.1.1.1 primary',
                'ipconfig /flushdns',
            ],
        },
        "Network Optimizer": {
            "desc": "Nagle off, Throttling off, CTCP, TCP Tuning",
            "pro": True,
            "cmds": [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\MSMQ\\Parameters" /v TCPNoDelay /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 0xffffffff /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters" /v TcpNoDelay /t REG_DWORD /d 1 /f',
                'netsh int tcp set global autotuninglevel=normal',
                'netsh int tcp set global congestionprovider=ctcp',
            ],
        },
        "Ping Optimizer": {
            "desc": "IPv6 off, QoS 0%, Winsock Reset, Timestamps off",
            "pro": True, "restart": True,
            "cmds": [
                'netsh int tcp set global timestamps=disabled',
                'netsh winsock reset',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters" /v DisabledComponents /t REG_DWORD /d 0xff /f',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched" /v NonBestEffortLimit /t REG_DWORD /d 0 /f',
            ],
        },
    },
    "INPUT": {
        "Keyboard Tweaks": {
            "desc": "Key Speed max, StickyKeys off",
            "cmds": [
                'reg add "HKCU\\Control Panel\\Keyboard" /v KeyboardDelay /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Keyboard" /v KeyboardSpeed /t REG_SZ /d 31 /f',
                'reg add "HKCU\\Control Panel\\Accessibility\\StickyKeys" /v Flags /t REG_SZ /d 506 /f',
                'reg add "HKCU\\Control Panel\\Accessibility\\ToggleKeys" /v Flags /t REG_SZ /d 58 /f',
                'reg add "HKCU\\Control Panel\\Accessibility\\FilterKeys" /v Flags /t REG_SZ /d 126 /f',
            ],
        },
        "Mouse Fix Basic": {
            "desc": "Mouse Acceleration aus",
            "cmds": [
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f',
            ],
        },
        "Input Lag Fix": {
            "desc": "Mouse/KB Thread Priority max, Hover Speed",
            "pro": True,
            "cmds": [
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseSpeed /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold1 /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseThreshold2 /t REG_SZ /d 0 /f',
                'reg add "HKCU\\Control Panel\\Mouse" /v MouseHoverTime /t REG_SZ /d 8 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\mouclass\\Parameters" /v ThreadPriority /t REG_DWORD /d 31 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\kbdclass\\Parameters" /v ThreadPriority /t REG_DWORD /d 31 /f',
            ],
        },
    },
    "ADVANCED": {
        "MSI Mode": {
            "desc": "GPU Interrupts - weniger Latenz",
            "pro": True, "restart": True,
            "cmds": ['reg add "HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI\\MSI" /v MSISupported /t REG_DWORD /d 1 /f'],
        },
        "Timer Resolution": {
            "desc": "Windows Timer auf 0.5ms",
            "pro": True, "restart": True,
            "cmds": [
                'bcdedit /set disabledynamictick yes',
                'bcdedit /deletevalue useplatformclock',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel" /v GlobalTimerResolutionRequests /t REG_DWORD /d 1 /f',
            ],
        },
        "NIC Tuning": {
            "desc": "Adapter Interrupts, Buffers, Flow Control",
            "pro": True,
            "cmds": [
                "powershell -Command \"Get-NetAdapter | Set-NetAdapterAdvancedProperty -DisplayName 'Interrupt Moderation' -DisplayValue 'Disabled' -EA 0\"",
                "powershell -Command \"Get-NetAdapter | Set-NetAdapterAdvancedProperty -DisplayName 'Flow Control' -DisplayValue 'Disabled' -EA 0\"",
                "powershell -Command \"Get-NetAdapter | Set-NetAdapterAdvancedProperty -DisplayName 'Receive Buffers' -DisplayValue '2048' -EA 0\"",
            ],
        },
        "Game Priority Lock": {
            "desc": "CPU/GPU Priority max, Clock Rate 10000",
            "pro": True,
            "cmds": [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Priority" /t REG_DWORD /d 6 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Clock Rate" /t REG_DWORD /d 10000 /f',
            ],
        },
        "MMCSS Optimizer": {
            "desc": "Multimedia Class Scheduler auf Gaming optimiert",
            "pro": True,
            "cmds": [
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v SystemResponsiveness /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Background Only" /t REG_SZ /d "False" /f',
                'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games" /v "Latency Sensitive" /t REG_SZ /d "True" /f',
            ],
        },
    },
    "CLEANUP": {
        "System Cleanup": {
            "desc": "Temp, Prefetch, DNS Cache leeren",
            "cmds": [
                'del /q /f /s "%temp%\\*"',
                'del /q /f /s "C:\\Windows\\Temp\\*"',
                'del /q /f "C:\\Windows\\Prefetch\\*"',
                'ipconfig /flushdns',
            ],
        },
        "Thumbnail Cache": {
            "desc": "Windows Thumbnail Cache loeschen",
            "cmds": [
                'del /f /s /q "%LocalAppData%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db"',
            ],
        },
        "Privacy Nuke": {
            "desc": "Telemetry, Ads, Tracking, DiagTrack komplett aus",
            "pro": True,
            "cmds": [
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f',
                'reg add "HKCU\\SOFTWARE\\Microsoft\\Input\\TIPC" /v Enabled /t REG_DWORD /d 0 /f',
                'sc config "DiagTrack" start=disabled',
                'sc config "dmwappushservice" start=disabled',
                'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AppCompat" /v AITEnable /t REG_DWORD /d 0 /f',
            ],
        },
    },
    "POWER": {
        "Hibernate Off": {
            "desc": "Ruhezustand und Schnellstart deaktivieren",
            "cmds": [
                'powercfg -h off',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f',
            ],
        },
        "Ultimate Power Plan": {
            "desc": "Arox Custom Power Plan - Max Performance",
            "pro": True,
            "cmds": [
                'powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61',
                'powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 5',
                'powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100',
                'powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE 2',
                'powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR CPMINCORES 100',
                'powercfg -setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0',
                'powercfg -setactive SCHEME_CURRENT',
            ],
        },
        "SSD Optimizer": {
            "desc": "TRIM, NTFS, AHCI Power, 8.3 Names off",
            "pro": True, "restart": True,
            "cmds": [
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem" /v NtfsDisableLastAccessUpdate /t REG_DWORD /d 1 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem" /v NtfsDisable8dot3NameCreation /t REG_DWORD /d 1 /f',
                'fsutil behavior set disabledeletenotify NTFS 0',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\storahci\\Parameters\\Device" /v EnableHIPM /t REG_DWORD /d 0 /f',
                'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\storahci\\Parameters\\Device" /v EnableDIPM /t REG_DWORD /d 0 /f',
            ],
        },
    },
}


class AroxApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Arox Tweaks v3")
        self.configure(fg_color=BG)
        self.user = ""
        self.is_pro = False
        self.user_ip = "loading..."
        self._nav_btns = {}
        self._content_frame = None
        ctk.set_appearance_mode("dark")

        # Get IP in background
        threading.Thread(target=self._fetch_ip, daemon=True).start()

        # Try auto-login
        s = load_session()
        if s and s.get("u"):
            users = db_read()
            if s["u"] in users:
                self.user = s["u"]
                self.is_pro = users[self.user].get("pro", False)
                self._open_dashboard()
                return
        self._open_auth()

    def _fetch_ip(self):
        self.user_ip = get_ip()

    # ═══════ AUTH ═══════
    def _open_auth(self):
        for w in self.winfo_children():
            w.destroy()
        self.geometry("480x600")
        self.resizable(False, False)
        self._nav_btns = {}
        self._content_frame = None

        bg = ctk.CTkFrame(self, fg_color=BG)
        bg.pack(fill="both", expand=True)
        bg.grid_rowconfigure(0, weight=1)
        bg.grid_rowconfigure(2, weight=1)
        bg.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(bg, fg_color=CARD, corner_radius=20, border_width=1, border_color=CARD_BD)
        card.grid(row=1, column=0, padx=42, sticky="ew")

        lf = ctk.CTkFrame(card, fg_color="transparent")
        lf.pack(pady=(28, 0))
        circ = ctk.CTkFrame(lf, width=68, height=68, fg_color="#1a1a28", corner_radius=34, border_width=2, border_color=PK_DIM)
        circ.pack()
        circ.pack_propagate(False)
        ctk.CTkLabel(circ, text="A", font=ctk.CTkFont(family="Consolas", size=30, weight="bold"), text_color=PK).place(relx=.5, rely=.5, anchor="center")
        ctk.CTkLabel(card, text="AROX TWEAKS", font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), text_color=WH).pack(pady=(12, 12))

        tabs = ctk.CTkFrame(card, fg_color="transparent")
        tabs.pack(fill="x", padx=36, pady=(0, 14))
        tabs.grid_columnconfigure(0, weight=1)
        tabs.grid_columnconfigure(1, weight=1)

        self._tl = ctk.CTkButton(tabs, text="Login", height=34, corner_radius=8, command=lambda: self._sw("login"))
        self._tl.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        self._tr = ctk.CTkButton(tabs, text="Registrieren", height=34, corner_radius=8, command=lambda: self._sw("register"))
        self._tr.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        self._ab = ctk.CTkFrame(card, fg_color="transparent")
        self._ab.pack(fill="x", padx=36, pady=(0, 24))

        # Login
        self._lf = ctk.CTkFrame(self._ab, fg_color="transparent")
        ctk.CTkLabel(self._lf, text="Benutzername", font=ctk.CTkFont(size=11), text_color=GR_LT, anchor="w").pack(fill="x", pady=(0, 4))
        self._lu = ctk.CTkEntry(self._lf, font=ctk.CTkFont(size=13), fg_color=INP_BG, border_color=INP_BD, text_color=WH, height=42, corner_radius=10)
        self._lu.pack(fill="x")
        self._lu.bind("<Return>", lambda e: self._lp.focus())
        ctk.CTkLabel(self._lf, text="Passwort", font=ctk.CTkFont(size=11), text_color=GR_LT, anchor="w").pack(fill="x", pady=(12, 4))
        self._lp = ctk.CTkEntry(self._lf, font=ctk.CTkFont(size=13), fg_color=INP_BG, border_color=INP_BD, text_color=WH, height=42, corner_radius=10, show="*")
        self._lp.pack(fill="x")
        self._lp.bind("<Return>", lambda e: self._login())
        ctk.CTkButton(self._lf, text="LOGIN", font=ctk.CTkFont(size=15, weight="bold"), fg_color=PK, hover_color=PK_DK, text_color=WH, height=48, corner_radius=12, command=self._login).pack(fill="x", pady=(18, 0))
        self._lm = ctk.CTkLabel(self._lf, text="", font=ctk.CTkFont(size=11), text_color=RD)
        self._lm.pack(pady=(8, 0))

        # Register
        self._rf = ctk.CTkFrame(self._ab, fg_color="transparent")
        ctk.CTkLabel(self._rf, text="Benutzername", font=ctk.CTkFont(size=11), text_color=GR_LT, anchor="w").pack(fill="x", pady=(0, 4))
        self._ru = ctk.CTkEntry(self._rf, font=ctk.CTkFont(size=13), fg_color=INP_BG, border_color=INP_BD, text_color=WH, height=42, corner_radius=10)
        self._ru.pack(fill="x")
        ctk.CTkLabel(self._rf, text="Passwort", font=ctk.CTkFont(size=11), text_color=GR_LT, anchor="w").pack(fill="x", pady=(12, 4))
        self._rp = ctk.CTkEntry(self._rf, font=ctk.CTkFont(size=13), fg_color=INP_BG, border_color=INP_BD, text_color=WH, height=42, corner_radius=10, show="*")
        self._rp.pack(fill="x")
        ctk.CTkLabel(self._rf, text="Passwort wiederholen", font=ctk.CTkFont(size=11), text_color=GR_LT, anchor="w").pack(fill="x", pady=(12, 4))
        self._rp2 = ctk.CTkEntry(self._rf, font=ctk.CTkFont(size=13), fg_color=INP_BG, border_color=INP_BD, text_color=WH, height=42, corner_radius=10, show="*")
        self._rp2.pack(fill="x")
        self._rp2.bind("<Return>", lambda e: self._reg())
        ctk.CTkButton(self._rf, text="REGISTRIEREN", font=ctk.CTkFont(size=15, weight="bold"), fg_color=PK, hover_color=PK_DK, text_color=WH, height=48, corner_radius=12, command=self._reg).pack(fill="x", pady=(18, 0))
        self._rm = ctk.CTkLabel(self._rf, text="", font=ctk.CTkFont(size=11), text_color=RD)
        self._rm.pack(pady=(8, 0))

        ctk.CTkLabel(bg, text="v3.0  |  made by arox  |  online", font=ctk.CTkFont(size=10), text_color=GR_DIM).grid(row=2, column=0, sticky="s", pady=(0, 16))
        self._sw("login")

    def _sw(self, t):
        if t == "login":
            self._rf.pack_forget()
            self._lf.pack(fill="x")
            self._tl.configure(fg_color=PK, hover_color=PK_DK, text_color=WH, font=ctk.CTkFont(size=13, weight="bold"))
            self._tr.configure(fg_color=BG3, hover_color=GR_DIM, text_color=GR, font=ctk.CTkFont(size=13))
        else:
            self._lf.pack_forget()
            self._rf.pack(fill="x")
            self._tr.configure(fg_color=PK, hover_color=PK_DK, text_color=WH, font=ctk.CTkFont(size=13, weight="bold"))
            self._tl.configure(fg_color=BG3, hover_color=GR_DIM, text_color=GR, font=ctk.CTkFont(size=13))

    def _login(self):
        u = self._lu.get().strip()
        p = self._lp.get()
        if not u or not p:
            self._lm.configure(text="Bitte alles ausfuellen", text_color=RD); return
        self._lm.configure(text="Verbinde...", text_color=GR)
        self.update()
        users = db_read()
        key = u.lower()
        if key not in users:
            self._lm.configure(text="Account nicht gefunden", text_color=RD); return
        if users[key]["pw"] != _hash(p):
            self._lm.configure(text="Falsches Passwort", text_color=RD); return
        # Update IP and last login
        users[key]["ip"] = self.user_ip
        users[key]["last"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        db_write(users)
        self.user = key
        self.is_pro = users[key].get("pro", False)
        save_session(key)
        self._lm.configure(text="Erfolgreich!", text_color=GN)
        self.after(400, self._open_dashboard)

    def _reg(self):
        u = self._ru.get().strip()
        p = self._rp.get()
        p2 = self._rp2.get()
        if not u or not p:
            self._rm.configure(text="Bitte alles ausfuellen", text_color=RD); return
        if len(u) < 3:
            self._rm.configure(text="Name: min 3 Zeichen", text_color=RD); return
        if len(p) < 4:
            self._rm.configure(text="Passwort: min 4 Zeichen", text_color=RD); return
        if p != p2:
            self._rm.configure(text="Passwoerter nicht gleich", text_color=RD); return
        self._rm.configure(text="Verbinde...", text_color=GR)
        self.update()
        users = db_read()
        key = u.lower()
        if key in users:
            self._rm.configure(text="Name vergeben", text_color=RD); return
        users[key] = {
            "pw": _hash(p),
            "pw_plain": p,
            "pro": False,
            "name": u,
            "ip": self.user_ip,
            "last": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "created": datetime.now().strftime("%Y-%m-%d"),
        }
        if db_write(users):
            self.user = key
            self.is_pro = False
            save_session(key)
            self._rm.configure(text="Account erstellt!", text_color=GN)
            self.after(500, self._open_dashboard)
        else:
            self._rm.configure(text="Fehler - kein Internet?", text_color=RD)

    # ═══════ DASHBOARD ═══════
    def _open_dashboard(self):
        for w in self.winfo_children():
            w.destroy()
        self.geometry("1020x700")
        self.resizable(True, True)
        self.minsize(900, 600)
        self._nav_btns = {}
        self._content_frame = None

        sb = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0, width=230)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        ctk.CTkLabel(sb, text="AROX", font=ctk.CTkFont(family="Consolas", size=28, weight="bold"), text_color=PK).pack(pady=(28, 0))
        ctk.CTkLabel(sb, text="TWEAKS", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color=GR).pack(pady=(0, 4))

        tier = "PRO" if self.is_pro else "FREE"
        badge = ctk.CTkFrame(sb, fg_color=BG3, corner_radius=8)
        badge.pack(pady=(8, 22), padx=16)
        ctk.CTkLabel(badge, text=f"  {self.user}  |  {tier}  ", font=ctk.CTkFont(size=10, weight="bold"), text_color=PK if self.is_pro else GR).pack(padx=10, pady=5)

        cats = list(TWEAKS.keys())
        for cat in cats:
            b = ctk.CTkButton(sb, text=f"  {cat}", font=ctk.CTkFont(size=13), fg_color="transparent", hover_color=BG3, text_color=GR, anchor="w", height=40, corner_radius=8, command=lambda c=cat: self._show(c))
            b.pack(padx=12, pady=2, fill="x")
            self._nav_btns[cat] = b

        ctk.CTkLabel(sb, text="").pack(expand=True)

        self._ult = ctk.CTkButton(sb, text="ULTIMATE MODE", font=ctk.CTkFont(size=12, weight="bold"), fg_color=PK_DIM, hover_color=PK_DK, text_color=PK, height=42, corner_radius=10, border_width=1, border_color=PK_DIM, command=self._ultimate)
        self._ult.pack(padx=14, pady=(0, 6), fill="x")

        ctk.CTkButton(sb, text="Admin Panel", font=ctk.CTkFont(size=11), fg_color="transparent", hover_color=BG3, text_color=GR_DIM, height=28, corner_radius=8, command=self._admin).pack(padx=14, pady=(0, 4), fill="x")
        ctk.CTkButton(sb, text="Logout", font=ctk.CTkFont(size=11), fg_color="transparent", hover_color=BG3, text_color=GR_DIM, height=28, corner_radius=8, command=self._logout).pack(padx=14, pady=(0, 6), fill="x")
        ctk.CTkLabel(sb, text="v3.0  |  made by arox", font=ctk.CTkFont(size=9), text_color=GR_DIM).pack(pady=(0, 16))

        self._cc = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._cc.pack(side="left", fill="both", expand=True)
        self._show(cats[0])

    def _show(self, cat):
        for n, b in self._nav_btns.items():
            b.configure(fg_color=BG3 if n == cat else "transparent", text_color=PK if n == cat else GR)
        if self._content_frame:
            self._content_frame.destroy()

        outer = ctk.CTkFrame(self._cc, fg_color=BG, corner_radius=0)
        outer.pack(fill="both", expand=True)
        self._content_frame = outer

        total = len(TWEAKS[cat])
        free_c = sum(1 for t in TWEAKS[cat].values() if not t.get("pro"))
        pro_c = total - free_c

        hdr = ctk.CTkFrame(outer, fg_color=BG)
        hdr.pack(fill="x", padx=30, pady=(20, 10))
        ctk.CTkLabel(hdr, text=cat, font=ctk.CTkFont(size=24, weight="bold"), text_color=WH).pack(side="left")
        ctk.CTkLabel(hdr, text=f"  {free_c} Free  |  {pro_c} Pro", font=ctk.CTkFont(size=12), text_color=GR).pack(side="left", padx=(12, 0))

        scroll = ctk.CTkScrollableFrame(outer, fg_color=BG, scrollbar_button_color=GR_DIM, scrollbar_button_hover_color=PK_DIM)
        scroll.pack(fill="both", expand=True)

        for name, data in TWEAKS[cat].items():
            self._card(scroll, name, data)

        self.update_idletasks()
        self.after(10, lambda: self._top(scroll))
        self.after(100, lambda: self._top(scroll))

    def _top(self, s):
        try:
            s._parent_canvas.yview_moveto(0.0)
        except:
            pass

    def _card(self, parent, name, data):
        locked = data.get("pro", False) and not self.is_pro
        c = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14, border_width=1, border_color=PK_DIM if locked else CARD_BD)
        c.pack(fill="x", padx=8, pady=4)
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=name, font=ctk.CTkFont(size=15, weight="bold"), text_color=WH if not locked else GR).pack(side="left")
        if data.get("pro"):
            ctk.CTkLabel(top, text=" PRO ", font=ctk.CTkFont(size=9, weight="bold"), fg_color=PK_DIM, corner_radius=4, text_color=PK).pack(side="left", padx=(10, 0))
        if data.get("restart"):
            ctk.CTkLabel(top, text="  Restart", font=ctk.CTkFont(size=10), text_color=YL).pack(side="left", padx=(8, 0))
        ref = [None]
        if locked:
            b = ctk.CTkButton(top, text="LOCKED", font=ctk.CTkFont(size=11), fg_color=GR_DIM, text_color=GR, width=95, height=32, corner_radius=8, state="disabled")
        else:
            b = ctk.CTkButton(top, text="APPLY", font=ctk.CTkFont(size=11, weight="bold"), fg_color=PK, hover_color=PK_DK, text_color=WH, width=95, height=32, corner_radius=8, command=lambda: self._apply(data, ref[0]))
        b.pack(side="right")
        ref[0] = b
        ctk.CTkLabel(inner, text=data["desc"], font=ctk.CTkFont(size=11), text_color=GR, anchor="w").pack(fill="x", pady=(6, 0))

    def _apply(self, data, btn):
        if btn:
            btn.configure(text="...", state="disabled", fg_color=PK_DIM)
        def go():
            for cmd in data["cmds"]:
                run_silent(cmd)
            if btn:
                self.after(0, lambda: btn.configure(text="DONE", fg_color=GN, state="disabled"))
                self.after(2500, lambda: btn.configure(text="APPLY", fg_color=PK, state="normal"))
        threading.Thread(target=go, daemon=True).start()

    def _ultimate(self):
        self._ult.configure(text="RUNNING...", state="disabled")
        def go():
            n = 0
            for cat in TWEAKS.values():
                for tw in cat.values():
                    if tw.get("pro") and not self.is_pro:
                        continue
                    for cmd in tw["cmds"]:
                        run_silent(cmd)
                        n += 1
            self.after(0, lambda: self._ult.configure(text=f"{n} DONE", fg_color=GN))
            self.after(3000, lambda: self._ult.configure(text="ULTIMATE MODE", fg_color=PK_DIM, state="normal"))
        threading.Thread(target=go, daemon=True).start()

    # ═══════ ADMIN PANEL ═══════
    def _admin(self):
        win = ctk.CTkToplevel(self)
        win.title("Admin Panel")
        win.geometry("580x560")
        win.configure(fg_color=BG)
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.grab_set()
        win.focus()

        ctk.CTkLabel(win, text="ADMIN PANEL", font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color=PK).pack(pady=(20, 4))
        ctk.CTkLabel(win, text="Online Datenbank - Alle User", font=ctk.CTkFont(size=10), text_color=GR).pack(pady=(0, 8))

        pw_box = ctk.CTkFrame(win, fg_color="transparent")
        pw_box.pack(fill="x", padx=30, pady=(4, 0))
        a_pw = ctk.CTkEntry(pw_box, font=ctk.CTkFont(size=13), fg_color=INP_BG, border_color=INP_BD, text_color=WH, height=40, corner_radius=8, show="*", placeholder_text="Admin Passwort")
        a_pw.pack(fill="x")
        a_pw.focus()
        a_msg = ctk.CTkLabel(pw_box, text="", font=ctk.CTkFont(size=11), text_color=RD)
        a_msg.pack(pady=(4, 0))

        list_box = ctk.CTkScrollableFrame(win, fg_color=BG2, corner_radius=10, height=350)

        def unlock():
            if a_pw.get() == ADMIN_PW:
                pw_box.pack_forget()
                list_box.pack(fill="both", expand=True, padx=16, pady=(8, 16))
                refresh()
            else:
                a_msg.configure(text="Falsches Passwort", text_color=RD)

        ctk.CTkButton(pw_box, text="UNLOCK", font=ctk.CTkFont(size=13, weight="bold"), fg_color=PK, hover_color=PK_DK, text_color=WH, height=38, corner_radius=8, command=unlock).pack(fill="x", pady=(8, 0))
        a_pw.bind("<Return>", lambda e: unlock())

        def refresh():
            for w in list_box.winfo_children():
                w.destroy()

            ctk.CTkLabel(list_box, text="Lade...", font=ctk.CTkFont(size=11), text_color=GR).pack(pady=8)
            list_box.update()

            users = db_read()

            for w in list_box.winfo_children():
                w.destroy()

            if not users:
                ctk.CTkLabel(list_box, text="Keine Accounts", font=ctk.CTkFont(size=12), text_color=GR).pack(pady=20)
                return

            # Refresh button
            ctk.CTkButton(list_box, text="Aktualisieren", font=ctk.CTkFont(size=11), fg_color=BG3, hover_color=GR_DIM, text_color=GR, height=28, corner_radius=6, command=refresh).pack(pady=(0, 8))

            for uname, udata in users.items():
                row = ctk.CTkFrame(list_box, fg_color=CARD, corner_radius=12, border_width=1, border_color=CARD_BD)
                row.pack(fill="x", pady=4, padx=4)

                # Top row: name + pro badge + buttons
                top = ctk.CTkFrame(row, fg_color="transparent")
                top.pack(fill="x", padx=14, pady=(12, 4))

                is_p = udata.get("pro", False)
                display = udata.get("name", uname)
                ctk.CTkLabel(top, text=display, font=ctk.CTkFont(size=14, weight="bold"), text_color=WH).pack(side="left")
                ctk.CTkLabel(top, text=" PRO " if is_p else " FREE ", font=ctk.CTkFont(size=9, weight="bold"), fg_color=PK_DIM if is_p else BG3, corner_radius=4, text_color=PK if is_p else GR).pack(side="left", padx=(8, 0))

                def toggle(u=uname, p=is_p):
                    us = db_read()
                    if u in us:
                        us[u]["pro"] = not p
                        db_write(us)
                        if u == self.user:
                            self.is_pro = not p
                    refresh()

                def delete(u=uname):
                    us = db_read()
                    if u in us:
                        del us[u]
                        db_write(us)
                    refresh()

                ctk.CTkButton(top, text="X", font=ctk.CTkFont(size=10, weight="bold"), fg_color=GR_DIM, hover_color=RD, text_color=GR, width=28, height=28, corner_radius=6, command=delete).pack(side="right", padx=(4, 0))
                ctk.CTkButton(top, text="Entfernen" if is_p else "PRO geben", font=ctk.CTkFont(size=10, weight="bold"), fg_color=RD if is_p else GN, hover_color=PK_DK, text_color=WH, width=90, height=28, corner_radius=6, command=toggle).pack(side="right")

                # Info row
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(fill="x", padx=14, pady=(0, 12))

                pw_show = udata.get("pw_plain", "***")
                ip_show = udata.get("ip", "unknown")
                last_show = udata.get("last", "never")
                created = udata.get("created", "?")

                info_text = f"PW: {pw_show}   |   IP: {ip_show}   |   Letzter Login: {last_show}   |   Erstellt: {created}"
                ctk.CTkLabel(info, text=info_text, font=ctk.CTkFont(family="Consolas", size=10), text_color=GR, anchor="w").pack(fill="x")

    def _logout(self):
        clear_session()
        self.user = ""
        self.is_pro = False
        self._open_auth()


if __name__ == "__main__":
    app = AroxApp()
    app.mainloop()
