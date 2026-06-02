
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import subprocess
import threading
import warnings
from datetime import timedelta, datetime
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = app_path()
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
BG_PATH = os.path.join(BASE_DIR, "fon.jpg")

# ---------- Фикс плагинов Qt ----------
def fix_qt_plugin_path():
    # Проверяем пользовательскую папку
    custom_plugins = r"A:\My Fille\GameLoderPC\plugins"
    if os.path.exists(custom_plugins):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = custom_plugins
        return
    try:
        import PyQt5
        pyqt_path = Path(PyQt5.__file__).parent
        candidates = [
            pyqt_path / "Qt5" / "plugins",
            pyqt_path / "Qt" / "plugins",
            pyqt_path / "plugins",
        ]
        for candidate in candidates:
            if candidate.exists():
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(candidate)
                return
        if getattr(sys, 'frozen', False):
            plugin_path = os.path.join(os.path.dirname(sys.executable), 'plugins')
            if os.path.exists(plugin_path):
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path
                return
    except Exception:
        pass

fix_qt_plugin_path()
# ------------------------------------

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QStackedWidget,
    QFileDialog, QInputDialog, QMessageBox, QListWidget, QListWidgetItem,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QEvent, QSize
from PyQt5.QtGui import QPixmap, QFont, QWheelEvent, QPalette, QBrush, QKeyEvent, QGuiApplication, QIcon, QColor

try:
    import pygame
    import pygame.joystick
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# ---------------------------- GameProcessWatcher ----------------------------
class GameProcessWatcher(QObject):
    finished = pyqtSignal(str, int)
    def __init__(self, game_id, process):
        super().__init__()
        self.game_id = game_id
        self.process = process
        self.start_time = time.time()
    def run(self):
        self.process.wait()
        elapsed = int(time.time() - self.start_time)
        self.finished.emit(self.game_id, elapsed)

# ---------------------------- HorizontalScrollFilter ----------------------------
class HorizontalScrollFilter(QObject):
    def __init__(self, scroll_area):
        super().__init__(scroll_area)
        self.scroll_area = scroll_area
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            delta = event.angleDelta().y()
            self.scroll_area.horizontalScrollBar().setValue(
                self.scroll_area.horizontalScrollBar().value() - delta
            )
            return True
        return super().eventFilter(obj, event)

# ---------------------------- Main Window ----------------------------
class PS5Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Launcher")
        self.setStyleSheet("background-color: transparent;")
        self.setMinimumSize(1300, 800)

        if os.path.exists(BG_PATH):
            self.bg_pixmap = QPixmap(BG_PATH)
            self.bg_pixmap = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.update_background()
        else:
            print(f"Фон не найден: {BG_PATH}")
            self.setStyleSheet("background-color: #0a0c10;")
            self.bg_pixmap = None

        self.data_file = os.path.join(BASE_DIR, "launcher_data.json")
        self.load_data()
        self.active_processes = {}
        self.init_ui()

        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_background)
        self.resize_timer.setInterval(100)

        if PYGAME_AVAILABLE:
            self.init_gamepad()
        else:
            self.gamepad_running = False

    # ---------------------- Gamepad, keyboard, background, data ----------------------
    def init_gamepad(self):
        try:
            pygame.init()
            pygame.joystick.init()
            if pygame.joystick.get_count() == 0:
                print("Геймпад не найден")
                return
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.gamepad_running = True
            self.gamepad_thread = threading.Thread(target=self.gamepad_loop, daemon=True)
            self.gamepad_thread.start()
        except Exception as e:
            print(f"Ошибка геймпада: {e}")
            self.gamepad_running = False

    def gamepad_loop(self):
        while getattr(self, 'gamepad_running', False):
            try:
                pygame.event.pump()
                axis_x = self.joystick.get_axis(0)
                if abs(axis_x) > 0.5:
                    delta = int(axis_x * 20)
                    if hasattr(self, 'scroll_area'):
                        QTimer.singleShot(0, lambda d=delta: self.scroll_area.horizontalScrollBar().setValue(
                            self.scroll_area.horizontalScrollBar().value() + d
                        ))
                time.sleep(0.05)
            except:
                break

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F12:
            self.close()
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        if self.bg_pixmap:
            self.resize_timer.start()
        super().resizeEvent(event)

    def update_background(self):
        if self.bg_pixmap:
            scaled = self.bg_pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled))
            self.setPalette(palette)

    def load_data(self):
        default_data = {
            "profile": {"nickname": "Gamer", "avatar": "", "background": ""},
            "games": {},
            "achievements": {}
        }
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]
                self.data = data
            except:
                self.data = default_data
                self.add_demo_game()
        else:
            self.data = default_data
            self.add_demo_game()
        self.save_data()

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def add_demo_game(self):
        gid = "demo_game"
        self.data["games"][gid] = {"name": "Cyberpunk 2077", "path": "", "icon": "", "total_time": 0}
        self.data["achievements"][gid] = {
            "ach1": {"name": "Новичок", "desc": "1 час", "unlocked": False, "condition_hours": 1},
            "ach2": {"name": "Опытный", "desc": "5 часов", "unlocked": False, "condition_hours": 5},
            "ach3": {"name": "Фанат", "desc": "20 часов", "unlocked": False, "condition_hours": 20}
        }

    # ---------------------- UI ----------------------
    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_panel = QFrame()
        left_panel.setFixedWidth(240)
        left_panel.setStyleSheet("background-color: rgba(20, 25, 35, 160); border-right: 1px solid rgba(255,255,255,30);")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(20, 40, 20, 40)
        left_layout.setSpacing(30)

        logo = QLabel("GAME HUB")
        logo.setFont(QFont("Arial", 22, QFont.Bold))
        logo.setStyleSheet("color: #ffffff;")
        left_layout.addWidget(logo)

        self.btn_games = self.create_menu_button("ИГРЫ")
        self.btn_games.clicked.connect(lambda: self.stack.setCurrentWidget(self.games_screen))
        left_layout.addWidget(self.btn_games)

        self.btn_media = self.create_menu_button("MEDIA")
        self.btn_media.clicked.connect(lambda: self.stack.setCurrentWidget(self.media_screen))
        left_layout.addWidget(self.btn_media)

        self.btn_profile = self.create_menu_button("ПРОФИЛЬ")
        self.btn_profile.clicked.connect(lambda: self.stack.setCurrentWidget(self.profile_screen))
        left_layout.addWidget(self.btn_profile)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: transparent;")

        self.games_screen = QWidget()
        self.setup_games_screen()
        self.stack.addWidget(self.games_screen)

        self.media_screen = QWidget()
        self.setup_media_screen()
        self.stack.addWidget(self.media_screen)

        self.profile_screen = QWidget()
        self.setup_profile_screen()
        self.stack.addWidget(self.profile_screen)

        self.stack.setCurrentWidget(self.games_screen)
        self.update_menu_styles()
        self.stack.currentChanged.connect(self.on_stack_changed)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.stack, 1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def create_menu_button(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 20px;
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                border: none;
                color: #e0e0e0;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,40);
                color: #ffffff;
            }
        """)
        return btn

    def update_menu_styles(self):
        current = self.stack.currentWidget()
        for btn, screen in [
            (self.btn_games, self.games_screen),
            (self.btn_media, self.media_screen),
            (self.btn_profile, self.profile_screen)
        ]:
            if screen == current:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 20px;
                        font-size: 16px;
                        font-weight: bold;
                        background-color: rgba(26,188,156,150);
                        color: #ffffff;
                        border-radius: 10px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding-left: 20px;
                        font-size: 16px;
                        font-weight: bold;
                        background-color: transparent;
                        border: none;
                        color: #e0e0e0;
                        border-radius: 10px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255,255,255,40);
                        color: #ffffff;
                    }
                """)

    def on_stack_changed(self, index):
        self.update_menu_styles()

    def update_clock(self):
        now = datetime.now().strftime("%H:%M")
        if hasattr(self, 'clock_label'):
            self.clock_label.setText(now)

    # ---------------------- Games Screen ----------------------
    def setup_games_screen(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(30)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        self.clock_label = QLabel()
        self.clock_label.setFont(QFont("Arial", 14))
        self.clock_label.setStyleSheet("background-color: rgba(30,36,48,180); color: white; padding: 5px 15px; border-radius: 20px;")
        top_bar.addWidget(self.clock_label, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        add_btn = QPushButton("+ Добавить игру")
        add_btn.setStyleSheet("QPushButton { background-color: rgba(44,62,80,180); border-radius: 20px; padding: 8px 20px; font-size: 13px; } QPushButton:hover { background-color: rgba(26,188,156,200); }")
        add_btn.clicked.connect(self.add_new_game)
        top_bar.addWidget(add_btn)
        left_layout.addLayout(top_bar)

        title = QLabel("Мои игры")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-top: 20px; margin-bottom: 20px;")
        left_layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_filter = HorizontalScrollFilter(self.scroll_area)
        self.scroll_area.installEventFilter(self.scroll_filter)

        self.games_container = QWidget()
        self.games_layout = QHBoxLayout()
        self.games_layout.setContentsMargins(0, 10, 0, 10)
        self.games_layout.setSpacing(30)
        self.games_container.setLayout(self.games_layout)
        self.scroll_area.setWidget(self.games_container)

        left_layout.addWidget(self.scroll_area)
        left_widget.setLayout(left_layout)

        self.news_widget = QFrame()
        self.news_widget.setFixedWidth(350)
        self.news_widget.setStyleSheet("background-color: rgba(20,25,35,150); border-radius: 20px;")
        news_layout = QVBoxLayout()
        news_layout.setContentsMargins(20, 20, 20, 20)

        news_header = QHBoxLayout()
        news_title = QLabel("НОВОСТИ")
        news_title.setFont(QFont("Arial", 18, QFont.Bold))
        news_title.setStyleSheet("color: #1abc9c;")
        news_header.addWidget(news_title)
        news_header.addStretch()
        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedSize(30,30)
        self.collapse_btn.setStyleSheet("background-color: rgba(30,36,48,160); border-radius:15px;")
        self.collapse_btn.clicked.connect(self.toggle_news)
        news_header.addWidget(self.collapse_btn)
        news_layout.addLayout(news_header)

        self.news_container = QWidget()
        self.news_inner_layout = QVBoxLayout()
        self.news_container.setLayout(self.news_inner_layout)
        for game, headline, desc in [("Fortnite","Новый костюм Веном","Симбиот теперь в игре!"),
                                     ("GTA Online","Гоночные уикенды","Новые трассы"),
                                     ("Cyberpunk 2077","Обновление 2.0","Переработанные навыки"),
                                     ("Deep Stone","Рейд доступен","Испытание для кланов")]:
            card = self.create_news_card(game, headline, desc)
            self.news_inner_layout.addWidget(card)
        self.news_inner_layout.addStretch()
        news_layout.addWidget(self.news_container)
        self.news_widget.setLayout(news_layout)

        layout.addWidget(left_widget, 2)
        layout.addWidget(self.news_widget, 1)
        self.games_screen.setLayout(layout)
        self.refresh_games_list()
        self.news_expanded = True

    def create_news_card(self, game, headline, desc):
        card = QFrame()
        card.setStyleSheet("background-color: rgba(30,36,48,150); border-radius:15px; margin-top:15px;")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15,15,15,15)
        title = QLabel(f"🎮 {game}")
        title.setFont(QFont("Arial",14,QFont.Bold))
        title.setStyleSheet("color:#ffffff;")
        head = QLabel(headline)
        head.setStyleSheet("color:#1abc9c; font-size:13px;")
        dsc = QLabel(desc)
        dsc.setStyleSheet("color:#b0b3b8; font-size:12px;")
        card_layout.addWidget(title)
        card_layout.addWidget(head)
        card_layout.addWidget(dsc)
        card.setLayout(card_layout)
        return card

    def toggle_news(self):
        if self.news_expanded:
            self.news_widget.setFixedWidth(0)
            self.news_widget.setVisible(False)
            self.collapse_btn.setText("▶")
            self.news_expanded = False
        else:
            self.news_widget.setFixedWidth(350)
            self.news_widget.setVisible(True)
            self.collapse_btn.setText("◀")
            self.news_expanded = True

    def refresh_games_list(self):
        for i in reversed(range(self.games_layout.count())):
            w = self.games_layout.itemAt(i).widget()
            if w: w.deleteLater()
        for gid, info in self.data["games"].items():
            self.games_layout.addWidget(self.create_game_card(gid, info))

    def create_game_card(self, game_id, game_info):
        card = QFrame()
        card.setFixedSize(300, 360)
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(30,36,48,180);
                border-radius: 20px;
            }
            QFrame:hover {
                background-color: rgba(44,62,80,200);
                border: 1px solid rgba(26,188,156,150);
            }
        """)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_path = game_info.get("icon", "")
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🎮")
            icon_label.setFont(QFont("Arial", 90))
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("color:#1abc9c;")
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        name = QLabel(game_info["name"])
        name.setFont(QFont("Arial", 16, QFont.Bold))
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet("color:white;")
        layout.addWidget(name)

        total_sec = game_info.get("total_time",0)
        time_str = str(timedelta(seconds=total_sec)).split('.')[0]
        time_lbl = QLabel(f"🕒 {time_str}")
        time_lbl.setAlignment(Qt.AlignCenter)
        time_lbl.setStyleSheet("color:#b0b3b8; font-size:12px;")
        layout.addWidget(time_lbl)

        play_btn = QPushButton("▶ Играть")
        play_btn.setStyleSheet("QPushButton { background-color: rgba(26,188,156,200); border-radius:15px; padding:6px; font-weight:bold; font-size:13px; } QPushButton:hover { background-color: rgba(22,160,133,200); }")
        play_btn.clicked.connect(lambda ch, gid=game_id: self.launch_game(gid))
        layout.addWidget(play_btn)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(30,30)
        del_btn.setStyleSheet("QPushButton { background-color: rgba(192,57,43,200); border-radius:15px; font-size:12px; }")
        del_btn.clicked.connect(lambda ch, gid=game_id: self.delete_single_game(gid))
        layout.addWidget(del_btn, alignment=Qt.AlignRight)

        card.setLayout(layout)
        return card

    def delete_single_game(self, game_id):
        confirm = QMessageBox.question(self, "Удалить", f"Удалить '{self.data['games'][game_id]['name']}'?",
                                       QMessageBox.Yes|QMessageBox.No)
        if confirm == QMessageBox.Yes:
            del self.data["games"][game_id]
            del self.data["achievements"][game_id]
            self.save_data()
            self.refresh_games_list()
            if self.stack.currentWidget() == self.profile_screen:
                self.refresh_profile_screen()

    # ---------------------- Media Screen (Screenshots) ----------------------
    def setup_media_screen(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        top_layout = QHBoxLayout()
        title = QLabel("MEDIA — Скриншоты игр")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        screenshot_btn = QPushButton("📸 Сделать скриншот")
        screenshot_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(26,188,156,200);
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(22,160,133,200);
            }
        """)
        screenshot_btn.clicked.connect(self.take_screenshot)
        top_layout.addWidget(screenshot_btn)

        layout.addLayout(top_layout)

        self.screenshots_list = QListWidget()
        self.screenshots_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.screenshots_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(30,36,48,180);
                border-radius: 20px;
                padding: 10px;
                color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid rgba(255,255,255,30);
            }
            QListWidget::item:selected {
                background-color: rgba(26,188,156,150);
            }
        """)
        self.screenshots_list.setIconSize(QSize(120, 68))
        self.screenshots_list.itemDoubleClicked.connect(self.open_screenshot)
        layout.addWidget(self.screenshots_list)

        delete_btn = QPushButton("🗑 Удалить выбранные скриншоты")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(192,57,43,200);
                border-radius: 20px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(231,76,60,200);
            }
        """)
        delete_btn.clicked.connect(self.delete_selected_screenshots)
        layout.addWidget(delete_btn, alignment=Qt.AlignRight)

        widget.setLayout(layout)
        self.media_screen = widget
        self.refresh_screenshots_list()

    def take_screenshot(self):
        try:
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить доступ к экрану")
                return
            screenshot = screen.grabWindow(0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(SCREENSHOTS_DIR, filename)
            if screenshot.save(filepath, "PNG"):
                QMessageBox.information(self, "Успех", f"Скриншот сохранён:\n{filename}")
                self.refresh_screenshots_list()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить скриншот")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def refresh_screenshots_list(self):
        self.screenshots_list.clear()
        if not os.path.exists(SCREENSHOTS_DIR):
            return
        files = []
        for f in os.listdir(SCREENSHOTS_DIR):
            if f.lower().endswith(".png"):
                filepath = os.path.join(SCREENSHOTS_DIR, f)
                stat = os.stat(filepath)
                files.append((stat.st_mtime, f, filepath))
        files.sort(reverse=True)
        for mtime, filename, filepath in files:
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(120, 68, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(pixmap)
            else:
                icon = QIcon()
            item = QListWidgetItem()
            item.setIcon(icon)
            dt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            item.setText(f"{filename}\nДата: {dt}")
            item.setData(Qt.UserRole, filepath)
            self.screenshots_list.addItem(item)

    def delete_selected_screenshots(self):
        selected = self.screenshots_list.selectedItems()
        if not selected:
            QMessageBox.information(self, "Нет выбора", "Выберите скриншоты для удаления")
            return
        confirm = QMessageBox.question(self, "Подтверждение", f"Удалить {len(selected)} скриншот(ов)?",
                                       QMessageBox.Yes|QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        deleted = 0
        for item in selected:
            filepath = item.data(Qt.UserRole)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    deleted += 1
            except Exception as e:
                print(e)
        QMessageBox.information(self, "Готово", f"Удалено {deleted} скриншотов")
        self.refresh_screenshots_list()

    def open_screenshot(self, item):
        filepath = item.data(Qt.UserRole)
        if os.path.exists(filepath):
            os.startfile(filepath)
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден")

    # ---------------------- Profile Screen ----------------------
    def setup_profile_screen(self):
        self.profile_screen = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40,40,40,40)
        self.profile_nick = QLabel(self.data["profile"]["nickname"])
        self.profile_nick.setFont(QFont("Arial",28,QFont.Bold))
        self.profile_nick.setStyleSheet("color:white; background-color:rgba(0,0,0,80); padding:10px; border-radius:20px;")
        layout.addWidget(self.profile_nick)

        edit_btn = QPushButton("Редактировать профиль")
        edit_btn.setStyleSheet("background-color:rgba(44,62,80,180); border-radius:15px; padding:8px;")
        edit_btn.clicked.connect(self.edit_profile)
        layout.addWidget(edit_btn)

        layout.addWidget(QLabel("Статистика по играм:"))
        self.profile_stats = QLabel()
        self.profile_stats.setWordWrap(True)
        layout.addWidget(self.profile_stats)
        layout.addWidget(QLabel("Достижения:"))
        self.profile_ach = QLabel()
        self.profile_ach.setWordWrap(True)
        layout.addWidget(self.profile_ach)
        layout.addStretch()
        self.profile_screen.setLayout(layout)
        self.refresh_profile_screen()

    def refresh_profile_screen(self):
        self.profile_nick.setText(self.data["profile"]["nickname"])
        stats = ""
        for g in self.data["games"].values():
            t = str(timedelta(seconds=g.get("total_time",0))).split('.')[0]
            stats += f"🎮 {g['name']}: {t}\n"
        self.profile_stats.setText(stats or "Нет игр")
        ach = ""
        for gid, game in self.data["games"].items():
            achs = self.data["achievements"].get(gid,{})
            if achs:
                ach += f"\n{game['name']}:\n"
                for a in achs.values():
                    status = "✅" if a["unlocked"] else "❌"
                    ach += f"  {status} {a['name']} — {a['desc']}\n"
        self.profile_ach.setText(ach or "Нет ачивок")

    def edit_profile(self):
        nick, ok = QInputDialog.getText(self, "Новый ник", "Ник:", text=self.data["profile"]["nickname"])
        if ok and nick.strip():
            self.data["profile"]["nickname"] = nick.strip()
        av, ok = QFileDialog.getOpenFileName(self, "Аватарка", "", "Images (*.png *.jpg)")
        if ok and av:
            self.data["profile"]["avatar"] = av
        bg, ok = QFileDialog.getOpenFileName(self, "Фон профиля", "", "Images (*.png *.jpg)")
        if ok and bg:
            self.data["profile"]["background"] = bg
        self.save_data()
        self.refresh_profile_screen()

    # ---------------------- Game Logic ----------------------
    def add_new_game(self):
        name, ok = QInputDialog.getText(self, "Новая игра", "Название:")
        if not ok or not name.strip(): return
        path, ok = QFileDialog.getOpenFileName(self, "Исполняемый файл", "", "Executable (*.exe)")
        if not ok or not path: return
        icon, ok = QFileDialog.getOpenFileName(self, "Иконка", "", "Images (*.png *.jpg)")
        if not ok: icon = ""
        gid = str(int(time.time()))
        self.data["games"][gid] = {"name": name, "path": path, "icon": icon, "total_time": 0}
        self.data["achievements"][gid] = {
            "ach1": {"name": "Первый запуск", "desc": "Запустить", "unlocked": False, "condition_hours": 0},
            "ach2": {"name": "1 час", "desc": "1 час", "unlocked": False, "condition_hours": 1},
            "ach3": {"name": "5 часов", "desc": "5 часов", "unlocked": False, "condition_hours": 5}
        }
        self.save_data()
        self.refresh_games_list()
        QMessageBox.information(self, "Успех", f"Игра '{name}' добавлена!")

    def launch_game(self, game_id):
        game = self.data["games"][game_id]
        if not game.get("path") or not os.path.exists(game["path"]):
            new_path, ok = QFileDialog.getOpenFileName(self, "Укажите путь", "", "Executable (*.exe)")
            if ok and new_path:
                game["path"] = new_path
                self.save_data()
            else:
                return
        try:
            proc = subprocess.Popen(game["path"], shell=True)
            watcher = GameProcessWatcher(game_id, proc)
            thread = threading.Thread(target=watcher.run, daemon=True)
            thread.start()
            self.active_processes[game_id] = (proc, thread, watcher)
            watcher.finished.connect(self.on_game_finished)
            QMessageBox.information(self, "Запуск", f"Игра '{game['name']}' запущена!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def on_game_finished(self, game_id, seconds):
        if seconds <= 0: return
        self.data["games"][game_id]["total_time"] += seconds
        self.check_achievements(game_id)
        self.save_data()
        self.refresh_games_list()
        if self.stack.currentWidget() == self.profile_screen:
            self.refresh_profile_screen()
        self.active_processes.pop(game_id, None)

    def check_achievements(self, game_id):
        total_hours = self.data["games"][game_id]["total_time"] / 3600.0
        new = []
        for ach in self.data["achievements"][game_id].values():
            if not ach["unlocked"]:
                if ach["condition_hours"] == 0 and total_hours > 0:
                    ach["unlocked"] = True
                    new.append(ach["name"])
                elif total_hours >= ach["condition_hours"] and ach["condition_hours"] > 0:
                    ach["unlocked"] = True
                    new.append(ach["name"])
        if new:
            QMessageBox.information(self, "Ачивки!", "Новые ачивки:\n" + "\n".join(new))

    def closeEvent(self, event):
        self.gamepad_running = False
        for proc,_,_ in self.active_processes.values():
            if proc.poll() is None:
                proc.terminate()
        event.accept()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        # Настройка тёмной палитры для всех диалогов
        palette = app.palette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)

        # Дополнительные стили для QMessageBox и QInputDialog
        app.setStyleSheet("""
            QMessageBox {
                background-color: #2c2c2c;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #5c5c5c;
                border-radius: 5px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #5c5c5c;
            }
            QInputDialog {
                background-color: #2c2c2c;
                color: white;
            }
            QInputDialog QLabel {
                color: white;
            }
            QInputDialog QLineEdit {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #5c5c5c;
                border-radius: 3px;
                padding: 3px;
            }
            QFileDialog {
                background-color: #2c2c2c;
                color: white;
            }
        """)

        window = PS5Launcher()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter...")
