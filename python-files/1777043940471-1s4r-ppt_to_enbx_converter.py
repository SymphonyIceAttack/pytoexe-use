#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPTX转ENBX批量转换器
功能：遍历指定文件夹及其子文件夹，将所有.pptx文件转换为希沃白板.enbx文件
输出：在原目录下创建ENBX文件夹，保留原文件夹结构
要求：Windows系统，已安装希沃白板5，已安装pywin32库
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import win32com.client
import time
import threading

class PPTToENBXConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("PPTX转ENBX批量转换器")
        self.root.geometry("600x400")
        
        # 初始化变量
        self.folder_path = tk.StringVar()
        self.is_running = False
        
        # 创建UI
        self._create_widgets()
        
        # 初始化希沃COM对象
        self.seewo_app = None
        self._init_seewo_app()
        
    def _init_seewo_app(self):
        """初始化希沃白板COM对象"""
        try:
            self.seewo_app = win32com.client.Dispatch("SeewoWhiteboard.Application")
            self.log("✅ 成功初始化希沃白板应用")
        except Exception as e:
            self.log(f"❌ 初始化希沃白板失败: {str(e)}")
            self.log("💡 请确保已安装希沃白板5，并且是Windows系统")
        
    def _create_widgets(self):
        """创建界面控件"""
        # 文件夹选择
        frame_folder = tk.Frame(self.root, padx=10, pady=10)
        frame_folder.pack(fill=tk.X)
        
        tk.Label(frame_folder, text="目标文件夹:").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(frame_folder, textvariable=self.folder_path, width=50).grid(row=0, column=1, padx=5)
        tk.Button(frame_folder, text="浏览", command=self._select_folder).grid(row=0, column=2)
        
        # 开始按钮
        frame_btn = tk.Frame(self.root, padx=10, pady=5)
        frame_btn.pack(fill=tk.X)
        
        self.start_btn = tk.Button(frame_btn, text="开始转换", command=self._start_conversion, bg="#4CAF50", fg="white", padx=20)
        self.start_btn.pack()
        
        # 日志区域
        frame_log = tk.Frame(self.root, padx=10, pady=10)
        frame_log.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame_log, text="处理日志:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(frame_log, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, msg):
        """添加日志"""
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def _select_folder(self):
        """选择目标文件夹"""
        folder = filedialog.askdirectory(title="选择要处理的根文件夹")
        if folder:
            self.folder_path.set(folder)
            
    def _start_conversion(self):
        """开始转换（后台线程）"""
        if self.is_running:
            messagebox.showwarning("提示", "转换正在进行中，请稍候...")
            return
            
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效的目标文件夹")
            return
            
        if not self.seewo_app:
            # 尝试重新初始化
            self._init_seewo_app()
            if not self.seewo_app:
                messagebox.showerror("错误", "希沃白板初始化失败，请检查是否已安装希沃白板5")
                return
        
        # 启动后台线程
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED, text="转换中...")
        thread = threading.Thread(target=self._convert_thread, args=(folder,))
        thread.daemon = True
        thread.start()
        
    def _convert_thread(self, root_dir):
        """转换处理线程"""
        try:
            self.log(f"🚀 开始处理文件夹: {root_dir}")
            
            # 输出根目录
            output_root = os.path.join(root_dir, "ENBX")
            self.log(f"📂 输出目录: {output_root}")
            
            # 统计
            total_files = 0
            success_count = 0
            fail_count = 0
            
            # 遍历所有文件
            for dirpath, dirnames, filenames in os.walk(root_dir):
                # 跳过输出目录，避免重复处理
                if os.path.basename(dirpath) == "ENBX":
                    continue
                    
                for filename in filenames:
                    if filename.lower().endswith(".pptx"):
                        total_files += 1
                        input_path = os.path.join(dirpath, filename)
                        
                        # 计算相对路径，用于重建目录结构
                        rel_path = os.path.relpath(input_path, root_dir)
                        # 新的文件名，替换后缀
                        new_filename = os.path.splitext(rel_path)[0] + ".enbx"
                        output_path = os.path.join(output_root, new_filename)
                        
                        # 创建输出目录
                        output_dir = os.path.dirname(output_path)
                        os.makedirs(output_dir, exist_ok=True)
                        
                        self.log(f"🔄 正在转换: {rel_path}")
                        
                        try:
                            # 调用希沃进行转换
                            # 打开PPT文件，希沃会自动导入
                            doc = self.seewo_app.Open(input_path)
                            time.sleep(1)  # 等待导入完成
                            
                            # 保存为enbx
                            doc.SaveAs(output_path)
                            time.sleep(0.5)
                            
                            # 关闭文档
                            doc.Close()
                            
                            self.log(f"✅ 转换成功: {os.path.basename(new_filename)}")
                            success_count += 1
                            
                        except Exception as e:
                            self.log(f"❌ 转换失败: {rel_path}, 错误: {str(e)}")
                            fail_count += 1
                            # 尝试关闭可能打开的文档
                            try:
                                if 'doc' in locals():
                                    doc.Close()
                            except:
                                pass
                            
            # 完成
            self.log("\n" + "="*50)
            self.log(f"🎉 转换完成！总计: {total_files} 个文件")
            self.log(f"✅ 成功: {success_count} 个")
            self.log(f"❌ 失败: {fail_count} 个")
            self.log(f"📂 转换后的文件保存在: {output_root}")
            
            messagebox.showinfo("完成", f"转换完成！\n总计: {total_files} 个文件\n成功: {success_count} 个\n失败: {fail_count} 个\n\n文件已保存到: {output_root}")
            
        except Exception as e:
            self.log(f"💥 处理过程中发生错误: {str(e)}")
            messagebox.showerror("错误", f"处理失败: {str(e)}")
        finally:
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL, text="开始转换")
            
    def __del__(self):
        """析构函数，退出希沃应用"""
        if self.seewo_app:
            try:
                self.seewo_app.Quit()
            except:
                pass

if __name__ == "__main__":
    # 支持中文
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    root = tk.Tk()
    app = PPTToENBXConverter(root)
    root.mainloop()
    
    # 退出时关闭希沃
    del app
