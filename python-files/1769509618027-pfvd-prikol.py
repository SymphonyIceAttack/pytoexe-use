import random
import time
import os

target_number = 10

def shutdown_computer():
    """Выключаем компьютер."""
    print("Совпадение найдено! Выключение компьютера...")
    os.system('shutdown /s /t 1')

while True:
    generated_number = random.randint(1, 20)
    if generated_number == target_number:
        shutdown_computer()
        break
    
    print(f"Случайное число: {generated_number}. Не совпадает.")
    time.sleep(300)  # Ждём 5 минут (300 секунд)
