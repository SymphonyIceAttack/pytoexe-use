import tkinter as tk
import random
import time

def main():
    # Скрытое главное окно (нужно для управления дочерними окнами)
    root = tk.Tk()
    root.withdraw()

    # Размеры экрана и окна
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    win_width = 200
    win_height = 100

    start_time = time.time()          # время запуска
    running = True                    # флаг работы программы

    def create_window():
        nonlocal running
        if not running:
            return

        # Создаём новое окно
        win = tk.Toplevel(root)
        win.title("ЛОХ")
        win.resizable(False, False)

        # Случайная позиция в пределах экрана
        x = random.randint(0, max(0, screen_width - win_width))
        y = random.randint(0, max(0, screen_height - win_height))
        win.geometry(f"{win_width}x{win_height}+{x}+{y}")

        # Надпись «ЛОХ» крупным шрифтом
        label = tk.Label(win, text="ЛОХ", font=("Arial", 24, "bold"), fg="red")
        label.pack(expand=True, fill=tk.BOTH)

        # Если 15 секунд ещё не прошло – создаём следующее окно через 50 мс
        if time.time() - start_time < 30:
            root.after(50, create_window)
        else:
            running = False
            root.destroy()            # закрываем всё и выходим

    # Запускаем бесконечное создание окон
    create_window()

    # Дополнительный таймер на случай, если create_window не вызовет destroy
    root.after(15000, lambda: root.destroy())

    root.mainloop()


if __name__ == "__main__":
    main()
