import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import psycopg2
from psycopg2 import extras
import threading  # 新增：用于异步查询，防止界面卡死
import warnings

warnings.filterwarnings("ignore", category=UserWarning)


class MesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("注塑计划查询系统")  # 修复了可能的乱码
        self.root.geometry("1100x700")

        self.df = None
        self.setup_ui()
        self.style_ui()

    def style_ui(self):
        """设置界面样式，让表格看起来更现代"""
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('微软雅黑', 10, 'bold'))
        style.configure("Treeview", rowheight=25)

    def setup_ui(self):
        # --- 顶部控制面板 ---
        top_frame = tk.Frame(self.root, pady=15, padx=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(top_frame, text="工单过滤 (逗号分隔):", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=5)

        self.filter_entry = tk.Entry(top_frame, width=30, font=('Consolas', 11))
        self.filter_entry.insert(0, "02, 21, 06")
        self.filter_entry.pack(side=tk.LEFT, padx=5)

        self.query_btn = tk.Button(top_frame, text="🔍 查询数据", command=self.start_query_thread,
                                   bg="#0078D7", fg="white", width=12, font=('微软雅黑', 9, 'bold'))
        self.query_btn.pack(side=tk.LEFT, padx=10)

        self.export_btn = tk.Button(top_frame, text="Excel 导出", command=self.export_excel,
                                    state=tk.DISABLED, bg="#28a745", fg="white", width=12, font=('微软雅黑', 9))
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- 数据显示区域 ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        # 中文列名映射
        self.col_map = {
            "item_order": "订单序号", "item_item": "物料项", "wo_no": "工单号",
            "item_no": "产品编号", "item_name": "产品名称", "color": "颜色",
            "material_quality": "材质", "remark": "备注"
        }

        self.tree = ttk.Treeview(table_frame, columns=list(self.col_map.keys()), show='headings')

        for col, text in self.col_map.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=120, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

    def get_db_connection(self):
        """数据库连接配置"""
        return psycopg2.connect(
            host="192.168.0.112",
            database="django_vue_admin",
            user="django_superadmin",
            password="django_superpassword",
            port="5432",
            connect_timeout=5  # 增加超时限制
        )

    def start_query_thread(self):
        """开启新线程查询，防止查询大负载时界面卡死"""
        thread = threading.Thread(target=self.fetch_data, daemon=True)
        thread.start()

    def fetch_data(self):
        self.query_btn.config(state=tk.DISABLED)
        self.status_var.set("正在查询数据库，请稍候...")

        # 清空现有表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # 数据清洗：处理空格并过滤空字符串
            raw_input = self.filter_entry.get().replace('，', ',')  # 兼容中文逗号
            codes = [c.strip() for c in raw_input.split(',') if c.strip()]

            if not codes:
                messagebox.showwarning("输入错误", "请输入有效的过滤代码")
                return

            conn = self.get_db_connection()
            query = """
                SELECT item_order, item_item, wo_no, item_no, 
                       item_name, color, material_quality, remark 
                FROM mes_plan_pool_manage
                WHERE is_delete = false 
                  AND is_show = true
                  AND substr(wo_no, 3, 2) IN %s;
            """

            # 封装执行
            with conn:
                self.df = pd.read_sql_query(query, conn, params=(tuple(codes),))
            conn.close()

            # 回到主线程更新 UI
            self.root.after(0, self.update_table)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("数据库错误", f"连接或查询失败: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.query_btn.config(state=tk.NORMAL))

    def update_table(self):
        """在主线程中渲染数据"""
        if self.df is not None and not self.df.empty:
            for _, row in self.df.iterrows():
                # 填充 NaN 值为空字符串，防止显示 'nan'
                display_values = ["" if pd.isna(v) else v for v in row]
                self.tree.insert("", tk.END, values=display_values)

            self.export_btn.config(state=tk.NORMAL)
            self.status_var.set(f"查询成功：找到 {len(self.df)} 条记录")
        else:
            self.status_var.set("未找到匹配数据")
            self.export_btn.config(state=tk.DISABLED)

    def export_excel(self):
        if self.df is None or self.df.empty:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="注塑计划导出数据.xlsx"
        )

        if file_path:
            try:
                # 导出时将列名替换为中文
                export_df = self.df.rename(columns=self.col_map)
                export_df.to_excel(file_path, index=False, engine='openpyxl')
                messagebox.showinfo("成功", "文件已成功导出！")
            except Exception as e:
                messagebox.showerror("导出失败", f"无法保存文件: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MesApp(root)
    root.mainloop()