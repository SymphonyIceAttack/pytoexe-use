import tkinter as tk
import sys
import os
import shutil
from pathlib import Path

class FullscreenGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        
        # На весь экран
        self.root.attributes('-fullscreen', True)
        
        # Правильное число - 77
        self.secret_number = 77
        self.attempt_made = False
        
        # Создаем тестовую папку
        self.create_test_folder()
        
        # Настройки внешнего вида
        self.root.configure(bg='black')
        
        # Блокируем все способы закрытия
        self.block_all_closing()
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Окно всегда сверху
        self.root.attributes('-topmost', True)
        
        self.root.mainloop()
    
    def create_test_folder(self):
        """Создаем тестовую папку"""
        try:
            # Путь к папке в той же директории, где запущен скрипт
            self.test_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TEST_FOLDER")
            
            # Удаляем если уже существует
            if os.path.exists(self.test_folder):
                shutil.rmtree(self.test_folder)
            
            # Создаем новую папку
            os.makedirs(self.test_folder)
            
            # Создаем несколько тестовых файлов
            for i in range(1, 4):
                file_path = os.path.join(self.test_folder, f"file_{i}.txt")
                with open(file_path, 'w') as f:
                    f.write(f"Test file {i}")
            
            print(f"[СОЗДАНО] Папка: {self.test_folder}")
            
        except Exception as e:
            print(f"[ОШИБКА] Не удалось создать папку: {e}")
            self.test_folder = None
    
    def delete_test_folder(self):
        """Удаляем тестовую папку"""
        try:
            if self.test_folder and os.path.exists(self.test_folder):
                shutil.rmtree(self.test_folder)
                print(f"[УДАЛЕНО] Папка: {self.test_folder}")
                return True
        except Exception as e:
            print(f"[ОШИБКА] Не удалось удалить папку: {e}")
        return False
    
    def block_all_closing(self):
        """Блокируем все способы закрытия"""
        self.root.protocol("WM_DELETE_WINDOW", self.block_close)
        
        # Блокируем горячие клавиши
        keys = ["<Alt-F4>", "<Control-w>", "<Control-q>", "<Escape>", 
                "<F11>", "<Alt-Tab>", "<Super_L>", "<Super_R>", "<F4>"]
        
        for key in keys:
            self.root.bind(key, self.block_close)
        
        # Блокируем мышь
        self.root.bind("<Button-3>", self.block_close)
        
        # Блокируем функциональные клавиши
        for i in range(1, 13):
            self.root.bind(f"<F{i}>", self.block_close)
    
    def block_close(self, event=None):
        return "break"
    
    def create_widgets(self):
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Заголовок
        title = tk.Label(
            main_frame,
            text="ВЫБЕРИ ЧИСЛО",
            font=("Arial", 48, "bold"),
            fg="red",
            bg="black"
        )
        title.pack(pady=30)
        
        # Инструкция
        instruction = tk.Label(
            main_frame,
            text="Введи число от 1 до 100:",
            font=("Arial", 24),
            fg="red",
            bg="black"
        )
        instruction.pack(pady=30)
        
        # Поле ввода
        self.entry = tk.Entry(
            main_frame,
            font=("Arial", 32),
            width=6,
            justify="center",
            bg="black",
            fg="red",
            insertbackground="red",
            relief="solid",
            bd=3
        )
        self.entry.pack(pady=30)
        self.entry.focus()
        
        # Кнопка
        self.button = tk.Button(
            main_frame,
            text="ПРОВЕРИТЬ",
            font=("Arial", 24, "bold"),
            bg="black",
            fg="red",
            activebackground="darkred",
            activeforeground="white",
            padx=50,
            pady=20,
            command=self.confirm_choice,
            relief="solid",
            bd=3
        )
        self.button.pack(pady=30)
        
        # Enter
        self.root.bind("<Return>", lambda event: self.confirm_choice())
        
        # Предупреждение
        warning = tk.Label(
            self.root,
            text="⚠️ ТОЛЬКО ОДНА ПОПЫТКА ⚠️",
            font=("Arial", 18, "bold"),
            fg="red",
            bg="black"
        )
        warning.place(relx=0.5, rely=0.85, anchor='center')
    
    def confirm_choice(self):
        """Подтверждение выбора"""
        
        if self.attempt_made:
            return
        
        number_text = self.entry.get().strip()
        if not number_text:
            return
        
        try:
            number = int(number_text)
            
            if number < 1 or number > 100:
                self.show_error("Число должно быть от 1 до 100!")
                return
            
            self.show_confirmation(number)
            
        except ValueError:
            self.show_error("Это не число!")
    
    def show_error(self, message):
        """Показываем ошибку ввода"""
        error = tk.Toplevel(self.root)
        error.title("")
        error.configure(bg='black')
        error.attributes('-topmost', True)
        
        # Центрируем
        w, h = 400, 200
        x = (error.winfo_screenwidth() - w) // 2
        y = (error.winfo_screenheight() - h) // 2
        error.geometry(f"{w}x{h}+{x}+{y}")
        
        tk.Label(
            error,
            text=message,
            font=("Arial", 14),
            fg="red",
            bg="black",
            wraplength=350
        ).pack(expand=True)
        
        error.after(1500, error.destroy)
    
    def show_confirmation(self, number):
        """Диалог подтверждения"""
        
        confirm = tk.Toplevel(self.root)
        confirm.title("")
        confirm.configure(bg='black')
        confirm.attributes('-topmost', True)
        
        # Нельзя закрыть
        confirm.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Размер и положение
        w, h = 500, 250
        x = (confirm.winfo_screenwidth() - w) // 2
        y = (confirm.winfo_screenheight() - h) // 2
        confirm.geometry(f"{w}x{h}+{x}+{y}")
        
        confirm.resizable(False, False)
        
        # Текст (без числа)
        question = tk.Label(
            confirm,
            text="Ты уверен в своем выборе?",
            font=("Arial", 20, "bold"),
            fg="red",
            bg="black"
        )
        question.pack(pady=40)
        
        # Предупреждение
        warning = tk.Label(
            confirm,
            text="Это твоя единственная попытка!",
            font=("Arial", 14),
            fg="darkred",
            bg="black"
        )
        warning.pack(pady=10)
        
        # Кнопка ДА
        yes_button = tk.Button(
            confirm,
            text="ДА",
            font=("Arial", 18, "bold"),
            bg="black",
            fg="red",
            activebackground="darkred",
            activeforeground="white",
            padx=60,
            pady=10,
            command=lambda: self.check_number(number, confirm),
            relief="solid",
            bd=3
        )
        yes_button.pack(pady=20)
        
        # Enter на кнопку ДА
        confirm.bind("<Return>", lambda event: self.check_number(number, confirm))
        
        confirm.grab_set()
        confirm.focus()
    
    def check_number(self, number, confirm_window):
        """Проверка числа"""
        
        self.attempt_made = True
        confirm_window.destroy()
        
        if number == self.secret_number:  # 77
            self.show_victory()
        else:
            self.show_defeat()
    
    def show_victory(self):
        """Победа"""
        victory = tk.Toplevel(self.root)
        victory.title("")
        victory.configure(bg='black')
        victory.attributes('-topmost', True)
        
        victory.protocol("WM_DELETE_WINDOW", lambda: None)
        
        w, h = 450, 250
        x = (victory.winfo_screenwidth() - w) // 2
        y = (victory.winfo_screenheight() - h) // 2
        victory.geometry(f"{w}x{h}+{x}+{y}")
        
        victory.resizable(False, False)
        
        tk.Label(
            victory,
            text="🎉 ПОБЕДА! 🎉",
            font=("Arial", 30, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=50)
        
        tk.Label(
            victory,
            text="Выход...",
            font=("Arial", 14),
            fg="red",
            bg="black"
        ).pack()
        
        victory.after(2000, self.exit_game)
        victory.grab_set()
    
    def show_defeat(self):
        """Поражение - удаляем папку"""
        
        # Удаляем папку
        deleted = self.delete_test_folder()
        
        defeat = tk.Toplevel(self.root)
        defeat.title("")
        defeat.configure(bg='black')
        defeat.attributes('-topmost', True)
        
        defeat.protocol("WM_DELETE_WINDOW", lambda: None)
        
        w, h = 450, 300
        x = (defeat.winfo_screenwidth() - w) // 2
        y = (defeat.winfo_screenheight() - h) // 2
        defeat.geometry(f"{w}x{h}+{x}+{y}")
        
        defeat.resizable(False, False)
        
        tk.Label(
            defeat,
            text="❌ ОШИБКА ❌",
            font=("Arial", 30, "bold"),
            fg="red",
            bg="black"
        ).pack(pady=40)
        
        if deleted:
            tk.Label(
                defeat,
                text="Папка System32 УДАЛЕНА!",
                font=("Arial", 16, "bold"),
                fg="red",
                bg="black"
            ).pack(pady=20)
        else:
            tk.Label(
                defeat,
                text="Не удалось удалить папку",
                font=("Arial", 16),
                fg="darkred",
                bg="black"
            ).pack(pady=20)
        
        tk.Label(
            defeat,
            text="Выход...",
            font=("Arial", 14),
            fg="red",
            bg="black"
        ).pack(pady=10)
        
        defeat.after(3000, self.exit_game)
        defeat.grab_set()
    
    def exit_game(self):
        """Выход"""
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    print("=" * 50)
    print("ЗАПУСК ПРОГРАММЫ")
    print("=" * 50)
    print("📁 Создается тестовая папка")
    print("🎯 Попробуй угадать число 77")
    print("⚠️  При ошибке папка будет удалена")
    print("=" * 50)
    
    app = FullscreenGame()