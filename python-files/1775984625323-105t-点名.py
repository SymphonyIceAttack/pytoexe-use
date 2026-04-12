import tkinter as tk
from tkinter import ttk, messagebox
import random
import datetime

# 完整名单（共58人）
NAMES = [
    "缪林诺", "袁子惠", "万沁瑜", "许芷欣", "刘一宁", "曹岚", "徐世晋",
    "欧阳静怡", "黎焰珊", "刘嘉瑜", "陈雨萱", "陆佳琦", "袁雪茗", "黎宛桐",
    "林千艺", "孔梓茜", "陈可馨", "阳昕妤", "李佳琳", "杨扬", "王惠萌",
    "谭晨纳", "李泳霖", "吕梦涵", "赖仁璨", "邓如乔", "赵紫含", "苗欣雨",
    "王靖然", "李佳杭", "祝鑫怡", "莫滢滢", "陈美锟", "韦婉", "胡欣颖",
    "李佳霓", "邓语鑫", "辛菲怡", "李俊希", "李俊", "肖睿熙", "谭漠南",
    "刘铭皓", "陈奕成", "史城郡", "杨子熙", "颜文宇", "庄浩峰", "李正珑",
    "江毅轩", "陈栋明", "郑天宇", "袁铨", "陈泊霖", "陈宇轩", "周庭羽",
    "莫雅雯", "罗戡"
]
TOTAL = len(NAMES)

class CallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("课堂点名器-DONGXI")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self.root.configure(bg="#1e1f2c")  # 深色高端背景

        # 设置全局字体
        self.font_title = ("微软雅黑", 16, "bold")
        self.font_name = ("微软雅黑", 48, "bold")
        self.font_btn = ("微软雅黑", 12)
        self.font_history = ("微软雅黑", 10)

        # 点名滚动控制
        self.is_rolling = False
        self.after_id = None

        # 构建界面
        self.setup_ui()

        # 窗口居中
        self.center_window()

    def setup_ui(self):
        # 主容器，使用左右分栏（左侧点名区，右侧历史区）
        main_frame = tk.Frame(self.root, bg="#1e1f2c")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 左侧区域（点名核心区）
        left_frame = tk.Frame(main_frame, bg="#2a2b3a", relief=tk.FLAT, bd=0)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 标题
        title_lbl = tk.Label(left_frame, text="✨ 课堂点名器-DONGXI ✨", font=self.font_title,
                             bg="#2a2b3a", fg="#e0e0e0")
        title_lbl.pack(pady=(30, 20))

        # 总人数卡片
        info_frame = tk.Frame(left_frame, bg="#3a3b4a", relief=tk.RAISED, bd=0)
        info_frame.pack(pady=(0, 30))
        tk.Label(info_frame, text=f"📋 班级总人数：{TOTAL}", font=("微软雅黑", 12),
                 bg="#3a3b4a", fg="#f0f0f0").pack(padx=20, pady=8)

        # 名字显示区域（醒目）
        self.name_label = tk.Label(left_frame, text="准备就绪", font=self.font_name,
                                   bg="#2a2b3a", fg="#ffd966", wraplength=500)
        self.name_label.pack(expand=True, pady=20)

        # 按钮框架
        btn_frame = tk.Frame(left_frame, bg="#2a2b3a")
        btn_frame.pack(pady=30)

        # 开始按钮（绿色）
        self.start_btn = tk.Button(btn_frame, text="▶ 开始点名", font=self.font_btn,
                                   bg="#2e7d32", fg="white", padx=20, pady=8,
                                   relief=tk.FLAT, cursor="hand2",
                                   command=self.start_roll)
        self.start_btn.pack(side=tk.LEFT, padx=15)

        # 结束按钮（红色，初始禁用）
        self.stop_btn = tk.Button(btn_frame, text="⏹️ 结束点名", font=self.font_btn,
                                  bg="#c62828", fg="white", padx=20, pady=8,
                                  relief=tk.FLAT, cursor="hand2",
                                  command=self.stop_roll, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=15)

        # 右侧区域（点名历史）
        right_frame = tk.Frame(main_frame, bg="#2a2b3a", relief=tk.FLAT, bd=0)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0))
        right_frame.configure(width=260)
        right_frame.pack_propagate(False)

        # 历史记录标题 + 清空按钮
        history_header = tk.Frame(right_frame, bg="#2a2b3a")
        history_header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(history_header, text="📜 点名历史", font=self.font_title,
                 bg="#2a2b3a", fg="#e0e0e0").pack(side=tk.LEFT)
        clear_btn = tk.Button(history_header, text="清空", font=("微软雅黑", 9),
                              bg="#5c5d6e", fg="white", relief=tk.FLAT,
                              cursor="hand2", command=self.clear_history)
        clear_btn.pack(side=tk.RIGHT)

        # 历史记录列表框 + 滚动条
        list_frame = tk.Frame(right_frame, bg="#2a2b3a")
        list_frame.pack(fill=tk.BOTH, expand=True)
        self.history_listbox = tk.Listbox(list_frame, font=self.font_history,
                                          bg="#3a3b4a", fg="#f0f0f0",
                                          selectbackground="#ffd966",
                                          relief=tk.FLAT, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.history_listbox.yview)
        self.history_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 初始添加欢迎信息
        #self.add_history("✨ 点名器已启动", is_system=True)

    def center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def start_roll(self):
        """开始随机滚动名字"""
        if self.is_rolling:
            return
        # 停止可能残留的滚动（但不记录历史）
        self._stop_roll_internal(record=False)
        self.is_rolling = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        # 立刻显示一个随机名字
        self._update_name_random()
        # 启动循环刷新
        self._schedule_update()

    def _schedule_update(self):
        """每隔50ms更新一次名字"""
        if self.is_rolling:
            self._update_name_random()
            self.after_id = self.root.after(50, self._schedule_update)

    def _update_name_random(self):
        """随机选择一个名字并显示"""
        if NAMES:
            name = random.choice(NAMES)
            self.name_label.config(text=name)

    def stop_roll(self):
        """结束点名（由用户点击结束按钮触发）"""
        if not self.is_rolling:
            return
        # 停止滚动并记录当前显示的名字
        self._stop_roll_internal(record=True)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def _stop_roll_internal(self, record=False):
        """内部停止滚动，可选择是否将当前名字记入历史"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.is_rolling = False

        if record:
            current_name = self.name_label.cget("text")
            if current_name and current_name != "准备就绪" and current_name in NAMES:
                self.add_history(current_name)

    def add_history(self, name, is_system=False):
        """添加一条点名记录（或系统消息）"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if is_system:
            record = f"[{timestamp}] {name}"
        else:
            record = f"[{timestamp}] 🎲 被点中：{name}"
        self.history_listbox.insert(0, record)  # 最新在上方
        # 保持最多30条记录
        if self.history_listbox.size() > 30:
            self.history_listbox.delete(30, tk.END)
        # 自动滚动到最新记录（索引0）
        self.history_listbox.see(0)

    def clear_history(self):
        """清空历史记录"""
        self.history_listbox.delete(0, tk.END)
        self.add_history("📌 历史记录已清空", is_system=True)

    def on_closing(self):
        """窗口关闭时的清理"""
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CallerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()