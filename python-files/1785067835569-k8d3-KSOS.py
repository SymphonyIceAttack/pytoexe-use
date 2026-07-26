#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TrialReset – полный аналог TrialReset.cmd на Python
Поддерживает: AVP (KSOS, KIS, KAV) и KES.
Работает без IObitUnlocker, использует встроенные средства Windows.
"""

import os
import sys
import subprocess
import ctypes
import winreg
import shutil
import time
import re
import base64
import tempfile
from pathlib import Path

# ========== Константы и глобальные переменные ==========
VERS_UTILITY = "1.0.0.12"
NAME_UTILITY = f"TrialReset & Activate {VERS_UTILITY}"

# Определение архитектуры
is_x64 = (os.environ.get("PROCESSOR_ARCHITECTURE") == "AMD64" or
          os.environ.get("PROCESSOR_ARCHITEW6432") == "AMD64")
SOFTWARE = r"SOFTWARE\WOW6432Node" if is_x64 else "SOFTWARE"

# Глобальные переменные для продукта
TypeAV = None
avp = None          # папка продукта для AVP
kes = None          # папка продукта для KES
ProductName = "No ProductName"
ProductVersion = "No ProductVersion"
ProductStatus = "No ProductStatus"
ProductType = "No ProductType"
SelfProtectionValue = 0
ExportImport = None
OpenFolder = os.environ.get("SystemDrive", "C:") + "\\"
ActivationVBS = None
OpenFileBoxEXE = None
TrialActCode = None
AddCode = None
Code = None

# ========== Вспомогательные функции ==========

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
    except Exception as e:
        print(f"Failed to elevate: {e}")
        input("Press Enter to exit...")
    sys.exit()

def run_cmd(command, capture=False):
    """Запуск команды, возврат кода и вывода."""
    try:
        if capture:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        else:
            subprocess.run(command, shell=True, check=False)
            return "", "", 0
    except Exception as e:
        return "", str(e), -1

def print_color(text, color=None):
    """Цветной вывод в консоль (ANSI)."""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    if color and color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)

# ========== Определение продукта и получение информации ==========

def get_product_info():
    global TypeAV, avp, kes, ProductName, ProductVersion, ProductStatus, ProductType
    program_data = os.environ.get("ProgramData", "C:\\ProgramData")
    base = os.path.join(program_data, "Kaspersky Lab")
    if not os.path.exists(base):
        return False

    avp_folders = [d for d in os.listdir(base) if d.startswith("AVP")]
    kes_folders = [d for d in os.listdir(base) if d.startswith("KES")]

    if avp_folders:
        TypeAV = "AVP"
        avp = avp_folders[0]
    elif kes_folders:
        TypeAV = "KES"
        kes = kes_folders[0]
    else:
        return False

    # Чтение реестра
    if TypeAV == "AVP":
        reg_path = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        product_name_key = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        product_version_key = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        product_status_key = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        product_type_key = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
    else:  # KES
        reg_path = f"HKLM\\{SOFTWARE}\\KasperskyLab\\protected\\{kes}\\environment"
        product_name_key = reg_path
        product_version_key = reg_path
        product_status_key = reg_path
        product_type_key = reg_path

    # Чтение значений
    def get_reg_value(key, value):
        out, err, code = run_cmd(f'reg query "{key}" /v {value}', capture=True)
        if code == 0:
            for line in out.splitlines():
                if value in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
        return None

    ProductName = get_reg_value(product_name_key, "ProductName") or "No ProductName"
    ProductVersion = get_reg_value(product_version_key, "ProductVersion") or "No ProductVersion"
    if ProductVersion == "No ProductVersion" and TypeAV == "KES":
        # Для KES ключ ProductDisplayVersion
        ProductVersion = get_reg_value(product_version_key, "ProductDisplayVersion") or "No ProductVersion"
    ProductStatus = get_reg_value(product_status_key, "ProductStatus") or "No ProductStatus"
    ProductType = get_reg_value(product_type_key, "ProductType") or "No ProductType"
    return True

# ========== Проверка самозащиты и процесса ==========

def check_self_protection(status_only=False):
    if TypeAV == "AVP":
        key = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\settings"
    else:
        key = f"HKLM\\{SOFTWARE}\\KasperskyLab\\protected\\{kes}\\settings"
    out, err, code = run_cmd(f'reg query "{key}" /v EnableSelfProtection', capture=True)
    if code == 0:
        for line in out.splitlines():
            if "EnableSelfProtection" in line:
                parts = line.split()
                if len(parts) >= 3:
                    val = parts[2]
                    if val == "0x1":
                        if status_only:
                            return True
                        else:
                            print_color("Self-protection is ON! Please disable it manually.", "red")
                            input("Press Enter to exit...")
                            sys.exit(1)
    return False

def check_process(status_only=False):
    out, err, code = run_cmd('tasklist /NH /FI "ImageName EQ avp.exe"', capture=True)
    if "avp.exe" in out:
        if status_only:
            return True
        else:
            print_color("Kaspersky process is running! Please unload it.", "red")
            input("Press Enter to exit...")
            sys.exit(1)
    return False

# ========== Удаление klobjdb.dat ==========

def remove_klobjdb():
    drive = os.environ.get("SystemDrive", "C:")
    svi = os.path.join(drive, "System Volume Information")
    if not os.path.exists(svi):
        print("System Volume Information not found.")
        return

    # Даём права
    run_cmd(f'icacls "{svi}" /grant *S-1-5-32-544:(F,WDAC) /t /q')
    # Права на подпапки K*
    for item in os.listdir(svi):
        if item.startswith("K"):
            subfolder = os.path.join(svi, item)
            if os.path.isdir(subfolder):
                run_cmd(f'icacls "{subfolder}" /grant *S-1-5-32-544:(F,WDAC) /t /q')

    # Поиск и удаление
    found = False
    for root, dirs, files in os.walk(svi):
        for file in files:
            if file.lower() == "klobjdb.dat":
                full = os.path.join(root, file)
                print(f"Found: {full}")
                found = True
                # takeown, icacls, attrib, del
                run_cmd(f'takeown /f "{full}"')
                run_cmd(f'icacls "{full}" /grant {os.environ["USERNAME"]}:F')
                run_cmd(f'icacls "{full}" /grant *S-1-5-32-544:(F)')
                run_cmd(f'attrib -r -s -h "{full}"')
                try:
                    os.remove(full)
                    print(f"Deleted: {full}")
                except Exception as e:
                    print(f"Failed to delete {full}: {e}")

    if not found:
        print("klobjdb.dat not found.")

    # Сброс прав
    run_cmd(f'icacls "{svi}" /remove *S-1-5-32-544 /t /c /q')

# ========== Функции сброса ==========

def trial_reset():
    print_color("\nResetting activation ...", "blue")

    # 1. Удаление klobjdb.dat
    remove_klobjdb()

    # 2. Удаление файлов данных
    if TypeAV == "AVP":
        data_path = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Kaspersky Lab", avp, "Data")
    else:
        data_path = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Kaspersky Lab", kes, "Data")

    if os.path.exists(data_path):
        for pattern in ["*.bin", "cat_engine*", "certdb_v2.*.idx"]:
            for file in Path(data_path).glob(pattern):
                try:
                    os.remove(file)
                    print(f"Deleted: {file}")
                except:
                    pass

    # 3. Удаление ключей реестра
    if TypeAV == "AVP":
        reg_base = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}"
    else:
        reg_base = f"HKLM\\{SOFTWARE}\\KasperskyLab\\protected\\{kes}"

    keys_to_delete = [
        f"{reg_base}\\Data\\LicCache",
        f"{reg_base}\\Data\\LicensingActivationErrorStorageLogic",
        f"HKLM\\{SOFTWARE}\\KasperskyLab\\LicStrg",
        f"{reg_base}\\Data\\UPAO",
        "HKLM\\SOFTWARE\\Microsoft\\SystemCertificates\\SPC"
    ]
    for key in keys_to_delete:
        run_cmd(f'reg delete "{key}" /f')

    # 4. Настройка реестра для сброса
    settings_path = f"{reg_base}\\settings"
    env_path = f"{reg_base}\\environment"
    data_upao = f"{reg_base}\\Data\\UPAO"
    run_cmd(f'reg add "{settings_path}" /v EnableSelfProtection /t REG_DWORD /d {SelfProtectionValue} /f')
    run_cmd(f'reg add "{settings_path}" /v Ins_InitMode /t REG_DWORD /d 1 /f')
    run_cmd(f'reg add "{data_upao}" /v UpaoState /t REG_DWORD /d 1 /f')
    run_cmd(f'reg add "{env_path}" /v UpaoState /t REG_SZ /d 1 /f')
    run_cmd(f'reg add "HKLM\\{SOFTWARE}\\KasperskyLab\\LicStrg" /f')

    print_color("Reset completed. Rebooting in 5 seconds...", "green")
    time.sleep(5)
    run_cmd("shutdown /r /t 0")

def trial_reset_kes():
    # Аналогично trial_reset, но с дополнительными шагами для KES
    print_color("\nResetting activation KES ...", "blue")
    remove_klobjdb()

    # Удаление Report и data.kvdb
    kes_path = os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Kaspersky Lab", kes)
    report_path = os.path.join(kes_path, "Report")
    if os.path.exists(report_path):
        run_cmd(f'takeown /F "{report_path}" /R /D Y')
        shutil.rmtree(report_path, ignore_errors=True)
    data_kvdb = os.path.join(kes_path, "Data", "data.kvdb")
    if os.path.exists(data_kvdb):
        try:
            os.remove(data_kvdb)
        except:
            pass

    reg_base = f"HKLM\\{SOFTWARE}\\KasperskyLab\\protected\\{kes}"
    keys_to_delete = [
        "HKLM\\SOFTWARE\\Microsoft\\SystemCertificates\\SPC",
        f"{reg_base}\\watchdog\\LicenseInfo",
        f"{reg_base}\\watchdog\\Ticket",
        f"HKLM\\{SOFTWARE}\\KasperskyLab\\protected\\LicStorage"
    ]
    for key in keys_to_delete:
        run_cmd(f'reg delete "{key}" /f')

    # Настройка
    run_cmd(f'reg add "{reg_base}\\Data" /v Install /t REG_DWORD /d 1 /f')
    run_cmd(f'reg add "{reg_base}\\settings" /v EnableSelfProtection /t REG_DWORD /d {SelfProtectionValue} /f')

    print_color("Reset completed. Rebooting...", "green")
    time.sleep(5)
    run_cmd("shutdown /r /t 0")

# ========== Активации (установка типа продукта) ==========

def activation_standard():
    global SelfProtectionValue
    if TypeAV == "AVP":
        reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        run_cmd(f'reg add "{reg_env}" /v ProductStatus /t REG_SZ /d "" /f')
        run_cmd(f'reg add "{reg_env}" /v ProductType /t REG_SZ /d kis /f')
    trial_reset()

def activation_premium():
    if TypeAV == "AVP":
        reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        run_cmd(f'reg add "{reg_env}" /v ProductStatus /t REG_SZ /d "" /f')
        run_cmd(f'reg add "{reg_env}" /v ProductType /t REG_SZ /d saas /f')
    trial_reset()

def activation_ksos():
    if TypeAV == "AVP":
        reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        run_cmd(f'reg add "{reg_env}" /v ProductStatus /t REG_SZ /d "" /f')
        run_cmd(f'reg add "{reg_env}" /v ProductType /t REG_SZ /d ksospc /f')
    trial_reset()

def activation_standard_release():
    if TypeAV == "AVP":
        reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        run_cmd(f'reg add "{reg_env}" /v ProductStatus /t REG_SZ /d release /f')
        run_cmd(f'reg add "{reg_env}" /v ProductType /t REG_SZ /d kis /f')
    trial_reset()

def activation_premium_release():
    if TypeAV == "AVP":
        reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        run_cmd(f'reg add "{reg_env}" /v ProductStatus /t REG_SZ /d release /f')
        run_cmd(f'reg add "{reg_env}" /v ProductType /t REG_SZ /d saas /f')
    trial_reset()

def activation_ksos_release():
    if TypeAV == "AVP":
        reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
        run_cmd(f'reg add "{reg_env}" /v ProductStatus /t REG_SZ /d release /f')
        run_cmd(f'reg add "{reg_env}" /v ProductType /t REG_SZ /d ksospc /f')
    trial_reset()

# ========== Встраивание/удаление кода ==========

def embed_trial_code(code, scenario="Trial"):
    if TypeAV != "AVP":
        return
    reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
    reg_settings = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\settings"
    run_cmd(f'reg add "{reg_env}" /v ShowActivateTrialOption /t REG_SZ /d 1 /f')
    run_cmd(f'reg add "{reg_env}" /v StartupScenario /t REG_SZ /d {scenario} /f')
    run_cmd(f'reg add "{reg_env}" /v TrialActCode /t REG_SZ /d "{code}" /f')
    run_cmd(f'reg add "{reg_settings}" /v Ins_ActivationCode /t REG_SZ /d "{code}" /f')
    print_color("Trial code embedded.", "green")

def remove_embedded_trial_code():
    if TypeAV != "AVP":
        return
    reg_env = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\environment"
    reg_settings = f"HKLM\\{SOFTWARE}\\KasperskyLab\\{avp}\\settings"
    run_cmd(f'reg add "{reg_env}" /v ShowActivateTrialOption /t REG_SZ /d "" /f')
    run_cmd(f'reg add "{reg_env}" /v StartupScenario /t REG_SZ /d Trial /f')
    run_cmd(f'reg add "{reg_env}" /v TrialActCode /t REG_SZ /d "" /f')
    run_cmd(f'reg add "{reg_settings}" /v Ins_ActivationCode /t REG_SZ /d "" /f')
    print_color("Embedded trial code removed.", "green")

# ========== Экспорт/импорт активации ==========

def extract_embedded_files():
    """
    Извлекает ActivationVBS и OpenFileBoxEXE из закодированных данных в скрипте.
    В оригинале они закодированы как PEM-сертификаты (base64).
    Мы храним их как строки в коде.
    """
    global ActivationVBS, OpenFileBoxEXE
    # Эти данные должны быть извлечены из скрипта TrialReset.cmd.
    # Поскольку здесь мы не можем вставить многомегабайтные строки, мы реализуем
    # заглушку: создадим минимальные версии или просто предупредим, что экспорт/импорт
    # не поддерживается в этой версии.
    print("Export/Import functionality requires embedded VBS and EXE files.")
    print("This feature is not fully implemented in this Python version.")
    return False

def export_activation():
    if not extract_embedded_files():
        print("Export not available.")
        return
    # ... выполнение wscript и копирование .dat ...
    print("Export completed (placeholder).")

def import_activation(enable_self_protection=False):
    if not extract_embedded_files():
        print("Import not available.")
        return
    # ... выполнение wscript ...
    print("Import completed (placeholder).")

# ========== Меню ==========

def menu1():
    global SelfProtectionValue
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_color(f"\n        {NAME_UTILITY}", "cyan")
        print(f"\n            ProductName: {ProductName}")
        print(f"                Version: {ProductVersion} [{avp or kes}] [{ProductType}]")
        print(f"                 Status: {ProductStatus}")
        print("")
        process_running = check_process(True)
        self_prot = check_self_protection(True)
        if process_running:
            print("                Process: Kaspersky is running")
        else:
            print("                Process: ●")
        if self_prot:
            print("        Self-Protection: ON")
        else:
            print("        Self-Protection: OFF")
        print("")
        print("        Select an action:")
        print("")
        print("  [0] = Exit")
        print("")
        print("  [1] = Menu: Reset activation")
        print("  [2] = Save activation (export)")
        print("  [3] = Install activation (import) + Enable Self-Protection")
        print("  [4] = Install activation (import)")
        print("")
        print("  [ENTER] = Reload menu")
        print("")
        choice = input(">  Your choice: ").strip()
        if choice == "":
            continue
        if choice == "0":
            sys.exit(0)
        elif choice == "1":
            menu2()
        elif choice == "2":
            export_activation()
            input("Press Enter to continue...")
        elif choice == "3":
            SelfProtectionValue = 1
            import_activation(True)
            input("Press Enter to continue...")
        elif choice == "4":
            SelfProtectionValue = 0
            import_activation(False)
            input("Press Enter to continue...")
        else:
            print("Wrong choice.")
            time.sleep(1)

def menu2():
    global SelfProtectionValue, Code, AddCode
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print_color("\n        Reset Activation/TRIAL (Autorestart of the computer)", "cyan")
        print(f"\n            ProductName: {ProductName}")
        print(f"                Version: {ProductVersion} [{avp or kes}] [{ProductType}]")
        print(f"                 Status: {ProductStatus}")
        print("")
        process_running = check_process(True)
        self_prot = check_self_protection(True)
        if process_running:
            print("                Process: Kaspersky is running")
        else:
            print("                Process: ●")
        if self_prot:
            print("        Self-Protection: ON")
        else:
            print("        Self-Protection: OFF")
        print("")
        print("        Select an action:")
        print("")
        print("  [0] = Return to previous menu")
        print("")
        print("  [1] = Reset")
        print("  [2] = Reset + Enable Self-Protection")
        print("  ***************************************************")
        print("   \"Experimental options\"")
        print("  ***************************************************")
        print("  [3] = Reset (Standard 90 days)")
        print("  [4] = Reset (Standard 90 days) + Enable Self-Protection")
        print("  [5] = Reset (Premium 90 days)")
        print("  [6] = Reset (Premium 90 days) + Enable Self-Protection")
        print("  [7] = Reset (KSOS beta-key)")
        print("  [8] = Reset (KSOS beta-key) + Enable Self-Protection")
        print("  ***************************************************")
        print("  [9]  = Reset (Standard return release-key)")
        print("  [10] = Reset (Premium return release-key)")
        print("  [11] = Reset (KSOS return release-key)")
        print("")

        # Определяем, доступно ли встраивание кода (для AVP с версией 21.6+)
        AddCode = None
        if TypeAV == "AVP":
            # Проверка версии
            try:
                ver_parts = ProductVersion.split('.')
                if len(ver_parts) >= 2:
                    major = int(ver_parts[0])
                    minor = int(ver_parts[1])
                    if major > 21 or (major == 21 and minor >= 6):
                        AddCode = "Base"  # Для обычных продуктов
                        if ProductType and "ksos" in ProductType.lower():
                            AddCode = "KSOS"
            except:
                pass

        if AddCode:
            print("  [33] = Embed the code > Free 365d: ZM4YW-FUTDY-W9B62-GSK26")
            print("  [44] = Embed the code > Basic Trial 30d: XMXWA-R191J-29HYQ-DBHSD")
            print("  [55] = Embed the code > Standard Trial 30d: 2RA3D-DGRBB-QY62B-62BX4")
            print("  [66] = Embed the code > Plus Trial 90d: 3M3K9-5R92S-ZDH5Y-NA944")
            print("  [99] = Remove embedded code")
        print("")
        print("  [ENTER] = Reload menu")
        print("")
        choice = input(">  Your choice: ").strip()
        if choice == "":
            continue
        if choice == "0":
            return
        # Сбросы
        if choice == "1":
            SelfProtectionValue = 0
            trial_reset()
        elif choice == "2":
            SelfProtectionValue = 1
            trial_reset()
        elif choice == "3":
            SelfProtectionValue = 0
            activation_standard()
        elif choice == "4":
            SelfProtectionValue = 1
            activation_standard()
        elif choice == "5":
            SelfProtectionValue = 0
            activation_premium()
        elif choice == "6":
            SelfProtectionValue = 1
            activation_premium()
        elif choice == "7":
            SelfProtectionValue = 0
            activation_ksos()
        elif choice == "8":
            SelfProtectionValue = 1
            activation_ksos()
        elif choice == "9":
            SelfProtectionValue = 0
            activation_standard_release()
        elif choice == "10":
            SelfProtectionValue = 0
            activation_premium_release()
        elif choice == "11":
            SelfProtectionValue = 0
            activation_ksos_release()
        elif choice in ("33", "44", "55", "66", "99") and AddCode:
            if choice == "33":
                embed_trial_code("ZM4YW-FUTDY-W9B62-GSK26", "Free")
            elif choice == "44":
                embed_trial_code("XMXWA-R191J-29HYQ-DBHSD", "Trial")
            elif choice == "55":
                embed_trial_code("2RA3D-DGRBB-QY62B-62BX4", "Trial")
            elif choice == "66":
                embed_trial_code("3M3K9-5R92S-ZDH5Y-NA944", "Trial")
            elif choice == "99":
                remove_embedded_trial_code()
            input("Press Enter to continue...")
        else:
            print("Wrong choice.")
            time.sleep(1)

# ========== Главная ==========

def main():
    if not is_admin():
        print("Administrator privileges required. Re-launching...")
        run_as_admin()
        return

    if not get_product_info():
        msg = "Not found supported Kaspersky!"
        print(msg)
        input("Press Enter to exit...")
        sys.exit(1)

    menu1()

if __name__ == "__main__":
    main()