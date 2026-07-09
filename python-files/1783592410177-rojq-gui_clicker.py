import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time
import datetime
import json
import keyboard  # 用于全局热键

CONFIG_FILE = "config_gui.json"

class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化点击器 By AI")
        self.root.geometry("550x650")
        self.root.resizable(False, False)

        self.coords = []
        self.schedule_times = []
        self.running = False
        self.hotkey_listening = False

        self.load_config()
        self.setup_ui()
        self.start_hotkey_listener()

    def setup_ui(self):
        # --- 坐标列表 ---
        frame_coords = ttk.LabelFrame(self.root, text="坐标列表 (热键: Ctrl+C 添加当前鼠标位置)")
        frame_coords.pack(fill="x", padx=10, pady=5)
        
        self.tree = ttk.Treeview(frame_coords, columns=("x", "y"), show="headings", height=8)
        self.tree.heading("x", text="X 坐标")
        self.tree.heading("y", text="Y 坐标")
        self.tree.column("x", width=150, anchor="center")
        self.tree.column("y", width=150, anchor="center")
        self.tree.pack(side="left", padx=5, pady=5)

        btn_frame = ttk.Frame(frame_coords)
        btn_frame.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="删除选中", command=self.delete_coord).pack(pady=5)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_coords).pack(pady=5)

        # --- 参数设置 ---
        frame_params = ttk.LabelFrame(self.root, text="点击参数")
        frame_params.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_params, text="点击间隔(ms):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.interval_entry = ttk.Entry(frame_params, width=10)
        self.interval_entry.insert(0, "500")
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_params, text="执行次数(0=无限):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.count_entry = ttk.Entry(frame_params, width=10)
        self.count_entry.insert(0, "1")
        self.count_entry.grid(row=1, column=1, padx=5, pady=5)

        # --- 定时设置 ---
        frame_schedule = ttk.LabelFrame(self.root, text="每日定时执行 (至少4个)")
        frame_schedule.pack(fill="x", padx=10, pady=5)
        
        self.schedule_enabled = tk.BooleanVar()
        ttk.Checkbutton(frame_schedule, text="启用定时", variable=self.schedule_enabled, command=self.toggle_schedule).grid(row=0, column=0, padx=5, sticky="w")
        
        self.time_entry = ttk.Entry(frame_schedule, width=10)
        self.time_entry.grid(row=0, column=1, padx=5)
        ttk.Button(frame_schedule, text="添加时间(HH:MM)", command=self.add_time).grid(row=0, column=2, padx=5)
        
        self.time_listbox = tk.Listbox(frame_schedule, height=4)
        self.time_listbox.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="we")

        # --- 控制按钮 ---
        frame_control = ttk.Frame(self.root)
        frame_control.pack(pady=10)
        
        self.start_btn = ttk.Button(frame_control, text="▶ 开始运行", command=self.start_clicking, width=15)
        self.start_btn.pack(side="left", padx=10)
        
        self.stop_btn = ttk.Button(frame_control, text="■ 停止", command=self.stop_clicking, width=15, state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        # --- 日志 ---
        frame_log = ttk.LabelFrame(self.root, text="运行日志")
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(frame_log, height=8, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.refresh_ui()

    def refresh_ui(self):
        # 刷新坐标树
        for item in self.tree.get_children():
            self.tree.delete(item)
        for x, y in self.coords:
            self.tree.insert("", "end", values=(x, y))
        
        # 刷新时间列表
        self.time_listbox.delete(0, tk.END)
        for t in sorted(self.schedule_times):
            self.time_listbox.insert(tk.END, t)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def add_coord(self):
        x, y = pyautogui.position()
        self.coords.append([x, y])
        self.save_config()
        self.refresh_ui()
        self.log(f"添加坐标: ({x}, {y})")

    def delete_coord(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        del self.coords[index]
        self.save_config()
        self.refresh_ui()
        self.log("删除选中坐标")

    def clear_coords(self):
        self.coords.clear()
        self.save_config()
        self.refresh_ui()
        self.log("清空坐标列表")

    def add_time(self):
        t = self.time_entry.get()
        try:
            datetime.datetime.strptime(t, "%H:%M")
            if t not in self.schedule_times:
                self.schedule_times.append(t)
                self.save_config()
                self.refresh_ui()
                self.log(f"添加定时: {t}")
        except ValueError:
            messagebox.showerror("错误", "时间格式应为 HH:MM")

    def toggle_schedule(self):
        if self.schedule_enabled.get():
            if len(self.schedule_times) < 4:
                messagebox.showwarning("警告", "定时模式需要至少设置4个时间点！")
                self.schedule_enabled.set(False)
                return
            self.start_schedule_checker()
        else:
            self.log("定时任务已禁用")

    def start_hotkey_listener(self):
        if not self.hotkey_listening:
            keyboard.add_hotkey('ctrl+c', self.add_coord, suppress=True)
            self.hotkey_listening = True
            self.log("热键监听已启动 (Ctrl+C 添加坐标)")

    def start_clicking(self):
        if len(self.coords) == 0:
            messagebox.showwarning("警告", "请先添加坐标！")
            return
        
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        interval = int(self.interval_entry.get()) / 1000.0
        count = int(self.count_entry.get())
        
        thread = threading.Thread(target=self.click_worker, args=(interval, count), daemon=True)
        thread.start()

    def click_worker(self, interval, count):
        self.log("开始执行点击任务...")
        clicked = 0
        while self.running:
            for x, y in self.coords:
                if not self.running:
                    break
                pyautogui.click(x, y)
                self.log(f"点击: ({x}, {y})")
                time.sleep(interval)
            
            clicked += 1
            if count != 0 and clicked >= count:
                self.log("任务完成")
                self.stop_clicking()
                break

    def start_schedule_checker(self):
        def checker():
            while self.schedule_enabled.get() and not self.running:
                now = datetime.datetime.now().strftime("%H:%M")
                if now in self.schedule_times:
                    self.log(f"触发定时任务: {now}")
                    self.root.after(0, self.start_clicking)
                    time.sleep(60)  # 防止一分钟内重复触发
                time.sleep(1)
        threading.Thread(target=checker, daemon=True).start()

    def stop_clicking(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.log("已停止")

    def save_config(self):
        data = {
            "coords": self.coords,
            "times": self.schedule_times
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.coords = data.get("coords", [])
                self.schedule_times = data.get("times", [])
        except FileNotFoundError:
            pass

    def on_closing(self):
        keyboard.remove_all_hotkeys()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()