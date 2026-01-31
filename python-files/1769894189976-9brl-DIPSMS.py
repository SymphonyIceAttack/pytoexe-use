import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, csv
from datetime import datetime

DB = "DIPSMS.db"

# ---------------- DATABASE ----------------
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS pharmacy(
        id INTEGER PRIMARY KEY, name TEXT, address TEXT, phone TEXT, vat TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS suppliers(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        entry_date TEXT,
        total REAL,
        payment_type TEXT,
        paid REAL,
        credit REAL
    )""")
    con.commit(); con.close()

# ---------------- MAIN APP ----------------
class DIPSMSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DIP Supplier Management System")
        self.root.geometry("1000x600")

        self.tab = ttk.Notebook(root)
        self.tab.pack(fill="both", expand=True)

        self.pharmacy_tab()
        self.supplier_tab()
        self.purchase_tab()
        self.report_tab()
        self.import_tab()

        self.load_suppliers()
        self.load_pharmacy()

    # ---------------- PHARMACY ----------------
    def pharmacy_tab(self):
        frame = ttk.Frame(self.tab)
        self.tab.add(frame, text="Pharmacy Info")

        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ph_name = ttk.Entry(frame, width=40); self.ph_name.grid(row=0,column=1)
        ttk.Label(frame, text="Address").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ph_addr = ttk.Entry(frame, width=40); self.ph_addr.grid(row=1,column=1)
        ttk.Label(frame, text="Phone").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.ph_phone = ttk.Entry(frame, width=40); self.ph_phone.grid(row=2,column=1)
        ttk.Label(frame, text="VAT").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ph_vat = ttk.Entry(frame, width=40); self.ph_vat.grid(row=3,column=1)
        ttk.Button(frame, text="Save Pharmacy", command=self.save_pharmacy).grid(row=4,column=1,pady=10)

    def save_pharmacy(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("DELETE FROM pharmacy")
        cur.execute("INSERT INTO pharmacy VALUES(1,?,?,?,?)",
                    (self.ph_name.get(), self.ph_addr.get(), self.ph_phone.get(), self.ph_vat.get()))
        con.commit(); con.close()
        messagebox.showinfo("Saved","Pharmacy details saved")

    def load_pharmacy(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT name,address,phone,vat FROM pharmacy")
        r = cur.fetchone(); con.close()
        if r:
            self.ph_name.insert(0,r[0]); self.ph_addr.insert(0,r[1])
            self.ph_phone.insert(0,r[2]); self.ph_vat.insert(0,r[3])

    # ---------------- SUPPLIER ----------------
    def supplier_tab(self):
        frame = ttk.Frame(self.tab)
        self.tab.add(frame, text="Suppliers")

        ttk.Label(frame, text="Supplier Name").grid(row=0,column=0,padx=5,pady=5)
        self.sup_name = ttk.Entry(frame,width=40); self.sup_name.grid(row=0,column=1)
        ttk.Button(frame,text="Add Supplier",command=self.add_supplier).grid(row=0,column=2,padx=5)

    def add_supplier(self):
        if not self.sup_name.get(): return
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO suppliers(name) VALUES(?)",(self.sup_name.get(),))
        con.commit(); con.close()
        self.sup_name.delete(0,"end")
        self.load_suppliers()
        messagebox.showinfo("Added","Supplier added successfully")

    def load_suppliers(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT name FROM suppliers ORDER BY name")
        self.suppliers = [r[0] for r in cur.fetchall()]; con.close()

    # ---------------- PURCHASE ----------------
    def purchase_tab(self):
        frame = ttk.Frame(self.tab)
        self.tab.add(frame, text="Purchase / Payment")

        ttk.Label(frame,text="Supplier").grid(row=0,column=0,padx=5,pady=5)
        self.cmb_supplier = ttk.Combobox(frame,values=self.suppliers,width=37); self.cmb_supplier.grid(row=0,column=1)
        ttk.Label(frame,text="Date").grid(row=1,column=0,padx=5,pady=5)
        self.entry_date = ttk.Entry(frame); self.entry_date.grid(row=1,column=1); self.entry_date.insert(0,datetime.today().strftime("%Y-%m-%d"))
        ttk.Label(frame,text="Total Bill").grid(row=2,column=0,padx=5,pady=5)
        self.entry_total = ttk.Entry(frame); self.entry_total.grid(row=2,column=1)
        ttk.Label(frame,text="Payment Type").grid(row=3,column=0,padx=5,pady=5)
        self.cmb_payment = ttk.Combobox(frame,values=["Cash","Cheque","Credit"]); self.cmb_payment.grid(row=3,column=1)
        self.cmb_payment.current(0)
        ttk.Label(frame,text="Paid Amount").grid(row=4,column=0,padx=5,pady=5)
        self.entry_paid = ttk.Entry(frame); self.entry_paid.grid(row=4,column=1)
        ttk.Button(frame,text="Save Purchase",command=self.save_purchase).grid(row=5,column=1,pady=10)

    def save_purchase(self):
        supplier = self.cmb_supplier.get(); total = float(self.entry_total.get() or 0)
        paid = float(self.entry_paid.get() or 0); credit = total - paid
        date_str = self.entry_date.get(); payment_type = self.cmb_payment.get()
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""INSERT INTO purchases(supplier_id,entry_date,total,payment_type,paid,credit)
        VALUES((SELECT id FROM suppliers WHERE name=?),?,?,?,?,?)""",
                    (supplier,date_str,total,payment_type,paid,credit))
        con.commit(); con.close()
        messagebox.showinfo("Saved","Purchase saved successfully")
        self.entry_total.delete(0,"end"); self.entry_paid.delete(0,"end")

    # ---------------- REPORTS ----------------
    def report_tab(self):
        frame = ttk.Frame(self.tab)
        self.tab.add(frame,text="Reports")
        ttk.Button(frame,text="Supplier Ledger",command=self.ledger_preview).pack(pady=5)
        ttk.Button(frame,text="Advance Cheque / Credit",command=self.advance_preview).pack(pady=5)

    def ledger_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""SELECT s.name,SUM(p.total),SUM(p.paid),SUM(p.credit) FROM suppliers s
        LEFT JOIN purchases p ON s.id=p.supplier_id GROUP BY s.id""")
        data = cur.fetchall(); con.close()
        self.show_table(data,["Supplier","Total Purchase","Total Paid","Balance"],"Supplier Ledger")

    def advance_preview(self):
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("""SELECT s.name,p.entry_date,p.payment_type,p.paid,p.credit FROM purchases p
        JOIN suppliers s ON s.id=p.supplier_id WHERE p.payment_type IN ('Cheque','Credit')""")
        data = cur.fetchall(); con.close()
        self.show_table(data,["Supplier","Date","Mode","Paid","Credit"],"Advance Cheque / Credit")

    def show_table(self,data,headers,title):
        win = tk.Toplevel(self.root); win.title(title)
        tree = ttk.Treeview(win,columns=headers,show="headings")
        for h in headers: tree.heading(h,text=h)
        for row in data: tree.insert("","end",values=row)
        tree.pack(fill="both",expand=True)
        ttk.Button(win,text="Export CSV",command=lambda: self.export_csv(data,headers)).pack(pady=5)

    def export_csv(self,data,headers):
        path = filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV files","*.csv")])
        if not path: return
        with open(path,"w",newline="") as f: w = csv.writer(f); w.writerow(headers); w.writerows(data)
        messagebox.showinfo("Exported","CSV exported successfully")

    # ---------------- IMPORT ----------------
    def import_tab(self):
        frame = ttk.Frame(self.tab)
        self.tab.add(frame,text="CSV Import")
        ttk.Button(frame,text="Import Purchase CSV",command=self.import_csv).pack(pady=20)

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
        if not path: return
        con = sqlite3.connect(DB); cur = con.cursor()
        with open(path,newline="") as f: reader = csv.DictReader(f)
        for row in reader:
            cur.execute("INSERT OR IGNORE INTO suppliers(name) VALUES(?)",(row["Vendor Name"],))
            cur.execute("""INSERT INTO purchases(supplier_id,entry_date,total,payment_type,paid,credit)
            VALUES((SELECT id FROM suppliers WHERE name=?),?,?,?,?,?)""",
                        (row["Vendor Name"],row["Date"],float(row["Total Incl. VAT"]),"Credit",float(row["Total Incl. VAT"]),float(row["Total Incl. VAT"])))
        con.commit(); con.close()
        self.load_suppliers()
        messagebox.showinfo("Imported","CSV imported successfully")
