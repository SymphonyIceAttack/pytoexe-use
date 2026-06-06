mport tkinter as tk
import time
import random

class TypingTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")
        
        # Предварительно подготовленные тексты для генерации
        self.sample_texts = [
            "Быстрая корова перепрыгнула через ленивого кота.",
            "Сегодня солнечная погода и птички поют в саду.",
            "Пожалуйста, печатайте как можно быстрее и точнее.",
            "Тестирование скорости печати — это интересно и полезно.",
            "Создавайте хорошие привычки для улучшения навыков."
        ]
        
        # Исходный текст по умолчанию
        self.default_text = ("Это пример текста для теста скорости печати. "
                            "Пожалуйста, печатайте как можно быстрее и точнее.")
        self.target_text = self.default_text
        self.words = self.target_text.split()
        self.word_count = len(self.words)
        self.current_word_index = 0
        self.start_time = None
        self.timer_running = False
        
        # Ввод собственного текста
        self.custom_text_label = tk.Label(root, text="Введите свой текст для теста:", font=("Helvetica", 12))
        self.custom_text_label.pack(pady=5)
        
        self.custom_text_entry = tk.Text(root, height=3, width=80, font=("Helvetica", 12))
        self.custom_text_entry.pack()

        self.set_text_button = tk.Button(root, text="Установить текст", command=self.set_custom_text)
        self.set_text_button.pack(pady=5)
        
        # Кнопка генерации случайного текста
        self.generate_text_button = tk.Button(root, text="Генерировать случайный текст", command=self.generate_random_text)
        self.generate_text_button.pack(pady=5)
        
        # Текст для печати
        self.label_target = tk.Label(root, text=self.target_text, wraplength=600, font=("Helvetica", 14))
        self.label_target.pack(pady=10)
        
        # Поле для ввода
        self.text_entry = tk.Text(root, height=10, width=80, font=("Helvetica", 14))
        self.text_entry.pack()
        self.text_entry.bind("<KeyRelease>", self.on_key_release)
        
        # Метки времени и ошибок
        self.time_label = tk.Label(root, text="Время: 0.00 сек", font=("Helvetica", 14))
        self.time_label.pack(pady=5)
        self.words_label = tk.Label(root, text="Слов: 0", font=("Helvetica", 14))
        self.words_label.pack(pady=5)
        self.errors_label = tk.Label(root, text="Ошибки: 0", font=("Helvetica", 14))
        self.errors_label.pack(pady=5)
        self.total_errors = 0  # Общее количество ошибок за тест

        # Кнопка сброса
        self.reset_button = tk.Button(root, text="Сбросить", command=self.reset_test)
        self.reset_button.pack(pady=10)
        
        # Инициализация переменных
        self.correct_chars = 0
        self.total_chars = len(self.target_text)
        self.errors = 0
        self.start_time = None

    def set_custom_text(self):
        new_text = self.custom_text_entry.get("1.0", tk.END).strip()
        if new_text:
            self.target_text = new_text
        else:
            self.target_text = self.default_text
        self.label_target.config(text=self.target_text)
        self.reset_test()

    def generate_random_text(self):
        self.target_text = random.choice(self.sample_texts)
        self.label_target.config(text=self.target_text)
        self.reset_test()

    def reset_test(self):
        self.text_entry.delete("1.0", tk.END)
        self.label_target.config(fg="black")
        self.time_label.config(text="Время: 0.00 сек")
        self.words_label.config(text="Слов: 0")
        self.errors_label.config(text="Ошибки: 0")
        self.current_word_index = 0
        self.correct_chars = 0
        self.errors = 0
        self.total_errors = 0
        self.start_time = None
        self.timer_running = False

    def on_key_release(self, event):
        if not self.timer_running:
            self.start_time = time.time()
            self.timer_running = True
            self.update_time()

        input_text = self.text_entry.get("1.0", tk.END).rstrip("\n")
        self.update_highlighting(input_text)

        # Обновление счетчика слов
        words_typed = input_text.split()
        self.words_label.config(text=f"Слов: {len(words_typed)}")
        
        # Подсчет ошибок
        self.errors = 0
        for i, (char_input, char_target) in enumerate(zip(input_text, self.target_text)):
            if char_input != char_target:
                self.errors += 1
        self.total_errors = self.errors  # Обновляем общее количество ошибок для отображения
        self.errors_label.config(text=f"Ошибки: {self.total_errors}")
        
        # Проверка окончания
        if input_text == self.target_text:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"Время: {elapsed:.2f} сек")
            self.timer_running = False

    def update_highlighting(self, input_text):
        # Удаление старых подсветок
        self.text_entry.tag_remove("error", "1.0", tk.END)
        self.text_entry.tag_remove("matched", "1.0", tk.END)

        # Подсветка ошибок и правильных символов
        for i, (char_input, char_target) in enumerate(zip(input_text, self.target_text)):
            if char_input == char_target:
                # Правильный символ — зеленый
                self.text_entry.tag_add("matched", f"1.0 + {i}c", f"1.0 + {i+1}c")
            else:
                # Ошибка — красный
                self.text_entry.tag_add("error", f"1.0 + {i}c", f"1.0 + {i+1}c")
        # Цвета для подсветки
        self.text_entry.tag_config("error", foreground="red")
        self.text_entry.tag_config("matched", foreground="green")
        # Ограничение длины
        if len(input_text) > len(self.target_text):
            self.text_entry.delete(f"1.0 + {len(self.target_text)}c", tk.END)

    def update_time(self):
        if self.timer_running:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"Время: {elapsed:.2f} сек")
            self.root.after(100, self.update_time)

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTest(root)
    root.mainloop()