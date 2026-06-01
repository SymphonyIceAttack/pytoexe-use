import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тренажёр скорости печати")
        self.root.geometry("800x550") # Увеличено окно по высоте

        # --- Данные ---
        self.default_phrases = [
            "Съешь ещё этих мягких французских булок да выпей же чаю.",
            "В чащах юга жил-был цитрус? Да, но фальшивый экземпляр!",
            "Ловко вскочив на коня, ястреб взвился в небеса.",
            "Python — мощный язык программирования общего назначения."
        ]
        self.current_phrase = ""
        self.start_time = 0

        # --- Создание виджетов ---
        # Верхняя панель управления
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, fill='x')

        self.btn_start = tk.Button(control_frame, text="Старт / Начать заново", command=self.start_test)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_custom = tk.Button(control_frame, text="Свой текст...", command=self.set_custom_text)
        self.btn_custom.grid(row=0, column=1, padx=5)

        # Текст для набора
        self.text_display = tk.Text(root, height=4, width=95, font=("Courier New", 12), wrap='word', bg='#f0f0f0')
        self.text_display.config(state='disabled') # Делаем поле только для чтения
        self.text_display.pack(pady=10)

        # Поле для ввода пользователя
        self.entry_input = tk.Entry(root, font=("Arial", 14), width=80)
        self.entry_input.pack(pady=5)

        # Статистика
        self.label_stats = tk.Label(root, text="", font=("Arial", 10), justify='left', fg='#555')
        self.label_stats.pack(pady=10)

        # Привязка события нажатия клавиши
        self.entry_input.bind("<KeyRelease>", self.check_input)

    def set_custom_text(self):
        """Открывает диалоговое окно для ввода собственного текста."""
        custom_text = simpledialog.askstring(
            title="Собственный текст",
            prompt="Введите или вставьте текст для теста:",
            parent=self.root
        )
        if custom_text: # Если пользователь ввёл текст и нажал ОК
            self.custom_phrase = custom_text.strip()
            messagebox.showinfo("Готово", "Ваш текст установлен. Нажмите 'Старт'!")

    def start_test(self):
        """Запускает новый тест."""
        # Выбираем фразу: если есть кастомный текст, используем его, иначе - случайный из списка
        if hasattr(self, 'custom_phrase'):
            self.current_phrase = self.custom_phrase
        else:
            self.current_phrase = random.choice(self.default_phrases)
        
        self.start_time = time.time()

        # Обновляем интерфейс
        self.text_display.config(state='normal')
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(tk.END, self.current_phrase)
        self.text_display.config(state='disabled')

        self.entry_input.config(state='normal')
        self.entry_input.delete(0, tk.END)
        self.label_stats.config(text="Печатайте!

