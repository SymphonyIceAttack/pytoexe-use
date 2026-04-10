import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import json
import os

def process_file(input_path, output_path):
    try:
        # 判断是 Excel 还是 CSV 文件
        if input_path.endswith('.csv'):
            # 自动跳过前面的空行或页签说明，找到表头。
            # 这里假设有 id 和 name 的那一行是表头
            df = pd.read_csv(input_path, dtype=str)
        else:
            df = pd.read_excel(input_path, dtype=str)
        
        # 寻找真正的表头（如果前几行是无效说明数据）
        header_row_index = None
        for i, row in df.iterrows():
            if 'id' in row.values and 'name' in row.values:
                header_row_index = i
                break
                
        if header_row_index is not None:
            if input_path.endswith('.csv'):
                df = pd.read_csv(input_path, skiprows=header_row_index + 1, dtype=str)
            else:
                df = pd.read_excel(input_path, skiprows=header_row_index + 1, dtype=str)

        # 必须要保留的字段（如果表格中有）
        target_keys = ["id", "name", "descript", "unlock", "storeClass", "goodsType", "price", "recipe"]
        
        build_list = []
        for _, row in df.iterrows():
            # 跳过没有 id 的空行
            if pd.isna(row.get('id')) or str(row.get('id')).strip() == "":
                continue
                
            item = {}
            for key in target_keys:
                if key in df.columns:
                    val = row[key]
                    
                    # 处理空值
                    if pd.isna(val):
                        if key in ["unlock", "price"]:
                            item[key] = 0
                        else:
                            item[key] = ""
                        continue
                    
                    # 转换数字类型
                    if key in ["unlock", "price"]:
                        try:
                            item[key] = int(float(val))
                        except ValueError:
                            item[key] = 0
                    else:
                        item[key] = str(val).strip()
            
            build_list.append(item)

        # 构建最终的 JSON 结构
        final_json = {
            "build": build_list
        }

        # 写入 JSON 文件，保持良好的缩进和中文显示
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, ensure_ascii=False, indent=4)
            
        return True, "转换成功！"
    except Exception as e:
        return False, f"转换失败：\n{str(e)}"

class ExcelToJsonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel/CSV 转 JSON 工具")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        self.input_file = ""
        self.output_file = ""

        # UI 元素
        tk.Label(root, text="第一步：选择需要转换的表格文件 (.xlsx / .csv)").pack(pady=10)
        
        self.btn_select = tk.Button(root, text="选择文件", command=self.select_file, width=20)
        self.btn_select.pack()

        self.lbl_file = tk.Label(root, text="未选择文件", fg="gray")
        self.lbl_file.pack(pady=5)

        tk.Label(root, text="第二步：执行转换并保存").pack(pady=10)

        self.btn_convert = tk.Button(root, text="转换为 JSON", command=self.convert, width=20, state=tk.DISABLED)
        self.btn_convert.pack()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="选择表格文件",
            filetypes=[("表格文件", "*.xlsx *.csv"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_file = file_path
            self.lbl_file.config(text=os.path.basename(file_path), fg="black")
            self.btn_convert.config(state=tk.NORMAL)

    def convert(self):
        if not self.input_file:
            return

        save_path = filedialog.asksaveasfilename(
            title="保存 JSON 文件",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            initialfile="ArticsConfig.json"
        )
        if save_path:
            success, msg = process_file(self.input_file, save_path)
            if success:
                messagebox.showinfo("成功", "文件已成功转换为 JSON 格式！")
            else:
                messagebox.showerror("错误", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToJsonApp(root)
    root.mainloop()