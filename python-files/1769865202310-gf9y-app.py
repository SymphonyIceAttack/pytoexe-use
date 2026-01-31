import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Plus Minus 5 Calculator")
        self.setGeometry(100, 100, 280, 250)
        
        # Force dark background always
        self.setStyleSheet("background-color: #2b2b2b;")
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 10, 20, 20)  # left, top, right, bottom
        
        # Label
        label = QLabel("Enter a number:")
        label.setFont(QFont("Helvetica", 14, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white;")
        layout.addWidget(label)
        
        # Input field
        self.entry = QLineEdit()
        self.entry.setFont(QFont("Helvetica", 16))
        self.entry.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #4a90e2;
                border-radius: 5px;
                background-color: white;
                color: black;
            }
        """)
        self.entry.setAlignment(Qt.AlignCenter)
        self.entry.returnPressed.connect(self.calculate)  # Enter key triggers calculation
        layout.addWidget(self.entry)
        
        # Buttons layout (2fr Calculate, 1fr Clear)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Calculate button
        calc_btn = QPushButton("Calculate")
        calc_btn.setFont(QFont("Helvetica", 14, QFont.Bold))
        calc_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        calc_btn.clicked.connect(self.calculate)
        buttons_layout.addWidget(calc_btn, 2)  # 2fr
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setFont(QFont("Helvetica", 14, QFont.Bold))
        clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.clear_fields)
        buttons_layout.addWidget(clear_btn, 1)  # 1fr
        
        layout.addLayout(buttons_layout)
        
        # Result label
        self.result_label = QLabel("")
        self.result_label.setFont(QFont("Helvetica", 18, QFont.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(self.result_label)
        
        self.setLayout(layout)
        self.entry.setFocus()
    
    def keyPressEvent(self, event):
        # Esc key clears the input field
        if event.key() == Qt.Key_Escape:
            self.entry.clear()
            self.result_label.setText("")
        else:
            super().keyPressEvent(event)
    
    def calculate(self):
        try:
            num = float(self.entry.text())
            plus = num + 5
            minus = num - 5
            self.result_label.setText(f"+5 = {plus}     -5 = {minus}")
        except ValueError:
            QMessageBox.critical(self, "Invalid input", "Please enter a number")
    
    def clear_fields(self):
        self.entry.clear()
        self.result_label.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    calculator = Calculator()
    calculator.show()
    sys.exit(app.exec_())
