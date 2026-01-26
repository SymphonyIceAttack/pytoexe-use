import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================= SETTINGS =================
LIMITS_FILE = "limits.txt"
SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}

COLOR_LEFT = "#B22222"     # red
COLOR_RIGHT = "#228B22"    # green
COLOR_MIDDLE = "white"
COLOR_SPECIAL = "#FF8C00"  # orange

topmost = True
dark_mode = False
history = []

# ================= LOAD LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= HISTORY =================
def add_history(value, left, middle, right):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append(
        f"{len(history)+1}. Input={value} | L={left} M={middle} R={right} | {ts}"
    )
    update_history()

def update_history():
    if history_window and history_window.winfo_exists():
        history_text.config(state="normal")
        history_text.delete("1.0", tk.END)
        for h in history:
            history_text.insert(tk.END, h + "\n")
        history_text.config(state="disabled")

def clear_history():
    history.clear()
    update_history()

# ================= CALCULATION =================
def calculate(event=None):
    try:
        value = int(entry.get())
    except ValueError:
        messagebox.showerror("Error", "Enter a valid integer")
        return

    for i in range(len(limits)-1):
        if limits[i] <= value <= limits[i+1]:
            left = limits[i]
            right = limits[i+1]
            break

    middle = left + 3

    left_lbl.config(text=str(left), bg=COLOR_LEFT)
    right_lbl.config(text=str(right), bg=COLOR_RIGHT)
    middle_lbl.config(text=str(middle))

    if value == middle and value in SPECIAL_MIDDLES:
        middle_lbl.config(bg=COLOR_SPECIAL)
    else:
        middle_lbl.config(bg=COLOR_MIDDLE)

    add_history(value, left, middle, right)

def clear_input():
    entry.delete(0, tk.END)

# ================= LIMIT EDIT =================
def edit_limits():
    global limits
    text = simpledialog.askstring(
        "Edit Limits", "Comma separated numbers:", 
        initialvalue=",".join(map(str, limits))
    )
    if text:
        try:
            limits = sorted(int(x.strip()) for x in text.split(","))
            with open(LIMITS_FILE, "w") as f:
                f.write(",".join(map(str, limits)))
        except:
            messagebox.showerror("Error", "Invalid limits")

# ================= WINDOW OPTIONS =================
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)
    pin_btn.config(text="Unpin" if topmost else "Pin")

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)
    mode_btn.config(text="Day Mode" if dark_mode else "Night Mode")

def set_alpha(val):
    root.attributes("-alpha", float(val))

def resize(size):
    sizes = {"small":"300x250", "medium":"420x300", "large":"520x360"}
    root.geometry(sizes[size])

# ================= HISTORY WINDOW =================
history_window = None
def open_history():
    global history_window, history_text
    if history_window and history_window.winfo_exists():
        history_window.lift()
        return
    history_window = tk.Toplevel(root)
    history_window.title("History")
    history_window.geometry("520x300")
    history_text = tk.Text(history_window, state="disabled")
    history_text.pack(fill="both", expand=True)
    tk.Button(history_window, text="Clear History", command=clear_history).pack(pady=5)
    update_history()

# ================= UI =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x300")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

entry = tk.Entry(root, font=("Segoe UI", 18), justify="center")
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack()
tk.Button(btns, text="Calculate", command=calculate).pack(side="left", padx=5)
tk.Button(btns, text="Clear", command=clear_input).pack(side="left", padx=5)

res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res, text="--", width=8, font=("Segoe UI", 16), bg=COLOR_LEFT, fg="white")
left_lbl.pack(side="left", padx=5)
middle_lbl = tk.Label(res, text="--", width=6, font=("Segoe UI", 16), bg=COLOR_MIDDLE)
middle_lbl.pack(side="left", padx=5)
right_lbl = tk.Label(res, text="--", width=8, font=("Segoe UI", 16), bg=COLOR_RIGHT, fg="white")
right_lbl.pack(side="left", padx=5)

pin_btn = tk.Button(root, text="Unpin", command=toggle_top)
pin_btn.pack(pady=3)

mode_btn = tk.Button(root, text="Night Mode", command=toggle_mode)
mode_btn.pack(pady=3)

tk.Button(root, text="Edit Limits", command=edit_limits).pack(pady=3)
tk.Button(root, text="History", command=open_history).pack(pady=3)

tk.Scale(root, from_=0.3, to=1.0, resolution=0.05,
         orient="horizontal", label="Transparency",
         command=set_alpha).pack()

resize_f = tk.Frame(root)
resize_f.pack(pady=5)
tk.Button(resize_f, text="Small", command=lambda: resize("small")).pack(side="left", padx=3)
tk.Button(resize_f, text="Medium", command=lambda: resize("medium")).pack(side="left", padx=3)
tk.Button(resize_f, text="Large", command=lambda: resize("large")).pack(side="left", padx=3)

root.bind("<Control-t>", lambda e: toggle_top())

root.mainloop()
