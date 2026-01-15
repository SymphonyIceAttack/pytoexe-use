import pyautogui
import time
import os

# 1. Открываем Chrome
os.system("start chrome.exe")
time.sleep(4)  # Ждем запуска Chrome

# 2. Активируем окно Chrome
# Пробуем несколько способов активации
try:
    # Способ 1: Через поиск окна
    chrome_windows = pyautogui.getWindowsWithTitle("Google Chrome")
    if chrome_windows:
        chrome_windows[0].activate()
    else:
        chrome_windows = pyautogui.getWindowsWithTitle("Chrome")
        if chrome_windows:
            chrome_windows[0].activate()
        else:
            # Способ 2: Alt+Tab
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
except:
    # Способ 3: Просто даем время
    time.sleep(1)

time.sleep(1)  # Даем время для активации

# 3. Нажимаем F6
pyautogui.press('f6')
time.sleep(0.5)

# 4. Вводим URL (исправленная ссылка)
pyautogui.write('chrome://password-manager/settings', interval=0.05)
time.sleep(0.5)

# 5. Нажимаем Enter
pyautogui.press('enter')
time.sleep(3)  # Ждем загрузки страницы

# 6. Нажимаем Tab 6 раз
for _ in range(6):
    pyautogui.press('tab')
    time.sleep(0.15)

# 7. Нажимаем Enter
pyautogui.press('enter')
time.sleep(1.5)

# 8. Вводим текст
# Разные способы ввода на выбор:

# Способ A: Обычный ввод
pyautogui.write('cvenyjtdhtvz', interval=0.1)

# ИЛИ Способ B: По буквам с большими задержками
# text = "cvenyjtdhtvz"
# for char in text:
#     pyautogui.write(char, interval=0.2)
#     time.sleep(0.1)

time.sleep(0.5)

# 9. Нажимаем Enter
pyautogui.press('enter')

print("Скрипт выполнен!")