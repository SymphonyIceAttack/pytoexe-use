import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import threading

class CountdownTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("倒计时工具")
        self.root.geometry("480x320")
        self.root.resizable(True, True)

        self.total_seconds = 0
        self.running = False
        self.timer_thread = None

        title_label = ttk.Label(root, text="倒计时", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=12)

        input_frame = ttk.Frame(root)
        input_frame.pack(pady=8)

        self.hour_entry = ttk.Entry(input_frame, width=6, font=("微软雅黑", 14), justify=tk.CENTER)
        self.hour_entry.grid(row=0, column=0, padx=4)
        self.hour_entry.insert(0, "0")
        ttk.Label(input_frame, text="小时", font=("微软雅黑", 12)).grid(row=0, column=1, padx=8)

        self.min_entry = ttk.Entry(input_frame, width=6, font=("微软雅黑", 14), justify=tk.CENTER)
        self.min_entry.grid(row=0, column=2, padx=4)
        self.min_entry.insert(0, "0")
        ttk.Label(input_frame, text="分钟", font=("微软雅黑", 12)).grid(row=0, column=3, padx=8)

        self.sec_entry = ttk.Entry(input_frame, width=6, font=("微软雅黑", 14), justify=tk.CENTER)
        self.sec_entry.grid(row=0, column=4, padx=4)
        self.sec_entry.insert(0, "0")
        ttk.Label(input_frame, text="秒", font=("微软雅黑", 12)).grid(row=0, column=5, padx=8)

        for entry in [self.hour_entry, self.min_entry, self.sec_entry]:
            entry.bind("<FocusOut>", self.fill_zero)
            entry.bind("<KeyRelease>", self.live_preview)

        self.time_label = ttk.Label(root, text="00:00:00", font=("微软雅黑", 40, "bold"))
        self.time_label.pack(pady=20)

        btn_frame1 = ttk.Frame(root)
        btn_frame1.pack(pady=6)

        self.start_btn = ttk.Button(btn_frame1, text="开始倒计时", command=self.start_timer)
        self.start_btn.grid(row=0, column=0, padx=8)

        self.stop_btn = ttk.Button(btn_frame1, text="停止", command=self.stop_timer, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=8)

        self.reset_btn = ttk.Button(btn_frame1, text="重置", command=self.reset_timer)
        self.reset_btn.grid(row=0, column=2, padx=8)

        btn_frame2 = ttk.Frame(root)
        btn_frame2.pack(pady=12)
        ttk.Button(btn_frame2, text="修改窗口尺寸(像素)", command=self.change_window_size).grid(row=0, column=0)

    def fill_zero(self, event):
        entry = event.widget
        content = entry.get().strip()
        if not content or not content.isdigit():
            entry.delete(0, tk.END)
            entry.insert(0, "0")
        self.live_preview(None)

    def live_preview(self, event):
        try:
            h = int(self.hour_entry.get())
            m = int(self.min_entry.get())
            s = int(self.sec_entry.get())
        except:
            h = m = s = 0
        self.total_seconds = h * 3600 + m * 60 + s
        self.update_display()

    def update_display(self):
        h = self.total_seconds // 3600
        m = (self.total_seconds % 3600) // 60
        s = self.total_seconds % 60
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    def countdown(self):
        while self.total_seconds > 0 and self.running:
            time.sleep(1)
            self.total_seconds -= 1
            self.root.after(0, self.update_display)
        if self.total_seconds <= 0 and self.running:
            self.running = False
            self.root.after(0, self.time_up)
            self.root.after(0, self.reset_ui)

    def start_timer(self):
        if self.running:
            return
        try:
            h = int(self.hour_entry.get())
            m = int(self.min_entry.get())
            s = int(self.sec_entry.get())
        except:
            messagebox.showerror("错误", "请输入合法数字！")
            return
        self.total_seconds = h * 3600 + m * 60 + s
        if self.total_seconds <= 0:
            messagebox.showwarning("提示", "请设置大于0的倒计时时长")
            return
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
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def reset_timer(self):
        self.running = False
        self.total_seconds = 0
        for e in [self.hour_entry, self.min_entry, self.sec_entry]:
            e.delete(0, tk.END)
            e.insert(0, "0")
        self.update_display()
        self.reset_ui()

    def reset_ui(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        for e in [self.hour_entry, self.min_entry, self.sec_entry]:
            e.config(state=tk.NORMAL)

    def time_up(self):
        messagebox.showinfo("提醒", "⏰ 倒计时时间到！")

    def change_window_size(self):
        try:
            w = simpledialog.askinteger("宽度", "输入窗口宽度(像素):", minvalue=200)
            if not w: return
            h = simpledialog.askinteger("高度", "输入窗口高度(像素):", minvalue=200)
            if not h: return
            self.root.geometry(f"{w}x{h}")
        except:
            messagebox.showerror("错误", "输入无效！")

if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownTimer(root)
    root.mainloop()