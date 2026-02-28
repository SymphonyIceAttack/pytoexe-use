# main.py - Dynamic Folder Comparator
import os
import sys
import zlib
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
import threading
import queue

class DynamicFolderComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("动态文件夹比较删除工具")
        
        # 设置窗口大小和位置
        window_width = 1000
        window_height = 750
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置图标（如果有）
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 变量
        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()
        self.fast_mode = tk.BooleanVar(value=True)
        self.delete_mode = tk.StringVar(value="dynamic")
        self.backup_mode = tk.BooleanVar(value=True)
        
        # 状态变量
        self.is_comparing = False
        self.stop_requested = False
        
        # 队列
        self.message_queue = queue.Queue()
        
        # 创建界面
        self.setup_ui()
        
        # 启动消息队列处理器
        self.process_messages()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="⚡ 动态文件夹比较删除工具", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 文件夹选择
        self.create_folder_section(main_frame)
        
        # 选项
        self.create_options_section(main_frame)
        
        # 控制按钮
        self.create_control_section(main_frame)
        
        # 进度条
        self.create_progress_section(main_frame)
        
        # 日志显示
        self.create_log_section(main_frame)
        
        # 统计信息
        self.create_stats_section(main_frame)
        
    def create_folder_section(self, parent):
        """创建文件夹选择部分"""
        # 文件夹1
        folder1_frame = ttk.LabelFrame(parent, text="文件夹 1 (源文件夹)", padding="10")
        folder1_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder1_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder1_frame, text="路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        folder1_entry = ttk.Entry(folder1_frame, textvariable=self.folder1_path)
        folder1_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder1_frame, text="浏览...", 
                  command=lambda: self.browse_folder(self.folder1_path)) \
                  .grid(row=0, column=2)
        
        # 文件夹2
        folder2_frame = ttk.LabelFrame(parent, text="文件夹 2 (目标文件夹 - 将从这里删除)", padding="10")
        folder2_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder2_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder2_frame, text="路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        folder2_entry = ttk.Entry(folder2_frame, textvariable=self.folder2_path)
        folder2_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder2_frame, text="浏览...", 
                  command=lambda: self.browse_folder(self.folder2_path)) \
                  .grid(row=0, column=2)
        
    def create_options_section(self, parent):
        """创建选项部分"""
        options_frame = ttk.LabelFrame(parent, text="选项设置", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 删除时机
        ttk.Label(options_frame, text="删除时机:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        ttk.Radiobutton(options_frame, text="动态删除(边比较边删除)", 
                       variable=self.delete_mode, value="dynamic").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="比较后删除", 
                       variable=self.delete_mode, value="after").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        
        # 比较模式
        ttk.Label(options_frame, text="比较模式:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        ttk.Radiobutton(options_frame, text="快速模式(CRC32)", 
                       variable=self.fast_mode, value=True).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        ttk.Radiobutton(options_frame, text="完整模式(MD5)", 
                       variable=self.fast_mode, value=False).grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        
        # 备份选项
        ttk.Label(options_frame, text="安全选项:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.backup_check = ttk.Checkbutton(options_frame, text="创建备份(推荐)", 
                                           variable=self.backup_mode)
        self.backup_check.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))
        
    def create_control_section(self, parent):
        """创建控制按钮部分"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.start_btn = ttk.Button(button_frame, text="开始比较", 
                                   command=self.start_comparison,
                                   width=15)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="停止", 
                                  command=self.stop_process,
                                  state=tk.DISABLED,
                                  width=15)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="清空日志", 
                                   command=self.clear_log,
                                   width=15)
        self.clear_btn.pack(side=tk.LEFT)
        
    def create_progress_section(self, parent):
        """创建进度部分"""
        progress_frame = ttk.Frame(parent)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           variable=self.progress_var,
                                           maximum=100,
                                           mode='determinate')
        self.progress_bar.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.pack()
        
        self.file_progress_label = ttk.Label(progress_frame, text="")
        self.file_progress_label.pack()
        
    def create_log_section(self, parent):
        """创建日志显示部分"""
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        parent.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_stats_section(self, parent):
        """创建统计信息部分"""
        stats_frame = ttk.LabelFrame(parent, text="实时统计", padding="10")
        stats_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_labels = {
            'scanned1': ttk.Label(stats_frame, text="已扫描(文件夹1): 0"),
            'scanned2': ttk.Label(stats_frame, text="已扫描(文件夹2): 0"),
            'identical': ttk.Label(stats_frame, text="发现相同文件: 0"),
            'deleted': ttk.Label(stats_frame, text="已删除文件: 0"),
            'saved': ttk.Label(stats_frame, text="节省空间: 0 B")
        }
        
        for i, (key, label) in enumerate(self.stats_labels.items()):
            row = i // 3
            col = i % 3
            label.grid(row=row, column=col, padx=(0, 20), pady=(2, 2), sticky=tk.W)
        
    def browse_folder(self, path_var):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            path_var.set(folder)
            
    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = {"ERROR": "red", "WARNING": "orange", "SUCCESS": "green", "INFO": "black"}.get(level, "black")
        self.message_queue.put(("LOG", (f"[{timestamp}] {message}\n", color)))
        
    def update_status(self, message):
        """更新状态栏"""
        self.message_queue.put(("STATUS", message))
        
    def update_progress(self, value):
        """更新进度条"""
        self.message_queue.put(("PROGRESS", value))
        
    def update_file_progress(self, current, total, filename=""):
        """更新文件处理进度"""
        self.message_queue.put(("FILE_PROGRESS", (current, total, filename)))
        
    def update_stats(self, stats):
        """更新统计信息"""
        self.message_queue.put(("STATS", stats))
        
    def process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == "LOG":
                    message, color = data
                    self.log_text.insert(tk.END, message)
                    if color != "black":
                        start = self.log_text.index("end-1c linestart")
                        end = self.log_text.index("end-1c")
                        self.log_text.tag_add(color, start, end)
                        self.log_text.tag_config(color, foreground=color)
                    self.log_text.see(tk.END)
                    
                elif msg_type == "STATUS":
                    self.status_label.config(text=data)
                    
                elif msg_type == "PROGRESS":
                    self.progress_var.set(data)
                    
                elif msg_type == "FILE_PROGRESS":
                    current, total, filename = data
                    if total > 0:
                        percent = (current / total) * 100
                        self.file_progress_label.config(text=f"处理中: {current}/{total} ({percent:.1f}%)")
                    else:
                        self.file_progress_label.config(text="")
                        
                elif msg_type == "STATS":
                    for key, value in data.items():
                        if key in self.stats_labels:
                            text = f"{key}: {value}"
                            if key == 'saved' and isinstance(value, (int, float)):
                                text = f"节省空间: {self.format_size(value)}"
                            self.stats_labels[key].config(text=text)
                            
        except queue.Empty:
            pass
            
        self.root.after(50, self.process_messages)
        
    def calculate_crc32(self, file_path):
        """计算文件的CRC32值"""
        try:
            crc_value = 0
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    crc_value = zlib.crc32(data, crc_value)
            return crc_value & 0xFFFFFFFF
        except:
            return None
            
    def calculate_md5(self, file_path):
        """计算文件的MD5值"""
        import hashlib
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
            
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
        
    def delete_file(self, file_path, rel_path, file_size, backup_dir=None):
        """删除文件（支持备份）"""
        try:
            if self.backup_mode.get() and backup_dir:
                backup_path = os.path.join(backup_dir, rel_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.move(file_path, backup_path)
                self.log_message(f"已备份并删除: {rel_path}", "SUCCESS")
                return True, backup_path
            else:
                os.remove(file_path)
                self.log_message(f"已删除: {rel_path}", "SUCCESS")
                return True, None
        except Exception as e:
            self.log_message(f"删除失败 {rel_path}: {str(e)}", "ERROR")
            return False, None
            
    def start_comparison(self):
        """开始比较文件夹"""
        folder1 = self.folder1_path.get()
        folder2 = self.folder2_path.get()
        
        if not folder1 or not folder2:
            messagebox.showerror("错误", "请选择两个文件夹")
            return
            
        if not os.path.exists(folder1) or not os.path.exists(folder2):
            messagebox.showerror("错误", "文件夹不存在")
            return
        
        # 确认对话框
        if self.backup_mode.get():
            confirm_msg = f"确定要开始吗？\n\n文件夹1: {folder1}\n文件夹2: {folder2}\n\n相同文件将被备份后删除。"
        else:
            confirm_msg = f"⚠️ 警告：直接删除模式！\n\n文件夹1: {folder1}\n文件夹2: {folder2}\n\n相同文件将被永久删除！"
        
        if not messagebox.askyesno("确认", confirm_msg):
            return
        
        self.stop_requested = False
        self.is_comparing = True
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log_text.delete(1.0, tk.END)
        self.update_progress(0)
        
        thread = threading.Thread(target=self.do_comparison, args=(folder1, folder2), daemon=True)
        thread.start()
        
    def do_comparison(self, folder1, folder2):
        """执行比较操作"""
        try:
            self.log_message("=" * 60)
            self.log_message("开始动态比较删除...")
            
            # 创建备份目录
            backup_dir = None
            if self.backup_mode.get():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(folder2, f"_backup_{timestamp}")
                os.makedirs(backup_dir, exist_ok=True)
                self.log_message(f"备份目录: {backup_dir}")
            
            stats = {'scanned1': 0, 'scanned2': 0, 'identical': 0, 'deleted': 0, 'saved': 0}
            
            # 扫描文件夹1
            self.log_message("扫描文件夹1...")
            folder1_files = {}
            all_files1 = []
            
            for root, dirs, files in os.walk(folder1):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, folder1)
                    all_files1.append((rel_path, file_path))
            
            total_files1 = len(all_files1)
            
            for i, (rel_path, file_path) in enumerate(all_files1, 1):
                if self.stop_requested:
                    return
                    
                try:
                    file_size = os.path.getsize(file_path)
                    
                    if self.fast_mode.get():
                        folder1_files[rel_path] = {'size': file_size, 'path': file_path, 'hash': None}
                    else:
                        file_hash = self.calculate_md5(file_path)
                        if file_hash:
                            folder1_files[rel_path] = {'size': file_size, 'path': file_path, 'hash': file_hash}
                    
                    stats['scanned1'] = i
                    self.update_stats(stats)
                    self.update_progress((i / total_files1) * 50)
                    
                except Exception as e:
                    self.log_message(f"扫描失败: {file_path}", "WARNING")
            
            # 扫描文件夹2并比较
            self.log_message("扫描文件夹2并比较...")
            all_files2 = []
            
            for root, dirs, files in os.walk(folder2):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, folder2)
                    all_files2.append((rel_path, file_path))
            
            total_files2 = len(all_files2)
            
            for i, (rel_path, file_path) in enumerate(all_files2, 1):
                if self.stop_requested:
                    return
                    
                try:
                    file_size = os.path.getsize(file_path)
                    stats['scanned2'] = i
                    
                    progress = 50 + (i / total_files2) * 50
                    self.update_progress(progress)
                    self.update_file_progress(i, total_files2, rel_path)
                    self.update_stats(stats)
                    
                    if rel_path in folder1_files:
                        folder1_info = folder1_files[rel_path]
                        
                        if folder1_info['size'] == file_size:
                            if self.fast_mode.get():
                                if folder1_info['hash'] is None:
                                    folder1_info['hash'] = self.calculate_crc32(folder1_info['path'])
                                current_hash = self.calculate_crc32(file_path)
                            else:
                                current_hash = self.calculate_md5(file_path)
                            
                            if folder1_info['hash'] is not None and current_hash is not None:
                                if folder1_info['hash'] == current_hash:
                                    success, _ = self.delete_file(file_path, rel_path, file_size, backup_dir)
                                    
                                    if success:
                                        stats['identical'] += 1
                                        stats['deleted'] += 1
                                        stats['saved'] += file_size
                                        self.update_stats(stats)
                    
                except Exception as e:
                    self.log_message(f"处理失败: {file_path}", "WARNING")
            
            self.root.after(0, self.on_comparison_complete, stats)
            
        except Exception as e:
            self.root.after(0, self.on_comparison_error, str(e))
        finally:
            self.root.after(0, self.enable_buttons)
    
    def on_comparison_complete(self, stats):
        """比较完成后的处理"""
        self.is_comparing = False
        self.update_progress(100)
        self.update_status("完成")
        
        self.log_message("=" * 60)
        self.log_message(f"完成！删除文件: {stats['deleted']}, 节省空间: {self.format_size(stats['saved'])}", "SUCCESS")
        
        messagebox.showinfo("完成", 
            f"操作完成！\n\n"
            f"扫描文件1: {stats['scanned1']}\n"
            f"扫描文件2: {stats['scanned2']}\n"
            f"发现相同: {stats['identical']}\n"
            f"成功删除: {stats['deleted']}\n"
            f"节省空间: {self.format_size(stats['saved'])}")
    
    def on_comparison_error(self, error_msg):
        """比较错误处理"""
        self.is_comparing = False
        self.update_status("错误")
        self.log_message(f"错误: {error_msg}", "ERROR")
        messagebox.showerror("错误", f"操作失败:\n{error_msg}")
    
    def enable_buttons(self):
        """启用按钮"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("就绪")
    
    def stop_process(self):
        """停止当前操作"""
        self.stop_requested = True
        self.log_message("正在停止...", "WARNING")
        self.update_status("正在停止...")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = DynamicFolderComparator(root)
    root.mainloop()

if __name__ == "__main__":
    main()