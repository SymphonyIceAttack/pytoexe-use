import tkinter as tk
from tkinter import messagebox
import random
import string
import pyperclip  # 需要安装，用于复制到剪贴板

def generate_code():
    # 获取输入的后两位
    suffix = entry.get().strip()
    if len(suffix) != 2:
        messagebox.showerror("错误", "最后两位必须恰好是 2 个字符！")
        return
    
    # 前8位：随机大写字母 + 数字
    prefix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    middle = "5Z9Z1M"
    full_code = prefix + middle + suffix
    
    # 显示结果
    result_var.set(full_code)
    # 复制到剪贴板
    pyperclip.copy(full_code)
    messagebox.showinfo("成功", "已生成并复制到剪贴板！")

# 创建窗口
root = tk.Tk()
root.title("编码生成器")
root.geometry("400x200")
root.resizable(False, False)

# 标签和输入框
tk.Label(root, text="请输入最后两位（任意字符）：", font=("Arial", 12)).pack(pady=10)
entry = tk.Entry(root, font=("Arial", 14), width=10, justify='center')
entry.pack(pady=5)
entry.focus()  # 自动聚焦输入框

# 生成按钮
tk.Button(root, text="生 成", font=("Arial", 12), command=generate_code, width=15).pack(pady=10)

# 显示结果
result_var = tk.StringVar()
tk.Label(root, textvariable=result_var, font=("Arial", 16, "bold"), fg="blue").pack(pady=10)

# 运行主循环
root.mainloop()