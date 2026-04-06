import time
import threading
import pyautogui
import tkinter as tk
from tkinter import ttk
from pymakcu import MAKCU
import pynput.mouse

# Инициализация контроллера MAKCU
makcu = MAKCU()

# Инициализация глобальных переменных
move_left = False
move_right = False
distance = 100  # Начальное расстояние
speed = 0.25  # Начальная скорость

# Функции для движения курсора
def move_cursor_left():
    x, y = pyautogui.position()
    pyautogui.moveTo(x - distance, y, duration=speed)

def move_cursor_right():
    x, y = pyautogui.position()
    pyautogui.moveTo(x + distance, y, duration=speed)

# Функция для контроля движений мыши
def move_mouse():
    while True:
        if move_left:
            move_cursor_left()
        if move_right:
            move_cursor_right()
        time.sleep(0.05)  # Задержка, чтобы уменьшить нагрузку на процессор

# Функция для обработки зажатых клавиш мыши
def on_click(x, y, button, pressed):
    global move_left, move_right
    if button == pynput.mouse.Button.left:  # ЛКМ
        move_left = pressed
    elif button == pynput.mouse.Button.right:  # ПКМ
        move_right = pressed

# Создаем окно интерфейса
def create_gui():
    def update_settings():
        global distance, speed
        distance = int(distance_entry.get())
        speed = float(speed_entry.get())

    # Создаем окно
    window = tk.Tk()
    window.title("Контроллер MAKCU")

    # Сетка
    grid_frame = ttk.Frame(window, padding="10")
    grid_frame.grid(row=0, column=0, padx=10, pady=10)

    # Настройки расстояния
    ttk.Label(grid_frame, text="Расстояние (пиксели):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    distance_entry = ttk.Entry(grid_frame)
    distance_entry.insert(0, str(distance))
    distance_entry.grid(row=0, column=1, padx=5, pady=5)

    # Настройки скорости
    ttk.Label(grid_frame, text="Скорость (секунды):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    speed_entry = ttk.Entry(grid_frame)
    speed_entry.insert(0, str(speed))
    speed_entry.grid(row=1, column=1, padx=5, pady=5)

    # Кнопка для обновления настроек
    update_button = ttk.Button(grid_frame, text="Обновить", command=update_settings)
    update_button.grid(row=2, column=0, columnspan=2, pady=10)

    # Запуск интерфейса
    window.mainloop()

# Запуск процесса движения мыши в отдельном потоке
mouse_thread = threading.Thread(target=move_mouse, daemon=True)
mouse_thread.start()

# Создаем слушателя для мыши
listener = pynput.mouse.Listener(on_click=on_click)
listener.start()

# Создаем GUI
create_gui()