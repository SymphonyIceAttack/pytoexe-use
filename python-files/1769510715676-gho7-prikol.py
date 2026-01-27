import random
import time
import os
import win32gui
import win32con

# Функция для минимизации окна
def minimize_window():
    window_handle = win32gui.GetForegroundWindow()  # Получаем дескриптор текущего активного окна
    win32gui.ShowWindow(window_handle, win32con.SW_HIDE)  # Минимизируем окно

# Заданное число, которое мы будем сравнивать с результатом генератора
target_number = 10  # Можно задать любое другое значение здесь

def shutdown_computer():
    """Выключаем компьютер."""
    print("Совпадение найдено! Выключение компьютера...")
    os.system('shutdown /s /t 1')  # Команда для завершения работы ОС Windows

minimize_window()  # Сразу же прячем окно при старте программы

while True:
    generated_number = random.randint(1, 50)
    if generated_number == target_number:
        shutdown_computer()
        break
    
    print(f"Случайное число: {generated_number}. Не совпадает.")
    time.sleep(180)  
