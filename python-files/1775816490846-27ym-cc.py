import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import csv
import traceback

def process_csv_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # 寻找真正的表头（定位包含 id 和 name 的行）
        header_row_index = -1
        for i, row in enumerate(rows):
            if 'id' in row and 'name' in row:
                header_row_index = i
                break
                
        if header_row_index == -1:
            return False, "在文件中找不到 'id' 和 'name' 表头，请确认文件格式！"

        headers = rows[header_row_index]
        data_rows = rows[header_row_index + 1:]

        # 必须要保留的字段
        target_keys = ["id", "name", "descript", "unlock", "storeClass", "goodsType", "price", "recipe"]
        
        build_list = []
        for row in data_rows:
            # 如果这一行长度比表头短，或者 id 为空，则跳过
            if not row or len(row) <= headers.index('id') or not row[headers.index('id')].strip():
                continue
                
            item = {}
            for key in target_keys:
                if key in headers:
                    val = row[headers.index(key)].strip()
                    
                    # 处理空值
                    if val == "":
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
                        item[key] = val
            
            # 如果提取到了 id，则加入列表
            if "id" in item and item["id"]:
                build_list.append(item)

        # 构建最终的 JSON 结构
        final_json = {
            "build": build_list
        }

        # 写入 JSON 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, ensure_ascii=False, indent=4)
            
        return True, "转换成功！"
    except Exception as e:
        return False, f"转换失败：\n{str(e)}"

class ExcelToJsonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV 转 JSON 工具 (纯净版)")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        self.input_file = ""

        # UI 元素
        tk.Label(root, text="第一步：选择需要转换的 CSV 文件").pack(pady=10)
        
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
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")]
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
            success, msg = process_csv_file(self.input_file, save_path)
            if success:
                messagebox.showinfo("成功", "文件已成功转换为 JSON 格式！")
            else:
                messagebox.showerror("错误", msg)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ExcelToJsonApp(root)
        root.mainloop()
    except Exception as e:
        # 万一崩溃，弹出 DOS 窗口显示具体错误，而不是一闪而过
        print("程序发生严重错误：")
        traceback.print_exc()
        input("\n按回车键退出...")