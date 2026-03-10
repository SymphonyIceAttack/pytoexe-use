import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import pandas as pd

DB = "customers.db"

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        customer TEXT,
        invoice TEXT,
        location TEXT,
        phone TEXT,
        diffuser TEXT,
        oil TEXT,
        note TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_record(data):
    conn = sqlite3.connect(DB)
    conn.execute("""
    INSERT INTO records(date,customer,invoice,location,phone,diffuser,oil,note)
    VALUES(?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()

def get_records(search=""):
    conn = sqlite3.connect(DB)
    if search:
        rows = conn.execute("""
        SELECT * FROM records
        WHERE customer LIKE ? OR location LIKE ? OR oil LIKE ?
        """,(f"%{search}%",f"%{search}%",f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM records ORDER BY id DESC").fetchall()
    conn.close()
    return rows

# ---------------- EXCEL IMPORT ---------------- #

def import_excel():
    file = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx")])
    if not file:
        return

    df = pd.read_excel(file)

    conn = sqlite3.connect(DB)

    for _,r in df.iterrows():
        conn.execute("""
        INSERT INTO records(date,customer,invoice,location,phone,diffuser,oil,note)
        VALUES(?,?,?,?,?,?,?,?)
        """,(
            str(r.get("Date","")),
            str(r.get("Custumer Name","")),
            str(r.get("Invoice NO","")),
            str(r.get("Location","")),
            str(r.get("Phone Num","")),
            str(r.get("Diffuser","")),
            str(r.get("Oil Scent","")),
            str(r.get("NOTE",""))
        ))

    conn.commit()
    conn.close()

    load_table()
    messagebox.showinfo("Import","Excel imported successfully")

# ---------------- GUI ---------------- #

root = tk.Tk()
root.title("Customer Manager")
root.geometry("1000x600")

init_db()

# Dashboard
top = tk.Frame(root)
top.pack(fill="x")

tk.Label(top,text="Customer Manager Dashboard",font=("Segoe UI",16)).pack(side="left",padx=10,pady=10)

tk.Button(top,text="Import Excel",command=import_excel).pack(side="right",padx=10)

# Search
search_var = tk.StringVar()

def search_records():
    load_table(search_var.get())

search_frame = tk.Frame(root)
search_frame.pack(fill="x")

tk.Label(search_frame,text="Search").pack(side="left",padx=5)
tk.Entry(search_frame,textvariable=search_var).pack(side="left",padx=5)
tk.Button(search_frame,text="Search",command=search_records).pack(side="left")

# Table
cols = ("ID","Date","Customer","Invoice","Location","Phone","Diffuser","Oil","Note")

tree = ttk.Treeview(root,columns=cols,show="headings")
for c in cols:
    tree.heading(c,text=c)
    tree.column(c,width=110)

tree.pack(fill="both",expand=True,pady=10)

# Load table
def load_table(search=""):
    for r in tree.get_children():
        tree.delete(r)

    rows = get_records(search)

    for r in rows:
        tree.insert("",tk.END,values=r)

# Add record form
form = tk.Frame(root)
form.pack(fill="x")

entries = {}

fields = ["Date","Customer","Invoice","Location","Phone","Diffuser","Oil","Note"]

for i,f in enumerate(fields):
    tk.Label(form,text=f).grid(row=0,column=i)
    e = tk.Entry(form,width=12)
    e.grid(row=1,column=i)
    entries[f] = e

def save_record():
    data = (
        entries["Date"].get(),
        entries["Customer"].get(),
        entries["Invoice"].get(),
        entries["Location"].get(),
        entries["Phone"].get(),
        entries["Diffuser"].get(),
        entries["Oil"].get(),
        entries["Note"].get()
    )

    add_record(data)
    load_table()

    for e in entries.values():
        e.delete(0,"end")

tk.Button(form,text="Add Record",command=save_record).grid(row=1,column=8,padx=10)

load_table()

root.mainloop()