import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}
AI_START_VALUES = {2,8,14,20,26,32,38,44,50,56}
AI_END_VALUES   = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
move_mode = False
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
root.geometry("500x360")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

night_bg = "#2E2E2E"
day_bg = "white"
ai_bg = "#ADD8E6"

# ================= FUNCTIONS =================
def calculate(event=None):
    global timer_running
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

    # AI logic
    if ai_mode and v in AI_START_VALUES:
        middle_lbl.config(text=f"{v} >\nNext", bg=ai_bg)
        if not timer_running:
            start_timer()
    elif ai_mode and v in AI_END_VALUES:
        middle_lbl.config(text=str(v), bg="white")
        stop_timer()
    elif v == m and v in SPECIAL_MIDDLES:
        middle_lbl.config(text=f"{m} =", bg="orange")
        stop_timer()
    else:
        sign = "=" if v==m else "<" if v<m else ">"
        middle_lbl.config(text=f"{m} {sign}", bg="white")
        stop_timer()

# ================= TIMER =================
timer_lbl = tk.Label(root, font=(current_font,int(BASE_FONT*0.8)), fg="blue", bg="white")

def start_timer():
    global timer_running
    if timer_running:
        return
    timer_running = True
    timer_lbl.config(text="00:59")
    timer_lbl.pack(pady=2)
    countdown(59)

def stop_timer():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id:
        root.after_cancel(timer_after_id)
        timer_after_id = None
    timer_lbl.pack_forget()

def countdown(sec):
    global timer_after_id, timer_running
    if not timer_running:
        return
    if sec < 0:
        stop_timer()
        return
    m, s = divmod(sec, 60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_after_id = root.after(1000, countdown, sec-1)

# ================= MODES =================
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)
    left_lbl.config(bg=left_lbl.cget("bg"), fg=left_lbl.cget("fg"))
    middle_lbl.config(bg=middle_lbl.cget("bg"), fg=middle_lbl.cget("fg"))
    right_lbl.config(bg=right_lbl.cget("bg"), fg=right_lbl.cget("fg"))
    for b in [calc_btn, clear_btn, pin_btn, scale_btn, alpha_btn, font_btn]:
        b.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)

# ================= MOVE =================
def enable_move():
    global move_mode
    move_mode = True
    root.config(cursor="fleur")

def start_move(e):
    if move_mode:
        root._x = e.x
        root._y = e.y

def move_window(e):
    if move_mode:
        root.geometry(f"+{e.x_root-root._x}+{e.y_root-root._y}")

def stop_move(e):
    global move_mode
    move_mode = False
    root.config(cursor="")

# ================= SCALE =================
def apply_scale(val):
    global current_scale
    current_scale = float(val)
    size = int(BASE_FONT*current_scale)
    for w in [entry,left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,size))

def open_scale_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+50}+{root.winfo_rooty()+50}")
    tk.Label(p,text="Scale").pack()
    s = tk.Scale(p, from_=0.7, to=1.5, resolution=0.05, orient="horizontal", command=apply_scale)
    s.set(current_scale)
    s.pack()
    tk.Button(p,text="X",command=p.destroy).pack()
    root.bind("<Button-1>",lambda e:p.destroy(), add="+")

# ================= TRANSPARENCY =================
def apply_alpha(val):
    root.attributes("-alpha", float(val))

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+80}+{root.winfo_rooty()+80}")
    tk.Label(p,text="Transparency").pack()
    s = tk.Scale(p, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", command=apply_alpha)
    s.set(root.attributes("-alpha"))
    s.pack()
    tk.Button(p,text="X",command=p.destroy).pack()
    root.bind("<Button-1>", lambda e:p.destroy(), add="+")

# ================= FONT =================
def open_font_popup():
    fonts = ["Segoe UI","Arial","Consolas","Times New Roman","Courier New",
             "Verdana","Tahoma","Impact","Georgia","Comic Sans MS"]
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+100}+{root.winfo_rooty()+100}")
    tk.Label(p,text="Select Font").pack()
    for f in fonts:
        tk.Button(p,text=f,command=lambda ff=f: set_font(ff)).pack(fill="x")
    tk.Button(p,text="X",command=p.destroy).pack()

def set_font(f):
    global current_font
    current_font = f
    for w in [entry,left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,int(BASE_FONT*current_scale)))

# ================= LIMIT EDIT =================
def edit_limits():
    global limits
    s = simpledialog.askstring("Edit Limits","Comma separated:",initialvalue=",".join(map(str,limits)))
    if s:
        limits = sorted(int(x.strip()) for x in s.split(","))
        with open(LIMITS_FILE,"w") as f:
            f.write(",".join(map(str,limits)))

# ================= UI =================
entry = tk.Entry(root, font=(current_font,BASE_FONT), justify="center")
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack(pady=5)
calc_btn = tk.Button(btns, text="Calculate", command=calculate)
calc_btn.pack(side="left", padx=5)
clear_btn = tk.Button(btns, text="Clear", command=lambda: entry.delete(0,tk.END))
clear_btn.pack(side="left", padx=5)
pin_btn = tk.Button(btns, text="Pin", command=toggle_top)
pin_btn.pack(side="left", padx=5)
scale_btn = tk.Button(btns, text="Scale", command=open_scale_popup)
scale_btn.pack(side="left", padx=5)
alpha_btn = tk.Button(btns, text="Transparency", command=open_alpha_popup)
alpha_btn.pack(side="left", padx=5)
font_btn = tk.Button(btns, text="Font", command=open_font_popup)
font_btn.pack(side="left", padx=5)

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res, width=6, bg="red", fg="white", font=(current_font, BASE_FONT))
middle_lbl = tk.Label(res, width=4, bg="white", font=(current_font, BASE_FONT))
right_lbl = tk.Label(res, width=6, bg="green", fg="white", font=(current_font, BASE_FONT))
left_lbl.pack(side="left", padx=5)
middle_lbl.pack(side="left", padx=5)
right_lbl.pack(side="left", padx=5)

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode

ai_menu = tk.Menu(root, tearoff=0)
ai_menu.add_command(label="Toggle AI", command=toggle_ai)
menubar = tk.Menu(root)
menubar.add_cascade(label="File", menu=tk.Menu(menubar, tearoff=0))
menubar.add_cascade(label="View", menu=tk.Menu(menubar, tearoff=0))
menubar.add_cascade(label="AI", menu=ai_menu)
root.config(menu=menubar)

# ================= BINDINGS =================
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", move_window)
root.bind("<ButtonRelease-1>", stop_move)

root.mainloop()