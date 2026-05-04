import tkinter as tk
from tkinter import scrolledtext, ttk


# === ФУНКЦИИ (все функции должны быть определены ДО создания GUI) ===

def add_echo():
    text_area.insert(tk.END, "echo Введите текст здесь\n")

def add_pause():
    text_area.insert(tk.END, "timeout /t 5\n")

def add_if():
    text_area.insert(tk.END, "if \"%choice%\"==\"1\" (\necho Вы выбрали вариант 1\n) else (\necho Вы выбрали другой вариант\n)\n")

def add_for_loop():
    text_area.insert(tk.END, "for %%i in (1 2 3 4 5) do (\necho Итерация %%i\n)\n")

def add_while_loop():
    text_area.insert(tk.END, ':while_loop\nif "%continue%"=="yes" (\necho Цикл продолжается\ngoto while_loop\n)\n')

def add_set_var():
    text_area.insert(tk.END, "set /p variable=Введите значение:\necho Введённое значение: %variable%\n")

def add_goto():
    text_area.insert(tk.END, "goto label_name\n:label_name\necho Выполнен переход\n")

def add_call():
    text_area.insert(tk.END, "call :subroutine\necho Возврат из подпрограммы\ngoto :eof\n\n:subroutine\necho Выполнение подпрограммы\n")

def add_copy():
    text_area.insert(tk.END, "copy \"source_file.txt\" \"destination_file.txt\"\n")

def add_move():
    text_area.insert(tk.END, "move \"file.txt\" \"new_location\\\"\n")

def add_delete():
    text_area.insert(tk.END, "del \"unnecessary_file.txt\"\n")

def add_mkdir():
    text_area.insert(tk.END, "mkdir \"new_folder\"\n")

def add_rmdir():
    text_area.insert(tk.END, "rmdir \"empty_folder\"\n")

def add_cd():
    text_area.insert(tk.END, "cd \"C:\\Target\\Folder\"\necho Текущая директория: %cd%\n")

def add_dir():
    text_area.insert(tk.END, "dir\n")

def add_start():
    text_area.insert(tk.END, "start notepad.exe\n")


def add_tasklist():
    text_area.insert(tk.END, "tasklist | find \"notepad\"\n")

def add_date_time():
    text_area.insert(tk.END, "echo Текущая дата: %date%\necho Текущее время: %time%\n")

def add_color():
    text_area.insert(tk.END, "color 0A\necho Текст зелёного цвета на чёрном фоне\n")

def add_title():
    text_area.insert(tk.END, "title Мой BAT-скрипт\n")

def add_chcp():
    text_area.insert(tk.END, "chcp 1251\necho Установлена кодировка Windows-1251\n")

def add_comment():
    text_area.insert(tk.END, "rem Это комментарий — он не выполняется\n")

# Функции для расширенных системных команд (перемещены в начало)
def add_ping():
    text_area.insert(tk.END, "ping -n 4 8.8.8.8\necho Проверка соединения с Google DNS\n")

def add_ipconfig():
    text_area.insert(tk.END, "ipconfig /all\npause\n")

def add_systeminfo():
    text_area.insert(tk.END, "systeminfo\npause\n")


def add_ver():
    text_area.insert(tk.END, "ver\necho Версия операционной системы\n")


def add_path():
    text_area.insert(tk.END, "echo Текущий PATH: %PATH%\npause\n")


def add_errorlevel():
    text_area.insert(tk.END, "dir nonexistent_folder\necho Код ошибки: %errorlevel%\nif %errorlevel% neq 0 (echo Произошла ошибка!)\n")

def add_variables():
    text_area.insert(tk.END, "echo Имя пользователя: %username%\necho Компьютер: %computername%\necho Временная папка: %temp%\n")

def add_find():
    text_area.insert(tk.END, 'find /i "error" "logfile.txt"\necho Поиск ошибок в логе\n')


def add_xcopy():
    text_area.insert(tk.END, 'xcopy "source_folder\\*.txt" "destination_folder" /i /s\necho Копирование с подпапками\n')

def add_robocopy():
    text_area.insert(tk.END, 'robocopy "source" "destination" *.txt /s\necho Надёжное копирование файлов\n')


def add_reg():
    text_area.insert(tk.END, 'reg query "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion"\necho Чтение из реестра\n')


def add_wmic():
    text_area.insert(tk.END, 'wmic cpu get name\nwmic os get caption\necho Информация о системе через WMIC\n')


def add_net():
    text_area.insert(tk.END, 'net view\necho Список доступных сетевых ресурсов\n')

def save_bat():
    with open("output.bat", "w", encoding="cp866") as f:
        f.write(text_area.get("1.0", tk.END))
    status.config(text="Файл output.bat сохранён!")

def clear_all():
    text_area.delete("1.0", tk.END)
    status.config(text="Поле очищено")

# Создание главного окна
root = tk.Tk()
root.title("Визуальный редактор bat")
root.geometry("800x600")


# Текстовое поле с прокруткой
text_area = scrolledtext.ScrolledText(root, width=80, height=25, font=("Consolas", 10))
text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)


# Основной фрейм для кнопок
main_frame = ttk.Frame(root)
main_frame.pack(pady=5, fill=tk.X)


# Категории с вкладками
notebook = ttk.Notebook(main_frame)
notebook.pack(fill=tk.BOTH, expand=True, padx=10)

# Вкладка: Вывод и ввод
frame_io = ttk.Frame(notebook)
notebook.add(frame_io, text="Вывод и ввод")
ttk.Button(frame_io, text="Echo (вывод текста)", command=add_echo).grid(row=0, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_io, text="Pause (пауза)", command=add_pause).grid(row=1, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_io, text="Set (ввод переменной)", command=add_set_var).grid(row=2, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_io, text="Comment (комментарий)", command=add_comment).grid(row=3, column=0, padx=5, pady=2, sticky="w")


# Вкладка: Условные операторы и циклы
frame_control = ttk.Frame(notebook)
notebook.add(frame_control, text="Условные операторы и циклы")


ttk.Button(frame_control, text="If-Else (условие)", command=add_if).grid(row=0, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_control, text="For Loop (цикл)", command=add_for_loop).grid(row=1, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_control, text="While Loop (цикл)", command=add_while_loop).grid(row=2, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_control, text="Goto (переход)", command=add_goto).grid(row=3, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_control, text="Call (подпрограмма)", command=add_call).grid(row=4, column=0, padx=5, pady=2, sticky="w")


# Вкладка: Работа с файлами
frame_files = ttk.Frame(notebook)
notebook.add(frame_files, text="Работа с файлами")


ttk.Button(frame_files, text="Copy (копирование)", command=add_copy).grid(row=0, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_files, text="Move (перемещение)", command=add_move).grid(row=1, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_files, text="Delete (удаление)", command=add_delete).grid(row=2, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_files, text="Mkdir (создание папки)", command=add_mkdir).grid(row=3, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_files, text="Rmdir (удаление папки)", command=add_rmdir).grid(row=4, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_files, text="CD (смена директории)", command=add_cd).grid(row=5, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_files, text="Dir (список файлов)", command=add_dir).grid(row=6, column=0, padx=5, pady=2, sticky="w")

# Вкладка: Запуск программ и системные команды
frame_system = ttk.Frame(notebook)
notebook.add(frame_system, text="Запуск программ и системы")


ttk.Button(frame_system, text="Start (запуск программы)", command=add_start).grid(row=0, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_system, text="Tasklist (список процессов)", command=add_tasklist).grid(row=1, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_system, text="Date & Time (дата и время)", command=add_date_time).grid(row=2, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_system, text="Color (цвет консоли)", command=add_color).grid(row=3, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_system, text="Title (заголовок окна)", command=add_title).grid(row=4, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_system, text="Chcp (кодировка)", command=add_chcp).grid(row=5, column=0, padx=5, pady=2, sticky="w")


# Вкладка: Дополнительные команды
frame_advanced = ttk.Frame(notebook)
notebook.add(frame_advanced, text="Дополнительно")


ttk.Button(frame_advanced, text="Exit (выход)", command=lambda: text_area.insert(tk.END, "exit /b\n")).grid(row=0, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced, text="Echo off (скрыть команды)", command=lambda: text_area.insert(tk.END, "@echo off\n")).grid(row=1, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced, text="Setlocal (локальные переменные)", command=lambda: text_area.insert(tk.END, "setlocal enabledelayedexpansion\n")).grid(row=2, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced, text="Shift (сдвиг аргументов)", command=lambda: text_area.insert(tk.END, "shift\necho %1\n")).grid(row=3, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced, text="Choice (выбор пользователя)", command=lambda: text_area.insert(tk.END, "choice /c YN /m \"Продолжить?\"\nif errorlevel 2 (echo Выбран No) else (echo Выбран Yes)\n")).grid(row=4, column=0, padx=5, pady=2, sticky="w")


# Вкладка: Расширенные системные команды
frame_advanced_system = ttk.Frame(notebook)
notebook.add(frame_advanced_system, text="Расширенные системные")


ttk.Button(frame_advanced_system, text="Ping (проверка сети)", command=add_ping).grid(row=0, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Ipconfig (настройки сети)", command=add_ipconfig).grid(row=1, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Systeminfo (информация о системе)", command=add_systeminfo).grid(row=2, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Ver (версия ОС)", command=add_ver).grid(row=3, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Path (переменная PATH)", command=add_path).grid(row=4, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Errorlevel (коды ошибок)", command=add_errorlevel).grid(row=5, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Системные переменные", command=add_variables).grid(row=6, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Find (поиск в файлах)", command=add_find).grid(row=7, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Xcopy (расширенное копирование)", command=add_xcopy).grid(row=8, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Robocopy (надёжное копирование)", command=add_robocopy).grid(row=9, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Reg (работа с реестром)", command=add_reg).grid(row=10, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="WMIC (системная информация)", command=add_wmic).grid(row=11, column=0, padx=5, pady=2, sticky="w")
ttk.Button(frame_advanced_system, text="Net (сетевые команды)", command=add_net).grid(row=12, column=0, padx=5, pady=2, sticky="w")


# Панель управления внизу
control_frame = ttk.Frame(root)
control_frame.pack(pady=5, fill=tk.X)


ttk.Button(control_frame, text="Сохранить .bat", command=save_bat).pack(side=tk.LEFT, padx=10)
ttk.Button(control_frame, text="Очистить всё", command=clear_all).pack(side=tk.LEFT, padx=10)
ttk.Button(control_frame, text="Закрыть", command=root.quit).pack(side=tk.RIGHT, padx=10)

# Статусная строка
status = ttk.Label(root, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
status.pack(side=tk.BOTTOM, fill=tk.X)

# Запуск приложения
root.mainloop()
