import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import webbrowser
import os  # Импортируем модуль os для работы с файловой системой
import shutil  # Импортируем модуль shutil для удаления папок и файлов

# Создаем главное окно
window = tk.Tk()

window.title("Diagnostics tool")
window.geometry("500x700")
window.resizable(width=False, height=False)


window.configure(bg="black")  # или window.config(bg="black")

notebook = ttk.Notebook(window)
notebook.pack(pady=10, padx=10, fill="both", expand=True)

tab1 = tk.Frame(notebook, bg="black")
notebook.add(tab1, text="Boot")

tab2 = tk.Frame(notebook, bg="black")
notebook.add(tab2, text="Links")



def open_disk_management():
    """Открывает управление дисками."""
    try:
        # Для Windows:  запускаем управление дисками через командную строку
        subprocess.Popen(["diskmgmt.msc"])
    except FileNotFoundError:
        print("Ошибка: Не удалось найти diskmgmt.msc.  Управление дисками не может быть открыто.")
    except Exception as e:
        print(f"Произошла ошибка при открытии управления дисками: {e}")


def open_computer_management():
    """Открывает управление компьютером."""
    try:
        # Для Windows:  запускаем управление компьютером через командную строку
        subprocess.Popen(["compmgmt.msc"])
    except FileNotFoundError:
        print("Ошибка: Не удалось найти compmgmt.msc. Управление компьютером не может быть открыто.")
    except Exception as e:
        print(f"Произошла ошибка при открытии управления компьютером: {e}")


def open_system_configuration():
    """Открывает конфигурацию системы."""
    try:
        # Для Windows:  запускаем конфигурацию системы через командную строку
        subprocess.Popen(["msconfig"])
    except FileNotFoundError:
        print("Ошибка: Не удалось найти msconfig. Конфигурация системы не может быть открыта.")
    except Exception as e:
        print(f"Произошла ошибка при открытии конфигурации системы: {e}")


def show_notification():
    """Авто-Рекомендации"""
    messagebox.showinfo("POSS", "p.o.s.s end 1,2s                                                                                os health - 45%/100;                                                             options usable - 13%/100;                                                           optimiz - 4%/100;       ")


# Функция для удаления программы
def uninstall_program():
    """Удаляет программу (удаляет файлы и, возможно, записи в реестре)."""
    if messagebox.askyesno("Удаление", "Вы уверены, что хотите полностью удалить программу? Это действие необратимо."):
        try:
            # 1. Удаление файлов программы (предполагаем, что программа находится в текущей директории или рядом)
            # Замените 'program_directory' на фактический путь к каталогу вашей программы, если он отличается
            program_directory = os.getcwd()  # Текущая директория (где находится скрипт)
            try:
                shutil.rmtree(program_directory)  # Удаляем папку и все ее содержимое (опасно, если программа не в отдельной папке!)
                messagebox.showinfo("Удаление", "Файлы программы успешно удалены.")
            except OSError as e:
                messagebox.showerror("Ошибка удаления", f"Не удалось удалить файлы программы: {e}")
            # 2. Удаление записей из реестра (требует прав администратора и более сложной логики)
            #  Реализация удаления записей из реестра выходит за рамки этого примера и требует дополнительных библиотек
            #  и прав.  Обычно это делается через установщик/деинсталлятор.
            # 3. Дополнительные действия (например, удаление ярлыков)
            #  Это также зависит от структуры вашей программы.

            messagebox.showinfo("Удаление", "Удаление завершено.  Необходимо перезагрузить компьютер для завершения.")
            #  Можно добавить код для перезагрузки компьютера (требует прав администратора)
            #  subprocess.call(["shutdown", "/r", "/t", "0"]) # Перезагрузка Windows
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при удалении: {e}")



# Создаем кнопку во вкладке 1 для открытия управления дисками
disk_management_button = tk.Button(tab1, text="Открыть управление дисками", command=open_disk_management, fg="white", bg="darkgray")
disk_management_button.pack(pady=10) # Добавляем отступ сверху

# Создаем кнопку во вкладке 1 для открытия управления компьютером
computer_management_button = tk.Button(tab1, text="Открыть управление компьютером", command=open_computer_management, fg="white", bg="darkgray")
computer_management_button.pack(pady=10) # Добавляем отступ сверху

# Создаем кнопку во вкладке 1 для открытия конфигурации системы
system_configuration_button = tk.Button(tab1, text="Открыть конфигурацию системы", command=open_system_configuration, fg="white", bg="darkgray")
system_configuration_button.pack(pady=10) # Добавляем отступ сверху

# Добавляем кнопку для показа уведомления
notification_button = tk.Button(tab1, text="POSS AUTO", command=show_notification, fg="white", bg="darkgray")
notification_button.pack(pady=10) # Добавляем отступ сверху

# Добавляем кнопку для удаления программы
uninstall_button = tk.Button(tab1, text="Удалить программу", command=uninstall_program, fg="white", bg="darkgray")
uninstall_button.pack(pady=10)


# Функция для открытия ссылки в браузере Dr.Web
def open_drweb_link():
    """Открывает ссылку https://free.drweb.ru/download+cureit+free/?ph=0f3522ae64a80d12b7d9b559870b5bd4 в браузере."""
    webbrowser.open_new("https://free.drweb.ru/download+cureit+free/?ph=0f3522ae64a80d12b7d9b559870b5bd4")


# Функция для открытия ссылки в браузере FurMark
def open_furmark_link():
    """Открывает ссылку https://geeks3d.com/furmark/downloads/ в браузере."""
    webbrowser.open_new("https://geeks3d.com/furmark/downloads/")

# Функция для открытия ссылки в браузере CrystalMark3D
def open_crystalmark_link():
    """Открывает ссылку https://sourceforge.net/projects/crystalmark3d25/files/1.0.0/CrystalMark3D25_1_0_0.exe/download в браузере."""
    webbrowser.open_new("https://sourceforge.net/projects/crystalmark3d25/files/1.0.0/CrystalMark3D25_1_0_0.exe/download")

# Функция для открытия ссылки в браузере Rufus
def open_rufus_link():
    """Открывает ссылку https://github.com/pbatard/rufus/releases/download/v4.14/rufus-4.14.exe в браузере."""
    webbrowser.open_new("https://github.com/pbatard/rufus/releases/download/v4.14/rufus-4.14.exe")

# Функция для открытия ссылки в браузере Flibusta
def open_flibusta_link():
    """Открывает ссылку https://flibustier64.com/ в браузере."""
    webbrowser.open_new("https://flibustier64.com/")

# Функция для открытия ссылки vc.ru
def open_vc_link():
    """Открывает ссылку https://vc.ru/flood/2763286-ofitsialnye-obraztsy-windows-10-i-11-v-rossii в браузере."""
    webbrowser.open_new("https://vc.ru/flood/2763286-ofitsialnye-obraztsy-windows-10-i-11-v-rossii")


# Создаем кнопку во вкладке 2 для открытия ссылки Dr.Web
drweb_button = tk.Button(tab2, text="Скачать CureIt!", command=open_drweb_link, fg="white", bg="darkgray")
drweb_button.pack(pady=10)

# Создаем кнопку во вкладке 2 для открытия ссылки FurMark
furmark_button = tk.Button(tab2, text="Скачать FurMark", command=open_furmark_link, fg="white", bg="darkgray")
furmark_button.pack(pady=10)

# Создаем кнопку во вкладке 2 для открытия ссылки CrystalMark3D
crystalmark_button = tk.Button(tab2, text="Скачать CrystalMark3D", command=open_crystalmark_link, fg="white", bg="darkgray")
crystalmark_button.pack(pady=10)

# Создаем кнопку во вкладке 2 для открытия ссылки Rufus
rufus_button = tk.Button(tab2, text="Скачать Rufus", command=open_rufus_link, fg="white", bg="darkgray")
rufus_button.pack(pady=10)

# Создаем кнопку во вкладке 2 для открытия ссылки Flibusta
flibusta_button = tk.Button(tab2, text="Открыть Flibusta", command=open_flibusta_link, fg="white", bg="darkgray")
flibusta_button.pack(pady=10)

# Создаем кнопку во вкладке 2 для открытия ссылки vc.ru
vc_button = tk.Button(tab2, text="Официальные образы Windows", command=open_vc_link, fg="white", bg="darkgray")
vc_button.pack(pady=10)


window.mainloop()
