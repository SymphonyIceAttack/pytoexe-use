# -*- coding: utf-8 -*-
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

root = tk.Tk()
root.title("医保费用查询工具")
root.geometry("480x380")
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
        messagebox.showerror("错误", "Excel加载失败")

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
    for i in tree.get_children():
        tree.delete(i)

    match_df = df[df["主要诊断代码"].astype(str).str.strip().str.lower() == short_code]
    if match_df.empty:
        messagebox.showinfo("结果", "未找到匹配数据")
        return

    for _, r in match_df.iterrows():
        tree.insert("", "end", values=(
            str(r["主要诊断代码"]),
            str(r["主要诊断名称"]),
            str(r["低倍率费用"]),
            str(r["标准费用"]),
            str(r["手术操作代码对应的费用"])
        ))

# 界面
ttk.Button(root, text="导入Excel", command=load_excel).place(x=10, y=10)
lbl_file = ttk.Label(root, text="未导入文件")
lbl_file.place(x=100, y=13)

ttk.Label(root, text="诊断编码：").place(x=10, y=45)
entry_code = ttk.Entry(root)
entry_code.place(x=80, y=43, width=180)
ttk.Button(root, text="查询", command=search).place(x=270, y=41)

lbl_match = ttk.Label(root, text="", font=("微软雅黑", 9))
lbl_match.place(x=10, y=75)

cols = ["诊断代码", "名称", "低倍率", "标准费", "手术费"]
tree = ttk.Treeview(root, columns=cols, show="headings", height=14)
for c in cols:
    tree.heading(c, text=c)
    tree.column(c, width=90, anchor="center")
tree.place(x=10, y=100, width=460, height=260)

root.mainloop()
