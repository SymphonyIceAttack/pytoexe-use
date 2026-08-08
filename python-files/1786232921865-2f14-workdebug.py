import urllib.request
import json

WEBHOOK = "https://discord.com/api/webhooks/1533951598827667627/uv3B3-C0D0lKs9I3RZs_Vuww8TrZ9qG_3hegvvwsRmBuUzpJhDM6JHgSAuH542aeQPyf"

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