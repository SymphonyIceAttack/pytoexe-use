import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from datetime import datetime
import json, os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
CONFIG_FILE = "config.json"
BASE_FONT = 18
SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}

# ================= DEFAULTS =================
limits = [0,6,12,18,24,30,36,42,48,54,60]
current_font = "Segoe UI"
current_scale = 1.0
topmost = True
dark_mode = False
history = []
move_mode = False
global_alpha = 0.9
auto_glass = False

# ================= LOAD LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))

# ================= LOAD SETTINGS =================
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
            current_font = config.get("font", current_font)
            current_scale = config.get("scale", current_scale)
            topmost = config.get("topmost", topmost)
            dark_mode = config.get("dark_mode", dark_mode)
            global_alpha = config.get("alpha", global_alpha)
            auto_glass = config.get("auto_glass", auto_glass)
    except:
        pass

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x280")
root.attributes("-topmost", topmost)
root.attributes("-alpha", global_alpha)

# ================= FUNCTIONS =================
def save_settings():
    config = {
        "font": current_font,
        "scale": current_scale,
        "topmost": topmost,
        "dark_mode": dark_mode,
        "alpha": global_alpha,
        "auto_glass": auto_glass
    }
    with open(CONFIG_FILE,"w") as f:
        json.dump(config,f)

def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt)>2:
        messagebox.showerror("Error","Enter 1 or 2 digits only")
        return
    v = int(txt)
    l=r=None
    for i in range(len(limits)-1):
        if limits[i]<=v<=limits[i+1]:
            l,r = limits[i],limits[i+1]
            break
    m = l + 3
    sign = "=" if v==m else "<" if v<m else ">"
    middle_lbl.config(text=f"{m} {sign}")
    left_lbl.config(text=l)
    right_lbl.config(text=r)
    if v==m and v in SPECIAL_MIDDLES:
        middle_lbl.config(bg="orange")
    else:
        middle_lbl.config(bg="white")
    add_history(v,l,m,r)

# ================= HISTORY =================
history_win = None
history_text = None

def add_history(v,l,m,r):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append(f"{len(history)+1}. {v} | {l}-{m}-{r} | {ts}")
    update_history()

def update_history():
    if history_win and history_win.winfo_exists():
        history_text.config(state="normal")
        history_text.delete("1.0", tk.END)
        for h in history:
            history_text.insert(tk.END,h+"\n")
        history_text.config(state="disabled")

def clear_history():
    history.clear()
    update_history()

def open_history():
    global history_win, history_text
    if history_win and history_win.winfo_exists():
        history_win.lift()
        return
    history_win = tk.Toplevel(root)
    history_win.title("History")
    history_win.geometry("520x300")
    history_text = tk.Text(history_win,state="disabled")
    history_text.pack(fill="both",expand=True)
    tk.Button(history_win,text="Clear History",command=clear_history).pack(pady=5)
    update_history()

# ================= MODES =================
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)
    save_settings()

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    left_lbl.config(bg=left_lbl.cget("bg"), fg=left_lbl.cget("fg"))
    middle_lbl.config(bg=middle_lbl.cget("bg"), fg=middle_lbl.cget("fg"))
    right_lbl.config(bg=right_lbl.cget("bg"), fg=right_lbl.cget("fg"))
    for b in [calc_btn, clear_btn, pin_btn, edit_btn, history_btn, view_btn]:
        b.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    save_settings()

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
    save_settings()

def open_scale_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+50}+{root.winfo_rooty()+50}")
    tk.Label(p,text="Scale").pack()
    s = tk.Scale(p,from_=0.7,to=1.5,resolution=0.05,orient="horizontal",command=apply_scale)
    s.set(current_scale)
    s.pack()
    tk.Button(p,text="X",command=p.destroy).pack()
    root.bind("<Button-1>",lambda e:p.destroy(), add="+")

# ================= TRANSPARENCY =================
def apply_alpha(val):
    global global_alpha
    global_alpha = float(val)
    root.attributes("-alpha",global_alpha)
    save_settings()

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+80}+{root.winfo_rooty()+80}")
    tk.Label(p,text="Transparency").pack()
    s = tk.Scale(p,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",command=apply_alpha)
    s.set(global_alpha)
    s.pack()
    tk.Button(p,text="X",command=p.destroy).pack()
    root.bind("<Button-1>",lambda e:p.destroy(), add="+")

# ================= FONT SELECTION =================
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
    save_settings()

# ================= LIMIT EDIT =================
def edit_limits():
    global limits
    s = simpledialog.askstring("Edit Limits","Comma separated:",initialvalue=",".join(map(str,limits)))
    if s:
        limits = sorted(int(x.strip()) for x in s.split(","))
        with open(LIMITS_FILE,"w") as f:
            f.write(",".join(map(str,limits)))

# ================= UI =================
entry = tk.Entry(root,font=(current_font,int(BASE_FONT*current_scale)),justify="center")
entry.pack(pady=5)
entry.bind("<Return>",calculate)

btns = tk.Frame(root)
btns.pack()
calc_btn = tk.Button(btns,text="Calculate",command=calculate)
calc_btn.pack(side="left",padx=5)
clear_btn = tk.Button(btns,text="Clear",command=lambda: entry.delete(0,tk.END))
clear_btn.pack(side="left",padx=5)

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res,width=6,bg="red",fg="white",font=(current_font,int(BASE_FONT*current_scale)))
middle_lbl = tk.Label(res,width=4,bg="white",font=(current_font,int(BASE_FONT*current_scale)))
right_lbl = tk.Label(res,width=6,bg="green",fg="white",font=(current_font,int(BASE_FONT*current_scale)))
left_lbl.pack(side="left",padx=5)
middle_lbl.pack(side="left",padx=5)
right_lbl.pack(side="left",padx=5)

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="Edit Limits",command=edit_limits)
file_menu.add_command(label="History",command=open_history)

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Day / Night",command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Move Window",command=enable_move)
view_menu.add_separator()
view_menu.add_command(label="Scale",command=open_scale_popup)
view_menu.add_command(label="Transparency",command=open_alpha_popup)
view_menu.add_command(label="Font",command=open_font_popup)

root.bind("<Button-1>",start_move)
root.bind("<B1-Motion>",move_window)
root.bind("<ButtonRelease-1>",stop_move)

# ================= AUTO-GLASS =================
def toggle_auto_glass():
    global auto_glass
    auto_glass = not auto_glass
    status = "ON" if auto_glass else "OFF"
    alpha_btn.config(text=f"Auto-Glass: {status}")
    save_settings()

def on_enter(e):
    if auto_glass:
        root.attributes("-alpha",1.0)
def on_leave(e):
    if auto_glass:
        root.attributes("-alpha",0.4)
    else:
        root.attributes("-alpha",global_alpha)

alpha_btn = tk.Button(root,text=f"Auto-Glass: {'ON' if auto_glass else 'OFF'}",command=toggle_auto_glass)
alpha_btn.pack(pady=2)
root.bind("<Enter>",on_enter)
root.bind("<Leave>",on_leave)

root.mainloop()
