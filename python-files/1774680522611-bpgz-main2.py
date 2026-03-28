import tkinter as tk  
from tkinter import messagebox, simpledialog, Listbox, Scrollbar, colorchooser  
import webbrowser  
import platform  
import os

# Глобальная переменная для хранения цвета фона  
bg_color = "white"

# Функция для открытия Проводника  
def open_explorer():
    explorer_window = tk.Toplevel(root)
    explorer_window.title("Проводник")
    explorer_window.geometry("600x400")
    explorer_window.config(bg=bg_color)  # Устанавливаем цвет фона

    # Функция для обновления списка файлов  
    def update_file_list():
        file_list.delete(0, tk.END)
        for item in os.listdir(os.getcwd()):
            file_list.insert(tk.END, item)

    # Функция для создания файла  
    def create_file():
        filename = simpledialog.askstring("Создать файл", "Введите имя файла (с расширением):")
        if filename:
            with open(filename, 'w') as f:
                f.write("")
            messagebox.showinfo("Создать файл", f"Файл '{filename}' был создан!")
            update_file_list()

    # Функция для удаления файла  
    def delete_file():
        selected_file = file_list.curselection()
        if selected_file:
            filename = file_list.get(selected_file)
            os.remove(filename)
            messagebox.showinfo("Удалить файл", f"Файл '{filename}' был удален!")
            update_file_list()
        else:
            messagebox.showwarning("Удалить файл", "Выберите файл для удаления.")

    # Функция для переименования файла  
    def rename_file():
        selected_file = file_list.curselection()
        if selected_file:
            old_filename = file_list.get(selected_file)
            new_filename = simpledialog.askstring("Переименовать файл", "Введите новое имя файла (с расширением):")
            if new_filename:
                os.rename(old_filename, new_filename)
                messagebox.showinfo("Переименовать файл", f"Файл '{old_filename}' переименован в '{new_filename}'!")
                update_file_list()
        else:
            messagebox.showwarning("Переименовать файл", "Выберите файл для переименования.")

    create_button = tk.Button(explorer_window, text="Создать файл", command=create_file)
    create_button.pack(pady=10)

    delete_button = tk.Button(explorer_window, text="Удалить файл", command=delete_file)
    delete_button.pack(pady=5)

    rename_button = tk.Button(explorer_window, text="Переименовать файл", command=rename_file)
    rename_button.pack(pady=5)

    file_list = Listbox(explorer_window, width=50, height=15)
    file_list.pack(pady=20)

    scrollbar = Scrollbar(explorer_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    file_list.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=file_list.yview)

    update_file_list()

# Функция для открытия Настроек  
def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Настройки")
    settings_window.geometry("600x400")
    settings_window.config(bg=bg_color)  # Устанавливаем цвет фона

    system_info = f"Версия Python: {platform.python_version()}\n" \
                  f"Система: {platform.system()} {platform.release()}\n" \
                  f"Платформа: {platform.platform()}"
    
    label = tk.Label(settings_window, text="Информация о системе", font=("Arial", 16), bg=bg_color)
    label.pack(pady=20)

    info_label = tk.Label(settings_window, text=system_info, font=("Arial", 12), justify="left", bg=bg_color)
    info_label.pack(pady=10)

    # Функция для изменения цвета фона  
    def change_bg_color():
        global bg_color  
        color = colorchooser.askcolor()[1]
        if color:
            bg_color = color  
            settings_window.config(bg=bg_color)
            info_label.config(bg=bg_color)
            update_explorer_windows_color()  # Обновляем цвет всех окон проводника

    # Кнопка для изменения цвета фона  
    personalize_button = tk.Button(settings_window, text="Персонализация", command=change_bg_color)
    personalize_button.pack(pady=10)

# Функция для обновления цвета всех открытых окон проводника  
def update_explorer_windows_color():
    for window in root.winfo_children():
        if isinstance(window, tk.Toplevel):
            window.config(bg=bg_color)
            for widget in window.winfo_children():
                widget.config(bg=bg_color)

# Функция для открытия Браузера  
def open_browser():
    webbrowser.open('http://www.google.com')

# Основное окно  
root = tk.Tk()
root.title("Windows 12")
root.geometry("800x600")
root.config(bg=bg_color)  # Устанавливаем цвет фона

# Создаем панель задач  
taskbar = tk.Frame(root, bg='lightgrey', height=40)
taskbar.pack(side=tk.BOTTOM, fill=tk.X)

# Создаем рабочий стол  
desktop_frame = tk.Frame(root, bg=bg_color)
desktop_frame.pack(expand=True, fill=tk.BOTH)

# Добавляем кнопки на рабочий стол  
explorer_button = tk.Button(desktop_frame, text="Проводник", command=open_explorer, width=20)
explorer_button.pack(pady=20)

settings_button = tk.Button(desktop_frame, text="Настройки", command=open_settings, width=20)
settings_button.pack(pady=10)

browser_button = tk.Button(desktop_frame, text="Браузер", command=open_browser, width=20)
browser_button.pack(pady=10)

# Основное содержимое окна  
label = tk.Label(desktop_frame, text="Добро пожаловать в Windows 12", font=("Arial", 24), bg=bg_color)
label.pack(pady=20)

# Запуск основного цикла  
root.mainloop()