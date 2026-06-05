# -*- coding: utf-8 -*-
import subprocess
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ======================== НАСТРОЙКИ ========================
PING_TIMEOUT = 0.3
PORT_TIMEOUT = 0.2
MAX_WORKERS = 50

CRITICAL_PORTS = {
    22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS", 554: "RTSP",
    445: "SMB", 3389: "RDP", 8000: "Hikvision", 37777: "Dahua",
    2020: "TP-Link", 9000: "Reolink", 161: "SNMP", 9100: "Printer"
}

DEVICE_MAP = {
    "Hikvision Camera": {"ports": [8000, 554], "type": "IP-камера", "poe": "PoE", "models": ["DS-2CD", "DS-2DE"]},
    "Dahua Camera": {"ports": [37777, 554], "type": "IP-камера", "poe": "PoE", "models": ["IPC-HFW", "XVR"]},
    "TP-Link VIGI": {"ports": [2020, 554], "type": "IP-камера PoE", "poe": "PoE", "models": ["VIGI C340"]},
    "TP-Link Tapo": {"ports": [2020], "type": "IP-камера Wi-Fi", "poe": "Нет", "models": ["Tapo C200"]},
    "Reolink": {"ports": [9000, 554], "type": "IP-камера", "poe": "PoE", "models": ["RLC-410"]},
    "Axis": {"ports": [8080, 554], "type": "IP-камера PoE", "poe": "PoE", "models": ["M10", "P13"]},
    "Cisco Catalyst PoE": {"ports": [22, 23], "type": "Коммутатор PoE+", "poe": "PoE+", "models": ["2960-POE"]},
    "D-Link PoE": {"ports": [80, 23], "type": "Коммутатор PoE", "poe": "PoE", "models": ["DGS-1210-28P"]},
    "TP-Link PoE": {"ports": [80, 23], "type": "Коммутатор PoE", "poe": "PoE", "models": ["TL-SG3428P"]},
    "Huawei PoE": {"ports": [22, 23], "type": "Коммутатор PoE", "poe": "PoE", "models": ["S5700-POE"]},
    "Juniper PoE": {"ports": [22, 830], "type": "Коммутатор PoE", "poe": "PoE", "models": ["EX2200-POE"]},
    "Windows PC": {"ports": [445, 3389], "type": "Компьютер", "os": "Windows", "poe": "Нет"},
    "Linux PC": {"ports": [22, 111], "type": "Компьютер", "os": "Linux", "poe": "Нет"},
    "HP Printer": {"ports": [9100, 515], "type": "Принтер", "poe": "Нет"},
    "Synology NAS": {"ports": [5000, 5001], "type": "NAS", "poe": "Нет"}
}

def fast_ping(ip):
    try:
        if sys.platform == 'win32':
            cmd = ['ping', '-n', '1', '-w', '300', ip]
        else:
            cmd = ['ping', '-c', '1', '-W', '1', ip]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
        return result.returncode == 0
    except:
        return False

def fast_scan_ports(ip):
    open_ports = []
    for port in CRITICAL_PORTS.keys():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(PORT_TIMEOUT)
            if sock.connect_ex((ip, port)) == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    return open_ports

def identify_fast(open_ports):
    if not open_ports:
        return None, 0
    best_match = None
    best_score = 0
    for device_name, device_info in DEVICE_MAP.items():
        expected_ports = device_info['ports']
        matched = [p for p in expected_ports if p in open_ports]
        score = len(matched) * 100 // len(expected_ports) if expected_ports else 0
        if 8000 in open_ports:
            score += 20
        if 37777 in open_ports:
            score += 20
        if 2020 in open_ports:
            score += 15
        if score > best_score and score >= 30:
            best_score = score
            best_match = device_info
            best_match['name'] = device_name
    return best_match, best_score

def quick_analyze(ip):
    result = {'ip': ip, 'status': 'СВОБОДЕН', 'type': '-', 'name': '-', 'model': '-', 'ping': '-', 'power': '-', 'ports': []}
    if not fast_ping(ip):
        return result
    open_ports = fast_scan_ports(ip)
    if not open_ports:
        result['status'] = 'ЗАНЯТ'
        result['type'] = 'Хост доступен'
        result['name'] = 'Порты закрыты'
        return result
    device, confidence = identify_fast(open_ports)
    result['status'] = 'ЗАНЯТ'
    result['ports'] = [f"{p}({CRITICAL_PORTS.get(p, '?')})" for p in open_ports[:8]]
    if device:
        result['type'] = device.get('type', 'Устройство')
        result['name'] = device.get('name', 'Неизвестно')
        result['model'] = device.get('models', ['-'])[0]
        result['power'] = device.get('poe', 'Неизвестно')
    else:
        if 554 in open_ports:
            result['type'] = "IP-камера"
            result['name'] = "Неизвестный производитель"
            result['power'] = "PoE (вероятно)"
        elif 445 in open_ports or 3389 in open_ports:
            result['type'] = "Компьютер"
            result['name'] = "Windows"
            result['power'] = "Обычное"
        else:
            result['type'] = "Сетевое устройство"
            result['name'] = "Не идентифицировано"
    return result

def scan_network_parallel(ip_list):
    results = []
    total = len(ip_list)
    print("\n" + "="*70)
    print(" БЫСТРОЕ СКАНИРОВАНИЕ СЕТИ")
    print("="*70)
    print(f" Всего адресов: {total}")
    print("="*70 + "\n")
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(quick_analyze, ip): ip for ip in ip_list}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            results.append(result)
            progress = int(completed / total * 40)
            bar = "[" + "#" * progress + "." * (40 - progress) + "]"
            icon = "📷" if result['status'] == 'ЗАНЯТ' and 'камера' in result['type'].lower() else "💻" if result['status'] == 'ЗАНЯТ' else "⚪"
            sys.stdout.write(f"\r Прогресс: {bar} {completed}/{total} {icon} {result['ip'][:15]}")
            sys.stdout.flush()
    print(f"\n\n ✅ Завершено за {time.time() - start_time:.1f} сек\n")
    return results

def print_results(results):
    occupied = [r for r in results if r['status'] == 'ЗАНЯТ']
    free = [r for r in results if r['status'] == 'СВОБОДЕН']
    cameras = [r for r in occupied if 'камера' in r['type'].lower()]
    switches = [r for r in occupied if 'коммутатор' in r['type'].lower()]
    print("="*70)
    print(" РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("="*70)
    print(f"\n 📊 Всего: {len(results)} | Занято: {len(occupied)} | Свободно: {len(free)} | Камер: {len(cameras)} | Коммутаторов: {len(switches)}\n")
    if cameras:
        print(" 🎥 IP-КАМЕРЫ:")
        for i, cam in enumerate(cameras, 1):
            print(f"\n {i}. {cam['ip']}")
            print(f"    Производитель: {cam['name']}")
            print(f"    Модель: {cam['model']}")
            print(f"    Питание: {cam['power']}")
    if switches:
        print("\n 🔌 КОММУТАТОРЫ:")
        for i, sw in enumerate(switches, 1):
            print(f"\n {i}. {sw['ip']}")
            print(f"    Производитель: {sw['name']}")
            print(f"    Модель: {sw['model']}")
            print(f"    Питание: {sw['power']}")
    if free:
        print("\n ✨ СВОБОДНЫЕ IP:")
        free_ips = [f"  {r['ip']}" for r in free[:20]]
        for i in range(0, len(free_ips), 5):
            print("".join(free_ips[i:i+5]))
        if len(free) > 20:
            print(f"  ... и еще {len(free)-20} адресов")
    print("\n" + "="*70)

def parse_ip_range(user_input):
    ip_list = []
    if '-' in user_input:
        parts = user_input.split('-')
        base_part = parts[0]
        if '.' in base_part:
            last_dot = base_part.rfind('.')
            base_ip = base_part[:last_dot + 1]
            start_num = int(base_part[last_dot + 1:])
            end_num = int(parts[1])
            if end_num - start_num > 100:
                print(f"\n ⚠️ Ограничиваем до 100 адресов")
                end_num = start_num + 100
            for i in range(start_num, min(end_num + 1, 255)):
                ip_list.append(f"{base_ip}{i}")
    elif '.' in user_input and user_input.count('.') == 3:
        ip_list.append(user_input)
    return ip_list

def main():
    try:
        import os
        os.system('cls' if sys.platform == 'win32' else 'clear')
        print("="*70)
        print("        ⚡ БЫСТРЫЙ АНАЛИЗАТОР СЕТИ v3.0")
        print("="*70)
        print("\n Введите IP или диапазон (пример: 192.168.1.1-50)\n")
        user_input = input(" > ").strip()
        if not user_input:
            print("\n Ошибка!")
            input("\n Нажмите Enter...")
            return
        ip_list = parse_ip_range(user_input)
        if not ip_list:
            print("\n Ошибка формата!")
            input("\n Нажмите Enter...")
            return
        results = scan_network_parallel(ip_list)
        print_results(results)
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Отчет: {datetime.now()}\n")
            for r in results:
                f.write(f"{r['ip']} - {r['status']} - {r['type']} - {r['name']}\n")
        print(f"\n 💾 Отчет: {filename}")
    except Exception as e:
        print(f"\n Ошибка: {e}")
    input("\n Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()