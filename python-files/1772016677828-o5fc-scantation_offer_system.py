"""
Scantation Offer Management System
A professional desktop application for creating and managing offers
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path

# Handle resource paths for PyInstaller
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Try to import reportlab, provide clear error if not found
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF export will be disabled.")

class ScantationOfferSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Scantation Offer Management System")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f2f5')
        
        # Set icon and style
        self.setup_styles()
        
        # Initialize database
        self.init_database()
        
        # Create GUI
        self.create_menu()
        self.create_widgets()
        
        # Load existing offers
        self.load_offers()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        self.colors = {
            'primary': '#1e3a5c',
            'secondary': '#2b4c7c',
            'accent': '#4a7db5',
            'light': '#f8fafc',
            'border': '#cbd5e1',
            'success': '#10b981',
            'warning': '#f59e0b'
        }
        
        # Custom styles
        style.configure('Header.TLabel', font=('Helvetica', 16, 'bold'), foreground=self.colors['primary'])
        style.configure('Title.TLabel', font=('Helvetica', 14, 'bold'), foreground=self.colors['secondary'])
        style.configure('Heading.TLabel', font=('Helvetica', 12, 'bold'), foreground=self.colors['primary'])
        style.configure('Status.TLabel', font=('Helvetica', 10), foreground=self.colors['secondary'])
        
        # Button styles
        style.configure('Primary.TButton', font=('Helvetica', 10, 'bold'))
        style.configure('Success.TButton', font=('Helvetica', 10, 'bold'))
        
    def init_database(self):
        """Initialize SQLite database"""
        # Store database in user's AppData folder
        app_data = Path(os.environ.get('LOCALAPPDATA', Path.home()))
        db_folder = app_data / 'ScantationOffers'
        db_folder.mkdir(exist_ok=True)
        
        self.db_path = db_folder / 'offers.db'
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT UNIQUE,
                date TEXT,
                client_name TEXT,
                client_address TEXT,
                total_amount TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS offer_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_id INTEGER,
                item_no INTEGER,
                description TEXT,
                unit_price TEXT,
                quantity TEXT,
                discount TEXT,
                total TEXT,
                FOREIGN KEY (offer_id) REFERENCES offers (id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        self.conn.commit()
        
        # Initialize default settings
        default_settings = {
            'company_name': 'Scantation',
            'company_address': 'English Village - Villa 403, Erbil, Iraq',
            'company_phone': '00 964 783 000 0083',
            'next_quote_number': f'Q {datetime.now().year}-0104',
            'logo_text': 'S'
        }
        
        for key, value in default_settings.items():
            self.cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))
        
        self.conn.commit()
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Offer", command=self.new_offer, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Offer", command=self.open_offer, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Offer", command=self.save_offer, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export to PDF", command=self.export_to_pdf, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Settings", command=self.open_settings)
        edit_menu.add_command(label="Clear All", command=self.clear_all_fields)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="User Guide", command=self.show_guide)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_offer())
        self.root.bind('<Control-o>', lambda e: self.open_offer())
        self.root.bind('<Control-s>', lambda e: self.save_offer())
        self.root.bind('<Control-p>', lambda e: self.export_to_pdf())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
    def create_widgets(self):
        """Create main GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Offer editor
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right panel - Offers list
        right_panel = ttk.Frame(main_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self.create_offer_editor(left_panel)
        self.create_offers_list(right_panel)
        
    def create_offer_editor(self, parent):
        """Create offer editing interface"""
        # Header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Scantation Offer Editor", style='Header.TLabel').pack(side=tk.LEFT)
        
        # Company info
        company_frame = ttk.LabelFrame(parent, text="Company Information", padding="15")
        company_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Get company settings
        self.cursor.execute('SELECT value FROM settings WHERE key="company_name"')
        company_name = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT value FROM settings WHERE key="company_address"')
        company_address = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT value FROM settings WHERE key="company_phone"')
        company_phone = self.cursor.fetchone()[0]
        
        ttk.Label(company_frame, text=company_name, style='Title.TLabel').grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(company_frame, text=company_address).grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(company_frame, text=company_phone).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # Quote reference
        quote_frame = ttk.Frame(company_frame)
        quote_frame.grid(row=0, column=1, rowspan=3, padx=(50, 0))
        
        ttk.Label(quote_frame, text="QUOTE", style='Heading.TLabel').pack(side=tk.LEFT, padx=5)
        
        self.cursor.execute('SELECT value FROM settings WHERE key="next_quote_number"')
        default_quote = self.cursor.fetchone()[0]
        
        self.quote_number = ttk.Entry(quote_frame, width=15, font=('Courier', 10, 'bold'))
        self.quote_number.insert(0, default_quote)
        self.quote_number.pack(side=tk.LEFT, padx=5)
        
        self.quote_date = ttk.Entry(quote_frame, width=12, font=('Courier', 10))
        self.quote_date.insert(0, datetime.now().strftime('%d-%b-%y'))
        self.quote_date.pack(side=tk.LEFT, padx=5)
        
        # Client information
        client_frame = ttk.LabelFrame(parent, text="Client Information", padding="15")
        client_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(client_frame, text="Client Name:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.client_name = ttk.Entry(client_frame, width=40)
        self.client_name.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(client_frame, text="Client Address:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.client_address = ttk.Entry(client_frame, width=60)
        self.client_address.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Items table
        items_frame = ttk.LabelFrame(parent, text="Offer Items", padding="15")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview for items
        columns = ('No.', 'Description', 'Unit Price (IQD)', 'Qty', 'Discount', 'Total (IQD)')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings', height=6)
        
        # Define headings
        for col in columns:
            self.items_tree.heading(col, text=col)
            if col == 'No.':
                self.items_tree.column(col, width=50, anchor='center')
            elif col == 'Description':
                self.items_tree.column(col, width=300)
            elif col == 'Unit Price (IQD)':
                self.items_tree.column(col, width=120, anchor='e')
            elif col == 'Qty':
                self.items_tree.column(col, width=70, anchor='center')
            elif col == 'Discount':
                self.items_tree.column(col, width=80, anchor='center')
            else:
                self.items_tree.column(col, width=120, anchor='e')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        
        self.items_tree.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Buttons for item management
        item_buttons_frame = ttk.Frame(items_frame)
        item_buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(item_buttons_frame, text="Add Item", command=self.add_item, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(item_buttons_frame, text="Edit Item", command=self.edit_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(item_buttons_frame, text="Delete Item", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(item_buttons_frame, text="Clear Items", command=self.clear_items).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        items_frame.grid_rowconfigure(0, weight=1)
        items_frame.grid_columnconfigure(0, weight=1)
        
        # Total amount
        total_frame = ttk.Frame(parent)
        total_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(total_frame, text="Total Amount:", style='Heading.TLabel').pack(side=tk.LEFT)
        self.total_amount = ttk.Entry(total_frame, width=20, font=('Courier', 12, 'bold'), justify='right')
        self.total_amount.pack(side=tk.RIGHT)
        self.total_amount.insert(0, "0")
        
        # Save button
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save Offer", command=self.save_offer, style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export PDF", command=self.export_to_pdf, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="New Offer", command=self.new_offer).pack(side=tk.LEFT, padx=5)
        
        # Load sample data
        self.load_sample_data()
        
    def create_offers_list(self, parent):
        """Create offers list panel"""
        ttk.Label(parent, text="Saved Offers", style='Header.TLabel').pack(pady=(0, 10))
        
        # Search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_offers)
        
        # Offers treeview
        columns = ('Quote #', 'Client', 'Date', 'Total', 'Status')
        self.offers_tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.offers_tree.heading(col, text=col)
            if col == 'Quote #':
                self.offers_tree.column(col, width=100)
            elif col == 'Client':
                self.offers_tree.column(col, width=150)
            elif col == 'Date':
                self.offers_tree.column(col, width=80)
            elif col == 'Total':
                self.offers_tree.column(col, width=100, anchor='e')
            else:
                self.offers_tree.column(col, width=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.offers_tree.yview)
        self.offers_tree.configure(yscrollcommand=scrollbar.set)
        
        self.offers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to open offer
        self.offers_tree.bind('<Double-1>', self.on_offer_double_click)
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Open", command=self.open_offer).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_offer).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.load_offers).pack(side=tk.LEFT, padx=2)
        
    def load_sample_data(self):
        """Load sample data from original offer"""
        sample_items = [
            (1, "Dimond Collection 1000 ML", "300,000", "1", "30%", "210,000"),
            (2, "Daimond Collection 1000 ML", "300,000", "1", "30%", "210,000"),
            (3, "vip Collection 1000 ML", "400,000", "1", "30%", "280,000")
        ]
        
        for item in sample_items:
            self.items_tree.insert('', 'end', values=item)
        
        self.calculate_total()
        
    def add_item(self):
        """Add new item to the offer"""
        dialog = ItemDialog(self.root, "Add Item")
        if dialog.result:
            self.items_tree.insert('', 'end', values=dialog.result)
            self.calculate_total()
            
    def edit_item(self):
        """Edit selected item"""
        selected = self.items_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item to edit.")
            return
        
        item = self.items_tree.item(selected[0])
        dialog = ItemDialog(self.root, "Edit Item", item['values'])
        if dialog.result:
            self.items_tree.item(selected[0], values=dialog.result)
            self.calculate_total()
            
    def delete_item(self):
        """Delete selected item"""
        selected = self.items_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            self.items_tree.delete(selected[0])
            self.calculate_total()
            
    def clear_items(self):
        """Clear all items"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all items?"):
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)
            self.calculate_total()
            
    def calculate_total(self):
        """Calculate total amount from all items"""
        total = 0
        for item in self.items_tree.get_children():
            values = self.items_tree.item(item)['values']
            if values and len(values) > 5:
                # Remove commas and convert to number
                total_str = values[5].replace(',', '')
                try:
                    total += int(total_str)
                except ValueError:
                    pass
        
        self.total_amount.delete(0, tk.END)
        self.total_amount.insert(0, f"{total:,}")
        
    def save_offer(self):
        """Save current offer to database"""
        try:
            # Get offer data
            quote_number = self.quote_number.get()
            date = self.quote_date.get()
            client_name = self.client_name.get()
            client_address = self.client_address.get()
            total = self.total_amount.get()
            
            if not client_name:
                messagebox.showwarning("Missing Data", "Please enter client name.")
                return
            
            # Save to database
            self.cursor.execute('''
                INSERT INTO offers (quote_number, date, client_name, client_address, total_amount, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (quote_number, date, client_name, client_address, total, 'draft'))
            
            offer_id = self.cursor.lastrowid
            
            # Save items
            for item in self.items_tree.get_children():
                values = self.items_tree.item(item)['values']
                self.cursor.execute('''
                    INSERT INTO offer_items (offer_id, item_no, description, unit_price, quantity, discount, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (offer_id, values[0], values[1], values[2], values[3], values[4], values[5]))
            
            self.conn.commit()
            
            # Update next quote number
            try:
                current_num = int(quote_number.split('-')[-1])
                next_num = current_num + 1
                next_quote = f"Q {datetime.now().year}-{next_num:04d}"
                self.cursor.execute('UPDATE settings SET value=? WHERE key="next_quote_number"', (next_quote,))
                self.conn.commit()
            except:
                pass  # If format is different, don't update
            
            messagebox.showinfo("Success", "Offer saved successfully!")
            self.load_offers()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save offer: {str(e)}")
            
    def load_offers(self):
        """Load offers from database into treeview"""
        # Clear existing items
        for item in self.offers_tree.get_children():
            self.offers_tree.delete(item)
        
        # Load offers
        self.cursor.execute('''
            SELECT quote_number, client_name, date, total_amount, status, id
            FROM offers
            ORDER BY created_at DESC
        ''')
        
        for row in self.cursor.fetchall():
            self.offers_tree.insert('', 'end', values=row[:5], tags=(row[5],))
            
    def open_offer(self):
        """Open selected offer"""
        selected = self.offers_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an offer to open.")
            return
        
        # Get offer ID from tags
        offer_id = self.offers_tree.item(selected[0])['tags'][0]
        
        # Load offer data
        self.cursor.execute('SELECT * FROM offers WHERE id=?', (offer_id,))
        offer = self.cursor.fetchone()
        
        if offer:
            # Clear current data
            self.clear_items()
            
            # Set offer data
            self.quote_number.delete(0, tk.END)
            self.quote_number.insert(0, offer[1])
            self.quote_date.delete(0, tk.END)
            self.quote_date.insert(0, offer[2])
            self.client_name.delete(0, tk.END)
            self.client_name.insert(0, offer[3])
            self.client_address.delete(0, tk.END)
            self.client_address.insert(0, offer[4])
            self.total_amount.delete(0, tk.END)
            self.total_amount.insert(0, offer[5])
            
            # Load items
            self.cursor.execute('SELECT item_no, description, unit_price, quantity, discount, total FROM offer_items WHERE offer_id=? ORDER BY item_no', (offer_id,))
            for item in self.cursor.fetchall():
                self.items_tree.insert('', 'end', values=item)
                
    def delete_offer(self):
        """Delete selected offer"""
        selected = self.offers_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an offer to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this offer?"):
            offer_id = self.offers_tree.item(selected[0])['tags'][0]
            
            # Delete items first (foreign key constraint)
            self.cursor.execute('DELETE FROM offer_items WHERE offer_id=?', (offer_id,))
            self.cursor.execute('DELETE FROM offers WHERE id=?', (offer_id,))
            self.conn.commit()
            
            self.load_offers()
            
    def search_offers(self, event=None):
        """Search offers by client name or quote number"""
        search_term = self.search_entry.get().lower()
        
        for item in self.offers_tree.get_children():
            values = self.offers_tree.item(item)['values']
            if search_term in str(values[0]).lower() or search_term in str(values[1]).lower():
                self.offers_tree.selection_add(item)
                self.offers_tree.focus(item)
            else:
                self.offers_tree.selection_remove(item)
                
    def on_offer_double_click(self, event):
        """Handle double-click on offer"""
        self.open_offer()
        
    def new_offer(self):
        """Create new offer"""
        if messagebox.askyesno("New Offer", "Create new offer? Unsaved changes will be lost."):
            self.clear_all_fields()
            
            # Get next quote number
            self.cursor.execute('SELECT value FROM settings WHERE key="next_quote_number"')
            next_quote = self.cursor.fetchone()[0]
            self.quote_number.delete(0, tk.END)
            self.quote_number.insert(0, next_quote)
            
            # Set current date
            self.quote_date.delete(0, tk.END)
            self.quote_date.insert(0, datetime.now().strftime('%d-%b-%y'))
            
    def clear_all_fields(self):
        """Clear all input fields"""
        self.client_name.delete(0, tk.END)
        self.client_address.delete(0, tk.END)
        self.clear_items()
        
    def export_to_pdf(self):
        """Export current offer to PDF"""
        if not REPORTLAB_AVAILABLE:
            messagebox.showerror("Error", 
                "PDF export requires reportlab library.\n\n"
                "Please install it with:\n"
                "pip install reportlab\n\n"
                "Or download the full version with PDF support.")
            return
        
        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"offer_{self.quote_number.get().replace(' ', '_')}.pdf"
            )
            
            if not file_path:
                return
            
            # Create PDF
            doc = SimpleDocTemplate(file_path, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1e3a5c'),
                spaceAfter=30
            )
            
            # Header
            story.append(Paragraph("SCANTATION", title_style))
            
            # Company info
            self.cursor.execute('SELECT value FROM settings WHERE key="company_name"')
            company_name = self.cursor.fetchone()[0]
            self.cursor.execute('SELECT value FROM settings WHERE key="company_address"')
            company_address = self.cursor.fetchone()[0]
            self.cursor.execute('SELECT value FROM settings WHERE key="company_phone"')
            company_phone = self.cursor.fetchone()[0]
            
            company_info = f"""
            <b>{company_address}</b><br/>
            <b>{company_phone}</b><br/>
            <br/>
            """
            story.append(Paragraph(company_info, styles['Normal']))
            
            # Quote reference
            quote_info = f"""
            <para alignment='right'>
            <b>QUOTE {self.quote_number.get()} {self.quote_date.get()}</b>
            </para>
            """
            story.append(Paragraph(quote_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Client info
            client_info = f"""
            <b>Client Name:</b> {self.client_name.get()}<br/>
            <b>Address:</b> {self.client_address.get()}<br/>
            """
            story.append(Paragraph(client_info, styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Items table
            table_data = [['No.', 'DESCRIPTION', 'Unit Price (IQD)', 'Qty', 'Discount', 'Total Amount (IQD)']]
            
            for item in self.items_tree.get_children():
                values = self.items_tree.item(item)['values']
                table_data.append(values)
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Total
            story.append(Paragraph(f"<para alignment='right'><b>Total Amount: {self.total_amount.get()} IQD</b></para>", styles['Normal']))
            story.append(Spacer(1, 30))
            
            # Thank you
            story.append(Paragraph("<para alignment='center'><b>Thank you for your business!</b></para>", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Terms
            terms = """
            <b>Notes & Terms</b><br/>
            Prices quote in IQD. Quotation is valid for 14 days. Payment terms is 100% upon confirmation.<br/><br/>
            Scantation will provide all scent material including refills of the scent and shall maintain and service 
            the subscriber Equipment during the term of this agreement. Scantation will service all Scantation equipment 
            on a 4-6 week internal period, and will provide a call center number shall the subscriber require any additional 
            service. Maintenance of the Equipment which are not the property of Scantation shall be the responsibility of Subscriber.<br/><br/>
            Except for Scantation maintenance obligations as set forth herein, Subscriber shall indemnify Scantation and hold it harmless 
            from and against any and all losses caused by accidental fire, theft, or misuse of the equipment.<br/><br/>
            Unless otherwise stipulated in a separate purchase agreement, Subscriber acquires no ownership, title, property rights or 
            interest in or to the Scantation Equipment, but acquires only the right of use in accordance with the provisions of this Agreement.
            """
            story.append(Paragraph(terms, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            messagebox.showinfo("Success", f"PDF exported successfully!\n{file_path}")
            
            # Open PDF
            try:
                os.startfile(file_path)
            except:
                pass
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
            
    def open_settings(self):
        """Open settings dialog"""
        SettingsDialog(self.root, self)
        
    def show_about(self):
        """Show about dialog"""
        about_text = """
        Scantation Offer Management System
        Version 1.0
        
        A professional desktop application for
        creating and managing Scantation offers.
        
        © 2026 Scantation
        """
        messagebox.showinfo("About", about_text)
        
    def show_guide(self):
        """Show user guide"""
        guide_text = """
        User Guide:
        
        1. Create New Offer: File → New Offer or Ctrl+N
        2. Add Items: Click "Add Item" button
        3. Save Offer: Click "Save Offer" or Ctrl+S
        4. Export to PDF: Click "Export PDF" or Ctrl+P
        5. Open Saved Offer: Double-click in offers list
        
        All fields are editable. Items can be added, edited, or deleted.
        """
        messagebox.showinfo("User Guide", guide_text)


class ItemDialog:
    """Dialog for adding/editing items"""
    def __init__(self, parent, title, values=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("600x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (300 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create form
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Form fields
        fields = [
            ('Item No.:', 'no'),
            ('Description:', 'desc'),
            ('Unit Price (IQD):', 'price'),
            ('Quantity:', 'qty'),
            ('Discount:', 'discount'),
            ('Total (IQD):', 'total')
        ]
        
        self.entries = {}
        
        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            self.entries[key] = ttk.Entry(frame, width=50)
            self.entries[key].grid(row=i, column=1, sticky=tk.W, pady=5, padx=10)
        
        # Fill values if editing
        if values:
            self.entries['no'].insert(0, values[0])
            self.entries['desc'].insert(0, values[1])
            self.entries['price'].insert(0, values[2])
            self.entries['qty'].insert(0, values[3])
            self.entries['discount'].insert(0, values[4])
            self.entries['total'].insert(0, values[5])
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind calculate total
        self.entries['price'].bind('<KeyRelease>', self.calculate_total)
        self.entries['qty'].bind('<KeyRelease>', self.calculate_total)
        self.entries['discount'].bind('<KeyRelease>', self.calculate_total)
        
        self.dialog.wait_window()
        
    def calculate_total(self, event=None):
        """Calculate total based on price, qty, and discount"""
        try:
            price = float(self.entries['price'].get().replace(',', ''))
            qty = float(self.entries['qty'].get() or 1)
            discount_str = self.entries['discount'].get().replace('%', '')
            discount = float(discount_str or 0) / 100
            
            total = price * qty * (1 - discount)
            self.entries['total'].delete(0, tk.END)
            self.entries['total'].insert(0, f"{int(total):,}")
            
        except ValueError:
            pass
            
    def ok_clicked(self):
        """Handle OK button click"""
        self.result = [
            self.entries['no'].get(),
            self.entries['desc'].get(),
            self.entries['price'].get(),
            self.entries['qty'].get(),
            self.entries['discount'].get(),
            self.entries['total'].get()
        ]
        self.dialog.destroy()


class SettingsDialog:
    """Settings dialog for application configuration"""
    def __init__(self, parent, app):
        self.app = app
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create settings widgets"""
        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Get current settings
        self.app.cursor.execute('SELECT key, value FROM settings')
        settings = dict(self.app.cursor.fetchall())
        
        # Settings fields
        fields = [
            ('Company Name:', 'company_name'),
            ('Company Address:', 'company_address'),
            ('Company Phone:', 'company_phone'),
            ('Next Quote Number:', 'next_quote_number'),
            ('Logo Text:', 'logo_text')
        ]
        
        self.entries = {}
        
        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=8)
            self.entries[key] = ttk.Entry(frame, width=50)
            self.entries[key].grid(row=i, column=1, sticky=tk.W, pady=8, padx=10)
            self.entries[key].insert(0, settings.get(key, ''))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def save_settings(self):
        """Save settings to database"""
        for key, entry in self.entries.items():
            self.app.cursor.execute('UPDATE settings SET value=? WHERE key=?', (entry.get(), key))
        
        self.app.conn.commit()
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = ScantationOfferSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()