import tkinter as tk
from tkinter import filedialog, messagebox
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # --- Переменные ---
        self.original_text = "Привет! Это стандартный текст для теста. Попробуйте напечатать его без ошибок."
        self.input_start_index = "1.0"
        self.start_time = None
        self.end_time = None
        self.test_finished = False

        # --- Панель управления ---
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x', pady=5)

        self.stats_label = tk.Label(control_frame, text="Время: 00:00 | Скорость: 0 слов/мин | Ошибок: 0", font=('Arial', 12))
        self.stats_label.pack(side='left', padx=10)

        btn_reset = tk.Button(control_frame, text="Сбросить", command=self.reset_test)
        btn_reset.pack(side='right', padx=5)

        # --- Меню ---
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Открыть файл .txt", command=self.load_from_file)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing)
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)

        texts_menu = tk.Menu(self.menu_bar, tearoff=0)
        texts_menu.add_command(label="Короткая фраза", command=lambda: self.load_builtin_text("short"))
        texts_menu.add_command(label="Средний текст", command=lambda: self.load_builtin_text("medium"))
        texts_menu.add_command(label="Длинный текст", command=lambda: self.load_builtin_text("long"))
        self.menu_bar.add_cascade(label="Тексты", menu=texts_menu)

        # --- Текстовое поле ---
        self.text_area = tk.Text(self.root, wrap='word', font=('Courier New', 14), undo=True)
        self.text_area.pack(expand=True, fill='both', padx=10, pady=5)

        # Теги для подсветки
        self.text_area.tag_configure("correct", foreground="green")
        self.text_area.tag_configure("wrong", foreground="red")

        # Привязка событий
        self.text_area.bind("<Key>", self.on_key_press)

         # Загружаем текст по умолчанию при старте
         self.load_text(self.original_text)

    # --- Логика теста ---
    def on_key_press(self, event):
         """Обрабатывает каждое нажатие клавиши"""
         # Игнорируем системные клавиши и навигацию (включая Enter и Tab)
         if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                             'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab', 'Return') or event.char == '':
             return

         # Если тест завершен, блокируем ввод до сброса
         if self.test_finished:
             return "break" # Блокируем обработку клавиши

         # Запуск таймера при первом нажатии клавиши (если есть текст для печати)
         if not self.start_time and self.original_text:
             self.start_time = time.time()
             if self.text_area.get("1.0", "end-1c") == self.original_text:
                 self.input_start_index = "1.0"
             else:
                 self.input_start_index = self.text_area.index("insert")

         if not self.original_text:
             return

         user_input = self.text_area.get(self.input_start_index, "insert")

         # Проверяем только последний введенный символ
         if user_input and len(user_input) <= len(self.original_text):
             expected_char = self.original_text[len(user_input) - 1]
             current_pos = "insert"

             if event.char == expected_char:
                 self.text_area.tag_add("correct", current_pos + "-1c", current_pos)
                 self.text_area.tag_remove("wrong", current_pos + "-1c", current_pos)
             else:
                 self.text_area.tag_add("wrong", current_pos + "-1c", current_pos)
                 self.text_area.tag_remove("correct", current_pos + "-1c", current_pos)

         self.update_stats()

         # Проверка завершения теста
         if user_input == self.original_text and user_input:
             if not self.end_time:
                 self.end_time = time.time()
                 self.test_finished = True # Останавливаем таймер логически
                 messagebox.showinfo("Готово!", "Тест завершен!")
                 # Блокируем ввод в поле после завершения
                 self.text_area.config(state='disabled')
                 return "break" # Блокируем обработку клавиши

    def update_stats(self):
         """Обновляет статистику в реальном времени"""
         if not self.start_time or self.test_finished is None:
             elapsed = 0
             time_str = "00:00"
             speed = 0
         else:
             # Используем end_time, если тест завершен, иначе текущее время
             end_time_to_use = self.end_time if (self.end_time and self.test_finished) else time.time()
             elapsed = end_time_to_use - self.start_time

             minutes, seconds = divmod(int(elapsed), 60)
             time_str = f"{minutes:02d}:{seconds:02d}"

             entered_text = self.text_area.get(self.input_start_index, "insert")
             char_count_with_spaces = len(entered_text)
             # Защита от аномально малых значений времени (ИСПРАВЛЕНИЕ №1)
             speed_divider = max(elapsed, 0.1) 
             speed = round((char_count_with_spaces / speed_divider) * 60 / 5) if elapsed > 0 else 0

          wrong_ranges = self.text_area.tag_ranges("wrong")
          error_count = len(wrong_ranges) // 2 if wrong_ranges else 0

          self.stats_label.config(text=f"Время: {time_str} | Скорость: {speed} слов/мин | Ошибок: {error_count}")

    def reset_test(self):
         """Сбрасывает текущий тест"""
         if messagebox.askyesno("Подтверждение", "Сбросить текущий тест? Прогресс будет утерян."):
             # Сбрасываем все переменные состояния (ИСПРАВЛЕНИЕ №1 из предыдущего шага)
             self.input_start_index = "1.0"
             self.start_time = None
             self.end_time = None
             self.test_finished = False

             for tag in ("correct", "wrong"):
                 self.text_area.tag_remove(tag, "1.0", "end")
             
             cursor_pos = self.text_area.index("insert")
             
             # Разблокируем поле для ввода перед очисткой (УЛУЧШЕНИЕ №2)
             if self.text_area.cget('state') == 'disabled':
                 self.text_area.config(state='normal')
                 
             self.text_area.delete(1.0, tk.END)
             
             if self.original_text:
                 self.text_area.insert(tk.END, self.original_text)
                 try:
                     self.text_area.mark_set(tk.INSERT, cursor_pos)
                 except tk.TclError:
                     self.text_area.mark_set(tk.INSERT, "1.0")
                 self.update_stats()

    def load_text(self, text):
         """Загружает новый текст для теста и сбрасывает состояние"""
         if text and text.strip():
             self.original_text = text.strip()
             self.reset_test()
         else:
             messagebox.showwarning("Ошибка", "Текст для теста не может быть пустым.")

    def load_from_file(self):
         file_path = filedialog.askopenfilename(
             title="Выберите текстовый файл",
             filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*.*"))
         )
         if file_path:
             try:
                 with open(file_path, 'r', encoding='utf-8') as file:
                     content = file.read()
                     if content.strip():
                         self.load_text(content)
                     else:
                         messagebox.showwarning("Ошибка", "Выбранный файл пуст.")
             except Exception as e:
                 messagebox.showerror("Ошибка чтения", f"Не удалось прочитать файл:\n{e}")

    def load_builtin_text(self, text_type):
         texts = {
             "short": "Съешь ещё этих мягких французских булок да выпей же чаю.",
             "medium": "В чащах юга жил-был цитрус? Да, но фальшивый экземпляр!",
             "long": """Удивительный факт: если взять все книги из библиотеки Конгресса США,
сложить их стопкой и поджечь, выделившейся энергии хватит лишь на то,
чтобы вскипятить чайник. Информация — это не просто данные, это энергия."""
         }
         text = texts.get(text_type)
         if text:
            self.load_text(text)

    def on_closing(self):
         if messagebox.askokcancel("Выход", "Вы действительно хотите выйти из программы?"):
            self.root.destroy()


if __name__ == "__main__":
     root = tk.Tk()
     app = TypingTestApp(root)
     root.protocol("WM_DELETE_WINDOW", app.on_closing)
     root.mainloop()