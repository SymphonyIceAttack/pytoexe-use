import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT_SIZE = 16
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
root.geometry("420x350")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

# ================= TIMER LOGIC (FIXED) =================
t1_id = None
t_ex_id = None

timer1_lbl = tk.Label(root, fg="blue", font=(current_font, 14))
timer_ex_lbl = tk.Label(root, font=(current_font, 14))

def stop_t1():
    global t1_id
    if t1_id: root.after_cancel(t1_id); t1_id = None
    timer1_lbl.pack_forget()

def start_t1(delay):
    stop_t1()
    timer1_lbl.pack(pady=2)
    update_t1(60, delay)

def update_t1(sec, delay):
    global t1_id
    if sec < 0: stop_t1(); return
    m, s = divmod(sec, 60)
    timer1_lbl.config(text=f"{m:02d}:{s:02d}")
    # تطبيق التأخير فقط على أول ثانية
    wait = 1000 if delay <= 0 else delay * 1000
    t1_id = root.after(wait, lambda: update_t1(sec-1, 0))

def stop_extra():
    global t_ex_id
    if t_ex_id: root.after_cancel(t_ex_id); t_ex_id = None
    timer_ex_lbl.pack_forget()

def start_extra_seq():
    stop_extra()
    timer_ex_lbl.pack(pady=2)
    update_extra(60, 1) # ابدأ بـ Extra 1

def update_extra(sec, phase):
    global t_ex_id
    if sec < 0:
        if phase == 1: update_extra(60, 2) # انتقل لـ Extra 2
        else: stop_extra()
        return
    
    m, s = divmod(sec, 60)
    color = "darkgreen" if phase == 1 else "purple"
    prefix = "Extra 1" if phase == 1 else "Extra 2"
    timer_ex_lbl.config(text=f"{prefix}: {m:02d}:{s:02d}", fg=color)
    t_ex_id = root.after(1000, lambda: update_extra(sec-1, phase))

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

    if ai_mode:
        if v in AI_NEXT_VALUES:
            middle_lbl.config(text=f"{v} {'<' if v<m else '>' if v>m else '='}\nNext", bg="#ADD8E6")
            start_t1(ai_delay_sec)
        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            if extra_timers_enabled: start_extra_seq()
        else:
            middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg="white")
            stop_extra() # اختفاء التايمرات إذا لم يكن الرقم مميزاً
    else:
        bg_col = "orange" if v in SPECIAL_MIDDLES else "white"
        middle_lbl.config(text=f"{m} {'<' if v<m else '>' if v>m else '='}", bg=bg_col)

# ================= AI CONTROL =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_lamp()
    if ai_mode: auto_run()
    else: stop_t1(); stop_extra()

def auto_run():
    if not ai_mode: return
    now = datetime.now()
    entry.delete(0, tk.END)
    entry.insert(0, str(now.minute))
    calculate()
    root.after(1000, auto_run)

def draw_lamp():
    ai_canvas.delete("all")
    ai_canvas.create_oval(2, 2, 18, 18, fill="green" if ai_mode else "red", outline="black")

# ================= UI ELEMENTS =================
entry = tk.Entry(root, justify="center", font=(current_font, BASE_FONT_SIZE))
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=5)

tk.Button(btns, text="Generate", command=calculate).pack(side="left", padx=2)
tk.Button(btns, text="Clear", command=lambda: entry.delete(0, tk.END)).pack(side="left", padx=2)
tk.Button(btns, text="◀", command=lambda: nav(-1)).pack(side="left", padx=2)
tk.Button(btns, text="▶", command=lambda: nav(1)).pack(side="left", padx=2)

ai_canvas = tk.Canvas(btns, width=20, height=20, bd=0, highlightthickness=0)
ai_canvas.pack(side="left", padx=5)

res = tk.Frame(root)
res.pack(pady=10)

# الأرقام عادية (ليست Bold)
left_lbl = tk.Label(res, width=6, height=2, bg="red", fg="black", font=(current_font, BASE_FONT_SIZE))
middle_lbl = tk.Label(res, width=6, height=2, bg="white", fg="black", font=(current_font, BASE_FONT_SIZE))
right_lbl = tk.Label(res, width=6, height=2, bg="green", fg="black", font=(current_font, BASE_FONT_SIZE))

for lbl in [left_lbl, middle_lbl, right_lbl]: lbl.pack(side="left", padx=2)

def nav(step):
    try: v = int(entry.get())
    except: v = 0
    entry.delete(0, tk.END)
    entry.insert(0, str((v + step) % 60))
    calculate()

# ================= MENUS & FEATURES =================
def set_night():
    is_d = root.cget("bg") == "#2E2E2E"
    root.config(bg="white" if is_d else "#2E2E2E")
    btns.config(bg="white" if is_d else "#2E2E2E")
    res.config(bg="white" if is_d else "#2E2E2E")
    entry.config(bg="white" if is_d else "#444", fg="black" if is_d else "white")
    # المربعات لا تتأثر
    for l in [left_lbl, middle_lbl, right_lbl]: l.config(fg="black")

def move_win():
    def start(e): root._x, root._y = e.x, e.y
    def drag(e): root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")
    root.bind("<Button-1>", start); root.bind("<B1-Motion>", drag)
    root.config(cursor="fleur")

def set_scale(v):
    s = float(v)
    new = int(BASE_FONT_SIZE * s)
    entry.config(font=(current_font, new))
    for l in [left_lbl, middle_lbl, right_lbl, timer1_lbl, timer_ex_lbl]: l.config(font=(current_font, new))

def open_p(t, f, to, c):
    p = tk.Toplevel(root); p.title(t)
    tk.Scale(p, from_=f, to=to, resolution=0.1, orient="horizontal", command=c).pack(padx=20, pady=20)

m_bar = tk.Menu(root)
f_m = tk.Menu(m_bar, tearoff=0)
f_m.add_command(label="Pin/Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
f_m.add_command(label="Move Window", command=move_win)
m_bar.add_cascade(label="File", menu=f_m)

v_m = tk.Menu(m_bar, tearoff=0)
v_m.add_command(label="Day/Night", command=set_night)
v_m.add_command(label="Scale", command=lambda: open_p("Scale", 0.7, 1.5, set_scale))
v_m.add_command(label="Alpha", command=lambda: open_p("Alpha", 0.3, 1.0, lambda v: root.attributes("-alpha", float(v))))
m_bar.add_cascade(label="View", menu=v_m)

a_m = tk.Menu(m_bar, tearoff=0)
a_m.add_command(label="Toggle AI", command=toggle_ai)
a_m.add_command(label="Extra Timers", command=lambda: [globals().update(extra_timers_enabled=not extra_timers_enabled), messagebox.showinfo("Extra", "Toggled")])
a_m.add_command(label="Edit Timer 1", command=lambda: open_p("Delay", -5, 5, lambda v: globals().update(ai_delay_sec=int(float(v)))))
m_bar.add_cascade(label="AI", menu=a_m)

root.config(menu=m_bar)
draw_lamp()
root.mainloop()