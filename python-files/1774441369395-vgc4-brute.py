import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import pyautogui
import string
from itertools import permutations
import time
import sys
import os

class PasswordGeneratorThread(threading.Thread):
    """Поток для генерации паролей"""
    def __init__(self, base_words, use_upper, use_lower, use_digits, 
                 use_symbols, min_length, max_length, use_combinations, callback):
        super().__init__()
        self.base_words = base_words
        self.use_upper = use_upper
        self.use_lower = use_lower
        self.use_digits = use_digits
        self.use_symbols = use_symbols
        self.min_length = min_length
        self.max_length = max_length
        self.use_combinations = use_combinations
        self.callback = callback
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        
    def generate_variations(self, word):
        """Генерирует вариации слова"""
        variations = [word]
        
        if self.use_upper:
            variations.append(word.upper())
        if self.use_lower:
            variations.append(word.lower())
        if self.use_upper and self.use_lower:
            variations.append(word.capitalize())
            if len(word) <= 5:
                for i in range(1, len(word)):
                    variations.append(word[:i].upper() + word[i:].lower())
                    variations.append(word[:i].lower() + word[i:].upper())
                    
        return list(set(variations))
    
    def run(self):
        words_list = [w.strip() for w in self.base_words.replace(',', ' ').split() if w.strip()]
        
        if not words_list:
            self.callback("error", "Введите хотя бы одно слово")
            return
            
        generated_count = 0
        all_variations = []
        
        # Генерируем вариации слов
        self.callback("status", "Генерация вариаций слов...")
        for word in words_list:
            if not self.is_running:
                break
            all_variations.extend(self.generate_variations(word))
        
        # Добавляем числа
        if self.use_digits and self.is_running:
            self.callback("status", "Добавление цифр...")
            for num in range(1000):
                if not self.is_running:
                    break
                all_variations.append(str(num))
        
        # Добавляем символы
        if self.use_symbols and self.is_running:
            common_symbols = ["!", "@", "#", "$", "%", "&", "*", "?", "+", "="]
            for sym in common_symbols:
                all_variations.append(sym)
        
        all_variations = list(set(all_variations))
        
        if len(all_variations) > 5000:
            self.callback("status", f"Слишком много вариаций ({len(all_variations)}), ограничиваю до 5000")
            all_variations = all_variations[:5000]
        
        self.callback("status", f"Сгенерировано {len(all_variations)} вариаций. Начинаю комбинирование...")
        
        try:
            if self.use_combinations:
                max_r = min(4, len(all_variations) + 1)
                for r in range(1, max_r):
                    if not self.is_running:
                        break
                    for combo in permutations(all_variations, r):
                        if not self.is_running:
                            break
                        password = ''.join(combo)
                        if self.min_length <= len(password) <= self.max_length:
                            self.callback("password", password)
                            generated_count += 1
                            if generated_count % 100 == 0:
                                self.callback("status", f"Сгенерировано {generated_count} паролей...")
            else:
                for variation in all_variations:
                    if not self.is_running:
                        break
                    if self.min_length <= len(variation) <= self.max_length:
                        self.callback("password", variation)
                        generated_count += 1
                        
        except Exception as e:
            self.callback("error", str(e))
        
        self.callback("status", f"Генерация завершена. Всего сгенерировано {generated_count} паролей")
        self.callback("finished", None)


class PasswordDialog(tk.Toplevel):
    """Диалоговое окно для ввода пароля"""
    def __init__(self, parent, title="Введите пароль"):
        super().__init__(parent)
        self.title(title)
        self.result = False
        self.password = ""
        
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Центрируем окно
        self.geometry("300x150")
        self.resizable(False, False)
        
        # Центрируем относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (300 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (150 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Создаем виджеты
        frame = ttk.Frame(self, padding="20")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Для выполнения этого действия\nвведите пароль:", 
                 font=("Arial", 10)).pack(pady=(0, 10))
        
        self.password_entry = ttk.Entry(frame, show="*", font=("Arial", 12))
        self.password_entry.pack(fill="x", pady=(0, 10))
        self.password_entry.focus()
        
        # Привязываем Enter
        self.password_entry.bind('<Return>', lambda e: self.check_password())
        
        button_frame = ttk.Frame(frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="OK", command=self.check_password).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side="left", padx=5)
        
        # Делаем окно поверх всех
        self.attributes('-topmost', True)
        
    def check_password(self):
        self.password = self.password_entry.get()
        self.result = True
        self.destroy()
        
    def cancel(self):
        self.result = False
        self.destroy()


class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор паролей для подбора")
        
        # Полноэкранный режим
        self.root.attributes('-fullscreen', True)
        
        # Цвета для оформления
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.accent_color = "#0078d4"
        
        # Настройка стилей
        self.root.configure(bg=self.bg_color)
        
        # Переменные для защиты
        self.admin_password = "pipisan"  # Пароль для закрытия/остановки
        self.is_closing = False
        
        # Привязываем клавишу Escape для выхода с паролем
        self.root.bind('<Escape>', lambda e: self.request_exit())
        
        # Привязываем закрытие окна
        self.root.protocol("WM_DELETE_WINDOW", self.request_exit)
        
        self.generator_thread = None
        self.last_password = ""
        
        self.create_widgets()
        
        # Показываем приветствие
        self.show_welcome()
        
    def show_welcome(self):
        """Показывает приветственное сообщение"""
        welcome = tk.Toplevel(self.root)
        welcome.title("Добро пожаловать")
        welcome.geometry("400x200")
        welcome.transient(self.root)
        welcome.grab_set()
        
        # Центрируем
        welcome.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (200 // 2)
        welcome.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(welcome, padding="20")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Генератор паролей", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Label(frame, text="Программа запущена в полноэкранном режиме\n"
                  "Для закрытия программы нажмите ESC\n"
                  "и введите пароль", 
                 font=("Arial", 10)).pack(pady=10)
        
        ttk.Button(frame, text="Понятно", command=welcome.destroy).pack(pady=10)
        
        # Автоматическое закрытие через 3 секунды
        welcome.after(3000, welcome.destroy)
        
    def create_widgets(self):
        # Основной контейнер с отступами
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Заголовок
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="ГЕНЕРАТОР ПАРОЛЕЙ", 
                                font=("Arial", 24, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Подбор комбинаций слов, цифр и символов",
                                  font=("Arial", 10))
        subtitle_label.pack()
        
        # Базовые слова
        ttk.Label(main_frame, text="Базовые слова (через запятую или пробел):", 
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.words_input = ttk.Entry(main_frame, width=80, font=("Arial", 10))
        self.words_input.insert(0, "password admin qwerty 123")
        self.words_input.pack(fill="x", pady=(0, 10))
        
        # Набор символов
        chars_frame = ttk.LabelFrame(main_frame, text="Набор символов", padding=10)
        chars_frame.pack(fill="x", pady=(0, 10))
        
        self.upper_case = tk.BooleanVar()
        self.lower_case = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar()
        
        # Две колонки для чекбоксов
        chars_left = ttk.Frame(chars_frame)
        chars_left.pack(side="left", fill="both", expand=True)
        
        chars_right = ttk.Frame(chars_frame)
        chars_right.pack(side="left", fill="both", expand=True)
        
        ttk.Checkbutton(chars_left, text="Заглавные буквы (A-Z)", 
                       variable=self.upper_case).pack(anchor="w", pady=2)
        ttk.Checkbutton(chars_left, text="Строчные буквы (a-z)", 
                       variable=self.lower_case).pack(anchor="w", pady=2)
        ttk.Checkbutton(chars_right, text="Цифры (0-9)", 
                       variable=self.use_digits).pack(anchor="w", pady=2)
        ttk.Checkbutton(chars_right, text="Спецсимволы (!@#$%...)", 
                       variable=self.use_symbols).pack(anchor="w", pady=2)
        
        # Длина пароля
        length_frame = ttk.LabelFrame(main_frame, text="Длина пароля", padding=10)
        length_frame.pack(fill="x", pady=(0, 10))
        
        length_inner = ttk.Frame(length_frame)
        length_inner.pack()
        
        ttk.Label(length_inner, text="Минимальная:", font=("Arial", 10)).grid(row=0, column=0, padx=5)
        self.min_length = ttk.Spinbox(length_inner, from_=1, to=100, width=10, font=("Arial", 10))
        self.min_length.set(4)
        self.min_length.grid(row=0, column=1, padx=5)
        
        ttk.Label(length_inner, text="Максимальная:", font=("Arial", 10)).grid(row=0, column=2, padx=5)
        self.max_length = ttk.Spinbox(length_inner, from_=1, to=100, width=10, font=("Arial", 10))
        self.max_length.set(20)
        self.max_length.grid(row=0, column=3, padx=5)
        
        # Дополнительные настройки
        options_frame = ttk.LabelFrame(main_frame, text="Дополнительные настройки", padding=10)
        options_frame.pack(fill="x", pady=(0, 10))
        
        self.use_combinations = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Генерировать комбинации из слов (может быть очень много вариантов)", 
                       variable=self.use_combinations).pack(anchor="w", pady=2)
        
        self.auto_paste = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Автоматически вставлять пароли в активное поле (осторожно!)", 
                       variable=self.auto_paste).pack(anchor="w", pady=2)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10)
        
        self.generate_btn = ttk.Button(buttons_frame, text="▶ Начать генерацию", 
                                       command=self.start_generation, width=20)
        self.generate_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(buttons_frame, text="⏹ Остановить", 
                                   command=self.request_stop, width=20)
        self.stop_btn.pack(side="left", padx=5)
        
        self.clear_btn = ttk.Button(buttons_frame, text="🗑 Очистить", 
                                    command=self.clear_output, width=20)
        self.clear_btn.pack(side="left", padx=5)
        
        # Кнопка выхода
        self.exit_btn = ttk.Button(buttons_frame, text="🚪 Выход", 
                                   command=self.request_exit, width=20)
        self.exit_btn.pack(side="left", padx=5)
        
        # Вывод паролей
        output_frame = ttk.LabelFrame(main_frame, text="Сгенерированные пароли", padding=10)
        output_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # Текстовое поле с прокруткой
        text_frame = ttk.Frame(output_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.output_text = scrolledtext.ScrolledText(text_frame, height=15, font=("Courier", 10),
                                                     bg="#1e1e1e", fg="#d4d4d4")
        self.output_text.pack(fill="both", expand=True)
        
        # Кнопки для работы с паролями
        action_frame = ttk.Frame(output_frame)
        action_frame.pack(pady=10)
        
        ttk.Button(action_frame, text="📋 Скопировать выбранный", 
                  command=self.copy_password, width=20).pack(side="left", padx=5)
        ttk.Button(action_frame, text="📌 Вставить выбранный", 
                  command=self.paste_password, width=20).pack(side="left", padx=5)
        ttk.Button(action_frame, text="⏎ Вставить последний", 
                  command=self.paste_last_password, width=20).pack(side="left", padx=5)
        
        # Статус
        self.status_label = ttk.Label(main_frame, text="✅ Готов к работе", 
                                      relief="sunken", font=("Arial", 9))
        self.status_label.pack(fill="x", pady=(5, 0))
        
        # Информация о выходе
        info_label = ttk.Label(main_frame, text="Для выхода нажмите ESC и введите пароль",
                              font=("Arial", 8), foreground="gray")
        info_label.pack(pady=(5, 0))
        
    def check_password(self, action_name):
        """Проверяет пароль перед выполнением защищенного действия"""
        dialog = PasswordDialog(self.root, f"Подтверждение: {action_name}")
        self.root.wait_window(dialog)
        
        if dialog.result and dialog.password == self.admin_password:
            return True
        elif dialog.result:
            messagebox.showerror("Ошибка", "Неверный пароль!", parent=self.root)
            return False
        return False
        
    def request_stop(self):
        """Запрос на остановку генерации с паролем"""
        if self.generator_thread and self.generator_thread.is_alive():
            if self.check_password("остановка генерации"):
                self.stop_generation()
        else:
            messagebox.showinfo("Информация", "Генерация не запущена", parent=self.root)
            
    def stop_generation(self):
        """Останавливает генерацию"""
        if self.generator_thread and self.generator_thread.is_alive():
            self.generator_thread.stop()
            self.update_status("⏸ Генерация остановлена")
            self.generate_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
    def request_exit(self):
        """Запрос на выход с паролем"""
        if self.check_password("закрытие программы"):
            self.safe_exit()
            
    def safe_exit(self):
        """Безопасный выход из программы"""
        if self.generator_thread and self.generator_thread.is_alive():
            self.generator_thread.stop()
            time.sleep(0.5)
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
        
    def start_generation(self):
        if not self.words_input.get():
            messagebox.showwarning("Предупреждение", "Введите хотя бы одно слово", parent=self.root)
            return
            
        if not (self.upper_case.get() or self.lower_case.get() or 
                self.use_digits.get() or self.use_symbols.get()):
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один набор символов", parent=self.root)
            return
        
        # Очищаем вывод
        self.output_text.delete(1.0, tk.END)
        self.last_password = ""
        
        # Запускаем поток генерации
        self.generator_thread = PasswordGeneratorThread(
            self.words_input.get(),
            self.upper_case.get(),
            self.lower_case.get(),
            self.use_digits.get(),
            self.use_symbols.get(),
            int(self.min_length.get()),
            int(self.max_length.get()),
            self.use_combinations.get(),
            self.handle_generator_message
        )
        
        self.generator_thread.start()
        
        self.generate_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.update_status("⏳ Генерация запущена...")
        
    def handle_generator_message(self, msg_type, value):
        if msg_type == "password":
            self.add_password(value)
        elif msg_type == "status":
            self.update_status(value)
        elif msg_type == "error":
            self.update_status(f"❌ Ошибка: {value}")
            messagebox.showerror("Ошибка", value, parent=self.root)
        elif msg_type == "finished":
            self.generate_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
    def add_password(self, password):
        self.output_text.insert(tk.END, password + "\n")
        self.last_password = password
        self.output_text.see(tk.END)
        self.root.update()
        
        if self.auto_paste.get():
            try:
                pyautogui.write(password)
                time.sleep(0.1)
            except Exception as e:
                self.update_status(f"⚠ Ошибка автоматической вставки: {str(e)}")
                
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()
        
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        self.last_password = ""
        self.update_status("✅ Вывод очищен")
        
    def copy_password(self):
        try:
            selected = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
            self.update_status(f"📋 Скопирован пароль: {selected[:30]}...")
        except tk.TclError:
            messagebox.showinfo("Информация", "Выделите пароль для копирования", parent=self.root)
            
    def paste_password(self):
        try:
            selected = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self._paste_to_current_field(selected)
        except tk.TclError:
            messagebox.showwarning("Предупреждение", "Выделите пароль для вставки", parent=self.root)
            
    def paste_last_password(self):
        if self.last_password:
            self._paste_to_current_field(self.last_password)
        else:
            messagebox.showwarning("Предупреждение", "Нет сгенерированных паролей", parent=self.root)
            
    def _paste_to_current_field(self, password):
        try:
            time.sleep(0.2)
            pyautogui.write(password)
            self.update_status(f"📌 Вставлен пароль: {password[:30]}...")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось вставить пароль: {str(e)}", parent=self.root)


def main():
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()