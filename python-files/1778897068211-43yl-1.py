import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QRegion, QPainterPath

# Windows DWM 灰度后置特效常量
DWMWA_GRAYSCALE = 17

# 调用Windows桌面窗口管理器API
dwmapi = ctypes.WinDLL("dwmapi.dll")

class GrayCircleMask(QWidget):
    def __init__(self):
        super().__init__()
        # 窗口基础设置
        self.win_size = 300  # 圆形大小
        self.init_window()
        self.set_circle_shape()
        self.set_back_gray()

    def init_window(self):
        # 无边框、置顶、穿透鼠标、透明背景
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(self.win_size, self.win_size)
        # 居中显示
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def set_circle_shape(self):
        # 裁剪窗口为纯圆形
        path = QPainterPath()
        path.addEllipse(0, 0, self.win_size, self.win_size)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def set_back_gray(self):
        # 设置窗口后方区域自动变为黑白灰度
        hwnd = int(self.winId())
        enable = ctypes.c_int(1)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_GRAYSCALE,
            ctypes.byref(enable),
            ctypes.sizeof(enable)
        )

    # 鼠标拖动移动圆形
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    # 右键关闭软件
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GrayCircleMask()
    window.show()
    sys.exit(app.exec())