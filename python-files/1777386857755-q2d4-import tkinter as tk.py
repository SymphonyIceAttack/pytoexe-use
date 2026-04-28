import tkinter as tk
from tkinter import messagebox
import random

# 主窗口设置
root = tk.Tk()
root.title("专属告白")
root.geometry("400x300")
root.resizable(False, False)
root.config(bg="#fff0f3")

# 拒绝按钮躲避效果
def no_move(event):
    x = random.randint(30, 300)
    y = random.randint(80, 200)
    btn_no.place(x=x, y=y)

# 同意按钮事件（修复无限弹窗bug）
def yes_click():
    root.destroy()
    tip_root = tk.Tk()
    tip_root.title("心动答复")
    tip_root.geometry("350x200")
    tip_root.config(bg="#ffe6ee")
    txt = tk.Label(tip_root,text="❤️ 太棒啦！❤️\n往后余生\n满眼皆是你\n满心全是你",
                   font=("微软雅黑",15),bg="#ffe6ee",fg="#d6336c")
    txt.pack(expand=True)
    tip_root.mainloop()

# 文字标签
label = tk.Label(root, text="你愿意做我的宝贝吗？", 
                 font=("微软雅黑",16),bg="#fff0f3",fg="#222")
label.place(x=70, y=30)

# 同意按钮
btn_yes = tk.Button(root, text="我愿意", font=("微软雅黑",12), 
                    bg="#ff6b81",fg="white",command=yes_click)
btn_yes.place(x=60, y=120, width=80, height=35)

# 拒绝按钮
btn_no = tk.Button(root, text="不要", font=("微软雅黑",12),bg="#cccccc")
btn_no.place(x=220, y=120, width=80, height=35)
btn_no.bind("<Enter>", no_move)

root.mainloop()