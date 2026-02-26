import time
import pyautogui
from pynput import mouse

print("Program çalışıyor...")
print("Scroll UP  -> 12x F1")
print("Scroll DOWN -> 12x SHIFT+F1")

cooldown = 0.3   # Scroll tetiklendikten sonra tekrar algılamadan önce bekleme
last_trigger = 0


def press_f1_12():
    for _ in range(12):
        pyautogui.press('f1')
        time.sleep(0.05)


def press_shift_f1_12():
    for _ in range(12):
        pyautogui.hotkey('shift', 'f1')
        time.sleep(0.05)


def on_scroll(x, y, dx, dy):
    global last_trigger
    now = time.time()

    # Spam tetiklemeyi önle
    if now - last_trigger < cooldown:
        return

    if dy > 0:
        press_f1_12()
        last_trigger = now

    elif dy < 0:
        press_shift_f1_12()
        last_trigger = now


# Mouse dinleyici başlat
with mouse.Listener(on_scroll=on_scroll) as listener:
    while True:
        time.sleep(0.1)   # CPU dinlendirme (çok önemli)