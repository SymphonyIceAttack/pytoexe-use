import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================= CONFIG =================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
current_scale = 1.0

SPECIAL_MIDDLES = {3,9,15,21,27,33,39,45,51,57}

topmost = True
dark_mode = False
history = []
move_mode = False

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

    m = l + 3
    sign = "=" if v == m else "<" if v < m else ">"
    middle_lbl.config(text=f"{m} {sign}")

    left_lbl.config(text=l)
    right_lbl.config(text=r)

    if v == m and v in SPECIAL_MIDDLES:
        middle_lbl.config(bg="orange")
    else:
        middle_lbl.config(bg="white")

def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)

def edit_limits():
    global limits
    s = simpledialog.askstring("Edit Limits","Comma separated:",initialvalue=",".join(map(str,limits)))
    if s:
        limits = sorted(int(x.strip()) for x in s.split(","))
        with open(LIMITS_FILE,"w") as f:
            f.write(",".join(map(str,limits)))

# ================= MOVE =================
def enable_move():
    global move_mode
    move_mode = True
    root.config(cursor="fleur")

def start_move(e):
    if move_mode:
        root._x = e.x
        root._y = e.y

def move(e):
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
    size = int(BASE_FONT * current_scale)

    for w in [entry, left_lbl, middle_lbl, right_lbl]:
        w.config(font=("Segoe UI", size))

def open_scale_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry("+{}+{}".format(root.winfo_rootx()+50, root.winfo_rooty()+50))

    s = tk.Scale(p, from_=0.7, to=1.5, resolution=0.05,
                 orient="horizontal", command=apply_scale)
    s.set(current_scale)
    s.pack()

    root.bind("<Button-1>", lambda e: p.destroy(), add="+")

# ================= TRANSPARENCY =================
def apply_alpha(val):
    root.attributes("-alpha", float(val))

def open_alpha_popup():
    p = tk.Toplevel(root)
    p.overrideredirect(True)
    p.geometry("+{}+{}".format(root.winfo_rootx()+80, root.winfo_rooty()+80))

    s = tk.Scale(p, from_=0.3, to=1.0, resolution=0.05,
                 orient="horizontal", command=apply_alpha)
    s.set(root.attributes("-alpha"))
    s.pack()

    root.bind("<Button-1>", lambda e: p.destroy(), add="+")

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin", command=toggle_top)
file_menu.add_command(label="Edit Limits", command=edit_limits)

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)
view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Move Window", command=enable_move)
view_menu.add_separator()
view_menu.add_command(label="Scale", command=open_scale_popup)
view_menu.add_command(label="Transparency", command=open_alpha_popup)

# ================= UI =================
entry = tk.Entry(root, font=("Segoe UI", BASE_FONT), justify="center")
entry.pack(pady=5)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack()

tk.Button(btns, text="Calculate", command=calculate).pack(side="left", padx=5)
tk.Button(btns, text="Clear", command=lambda: entry.delete(0, tk.END)).pack(side="left", padx=5)

res = tk.Frame(root)
res.pack(pady=10)

left_lbl = tk.Label(res, width=6, bg="red", fg="white", font=("Segoe UI", BASE_FONT))
middle_lbl = tk.Label(res, width=4, bg="white", font=("Segoe UI", BASE_FONT))
right_lbl = tk.Label(res, width=6, bg="green", fg="white", font=("Segoe UI", BASE_FONT))

left_lbl.pack(side="left", padx=5)
middle_lbl.pack(side="left", padx=5)
right_lbl.pack(side="left", padx=5)

root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", move)
root.bind("<ButtonRelease-1>", stop_move)

root.mainloop()
