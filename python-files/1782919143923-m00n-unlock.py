Python 3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import tkinter as tk
from tkinter import messagebox
import secrets
import string

# ----------------------------
# CHANGE THIS
# ----------------------------
SCREEN_TIME_PASSWORD = "q7ml2vn8xr4p"
CHALLENGE_LENGTH = 1000
VISIBLE_SECONDS = 30

characters = (
    string.ascii_letters +
    string.digits +
    "!@#$%^&*()-_=+[]{};:,.<>/?"
)

challenge = ""

def generate():
    global challenge

    challenge = "".join(
        secrets.choice(characters)
        for _ in range(CHALLENGE_LENGTH)
    )

    challenge_box.config(state="normal")
    challenge_box.delete("1.0", tk.END)
    challenge_box.insert(tk.END, challenge)
    challenge_box.config(state="disabled")

    entry.delete("1.0", tk.END)
    password_label.config(text="")

def reveal():
    typed = entry.get("1.0", tk.END).rstrip("\n")

    if typed == challenge:
        password_label.config(
            text=f"Password:\n{SCREEN_TIME_PASSWORD}",
            fg="green"
        )

        root.after(
            VISIBLE_SECONDS * 1000,
            lambda: password_label.config(text="")
        )

    else:
        messagebox.showerror(
            "Incorrect",
            "The challenge was not entered exactly."
        )

def disable_paste(event):
    return "break"

root = tk.Tk()
root.title("Emergency Unlock")
root.geometry("900x700")

title = tk.Label(
    root,
    text="Emergency Unlock Barrier",
    font=("Segoe UI", 18, "bold")
)
title.pack(pady=10)

tk.Label(root, text="Random challenge").pack()

challenge_box = tk.Text(
    root,
    height=10,
    wrap="word"
... )
... challenge_box.pack(fill="both", padx=10)
... 
... challenge_box.config(state="disabled")
... 
... tk.Label(root, text="Type the challenge exactly").pack(pady=(10,0))
... 
... entry = tk.Text(
...     root,
...     height=10,
...     wrap="word"
... )
... entry.pack(fill="both", padx=10)
... 
... entry.bind("<Control-v>", disable_paste)
... entry.bind("<Control-V>", disable_paste)
... entry.bind("<Shift-Insert>", disable_paste)
... entry.bind("<Button-3>", disable_paste)
... 
... tk.Button(
...     root,
...     text="Generate Challenge",
...     command=generate
... ).pack(pady=5)
... 
... tk.Button(
...     root,
...     text="Reveal Password",
...     command=reveal
... ).pack()
... 
... password_label = tk.Label(
...     root,
...     font=("Segoe UI", 14, "bold")
... )
... password_label.pack(pady=20)
... 
... generate()
... 
