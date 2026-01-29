# ------------------- DIPMED PHARMACY POS SYSTEM -------------------
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import csv
import os
from barcode import Code128
from barcode.writer import ImageWriter

# ------------------- DATABASE SETUP -------------------
conn = sqlite3.connect('abc.db')
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

# Sales return table
c.execute('''CREATE TABLE IF NOT EXISTS sales_return (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    qty INTEGER,
    refund REAL,
    date TEXT
)''')

# Purchase return table
c.execute('''CREATE TABLE IF NOT EXISTS purchase_return (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    qty INTEGER,
    refund REAL,
    date TEXT
)''')

# Pharmacy details table
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
    conn = sqlite3.connect('abc.db')
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def fetch_query(query, params=()):
    conn = sqlite3.connect('abc.db')
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

# ------------------- PHARMACY DETAILS -------------------
def save_pharmacy_details(name, phone, address, vat):
    software_info = "DipMed - Developer Dipesh Tajpuriya"
    run_query('DELETE FROM pharmacy_details')
    run_query('INSERT INTO pharmacy_details VALUES (?,?,?,?,?)', (name, phone, address, vat, software_info))
    messagebox.showinfo("Saved", "Pharmacy details saved!")

def get_pharmacy_details():
    data = fetch_query('SELECT * FROM pharmacy_details')
    if data:
        return data[0]
    else:
        return ("Your Pharmacy", "Phone", "Address", "VAT", "DipMed - Developer Dipesh Tajpuriya")

# ------------------- BARCODE GENERATION -------------------
def generate_barcode(item_code):
    barcode_obj = Code128(item_code, writer=ImageWriter(), add_checksum=False)
    filename = f"barcode_{item_code}.png"
    barcode_obj.save(filename)
    messagebox.showinfo("Barcode", f"Barcode saved as {filename}")

# ------------------- MONEY DRAWER -------------------
def open_money_drawer():
    try:
        os.system('echo "\x1B\x70\x00\x19\xFA" > LPT1')  # ESC/POS printer command
        messagebox.showinfo("Success", "Money drawer opened!")
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open drawer: {str(e)}")

# ------------------- CSV IMPORT -------------------
def import_csv():
    filename = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not filename:
        return
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                run_query('''
                    INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (
                    row['ITEM CODE'], row['ITEM NAME'], row['BATCH'], row['EXP'], row['UNIT PRICE'],
                    row['SALE RATE'], row['COST PRICE'], row['VAT %'], row['Full Pack Qty'], 
                    row['Granular Qty'], row['QTY'], row['TotalCostPrice'], row['TotalSaleRate']
                ))
            except Exception as e:
                messagebox.showerror("Error", f"Error importing CSV: {str(e)}")
    messagebox.showinfo("Success", "CSV Imported Successfully!")

# ------------------- STOCK -------------------
def show_stock():
    stock_items = fetch_query("SELECT * FROM items")
    for widget in tab_stock.winfo_children():
        widget.destroy()
    tree = ttk.Treeview(tab_stock, columns=("Code","Name","Batch","Exp","Unit Price","Sale Rate","Cost","VAT","Qty"), show='headings')
    for col in tree["columns"]:
        tree.heading(col, text=col)
    tree.pack(expand=True, fill='both')
    for item in stock_items:
        tree.insert('', tk.END, values=(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[10]))

# ------------------- SALES ENTRY -------------------
def add_sale(item_code, qty, payment_method):
    item = fetch_query("SELECT item_name, sale_rate, qty FROM items WHERE item_code=?", (item_code,))
    if not item:
        messagebox.showerror("Error", "Item not found")
        return
    name, sale_rate, stock_qty = item[0]
    if qty > stock_qty:
        messagebox.showerror("Error", "Not enough stock")
        return
    total = sale_rate * qty
    today = datetime.now().strftime("%Y-%m-%d")
    run_query("INSERT INTO sales (item_code, qty, sale_rate, total, date, payment_method) VALUES (?,?,?,?,?,?)",
              (item_code, qty, sale_rate, total, today, payment_method))
    # Update stock
    new_qty = stock_qty - qty
    run_query("UPDATE items SET qty=? WHERE item_code=?", (new_qty, item_code))
    messagebox.showinfo("Sale", f"Sale successful! Total: {total}")

# ------------------- PURCHASE ENTRY -------------------
def add_purchase(item_code, qty, cost_price):
    item = fetch_query("SELECT qty FROM items WHERE item_code=?", (item_code,))
    today = datetime.now().strftime("%Y-%m-%d")
    total = cost_price * qty
    run_query("INSERT INTO purchases (item_code, qty, cost_price, total, date) VALUES (?,?,?,?,?)",
              (item_code, qty, cost_price, total, today))
    if item:
        new_qty = item[0][0] + qty
        run_query("UPDATE items SET qty=? WHERE item_code=?", (new_qty, item_code))
    else:
        messagebox.showinfo("Purchase", "Item not in stock. Add to items first.")
    messagebox.showinfo("Purchase", f"Purchase recorded. Total: {total}")

# ------------------- RETURNS -------------------
def sales_return(item_code, qty):
    item = fetch_query("SELECT qty, sale_rate FROM items WHERE item_code=?", (item_code,))
    if not item:
        messagebox.showerror("Error", "Item not found")
        return
    stock_qty, sale_rate = item[0]
    refund = qty * sale_rate
    today = datetime.now().strftime("%Y-%m-%d")
    run_query("INSERT INTO sales_return (item_code, qty, refund, date) VALUES (?,?,?,?)",
              (item_code, qty, refund, today))
    # Update stock
    run_query("UPDATE items SET qty=? WHERE item_code=?", (stock_qty+qty, item_code))
    messagebox.showinfo("Return", f"Sales return processed. Refund: {refund}")

def purchase_return(item_code, qty):
    item = fetch_query("SELECT qty, cost_price FROM items WHERE item_code=?", (item_code,))
    if not item:
        messagebox.showerror("Error", "Item not found")
        return
    stock_qty, cost_price = item[0]
    refund = qty * cost_price
    today = datetime.now().strftime("%Y-%m-%d")
    run_query("INSERT INTO purchase_return (item_code, qty, refund, date) VALUES (?,?,?,?)",
              (item_code, qty, refund, today))
    run_query("UPDATE items SET qty=? WHERE item_code=?", (stock_qty-qty, item_code))
    messagebox.showinfo("Return", f"Purchase return processed. Refund: {refund}")

# ------------------- BILL PRINTING -------------------
def print_bill(sale_id):
    sale = fetch_query("SELECT item_code, qty, sale_rate, total, date, payment_method FROM sales WHERE id=?", (sale_id,))
    if not sale:
        messagebox.showerror("Error", "Sale not found")
        return
    sale = sale[0]
    item_code, qty, sale_rate, total, date, payment_method = sale
    pharmacy = get_pharmacy_details()
    bill = f"""
    {pharmacy[0]} | {pharmacy[3]}
    {pharmacy[1]} | {pharmacy[2]}
    Software: {pharmacy[4]}
    Date: {date}
    -------------------------
    Item: {item_code}
    Qty: {qty} x {sale_rate}
    -------------------------
    Total: {total}
    Payment Method: {payment_method}
    -------------------------
    Thank you!
    """
    print(bill)
    messagebox.showinfo("Bill", f"Bill printed in console\n{bill}")

# ------------------- REPORTS -------------------
def daily_sales_report():
    today = datetime.now().strftime("%Y-%m-%d")
    sales = fetch_query("SELECT item_code, qty, total, payment_method FROM sales WHERE date=?", (today,))
    report = f"Daily Sales Report ({today})\n-----------------\n"
    total_sales = 0
    for s in sales:
        report += f"{s[0]} | {s[1]} x {s[2]/s[1]} | {s[2]} | {s[3]}\n"
        total_sales += s[2]
    report += f"Total Sales: {total_sales}\n"
    print(report)
    messagebox.showinfo("Daily Sales", f"Check console for detailed report.\nTotal: {total_sales}")

def monthly_profit_loss(month):
    month_like = f"{month}-%"
    sales = fetch_query("SELECT item_code, qty, total FROM sales WHERE date LIKE ?", (month_like,))
    purchases = fetch_query("SELECT item_code, qty, total FROM purchases WHERE date LIKE ?", (month_like,))
    sales_total = sum([s[2] for s in sales])
    purchase_total = sum([p[2] for p in purchases])
    profit = sales_total - purchase_total
    messagebox.showinfo("Monthly Report", f"Sales: {sales_total}\nPurchases: {purchase_total}\nProfit: {profit}")

# ------------------- GUI SETUP -------------------
root = tk.Tk()
root.title("DipMed Pharmacy POS")
root.geometry("1200x700")

tab_control = ttk.Notebook(root)
tab_sales = ttk.Frame(tab_control)
tab_purchase = ttk.Frame(tab_control)
tab_sales_return = ttk.Frame(tab_control)
tab_purchase_return = ttk.Frame(tab_control)
tab_stock = ttk.Frame(tab_control)
tab_reports = ttk.Frame(tab_control)
tab_pharmacy = ttk.Frame(tab_control)
tab_drawer = ttk.Frame(tab_control)

tab_control.add(tab_sales, text='Sales')
tab_control.add(tab_purchase, text='Purchase')
tab_control.add(tab_sales_return, text='Sales Return')
tab_control.add(tab_purchase_return, text='Purchase Return')
tab_control.add(tab_stock, text='Stock')
tab_control.add(tab_reports, text='Reports')
tab_control.add(tab_pharmacy, text='Pharmacy Details')
tab_control.add(tab_drawer, text='Money Drawer')
tab_control.pack(expand=1, fill="both")

# ------------------- PHARMACY DETAILS TAB ------------------
tk.Label(tab_pharmacy, text="Pharmacy Name").grid(row=0, column=0)
entry_name = tk.Entry(tab_pharmacy); entry_name.grid(row=0,column=1)
tk.Label(tab_pharmacy, text="Phone").grid(row=1,column=0)
entry_phone = tk.Entry(tab_pharmacy); entry_phone.grid(row=1,column=1)
tk.Label(tab_pharmacy, text="Address").grid(row=2,column=0)
entry_address = tk.Entry(tab_pharmacy); entry_address.grid(row=2,column=1)
tk.Label(tab_pharmacy, text="VAT Number").grid(row=3,column=0)
entry_vat = tk.Entry(tab_pharmacy); entry_vat.grid(row=3,column=1)
tk.Button(tab_pharmacy, text="Save Details", command=lambda: save_pharmacy_details(entry_name.get(), entry_phone.get(), entry_address.get(), entry_vat.get())).grid(row=4,column=0,columnspan=2)

pharmacy_data = get_pharmacy_details()
entry_name.insert(0, pharmacy_data[0])
entry_phone.insert(0, pharmacy_data[1])
entry_address.insert(0, pharmacy_data[2])
entry_vat.insert(0, pharmacy_data[3])

# ------------------- STOCK TAB ------------------
tk.Button(tab_stock, text="Import CSV", command=import_csv).pack(pady=5)
tk.Button(tab_stock, text="Show Stock", command=show_stock).pack(pady=5)

# ------------------- REPORTS TAB ------------------
tk.Button(tab_reports, text="Daily Sales Report", command=daily_sales_report).pack(pady=5)
tk.Button(tab_reports, text="Monthly Profit/Loss", command=lambda: monthly_profit_loss(datetime.now().strftime("%Y-%m"))).pack(pady=5)
tk.Button(tab_drawer, text="Open Money Drawer", command=open_money_drawer).pack(pady=50)

root.mainloop()
