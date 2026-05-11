import random
import tkinter as tk
from tkinter import messagebox, simpledialog

root = tk.Tk()
root.title("打字小游戏")
root.geometry("600x400")
root.resizable(False, False)

target_text = ""
left_time = 60
timer_id = None

# 倒计时
def count_down():
    global left_time, timer_id
    left_time -= 1
    label_time.config(text=f"剩余时间：{left_time} 秒")
    if left_time > 0:
        timer_id = root.after(1000, count_down)
    else:
        messagebox.showwarning("时间到", "一分钟时间已到，自动提交成绩！")
        check_result()

# 生成随机字符
def generate_text():
    global target_text, left_time, timer_id
    # 重置倒计时
    if timer_id is not None:
        root.after_cancel(timer_id)
    left_time = 60
    label_time.config(text=f"剩余时间：{left_time} 秒")
    
    count = simpledialog.askinteger("输入", "请输入你要挑战的字符个数：", parent=root, minvalue=1)
    if not count:
        return
    
    target_text = ""
    for i in range(count):
        target_text += chr(random.randint(97, 122))
    
    label_target.config(text=target_text, wraplength=550)
    entry_input.delete(0, tk.END)
    entry_input.focus()
    # 开始倒计时
    count_down()

# 检查正确率
def check_result():
    global target_text, timer_id
    # 停止倒计时
    if timer_id is not None:
        root.after_cancel(timer_id)
        timer_id = None
    
    user_input = entry_input.get()
    if not target_text:
        messagebox.showwarning("提示", "请先生成目标字符！")
        return
    
    correct_count = 0
    min_len = min(len(target_text), len(user_input))
    for i in range(min_len):
        if target_text[i] == user_input[i]:
            correct_count += 1
    
    accuracy = round(correct_count / len(target_text) * 100)
    messagebox.showinfo("成绩", f"挑战完成！\n正确字数：{correct_count}\n你的正确率为：{accuracy}%")

# 界面布局
label_title = tk.Label(root, text="一分钟打字小游戏", font=("微软雅黑", 16))
label_title.pack(pady=10)

# 倒计时显示
label_time = tk.Label(root, text="剩余时间：60 秒", font=("微软雅黑", 14), fg="red")
label_time.pack(pady=5)

# 目标文字 自动换行
label_target = tk.Label(
    root, 
    text="点击生成按钮开始游戏", 
    font=("微软雅黑", 14), 
    fg="blue",
    wraplength=550
)
label_target.pack(pady=10, padx=20)

entry_input = tk.Entry(root, font=("微软雅黑", 14), width=40)
entry_input.pack(pady=10)

frame_btn = tk.Frame(root)
frame_btn.pack(pady=20)

btn_generate = tk.Button(frame_btn, text="生成字符开始", font=("微软雅黑", 12), 
                        command=generate_text, bg="#4CAF50", fg="white", width=12)
btn_generate.grid(row=0, column=0, padx=10)

btn_check = tk.Button(frame_btn, text="提前交卷", font=("微软雅黑", 12), 
                     command=check_result, bg="#2196F3", fg="white", width=12)
btn_check.grid(row=0, column=1, padx=10)

root.mainloop()