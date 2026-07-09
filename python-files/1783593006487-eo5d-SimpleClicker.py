import tkinter as tk
import pyautogui
import time
import json
from datetime import datetime

CONFIG = "config.json"

class Clicker:
    def __init__(self, root):
        self.root = root
        self.root.title("傻瓜式点击器")
        self.root.geometry("450x600")
        self.coords = []
        self.times = []
        self.running = False
        self.load()
        self.build_ui()

    def build_ui(self):
        # 坐标区
        tk.Label(root, text="1. 添加坐标（先移鼠标到点位，再点按钮）").pack(pady=5)
        tk.Button(root, text="添加当前鼠标位置", command=self.add_coord).pack()
        self.coord_list = tk.Listbox(root, height=6)
        self.coord_list.pack(fill="x", padx=10, pady=5)
        tk.Button(root, text="删除选中", command=self.del_coord).pack()

        # 参数区
        tk.Label(root, text="2. 点击设置").pack(pady=5)
        frame = tk.Frame(root)
        frame.pack()
        tk.Label(frame, text="间隔(ms):").grid(row=0, column=0)
        self.interval = tk.Entry(frame, width=8)
        self.interval.insert(0, "500")
        self.interval.grid(row=0, column=1)
        tk.Label(frame, text="次数(0=无限):").grid(row=1, column=0)
        self.count = tk.Entry(frame, width=8)
        self.count.insert(0, "1")
        self.count.grid(row=1, column=1)

        # 定时区
        tk.Label(root, text="3. 每日定时（至少4个，格式HH:MM）").pack(pady=5)
        frame2 = tk.Frame(root)
        frame2.pack()
        self.time_entry = tk.Entry(frame2, width=8)
        self.time_entry.grid(row=0, column=0)
        tk.Button(frame2, text="添加时间", command=self.add_time).grid(row=0, column=1)
        self.time_list = tk.Listbox(root, height=4)
        self.time_list.pack(fill="x", padx=10)

        # 控制区
        tk.Button(root, text="▶ 开始点击", command=self.start).pack(pady=10)
        tk.Button(root, text="■ 停止", command=self.stop).pack()
        self.log = tk.Text(root, height=6, state="disabled")
        self.log.pack(fill="x", padx=10, pady=5)
        self.refresh()
        self.check_time()  # 启动定时检查

    def log_msg(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def add_coord(self):
        x, y = pyautogui.position()
        self.coords.append([x, y])
        self.save()
        self.refresh()
        self.log_msg(f"添加坐标({x},{y})")

    def del_coord(self):
        sel = self.coord_list.curselection()
        if sel:
            del self.coords[sel[0]]
            self.save()
            self.refresh()

    def add_time(self):
        t = self.time_entry.get()
        if len(t.split(":")) == 2:
            self.times.append(t)
            self.save()
            self.refresh()
            self.log_msg(f"添加定时{t}")

    def refresh(self):
        self.coord_list.delete(0, "end")
        for x, y in self.coords:
            self.coord_list.insert("end", f"X:{x} Y:{y}")
        self.time_list.delete(0, "end")
        for t in sorted(self.times):
            self.time_list.insert("end", t)

    def start(self):
        if len(self.coords) == 0:
            self.log_msg("请先加坐标！")
            return
        self.running = True
        self.log_msg("开始运行")
        import threading
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        gap = float(self.interval.get()) / 1000
        cnt = int(self.count.get())
        run_cnt = 0
        while self.running:
            for x, y in self.coords:
                if not self.running:
                    break
                pyautogui.click(x, y)
                self.log_msg(f"点击({x},{y})")
                time.sleep(gap)
            run_cnt += 1
            if cnt != 0 and run_cnt >= cnt:
                self.stop()
                break

    def stop(self):
        self.running = False
        self.log_msg("已停止")

    def check_time(self):
        if len(self.times) >= 4 and not self.running:
            now = datetime.now().strftime("%H:%M")
            if now in self.times:
                self.start()
                time.sleep(60)  # 防止重复触发
        self.root.after(1000, self.check_time)  # 每秒检查一次

    def save(self):
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump({"coords": self.coords, "times": self.times}, f, ensure_ascii=False)

    def load(self):
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.coords = data.get("coords", [])
                self.times = data.get("times", [])
        except:
            pass

root = tk.Tk()
Clicker(root)
root.mainloop()