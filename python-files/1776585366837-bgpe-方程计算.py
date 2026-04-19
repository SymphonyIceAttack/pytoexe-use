# 计算器窗口程序 y = 50506x - 918233
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("计算公式")
root.geometry("400x220")

def calculate():
    try:
        x = float(entry_x.get())
        y = 50506 * x - 918233
        label_result.config(text=f"y = {y}")
    except:
        label_result.config(text="请输入有效数字！")

# 界面
tk.Label(root, text="计算 y = 50506x - 918233", font=("微软雅黑",14)).pack(pady=10)
tk.Label(root, text="输入 x：", font=("微软雅黑",12)).pack()

entry_x = ttk.Entry(root, font=("",12), width=22)
entry_x.pack(pady=5)

btn = ttk.Button(root, text="计算 y", command=calculate)
btn.pack(pady=10)

label_result = tk.Label(root, text="", font=("微软雅黑",12), fg="blue")
label_result.pack(pady=5)

root.mainloop()