import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import urllib.request
from datetime import datetime, timezone, timedelta

# ============================================================
# TSETMC SERVER CLOCK - FINAL
# API: https://cdn.tsetmc.com/api/StaticData/GetTime
# No third-party package is required.
# Python 3.9+
# ============================================================

API_URL = "https://cdn.tsetmc.com/api/StaticData/GetTime"
TIMEOUT = 7
SAMPLES = 7
RESYNC_SECONDS = 5

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))


def parse_time(obj):
    """Parse the known/common forms returned by the TSETMC time endpoint."""
    if isinstance(obj, dict):
        # Some API versions may wrap the value.
        for key in ("time", "Time", "serverTime", "ServerTime",
                    "dateTime", "DateTime", "datetime",
                    "result", "Result", "data", "Data"):
            if key in obj:
                return parse_time(obj[key])
        # If there is exactly one value, try it.
        if len(obj) == 1:
            return parse_time(next(iter(obj.values())))
        raise ValueError("No time field found in JSON response")

    if isinstance(obj, list):
        if len(obj) == 1:
            return parse_time(obj[0])
        raise ValueError("Unexpected JSON list")

    if isinstance(obj, (int, float)):
        x = float(obj)
        if x > 10_000_000_000:
            x /= 1000.0
        return datetime.fromtimestamp(x, tz=timezone.utc)

    s = str(obj).strip().strip('"').strip("'")

    # Numeric Unix timestamp
    try:
        x = float(s)
        if x > 1_000_000_000:
            if x > 10_000_000_000:
                x /= 1000.0
            return datetime.fromtimestamp(x, tz=timezone.utc)
    except ValueError:
        pass

    # ISO 8601
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IRAN_TZ)
        return dt
    except ValueError:
        pass

    # Common textual formats
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S",
        "%H:%M:%S.%f",
        "%H:%M:%S",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.year == 1900:
                now = datetime.now(IRAN_TZ)
                dt = dt.replace(year=now.year, month=now.month, day=now.day)
            return dt.replace(tzinfo=IRAN_TZ)
        except ValueError:
            continue

    raise ValueError("Unsupported TSETMC time format: " + s)


def get_sample():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json,text/plain,*/*",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )

    # perf_counter is monotonic and is therefore suitable for measuring RTT.
    t0 = time.perf_counter()
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read()
    t1 = time.perf_counter()

    rtt = t1 - t0
    text = raw.decode("utf-8-sig", errors="replace").strip()

    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        obj = text

    server_dt = parse_time(obj)

    # Estimate server time at the midpoint of request/response.
    midpoint = t0 + rtt / 2.0
    return server_dt.astimezone(IRAN_TZ), rtt, midpoint


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("TSETMC Server Clock")
        self.root.geometry("720x500")
        self.root.minsize(650, 450)

        self.base_server_time = None
        self.base_perf = None
        self.rtt_ms = None
        self.offset_ms = None
        self.best_rtt_ms = None
        self.samples = 0
        self.busy = False
        self.auto = True

        self.build_ui()
        self.root.after(10, self.draw_clock)
        self.root.after(300, self.sync)

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame, text="ساعت سرور TSETMC",
            font=("Segoe UI", 23, "bold")
        ).pack(pady=(0, 3))

        ttk.Label(
            frame, text="همگام‌سازی مستقیم با API زمان TSETMC",
            font=("Segoe UI", 10)
        ).pack(pady=(0, 15))

        box = ttk.Frame(frame, relief="ridge", borderwidth=2)
        box.pack(fill="x", pady=5)

        self.clock = ttk.Label(
            box, text="--:--:--.---",
            font=("Consolas", 40, "bold"),
            anchor="center"
        )
        self.clock.pack(fill="x", pady=(20, 5))

        self.date = ttk.Label(
            box, text="----/--/--",
            font=("Segoe UI", 11),
            anchor="center"
        )
        self.date.pack(pady=(0, 20))

        info = ttk.Frame(frame)
        info.pack(fill="x", pady=12)

        self.status = tk.StringVar(value="● در حال اتصال...")
        self.rtt = tk.StringVar(value="RTT: --- ms")
        self.offset = tk.StringVar(value="Offset: --- ms")
        self.best = tk.StringVar(value="Best RTT: --- ms")
        self.count = tk.StringVar(value="Samples: 0")

        for row, (name, var) in enumerate([
            ("وضعیت", self.status),
            ("تأخیر رفت‌وبرگشت", self.rtt),
            ("اختلاف تخمینی با ساعت سیستم", self.offset),
            ("بهترین RTT", self.best),
            ("تعداد نمونه", self.count),
        ]):
            ttk.Label(info, text=name + ":", font=("Segoe UI", 10, "bold")).grid(
                row=row, column=0, sticky="w", padx=8, pady=3
            )
            ttk.Label(info, textvariable=var).grid(
                row=row, column=1, sticky="w", padx=8, pady=3
            )

        info.columnconfigure(1, weight=1)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=10)

        self.sync_btn = ttk.Button(
            buttons, text="همگام‌سازی الآن", command=self.sync
        )
        self.sync_btn.pack(side="left", padx=4)

        self.auto_btn = ttk.Button(
            buttons, text="توقف همگام‌سازی خودکار",
            command=self.toggle_auto
        )
        self.auto_btn.pack(side="left", padx=4)

        ttk.Button(
            buttons, text="خروج", command=self.root.destroy
        ).pack(side="right", padx=4)

        ttk.Label(
            frame,
            text="نمایش تا میلی‌ثانیه است؛ دقت واقعی به RTT و نوسان شبکه وابسته است.",
            font=("Segoe UI", 9)
        ).pack(pady=8)

    def toggle_auto(self):
        self.auto = not self.auto
        self.auto_btn.config(
            text="توقف همگام‌سازی خودکار" if self.auto
            else "فعال‌کردن همگام‌سازی خودکار"
        )
        if self.auto and not self.busy:
            self.sync()

    def sync(self):
        if self.busy:
            return

        self.busy = True
        self.sync_btn.config(state="disabled")
        self.status.set("● در حال دریافت زمان از TSETMC...")

        threading.Thread(target=self.sync_worker, daemon=True).start()

    def sync_worker(self):
        results = []
        errors = []

        for _ in range(SAMPLES):
            try:
                results.append(get_sample())
            except Exception as exc:
                errors.append(str(exc))

        if results:
            # Lowest RTT is normally the cleanest sample.
            server_dt, rtt, midpoint_perf = min(results, key=lambda x: x[1])

            # Estimate local wall-clock time at the same monotonic midpoint.
            now_perf = time.perf_counter()
            local_now = datetime.now(IRAN_TZ)
            local_mid = local_now - timedelta(seconds=now_perf - midpoint_perf)

            offset_ms = (server_dt - local_mid).total_seconds() * 1000.0

            self.root.after(
                0, lambda: self.sync_ok(
                    server_dt, rtt * 1000, offset_ms, len(results)
                )
            )
        else:
            msg = errors[-1] if errors else "پاسخ معتبر دریافت نشد."
            self.root.after(0, lambda: self.sync_error(msg))

    def sync_ok(self, server_dt, rtt_ms, offset_ms, n):
        self.base_server_time = server_dt
        self.base_perf = time.perf_counter()
        self.rtt_ms = rtt_ms
        self.offset_ms = offset_ms
        self.samples += n
        self.best_rtt_ms = (
            rtt_ms if self.best_rtt_ms is None
            else min(self.best_rtt_ms, rtt_ms)
        )

        self.rtt.set(f"RTT: {rtt_ms:.2f} ms")
        self.offset.set(f"Offset: {offset_ms:+.2f} ms")
        self.best.set(f"Best RTT: {self.best_rtt_ms:.2f} ms")
        self.count.set(f"Samples: {self.samples}")
        self.status.set("● متصل و همگام")
        self.busy = False
        self.sync_btn.config(state="normal")

        if self.auto:
            self.root.after(RESYNC_SECONDS * 1000, self.sync)

    def sync_error(self, msg):
        self.status.set("● خطا: " + msg[:90])
        self.busy = False
        self.sync_btn.config(state="normal")

        if self.auto:
            self.root.after(RESYNC_SECONDS * 1000, self.sync)

    def draw_clock(self):
        if self.base_server_time is not None:
            elapsed = time.perf_counter() - self.base_perf
            now = self.base_server_time + timedelta(seconds=elapsed)

            self.clock.config(text=now.strftime("%H:%M:%S.%f")[:-3])
            self.date.config(text=now.strftime("%Y-%m-%d"))

        self.root.after(10, self.draw_clock)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
