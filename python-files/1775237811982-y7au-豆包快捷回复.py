import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pyperclip
from PIL import Image, ImageTk
import os
from datetime import datetime

# --- 数据库操作类 ---
class DatabaseManager:
    def __init__(self, db_name="quick_reply.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content_type TEXT NOT NULL, -- 'text', 'image', 'file'
                content_text TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_item(self, category, title, content_type, content_text="", file_path=""):
        self.cursor.execute('''
            INSERT INTO items (category, title, content_type, content_text, file_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (category, title, content_type, content_text, file_path))
        self.conn.commit()

    def get_items(self, category=None):
        if category:
            self.cursor.execute("SELECT * FROM items WHERE category=? ORDER BY created_at DESC", (category,))
        else:
            self.cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
        return self.cursor.fetchall()

    def delete_item(self, item_id):
        self.cursor.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def get_categories(self):
        self.cursor.execute("SELECT DISTINCT category FROM items")
        return [row[0] for row in self.cursor.fetchall()]

# --- 主应用程序类 ---
class QuickReplyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("快捷回复助手")
        self.root.geometry("800x600")
        
        self.db = DatabaseManager()
        self.current_category = None

        self.setup_ui()
        self.refresh_categories()
        self.refresh_list()

    def setup_ui(self):
        # 1. 顶部区域：分类和添加按钮
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="分类:").pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(top_frame, state="readonly", width=15)
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)
        
        ttk.Button(top_frame, text="全部分类", command=self.show_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="➕ 新增内容", command=self.open_add_window).pack(side=tk.RIGHT)

        # 2. 中间区域：列表
        self.list_frame = ttk.Frame(self.root, padding="10")
        self.list_frame.pack(fill=tk.BOTH, expand=True)

        # 3. 底部预览区域
        self.preview_frame = ttk.LabelFrame(self.root, text="预览 / 操作", padding="10", height=150)
        self.preview_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.preview_label = ttk.Label(self.preview_frame, text="点击列表项查看详情")
        self.preview_label.pack()

    def refresh_categories(self):
        cats = self.db.get_categories()
        self.category_combo['values'] = cats

    def refresh_list(self):
        # 清空现有列表
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        items = self.db.get_items(self.current_category)
        
        if not items:
            ttk.Label(self.list_frame, text="暂无数据，请点击右上角添加").pack(pady=20)
            return

        # 动态生成卡片
        for item in items:
            item_id, cat, title, c_type, c_text, c_path, _ = item
            card = ttk.Frame(self.list_frame, borderwidth=1, relief="solid", padding=10)
            card.pack(fill=tk.X, pady=5)

            # 标题和类型标签
            lbl_title = ttk.Label(card, text=f"[{c_type.upper()}] {title}", font=("Arial", 10, "bold"))
            lbl_title.pack(anchor=tk.W)
            
            # 按钮区域
            btn_frame = ttk.Frame(card)
            btn_frame.pack(anchor=tk.E, pady=5)
            
            ttk.Button(btn_frame, text="复制/使用", command=lambda i=item: self.use_item(i)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="删除", command=lambda iid=item_id: self.delete_item(iid)).pack(side=tk.LEFT)

    def on_category_change(self, event):
        self.current_category = self.category_combo.get()
        self.refresh_list()

    def show_all(self):
        self.current_category = None
        self.category_combo.set('')
        self.refresh_list()

    def open_add_window(self):
        # 新建窗口
        win = tk.Toplevel(self.root)
        win.title("新增快捷内容")
        win.geometry("400x450")

        # 表单变量
        var_cat = tk.StringVar()
        var_title = tk.StringVar()
        var_type = tk.StringVar(value="text")
        var_text = tk.StringVar()
        var_path = tk.StringVar()

        # 布局
        ttk.Label(win, text="分类 (如: 问候, 报价):").pack(pady=5)
        ttk.Entry(win, textvariable=var_cat).pack(pady=5)
        
        ttk.Label(win, text="标题 (便于查找):").pack(pady=5)
        ttk.Entry(win, textvariable=var_title).pack(pady=5)

        ttk.Label(win, text="类型:").pack(pady=5)
        type_frame = ttk.Frame(win)
        type_frame.pack()
        ttk.Radiobutton(type_frame, text="纯文字", variable=var_type, value="text").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="图片", variable=var_type, value="image").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="文件", variable=var_type, value="file").pack(side=tk.LEFT)

        # 文字输入
        ttk.Label(win, text="文字内容:").pack(pady=5)
        txt_widget = tk.Text(win, height=5)
        txt_widget.pack(pady=5)

        # 文件选择
        def select_file():
            file_path = filedialog.askopenfilename()
            if file_path:
                var_path.set(file_path)
                lbl_path.config(text=file_path)

        ttk.Button(win, text="选择文件/图片", command=select_file).pack(pady=5)
        lbl_path = ttk.Label(win, text="未选择", foreground="gray")
        lbl_path.pack()

        def save():
            cat = var_cat.get()
            title = var_title.get()
            c_type = var_type.get()
            text_content = txt_widget.get("1.0", tk.END).strip()
            path_content = var_path.get()

            if not cat or not title:
                messagebox.showerror("错误", "分类和标题必填!")
                return
            
            self.db.add_item(cat, title, c_type, text_content, path_content)
            self.refresh_categories()
            self.refresh_list()
            win.destroy()

        ttk.Button(win, text="保存", command=save).pack(pady=20)

    def use_item(self, item):
        item_id, cat, title, c_type, c_text, c_path, _ = item
        
        self.preview_label.config(text=f"正在处理: {title}")

        if c_type == 'text':
            pyperclip.copy(c_text)
            messagebox.showinfo("成功", "文字已复制到剪贴板！")
        elif c_type == 'image' or c_type == 'file':
            if os.path.exists(c_path):
                os.startfile(c_path) # Windows打开文件
                # 如果是Mac，使用: import subprocess; subprocess.call(["open", c_path])
            else:
                messagebox.showerror("错误", "文件路径不存在")

    def delete_item(self, item_id):
        if messagebox.askyesno("确认", "确定要删除这条吗？"):
            self.db.delete_item(item_id)
            self.refresh_list()

# --- 运行程序 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = QuickReplyApp(root)
    root.mainloop()