import tkinter as tk
from tkinter import messagebox
import threading
import os
import shutil
import subprocess
import sys
import ctypes

# =========================
# CONFIG
# =========================
USERNAME = "PRIME"
PASSWORD = "3K"

# =========================
# MAIN WINDOW
# =========================
root = tk.Tk()
root.title("PRIME OPTIMIZER PRO X")
root.geometry("1000x600")
root.resizable(False, False)
root.configure(bg='#0D0D0D')  # Solid black background - no video, no PIL error

# =========================
# LOGIN FRAME
# =========================
login_frame = tk.Frame(root, bg="#111111")
login_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)

tk.Label(login_frame, text="PRIME LOGIN", font=("Segoe UI", 18, "bold"),
         bg="#111111", fg="white").pack(pady=20)

user_entry = tk.Entry(login_frame, font=("Segoe UI", 12))
user_entry.pack(pady=10)

pass_entry = tk.Entry(login_frame, show="*", font=("Segoe UI", 12))
pass_entry.pack(pady=10)

def login():
    if user_entry.get() == USERNAME and pass_entry.get() == PASSWORD:
        login_frame.destroy()
        show_dashboard()
    else:
        messagebox.showerror("Error", "Invalid Login")

tk.Button(login_frame, text="LOGIN", font=("Segoe UI", 11, "bold"),
          bg="#1f1f1f", fg="white", relief="flat",
          command=login).pack(pady=20)

# =========================
# DASHBOARD
# =========================
def show_dashboard():
    dash = tk.Frame(root, bg="#111111")
    dash.place(relx=0.5, rely=0.5, anchor="center", width=500, height=400)

    tk.Label(dash, text="PRIME OPTIMIZER PRO X",
             font=("Segoe UI", 18, "bold"),
             bg="#111111", fg="white").pack(pady=20)

    def clean_temp():
        temp = os.environ['TEMP']
        try:
            shutil.rmtree(temp)
            os.makedirs(temp)
            messagebox.showinfo("Done", "Temp Cleaned")
        except:
            messagebox.showwarning("Warning", "Some files in use")

    def high_performance():
        subprocess.call("powercfg -setactive SCHEME_MIN", shell=True)
        messagebox.showinfo("Mode", "High Performance Enabled")

    def flush_dns():
        subprocess.call("ipconfig /flushdns", shell=True)
        messagebox.showinfo("Done", "DNS Flushed")
    
    def raw_mouse():
        try:
            # Disable mouse acceleration
            ctypes.windll.user32.SystemParametersInfoW(0x0073, 0, 0, 0)
            messagebox.showinfo("Success", "Raw Mouse Input Enabled")
        except:
            messagebox.showerror("Error", "Run as administrator")

    tk.Button(dash, text="🧹 Clean Temp",
              font=("Segoe UI", 11), width=25,
              command=lambda: threading.Thread(target=clean_temp).start()
              ).pack(pady=10)

    tk.Button(dash, text="⚡ High Performance Mode",
              font=("Segoe UI", 11), width=25,
              command=lambda: threading.Thread(target=high_performance).start()
              ).pack(pady=10)

    tk.Button(dash, text="🌐 Flush DNS",
              font=("Segoe UI", 11), width=25,
              command=lambda: threading.Thread(target=flush_dns).start()
              ).pack(pady=10)
    
    tk.Button(dash, text="🖱️ Raw Mouse Fix",
              font=("Segoe UI", 11), width=25,
              command=lambda: threading.Thread(target=raw_mouse).start()
              ).pack(pady=10)

# =========================
# CLEAN EXIT
# =========================
def on_close():
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()