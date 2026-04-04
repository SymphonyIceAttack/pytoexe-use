import random
import tkinter as tk
from tkinter import ttk
import json
import os
from datetime import datetime

# ===================== 2306班学生名单（学号+姓名，已预录入）=====================
CLASS_2306_STUDENTS = [
    "2306101 罗惠华", "2306102 阳天晟", "2306103 熊雪森", "2306104 廖家辉", "2306105 邓羽翔",
    "2306106 赵城辉", "2306107 陈治成", "2306108 高凡睿", "2306109 李子屹", "2306110 蒙志宇",
    "2306111 ALFREDOGALLARDOWU", "2306112 朱敬乔", "2306113 蒋承宇", "2306114 詹嘉俊", "2306115 周伦羽",
    "2306116 黄泽元", "2306117 李明峰", "2306118 俞业嘉", "2306119 龙奕丞", "2306120 高焌凌",
    "2306121 陈博睿", "2306122 于子鑫", "2306123 蒋泞骏", "2306125 黄梓骞", "2306126 张浩轩",
    "2306127 韦肇堂", "2306128 莫智杰", "2306129 周小川", "2306130 莫诗妍", "2306131 朱雨婷",
    "2306132 阮馨逸", "2306133 梁洲瑜", "2306134 赵子燕", "2306135 刘佳衢", "2306136 蔡依言",
    "2306137 付一萱", "2306138 张净溪", "2306139 姚孜仪", "2306140 韦紫芊", "2306141 蒋欣乐",
    "2306142 蒋雨晴", "2306143 徐梓菡", "2306144 张欣怡", "2306145 周付彦昕", "2306147 莫蕙竹",
    "2306148 梁雨晨", "2306149 蒋语彤", "2306150 韦芊语", "2306151 邓惠雯", "2306152 唐忆恩",
    "2306153 唐宇清", "2306154 易淘淘", "2306155 李宛珂"
]
# =========================================================================

class StudentLottery2306:
    def __init__(self, root):
        self.root = root
        # 程序标题：金玉瑶 2306学生抽签系统
        self.root.title("金玉瑶 2306学生抽签系统")
        self.root.geometry("800x650")
        self.root.resizable(False, False)
        
        # 字体配置（Windows/macOS通用，适配中文字体）
        self.font_title = ("微软雅黑", 18, "bold") if os.name == "nt" else ("华文黑体", 18, "bold")
        self.font_normal = ("微软雅黑", 11) if os.name == "nt" else ("华文黑体", 11)
        self.font_lottery = ("微软雅黑", 56, "bold") if os.name == "nt" else ("华文黑体", 56, "bold")
        self.font_list = ("微软雅黑", 10) if os.name == "nt" else ("华文黑体", 10)
        
        # 核心数据
        self.students = []  # 2306班学生名单（学号+姓名）
        self.selected_history = []  # 已抽中记录
        self.data_file = "2306班抽签数据.json"  # 本地保存文件
        
        # 抽签动画参数
        self.animation_running = False
        self.animation_count = 0
        self.auto_stop_times = 35  # 动画自动停止次数（可调整，数值越大动画越久）
        
        # 初始化数据（首次加载内置名单，后续加载本地数据）
        self.init_data()
        # 创建界面
        self.create_widgets()

    def init_data(self):
        """初始化数据：首次运行加载2306班内置名单，否则加载本地保存数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.students = data.get("students", [])
                    self.selected_history = data.get("history", [])
            except Exception as e:
                self.students = CLASS_2306_STUDENTS.copy()
                self.selected_history = []
        else:
            self.students = CLASS_2306_STUDENTS.copy()
            self.selected_history = []
        self.save_data()

    def save_data(self):
        """保存数据到本地json文件"""
        data = {
            "students": self.students,
            "history": self.selected_history,
            "save_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "class": "2306班"
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def create_widgets(self):
        """创建程序界面：双栏名单、仅保留开始/重置按钮"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 界面内标题
        title_label = ttk.Label(main_frame, text="金玉瑶 2306学生抽签系统", font=self.font_title, foreground="#2F5496")
        title_label.pack(pady=(0, 25))
        
        # 抽签显示区域（抽中为绿色#009688）
        lottery_frame = ttk.Frame(main_frame, relief=tk.RAISED, borderwidth=2, padding="10")
        lottery_frame.pack(fill=tk.X, pady=(0, 25), ipady=40)
        self.lottery_label = ttk.Label(
            lottery_frame, 
            text="点击开始抽签", 
            font=self.font_lottery,
            foreground="#3366CC"
        )
        self.lottery_label.pack(expand=True)
        
        # 控制按钮区域（仅开始/重置）
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 25))
        ttk.Style().configure("Custom.TButton", font=self.font_normal, padding=12)
        
        self.start_btn = ttk.Button(
            button_frame, 
            text="开始抽签", 
            command=self.start_lottery,
            style="Custom.TButton"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 20), fill=tk.X, expand=True)
        
        self.reset_btn = ttk.Button(
            button_frame, 
            text="重置抽签", 
            command=self.reset_lottery,
            style="Custom.TButton"
        )
        self.reset_btn.pack(side=tk.RIGHT, padx=(20, 0), fill=tk.X, expand=True)
        
        # 双名单展示区（左：全体名单 右：抽签状态）
        list_container = ttk.Frame(main_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：2306班全体学生名单（学号+姓名，无标记）
        all_student_frame = ttk.LabelFrame(list_container, text="2306班全体学生名单（学号+姓名）", padding="10")
        all_student_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        all_scroll = ttk.Scrollbar(all_student_frame)
        all_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.all_student_list = tk.Listbox(
            all_student_frame,
            font=self.font_list,
            yscrollcommand=all_scroll.set,
            selectbackground="#E8F4F8",
            selectforeground="#2F5496"
        )
        self.all_student_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        all_scroll.config(command=self.all_student_list.yview)
        
        # 右侧：抽签状态名单（✅已抽中 | ⬜未抽中）
        status_frame = ttk.LabelFrame(list_container, text="抽签状态（✅已抽中 | ⬜未抽中）", padding="10")
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        status_scroll = ttk.Scrollbar(status_frame)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_student_list = tk.Listbox(
            status_frame,
            font=self.font_list,
            yscrollcommand=status_scroll.set,
            selectbackground="#E8F4F8",
            selectforeground="#2F5496"
        )
        self.status_student_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.config(command=self.status_student_list.yview)
        
        # 刷新双名单
        self.refresh_all_list()
        self.refresh_status_list()

    def refresh_all_list(self):
        """刷新左侧全体学生名单"""
        self.all_student_list.delete(0, tk.END)
        for idx, student in enumerate(self.students, 1):
            self.all_student_list.insert(tk.END, f"{idx:2d}. {student}")

    def refresh_status_list(self):
        """刷新右侧抽签状态名单"""
        self.status_student_list.delete(0, tk.END)
        for idx, student in enumerate(self.students, 1):
            status = "✅" if student in self.selected_history else "⬜"
            self.status_student_list.insert(tk.END, f"{idx:2d}. {status} {student}")

    def start_lottery(self):
        """开始抽签：动画自动运行、自动停止，无手动停止"""
        if not self.students:
            return
        # 筛选未抽中学生
        available_students = [s for s in self.students if s not in self.selected_history]
        if not available_students:
            self.lottery_label.config(text="全体已抽中", foreground="#E63946")
            return
        # 仅在未运行时启动动画
        if not self.animation_running:
            self.animation_running = True
            self.start_btn.config(state=tk.DISABLED)  # 抽签中禁用开始按钮，防止重复点击
            self.lottery_animation(available_students)

    def lottery_animation(self, available_students):
        """抽签滚动动画：自动计数停止，无弹窗，抽中绿色高亮"""
        if self.animation_running:
            # 随机显示未抽中学生
            random_student = random.choice(available_students)
            self.lottery_label.config(text=random_student, foreground="#3366CC")
            self.animation_count += 1
            
            # 动画速度：先快后慢（和之前一致，氛围感拉满）
            speed = 50 if self.animation_count < 20 else 100 if self.animation_count < 30 else 200
            
            # 判断是否达到自动停止次数
            if self.animation_count < self.auto_stop_times:
                self.root.after(speed, lambda: self.lottery_animation(available_students))
            else:
                # 自动停止：确定抽中者，绿色高亮
                lucky_student = random.choice(available_students)
                self.selected_history.append(lucky_student)
                self.lottery_label.config(text=lucky_student, foreground="#009688")
                # 保存数据+刷新抽签状态
                self.save_data()
                self.refresh_status_list()
                # 重置动画参数，启用开始按钮
                self.animation_running = False
                self.animation_count = 0
                self.start_btn.config(state=tk.NORMAL)

    def reset_lottery(self):
        """重置抽签记录，保留全体名单"""
        self.selected_history.clear()
        self.lottery_label.config(text="点击开始抽签", foreground="#3366CC")
        self.save_data()
        self.refresh_status_list()
        # 重置动画参数，确保按钮可用
        self.animation_running = False
        self.animation_count = 0
        self.start_btn.config(state=tk.NORMAL)

# ===================== 程序入口 =====================
if __name__ == "__main__":
    root = tk.Tk()
    app = StudentLottery2306(root)
    root.mainloop()