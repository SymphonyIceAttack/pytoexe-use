import tkinter as tk
from tkinter import messagebox

# 时间设置（秒）
WORK_TIME = 25 * 60
BREAK_TIME = 5 * 60

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("番茄时钟")
        self.root.geometry("350x300")
        self.root.resizable(False, False)

        self.is_running = False
        self.is_work = True
        self.time_left = WORK_TIME

        # 标题
        self.label_title = tk.Label(root, text="专注时间", font=("微软雅黑", 18))
        self.label_title.pack(pady=10)

        # 时间显示
        self.label_time = tk.Label(root, text=self.format_time(self.time_left),
                                   font=("Arial", 40), fg="red")
        self.label_time.pack(pady=10)

        # 按钮
        self.btn_start = tk.Button(root, text="开始", width=10, command=self.start)
        self.btn_start.pack(pady=5)

        self.btn_pause = tk.Button(root, text="暂停", width=10, command=self.pause)
        self.btn_pause.pack(pady=5)

        self.btn_reset = tk.Button(root, text="重置", width=10, command=self.reset)
        self.btn_reset.pack(pady=5)

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def update_timer(self):
        if self.is_running:
            if self.time_left > 0:
                self.time_left -= 1
                self.label_time.config(text=self.format_time(self.time_left))
                self.root.after(1000, self.update_timer)
            else:
                self.switch_mode()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.update_timer()

    def pause(self):
        self.is_running = False

    def reset(self):
        self.is_running = False
        self.is_work = True
        self.time_left = WORK_TIME
        self.label_title.config(text="专注时间")
        self.label_time.config(text=self.format_time(self.time_left))

    def switch_mode(self):
        self.is_running = False
        if self.is_work:
            messagebox.showinfo("时间到", "专注结束，开始休息！")
            self.is_work = False
            self.time_left = BREAK_TIME
            self.label_title.config(text="休息时间")
        else:
            messagebox.showinfo("时间到", "休息结束，开始专注！")
            self.is_work = True
            self.time_left = WORK_TIME
            self.label_title.config(text="专注时间")

        self.label_time.config(text=self.format_time(self.time_left))

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()