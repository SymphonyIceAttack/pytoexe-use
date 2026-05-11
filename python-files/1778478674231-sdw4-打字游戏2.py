import random
import tkinter as tk
from tkinter import messagebox

# 主窗口设置
root = tk.Tk()
root.title("自定义字数打字挑战")
root.geometry("450x300")

# 全局变量
rand_str = ""

# 生成随机字母串
def create_str():
    global rand_str
    try:
        # 获取输入的字符个数
        n = int(entry_num.get())
    except:
        messagebox.showerror("错误","请输入合法数字")
        return
    
    rand_str = ""
    for i in range(n):
        # 随机小写英文字母
        rand_str += chr(random.randint(97, 122))
    
    # 显示随机字符
    label_show.config(text=rand_str)
    entry_input.delete(0, tk.END)

# 计算正确率
def calc_rate():
    global rand_str
    if not rand_str:
        messagebox.showwarning("提示","请先生成随机字符")
        return
    
    user_str = entry_input.get()
    n = len(rand_str)
    # 防止输入长度不够报错
    if len(user_str) < n:
        messagebox.showwarning("提示","输入字符数量不足")
        return
    
    count = 0
    # 逐字符比对
    for i in range(n):
        if rand_str[i] == user_str[i]:
            count += 1
    
    # 计算正确率四舍五入
    rate = round(count / n * 100)
    messagebox.showinfo("测评结果", f"正确个数：{count}\n正确率：{rate}%")

# 界面布局
tk.Label(root, text="请输入挑战字符个数：", font=("微软雅黑",11)).pack(pady=8)
entry_num = tk.Entry(root, font=("微软雅黑",12))
entry_num.pack()

tk.Button(root, text="生成随机字符", command=create_str, font=("微软雅黑",11)).pack(pady=8)

label_show = tk.Label(root, text="", font=("Consolas",14), fg="blue")
label_show.pack(pady=5)

tk.Label(root, text="请输入上面的字符：", font=("微软雅黑",11)).pack(pady=5)
entry_input = tk.Entry(root, font=("微软雅黑",12), width=30)
entry_input.pack()

tk.Button(root, text="计算正确率", command=calc_rate, font=("微软雅黑",11)).pack(pady=15)

root.mainloop()