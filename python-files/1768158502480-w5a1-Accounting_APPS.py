import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# ---------- DATABASE ----------
conn = sqlite3.connect("accounting.db")
c = conn.cursor()

# Transactions table
c.execute("""CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY,
date TEXT,
category TEXT,
type TEXT,
amount REAL,
description TEXT
)""")

# Customers table
c.execute("""CREATE TABLE IF NOT EXISTS customers(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT,
email TEXT
)""")

# Suppliers table
c.execute("""CREATE TABLE IF NOT EXISTS suppliers(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT,
email TEXT
)""")

# Inventory table
c.execute("""CREATE TABLE IF NOT EXISTS inventory(
id INTEGER PRIMARY KEY,
product TEXT,
qty INTEGER,
price REAL
)""")

conn.commit()

# ---------- FUNCTIONS ----------
def add_transaction(t_type):
    amt = amount.get()
    cat = category.get()
    desc = description.get()
    if not amt or not cat:
        messagebox.showerror("Error", "Category and Amount required")
        return
    c.execute("INSERT INTO transactions VALUES(NULL,?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d"), cat, t_type, float(amt), desc))
    conn.commit()
    amount.delete(0, tk.END)
    description.delete(0, tk.END)
    messagebox.showinfo("Success", f"{t_type} added")

def add_customer():
    if not cust_name.get():
        messagebox.showerror("Error", "Name required")
        return
    c.execute("INSERT INTO customers VALUES(NULL,?,?,?)",
              (cust_name.get(), cust_phone.get(), cust_email.get()))
    conn.commit()
    messagebox.showinfo("Success", "Customer added")

def add_supplier():
    if not sup_name.get():
        messagebox.showerror("Error", "Name required")
        return
    c.execute("INSERT INTO suppliers VALUES(NULL,?,?,?)",
              (sup_name.get(), sup_phone.get(), sup_email.get()))
    conn.commit()
    messagebox.showinfo("Success", "Supplier added")

def add_product():
    if not prod_name.get() or not prod_qty.get() or not prod_price.get():
        messagebox.showerror("Error", "All fields required")
        return
    c.execute("INSERT INTO inventory VALUES(NULL,?,?,?)",
              (prod_name.get(), int(prod_qty.get()), float(prod_price.get())))
    conn.commit()
    messagebox.showinfo("Success", "Product added")

def report():
    # Income
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    income = c.fetchone()[0] or 0
    # Expense
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    expense = c.fetchone()[0] or 0
    # Profit/Loss
    pl = income - expense
    messagebox.showinfo("Report",
        f"Total Income: {income}\nTotal Expense: {expense}\nProfit/Loss: {pl}")

# ---------- UI ----------
app = tk.Tk()
app.title("K&H Company Limited – Accounting Software")
app.geometry("500x650")

# Income / Expense
tk.Label(app, text="INCOME / EXPENSE", font=("Arial", 12, "bold")).pack(pady=5)
category = tk.Entry(app)
category.insert(0, "Category")
category.pack()
amount = tk.Entry(app)
amount.insert(0, "Amount")
amount.pack()
description = tk.Entry(app)
description.insert(0, "Description")
description.pack()
tk.Button(app, text="Add Income", bg="green", fg="white", command=lambda: add_transaction("Income")).pack(pady=2)
tk.Button(app, text="Add Expense", bg="red", fg="white", command=lambda: add_transaction("Expense")).pack(pady=2)
tk.Button(app, text="View Report", command=report).pack(pady=5)

# Customers
tk.Label(app, text="CUSTOMERS", font=("Arial", 12, "bold")).pack(pady=5)
cust_name = tk.Entry(app)
cust_name.insert(0, "Name")
cust_name.pack()
cust_phone = tk.Entry(app)
cust_phone.insert(0, "Phone")
cust_phone.pack()
cust_email = tk.Entry(app)
cust_email.insert(0, "Email")
cust_email.pack()
tk.Button(app, text="Add Customer", command=add_customer).pack(pady=2)

# Suppliers
tk.Label(app, text="SUPPLIERS", font=("Arial", 12, "bold")).pack(pady=5)
sup_name = tk.Entry(app)
sup_name.insert(0, "Name")
sup_name.pack()
sup_phone = tk.Entry(app)
sup_phone.insert(0, "Phone")
sup_phone.pack()
sup_email = tk.Entry(app)
sup_email.insert(0, "Email")
sup_email.pack()
tk.Button(app, text="Add Supplier", command=add_supplier).pack(pady=2)

# Inventory
tk.Label(app, text="INVENTORY", font=("Arial", 12, "bold")).pack(pady=5)
prod_name = tk.Entry(app)
prod_name.insert(0, "Product Name")
prod_name.pack()
prod_qty = tk.Entry(app)
prod_qty.insert(0, "Quantity")
prod_qty.pack()
prod_price = tk.Entry(app)
prod_price.insert(0, "Price")
prod_price.pack()
tk.Button(app, text="Add Product", command=add_product).pack(pady=2)

app.mainloop()