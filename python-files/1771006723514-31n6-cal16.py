import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================== CONSTANTS ==================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18

SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}

# ================== GLOBALS ==================
topmost = True
dark_mode = False
history = []
move_mode = False
offset_x = offset_y = 0

# ================== LIMITS ==================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================== HISTORY ==================
history_win = None
history_text = None

def add_history(v, l, m, r):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append(f"{len(history)+1}. {v} | {l}-{m}-{r} | {ts}")
    update_history()

def update_history():
    if history_win and history_win.winfo_exists():
        history_text.config(state="normal")
        history_text.delete("1.0", tk.END)
        for h in history:
            history_text.insert(tk.END, h + "\n")
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

    history_text = tk.Text(history_win, state="disabled")
    history_text.pack(fill="both", expand=True)

    tk.Button(history_win, text="Clear History", command=clear_history).pack(pady=5)
    update_history()

# ================== CALCULATION ==================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        messagebox.showerror("Error", "Enter only 1 or 2 digits")
        return

    value = int(txt)

    for i in range(len(limits)-1):
        if limits[i] <= value <= limits[i+1]:
            left = limits[i]
            right = limits[i+1]
            break

    middle = left + 3

    if value < middle:
        mid_text = f"{middle} <"
    elif value > middle:
        mid_text = f"{middle} >"
    else:
        mid_text = f"{middle} ="

    left_lbl.config(text=left)
    right_lbl.config(text=right)
    middle_lbl.config(text=mid_text)

    if value == middle and value in SPECIAL_MIDDLES:
        middle_lbl.config(bg="orange")
    else:
        middle_lbl.config(bg="white")

    add_history(value, left, middle, right)

# ================== MODES ==================
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

# ================== LIMIT EDIT ==================
def edit_limits():
    global limits
    txt = simpledialog.askstring(
        "Edit Limits",
        "Comma separated limits:",
        initialvalue=",".join(map(str, limits))
    )
    if txt:
        try:
            limits = sorted(int(x.strip()) for x in txt.split(","))
            with open(LIMITS_FILE, "w") as f:
                f.write(",".join(map(str, limits)))
        except:
            messagebox.showerror("Error", "Invalid limits")

# ================== RESIZE ==================
def resize(mode):
    sizes = {
        "small": "300x220",
        "medium": "420x280",
        "large": "520x340"
    }
    root.geometry(sizes[mode])

# ================== MOVE WINDOW ==================
def enable_move():
    global move_mode
    move_mode = True
    root.config(cursor="fleur")

def start_move(e):
    global offset_x, offset_y
    if move_mode:
        offset_x = e.x
        offset_y = e.y

def move_window(e):
    if move_mode:
        root.geometry(f"+{e.x_root-offset_x}+{e.y_root-offset_y}")

def stop_move(e):
    global move_mode
    if move_mode:
        move_mode = False
        root.config(cursor="")

# ================== UI ==================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x280")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.85)

# ================== MENU ==================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin", command=toggle_top)
file_menu.add_command(label="Edit Limits", command=edit_limits)
file_menu.add_command(label="History", command=open_history)

view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)

view_menu.add_command(label="Day / Night", command=toggle_mode)
view_menu.add_separator()
view_menu.add_command(label="Move Window", command=enable_move)
view_menu.add_separator()

resize_menu = tk.Menu(view_menu, tearoff=0)
resize_menu.add_command(label="Small", command=lambda: resize("small"))
resize_menu.add_command(label="Medium", command=lambda: resize("medium"))
resize_menu.add_command(label="Large", command=lambda: resize("large"))
view_menu.add_cascade(label="Resize", menu=resize_menu)

# ================== CONTENT ==================
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
root.bind("<B1-Motion>", move_window)
root.bind("<ButtonRelease-1>", stop_move)

root.mainloop()
