import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import os

# ================== CONSTANTS ==================
LIMITS_FILE = "limits.txt"
BASE_FONT = 18
BTN_FONT = 12
BASE_WIDTH_LR = 6
BASE_WIDTH_M = 4
SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}

# ================== GLOBALS ==================
current_scale = 1.0
topmost = True
dark_mode = False
history = []

# ================== LOAD LIMITS ==================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================== FUNCTIONS ==================
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

def clear_input():
    entry.delete(0, tk.END)

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

def resize(mode):
    sizes = {"small": "300x220", "medium": "420x280", "large": "520x340"}
    root.geometry(sizes[mode])

def set_scale(percent):
    global current_scale
    current_scale = 1.0 - (percent / 100)

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

# ================== UI ==================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x280")
root.attributes("-topmost", True)

# ================== MENU ==================
menubar = tk.Menu(root)
root.config(menu=menubar)

# ---- File Menu
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Pin / Unpin", command=toggle_top)
file_menu.add_command(label="Edit Limits", command=edit_limits)
file_menu.add_command(label="History", command=open_history)

# ---- View Menu
view_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="View", menu=view_menu)

view_menu.add_command(label="Day / Night", command=toggle_mode)

scale_menu = tk.Menu(view_menu, tearoff=0)
view_menu.add_cascade(label="Scale (%)", menu=scale_menu)
for p in [5, 10, 15, 20, 25, 30, 35]:
    scale_menu.add_command(label=f"{p}%", command=lambda x=p: set_scale(x))

resize_menu = tk.Menu(view_menu, tearoff=0)
view_menu.add_cascade(label="Resize", menu=resize_menu)
resize_menu.add_command(label="Small", command=lambda: resize("small"))
resize_menu.add_command(label="Medium", command=lambda: resize("medium"))
resize_menu.add_command(label="Large", command=lambda: resize("large"))

# ================== CONTENT ==================
entry = tk.Entry(root, font=("Segoe UI", BASE_FONT), justify="center")
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btn_frame = tk.Frame(root)
btn_frame.pack()

calc_btn = tk.Button(btn_frame, text="Calculate", command=calculate)
clear_btn = tk.Button(btn_frame, text="Clear", command=clear_input)

calc_btn.pack(side="left", padx=5)
clear_btn.pack(side="left", padx=5)

buttons = [calc_btn, clear_btn]

res_frame = tk.Frame(root)
res_frame.pack(pady=10)

left_lbl = tk.Label(res_frame, width=BASE_WIDTH_LR,
                    font=("Segoe UI", BASE_FONT),
                    bg="red", fg="white")
middle_lbl = tk.Label(res_frame, width=BASE_WIDTH_M,
                      font=("Segoe UI", BASE_FONT),
                      bg="white")
right_lbl = tk.Label(res_frame, width=BASE_WIDTH_LR,
                     font=("Segoe UI", BASE_FONT),
                     bg="green", fg="white")

left_lbl.pack(side="left", padx=5)
middle_lbl.pack(side="left", padx=5)
right_lbl.pack(side="left", padx=5)

history_win = None

root.mainloop()
