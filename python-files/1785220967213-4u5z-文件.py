import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

class ExtractApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel 行提取工具")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # 变量
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.sheet_name = tk.StringVar()
        self.column_name = tk.StringVar()
        self.keyword = tk.StringVar()
        self.match_mode = tk.StringVar(value="exact")

        # 用于存储工作表列表和列名列表
        self.sheet_list = []
        self.column_list = []

        # 创建界面组件
        self.create_widgets()

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== 源文件 =====
        row1 = ttk.Frame(main_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="源 Excel 文件：").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.input_file, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(row1, text="浏览", command=self.browse_input).pack(side=tk.LEFT)

        # ===== 加载按钮（读取工作表/列名） =====
        load_frame = ttk.Frame(main_frame)
        load_frame.pack(fill=tk.X, pady=5)
        ttk.Button(load_frame, text="加载文件信息（读取工作表及列名）", command=self.load_file_info).pack()

        # ===== 工作表 =====
        row2 = ttk.Frame(main_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="工作表名称：").pack(side=tk.LEFT)
        self.sheet_combo = ttk.Combobox(row2, textvariable=self.sheet_name, state="readonly", width=30)
        self.sheet_combo.pack(side=tk.LEFT, padx=5)

        # ===== 列名 =====
        row3 = ttk.Frame(main_frame)
        row3.pack(fill=tk.X, pady=5)
        ttk.Label(row3, text="搜索列名：").pack(side=tk.LEFT)
        self.column_combo = ttk.Combobox(row3, textvariable=self.column_name, state="readonly", width=30)
        self.column_combo.pack(side=tk.LEFT, padx=5)

        # ===== 关键字 =====
        row4 = ttk.Frame(main_frame)
        row4.pack(fill=tk.X, pady=5)
        ttk.Label(row4, text="搜索关键字：").pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=self.keyword, width=35).pack(side=tk.LEFT, padx=5)

        # ===== 匹配模式 =====
        row5 = ttk.Frame(main_frame)
        row5.pack(fill=tk.X, pady=5)
        ttk.Label(row5, text="匹配模式：").pack(side=tk.LEFT)
        ttk.Radiobutton(row5, text="精确匹配", variable=self.match_mode, value="exact").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row5, text="包含匹配", variable=self.match_mode, value="contains").pack(side=tk.LEFT, padx=5)

        # ===== 输出文件 =====
        row6 = ttk.Frame(main_frame)
        row6.pack(fill=tk.X, pady=5)
        ttk.Label(row6, text="输出文件：").pack(side=tk.LEFT)
        ttk.Entry(row6, textvariable=self.output_file, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(row6, text="浏览", command=self.browse_output).pack(side=tk.LEFT)

        # ===== 执行按钮 =====
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="开始提取", command=self.run_extract, width=20).pack()

        # ===== 日志框 =====
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, message):
        """在日志区域追加消息"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def browse_input(self):
        path = filedialog.askopenfilename(
            title="选择 Excel 文件",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.input_file.set(path)
            # 清空之前加载的信息
            self.sheet_combo.set('')
            self.column_combo.set('')
            self.sheet_combo['values'] = []
            self.column_combo['values'] = []
            # 自动设置输出文件名（与源文件同目录，加 _result）
            dirname = os.path.dirname(path)
            basename = os.path.basename(path)
            name, ext = os.path.splitext(basename)
            default_out = os.path.join(dirname, f"{name}_result{ext}")
            self.output_file.set(default_out)

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if path:
            self.output_file.set(path)

    def load_file_info(self):
        """读取 Excel 文件，获取工作表列表和第一个工作表的列名"""
        input_path = self.input_file.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("错误", "请先选择有效的源文件！")
            return
        try:
            # 获取所有工作表名
            xl = pd.ExcelFile(input_path, engine="openpyxl" if input_path.endswith('.xlsx') else None)
            self.sheet_list = xl.sheet_names
            self.sheet_combo['values'] = self.sheet_list
            if self.sheet_list:
                self.sheet_combo.set(self.sheet_list[0])
                self.sheet_name.set(self.sheet_list[0])
            else:
                self.log("未找到任何工作表。")
                return

            # 读取第一个工作表以获取列名
            first_sheet = self.sheet_list[0]
            df = pd.read_excel(input_path, sheet_name=first_sheet, nrows=0, engine="openpyxl" if input_path.endswith('.xlsx') else None)
            self.column_list = list(df.columns)
            self.column_combo['values'] = self.column_list
            if self.column_list:
                self.column_combo.set(self.column_list[0])
                self.column_name.set(self.column_list[0])
            else:
                self.log("警告：第一个工作表无列名。")
            self.log(f"成功加载文件，共有 {len(self.sheet_list)} 个工作表，{len(self.column_list)} 列。")
            self.log(f"当前默认工作表：{first_sheet}，默认列：{self.column_list[0] if self.column_list else '无'}")

        except Exception as e:
            messagebox.showerror("加载失败", f"读取文件出错：{str(e)}")
            self.log(f"加载失败：{str(e)}")

    def run_extract(self):
        # 参数检查
        input_path = self.input_file.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("错误", "源文件不存在，请选择文件。")
            return
        sheet = self.sheet_name.get().strip()
        if not sheet:
            messagebox.showerror("错误", "请选择或输入工作表名称。")
            return
        col = self.column_name.get().strip()
        if not col:
            messagebox.showerror("错误", "请选择搜索列。")
            return
        keyword = self.keyword.get().strip()
        if not keyword:
            messagebox.showerror("错误", "请输入搜索关键字。")
            return
        output_path = self.output_file.get().strip()
        if not output_path:
            messagebox.showerror("错误", "请指定输出文件路径。")
            return
        mode = self.match_mode.get()

        try:
            # 读取数据
            df = pd.read_excel(input_path, sheet_name=sheet, engine="openpyxl" if input_path.endswith('.xlsx') else None)
            if col not in df.columns:
                messagebox.showerror("错误", f"列 '{col}' 不存在于当前工作表中。")
                return

            # 匹配
            if mode == "exact":
                mask = df[col].astype(str).str.strip() == keyword.strip()
            else:  # contains
                mask = df[col].astype(str).str.contains(keyword, na=False, case=False)

            result_df = df[mask].copy()
            count = len(result_df)

            if count == 0:
                self.log("未找到匹配的行。")
                messagebox.showinfo("提示", "没有匹配任何行，请检查关键字或模式。")
                return

            # 保存结果
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                result_df.to_excel(writer, sheet_name="提取结果", index=False)

            self.log(f"提取完成！共匹配 {count} 行，已保存到：{output_path}")
            messagebox.showinfo("成功", f"提取成功！\n匹配行数：{count}\n输出文件：{output_path}")

        except Exception as e:
            messagebox.showerror("执行出错", f"提取过程发生错误：\n{str(e)}")
            self.log(f"错误：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtractApp(root)
    root.mainloop()