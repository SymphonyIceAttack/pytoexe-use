import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import hashlib

# =========================
# DATABASE MANAGER
# =========================
class Database:
    def __init__(self, db_name="sample_management.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            srq_num TEXT,
            customer TEXT,
            sample_purpose TEXT,
            given_by TEXT,
            date TEXT
        )
        """)
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            self.conn.commit()
            return True, "Account Created Successfully!"
        except sqlite3.IntegrityError:
            return False, "Username already exists!"
        except Exception as e:
            return False, str(e)

    def login_user(self, username, password):
        hashed_pw = self.hash_password(password)
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
        return self.cursor.fetchone() is not None

    def execute_query(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        self.conn.commit()

    def fetch_data(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


# =========================
# MAIN APPLICATION
# =========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KSPA - Sample Development System")
        self.geometry("1100x700")
        self.configure(bg="#0f172a")
        self.resizable(False, False)
        
        self.db = Database()
        self.current_user = None
        
        self.setup_styles()
        self.show_login_screen()

        # Handle window close securely
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background="#1e293b", foreground="white", 
                        fieldbackground="#1e293b", rowheight=30, font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", "#2563eb")])
        style.configure("Treeview.Heading", background="#2563eb", foreground="white", font=("Segoe UI", 11, "bold"))

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def on_closing(self):
        self.db.close()
        self.destroy()

    # -------------------------
    # LOGIN SCREEN
    # -------------------------
    def show_login_screen(self):
        self.clear_window()
        
        frame = tk.Frame(self, bg="#1e293b", bd=0, relief="flat")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=450)

        tk.Label(frame, text="WELCOME BACK", font=("Segoe UI", 24, "bold"), fg="white", bg="#1e293b").pack(pady=(40, 30))

        tk.Label(frame, text="Username", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40)
        username_entry = tk.Entry(frame, font=("Segoe UI", 12), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
        username_entry.pack(fill="x", padx=40, pady=(5, 20), ipady=8)

        tk.Label(frame, text="Password", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40)
        password_entry = tk.Entry(frame, show="*", font=("Segoe UI", 12), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
        password_entry.pack(fill="x", padx=40, pady=(5, 30), ipady=8)

        def attempt_login(event=None):
            user = username_entry.get().strip()
            pw = password_entry.get().strip()
            if self.db.login_user(user, pw):
                self.current_user = user
                self.show_dashboard()
            else:
                messagebox.showerror("Error", "Invalid Username or Password")

        self.bind('<Return>', attempt_login)

        tk.Button(frame, text="LOGIN", bg="#2563eb", fg="white", font=("Segoe UI", 12, "bold"), relief="flat", 
                  activebackground="#1d4ed8", activeforeground="white", command=attempt_login).pack(fill="x", padx=40, ipady=8)

        tk.Button(frame, text="Create new account", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "underline"), 
                  relief="flat", activebackground="#1e293b", activeforeground="white", bd=0, 
                  command=self.show_register_screen).pack(pady=20)

    # -------------------------
    # REGISTER SCREEN
    # -------------------------
    def show_register_screen(self):
        self.clear_window()
        
        frame = tk.Frame(self, bg="#1e293b", bd=0)
        frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=450)

        tk.Label(frame, text="CREATE ACCOUNT", font=("Segoe UI", 24, "bold"), fg="white", bg="#1e293b").pack(pady=(40, 30))

        tk.Label(frame, text="Username", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40)
        username_entry = tk.Entry(frame, font=("Segoe UI", 12), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
        username_entry.pack(fill="x", padx=40, pady=(5, 20), ipady=8)

        tk.Label(frame, text="Password", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=40)
        password_entry = tk.Entry(frame, show="*", font=("Segoe UI", 12), bg="#0f172a", fg="white", insertbackground="white", relief="flat")
        password_entry.pack(fill="x", padx=40, pady=(5, 30), ipady=8)

        def attempt_register():
            user = username_entry.get().strip()
            pw = password_entry.get().strip()
            if not user or not pw:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            success, msg = self.db.register_user(user, pw)
            if success:
                messagebox.showinfo("Success", msg)
                self.show_login_screen()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(frame, text="REGISTER", bg="#10b981", fg="white", font=("Segoe UI", 12, "bold"), relief="flat", 
                  activebackground="#059669", activeforeground="white", command=attempt_register).pack(fill="x", padx=40, ipady=8)

        tk.Button(frame, text="Back to Login", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10, "underline"), 
                  relief="flat", activebackground="#1e293b", activeforeground="white", bd=0, 
                  command=self.show_login_screen).pack(pady=20)

    # -------------------------
    # DASHBOARD SCREEN
    # -------------------------
    def show_dashboard(self):
        self.clear_window()
        self.unbind('<Return>') # Remove login keybind
        self.selected_id = None

        # Top Bar
        topbar = tk.Frame(self, bg="#1e3a8a", height=60)
        topbar.pack(fill="x")
        
        tk.Label(topbar, text="KSPA Dashboard", bg="#1e3a8a", fg="white", font=("Segoe UI", 20, "bold")).pack(side="left", padx=20, pady=10)
        tk.Button(topbar, text="Logout", bg="#ef4444", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", 
                  command=self.show_login_screen, padx=15).pack(side="right", padx=20, pady=15)
        tk.Label(topbar, text=f"User: {self.current_user}", bg="#1e3a8a", fg="#93c5fd", font=("Segoe UI", 12, "bold")).pack(side="right", padx=20, pady=15)

        # Content Frame
        content_frame = tk.Frame(self, bg="#0f172a")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Form Section
        form_frame = tk.Frame(content_frame, bg="#1e293b")
        form_frame.pack(fill="x", pady=(0, 20), ipady=10)

        entries = {}
        fields = [("SRQ Number", 0, 0), ("Customer", 0, 2), ("Sample Purpose", 1, 0), ("Who Gave It", 1, 2), ("Date", 2, 0)]
        
        for name, row, col in fields:
            tk.Label(form_frame, text=name, bg="#1e293b", fg="white", font=("Segoe UI", 10, "bold")).grid(row=row, column=col, padx=20, pady=10, sticky="w")
            ent = tk.Entry(form_frame, font=("Segoe UI", 11), bg="#0f172a", fg="white", insertbackground="white", relief="flat", width=30)
            ent.grid(row=row, column=col+1, padx=20, pady=10, ipady=5)
            entries[name] = ent
            
        entries["Date"].insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Search Bar
        search_frame = tk.Frame(form_frame, bg="#1e293b")
        search_frame.grid(row=2, column=2, columnspan=2, sticky="e", padx=20)
        tk.Label(search_frame, text="Search SRQ:", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        search_entry = tk.Entry(search_frame, font=("Segoe UI", 11), bg="#0f172a", fg="white", insertbackground="white", relief="flat", width=20)
        search_entry.pack(side="left", padx=5, ipady=5)
        
        # Action Buttons
        btn_frame = tk.Frame(content_frame, bg="#0f172a")
        btn_frame.pack(fill="x", pady=(0, 10))

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "relief": "flat", "width": 12, "height": 1}
        
        tk.Button(btn_frame, text="Add New", bg="#10b981", command=lambda: self.save_data(entries), **btn_style).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Update", bg="#3b82f6", command=lambda: self.update_data(entries), **btn_style).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete", bg="#ef4444", command=self.delete_data, **btn_style).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Clear Fields", bg="#64748b", command=lambda: self.clear_fields(entries), **btn_style).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="Search", bg="#8b5cf6", command=lambda: self.load_data(search_entry.get()), **btn_style).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Refresh All", bg="#0ea5e9", command=lambda: self.load_data(), **btn_style).pack(side="right", padx=5)

        # Table Section
        table_frame = tk.Frame(content_frame)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "srq", "customer", "purpose", "giver", "date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        headings = {"id": ("ID", 50), "srq": ("SRQ Number", 150), "customer": ("Customer", 180), 
                    "purpose": ("Sample Purpose", 250), "giver": ("Who Gave It", 150), "date": ("Date", 120)}
        
        for col, (text, width) in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<ButtonRelease-1>", lambda e: self.select_record(entries))
        self.load_data()

    # -------------------------
    # CRUD OPERATIONS
    # -------------------------
    def clear_fields(self, entries):
        for ent in entries.values():
            ent.delete(0, tk.END)
        entries["Date"].insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.selected_id = None

    def load_data(self, search_term=""):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        if search_term:
            query = "SELECT * FROM samples WHERE srq_num LIKE ? ORDER BY id DESC"
            rows = self.db.fetch_data(query, ('%' + search_term + '%',))
        else:
            rows = self.db.fetch_data("SELECT * FROM samples ORDER BY id DESC")
            
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def save_data(self, entries):
        data = [entries[k].get().strip() for k in ["SRQ Number", "Customer", "Sample Purpose", "Who Gave It", "Date"]]
        
        if not data[0] or not data[1]:
            messagebox.showerror("Error", "SRQ Number and Customer are required!")
            return
            
        self.db.execute_query("INSERT INTO samples (srq_num, customer, sample_purpose, given_by, date) VALUES (?, ?, ?, ?, ?)", tuple(data))
        messagebox.showinfo("Success", "Data Saved Successfully!")
        self.clear_fields(entries)
        self.load_data()

    def select_record(self, entries):
        selected = self.tree.focus()
        if not selected:
            return
            
        values = self.tree.item(selected, "values")
        self.selected_id = values[0]
        
        self.clear_fields(entries)
        for i, key in enumerate(["SRQ Number", "Customer", "Sample Purpose", "Who Gave It", "Date"], start=1):
            entries[key].insert(0, values[i])

    def update_data(self, entries):
        if not self.selected_id:
            messagebox.showwarning("Warning", "Please select a record from the table first!")
            return
            
        data = [entries[k].get().strip() for k in ["SRQ Number", "Customer", "Sample Purpose", "Who Gave It", "Date"]]
        data.append(self.selected_id)
        
        self.db.execute_query("UPDATE samples SET srq_num=?, customer=?, sample_purpose=?, given_by=?, date=? WHERE id=?", tuple(data))
        messagebox.showinfo("Success", "Record Updated Successfully!")
        self.clear_fields(entries)
        self.load_data()

    def delete_data(self):
        if not self.selected_id:
            messagebox.showwarning("Warning", "Please select a record from the table first!")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
            self.db.execute_query("DELETE FROM samples WHERE id=?", (self.selected_id,))
            messagebox.showinfo("Deleted", "Record Deleted Successfully!")
            self.load_data()
            self.selected_id = None

# =========================
# RUN APPLICATION
# =========================
if __name__ == "__main__":
    app = App()
    app.mainloop()