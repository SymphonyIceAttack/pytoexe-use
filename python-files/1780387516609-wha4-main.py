import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")
        self.root.geometry("800x650")

        # --- Переменные для теста ---
        self.original_text = ""
        self.current_index = 0  # Текущая позиция в тексте
        self.start_time = None
        self.total_errors = 0

        # --- Текстовые поля ---
        self.label_source = tk.Label(root, text="Текст для набора:")
        self.text_display = scrolledtext.ScrolledText(root, width=90, height=10, wrap='word', state='disabled')

        self.label_input = tk.Label(root, text="Ваш набор:")
        self.user_input = scrolledtext.ScrolledText(root, width=90, height=10, wrap='word')
        self.user_input.bind('<Key>', self.on_key_press) # Отслеживаем каждое нажатие

        # --- Кнопки (в отдельном фрейме для центрирования) ---
        button_frame = tk.Frame(root)
        self.load_button = tk.Button(button_frame, text="Загрузить текст (.txt)", command=self.load_file)
        self.reset_button = tk.Button(button_frame, text="Начать заново", command=self.reset_test)

        # --- Строка состояния ---
        self.status_var = tk.StringVar(value="Ошибок: 0 | Слов: 0")
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)

        # --- Размещение виджетов ---
        self.label_source.pack(pady=(10, 0))
        self.text_display.pack(padx=20, pady=5, fill='both', expand=True)

        self.label_input.pack(pady=(10, 0))
        self.user_input.pack(padx=20, pady=5, fill='both', expand=True)

        # Располагаем кнопки рядом друг с другом
        self.load_button.pack(side='left', padx=10, ipadx=10, ipady=4)
        self.reset_button.pack(side='right', padx=10, ipadx=10, ipady=4)
        button_frame.pack(pady=10)

        self.status_bar.pack(side='bottom', fill='x')

    def load_file(self):
        """Открывает .txt файл и загружает его содержимое."""
        file_path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.original_text = content
                self.text_display.config(state='normal')
                self.text_display.delete(1.0, tk.END)
                self.text_display.insert(tk.END, self.original_text)
                self.text_display.config(state='disabled')
                self.reset_test() # Автоматический сброс при загрузке нового текста
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def on_key_press(self, event=None):
        """
        Обрабатывает каждое нажатие клавиши.
        Сравнивает нажатый символ с ожидаемым и обновляет статистику.
        """
        # Игнорируем управляющие клавиши (Shift, Ctrl, Alt и т.д.)
        if event.state != 0 or len(event.char) == 0:
            return

        # Если тест еще не начался или уже завершен, ничего не делаем
        if self.start_time is None or self.current_index >= len(self.original_text):
            return

        user_char = event.char
        expected_char = self.original_text[self.current_index]

        # Запускаем таймер при первом правильном действии
        if self.start_time is None and user_char == expected_char:
            self.start_time = time.time()

        if user_char == expected_char:
            # ВЕРНЫЙ СИМВОЛ
            self.user_input.insert(tk.END, user_char)
            self.current_index += 1
            self.highlight_char(self.current_index - 1, 'green')
        else:
            # ОШИБКА
            self.total_errors += 1
            self.highlight_char(self.current_index, 'red')

        # Обновляем счетчики в статус-баре
        words_typed = len(self.user_input.get(1.0, tk.END).split())
        self.status_var.set(f"Ошибок: {self.total_errors} | Слов: {words_typed}")

        # Проверка завершения теста
        if self.current_index == len(self.original_text):
            self.end_time = time.time()
            elapsed_time = max(self.end_time - self.start_time, 0.001) # Защита от деления на ноль
            wpm = round((words_typed / elapsed_time) * 60)
            print(f"\n--- Тест завершен! ---")
            print(f"Время: {elapsed_time:.2f} сек")
            print(f"Скорость: {wpm} слов/мин")
            print(f"Ошибок допущено: {self.total_errors}\n")

    def highlight_char(self, index, color):
        """Подсвечивает символ в исходном тексте заданным цветом."""
        fmt = tk.Text.tag_configure(self.text_display, foreground='black') # Сброс цвета
        tag_name = f"tag_{index}"
        self.text_display.tag_delete(tag_name) # Удаляем старую подсветку, если была
        self.text_display.tag_add(tag_name, f"1.{index}", f"1.{index+1}")
        self.text_display.tag_configure(tag_name, background=color)

    def reset_test(self):
        """Сбрасывает все параметры теста для начала заново."""
        self.current_index = 0
        self.total_errors = 0
        self.start_time = None
        self.end_time = None

        self.user_input.delete(1.0, tk.END)
        self.text_display.tag_remove('sel', '1.0', 'end') # Убираем всю подсветку
        self.status_var.set("Ошибок: 0 | Слов: 0")
        self.user_input.focus_set() # Возвращаем фокус на поле ввода

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestApp(root)
    root.mainloop()