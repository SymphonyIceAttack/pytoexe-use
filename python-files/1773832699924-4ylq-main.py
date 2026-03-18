#!/usr/bin/env python3
"""
WINLOCKER - Блокировка экрана (только визуальная)
Приложения остаются поверх
В диспетчере задач: winl.exe
Запуск: python winl.py
Выход: найти процесс winl.exe в диспетчере и завершить
"""

import tkinter as tk
import sys
import os
import platform

# Проверка Windows
if platform.system() != "Windows":
    print("❌ Этот скрипт работает только на Windows")
    print("Но для демонстрации мы всё равно покажем окно")
    # Не выходим, просто покажем окно


class WinLocker:
    def __init__(self):
        self.root = tk.Tk()

        # Меняем название процесса (только в заголовке)
        self.root.title("winl.exe - системный процесс")

        # Настройки окна - теперь НЕ поверх всех
        self.root.attributes('-fullscreen', True)  # Полный экран
        self.root.attributes('-topmost', False)  # НЕ поверх других окон!
        self.root.configure(bg='black')

        # Делаем окно полупрозрачным, чтобы видеть другие приложения
        self.root.attributes('-alpha', 0.85)  # 85% непрозрачности

        # Убираем рамку окна
        self.root.overrideredirect(True)

        # Перехватываем только некоторые клавиши
        self.root.bind('<Escape>', self.minimize_window)  # Escape сворачивает
        self.root.bind('<Alt-F4>', self.block_key)  # Alt+F4 блокируем
        self.root.bind('<Control-Alt-Delete>', self.show_instructions)  # Ctrl+Alt+Del

        # Создаём интерфейс
        self.create_ui()

    def create_ui(self):
        """Создаёт интерфейс блокировки (полупрозрачный)"""

        # Главный текст (слева сверху)
        main_label = tk.Label(
            self.root,
            text="⚠️ ВИНЛОКЕР АКТИВЕН ⚠️",
            font=("Arial", 24, "bold"),
            fg="red",
            bg="black"
        )
        main_label.place(x=20, y=20)

        # Инструкция по выходу
        exit_label = tk.Label(
            self.root,
            text="Диспетчер задач (Ctrl+Shift+Esc) → завершить процесс winl.exe",
            font=("Arial", 14),
            fg="yellow",
            bg="black"
        )
        exit_label.place(x=20, y=70)

        # Таймер работы (для красоты)
        self.time_label = tk.Label(
            self.root,
            text="Время блокировки: 0 сек",
            font=("Arial", 12),
            fg="lightblue",
            bg="black"
        )
        self.time_label.place(x=20, y=120)

        # Запускаем обновление таймера
        self.seconds = 0
        self.update_timer()

    def update_timer(self):
        """Обновляет таймер"""
        self.seconds += 1
        self.time_label.config(text=f"Время блокировки: {self.seconds} сек")
        self.root.after(1000, self.update_timer)

    def minimize_window(self, event=None):
        """Сворачивает окно по Escape"""
        self.root.iconify()  # Сворачиваем в панель задач
        return "break"

    def block_key(self, event=None):
        """Блокирует опасные комбинации"""
        return "break"

    def show_instructions(self, event=None):
        """Показывает подсказку при Ctrl+Alt+Del"""
        # Создаём временное окно с подсказкой
        popup = tk.Toplevel(self.root)
        popup.title("Подсказка")
        popup.geometry("400x200")
        popup.attributes('-topmost', True)

        label = tk.Label(
            popup,
            text="Для выхода из винлокера:\n\n"
                 "1. Нажмите Ctrl+Shift+Esc\n"
                 "2. Найдите процесс winl.exe\n"
                 "3. Нажмите 'Снять задачу'",
            font=("Arial", 12),
            justify=tk.LEFT
        )
        label.pack(padx=20, pady=20)

        button = tk.Button(popup, text="OK", command=popup.destroy)
        button.pack(pady=10)

        # Закрыть через 5 секунд
        popup.after(5000, popup.destroy)

    def run(self):
        """Запуск"""
        print("\n" + "=" * 60)
        print("🔒 WINLOCKER ЗАПУЩЕН")
        print("=" * 60)
        print("📌 Приложения сверху - окно только фон")
        print("📌 Имя процесса: winl.exe")
        print("📌 Escape - свернуть в трей")
        print("📌 Выход: Диспетчер задач → завершить winl.exe")
        print("=" * 60)
        print("Ctrl+Shift+Esc - открыть диспетчер")
        print("=" * 60)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n✅ Выход")
            sys.exit(0)


if __name__ == "__main__":
    # Создаем .bat файл для переименования процесса (не обязательно)
    if platform.system() == "Windows" and not os.path.exists("winl.bat"):
        with open("winl.bat", "w") as f:
            f.write("@echo off\n")
            f.write("title winl.exe\n")
            f.write("python winl.py\n")
            f.write("pause\n")
        print("✅ Создан файл winl.bat - запускайте его для имени winl.exe")

    # Запускаем
    locker = WinLocker()
    locker.run()