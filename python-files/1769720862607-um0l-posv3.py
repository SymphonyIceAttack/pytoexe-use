# ------------------- DIPMED PHARMACY FULL-PHASE POS -------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, os, csv
from datetime import datetime
from barcode import Code128
from barcode.writer import ImageWriter
import matplotlib.pyplot as plt

# ------------------- DATABASE SETUP -------------------
DB_FILE = "abc.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Items table
c.execute('''CREATE TABLE IF NOT EXISTS items (
    item_code TEXT PRIMARY KEY,
    item_name TEXT,
    batch TEXT,
    exp_date TEXT,
    unit_price REAL,
    sale_rate REAL,
    cost_price REAL,
    vat REAL,
    full_pack_qty INTEGER,
    granular_qty INTEGER,
    qty INTEGER,
    total_cost_price REAL,
    total_sale_rate REAL
)''')

# Sales table
c.execute('''CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    qty INTEGER,
    sale_rate REAL,
    total REAL,
    date TEXT,
    payment_method TEXT
)''')

# Purchases table
c.execute('''CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    qty INTEGER,
    cost_price REAL,
    total REAL,
    date TEXT
)''')

# Sales return
c.execute('''CREATE TABLE IF NOT EXISTS sales_return (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    qty INTEGER,
    refund REAL,
    date TEXT
)''')

# Purchase return
c.execute('''CREATE TABLE IF NOT EXISTS purchase_return (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    qty INTEGER,
    refund REAL,
    date TEXT
)''')

# Pharmacy details
c.execute('''CREATE TABLE IF NOT EXISTS pharmacy_details (
    name TEXT,
    phone TEXT,
    address TEXT,
    vat TEXT,
    software_info TEXT
)''')
conn.commit()
conn.close()

# ------------------- HELPER FUNCTIONS -------------------
def run_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def fetch_query(query, params=()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

# ------------------- PHARMACY DETAILS -------------------
def save_pharmacy_details(name, phone, address, vat):
    software_info = "DipMed - Developer Dipesh Tajpuriya"
    run_query("DELETE FROM pharmacy_details")
    run_query("INSERT INTO pharmacy_details VALUES (?,?,?,?,?)", (name, phone, address, vat, software_info))
    messagebox.showinfo("Saved", "Pharmacy details saved!")

def get_pharmacy_details():
    data = fetch_query("SELECT * FROM pharmacy_details")
    if data:
        return data[0]
    return ("Your Pharmacy","Phone","Address","VAT","DipMed - Developer Dipesh Tajpuriya")

# ------------------- BARCODE -------------------
def generate_barcode(item_code):
    barcode_obj = Code128(item_code, writer=ImageWriter(), add_checksum=False)
    filename = f"barcode_{item_code}.png"
    barcode_obj.save(filename)
    messagebox.showinfo("Barcode", f"Barcode saved as {filename}")

# ------------------- MONEY DRAWER -------------------
def open_money_drawer():
    messagebox.showinfo("Money Drawer", "Money drawer function simulated!")

# ------------------- CSV IMPORT -------------------
def import_csv():
    file = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not file: return
    with open(file,"r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                run_query('''INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                    row['ITEM CODE'],row['ITEM NAME'],row['BATCH'],row['EXP'],float(row['UNIT PRICE']),
                    float(row['SALE RATE']),float(row['COST PRICE']),float(row['VAT %']),
                    int(row['Full Pack Qty']),int(row['Granular Qty']),int(row['QTY']),
                    float(row['TotalCostPrice']),float(row['TotalSaleRate'])
                ))
            except Exception as e:
                messagebox.showerror("CSV Error",str(e))
    messagebox.showinfo("Success","CSV Imported")

# ------------------- STOCK -------------------
def show_stock():
    for widget in tab_stock.winfo_children():
        widget.destroy()
    items = fetch_query("SELECT * FROM items")
    tree = ttk.Treeview(tab_stock, columns=("Code","Name","Batch","Exp","Unit","Sale","Cost","VAT","Qty"), show="headings")
    for col in tree["columns"]:
        tree.heading(col,text=col)
    tree.pack(expand=True,fill="both")
    for i in items:
        tree.insert('',tk.END, values=(i[0],i[1],i[2],i[3],i[5],i[6],i[7],i[8],i[10]))
        # Alerts
        if i[10]<=5:
            messagebox.showwarning("Low Stock", f"{i[1]} stock is low ({i[10]} left)")
        if i[3]<=datetime.now().strftime("%Y-%m-%d"):
            messagebox.showwarning("Expiry Alert", f"{i[1]} is expired or expiring today")

# ------------------- SALES ENTRY -------------------
def add_sale(item_code,qty,payment_method):
    item = fetch_query("SELECT item_name, sale_rate, qty FROM items WHERE item_code=?",(item_code,))
    if not item: messagebox.showerror("Error","Item not found"); return
    name, rate, stock_qty = item[0]
    if qty>stock_qty: messagebox.showerror("Error","Not enough stock"); return
    total = rate*qty
    run_query("INSERT INTO sales (item_code,qty,sale_rate,total,date,payment_method) VALUES (?,?,?,?,?,?)",
              (item_code,qty,rate,total,datetime.now().strftime("%Y-%m-%d"),payment_method))
    run_query("UPDATE items SET qty=? WHERE item_code=?",(stock_qty-qty,item_code))
    print_bill_console(item_code, qty, rate, total, payment_method)
    messagebox.showinfo("Sale",f"Sale successful! Total: {total}")

# ------------------- PURCHASE ENTRY -------------------
def add_purchase(item_code, qty, cost_price):
    item = fetch_query("SELECT qty FROM items WHERE item_code=?",(item_code,))
    total = cost_price*qty
    run_query("INSERT INTO purchases (item_code,qty,cost_price,total,date) VALUES (?,?,?,?,?)",
              (item_code,qty,cost_price,total,datetime.now().strftime("%Y-%m-%d")))
    if item: run_query("UPDATE items SET qty=? WHERE item_code=?",(item[0][0]+qty,item_code))
    messagebox.showinfo("Purchase", f"Purchase recorded! Total: {total}")

# ------------------- RETURNS -------------------
def sales_return(item_code,qty):
    item = fetch_query("SELECT qty, sale_rate FROM items WHERE item_code=?",(item_code,))
    if not item: messagebox.showerror("Error","Item not found"); return
    stock_qty, rate = item[0]
    refund = qty*rate
    run_query("INSERT INTO sales_return (item_code,qty,refund,date) VALUES (?,?,?,?)",
              (item_code, qty, refund, datetime.now().strftime("%Y-%m-%d")))
    run_query("UPDATE items SET qty=? WHERE item_code=?",(stock_qty+qty,item_code))
    messagebox.showinfo("Return", f"Sales return processed. Refund: {refund}")

def purchase_return(item_code,qty):
    item = fetch_query("SELECT qty, cost_price FROM items WHERE item_code=?",(item_code,))
    if not item: messagebox.showerror("Error","Item not found"); return
    stock_qty, cost = item[0]
    refund = qty*cost
    run_query("INSERT INTO purchase_return (item_code,qty,refund,date) VALUES (?,?,?,?)",
              (item_code, qty, refund, datetime.now().strftime("%Y-%m-%d")))
    run_query("UPDATE items SET qty=? WHERE item_code=?",(stock_qty-qty,item_code))
    messagebox.showinfo("Return", f"Purchase return processed. Refund: {refund}")

# ------------------- BILL PRINT -------------------
def print_bill_console(item_code, qty, rate, total, payment_method):
    ph = get_pharmacy_details()
    bill = f"""
    -----------------------------
    {ph[0]} | VAT:{ph[3]}
    {ph[1]} | {ph[2]}
    Software: {ph[4]}
    Date:{datetime.now().strftime("%Y-%m-%d %H:%M")}
    -----------------------------
    Item:{item_code}
    Qty:{qty} x {rate} = {total}
    Payment: {payment_method}
    -----------------------------
    Thank you!
    -----------------------------
    """
    print(bill)

# ------------------- REPORTS -------------------
def daily_sales_report():
    today = datetime.now().strftime("%Y-%m-%d")
    sales = fetch_query("SELECT item_code, qty, total, payment_method FROM sales WHERE date=?",(today,))
    total_sales = sum([s[2] for s in sales])
    messagebox.showinfo("Daily Sales", f"Total Sales Today: {total_sales}")
    print(f"--- Daily Sales Report ({today}) ---")
    for s in sales: print(s)

def monthly_profit_loss(month):
    month_like = f"{month}-%"
    sales = fetch_query("SELECT total FROM sales WHERE date LIKE ?",(month_like,))
    purchases = fetch_query("SELECT total FROM purchases WHERE date LIKE ?",(month_like,))
    sales_total = sum([s[0] for s in sales])
    purchase_total = sum([p[0] for p in purchases])
    profit = sales_total - purchase_total
    plt.bar(["Sales","Purchases","Profit"],[sales_total,purchase_total,profit],color=['green','blue','orange'])
    plt.title(f"Monthly Sales & Profit ({month})")
    plt.show()
    messagebox.showinfo("Monthly Report",f"Sales:{sales_total}\nPurchases:{purchase_total}\nProfit:{profit}")

# ------------------- GUI -------------------
root = tk.Tk()
root.title("DipMed Pharmacy POS")
root.geometry("1200x700")

tab_control = ttk.Notebook(root)
tabs = {}
for t in ["Sales","Purchase","Sales Return","Purchase Return","Stock","Reports","Pharmacy Details","Money Drawer"]:
    tabs[t] = ttk.Frame(tab_control)
    tab_control.add(tabs[t], text=t)
tab_control.pack(expand=True, fill="both")

tab_sales = tabs["Sales"]
tab_purchase = tabs["Purchase"]
tab_sales_return = tabs["Sales Return"]
tab_purchase_return = tabs["Purchase Return"]
tab_stock = tabs["Stock"]
tab_reports = tabs["Reports"]
tab_pharmacy = tabs["Pharmacy Details"]
tab_drawer = tabs["Money Drawer"]

# Pharmacy Tab
tk.Label(tab_pharmacy,text="Name").grid(row=0,column=0)
entry_name=tk.Entry(tab_pharmacy); entry_name.grid(row=0,column=1)
tk.Label(tab_pharmacy,text="Phone").grid(row=1,column=0)
entry_phone=tk.Entry(tab_pharmacy); entry_phone.grid(row=1,column=1)
tk.Label(tab_pharmacy,text="Address").grid(row=2,column=0)
entry_address=tk.Entry(tab_pharmacy); entry_address.grid(row=2,column=1)
tk.Label(tab_pharmacy,text="VAT").grid(row=3,column=0)
entry_vat=tk.Entry(tab_pharmacy); entry_vat.grid(row=3,column=1)
tk.Button(tab_pharmacy,text="Save", command=lambda: save_pharmacy_details(entry_name.get(),entry_phone.get(),entry_address.get(),entry_vat.get())).grid(row=4,column=0,columnspan=2)
ph_data = get_pharmacy_details()
entry_name.insert(0,ph_data[0]); entry_phone.insert(0,ph_data[1]); entry_address.insert(0,ph_data[2]); entry_vat.insert(0,ph_data[3])

# Stock Tab
tk.Button(tab_stock,text="Import CSV",command=import_csv).pack(pady=5)
tk.Button(tab_stock,text="Show Stock & Alerts",command=show_stock).pack(pady=5)

# Reports Tab
tk.Button(tab_reports,text="Daily Sales",command=daily_sales_report).pack(pady=5)
tk.Button(tab_reports,text="Monthly Profit/Loss",command=lambda: monthly_profit_loss(datetime.now().strftime("%Y-%m"))).pack(pady=5)

# Money Drawer Tab
tk.Button(tab_drawer,text="Open Money Drawer",command=open_money_drawer).pack(pady=50)

root.mainloop()
