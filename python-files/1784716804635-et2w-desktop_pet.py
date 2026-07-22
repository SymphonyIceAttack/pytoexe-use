import sys
import os
import random
import math
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMenu, QAction
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QTimer, QPoint, QSize

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PetWidget(QWidget):
    def __init__(self):
        super().__init__()
        # ---------- 动画状态 ----------
        self.scale = 1.0
        self.scale_direction = 0.01          # 呼吸步长（调大更明显）
        self.blink_state = False
        self.blink_counter = 0
        self.walk_dx = 0
        self.walk_dy = 0
        self.dragging = False
        self.drag_pos = QPoint()

        # ---------- UI ----------
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.pet_label = QLabel(self)
        self.pixmap = QPixmap(resource_path("character.png"))
        if not self.pixmap.isNull():
            self.base_size = self.pixmap.size()
        else:
            self.base_size = QSize(200, 200)
        self.update_pet_size()
        self.pet_label.move(50, 50)
        self.resize(self.base_size.width() + 100, self.base_size.height() + 100)

        # ---------- 定时器 ----------
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.idle_update)
        self.idle_timer.start(30)            # 约33帧/秒

        self.walk_timer = QTimer(self)
        self.walk_timer.timeout.connect(self.random_walk)
        self.walk_timer.start(2000)

        # ---------- 调试（打包时可注释掉） ----------
        print("宠物已启动，动画循环开始")

    def update_pet_size(self):
        """更新图片大小（带呼吸缩放）"""
        w = int(self.base_size.width() * self.scale)
        h = int(self.base_size.height() * self.scale)
        scaled = self.pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pet_label.setPixmap(scaled)
        self.pet_label.setFixedSize(scaled.size())
        # 确保图片居中（可选）
        self.pet_label.move(50, 50)

    def idle_update(self):
        """每帧执行：呼吸 + 眨眼 + 走动"""
        # 1. 呼吸缩放
        self.scale += self.scale_direction
        if self.scale > 1.15 or self.scale < 0.85:   # ±15% 范围，肉眼可见
            self.scale_direction = -self.scale_direction
        self.update_pet_size()          # 更新图片
        self.update()                   # 强制重绘（触发 paintEvent）

        # 2. 眨眼（随机闭眼）
        self.blink_counter += 1
        if self.blink_counter >= random.randint(30, 90):   # 1~3秒眨一次
            self.blink_state = not self.blink_state
            self.blink_counter = 0
            self.update()               # 闭眼/睁眼都要重绘

        # 3. 随机走动
        if not self.dragging and (self.walk_dx != 0 or self.walk_dy != 0):
            x = self.x() + self.walk_dx
            y = self.y() + self.walk_dy
            screen = QApplication.primaryScreen().geometry()
            x = max(0, min(x, screen.width() - self.width()))
            y = max(0, min(y, screen.height() - self.height()))
            self.move(x, y)

        # 调试输出（确认动画在跑）
        # print(f"帧: scale={self.scale:.2f}, blink={self.blink_state}")

    def random_walk(self):
        if self.dragging:
            return
        self.walk_dx = random.choice([-2, -1, 0, 1, 2])
        self.walk_dy = random.choice([-2, -1, 0, 1, 2])
        if random.random() < 0.3:
            self.walk_dx = 0
            self.walk_dy = 0
        self.walk_timer.start(random.randint(1500, 4000))

    def paintEvent(self, event):
        """绘制眨眼线条（在角色图片上画两条黑线）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 先让子控件正常绘制（QLabel显示图片）
        super().paintEvent(event)

        if self.blink_state and not self.pixmap.isNull():
            label = self.pet_label
            rect = label.geometry()
            # 眼睛位置比例（根据你的猫图调整）
            eye_y = rect.y() + int(rect.height() * 0.40)
            eye_width = int(rect.width() * 0.12)
            painter.setPen(QPen(QColor(0, 0, 0), 3))
            # 左眼
            x1 = rect.x() + int(rect.width() * 0.30)
            painter.drawLine(x1, eye_y, x1 + eye_width, eye_y)
            # 右眼
            x2 = rect.x() + int(rect.width() * 0.55)
            painter.drawLine(x2, eye_y, x2 + eye_width, eye_y)

    # ---------- 鼠标交互（保留拖拽和右键菜单） ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def show_context_menu(self, pos):
        menu = QMenu(self)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        menu.exec_(pos)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pet = PetWidget()
    pet.move(400, 300)
    pet.show()
    sys.exit(app.exec_())