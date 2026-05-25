import time
import pyautogui
import keyboard
import os
from PIL import Image
import numpy as np

# Отключаем безопасный режим pyautogui (осторожно!)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1  # Небольшая пауза между действиями

def find_window_on_screen(image_path, region=None):
    """
    Поиск окна/изображения на экране.
    Если изображение найдено, возвращает координаты центра.
    Если не найдено, возвращает None.
    """
    try:
        if not os.path.exists(image_path):
            print(f"Изображение не найдено: {image_path}")
            return None
        
        location = pyautogui.locateOnScreen(image_path, confidence=0.8, region=region)
        if location:
            center = pyautogui.center(location)
            return center
        return None
    except Exception as e:
        print(f"Ошибка при поиске изображения: {e}")
        return None

def press_combination(*keys):
    """Нажатие комбинации клавиш"""
    for key in keys:
        keyboard.press(key)
    time.sleep(0.05)
    for key in reversed(keys):
        keyboard.release(key)
    time.sleep(0.1)

def main():
    print("Программа запущена. Ждем 10 секунд...")
    time.sleep(10)
    
    print("Начинаем выполнение действий...")
    
    # 1. Нажимаем Ctrl+C
    print("Нажимаем Ctrl+C")
    press_combination('ctrl', 'c')
    time.sleep(0.2)
    
    # 2. Alt+Tab
    print("Нажимаем Alt+Tab")
    press_combination('alt', 'tab')
    time.sleep(0.5)
    
    # 3. Ctrl+F
    print("Нажимаем Ctrl+F")
    press_combination('ctrl', 'f')
    time.sleep(0.2)
    
    # 4. Ctrl+V
    print("Нажимаем Ctrl+V")
    press_combination('ctrl', 'v')
    time.sleep(0.2)
    
    # 5. Проверяем появление определенного окна
    print("Проверяем наличие определенного окна...")
    
    # Путь к изображению окна (замените на ваше)
    image_path = "target_window.png"  # Положите скриншот окна в папку с программой
    
    # Поиск окна на экране
    window_found = find_window_on_screen(image_path)
    
    if window_found:
        print(f"Окно найдено! Выполняем дополнительную последовательность...")
        
        # Space
        print("Нажимаем Space")
        keyboard.press_and_release('space')
        time.sleep(0.2)
        
        # Alt+F4
        print("Нажимаем Alt+F4")
        press_combination('alt', 'f4')
        time.sleep(0.2)
        
        # Ctrl+Down
        print("Нажимаем Ctrl+Down")
        press_combination('ctrl', 'down')
        time.sleep(0.2)
        
        # Down
        print("Нажимаем Down")
        keyboard.press_and_release('down')
        time.sleep(0.2)
        
        # Ctrl+V
        print("Нажимаем Ctrl+V")
        press_combination('ctrl', 'v')
        time.sleep(0.2)
    else:
        print("Окно не найдено. Нажимаем только Alt+F4")
        press_combination('alt', 'f4')
        time.sleep(0.2)
    
    # 6. Alt+Tab
    print("Нажимаем Alt+Tab")
    press_combination('alt', 'tab')
    time.sleep(0.5)
    
    # 7. Down
    print("Нажимаем Ctrl+Down")
    press_combination('ctrl', 'down')
    time.sleep(0.2)

    # 8. Down
    print("Нажимаем Down")
    keyboard.press_and_release('down')
    
    print("Программа завершена!")

# Альтернативная функция для проверки пикселей в определенной области
def check_pixels_in_region(region, expected_colors):
    """
    Проверка пикселей в определенной области экрана.
    region: (x, y, width, height)
    expected_colors: список ожидаемых цветов пикселей [(x_offset, y_offset, (r,g,b)), ...]
    """
    screenshot = pyautogui.screenshot(region=region)
    pixels = screenshot.load()
    
    for x_offset, y_offset, expected_color in expected_colors:
        actual_color = pixels[x_offset, y_offset]
        # Сравниваем с допуском
        if not all(abs(actual_color[i] - expected_color[i]) < 10 for i in range(3)):
            return False
    return True

def main_with_pixel_check():
    """Альтернативная версия с проверкой по пикселям"""
    print("Программа запущена. Ждем 10 секунд...")
    time.sleep(10)
    
    print("Начинаем выполнение действий...")
    
    # Основная последовательность (как в первой версии)
    press_combination('ctrl', 'c')
    time.sleep(0.2)
    
    press_combination('alt', 'tab')
    time.sleep(0.5)
    
    press_combination('ctrl', 'f')
    time.sleep(0.2)
    
    press_combination('ctrl', 'v')
    time.sleep(0.2)
    
    # Проверка пикселей в определенной области
    # ВАЖНО: Замените координаты на свои!
    region = (100, 100, 200, 200)  # x, y, width, height
    expected_colors = [
        (10, 10, (255, 255, 255)),  # Пример: пиксель на позиции (x+10, y+10) должен быть белым
        (50, 30, (0, 0, 255)),      # Пример: пиксель на позиции (x+50, y+30) должен быть синим
    ]
    
    window_found = check_pixels_in_region(region, expected_colors)
    
    if window_found:
        print("Окно найдено по пикселям! Выполняем дополнительную последовательность...")
        
        keyboard.press_and_release('space')
        time.sleep(0.2)
        
        press_combination('alt', 'f4')
        time.sleep(0.2)
        
        press_combination('ctrl', 'down')
        time.sleep(0.2)
        
        keyboard.press_and_release('down')
        time.sleep(0.2)
        
        press_combination('ctrl', 'v')
        time.sleep(0.2)
    else:
        print("Окно не найдено по пикселям. Нажимаем только Alt+F4")
        press_combination('alt', 'f4')
        time.sleep(0.2)
    
    press_combination('alt', 'tab')
    time.sleep(0.5)
    
    keyboard.press_and_release('down')
    
    print("Программа завершена!")

if __name__ == "__main__":
    # Выберите один из вариантов:
    main()  # Использует поиск по изображению
    # main_with_pixel_check()  # Использует проверку пикселей