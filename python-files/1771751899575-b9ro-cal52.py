import tkinter as tk
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}
AI_NEXT_VALUES = {2,8,14,20,26,32,38,44,50,56}

topmost = True
dark_mode = False
history = []
current_group_idx = 0
ai_mode = False
timer_running = False
timer_after_id = None

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("500x340")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= TIMER =================
def start_timer():
    global timer_running
    if timer_running:
        return
    timer_running = True
    timer_lbl.config(text="01:00")
    timer_lbl.pack(pady=2)
    countdown(60)

def stop_timer():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id:
        root.after_cancel(timer_after_id)
        timer_after_id = None
    timer_lbl.pack_forget()

def countdown(sec):
    global timer_after_id
    if not timer_running:
        return
    if sec <= 0:
        stop_timer()
        return
    m, s = divmod(sec, 60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id = root.after(1000, countdown, sec - 1)

# ================= CALCULATE =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        return

    v = int(txt)
    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l, r = limits[i], limits[i+1]
            break

    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    middle_lbl.config(
        font=(current_font, int(BASE_FONT*current_scale*1.05)),
        justify="center",
        anchor="center",
        pady=1
    )

    # ===== AI MODE =====
    if ai_mode and v in AI_NEXT_VALUES:
        middle_lbl.config(
            text=f"{v} >\nNext",
            bg=ai_bg
        )
        start_timer()

    elif ai_mode and v in SPECIAL_MIDDLES:
        stop_timer()
        middle_lbl.config(
            text=f"{m} =",
            bg="orange"
        )

    else:
        stop_timer()
        sign = "=" if v == m else "<" if v < m else ">"
        middle_lbl.config(
            text=f"{m} {sign}",
            bg=night_bg if dark_mode else "white"
        )

    add_history(v,l,m,r)

# ================= HISTORY =================
def add_history(v,l,m,r):
    ts = datetime.now().strftime("%H:%M:%S")
    history.append(f"{v} → {l}-{m}-{r} | {ts}")

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode
    draw_ai_lamp()
    if ai_mode:
        auto_update()

def auto_update():
    if not ai_mode:
        return
    now = datetime.now()
    entry.delete(0,"end")
    entry.insert(0,(now.hour*60 + now.minute) % 60)
    calculate()
    root.after(1000, auto_update)

def draw_ai_lamp():
    ai_canvas.delete("all")
    size = int(BASE_FONT * current_scale * 0.6)
    ai_canvas.config(width=size+4, height=size+4)
    color = "green" if ai_mode else "red"
    ai_canvas.create_oval(2,2,2+size,2+size,fill=color,outline="black")

# ================= UI =================
entry = tk.Entry(root, justify="center", font=(current_font,BASE_FONT))
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=2)

tk.Button(btns,text="Generate",command=calculate).pack(side="left",padx=3)
tk.Button(btns,text="Clear",command=lambda: entry.delete(0,"end")).pack(side="left",padx=3)

ai_canvas = tk.Canvas(btns, bd=0, highlightthickness=0)
ai_canvas.pack(side="left",padx=4)
draw_ai_lamp()

res = tk.Frame(root)
res.pack(pady=4)

left_lbl = tk.Label(res,width=6,bg="red",fg="white")
middle_lbl = tk.Label(res,width=6,bg="white")
right_lbl = tk.Label(res,width=6,bg="green",fg="white")

left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

timer_lbl = tk.Label(root, font=(current_font, int(BASE_FONT*0.9)), fg="blue")

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

ai_menu = tk.Menu(menubar,tearoff=0)
ai_menu.add_command(label="Toggle AI",command=toggle_ai)
menubar.add_cascade(label="AI",menu=ai_menu)

root.mainloop()