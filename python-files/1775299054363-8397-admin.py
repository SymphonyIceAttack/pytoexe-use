import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# ডাটাবেস তৈরি ও টেবিল সেটআপ
def setup_database():
    conn = sqlite3.connect('registration.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reg_keys (
                    key_text TEXT PRIMARY KEY,
                    status TEXT,
                    used_by TEXT,
                    used_date TEXT
                )''')
    conn.commit()
    conn.close()

# কী লোড করে টেবিলে দেখানো
def load_keys(tree):
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect('registration.db')
    c = conn.cursor()
    c.execute("SELECT key_text, status, used_by, used_date FROM reg_keys")
    rows = c.fetchall()
    for row in rows:
        tree.insert("", tk.END, values=row)
    conn.close()

# নতুন কী অ্যাড করা
def add_key(key_entry, tree):
    key = key_entry.get().strip()
    if not key:
        messagebox.showerror("Error", "Please enter a registration key")
        return
    conn = sqlite3.connect('registration.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO reg_keys (key_text, status, used_by, used_date) VALUES (?, ?, ?, ?)",
                  (key, "unused", "", ""))
        conn.commit()
        messagebox.showinfo("Success", "Key added successfully")
        key_entry.delete(0, tk.END)
        load_keys(tree)
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Key already exists")
    finally:
        conn.close()

# কী ডিলিট করা
def delete_key(tree):
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "Select a key to delete")
        return
    key = tree.item(selected[0])['values'][0]
    conn = sqlite3.connect('registration.db')
    c = conn.cursor()
    c.execute("DELETE FROM reg_keys WHERE key_text=?", (key,))
    conn.commit()
    conn.close()
    load_keys(tree)

# অ্যাডমিন GUI
def admin_gui():
    setup_database()
    root = tk.Tk()
    root.title("Admin Panel - Registration Key Manager")
    root.geometry("700x500")

    # ফ্রেম
    top_frame = tk.Frame(root)
    top_frame.pack(pady=10)

    tk.Label(top_frame, text="New Registration Key:").grid(row=0, column=0, padx=5)
    key_entry = tk.Entry(top_frame, width=30)
    key_entry.grid(row=0, column=1, padx=5)

    add_btn = tk.Button(top_frame, text="Add Key", command=lambda: add_key(key_entry, tree))
    add_btn.grid(row=0, column=2, padx=5)

    # ট্রিবিউ
    columns = ("Key", "Status", "Used By", "Used Date")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.pack(pady=10, fill=tk.BOTH, expand=True)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    delete_btn = tk.Button(btn_frame, text="Delete Selected Key", command=lambda: delete_key(tree))
    delete_btn.pack(side=tk.LEFT, padx=10)

    refresh_btn = tk.Button(btn_frame, text="Refresh List", command=lambda: load_keys(tree))
    refresh_btn.pack(side=tk.LEFT, padx=10)

    load_keys(tree)
    root.mainloop()

if __name__ == "__main__":
    admin_gui()