import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import random

class TypingTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")
        
        # Список примеров без тире
        self.examples = [
            "Это пример текста для теста скорости печати без тире.",
            "Пожалуйста, напечатайте этот текст как можно быстрее и точнее.",
            "Тест поможет вам улучшить навыки набора текста.",
            "Быстрая печать требует практики и сосредоточенности.",
            "Практикуйтесь регулярно чтобы повысить свою скорость.",
            "Тексты для тренировки можно добавлять самостоятельно.",
            "Тестирование скорости печати помогает выявить слабые места.",
            "Концентрация и правильная техника важны для успеха.",
            "Чем больше практики тем лучше ваш результат станет.",
            "Запомните важность правильной постановки рук и пальцев.",
            "Тренировка помогает преодолеть страх ошибок.",
            "Используйте удобное положение тела для комфортной работы.",
            "Постоянная практика делает вас быстрее и точнее.",
            "Обучение скоростной печати — это полезное умение для работы.",
            "Постарайтесь печатать без ошибок и с хорошей скоростью.",
            "Тексты для тренировки без тире помогают сосредоточиться на скорости и точности.",
            "Регулярные тренировки заметно улучшают навыки набора текста.",
        ]
        
        self.current_text = ""
        self.start_time = None
        self.correct_word_indices = []
        self.wrong_word_indices = []

        self.create_widgets()
        self.load_example()

    def create_widgets(self):
        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        self.btn_load_example = tk.Button(btn_frame, text="Добавить пример", command=self.load_example)
        self.btn_load_example.pack(side=tk.LEFT, padx=5)

        self.btn_add_text = tk.Button(btn_frame, text="Добавить свой текст", command=self.add_custom_text)
        self.btn_add_text.pack(side=tk.LEFT, padx=5)

        self.btn_start = tk.Button(btn_frame, text="Начать тест", command=self.start_test)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        # Текст для отображения примера
        self.label_example = tk.Label(self.root, text="", font=("Arial", 14))
        self.label_example.pack(pady=10)

        # Текстовое поле для ввода
        self.text_entry = tk.Text(self.root, height=10, width=80, state=tk.DISABLED, font=("Arial", 14))
        self.text_entry.pack(pady=10)
        self.text_entry.bind("<KeyPress>", self.on_key_press)

        # Результаты
        self.label_result = tk.Label(self.root, text="", font=("Arial", 12))
        self.label_result.pack(pady=5)

    def load_example(self):
        self.current_text = random.choice(self.examples)
        self.label_example.config(text=self.current_text)
        self.reset_text_field()
        self.correct_word_indices.clear()
        self.wrong_word_indices.clear()
        self.label_result.config(text="")

    def add_custom_text(self):
        text = simpledialog.askstring("Добавить текст", "Введите ваш текст без тире:")
        if text:
            self.examples.append(text)
            messagebox.showinfo("Готово", "Текст добавлен в список примеров.")

    def start_test(self):
        self.reset_text_field()
        self.text_entry.config(state=tk.NORMAL)
        self.text_entry.delete("1.0", tk.END)
        self.text_entry.focus()
        self.start_time = time.time()
        self.correct_word_indices.clear()
        self.wrong_word_indices.clear()
        self.label_result.config(text="")

    def reset_text_field(self):
        self.text_entry.config(state=tk.NORMAL)
        self.text_entry.delete("1.0", tk.END)
        self.text_entry.config(bg="white")

    def on_key_press(self, event):
        if event.keysym in ("space", "Return"):
            self.check_input()

    def check_input(self):
        typed_text = self.text_entry.get("1.0", tk.END).rstrip("\n")
        original_words = self.current_text.split()
        typed_words = typed_text.split()

        self.correct_word_indices.clear()
        self.wrong_word_indices.clear()

        for i, word in enumerate(typed_words):
            if i < len(original_words):
                if word == original_words[i]:
                    self.correct_word_indices.append(i)
                else:
                    self.wrong_word_indices.append(i)
            else:
                self.wrong_word_indices.append(i)

        self.display_feedback(typed_words, original_words)
        self.calculate_results()
        self.text_entry.config(state=tk.DISABLED)

    def display_feedback(self, typed_words, original_words):
        self.text_entry.tag_remove("correct", "1.0", tk.END)
        self.text_entry.tag_remove("wrong", "1.0", tk.END)

        index = "1.0"
        for i, word in enumerate(typed_words):
            start_index = index
            end_index = f"{start_index} + {len(word)}c"
            # Добавляем пробел после слова, если есть
            if i < len(typed_words) - 1:
                end_index = f"{end_index} + 1c"
            # Добавляем тег для правильных и неправильных слов
            if i in self.correct_word_indices:
                self.text_entry.tag_add("correct", start_index, end_index)
            elif i in self.wrong_word_indices:
                self.text_entry.tag_add("wrong", start_index, end_index)
            index = self.text_entry.index(end_index)

        # Настраиваем цвета и подчеркнение
        self.text_entry.tag_config("correct", foreground="green")
        self.text_entry.tag_config("wrong", foreground="red", underline=True)

    def calculate_results(self):
        end_time = time.time()
        elapsed = end_time - self.start_time
        total_words = len(self.current_text.split())
        correct_words = len(self.correct_word_indices)
        wrong_words = len(self.wrong_word_indices)
        wpm = (correct_words / elapsed) * 60 if elapsed > 0 else 0
        result_text = (
            f"Всего слов: {total_words}\n"
            f"Правильно: {correct_words}\n"
            f"Ошибки: {wrong_words}\n"
            f"Время: {elapsed:.2f} сек\n"
            f"Скорость: {wpm:.2f} слов/мин"
        )
        self.label_result.config(text=result_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTest(root)
    root.mainloop()