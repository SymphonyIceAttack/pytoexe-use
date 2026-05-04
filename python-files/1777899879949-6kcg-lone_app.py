import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import pandas as pd

class LoanDatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Loan Application Management System")
        self.root.geometry("1400x700")
        
        # Create database connection
        self.conn = sqlite3.connect('loan_applications.db')
        self.cursor = self.conn.cursor()
        
        # Create table
        self.create_table()
        
        # Setup UI
        self.setup_ui()
        
        # Load initial data
        self.load_data()
        
    def create_table(self):
        """Create the loan applications table if it doesn't exist"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_code TEXT,
                branch_name TEXT,
                district TEXT,
                region_code TEXT,
                region_name TEXT,
                applicant_name TEXT,
                gender TEXT,
                mobile TEXT,
                email TEXT,
                address TEXT,
                category TEXT,
                occupation TEXT,
                annual_income TEXT,
                loan_type TEXT,
                loan_amount TEXT,
                dob TEXT,
                application_date TEXT,
                application_time TEXT,
                is_active TEXT,
                account_number TEXT,
                bank_name TEXT,
                pan_number TEXT,
                days_overdue TEXT,
                remarks TEXT
            )
        ''')
        self.conn.commit()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search Records", padding="10")
        search_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_records())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(search_frame, text="Search by:").grid(row=0, column=2, padx=5)
        self.search_by = ttk.Combobox(search_frame, values=['Name', 'Mobile', 'Email', 'PAN', 'Application ID'], width=15)
        self.search_by.grid(row=0, column=3, padx=5)
        self.search_by.set('Name')
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="Add New Record", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Selected", command=self.edit_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Bulk Import", command=self.bulk_import).pack(side=tk.LEFT, padx=5)
        
        # Treeview frame
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        self.tree = ttk.Treeview(tree_frame, columns=tuple(range(20)), show="headings", 
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Define columns
        columns = ['ID', 'Branch Code', 'Branch Name', 'District', 'Region Code', 'Region Name',
                  'Applicant Name', 'Gender', 'Mobile', 'Email', 'Address', 'Category', 
                  'Occupation', 'Annual Income', 'Loan Type', 'Loan Amount', 'DOB', 
                  'Application Date', 'Status', 'Remarks']
        
        for idx, col in enumerate(columns):
            self.tree.heading(idx, text=col)
            self.tree.column(idx, width=120, minwidth=80)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def load_data(self):
        """Load data from database into treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Fetch data
        self.cursor.execute("SELECT * FROM loan_applications ORDER BY id DESC")
        rows = self.cursor.fetchall()
        
        # Insert data
        for row in rows:
            self.tree.insert('', tk.END, values=(
                row[0], row[1], row[2], row[3], row[4], row[5],
                row[6], row[7], row[8], row[9], row[10], row[11],
                row[12], row[13], row[14], row[15], row[16], row[17],
                row[19], row[23]
            ))
        
        self.status_var.set(f"Loaded {len(rows)} records")
        
    def search_records(self):
        """Search records based on search criteria"""
        search_term = self.search_var.get().strip()
        if not search_term:
            self.load_data()
            return
        
        search_by = self.search_by.get()
        column_map = {
            'Name': 'applicant_name',
            'Mobile': 'mobile',
            'Email': 'email',
            'PAN': 'pan_number',
            'Application ID': 'id'
        }
        
        column = column_map.get(search_by, 'applicant_name')
        
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Search query
        query = f"SELECT * FROM loan_applications WHERE {column} LIKE ? ORDER BY id DESC"
        self.cursor.execute(query, (f'%{search_term}%',))
        rows = self.cursor.fetchall()
        
        # Insert results
        for row in rows:
            self.tree.insert('', tk.END, values=(
                row[0], row[1], row[2], row[3], row[4], row[5],
                row[6], row[7], row[8], row[9], row[10], row[11],
                row[12], row[13], row[14], row[15], row[16], row[17],
                row[19], row[23]
            ))
        
        self.status_var.set(f"Found {len(rows)} records")
        
    def add_record(self):
        """Open dialog to add new record"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Loan Application")
        dialog.geometry("800x600")
        
        # Create form
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable canvas
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields
        fields = {}
        field_labels = [
            ("Branch Code", "branch_code"), ("Branch Name", "branch_name"), ("District", "district"),
            ("Region Code", "region_code"), ("Region Name", "region_name"), ("Applicant Name", "applicant_name"),
            ("Gender", "gender"), ("Mobile", "mobile"), ("Email", "email"), ("Address", "address"),
            ("Category", "category"), ("Occupation", "occupation"), ("Annual Income", "annual_income"),
            ("Loan Type", "loan_type"), ("Loan Amount", "loan_amount"), ("DOB", "dob"),
            ("Status", "is_active"), ("Remarks", "remarks"), ("Bank Name", "bank_name"),
            ("PAN Number", "pan_number"), ("Account Number", "account_number")
        ]
        
        row = 0
        for label_text, field_name in field_labels:
            ttk.Label(scrollable_frame, text=label_text + ":").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
            
            if field_name == "remarks":
                entry = tk.Text(scrollable_frame, height=4, width=30)
                entry.grid(row=row, column=1, pady=5, padx=5)
            elif field_name == "gender":
                entry = ttk.Combobox(scrollable_frame, values=['M', 'F', 'Other'], width=27)
                entry.grid(row=row, column=1, pady=5, padx=5)
            elif field_name == "is_active":
                entry = ttk.Combobox(scrollable_frame, values=['Y', 'N'], width=27)
                entry.grid(row=row, column=1, pady=5, padx=5)
                entry.set('Y')
            else:
                entry = ttk.Entry(scrollable_frame, width=30)
                entry.grid(row=row, column=1, pady=5, padx=5)
            
            fields[field_name] = entry
            row += 1
        
        def save_record():
            data = {}
            for field_name, widget in fields.items():
                if field_name == "remarks":
                    data[field_name] = widget.get("1.0", tk.END).strip()
                else:
                    data[field_name] = widget.get().strip()
            
            # Add application date and time
            now = datetime.now()
            data['application_date'] = now.strftime("%m/%d/%Y")
            data['application_time'] = now.strftime("%m/%d/%Y %H:%M")
            
            # Insert into database
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            
            query = f"INSERT INTO loan_applications ({columns}) VALUES ({placeholders})"
            
            try:
                self.cursor.execute(query, tuple(data.values()))
                self.conn.commit()
                messagebox.showinfo("Success", "Record added successfully!")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add record: {str(e)}")
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Button(button_frame, text="Save", command=save_record).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def edit_record(self):
        """Edit selected record"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record to edit")
            return
        
        # Get record ID
        record_id = self.tree.item(selected[0])['values'][0]
        
        # Fetch full record
        self.cursor.execute("SELECT * FROM loan_applications WHERE id = ?", (record_id,))
        record = self.cursor.fetchone()
        
        if not record:
            messagebox.showerror("Error", "Record not found")
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Loan Application")
        dialog.geometry("800x600")
        
        # Similar form as add_record but populated with existing data
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        fields = {}
        field_mapping = [
            ("Branch Code", 1), ("Branch Name", 2), ("District", 3), ("Region Code", 4),
            ("Region Name", 5), ("Applicant Name", 6), ("Gender", 7), ("Mobile", 8),
            ("Email", 9), ("Address", 10), ("Category", 11), ("Occupation", 12),
            ("Annual Income", 13), ("Loan Type", 14), ("Loan Amount", 15), ("DOB", 16),
            ("Bank Name", 21), ("PAN Number", 22), ("Status", 19), ("Remarks", 23)
        ]
        
        row = 0
        for label_text, idx in field_mapping:
            ttk.Label(scrollable_frame, text=label_text + ":").grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
            
            if label_text == "Remarks":
                entry = tk.Text(scrollable_frame, height=4, width=30)
                entry.insert("1.0", record[idx] if record[idx] else "")
                entry.grid(row=row, column=1, pady=5, padx=5)
            elif label_text == "Gender":
                entry = ttk.Combobox(scrollable_frame, values=['M', 'F', 'Other'], width=27)
                entry.set(record[idx] if record[idx] else "")
                entry.grid(row=row, column=1, pady=5, padx=5)
            elif label_text == "Status":
                entry = ttk.Combobox(scrollable_frame, values=['Y', 'N'], width=27)
                entry.set(record[idx] if record[idx] else "")
                entry.grid(row=row, column=1, pady=5, padx=5)
            else:
                entry = ttk.Entry(scrollable_frame, width=30)
                entry.insert(0, record[idx] if record[idx] else "")
                entry.grid(row=row, column=1, pady=5, padx=5)
            
            fields[label_text] = entry
            row += 1
        
        def update_record():
            update_data = {
                'branch_code': fields["Branch Code"].get(),
                'branch_name': fields["Branch Name"].get(),
                'district': fields["District"].get(),
                'region_code': fields["Region Code"].get(),
                'region_name': fields["Region Name"].get(),
                'applicant_name': fields["Applicant Name"].get(),
                'gender': fields["Gender"].get(),
                'mobile': fields["Mobile"].get(),
                'email': fields["Email"].get(),
                'address': fields["Address"].get(),
                'category': fields["Category"].get(),
                'occupation': fields["Occupation"].get(),
                'annual_income': fields["Annual Income"].get(),
                'loan_type': fields["Loan Type"].get(),
                'loan_amount': fields["Loan Amount"].get(),
                'dob': fields["DOB"].get(),
                'bank_name': fields["Bank Name"].get(),
                'pan_number': fields["PAN Number"].get(),
                'is_active': fields["Status"].get(),
                'remarks': fields["Remarks"].get("1.0", tk.END).strip()
            }
            
            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            query = f"UPDATE loan_applications SET {set_clause} WHERE id = ?"
            
            try:
                self.cursor.execute(query, tuple(update_data.values()) + (record_id,))
                self.conn.commit()
                messagebox.showinfo("Success", "Record updated successfully!")
                dialog.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update record: {str(e)}")
        
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Button(button_frame, text="Update", command=update_record).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def delete_record(self):
        """Delete selected record"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a record to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
            record_id = self.tree.item(selected[0])['values'][0]
            
            self.cursor.execute("DELETE FROM loan_applications WHERE id = ?", (record_id,))
            self.conn.commit()
            
            self.load_data()
            messagebox.showinfo("Success", "Record deleted successfully!")
            
    def export_to_csv(self):
        """Export data to CSV file"""
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            self.cursor.execute("SELECT * FROM loan_applications")
            data = self.cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in self.cursor.description]
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=columns)
            df.to_csv(filename, index=False)
            
            messagebox.showinfo("Success", f"Data exported to {filename}")
            
    def bulk_import(self):
        """Bulk import data from CSV"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                df = pd.read_csv(filename)
                df.to_sql('loan_applications', self.conn, if_exists='append', index=False)
                self.load_data()
                messagebox.showinfo("Success", f"Imported {len(df)} records successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")

def main():
    root = tk.Tk()
    app = LoanDatabaseApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()