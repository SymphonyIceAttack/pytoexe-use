import os
import shutil
import sqlite3
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import pyperclip
import subprocess
import sys

# 数据目录
DATA_DIR = "quick_reply_data"
FILES_DIR = os.path.join(DATA_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "replies.db")

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    title TEXT NOT NULL,
                    content_type TEXT NOT NULL,  -- text, image, file
                    content TEXT NOT NULL,       -- 文本内容 或 文件相对路径
                    FOREIGN KEY(category_id) REFERENCES categories(id)
                )''')
    # 插入默认分类
    c.execute("INSERT OR IGNORE INTO categories (name) VALUES ('默认')")
    conn.commit()
    conn.close()

init_db()

class ReplyManager:
    def __init__(self, root):
        self.root = root
        self.root.title("快捷回复工具")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        self.current_category = tk.StringVar(value="默认")
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_replies)
        
        self.create_widgets()
        self.load_categories()
        self.load_replies()
        
    def create_widgets(self):
        # 左侧分类树
        left_frame = ttk.Frame(self.root, width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Label(left_frame, text="分类", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        self.category_tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        self.category_tree.pack(fill=tk.BOTH, expand=True)
        self.category_tree.bind("<<TreeviewSelect>>", self.on_category_select)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="新建分类", command=self.add_category).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除分类", command=self.del_category).pack(side=tk.LEFT, padx=2)
        
        # 右侧主区域
        right_frame = ttk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 搜索框
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill=tk.X, pady=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 回复列表（可自定义显示）
        self.reply_listbox = tk.Listbox(right_frame, height=20, font=("微软雅黑", 10))
        self.reply_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.reply_listbox.bind("<Double-Button-1>", self.on_reply_click)
        
        # 操作按钮
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X, pady=5)
        ttk.Button(action_frame, text="添加回复", command=self.add_reply).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="编辑回复", command=self.edit_reply).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="删除回复", command=self.del_reply).pack(side=tk.LEFT, padx=2)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_categories(self):
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name FROM categories ORDER BY name")
        for cid, name in c.fetchall():
            self.category_tree.insert("", tk.END, iid=cid, text=name)
        conn.close()
        # 选中当前分类
        for cid in self.category_tree.get_children():
            if self.category_tree.item(cid, "text") == self.current_category.get():
                self.category_tree.selection_set(cid)
                break
    
    def on_category_select(self, event):
        selected = self.category_tree.selection()
        if selected:
            cid = selected[0]
            name = self.category_tree.item(cid, "text")
            self.current_category.set(name)
            self.load_replies()
    
    def load_replies(self):
        self.reply_listbox.delete(0, tk.END)
        keyword = self.search_var.get().strip()
        category_name = self.current_category.get()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM categories WHERE name=?", (category_name,))
        cat_row = c.fetchone()
        if not cat_row:
            conn.close()
            return
        cat_id = cat_row[0]
        if keyword:
            c.execute("SELECT id, title, content_type, content FROM replies WHERE category_id=? AND title LIKE ? ORDER BY title",
                      (cat_id, f"%{keyword}%"))
        else:
            c.execute("SELECT id, title, content_type, content FROM replies WHERE category_id=? ORDER BY title", (cat_id,))
        self.reply_items = []  # 存储(id, type, content)
        for rid, title, ctype, content in c.fetchall():
            display = f"[{ctype.upper()}] {title}"
            self.reply_listbox.insert(tk.END, display)
            self.reply_items.append((rid, ctype, content))
        conn.close()
    
    def filter_replies(self, *args):
        self.load_replies()
    
    def add_category(self):
        name = simpledialog.askstring("新建分类", "请输入分类名称:")
        if name:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
                self.load_categories()
            except sqlite3.IntegrityError:
                messagebox.showerror("错误", "分类已存在")
            conn.close()
    
    def del_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个分类")
            return
        cid = selected[0]
        name = self.category_tree.item(cid, "text")
        if name == "默认":
            messagebox.showwarning("警告", "不能删除默认分类")
            return
        if messagebox.askyesno("确认", f"删除分类 '{name}' 及其下所有回复？"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # 删除该分类下所有回复的文件
            c.execute("SELECT content_type, content FROM replies WHERE category_id=?", (cid,))
            for ctype, content in c.fetchall():
                if ctype in ('image', 'file'):
                    full_path = os.path.join(FILES_DIR, content)
                    if os.path.exists(full_path):
                        os.remove(full_path)
            c.execute("DELETE FROM replies WHERE category_id=?", (cid,))
            c.execute("DELETE FROM categories WHERE id=?", (cid,))
            conn.commit()
            conn.close()
            self.load_categories()
            self.current_category.set("默认")
            self.load_replies()
    
    def add_reply(self):
        self._edit_reply_dialog(is_add=True)
    
    def edit_reply(self):
        selection = self.reply_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个回复")
            return
        idx = selection[0]
        rid, ctype, content = self.reply_items[idx]
        self._edit_reply_dialog(is_add=False, rid=rid, current_type=ctype, current_content=content)
    
    def _edit_reply_dialog(self, is_add, rid=None, current_type="text", current_content=""):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加回复" if is_add else "编辑回复")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 标题
        ttk.Label(dialog, text="标题:").pack(anchor=tk.W, padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=50)
        title_entry.pack(fill=tk.X, padx=10)
        if not is_add:
            # 获取原标题
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT title FROM replies WHERE id=?", (rid,))
            title_entry.insert(0, c.fetchone()[0])
            conn.close()
        
        # 类型选择
        ttk.Label(dialog, text="类型:").pack(anchor=tk.W, padx=10, pady=5)
        type_var = tk.StringVar(value=current_type)
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=10)
        ttk.Radiobutton(type_frame, text="文本", variable=type_var, value="text").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="图片", variable=type_var, value="image").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="文件", variable=type_var, value="file").pack(side=tk.LEFT, padx=5)
        
        # 内容编辑区
        ttk.Label(dialog, text="内容:").pack(anchor=tk.W, padx=10, pady=5)
        text_frame = ttk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        content_text = tk.Text(text_frame, height=10, wrap=tk.WORD)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(text_frame, command=content_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        content_text.config(yscrollcommand=scroll.set)
        
        if not is_add and current_type in ('text',):
            content_text.insert(tk.END, current_content)
        elif not is_add and current_type in ('image', 'file'):
            content_text.insert(tk.END, current_content)  # 显示文件名
        
        # 文件/图片选择按钮
        def choose_file():
            filetypes = []
            if type_var.get() == 'image':
                filetypes = [("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
            else:
                filetypes = [("所有文件", "*.*")]
            filename = filedialog.askopenfilename(title="选择文件", filetypes=filetypes)
            if filename:
                # 显示相对路径或仅文件名
                content_text.delete(1.0, tk.END)
                content_text.insert(tk.END, filename)
        
        choose_btn = ttk.Button(dialog, text="浏览文件", command=choose_file)
        choose_btn.pack(pady=5)
        
        def save():
            title = title_entry.get().strip()
            if not title:
                messagebox.showerror("错误", "标题不能为空")
                return
            reply_type = type_var.get()
            content = content_text.get(1.0, tk.END).strip()
            if not content:
                messagebox.showerror("错误", "内容不能为空")
                return
            
            # 处理文件/图片：将文件复制到数据目录
            saved_path = content
            if reply_type in ('image', 'file'):
                if not os.path.exists(content):
                    messagebox.showerror("错误", "文件不存在，请重新选择")
                    return
                # 复制到数据目录
                base_name = os.path.basename(content)
                dest = os.path.join(FILES_DIR, base_name)
                # 如果目标存在，加数字后缀
                counter = 1
                name, ext = os.path.splitext(base_name)
                while os.path.exists(dest):
                    dest = os.path.join(FILES_DIR, f"{name}_{counter}{ext}")
                    counter += 1
                shutil.copy2(content, dest)
                saved_path = os.path.basename(dest)
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            cat_name = self.current_category.get()
            c.execute("SELECT id FROM categories WHERE name=?", (cat_name,))
            cat_id = c.fetchone()[0]
            
            if is_add:
                c.execute("INSERT INTO replies (category_id, title, content_type, content) VALUES (?,?,?,?)",
                          (cat_id, title, reply_type, saved_path))
            else:
                # 编辑时，如果内容类型改变且旧文件存在，则删除旧文件
                old_ctype, old_content = None, None
                c.execute("SELECT content_type, content FROM replies WHERE id=?", (rid,))
                old_ctype, old_content = c.fetchone()
                if old_ctype in ('image','file') and old_content != saved_path:
                    old_path = os.path.join(FILES_DIR, old_content)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                c.execute("UPDATE replies SET title=?, content_type=?, content=? WHERE id=?",
                          (title, reply_type, saved_path, rid))
            conn.commit()
            conn.close()
            dialog.destroy()
            self.load_replies()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def del_reply(self):
        selection = self.reply_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个回复")
            return
        idx = selection[0]
        rid, ctype, content = self.reply_items[idx]
        if messagebox.askyesno("确认", "删除此回复？"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            if ctype in ('image', 'file'):
                file_path = os.path.join(FILES_DIR, content)
                if os.path.exists(file_path):
                    os.remove(file_path)
            c.execute("DELETE FROM replies WHERE id=?", (rid,))
            conn.commit()
            conn.close()
            self.load_replies()
    
    def on_reply_click(self, event):
        selection = self.reply_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        rid, ctype, content = self.reply_items[idx]
        
        if ctype == "text":
            pyperclip.copy(content)
            self.status_var.set(f"已复制文本: {content[:50]}...")
            messagebox.showinfo("成功", "文本已复制到剪贴板")
        elif ctype == "image":
            # 打开图片预览，并尝试复制图片文件到剪贴板（需要额外处理）
            img_path = os.path.join(FILES_DIR, content)
            if os.path.exists(img_path):
                # 打开默认图片查看器
                if sys.platform == "win32":
                    os.startfile(img_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", img_path])
                else:
                    subprocess.run(["xdg-open", img_path])
                # 复制图片文件路径到剪贴板
                pyperclip.copy(img_path)
                self.status_var.set(f"已复制图片路径: {img_path}")
                messagebox.showinfo("提示", "已打开图片，图片路径已复制到剪贴板")
            else:
                messagebox.showerror("错误", "图片文件不存在")
        elif ctype == "file":
            file_path = os.path.join(FILES_DIR, content)
            if os.path.exists(file_path):
                # 打开文件
                if sys.platform == "win32":
                    os.startfile(file_path)
                elif sys.platform == "darwin":
                    subprocess.run(["open", file_path])
                else:
                    subprocess.run(["xdg-open", file_path])
                pyperclip.copy(file_path)
                self.status_var.set(f"已复制文件路径: {file_path}")
                messagebox.showinfo("提示", "已打开文件，文件路径已复制到剪贴板")
            else:
                messagebox.showerror("错误", "文件不存在")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReplyManager(root)
    root.mainloop()