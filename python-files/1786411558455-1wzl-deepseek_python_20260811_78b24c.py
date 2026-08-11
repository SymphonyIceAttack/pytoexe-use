import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import os

class WinLocker:
    def __init__(self):
        # Скрываем консольное окно (если запущено как .py)
        if sys.platform == 'win32':
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        self.window = tk.Tk()
        self.window.title("Винлокер - Розыгрыш!")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        
        # Делаем окно поверх всех окон
        self.window.attributes('-topmost', True)
        
        # На весь экран (F11 эффект)
        self.window.attributes('-fullscreen', True)
        
        # Запрещаем закрытие через Alt+F4 и крестик
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)
        self.window.bind('<Alt-F4>', lambda e: "break")
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Блокируем клавиши Windows и Alt+Tab
        self.block_keys()
        
    def block_keys(self):
        # Блокируем системные комбинации
        self.window.bind('<Control-Alt-Delete>', lambda e: "break")
        self.window.bind('<Control-Alt-Escape>', lambda e: "break")
        self.window.bind('<Alt-Tab>', lambda e: "break")
        self.window.bind('<Win_L>', lambda e: "break")
        self.window.bind('<Win_R>', lambda e: "break")
        
    def create_widgets(self):
        # Фон
        self.window.configure(bg='#2c3e50')
        
        # Заголовок
        title = tk.Label(
            self.window,
            text="🔒 СИСТЕМА ЗАБЛОКИРОВАНА 🔒",
            font=('Arial', 24, 'bold'),
            fg='#e74c3c',
            bg='#2c3e50'
        )
        title.pack(pady=50)
        
        # Подзаголовок
        sub = tk.Label(
            self.window,
            text="Введите пароль для разблокировки:",
            font=('Arial', 14),
            fg='white',
            bg='#2c3e50'
        )
        sub.pack(pady=10)
        
        # Поле для ввода пароля
        self.password_entry = tk.Entry(
            self.window,
            font=('Arial', 18),
            show='●',
            width=20,
            justify='center'
        )
        self.password_entry.pack(pady=20)
        self.password_entry.focus()
        
        # Кнопка разблокировки
        unlock_btn = tk.Button(
            self.window,
            text="РАЗБЛОКИРОВАТЬ",
            font=('Arial', 14, 'bold'),
            bg='#27ae60',
            fg='white',
            width=20,
            height=2,
            command=self.check_password,
            relief='ridge',
            cursor='hand2'
        )
        unlock_btn.pack(pady=20)
        
        # Привязываем Enter к проверке
        self.window.bind('<Return>', lambda e: self.check_password())
        
        # Шутливое сообщение
        joke = tk.Label(
            self.window,
            text="💀 Попробуй угадай! Подсказка: 1...2...3...4...",
            font=('Arial', 12, 'italic'),
            fg='#f1c40f',
            bg='#2c3e50'
        )
        joke.pack(pady=30)
        
        # Показываем количество попыток
        self.attempts = 0
        self.attempt_label = tk.Label(
            self.window,
            text="Попыток: 0",
            font=('Arial', 10),
            fg='#95a5a6',
            bg='#2c3e50'
        )
        self.attempt_label.pack(pady=10)
        
    def check_password(self):
        password = self.password_entry.get()
        self.attempts += 1
        self.attempt_label.config(text=f"Попыток: {self.attempts}")
        
        if password == "1234":
            # Правильный пароль - разблокируем
            messagebox.showinfo(
                "🎉 Успех!",
                "Ты угадал! Это была шутка! 😄\n\nНаслаждайся своим рабочим столом!"
            )
            self.window.destroy()
            sys.exit()
        else:
            # Неправильный пароль - мигаем и ругаемся
            self.window.configure(bg='#c0392b')
            self.window.after(200, lambda: self.window.configure(bg='#2c3e50'))
            
            if self.attempts >= 5:
                messagebox.showwarning(
                    "😈 Не угадал!",
                    "Ха-ха! Ты не угадал! \n\nПодсказка: это самое простое число... 1-2-3-4!"
                )
            elif self.attempts >= 10:
                messagebox.showerror(
                    "🤡 Ну ты и тупой!",
                    "Серьёзно? 10 попыток, а ты всё ещё не угадал? \n\nПАРОЛЬ: 1234 (надеюсь, теперь запомнишь!)"
                )
            else:
                messagebox.showerror(
                    "❌ Неверный пароль!",
                    f"Попробуй ещё раз! (Попытка {self.attempts})"
                )
            
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

if __name__ == "__main__":
    # Проверяем, что запущено на Windows
    if sys.platform == 'win32':
        app = WinLocker()
        app.window.mainloop()
    else:
        print("Этот скрипт работает только на Windows!")
        input("Нажмите Enter для выхода...")