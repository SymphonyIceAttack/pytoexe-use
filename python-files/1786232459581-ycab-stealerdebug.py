import urllib.request
import json

WEBHOOK = "https://discord.com/api/webhooks/1535702294404931656/6SecH-rwfld_WKA6jS6z7vFsTx4iIYTQQ_SVjUj5V5ofO0MDuNzmVnTmyTV7m-ZIelJG"

def send_test():
    data = json.dumps({"content": "✅ Webhook is alive and working"}).encode()
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"✅ Success! Status: {response.status}")
            print("Check your Discord channel for the message.")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    send_test()