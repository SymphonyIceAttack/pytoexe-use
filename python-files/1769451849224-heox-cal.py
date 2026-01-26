import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ---------- FILE & LIMITS ----------
LIMITS_FILE = "limits.txt"

if os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "r") as f:
        limits = sorted([int(x) for x in f.read().split(",")])
else:
    limits = [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]

topmost = True
dark_mode = False
size_mode = "medium"
history = []

# ---------- HISTORY FUNCTIONS ----------
def add_to_history(value, left, right):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history.append(f"#{len(history)+1} | Input: {value} | Left: {left} | Right: {right} | {timestamp}")
    update_history_text()

def update_history_text():
    if history_panel and history_panel.winfo_exists():
        history_text.config(state="normal")
        history_text.delete(1.0, tk.END)
        for line in history:
            history_text.insert(tk.END, line + "\n")
        history_text.config(state="disabled")

def clear_history():
    global history
    history = []
    update_history_text()

# ---------- CALCULATION ----------
def calculate(event=None):
    try:
        value = int(entry.get())
        left = None
        right = None
        
        if value <= limits[0]:
            left = limits[0]
            right = limits[1]
        elif value >= limits[-1]:
            left = limits[-2]
            right = limits[-1]
        else:
            for i in range(len(limits)-1):
                if value == limits[i]:
                    left = limits[i]
                    right = limits[i+1]
                    break
                elif limits[i] < value < limits[i+1]:
                    left = limits[i]
                    right = limits[i+1]
                    break

        left_var.set(left)
        right_var.set(right)

        # COLORS
        left_label.config(bg="green", fg="white")
        right_label.config(bg="red", fg="white")

        add_to_history(value, left_var.get(), right_var.get())

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid integer")

# ---------- TOPMOST ----------
def toggle_topmost(event=None):
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)
    pin_button.config(text="Unpin" if topmost else "Pin")

# ---------- NIGHT/DAY MODE ----------
def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg="#555555" if dark_mode else "white", fg=fg)
    for b in [calc_button, clear_button, pin_button, dark_button, edit_button, history_button]:
        b.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    left_label.config(bg=left_label.cget("bg"), fg=left_label.cget("fg"))
    right_label.config(bg=right_label.cget("bg"), fg=right_label.cget("fg"))
    if history_panel and history_panel.winfo_exists():
        history_panel.config(bg=bg)
        history_text.config(bg=bg, fg=fg)
    dark_button.config(text="Day Mode" if dark_mode else "Night Mode")

# ---------- TRANSPARENCY ----------
def update_transparency(val):
    if topmost:
        root.attributes("-alpha", float(val))

# ---------- EDIT LIMITS ----------
def edit_limits():
    global limits
    new_limits = simpledialog.askstring("Edit Limits", "Enter comma-separated limits:", initialvalue=",".join(str(x) for x in limits))
    if new_limits:
        try:
            limits = sorted([int(x.strip()) for x in new_limits.split(",")])
            save_limits()
            messagebox.showinfo("Saved", "Limits updated successfully!")
        except:
            messagebox.showerror("Error", "Invalid input!")

def save_limits():
    with open(LIMITS_FILE, "w") as f:
        f.write(",".join(str(x) for x in limits))

# ---------- HISTORY PANEL ----------
history_panel = None
def open_history():
    global history_panel
    if history_panel and history_panel.winfo_exists():
        history_panel.lift()
        return
    history_panel = tk.Toplevel(root)
    history_panel.title("History")
    history_panel.geometry("500x300")
    history_panel.attributes("-topmost", True)
    global history_text
    history_text = tk.Text(history_panel, state="disabled", font=("Arial", 12))
    history_text.pack(fill="both", expand=True)
    clear_history_button = tk.Button(history_panel, text="Clear History", command=clear_history)
    clear_history_button.pack(pady=5)
    update_history_text()

# ---------- RESIZE ----------
def resize_window(mode):
    sizes = {"small":"300x260","medium":"400x320","large":"500x400"}
    root.geometry(sizes[mode])

# ---------- GUI ----------
root = tk.Tk()
root.title("Range Calculator")
root.geometry("400x320")
root.attributes("-topmost", topmost)
root.attributes("-alpha", 0.8)

# Entry
entry = tk.Entry(root, font=("Arial", 18), justify="center")
entry.pack(pady=10)
entry.bind("<Return>", calculate)

# Buttons
buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=5)

calc_button = tk.Button(buttons_frame, text="=", font=("Arial", 18), width=4, command=calculate)
calc_button.pack(side="left", padx=5)

clear_button = tk.Button(buttons_frame, text="Clear", font=("Arial", 18), width=6, command=lambda: entry.delete(0, tk.END))
clear_button.pack(side="left", padx=5)

# Left/Right labels
frame_limits = tk.Frame(root)
frame_limits.pack(pady=5)
left_var = tk.StringVar(value="-")
right_var = tk.StringVar(value="-")
left_label = tk.Label(frame_limits, textvariable=left_var, font=("Arial", 16), width=8, bg="grey", fg="white")
left_label.pack(side="left", padx=10)
right_label = tk.Label(frame_limits, textvariable=right_var, font=("Arial", 16), width=8, bg="grey", fg="white")
right_label.pack(side="right", padx=10)

# Pin/Unpin
pin_button = tk.Button(root, text="Unpin", font=("Arial", 12), command=toggle_topmost)
pin_button.pack(pady=5)

# Night/Day
dark_button = tk.Button(root, text="Night Mode", font=("Arial", 12), command=toggle_dark_mode)
dark_button.pack(pady=5)

# Edit Limits
edit_button = tk.Button(root, text="Edit Limits", font=("Arial", 12), command=edit_limits)
edit_button.pack(pady=5)

# History
history_button = tk.Button(root, text="History", font=("Arial", 12), command=open_history)
history_button.pack(pady=5)

# Transparency slider
transparency_slider = tk.Scale(root, from_=0.2, to=1.0, resolution=0.05, orient="horizontal", label="Transparency", command=update_transparency, length=250)
transparency_slider.set(0.8)
transparency_slider.pack(pady=5)

# Resize
resize_frame = tk.Frame(root)
resize_frame.pack(pady=5)
tk.Button(resize_frame, text="Small", command=lambda: resize_window("small")).pack(side="left", padx=5)
tk.Button(resize_frame, text="Medium", command=lambda: resize_window("medium")).pack(side="left", padx=5)
tk.Button(resize_frame, text="Large", command=lambda: resize_window("large")).pack(side="left", padx=5)

# Shortcuts
root.bind("<Control-t>", toggle_topmost)
root.bind("<Control-h>", lambda e: open_history())

root.mainloop()
