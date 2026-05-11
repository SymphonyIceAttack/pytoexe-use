import random
import tkinter as tk
from tkinter import messagebox

# 创建主窗口
win = tk.Tk()
win.title("自定义字数字母打字训练")
win.geometry("500x320")

# 全局存随机生成的字母串
s = ""

# 生成随机字母串
def make_code():
    global s
    try:
        # 获取用户输入的字符个数
        n = int(ent_num.get())
    except:
        messagebox.showerror("输入错误", "请输入整数数字！")
        return
    
    s = ""
    # 循环随机生成小写字母
    for i in range(n):
        s = s + chr(random.randint(97, 122))
    
    # 显示生成的字母
    lab_code.config(text=s)
    ent_input.delete(0, tk.END)

# 比对计算正确率
def check():
    global s
    if s == "":
        messagebox.showwarning("提示", "请先点击生成字母！")
        return
    
    t = ent_input.get()
    n = len(s)
    # 防止输入长度不够越界
    if len(t) < n:
        messagebox.showwarning("提示", "输入字符数量不够，请输满对应个数！")
        return
    
    c = 0
    # 逐位比对统计正确个数
    for i in range(n):
        if s[i] == t[i]:
            c = c + 1
    
    # 计算正确率并四舍五入
    rate = round(c / len(s) * 100)
    messagebox.showinfo("测评结果", f"正确个数：{c} 个\n正确率：{rate} %")

# 界面布局
tk.Label(win, text("请输入练习字符个数：", font=("微软雅黑", 12))).pack(pady=8)
ent_num = tk.Entry(win, font=("微软雅黑", 12), width=20)
ent_num.pack()

tk.Button(win, text("随机生成字母", command=make_code, font=("微软雅黑", 11)).pack(pady=8)

lab_code = tk.Label(win, text="", font=("Consolas", 16), fg="#0066cc")
lab_code.pack(pady=6)

tk.Label(win, text("请对照输入上面字母：", font=("微软雅黑", 12))).pack(pady=6)
ent_input = tk.Entry(win, font=("微软雅黑", 12), width=30)
ent_input.pack()

tk.Button(win, text("查看打字正确率", command=check, font=("微软雅黑", 11)).pack(pady=15)

win.mainloop()