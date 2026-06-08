import urllib.request
import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://android.googlesource.com/platform/system/ca-certificates/+/refs/heads/main/files/"
OUTPUT = "android-ca-bundle.pem"
MAX_WORKERS = 3   # параллельных потоков
MAX_RETRIES = 5    # попыток на файл
RETRY_DELAY = 5    # секунд между попытками

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    return urllib.request.urlopen(req).read()

def get_file_list():
    raw = fetch(BASE + "?format=JSON")
    data = json.loads(raw.split(b"\n", 1)[1])
    entries = data["entries"]
    if isinstance(entries, list):
        return [e["name"] for e in entries]
    else:
        return list(entries.keys())

def download_cert(filename):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            content = fetch(BASE + filename + "?format=TEXT")
            pem = base64.b64decode(content).decode("utf-8")
            time.sleep(0.5)
            return filename, pem
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return filename, None  # все попытки исчерпаны

files = get_file_list()
print(f"Найдено файлов: {len(files)}")

results = {}
failed = []

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(download_cert, f): f for f in files}
    done = 0
    for future in as_completed(futures):
        filename, pem = future.result()
        done += 1
        if pem:
            results[filename] = pem
            print(f"[{done}/{len(files)}] ✓ {filename}")
        else:
            failed.append(filename)
            print(f"[{done}/{len(files)}] ✗ {filename} — не удалось скачать")

if failed:
    print(f"\nПропущено ({len(failed)}): {', '.join(failed)}")

import os
os.makedirs("certs", exist_ok=True)
for filename in sorted(results):
    with open(os.path.join("certs", filename), "w", encoding="utf-8") as out:
        out.write(results[filename])

# Атомарная замена: заменяем старый файл только после успешной записи
import os
os.replace(tmp_output, OUTPUT)

print(f"\nГотово! Записано {len(results)} сертификатов → {OUTPUT}")