import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import threading
import time
import pystray
from PIL import Image, ImageDraw

# ===============================
# 创建托盘图标
# ===============================
def create_tray_icon():
    image = Image.new('RGB', (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill="blue")

    menu = pystray.Menu(
        pystray.MenuItem("打开窗口", lambda: show_window()),
        pystray.MenuItem("退出程序", lambda: exit_app())
    )

    icon = pystray.Icon("reminder", image, "提醒小工具", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon

def show_window():
    root.deiconify()

def hide_window():
    root.withdraw()

def exit_app():
    global running
    running = False
    root.destroy()

# ===============================
# 格式化时间：自动加入当前日期
# ===============================
def normalize_time_input(time_str):
    now_date = datetime.now().strftime("%Y-%m-%d")

    # 只有时间 HH:MM
    if len(time_str) == 5 and ":" in time_str:
        return f"{now_date} {time_str}:00"

    # HH:MM:SS
    if len(time_str) == 8 and time_str.count(":") == 2:
        return f"{now_date} {time_str}"

    # 用户自己输入完整日期格式
    return time_str

# ===============================
# 提醒检查线程
# ===============================
def reminder_checker():
    while running:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in reminders[:]:
            if now == item["time"]:
                for i in range(item["repeat"]):
                    messagebox.showinfo("提醒", item["text"])
                    time.sleep(2)
                reminders.remove(item)
        time.sleep(1)

# ===============================
# 添加提醒
# ===============================
def add_reminder():
    text = text_entry.get().strip()
    time_str = time_entry.get().strip()
    repeat = repeat_entry.get().strip()

    if not text or not time_str or not repeat:
        messagebox.showwarning("提示", "不能为空！")
        return

    # 自动补当前日期
    time_str = normalize_time_input(time_str)

    try:
        datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except:
        messagebox.showerror("错误", "时间格式错误！示例：20:30 或 20:30:10")
        return

    try:
        repeat = int(repeat)
    except:
        messagebox.showerror("错误", "提醒次数必须是数字")
        return

    reminders.append({"text": text, "time": time_str, "repeat": repeat})
    listbox.insert(tk.END, f"{time_str} - {text}（次数：{repeat}）")

    text_entry.delete(0, tk.END)
    time_entry.delete(0, tk.END)
    repeat_entry.delete(0, tk.END)

# ===============================
# GUI 主界面
# ===============================
root = tk.Tk()
root.title("桌面提醒小工具")
root.geometry("450x420")

reminders = []
running = True

tk.Label(root, text="提醒内容：").pack()
text_entry = tk.Entry(root, width=45)
text_entry.pack()

tk.Label(root, text="提醒时间（示例：20:30 或 20:30:10）：").pack()
time_entry = tk.Entry(root, width=45)
time_entry.pack()

tk.Label(root, text="提醒次数：").pack()
repeat_entry = tk.Entry(root, width=10)
repeat_entry.pack()

tk.Button(root, text="添加提醒", width=20, command=add_reminder).pack(pady=10)

tk.Label(root, text="提醒列表：").pack()
listbox = tk.Listbox(root, width=60, height=10)
listbox.pack()

# 最小化到托盘
root.protocol("WM_DELETE_WINDOW", hide_window)

# ===============================
# 启动后台线程 & 托盘
# ===============================
threading.Thread(target=reminder_checker, daemon=True).start()
tray_icon = create_tray_icon()

root.mainloop()
running = False
``