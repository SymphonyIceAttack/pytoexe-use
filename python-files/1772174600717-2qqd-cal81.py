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

# ================= TIMERS =================
timers_frame = tk.Frame(root)
timers_frame.pack(pady=4)

timer1_lbl = tk.Label(timers_frame, fg="blue")
timer2_lbl = tk.Label(timers_frame, fg="darkgreen")
timer3_lbl = tk.Label(timers_frame, fg="purple")

timer1_lbl.pack()
timer2_lbl.pack()
timer3_lbl.pack()

t1_id = t2_id = t3_id = None

def run_timer(lbl, sec, color, after_var):
    if sec < 0:
        lbl.config(text="")
        return None
    m, s = divmod(sec, 60)
    lbl.config(text=f"{m:02d}:{s:02d}", fg=color)
    return root.after(1000, lambda: run_timer(lbl, sec - 1, color, after_var))

def start_timer1(delay):
    global t1_id
    if t1_id:
        root.after_cancel(t1_id)
    def start():
        run_timer(timer1_lbl, 60, "blue", "t1")
    if delay:
        t1_id = root.after(int(delay * 1000), start)
    else:
        start()

def start_timer2():
    global t2_id
    if not extra_timers_enabled:
        timer2_lbl.config(text="")
        return
    if t2_id:
        root.after_cancel(t2_id)
    t2_id = run_timer(timer2_lbl, 60, "darkgreen", "t2")

def start_timer3():
    global t3_id
    if not extra_timers_enabled:
        timer3_lbl.config(text="")
        return
    if t3_id:
        root.after_cancel(t3_id)
    t3_id = run_timer(timer3_lbl, 60, "purple", "t3")

def stop_extra():
    global t2_id, t3_id
    if t2_id: root.after_cancel(t2_id)
    if t3_id: root.after_cancel(t3_id)
    timer2_lbl.config(text="")
    timer3_lbl.config(text="")

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit():
        return
    v = int(txt)

    l = r = 0
    for i in range(len(limits)-1):
        if limits[i] <= v < limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    if ai_mode:
        if v in AI_NEXT_VALUES:
            middle_lbl.config(text=f"{v}\nNext", bg="#ADD8E6")
            start_timer1(ai_delay_sec)

        elif v in SPECIAL_MIDDLES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            start_timer2()

        elif v in EXTRA_TRIGGER_VALUES:
            middle_lbl.config(text=f"{m} =", bg="orange")
            start_timer3()
        else:
            middle_lbl.config(text=f"{m}", bg="white")
    else:
        middle_lbl.config(text=f"{m}", bg="white")

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()
    else:
        stop_extra()

def toggle_extra():
    global extra_timers_enabled
    extra_timers_enabled = not extra_timers_enabled
    if not extra_timers_enabled:
        stop_extra()
    messagebox.showinfo("Extra Timers", "ON" if extra_timers_enabled else "OFF")

def auto_update():
    if not ai_mode:
        return
    entry.delete(0, tk.END)
    entry.insert(0, str(datetime.now().minute))
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    ai_canvas.create_oval(2, 2, 18, 18, fill="green" if ai_mode else "red")

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

ai_canvas = tk.Canvas(btn_frame, width=20, height=20, bd=0, highlightthickness=0)
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

# ================= MENUS =================
menubar = tk.Menu(root)
root.config(menu=menubar)

ai_menu = tk.Menu(menubar, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
ai_menu.add_command(label="Extra Timers", command=toggle_extra)
menubar.add_cascade(label="AI", menu=ai_menu)

draw_ai_lamp()
root.mainloop()