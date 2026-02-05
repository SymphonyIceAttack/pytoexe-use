import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import datetime
import csv
import os
import json
from datetime import datetime, timedelta
import hashlib
import shutil
from decimal import Decimal

class CompleteInventorySystemWithInvoice:
    def __init__(self, root):
        self.root = root
        self.root.title("完整进销存管理系统 v3.0（含发票管理）")
        self.root.geometry("1400x800")
        
        # 设置窗口图标
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        # 连接数据库
        self.conn = sqlite3.connect('inventory_complete_with_invoice.db')
        self.cursor = self.conn.cursor()
        
        # 创建数据表（包含所有表）
        self.create_all_tables()
        
        # 当前登录用户
        self.current_user = None
        self.current_role = None
        
        # 设置样式
        self.setup_styles()
        
        # 显示登录界面
        self.show_login()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置标签页样式
        style.configure('TNotebook.Tab', padding=[10, 5], font=('微软雅黑', 10))
        
        # 配置按钮样式
        style.configure('Primary.TButton', foreground='white', background='#007bff', font=('微软雅黑', 10))
        style.map('Primary.TButton', background=[('active', '#0056b3')])
        
        style.configure('Success.TButton', foreground='white', background='#28a745', font=('微软雅黑', 10))
        style.map('Success.TButton', background=[('active', '#1e7e34')])
        
        style.configure('Danger.TButton', foreground='white', background='#dc3545', font=('微软雅黑', 10))
        style.map('Danger.TButton', background=[('active', '#bd2130')])
        
        style.configure('Warning.TButton', foreground='white', background='#ffc107', font=('微软雅黑', 10))
        style.map('Warning.TButton', background=[('active', '#e0a800')])
        
        style.configure('Info.TButton', foreground='white', background='#17a2b8', font=('微软雅黑', 10))
        style.map('Info.TButton', background=[('active', '#138496')])
    
    def create_all_tables(self):
        """创建所有数据库表"""
        # 用户表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                realname TEXT NOT NULL,
                role TEXT NOT NULL,
                department TEXT,
                phone TEXT,
                email TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # 角色权限表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                permissions TEXT,
                description TEXT
            )
        ''')
        
        # 产品表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                barcode TEXT,
                category TEXT,
                unit TEXT,
                purchase_price REAL,
                sale_price REAL,
                cost_price REAL,
                stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                max_stock INTEGER DEFAULT 1000,
                supplier_id INTEGER,
                warehouse_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 仓库表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                manager_id INTEGER,
                capacity INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                tax_number TEXT,
                bank_account TEXT,
                credit_rating TEXT,
                status TEXT DEFAULT 'active',
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
                tax_number TEXT,
                bank_account TEXT,
                credit_limit REAL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 部门表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                manager_id INTEGER,
                parent_id INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== 入库管理相关表 ==========
        
        # 采购入库单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                supplier_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                tax_amount REAL,
                discount REAL,
                final_amount REAL NOT NULL,
                order_date DATE NOT NULL,
                expected_date DATE,
                received_date DATE,
                status TEXT DEFAULT 'pending', -- pending, partial, completed, cancelled
                payment_status TEXT DEFAULT 'unpaid', -- unpaid, partial, paid
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # 采购入库明细
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_order_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                amount REAL NOT NULL,
                received_quantity INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                remarks TEXT,
                FOREIGN KEY (order_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 采购退货单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_no TEXT UNIQUE NOT NULL,
                purchase_order_id INTEGER,
                supplier_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                return_date DATE NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # 生产入库单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS production_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_no TEXT UNIQUE NOT NULL,
                warehouse_id INTEGER NOT NULL,
                production_order_no TEXT,
                total_quantity INTEGER NOT NULL,
                entry_date DATE NOT NULL,
                status TEXT DEFAULT 'pending',
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # ========== 出库管理相关表 ==========
        
        # 销售出库单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                tax_amount REAL,
                discount REAL,
                final_amount REAL NOT NULL,
                order_date DATE NOT NULL,
                delivery_date DATE,
                delivered_date DATE,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'unpaid',
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # 销售出库明细
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_order_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                amount REAL NOT NULL,
                delivered_quantity INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                remarks TEXT,
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 销售退货单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_no TEXT UNIQUE NOT NULL,
                sales_order_id INTEGER,
                customer_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                return_date DATE NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # 部门领用单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS department_usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usage_no TEXT UNIQUE NOT NULL,
                department_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                usage_date DATE NOT NULL,
                purpose TEXT,
                status TEXT DEFAULT 'pending',
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # ========== 库存管理相关表 ==========
        
        # 库存表（按仓库）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warehouse_stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                locked_quantity INTEGER DEFAULT 0,
                available_quantity INTEGER GENERATED ALWAYS AS (quantity - locked_quantity) VIRTUAL,
                min_stock INTEGER DEFAULT 0,
                max_stock INTEGER DEFAULT 0,
                average_cost REAL,
                last_in_date DATE,
                last_out_date DATE,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(warehouse_id, product_id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 库存变动记录
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_no TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL, -- purchase, sale, transfer, adjustment, etc.
                related_order TEXT,
                quantity_change INTEGER NOT NULL,
                unit_cost REAL,
                total_cost REAL,
                previous_quantity INTEGER NOT NULL,
                current_quantity INTEGER NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                operator_id INTEGER,
                remarks TEXT,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 库存盘点单
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_no TEXT UNIQUE NOT NULL,
                warehouse_id INTEGER NOT NULL,
                check_date DATE NOT NULL,
                checker_id INTEGER,
                total_items INTEGER,
                checked_items INTEGER DEFAULT 0,
                profit_amount REAL,
                loss_amount REAL,
                status TEXT DEFAULT 'pending',
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            )
        ''')
        
        # ========== 往来账款相关表 ==========
        
        # 应收款
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS receivables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receivable_no TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                source_type TEXT NOT NULL, -- sales_order, other
                source_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                received_amount REAL DEFAULT 0,
                balance_amount REAL GENERATED ALWAYS AS (amount - received_amount) VIRTUAL,
                due_date DATE,
                status TEXT DEFAULT 'unpaid',
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # 应付款
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payable_no TEXT UNIQUE NOT NULL,
                supplier_id INTEGER NOT NULL,
                source_type TEXT NOT NULL, -- purchase_order, other
                source_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                balance_amount REAL GENERATED ALWAYS AS (amount - paid_amount) VIRTUAL,
                due_date DATE,
                status TEXT DEFAULT 'unpaid',
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        
        # 收款记录
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no TEXT UNIQUE NOT NULL,
                receivable_id INTEGER,
                customer_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                bank_account TEXT,
                receipt_date DATE NOT NULL,
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receivable_id) REFERENCES receivables(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # 付款记录
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_no TEXT UNIQUE NOT NULL,
                payable_id INTEGER,
                supplier_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT,
                bank_account TEXT,
                payment_date DATE NOT NULL,
                operator_id INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (payable_id) REFERENCES payables(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')
        
        # ========== 发票管理相关表 ==========
        
        # 发票基础信息表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE NOT NULL,           -- 发票号码
                invoice_type TEXT NOT NULL,                -- 发票类型：进项/销项
                invoice_category TEXT,                     -- 发票类别：增值税专用发票、普通发票等
                invoice_date DATE NOT NULL,                -- 开票日期
                invoice_amount REAL NOT NULL,              -- 发票金额
                tax_amount REAL NOT NULL,                  -- 税额
                total_amount REAL NOT NULL,                -- 价税合计
                tax_rate REAL DEFAULT 0.13,                -- 税率
                supplier_id INTEGER,                       -- 供应商ID（进项发票）
                customer_id INTEGER,                       -- 客户ID（销项发票）
                related_order_no TEXT,                     -- 关联业务单号
                related_order_type TEXT,                   -- 关联业务类型：采购/销售
                status TEXT DEFAULT 'draft',               -- 状态：draft(草稿), submitted(已提交), verified(已审核), archived(已归档)
                payment_status TEXT DEFAULT 'unpaid',      -- 付款状态：unpaid, partial, paid
                receiver_status TEXT DEFAULT 'pending',    -- 收票状态：pending, received, lost
                issued_by TEXT,                            -- 开票方
                received_by TEXT,                          -- 收票方
                issuer_tax_no TEXT,                        -- 开票方税号
                receiver_tax_no TEXT,                      -- 收票方税号
                issuer_address TEXT,                       -- 开票方地址
                receiver_address TEXT,                     -- 收票方地址
                issuer_phone TEXT,                         -- 开票方电话
                receiver_phone TEXT,                       -- 收票方电话
                issuer_bank TEXT,                          -- 开票方开户行
                issuer_account TEXT,                       -- 开票方账号
                receiver_bank TEXT,                        -- 收票方开户行
                receiver_account TEXT,                     -- 收票方账号
                remarks TEXT,                              -- 备注
                operator_id INTEGER,                       -- 操作员
                verify_by INTEGER,                         -- 审核人
                verify_date DATE,                          -- 审核日期
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        ''')
        
        # 发票明细表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,                -- 产品名称（冗余存储）
                product_spec TEXT,                         -- 规格型号
                unit TEXT,                                 -- 单位
                quantity REAL NOT NULL,                    -- 数量
                unit_price REAL NOT NULL,                  -- 单价
                amount REAL NOT NULL,                      -- 金额
                tax_rate REAL DEFAULT 0.13,                -- 税率
                tax_amount REAL NOT NULL,                  -- 税额
                total_amount REAL NOT NULL,                -- 价税合计
                remarks TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        
        # 发票收付款记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                payment_no TEXT UNIQUE NOT NULL,           -- 付款单号
                payment_type TEXT NOT NULL,                -- 付款类型：payment(付款)/receipt(收款)
                payment_date DATE NOT NULL,                -- 付款日期
                amount REAL NOT NULL,                      -- 付款金额
                payment_method TEXT,                       -- 付款方式：现金、转账、支票等
                bank_account TEXT,                         -- 银行账号
                voucher_no TEXT,                           -- 凭证号
                operator_id INTEGER,                       -- 操作员
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        
        # 发票认证记录表（仅进项发票）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                verify_no TEXT UNIQUE NOT NULL,            -- 认证号
                verify_date DATE NOT NULL,                 -- 认证日期
                verify_status TEXT DEFAULT 'pending',      -- 认证状态
                verify_result TEXT,                        -- 认证结果
                verify_by INTEGER,                         -- 认证人
                next_verify_date DATE,                     -- 下次认证日期
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        ''')
        
        # 发票红冲记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_reversals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_invoice_id INTEGER NOT NULL,      -- 原发票ID
                reversal_invoice_id INTEGER NOT NULL,      -- 红冲发票ID
                reversal_reason TEXT NOT NULL,             -- 红冲原因
                reversal_date DATE NOT NULL,               -- 红冲日期
                operator_id INTEGER,                       -- 操作员
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (original_invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (reversal_invoice_id) REFERENCES invoices(id)
            )
        ''')
        
        # ========== 系统表 ==========
        
        # 账套管理
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_name TEXT UNIQUE NOT NULL,
                company_name TEXT,
                start_date DATE,
                end_date DATE,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 系统日志
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT NOT NULL,
                action_detail TEXT,
                ip_address TEXT,
                log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 初始化默认数据
        self.init_default_data()
        
        self.conn.commit()
    
    def init_default_data(self):
        """初始化默认数据"""
        # 检查是否已有管理员用户
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if self.cursor.fetchone()[0] == 0:
            # 创建默认管理员用户
            password_hash = hashlib.md5('admin123'.encode()).hexdigest()
            self.cursor.execute('''
                INSERT INTO users (username, password, realname, role, status)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', password_hash, '系统管理员', 'admin', 'active'))
        
        # 检查是否已有默认角色
        self.cursor.execute("SELECT COUNT(*) FROM roles WHERE role_name = 'admin'")
        if self.cursor.fetchone()[0] == 0:
            # 创建默认角色
            admin_permissions = {
                'user_management': True,
                'product_management': True,
                'purchase_management': True,
                'sales_management': True,
                'inventory_management': True,
                'report_view': True,
                'financial_management': True,
                'system_settings': True,
                'invoice_management': True
            }
            
            self.cursor.execute('''
                INSERT INTO roles (role_name, permissions, description)
                VALUES (?, ?, ?)
            ''', ('admin', json.dumps(admin_permissions), '系统管理员'))
            
            user_permissions = {
                'product_management': True,
                'purchase_management': False,
                'sales_management': True,
                'inventory_management': True,
                'report_view': True,
                'financial_management': False,
                'system_settings': False,
                'invoice_management': True
            }
            
            self.cursor.execute('''
                INSERT INTO roles (role_name, permissions, description)
                VALUES (?, ?, ?)
            ''', ('user', json.dumps(user_permissions), '普通用户'))
        
        # 检查是否已有默认仓库
        self.cursor.execute("SELECT COUNT(*) FROM warehouses WHERE code = 'WH001'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO warehouses (code, name, location, capacity)
                VALUES (?, ?, ?, ?)
            ''', ('WH001', '主仓库', '公司总部', 10000))
        
        # 检查是否已有默认部门
        self.cursor.execute("SELECT COUNT(*) FROM departments WHERE code = 'DEPT001'")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute('''
                INSERT INTO departments (code, name)
                VALUES (?, ?)
            ''', ('DEPT001', '办公室'))
        
        self.conn.commit()
    
    def show_login(self):
        """显示登录界面"""
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("系统登录")
        self.login_window.geometry("400x300")
        self.login_window.resizable(False, False)
        self.login_window.transient(self.root)
        self.login_window.grab_set()
        
        # 居中显示
        self.login_window.update_idletasks()
        width = self.login_window.winfo_width()
        height = self.login_window.winfo_height()
        x = (self.login_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.login_window.winfo_screenheight() // 2) - (height // 2)
        self.login_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # 登录界面内容
        title_label = tk.Label(self.login_window, text="进销存管理系统", 
                               font=("微软雅黑", 20, "bold"), fg="#2c3e50")
        title_label.pack(pady=30)
        
        # 用户名
        tk.Label(self.login_window, text="用户名:", font=("微软雅黑", 12)).pack()
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(self.login_window, textvariable=self.username_var, 
                                 font=("微软雅黑", 12), width=25)
        username_entry.pack(pady=5)
        username_entry.insert(0, "admin")
        
        # 密码
        tk.Label(self.login_window, text="密码:", font=("微软雅黑", 12)).pack()
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(self.login_window, textvariable=self.password_var, 
                                 font=("微软雅黑", 12), width=25, show="*")
        password_entry.pack(pady=5)
        password_entry.insert(0, "admin123")
        
        # 登录按钮
        login_button = tk.Button(self.login_window, text="登录", 
                                command=self.do_login,
                                font=("微软雅黑", 12), bg="#3498db", fg="white",
                                width=15, height=1)
        login_button.pack(pady=20)
        
        # 绑定回车键
        self.login_window.bind('<Return>', lambda event: self.do_login())
        
        # 默认焦点
        username_entry.focus_set()
    
    def do_login(self):
        """执行登录"""
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showwarning("警告", "请输入用户名和密码！")
            return
        
        # 验证用户
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        self.cursor.execute('''
            SELECT id, username, realname, role, status FROM users 
            WHERE username = ? AND password = ? AND status = 'active'
        ''', (username, password_hash))
        
        user = self.cursor.fetchone()
        
        if user:
            # 登录成功
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'realname': user[2],
                'role': user[3]
            }
            self.current_role = user[3]
            
            # 更新最后登录时间
            self.cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (user[0],))
            self.conn.commit()
            
            # 记录日志
            self.log_action('login', f'用户 {username} 登录系统')
            
            # 关闭登录窗口
            self.login_window.destroy()
            
            # 创建主界面
            self.create_main_interface()
            
        else:
            messagebox.showerror("错误", "用户名或密码错误！")
    
    def create_main_interface(self):
        """创建主界面"""
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 系统菜单
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="系统", menu=system_menu)
        system_menu.add_command(label="用户管理", command=self.show_user_management)
        system_menu.add_command(label="角色管理", command=self.show_role_management)
        system_menu.add_command(label="系统备份", command=self.backup_system)
        system_menu.add_command(label="数据清理", command=self.clean_data)
        system_menu.add_separator()
        system_menu.add_command(label="退出系统", command=self.on_closing)
        
        # 基础数据菜单
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="基础数据", menu=data_menu)
        data_menu.add_command(label="产品管理", command=lambda: self.show_tab("产品管理"))
        data_menu.add_command(label="供应商管理", command=lambda: self.show_tab("供应商管理"))
        data_menu.add_command(label="客户管理", command=lambda: self.show_tab("客户管理"))
        data_menu.add_command(label="仓库管理", command=lambda: self.show_tab("仓库管理"))
        data_menu.add_command(label="部门管理", command=lambda: self.show_tab("部门管理"))
        
        # 入库管理菜单
        in_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="入库管理", menu=in_menu)
        in_menu.add_command(label="采购入库", command=lambda: self.show_tab("采购入库"))
        in_menu.add_command(label="采购退货", command=lambda: self.show_tab("采购退货"))
        in_menu.add_command(label="生产入库", command=lambda: self.show_tab("生产入库"))
        in_menu.add_separator()
        in_menu.add_command(label="入库统计", command=lambda: self.show_tab("入库统计"))
        in_menu.add_command(label="退货统计", command=lambda: self.show_tab("退货统计"))
        
        # 出库管理菜单
        out_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="出库管理", menu=out_menu)
        out_menu.add_command(label="销售出库", command=lambda: self.show_tab("销售出库"))
        out_menu.add_command(label="销售退货", command=lambda: self.show_tab("销售退货"))
        out_menu.add_command(label="部门领用", command=lambda: self.show_tab("部门领用"))
        out_menu.add_command(label="部门退回", command=lambda: self.show_tab("部门退回"))
        out_menu.add_separator()
        out_menu.add_command(label="出库统计", command=lambda: self.show_tab("出库统计"))
        out_menu.add_command(label="退库统计", command=lambda: self.show_tab("退库统计"))
        
        # 库存管理菜单
        stock_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="库存管理", menu=stock_menu)
        stock_menu.add_command(label="库存查询", command=lambda: self.show_tab("库存查询"))
        stock_menu.add_command(label="库存盘点", command=lambda: self.show_tab("库存盘点"))
        stock_menu.add_command(label="库存报警", command=lambda: self.show_tab("库存报警"))
        
        # 统计报表菜单
        report_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="统计报表", menu=report_menu)
        report_menu.add_command(label="进销存明细", command=lambda: self.show_tab("进销存明细"))
        report_menu.add_command(label="进销存汇总", command=lambda: self.show_tab("进销存汇总"))
        report_menu.add_command(label="收货对账单", command=lambda: self.show_tab("收货对账单"))
        report_menu.add_command(label="发货对账单", command=lambda: self.show_tab("发货对账单"))
        report_menu.add_command(label="发货成本", command=lambda: self.show_tab("发货成本"))
        report_menu.add_command(label="销售毛利", command=lambda: self.show_tab("销售毛利"))
        
        # 往来账款菜单
        finance_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="往来账款", menu=finance_menu)
        finance_menu.add_command(label="应收登记", command=lambda: self.show_tab("应收登记"))
        finance_menu.add_command(label="应付登记", command=lambda: self.show_tab("应付登记"))
        finance_menu.add_command(label="收款登记", command=lambda: self.show_tab("收款登记"))
        finance_menu.add_command(label="付款登记", command=lambda: self.show_tab("付款登记"))
        finance_menu.add_separator()
        finance_menu.add_command(label="应收帐表", command=lambda: self.show_tab("应收帐表"))
        finance_menu.add_command(label="应付帐表", command=lambda: self.show_tab("应付帐表"))
        
        # 发票管理菜单（新增）
        invoice_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="发票管理", menu=invoice_menu)
        invoice_menu.add_command(label="进项发票管理", command=lambda: self.show_tab("进项发票管理"))
        invoice_menu.add_command(label="销售发票管理", command=lambda: self.show_tab("销售发票管理"))
        invoice_menu.add_separator()
        invoice_menu.add_command(label="发票认证管理", command=lambda: self.show_tab("发票认证管理"))
        invoice_menu.add_command(label="发票红冲管理", command=lambda: self.show_tab("发票红冲管理"))
        invoice_menu.add_separator()
        invoice_menu.add_command(label="发票统计报表", command=lambda: self.show_tab("发票统计报表"))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标题栏
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame, 
            text="完整进销存管理系统（含发票管理）", 
            font=("微软雅黑", 24, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(side=tk.LEFT)
        
        # 用户信息
        user_info = tk.Label(
            title_frame,
            text=f"当前用户: {self.current_user['realname']} ({self.current_user['role']})",
            font=("微软雅黑", 10),
            fg="#7f8c8d"
        )
        user_info.pack(side=tk.RIGHT, padx=10)
        
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
        
        # 创建仪表盘标签页
        self.create_dashboard_tab()
        
        # 状态栏
        self.status_bar = tk.Label(
            self.root, 
            text="就绪", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=("微软雅黑", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 更新仪表盘数据
        self.update_dashboard_stats()
    
    def show_tab(self, tab_name):
        """显示指定标签页"""
        # 检查标签页是否已存在
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == tab_name:
                self.notebook.select(i)
                return
        
        # 创建标签页
        if tab_name == "产品管理":
            self.create_product_tab()
        elif tab_name == "供应商管理":
            self.create_supplier_tab()
        elif tab_name == "客户管理":
            self.create_customer_tab()
        elif tab_name == "仓库管理":
            self.create_warehouse_tab()
        elif tab_name == "部门管理":
            self.create_department_tab()
        elif tab_name == "进项发票管理":
            self.create_purchase_invoice_tab()
        elif tab_name == "销售发票管理":
            self.create_sales_invoice_tab()
        elif tab_name == "发票认证管理":
            self.create_invoice_verification_tab()
        elif tab_name == "发票红冲管理":
            self.create_invoice_reversal_tab()
        elif tab_name == "发票统计报表":
            self.create_invoice_report_tab()
        # 其他标签页创建函数...
        else:
            # 创建默认标签页
            self.create_default_tab(tab_name)
    
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
            {"title": "产品总数", "value": "0", "color": "#3498db", "icon": "📦", "key": "products"},
            {"title": "总库存量", "value": "0", "color": "#2ecc71", "icon": "📊", "key": "stock"},
            {"title": "今日销售", "value": "¥0", "color": "#9b59b6", "icon": "💰", "key": "today_sales"},
            {"title": "今日采购", "value": "¥0", "color": "#e67e22", "icon": "🛒", "key": "today_purchase"},
            {"title": "应收余额", "value": "¥0", "color": "#e74c3c", "icon": "📈", "key": "receivable"},
            {"title": "应付余额", "value": "¥0", "color": "#f39c12", "icon": "📉", "key": "payable"},
            {"title": "本月进项发票", "value": "¥0", "color": "#1abc9c", "icon": "🧾", "key": "purchase_invoices"},
            {"title": "本月销项发票", "value": "¥0", "color": "#d35400", "icon": "📋", "key": "sales_invoices"},
        ]
        
        self.stat_cards = []
        
        for i, stat in enumerate(stats_data):
            card = tk.Frame(stats_frame, bg=stat["color"], relief=tk.RAISED, bd=2)
            card.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="nsew")
            stats_frame.columnconfigure(i%4, weight=1)
            stats_frame.rowconfigure(i//4, weight=1)
            
            # 图标
            icon_label = tk.Label(card, text=stat["icon"], font=("Arial", 24), bg=stat["color"])
            icon_label.pack(side=tk.LEFT, padx=10, pady=10)
            
            # 数值和标题
            content_frame = tk.Frame(card, bg=stat["color"])
            content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
            
            value_label = tk.Label(
                content_frame, 
                text=stat["value"], 
                font=("微软雅黑", 16, "bold"), 
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
            
            self.stat_cards.append({"frame": card, "value_label": value_label, "key": stat["key"]})
        
        # 快速操作区域
        quick_actions_frame = ttk.LabelFrame(dashboard_frame, text="快速操作", padding=10)
        quick_actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 快速操作按钮
        quick_actions = [
            ("📦 采购入库", lambda: self.show_tab("采购入库")),
            ("💰 销售出库", lambda: self.show_tab("销售出库")),
            ("🧾 进项发票", lambda: self.show_tab("进项发票管理")),
            ("📋 销项发票", lambda: self.show_tab("销售发票管理")),
            ("📊 库存查询", lambda: self.show_tab("库存查询")),
            ("📈 销售报表", lambda: self.show_tab("销售毛利")),
            ("⚠️ 库存报警", lambda: self.show_tab("库存报警")),
            ("📋 今日订单", self.show_today_orders),
        ]
        
        for i, (text, command) in enumerate(quick_actions):
            btn = ttk.Button(
                quick_actions_frame, 
                text=text, 
                command=command,
                style='Primary.TButton',
                width=20
            )
            btn.grid(row=i//4, column=i%4, padx=10, pady=10, sticky="ew")
            quick_actions_frame.columnconfigure(i%4, weight=1)
        
        # 库存预警区域
        alert_frame = ttk.LabelFrame(dashboard_frame, text="库存预警", padding=10)
        alert_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建表格显示库存预警
        columns = ("产品", "仓库", "当前库存", "最低库存", "状态")
        self.alert_tree = ttk.Treeview(alert_frame, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.alert_tree.heading(col, text=col)
            self.alert_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(alert_frame, orient="vertical", command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=scrollbar.set)
        
        self.alert_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载库存预警
        self.load_stock_alerts()
    
    def update_dashboard_stats(self):
        """更新仪表盘统计数据"""
        # 产品总数
        self.cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
        total_products = self.cursor.fetchone()[0] or 0
        
        # 总库存量
        self.cursor.execute("SELECT SUM(quantity) FROM warehouse_stocks")
        total_stock = self.cursor.fetchone()[0] or 0
        
        # 今日销售额
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT SUM(final_amount) FROM sales_orders WHERE order_date = ? AND status = 'completed'", (today,))
        today_sales = self.cursor.fetchone()[0] or 0
        
        # 今日采购额
        self.cursor.execute("SELECT SUM(final_amount) FROM purchase_orders WHERE order_date = ? AND status = 'completed'", (today,))
        today_purchase = self.cursor.fetchone()[0] or 0
        
        # 应收余额
        self.cursor.execute("SELECT SUM(balance_amount) FROM receivables WHERE status = 'unpaid'")
        receivable_balance = self.cursor.fetchone()[0] or 0
        
        # 应付余额
        self.cursor.execute("SELECT SUM(balance_amount) FROM payables WHERE status = 'unpaid'")
        payable_balance = self.cursor.fetchone()[0] or 0
        
        # 本月进项发票金额
        current_month = datetime.now().strftime("%Y-%m")
        self.cursor.execute('''
            SELECT SUM(total_amount) FROM invoices 
            WHERE invoice_type = '进项' 
              AND strftime('%Y-%m', invoice_date) = ? 
              AND status != 'draft'
        ''', (current_month,))
        month_purchase_invoices = self.cursor.fetchone()[0] or 0
        
        # 本月销项发票金额
        self.cursor.execute('''
            SELECT SUM(total_amount) FROM invoices 
            WHERE invoice_type = '销项' 
              AND strftime('%Y-%m', invoice_date) = ? 
              AND status != 'draft'
        ''', (current_month,))
        month_sales_invoices = self.cursor.fetchone()[0] or 0
        
        # 更新卡片
        for card in self.stat_cards:
            if card["key"] == "products":
                card["value_label"].config(text=str(total_products))
            elif card["key"] == "stock":
                card["value_label"].config(text=str(total_stock))
            elif card["key"] == "today_sales":
                card["value_label"].config(text=f"¥{today_sales:.2f}")
            elif card["key"] == "today_purchase":
                card["value_label"].config(text=f"¥{today_purchase:.2f}")
            elif card["key"] == "receivable":
                card["value_label"].config(text=f"¥{receivable_balance:.2f}")
            elif card["key"] == "payable":
                card["value_label"].config(text=f"¥{payable_balance:.2f}")
            elif card["key"] == "purchase_invoices":
                card["value_label"].config(text=f"¥{month_purchase_invoices:.2f}")
            elif card["key"] == "sales_invoices":
                card["value_label"].config(text=f"¥{month_sales_invoices:.2f}")
        
        # 每30秒更新一次
        self.root.after(30000, self.update_dashboard_stats)
    
    def load_stock_alerts(self):
        """加载库存预警"""
        # 清空表格
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)
        
        # 查询库存不足的产品
        self.cursor.execute('''
            SELECT p.name, w.name, ws.quantity, ws.min_stock,
                   CASE 
                       WHEN ws.quantity <= 0 THEN '缺货'
                       WHEN ws.quantity < ws.min_stock THEN '库存不足'
                       ELSE '正常'
                   END as status
            FROM warehouse_stocks ws
            JOIN products p ON ws.product_id = p.id
            JOIN warehouses w ON ws.warehouse_id = w.id
            WHERE ws.quantity < ws.min_stock OR ws.quantity <= 0
            ORDER BY ws.quantity ASC
            LIMIT 10
        ''')
        
        alerts = self.cursor.fetchall()
        
        for alert in alerts:
            self.alert_tree.insert("", "end", values=alert)
    
    # ========== 发票管理功能 ==========
    
    def create_purchase_invoice_tab(self):
        """创建进项发票管理标签页"""
        invoice_frame = ttk.Frame(self.notebook)
        self.notebook.add(invoice_frame, text="进项发票管理")
        
        # 创建工具栏
        toolbar = ttk.Frame(invoice_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        # 工具栏按钮
        ttk.Button(toolbar, text="新增发票", command=self.add_purchase_invoice, 
                   style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="修改发票", command=self.edit_purchase_invoice, 
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除发票", command=self.delete_purchase_invoice, 
                   style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="审核发票", command=self.verify_purchase_invoice, 
                   style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="认证发票", command=self.certify_purchase_invoice,
                   style='Info.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="付款登记", command=self.register_purchase_payment).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出Excel", command=self.export_purchase_invoices).pack(side=tk.LEFT, padx=5)
        
        # 搜索区域
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.purchase_invoice_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.purchase_invoice_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.load_purchase_invoices())
        
        # 筛选条件
        ttk.Label(search_frame, text="状态:").pack(side=tk.LEFT, padx=5)
        self.purchase_invoice_status_var = tk.StringVar(value="全部")
        status_combo = ttk.Combobox(search_frame, textvariable=self.purchase_invoice_status_var, 
                                    values=["全部", "草稿", "已提交", "已审核", "已归档"], width=10)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.load_purchase_invoices())
        
        # 发票表格
        tree_frame = ttk.Frame(invoice_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 创建表格
        columns = ("发票号码", "开票日期", "供应商", "发票金额", "税额", "价税合计", 
                   "状态", "付款状态", "收票状态", "关联单号", "操作员")
        self.purchase_invoice_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        column_widths = {
            "发票号码": 120,
            "开票日期": 100,
            "供应商": 150,
            "发票金额": 100,
            "税额": 80,
            "价税合计": 100,
            "状态": 80,
            "付款状态": 80,
            "收票状态": 80,
            "关联单号": 120,
            "操作员": 80
        }
        
        for col in columns:
            self.purchase_invoice_tree.heading(col, text=col)
            self.purchase_invoice_tree.column(col, width=column_widths.get(col, 100))
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.purchase_invoice_tree.yview)
        self.purchase_invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        self.purchase_invoice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.purchase_invoice_tree.bind('<<TreeviewSelect>>', self.on_purchase_invoice_select)
        
        # 状态栏
        self.purchase_invoice_stats_frame = ttk.Frame(invoice_frame)
        self.purchase_invoice_stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 统计信息
        stats_labels = [
            ("发票总数:", "total_count"),
            ("发票总额:", "total_amount"),
            ("已认证:", "verified_count"),
            ("待付款:", "unpaid_amount"),
        ]
        
        self.purchase_invoice_stats_vars = {}
        
        for i, (label, key) in enumerate(stats_labels):
            ttk.Label(self.purchase_invoice_stats_frame, text=label).grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value="0")
            ttk.Label(self.purchase_invoice_stats_frame, textvariable=var, 
                     font=("微软雅黑", 10, "bold")).grid(row=0, column=i*2+1, padx=(0, 20), pady=5, sticky="w")
            self.purchase_invoice_stats_vars[key] = var
        
        # 加载数据
        self.load_purchase_invoices()
    
    def load_purchase_invoices(self):
        """加载进项发票数据"""
        # 清空表格
        for item in self.purchase_invoice_tree.get_children():
            self.purchase_invoice_tree.delete(item)
        
        # 构建查询条件
        search_term = self.purchase_invoice_search_var.get()
        status_filter = self.purchase_invoice_status_var.get()
        
        conditions = ["invoice_type = '进项'"]
        params = []
        
        if search_term:
            conditions.append("(invoice_no LIKE ? OR related_order_no LIKE ?)")
            params.append(f'%{search_term}%')
            params.append(f'%{search_term}%')
        
        if status_filter != "全部":
            status_map = {"草稿": "draft", "已提交": "submitted", "已审核": "verified", "已归档": "archived"}
            if status_filter in status_map:
                conditions.append("status = ?")
                params.append(status_map[status_filter])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 执行查询
        query = f'''
            SELECT 
                i.invoice_no,
                i.invoice_date,
                COALESCE(s.name, '') as supplier_name,
                i.invoice_amount,
                i.tax_amount,
                i.total_amount,
                CASE i.status
                    WHEN 'draft' THEN '草稿'
                    WHEN 'submitted' THEN '已提交'
                    WHEN 'verified' THEN '已审核'
                    WHEN 'archived' THEN '已归档'
                    ELSE i.status
                END as status,
                CASE i.payment_status
                    WHEN 'unpaid' THEN '未付款'
                    WHEN 'partial' THEN '部分付款'
                    WHEN 'paid' THEN '已付款'
                    ELSE i.payment_status
                END as payment_status,
                CASE i.receiver_status
                    WHEN 'pending' THEN '待收票'
                    WHEN 'received' THEN '已收票'
                    WHEN 'lost' THEN '发票遗失'
                    ELSE i.receiver_status
                END as receiver_status,
                COALESCE(i.related_order_no, ''),
                COALESCE(u.realname, '')
            FROM invoices i
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            LEFT JOIN users u ON i.operator_id = u.id
            WHERE {where_clause}
            ORDER BY i.invoice_date DESC, i.invoice_no DESC
            LIMIT 200
        '''
        
        self.cursor.execute(query, params)
        invoices = self.cursor.fetchall()
        
        # 填充数据
        for invoice in invoices:
            self.purchase_invoice_tree.insert("", "end", values=invoice)
        
        # 更新统计信息
        self.update_purchase_invoice_stats()
    
    def update_purchase_invoice_stats(self):
        """更新进项发票统计信息"""
        # 发票总数
        self.cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_type = '进项'")
        total_count = self.cursor.fetchone()[0] or 0
        self.purchase_invoice_stats_vars["total_count"].set(str(total_count))
        
        # 发票总额
        self.cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE invoice_type = '进项' AND status != 'draft'")
        total_amount = self.cursor.fetchone()[0] or 0
        self.purchase_invoice_stats_vars["total_amount"].set(f"¥{total_amount:,.2f}")
        
        # 已认证发票数
        self.cursor.execute('''
            SELECT COUNT(DISTINCT i.id) 
            FROM invoices i
            JOIN invoice_verifications v ON i.id = v.invoice_id
            WHERE i.invoice_type = '进项' AND v.verify_status = 'success'
        ''')
        verified_count = self.cursor.fetchone()[0] or 0
        self.purchase_invoice_stats_vars["verified_count"].set(str(verified_count))
        
        # 待付款金额
        self.cursor.execute('''
            SELECT SUM(i.total_amount - COALESCE(SUM(p.amount), 0)) 
            FROM invoices i
            LEFT JOIN invoice_payments p ON i.id = p.invoice_id AND p.payment_type = 'payment'
            WHERE i.invoice_type = '进项' AND i.status != 'draft'
            GROUP BY i.id
            HAVING i.total_amount > COALESCE(SUM(p.amount), 0)
        ''')
        unpaid_result = self.cursor.fetchone()
        unpaid_amount = unpaid_result[0] if unpaid_result else 0
        self.purchase_invoice_stats_vars["unpaid_amount"].set(f"¥{unpaid_amount:,.2f}")
    
    def on_purchase_invoice_select(self, event):
        """进项发票选择事件"""
        selection = self.purchase_invoice_tree.selection()
        if not selection:
            return
        
        item = self.purchase_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        # 可以在这里实现显示发票详情的功能
        self.status_bar.config(text=f"选中发票: {invoice_no}")
    
    def add_purchase_invoice(self):
        """新增进项发票"""
        # 创建新增发票窗口
        add_window = tk.Toplevel(self.root)
        add_window.title("新增进项发票")
        add_window.geometry("800x600")
        add_window.resizable(True, True)
        add_window.transient(self.root)
        add_window.grab_set()
        
        # 创建表单
        form_frame = ttk.Frame(add_window)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 发票基本信息
        ttk.Label(form_frame, text="发票号码:", font=("微软雅黑", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=10)
        self.new_invoice_no_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_invoice_no_var, width=30).grid(row=0, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="开票日期:", font=("微软雅黑", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=10)
        self.new_invoice_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=self.new_invoice_date_var, width=30).grid(row=1, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="供应商:", font=("微软雅黑", 10)).grid(row=2, column=0, sticky="e", padx=5, pady=10)
        self.new_supplier_var = tk.StringVar()
        
        # 加载供应商列表
        self.cursor.execute("SELECT id, name FROM suppliers WHERE status = 'active' ORDER BY name")
        suppliers = self.cursor.fetchall()
        supplier_names = [s[1] for s in suppliers]
        
        supplier_combo = ttk.Combobox(form_frame, textvariable=self.new_supplier_var, values=supplier_names, width=28)
        supplier_combo.grid(row=2, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="发票金额:", font=("微软雅黑", 10)).grid(row=3, column=0, sticky="e", padx=5, pady=10)
        self.new_invoice_amount_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.new_invoice_amount_var, width=30).grid(row=3, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="税额:", font=("微软雅黑", 10)).grid(row=4, column=0, sticky="e", padx=5, pady=10)
        self.new_tax_amount_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.new_tax_amount_var, width=30).grid(row=4, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="价税合计:", font=("微软雅黑", 10)).grid(row=5, column=0, sticky="e", padx=5, pady=10)
        self.new_total_amount_var = tk.StringVar(value="0.00")
        ttk.Entry(form_frame, textvariable=self.new_total_amount_var, width=30).grid(row=5, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="税率(%):", font=("微软雅黑", 10)).grid(row=6, column=0, sticky="e", padx=5, pady=10)
        self.new_tax_rate_var = tk.StringVar(value="13")
        ttk.Entry(form_frame, textvariable=self.new_tax_rate_var, width=30).grid(row=6, column=1, sticky="w", padx=5, pady=10)
        
        ttk.Label(form_frame, text="备注:", font=("微软雅黑", 10)).grid(row=7, column=0, sticky="ne", padx=5, pady=10)
        self.new_remarks_text = tk.Text(form_frame, height=4, width=40)
        self.new_remarks_text.grid(row=7, column=1, sticky="w", padx=5, pady=10)
        
        # 按钮区域
        button_frame = ttk.Frame(add_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="保存为草稿", 
                   command=lambda: self.save_purchase_invoice('draft', add_window),
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存并提交", 
                   command=lambda: self.save_purchase_invoice('submitted', add_window),
                   style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", 
                   command=add_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_purchase_invoice(self, status, window):
        """保存进项发票"""
        try:
            invoice_no = self.new_invoice_no_var.get()
            invoice_date = self.new_invoice_date_var.get()
            supplier_name = self.new_supplier_var.get()
            
            # 验证必填字段
            if not invoice_no or not invoice_date:
                messagebox.showwarning("警告", "发票号码和开票日期不能为空！")
                return
            
            # 检查发票号码是否重复
            self.cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,))
            if self.cursor.fetchone():
                messagebox.showwarning("警告", "发票号码已存在！")
                return
            
            # 获取供应商ID
            supplier_id = None
            if supplier_name:
                self.cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier_name,))
                supplier = self.cursor.fetchone()
                if supplier:
                    supplier_id = supplier[0]
            
            # 获取金额
            invoice_amount = float(self.new_invoice_amount_var.get() or 0)
            tax_amount = float(self.new_tax_amount_var.get() or 0)
            total_amount = float(self.new_total_amount_var.get() or 0)
            tax_rate = float(self.new_tax_rate_var.get() or 13)
            
            # 获取备注
            remarks = self.new_remarks_text.get("1.0", tk.END).strip()
            
            # 插入数据库
            self.cursor.execute('''
                INSERT INTO invoices (
                    invoice_no, invoice_type, invoice_date, invoice_amount,
                    tax_amount, total_amount, tax_rate, supplier_id,
                    status, receiver_status, remarks, operator_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_no,
                '进项',
                invoice_date,
                invoice_amount,
                tax_amount,
                total_amount,
                tax_rate,
                supplier_id,
                status,
                'pending',  # 默认待收票
                remarks,
                self.current_user['id']
            ))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", f"发票保存成功！状态：{'草稿' if status == 'draft' else '已提交'}")
            window.destroy()
            self.load_purchase_invoices()
            
            # 记录日志
            self.log_action('add_invoice', f"新增进项发票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存发票失败：{str(e)}")
    
    def edit_purchase_invoice(self):
        """编辑进项发票"""
        selection = self.purchase_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.purchase_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        # 这里实现编辑发票的功能
        messagebox.showinfo("提示", f"编辑发票: {invoice_no}\n此功能需要进一步实现")
    
    def delete_purchase_invoice(self):
        """删除进项发票"""
        selection = self.purchase_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.purchase_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        if not messagebox.askyesno("确认", f"确定要删除发票 {invoice_no} 吗？"):
            return
        
        try:
            self.cursor.execute("DELETE FROM invoices WHERE invoice_no = ?", (invoice_no,))
            self.conn.commit()
            
            messagebox.showinfo("成功", "发票删除成功！")
            self.load_purchase_invoices()
            
            # 记录日志
            self.log_action('delete_invoice', f"删除进项发票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除发票失败：{str(e)}")
    
    def verify_purchase_invoice(self):
        """审核进项发票"""
        selection = self.purchase_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.purchase_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        # 更新发票状态为已审核
        try:
            self.cursor.execute('''
                UPDATE invoices 
                SET status = 'verified', verify_date = ?, verify_by = ?
                WHERE invoice_no = ?
            ''', (datetime.now().strftime("%Y-%m-%d"), self.current_user['id'], invoice_no))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", f"发票 {invoice_no} 审核通过！")
            self.load_purchase_invoices()
            
            # 记录日志
            self.log_action('verify_invoice', f"审核进项发票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"审核发票失败：{str(e)}")
    
    def certify_purchase_invoice(self):
        """认证进项发票"""
        selection = self.purchase_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.purchase_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        # 获取发票ID
        self.cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,))
        invoice = self.cursor.fetchone()
        
        if not invoice:
            messagebox.showerror("错误", "未找到该发票！")
            return
        
        invoice_id = invoice[0]
        
        # 创建认证记录
        try:
            self.cursor.execute('''
                INSERT INTO invoice_verifications (
                    invoice_id, verify_no, verify_date, verify_status, verify_by
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                invoice_id,
                f"VFY{datetime.now().strftime('%Y%m%d%H%M%S')}",
                datetime.now().strftime("%Y-%m-%d"),
                "success",
                self.current_user['id']
            ))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", f"发票 {invoice_no} 认证成功！")
            self.load_purchase_invoices()
            
            # 记录日志
            self.log_action('certify_invoice', f"认证进项发票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"认证发票失败：{str(e)}")
    
    def register_purchase_payment(self):
        """登记付款"""
        selection = self.purchase_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.purchase_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        total_amount = float(item['values'][5])
        
        # 获取发票ID
        self.cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,))
        invoice = self.cursor.fetchone()
        
        if not invoice:
            messagebox.showerror("错误", "未找到该发票！")
            return
        
        invoice_id = invoice[0]
        
        # 创建付款登记窗口
        payment_window = tk.Toplevel(self.root)
        payment_window.title("付款登记")
        payment_window.geometry("400x300")
        payment_window.resizable(False, False)
        payment_window.transient(self.root)
        payment_window.grab_set()
        
        ttk.Label(payment_window, text=f"发票号码: {invoice_no}", font=("微软雅黑", 10, "bold")).pack(pady=10)
        ttk.Label(payment_window, text=f"应付金额: ¥{total_amount:,.2f}", font=("微软雅黑", 10)).pack(pady=5)
        
        ttk.Label(payment_window, text="付款金额:").pack(pady=5)
        payment_amount_var = tk.StringVar(value=str(total_amount))
        ttk.Entry(payment_window, textvariable=payment_amount_var, width=20).pack(pady=5)
        
        ttk.Label(payment_window, text="付款日期:").pack(pady=5)
        payment_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(payment_window, textvariable=payment_date_var, width=20).pack(pady=5)
        
        ttk.Label(payment_window, text="付款方式:").pack(pady=5)
        payment_method_var = tk.StringVar(value="转账")
        payment_method_combo = ttk.Combobox(payment_window, textvariable=payment_method_var, 
                                            values=["转账", "现金", "支票", "其他"], width=17)
        payment_method_combo.pack(pady=5)
        
        def save_payment():
            try:
                payment_amount = float(payment_amount_var.get())
                payment_date = payment_date_var.get()
                payment_method = payment_method_var.get()
                
                # 创建付款记录
                self.cursor.execute('''
                    INSERT INTO invoice_payments (
                        invoice_id, payment_no, payment_type, payment_date,
                        amount, payment_method, operator_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id,
                    f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "payment",
                    payment_date,
                    payment_amount,
                    payment_method,
                    self.current_user['id']
                ))
                
                # 更新发票付款状态
                # 计算已付款总额
                self.cursor.execute('''
                    SELECT SUM(amount) FROM invoice_payments 
                    WHERE invoice_id = ? AND payment_type = 'payment'
                ''', (invoice_id,))
                total_paid = self.cursor.fetchone()[0] or 0
                
                # 更新付款状态
                if total_paid >= total_amount:
                    payment_status = "paid"
                elif total_paid > 0:
                    payment_status = "partial"
                else:
                    payment_status = "unpaid"
                
                self.cursor.execute('''
                    UPDATE invoices SET payment_status = ? WHERE id = ?
                ''', (payment_status, invoice_id))
                
                self.conn.commit()
                
                messagebox.showinfo("成功", "付款登记成功！")
                payment_window.destroy()
                self.load_purchase_invoices()
                
                # 记录日志
                self.log_action('register_payment', f"登记付款: 发票 {invoice_no}, 金额 ¥{payment_amount}")
                
            except Exception as e:
                messagebox.showerror("错误", f"付款登记失败：{str(e)}")
        
        ttk.Button(payment_window, text="保存", command=save_payment, 
                   style='Success.TButton').pack(pady=20)
    
    def export_purchase_invoices(self):
        """导出进项发票"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 查询所有进项发票
            self.cursor.execute('''
                SELECT 
                    i.invoice_no,
                    i.invoice_date,
                    COALESCE(s.name, '') as supplier_name,
                    i.invoice_amount,
                    i.tax_amount,
                    i.total_amount,
                    CASE i.status
                        WHEN 'draft' THEN '草稿'
                        WHEN 'submitted' THEN '已提交'
                        WHEN 'verified' THEN '已审核'
                        WHEN 'archived' THEN '已归档'
                        ELSE i.status
                    END as status,
                    CASE i.payment_status
                        WHEN 'unpaid' THEN '未付款'
                        WHEN 'partial' THEN '部分付款'
                        WHEN 'paid' THEN '已付款'
                        ELSE i.payment_status
                    END as payment_status,
                    i.related_order_no,
                    COALESCE(u.realname, '') as operator
                FROM invoices i
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                LEFT JOIN users u ON i.operator_id = u.id
                WHERE i.invoice_type = '进项'
                ORDER BY i.invoice_date DESC
            ''')
            
            invoices = self.cursor.fetchall()
            
            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['发票号码', '开票日期', '供应商', '发票金额', '税额', '价税合计', 
                               '状态', '付款状态', '关联单号', '操作员'])
                writer.writerows(invoices)
            
            messagebox.showinfo("成功", f"数据已导出到：{file_path}")
            
            # 记录日志
            self.log_action('export_invoices', "导出进项发票数据")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def create_sales_invoice_tab(self):
        """创建销售发票管理标签页"""
        invoice_frame = ttk.Frame(self.notebook)
        self.notebook.add(invoice_frame, text="销售发票管理")
        
        # 创建工具栏
        toolbar = ttk.Frame(invoice_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar, text="新增发票", command=self.add_sales_invoice, 
                   style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="修改发票", command=self.edit_sales_invoice, 
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除发票", command=self.delete_sales_invoice, 
                   style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="审核发票", command=self.verify_sales_invoice, 
                   style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="开票确认", command=self.confirm_issue_sales_invoice,
                   style='Info.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="收款登记", command=self.register_sales_payment).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出Excel", command=self.export_sales_invoices).pack(side=tk.LEFT, padx=5)
        
        # 搜索区域
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.sales_invoice_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.sales_invoice_search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.load_sales_invoices())
        
        # 筛选条件
        ttk.Label(search_frame, text="状态:").pack(side=tk.LEFT, padx=5)
        self.sales_invoice_status_var = tk.StringVar(value="全部")
        status_combo = ttk.Combobox(search_frame, textvariable=self.sales_invoice_status_var, 
                                    values=["全部", "草稿", "已提交", "已审核", "已开票", "已归档"], width=10)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.load_sales_invoices())
        
        # 发票表格
        tree_frame = ttk.Frame(invoice_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("发票号码", "开票日期", "客户", "发票金额", "税额", "价税合计", 
                   "状态", "收款状态", "关联单号", "开票人", "操作员")
        self.sales_invoice_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        column_widths = {
            "发票号码": 120,
            "开票日期": 100,
            "客户": 150,
            "发票金额": 100,
            "税额": 80,
            "价税合计": 100,
            "状态": 80,
            "收款状态": 80,
            "关联单号": 120,
            "开票人": 80,
            "操作员": 80
        }
        
        for col in columns:
            self.sales_invoice_tree.heading(col, text=col)
            self.sales_invoice_tree.column(col, width=column_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.sales_invoice_tree.yview)
        self.sales_invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sales_invoice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.sales_invoice_tree.bind('<<TreeviewSelect>>', self.on_sales_invoice_select)
        
        # 状态栏
        self.sales_invoice_stats_frame = ttk.Frame(invoice_frame)
        self.sales_invoice_stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 统计信息
        stats_labels = [
            ("发票总数:", "total_count"),
            ("发票总额:", "total_amount"),
            ("已开票:", "issued_count"),
            ("待收款:", "unreceived_amount"),
        ]
        
        self.sales_invoice_stats_vars = {}
        
        for i, (label, key) in enumerate(stats_labels):
            ttk.Label(self.sales_invoice_stats_frame, text=label).grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value="0")
            ttk.Label(self.sales_invoice_stats_frame, textvariable=var, 
                     font=("微软雅黑", 10, "bold")).grid(row=0, column=i*2+1, padx=(0, 20), pady=5, sticky="w")
            self.sales_invoice_stats_vars[key] = var
        
        # 加载数据
        self.load_sales_invoices()
    
    def load_sales_invoices(self):
        """加载销售发票数据"""
        for item in self.sales_invoice_tree.get_children():
            self.sales_invoice_tree.delete(item)
        
        # 构建查询条件
        search_term = self.sales_invoice_search_var.get()
        status_filter = self.sales_invoice_status_var.get()
        
        conditions = ["invoice_type = '销项'"]
        params = []
        
        if search_term:
            conditions.append("(invoice_no LIKE ? OR related_order_no LIKE ?)")
            params.append(f'%{search_term}%')
            params.append(f'%{search_term}%')
        
        if status_filter != "全部":
            status_map = {
                "草稿": "draft", 
                "已提交": "submitted", 
                "已审核": "verified", 
                "已开票": "issued",
                "已归档": "archived"
            }
            if status_filter in status_map:
                conditions.append("status = ?")
                params.append(status_map[status_filter])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 执行查询
        query = f'''
            SELECT 
                i.invoice_no,
                i.invoice_date,
                COALESCE(c.name, '') as customer_name,
                i.invoice_amount,
                i.tax_amount,
                i.total_amount,
                CASE i.status
                    WHEN 'draft' THEN '草稿'
                    WHEN 'submitted' THEN '已提交'
                    WHEN 'verified' THEN '已审核'
                    WHEN 'issued' THEN '已开票'
                    WHEN 'archived' THEN '已归档'
                    ELSE i.status
                END as status,
                CASE i.payment_status
                    WHEN 'unpaid' THEN '未收款'
                    WHEN 'partial' THEN '部分收款'
                    WHEN 'paid' THEN '已收款'
                    ELSE i.payment_status
                END as payment_status,
                COALESCE(i.related_order_no, ''),
                COALESCE(i.issued_by, ''),
                COALESCE(u.realname, '')
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN users u ON i.operator_id = u.id
            WHERE {where_clause}
            ORDER BY i.invoice_date DESC, i.invoice_no DESC
            LIMIT 200
        '''
        
        self.cursor.execute(query, params)
        invoices = self.cursor.fetchall()
        
        for invoice in invoices:
            self.sales_invoice_tree.insert("", "end", values=invoice)
        
        self.update_sales_invoice_stats()
    
    def update_sales_invoice_stats(self):
        """更新销售发票统计信息"""
        # 发票总数
        self.cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_type = '销项'")
        total_count = self.cursor.fetchone()[0] or 0
        self.sales_invoice_stats_vars["total_count"].set(str(total_count))
        
        # 发票总额
        self.cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE invoice_type = '销项' AND status != 'draft'")
        total_amount = self.cursor.fetchone()[0] or 0
        self.sales_invoice_stats_vars["total_amount"].set(f"¥{total_amount:,.2f}")
        
        # 已开票数量
        self.cursor.execute("SELECT COUNT(*) FROM invoices WHERE invoice_type = '销项' AND status = 'issued'")
        issued_count = self.cursor.fetchone()[0] or 0
        self.sales_invoice_stats_vars["issued_count"].set(str(issued_count))
        
        # 待收款金额
        self.cursor.execute('''
            SELECT SUM(i.total_amount - COALESCE(SUM(p.amount), 0)) 
            FROM invoices i
            LEFT JOIN invoice_payments p ON i.id = p.invoice_id AND p.payment_type = 'receipt'
            WHERE i.invoice_type = '销项' AND i.status != 'draft'
            GROUP BY i.id
            HAVING i.total_amount > COALESCE(SUM(p.amount), 0)
        ''')
        unreceived_result = self.cursor.fetchone()
        unreceived_amount = unreceived_result[0] if unreceived_result else 0
        self.sales_invoice_stats_vars["unreceived_amount"].set(f"¥{unreceived_amount:,.2f}")
    
    def on_sales_invoice_select(self, event):
        """销售发票选择事件"""
        selection = self.sales_invoice_tree.selection()
        if not selection:
            return
        
        item = self.sales_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        self.status_bar.config(text=f"选中发票: {invoice_no}")
    
    def add_sales_invoice(self):
        """新增销售发票"""
        messagebox.showinfo("提示", "新增销售发票功能需要进一步实现")
    
    def edit_sales_invoice(self):
        """编辑销售发票"""
        selection = self.sales_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.sales_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        messagebox.showinfo("提示", f"编辑发票: {invoice_no}\n此功能需要进一步实现")
    
    def delete_sales_invoice(self):
        """删除销售发票"""
        selection = self.sales_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.sales_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        if not messagebox.askyesno("确认", f"确定要删除发票 {invoice_no} 吗？"):
            return
        
        try:
            self.cursor.execute("DELETE FROM invoices WHERE invoice_no = ?", (invoice_no,))
            self.conn.commit()
            
            messagebox.showinfo("成功", "发票删除成功！")
            self.load_sales_invoices()
            
            # 记录日志
            self.log_action('delete_invoice', f"删除销售发票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除发票失败：{str(e)}")
    
    def verify_sales_invoice(self):
        """审核销售发票"""
        selection = self.sales_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.sales_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        # 更新发票状态为已审核
        try:
            self.cursor.execute('''
                UPDATE invoices 
                SET status = 'verified', verify_date = ?, verify_by = ?
                WHERE invoice_no = ?
            ''', (datetime.now().strftime("%Y-%m-%d"), self.current_user['id'], invoice_no))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", f"发票 {invoice_no} 审核通过！")
            self.load_sales_invoices()
            
            # 记录日志
            self.log_action('verify_invoice', f"审核销售发票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"审核发票失败：{str(e)}")
    
    def confirm_issue_sales_invoice(self):
        """确认开票"""
        selection = self.sales_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.sales_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        # 更新发票状态为已开票
        try:
            self.cursor.execute('''
                UPDATE invoices 
                SET status = 'issued', issued_by = ?
                WHERE invoice_no = ?
            ''', (self.current_user['realname'], invoice_no))
            
            self.conn.commit()
            
            messagebox.showinfo("成功", f"发票 {invoice_no} 已标记为已开票！")
            self.load_sales_invoices()
            
            # 记录日志
            self.log_action('issue_invoice', f"确认开票: {invoice_no}")
            
        except Exception as e:
            messagebox.showerror("错误", f"确认开票失败：{str(e)}")
    
    def register_sales_payment(self):
        """登记收款"""
        selection = self.sales_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.sales_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        total_amount = float(item['values'][5])
        
        # 获取发票ID
        self.cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,))
        invoice = self.cursor.fetchone()
        
        if not invoice:
            messagebox.showerror("错误", "未找到该发票！")
            return
        
        invoice_id = invoice[0]
        
        # 创建收款登记窗口
        payment_window = tk.Toplevel(self.root)
        payment_window.title("收款登记")
        payment_window.geometry("400x300")
        payment_window.resizable(False, False)
        payment_window.transient(self.root)
        payment_window.grab_set()
        
        ttk.Label(payment_window, text=f"发票号码: {invoice_no}", font=("微软雅黑", 10, "bold")).pack(pady=10)
        ttk.Label(payment_window, text=f"应收金额: ¥{total_amount:,.2f}", font=("微软雅黑", 10)).pack(pady=5)
        
        ttk.Label(payment_window, text="收款金额:").pack(pady=5)
        payment_amount_var = tk.StringVar(value=str(total_amount))
        ttk.Entry(payment_window, textvariable=payment_amount_var, width=20).pack(pady=5)
        
        ttk.Label(payment_window, text="收款日期:").pack(pady=5)
        payment_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(payment_window, textvariable=payment_date_var, width=20).pack(pady=5)
        
        ttk.Label(payment_window, text="收款方式:").pack(pady=5)
        payment_method_var = tk.StringVar(value="转账")
        payment_method_combo = ttk.Combobox(payment_window, textvariable=payment_method_var, 
                                            values=["转账", "现金", "支票", "其他"], width=17)
        payment_method_combo.pack(pady=5)
        
        def save_payment():
            try:
                payment_amount = float(payment_amount_var.get())
                payment_date = payment_date_var.get()
                payment_method = payment_method_var.get()
                
                # 创建收款记录
                self.cursor.execute('''
                    INSERT INTO invoice_payments (
                        invoice_id, payment_no, payment_type, payment_date,
                        amount, payment_method, operator_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id,
                    f"REC{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "receipt",
                    payment_date,
                    payment_amount,
                    payment_method,
                    self.current_user['id']
                ))
                
                # 更新发票收款状态
                # 计算已收款总额
                self.cursor.execute('''
                    SELECT SUM(amount) FROM invoice_payments 
                    WHERE invoice_id = ? AND payment_type = 'receipt'
                ''', (invoice_id,))
                total_received = self.cursor.fetchone()[0] or 0
                
                # 更新收款状态
                if total_received >= total_amount:
                    payment_status = "paid"
                elif total_received > 0:
                    payment_status = "partial"
                else:
                    payment_status = "unpaid"
                
                self.cursor.execute('''
                    UPDATE invoices SET payment_status = ? WHERE id = ?
                ''', (payment_status, invoice_id))
                
                self.conn.commit()
                
                messagebox.showinfo("成功", "收款登记成功！")
                payment_window.destroy()
                self.load_sales_invoices()
                
                # 记录日志
                self.log_action('register_receipt', f"登记收款: 发票 {invoice_no}, 金额 ¥{payment_amount}")
                
            except Exception as e:
                messagebox.showerror("错误", f"收款登记失败：{str(e)}")
        
        ttk.Button(payment_window, text="保存", command=save_payment, 
                   style='Success.TButton').pack(pady=20)
    
    def export_sales_invoices(self):
        """导出销售发票"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 查询所有销售发票
            self.cursor.execute('''
                SELECT 
                    i.invoice_no,
                    i.invoice_date,
                    COALESCE(c.name, '') as customer_name,
                    i.invoice_amount,
                    i.tax_amount,
                    i.total_amount,
                    CASE i.status
                        WHEN 'draft' THEN '草稿'
                        WHEN 'submitted' THEN '已提交'
                        WHEN 'verified' THEN '已审核'
                        WHEN 'issued' THEN '已开票'
                        WHEN 'archived' THEN '已归档'
                        ELSE i.status
                    END as status,
                    CASE i.payment_status
                        WHEN 'unpaid' THEN '未收款'
                        WHEN 'partial' THEN '部分收款'
                        WHEN 'paid' THEN '已收款'
                        ELSE i.payment_status
                    END as payment_status,
                    i.related_order_no,
                    COALESCE(u.realname, '') as operator
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                LEFT JOIN users u ON i.operator_id = u.id
                WHERE i.invoice_type = '销项'
                ORDER BY i.invoice_date DESC
            ''')
            
            invoices = self.cursor.fetchall()
            
            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['发票号码', '开票日期', '客户', '发票金额', '税额', '价税合计', 
                               '状态', '收款状态', '关联单号', '操作员'])
                writer.writerows(invoices)
            
            messagebox.showinfo("成功", f"数据已导出到：{file_path}")
            
            # 记录日志
            self.log_action('export_invoices', "导出销售发票数据")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    def create_invoice_verification_tab(self):
        """创建发票认证管理标签页"""
        verify_frame = ttk.Frame(self.notebook)
        self.notebook.add(verify_frame, text="发票认证管理")
        
        # 工具栏
        toolbar = ttk.Frame(verify_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar, text="待认证发票", command=self.load_unverified_invoices, 
                   style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="认证通过", command=self.mark_invoice_verified, 
                   style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="认证不通过", command=self.mark_invoice_unverified, 
                   style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="批量认证", command=self.batch_verify_invoices).pack(side=tk.LEFT, padx=5)
        
        # 搜索区域
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="发票号码:").pack(side=tk.LEFT, padx=5)
        self.verify_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.verify_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_invoices_for_verification).pack(side=tk.LEFT, padx=5)
        
        # 发票表格
        tree_frame = ttk.Frame(verify_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("选择", "发票号码", "开票日期", "供应商", "发票金额", "税额", 
                   "收票状态", "认证状态", "认证日期", "下次认证日期", "操作员")
        self.verification_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # 添加复选框列
        self.verification_tree.heading("选择", text="选择")
        self.verification_tree.column("选择", width=50)
        
        for col in columns[1:]:
            self.verification_tree.heading(col, text=col)
            self.verification_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.verification_tree.yview)
        self.verification_tree.configure(yscrollcommand=scrollbar.set)
        
        self.verification_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定复选框点击事件
        self.verification_tree.bind('<Button-1>', self.on_verification_checkbox_click)
        
        # 加载待认证发票
        self.load_unverified_invoices()
    
    def load_unverified_invoices(self):
        """加载待认证发票"""
        for item in self.verification_tree.get_children():
            self.verification_tree.delete(item)
        
        # 查询待认证的进项发票
        self.cursor.execute('''
            SELECT 
                i.id,
                i.invoice_no,
                i.invoice_date,
                COALESCE(s.name, '') as supplier_name,
                i.invoice_amount,
                i.tax_amount,
                CASE i.receiver_status
                    WHEN 'pending' THEN '待收票'
                    WHEN 'received' THEN '已收票'
                    WHEN 'lost' THEN '发票遗失'
                    ELSE i.receiver_status
                END as receiver_status,
                COALESCE(v.verify_status, '未认证') as verify_status,
                COALESCE(v.verify_date, '') as verify_date,
                COALESCE(v.next_verify_date, '') as next_verify_date,
                COALESCE(u.realname, '') as operator_name
            FROM invoices i
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            LEFT JOIN invoice_verifications v ON i.id = v.invoice_id
            LEFT JOIN users u ON i.operator_id = u.id
            WHERE i.invoice_type = '进项' 
              AND i.status != 'draft'
              AND (v.id IS NULL OR v.verify_status != 'success')
            ORDER BY i.invoice_date ASC, i.invoice_no ASC
            LIMIT 100
        ''')
        
        invoices = self.cursor.fetchall()
        
        for i, invoice in enumerate(invoices):
            # 添加复选框
            values = ("□",) + invoice[1:]  # 从第二个元素开始是发票数据
            item_id = self.verification_tree.insert("", "end", values=values)
            
            # 根据认证状态设置行颜色
            verify_status = invoice[7]
            if verify_status == "success":
                self.verification_tree.item(item_id, tags=("success",))
            elif verify_status == "failed":
                self.verification_tree.item(item_id, tags=("failed",))
            elif verify_status == "未认证":
                self.verification_tree.item(item_id, tags=("unverified",))
        
        # 设置行样式
        self.verification_tree.tag_configure("success", background="#d4edda")
        self.verification_tree.tag_configure("failed", background="#f8d7da")
        self.verification_tree.tag_configure("unverified", background="#fff3cd")
    
    def on_verification_checkbox_click(self, event):
        """处理复选框点击事件"""
        region = self.verification_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.verification_tree.identify_column(event.x)
            if column == "#1":  # 第一列是复选框列
                item_id = self.verification_tree.identify_row(event.y)
                if item_id:
                    current_value = self.verification_tree.item(item_id, "values")[0]
                    new_value = "✓" if current_value == "□" else "□"
                    values = list(self.verification_tree.item(item_id, "values"))
                    values[0] = new_value
                    self.verification_tree.item(item_id, values=values)
    
    def mark_invoice_verified(self):
        """标记发票认证通过"""
        selected_items = []
        
        # 获取选中的发票
        for item_id in self.verification_tree.get_children():
            values = self.verification_tree.item(item_id, "values")
            if values and values[0] == "✓":
                invoice_no = values[1]
                selected_items.append(invoice_no)
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要认证的发票！")
            return
        
        # 确认认证
        if not messagebox.askyesno("确认", f"确定要将选中的 {len(selected_items)} 张发票标记为认证通过吗？"):
            return
        
        try:
            # 更新发票认证状态
            for invoice_no in selected_items:
                # 获取发票ID
                self.cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,))
                invoice = self.cursor.fetchone()
                
                if invoice:
                    invoice_id = invoice[0]
                    
                    # 检查是否已有认证记录
                    self.cursor.execute("SELECT id FROM invoice_verifications WHERE invoice_id = ?", (invoice_id,))
                    existing = self.cursor.fetchone()
                    
                    if existing:
                        # 更新现有记录
                        self.cursor.execute('''
                            UPDATE invoice_verifications 
                            SET verify_status = 'success', verify_date = ?, verify_by = ?
                            WHERE invoice_id = ?
                        ''', (datetime.now().strftime("%Y-%m-%d"), self.current_user['id'], invoice_id))
                    else:
                        # 插入新记录
                        self.cursor.execute('''
                            INSERT INTO invoice_verifications 
                            (invoice_id, verify_no, verify_date, verify_status, verify_by)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            invoice_id,
                            f"VFY{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            datetime.now().strftime("%Y-%m-%d"),
                            "success",
                            self.current_user['id']
                        ))
            
            self.conn.commit()
            messagebox.showinfo("成功", f"已成功认证 {len(selected_items)} 张发票")
            
            # 重新加载数据
            self.load_unverified_invoices()
            
            # 记录日志
            self.log_action('verify_invoice', f"认证发票: {', '.join(selected_items[:5])}{'...' if len(selected_items) > 5 else ''}")
            
        except Exception as e:
            messagebox.showerror("错误", f"认证发票失败：{str(e)}")
    
    def mark_invoice_unverified(self):
        """标记发票认证不通过"""
        selection = self.verification_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一张发票！")
            return
        
        item = self.verification_tree.item(selection[0])
        invoice_no = item['values'][1]
        
        # 获取认证失败原因
        reason = simpledialog.askstring("认证不通过", f"请输入发票 {invoice_no} 认证不通过的原因:")
        
        if not reason:
            return
        
        # 获取发票ID
        self.cursor.execute("SELECT id FROM invoices WHERE invoice_no = ?", (invoice_no,))
        invoice = self.cursor.fetchone()
        
        if not invoice:
            messagebox.showerror("错误", "未找到该发票！")
            return
        
        invoice_id = invoice[0]
        
        try:
            # 检查是否已有认证记录
            self.cursor.execute("SELECT id FROM invoice_verifications WHERE invoice_id = ?", (invoice_id,))
            existing = self.cursor.fetchone()
            
            if existing:
                # 更新现有记录
                self.cursor.execute('''
                    UPDATE invoice_verifications 
                    SET verify_status = 'failed', verify_result = ?, verify_date = ?, verify_by = ?
                    WHERE invoice_id = ?
                ''', (reason, datetime.now().strftime("%Y-%m-%d"), self.current_user['id'], invoice_id))
            else:
                # 插入新记录
                self.cursor.execute('''
                    INSERT INTO invoice_verifications 
                    (invoice_id, verify_no, verify_date, verify_status, verify_result, verify_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id,
                    f"VFY{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    datetime.now().strftime("%Y-%m-%d"),
                    "failed",
                    reason,
                    self.current_user['id']
                ))
            
            self.conn.commit()
            messagebox.showinfo("成功", f"发票 {invoice_no} 已标记为认证不通过")
            
            # 重新加载数据
            self.load_unverified_invoices()
            
            # 记录日志
            self.log_action('reject_invoice', f"认证不通过: {invoice_no}, 原因: {reason}")
            
        except Exception as e:
            messagebox.showerror("错误", f"标记认证不通过失败：{str(e)}")
    
    def batch_verify_invoices(self):
        """批量认证"""
        messagebox.showinfo("提示", "批量认证功能需要进一步实现")
    
    def search_invoices_for_verification(self):
        """搜索待认证发票"""
        search_term = self.verify_search_var.get()
        
        # 清空表格
        for item in self.verification_tree.get_children():
            self.verification_tree.delete(item)
        
        # 查询待认证的进项发票
        self.cursor.execute('''
            SELECT 
                i.id,
                i.invoice_no,
                i.invoice_date,
                COALESCE(s.name, '') as supplier_name,
                i.invoice_amount,
                i.tax_amount,
                CASE i.receiver_status
                    WHEN 'pending' THEN '待收票'
                    WHEN 'received' THEN '已收票'
                    WHEN 'lost' THEN '发票遗失'
                    ELSE i.receiver_status
                END as receiver_status,
                COALESCE(v.verify_status, '未认证') as verify_status,
                COALESCE(v.verify_date, '') as verify_date,
                COALESCE(v.next_verify_date, '') as next_verify_date,
                COALESCE(u.realname, '') as operator_name
            FROM invoices i
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            LEFT JOIN invoice_verifications v ON i.id = v.invoice_id
            LEFT JOIN users u ON i.operator_id = u.id
            WHERE i.invoice_type = '进项' 
              AND i.status != 'draft'
              AND (v.id IS NULL OR v.verify_status != 'success')
              AND (i.invoice_no LIKE ? OR s.name LIKE ?)
            ORDER BY i.invoice_date ASC, i.invoice_no ASC
            LIMIT 100
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        invoices = self.cursor.fetchall()
        
        for i, invoice in enumerate(invoices):
            # 添加复选框
            values = ("□",) + invoice[1:]
            item_id = self.verification_tree.insert("", "end", values=values)
            
            # 根据认证状态设置行颜色
            verify_status = invoice[7]
            if verify_status == "success":
                self.verification_tree.item(item_id, tags=("success",))
            elif verify_status == "failed":
                self.verification_tree.item(item_id, tags=("failed",))
            elif verify_status == "未认证":
                self.verification_tree.item(item_id, tags=("unverified",))
    
    def create_invoice_reversal_tab(self):
        """创建发票红冲管理标签页"""
        reversal_frame = ttk.Frame(self.notebook)
        self.notebook.add(reversal_frame, text="发票红冲管理")
        
        # 工具栏
        toolbar = ttk.Frame(reversal_frame)
        toolbar.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(toolbar, text="新增红冲", command=self.add_invoice_reversal, 
                   style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="查看红冲记录", command=self.show_reversal_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出红冲报表", command=self.export_reversal_report).pack(side=tk.LEFT, padx=5)
        
        # 搜索区域
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="原发票号:").pack(side=tk.LEFT, padx=5)
        self.reversal_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.reversal_search_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.search_invoices_for_reversal).pack(side=tk.LEFT, padx=5)
        
        # 可红冲发票表格
        tree_frame = ttk.Frame(reversal_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        columns = ("发票号码", "开票日期", "客户/供应商", "发票类型", "发票金额", "税额", 
                   "价税合计", "状态", "是否已红冲")
        self.reversible_invoice_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.reversible_invoice_tree.heading(col, text=col)
            self.reversible_invoice_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.reversible_invoice_tree.yview)
        self.reversible_invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        self.reversible_invoice_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.reversible_invoice_tree.bind('<<TreeviewSelect>>', self.on_reversible_invoice_select)
        
        # 加载可红冲发票
        self.load_reversible_invoices()
    
    def load_reversible_invoices(self):
        """加载可红冲发票"""
        for item in self.reversible_invoice_tree.get_children():
            self.reversible_invoice_tree.delete(item)
        
        # 查询已审核但未红冲的发票
        self.cursor.execute('''
            SELECT 
                i.invoice_no,
                i.invoice_date,
                CASE 
                    WHEN i.invoice_type = '进项' THEN COALESCE(s.name, '')
                    WHEN i.invoice_type = '销项' THEN COALESCE(c.name, '')
                    ELSE ''
                END as partner_name,
                CASE i.invoice_type
                    WHEN '进项' THEN '进项发票'
                    WHEN '销项' THEN '销项发票'
                    ELSE i.invoice_type
                END as invoice_type,
                i.invoice_amount,
                i.tax_amount,
                i.total_amount,
                CASE i.status
                    WHEN 'verified' THEN '已审核'
                    WHEN 'issued' THEN '已开票'
                    WHEN 'archived' THEN '已归档'
                    ELSE i.status
                END as status,
                CASE 
                    WHEN r.id IS NOT NULL THEN '是'
                    ELSE '否'
                END as is_reversed
            FROM invoices i
            LEFT JOIN suppliers s ON i.supplier_id = s.id AND i.invoice_type = '进项'
            LEFT JOIN customers c ON i.customer_id = c.id AND i.invoice_type = '销项'
            LEFT JOIN invoice_reversals r ON i.id = r.original_invoice_id
            WHERE i.status IN ('verified', 'issued', 'archived')
              AND r.id IS NULL
            ORDER BY i.invoice_date DESC
            LIMIT 100
        ''')
        
        invoices = self.cursor.fetchall()
        
        for invoice in invoices:
            self.reversible_invoice_tree.insert("", "end", values=invoice)
    
    def on_reversible_invoice_select(self, event):
        """可红冲发票选择事件"""
        selection = self.reversible_invoice_tree.selection()
        if not selection:
            return
        
        item = self.reversible_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        self.status_bar.config(text=f"选中发票: {invoice_no}")
    
    def add_invoice_reversal(self):
        """新增发票红冲"""
        selection = self.reversible_invoice_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要红冲的发票！")
            return
        
        item = self.reversible_invoice_tree.item(selection[0])
        invoice_no = item['values'][0]
        
        messagebox.showinfo("提示", f"红冲发票: {invoice_no}\n此功能需要进一步实现")
    
    def show_reversal_history(self):
        """查看红冲记录"""
        messagebox.showinfo("提示", "查看红冲记录功能需要进一步实现")
    
    def export_reversal_report(self):
        """导出红冲报表"""
        messagebox.showinfo("提示", "导出红冲报表功能需要进一步实现")
    
    def search_invoices_for_reversal(self):
        """搜索可红冲发票"""
        search_term = self.reversal_search_var.get()
        
        # 清空表格
        for item in self.reversible_invoice_tree.get_children():
            self.reversible_invoice_tree.delete(item)
        
        # 查询可红冲发票
        self.cursor.execute('''
            SELECT 
                i.invoice_no,
                i.invoice_date,
                CASE 
                    WHEN i.invoice_type = '进项' THEN COALESCE(s.name, '')
                    WHEN i.invoice_type = '销项' THEN COALESCE(c.name, '')
                    ELSE ''
                END as partner_name,
                CASE i.invoice_type
                    WHEN '进项' THEN '进项发票'
                    WHEN '销项' THEN '销项发票'
                    ELSE i.invoice_type
                END as invoice_type,
                i.invoice_amount,
                i.tax_amount,
                i.total_amount,
                CASE i.status
                    WHEN 'verified' THEN '已审核'
                    WHEN 'issued' THEN '已开票'
                    WHEN 'archived' THEN '已归档'
                    ELSE i.status
                END as status,
                CASE 
                    WHEN r.id IS NOT NULL THEN '是'
                    ELSE '否'
                END as is_reversed
            FROM invoices i
            LEFT JOIN suppliers s ON i.supplier_id = s.id AND i.invoice_type = '进项'
            LEFT JOIN customers c ON i.customer_id = c.id AND i.invoice_type = '销项'
            LEFT JOIN invoice_reversals r ON i.id = r.original_invoice_id
            WHERE i.status IN ('verified', 'issued', 'archived')
              AND r.id IS NULL
              AND (i.invoice_no LIKE ? OR s.name LIKE ? OR c.name LIKE ?)
            ORDER BY i.invoice_date DESC
            LIMIT 100
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        invoices = self.cursor.fetchall()
        
        for invoice in invoices:
            self.reversible_invoice_tree.insert("", "end", values=invoice)
    
    def create_invoice_report_tab(self):
        """创建发票统计报表标签页"""
        report_frame = ttk.Frame(self.notebook)
        self.notebook.add(report_frame, text="发票统计报表")
        
        # 报表选项
        option_frame = ttk.LabelFrame(report_frame, text="报表选项", padding=10)
        option_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 报表类型
        ttk.Label(option_frame, text="报表类型:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.invoice_report_type_var = tk.StringVar(value="summary")
        report_combo = ttk.Combobox(option_frame, textvariable=self.invoice_report_type_var, 
                                    values=["汇总报表", "明细报表", "认证统计", "收付款统计"], width=15)
        report_combo.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # 发票类型
        ttk.Label(option_frame, text="发票类型:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        self.invoice_type_var = tk.StringVar(value="全部")
        type_combo = ttk.Combobox(option_frame, textvariable=self.invoice_type_var, 
                                  values=["全部", "进项发票", "销项发票"], width=12)
        type_combo.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        # 时间范围
        ttk.Label(option_frame, text="时间范围:").grid(row=0, column=4, sticky="e", padx=5, pady=5)
        self.invoice_period_var = tk.StringVar(value="本月")
        period_combo = ttk.Combobox(option_frame, textvariable=self.invoice_period_var, 
                                    values=["今日", "本周", "本月", "本季", "本年", "自定义"], width=10)
        period_combo.grid(row=0, column=5, sticky="w", padx=5, pady=5)
        
        # 自定义时间
        ttk.Label(option_frame, text="开始日期:").grid(row=0, column=6, sticky="e", padx=5, pady=5)
        self.invoice_start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-01"))
        ttk.Entry(option_frame, textvariable=self.invoice_start_date_var, width=12).grid(row=0, column=7, sticky="w", padx=5, pady=5)
        
        ttk.Label(option_frame, text="结束日期:").grid(row=0, column=8, sticky="e", padx=5, pady=5)
        self.invoice_end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(option_frame, textvariable=self.invoice_end_date_var, width=12).grid(row=0, column=9, sticky="w", padx=5, pady=5)
        
        # 按钮
        ttk.Button(option_frame, text="生成报表", command=self.generate_invoice_report,
                  style='Primary.TButton').grid(row=0, column=10, padx=10, pady=5)
        ttk.Button(option_frame, text="导出Excel", command=self.export_invoice_report,
                  style='Success.TButton').grid(row=0, column=11, padx=5, pady=5)
        
        # 报表显示区域
        display_frame = ttk.Frame(report_frame)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 报表表格
        columns = ("期间", "进项发票数", "进项金额", "进项税额", "销项发票数", "销项金额", "销项税额", "净税额", "税负率")
        self.invoice_report_tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.invoice_report_tree.heading(col, text=col)
            self.invoice_report_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(display_frame, orient="vertical", command=self.invoice_report_tree.yview)
        self.invoice_report_tree.configure(yscrollcommand=scrollbar.set)
        
        self.invoice_report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 汇总信息
        summary_frame = ttk.LabelFrame(report_frame, text="汇总信息", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.invoice_summary_vars = {}
        summary_labels = [
            ("进项发票总数:", "purchase_count"),
            ("进项发票总额:", "purchase_amount"),
            ("进项税额合计:", "purchase_tax"),
            ("销项发票总数:", "sales_count"),
            ("销项发票总额:", "sales_amount"),
            ("销项税额合计:", "sales_tax"),
            ("应缴税额:", "tax_payable"),
            ("综合税负率:", "tax_rate"),
        ]
        
        for i, (label, key) in enumerate(summary_labels):
            row = i // 4
            col = (i % 4) * 2
            
            ttk.Label(summary_frame, text=label).grid(row=row, column=col, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value="0.00")
            ttk.Label(summary_frame, textvariable=var, font=("微软雅黑", 10, "bold")).grid(
                row=row, column=col+1, padx=(0, 20), pady=5, sticky="w"
            )
            self.invoice_summary_vars[key] = var
        
        # 生成默认报表
        self.generate_invoice_report()
    
    def generate_invoice_report(self):
        """生成发票统计报表"""
        # 清空表格
        for item in self.invoice_report_tree.get_children():
            self.invoice_report_tree.delete(item)
        
        report_type = self.invoice_report_type_var.get()
        invoice_type = self.invoice_type_var.get()
        period = self.invoice_period_var.get()
        start_date = self.invoice_start_date_var.get()
        end_date = self.invoice_end_date_var.get()
        
        # 根据时间范围计算日期
        today = datetime.now()
        if period == "今日":
            start_date = today.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
        elif period == "本周":
            # 本周一
            monday = today - timedelta(days=today.weekday())
            start_date = monday.strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
        elif period == "本月":
            start_date = today.strftime("%Y-%m-01")
            end_date = today.strftime("%Y-%m-%d")
        elif period == "本季":
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = today.replace(month=start_month, day=1).strftime("%Y-%m-01")
            end_date = today.strftime("%Y-%m-%d")
        elif period == "本年":
            start_date = today.strftime("%Y-01-01")
            end_date = today.strftime("%Y-%m-%d")
        
        if report_type == "汇总报表":
            self.generate_invoice_summary_report(start_date, end_date, invoice_type)
        elif report_type == "明细报表":
            messagebox.showinfo("提示", "明细报表功能需要进一步实现")
        elif report_type == "认证统计":
            messagebox.showinfo("提示", "认证统计功能需要进一步实现")
        elif report_type == "收付款统计":
            messagebox.showinfo("提示", "收付款统计功能需要进一步实现")
    
    def generate_invoice_summary_report(self, start_date, end_date, invoice_type):
        """生成发票汇总报表"""
        # 按月汇总
        self.cursor.execute('''
            SELECT 
                strftime('%Y-%m', invoice_date) as month,
                SUM(CASE WHEN invoice_type = '进项' THEN 1 ELSE 0 END) as purchase_count,
                SUM(CASE WHEN invoice_type = '进项' THEN invoice_amount ELSE 0 END) as purchase_amount,
                SUM(CASE WHEN invoice_type = '进项' THEN tax_amount ELSE 0 END) as purchase_tax,
                SUM(CASE WHEN invoice_type = '销项' THEN 1 ELSE 0 END) as sales_count,
                SUM(CASE WHEN invoice_type = '销项' THEN invoice_amount ELSE 0 END) as sales_amount,
                SUM(CASE WHEN invoice_type = '销项' THEN tax_amount ELSE 0 END) as sales_tax
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ? 
              AND status != 'draft'
              AND (? = '全部' OR 
                   (? = '进项发票' AND invoice_type = '进项') OR 
                   (? = '销项发票' AND invoice_type = '销项'))
            GROUP BY strftime('%Y-%m', invoice_date)
            ORDER BY month DESC
        ''', (start_date, end_date, invoice_type, invoice_type, invoice_type))
        
        summary_data = self.cursor.fetchall()
        
        total_purchase_count = 0
        total_purchase_amount = 0
        total_purchase_tax = 0
        total_sales_count = 0
        total_sales_amount = 0
        total_sales_tax = 0
        
        for row in summary_data:
            month = row[0]
            purchase_count = row[1] or 0
            purchase_amount = row[2] or 0
            purchase_tax = row[3] or 0
            sales_count = row[4] or 0
            sales_amount = row[5] or 0
            sales_tax = row[6] or 0
            
            # 计算净税额和税负率
            net_tax = sales_tax - purchase_tax
            tax_rate = (net_tax / sales_amount * 100) if sales_amount > 0 else 0
            
            self.invoice_report_tree.insert("", "end", values=(
                month,
                f"{purchase_count}",
                f"¥{purchase_amount:,.2f}",
                f"¥{purchase_tax:,.2f}",
                f"{sales_count}",
                f"¥{sales_amount:,.2f}",
                f"¥{sales_tax:,.2f}",
                f"¥{net_tax:,.2f}",
                f"{tax_rate:.2f}%"
            ))
            
            total_purchase_count += purchase_count
            total_purchase_amount += purchase_amount
            total_purchase_tax += purchase_tax
            total_sales_count += sales_count
            total_sales_amount += sales_amount
            total_sales_tax += sales_tax
        
        # 添加合计行
        total_net_tax = total_sales_tax - total_purchase_tax
        total_tax_rate = (total_net_tax / total_sales_amount * 100) if total_sales_amount > 0 else 0
        
        self.invoice_report_tree.insert("", "end", values=(
            "合计",
            f"{total_purchase_count}",
            f"¥{total_purchase_amount:,.2f}",
            f"¥{total_purchase_tax:,.2f}",
            f"{total_sales_count}",
            f"¥{total_sales_amount:,.2f}",
            f"¥{total_sales_tax:,.2f}",
            f"¥{total_net_tax:,.2f}",
            f"{total_tax_rate:.2f}%"
        ), tags=("total",))
        
        # 设置合计行样式
        self.invoice_report_tree.tag_configure("total", background="#e8f4fd", font=("微软雅黑", 10, "bold"))
        
        # 更新汇总信息
        self.invoice_summary_vars["purchase_count"].set(f"{total_purchase_count}")
        self.invoice_summary_vars["purchase_amount"].set(f"¥{total_purchase_amount:,.2f}")
        self.invoice_summary_vars["purchase_tax"].set(f"¥{total_purchase_tax:,.2f}")
        self.invoice_summary_vars["sales_count"].set(f"{total_sales_count}")
        self.invoice_summary_vars["sales_amount"].set(f"¥{total_sales_amount:,.2f}")
        self.invoice_summary_vars["sales_tax"].set(f"¥{total_sales_tax:,.2f}")
        self.invoice_summary_vars["tax_payable"].set(f"¥{total_net_tax:,.2f}")
        self.invoice_summary_vars["tax_rate"].set(f"{total_tax_rate:.2f}%")
    
    def export_invoice_report(self):
        """导出发票报表"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 获取报表数据
            data = []
            for item_id in self.invoice_report_tree.get_children():
                item = self.invoice_report_tree.item(item_id)
                data.append(item['values'])
            
            if not data:
                messagebox.showwarning("警告", "没有数据可导出！")
                return
            
            # 获取列名
            columns = [self.invoice_report_tree.heading(col)["text"] for col in self.invoice_report_tree["columns"]]
            
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(data)
            
            messagebox.showinfo("成功", f"报表数据已导出到：{file_path}")
            
            # 记录日志
            self.log_action('export_invoice_report', "导出发票统计报表")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
    
    # ========== 其他基础功能框架 ==========
    
    def create_product_tab(self):
        """创建产品管理标签页（框架）"""
        product_frame = ttk.Frame(self.notebook)
        self.notebook.add(product_frame, text="产品管理")
        
        # 添加简单内容
        ttk.Label(product_frame, text="产品管理功能", font=("微软雅黑", 16)).pack(pady=50)
        ttk.Label(product_frame, text="此功能需要进一步实现", font=("微软雅黑", 12)).pack(pady=20)
    
    def create_supplier_tab(self):
        """创建供应商管理标签页（框架）"""
        supplier_frame = ttk.Frame(self.notebook)
        self.notebook.add(supplier_frame, text="供应商管理")
        
        ttk.Label(supplier_frame, text="供应商管理功能", font=("微软雅黑", 16)).pack(pady=50)
        ttk.Label(supplier_frame, text="此功能需要进一步实现", font=("微软雅黑", 12)).pack(pady=20)
    
    def create_customer_tab(self):
        """创建客户管理标签页（框架）"""
        customer_frame = ttk.Frame(self.notebook)
        self.notebook.add(customer_frame, text="客户管理")
        
        ttk.Label(customer_frame, text="客户管理功能", font=("微软雅黑", 16)).pack(pady=50)
        ttk.Label(customer_frame, text="此功能需要进一步实现", font=("微软雅黑", 12)).pack(pady=20)
    
    def create_warehouse_tab(self):
        """创建仓库管理标签页（框架）"""
        warehouse_frame = ttk.Frame(self.notebook)
        self.notebook.add(warehouse_frame, text="仓库管理")
        
        ttk.Label(warehouse_frame, text="仓库管理功能", font=("微软雅黑", 16)).pack(pady=50)
        ttk.Label(warehouse_frame, text="此功能需要进一步实现", font=("微软雅黑", 12)).pack(pady=20)
    
    def create_department_tab(self):
        """创建部门管理标签页（框架）"""
        department_frame = ttk.Frame(self.notebook)
        self.notebook.add(department_frame, text="部门管理")
        
        ttk.Label(department_frame, text="部门管理功能", font=("微软雅黑", 16)).pack(pady=50)
        ttk.Label(department_frame, text="此功能需要进一步实现", font=("微软雅黑", 12)).pack(pady=20)
    
    def create_default_tab(self, tab_name):
        """创建默认标签页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=tab_name)
        
        ttk.Label(frame, text=f"{tab_name}功能", font=("微软雅黑", 16)).pack(pady=50)
        ttk.Label(frame, text="此功能需要进一步实现", font=("微软雅黑", 12)).pack(pady=20)
    
    def show_user_management(self):
        """显示用户管理"""
        messagebox.showinfo("提示", "用户管理功能需要进一步实现")
    
    def show_role_management(self):
        """显示角色管理"""
        messagebox.showinfo("提示", "角色管理功能需要进一步实现")
    
    def backup_system(self):
        """系统备份"""
        backup_dir = filedialog.askdirectory(title="选择备份目录")
        
        if not backup_dir:
            return
        
        try:
            # 备份数据库
            backup_file = os.path.join(backup_dir, f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            
            # 创建数据库备份
            backup_conn = sqlite3.connect(backup_file)
            self.conn.backup(backup_conn)
            backup_conn.close()
            
            messagebox.showinfo("成功", f"系统备份完成！\n备份文件保存在：{backup_file}")
            
            # 记录日志
            self.log_action('backup_system', '执行系统备份')
            
        except Exception as e:
            messagebox.showerror("错误", f"备份失败：{str(e)}")
    
    def clean_data(self):
        """数据清理"""
        if not messagebox.askyesno("确认", "确定要清理数据吗？此操作将删除所有业务数据，但保留基础数据。"):
            return
        
        try:
            # 清理业务数据（保留最近3个月的数据）
            three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            
            # 删除旧的业务记录
            self.cursor.execute("DELETE FROM invoices WHERE invoice_date < ?", (three_months_ago,))
            self.cursor.execute("DELETE FROM purchase_orders WHERE order_date < ?", (three_months_ago,))
            self.cursor.execute("DELETE FROM sales_orders WHERE order_date < ?", (three_months_ago,))
            
            # 压缩数据库
            self.cursor.execute("VACUUM")
            
            self.conn.commit()
            
            messagebox.showinfo("成功", "数据清理完成！")
            
            # 记录日志
            self.log_action('clean_data', '执行数据清理')
            
        except Exception as e:
            messagebox.showerror("错误", f"数据清理失败：{str(e)}")
    
    def show_today_orders(self):
        """显示今日订单"""
        messagebox.showinfo("提示", "今日订单功能需要进一步实现")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """完整进销存管理系统 v3.0（含发票管理）

功能模块：
1. 系统设置：用户管理、角色管理、系统备份、数据清理
2. 基础数据：产品、供应商、客户、仓库、部门管理
3. 入库管理：采购入库、采购退货、生产入库、入库统计
4. 出库管理：销售出库、销售退货、部门领用、出库统计
5. 库存管理：库存查询、库存盘点、库存报警
6. 统计报表：进销存明细、汇总、对账单、成本、毛利分析
7. 往来账款：应收应付登记、收付款登记、帐表查询
8. 发票管理：进项发票、销项发票、认证管理、红冲管理、统计报表

开发团队：进销存管理系统开发组
版权所有 © 2023"""
        
        messagebox.showinfo("关于", about_text)
    
    def log_action(self, action_type, action_detail):
        """记录系统日志"""
        try:
            self.cursor.execute('''
                INSERT INTO system_logs (user_id, action_type, action_detail, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (self.current_user['id'], action_type, action_detail, '127.0.0.1'))
            self.conn.commit()
        except:
            pass
    
    def on_closing(self):
        """关闭窗口时执行"""
        if messagebox.askokcancel("退出", "确定要退出进销存管理系统吗？"):
            # 记录日志
            self.log_action('logout', f'用户 {self.current_user["username"]} 退出系统')
            
            self.conn.close()
            self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = CompleteInventorySystemWithInvoice(root)
    root.mainloop()

if __name__ == "__main__":
    main()