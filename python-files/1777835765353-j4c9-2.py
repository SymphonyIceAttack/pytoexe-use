import tkinter as tk
from tkinter import ttk
import random
import time
from threading import Thread

root = tk.Tk()
root.title("🎲 摇一摇随机数字")
root.geometry("400x380")
root.resizable(False, False)
root.configure(bg="#f5f5f5")

is_running = False
min_num = 1
max_num = 100

title_label = ttk.Label(root, text="摇一摇随机数", font=("微软雅黑", 20, "bold"), background="#f5f5f5")
title_label.pack(pady=15)

num_label = ttk.Label(root, text="0", font=("微软雅黑", 60, "bold"), foreground="#2c3e50", background="#f5f5f5")
num_label.pack(pady=20)

frame_range = tk.Frame(root, bg="#f5f5f5")
frame_range.pack(pady=5)

ttk.Label(frame_range, text="最小值：", font=("微软雅黑", 12), background="#f5f5f5").grid(row=0, column=0, padx=5)
min_entry = ttk.Entry(frame_range, width=8, font=("微软雅黑", 12))
min_entry.grid(row=0, column=1, padx=5)
min_entry.insert(0, "1")

ttk.Label(frame_range, text="最大值：", font=("微软雅黑", 12), background="#f5f5f5").grid(row=0, column=2, padx=5)
max_entry = ttk.Entry(frame_range, width=8, font=("微软雅黑", 12))
max_entry.grid(row=0, column=3, padx=5)
max_entry.insert(0, "100")

def start_shake():
    global is_running, min_num, max_num
    if is_running:
        return
    try:
        min_num = int(min_entry.get().strip())
        max_num = int(max_entry.get().strip())
    except:
        num_label.config(text="输入错误")
        return
    if min_num >= max_num:
        num_label.config(text="范围错误")
        return
    is_running = True
    shake_btn.config(text="摇一摇中...", state=tk.DISABLED)
    Thread(target=shake_animation).start()

def shake_animation():
    global is_running
    for _ in range(15):
        n = random.randint(min_num, max_num)
        num_label.config(text=str(n))
        time.sleep(0.08)
    final = random.randint(min_num, max_num)
    num_label.config(text=str(final))
    is_running = False
    shake_btn.config(text="开始摇一摇", state=tk.NORMAL)

shake_btn = tk.Button(root, text="开始摇一摇", font=("微软雅黑", 14, "bold"),
                     bg="#3498db", fg="white", activebackground="#2980b9",
                     activeforeground="white", relief=tk.FLAT, width=15, height=2,
                     command=start_shake)
shake_btn.pack(pady=20)

tip_label = ttk.Label(root, text="按空格键也可以摇一摇", font=("微软雅黑", 10), foreground="#7f8c8d", background="#f5f5f5")
tip_label.pack()

root.bind("<space>", lambda e: start_shake())
root.mainloop()