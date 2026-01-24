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

# ---------------- HELPER ----------------
def resource_path(filename):
    """Return absolute path for files (works in PyInstaller EXE)"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

# ---------------- DATABASE ----------------
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

# ---------------- APP ----------------
class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x650")
        self.sound_on = True

        self.create_ui()
        self.load_items_to_table()

    # ---------------- UI ----------------
    def create_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        self.tab_main = ttk.Frame(notebook)
        self.tab_report = ttk.Frame(notebook)
        self.tab_settings = ttk.Frame(notebook)
        self.tab_about = ttk.Frame(notebook)

        notebook.add(self.tab_main, text="Stock Take")
        notebook.add(self.tab_report, text="Reports")
        notebook.add(self.tab_settings, text="Settings")
        notebook.add(self.tab_about, text="About")

        self.build_main_tab()
        self.build_report_tab()
        self.build_settings_tab()
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

        self.last_scan_label = ttk.Label(self.tab_main, text="Last Scan: None", font=("Arial", 11))
        self.last_scan_label.pack(pady=5)

        self.tree = ttk.Treeview(self.tab_main, columns=("SN","BARCODE","ITEM","ORIGINAL","SCANNED"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180)
        self.tree.pack(fill="both", expand=True, pady=10)

    def build_report_tab(self):
        btns = ttk.Frame(self.tab_report)
        btns.pack(pady=10)

        ttk.Button(btns, text="Matched Items", command=self.report_matched).pack(side="left", padx=5)
        ttk.Button(btns, text="Unmatched Items", command=self.report_unmatched).pack(side="left", padx=5)
        ttk.Button(btns, text="Difference Report", command=self.report_difference).pack(side="left", padx=5)
        ttk.Button(btns, text="Export Report", command=self.export_report).pack(side="left", padx=5)

        self.report_tree = ttk.Treeview(self.tab_report, show="headings")
        self.report_tree.pack(fill="both", expand=True)

    def build_settings_tab(self):
        ttk.Label(self.tab_settings, text="App Settings", font=("Arial", 14)).pack(pady=10)
        ttk.Button(self.tab_settings, text="Toggle Sound", command=self.toggle_sound).pack(pady=5)
        ttk.Button(self.tab_settings, text="Blue Theme", command=lambda:self.change_theme("#dbe9ff")).pack(pady=5)
        ttk.Button(self.tab_settings, text="Dark Theme", command=lambda:self.change_theme("#2b2b2b")).pack(pady=5)

    def build_about_tab(self):
        about_text = f"""
{APP_NAME}

SOFTWARE DEVELOPER:
DIPESH TAJPURIYA

CONTACT:
www.ladybud@gmail.com
"""
        ttk.Label(self.tab_about, text=about_text, font=("Arial", 12), justify="center").pack(expand=True)

    # ---------------- FUNCTIONS ----------------
    def import_csv(self):
        file = filedialog.askopenfilename(filetypes=[("CSV Files","*.csv")])
        if not file:
            return
        try:
            with open(file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        cur.execute("""
                        INSERT OR REPLACE INTO items (SN, BARCODE, ITEM_NAME, ORIGINAL_QTY)
                        VALUES (?, ?, ?, ?)
                        """, (row["SN"], row["BARCODE"], row["ITEM NAME"], int(row["ORGINAL QTY"])))
                    except Exception:
                        continue
            conn.commit()
            messagebox.showinfo("Imported", "CSV data imported successfully.")
            self.load_items_to_table()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_template(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return
        with open(resource_path(os.path.basename(file)), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["SN","BARCODE","ITEM NAME","ORGINAL QTY"])
        messagebox.showinfo("Template", "Blank CSV template exported.")

    def scan_barcode(self, event=None):
        barcode = self.scan_entry.get().strip().replace("\t","").replace("\n","")
        self.scan_entry.delete(0, tk.END)

        if not barcode:
            return

        cur.execute("SELECT id, ITEM_NAME, SCANNED_QTY FROM items WHERE BARCODE=?", (barcode,))
        item = cur.fetchone()
        if item:
            new_qty = item[2] + 1
            cur.execute("UPDATE items SET SCANNED_QTY=? WHERE id=?", (new_qty, item[0]))
            conn.commit()
            self.last_scan_label.config(text=f"✔ {item[1]} | Qty: {new_qty}", fg="green")
        else:
            cur.execute("SELECT QTY FROM unmatched WHERE BARCODE=?", (barcode,))
            un = cur.fetchone()
            if un:
                cur.execute("UPDATE unmatched SET QTY=? WHERE BARCODE=?", (un[0]+1, barcode))
            else:
                cur.execute("INSERT INTO unmatched (BARCODE, QTY, FIRST_SEEN) VALUES (?, ?, ?)",
                            (barcode, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            self.last_scan_label.config(text=f"✖ Barcode {barcode} not found!", fg="red")

        if self.sound_on:
            winsound.Beep(1000, 100)

        self.load_items_to_table()
        self.scan_entry.focus()

    def load_items_to_table(self):
        self.tree.delete(*self.tree.get_children())
        cur.execute("SELECT SN, BARCODE, ITEM_NAME, ORIGINAL_QTY, SCANNED_QTY FROM items")
        for row in cur.fetchall():
            self.tree.insert("", "end", values=row)

    # ---------------- REPORTS ----------------
    def report_matched(self):
        self.load_report("MATCHED")

    def report_unmatched(self):
        self.load_report("UNMATCHED")

    def report_difference(self):
        self.load_report("DIFFERENCE")

    def load_report(self, type_):
        self.report_tree.delete(*self.report_tree.get_children())
        if type_=="MATCHED":
            cur.execute("SELECT SN, BARCODE, ITEM_NAME, SCANNED_QTY FROM items WHERE SCANNED_QTY>0")
            cols = ["SN","BARCODE","ITEM","SCANNED"]
        elif type_=="UNMATCHED":
            cur.execute("SELECT BARCODE, QTY, FIRST_SEEN FROM unmatched")
            cols = ["BARCODE","QTY","FIRST_SEEN"]
        else:
            cur.execute("SELECT SN, BARCODE, ITEM_NAME, ORIGINAL_QTY, SCANNED_QTY, (SCANNED_QTY-ORIGINAL_QTY) FROM items")
            cols = ["SN","BARCODE","ITEM","ORIGINAL","NEW","VARIATION"]

        self.report_tree["columns"] = cols
        for c in cols:
            self.report_tree.heading(c, text=c)
            self.report_tree.column(c, width=180)

        for row in cur.fetchall():
            self.report_tree.insert("", "end", values=row)

    def export_report(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return
        cols = self.report_tree["columns"]
        with open(resource_path(os.path.basename(file)), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            for row_id in self.report_tree.get_children():
                writer.writerow(self.report_tree.item(row_id)["values"])
        messagebox.showinfo("Exported", "Report exported successfully.")

    # ---------------- SETTINGS ----------------
    def toggle_sound(self):
        self.sound_on = not self.sound_on
        messagebox.showinfo("Sound", f"Sound {'ON' if self.sound_on else 'OFF'}")

    def change_theme(self, color):
        self.root.configure(bg=color)

# ---------------- RUN ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()
