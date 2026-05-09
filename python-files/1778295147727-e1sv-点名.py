import tkinter as tk
import random

names = [
    "魏甲儒","赵宇","梁耀","王乾","范海英",
    "盛鸿超","汪子航","董春朋","乔楠","宋垚",
    "李冠军","明升亮","马勇","王小龙","胡三飞",
    "朱文瀚","陶含笑","侯泽玮","陶梦","杨善","杨保存"
]

def draw():
    name = random.choice(names)
    label_res.config(text=name)

root = tk.Tk()
root.title("随机抽签器")
root.geometry("420x280")
root.configure(bg="#f5f5f5")

title = tk.Label(root, text="随机抽签", font=("微软雅黑",22), bg="#f5f5f5")
title.pack(pady=25)

label_res = tk.Label(root, text="等待抽签", font=("微软雅黑",28,"bold"), fg="#d93025", bg="#f5f5f5")
label_res.pack(pady=15)

btn = tk.Button(root, text="点击抽签", command=draw, font=("微软雅黑",15), width=12, height=2)
btn.pack(pady=20)

root.mainloop()