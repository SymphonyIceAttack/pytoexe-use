import tk as tk
import tkinter as tk
from tkinter import simpledialog, messagebox
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
extra_timers_enabled = False  # حالة زر Extra Timers
current_group_idx = 0
ai_delay_sec = 0

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("520x450") # زيادة الارتفاع قليلاً للتايمرات الإضافية
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= TIMERS UI =================
# التايمر الأساسي
timer_lbl = tk.Label(root, font=(current_font, int(BASE_FONT * 0.9)), fg="blue")
timer_running = False
timer_after_id = None

# التايمرات الإضافية (Extra Timers)
extra_timer1_lbl = tk.Label(root, font=(current_font, int(BASE_FONT * 0.8)), fg="purple")
extra_timer2_lbl = tk.Label(root, font=(current_font, int(BASE_FONT * 0.8)), fg="darkred")
extra_after_id = None

# ================= TIMER LOGIC =================
def start_timer(delay_sec=0):
    global timer_running
    if timer_running: return
    timer_running = True
    timer_lbl.config(text="01:00")
    timer_lbl.pack(pady=2)
    root.after(delay_sec * 1000, _countdown, 60)

def stop_timer():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id: root.after_cancel(timer_after_id)
    timer_after_id = None
    timer_lbl.pack_forget()

def _countdown(sec):
    global timer_after_id, timer_running
    if not timer_running: return
    if sec <= 0:
        stop_timer()
        return
    m, s = divmod(sec, 60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id = root.after(1000, _countdown, sec - 1)

# ================= EXTRA TIMERS LOGIC =================
def start_extra_sequence():
    """تبدأ بالتسلسل: التايمر الأول ثم الثاني"""
    if not extra_timers_enabled or not ai_mode: return
    
    # تصفير الأرقام وإظهار الليبلات
    extra_timer1_lbl.config(text="Extra 1: 01:00")
    extra_timer2_lbl.config(text="Extra 2: 01:00")
    extra_timer1_lbl.pack(pady=1)
    
    _extra_countdown(60, 1)

def _extra_countdown(sec, timer_num):
    global extra_after_id
    if not extra_timers_enabled: 
        hide_extra_timers()
        return

    m, s = divmod(sec, 60)
    if timer_num == 1:
        extra_timer1_lbl.config(text=f"Extra 1: {m:02d}:{s:02d}")
        if sec <= 0:
            extra_timer1_lbl.pack_forget()
            extra_timer2_lbl.pack(pady=1)
            extra_after_id = root.after(1000, _extra_countdown, 60, 2)
        else:
            extra_after_id = root.after(1000, _extra_countdown, sec - 1, 1)
    else:
        extra_timer2_lbl.config(text=f"Extra 2: {m:02d}:{s:02d}")
        if sec <= 0:
            hide_extra_timers()
        else:
            extra_after_id = root.after(1000, _extra_countdown, sec - 1, 2)

def hide_extra_timers():
    global extra_after_id
    if extra_after_id: root.after_cancel(extra_after_id)
    extra_after_id = None
    extra_timer1_lbl.pack_forget()
    extra_timer2_lbl.pack_forget()

def toggle_extra_timers():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    if not extra_timers_enabled:
        hide_extra_timers()
    messagebox.showinfo("Extra Timers", f"Extra Timers is now {'ON' if extra_timers_enabled else 'OFF'}")

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2: return
    v = int(txt)
    
    for i in range(len(limits) - 1):
        if limits[i] <= v <= limits[i + 1]:
            l, r = limits[i], limits[i+1]
            break
    else: l, r = 0, 0
    
    m = l + 3
    left_lbl.config(text=l)
    right_lbl.config(text=r)

    # AI behavior
    if ai_mode and v in AI_NEXT_VALUES:
        sign = "<" if v < m else ">" if v > m else "="
        middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
        start_timer(ai_delay_sec)
    elif v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer()
        # تشغيل التايمرات الإضافية إذا كان الـ AI مفعلاً
        if ai_mode and extra_timers_enabled:
            start_extra_sequence()
    else:
        middle_lbl.config(text=f"{m} {'<' if v < m else '>' if v > m else '='}", bg="white")
        stop_timer()

# ================= AI & MODES =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()
    else:
        hide_extra_timers()

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, "end")
    entry.insert(0, (now.hour * 60 + now.minute) % 60)
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.45 * 1.23)
    ai_canvas.config(width=size + 4, height=size + 4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, 2 + size, 2 + size, fill=color, outline="black")

# ================= UI COMPONENTS =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=2)
calc_btn = tk.Button(btns, text="Generate", command=calculate)
calc_btn.pack(side="left", padx=3)
clear_btn = tk.Button(btns, text="Clear", command=lambda: entry.delete(0, "end"))
clear_btn.pack(side="left", padx=3)

ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=4)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=3)
left_lbl = tk.Label(res, width=6, bg="red", fg="black", font=(current_font, int(BASE_FONT * 1.05)))
middle_lbl = tk.Label(res, width=6, bg="white", font=(current_font, int(BASE_FONT * 1.05)))
right_lbl = tk.Label(res, width=6, bg="green", fg="black", font=(current_font, int(BASE_FONT * 1.05)))
left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

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
ai_menu.add_command(label="Extra Timers", command=toggle_extra_timers) # الزر الجديد
menubar.add_cascade(label="AI", menu=ai_menu)

# ================= HELPER FUNCTIONS =================
def apply_scale(val):
    global current_scale
    current_scale = float(val)
    size = int(BASE_FONT * current_scale)
    for w in [entry, calc_btn, clear_btn, left_lbl, middle_lbl, right_lbl]:
        w.config(font=(current_font, int(size * 1.05)))
    draw_ai_lamp()

def open_scale_popup():
    p = tk.Toplevel(root)
    tk.Scale(p, from_=0.7, to=1.5, resolution=0.05, orient="horizontal", command=apply_scale).pack(fill="x")

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)

def enable_move():
    root.config(cursor="fleur")
    def start_move(e):
        root._x, root._y = e.x, e.y
    def do_move(e):
        root.geometry(f"+{e.x_root - root._x}+{e.y_root - root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

root.mainloop()