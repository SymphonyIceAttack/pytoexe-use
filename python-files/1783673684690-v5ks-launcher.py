import sys
import json
import os
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QMessageBox, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QColor, QLinearGradient, QBrush, QPixmap, QPainter, QRadialGradient

# ======================== Хранилище пользователей ========================
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# ======================== Анимированный фон с частицами ========================
class ParticleBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(25)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(0, 0, parent.width(), parent.height())

    def showEvent(self, event):
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.generate_particles()

    def generate_particles(self):
        self.particles = []
        for _ in range(80):
            x = random.randint(0, self.width())
            y = random.randint(0, self.height())
            speed = random.uniform(0.4, 1.8)
            size = random.randint(2, 5)
            alpha = random.randint(120, 255)
            self.particles.append([x, y, speed, size, alpha])

    def update_particles(self):
        for p in self.particles:
            p[1] += p[2] * 0.6
            p[0] += random.uniform(-0.3, 0.3)
            if p[1] > self.height():
                p[1] = 0
                p[0] = random.randint(0, self.width())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(18, 10, 30))
        gradient.setColorAt(0.5, QColor(35, 18, 55))
        gradient.setColorAt(1, QColor(10, 8, 20))
        painter.fillRect(self.rect(), gradient)

        for p in self.particles:
            alpha = p[3]
            color = QColor(255, 160, 50, alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            # Рисуем свечение
            radial = QRadialGradient(p[0], p[1], p[4] * 2)
            radial.setColorAt(0, QColor(255, 200, 100, alpha))
            radial.setColorAt(1, QColor(255, 100, 0, 0))
            painter.setBrush(radial)
            painter.drawEllipse(p[0] - p[4], p[1] - p[4], p[4] * 2, p[4] * 2)

# ======================== Окно регистрации ========================
class RegisterWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Регистрация — FlamyLauncher")
        self.setFixedSize(400, 320)
        self.setStyleSheet("background-color: #1c1c2e; color: white;")
        self.center()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        title = QLabel("✨ Создать аккаунт")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Придумайте логин")
        self.login_input.setStyleSheet("padding: 10px; border-radius: 8px; background: #2a2a3e; color: white; font-size: 13px;")
        layout.addWidget(self.login_input)

        self.pass_input = QLineEdit(


)
        self.pass_input.setPlaceholderText("Пароль")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet("padding: 10px; border-radius: 8px; background: #2a2a3e; color: white; font-size: 13px;")
        layout.addWidget(self.pass_input)

        self.pass_confirm = QLineEdit()
        self.pass_confirm.setPlaceholderText("Повторите пароль")
        self.pass_confirm.setEchoMode(QLineEdit.Password)
        self.pass_confirm.setStyleSheet("padding: 10px; border-radius: 8px; background: #2a2a3e; color: white; font-size: 13px;")
        layout.addWidget(self.pass_confirm)

        self.register_btn = QPushButton("✅ Зарегистрироваться")
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff7e5f, stop:1 #feb47b);
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6a4a, stop:1 #fd9a6a);
            }
        """)
        self.register_btn.clicked.connect(self.register)
        layout.addWidget(self.register_btn)

        self.back_btn = QPushButton("← Назад")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #2a2a3e;
                color: white;
            }
        """)
        self.back_btn.clicked.connect(self.close)
        layout.addWidget(self.back_btn)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def register(self):
        login = self.login_input.text().strip()
        password = self.pass_input.text()
        confirm = self.pass_confirm.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Все поля обязательны.")
            return
        if password != confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Ошибка", "Пароль должен быть не менее 4 символов.")
            return

        users = load_users()
        if login in users:
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует.")
            return

        users[login] = password
        save_users(users)
        QMessageBox.information(self, "Успех", "Аккаунт создан! Теперь войдите.")
        self.close()

# ======================== Главное окно лаунчера ========================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlamyLauncher")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.center()

        # Центральный виджет с фоном
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)

        # Фон с частицами
        self.bg = ParticleBackground(self.central_widget)
        self.bg.lower()

        # Основной layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        # Заголовок с логотипом (текстовый или из файла)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        logo_pixmap = None
        if os.path.exi


sts("logo.png"):
            logo_pixmap = QPixmap("logo.png").scaled(200, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            logo_pixmap = QPixmap(200, 80)
            logo_pixmap.fill(Qt.transparent)
            painter = QPainter(logo_pixmap)
            painter.setPen(QColor(255, 180, 100))
            painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
            painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "Flamy")
            painter.end()
        self.logo_label.setPixmap(logo_pixmap)
        main_layout.addWidget(self.logo_label)

        # Стек для переключения между входом и главным меню
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # ---- Страница входа ----
        login_page = QWidget()
        login_layout = QVBoxLayout(login_page)
        login_layout.setSpacing(12)

        login_label = QLabel("Вход в аккаунт")
        login_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        login_label.setAlignment(Qt.AlignCenter)
        login_label.setStyleSheet("color: #f0d0b0;")
        login_layout.addWidget(login_label)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")
        self.login_input.setStyleSheet("padding: 10px; border-radius: 8px; background: #2a2a3e; color: white; font-size: 13px;")
        login_layout.addWidget(self.login_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Пароль")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet("padding: 10px; border-radius: 8px; background: #2a2a3e; color: white; font-size: 13px;")
        login_layout.addWidget(self.pass_input)

        self.login_btn = QPushButton("🔥 Войти")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff7e5f, stop:1 #feb47b);
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6a4a, stop:1 #fd9a6a);
            }
        """)
        self.login_btn.clicked.connect(self.login)
        login_layout.addWidget(self.login_btn)

        self.register_btn = QPushButton("Создать аккаунт")
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #f0d0b0;
                border: 2px solid #ff7e5f;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2a2a3e;
            }
        """)
        self.register_btn.clicked.connect(self.open_register)
        login_layout.addWidget(self.register_btn)

        self.stack.addWidget(login_page)

        # ---- Главное меню (после входа) ----
        menu_page = QWidget()
        menu_layout = QVBoxLayout(menu_page)
        menu_layout.setSpacing(12)

        welcome_label = QLabel("Добро пожаловать, <user>!")
        welcome_label.setObjectName("welcome")
        welcome_label.setFont(QFont("Segoe UI", 14))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #f0d0b0;")
        menu_layout.addWidget(welcome_label)

        # Версия Minecraft
        version_label = QLabel("Выберите версию:")
        version_label.setStyleSheet("color: #ccc; font-size: 13px;")
        menu_layout.addWidget(version_label)

        self.version_combo = QComboBox()
        # Список версий от 1.8.9 до 1.21.11 (основные релизы)
        versions = [
            "1.8.9", "1.9", "1.9.4", "1.10.2", "1.11.2", "1.12.2",
            "1.13.2", "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
            "1.1


9.2", "1.19.4", "1.20.1", "1.20.4", "1.21", "1.21.1",
            "1.21.3", "1.21.4", "1.21.11"
        ]
        self.version_combo.addItems(versions)
        self.version_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border-radius: 8px;
                background: #2a2a3e;
                color: white;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background: #2a2a3e;
                color: white;
                selection-background-color: #ff7e5f;
            }
        """)
        menu_layout.addWidget(self.version_combo)

        # Загрузчик
        loader_label = QLabel("Выберите загрузчик:")
        loader_label.setStyleSheet("color: #ccc; font-size: 13px;")
        menu_layout.addWidget(loader_label)

        self.loader_combo = QComboBox()
        self.loader_combo.addItems(["Fabric", "Forge", "OptiFine", "Forge+OptiFine"])
        self.loader_combo.setStyleSheet(self.version_combo.styleSheet())
        menu_layout.addWidget(self.loader_combo)

        # Кнопка "Играть"
        self.play_btn = QPushButton("▶ Играть")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f7971e, stop:1 #ffd200);
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-size: 16px;
                font-weight: bold;
                color: #1c1c2e;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e68a1e, stop:1 #f0c800);
            }
        """)
        self.play_btn.clicked.connect(self.play)
        menu_layout.addWidget(self.play_btn)

        # Кнопка выхода
        self.logout_btn = QPushButton("🚪 Выйти")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaa;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #2a2a3e;
                color: white;
            }
        """)
        self.logout_btn.clicked.connect(self.logout)
        menu_layout.addWidget(self.logout_btn)

        self.stack.addWidget(menu_page)

        # По умолчанию показываем страницу входа
        self.stack.setCurrentIndex(0)

        # Текущий пользователь
        self.current_user = None

        # Кнопка закрытия (крестик) - в верхнем правом углу
        self.close_btn = QPushButton("✕", self.central_widget)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ccc;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff5555;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.move(self.width() - 40, 10)

        # Анимация появления
        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def resizeEvent(self, event):
        self.bg.setGeometry(0, 0, self.width(), self.height())
        self.close_btn.move(self.width() - 40, 10)

    def open_register(self):
        self.register_window = RegisterWindow(self)
        self.register_window.show()

    def login(self):


login = self.login_input.text().strip()
        password = self.pass_input.text()
        users = load_users()
        if login in users and users[login] == password:
            self.current_user = login
            self.stack.setCurrentIndex(1)
            # Обновить приветствие
            welcome = self.findChild(QLabel, "welcome")
            if welcome:
                welcome.setText(f"Добро пожаловать, {login}!")
            self.login_input.clear()
            self.pass_input.clear()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")

    def logout(self):
        self.current_user = None
        self.stack.setCurrentIndex(0)

    def play(self):
        version = self.version_combo.currentText()
        loader = self.loader_combo.currentText()
        msg = f"🚀 Запуск Minecraft {version} с загрузчиком {loader}\n(реальная реализация требует интеграции с официальным лаунчером)"
        QMessageBox.information(self, "Запуск", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


