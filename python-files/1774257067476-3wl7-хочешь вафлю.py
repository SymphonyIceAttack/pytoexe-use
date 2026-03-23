import tkinter as tk
from tkinter import messagebox
import random
import webbrowser

def move_button(event):
    """
    Функция для "уползающего" поведения кнопки "Нет".
    Рандомно перемещает кнопку при наведении на нее курсора.
    """
    # Координаты для случайного перемещения кнопки.
    # Диапазон y уменьшен, чтобы кнопка оставалась в пределах окна.
    x, y = random.randint(0, 200), random.randint(120, 170)
    no_button.place(x=x, y=y)

def show_custom_warning_and_prompt_close():
    """
    Показывает окно с сообщением "неа" и кнопкой "Ну пожаалуйста".
    При нажатии на кнопку "Ну пожаалуйста" основное окно закрывается.
    """
    # Создаем окно сообщения с пользовательской кнопкой.
    # messagebox.askyesno возвращает True, если пользователь нажимает "Да" (или соответствующую кнопку),
    # и False, если нажимает "Нет". Нам нужно переопределить это поведение.

    # Создаем временное окно верхнего уровня для нашего кастомного диалога
    custom_dialog = tk.Toplevel(root)
    custom_dialog.title("Внимание!")
    custom_dialog.geometry("250x150")
    custom_dialog.transient(root) # Делает диалоговое окно "над" основным
    custom_dialog.grab_set() # Перехватывает фокус, чтобы пользователь взаимодействовал только с этим окном

    # Метка с сообщением
    label = tk.Label(custom_dialog, text="неа:)", font=("Arial", 16))
    label.pack(pady=20)

    # Кнопка "Ну пожаалуйста"
    plead_button = tk.Button(custom_dialog, text="Ну пожаалуйста!!", font=("Arial", 14),
                             command=lambda: [root.destroy(), custom_dialog.destroy()]) # Закрывает основное и это диалоговое окно
    plead_button.pack(pady=10)

    # Обработка стандартного закрытия окна (например, крестиком)
    # Если пользователь попытается закрыть это диалоговое окно, оно просто останется открытым,
    # пока не нажмет "Ну пожаалуйста".
    custom_dialog.protocol("WM_DELETE_WINDOW", lambda: None)

    # Ждем, пока диалоговое окно не будет закрыто
    root.wait_window(custom_dialog)


def open_google_for_waffles():
    """
    Открывает Google с поисковым запросом "вафли".
    """
    webbrowser.open("https://www.google.com/search?q=вафли")

# Создание основного окна
root = tk.Tk()
root.title("Вопрос")
root.geometry("300x200") # Устанавливаем размер окна

# Надпись с вопросом
label = tk.Label(root, text="Хочешь вафлю?", font=("Arial", 16))
label.pack(pady=20)

# Кнопка "ага"
yes_button = tk.Button(root, text="ага", font=("Arial", 14), command=open_google_for_waffles)
yes_button.pack(side=tk.LEFT, padx=30)

# Кнопка "Нет"
no_button = tk.Button(root, text="Нет", font=("Arial", 14))
no_button.pack(side=tk.RIGHT, padx=30)
no_button.bind("<Enter>", move_button) # Привязываем функцию к событию наведения курсора

# Обработка закрытия окна: теперь вызывается наша кастомная функция
root.protocol("WM_DELETE_WINDOW", show_custom_warning_and_prompt_close)

# Запуск главного цикла обработки событий
root.mainloop()


