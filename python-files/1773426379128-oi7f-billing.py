import tkinter as tk
from tkinter import ttk, messagebox
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
import datetime
import os

SHOP_NAME = "MOHIT TRADING COMPANY"
OWNER = "Owner: Mohit Kumar Mittal"
ADDRESS = "Sarafa Bazar, Faridpur"
PHONE = "Phone: 7017795365"

invoice_no = 1
items = []

def add_item():
    try:
        name = item_entry.get()
        qty = int(qty_entry.get())
        price = float(price_entry.get())

        total = qty * price
        items.append((name, qty, price, total))

        table.insert("", "end", values=(name, qty, price, total))

        item_entry.delete(0, tk.END)
        qty_entry.delete(0, tk.END)
        price_entry.delete(0, tk.END)

        update_total()
    except:
        messagebox.showerror("Error","Enter valid values")

def update_total():
    total = sum(i[3] for i in items)
    total_label.config(text=f"Total: ₹{total}")

def new_invoice():
    global invoice_no, items
    invoice_no += 1
    items = []

    for row in table.get_children():
        table.delete(row)

    invoice_label.config(text=f"Invoice No: {invoice_no}")
    total_label.config(text="Total: ₹0")

def save_pdf():
    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%Y")
    time = now.strftime("%H:%M:%S")

    filename = f"invoice_{invoice_no}.pdf"

    c = canvas.Canvas(filename, pagesize=(58*mm, 200*mm))

    y = 190

    c.setFont("Helvetica-Bold",8)
    c.drawCentredString(80,y,SHOP_NAME)
    y -= 10

    c.setFont("Helvetica",7)
    c.drawCentredString(80,y,OWNER)
    y -= 8
    c.drawCentredString(80,y,ADDRESS)
    y -= 8
    c.drawCentredString(80,y,PHONE)

    y -= 12
    c.drawString(10,y,f"Invoice No: {invoice_no}")
    y -= 8
    c.drawString(10,y,f"Date: {date}")
    y -= 8
    c.drawString(10,y,f"Time: {time}")

    y -= 10
    c.drawString(10,y,f"Customer: {customer_entry.get()}")

    y -= 10
    c.drawString(10,y,"--------------------------------")

    y -= 8
    c.drawString(10,y,"Item")
    c.drawString(80,y,"Qty")
    c.drawString(100,y,"Price")
    c.drawString(140,y,"Total")

    y -= 8
    c.drawString(10,y,"--------------------------------")

    total = 0

    for item in items:
        y -= 10
        c.drawString(10,y,item[0][:12])
        c.drawString(80,y,str(item[1]))
        c.drawString(100,y,str(item[2]))
        c.drawString(140,y,str(item[3]))
        total += item[3]

    y -= 12
    c.drawString(10,y,"--------------------------------")

    y -= 10
    c.setFont("Helvetica-Bold",8)
    c.drawString(10,y,f"Total Amount: ₹{total}")

    y -= 15
    c.setFont("Helvetica",7)
    c.drawCentredString(80,y,"Thank you for shopping with us!")

    c.save()

    messagebox.showinfo("Saved", f"Invoice saved as {filename}")

def print_bill():
    save_pdf()
    os.startfile(f"invoice_{invoice_no}.pdf", "print")

root = tk.Tk()
root.title("Mohit Trading Company Billing")

invoice_label = tk.Label(root, text=f"Invoice No: {invoice_no}", font=("Arial",12))
invoice_label.pack()

tk.Label(root,text="Customer Name").pack()
customer_entry = tk.Entry(root)
customer_entry.pack()

tk.Label(root,text="Item Name").pack()
item_entry = tk.Entry(root)
item_entry.pack()

tk.Label(root,text="Quantity").pack()
qty_entry = tk.Entry(root)
qty_entry.pack()

tk.Label(root,text="Price").pack()
price_entry = tk.Entry(root)
price_entry.pack()

tk.Button(root,text="Add Item",command=add_item).pack(pady=5)

table = ttk.Treeview(root, columns=("Item","Qty","Price","Total"), show="headings")
table.heading("Item",text="Item")
table.heading("Qty",text="Qty")
table.heading("Price",text="Price")
table.heading("Total",text="Total")
table.pack()

total_label = tk.Label(root,text="Total: ₹0",font=("Arial",12))
total_label.pack()

tk.Button(root,text="Save PDF",command=save_pdf).pack(pady=5)
tk.Button(root,text="Print Bill",command=print_bill).pack(pady=5)
tk.Button(root,text="New Invoice",command=new_invoice).pack(pady=5)

root.mainloop()