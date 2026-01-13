import sys
import os
import json
import webbrowser
import winsound
import winreg
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QCheckBox, QMessageBox, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QTimer

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

PINK = "#ff4fa3"
NEON_BLUE = "#5ee7ff"
GRAY = "#5a5f6a"
BG_COLOR = "#0b0614"
CARD_BG = "#140c24"
VOTE_URL = "https://top-serveurs.net/gta/vote/alibirp"
TIMER_INTERVAL = 30
CONFIG_FILE = "config.json"
SOUND_FILE = "alert.wav"

class AlibiRPVote(QWidget):
    def __init__(self):
        super().__init__()
        self.remaining_time = 0
        self.timer_active = False
        self.sound_step = 0
        self.setWindowTitle("ALIBIRP – CYBER VOTE")
        self.setFixedSize(420, 600)
        self.setStyleSheet(f"background:{BG_COLOR}; color:white;")
        self.vote_timer = QTimer(self)
        self.vote_timer.timeout.connect(self.vote_ready)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.sound_timer = QTimer(self)
        self.sound_timer.timeout.connect(self.play_sound_sequence)
        self.init_ui()
        self.init_tray()
        self.enable_startup()
        self.load_pseudo()
        self.set_available()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignTop)
        logo = QLabel()
        logo.setPixmap(QPixmap(resource_path("logo.png")).scaled(130,130,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        self.timer_label = QLabel("00:30")
        self.timer_label.setFont(QFont("Consolas", 28, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(f"color:{NEON_BLUE};")
        layout.addWidget(self.timer_label)
        self.status_label = QLabel("DISPONIBLE")
        self.status_label.setFont(QFont("Arial", 15, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        self.vote_btn = QPushButton("ALLER VOTER")
        self.vote_btn.setMinimumHeight(60)
        self.vote_btn.clicked.connect(self.open_vote_page)
        layout.addWidget(self.vote_btn)
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(45)
        self.glow.setOffset(0)
        self.vote_btn.setGraphicsEffect(self.glow)
        card = QWidget()
        card.setStyleSheet(f"background:{CARD_BG}; border-radius:18px; padding:20px;")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(QLabel("Nom & Prénom RP"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex : Titouan Dong")
        self.name_input.setStyleSheet("background:black; border-radius:10px; padding:8px; color:white;")
        card_layout.addWidget(self.name_input)
        self.popup_checkbox = QCheckBox("Activer le rappel automatique")
        self.popup_checkbox.setChecked(True)
        card_layout.addWidget(self.popup_checkbox)
        layout.addWidget(card)
        quit_btn = QPushButton("QUITTER")
        quit_btn.setStyleSheet("background:#b91c1c; border-radius:14px; padding:10px; color:white;")
        quit_btn.clicked.connect(QApplication.quit)
        layout.addWidget(quit_btn)

    def start_timer(self):
        self.remaining_time = TIMER_INTERVAL
        self.vote_timer.start(TIMER_INTERVAL * 1000)
        self.countdown_timer.start(1000)
        self.timer_active = True
        self.set_unavailable()

    def update_countdown(self):
        self.remaining_time -= 1
        if self.remaining_time <= 0:
            self.timer_label.setText("00:00")
            return
        self.timer_label.setText(f"00:{self.remaining_time:02d}")

    def vote_ready(self):
        self.vote_timer.stop()
        self.countdown_timer.stop()
        self.timer_active = False
        self.set_available()
        self.show(); self.raise_(); self.activateWindow()
        self.tray.showMessage("Vote AlibiRP", "⏰ Tu peux revoter maintenant 💖", QSystemTrayIcon.Information, 8000)
        if self.popup_checkbox.isChecked():
            self.sound_step = 0
            self.sound_timer.start(200)

    def play_sound_sequence(self):
        pattern = [True, True, False, False, True, True, False, False, True, True]
        if self.sound_step >= len(pattern):
            self.sound_timer.stop()
            return
        if pattern[self.sound_step]:
            if os.path.exists(resource_path(SOUND_FILE)):
                winsound.PlaySound(resource_path(SOUND_FILE), winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.sound_step += 1

    def set_available(self):
        self.status_label.setText("DISPONIBLE")
        self.status_label.setStyleSheet(f"color:{PINK};")
        self.glow.setEnabled(True)
        self.glow.setColor(QColor(PINK))
        self.vote_btn.setStyleSheet(f"QPushButton {{background:{PINK}; color:black; border-radius:30px; font-size:16px; font-weight:bold; padding:15px;}}")

    def set_unavailable(self):
        self.status_label.setText("INDISPONIBLE")
        self.status_label.setStyleSheet(f"color:{GRAY};")
        self.glow.setEnabled(False)
        self.vote_btn.setStyleSheet(f"QPushButton {{background:{GRAY}; color:black; border-radius:30px; font-size:16px; font-weight:bold; padding:15px;}}")

    def open_vote_page(self):
        pseudo = self.name_input.text().strip()
        if not pseudo:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer votre pseudo RP.")
            return
        self.save_pseudo(pseudo)
        webbrowser.open(f"{VOTE_URL}?pseudo={pseudo.replace(' ', '%20')}")
        self.start_timer()

    def save_pseudo(self, pseudo):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"pseudo": pseudo}, f)

    def load_pseudo(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.name_input.setText(data.get("pseudo", ""))
            except:
                pass

    def init_tray(self):
        self.tray = QSystemTrayIcon(QIcon(resource_path("icon.ico")), self)
        menu = QMenu()
        menu.addAction("Ouvrir", self.show)
        menu.addAction("Voter", self.open_vote_page)
        menu.addAction("Quitter", QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def enable_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AlibiRPVote", 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(key)
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlibiRPVote()
    window.show()
    sys.exit(app.exec_())
