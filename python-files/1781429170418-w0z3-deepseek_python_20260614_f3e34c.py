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
    root.withdraw()
    if is_error:
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)
    root.destroy()

def log(msg):
    """Запись лога в файл рядом с exe"""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(base_dir, "launcher.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass

def wait_with_cancel(seconds):
    """
    Показывает маленькое окно с таймером и возможностью отмены по ESC.
    Возвращает True, если пользователь нажал ESC (отмена), иначе False.
    """
    canceled = False
    root = tk.Tk()
    root.title("Автозапуск")
    root.geometry("300x100")
    root.resizable(False, False)
    # Окно поверх всех окон
    root.attributes("-topmost", True)
    # Центрируем окно
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (150)
    y = (root.winfo_screenheight() // 2) - (50)
    root.geometry(f"300x100+{x}+{y}")

    label = tk.Label(root, text=f"Автозапуск через {seconds} сек.\nНажмите ESC для отмены", font=("Arial", 10))
    label.pack(expand=True)

    def on_escape(event=None):
        nonlocal canceled
        canceled = True
        root.destroy()

    root.bind("<Escape>", on_escape)

    # Обновляем таймер каждую секунду
    def update_counter(remaining):
        if remaining <= 0 or canceled:
            root.destroy()
            return
        label.config(text=f"Автозапуск через {remaining} сек.\nНажмите ESC для отмены")
        root.after(1000, update_counter, remaining - 1)

    root.after(1000, update_counter, seconds - 1)
    root.mainloop()
    return canceled

def main():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    shortcuts_dir = os.path.join(base_dir, "LaunchTarget")
    log("Скрипт запущен")

    # --- Первый запуск: создаём папку с инструкцией ---
    if not os.path.isdir(shortcuts_dir):
        os.makedirs(shortcuts_dir)
        log(f"Создана папка: {shortcuts_dir}")
        subprocess.run(f'explorer "{shortcuts_dir}"', shell=True)
        show_message(
            "Настройка",
            f"Папка создана:\n{shortcuts_dir}\n\n"
            "Положите в неё ярлык (.lnk) нужной программы.\n"
            "После этого перезапустите программу."
        )
        return

    # --- Поиск ярлыка ---
    lnk_files = list(Path(shortcuts_dir).glob("*.lnk"))
    if not lnk_files:
        log("Ошибка: в папке LaunchTarget нет ярлыка .lnk")
        show_message(
            "Ошибка",
            f"В папке\n{shortcuts_dir}\nне найден ярлык (.lnk).\n"
            "Положите ярлык программы и перезапустите.",
            is_error=True
        )
        return

    shortcut_path = str(lnk_files[0])
    log(f"Найден ярлык: {shortcut_path}")

    # --- Ожидание 5 секунд с возможностью отмены по ESC ---
    log("Ожидание 5 секунд, можно отменить нажатием ESC...")
    if wait_with_cancel(5):
        log("Действие отменено пользователем (ESC)")
        return

    # --- Убиваем explorer.exe ---
    try:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"],
                       capture_output=True, check=False)
        log("explorer.exe успешно завершён")
    except Exception as e:
        log(f"Ошибка при завершении explorer.exe: {e}")

    # --- Запускаем программу ---
    try:
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