import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, filedialog
import csv

DB_NAME = "library.db"

def init_db():
    """初始化数据库和表"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            isbn TEXT UNIQUE,
            publisher TEXT,
            publish_year INTEGER,
            category TEXT,
            location TEXT,
            status TEXT DEFAULT '可借阅'
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_title ON books(title)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_author ON books(author)")
    conn.commit()
    conn.close()

class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图书管理系统")
        self.root.geometry("1000x600")
        self.root.resizable(True, True)

        self.current_query = None
        self.current_params = None

        # 菜单栏
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="操作", menu=file_menu)
        file_menu.add_command(label="录入新书", command=self.add_book_window)
        file_menu.add_command(label="从CSV导入", command=self.import_from_csv)
        file_menu.add_command(label="刷新列表", command=self.refresh_list)
        file_menu.add_separator()
        file_menu.add_command(label="导出当前列表到CSV", command=self.export_current_to_csv)
        file_menu.add_command(label="导出全部数据到CSV", command=self.export_all_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=root.quit)

        # 工具栏
        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Label(toolbar, text="关键词:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        self.search_by = tk.StringVar(value="title")
        search_options = [("书名", "title"), ("作者", "author"), ("ISBN", "isbn"), ("全文", "fulltext")]
        for text, val in search_options:
            tk.Radiobutton(toolbar, text=text, variable=self.search_by, value=val).pack(side=tk.LEFT, padx=2)

        tk.Button(toolbar, text="搜索", command=self.search_books).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="显示全部", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="录入新书", command=self.add_book_window).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="从CSV导入", command=self.import_from_csv, bg="lightgreen").pack(side=tk.LEFT, padx=5)

        # 表格
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "title", "author", "isbn", "publish_year", "status")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="书名")
        self.tree.heading("author", text="作者")
        self.tree.heading("isbn", text="ISBN")
        self.tree.heading("publish_year", text="出版年份")
        self.tree.heading("status", text="状态")
        self.tree.column("id", width=50)
        self.tree.column("title", width=280)
        self.tree.column("author", width=140)
        self.tree.column("isbn", width=140)
        self.tree.column("publish_year", width=80)
        self.tree.column("status", width=80)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 右键菜单
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="查看/编辑", command=self.edit_book)
        self.context_menu.add_command(label="删除", command=self.delete_book)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.edit_book())

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.refresh_list()

    # ---------- 核心功能 ----------
    def refresh_list(self):
        try:
            self.current_query = "SELECT id, title, author, isbn, publish_year, status FROM books ORDER BY id"
            self.current_params = None
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(self.current_query)
            rows = c.fetchall()
            conn.close()
            self.update_treeview(rows)
            self.status_var.set(f"共 {len(rows)} 条记录")
        except Exception as e:
            messagebox.showerror("错误", f"刷新列表失败：{str(e)}")

    def search_books(self):
        try:
            keyword = self.search_var.get().strip()
            if not keyword:
                self.refresh_list()
                return
            search_type = self.search_by.get()
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            if search_type == "title":
                sql = "SELECT id, title, author, isbn, publish_year, status FROM books WHERE title LIKE ?"
                param = (f"%{keyword}%",)
            elif search_type == "author":
                sql = "SELECT id, title, author, isbn, publish_year, status FROM books WHERE author LIKE ?"
                param = (f"%{keyword}%",)
            elif search_type == "isbn":
                sql = "SELECT id, title, author, isbn, publish_year, status FROM books WHERE isbn = ?"
                param = (keyword,)
            else:
                sql = "SELECT id, title, author, isbn, publish_year, status FROM books WHERE title LIKE ? OR author LIKE ? OR isbn = ?"
                param = (f"%{keyword}%", f"%{keyword}%", keyword)
            c.execute(sql, param)
            rows = c.fetchall()
            conn.close()
            self.update_treeview(rows)
            self.current_query = sql
            self.current_params = param
            self.status_var.set(f"找到 {len(rows)} 条记录")
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败：{str(e)}")

    def update_treeview(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            display_row = list(row)
            if display_row[4] is None:
                display_row[4] = ""
            else:
                display_row[4] = str(display_row[4])
            self.tree.insert("", tk.END, values=display_row)

    # ---------- 录入窗口 ----------
    def add_book_window(self):
        win = Toplevel(self.root)
        win.title("录入新书")
        win.geometry("400x450")
        win.transient(self.root)
        win.grab_set()

        fields = ['书名*', '作者', 'ISBN', '出版社', '出版年份', '分类', '存放位置', '状态']
        entries = {}
        for i, field in enumerate(fields):
            tk.Label(win, text=field).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            entry = tk.Entry(win, width=30)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = entry
        status_combo = ttk.Combobox(win, values=["可借阅", "已借出"], state="readonly")
        status_combo.grid(row=len(fields)-1, column=1, padx=10, pady=5)
        status_combo.current(0)
        entries['状态'] = status_combo

        def save():
            try:
                data = {}
                data['title'] = entries['书名*'].get().strip()
                if not data['title']:
                    messagebox.showerror("错误", "书名不能为空")
                    return
                data['author'] = entries['作者'].get().strip()
                data['isbn'] = entries['ISBN'].get().strip()
                data['publisher'] = entries['出版社'].get().strip()
                year_str = entries['出版年份'].get().strip()
                data['publish_year'] = int(year_str) if year_str.isdigit() else None
                data['category'] = entries['分类'].get().strip()
                data['location'] = entries['存放位置'].get().strip()
                data['status'] = entries['状态'].get()

                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                try:
                    c.execute('''
                        INSERT INTO books (title, author, isbn, publisher, publish_year, category, location, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data['title'], data['author'], data['isbn'], data['publisher'],
                          data['publish_year'], data['category'], data['location'], data['status']))
                    conn.commit()
                    messagebox.showinfo("成功", "图书录入成功")
                    win.destroy()
                    self.refresh_list()
                except sqlite3.IntegrityError:
                    messagebox.showerror("错误", "ISBN已存在，请勿重复录入")
                finally:
                    conn.close()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{str(e)}")

        tk.Button(win, text="保存", command=save, bg="lightblue").grid(row=len(fields), column=0, columnspan=2, pady=20)

    # ---------- CSV 导入 ----------
    def import_from_csv(self):
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        # 尝试自动检测编码
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
        used_encoding = None
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    f.read(1024)
                    used_encoding = enc
                    break
            except:
                continue
        if not used_encoding:
            messagebox.showerror("错误", "无法识别CSV文件编码，请确保文件为UTF-8或GBK格式")
            return

        try:
            with open(file_path, 'r', encoding=used_encoding) as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                if not fieldnames:
                    messagebox.showerror("错误", "CSV文件无列名（第一行应为字段名）")
                    return
                # 字段映射
                mapping = {}
                possible_title = ['书名', '标题', 'book_name', 'title', '名称']
                for p in possible_title:
                    if p in fieldnames:
                        mapping['title'] = p
                        break
                if 'title' not in mapping:
                    messagebox.showerror("错误", "CSV文件必须包含“书名”列")
                    return

                possible_author = ['作者', 'author']
                for p in possible_author:
                    if p in fieldnames:
                        mapping['author'] = p
                        break
                possible_isbn = ['ISBN', 'isbn', '书号']
                for p in possible_isbn:
                    if p in fieldnames:
                        mapping['isbn'] = p
                        break
                possible_publisher = ['出版社', 'publisher']
                for p in possible_publisher:
                    if p in fieldnames:
                        mapping['publisher'] = p
                        break
                possible_year = ['出版年份', '年份', 'publish_year', 'year']
                for p in possible_year:
                    if p in fieldnames:
                        mapping['publish_year'] = p
                        break
                possible_category = ['分类', 'category']
                for p in possible_category:
                    if p in fieldnames:
                        mapping['category'] = p
                        break
                possible_location = ['存放位置', '位置', 'location']
                for p in possible_location:
                    if p in fieldnames:
                        mapping['location'] = p
                        break
                possible_status = ['状态', 'status']
                for p in possible_status:
                    if p in fieldnames:
                        mapping['status'] = p
                        break

                success_count = 0
                skip_count = 0
                error_rows = []
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                for row_num, row in enumerate(reader, start=2):
                    try:
                        title = row.get(mapping.get('title', '')).strip()
                        if not title:
                            error_rows.append((row_num, "书名为空"))
                            continue
                        author = row.get(mapping.get('author', ''), '').strip()
                        isbn = row.get(mapping.get('isbn', ''), '').strip()
                        publisher = row.get(mapping.get('publisher', ''), '').strip()
                        year_str = row.get(mapping.get('publish_year', ''), '').strip()
                        publish_year = int(year_str) if year_str.isdigit() else None
                        category = row.get(mapping.get('category', ''), '').strip()
                        location = row.get(mapping.get('location', ''), '').strip()
                        status = row.get(mapping.get('status', ''), '').strip()
                        if status not in ['可借阅', '已借出']:
                            status = '可借阅'

                        c.execute('''
                            INSERT INTO books (title, author, isbn, publisher, publish_year, category, location, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (title, author, isbn, publisher, publish_year, category, location, status))
                        success_count += 1
                    except sqlite3.IntegrityError:
                        skip_count += 1
                    except Exception as e:
                        error_rows.append((row_num, str(e)))
                conn.commit()
                conn.close()

                msg = f"导入完成！\n成功: {success_count} 条\n跳过(ISBN重复): {skip_count} 条"
                if error_rows:
                    msg += f"\n错误: {len(error_rows)} 条\n详情请查看控制台输出"
                messagebox.showinfo("导入结果", msg)
                self.refresh_list()
        except Exception as e:
            messagebox.showerror("导入失败", f"读取CSV文件出错：{str(e)}")

    # ---------- 编辑与删除 ----------
    def edit_book(self):
        try:
            book_id = self.get_selected_id()
            if not book_id:
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM books WHERE id=?", (book_id,))
            book = c.fetchone()
            conn.close()
            if not book:
                messagebox.showerror("错误", "图书不存在")
                self.refresh_list()
                return

            win = Toplevel(self.root)
            win.title("编辑图书")
            win.geometry("400x450")
            win.transient(self.root)
            win.grab_set()

            fields = ['书名', '作者', 'ISBN', '出版社', '出版年份', '分类', '存放位置', '状态']
            entries = {}
            for i, field in enumerate(fields):
                tk.Label(win, text=field).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
                entry = tk.Entry(win, width=30)
                entry.grid(row=i, column=1, padx=10, pady=5)
                if field == '书名':
                    entry.insert(0, book[1])
                elif field == '作者':
                    entry.insert(0, book[2] if book[2] else "")
                elif field == 'ISBN':
                    entry.insert(0, book[3] if book[3] else "")
                elif field == '出版社':
                    entry.insert(0, book[4] if book[4] else "")
                elif field == '出版年份':
                    entry.insert(0, str(book[5]) if book[5] else "")
                elif field == '分类':
                    entry.insert(0, book[6] if book[6] else "")
                elif field == '存放位置':
                    entry.insert(0, book[7] if book[7] else "")
                entries[field] = entry

            status_combo = ttk.Combobox(win, values=["可借阅", "已借出"], state="readonly")
            status_combo.grid(row=len(fields)-1, column=1, padx=10, pady=5)
            status_combo.set(book[8])
            entries['状态'] = status_combo

            def update():
                try:
                    data = {}
                    data['title'] = entries['书名'].get().strip()
                    if not data['title']:
                        messagebox.showerror("错误", "书名不能为空")
                        return
                    data['author'] = entries['作者'].get().strip()
                    data['isbn'] = entries['ISBN'].get().strip()
                    data['publisher'] = entries['出版社'].get().strip()
                    year_str = entries['出版年份'].get().strip()
                    data['publish_year'] = int(year_str) if year_str.isdigit() else None
                    data['category'] = entries['分类'].get().strip()
                    data['location'] = entries['存放位置'].get().strip()
                    data['status'] = entries['状态'].get()

                    conn = sqlite3.connect(DB_NAME)
                    c = conn.cursor()
                    try:
                        c.execute('''
                            UPDATE books SET title=?, author=?, isbn=?, publisher=?, publish_year=?, category=?, location=?, status=?
                            WHERE id=?
                        ''', (data['title'], data['author'], data['isbn'], data['publisher'],
                              data['publish_year'], data['category'], data['location'], data['status'], book_id))
                        conn.commit()
                        messagebox.showinfo("成功", "更新成功")
                        win.destroy()
                        self.refresh_list()
                    except sqlite3.IntegrityError:
                        messagebox.showerror("错误", "ISBN已存在，无法更新")
                    finally:
                        conn.close()
                except Exception as e:
                    messagebox.showerror("错误", f"更新失败：{str(e)}")

            tk.Button(win, text="保存修改", command=update, bg="lightgreen").grid(row=len(fields), column=0, columnspan=2, pady=20)
        except Exception as e:
            messagebox.showerror("错误", f"编辑失败：{str(e)}")

    def delete_book(self):
        try:
            book_id = self.get_selected_id()
            if not book_id:
                return
            if messagebox.askyesno("确认删除", "确定要删除这本书吗？"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM books WHERE id=?", (book_id,))
                conn.commit()
                conn.close()
                self.refresh_list()
                messagebox.showinfo("成功", "图书已删除")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{str(e)}")

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("未选择", "请先选择一本书")
            return None
        values = self.tree.item(selected[0], "values")
        if values:
            return int(values[0])
        return None

    # ---------- CSV 导出 ----------
    def export_to_csv(self, full_sql, params, filename):
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            if params is None:
                c.execute(full_sql)
            else:
                c.execute(full_sql, params)
            rows = c.fetchall()
            conn.close()
            if not rows:
                messagebox.showwarning("无数据", "没有数据可导出")
                return
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "书名", "作者", "ISBN", "出版社", "出版年份", "分类", "存放位置", "状态"])
                for row in rows:
                    clean_row = [str(cell) if cell is not None else "" for cell in row]
                    writer.writerow(clean_row)
            messagebox.showinfo("导出成功", f"已导出到：{filename}\n共 {len(rows)} 条记录")
        except Exception as e:
            messagebox.showerror("导出失败", f"保存文件时出错：{str(e)}")

    def export_current_to_csv(self):
        if not self.current_query:
            self.export_all_to_csv()
            return
        keyword = self.search_var.get().strip()
        search_type = self.search_by.get()
        if not keyword:
            full_sql = "SELECT id, title, author, isbn, publisher, publish_year, category, location, status FROM books ORDER BY id"
            params = None
        else:
            if search_type == "title":
                full_sql = "SELECT id, title, author, isbn, publisher, publish_year, category, location, status FROM books WHERE title LIKE ? ORDER BY id"
                params = (f"%{keyword}%",)
            elif search_type == "author":
                full_sql = "SELECT id, title, author, isbn, publisher, publish_year, category, location, status FROM books WHERE author LIKE ? ORDER BY id"
                params = (f"%{keyword}%",)
            elif search_type == "isbn":
                full_sql = "SELECT id, title, author, isbn, publisher, publish_year, category, location, status FROM books WHERE isbn = ? ORDER BY id"
                params = (keyword,)
            else:
                full_sql = "SELECT id, title, author, isbn, publisher, publish_year, category, location, status FROM books WHERE title LIKE ? OR author LIKE ? OR isbn = ? ORDER BY id"
                params = (f"%{keyword}%", f"%{keyword}%", keyword)
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if file_path:
            self.export_to_csv(full_sql, params, file_path)

    def export_all_to_csv(self):
        full_sql = "SELECT id, title, author, isbn, publisher, publish_year, category, location, status FROM books ORDER BY id"
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if file_path:
            self.export_to_csv(full_sql, None, file_path)

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
