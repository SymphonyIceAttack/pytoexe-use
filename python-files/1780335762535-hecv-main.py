import tkinter as tk
from tkinter import messagebox
import random
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажёр скорости печати")
        self.root.geometry("750x450") # Увеличена ширина под Courier New

        self.phrases = [
            "Съешь ещё этих мягких французских булок да выпей же чаю.",
            "В чащах юга жил-был цитрус? Да, но фальшивый экземпляр!",
            "Ловко вскочив на коня, ястреб взвился в небеса.",
            "Python — мощный язык программирования общего назначения.",
            "Красивая девушка шла по набережной и любовалась закатом."
        ]

        # --- Создание виджетов ---
        self.label_prompt = tk.Label(root, text="Нажмите 'Старт', чтобы начать.", font=("Arial", 12))
        self.label_prompt.pack(pady=10)

        self.text_display = tk.Text(root, height=3, width=90, font=("Courier New", 12), wrap='word')
        self.text_display.config(state='disabled') # Делаем поле только для чтения
        self.text_display.pack(pady=10)

        self.entry_input = tk.Entry(root, font=("Arial", 14), width=80)
        self.entry_input.pack(pady=5)

        self.button_start = tk.Button(root, text="Старт / Начать заново", command=self.start_test)
        self.button_start.pack(pady=5)

        self.label_stats = tk.Label(root, text="", font=("Arial", 10), justify='left')
        self.label_stats.pack(pady=10)

        # Привязываем событие нажатия клавиши к полю ввода
        self.entry_input.bind("<KeyRelease>", self.check_input)

    def start_test(self):
        """Запускает новый тест."""
        self.current_phrase = random.choice(self.phrases)
        self.start_time = time.time() # Присваиваем время старта

        # Обновляем интерфейс
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.current_phrase)
        self.text_display.config(state='disabled')

        self.entry_input.config(state='normal') # Разблокируем ввод
        self.entry_input.delete(0, tk.END)
        
        # Сбрасываем статистику перед началом
        self.label_stats.config(text="Печатайте! Время пошло.")
        self.entry_input.focus_set()

    def check_input(self, event=None):
        """
        Проверяет ввод пользователя. Исправлена проверка наличия активного теста.
        Используется проверка существования атрибута через vars(self).
        """
        if 'start_time' not in vars(self): 
            return # Тест еще не начат

        user_text = self.entry_input.get()
        elapsed_seconds = max(time.time() - self.start_time, 1)

        wpm = round((len(user_text) / 5) / (elapsed_seconds / 60))

        errors = sum(1 for a, b in zip(self.current_phrase, user_text) if a != b)
        errors += abs(len(self.current_phrase) - len(user_text))

        accuracy_percent = round(((len(self.current_phrase) - errors) / len(self.current_phrase)) * 100) if self.current_phrase else 100

        stats_text = f"Скорость: {wpm} слов/мин | Точность: {accuracy_percent}% | Ошибок: {errors}"
        self.label_stats.config(text=stats_text)

        # Проверка завершения теста
        if user_text == self.current_phrase:
            end_time = time.time()
            total_time = round(end_time - self.start_time, 2)
            
            # Блокируем ввод и показываем финальный результат
            self.entry_input.config(state='disabled')
            final_msg = (
                f"Тест успешно пройден!\n"
                f"Время: {total_time} сек.\n\n"
                f"{stats_text}"
            )
            messagebox.showinfo("Тест завершён!", final_msg, parent=self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestApp(root)
    root.mainloop()