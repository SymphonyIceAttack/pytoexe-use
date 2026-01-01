#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==================================================
ВНИМАНИЕ: ЭТО УЧЕБНАЯ ПРОГРАММА!
Назначение: Изучение принципов UI-атак в Windows
Запрещено: Использование вне изолированной среды
Принципы безопасности:
1. Аварийный выход: ESC (удерживать 3 секунды)
2. Авторазблокировка через 60 секунд
3. Не скрывает консоль (для отладки)
==================================================
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import os

class SecureWinLockerLab:
    def __init__(self):
        self.PASSWORD = "1111"  # Фиксированный пароль для лаборатории
        self.ESCAPE_SEQUENCE_TIME = 3  # секунды удержания ESC
        self.AUTO_UNLOCK_TIME = 60     # авторазблокировка
        self.MAX_ATTEMPTS = 5
        
        self.root = None
        self.attempts = 0
        self.escape_pressed_time = 0
        self.start_time = time.time()
        
        print("=" * 50)
        print("УЧЕБНЫЙ БЛОКИРОВЩИК ЭКРАНА")
        print("Только для лабораторных целей!")
        print("=" * 50)
        print(f"\nПравила безопасной работы:")
        print(f"1. Удерживайте ESC {self.ESCAPE_SEQUENCE_TIME} сек. для выхода")
        print(f"2. Авторазблокировка через {self.AUTO_UNLOCK_TIME} сек.")
        print(f"3. Максимум {self.MAX_ATTEMPTS} попыток ввода пароля")

    def create_lock_screen(self):
        """Создает полноэкранное окно блокировки"""
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)  # Полноэкранный режим
        self.root.attributes("-topmost", True)     # Поверх всех окон
        self.root.title("[УЧЕБНЫЙ БЛОКИРОВЩИК]")
        
        # Блокируем закрытие окна
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Полупрозрачный черный фон
        self.root.config(bg='black')
        self.root.attributes("-alpha", 0.95)
        
        # Основной фрейм
        frame = tk.Frame(self.root, bg='black')
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Заголовок
        title = tk.Label(
            frame,
            text="ЭКРАН БЛОКИРОВАН",
            font=('Consolas', 48, 'bold'),
            fg='white',
            bg='black'
        )
        title.pack(pady=20)
        
        # Таймер авторазблокировки
        self.timer_label = tk.Label(
            frame,
            text="",
            font=('Consolas', 24),
            fg='red',
            bg='black'
        )
        self.timer_label.pack(pady=10)
        
        # Пароль поле
        pwd_frame = tk.Frame(frame, bg='black')
        pwd_frame.pack(pady=20)
        
        tk.Label(
            pwd_frame,
            text="Пароль: ",
            font=('Consolas', 24),
            fg='white',
            bg='black'
        ).pack(side=tk.LEFT)
        
        self.pwd_entry = tk.Entry(
            pwd_frame,
            show="*",
            font=('Consolas', 24),
            width=10
        )
        self.pwd_entry.pack(side=tk.LEFT)
        self.pwd_entry.focus()
        
        # Кнопка разблокировки
        btn = tk.Button(
            frame,
            text="Разблокировать",
            command=self.check_password,
            font=('Consolas', 20),
            bg='darkred',
            fg='white',
            padx=20,
            pady=10
        )
        btn.pack(pady=20)
        
        # Статус
        self.status_label = tk.Label(
            frame,
            text="",
            font=('Consolas', 18),
            fg='yellow',
            bg='black'
        )
        self.status_label.pack(pady=10)
        
        # Аварийный выход
        emergency = tk.Label(
            frame,
            text=f"Удерживайте ESC {self.ESCAPE_SEQUENCE_TIME} сек. для аварийного выхода",
            font=('Consolas', 16),
            fg='orange',
            bg='black'
        )
        emergency.pack(pady=5)
        
        # Обрабатываем ввод
        self.root.bind('<Escape>', self.on_escape_press)
        self.root.bind('<KeyRelease-Escape>', self.on_escape_release)
        self.root.bind('<Return>', lambda e: self.check_password())
        
        # Запускаем таймер
        self.update_timer()
        
        # Запускаем блокировку курсора
        self.lock_cursor()
        
        return self.root

    def lock_cursor(self):
        """Блокирует курсор в центре экрана"""
        def cursor_lock():
            while self.root and self.root.winfo_exists():
                # Получаем размеры экрана
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                # Устанавливаем курсор в центр
                # ВНИМАНИЕ: В реальном ПО это вредоносно, в учебном — с аварийным выходом
                # Для безопасности закомментировано по умолчанию
                # try:
                #     import pyautogui
                #     pyautogui.moveTo(screen_width//2, screen_height//2)
                # except ImportError:
                #     pass
                
                time.sleep(0.1)
        
        # Для безопасности курсор НЕ блокируется
        # thread = threading.Thread(target=cursor_lock, daemon=True)
        # thread.start()

    def on_escape_press(self, event):
        """Обработчик нажатия ESC"""
        if self.escape_pressed_time == 0:
            self.escape_pressed_time = time.time()
            print("\n[ESC] Активирован аварийный выход...")

    def on_escape_release(self, event):
        """Обработчик отпускания ESC"""
        current_time = time.time()
        
        if self.escape_pressed_time > 0:
            hold_time = current_time - self.escape_pressed_time
            
            if hold_time >= self.ESCAPE_SEQUENCE_TIME:
                print(f"\n[АВАРИЙНЫЙ ВЫХОД] Длительность: {hold_time:.1f} сек.")
                self.unlock()
            elif hold_time > 0.5:
                print(f"[!] Удерживайте ESC еще {self.ESCAPE_SEQUENCE_TIME - hold_time:.1f} сек.")
        
        self.escape_pressed_time = 0

    def update_timer(self):
        """Обновляет таймер авторазблокировки"""
        elapsed = time.time() - self.start_time
        remaining = self.AUTO_UNLOCK_TIME - elapsed
        
        if remaining > 0:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            self.timer_label.config(
                text=f"Авторазблокировка через: {minutes:02d}:{seconds:02d}",
                fg='red'
            )
            self.root.after(1000, self.update_timer)
        else:
            self.timer_label.config(
                text="[!] СРАБОТАЛА АВТОРАЗБЛОКИРОВКА",
                fg='green'
            )
            print("\n[!] Превышено время ожидания. Авторазблокировка!")
            self.unlock()

    def check_password(self):
        """Проверка пароля"""
        entered = self.pwd_entry.get()
        
        if entered == self.PASSWORD:
            print("\n[✓] Пароль верный. Разблокировка...")
            self.unlock()
        else:
            self.attempts += 1
            remaining = self.MAX_ATTEMPTS - self.attempts
            
            self.status_label.config(
                text=f"✗ Неверно! Осталось попыток: {remaining}",
                fg='red'
            )
            print(f"\n[✗] Ошибка #{self.attempts}. Осталось: {remaining}")
            
            self.pwd_entry.delete(0, tk.END)
            
            if self.attempts >= self.MAX_ATTEMPTS:
                print("\n[!] Превышено количество попыток. Авторазблокировка!")
                self.unlock()

    def unlock(self):
        """Безопасное снятие блокировки"""
        print("\n" + "=" * 50)
        print("БЛОКИРОВКА СНЯТА")
        print("=" * 50)
        
        if self.root:
            self.root.destroy()
            self.root = None

def main():
    """Главная функция с предварительными проверками"""
    
    # Проверка окружения
    if not sys.platform.startswith('win'):
        print("ОШИБКА: Эта программа только для Windows!")
        return
    
    # Предупреждение
    print("\n" + "!" * 50)
    print("ЗАПУСК УЧЕБНОГО БЛОКИРОВЩИКА")
    print("!" * 50)
    
    confirmation = input("\nДля подтверждения запуска введите 'start': ")
    
    if confirmation.lower() != 'start':
        print("Запуск отменен.")
        return
    
    try:
        locker = SecureWinLockerLab()
        root = locker.create_lock_screen()
        root.mainloop()
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
    finally:
        # Гарантируем разблокировку
        locker.unlock()

    # Учебные вопросы
    print("\n" + "=" * 50)
    print("ВОПРОСЫ ДЛЯ РАЗМЫШЛЕНИЯ:")
    print("1. Какие Windows API используются для блокировки?")
    print("2. Почему важен аварийный выход (ESC)?")
    print("3. Как антивирус может обнаружить такое ПО?")
    print("4. Что такое WS_EX_TOPMOST и зачем оно здесь?")
    print("5. Как защититься от реальных атак такого типа?")
    print("=" * 50)

if __name__ == "__main__":
    # Для образовательных целей требуется явный запуск
    main()