import cv2
import numpy as np
import pyautogui
import time
import winsound

template = cv2.imread("market.png", 0)

print("Total Battle Börsen Scanner gestartet")

while True:

    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)

    threshold = 0.8
    loc = np.where(result >= threshold)

    if len(loc[0]) > 0:
        print("Börse erkannt!")
        winsound.Beep(2000, 700)
        time.sleep(10)

    time.sleep(5)