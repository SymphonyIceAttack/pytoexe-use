import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")
        self.root.geometry("700x500")

        # --- Переменные ---
        self.original_text = ""
        self.start_time = None
        self.end_time = None

        # --- Текстовые поля ---
        # Поле с текстом для набора
        self.text_label = tk.Label(root, text="Текст для набора:")
        self.text_display = scrolledtext.ScrolledText(root, width=80, height=10, wrap='word', state='disabled')
        
        # Поле для ввода пользователя
        self.input_label = tk.Label(root, text="Ваш набор:")
        self.user_input = scrolledtext.ScrolledText(root, width=80, height=10, wrap='word')
        self.user_input.bind('<Key>', self.on_key_press) # Отслеживаем нажатия клавиш

        # --- Строка состояния для счетчика слов ---
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)

        # --- Панель кнопок (располагается по центру) ---
        button_frame = tk.Frame(root)
        self.load_button = tk.Button(button_frame, text="Загрузить текст (.txt)", command=self.load_file)
        self.reset_button = tk.Button(button_frame, text="Начать заново", command=self.reset_test)

        # Размещение виджетов в окне
        self.text_label.pack(pady=(10, 0))
        self.text_display.pack(padx=20, pady=5, fill='both', expand=True)

        self.input_label.pack(pady=(10, 0))
        self.user_input.pack(padx=20, pady=5, fill='both', expand=True)

        # Располагаем кнопки в фрейме друг за другом (по горизонтали)
        self.load_button.pack(side='left', padx=10, ipadx=10, ipady=5)
        self.reset_button.pack(side='right', padx=10, ipadx=10, ipady=5)
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
                self.reset_test() # Сброс при каждой новой загрузке
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")

    def on_key_press(self, event=None):
        """Обрабатывает каждое нажатие клавиши пользователем."""
        # Запускаем таймер при первом нажатии
        if self.start_time is None and self.user_input.get(1.0, tk.END).strip():
            self.start_time = time.time()

        # Проверяем, завершен ли ввод
        user_text = self.user_input.get(1.0, tk.END)
        # Сравниваем без последнего символа '\n', который добавляет ScrolledText
        if user_text.rstrip('\n') == self.original_text:
            self.end_time = time.time()
            elapsed = max(self.end_time - self.start_time, 0.01) # Защита от деления на ноль
            words_typed = len(user_text.split())
            wpm = round((words_typed / elapsed) * 60)
            print(f"Тест завершен! Ваша скорость: {wpm} слов/мин.")

        # Обновляем счетчик слов в статус-баре
        current_words = len(user_text.split())
        self.status_var.set(f"Введено слов: {current_words}")

    def reset_test(self):
        """Сбрасывает все поля и таймеры."""
        self.user_input.delete(1.0, tk.END)
        self.start_time = None
        self.end_time = None
        self.status_var.set("")
        self.user_input.focus_set() # Возвращаем фокус на поле ввода

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestApp(root)
    root.mainloop()