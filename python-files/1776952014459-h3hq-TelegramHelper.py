from tokenize import endpats

import requests
import random
import time
from colorama import Fore, init
from concurrent.futures import ThreadPoolExecutor

init(autoreset=True)

def print_banner():
    print(Fore.RED + """
KARATEL.TOOL
""")

# Список из 50 вымышленных прокси (замените на реальные)
PROXY_LIST = [
    "http://103.123.45.67:8080",
    "http://112.234.56.78:3128",
    "http://121.345.67.89:80",
    "http://130.456.78.90:8080",
    "http://142.567.89.01:3128",
    "http://151.678.90.12:80",
    "http://163.789.01.23:8080",
    "http://172.890.12.34:3128",
    "http://181.901.23.45:80",
    "http://190.012.34.56:8080",
    "http://202.123.45.67:3128",
    "http://211.234.56.78:80",
    "http://220.345.67.89:8080",
    "http://233.456.78.90:3128",
    "http://242.567.89.01:80",
    "http://251.678.90.12:8080",
    "http://260.789.01.23:3128",
    "http://273.890.12.34:80",
    "http://282.901.23.45:8080",
    "http://291.012.34.56:3128",
    "http://300.123.45.67:80",
    "http://312.234.56.78:8080",
    "http://321.345.67.89:3128",
    "http://330.456.78.90:80",
    "http://343.567.89.01:8080",
    "http://352.678.90.12:3128",
    "http://361.789.01.23:80",
    "http://370.890.12.34:8080",
    "http://383.901.23.45:3128",
    "http://392.012.34.56:80",
    "http://401.123.45.67:8080",
    "http://410.234.56.78:3128",
    "http://423.345.67.89:80",
    "http://432.456.78.90:8080",
    "http://441.567.89.01:3128",
    "http://450.678.90.12:80",
    "http://463.789.01.23:8080",
    "http://472.890.12.34:3128",
    "http://481.901.23.45:80",
    "http://490.012.34.56:8080",
    "http://503.123.45.67:3128",
    "http://512.234.56.78:80",
    "http://521.345.67.89:8080",
    "http://530.456.78.90:3128",
    "http://543.567.89.01:80",
    "http://552.678.90.12:8080",
    "http://561.789.01.23:3128",
    "http://570.890.12.34:80",
    "http://583.901.23.45:8080",
    "http://592.012.34.56:3128"
]

def send_complaint(username, proxy):
    try:
        proxies = {'http': proxy, 'https': proxy}
        url = f"https://telegram.org/support/report_user?username={username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        response = requests.get(url, proxies=proxies, headers=headers, timeout=5)
        if response.status_code == 200:
            print(Fore.GREEN + f"[+] Жалоба отправлена с {proxy}")
            return True
        else:
            print(Fore.YELLOW + f"[!] Ошибка {response.status_code} с {proxy}")
            return False
    except Exception as e:
        print(Fore.RED + f"[-] Ошибка с {proxy}: {str(e)}")
        return False

def main():
    print_banner()
    username = input(Fore.CYAN + "Введите юзернейм Telegram: ")
    count = int(input(Fore.CYAN + "Сколько жалоб отправить? "))
    threads = int(input(Fore.CYAN + "Сколько потоков использовать? (макс 50) "))

    print(Fore.MAGENTA + f"\n[!] Запускаю атаку на {username}...")
    time.sleep(1)

    success = 0
    with ThreadPoolExecutor(max_workers=threads) as executor:  # Вот это исправил!
        for _ in range(count):
            proxy = random.choice(PROXY_LIST)
            executor.submit(send_complaint, username, proxy)
            time.sleep(0.1)  # Чтобы не спалить прокси

    print(Fore.YELLOW + "\n[!] Атака завершена. Рекомендую сменить IP.")

if __name__ == "__main__":
    main()
