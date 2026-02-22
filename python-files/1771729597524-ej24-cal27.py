import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0
current_font = "Segoe UI"

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
history = []
move_mode = False
current_group_idx = 0

# ================= LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE) as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0,6,12,18,24,30,36,42,48,54,60]

# ================= ROOT =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x280")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

# ================= FUNCTIONS =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        messagebox.showerror("Error","Enter 1 or 2 digits only")
        return

    v = int(txt)
    for i in range(len(limits)-1):
        if limits[i] <= v <= limits[i+1]:
            l, r = limits[i], limits[i+1]
            break
    else:
        l, r = 0, 0

    m = l + 3
    sign = "=" if v == m else "<" if v < m else ">"
    middle_lbl.config(text=f"{m} {sign}")

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    # Day/Night white label behavior from old version
    if v == m and v in SPECIAL_MIDDLES:
        middle_lbl.config(bg="orange")
    else:
        middle_lbl.config(bg=night_bg if dark_mode else "white")

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
    history_text = tk.Text(history_win,state="disabled", font=(current_font,int(BASE_FONT*current_scale)))
    history_text.pack(fill="both",expand=True)
    tk.Button(history_win,text="Clear History",command=clear_history).pack(pady=5)
    update_history()

# ================= MODES =================
night_bg = "#2E2E2E"
night_fg = "white"
day_bg = "white"
day_fg = "black"

def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = night_bg if dark_mode else day_bg
    fg = night_fg if dark_mode else day_fg
    root.config(bg=bg)
    entry.config(bg=bg,fg=fg)
    left_lbl.config(bg="red", fg=fg)
    middle_lbl.config(bg=night_bg if dark_mode else "white", fg=fg)
    right_lbl.config(bg="green", fg=fg)
    for b in [calc_btn, clear_btn, prev_btn, next_btn, pin_btn, edit_btn, history_btn, view_btn]:
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
    button_size = max(1,int(size*0.8))
    label_size = max(1,int(size*1.05))
    entry.config(font=(current_font,size))
    for w in [calc_btn, clear_btn, prev_btn, next_btn]:
        w.config(font=(current_font,button_size))
    for w in [left_lbl,middle_lbl,right_lbl]:
        w.config(font=(current_font,label_size))

def open_scale_popup():
    p = tk.Toplevel(root)
    p.title("Scale / Font Size")
    p.geometry("300x80")
    p.resizable(False, False)
    def on_zoom(val):
        apply_scale(val)
    scale = tk.Scale(p, from_=0.7, to=1.5, resolution=0.05, orient="horizontal", label="Font Size", command=on_zoom)
    scale.set(current_scale)
    scale.pack(fill="x", padx=10, pady=10)

# ================= TRANSPARENCY =================
def apply_alpha(val):
    root.attributes("-alpha",float(val))

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry(f"+{root.winfo_rootx()+80}+{root.winfo_rooty()+80}")
    tk.Label(p,text="Transparency").pack()
    s = tk.Scale(p,from_=0.3,to=1.0,resolution=0.05,orient="horizontal",command=apply_alpha)
    s.set(root.attributes("-alpha"))
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
    apply_scale(current_scale)

# ================= LIMIT EDIT =================
def edit_limits():
    global limits
    s = simpledialog.askstring("Edit Limits","Comma separated:",initialvalue=",".join(map(str,limits)))
    if s:
        limits = sorted(int(x.strip()) for x in s.split(","))
        with open(LIMITS_FILE,"w") as f:
            f.write(",".join(map(str,limits)))

# ================= GROUP NAVIGATION =================
def prev_group(event=None):
    global current_group_idx
    current_group_idx -= 1
    if current_group_idx < 0:
        current_group_idx = len(limits)-2
    entry.delete(0,tk.END)
    entry.insert(0,str(limits[current_group_idx]))
    calculate()
    return "break"

def next_group(event=None):
    global current_group_idx
    current_group_idx += 1
    if current_group_idx >= len(limits)-1:
        current_group_idx = 0
    entry.delete(0,tk.END)
    entry.insert(0,str(limits[current_group_idx]))
    calculate()
    return "break"

# ================= UI =================
entry = tk.Entry(root,font=(current_font,BASE_FONT),justify="center")
entry.pack(pady=5)
entry.bind("<Return>",calculate)

btns = tk.Frame(root)
btns.pack(pady=2)
calc_btn = tk.Button(btns,text="Calculate",command=calculate)
calc_btn.pack(side="left",padx=3)
clear_btn = tk.Button(btns,text="Clear",command=lambda: entry.delete(0,tk.END))
clear_btn.pack(side="left",padx=3)
prev_btn = tk.Button(btns,text="◀",command=prev_group)
prev_btn.pack(side="left",padx=3)
next_btn = tk.Button(btns,text="▶",command=next_group)
next_btn.pack(side="left",padx=3)

res = tk.Frame(root)
res.pack(pady=5)
left_lbl = tk.Label(res,width=6,bg="red",fg="white",font=(current_font,BASE_FONT))
middle_lbl = tk.Label(res,width=4,bg="white",font=(current_font,BASE_FONT))
right_lbl = tk.Label(res,width=6,bg="green",fg="white",font=(current_font,BASE_FONT))
left_lbl.pack(side="left")
middle_lbl.pack(side="left")
right_lbl.pack(side="left")

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Pin / Unpin",command=toggle_top)
file_menu.add_command(label="Edit Limits",command=edit_limits)
file_menu.add_command(label="History",command=open_history)
menubar.add_cascade(label="File", menu=file_menu)

view_menu = tk.Menu(menubar, tearoff=0)
view_menu.add_command(label="Day / Night",command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Move Window",command=enable_move)
view_menu.add_separator()
view_menu.add_command(label="Scale",command=open_scale_popup)
view_menu.add_command(label="Transparency",command=open_alpha_popup)
view_menu.add_command(label="Font",command=open_font_popup)
menubar.add_cascade(label="View", menu=view_menu)

# ================= KEY BINDINGS =================
root.bind("<Left>",prev_group)
root.bind("<Right>",next_group)

# ================= MOVE BINDINGS =================
root.bind("<Button-1>",start_move)
root.bind("<B1-Motion>",move_window)
root.bind("<ButtonRelease-1>",stop_move)

root.mainloop()