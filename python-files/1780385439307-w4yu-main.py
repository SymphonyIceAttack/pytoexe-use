import sys
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QLineEdit,
                             QPushButton, QVBoxLayout, QWidget, QFileDialog,
                             QLabel, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QTextCharFormat

class TypingTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажер скорости печати")
        self.setGeometry(100, 100, 800, 600)

        # --- Инициализация переменных ---
        self.original_text = ""
        self.current_index = 0
        self.start_time = None
        self.total_errors = 0

        # --- Создание виджетов ---
        self.text_source = QTextEdit(self)
        self.text_source.setReadOnly(True)

        self.text_input = QLineEdit(self)
        self.text_input.setReadOnly(True) # Запрещаем ручное редактирование
        self.text_input.setFocusPolicy(Qt.StrongFocus) # Позволяем виджету получать фокус

        self.btn_load = QPushButton("Загрузить текст (.txt)", self)
        self.btn_load.clicked.connect(self.load_text_from_file)

        self.btn_reset = QPushButton("Начать заново", self)
        self.btn_reset.clicked.connect(self.reset_test)

        # Счетчики и таймер
        self.label_timer = QLabel("Время: 0.00 сек", self)
        self.label_words = QLabel("Слов: 0", self)
        self.label_errors = QLabel("Ошибок: 0", self)

        # --- Настройка компоновки ---
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.btn_load)
        controls_layout.addWidget(self.btn_reset)

        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self.label_timer)
        stats_layout.addWidget(self.label_words)
        stats_layout.addWidget(self.label_errors)

        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("Текст для набора:"))
        main_layout.addWidget(self.text_source)

        main_layout.addWidget(QLabel("Ваш набор:"))
        main_layout.addWidget(self.text_input)
        
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(stats_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def keyPressEvent(self, event):
        if not self.original_text or self.current_index >= len(self.original_text):
            return

        key = event.key()

         # Игнорируем Backspace и другие неалфавитные клавиши навигации/редактирования
         if key in (Qt.Key_Backspace, Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down,
                    Qt.Key_Home, Qt.Key_End, Qt.Key_Delete):
             event.accept()
             return

         # Обрабатываем только печатные символы и Enter
         if key in (Qt.Key_Return, Qt.Key_Enter):
             char_to_check = '\n'
             user_char = '\n'
         elif 32 <= key <= 126: # Диапазон ASCII для печатных символов
             char_to_check = self.original_text[self.current_index]
             user_char = event.text()
         else:
             return

         if user_char == char_to_check:
             self.text_input.setText(self.text_input.text() + user_char)
             self.highlight_char(self.current_index, Qt.green)
             self.current_index += 1

             if not self.start_time:
                 self.start_time = time.time()

             self.update_stats()

             if self.current_index == len(self.original_text):
                 self.test_finished()
         else:
             # Неверный ввод: подсвечиваем ошибку и считаем ее
             self.total_errors += 1
             self.highlight_char(self.current_index, Qt.red)
             self.update_stats() # Обновляем счетчик ошибок на экране

         event.accept()

    def highlight_char(self, index, color):
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(color))
        
        cursor = self.text_source.textCursor()
        
        cursor.setPosition(index)
        cursor.movePosition(cursor.Right, cursor.KeepAnchor) # Выделяем один символ справа

        cursor.mergeCharFormat(fmt)

    def clear_formatting(self):
        """Сбрасывает все форматирование в исходном тексте."""
       fmt = QTextCharFormat()
       fmt.clearBackground()
       
       cursor = self.text_source.textCursor()
       cursor.select(cursor.Document) # Выделяем весь документ
       cursor.mergeCharFormat(fmt)
       cursor.clearSelection()
       
    def load_text_from_file(self):
         options = QFileDialog.Options()
         file_name, _ = QFileDialog.getOpenFileName(
             self, "Выбрать текстовый файл", "", "Text Files (*.txt)", options=options)
         
         if file_name:
             try:
                 with open(file_name, 'r', encoding='utf-8') as f:
                     text = f.read().replace('\r\n', '\n')
                     self.original_text = text
                     self.text_source.setPlainText(self.original_text)
                     self.reset_test()
             except Exception as e:
                 QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл:\n{str(e)}")

    def reset_test(self):
         self.current_index = 0
         self.total_errors = 0
         self.start_time = None

         self.clear_formatting() # Сбрасываем подсветку

         current_text = self.text_source.toPlainText()
         self.text_source.setPlainText(current_text) 
         
         self.text_input.clear()
         self.update_stats()
         self.text_input.setFocus() # Возвращаем фокус на поле ввода

    def update_stats(self):
         elapsed_time = time.time() - self.start_time if self.start_time else 0

         # Корректный подсчет слов по любым пробельным символам
         word_count = len(self.text_input.text().split())
         
         self.label_timer.setText(f"Время: {elapsed_time:.2f} сек")
         self.label_words.setText(f"Слов: {word_count}")
         self.label_errors.setText(f"Ошибок: {self.total_errors}")

    def test_finished(self):
         elapsed_time = time.time() - self.start_time if self.start_time else 0

         total_chars = len([c for c in self.original_text if c != '\n'])
         chars_per_min = (total_chars / elapsed_time * 60) if elapsed_time > 0 else 0

         result_message = (f"Тест завершен!\n"
                          f"Время: {elapsed_time:.2f} сек\n"
                          f"Скорость: {chars_per_min:.1f} знаков/мин\n"
                          f"Ошибок: {self.totalerrors}")
         
         print(result_message) # Выводим результат в консоль

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TypingTrainer()
    window.show()
    sys.exit(app.exec_())