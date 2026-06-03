import sys
import os
import shutil
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pathlib import Path

class FileCopyTool:
    def __init__(self, root):
        self.root = root
        self.root.title("批量按后缀检索复制工具")
        self.root.geometry("730x530")

        # 源文件夹
        tk.Label(root, text="源查找根目录：").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.var_src = tk.StringVar()
        tk.Entry(root, textvariable=self.var_src, width=86).grid(row=0, column=1, padx=8)

        # 目标文件夹
        tk.Label(root, text="目标复制目录：").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        self.var_dst = tk.StringVar()
        tk.Entry(root, textvariable=self.var_dst, width=86).grid(row=1, column=1, padx=8)

        # 后缀输入
        tk.Label(root, text="文件后缀(英文逗号分隔，不区分大小写)：").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.var_ext = tk.StringVar(value="step,stp,igs,sldprt,sldasm,dwg,dxf")
        tk.Entry(root, textvariable=self.var_ext, width=86).grid(row=2, column=1, padx=8)

        # 按钮区域
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=8)
        tk.Button(btn_frame, text="开始检索并复制", command=self.run_task, bg="#2376dd", fg="white", width=15).pack(side="left", padx=12)
        tk.Button(btn_frame, text="清空日志", command=self.clear_log, width=10).pack(side="left")

        # 运行日志
        tk.Label(root, text="运行日志明细：").grid(row=4, column=0, sticky="nw", padx=8, pady=3)
        self.log_box = scrolledtext.ScrolledText(root, width=94, height=17)
        self.log_box.grid(row=5, column=0, columnspan=2, padx=8)

    def log_print(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_box.delete(1.0, tk.END)

    # 递归遍历全目录
    def scan_all_dir(self, source_path, target_exts):
        res_list = []
        if not os.path.isdir(source_path):
            return res_list
        for info in os.scandir(source_path):
            if info.is_dir(follow_symlinks=False):
                res_list += self.scan_all_dir(info.path, target_exts)
            else:
                file_suffix = Path(info.name).suffix.strip(".").lower()
                if file_suffix in target_exts:
                    res_list.append(info.path)
        return res_list

    def run_task(self):
        src_path = self.var_src.get().strip()
        dst_path = self.var_dst.get().strip()
        ext_text = self.var_ext.get().strip()
        if not all([src_path, dst_path, ext_text]):
            messagebox.showwarning("提醒", "源目录、目标目录、后缀均不能为空！")
            return
        # 统一小写后缀
        ext_list = [i.strip().lower() for i in ext_text.split(",") if i.strip()]
        self.clear_log()
        self.log_print(f"【源目录】{src_path}")
        self.log_print(f"【目标目录】{dst_path}")
        self.log_print(f"【筛选后缀】{','.join(ext_list)}")
        self.log_print("正在遍历所有子文件夹...")

        find_files = self.scan_all_dir(src_path, ext_list)
        total_count = len(find_files)
        self.log_print(f"\n检索完成，匹配文件总数：{total_count}")
        if total_count == 0:
            self.log_print("无符合条件文件，任务结束")
            return

        os.makedirs(dst_path, exist_ok=True)
        success = 0
        fail = 0
        for full_file in find_files:
            fname = os.path.basename(full_file)
            save_full = os.path.join(dst_path, fname)
            try:
                shutil.copy2(full_file, save_full)
                self.log_print(f"✅复制成功：{fname}")
                success += 1
            except Exception as err:
                self.log_print(f"❌复制失败：{fname} → {str(err)}")
                fail += 1
        self.log_print(f"\n========统计汇总========")
        self.log_print(f"总计：{total_count} | 成功：{success} | 失败：{fail}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileCopyTool(root)
    root.mainloop()