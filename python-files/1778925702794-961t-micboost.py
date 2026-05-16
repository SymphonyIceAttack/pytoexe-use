import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk
import threading

__author__ = "forgot1en"

# ── State ─────────────────────────────────────────────
gain_db = 30.0
pan_val = 0.0
running = False
stream_thread = None

def db_to_linear(db):
    return 10 ** (db / 20)

def process(indata, outdata, frames, time, status):
    gain  = db_to_linear(gain_db)
    audio = indata[:, 0] * gain
    audio = np.clip(audio, -1.0, 1.0)
    left  = audio * (1.0 - max(0.0, pan_val))
    right = audio * (1.0 + min(0.0, pan_val))
    if outdata.shape[1] >= 2:
        outdata[:, 0] = left
        outdata[:, 1] = right
    else:
        outdata[:, 0] = audio

def start_stream(in_idx, out_idx):
    global running
    running = True
    try:
        with sd.Stream(
            device=(in_idx, out_idx),
            samplerate=48000,
            channels=(1, 2),
            dtype='float32',
            latency='low',
            callback=process
        ):
            while running:
                sd.sleep(50)
    except Exception as e:
        print(f"Stream error: {e}")

def stop_stream():
    global running
    running = False

# ── GUI ───────────────────────────────────────────────
root = tk.Tk()
root.title("MicBoost")
root.geometry("430x560")
root.resizable(False, False)

DARK  = "#1e1f22"
CARD  = "#2b2d31"
BORD  = "#3a3b3e"
TEXT  = "#dbdee1"
MUTED = "#949ba4"
BLUE  = "#5865f2"
GREEN = "#23a55a"
RED   = "#ed4245"
AMBER = "#faa61a"

root.configure(bg=DARK)

style = ttk.Style()
style.theme_use("clam")
style.configure("TCombobox", fieldbackground=CARD, background=CARD,
                foreground=TEXT, bordercolor=BORD, arrowcolor=TEXT)

def lbl(parent, text, size=13, color=TEXT, bold=False, anchor="w", **kw):
    return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                    font=("Segoe UI", size, "bold" if bold else "normal"),
                    anchor=anchor, **kw)

def hframe(parent, bg=DARK, **kw):
    return tk.Frame(parent, bg=bg, **kw)

def cframe(parent):
    f = tk.Frame(parent, bg=CARD, highlightbackground=BORD, highlightthickness=1)
    return f

# ── Header ────────────────────────────────────────────
hdr = hframe(root, pady=10, padx=16)
hdr.pack(fill="x")
lbl(hdr, "🔊  MicBoost", 16, TEXT, bold=True).pack(side="left")
status_dot = lbl(hdr, "● Stopped", 12, RED)
status_dot.pack(side="right")

# ── Devices ───────────────────────────────────────────
dev_card = cframe(root)
dev_card.pack(fill="x", padx=16, pady=(0, 8))
dp = hframe(dev_card, CARD, padx=12, pady=10)
dp.pack(fill="x")

devices  = sd.query_devices()
in_devs  = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
out_devs = [(i, d['name']) for i, d in enumerate(devices) if d['max_output_channels'] > 0]

lbl(dp, "Microphone (input)", 11, MUTED).pack(anchor="w")
in_var = tk.StringVar()
in_box  = ttk.Combobox(dp, textvariable=in_var, state="readonly", width=50)
in_box['values'] = [f"{i}: {n}" for i, n in in_devs]
if in_devs: in_box.current(0)
in_box.pack(fill="x", pady=(2, 8))

lbl(dp, "Output (headphones / speakers)", 11, MUTED).pack(anchor="w")
out_var = tk.StringVar()
out_box  = ttk.Combobox(dp, textvariable=out_var, state="readonly", width=50)
out_box['values'] = [f"{i}: {n}" for i, n in out_devs]
if out_devs: out_box.current(0)
out_box.pack(fill="x", pady=(2, 0))

# ── Stats ─────────────────────────────────────────────
stats_row = hframe(root, padx=16)
stats_row.pack(fill="x", pady=(0, 8))
for col in range(3):
    stats_row.columnconfigure(col, weight=1)

def stat_card(parent, val, label_text, col):
    f = tk.Frame(parent, bg=CARD, highlightbackground=BORD, highlightthickness=1)
    f.grid(row=0, column=col, sticky="ew", padx=(0 if col==0 else 4, 0))
    vl = tk.Label(f, text=val, bg=CARD, fg="#fff",
                  font=("Segoe UI", 18, "bold"), anchor="center")
    vl.pack(pady=(10,0))
    tk.Label(f, text=label_text, bg=CARD, fg=MUTED,
             font=("Segoe UI", 10), anchor="center").pack(pady=(0,10))
    return vl

stat_gain = stat_card(stats_row, "30 dB",   "Gain",    0)
stat_pan  = stat_card(stats_row, "Center",  "Pan",     1)
stat_sr   = stat_card(stats_row, "48k Hz",  "Sample",  2)

# ── Sliders ───────────────────────────────────────────
sliders_card = cframe(root)
sliders_card.pack(fill="x", padx=16, pady=(0, 8))
sp = hframe(sliders_card, CARD, padx=12, pady=10)
sp.pack(fill="x")

def make_slider(parent, label_text, from_, to, init, fmt, color, on_change):
    row = hframe(parent, CARD)
    row.pack(fill="x", pady=(0, 10))
    top = hframe(row, CARD)
    top.pack(fill="x")
    lbl(top, label_text, 13, TEXT).pack(side="left")
    val_lbl = lbl(top, fmt(init), 13, "#fff", bold=True, anchor="e")
    val_lbl.pack(side="right")
    var = tk.DoubleVar(value=init)
    def _on(v):
        val_lbl.config(text=fmt(float(v)))
        on_change(float(v))
    s = tk.Scale(row, variable=var, from_=from_, to=to, orient="horizontal",
                 bg=CARD, fg=TEXT, troughcolor="#1e1f22", activebackground=color,
                 highlightthickness=0, bd=0, showvalue=False,
                 command=_on, sliderlength=18, sliderrelief="flat")
    s.configure(cursor="hand2")
    s.pack(fill="x")
    return var

def on_gain(v):
    global gain_db
    gain_db = v
    stat_gain.config(text=f"{int(v)} dB")

def on_pan(v):
    global pan_val
    pan_val = v / 100.0
    if v == 0:
        stat_pan.config(text="Center")
    elif v < 0:
        stat_pan.config(text=f"L {int(abs(v))}")
    else:
        stat_pan.config(text=f"R {int(v)}")

make_slider(sp, "Gain (dB)", 0, 60, 30,
            lambda v: f"{int(v)} dB", BLUE, on_gain)
make_slider(sp, "Pan", -100, 100, 0,
            lambda v: "Center" if v==0 else (f"L {int(abs(v))}" if v<0 else f"R {int(v)}"),
            BLUE, on_pan)

# ── Buttons ───────────────────────────────────────────
btn_frame = hframe(root, padx=16, pady=4)
btn_frame.pack(fill="x")

def toggle():
    global stream_thread
    if not running:
        in_idx  = int(in_var.get().split(":")[0])
        out_idx = int(out_var.get().split(":")[0])
        stream_thread = threading.Thread(target=start_stream, args=(in_idx, out_idx), daemon=True)
        stream_thread.start()
        start_btn.config(text="⏹  Stop", bg=RED)
        status_dot.config(text="● Active", fg=GREEN)
    else:
        stop_stream()
        start_btn.config(text="▶  Start boost", bg=BLUE)
        status_dot.config(text="● Stopped", fg=RED)

start_btn = tk.Button(btn_frame, text="▶  Start boost", bg=BLUE, fg="#fff",
                      font=("Segoe UI", 13, "bold"), relief="flat", cursor="hand2",
                      activebackground="#4752c4", activeforeground="#fff",
                      command=toggle, pady=10)
start_btn.pack(fill="x")

# ── Footer ────────────────────────────────────────────
tk.Label(root, text="Set output to your mic's virtual cable or same device loopback",
         bg=DARK, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(8,0))
tk.Label(root, text="by forgot1en", bg=DARK, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(2,8))

root.mainloop()
