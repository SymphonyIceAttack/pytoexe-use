import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_NAME = "skate_passes_weekly.db"

# -----------------------------
# Database Setup
# -----------------------------
def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pass_number TEXT NOT NULL,
            ticket_number TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            initial TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# -----------------------------
# Add Record
# -----------------------------
def add_record():
    name = name_var.get().strip()
    pass_number = pass_var.get().strip()
    ticket_number = ticket_var.get().strip()
    purchase_date = purchase_var.get().strip()
    expiry_date = expiry_var.get().strip()
    initial = initial_var.get().strip()

    if not all([name, pass_number, ticket_number, purchase_date, expiry_date, initial]):
        messagebox.showerror("Missing Data", "Please complete all fields.")
        return

    try:
        datetime.strptime(purchase_date, "%d/%m/%Y")
        datetime.strptime(expiry_date, "%d/%m/%Y")
    except ValueError:
        messagebox.showerror("Date Error", "Dates must be in DD/MM/YYYY format.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO passes (
            name,
            pass_number,
            ticket_number,
            purchase_date,
            expiry_date,
            initial
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        name,
        pass_number,
        ticket_number,
        purchase_date,
        expiry_date,
        initial
    ))

    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Record added successfully.")
    clear_fields()
    load_records()

# -----------------------------
# Search Records
# -----------------------------
def search_records():
    query = search_var.get().strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM passes
        WHERE
            name LIKE ? OR
            pass_number LIKE ? OR
            ticket_number LIKE ? OR
            initial LIKE ?
    ''', (
        f'%{query}%',
        f'%{query}%',
        f'%{query}%',
        f'%{query}%'
    ))

    rows = cursor.fetchall()
    conn.close()

    records_tree.delete(*records_tree.get_children())

    for row in rows:
        records_tree.insert('', tk.END, values=row[1:])

# -----------------------------
# Load All Records
# -----------------------------
def load_records():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM passes ORDER BY id DESC')
    rows = cursor.fetchall()

    conn.close()

    records_tree.delete(*records_tree.get_children())

    for row in rows:
        records_tree.insert('', tk.END, values=row[1:])

# -----------------------------
# Clear Entry Fields
# -----------------------------
def clear_fields():
    name_var.set('')
    pass_var.set('')
    ticket_var.set('')
    purchase_var.set('')
    expiry_var.set('')
    initial_var.set('')

# -----------------------------
# GUI Setup
# -----------------------------
create_database()

root = tk.Tk()
root.title("Skate Passes WEEKLY")
root.geometry("1100x650")
root.configure(bg="#f0f0f0")

# -----------------------------
# Title
# -----------------------------
title_label = tk.Label(
    root,
    text="Skate Passes WEEKLY",
    font=("Arial", 22, "bold"),
    bg="#f0f0f0",
    fg="#003366"
)

title_label.pack(pady=15)

# -----------------------------
# Entry Frame
# -----------------------------
entry_frame = tk.Frame(root, bg="#f0f0f0")
entry_frame.pack(pady=10)

name_var = tk.StringVar()
pass_var = tk.StringVar()
ticket_var = tk.StringVar()
purchase_var = tk.StringVar()
expiry_var = tk.StringVar()
initial_var = tk.StringVar()
search_var = tk.StringVar()

fields = [
    ("Name", name_var),
    ("Pass Number", pass_var),
    ("Ticket Number", ticket_var),
    ("Purchase Date (DD/MM/YYYY)", purchase_var),
    ("Expiry Date (DD/MM/YYYY)", expiry_var),
    ("Initial", initial_var)
]

for index, (label_text, variable) in enumerate(fields):
    row = index // 2
    col = (index % 2) * 2

    label = tk.Label(
        entry_frame,
        text=label_text,
        font=("Arial", 11, "bold"),
        bg="#f0f0f0"
    )
    label.grid(row=row, column=col, padx=10, pady=8, sticky='e')

    entry = tk.Entry(
        entry_frame,
        textvariable=variable,
        width=30,
        font=("Arial", 11)
    )
    entry.grid(row=row, column=col + 1, padx=10, pady=8)

# -----------------------------
# Buttons
# -----------------------------
button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=10)

add_button = tk.Button(
    button_frame,
    text="Add Record",
    font=("Arial", 11, "bold"),
    width=15,
    bg="#4CAF50",
    fg="white",
    command=add_record
)
add_button.grid(row=0, column=0, padx=10)

clear_button = tk.Button(
    button_frame,
    text="Clear Fields",
    font=("Arial", 11, "bold"),
    width=15,
    bg="#f39c12",
    fg="white",
    command=clear_fields
)
clear_button.grid(row=0, column=1, padx=10)

show_button = tk.Button(
    button_frame,
    text="Show All",
    font=("Arial", 11, "bold"),
    width=15,
    bg="#3498db",
    fg="white",
    command=load_records
)
show_button.grid(row=0, column=2, padx=10)

# -----------------------------
# Search Area
# -----------------------------
search_frame = tk.Frame(root, bg="#f0f0f0")
search_frame.pack(pady=10)

search_label = tk.Label(
    search_frame,
    text="Search:",
    font=("Arial", 11, "bold"),
    bg="#f0f0f0"
)
search_label.grid(row=0, column=0, padx=5)

search_entry = tk.Entry(
    search_frame,
    textvariable=search_var,
    width=40,
    font=("Arial", 11)
)
search_entry.grid(row=0, column=1, padx=5)

search_button = tk.Button(
    search_frame,
    text="Search Records",
    font=("Arial", 11, "bold"),
    bg="#8e44ad",
    fg="white",
    command=search_records
)
search_button.grid(row=0, column=2, padx=5)

# -----------------------------
# Records Table
# -----------------------------
columns = (
    "Name",
    "Pass Number",
    "Ticket Number",
    "Purchase Date",
    "Expiry Date",
    "Initial"
)

records_tree = ttk.Treeview(root, columns=columns, show='headings', height=18)

for col in columns:
    records_tree.heading(col, text=col)
    records_tree.column(col, width=160, anchor='center')

scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=records_tree.yview)
records_tree.configure(yscroll=scrollbar.set)

records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=20)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=20)

# -----------------------------
# Initial Load
# -----------------------------
load_records()

# -----------------------------
# Run Application
# -----------------------------
root.mainloop()

'''
TO CREATE AN EXECUTABLE (.EXE) FILE:

1. Install Python from:
https://www.python.org/downloads/

2. Install PyInstaller:
Open Command Prompt and run:

pip install pyinstaller

3. Navigate to the folder containing this file.

4. Build the executable:

pyinstaller --onefile --windowed skate_passes_weekly_database_app.py

5. Your executable will appear inside the "dist" folder.
'''
