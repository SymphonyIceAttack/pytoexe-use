import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ================= FILES =================
LIMITS_FILE = "limits.txt"

# ================= DATA =================
SPECIAL_MIDDLES = {3, 9, 15, 21, 27, 33, 39, 45, 51, 57}
history = []
topmost = True
dark_mode = False

# ================= LOAD LIMITS =================
if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted(int(x) for x in f.read().split(","))
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

# ================= HISTORY =================
def add_history(value, left, middle, right):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append(f"{len(history)+1}. {value} | {left}-{middle}-{right} | {ts}")
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

# ================= CALC =================
def calculate(event=None):
    txt = entry.get().strip()
    if not txt.isdigit() or len(txt) > 2:
        messagebox.showerror("Error", "Enter 1 or 2 digit number only")
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

def clear_input():
    entry.delete(0, tk.END)

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

def set_alpha(val):
    root.attributes("-alpha", float(val))

def resize(size):
    sizes = {"small":"300x220","medium":"420x280","large":"520x340"}
    root.geometry(sizes[size])

# ================= SCALE =================
def set_scale(percent):
    scale = 1.0 - (percent / 100)
    root.tk.call("tk", "scaling", scale)

# ================= LIMITS =================
def edit_limits():
    global limits
    txt = simpledialog.askstring("Edit Limits", "Comma separated limits:",
                                 initialvalue=",".join(map(str, limits)))
    if txt:
        try:
            limits = sorted(int(x.strip()) for x in txt.split(","))
            with open(LIMITS_FILE, "w") as f:
                f.write(",".join(map(str, limits)))
        except:
            messagebox.showerror("Error", "Invalid limits")

# ================= HISTORY WINDOW =================
history_win = None
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

# ================= UI =================
root = tk.Tk()
root.title("Range Calculator")
root.geometry("420x280")
root.attributes("-topmost", True)
root.attributes("-alpha", 0.9)

# ================= MENU =================
menubar = tk.Menu(root)
root.config(menu=menubar)

file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)

file_menu.add_command(label="Pin / Unpin", command=toggle_top)
file_menu.add_command(label="Night / Day", command=toggle_mode)
file_menu.add_command(label="Edit Limits", command=edit_limits)
file_menu.add_command(label="History", command=open_history)

# ---- Transparency
trans_menu = tk.Menu(file_menu, tearoff=0)
file_menu.add_cascade(label="Transparency", menu=trans_menu)
for v in [0.3, 0.5, 0.7, 0.9]:
    trans_menu.add_command(label=str(v), command=lambda x=v: set_alpha(x))

# ---- Resize
resize_menu = tk.Menu(file_menu, tearoff=0)
file_menu.add_cascade(label="Resize", menu=resize_menu)
resize_menu.add_command(label="Small", command=lambda: resize("small"))
resize_menu.add_command(label="Medium", command=lambda: resize("medium"))
resize_menu.add_command(label="Large", command=lambda: resize("large"))

# ---- Scale
scale_menu = tk.Menu(file_menu, tearoff=0)
file_menu.add_cascade(label="Scale (%)", menu=scale_menu)
for p in [5,10,15,20,25,30,35]:
    scale_menu.add_command(label=f"{p}%", command=lambda x=p: set_scale(x))

# ================= CONTENT =================
entry = tk.Entry(root, font=("Segoe UI", 18), justify="center")
entry.pack(pady=10)
entry.bind("<Return>", calculate)

btns = tk.Frame(root)
btns.pack()
tk.Button(btns, text="Calculate", command=calculate).pack(side="left", padx=5)
tk.Button(btns, text="Clear", command=clear_input).pack(side="left", padx=5)

res = tk.Frame(root)
res.pack(pady=10)

left_lbl = tk.Label(res, width=6, font=("Segoe UI",16), bg="#B22222", fg="white")
left_lbl.pack(side="left", padx=5)

middle_lbl = tk.Label(res, width=4, font=("Segoe UI",16), bg="white")
middle_lbl.pack(side="left", padx=5)

right_lbl = tk.Label(res, width=6, font=("Segoe UI",16), bg="#228B22", fg="white")
right_lbl.pack(side="left", padx=5)

root.mainloop()
