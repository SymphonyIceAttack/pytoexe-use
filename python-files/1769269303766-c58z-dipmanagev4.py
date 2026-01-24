import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
import winsound

APP_NAME = "DIP MANAGE - Manual Stock Take"

class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x650")

        self.data = {}      # barcode -> item dict
        self.scanned = {}   # barcode -> scanned qty
        self.sound_on = True

        self.create_ui()

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

    # ---------------- MAIN TAB ----------------
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

    # ---------------- REPORT TAB ----------------
    def build_report_tab(self):
        btns = ttk.Frame(self.tab_report)
        btns.pack(pady=10)

        ttk.Button(btns, text="Matched Items", command=self.report_matched).pack(side="left", padx=5)
        ttk.Button(btns, text="Unmatched Items", command=self.report_unmatched).pack(side="left", padx=5)
        ttk.Button(btns, text="Difference Report", command=self.report_difference).pack(side="left", padx=5)
        ttk.Button(btns, text="Export Report", command=self.export_report).pack(side="left", padx=5)

        self.report_tree = ttk.Treeview(self.tab_report, show="headings")
        self.report_tree.pack(fill="both", expand=True)

    # ---------------- SETTINGS ----------------
    def build_settings_tab(self):
        ttk.Label(self.tab_settings, text="App Settings", font=("Arial", 14)).pack(pady=10)

        ttk.Button(self.tab_settings, text="Toggle Sound", command=self.toggle_sound).pack(pady=5)
        ttk.Button(self.tab_settings, text="Blue Theme", command=lambda:self.change_theme("#dbe9ff")).pack(pady=5)
        ttk.Button(self.tab_settings, text="Dark Theme", command=lambda:self.change_theme("#2b2b2b")).pack(pady=5)

    # ---------------- ABOUT ----------------
    def build_about_tab(self):
        about_text = """
DIP MANAGE FOR MANUAL STOCK TAKE

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

        self.data.clear()
        self.scanned.clear()
        self.tree.delete(*self.tree.get_children())

        with open(file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                barcode = row["BARCODE"]
                self.data[barcode] = {
                    "SN": row["SN"],
                    "ITEM": row["ITEM NAME"],
                    "ORIGINAL": int(row["ORGINAL QTY"])
                }
                self.scanned[barcode] = 0

        messagebox.showinfo("Imported", "CSV data imported successfully.")

    def export_template(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return

        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["SN","BARCODE","ITEM NAME","ORGINAL QTY"])

        messagebox.showinfo("Template", "Blank CSV template exported.")

    def scan_barcode(self, event):
        barcode = self.scan_entry.get().strip()
        self.scan_entry.delete(0, tk.END)

        if barcode in self.data:
            self.scanned[barcode] += 1
            item = self.data[barcode]
            self.last_scan_label.config(
                text=f"Last Scan: {item['ITEM']} | Qty: {self.scanned[barcode]}"
            )
            if self.sound_on:
                winsound.Beep(1000, 100)
            self.refresh_table()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for b, item in self.data.items():
            self.tree.insert("", "end", values=(
                item["SN"], b, item["ITEM"], item["ORIGINAL"], self.scanned.get(b,0)
            ))

    def report_matched(self):
        self.load_report(
            ["SN","BARCODE","ITEM","SCANNED"],
            [(v["SN"],k,v["ITEM"],self.scanned[k]) for k,v in self.data.items() if self.scanned[k]>0]
        )

    def report_unmatched(self):
        self.load_report(
            ["SN","BARCODE","ITEM","ORIGINAL"],
            [(v["SN"],k,v["ITEM"],v["ORIGINAL"]) for k,v in self.data.items() if self.scanned[k]==0]
        )

    def report_difference(self):
        self.load_report(
            ["SN","BARCODE","ITEM","ORIGINAL","NEW","VARIATION"],
            [(v["SN"],k,v["ITEM"],v["ORIGINAL"],self.scanned[k],self.scanned[k]-v["ORIGINAL"])
             for k,v in self.data.items()]
        )

    def load_report(self, cols, rows):
        self.report_tree.delete(*self.report_tree.get_children())
        self.report_tree["columns"] = cols
        for c in cols:
            self.report_tree.heading(c, text=c)
            self.report_tree.column(c, width=180)
        for r in rows:
            self.report_tree.insert("", "end", values=r)

    def export_report(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return

        with open(file,"w",newline="",encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.report_tree["columns"])
            for row in self.report_tree.get_children():
                writer.writerow(self.report_tree.item(row)["values"])

        messagebox.showinfo("Exported", "Report exported successfully.")

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
