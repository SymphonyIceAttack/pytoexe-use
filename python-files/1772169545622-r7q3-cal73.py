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
extra_timers_enabled = False # الخيار الجديد
current_group_idx = 0
ai_delay_sec = 0

if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator Pro")
root.geometry("520x500")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "#F0F0F0"
ai_bg = "#ADD8E6"

# ================= TIMERS LOGIC =================
# Timer 1 (Original), Timer 2, Timer 3
timer_labels = []
timer_ids = [None, None, None]
timer_active = [False, False, False]

def create_timer_label(color):
    lbl = tk.Label(root, font=(current_font, int(BASE_FONT * 0.8)), fg=color)
    return lbl

timer_lbl1 = create_timer_label("blue")
timer_lbl2 = create_timer_label("red")
timer_lbl3 = create_timer_label("darkgreen")

def start_sequence_timers():
    """تشغيل تايمر 2 ثم تايمر 3 بالتتابع"""
    if not extra_timers_enabled: return
    stop_all_timers()
    run_timer(1, 60, next_timer=2) # يبدأ تايمر 2 (اندكس 1)

def run_timer(idx, sec, next_timer=None):
    stop_timer(idx)
    timer_active[idx] = True
    lbl = [timer_lbl1, timer_lbl2, timer_lbl3][idx]
    lbl.pack(pady=2)
    _countdown(idx, sec, next_timer)

def _countdown(idx, sec, next_timer):
    if not timer_active[idx]: return
    m, s = divmod(sec, 60)
    lbl = [timer_lbl1, timer_lbl2, timer_lbl3][idx]
    lbl.config(text=f"Timer {idx+1}: {m:02d}:{s:02d}")
    
    if sec > 0:
        timer_ids[idx] = root.after(1000, _countdown, idx, sec-1, next_timer)
    else:
        stop_timer(idx)
        if next_timer is not None:
            run_timer(next_timer, 60)

def stop_timer(idx):
    timer_active[idx] = False
    if timer_ids[idx]:
        root.after_cancel(timer_ids[idx])
        timer_ids[idx] = None
    [timer_lbl1, timer_lbl2, timer_lbl3][idx].pack_forget()

def stop_all_timers():
    for i in range(3): stop_timer(i)

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

    # المنطق البرمجي للألوان والتايمر
    if ai_mode and v in AI_NEXT_VALUES:
        sign = "<" if v < m else ">" if v > m else "="
        middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
        run_timer(0, 60) # تشغيل تايمر 1 التقليدي
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        if ai_mode and extra_timers_enabled:
            start_sequence_timers() # تشغيل 2 ثم 3
        else:
            stop_all_timers()
    else:
        sign = "<" if v < m else ">" if v > m else "="
        middle_lbl.config(text=f"{m} {sign}", bg="white")
        stop_all_timers()

# ================= AI & MODES =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode: auto_update()
    else: stop_all_timers()

def toggle_extra_timers():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    status = "ON" if extra_timers_enabled else "OFF"
    messagebox.showinfo("Extra Timers", f"Sequence Timers (2 & 3) are now {status}")

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    val = now.minute % 60
    entry.delete(0, tk.END)
    entry.insert(0, val)
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.6)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, size, size, fill=color, outline="black")

# ================= UI HELPERS =================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    for w in [entry, left_lbl, right_lbl, res]: w.config(bg=bg)
    if not dark_mode: middle_lbl.config(bg="white")

def apply_scale(val):
    global current_scale
    current_scale = float(val)
    new_size = int(BASE_FONT * current_scale)
    entry.config(font=(current_font, new_size))
    for b in [calc_btn, clear_btn, prev_btn, next_btn]: b.config(font=(current_font, int(new_size*0.8)))
    for l in [left_lbl, middle_lbl, right_lbl]: l.config(font=(current_font, new_size))
    draw_ai_lamp()

def enable_move():
    root.config(cursor="fleur")
    root.bind("<Button-1>", lambda e: setattr(root, '_drag_data', {'x': e.x, 'y': e.y}))
    root.bind("<B1-Motion>", lambda e: root.geometry(f"+{e.x_root - root._drag_data['x']}+{e.y_root - root._drag_data['y']}"))

# ================= UI LAYOUT =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=5)
calc_btn = tk.Button(btns, text="Gen", command=calculate)
calc_btn.pack(side="left", padx=2)
clear_btn = tk.Button(btns, text="C", command=lambda: entry.delete(0, tk.END))
clear_btn.pack(side="left", padx=2)
prev_btn = tk.Button(btns, text="◀", command=lambda: navigate(-1))
prev_btn.pack(side="left", padx=2)
next_btn = tk.Button(btns, text="▶", command=lambda: navigate(1))
next_btn.pack(side="left", padx=2)

ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res, width=5, bg="red", fg="white", font=(current_font, BASE_FONT))
middle_lbl = tk.Label(res, width=8, bg="white", font=(current_font, BASE_FONT))
right_lbl = tk.Label(res, width=5, bg="green", fg="white", font=(current_font, BASE_FONT))
left_lbl.pack(side="left", padx=2)
middle_lbl.pack(side="left", padx=2)
right_lbl.pack(side="left", padx=2)

def navigate(step):
    global current_group_idx
    current_group_idx = (current_group_idx + step) % (len(limits)-1)
    entry.delete(0, tk.END)
    entry.insert(0, limits[current_group_idx])
    calculate()

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
ai_menu.add_command(label="Edit Timer 1", command=lambda: open_popup("Timer Delay", -5, 5, lambda v: globals().update(ai_delay_sec=int(v))))
ai_menu.add_command(label="Extra Timers (2 & 3)", command=toggle_extra_timers)
menubar.add_cascade(label="AI", menu=ai_menu)

def open_popup(title, f, t, cmd):
    p = tk.Toplevel(root)
    p.title(title)
    p.geometry("250x100")
    tk.Scale(p, from_=f, to=t, resolution=0.05 if t<=1.5 else 1, orient="horizontal", command=cmd).pack(fill="x", padx=10)
    tk.Button(p, text="Close", command=p.destroy).pack()

root.mainloop()