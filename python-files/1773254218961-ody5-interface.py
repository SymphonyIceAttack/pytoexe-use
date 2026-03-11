import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QTimer

# ---------- Кастомная кнопка-триггер ----------
class DropdownButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(58)
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1.5px solid #d4d4e2;
                border-radius: 10px;
                text-align: left;
                padding: 0 20px;
                font-size: 18px;
                font-weight: 450;
                color: #1a1a24;
                margin: 0px;
                box-sizing: border-box;
            }
            QPushButton:hover {
                background-color: #fafaff;
                border-color: #a0a0ba;
            }
            QPushButton:pressed {
                background-color: #eaeaff;
                border-color: #e11d48;
            }
        """)
        self.arrow = QLabel("▼", self)
        self.arrow.setStyleSheet("color: #8a8aa8; font-size: 16px; border: none; margin: 0px;")
        self.arrow.setGeometry(self.width() - 34, (self.height() - 16) // 2, 16, 16)

    def resizeEvent(self, event):
        self.arrow.setGeometry(self.width() - 34, (self.height() - 16) // 2, 16, 16)
        super().resizeEvent(event)

# ---------- Выпадающий список без зазоров ----------
class DropdownList(QFrame):
    def __init__(self, items, parent=None, on_selected=None):
        super().__init__(parent)
        self.on_selected = on_selected
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1.5px solid #d4d4e2;
                border-radius: 12px;
                padding: 6px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)   # внутренние отступы layout = 0
        layout.setSpacing(0)                    # кнопки вплотную

        self.items = items
        self.item_widgets = []
        for text in items:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(48)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1.5px solid transparent;
                    border-radius: 8px;
                    text-align: left;
                    padding: 0 14px;
                    font-size: 16px;
                    color: #1a1a24;
                    margin: 0px;
                    box-sizing: border-box;
                }
                QPushButton:hover {
                    background-color: #f2f2ff;
                    border-color: #a0a0c0;
                }
                QPushButton:pressed {
                    background-color: #eaeaff;
                    border-color: #e11d48;
                }
            """)
            btn.clicked.connect(self.on_item_clicked)
            layout.addWidget(btn)
            self.item_widgets.append(btn)

        self.selected_item = None

    def highlight_selected(self, index):
        for i, btn in enumerate(self.item_widgets):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f0ff;
                        border: 1.5px solid #e11d48;
                        border-radius: 8px;
                        text-align: left;
                        padding: 0 14px;
                        font-size: 16px;
                        color: #1a1a24;
                        margin: 0px;
                        box-sizing: border-box;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 1.5px solid transparent;
                        border-radius: 8px;
                        text-align: left;
                        padding: 0 14px;
                        font-size: 16px;
                        color: #1a1a24;
                        margin: 0px;
                        box-sizing: border-box;
                    }
                """)

    def on_item_clicked(self):
        btn = self.sender()
        index = self.item_widgets.index(btn)
        self.highlight_selected(index)
        self.selected_item = btn.text()
        if self.on_selected:
            self.on_selected(btn.text())
        self.close()

# ---------- Главное окно ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StaticBullet")
        self.setFixedSize(360, 700)
        self.setStyleSheet("QMainWindow { background-color: #f5f5f7; }")

        central_widget = QWidget()
        central_widget.setStyleSheet("""
            background-color: white;
            border-radius: 28px;
        """)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 40, 24, 32)
        main_layout.setSpacing(40)

        # ----- Красный контейнер с чёрной рамкой -----
        title_container = QFrame()
        title_container.setFixedHeight(70)
        title_container.setStyleSheet("""
            background-color: #e11d48;
            border: 2px solid black;
            border-radius: 10px;
        """)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(12, 10, 12, 10)

        title_label = QLabel("StaticBullet")
        title_label.setStyleSheet("font-size: 42px; font-weight: 500; color: black; border: none; margin: 0px;")
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_container)

        # ----- Кастомный выпадающий список -----
        self.dropdown_trigger = DropdownButton("Minecraft")
        self.dropdown_trigger.clicked.connect(self.toggle_dropdown)
        main_layout.addWidget(self.dropdown_trigger)

        self.dropdown = None

        # ----- Кнопки -----
        self.disable_btn = QPushButton("Disable WD")
        self.disable_btn.setCursor(Qt.PointingHandCursor)
        self.disable_btn.setFixedHeight(52)
        self.disable_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1.5px solid #c2c2d6;
                border-radius: 8px;
                font-size: 18px;
                font-weight: 500;
                color: black;
                margin: 0px;
                box-sizing: border-box;
            }
            QPushButton:hover {
                background-color: #f2f2ff;
                border-color: #a0a0c0;
            }
            QPushButton:pressed {
                background-color: #eaeaff;
                border-color: #e11d48;
            }
        """)
        self.disable_btn.clicked.connect(self.toggle_wd)

        self.inject_btn = QPushButton("Inject")
        self.inject_btn.setCursor(Qt.PointingHandCursor)
        self.inject_btn.setFixedHeight(52)
        self.inject_btn.setStyleSheet(self.disable_btn.styleSheet())
        self.inject_btn.clicked.connect(self.inject_game)

        main_layout.addWidget(self.disable_btn)
        main_layout.addWidget(self.inject_btn)

        # ----- Индикаторы -----
        indicators_widget = QWidget()
        indicators_layout = QVBoxLayout(indicators_widget)
        indicators_layout.setContentsMargins(0, 0, 0, 0)
        indicators_layout.setSpacing(8)

        # WD Status
        wd_row = QHBoxLayout()
        wd_row.setAlignment(Qt.AlignCenter)
        wd_label = QLabel("WD Status:")
        wd_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #6a6a86; text-transform: uppercase; border: none; margin: 0px;")
        self.wd_status = QLabel("Disabled")
        self.wd_status.setStyleSheet("""
            font-size: 14px; font-weight: 600; color: #2c7a5a;
            background-color: #e0f5ec; padding: 4px 8px; border-radius: 6px; border: none; margin: 0px;
        """)
        wd_row.addWidget(wd_label)
        wd_row.addWidget(self.wd_status)

        # Injected
        inj_row = QHBoxLayout()
        inj_row.setAlignment(Qt.AlignCenter)
        inj_label = QLabel("Injected:")
        inj_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #6a6a86; text-transform: uppercase; border: none; margin: 0px;")
        self.inj_status = QLabel("Minecraft")
        self.inj_status.setStyleSheet("font-size: 14px; font-weight: 500; color: #1a1a2a; padding: 4px 8px; border-radius: 6px; border: none; margin: 0px;")
        inj_row.addWidget(inj_label)
        inj_row.addWidget(self.inj_status)

        indicators_layout.addLayout(wd_row)
        indicators_layout.addLayout(inj_row)

        main_layout.addWidget(indicators_widget)
        main_layout.addStretch()

        # Состояния
        self.wd_disabled = True
        self.current_game = "Minecraft"
        self.injected_game = "Minecraft"

    def toggle_dropdown(self):
        if self.dropdown is None or not self.dropdown.isVisible():
            self.show_dropdown()
        else:
            self.dropdown.close()

    def show_dropdown(self):
        items = [
            "Counter-Strike 2", "Valorant", "Fortnite", "Apex Legends",
            "Overwatch 2", "Rust", "Minecraft", "GTA V Online"
        ]
        self.dropdown = DropdownList(items, self, on_selected=self.on_game_selected)
        self.dropdown.selected_item = self.current_game

        trigger_rect = self.dropdown_trigger.rect()
        global_pos = self.dropdown_trigger.mapToGlobal(trigger_rect.bottomLeft())
        global_pos.setY(global_pos.y() - 6)
        self.dropdown.move(global_pos)
        self.dropdown.setFixedWidth(self.dropdown_trigger.width())
        self.dropdown.show()

        if self.current_game in items:
            idx = items.index(self.current_game)
            self.dropdown.highlight_selected(idx)

        self.dropdown_trigger.setStyleSheet("""
            QPushButton {
                background-color: #eaeaff;
                border: 1.5px solid #e11d48;
                border-radius: 10px;
                text-align: left;
                padding: 0 20px;
                font-size: 18px;
                font-weight: 450;
                color: #1a1a24;
                margin: 0px;
                box-sizing: border-box;
            }
            QPushButton:hover {
                background-color: #f2f2ff;
                border-color: #a0a0c0;
            }
            QPushButton:pressed {
                background-color: #eaeaff;
                border-color: #e11d48;
            }
        """)

        self.dropdown.installEventFilter(self)

    def on_game_selected(self, game_name):
        self.current_game = game_name
        self.dropdown_trigger.setText(game_name)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self.dropdown and event.type() == QEvent.Type.Close:
            self.dropdown_trigger.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1.5px solid #d4d4e2;
                    border-radius: 10px;
                    text-align: left;
                    padding: 0 20px;
                    font-size: 18px;
                    font-weight: 450;
                    color: #1a1a24;
                    margin: 0px;
                    box-sizing: border-box;
                }
                QPushButton:hover {
                    background-color: #fafaff;
                    border-color: #a0a0ba;
                }
                QPushButton:pressed {
                    background-color: #eaeaff;
                    border-color: #e11d48;
                }
            """)
        return super().eventFilter(obj, event)

    def toggle_wd(self):
        self.wd_disabled = not self.wd_disabled
        if self.wd_disabled:
            self.wd_status.setText("Disabled")
            self.wd_status.setStyleSheet("font-size: 14px; font-weight: 600; color: #2c7a5a; background-color: #e0f5ec; padding: 4px 8px; border-radius: 6px; border: none; margin: 0px;")
        else:
            self.wd_status.setText("Enabled")
            self.wd_status.setStyleSheet("font-size: 14px; font-weight: 600; color: #e11d48; background-color: #ffe8ec; padding: 4px 8px; border-radius: 6px; border: none; margin: 0px;")
        self.animate_button(self.disable_btn)

    def inject_game(self):
        self.injected_game = self.current_game
        self.inj_status.setText(self.injected_game)
        self.inj_status.setStyleSheet("font-size: 14px; font-weight: 500; color: #e11d48; background-color: #eaeaff; padding: 4px 8px; border-radius: 6px; border: none; margin: 0px;")
        QTimer.singleShot(200, self.reset_inj_style)
        self.animate_button(self.inject_btn)

    def reset_inj_style(self):
        self.inj_status.setStyleSheet("font-size: 14px; font-weight: 500; color: #1a1a2a; padding: 4px 8px; border-radius: 6px; border: none; margin: 0px;")

    def animate_button(self, btn):
        original = btn.styleSheet()
        temp = original.replace("background-color: white;", "background-color: #f0f0fc;")
        btn.setStyleSheet(temp)
        QTimer.singleShot(100, lambda: btn.setStyleSheet(original))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    screen = app.primaryScreen().geometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)
    window.show()
    sys.exit(app.exec())