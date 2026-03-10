import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

DB_NAME = "myschool.db"


# ---------------- DATABASE ---------------- #

def init_db():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    username TEXT,
    password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS schools(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    contact TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER,
    name TEXT,
    class TEXT,
    parent TEXT,
    contact TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS fees(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    amount REAL,
    date TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT
    )
    """)

    c.execute("SELECT * FROM users")

    if not c.fetchone():
        c.execute("INSERT INTO users VALUES('admin','admin123')")

    conn.commit()
    conn.close()


# ---------------- MAIN APP ---------------- #

class MySchoolApp:

    def __init__(self, root):

        self.root = root
        self.root.title("MY SCHOOL - Management Software")
        self.root.geometry("1100x700")

        self.login_screen()

    # ---------------- LOGIN ---------------- #

    def login_screen(self):

        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=200)

        tk.Label(
            self.login_frame,
            text="MY SCHOOL SOFTWARE",
            font=("Arial", 20)
        ).pack(pady=10)

        self.username = ttk.Entry(self.login_frame)
        self.username.pack(pady=5)

        self.password = ttk.Entry(self.login_frame, show="*")
        self.password.pack(pady=5)

        tk.Button(
            self.login_frame,
            text="Login",
            command=self.check_login
        ).pack(pady=10)

    def check_login(self):

        u = self.username.get()
        p = self.password.get()

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (u, p)
        )

        if c.fetchone():

            self.login_frame.destroy()
            self.dashboard()

        else:
            messagebox.showerror("Error", "Invalid Login")

        conn.close()

    # ---------------- DASHBOARD ---------------- #

    def dashboard(self):

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True)

        self.tab_home = ttk.Frame(self.nb)
        self.tab_schools = ttk.Frame(self.nb)
        self.tab_students = ttk.Frame(self.nb)
        self.tab_fees = ttk.Frame(self.nb)

        self.nb.add(self.tab_home, text="Dashboard")
        self.nb.add(self.tab_schools, text="Schools")
        self.nb.add(self.tab_students, text="Students")
        self.nb.add(self.tab_fees, text="Fees")

        self.dashboard_tab()
        self.schools_tab()
        self.students_tab()
        self.fees_tab()

    # ---------------- DASHBOARD ---------------- #

    def dashboard_tab(self):

        tk.Label(
            self.tab_home,
            text="System Dashboard",
            font=("Arial", 20)
        ).pack(pady=20)

        self.lbl_students = tk.Label(self.tab_home, font=("Arial", 16))
        self.lbl_students.pack()

        self.lbl_fees = tk.Label(self.tab_home, font=("Arial", 16))
        self.lbl_fees.pack()

        self.refresh_dashboard()

    def refresh_dashboard(self):

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM students")
        students = c.fetchone()[0]

        c.execute("SELECT SUM(amount) FROM fees")
        fees = c.fetchone()[0]

        if fees is None:
            fees = 0

        self.lbl_students.config(text=f"Total Students: {students}")
        self.lbl_fees.config(text=f"Total Fee Collected: PKR {fees}")

        conn.close()

    # ---------------- SCHOOLS ---------------- #

    def schools_tab(self):

        frame = tk.Frame(self.tab_schools)
        frame.pack(pady=20)

        tk.Label(frame, text="School Name").grid(row=0, column=0)
        tk.Label(frame, text="Address").grid(row=0, column=1)
        tk.Label(frame, text="Contact").grid(row=0, column=2)

        self.sc_name = ttk.Entry(frame)
        self.sc_addr = ttk.Entry(frame)
        self.sc_contact = ttk.Entry(frame)

        self.sc_name.grid(row=1, column=0)
        self.sc_addr.grid(row=1, column=1)
        self.sc_contact.grid(row=1, column=2)

        tk.Button(
            frame,
            text="Add School",
            command=self.add_school
        ).grid(row=1, column=3)

        self.school_tree = ttk.Treeview(
            self.tab_schools,
            columns=("id", "name", "contact"),
            show="headings"
        )

        for col in ("id", "name", "contact"):
            self.school_tree.heading(col, text=col)

        self.school_tree.pack(fill="both", expand=True)

        self.load_schools()

    def add_school(self):

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "INSERT INTO schools(name,address,contact) VALUES(?,?,?)",
            (
                self.sc_name.get(),
                self.sc_addr.get(),
                self.sc_contact.get()
            )
        )

        conn.commit()
        conn.close()

        self.load_schools()

    def load_schools(self):

        for i in self.school_tree.get_children():
            self.school_tree.delete(i)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("SELECT id,name,contact FROM schools")

        for row in c.fetchall():
            self.school_tree.insert("", tk.END, values=row)

        conn.close()

    # ---------------- STUDENTS ---------------- #

    def students_tab(self):

        tk.Label(self.tab_students, text="Add Students from School Section").pack(pady=20)

    # ---------------- FEES ---------------- #

    def fees_tab(self):

        tk.Label(self.tab_fees, text="Fees System Coming Next Update").pack(pady=20)


# ---------------- RUN ---------------- #

init_db()

root = tk.Tk()
app = MySchoolApp(root)
root.mainloop()