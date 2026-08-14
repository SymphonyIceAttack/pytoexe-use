import csv
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path

import pyautogui

# -----------------------------
# Settings
# -----------------------------
DEFAULT_CLICK_COUNT = 10
DEFAULT_INTERVAL_MS = 100
LOG_FILE = "click_log.csv"

saved_position = None
clicking = False
stop_requested = False


def now_ms():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log_event(event, details=""):
    path = Path(LOG_FILE)
    new_file = not path.exists()

    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["time", "event", "details"])
        writer.writerow([now_ms(), event, details])


def set_position():
    global saved_position

    saved_position = pyautogui.position()
    x, y = saved_position

    position_label.config(text=f"X: {x}    Y: {y}")
    status_label.config(text="Position saved")
    log_event("POSITION_SET", f"x={x};y={y}")


def start_clicking():
    global clicking, stop_requested

    if saved_position is None:
        status_label.config(text="ابتدا F2 را بزن و موقعیت را ثبت کن.")
        return

    if clicking:
        return

    try:
        count = int(count_var.get())
        interval_ms = int(interval_var.get())
        if count < 1 or interval_ms < 0:
            raise ValueError
    except ValueError:
        status_label.config(text="تعداد و فاصله باید عدد صحیح معتبر باشند.")
        return

    clicking = True
    stop_requested = False

    start_button.config(state="disabled")
    stop_button.config(state="normal")
    status_label.config(text="در حال کلیک...")

    x, y = saved_position
    log_event(
        "START",
        f"x={x};y={y};count={count};interval_ms={interval_ms}"
    )

    # Run one click at a time through Tkinter's event loop so
    # the window remains responsive.
    perform_click(1, count, interval_ms)


def perform_click(index, count, interval_ms):
    global clicking

    if stop_requested or not clicking:
        finish_clicking("STOPPED")
        return

    if saved_position is None:
        finish_clicking("NO_POSITION")
        return

    x, y = saved_position

    click_start = time.perf_counter_ns()
    pyautogui.click(x=x, y=y)
    elapsed_ms = (time.perf_counter_ns() - click_start) / 1_000_000

    log_event(
        "CLICK",
        f"index={index}/{count};x={x};y={y};duration_ms={elapsed_ms:.3f}"
    )

    if index >= count:
        finish_clicking("DONE")
        return

    root.after(
        interval_ms,
        lambda: perform_click(index + 1, count, interval_ms)
    )


def stop_clicking():
    global stop_requested
    stop_requested = True
    status_label.config(text="Stopping...")


def finish_clicking(reason):
    global clicking, stop_requested

    clicking = False
    stop_requested = False

    start_button.config(state="normal")
    stop_button.config(state="disabled")

    status_label.config(text="آماده" if reason == "DONE" else "متوقف شد")
    log_event("END", reason)


def clear_position():
    global saved_position

    saved_position = None
    position_label.config(text="X: 0    Y: 0")
    status_label.config(text="Position cleared")
    log_event("POSITION_CLEARED")


def clear_log():
    path = Path(LOG_FILE)
    try:
        if path.exists():
            path.unlink()
        status_label.config(text="Log cleared")
    except OSError as exc:
        status_label.config(text=f"خطا در حذف لاگ: {exc}")


def close_app():
    global stop_requested
    stop_requested = True
    root.destroy()


# -----------------------------
# GUI
# -----------------------------
root = tk.Tk()
root.title("Fixed Point Auto Clicker")
root.geometry("760x570")
root.minsize(700, 520)

count_var = tk.StringVar(value=str(DEFAULT_CLICK_COUNT))
interval_var = tk.StringVar(value=str(DEFAULT_INTERVAL_MS))

title = tk.Label(
    root,
    text="Fixed Point Auto Clicker",
    font=("Arial", 22, "bold")
)
title.pack(pady=(15, 5))

status_label = tk.Label(
    root,
    text="آماده — برای ثبت نقطه F2 را بزن",
    font=("Arial", 12),
    padx=15,
    pady=10
)
status_label.pack(fill="x", padx=20)

settings = tk.LabelFrame(
    root,
    text="Click Settings",
    font=("Arial", 11, "bold"),
    padx=15,
    pady=12
)
settings.pack(fill="x", padx=20, pady=10)

tk.Label(settings, text="Click Count:").grid(
    row=0, column=0, sticky="w", padx=8, pady=8
)
tk.Spinbox(
    settings,
    from_=1,
    to=100000,
    textvariable=count_var,
    width=12
).grid(row=0, column=1, padx=8)

tk.Label(settings, text="Interval (ms):").grid(
    row=1, column=0, sticky="w", padx=8, pady=8
)
tk.Spinbox(
    settings,
    from_=0,
    to=100000,
    textvariable=interval_var,
    width=12
).grid(row=1, column=1, padx=8)

position_frame = tk.LabelFrame(
    root,
    text="Position",
    font=("Arial", 11, "bold"),
    padx=15,
    pady=12
)
position_frame.pack(fill="x", padx=20, pady=5)

position_label = tk.Label(
    position_frame,
    text="X: 0    Y: 0",
    font=("Arial", 15, "bold")
)
position_label.pack(side="left", padx=15)

tk.Button(
    position_frame,
    text="Set Position (F2)",
    width=18,
    command=set_position
).pack(side="right", padx=10)

controls = tk.Frame(root)
controls.pack(fill="x", padx=20, pady=12)

start_button = tk.Button(
    controls,
    text="▶ Start Clicking (F3)",
    font=("Arial", 12, "bold"),
    command=start_clicking,
    width=20
)
start_button.pack(side="left", expand=True, padx=5)

stop_button = tk.Button(
    controls,
    text="■ Stop",
    font=("Arial", 12, "bold"),
    command=stop_clicking,
    width=14,
    state="disabled"
)
stop_button.pack(side="left", expand=True, padx=5)

tk.Button(
    controls,
    text="Clear Position",
    width=16,
    command=clear_position
).pack(side="left", expand=True, padx=5)

log_frame = tk.LabelFrame(
    root,
    text="Log",
    font=("Arial", 11, "bold"),
    padx=8,
    pady=8
)
log_frame.pack(fill="both", expand=True, padx=20, pady=5)

tk.Button(
    log_frame,
    text="Clear Log",
    command=clear_log
).pack(anchor="e", pady=(0, 5))

log_info = tk.Label(
    log_frame,
    text=f"جزئیات کلیک‌ها در {LOG_FILE} ذخیره می‌شود."
)
log_info.pack(anchor="w")

footer = tk.Label(
    root,
    text="Hotkeys: F2 = Set Position   |   F3 = Start Clicking",
    font=("Arial", 9)
)
footer.pack(pady=10)

# Hotkeys
root.bind_all("<F2>", lambda event: set_position())
root.bind_all("<F3>", lambda event: start_clicking())

root.protocol("WM_DELETE_WINDOW", close_app)

log_event("APPLICATION_STARTED")
root.mainloop()
