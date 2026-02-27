import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}
AI_NEXT_VALUES = {2, 8, 14, 20, 26, 32, 38, 44, 50, 56}

topmost = True
dark_mode = False
ai_mode = False
extra_timers_enabled = False  # الخاصية الجديدة
current_group_idx = 0
ai_delay_sec = 0

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    try:
        with open(LIMITS_FILE) as f:
            limits = sorted(int(x.strip()) for x in f.read().split(",") if x.strip())
    except:
        limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator Pro")
root.geometry("520x450")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "#F0F0F0"
ai_bg = "#ADD8E6"

# ================= TIMERS LOGIC =================
timer_lbl = tk.Label(root, font=(current_font, int(BASE_FONT * 0.8)), fg="blue")
extra_timer_lbl = tk.Label(root, font=(current_font, int(BASE_FONT * 0.8)), fg="red")

timer_after_id = None
extra_after_id = None

def start_main_timer(delay_sec=0):
    stop_main_timer()
    timer_lbl.pack(pady=2)
    root.after(int(delay_sec * 1000), lambda: _countdown_main(60))

def stop_main_timer():
    global timer_after_id
    if timer_after_id:
        root.after_cancel(timer_after_id)
        timer_after_id = None
    timer_lbl.pack_forget()

def _countdown_main(sec):
    global timer_after_id
    if sec < 0:
        stop_main_timer()
        return
    m, s = divmod(sec, 60)
    timer_lbl.config(text=f"Main: {m:02d}:{s:02d}")
    timer_after_id = root.after(1000, _countdown_main, sec - 1)

# --- Extra Timers (Sequential) ---
def start_extra_sequence():
    if not extra_timers_enabled or not ai_mode: return
    stop_extra_timer()
    extra_timer_lbl.pack(pady=2)
    _countdown_extra(60, sequence_part=1)

def stop_extra_timer():
    global extra_after_id
    if extra_after_id:
        root.after_cancel(extra_after_id)
        extra_after_id = None
    extra_timer_lbl.pack_forget()

def _countdown_extra(sec, sequence_part):
    global extra_after_id
    if sec < 0:
        if sequence_part == 1:
            _countdown_extra(60, sequence_part=2) # ابدأ الدقيقة الثانية فوراً
        else:
            stop_extra_timer()
        return
    
    m, s = divmod(sec, 60)
    color = "purple" if sequence_part == 1 else "darkorange"
    extra_timer_lbl.config(text=f"T{sequence_part}: {m:02d}:{s:02d}", fg=color)
    extra_after_id = root.after(1000, _countdown_extra, sec - 1, sequence_part)

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit(): return
    v = int(txt)
    
    # تحديد النطاق
    l, r = 0, 60
    for i in range(len(limits)-1):
        if limits[i] <= v < limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    
    m = l + 3
    left_lbl.config(text=l)
    right_lbl.config(text=r)

    # التحقق من الحالات
    if ai_mode and v in AI_NEXT_VALUES:
        sign = "<" if v < m else ">" if v > m else "="
        middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
        start_main_timer(ai_delay_sec)
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_main_timer()
        if ai_mode and extra_timers_enabled:
            start_extra_sequence()
    else:
        sign = "<" if v < m else ">" if v > m else "="
        middle_lbl.config(text=f"{m} {sign}", bg="white")
        stop_main_timer()

# ================= AI & MODES =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()
    else:
        stop_main_timer()
        stop_extra_timer()

def toggle_extra_timers():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    state = "Enabled" if extra_timers_enabled else "Disabled"
    messagebox.showinfo("Extra Timers", f"Extra Timers are now {state}")

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    val = now.minute % 60
    entry.delete(0, tk.END)
    entry.insert(0, str(val))
    calculate()
    root.after(30000, auto_update) # تحديث كل 30 ثانية لتوفير الجهد

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.6)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, size, size, fill=color, outline="black")

# ================= UI COMPONENTS =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=10)

btns = tk.Frame(root)
btns.pack(pady=5)

calc_btn = tk.Button(btns, text="Generate", command=calculate)
calc_btn.pack(side="left", padx=5)

clear_btn = tk.Button(btns, text="Clear", command=lambda: entry.delete(0, tk.END))
clear_btn.pack(side="left", padx=5)

ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=10)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res, width=8, bg="red", fg="white", font=(current_font, BASE_FONT, "bold"))
middle_lbl = tk.Label(res, width=10, bg="white", font=(current_font, BASE_FONT, "bold"))
right_lbl = tk.Label(res, width=8, bg="green", fg="white", font=(current_font, BASE_FONT, "bold"))
left_lbl.pack(side="left", padx=2)
middle_lbl.pack(side="left", padx=2)
right_lbl.pack(side="left", padx=2)

# ================= MENUS =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Move Window", command=lambda: enable_move())
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=lambda: toggle_mode())
view_menu.add_command(label="Scale", command=lambda: open_scale_popup())
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
ai_menu.add_command(label="Extra Timers (On/Off)", command=toggle_extra_timers)
menubar.add_cascade(label="AI", menu=ai_menu)

# ================= HELPERS =================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg="#404040" if dark_mode else "white", fg=fg)

def open_scale_popup():
    p = tk.Toplevel(root)
    p.title("Scale")
    tk.Scale(p, from_=0.7, to=1.5, resolution=0.1, orient="horizontal", 
             command=lambda v: apply_scale(v)).pack(padx=20, pady=20)

def apply_scale(val):
    global current_scale
    current_scale = float(val)
    new_size = int(BASE_FONT * current_scale)
    entry.config(font=(current_font, new_size))
    left_lbl.config(font=(current_font, new_size, "bold"))
    middle_lbl.config(font=(current_font, new_size, "bold"))
    right_lbl.config(font=(current_font, new_size, "bold"))

def enable_move():
    def start_move(e): root._x, root._y = e.x, e.y
    def do_move(e): root.geometry(f"+{e.x_root - root._x}+{e.y_root - root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

root.mainloop()