import random
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("打字正确率练习")
root.geometry("400x250")

target = ""

def generate():
    global target
    try:
        n = int(entry1.get())
    except:
        messagebox.showerror("错误","请输入数字")
        return
    target = ""
    for i in range(n):
        target += chr(random.randint(97,122))
    label2.config(text=target)

def check():
    global target
    user = entry2.get()
    correct = 0
    length = len(target)
    if len(user) < length:
        messagebox.showwarning("提示","请输入完整")
        return
    for i in range(length):
        if target[i] == user[i]:
            correct +=1
    rate = round(correct / length *100)
    messagebox.showinfo("结果", f"正确：{correct}个\n正确率：{rate}%")

# 界面
tk.Label(root, text="输入字符个数：").pack()
entry1 = tk.Entry(root)
entry1.pack()

tk.Button(root, text="生成字母", command=generate).pack(pady=5)

label2 = tk.Label(root, text="", font=("Arial",14), fg="blue")
label2.pack()

tk.Label(root, text="请输入：").pack()
entry2 = tk.Entry(root)
entry2.pack()

tk.Button(root, text="计算正确率", command=check).pack(pady=10)

root.mainloop()