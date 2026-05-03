import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sqlite3
from datetime import datetime
import json
import os
import shutil
import sys

class DatabaseManager:
    def __init__(self, db_name="wms.db"):
        self.db_name = db_name
        self.conn = None
        
    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close_connection(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                spec TEXT,
                unit TEXT,
                category TEXT,
                purchase_price REAL DEFAULT 0,
                sale_price REAL DEFAULT 0,
                alert_qty INTEGER DEFAULT 0,
                remark TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT,
                quantity INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_code) REFERENCES products(code) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inbound_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT,
                quantity INTEGER,
                supplier TEXT,
                operator TEXT,
                remark TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_code) REFERENCES products(code)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outbound_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT,
                quantity INTEGER,
                customer TEXT,
                operator TEXT,
                remark TEXT,
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_code) REFERENCES products(code)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_code ON inventory(product_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inbound_time ON inbound_records(create_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outbound_time ON outbound_records(create_time)')
        conn.commit()
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS create_inventory_after_product
            AFTER INSERT ON products
            BEGIN
                INSERT INTO inventory (product_code, quantity) VALUES (NEW.code, 0);
            END
        ''')
        conn.commit()
    
    def add_product(self, product_data):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO products (code, name, spec, unit, category, 
                                    purchase_price, sale_price, alert_qty, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_data['code'], product_data['name'], product_data.get('spec', ''),
                product_data.get('unit', ''), product_data.get('category', ''),
                product_data.get('purchase_price', 0), product_data.get('sale_price', 0),
                product_data.get('alert_qty', 0), product_data.get('remark', '')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_product(self, code, product_data):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET name=?, spec=?, unit=?, category=?, 
                purchase_price=?, sale_price=?, alert_qty=?, remark=?
            WHERE code=?
        ''', (
            product_data['name'], product_data.get('spec', ''),
            product_data.get('unit', ''), product_data.get('category', ''),
            product_data.get('purchase_price', 0), product_data.get('sale_price', 0),
            product_data.get('alert_qty', 0), product_data.get('remark', ''),
            code
        ))
        conn.commit()
        return cursor.rowcount > 0
    
    def delete_product(self, code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE code=?', (code,))
        conn.commit()
        return cursor.rowcount > 0
    
    def get_all_products(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY code')
        return cursor.fetchall()
    
    def get_product_by_code(self, code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE code=?', (code,))
        return cursor.fetchone()
    
    def search_products(self, keyword):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM products 
            WHERE code LIKE ? OR name LIKE ? OR spec LIKE ? OR category LIKE ?
            ORDER BY code
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        return cursor.fetchall()
    
    def get_product_codes(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM products ORDER BY code')
        return [row[0] for row in cursor.fetchall()]
    
    def get_categories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM products WHERE category != ""')
        return [row[0] for row in cursor.fetchall()]
    
    def get_inventory(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.code, p.name, p.spec, i.quantity, p.unit, i.last_update
            FROM products p
            LEFT JOIN inventory i ON p.code = i.product_code
            ORDER BY p.code
        ''')
        return cursor.fetchall()
    
    def get_current_stock(self, product_code):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM inventory WHERE product_code=?', (product_code,))
        result = cursor.fetchone()
        return result[0] if result else 0
    
    def query_inventory(self, code='', name='', category=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = '''
            SELECT p.code, p.name, p.spec, i.quantity, p.unit, i.last_update
            FROM products p
            LEFT JOIN inventory i ON p.code = i.product_code
            WHERE 1=1
        '''
        params = []
        if code:
            query += ' AND p.code LIKE ?'
            params.append(f'%{code}%')
        if name:
            query += ' AND p.name LIKE ?'
            params.append(f'%{name}%')
        if category:
            query += ' AND p.category = ?'
            params.append(category)
        query += ' ORDER BY p.code'
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def get_alert_products(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.code, p.name, i.quantity, p.alert_qty
            FROM products p
            LEFT JOIN inventory i ON p.code = i.product_code
            WHERE i.quantity <= p.alert_qty
            ORDER BY i.quantity
        ''')
        return cursor.fetchall()
    
    def inbound_product(self, product_code, quantity, supplier='', remark=''):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE inventory 
                SET quantity = quantity + ?, last_update = CURRENT_TIMESTAMP
                WHERE product_code=?
            ''', (quantity, product_code))
            cursor.execute('''
                INSERT INTO inbound_records (product_code, quantity, supplier, remark)
                VALUES (?, ?, ?, ?)
            ''', (product_code, quantity, supplier, remark))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
    
    def get_inbound_records(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.id, p.code, p.name, r.quantity, r.supplier, 
                   r.operator, r.create_time, r.remark
            FROM inbound_records r
            LEFT JOIN products p ON r.product_code = p.code
            ORDER BY r.create_time DESC
            LIMIT 100
        ''')
        return cursor.fetchall()
    
    def outbound_product(self, product_code, quantity, customer='', remark=''):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT quantity FROM inventory WHERE product_code=?', (product_code,))
            result = cursor.fetchone()
            if not result or result[0] < quantity:
                return False
            cursor.execute('''
                UPDATE inventory 
                SET quantity = quantity - ?, last_update = CURRENT_TIMESTAMP
                WHERE product_code=?
            ''', (quantity, product_code))
            cursor.execute('''
                INSERT INTO outbound_records (product_code, quantity, customer, remark)
                VALUES (?, ?, ?, ?)
            ''', (product_code, quantity, customer, remark))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
    
    def get_outbound_records(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.id, p.code, p.name, r.quantity, r.customer, 
                   r.operator, r.create_time, r.remark
            FROM outbound_records r
            LEFT JOIN products p ON r.product_code = p.code
            ORDER BY r.create_time DESC
            LIMIT 100
        ''')
        return cursor.fetchall()
    
    def export_data(self, filename):
        data = {'products': [], 'inventory': [], 'inbound_records': [], 'outbound_records': []}
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        for row in cursor.fetchall():
            data['products'].append(dict(row))
        cursor.execute('SELECT * FROM inventory')
        for row in cursor.fetchall():
            data['inventory'].append(dict(row))
        cursor.execute('SELECT * FROM inbound_records')
        for row in cursor.fetchall():
            data['inbound_records'].append(dict(row))
        cursor.execute('SELECT * FROM outbound_records')
        for row in cursor.fetchall():
            data['outbound_records'].append(dict(row))
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def import_data(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM outbound_records')
            cursor.execute('DELETE FROM inbound_records')
            cursor.execute('DELETE FROM inventory')
            cursor.execute('DELETE FROM products')
            for product in data.get('products', []):
                cursor.execute('''
                    INSERT INTO products (code, name, spec, unit, category, 
                                        purchase_price, sale_price, alert_qty, remark, create_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (product['code'], product['name'], product.get('spec', ''),
                      product.get('unit', ''), product.get('category', ''),
                      product.get('purchase_price', 0), product.get('sale_price', 0),
                      product.get('alert_qty', 0), product.get('remark', ''),
                      product.get('create_time', datetime.now().isoformat())))
            for inventory in data.get('inventory', []):
                cursor.execute('''
                    INSERT INTO inventory (id, product_code, quantity, last_update)
                    VALUES (?, ?, ?, ?)
                ''', (inventory['id'], inventory['product_code'], 
                      inventory['quantity'], inventory['last_update']))
            for record in data.get('inbound_records', []):
                cursor.execute('''
                    INSERT INTO inbound_records (id, product_code, quantity, supplier, 
                                                operator, remark, create_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (record['id'], record['product_code'], record['quantity'],
                      record.get('supplier', ''), record.get('operator', ''),
                      record.get('remark', ''), record['create_time']))
            for record in data.get('outbound_records', []):
                cursor.execute('''
                    INSERT INTO outbound_records (id, product_code, quantity, customer, 
                                                operator, remark, create_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (record['id'], record['product_code'], record['quantity'],
                      record.get('customer', ''), record.get('operator', ''),
                      record.get('remark', ''), record['create_time']))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False

class WMS_System:
    def __init__(self, root):
        self.root = root
        self.root.title("仓库管理系统 - WMS")
        self.root.geometry("1200x700")
        self.db = DatabaseManager()
        self.db.create_tables()
        self.create_menu()
        self.create_main_interface()
        self.status_bar = tk.Label(root, text="就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_command(label="导入数据", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def create_main_interface(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.create_product_tab()
        self.create_inventory_tab()
        self.create_inbound_tab()
        self.create_outbound_tab()
        self.create_report_tab()
        
    def create_product_tab(self):
        self.product_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.product_frame, text="产品管理")
        left_frame = ttk.LabelFrame(self.product_frame, text="产品信息录入", padding=10)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        fields = [("产品编码:", "code"), ("产品名称:", "name"), ("规格型号:", "spec"),
                  ("单位:", "unit"), ("分类:", "category"), ("采购价:", "purchase_price"),
                  ("销售价:", "sale_price"), ("预警库存:", "alert_qty")]
        self.product_entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(left_frame, text=label).grid(row=i, column=0, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(left_frame, width=25)
            entry.grid(row=i, column=1, padx=5, pady=5)
            self.product_entries[key] = entry
        ttk.Label(left_frame, text="备注:").grid(row=len(fields), column=0, sticky="ne", padx=5, pady=5)
        self.product_entries['remark'] = scrolledtext.ScrolledText(left_frame, width=25, height=4)
        self.product_entries['remark'].grid(row=len(fields), column=1, padx=5, pady=5)
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="添加产品", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="更新产品", command=self.update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除产品", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空表单", command=self.clear_product_form).pack(side=tk.LEFT, padx=5)
        right_frame = ttk.LabelFrame(self.product_frame, text="产品列表", padding=10)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_products)
        ttk.Button(search_frame, text="刷新", command=self.load_products).pack(side=tk.LEFT, padx=5)
        columns = ('code', 'name', 'spec', 'unit', 'category', 'purchase_price', 'sale_price', 'alert_qty')
        self.product_tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=20)
        headings = ['产品编码', '产品名称', '规格型号', '单位', '分类', '采购价', '销售价', '预警库存']
        for col, head in zip(columns, headings):
            self.product_tree.heading(col, text=head)
            self.product_tree.column(col, width=100)
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.product_tree.bind('<<TreeviewSelect>>', self.on_product_select)
        self.load_products()
        self.product_frame.grid_columnconfigure(0, weight=1)
        self.product_frame.grid_columnconfigure(1, weight=2)
        self.product_frame.grid_rowconfigure(0, weight=1)
        
    def create_inventory_tab(self):
        self.inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.inventory_frame, text="库存查询")
        query_frame = ttk.LabelFrame(self.inventory_frame, text="查询条件", padding=10)
        query_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(query_frame, text="产品编码:").grid(row=0, column=0, padx=5, pady=5)
        self.inv_code_entry = ttk.Entry(query_frame, width=15)
        self.inv_code_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(query_frame, text="产品名称:").grid(row=0, column=2, padx=5, pady=5)
        self.inv_name_entry = ttk.Entry(query_frame, width=15)
        self.inv_name_entry.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(query_frame, text="分类:").grid(row=0, column=4, padx=5, pady=5)
        self.inv_category = ttk.Combobox(query_frame, width=12)
        self.inv_category.grid(row=0, column=5, padx=5, pady=5)
        ttk.Button(query_frame, text="查询", command=self.query_inventory).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(query_frame, text="刷新", command=self.load_inventory).grid(row=0, column=7, padx=5, pady=5)
        inv_table_frame = ttk.Frame(self.inventory_frame)
        inv_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ('code', 'name', 'spec', 'quantity', 'unit', 'last_update')
        self.inventory_tree = ttk.Treeview(inv_table_frame, columns=columns, show='headings', height=20)
        headings = ['产品编码', '产品名称', '规格型号', '当前库存', '单位', '最后更新']
        for col, head in zip(columns, headings):
            self.inventory_tree.heading(col, text=head)
            self.inventory_tree.column(col, width=120)
        scrollbar = ttk.Scrollbar(inv_table_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_inventory()
        self.load_categories()
        
    def create_inbound_tab(self):
        self.inbound_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.inbound_frame, text="入库管理")
        form_frame = ttk.LabelFrame(self.inbound_frame, text="入库单", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(form_frame, text="产品编码:").grid(row=0, column=0, padx=5, pady=5)
        self.inbound_code = ttk.Combobox(form_frame, width=20)
        self.inbound_code.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form_frame, text="入库数量:").grid(row=0, column=2, padx=5, pady=5)
        self.inbound_qty = ttk.Entry(form_frame, width=15)
        self.inbound_qty.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(form_frame, text="供应商:").grid(row=0, column=4, padx=5, pady=5)
        self.inbound_supplier = ttk.Entry(form_frame, width=20)
        self.inbound_supplier.grid(row=0, column=5, padx=5, pady=5)
        ttk.Label(form_frame, text="备注:").grid(row=1, column=0, padx=5, pady=5)
        self.inbound_remark = ttk.Entry(form_frame, width=50)
        self.inbound_remark.grid(row=1, column=1, columnspan=5, padx=5, pady=5, sticky="we")
        ttk.Button(form_frame, text="确认入库", command=self.inbound_product).grid(row=2, column=0, columnspan=6, pady=10)
        record_frame = ttk.LabelFrame(self.inbound_frame, text="入库记录", padding=10)
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ('id', 'code', 'name', 'quantity', 'supplier', 'operator', 'datetime', 'remark')
        self.inbound_tree = ttk.Treeview(record_frame, columns=columns, show='headings', height=15)
        headings = ['流水号', '产品编码', '产品名称', '数量', '供应商', '操作员', '入库时间', '备注']
        widths = [50, 100, 150, 80, 120, 80, 150, 150]
        for col, head, width in zip(columns, headings, widths):
            self.inbound_tree.heading(col, text=head)
            self.inbound_tree.column(col, width=width)
        scrollbar = ttk.Scrollbar(record_frame, orient=tk.VERTICAL, command=self.inbound_tree.yview)
        self.inbound_tree.configure(yscrollcommand=scrollbar.set)
        self.inbound_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_product_codes()
        self.load_inbound_records()
        
    def create_outbound_tab(self):
        self.outbound_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.outbound_frame, text="出库管理")
        form_frame = ttk.LabelFrame(self.outbound_frame, text="出库单", padding=10)
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(form_frame, text="产品编码:").grid(row=0, column=0, padx=5, pady=5)
        self.outbound_code = ttk.Combobox(form_frame, width=20)
        self.outbound_code.grid(row=0, column=1, padx=5, pady=5)
        self.outbound_code.bind('<<ComboboxSelected>>', self.load_current_stock)
        ttk.Label(form_frame, text="当前库存:").grid(row=0, column=2, padx=5, pady=5)
        self.current_stock = ttk.Entry(form_frame, width=15, state='readonly')
        self.current_stock.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(form_frame, text="出库数量:").grid(row=0, column=4, padx=5, pady=5)
        self.outbound_qty = ttk.Entry(form_frame, width=15)
        self.outbound_qty.grid(row=0, column=5, padx=5, pady=5)
        ttk.Label(form_frame, text="客户:").grid(row=1, column=0, padx=5, pady=5)
        self.outbound_customer = ttk.Entry(form_frame, width=20)
        self.outbound_customer.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(form_frame, text="备注:").grid(row=1, column=2, padx=5, pady=5)
        self.outbound_remark = ttk.Entry(form_frame, width=50)
        self.outbound_remark.grid(row=1, column=3, columnspan=3, padx=5, pady=5, sticky="we")
        ttk.Button(form_frame, text="确认出库", command=self.outbound_product).grid(row=2, column=0, columnspan=6, pady=10)
        record_frame = ttk.LabelFrame(self.outbound_frame, text="出库记录", padding=10)
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ('id', 'code', 'name', 'quantity', 'customer', 'operator', 'datetime', 'remark')
        self.outbound_tree = ttk.Treeview(record_frame, columns=columns, show='headings', height=15)
        headings = ['流水号', '产品编码', '产品名称', '数量', '客户', '操作员', '出库时间', '备注']
        widths = [50, 100, 150, 80, 120, 80, 150, 150]
        for col, head, width in zip(columns, headings, widths):
            self.outbound_tree.heading(col, text=head)
            self.outbound_tree.column(col, width=width)
        scrollbar = ttk.Scrollbar(record_frame, orient=tk.VERTICAL, command=self.outbound_tree.yview)
        self.outbound_tree.configure(yscrollcommand=scrollbar.set)
        self.outbound_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.load_outbound_codes()
        self.load_outbound_records()
        
    def create_report_tab(self):
        self.report_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.report_frame, text="报表统计")
        alert_frame = ttk.LabelFrame(self.report_frame, text="库存预警", padding=10)
        alert_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        columns = ('code', 'name', 'current_qty', 'alert_qty', 'status')
        self.alert_tree = ttk.Treeview(alert_frame, columns=columns, show='headings', height=10)
        headings = ['产品编码', '产品名称', '当前库存', '预警库存', '状态']
        for col, head in zip(columns, headings):
            self.alert_tree.heading(col, text=head)
            self.alert_tree.column(col, width=150)
        scrollbar = ttk.Scrollbar(alert_frame, orient=tk.VERTICAL, command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=scrollbar.set)
        self.alert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(self.report_frame, text="刷新预警", command=self.load_alert_products).pack(pady=10)
        self.load_alert_products()
    
    def add_product(self):
        data = {}
        for key, entry in self.product_entries.items():
            if key == 'remark':
                data[key] = entry.get('1.0', tk.END).strip()
            else:
                data[key] = entry.get().strip()
        if not data['code'] or not data['name']:
            messagebox.showerror("错误", "产品编码和产品名称不能为空！")
            return
        for field in ['purchase_price', 'sale_price', 'alert_qty']:
            if data[field]:
                try:
                    data[field] = float(data[field]) if field != 'alert_qty' else int(data[field])
                except:
                    data[field] = 0
            else:
                data[field] = 0
        if self.db.add_product(data):
            messagebox.showinfo("成功", "产品添加成功！")
            self.clear_product_form()
            self.load_products()
            self.load_product_codes()
            self.load_outbound_codes()
            self.load_inventory()
        else:
            messagebox.showerror("错误", "产品编码已存在！")
    
    def update_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要更新的产品！")
            return
        old_code = self.product_tree.item(selected[0])['values'][0]
        data = {}
        for key, entry in self.product_entries.items():
            if key == 'remark':
                data[key] = entry.get('1.0', tk.END).strip()
            else:
                data[key] = entry.get().strip()
        for field in ['purchase_price', 'sale_price', 'alert_qty']:
            if data[field]:
                try:
                    data[field] = float(data[field]) if field != 'alert_qty' else int(data[field])
                except:
                    data[field] = 0
            else:
                data[field] = 0
        if self.db.update_product(old_code, data):
            messagebox.showinfo("成功", "产品更新成功！")
            self.load_products()
            self.load_inventory()
        else:
            messagebox.showerror("错误", "更新失败！")
    
    def delete_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的产品！")
            return
        if messagebox.askyesno("确认", "确定要删除该产品吗？"):
            code = self.product_tree.item(selected[0])['values'][0]
            if self.db.delete_product(code):
                messagebox.showinfo("成功", "产品删除成功！")
                self.clear_product_form()
                self.load_products()
                self.load_product_codes()
                self.load_outbound_codes()
                self.load_inventory()
            else:
                messagebox.showerror("错误", "删除失败！")
    
    def clear_product_form(self):
        for key, entry in self.product_entries.items():
            if key == 'remark':
                entry.delete('1.0', tk.END)
            else:
                entry.delete(0, tk.END)
    
    def load_products(self):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        products = self.db.get_all_products()
        for product in products:
            self.product_tree.insert('', tk.END, values=(
                product[0], product[1], product[2], product[3],
                product[4], product[5], product[6], product[7]
            ))
    
    def search_products(self, event=None):
        keyword = self.search_entry.get().strip()
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)
        products = self.db.search_products(keyword)
        for product in products:
            self.product_tree.insert('', tk.END, values=(
                product[0], product[1], product[2], product[3],
                product[4], product[5], product[6], product[7]
            ))
    
    def on_product_select(self, event):
        selected = self.product_tree.selection()
        if selected:
            values = self.product_tree.item(selected[0])['values']
            fields = ['code', 'name', 'spec', 'unit', 'category', 'purchase_price', 'sale_price', 'alert_qty']
            for i, key in enumerate(fields):
                self.product_entries[key].delete(0, tk.END)
                self.product_entries[key].insert(0, str(values[i]) if values[i] is not None else '')
            product = self.db.get_product_by_code(values[0])
            if product and product[8]:
                self.product_entries['remark'].delete('1.0', tk.END)
                self.product_entries['remark'].insert('1.0', product[8])
    
    def load_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        inventory = self.db.get_inventory()
        for inv in inventory:
            self.inventory_tree.insert('', tk.END, values=inv)
    
    def query_inventory(self):
        code = self.inv_code_entry.get().strip()
        name = self.inv_name_entry.get().strip()
        category = self.inv_category.get().strip()
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        inventory = self.db.query_inventory(code, name, category)
        for inv in inventory:
            self.inventory_tree.insert('', tk.END, values=inv)
    
    def load_categories(self):
        categories = self.db.get_categories()
        self.inv_category['values'] = categories
    
    def load_product_codes(self):
        codes = self.db.get_product_codes()
        self.inbound_code['values'] = codes
    
    def load_inbound_records(self):
        for item in self.inbound_tree.get_children():
            self.inbound_tree.delete(item)
        records = self.db.get_inbound_records()
        for record in records:
            self.inbound_tree.insert('', tk.END, values=record)
    
    def inbound_product(self):
        code = self.inbound_code.get().strip()
        qty_str = self.inbound_qty.get().strip()
        supplier = self.inbound_supplier.get().strip()
        remark = self.inbound_remark.get().strip()
        if not code or not qty_str:
            messagebox.showerror("错误", "请选择产品和输入入库数量！")
            return
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入有效的数量！")
            return
        if self.db.inbound_product(code, qty, supplier, remark):
            messagebox.showinfo("成功", "入库成功！")
            self.inbound_qty.delete(0, tk.END)
            self.inbound_supplier.delete(0, tk.END)
            self.inbound_remark.delete(0, tk.END)
            self.load_inventory()
            self.load_inbound_records()
            self.load_alert_products()
            self.update_status("入库成功")
        else:
            messagebox.showerror("错误", "入库失败，请检查产品是否存在！")
    
    def load_outbound_codes(self):
        codes = self.db.get_product_codes()
        self.outbound_code['values'] = codes
    
    def load_current_stock(self, event=None):
        code = self.outbound_code.get().strip()
        if code:
            stock = self.db.get_current_stock(code)
            self.current_stock.config(state='normal')
            self.current_stock.delete(0, tk.END)
            self.current_stock.insert(0, str(stock))
            self.current_stock.config(state='readonly')
    
    def load_outbound_records(self):
        for item in self.outbound_tree.get_children():
            self.outbound_tree.delete(item)
        records = self.db.get_outbound_records()
        for record in records:
            self.outbound_tree.insert('', tk.END, values=record)
    
    def outbound_product(self):
        code = self.outbound_code.get().strip()
        qty_str = self.outbound_qty.get().strip()
        customer = self.outbound_customer.get().strip()
        remark = self.outbound_remark.get().strip()
        if not code or not qty_str:
            messagebox.showerror("错误", "请选择产品和输入出库数量！")
            return
        try:
            qty = int(qty_str)
            if qty <= 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入有效的数量！")
            return
        current_stock = self.db.get_current_stock(code)
        if qty > current_stock:
            messagebox.showerror("错误", f"库存不足！当前库存：{current_stock}")
            return
        if self.db.outbound_product(code, qty, customer, remark):
            messagebox.showinfo("成功", "出库成功！")
            self.outbound_qty.delete(0, tk.END)
            self.outbound_customer.delete(0, tk.END)
            self.outbound_remark.delete(0, tk.END)
            self.load_inventory()
            self.load_outbound_records()
            self.load_alert_products()
            self.update_status("出库成功")
        else:
            messagebox.showerror("错误", "出库失败！")
    
    def load_alert_products(self):
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)
        products = self.db.get_alert_products()
        for product in products:
            status = "⚠️ 库存不足" if product[2] <= product[3] else "正常"
            self.alert_tree.insert('', tk.END, values=(
                product[0], product[1], product[2], product[3], status
            ))
    
    def export_data(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON文件", "*.json")])
        if filename:
            self.db.export_data(filename)
            messagebox.showinfo("成功", f"数据已导出到：{filename}")
    
    def import_data(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON文件", "*.json")])
        if filename:
            if messagebox.askyesno("确认", "导入数据将覆盖现有数据，确定要继续吗？"):
                self.db.import_data(filename)
                messagebox.showinfo("成功", "数据导入成功！")
                self.load_products()
                self.load_inventory()
                self.load_inbound_records()
                self.load_outbound_records()
    
    def backup_database(self):
        filename = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("数据库文件", "*.db")])
        if filename:
            shutil.copy2("wms.db", filename)
            messagebox.showinfo("成功", f"数据库已备份到：{filename}")
    
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("400x300")
        about_text = """
        仓库管理系统(WMS)
        
        版本：1.0.0
        
        功能特点：
        - 产品信息管理
        - 库存实时查询
        - 入库/出库管理
        - 自动库存预警
        - 数据导入导出
        
        技术支持：WMS System
        """
        label = ttk.Label(about_window, text=about_text, justify=tk.LEFT, font=("微软雅黑", 10))
        label.pack(expand=True, padx=20, pady=20)
        ttk.Button(about_window, text="确定", command=about_window.destroy).pack(pady=10)
    
    def update_status(self, message):
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text="就绪"))

def main():
    root = tk.Tk()
    app = WMS_System(root)
    root.mainloop()

if __name__ == "__main__":
    main()