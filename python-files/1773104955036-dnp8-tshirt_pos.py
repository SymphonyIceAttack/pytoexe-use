import tkinter as tk
from tkinter import ttk,messagebox,filedialog
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

PASSWORD="Pajarodidit"

conn=sqlite3.connect("tshirt_pos.db")
cursor=conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS records(
id INTEGER PRIMARY KEY AUTOINCREMENT,
date TEXT,
customer TEXT,
color TEXT,
qty INTEGER,
price REAL,
total REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock(
color TEXT PRIMARY KEY,
bought INTEGER,
printed INTEGER
)
""")

conn.commit()


class Login:

    def __init__(self,root):

        self.root=root
        root.title("POS Login")
        root.geometry("300x200")

        tk.Label(root,text="T-Shirt POS Login",font=("Arial",14)).pack(pady=20)

        self.password=tk.Entry(root,show="*")
        self.password.pack()

        tk.Button(root,text="Login",command=self.check).pack(pady=10)

    def check(self):

        if self.password.get()==PASSWORD:
            self.root.destroy()
            start_app()

        else:
            messagebox.showerror("Error","Wrong Password")


class POS:

    def __init__(self,root):

        self.root=root
        root.title("T-Shirt Printing POS Manager")
        root.geometry("1400x750")

        title=tk.Label(root,text="T-SHIRT PRINTING POS MANAGER",font=("Arial",22,"bold"))
        title.pack(pady=10)

        main=tk.Frame(root)
        main.pack(fill="both",expand=True)

        left=tk.Frame(main)
        left.pack(side="left",fill="y",padx=10)

        center=tk.Frame(main)
        center.pack(side="left",fill="both",expand=True)

        right=tk.Frame(main)
        right.pack(side="right",fill="y",padx=10)

        tk.Label(left,text="DATE").pack()
        self.date=tk.Entry(left)
        self.date.insert(0,datetime.now().strftime("%Y-%m-%d"))
        self.date.pack()

        tk.Label(left,text="CUSTOMER").pack()
        self.customer=tk.Entry(left)
        self.customer.pack()

        tk.Label(left,text="COLOR").pack()
        self.color=ttk.Combobox(left,values=self.get_colors())
        self.color.pack()

        tk.Label(left,text="QTY").pack()
        self.qty=tk.Entry(left)
        self.qty.pack()

        tk.Label(left,text="PRICE").pack()
        self.price=tk.Entry(left)
        self.price.pack()

        tk.Button(left,text="ADD PRINT JOB",command=self.add_record).pack(pady=5)
        tk.Button(left,text="UPDATE",command=self.edit_record).pack(pady=5)
        tk.Button(left,text="DELETE",command=self.delete_record).pack(pady=5)

        columns=("Date","Customer","Color","Qty","Price","Total")

        self.tree=ttk.Treeview(center,columns=columns,show="headings")

        for col in columns:
            self.tree.heading(col,text=col)

        self.tree.pack(fill="both",expand=True)

        self.tree.bind("<ButtonRelease-1>",self.select)

        dash=tk.LabelFrame(right,text="Business Dashboard")
        dash.pack(pady=10)

        self.today_label=tk.Label(dash,text="")
        self.today_label.pack()

        self.month_label=tk.Label(dash,text="")
        self.month_label.pack()

        tk.Button(right,text="Daily Report",command=self.daily_report).pack(pady=3)
        tk.Button(right,text="Monthly Report",command=self.monthly_report).pack(pady=3)
        tk.Button(right,text="Profit Chart",command=self.chart).pack(pady=3)
        tk.Button(right,text="Export Excel",command=self.export_excel).pack(pady=3)

        stock=tk.LabelFrame(root,text="Stock Manager")
        stock.pack(fill="x",pady=10)

        tk.Label(stock,text="COLOR").grid(row=0,column=0)
        tk.Label(stock,text="BOUGHT").grid(row=0,column=1)

        self.stock_color=tk.Entry(stock)
        self.stock_color.grid(row=1,column=0)

        self.stock_qty=tk.Entry(stock)
        self.stock_qty.grid(row=1,column=1)

        tk.Button(stock,text="Add Stock",command=self.add_stock).grid(row=1,column=2)
        tk.Button(stock,text="Delete Stock",command=self.delete_stock).grid(row=1,column=3)
        tk.Button(stock,text="View Stock",command=self.view_stock).grid(row=1,column=4)

        creator=tk.Label(root,text="Creator: MAXWELLPAJARO   Contact: 0599966047")
        creator.pack()

        self.load_data()
        self.update_dashboard()


    def get_colors(self):

        cursor.execute("SELECT color FROM stock")

        data=cursor.fetchall()

        return [i[0] for i in data]


    def add_record(self):

        date=self.date.get()
        customer=self.customer.get()
        color=self.color.get()
        qty=int(self.qty.get())
        price=float(self.price.get())

        total=qty*price

        cursor.execute("INSERT INTO records(date,customer,color,qty,price,total) VALUES(?,?,?,?,?,?)",
        (date,customer,color,qty,price,total))

        cursor.execute("UPDATE stock SET printed=printed+? WHERE color=?",(qty,color))

        conn.commit()

        self.load_data()
        self.update_dashboard()


    def load_data(self):

        for i in self.tree.get_children():
            self.tree.delete(i)

        cursor.execute("SELECT date,customer,color,qty,price,total FROM records")

        rows=cursor.fetchall()

        for row in rows:
            self.tree.insert("",tk.END,values=row)


    def select(self,event):

        item=self.tree.focus()

        values=self.tree.item(item,"values")

        if values:

            self.date.delete(0,tk.END)
            self.date.insert(0,values[0])

            self.customer.delete(0,tk.END)
            self.customer.insert(0,values[1])

            self.color.set(values[2])

            self.qty.delete(0,tk.END)
            self.qty.insert(0,values[3])

            self.price.delete(0,tk.END)
            self.price.insert(0,values[4])


    def delete_record(self):

        item=self.tree.focus()

        values=self.tree.item(item,"values")

        cursor.execute("DELETE FROM records WHERE date=? AND customer=?",(values[0],values[1]))

        conn.commit()

        self.load_data()


    def edit_record(self):

        item=self.tree.focus()

        values=self.tree.item(item,"values")

        qty=int(self.qty.get())
        price=float(self.price.get())
        total=qty*price

        cursor.execute("""
        UPDATE records
        SET date=?,customer=?,color=?,qty=?,price=?,total=?
        WHERE date=? AND customer=?
        """,(self.date.get(),self.customer.get(),self.color.get(),qty,price,total,values[0],values[1]))

        conn.commit()

        self.load_data()


    def add_stock(self):

        color=self.stock_color.get()
        qty=int(self.stock_qty.get())

        cursor.execute("INSERT OR IGNORE INTO stock(color,bought,printed) VALUES(?,?,0)",(color,qty))

        cursor.execute("UPDATE stock SET bought=bought+? WHERE color=?",(qty,color))

        conn.commit()

        self.color["values"]=self.get_colors()


    def delete_stock(self):

        color=self.stock_color.get()

        cursor.execute("DELETE FROM stock WHERE color=?",(color,))

        conn.commit()


    def view_stock(self):

        window=tk.Toplevel(self.root)

        tree=ttk.Treeview(window,columns=("Color","Bought","Printed","Remaining"),show="headings")

        for col in ("Color","Bought","Printed","Remaining"):
            tree.heading(col,text=col)

        tree.pack(fill="both",expand=True)

        cursor.execute("SELECT color,bought,printed FROM stock")

        rows=cursor.fetchall()

        for r in rows:

            remaining=r[1]-r[2]

            tree.insert("",tk.END,values=(r[0],r[1],r[2],remaining))


    def daily_report(self):

        today=datetime.now().strftime("%Y-%m-%d")

        cursor.execute("SELECT SUM(qty),SUM(total) FROM records WHERE date=?",(today,))

        data=cursor.fetchone()

        messagebox.showinfo("Daily Report",f"Shirts Printed: {data[0]}\nRevenue: {data[1]}")


    def monthly_report(self):

        month=datetime.now().strftime("%Y-%m")

        cursor.execute("SELECT SUM(qty),SUM(total) FROM records WHERE date LIKE ?",(month+'%',))

        data=cursor.fetchone()

        messagebox.showinfo("Monthly Report",f"Shirts Printed: {data[0]}\nRevenue: {data[1]}")


    def chart(self):

        cursor.execute("SELECT date,total FROM records")

        data=cursor.fetchall()

        dates=[i[0] for i in data]
        totals=[i[1] for i in data]

        plt.plot(dates,totals)
        plt.title("Revenue Growth")
        plt.xlabel("Date")
        plt.ylabel("Revenue")
        plt.show()


    def export_excel(self):

        cursor.execute("SELECT * FROM records")

        data=cursor.fetchall()

        df=pd.DataFrame(data,columns=["ID","Date","Customer","Color","Qty","Price","Total"])

        file=filedialog.asksaveasfilename(defaultextension=".xlsx")

        df.to_excel(file,index=False)

        messagebox.showinfo("Export","Excel Exported")


    def update_dashboard(self):

        today=datetime.now().strftime("%Y-%m-%d")
        month=datetime.now().strftime("%Y-%m")

        cursor.execute("SELECT SUM(total) FROM records WHERE date=?",(today,))
        today_rev=cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total) FROM records WHERE date LIKE ?",(month+'%',))
        month_rev=cursor.fetchone()[0]

        self.today_label.config(text=f"Revenue Today: {today_rev}")
        self.month_label.config(text=f"Revenue This Month: {month_rev}")


def start_app():

    root=tk.Tk()

    POS(root)

    root.mainloop()


login=tk.Tk()

Login(login)

login.mainloop()