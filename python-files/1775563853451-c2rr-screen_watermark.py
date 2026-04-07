import sys
import os
import winreg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QPushButton, QLineEdit, QLabel, QSpinBox,
    QColorDialog, QSystemTrayIcon, QMenu, QCheckBox
)

# 开机自启注册表操作
def set_startup(enable: bool):
    key = winreg.HKEY_CURRENT_USER
    sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_path = sys.executable
    app_name = "ScreenWatermark"
    try:
        with winreg.OpenKey(key, sub_key, 0, winreg.KEY_WRITE) as reg:
            if enable:
                winreg.SetValueEx(reg, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(reg, app_name)
                except FileNotFoundError:
                    pass
    except:
        pass

class WatermarkWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 无边框、置顶、工具窗口（不占任务栏）
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

        # 默认配置
        self.text = "内部资料 请勿外泄"
        self.font = QFont("微软雅黑", 14)
        self.color = QColor(180, 180, 180)
        self.opacity = 0.25
        self.rotate_angle = 30

    def set_config(self, text, font_size, opacity, color, rotate):
        self.text = text
        self.font = QFont("微软雅黑", font_size)
        self.opacity = opacity
        self.color = color
        self.rotate_angle = rotate
        self.update()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setOpacity(self.opacity)
        qp.setFont(self.font)
        qp.setPen(QPen(self.color))

        w, h = self.width(), self.height()
        step_x = 240
        step_y = 110

        # 全屏平铺绘制
        for x in range(0, w, step_x):
            for y in range(0, h, step_y):
                qp.save()
                qp.translate(x, y)
                qp.rotate(self.rotate_angle)
                qp.drawText(0, 0, self.text)
                qp.restore()

class ControlPanel(QWidget):
    def __init__(self, wm):
        super().__init__()
        self.wm = wm
        self.setWindowTitle("屏幕水印工具")
        self.resize(320, 420)
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 水印文字
        layout.addWidget(QLabel("水印文字"))
        self.text_edit = QLineEdit("内部资料 请勿外泄")
        layout.addWidget(self.text_edit)

        # 字体大小
        layout.addWidget(QLabel("字体大小"))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 120)
        self.font_size.setValue(14)
        layout.addWidget(self.font_size)

        # 透明度
        layout.addWidget(QLabel("透明度 (1~100)"))
        self.op_spin = QSpinBox()
        self.op_spin.setRange(1, 100)
        self.op_spin.setValue(25)
        layout.addWidget(self.op_spin)

        # 旋转角度
        layout.addWidget(QLabel("旋转角度 (0~360°)"))
        self.rot_spin = QSpinBox()
        self.rot_spin.setRange(0, 360)
        self.rot_spin.setValue(30)
        layout.addWidget(self.rot_spin)

        # 颜色选择
        self.color = QColor(180, 180, 180)
        self.btn_color = QPushButton("选择水印颜色")
        self.btn_color.clicked.connect(self.choose_color)
        layout.addWidget(self.btn_color)

        # 开机自启
        self.cb_start = QCheckBox("开机自动启动")
        layout.addWidget(self.cb_start)

        # 应用按钮
        self.btn_apply = QPushButton("应用水印")
        self.btn_apply.setStyleSheet("padding: 8px; font-size: 14px;")
        self.btn_apply.clicked.connect(self.apply)
        layout.addWidget(self.btn_apply)

        self.setLayout(layout)
        self.apply()

    def choose_color(self):
        c = QColorDialog.getColor(self.color, self, "选择水印颜色")
        if c.isValid():
            self.color = c

    def apply(self):
        # 应用配置
        set_startup(self.cb_start.isChecked())
        self.wm.set_config(
            text=self.text_edit.text(),
            font_size=self.font_size.value(),
            opacity=self.op_spin.value() / 100,
            color=self.color,
            rotate=self.rot_spin.value()
        )

    # 点击关闭按钮 → 最小化到托盘，不退出
    def closeEvent(self, e):
        e.ignore()
        self.hide()

class TrayIcon(QSystemTrayIcon):
    def __init__(self, panel, wm):
        super().__init__()
        self.panel = panel
        self.wm = wm

        # 托盘菜单
        menu = QMenu()
        self.act_open = menu.addAction("打开设置")
        self.act_exit = menu.addAction("退出")

        self.act_open.triggered.connect(panel.show)
        self.act_exit.triggered.connect(self.quit_all)
        self.setContextMenu(menu)
        self.activated.connect(self.on_click)

    def on_click(self, reason):
        # 左键单击托盘图标 → 打开设置
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.panel.show()

    def quit_all(self):
        # 完全退出
        self.wm.close()
        self.panel.close()
        sys.exit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 最后窗口关闭不退出程序

    wm = WatermarkWindow()
    panel = ControlPanel(wm)

    tray = TrayIcon(panel, wm)
    tray.setIcon(QIcon.fromTheme("computer"))
    tray.show()

    panel.show()
    sys.exit(app.exec())
