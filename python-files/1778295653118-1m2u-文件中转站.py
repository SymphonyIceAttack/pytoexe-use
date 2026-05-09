import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES  # 拖拽支持

# ===================== 配置项（可自行修改）=====================
STORAGE_FOLDER = "./文件中转站"  # 中转文件夹路径
# ===============================================================

# 创建中转文件夹（不存在则自动创建）
if not os.path.exists(STORAGE_FOLDER):
    os.makedirs(STORAGE_FOLDER)

class FileTransferStation(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("本地文件中转站")
        self.geometry("750x500")
        self.resizable(True, True)

        # 操作模式：copy / cut
        self.operation_mode = tk.StringVar(value="copy")

        # 顶部栏
        self.create_top_bar()

        # 文件列表
        self.create_file_list()

        # 加载现有文件
        self.refresh_file_list()

        # 绑定拖拽
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_files_drop)

    def create_top_bar(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(frame, text="📂 打开中转文件夹", command=self.open_storage_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="🔄 刷新列表", command=self.refresh_file_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="🗑 清空所有文件", command=self.clear_all_files).pack(side=tk.LEFT, padx=5)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # 复制/剪切选择栏
        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill=tk.X, padx=10, pady=6)
        ttk.Radiobutton(mode_frame, text="📋 复制文件（保留原文件）", variable=self.operation_mode, value="copy").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="✂️ 剪切文件（移动原文件）", variable=self.operation_mode, value="cut").pack(side=tk.LEFT, padx=10)

        ttk.Label(self, text="⬇️ 可直接拖入多个文件/文件夹到下方列表区域 ⬇️", foreground="#0066cc", font=("微软雅黑", 10, "bold")).pack(pady=4)

    def create_file_list(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("name", "size", "path")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.tree.heading("name", text="文件名")
        self.tree.heading("size", text="大小")
        self.tree.heading("path", text="完整路径")

        self.tree.column("name", width=250)
        self.tree.column("size", width=100)
        self.tree.column("path", width=350)

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

    # 拖拽文件进入
    def on_files_drop(self, event):
        paths = self.split_drop_paths(event.data)
        if not paths:
            return

        mode = self.operation_mode.get()
        success = 0

        for src in paths:
            if not os.path.exists(src):
                continue
            try:
                name = os.path.basename(src)
                dst = os.path.join(STORAGE_FOLDER, name)

                # 重名处理
                if os.path.exists(dst):
                    new_name = self.get_rename(name)
                    dst = os.path.join(STORAGE_FOLDER, new_name)

                if mode == "copy":
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                    else:
                        shutil.copytree(src, dst)
                else:
                    shutil.move(src, dst)
                success += 1
            except Exception as e:
                messagebox.showerror("错误", f"处理失败：{src}\n{str(e)}")

        messagebox.showinfo("完成", f"已处理 {success} 个项目\n模式：{('复制' if mode=='copy' else '剪切')}")
        self.refresh_file_list()

    # 处理拖拽路径（解决带空格路径问题）
    def split_drop_paths(self, data):
        paths = []
        temp = ""
        inside_quote = False
        for c in data:
            if c == '{':
                inside_quote = True
            elif c == '}':
                inside_quote = False
                if temp:
                    paths.append(temp)
                    temp = ""
            elif c == ' ' and not inside_quote:
                if temp:
                    paths.append(temp)
                    temp = ""
            else:
                temp += c
        if temp:
            paths.append(temp)
        return paths

    # 重名自动编号
    def get_rename(self, name):
        base, ext = os.path.splitext(name)
        i = 1
        while True:
            new_name = f"{base}({i}){ext}"
            if not os.path.exists(os.path.join(STORAGE_FOLDER, new_name)):
                return new_name
            i += 1

    # 刷新文件列表
    def refresh_file_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name in os.listdir(STORAGE_FOLDER):
            path = os.path.join(STORAGE_FOLDER, name)
            size = self.get_size_str(path)
            self.tree.insert("", tk.END, values=(name, size, path))

    # 文件大小格式化
    def get_size_str(self, path):
        if os.path.isdir(path):
            return "文件夹"
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} B"
        elif size < 1024*1024:
            return f"{size/1024:.1f} KB"
        else:
            return f"{size/(1024*1024):.1f} MB"

    # 打开中转文件夹
    def open_storage_folder(self):
        os.startfile(STORAGE_FOLDER) if os.name == "nt" else os.system(f"open '{STORAGE_FOLDER}'")

    # 清空所有文件
    def clear_all_files(self):
        if not messagebox.askyesno("确认", "确定要删除中转区内所有文件吗？不可恢复！"):
            return
        for name in os.listdir(STORAGE_FOLDER):
            path = os.path.join(STORAGE_FOLDER, name)
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            except:
                pass
        self.refresh_file_list()
        messagebox.showinfo("完成", "已清空中转文件夹")

if __name__ == "__main__":
    app = FileTransferStation()
    app.mainloop()