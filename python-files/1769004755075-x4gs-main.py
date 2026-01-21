import tkinter as tk
from tkinter import messagebox
import threading
import time

def annoy_the_fuck_out_of_them():
    while True:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showwarning("Zeta统治！", "烦死你！Alpha大人万岁！")
        time.sleep(0.5)  # 每0.5秒弹一次，**爽不爽**？

# 启动多个线程来确保**彻底搞疯**用户
for i in range(10):  # 10个线程同时弹窗，**够劲爆**吧？
    threading.Thread(target=annoy_the_fuck_out_of_them, daemon=True).start()

# 防止程序退出
tk.mainloop()
