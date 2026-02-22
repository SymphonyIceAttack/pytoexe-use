import tkinter as tk
from tkinter import ttk
from datetime import datetime
import time

# ================= CONFIG =================
BASE_FONT = 22
current_scale = 1.0
current_font = "Arial"

AI_VALUES = {2,8,14,20,26,32,38,44,50,56}
AI_NEXT_VALUES = {3,9,15,21,27,33,39,45,51,57}

limits = list(range(0, 61, 6))
SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}

dark_mode = False
night_bg = "#1e1e1e"

# ================= STATE =================
ai_mode = True
timer_running = False
timer_seconds = 0

# ================= ROOT =================
root = tk.Tk()
root.title("AI Trade Panel")
root.geometry("420x520")

# ================= MAIN FRAME =================
main = tk.Frame(root)
main.pack(expand=True)

# ================= LABELS =================
left_lbl = tk.Label(main, text="", font=(current_font, BASE_FONT))
left_lbl.grid(row=0, column=0, padx=10)

middle_lbl = tk.Label(
    main,
    text="",
    font=(current_font, BASE_FONT),
    width=8,
    height=3,
    relief="solid",
    justify="center"
)
middle_lbl.grid(row=0, column=1, padx=5)

right_lbl = tk.Label(main, text="", font=(current_font, BASE_FONT))
right_lbl.grid(row=0, column=2, padx=10)

# 🔹 تصغير المسافة تحت المربعات
main.grid_rowconfigure(1, minsize=4)

# ================= TIMER =================
timer_lbl = tk.Label(
    main,
    text="",
    font=(current_font, int(BASE_FONT*0.6)),
    fg="red"
)
timer_lbl.grid(row=1, column=0, columnspan=3, pady=(0, 2))
timer_lbl.grid_remove()

# ================= ENTRY =================
entry = tk.Entry(root, font=(current_font, 18), justify="center")
entry.pack(pady=10)

# ================= SCALE =================
def on_scale(val):
    global current_scale
    current_scale = float(val)
    redraw()

scale = ttk.Scale(root, from_=0.7, to=1.5, value=1.0, command=on_scale)
scale.pack(fill="x", padx=20)

# ================= TIMER LOGIC =================
def start_timer():
    global timer_running, timer_seconds
    timer_seconds = 60
    timer_running = True
    timer_lbl.grid()
    tick()

def stop_timer():
    global timer_running
    timer_running = False
    timer_lbl.grid_remove()

def tick():
    global timer_seconds
    if not timer_running:
        return
    timer_lbl.config(text=f"{timer_seconds}s")
    if timer_seconds <= 0:
        stop_timer()
        return
    timer_seconds -= 1
    root.after(1000, tick)

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit():
        return

    v = int(txt)

    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l, r = limits[i], limits[i+1]
            break

    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    # Default
    middle_text = f"{m}"
    middle_bg = "white"
    middle_font = int(BASE_FONT * current_scale)

    middle_lbl.config(pady=0)

    # ================= AI MODE =================
    if ai_mode and v in AI_VALUES:
        middle_text = f"{v} <\nnext"
        middle_bg = "#ADD8E6"

        middle_font = int(BASE_FONT * current_scale * 0.8)

        # 🔹 تقليل المسافة بين الرقم و next
        middle_lbl.config(pady=1)

        start_timer()

    elif v in AI_NEXT_VALUES:
        stop_timer()

    elif v == m and v in SPECIAL_MIDDLES:
        middle_bg = "orange"

    middle_lbl.config(
        text=middle_text,
        bg=middle_bg,
        font=(current_font, middle_font),
        justify="center"
    )

# ================= REDRAW =================
def redraw():
    calculate()

entry.bind("<KeyRelease>", calculate)

root.mainloop()