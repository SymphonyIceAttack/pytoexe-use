import tkinter as tk
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}
AI_START = {2,8,14,20,26,32,38,44,50,56}
AI_END   = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
history = []
current_group_idx = 0
ai_mode = False
timer_running = False
timer_after_id = None
timer_seconds = 60

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("500x360")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= TIMER =================
def start_timer():
    global timer_running, timer_seconds
    if timer_running:
        return
    timer_running = True
    timer_seconds = 60
    timer_lbl.pack(pady=2)
    root.after(1000, countdown)

def stop_timer():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id:
        root.after_cancel(timer_after_id)
        timer_after_id = None
    timer_lbl.pack_forget()

def countdown():
    global timer_running, timer_seconds, timer_after_id
    if not timer_running:
        return
    if timer_seconds <= 0:
        stop_timer()
        return
    m, s = divmod(timer_seconds, 60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_seconds -= 1
    timer_after_id = root.after(1000, countdown)

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
    if ai_mode and v in AI_START:
        middle_lbl.config(text=f"{v} >\nNext", bg=ai_bg)
        root.after(1000, start_timer)  # يبدأ بعد ثانية واحدة
    elif ai_mode and v in AI_END:
        middle_lbl.config(text=str(v), bg="white")
        stop_timer()
    elif v == m and v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer()
    else:
        sign = "=" if v==m else "<" if v<m else ">"
        middle_lbl.config(text=f"{m} {sign}", bg=night_bg if dark_mode else "white")
        stop_timer()

# ================= HISTORY =================
def add_history(v,l,m,r):
    ts = datetime.now().strftime("%H:%M:%S")
    history.append(f"{v} → {l}-{m}-{r} | {ts}")

def open_history():
    w = tk.Toplevel(root)
    w.title("History")
    t = tk.Text(w)
    t.pack(fill="both",expand=True)
    for h in history:
        t.insert("end",h+"\n")

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
tk.Button(btns,text="◀",command=lambda: navigate(-1)).pack(side="left",padx=3)
tk.Button(btns,text="▶",command=lambda: navigate(1)).pack(side="left",padx=3)

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

timer_lbl = tk.Label(root, font=(current_font,int(BASE_FONT*0.9)), fg="blue")

# ================= NAVIGATION =================
def navigate(step):
    global current_group_idx
    current_group_idx = (current_group_idx + step) % (len(limits)-1)
    entry.delete(0,"end")
    entry.insert(0,limits[current_group_idx])
    calculate()

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar,tearoff=0)
file_menu.add_command(label="Pin / Unpin", command=lambda: root.attributes("-topmost", not root.attributes("-topmost")))
file_menu.add_command(label="History", command=open_history)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar,tearoff=0)
view_menu.add_command(label="Day / Night", command=lambda: toggle_dark())
view_menu.add_command(label="Scale", command=lambda: open_scale_popup())
menubar.add_cascade(label="View", menu=view_menu)

ai_menu = tk.Menu(menubar,tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
menubar.add_cascade(label="AI", menu=ai_menu)

# ================= VIEW & SCALE =================
def toggle_dark():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    middle_lbl.config(bg="white")
    draw_ai_lamp()

def open_scale_popup():
    p = tk.Toplevel(root)
    tk.Scale(
        p,
        from_=0.7,
        to=1.5,
        resolution=0.05,
        orient="horizontal",
        command=apply_scale
    ).pack(fill="x")

def apply_scale(val):
    global current_scale
    current_scale = float(val)
    size = int(BASE_FONT*current_scale)
    entry.config(font=(current_font,size))
    for w in [left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,int(size*1.05)))
    draw_ai_lamp()

# ================= RUN =================
root.bind("<Left>", lambda e: navigate(-1))
root.bind("<Right>", lambda e: navigate(1))
root.mainloop()