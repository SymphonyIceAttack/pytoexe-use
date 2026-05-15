import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import hashlib

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("sample_management.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    srq_num TEXT,
    customer TEXT,
    sample_purpose TEXT,
    given_by TEXT,
    date TEXT
)
""")

conn.commit()

# =========================
# MAIN WINDOW
# =========================
root = tk.Tk()
root.title("Advanced Sample Management System")
root.geometry("1250x720")
root.configure(bg="#0f172a")
root.resizable(False, False)

# =========================
# STYLE
# =========================
style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background="#1e293b",
    foreground="white",
    fieldbackground="#1e293b",
    rowheight=30,
    font=("Segoe UI", 10)
)

style.configure(
    "Treeview.Heading",
    background="#2563eb",
    foreground="white",
    font=("Segoe UI", 11, "bold")
)

# =========================
# FUNCTIONS
# =========================
def clear_frame():
    for widget in root.winfo_children():
        widget.destroy()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# REGISTER WINDOW
# =========================
def register_window():
    clear_frame()

    frame = tk.Frame(root, bg="#111827")
    frame.place(relx=0.5, rely=0.5, anchor="center", width=420, height=450)

    title = tk.Label(
        frame,
        text="Create Account",
        font=("Segoe UI", 26, "bold"),
        fg="white",
        bg="#111827"
    )
    title.pack(pady=25)

    tk.Label(
        frame,
        text="Username",
        bg="#111827",
        fg="white",
        font=("Segoe UI", 11)
    ).pack()

    username_entry = tk.Entry(frame, font=("Segoe UI", 12), width=30)
    username_entry.pack(pady=10)

    tk.Label(
        frame,
        text="Password",
        bg="#111827",
        fg="white",
        font=("Segoe UI", 11)
    ).pack()

    password_entry = tk.Entry(
        frame,
        show="*",
        font=("Segoe UI", 12),
        width=30
    )
    password_entry.pack(pady=10)

    def register_user():

        username = username_entry.get()
        password = password_entry.get()

        if username == "" or password == "":
            messagebox.showerror(
                "Error",
                "Please fill all fields"
            )
            return

        hashed_password = hash_password(password)

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            conn.commit()

            messagebox.showinfo(
                "Success",
                "Account Created Successfully"
            )

            login_window()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Error",
                "Username already exists"
            )

    tk.Button(
        frame,
        text="Create Account",
        bg="#2563eb",
        fg="white",
        font=("Segoe UI", 12, "bold"),
        width=22,
        height=2,
        command=register_user
    ).pack(pady=25)

    tk.Button(
        frame,
        text="Back To Login",
        bg="#374151",
        fg="white",
        font=("Segoe UI", 11),
        width=22,
        height=2,
        command=login_window
    ).pack()

# =========================
# DASHBOARD
# =========================
def dashboard(username):

    clear_frame()

    selected_id = {"id": None}

    # =========================
    # TOPBAR
    # =========================
    topbar = tk.Frame(root, bg="#1e3a8a", height=70)
    topbar.pack(fill="x")

    title = tk.Label(
        topbar,
        text="Sample Management Dashboard",
        bg="#1e3a8a",
        fg="white",
        font=("Segoe UI", 24, "bold")
    )
    title.pack(side="left", padx=20)

    user_label = tk.Label(
        topbar,
        text=f"Welcome : {username}",
        bg="#1e3a8a",
        fg="white",
        font=("Segoe UI", 11)
    )
    user_label.pack(side="right", padx=20)

    # =========================
    # FORM
    # =========================
    form_frame = tk.Frame(root, bg="#0f172a")
    form_frame.pack(pady=20)

    # SRQ
    tk.Label(
        form_frame,
        text="SRQ Number",
        bg="#0f172a",
        fg="white",
        font=("Segoe UI", 11)
    ).grid(row=0, column=0, padx=10, pady=10)

    srq_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=35)
    srq_entry.grid(row=0, column=1)

    # CUSTOMER
    tk.Label(
        form_frame,
        text="Customer",
        bg="#0f172a",
        fg="white",
        font=("Segoe UI", 11)
    ).grid(row=1, column=0, padx=10, pady=10)

    customer_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=35)
    customer_entry.grid(row=1, column=1)

    # PURPOSE
    tk.Label(
        form_frame,
        text="Sample Purpose",
        bg="#0f172a",
        fg="white",
        font=("Segoe UI", 11)
    ).grid(row=2, column=0, padx=10, pady=10)

    purpose_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=35)
    purpose_entry.grid(row=2, column=1)

    # GIVER
    tk.Label(
        form_frame,
        text="Who Gave It",
        bg="#0f172a",
        fg="white",
        font=("Segoe UI", 11)
    ).grid(row=3, column=0, padx=10, pady=10)

    giver_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=35)
    giver_entry.grid(row=3, column=1)

    # DATE
    tk.Label(
        form_frame,
        text="Date",
        bg="#0f172a",
        fg="white",
        font=("Segoe UI", 11)
    ).grid(row=4, column=0, padx=10, pady=10)

    date_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=35)
    date_entry.grid(row=4, column=1)

    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    # SEARCH
    tk.Label(
        form_frame,
        text="Search SRQ",
        bg="#0f172a",
        fg="#93c5fd",
        font=("Segoe UI", 11, "bold")
    ).grid(row=0, column=2, padx=15)

    search_entry = tk.Entry(form_frame, font=("Segoe UI", 11), width=30)
    search_entry.grid(row=0, column=3)

    # =========================
    # TABLE
    # =========================
    table_frame = tk.Frame(root)
    table_frame.pack(pady=20)

    columns = (
        "id",
        "srq",
        "customer",
        "purpose",
        "giver",
        "date"
    )

    tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=14
    )

    tree.heading("id", text="ID")
    tree.heading("srq", text="SRQ Number")
    tree.heading("customer", text="Customer")
    tree.heading("purpose", text="Sample Purpose")
    tree.heading("giver", text="Who Gave It")
    tree.heading("date", text="Date")

    tree.column("id", width=60)
    tree.column("srq", width=150)
    tree.column("customer", width=180)
    tree.column("purpose", width=250)
    tree.column("giver", width=180)
    tree.column("date", width=120)

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview
    )

    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left")
    scrollbar.pack(side="right", fill="y")

    # =========================
    # FUNCTIONS
    # =========================
    def clear_fields():

        srq_entry.delete(0, tk.END)
        customer_entry.delete(0, tk.END)
        purpose_entry.delete(0, tk.END)
        giver_entry.delete(0, tk.END)

        date_entry.delete(0, tk.END)
        date_entry.insert(
            0,
            datetime.now().strftime("%Y-%m-%d")
        )

    def load_data():

        for row in tree.get_children():
            tree.delete(row)

        cursor.execute("""
        SELECT id, srq_num, customer,
        sample_purpose, given_by, date
        FROM samples
        ORDER BY id DESC
        """)

        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

    def save_data():

        srq = srq_entry.get()
        customer = customer_entry.get()
        purpose = purpose_entry.get()
        giver = giver_entry.get()
        date = date_entry.get()

        if srq == "" or customer == "":
            messagebox.showerror(
                "Error",
                "Please fill required fields"
            )
            return

        cursor.execute("""
        INSERT INTO samples (
            srq_num,
            customer,
            sample_purpose,
            given_by,
            date
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            srq,
            customer,
            purpose,
            giver,
            date
        ))

        conn.commit()

        messagebox.showinfo(
            "Success",
            "Data Saved Successfully"
        )

        clear_fields()
        load_data()

    def search_data():

        search = search_entry.get()

        for row in tree.get_children():
            tree.delete(row)

        cursor.execute("""
        SELECT id, srq_num, customer,
        sample_purpose, given_by, date
        FROM samples
        WHERE srq_num LIKE ?
        """, ('%' + search + '%',))

        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

    def select_record(event):

        selected = tree.focus()

        if not selected:
            return

        values = tree.item(selected, "values")

        selected_id["id"] = values[0]

        clear_fields()

        srq_entry.insert(0, values[1])
        customer_entry.insert(0, values[2])
        purpose_entry.insert(0, values[3])
        giver_entry.insert(0, values[4])
        date_entry.insert(0, values[5])

    def update_data():

        if selected_id["id"] is None:
            messagebox.showerror(
                "Error",
                "Select a record first"
            )
            return

        cursor.execute("""
        UPDATE samples
        SET
            srq_num=?,
            customer=?,
            sample_purpose=?,
            given_by=?,
            date=?
        WHERE id=?
        """, (
            srq_entry.get(),
            customer_entry.get(),
            purpose_entry.get(),
            giver_entry.get(),
            date_entry.get(),
            selected_id["id"]
        ))

        conn.commit()

        messagebox.showinfo(
            "Success",
            "Record Updated Successfully"
        )

        clear_fields()
        load_data()

    def delete_data():

        if selected_id["id"] is None:
            messagebox.showerror(
                "Error",
                "Select a record first"
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete?"
        )

        if confirm:

            cursor.execute(
                "DELETE FROM samples WHERE id=?",
                (selected_id["id"],)
            )

            conn.commit()

            messagebox.showinfo(
                "Deleted",
                "Record Deleted Successfully"
            )

            clear_fields()
            load_data()

    # =========================
    # BUTTONS
    # =========================
    button_frame = tk.Frame(root, bg="#0f172a")
    button_frame.pack(pady=10)

    tk.Button(
        button_frame,
        text="Save Data",
        bg="#16a34a",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=15,
        height=2,
        command=save_data
    ).grid(row=0, column=0, padx=8)

    tk.Button(
        button_frame,
        text="Update",
        bg="#2563eb",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=15,
        height=2,
        command=update_data
    ).grid(row=0, column=1, padx=8)

    tk.Button(
        button_frame,
        text="Delete",
        bg="#dc2626",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=15,
        height=2,
        command=delete_data
    ).grid(row=0, column=2, padx=8)

    tk.Button(
        button_frame,
        text="Search",
        bg="#7c3aed",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=15,
        height=2,
        command=search_data
    ).grid(row=0, column=3, padx=8)

    tk.Button(
        button_frame,
        text="Refresh",
        bg="#0891b2",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=15,
        height=2,
        command=load_data
    ).grid(row=0, column=4, padx=8)

    tk.Button(
        button_frame,
        text="Logout",
        bg="#ea580c",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=15,
        height=2,
        command=login_window
    ).grid(row=0, column=5, padx=8)

    tree.bind("<ButtonRelease-1>", select_record)

    load_data()

# =========================
# LOGIN WINDOW
# =========================
def login_window():

    clear_frame()

    frame = tk.Frame(root, bg="#111827")
    frame.place(
        relx=0.5,
        rely=0.5,
        anchor="center",
        width=420,
        height=480
    )

    title = tk.Label(
        frame,
        text="LOGIN",
        font=("Segoe UI", 30, "bold"),
        fg="white",
        bg="#111827"
    )

    title.pack(pady=35)

    tk.Label(
        frame,
        text="Username",
        bg="#111827",
        fg="white",
        font=("Segoe UI", 11)
    ).pack()

    username_entry = tk.Entry(
        frame,
        font=("Segoe UI", 12),
        width=30
    )

    username_entry.pack(pady=10)

    tk.Label(
        frame,
        text="Password",
        bg="#111827",
        fg="white",
        font=("Segoe UI", 11)
    ).pack()

    password_entry = tk.Entry(
        frame,
        show="*",
        font=("Segoe UI", 12),
        width=30
    )

    password_entry.pack(pady=10)

    def login_user():

        username = username_entry.get()
        password = hash_password(password_entry.get())

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        if user:
            dashboard(username)

        else:
            messagebox.showerror(
                "Error",
                "Invalid Username or Password"
            )

    tk.Button(
        frame,
        text="Login",
        bg="#2563eb",
        fg="white",
        font=("Segoe UI", 12, "bold"),
        width=22,
        height=2,
        command=login_user
    ).pack(pady=25)

    tk.Label(
        frame,
        text="Don't have an account?",
        bg="#111827",
        fg="white",
        font=("Segoe UI", 10)
    ).pack(pady=10)

    tk.Button(
        frame,
        text="Create New Account",
        bg="#16a34a",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        width=24,
        height=2,
        command=register_window
    ).pack()

# =========================
# START
# =========================
login_window()
root.mainloop()