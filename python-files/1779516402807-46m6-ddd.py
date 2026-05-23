import pyautogui as pipi
import time
import random

time.sleep(1000)
d = 0
while True:
    if d >= 10000:
        break
    else:
        pipi.click(random.randint(1, 1500), random.randint(1, 1000))

    

