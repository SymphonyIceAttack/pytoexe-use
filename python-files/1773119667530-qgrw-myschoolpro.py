School Management System GUI

import tkinter as tkfrom tkinter import ttk, messageboximport sqlite3from datetime import datetime, timedelta
class SchoolManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Management & Accounts System")
        self.root.geometry("900x600")
        
        # Initialize Database
        self.setup_database()
        
        # UI Styling
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[10, 5])
        
        # Create Tab Control

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill="both")
        
        # Create Tabs
        self.tab_admission = ttk.Frame(self.notebook)
        self.tab_accounts = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_admission, text=" Admissions & Students ")
        self.notebook.add(self.tab_accounts, text=" Fees & Expenses ")
        self.notebook.add(self.tab_reports, text=" Financial Reports ")
        
        self.setup_admission_tab()
        self.setup_accounts_tab()
        self.setup_reports_tab()

    def setup_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect('school_data.db')

        cursor = conn.cursor()
        # Students Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           name TEXT, 
                           class TEXT, 
                           admission_date TEXT,
                           contact TEXT)''')
        # Finance Table (Fees, Income, Spending)
        cursor.execute('''CREATE TABLE IF NOT EXISTS finance 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           type TEXT, 
                           amount REAL, 
                           category TEXT, 
                           date TEXT,
                           description TEXT)''')
        conn.commit()
        conn.close()


    # --- ADMISSION TAB ---
    def setup_admission_tab(self):
        # Input Frame
        frame = ttk.LabelFrame(self.tab_admission, text="New Student Admission")
        frame.pack(pady=20, padx=20, fill="x")
        
        ttk.Label(frame, text="Student Name:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_name = ttk.Entry(frame, width=30)
        self.ent_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Class:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_class = ttk.Entry(frame, width=15)
        self.ent_class.grid(row=0, column=3, padx=5, pady=5)
        
        btn_add = ttk.Button(frame, text="Register Student", command=self.add_student)
        btn_add.grid(row=0, column=4, padx=10, pady=5)
        
        # Student List
        self.tree_students = ttk.Treeview(self.tab_admission, columns=("ID", "Name", "Class", "Date"), show='headings')

        self.tree_students.heading("ID", text="ID")
        self.tree_students.heading("Name", text="Student Name")
        self.tree_students.heading("Class", text="Class")
        self.tree_students.heading("Date", text="Admission Date")
        self.tree_students.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.refresh_student_list()

    def add_student(self):
        name = self.ent_name.get()
        s_class = self.ent_class.get()
        date = datetime.now().strftime("%Y-%m-%d")
        
        if name and s_class:
            conn = sqlite3.connect('school_data.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO students (name, class, admission_date) VALUES (?, ?, ?)", 
                           (name, s_class, date))
            conn.commit()

            conn.close()
            messagebox.showinfo("Success", f"Student {name} registered successfully!")
            self.ent_name.delete(0, tk.END)
            self.ent_class.delete(0, tk.END)
            self.refresh_student_list()
        else:
            messagebox.showwarning("Input Error", "Please fill all fields.")

    def refresh_student_list(self):
        for item in self.tree_students.get_children():
            self.tree_students.delete(item)
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, class, admission_date FROM students")
        for row in cursor.fetchall():
            self.tree_students.insert("", tk.END, values=row)
        conn.close()

    # --- ACCOUNTS TAB ---

    def setup_accounts_tab(self):
        frame = ttk.LabelFrame(self.tab_accounts, text="Record Transaction (Income/Expense)")
        frame.pack(pady=20, padx=20, fill="x")
        
        ttk.Label(frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_amount = ttk.Entry(frame, width=20)
        self.ent_amount.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
        self.combo_cat = ttk.Combobox(frame, values=["Monthly Fee", "Admission Fee", "Salary", "Electricity", "Stationery", "Other"])
        self.combo_cat.grid(row=0, column=3, padx=5, pady=5)
        
        btn_income = tk.Button(frame, text="Add as Income", bg="#4CAF50", fg="white", 
                               command=lambda: self.record_finance("Income"))
        btn_income.grid(row=1, column=1, pady=10)
        
        btn_expense = tk.Button(frame, text="Add as Spending", bg="#f44336", fg="white", 
                                command=lambda: self.record_finance("Expense"))
        btn_expense.grid(row=1, column=3, pady=10)


    def record_finance(self, f_type):
        amount = self.ent_amount.get()
        cat = self.combo_cat.get()
        date = datetime.now().strftime("%Y-%m-%d")
        
        if amount and cat:
            try:
                amount_val = float(amount)
                conn = sqlite3.connect('school_data.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO finance (type, amount, category, date) VALUES (?, ?, ?, ?)", 
                               (f_type, amount_val, cat, date))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"{f_type} of {amount} recorded under {cat}.")
                self.ent_amount.delete(0, tk.END)
            except ValueError:
                messagebox.showerror("Error", "Invalid amount entered.")
        else:

            messagebox.showwarning("Input Error", "Please enter amount and category.")

    # --- REPORTS TAB ---
    def setup_reports_tab(self):
        btn_frame = ttk.Frame(self.tab_reports)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Daily Summary", command=lambda: self.show_report("daily")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Monthly Summary", command=lambda: self.show_report("monthly")).pack(side=tk.LEFT, padx=5)
        
        self.txt_report = tk.Text(self.tab_reports, height=15, width=80, font=("Courier", 10))
        self.txt_report.pack(pady=10, padx=20)

    def show_report(self, period):
        conn = sqlite3.connect('school_data.db')
        cursor = conn.cursor()
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        if period == "monthly":

            date_str = datetime.now().strftime("%Y-%m")
            query = f"SELECT type, SUM(amount) FROM finance WHERE date LIKE '{date_str}%' GROUP BY type"
        else:
            query = f"SELECT type, SUM(amount) FROM finance WHERE date = '{date_str}' GROUP BY type"
            
        cursor.execute(query)
        results = cursor.fetchall()
        
        self.txt_report.delete(1.0, tk.END)
        self.txt_report.insert(tk.END, f"--- {period.upper()} FINANCIAL SUMMARY ({date_str}) ---\n\n")
        
        total_income = 0
        total_expense = 0
        
        for r_type, total in results:
            self.txt_report.insert(tk.END, f"{r_type}: {total}\n")
            if r_type == "Income": total_income = total
            else: total_expense = total
            

        balance = total_income - total_expense
        self.txt_report.insert(tk.END, f"\n---------------------------\n")
        self.txt_report.insert(tk.END, f"NET BALANCE: {balance}\n")
        conn.close()
if __name__ == "__main__":
    root = tk.Tk()
    app = SchoolManagementApp(root)
    root.mainloop()


