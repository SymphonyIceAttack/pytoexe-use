import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import csv
import os
from datetime import datetime

class InventoryManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("进销存管理系统 v1.0")
        self.root.geometry("1200x700")
        
        # 设置窗口图标
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # 连接数据库
        self.conn = sqlite3.connect('inventory.db')
        self.cursor = self.conn.cursor()
        
        # 创建数据表
        self.create_tables()
        
        # 设置样式
        self.setup_styles()
        
        # 创建主界面
        self.create_main_interface()
        
        # 加载初始数据
        self.load_products()
        self.load_suppliers()
        self.load_customers()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置标签页样式
        style.configure('TNotebook.Tab', padding=[10, 5])
        
        # 配置按钮样式
        style.configure('Primary.TButton', foreground='white', background='#007bff')
        style.map('Primary.TButton', background=[('active', '#0056b3')])
        
        style.configure('Success.TButton', foreground='white', background='#28a745')
        style.map('Success.TButton', background=[('active', '#1e7e34')])
        
        style.configure('Danger.TButton', foreground='white', background='#dc3545')
        style.map('Danger.TButton', background=[('active', '#bd2130')])
    
    def create_tables(self):
        """创建数据库表"""
        # 产品表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                unit TEXT,
                purchase_price REAL,
                sale_price REAL,
                stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                supplier_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 供应商表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                address TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 客户表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                address TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 入库记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                supplier_id INTEGER,
                purchase_date DATE NOT NULL,
                operator TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        
        # 出库记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                customer_id INTEGER,
                sale_date DATE NOT NULL,
                operator TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # 库存变动记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                change_quantity INTEGER NOT NULL,
                previous_stock INTEGER NOT NULL,
                current_stock INTEGER NOT NULL,
                related_order TEXT,
                operator TEXT,
                change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        self.conn.commit()
    
    def create_main_interface(self):
        """创建主界面"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题栏
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame, 
            text="进销存管理系统", 
            font=("微软雅黑", 24, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT)
        
        # 当前时间标签
        self.time_label = tk.Label(
            title_frame,
            text="",
            font=("微软雅黑", 10),
            fg="#7f8c8d"
        )
        self.time_label.pack(side=tk.RIGHT)
        self.update_time()
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个功能标签页
        self.create_dashboard_tab()
        self.create_product_tab()
        self.create_purchase_tab()
        self.create_sale_tab()
        self.create_inventory_tab()
        self.create_report_tab()
        
        # 状态栏
        self.status_bar = tk.Label(
            self.root, 
            text="就绪", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def create_dashboard_tab(self):
        """创建仪表盘标签页"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="仪表盘")
        
        # 创建统计卡片容器
        stats_frame = ttk.Frame(dashboard_frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 统计卡片数据
        stats_data = [
            {"title": "产品总数", "value": "0", "color": "#3498db", "icon": "📦"},
            {"title": "总库存量", "value": "0", "color": "#2ecc71", "icon": "📊"},
            {"title": "低库存产品", "value": "0", "color": "#e74c3c", "icon": "⚠️"},
            {"title": "本月销售额", "value": "¥0", "color": "#9b59b6", "icon": "💰"},
        ]
        
        self.stat_cards = []
        
        for i, stat in enumerate(stats_data):
            card = tk.Frame(stats_frame, bg=stat["color"], relief=tk.RAISED, bd=2)
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            
            # 图标
            icon_label = tk.Label(card, text=stat["icon"], font=("Arial", 24), bg=stat["color"])
            icon_label.pack(side=tk.LEFT, padx=10, pady=10)
            
            # 数值和标题
            content_frame = tk.Frame(card, bg=stat["color"])
            content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
            
            value_label = tk.Label(
                content_frame, 
                text=stat["value"], 
                font=("微软雅黑", 18, "bold"), 
                bg=stat["color"], 
                fg="white"
            )
            value_label.pack(anchor="w")
            
            title_label = tk.Label(
                content_frame, 
                text=stat["title"], 
                font=("微软雅黑", 10), 
                bg=stat["color"], 
                fg="white"
            )
            title_label.pack(anchor="w")
            
            self.stat_cards.append({"frame": card, "value_label": value_label})
        
        # 快速操作区域
        quick_actions_frame = ttk.LabelFrame(dashboard_frame, text="快速操作", padding=10)
        quick_actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 快速操作按钮
        quick_actions = [
            ("📦 新增产品", self.show_product_tab),
            ("🛒 采购入库", self.show_purchase_tab),
            ("💰 销售出库", self.show_sale_tab),
            ("📊 查看库存", self.show_inventory_tab),
            ("📈 生成报表", self.show_report_tab),
            ("📤 导出数据", self.export_data),
        ]
        
        for i, (text, command) in enumerate(quick_actions):
            btn = ttk.Button(
                quick_actions_frame, 
                text=text, 
                command=command,
                style='Primary.TButton'
            )
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
            quick_actions_frame.columnconfigure(i%3, weight=1)
        
        # 最近操作记录
        recent_frame = ttk.LabelFrame(dashboard_frame, text="最近操作记录", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建表格显示最近操作
        columns = ("时间", "类型", "产品", "数量", "操作员", "备注")
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 更新仪表盘数据
        self.update_dashboard_stats()
        self.load_recent_operations()
    
    def create_product_tab(self):
        """创建产品管理标签页"""
        product_frame = ttk.Frame(self.notebook)
        self.notebook.add(product_frame, text="产品管理")
        
        # 左侧：产品列表
        list_frame = ttk.Frame(product_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=10)
        
        # 搜索框
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.product_search_var = tk.StringVar()
        self.product_search_var.trace("w", self.search_products)
        search_entry = ttk.Entry(search_frame, textvariable=self.product_search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 产品表格
        columns = ("ID", "编码", "名称", "分类", "单位", "进货价", "销售价", "库存", "最低库存", "供应商")
        self.product_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.product_tree.heading(col, text=col)
            self.product_tree.column(col, width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.product_tree.bind('<<TreeviewSelect>>', self.on_product_select)
        
        # 右侧：产品表单
        form_frame = ttk.LabelFrame(product_frame, text="产品信息", padding=10)
        form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0), pady=10, ipadx=5, ipady=5)
        
        # 表单字段
        fields = [
            ("产品编码:", "product_code"),
            ("产品名称:", "product_name"),
            ("产品分类:", "product_category"),
            ("单位:", "product_unit"),
            ("进货价:", "product_purchase_price"),
            ("销售价:", "product_sale_price"),
            ("库存:", "product_stock"),
            ("最低库存:", "product_min_stock"),
            ("供应商:", "product_supplier")
        ]
        
        self.product_form_vars = {}
        
        for i, (label, field) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            if field == "product_supplier":
                # 供应商下拉框
                self.product_supplier_var = tk.StringVar()
                self.supplier_combo = ttk.Combobox(form_frame, textvariable=self.product_supplier_var, width=20)
                self.supplier_combo.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                self.product_form_vars[field] = var
        
        # 按钮区域
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame, 
            text="新增", 
            command=self.add_product,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="修改", 
            command=self.update_product,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="删除", 
            command=self.delete_product,
            style='Danger.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="清空", 
            command=self.clear_product_form
        ).pack(side=tk.LEFT, padx=5)
    
    def create_purchase_tab(self):
        """创建采购管理标签页"""
        purchase_frame = ttk.Frame(self.notebook)
        self.notebook.add(purchase_frame, text="采购入库")
        
        # 采购表单
        form_frame = ttk.LabelFrame(purchase_frame, text="采购信息", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 表单字段
        fields = [
            ("采购单号:", "purchase_order_no"),
            ("产品:", "purchase_product"),
            ("数量:", "purchase_quantity"),
            ("单价:", "purchase_unit_price"),
            ("供应商:", "purchase_supplier"),
            ("采购日期:", "purchase_date"),
            ("操作员:", "purchase_operator"),
            ("备注:", "purchase_remarks")
        ]
        
        self.purchase_form_vars = {}
        
        for i, (label, field) in enumerate(fields[:4]):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            if field == "purchase_product":
                self.purchase_product_var = tk.StringVar()
                self.purchase_product_combo = ttk.Combobox(form_frame, textvariable=self.purchase_product_var, width=25)
                self.purchase_product_combo.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                self.purchase_form_vars[field] = var
        
        for i, (label, field) in enumerate(fields[4:]):
            ttk.Label(form_frame, text=label).grid(row=i, column=2, sticky="e", padx=5, pady=5)
            
            if field == "purchase_supplier":
                self.purchase_supplier_var = tk.StringVar()
                self.purchase_supplier_combo = ttk.Combobox(form_frame, textvariable=self.purchase_supplier_var, width=25)
                self.purchase_supplier_combo.grid(row=i, column=3, padx=5, pady=5, sticky="w")
            elif field == "purchase_date":
                var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=3, padx=5, pady=5, sticky="w")
                self.purchase_form_vars[field] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=3, padx=5, pady=5, sticky="w")
                self.purchase_form_vars[field] = var
        
        # 总金额显示
        ttk.Label(form_frame, text="总金额:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.purchase_total_var = tk.StringVar(value="0.00")
        total_label = ttk.Label(form_frame, textvariable=self.purchase_total_var, font=("微软雅黑", 12, "bold"))
        total_label.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=10)
        
        ttk.Button(
            button_frame, 
            text="计算总价", 
            command=self.calculate_purchase_total,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="提交采购", 
            command=self.submit_purchase,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="清空表单", 
            command=self.clear_purchase_form
        ).pack(side=tk.LEFT, padx=5)
        
        # 采购记录表格
        record_frame = ttk.LabelFrame(purchase_frame, text="采购记录", padding=10)
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("采购单号", "产品", "数量", "单价", "总金额", "供应商", "日期", "操作员")
        self.purchase_tree = ttk.Treeview(record_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.purchase_tree.heading(col, text=col)
            self.purchase_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(record_frame, orient="vertical", command=self.purchase_tree.yview)
        self.purchase_tree.configure(yscrollcommand=scrollbar.set)
        
        self.purchase_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载采购记录
        self.load_purchase_records()
    
    def create_sale_tab(self):
        """创建销售管理标签页"""
        sale_frame = ttk.Frame(self.notebook)
        self.notebook.add(sale_frame, text="销售出库")
        
        # 销售表单
        form_frame = ttk.LabelFrame(sale_frame, text="销售信息", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 表单字段
        fields = [
            ("销售单号:", "sale_order_no"),
            ("产品:", "sale_product"),
            ("数量:", "sale_quantity"),
            ("单价:", "sale_unit_price"),
            ("客户:", "sale_customer"),
            ("销售日期:", "sale_date"),
            ("操作员:", "sale_operator"),
            ("备注:", "sale_remarks")
        ]
        
        self.sale_form_vars = {}
        
        for i, (label, field) in enumerate(fields[:4]):
            ttk.Label(form_frame, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=5)
            
            if field == "sale_product":
                self.sale_product_var = tk.StringVar()
                self.sale_product_combo = ttk.Combobox(form_frame, textvariable=self.sale_product_var, width=25)
                self.sale_product_combo.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
                self.sale_form_vars[field] = var
        
        for i, (label, field) in enumerate(fields[4:]):
            ttk.Label(form_frame, text=label).grid(row=i, column=2, sticky="e", padx=5, pady=5)
            
            if field == "sale_customer":
                self.sale_customer_var = tk.StringVar()
                self.sale_customer_combo = ttk.Combobox(form_frame, textvariable=self.sale_customer_var, width=25)
                self.sale_customer_combo.grid(row=i, column=3, padx=5, pady=5, sticky="w")
            elif field == "sale_date":
                var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=3, padx=5, pady=5, sticky="w")
                self.sale_form_vars[field] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var, width=25)
                entry.grid(row=i, column=3, padx=5, pady=5, sticky="w")
                self.sale_form_vars[field] = var
        
        # 总金额显示
        ttk.Label(form_frame, text="总金额:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.sale_total_var = tk.StringVar(value="0.00")
        total_label = ttk.Label(form_frame, textvariable=self.sale_total_var, font=("微软雅黑", 12, "bold"))
        total_label.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # 库存检查
        self.stock_check_var = tk.StringVar()
        stock_label = ttk.Label(form_frame, textvariable=self.stock_check_var, foreground="red")
        stock_label.grid(row=4, column=2, columnspan=2, sticky="w", padx=5, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=10)
        
        ttk.Button(
            button_frame, 
            text="计算总价", 
            command=self.calculate_sale_total,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="检查库存", 
            command=self.check_stock,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="提交销售", 
            command=self.submit_sale,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="清空表单", 
            command=self.clear_sale_form
        ).pack(side=tk.LEFT, padx=5)
        
        # 销售记录表格
        record_frame = ttk.LabelFrame(sale_frame, text="销售记录", padding=10)
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("销售单号", "产品", "数量", "单价", "总金额", "客户", "日期", "操作员")
        self.sale_tree = ttk.Treeview(record_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.sale_tree.heading(col, text=col)
            self.sale_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(record_frame, orient="vertical", command=self.sale_tree.yview)
        self.sale_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sale_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载销售记录
        self.load_sale_records()
    
    def create_inventory_tab(self):
        """创建库存管理标签页"""
        inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(inventory_frame, text="库存管理")
        
        # 搜索和过滤区域
        filter_frame = ttk.Frame(inventory_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(filter_frame, text="分类筛选:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter_var = tk.StringVar()
        category_combo = ttk.Combobox(filter_frame, textvariable=self.category_filter_var, width=15)
        category_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(filter_frame, text="库存状态:").pack(side=tk.LEFT, padx=(0, 5))
        self.stock_status_var = tk.StringVar()
        status_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.stock_status_var, 
            values=["全部", "正常", "不足", "缺货"],
            width=10
        )
        status_combo.pack(side=tk.LEFT, padx=(0, 20))
        status_combo.set("全部")
        
        ttk.Button(
            filter_frame, 
            text="筛选", 
            command=self.filter_inventory,
            style='Primary.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            filter_frame, 
            text="导出库存", 
            command=self.export_inventory,
            style='Success.TButton'
        ).pack(side=tk.LEFT, padx=5)
        
        # 库存表格
        tree_frame = ttk.Frame(inventory_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("ID", "产品编码", "产品名称", "分类", "单位", "当前库存", "最低库存", "状态", "最近变动")
        self.inventory_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 库存统计
        stats_frame = ttk.LabelFrame(inventory_frame, text="库存统计", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.inventory_stats_vars = {
            "total_products": tk.StringVar(value="0"),
            "total_stock": tk.StringVar(value="0"),
            "low_stock": tk.StringVar(value="0"),
            "out_of_stock": tk.StringVar(value="0"),
        }
        
        for i, (label, key) in enumerate([
            ("产品总数:", "total_products"),
            ("总库存量:", "total_stock"),
            ("库存不足:", "low_stock"),
            ("缺货产品:", "out_of_stock"),
        ]):
            ttk.Label(stats_frame, text=label).grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, textvariable=self.inventory_stats_vars[key], 
                     font=("微软雅黑", 10, "bold")).grid(row=0, column=i*2+1, padx=(0, 20), pady=5, sticky="w")
        
        # 加载库存数据
        self.load_inventory()
    
    def create_report_tab(self):
        """创建报表标签页"""
        report_frame = ttk.Frame(self.notebook)
        self.notebook.add(report_frame, text="报表分析")
        
        # 报表选项
        option_frame = ttk.LabelFrame(report_frame, text="报表选项", padding=10)
        option_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(option_frame, text="报表类型:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.report_type_var = tk.StringVar(value="sales")
        report_combo = ttk.Combobox(
            option_frame, 
            textvariable=self.report_type_var, 
            values=["销售报表", "采购报表", "库存报表", "利润分析"],
            width=15
        )
        report_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(option_frame, text="时间范围:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.report_period_var = tk.StringVar(value="month")
        period_combo = ttk.Combobox(
            option_frame, 
            textvariable=self.report_period_var, 
            values=["今天", "本周", "本月", "本年", "自定义"],
            width=10
        )
        period_combo.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        ttk.Label(option_frame, text="开始日期:").grid(row=0, column=4, sticky="e", padx=5, pady=5)
        self.report_start_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        ttk.Entry(option_frame, textvariable=self.report_start_var, width=12).grid(row=0, column=5, sticky="w", padx=5, pady=5)
        
        ttk.Label(option_frame, text="结束日期:").grid(row=0, column=6, sticky="e", padx=5, pady=5)
        self.report_end_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(option_frame, textvariable=self.report_end_var, width=12).grid(row=0, column=7, sticky="w", padx=5, pady=5)
        
        ttk.Button(
            option_frame, 
            text="生成报表", 
            command=self.generate_report,
            style='Primary.TButton'
        ).grid(row=0, column=8, padx=10, pady=5)
        
        ttk.Button(
            option_frame, 
            text="导出报表", 
            command=self.export_report,
            style='Success.TButton'
        ).grid(row=0, column=9, padx=5, pady=5)
        
        # 报表显示区域
        display_frame = ttk.Frame(report_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 报表表格
        columns = ("项目", "数值", "占比", "趋势")
        self.report_tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scrollbar.set)
        
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 统计摘要
        summary_frame = ttk.LabelFrame(report_frame, text="统计摘要", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.summary_vars = {}
        summary_labels = [
            ("总销售额:", "total_sales"),
            ("总采购额:", "total_purchase"),
            ("总利润:", "total_profit"),
            ("毛利率:", "profit_margin"),
            ("最畅销产品:", "top_product"),
            ("库存周转率:", "turnover_rate"),
        ]
        
        for i, (label, key) in enumerate(summary_labels):
            ttk.Label(summary_frame, text=label).grid(row=i//3, column=(i%3)*2, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value="--")
            ttk.Label(summary_frame, textvariable=var, font=("微软雅黑", 10, "bold")).grid(
                row=i//3, column=(i%3)*2+1, padx=(0, 20), pady=5, sticky="w"
            )
            self.summary_vars[key] = var
    
    # 数据操作方法
    def load_products(self):
        """加载产品数据"""
        self.cursor.execute("SELECT * FROM products")
        products = self.cursor.fetchall()
        
        # 清空表格
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # 填充数据
        for product in products:
            # 获取供应商名称
            supplier_name = ""
            if product[9]:  # supplier_id
                self.cursor.execute("SELECT name FROM suppliers WHERE id = ?", (product[9],))
                supplier_result = self.cursor.fetchone()
                if supplier_result:
                    supplier_name = supplier_result[0]
            
            self.product_tree.insert("", "end", values=product[:10] + (supplier_name,))
        
        # 更新下拉框
        product_names = [f"{p[1]} - {p[2]}" for p in products]
        self.purchase_product_combo['values'] = product_names
        self.sale_product_combo['values'] = product_names
        
        # 更新分类筛选
        categories = list(set([p[3] for p in products if p[3]]))
        self.category_filter_var.set("")
        # 这里需要找到分类下拉框并更新值
    
    def load_suppliers(self):
        """加载供应商数据"""
        self.cursor.execute("SELECT id, name FROM suppliers")
        suppliers = self.cursor.fetchall()
        
        supplier_names = [s[1] for s in suppliers]
        self.supplier_combo['values'] = supplier_names
        self.purchase_supplier_combo['values'] = supplier_names
    
    def load_customers(self):
        """加载客户数据"""
        self.cursor.execute("SELECT id, name FROM customers")
        customers = self.cursor.fetchall()
        
        customer_names = [c[1] for c in customers]
        self.sale_customer_combo['values'] = customer_names
    
    def load_purchase_records(self):
        """加载采购记录"""
        self.cursor.execute('''
            SELECT pr.order_no, p.name, pr.quantity, pr.unit_price, pr.total_amount,
                   s.name, pr.purchase_date, pr.operator
            FROM purchase_records pr
            JOIN products p ON pr.product_id = p.id
            LEFT JOIN suppliers s ON pr.supplier_id = s.id
            ORDER BY pr.purchase_date DESC
            LIMIT 100
        ''')
        records = self.cursor.fetchall()
        
        # 清空表格
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)
        
        # 填充数据
        for record in records:
            self.purchase_tree.insert("", "end", values=record)
    
    def load_sale_records(self):
        """加载销售记录"""
        self.cursor.execute('''
            SELECT sr.order_no, p.name, sr.quantity, sr.unit_price, sr.total_amount,
                   c.name, sr.sale_date, sr.operator
            FROM sale_records sr
            JOIN products p ON sr.product_id = p.id
            LEFT JOIN customers c ON sr.customer_id = c.id
            ORDER BY sr.sale_date DESC
            LIMIT 100
        ''')
        records = self.cursor.fetchall()
        
        # 清空表格
        for item in self.sale_tree.get_children():
            self.sale_tree.delete(item)
        
        # 填充数据
        for record in records:
            self.sale_tree.insert("", "end", values=record)
    
    def load_inventory(self):
        """加载库存数据"""
        self.cursor.execute('''
            SELECT p.id, p.code, p.name, p.category, p.unit, p.stock, p.min_stock,
                   CASE 
                       WHEN p.stock <= 0 THEN '缺货'
                       WHEN p.stock < p.min_stock THEN '不足'
                       ELSE '正常'
                   END as status,
                   MAX(sc.change_time) as last_change
            FROM products p
            LEFT JOIN stock_changes sc ON p.id = sc.product_id
            GROUP BY p.id
            ORDER BY p.stock ASC
        ''')
        inventory = self.cursor.fetchall()
        
        # 清空表格
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # 填充数据
        for item in inventory:
            self.inventory_tree.insert("", "end", values=item)
        
        # 更新统计
        self.update_inventory_stats()
    
    def load_recent_operations(self):
        """加载最近操作记录"""
        # 清空表格
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        
        # 加载最近操作
        self.cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d %H:%M', sc.change_time) as time,
                sc.change_type,
                p.name,
                sc.change_quantity,
                sc.operator,
                sc.related_order
            FROM stock_changes sc
            JOIN products p ON sc.product_id = p.id
            ORDER BY sc.change_time DESC
            LIMIT 20
        ''')
        operations = self.cursor.fetchall()
        
        for op in operations:
            self.recent_tree.insert("", "end", values=op)
    
    # 业务逻辑方法
    def add_product(self):
        """添加产品"""
        try:
            # 获取表单数据
            code = self.product_form_vars["product_code"].get()
            name = self.product_form_vars["product_name"].get()
            category = self.product_form_vars["product_category"].get()
            unit = self.product_form_vars["product_unit"].get()
            
            # 验证必填字段
            if not code or not name:
                messagebox.showwarning("警告", "产品编码和名称不能为空！")
                return
            
            # 检查编码是否重复
            self.cursor.execute("SELECT id FROM products WHERE code = ?", (code,))
            if self.cursor.fetchone():
                messagebox.showwarning("警告", "产品编码已存在！")
                return
            
            # 获取价格
            purchase_price = float(self.product_form_vars["product_purchase_price"].get() or 0)
            sale_price = float(self.product_form_vars["product_sale_price"].get() or 0)
            stock = int(self.product_form_vars["product_stock"].get() or 0)
            min_stock = int(self.product_form_vars["product_min_stock"].get() or 10)
            
            # 获取供应商ID
            supplier_id = None
            supplier_name = self.product_supplier_var.get()
            if supplier_name:
                self.cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier_name,))
                result = self.cursor.fetchone()
                if result:
                    supplier_id = result[0]
            
            # 插入数据库
            self.cursor.execute('''
                INSERT INTO products (code, name, category, unit, purchase_price, 
                                     sale_price, stock, min_stock, supplier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, category, unit, purchase_price, sale_price, stock, min_stock, supplier_id))
            
            self.conn.commit()
            
            # 记录库存变动
            if stock > 0:
                self.cursor.execute('''
                    INSERT INTO stock_changes (product_id, change_type, change_quantity, 
                                             previous_stock, current_stock, related_order, operator)
                    VALUES (?, '初始库存', ?, 0, ?, '系统', '系统')
                ''', (self.cursor.lastrowid, stock, stock))
                self.conn.commit()
            
            messagebox.showinfo("成功", "产品添加成功！")
            self.load_products()
            self.clear_product_form()
            
        except Exception as e:
            messagebox.showerror("错误", f"添加产品失败：{str(e)}")
    
    def update_product(self):
        """更新产品"""
        try:
            selection = self.product_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个产品！")
                return
            
            item = self.product_tree.item(selection[0])
            product_id = item['values'][0]
            
            # 获取表单数据
            code = self.product_form_vars["product_code"].get()
            name = self.product_form_vars["product_name"].get()
            category = self.product_form_vars["product_category"].get()
            unit = self.product_form_vars["product_unit"].get()
            purchase_price = float(self.product_form_vars["product_purchase_price"].get() or 0)
            sale_price = float(self.product_form_vars["product_sale_price"].get() or 0)
            stock = int(self.product_form_vars["product_stock"].get() or 0)
            min_stock = int(self.product_form_vars["product_min_stock"].get() or 10)
            
            # 获取供应商ID
            supplier_id = None
            supplier_name = self.product_supplier_var.get()
            if supplier_name:
                self.cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier_name,))
                result = self.cursor.fetchone()
                if result:
                    supplier_id = result[0]
            
            # 更新数据库
            self.cursor.execute('''
                UPDATE products 
                SET code = ?, name = ?, category = ?, unit = ?, purchase_price = ?,
                    sale_price = ?, stock = ?, min_stock = ?, supplier_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (code, name, category, unit, purchase_price, sale_price, stock, min_stock, supplier_id, product_id))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", "产品更新成功！")
            self.load_products()
            
        except Exception as e:
            messagebox.showerror("错误", f"更新产品失败：{str(e)}")
    
    def delete_product(self):
        """删除产品"""
        selection = self.product_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个产品！")
            return
        
        if not messagebox.askyesno("确认", "确定要删除这个产品吗？"):
            return
        
        item = self.product_tree.item(selection[0])
        product_id = item['values'][0]
        
        try:
            # 检查是否有相关记录
            self.cursor.execute("SELECT COUNT(*) FROM purchase_records WHERE product_id = ?", (product_id,))
            purchase_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM sale_records WHERE product_id = ?", (product_id,))
            sale_count = self.cursor.fetchone()[0]
            
            if purchase_count > 0 or sale_count > 0:
                messagebox.showwarning("警告", "该产品有相关记录，无法删除！")
                return
            
            # 删除产品
            self.cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            self.conn.commit()
            
            messagebox.showinfo("成功", "产品删除成功！")
            self.load_products()
            self.clear_product_form()
            
        except Exception as e:
            messagebox.showerror("错误", f"删除产品失败：{str(e)}")
    
    def clear_product_form(self):
        """清空产品表单"""
        for var in self.product_form_vars.values():
            var.set("")
        self.product_supplier_var.set("")
    
    def on_product_select(self, event):
        """产品选择事件"""
        selection = self.product_tree.selection()
        if not selection:
            return
        
        item = self.product_tree.item(selection[0])
        values = item['values']
        
        # 填充表单
        self.product_form_vars["product_code"].set(values[1])
        self.product_form_vars["product_name"].set(values[2])
        self.product_form_vars["product_category"].set(values[3] if len(values) > 3 else "")
        self.product_form_vars["product_unit"].set(values[4] if len(values) > 4 else "")
        self.product_form_vars["product_purchase_price"].set(values[5] if len(values) > 5 else "")
        self.product_form_vars["product_sale_price"].set(values[6] if len(values) > 6 else "")
        self.product_form_vars["product_stock"].set(values[7] if len(values) > 7 else "")
        self.product_form_vars["product_min_stock"].set(values[8] if len(values) > 8 else "")
        
        # 设置供应商
        if len(values) > 9:
            self.product_supplier_var.set(values[9])
    
    def search_products(self, *args):
        """搜索产品"""
        search_term = self.product_search_var.get().lower()
        
        # 清空表格
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        
        # 重新查询
        self.cursor.execute("SELECT * FROM products")
        products = self.cursor.fetchall()
        
        # 过滤和填充
        for product in products:
            if (search_term in str(product[1]).lower() or  # 编码
                search_term in str(product[2]).lower() or  # 名称
                search_term in str(product[3]).lower()):   # 分类
                
                # 获取供应商名称
                supplier_name = ""
                if product[9]:
                    self.cursor.execute("SELECT name FROM suppliers WHERE id = ?", (product[9],))
                    supplier_result = self.cursor.fetchone()
                    if supplier_result:
                        supplier_name = supplier_result[0]
                
                self.product_tree.insert("", "end", values=product[:10] + (supplier_name,))
    
    def calculate_purchase_total(self):
        """计算采购总价"""
        try:
            quantity = float(self.purchase_form_vars["purchase_quantity"].get() or 0)
            unit_price = float(self.purchase_form_vars["purchase_unit_price"].get() or 0)
            total = quantity * unit_price
            self.purchase_total_var.set(f"{total:.2f}")
        except:
            self.purchase_total_var.set("0.00")
    
    def submit_purchase(self):
        """提交采购"""
        try:
            # 验证必填字段
            order_no = self.purchase_form_vars["purchase_order_no"].get()
            product_name = self.purchase_product_var.get()
            quantity = self.purchase_form_vars["purchase_quantity"].get()
            
            if not order_no or not product_name or not quantity:
                messagebox.showwarning("警告", "请填写完整的采购信息！")
                return
            
            # 获取产品ID
            product_code = product_name.split(" - ")[0]
            self.cursor.execute("SELECT id, stock FROM products WHERE code = ?", (product_code,))
            product_result = self.cursor.fetchone()
            
            if not product_result:
                messagebox.showwarning("警告", "产品不存在！")
                return
            
            product_id, current_stock = product_result
            
            # 获取供应商ID
            supplier_id = None
            supplier_name = self.purchase_supplier_var.get()
            if supplier_name:
                self.cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier_name,))
                supplier_result = self.cursor.fetchone()
                if supplier_result:
                    supplier_id = supplier_result[0]
            
            # 计算总价
            quantity_val = int(quantity)
            unit_price = float(self.purchase_form_vars["purchase_unit_price"].get() or 0)
            total_amount = quantity_val * unit_price
            
            # 插入采购记录
            self.cursor.execute('''
                INSERT INTO purchase_records (order_no, product_id, quantity, unit_price, 
                                            total_amount, supplier_id, purchase_date, operator, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_no, product_id, quantity_val, unit_price, total_amount,
                supplier_id, self.purchase_form_vars["purchase_date"].get(),
                self.purchase_form_vars["purchase_operator"].get(),
                self.purchase_form_vars["purchase_remarks"].get()
            ))
            
            # 更新库存
            new_stock = current_stock + quantity_val
            self.cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
            
            # 记录库存变动
            self.cursor.execute('''
                INSERT INTO stock_changes (product_id, change_type, change_quantity, 
                                         previous_stock, current_stock, related_order, operator)
                VALUES (?, '采购入库', ?, ?, ?, ?, ?)
            ''', (product_id, quantity_val, current_stock, new_stock, order_no, 
                 self.purchase_form_vars["purchase_operator"].get() or "系统"))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", "采购入库成功！")
            self.load_purchase_records()
            self.load_products()
            self.load_inventory()
            self.load_recent_operations()
            self.clear_purchase_form()
            self.update_dashboard_stats()
            
        except Exception as e:
            messagebox.showerror("错误", f"采购入库失败：{str(e)}")
    
    def clear_purchase_form(self):
        """清空采购表单"""
        for var in self.purchase_form_vars.values():
            var.set("")
        self.purchase_product_var.set("")
        self.purchase_supplier_var.set("")
        self.purchase_total_var.set("0.00")
        self.purchase_form_vars["purchase_date"].set(datetime.now().strftime("%Y-%m-%d"))
    
    def calculate_sale_total(self):
        """计算销售总价"""
        try:
            quantity = float(self.sale_form_vars["sale_quantity"].get() or 0)
            unit_price = float(self.sale_form_vars["sale_unit_price"].get() or 0)
            total = quantity * unit_price
            self.sale_total_var.set(f"{total:.2f}")
        except:
            self.sale_total_var.set("0.00")
    
    def check_stock(self):
        """检查库存"""
        product_name = self.sale_product_var.get()
        quantity = self.sale_form_vars["sale_quantity"].get()
        
        if not product_name or not quantity:
            self.stock_check_var.set("请选择产品和输入数量")
            return
        
        try:
            product_code = product_name.split(" - ")[0]
            self.cursor.execute("SELECT stock, name FROM products WHERE code = ?", (product_code,))
            product_result = self.cursor.fetchone()
            
            if product_result:
                stock, name = product_result
                quantity_val = int(quantity)
                
                if stock >= quantity_val:
                    self.stock_check_var.set(f"库存充足：{name} 当前库存 {stock}")
                else:
                    self.stock_check_var.set(f"库存不足：{name} 当前库存 {stock}，需要 {quantity_val}")
            else:
                self.stock_check_var.set("产品不存在")
        except:
            self.stock_check_var.set("库存检查失败")
    
    def submit_sale(self):
        """提交销售"""
        try:
            # 验证必填字段
            order_no = self.sale_form_vars["sale_order_no"].get()
            product_name = self.sale_product_var.get()
            quantity = self.sale_form_vars["sale_quantity"].get()
            
            if not order_no or not product_name or not quantity:
                messagebox.showwarning("警告", "请填写完整的销售信息！")
                return
            
            # 获取产品ID和库存
            product_code = product_name.split(" - ")[0]
            self.cursor.execute("SELECT id, stock, sale_price FROM products WHERE code = ?", (product_code,))
            product_result = self.cursor.fetchone()
            
            if not product_result:
                messagebox.showwarning("警告", "产品不存在！")
                return
            
            product_id, current_stock, default_price = product_result
            
            # 检查库存
            quantity_val = int(quantity)
            if current_stock < quantity_val:
                messagebox.showwarning("警告", f"库存不足！当前库存：{current_stock}")
                return
            
            # 获取客户ID
            customer_id = None
            customer_name = self.sale_customer_var.get()
            if customer_name:
                self.cursor.execute("SELECT id FROM customers WHERE name = ?", (customer_name,))
                customer_result = self.cursor.fetchone()
                if customer_result:
                    customer_id = customer_result[0]
            
            # 获取单价
            unit_price = float(self.sale_form_vars["sale_unit_price"].get() or default_price)
            total_amount = quantity_val * unit_price
            
            # 插入销售记录
            self.cursor.execute('''
                INSERT INTO sale_records (order_no, product_id, quantity, unit_price, 
                                        total_amount, customer_id, sale_date, operator, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_no, product_id, quantity_val, unit_price, total_amount,
                customer_id, self.sale_form_vars["sale_date"].get(),
                self.sale_form_vars["sale_operator"].get(),
                self.sale_form_vars["sale_remarks"].get()
            ))
            
            # 更新库存
            new_stock = current_stock - quantity_val
            self.cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
            
            # 记录库存变动
            self.cursor.execute('''
                INSERT INTO stock_changes (product_id, change_type, change_quantity, 
                                         previous_stock, current_stock, related_order, operator)
                VALUES (?, '销售出库', ?, ?, ?, ?, ?)
            ''', (product_id, -quantity_val, current_stock, new_stock, order_no, 
                 self.sale_form_vars["sale_operator"].get() or "系统"))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", "销售出库成功！")
            self.load_sale_records()
            self.load_products()
            self.load_inventory()
            self.load_recent_operations()
            self.clear_sale_form()
            self.update_dashboard_stats()
            
        except Exception as e:
            messagebox.showerror("错误", f"销售出库失败：{str(e)}")
    
    def clear_sale_form(self):
        """清空销售表单"""
        for var in self.sale_form_vars.values():
            var.set("")
        self.sale_product_var.set("")
        self.sale_customer_var.set("")
        self.sale_total_var.set("0.00")
        self.stock_check_var.set("")
        self.sale_form_vars["sale_date"].set(datetime.now().strftime("%Y-%m-%d"))
    
    def filter_inventory(self):
        """筛选库存"""
        category = self.category_filter_var.get()
        status = self.stock_status_var.get()
        
        # 构建查询条件
        conditions = []
        params = []
        
        if category:
            conditions.append("p.category = ?")
            params.append(category)
        
        if status != "全部":
            if status == "不足":
                conditions.append("p.stock < p.min_stock AND p.stock > 0")
            elif status == "缺货":
                conditions.append("p.stock <= 0")
            else:  # 正常
                conditions.append("p.stock >= p.min_stock")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f'''
            SELECT p.id, p.code, p.name, p.category, p.unit, p.stock, p.min_stock,
                   CASE 
                       WHEN p.stock <= 0 THEN '缺货'
                       WHEN p.stock < p.min_stock THEN '不足'
                       ELSE '正常'
                   END as status,
                   MAX(sc.change_time) as last_change
            FROM products p
            LEFT JOIN stock_changes sc ON p.id = sc.product_id
            WHERE {where_clause}
            GROUP BY p.id
            ORDER BY p.stock ASC
        '''
        
        self.cursor.execute(query, params)
        inventory = self.cursor.fetchall()
        
        # 清空表格
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # 填充数据
        for item in inventory:
            self.inventory_tree.insert("", "end", values=item)
    
    def update_inventory_stats(self):
        """更新库存统计"""
        # 产品总数
        self.cursor.execute("SELECT COUNT(*) FROM products")
        total_products = self.cursor.fetchone()[0]
        self.inventory_stats_vars["total_products"].set(str(total_products))
        
        # 总库存量
        self.cursor.execute("SELECT SUM(stock) FROM products")
        total_stock = self.cursor.fetchone()[0] or 0
        self.inventory_stats_vars["total_stock"].set(str(total_stock))
        
        # 库存不足
        self.cursor.execute("SELECT COUNT(*) FROM products WHERE stock < min_stock AND stock > 0")
        low_stock = self.cursor.fetchone()[0]
        self.inventory_stats_vars["low_stock"].set(str(low_stock))
        
        # 缺货产品
        self.cursor.execute("SELECT COUNT(*) FROM products WHERE stock <= 0")
        out_of_stock = self.cursor.fetchone()[0]
        self.inventory_stats_vars["out_of_stock"].set(str(out_of_stock))
    
    def export_inventory(self):
        """导出库存"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.cursor.execute('''
                SELECT code, name, category, unit, stock, min_stock,
                       CASE 
                           WHEN stock <= 0 THEN '缺货'
                           WHEN stock < min_stock THEN '不足'
                           ELSE '正常'
                       END as status
                FROM products
                ORDER BY stock ASC
            ''')
            inventory = self.cursor.fetchall()
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['产品编码', '产品名称', '分类', '单位', '当前库存', '最低库存', '状态'])
                writer.writerows(inventory)
            
            messagebox.showinfo("成功", f"库存数据已导出到：{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def generate_report(self):
        """生成报表"""
        report_type = self.report_type_var.get()
        period = self.report_period_var.get()
        start_date = self.report_start_var.get()
        end_date = self.report_end_var.get()
        
        # 清空表格
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        # 根据报表类型生成数据
        if report_type == "销售报表":
            self.generate_sales_report(start_date, end_date)
        elif report_type == "采购报表":
            self.generate_purchase_report(start_date, end_date)
        elif report_type == "库存报表":
            self.generate_inventory_report()
        elif report_type == "利润分析":
            self.generate_profit_report(start_date, end_date)
    
    def generate_sales_report(self, start_date, end_date):
        """生成销售报表"""
        self.cursor.execute('''
            SELECT 
                p.name as 产品,
                SUM(sr.quantity) as 销售数量,
                AVG(sr.unit_price) as 平均单价,
                SUM(sr.total_amount) as 销售总额,
                COUNT(*) as 订单数
            FROM sale_records sr
            JOIN products p ON sr.product_id = p.id
            WHERE sr.sale_date BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY SUM(sr.total_amount) DESC
        ''', (start_date, end_date))
        
        sales_data = self.cursor.fetchall()
        
        # 计算总计
        total_sales = sum(row[3] for row in sales_data) if sales_data else 0
        
        for row in sales_data:
            percentage = (row[3] / total_sales * 100) if total_sales > 0 else 0
            self.report_tree.insert("", "end", values=(
                row[0],  # 产品
                f"{row[1]}",  # 销售数量
                f"{row[2]:.2f}",  # 平均单价
                f"{row[3]:.2f}",  # 销售总额
                f"{percentage:.1f}%",  # 占比
                f"{row[4]}"  # 订单数
            ))
        
        # 更新摘要
        self.summary_vars["total_sales"].set(f"¥{total_sales:.2f}")
        
        # 最畅销产品
        if sales_data:
            top_product = sales_data[0][0]
            self.summary_vars["top_product"].set(top_product)
    
    def generate_purchase_report(self, start_date, end_date):
        """生成采购报表"""
        self.cursor.execute('''
            SELECT 
                p.name as 产品,
                SUM(pr.quantity) as 采购数量,
                AVG(pr.unit_price) as 平均单价,
                SUM(pr.total_amount) as 采购总额,
                COUNT(*) as 采购单数
            FROM purchase_records pr
            JOIN products p ON pr.product_id = p.id
            WHERE pr.purchase_date BETWEEN ? AND ?
            GROUP BY p.id
            ORDER BY SUM(pr.total_amount) DESC
        ''', (start_date, end_date))
        
        purchase_data = self.cursor.fetchall()
        
        # 计算总计
        total_purchase = sum(row[3] for row in purchase_data) if purchase_data else 0
        
        for row in purchase_data:
            percentage = (row[3] / total_purchase * 100) if total_purchase > 0 else 0
            self.report_tree.insert("", "end", values=(
                row[0],  # 产品
                f"{row[1]}",  # 采购数量
                f"{row[2]:.2f}",  # 平均单价
                f"{row[3]:.2f}",  # 采购总额
                f"{percentage:.1f}%",  # 占比
                f"{row[4]}"  # 采购单数
            ))
        
        # 更新摘要
        self.summary_vars["total_purchase"].set(f"¥{total_purchase:.2f}")
    
    def generate_inventory_report(self):
        """生成库存报表"""
        self.cursor.execute('''
            SELECT 
                p.name as 产品,
                p.category as 分类,
                p.stock as 当前库存,
                p.min_stock as 最低库存,
                p.stock * p.purchase_price as 库存金额,
                CASE 
                    WHEN p.stock <= 0 THEN '缺货'
                    WHEN p.stock < p.min_stock THEN '不足'
                    ELSE '正常'
                END as 状态
            FROM products p
            ORDER BY p.stock ASC
        ''')
        
        inventory_data = self.cursor.fetchall()
        
        # 计算总计
        total_value = sum(row[4] for row in inventory_data) if inventory_data else 0
        
        for row in inventory_data:
            self.report_tree.insert("", "end", values=(
                row[0],  # 产品
                row[1],  # 分类
                f"{row[2]}",  # 当前库存
                f"{row[3]}",  # 最低库存
                f"¥{row[4]:.2f}",  # 库存金额
                row[5]  # 状态
            ))
    
    def generate_profit_report(self, start_date, end_date):
        """生成利润分析报表"""
        # 计算销售收入
        self.cursor.execute('''
            SELECT 
                p.name,
                SUM(sr.quantity) as sale_qty,
                SUM(sr.total_amount) as sale_amount,
                AVG(sr.unit_price) as avg_sale_price
            FROM sale_records sr
            JOIN products p ON sr.product_id = p.id
            WHERE sr.sale_date BETWEEN ? AND ?
            GROUP BY p.id
        ''', (start_date, end_date))
        
        sales_data = self.cursor.fetchall()
        
        # 计算采购成本
        self.cursor.execute('''
            SELECT 
                p.name,
                SUM(pr.quantity) as purchase_qty,
                SUM(pr.total_amount) as purchase_amount,
                AVG(pr.unit_price) as avg_purchase_price
            FROM purchase_records pr
            JOIN products p ON pr.product_id = p.id
            WHERE pr.purchase_date BETWEEN ? AND ?
            GROUP BY p.id
        ''', (start_date, end_date))
        
        purchase_data = self.cursor.fetchall()
        
        # 计算利润
        total_sales = sum(row[2] for row in sales_data) if sales_data else 0
        total_purchase = sum(row[2] for row in purchase_data) if purchase_data else 0
        total_profit = total_sales - total_purchase
        profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        # 显示利润数据
        self.report_tree.insert("", "end", values=("销售收入", f"¥{total_sales:.2f}", "100%", "↑"))
        self.report_tree.insert("", "end", values=("采购成本", f"¥{total_purchase:.2f}", 
                                                 f"{(total_purchase/total_sales*100):.1f}%" if total_sales > 0 else "0%", "↓"))
        self.report_tree.insert("", "end", values=("总利润", f"¥{total_profit:.2f}", 
                                                 f"{profit_margin:.1f}%", "↑" if total_profit > 0 else "↓"))
        
        # 更新摘要
        self.summary_vars["total_sales"].set(f"¥{total_sales:.2f}")
        self.summary_vars["total_purchase"].set(f"¥{total_purchase:.2f}")
        self.summary_vars["total_profit"].set(f"¥{total_profit:.2f}")
        self.summary_vars["profit_margin"].set(f"{profit_margin:.1f}%")
    
    def export_report(self):
        """导出报表"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 获取当前报表数据
            data = []
            for item_id in self.report_tree.get_children():
                item = self.report_tree.item(item_id)
                data.append(item['values'])
            
            if not data:
                messagebox.showwarning("警告", "没有数据可导出！")
                return
            
            # 获取列名
            columns = [self.report_tree.heading(col)["text"] for col in self.report_tree["columns"]]
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(data)
            
            messagebox.showinfo("成功", f"报表数据已导出到：{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def export_data(self):
        """导出数据"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 获取所有数据
            self.cursor.execute("SELECT * FROM products")
            products = self.cursor.fetchall()
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', '编码', '名称', '分类', '单位', '进货价', '销售价', '库存', '最低库存', '供应商ID', '创建时间', '更新时间'])
                writer.writerows(products)
            
            messagebox.showinfo("成功", f"数据已导出到：{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def update_dashboard_stats(self):
        """更新仪表盘统计数据"""
        # 产品总数
        self.cursor.execute("SELECT COUNT(*) FROM products")
        total_products = self.cursor.fetchone()[0]
        
        # 总库存量
        self.cursor.execute("SELECT SUM(stock) FROM products")
        total_stock = self.cursor.fetchone()[0] or 0
        
        # 低库存产品数
        self.cursor.execute("SELECT COUNT(*) FROM products WHERE stock < min_stock AND stock > 0")
        low_stock = self.cursor.fetchone()[0]
        
        # 本月销售额
        current_month = datetime.now().strftime("%Y-%m")
        self.cursor.execute("SELECT SUM(total_amount) FROM sale_records WHERE strftime('%Y-%m', sale_date) = ?", (current_month,))
        month_sales = self.cursor.fetchone()[0] or 0
        
        # 更新卡片
        self.stat_cards[0]["value_label"].config(text=str(total_products))
        self.stat_cards[1]["value_label"].config(text=str(total_stock))
        self.stat_cards[2]["value_label"].config(text=str(low_stock))
        self.stat_cards[3]["value_label"].config(text=f"¥{month_sales:.2f}")
    
    # 标签页显示方法
    def show_product_tab(self):
        self.notebook.select(1)  # 产品管理标签页索引为1
    
    def show_purchase_tab(self):
        self.notebook.select(2)  # 采购管理标签页索引为2
    
    def show_sale_tab(self):
        self.notebook.select(3)  # 销售管理标签页索引为3
    
    def show_inventory_tab(self):
        self.notebook.select(4)  # 库存管理标签页索引为4
    
    def show_report_tab(self):
        self.notebook.select(5)  # 报表分析标签页索引为5
    
    def on_closing(self):
        """关闭窗口时执行"""
        if messagebox.askokcancel("退出", "确定要退出进销存管理系统吗？"):
            self.conn.close()
            self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = InventoryManagementSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main()