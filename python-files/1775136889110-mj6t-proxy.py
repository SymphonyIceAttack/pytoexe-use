import requests
import time
import socket
import re
import os
import sys
import shutil
import qrcode
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import ping3

# ===================== НАСТРОЙКИ =====================
MTPROTO_SOURCES = [
    "https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt",
    "https://raw.githubusercontent.com/Grim1313/mtproto-for-telegram/master/all_proxies.txt",
    "https://raw.githubusercontent.com/Grim1313/mtproto-for-telegram/master/all_proxies.md",
    "https://raw.githubusercontent.com/ALIILAPRO/MTProtoProxy/main/mtproto.txt",
    "https://raw.githubusercontent.com/Argh94/Proxy-List/main/MTProto.txt",
]

TEST_TIMEOUT = 12
MAX_WORKERS = 100
TOP_QR_COUNT = 10  # сколько QR-кодов делать
# ====================================================

def get_base_dir():
    """Работает и в .py и в .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_mtproto_proxies():
    proxies = []
    print("Скачиваем свежие MTProto-прокси...")
    for url in MTPROTO_SOURCES:
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if re.match(r'^[a-zA-Z0-9\.\-]+:\d+:[a-fA-F0-9]+$', line):
                        proxies.append(line)
                    elif "server=" in line:
                        m = re.search(r'server=([^&]+)&port=(\d+)&secret=([a-fA-F0-9]+)', line)
                        if m:
                            proxies.append(f"{m.group(1)}:{m.group(2)}:{m.group(3)}")
        except:
            pass
    unique = list(dict.fromkeys(proxies))
    print(f"Найдено уникальных: {len(unique)}")
    return unique

def parse_proxy(proxy_str):
    try:
        parts = proxy_str.split(':')
        if len(parts) == 3:
            return parts[0].strip(), int(parts[1]), parts[2].strip()
    except:
        pass
    return None, None, None

def check_mtproto_proxy(proxy_str):
    server, port, secret = parse_proxy(proxy_str)
    if not server or not port:
        return None
    try:
        ping_time = ping3.ping(server, timeout=4, unit='ms')
        ping_time = round(ping_time, 1) if ping_time else None

        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TEST_TIMEOUT)
        result = sock.connect_ex((server, port))
        latency = round((time.time() - start) * 1000, 1)
        sock.close()

        if result == 0:
            sort_key = ping_time if ping_time is not None else latency + 10000
            return {
                "proxy": proxy_str,
                "server": server,
                "port": port,
                "secret": secret,
                "latency": latency,
                "ping": ping_time,
                "sort_key": sort_key
            }
    except:
        pass
    return None

def generate_qr(proxy_dict, rank, qr_dir):
    tg_link = f"tg://proxy?server={proxy_dict['server']}&port={proxy_dict['port']}&secret={proxy_dict['secret']}"
    qr = qrcode.QRCode(version=1, box_size=12, border=4)
    qr.add_data(tg_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"{rank:02d}_fastest.png"
    img.save(os.path.join(qr_dir, filename))

def main():
    base_dir = get_base_dir()
    qr_dir = os.path.join(base_dir, "QR_MTProto")

    # Очищаем старую папку с QR-кодами
    if os.path.exists(qr_dir):
        shutil.rmtree(qr_dir)
    os.makedirs(qr_dir, exist_ok=True)

    all_proxies = get_mtproto_proxies()
    if not all_proxies:
        print("Не удалось скачать прокси.")
        return

    print(f"\nПроверяем {len(all_proxies)} прокси...\n")
    working = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_mtproto_proxy, p): p for p in all_proxies}
        for future in tqdm(as_completed(futures), total=len(all_proxies), desc="Проверка"):
            result = future.result()
            if result:
                working.append(result)

    working.sort(key=lambda x: x["sort_key"])

    print(f"\n✅ Найдено рабочих: {len(working)}")

    # Сохраняем текстовые файлы
    with open(os.path.join(base_dir, "working_mtproto.txt"), "w", encoding="utf-8") as f:
        for p in working:
            ping_str = f"{p['ping']}ms" if p['ping'] is not None else "N/A"
            f.write(f"{p['server']}:{p['port']}:{p['secret']} | ping={ping_str} | latency={p['latency']}ms\n")

    with open(os.path.join(base_dir, "mtproto_for_telegram.txt"), "w", encoding="utf-8") as f:
        for p in working:
            f.write(f"tg://proxy?server={p['server']}&port={p['port']}&secret={p['secret']}\n")

    # Генерируем QR-коды топ-10
    print(f"\nГенерируем QR-коды (топ-{TOP_QR_COUNT}) → папка QR_MTProto")
    for rank, p in enumerate(working[:TOP_QR_COUNT], 1):
        generate_qr(p, rank, qr_dir)
        ping_str = f"{p['ping']}ms" if p['ping'] is not None else "N/A"
        print(f"  ✓ {rank:02d}. {p['server']}:{p['port']} → ping: {ping_str}")

    print("\nГотово! Открывай папку QR_MTProto и сканируй QR-коды телефоном.")

if __name__ == "__main__":
    main()