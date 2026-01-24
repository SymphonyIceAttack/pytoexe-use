import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import csv
import os
import sys
import winsound
from datetime import datetime

APP_NAME = "DIP MANAGE - Manual Stock Take"
DB_FILE = "dip_manage.db"

# ================= PATH HELPER =================
def resource_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# ================= BARCODE HELPERS =================
def fix_barcode(raw):
    if raw is None:
        return None, "Empty barcode"

    b = str(raw).strip()

    if "E+" in b or "e+" in b:
        return None, "Scientific notation (Excel damage)"

    if b.endswith(".0"):
        b = b[:-2]

    if not b.isdigit():
        return None, "Non-numeric characters"

    return b, None


def is_valid_barcode(barcode, min_len=8, max_len=14):
    return barcode.isdigit() and min_len <= len(barcode) <= max_len

# ================= DATABASE =================
conn = sqlite3.connect(resource_path(DB_FILE))
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SN TEXT,
    BARCODE TEXT UNIQUE,
    ITEM_NAME TEXT,
    ORIGINAL_QTY INTEGER DEFAULT 0,
    SCANNED_QTY INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS unmatched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    BARCODE TEXT UNIQUE,
    QTY INTEGER DEFAULT 1,
    FIRST_SEEN TEXT
)
""")
conn.commit()

# ================= APP =================
class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x650")
        self.sound_on = True

        self.create_ui()
        self.load_items()

    # ---------------- UI ----------------
    def create_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab_main = ttk.Frame(notebook)
        self.tab_report = ttk.Frame(notebook)
        self.tab_about = ttk.Frame(notebook)

        notebook.add(self.tab_main, text="Stock Take")
        notebook.add(self.tab_report, text="Reports")
        notebook.add(self.tab_about, text="About")

        self.build_main_tab()
        self.build_report_tab()
        self.build_about_tab()

    def build_main_tab(self):
        top = ttk.Frame(self.tab_main)
        top.pack(fill="x", pady=10)

        ttk.Label(top, text="Scan Barcode:", font=("Arial", 12)).pack(side="left", padx=5)
        self.scan_entry = ttk.Entry(top, font=("Arial", 14), width=30)
        self.scan_entry.pack(side="left", padx=5)
        self.scan_entry.bind("<Return>", self.scan_barcode)
        self.scan_entry.focus()

        ttk.Button(top, text="Import CSV", command=self.import_csv).pack(side="left", padx=5)
        ttk.Button(top, text="Export Template", command=self.export_template).pack(side="left", padx=5)

        self.status = ttk.Label(self.tab_main, text="Ready", font=("Arial", 11))
        self.status.pack(pady=5)

        self.tree = ttk.Treeview(
            self.tab_main,
            columns=("SN","BARCODE","ITEM","ORIGINAL","SCANNED"),
            show="headings"
        )
        for c in self.tree["columns"]:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=200)
        self.tree.pack(fill="both", expand=True)

    def build_report_tab(self):
        self.report_tree = ttk.Treeview(self.tab_report, show="headings")
        self.report_tree.pack(fill="both", expand=True)

    def build_about_tab(self):
        ttk.Label(
            self.tab_about,
            text=f"""{APP_NAME}

SOFTWARE DEVELOPER:
Dipesh Tajpuriya

CONTACT:
www.ladybud@gmail.com
""",
            font=("Arial", 12),
            justify="center"
        ).pack(expand=True)

    # ---------------- CSV IMPORT ----------------
    def import_csv(self):
        file = filedialog.askopenfilename(filetypes=[("CSV Files","*.csv")])
        if not file:
            return

        preview = []

        with open(file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fixed, err = fix_barcode(row.get("BARCODE"))
                if err:
                    status = f"ERROR: {err}"
                elif not is_valid_barcode(fixed):
                    status = "ERROR: Invalid length"
                else:
                    status = "OK"

                preview.append({
                    "SN": row.get("SN",""),
                    "BARCODE": fixed,
                    "ITEM": row.get("ITEM NAME",""),
                    "QTY": row.get("ORGINAL QTY","0"),
                    "STATUS": status
                })

        self.preview_window(preview)

    def preview_window(self, rows):
        win = tk.Toplevel(self.root)
        win.title("CSV Import Preview")
        win.geometry("1000x500")

        tree = ttk.Treeview(
            win,
            columns=("SN","BARCODE","ITEM","QTY","STATUS"),
            show="headings"
        )
        for c in tree["columns"]:
            tree.heading(c, text=c)
            tree.column(c, width=180)
        tree.pack(fill="both", expand=True)

        valid = []

        for r in rows:
            tree.insert("", "end", values=(
                r["SN"], r["BARCODE"], r["ITEM"], r["QTY"], r["STATUS"]
            ))
            if r["STATUS"] == "OK":
                valid.append(r)

        def confirm():
            for r in valid:
                cur.execute("""
                    INSERT OR REPLACE INTO items
                    (SN, BARCODE, ITEM_NAME, ORIGINAL_QTY)
                    VALUES (?, ?, ?, ?)
                """, (r["SN"], r["BARCODE"], r["ITEM"], int(r["QTY"])))
            conn.commit()
            win.destroy()
            self.load_items()
            messagebox.showinfo("Success", f"{len(valid)} items imported")

        ttk.Button(win, text="CONFIRM IMPORT", command=confirm).pack(pady=10)

    def export_template(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return
        with open(file, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                ["SN","BARCODE","ITEM NAME","ORGINAL QTY"]
            )
        messagebox.showinfo("Template", "CSV template created")

    # ---------------- SCAN ----------------
    def scan_barcode(self, event=None):
        raw = self.scan_entry.get().strip()
        self.scan_entry.delete(0, tk.END)

        barcode, err = fix_barcode(raw)
        if err or not is_valid_barcode(barcode):
            self.status.config(text="✖ Invalid barcode", foreground="red")
            return

        cur.execute("SELECT id, ITEM_NAME, SCANNED_QTY FROM items WHERE BARCODE=?", (barcode,))
        item = cur.fetchone()

        if item:
            cur.execute("UPDATE items SET SCANNED_QTY=? WHERE id=?", (item[2]+1, item[0]))
            self.status.config(text=f"✔ {item[1]} scanned", foreground="green")
        else:
            cur.execute(
                "INSERT OR IGNORE INTO unmatched (BARCODE, QTY, FIRST_SEEN) VALUES (?,1,?)",
                (barcode, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.status.config(text=f"✖ {barcode} not found", foreground="red")

        conn.commit()
        winsound.Beep(1000, 100)
        self.load_items()

    # ---------------- LOAD ----------------
    def load_items(self):
        self.tree.delete(*self.tree.get_children())
        cur.execute("SELECT SN, BARCODE, ITEM_NAME, ORIGINAL_QTY, SCANNED_QTY FROM items")
        for r in cur.fetchall():
            self.tree.insert("", "end", values=r)

# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    StockApp(root)
    root.mainloop()
