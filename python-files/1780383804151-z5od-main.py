import tkinter as tk
import time
import random

class TypingSpeedTest:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")

        # Список текстов с ошибками
        self.texts = [
            "Пример текста с ошбками для трениировки скорости печати.",
            "Это тестовое предложение с некорректными словами, чтобы улучшить ваши навыки.",
            "Проверьте свою спдность печати с этимобразцом текста с ошибками.",
            "Максимально полезный тест для того, чтобы проверить, как быстро вы печатаете.",
            "Вы должны исправить эти ошиби в тексте, чтобы завершить тест."
        ]
        
        self.start_time = None
        self.time_limit = 30  # Ограничение по времени в секундах
        self.timer_running = False
        
        # Интерфейс
        self.label = tk.Label(root, text="Введите следующий текст:")
        self.label.pack()

        self.text_area = tk.Text(root, height=5, width=50)
        self.text_area.pack()
        self.text_area.bind("<KeyRelease>", self.check_text)

        self.start_button = tk.Button(root, text="Начать", command=self.start_test)
        self.start_button.pack()

        self.result_label = tk.Label(root, text="", fg="green")
        self.result_label.pack()

        self.timer_label = tk.Label(root, text="", fg="red")
        self.timer_label.pack()

        self.timer = None

    def start_test(self):
        """Начинает тест, отображая случайный текст для ввода."""
        self.selected_text = random.choice(self.texts)  # Случайный выбор текста
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.selected_text)
        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()
        self.result_label.config(text="")

    def check_text(self, event):
        """Проверяет введенный текст."""
        if not self.timer_running:
            return

        typed_text = self.text_area.get(1.0, tk.END).strip()
        
        # Проверка, совпадает ли введенный текст с оригиналом
        if typed_text == self.selected_text:
            self.end_test()

    def update_timer(self):
        """Обновляет таймер."""
        if self.start_time is not None and self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            remaining_time = self.time_limit - elapsed_time

            if remaining_time <= 0:
                self.timer_running = False
                self.end_test()
                return

            self.timer_label.config(text=f"Оставшееся время: {remaining_time} сек")
            self.timer = self.root.after(1000, self.update_timer)

    def end_test(self):
        """Заканчивает тест, подсчитывает скорость печати."""
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        
        end_time = time.time()
        time_taken = end_time - self.start_time
        
        # Подсчет слов в исходном тексте
        word_count = len(self.selected_text.split())
        # Подсчет скорости печати в словах в минуту
        typing_speed = (word_count / (time_taken if time_taken > 0 else 1)) * 60  

        self.result_label.config(text=f"Скорость печати: {typing_speed:.2f} сл./мин")
        self.timer_label.config(text="")
        self.start_time = None

if __name__ == "__main__":
    root = tk.Tk()
    typing_test = TypingSpeedTest(root)
    root.mainloop()