import random
import tkinter as tk
from tkinter import ttk, messagebox

# ======================
# 【你的原代码逻辑 完全保留】
# ======================
f = open("book.txt", "r", encoding="utf-8")
book = f.read()
f.close()
words = book.split()

score = 0
wrong = 0
current_text = ""
limit = 0
start_time = 0

# ======================
# 界面主程序
# ======================
root = tk.Tk()
root.title("英文打字练习软件")
root.geometry("650x380")
root.resizable(False, False)

def new_question():
    global current_text, limit, start_time
    p = random.randint(0, len(words)-3)
    n = random.randint(1, 3)
    current_text = " ".join(words[p:p+n])
    limit = len(current_text)
    label_question.config(text=current_text)
    entry_input.delete(0, tk.END)
    label_limit.config(text=f"限时：{limit} 秒")
    start_time = root.after(limit * 1000, timeout)

def timeout():
    global wrong
    wrong += 1
    label_wrong.config(text=f"错误次数：{wrong}")
    messagebox.showwarning("超时", "超时！")
    if wrong >= 3:
        end_game()
    else:
        new_question()

def check(event=None):
    global score, wrong
    root.after_cancel(start_time)
    u = entry_input.get()
    err = False

    # ======================
    # 【你的原核对代码 原样】
    # ======================
    for i in range(max(len(current_text), len(u))):
        if i >= len(current_text) or i >= len(u) or current_text[i] != u[i]:
            messagebox.showerror("错误", f"第{i+1}个字符错误")
            wrong += 1
            label_wrong.config(text=f"错误次数：{wrong}")
            err = True
            break
    if not err:
        messagebox.showinfo("正确", "输入正确！")
        score += 5
        label_score.config(text=f"得分：{score}")
    if wrong >= 3:
        end_game()
        return
    new_question()

def end_game():
    messagebox.showinfo("游戏结束", f"最终得分：{score}")
    root.destroy()

# ======================
# 界面布局
# ======================
tk.Label(root, text="英文打字练习", font=("微软雅黑", 20)).pack(pady=10)
label_question = tk.Label(root, text="", font=("Consolas", 16), fg="blue")
label_question.pack(pady=10)
label_limit = tk.Label(root, text="", font=("微软雅黑", 12))
label_limit.pack()
entry_input = ttk.Entry(root, font=("微软雅黑", 14), width=40)
entry_input.pack(pady=10)
entry_input.bind("<Return>", check)
ttk.Button(root, text="提交", command=check).pack(pady=5)
label_score = tk.Label(root, text="得分：0", font=("微软雅黑", 12))
label_score.pack()
label_wrong = tk.Label(root, text="错误次数：0", font=("微软雅黑", 12))
label_wrong.pack()

new_question()
root.mainloop()