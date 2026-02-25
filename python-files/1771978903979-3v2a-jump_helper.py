#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信跳一跳游戏助手
在Windows电脑上运行的.exe文件，帮助玩家不会掉下去
"""

import sys
import cv2
import numpy as np
import time
import threading
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, QTextEdit,
                             QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
import mss
import pyautogui
import win32gui
import win32con

class ScreenCapture:
    """屏幕捕获类"""
    
    def __init__(self):
        self.sct = mss.mss()
        self.monitor = None
        
    def find_game_window(self):
        """查找游戏窗口"""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if "微信" in window_text or "跳一跳" in window_text:
                    windows.append((hwnd, window_text))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows
    
    def capture_game_area(self, hwnd=None):
        """捕获游戏区域"""
        if hwnd:
            # 获取窗口位置
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # 捕获窗口区域
            monitor = {
                "top": top,
                "left": left,
                "width": width,
                "height": height
            }
        else:
            # 全屏捕获
            monitor = self.sct.monitors[0]
        
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img, monitor

class JumpDetector:
    """跳跃检测类"""
    
    def __init__(self):
        self.character_template = None
        self.last_character_pos = None
        
    def load_character_template(self):
        """加载角色模板"""
        # 创建一个简单的角色模板（圆形）
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.circle(template, (25, 25), 20, (255, 255, 255), -1)
        return template
    
    def detect_character(self, image):
        """检测角色位置"""
        if self.character_template is None:
            self.character_template = self.load_character_template()
        
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(self.character_template, cv2.COLOR_BGR2GRAY)
        
        # 模板匹配
        result = cv2.matchTemplate(gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.7:  # 匹配阈值
            h, w = template_gray.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y), max_val
        
        return None, 0
    
    def detect_target_platform(self, image, character_pos):
        """检测目标平台"""
        h, w = image.shape[:2]
        
        # 在角色右侧寻找下一个平台
        search_region = image[:, character_pos[0]:]
        
        # 边缘检测
        edges = cv2.Canny(search_region, 50, 150)
        
        # 寻找水平线（平台）
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
        
        if lines is not None:
            # 找到最底部的水平线
            bottom_line = None
            max_y = 0
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(y1 - y2) < 10:  # 水平线
                    if y1 > max_y:
                        max_y = y1
                        bottom_line = (x1, y1, x2, y2)
            
            if bottom_line:
                target_x = (bottom_line[0] + bottom_line[2]) // 2 + character_pos[0]
                target_y = bottom_line[1]
                return (target_x, target_y)
        
        return None
    
    def calculate_distance(self, pos1, pos2):
        """计算两点间距离"""
        if pos1 and pos2:
            return math.sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2)
        return 0

class JumpHelperGUI(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.capture = ScreenCapture()
        self.detector = JumpDetector()
        self.running = False
        self.auto_jump = False
        
        self.init_ui()
        self.init_timer()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("微信跳一跳游戏助手")
        self.setFixedSize(1080, 720)  # 设置窗口大小为1080x720
        self.center_window()  # 窗口居中
        
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧：图像显示
        left_panel = QVBoxLayout()
        
        # 图像标签
        self.image_label = QLabel()
        self.image_label.setFixedSize(640, 480)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.image_label)
        
        # 状态标签
        self.status_label = QLabel("状态: 待机")
        self.status_label.setStyleSheet("font-size: 14px; color: #333;")
        left_panel.addWidget(self.status_label)
        
        main_layout.addLayout(left_panel)
        
        # 右侧：控制面板
        right_panel = QVBoxLayout()
        
        # 游戏窗口选择
        window_group = QGroupBox("游戏窗口")
        window_layout = QVBoxLayout()
        
        self.window_list_label = QLabel("检测到的窗口:")
        window_layout.addWidget(self.window_list_label)
        
        self.refresh_windows_btn = QPushButton("刷新窗口列表")
        self.refresh_windows_btn.clicked.connect(self.refresh_windows)
        window_layout.addWidget(self.refresh_windows_btn)
        
        window_group.setLayout(window_layout)
        right_panel.addWidget(window_group)
        
        # 参数设置
        params_group = QGroupBox("参数设置")
        params_layout = QVBoxLayout()
        
        # 按压系数
        coeff_layout = QHBoxLayout()
        coeff_layout.addWidget(QLabel("按压系数:"))
        self.coeff_spinbox = QDoubleSpinBox()
        self.coeff_spinbox.setRange(1.0, 5.0)
        self.coeff_spinbox.setValue(2.8)
        self.coeff_spinbox.setSingleStep(0.1)
        coeff_layout.addWidget(self.coeff_spinbox)
        params_layout.addLayout(coeff_layout)
        
        # 延迟时间
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("跳跃延迟(ms):"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(500, 3000)
        self.delay_spinbox.setValue(1200)
        self.delay_spinbox.setSingleStep(100)
        delay_layout.addWidget(self.delay_spinbox)
        params_layout.addLayout(delay_layout)
        
        params_group.setLayout(params_layout)
        right_panel.addWidget(params_group)
        
        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("开始捕获")
        self.start_btn.clicked.connect(self.toggle_capture)
        control_layout.addWidget(self.start_btn)
        
        self.auto_jump_checkbox = QCheckBox("自动跳跃")
        self.auto_jump_checkbox.stateChanged.connect(self.toggle_auto_jump)
        control_layout.addWidget(self.auto_jump_checkbox)
        
        self.test_jump_btn = QPushButton("测试跳跃")
        self.test_jump_btn.clicked.connect(self.test_jump)
        control_layout.addWidget(self.test_jump_btn)
        
        control_group.setLayout(control_layout)
        right_panel.addWidget(control_group)
        
        # 日志
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setFixedHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        right_panel.addWidget(log_group)
        
        main_layout.addLayout(right_panel)
        
        # 初始状态
        self.refresh_windows()
        
    def center_window(self):
        """窗口居中显示"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.setGeometry(x, y, self.width(), self.height())
    
    def init_timer(self):
        """初始化定时器"""
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.update_frame)
        self.capture_timer.setInterval(100)  # 100ms更新一次
    
    def refresh_windows(self):
        """刷新窗口列表"""
        windows = self.capture.find_game_window()
        window_text = "检测到的窗口:\n"
        for i, (hwnd, text) in enumerate(windows):
            window_text += f"{i+1}. {text}\n"
        if not windows:
            window_text += "未找到游戏窗口"
        self.window_list_label.setText(window_text)
    
    def toggle_capture(self):
        """切换捕获状态"""
        if self.running:
            self.stop_capture()
        else:
            self.start_capture()
    
    def start_capture(self):
        """开始捕获"""
        self.running = True
        self.start_btn.setText("停止捕获")
        self.status_label.setText("状态: 捕获中...")
        self.log("开始屏幕捕获")
        self.capture_timer.start()
    
    def stop_capture(self):
        """停止捕获"""
        self.running = False
        self.start_btn.setText("开始捕获")
        self.status_label.setText("状态: 待机")
        self.log("停止屏幕捕获")
        self.capture_timer.stop()
    
    def toggle_auto_jump(self, state):
        """切换自动跳跃"""
        self.auto_jump = state == Qt.Checked
        if self.auto_jump:
            self.log("启用自动跳跃")
        else:
            self.log("禁用自动跳跃")
    
    def update_frame(self):
        """更新帧"""
        try:
            # 捕获屏幕
            image, monitor = self.capture.capture_game_area()
            
            if image is not None:
                # 检测角色
                character_pos, confidence = self.detector.detect_character(image)
                
                if character_pos:
                    # 绘制角色位置
                    cv2.circle(image, character_pos, 10, (0, 255, 0), 2)
                    
                    # 检测目标平台
                    target_pos = self.detector.detect_target_platform(image, character_pos)
                    
                    if target_pos:
                        # 绘制目标位置
                        cv2.circle(image, target_pos, 10, (255, 0, 0), 2)
                        
                        # 计算距离
                        distance = self.detector.calculate_distance(character_pos, target_pos)
                        
                        # 显示信息
                        cv2.putText(image, f"Distance: {distance:.1f}", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                        
                        # 自动跳跃
                        if self.auto_jump:
                            self.perform_jump(distance)
                
                # 转换图像格式并显示
                self.display_image(image)
                
        except Exception as e:
            self.log(f"更新帧错误: {str(e)}")
    
    def display_image(self, image):
        """显示图像"""
        # 调整图像大小
        h, w = image.shape[:2]
        target_height = 480
        target_width = int(w * target_height / h)
        
        if target_width > 640:
            target_width = 640
            target_height = int(h * target_width / w)
        
        resized = cv2.resize(image, (target_width, target_height))
        
        # 转换颜色格式
        rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # 创建QImage
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # 显示图像
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)
    
    def perform_jump(self, distance):
        """执行跳跃"""
        try:
            # 计算按压时间
            press_time = int(distance * self.coeff_spinbox.value())
            
            # 获取屏幕中心位置
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            # 模拟按压
            pyautogui.mouseDown(x=center_x, y=center_y)
            time.sleep(press_time / 1000)  # 转换为秒
            pyautogui.mouseUp(x=center_x, y=center_y)
            
            self.log(f"执行跳跃: 距离={distance:.1f}, 时间={press_time}ms")
            
            # 等待一段时间再进行下一次跳跃
            time.sleep(self.delay_spinbox.value() / 1000)
            
        except Exception as e:
            self.log(f"跳跃错误: {str(e)}")
    
    def test_jump(self):
        """测试跳跃"""
        try:
            # 执行一个测试跳跃
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            
            pyautogui.mouseDown(x=center_x, y=center_y)
            time.sleep(0.5)  # 500ms
            pyautogui.mouseUp(x=center_x, y=center_y)
            
            self.log("执行测试跳跃")
            
        except Exception as e:
            self.log(f"测试跳跃错误: {str(e)}")
    
    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insertPlainText(log_message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("微信跳一跳游戏助手")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("JumpHelper")
    
    # 创建并显示主窗口
    window = JumpHelperGUI()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()