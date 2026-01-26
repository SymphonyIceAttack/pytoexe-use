import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime
import os

# ---------- LOAD OR CREATE LIMITS ----------
limits_file = "limits.txt"
if os.path.exists(limits_file):
    with open(limits_file, "r") as f:
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
    if history_panel and history_panel.winfo_exists():
        update_history_text()

def update_history_text():
    history_text.config(state="normal")
    history_text.delete(1.0, tk.END)
    for line in history:
        history_text.insert(tk.END, line + "\n")
    history_text.config(state="disabled")

def clear_history():
    global history
    history = []
    update_history_text()

# ---------- CALCULATION FUNCTION ----------
def calculate(event=None):
    try:
        value = int(entry.get())
        left = None
        right = None
        
        for i in range(len(limits)-1):
            if limits[i] < value < limits[i+1]:
                left = limits[i]
                right = limits[i+1]
                break
            elif value == limits[i]:
                left = limits[i-1] if i > 0 else limits[i]
                right = limits[i+1]
                break
        if value == limits[-1]:
            left = limits[-2]
            right = limits[-1]
        
        left_var.set(left)
        right_var.set(right)
        
        # COLORS
        left_label.config(bg="green", fg="white")
        right_label.config(bg="red", fg="white")
        
        # HISTORY
        add_to_history(value, left_var.get(), right_var.get())
        
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid integer")

# ---------- TOPMOST ----------
def toggle_topmost(event=None):
    global topmost
    topmost = not topmost
    root.attributes("-topmost", topmost)
    root.attributes("-alpha", transparency_slider.get() if topmost else 1.0)
    pin_button.config(text="Unpin" if topmost else "Pin")

# ---------- NIGHT/DAY MODE ----------
def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#2E2E2E" if dark_mode else "white"
    fg = "white" if dark_mode else "black"
    root.config(bg=bg)
    entry.config(bg="#555555" if dark_mode else "white", fg=fg)
    calc_button.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    clear_entry_button.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    pin_button.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    dark_button.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    edit_button.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    transparency_slider.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    history_button.config(bg="#777777" if dark_mode else "#DDDDDD", fg=fg)
    left_label.config(bg=left_label.cget("bg"), fg=left_label.cget("fg"))
    right_label.config(bg=right_label.cget("bg"), fg=right_label.cget("fg"))
    dark_button.config(text="Day Mode" if dark_mode else "Night Mode")
    if history_panel and history_panel.winfo_exists():
        history_panel.config(bg=bg)
        history_text.config(bg=bg, fg=fg)

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
