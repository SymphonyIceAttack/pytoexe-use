#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# -*- coding: utf-8 -*-
"""
外贸单证数据检错工具 - GUI 版（Python 2.7 / 3.x）
依赖：pandas, openpyxl （请先在命令行执行：pip install pandas openpyxl）
如果运行后没有窗口弹出，说明你的 Python 未安装 Tkinter，请看本文件最后的排查方法。
"""
from __future__ import print_function, division, unicode_literals
import sys
import os
import io

# ------------------------------ 1. 先确保 Tkinter 可用 ------------------------------
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
except ImportError:
    try:
        import Tkinter as tk
        import tkFileDialog as filedialog
        import tkMessageBox as messagebox
        import ScrolledText as scrolledtext
    except ImportError:
        # 连 Tkinter 都没有，直接在控制台打印错误并退出
        print("❌ 缺少 Tkinter 图形库，无法启动 GUI。")
        print("   请安装 Python 时勾选 'tcl/tk and IDLE'，或参考以下方法：")
        print("   · Windows：重新安装 Python，务必选中 tcl/tk")
        print("   · macOS：用官方安装包，或 brew install python-tk")
        print("   · Linux：sudo apt-get install python3-tk")
        sys.exit(1)

# ------------------------------ 2. 再检查 pandas ------------------------------
try:
    import pandas as pd
except ImportError:
    # 这时 Tkinter 已经有了，可以弹出图形错误框
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("缺少依赖", "请先安装 pandas 和 openpyxl：\n打开命令行执行：pip install pandas openpyxl")
    sys.exit(1)

# ======================= 配置区域 =======================
UNIT_PRICE_MIN = 0.01
UNIT_PRICE_MAX = 1000000.0
PRICE_TOLERANCE = 0.01
# =======================================================

class TradeCheckerApp:
    def __init__(self, master):
        self.master = master
        master.title("外贸单证检错工具")
        master.geometry("800x600")
        master.resizable(True, True)

        # ---- 顶部按钮区域 ----
        btn_frame = tk.Frame(master)
        btn_frame.pack(pady=10, padx=10, fill=tk.X)

        self.label_file = tk.Label(btn_frame, text="当前文件：未选择", anchor='w', relief=tk.RIDGE, width=50)
        self.label_file.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.btn_choose = tk.Button(btn_frame, text="选择文件", command=self.choose_file)
        self.btn_choose.pack(side=tk.LEFT, padx=5)

        self.btn_sample = tk.Button(btn_frame, text="生成范例", command=self.generate_sample)
        self.btn_sample.pack(side=tk.LEFT, padx=5)

        self.btn_analyze = tk.Button(btn_frame, text="开始分析", command=self.run_analysis, state=tk.DISABLED)
        self.btn_analyze.pack(side=tk.LEFT, padx=5)

        # ---- 错误信息显示区域（单独区域） ----
        error_frame = tk.LabelFrame(master, text="检查报告（错误列表）", padx=5, pady=5)
        error_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.error_text = scrolledtext.ScrolledText(error_frame, wrap=tk.WORD, width=80, height=25)
        self.error_text.pack(fill=tk.BOTH, expand=True)

        self.current_file = None

    def choose_file(self):
        """选择待分析文件"""
        filetypes = [
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        filename = filedialog.askopenfilename(title="选择外贸文件", filetypes=filetypes)
        if filename:
            self.current_file = filename
            self.label_file.config(text="当前文件：" + os.path.basename(filename))
            self.btn_analyze.config(state=tk.NORMAL)
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, "已选择文件，点击“开始分析”进行检查。\n")

    def generate_sample(self):
        """生成包含错误的范例 Excel 文件（使用英文列名，与检错逻辑匹配）"""
        try:
            sample_data = {
                "order_id":   ["ORD001", "ORD002", "ORD003", "ORD004", "ORD005", "ORD006"],
                "product":    ["蓝牙耳机", "手机壳", "数据线", "充电宝", "无线鼠标", "键盘"],
                "quantity":   [100, 200, 150, None, 80, 50],
                "unit_price": [15.5, -3.2, 8.0, 25.0, 1000.0, 22.0],
                "total_price":[1550, 640, 1200, 500, 80000, 1100],
                "date":       ["2026-05-01", "2026-05-03", "2026/13/01", "2026-05-05", "2026-05-10", "2026-05-12"]
            }
            df = pd.DataFrame(sample_data)
            filename = "trade_sample_errors.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            messagebox.showinfo("生成成功", 
                "范例文件已生成：{}\n\n包含预设错误：\n"
                "- ORD002：单价为负数\n"
                "- ORD003：总价与数量*单价不匹配\n"
                "- ORD004：数量缺失\n"
                "- ORD003：日期格式无效（13月）\n"
                "- ORD005：单价/总价异常".format(filename))
        except Exception as e:
            messagebox.showerror("生成失败", str(e))

    def run_analysis(self):
        """执行分析并显示报告"""
        if not self.current_file:
            return
        filepath = self.current_file
        self.error_text.delete(1.0, tk.END)
        self.error_text.insert(tk.END, "正在分析文件，请稍候...\n")
        self.master.update()

        try:
            errors = self.analyze_file_to_errors(filepath)
            self.error_text.delete(1.0, tk.END)
            if not errors:
                self.error_text.insert(tk.END, "✅ 未发现任何错误，数据通过检查。")
            else:
                for msg in errors:
                    self.error_text.insert(tk.END, msg + "\n")

            # 询问是否保存标注文件
            if hasattr(self, 'annotated_df') and not self.annotated_df.empty:
                if messagebox.askyesno("导出结果", "是否将标注异常的文件另存为 Excel？"):
                    base, ext = os.path.splitext(filepath)
                    outfile = "{}_检查结果.xlsx".format(base)
                    self.annotated_df.to_excel(outfile, index=False, engine='openpyxl')
                    messagebox.showinfo("保存成功", "已保存到：\n{}".format(outfile))
        except Exception as e:
            self.error_text.delete(1.0, tk.END)
            self.error_text.insert(tk.END, "❌ 分析过程中出现错误：\n{}".format(e))

    def load_file(self, filepath):
        """根据扩展名加载 Excel 或 CSV 文件"""
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.xlsx', '.xls']:
            return pd.read_excel(filepath, engine='openpyxl')
        elif ext == '.csv':
            with io.open(filepath, 'rb') as f:
                return pd.read_csv(f, encoding='utf-8')
        else:
            raise ValueError("不支持的文件格式，请使用 .xlsx, .xls 或 .csv")

    def normalize_columns(self, df):
        """将中英文列名统一为内部标准列名"""
        column_mapping = {
            '商品名称': 'product', 'product': 'product', '品名': 'product',
            '数量': 'quantity', 'quantity': 'quantity', 'qty': 'quantity',
            '单价': 'unit_price', 'unit_price': 'unit_price', 'price': 'unit_price',
            '总价': 'total_price', 'total_price': 'total_price', 'amount': 'total_price',
            '订单号': 'order_id', 'order_id': 'order_id', '订单编号': 'order_id',
            '客户': 'customer', 'customer': 'customer', '客户名称': 'customer',
            '日期': 'date', 'date': 'date', '订单日期': 'date'
        }
        rename_dict = {}
        for col in df.columns:
            col_stripped = col.strip()
            if col_stripped in column_mapping:
                rename_dict[col] = column_mapping[col_stripped]
        return df.rename(columns=rename_dict)

    def analyze_dataframe(self, df, original_df):
        """对 DataFrame 执行一系列检查，返回错误列表和标注 DataFrame"""
        errors = []
        annotated = original_df.copy()
        annotated['错误备注'] = ''

        required = ['product', 'quantity', 'unit_price', 'total_price']
        missing_cols = [col for col in required if col not in df.columns]
        if missing_cols:
            errors.append("❌ 缺少关键列：{}（请确保文件包含商品名称、数量、单价、总价等列）".format(', '.join(missing_cols)))
            return errors, annotated

        for idx, row in df.iterrows():
            row_errors = []

            # --- 数量检查 ---
            qty = row['quantity']
            if pd.isna(qty):
                row_errors.append("数量缺失")
            else:
                try:
                    qty = float(qty)
                    if qty <= 0:
                        row_errors.append("数量非正数 ({})".format(qty))
                except (ValueError, TypeError):
                    row_errors.append("数量不是有效数字 ({})".format(qty))

            # --- 单价检查 ---
            up = row['unit_price']
            if pd.isna(up):
                row_errors.append("单价缺失")
            else:
                try:
                    up = float(up)
                    if up < 0:
                        row_errors.append("单价为负数 ({})".format(up))
                    elif up == 0:
                        row_errors.append("单价为零")
                    elif up < UNIT_PRICE_MIN:
                        row_errors.append("单价过低 ({})".format(up))
                    elif up > UNIT_PRICE_MAX:
                        row_errors.append("单价过高 ({})".format(up))
                except (ValueError, TypeError):
                    row_errors.append("单价不是有效数字 ({})".format(up))

            # --- 总价检查 ---
            tp = row['total_price']
            if pd.isna(tp):
                row_errors.append("总价缺失")
            else:
                try:
                    tp = float(tp)
                    if tp < 0:
                        row_errors.append("总价为负数 ({})".format(tp))
                except (ValueError, TypeError):
                    row_errors.append("总价不是有效数字 ({})".format(tp))

            # --- 数量*单价 vs 总价 计算校验 ---
            if not pd.isna(qty) and not pd.isna(up) and not pd.isna(tp):
                try:
                    qty_f = float(qty)
                    up_f = float(up)
                    tp_f = float(tp)
                    expected = qty_f * up_f
                    if expected != 0:
                        rel_error = abs(tp_f - expected) / abs(expected)
                        if rel_error > PRICE_TOLERANCE:
                            row_errors.append(
                                "总价不匹配：期望 {:.2f}，实际 {:.2f}，相对误差 {:.2%}".format(expected, tp_f, rel_error))
                    else:
                        if abs(tp_f) > 0.01:
                            row_errors.append("总价不匹配：数量*单价为0，但总价为 {}".format(tp_f))
                except:
                    row_errors.append("价格计算过程中出现异常")

            # --- 日期格式检查 ---
            if 'date' in df.columns:
                date_val = row['date']
                if pd.notna(date_val):
                    try:
                        pd.to_datetime(date_val)
                    except:
                        row_errors.append("日期格式无效 ({})".format(date_val))

            if row_errors:
                excel_row = idx + 2
                errors.append("第 {} 行 (订单号: {}): {}".format(
                    excel_row,
                    row.get('order_id', 'N/A'),
                    '; '.join(row_errors)))
                annotated.at[idx, '错误备注'] = '; '.join(row_errors)

        # --- 订单号重复检查 ---
        if 'order_id' in df.columns:
            dup_ids = df['order_id'].dropna()
            if dup_ids.duplicated().any():
                dup_list = dup_ids[dup_ids.duplicated()].unique()
                errors.append("⚠️ 发现重复的订单号：{}".format(list(dup_list)))
                dup_mask = df['order_id'].isin(dup_list)
                for idx in df[dup_mask].index:
                    existing_note = annotated.at[idx, '错误备注']
                    if existing_note:
                        annotated.at[idx, '错误备注'] += '; 订单号重复'
                    else:
                        annotated.at[idx, '错误备注'] = '订单号重复'

        if not errors:
            errors.append("✅ 未发现明显错误，数据通过基本检查。")
        else:
            errors.insert(0, "🔍 共发现 {} 项异常：".format(len(errors)))

        return errors, annotated

    def analyze_file_to_errors(self, filepath):
        """分析文件并返回错误字符串列表（供 GUI 使用），同时保存标注 DataFrame"""
        df_original = self.load_file(filepath)
        df_normalized = self.normalize_columns(df_original.copy())
        errors, annotated = self.analyze_dataframe(df_normalized, df_original)
        self.annotated_df = annotated
        return errors

def main():
    root = tk.Tk()
    app = TradeCheckerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()


# In[ ]:




