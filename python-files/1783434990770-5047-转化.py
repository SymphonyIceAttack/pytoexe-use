# build_exe.py
"""
改进的自动打包脚本 - 带详细日志和错误处理
"""

import os
import sys
import subprocess
import shutil
import time

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def install_packages():
    """安装必要的包"""
    print_header("安装依赖包")
    
    packages = [
        'pandas',
        'openpyxl', 
        'xlrd',
        'pyinstaller',
        'pillow'  # 用于创建图标
    ]
    
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} 已安装")
        except ImportError:
            print(f"正在安装 {pkg}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                print(f"✓ {pkg} 安装成功")
            except Exception as e:
                print(f"✗ {pkg} 安装失败: {e}")

def create_main_program():
    """创建主程序文件"""
    print_header("创建主程序文件")
    
    # 检查文件是否已存在
    if os.path.exists('excel_data_tool.py'):
        response = input("excel_data_tool.py 已存在，是否覆盖? (y/n): ")
        if response.lower() != 'y':
            print("使用现有文件")
            return True
    
    print("正在创建 excel_data_tool.py...")
    
    try:
        # 简化的主程序代码（包含所有功能）
        main_code = '''# -*- coding: utf-8 -*-
"""
Excel数据提取工具 - WPS兼容版
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
    @staticmethod
    def read_excel(file_path, sheet_name=0):
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        except:
            return pd.read_excel(file_path, sheet_name=sheet_name, engine='xlrd')
    
    @staticmethod
    def write_excel(df, file_path, sheet_name='数据'):
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        return True
    
    @staticmethod
    def process_data(sheet2_path, sheet1_path, date_column, output_dir, callback=None):
        try:
            if callback: callback("读取源数据文件...")
            df_sheet2 = ExcelDataProcessor.read_excel(sheet2_path)
            
            if callback: callback("读取目标模板文件...")
            df_sheet1 = ExcelDataProcessor.read_excel(sheet1_path)
            
            if date_column not in df_sheet2.columns:
                raise Exception(f"工作表2中找不到 '{date_column}' 列")
            if date_column not in df_sheet1.columns:
                raise Exception(f"工作表1中找不到 '{date_column}' 列")
            
            if callback: callback("处理日期数据...")
            df_sheet2[date_column] = pd.to_datetime(df_sheet2[date_column], errors='coerce')
            df_sheet1[date_column] = pd.to_datetime(df_sheet1[date_column], errors='coerce')
            
            df_sheet2 = df_sheet2.dropna(subset=[date_column])
            df_sheet1 = df_sheet1.dropna(subset=[date_column])
            
            if callback: callback("匹配数据...")
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
            for idx, row in df_result.iterrows():
                target_date = row[date_column]
                if target_date in date_dict:
                    matching_row = date_dict[target_date]
                    for col in sheet2_columns:
                        if col in df_sheet2.columns and col in df_result.columns:
                            df_result.at[idx, col] = matching_row[col]
                    match_count += 1
            
            if callback: callback(f"匹配完成: {match_count} 条")
            
            if callback: callback("保存完整数据...")
            result_file = os.path.join(os.path.dirname(sheet1_path), "工作表1_完整数据.xlsx")
            ExcelDataProcessor.write_excel(df_result, result_file)
            
            if callback: callback("按日期拆分...")
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
            
            return {
                'success': True,
                'match_count': match_count,
                'total_files': len(split_files),
                'result_file': result_file,
                'output_dir': output_dir
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel数据提取工具")
        self.root.geometry("800x650")
        
        self.sheet2_path = tk.StringVar()
        self.sheet1_path = tk.StringVar()
        self.date_column = tk.StringVar(value="发货日期")
        self.output_dir = tk.StringVar(value="拆分结果")
        self.is_processing = False
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        self.root.update_idletasks()
        w, h = 800, 650
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="Excel数据提取与拆分工具", 
                 font=('Microsoft YaHei', 16, 'bold')).pack(pady=(0, 20))
        
        # 文件设置
        input_frame = ttk.LabelFrame(main_frame, text="文件设置", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 源数据文件
        ttk.Label(input_frame, text="源数据文件（工作表2）:").grid(row=0, column=0, sticky=tk.W, pady=5)
        frame2 = ttk.Frame(input_frame)
        frame2.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(10, 0))
        ttk.Entry(frame2, textvariable=self.sheet2_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame2, text="浏览...", command=lambda: self.browse_file(self.sheet2_path)).pack(side=tk.LEFT, padx=(5, 0))
        
        # 目标模板文件
        ttk.Label(input_frame, text="目标模板文件（工作表1）:").grid(row=1, column=0, sticky=tk.W, pady=5)
        frame1 = ttk.Frame(input_frame)
        frame1.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(10, 0))
        ttk.Entry(frame1, textvariable=self.sheet1_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame1, text="浏览...", command=lambda: self.browse_file(self.sheet1_path)).pack(side=tk.LEFT, padx=(5, 0))
        
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
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))
        
        # 日志
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, pady=(10, 0))
    
    def browse_file(self, var):
        path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx *.xls")])
        if path:
            var.set(path)
    
    def browse_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def open_output_dir(self):
        if os.path.exists(self.output_dir.get()):
            os.startfile(self.output_dir.get())
    
    def start_processing(self):
        if self.is_processing:
            return
        
        if not self.sheet2_path.get() or not self.sheet1_path.get():
            messagebox.showerror("错误", "请选择所有必需的文件")
            return
        
        self.clear_log()
        self.is_processing = True
        self.process_button.config(text="处理中...", state='disabled')
        self.progress_bar.start()
        
        self.log("开始处理...")
        thread = threading.Thread(target=self.process_thread)
        thread.daemon = True
        thread.start()
    
    def process_thread(self):
        result = ExcelDataProcessor.process_data(
            self.sheet2_path.get(),
            self.sheet1_path.get(),
            self.date_column.get(),
            self.output_dir.get(),
            self.log
        )
        self.root.after(0, lambda: self.on_complete(result))
    
    def on_complete(self, result):
        self.progress_bar.stop()
        self.is_processing = False
        self.process_button.config(text="开始处理", state='normal')
        
        if result['success']:
            self.log(f"处理完成！共生成 {result['total_files']} 个文件")
            messagebox.showinfo("完成", f"处理完成！共生成 {result['total_files']} 个文件")
        else:
            self.log(f"处理失败: {result.get('error', '未知错误')}")
            messagebox.showerror("错误", f"处理失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
'''
        
        with open('excel_data_tool.py', 'w', encoding='utf-8') as f:
            f.write(main_code)
        
        print("✓ 主程序文件创建成功")
        return True
        
    except Exception as e:
        print(f"✗ 创建失败: {e}")
        return False

def create_icon():
    """创建图标"""
    print_header("创建图标")
    
    try:
        from PIL import Image, ImageDraw
        
        # 创建图标
        size = 256
        img = Image.new('RGB', (size, size), '#0078d4')
        draw = ImageDraw.Draw(img)
        
        # 绘制简单图形
        draw.rectangle([40, 40, 216, 216], outline='white', width=10)
        draw.text((85, 95), "📊", fill='white')
        
        img.save('app.ico', format='ICO')
        print("✓ 图标创建成功")
        return True
        
    except Exception as e:
        print(f"⚠ 图标创建失败: {e}")
        print("将使用默认图标")
        return False

def build_exe():
    """打包exe文件"""
    print_header("开始打包")
    
    # 清理旧的打包文件
    dirs_to_clean = ['dist', 'build']
    for d in dirs_to_clean:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"✓ 清理 {d} 目录")
            except:
                print(f"⚠ 清理 {d} 目录失败")
    
    # 构建打包命令
    icon_option = "--icon=app.ico" if os.path.exists('app.ico') else ""
    cmd = (
        f'pyinstaller --onefile --windowed '
        f'--name Excel数据处理工具 '
        f'{icon_option} '
        f'--hidden-import pandas '
        f'--hidden-import openpyxl '
        f'--hidden-import xlrd '
        f'--hidden-import tkinter '
        f'--hidden-import PIL '
        f'excel_data_tool.py'
    )
    
    print(f"执行命令: {cmd}")
    print("\n打包过程可能需要几分钟，请耐心等待...\n")
    
    try:
        # 执行打包
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        # 显示结果
        if result.stdout:
            print("输出信息:")
            print(result.stdout[-1000:])  # 只显示最后1000个字符
        
        if result.returncode == 0:
            print("\n✓ 打包成功！")
            
            # 检查exe文件
            exe_path = 'dist/Excel数据处理工具.exe'
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / 1024 / 1024
                print(f"\n✅ exe文件已生成:")
                print(f"  位置: {os.path.abspath(exe_path)}")
                print(f"  大小: {size_mb:.2f} MB")
                return True
            else:
                print("\n❌ 打包成功但exe文件不存在")
                return False
        else:
            print(f"\n❌ 打包失败 (错误代码: {result.returncode})")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ 打包超时（超过5分钟）")
        return False
    except Exception as e:
        print(f"\n❌ 打包出错: {e}")
        return False

def main():
    """主函数"""
    clear_screen()
    print_header("Excel数据处理工具 - 自动打包程序")
    
    print("此程序将自动完成以下步骤：")
    print("1. 安装必要的Python包")
    print("2. 创建主程序文件")
    print("3. 创建图标文件")
    print("4. 打包成exe文件")
    print("\n注意：打包过程需要几分钟时间")
    
    input("\n按Enter键开始...")
    
    # 步骤1: 安装依赖
    install_packages()
    
    # 步骤2: 创建主程序
    if not create_main_program():
        print("主程序创建失败，退出")
        sys.exit(1)
    
    # 步骤3: 创建图标
    create_icon()
    
    # 步骤4: 打包
    if build_exe():
        print_header("🎉 打包完成！")
        print("\n您可以在 dist 文件夹中找到 exe 文件")
        print("将 Excel数据处理工具.exe 复制到桌面即可使用")
    else:
        print_header("❌ 打包失败")
        print("\n请检查错误信息并重试")
        print("如果问题持续，请尝试手动打包：")
        print("  pyinstaller --onefile --windowed --name Excel数据处理工具 excel_data_tool.py")

if __name__ == "__main__":
    main()