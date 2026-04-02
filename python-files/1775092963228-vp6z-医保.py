# -*- coding: utf-8 -*-
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

root = tk.Tk()
root.title("医保费用查询工具")
root.geometry("490x390")
root.attributes("-topmost", True)
root.resizable(False, False)
df = None

def load_excel():
    global df
    path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx;*.xls")])
    if not path:
        return
    try:
        df = pd.read_excel(path)
        lbl_file.config(text="已加载：" + path.split("/")[-1].split("\\")[-1])
    except Exception as e:
        messagebox.showerror("错误", "加载失败：\n" + str(e))

def search():
    if df is None:
        messagebox.showwarning("提示", "请先导入Excel")
        return
    code = entry_code.get().strip().lower()
    if "." in code:
        left, right = code.split(".", 1)
        short_code = f"{left}.{right[0]}" if right else left
    else:
        short_code = code
    lbl_match.config(text=f"匹配编码：{short_code}")
    for item in tree.get_children():
        tree.delete(item)
    match_df = df[df["主要诊断代码"].astype(str).str.strip().str.lower() == short_code]
    if match_df.empty:
        messagebox.showinfo("结果", "未找到数据")
        return
    for _, row in match_df.iterrows():
        tree.insert("", "end", values=(
            str(row["主要诊断代码"]),
            str(row["主要诊断名称"]),
            str(row["低倍率费用"]),
            str(row["标准费用"]),
            str(row["手术操作代码对应的费用"])
        ))

frame1 = ttk.Frame(root)
frame1.pack(pady=6, padx=10, fill="x")
ttk.Button(frame1, text="导入Excel", command=load_excel).pack(side="left")
lbl_file = ttk.Label(frame1, text="未导入文件")
lbl_file.pack(side="left", padx=10)

frame2 = ttk.Frame(root)
frame2.pack(pady=6, padx=10, fill="x")
ttk.Label(frame2, text="诊断编码：").pack(side="left")
entry_code = ttk.Entry(frame2, width=22)
entry_code.pack(side="left", padx=5)
ttk.Button(frame2, text="查询", command=search).pack(side="left")

lbl_match = ttk.Label(root, text="")
lbl_match.pack(pady=2)

cols = ["诊断代码", "诊断名称", "低倍率", "标准费用", "手术费用"]
tree = ttk.Treeview(root, columns=cols, show="headings", height=13)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=92, anchor="center")
tree.pack(padx=10, pady=8, fill="x")

root.mainloop()
