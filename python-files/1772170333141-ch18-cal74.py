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
extra_timers_enabled = False
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
root.geometry("520x450")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

night_bg = "#2E2E2E"
day_bg = "#F0F0F0"
ai_bg = "#ADD8E6"

# ================= TIMERS LOGIC =================
# Timer 1 (Original)
timer1_lbl = tk.Label(root, font=(current_font, int(BASE_FONT*0.8)), fg="blue")
timer1_active = False
t1_after_id = None

# Extra Timers (2 & 3)
timer2_lbl = tk.Label(root, font=(current_font, int(BASE_FONT*0.8)), fg="darkgreen")
timer3_lbl = tk.Label(root, font=(current_font, int(BASE_FONT*0.8)), fg="purple")
t2_after_id = None
t3_after_id = None

def stop_all_timers():
    global t1_after_id, t2_after_id, t3_after_id, timer1_active
    timer1_active = False
    for tid, lbl in [(t1_after_id, timer1_lbl), (t2_after_id, timer2_lbl), (t3_after_id, timer3_lbl)]:
        if tid: root.after_cancel(tid)
        lbl.pack_forget()

def start_main_timer(delay_sec):
    global timer1_active, t1_after_id
    if timer1_active: return
    timer1_active = True
    timer1_lbl.config(text="01:00")
    timer1_lbl.pack(pady=2)
    root.after(max(0, delay_sec*1000), lambda: countdown(60, timer1_lbl, "t1"))

def start_extra_sequence():
    stop_all_timers()
    timer2_lbl.config(text="Extra 1: 01:00")
    timer2_lbl.pack(pady=2)
    countdown(60, timer2_lbl, "t2")

def countdown(sec, label, type):
    global t1_after_id, t2_after_id, t3_after_id, timer1_active
    m, s = divmod(sec, 60)
    label.config(text=f"{'Timer' if type=='t1' else 'Extra'}: {m:02d}:{s:02d}")
    
    if sec <= 0:
        label.pack_forget()
        if type == "t2": # Start Timer 3 after 2 finishes
            timer3_lbl.config(text="Extra 2: 01:00")
            timer3_lbl.pack(pady=2)
            countdown(60, timer3_lbl, "t3")
        elif type == "t1": timer1_active = False
        return

    aid = root.after(1000, lambda: countdown(sec-1, label, type))
    if type == "t1": t1_after_id = aid
    elif type == "t2": t2_after_id = aid
    elif type == "t3": t3_after_id = aid

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit(): return
    v = int(txt)
    
    l, r = 0, 60
    for i in range(len(limits)-1):
        if limits[i] <= v < limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)
    
    # AI and Timer Logic
    if ai_mode:
        if v in AI_NEXT_VALUES:
            sign = "<" if v < m else ">" if v > m else "="
            middle_lbl.config(text=f"{v} {sign}\nNext", bg=ai_bg)
            start_main_timer(ai_delay_sec)
        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            if extra_timers_enabled:
                start_extra_sequence()
        else:
            middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg="white")
            stop_all_timers()
    else:
        # Manual Mode
        bg_col = "orange" if v in SPECIAL_MIDDLES else "white"
        middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg=bg_col)

# ================= AI LOGIC =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode: auto_update()
    else: stop_all_timers()

def toggle_extra_timers():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    status = "Enabled" if extra_timers_enabled else "Disabled"
    messagebox.showinfo("Extra Timers", f"Extra Timers are now {status}")

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, "end")
    entry.insert(0, str(now.second)) # Use seconds for testing logic easily
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(20 * current_scale)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, size, size, fill=color, outline="black")

# ================= UI COMPONENTS =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=5)

tk.Button(btns, text="Generate", command=calculate).pack(side="left", padx=2)
tk.Button(btns, text="Clear", command=lambda: entry.delete(0, "end")).pack(side="left", padx=2)
tk.Button(btns, text="◀", command=lambda: prev_group()).pack(side="left", padx=2)
tk.Button(btns, text="▶", command=lambda: next_group()).pack(side="left", padx=2)

ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0, width=25, height=25)
ai_canvas.pack(side="left", padx=5)

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res, width=8, height=2, bg="red", fg="white", font=(current_font, BASE_FONT, "bold"))
middle_lbl = tk.Label(res, width=8, height=2, bg="white", fg="black", font=(current_font, BASE_FONT, "bold"))
right_lbl = tk.Label(res, width=8, height=2, bg="green", fg="white", font=(current_font, BASE_FONT, "bold"))
left_lbl.pack(side="left", padx=2)
middle_lbl.pack(side="left", padx=2)
right_lbl.pack(side="left", padx=2)

# ================= NAVIGATION =================
def prev_group():
    global current_group_idx
    current_group_idx = (current_group_idx - 1) % (len(limits)-1)
    entry.delete(0, "end")
    entry.insert(0, limits[current_group_idx])
    calculate()

def next_group():
    global current_group_idx
    current_group_idx = (current_group_idx + 1) % (len(limits)-1)
    entry.delete(0, "end")
    entry.insert(0, limits[current_group_idx])
    calculate()

# ================= SETTINGS POPUPS =================
def open_scale_popup():
    p = tk.Toplevel(root)
    p.title("Scale")
    tk.Scale(p, from_=0.7, to=1.5, resolution=0.1, orient="horizontal", 
             command=lambda v: apply_scale(v)).pack(padx=20, pady=20)

def apply_scale(v):
    global current_scale
    current_scale = float(v)
    new_size = int(BASE_FONT * current_scale)
    entry.config(font=(current_font, new_size))
    for l in [left_lbl, middle_lbl, right_lbl]:
        l.config(font=(current_font, new_size, "bold"))
    draw_ai_lamp()

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.title("Transparency")
    tk.Scale(p, from_=0.3, to=1.0, resolution=0.05, orient="horizontal",
             command=lambda v: root.attributes("-alpha", float(v))).pack(padx=20, pady=20)

def edit_ai_timer():
    p = tk.Toplevel(root)
    p.title("Edit Timer 1")
    tk.Label(p, text="Delay (seconds)").pack()
    s = tk.Scale(p, from_=-5, to=5, orient="horizontal")
    s.set(ai_delay_sec)
    s.pack()
    tk.Button(p, text="Save", command=lambda: [setattr(root, 'ai_delay_sec', s.get()), p.destroy()]).pack()

# ================= APPEARANCE =================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    btns.config(bg=bg)
    res.config(bg=bg)
    entry.config(bg="white" if not dark_mode else "#404040", fg=fg)
    # نضمن بقاء مربعات النتائج بألوانها الأصلية
    left_lbl.config(fg="white")
    right_lbl.config(fg="white")

def enable_move():
    def start_move(e): root._x, root._y = e.x, e.y
    def do_move(e): root.geometry(f"+{e.x_root - root._x}+{e.y_root - root._y}")
    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)
    root.config(cursor="fleur")

# ================= MENUS =================
menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="Move Window", command=enable_move)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_command(label="Scale", command=open_scale_popup)
view_menu.add_command(label="Transparency", command=open_alpha_popup)
menubar.add_cascade(label="View", menu=view_menu)

ai_menu_obj = tk.Menu(menubar, tearoff=0)
ai_menu_obj.add_command(label="Toggle AI", command=toggle_ai)
ai_menu_obj.add_command(label="Edit Timer 1", command=edit_ai_timer)
ai_menu_obj.add_command(label="Extra Timers (ON/OFF)", command=toggle_extra_timers)
menubar.add_cascade(label="AI", menu=ai_menu_obj)

root.config(menu=menubar)
draw_ai_lamp()
root.mainloop()