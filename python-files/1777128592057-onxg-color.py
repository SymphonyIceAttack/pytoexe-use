import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QSpinBox, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPen
import mss
import mss.tools

# 主窗口工具类
class ColorAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("屏幕区域颜色占比实时分析工具")
        self.setGeometry(100, 100, 500, 400)
        self.setAlwaysOnTop(True)  # 窗口置顶

        # 核心变量
        self.selecting = False  # 是否正在框选区域
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.capture_rect = None  # 最终捕获区域
        self.refresh_rate = 30  # 默认刷新帧率
        self.colors_count = 10  # 显示前10种颜色

        # 初始化截图工具
        self.sct = mss.mss()

        # 创建UI
        self.init_ui()

        # 实时刷新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.analyze_color)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 标题
        title = QLabel("屏幕区域颜色实时分析")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:16px; font-weight:bold; padding:8px;")
        layout.addWidget(title)

        # 功能按钮行
        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("框选屏幕区域")
        self.select_btn.clicked.connect(self.start_select)
        self.start_btn = QPushButton("开始分析")
        self.start_btn.clicked.connect(self.start_analyze)
        self.stop_btn = QPushButton("停止分析")
        self.stop_btn.clicked.connect(self.stop_analyze)
        btn_layout.addWidget(self.select_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 帧率设置
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("刷新帧率："))
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(1, 60)
        self.rate_spin.setValue(self.refresh_rate)
        self.rate_spin.valueChanged.connect(self.update_rate)
        rate_layout.addWidget(self.rate_spin)
        rate_layout.addStretch()
        layout.addLayout(rate_layout)

        # 区域信息
        self.rect_label = QLabel("未选择区域 | 请先点击【框选屏幕区域】")
        layout.addWidget(self.rect_label)

        # 颜色结果展示
        self.result_label = QLabel("颜色分析结果将在这里显示")
        self.result_label.setAlignment(Qt.AlignTop)
        self.result_label.setStyleSheet("background-color:#f5f5f5; padding:10px;")
        layout.addWidget(self.result_label)

    # 开始框选区域
    def start_select(self):
        self.selecting = True
        self.setWindowOpacity(0.2)
        self.rect_label.setText("正在框选：拖动鼠标选择区域，松开完成")

    def mousePressEvent(self, event):
        if self.selecting and event.button() == Qt.LeftButton:
            self.start_point = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.globalPos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.selecting and event.button() == Qt.LeftButton:
            self.end_point = event.globalPos()
            self.selecting = False
            self.setWindowOpacity(1)
            self.update()

            # 生成有效区域
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())
            self.capture_rect = QRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))
            self.rect_label.setText(f"已选区域：X={self.capture_rect.x()} Y={self.capture_rect.y()} 宽={self.capture_rect.width()} 高={self.capture_rect.height()}")

    def paintEvent(self, event):
        if self.selecting and not self.start_point.isNull() and not self.end_point.isNull():
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRect(self.start_point, self.end_point))

    # 更新帧率
    def update_rate(self, value):
        self.refresh_rate = value
        if self.timer.isActive():
            self.timer.setInterval(1000 // self.refresh_rate)

    # 开始实时分析
    def start_analyze(self):
        if not self.capture_rect or self.capture_rect.width() < 2 or self.capture_rect.height() < 2:
            self.rect_label.setText("错误：请先框选有效区域！")
            return
        interval = 1000 // self.refresh_rate
        self.timer.start(interval)
        self.rect_label.setText(f"✅ 正在实时分析（{self.refresh_rate}帧/秒）")

    def stop_analyze(self):
        self.timer.stop()
        self.rect_label.setText("⏹ 已停止分析")

    # 核心：捕获区域 → 分析颜色占比
    def analyze_color(self):
        try:
            # 屏幕捕获
            monitor = {
                "top": self.capture_rect.y(),
                "left": self.capture_rect.x(),
                "width": self.capture_rect.width(),
                "height": self.capture_rect.height()
            }
            img = self.sct.grab(monitor)
            img_np = np.array(img)

            # 提取RGB并降采样（提速）
            pixels = img_np.reshape(-1, 4)[:, :3]
            total = len(pixels)

            # 统计颜色
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            sorted_idx = np.argsort(counts)[::-1]
            top_colors = unique_colors[sorted_idx[:self.colors_count]]
            top_counts = counts[sorted_idx[:self.colors_count]]

            # 构建显示文本
            text = "📊 实时颜色占比（前10种）\n"
            text += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            for i, (rgb, cnt) in enumerate(zip(top_colors, top_counts)):
                r, g, b = rgb
                hex_color = f"#{r:02x}{g:02x}{b:02x}".upper()
                ratio = cnt / total * 100
                text += f"{i+1:2d}. {hex_color} | RGB({r:3d},{g:3d},{b:3d}) | {ratio:.2f}%\n"

            self.result_label.setText(text)

        except Exception as e:
            self.result_label.setText(f"分析异常：{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorAnalyzer()
    window.show()
    sys.exit(app.exec_())
