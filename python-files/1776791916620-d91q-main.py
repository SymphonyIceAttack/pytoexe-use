import tkinter as tk



# Создаём основное окно
window = tk.Tk()
window.title("Окно с кнопкой")
window.geometry("400x300")

# Создаём кнопку
button = tk.Button(
    window,
    text="Нажми меня!",

)

# Размещаем кнопку по центру с помощью pack()
button.pack(expand=True)

# Запускаем главный цикл обработки событий
window.mainloop()