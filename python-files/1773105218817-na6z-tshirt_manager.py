import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

PASSWORD = "Pajarodidit"

# DATABASE
conn = sqlite3.connect("tshirt_records.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock(
id INTEGER PRIMARY KEY,
color TEXT,
quantity INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS prints(
id INTEGER PRIMARY KEY,
date TEXT,
customer TEXT,
color TEXT,
qty INTEGER,
price REAL,
total REAL
)
""")

conn.commit()


class TshirtApp:

    def __init__(self, root):

        self.root = root
        self.root.title("T-Shirt Business Manager")
        self.root.geometry("1100x650")

        self.login()

    # LOGIN
    def login(self):
        pw = simpledialog.askstring("Login", "Enter Password", show="*")
        if pw != PASSWORD:
            messagebox.showerror("Access Denied", "Wrong Password")
            self.root.destroy()
        else:
            self.build_ui()

    # INTERFACE
    def build_ui(self):

        top = tk.Frame(self.root, bg="#2c3e50", height=40)
        top.pack(fill="x")

        tk.Label(
            top,
            text="T-SHIRT MANAGEMENT APP",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        tk.Label(
            top,
            text="MAXWELLPAJARO SOFTWARE | 0599966047",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 10)
        ).pack(side="right", padx=10)

        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # SIDEBAR
        sidebar = tk.Frame(main, width=250, bg="#ecf0f1")
        sidebar.pack(side="left", fill="y")

        tk.Label(sidebar, text="Stock Bought", bg="#ecf0f1",
                 font=("Arial", 12, "bold")).pack(pady=10)

        self.color_entry = tk.Entry(sidebar)
        self.color_entry.pack(pady=5)

        self.stock_entry = tk.Entry(sidebar)
        self.stock_entry.pack(pady=5)

        tk.Button(
            sidebar,
            text="Add Stock",
            bg="#3498db",
            fg="white",
            command=self.add_stock
        ).pack(fill="x", padx=20, pady=5)

        tk.Button(
            sidebar,
            text="View Stock",
            bg="#3498db",
            fg="white",
            command=self.view_stock
        ).pack(fill="x", padx=20, pady=5)

        tk.Label(sidebar, text="Total Printed Today:",
                 bg="#ecf0f1").pack(pady=10)

        self.today_label = tk.Label(sidebar, text="0", bg="#ecf0f1")
        self.today_label.pack()

        tk.Label(sidebar, text="Remaining Shirts:",
                 bg="#ecf0f1").pack(pady=10)

        self.remaining_label = tk.Label(sidebar, text="0", bg="#ecf0f1")
        self.remaining_label.pack()

        # MAIN AREA
        workspace = tk.Frame(main)
        workspace.pack(fill="both", expand=True)

        form = tk.Frame(workspace)
        form.pack(fill="x", pady=10)

        self.date = tk.Entry(form)
        self.date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.date.grid(row=0, column=0, padx=5)

        self.customer = tk.Entry(form)
        self.customer.insert(0, "Customer Name")
        self.customer.grid(row=0, column=1, padx=5)

        self.color = tk.Entry(form)
        self.color.insert(0, "Color")
        self.color.grid(row=0, column=2, padx=5)

        self.qty = tk.Entry(form)
        self.qty.insert(0, "Qty")
        self.qty.grid(row=0, column=3, padx=5)

        self.price = tk.Entry(form)
        self.price.insert(0, "Price")
        self.price.grid(row=0, column=4, padx=5)

        tk.Button(
            form,
            text="Save Print Record",
            bg="#2980b9",
            fg="white",
            command=self.add_record
        ).grid(row=0, column=5, padx=10)

        # TABLE
        columns = ("ID", "Date", "Customer", "Color", "Qty", "Price", "Total")

        self.table = ttk.Treeview(
            workspace,
            columns=columns,
            show="headings"
        )

        for col in columns:
            self.table.heading(col, text=col)

        self.table.pack(fill="both", expand=True)

        btns = tk.Frame(workspace)
        btns.pack(pady=5)

        tk.Button(btns, text="Edit", command=self.edit_record).pack(side="left", padx=5)
        tk.Button(btns, text="Delete", command=self.delete_record).pack(side="left", padx=5)
        tk.Button(btns, text="Refresh", command=self.load_records).pack(side="left", padx=5)

        self.load_records()
        self.update_dashboard()

    # ADD STOCK
    def add_stock(self):

        color = self.color_entry.get()
        qty = int(self.stock_entry.get())

        cursor.execute("INSERT INTO stock(color,quantity) VALUES(?,?)",
                       (color, qty))
        conn.commit()

        messagebox.showinfo("Saved", "Stock added successfully")

        self.update_dashboard()

    # VIEW STOCK
    def view_stock(self):

        win = tk.Toplevel()
        win.title("Stock")

        tree = ttk.Treeview(win, columns=("Color", "Qty"), show="headings")
        tree.heading("Color", text="Color")
        tree.heading("Qty", text="Quantity")

        tree.pack(fill="both", expand=True)

        for row in cursor.execute("SELECT color,quantity FROM stock"):
            tree.insert("", "end", values=row)

    # ADD PRINT RECORD
    def add_record(self):

        try:
            date = self.date.get()
            customer = self.customer.get()
            color = self.color.get()
            qty = int(self.qty.get())
            price = float(self.price.get())

            total = qty * price

            cursor.execute("""
            INSERT INTO prints(date,customer,color,qty,price,total)
            VALUES(?,?,?,?,?,?)
            """, (date, customer, color, qty, price, total))

            conn.commit()

            self.load_records()
            self.update_dashboard()

        except:
            messagebox.showerror("Error", "Enter correct values")

    # LOAD RECORDS
    def load_records(self):

        for i in self.table.get_children():
            self.table.delete(i)

        for row in cursor.execute("SELECT * FROM prints"):
            self.table.insert("", "end", values=row)

    # DELETE
    def delete_record(self):

        selected = self.table.selection()

        if not selected:
            return

        record = self.table.item(selected[0])["values"][0]

        cursor.execute("DELETE FROM prints WHERE id=?", (record,))
        conn.commit()

        self.load_records()
        self.update_dashboard()

    # EDIT
    def edit_record(self):

        selected = self.table.selection()

        if not selected:
            return

        data = self.table.item(selected[0])["values"]

        new_qty = simpledialog.askinteger("Edit", "New Quantity", initialvalue=data[4])

        cursor.execute("UPDATE prints SET qty=? WHERE id=?", (new_qty, data[0]))
        conn.commit()

        self.load_records()
        self.update_dashboard()

    # DASHBOARD
    def update_dashboard(self):

        today = datetime.now().strftime("%d/%m/%Y")

        cursor.execute("SELECT SUM(qty) FROM prints WHERE date=?", (today,))
        total_today = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(quantity) FROM stock")
        total_stock = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(qty) FROM prints")
        total_printed = cursor.fetchone()[0] or 0

        remaining = total_stock - total_printed

        self.today_label.config(text=str(total_today))
        self.remaining_label.config(text=str(remaining))


root = tk.Tk()
app = TshirtApp(root)
root.mainloop()