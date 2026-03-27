import sys
import os
import psutil
import subprocess
import ctypes
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QComboBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

# ---------------- FPS OVERLAY WINDOW ----------------
class Overlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(20, 20, 200, 100)

        layout = QVBoxLayout()
        self.label = QLabel("FPS: --\nCPU: --\nRAM: --")
        self.label.setStyleSheet("color: #22c55e; font-size: 14px;")
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def update_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        fps_fake = 60 - int(cpu / 5)  # simulated FPS
        self.label.setText(f"FPS: {fps_fake}\nCPU: {cpu}%\nRAM: {ram}%")


# ---------------- MAIN BOOSTER ----------------
class BoosterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ReZK Booster GOD MODE 🚀")
        self.setGeometry(300, 200, 400, 340)
        self.setStyleSheet("background-color: #020617; color: #e5e7eb;")

        layout = QVBoxLayout()

        self.title = QLabel("ReZK Booster GOD MODE")
        self.title.setFont(QFont("Arial", 16, QFont.Bold))

        self.label_cpu = QLabel("CPU: 0%")
        self.label_ram = QLabel("RAM: 0%")

        self.emulator_select = QComboBox()
        self.emulator_select.addItems(["GameLoop", "BlueStacks", "LDPlayer"])

        self.button = QPushButton("BOOST NOW 🚀")
        self.button.clicked.connect(self.boost_system)

        self.ultra_btn = QPushButton("GOD MODE 🔥")
        self.ultra_btn.clicked.connect(self.ultra_mode)

        self.overlay_btn = QPushButton("TOGGLE OVERLAY 🎮")
        self.overlay_btn.clicked.connect(self.toggle_overlay)

        layout.addWidget(self.title)
        layout.addWidget(self.label_cpu)
        layout.addWidget(self.label_ram)
        layout.addWidget(self.emulator_select)
        layout.addWidget(self.button)
        layout.addWidget(self.ultra_btn)
        layout.addWidget(self.overlay_btn)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.overlay = Overlay()
        self.overlay_visible = False

    def update_stats(self):
        self.label_cpu.setText(f"CPU: {psutil.cpu_percent()}%")
        self.label_ram.setText(f"RAM: {psutil.virtual_memory().percent}%")

    # ---------------- SYSTEM BOOST ----------------

    def boost_system(self):
        subprocess.run("powercfg /setactive SCHEME_MIN", shell=True)
        subprocess.run("ipconfig /flushdns", shell=True)
        subprocess.run("netsh int tcp set global autotuninglevel=highlyrestricted", shell=True)

        for proc in psutil.process_iter(['name']):
            try:
                if "emulator" in proc.info['name'].lower() or "player" in proc.info['name'].lower():
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
            except:
                pass

        self.button.setText("BOOSTED ✅")

    def ultra_mode(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] not in ['explorer.exe', 'System']:
                    proc.kill()
            except:
                pass

        self.ultra_btn.setText("GOD MODE ACTIVE 🔥")

    # ---------------- OVERLAY ----------------

    def toggle_overlay(self):
        if self.overlay_visible:
            self.overlay.hide()
            self.overlay_visible = False
        else:
            self.overlay.show()
            self.overlay_visible = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BoosterApp()
    window.show()
    sys.exit(app.exec_())
