"""
AL.RE.CC ▸ مراقب الشبكة المتقدم  Network Security Admin
كود نهائي شامل في ملف واحد | الإصدار 2.0
(الوحيدة الخارجية المطلوبة) pip install psutil
"""

# ========== المكتبات ==========
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import socket
import subprocess
import platform
import time
import ipaddress
import datetime
import json
import csv
import os
import queue
import urllib.request
from collections import defaultdict

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

# ========== قاموس البرامج المشبوهة (منافذ) ==========
SUSPICIOUS_PORTS: dict[int, tuple[str, str]] = {
    6881: ("BitTorrent", "🔴 خطر"),
    6882: ("BitTorrent", "🔴 خطر"),
    6883: ("BitTorrent", "🔴 خطر"),
    6884: ("BitTorrent", "🔴 خطر"),
    6885: ("BitTorrent", "🔴 خطر"),
    6886: ("BitTorrent", "🔴 خطر"),
    6887: ("BitTorrent", "🔴 خطر"),
    6888: ("BitTorrent", " خطر"),
    6889: ("BitTorrent", "🔴 خطر"),
    51413: ("Transmission", "🔴 خطر"),
    67: ("DHCP Server / SelfShNet", " تحذير حرج"),
    9000: ("SelfShNet HTTP", " تحذير حرج"),
    7080: ("WiFi Hotspot Admin", " تحذير حرج"),
    1194: ("OpenVPN", "🟠 تحذير"),
    1723: ("PPTP VPN", "🟠 تحذير"),
    500: ("IPSec VPN", "🟠 تحذير"),
    4500: ("IPSec NAT-T", "🟠 تحذير"),
    1080: ("SOCKS Proxy", " تحذير"),
    3128: ("Squid Proxy", "🟠 تحذير"),
    8888: ("HTTP Proxy", "🟠 تحذير"),
    8080: ("HTTP Proxy / Tunnel", "🟠 تحذير"),
    5900: ("VNC Remote Desktop", "🟡 انتبه"),
    5800: ("VNC Web Interface", "🟡 انتبه"),
    3389: ("RDP Remote Desktop", " انتبه"),
    22: ("SSH Server", "🟡 انتبه"),
    23: ("Telnet (خطير!)", "🔴 خطر"),
    3333: ("Crypto Mining Stratum", "🔴 خطر"),
    3334: ("Crypto Mining", "🔴 خطر"),
    14444: ("XMR Monero Mining", "🔴 خطر"),
    45560: ("Crypto Pool", "🔴 خطر"),
    9001: ("Tor Relay", "🔴 خطر"),
    9050: ("Tor SOCKS", "🔴 خطر"),
    9150: ("Tor Browser", "🔴 خطر"),
    4444: ("Metasploit/Backdoor", "🚨 تحذير حرج"),
    5555: ("Android ADB / Backdoor", "🚨 تحذير حرج"),
    1337: ("Leet Backdoor", "🚨 تحذير حرج"),
    31337: ("Back Orifice", "🚨 تحذير حرج"),
    27015: ("Steam Game Server", "🟡 انتبه"),
    25565: ("Minecraft Server", "🟡 انتبه"),
    445: ("SMB File Share", "🟡 انتبه"),
    139: ("NetBIOS", "🟡 انتبه"),
    21: ("FTP Server", "🟡 انتبه"),
    8443: ("Alt HTTPS / C&C", "🟠 تحذير"),
    2222: ("Alt SSH", "🟡 انتبه"),
}

SEVERITY_RANK = {
    "🚨 تحذير حرج": 4,
    "🔴 خطر": 3,
    "🟠 تحذير": 2,
    "🟡 انتبه": 1,
}

DEFAULT_CONFIG = {
    "whitelist_macs": [],
    "whitelist_ips": [],
    "blacklist_macs": [],
    "blacklist_ips": [],
    "auto_scan_min": 5,
    "sound_alert": True,
    "popup_alert": True,
    "ports_to_scan": list(SUSPICIOUS_PORTS.keys()),
    "port_timeout": 0.4,
    "scan_threads": 60,
    "alert_email": "",
    "last_scan": "",
}

CONFIG_FILE = "alrecc_network_config.json"


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_subnet(local_ip: str) -> str:
    parts = local_ip.split(".")
    return ".".join(parts[:3]) + ".0/24"


def ping_host(ip: str, timeout: int = 1) -> bool:
    IS_WIN = platform.system().lower() == "windows"
    param = "-n" if IS_WIN else "-c"
    wait = "-w" if IS_WIN else "-W"
    wait_v = str(timeout * 1000) if IS_WIN else str(timeout)
    cmd = ["ping", param, "1", wait, wait_v, ip]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout + 1)
        return r.returncode == 0
    except Exception:
        return False


def get_hostname(ip: str) -> str:
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return "—"


def get_mac_from_arp(ip: str) -> str:
    try:
        IS_WIN = platform.system().lower() == "windows"
        output = subprocess.check_output(
            ["arp", "-a", ip] if IS_WIN else ["arp", "-n", ip],
            timeout=3
        ).decode(errors="ignore")
        sep = "-" if IS_WIN else ":"
        for line in output.splitlines():
            if ip in line:
                for part in line.split():
                    if sep in part and len(part) == 17:
                        return part.upper()
    except Exception:
        pass
    return "—"


def ping_rtt(ip: str) -> float | None:
    try:
        IS_WIN = platform.system().lower() == "windows"
        param = "-n" if IS_WIN else "-c"
        wait = "-w" if IS_WIN else "-W"
        wait_v = "1000" if IS_WIN else "1"
        output = subprocess.check_output(
            ["ping", param, "3", wait, wait_v, ip], timeout=5
        ).decode(errors="ignore")
        for line in output.splitlines():
            ll = line.lower()
            if "average" in ll or "avg" in ll:
                nums = [s for s in line.replace("ms", "").replace("/", " ").split()
                        if s.replace(".", "").isdigit()]
                if nums:
                    return float(nums[-1])
            if "min/avg/max" in ll or "rtt" in ll:
                try:
                    nums = line.split("=")[1].strip().split("/")
                    return float(nums[1])
                except Exception:
                    pass
    except Exception:
        pass
    return None


def quality_label(rtt: float | None) -> str:
    if rtt is None:
        return "متصل"
    if rtt < 5:
        return "🟢 ممتاز"
    if rtt < 20:
        return " جيد"
    if rtt < 80:
        return "🟠 متوسط"
    return "🔴 ضعيف"


def measure_download_speed(url="http://speedtest.tele2.net/1MB.zip",
                           duration=4.0) -> float:
    try:
        start = time.time()
        total = 0
        req = urllib.request.urlopen(url, timeout=12)
        while time.time() - start < duration:
            chunk = req.read(8192)
            if not chunk:
                break
            total += len(chunk)
        elapsed = time.time() - start
        return round((total / elapsed) / (1024 * 1024), 2) if elapsed > 0 else 0.0
    except Exception:
        return 0.0


def scan_ports(ip: str, ports: list[int], timeout: float = 0.4) -> list[int]:
    open_ports = []

    def check(p):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((ip, p)) == 0:
                    open_ports.append(p)
        except Exception:
            pass

    threads = [threading.Thread(target=check, args=(p,), daemon=True) for p in ports]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(open_ports)


class AlertSystem:
    def __init__(self, sound: bool = True, popup: bool = True):
        self.sound = sound
        self.popup = popup
        self._queue: queue.Queue = queue.Queue()

    def fire(self, title: str, msg: str, level: str = "warning"):
        self._queue.put((title, msg, level))
        if self.sound:
            try:
                if HAS_SOUND:
                    freq = 1200 if "حرج" in level else 800
                    winsound.Beep(freq, 400)
                else:
                    print("\a", end="", flush=True)
            except Exception:
                pass

    def get_pending(self):
        items = []
        while not self._queue.empty():
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items


def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class NetworkAdminApp(tk.Tk):

    # ═══════════════════════════════════════════════
    # ️ فقط هنا تم تغيير الألوان إلى الأبيض والفاتح ⬇️
    # ═══════════════════════════════════════════════
    BG        = "#F8FAFC"   # أبيض مائل للرمادي (خلفية رئيسية)
    SURF      = "#F1F5F9"   # سطح فاتح (Header, Sidebar)
    CARD      = "#FFFFFF"   # أبيض نقي (البطاقات)
    CARD2     = "#F8FAFC"   # خلفية ثانية فاتحة
    ACCENT    = "#0EA5E9"   # أزرق سماوي (للتمييز)
    ACCENT2   = "#6366F1"   # بنفسجي
    SUCCESS   = "#22C55E"   # أخضر
    WARNING   = "#F59E0B"   # برتقالي
    DANGER    = "#EF4444"   # أحمر
    CRITICAL  = "#DC2626"   # أحمر غامق
    TEXT      = "#0F172A"   # نص داكن (ضروري للقراءة على الخلفية الفاتحة!)
    MUTED     = "#64748B"   # رمادي متوسط
    BORDER    = "#E2E8F0"   # حدود فاتحة
    BLINK_ON  = "#EF4444"   # وميض أحمر
    BLINK_OFF = "#FEE2E2"   # وميض أحمر فاتح
    # ═══════════════════════════════════════════════

    def __init__(self):
        super().__init__()
        self.title("AL.RE.CC ▸ مراقب الشبكة الأمني المتقدم v2.0")
        self.geometry("1280x800")
        self.minsize(1000, 640)
        self.configure(bg=self.BG)

        self.cfg = load_config()
        self.local_ip = get_local_ip()
        self.subnet = get_subnet(self.local_ip)
        self.devices: dict = {}
        self.alerts_log: list = []
        self.threat_log: list = []
        self._scan_running = False
        self._port_scanning = False
        self._stop_event = threading.Event()
        self._auto_timer = None
        self._blink_state = False
        self.alert_sys = AlertSystem(
            sound=self.cfg["sound_alert"],
            popup=self.cfg["popup_alert"],
        )
        self._alert_count = 0

        self._apply_styles()
        self._build_ui()
        self._start_alert_poller()
        self._schedule_auto_scan()

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        for name in ("Device", "Threat", "Alert", "Unauth"):
            s.configure(f"{name}.Treeview",
                        background=self.CARD, foreground=self.TEXT,
                        fieldbackground=self.CARD, rowheight=30,
                        borderwidth=0, font=("Courier New", 9))
            s.configure(f"{name}.Treeview.Heading",
                        background=self.ACCENT, foreground="white",
                        font=("Courier New", 9, "bold"),
                        borderwidth=0, relief="flat")
            s.map(f"{name}.Treeview",
                  background=[("selected", self.ACCENT2)],
                  foreground=[("selected", "#FFFFFF")])

        s.configure("Cyan.Horizontal.TProgressbar",
                    troughcolor=self.BORDER, background=self.ACCENT, borderwidth=0)
        s.configure("Red.Horizontal.TProgressbar",
                    troughcolor=self.BORDER, background=self.DANGER, borderwidth=0)

        s.configure("TNotebook",
                    background=self.SURF, borderwidth=0,
                    tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=self.CARD, foreground=self.MUTED,
                    font=("Courier New", 10, "bold"),
                    padding=[18, 8], borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", self.ACCENT)],
              foreground=[("selected", "white")])

    def _build_ui(self):
        hdr = tk.Frame(self, bg=self.SURF, height=60)
        hdr.pack(fill=tk.X); hdr.pack_propagate(False)

        tk.Label(hdr, text="⬡  AL.RE.CC  ▸  مراقب الشبكة الأمني",
                 bg=self.SURF, fg=self.ACCENT,
                 font=("Courier New", 15, "bold")).pack(side=tk.LEFT, padx=20)

        self.lbl_alert_badge = tk.Label(hdr, text="",
            bg=self.SURF, fg=self.CRITICAL,
            font=("Courier New", 12, "bold"))
        self.lbl_alert_badge.pack(side=tk.LEFT, padx=6)

        self.lbl_clock = tk.Label(hdr, text="",
            bg=self.SURF, fg=self.MUTED, font=("Courier New", 10))
        self.lbl_clock.pack(side=tk.RIGHT, padx=20)
        self._tick()

        self.lbl_ip = tk.Label(hdr,
            text=f"🌐  {self.subnet}   |   جهازك: {self.local_ip}",
            bg=self.SURF, fg=self.TEXT, font=("Courier New", 9))
        self.lbl_ip.pack(side=tk.RIGHT, padx=20)

        ibar = tk.Frame(self, bg=self.CARD, height=38)
        ibar.pack(fill=tk.X); ibar.pack_propagate(False)

        self.lbl_online   = self._ilabel(ibar, "متصل: 0",        self.SUCCESS)
        self.lbl_unauth   = self._ilabel(ibar, "غير مرخص: 0",    self.DANGER)
        self.lbl_threats  = self._ilabel(ibar, "تهديدات: 0",     self.CRITICAL)
        self.lbl_speed    = self._ilabel(ibar, "سرعتك: —",       self.ACCENT)
        self.lbl_lastscan = self._ilabel(ibar, "آخر فحص: —",     self.MUTED)

        for w in (self.lbl_online, self.lbl_unauth,
                  self.lbl_threats, self.lbl_speed, self.lbl_lastscan):
            w.pack(side=tk.LEFT, padx=14)

        tb = tk.Frame(self, bg=self.BG, pady=6)
        tb.pack(fill=tk.X, padx=10)

        btns = [
            ("🔍  فحص الشبكة",        self.ACCENT,   self._do_scan),
            ("⚡  قياس سرعتك",         self.ACCENT2,  self._do_speedtest),
            ("🛡  فحص التهديدات",      self.WARNING,  self._do_port_scan),
            ("🔄  فحص تلقائي",         self.SUCCESS,  self._toggle_auto_scan),
            ("📋  تقرير PDF",           self.MUTED,    self._export_report),
            ("⚙  الإعدادات",           self.MUTED,    self._open_settings),
        ]
        self.btn_refs = {}
        for txt, col, cmd in btns:
            b = self._mkbtn(tb, txt, col, cmd)
            b.pack(side=tk.LEFT, padx=3)
            self.btn_refs[txt] = b

        self.btn_refs["🔄  فحص تلقائي"].config(
            fg=self.SUCCESS if self.cfg["auto_scan_min"] > 0 else self.MUTED)

        self.prog_var = tk.DoubleVar()
        self.prog = ttk.Progressbar(self, variable=self.prog_var,
                                     maximum=100,
                                     style="Cyan.Horizontal.TProgressbar")
        self.prog.pack(fill=tk.X, padx=10, pady=(2, 0))

        self.lbl_prog = tk.Label(self, text="",
            bg=self.BG, fg=self.MUTED, font=("Courier New", 8))
        self.lbl_prog.pack(anchor="w", padx=12)

        self.nb = ttk.Notebook(self, style="TNotebook")
        self.nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        self.tab_devices = self._make_tab("🌐  الأجهزة المتصلة")
        self.tab_unauth  = self._make_tab("🚫  غير مرخص / محظور")
        self.tab_threats = self._make_tab("🛡  التهديدات والبرامج")
        self.tab_log     = self._make_tab("📋  سجل الأحداث")
        self.tab_wl      = self._make_tab("✅  القائمة البيضاء")

        self._build_tab_devices()
        self._build_tab_unauth()
        self._build_tab_threats()
        self._build_tab_log()
        self._build_tab_whitelist()

        self.status = tk.Label(self, text="  جاهز",
            bg=self.SURF, fg=self.MUTED,
            font=("Courier New", 9), anchor="w")
        self.status.pack(fill=tk.X, side=tk.BOTTOM, ipady=3)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_tab_devices(self):
        p = self.tab_devices
        cols = ("ip","hostname","mac","status","quality","speed_est",
                "first_seen","last_seen","auth_status")
        hdrs = ("IP","اسم الجهاز","MAC","الحالة","جودة","سرعة/جودة",
                "أول اتصال","آخر ظهور","الترخيص")
        widths = [115,160,145,90,105,110,120,120,110]
        self.tree_dev = self._build_tree(p, "Device", cols, hdrs, widths)
        self.tree_dev.tag_configure("local",   foreground=self.ACCENT)
        self.tree_dev.tag_configure("online",  foreground=self.SUCCESS)
        self.tree_dev.tag_configure("offline", foreground=self.MUTED)
        self.tree_dev.tag_configure("unauth",  foreground=self.DANGER)
        self.tree_dev.tag_configure("blocked", foreground="white",
                                    background=self.CRITICAL)
        self.tree_dev.bind("<Double-Button-1>", self._on_device_dbl)

        bf = tk.Frame(p, bg=self.SURF)
        bf.pack(fill=tk.X, padx=8, pady=4)
        self._mkbtn(bf,"➕ أضف للقائمة البيضاء", self.SUCCESS, self._whitelist_selected).pack(side=tk.LEFT,padx=3)
        self._mkbtn(bf,"🚫 أضف للمحظورين",        self.DANGER,  self._blacklist_selected).pack(side=tk.LEFT,padx=3)
        self._mkbtn(bf,"🛡 فحص هذا الجهاز",        self.WARNING, self._scan_selected_device).pack(side=tk.LEFT,padx=3)
        self._mkbtn(bf,"📋 تفاصيل",               self.ACCENT,  self._device_details).pack(side=tk.LEFT,padx=3)

    def _build_tab_unauth(self):
        p = self.tab_unauth
        tk.Label(p, text="الأجهزة غير المرخصة والمحظورة",
                 bg=self.SURF, fg=self.DANGER,
                 font=("Courier New", 11, "bold")).pack(anchor="w", padx=10, pady=6)

        cols = ("ip","hostname","mac","reason","first_detected","count")
        hdrs = ("IP","اسم الجهاز","MAC","السبب","أول رصد","عدد الظهور")
        widths = [115,160,145,200,140,80]
        self.tree_unauth = self._build_tree(p, "Unauth", cols, hdrs, widths)
        self.tree_unauth.tag_configure("blocked",  foreground="white", background=self.CRITICAL)
        self.tree_unauth.tag_configure("unauth",   foreground=self.DANGER)

        bf = tk.Frame(p, bg=self.SURF)
        bf.pack(fill=tk.X, padx=8, pady=4)
        self._mkbtn(bf,"✅ رخّص هذا الجهاز",     self.SUCCESS, self._authorize_unauth).pack(side=tk.LEFT,padx=3)
        self._mkbtn(bf,"🚫 أضف للمحظورين",         self.DANGER,  self._blacklist_unauth).pack(side=tk.LEFT,padx=3)
        self._mkbtn(bf,"🗑 امسح من القائمة",       self.MUTED,   self._remove_unauth).pack(side=tk.LEFT,padx=3)

    def _build_tab_threats(self):
        p = self.tab_threats

        top = tk.Frame(p, bg=self.SURF)
        top.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top, text="كشف البرامج المشبوهة والتهديدات الأمنية",
                 bg=self.SURF, fg=self.WARNING,
                 font=("Courier New", 11, "bold")).pack(side=tk.LEFT)

        self.lbl_threat_count = tk.Label(top, text="",
            bg=self.SURF, fg=self.CRITICAL, font=("Courier New", 11, "bold"))
        self.lbl_threat_count.pack(side=tk.RIGHT)

        cols = ("ip","hostname","port","app","severity","detected_at")
        hdrs = ("IP","اسم الجهاز","المنفذ","البرنامج","الخطورة","وقت الكشف")
        widths = [115,160,80,180,130,140]
        self.tree_threats = self._build_tree(p, "Threat", cols, hdrs, widths)
        self.tree_threats.tag_configure("critical", foreground="white", background=self.CRITICAL)
        self.tree_threats.tag_configure("danger",   foreground="white", background=self.DANGER)
        self.tree_threats.tag_configure("warning",  foreground=self.TEXT, background="#FEF3C7")
        self.tree_threats.tag_configure("info",     foreground=self.TEXT)

        frame_ports = tk.LabelFrame(p, text=" قاموس التهديدات المعروفة ",
            bg=self.SURF, fg=self.ACCENT, font=("Courier New", 9),
            bd=1, relief=tk.SOLID, highlightbackground=self.BORDER)
        frame_ports.pack(fill=tk.X, padx=10, pady=4)

        self.ports_txt = tk.Text(frame_ports, height=5, bg=self.CARD2,
            fg=self.MUTED, font=("Courier New", 8), state=tk.NORMAL,
            wrap=tk.WORD, relief=tk.FLAT)
        self.ports_txt.pack(fill=tk.X, padx=4, pady=4)
        self._fill_ports_legend()

    def _build_tab_log(self):
        p = self.tab_log
        top = tk.Frame(p, bg=self.SURF)
        top.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top, text="سجل الأحداث والتنبيهات",
                 bg=self.SURF, fg=self.TEXT,
                 font=("Courier New", 11, "bold")).pack(side=tk.LEFT)
        self._mkbtn(top,"🗑 مسح",self.MUTED,self._clear_log).pack(side=tk.RIGHT)
        self._mkbtn(top,"💾 تصدير CSV",self.WARNING,self._export_log).pack(side=tk.RIGHT,padx=4)

        self.log_txt = tk.Text(p, bg=self.CARD2, fg=self.TEXT,
            font=("Courier New", 9), state=tk.DISABLED, relief=tk.FLAT,
            wrap=tk.WORD, selectbackground=self.ACCENT2)
        sb = ttk.Scrollbar(p, command=self.log_txt.yview)
        self.log_txt.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,4))
        self.log_txt.pack(fill=tk.BOTH, expand=True, padx=(10,0), pady=(0,6))

        self.log_txt.tag_config("join",     foreground=self.SUCCESS)
        self.log_txt.tag_config("leave",    foreground=self.MUTED)
        self.log_txt.tag_config("unauth",   foreground=self.DANGER)
        self.log_txt.tag_config("critical", foreground=self.CRITICAL)
        self.log_txt.tag_config("threat",   foreground=self.WARNING)
        self.log_txt.tag_config("info",     foreground=self.ACCENT)
        self.log_txt.tag_config("speed",    foreground="#8B5CF6")
        self.log_txt.tag_config("sep",      foreground=self.BORDER)

    def _build_tab_whitelist(self):
        p = self.tab_wl

        lf_w = tk.LabelFrame(p, text="  ✅  الأجهزة المرخصة (Whitelist)  ",
            bg=self.SURF, fg=self.SUCCESS, font=("Courier New", 10, "bold"),
            bd=1, relief=tk.SOLID, highlightbackground=self.BORDER)
        lf_w.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.lb_white = tk.Listbox(lf_w, bg=self.CARD, fg=self.SUCCESS,
            font=("Courier New", 10), selectbackground=self.ACCENT2,
            relief=tk.FLAT, activestyle="none")
        self.lb_white.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self._refresh_whitelist_view()

        wf = tk.Frame(lf_w, bg=self.SURF)
        wf.pack(fill=tk.X, padx=6, pady=4)
        self._mkbtn(wf,"➕ أضف MAC/IP",self.SUCCESS,self._add_whitelist_manual).pack(side=tk.LEFT,padx=3)
        self._mkbtn(wf,"🗑 احذف",       self.DANGER, self._del_whitelist).pack(side=tk.LEFT,padx=3)

        lf_b = tk.LabelFrame(p, text="  🚫  الأجهزة المحظورة (Blacklist)  ",
            bg=self.SURF, fg=self.DANGER, font=("Courier New", 10, "bold"),
            bd=1, relief=tk.SOLID, highlightbackground=self.BORDER)
        lf_b.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,8))

        self.lb_black = tk.Listbox(lf_b, bg=self.CARD, fg=self.DANGER,
            font=("Courier New", 10), selectbackground=self.ACCENT2,
            relief=tk.FLAT, activestyle="none")
        self.lb_black.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self._refresh_blacklist_view()

        bf2 = tk.Frame(lf_b, bg=self.SURF)
        bf2.pack(fill=tk.X, padx=6, pady=4)
        self._mkbtn(bf2,"➕ أضف MAC/IP",self.DANGER,  self._add_blacklist_manual).pack(side=tk.LEFT,padx=3)
        self._mkbtn(bf2,"🗑 احذف",       self.MUTED,  self._del_blacklist).pack(side=tk.LEFT,padx=3)

    def _make_tab(self, title: str) -> tk.Frame:
        f = tk.Frame(self.nb, bg=self.SURF)
        self.nb.add(f, text=title)
        return f

    def _mkbtn(self, parent, text, color, cmd) -> tk.Button:
        return tk.Button(parent, text=text, command=cmd,
                         bg=self.CARD, fg=color,
                         activebackground=self.BORDER,
                         activeforeground=color,
                         font=("Courier New", 9, "bold"),
                         relief=tk.FLAT, padx=10, pady=5,
                         cursor="hand2",
                         highlightthickness=1,
                         highlightbackground=color)

    def _ilabel(self, parent, text, color) -> tk.Label:
        return tk.Label(parent, text=text,
                        bg=self.CARD, fg=color,
                        font=("Courier New", 9, "bold"))

    def _build_tree(self, parent, style, cols, hdrs, widths) -> ttk.Treeview:
        frame = tk.Frame(parent, bg=self.SURF)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,4))

        tree = ttk.Treeview(frame, columns=cols, show="headings",
                             style=f"{style}.Treeview", selectmode="browse")
        for col, hdr, w in zip(cols, hdrs, widths):
            tree.heading(col, text=hdr)
            tree.column(col, width=w, anchor="center", minwidth=60)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def _fill_ports_legend(self):
        self.ports_txt.config(state=tk.NORMAL)
        self.ports_txt.delete("1.0", tk.END)
        lines = []
        for port, (app, sev) in sorted(SUSPICIOUS_PORTS.items(),
                                        key=lambda x: -SEVERITY_RANK.get(x[1][1], 0)):
            lines.append(f"  {sev}  منفذ {port:>5}  ◂  {app}")
        self.ports_txt.insert(tk.END, "\n".join(lines))
        self.ports_txt.config(state=tk.DISABLED)

    def _tick(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.lbl_clock.config(text=now)
        self.after(1000, self._tick)

    def _do_scan(self):
        if self._scan_running:
            self._log("⚠  الفحص جارٍ بالفعل", "info"); return
        self._stop_event.clear()
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        self._scan_running = True
        self._set_status("⏳  فحص الشبكة...")
        self._log(f"{'━'*55}", "sep")
        self._log(f"▶  بدء فحص  {self.subnet}", "info")

        network  = list(ipaddress.ip_network(self.subnet, strict=False).hosts())
        total    = len(network)
        counter  = [0]
        lock     = threading.Lock()

        def check(ip_obj):
            if self._stop_event.is_set(): return
            ip = str(ip_obj)
            up = ping_host(ip)
            with lock:
                counter[0] += 1
                pct = counter[0] / total * 100
                self.after(0, lambda p=pct, i=ip: (
                    self.prog_var.set(p),
                    self.lbl_prog.config(text=f"فحص {i}  ({counter[0]}/{total})")
                ))
                if up:
                    ts       = datetime.datetime.now().strftime("%H:%M:%S")
                    hostname = get_hostname(ip)
                    mac      = get_mac_from_arp(ip)
                    rtt      = ping_rtt(ip)
                    quality  = quality_label(rtt)
                    is_local = (ip == self.local_ip)
                    prev     = self.devices.get(ip, {})
                    fseen    = prev.get("first_seen", ts)
                    was_up   = "🟢" in prev.get("status", "")

                    auth_status = self._check_authorization(ip, mac)

                    self.devices[ip] = {
                        "hostname":    hostname,
                        "mac":         mac,
                        "status":      "متصل 🟢",
                        "quality":     quality,
                        "rtt":         rtt,
                        "speed_est":   f"{rtt:.1f}ms" if rtt else "—",
                        "first_seen":  fseen,
                        "last_seen":   ts,
                        "is_local":    is_local,
                        "auth_status": auth_status,
                        "open_ports":  prev.get("open_ports", []),
                    }

                    if not was_up:
                        label = " (جهازك)" if is_local else ""
                        self.after(0, lambda i=ip, h=hostname, l=label, a=auth_status:
                            self._on_device_joined(i, h, l, a))
                else:
                    if ip in self.devices and "" in self.devices[ip].get("status", ""):
                        ts2 = datetime.datetime.now().strftime("%H:%M:%S")
                        self.devices[ip]["status"]    = "غير متصل 🔴"
                        self.devices[ip]["last_seen"] = ts2
                        hn = self.devices[ip].get("hostname", "—")
                        self.after(0, lambda i=ip, h=hn:
                            self._log(f"⬛  انقطع الاتصال  {i}  {h}", "leave"))

        BATCH = self.cfg["scan_threads"]
        for i in range(0, total, BATCH):
            if self._stop_event.is_set(): break
            batch   = network[i:i+BATCH]
            threads = [threading.Thread(target=check,args=(h,),daemon=True) for h in batch]
            for t in threads: t.start()
            for t in threads: t.join()

        ts_done = datetime.datetime.now().strftime("%H:%M:%S")
        self.cfg["last_scan"] = ts_done
        save_config(self.cfg)

        online_n = sum(1 for d in self.devices.values() if "🟢" in d.get("status",""))
        unauth_n = sum(1 for d in self.devices.values()
                       if d.get("auth_status","") in ("غير مرخص","محظور"))

        self.after(0, self._refresh_all_tables)
        self.after(0, lambda: (
            self.prog_var.set(100),
            self.lbl_prog.config(text=f"✓ اكتمل الفحص — {online_n} متصل"),
            self.lbl_online.config(text=f"متصل: {online_n}"),
            self.lbl_unauth.config(text=f"غير مرخص: {unauth_n}"),
            self.lbl_lastscan.config(text=f"آخر فحص: {ts_done}"),
            self._set_status(f"✅  الفحص اكتمل — {online_n} جهاز متصل"),
        ))
        self._log(f"✅  الفحص اكتمل  ▸  {online_n} متصل  |  {unauth_n} غير مرخص", "info")
        self._scan_running = False

    def _do_port_scan(self):
        if self._port_scanning:
            self._log("  فحص التهديدات جارٍ", "info"); return
        online = [ip for ip, d in self.devices.items() if "🟢" in d.get("status","")]
        if not online:
            messagebox.showinfo("تنبيه", "افحص الشبكة أولاً للكشف عن الأجهزة المتصلة."); return
        self._port_scanning = True
        threading.Thread(target=self._port_scan_worker, args=(online,), daemon=True).start()

    def _port_scan_worker(self, ips: list[str]):
        self._set_status(f"🛡  فحص التهديدات على {len(ips)} جهاز...")
        self._log(f"🛡  بدء فحص التهديدات — {len(ips)} جهاز", "threat")
        ports = self.cfg["ports_to_scan"]
        timeout = self.cfg["port_timeout"]
        threat_count = 0

        for idx, ip in enumerate(ips):
            if self._stop_event.is_set(): break
            pct = (idx + 1) / len(ips) * 100
            self.after(0, lambda p=pct, i=ip: (
                self.prog_var.set(p),
                self.lbl_prog.config(text=f"🛡 فحص تهديدات {i} ({idx+1}/{len(ips)})")
            ))

            open_ports = scan_ports(ip, ports, timeout)
            hostname   = self.devices.get(ip, {}).get("hostname", "—")

            if ip in self.devices:
                self.devices[ip]["open_ports"] = open_ports

            for port in open_ports:
                app, sev = SUSPICIOUS_PORTS.get(port, ("غير معروف", "🟡 انتبه"))
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                entry = {
                    "ip": ip, "hostname": hostname,
                    "port": port, "app": app,
                    "severity": sev, "detected_at": ts,
                }
                self.threat_log.append(entry)
                threat_count += 1
                self.after(0, lambda e=entry: self._add_threat_row(e))

                if SEVERITY_RANK.get(sev, 0) >= 3:
                    msg = f"🚨  تهديد خطير على {ip}\n{app}  (منفذ {port})"
                    self.alert_sys.fire(f"تهديد أمني — {app}", msg, sev)
                    self.after(0, lambda m=msg: self._log(m, "critical"))
                    self._alert_count += 1
                else:
                    self.after(0, lambda i=ip, a=app, pt=port, s=sev:
                        self._log(f"⚠  {i}  ▸  {a}  (:{pt})  {s}", "threat"))

        self.after(0, lambda: (
            self.lbl_threats.config(text=f"تهديدات: {threat_count}"),
            self.lbl_threat_count.config(text=f"إجمالي التهديدات المكتشفة: {threat_count}"),
            self._set_status(f"  اكتمل فحص التهديدات — {threat_count} تهديد"),
        ))
        self._log(f"🛡  فحص التهديدات اكتمل — {threat_count} تهديد مكتشف", "threat")
        self._port_scanning = False

    def _add_threat_row(self, e: dict):
        sev = e["severity"]
        rank = SEVERITY_RANK.get(sev, 0)
        tag = "critical" if rank == 4 else ("danger" if rank == 3
              else ("warning" if rank == 2 else "info"))
        self.tree_threats.insert("", 0, values=(
            e["ip"], e["hostname"], e["port"],
            e["app"], e["severity"], e["detected_at"]
        ), tags=(tag,))

    def _scan_selected_device(self):
        sel = self.tree_dev.selection()
        if not sel: return
        vals = self.tree_dev.item(sel[0], "values")
        ip   = vals[0]
        if not ip: return
        self._log(f"  فحص تهديدات الجهاز: {ip}", "info")
        threading.Thread(target=self._port_scan_worker, args=([ip],), daemon=True).start()

    def _do_speedtest(self):
        self.btn_refs["⚡  قياس سرعتك"].config(state=tk.DISABLED, text="⏳  يقيس...")
        self._log("⚡  قياس سرعة التحميل لجهازك...", "speed")
        def run():
            speed = measure_download_speed()
            self.after(0, lambda: (
                self.lbl_speed.config(text=f"سرعتك: {speed:.2f} MB/s"),
                self.btn_refs["⚡  قياس سرعتك"].config(
                    state=tk.NORMAL, text="⚡  قياس سرعتك"),
                self._log(f"📶  سرعة تحميلك: {speed:.2f} MB/s  ({speed*8:.1f} Mbps)", "speed"),
            ))
            if self.local_ip in self.devices:
                self.devices[self.local_ip]["speed_est"] = f"{speed:.2f} MB/s"
                self.after(0, self._refresh_devices_table)
        threading.Thread(target=run, daemon=True).start()

    def _check_authorization(self, ip: str, mac: str) -> str:
        bl_macs = self.cfg.get("blacklist_macs", [])
        bl_ips  = self.cfg.get("blacklist_ips",  [])
        wl_macs = self.cfg.get("whitelist_macs", [])
        wl_ips  = self.cfg.get("whitelist_ips",  [])

        if mac in bl_macs or ip in bl_ips:
            return "محظور "
        if ip == self.local_ip:
            return "جهازك ✅"
        has_wl = bool(wl_macs or wl_ips)
        if not has_wl:
            return "غير محدد"
        if mac in wl_macs or ip in wl_ips:
            return "مرخص ✅"
        return "غير مرخص "

    def _on_device_joined(self, ip, hostname, label, auth_status):
        if "محظور" in auth_status:
            self._log(f"🚨  جهاز محظور اتصل!  {ip}  {hostname}", "critical")
            self.alert_sys.fire("جهاز محظور!", f"الجهاز {ip} ({hostname}) محظور وقد اتصل!", "حرج")
            self._alert_count += 1
            self._blink_start()
            self._add_unauth_row(ip, hostname,
                                 self.devices[ip].get("mac","—"),
                                 "جهاز محظور ")
        elif "غير مرخص" in auth_status:
            self._log(f"  جهاز غير مرخص:  {ip}  {hostname}", "unauth")
            self.alert_sys.fire("جهاز غير مرخص", f"{ip} ({hostname})", "تحذير")
            self._alert_count += 1
            self._add_unauth_row(ip, hostname,
                                 self.devices[ip].get("mac","—"),
                                 "غير مرخص ⚠")
        else:
            self._log(f"✅  اتصل  {ip}  {hostname}{label}", "join")

        self.after(0, lambda: self.lbl_alert_badge.config(
            text=f"🔔 {self._alert_count} تنبيه" if self._alert_count > 0 else ""))

    def _add_unauth_row(self, ip, hostname, mac, reason):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        for row in self.tree_unauth.get_children():
            if self.tree_unauth.item(row,"values")[0] == ip:
                old = self.tree_unauth.item(row,"values")
                cnt = int(old[5]) + 1 if old[5].isdigit() else 2
                self.tree_unauth.item(row, values=(ip,hostname,mac,reason,old[4],cnt))
                return
        tag = "blocked" if "محظور" in reason else "unauth"
        self.tree_unauth.insert("", 0, values=(ip,hostname,mac,reason,ts,"1"), tags=(tag,))

    def _refresh_all_tables(self):
        self._refresh_devices_table()

    def _refresh_devices_table(self):
        for r in self.tree_dev.get_children(): self.tree_dev.delete(r)
        sorted_d = sorted(self.devices.items(),
                          key=lambda x: (0 if "🟢" in x[1].get("status","") else 1, x[0]))
        for ip, info in sorted_d:
            auth = info.get("auth_status","—")
            if "محظور" in auth:    tag = "blocked"
            elif "غير مرخص" in auth: tag = "unauth"
            elif info.get("is_local"): tag = "local"
            elif "🟢" in info.get("status",""): tag = "online"
            else: tag = "offline"

            self.tree_dev.insert("", tk.END, values=(
                ip,
                info.get("hostname","—"),
                info.get("mac","—"),
                info.get("status","—"),
                info.get("quality","—"),
                info.get("speed_est","—"),
                info.get("first_seen","—"),
                info.get("last_seen","—"),
                auth,
            ), tags=(tag,))

    def _get_selected_ip_mac(self, tree=None) -> tuple[str, str]:
        t = tree or self.tree_dev
        sel = t.selection()
        if not sel: return "", ""
        vals = t.item(sel[0], "values")
        return vals[0], vals[2] if len(vals) > 2 else ""

    def _whitelist_selected(self):
        ip, mac = self._get_selected_ip_mac()
        if not ip: return
        choice = simpledialog.askstring("إضافة للقائمة البيضاء",
            f"أضف بواسطة:\nIP: {ip}\nMAC: {mac}\n\nاكتب IP أو MAC:")
        if not choice: return
        choice = choice.strip()
        if ":" in choice and len(choice) == 17:
            if choice.upper() not in self.cfg["whitelist_macs"]:
                self.cfg["whitelist_macs"].append(choice.upper())
        elif "." in choice:
            if choice not in self.cfg["whitelist_ips"]:
                self.cfg["whitelist_ips"].append(choice)
        save_config(self.cfg)
        self._refresh_whitelist_view()
        self._log(f"✅  أضيف للقائمة البيضاء: {choice}", "join")

    def _blacklist_selected(self):
        ip, mac = self._get_selected_ip_mac()
        if not ip: return
        choice = simpledialog.askstring("إضافة للمحظورين",
            f"IP: {ip}\nMAC: {mac}\n\nاكتب IP أو MAC:")
        if not choice: return
        choice = choice.strip()
        if ":" in choice and len(choice) == 17:
            if choice.upper() not in self.cfg["blacklist_macs"]:
                self.cfg["blacklist_macs"].append(choice.upper())
        elif "." in choice:
            if choice not in self.cfg["blacklist_ips"]:
                self.cfg["blacklist_ips"].append(choice)
        save_config(self.cfg)
        self._refresh_blacklist_view()
        self._log(f"🚫  أضيف للمحظورين: {choice}", "unauth")

    def _authorize_unauth(self):
        ip, mac = self._get_selected_ip_mac(self.tree_unauth)
        if not ip: return
        if ip not in self.cfg["whitelist_ips"]:
            self.cfg["whitelist_ips"].append(ip)
        save_config(self.cfg)
        sel = self.tree_unauth.selection()
        if sel: self.tree_unauth.delete(sel[0])
        self._refresh_whitelist_view()
        self._log(f"✅  رُخِّص الجهاز: {ip}", "join")

    def _blacklist_unauth(self):
        ip, mac = self._get_selected_ip_mac(self.tree_unauth)
        if not ip: return
        if ip not in self.cfg["blacklist_ips"]:
            self.cfg["blacklist_ips"].append(ip)
        save_config(self.cfg)
        self._refresh_blacklist_view()
        self._log(f"🚫  حُظِر الجهاز: {ip}", "unauth")

    def _remove_unauth(self):
        sel = self.tree_unauth.selection()
        if sel: self.tree_unauth.delete(sel[0])

    def _add_whitelist_manual(self):
        v = simpledialog.askstring("إضافة يدوية", "أدخل IP أو MAC:")
        if not v: return
        v = v.strip()
        if ":" in v and len(v) == 17:
            if v.upper() not in self.cfg["whitelist_macs"]:
                self.cfg["whitelist_macs"].append(v.upper())
        elif v:
            if v not in self.cfg["whitelist_ips"]:
                self.cfg["whitelist_ips"].append(v)
        save_config(self.cfg); self._refresh_whitelist_view()

    def _del_whitelist(self):
        sel = self.lb_white.curselection()
        if not sel: return
        val = self.lb_white.get(sel[0]).strip()
        self.cfg["whitelist_macs"] = [x for x in self.cfg["whitelist_macs"] if x != val]
        self.cfg["whitelist_ips"]  = [x for x in self.cfg["whitelist_ips"]  if x != val]
        save_config(self.cfg); self._refresh_whitelist_view()

    def _add_blacklist_manual(self):
        v = simpledialog.askstring("إضافة يدوية", "أدخل IP أو MAC للحظر:")
        if not v: return
        v = v.strip()
        if ":" in v and len(v) == 17:
            if v.upper() not in self.cfg["blacklist_macs"]:
                self.cfg["blacklist_macs"].append(v.upper())
        elif v:
            if v not in self.cfg["blacklist_ips"]:
                self.cfg["blacklist_ips"].append(v)
        save_config(self.cfg); self._refresh_blacklist_view()

    def _del_blacklist(self):
        sel = self.lb_black.curselection()
        if not sel: return
        val = self.lb_black.get(sel[0]).strip()
        self.cfg["blacklist_macs"] = [x for x in self.cfg["blacklist_macs"] if x != val]
        self.cfg["blacklist_ips"]  = [x for x in self.cfg["blacklist_ips"]  if x != val]
        save_config(self.cfg); self._refresh_blacklist_view()

    def _refresh_whitelist_view(self):
        self.lb_white.delete(0, tk.END)
        for m in self.cfg["whitelist_macs"]: self.lb_white.insert(tk.END, f"  MAC: {m}")
        for i in self.cfg["whitelist_ips"]:  self.lb_white.insert(tk.END, f"  IP:  {i}")

    def _refresh_blacklist_view(self):
        self.lb_black.delete(0, tk.END)
        for m in self.cfg["blacklist_macs"]: self.lb_black.insert(tk.END, f"  MAC: {m}")
        for i in self.cfg["blacklist_ips"]:  self.lb_black.insert(tk.END, f"  IP:  {i}")

    def _on_device_dbl(self, event):
        self._device_details()

    def _device_details(self):
        sel = self.tree_dev.selection()
        if not sel: return
        ip = self.tree_dev.item(sel[0], "values")[0]
        d  = self.devices.get(ip, {})
        open_ports = d.get("open_ports", [])
        port_info  = []
        for p in open_ports:
            app, sev = SUSPICIOUS_PORTS.get(p, ("منفذ مفتوح", "—"))
            port_info.append(f"  :{p}  {app}  {sev}")

        msg = f"""
══════════════════════════════
  تفاصيل الجهاز
══════════════════════════════
  IP          : {ip}
  الاسم       : {d.get('hostname','—')}
  MAC         : {d.get('mac','—')}
  الحالة      : {d.get('status','—')}
  جودة الاتصال: {d.get('quality','—')}
  زمن الاستجابة: {d.get('rtt','—')} ms
  الترخيص    : {d.get('auth_status','—')}
  أول اتصال  : {d.get('first_seen','—')}
  آخر ظهور   : {d.get('last_seen','—')}
══════════════════════════════
  المنافذ المشبوهة المفتوحة:
{chr(10).join(port_info) if port_info else '  لا يوجد'}
══════════════════════════════
"""
        win = tk.Toplevel(self)
        win.title(f"تفاصيل — {ip}")
        win.configure(bg=self.CARD)
        win.geometry("420x380")
        txt = tk.Text(win, bg=self.CARD2, fg=self.TEXT,
                      font=("Courier New", 10), relief=tk.FLAT,
                      wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, msg)
        txt.config(state=tk.DISABLED)

    def _schedule_auto_scan(self):
        mins = self.cfg.get("auto_scan_min", 0)
        if mins > 0:
            ms = mins * 60 * 1000
            self._auto_timer = self.after(ms, self._auto_scan_tick)

    def _auto_scan_tick(self):
        self._log(f"🔄  فحص تلقائي — كل {self.cfg['auto_scan_min']} دقيقة", "info")
        self._do_scan()
        self._schedule_auto_scan()

    def _toggle_auto_scan(self):
        win = tk.Toplevel(self)
        win.title("إعداد الفحص التلقائي")
        win.configure(bg=self.CARD)
        win.geometry("300x160")
        tk.Label(win, text="الفحص التلقائي كل (دقائق):\n0 = إيقاف",
                 bg=self.CARD, fg=self.TEXT, font=("Courier New", 10)).pack(pady=14)
        var = tk.IntVar(value=self.cfg["auto_scan_min"])
        tk.Spinbox(win, from_=0, to=60, textvariable=var,
                   bg=self.CARD2, fg=self.ACCENT,
                   font=("Courier New", 12), width=6, justify="center").pack()

        def apply():
            self.cfg["auto_scan_min"] = var.get()
            save_config(self.cfg)
            if self._auto_timer:
                self.after_cancel(self._auto_timer)
            self._schedule_auto_scan()
            col = self.SUCCESS if var.get() > 0 else self.MUTED
            self.btn_refs["🔄  فحص تلقائي"].config(fg=col)
            self._log(f"🔄  الفحص التلقائي: كل {var.get()} دقيقة", "info")
            win.destroy()

        self._mkbtn(win, "✓ تطبيق", self.SUCCESS, apply).pack(pady=10)

    def _start_alert_poller(self):
        def poll():
            items = self.alert_sys.get_pending()
            for title, msg, level in items:
                self._show_alert_popup(title, msg, level)
            self.after(1000, poll)
        self.after(1000, poll)

    def _show_alert_popup(self, title, msg, level):
        if not self.cfg.get("popup_alert", True): return
        popup = tk.Toplevel(self)
        popup.title(f"🔔  {title}")
        color = self.CRITICAL if "حرج" in level else self.DANGER
        popup.configure(bg=color)
        popup.geometry("380x180")
        popup.lift()
        popup.attributes("-topmost", True)

        tk.Label(popup, text=f"🚨  {title}",
                 bg=color, fg="white",
                 font=("Courier New", 12, "bold")).pack(pady=10)
        tk.Label(popup, text=msg, bg=color, fg="white",
                 font=("Courier New", 10),
                 wraplength=340, justify="center").pack(pady=4)
        self._mkbtn(popup, "إغلاق", "white", popup.destroy).pack(pady=10)
        popup.after(8000, lambda: popup.destroy() if popup.winfo_exists() else None)

    def _blink_start(self):
        self._blink_state = True
        self._do_blink()

    def _do_blink(self):
        if not self._blink_state: return
        c = self.BLINK_ON if int(time.time()) % 2 == 0 else self.BLINK_OFF
        self.lbl_alert_badge.config(fg=c)
        self.after(500, self._do_blink)

    def _log(self, msg: str, tag: str = "info"):
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        self.alerts_log.append({"time": ts, "msg": msg, "tag": tag})
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.insert(tk.END, line, tag)
        self.log_txt.see(tk.END)
        self.log_txt.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.delete("1.0", tk.END)
        self.log_txt.config(state=tk.DISABLED)

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile=f"alrecc_log_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv")
        if not path: return
        try:
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["الوقت","الرسالة","النوع"])
                for e in self.alerts_log:
                    w.writerow([e["time"],e["msg"],e["tag"]])
            self._log(f"💾  تم تصدير السجل: {path}", "info")
            messagebox.showinfo("تصدير","تم الحفظ بنجاح ✓")
        except Exception as ex:
            messagebox.showerror("خطأ", str(ex))

    def _export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv")],
            initialfile=f"alrecc_report_{datetime.datetime.now():%Y%m%d_%H%M%S}.csv")
        if not path: return
        try:
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["IP","اسم الجهاز","MAC","الحالة","جودة","زمن ms",
                             "الترخيص","أول اتصال","آخر ظهور","منافذ مشبوهة"])
                for ip, d in sorted(self.devices.items()):
                    w.writerow([
                        ip, d.get("hostname","—"), d.get("mac","—"),
                        d.get("status","—"), d.get("quality","—"),
                        d.get("rtt","—"), d.get("auth_status","—"),
                        d.get("first_seen","—"), d.get("last_seen","—"),
                        "|".join(str(p) for p in d.get("open_ports",[]))
                    ])
            messagebox.showinfo("تصدير التقرير", f"تم الحفظ:\n{path}")
        except Exception as ex:
            messagebox.showerror("خطأ", str(ex))

    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title("  الإعدادات")
        win.configure(bg=self.CARD)
        win.geometry("420x360")
        win.resizable(False,False)

        rows = [
            ("الفحص التلقائي (دقائق، 0=إيقاف):", "auto_scan_min",  "int"),
            ("مهلة فحص المنافذ (ثواني):",          "port_timeout",   "float"),
            ("عدد خيوط الفحص:",                    "scan_threads",   "int"),
        ]
        vars_ = {}
        for i,(label,key,typ) in enumerate(rows):
            tk.Label(win,text=label,bg=self.CARD,fg=self.TEXT,
                     font=("Courier New",9)).grid(row=i,column=0,sticky="w",padx=16,pady=8)
            v = tk.StringVar(value=str(self.cfg[key]))
            vars_[key] = (v, typ)
            tk.Entry(win,textvariable=v,bg=self.CARD2,fg=self.ACCENT,
                     font=("Courier New",10),width=10,relief=tk.FLAT).grid(
                     row=i,column=1,padx=10)

        sound_var = tk.BooleanVar(value=self.cfg["sound_alert"])
        popup_var = tk.BooleanVar(value=self.cfg["popup_alert"])
        tk.Checkbutton(win,text="تنبيه صوتي",variable=sound_var,
                       bg=self.CARD,fg=self.SUCCESS,selectcolor=self.CARD2,
                       font=("Courier New",10),activebackground=self.CARD
                       ).grid(row=3,column=0,sticky="w",padx=16,pady=8)
        tk.Checkbutton(win,text="نافذة منبثقة للتنبيه",variable=popup_var,
                       bg=self.CARD,fg=self.SUCCESS,selectcolor=self.CARD2,
                       font=("Courier New",10),activebackground=self.CARD
                       ).grid(row=4,column=0,sticky="w",padx=16)

        def apply():
            for key,(v,typ) in vars_.items():
                try:
                    self.cfg[key] = int(v.get()) if typ=="int" else float(v.get())
                except Exception: pass
            self.cfg["sound_alert"] = sound_var.get()
            self.cfg["popup_alert"] = popup_var.get()
            self.alert_sys.sound = sound_var.get()
            self.alert_sys.popup = popup_var.get()
            save_config(self.cfg)
            if self._auto_timer: self.after_cancel(self._auto_timer)
            self._schedule_auto_scan()
            self._log("⚙  تم حفظ الإعدادات", "info")
            win.destroy()

        self._mkbtn(win,"✓ حفظ الإعدادات",self.SUCCESS,apply).grid(
            row=5,column=0,columnspan=2,pady=20)

    def _set_status(self, msg):
        self.after(0, lambda: self.status.config(text=f"  {msg}"))

    def _on_close(self):
        self._stop_event.set()
        if self._auto_timer:
            self.after_cancel(self._auto_timer)
        save_config(self.cfg)
        self.destroy()


def launch_as_module(parent=None):
    """استدعاء من داخل AL.RE.CC"""
    win = NetworkAdminApp.__new__(NetworkAdminApp)
    tk.Toplevel.__init__(win, parent)
    NetworkAdminApp.__init__(win)
    return win


if __name__ == "__main__":
    app = NetworkAdminApp()
    app.mainloop()