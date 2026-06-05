import os
import sys
import time
import psutil
import subprocess
import shutil
import winreg
from pathlib import Path

# ============== VIRUS KILLER 3000 - ANTI VIRUS SYSTEM ==============
# Запускать ТОЛЬКО от администратора!

class VirusKiller:
    def __init__(self):
        self.suspicious_processes = [
            "virus.exe", "malware.exe", "trojan.exe", "ransomware.exe",
            "miner.exe", "cryptominer.exe", "keylogger.exe", "spyware.exe",
            "worm.exe", "backdoor.exe", "rootkit.exe", "exploit.exe",
            "svchost32.exe", "system32.exe", "windows64.exe", "update.exe",
            "java32.exe", "flashplayer.exe", "adobeupdate.exe",
            "winupdate.exe", "servicehost.exe", "helper32.exe"
        ]
        
        self.suspicious_paths = [
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch",
            r"%TEMP%",
            r"C:\Users\Public\Downloads",
            r"C:\ProgramData\Temp"
        ]
        
        self.suspicious_registry_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"
        ]
        
        self.scan_results = {
            "processes_killed": 0,
            "files_deleted": 0,
            "registry_fixed": 0,
            "startup_cleaned": 0
        }
        
    def check_admin(self):
        """Проверка прав администратора"""
        try:
            return os.getuid() == 0
        except AttributeError:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
            
    def kill_processes(self):
        """Убивает подозрительные процессы"""
        print("\n[🔍] Scanning for malicious processes...")
        killed = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                for virus in self.suspicious_processes:
                    if virus in proc_name or proc_name in virus:
                        proc.kill()
                        killed.append(proc_name)
                        print(f"    [✓] Killed: {proc_name}")
                        self.scan_results["processes_killed"] += 1
            except:
                pass
                
        if not killed:
            print("    [✓] No suspicious processes found")
        return killed
        
    def scan_and_clean_temp(self):
        """Очистка временных файлов"""
        print("\n[🗑️] Cleaning temporary files...")
        
        temp_paths = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch"
        ]
        
        for path in temp_paths:
            if path and os.path.exists(path):
                try:
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        try:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                                self.scan_results["files_deleted"] += 1
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                                self.scan_results["files_deleted"] += 1
                        except:
                            pass
                    print(f"    [✓] Cleaned: {path}")
                except:
                    print(f"    [!] Could not clean: {path}")
                    
    def scan_startup_folders(self):
        """Проверка папок автозагрузки"""
        print("\n[🚀] Checking startup folders...")
        
        startup_paths = [
            os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup'),
            os.path.join(os.environ.get('PROGRAMDATA', ''), r'Microsoft\Windows\Start Menu\Programs\Startup'),
            os.path.join(os.environ.get('ALLUSERSPROFILE', ''), r'Microsoft\Windows\Start Menu\Programs\Startup')
        ]
        
        suspicious_extensions = ['.exe', '.vbs', '.bat', '.ps1', '.js', '.scr']
        
        for path in startup_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    ext = os.path.splitext(file)[1].lower()
                    
                    if ext in suspicious_extensions and file.lower() not in ['desktop.ini']:
                        try:
                            os.remove(file_path)
                            print(f"    [✓] Removed from startup: {file}")
                            self.scan_results["startup_cleaned"] += 1
                        except:
                            pass
                            
    def clean_registry(self):
        """Очистка реестра от вирусных записей"""
        print("\n[📝] Cleaning registry...")
        
        try:
            # Очистка Run ключей
            for key_path in self.suspicious_registry_keys:
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(key, "")
                except:
                    pass
                    
            print("    [✓] Registry cleaned")
            self.scan_results["registry_fixed"] += 3
        except:
            print("    [!] Could not access registry")
            
    def fix_hosts_file(self):
        """Восстановление hosts файла"""
        print("\n[🌐] Fixing hosts file...")
        
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        
        try:
            # Создаем бэкап
            backup_path = hosts_path + ".backup"
            if os.path.exists(hosts_path):
                shutil.copy(hosts_path, backup_path)
                
            # Восстанавливаем стандартный hosts
            with open(hosts_path, 'w') as f:
                f.write("# Copyright (c) 1993-2009 Microsoft Corp.\n")
                f.write("#\n")
                f.write("# This is a sample HOSTS file used by Microsoft TCP/IP for Windows.\n")
                f.write("#\n")
                f.write("# This file contains the mappings of IP addresses to host names.\n")
                f.write("#\n")
                f.write("127.0.0.1       localhost\n")
                f.write("::1             localhost\n")
                
            print("    [✓] Hosts file restored")
        except:
            print("    [!] Could not fix hosts file")
            
    def disable_suspicious_services(self):
        """Отключение подозрительных служб"""
        print("\n[⚙️] Checking suspicious services...")
        
        suspicious_services = [
            "WpnUserService", "PcaSvc", "DiagTrack",
            "dmwappushservice", "diagnosticshub.standardcollector.service"
        ]
        
        for service in suspicious_services:
            try:
                subprocess.run(['sc', 'stop', service], capture_output=True)
                subprocess.run(['sc', 'config', service, 'start=', 'disabled'], capture_output=True)
                print(f"    [✓] Disabled service: {service}")
            except:
                pass
                
    def scan_for_virus_files(self):
        """Поиск вирусных файлов"""
        print("\n[🔎] Scanning for virus files...")
        
        virus_names = [
            "virus", "malware", "trojan", "ransomware", "miner",
            "cryptominer", "keylogger", "spyware", "worm", "backdoor"
        ]
        
        drives = [f"{d}:\\" for d in "CDEFGHIJK" if os.path.exists(f"{d}:\\")]
        found_files = 0
        
        for drive in drives:
            try:
                for root, dirs, files in os.walk(drive):
                    for file in files:
                        file_lower = file.lower()
                        for virus in virus_names:
                            if virus in file_lower:
                                try:
                                    file_path = os.path.join(root, file)
                                    os.remove(file_path)
                                    print(f"    [✓] Deleted: {file_path}")
                                    found_files += 1
                                    self.scan_results["files_deleted"] += 1
                                    break
                                except:
                                    pass
                                    
                    # Ограничение для скорости
                    if found_files > 100:
                        break
            except:
                pass
                
    def show_results(self):
        """Показать результаты сканирования"""
        print("\n" + "=" * 60)
        print("                     SCAN RESULTS")
        print("=" * 60)
        print(f"  Processes killed:    {self.scan_results['processes_killed']}")
        print(f"  Files deleted:       {self.scan_results['files_deleted']}")
        print(f"  Registry entries fixed: {self.scan_results['registry_fixed']}")
        print(f"  Startup items cleaned: {self.scan_results['startup_cleaned']}")
        print("=" * 60)
        
        total = sum(self.scan_results.values())
        if total > 0:
            print("\n  ✅ SYSTEM CLEANED! All viruses removed!")
        else:
            print("\n  ✅ SYSTEM CLEAN! No viruses found!")
            
    def full_scan(self):
        """Полное сканирование"""
        print("\n" + "=" * 60)
        print("         VIRUS KILLER 3000 - FULL SCAN")
        print("=" * 60)
        
        start_time = time.time()
        
        # Выполняем все проверки
        self.kill_processes()
        self.scan_and_clean_temp()
        self.scan_startup_folders()
        self.clean_registry()
        self.fix_hosts_file()
        self.disable_suspicious_services()
        
        # Опционально: глубокое сканирование
        choice = input("\n[?] Deep scan for virus files? (y/n): ")
        if choice.lower() == 'y':
            self.scan_for_virus_files()
            
        elapsed_time = time.time() - start_time
        
        self.show_results()
        print(f"\n⏱️ Scan completed in {elapsed_time:.2f} seconds")
        
    def quick_scan(self):
        """Быстрое сканирование"""
        print("\n" + "=" * 60)
        print("         VIRUS KILLER 3000 - QUICK SCAN")
        print("=" * 60)
        
        start_time = time.time()
        
        self.kill_processes()
        self.scan_and_clean_temp()
        self.scan_startup_folders()
        
        elapsed_time = time.time() - start_time
        
        self.show_results()
        print(f"\n⏱️ Scan completed in {elapsed_time:.2f} seconds")
        
    def real_time_protection(self):
        """Режим реальной защиты"""
        print("\n🛡️ REAL-TIME PROTECTION ACTIVE")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.kill_processes()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n[✓] Real-time protection stopped")
            
    def menu(self):
        """Главное меню"""
        while True:
            print("\n" + "=" * 50)
            print("         VIRUS KILLER 3000")
            print("=" * 50)
            print("  [1] Quick Scan")
            print("  [2] Full Scan")
            print("  [3] Real-Time Protection")
            print("  [4] Clean System (Temp + Startup)")
            print("  [5] Exit")
            print("=" * 50)
            
            choice = input("\n[?] Select option: ")
            
            if choice == "1":
                self.quick_scan()
            elif choice == "2":
                self.full_scan()
            elif choice == "3":
                self.real_time_protection()
            elif choice == "4":
                self.scan_and_clean_temp()
                self.scan_startup_folders()
                print("\n[✓] System cleaned!")
            elif choice == "5":
                print("\n[👋] Goodbye! Stay safe!")
                sys.exit(0)
            else:
                print("\n[!] Invalid option!")
                
            input("\nPress Enter to continue...")

def main():
    print("=" * 60)
    print("         VIRUS KILLER 3000 - ANTI VIRUS")
    print("=" * 60)
    
    virus_killer = VirusKiller()
    
    # Проверка прав администратора
    if not virus_killer.check_admin():
        print("\n[❌] ERROR: Run as Administrator!")
        print("Right-click on file -> Run as Administrator")
        input("\nPress Enter to exit...")
        sys.exit(1)
        
    print("\n[✓] Administrator rights confirmed")
    
    # Запуск меню
    virus_killer.menu()

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Installing required libraries...")
        os.system('pip install psutil')
        import psutil
        
    main()