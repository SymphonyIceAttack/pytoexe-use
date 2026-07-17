import time
import pyautogui
FISH_BUTTON_POS = (100, 200)
SELL_BUTTON_POS = (300, 400)
RETURN_BUTTON_POS = (500, 600)
def fish():
    print("Отправляемся на рыбалку...")
    pyautogui.click(FISH_BUTTON_POS)
    time.sleep(5)
def sell_fish():
    print("Продаем рыбу...")
    pyautogui.click(SELL_BUTTON_POS)
    time.sleep(2)
def return_to_fish():
    print("Возвращаемся на рыбалку...")
    pyautogui.click(RETURN_BUTTON_POS)
    time.sleep(3)

