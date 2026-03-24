import tkinter as tk
from tkinter import ttk, messagebox
from datetime import timedelta
import winsound  # Windows系统提示音

class SimpleCountdown:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面倒计时")
        self.root.geometry("420x260")
        self.root.resizable(False, False)
        
        self.total_seconds = 0
        self.running = False
        self.timer_id = None
        
        # 界面
        self.setup_ui()

    def setup_ui(self):
        # 标题
        ttk.Label(self.root, text="倒计时工具", font=("微软雅黑", 16)).pack(pady=10)
        
        # 时间输入
        frame = ttk.Frame(self.root)
        frame.pack(pady=5)
        
        ttk.Label(frame, text="时", font=("微软雅黑", 12)).grid(row=0, column=1, padx=5)
        ttk.Label(frame, text="分", font=("微软雅黑", 12)).grid(row=0, column=3, padx=5)
        ttk.Label(frame, text="秒", font=("微软雅黑", 12)).grid(row=0, column=5, padx=5)
        
        self.h = tk.StringVar(value="00")
        self.m = tk.StringVar(value="00")
        self.s = tk.StringVar(value="00")
        
        ttk.Entry(frame, textvariable=self.h, width=3, font=("微软雅黑", 16), justify="center").grid(row=0, column=0, padx=5)
        ttk.Entry(frame, textvariable=self.m, width=3, font=("微软雅黑", 16), justify="center").grid(row=0, column=2, padx=5)
        ttk.Entry(frame, textvariable=self.s, width=3, font=("微软雅黑", 16), justify="center").grid(row=0, column=4, padx=5)
        
        # 显示
        self.display = ttk.Label(self.root, text="00:00:00", font=("微软雅黑", 36))
        self.display.pack(pady=15)
        
        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="开始", command=self.start, width=8).grid(row=0, column=0, padx=8)
        ttk.Button(btn_frame, text="暂停", command=self.pause, width=8).grid(row=0, column=1, padx=8)
        ttk.Button(btn_frame, text="重置", command=self.reset, width=8).grid(row=0, column=2, padx=8)

    def get_seconds(self):
        try:
            return int(self.h.get())*3600 + int(self.m.get())*60 + int(self.s.get())
        except:
            return 0

    def update(self):
        if self.running and self.total_seconds > 0:
            self.total_seconds -= 1
            self.display.config(text=str(timedelta(seconds=self.total_seconds)))
            self.timer_id = self.root.after(1000, self.update)
        elif self.total_seconds <= 0:
            self.display.config(text="时间到！")
            winsound.Beep(1000, 500)  # 提示音
            messagebox.showinfo("提示", "倒计时结束！")
            self.running = False

    def start(self):
        if not self.running:
            if self.total_seconds == 0:
                self.total_seconds = self.get_seconds()
                if self.total_seconds <= 0:
                    messagebox.showwarning("警告", "请输入有效时间！")
                    return
            self.running = True
            self.update()

    def pause(self):
        self.running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

    def reset(self):
        self.pause()
        self.total_seconds = 0
        self.display.config(text="00:00:00")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleCountdown(root)
    root.mainloop()