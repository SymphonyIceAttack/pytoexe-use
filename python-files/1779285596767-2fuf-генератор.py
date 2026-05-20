import secrets
import string
import tkinter as tk
from tkinter import messagebox, ttk

class PasswordGenerator:
    """Класс для генерации криптостойких паролей"""
    
    # Наборы символов
    LOWERS = string.ascii_lowercase          # 'abcdefghijklmnopqrstuvwxyz'
    UPPERS = string.ascii_uppercase          # 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    DIGITS = string.digits                   # '0123456789'
    # Специальные символы (без проблемных для некоторых систем)
    SPECIALS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Символы, которые легко перепутать
    AMBIGUOUS = "1lI0O"
    
    def __init__(self):
        self.pool = ""
        self.length = 16
        self.use_lowers = True
        self.use_uppers = True
        self.use_digits = True
        self.use_specials = True
        self.exclude_ambiguous = False
    
    def set_params(self, length, use_lowers, use_uppers, use_digits, use_specials, exclude_ambiguous):
        """Установка параметров генерации"""
        self.length = length
        self.use_lowers = use_lowers
        self.use_uppers = use_uppers
        self.use_digits = use_digits
        self.use_specials = use_specials
        self.exclude_ambiguous = exclude_ambiguous
        self._build_pool()
    
    def _build_pool(self):
        """Формирует пул символов на основе выбранных типов"""
        self.pool = ""
        if self.use_lowers:
            self.pool += self.LOWERS
        if self.use_uppers:
            self.pool += self.UPPERS
        if self.use_digits:
            self.pool += self.DIGITS
        if self.use_specials:
            self.pool += self.SPECIALS
        
        if self.exclude_ambiguous:
            for ch in self.AMBIGUOUS:
                self.pool = self.pool.replace(ch, '')
    
    def generate_one(self):
        """Генерирует один пароль согласно текущим параметрам"""
        if not self.pool:
            return None
        if len(self.pool) < 2:
            return None
        
        # Генерация пароля с помощью криптостойкого метода
        password_chars = [secrets.choice(self.pool) for _ in range(self.length)]
        password = ''.join(password_chars)
        
        # Дополнительная проверка: пароль должен содержать хотя бы один символ из каждого выбранного класса
        # (для соответствия требованиям сложности)
        if self.use_lowers and not any(c in self.LOWERS for c in password):
            return self.generate_one()  # рекурсивная перегенерация (обычно не более 2-3 попыток)
        if self.use_uppers and not any(c in self.UPPERS for c in password):
            return self.generate_one()
        if self.use_digits and not any(c in self.DIGITS for c in password):
            return self.generate_one()
        if self.use_specials and not any(c in self.SPECIALS for c in password):
            return self.generate_one()
        if self.exclude_ambiguous:
            # дополнительно убедимся, что нет нежелательных символов (на всякий случай)
            if any(c in self.AMBIGUOUS for c in password):
                return self.generate_one()
        
        return password
    
    def generate_multiple(self, count):
        """Генерирует несколько паролей (список строк)"""
        passwords = []
        for _ in range(count):
            pwd = self.generate_one()
            if pwd is None:
                return []
            passwords.append(pwd)
        return passwords


class PasswordGeneratorApp:
    """Графическое приложение на Tkinter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор паролей")
        self.root.geometry("550x500")
        self.root.resizable(False, False)
        
        self.generator = PasswordGenerator()
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Рамка для настроек
        settings_frame = ttk.LabelFrame(self.root, text="Настройки пароля", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # Длина пароля
        ttk.Label(settings_frame, text="Длина пароля:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.length_var = tk.IntVar(value=16)
        length_spinbox = ttk.Spinbox(settings_frame, from_=8, to=50, textvariable=self.length_var, width=10)
        length_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(settings_frame, text="(рекомендуется 12-20)").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        
        # Флажки типов символов
        self.use_lowers_var = tk.BooleanVar(value=True)
        self.use_uppers_var = tk.BooleanVar(value=True)
        self.use_digits_var = tk.BooleanVar(value=True)
        self.use_specials_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(settings_frame, text="Строчные (a-z)", variable=self.use_lowers_var).grid(row=1, column=0, sticky="w", padx=20, pady=2)
        ttk.Checkbutton(settings_frame, text="Прописные (A-Z)", variable=self.use_uppers_var).grid(row=1, column=1, sticky="w", padx=20, pady=2)
        ttk.Checkbutton(settings_frame, text="Цифры (0-9)", variable=self.use_digits_var).grid(row=2, column=0, sticky="w", padx=20, pady=2)
        ttk.Checkbutton(settings_frame, text="Спецсимволы (!@#...)", variable=self.use_specials_var).grid(row=2, column=1, sticky="w", padx=20, pady=2)
        
        # Исключение похожих
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Исключить похожие символы (1,l,I,0,O)", 
                        variable=self.exclude_ambiguous_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=5)
        
        # Количество паролей
        ttk.Label(settings_frame, text="Количество паролей:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.count_var = tk.IntVar(value=1)
        count_spinbox = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.count_var, width=10)
        count_spinbox.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        # Кнопка генерации
        generate_btn = ttk.Button(settings_frame, text="Сгенерировать", command=self.generate_passwords)
        generate_btn.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Рамка для вывода результатов
        result_frame = ttk.LabelFrame(self.root, text="Сгенерированные пароли", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Текстовое поле для вывода (с прокруткой)
        text_frame = ttk.Frame(result_frame)
        text_frame.pack(fill="both", expand=True)
        
        self.output_text = tk.Text(text_frame, wrap="word", height=12, font=("Courier", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)
        self.output_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Кнопка копирования
        self.copy_btn = ttk.Button(result_frame, text="Копировать первый пароль", command=self.copy_to_clipboard)
        self.copy_btn.pack(pady=5)
        
        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")
    
    def generate_passwords(self):
        """Обработчик кнопки генерации"""
        length = self.length_var.get()
        if length < 4:
            messagebox.showerror("Ошибка", "Длина пароля должна быть не менее 4 символов")
            return
        
        use_lowers = self.use_lowers_var.get()
        use_uppers = self.use_uppers_var.get()
        use_digits = self.use_digits_var.get()
        use_specials = self.use_specials_var.get()
        exclude_ambiguous = self.exclude_ambiguous_var.get()
        count = self.count_var.get()
        
        if not (use_lowers or use_uppers or use_digits or use_specials):
            messagebox.showerror("Ошибка", "Выберите хотя бы один тип символов!")
            return
        
        # Установка параметров и генерация
        self.generator.set_params(length, use_lowers, use_uppers, use_digits, use_specials, exclude_ambiguous)
        passwords = self.generator.generate_multiple(count)
        
        if not passwords:
            messagebox.showerror("Ошибка", "Не удалось сгенерировать пароли. Проверьте настройки.")
            return
        
        # Отображение
        self.output_text.delete(1.0, tk.END)
        for i, pwd in enumerate(passwords, 1):
            self.output_text.insert(tk.END, f"{i}: {pwd}\n")
        
        self.last_password = passwords[0]  # для копирования
        self.status_var.set(f"Сгенерировано {count} паролей. Длина: {length}")
        self.copy_btn.config(text="Копировать первый пароль")
    
    def copy_to_clipboard(self):
        """Копирует первый сгенерированный пароль в буфер обмена"""
        if not hasattr(self, 'last_password') or not self.last_password:
            self.status_var.set("Нет паролей для копирования. Сначала сгенерируйте.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.last_password)
        self.root.update()  # важно для сохранения в буфере
        self.status_var.set(f"Пароль '{self.last_password}' скопирован в буфер обмена")


def main():
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
