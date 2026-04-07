import sys
import random
import pyautogui
import keyboard
from PyQt5 import QtWidgets, QtGui, QtCore

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 1920, 1080)

        self.targets = [(random.randint(200, 1700), random.randint(200, 900)) for _ in range(5)]
        self.names = [f"Enemy{i}" for i in range(len(self.targets))]
        self.show_targets = True
        self.fov = 150
        self.locked_target = None

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        mouse_x, mouse_y = pyautogui.position()

        # Draw FOV
        painter.setPen(QtGui.QPen(QtCore.Qt.green, 2))
        painter.drawEllipse(mouse_x - self.fov, mouse_y - self.fov, self.fov*2, self.fov*2)

        if self.show_targets:
            for i, (x, y) in enumerate(self.targets):
                # Lock color
                if self.locked_target == (x, y):
                    painter.setPen(QtGui.QPen(QtCore.Qt.yellow, 3))
                else:
                    painter.setPen(QtGui.QPen(QtCore.Qt.red, 2))

                painter.drawEllipse(x, y, 20, 20)

                # Name
                painter.setPen(QtGui.QPen(QtCore.Qt.white))
                painter.drawText(x, y - 10, self.names[i])

                # Line to target if locked
                if self.locked_target == (x, y):
                    painter.setPen(QtGui.QPen(QtCore.Qt.cyan, 1))
                    painter.drawLine(mouse_x, mouse_y, x, y)


class CheatMenu(QtWidgets.QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay

        self.setWindowTitle("R6 External Client")
        self.setGeometry(100, 100, 300, 350)
        self.setStyleSheet("background-color: #111; color: white;")

        layout = QtWidgets.QVBoxLayout()

        title = QtWidgets.QLabel("R6 Cheat Simulator")
        title.setStyleSheet("font-size: 16px; color: cyan;")
        layout.addWidget(title)

        self.aim_checkbox = QtWidgets.QCheckBox("Aim Assist")
        layout.addWidget(self.aim_checkbox)

        self.esp_checkbox = QtWidgets.QCheckBox("ESP (Targets)")
        self.esp_checkbox.setChecked(True)
        self.esp_checkbox.stateChanged.connect(self.toggle_targets)
        layout.addWidget(self.esp_checkbox)

        layout.addWidget(QtWidgets.QLabel("FOV"))
        self.fov_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fov_slider.setMinimum(50)
        self.fov_slider.setMaximum(400)
        self.fov_slider.setValue(150)
        self.fov_slider.valueChanged.connect(self.update_fov)
        layout.addWidget(self.fov_slider)

        layout.addWidget(QtWidgets.QLabel("Smooth"))
        self.smooth_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.smooth_slider.setMinimum(1)
        self.smooth_slider.setMaximum(20)
        self.smooth_slider.setValue(5)
        layout.addWidget(self.smooth_slider)

        self.lock_label = QtWidgets.QLabel("Locked Targets: 0")
        layout.addWidget(self.lock_label)

        self.setLayout(layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.aim_logic)
        self.timer.start(10)

    def toggle_targets(self):
        self.overlay.show_targets = self.esp_checkbox.isChecked()

    def update_fov(self):
        self.overlay.fov = self.fov_slider.value()

    def aim_logic(self):
        if not self.aim_checkbox.isChecked():
            self.overlay.locked_target = None
            return

        mouse_x, mouse_y = pyautogui.position()
        closest = None
        min_dist = 99999

        for x, y in self.overlay.targets:
            dist = ((x - mouse_x)**2 + (y - mouse_y)**2)**0.5
            if dist < min_dist and dist < self.overlay.fov:
                min_dist = dist
                closest = (x, y)

        self.overlay.locked_target = closest

        if closest:
            tx, ty = closest
            smooth = self.smooth_slider.value()

            move_x = (tx - mouse_x) / smooth
            move_y = (ty - mouse_y) / smooth

            pyautogui.moveRel(move_x, move_y)
            self.lock_label.setText("Locked Targets: 1")
        else:
            self.lock_label.setText("Locked Targets: 0")


def main():
    app = QtWidgets.QApplication(sys.argv)

    overlay = Overlay()
    overlay.show()

    menu = CheatMenu(overlay)
    menu.show()

    def toggle_menu():
        if menu.isVisible():
            menu.hide()
        else:
            menu.show()

    keyboard.add_hotkey("F1", toggle_menu)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()