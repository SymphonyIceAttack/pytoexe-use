import tkinter as tk
import random
import json
from tkinter import messagebox

# -------------------------- 100%匹配截图配置 --------------------------
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 450
TITLE_BAR_HEIGHT = 40
BACKGROUND_COLOR = "#04302d"
GRID_COLOR = "#1a4538"
TITLE_BG_COLOR = "#0f2d25"
TITLE_STRIP_COLOR = "#184033"
BUTTON_SET_COLOR = "#1f5f30"
BUTTON_START_COLOR = "#589764"
TEXT_WHITE = "#ffffff"
TEXT_YELLOW = "#f9f900"
FONT_LABEL = ("黑体", 14)
FONT_BUTTON_SET = ("黑体", 16, "bold")
FONT_BUTTON_START = ("黑体", 22, "bold")
FONT_NUMBER = ("黑体", 150, "bold")
FONT_TITLE = ("黑体", 20, "bold")
FONT_HISTORY = ("黑体", 14)
CONFIG_FILE = "抽号配置.json"

# -------------------------- 全局变量 --------------------------
is_running = False
min_num = 1
max_num = 100
remaining_numbers = []
draw_history = []
exclude_numbers = []
force_numbers = {}
hidden_window = None
x_offset = 0
y_offset = 0
main_canvas = None
number_text_id = None
history_text_id = None  # 轮次记录文本ID

# -------------------------- 配置文件读写 --------------------------
def load_config():
    global exclude_numbers, force_numbers
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            exclude_numbers = config.get("exclude", [])
            force_numbers = config.get("force", {})
    except FileNotFoundError:
        exclude_numbers = []
        force_numbers = {}

def save_config():
    config = {"exclude": exclude_numbers, "force": force_numbers}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    messagebox.showinfo("提示", "配置保存成功！")

def clear_config():
    global exclude_numbers, force_numbers
    if messagebox.askyesno("确认", "确定要清除所有配置吗？"):
        exclude_numbers = []
        force_numbers = {}
        save_config()
        messagebox.showinfo("提示", "配置已清除！")

# -------------------------- 核心抽号逻辑 --------------------------
def initialize_numbers():
    global remaining_numbers
    remaining_numbers = []
    for num in range(min_num, max_num + 1):
        if num not in exclude_numbers:
            remaining_numbers.append(num)
    random.shuffle(remaining_numbers)

def set_range():
    global min_num, max_num, draw_history
    try:
        min_num = int(entry_min.get())
        max_num = int(entry_max.get())
        if min_num >= max_num:
            messagebox.showerror("错误", "最大编号必须大于最小编号")
            return
        draw_history = []
        initialize_numbers()
        update_number("0")
        update_history_display()
        button_start.config(text="开始", state="normal")
    except ValueError:
        messagebox.showerror("错误", "请输入有效的数字")

def roll_number():
    if is_running:
        current_num = random.randint(min_num, max_num)
        update_number(str(current_num))
        root.after(50, roll_number)

def start_stop_draw():
    global is_running
    if not remaining_numbers and (len(draw_history)+1 not in force_numbers):
        messagebox.showinfo("提示", "所有编号已经抽完！")
        return
    if not is_running:
        is_running = True
        button_start.config(text="停止")
        roll_number()
    else:
        is_running = False
        button_start.config(text="开始")
        current_round = len(draw_history) + 1
        if current_round in force_numbers:
            final_num = force_numbers[current_round]
            if final_num < min_num or final_num > max_num:
                messagebox.showerror("错误", f"第{current_round}轮指定数字{final_num}超出范围")
                return
            if final_num in exclude_numbers:
                messagebox.showerror("错误", f"第{current_round}轮指定数字{final_num}在排除列表中")
                return
            if final_num in remaining_numbers:
                remaining_numbers.remove(final_num)
        else:
            if not remaining_numbers:
                messagebox.showinfo("提示", "所有编号已经抽完！")
                return
            final_num = remaining_numbers.pop()
        update_number(str(final_num))
        draw_history.append(final_num)
        update_history_display()
        if not remaining_numbers and (current_round+1 not in force_numbers):
            button_start.config(state="disabled")

def update_number(text):
    global number_text_id
    if number_text_id is not None:
        main_canvas.delete(number_text_id)
    number_text_id = main_canvas.create_text(
        WINDOW_WIDTH/2,
        (WINDOW_HEIGHT-TITLE_BAR_HEIGHT)/2 + 30,
        text=text,
        font=FONT_NUMBER,
        fill=TEXT_YELLOW,
        anchor="center"
    )

# -------------------------- 更新轮次记录（画布绘制，无底色） --------------------------
def update_history_display():
    global history_text_id
    # 删除旧文本
    if history_text_id is not None:
        main_canvas.delete(history_text_id)
    # 拼接轮次内容
    history_text = ""
    for i, num in enumerate(draw_history, 1):
        history_text += f"第{i}轮：{num}\n"
    # 在画布右上角绘制轮次文字
    history_text_id = main_canvas.create_text(
        450, 15,
        text=history_text.strip(),
        font=FONT_HISTORY,
        fill=TEXT_WHITE,
        anchor="nw"
    )

# -------------------------- 隐藏后台窗口 --------------------------
def open_hidden_window(event=None):
    global hidden_window, entry_exclude, entry_force
    if hidden_window is not None and hidden_window.winfo_exists():
        hidden_window.lift()
        return
    hidden_window = tk.Toplevel(root)
    hidden_window.title("后台设置")
    hidden_window.geometry("500x300")
    hidden_window.resizable(False, False)
    hidden_window.configure(bg="#f0f0f0")
    tk.Label(hidden_window, text="全局排除数字（多个用逗号分隔）：", font=("微软雅黑", 12), bg="#f0f0f0").place(x=20, y=20)
    entry_exclude = tk.Entry(hidden_window, font=("微软雅黑", 12), width=40)
    entry_exclude.place(x=20, y=50)
    entry_exclude.insert(0, ",".join(map(str, exclude_numbers)))
    tk.Label(hidden_window, text="指定轮次（格式：1:5,2:10,3:15）：", font=("微软雅黑", 12), bg="#f0f0f0").place(x=20, y=90)
    entry_force = tk.Entry(hidden_window, font=("微软雅黑", 12), width=40)
    entry_force.place(x=20, y=120)
    force_text = ",".join([f"{k}:{v}" for k, v in force_numbers.items()])
    entry_force.insert(0, force_text)
    tk.Button(hidden_window, text="保存配置", font=("微软雅黑", 12, "bold"), bg="#226633", fg="white", width=10, command=apply_and_save).place(x=50, y=180)
    tk.Button(hidden_window, text="一键清除", font=("微软雅黑", 12, "bold"), bg="#cc3333", fg="white", width=10, command=clear_config).place(x=180, y=180)
    tk.Button(hidden_window, text="关闭", font=("微软雅黑", 12, "bold"), bg="#666666", fg="white", width=10, command=hidden_window.destroy).place(x=310, y=180)
    tk.Label(hidden_window, text="提示：保存配置后需要点击主界面的「设定」按钮生效", font=("微软雅黑", 10), fg="#666666", bg="#f0f0f0").place(x=20, y=240)

def apply_and_save():
    global exclude_numbers, force_numbers
    exclude_text = entry_exclude.get().strip()
    exclude_numbers = []
    if exclude_text:
        try:
            exclude_numbers = list(map(int, exclude_text.split(",")))
        except ValueError:
            messagebox.showerror("错误", "排除数字格式错误，请用逗号分隔整数")
            return
    force_text = entry_force.get().strip()
    force_numbers = {}
    if force_text:
        try:
            items = force_text.split(",")
            for item in items:
                round_num, num = item.split(":")
                force_numbers[int(round_num.strip())] = int(num.strip())
        except ValueError:
            messagebox.showerror("错误", "指定轮次格式错误，请使用 轮次:数字 格式")
            return
    save_config()

# -------------------------- 自定义标题栏 --------------------------
def drag_window(event):
    x = root.winfo_pointerx() - x_offset
    y = root.winfo_pointery() - y_offset
    root.geometry(f"+{x}+{y}")

def press_window(event):
    global x_offset, y_offset
    x_offset = event.x_root - root.winfo_x()
    y_offset = event.y_root - root.winfo_y()

def close_window():
    root.destroy()

# -------------------------- 绘制菱形网格背景 --------------------------
def draw_original_diamond_background():
    canvas = tk.Canvas(
        root,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT-TITLE_BAR_HEIGHT,
        bg=BACKGROUND_COLOR,
        highlightthickness=0
    )
    canvas.place(x=0, y=TITLE_BAR_HEIGHT)
    grid_size = 24
    for x in range(0, WINDOW_WIDTH + grid_size, grid_size):
        for y in range(0, WINDOW_HEIGHT + grid_size, grid_size):
            canvas.create_polygon(
                x, y - grid_size/2,
                x + grid_size/2, y,
                x, y + grid_size/2,
                x - grid_size/2, y,
                fill=GRID_COLOR,
                outline=""
            )
    return canvas

# -------------------------- 主界面搭建 --------------------------
root = tk.Tk()
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
root.overrideredirect(True)
root.resizable(False, False)
root.configure(bg=BACKGROUND_COLOR)

root.bind("<Control-Alt-a>", open_hidden_window)
load_config()

# 标题栏
title_bar = tk.Frame(root, bg=TITLE_BG_COLOR, height=TITLE_BAR_HEIGHT)
title_bar.pack(fill="x")
title_bar.bind("<ButtonPress-1>", press_window)
title_bar.bind("<B1-Motion>", drag_window)
title_strip = tk.Frame(title_bar, bg=TITLE_STRIP_COLOR, height=TITLE_BAR_HEIGHT)
title_strip.place(x=0, y=0, width=610)
title_label = tk.Label(
    title_strip,
    text="武警部队军事训练等级评定考核抽签系统",
    font=FONT_TITLE,
    fg=TEXT_WHITE,
    bg=TITLE_STRIP_COLOR
)
title_label.place(x=20, y=3)
close_btn = tk.Button(
    title_bar,
    text="×",
    font=("黑体", 15),
    bg=TITLE_BG_COLOR,
    fg=TEXT_WHITE,
    bd=0,
    command=close_window,
    activebackground=TITLE_BG_COLOR,
    activeforeground=TEXT_WHITE
)
close_btn.place(x=WINDOW_WIDTH-45, y=0, width=45, height=TITLE_BAR_HEIGHT)

# 背景画布
main_canvas = draw_original_diamond_background()

# 左侧文字：画布直接绘制，无任何底色
main_canvas.create_text(15, 30, text="最小编号", font=FONT_LABEL, fill=TEXT_WHITE, anchor="w")
main_canvas.create_text(15, 75, text="最大编号", font=FONT_LABEL, fill=TEXT_WHITE, anchor="w")

# 输入框
entry_min = tk.Entry(
    root,
    font=FONT_LABEL,
    width=8,
    bd=1,
    relief="solid",
    bg=BACKGROUND_COLOR,
    fg=TEXT_WHITE,
    insertbackground=TEXT_WHITE
)
entry_min.place(x=100, y=60)
entry_min.insert(0, "1")

entry_max = tk.Entry(
    root,
    font=FONT_LABEL,
    width=8,
    bd=1,
    relief="solid",
    bg=BACKGROUND_COLOR,
    fg=TEXT_WHITE,
    insertbackground=TEXT_WHITE
)
entry_max.place(x=100, y=105)
entry_max.insert(0, "100")

# 设定按钮
button_set = tk.Button(
    root,
    text="设定",
    font=FONT_BUTTON_SET,
    bg=BUTTON_SET_COLOR,
    fg=TEXT_WHITE,
    width=10,
    height=1,
    relief="flat",
    bd=0,
    command=set_range
)
button_set.place(x=15, y=140)

# 底部开始按钮
button_start = tk.Button(
    root,
    text="开始",
    font=FONT_BUTTON_START,
    bg=BUTTON_START_COLOR,
    fg=TEXT_WHITE,
    width=20,
    height=1,
    relief="flat",
    bd=0,
    command=start_stop_draw
)
button_start.place(relx=0.5,y=410, anchor="center")

# 初始化内容
update_number("0")
initialize_numbers()
update_history_display()

root.mainloop()
