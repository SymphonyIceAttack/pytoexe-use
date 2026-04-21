"""
Cython 编译工具 - GUI 版本
支持文件选择、输出目录设置、编译选项配置
可打包为单文件 exe
"""
import os
import sys
import shutil
import glob
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from distutils.core import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

class CythonCompilerGUI:
    """Cython 编译器图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cython 编译工具 - Python 代码加密")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.selected_files = []
        self.is_compiling = False
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """设置界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_file_section(main_frame)
        self.create_output_section(main_frame)
        self.create_options_section(main_frame)
        self.create_progress_section(main_frame)
        self.create_button_section(main_frame)
    
    def create_file_section(self, parent):
        """文件选择区域"""
        file_frame = ttk.LabelFrame(parent, text="选择要编译的 Python 文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(btn_frame, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="移除选中", command=self.remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空列表", command=self.clear_files).pack(side=tk.LEFT)
        
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(
            list_frame,
            height=8,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 9)
        )
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        self.file_count_label = ttk.Label(file_frame, text="已选择: 0 个文件", foreground="gray")
        self.file_count_label.pack(fill=tk.X, pady=(5, 0))
    
    def create_output_section(self, parent):
        """输出目录区域"""
        output_frame = ttk.LabelFrame(parent, text="输出目录设置", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        path_frame = ttk.Frame(output_frame)
        path_frame.pack(fill=tk.X)
        
        ttk.Label(path_frame, text="输出路径:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.output_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "dist_pyd"))
        self.output_entry = ttk.Entry(path_frame, textvariable=self.output_path_var, font=("Consolas", 9))
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(path_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT)
        
        build_frame = ttk.Frame(output_frame)
        build_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(build_frame, text="临时目录:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.build_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "build_cython"))
        ttk.Entry(build_frame, textvariable=self.build_path_var, font=("Consolas", 9)).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
    
    def create_options_section(self, parent):
        """编译选项区域"""
        options_frame = ttk.LabelFrame(parent, text="编译选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        options_grid = ttk.Frame(options_frame)
        options_grid.pack(fill=tk.X)
        
        self.optimize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_grid,
            text="启用优化（关闭边界检查）",
            variable=self.optimize_var
        ).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.remove_docstrings_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_grid,
            text="移除文档字符串",
            variable=self.remove_docstrings_var
        ).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        self.annotate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_grid,
            text="生成注释 HTML",
            variable=self.annotate_var
        ).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.clean_build_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_grid,
            text="编译前清理旧文件",
            variable=self.clean_build_var
        ).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        lang_frame = ttk.Frame(options_frame)
        lang_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(lang_frame, text="Python 版本:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.language_level_var = tk.StringVar(value="3")
        ttk.Combobox(
            lang_frame,
            textvariable=self.language_level_var,
            values=["2", "3"],
            width=5,
            state="readonly"
        ).pack(side=tk.LEFT)
    
    def create_progress_section(self, parent):
        """进度和日志区域"""
        progress_frame = ttk.LabelFrame(parent, text="编译日志", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            progress_frame,
            height=15,
            font=("Consolas", 9),
            state=tk.DISABLED,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        progress_bar_frame = ttk.Frame(progress_frame)
        progress_bar_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(progress_bar_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(progress_bar_frame, text="就绪", foreground="green")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_button_section(self, parent):
        """按钮区域"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        self.compile_btn = ttk.Button(
            btn_frame,
            text="开始编译",
            command=self.start_compilation,
            style="Accent.TButton"
        )
        self.compile_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(btn_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="打开输出目录", command=self.open_output_dir).pack(side=tk.LEFT)
    
    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="选择 Python 文件",
            filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.file_listbox.insert(tk.END, file)
        
        self.update_file_count()
    
    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择包含 Python 文件的文件夹")
        
        if folder:
            py_files = glob.glob(os.path.join(folder, "*.py"))
            count = 0
            
            for file in py_files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    self.file_listbox.insert(tk.END, file)
                    count += 1
            
            self.log(f"从文件夹添加了 {count} 个文件")
            self.update_file_count()
    
    def remove_selected(self):
        """移除选中的文件"""
        selected = self.file_listbox.curselection()
        
        for index in reversed(selected):
            self.file_listbox.delete(index)
            del self.selected_files[index]
        
        self.update_file_count()
    
    def clear_files(self):
        """清空文件列表"""
        self.file_listbox.delete(0, tk.END)
        self.selected_files.clear()
        self.update_file_count()
    
    def update_file_count(self):
        """更新文件计数"""
        count = len(self.selected_files)
        self.file_count_label.config(text=f"已选择: {count} 个文件")
    
    def browse_output(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        
        if directory:
            self.output_path_var.set(directory)
    
    def log(self, message, level="INFO"):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "INFO": "#4ec9b0",
            "SUCCESS": "#4ec9b0",
            "WARNING": "#dcdcaa",
            "ERROR": "#f44747",
            "DEBUG": "#808080"
        }
        
        color = colors.get(level, "#d4d4d4")
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "#808080")
        self.log_text.insert(tk.END, f"[{level}] ", color)
        self.log_text.insert(tk.END, f"{message}\n", "#d4d4d4")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def set_status(self, message, color="black"):
        """设置状态"""
        self.status_label.config(text=message, foreground=color)
    
    def start_compilation(self):
        """开始编译"""
        if self.is_compiling:
            messagebox.showwarning("警告", "编译正在进行中，请稍候...")
            return
        
        if not self.selected_files:
            messagebox.showerror("错误", "请先选择要编译的 Python 文件!")
            return
        
        output_dir = self.output_path_var.get().strip()
        if not output_dir:
            messagebox.showerror("错误", "请指定输出目录!")
            return
        
        self.is_compiling = True
        self.compile_btn.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.set_status("编译中...", "blue")
        
        thread = threading.Thread(target=self.compile_thread, daemon=True)
        thread.start()
    
    def compile_thread(self):
        """编译线程"""
        try:
            self.log("=" * 60)
            self.log("开始编译 Python 文件")
            self.log("=" * 60)
            
            output_dir = self.output_path_var.get()
            build_dir = self.build_path_var.get()
            
            self.log(f"输出目录: {output_dir}")
            self.log(f"临时目录: {build_dir}")
            self.log(f"文件数量: {len(self.selected_files)}")
            
            if self.clean_build_var.get():
                self.log("清理旧文件...")
                
                if os.path.exists(build_dir):
                    shutil.rmtree(build_dir)
                    self.log(f"已删除: {build_dir}")
                
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
                    self.log(f"已删除: {output_dir}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            self.log("\n配置编译选项...")
            
            Options.annotate = self.annotate_var.get()
            Options.docstrings = not self.remove_docstrings_var.get()
            
            compiler_directives = {
                'language_level': int(self.language_level_var.get()),
            }
            
            if self.optimize_var.get():
                compiler_directives.update({
                    'boundscheck': False,
                    'wraparound': False,
                    'cdivision': True,
                    'nonecheck': False,
                })
            
            self.log(f"优化: {'启用' if self.optimize_var.get() else '禁用'}")
            self.log(f"移除文档字符串: {'是' if self.remove_docstrings_var.get() else '否'}")
            self.log(f"生成注释: {'是' if self.annotate_var.get() else '否'}")
            
            self.log("\n开始编译...")
            
            setup(
                ext_modules=cythonize(
                    self.selected_files,
                    language_level=int(self.language_level_var.get()),
                    compiler_directives=compiler_directives
                ),
                script_args=['build_ext', '--build-lib', build_dir]
            )
            
            self.log("\n复制编译后的文件...")
            
            pyd_pattern = os.path.join(build_dir, "**", "*.pyd")
            pyd_files = glob.glob(pyd_pattern, recursive=True)
            
            if not pyd_files:
                self.log("错误: 没有找到编译生成的 .pyd 文件!", "ERROR")
                self.compilation_complete(False)
                return
            
            for pyd_file in pyd_files:
                filename = os.path.basename(pyd_file)
                dest = os.path.join(output_dir, filename)
                shutil.copy2(pyd_file, dest)
                self.log(f"  输出: {dest}", "SUCCESS")
            
            self.log("\n" + "=" * 60)
            self.log(f"编译完成! 共生成 {len(pyd_files)} 个文件", "SUCCESS")
            self.log(f"输出目录: {os.path.abspath(output_dir)}", "SUCCESS")
            self.log("=" * 60)
            
            self.compilation_complete(True)
            
        except Exception as e:
            self.log(f"\n编译失败: {str(e)}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            self.compilation_complete(False)
    
    def compilation_complete(self, success):
        """编译完成"""
        self.is_compiling = False
        self.compile_btn.config(state=tk.NORMAL)
        self.progress_bar.stop()
        
        if success:
            self.set_status("编译成功!", "green")
            self.root.after(100, lambda: messagebox.showinfo("成功", "编译完成!"))
        else:
            self.set_status("编译失败!", "red")
            self.root.after(100, lambda: messagebox.showerror("错误", "编译失败，请查看日志!"))
    
    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.output_path_var.get()
        
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showwarning("警告", f"输出目录不存在:\n{output_dir}")

def main():
    """主函数"""
    root = tk.Tk()
    
    try:
        from tkinter import font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=9)
    except:
        pass
    
    app = CythonCompilerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
