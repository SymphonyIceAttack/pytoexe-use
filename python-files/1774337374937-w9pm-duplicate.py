import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
from difflib import SequenceMatcher
import subprocess
import string
import threading

# 相似度计算
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100

# 清理文件名（去除符号方便比对）
def clean_name(s):
    return ''.join(c for c in s if c not in string.punctuation + ' ').lower()

# 扫描重复文件
def scan_thread(folder):
    result_table.delete(*result_table.get_children())
    status_label.config(text="扫描中...")
    root.update()
    
    file_map = defaultdict(list)
    
    for dirpath, _, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(path)
                name_clean = clean_name(name)
                file_map[name_clean].append((name, path, size))
            except:
                continue
    
    # 分组查重
    duplicates = []
    processed = set()

    # 1. 完全同名
    for key, files in file_map.items():
        if len(files) > 1:
            duplicates.append(files)
            processed.add(key)

    # 2. 相似度>90% + 大小相同
    all_files = []
    for dirpath, _, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(path)
                all_files.append((name, path, size))
            except:
                continue

    for i in range(len(all_files)):
        n1, p1, s1 = all_files[i]
        c1 = clean_name(n1)
        if c1 in processed:
            continue
        for j in range(i+1, len(all_files)):
            n2, p2, s2 = all_files[j]
            c2 = clean_name(n2)
            if c2 in processed:
                continue
            if s1 == s2 and similarity(c1, c2) > 90:
                duplicates.append([all_files[i], all_files[j]])
                processed.add(c1)
                processed.add(c2)

    # 展示结果
    count = 0
    for group in duplicates:
        for name, path, size in group:
            size_str = f"{size/1024/1024:.2f} MB" if size>1024*1024 else f"{size/1024:.2f} KB"
            result_table.insert("", "end", values=(name, path, size_str))
            count += 1

    status_label.config(text=f"完成！共找到 {count} 个重复文件")
    if count == 0:
        messagebox.showinfo("结果", "未找到重复文件")

# 启动扫描线程
def start_scan():
    folder = scan_path.get()
    if not folder or not os.path.exists(folder):
        messagebox.showerror("错误", "请选择有效路径")
        return
    threading.Thread(target=scan_thread, args=(folder,), daemon=True).start()

# 选择路径
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        scan_path.set(folder)

# 选择磁盘
def select_disk():
    disk = filedialog.askdirectory()
    if disk:
        scan_path.set(disk.split(':\\')[0] + ':\\')

# 全盘扫描
def scan_all_disks():
    scan_path.set("")
    disks = []
    for c in string.ascii_uppercase:
        d = c + ":\\",
        if os.path.exists(d):
            disks.append(c + ":\\")
    if not disks:
        messagebox.showerror("错误", "未找到磁盘")
        return
    scan_thread(disks[0])  # 演示：扫第一个盘，如需全盘可循环遍历

# 右键菜单
def on_right_click(event):
    try:
        item = result_table.selection()[0]
        menu.post(event.x_root, event.y_root)
    except:
        pass

# 打开文件夹
def open_path():
    try:
        path = result_table.item(result_table.selection()[0], "values")[1]
        subprocess.run(f'explorer /select,"{path}"')
    except:
        messagebox.showwarning("提示", "请选中文件")

# 复制路径
def copy_path():
    try:
        path = result_table.item(result_table.selection()[0], "values")[1]
        root.clipboard_clear()
        root.clipboard_append(path)
        status_label.config(text="已复制路径")
    except:
        pass

# ==================== 界面 ====================
root = tk.Tk()
root.title("文件查重工具 - 增强版")
root.geometry("950x600")

scan_path = tk.StringVar()

# 控制面板
frame = ttk.Frame(root)
frame.pack(pady=8, fill=tk.X)

ttk.Label(frame, text="扫描路径：").pack(side=tk.LEFT, padx=5)
ttk.Entry(frame, textvariable=scan_path, width=50).pack(side=tk.LEFT, padx=5)
ttk.Button(frame, text="选择文件夹", command=select_folder).pack(side=tk.LEFT, padx=4)
ttk.Button(frame, text="选择磁盘", command=select_disk).pack(side=tk.LEFT, padx=4)
ttk.Button(frame, text="全盘扫描", command=scan_all_disks).pack(side=tk.LEFT, padx=4)
ttk.Button(frame, text="开始扫描", command=start_scan).pack(side=tk.LEFT, padx=4)

# 表格
columns = ("name", "path", "size")
result_table = ttk.Treeview(root, columns=columns, show="headings")
result_table.heading("name", text="文件名")
result_table.heading("path", text="完整路径")
result_table.heading("size", text="文件大小")
result_table.column("name", width=250)
result_table.column("path", width=550)
result_table.column("size", width=100)
result_table.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

# 右键菜单
menu = tk.Menu(root, tearoff=0)
menu.add_command(label="打开所在文件夹", command=open_path)
menu.add_command(label="复制文件路径", command=copy_path)
result_table.bind("<Button-3>", on_right_click)

# 状态栏
status_label = ttk.Label(root, text="就绪")
status_label.pack(side=tk.BOTTOM, pady=5)

root.mainloop()