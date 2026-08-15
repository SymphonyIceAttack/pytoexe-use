# -*- coding: utf-8 -*-
"""
bazgoshai FINAL
--------------------------------
هدف:
- پایش فقط 1 یا 2 نماد که کاربر وارد می‌کند.
- پیدا کردن InsCode از روی نام نماد.
- بررسی API همان نمادها با فاصله پیش‌فرض 50ms.
- تشخیص فقط این تغییر:
      ممنوع-متوقف (IS) -> ممنوع-محفوظ (IR)
- بعد از Delay قابل تنظیم، شروع کلیک.
- تعداد کلیک و فاصله بین کلیک‌ها قابل تنظیم.
- ثبت مختصات کلیک با F2 (کلید سراسری ویندوز).
- بدون لاگین به کارگزاری.

ویندوز:
- Python 3.10+ پیشنهاد می‌شود.
- Tkinter معمولاً همراه Python ویندوز نصب است.
- برای اجرای کلیک و F2 هیچ پکیج خارجی لازم نیست؛ از WinAPI استفاده شده.
"""

import ctypes
from ctypes import wintypes
import json
import threading
import time
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


# ---------------------- Settings ----------------------

API_BASE = "https://cdn.tsetmc.com"
SEARCH_URL = API_BASE + "/api/Instrument/GetInstrumentSearch/{query}"
STATUS_URL = API_BASE + "/api/ClosingPrice/GetClosingPriceInfo/{inscode}"

DEFAULT_POLL_MS = 50
DEFAULT_DELAY_MS = 800
DEFAULT_CLICKS = 1
DEFAULT_CLICK_INTERVAL_MS = 100

HTTP_TIMEOUT = 2.5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# TSETMC status codes:
# IS = ممنوع-متوقف
# IR = ممنوع-محفوظ
TARGET_FROM = "IS"
TARGET_TO = "IR"


# ---------------------- Windows mouse ----------------------

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

MOD_NOREPEAT = 0x4000
VK_F2 = 0x71
HOTKEY_ID = 1001


def get_mouse_position():
    point = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        raise RuntimeError("GetCursorPos failed")
    return point.x, point.y


def left_click(x, y):
    user32.SetCursorPos(int(x), int(y))
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


# ---------------------- TSETMC API ----------------------

def http_get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,*/*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
        raw = response.read()

    text = raw.decode("utf-8-sig", errors="replace")
    return json.loads(text)


def search_symbol(symbol):
    """Return the best matching instrument from TSETMC search."""
    query = urllib.parse.quote(symbol.strip(), safe="")
    data = http_get_json(SEARCH_URL.format(query=query))

    rows = data.get("instrumentSearch", [])
    if not isinstance(rows, list):
        rows = []

    exact = []
    for row in rows:
        l18 = str(row.get("lVal18AFC", "")).strip()
        if l18 == symbol.strip():
            exact.append(row)

    candidates = exact if exact else rows

    if not candidates:
        raise ValueError(f"نماد «{symbol}» پیدا نشد")

    row = candidates[0]
    inscode = str(row.get("insCode", "")).strip()
    if not inscode:
        raise ValueError(f"InsCode برای «{symbol}» پیدا نشد")

    display_name = str(
        row.get("lVal18AFC") or row.get("lVal30") or symbol
    ).strip()

    return inscode, display_name


def unwrap_status(data):
    """
    ClosingPrice/GetClosingPriceInfo returns an object containing
    instrumentState. cEtaval is the machine status code and
    cEtavalTitle is its Persian title.
    """
    if not isinstance(data, dict):
        raise ValueError("پاسخ API معتبر نیست")

    state = data.get("instrumentState")
    if not isinstance(state, dict):
        # Some wrappers may use a different casing.
        state = data.get("InstrumentState")

    if not isinstance(state, dict):
        raise ValueError("instrumentState در پاسخ API پیدا نشد")

    code = str(state.get("cEtaval", "")).strip()
    title = str(state.get("cEtavalTitle", "")).strip()

    return code, title


def get_status(inscode):
    data = http_get_json(STATUS_URL.format(inscode=urllib.parse.quote(inscode)))
    return unwrap_status(data)


# ---------------------- GUI Application ----------------------

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("payesh-V3")
        self.root.geometry("900x700")
        self.root.minsize(650, 500)
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.root.attributes("-topmost", False)

        self.running = False
        self.stop_event = threading.Event()
        self.click_lock = threading.Lock()

        self.symbols = []
        self.states = {}
        self.symbol_labels = {}
        self.search_ok = [None, None]
        self.search_status_vars = [tk.StringVar(value="●"), tk.StringVar(value="●")]
        self.search_status_labels = []
        self.click_x = None
        self.click_y = None

        self.poll_ms = DEFAULT_POLL_MS
        self.delay_ms = DEFAULT_DELAY_MS
        self.click_count = DEFAULT_CLICKS
        self.click_interval_ms = DEFAULT_CLICK_INTERVAL_MS

        self.build_ui()
        self.register_f2_hotkey()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(50, self.process_hotkey)

    # ---------- UI ----------
    def toggle_always_on_top(self):
        """Keep the Payesh window above other windows when enabled."""
        enabled = bool(self.always_on_top_var.get())
        self.root.attributes("-topmost", enabled)
        if enabled:
            # Briefly lift the window so the change is immediately visible.
            self.root.lift()
            self.root.focus_force()


    def build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer,
            text="TSETMC Status Clicker",
            font=("Segoe UI", 18, "bold"),
        ).pack(pady=(0, 3))

        ttk.Label(
            outer,
            text="پایش فقط نمادهای واردشده و اجرای کلیک پس از IS → IR",
            font=("Segoe UI", 10),
        ).pack(pady=(0, 15))

        # Symbols
        sym_frame = ttk.LabelFrame(outer, text=" نمادها ")
        sym_frame.pack(fill="x", pady=6)

        ttk.Label(sym_frame, text="نماد ۱:").grid(
            row=0, column=0, padx=8, pady=8, sticky="e"
        )
        self.sym1 = ttk.Entry(sym_frame, width=20, justify="center")
        self.sym1.grid(row=0, column=1, padx=8, pady=8)
        ttk.Button(sym_frame, text="جستجو", command=lambda: self.search_button(0)).grid(
            row=0, column=2, padx=5, pady=8
        )
        lab1 = tk.Label(sym_frame, textvariable=self.search_status_vars[0],
                        font=("Segoe UI", 16, "bold"), fg="gray")
        lab1.grid(row=0, column=3, padx=5, pady=8)
        self.search_status_labels.append(lab1)

        ttk.Label(sym_frame, text="نماد ۲ (اختیاری):").grid(
            row=1, column=0, padx=8, pady=8, sticky="e"
        )
        self.sym2 = ttk.Entry(sym_frame, width=20, justify="center")
        self.sym2.grid(row=1, column=1, padx=8, pady=8)
        ttk.Button(sym_frame, text="جستجو", command=lambda: self.search_button(1)).grid(
            row=1, column=2, padx=5, pady=8
        )
        lab2 = tk.Label(sym_frame, textvariable=self.search_status_vars[1],
                        font=("Segoe UI", 16, "bold"), fg="gray")
        lab2.grid(row=1, column=3, padx=5, pady=8)
        self.search_status_labels.append(lab2)

        # Settings
        settings = ttk.LabelFrame(outer, text=" تنظیمات قبل از Start ")
        settings.pack(fill="x", pady=6)

        self.poll_entry = self.make_setting(
            settings, 0, "فاصله پایش API (ms):", DEFAULT_POLL_MS
        )
        self.delay_entry = self.make_setting(
            settings, 1, "تأخیر تشخیص تا کلیک (ms):", DEFAULT_DELAY_MS
        )
        self.count_entry = self.make_setting(
            settings, 2, "تعداد کلیک:", DEFAULT_CLICKS
        )
        self.interval_entry = self.make_setting(
            settings, 3, "فاصله بین کلیک‌ها (ms):", DEFAULT_CLICK_INTERVAL_MS
        )

        # Position
        pos = ttk.LabelFrame(outer, text=" مختصات کلیک ")
        pos.pack(fill="x", pady=6)

        self.pos_var = tk.StringVar(value="مختصات ثبت نشده")
        ttk.Label(
            pos, textvariable=self.pos_var, font=("Consolas", 11)
        ).pack(side="left", padx=12, pady=10)

        ttk.Button(
            pos, text="ثبت موقعیت با F2",
            command=self.capture_position,
        ).pack(side="left", padx=5)

        ttk.Button(
            pos, text="تست کلیک",
            command=self.test_click,
        ).pack(side="left", padx=5)

        # Status
        status_box = ttk.LabelFrame(outer, text=" وضعیت ")
        status_box.pack(fill="x", pady=6)

        self.status1 = tk.StringVar(value="نماد ۱: ---")
        self.status2 = tk.StringVar(value="نماد ۲: ---")

        ttk.Label(
            status_box, textvariable=self.status1, font=("Segoe UI", 11)
        ).pack(anchor="w", padx=12, pady=5)

        ttk.Label(
            status_box, textvariable=self.status2, font=("Segoe UI", 11)
        ).pack(anchor="w", padx=12, pady=5)

        self.main_status = tk.StringVar(value="● آماده")
        ttk.Label(
            status_box,
            textvariable=self.main_status,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(5, 10))

        # Buttons
        btns = ttk.Frame(outer)
        btns.pack(fill="x", pady=10)

        self.start_btn = ttk.Button(
            btns, text="▶ شروع پایش", command=self.start
        )
        self.start_btn.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        self.stop_btn = ttk.Button(
            btns, text="■ توقف پایش", command=self.stop, state="disabled"
        )
        self.stop_btn.grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self.always_on_top_chk = ttk.Checkbutton(
            btns,
            text="☑ همیشه روی صفحه",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
        )
        self.always_on_top_chk.grid(row=0, column=2, padx=6, pady=6, sticky="w")

        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=0)

        # Log
        log_frame = ttk.LabelFrame(outer, text=" گزارش ")
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log = tk.Text(
            log_frame,
            height=12,
            wrap="none",
            font=("Consolas", 9),
        )
        self.log.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log.yview
        )
        scroll.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scroll.set)

        self.write_log("برنامه آماده است. تنظیمات را وارد کنید و START بزنید.")

    def make_setting(self, parent, row, label, default):
        ttk.Label(parent, text=label).grid(
            row=row, column=0, padx=8, pady=5, sticky="e"
        )
        entry = ttk.Entry(parent, width=16, justify="center")
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, padx=8, pady=5, sticky="w")
        return entry

    def write_log(self, text):
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log.insert("end", f"[{stamp}] {text}\n")
        self.log.see("end")

    # ---------- Symbol search ----------
    def search_button(self, index):
        entry = self.sym1 if index == 0 else self.sym2
        name = entry.get().strip()
        if not name:
            self.set_search_result(index, None, "نام نماد را وارد کنید.")
            return

        self.set_search_result(index, None, "در حال جستجو...")
        threading.Thread(
            target=self.search_symbol_worker,
            args=(index, name),
            daemon=True,
        ).start()

    def search_symbol_worker(self, index, name):
        try:
            inscode, display = search_symbol(name)
            self.root.after(0, lambda: self.set_search_result(
                index, True, f"✓ {display} | InsCode: {inscode}"
            ))
            self.root.after(0, lambda: self.write_log(
                f"جستجوی نماد {name}: پیدا شد → {inscode}"
            ))
        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda msg=msg: self.set_search_result(
                index, False, msg
            ))
            self.root.after(0, lambda msg=str(exc), n=name: self.write_log(
                f"جستجوی نماد {n}: خطا/پیدا نشد → {msg}"
            ))

    def set_search_result(self, index, ok, message):
        self.search_ok[index] = ok
        if ok is True:
            self.search_status_vars[index].set("✓")
            self.search_status_labels[index].config(fg="green")
            self.main_status.set("● نماد با موفقیت پیدا شد")
        elif ok is False:
            self.search_status_vars[index].set("✗")
            self.search_status_labels[index].config(fg="red")
            self.main_status.set("● نماد پیدا نشد / خطای اتصال")
            messagebox.showerror("جستجوی نماد", message)
        else:
            self.search_status_vars[index].set("…")
            self.search_status_labels[index].config(fg="orange")

        if message and ok is not None:
            self.write_log(message)

    # ---------- F2 ----------

    def register_f2_hotkey(self):
        # Global F2 hotkey on Windows. Also bind Tk's F2 so the key works
        # reliably while this application has focus.
        try:
            ok = user32.RegisterHotKey(None, HOTKEY_ID, MOD_NOREPEAT, VK_F2)
            if not ok:
                self.write_log("هشدار: F2 سراسری ثبت نشد؛ F2 داخل برنامه فعال است.")
        except Exception as exc:
            self.write_log(f"هشدار ثبت F2 سراسری: {exc}")

        self.root.bind_all("<F2>", self._f2_tk_event)

    def _f2_tk_event(self, event=None):
        self.capture_position()
        return "break"

    def process_hotkey(self):
        msg = wintypes.MSG()
        while user32.PeekMessageW(
            ctypes.byref(msg), None, 0, 0, 1
        ):
            if msg.message == 0x0312 and msg.wParam == HOTKEY_ID:
                self.capture_position()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.root.winfo_exists():
            self.root.after(50, self.process_hotkey)

    def capture_position(self):
        try:
            x, y = get_mouse_position()
            self.click_x = x
            self.click_y = y
            self.pos_var.set(f"X = {x}    Y = {y}")
            self.write_log(f"مختصات کلیک ثبت شد: X={x}, Y={y}")
        except Exception as exc:
            messagebox.showerror("خطا", str(exc))

    def test_click(self):
        if self.click_x is None:
            messagebox.showwarning(
                "مختصات ثبت نشده",
                "ابتدا نشانگر ماوس را روی نقطه موردنظر ببرید و F2 بزنید."
            )
            return

        if self.running:
            messagebox.showwarning(
                "در حال پایش",
                "برای تست کلیک، ابتدا STOP کنید."
            )
            return

        left_click(self.click_x, self.click_y)
        self.write_log(
            f"تست کلیک انجام شد: X={self.click_x}, Y={self.click_y}"
        )

    # ---------- Start / Stop ----------

    def read_settings(self):
        try:
            poll = int(self.poll_entry.get().strip())
            delay = int(self.delay_entry.get().strip())
            count = int(self.count_entry.get().strip())
            interval = int(self.interval_entry.get().strip())
        except ValueError:
            raise ValueError("همه تنظیمات باید عدد صحیح باشند.")

        if poll < 10:
            raise ValueError("فاصله پایش کمتر از 10ms قابل تنظیم نیست.")
        if delay < 0:
            raise ValueError("Delay نمی‌تواند منفی باشد.")
        if count < 1:
            raise ValueError("تعداد کلیک باید حداقل 1 باشد.")
        if interval < 0:
            raise ValueError("فاصله کلیک نمی‌تواند منفی باشد.")

        s1 = self.sym1.get().strip()
        s2 = self.sym2.get().strip()

        if not s1 and not s2:
            raise ValueError("حداقل یک نماد وارد کنید.")

        if s1 and s2 and s1 == s2:
            raise ValueError("دو فیلد نباید یک نماد یکسان داشته باشند.")

        self.poll_ms = poll
        self.delay_ms = delay
        self.click_count = count
        self.click_interval_ms = interval

        names = [s for s in (s1, s2) if s]
        return names

    def start(self):
        if self.running:
            return

        try:
            names = self.read_settings()
        except Exception as exc:
            messagebox.showerror("تنظیمات", str(exc))
            return

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.main_status.set("● در حال شروع پایش...")
        self.write_log("دکمه شروع زده شد؛ در حال اتصال به TSETMC و آماده‌سازی پایش...")
        self.running = True
        self.stop_event.clear()

        threading.Thread(
            target=self.resolve_and_start, args=(names,), daemon=True
        ).start()

    def resolve_and_start(self, names):
        resolved = []

        try:
            for name in names:
                inscode, display = search_symbol(name)
                resolved.append((name, inscode, display))
                self.root.after(
                    0,
                    lambda n=name, i=inscode:
                    self.write_log(f"نماد {n} → InsCode: {i}")
                )

            self.symbols = resolved

            # Initial state is read once before monitoring.
            # This prevents a symbol that is already IR at START
            # from falsely triggering a click.
            for index, (name, inscode, display) in enumerate(resolved):
                code, title = get_status(inscode)
                self.states[inscode] = code
                self.update_symbol_status(index, name, code, title)

                self.root.after(
                    0,
                    lambda n=name, c=code, t=title:
                    self.write_log(f"{n}: وضعیت اولیه = {t or c}")
                )

            self.root.after(
                0,
                lambda: self.main_status.set(
                    f"● پایش فعال | فاصله هدف: {self.poll_ms}ms"
                )
            )
            self.root.after(
                0,
                lambda: self.write_log(
                    "پایش شروع شد؛ فقط IS → IR باعث اجرای کلیک می‌شود."
                )
            )

            # One worker per entered symbol.
            # Each worker only talks to its own InsCode.
            for index, item in enumerate(resolved):
                threading.Thread(
                    target=self.monitor_symbol,
                    args=(index, item),
                    daemon=True
                ).start()

        except Exception as exc:
            msg = str(exc)
            self.root.after(0, lambda msg=msg: self.start_failed(msg))

    def start_failed(self, msg):
        self.running = False
        self.stop_event.set()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.main_status.set("● خطا")
        self.write_log("خطا: " + msg)
        messagebox.showerror("خطا در شروع", msg)

    def stop(self):
        self.running = False
        self.stop_event.set()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.main_status.set("● متوقف")
        self.write_log("پایش متوقف شد.")

    # ---------- Monitoring ----------

    def monitor_symbol(self, index, item):
        name, inscode, display = item
        previous = self.states.get(inscode, "")

        next_time = time.perf_counter()

        while self.running and not self.stop_event.is_set():
            try:
                code, title = get_status(inscode)

                if code != previous:
                    self.root.after(
                        0,
                        lambda i=index, n=name, c=code, t=title:
                        self.update_symbol_status(i, n, c, t)
                    )

                    self.root.after(
                        0,
                        lambda n=name, old=previous, new=code, t=title:
                        self.write_log(
                            f"{n}: تغییر وضعیت {old} → {new} ({t})"
                        )
                    )

                    # Exact trigger: IS -> IR
                    if previous == TARGET_FROM and code == TARGET_TO:
                        detected_perf = time.perf_counter()
                        detected_text = datetime.now().strftime(
                            "%H:%M:%S.%f"
                        )[:-3]

                        self.root.after(
                            0,
                            lambda n=name, ts=detected_text:
                            self.write_log(
                                f"*** {n}: IS → IR در {ts} ***"
                            )
                        )

                        threading.Thread(
                            target=self.delayed_click,
                            args=(name, detected_perf),
                            daemon=True
                        ).start()

                previous = code
                self.states[inscode] = code

            except Exception as exc:
                self.root.after(
                    0,
                    lambda n=name, e=str(exc):
                    self.write_log(f"{n}: خطای API: {e}")
                )

            # Targeted polling interval. If API takes longer, the next
            # request starts immediately after the current one finishes.
            next_time += self.poll_ms / 1000.0
            sleep_for = next_time - time.perf_counter()

            if sleep_for > 0:
                self.stop_event.wait(sleep_for)
            else:
                next_time = time.perf_counter()

    # ---------- Click sequence ----------

    def delayed_click(self, symbol, detected_perf):
        # The user said only one symbol changes at a time. The lock is
        # nevertheless kept so two accidental triggers cannot overlap.
        with self.click_lock:
            delay_s = self.delay_ms / 1000.0

            if self.stop_event.wait(delay_s):
                return

            if self.click_x is None:
                self.root.after(0, lambda: self.write_log(
                    f"{symbol}: تغییر IS → IR تشخیص داده شد، اما مختصات کلیک با F2 ثبت نشده است."
                ))
                return

            click_start_perf = time.perf_counter()
            actual_delay_ms = (click_start_perf - detected_perf) * 1000.0

            self.root.after(
                0,
                lambda: self.write_log(
                    f"{symbol}: شروع کلیک | Delay واقعی ≈ "
                    f"{actual_delay_ms:.1f}ms | تعداد={self.click_count}"
                )
            )

            for i in range(self.click_count):
                if self.stop_event.is_set() or not self.running:
                    return

                left_click(self.click_x, self.click_y)

                self.root.after(
                    0,
                    lambda n=i + 1, total=self.click_count:
                    self.write_log(f"{symbol}: کلیک {n}/{total}")
                )

                if i + 1 < self.click_count:
                    if self.stop_event.wait(
                        self.click_interval_ms / 1000.0
                    ):
                        return

            self.root.after(
                0,
                lambda: self.write_log(f"{symbol}: عملیات کلیک تمام شد.")
            )

    # ---------- UI helpers ----------

    def update_symbol_status(self, index, name, code, title):
        text = f"{name}: {title or code} [{code}]"
        if index == 0:
            self.status1.set(text)
        else:
            self.status2.set(text)

    def close(self):
        self.running = False
        self.stop_event.set()

        try:
            user32.UnregisterHotKey(None, HOTKEY_ID)
        except Exception:
            pass

        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
