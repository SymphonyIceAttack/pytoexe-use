import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import time
import threading
from cv2 import cvtColor, imread, COLOR_RGB2BGR, matchTemplate, TM_CCOEFF_NORMED, minMaxLoc
from numpy import array
from PIL import Image
from win32api import mouse_event
from win32con import MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
import mss
import random


class FishingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自动钓鱼助手 v2.0")
        self.root.geometry("340x340")
        self.root.resizable(False, False)

        # 运行状态标志
        self.running = False
        self.threshold = 0.41
        self.min_delay = 0
        self.max_delay = 0.3

        # 自动加载模板图片
        self.template_path = "template.png"

        # 设置主题风格
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # 创建UI
        self.create_widgets()

    def configure_styles(self):
        """自定义样式"""
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0')
        self.style.configure('Title.TLabel',
                             font=('Helvetica', 18, 'bold'),
                             foreground='#2c3e50')
        self.style.configure('Status.TLabel',
                             font=('Helvetica', 10),
                             foreground='#7f8c8d')
        self.style.configure('TButton', padding=6)
        self.style.configure('Start.TButton',
                             foreground='white',
                             background='#27ae60')
        self.style.map('Start.TButton',
                       background=[('active', '#2ecc71'), ('disabled', '#bdc3c7')])
        self.style.configure('Stop.TButton',
                             foreground='white',
                             background='#e74c3c')
        self.style.map('Stop.TButton',
                       background=[('active', '#c0392b'), ('disabled', '#bdc3c7')])
        self.style.configure('Settings.TButton',
                             foreground='white',
                             background='#3498db')
        self.style.map('Settings.TButton',
                       background=[('active', '#2980b9')])

    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题区域
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(title_frame,
                                text="自动钓鱼助手",
                                style='Title.TLabel')
        title_label.pack(side=tk.LEFT)

        # 版本标签
        version_label = ttk.Label(title_frame,
                                  text="v2.0",
                                  style='Status.TLabel')
        version_label.pack(side=tk.RIGHT)

        # 设置区域
        settings_frame = ttk.LabelFrame(main_frame,
                                        text="设置",
                                        padding=(15, 10, 15, 10))
        settings_frame.pack(fill=tk.X, pady=5)

        # 阈值设置
        threshold_row = ttk.Frame(settings_frame)
        threshold_row.pack(fill=tk.X, pady=5)

        ttk.Label(threshold_row, text="匹配阈值:").pack(side=tk.LEFT)

        self.threshold_label = ttk.Label(threshold_row, text=f"{self.threshold:.2f}")
        self.threshold_label.pack(side=tk.LEFT, padx=5)

        adjust_btn = ttk.Button(threshold_row,
                                text="调整",
                                command=self.adjust_threshold,
                                style='Settings.TButton')
        adjust_btn.pack(side=tk.RIGHT)

        # 延迟设置
        delay_row = ttk.Frame(settings_frame)
        delay_row.pack(fill=tk.X, pady=5)

        ttk.Label(delay_row, text="随机延迟:").pack(side=tk.LEFT)

        self.delay_label = ttk.Label(delay_row, text=f"{self.min_delay}-{self.max_delay}秒")
        self.delay_label.pack(side=tk.LEFT, padx=5)

        delay_btn = ttk.Button(delay_row,
                               text="设置",
                               command=self.adjust_delay,
                               style='Settings.TButton')
        delay_btn.pack(side=tk.RIGHT)

        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_btn = ttk.Button(control_frame,
                                    text="开始钓鱼",
                                    command=self.toggle_fishing,
                                    style='Start.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True)

        self.stop_btn = ttk.Button(control_frame,
                                   text="停止",
                                   command=self.toggle_fishing,
                                   style='Stop.TButton',
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5, expand=True)

        # 状态栏
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_var = tk.StringVar()
        self.status_var.set("就绪")

        status_label = ttk.Label(status_frame,
                                 textvariable=self.status_var,
                                 style='Status.TLabel')
        status_label.pack(side=tk.LEFT, padx=5)

    def adjust_threshold(self):
        new_threshold = simpledialog.askfloat(
            "调整匹配阈值",
            "请输入新的匹配阈值(0-1之间):",
            initialvalue=self.threshold,
            minvalue=0.1,
            maxvalue=0.99
        )
        if new_threshold is not None:
            self.threshold = new_threshold
            self.threshold_label.config(text=f"{self.threshold:.2f}")
            self.status_var.set(f"阈值已更新为 {self.threshold:.2f}")

    def adjust_delay(self):
        min_delay = simpledialog.askfloat(
            "最小延迟时间",
            "请输入最小延迟时间(秒):",
            initialvalue=self.min_delay,
            minvalue=0,
            maxvalue=1.0
        )

        max_delay = simpledialog.askfloat(
            "最大延迟时间",
            "请输入最大延迟时间(秒):",
            initialvalue=self.max_delay,
            minvalue=0,
            maxvalue=2.0
        )

        if min_delay is not None and max_delay is not None and min_delay < max_delay:
            self.min_delay = min_delay
            self.max_delay = max_delay
            self.delay_label.config(text=f"{self.min_delay}-{self.max_delay}秒")
            self.status_var.set(f"延迟时间更新为 {self.min_delay}-{self.max_delay}秒")
        else:
            messagebox.showwarning("警告", "最小延迟必须小于最大延迟且大于0")

    def toggle_fishing(self):
        if not self.running:
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set("运行中...")

            # 在新线程中启动钓鱼脚本
            self.fishing_thread = threading.Thread(target=self.run_fishing, daemon=True)
            self.fishing_thread.start()
        else:
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("已停止")

    def take_screenshot(self):
        """使用mss高性能截屏"""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[0]  # 主显示器
                sct_img = sct.grab(monitor)

                # 转换为PIL图像
                img = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
                return img
        except Exception as e:
            self.status_var.set(f"截图失败: {str(e)}")
            return None

    def right_click(self, x, y):
        """右键点击行为"""
        # 延迟后点击
        time.sleep(random.uniform(0.1, 0.3))
        mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    def run_fishing(self):
        """钓鱼主循环"""
        # 预加载模板图片
        template_img = imread(self.template_path)
        if template_img is None:
            self.status_var.set("无法加载模板图片")
            return

        template_img = cvtColor(template_img, COLOR_RGB2BGR)
        h, w = template_img.shape[:2]

        while self.running:
            # 使用高性能截图
            frame = self.take_screenshot()

            if frame is None:
                time.sleep(0.5)
                continue

            # 处理截图
            screenshot_img = array(frame)
            screenshot_img = cvtColor(screenshot_img, COLOR_RGB2BGR)

            # 模板匹配
            result = matchTemplate(screenshot_img, template_img, TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = minMaxLoc(result)

            if max_val >= self.threshold:
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                self.status_var.set(f"检测到浮漂溅起水花 (匹配度: {max_val:.2f})")
              
                # 第一步：随机1-5次右键（模拟人类随机操作次数）
                click_times = 3 # 次右键
                for i in range(click_times):
                    # 每次右键间隔随机0.05-0.3秒，更贴近人类操作节奏
                    time.sleep(random.uniform(0.02, 0.3))
                    self.right_click(center_x, center_y)
                    self.status_var.set(f"模拟人类右键第{i + 1}次 (共{click_times}次)")
                    
                # 模拟人类右键点击
                self.right_click(center_x, center_y)

                # 随机延迟后再次点击
                time.sleep(random.uniform(0.1, 0.5))
                self.right_click(center_x, center_y)

                # 等待下次抛竿
                time.sleep(2)
            else:
                self.status_var.set(f"运行中...未检测到浮漂溅起水花 (阈值: {self.threshold:.2f})")

            # 随机操作间隔
            time.sleep(random.uniform(self.min_delay, self.max_delay))


if __name__ == "__main__":
    root = tk.Tk()
    app = FishingApp(root)
    root.mainloop()