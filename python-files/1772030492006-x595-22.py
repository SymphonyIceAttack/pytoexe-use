# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

# --- 核心修改 1: 强制隐藏黑窗口 (安全版) ---
# 这段代码会检测是否在 Windows 下运行，尝试隐藏控制台
# 并且加了防崩溃处理，不会影响在线打包
try:
    if sys.platform == "win32":
        import ctypes
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
except:
    pass
# ------------------------------------------

class GameListGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏列表生成工具 (自定义输出版)")
        self.root.geometry("750x650")
        
        # --- 顶部区域 ---
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill=tk.X, padx=15)
        
        # 1. 游戏根目录选择
        tk.Label(top_frame, text="1. 游戏根目录 (扫描哪里):").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_in = tk.Entry(top_frame, width=55)
        self.entry_in.grid(row=0, column=1, padx=5)
        tk.Button(top_frame, text="浏览...", command=self.browse_input).grid(row=0, column=2)
        
        # 2. 输出目录选择 (新增功能)
        tk.Label(top_frame, text="2. 列表保存到 (输出哪里):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_out = tk.Entry(top_frame, width=55)
        self.entry_out.grid(row=1, column=1, padx=5)
        tk.Button(top_frame, text="浏览...", command=self.browse_output).grid(row=1, column=2)
        
        # 3. 起始编号
        tk.Label(top_frame, text="3. 起始编号 (默认1):").grid(row=2, column=0, sticky="w", pady=5)
        self.entry_num = tk.Entry(top_frame, width=10)
        self.entry_num.insert(0, "1")
        self.entry_num.grid(row=2, column=1, sticky="w", padx=5)
        
        # --- 运行按钮 ---
        self.btn_run = tk.Button(root, text="开始生成列表", bg="#0078D7", fg="white", 
                                 font=("微软雅黑", 12, "bold"), height=2, command=self.start_thread)
        self.btn_run.pack(fill=tk.X, padx=30, pady=15)
        
        # --- 日志区域 ---
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=20)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.log("就绪。请选择游戏目录和输出目录。")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def browse_input(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_in.delete(0, tk.END)
            self.entry_in.insert(0, path)
            
            # 为了方便，默认输出目录 = 输入目录
            # 如果用户想改，可以再点下面的浏览
            if not self.entry_out.get():
                self.entry_out.delete(0, tk.END)
                self.entry_out.insert(0, path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_out.delete(0, tk.END)
            self.entry_out.insert(0, path)

    def start_thread(self):
        target_dir = self.entry_in.get()
        output_dir = self.entry_out.get()
        
        if not os.path.isdir(target_dir):
            messagebox.showerror("错误", "请选择有效的【游戏根目录】！")
            return
        if not os.path.isdir(output_dir):
            messagebox.showerror("错误", "请选择有效的【输出目录】！")
            return
            
        try:
            start_num = int(self.entry_num.get())
            if start_num < 0: raise ValueError
        except:
            messagebox.showerror("错误", "起始编号必须是正整数！")
            return

        self.btn_run.config(state='disabled', text="正在生成中...")
        threading.Thread(target=self.run_process, args=(target_dir, output_dir, start_num)).start()

    def run_process(self, target_dir, output_dir, start_num):
        self.log("-" * 40)
        self.log(f"扫描目录: {target_dir}")
        self.log(f"输出位置: {output_dir}")
        
        # --- 配置 (保持原版逻辑) ---
        excluded_folders = {
            '__pycache__', '.git', '.vscode', 'venv', 'env',
            'node_modules', '.idea', '.vs', 'build', 'dist',
            'bin', 'obj', 'logs', 'temp', 'tmp', '_internal'
        }
        
        excluded_extensions = {
            '.py', '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe',
            '.bat', '.sh', '.cmd', '.ps1', '.db', '.sqlite',
            '.log', '.ini', '.cfg', '.config', '.json', '.xml',
            '.yml', '.yaml', '.md', '.txt', '.rtf',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.odt', '.ods', '.odp', '.epub', '.mobi', '.azw', '.azw3',
            '.pages', '.numbers', '.key', '.vsd', '.vsdx',
            '.c', '.cpp', '.h', '.hpp', '.java', '.class', '.js', '.ts',
            '.css', '.html', '.htm', '.php', '.asp', '.aspx', '.jsp',
            '.cs', '.vb', '.swift', '.kt', '.go', '.rs', '.rb', '.pl',
            '.pyw', '.pyi', '.pyx', '.pyd',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
            '.dmg', '.deb', '.rpm', '.msi', 
            '.lnk', '.url', '.torrent', '.crdownload', '.part',
            '.tmp', '.temp', '.cache', '.bak', '.backup'
        }
        
        image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
            '.webp', '.svg', '.ico', '.heic', '.jfif', '.pjpeg', '.pjp',
            '.apng', '.avif', '.cur', '.tif', '.raw', '.cr2', '.nef', 
            '.orf', '.sr2', '.psd', '.ai', '.eps', '.indd', '.sketch', '.xd', '.fig'
        }

        # --- 扫描文件夹 ---
        try:
            all_items = os.listdir(target_dir)
            folders = []
            
            for item in all_items:
                item_path = os.path.join(target_dir, item)
                if os.path.isdir(item_path):
                    if item.lower() in [f.lower() for f in excluded_folders]: continue
                    if item.startswith('.'): continue
                    folders.append(item)
        except Exception as e:
            self.log(f"错误: 无法访问目录 - {e}")
            self.btn_run.config(state='normal', text="开始生成列表")
            return

        if not folders:
            self.log("未找到符合条件的文件夹。")
            self.btn_run.config(state='normal', text="开始生成列表")
            return

        self.log(f"找到 {len(folders)} 个文件夹")
        folders.sort()

        # --- 输出文件 (使用用户指定的 output_dir) ---
        output_file_path = os.path.join(output_dir, "游戏列表.txt")
        
        current_num = start_num
        total_files = 0
        processed_folders = 0

        try:
            with open(output_file_path, 'w', encoding='utf-8') as out_f:
                for folder_name in folders:
                    folder_path = os.path.join(target_dir, folder_name)
                    
                    try:
                        all_items = os.listdir(folder_path)
                        files_to_process = []
                        
                        for item in all_items:
                            item_path = os.path.join(folder_path, item)
                            if os.path.isfile(item_path):
                                _, ext = os.path.splitext(item)
                                ext_lower = ext.lower()
                                item_lower = item.lower()

                                if ext_lower in image_extensions: continue
                                if ext_lower in excluded_extensions: continue
                                if (item_lower.startswith('thumbs.db') or 
                                    item_lower.startswith('.') or 
                                    item_lower == 'desktop.ini' or 
                                    item_lower.startswith('~$')): continue
                                
                                # 二进制检测
                                try:
                                    if ext_lower == '':
                                        with open(item_path, 'rb') as f:
                                            content = f.read(1024)
                                        text_chars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
                                        if not content: continue
                                        if bool(content.translate(None, text_chars)): pass 
                                        else: continue 
                                except: pass
                                
                                files_to_process.append(item)

                        if not files_to_process:
                            self.log(f"[跳过] {folder_name} (空)")
                            continue

                        # 排序逻辑
                        def sort_key(filename):
                            filename_lower = filename.lower()
                            priority_order = {'.xci': 0, '.nsp': 1, '.pkg': 2, '.iso': 3, '.img': 4}
                            for ext, priority in priority_order.items():
                                if filename_lower.endswith(ext): return (priority, filename_lower)
                            return (999, filename_lower)
                        
                        files_to_process.sort(key=sort_key)

                        # 写入
                        for filename in files_to_process:
                            sort_str = f"{current_num:03d}"
                            out_f.write(f"game: {folder_name}\n")
                            out_f.write(f"file: {filename}\n")
                            out_f.write(f"sort-by: {sort_str}\n")
                            out_f.write(f"developer: {folder_name}\n")
                            out_f.write(f"description: 暂无信息。\n\n")
                            
                            current_num += 1
                            total_files += 1
                        
                        processed_folders += 1
                        self.log(f"[处理] {folder_name}")

                    except Exception as e:
                        self.log(f"[错误] {folder_name}: {e}")

            self.log("-" * 40)
            self.log(f"成功！文件已保存到: {output_file_path}")
            messagebox.showinfo("成功", f"列表生成完成！\n文件路径:\n{output_file_path}")

        except Exception as e:
            self.log(f"文件写入失败: {e}")
            messagebox.showerror("错误", str(e))

        self.btn_run.config(state='normal', text="开始生成列表")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameListGeneratorApp(root)
    root.mainloop()