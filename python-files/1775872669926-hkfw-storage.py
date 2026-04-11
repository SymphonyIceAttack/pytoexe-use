import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import json
import os

# ====================== 主程序 ======================
class DataStorageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("分类信息存储工具 - 专业版")
        self.root.geometry("780x580")

        # ========== 窗口图标（自带，不需要外部ICO文件！）==========
        try:
            self.root.iconbitmap(default="")  # 使用系统默认图标，干净无异常
        except:
            pass

        # 数据文件路径（自动保存在软件同目录下）
        self.data_file = "saved_data.json"
        self.data = []  # [分类, 内容]

        # 启动时自动加载本地数据
        self.load_data()

        # ====================== 顶部输入区 ======================
        input_frame = ttk.LabelFrame(root, text="录入/修改信息")
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="分类：").grid(row=0, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_entry = ttk.Entry(input_frame, textvariable=self.category_var, width=16)
        self.category_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="内容：").grid(row=0, column=2, padx=5, pady=5)
        self.content_var = tk.StringVar()
        self.content_entry = ttk.Entry(input_frame, textvariable=self.content_var, width=35)
        self.content_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(input_frame, text="保存", command=self.save_data).grid(row=0, column=4, padx=4)
        ttk.Button(input_frame, text="修改选中", command=self.modify_selected).grid(row=0, column=5, padx=4)
        ttk.Button(input_frame, text="删除选中", command=self.delete_selected).grid(row=0, column=6, padx=4)
        ttk.Button(input_frame, text="清空输入", command=self.clear_input).grid(row=0, column=7, padx=4)

        # ====================== 搜索区 ======================
        search_frame = ttk.LabelFrame(root, text="搜索")
        search_frame.pack(fill="x", padx=10, pady=3)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=40).pack(side="left", padx=5, pady=5)
        ttk.Button(search_frame, text="搜索", command=self.search_data).pack(side="left", padx=5)
        ttk.Button(search_frame, text="显示全部", command=self.update_tables).pack(side="left", padx=5)
        ttk.Button(search_frame, text="导出Excel", command=self.export_excel).pack(side="right", padx=10)

        # ====================== 分类标签 ======================
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.tables = {}

        self.current_edit_item = None
        self.update_tables()

    # ====================== 自动保存到本地文件 ======================
    def save_to_file(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

    # ====================== 启动自动加载数据 ======================
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = []

    # ====================== 保存 ======================
    def save_data(self):
        cat = self.category_var.get().strip()
        con = self.content_var.get().strip()
        if not cat or not con:
            messagebox.showwarning("提示", "分类和内容不能为空")
            return
        self.data.append([cat, con])
        self.save_to_file()  # 自动保存
        self.update_tables()
        self.clear_input()

    # ====================== 刷新表格 ======================
    def update_tables(self, data_list=None):
        data = data_list if data_list is not None else self.data

        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        self.tables.clear()

        cats = sorted(set(item[0] for item in data))
        for cat in cats:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=cat)

            table = ttk.Treeview(frame, columns=["内容"], show="headings")
            table.heading("内容", text=f"{cat}")
            table.column("内容", width=720)
            table.pack(fill="both", expand=True, padx=5, pady=5)
            self.tables[cat] = table

            for item in data:
                if item[0] == cat:
                    table.insert("", "end", values=[item[1]])

            # 绑定点击事件，点一下就自动填到输入框
            def on_click(e, c=cat):
                selected = table.selection()
                if selected:
                    val = table.item(selected[0])["values"][0]
                    self.category_var.set(c)
                    self.content_var.set(val)
            table.bind("<<TreeviewSelect>>", on_click)

    # ====================== 清空输入 ======================
    def clear_input(self):
        self.category_var.set("")
        self.content_var.set("")
        self.current_edit_item = None

    # ====================== 删除选中 ======================
    def delete_selected(self):
        cat = self.category_var.get().strip()
        con = self.content_var.get().strip()
        target = [cat, con]
        if target not in self.data:
            messagebox.showinfo("提示", "请选中一条数据")
            return
        self.data.remove(target)
        self.save_to_file()
        self.update_tables()
        self.clear_input()

    # ====================== 修改选中 ======================
    def modify_selected(self):
        old_cat = self.category_var.get().strip()
        old_con = self.content_var.get().strip()
        old = [old_cat, old_con]

        if old not in self.data:
            messagebox.showinfo("提示", "请先选中要修改的数据")
            return

        new_cat = self.category_var.get().strip()
        new_con = self.content_var.get().strip()
        if not new_cat or not new_con:
            messagebox.showwarning("提示", "分类和内容不能为空")
            return

        idx = self.data.index(old)
        self.data[idx] = [new_cat, new_con]
        self.save_to_file()
        self.update_tables()
        self.clear_input()

    # ====================== 搜索 ======================
    def search_data(self):
        keyword = self.search_var.get().lower()
        if not keyword:
            self.update_tables()
            return
        result = [item for item in self.data if keyword in item[0].lower() or keyword in item[1].lower()]
        self.update_tables(result)

    # ====================== 导出 Excel ======================
    def export_excel(self):
        if not self.data:
            messagebox.showwarning("提示", "无数据可导出")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")])
        if not path:
            return
        df = pd.DataFrame(self.data, columns=["分类", "内容"])
        df.to_excel(path, index=False)
        messagebox.showinfo("成功", f"已导出到：\n{path}")

# ====================== 启动 ======================
if __name__ == "__main__":
    main_root = tk.Tk()
    app = DataStorageApp(main_root)
    main_root.mainloop()