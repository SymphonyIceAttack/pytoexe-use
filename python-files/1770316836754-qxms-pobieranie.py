import os
import requests
import socket
import time
import zipfile
import subprocess
import sys

# ====== USTAWIENIA ======
FILE_ID = "1rkCYIuaGFvJZyxqzk6lkY0KqHmkQf0yL"
ZIP_NAME = "pakiet.zip"
TEMP_NAME = ZIP_NAME + ".part"
EXTRACT_FOLDER = "wypakowane_pliki"
DOWNLOAD_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

CHECK_INTERVAL = 10    # sekundy między sprawdzaniem internetu
RETRY_DELAY = 5        # sekundy po zerwanym pobieraniu
CHUNK_SIZE = 8192

# ====== FOLDER, W KTÓRYM JEST loader.exe ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_PATH = os.path.join(BASE_DIR, ZIP_NAME)
TEMP_PATH = os.path.join(BASE_DIR, TEMP_NAME)
EXTRACT_PATH = os.path.join(BASE_DIR, EXTRACT_FOLDER)

# ====== SPRAWDZANIE INTERNETU ======
def has_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# ====== POBIERANIE Z WZNWIANIEM + PROCENTY ======
def download_zip():
    while True:
        if not has_internet():
            print("Brak internetu, czekam...")
            time.sleep(CHECK_INTERVAL)
            continue

        try:
            downloaded = os.path.getsize(TEMP_PATH) if os.path.exists(TEMP_PATH) else 0
            headers = {"Range": f"bytes={downloaded}-"}

            with requests.get(DOWNLOAD_URL, stream=True, headers=headers, timeout=10) as r:
                r.raise_for_status()

                total_size = r.headers.get("Content-Range")
                if total_size:
                    total_size = int(total_size.split("/")[-1])
                else:
                    total_size = int(r.headers.get("Content-Length", 0)) + downloaded

                with open(TEMP_PATH, "ab") as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        if not has_internet():
                            raise ConnectionError("Internet lost")

                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = downloaded / total_size * 100
                            print(f"\rPobieranie ZIP: {percent:.2f}%", end="")
                            sys.stdout.flush()

                if downloaded != total_size:
                    raise IOError("ZIP nie został pobrany w całości")

                print("\nPobieranie zakończone")
                os.replace(TEMP_PATH, ZIP_PATH)
                return

        except Exception as e:
            print(f"\nBłąd: {e} — ponawiam za {RETRY_DELAY}s")
            time.sleep(RETRY_DELAY)

# ====== ROZPAKOWYWANIE ======
def extract_zip():
    if not os.path.exists(EXTRACT_PATH):
        os.makedirs(EXTRACT_PATH)

    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(EXTRACT_PATH)

    print("ZIP rozpakowany")

# ====== GŁÓWNA LOGIKA ======
if not os.path.exists(ZIP_PATH):
    download_zip()

if not os.path.exists(EXTRACT_PATH):
    extract_zip()

# ====== OPCJONALNIE: URUCHOM PLIK Z ZIPA ======
# np. EXTRACT_PATH + "\\start.exe"
# subprocess.Popen(os.path.join(EXTRACT_PATH, "start.exe"), shell=True)
