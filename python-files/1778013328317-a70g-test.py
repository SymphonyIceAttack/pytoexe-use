import sys
import string
import math
import secrets
import re
from collections import Counter
from itertools import product

import PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGroupBox, QProgressBar, QTextEdit, QFrame, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon


class PasswordAnalyzer:
    def __init__(self):
        self.common_passwords = [
            '123456', 'password', '123456789', '12345678', '12345',
            'qwerty', 'abc123', 'admin', 'welcome', 'password1',
            '1234567', '123123', '111111', 'letmein', 'monkey',
            'sunshine', 'master', 'shadow', 'superman', 'football'
        ]

        self.keyboard_patterns = [
            'qwerty', 'asdfgh', 'zxcvbn', '123456', '987654',
            'qazwsx', 'edcrfv', 'yhnujm', '!@#$%^', '1qaz2wsx'
        ]

    def analyze_password(self, password):
        """Полный анализ пароля"""
        if not password:
            return self._get_empty_result()

        analysis = {
            'password': password,
            'length': len(password),
            'entropy': self._calculate_entropy(password),
            'strength_score': 0,
            'strength_level': '',
            'feedback': [],
            'vulnerabilities': [],
            'cracking_time': self._estimate_cracking_time(password),
            'character_analysis': self._analyze_characters(password),
            'pattern_analysis': self._check_patterns(password)
        }

        self._check_vulnerabilities(analysis)
        self._calculate_strength_score(analysis)

        return analysis

    def _calculate_entropy(self, password):
        # Вычисляет энтропию пароля
        charset_size = 0

        has_lower = any(c in string.ascii_lowercase for c in password)
        has_upper = any(c in string.ascii_uppercase for c in password)
        has_digit = any(c in string.digits for c in password)
        has_special = any(c in string.punctuation for c in password)

        if has_lower: charset_size += 26
        if has_upper: charset_size += 26
        if has_digit: charset_size += 10
        if has_special: charset_size += 32

        if charset_size == 0:
            return 0

        entropy = len(password) * math.log2(charset_size)
        return round(entropy, 2)

    def _estimate_cracking_time(self, password):
        # Оценивает время взлома пароля
        entropy = self._calculate_entropy(password)
        if entropy == 0:
            return {'instant': 'мгновенно'}

        combinations = 2 ** entropy

        attack_speeds = {
            'Обычный компьютер': 1e6,
            'Игровой ПК': 1e9,
            'Ботнет': 1e12,
            'Спец. оборудование': 1e15
        }

        results = {}
        for scenario, speed in attack_speeds.items():
            seconds = combinations / (2 * speed)
            results[scenario] = self._format_time(seconds)

        return results

    def _format_time(self, seconds):
        # Форматирует время
        if seconds < 1:
            return "мгновенно"

        time_units = [
            ('лет', 31536000),
            ('месяцев', 2592000),
            ('дней', 86400),
            ('часов', 3600),
            ('минут', 60),
            ('секунд', 1)
        ]

        for unit, divisor in time_units:
            if seconds >= divisor:
                value = seconds / divisor
                if value > 1:
                    if value > 1000:
                        return f"более 1000 {unit}"
                    return f"{value:.1f} {unit}"

        return "мгновенно"

    def _analyze_characters(self, password):
        # Анализирует состав символов
        analysis = {
            'lowercase': sum(1 for c in password if c in string.ascii_lowercase),
            'uppercase': sum(1 for c in password if c in string.ascii_uppercase),
            'digits': sum(1 for c in password if c in string.digits),
            'special': sum(1 for c in password if c in string.punctuation),
            'spaces': sum(1 for c in password if c.isspace()),
        }

        analysis['unique_chars'] = len(set(password))
        analysis['diversity_ratio'] = round(analysis['unique_chars'] / len(password), 2)

        return analysis

    def _check_patterns(self, password):
        # Проверяет шаблоны
        patterns = {
            'is_common': password.lower() in [p.lower() for p in self.common_passwords],
            'is_sequential': self._is_sequential(password),
            'is_keyboard_pattern': self._is_keyboard_pattern(password),
        }

        return patterns

    def _is_sequential(self, password):
        # Проверяет последовательности
        sequences = [
            '123', '234', '345', '456', '567', '678', '789',
            'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi',
            '987', '876', '765', '654', '543', '432', '321'
        ]

        password_lower = password.lower()
        return any(seq in password_lower for seq in sequences)

    def _is_keyboard_pattern(self, password):
        # Проверяет раскладку клавиатуры
        password_lower = password.lower()
        return any(pattern in password_lower for pattern in self.keyboard_patterns)

    def _check_vulnerabilities(self, analysis):
        # Проверяет уязвимости
        vulnerabilities = []

        if analysis['length'] < 8:
            vulnerabilities.append('Слишком короткий (менее 8 символов)')

        char_types = sum([
            analysis['character_analysis']['lowercase'] > 0,
            analysis['character_analysis']['uppercase'] > 0,
            analysis['character_analysis']['digits'] > 0,
            analysis['character_analysis']['special'] > 0
        ])

        if char_types < 2:
            vulnerabilities.append('Малое разнообразие символов')

        if analysis['pattern_analysis']['is_common']:
            vulnerabilities.append('Очень распространенный пароль')

        if analysis['pattern_analysis']['is_sequential']:
            vulnerabilities.append('Содержит последовательности')

        if analysis['pattern_analysis']['is_keyboard_pattern']:
            vulnerabilities.append('Содержит шаблоны клавиатуры')

        analysis['vulnerabilities'] = vulnerabilities

    def _calculate_strength_score(self, analysis):
        # Рассчитывает оценку стойкости
        score = 0

        length_score = min(analysis['length'] * 2, 30)
        score += length_score

        char_types = sum([
            analysis['character_analysis']['lowercase'] > 0,
            analysis['character_analysis']['uppercase'] > 0,
            analysis['character_analysis']['digits'] > 0,
            analysis['character_analysis']['special'] > 0
        ])
        score += char_types * 7.5

        entropy_score = min(analysis['entropy'] / 2, 20)
        score += entropy_score

        diversity_score = analysis['character_analysis']['diversity_ratio'] * 10
        score += diversity_score

        penalty = len(analysis['vulnerabilities']) * 5
        score = max(0, score - penalty)

        analysis['strength_score'] = min(round(score), 100)

        if score >= 80:
            analysis['strength_level'] = 'Очень сильный'
        elif score >= 60:
            analysis['strength_level'] = 'Сильный'
        elif score >= 40:
            analysis['strength_level'] = 'Средний'
        elif score >= 20:
            analysis['strength_level'] = 'Слабый'
        else:
            analysis['strength_level'] = 'Очень слабый'

        self._generate_feedback(analysis)

    def _generate_feedback(self, analysis):
        # Генерирует рекомендации
        feedback = []

        if analysis['length'] < 12:
            feedback.append(f"Увеличьте длину до 12+ символов")

        char_analysis = analysis['character_analysis']
        if char_analysis['uppercase'] == 0:
            feedback.append("Добавьте заглавные буквы")
        if char_analysis['digits'] == 0:
            feedback.append("Добавьте цифры")
        if char_analysis['special'] == 0:
            feedback.append("Добавьте специальные символы")

        if char_analysis['diversity_ratio'] < 0.7:
            feedback.append("Используйте больше уникальных символов")

        for vuln in analysis['vulnerabilities']:
            feedback.append(f"Исправьте: {vuln}")

        if not feedback:
            feedback.append("Отличный пароль!")

        analysis['feedback'] = feedback

    def _get_empty_result(self):
        # Результат для пустого пароля
        return {
            'password': '',
            'length': 0,
            'entropy': 0,
            'strength_score': 0,
            'strength_level': 'Очень слабый',
            'feedback': ['Введите пароль для анализа'],
            'vulnerabilities': ['Пустой пароль'],
            'cracking_time': {'instant': 'мгновенно'},
            'character_analysis': {},
            'pattern_analysis': {}
        }

    def generate_strong_password(self, length=16):
        # Генератор надежных паролей
        charset = string.ascii_letters + string.digits + string.punctuation

        while True:
            password = ''.join(secrets.choice(charset) for _ in range(length))

            has_upper = any(c in string.ascii_uppercase for c in password)
            has_lower = any(c in string.ascii_lowercase for c in password)
            has_digit = any(c in string.digits for c in password)
            has_special = any(c in string.punctuation for c in password)

            if (has_upper and has_lower and has_digit and has_special and
                    len(set(password)) / len(password) > 0.7):
                return password


class PasswordInputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("🔒 Анализатор стойкости паролей")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 20px 0;")

        # Поле ввода пароля
        input_group = QGroupBox("Введите пароль для анализа")
        input_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        input_layout = QVBoxLayout()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Введите ваш пароль...")
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)

        # Кнопки
        button_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("📊 Анализировать")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        self.generate_btn = QPushButton("🎲 Сгенерировать")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        self.show_hide_btn = QPushButton("👁 Показать")
        self.show_hide_btn.setCheckable(True)
        self.show_hide_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)

        button_layout.addWidget(self.analyze_btn)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.show_hide_btn)

        input_layout.addWidget(self.password_input)
        input_layout.addLayout(button_layout)
        input_group.setLayout(input_layout)

        layout.addWidget(title)
        layout.addWidget(input_group)

        self.setLayout(layout)

        # Подключаем сигналы
        self.show_hide_btn.toggled.connect(self.toggle_password_visibility)
        self.password_input.returnPressed.connect(self.analyze_btn.click)

    def toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.show_hide_btn.setText("👁 Скрыть")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.show_hide_btn.setText("👁 Показать")


class AnalysisResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Группа результатов
        result_group = QGroupBox("Результаты анализа")
        result_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        result_layout = QVBoxLayout()

        # Основная информация
        self.info_label = QLabel("Введите пароль для анализа")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")

        # Прогресс бар
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setTextVisible(True)
        self.strength_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #e74c3c;
                border-radius: 3px;
            }
        """)

        # Детальная информация
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.Box)
        details_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ecf0f1;
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 10px;
            }
        """)

        details_layout = QVBoxLayout()

        self.details_label = QLabel()
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("font-size: 11px;")

        details_layout.addWidget(self.details_label)
        details_frame.setLayout(details_layout)

        result_layout.addWidget(self.info_label)
        result_layout.addWidget(self.strength_bar)
        result_layout.addWidget(details_frame)
        result_group.setLayout(result_layout)

        layout.addWidget(result_group)
        self.setLayout(layout)

    def update_results(self, analysis):
        # Обновляет результаты анализа
        # Обновляет прогресс бар
        score = analysis['strength_score']
        self.strength_bar.setValue(score)

        # Устанавливаем цвет в зависимости от оценки
        if score >= 80:
            color = "#27ae60"  # зеленый
        elif score >= 60:
            color = "#f39c12"  # оранжевый
        elif score >= 40:
            color = "#e67e22"  # темно-оранжевый
        elif score >= 20:
            color = "#e74c3c"  # красный
        else:
            color = "#c0392b"  # темно-красный

        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

        # Формируем текст информации
        info_text = f"""
        <b>Уровень стойкости:</b> {analysis['strength_level']}<br>
        <b>Длина:</b> {analysis['length']} символов<br>
        <b>Энтропия:</b> {analysis['entropy']} бит<br>
        <b>Оценка:</b> {score}/100
        """
        self.info_label.setText(info_text)

        # Формируем детальную информацию
        details_text = "<b>📊 Состав символов:</b><br>"
        chars = analysis['character_analysis']
        details_text += f"• Строчные буквы: {chars.get('lowercase', 0)}<br>"
        details_text += f"• Заглавные буквы: {chars.get('uppercase', 0)}<br>"
        details_text += f"• Цифры: {chars.get('digits', 0)}<br>"
        details_text += f"• Спец. символы: {chars.get('special', 0)}<br>"
        details_text += f"• Уникальность: {chars.get('diversity_ratio', 0) * 100:.1f}%<br><br>"

        details_text += "<b>⏰ Время взлома:</b><br>"
        for scenario, time_est in analysis['cracking_time'].items():
            details_text += f"• {scenario}: {time_est}<br>"

        if analysis['vulnerabilities']:
            details_text += "<br><b>⚠ Уязвимости:</b><br>"
            for vuln in analysis['vulnerabilities']:
                details_text += f"• {vuln}<br>"

        if analysis['feedback']:
            details_text += "<br><b>💡 Рекомендации:</b><br>"
            for advice in analysis['feedback']:
                details_text += f"• {advice}<br>"

        self.details_label.setText(details_text)


class PasswordAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.analyzer = PasswordAnalyzer()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("🔒 Анализатор стойкости паролей")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(700, 500)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 30)

        # Виджет ввода
        self.input_widget = PasswordInputWidget()

        # Виджет результатов
        self.result_widget = AnalysisResultWidget()

        main_layout.addWidget(self.input_widget)
        main_layout.addWidget(self.result_widget)

        central_widget.setLayout(main_layout)

        # Подключаем сигналы
        self.input_widget.analyze_btn.clicked.connect(self.analyze_password)
        self.input_widget.generate_btn.clicked.connect(self.generate_password)

        # Устанавливаем стиль приложения
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

    def analyze_password(self):
        # Анализирует введенный пароль
        password = self.input_widget.password_input.text()
        analysis = self.analyzer.analyze_password(password)
        self.result_widget.update_results(analysis)

    def generate_password(self):
        # Генерирует и вставляет надежный пароль
        password = self.analyzer.generate_strong_password()
        self.input_widget.password_input.setText(password)
        self.input_widget.password_input.setEchoMode(QLineEdit.Normal)
        self.input_widget.show_hide_btn.setChecked(True)
        self.input_widget.show_hide_btn.setText("👁 Скрыть")

        # Анализируем сгенерированный пароль
        QTimer.singleShot(100, self.analyze_password)


def main():
    app = QApplication(sys.argv)

    # Устанавливаем стиль приложения
    app.setStyle('Fusion')

    window = PasswordAnalyzerApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()