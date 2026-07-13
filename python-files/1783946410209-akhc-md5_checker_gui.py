#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MD5 校验工具 - 图形界面版
功能：选择包含 MD5 列表的 txt 文件，输入期望的 MD5 值，
点击“校验”按钮，判断该值是否在文件中。
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os

class MD5CheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MD5 校验工具")
        self.root.geometry("600x200")
        self.root.resizable(False, False)

        # 文件路径选择
        tk.Label(root, text="MD5 列表文件：").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.file_path_var = tk.StringVar()
        tk.Entry(root, textvariable=self.file_path_var, width=50).grid(row=0, column=1, padx=5, pady=10)
        tk.Button(root, text="浏览...", command=self.browse_file).grid(row=0, column=2, padx=5, pady=10)

        # 期望 MD5 输入
        tk.Label(root, text="期望的 MD5 值：").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.expected_md5_var = tk.StringVar()
        tk.Entry(root, textvariable=self.expected_md5_var, width=50).grid(row=1, column=1, padx=5, pady=10)

        # 校验按钮
        tk.Button(root, text="校验", command=self.check_md5, bg="#4CAF50", fg="white", width=10).grid(row=2, column=1, pady=15)

        # 结果显示
        self.result_label = tk.Label(root, text="", font=("Arial", 12))
        self.result_label.grid(row=3, column=0, columnspan=3, pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="选择 MD5 列表文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)

    def check_md5(self):
        file_path = self.file_path_var.get().strip()
        expected_md5 = self.expected_md5_var.get().strip()

        # 输入验证
        if not file_path:
            messagebox.showerror("错误", "请先选择 MD5 列表文件！")
            return
        if not os.path.isfile(file_path):
            messagebox.showerror("错误", f"文件 '{file_path}' 不存在！")
            return
        if not expected_md5:
            messagebox.showerror("错误", "请输入期望的 MD5 值！")
            return

        # 读取文件中的 MD5 值
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            messagebox.showerror("读取错误", f"无法读取文件：{e}")
            return

        md5_list = [line.strip() for line in lines if line.strip()]
        if not md5_list:
            messagebox.showinfo("提示", "文件中没有找到任何 MD5 值。")
            return

        # 不区分大小写比较
        expected_lower = expected_md5.lower()
        found = any(md5.lower() == expected_lower for md5 in md5_list)

        if found:
            self.result_label.config(text="✓ 匹配成功！该 MD5 值存在于文件中。", fg="green")
        else:
            self.result_label.config(text="✗ 匹配失败！该 MD5 值不在文件中。", fg="red")
            # 弹窗显示文件中的所有 MD5 值
            md5_str = "\n".join(md5_list)
            messagebox.showinfo("文件中的 MD5 值", f"文件包含以下 MD5 值：\n\n{md5_str}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MD5CheckerApp(root)
    root.mainloop()