import tkinter as tk
from tkinter import ttk, colorchooser
from datetime import datetime

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("计时器")
        self.root.geometry("720x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # 全屏状态
        self.fullscreen = False

        # 状态变量
        self.mode = "正计时"
        self.running = False
        self.paused = False
        self.current_seconds = 0
        self.set_seconds = 0
        self.after_id = None
        self.sys_after_id = None

        # 样式变量
        self.font_color = "#000000"
        self.font_size = 56
        self.bg_color = None

        # 创建菜单栏
        self.create_menu()
        # 创建主界面
        self.create_widgets()
        # 绑定全屏快捷键
        self.root.bind("<F11>", self.toggle_fullscreen)

        self.update_display()
        self.update_system_time()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 窗口菜单
        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="窗口", menu=window_menu)

        window_menu.add_command(label="最小化", command=self.minimize_window)
        window_menu.add_separator()
        window_menu.add_command(label="全屏", command=self.enter_fullscreen)
        window_menu.add_command(label="退出全屏", command=self.exit_fullscreen)
        window_menu.add_separator()
        window_menu.add_command(label="切换全屏 (F11)", command=self.toggle_fullscreen)

        # 帮助菜单（可选）
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="快捷键: F11 切换全屏", command=lambda: None)

    def minimize_window(self):
        """最小化窗口"""
        self.root.iconify()

    def enter_fullscreen(self):
        """进入全屏"""
        self.fullscreen = True
        self.root.attributes("-fullscreen", True)
        # 全屏时允许调整大小（适应屏幕）
        self.root.resizable(True, True)

    def exit_fullscreen(self):
        """退出全屏"""
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)
        self.root.resizable(False, False)
        self.root.geometry("720x550")  # 恢复原始尺寸

    def toggle_fullscreen(self, event=None):
        """切换全屏状态"""
        if self.fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    # ---------- 创建界面组件 ----------
    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # 系统时间
        self.sys_time_label = tk.Label(main_frame, text="", font=("Arial", 12),
                                       fg="#888888", bg="#f0f0f0")
        self.sys_time_label.pack(pady=(0, 5))

        # 模式切换
        mode_frame = tk.Frame(main_frame, bg="#f0f0f0")
        mode_frame.pack(pady=2)

        self.mode_var = tk.StringVar(value="正计时")
        rb1 = tk.Radiobutton(mode_frame, text="正计时", variable=self.mode_var,
                             value="正计时", command=self.switch_mode,
                             font=("Arial", 11), bg="#f0f0f0", selectcolor="#d0d0d0")
        rb1.pack(side=tk.LEFT, padx=15)
        rb2 = tk.Radiobutton(mode_frame, text="倒计时", variable=self.mode_var,
                             value="倒计时", command=self.switch_mode,
                             font=("Arial", 11), bg="#f0f0f0", selectcolor="#d0d0d0")
        rb2.pack(side=tk.LEFT, padx=15)

        # 时间显示
        self.time_label = tk.Label(main_frame, text="00:00:00",
                                   font=("Arial", self.font_size, "bold"),
                                   fg=self.font_color, bg="#f0f0f0",
                                   bd=0, highlightthickness=0)
        self.time_label.pack(pady=15)

        # 设置时间
        set_frame = tk.Frame(main_frame, bg="#f0f0f0")
        set_frame.pack(pady=8)

        tk.Label(set_frame, text="时", font=("Arial", 11), bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.hour_entry = tk.Spinbox(set_frame, from_=0, to=99, width=4,
                                     font=("Arial", 13), justify="center",
                                     format="%02.0f", bg="white")
        self.hour_entry.pack(side=tk.LEFT, padx=(0, 12))
        self.hour_entry.delete(0, tk.END)
        self.hour_entry.insert(0, "00")

        tk.Label(set_frame, text="分", font=("Arial", 11), bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.min_entry = tk.Spinbox(set_frame, from_=0, to=59, width=4,
                                    font=("Arial", 13), justify="center",
                                    format="%02.0f", bg="white")
        self.min_entry.pack(side=tk.LEFT, padx=(0, 12))
        self.min_entry.delete(0, tk.END)
        self.min_entry.insert(0, "00")

        tk.Label(set_frame, text="秒", font=("Arial", 11), bg="#f0f0f0").pack(side=tk.LEFT, padx=2)
        self.sec_entry = tk.Spinbox(set_frame, from_=0, to=59, width=4,
                                    font=("Arial", 13), justify="center",
                                    format="%02.0f", bg="white")
        self.sec_entry.pack(side=tk.LEFT)
        self.sec_entry.delete(0, tk.END)
        self.sec_entry.insert(0, "00")

        # 控制按钮
        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.pack(pady=12)

        self.start_btn = tk.Button(btn_frame, text="开始", command=self.start_timer,
                                   width=8, height=1, font=("Arial", 11, "bold"),
                                   bg="#4CAF50", fg="white", relief=tk.RAISED, bd=2)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.pause_btn = tk.Button(btn_frame, text="暂停", command=self.pause_timer,
                                   width=8, height=1, font=("Arial", 11, "bold"),
                                   bg="#FF9800", fg="white", relief=tk.RAISED, bd=2,
                                   state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=10)

        self.reset_btn = tk.Button(btn_frame, text="重置", command=self.reset_timer,
                                   width=8, height=1, font=("Arial", 11, "bold"),
                                   bg="#f44336", fg="white", relief=tk.RAISED, bd=2)
        self.reset_btn.pack(side=tk.LEFT, padx=10)

        # 样式设置
        style_frame = tk.LabelFrame(main_frame, text=" 样式设置 ", font=("Arial", 10, "bold"),
                                    bg="#f0f0f0", fg="#333333", padx=15, pady=10)
        style_frame.pack(fill=tk.X, pady=8)

        row1 = tk.Frame(style_frame, bg="#f0f0f0")
        row1.pack(fill=tk.X, pady=3)

        tk.Label(row1, text="样式:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.style_combo = ttk.Combobox(row1, values=["默认", "暗黑", "蓝色"], state="readonly",
                                        width=8)
        self.style_combo.set("默认")
        self.style_combo.pack(side=tk.LEFT, padx=5)
        self.style_combo.bind("<<ComboboxSelected>>", self.change_style)

        tk.Label(row1, text="字体颜色:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT, padx=(15,5))
        self.color_combo = ttk.Combobox(row1, values=["黑色", "红色", "蓝色", "绿色", "自定义..."],
                                        state="readonly", width=10)
        self.color_combo.set("黑色")
        self.color_combo.pack(side=tk.LEFT, padx=5)
        self.color_combo.bind("<<ComboboxSelected>>", self.change_color)

        tk.Label(row1, text="字体大小:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT, padx=(15,5))
        self.size_spinbox = tk.Spinbox(row1, from_=20, to=100, width=5,
                                       font=("Arial", 11), justify="center")
        self.size_spinbox.delete(0, tk.END)
        self.size_spinbox.insert(0, str(self.font_size))
        self.size_spinbox.pack(side=tk.LEFT, padx=5)
        tk.Label(row1, text="px", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT, padx=2)

        def on_spin():
            self.change_size(self.size_spinbox.get())
        self.size_spinbox.config(command=on_spin)
        self.size_spinbox.bind("<Return>", lambda e: self.change_size(self.size_spinbox.get()))
        self.size_spinbox.bind("<FocusOut>", lambda e: self.change_size(self.size_spinbox.get()))

        row2 = tk.Frame(style_frame, bg="#f0f0f0")
        row2.pack(fill=tk.X, pady=3)

        tk.Label(row2, text="背景颜色:", font=("Arial", 9), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.bg_color_combo = ttk.Combobox(row2, values=["默认", "自定义..."], state="readonly",
                                           width=10)
        self.bg_color_combo.set("默认")
        self.bg_color_combo.pack(side=tk.LEFT, padx=5)
        self.bg_color_combo.bind("<<ComboboxSelected>>", self.change_bg_color)

        tk.Label(row2, text="", bg="#f0f0f0").pack(side=tk.LEFT, expand=True)

        self.update_set_seconds()
        self.main_frame = main_frame
        self.style_frame = style_frame

    # ---------- 系统时间 ----------
    def update_system_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sys_time_label.config(text=now)
        self.sys_after_id = self.root.after(1000, self.update_system_time)

    # ---------- 计时器核心 ----------
    def switch_mode(self):
        self.mode = self.mode_var.get()
        self.reset_timer()

    def update_set_seconds(self):
        try:
            h = int(self.hour_entry.get()) if self.hour_entry.get().isdigit() else 0
            m = int(self.min_entry.get()) if self.min_entry.get().isdigit() else 0
            s = int(self.sec_entry.get()) if self.sec_entry.get().isdigit() else 0
            self.set_seconds = h * 3600 + m * 60 + s
        except:
            self.set_seconds = 0

    def update_display(self):
        if self.mode == "正计时":
            seconds = self.current_seconds
        else:
            seconds = max(0, self.set_seconds - self.current_seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    def timer_tick(self):
        if not self.running or self.paused:
            return

        if self.mode == "正计时":
            self.current_seconds += 1
        else:
            if self.current_seconds < self.set_seconds:
                self.current_seconds += 1
            else:
                self.running = False
                self.start_btn.config(state=tk.NORMAL)
                self.pause_btn.config(state=tk.DISABLED)
                self.update_display()
                return

        self.update_display()
        self.after_id = self.root.after(1000, self.timer_tick)

    def start_timer(self):
        if self.running and not self.paused:
            return
        if self.paused:
            self.paused = False
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(text="暂停", state=tk.NORMAL)
            self.after_id = self.root.after(1000, self.timer_tick)
            return

        self.update_set_seconds()
        if self.mode == "倒计时" and self.set_seconds == 0:
            return

        self.running = True
        self.paused = False
        self.current_seconds = 0
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(text="暂停", state=tk.NORMAL)
        self.hour_entry.config(state=tk.DISABLED)
        self.min_entry.config(state=tk.DISABLED)
        self.sec_entry.config(state=tk.DISABLED)
        self.update_display()
        self.after_id = self.root.after(1000, self.timer_tick)

    def pause_timer(self):
        if not self.running:
            return
        if self.paused:
            self.paused = False
            self.pause_btn.config(text="暂停")
            self.start_btn.config(state=tk.DISABLED)
            self.after_id = self.root.after(1000, self.timer_tick)
        else:
            self.paused = True
            self.pause_btn.config(text="继续")
            self.start_btn.config(state=tk.NORMAL)
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None

    def reset_timer(self):
        self.running = False
        self.paused = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.current_seconds = 0
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(text="暂停", state=tk.DISABLED)
        self.hour_entry.config(state=tk.NORMAL)
        self.min_entry.config(state=tk.NORMAL)
        self.sec_entry.config(state=tk.NORMAL)
        self.update_display()

    # ---------- 样式控制 ----------
    def apply_style(self, style=None):
        if style is None:
            style = self.style_combo.get()

        if self.bg_color is not None:
            bg = self.bg_color
        else:
            if style == "暗黑":
                bg = "#2b2b2b"
            elif style == "蓝色":
                bg = "#d9e4f5"
            else:
                bg = "#f0f0f0"

        if style == "暗黑":
            fg = "white"
        elif style == "蓝色":
            fg = "#003366"
        else:
            fg = "black"

        self.root.configure(bg=bg)
        self.main_frame.configure(bg=bg)
        self.style_frame.configure(bg=bg)
        self.time_label.configure(bg=bg)
        self.sys_time_label.configure(bg=bg)

        for child in self.main_frame.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=bg)
            elif isinstance(child, tk.LabelFrame):
                child.configure(bg=bg)
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Frame):
                        sub.configure(bg=bg)
                    elif isinstance(sub, tk.Label):
                        sub.configure(bg=bg, fg=fg)
                    elif isinstance(sub, tk.Spinbox):
                        sub.configure(bg="white" if style != "暗黑" else "#3c3c3c",
                                      fg="black" if style != "暗黑" else "white")
            elif isinstance(child, tk.Label):
                child.configure(bg=bg, fg=fg)

        if style == "暗黑":
            self.start_btn.configure(fg="white")
            self.pause_btn.configure(fg="white")
            self.reset_btn.configure(fg="white")
        else:
            self.start_btn.configure(fg="white")
            self.pause_btn.configure(fg="white")
            self.reset_btn.configure(fg="white")

        for entry in [self.hour_entry, self.min_entry, self.sec_entry]:
            entry.configure(bg="white" if style != "暗黑" else "#3c3c3c",
                            fg="black" if style != "暗黑" else "white")

        self.time_label.config(fg=self.font_color)
        self.sys_time_label.config(fg="white" if style == "暗黑" else "#888888")

    def change_style(self, event=None):
        self.apply_style()

    def change_bg_color(self, event=None):
        choice = self.bg_color_combo.get()
        if choice == "自定义...":
            color = colorchooser.askcolor(title="选择背景颜色")[1]
            if color:
                self.bg_color = color
                self.apply_style()
            else:
                if self.bg_color is None:
                    self.bg_color_combo.set("默认")
                else:
                    self.bg_color_combo.set("自定义...")
        else:
            self.bg_color = None
            self.apply_style()

    def change_color(self, event=None):
        color_name = self.color_combo.get()
        if color_name == "自定义...":
            color = colorchooser.askcolor(title="选择字体颜色")[1]
            if not color:
                return
        else:
            color_map = {"黑色": "#000000", "红色": "#ff0000", "蓝色": "#0000ff", "绿色": "#00aa00"}
            color = color_map.get(color_name, "#000000")
        self.font_color = color
        self.time_label.config(fg=color)

    def change_size(self, value):
        try:
            size = int(value)
            if size < 20:
                size = 20
            elif size > 100:
                size = 100
        except ValueError:
            size = self.font_size
        self.font_size = size
        self.time_label.config(font=("Arial", size, "bold"))
        self.size_spinbox.delete(0, tk.END)
        self.size_spinbox.insert(0, str(size))

if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()