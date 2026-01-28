import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys

# Функция для открытия командной строки
def open_cmd():
    try:
        # 'start' используется для открытия в новом окне на Windows
        subprocess.run('start cmd', shell=True)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть CMD: {e}")

# Функция для открытия реестра
def open_registry():
    try:
        # Требует прав администратора для внесения изменений, но откроется и так
        subprocess.Popen('regedit')
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось открыть реестр: {e}")

# Функция-заглушка для имитации сканирования
def scan_system():
    # Здесь могла бы быть логика проверки хэшей файлов
    messagebox.showinfo("Сканирование", "Быстрое сканирование системы завершено.\nУгроз не обнаружено (Демо-режим).")

# Настройка главного окна
root = tk.Tk()
root.title("My Custom Antivirus Tool")
root.geometry("400x300")
root.configure(bg="#f0f0f0")

# Заголовок
label = tk.Label(root, text="Системная Защита", font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#333")
label.pack(pady=20)

# Кнопка для CMD
btn_cmd = tk.Button(root, text="Открыть CMD", command=open_cmd, width=20, height=2, bg="#0078D7", fg="white")
btn_cmd.pack(pady=5)

# Кнопка для Реестра
btn_reg = tk.Button(root, text="Открыть Реестр (Regedit)", command=open_registry, width=20, height=2, bg="#0078D7", fg="white")
btn_reg.pack(pady=5)

# Кнопка Сканирования
btn_scan = tk.Button(root, text="Сканировать систему", command=scan_system, width=20, height=2, bg="#28a745", fg="white")
btn_scan.pack(pady=20)

# Запуск основного цикла приложения
root.mainloop()