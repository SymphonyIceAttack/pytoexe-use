import tkinter as tk
from tkinter import messagebox
import webbrowser

def check_password():
    entered_password = entry.get()
    correct_password = "prioritizeChunkUpdates:0"
    
    if entered_password == correct_password:
        # 打开指定的链接
        webbrowser.open("https://pan.baidu.com/s/50N4TkbCEJMpt-1-K18FoCg")
        root.destroy()  # 关闭窗口
    else:
        messagebox.showerror("错误", "密码不正确！")

# 创建主窗口
root = tk.Tk()
root.title("密码验证")
root.geometry("300x150")

# 创建标签
label = tk.Label(root, text="请输入密码:")
label.pack(pady=20)

# 创建输入框
entry = tk.Entry(root, show="*", width=30)
entry.pack(pady=10)

# 创建按钮
button = tk.Button(root, text="提交", command=check_password)
button.pack(pady=10)

# 运行主循环
root.mainloop()



