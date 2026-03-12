# JANUS VPN LAUNCHER - ФИНАЛ
import socket
import socks
import requests
import sys
import os
import time

def resource_path(relative_path):
    """Для корректной работы файлов после компиляции"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("""
    ╔════════════════════════════════════════╗
    ║     🔥 JANUS/TESAVEK VPN v2.0 🔥       ║
    ║        Никаких ограничений             ║
    ║        Только чистая анонимность       ║
    ╚════════════════════════════════════════╝
    """)
    
    # Бесплатные тестовые прокси
    proxies = [
        {"ip": "185.165.29.101", "port": 1080, "proto": "socks5"},
        {"ip": "45.155.205.233", "port": 1080, "proto": "socks5"},
        {"ip": "213.183.57.101", "port": 1080, "proto": "socks5"},
        {"ip": "185.165.31.40", "port": 1080, "proto": "socks5"},
        {"ip": "46.17.108.10", "port": 1080, "proto": "socks5"}
    ]
    
    print("Доступные прокси:")
    for i, p in enumerate(proxies, 1):
        print(f"{i}. {p['ip']}:{p['port']} ({p['proto']})")
    print("6. Свой вариант")
    
    try:
        choice = input("\nВыбери номер (1-6): ").strip()
        
        if choice == "6":
            ip = input("Введи IP: ").strip()
            port = int(input("Введи порт: ").strip())
            proto = input("Тип (socks5/socks4/http): ").strip() or "socks5"
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(proxies):
                ip = proxies[idx]["ip"]
                port = proxies[idx]["port"]
                proto = proxies[idx]["proto"]
            else:
                print("❌ Неверный выбор!")
                return
        
        print(f"\n[+] Подключаюсь к {ip}:{port} через {proto}...")
        
        # Сохраняем оригинальный socket
        original_socket = socket.socket
        
        # Настройка прокси
        if proto == "socks5":
            socks.set_default_proxy(socks.SOCKS5, ip, port)
        elif proto == "socks4":
            socks.set_default_proxy(socks.SOCKS4, ip, port)
        else:
            socks.set_default_proxy(socks.HTTP, ip, port)
            
        socket.socket = socks.socksocket
        
        # Проверка подключения
        print("[*] Проверяю соединение...")
        r = requests.get("https://api.ipify.org?format=json", timeout=10)
        data = r.json()
        current_ip = data.get('ip', 'неизвестно')
        
        print(f"\n✅ УСПЕХ! Твой внешний IP: {current_ip}")
        print("\n🔒 VPN активен. Нажми Ctrl+C для отключения.")
        
        # Держим соединение
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n[!] Отключаю VPN...")
        socket.socket = original_socket
        print("✅ VPN отключен. До встречи!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        socket.socket = original_socket

if __name__ == "__main__":
    main()