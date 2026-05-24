import sys
import time
import threading
import cv2
import numpy as np
from mss import mss
from pynput.keyboard import Key, Controller
import win32gui
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor

# 后台Bot工作线程
class BotWorker(QObject):
    status_update = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.keyboard = Controller()
        
        # 音符位置的相对比例（适配所有分辨率）
        self.note_relative_pos = [
            (0.40, 0.66, 0.475, 0.83),  # 左
            (0.475, 0.66, 0.55, 0.83),  # 下
            (0.55, 0.66, 0.625, 0.83),  # 上
            (0.625, 0.66, 0.70, 0.83)   # 右
        ]
        # 对应按键
        self.keys = [Key.left, Key.down, Key.up, Key.right]
        
        # 颜色识别阈值：区分普通音符和扣血音符
        # 普通音符（蓝/紫系）
        self.normal_lower = np.array([90, 0, 0])
        self.normal_upper = np.array([255, 160, 160])
        # 扣血音符（红系陷阱）
        self.damage_lower = np.array([0, 0, 100])
        self.damage_upper = np.array([100, 100, 255])

    # 自动查找FNF游戏窗口，兼容所有引擎
    def find_game_window(self):
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # 匹配所有常见引擎的窗口标题
                if any(name in title for name in [
                    "Friday Night Funkin", "Codename Engine", 
                    "Psych Engine", "FNF"
                ]):
                    extra.append(hwnd)
        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None

    def run(self):
        self.running = True
        self.status_update.emit("正在查找游戏窗口...")
        
        # 查找游戏窗口
        hwnd = self.find_game_window()
        if not hwnd:
            self.status_update.emit("❌ 未找到FNF窗口，请先打开游戏！")
            self.running = False
            return
        
        # 获取窗口大小，适配分辨率
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        win_w = right - left
        win_h = bottom - top
        self.status_update.emit(f"✅ 找到游戏，大小：{win_w}x{win_h}，开始自动游玩...")

        # 计算当前分辨率下的音符实际位置
        note_positions = []
        for (rx1, ry1, rx2, ry2) in self.note_relative_pos:
            x1 = int(left + win_w * rx1)
            y1 = int(top + win_h * ry1)
            x2 = int(left + win_w * rx2)
            y2 = int(top + win_h * ry2)
            note_positions.append((x1, y1, x2, y2))

        # 初始化截图工具
        sct = mss()
        monitor = {"top": top, "left": left, "width": win_w, "height": win_h}

        # 主循环
        while self.running:
            try:
                # 截取游戏画面
                frame = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # 遍历四个音符轨道
                for i in range(4):
                    x1, y1, x2, y2 = note_positions[i]
                    # 截取轨道区域
                    roi = frame[y1:y2, x1:x2]
                    if roi.size == 0:
                        continue

                    # 识别普通音符
                    normal_mask = cv2.inRange(roi, self.normal_lower, self.normal_upper)
                    normal_pixels = cv2.countNonZero(normal_mask)
                    
                    # 识别扣血音符
                    damage_mask = cv2.inRange(roi, self.damage_lower, self.damage_upper)
                    damage_pixels = cv2.countNonZero(damage_mask)

                    # 普通音符：自动按键命中
                    if normal_pixels > 100:
                        self.keyboard.press(self.keys[i])
                        time.sleep(0.05)
                        self.keyboard.release(self.keys[i])
                    # 扣血音符：自动避开，不按键
            except Exception as e:
                self.status_update.emit(f"运行出错: {str(e)}")
                break
            
            time.sleep(0.01)
        
        self.status_update.emit("已停止Bot")

# iOS风格的UI窗口
class FNF_Bot_Window(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.thread = None
        self.initUI()

    def initUI(self):
        # 窗口基础设置
        self.setWindowTitle("FNF 自动Bot")
        self.setFixedSize(360, 220)
        
        # iOS风格样式表：圆角、浅色、系统蓝
        self.setStyleSheet("""
            QWidget {
                background-color: #f2f2f7;
                font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
            }
            QPushButton {
                background-color: #007aff;
                color: white;
                border: none;
                border-radius: 14px;
                padding: 14px 28px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0066cc;
            }
            QPushButton:pressed {
                background-color: #0051a8;
            }
            QLabel {
                color: #1c1c1e;
            }
        """)

        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # 标题
        title_label = QLabel("FNF 全自动Bot")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 状态显示
        self.status_label = QLabel("准备就绪，打开游戏后点击启动")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.status_label)

        # 启动按钮
        self.toggle_btn = QPushButton("启动Bot")
        self.toggle_btn.clicked.connect(self.toggle_bot)
        layout.addWidget(self.toggle_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        # 窗口标志
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

    def toggle_bot(self):
        if self.worker and self.worker.running:
            # 停止Bot
            self.worker.running = False
            self.toggle_btn.setText("启动Bot")
            self.status_label.setText("已停止Bot")
        else:
            # 启动Bot
            self.worker = BotWorker()
            self.worker.status_update.connect(self.update_status)
            # 后台线程运行，不卡UI
            self.thread = threading.Thread(target=self.worker.run, daemon=True)
            self.thread.start()
            self.toggle_btn.setText("停止Bot")

    def update_status(self, status):
        self.status_label.setText(status)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 全局字体
    app.setFont(QFont("Segoe UI"))
    window = FNF_Bot_Window()
    window.show()
    sys.exit(app.exec())
