import os
import sys
import subprocess
import hashlib
import uuid
import json
import time
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor

# ===== AUTO INSTALL =====
def install(package):
    try:
        __import__(package)
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install("requests")
import requests

# ===== BASE DIR (EXE SAFE) =====
def get_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE = get_base()
OUTPUT_FILE = os.path.join(BASE, "available_usernames.txt")

# ===== KEYS =====
DEV_KEY = "DEVMASTERKEY12345"

VALID_KEYS = [
"A9F3K2M8Z1Q7X5C",
"B7D2L9P4T6W8R1Y",
"C1X8V3N7M5K2Q9A"
]

# ===== HWID =====
def get_hwid():
    raw = str(uuid.getnode()) + os.getenv("COMPUTERNAME", "")
    return hashlib.sha256(raw.encode()).hexdigest()

KEY_FILE = os.path.join(BASE, "keys.json")

def load_keys():
    if not os.path.exists(KEY_FILE):
        return {}
    return json.load(open(KEY_FILE))

def save_keys(d):
    json.dump(d, open(KEY_FILE, "w"), indent=4)

# ===== AUTH =====
def auth():
    print("=== ENTER KEY ===")
    key = input("Key: ").strip()

    if key == DEV_KEY:
        print("DEV MODE ENABLED\n")
        return "dev"

    if key not in VALID_KEYS:
        print("Invalid key")
        input()
        sys.exit()

    data = load_keys()
    hwid = get_hwid()

    if key not in data:
        data[key] = hwid
        save_keys(data)
    elif data[key] != hwid:
        print("Key used on another PC")
        input()
        sys.exit()

    return "user"

# ===== GLOBAL STATS =====
checks = 0
found = 0
found_list = []

# ===== USERNAME =====
def gen():
    return ''.join(random.choices(string.ascii_lowercase + "_", k=4))

def check(name):
    url = "https://auth.roblox.com/v1/usernames/validate"
    try:
        r = requests.post(url, json={
            "username": name,
            "birthday": "2000-01-01T00:00:00.000Z",
            "context": 2
        }, timeout=5)
        return r.json().get("code") == 0
    except:
        return False

# ===== WORKER =====
def worker(_):
    global checks, found

    name = gen()
    checks += 1

    if check(name):
        found += 1
        found_list.append(name)

        print(f"[FOUND] {name}")

        with open(OUTPUT_FILE, "a") as f:
            f.write(name + "\n")

    if checks % 50 == 0:
        print(f"[STATS] Checked: {checks} | Found: {found}")

    time.sleep(0.5)

# ===== DEV DASHBOARD =====
def dev_ui():
    while True:
        os.system("cls")
        print("===== DEV DASHBOARD =====\n")
        print(f"Checks: {checks}")
        print(f"Found: {found}\n")

        print("Recent Finds:")
        for name in found_list[-10:]:
            print("-", name)

        time.sleep(2)

# ===== RUN =====
def run(mode):
    if mode == "dev":
        threading.Thread(target=dev_ui, daemon=True).start()

    with ThreadPoolExecutor(max_workers=5) as ex:
        while True:
            ex.map(worker, range(5))

# ===== MAIN =====
def main():
    mode = auth()
    run(mode)

if __name__ == "__main__":
    main()