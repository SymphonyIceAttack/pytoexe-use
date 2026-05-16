import multiprocessing
import time

import confidence
import interception
import numpy as np
import pyautogui
import cv2
import win32api
import pyscreenshot as ImageGrab
from datetime import datetime
import os

def find_image(template_path, screen_path, confidence=0.97):

    """
    Ищет шаблон (template_path) внутри большого изображения (screen_path).
    Возвращает координаты (x, y) верхнего левого угла найденного шаблона и уровень совпадения.
    """
    # Загружаем изображения
    screen = cv2.imread(screen_path)
    template = cv2.imread(template_path)

    if screen is None:
        raise FileNotFoundError(f"Не удалось загрузить {screen_path}")
    if template is None:
        raise FileNotFoundError(f"Не удалось загрузить {template_path}")

    # Получаем размеры шаблона
    h, w = template.shape[:2]

    # Метод сравнения шаблонов
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)

    # Находим все позиции с совпадением выше порога confidence
    locations = np.where(result >= confidence)

    # Преобразуем в список координат (x, y)
    points = list(zip(locations[1], locations[0]))  # result[x][y] -> (x, y)

    if not points:
        return None, 0.0

    # Лучшее совпадение (максимальное значение)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # max_loc — это координаты верхнего левого угла
    return max_loc, max_val

time.sleep(5)

while True:
    timings = 0.1
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    screenshot_folder = os.path.join(desktop, "sampMod")
    screenshot_folder_A = os.path.join(desktop, "sampMod\\screens\\A.png")
    screenshot_folder_W = os.path.join(desktop, "sampMod\\screens\\W.png")
    screenshot_folder_D = os.path.join(desktop, "sampMod\\screens\\D.png")
    screenshot_folder_S = os.path.join(desktop, "sampMod\\screens\\S.png")
    screenshot_folder_Q = os.path.join(desktop, "sampMod\\screens\\Q.png")
    screenshot_folder_E = os.path.join(desktop, "sampMod\\screens\\E.png")
    # screenshot_folder_Probel = os.path.join(desktop, "sampMod\screens\Probel.png")
    full_path = os.path.join(screenshot_folder, filename)
    screenshot = ImageGrab.grab()
    screenshot.save(full_path)
    print(f"Скриншот сохранён: {full_path}")

    os.makedirs(screenshot_folder, exist_ok=True)
    posA, scoreA = find_image(screenshot_folder_A, full_path)
    posW, scoreW = find_image(screenshot_folder_W, full_path)
    posD, scoreD = find_image(screenshot_folder_D, full_path)
    posS, scoreS = find_image(screenshot_folder_S, full_path)
    posQ, scoreQ = find_image(screenshot_folder_Q, full_path)
    posE, scoreE = find_image(screenshot_folder_E, full_path)

    if posA is not None:
        time.sleep(1)
        interception.press("a")
        print(f"Шаблон найден в позиции: x={posA[0]}, y={posA[1]}")

    if posW is not None:
        time.sleep(timings)
        interception.press("w")
        print(f"Шаблон найден в позиции: x={posW[0]}, y={posW[1]}")

    if posD is not None:
        time.sleep(timings)
        interception.press("d")
        print(f"Шаблон найден в позиции: x={posD[0]}, y={posD[1]}")

    if posS is not None:
        time.sleep(timings)
        interception.press("s")
        print(f"Шаблон найден в позиции: x={posS[0]}, y={posS[1]}")

    if posQ is not None:
        time.sleep(timings)
        interception.press("q")
        print(f"Шаблон найден в позиции: x={posQ[0]}, y={posQ[1]}")

    if posE is not None:
        time.sleep(timings)
        interception.press("e")
        print(f"Шаблон найден в позиции: x={posE[0]}, y={posE[1]}")

    time.sleep(timings)
    os.remove(full_path)


