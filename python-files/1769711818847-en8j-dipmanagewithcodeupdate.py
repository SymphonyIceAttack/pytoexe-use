import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import csv
from datetime import datetime
import winsound
import re
import threading
import os

# ---------------- DATABASE ----------------
conn = sqlite3.connect("dip_manage.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auto_sn TEXT,
    item_code TEXT,
    barcode TEXT UNIQUE,
    item_name TEXT,
    quantity INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS unmatched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE,
    quantity INTEGER DEFAULT 1,
    first_seen TEXT
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------

def import_data():
    file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if not file:
        return
    try:
        with open(file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    cur.execute("""
                    INSERT INTO items (auto_sn, item_code, barcode, item_name, quantity)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        row.get("Auto SN", ""),
                        row.get("Item Code", ""),
                        row.get("Barcode", ""),
                        row.get("Item Name", ""),
                        int(row.get("Quantity", 0))
                    ))
                except sqlite3.IntegrityError:
                    pass  # Ignore duplicates
        conn.commit()
        messagebox.showinfo("Success", "Data Imported Successfully")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def validate_barcode(barcode):
    barcode = barcode.strip()
    if len(barcode) < 3:
        return False, "Too short"
    if not re.match("^[A-Za-z0-9]+$", barcode):
        return False, "Invalid characters"
    return True, ""


def process_barcode(barcode):
    barcode = barcode.strip()
    if not barcode:
        return

    valid, reason = validate_barcode(barcode)
    if not valid:
        status_label.config(text=f"⚠ Broken/Invalid: {reason}", fg="orange")
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        return

    cur.execute("SELECT id, item_name, quantity FROM items WHERE barcode=?", (barcode,))
    item = cur.fetchone()
    if item:
        new_qty = item[2] + 1
        cur.execute("UPDATE items SET quantity=? WHERE id=?", (new_qty, item[0]))
        conn.commit()
        status_label.config(text=f"✔ {item[1]} | Qty: {new_qty}", fg="green")
        winsound.MessageBeep(winsound.MB_OK)
    else:
        cur.execute("SELECT quantity FROM unmatched WHERE barcode=?", (barcode,))
        un = cur.fetchone()
        if un:
            cur.execute("UPDATE unmatched SET quantity=? WHERE barcode=?", (un[0]+1, barcode))
        else:
            cur.execute("INSERT INTO unmatched (barcode, quantity, first_seen) VALUES (?, ?, ?)",
                        (barcode, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        status_label.config(text=f"✖ Barcode not found!", fg="red")
        winsound.MessageBeep(winsound.MB_ICONHAND)


def auto_scan(event):
    barcode = scan_entry.get()
    scan_entry.delete(0, tk.END)
    threading.Thread(target=process_barcode, args=(barcode,), daemon=True).start()


def export_data():
    cur.execute("SELECT item_name, barcode, quantity FROM items WHERE quantity > 0")
    matched = cur.fetchall()
    file1 = filedialog.asksaveasfilename(title="Save Matched Items", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if file1:
        with open(file1, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Item Name", "Barcode", "Quantity"])
            writer.writerows(matched)

    cur.execute("SELECT barcode, quantity, first_seen FROM unmatched")
    unmatched = cur.fetchall()
    file2 = filedialog.asksaveasfilename(title="Save Unmatched Items", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if file2:
        with open(file2, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Barcode", "Quantity", "First Seen"])
            writer.writerows(unmatched)

    messagebox.showinfo("Export", "Matched & Unmatched Items Exported Successfully")


def view_report():
    report = tk.Toplevel(root)
    report.title("Scanned Items Report")
    report.geometry("700x500")
    text = tk.Text(report)
    text.pack(fill="both", expand=True)
    
    cur.execute("SELECT item_name, barcode, quantity FROM items WHERE quantity > 0 ORDER BY item_name")
    data = cur.fetchall()
    if not data:
        text.insert(tk.END, "No items scanned yet.\n")
        return
    for row in data:
        text.insert(tk.END, f"{row[0]} | {row[1]} | Qty: {row[2]}\n")


def show_about():
    messagebox.showinfo(
        "About Dip Manage Pro",
        "Dip Manage Pro\n\n"
        "Developer: Dipesh Tajpuriya\n"
        "Email: gagagaga.com\n\n"
        "Advanced barcode inventory management system\n"
        "Automatic scanning, real-time updates, sound alerts."
    )


def edit_code():
    editor = tk.Toplevel(root)
    editor.title("Edit Code")
    editor.geometry("800x600")

    code_text = tk.Text(editor, font=("Consolas", 12))
    code_text.pack(fill="both", expand=True)

    script_path = os.path.realpath(__file__)
    with open(script_path, "r", encoding="utf-8") as f:
        code_text.insert(tk.END, f.read())

    def save_changes():
        try:
            new_code = code_text.get("1.0", tk.END)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(new_code)
            messagebox.showinfo("Success", "Code updated successfully.\nPlease restart the app to apply changes.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(editor, text="Apply Changes", command=save_changes, bg="green", fg="white").pack(pady=5)


# ---------------- UI ----------------
root = tk.Tk()
root.title("Dip Manage Pro")
root.geometry("800x500")

tk.Label(root, text="DIP MANAGE PRO", font=("Arial", 20, "bold")).pack(pady=10)

scan_entry = tk.Entry(root, font=("Arial", 16), justify="center")
scan_entry.pack(pady=10, ipadx=20, ipady=8)
scan_entry.focus()
scan_entry.bind("<Return>", auto_scan)
scan_entry.bind("<Tab>", auto_scan)
scan_entry.bind("<space>", auto_scan)

status_label = tk.Label(root, text="Ready to Scan", font=("Arial", 12))
status_label.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Import CSV", width=15, command=import_data).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Export Data", width=15, command=export_data).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="View Report", width=15, command=view_report).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="About", width=15, command=show_about).grid(row=0, column=3, padx=5)
tk.Button(btn_frame, text="Edit Code", width=15, command=edit_code).grid(row=0, column=4, padx=5)

root.mainloop()
