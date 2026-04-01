import pyautogui
import time

pyautogui.FAILSAFE = True

while True
    # �ո��2 ���0.2s
    pyautogui.press('space')
    time.sleep(0.2)
    pyautogui.press('space')

    time.sleep(1.5)
    pyautogui.hotkey('s', 'space')

    time.sleep(1)
    pyautogui.press('q')

    time.sleep(1.5)
    pyautogui.press('f')

    time.sleep(1)
    pyautogui.press('f')