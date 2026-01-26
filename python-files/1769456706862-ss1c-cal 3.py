import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================= SETTINGS =================
LIMITS_FILE = "limits.txt"
SETTINGS_FILE = "settings.txt"
SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}

COLOR_LEFT = "#B22222"     # Red
COLOR_RIGHT = "#228B22"    # Green
COLOR_MIDDLE = "white"
COLOR_SPECIAL = "#FF8C00"  # Orange

topmost = True
dark_mode = False
history = []

# ================= LOAD LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= LOAD WINDOW SETTINGS =================
win_width, win_height, win_x, win_y = 420, 280, 100, 100
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = f.read().split(",")
            if len(data) >= 4:
                win_width, win_height, win_x, win_y = map(int, data[:4])
    except:
        pass

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
    if history and messagebox.askyesno("Confirm", "Clear all history?"):
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

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)
    for lbl in [left_lbl, middle_lbl, right_lbl]:
        lbl.config(bg=lbl.cget("bg"))

def set_alpha(val):
    root.attributes("-alpha", float(val))

def resize(size):
    sizes = {"small":"300x220", "medium":"420x280", "large":"520x340"}
    root.geometry(sizes[size])

def save_window_position():
    global win_width, win_height, win_x, win_y
    win_width = root.winfo_width()
    win_height = root.winfo_height()
    win_x = root.winfo_x()
    win_y = root.winfo_y()
    with open(SETTINGS_FILE, "w") as f:
        f.write(f"{win_width},{win_height},{win_x},{win_y}")
    messagebox.showinfo("Saved", "Window size and position saved!")

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
    history_text = tk.Text(history_window, state="disabled", font=("Segoe UI", 11))
    history_text.pack(fill="both", expand=True, padx=5, pady=5)

    btn_frame = tk.Frame(history_window)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Clear History", bg="#B22222", fg="white", command=clear_history).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Close", command=history_window.destroy).pack(side="left", padx=5)

    update_history()

# ================= UI =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

# Menu Bar
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin", command=toggle_top)
file_menu.add_command(label="Night / Day Mode", command=toggle_mode)
file_menu.add_command(label="Edit Limits", command=edit_limits)
file_menu.add_command(label="History", command=open_history)

# Transparency submenu
trans_menu = tk.Menu(file_menu, tearoff=0)
file_menu.add_cascade(label="Transparency", menu=trans_menu)
for val in [0.3, 0.5, 0.7, 0.9]:
    trans_menu.add_command(label=str(val), command=lambda v=val: set_alpha(v))

# Resize submenu
resize_menu = tk.Menu(file_menu, tearoff=0)
file_menu.add_cascade(label="Resize", menu=resize_menu)
resize_menu.add_command(label="Small", command=lambda: resize("small"))
resize_menu.add_command(label="Medium", command=lambda: resize("medium"))
resize_menu.add_command(label="Large", command=lambda: resize("large"))

# Save window position
file_menu.add_separator()
file_menu.add_command(label="Save Window Size/Position", command=save_window_position)

# Entry
entry = tk.Entry(root, font=("Segoe UI", 18), justify="center")
entry.pack(pady=10)
entry.bind("<Return>", calculate)

# Buttons
btns = tk.Frame(root)
btns.pack()
calc_btn = tk.Button(btns, text="Calculate", command=calculate)
calc_btn.pack(side="left", padx=5)
clear_btn = tk.Button(btns, text="Clear", command=clear_input)
clear_btn.pack(side="left", padx=5)

# Result Labels أصغر 25% من قبل
res = tk.Frame(root)
res.pack(pady=10)
left_lbl = tk.Label(res, text="--", width=6, font=("Segoe UI", 16), bg=COLOR_LEFT, fg="white")
left_lbl.pack(side="left", padx=5)
middle_lbl = tk.Label(res, text="--", width=4, font=("Segoe UI", 16), bg=COLOR_MIDDLE)
middle_lbl.pack(side="left", padx=5)
right_lbl = tk.Label(res, text="--", width=6, font=("Segoe UI", 16), bg=COLOR_RIGHT, fg="white")
right_lbl.pack(side="left", padx=5)

# Shortcuts
root.bind("<Control-t>", lambda e: toggle_top())

root.mainloop()
