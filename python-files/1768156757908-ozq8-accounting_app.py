import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

# DATABASE
conn = sqlite3.connect("accounting.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY,
date TEXT,
type TEXT,
amount REAL,
description TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS customers(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS suppliers(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS inventory(
id INTEGER PRIMARY KEY,
product TEXT,
qty INTEGER
)""")

conn.commit()

# FUNCTIONS
def add_income():
    save_transaction("Income")

def add_expense():
    save_transaction("Expense")

def save_transaction(t_type):
    amt = amount.get()
    desc = description.get()
    if amt == "":
        messagebox.showerror("Error", "Amount required")
        return
    c.execute("INSERT INTO transactions VALUES(NULL,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d"), t_type, float(amt), desc))
    conn.commit()
    amount.delete(0, tk.END)
    description.delete(0, tk.END)
    messagebox.showinfo("Success", f"{t_type} added")

def add_customer():
    c.execute("INSERT INTO customers VALUES(NULL,?,?)",
              (cust_name.get(), cust_phone.get()))
    conn.commit()
    messagebox.showinfo("Success", "Customer added")

def add_supplier():
    c.execute("INSERT INTO suppliers VALUES(NULL,?,?)",
              (sup_name.get(), sup_phone.get()))
    conn.commit()
    messagebox.showinfo("Success", "Supplier added")

def add_product():
    c.execute("INSERT INTO inventory VALUES(NULL,?,?)",
              (prod_name.get(), int(prod_qty.get())))
    conn.commit()
    messagebox.showinfo("Success", "Product added")

def report():
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Expense'")
    expense = c.fetchone()[0] or 0
    messagebox.showinfo("Report",
        f"Total Income: {income}\nTotal Expense: {expense}\nBalance: {income-expense}")

# UI
app = tk.Tk()
app.title("K&H Company Limited – Accounting Software")
app.geometry("420x600")

tk.Label(app, text="INCOME / EXPENSE").pack()
amount = tk.Entry(app)
amount.pack()
description = tk.Entry(app)
description.pack()

tk.Button(app, text="Add Income", bg="green", fg="white", command=add_income).pack(pady=3)
tk.Button(app, text="Add Expense", bg="red", fg="white", command=add_expense).pack(pady=3)
tk.Button(app, text="View Report", command=report).pack(pady=10)

tk.Label(app, text="CUSTOMER").pack()
cust_name = tk.Entry(app)
cust_name.insert(0, "Name")
cust_name.pack()
cust_phone = tk.Entry(app)
cust_phone.insert(0, "Phone")
cust_phone.pack()
tk.Button(app, text="Add Customer", command=add_customer).pack(pady=5)

tk.Label(app, text="SUPPLIER").pack()
sup_name = tk.Entry(app)
sup_name.insert(0, "Name")
sup_name.pack()
sup_phone = tk.Entry(app)
sup_phone.insert(0, "Phone")
sup_phone.pack()
tk.Button(app, text="Add Supplier", command=add_supplier).pack(pady=5)

tk.Label(app, text="INVENTORY").pack()
prod_name = tk.Entry(app)
prod_name.insert(0, "Product Name")
prod_name.pack()
prod_qty = tk.Entry(app)
prod_qty.insert(0, "Quantity")
prod_qty.pack()
tk.Button(app, text="Add Product", command=add_product).pack(pady=5)

app.mainloop()