import socket
import psutil
import platform
import csv
import re
from datetime import datetime

def get_cpu_info():
    """Lấy tên đầy đủ của CPU (Ví dụ: Intel Core i5-10400)"""
    # Trên Windows, platform.processor() đôi khi không đầy đủ, dùng thêm mẹo này
    cpu_name = platform.processor()
    if platform.system() == "Windows":
        import subprocess
        try:
            command = "wmic cpu get name"
            cpu_name = subprocess.check_output(command, shell=True).decode().strip().split('\n')[1]
        except:
            pass
    return cpu_name

def collect_data():
    # 1. Tên máy & OS
    hostname = socket.gethostname()
    os_ver = f"{platform.system()} {platform.release()}"
    
    # 2. CPU & RAM
    cpu_detail = get_cpu_info()
    # Tính RAM (Bytes -> GB), làm tròn 2 chữ số thập phân
    total_ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    
    # 3. Network (Wi-Fi & LAN)
    net_interfaces = psutil.net_if_addrs()
    target_keys = ['wi-fi', 'ethernet', 'lan', 'en', 'eth', 'wlan']
    
    # Khởi tạo giá trị trống để tránh lỗi cột
    lan_ip = "N/A"; lan_mac = "N/A"
    wifi_ip = "N/A"; wifi_mac = "N/A"
    
    for name, addrs in net_interfaces.items():
        name_l = name.lower()
        ip = "N/A"
        mac = "N/A"
        
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
            elif addr.family == psutil.AF_LINK or (platform.system() == 'Windows' and addr.family == -1):
                mac = addr.address
        
        # Phân loại dựa trên tên Interface
        if any(k in name_l for k in ['wi-fi', 'wlan']):
            wifi_ip, wifi_mac = ip, mac
        elif any(k in name_l for k in ['ethernet', 'lan', 'eth', 'en']):
            lan_ip, lan_mac = ip, mac

    # Trả về một Dictionary để xuất file dạng cột
    return {
        "Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "Computer_Name": hostname,
        "OS_Version": os_ver,
        "CPU_Model": cpu_detail,
        "RAM_GB": f"{total_ram_gb} GB",
        "LAN_IP": lan_ip,
        "LAN_MAC": lan_mac,
        "WiFi_IP": wifi_ip,
        "WiFi_MAC": wifi_mac
    }

def save_to_csv(data):
    filename = f"Report_{socket.gethostname()}.csv"
    headers = data.keys()
    
    try:
        with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow(data)
        print(f"[+] Đã trích xuất xong: {filename}")
    except Exception as e:
        print(f"[-] Lỗi: {e}")

if __name__ == "__main__":
    info = collect_data()
    save_to_csv(info)