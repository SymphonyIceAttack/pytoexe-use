import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажёр скорости печати")
        self.root.geometry("800x550")

        # --- Данные ---
        self.default_phrases = [
            "Съешь ещё этих мягких французских булок да выпей же чаю.",
            "В чащах юга жил-был цитрус? Да, но фальшивый экземпляр!",
            "Ловко вскочив на коня, ястреб взвился в небеса.",
            "Python — мощный язык программирования общего назначения."
        ]
        self.current_phrase = ""
        self.start_time = 0
        self.input_state_active = False # Флаг для отслеживания активного теста

        # --- Создание виджетов ---
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, fill='x')

        self.btn_start = tk.Button(control_frame, text="Старт / Начать заново", command=self.start_test)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_custom = tk.Button(control_frame, text="Свой текст...", command=self.set_custom_text)
        self.btn_custom.grid(row=0, column=1, padx=5)

        # Текст для набора (с тегами)
        self.text_display = tk.Text(root, height=4, width=95, font=("Courier New", 12), wrap='word', bg='#f0f0f0')
        self.text_display.tag_configure('error', background='#FFB3BA') # Светло-красный для ошибок
        self.text_display.config(state='disabled')
        self.text_display.pack(pady=10)

        # Поле для ввода пользователя
        self.entry_input = tk.Entry(root, font=("Arial", 14), width=80)
        self.entry_input.pack(pady=5)

        self.label_stats = tk.Label(root, text="", font=("Arial", 10), justify='left', fg='#555')
        self.label_stats.pack(pady=10)

        # Привязываем события: нажатие клавиши И получение фокуса
        self.entry_input.bind("<KeyRelease>", self.check_input)
        self.entry_input.bind("<FocusIn>", lambda _: self.highlight_errors())

    def set_custom_text(self):
        custom_text = simpledialog.askstring(
            title="Собственный текст",
            prompt="Введите или вставьте текст для теста:",
            parent=self.root
        )
        if custom_text:
            self.custom_phrase = custom_text.strip()
            messagebox.showinfo("Готово", "Ваш текст установлен. Нажмите 'Старт'!")

    def start_test(self):
        """Запускает новый тест и сбрасывает всё к начальному состоянию."""
        if hasattr(self, 'custom_phrase'):
            self.current_phrase = self.custom_phrase
        else:
            self.current_phrase = random.choice(self.default_phrases)
        
        self.start_time = time.time()
        self.input_state_active = True

        # Сброс интерфейса перед стартом
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.current_phrase)
        # Сначала убираем всю предыдущую подсветку
        for i in range(len(self.current_phrase)):
            self.text_display.tag_remove('error', f'1.{i}', f'1.{i+1}')
        self.text_display.config(state='disabled')

        self.entry_input.config(state='normal')
        self.entry_input.delete(0, tk.END)
        self.label_stats.config(text="Печатайте! Время пошло.")
        self.entry_input.focus_set()

    def check_input(self, event=None):
        """Проверяет ввод и подсвечивает ошибки."""
        if not self.input_state_active:
            return

        user_text = self.entry_input.get()
        elapsed_seconds = max(time.time() - self.start_time, 1)
        wpm = round((len(user_text) / 5) / (elapsed_seconds / 60))

        errors = sum(1 for a, b in zip(self.current_phrase, user_text) if a != b)
        errors += abs(len(self.current_phrase) - len(user_text))
        accuracy_percent = round(((len(self.current_phrase) - errors) / len(self.current_phrase)) * 100) if self.current_phrase else 100

        stats_text = f"Скорость: {wpm} слов/мин | Точность: {accuracy_percent}% | Ошибок: {errors}"
        self.label_stats.config(text=stats_text)

        # Вызов функции подсветки
        self.highlight_errors()

        # Проверка завершения теста
        if user_text == self.current_phrase:
            end_time = time.time()
            total_time = round(end_time - self.start_time, 2)
            self.entry_input.config(state='disabled')
            final_msg = (
                f"Тест успешно пройден!\n"
                f"Время: {total_time} сек.\n\n"
                f"{stats_text}"
            )
            messagebox.showinfo("Тест завершён!", final_msg, parent=self.root)
            self.input_state_active = False # Тест завершён

    def highlight_errors(self):
        """
        Проходит по каждому символу введённого текста и сравнивает его с оригиналом.
        Применяет тег 'error' к неверным символам в поле отображения текста.
        """
        user_text = self.entry_input.get()
        display_length = min(len(user_text), len(self.current_phrase))

        # Проходим по каждому индексу до конца введенного пользователем текста
        for i in range(len(user_text)):
            # Если индекс в пределах длины оригинального текста
            if i < len(self.current_phrase):
                # Сравниваем символы
                if user_text[i] == self.current_phrase[i]:
                    # Правильно -> убираем подсветку, если она была
                    self.text_display.tag_remove('error', f'1.{i}', f'1.{i+1}')
                else:
                    # Ошибка -> добавляем подсветку
                    self.text_display.tag_add('error', f'1.{i}', f'1.{i+1}')
            else:
                # Лишний символ -> тоже ошибка
                self.text_display.tag_add('error', f'1.{i}', f'1.{i+1}')

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestApp(root)
    root.mainloop()