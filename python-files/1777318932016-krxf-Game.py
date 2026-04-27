import tkinter as tk

print("Начало игры")
name = input("Напишите своё имя --- ")
print(f"Привет, {name}!")
print("Вы готовы начать?")

while True:
    try:
        start = int(input("Напишите 1 если да и 2 если нет --- "))
        
        if start == 1:
            print(f"Отлично, {name}! Запускаем игру...")
            
            # Создаём окно игры
            window = tk.Tk()
            window.title(f"Игра для {name}")
            window.geometry("800x600")
            
            # Холст для рисования
            canvas = tk.Canvas(window, width=800, height=600, bg='black')
            canvas.pack()
            
            # Квадрат игрока
            player = canvas.create_rectangle(375, 275, 425, 325, fill='red')
            speed = 20
            
            # Управление стрелками
            def move_left(event):
                canvas.move(player, -speed, 0)
            def move_right(event):
                canvas.move(player, speed, 0)
            def move_up(event):
                canvas.move(player, 0, -speed)
            def move_down(event):
                canvas.move(player, 0, speed)
            
            # Привязываем клавиши
            window.bind('<Left>', move_left)
            window.bind('<Right>', move_right)
            window.bind('<Up>', move_up)
            window.bind('<Down>', move_down)
            
            # Запускаем окно
            window.mainloop()
            break
            
        elif start == 2:
            print("Жаль... Давай попробуем ещё раз!")
            name = input("Напишите своё имя --- ")
            print(f"Привет, {name}!")
            print("Вы готовы начать?")
            
        else:
            print("Ошибка! Нужно ввести 1 (да) или 2 (нет)")
            
    except ValueError:
        print("Ошибка! Введите число 1 или 2")
