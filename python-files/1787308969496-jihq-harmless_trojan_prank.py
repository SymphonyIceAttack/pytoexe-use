import tkinter as tk
from tkinter import messagebox
import random

root = tk.Tk()
root.title("Totally Real Security Tool")
root.geometry("700x400")
root.resizable(False, False)

title = tk.Label(root, text="⚠ SECURITY ALERT ⚠", font=("Arial", 28, "bold"))
title.pack(pady=25)

status = tk.Label(root, text="Scanning your computer...", font=("Arial", 18))
status.pack(pady=15)

progress = tk.Label(root, text="0%", font=("Arial", 20, "bold"))
progress.pack(pady=10)

info = tk.Label(root, text="Please do not close this window.", font=("Arial", 13))
info.pack(pady=10)

bar = tk.Frame(root, height=25, width=600, relief="sunken", borderwidth=2)
bar.pack(pady=15)
fill = tk.Frame(bar, height=21, width=0)
fill.place(x=0, y=0)

def scan(n=0):
    if n <= 100:
        progress.config(text=f"{n}%")
        fill.config(width=6*n)
        if n < 35:
            status.config(text="Scanning files...")
        elif n < 70:
            status.config(text="Detecting suspicious activity...")
        else:
            status.config(text="Threat level: EXTREMELY CONCERNING")
        root.after(55, scan, n + 1)
    else:
        status.config(text="CRITICAL ERROR: 127 THREATS FOUND")
        root.after(1200, reveal)

def reveal():
    messagebox.showwarning(
        "💀 SYSTEM COMPROMISED 💀",
        "Just kidding 😂\\n\\n"
        "You got pranked!\\n"
        "Nothing was changed, deleted, or infected."
    )
    root.destroy()

scan()
root.mainloop()
