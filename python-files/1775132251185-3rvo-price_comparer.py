import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

class PriceComparerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("供应商最低价比对工具")
        self.root.geometry("700x500")

        # 主表格文件路径
        self.main_file_path = tk.StringVar()
        # 供应商列表：每个元素为 {"file": 路径, "name": 供应商名}
        self.suppliers = []

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        # 主表格区域
        main_frame = tk.LabelFrame(self.root, text="1. 选择你的进货表格", padx=10, pady=10)
        main_frame.pack(fill="x", padx=10, pady=5)

        tk.Entry(main_frame, textvariable=self.main_file_path, width=60).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(main_frame, text="浏览", command=self.select_main_file).grid(row=0, column=1, padx=5)

        # 供应商区域
        supplier_frame = tk.LabelFrame(self.root, text="2. 添加供应商表格（每个供应商需指定名称）", padx=10, pady=10)
        supplier_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 供应商列表显示区域
        self.supplier_listbox = tk.Listbox(supplier_frame, height=6)
        self.supplier_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = tk.Frame(supplier_frame)
        btn_frame.pack(fill="x", pady=5)
        tk.Button(btn_frame, text="添加供应商", command=self.add_supplier).pack(side="left", padx=5)
        tk.Button(btn_frame, text="删除选中供应商", command=self.remove_supplier).pack(side="left", padx=5)

        # 说明信息
        info_text = """
        【表格要求】
        1. 你的进货表格必须包含列：条码、名称、价格、数量（列名需完全一致）。
        2. 供应商表格必须包含列：条码、价格。
           可选列：数量（若存在，则数量>0才视为有现货；若无数量列，则默认有现货）。
        3. 支持 .xlsx 或 .xls 格式。
        """
        info_label = tk.Label(self.root, text=info_text, justify="left", fg="gray", font=("微软雅黑", 9))
        info_label.pack(fill="x", padx=10, pady=5)

        # 执行按钮
        self.run_btn = tk.Button(self.root, text="开始比对并生成新表格", command=self.run_comparison, bg="#4CAF50", fg="white", font=("微软雅黑", 11))
        self.run_btn.pack(pady=15)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")

    def select_main_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx *.xls")])
        if file_path:
            self.main_file_path.set(file_path)

    def add_supplier(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx *.xls")])
        if not file_path:
            return
        # 弹窗输入供应商名称
        dialog = tk.Toplevel(self.root)
        dialog.title("供应商名称")
        dialog.geometry("300x120")
        tk.Label(dialog, text="请输入此供应商的名称（例如：供应商A）：").pack(pady=10)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        def confirm():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("警告", "供应商名称不能为空！")
                return
            self.suppliers.append({"file": file_path, "name": name})
            self.refresh_supplier_list()
            dialog.destroy()
        tk.Button(dialog, text="确定", command=confirm).pack(pady=5)

    def remove_supplier(self):
        selection = self.supplier_listbox.curselection()
        if selection:
            index = selection[0]
            del self.suppliers[index]
            self.refresh_supplier_list()

    def refresh_supplier_list(self):
        self.supplier_listbox.delete(0, tk.END)
        for sup in self.suppliers:
            self.supplier_listbox.insert(tk.END, f"{sup['name']} —— {os.path.basename(sup['file'])}")

    def run_comparison(self):
        # 校验主表格
        main_path = self.main_file_path.get()
        if not main_path or not os.path.exists(main_path):
            messagebox.showerror("错误", "请先选择你的进货表格！")
            return
        if len(self.suppliers) == 0:
            messagebox.showerror("错误", "请至少添加一个供应商表格！")
            return

        self.status_var.set("正在处理，请稍候...")
        self.root.update()

        try:
            # 读取主表格
            df_main = pd.read_excel(main_path)
            required_cols = {"条码", "名称", "价格", "数量"}
            if not required_cols.issubset(df_main.columns):
                missing = required_cols - set(df_main.columns)
                raise ValueError(f"你的进货表格缺少必需列：{missing}。请确保列名包含：条码、名称、价格、数量")

            # 合并所有供应商有效现货（价格、供应商名称）
            all_supply = pd.DataFrame()
            for sup in self.suppliers:
                df_sup = pd.read_excel(sup["file"])
                # 检查供应商表格基本列
                if "条码" not in df_sup.columns or "价格" not in df_sup.columns:
                    raise ValueError(f"供应商表格 {sup['name']} 缺少 '条码' 或 '价格' 列")
                # 处理现货逻辑
                if "数量" in df_sup.columns:
                    # 有数量列，只保留数量 > 0 的
                    df_sup_valid = df_sup[df_sup["数量"] > 0].copy()
                else:
                    # 没有数量列，默认全部有现货
                    df_sup_valid = df_sup.copy()
                if df_sup_valid.empty:
                    continue  # 该供应商无现货
                # 确保价格是数值类型
                df_sup_valid["价格"] = pd.to_numeric(df_sup_valid["价格"], errors="coerce")
                df_sup_valid = df_sup_valid.dropna(subset=["价格"])
                # 添加供应商名称列
                df_sup_valid["供应商名称"] = sup["name"]
                # 可能同一供应商同一条码有多条记录（比如不同价格），取最低价格
                df_sup_valid = df_sup_valid.groupby(["条码"], as_index=False).agg({"价格": "min", "供应商名称": "first"})
                all_supply = pd.concat([all_supply, df_sup_valid[["条码", "价格", "供应商名称"]]], ignore_index=True)

            if all_supply.empty:
                # 没有任何供应商有现货
                df_main["最低价格供应商"] = "无现货"
            else:
                # 对每个条码，找出最低价格的供应商
                # 先按条码分组，取最低价格行，可能有多条同价，这里取第一个（可自行调整）
                idx_min = all_supply.groupby("条码")["价格"].idxmin()
                best_supply = all_supply.loc[idx_min, ["条码", "供应商名称"]]
                # 合并到主表格
                df_main = df_main.merge(best_supply, on="条码", how="left")
                df_main["最低价格供应商"] = df_main["供应商名称"].fillna("无现货")
                df_main.drop(columns=["供应商名称"], inplace=True)

            # 保存新表格
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")])
            if not save_path:
                self.status_var.set("已取消保存")
                return
            df_main.to_excel(save_path, index=False)
            self.status_var.set(f"处理完成！新表格已保存至：{save_path}")
            messagebox.showinfo("完成", f"比对完成！\n共处理 {len(df_main)} 行商品，其中“无现货”商品 {len(df_main[df_main['最低价格供应商'] == '无现货'])} 个。")
        except Exception as e:
            self.status_var.set("处理出错")
            messagebox.showerror("错误", f"运行失败：\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PriceComparerApp(root)
    root.mainloop()