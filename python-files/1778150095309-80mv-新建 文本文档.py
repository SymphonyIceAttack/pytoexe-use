import tkinter as tk
import random
import threading

msgs = [
    "下班下班！",
    "打洲打洲打洲打洲打洲打洲！",
    "再不打就废了！",
    "上号上号上号上号上号上号！",
    "搜、打、撤"
]

def create_win():
    root = tk.Tk()
    root.title("打洲通知")
    w = 300
    h = 150
    x = random.randint(0, 900)
    y = random.randint(0, 500)
    root.geometry(f"{w}x{h}+{x}+{y}")
    tk.Label(root, text=random.choice(msgs), font=("微软雅黑",12), fg="red").pack(expand=True)
    root.mainloop()

while True:
    t = threading.Thread(target=create_win, daemon=True)
    t.start()