import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

TYPE_FOLDER = {
    "Word文档": [".doc", ".docx"],
    "PPT演示文稿": [".ppt", ".pptx"],
    "Excel表格": [".xls", ".xlsx", ".csv"],
    "文本文档": [".txt", ".md"],
    "PDF文档": [".pdf"],
    "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "图片": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "视频": [".mp4", ".avi", ".mov", ".mkv", ".flv"],
    "音频": [".mp3", ".wav", ".flac"],
    "程序脚本": [".exe", ".bat", ".py", ".js"],
}

class FileSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文档整理工具 - 文件自动分类移动")
        self.root.geometry("900x650")
        self.root.resizable(True, True)

        self.source_path = tk.StringVar()
        self.target_root = tk.StringVar()
        self.keyword = tk.StringVar()
        self.sort_mode = tk.StringVar(value="type")

        self.build_ui()

    def build_ui(self):
        frame_top = ttk.Frame(self.root, padding=10)
        frame_top.pack(fill=tk.X)

        ttk.Label(frame_top, text="源文件夹(待整理):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_top, textvariable=self.source_path, width=70).grid(row=0, column=1, padx=5)
        ttk.Button(frame_top, text="选择", command=self.select_source).grid(row=0, column=2)

        ttk.Label(frame_top, text="输出根目录:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame_top, textvariable=self.target_root, width=70).grid(row=1, column=1, padx=5)
        ttk.Button(frame_top, text="选择", command=self.select_target).grid(row=1, column=2)

        frame_mode = ttk.LabelFrame(self.root, text="分类模式选择", padding=10)
        frame_mode.pack(fill=tk.X, padx=10, pady=5)

        ttk.Radiobutton(frame_mode, text="按 文件类型 分类", variable=self.sort_mode, value="type").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(frame_mode, text="按 创建时间(年月) 分类", variable=self.sort_mode, value="time").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(frame_mode, text="按 关键词 分类", variable=self.sort_mode, value="keyword").pack(side=tk.LEFT, padx=15)

        frame_key = ttk.Frame(self.root, padding=10)
        frame_key.pack(fill=tk.X)
        ttk.Label(frame_key, text="关键词(多个用英文逗号分隔):").pack(side=tk.LEFT)
        ttk.Entry(frame_key, textvariable=self.keyword, width=50).pack(side=tk.LEFT, padx=5)

        frame_btn = ttk.Frame(self.root, padding=10)
        frame_btn.pack(fill=tk.X)
        ttk.Button(frame_btn, text="开始整理文件(剪切移动)", command=self.start_sort).pack()

        frame_log = ttk.LabelFrame(self.root, text="运行日志", padding=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(frame_log)
        scrollbar = ttk.Scrollbar(frame_log, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def select_source(self):
        path = filedialog.askdirectory(title="选择待整理文件夹")
        if path:
            self.source_path.set(path)

    def select_target(self):
        path = filedialog.askdirectory(title="选择输出根目录")
        if path:
            self.target_root.set(path)

    def get_file_category(self, ext):
        ext_low = ext.lower()
        for cat_name, ext_list in TYPE_FOLDER.items():
            if ext_low in ext_list:
                return cat_name
        return "其他文件"

    def get_create_time_folder(self, filepath):
        ctime = os.path.getctime(filepath)
        dt = datetime.fromtimestamp(ctime)
        return dt.strftime("%Y-%m")

    def move_file(self, src_file, dst_folder):
        os.makedirs(dst_folder, exist_ok=True)
        filename = os.path.basename(src_file)
        dst_path = os.path.join(dst_folder, filename)
        counter = 1
        while os.path.exists(dst_path):
            name, ext = os.path.splitext(filename)
            dst_path = os.path.join(dst_folder, f"{name}_{counter}{ext}")
            counter += 1
        shutil.move(src_file, dst_path)
        self.log(f"✅已移动: {filename} --> {dst_folder}")

    def start_sort(self):
        src_dir = self.source_path.get().strip()
        out_root = self.target_root.get().strip()
        mode = self.sort_mode.get()

        if not src_dir or not os.path.isdir(src_dir):
            messagebox.showerror("错误", "请选择有效的源文件夹！")
            return
        if not out_root:
            messagebox.showerror("错误", "请选择输出根目录！")
            return

        keyword_list = []
        if mode == "keyword":
            kw_text = self.keyword.get().strip()
            if not kw_text:
                messagebox.showerror("错误", "关键词模式下必须填写关键词！多个逗号隔开")
                return
            keyword_list = [k.strip().lower() for k in kw_text.split(",")]

        self.log("="*50)
        self.log(f"开始整理，模式:{mode}")

        for fname in os.listdir(src_dir):
            full_path = os.path.join(src_dir, fname)
            if os.path.isdir(full_path):
                continue
            _, ext = os.path.splitext(fname)

            target_subfolder = ""
            if mode == "type":
                target_subfolder = self.get_file_category(ext)
            elif mode == "time":
                target_subfolder = self.get_create_time_folder(full_path)
            elif mode == "keyword":
                fn_low = fname.lower()
                matched_kw = None
                for kw in keyword_list:
                    if kw in fn_low:
                        matched_kw = kw
                        break
                if matched_kw is None:
                    self.log(f"⏭跳过(无匹配关键词): {fname}")
                    continue
                target_subfolder = f"关键词_{matched_kw}"

            dst_folder = os.path.join(out_root, target_subfolder)
            self.move_file(full_path, dst_folder)

        self.log("\n🎉全部任务完成！")
        messagebox.showinfo("完成", "文件整理完毕！")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileSorterApp(root)
    root.mainloop()
