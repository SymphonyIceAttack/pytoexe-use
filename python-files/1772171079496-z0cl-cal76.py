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
root.geometry("450x380")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

# ================= TIMER LOGIC =================
t1_after_id = None
t_extra_after_id = None

timer1_lbl = tk.Label(root, fg="blue")
timer_extra_lbl = tk.Label(root) # Label for Extra 1 and Extra 2

def stop_timer1():
    global t1_after_id
    if t1_after_id:
        root.after_cancel(t1_after_id)
        t1_after_id = None
    timer1_lbl.pack_forget()

def start_timer1(delay):
    stop_timer1()
    timer1_lbl.config(text="01:00")
    timer1_lbl.pack(pady=2)
    run_countdown1(60, delay)

def run_countdown1(sec, delay):
    global t1_after_id
    if sec < 0:
        stop_timer1()
        return
    m, s = divmod(sec, 60)
    timer1_lbl.config(text=f"{m:02d}:{s:02d}")
    t1_after_id = root.after(1000 if delay <= 0 else delay*1000, lambda: run_countdown1(sec-1, 0))

def stop_extra_timers():
    global t_extra_after_id
    if t_extra_after_id:
        root.after_cancel(t_extra_after_id)
        t_extra_after_id = None
    timer_extra_lbl.pack_forget()

def start_extra_sequence():
    stop_extra_timers()
    timer_extra_lbl.config(text="Extra 1: 01:00", fg="darkgreen")
    timer_extra_lbl.pack(pady=2)
    run_extra_countdown(60, 1)

def run_extra_countdown(sec, sequence_num):
    global t_extra_after_id
    if sec < 0:
        if sequence_num == 1:
            timer_extra_lbl.config(text="Extra 2: 01:00", fg="purple")
            run_extra_countdown(60, 2)
        else:
            stop_extra_timers()
        return
    m, s = divmod(sec, 60)
    label_prefix = "Extra 1" if sequence_num == 1 else "Extra 2"
    timer_extra_lbl.config(text=f"{label_prefix}: {m:02d}:{s:02d}")
    t_extra_after_id = root.after(1000, lambda: run_extra_countdown(sec-1, sequence_num))

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit(): return
    v = int(txt)
    
    l, r = 0, 0
    for i in range(len(limits)-1):
        if limits[i] <= v < limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    if ai_mode:
        if v in AI_NEXT_VALUES:
            sign = "<" if v < m else ">" if v > m else "="
            middle_lbl.config(text=f"{v} {sign}\nNext", bg="#ADD8E6")
            start_timer1(ai_delay_sec)
        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            stop_timer1()
            if extra_timers_enabled:
                start_extra_sequence()
        else:
            middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg="white")
            stop_timer1()
            stop_extra_timers()
    else:
        # Manual Mode
        bg_col = "orange" if v in SPECIAL_MIDDLES else "white"
        middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg=bg_col)

# ================= AI & UPDATES =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode: auto_update()
    else: 
        stop_timer1()
        stop_extra_timers()

def toggle_extra():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    messagebox.showinfo("Extra Timers", f"Extra Timers: {'ON' if extra_timers_enabled else 'OFF'}")

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, tk.END)
    entry.insert(0, str(now.minute))
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black")

# ================= UI SETUP =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT_SIZE))
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Generate", command=calculate).pack(side="left", padx=2)
tk.Button(btn_frame, text="Clear", command=lambda: entry.delete(0, tk.END)).pack(side="left", padx=2)
tk.Button(btn_frame, text="◀", command=lambda: navigate(-1)).pack(side="left", padx=2)
tk.Button(btn_frame, text="▶", command=lambda: navigate(1)).pack(side="left", padx=2)

ai_canvas = tk.Canvas(btn_frame, width=20, height=20, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)

res_frame = tk.Frame(root)
res_frame.pack(pady=10)

left_lbl = tk.Label(res_frame, width=6, height=2, bg="red", fg="black", font=(current_font, BASE_FONT_SIZE))
middle_lbl = tk.Label(res_frame, width=6, height=2, bg="white", fg="black", font=(current_font, BASE_FONT_SIZE))
right_lbl = tk.Label(res_frame, width=6, height=2, bg="green", fg="black", font=(current_font, BASE_FONT_SIZE))

left_lbl.pack(side="left", padx=2)
middle_lbl.pack(side="left", padx=2)
right_lbl.pack(side="left", padx=2)

def navigate(step):
    try:
        curr = int(entry.get())
    except: curr = 0
    entry.delete(0, tk.END)
    entry.insert(0, str((curr + step) % 60))
    calculate()

# ================= VIEW & FILE FUNCTIONS =================
def toggle_mode():
    is_dark = root.cget("bg") == "#2E2E2E"
    new_bg = "white" if is_dark else "#2E2E2E"
    new_fg = "black" if is_dark else "white"
    root.config(bg=new_bg)
    btn_frame.config(bg=new_bg)
    res_frame.config(bg=new_bg)
    entry.config(bg="white" if is_dark else "#444", fg=new_fg)
    # المربعات تظل ثابتة الألوان
    left_lbl.config(fg="black")
    right_lbl.config(fg="black")
    middle_lbl.config(fg="black")

def apply_scale(val):
    global current_scale
    current_scale = float(val)
    new_size = int(BASE_FONT_SIZE * current_scale)
    entry.config(font=(current_font, new_size))
    for lbl in [left_lbl, middle_lbl, right_lbl, timer1_lbl, timer_extra_lbl]:
        lbl.config(font=(current_font, new_size))

def enable_move():
    def start_move(e): root._x, root._y = e.x, e.y
    def do_move(e): root.geometry(f"+{e.x_root - root._x}+{e.y_root - root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)
    root.config(cursor="fleur")

# ================= MENUS =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Move Window", command=enable_move)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_command(label="Scale", command=lambda: open_popup("Scale", 0.7, 1.5, apply_scale))
view_menu.add_command(label="Transparency", command=lambda: open_popup("Alpha", 0.3, 1.0, lambda v: root.attributes("-alpha", float(v))))
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
ai_menu.add_command(label="Extra Timers", command=toggle_extra)
ai_menu.add_command(label="Edit Timer 1", command=lambda: open_popup("Timer 1 Delay", -5, 5, set_delay))
menubar.add_cascade(label="AI", menu=ai_menu)

def set_delay(v):
    global ai_delay_sec
    ai_delay_sec = int(float(v))

def open_popup(title, f, t, cmd):
    p = tk.Toplevel(root)
    p.title(title)
    tk.Scale(p, from_=f, to=t, resolution=0.05 if f<1 else 1, orient="horizontal", command=cmd).pack(padx=20, pady=20)

draw_ai_lamp()
root.mainloop()