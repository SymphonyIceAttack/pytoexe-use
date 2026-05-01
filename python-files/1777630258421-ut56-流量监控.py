import psutil
import tkinter as tk

class TrafficMonitor:
    def __init__(self, win):
        self.win = win
        self.win.title("网速流量监控")
        self.win.geometry("190x80")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)

        self.lb_up = tk.Label(win, text="上行：0.00 KB/s", font=("微软雅黑", 12))
        self.lb_down = tk.Label(win, text="下行：0.00 KB/s", font=("微软雅黑", 12))
        self.lb_up.pack()
        self.lb_down.pack()

        self.last = psutil.net_io_counters()
        self.refresh()

    def refresh(self):
        now = psutil.net_io_counters()
        up = (now.bytes_sent - self.last.bytes_sent) / 1024
        down = (now.bytes_recv - self.last.bytes_recv) / 1024
        self.last = now

        self.lb_up.config(text=f"上行：{up:.2f} KB/s")
        self.lb_down.config(text=f"下行：{down:.2f} KB/s")
        self.win.after(1000, self.refresh)

if __name__ == "__main__":
    root = tk.Tk()
    TrafficMonitor(root)
    root.mainloop()