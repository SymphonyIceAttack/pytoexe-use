import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import threading
import time

# 提醒检查线程
def reminder_checker():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for item in reminders[:]:
            if item["time"] == now:
                messagebox.showinfo("提醒", item["text"])
                reminders.remove(item)
        time.sleep(30)

# 添加提醒
def add_reminder():
    text = text_entry.get().strip()
    time_str = time_entry.get().strip()

    if not text or not time_str:
        messagebox.showwarning("提示", "提醒内容和时间不能为空！")
        return

    try:
        datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except:
        messagebox.showerror("错误", "时间格式错误！\n正确例子：2026-03-26 20:30")
        return

    reminders.append({"text": text, "time": time_str})
    listbox.insert(tk.END, f"{time_str} - {text}")
    text_entry.delete(0, tk.END)
    time_entry.delete(0, tk.END)

# GUI
root = tk.Tk()
root.title("桌面提醒小工具")
root.geometry("420x380")

reminders = []

tk.Label(root, text="提醒内容：").pack()
text_entry = tk.Entry(root, width=40)
text_entry.pack()

tk.Label(root, text="提醒时间（格式：2026-03-26 20:30）：").pack()
time_entry = tk.Entry(root, width=40)
time_entry.pack()

tk.Button(root, text="添加提醒", width=20, command=add_reminder).pack(pady=10)

tk.Label(root, text="提醒列表：").pack()
listbox = tk.Listbox(root, width=55, height=10)
listbox.pack()

# 启动后台检测线程
thread = threading.Thread(target=reminder_checker, daemon=True)
thread.start()

root.mainloop()