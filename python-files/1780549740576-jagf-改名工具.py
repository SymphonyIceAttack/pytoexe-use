import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

def export_to_excel():
    folder_path = filedialog.askdirectory(title="选择待提取目录")
    if not folder_path:
        return
    all_names = os.listdir(folder_path)
    df = pd.DataFrame({
        "原始名称": all_names,
        "新名称(自行填写)": [""] * len(all_names)
    })
    save_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx")],
        initialfile="文件名清单.xlsx"
    )
    if save_path:
        df.to_excel(save_path, index=False)
        messagebox.showinfo("完成", f"导出成功，共{len(all_names)}条")

def rename_from_excel():
    excel_path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")], title="选择清单Excel")
    if not excel_path:
        return
    folder = filedialog.askdirectory(title="选择要批量改名的文件夹")
    if not folder:
        return
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        messagebox.showerror("错误", f"读取失败：{str(e)}")
        return
    if "原始名称" not in df.columns or "新名称(自行填写)" not in df.columns:
        messagebox.showerror("格式错误", "必须使用本软件导出的Excel！")
        return
    suc, err = 0, 0
    for _, row in df.iterrows():
        old = str(row["原始名称"]).strip()
        new = str(row["新名称(自行填写)"]).strip()
        if not old or not new:
            continue
        old_p = os.path.join(folder, old)
        new_p = os.path.join(folder, new)
        if os.path.exists(old_p) and old_p != new_p:
            try:
                os.rename(old_p, new_p)
                suc += 1
            except:
                err += 1
    messagebox.showinfo("改名结束", f"成功：{suc}个\n失败：{err}个")

def main():
    root = tk.Tk()
    root.title("文件批量提取改名工具")
    root.geometry("380x180")
    root.resizable(0,0)
    ttk.Label(root,text="提取文件名→Excel | Excel批量改名",font=("微软雅黑",13)).pack(pady=18)
    ttk.Button(root,text="1.提取目录名称到Excel",command=export_to_excel,width=32).pack(pady=8)
    ttk.Button(root,text="2.根据Excel批量重命名",command=rename_from_excel,width=32).pack(pady=8)
    root.mainloop()

if __name__ == "__main__":
    main()