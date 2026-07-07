# auto_build.py
"""
自动打包脚本 - 一键生成exe文件
运行此脚本会自动完成所有打包工作
"""

import os
import sys
import subprocess
import shutil

def check_and_install_packages():
    """检查并安装必要的包"""
    packages = ['pyinstaller', 'pandas', 'openpyxl', 'xlrd']
    
    print("="*50)
    print("正在检查并安装必要的Python包...")
    print("="*50)
    
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} 安装完成")
    
    print("\n所有依赖包已准备就绪！")

def create_icon():
    """创建简单的图标文件"""
    try:
        from PIL import Image, ImageDraw
        
        # 创建一个简单的图标
        size = 256
        img = Image.new('RGB', (size, size), color='#0078d4')
        draw = ImageDraw.Draw(img)
        
        # 绘制一个简单的图标（Excel样式）
        draw.rectangle([40, 40, 216, 216], outline='white', width=8)
        draw.text((80, 100), "📊", font=None, fill='white')
        
        img.save('app.ico', format='ICO')
        print("✓ 图标文件创建成功")
        return True
    except:
        print("⚠ 无法创建图标，将使用默认图标")
        return False

def create_main_program():
    """创建主程序文件"""
    main_code = '''# -*- coding: utf-8 -*-
"""
Excel数据提取工具 - 桌面版
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import os
import threading
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ExcelDataProcessor:
    """Excel数据处理核心类"""
    
    @staticmethod
    def read_excel(file_path, sheet_name=0):
        """读取Excel文件"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            return df
        except:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd')
                return df
            except Exception as e:
                raise Exception(f"读取文件失败: {str(e)}")
    
    @staticmethod
    def write_excel(df, file_path, sheet_name='数据'):
        """写入Excel文件"""
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            return True
        except Exception as e:
            raise Exception(f"写入文件失败: {str(e)}")
    
    @staticmethod
    def process_data(sheet2_path, sheet1_path, date_column, output_dir, callback=None):
        """处理数据的主函数"""
        try:
            if callback:
                callback("正在读取源数据文件...")
            df_sheet2 = ExcelDataProcessor.read_excel(sheet2_path)
            
            if callback:
                callback("正在读取目标模板文件...")
            df_sheet1 = ExcelDataProcessor.read_excel(sheet1_path)
            
            if date_column not in df_sheet2.columns:
                raise Exception(f"工作表2中找不到 '{date_column}' 列")
            if date_column not in df_sheet1.columns:
                raise Exception(f"工作表1中找不到 '{date_column}' 列")
            
            if callback:
                callback("正在处理日期数据...")
            df_sheet2[date_column] = pd.to_datetime(df_sheet2[date_column], errors='coerce')
            df_sheet1[date_column] = pd.to_datetime(df_sheet1[date_column], errors='coerce')
            
            df_sheet2 = df_sheet2.dropna(subset=[date_column])
            df_sheet1 = df_sheet1.dropna(subset=[date_column])
            
            if callback:
                callback("正在匹配数据...")
            
            df_result = df_sheet1.copy()
            sheet2_columns = [col for col in df_sheet2.columns if col != date_column]
            
            for col in sheet2_columns:
                if col not in df_result.columns:
                    df_result[col] = None
            
            date_dict = {}
            for idx, row in df_sheet2.iterrows():
                date_key = row[date_column]
                if date_key not in date_dict:
                    date_dict[date_key] = row
            
            match_count = 0
            unmatched_dates = []
            
            for idx, row in df_result.iterrows():
                target_date = row[date_column]
                if target_date in date_dict:
                    matching_row = date_dict[target_date]
                    for col in sheet2_columns:
                        if col in df_sheet2.columns and col in df_result.columns:
                            df_result.at[idx, col] = matching_row[col]
                    match_count += 1
                else:
                    date_str = target_date.strftime('%Y-%m-%d') if pd.notna(target_date) else '未知'
                    unmatched_dates.append(date_str)
            
            if callback:
                callback(f"匹配完成: {match_count} 条记录匹配成功")
            
            if callback:
                callback("正在保存完整数据...")
            
            result_file = os.path.join(os.path.dirname(sheet1_path), "工作表1_完整数据.xlsx")
            ExcelDataProcessor.write_excel(df_result, result_file)
            
            if callback:
                callback(f"完整数据已保存: {result_file}")
            
            if callback:
                callback("正在按日期拆分数据...")
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            df_result[date_column] = pd.to_datetime(df_result[date_column], errors='coerce')
            df_valid = df_result.dropna(subset=[date_column])
            grouped = df_valid.groupby(df_valid[date_column].dt.date)
            
            split_files = []
            for date_value, group_df in grouped:
                date_str = date_value.strftime('%Y%m%d')
                filename = os.path.join(output_dir, f"数据_{date_str}.xlsx")
                ExcelDataProcessor.write_excel(group_df, filename)
                split_files.append(filename)
                if callback:
                    callback(f"  ✓ {os.path.basename(filename)} ({len(group_df)} 条记录)")
            
            if callback:
                callback(f"拆分完成: 共 {len(split_files)} 个文件")
            
            return {
                'success': True,
                'match_count': match_count,
                'total_files': len(split_files),
                'result_file': result_file,
                'output_dir': output_dir,
                'unmatched_count': len(unmatched_dates)
            }
            
        except Exception as e:
            if callback:
                callback(f"错误: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class MainApplication:
    """主应用程序类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Excel数据提取工具 - WPS兼容版")
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        self.sheet2_path = tk.StringVar()
        self.sheet1_path = tk.StringVar()
        self.date_column = tk.StringVar(value="发货日期")
        self.output_dir = tk.StringVar(value="拆分结果")
        self.is_processing = False
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="📊 Excel数据提取与拆分工具",
            font=('Microsoft YaHei', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        desc_label = ttk.Label(
            main_frame,
            text="根据发货日期从工作表2提取数据到工作表1，并按日期拆分文件",
            font=('Microsoft YaHei', 10)
        )
        desc_label.pack(pady=(0, 20))
        
        # 文件设置区域
        input_frame = ttk.LabelFrame(main_frame, text="文件设置", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 工作表2
        ttk.Label(input_frame, text="源数据文件（工作表2）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        frame2 = ttk.Frame(input_frame)
        frame2.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(10, 0))
        ttk.Entry(frame2, textvariable=self.sheet2_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame2, text="浏览...", command=lambda: self.browse_file(self.sheet2_path, "选择源数据文件")).pack(side=tk.LEFT, padx=(5, 0))
        
        # 工作表1
        ttk.Label(input_frame, text="目标模板文件（工作表1）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        frame1 = ttk.Frame(input_frame)
        frame1.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(10, 0))
        ttk.Entry(frame1, textvariable=self.sheet1_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame1, text="浏览...", command=lambda: self.browse_file(self.sheet1_path, "选择目标模板文件")).pack(side=tk.LEFT, padx=(5, 0))
        
        # 日期列名
        ttk.Label(input_frame, text="日期列名:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.date_column, width=20).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # 输出目录
        ttk.Label(input_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, pady=5)
        frame_out = ttk.Frame(input_frame)
        frame_out.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5, padx=(10, 0))
        ttk.Entry(frame_out, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame_out, text="选择目录...", command=self.browse_directory).pack(side=tk.LEFT, padx=(5, 0))
        
        input_frame.columnconfigure(1, weight=1)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = ttk.Button(
            button_frame,
            text="🚀 开始处理",
            command=self.start_processing
        )
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="清空日志",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="打开输出目录",
            command=self.open_output_dir
        ).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            length=400,
            mode='indeterminate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            font=('Consolas', 9),
            wrap=tk.WORD,
            bg='#f8f8f8'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_label = ttk.Label(
            main_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Microsoft YaHei', 9)
        )
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def browse_file(self, var, title):
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            var.set(file_path)
    
    def browse_directory(self):
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.status_label.config(text="日志已清空")
    
    def open_output_dir(self):
        output_dir = self.output_dir.get()
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showwarning("警告", f"目录不存在: {output_dir}")
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def log_callback(self, message):
        self.root.after(0, lambda: self.log(message))
        self.root.after(0, lambda: self.update_status(message))
    
    def start_processing(self):
        if self.is_processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
        
        if not self.sheet2_path.get() or not self.sheet1_path.get():
            messagebox.showerror("错误", "请选择所有必需的文件")
            return
        
        self.clear_log()
        self.is_processing = True
        self.process_button.config(text="⏳ 处理中...", state='disabled')
        self.progress_bar.start(10)
        
        self.log("="*50)
        self.log("开始数据处理...")
        self.log(f"源数据文件: {self.sheet2_path.get()}")
        self.log(f"目标模板文件: {self.sheet1_path.get()}")
        self.log(f"日期列名: {self.date_column.get()}")
        self.log(f"输出目录: {self.output_dir.get()}")
        self.log("="*50)
        
        thread = threading.Thread(target=self.process_data_thread)
        thread.daemon = True
        thread.start()
    
    def process_data_thread(self):
        try:
            result = ExcelDataProcessor.process_data(
                self.sheet2_path.get(),
                self.sheet1_path.get(),
                self.date_column.get(),
                self.output_dir.get(),
                self.log_callback
            )
            self.root.after(0, lambda: self.on_process_complete(result))
        except Exception as e:
            self.root.after(0, lambda: self.on_process_error(str(e)))
    
    def on_process_complete(self, result):
        self.progress_bar.stop()
        self.is_processing = False
        self.process_button.config(text="🚀 开始处理", state='normal')
        
        if result['success']:
            self.log("="*50)
            self.log("✅ 处理完成！")
            self.log(f"匹配记录数: {result['match_count']}")
            self.log(f"生成文件数: {result['total_files']}")
            self.log(f"输出目录: {result['output_dir']}")
            self.log("="*50)
            self.status_label.config(text="✅ 处理完成")
            messagebox.showinfo("完成", f"处理完成！共生成 {result['total_files']} 个文件。")
        else:
            self.log("="*50)
            self.log(f"❌ 处理失败: {result.get('error', '未知错误')}")
            self.log("="*50)
            self.status_label.config(text="❌ 处理失败")
            messagebox.showerror("错误", f"处理失败:\n{result.get('error', '未知错误')}")
    
    def on_process_error(self, error_msg):
        self.progress_bar.stop()
        self.is_processing = False
        self.process_button.config(text="🚀 开始处理", state='normal')
        self.log(f"❌ 错误: {error_msg}")
        self.status_label.config(text="❌ 处理失败")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
'''
    
    with open('excel_data_tool.py', 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("✓ 主程序文件创建成功")

def build_exe():
    """打包exe文件"""
    print("\n" + "="*50)
    print("开始打包exe文件...")
    print("="*50)
    
    # 检查是否有图标
    icon_option = "--icon=app.ico" if os.path.exists('app.ico') else ""
    
    # PyInstaller打包命令
    cmd = f'pyinstaller --onefile --windowed --name Excel数据处理工具 {icon_option} --hidden-import pandas --hidden-import openpyxl --hidden-import xlrd excel_data_tool.py'
    
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\n✅ 打包成功！")
        print(f"exe文件位置: {os.path.abspath('dist/Excel数据处理工具.exe')}")
        print("\n您可以将 dist 文件夹中的 exe 文件复制到桌面使用")
    else:
        print("\n❌ 打包失败")
        print(result.stderr)

def main():
    """主函数"""
    print("="*60)
    print("  Excel数据处理工具 - 自动打包程序")
    print("="*60)
    print("\n此程序将自动完成以下步骤：")
    print("1. 检查并安装必要的Python包")
    print("2. 创建主程序文件")
    print("3. 创建图标文件")
    print("4. 打包成exe文件")
    print("\n开始执行...\n")
    
    # 步骤1: 安装依赖
    check_and_install_packages()
    
    # 步骤2: 创建程序文件
    create_main_program()
    
    # 步骤3: 创建图标
    create_icon()
    
    # 步骤4: 打包
    build_exe()
    
    print("\n" + "="*60)
    print("  所有步骤完成！")
    print("="*60)

if __name__ == "__main__":
    main()