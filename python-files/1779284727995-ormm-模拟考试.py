import tkinter as tk
from tkinter import messagebox, filedialog
import random
import time
import os

# ---------------------- 题库（来自你提供文档） ----------------------
# 互联网、AI、物联网 选择题
internet_questions = [
    {"q":"家庭WiFi网络属于？","A":"LAN局域网","B":"MAN城域网","C":"WAN广域网","D":"PAN个人网","ans":"A"},
    {"q":"覆盖全国的网络英文缩写？","A":"LAN","B":"MAN","C":"WAN","D":"PAN","ans":"C"},
    {"q":"光纤优势？","A":"便宜","B":"速度快抗干扰","C":"不用路由器","D":"稳定","ans":"B"},
    {"q":"域名解析系统？","A":"HTTP","B":"DNS","C":"FTP","D":"SMTP","ans":"B"},
    {"q":".cn代表？","A":"美国","B":"英国","C":"中国","D":"日本","ans":"C"},
]
ai_questions = [
    {"q":"AI听懂指令控制家电体现？","A":"模拟人类智能","B":"替代人类","C":"不用数据","D":"简单任务","ans":"A"},
    {"q":"AI下棋赢人类靠？","A":"情感","B":"计算决策","C":"直觉","D":"创造","ans":"B"},
    {"q":"AI招聘性别偏见原因？","A":"故意","B":"训练数据偏见","C":"算力不足","D":"使用不当","ans":"B"},
]
iot_questions = [
    {"q":"物联网英文缩写？","A":"LAN","B":"IoT","C":"WAN","D":"Internet","ans":"B"},
    {"q":"物联网核心依托？","A":"传感器","B":"控制器","C":"互联网","D":"执行器","ans":"C"},
    {"q":"物联网终端是？","A":"计算机","B":"智能设备","C":"手机","D":"服务器","ans":"B"},
]
# Python编程 填空/连线/拖拽
python_fill = [
    {"code":"n = ____(\"请输入座号：\")\n____(\"右侧入口\")\n____ n%2==0:\n    print(\"右\")\n____:\n    print(\"左\")",
     "blanks":["input","print","if","else"],
     "ans":["input","print","if","else"]}
]
python_link = [
    {"left":"print(\"右侧入口进入\")","right":"打印输出：右侧入口进入"},
    {"left":"n = int(input())","right":"输入座号转为整数"},
]
python_drag = [
    {"origin":["输入座号n","n≠0？","偶数？","右侧入口","左侧入口"],
     "target":["判断n≠0","判断偶数","输出右侧","输出左侧","输入座号"]}
]
# WPS操作题
wps_table_q = "WPS表格：新建表格，A1:C3输入数据，A4求和；设置列宽10，行高20，居中对齐。"
wps_ppt_q = "WPS演示：新建幻灯片，插入图片+音频；设置图片动画为擦除；新增1张幻灯片。"

# ---------------------- 全局变量 ----------------------
total_score = 100
q_per_set = 30
current_q = 0
answers = {}
score = 0
wrong_list = []
root = None
main_frame = None
q_frame = None
nav_frame = None
btn_frame = None

# ---------------------- 生成30套试卷 ----------------------
def generate_30_sets():
    sets = []
    for set_id in range(1,31):
        qs = []
        # 选择20道选择
        all_choice = internet_questions+ai_questions+iot_questions
        random.shuffle(all_choice)
        qs.extend(all_choice[:20])
        # 填空1
        qs.append({"type":"fill","data":python_fill[0]})
        # 连线1
        qs.append({"type":"link","data":python_link})
        # 拖拽1
        qs.append({"type":"drag","data":python_drag[0]})
        # WPS表格
        qs.append({"type":"wps_table","q":wps_table_q})
        # WPS演示
        qs.append({"type":"wps_ppt","q":wps_ppt_q})
        # Python编程
        qs.append({"type":"py_code","q":"剧场引导程序：输入座号，偶数右入口，奇数左入口，输入0退出。"})
        sets.append(qs[:30])
    return sets

all_sets = generate_30_sets()
current_set = None

# ---------------------- 登录界面 ----------------------
def login():
    global root
    root = tk.Tk()
    root.title("模拟考试系统")
    root.geometry("800x600")
    root.attributes('-fullscreen', True)
    root.configure(bg='#f0f0f0')

    tk.Label(root, text="考生登录", font=('微软雅黑',24,'bold'), bg='#f0f0f0').pack(pady=50)

    tk.Label(root, text="选择试卷：", font=('微软雅黑',14)).pack()
    set_var = tk.StringVar()
    set_combo = tk.OptionMenu(root, set_var, *[f"第{i}套" for i in range(1,31)])
    set_combo.config(font=('微软雅黑',12))
    set_combo.pack(pady=10)

    tk.Label(root, text="考号（班级+机器号）：", font=('微软雅黑',14)).pack()
    id_entry = tk.Entry(root, font=('微软雅黑',14), width=30)
    id_entry.pack(pady=10)

    def start():
        global current_set
        set_name = set_var.get()
        if not set_name:
            messagebox.showerror("错误","请选择试卷！")
            return
        if not id_entry.get().strip():
            messagebox.showerror("错误","请输入考号！")
            return
        set_idx = int(set_name.replace("第","").replace("套",""))-1
        current_set = all_sets[set_idx]
        root.destroy()
        exam_ui()

    tk.Button(root, text="进入考试", font=('微软雅黑',16), bg='#0078d4', fg='white', width=15, command=start).pack(pady=30)
    root.mainloop()

# ---------------------- 考试主界面 ----------------------
def exam_ui():
    global root, main_frame, q_frame, nav_frame, btn_frame, current_q
    root = tk.Tk()
    root.title("模拟考试")
    root.attributes('-fullscreen', True)
    root.configure(bg='white')

    # 右侧导航
    nav_frame = tk.Frame(root, width=150, bg='#e0e0e0')
    nav_frame.pack(side='right', fill='y')
    tk.Label(nav_frame, text="题目目录", font=('微软雅黑',14,'bold'), bg='#e0e0e0').pack(pady=10)

    # 主题目区
    main_frame = tk.Frame(root)
    main_frame.pack(side='left', fill='both', expand=True)
    q_frame = tk.Frame(main_frame, bg='white')
    q_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # 按钮区
    btn_frame = tk.Frame(root, bg='#f0f0f0')
    btn_frame.pack(side='bottom', fill='x')
    tk.Button(btn_frame, text="上一题", font=('微软雅黑',12), command=prev_q).pack(side='left', padx=20, pady=5)
    tk.Button(btn_frame, text="下一题", font=('微软雅黑',12), command=next_q).pack(side='left', padx=20, pady=5)
    tk.Button(btn_frame, text="评分", font=('微软雅黑',12), bg='#ffc107', command=show_score).pack(side='left', padx=20, pady=5)
    tk.Button(btn_frame, text="交卷", font=('微软雅黑',12), bg='#dc3545', fg='white', command=submit_exam).pack(side='left', padx=20, pady=5)

    # 生成导航按钮
    for i in range(q_per_set):
        tk.Button(nav_frame, text=str(i+1), width=4, command=lambda idx=i: jump_q(idx)).pack(pady=2)

    current_q = 0
    load_q()
    root.mainloop()

# ---------------------- 加载题目 ----------------------
def load_q():
    global current_q, answers
    for widget in q_frame.winfo_children():
        widget.destroy()
    q = current_set[current_q]
    tk.Label(q_frame, text=f"第{current_q+1}题", font=('微软雅黑',16,'bold')).pack(anchor='w')

    if "ans" in q: # 选择题
        tk.Label(q_frame, text=q["q"], font=('微软雅黑',14)).pack(anchor='w', pady=10)
        opts = [("A",q["A"]),("B",q["B"]),("C",q["C"]),("D",q["D"])]
        var = tk.StringVar(value=answers.get(current_q, ""))
        for opt, txt in opts:
            tk.Radiobutton(q_frame, text=f"{opt}. {txt}", variable=var, value=opt, font=('微软雅黑',12)).pack(anchor='w')
        answers[current_q] = var
    elif q["type"]=="fill":
        data = q["data"]
        tk.Label(q_frame, text="填空题（4空，填input/print/if/else）", font=('微软雅黑',14)).pack()
        tk.Label(q_frame, text=data["code"], font=('Consolas',12)).pack(pady=10)
        entries = []
        for i in range(4):
            e = tk.Entry(q_frame, width=10)
            e.pack()
            entries.append(e)
        answers[current_q] = entries
    elif q["type"]=="link":
        tk.Label(q_frame, text="连线题：左右匹配", font=('微软雅黑',14)).pack()
        lefts = [x["left"] for x in q["data"]]
        rights = [x["right"] for x in q["data"]]
        random.shuffle(rights)
        for i,l in enumerate(lefts):
            tk.Label(q_frame, text=l, font=('微软雅黑',12)).grid(row=i, column=0, padx=20)
        for i,r in enumerate(rights):
            tk.Label(q_frame, text=r, font=('微软雅黑',12)).grid(row=i, column=2, padx=20)
        answers[current_q] = {"left":lefts, "right":rights}
    elif q["type"]=="drag":
        tk.Label(q_frame, text="拖拽排序题：按流程排序", font=('微软雅黑',14)).pack()
        items = q["data"]["origin"]
        random.shuffle(items)
        for it in items:
            tk.Label(q_frame, text=it, bg='#e0e0e0', font=('微软雅黑',12)).pack(pady=5)
        answers[current_q] = items
    elif q["type"] in ["wps_table","wps_ppt"]:
        tk.Label(q_frame, text=q["q"], font=('微软雅黑',14), fg='blue').pack(pady=20)
        tk.Label(q_frame, text="请打开WPS/Office完成操作，完成后点击下一题", font=('微软雅黑',12)).pack()
    elif q["type"]=="py_code":
        tk.Label(q_frame, text="Python编程题：", font=('微软雅黑',14)).pack()
        tk.Label(q_frame, text=q["q"], font=('微软雅黑',12)).pack(pady=10)
        tk.Text(q_frame, width=80, height=10, font=('Consolas',10)).pack()

# ---------------------- 上下题/跳转 ----------------------
def prev_q():
    global current_q
    if current_q>0:
        current_q-=1
        load_q()

def next_q():
    global current_q
    if current_q<q_per_set-1:
        current_q+=1
        load_q()

def jump_q(idx):
    global current_q
    current_q=idx
    load_q()

# ---------------------- 评分 ----------------------
def calc_score():
    global score, wrong_list
    score=0
    wrong_list=[]
    for idx,q in enumerate(current_set):
        if "ans" in q:
            user_ans = answers.get(idx, tk.StringVar()).get()
            if user_ans==q["ans"]:
                score += 3
            else:
                wrong_list.append((idx+1, q["q"], q["ans"], user_ans))
        elif q["type"]=="fill":
            user = [e.get().strip() for e in answers[idx]]
            if user == q["data"]["ans"]:
                score += 5
            else:
                wrong_list.append((idx+1, "填空题", q["data"]["ans"], user))
        elif q["type"] in ["wps_table","wps_ppt"]:
            score += 5
        elif q["type"]=="py_code":
            score += 10
    return score

def show_score():
    s = calc_score()
    msg = f"当前得分：{s}/100\n错题数：{len(wrong_list)}\n"
    for w in wrong_list:
        msg += f"第{w[0]}题：{w[1]}\n正确：{w[2]} 你的：{w[3]}\n"
    messagebox.showinfo("评分结果", msg)

# ---------------------- 交卷 ----------------------
def submit_exam():
    # 第一次确认：输入Y
    confirm1 = tk.Toplevel(root)
    confirm1.title("确认交卷")
    confirm1.geometry("300x150")
    tk.Label(confirm1, text="请输入Y确认交卷：").pack(pady=10)
    e = tk.Entry(confirm1)
    e.pack()
    def ok1():
        if e.get().strip().upper()=="Y":
            confirm1.destroy()
            # 第二次确认
            if messagebox.askyesno("最终确认","交卷后无法修改，确定交卷？"):
                final_submit()
        else:
            messagebox.showerror("错误","请输入Y")
    tk.Button(confirm1, text="确定", command=ok1).pack(pady=10)

def final_submit():
    s = calc_score()
    # 生成报告到桌面
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    report_path = os.path.join(desktop, "考试评估报告.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"模拟考试报告\n得分：{s}/100\n错题数：{len(wrong_list)}\n")
        for w in wrong_list:
            f.write(f"第{w[0]}题：{w[1]}\n正确：{w[2]} 你的：{w[3]}\n")
    # 显示考试结束
    end_win = tk.Toplevel(root)
    end_win.attributes('-fullscreen', True)
    end_win.configure(bg='black')
    tk.Label(end_win, text="考试结束", font=('微软雅黑',60,'bold'), fg='white', bg='black').pack(expand=True)
    root.destroy()
    # 15秒退出
    end_win.after(15000, lambda: exit())
    end_win.mainloop()

# ---------------------- 启动 ----------------------
if __name__=="__main__":
    login()