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

# Customers
c.execute("""CREATE TABLE IF NOT EXISTS customers(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT,
email TEXT
)""")

# Suppliers
c.execute("""CREATE TABLE IF NOT EXISTS suppliers(
id INTEGER PRIMARY KEY,
name TEXT,
phone TEXT,
email TEXT
)""")

# Inventory
c.execute("""CREATE TABLE IF NOT EXISTS inventory(
id INTEGER PRIMARY KEY,
product TEXT,
qty INTEGER,
price REAL
)""")

# Equity (capital)
c.execute("""CREATE TABLE IF NOT EXISTS equity(
id INTEGER PRIMARY KEY,
amount REAL
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

# Income Statement / P&L
def income_statement():
    c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='Income' GROUP BY category")
    income_data = c.fetchall()
    c.execute("SELECT category, SUM(amount) FROM transactions WHERE type='Expense' GROUP BY category")
    expense_data = c.fetchall()

    report = "INCOME STATEMENT\n\nINCOME:\n"
    total_income = 0
    for cat, amt in income_data:
        report += f"{cat}: {amt}\n"
        total_income += amt
    report += f"Total Income: {total_income}\n\nEXPENSES:\n"
    total_expense = 0
    for cat, amt in expense_data:
        report += f"{cat}: {amt}\n"
        total_expense += amt
    report += f"Total Expense: {total_expense}\n\nNet Profit: {total_income - total_expense}"
    messagebox.showinfo("Income Statement", report)

# Balance Sheet
def balance_sheet():
    # Assets = Cash + Inventory value
    c.execute("SELECT SUM(amount) FROM transactions WHERE type='Income'")
    cash = c.fetchone()[0] or 0
    c.execute("SELECT SUM(qty*price) FROM inventor*
