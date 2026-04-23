Python 3.13.13 (tags/v3.13.13:01104ce, Apr  7 2026, 19:25:48) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import tkinter as tk
from tkinter import messagebox
import hashlib
import time

# =========================
# 🔒 FIXED PASSWORD
# =========================
REAL_PASSWORD = "DUNCAN"
PASSWORD_HASH = hashlib.sha256(REAL_PASSWORD.encode()).hexdigest()

# =========================
# 🖥 LOGIC
# =========================
attempts = 0
locked = False

def fake_decrypt(callback):
    progress_label.config(text="Decrypting")
    for i in range(6):
        root.update()
        time.sleep(0.25)
        progress_label.config(text="Decrypting" + "." * (i % 4))
    callback()

def check_password():
    global attempts, locked

    if locked:
        messagebox.showwarning("Locked", "System locked due to too many attempts.")
        return

    entered = entry.get()

    def result():
        global attempts, locked
...         entered_hash = hashlib.sha256(entered.encode()).hexdigest()
... 
...         if entered_hash == PASSWORD_HASH:
...             open_success_window()
...         else:
...             attempts += 1
...             messagebox.showerror("Access Denied", f"Incorrect password ({attempts}/3)")
...             if attempts >= 3:
...                 locked = True
...                 messagebox.showwarning("System Locked", "Too many failed attempts.")
... 
...     fake_decrypt(result)
... 
... def open_success_window():
...     success = tk.Toplevel(root)
...     success.title("Success")
...     success.geometry("300x150")
...     tk.Label(success, text="Password Cracked", font=("Arial", 16)).pack(expand=True)
... 
... # =========================
... # 🪟 GUI
... # =========================
... root = tk.Tk()
... root.title("Secure System")
... root.geometry("320x200")
... 
... tk.Label(root, text="ENTER PASSWORD", font=("Arial", 12)).pack(pady=10)
... 
... entry = tk.Entry(root, show="*", width=30)
... entry.pack()
... 
... tk.Button(root, text="Submit", command=check_password).pack(pady=10)
... 
... progress_label = tk.Label(root, text="", font=("Arial", 10))
... progress_label.pack()
... 
