import tkinter as tk
from tkinter import messagebox, ttk, font
import datetime
import csv
import os
from tkinter import scrolledtext
import threading
import time

class ModernCaseManager:
    def __init__(self, root):
        self.root = root
        self.root.title("سیستم مدیریت پیشرفته پرونده‌ها")
        self.root.geometry("1400x800")
        
        # Modern color scheme
        self.colors = {
            'primary': '#2c3e50',      # Dark blue-gray
            'secondary': '#34495e',     # Slightly lighter blue-gray
            'accent': '#3498db',         # Bright blue
            'success': '#27ae60',        # Green
            'danger': '#e74c3c',         # Red
            'warning': '#f39c12',         # Orange
            'light': '#ecf0f1',           # Light gray
            'dark': '#2c3e50',            # Dark
            'white': '#ffffff',            # White
            'hover': '#2980b9'             # Darker blue for hover
        }
        
        # Set modern style
        self.setup_styles()
        
        # Initialize data file
        self.FILE_NAME = "پرونده‌ها.csv"
        self.init_file()
        
        # Create UI
        self.create_widgets()
        
        # Load data
        self.refresh_table()
        self.remind_cases()
        
    def setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure treeview style
        style.configure("Treeview",
                        background="#f8f9fa",
                        foreground="#2c3e50",
                        rowheight=30,
                        fieldbackground="#f8f9fa",
                        font=('Segoe UI', 10))
        
        style.configure("Treeview.Heading",
                        background="#34495e",
                        foreground="white",
                        relief="flat",
                        font=('Segoe UI', 11, 'bold'))
        
        style.map("Treeview.Heading",
                  background=[('active', '#2980b9')])
        
        # Configure button style
        style.configure("Modern.TButton",
                        background="#3498db",
                        foreground="white",
                        borderwidth=0,
                        focuscolor="none",
                        font=('Segoe UI', 10))
        
        style.map("Modern.TButton",
                  background=[('active', '#2980b9')])
        
        # Configure label frame
        style.configure("Modern.TLabelframe",
                        background="#ffffff",
                        relief="solid",
                        borderwidth=1)
        
        style.configure("Modern.TLabelframe.Label",
                        background="#ffffff",
                        foreground="#2c3e50",
                        font=('Segoe UI', 11, 'bold'))
        
    def init_file(self):
        """Initialize CSV file if not exists"""
        if not os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["شناسه پرونده", "ضامن", "کد ملی", "شماره تلفن",
                                 "وضعیت", "کد چک", "کد سفته", "یادداشت", 
                                 "کد سفته دو", "کد ملی ضامن", "کد سفته ضامن", 
                                 "تاریخ ثبت", "آخرین ویرایش", "وضعیت پرداخت"])
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with title and stats
        self.create_header(main_container)
        
        # Content area (split into left and right)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Left panel - Input form
        self.create_input_panel(content_frame)
        
        # Right panel - Table and controls
        self.create_table_panel(content_frame)
        
        # Status bar
        self.create_status_bar()
        
    def create_header(self, parent):
        """Create modern header with stats"""
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=100)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Title
        title_label = tk.Label(header_frame, 
                               text="📋 سیستم مدیریت هوشمند پرونده‌ها",
                               font=('Segoe UI', 20, 'bold'),
                               fg='white',
                               bg=self.colors['primary'])
        title_label.pack(side=tk.RIGHT, padx=30, pady=25)
        
        # Stats frame
        stats_frame = tk.Frame(header_frame, bg=self.colors['primary'])
        stats_frame.pack(side=tk.LEFT, padx=30, pady=20)
        
        # Create stats boxes
        self.create_stat_box(stats_frame, "کل پرونده‌ها", "0", 0)
        self.create_stat_box(stats_frame, "پرونده‌های فعال", "0", 1)
        self.create_stat_box(stats_frame, "یادآوری امروز", "0", 2)
        
    def create_stat_box(self, parent, label, value, column):
        """Create statistic box"""
        box = tk.Frame(parent, bg=self.colors['secondary'], 
                      width=150, height=70, relief='flat')
        box.grid(row=0, column=column, padx=10)
        box.pack_propagate(False)
        
        tk.Label(box, text=label, fg=self.colors['light'],
                bg=self.colors['secondary'],
                font=('Segoe UI', 10)).pack(pady=(10, 0))
        
        self.stat_labels = getattr(self, 'stat_labels', {})
        stat_value = tk.Label(box, text=value, fg='white',
                            bg=self.colors['secondary'],
                            font=('Segoe UI', 16, 'bold'))
        stat_value.pack()
        self.stat_labels[label] = stat_value
        
    def create_input_panel(self, parent):
        """Create advanced input panel with tabs"""
        # Left panel frame
        left_panel = ttk.Frame(parent, width=500)
        left_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Notebook for tabs
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Basic Information
        basic_tab = ttk.Frame(notebook, padding=20)
        notebook.add(basic_tab, text="📝 اطلاعات پایه")
        self.create_basic_info_tab(basic_tab)
        
        # Tab 2: Financial Information
        financial_tab = ttk.Frame(notebook, padding=20)
        notebook.add(financial_tab, text="💰 اطلاعات مالی")
        self.create_financial_tab(financial_tab)
        
        # Tab 3: Additional Info
        additional_tab = ttk.Frame(notebook, padding=20)
        notebook.add(additional_tab, text="📎 اطلاعات تکمیلی")
        self.create_additional_tab(additional_tab)
        
        # Button frame
        button_frame = tk.Frame(left_panel, bg=self.colors['white'], height=60)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Modern buttons
        self.create_modern_button(button_frame, "💾 ثبت / ویرایش", 
                                 self.add_or_update_case, 
                                 self.colors['success']).pack(side=tk.RIGHT, padx=5)
        
        self.create_modern_button(button_frame, "🗑️ حذف", 
                                 self.remove_case, 
                                 self.colors['danger']).pack(side=tk.RIGHT, padx=5)
        
        self.create_modern_button(button_frame, "🔄 پاک کردن فرم", 
                                 self.clear_form, 
                                 self.colors['warning']).pack(side=tk.RIGHT, padx=5)
        
    def create_basic_info_tab(self, parent):
        """Create basic information tab"""
        # Create two columns
        left_col = tk.Frame(parent, bg=self.colors['white'])
        left_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        right_col = tk.Frame(parent, bg=self.colors['white'])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Basic fields
        self.basic_fields = {}
        basic_labels = [
            ("شناسه پرونده", "📋"),
            ("ضامن", "👤"),
            ("کد ملی", "🆔"),
            ("شماره تلفن", "📞"),
            ("وضعیت", "⚡"),
        ]
        
        for i, (label, icon) in enumerate(basic_labels):
            self.create_modern_entry(left_col, label, icon, i)
        
        # Status combobox
        status_values = ["فعال", "غیرفعال", "در انتظار", "تکمیل شده", "معلق"]
        self.create_modern_combobox(right_col, "وضعیت پرونده", "📊", 0, status_values)
        
        # Date picker (simplified)
        self.create_modern_date_picker(right_col, "تاریخ ثبت", "📅", 1)
        
    def create_financial_tab(self, parent):
        """Create financial information tab"""
        fields = [
            ("کد چک", "💰", 0),
            ("کد سفته", "📄", 1),
            ("کد سفته دو", "📄", 2),
            ("مبلغ (ریال)", "💵", 3),
            ("تعداد اقساط", "🔢", 4),
        ]
        
        for label, icon, row in fields:
            self.create_modern_entry(parent, label, icon, row)
        
        # Payment status
        payment_status = ["پرداخت شده", "پرداخت نشده", "پرداخت جزئی", "تاخیر"]
        self.create_modern_combobox(parent, "وضعیت پرداخت", "💳", 5, payment_status)
        
    def create_additional_tab(self, parent):
        """Create additional information tab"""
        fields = [
            ("کد ملی ضامن", "🆔", 0),
            ("کد سفته ضامن", "📄", 1),
        ]
        
        for label, icon, row in fields:
            self.create_modern_entry(parent, label, icon, row)
        
        # Notes
        tk.Label(parent, text="📝 یادداشت‌ها", 
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['white'],
                fg=self.colors['primary']).grid(row=2, column=0, sticky='w', pady=(20, 5))
        
        self.notes_text = scrolledtext.ScrolledText(parent, 
                                                    height=8,
                                                    width=40,
                                                    font=('Segoe UI', 10),
                                                    wrap=tk.WORD,
                                                    relief='solid',
                                                    borderwidth=1)
        self.notes_text.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=(0, 10))
        
    def create_modern_entry(self, parent, label, icon, row):
        """Create a modern entry field"""
        frame = tk.Frame(parent, bg=self.colors['white'])
        frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=5)
        
        # Label with icon
        label_widget = tk.Label(frame, text=f"{icon} {label}:", 
                               font=('Segoe UI', 10),
                               bg=self.colors['white'],
                               fg=self.colors['primary'],
                               width=15, anchor='w')
        label_widget.pack(side=tk.RIGHT)
        
        # Entry
        entry = tk.Entry(frame, font=('Segoe UI', 10),
                        relief='solid', borderwidth=1,
                        highlightthickness=1,
                        highlightcolor=self.colors['accent'],
                        highlightbackground='#ddd')
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Store reference
        if not hasattr(self, 'entries'):
            self.entries = {}
        self.entries[label] = entry
        
        return entry
        
    def create_modern_combobox(self, parent, label, icon, row, values):
        """Create a modern combobox"""
        frame = tk.Frame(parent, bg=self.colors['white'])
        frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=5)
        
        tk.Label(frame, text=f"{icon} {label}:",
                font=('Segoe UI', 10),
                bg=self.colors['white'],
                fg=self.colors['primary'],
                width=15, anchor='w').pack(side=tk.RIGHT)
        
        combo = ttk.Combobox(frame, values=values, font=('Segoe UI', 10))
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        if not hasattr(self, 'combos'):
            self.combos = {}
        self.combos[label] = combo
        
    def create_modern_date_picker(self, parent, label, icon, row):
        """Create a modern date picker"""
        frame = tk.Frame(parent, bg=self.colors['white'])
        frame.grid(row=row, column=0, columnspan=2, sticky='ew', pady=5)
        
        tk.Label(frame, text=f"{icon} {label}:",
                font=('Segoe UI', 10),
                bg=self.colors['white'],
                fg=self.colors['primary'],
                width=15, anchor='w').pack(side=tk.RIGHT)
        
        date_entry = tk.Entry(frame, font=('Segoe UI', 10),
                            relief='solid', borderwidth=1)
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Insert current date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        date_entry.insert(0, current_date)
        
        if not hasattr(self, 'date_entries'):
            self.date_entries = {}
        self.date_entries[label] = date_entry
        
    def create_modern_button(self, parent, text, command, color):
        """Create a modern button with hover effect"""
        btn = tk.Button(parent, text=text, command=command,
                       font=('Segoe UI', 10, 'bold'),
                       bg=color, fg='white',
                       relief='flat', padx=20, pady=8,
                       cursor='hand2')
        
        # Hover effect
        btn.bind("<Enter>", lambda e: btn.config(bg=self.colors['hover']))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        
        return btn
        
    def create_table_panel(self, parent):
        """Create advanced table panel with search and filters"""
        right_panel = ttk.Frame(parent)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Search and filter bar
        search_frame = tk.Frame(right_panel, bg=self.colors['white'], height=60)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        search_frame.pack_propagate(False)
        
        # Search entry
        tk.Label(search_frame, text="🔍 جستجو:",
                font=('Segoe UI', 10),
                bg=self.colors['white'],
                fg=self.colors['primary']).pack(side=tk.RIGHT, padx=(5, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_table())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('Segoe UI', 11),
                               relief='solid', borderwidth=1,
                               width=30)
        search_entry.pack(side=tk.RIGHT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_table())
        
        # Filter combobox
        tk.Label(search_frame, text="📊 فیلتر وضعیت:",
                font=('Segoe UI', 10),
                bg=self.colors['white'],
                fg=self.colors['primary']).pack(side=tk.RIGHT, padx=(20, 5))
        
        self.filter_var = tk.StringVar(value="همه")
        filter_combo = ttk.Combobox(search_frame, 
                                   textvariable=self.filter_var,
                                   values=["همه", "فعال", "غیرفعال", "در انتظار", "تکمیل شده"],
                                   font=('Segoe UI', 10),
                                   width=15)
        filter_combo.pack(side=tk.RIGHT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_table())
        
        # Export button
        self.create_modern_button(search_frame, "📥 خروجی اکسل", 
                                self.export_to_excel, 
                                self.colors['accent']).pack(side=tk.LEFT, padx=10)
        
        # Table frame
        table_frame = ttk.Frame(right_panel)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbars
        self.create_modern_table(table_frame)
        
    def create_modern_table(self, parent):
        """Create a modern treeview table"""
        # Scrollbars
        vsb = ttk.Scrollbar(parent)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Columns
        columns = ["شناسه پرونده", "ضامن", "کد ملی", "شماره تلفن", 
                   "وضعیت", "کد چک", "کد سفته", "تاریخ ثبت", "وضعیت پرداخت"]
        
        self.tree = ttk.Treeview(parent, columns=columns, show="headings",
                                 yscrollcommand=vsb.set,
                                 xscrollcommand=hsb.set,
                                 height=20)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure columns
        column_widths = [120, 150, 120, 120, 100, 120, 120, 120, 120]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        # Tags for row colors
        self.tree.tag_configure('active', background='#d4edda')
        self.tree.tag_configure('inactive', background='#f8d7da')
        self.tree.tag_configure('pending', background='#fff3cd')
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Double click event
        self.tree.bind('<Double-Button-1>', self.on_tree_double_click)
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_bar = tk.Frame(self.root, bg=self.colors['secondary'], height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        self.status_label = tk.Label(status_bar, 
                                     text="✅ آماده به کار",
                                     bg=self.colors['secondary'],
                                     fg='white',
                                     font=('Segoe UI', 9))
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=5)
        
        # Time label
        self.time_label = tk.Label(status_bar,
                                   text=datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                                   bg=self.colors['secondary'],
                                   fg='white',
                                   font=('Segoe UI', 9))
        self.time_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        # Update time every second
        self.update_time()
        
    def update_time(self):
        """Update time in status bar"""
        current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def load_cases(self):
        """Load cases from CSV"""
        cases = {}
        try:
            with open(self.FILE_NAME, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cases[row["شناسه پرونده"]] = row
        except:
            pass
        return cases
        
    def save_cases(self, cases):
        """Save cases to CSV"""
        with open(self.FILE_NAME, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["شناسه پرونده", "ضامن", "کد ملی", "شماره تلفن",
                         "وضعیت", "کد چک", "کد سفته", "یادداشت", 
                         "کد سفته دو", "کد ملی ضامن", "کد سفته ضامن", 
                         "تاریخ ثبت", "آخرین ویرایش", "وضعیت پرداخت"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for case in cases.values():
                writer.writerow(case)
                
    def add_or_update_case(self):
        """Add or update a case"""
        case_id = self.entries["شناسه پرونده"].get().strip()
        
        if not case_id:
            messagebox.showerror("خطا", "شناسه پرونده الزامی است")
            return
            
        cases = self.load_cases()
        
        # Collect data from all fields
        case_data = {
            "شناسه پرونده": case_id,
            "ضامن": self.entries["ضامن"].get().strip(),
            "کد ملی": self.entries["کد ملی"].get().strip(),
            "شماره تلفن": self.entries["شماره تلفن"].get().strip(),
            "وضعیت": self.combos.get("وضعیت پرونده", ttk.Combobox()).get() if hasattr(self, 'combos') else "",
            "کد چک": self.entries.get("کد چک", tk.Entry()).get().strip() if hasattr(self, 'entries') else "",
            "کد سفته": self.entries.get("کد سفته", tk.Entry()).get().strip() if hasattr(self, 'entries') else "",
            "یادداشت": self.notes_text.get("1.0", tk.END).strip() if hasattr(self, 'notes_text') else "",
            "کد سفته دو": self.entries.get("کد سفته دو", tk.Entry()).get().strip() if hasattr(self, 'entries') else "",
            "کد ملی ضامن": self.entries.get("کد ملی ضامن", tk.Entry()).get().strip() if hasattr(self, 'entries') else "",
            "کد سفته ضامن": self.entries.get("کد سفته ضامن", tk.Entry()).get().strip() if hasattr(self, 'entries') else "",
            "تاریخ ثبت": self.date_entries.get("تاریخ ثبت", tk.Entry()).get() if hasattr(self, 'date_entries') else datetime.datetime.now().strftime("%Y-%m-%d"),
            "آخرین ویرایش": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "وضعیت پرداخت": self.combos.get("وضعیت پرداخت", ttk.Combobox()).get() if hasattr(self, 'combos') else "",
        }
        
        cases[case_id] = case_data
        self.save_cases(cases)
        
        messagebox.showinfo("موفق", f"پرونده {case_id} با موفقیت ثبت شد.")
        self.refresh_table()
        self.update_status(f"پرونده {case_id} ثبت شد")
        
    def remove_case(self):
        """Remove a case"""
        case_id = self.entries["شناسه پرونده"].get().strip()
        
        if not case_id:
            messagebox.showerror("خطا", "لطفاً شناسه پرونده را وارد کنید")
            return
            
        if messagebox.askyesno("تأیید حذف", f"آیا از حذف پرونده {case_id} اطمینان دارید؟"):
            cases = self.load_cases()
            if case_id in cases:
                del cases[case_id]
                self.save_cases(cases)
                messagebox.showinfo("حذف شد", f"پرونده {case_id} حذف شد.")
                self.clear_form()
                self.refresh_table()
                self.update_status(f"پرونده {case_id} حذف شد")
            else:
                messagebox.showwarning("یافت نشد", "پرونده موجود نیست.")
                
    def clear_form(self):
        """Clear all input fields"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
            
        if hasattr(self, 'combos'):
            for combo in self.combos.values():
                combo.set('')
                
        if hasattr(self, 'notes_text'):
            self.notes_text.delete("1.0", tk.END)
            
        if hasattr(self, 'date_entries'):
            for date_entry in self.date_entries.values():
                date_entry.delete(0, tk.END)
                date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
                
        self.update_status("فرم پاک شد")
        
    def refresh_table(self):
        """Refresh the table with latest data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Load and display cases
        cases = self.load_cases()
        
        # Update stats
        self.update_stats(cases)
        
        # Add to table
        for case in cases.values():
            # Determine tag based on status
            status = case.get("وضعیت", "")
            if status == "فعال":
                tag = 'active'
            elif status == "غیرفعال":
                tag = 'inactive'
            elif status == "در انتظار":
                tag = 'pending'
            else:
                tag = ''
                
            self.tree.insert("", "end", values=(
                case.get("شناسه پرونده", ""),
                case.get("ضامن", ""),
                case.get("کد ملی", ""),
                case.get("شماره تلفن", ""),
                status,
                case.get("کد چک", ""),
                case.get("کد سفته", ""),
                case.get("تاریخ ثبت", ""),
                case.get("وضعیت پرداخت", "")
            ), tags=(tag,))
            
    def update_stats(self, cases):
        """Update statistics"""
        total = len(cases)
        active = sum(1 for c in cases.values() if c.get("وضعیت") == "فعال")
        
        # Count reminders for today
        now = datetime.datetime.now()
        reminders = 0
        for case in cases.values():
            try:
                created = datetime.datetime.strptime(case.get("تاریخ ثبت", ""), "%Y-%m-%d")
                if (now - created).days >= 3:
                    reminders += 1
            except:
                pass
                
        # Update stat labels
        if hasattr(self, 'stat_labels'):
            if "کل پرونده‌ها" in self.stat_labels:
                self.stat_labels["کل پرونده‌ها"].config(text=str(total))
            if "پرونده‌های فعال" in self.stat_labels:
                self.stat_labels["پرونده‌های فعال"].config(text=str(active))
            if "یادآوری امروز" in self.stat_labels:
                self.stat_labels["یادآوری امروز"].config(text=str(reminders))
                
    def filter_table(self):
        """Filter table based on search and filter criteria"""
        search_term = self.search_var.get().lower()
        filter_status = self.filter_var.get()
        
        # Clear table
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Load and filter cases
        cases = self.load_cases()
        
        for case in cases.values():
            # Apply filters
            if filter_status != "همه" and case.get("وضعیت") != filter_status:
                continue
                
            if search_term:
                searchable_fields = [
                    case.get("شناسه پرونده", "").lower(),
                    case.get("ضامن", "").lower(),
                    case.get("کد ملی", ""),
                    case.get("شماره تلفن", "")
                ]
                if not any(search_term in field for field in searchable_fields):
                    continue
                    
            # Add to table
            status = case.get("وضعیت", "")
            if status == "فعال":
                tag = 'active'
            elif status == "غیرفعال":
                tag = 'inactive'
            elif status == "در انتظار":
                tag = 'pending'
            else:
                tag = ''
                
            self.tree.insert("", "end", values=(
                case.get("شناسه پرونده", ""),
                case.get("ضامن", ""),
                case.get("کد ملی", ""),
                case.get("شماره تلفن", ""),
                status,
                case.get("کد چک", ""),
                case.get("کد سفته", ""),
                case.get("تاریخ ثبت", ""),
                case.get("وضعیت پرداخت", "")
            ), tags=(tag,))
            
    def on_tree_double_click(self, event):
        """Handle double click on tree item"""
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected[0])
        values = item['values']
        
        if values:
            self.clear_form()
            
            # Load data into form
            if "شناسه پرونده" in self.entries:
                self.entries["شناسه پرونده"].insert(0, values[0])
            if "ضامن" in self.entries:
                self.entries["ضامن"].insert(0, values[1])
            if "کد ملی" in self.entries:
                self.entries["کد ملی"].insert(0, values[2])
            if "شماره تلفن" in self.entries:
                self.entries["شماره تلفن"].insert(0, values[3])
                
            if hasattr(self, 'combos') and "وضعیت پرونده" in self.combos:
                self.combos["وضعیت پرونده"].set(values[4])
                
            if "کد چک" in self.entries:
                self.entries["کد چک"].insert(0, values[5])
            if "کد سفته" in self.entries:
                self.entries["کد سفته"].insert(0, values[6])
                
            if hasattr(self, 'date_entries') and "تاریخ ثبت" in self.date_entries:
                self.date_entries["تاریخ ثبت"].delete(0, tk.END)
                self.date_entries["تاریخ ثبت"].insert(0, values[7])
                
            if hasattr(self, 'combos') and "وضعیت پرداخت" in self.combos and len(values) > 8:
                self.combos["وضعیت پرداخت"].set(values[8])
                
            self.update_status(f"پرونده {values[0]} بارگذاری شد")
            
    def remind_cases(self):
        """Check for cases needing reminder"""
        cases = self.load_cases()
        now = datetime.datetime.now()
        reminders = []
        
        for case in cases.values():
            try:
                created = datetime.datetime.strptime(case.get("تاریخ ثبت", ""), "%Y-%m-%d")
                days_passed = (now - created).days
                if days_passed >= 3 and days_passed % 3 == 0:  # Remind every 3 days
                    reminders.append(f"📞 تماس با {case['ضامن']} - {case['شماره تلفن']}")
            except:
                pass
                
        if reminders:
            # Show notification in status bar
            self.update_status(f"⚠️ {len(reminders)} یادآوری فعال")
            
            # Show popup for first 5 reminders
            if len(reminders) > 0:
                messagebox.showinfo("یادآوری‌ها", "\n".join(reminders[:5]) + 
                                   ("\n..." if len(reminders) > 5 else ""))
                
    def export_to_excel(self):
        """Export data to Excel format (CSV)"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"گزارش_پرونده‌ها_{timestamp}.csv"
            
            cases = self.load_cases()
            
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                if cases:
                    writer = csv.DictWriter(f, fieldnames=list(next(iter(cases.values())).keys()))
                    writer.writeheader()
                    writer.writerows(cases.values())
                    
            messagebox.showinfo("موفق", f"گزارش با نام {filename} ذخیره شد.")
            self.update_status(f"گزارش ذخیره شد: {filename}")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره گزارش: {str(e)}")
            
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=f"✅ {message}")

def main():
    root = tk.Tk()
    
    # Set window icon (if you have one)
    # root.iconbitmap('icon.ico')
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{1400}x{800}+{x}+{y}')
    
    # Make window resizable
    root.resizable(True, True)
    
    app = ModernCaseManager(root)
    
    # Bind keyboard shortcuts
    root.bind('<Control-s>', lambda e: app.add_or_update_case())
    root.bind('<Control-d>', lambda e: app.remove_case())
    root.bind('<Control-f>', lambda e: app.search_var.set(''))
    root.bind('<Escape>', lambda e: app.clear_form())
    
    root.mainloop()

if __name__ == "__main__":
    main()