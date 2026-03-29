import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def delete_file_or_folder(path):
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        messagebox.showinfo("Успех", f"Файл/папка '{path}' успешно удален(а).")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить '{path}'.\nОшибка: {e}")

def select_and_delete():
    path = filedialog.askopenfilename(title="Выберите файл для удаления")
    if path:
        confirm = messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить этот файл?\n{path}")
        if confirm:
            delete_file_or_folder(path)

def select_folder_and_delete():
    path = filedialog.askdirectory(title="Выберите папку для удаления")
    if path:
        confirm = messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить эту папку?\n{path}")
        if confirm:
            delete_file_or_folder(path)

# Создание основного окна
root = tk.Tk()
root.title("Удаление файлов и папок")
root.geometry("300x150")

# Кнопки
btn_delete_file = tk.Button(root, text="Удалить файл", command=select_and_delete, width=20)
btn_delete_file.pack(pady=10)

btn_delete_folder = tk.Button(root, text="Удалить папку", command=select_folder_and_delete, width=20)
btn_delete_folder.pack(pady=10)

btn_exit = tk.Button(root, text="Выход", command=root.quit, width=20)
btn_exit.pack(pady=10)

# Запуск главного цикла
root.mainloop()
