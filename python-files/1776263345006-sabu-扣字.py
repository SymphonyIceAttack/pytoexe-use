import tkinter as tk
from tkinter import ttk
import threading
import time
import ctypes

class BaiHuaShenKouZi:
    def __init__(self, root):
        self.root = root
        self.root.title("白花神扣字")
        self.root.geometry("450x500")
        self.root.configure(bg='#F0F0F0')
        self.root.resizable(False, False)
        
        self.running = False
        self.count = 0
        
        # 标题
        tk.Label(root, text="白花神扣字", bg='#F0F0F0', font=("微软雅黑", 18, "bold"), fg="#003399").pack(pady=10)
        
        # 内容区域
        tk.Label(root, text="扣字内容", bg='#F0F0F0', font=("微软雅黑", 9)).pack(anchor=tk.W, padx=20)
        self.text = tk.Text(root, height=12, font=("微软雅黑", 10))
        self.text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # 快捷短语
        quick_frame = tk.Frame(root, bg='#F0F0F0')
        quick_frame.pack(pady=5)
        for txt in ["为什么沉默是金", "你告诉我", "你是乌龟吗"]:
            tk.Button(quick_frame, text=txt, command=lambda t=txt: self.text.insert(tk.END, t + "\n")).pack(side=tk.LEFT, padx=5)
        
        # 速度设置
        speed_frame = tk.Frame(root, bg='#F0F0F0')
        speed_frame.pack(pady=10)
        tk.Label(speed_frame, text="发送间隔(秒):", bg='#F0F0F0').pack(side=tk.LEFT)
        self.delay_var = tk.DoubleVar(value=0.05)
        tk.Spinbox(speed_frame, from_=0.01, to=0.5, increment=0.01, textvariable=self.delay_var, width=8).pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = tk.Frame(root, bg='#F0F0F0')
        btn_frame.pack(pady=10)
        self.start_btn = tk.Button(btn_frame, text="开始", bg='#4CAF50', fg='white', width=8, command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="停止", bg='#f44336', fg='white', width=8, command=self.stop).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="单发", bg='#2196F3', fg='white', width=8, command=self.send_one).pack(side=tk.LEFT, padx=10)
        
        # 状态
        status_frame = tk.Frame(root, bg='#F0F0F0')
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        self.status_label = tk.Label(status_frame, text="状态: 停止", bg='#F0F0F0', fg='red')
        self.status_label.pack(side=tk.LEFT)
        self.count_label = tk.Label(status_frame, text="发送: 0条", bg='#F0F0F0')
        self.count_label.pack(side=tk.RIGHT)
        
        # 说明
        tk.Label(root, text="本软件为百花神自写", bg='#F0F0F0', fg='gray', font=("微软雅黑", 8)).pack(pady=5)
        
        # 快捷键
        root.bind('<F6>', lambda e: self.start())
        root.bind('<F7>', lambda e: self.stop())
        root.bind('<F8>', lambda e: self.send_one())
        root.attributes('-topmost', True)
    
    def get_lines(self):
        content = self.text.get("1.0", tk.END)
        return [line.strip() for line in content.split('\n') if line.strip()]
    
    def copy_text(self, txt):
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        self.root.update()
    
    def send(self, txt):
        self.copy_text(txt)
        ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
        time.sleep(0.01)
        ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)
        self.count += 1
        self.count_label.config(text=f"发送: {self.count}条")
    
    def send_one(self):
        try:
            txt = self.text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except:
            lines = self.get_lines()
            txt = lines[0] if lines else ""
        if txt:
            self.send(txt)
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.status_label.config(text="状态: 运行中", fg='green')
        threading.Thread(target=self.run, daemon=True).start()
    
    def stop(self):
        self.running = False
        self.status_label.config(text="状态: 停止", fg='red')
    
    def run(self):
        delay = self.delay_var.get()
        while self.running:
            lines = self.get_lines()
            if not lines:
                self.stop()
                break
            for line in lines:
                if not self.running:
                    break
                self.send(line)
                time.sleep(delay)

if __name__ == "__main__":
    root = tk.Tk()
    BaiHuaShenKouZi(root)
    root.mainloop()