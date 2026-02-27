import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT_SIZE = 16
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}
AI_NEXT_VALUES = {2, 8, 14, 20, 26, 32, 38, 44, 50, 56}
EXTRA_TRIGGER_VALUES = {4, 10, 16, 22, 28, 34, 40, 46, 52, 58}

ai_mode = False
extra_timers_enabled = False
ai_delay_sec = 0

if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calc")
root.geometry("420x380")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

# ================= TIMER (SINGLE LINE / SEQUENTIAL) =================
timer_after = None
timer_stage = 0  # 1,2,3
timer_lbl = tk.Label(root, fg="blue", font=(current_font, BASE_FONT_SIZE))
timer_lbl.pack(pady=4)  # مكانه ثابت تحت النتائج

def stop_timer():
    global timer_after, timer_stage
    if timer_after:
        root.after_cancel(timer_after)
        timer_after = None
    timer_stage = 0
    timer_lbl.config(text="")

def start_timer_chain():
    stop_timer()
    start_stage(1, ai_delay_sec)

def start_stage(stage, delay=0):
    global timer_stage
    timer_stage = stage
    root.after(max(0, int(delay * 1000)), lambda: run_timer(60))

def run_timer(sec):
    global timer_after, timer_stage

    if sec < 0:
        # hide current
        timer_lbl.config(text="")

        # next stage
        if timer_stage == 1 and extra_timers_enabled:
            start_stage(2)
            return
        if timer_stage == 2 and extra_timers_enabled:
            start_stage(3)
            return

        stop_timer()
        return

    m, s = divmod(sec, 60)
    name = f"Timer {timer_stage}"
    timer_lbl.config(text=f"{name}: {m:02d}:{s:02d}")

    timer_after = root.after(1000, lambda: run_timer(sec - 1))

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit():
        return
    v = int(txt)

    l = r = 0
    for i in range(len(limits) - 1):
        if limits[i] <= v < limits[i + 1]:
            l, r = limits[i], limits[i + 1]
            break

    m = l + 3
    left_lbl.config(text=l)
    right_lbl.config(text=r)

    if ai_mode:
        if v in AI_NEXT_VALUES:
            middle_lbl.config(text=f"{v}\nNext", bg="#ADD8E6")
            start_timer_chain()

        elif v in SPECIAL_MIDDLES or v in EXTRA_TRIGGER_VALUES:
            middle_lbl.config(text=f"{m} =", bg="orange")

        else:
            middle_lbl.config(text=f"{m}", bg="white")
    else:
        bg = "orange" if v in SPECIAL_MIDDLES else "white"
        middle_lbl.config(text=f"{m}", bg=bg)

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()
    else:
        stop_timer()

def toggle_extra():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    if not extra_timers_enabled:
        stop_timer()
    messagebox.showinfo("Extra Timers", "ON" if extra_timers_enabled else "OFF")

def auto_update():
    if not ai_mode:
        return
    now = datetime.now()
    entry.delete(0, tk.END)
    entry.insert(0, str(now.minute))
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    ai_canvas.create_oval(2, 2, 18, 18,
                          fill="green" if ai_mode else "red",
                          outline="black")

# ================= UI =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT_SIZE))
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Generate", command=calculate).pack(side="left", padx=2)
tk.Button(btn_frame, text="Clear", command=lambda: entry.delete(0, tk.END)).pack(side="left", padx=2)
tk.Button(btn_frame, text="◀", command=lambda: navigate(-1)).pack(side="left", padx=2)
tk.Button(btn_frame, text="▶", command=lambda: navigate(1)).pack(side="left", padx=2)

ai_canvas = tk.Canvas(btn_frame, width=20, height=20, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)

res_frame = tk.Frame(root)
res_frame.pack(pady=10)

left_lbl = tk.Label(res_frame, width=6, height=2, bg="red", font=(current_font, BASE_FONT_SIZE))
middle_lbl = tk.Label(res_frame, width=6, height=2, bg="white", font=(current_font, BASE_FONT_SIZE))
right_lbl = tk.Label(res_frame, width=6, height=2, bg="green", font=(current_font, BASE_FONT_SIZE))

left_lbl.pack(side="left", padx=2)
middle_lbl.pack(side="left", padx=2)
right_lbl.pack(side="left", padx=2)

def navigate(step):
    try:
        v = int(entry.get())
    except:
        v = 0
    entry.delete(0, tk.END)
    entry.insert(0, str((v + step) % 60))
    calculate()

# ================= MENUS (UNCHANGED) =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin",
    command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Move Window",
    command=lambda: root.bind("<B1-Motion>",
    lambda e: root.geometry(f"+{e.x_root}+{e.y_root}")))
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=lambda: None)
view_menu.add_command(label="Scale",
    command=lambda: open_popup("Scale", 0.7, 1.5, apply_scale))
view_menu.add_command(label="Transparency",
    command=lambda: open_popup("Alpha", 0.3, 1.0,
    lambda v: root.attributes("-alpha", float(v))))
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
ai_menu.add_command(label="Extra Timers", command=toggle_extra)
ai_menu.add_command(label="Edit Timer 1",
    command=lambda: open_popup("Delay", -5, 5, set_delay))
menubar.add_cascade(label="AI", menu=ai_menu)

def set_delay(v):
    global ai_delay_sec
    ai_delay_sec = int(float(v))

def apply_scale(v):
    sz = int(BASE_FONT_SIZE * float(v))
    for w in [entry, left_lbl, middle_lbl, right_lbl, timer_lbl]:
        w.config(font=(current_font, sz))

def open_popup(title, f, t, cmd):
    p = tk.Toplevel(root)
    p.title(title)
    tk.Scale(p, from_=f, to=t,
             resolution=0.05 if f < 1 else 1,
             orient="horizontal",
             command=cmd).pack(padx=20, pady=20)

draw_ai_lamp()
root.mainloop()