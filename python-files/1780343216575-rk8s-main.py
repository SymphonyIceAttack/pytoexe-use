import tkinter as tk
from tkinter import messagebox, simpledialog
import time

class TypingTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест скорости печати")
        self.root.geometry("800x500")
        
        # Переменные состояния
        self.original_text = "Привет! Это стандартный текст для теста. Попробуйте напечатать его без ошибок."
        self.start_time = None
        self.end_time = None
        self.is_running = False

        # Настройка тегов для Text-виджета
        self.text_area = tk.Text(self.root, wrap='word', font=('Courier New', 14))
        self.text_area.pack(expand=True, fill='both')
        self.text_area.tag_configure("correct", foreground="green")
        self.text_area.tag_configure("wrong", foreground="red")
        self.text_area.tag_configure("default", foreground="black")

        # Привязка событий
        self.text_area.bind("<Key>", self.on_key_press)
        self.text_area.bind("<FocusOut>", lambda e: self.stop_timer())

        # Панель управления
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x', pady=5)

        self.speed_label = tk.Label(control_frame, text="Скорость: 0 зн/мин | Ошибок: 0", font=('Arial', 12))
        self.speed_label.pack(side='left', padx=10)

        btn_custom = tk.Button(control_frame, text="Свой текст", command=self.set_custom_text)
        btn_custom.pack(side='right', padx=5)

        btn_reset = tk.Button(control_frame, text="Сбросить", command=self.reset_test)
        btn_reset.pack(side='right', padx=5)

        self.load_default_text()

    def load_default_text(self):
        """Загрузка исходного текста в редактор"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, self.original_text, ("default"))
        self.text_area.mark_set(tk.INSERT, 1.0) # Устанавливаем курсор в начало

    def set_custom_text(self):
        """Установка собственного текста"""
        new_text = simpledialog.askstring("Ввод текста", "Введите текст для теста:", parent=self.root)
        if new_text is not None and new_text.strip():
            self.original_text = new_text
            self.reset_test()

    def on_key_press(self, event):
        """Обработка каждого нажатия клавиши"""
        # Игнорируем служебные клавиши навигации
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R',
                            'Left', 'Right', 'Up', 'Down', 'Home', 'End'):
            return

        # Старт таймера при первом действии пользователя
        if not self.is_running:
            self.start_timer()

        current_pos = self.text_area.index(tk.INSERT)
        line, char = map(int, current_pos.split('.'))
        expected_char = ''
        try:
            expected_char = self.original_text[int(current_pos)-1]
        except IndexError:
            pass

        user_input = self.text_area.get(f"{current_pos} -1c", current_pos)

        # Проверяем текущий символ
        if user_input == expected_char:
            self.text_area.tag_add("correct", f"{line}.{char-1}", current_pos)
            self.text_area.tag_remove("wrong", f"{line}.{char-1}", current_pos)
        else:
            self.text_area.tag_add("wrong", f"{line}.{char-1}", current_pos)
            self.text_area.tag_remove("correct", f"{line}.{char-1}", current_pos)

        self.update_stats()

    def start_timer(self):
        self.start_time = time.time()
        self.is_running = True

    def stop_timer(self):
        if self.is_running:
            self.end_time = time.time()
            self.is_running = False
            self.update_stats()

    def update_stats(self):
        """Пересчет и отображение статистики"""
        elapsed = time.time() - self.start_time if self.is_running else (self.end_time - self.start_time if self.end_time else 0)
        entered_text = self.text_area.get(1.0, tk.END).replace('\n', '')
        length = len(entered_text.replace(' ', '')) # Считаем только значимые символы
        speed = round((length / max(elapsed, 1)) * 60) if elapsed > 0 else 0

        wrong_tags = list(self.text_area.tag_ranges("wrong"))
        error_count = len(wrong_tags) // 2

        self.speed_label.config(text=f"Скорость: {speed} зн/мин | Ошибок: {error_count}")

    def reset_test(self):
        """Сброс теста с подтверждением"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите сбросить тест? Текущий прогресс будет потерян."):
            self.start_time = None
            self.end_time = None
            self.is_running = False
            self.load_default_text()
            self.speed_label.config(text="Скорость: 0 зн/мин | Ошибок: 0")

    def on_closing(self):
        """Обработчик закрытия окна с подтверждением"""
        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти из программы?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TypingTestApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()