import pandas as pd
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

def one_excel_to_js(excel_path, js_path, log_func):
    """原有逻辑封装"""
    try:
        with pd.ExcelFile(excel_path) as xls:
            sheet_names = xls.sheet_names
            json_data = {}
            for sheet_name in sheet_names:
                # 忽略以下划线开头的页签
                if not sheet_name.startswith('_'):
                    # header=10 表示从第11行开始读取列名
                    df = pd.read_excel(xls, sheet_name=sheet_name, header=10)
                    df.fillna("", inplace=True)
                    
                    # 移除以下划线开头的列
                    df = df.loc[:, ~df.columns.astype(str).str.startswith('_')]
                    
                    # 转换为字典
                    data = df.to_dict(orient='records')
                    json_data[sheet_name] = data
            
            if json_data:
                with open(js_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)
                return True
            return False
    except Exception as e:
        log_func(f"❌ 错误: {os.path.basename(excel_path)} -> {str(e)}")
        return False

class ExcelToJsonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel 转 JSON 工具 v1.0")
        self.root.geometry("600x450")

        # --- UI 布局 ---
        # Excel 文件夹
        tk.Label(root, text="Excel 文件夹:").pack(pady=(10, 0), anchor="w", padx=20)
        self.entry_excel = tk.Entry(root, width=60)
        self.entry_excel.pack(side="top", pady=5, padx=20, fill="x")
        tk.Button(root, text="选择路径", command=self.select_excel_folder).pack(pady=2, padx=20, anchor="e")

        # JSON 文件夹
        tk.Label(root, text="JSON 输出文件夹:").pack(pady=(10, 0), anchor="w", padx=20)
        self.entry_json = tk.Entry(root, width=60)
        self.entry_json.pack(side="top", pady=5, padx=20, fill="x")
        tk.Button(root, text="选择路径", command=self.select_json_folder).pack(pady=2, padx=20, anchor="e")

        # 日志显示区域
        tk.Label(root, text="执行日志:").pack(pady=(10, 0), anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(root, height=10, width=70)
        self.log_area.pack(pady=10, padx=20, fill="both", expand=True)

        # 开始按钮
        self.btn_run = tk.Button(root, text="🚀 开始转换", bg="#4CAF50", fg="white", height=2, width=20, command=self.start_thread)
        self.btn_run.pack(pady=10)

    def select_excel_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_excel.delete(0, tk.END)
            self.entry_excel.insert(0, path)

    def select_json_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_json.delete(0, tk.END)
            self.entry_json.insert(0, path)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def start_thread(self):
        # 使用线程防止 UI 卡死
        t = threading.Thread(target=self.run_conversion)
        t.start()

    def run_conversion(self):
        excel_folder = self.entry_excel.get()
        output_folder = self.entry_json.get()

        if not excel_folder or not output_folder:
            messagebox.showwarning("提示", "请先选择输入和输出路径！")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        self.btn_run.config(state="disabled", text="转换中...")
        self.log("--- 转换开始 ---")
        
        count = 0
        files = [f for f in os.listdir(excel_folder) if f.endswith('.xlsx') and not f.startswith('~$')]
        
        for file_name in files:
            excel_path = os.path.join(excel_folder, file_name)
            js_name = file_name.replace('.xlsx', '.json')
            js_path = os.path.join(output_folder, js_name)
            
            if one_excel_to_js(excel_path, js_path, self.log):
                self.log(f"✅ 成功: {file_name} -> {js_name}")
                count += 1
        
        self.log(f"--- 转换结束，共完成 {count} 个文件 ---")
        self.btn_run.config(state="normal", text="🚀 开始转换")
        messagebox.showinfo("完成", f"成功转换 {count} 个文件！")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelToJsonGUI(root)
    root.mainloop()