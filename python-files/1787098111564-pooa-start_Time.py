# -*- coding: utf-8 -*-
"""
start_Time v1
----------------
نسخه جدید پایش ساعت بازار:

- ابعاد پنجره مشابه نسخه پایش قبلی
- دریافت ساعت بازار از TSETMC StaticData/GetTime
- نمایش مستقیم ساعت دریافت‌شده از API
- Poll قابل تنظیم با حداقل 1ms
- هدف پیش‌فرض: 08:44:59
- Delay قابل تنظیم
- تنظیم ساعت شروع عملیات
- فیلد نام نماد + بررسی از TSETMC و تیک سبز
- فیلد حجم و قیمت برای نگهداری پارامترهای سفارش
- دکمه باز کردن صفحه ورود مفید
- نام کاربری قابل ذخیره در فایل تنظیمات
- رمز عبور در این نسخه به‌صورت محلی/شفاف ذخیره نمی‌شود
- این نسخه عمداً سفارش را خودکار ارسال نمی‌کند؛ برای جلوگیری از ارسال
  ناخواسته سفارش واقعی، ورود و تأیید سفارش در مرورگر دستی است.

نکته:
StaticData/GetTime یک endpoint عمومی TSETMC است و ممکن است فرمت پاسخ آن
تغییر کند؛ تابع extract_market_time چند قالب رایج را پشتیبانی می‌کند.
"""

import ctypes
from ctypes import wintypes
import json
import threading
import time
import urllib.parse
import urllib.request
import http.client
import webbrowser
import tkinter as tk
import pyautogui
import pyperclip
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

# ---------------- Settings ----------------

API_BASE = "https://cdn.tsetmc.com"
TIME_URL = API_BASE + "/api/StaticData/GetTime"
SEARCH_URL = API_BASE + "/api/Instrument/GetInstrumentSearch/{query}"
CLOSING_INFO_URL = API_BASE + "/api/ClosingPrice/GetClosingPriceInfo/{inscode}"

DEFAULT_POLL_MS = 50
MIN_POLL_MS = 1
DEFAULT_DELAY_MS = 800
DEFAULT_TARGET = "08:44:59"

EASYTRADER_URL = "https://easytrader.emofid.com/"

LOGIN_URL = (
    "https://login.emofid.com/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback"
    "%3Fclient_id%3Deasy_pkce%26redirect_uri%3Dhttps%253A%252F%252Fm.easytrader.ir"
    "%252Fauth-callback%26response_type%3Dcode%26scope%3Deasy2_api%2520mts_api"
    "%2520openid%2520profile%2520login_delegation-api"
)

CONFIG_PATH = Path.home() / "PayeshClock_config.json"
HTTP_TIMEOUT = 2.5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# ---------------- HTTP ----------------

_http_local = threading.local()
_TIME_HOST = urllib.parse.urlsplit(API_BASE).netloc


def _get_http_connection():
    conn = getattr(_http_local, "conn", None)
    if conn is None:
        conn = http.client.HTTPSConnection(_TIME_HOST, timeout=HTTP_TIMEOUT)
        _http_local.conn = conn
    return conn


def http_get_json(url):
    parts = urllib.parse.urlsplit(url)
    query = parts.query
    cache = f"_payesh_ts={time.time_ns()}"
    query = f"{query}&{cache}" if query else cache
    path = parts.path + ("?" + query if query else "")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Connection": "keep-alive",
    }

    started = time.perf_counter()
    conn = _get_http_connection()

    try:
        conn.request("GET", path, headers=headers)
        with conn.getresponse() as response:
            raw = response.read()
            status = response.status
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        conn = http.client.HTTPSConnection(_TIME_HOST, timeout=HTTP_TIMEOUT)
        _http_local.conn = conn
        conn.request("GET", path, headers=headers)
        with conn.getresponse() as response:
            raw = response.read()
            status = response.status

    rtt_ms = (time.perf_counter() - started) * 1000.0

    if not (200 <= status < 300):
        raise RuntimeError(f"HTTP {status}")

    data = json.loads(raw.decode("utf-8-sig", errors="replace"))
    _http_local.last_rtt_ms = rtt_ms
    return data


# ---------------- TSETMC time parsing ----------------

def _walk_values(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k), v
            yield from _walk_values(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_values(item)


def _format_time_candidate(value):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        s = str(int(value))
    else:
        s = str(value).strip()

    # HHMMSS
    if s.isdigit() and len(s) in (5, 6):
        s = s.zfill(6)
        hh, mm, ss = s[:2], s[2:4], s[4:6]
        if int(hh) < 24 and int(mm) < 60 and int(ss) < 60:
            return f"{hh}:{mm}:{ss}"

    # HH:MM:SS or ISO datetime
    if "T" in s:
        s = s.split("T", 1)[1]
    if "." in s:
        s = s.split(".", 1)[0]
    if "+" in s:
        s = s.split("+", 1)[0]
    if len(s) >= 8 and s[2] == ":" and s[5] == ":":
        t = s[:8]
        try:
            hh, mm, ss = map(int, t.split(":"))
            if hh < 24 and mm < 60 and ss < 60:
                return t
        except Exception:
            pass

    return None


def extract_market_time(data):
    """
    Tolerant parser for GetTime responses.
    It prefers keys that look like time/time fields.
    """
    preferred_keys = {
        "time", "Time", "hEven", "HEven", "marketTime",
        "markettime", "currentTime", "serverTime", "ServerTime"
    }

    candidates = []
    for key, value in _walk_values(data):
        if key in preferred_keys or "time" in key.lower() or key.lower() == "heven":
            t = _format_time_candidate(value)
            if t:
                candidates.append(t)

    if candidates:
        return candidates[0]

    # Last fallback: scan all scalar values.
    for _, value in _walk_values(data):
        t = _format_time_candidate(value)
        if t:
            return t

    raise ValueError(f"فرمت ساعت API ناشناخته است: {data}")


def get_market_time():
    data = http_get_json(TIME_URL)
    return extract_market_time(data)


# ---------------- Symbol validation ----------------

def get_price_limits(inscode):
    data = http_get_json(CLOSING_INFO_URL.format(inscode=inscode))
    info = data.get("closingPriceInfo", data)
    pmin = info.get("priceMin")
    pmax = info.get("priceMax")
    if pmin is None or pmax is None:
        raise ValueError(f"حداقل/حداکثر قیمت برای InsCode={inscode} در پاسخ API پیدا نشد.")
    return float(pmin), float(pmax)


def search_symbol(symbol):
    q = urllib.parse.quote(symbol.strip(), safe="")
    data = http_get_json(SEARCH_URL.format(query=q))
    rows = data.get("instrumentSearch", [])
    if not isinstance(rows, list):
        rows = []

    exact = [
        row for row in rows
        if str(row.get("lVal18AFC", "")).strip() == symbol.strip()
    ]
    rows = exact if exact else rows

    if not rows:
        raise ValueError(f"نماد «{symbol}» پیدا نشد")

    row = rows[0]
    inscode = str(row.get("insCode", "")).strip()
    display = str(row.get("lVal18AFC") or row.get("lVal30") or symbol).strip()

    if not inscode:
        raise ValueError(f"InsCode برای «{symbol}» پیدا نشد")

    return inscode, display


# ---------------- Config ----------------

def load_config():
    try:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_config(username):
    data = {"username": username}
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------- GUI ----------------

class PayeshClockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("start_Time")
        self.root.geometry("1180x760")
        self.root.minsize(1050, 700)
        self.root.configure(bg="#07101d")

        self.running = False
        self.stop_event = threading.Event()
        self.last_market_time = None
        self.triggered_today = False
        self.last_rtt = None
        self.symbol_ok = False
        self.volume_pos = None
        self.price_pos = None
        self.submit_pos = None

        self.cfg = load_config()

        self.username_var = tk.StringVar(value=self.cfg.get("username", ""))
        self.password_var = tk.StringVar()
        self.symbol_var = tk.StringVar()
        self.volume_var = tk.StringVar()
        self.price_var = tk.StringVar()

        self.poll_var = tk.StringVar(value=str(DEFAULT_POLL_MS))
        self.delay_var = tk.StringVar(value=str(DEFAULT_DELAY_MS))
        self.target_var = tk.StringVar(value=DEFAULT_TARGET)

        self.market_clock_var = tk.StringVar(value="--:--:--")
        self.rtt_var = tk.StringVar(value="RTT: ---")
        self.status_var = tk.StringVar(value="● متوقف")
        self.symbol_status_var = tk.StringVar(value="—")
        self.price_limits_var = tk.StringVar(value="حد مجاز قیمت: ---")
        self.volume_pos_var = tk.StringVar(value="حجم: ثبت نشده")
        self.price_pos_var = tk.StringVar(value="قیمت: ثبت نشده")
        self.submit_pos_var = tk.StringVar(value="ثبت سفارش: ثبت نشده")
        self.click_count_var = tk.StringVar(value="1")
        self.trigger_status_var = tk.StringVar(value="هدف: " + DEFAULT_TARGET)

        self.build_ui()

    def build_ui(self):
        # Dashboard inspired by the supplied reference image:
        # dark navy background, blue section headers, green live clock,
        # compact order/timing panels, coordinate cards and an event log.
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#07101d")
        style.configure(
            "TLabelframe",
            background="#07101d",
            bordercolor="#1c3555",
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background="#07101d",
            foreground="#5aa7ff",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "TLabel",
            background="#07101d",
            foreground="#d9e5f5",
            font=("Segoe UI", 9),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 6),
        )
        style.configure(
            "TEntry",
            fieldbackground="#101b2a",
            foreground="#ffffff",
            insertcolor="#ffffff",
            bordercolor="#2a4568",
            padding=5,
        )

        main = tk.Frame(self.root, bg="#07101d")
        main.pack(fill="both", expand=True, padx=12, pady=10)

        # Header
        header = tk.Frame(main, bg="#0b1727", height=48)
        header.pack(fill="x", pady=(0, 8))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="start_Time",
            bg="#0b1727",
            fg="#ffffff",
            font=("Segoe UI", 15, "bold"),
        ).pack(side="right", padx=16)

        tk.Label(
            header,
            textvariable=self.status_var,
            bg="#0b1727",
            fg="#39e75f",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=16)

        # Three-column body
        body = tk.Frame(main, bg="#07101d")
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg="#07101d", width=350)
        center = tk.Frame(body, bg="#07101d", width=410)
        right = tk.Frame(body, bg="#07101d", width=350)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        center.pack(side="left", fill="both", expand=True, padx=5)
        right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        def box(parent, title):
            f = ttk.LabelFrame(parent, text=title, padding=9)
            f.pack(fill="x", pady=(0, 8))
            return f

        # Left: login
        b = box(left, "اتصال و ورود")
        ttk.Label(b, text="نام کاربری").grid(row=0, column=0, sticky="e", pady=4)
        ttk.Entry(b, textvariable=self.username_var, width=23).grid(row=0, column=1, pady=4, padx=5)
        ttk.Label(b, text="رمز عبور").grid(row=1, column=0, sticky="e", pady=4)
        ttk.Entry(b, textvariable=self.password_var, show="•", width=23).grid(row=1, column=1, pady=4, padx=5)
        ttk.Button(b, text="باز کردن صفحه ورود مفید", command=self.open_login).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=6
        )
        ttk.Button(b, text="ذخیره نام کاربری", command=self.save_username).grid(
            row=3, column=0, columnspan=2, sticky="ew"
        )

        # Left: symbol and price limits
        b = box(left, "نماد و اطلاعات قیمت")
        ttk.Label(b, text="نام نماد").grid(row=0, column=0, sticky="e", pady=4)
        ttk.Entry(b, textvariable=self.symbol_var, width=20).grid(row=0, column=1, pady=4, padx=4)
        ttk.Button(b, text="بررسی نماد ✓", command=self.validate_symbol).grid(
            row=0, column=2, pady=4
        )
        ttk.Label(b, textvariable=self.symbol_status_var).grid(
            row=1, column=0, columnspan=3, pady=4
        )
        tk.Label(
            b, text="حد مجاز قیمت امروز",
            bg="#07101d", fg="#7f9ab8",
            font=("Segoe UI", 9, "bold")
        ).grid(row=2, column=0, columnspan=3, pady=(8, 2))
        tk.Label(
            b, textvariable=self.price_limits_var,
            bg="#07101d", fg="#39e75f",
            font=("Segoe UI", 11, "bold")
        ).grid(row=3, column=0, columnspan=3, pady=(0, 5))

        # Left: order values
        b = box(left, "مشخصات سفارش")
        ttk.Label(b, text="حجم").grid(row=0, column=0, sticky="e", pady=5)
        ttk.Entry(b, textvariable=self.volume_var, width=23).grid(row=0, column=1, pady=5, padx=5)
        ttk.Label(b, text="قیمت").grid(row=1, column=0, sticky="e", pady=5)
        ttk.Entry(b, textvariable=self.price_var, width=23).grid(row=1, column=1, pady=5, padx=5)

        # Center: market clock
        clock_box = box(center, "ساعت هسته معاملات")
        self.clock_label = tk.Label(
            clock_box,
            textvariable=self.market_clock_var,
            bg="#07101d",
            fg="#36e83c",
            font=("Consolas", 30, "bold"),
        )
        self.clock_label.pack(pady=(3, 0))
        tk.Label(
            clock_box,
            textvariable=self.rtt_var,
            bg="#07101d",
            fg="#6ea7d9",
            font=("Segoe UI", 9),
        ).pack(pady=(0, 6))

        # Center: timing
        b = box(center, "تنظیمات زمان‌بندی")
        ttk.Label(b, text="ساعت شروع کلیک").grid(row=0, column=0, sticky="e", pady=5)
        ttk.Entry(b, textvariable=self.target_var, width=16).grid(row=0, column=1, pady=5, padx=5)
        ttk.Label(b, text="Delay (ms)").grid(row=1, column=0, sticky="e", pady=5)
        ttk.Entry(b, textvariable=self.delay_var, width=16).grid(row=1, column=1, pady=5, padx=5)
        ttk.Label(b, text="فاصله پایش API (ms)").grid(row=2, column=0, sticky="e", pady=5)
        ttk.Entry(b, textvariable=self.poll_var, width=16).grid(row=2, column=1, pady=5, padx=5)
        ttk.Label(b, textvariable=self.trigger_status_var).grid(
            row=3, column=0, columnspan=2, pady=6
        )

        ttk.Button(b, text="▶ شروع پایش", command=self.start_monitor).grid(
            row=4, column=0, sticky="ew", pady=4
        )
        ttk.Button(b, text="■ توقف", command=self.stop_monitor).grid(
            row=4, column=1, sticky="ew", pady=4
        )

        # Center: order preparation
        b = box(center, "عملیات")
        ttk.Button(
            b, text="ورود حجم و قیمت در EasyTrader",
            command=self.fill_easytrader_order
        ).pack(fill="x", pady=3)
        ttk.Button(
            b, text="آماده‌سازی سفارش",
            command=self.prepare_order
        ).pack(fill="x", pady=3)

        tk.Label(
            b,
            text="ارسال نهایی سفارش در این نسخه دستی است.",
            bg="#07101d",
            fg="#f2c94c",
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=6)

        # Right: coordinate cards
        b = box(right, "مختصات صفحه EasyTrader")
        self._coord_row(b, 0, "نقطه حجم", self.volume_pos_var, "volume")
        self._coord_row(b, 1, "نقطه قیمت", self.price_pos_var, "price")
        self._coord_row(b, 2, "نقطه ثبت سفارش", self.submit_pos_var, "submit")

        ttk.Label(b, text="تعداد کلیک").grid(row=3, column=0, sticky="e", pady=8)
        ttk.Entry(b, textvariable=self.click_count_var, width=8).grid(
            row=3, column=1, pady=8, padx=4
        )

        # Registration buttons
        ttk.Button(
            b, text="ثبت نقطه حجم",
            command=lambda: self.register_position("volume")
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Button(
            b, text="ثبت نقطه قیمت",
            command=lambda: self.register_position("price")
        ).grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Button(
            b, text="ثبت نقطه ثبت سفارش",
            command=lambda: self.register_position("submit")
        ).grid(row=6, column=0, columnspan=2, sticky="ew", pady=2)

        # Right: final sequence controls
        b = box(right, "توالی آماده‌سازی")
        ttk.Button(
            b, text="ورود حجم/قیمت",
            command=self.fill_easytrader_order
        ).pack(fill="x", pady=3)
        ttk.Label(
            b,
            text="نقطه ثبت سفارش فقط ذخیره می‌شود و کلیک خودکار ندارد.",
            wraplength=280,
            justify="right",
        ).pack(fill="x", pady=7)

        # Full-width log
        log_box = ttk.LabelFrame(main, text="لاگ رویدادها", padding=6)
        log_box.pack(fill="both", expand=True, pady=(8, 0))

        self.log = tk.Text(
            log_box,
            height=8,
            bg="#050b14",
            fg="#d9e5f5",
            insertbackground="#ffffff",
            relief="flat",
            font=("Consolas", 9),
        )
        self.log.pack(fill="both", expand=True)

        # Footer
        footer = tk.Frame(main, bg="#0b1727", height=28)
        footer.pack(fill="x", pady=(8, 0))
        footer.pack_propagate(False)
        tk.Label(
            footer,
            text="TSETMC API  •  EasyTrader preparation  •  RTT",
            bg="#0b1727",
            fg="#6ea7d9",
            font=("Segoe UI", 8),
        ).pack(side="left", padx=10)
        tk.Label(
            footer,
            text="● آماده",
            bg="#0b1727",
            fg="#39e75f",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="right", padx=10)

        self.write_log("نسخه نهایی آماده است — طراحی بر اساس تصویر مرجع ساخته شد.")

    def _coord_row(self, parent, row, title, variable, field_name):
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="e", pady=6)
        ttk.Label(parent, textvariable=variable).grid(row=row, column=1, sticky="w", pady=6)
        ttk.Button(
            parent,
            text="ثبت",
            command=lambda n=field_name: self.register_position(n)
        ).grid(row=row, column=2, padx=4)

    # ---------- UI helpers ----------

    def write_log(self, text):
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log.config(state="normal")
        self.log.insert("end", f"[{now}] {text}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def open_login(self):
        webbrowser.open(LOGIN_URL)
        self.write_log("صفحه ورود مفید در مرورگر باز شد.")
        self.write_log("ورود به حساب و تأیید سفارش در مرورگر به‌صورت دستی انجام می‌شود.")

    def save_username(self):
        try:
            save_config(self.username_var.get().strip())
            self.write_log("نام کاربری ذخیره شد.")
        except Exception as exc:
            messagebox.showerror("خطا", f"ذخیره تنظیمات انجام نشد:\n{exc}")

    # ---------- Symbol ----------

    def validate_symbol(self):
        symbol = self.symbol_var.get().strip()
        if not symbol:
            self.symbol_status_var.set("✗")
            self.symbol_ok = False
            return

        self.symbol_status_var.set("در حال بررسی...")
        threading.Thread(
            target=self._validate_symbol_worker,
            args=(symbol,),
            daemon=True
        ).start()

    def _validate_symbol_worker(self, symbol):
        try:
            inscode, display = search_symbol(symbol)
            pmin, pmax = get_price_limits(inscode)
            self.root.after(
                0,
                lambda: self._symbol_result(True, display, inscode, pmin, pmax)
            )
        except Exception as exc:
            self.root.after(
                0,
                lambda e=str(exc): self._symbol_result(False, e, "", None, None)
            )

    def _symbol_result(self, ok, text, inscode, pmin=None, pmax=None):
        self.symbol_ok = ok
        if ok:
            self.symbol_status_var.set(f"✓ {text}")
            self.price_limits_var.set(
                f"حد مجاز قیمت امروز: {pmin:,.0f}  تا  {pmax:,.0f}"
            )
            self.write_log(
                f"نماد معتبر است: {text} | InsCode={inscode} | "
                f"حد قیمت={pmin:,.0f}..{pmax:,.0f}"
            )
        else:
            self.symbol_status_var.set("✗")
            self.price_limits_var.set("حد مجاز قیمت: ---")
            self.write_log(f"خطای نماد: {text}")

    # ---------- Order preparation (no submission) ----------

    def prepare_order(self):
        symbol = self.symbol_var.get().strip()
        volume = self.volume_var.get().strip()
        price = self.price_var.get().strip()

        if not symbol:
            messagebox.showwarning("سفارش", "نام نماد وارد نشده است.")
            return
        if not self.symbol_ok:
            messagebox.showwarning("سفارش", "ابتدا نماد را بررسی کن تا تیک سبز بگیرد.")
            return
        if not volume.isdigit() or int(volume) <= 0:
            messagebox.showwarning("سفارش", "حجم معتبر وارد کن.")
            return
        try:
            price_value = float(price.replace(",", ""))
            if price_value <= 0:
                raise ValueError
        except Exception:
            messagebox.showwarning("سفارش", "قیمت معتبر وارد کن.")
            return

        # Refresh today's limits before accepting the price.
        try:
            inscode, _ = search_symbol(symbol)
            pmin, pmax = get_price_limits(inscode)
            if not (pmin <= price_value <= pmax):
                messagebox.showwarning(
                    "سفارش",
                    f"قیمت واردشده خارج از محدوده مجاز امروز است.\n"
                    f"حداقل: {pmin:,.0f}\nحداکثر: {pmax:,.0f}"
                )
                self.price_limits_var.set(
                    f"حد مجاز قیمت امروز: {pmin:,.0f}  تا  {pmax:,.0f}"
                )
                return
            self.price_limits_var.set(
                f"حد مجاز قیمت امروز: {pmin:,.0f}  تا  {pmax:,.0f}"
            )
        except Exception as exc:
            self.write_log(f"دریافت حدود قیمت ناموفق بود: {exc}")
            messagebox.showwarning(
                "سفارش",
                "حدود قیمت نماد از API دریافت نشد؛ سفارش آماده نمی‌شود."
            )
            return

        # This deliberately opens the trading site only. It does not
        # authenticate, fill, click, or submit a real order.
        webbrowser.open(EASYTRADER_URL)
        self.write_log(
            f"صفحه EasyTrader برای آماده‌سازی سفارش باز شد | "
            f"نماد={symbol} | حجم={volume} | قیمت={price}"
        )
        self.write_log(
            "ارسال سفارش خودکار غیرفعال است؛ اطلاعات فقط برای آماده‌سازی ثبت شدند."
        )

    # ---------- EasyTrader field filling (no submit) ----------

    def register_position(self, field_name):
        """
        Move the mouse to the desired EasyTrader field and press Enter.
        The current screen coordinates are saved locally.
        """
        self.write_log(
            f"ثبت نقطه «{field_name}»: موس را روی محل موردنظر ببر و Enter بزن."
        )
        threading.Thread(
            target=self._wait_for_enter_position,
            args=(field_name,),
            daemon=True
        ).start()

    def _wait_for_enter_position(self, field_name):
        # Give the user a short window to move the mouse to the browser field.
        time.sleep(1.0)
        self.root.after(
            0,
            lambda: self.write_log(
                f"ثبت نقطه «{field_name}» فعال شد؛ اکنون Enter را فشار بده."
            )
        )

        # Use a simple polling loop for the Enter key without blocking Tk.
        # pyautogui can read the keyboard state when available.
        while True:
            if pyautogui.press.__name__:  # keep pyautogui loaded
                # A lightweight Windows GetAsyncKeyState check avoids
                # requiring a keyboard-hook package.
                state = ctypes.windll.user32.GetAsyncKeyState(0x0D)
                if state & 0x8000:
                    pos = pyautogui.position()
                    if field_name == "volume":
                        self.volume_pos = (pos.x, pos.y)
                        self.root.after(
                            0,
                            lambda p=self.volume_pos:
                            self.volume_pos_var.set(f"حجم: {p[0]},{p[1]}")
                        )
                    elif field_name == "price":
                        self.price_pos = (pos.x, pos.y)
                        self.root.after(
                            0,
                            lambda p=self.price_pos:
                            self.price_pos_var.set(f"قیمت: {p[0]},{p[1]}")
                        )
                    else:
                        self.submit_pos = (pos.x, pos.y)
                        self.root.after(
                            0,
                            lambda p=self.submit_pos:
                            self.submit_pos_var.set(f"ثبت سفارش: {p[0]},{p[1]}")
                        )

                    self.root.after(
                        0,
                        lambda n=field_name, p=pos:
                        self.write_log(
                            f"نقطه «{n}» ثبت شد: ({p.x},{p.y})"
                        )
                    )
                    return
            time.sleep(0.02)

    def _paste_text_at(self, pos, value):
        pyautogui.click(pos[0], pos[1])
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.03)
        pyperclip.copy(str(value))
        pyautogui.hotkey("ctrl", "v")

    def fill_easytrader_order(self):
        """
        Fill ONLY volume and price in the two previously registered
        EasyTrader coordinates. It never clicks the buy/submit button.
        """
        if self.volume_pos is None or self.price_pos is None:
            messagebox.showwarning(
                "ورود سفارش",
                "ابتدا نقطه فیلد حجم و فیلد قیمت را ثبت کن."
            )
            return

        symbol = self.symbol_var.get().strip()
        volume = self.volume_var.get().strip()
        price = self.price_var.get().strip()

        if not self.symbol_ok:
            messagebox.showwarning("ورود سفارش", "ابتدا نماد را تأیید کن.")
            return
        if not volume.isdigit() or int(volume) <= 0:
            messagebox.showwarning("ورود سفارش", "حجم معتبر وارد کن.")
            return
        if not price:
            messagebox.showwarning("ورود سفارش", "قیمت را وارد کن.")
            return

        # Recheck price range before filling the order fields.
        try:
            inscode, _ = search_symbol(symbol)
            pmin, pmax = get_price_limits(inscode)
            p = float(price.replace(",", ""))
            if not (pmin <= p <= pmax):
                messagebox.showwarning(
                    "ورود سفارش",
                    f"قیمت خارج از محدوده مجاز است.\n"
                    f"حداقل: {pmin:,.0f}\nحداکثر: {pmax:,.0f}"
                )
                return
        except Exception as exc:
            messagebox.showwarning(
                "ورود سفارش",
                f"بررسی حدود قیمت انجام نشد:\n{exc}"
            )
            return

        self.write_log(
            f"در حال ورود حجم={volume} و قیمت={price} در EasyTrader..."
        )

        try:
            self._paste_text_at(self.volume_pos, volume)
            time.sleep(0.08)
            self._paste_text_at(self.price_pos, price)
            self.write_log(
                "حجم و قیمت در فیلدهای ثبت‌شده EasyTrader وارد شدند. "
                "دکمه خرید/ارسال به‌هیچ‌وجه کلیک نشد."
            )
        except Exception as exc:
            self.write_log(f"خطا در ورود حجم/قیمت: {exc}")
            messagebox.showerror("خطا", f"ورود اطلاعات انجام نشد:\n{exc}")

    # ---------- Monitor ----------

    def start_monitor(self):
        if self.running:
            return

        try:
            poll_ms = max(MIN_POLL_MS, int(float(self.poll_var.get())))
            delay_ms = max(0, int(float(self.delay_var.get())))
            target = self.target_var.get().strip()

            datetime.strptime(target, "%H:%M:%S")

            self.poll_var.set(str(poll_ms))
            self.delay_var.set(str(delay_ms))
        except Exception:
            messagebox.showerror(
                "خطا",
                "فاصله API، Delay یا ساعت هدف معتبر نیست."
            )
            return

        self.running = True
        self.stop_event.clear()
        self.triggered_today = False
        self.status_var.set("🟡 پایش فعال")
        self.write_log(
            f"پایش ساعت شروع شد | Poll={poll_ms}ms | هدف={target} | Delay={delay_ms}ms"
        )

        threading.Thread(
            target=self.monitor_clock,
            args=(poll_ms, target, delay_ms),
            daemon=True
        ).start()

    def stop_monitor(self):
        self.running = False
        self.stop_event.set()
        self.status_var.set("● متوقف")
        self.write_log("پایش ساعت متوقف شد.")

    def monitor_clock(self, poll_ms, target, delay_ms):
        while self.running and not self.stop_event.is_set():
            try:
                market_time = get_market_time()
                self.last_market_time = market_time
                self.last_rtt = getattr(_http_local, "last_rtt_ms", None)

                rtt = self.last_rtt
                self.root.after(
                    0,
                    lambda t=market_time, r=rtt:
                    self.update_clock_ui(t, r)
                )

                if market_time == target and not self.triggered_today:
                    self.triggered_today = True
                    detected = time.perf_counter()

                    self.root.after(
                        0,
                        lambda t=market_time:
                        self.write_log(
                            f"ساعت هدف {t} از API دیده شد؛ پایش متوقف شد."
                        )
                    )

                    # The clock monitor stops after the target is seen.
                    self.running = False
                    self.monitor_stop_only()

                    # Safe version: prepare/log the timing point but do not
                    # submit/click a real brokerage order automatically.
                    threading.Thread(
                        target=self.target_reached,
                        args=(detected, delay_ms),
                        daemon=True
                    ).start()

                    return

            except Exception as exc:
                self.root.after(
                    0,
                    lambda e=str(exc):
                    self.write_log(f"خطای API ساعت: {e}")
                )

            # Do not busy-spin. The user can set 1ms, but actual network RTT
            # determines the achievable request rate.
            wait_s = poll_ms / 1000.0
            if self.stop_event.wait(wait_s):
                return

    def monitor_stop_only(self):
        self.root.after(
            0,
            lambda: self.status_var.set("🟢 هدف دیده شد")
        )

    def update_clock_ui(self, market_time, rtt):
        self.market_clock_var.set(market_time)
        if rtt is None:
            self.rtt_var.set("RTT: ---")
        else:
            self.rtt_var.set(f"RTT: {rtt:.1f}ms")
        self.trigger_status_var.set(
            f"هدف: {self.target_var.get().strip()} | API: {market_time}"
        )

    def target_reached(self, detected_perf, delay_ms):
        # Delay is measured locally and logged for diagnostics.
        time.sleep(delay_ms / 1000.0)
        actual = (time.perf_counter() - detected_perf) * 1000.0

        self.root.after(
            0,
            lambda: self.write_log(
                f"Delay تمام شد | زمان واقعی از تشخیص ≈ {actual:.1f}ms"
            )
        )

        symbol = self.symbol_var.get().strip()
        volume = self.volume_var.get().strip()
        price = self.price_var.get().strip()

        self.root.after(
            0,
            lambda: self.write_log(
                f"زمان هدف آماده شد | نماد={symbol or '---'} | حجم={volume or '---'} | قیمت={price or '---'}"
            )
        )

        # Open the trading page for manual review/entry.
        self.root.after(0, lambda: webbrowser.open(EASYTRADER_URL))
        self.root.after(
            0,
            lambda: self.write_log(
                "صفحه EasyTrader باز شد؛ بررسی و ارسال نهایی سفارش دستی است."
            )
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = PayeshClockApp(root)
    root.mainloop()
