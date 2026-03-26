import tkinter as tk
import random

# Список слов
words = ["Данил", "Салават", "лёня", "костя", "глебас-котакбас"]

# Функция, которая вызывается при нажатии кнопки
def show_random_word():
    chosen = random.choice(words)
    label.config(text=chosen)

# Создаём окно
window = tk.Tk()
window.title("Генератор слов")
window.geometry("300x150")
window.resizable(False, False)

# Метка (надпись) для вывода слова
label = tk.Label(window, text="Нажми кнопку", font=("Arial", 16), pady=20)
label.pack()

# Кнопка
button = tk.Button(window, text="Получить слово", command=show_random_word, font=("Arial", 12), padx=10, pady=5)
button.pack()

# Запускаем приложение
window.mainloop()
