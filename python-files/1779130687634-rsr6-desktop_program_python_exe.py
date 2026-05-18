import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QTabWidget, QLabel
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tehnični Program")
        self.setGeometry(100, 100, 900, 600)

        # Glavni tabi
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Ustvari osnovne zavihke
        self.masa_tab = QWidget()
        self.standardi_tab = QWidget()
        self.razno_tab = QWidget()

        self.tabs.addTab(self.masa_tab, "Masa")
        self.tabs.addTab(self.standardi_tab, "Standardi")
        self.tabs.addTab(self.razno_tab, "Razno")

        self.init_masa_tab()
        self.init_standardi_tab()
        self.init_razno_tab()

        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    def init_masa_tab(self):
        layout = QVBoxLayout()

        self.masa_button = QPushButton("Odpri izračun mase")
        self.masa_button.clicked.connect(self.open_masa_subtab)

        layout.addWidget(self.masa_button)
        self.masa_tab.setLayout(layout)

    def open_masa_subtab(self):
        new_tab = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tukaj bo izračun mase (še v razvoju)"))
        new_tab.setLayout(layout)

        self.tabs.addTab(new_tab, "Izračun mase")
        self.tabs.setCurrentWidget(new_tab)

    def init_standardi_tab(self):
        layout = QVBoxLayout()

        self.subtabs = QTabWidget()

        self.subtabs.addTab(QLabel("Vijaki - vsebina kasneje"), "Vijaki")
        self.subtabs.addTab(QLabel("Matice - vsebina kasneje"), "Matice")
        self.subtabs.addTab(QLabel("Podložke - vsebina kasneje"), "Podložke")
        self.subtabs.addTab(QLabel("Ostalo - vsebina kasneje"), "Ostalo")

        layout.addWidget(self.subtabs)
        self.standardi_tab.setLayout(layout)

    def init_razno_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Razno - dodatne funkcije"))
        self.razno_tab.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

# NAVODILA ZA .EXE:
# 1. Namesti PyInstaller: pip install pyinstaller
# 2. Zaženi: pyinstaller --onefile --windowed ime_datoteke.py
# 3. EXE bo v mapi dist/
