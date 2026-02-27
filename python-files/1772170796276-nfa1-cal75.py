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

ai_mode = False
extra_timers_enabled = False
dark_mode = False
ai_delay_sec = 0

if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Pro")
root.geometry("480x420")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

# ================= TIMER LOGIC (NO OVERLAP) =================
t1_id, t2_id, t3_id = None, None, None

def stop_timer(timer_num):
    global t1_id, t2_id, t3_id
    if timer_num == 1 and t1_id: root.after_cancel(t1_id); t1_id = None; lbl_t1.pack_forget()
    if timer_num == 2 and t2_id: root.after_cancel(t2_id); t2_id = None; lbl_t2.pack_forget()
    if timer_num == 3 and t3_id: root.after_cancel(t3_id); t3_id = None; lbl_t3.pack_forget()

def start_t1(delay):
    stop_timer(1)
    lbl_t1.config(text="Timer 1: 01:00")
    lbl_t1.pack(pady=1)
    root.after(delay * 1000, lambda: run_countdown(60, lbl_t1, 1))

def start_extra_sequence():
    stop_timer(2); stop_timer(3)
    lbl_t2.config(text="Extra 1: 01:00")
    lbl_t2.pack(pady=1)
    run_countdown(60, lbl_t2, 2)

def run_countdown(sec, label, num):
    global t1_id, t2_id, t3_id
    m, s = divmod(sec, 60)
    label.config(text=f"{label.cget('text').split(':')[0]}: {m:02d}:{s:02d}")
    if sec > 0:
        next_call = lambda: run_countdown(sec-1, label, num)
        if num == 1: t1_id = root.after(1000, next_call)
        elif num == 2: t2_id = root.after(1000, next_call)
        elif num == 3: t3_id = root.after(1000, next_call)
    else:
        label.pack_forget()
        if num == 2: # Start T3 after T2 ends
            lbl_t3.config(text="Extra 2: 01:00")
            lbl_t3.pack(pady=1)
            run_countdown(60, lbl_t3, 3)

# ================= CORE FUNCTIONS =================
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

    if ai_mode:
        if v in AI_NEXT_VALUES:
            middle_lbl.config(text=f"{v} {'<' if v<m else '>'}\nNext", bg="#ADD8E6")
            start_t1(ai_delay_sec)
        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            if extra_timers_enabled: start_extra_sequence()
        else:
            middle_lbl.config(text=f"{m} {'<' if v<m else '>'}", bg="white")
    else:
        middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg="orange" if v in SPECIAL_MIDDLES else "white")

def auto_update():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, tk.END)
    entry.insert(0, str(now.minute)) # أو now.second للتجربة السريعة
    calculate()
    root.after(1000, auto_update)

# ================= UI SETUP =================
lbl_t1 = tk.Label(root, fg="blue", font=(current_font, 10, "bold"))
lbl_t2 = tk.Label(root, fg="green", font=(current_font, 10, "bold"))
lbl_t3 = tk.Label(root, fg="purple", font=(current_font, 10, "bold"))

entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="Generate", command=calculate).pack(side="left", padx=2)
tk.Button(btn_frame, text="Clear", command=lambda: entry.delete(0, tk.END)).pack(side="left", padx=2)
tk.Button(btn_frame, text="◀", command=lambda: nav_group(-1)).pack(side="left", padx=2)
tk.Button(btn_frame, text="▶", command=lambda: nav_group(1)).pack(side="left", padx=2)

ai_canvas = tk.Canvas(btn_frame, width=20, height=20, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)

res_frame = tk.Frame(root)
res_frame.pack(pady=10)
left_lbl = tk.Label(res_frame, width=6, height=2, bg="red", fg="black", font=(current_font, BASE_FONT, "bold"))
middle_lbl = tk.Label(res_frame, width=6, height=2, bg="white", fg="black", font=(current_font, BASE_FONT, "bold"))
right_lbl = tk.Label(res_frame, width=6, height=2, bg="green", fg="black", font=(current_font, BASE_FONT, "bold"))
for lbl in [left_lbl, middle_lbl, right_lbl]: lbl.pack(side="left", padx=2)

# ================= VIEW & AI ACTIONS =================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    btn_frame.config(bg=bg); res_frame.config(bg=bg)
    entry.config(bg="#404040" if dark_mode else "white", fg=fg, insertbackground=fg)
    # المربعات لا تتأثر ألوان خلفيتها
    for lbl in [left_lbl, right_lbl, middle_lbl]: lbl.config(fg="black")

def apply_scale(v):
    global current_scale
    current_scale = float(v)
    size = int(BASE_FONT * current_scale)
    entry.config(font=(current_font, size))
    for lbl in [left_lbl, middle_lbl, right_lbl]: lbl.config(font=(current_font, size, "bold"))

def nav_group(step):
    global limits
    try:
        curr = int(entry.get())
        idx = next((i for i, val in enumerate(limits) if val >= curr), 0)
        new_idx = (idx + step) % (len(limits)-1)
        entry.delete(0, tk.END); entry.insert(0, limits[new_idx]); calculate()
    except: entry.delete(0, tk.END); entry.insert(0, limits[0]); calculate()

def draw_lamp():
    ai_canvas.delete("all")
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2, 2, 18, 18, fill=color, outline="black")

# ================= MENUS =================
m_bar = tk.Menu(root)
f_menu = tk.Menu(m_bar, tearoff=0)
f_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
f_menu.add_command(label="Move Window", command=lambda: [root.bind("<B1-Motion>", lambda e: root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")), root.bind("<Button-1>", lambda e: setattr(root, '_x', e.x) or setattr(root, '_y', e.y))])
m_bar.add_cascade(label="File", menu=f_menu)

v_menu = tk.Menu(m_bar, tearoff=0)
v_menu.add_command(label="Day / Night", command=toggle_mode)
v_menu.add_command(label="Scale", command=lambda: [tk.Toplevel(root).title("Scale"), tk.Scale(tk.Toplevel(root), from_=0.7, to=1.5, resolution=0.1, orient="horizontal", command=apply_scale).pack()])
v_menu.add_command(label="Transparency", command=lambda: tk.Scale(tk.Toplevel(root), from_=0.3, to=1.0, resolution=0.05, orient="horizontal", command=lambda v: root.attributes("-alpha", float(v))).pack())
m_bar.add_cascade(label="View", menu=v_menu)

a_menu = tk.Menu(m_bar, tearoff=0)
a_menu.add_command(label="Toggle AI", command=lambda: [globals().update(ai_mode=not ai_mode), draw_lamp(), auto_update() if ai_mode else [stop_timer(1), stop_timer(2), stop_timer(3)]])
a_menu.add_command(label="Edit Timer 1", command=lambda: setattr(globals(), 'ai_delay_sec', int(tk.simpledialog.askstring("Delay", "Seconds:", parent=root) or 0)))
a_menu.add_command(label="Extra Timers", command=lambda: [globals().update(extra_timers_enabled=not extra_timers_enabled), messagebox.showinfo("AI", f"Extra Timers: {extra_timers_enabled}")])
m_bar.add_cascade(label="AI", menu=a_menu)

root.config(menu=m_bar)
draw_lamp()
root.mainloop()