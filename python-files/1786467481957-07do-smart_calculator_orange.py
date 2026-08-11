import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class SmartCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.after_equals = False  # только что был результат (нажали =)
        self.base_font_size = 20   # базовый размер шрифта
        self.min_font_size = 12    # минимальный размер
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Оранжевый калькулятор")
        self.resize(320, 450)

        # Поле ввода
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFont(QFont("Arial", self.base_font_size))
        self.display.setMaxLength(24)  # лимит 24 символа
        self.display.textChanged.connect(self.adjust_font_size)
        self.display.setStyleSheet("""
            QLineEdit {
                background-color: #FFF8E1;
                color: #D35400;
                border: 1px solid #FFA000;
                padding: 10px;
                border-radius: 12px;
            }
        """)

        # Сетка кнопок
        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(20, 20, 20, 20)

        buttons = [
            ('C', 0, 0), ('/', 0, 1), ('*', 0, 2), ('-', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('+', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('=', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('(', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('←', 4, 2), (')', 4, 3)
        ]

        self.buttons = {}

        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 16, QFont.Bold))

            # Цвета кнопок
            if text in ['C', '←']:
                bg_normal, bg_hover, bg_pressed = "#E67E22", "#D35400", "#A04000"
            elif text in ['+', '-', '*', '/', '=', '(', ')']:
                bg_normal, bg_hover, bg_pressed = "#F39C12", "#D4AC0D", "#B98905"
            else:
                bg_normal, bg_hover, bg_pressed = "#FFC107", "#FFB300", "#FF9500"

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_normal};
                    color: #333;
                    border: none;
                    border-radius: 36px;
                    padding: 15px;
                    min-width: 64px;
                    min-height: 64px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {bg_hover}; }}
                QPushButton:pressed {{ background-color: {bg_pressed}; }}
            """)

            btn.clicked.connect(lambda checked, t=text: self.on_click(t))
            self.buttons[text] = btn
            grid.addWidget(btn, row, col)

        layout = QVBoxLayout()
        layout.addWidget(self.display)
        layout.addLayout(grid)
        self.setLayout(layout)

    def adjust_font_size(self):
        """Уменьшает шрифт, если символов много, чтобы всё помещалось."""
        text_length = len(self.display.text())
        if text_length <= 12:
            font_size = self.base_font_size
        elif text_length <= 18:
            font_size = max(self.min_font_size, self.base_font_size - 4)
        else:
            font_size = max(self.min_font_size, self.base_font_size - 8)

        font = self.display.font()
        font.setPointSize(font_size)
        self.display.setFont(font)

    @staticmethod
    def is_operator(char):
        return char in '+-*/()'

    def on_click(self, text):
        current = self.display.text()

        if text == 'C':
            self.display.setText('')
            self.after_equals = False
            return

        if text == '←':
            self.display.setText(current[:-1])
            self.after_equals = False
            return

        if text == '=':
            try:
                result = str(eval(current))
                if len(result) > 24:
                    result = result[:24]
                self.display.setText(result)
                self.after_equals = True
            except Exception:
                self.display.setText('Ошибка')
                self.after_equals = False
            return

        # Логика после «=»
        if self.after_equals:
            if text.isdigit() or text == '.':
                # Цифра/точка после результата — сброс и новое число
                self.display.setText(text)
                self.after_equals = False
                return
            else:
                # Знак после результата — продолжаем от результата
                self.display.setText(current + text)
                self.after_equals = False
                return

        # Обычная логика ввода
        # Запрет двух операторов подряд
        if self.is_operator(text):
            if current and self.is_operator(current[-1]):
                # Если последний символ — тоже оператор, не добавляем новый
                return

        new_text = current + text

        # Проверка длины (до 24)
        if len(new_text) <= 24:
            self.display.setText(new_text)
        # Иначе просто ничего не делаем (лимит превышен)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#FFF3E0"))
    app.setPalette(palette)

    calc = SmartCalculator()
    calc.show()
    sys.exit(app.exec_())
