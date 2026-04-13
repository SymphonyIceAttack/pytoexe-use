import os
os.system("pip install requests")

import socket
import ipaddress
import concurrent.futures
import json
import requests
import uuid
import threading

OUTPUT_FILE = "network_devices.json"

PORTS = [80, 443, 8080, 554]
TIMEOUT = 0.5
MAX_WORKERS = 80

print_lock = threading.Lock()


# ---------------------------
# 🌐 свой IP
# ---------------------------
def get_own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


# ---------------------------
# 🌐 сеть
# ---------------------------
def get_network():
    ip = get_own_ip()
    return ipaddress.IPv4Network(f"{ip}/24", strict=False)


# ---------------------------
# 🟢 MAC self
# ---------------------------
def get_self_mac():
    h = uuid.getnode()
    mac = ":".join([f"{(h >> i) & 0xff:02x}" for i in range(40, -1, -8)])
    return mac.upper()


# ---------------------------
# 📡 MAC other (fake fallback)
# ---------------------------
def get_mac(ip):
    h = uuid.uuid5(uuid.NAMESPACE_DNS, ip).hex
    return ":".join([h[i:i+2] for i in range(0, 12, 2)]).upper()


# ---------------------------
# 🔎 host check
# ---------------------------
def check_host(ip):
    ip = str(ip)

    for port in PORTS:
        try:
            s = socket.socket()
            s.settimeout(TIMEOUT)

            if s.connect_ex((ip, port)) == 0:
                s.close()
                return ip

            s.close()
        except:
            pass

    return None


# ---------------------------
# 🌐 name
# ---------------------------
def get_name(ip):
    try:
        r = requests.get(f"http://{ip}", timeout=0.8)

        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding or "utf-8"

        text = r.text

        start = text.lower().find("<title>")
        end = text.lower().find("</title>")

        if start != -1 and end != -1:
            return text[start + 7:end].strip()

    except:
        pass

    return None


# ---------------------------
# 🧠 type
# ---------------------------
def detect_type(name):
    if not name:
        return "web"

    n = name.lower()

    if any(x in n for x in ["camera", "hikvision", "dahua", "rtsp"]):
        return "camera"

    if any(x in n for x in ["esp", "iot", "xiaomi", "smart"]):
        return "iot"

    return "web"


# ---------------------------
# 🟢 self device
# ---------------------------
def get_self_device():
    ip = get_own_ip()
    mac = get_self_mac()

    return {
        "id": "dev_self",
        "name": f"This Device ({mac})",
        "ip": ip,
        "url": f"http://{ip}",
        "type": "self"
    }


# ---------------------------
# 🚀 scan
# ---------------------------
def scan():
    net = get_network()
    own_ip = get_own_ip()

    print(f"\n🌐 Network: {net}")
    print(f"🟢 Self IP: {own_ip}")
    print(f"🏷 Self MAC: {get_self_mac()}")
    print("-" * 50)

    sections = {
        "self": {
            "id": "section_0",
            "name": "Моё устройство",
            "devices": [get_self_device()]
        },
        "camera": {
            "id": "section_1",
            "name": "Камеры видеонаблюдения",
            "devices": []
        },
        "iot": {
            "id": "section_2",
            "name": "Умный дом / IoT",
            "devices": []
        },
        "web": {
            "id": "section_3",
            "name": "Веб устройства",
            "devices": []
        }
    }

    found_devices = []
    i = 1

    def process(ip):
        nonlocal i

        mac = get_mac(ip)
        name = get_name(ip)

        if not name:
            name = f"Device {ip}"

        name = f"{name} ({mac})"

        dtype = detect_type(name)

        device = {
            "id": f"dev_{i}",
            "name": name,
            "ip": ip,
            "url": f"http://{ip}"
        }

        sections[dtype]["devices"].append(device)

        # 🔥 LIVE OUTPUT
        with print_lock:
            print(f"[+] {ip} → {name} ({dtype})")

        i += 1

        return device


    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(check_host, str(ip)) for ip in net.hosts()]

        for f in concurrent.futures.as_completed(futures):
            ip = f.result()
            if not ip:
                continue

            process(ip)

    print("\n" + "-" * 50)
    print("🟢 Scan finished")

    return list(sections.values())


# ---------------------------
# 💾 save
# ---------------------------
def save(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------
# main
# ---------------------------
if __name__ == "__main__":
    result = scan()
    save(result)

    print(f"\n✅ Saved: {OUTPUT_FILE}")