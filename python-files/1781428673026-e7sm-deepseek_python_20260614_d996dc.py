import os
import sys
import time
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

def show_message(title, message, is_error=False):
    """Показывает всплывающее окно (без консоли)"""
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    if is_error:
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)
    root.destroy()

def log(msg):
    """Запись лога в файл рядом с exe"""
    try:
        # Определяем папку, где находится exe (или скрипт)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(base_dir, "launcher.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass  # Не критично

def main():
    # Определяем базовую папку (там, где лежит exe)
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Папка, в которую пользователь должен положить ярлык
    shortcuts_dir = os.path.join(base_dir, "LaunchTarget")

    log("Скрипт запущен")

    # --- Первый запуск: папки нет, создаём и показываем инструкцию ---
    if not os.path.isdir(shortcuts_dir):
        os.makedirs(shortcuts_dir)
        log(f"Создана папка: {shortcuts_dir}")

        # Открываем папку в проводнике, чтобы пользователь сразу мог положить ярлык
        subprocess.run(f'explorer "{shortcuts_dir}"', shell=True)

        show_message(
            "Настройка завершена",
            f"Папка создана:\n{shortcuts_dir}\n\n"
            "Пожалуйста, положите в неё ярлык (.lnk) нужной программы.\n"
            "После этого перезапустите программу."
        )
        log("Первый запуск: папка создана, ожидание ярлыка")
        return  # Завершаем, ничего не убиваем и не запускаем

    # --- Последующие запуски: папка существует, ищем ярлык ---
    # Ищем первый файл с расширением .lnk в папке shortcuts_dir
    lnk_files = list(Path(shortcuts_dir).glob("*.lnk"))

    if not lnk_files:
        log("Ошибка: в папке LaunchTarget нет ни одного ярлыка .lnk")
        show_message(
            "Ошибка",
            f"В папке\n{shortcuts_dir}\nне найден ярлык (.lnk).\n"
            "Положите ярлык программы и перезапустите.",
            is_error=True
        )
        return

    # Берём первый найденный ярлык
    shortcut_path = str(lnk_files[0])
    log(f"Найден ярлык: {shortcut_path}")

    # Ждём 5 секунд перед убийством explorer.exe
    log("Ожидание 5 секунд...")
    time.sleep(5)

    # Убиваем explorer.exe
    try:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"],
                       capture_output=True, check=False)
        log("explorer.exe успешно завершён")
    except Exception as e:
        log(f"Ошибка при завершении explorer.exe: {e}")

    # Запускаем программу по ярлыку
    try:
        # os.startfile умеет запускать .lnk как ярлык
        os.startfile(shortcut_path)
        log(f"Программа запущена через ярлык: {shortcut_path}")
    except Exception as e:
        log(f"Ошибка запуска программы: {e}")
        show_message(
            "Ошибка запуска",
            f"Не удалось запустить программу по ярлыку:\n{shortcut_path}\n\n{e}",
            is_error=True
        )

if __name__ == "__main__":
    main()