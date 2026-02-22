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
AI_STOP_VALUES = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
ai_mode = False
timer_running = False
timer_after_id = None
timer_seconds = 0

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
    global timer_running, timer_seconds
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        return
    v = int(txt)
    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l,r = limits[i],limits[i+1]
            break
    m = l + 3

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    # AI handling
    if ai_mode and v in AI_START_VALUES:
        middle_lbl.config(
            text=f"{v} >\nNext",
            bg=ai_bg,
            font=(current_font, int(BASE_FONT*current_scale*1.05)),
            justify="center",
            anchor="center",
            pady=1
        )
        if not timer_running:
            timer_seconds = 59
            timer_lbl.pack(pady=2)
            timer_running = True
            run_timer()
    elif ai_mode and v in AI_STOP_VALUES:
        middle_lbl.config(
            text=str(v),
            bg="white",
            font=(current_font, int(BASE_FONT*current_scale*1.05))
        )
        stop_timer()
    else:
        sign = "=" if v==m else "<" if v<m else ">"
        middle_lbl.config(
            text=f"{m} {sign}",
            bg=night_bg if dark_mode else "white",
            font=(current_font, int(BASE_FONT*current_scale*1.05)),
            justify="center",
            anchor="center",
            pady=1
        )
        stop_timer()

# ================= TIMER =================
def run_timer():
    global timer_seconds, timer_after_id, timer_running
    if timer_seconds < 0 or not timer_running:
        timer_running = False
        timer_lbl.pack_forget()
        return
    m,s = divmod(timer_seconds,60)
    timer_lbl.config(text=f"{m:02d}:{s:02d}")
    timer_seconds -= 1
    timer_after_id = root.after(1000, run_timer)

def stop_timer():
    global timer_running, timer_after_id
    timer_running = False
    if timer_after_id:
        root.after_cancel(timer_after_id)
        timer_after_id = None
    timer_lbl.pack_forget()

# ================= UI =================
entry = tk.Entry(root,font=(current_font,BASE_FONT),justify="center")
entry.pack(pady=5)
entry.bind("<Return>",calculate)

btns = tk.Frame(root)
btns.pack(pady=2)
calc_btn = tk.Button(btns,text="Generate",command=calculate)
calc_btn.pack(side="left",padx=3)
clear_btn = tk.Button(btns,text="Clear",command=lambda: entry.delete(0,"end"))
clear_btn.pack(side="left",padx=3)

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res,width=6,bg="red",fg="white",font=(current_font,BASE_FONT))
middle_lbl = tk.Label(res,width=4,bg="white",font=(current_font,BASE_FONT))
right_lbl = tk.Label(res,width=6,bg="green",fg="white",font=(current_font,BASE_FONT))
left_lbl.pack(side="left",padx=5)
middle_lbl.pack(side="left",padx=5)
right_lbl.pack(side="left",padx=5)

timer_lbl = tk.Label(root,font=(current_font,int(BASE_FONT*0.9)),fg="blue")

# ================= MODES =================
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost",topmost)

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    for lbl in [left_lbl,middle_lbl,right_lbl]:
        lbl.config(bg=lbl.cget("bg"),fg=lbl.cget("fg"))

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
    s=tk.Scale(p,from_=0.7,to=1.5,resolution=0.05,orient="horizontal",command=apply_scale)
    s.set(current_scale)
    s.pack()
    tk.Button(p,text="X",command=p.destroy).pack()
    root.bind("<Button-1>",lambda e:p.destroy(), add="+")

# ================= TRANSPARENCY =================
def apply_alpha(val):
    root.attributes("-alpha",float(val))

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+80}+{root.winfo_rooty()+80}")
    tk.Label(p,text="Transparency").pack()
    s=tk.Scale(p,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",command=apply_alpha)
    s.set(root.attributes("-alpha"))
    s.pack()
    tk.Button(p,text="X",command=p.destroy).pack()
    root.bind("<Button-1>",lambda e:p.destroy(), add="+")

# ================= FONT =================
def open_font_popup():
    fonts = ["Segoe UI","Arial","Consolas","Times New Roman","Courier New",
             "Verdana","Tahoma","Impact","Georgia","Comic Sans MS"]
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+100}+{root.winfo_rooty()+100}")
    tk.Label(p,text="Select Font").pack()
    for f in fonts:
        tk.Button(p,text=f,command=lambda ff=f:set_font(ff)).pack(fill="x")
    tk.Button(p,text="X",command=p.destroy).pack()

def set_font(f):
    global current_font
    current_font=f
    for w in [entry,left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,int(BASE_FONT*current_scale)))

# ================= LIMITS =================
def edit_limits():
    global limits
    s = simpledialog.askstring("Edit Limits","Comma separated:",initialvalue=",".join(map(str,limits)))
    if s:
        limits = sorted(int(x.strip()) for x in s.split(","))
        with open(LIMITS_FILE,"w") as f:
            f.write(",".join(map(str,limits)))

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar,tearoff=0)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="Edit Limits",command=edit_limits)
menubar.add_cascade(label="File",menu=file_menu)

view_menu = tk.Menu(menubar,tearoff=0)
view_menu.add_command(label="Day / Night",command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Scale",command=open_scale_popup)
view_menu.add_command(label="Transparency",command=open_alpha_popup)
view_menu.add_command(label="Font",command=open_font_popup)
menubar.add_cascade(label="View",menu=view_menu)

ai_menu = tk.Menu(menubar,tearoff=0)
ai_menu.add_command(label="Toggle AI",command=lambda:toggle_ai())
menubar.add_cascade(label="AI",menu=ai_menu)

# ================= AI =================
def toggle_ai():
    global ai_mode
    ai_mode = not ai_mode

root.mainloop()