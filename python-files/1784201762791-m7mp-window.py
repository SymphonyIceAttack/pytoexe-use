
import tkinter as tk
from tkinter import messagebox

def on_ok():
    messagebox.showinfo("Результат", "Вы нажали ОК!")
    # Здесь можно добавить свою логику при нажатии ОК

def on_cancel():
    if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите отменить?"):
        root.destroy()  # Закрываем окно

# Создаем главное окно
root = tk.Tk()
root.title("Пример окна")
root.geometry("300x150")  # Ширина x Высота

# Добавляем фрейм для кнопок (для центрирования)
frame = tk.Frame(root)
frame.pack(pady=20)

# Кнопка ОК
btn_ok = tk.Button(frame, text="ОК", width=10, command=on_ok)
btn_ok.pack(side=tk.LEFT, padx=10)

# Кнопка Отмена
btn_cancel = tk.Button(frame, text="Отмена", width=10, command=on_cancel)
btn_cancel.pack(side=tk.RIGHT, padx=10)

# Запуск главного цикла обработки событий
root.mainloop()