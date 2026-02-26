import keyboard
import pyautogui
import time

print("Dinlemede... F1'e basınca 12 kere F1 basacak!")

while True:
    if keyboard.is_pressed('f1'):
        for _ in range(12):
            pyautogui.press('f1')
            time.sleep(0.05)
        while keyboard.is_pressed('f1'):
            pass