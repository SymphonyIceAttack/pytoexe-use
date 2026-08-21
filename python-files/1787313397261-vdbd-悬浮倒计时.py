import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont


class FloatCountDown(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.total_seconds = 0
        self.running = False
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_countdown)
        self.drag_pos = None

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(320, 180)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        time_layout = QHBoxLayout()
        self.edit_h = QLineEdit("00")
        self.edit_m = QLineEdit("00")
        self.edit_s = QLineEdit("10")
        for edit in [self.edit_h, self.edit_m, self.edit_s]:
            edit.setMaxLength(2)
            edit.setFont(QFont("Microsoft YaHei", 14))
            edit.setFixedWidth(55)
        time_layout.addWidget(self.edit_h)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.edit_m)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.edit_s)

        self.label_time = QLabel("00:00:10")
        self.label_time.setFont(QFont("Microsoft YaHei", 32, QFont.Bold))
        self.label_time.setAlignment(Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("开始")
        self.btn_reset = QPushButton("重置")
        self.btn_close = QPushButton("关闭")
        self.btn_start.clicked.connect(self.start_count)
        self.btn_reset.clicked.connect(self.reset_count)
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.btn_close)

        main_layout.addLayout(time_layout)
        main_layout.addWidget(self.label_time)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def start_count(self):
        if self.running:
            self.timer.stop()
            self.running = False
            self.btn_start.setText("开始")
            return
        try:
            h = int(self.edit_h.text())
            m = int(self.edit_m.text())
            s = int(self.edit_s.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入数字")
            return
        self.total_seconds = h * 3600 + m * 60 + s
        if self.total_seconds <= 0:
            QMessageBox.warning(self, "提示", "时间必须大于0")
            return
        self.running = True
        self.btn_start.setText("暂停")
        self.timer.start()

    def update_countdown(self):
        self.total_seconds -= 1
        if self.total_seconds <= 0:
            self.timer.stop()
            self.running = False
            self.btn_start.setText("开始")
            QMessageBox.information(self, "倒计时结束", "时间到！")
            self.reset_count()
            return
        h = self.total_seconds // 3600
        m = (self.total_seconds % 3600) // 60
        s = self.total_seconds % 60
        self.label_time.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def reset_count(self):
        self.timer.stop()
        self.running = False
        self.btn_start.setText("开始")
        self.label_time.setText("00:00:00")
        self.edit_h.setText("00")
        self.edit_m.setText("00")
        self.edit_s.setText("00")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        self.drag_pos = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FloatCountDown()
    win.show()
    sys.exit(app.exec_())