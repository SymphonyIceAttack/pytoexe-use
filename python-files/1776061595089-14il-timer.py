import tkinter as tk
import time

class MultiTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("12宫格计时器")
        
        # 设置每个按钮的状态：None 表示未开始，或者存储开始的时间戳
        self.start_times = [None] * 12
        self.buttons = []
        
        # 布局：4列 x 3行
        for i in range(12):
            row = i // 4
            col = i % 4
            
            btn = tk.Button(
                root, 
                text="开始计时", 
                font=("Arial", 12),
                width=15, 
                height=5,
                command=lambda idx=i: self.toggle_timer(idx)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.buttons.append(btn)
        
        # 启动刷新循环
        self.update_clocks()

    def toggle_timer(self, idx):
        # 如果还没开始，就记录当前时间；如果已经开始，则重置
        if self.start_times[idx] is None:
            self.start_times[idx] = time.time()
        else:
            self.start_times[idx] = None
            self.buttons[idx].config(text="开始计时")

    def update_clocks(self):
        for i in range(12):
            if self.start_times[i] is not None:
                # 计算经过的时间
                elapsed = int(time.time() - self.start_times[i])
                mins, secs = divmod(elapsed, 60)
                # 格式化为 分:秒
                time_str = f"{mins:02d}:{secs:02d}"
                self.buttons[i].config(text=time_str)
        
        # 每隔 100 毫秒刷新一次界面
        self.root.after(100, self.update_clocks)

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiTimerApp(root)
    root.mainloop()