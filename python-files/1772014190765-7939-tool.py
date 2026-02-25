# -*- coding: utf-8 -*-
import sys
import os
import ctypes # 引入系统级控制库

# --- 【核心修改】 ---
# 在程序最开始，强制切断与控制台黑窗口的连接
# 这比隐藏窗口更彻底，它会直接关闭那个黑框，只保留界面
if sys.platform == 'win32':
    try:
        # 1. 先把输出重定向到空设备，防止切断控制台后 print() 报错崩溃
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        # 2. 调用 Windows API 释放控制台
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass
# --------------------

import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading

# --- 配置区域 ---
# 定义图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}

# 定义要忽略的文件
IGNORE_EXTENSIONS = {'.exe', '.py', '.bat', '.sh', '.ini', '.db', '.txt', '.dll'}

class CoverExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏封面提取工具 (文件名精准匹配版)")
        self.root.geometry("700x550")
        
        # 1. 顶部选择区域
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(top_frame, text="游戏根目录:").pack(side=tk.LEFT)
        
        self.path_entry = tk.Entry(top_frame, width=50)
        self.path_entry.insert(0, os.getcwd()) # 默认是当前文件夹
        self.path_entry.pack(side=tk.LEFT, padx=5)
        
        btn_browse = tk.Button(top_frame, text="选择文件夹", command=self.browse_folder)
        btn_browse.pack(side=tk.LEFT)
        
        # 2. 核心操作按钮
        btn_frame = tk.Frame(root, pady=5)
        btn_frame.pack(fill=tk.X, padx=10)
        
        self.btn_start = tk.Button(btn_frame, text="开始扫描并提取", command=self.start_thread, 
                                   bg="#0078D7", fg="white", font=("微软雅黑", 12, "bold"), height=2)
        self.btn_start.pack(fill=tk.X)
        
        # 3. 日志显示区域
        self.log_text = scrolledtext.ScrolledText(root, state='disabled', height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log("程序已就绪。")
        self.log(f"支持的图片格式: {', '.join(IMAGE_EXTENSIONS)}")
        self.log("规则: 只有当图片名与同文件夹下的非图片文件名完全一致时，才会被提取。")

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_selected)

    def start_thread(self):
        # 使用多线程，防止界面卡死
        process_thread = threading.Thread(target=self.run_extraction)
        process_thread.start()

    def run_extraction(self):
        root_path = self.path_entry.get()
        if not os.path.exists(root_path):
            messagebox.showerror("错误", "文件夹路径不存在！")
            return

        self.btn_start.config(state='disabled', text="正在运行中...")
        
        # 创建输出文件夹
        output_dir = os.path.join(root_path, "_提取出的封面_Output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.log(f"创建输出目录: {output_dir}")
        
        total_extracted = 0
        
        self.log("-" * 30)
        self.log("开始扫描...")

        # 遍历所有子文件夹
        for current_root, dirs, files in os.walk(root_path):
            if "_提取出的封面_Output" in current_root:
                continue
            
            # --- 核心逻辑开始 ---
            image_files = {} 
            game_files = set()
            
            for f in files:
                name, ext = os.path.splitext(f)
                ext = ext.lower()
                
                if ext in IMAGE_EXTENSIONS:
                    image_files[name] = f
                elif ext not in IGNORE_EXTENSIONS:
                    game_files.add(name)
            
            for game_name in game_files:
                if game_name in image_files:
                    img_filename = image_files[game_name]
                    src_path = os.path.join(current_root, img_filename)
                    dst_path = os.path.join(output_dir, img_filename)
                    
                    if os.path.exists(dst_path):
                        parent_folder_name = os.path.basename(current_root)
                        base, extension = os.path.splitext(img_filename)
                        new_name = f"{base}_{parent_folder_name}{extension}"
                        dst_path = os.path.join(output_dir, new_name)
                    
                    try:
                        shutil.copy2(src_path, dst_path)
                        self.log(f"[提取] {img_filename} (来源: {os.path.basename(current_root)})")
                        total_extracted += 1
                    except Exception as e:
                        self.log(f"[错误] 复制失败: {e}")
            # --- 核心逻辑结束 ---

        self.log("-" * 30)
        self.log(f"全部完成！共提取 {total_extracted} 张图片。")
        messagebox.showinfo("完成", f"提取完成！\n请查看文件夹:\n{output_dir}")
        self.btn_start.config(state='normal', text="开始扫描并提取")

if __name__ == "__main__":
    root = tk.Tk()
    app = CoverExtractorApp(root)
    root.mainloop()