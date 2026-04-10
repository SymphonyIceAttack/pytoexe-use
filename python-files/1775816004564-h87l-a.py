import pandas as pd
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import os

class ExcelToJsonConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel 转 JSON 工具 - 游戏配置专用")
        self.root.geometry("500x250")

        # 变量存储路径
        self.excel_path = tk.StringVar()
        self.save_path = tk.StringVar()

        # 界面布局
        tk.Label(root, text="第一步：选择 Excel 文件 (.xlsx)").pack(pady=(20, 5))
        frame1 = tk.Frame(root)
        frame1.pack()
        tk.Entry(frame1, textvariable=self.excel_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(frame1, text="浏览", command=self.select_excel).pack(side=tk.LEFT)

        tk.Label(root, text="第二步：执行转换").pack(pady=(30, 5))
        tk.Button(root, text="开始转换并保存 JSON", command=self.convert, 
                  bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20).pack()

        self.status_label = tk.Label(root, text="等待操作...", fg="gray")
        self.status_label.pack(side=tk.BOTTOM, pady=10)

    def select_excel(self):
        file = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file:
            self.excel_path.set(file)
            # 默认保存路径为同名 json
            self.save_path.set(file.rsplit('.', 1)[0] + ".json")

    def convert(self):
        input_file = self.excel_path.get()
        if not input_file:
            messagebox.showwarning("错误", "请先选择 Excel 文件！")
            return

        try:
            self.status_label.config(text="转换中，请稍候...", fg="blue")
            self.root.update()

            # 读取所有 Sheet
            xls = pd.ExcelFile(input_file)
            final_data = {}

            for sheet_name in xls.sheet_names:
                # 跳过目录或映射等辅助页签（可根据需要调整）
                if sheet_name.startswith('_'):
                    continue
                
                # 读取 Sheet 寻找表头
                # 逻辑：寻找包含 "id" 的行作为 header
                df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                header_idx = None
                for idx, row in df_raw.iterrows():
                    if "id" in row.values:
                        header_idx = idx
                        break
                
                if header_idx is not None:
                    # 重新以找到的行作为表头读取
                    df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=header_idx)
                    
                    # 清理空列和完全为空的行
                    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                    df = df.dropna(how='all', subset=['id'])

                    # 处理数值类型，防止 JSON 中出现 NaN
                    df = df.where(pd.notnull(df), None)

                    # 转换为对象列表
                    # pandas 会自动处理重复列名为 name, name.1, name.2
                    sheet_list = df.to_dict(orient='records')
                    final_data[sheet_name] = sheet_list

            # 导出 JSON
            output_file = self.save_path.get()
            with open(output_file, 'w', encoding='utf-8') as f:
                # ensure_ascii=False 保证中文不乱码，indent=4 保持美观
                json.dump(final_data, f, ensure_ascii=False, indent=4)

            self.status_label.config(text="转换成功！", fg="green")
            messagebox.showinfo("成功", f"JSON 文件已生成：\n{output_file}")

        except Exception as e:
            self.status_label.config(text="转换失败", fg="red")
            messagebox.showerror("发生错误", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToJsonConverter(root)
    root.mainloop()