import pyautogui
import time
from threading import Thread
import keyboard  # pip install keyboard

# SETTINGS
click_interval = 0.1  # seconds between clicks
running = True        # toggle for clicking

# Function that runs auto-clicking
def auto_click():
    while running:
        pyautogui.click()
        time.sleep(click_interval)

# Function to stop clicking when 'q' is pressed
def check_stop():
    global running
    keyboard.wait('q')  # waits until 'q' is pressed
    running = False

# Start the auto-clicker thread
click_thread = Thread(target=auto_click)
click_thread.start()

# Start the key listener thread
stop_thread = Thread(target=check_stop)
stop_thread.start()

print("Auto-clicker started! Press 'q' to stop.")

# Wait for threads to finish
click_thread.join()
stop_thread.join()

print("Auto-clicker stopped.")
