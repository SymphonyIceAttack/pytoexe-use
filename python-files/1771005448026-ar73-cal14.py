import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import os

# ================== CONSTANTS ==================
LIMITS_FILE = "limits.txt"
SETTINGS_FILE = "settings.txt"
BASE_FONT = 18
BTN_FONT = 12
BASE_WIDTH_LR = 6
BASE_WIDTH_M = 4
SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}

# ================== GLOBALS ==================
current_scale = 1.0
current_alpha = 0.8
topmost = True
dark_mode = False
history = []

# Move window globals
move_mode = False
offset_x = 0
offset_y = 0

# ================== LOAD LIMITS ==================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================== SETTINGS ==================
def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        f.write(f"{current_alpha},{current_scale},{int(dark_mode)},{int(topmost)}\n")

def load_settings():
    global current_alpha, current_scale, dark_mode, topmost
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                line = f.readline().strip()
                alpha, scale, dm, tm = line.split(",")
                current_alpha = float(alpha)
                current_scale = float(scale)
                dark_mode = bool(int(dm))
                topmost = bool(int(tm))
        except:
            pass

load_settings()

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
    if messagebox.askyesno("Confirm", "Clear all history?"):
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

    tk.Button(history_win, text="Clear History",
              command=clear_history).pack(pady=5)

    update_history()

# ================== CALCULATION ==================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        messagebox.showerror("Error", "Enter 1 or 2 digit number only")
        return

    value = int(txt)
    for i in range(len(limits) - 1):
        if limits[i] <= value <= limits[i + 1]:
            left = limits[i]
            right = limits[i + 1]
            break

    middle = left + 3
    if value < middle:
        mid_txt = f"{middle} <"
    elif value > middle:
        mid_txt = f"{middle} >"
    else:
        mid_txt = f"{middle} ="

    left_lbl.config(text=left)
    right_lbl.config(text=right)
    middle_lbl.config(text=mid_txt)
    if value == middle and value in SPECIAL_MIDDLES:
        middle_lbl.config(bg="orange")
    else:
        middle_lbl.config(bg="white")

    add_history(value, left, middle, right)

# ================== TOPMOST ==================
def toggle_top():
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)
    save_settings()

# ================== DARK MODE ==================
def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg=bg, fg=fg)
    left_lbl.config(bg=left_lbl.cget("bg"), fg=left_lbl.cget("fg"))
    middle_lbl.config(bg=middle_lbl.cget("bg"), fg=middle_lbl.cget("fg"))
    right_lbl.config(bg=right_lbl.cget("bg"), fg=right_lbl.cget("fg"))
    for b in buttons:
        b.config(bg="#777" if dark_mode else "#DDDDDD", fg=fg)
    save_settings()

# ================== LIMITS ==================
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

# ================== RESIZE & SCALE ==================
def resize(mode):
    sizes = {"small": "300x220", "medium": "420x280", "large": "520x340"}
    root.geometry(sizes[mode])

def set_scale(val):
    global current_scale
    current_scale = float(val)/100
    font_main = max(8, int(BASE_FONT * current_scale))
    font_btn = max(8, int(BTN_FONT * current_scale))

    entry.config(font=("Segoe UI", font_main))
    left_lbl.config(font=("Segoe UI", font_main),
                    width=max(3, int(BASE_WIDTH_LR * current_scale)))
    middle_lbl.config(font=("Segoe UI", font_main),
                      width=max(2, int(BASE_WIDTH_M * current_scale)))
    right_lbl.config(font=("Segoe UI", font_main),
                     width=max(3, int(BASE_WIDTH_LR * current_scale)))
    for b in buttons:
        b.config(font=("Segoe UI", font_btn))
    save_settings()

# ================== TRANSPARENCY ==================
def set_alpha(val):
    global current_alpha
    current_alpha = float(val)/100
    root.attributes("-alpha", current_alpha)
    save_settings()

# ================== MOVE WINDOW ==================
def enable_move_mode():
    global move_mode
    move_mode = True
    root.config(cursor="fleur")

def start_move(event):
    global offset_x, offset_y
    if move_mode:
        offset_x = event.x
        offset_y = event.y

def move_window(event):
    if move_mode:
        x = event.x_root - offset_x
        y = event.y_root - offset_y
        root.geometry(f"+{x}+{y}")

def stop_move(event):
    global move_mode
    if move_mode:
        move_mode = False
        root.config(cursor="")

# ================== UI ==================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x280")
root.attributes("-topmost", topmost)
root.attributes("-alpha", current_alpha)

# ---- Menu ----
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

# Scale slider
tk.Label(root, text="Scale (%)").pack()
scale_slider = tk.Scale(root, from_=5, to=200, orient="horizontal",
                        command=set_scale)
scale_slider.set(current_scale*100)
scale_slider.pack(fill="x", padx=10)

# Transparency slider
tk.Label(root, text="Transparency (%)").pack()
alpha_slider = tk.Scale(root, from_=10, to=100, orient="horizontal",
                        command=set_alpha)
alpha_slider.set(current_alpha*100)
alpha_slider.pack(fill="x", padx=10)

# Entry
entry = tk.Entry(root, font=("Segoe UI", BASE_FONT), justify="center")
entry.pack(pady=5)
entry.bind("<Return>", calculate)

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack()
calc_btn = tk.Button(btn_frame, text="Calculate", command=calculate)
clear_btn = tk.Button(btn_frame, text="Clear", command=lambda: entry.delete(0, tk.END))
calc_btn.pack(side="left", padx=5)
clear_btn.pack(side="left", padx=5)
buttons = [calc_btn, clear_btn]

# Labels
res_frame = tk.Frame(root)
res_frame.pack(pady=10)
left_lbl = tk.Label(res_frame, width=BASE_WIDTH_LR, font=("Segoe UI", BASE_FONT),
                    bg="red", fg="white")
middle_lbl = tk.Label(res_frame, width=BASE_WIDTH_M, font=("Segoe UI", BASE_FONT), bg="white")
right_lbl = tk.Label(res_frame, width=BASE_WIDTH_LR, font=("Segoe UI", BASE_FONT),
                     bg="green", fg="white")
left_lbl.pack(side="left", padx=5)
middle_lbl.pack(side="left", padx=5)
right_lbl.pack(side="left", padx=5)

# ================== BIND MOVE ==================
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", move_window)
root.bind("<ButtonRelease-1>", stop_move)

root.mainloop()
