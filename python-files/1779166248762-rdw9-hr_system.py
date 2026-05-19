import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
from datetime import datetime

PASSWORD = "mjk123679"

DATA_FILE = "employees.xlsx"
ATTACHMENTS_DIR = "attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

employees = []


def load_data():
    global employees
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_excel(DATA_FILE)
            employees = df.to_dict(orient="records")
        except:
            employees = []
    else:
        employees = []


def save_to_excel():
    df = pd.DataFrame(employees)
    df.to_excel(DATA_FILE, index=False)


def login():
    if password_entry.get() == PASSWORD:
        login_window.destroy()
        open_dashboard()
    else:
        messagebox.showerror("Error", "Wrong password")


def add_employee():
    name = name_entry.get().strip()
    job = job_entry.get().strip()

    if not name or not job:
        messagebox.showwarning("Warning", "Please fill all fields")
        return

    record = {
        "Name": name,
        "Job": job,
        "Photo": photo_path.get(),
        "Document": doc_path.get(),
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    employees.append(record)
    save_to_excel()
    refresh_table()

    name_entry.delete(0, tk.END)
    job_entry.delete(0, tk.END)
    photo_path.set("")
    doc_path.set("")


def choose_photo():
    file = filedialog.askopenfilename()
    if file:
        photo_path.set(file)


def choose_doc():
    file = filedialog.askopenfilename()
    if file:
        doc_path.set(file)


def refresh_table():
    for row in table.get_children():
        table.delete(row)

    for emp in employees:
        table.insert("", tk.END, values=(
            emp.get("Name", ""),
            emp.get("Job", ""),
            emp.get("Date", "")
        ))


def open_dashboard():
    global name_entry, job_entry, photo_path, doc_path, table

    app = tk.Tk()
    app.title("HR Employee System")
    app.geometry("800x500")

    tk.Label(app, text="Employee Name").pack()
    name_entry = tk.Entry(app, width=40)
    name_entry.pack()

    tk.Label(app, text="Job").pack()
    job_entry = tk.Entry(app, width=40)
    job_entry.pack()

    photo_path = tk.StringVar()
    doc_path = tk.StringVar()

    tk.Button(app, text="Select Photo", command=choose_photo).pack(pady=2)
    tk.Label(app, textvariable=photo_path).pack()

    tk.Button(app, text="Select Document", command=choose_doc).pack(pady=2)
    tk.Label(app, textvariable=doc_path).pack()

    tk.Button(app, text="Add Employee", command=add_employee, bg="green", fg="white").pack(pady=10)

    columns = ("Name", "Job", "Date")
    table = ttk.Treeview(app, columns=columns, show="headings")

    for col in columns:
        table.heading(col, text=col)
        table.column(col, width=200)

    table.pack(fill="both", expand=True)

    refresh_table()

    app.mainloop()


load_data()

login_window = tk.Tk()
login_window.title("HR Login")
login_window.geometry("300x200")

tk.Label(login_window, text="Enter Password").pack(pady=10)

password_entry = tk.Entry(login_window, show="*")
password_entry.pack()

tk.Button(login_window, text="Login", command=login, bg="blue", fg="white").pack(pady=10)

login_window.mainloop()
