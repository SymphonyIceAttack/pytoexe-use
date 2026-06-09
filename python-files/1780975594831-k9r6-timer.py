import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading

class CountdownTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("倒计时工具")
        self.root.geometry("450x280")
        self.root.resizable(False, False)

        # 计时变量
        self.total_seconds = 0
        self.running = False
        self.timer_thread = None

        # 标题
        title_label = ttk.Label(root, text="倒计时", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=10)

        # 输入框框架
        input_frame = ttk.Frame(root)
        input_frame.pack(pady=10)

        # 小时
        ttk.Label(input_frame, text="小时:", font=("微软雅黑", 12)).grid(row=0, column=0, padx=5)
        self.hour_entry = ttk.Entry(input_frame, width=5, font=("微软雅黑", 14))
        self.hour_entry.grid(row=0, column=1, padx=5)
        self.hour_entry.insert(0, "0")

        # 分钟
        ttk.Label(input_frame, text="分钟:", font=("微软雅黑", 12)).grid(row=0, column=2, padx=5)
        self.min_entry = ttk.Entry(input_frame, width=5, font=("微软雅黑", 14))
        self.min_entry.grid(row=0, column=3, padx=5)
        self.min_entry.insert(0, "0")

        # 秒
        ttk.Label(input_frame, text="秒:", font=("微软雅黑", 12)).grid(row=0, column=4, padx=5)
        self.sec_entry = ttk.Entry(input_frame, width=5, font=("微软雅黑", 14))
        self.sec_entry.grid(row=0, column=5, padx=5)
        self.sec_entry.insert(0, "0")

        # 时间显示
        self.time_label = ttk.Label(root, text="00:00:00", font=("微软雅黑", 36, "bold"))
        self.time_label.pack(pady=15)

        # 按钮框架
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="开始倒计时", command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_timer, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=10)

        self.reset_btn = ttk.Button(btn_frame, text="重置", command=self.reset_timer)
        self.reset_btn.grid(row=0, column=2, padx=10)

    def get_total_seconds(self):
        """获取输入的总秒数"""
        try:
            h = int(self.hour_entry.get())
            m = int(self.min_entry.get())
            s = int(self.sec_entry.get())
            return h * 3600 + m * 60 + s
        except ValueError:
            messagebox.showerror("错误", "请输入有效数字！")
            return -1

    def update_display(self):
        """更新界面时间显示"""
        h = self.total_seconds // 3600
        m = (self.total_seconds % 3600) // 60
        s = self.total_seconds % 60
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    def countdown(self):
        """倒计时核心逻辑"""
        while self.total_seconds > 0 and self.running:
            time.sleep(1)
            self.total_seconds -= 1
            self.root.after(0, self.update_display)

        # 倒计时结束
        if self.total_seconds <= 0 and self.running:
            self.running = False
            self.root.after(0, self.time_up)
            self.root.after(0, self.reset_ui)

    def start_timer(self):
        """开始按钮"""
        if self.running:
            return

        sec = self.get_total_seconds()
        if sec <= 0:
            return

        self.total_seconds = sec
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.hour_entry.config(state=tk.DISABLED)
        self.min_entry.config(state=tk.DISABLED)
        self.sec_entry.config(state=tk.DISABLED)

        self.timer_thread = threading.Thread(target=self.countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def stop_timer(self):
        """停止按钮"""
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def reset_timer(self):
        """重置按钮"""
        self.running = False
        self.total_seconds = 0
        self.update_display()
        self.reset_ui()

    def reset_ui(self):
        """重置界面状态"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.hour_entry.config(state=tk.NORMAL)
        self.min_entry.config(state=tk.NORMAL)
        self.sec_entry.config(state=tk.NORMAL)

    def time_up(self):
        """时间到弹窗提醒"""
        messagebox.showinfo("提醒", "⏰ 倒计时时间到！")

if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownTimer(root)
    root.mainloop()