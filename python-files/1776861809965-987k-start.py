import os
import subprocess
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(command):
    try:
        # Выполняем команду и ждем завершения
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения: {e}")
        return False

def set_static():
    adapter = input("\nВведите название адаптера (обычно Ethernet): ") or "Ethernet"
    
    print(f" Настраиваю IPv4 для {adapter}...")
    # IP, Маска, Шлюз
    cmd_ip = f'netsh interface ipv4 set address name="{adapter}" static 176.221.21.62 255.255.255.252 176.221.21.61'
    # DNS 1
    cmd_dns1 = f'netsh interface ipv4 set dns name="{adapter}" static 81.23.96.138 primary'
    # DNS 2
    cmd_dns2 = f'netsh interface ipv4 add dns name="{adapter}" 81.23.99.2 index=2'
    
    # Отключение IPv6 через PowerShell
    cmd_ipv6 = f'powershell -Command "Disable-NetAdapterBinding -Name \'{adapter}\' -ComponentID ms_tcpip6"'

    if run_command(cmd_ip) and run_command(cmd_dns1) and run_command(cmd_dns2):
        run_command(cmd_ipv6)
        print("[OK] Настройки успешно применены. IPv6 отключен.")
    else:
        print("[!] Произошла ошибка. Проверьте название адаптера.")

def set_dhcp():
    adapter = input("\nВведите название адаптера (обычно Ethernet): ") or "Ethernet"
    print(f" Сброс настроек для {adapter}...")
    
    cmd_ip_dhcp = f'netsh interface ipv4 set address name="{adapter}" source=dhcp'
    cmd_dns_dhcp = f'netsh interface ipv4 set dns name="{adapter}" source=dhcp'
    cmd_ipv6_on = f'powershell -Command "Enable-NetAdapterBinding -Name \'{adapter}\' -ComponentID ms_tcpip6"'

    if run_command(cmd_ip_dhcp) and run_command(cmd_dns_dhcp):
        run_command(cmd_ipv6_on)
        print("[OK] Настройки сброшены на DHCP. IPv6 включен.")
    else:
        print("[!] Произошла ошибка.")

def run_ping():
    print("\n" + "="*40)
    print("ЗАМЕР PING: 85.235.192.2 BY @DEVELOP40")
    print("="*40)
    # Пакет 1450 байт, 100 раз
    os.system("ping 85.235.192.2 -l 1450 -n 100")

def main_menu():
    if not is_admin():
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ОШИБКА: ЗАПУСТИТЕ PYTHON ОТ ИМЕНИ АДМИНИСТРАТОРА")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        input("Нажмите Enter для выхода...")
        return

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("======================================================")
        print("          СЕТЕВЫЕ НАСТРОЙКИ BY @DEVELOP40          ")
        print("======================================================")
        print("1) Прописать настройки сети:")
        print("   IP: 176.221.21.62, GW: 176.221.21.61")
        print("   DNS: 81.23.96.138, 81.23.99.2")
        print("   (IPv6 будет ОТКЛЮЧЕН)")
        print("\n2) Очистить настройки (DHCP / По умолчанию)")
        print("\n3) Замеры Ping (85.235.192.2 -l 1450 -n 100)")
        print("\n0) Выход")
        print("======================================================")
        print("Разработано: @develop40")
        
        choice = input("\nВыберите пункт: ")

        if choice == '1':
            set_static()
            input("\nНажмите Enter, чтобы вернуться в меню...")
        elif choice == '2':
            set_dhcp()
            input("\nНажмите Enter, чтобы вернуться в меню...")
        elif choice == '3':
            run_ping()
            input("\nНажмите Enter, чтобы вернуться в меню...")
        elif choice == '0':
            break

if __name__ == "__main__":
    main_menu()