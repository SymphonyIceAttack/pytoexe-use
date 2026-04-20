# 拼多多商家利润核算系统 全功能代码
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

# 配置项：可根据自己的订单表字段修改，必须和Excel列名完全一致
CONFIG = {
    "order_fields": {
        "order_id": "订单编号",
        "goods_id": "商品ID",
        "goods_name": "商品名称",
        "quantity": "数量",
        "actual_pay": "买家实付金额",
        "service_fee": "平台技术服务费",
        "commission": "多多进宝佣金",
        "coupon_fee": "商家承担优惠券金额",
        "refund_fee": "退款金额",
        "order_date": "下单时间",
        "order_status": "订单状态"
    },
    "goods_cost": {}
}

class ProfitCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("拼多多商家利润核算系统")
        self.root.geometry("1200x700")
        self.order_df = None
        self.cost_df = None
        self.profit_df = None
        self._build_ui()

    def _build_ui(self):
        # 顶部功能按钮区
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        tk.Button(top_frame, text="导入商品成本表", command=self.import_cost_table, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="导入拼多多订单表", command=self.import_order_table, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="一键计算利润", command=self.calculate_profit, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="导出利润报表", command=self.export_profit, width=20).pack(side=tk.LEFT, padx=5)

        # 日期筛选区
        filter_frame = tk.Frame(self.root, padx=10, pady=5)
        filter_frame.pack(fill=tk.X)
        tk.Label(filter_frame, text="日期筛选：").pack(side=tk.LEFT)
        self.start_date = tk.Entry(filter_frame, width=12)
        self.start_date.pack(side=tk.LEFT, padx=5)
        self.start_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        tk.Label(filter_frame, text="至").pack(side=tk.LEFT)
        self.end_date = tk.Entry(filter_frame, width=12)
        self.end_date.pack(side=tk.LEFT, padx=5)
        self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        tk.Button(filter_frame, text="筛选查看", command=self.filter_daily_profit, width=15).pack(side=tk.LEFT, padx=10)

        # 核心数据指标区
        stat_frame = tk.Frame(self.root, padx=10, pady=10)
        stat_frame.pack(fill=tk.X)
        self.stat_labels = {}
        stat_items = [("当日净利润", "daily_profit"), ("当日订单量", "daily_order_count"), ("当日销售额", "daily_sales"), ("累计总利润", "total_profit")]
        for name, key in stat_items:
            frame = tk.Frame(stat_frame, relief=tk.GROOVE, borderwidth=2, padx=20, pady=10)
            frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            tk.Label(frame, text=name, font=("微软雅黑", 12)).pack()
            self.stat_labels[key] = tk.Label(frame, text="0", font=("微软雅黑", 16, "bold"), fg="red")
            self.stat_labels[key].pack()

        # 利润明细表格区
        table_frame = tk.Frame(self.root, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scroll_y = tk.Scrollbar(table_frame, orient=tk.VERTICAL)
        self.profit_table = ttk.Treeview(
            table_frame, xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set,
            columns=("order_id", "goods_name", "quantity", "actual_pay", "total_cost", "total_fee", "profit", "order_date", "status"),
            show="headings"
        )
        # 表格表头配置
        table_headers = {
            "order_id": "订单编号", "goods_name": "商品名称", "quantity": "数量", "actual_pay": "实付金额",
            "total_cost": "订单总成本", "total_fee": "总扣费", "profit": "订单净利润", "order_date": "下单日期", "status": "订单状态"
        }
        for col, name in table_headers.items():
            self.profit_table.heading(col, text=name)
            self.profit_table.column(col, width=120, anchor=tk.CENTER)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.config(command=self.profit_table.xview)
        scroll_y.config(command=self.profit_table.yview)
        self.profit_table.pack(fill=tk.BOTH, expand=True)

    # 导入商品成本表
    def import_cost_table(self):
        file_path = filedialog.askopenfilename(title="选择商品成本表", filetypes=[("Excel文件", "*.xlsx;*.xls"), ("CSV文件", "*.csv")])
        if not file_path: return
        try:
            self.cost_df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
            for _, row in self.cost_df.iterrows():
                CONFIG["goods_cost"][str(row["商品ID"])] = {"cost": float(row["单件成本"]), "freight": float(row["单笔运费"])}
            messagebox.showinfo("成功", f"商品成本表导入成功，共导入{len(self.cost_df)}个商品")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    # 导入拼多多订单表
    def import_order_table(self):
        file_path = filedialog.askopenfilename(title="选择拼多多订单表", filetypes=[("Excel文件", "*.xlsx;*.xls"), ("CSV文件", "*.csv")])
        if not file_path: return
        try:
            self.order_df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
            date_col = CONFIG["order_fields"]["order_date"]
            self.order_df[date_col] = pd.to_datetime(self.order_df[date_col]).dt.strftime("%Y-%m-%d")
            messagebox.showinfo("成功", f"订单表导入成功，共导入{len(self.order_df)}条订单")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    # 核心利润计算
    def calculate_profit(self):
        if self.order_df is None:
            messagebox.showwarning("警告", "请先导入订单表")
            return
        if not CONFIG["goods_cost"]:
            messagebox.showwarning("警告", "请先导入商品成本表")
            return
        try:
            df = self.order_df.copy()
            fields = CONFIG["order_fields"]
            # 逐行计算利润
            def calc_row(row):
                goods_id = str(row[fields["goods_id"]])
                cost_info = CONFIG["goods_cost"].get(goods_id, {"cost": 0, "freight": 0})
                quantity = int(row[fields["quantity"]])
                total_cost = cost_info["cost"] * quantity + cost_info["freight"]
                total_fee = sum([
                    float(row[fields[key]]) if pd.notna(row[fields[key]]) else 0
                    for key in ["service_fee", "commission", "coupon_fee", "refund_fee"]
                ])
                actual_pay = float(row[fields["actual_pay"]]) if pd.notna(row[fields["actual_pay"]]) else 0
                profit = actual_pay - total_cost - total_fee
                return pd.Series([total_cost, total_fee, profit])
            df[["订单总成本", "总扣费", "订单净利润"]] = df.apply(calc_row, axis=1)
            self.profit_df = df
            self._refresh_table(df)
            self._refresh_stats(df)
            messagebox.showinfo("成功", "利润计算完成")
        except Exception as e:
            messagebox.showerror("错误", f"计算失败：{str(e)}")

    # 刷新表格数据
    def _refresh_table(self, df):
        for item in self.profit_table.get_children():
            self.profit_table.delete(item)
        fields = CONFIG["order_fields"]
        for _, row in df.iterrows():
            self.profit_table.insert("", tk.END, values=(
                row[fields["order_id"]], row[fields["goods_name"]], row[fields["quantity"]],
                round(row[fields["actual_pay"]], 2), round(row["订单总成本"], 2), round(row["总扣费"], 2),
                round(row["订单净利润"], 2), row[fields["order_date"]], row[fields["order_status"]]
            ))

    # 刷新统计指标
    def _refresh_stats(self, df):
        total_profit = round(df["订单净利润"].sum(), 2)
        self.stat_labels["total_profit"].config(text=f"¥ {total_profit}")
        # 当日数据统计
        today = datetime.now().strftime("%Y-%m-%d")
        today_df = df[df[CONFIG["order_fields"]["order_date"]] == today]
        self.stat_labels["daily_profit"].config(text=f"¥ {round(today_df['订单净利润'].sum(), 2)}")
        self.stat_labels["daily_order_count"].config(text=str(len(today_df)))
        self.stat_labels["daily_sales"].config(text=f"¥ {round(today_df[CONFIG['order_fields']['actual_pay']].sum(), 2)}")

    # 日期筛选
    def filter_daily_profit(self):
        if self.profit_df is None:
            messagebox.showwarning("警告", "请先计算利润")
            return
        try:
            start_date = self.start_date.get().strip()
            end_date = self.end_date.get().strip()
            date_col = CONFIG["order_fields"]["order_date"]
            filter_df = self.profit_df[(self.profit_df[date_col] >= start_date) & (self.profit_df[date_col] <= end_date)]
            self._refresh_table(filter_df)
            self._refresh_stats(filter_df)
        except Exception as e:
            messagebox.showerror("错误", f"筛选失败：{str(e)}")

    # 导出利润报表
    def export_profit(self):
        if self.profit_df is None:
            messagebox.showwarning("警告", "请先计算利润")
            return
        file_path = filedialog.asksaveasfilename(title="保存利润报表", defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")])
        if not file_path: return
        try:
            self.profit_df.to_excel(file_path, index=False)
            messagebox.showinfo("成功", f"报表导出成功，保存路径：{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfitCalculator(root)
    root.mainloop()