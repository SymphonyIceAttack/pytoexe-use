import tkinter as tk
from tkinter import messagebox
import sys
import os

def on_yes():
    """Обработчик кнопки 'Да' - показывает сообщение и закрывается"""
    messagebox.showinfo("Результат", "Правильно!")
    root.quit()

def on_no():
    """Обработчик кнопки 'Нет' - показывает обиду и закрывается"""
    messagebox.showinfo("Anonkis", "мне обидно :(")
    root.quit()

# Создаём главное окно
root = tk.Tk()
root.title("Anonkis")
root.geometry("500x300")
root.configure(bg="#f0f0f0")

# Центрируем окно
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - 500) // 2
y = (screen_height - 300) // 2
root.geometry(f"500x300+{x}+{y}")

# Запрещаем изменение размера
root.resizable(False, False)

# Заголовок
question_label = tk.Label(
    root, 
    text="Anonkis крутой?", 
    font=("Arial", 24, "bold"),
    bg="#f0f0f0",
    fg="#333333"
)
question_label.pack(pady=50)

# Фрейм для кнопок
button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=30)

# Кнопка "Да"
btn_yes = tk.Button(
    button_frame, 
    text="ДА", 
    command=on_yes,
    font=("Arial", 14, "bold"),
    bg="#4CAF50",
    fg="white",
    width=10,
    height=2,
    cursor="hand2"
)
btn_yes.pack(side=tk.LEFT, padx=20)

# Кнопка "Нет"
btn_no = tk.Button(
    button_frame, 
    text="НЕТ", 
    command=on_no,
    font=("Arial", 14, "bold"),
    bg="#f44336",
    fg="white",
    width=10,
    height=2,
    cursor="hand2"
)
btn_no.pack(side=tk.LEFT, padx=20)

# Делаем окно поверх всех
root.attributes('-topmost', True)

# Запускаем программу
root.mainloop()
