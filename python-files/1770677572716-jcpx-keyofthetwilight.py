# KeyOfTheTwilight.py
# Python 3 + PyQt5 prototype
# SAO-style UI for AD&D 2e toolkit

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QVBoxLayout,
                             QLabel, QGridLayout, QPushButton, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHBoxLayout, QTextEdit)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

class KeyOfTheTwilight(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Key of the Twilight")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #0a0a0a;")  # Dark background

        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 0; }
            QTabBar::tab { background: #111111; color: #00ffff; font: bold 14px; padding: 10px; }
            QTabBar::tab:selected { background: #222222; color: #ff0000; }
        """)
        layout.addWidget(self.tabs)

        # Tabs
        self.character_tab()
        self.inventory_tab()
        self.monsters_tab()

        self.setLayout(layout)

    # ---------------- Character Tab ----------------
    def character_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Character Info")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #00ffff;")
        layout.addWidget(title)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)

        # Example stats
        stats = {"Name": "Ember", "Level": "1", "HP": "12", "AC": "12", "Attack Bonus": "+1"}
        row = 0
        for key, value in stats.items():
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 14))
            label.setStyleSheet("color: #00ffff;")
            val = QLabel(value)
            val.setFont(QFont("Arial", 14, QFont.Bold))
            val.setStyleSheet("color: #ff0000;" if key in ["AC", "Attack Bonus"] else "color: #ffffff;")
            stats_layout.addWidget(label, row, 0)
            stats_layout.addWidget(val, row, 1)
            row += 1

        layout.addLayout(stats_layout)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Character")

    # ---------------- Inventory Tab ----------------
    def inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Inventory")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #00ffff;")
        layout.addWidget(title)

        # Weapon slots
        weapon_layout = QHBoxLayout()
        for i in range(4):
            slot = QPushButton(f"Slot {i+1}")
            slot.setStyleSheet("""
                QPushButton {
                    background-color: #111111; color: #ff0000; font: bold 14px;
                    border: 2px solid #00ffff; border-radius: 5px; padding: 10px;
                }
                QPushButton:hover { background-color: #222222; }
            """)
            weapon_layout.addWidget(slot)
        layout.addLayout(weapon_layout)

        # Item table (50 per page)
        self.item_table = QTableWidget()
        self.item_table.setRowCount(50)
        self.item_table.setColumnCount(4)
        self.item_table.setHorizontalHeaderLabels(["Name", "Qty", "Weight", "Notes"])
        self.item_table.setStyleSheet("""
            QHeaderView::section { background-color: #111111; color: #00ffff; font: bold 12px; }
            QTableWidget { background-color: #111111; color: #ffffff; gridline-color: #00ffff; }
        """)
        layout.addWidget(self.item_table)

        # Weight calculator
        self.weight_label = QLabel("Total Weight: 0")
        self.weight_label.setFont(QFont("Arial", 14))
        self.weight_label.setStyleSheet("color: #00ffff;")
        layout.addWidget(self.weight_label)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Inventory")

    # ---------------- Monsters Tab ----------------
    def monsters_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Monsters Repository")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #00ffff;")
        layout.addWidget(title)

        # Wiki scan input
        scan_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste wiki page URL here")
        self.url_input.setStyleSheet("background-color: #111111; color: #ffffff;")
        scan_button = QPushButton("Scan Page")
        scan_button.setStyleSheet("""
            QPushButton { background-color: #111111; color: #00ffff; font: bold 14px; border: 2px solid #00ffff; padding: 5px; }
            QPushButton:hover { background-color: #222222; }
        """)
        scan_layout.addWidget(self.url_input)
        scan_layout.addWidget(scan_button)
        layout.addLayout(scan_layout)

        # Preview / output box
        self.preview_box = QTextEdit()
        self.preview_box.setStyleSheet("background-color: #111111; color: #ffffff;")
        self.preview_box.setPlaceholderText("Parsed monster info will appear here...")
        layout.addWidget(self.preview_box)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Monsters")

# ---------------- Run App ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KeyOfTheTwilight()
    window.show()
    sys.exit(app.exec_())
