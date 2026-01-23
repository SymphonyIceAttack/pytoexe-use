import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
import json
from datetime import datetime
import csv

# ================= SETTINGS =================
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "theme": "Light",
    "auto_scan": True
}

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(DEFAULT_SETTINGS, f)

settings = json.load(open(SETTINGS_FILE))

THEMES = {
    "Light": {"bg": "#ffffff", "fg": "#000000"},
    "Dark": {"bg": "#2b2b2b", "fg": "#ffffff"},
    "Blue": {"bg": "#e3f2fd", "fg": "#000000"}
}

# ================= DATABASE =================
conn = sqlite3.connect("dip_manage_v_simple.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    barcode TEXT UNIQUE,
    item_name TEXT,
    original_qty INTEGER,
    scanned_qty INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    user TEXT,
    barcode TEXT,
    result TEXT,
    time TEXT
)
""")

cur.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin', 'Admin')")
conn.commit()

current_user = None
user_role = None

# ================= LOGIN =================
def login():
    global current_user, user_role
    u = user_entry.get()
    p = pass_entry.get()

    cur.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
    r = cur.fetchone()
    if r:
        current_user = u
        user_role = r[0]
        login_win.destroy()
        main_app()
    else:
        messagebox.showerror("Login Failed", "Invalid credentials")

login_win = tk.Tk()
login_win.title("DIP MANAGE Login")
login_win.geometry("300x200")

tk.Label(login_win, text="Username").pack(pady=5)
user_entry = tk.Entry(login_win)
user_entry.pack()

tk.Label(login_win, text="Password").pack(pady=5)
pass_entry = tk.Entry(login_win, show="*")
pass_entry.pack()

tk.Button(login_win, text="Login", command=login).pack(pady=10)
login_win.mainloop()

# ================= MAIN APP =================
def main_app():
    root = tk.Tk()
    root.title("DIP MANAGE V3 Simple")
    root.geometry("900x500")

    theme = THEMES[settings["theme"]]
    root.configure(bg=theme["bg"])

    status_var = tk.StringVar(value="🔴 Waiting for barcode")
    last_scan_var = tk.StringVar(value="")

    # -------- SCAN --------
    def scan(barcode):
        if not barcode:
            return

        cur.execute("SELECT id, item_name, scanned_qty, original_qty FROM items WHERE barcode=?", (barcode,))
        item = cur.fetchone()
        if item:
            cur.execute("UPDATE items SET scanned_qty=? WHERE id=?", (item[2]+1, item[0]))
            result = "Matched"
            status_var.set(f"🟢 Matched: {item[1]}")
        else:
            result = "Unmatched"
            status_var.set("❌ Unmatched barcode")

        cur.execute("INSERT INTO audit_log (user, barcode, result, time) VALUES (?, ?, ?, ?)",
                    (current_user, barcode, result, datetime.now()))
        conn.commit()
        refresh_table()
        scan_entry.delete(0, tk.END)
        last_scan_var.set(f"Last scanned: {barcode}")

    def auto_receive(e):
        if settings["auto_scan"]:
            scan(scan_entry.get())

    # -------- TABLE --------
    columns = ("barcode", "item_name", "original_qty", "scanned_qty", "difference")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())
    tree.pack(fill="both", expand=True, pady=10)

    def refresh_table():
        for row in tree.get_children():
            tree.delete(row)
        cur.execute("SELECT barcode, item_name, original_qty, scanned_qty, scanned_qty-original_qty FROM items")
        for r in cur.fetchall():
            tree.insert("", "end", values=r)

    # -------- SETTINGS --------
    def open_settings():
        win = tk.Toplevel(root)
        win.title("Settings")
        win.geometry("250x200")

        theme_var = tk.StringVar(value=settings["theme"])
        auto_var = tk.BooleanVar(value=settings["auto_scan"])

        def save():
            settings["theme"] = theme_var.get()
            settings["auto_scan"] = auto_var.get()
            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f)
            messagebox.showinfo("Saved", "Restart app to apply changes")
            win.destroy()

        ttk.Label(win, text="Theme").pack(pady=5)
        ttk.Combobox(win, values=list(THEMES.keys()), textvariable=theme_var).pack()
        ttk.Checkbutton(win, text="Auto Scan", variable=auto_var).pack(pady=5)
        ttk.Button(win, text="Save", command=save).pack(pady=10)

    # -------- EXPORT CSV --------
    def export_csv():
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if file:
            with open(file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Barcode", "Item Name", "Original Qty", "Scanned Qty", "Difference"])
                cur.execute("SELECT barcode, item_name, original_qty, scanned_qty, scanned_qty-original_qty FROM items")
                writer.writerows(cur.fetchall())
            messagebox.showinfo("Done", "CSV Exported")

    # -------- UI --------
    top = tk.Frame(root, bg=theme["bg"])
    top.pack(fill="x")

    tk.Label(top, text=f"User: {current_user}", bg=theme["bg"], fg=theme["fg"]).pack(side="left", padx=10)
    ttk.Button(top, text="Settings", command=open_settings).pack(side="right", padx=5)
    ttk.Button(top, text="Export CSV", command=export_csv).pack(side="right", padx=5)

    scan_entry = tk.Entry(root, font=("Arial", 16))
    scan_entry.pack(pady=10)
    scan_entry.bind("<Return>", lambda e: scan(scan_entry.get()))
    scan_entry.bind("<KeyRelease>", auto_receive)

    tk.Label(root, textvariable=status_var, font=("Arial", 12), bg=theme["bg"], fg=theme["fg"]).pack()
    tk.Label(root, textvariable=last_scan_var, font=("Arial", 12), bg=theme["bg"], fg=theme["fg"]).pack()

    refresh_table()
    root.mainloop()
