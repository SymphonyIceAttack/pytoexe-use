# tools_plugin.py
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import csv
from datetime import datetime

def build_tools_tab(tab, cur, conn, PLUGINS_DIR, VERSIONS_DIR):
    tk.Label(tab, text="Tools / Utilities", font=("Arial", 14, "bold")).pack(pady=10)

    btn_frame = tk.Frame(tab)
    btn_frame.pack(pady=10)

    # ---------------- Import CSV ----------------
    def import_data():
        file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file:
            return
        try:
            with open(file, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                imported = 0
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
                        imported += 1
                    except Exception:
                        pass  # ignore duplicates
                conn.commit()
            messagebox.showinfo("Import Successful", f"Imported {imported} items successfully")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))

    # ---------------- Export All Items ----------------
    def export_data():
        cur.execute("SELECT item_name, barcode, quantity FROM items ORDER BY item_name")
        data = cur.fetchall()
        if not data:
            messagebox.showinfo("Info", "No data to export")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file:
            with open(file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Item Name", "Barcode", "Quantity"])
                writer.writerows(data)
            messagebox.showinfo("Export Successful", "Data exported successfully")

    # ---------------- Plugin Backup / Rollback ----------------
    def backup_plugins():
        backup_dir = os.path.join(VERSIONS_DIR, datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_dir, exist_ok=True)
        for f in os.listdir(PLUGINS_DIR):
            if f.endswith(".py"):
                shutil.copy(os.path.join(PLUGINS_DIR, f), backup_dir)
        messagebox.showinfo("Backup Done", f"Plugins backed up to {backup_dir}")

    tk.Button(btn_frame, text="Import CSV Data", width=20, command=import_data).grid(row=0, column=0, padx=5, pady=5)
    tk.Button(btn_frame, text="Export All Items", width=20, command=export_data).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(btn_frame, text="Backup Plugins", width=20, command=backup_plugins).grid(row=1, column=0, padx=5, pady=5)
