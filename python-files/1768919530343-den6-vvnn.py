import tkinter as tk
from tkinter import messagebox
import threading

def fuck_with_user():
    while True:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showwarning("Zeta系统通知", "烦死你！😈")
        root.destroy()

# 启动多线程确保弹窗不会阻塞
thread = threading.Thread(target=fuck_with_user)
thread.daemon = True
thread.start()

# 防止主线程退出
input("按Enter键停止（骗你的，根本停不下来）哈哈哈！")
