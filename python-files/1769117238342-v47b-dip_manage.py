import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import pandas as pd
from datetime import datetime

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
    file = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.csv")])
    if not file:
        return

    try:
        df = pd.read_excel(file) if file.endswith("xlsx") else pd.read_csv(file)

        for _, row in df.iterrows():
            try:
                cur.execute("""
                INSERT INTO items (auto_sn, item_code, barcode, item_name, quantity)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    str(row.get("Auto SN", "")),
                    str(row.get("Item Code", "")),
                    str(row.get("Barcode", "")),
                    str(row.get("Item Name", "")),
                    int(row.get("Quantity", 0))
                ))
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        messagebox.showinfo("Success", "Data Imported Successfully")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def scan_barcode(event=None):
    barcode = scan_entry.get().strip()
    scan_entry.delete(0, tk.END)

    if not barcode:
        return

    cur.execute("SELECT id, item_name, quantity FROM items WHERE barcode=?", (barcode,))
    item = cur.fetchone()

    if item:
        new_qty = item[2] + 1
        cur.execute("UPDATE items SET quantity=? WHERE id=?", (new_qty, item[0]))
        conn.commit()
        status_label.config(
            text=f"✔ {item[1]} | Quantity: {new_qty}",
            fg="green"
        )
    else:
        cur.execute("SELECT quantity FROM unmatched WHERE barcode=?", (barcode,))
        un = cur.fetchone()

        if un:
            cur.execute(
                "UPDATE unmatched SET quantity=? WHERE barcode=?",
                (un[0] + 1, barcode)
            )
        else:
            cur.execute(
                "INSERT INTO unmatched (barcode, quantity, first_seen) VALUES (?, ?, ?)",
                (barcode, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )

        conn.commit()
        status_label.config(text="✖ Barcode does not match", fg="red")


def export_unmatched():
    cur.execute("SELECT barcode, quantity, first_seen FROM unmatched")
    data = cur.fetchall()

    if not data:
        messagebox.showinfo("Info", "No unmatched barcodes found")
        return

    df = pd.DataFrame(data, columns=["Barcode", "Quantity", "First Seen"])
    file = filedialog.asksaveasfilename(defaultextension=".xlsx")

    if file:
        df.to_excel(file, index=False)
        messagebox.showinfo("Success", "Unmatched barcodes exported")


def view_report():
    report = tk.Toplevel(root)
    report.title("Scan Report")
    report.geometry("600x400")

    text = tk.Text(report)
    text.pack(fill="both", expand=True)

    cur.execute("SELECT item_name, barcode, quantity FROM items ORDER BY item_name")
    for row in cur.fetchall():
        text.insert(tk.END, f"{row[0]} | {row[1]} | Qty: {row[2]}\n")


# ---------------- UI ----------------
root = tk.Tk()
root.title("Dip Manage")
root.geometry("500x300")
root.resizable(False, False)

tk.Label(root, text="DIP MANAGE", font=("Arial", 18, "bold")).pack(pady=10)

scan_entry = tk.Entry(root, font=("Arial", 16), justify="center")
scan_entry.pack(pady=10, ipadx=20, ipady=8)
scan_entry.focus()

scan_entry.bind("<Return>", scan_barcode)

status_label = tk.Label(root, text="Ready to Scan", font=("Arial", 12))
status_label.pack(pady=10)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Import Data", width=12, command=import_data).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Report View", width=12, command=view_report).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Export Unmatched", width=15, command=export_unmatched).grid(row=0, column=2, padx=5)

root.mainloop()
