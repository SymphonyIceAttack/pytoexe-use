import os
import time
import requests

# CONFIG
SERVER_URL = "https://your-server-domain.com/upload"  # ide megy a feltöltés
USERNAME = "demo_user"  # a user azonosító
UPLOAD_FOLDER = "C:\\Users\\Public\\Documents\\BackupFiles"  # a mentendő mappád
INTERVAL = 30  # másodpercenként ellenőriz, és feltölt

def get_files_to_upload():
    files = []
    for f in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, f)
        if os.path.isfile(path):
            files.append(path)
    return files

def upload_file(file_path):
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        data = {"username": USERNAME}
        try:
            response = requests.post(SERVER_URL, files=files, data=data)
            if response.status_code == 200:
                print(f"[OK] Uploaded: {file_path}")
            else:
                print(f"[FAIL] Upload failed: {file_path}")
        except Exception as e:
            print(f"[ERROR] {e}")

def main():
    print("[Agent] Windows backup agent started...")
    while True:
        files = get_files_to_upload()
        for file_path in files:
            upload_file(file_path)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()