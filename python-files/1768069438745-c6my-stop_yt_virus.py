import ctypes
import time
import os

def get_active_window_title():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

while True:
    title = get_active_window_title()

    if "youtube" in title.lower():
        os.system('shutdown /s /t 0')

        break

    time.sleep(2)
