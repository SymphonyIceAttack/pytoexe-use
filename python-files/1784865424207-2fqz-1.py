import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
import ctypes
import subprocess

def set_topmost(window):
    """窗口置顶"""
    hwnd = window.winfo_id()
    ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("定时倒计时工具 - 弹窗提醒/定时关机")
        self.root.geometry("420x320")
        self.root.resizable(False, False)

        self.running = False
        self.timer_thread = None

        self.hour_var = tk.StringVar(value="0")
        self.min_var = tk.StringVar(value="0")
        self.sec_var = tk.StringVar(value="10")
        self.shutdown_var = tk.BooleanVar()
        self.msg_var = tk.StringVar(value="时间到！任务完成")

        self.create_ui()

    def create_ui(self):
        frame_time = ttk.LabelFrame(self.root, text="设置倒计时时长")
        frame_time.pack(pady=10, padx=10, fill="x")

        ttk.Label(frame_time, text="时").grid(row=0, column=0, padx=5, pady=5)
        ttk.Spinbox(frame_time, from_=0, to=99, textvariable=self.hour_var, width=6).grid(row=0, column=1)
        ttk.Label(frame_time, text="分").grid(row=0, column=2, padx=5)
        ttk.Spinbox(frame_time, from_=0, to=59, textvariable=self.min_var, width=6).grid(row=0, column=3)
        ttk.Label(frame_time, text="秒").grid(row=0, column=4, padx=5)
        ttk.Spinbox(frame_time, from_=0, to=59, textvariable=self.sec_var, width=6).grid(row=0, column=5)

        frame_msg = ttk.LabelFrame(self.root, text="弹窗提醒文字")
        frame_msg.pack(pady=5, padx=10, fill="x")
        ttk.Entry(frame_msg, textvariable=self.msg_var, width=50).pack(padx=5, pady=5)

        frame_opt = ttk.Frame(self.root)
        frame_opt.pack(pady=5)
        ttk.Checkbutton(frame_opt, text="倒计时结束自动关机", variable=self.shutdown_var).pack()

        frame_btn = ttk.Frame(self.root)
        frame_btn.pack(pady=15)
        self.start_btn = ttk.Button(frame_btn, text="开始倒计时", command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = ttk.Button(frame_btn, text="停止倒计时", command=self.stop_timer, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=10)

        self.time_label = ttk.Label(self.root, text="等待启动...", font=("微软雅黑", 16, "bold"))
        self.time_label.pack(pady=10)

    def count_down_logic(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.min_var.get())
            s = int(self.sec_var.get())
            total = h * 3600 + m * 60 + s
            if total <= 0:
                self.root.after(0, lambda: messagebox.showerror("错误", "时长必须大于0秒！"))
                self.root.after(0, self.reset_btn)
                return
        except ValueError:
            self.root.after(0, lambda: messagebox.showerror("错误", "请输入纯数字时间！"))
            self.root.after(0, self.reset_btn)
            return

        remain = total
        while remain > 0 and self.running:
            hh = remain // 3600
            mm = (remain % 3600) // 60
            ss = remain % 60
            self.root.after(0, lambda t=f"剩余 {hh:02d}:{mm:02d}:{ss:02d}": self.time_label.config(text=t))
            time.sleep(1)
            remain -= 1

        if self.running:
            self.root.after(0, self.alert_popup)
            if self.shutdown_var.get():
                subprocess.run(["shutdown", "/s", "/t", "10", "/c", "倒计时结束，10秒后自动关机，可输入shutdown -a取消"])
        self.root.after(0, self.reset_btn)

    def alert_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("提醒通知")
        popup.geometry("300x120")
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        popup.geometry(f"300x120+{screen_w - 320}+{screen_h - 180}")
        set_topmost(popup)

        ttk.Label(popup, text=self.msg_var.get(), font=("微软雅黑", 12)).pack(pady=20)
        ttk.Button(popup, text="知道了", command=popup.destroy).pack()

    def start_timer(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.timer_thread = threading.Thread(target=self.count_down_logic, daemon=True)
        self.timer_thread.start()

    def stop_timer(self):
        self.running = False
        self.time_label.config(text="已手动停止")
        self.reset_btn()

    def reset_btn(self):
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()