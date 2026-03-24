import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict
import subprocess

def scan_duplicates():
    folder = filedialog.askdirectory()
    if not folder:
        return
    
    result_box.delete(1.0, tk.END)
    size_map = defaultdict(list)
    
    result_box.insert(tk.END, "正在扫描文件...\n")
    root.update()
    
    for dirpath, _, filenames in os.walk(folder):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(path)
                size_map[size].append(path)
            except:
                continue
    
    duplicates = [s for s in size_map.values() if len(s) > 1]
    
    if not duplicates:
        result_box.insert(tk.END, "✅ 未发现重复文件\n")
        return
    
    result_box.insert(tk.END, f"✅ 扫描完成！找到 {len(duplicates)} 组重复文件\n\n")
    
    for idx, files in enumerate(duplicates, 1):
        size = os.path.getsize(files[0])
        size_str = f"{size/1024/1024:.2f} MB" if size > 1024*1024 else f"{size/1024:.2f} KB"
        result_box.insert(tk.END, f"===== 第{idx}组重复（大小：{size_str}）=====\n")
        for f in files:
            result_box.insert(tk.END, f"📄 {f}\n")
        result_box.insert(tk.END, "\n")

def open_location():
    try:
        path = result_box.get(tk.SEL_FIRST, tkc.SEL_LAST).strip()
        if os.path.exists(path):
            subprocess.run(f'explorer /select,"{path}"')
    except:
        messagebox.showinfo("提示", "请先选中一条完整文件路径！")

def clear_result():
    result_box.delete(1.0, tk.END)

# 界面
root = tk.Tk()
root.title("文件查重工具 - 大小比对版")
root.geometry("750x500")

frame = ttk.Frame(root)
frame.pack(pady=10, fill=tk.X)

ttk.Button(frame, text="选择文件夹并扫描", command=scan_duplicates).pack(side=tk.LEFT, padx=10)
ttk.Button(frame, text="打开选中文件位置", command=open_location).pack(side=tk.LEFT, padx=10)
ttk.Button(frame, text="清空结果", command=clear_result).pack(side=tk.LEFT, padx=10)

result_box = tk.Text(root, font=("微软雅黑", 10))
result_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
result_box.insert(tk.END, "使用说明：\n1. 点击【选择文件夹并扫描】\n2. 扫描后选中路径可打开位置\n3. 按文件大小查重，速度极快\n")

root.mainloop()