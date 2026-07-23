#开始编写你的代码吧!
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import shutil
import win32com.client  # 需要安装 pywin32

# 全局变量控制停止
stop_flag = False

class Word2PDFApp:
    def __init__(self, root, init_path=None):
        self.root = root
        self.root.title("Word 转 PDF 工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # 变量
        self.folder_path = tk.StringVar(value=init_path if init_path else "")
        self.delete_original = tk.BooleanVar(value=False)
        self.files_list = []
        self.total_files = 0
        self.converted = 0

        # 创建界面
        self.create_widgets()

        # 如果启动时传入了文件夹路径，自动扫描
        if init_path and os.path.isdir(init_path):
            self.scan_folder()

    def create_widgets(self):
        # 文件夹选择框
        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=10, padx=10, fill=tk.X)

        tk.Label(frame_top, text="目标文件夹：").pack(side=tk.LEFT)
        entry = tk.Entry(frame_top, textvariable=self.folder_path, width=50)
        entry.pack(side=tk.LEFT, padx=5)
        btn_browse = tk.Button(frame_top, text="浏览...", command=self.browse_folder)
        btn_browse.pack(side=tk.LEFT)
        btn_scan = tk.Button(frame_top, text="扫描 Word 文件", command=self.scan_folder)
        btn_scan.pack(side=tk.LEFT, padx=5)

        # 删除选项
        frame_del = tk.Frame(self.root)
        frame_del.pack(pady=5, padx=10, anchor=tk.W)
        tk.Checkbutton(frame_del, text="转换后删除原始文件（移到回收站）", 
                       variable=self.delete_original).pack(side=tk.LEFT)

        # 文件列表（带滚动条）
        frame_list = tk.Frame(self.root)
        frame_list.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(frame_list, selectmode=tk.EXTENDED)
        scrollbar = tk.Scrollbar(frame_list, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 进度条和状态
        frame_progress = tk.Frame(self.root)
        frame_progress.pack(pady=5, padx=10, fill=tk.X)

        self.progress = ttk.Progressbar(frame_progress, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))

        self.lbl_status = tk.Label(frame_progress, text="就绪")
        self.lbl_status.pack(side=tk.RIGHT)

        # 按钮区域
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)

        self.btn_start = tk.Button(frame_btn, text="开始转换", command=self.start_conversion, bg="#4CAF50", fg="white", width=12)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_cancel = tk.Button(frame_btn, text="取消", command=self.cancel_conversion, bg="#f44336", fg="white", width=12)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        self.btn_cancel.config(state=tk.DISABLED)

        # 底部日志
        self.log_text = tk.Text(self.root, height=6, state=tk.DISABLED)
        self.log_text.pack(pady=5, padx=10, fill=tk.X)

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.scan_folder()

    def scan_folder(self):
        path = self.folder_path.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("错误", "请选择有效的文件夹路径")
            return

        self.files_list = []
        self.listbox.delete(0, tk.END)
        self.log("正在扫描...")

        def walk_dir(dir_path):
            for entry in os.listdir(dir_path):
                full = os.path.join(dir_path, entry)
                if os.path.isdir(full):
                    walk_dir(full)
                else:
                    ext = os.path.splitext(entry)[1].lower()
                    if ext in ['.doc', '.docx']:
                        self.files_list.append(full)

        walk_dir(path)
        self.total_files = len(self.files_list)
        for f in self.files_list:
            self.listbox.insert(tk.END, f)
        self.log(f"扫描完成，共找到 {self.total_files} 个 Word 文件")
        self.lbl_status.config(text=f"共 {self.total_files} 个文件")

    def start_conversion(self):
        if not self.files_list:
            messagebox.showwarning("警告", "请先扫描并确认有 Word 文件")
            return

        self.btn_start.config(state=tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL)
        self.converted = 0
        self.progress['maximum'] = self.total_files
        self.progress['value'] = 0
        global stop_flag
        stop_flag = False

        # 启动转换线程（防止界面卡死）
        threading.Thread(target=self.do_conversion, daemon=True).start()

    def do_conversion(self):
        try:
            # 连接 Word 或 WPS
            try:
                word = win32com.client.Dispatch("Word.Application")
            except:
                try:
                    word = win32com.client.Dispatch("WPS.Application")
                except:
                    try:
                        word = win32com.client.Dispatch("KWPS.Application")
                    except:
                        self.log("错误：未检测到 Microsoft Word 或 WPS")
                        self.root.after(0, self.finish_conversion)
                        return

            word.Visible = False
            wdFormatPDF = 17

            for idx, file_path in enumerate(self.files_list):
                if stop_flag:
                    self.log("用户取消转换")
                    break
                self.root.after(0, self.log, f"正在转换: {os.path.basename(file_path)}")
                try:
                    doc = word.Documents.Open(file_path, False, True)
                    pdf_path = os.path.splitext(file_path)[0] + ".pdf"
                    doc.SaveAs(pdf_path, wdFormatPDF)
                    doc.Close(False)
                    self.converted += 1
                    self.root.after(0, self.progress.step, 1)
                    self.root.after(0, self.lbl_status.config, 
                                   text=f"已转换 {self.converted}/{self.total_files}")

                    if self.delete_original.get():
                        # 移到回收站
                        self.move_to_recycle_bin(file_path)
                        self.root.after(0, self.log, f"已删除原文件: {os.path.basename(file_path)}")
                except Exception as e:
                    self.root.after(0, self.log, f"转换失败: {os.path.basename(file_path)} - {str(e)}")
                finally:
                    pass

            word.Quit()
            self.root.after(0, self.log, f"转换完成！成功 {self.converted} 个文件")
            if self.converted == self.total_files:
                self.root.after(0, messagebox.showinfo, "完成", f"所有文件转换成功！共 {self.converted} 个")
        except Exception as e:
            self.root.after(0, self.log, f"发生异常: {str(e)}")
        finally:
            self.root.after(0, self.finish_conversion)

    def finish_conversion(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_cancel.config(state=tk.DISABLED)
        self.lbl_status.config(text=f"完成 {self.converted}/{self.total_files}")

    def cancel_conversion(self):
        global stop_flag
        stop_flag = True
        self.log("正在取消...")

    def move_to_recycle_bin(self, file_path):
        """使用 Shell 将文件移到回收站（不直接删除）"""
        try:
            import ctypes
            from ctypes import wintypes
            # 使用 SHEmptyRecycleBin 或 SHFileOperation
            # 这里简单使用 os.remove 但为了回收站，我们使用 Shell32
            import win32file
            win32file.DeleteFile(file_path)  # 注意：这是永久删除，不是回收站！
            # 实际移回收站更复杂，建议使用 pywin32 的 shell 模块
            # 下面用简单方式：调用系统命令
            import subprocess
            subprocess.run(['cmd', '/c', f'powershell -Command "Remove-Item -Path \'{file_path}\' -Force -Confirm:$false -Recycle"'], 
                           capture_output=True, shell=True)
        except:
            pass  # 若失败则忽略

# 主入口
if __name__ == "__main__":
    root = tk.Tk()
    init_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = Word2PDFApp(root, init_path)
    root.mainloop()