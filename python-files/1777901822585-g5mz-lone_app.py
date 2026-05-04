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
        
        ttk.Button(button_frame, text="➕ Add New Record", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✏️ Edit Selected", command=self.edit_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete Selected", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Refresh", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📁 Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📂 Bulk Import", command=self.bulk_import).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="⭐ Import All Data", command=self.import_all_original_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Delete All", command=self.delete_all_records).pack(side=tk.LEFT, padx=5)
        
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
        
    def import_all_original_data(self):
        """Import all original data at once"""
        
        # First check if table exists and has data
        self.cursor.execute("SELECT COUNT(*) FROM loan_applications")
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            if not messagebox.askyesno("Confirm", f"Database already has {count} records. Do you want to delete existing records and import fresh data?"):
                return
            self.cursor.execute("DELETE FROM loan_applications")
            self.conn.commit()
        
        # Complete original data
        all_data = [
            # Record 1
            ("5345", "Pratapgarh", "PRATAPGARH", "5344", "REGIONAL OFFICE, PRATAPGARH", "MOHD ANEES", "M", "9721144093", "mohdanis.pbh@gmail.com", "Village kishundaspur Post Kadipur prtapgarh", "", "Sr.Excutive", "", "Personal Loan", "250000", "", "7/20/2023 8:40", "Y", "", "", "AUBPA4083C", "0", ""),
            # Record 2
            ("6370", "Azad Chaowk", "GORAKHPUR", "6332", "REGIONAL OFFICE, GORAKHPUR 2", "SS", "M", "7506157834", "sarvesh055@rediffmail.com", "AA", "", "AA", "", "Education Loan", "1000000", "", "7/25/2023 12:51", "N", "", "", "", "2", "Detail na"),
            # Record 3
            ("8275", "Jaigopalganj", "JAUNPUR", "8209", "REGIONAL OFFICE, JAUNPUR", "Ankur patel", "M", "8009183873", "aankurpatel773@gmail.com", "New colony", "", "Job", "", "Housing Loan", "2000000", "", "7/25/2023 1:51", "Y", "", "", "Ceupp5419l", "0", ""),
            # Record 4
            ("5667", "VIKAS BHAWAN ALLAHABAD", "ALLAHABAD", "5261", "REGIONAL OFFICE, Prayagraj(Allahabad)", "Abhay", "M", "8299330151", "eng.abhay@gmail.com", "Allahabad ram", "", "Salaried", "", "Housing Loan", "2000000", "", "7/25/2023 2:02", "Y", "", "", "EMJPS5678P", "0", ""),
            # Record 5
            ("5109", "AHIMANE", "SULTANPUR", "5827", "REGIONAL OFFICE, SULTANPUR", "Pawan kumar pandey", "M", "8737821557", "pawanpandey922@gmail.com", "169 new abadi gwalmandi near police line sitapur", "", "Employee", "", "Vehicle Loan", "10000", "", "7/25/2023 2:18", "N", "", "", "", "0", ""),
            # Record 6
            ("8154", "Bahariyabad", "GHAZIPUR", "8140", "Regional Office, GHAZIPUR", "Ankit Singh", "M", "9451546819", "dankitsingh@gmail.com", "Village and Post Gadaipur", "", "Service", "", "MSME Loan", "1000000", "", "7/25/2023 2:18", "Y", "", "", "DIBPS8625D", "2", "Ankit singh is staff of our bank. By mistake he has applied for loan application ."),
            # Record 7
            ("5450", "CHURIYANI", "FATEHPUR", "5826", "REGIONAL OFFICE FATEHPUR", "Ashwani Yadav", "M", "7037696204", "ashwaniyadav1248@gmail.com", "Baroda UP gramin Bank Naraini", "", "Agriculture", "", "Agriculture", "125000", "", "7/25/2023 2:40", "Y", "", "", "CQHPA2040R", "2", "Dummy data test by branch"),
            # Record 8
            ("8244", "Shahganj", "JAUNPUR", "8209", "REGIONAL OFFICE, JAUNPUR", "vivek srivastav", "M", "8707225440", "viveksrivastav30@gmail.com", "MADHUKER SRIVASTAV near pooja samagri ghar", "", "Officer", "", "Vehicle Loan", "1500000", "", "7/25/2023 3:33", "N", "", "", "FETPS4307Q", "0", ""),
            # Record 9
            ("8383", "BHARLAI", "VARANASI", "8355", "REGIONAL OFFICE, VARANASI", "Dali Gupta", "F", "9935086528", "pradeep8031vns@gmail.com", "Flat no. 28 Nagar Nigam colony shivpur", "", "Tellering", "", "Mudra Loan", "100000", "", "7/25/2023 4:50", "Y", "", "", "", "0", ""),
            # Record 10
            ("5939", "PANDAR", "ALLAHABAD", "5261", "REGIONAL OFFICE, Prayagraj(Allahabad)", "Deepak singh patel", "M", "8707003838", "deepaksinghpatelit@gmail.com", "Dandi prayagraj", "", "Service", "", "Personal Loan", "500000", "", "7/26/2023 2:29", "Y", "", "", "CCAPP6434K", "0", ""),
            # Record 11
            ("5823", "RAMPUR THARIYANW", "FATEHPUR", "5826", "REGIONAL OFFICE FATEHPUR", "saubhagya kant", "M", "8090841226", "saubhayakant1226@gmail.com", "L I G 79 barra 4 kanpur", "", "Service", "", "Housing Loan", "5000000", "", "7/26/2023 5:04", "Y", "", "", "DLNPK3121B", "2", "Dummy inquiry by staff"),
            # Record 12
            ("5531", "DULHU PUR", "AMBEDKAR NAGAR", "5469", "REGIONAL OFFICE, FAIZABAD", "SINTOO KUMAR", "M", "9205503235", "sintookgautam@gmail.com", "PINDORIYA AMBEDKARNAGAR", "", "LAL PAH LAB", "", "Mudra Loan", "200000", "", "7/26/2023 5:06", "Y", "", "", "GCLPK7346J", "2", "branch has try to contact but unable to contact and also contact on the given mobile numer but he didnot pickup the call"),
            # Record 13
            ("6295", "KURI BAZAR", "GORAKHPUR", "6271", "REGIONAL OFFICE, GORAKHPUR 1", "Krishan Dutt", "M", "9971322716", "kdutt446@gmail.com", "kuri bazaar belghat", "", "self employed", "", "Housing Loan", "2500000", "", "7/26/2023 5:49", "N", "", "", "BGDPD5828F", "0", ""),
            # Record 14
            ("6011", "MALDAH BAGHURI", "BALLIA", "6002", "REGIONAL OFFICE, BALLIA 1", "Golu", "M", "8174887351", "golukumar887351@gmail.com", "Kurha tetra", "General", "Drive", "15000", "Vehicle Loan", "350", "7/21/2004", "7/26/2023 8:06", "N", "", "State Bank Of India", "DOFPG5949G", "2", "PROJECT NOT VIABLE"),
            # Record 15
            ("6337", "Ahirauli (K)", "KUSHI NAGAR", "6332", "REGIONAL OFFICE, GORAKHPUR 2", "NITESH RAM", "M", "7970402182", "niteshram797040@gmail.com", "BARWABRIT JALALPUR GOPALGANJ BIHAR", "SC", "Chamar", "5000", "Personal Loan", "10000", "1/2/2004", "7/26/2023 10:21", "N", "", "Bank Of Baroda", "FXEPR3172N", "2", "Other branch applicant"),
            # Record 16
            ("5849", "JALALPURR TENGAI", "KAUSHAMBI", "5941", "REGIONAL OFFICE, KAUSHAMBI", "NITESH RAM", "M", "7970402182", "niteshram797040@gmail.com", "BARWABRIT", "SC", "Chamar", "5000", "Personal Loan", "10000", "1/1/2004", "7/26/2023 10:26", "Y", "6.47401E+13", "Baroda UP Bank", "FXEPR3172N", "0", ""),
            # Record 17
            ("6337", "Ahirauli (K)", "KUSHI NAGAR", "6332", "REGIONAL OFFICE, GORAKHPUR 2", "NITESH RAM", "M", "7970402182", "niteshram797040@gmail.com", "BARWABRIT JALALPUR GOPALGANJ", "SC", "Teacher", "20000", "Personal Loan", "10000", "1/1/2004", "7/26/2023 10:30", "Y", "6.47401E+13", "Baroda UP Bank", "FXEPR3172N", "2", "Other br applicant"),
            # Record 18
            ("5617", "BARKHAN", "BAREILLY", "5673", "REGIONAL OFFICE, BARELLI", "mohammad imran", "M", "7351266786", "immy50051@gmail.com", "Barkhan nawabganj bareilly", "OBC", "Self employed", "350000", "Personal Loan", "100000", "10/20/1992", "7/26/2023 11:00", "Y", "5.61701E+13", "Baroda UP Bank", "AFWPI8079L", "0", ""),
            # Record 19
            ("5096", "JAISINGHPUR", "SULTANPUR", "5827", "REGIONAL OFFICE, SULTANPUR", "RAM SURAT VISHWKARMA", "M", "9795901366", "ramsurat1002@gmail.com", "Village And Post Sevtari", "OBC", "Teacher", "80000", "Personal Loan", "50000", "2/10/1995", "7/26/2023 12:14", "N", "", "Bank Of Baroda", "BDUPV8577P", "0", ""),
            # Record 20
            ("8008", "Sardaha Bazar", "AZAMGARH", "8002", "Regional Office, AZAMGARH", "Alok Gupta", "M", "8933096052", "eshu3321@gmail.com", "Bhilampur sardaha bazar", "OBC", "Student", "100000", "Education Loan", "350000", "10/14/2003", "7/26/2023 1:16", "N", "", "Bank Of Baroda", "DRKPG4188K", "0", ""),
            # Record 21
            ("5898", "BARWARIPUR", "SULTANPUR", "5827", "REGIONAL OFFICE, SULTANPUR", "Saurabh Kumar", "M", "6306247728", "saurabhsharmacaac1@gmail.com", "Bhatpura", "General", "Accountant", "264000", "Personal Loan", "200000", "8/28/1997", "7/26/2023 3:05", "N", "", "Central Bank Of India", "", "0", ""),
            # Record 22
            ("6125", "PURSIA", "BASTI", "6095", "REGIONAL OFFICE, BASTI", "vinod kumar tripathi", "M", "7017064560", "vnppp@gmail.com", "village bhadi buzurg post majhowa meer basti", "General", "State Govt Employee", "360000", "Agriculture", "300000", "12/1/1959", "7/26/2023 5:02", "Y", "5.62501E+13", "Baroda UP Bank", "", "2", "DENY BY APPLICANT"),
            # Record 23
            ("8027", "Balrampur", "AZAMGARH", "8002", "Regional Office, AZAMGARH", "Mahesh", "M", "9453369430", "mahishg790@gmail.com", "Basti bhujwal", "General", "Farmer", "20000", "Mudra Loan", "200000", "7/26/1997", "7/26/2023 5:26", "Y", "1.11252E+14", "Baroda UP Bank", "CFRPG1197J", "0", ""),
            # Record 24
            ("6330", "BARGO BARAIPAR", "GORAKHPUR", "6271", "REGIONAL OFFICE, GORAKHPUR 1", "Suraj vishwakarma", "M", "9005353267", "sikzbabu010797@gmail.com", "VILL-BARGO POST-BARAIPAR PS-GAGAHA, DISTRICT-GORAKHPUR 273412", "OBC", "Hero fin Corp ltd", "280000", "Mudra Loan", "200000", "7/1/1997", "7/27/2023 3:37", "Y", "6.33001E+13", "Baroda UP Bank", "GHKPS7629C", "0", ""),
            # Record 25
            ("6210", "RAMPUR BUJURG", "DEORIA", "6157", "REGIONAL OFFICE, DEORIA", "abhishek kumar", "M", "7881115801", "as4543158@gmail.com", "rampur buzurg deoria up", "OBC", "self employed", "220000", "Education Loan", "251000", "1/11/2004", "7/27/2023 4:08", "Y", "75044310414", "Baroda UP Bank", "GHWPD0152F", "0", ""),
            # Record 26
            ("5685", "AYODHYA", "AYODHYA", "5469", "REGIONAL OFFICE, FAIZABAD", "Sujeet Pathak", "M", "6306329457", "sujeet2241223@gmail.com", "AYODHYA, UTTAR PRADESH, INDIA", "General", "Computer opretor", "300000", "MSME Loan", "200000", "12/10/2001", "7/27/2023 4:45", "Y", "5.68501E+13", "Baroda UP Bank", "GSLPP9828l", "0", ""),
            # Record 27
            ("6496", "BASDILA PANDEY", "KUSHI NAGAR", "6444", "REGIONAL OFFICE, PADRAUNA", "UTKARSH PRASAD NIRMAL", "M", "8543082363", "nirmalsushant004@gmail.com", "Village.Karaunda,Post.mandipur,dist.deoria", "SC", "Student", "60000", "Education Loan", "100000", "5/11/2003", "7/27/2023 5:13", "Y", "75128772691", "Baroda UP Bank", "CPDPN8254F", "2", "Not applicable for branch"),
            # Record 28
            ("5173", "NAURANGA", "KANPUR NAGAR", "5165", "REGIONAL OFFICE, KANPUR", "DEEPANSHOO", "M", "8090174629", "deepanshoosen32@gmail.com", "VILL KAITHA", "OBC", "MANUFACTURE AND SERVICE", "250000", "Mudra Loan", "300000", "1/12/2003", "7/27/2023 5:26", "Y", "5.17301E+13", "Baroda UP Bank", "GWGPD3992A", "0", ""),
            # Record 29
            ("6462", "KASIA", "KUSHI NAGAR", "6444", "REGIONAL OFFICE, PADRAUNA", "Singaldeep", "M", "9565709116", "singaldeepkumar1@gmail.com", "2.99706E+11", "SC", "PSU Employee", "9565709116", "Vehicle Loan", "100", "7/27/2023", "7/27/2023 9:42", "Y", "75106805056", "Baroda UP Bank", "QSNPS5599P", "2", "Customer has no information regarding this loan application.He denied for any loan requirement"),
            # Record 30
            ("5099", "Durgapur", "AMETHI", "5833", "REGIONAL OFFICE, AMETHI", "ANKIT PANDEY", "M", "7236097128", "ANKITWINNER121@GMAIL.COM", "SOHAGDANE RAMGANJ AMETHI", "General", "IMPORT HEAD(CHA)", "500000", "Tractor Loan", "500000", "7/15/1998", "7/27/2023 11:43", "Y", "5.6981E+12", "Baroda UP Bank", "DTSPP9260B", "2", "Applicant works in Ludhiana, not residing in service area"),
            # Record 31
            ("5659", "Katra", "SHAHJAHANPUR", "5628", "REGIONAL OFFICE, SHAHJAHANPUR", "Akhilesh yadav", "F", "9335471293", "Akhileshy3904@gmail.com", "Kamalpur urf Nawada post khundra Tilhar Shahjahanpur", "OBC", "Farmer", "10000", "Personal Loan", "10000", "1/1/2003", "7/27/2023 12:40", "N", "", "Bank Of Baroda", "BHMPY1117N", "0", ""),
            # Record 32
            ("5659", "Katra", "SHAHJAHANPUR", "5628", "REGIONAL OFFICE, SHAHJAHANPUR", "Akhilesh yadav", "F", "9335471293", "Akhileshy3904@gmail.com", "Kamalpur urf Nawada post khundra Tilhar Shahjahanpur", "OBC", "Farmer", "10000", "Personal Loan", "50000", "1/1/2003", "7/27/2023 12:42", "N", "", "Bank Of Baroda", "BHMPY1117N", "0", ""),
            # Record 33
            ("5345", "Pratapgarh", "PRATAPGARH", "5344", "REGIONAL OFFICE, PRATAPGARH", "DURGA PRASAD SHUKLA", "M", "9118887800", "shivamshing1112@gmail.com", "Shukulpur dahilamau", "General", "HOMEGUARD", "308016", "Personal Loan", "300000", "1/15/1978", "7/27/2023 1:42", "Y", "5.34501E+13", "Baroda UP Bank", "OIIPS4459B", "0", ""),
            # Record 34
            ("6168", "Bhawani Chhapar", "DEORIA", "6157", "REGIONAL OFFICE, DEORIA", "Dharmendar Kumar singh", "M", "7607166299", "singhdharmendar9252@gmail.com", "Koiladewa", "OBC", "Farmer", "10000", "Education Loan", "20000", "7/17/2002", "7/27/2023 2:08", "Y", "75101314392", "Baroda UP Bank", "LTDPK4957P", "2", "Resident of Bihar State"),
            # Record 35
            ("5173", "NAURANGA", "KANPUR NAGAR", "5165", "REGIONAL OFFICE, KANPUR", "Deepanshoo", "M", "8090174629", "deepanshoosen32@gmail.com", "VILL KAITHA", "OBC", "MANUFACTURE AND SERVICE", "250000", "Mudra Loan", "300000", "1/12/2003", "7/27/2023 3:33", "Y", "5.17301E+13", "Baroda UP Bank", "GWGPD3992A", "0", ""),
        ]
        
        inserted = 0
        for record in all_data:
            try:
                self.cursor.execute('''
                    INSERT INTO loan_applications (
                        branch_code, branch_name, district, region_code, region_name,
                        applicant_name, gender, mobile, email, address, category,
                        occupation, annual_income, loan_type, loan_amount, dob,
                        application_date, is_active, account_number, bank_name,
                        pan_number, days_overdue, remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', record)
                inserted += 1
            except Exception as e:
                print(f"Error inserting record: {e}")
        
        self.conn.commit()
        self.load_data()
        messagebox.showinfo("Success", f"Successfully imported {inserted} records!")
        
    def delete_all_records(self):
        """Delete all records from database"""
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete ALL records? This action cannot be undone!"):
            self.cursor.execute("DELETE FROM loan_applications")
            self.conn.commit()
            self.load_data()
            messagebox.showinfo("Success", "All records deleted successfully!")
        
    def load_data(self):
        """Load data from database into treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.cursor.execute("SELECT * FROM loan_applications ORDER BY id DESC")
        rows = self.cursor.fetchall()
        
        for row in rows:
            self.tree.insert('', tk.END, values=(
                row[0], row[1], row[2], row[3], row[4], row[5],
                row[6], row[7], row[8], row[9], row[10], row[11],
                row[12], row[13], row[14], row[15], row[16], row[17],
                row[19], row[24] if len(row) > 24 else ""
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
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = f"SELECT * FROM loan_applications WHERE {column} LIKE ? ORDER BY id DESC"
        self.cursor.execute(query, (f'%{search_term}%',))
        rows = self.cursor.fetchall()
        
        for row in rows:
            self.tree.insert('', tk.END, values=(
                row[0], row[1], row[2], row[3], row[4], row[5],
                row[6], row[7], row[8], row[9], row[10], row[11],
                row[12], row[13], row[14], row[15], row[16], row[17],
                row[19], row[24] if len(row) > 24 else ""
            ))
        
        self.status_var.set(f"Found {len(rows)} records")
        
    def add_record(self):
        """Open dialog to add new record"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Loan Application")
        dialog.geometry("800x600")
        
        form_frame = ttk.Frame(dialog, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        fields = {}
        field_labels = [
            ("Branch Code", "branch_code"), ("Branch Name", "branch_name"), ("District", "district"),
            ("Region Code", "region_code"), ("Region Name", "region_name"), ("Applicant Name", "applicant_name"),
            ("Gender", "gender"), ("Mobile", "mobile"), ("Email", "email"), ("Address", "address"),
            ("Category", "category"), ("Occupation", "occupation"), ("Annual Income", "annual_income"),
            ("Loan Type", "loan_type"), ("Loan Amount", "loan_amount"), ("DOB", "dob"),
            ("Status", "is_active"), ("Remarks", "remarks"), ("Bank Name", "bank_name"),
            ("PAN Number", "pan_number"), ("Account Number", "account_number"), ("Days Overdue", "days_overdue")
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
            
            now = datetime.now()
            data['application_date'] = now.strftime("%m/%d/%Y")
            data['application_time'] = now.strftime("%m/%d/%Y %H:%M")
            
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
        
        record_id = self.tree.item(selected[0])['values'][0]
        self.cursor.execute("SELECT * FROM loan_applications WHERE id = ?", (record_id,))
        record = self.cursor.fetchone()
        
        if not record:
            messagebox.showerror("Error", "Record not found")
            return
        
        # Similar to add_record but with data pre-filled
        messagebox.showinfo("Info", "Edit feature - Select record and modify")
        
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
            columns = [description[0] for description in self.cursor.description]
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