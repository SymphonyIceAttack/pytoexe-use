import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime
import random
import re

class UserManager:
    """用户数据管理类"""
    def __init__(self, data_file="users_data.json", billing_file="billing_data.json"):
        self.data_file = data_file
        self.billing_file = billing_file
        self.users = {}
        self.billing_records = {}
        self.load_data()
        self.load_billing_data()
    
    def load_data(self):
        """从文件加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            # 初始化只有admin账户
            self.users = {
                "admin": {
                    "password": "admin123",
                    "email": "admin@system.com",
                    "role": "admin",
                    "balance": 0,
                    "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_login": ""
                }
            }
            self.save_data()
    
    def save_data(self):
        """保存用户数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def load_billing_data(self):
        """加载消费记录"""
        if os.path.exists(self.billing_file):
            try:
                with open(self.billing_file, 'r', encoding='utf-8') as f:
                    self.billing_records = json.load(f)
            except:
                self.billing_records = {}
        else:
            self.billing_records = {}
            self.save_billing_data()
    
    def save_billing_data(self):
        """保存消费记录"""
        try:
            with open(self.billing_file, 'w', encoding='utf-8') as f:
                json.dump(self.billing_records, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def add_user(self, username, password, email="", role="user"):
        """添加新用户"""
        if username in self.users:
            return False, "用户名已存在"
        
        self.users[username] = {
            "password": password,
            "email": email if email else "未设置",
            "role": role,
            "balance": 0,
            "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": ""
        }
        return self.save_data(), "注册成功"
    
    def add_test_user(self, username, password):
        """添加测试用户"""
        if username in self.users:
            return False, "用户名已存在"
        
        self.users[username] = {
            "password": password,
            "email": "test@example.com",
            "role": "test",
            "balance": 100,  # 测试用户赠送100余额
            "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": ""
        }
        return self.save_data(), "测试用户创建成功"
    
    def add_admin_user(self, username, password, email=""):
        """添加管理员用户"""
        if username in self.users:
            return False, "用户名已存在"
        
        self.users[username] = {
            "password": password,
            "email": email if email else "未设置",
            "role": "admin",
            "balance": 0,
            "register_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": ""
        }
        return self.save_data(), "管理员创建成功"
    
    def check_login(self, username, password):
        """检查登录"""
        if username not in self.users:
            return False, "用户不存在"
        
        if self.users[username]["password"] != password:
            return False, "密码错误"
        
        # 更新最后登录时间
        self.users[username]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_data()
        
        return True, self.users[username]["role"]
    
    def delete_user(self, username):
        """删除用户"""
        if username == "admin":
            return False, "不能删除超级管理员账户"
        
        if username in self.users:
            # 删除用户的消费记录
            if username in self.billing_records:
                del self.billing_records[username]
                self.save_billing_data()
            del self.users[username]
            return self.save_data(), "删除成功"
        return False, "用户不存在"
    
    def get_all_users(self):
        """获取所有用户"""
        return self.users
    
    def update_user(self, username, **kwargs):
        """更新用户信息"""
        if username in self.users:
            for key, value in kwargs.items():
                if key in self.users[username]:
                    self.users[username][key] = value
            return self.save_data()
        return False
    
    def update_balance(self, username, amount, description, operator):
        """更新用户余额"""
        if username not in self.users:
            return False, "用户不存在"
        
        old_balance = self.users[username].get("balance", 0)
        new_balance = old_balance + amount
        
        if new_balance < 0:
            return False, "余额不足，无法扣除"
        
        self.users[username]["balance"] = new_balance
        self.save_data()
        
        # 添加消费记录
        record = {
            "username": username,
            "amount": amount,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "description": description,
            "operator": operator,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if username not in self.billing_records:
            self.billing_records[username] = []
        
        self.billing_records[username].append(record)
        self.save_billing_data()
        
        return True, f"余额更新成功！当前余额: {new_balance}"
    
    def get_user_balance(self, username):
        """获取用户余额"""
        return self.users.get(username, {}).get("balance", 0)
    
    def get_user_billing_records(self, username):
        """获取用户消费记录"""
        return self.billing_records.get(username, [])
    
    def get_all_billing_records(self):
        """获取所有消费记录"""
        all_records = []
        for username, records in self.billing_records.items():
            all_records.extend(records)
        # 按时间倒序排序
        all_records.sort(key=lambda x: x["time"], reverse=True)
        return all_records
    
    def get_existing_usernames(self):
        """获取所有已存在的用户名"""
        return list(self.users.keys())
    
    def generate_test_username(self):
        """生成不重复的测试用户名"""
        existing_usernames = self.get_existing_usernames()
        while True:
            random_num = random.randint(1000, 9999)
            test_username = f"ceshi{random_num}"
            if test_username not in existing_usernames:
                return test_username

class LoginWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("登录界面")
        self.window.geometry("400x500")
        self.window.configure(bg="#f5f5f5")
        
        # 初始化用户管理器
        self.user_manager = UserManager()
        
        # 居中显示窗口
        self.center_window()
        
        # 创建主框架
        self.create_login_interface()
        
    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = 400
        height = 500
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_login_interface(self):
        # 标题
        title_label = tk.Label(self.window, text="欢迎登录", 
                               font=("微软雅黑", 24, "bold"),
                               bg="#f5f5f5", fg="#333333")
        title_label.pack(pady=(50, 30))
        
        # 登录框架
        login_frame = tk.Frame(self.window, bg="#f5f5f5")
        login_frame.pack(pady=20)
        
        # 用户名输入框
        username_label = tk.Label(login_frame, text="用户名:", 
                                  font=("微软雅黑", 12),
                                  bg="#f5f5f5", fg="#666666")
        username_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.username_entry = tk.Entry(login_frame, font=("微软雅黑", 12),
                                       width=25, relief="solid", bd=1)
        self.username_entry.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # 密码输入框
        password_label = tk.Label(login_frame, text="密码:", 
                                  font=("微软雅黑", 12),
                                  bg="#f5f5f5", fg="#666666")
        password_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        self.password_entry = tk.Entry(login_frame, font=("微软雅黑", 12),
                                       width=25, relief="solid", bd=1,
                                       show="*")
        self.password_entry.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # 注册账号蓝色小字
        self.register_label = tk.Label(login_frame, text="注册账号", 
                                       font=("微软雅黑", 10),
                                       fg="#1e90ff", bg="#f5f5f5",
                                       cursor="hand2")
        self.register_label.grid(row=4, column=0, sticky="w", pady=(0, 20))
        # 绑定点击事件
        self.register_label.bind("<Button-1>", self.show_register_window)
        
        # 登录按钮
        login_button = tk.Button(login_frame, text="登录", 
                                 font=("微软雅黑", 12, "bold"),
                                 width=20, height=1,
                                 bg="#1e90ff", fg="white",
                                 relief="flat", cursor="hand2",
                                 command=self.login)
        login_button.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        # 绑定回车键登录
        self.window.bind('<Return>', lambda event: self.login())
        
    def login(self):
        """登录验证"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("警告", "请输入用户名和密码！")
            return
        
        # 检查登录
        success, result = self.user_manager.check_login(username, password)
        
        if not success:
            if result == "用户不存在":
                result_msg = messagebox.askyesno("用户不存在", 
                                                f"用户 '{username}' 不存在！\n是否前往注册？")
                if result_msg:
                    self.show_register_window()
            else:
                messagebox.showerror("登录失败", result)
            return
        
        # 登录成功
        role = result
        messagebox.showinfo("登录成功", f"欢迎回来，{username}！")
        
        # 根据角色跳转不同界面
        if role == "admin":
            self.show_admin_window(username)
        else:
            self.show_main_window(username)
        
        # 隐藏登录窗口
        self.window.withdraw()
    
    def show_admin_window(self, username):
        """显示后台管理界面"""
        admin_win = tk.Toplevel(self.window)
        admin_win.title("后台管理系统")
        admin_win.geometry("1300x750")
        admin_win.configure(bg="#f5f5f5")
        
        # 居中窗口
        admin_win.update_idletasks()
        x = (admin_win.winfo_screenwidth() // 2) - (1300 // 2)
        y = (admin_win.winfo_screenheight() // 2) - (750 // 2)
        admin_win.geometry(f'1300x750+{x}+{y}')
        
        # ========== 创建菜单栏 ==========
        menubar = tk.Menu(admin_win)
        admin_win.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="数据备份", command=self.backup_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出登录", command=lambda: self.logout(admin_win))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # ========== 顶部工具栏 ==========
        toolbar = tk.Frame(admin_win, bg="#1e90ff", height=60)
        toolbar.pack(fill=tk.X)
        
        # 欢迎信息
        welcome_label = tk.Label(toolbar, 
                                text=f"欢迎，管理员 {username}！", 
                                font=("微软雅黑", 16, "bold"),
                                bg="#1e90ff", fg="white")
        welcome_label.pack(side=tk.LEFT, padx=30, pady=15)
        
        # 时间显示
        time_label = tk.Label(toolbar, 
                             text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             font=("微软雅黑", 11),
                             bg="#1e90ff", fg="white")
        time_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        def update_time():
            time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            admin_win.after(1000, update_time)
        update_time()
        
        # ========== 主要内容区域（使用PanedWindow实现伸缩） ==========
        main_paned = ttk.PanedWindow(admin_win, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧面板（统计信息）
        left_frame = tk.Frame(main_paned, bg="white", relief="solid", bd=1)
        main_paned.add(left_frame, weight=1)
        
        stats_title = tk.Label(left_frame, text="系统统计", 
                              font=("微软雅黑", 16, "bold"),
                              bg="#1e90ff", fg="white")
        stats_title.pack(fill=tk.X, pady=0)
        
        stats_frame = tk.Frame(left_frame, bg="white")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 右侧面板（标签页）
        right_frame = tk.Frame(main_paned, bg="white", relief="solid", bd=1)
        main_paned.add(right_frame, weight=3)
        
        # 创建标签页
        notebook = ttk.Notebook(right_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 用户管理标签页
        user_frame = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(user_frame, text="用户管理")
        
        # 计费管理标签页
        billing_frame = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(billing_frame, text="计费管理")
        
        # 统计报表标签页
        report_frame = tk.Frame(notebook, bg="#f5f5f5")
        notebook.add(report_frame, text="统计报表")
        
        # ========== 用户管理界面 ==========
        # 创建用户管理内部的PanedWindow
        user_paned = ttk.PanedWindow(user_frame, orient=tk.HORIZONTAL)
        user_paned.pack(fill=tk.BOTH, expand=True)
        
        # 用户列表区域
        user_list_container = tk.Frame(user_paned, bg="white", relief="solid", bd=1)
        user_paned.add(user_list_container, weight=2)
        
        user_list_title = tk.Label(user_list_container, text="用户列表", 
                                  font=("微软雅黑", 14, "bold"),
                                  bg="#1e90ff", fg="white")
        user_list_title.pack(fill=tk.X, pady=0)
        
        # 工具栏
        tool_frame = tk.Frame(user_list_container, bg="white")
        tool_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 搜索框
        search_label = tk.Label(tool_frame, text="搜索:", 
                               font=("微软雅黑", 10),
                               bg="white")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = tk.Entry(tool_frame, font=("微软雅黑", 10), width=15)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 用户列表
        columns = ("用户名", "邮箱", "角色", "余额", "注册时间", "最后登录")
        tree = ttk.Treeview(user_list_container, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            if col == "余额":
                tree.column(col, width=100)
            elif col == "用户名":
                tree.column(col, width=100)
            elif col == "邮箱":
                tree.column(col, width=150)
            else:
                tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(user_list_container, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        
        # 按钮框架
        button_frame = tk.Frame(user_list_container, bg="white")
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 右侧操作区域
        user_operation_container = tk.Frame(user_paned, bg="white", relief="solid", bd=1)
        user_paned.add(user_operation_container, weight=1)
        
        operation_title = tk.Label(user_operation_container, text="用户操作", 
                                  font=("微软雅黑", 14, "bold"),
                                  bg="#1e90ff", fg="white")
        operation_title.pack(fill=tk.X, pady=0)
        
        operation_frame = tk.Frame(user_operation_container, bg="white")
        operation_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        def refresh_user_list(search_text=""):
            """刷新用户列表"""
            for item in tree.get_children():
                tree.delete(item)
            
            users = self.user_manager.get_all_users()
            for username, info in users.items():
                if search_text and search_text.lower() not in username.lower():
                    continue
                
                role_display = {
                    "admin": "管理员",
                    "user": "普通用户",
                    "test": "测试用户"
                }.get(info.get("role"), "普通用户")
                
                tree.insert("", tk.END, values=(
                    username,
                    info.get("email", "未设置"),
                    role_display,
                    f"{info.get('balance', 0):.2f}",
                    info.get("register_time", "未知"),
                    info.get("last_login", "从未登录")
                ))
        
        def search_users():
            search_text = search_entry.get().strip()
            refresh_user_list(search_text)
        
        search_btn = tk.Button(tool_frame, text="搜索", 
                              font=("微软雅黑", 10),
                              bg="#1e90ff", fg="white",
                              cursor="hand2",
                              command=search_users)
        search_btn.pack(side=tk.LEFT)
        
        def delete_selected_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择要删除的用户")
                return
            
            username = tree.item(selected[0])['values'][0]
            if username == "admin":
                messagebox.showerror("错误", "不能删除超级管理员账户")
                return
            
            result = messagebox.askyesno("确认", f"确定要删除用户 '{username}' 吗？")
            if result:
                success, msg = self.user_manager.delete_user(username)
                if success:
                    messagebox.showinfo("成功", msg)
                    refresh_user_list()
                    update_stats()
                else:
                    messagebox.showerror("错误", msg)
        
        def edit_selected_user():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择要编辑的用户")
                return
            
            username = tree.item(selected[0])['values'][0]
            self.edit_user_dialog(admin_win, username, lambda: [refresh_user_list(), update_stats()])
        
        add_user_btn = tk.Button(button_frame, text="➕ 新建用户", 
                                font=("微软雅黑", 10, "bold"),
                                bg="#28a745", fg="white",
                                cursor="hand2",
                                command=lambda: self.show_add_user_dialog(admin_win, lambda: [refresh_user_list(), update_stats()]))
        add_user_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(button_frame, text="删除用户", 
                              font=("微软雅黑", 10),
                              bg="#ff6b6b", fg="white",
                              cursor="hand2",
                              command=delete_selected_user)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        edit_btn = tk.Button(button_frame, text="编辑用户", 
                            font=("微软雅黑", 10),
                            bg="#4ecdc4", fg="white",
                            cursor="hand2",
                            command=edit_selected_user)
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(button_frame, text="刷新列表", 
                               font=("微软雅黑", 10),
                               bg="#95e1d3", fg="white",
                               cursor="hand2",
                               command=lambda: refresh_user_list())
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 初始化用户列表
        refresh_user_list()
        
        def update_stats():
            """更新统计数据"""
            users = self.user_manager.get_all_users()
            total = len(users)
            admin = sum(1 for u in users.values() if u.get("role") == "admin")
            normal = sum(1 for u in users.values() if u.get("role") == "user")
            test = sum(1 for u in users.values() if u.get("role") == "test")
            total_balance = sum(u.get("balance", 0) for u in users.values())
            
            # 清空原有统计
            for widget in stats_frame.winfo_children():
                widget.destroy()
            
            stats = [
                ("总用户数", total),
                ("管理员数", admin),
                ("普通用户数", normal),
                ("测试用户数", test),
                ("总余额", f"{total_balance:.2f}")
            ]
            
            for i, (label, value) in enumerate(stats):
                stat_frame = tk.Frame(stats_frame, bg="white")
                stat_frame.pack(fill=tk.X, pady=10)
                
                label_widget = tk.Label(stat_frame, text=label, 
                                       font=("微软雅黑", 12),
                                       bg="white", fg="#666666")
                label_widget.pack(side=tk.LEFT)
                
                value_widget = tk.Label(stat_frame, text=str(value), 
                                       font=("微软雅黑", 18, "bold"),
                                       bg="white", fg="#1e90ff")
                value_widget.pack(side=tk.RIGHT)
        
        update_stats()
        
        # ========== 计费管理界面 ==========
        billing_paned = ttk.PanedWindow(billing_frame, orient=tk.HORIZONTAL)
        billing_paned.pack(fill=tk.BOTH, expand=True)
        
        # 用户选择区域
        user_select_container = tk.Frame(billing_paned, bg="white", relief="solid", bd=1)
        billing_paned.add(user_select_container, weight=1)
        
        user_select_title = tk.Label(user_select_container, text="用户列表", 
                                    font=("微软雅黑", 14, "bold"),
                                    bg="#1e90ff", fg="white")
        user_select_title.pack(fill=tk.X, pady=0)
        
        billing_user_listbox = tk.Listbox(user_select_container, font=("微软雅黑", 11), height=20)
        billing_user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 操作区域
        billing_operation_container = tk.Frame(billing_paned, bg="white", relief="solid", bd=1)
        billing_paned.add(billing_operation_container, weight=2)
        
        billing_operation_title = tk.Label(billing_operation_container, text="余额操作", 
                                          font=("微软雅黑", 14, "bold"),
                                          bg="#1e90ff", fg="white")
        billing_operation_title.pack(fill=tk.X, pady=0)
        
        # 操作表单
        op_form_frame = tk.Frame(billing_operation_container, bg="white")
        op_form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        selected_user_display = tk.Label(op_form_frame, text="当前用户: 未选择", 
                                        font=("微软雅黑", 12, "bold"),
                                        bg="white", fg="#1e90ff")
        selected_user_display.grid(row=0, column=0, columnspan=3, pady=10, sticky="w")
        
        current_balance_display = tk.Label(op_form_frame, text="当前余额: 0", 
                                          font=("微软雅黑", 14, "bold"),
                                          bg="white", fg="#28a745")
        current_balance_display.grid(row=1, column=0, columnspan=3, pady=10, sticky="w")
        
        op_type_label = tk.Label(op_form_frame, text="操作类型:", 
                                font=("微软雅黑", 12),
                                bg="white", fg="#666666")
        op_type_label.grid(row=2, column=0, sticky="w", pady=10)
        
        billing_op_var = tk.StringVar(value="add")
        add_radio_billing = tk.Radiobutton(op_form_frame, text="增加余额", 
                                          variable=billing_op_var, value="add",
                                          font=("微软雅黑", 10),
                                          bg="white")
        add_radio_billing.grid(row=2, column=1, sticky="w", pady=10)
        
        subtract_radio_billing = tk.Radiobutton(op_form_frame, text="扣除余额", 
                                               variable=billing_op_var, value="subtract",
                                               font=("微软雅黑", 10),
                                               bg="white")
        subtract_radio_billing.grid(row=2, column=2, sticky="w", pady=10)
        
        amount_label_billing = tk.Label(op_form_frame, text="金额:", 
                                       font=("微软雅黑", 12),
                                       bg="white", fg="#666666")
        amount_label_billing.grid(row=3, column=0, sticky="w", pady=10)
        
        amount_entry_billing = tk.Entry(op_form_frame, font=("微软雅黑", 12), width=20)
        amount_entry_billing.grid(row=3, column=1, columnspan=2, pady=10, sticky="w")
        
        desc_label_billing = tk.Label(op_form_frame, text="描述:", 
                                     font=("微软雅黑", 12),
                                     bg="white", fg="#666666")
        desc_label_billing.grid(row=4, column=0, sticky="w", pady=10)
        
        desc_entry_billing = tk.Entry(op_form_frame, font=("微软雅黑", 12), width=30)
        desc_entry_billing.grid(row=4, column=1, columnspan=2, pady=10, sticky="w")
        
        # 消费记录区域
        records_frame_billing = tk.Frame(billing_operation_container, bg="white", relief="solid", bd=1)
        records_frame_billing.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 10))
        
        records_title_billing = tk.Label(records_frame_billing, text="消费记录", 
                                        font=("微软雅黑", 12, "bold"),
                                        bg="#f0f0f0", fg="#333333")
        records_title_billing.pack(fill=tk.X, pady=0)
        
        billing_columns = ("时间", "操作", "金额", "变更前", "变更后", "描述", "操作员")
        billing_tree = ttk.Treeview(records_frame_billing, columns=billing_columns, show="headings", height=8)
        
        for col in billing_columns:
            billing_tree.heading(col, text=col)
            if col == "时间":
                billing_tree.column(col, width=150)
            elif col == "描述":
                billing_tree.column(col, width=120)
            else:
                billing_tree.column(col, width=80)
        
        billing_scrollbar = ttk.Scrollbar(records_frame_billing, orient=tk.VERTICAL, command=billing_tree.yview)
        billing_tree.configure(yscrollcommand=billing_scrollbar.set)
        
        billing_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        billing_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_billing_user_list():
            billing_user_listbox.delete(0, tk.END)
            users = self.user_manager.get_all_users()
            for username, info in users.items():
                balance = info.get("balance", 0)
                role_display = {
                    "admin": "管理员",
                    "user": "普通用户",
                    "test": "测试用户"
                }.get(info.get("role"), "普通用户")
                billing_user_listbox.insert(tk.END, f"{username} ({role_display}) - 余额: {balance:.2f}")
        
        refresh_billing_user_list()
        
        def update_billing_selected_user():
            selection = billing_user_listbox.curselection()
            if selection:
                selected_text = billing_user_listbox.get(selection[0])
                username = selected_text.split(" ")[0]
                balance = self.user_manager.get_user_balance(username)
                selected_user_display.config(text=f"当前用户: {username}")
                current_balance_display.config(text=f"当前余额: {balance:.2f}")
                return username
            return None
        
        def on_billing_user_select(event):
            update_billing_selected_user()
            refresh_billing_records()
        
        billing_user_listbox.bind('<<ListboxSelect>>', on_billing_user_select)
        
        def perform_billing_operation():
            username = update_billing_selected_user()
            if not username:
                messagebox.showwarning("警告", "请先选择用户")
                return
            
            try:
                amount = float(amount_entry_billing.get())
                if amount <= 0:
                    messagebox.showwarning("警告", "金额必须大于0")
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的金额")
                return
            
            operation = billing_op_var.get()
            description = desc_entry_billing.get().strip()
            if not description:
                description = f"{'增加' if operation == 'add' else '扣除'}余额"
            
            operator = "admin"
            
            if operation == "add":
                success, msg = self.user_manager.update_balance(username, amount, description, operator)
            else:
                success, msg = self.user_manager.update_balance(username, -amount, description, operator)
            
            if success:
                messagebox.showinfo("成功", msg)
                refresh_billing_user_list()
                update_billing_selected_user()
                refresh_billing_records()
                amount_entry_billing.delete(0, tk.END)
                desc_entry_billing.delete(0, tk.END)
                update_stats()
                refresh_user_list()
            else:
                messagebox.showerror("错误", msg)
        
        def refresh_billing_records():
            for item in billing_tree.get_children():
                billing_tree.delete(item)
            
            username = update_billing_selected_user()
            if username:
                records = self.user_manager.get_user_billing_records(username)
                for record in records:
                    operation_type = "增加" if record["amount"] > 0 else "扣除"
                    billing_tree.insert("", tk.END, values=(
                        record["time"],
                        operation_type,
                        f"{record['amount']:+.2f}",
                        f"{record['old_balance']:.2f}",
                        f"{record['new_balance']:.2f}",
                        record["description"],
                        record["operator"]
                    ))
        
        op_button_frame = tk.Frame(op_form_frame, bg="white")
        op_button_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        submit_billing_btn = tk.Button(op_button_frame, text="执行操作", 
                                      font=("微软雅黑", 11, "bold"),
                                      width=12, height=1,
                                      bg="#1e90ff", fg="white",
                                      relief="flat", cursor="hand2",
                                      command=perform_billing_operation)
        submit_billing_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_records_btn = tk.Button(op_button_frame, text="刷新记录", 
                                       font=("微软雅黑", 10),
                                       bg="#95e1d3", fg="white",
                                       cursor="hand2",
                                       command=refresh_billing_records)
        refresh_records_btn.pack(side=tk.LEFT, padx=5)
        
        # ========== 统计报表界面 ==========
        report_content_frame = tk.Frame(report_frame, bg="white", relief="solid", bd=1)
        report_content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        report_title = tk.Label(report_content_frame, text="系统统计报表", 
                               font=("微软雅黑", 18, "bold"),
                               bg="white", fg="#333333")
        report_title.pack(pady=20)
        
        # 统计信息
        stats_text_frame = tk.Frame(report_content_frame, bg="white")
        stats_text_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        stats_label = tk.Label(stats_text_frame, text="", 
                              font=("微软雅黑", 12),
                              bg="white", fg="#333333",
                              justify=tk.LEFT)
        stats_label.pack(anchor=tk.W, pady=10)
        
        def refresh_report():
            """刷新统计报表"""
            users = self.user_manager.get_all_users()
            total_users = len(users)
            total_balance = sum(u.get("balance", 0) for u in users.values())
            avg_balance = total_balance / total_users if total_users > 0 else 0
            
            all_records = self.user_manager.get_all_billing_records()
            total_recharge = sum(r["amount"] for r in all_records if r["amount"] > 0)
            total_consume = sum(abs(r["amount"]) for r in all_records if r["amount"] < 0)
            
            stats_info = f"""
            📊 系统统计报表
            
            👥 用户统计：
            • 总用户数：{total_users}
            • 总余额：¥{total_balance:.2f}
            • 平均余额：¥{avg_balance:.2f}
            
            💰 财务统计：
            • 总充值金额：¥{total_recharge:.2f}
            • 总消费金额：¥{total_consume:.2f}
            • 系统总流水：¥{(total_recharge + total_consume):.2f}
            
            📈 用户类型分布：
            • 管理员：{sum(1 for u in users.values() if u.get("role") == "admin")}
            • 普通用户：{sum(1 for u in users.values() if u.get("role") == "user")}
            • 测试用户：{sum(1 for u in users.values() if u.get("role") == "test")}
            """
            
            stats_label.config(text=stats_info)
        
        refresh_report()
        
        # 刷新按钮
        report_button_frame = tk.Frame(report_content_frame, bg="white")
        report_button_frame.pack(pady=10)
        
        refresh_report_btn = tk.Button(report_button_frame, text="刷新报表", 
                                      font=("微软雅黑", 11),
                                      bg="#1e90ff", fg="white",
                                      cursor="hand2",
                                      command=refresh_report)
        refresh_report_btn.pack()
        
        # 底部状态栏
        statusbar = tk.Label(admin_win, text="后台管理系统就绪", 
                            bd=1, relief=tk.SUNKEN, 
                            anchor=tk.W, bg="#e0e0e0")
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 处理窗口关闭事件
        admin_win.protocol("WM_DELETE_WINDOW", lambda: self.on_admin_window_close(admin_win))
    
    def show_add_user_dialog(self, parent, refresh_callback):
        """显示添加用户对话框"""
        dialog = tk.Toplevel(parent)
        dialog.title("添加新用户")
        dialog.geometry("500x600")
        dialog.configure(bg="#f5f5f5")
        dialog.resizable(False, False)
        
        # 居中对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f'500x600+{x}+{y}')
        
        # 标题
        title_label = tk.Label(dialog, text="添加新用户", 
                              font=("微软雅黑", 18, "bold"),
                              bg="#f5f5f5", fg="#333333")
        title_label.pack(pady=(20, 15))
        
        # 用户类型选择
        type_frame = tk.Frame(dialog, bg="#f5f5f5")
        type_frame.pack(pady=10)
        
        user_type_label = tk.Label(type_frame, text="用户类型:", 
                                  font=("微软雅黑", 12),
                                  bg="#f5f5f5", fg="#666666")
        user_type_label.pack(side=tk.LEFT, padx=5)
        
        user_type_var = tk.StringVar(value="normal")
        normal_radio = tk.Radiobutton(type_frame, text="普通用户", 
                                     variable=user_type_var, value="normal",
                                     font=("微软雅黑", 10),
                                     bg="#f5f5f5", command=lambda: toggle_form())
        normal_radio.pack(side=tk.LEFT, padx=5)
        
        test_radio = tk.Radiobutton(type_frame, text="测试用户", 
                                   variable=user_type_var, value="test",
                                   font=("微软雅黑", 10),
                                   bg="#f5f5f5", command=lambda: toggle_form())
        test_radio.pack(side=tk.LEFT, padx=5)
        
        admin_radio = tk.Radiobutton(type_frame, text="管理员", 
                                    variable=user_type_var, value="admin",
                                    font=("微软雅黑", 10),
                                    bg="#f5f5f5", command=lambda: toggle_form())
        admin_radio.pack(side=tk.LEFT, padx=5)
        
        # 普通用户表单
        normal_frame = tk.Frame(dialog, bg="#f5f5f5")
        
        # 用户名
        username_label = tk.Label(normal_frame, text="用户名*:", 
                                 font=("微软雅黑", 12),
                                 bg="#f5f5f5", fg="#666666")
        username_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        username_entry = tk.Entry(normal_frame, font=("微软雅黑", 12),
                                 width=25, relief="solid", bd=1)
        username_entry.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # 邮箱（可选）
        email_label = tk.Label(normal_frame, text="邮箱（可选）:", 
                              font=("微软雅黑", 12),
                              bg="#f5f5f5", fg="#666666")
        email_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        email_entry = tk.Entry(normal_frame, font=("微软雅黑", 12),
                              width=25, relief="solid", bd=1)
        email_entry.grid(row=3, column=0, columnspan=2, pady=(0, 15))
        
        # 密码
        password_label = tk.Label(normal_frame, text="密码*:", 
                                 font=("微软雅黑", 12),
                                 bg="#f5f5f5", fg="#666666")
        password_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        password_entry = tk.Entry(normal_frame, font=("微软雅黑", 12),
                                 width=25, relief="solid", bd=1,
                                 show="*")
        password_entry.grid(row=5, column=0, columnspan=2, pady=(0, 15))
        
        # 确认密码
        confirm_label = tk.Label(normal_frame, text="确认密码*:", 
                                font=("微软雅黑", 12),
                                bg="#f5f5f5", fg="#666666")
        confirm_label.grid(row=6, column=0, sticky="w", pady=(0, 5))
        
        confirm_entry = tk.Entry(normal_frame, font=("微软雅黑", 12),
                                width=25, relief="solid", bd=1,
                                show="*")
        confirm_entry.grid(row=7, column=0, columnspan=2, pady=(0, 25))
        
        # 测试用户表单
        test_frame = tk.Frame(dialog, bg="#f5f5f5")
        
        test_info_label = tk.Label(test_frame, text="测试用户信息将自动生成", 
                                  font=("微软雅黑", 11),
                                  bg="#f5f5f5", fg="#1e90ff")
        test_info_label.pack(pady=20)
        
        test_detail_frame = tk.Frame(test_frame, bg="#f5f5f5")
        test_detail_frame.pack(pady=10)
        
        test_username_label = tk.Label(test_detail_frame, text="用户名格式: ceshiXXXX", 
                                      font=("微软雅黑", 10),
                                      bg="#f5f5f5", fg="#666666")
        test_username_label.pack(pady=5)
        
        test_password_label = tk.Label(test_detail_frame, text="密码格式: 用户名+abc", 
                                      font=("微软雅黑", 10),
                                      bg="#f5f5f5", fg="#666666")
        test_password_label.pack(pady=5)
        
        test_balance_label = tk.Label(test_detail_frame, text="初始余额: 100元", 
                                     font=("微软雅黑", 10),
                                     bg="#f5f5f5", fg="#28a745")
        test_balance_label.pack(pady=5)
        
        test_count_label = tk.Label(test_detail_frame, text="数字部分随机生成且不重复", 
                                   font=("微软雅黑", 10),
                                   bg="#f5f5f5", fg="#666666")
        test_count_label.pack(pady=5)
        
        # 管理员用户表单
        admin_frame = tk.Frame(dialog, bg="#f5f5f5")
        
        admin_username_label = tk.Label(admin_frame, text="用户名*:", 
                                       font=("微软雅黑", 12),
                                       bg="#f5f5f5", fg="#666666")
        admin_username_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        admin_username_entry = tk.Entry(admin_frame, font=("微软雅黑", 12),
                                       width=25, relief="solid", bd=1)
        admin_username_entry.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        admin_email_label = tk.Label(admin_frame, text="邮箱（可选）:", 
                                    font=("微软雅黑", 12),
                                    bg="#f5f5f5", fg="#666666")
        admin_email_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        admin_email_entry = tk.Entry(admin_frame, font=("微软雅黑", 12),
                                    width=25, relief="solid", bd=1)
        admin_email_entry.grid(row=3, column=0, columnspan=2, pady=(0, 15))
        
        admin_password_label = tk.Label(admin_frame, text="密码*:", 
                                       font=("微软雅黑", 12),
                                       bg="#f5f5f5", fg="#666666")
        admin_password_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        admin_password_entry = tk.Entry(admin_frame, font=("微软雅黑", 12),
                                       width=25, relief="solid", bd=1,
                                       show="*")
        admin_password_entry.grid(row=5, column=0, columnspan=2, pady=(0, 15))
        
        admin_confirm_label = tk.Label(admin_frame, text="确认密码*:", 
                                      font=("微软雅黑", 12),
                                      bg="#f5f5f5", fg="#666666")
        admin_confirm_label.grid(row=6, column=0, sticky="w", pady=(0, 5))
        
        admin_confirm_entry = tk.Entry(admin_frame, font=("微软雅黑", 12),
                                      width=25, relief="solid", bd=1,
                                      show="*")
        admin_confirm_entry.grid(row=7, column=0, columnspan=2, pady=(0, 25))
        
        def toggle_form():
            """切换表单显示"""
            # 隐藏所有表单
            normal_frame.pack_forget()
            test_frame.pack_forget()
            admin_frame.pack_forget()
            
            # 显示选中的表单
            if user_type_var.get() == "normal":
                normal_frame.pack(pady=20)
            elif user_type_var.get() == "test":
                test_frame.pack(pady=20)
            elif user_type_var.get() == "admin":
                admin_frame.pack(pady=20)
        
        # 初始显示普通用户表单
        toggle_form()
        
        def create_normal_user():
            """创建普通用户"""
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            # 验证
            if not username:
                messagebox.showwarning("警告", "用户名不能为空！")
                return
            
            if not password:
                messagebox.showwarning("警告", "密码不能为空！")
                return
            
            if password != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致！")
                return
            
            if len(password) < 6:
                messagebox.showerror("错误", "密码长度至少为6位！")
                return
            
            # 验证用户名格式
            if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', username):
                messagebox.showerror("错误", "用户名只能包含字母、数字和中文！")
                return
            
            # 验证邮箱格式
            if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messagebox.showerror("错误", "请输入有效的邮箱地址！")
                return
            
            # 创建用户
            success, msg = self.user_manager.add_user(username, password, email, "user")
            
            if success:
                messagebox.showinfo("成功", f"用户 '{username}' 创建成功！\n初始余额: 0元")
                dialog.destroy()
                refresh_callback()
            else:
                messagebox.showerror("错误", msg)
        
        def create_test_user():
            """创建测试用户"""
            # 生成不重复的测试用户名
            test_username = self.user_manager.generate_test_username()
            test_password = f"{test_username}abc"
            
            # 创建测试用户
            success, msg = self.user_manager.add_test_user(test_username, test_password)
            
            if success:
                # 显示创建成功的测试用户信息
                info_text = f"测试用户创建成功！\n\n用户名: {test_username}\n密码: {test_password}\n邮箱: test@example.com\n初始余额: 100元"
                messagebox.showinfo("成功", info_text)
                dialog.destroy()
                refresh_callback()
            else:
                messagebox.showerror("错误", msg)
        
        def create_admin_user():
            """创建管理员用户"""
            username = admin_username_entry.get().strip()
            email = admin_email_entry.get().strip()
            password = admin_password_entry.get()
            confirm = admin_confirm_entry.get()
            
            # 验证
            if not username:
                messagebox.showwarning("警告", "用户名不能为空！")
                return
            
            if not password:
                messagebox.showwarning("警告", "密码不能为空！")
                return
            
            if password != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致！")
                return
            
            if len(password) < 6:
                messagebox.showerror("错误", "密码长度至少为6位！")
                return
            
            # 验证用户名格式
            if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9]+$', username):
                messagebox.showerror("错误", "用户名只能包含字母、数字和中文！")
                return
            
            # 验证邮箱格式
            if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messagebox.showerror("错误", "请输入有效的邮箱地址！")
                return
            
            # 创建管理员
            success, msg = self.user_manager.add_admin_user(username, password, email)
            
            if success:
                messagebox.showinfo("成功", f"管理员 '{username}' 创建成功！")
                dialog.destroy()
                refresh_callback()
            else:
                messagebox.showerror("错误", msg)
        
        def on_submit():
            """提交创建用户"""
            if user_type_var.get() == "normal":
                create_normal_user()
            elif user_type_var.get() == "test":
                create_test_user()
            elif user_type_var.get() == "admin":
                create_admin_user()
        
        # 按钮框架
        button_frame = tk.Frame(dialog, bg="#f5f5f5")
        button_frame.pack(pady=20)
        
        submit_btn = tk.Button(button_frame, text="创建用户", 
                              font=("微软雅黑", 11, "bold"),
                              width=12, height=1,
                              bg="#1e90ff", fg="white",
                              relief="flat", cursor="hand2",
                              command=on_submit)
        submit_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_frame, text="取消", 
                              font=("微软雅黑", 11),
                              width=12, height=1,
                              bg="#cccccc", fg="white",
                              relief="flat", cursor="hand2",
                              command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # 绑定回车键
        dialog.bind('<Return>', lambda event: on_submit())
    
    def edit_user_dialog(self, parent, username, refresh_callback):
        """编辑用户对话框"""
        users = self.user_manager.get_all_users()
        user_info = users.get(username, {})
        
        dialog = tk.Toplevel(parent)
        dialog.title(f"编辑用户 - {username}")
        dialog.geometry("400x400")
        dialog.configure(bg="#f5f5f5")
        
        # 居中对话框
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f'400x400+{x}+{y}')
        
        # 表单
        frame = tk.Frame(dialog, bg="#f5f5f5")
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # 邮箱
        email_label = tk.Label(frame, text="邮箱:", 
                              font=("微软雅黑", 12),
                              bg="#f5f5f5")
        email_label.grid(row=0, column=0, sticky="w", pady=10)
        
        email_entry = tk.Entry(frame, font=("微软雅黑", 12), width=25)
        email_entry.grid(row=0, column=1, pady=10)
        email_entry.insert(0, user_info.get("email", ""))
        
        # 角色
        role_label = tk.Label(frame, text="角色:", 
                             font=("微软雅黑", 12),
                             bg="#f5f5f5")
        role_label.grid(row=1, column=0, sticky="w", pady=10)
        
        role_var = tk.StringVar(value=user_info.get("role", "user"))
        role_combo = ttk.Combobox(frame, textvariable=role_var, 
                                 values=["user", "test", "admin"], 
                                 state="readonly", width=22)
        role_combo.grid(row=1, column=1, pady=10)
        
        # 新密码（可选）
        password_label = tk.Label(frame, text="新密码（可选）:", 
                                 font=("微软雅黑", 12),
                                 bg="#f5f5f5")
        password_label.grid(row=2, column=0, sticky="w", pady=10)
        
        password_entry = tk.Entry(frame, font=("微软雅黑", 12), 
                                 width=25, show="*")
        password_entry.grid(row=2, column=1, pady=10)
        
        def save_changes():
            updates = {}
            
            email = email_entry.get().strip()
            if email:
                updates["email"] = email
            
            role = role_var.get()
            if role != user_info.get("role"):
                updates["role"] = role
            
            new_password = password_entry.get()
            if new_password:
                if len(new_password) < 6:
                    messagebox.showerror("错误", "密码长度至少6位")
                    return
                updates["password"] = new_password
            
            if updates:
                success = self.user_manager.update_user(username, **updates)
                if success:
                    messagebox.showinfo("成功", "用户信息已更新")
                    refresh_callback()
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "更新失败")
            else:
                dialog.destroy()
        
        # 按钮
        button_frame = tk.Frame(frame, bg="#f5f5f5")
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        save_btn = tk.Button(button_frame, text="保存", 
                            font=("微软雅黑", 10),
                            bg="#1e90ff", fg="white",
                            cursor="hand2",
                            command=save_changes)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(button_frame, text="取消", 
                              font=("微软雅黑", 10),
                              bg="#cccccc", fg="white",
                              cursor="hand2",
                              command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def backup_data(self):
        """备份数据"""
        import shutil
        backup_file = f"users_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        billing_backup_file = f"billing_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            shutil.copy("users_data.json", backup_file)
            shutil.copy("billing_data.json", billing_backup_file)
            messagebox.showinfo("成功", f"数据已备份到:\n{backup_file}\n{billing_backup_file}")
        except Exception as e:
            messagebox.showerror("错误", f"备份失败: {str(e)}")
    
    def show_main_window(self, username):
        """显示普通用户主窗口"""
        main_win = tk.Toplevel(self.window)
        main_win.title("主界面")
        main_win.geometry("1000x700")
        main_win.configure(bg="#f5f5f5")
        
        # 居中主窗口
        main_win.update_idletasks()
        x = (main_win.winfo_screenwidth() // 2) - (1000 // 2)
        y = (main_win.winfo_screenheight() // 2) - (700 // 2)
        main_win.geometry(f'1000x700+{x}+{y}')
        
        # 创建菜单栏
        menubar = tk.Menu(main_win)
        main_win.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出登录", command=lambda: self.logout(main_win))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)
        
        # 创建顶部工具栏
        toolbar = tk.Frame(main_win, bg="#1e90ff", height=60)
        toolbar.pack(fill=tk.X)
        
        # 左上角显示欢迎某某某用户
        welcome_label = tk.Label(toolbar, 
                                text=f"欢迎，{username}！", 
                                font=("微软雅黑", 16, "bold"),
                                bg="#1e90ff", fg="white")
        welcome_label.pack(side=tk.LEFT, padx=30, pady=15)
        
        # 右侧显示时间和余额
        balance = self.user_manager.get_user_balance(username)
        balance_label = tk.Label(toolbar, 
                                text=f"余额: {balance:.2f} 元", 
                                font=("微软雅黑", 12, "bold"),
                                bg="#1e90ff", fg="#ffd700")
        balance_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        time_label = tk.Label(toolbar, 
                             text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             font=("微软雅黑", 11),
                             bg="#1e90ff", fg="white")
        time_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        def update_time_and_balance():
            time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            new_balance = self.user_manager.get_user_balance(username)
            balance_label.config(text=f"余额: {new_balance:.2f} 元")
            main_win.after(1000, update_time_and_balance)
        update_time_and_balance()
        
        # 退出登录按钮
        logout_btn = tk.Button(toolbar, text="退出登录", 
                              font=("微软雅黑", 10),
                              bg="#ff6b6b", fg="white",
                              relief="flat", cursor="hand2",
                              command=lambda: self.logout(main_win))
        logout_btn.pack(side=tk.RIGHT, padx=10, pady=12)
        
        # 主要内容区域
        main_frame = tk.Frame(main_win, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # 欢迎卡片
        welcome_card = tk.Frame(main_frame, bg="white", relief="flat", bd=0)
        welcome_card.pack(fill=tk.BOTH, expand=True)
        welcome_card.configure(highlightbackground="#e0e0e0", highlightthickness=1)
        
        # 大标题
        big_title = tk.Label(welcome_card, 
                            text="欢迎使用系统", 
                            font=("微软雅黑", 32, "bold"),
                            bg="white", fg="#333333")
        big_title.pack(pady=(60, 20))
        
        # 副标题
        subtitle = tk.Label(welcome_card, 
                           text="您已成功登录系统", 
                           font=("微软雅黑", 16),
                           bg="white", fg="#666666")
        subtitle.pack(pady=10)
        
        # 分隔线
        separator = tk.Frame(welcome_card, bg="#e0e0e0", height=2)
        separator.pack(fill=tk.X, padx=100, pady=30)
        
        # 用户信息简洁显示
        info_frame = tk.Frame(welcome_card, bg="white")
        info_frame.pack(pady=20)
        
        # 获取用户信息
        user_info = self.user_manager.get_all_users().get(username, {})
        
        user_avatar = tk.Label(info_frame, text="👤", 
                              font=("微软雅黑", 48),
                              bg="white", fg="#1e90ff")
        user_avatar.grid(row=0, column=0, rowspan=4, padx=20)
        
        info_text = f"当前登录用户：{username}\n用户邮箱：{user_info.get('email', '未设置')}\n账户余额：{user_info.get('balance', 0):.2f} 元\n登录时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        user_info_label = tk.Label(info_frame, text=info_text, 
                                  font=("微软雅黑", 12),
                                  bg="white", fg="#555555",
                                  justify=tk.LEFT)
        user_info_label.grid(row=0, column=1, sticky="w")
        
        # 消费记录按钮
        def show_my_records():
            records_win = tk.Toplevel(main_win)
            records_win.title("我的消费记录")
            records_win.geometry("900x500")
            records_win.configure(bg="#f5f5f5")
            
            records_win.update_idletasks()
            x = (records_win.winfo_screenwidth() // 2) - (900 // 2)
            y = (records_win.winfo_screenheight() // 2) - (500 // 2)
            records_win.geometry(f'900x500+{x}+{y}')
            
            title = tk.Label(records_win, text="我的消费记录", 
                            font=("微软雅黑", 18, "bold"),
                            bg="#1e90ff", fg="white")
            title.pack(fill=tk.X, pady=0)
            
            columns = ("时间", "操作", "金额", "变更前", "变更后", "描述", "操作员")
            tree = ttk.Treeview(records_win, columns=columns, show="headings", height=20)
            
            for col in columns:
                tree.heading(col, text=col)
                if col == "时间":
                    tree.column(col, width=150)
                elif col == "描述":
                    tree.column(col, width=150)
                else:
                    tree.column(col, width=100)
            
            scrollbar = ttk.Scrollbar(records_win, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            records = self.user_manager.get_user_billing_records(username)
            for record in records:
                operation_type = "增加" if record["amount"] > 0 else "扣除"
                tree.insert("", tk.END, values=(
                    record["time"],
                    operation_type,
                    f"{record['amount']:+.2f}",
                    f"{record['old_balance']:.2f}",
                    f"{record['new_balance']:.2f}",
                    record["description"],
                    record["operator"]
                ))
        
        records_btn = tk.Button(welcome_card, text="查看消费记录", 
                               font=("微软雅黑", 12),
                               bg="#4ecdc4", fg="white",
                               cursor="hand2",
                               command=show_my_records)
        records_btn.pack(pady=20)
        
        # 底部状态栏
        statusbar = tk.Label(main_win, text="系统就绪", 
                            bd=1, relief=tk.SUNKEN, 
                            anchor=tk.W, bg="#e0e0e0",
                            font=("微软雅黑", 9))
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 处理窗口关闭事件
        main_win.protocol("WM_DELETE_WINDOW", lambda: self.on_main_window_close(main_win))
    
    def show_about(self):
        """显示关于信息"""
        about_text = """用户管理系统 v7.0

功能特性：
- 用户数据持久化存储
- 完整的计费管理系统
- 支持余额增加和扣除
- 详细的消费记录
- 管理员后台管理
- 支持创建普通用户、测试用户和管理员
- 测试用户自动生成不重复用户名
- 数据备份功能
- 统计报表功能
- 窗口伸缩功能

© 2024 版权所有"""
        messagebox.showinfo("关于", about_text)
    
    def logout(self, window):
        """退出登录"""
        result = messagebox.askyesno("确认", "确定要退出登录吗？")
        if result:
            window.destroy()
            self.window.deiconify()
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.username_entry.focus()
    
    def on_main_window_close(self, main_window):
        """处理主窗口关闭事件"""
        result = messagebox.askyesno("确认", "确定要退出程序吗？")
        if result:
            main_window.destroy()
            self.window.quit()
    
    def on_admin_window_close(self, admin_window):
        """处理管理员窗口关闭事件"""
        result = messagebox.askyesno("确认", "确定要退出程序吗？")
        if result:
            admin_window.destroy()
            self.window.quit()
    
    def show_register_window(self, event=None):
        """显示注册窗口"""
        register_win = tk.Toplevel(self.window)
        register_win.title("注册账号")
        register_win.geometry("400x550")
        register_win.configure(bg="#f5f5f5")
        register_win.resizable(False, False)
        
        # 居中注册窗口
        register_win.update_idletasks()
        x = (register_win.winfo_screenwidth() // 2) - (400 // 2)
        y = (register_win.winfo_screenheight() // 2) - (550 // 2)
        register_win.geometry(f'400x550+{x}+{y}')
        
        # 注册标题
        title_label = tk.Label(register_win, text="注册新账号", 
                               font=("微软雅黑", 20, "bold"),
                               bg="#f5f5f5", fg="#333333")
        title_label.pack(pady=(40, 30))
        
        # 注册表单框架
        register_frame = tk.Frame(register_win, bg="#f5f5f5")
        register_frame.pack(pady=20)
        
        # 用户名
        reg_username_label = tk.Label(register_frame, text="用户名*:", 
                                      font=("微软雅黑", 12),
                                      bg="#f5f5f5", fg="#666666")
        reg_username_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        reg_username_entry = tk.Entry(register_frame, font=("微软雅黑", 12),
                                      width=25, relief="solid", bd=1)
        reg_username_entry.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        
        # 邮箱（可选）
        email_label = tk.Label(register_frame, text="邮箱（可选）:", 
                               font=("微软雅黑", 12),
                               bg="#f5f5f5", fg="#666666")
        email_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        reg_email_entry = tk.Entry(register_frame, font=("微软雅黑", 12),
                                   width=25, relief="solid", bd=1)
        reg_email_entry.grid(row=3, column=0, columnspan=2, pady=(0, 15))
        
        # 密码
        reg_password_label = tk.Label(register_frame, text="密码*:", 
                                      font=("微软雅黑", 12),
                                      bg="#f5f5f5", fg="#666666")
        reg_password_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        reg_password_entry = tk.Entry(register_frame, font=("微软雅黑", 12),
                                      width=25, relief="solid", bd=1,
                                      show="*")
        reg_password_entry.grid(row=5, column=0, columnspan=2, pady=(0, 15))
        
        # 确认密码
        confirm_label = tk.Label(register_frame, text="确认密码*:", 
                                 font=("微软雅黑", 12),
                                 bg="#f5f5f5", fg="#666666")
        confirm_label.grid(row=6, column=0, sticky="w", pady=(0, 5))
        
        reg_confirm_entry = tk.Entry(register_frame, font=("微软雅黑", 12),
                                     width=25, relief="solid", bd=1,
                                     show="*")
        reg_confirm_entry.grid(row=7, column=0, columnspan=2, pady=(0, 25))
        
        def register():
            """注册验证"""
            username = reg_username_entry.get().strip()
            email = reg_email_entry.get().strip()
            password = reg_password_entry.get()
            confirm = reg_confirm_entry.get()
            
            # 验证必填项
            if not username:
                messagebox.showwarning("警告", "用户名不能为空！")
                return
            
            if not password:
                messagebox.showwarning("警告", "密码不能为空！")
                return
            
            if not confirm:
                messagebox.showwarning("警告", "请确认密码！")
                return
            
            # 验证密码一致性
            if password != confirm:
                messagebox.showerror("错误", "两次输入的密码不一致！")
                return
            
            # 验证密码强度
            if len(password) < 6:
                messagebox.showerror("错误", "密码长度至少为6位！")
                return
            
            # 验证邮箱格式
            if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                messagebox.showerror("错误", "请输入有效的邮箱地址！")
                return
            
            # 注册用户
            success, msg = self.user_manager.add_user(username, password, email, "user")
            
            if success:
                messagebox.showinfo("注册成功", f"账号 '{username}' 注册成功！\n请登录。")
                register_win.destroy()
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, username)
                self.password_entry.focus()
            else:
                messagebox.showerror("注册失败", msg)
        
        # 注册按钮
        register_button = tk.Button(register_frame, text="注册", 
                                    font=("微软雅黑", 12, "bold"),
                                    width=20, height=1,
                                    bg="#1e90ff", fg="white",
                                    relief="flat", cursor="hand2",
                                    command=register)
        register_button.grid(row=8, column=0, columnspan=2, pady=(0, 15))
        
        # 已有账号提示
        login_label = tk.Label(register_frame, text="已有账号？", 
                               font=("微软雅黑", 10),
                               fg="#666666", bg="#f5f5f5")
        login_label.grid(row=9, column=0, pady=(0, 10))
        
        back_login_label = tk.Label(register_frame, text="去登录", 
                                    font=("微软雅黑", 10),
                                    fg="#1e90ff", bg="#f5f5f5",
                                    cursor="hand2")
        back_login_label.grid(row=9, column=1, sticky="w", pady=(0, 10))
        back_login_label.bind("<Button-1>", lambda e: register_win.destroy())
        
        # 绑定回车键注册
        register_win.bind('<Return>', lambda event: register())
    
    def run(self):
        """运行程序"""
        self.window.mainloop()

# 运行登录界面
if __name__ == "__main__":
    app = LoginWindow()
    app.run()