# -*- coding: utf-8 -*-
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

class GameListGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏列表生成工具 (GUI版)")
        self.root.geometry("750x600")
        
        # --- 1. 顶部选择区域 ---
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        
        # 目录选择
        tk.Label(top_frame, text="游戏根目录:").grid(row=0, column=0, sticky="w")
        self.entry_path = tk.Entry(top_frame, width=50)
        self.entry_path.grid(row=0, column=1, padx=5)
        tk.Button(top_frame, text="浏览文件夹", command=self.browse_folder).grid(row=0, column=2)
        
        # 起始编号
        tk.Label(top_frame, text="起始编号 (默认1):").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_num = tk.Entry(top_frame, width=10)
        self.entry_num.insert(0, "1")
        self.entry_num.grid(row=1, column=1, sticky="w", padx=5)
        
        # --- 2. 运行按钮 ---
        self.btn_run = tk.Button(root, text="开始生成列表", bg="#0078D7", fg="white", 
                                 font=("微软雅黑", 12, "bold"), height=2, command=self.start_thread)
        self.btn_run.pack(fill=tk.X, padx=20, pady=10)
        
        # --- 3. 日志区域 ---
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=20)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log("工具已就绪。请选择包含游戏子文件夹的根目录。")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, path)

    def start_thread(self):
        target_dir = self.entry_path.get()
        if not os.path.isdir(target_dir):
            messagebox.showerror("错误", "请先选择有效的文件夹路径！")
            return
            
        try:
            start_num = int(self.entry_num.get())
            if start_num < 0: raise ValueError
        except:
            messagebox.showerror("错误", "起始编号必须是正整数！")
            return

        self.btn_run.config(state='disabled', text="正在生成中...")
        threading.Thread(target=self.run_process, args=(target_dir, start_num)).start()

    def run_process(self, target_dir, start_num):
        self.log("-" * 40)
        self.log(f"开始扫描目录: {target_dir}")
        
        # --- 原有配置逻辑 (保持不变) ---
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

        self.log(f"找到 {len(folders)} 个游戏文件夹")
        folders.sort() # 按名称排序

        # --- 输出文件路径 ---
        output_file = os.path.join(target_dir, "游戏列表.txt")
        
        current_num = start_num
        total_files = 0
        processed_folders = 0

        try:
            with open(output_file, 'w', encoding='utf-8') as out_f:
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
                                
                                # 二进制/文本检测逻辑 (保留原版)
                                try:
                                    if ext_lower == '':
                                        with open(item_path, 'rb') as f:
                                            content = f.read(1024)
                                        text_chars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
                                        if not content: continue
                                        if bool(content.translate(None, text_chars)): pass # 是二进制，保留
                                        else: continue # 是文本，跳过
                                except: pass
                                
                                files_to_process.append(item)

                        if not files_to_process:
                            self.log(f"[跳过] {folder_name} (无游戏文件)")
                            continue

                        # 排序逻辑 (保留原版优先级)
                        def sort_key(filename):
                            filename_lower = filename.lower()
                            priority_order = {'.xci': 0, '.nsp': 1, '.pkg': 2, '.iso': 3, '.img': 4}
                            for ext, priority in priority_order.items():
                                if filename_lower.endswith(ext): return (priority, filename_lower)
                            return (999, filename_lower)
                        
                        files_to_process.sort(key=sort_key)

                        # 写入文件
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
                        self.log(f"[处理] {folder_name} -> 找到 {len(files_to_process)} 个文件")

                    except Exception as e:
                        self.log(f"[错误] 处理文件夹 {folder_name} 失败: {e}")

            self.log("-" * 40)
            self.log("处理完成！")
            self.log(f"生成文件: {output_file}")
            self.log(f"共处理: {total_files} 个文件")
            messagebox.showinfo("成功", f"列表生成完成！\n文件已保存在:\n{output_file}")

        except Exception as e:
            self.log(f"写入文件失败: {e}")
            messagebox.showerror("错误", str(e))

        self.btn_run.config(state='normal', text="开始生成列表")

if __name__ == "__main__":
    root = tk.Tk()
    app = GameListGeneratorApp(root)
    root.mainloop()