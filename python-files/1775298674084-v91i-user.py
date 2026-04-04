import tkinter as tk
from tkinter import messagebox
import sqlite3
import platform
import getpass
from datetime import datetime

# ইউজারের সিস্টেম তথ্য
def get_system_id():
    return f"{platform.node()}_{getpass.getuser()}"

# কী ভেরিফাই করা
def verify_key(key_entry, status_label, activate_btn):
    key = key_entry.get().strip()
    if not key:
        messagebox.showerror("Error", "Please enter registration key")
        return

    conn = sqlite3.connect('registration.db')
    c = conn.cursor()
    c.execute("SELECT status, used_by FROM reg_keys WHERE key_text=?", (key,))
    result = c.fetchone()

    if not result:
        messagebox.showerror("Error", "Invalid registration key")
    elif result[0] == "used":
        messagebox.showerror("Error", f"This key is already used by: {result[1]}")
    else:
        # কী ইউজ করো
        system_id = get_system_id()
        used_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE reg_keys SET status=?, used_by=?, used_date=? WHERE key_text=?",
                  ("used", system_id, used_date, key))
        conn.commit()
        messagebox.showinfo("Success", "Registration successful! Software activated.")
        status_label.config(text=f"Status: Activated for {system_id}", fg="green")
        key_entry.config(state=tk.DISABLED)
        activate_btn.config(state=tk.DISABLED)
    conn.close()

# ইউজার GUI
def user_gui():
    root = tk.Tk()
    root.title("User Panel - Enter Registration Key")
    root.geometry("500x250")
    root.resizable(False, False)

    # UI এলিমেন্ট
    tk.Label(root, text="Software Registration", font=("Arial", 16, "bold")).pack(pady=20)
    tk.Label(root, text="Enter your registration key (like IDM):").pack(pady=5)

    key_entry = tk.Entry(root, width=40, font=("Arial", 12))
    key_entry.pack(pady=5)

    activate_btn = tk.Button(root, text="Activate", command=lambda: verify_key(key_entry, status_label, activate_btn))
    activate_btn.pack(pady=10)

    status_label = tk.Label(root, text="Status: Not activated", font=("Arial", 10), fg="red")
    status_label.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    user_gui()