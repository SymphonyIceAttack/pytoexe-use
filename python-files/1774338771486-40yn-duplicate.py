import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
from difflib import SequenceMatcher
import subprocess
import threading

# 极简相似度计算（只做核心比对，不做冗余处理）
def get_similarity(name1, name2):
    # 只比对文件名（去掉后缀），保留核心逻辑
    n1 = os.path.splitext(name1)[0].lower().replace(" ", "").replace("_", "")
    n2 = os.path.splitext(name2)[0].lower().replace(" ", "").replace("_", "")
    return SequenceMatcher(None, n1, n2).ratio() * 100

# 极速扫描核心（回归上一版的快速度）
def fast_scan(folder):
    # 清空表格
    root.after(0, lambda: result_table.delete(*result_table.get_children()))
    root.after(0, lambda: status_label.config(text="扫描中..."))

    # 第一步：快速收集所有文件信息
    all_files = []
    file_count = 0
    for dirpath, _, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(path)
                if size == 0:  # 跳过空文件
                    continue
                all_files.append( (name, path, size) )
                file_count += 1
            except:
                continue  # 极简异常处理，不卡壳

    # 第二步：查重（分2类，极速比对）
    duplicates = []
    processed = set()

    # 1. 优先：文件名完全一致（忽略后缀/空格）
    name_map = defaultdict(list)
    for name, path, size in all_files:
        clean_name = os.path.splitext(name)[0].lower().replace(" ", "")
        name_map[clean_name].append( (name, path, size) )
    
    for clean_name, files in name_map.items():
        if len(files) > 1:
            duplicates.extend(files)
            processed.update([f"{n}_{p}" for n,p,s in files])  # 标记已处理

    # 2. 补充：相似度>90% + 大小相同（只扫未处理的）
    unprocessed = [f for f in all_files if f"{f[0]}_{f[1]}" not in processed]
    for i in range(len(unprocessed)):
        n1, p1, s1 = unprocessed[i]
        if f"{n1}_{p1}" in processed:
            continue
        for j in range(i+1, len(unprocessed)):
            n2, p2, s2 = unprocessed[j]
            if f"{n2}_{p2}" in processed:
                continue
            if s1 == s2 and get_similarity(n1, n2) > 90:
                duplicates.append( (n1, p1, s1) )
                duplicates.append( (n2, p2, s2) )
                processed.add(f"{n1}_{p1}")
                processed.add(f"{n2}_{p2}")
                break  # 找到即停，不重复比对

    # 第三步：快速展示结果
    root.after(0, lambda: status_label.config(text=f"完成！共扫描{file_count}个文件"))
    if not duplicates:
        messagebox.showinfo("结果", "未找到重复文件")
        return
    
    # 极速插入表格（批量处理，不卡界面）
    for name, path, size in duplicates:
        size_str = f"{size/1024/1024:.2f} MB" if size>1024*1024 else f"{size/1024:.2f} KB"
        root.after(0, lambda n=name,p=path,s=size_str: result_table.insert("", "end", values=(n,p,s)))

# 启动扫描（独立线程，不卡界面）
def start_scan():
    folder = scan_path.get()
    if not folder or not os.path.exists(folder):
        messagebox.showerror("错误", "请选择有效路径")
        return
    threading.Thread(target=fast_scan, args=(folder,), daemon=True).start()

# 选择路径/磁盘
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        scan_path.set(folder)

def select_disk():
    disk = filedialog.askdirectory()
    if disk:
        scan_path.set(disk.split(':\\')[0] + ':\\')

# 右键功能（极简实现）
def open_path():
    try:
        path = result_table.item(result_table.selection()[0], "values")[1]
        subprocess.run(f'explorer /select,"{path}"', shell=True)
    except:
        messagebox.showwarning("提示", "请选中文件路径！")

# ==================== 极简界面（和上一版一致） ====================
root = tk.Tk()
root.title("文件查重工具 - 极速版")
root.geometry("950x600")

scan_path = tk.StringVar()

# 控制面板
frame = ttk.Frame(root)
frame.pack(pady=8, fill=tk.X)
ttk.Label(frame, text="扫描路径：").pack(side=tk.LEFT, padx=5)
ttk.Entry(frame, textvariable=scan_path, width=50).pack(side=tk.LEFT, padx=5)
ttk.Button(frame, text="选择文件夹", command=select_folder).pack(side=tk.LEFT, padx=4)
ttk.Button(frame, text="选择磁盘", command=select_disk).pack(side=tk.LEFT, padx=4)
ttk.Button(frame, text="开始扫描", command=start_scan).pack(side=tk.LEFT, padx=4)

# 结果表格
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
result_table.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))

# 状态栏
status_label = ttk.Label(root, text="就绪")
status_label.pack(side=tk.BOTTOM, pady=5)

root.mainloop()