#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Приложение «Копилка на компьютер».
Помогает накопить 50 000 рублей.
Сохраняет прогресс между запусками через QSettings.
Запуск:
    python3 savings_app.py
Требуется PyQt5.
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QProgressBar, QLineEdit, QPushButton,
                             QMessageBox)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont


TARGET_AMOUNT = 50_000  # Целевая сумма в рублях


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Копилка на компьютер")
        # Загрузка сохранённой суммы
        self.settings = QSettings("MySoft", "SavingsApp")
        self.current_amount = self.settings.value("saved_amount", 0, type=int)

        # Инициализация интерфейса
        self.init_ui()

        # Первичное обновление интерфейса
        self.update_ui()

    def init_ui(self):
        """Создание и размещение всех виджетов."""
        # Центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        central_widget.setLayout(layout)

        # Крупный шрифт для основных цифр
        big_font = QFont("Arial", 28, QFont.Bold)
        medium_font = QFont("Arial", 16)

        # ----- Виджеты -----
        # Целевая сумма
        self.label_goal = QLabel(f"Цель: {TARGET_AMOUNT:,} руб.")
        self.label_goal.setFont(medium_font)
        self.label_goal.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_goal)

        # Текущая сумма
        self.label_current = QLabel()
        self.label_current.setFont(big_font)
        self.label_current.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_current)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setFont(medium_font)
        layout.addWidget(self.progress_bar)

        # Осталось собрать
        self.label_remaining = QLabel()
        self.label_remaining.setFont(medium_font)
        self.label_remaining.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_remaining)

        # Поле ввода
        self.input_amount = QLineEdit()
        self.input_amount.setPlaceholderText("Введите сумму пополнения (руб.)")
        self.input_amount.setFont(medium_font)
        self.input_amount.setAlignment(Qt.AlignCenter)
        self.input_amount.setFixedWidth(300)
        layout.addWidget(self.input_amount, alignment=Qt.AlignCenter)

        # Кнопка «Добавить»
        self.button_add = QPushButton("Добавить")
        self.button_add.setFont(medium_font)
        self.button_add.clicked.connect(self.add_money)
        self.button_add.setFixedWidth(200)
        layout.addWidget(self.button_add, alignment=Qt.AlignCenter)

        # Кнопка «Сбросить»
        self.button_reset = QPushButton("Сбросить")
        self.button_reset.setFont(medium_font)
        self.button_reset.clicked.connect(self.reset_savings)
        self.button_reset.setFixedWidth(200)
        layout.addWidget(self.button_reset, alignment=Qt.AlignCenter)

        # Кнопка «Выход» (опционально)
        self.button_exit = QPushButton("Выход")
        self.button_exit.setFont(medium_font)
        self.button_exit.clicked.connect(self.close)
        self.button_exit.setFixedWidth(200)
        layout.addWidget(self.button_exit, alignment=Qt.AlignCenter)

        # Растяжки для вертикального центрирования
        layout.insertStretch(0, 1)
        layout.addStretch(1)

    def update_ui(self):
        """Обновляет все отображаемые значения и цвета прогресс-бара."""
        # Процент выполнения
        if TARGET_AMOUNT == 0:
            percent = 0
        else:
            percent = min(int(self.current_amount / TARGET_AMOUNT * 100), 100)

        # Обновление надписей
        self.label_current.setText(f"Накоплено: {self.current_amount:,} руб.")
        remaining = max(TARGET_AMOUNT - self.current_amount, 0)
        self.label_remaining.setText(f"Осталось собрать: {remaining:,} руб.")

        # Прогресс-бар
        self.progress_bar.setValue(percent)
        self.update_progress_bar_color(percent)

        # Проверка достижения цели
        if self.current_amount >= TARGET_AMOUNT:
            self.button_add.setEnabled(False)
            self.input_amount.setEnabled(False)
            # Покажем сообщение, если ещё не показывали (защита от спама)
            if self.current_amount == TARGET_AMOUNT or self.current_amount > TARGET_AMOUNT:
                self.show_congratulations()
        else:
            self.button_add.setEnabled(True)
            self.input_amount.setEnabled(True)

    def update_progress_bar_color(self, percent):
        """Меняет цвет прогресс-бара в зависимости от процента."""
        if percent >= 100:
            color = "#4CAF50"   # зелёный
        elif percent >= 50:
            color = "#FF9800"   # оранжевый
        else:
            color = "#F44336"   # красный

        style = f"""
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 5px;
        }}
        """
        self.progress_bar.setStyleSheet(style)

    def add_money(self):
        """Обработчик нажатия кнопки «Добавить»."""
        text = self.input_amount.text().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите сумму для пополнения.")
            return

        try:
            amount = int(text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите целое число (рубли).")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Ошибка", "Сумма должна быть положительным числом.")
            return

        # Проверяем, не превышает ли пополнение остаток до цели
        remaining = TARGET_AMOUNT - self.current_amount
        if amount > remaining:
            # Добавляем только недостающую часть
            amount = remaining
            self.current_amount += amount
            self.save_data()
            self.update_ui()
            QMessageBox.information(
                self,
                "Поздравляем!",
                "Вы накопили на компьютер! Была добавлена недостающая сумма."
            )
            return

        # Обычное пополнение
        self.current_amount += amount
        self.save_data()
        self.update_ui()

        # Если после пополнения цель достигнута, покажем сообщение
        if self.current_amount >= TARGET_AMOUNT:
            self.show_congratulations()

        self.input_amount.clear()

    def reset_savings(self):
        """Сброс накоплений с подтверждением."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы действительно хотите обнулить все накопления?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_amount = 0
            self.save_data()
            self.update_ui()
            self.input_amount.clear()
            self.button_add.setEnabled(True)
            self.input_amount.setEnabled(True)

    def show_congratulations(self):
        """Показывает поздравительное сообщение."""
        QMessageBox.information(
            self,
            "Поздравляем!",
            "Вы накопили на компьютер! Отличная работа!"
        )

    def save_data(self):
        """Сохраняет текущую сумму в QSettings."""
        self.settings.setValue("saved_amount", self.current_amount)

    def closeEvent(self, event):
        """Сохранение перед выходом (на всякий случай)."""
        self.save_data()
        event.accept()


def main():
    """Точка входа в приложение."""
    app = QApplication(sys.argv)

    # Тёмная тема через глобальную таблицу стилей
    dark_style = """
    QWidget {
        background-color: #1e1e1e;
        color: #e0e0e0;
        font-family: "Arial";
    }
    QLabel {
        color: #ffffff;
        background: transparent;
    }
    QProgressBar {
        border: 2px solid #555555;
        border-radius: 8px;
        text-align: center;
        background-color: #2d2d2d;
        color: #ffffff;
    }
    QProgressBar::chunk {
        border-radius: 5px;
    }
    QLineEdit {
        background-color: #2d2d2d;
        border: 2px solid #555555;
        border-radius: 6px;
        padding: 6px;
        color: #ffffff;
    }
    QPushButton {
        background-color: #3c3c3c;
        border: 2px solid #5a5a5a;
        border-radius: 8px;
        padding: 8px 16px;
        color: #ffffff;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #4a4a4a;
    }
    QPushButton:pressed {
        background-color: #2a2a2a;
    }
    QPushButton:disabled {
        background-color: #2a2a2a;
        color: #888888;
        border-color: #444444;
    }
    """
    app.setStyleSheet(dark_style)

    window = MainWindow()
    window.showFullScreen()  # Полноэкранный режим без рамок
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()