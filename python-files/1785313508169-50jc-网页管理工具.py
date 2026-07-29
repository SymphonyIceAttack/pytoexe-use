import os
import json
import webbrowser
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import re

# ------------------ 数据存储管理 ------------------
DATA_DIR = "user_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
BOOKMARKS_FILE = os.path.join(DATA_DIR, "bookmarks.json")
BACKUP_FILE = os.path.join(DATA_DIR, "bookmarks_backup.json")

def ensure_data_dir():
    """确保数据目录和必要的文件存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    if not os.path.exists(BOOKMARKS_FILE):
        with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_all_bookmarks():
    try:
        with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # 如果JSON损坏，尝试从备份恢复
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

def save_all_bookmarks(all_bookmarks):
    # 先备份当前数据
    try:
        if os.path.exists(BOOKMARKS_FILE):
            with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                current_data = f.read()
            with open(BACKUP_FILE, "w", encoding="utf-8") as f:
                f.write(current_data)
    except:
        pass
    
    with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_bookmarks, f, indent=2, ensure_ascii=False)

def repair_data():
    """修复损坏的数据"""
    try:
        all_bookmarks = load_all_bookmarks()
        repaired = False
        
        for username in all_bookmarks:
            bookmarks = all_bookmarks[username]
            # 修复每个书签数据
            for bid in list(bookmarks.keys()):
                if not isinstance(bookmarks[bid], dict):
                    del bookmarks[bid]
                    repaired = True
                    continue
                    
                # 确保必要字段存在
                if "name" not in bookmarks[bid] or not bookmarks[bid]["name"]:
                    bookmarks[bid]["name"] = f"未命名_{bid}"
                    repaired = True
                if "url" not in bookmarks[bid] or not bookmarks[bid]["url"]:
                    bookmarks[bid]["url"] = "http://example.com"
                    repaired = True
                if "category" not in bookmarks[bid]:
                    bookmarks[bid]["category"] = "默认分类"
                    repaired = True
                if "order" not in bookmarks[bid]:
                    bookmarks[bid]["order"] = int(bid)
                    repaired = True
                    
                # 清理特殊字符
                bookmarks[bid]["name"] = clean_text(bookmarks[bid]["name"])
                bookmarks[bid]["url"] = clean_text(bookmarks[bid]["url"])
                bookmarks[bid]["category"] = clean_text(bookmarks[bid]["category"])
        
        if repaired:
            save_all_bookmarks(all_bookmarks)
            return True
        return False
    except:
        return False

def clean_text(text):
    """清理文本中的特殊字符"""
    if not text:
        return ""
    # 移除控制字符
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    # 移除多余的空白
    text = ' '.join(text.split())
    return text

# ------------------ 窗口居中工具 ------------------
def center_window(window, width, height):
    """将窗口居中显示"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

# ------------------ 登录窗口 ------------------
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 登录 - 网址管理")
        center_window(root, 360, 280)
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f4fa")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#f0f4fa", font=("微软雅黑", 10))
        style.configure("TButton", font=("微软雅黑", 10), padding=6)
        style.configure("TEntry", font=("微软雅黑", 10))

        title_label = tk.Label(root, text="📁 网址管理助手", font=("微软雅黑", 16, "bold"), bg="#f0f4fa", fg="#2c3e50")
        title_label.pack(pady=(15, 10))

        frame_user = tk.Frame(root, bg="#f0f4fa")
        frame_user.pack(pady=6)
        tk.Label(frame_user, text="👤 用户名", font=("微软雅黑", 10), bg="#f0f4fa", width=10, anchor="e").pack(side=tk.LEFT)
        self.entry_username = ttk.Entry(frame_user, width=20, font=("微软雅黑", 10))
        self.entry_username.pack(side=tk.LEFT, padx=5)

        frame_pass = tk.Frame(root, bg="#f0f4fa")
        frame_pass.pack(pady=6)
        tk.Label(frame_pass, text="🔑 密码", font=("微软雅黑", 10), bg="#f0f4fa", width=10, anchor="e").pack(side=tk.LEFT)
        self.entry_password = ttk.Entry(frame_pass, width=20, font=("微软雅黑", 10), show="*")
        self.entry_password.pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(root, bg="#f0f4fa")
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="登录", command=self.login, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="注册", command=self.register, width=10).pack(side=tk.LEFT, padx=10)

        tip_label = tk.Label(root, text="💡 注册后请使用新账号登录", font=("微软雅黑", 9), bg="#f0f4fa", fg="#7f8c8d")
        tip_label.pack(pady=(5, 10))

        ensure_data_dir()
        # 启动时尝试修复数据
        repair_data()
        self.root.bind("<Return>", lambda e: self.login())

    def login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        users = load_users()
        if username in users and users[username] == password:
            self.root.destroy()
            open_main_app(username)
        else:
            messagebox.showerror("错误", "用户名或密码错误")

    def register(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        users = load_users()
        if username in users:
            messagebox.showerror("错误", "用户名已存在")
            return

        users[username] = password
        save_users(users)
        messagebox.showinfo("成功", "🎉 注册成功！请登录")
        self.entry_password.delete(0, tk.END)

# ------------------ 主应用窗口（文件夹分类） ------------------
class MainApp:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title(f"📚 网址管理 - {username}")
        center_window(root, 900, 650)
        self.root.configure(bg="#f0f4fa")

        # 初始化数据
        self.bookmarks = {}
        self.id_counter = 1
        self.load_user_data()

        # 界面状态
        self.expanded_categories = set()  # 记录展开的分类
        self.current_filter = "全部"  # 当前筛选

        # 创建界面
        self.create_widgets()
        
        # 更新分类列表并刷新显示
        self.update_category_lists()
        self.refresh_tree()

    def load_user_data(self):
        """加载用户数据并初始化结构"""
        all_bookmarks = load_all_bookmarks()
        self.bookmarks = all_bookmarks.get(self.username, {})
        
        # 确保数据结构完整，并修复损坏的数据
        corrupted = []
        for bid in list(self.bookmarks.keys()):
            try:
                if not isinstance(self.bookmarks[bid], dict):
                    corrupted.append(bid)
                    continue
                    
                if "name" not in self.bookmarks[bid] or not self.bookmarks[bid]["name"]:
                    self.bookmarks[bid]["name"] = f"未命名_{bid}"
                if "url" not in self.bookmarks[bid] or not self.bookmarks[bid]["url"]:
                    self.bookmarks[bid]["url"] = "http://example.com"
                if "category" not in self.bookmarks[bid]:
                    self.bookmarks[bid]["category"] = "默认分类"
                if "order" not in self.bookmarks[bid]:
                    self.bookmarks[bid]["order"] = int(bid)
                    
                # 清理特殊字符
                self.bookmarks[bid]["name"] = clean_text(self.bookmarks[bid]["name"])
                self.bookmarks[bid]["url"] = clean_text(self.bookmarks[bid]["url"])
                self.bookmarks[bid]["category"] = clean_text(self.bookmarks[bid]["category"])
            except:
                corrupted.append(bid)
        
        # 删除损坏的数据
        for bid in corrupted:
            del self.bookmarks[bid]
            messagebox.showwarning("数据修复", f"已删除损坏的网址数据 (ID: {bid})")
        
        # 如果有修复，保存数据
        if corrupted:
            self.save_current_bookmarks()
        
        self.id_counter = max([int(k) for k in self.bookmarks.keys()] + [0]) + 1

    def create_widgets(self):
        # 顶部工具栏
        top_frame = tk.Frame(self.root, bg="#f0f4fa", height=40)
        top_frame.pack(fill=tk.X, pady=(10, 5), padx=15)
        top_frame.pack_propagate(False)

        # 用户信息（左）
        user_label = tk.Label(top_frame, text=f"👤 {self.username}", font=("微软雅黑", 11, "bold"), 
                             bg="#f0f4fa", fg="#2c3e50")
        user_label.pack(side=tk.LEFT)

        # 操作按钮（右）
        btn_frame_top = tk.Frame(top_frame, bg="#f0f4fa")
        btn_frame_top.pack(side=tk.RIGHT)
        ttk.Button(btn_frame_top, text="🔑 修改密码", command=self.change_password, width=12).pack(side=tk.LEFT, padx=5)

        # 添加网址区域
        add_frame = tk.Frame(self.root, bg="#ffffff", relief=tk.GROOVE, bd=2)
        add_frame.pack(pady=10, padx=15, fill=tk.X)

        tk.Label(add_frame, text="📝 添加网址", font=("微软雅黑", 11, "bold"), 
                bg="#ffffff", fg="#34495e").pack(anchor="w", padx=10, pady=(8, 5))

        inner_add = tk.Frame(add_frame, bg="#ffffff")
        inner_add.pack(pady=5, padx=10, fill=tk.X)

        # 输入控件
        tk.Label(inner_add, text="名称:", font=("微软雅黑", 10), bg="#ffffff").pack(side=tk.LEFT, padx=2)
        self.entry_name = ttk.Entry(inner_add, width=15, font=("微软雅黑", 10))
        self.entry_name.pack(side=tk.LEFT, padx=5)

        tk.Label(inner_add, text="网址:", font=("微软雅黑", 10), bg="#ffffff").pack(side=tk.LEFT, padx=2)
        self.entry_url = ttk.Entry(inner_add, width=25, font=("微软雅黑", 10))
        self.entry_url.pack(side=tk.LEFT, padx=5)

        tk.Label(inner_add, text="分类:", font=("微软雅黑", 10), bg="#ffffff").pack(side=tk.LEFT, padx=2)
        self.category_var = tk.StringVar(value="默认分类")
        self.category_combo = ttk.Combobox(inner_add, textvariable=self.category_var, width=12, font=("微软雅黑", 10))
        self.category_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(inner_add, text="➕ 添加", command=self.add_bookmark, width=8).pack(side=tk.LEFT, padx=10)

        # 分类管理工具栏
        cat_toolbar = tk.Frame(self.root, bg="#f0f4fa")
        cat_toolbar.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(cat_toolbar, text="📂 分类:", font=("微软雅黑", 10), bg="#f0f4fa").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="全部")
        self.filter_combo = ttk.Combobox(cat_toolbar, textvariable=self.filter_var, width=15, font=("微软雅黑", 10))
        self.filter_combo.pack(side=tk.LEFT, padx=5)
        self.filter_combo.bind("<<ComboboxSelected>>", self.on_filter_change)

        # 分类管理按钮
        cat_btn_frame = tk.Frame(cat_toolbar, bg="#f0f4fa")
        cat_btn_frame.pack(side=tk.LEFT, padx=10)
        ttk.Button(cat_btn_frame, text="➕ 新建文件夹", command=self.create_category, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(cat_btn_frame, text="✏️ 重命名", command=self.rename_category, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(cat_btn_frame, text="🗑️ 删除", command=self.delete_category, width=8).pack(side=tk.LEFT, padx=2)

        # 网址树形列表
        list_title = tk.Label(self.root, text="📋 我的网址列表 (点击文件夹展开/收起)", font=("微软雅黑", 11, "bold"), 
                             bg="#f0f4fa", fg="#34495e")
        list_title.pack(anchor="w", padx=20, pady=(10, 2))

        # 树形列表容器
        list_frame = tk.Frame(self.root, bg="#ffffff", relief=tk.GROOVE, bd=2)
        list_frame.pack(pady=5, padx=15, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(list_frame, yscrollcommand=scrollbar.set, 
                                selectmode="browse", show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.tree.yview)

        # 绑定事件
        self.tree.bind("<Double-Button-1>", self.open_selected)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Button-3>", self.show_context_menu)  # 右键菜单

        # 底部操作按钮
        btn_frame = tk.Frame(self.root, bg="#f0f4fa")
        btn_frame.pack(pady=10)

        btn_style = {"width": 10, "padding": 5}
        ttk.Button(btn_frame, text="🌐 打开", command=self.open_selected, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🗑️ 删除", command=self.delete_selected, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="✏️ 重命名", command=self.rename_selected, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🔗 编辑网址", command=self.edit_url, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="📂 移动分类", command=self.move_to_category, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🔄 展开全部", command=self.expand_all, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="📁 收起全部", command=self.collapse_all, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🔧 修复数据", command=self.manual_repair, **btn_style).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🚪 退出", command=self.logout, **btn_style).pack(side=tk.LEFT, padx=4)

    # ------------------ 右键菜单 ------------------
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # 选中该项
        self.tree.selection_set(item)
        
        # 检查是否是网址
        tags = self.tree.item(item, "tags")
        if "bookmark" in tags:
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="🌐 打开", command=self.open_selected)
            menu.add_command(label="🗑️ 删除", command=self.delete_selected)
            menu.add_command(label="✏️ 重命名", command=self.rename_selected)
            menu.add_command(label="🔗 编辑网址", command=self.edit_url)
            menu.add_command(label="📂 移动分类", command=self.move_to_category)
            menu.add_separator()
            menu.add_command(label="🔧 强制删除", command=self.force_delete_selected)
            menu.post(event.x_root, event.y_root)

    # ------------------ 强制删除功能 ------------------
    def force_delete_selected(self):
        """强制删除选中的网址（绕过数据检查）"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("错误", "请先选中一个网址")
            return
        item = selection[0]
        
        # 检查是否是网址节点
        tags = self.tree.item(item, "tags")
        if "folder" in tags:
            messagebox.showerror("错误", "请选中一个网址，而不是文件夹")
            return
        
        # 直接删除（不检查数据完整性）
        if item in self.bookmarks:
            if messagebox.askyesno("强制删除", f"确定要强制删除这个网址吗？\n这将直接从数据中移除。"):
                del self.bookmarks[item]
                self.save_current_bookmarks()
                self.refresh_tree()
                messagebox.showinfo("成功", "✅ 已强制删除")
        else:
            # 如果数据中不存在，直接从树中移除
            self.tree.delete(item)
            messagebox.showinfo("成功", "✅ 已从列表中移除")

    # ------------------ 手动修复数据 ------------------
    def manual_repair(self):
        """手动修复数据"""
        if messagebox.askyesno("修复数据", "这将尝试修复所有损坏的数据，并清理无效条目。\n确定继续吗？"):
            repaired = repair_data()
            # 重新加载数据
            self.load_user_data()
            self.update_category_lists()
            self.refresh_tree()
            if repaired:
                messagebox.showinfo("成功", "✅ 数据修复完成")
            else:
                messagebox.showinfo("提示", "数据看起来是完整的，无需修复")

    # ------------------ 树形列表管理 ------------------
    def get_all_categories(self):
        """获取所有分类"""
        categories = set()
        for info in self.bookmarks.values():
            if isinstance(info, dict):
                categories.add(info.get("category", "默认分类"))
        # 确保默认分类始终存在
        if not categories:
            categories.add("默认分类")
        return sorted(list(categories))

    def update_category_lists(self):
        """更新所有分类下拉列表"""
        categories = self.get_all_categories()
        
        # 更新添加网址的分类下拉框
        self.category_combo['values'] = categories
        if not self.category_var.get() or self.category_var.get() not in categories:
            self.category_var.set(categories[0] if categories else "默认分类")

        # 更新过滤器下拉框
        filter_cats = ["全部"] + categories
        self.filter_combo['values'] = filter_cats
        if self.filter_var.get() not in filter_cats:
            self.filter_var.set("全部")

    def refresh_tree(self):
        """刷新树形列表"""
        # 清空树
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_cat = self.filter_var.get()
        
        # 获取所有分类
        if filter_cat == "全部":
            categories = self.get_all_categories()
        else:
            categories = [filter_cat] if filter_cat in self.get_all_categories() else []

        # 为每个分类创建文件夹节点
        for category in categories:
            # 统计该分类下的网址数量
            count = sum(1 for info in self.bookmarks.values() 
                       if isinstance(info, dict) and info.get("category", "默认分类") == category)
            
            # 创建文件夹节点
            folder_id = f"folder_{category}"
            folder_text = f"📁 {category} ({count})"
            
            # 检查是否展开
            is_expanded = category in self.expanded_categories
            
            # 添加文件夹节点
            folder_node = self.tree.insert("", "end", folder_id, text=folder_text, 
                                          open=is_expanded, tags=("folder",))
            
            # 如果展开，添加子项
            if is_expanded:
                # 获取该分类下的网址，按order排序
                items = []
                for bid, info in self.bookmarks.items():
                    if isinstance(info, dict) and info.get("category", "默认分类") == category:
                        items.append((info.get("order", int(bid)), bid, info))
                items.sort(key=lambda x: x[0])
                
                for _, bid, info in items:
                    name = info.get("name", "未命名")
                    url = info.get("url", "http://example.com")
                    item_text = f"  🌐 {name}  →  {url}"
                    self.tree.insert(folder_id, "end", bid, text=item_text, tags=("bookmark",))

    def on_tree_click(self, event):
        """处理树节点点击，用于展开/收起文件夹"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # 获取点击的项
        tags = self.tree.item(item, "tags")
        if "folder" in tags:
            # 切换展开状态
            current_state = self.tree.item(item, "open")
            self.tree.item(item, open=not current_state)
            
            # 更新展开状态记录
            text = self.tree.item(item, "text")
            # 从文本中提取分类名
            if "📁 " in text:
                category = text.split("📁 ")[1].split(" (")[0]
                if current_state:
                    if category in self.expanded_categories:
                        self.expanded_categories.remove(category)
                else:
                    self.expanded_categories.add(category)
                
                # 刷新树以更新计数
                self.refresh_tree()

    def on_filter_change(self, event=None):
        """分类筛选变化时刷新"""
        self.refresh_tree()

    def expand_all(self):
        """展开所有文件夹"""
        categories = self.get_all_categories()
        self.expanded_categories = set(categories)
        self.refresh_tree()

    def collapse_all(self):
        """收起所有文件夹"""
        self.expanded_categories.clear()
        self.refresh_tree()

    # ------------------ 分类管理功能 ------------------
    def create_category(self):
        """新建分类文件夹"""
        name = simpledialog.askstring("新建文件夹", "请输入新分类名称:", parent=self.root)
        if name and name.strip():
            name = name.strip()
            categories = self.get_all_categories()
            if name in categories:
                messagebox.showerror("错误", f"文件夹 '{name}' 已存在")
                return
            
            # 创建一个示例网址来保存分类（这样分类就会出现在列表中）
            # 实际上，分类不需要保存，它从网址数据中动态生成
            # 但为了立即显示，我们添加一个临时网址到该分类
            # 或者更简单：直接更新下拉列表和树
            self.update_category_lists()
            self.category_var.set(name)
            
            # 自动展开新分类
            self.expanded_categories.add(name)
            
            # 刷新树显示
            self.refresh_tree()
            
            messagebox.showinfo("成功", f"✅ 文件夹 '{name}' 已创建\n提示：添加网址时选择该分类即可将网址放入此文件夹")

    def rename_category(self):
        """重命名分类"""
        old_name = self.filter_var.get()
        if old_name == "全部":
            messagebox.showerror("错误", "不能重命名'全部'")
            return
        if old_name not in self.get_all_categories():
            messagebox.showerror("错误", "请选择要重命名的分类")
            return

        new_name = simpledialog.askstring("重命名文件夹", f"将 '{old_name}' 重命名为:", 
                                         initialvalue=old_name, parent=self.root)
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name in self.get_all_categories() and new_name != old_name:
                messagebox.showerror("错误", "分类已存在")
                return
            
            # 更新所有网址的分类
            for bid in list(self.bookmarks.keys()):
                if isinstance(self.bookmarks[bid], dict) and self.bookmarks[bid].get("category", "默认分类") == old_name:
                    self.bookmarks[bid]["category"] = new_name
            
            # 更新展开状态
            if old_name in self.expanded_categories:
                self.expanded_categories.remove(old_name)
                self.expanded_categories.add(new_name)
            
            self.save_current_bookmarks()
            self.update_category_lists()
            self.filter_var.set("全部")
            self.refresh_tree()
            messagebox.showinfo("成功", f"✅ 文件夹已重命名为 '{new_name}'")

    def delete_category(self):
        """删除分类"""
        cat_name = self.filter_var.get()
        if cat_name == "全部":
            messagebox.showerror("错误", "不能删除'全部'")
            return
        if cat_name not in self.get_all_categories():
            messagebox.showerror("错误", "请选择要删除的分类")
            return
        if cat_name == "默认分类":
            if not messagebox.askyesno("确认", "确定要删除'默认分类'吗？所有该分类的网址将保留但分类会变为空"):
                return

        count = sum(1 for info in self.bookmarks.values() 
                   if isinstance(info, dict) and info.get("category", "默认分类") == cat_name)
        if count > 0:
            msg = f"文件夹 '{cat_name}' 中有 {count} 个网址，将移至'默认分类'，确定继续吗？"
            if not messagebox.askyesno("确认删除", msg):
                return

        # 移动网址到默认分类
        for bid in list(self.bookmarks.keys()):
            if isinstance(self.bookmarks[bid], dict) and self.bookmarks[bid].get("category", "默认分类") == cat_name:
                self.bookmarks[bid]["category"] = "默认分类"

        # 移除展开状态
        if cat_name in self.expanded_categories:
            self.expanded_categories.remove(cat_name)

        self.save_current_bookmarks()
        self.update_category_lists()
        self.filter_var.set("全部")
        self.refresh_tree()
        messagebox.showinfo("成功", f"✅ 文件夹 '{cat_name}' 已删除")

    # ------------------ 添加和刷新 ------------------
    def add_bookmark(self):
        name = self.entry_name.get().strip()
        url = self.entry_url.get().strip()
        category = self.category_var.get().strip() or "默认分类"
        if not name or not url:
            messagebox.showerror("错误", "名称和网址不能为空")
            return
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        # 清理输入
        name = clean_text(name)
        url = clean_text(url)
        category = clean_text(category)

        max_order = max([info.get("order", 0) for info in self.bookmarks.values() if isinstance(info, dict)] + [0]) + 1

        self.bookmarks[str(self.id_counter)] = {
            "name": name,
            "url": url,
            "category": category,
            "order": max_order
        }
        self.id_counter += 1
        self.save_current_bookmarks()
        self.update_category_lists()
        
        # 确保分类展开
        if category in self.get_all_categories():
            self.expanded_categories.add(category)
        
        self.refresh_tree()
        self.entry_name.delete(0, tk.END)
        self.entry_url.delete(0, tk.END)
        messagebox.showinfo("成功", "✅ 网址已添加")

    def save_current_bookmarks(self):
        """保存当前用户数据"""
        all_bookmarks = load_all_bookmarks()
        all_bookmarks[self.username] = self.bookmarks
        save_all_bookmarks(all_bookmarks)

    # ------------------ 获取选中项 ------------------
    def get_selected_item(self):
        """获取当前选中的树节点"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("错误", "请先选中一个网址")
            return None, None
        item = selection[0]
        
        # 检查是否是网址节点
        tags = self.tree.item(item, "tags")
        if "folder" in tags:
            messagebox.showerror("错误", "请选中一个网址，而不是文件夹")
            return None, None
        
        # 从文本中提取信息
        text = self.tree.item(item, "text")
        if "🌐 " in text:
            # 解析 "  🌐 name  →  url"
            parts = text.split("→")
            if len(parts) == 2:
                name_part = parts[0].strip()
                if "🌐 " in name_part:
                    name_part = name_part.split("🌐 ")[1]
                url_part = parts[1].strip()
                
                # 查找匹配的网址
                for bid, info in self.bookmarks.items():
                    if isinstance(info, dict) and info.get("name") == name_part and info.get("url") == url_part:
                        return bid, info
        return None, None

    def get_selected_id(self):
        """获取选中网址的ID（兼容旧方法）"""
        bid, _ = self.get_selected_item()
        return bid

    # ------------------ 操作功能 ------------------
    def open_selected(self, event=None):
        """打开选中的网址"""
        bid, info = self.get_selected_item()
        if bid and info:
            try:
                webbrowser.open(info["url"])
            except Exception as e:
                messagebox.showerror("错误", f"无法打开网址: {str(e)}")

    def delete_selected(self):
        """删除选中的网址"""
        bid, info = self.get_selected_item()
        if bid and info:
            if messagebox.askyesno("确认删除", f"确定删除 '{info['name']}' 吗？"):
                del self.bookmarks[bid]
                self.save_current_bookmarks()
                self.refresh_tree()

    def rename_selected(self):
        """重命名选中的网址"""
        bid, info = self.get_selected_item()
        if bid and info:
            old_name = info["name"]
            new_name = simpledialog.askstring("重命名", "输入新名称:", 
                                             initialvalue=old_name, parent=self.root)
            if new_name and new_name.strip():
                self.bookmarks[bid]["name"] = clean_text(new_name.strip())
                self.save_current_bookmarks()
                self.refresh_tree()

    def edit_url(self):
        """编辑选中的网址"""
        bid, info = self.get_selected_item()
        if bid and info:
            old_url = info["url"]
            new_url = simpledialog.askstring("编辑网址", "输入新的网址:", 
                                            initialvalue=old_url, parent=self.root)
            if new_url and new_url.strip():
                new_url = clean_text(new_url.strip())
                if not new_url.startswith(("http://", "https://")):
                    new_url = "http://" + new_url
                self.bookmarks[bid]["url"] = new_url
                self.save_current_bookmarks()
                self.refresh_tree()

    def move_to_category(self):
        """移动选中网址到其他分类"""
        bid, info = self.get_selected_item()
        if not bid or not info:
            return

        categories = self.get_all_categories()
        current_cat = info.get("category", "默认分类")
        
        # 创建选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("移动分类")
        center_window(dialog, 300, 180)
        dialog.configure(bg="#f0f4fa")
        dialog.grab_set()

        tk.Label(dialog, text=f"将 '{info['name']}' 移动到:", 
                font=("微软雅黑", 10), bg="#f0f4fa").pack(pady=10)
        
        combo = ttk.Combobox(dialog, values=categories, font=("微软雅黑", 10), width=20)
        combo.set(current_cat)
        combo.pack(pady=10)

        def confirm_move():
            new_cat = combo.get().strip()
            if new_cat:
                if new_cat not in categories:
                    if messagebox.askyesno("新建分类", f"分类 '{new_cat}' 不存在，是否创建？"):
                        # 创建新分类
                        self.update_category_lists()
                    else:
                        return
                self.bookmarks[bid]["category"] = new_cat
                self.save_current_bookmarks()
                self.update_category_lists()
                self.expanded_categories.add(new_cat)
                self.refresh_tree()
                messagebox.showinfo("成功", f"✅ 已移动到文件夹 '{new_cat}'")
                dialog.destroy()

        btn_frame = tk.Frame(dialog, bg="#f0f4fa")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确认", command=confirm_move, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=10)

    # ------------------ 修改密码 ------------------
    def change_password(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("修改密码")
        center_window(dialog, 320, 180)
        dialog.resizable(False, False)
        dialog.configure(bg="#f0f4fa")
        dialog.grab_set()

        tk.Label(dialog, text="🔑 修改密码", font=("微软雅黑", 14, "bold"), 
                bg="#f0f4fa", fg="#2c3e50").pack(pady=(15, 10))

        frame_old = tk.Frame(dialog, bg="#f0f4fa")
        frame_old.pack(pady=5)
        tk.Label(frame_old, text="原密码:", font=("微软雅黑", 10), bg="#f0f4fa", width=8, anchor="e").pack(side=tk.LEFT)
        entry_old = ttk.Entry(frame_old, width=18, font=("微软雅黑", 10), show="*")
        entry_old.pack(side=tk.LEFT, padx=5)

        frame_new = tk.Frame(dialog, bg="#f0f4fa")
        frame_new.pack(pady=5)
        tk.Label(frame_new, text="新密码:", font=("微软雅黑", 10), bg="#f0f4fa", width=8, anchor="e").pack(side=tk.LEFT)
        entry_new = ttk.Entry(frame_new, width=18, font=("微软雅黑", 10), show="*")
        entry_new.pack(side=tk.LEFT, padx=5)

        frame_confirm = tk.Frame(dialog, bg="#f0f4fa")
        frame_confirm.pack(pady=5)
        tk.Label(frame_confirm, text="确认密码:", font=("微软雅黑", 10), bg="#f0f4fa", width=8, anchor="e").pack(side=tk.LEFT)
        entry_confirm = ttk.Entry(frame_confirm, width=18, font=("微软雅黑", 10), show="*")
        entry_confirm.pack(side=tk.LEFT, padx=5)

        def submit_change():
            old_pwd = entry_old.get().strip()
            new_pwd = entry_new.get().strip()
            confirm_pwd = entry_confirm.get().strip()

            if not old_pwd or not new_pwd or not confirm_pwd:
                messagebox.showerror("错误", "所有字段都不能为空")
                return

            users = load_users()
            if self.username not in users or users[self.username] != old_pwd:
                messagebox.showerror("错误", "原密码错误")
                return

            if new_pwd != confirm_pwd:
                messagebox.showerror("错误", "两次输入的新密码不一致")
                return

            if len(new_pwd) < 3:
                messagebox.showerror("错误", "新密码长度至少3位")
                return

            users[self.username] = new_pwd
            save_users(users)
            messagebox.showinfo("成功", "✅ 密码修改成功！")
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg="#f0f4fa")
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="确认修改", command=submit_change, width=12).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=8).pack(side=tk.LEFT, padx=10)

        dialog.bind("<Return>", lambda e: submit_change())

    # ------------------ 退出登录 ------------------
    def logout(self):
        if messagebox.askyesno("退出登录", "确定要退出登录吗？"):
            self.root.destroy()
            new_root = tk.Tk()
            LoginWindow(new_root)
            new_root.mainloop()

# ------------------ 启动函数 ------------------
def open_main_app(username):
    root = tk.Tk()
    MainApp(root, username)
    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()