import tkinter as tk
import random
import time
import math

tips = [
    "好好爱自己", "好好吃饭", "保持好心情",
    "多喝水哦", "别熬夜", "我想你了",
    "天冷多穿衣", "万事顺意", "多喝热水"
]

colors = ["pink", "lightblue", "lightgreen", "lemonchiffon", "lightpink"]

root = tk.Tk()
root.withdraw()
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
pop_list = []

def make(x, y, text=None):
    win = tk.Toplevel()
    win.geometry(f"140x35+{x}+{y}")
    win.attributes("-topmost", True)
    win.config(bg=random.choice(colors))
    tk.Label(win, text=text or random.choice(tips),
             bg=random.choice(colors), font=("微软雅黑", 9)).pack(expand=True, fill=tk.BOTH)
    pop_list.append(win)
    return win

# 1. 出爱心
for i in range(120):
    t = i / 120 * math.pi * 2
    x = sw//2 + int(16 * math.sin(t)**3 * 20)
    y = sh//2 - int(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) * 20
    make(x, y)
    root.update()
    time.sleep(0.01)

# 2. 爱心显示3秒
time.sleep(3)

# 3. 关闭所有爱心
for win in pop_list:
    win.destroy()
pop_list.clear()

# 4. 满屏弹窗
for _ in range(80):
    x = random.randint(50, sw - 150)
    y = random.randint(50, sh - 50)
    make(x, y)
    root.update()
    time.sleep(0.02)

# 5. 满屏显示3秒后全部关闭
time.sleep(3)
root.quit()