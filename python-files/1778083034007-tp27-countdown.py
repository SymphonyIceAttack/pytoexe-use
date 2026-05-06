import tkinter as tk
from datetime import datetime, timedelta

# ---------- 配置 ----------
TARGET_MONTH = 6
TARGET_DAY = 7
TARGET_HOUR = 0
TARGET_MINUTE = 0
# --------------------------

def get_next_gaokao():
    """获取未来最近的高考日期（6月7日 00:00:00）"""
    now = datetime.now()
    target = datetime(now.year, TARGET_MONTH, TARGET_DAY,
                      TARGET_HOUR, TARGET_MINUTE)
    if now > target:
        target = datetime(now.year + 1, TARGET_MONTH, TARGET_DAY,
                          TARGET_HOUR, TARGET_MINUTE)
    return target

def update_time():
    target = get_next_gaokao()
    delta = target - datetime.now()
    if delta.total_seconds() <= 0:
        label.config(text="高考已开始！")
    else:
        days = delta.days
        hours, rem = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        label.config(text=f"距高考: {days}天 {hours:02d}:{minutes:02d}:{seconds:02d}")
    root.after(1000, update_time)

def on_enter(event):
    """鼠标进入时改变光标"""
    root.config(cursor="fleur")

def on_leave(event):
    root.config(cursor="arrow")

def start_move(event):
    root.x = event.x
    root.y = event.y

def do_move(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")

def show_menu(event):
    menu.post(event.x_root, event.y_root)

def exit_app():
    root.destroy()

# ---------- 创建窗口 ----------
root = tk.Tk()
root.overrideredirect(True)          # 无边框
root.attributes("-topmost", False)   # 不置顶
root.wm_attributes("-transparentcolor", "white")  # 白色透明，可用于背景
root.configure(bg='white')           # 设置透明色底色

# 设置窗口大小和初始位置
window_width = 320
window_height = 60
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = screen_width - window_width - 50   # 靠右下角
y = screen_height - window_height - 80
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

# ---------- 显示标签 ----------
# 选用不易与背景冲突的字体颜色，白色透明背景会让这个颜色显示在桌面上
label = tk.Label(
    root,
    text="",
    font=("Microsoft YaHei", 16, "bold"),
    fg="#00AAFF",          # 亮蓝色文字
    bg="white"             # 与透明色一致
)
label.pack(expand=True, fill='both')
label.bind("<Button-1>", start_move)
label.bind("<B1-Motion>", do_move)
label.bind("<Enter>", on_enter)
label.bind("<Leave>", on_leave)
label.bind("<Button-3>", show_menu)   # 右键菜单

# 也可拖动整个窗口
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", do_move)

# ---------- 右键菜单 ----------
menu = tk.Menu(root, tearoff=0)
menu.add_command(label="退出", command=exit_app)

# ---------- 启动倒计时 ----------
update_time()
root.mainloop()