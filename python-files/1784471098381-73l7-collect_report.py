# ================= ГЛОБАЛЬНЫЙ ПЕРЕХВАТ ОШИБОК =================
import sys, os, traceback, platform, socket, getpass, subprocess, urllib.request, hashlib, json, csv
from datetime import datetime
from pathlib import Path
from io import StringIO

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
except Exception as e:
    print("ОШИБКА: не установлена библиотека pycryptodome.")
    print("Установите её командой: pip install pycryptodome")
    print(f"Техническая информация: {e}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# ================= ПАРАМЕТРЫ ШИФРОВАНИЯ =================
PASSWORD = "OtP1nd2j3hL9dxeREJOlQkUvMRPdICH0m2K7BQh8sVuY8XRT3ugUpPHdw1xnLEvh"
SALT = b"MyS@lt!2024_"
ITERATIONS = 10_000
KEY_SIZE = 32
OUTPUT_DIR = r"C:\Temp"

def log_and_pause():
    print("\n" + "=" * 60)
    print("КРИТИЧЕСКАЯ ОШИБКА! Окно останется открытым до нажатия Enter.")
    traceback.print_exc()
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "error.log"), "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        print(f"\nПодробности сохранены в {OUTPUT_DIR}\\error.log")
    except:
        pass
    input("\nНажмите Enter для выхода...")

# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
def run_cmd(command, encoding='cp866'):
    try:
        proc = subprocess.run(command, shell=True, capture_output=True, text=False)
        if proc.returncode == 0:
            return proc.stdout.decode(encoding, errors='replace').strip()
        else:
            return ""
    except:
        return ""

def run_powershell(script, encoding='utf-8'):
    try:
        proc = subprocess.run(["powershell", "-Command", script], capture_output=True, text=False)
        if proc.returncode == 0:
            return proc.stdout.decode(encoding, errors='replace').strip()
        else:
            return ""
    except:
        return ""

def get_hostname():
    return platform.node()

def get_user():
    domain = os.environ.get('USERDOMAIN', '')
    username = os.environ.get('USERNAME', getpass.getuser())
    if domain and username:
        return f"{domain}\\{username}"
    return username

def get_external_ip():
    try:
        with urllib.request.urlopen("https://ifconfig.me", timeout=3) as response:
            return response.read().decode('utf-8').strip()
    except:
        return "Недоступен"

def file_sha256(filepath):
    if not filepath or not os.path.isfile(filepath):
        return ""
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return "Ошибка"

# ================= СЛОВАРЬ СИСТЕМНЫХ ПРОЦЕССОВ =================
KNOWN_SYSTEM_PROCESSES = {
    "svchost.exe": "Хост-процесс служб Windows",
    "csrss.exe": "Подсистема клиент-сервер",
    "winlogon.exe": "Вход в систему",
    "services.exe": "Диспетчер служб",
    "lsass.exe": "Локальная проверка подлинности",
    "smss.exe": "Диспетчер сеанса",
    "wininit.exe": "Инициализация Windows",
    "explorer.exe": "Проводник",
    "taskhostw.exe": "Хост задач",
    "rundll32.exe": "Запуск DLL",
    "dwm.exe": "Диспетчер окон рабочего стола",
    "sppsvc.exe": "Защита ПО",
    "spoolsv.exe": "Очередь печати",
    "audiodg.exe": "Изоляция аудиографов",
    "System": "Бездействие системы",
    "conhost.exe": "Хост консоли",
    "dllhost.exe": "COM Surrogate",
}

def describe_process(name):
    base = os.path.basename(name).lower() if name else ""
    return KNOWN_SYSTEM_PROCESSES.get(base, "")

def check_signature(filepath):
    if not filepath or not os.path.exists(filepath):
        return "Unknown"
    ps_cmd = f"(Get-AuthenticodeSignature '{filepath}').Status"
    out = run_powershell(ps_cmd)
    return out.strip() if out else "Unknown"

# ================= ФУНКЦИИ СБОРА ДАННЫХ =================
def collect_overview():
    data = {
        "Дата создания отчёта": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Хост": get_hostname(),
        "Внутренний IP": socket.gethostbyname(socket.gethostname()),
        "Внешний IP": get_external_ip(),
        "Пользователь": get_user(),
        "ОС": platform.platform(),
        "Архитектура": platform.architecture()[0],
        "Процессор": platform.processor(),
    }
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            data["ОС (название)"] = winreg.QueryValueEx(key, "ProductName")[0]
            try:
                data["Релиз"] = winreg.QueryValueEx(key, "DisplayVersion")[0]
            except:
                data["Релиз"] = ""
            data["Сборка"] = winreg.QueryValueEx(key, "CurrentBuild")[0]
    except:
        data["ОС (название)"] = platform.platform()
    out = run_cmd("systeminfo")
    for line in out.splitlines():
        if "Domain:" in line or "Домен:" in line:
            data["Домен"] = line.split(":")[1].strip()
            break
    else:
        data["Домен"] = "Unknown"
    return data

def collect_system_info():
    info = {}
    # Явно задаём кодировку консоли PowerShell и вывода
    ps_script = r"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    $cs = Get-CimInstance Win32_ComputerSystem
    $proc = Get-CimInstance Win32_Processor | Select-Object -First 1
    $board = Get-CimInstance Win32_BaseBoard
    $bios = Get-CimInstance Win32_BIOS
    $os = Get-CimInstance Win32_OperatingSystem
    @{
        Производитель = $cs.Manufacturer
        Модель = $cs.Model
        "ОЗУ (ГБ)" = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
        Процессор = $proc.Name
        Ядра = $proc.NumberOfCores
        "Логические процессоры" = $proc.NumberOfLogicalProcessors
        "Макс. частота (МГц)" = $proc.MaxClockSpeed
        "Производитель платы" = $board.Manufacturer
        "Модель платы" = $board.Product
        "Версия BIOS" = $bios.SMBIOSBIOSVersion
        "Дата BIOS" = $bios.ReleaseDate.ToString('yyyy-MM-dd')
        "Серийный номер" = $bios.SerialNumber
        "Дата установки ОС" = $os.InstallDate.ToString('yyyy-MM-dd HH:mm:ss')
    } | ConvertTo-Json
    """
    out = run_powershell(ps_script)
    if out:
        try:
            d = json.loads(out)
            for k, v in d.items():
                info[k] = v
        except:
            pass

    # Проверка Sysmon (без изменений)
    sysmon_installed = False
    sysmon_date = ""
    sc_out = run_cmd("sc query Sysmon")
    if not sc_out:
        sc_out = run_cmd("sc query Sysmon64")
    if sc_out and ("RUNNING" in sc_out or "STOPPED" in sc_out):
        sysmon_installed = True
        try:
            import winreg
            for subkey_name in ["Sysmon", "Sysmon64"]:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                         f"SYSTEM\\CurrentControlSet\\Services\\{subkey_name}")
                    install_date = winreg.QueryValueEx(key, "InstallDate")
                    if install_date:
                        sysmon_date = install_date[0]
                    winreg.CloseKey(key)
                    break
                except:
                    pass
        except:
            pass
    info["Sysmon установлен"] = "Да" if sysmon_installed else "Нет"
    if sysmon_date:
        info["Дата установки Sysmon"] = sysmon_date
    return info

def collect_users_and_groups():
    users = []
    admins = []
    out = run_cmd("net user")
    if out:
        lines = out.splitlines()
        start = False
        for line in lines:
            if "---" in line:
                start = True
                continue
            if start and line.strip() and not line.startswith("Команда выполнена"):
                parts = line.split()
                for p in parts:
                    if p:
                        users.append(p)
    out = run_cmd("net localgroup administrators")
    if out:
        capture = False
        for line in out.splitlines():
            if "---" in line:
                capture = True
                continue
            if capture and line.strip() and not line.startswith("Команда выполнена"):
                admins.append(line.strip())
    def normalize(name):
        return name.lower().split('\\')[-1]
    admins_set = {normalize(a) for a in admins}
    user_list = [{"Пользователь": u, "Администратор": normalize(u) in admins_set} for u in users]
    groups = []
    out = run_cmd("net localgroup")
    if out:
        for line in out.splitlines():
            if line.startswith("*"):
                group_name = line[1:].strip()
                members_out = run_cmd(f'net localgroup "{group_name}"')
                members = []
                capture = False
                for mline in members_out.splitlines():
                    if "---" in mline:
                        capture = True
                        continue
                    if capture and mline.strip() and not mline.startswith("Команда выполнена"):
                        members.append(mline.strip())
                groups.append({"Группа": group_name, "Члены": ", ".join(members)})
    return user_list, groups

def collect_network():
    rdp = {}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SYSTEM\CurrentControlSet\Control\Terminal Server") as key:
            fDeny = winreg.QueryValueEx(key, "fDenyTSConnections")[0]
        rdp["RDP включён"] = fDeny == 0
    except:
        rdp["RDP включён"] = "Unknown"
    netstat = [{"Строка": line.strip()} for line in run_cmd("netstat -ano").splitlines() if line.strip()]
    hosts = []
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    if os.path.exists(hosts_path):
        with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    hosts.append({"Запись": line})
    dns_cache = []
    # Исправленный запрос: Data приводится к строке, чтобы избежать вложенных объектов
    ps_out = run_powershell("Get-DnsClientCache | Select-Object Entry,RecordType,@{Name='Data';Expression={[string]$_.Data}} | Where-Object { $_.Entry -notmatch '\\.in-addr\\.arpa$' } | ConvertTo-Json")
    if ps_out:
        try:
            cache_data = json.loads(ps_out)
            if isinstance(cache_data, dict): cache_data = [cache_data]
            for entry in cache_data:
                dns_cache.append({
                    "Имя": entry.get("Entry", ""),
                    "Тип": entry.get("RecordType", ""),
                    "Данные": entry.get("Data", "")
                })
        except:
            pass
    return rdp, netstat, hosts, dns_cache

def collect_installed_software():
    import winreg
    software = []
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    for uninstall_path in paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    except:
                        name = None
                    if name:
                        version = publisher = install_date_raw = install_location = ""
                        try: version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                        except: pass
                        try: publisher = winreg.QueryValueEx(subkey, "Publisher")[0]
                        except: pass
                        try: install_date_raw = winreg.QueryValueEx(subkey, "InstallDate")[0]
                        except: pass
                        try: install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                        except: pass
                        install_date_formatted = ""
                        if install_date_raw:
                            try:
                                if len(install_date_raw) == 8:
                                    dt = datetime.strptime(install_date_raw, "%Y%m%d")
                                    install_date_formatted = dt.strftime("%d/%m/%Y-%H:%M:%S")
                                else:
                                    install_date_formatted = install_date_raw
                            except:
                                install_date_formatted = install_date_raw
                        software.append({
                            "Название": name,
                            "Версия": version,
                            "Издатель": publisher,
                            "Дата установки": install_date_formatted,
                            "Расположение": install_location,
                        })
                    winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass
    return software

def collect_portable_apps():
    known_names = {sw["Название"].lower().replace(" ", "") for sw in collect_installed_software()}
    portable_paths = [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    ]
    portable = []
    for base in portable_paths:
        if not base or not os.path.exists(base):
            continue
        try:
            for entry in os.scandir(base):
                if entry.is_dir():
                    exe_file = None
                    for f in os.scandir(entry.path):
                        if f.is_file() and f.name.lower().endswith(".exe"):
                            exe_file = f.path
                            break
                    if exe_file:
                        name = os.path.splitext(os.path.basename(exe_file))[0]
                        if name.lower().replace(" ", "") in known_names:
                            continue
                        version = manufacturer = ""
                        try:
                            escaped = exe_file.replace("\\", "\\\\")
                            info = run_cmd(f'wmic datafile where name="{escaped}" get version, manufacturer')
                            lines = info.splitlines()
                            if len(lines) >= 2:
                                parts = lines[1].split(None, 1)
                                version = parts[0] if parts else ""
                                manufacturer = parts[1] if len(parts) > 1 else ""
                        except:
                            pass
                        portable.append({
                            "Название": name,
                            "Версия": version,
                            "Издатель": manufacturer,
                            "Путь": entry.path,
                        })
        except:
            pass
    return portable

def collect_autoruns():
    import winreg
    entries = []
    hives = {"HKCU": winreg.HKEY_CURRENT_USER, "HKLM": winreg.HKEY_LOCAL_MACHINE}
    subpaths = [
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        r"Software\Microsoft\Windows\CurrentVersion\RunServices",
        r"Software\Microsoft\Windows\CurrentVersion\RunServicesOnce",
    ]
    for hive_name, hive in hives.items():
        for subpath in subpaths:
            try:
                key = winreg.OpenKey(hive, subpath, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entries.append({"Ветвь": hive_name, "Раздел": subpath, "Имя": name, "Значение": str(value)})
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except:
                pass
    special = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", "Shell"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", "Userinit"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows", "AppInit_DLLs"),
    ]
    for hive, path, value_name in special:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            entries.append({"Ветвь": "HKLM", "Раздел": path, "Имя": value_name, "Значение": str(value)})
            winreg.CloseKey(key)
        except:
            pass
    return entries

def collect_processes():
    proc_list = []
    # Получаем процессы через PowerShell с гарантированным UTF-8
    ps_script = r"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Get-Process | Select-Object Id, Name, 
        @{Name='Path'; Expression={$_.Path}},
        @{Name='UserName'; Expression={$_.UserName}},
        @{Name='Description'; Expression={$_.Description}} | 
    ConvertTo-Json
    """
    out = run_powershell(ps_script)
    if not out:
        return proc_list

    try:
        processes_data = json.loads(out)
        if isinstance(processes_data, dict):
            processes_data = [processes_data]

        for proc in processes_data:
            pid = proc.get("Id")
            name = proc.get("Name", "")
            path = proc.get("Path", "")
            user = proc.get("UserName", "")
            # Используем наш словарь для известных процессов
            desc = describe_process(name)
            # Цифровая подпись и SHA256 (только если путь не пуст)
            signature = check_signature(path) if path else "Unknown"
            sha256 = file_sha256(path) if path else ""

            proc_list.append({
                "PID": pid,
                "Имя": name,
                "Путь": path,
                "Пользователь": user if user else "",
                "Описание": desc,
                "Подпись": signature,
                "SHA256": sha256,
            })
    except:
        pass

    return proc_list

def collect_services():
    # PowerShell-команда с принудительным UTF-8
    ps_script = r"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,PathName | ConvertTo-Json
    """
    out = run_powershell(ps_script)
    services = []
    if out:
        try:
            svc_data = json.loads(out)
            if isinstance(svc_data, dict): svc_data = [svc_data]
            for svc in svc_data:
                services.append({
                    "Имя": svc.get("Name", ""),
                    "Отображаемое имя": svc.get("DisplayName", ""),
                    "Состояние": svc.get("State", ""),
                    "Тип запуска": svc.get("StartMode", ""),
                    "Путь": svc.get("PathName", ""),
                })
        except:
            pass
    return services

def collect_scheduled_tasks():
    # Запуск schtasks внутри cmd с кодовой страницей 65001 (UTF-8)
    ps_script = r"""
    $prev = [Console]::OutputEncoding
    [Console]::OutputEncoding = [Text.Encoding]::UTF8
    $result = cmd /c "chcp 65001 > nul & schtasks /query /fo CSV /v"
    [Console]::OutputEncoding = $prev
    $result
    """
    out = run_powershell(ps_script, encoding='utf-8')
    tasks = []
    if not out:
        return tasks
    f = StringIO(out)
    reader = csv.reader(f, delimiter=',', quotechar='"')
    try:
        headers = next(reader)
    except StopIteration:
        return tasks
    headers = [h.strip() for h in headers]
    if not headers:
        return tasks

    try:
        status_idx = headers.index('Status') if 'Status' in headers else headers.index('Состояние')
    except ValueError:
        status_idx = None
    try:
        path_idx = headers.index('TaskPath')
    except ValueError:
        path_idx = None

    header_check = ("Имя узла", "TaskName", "HostName")

    for row in reader:
        if len(row) < len(headers):
            continue
        if row[0].strip() in header_check or row[0].strip() == headers[0]:
            continue
        task = dict(zip(headers, [r.strip() for r in row]))

        if status_idx is not None:
            status = row[status_idx].strip()
            if status not in ("Ready", "Готово"):
                continue

        if path_idx is not None:
            path = row[path_idx].strip()
            if path and (path.startswith('\\Microsoft\\') or '\\Microsoft\\Windows\\' in path):
                continue

        tasks.append(task)

    # Перевод ключей на русский для красоты
    translated_headers = {
        'HostName': 'Хост',
        'TaskName': 'Имя задачи',
        'Next Run Time': 'Следующий запуск',
        'Status': 'Состояние',
        'Logon Mode': 'Режим входа',
        'Last Run Time': 'Последний запуск',
        'Last Result': 'Результат',
        'Author': 'Автор',
        'Task To Run': 'Задача для выполнения',
        'Start In': 'Рабочая папка',
        'Comment': 'Примечание',
        'Scheduled Task State': 'Состояние задачи',
        'Idle Time': 'Время простоя',
        'Power Management': 'Управление питанием',
        'Run As User': 'Запуск от имени',
        'Delete Task If Not Rescheduled': 'Удалить если не перенесена',
        'Stop Task If Runs X Hours and X Mins': 'Остановить при выполнении',
        'Schedule': 'Расписание',
        'Schedule Type': 'Тип расписания',
        'Start Time': 'Время начала',
        'Start Date': 'Дата начала',
        'End Date': 'Дата окончания',
        'Days': 'Дни',
        'Months': 'Месяцы',
        'Repeat: Every': 'Повторять каждые',
        'Repeat: Until: Time': 'Повторять до',
        'Repeat: Until: Duration': 'Длительность повтора',
        'Repeat: Stop If Still Running': 'Остановить если выполняется',
    }
    translated_tasks = []
    for task in tasks:
        new_task = {}
        for k, v in task.items():
            new_key = translated_headers.get(k, k)
            new_task[new_key] = v
        translated_tasks.append(new_task)
    return translated_tasks

def collect_disk_encryption():
    disks = []
    ps_out = run_powershell(r"Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,Size,FreeSpace,FileSystem | ConvertTo-Json")
    if ps_out:
        try:
            json_data = json.loads(ps_out)
            if isinstance(json_data, dict): json_data = [json_data]
            for disk in json_data:
                size = disk.get("Size", 0)
                free = disk.get("FreeSpace", 0)
                disks.append({
                    "Устройство": disk["DeviceID"],
                    "Метка": disk["DeviceID"],
                    "ФС": disk.get("FileSystem", ""),
                    "Всего ГБ": round(size / (1024**3), 2) if size else 0,
                    "Свободно ГБ": round(free / (1024**3), 2) if free else 0,
                })
        except:
            pass
    bitlocker = []
    out = run_cmd("manage-bde -status")
    if out:
        vol = {}
        for line in out.splitlines():
            if "Volume:" in line or "Том:" in line:
                if vol:
                    bitlocker.append(vol)
                vol = {"Том": line.split(":",1)[1].strip()}
            elif "Conversion Status:" in line or "Состояние преобразования:" in line:
                vol["Состояние"] = line.split(":",1)[1].strip()
            elif "Protection Method:" in line or "Метод защиты:" in line:
                vol["Метод защиты"] = line.split(":",1)[1].strip()
        if vol:
            bitlocker.append(vol)
    return disks, bitlocker

def collect_windows_defender():
    defender = {}
    ps_cmd = "(Get-Service -Name WinDefend -ErrorAction SilentlyContinue).Status"
    status = run_powershell(ps_cmd)
    defender["Статус Defender"] = status if status else "Не установлена"
    defender["Defender отключён"] = "Да" if status and status.lower() == "stopped" else "Нет"
    exclusions = run_powershell(r"""
    $prefs = Get-MpPreference
    $result = @{}
    if ($prefs.ExclusionPath) { $result['Пути исключений'] = $prefs.ExclusionPath -join '; ' }
    if ($prefs.ExclusionProcess) { $result['Процессы исключений'] = $prefs.ExclusionProcess -join '; ' }
    if ($prefs.ExclusionExtension) { $result['Расширения исключений'] = $prefs.ExclusionExtension -join '; ' }
    if ($prefs.ExclusionIpAddress) { $result['IP-адреса исключений'] = $prefs.ExclusionIpAddress -join '; ' }
    $result | ConvertTo-Json
    """)
    if exclusions:
        try:
            excl_data = json.loads(exclusions)
            for k, v in excl_data.items():
                defender[k] = v
        except:
            pass
    return defender

def collect_usb_history():
    import winreg
    devices = []
    path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
                dev_key = winreg.OpenKey(key, subkey_name)
                hw_id = None
                try:
                    hw_subkey = winreg.OpenKey(dev_key, winreg.EnumKey(dev_key, 0))
                    try:
                        hw_id = winreg.QueryValueEx(hw_subkey, "HardwareID")[0][0]
                    except:
                        pass
                    winreg.CloseKey(hw_subkey)
                except:
                    pass
                last_connect = ""
                try:
                    prop_key = winreg.OpenKey(dev_key, r"Properties\{83da6326-97a6-4088-9453-a1923f573b29}\0064")
                    last_connect_bytes, _ = winreg.QueryValueEx(prop_key, "")
                    if last_connect_bytes:
                        try:
                            us = int.from_bytes(last_connect_bytes, byteorder='little')
                            last_connect = datetime(1601, 1, 1) + timedelta(microseconds=us // 10)
                            last_connect = last_connect.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            pass
                    winreg.CloseKey(prop_key)
                except:
                    pass
                devices.append({
                    "Устройство": subkey_name,
                    "Идентификатор": hw_id or subkey_name,
                    "Последнее подключение": last_connect if last_connect else "Неизвестно"
                })
                winreg.CloseKey(dev_key)
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except:
        pass
    return devices

def collect_unsigned_drivers():
    unsigned = []
    ps_cmd = r'Get-ChildItem -Path C:\Windows\System32\drivers -Filter *.sys -ErrorAction SilentlyContinue | Get-AuthenticodeSignature | Where-Object { $_.Status -ne "Valid" } | Select-Object -ExpandProperty Path'
    out = run_powershell(ps_cmd)
    for line in out.splitlines():
        if line.strip():
            unsigned.append({"Путь": line.strip()})
    return unsigned

def collect_applocker():
    out = run_powershell("Get-AppLockerPolicy -Effective -ErrorAction SilentlyContinue | Select-Object -ExpandProperty RuleCollections | Out-String")
    if out.strip():
        return [{"Правила": out.strip()}]
    return []

# ================= ГЕНЕРАЦИЯ HTML =================
def html_table(headers, rows, table_id="", row_class_func=None):
    if not rows:
        return '<div class="nodata">Нет данных</div>'
    html = f'<table id="{table_id}">'
    html += "<thead><tr>"
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr></thead><tbody>"
    for i, row in enumerate(rows):
        cls = "even" if i % 2 else "odd"
        if row_class_func:
            cls += " " + row_class_func(row)
        html += f'<tr class="{cls}">'
        for h in headers:
            val = row.get(h, "")
            if val is None: val = ""
            if isinstance(val, str) and len(val) > 100:
                short = val[:100] + "..."
                html += f'<td title="{val}">{short}</td>'
            else:
                html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def html_report(overview, system_info, users, groups, rdp, netstat, hosts, dns_cache,
                installed, portable, autoruns, processes, services,
                tasks, disks, bitlocker, usb, unsigned, applocker, defender):
    def process_class(row):
        sig = row.get("Подпись", "")
        return "warning" if sig not in ("Valid", "Unknown") else ""

    def service_class(row):
        status = row.get("Состояние", "")
        if status == "Running":
            return "running"
        elif status == "Stopped":
            return "stopped"
        return ""

    sidebar = """
    <nav class="sidebar">
      <div class="logo">🖥️ <span>Host Audit</span></div>
      <ul>
        <li><a href="#sysinfo">📋 Системная информация</a></li>
        <li><a href="#users">👤 Пользователи</a></li>
        <li><a href="#groups">👥 Группы</a></li>
        <li><a href="#defender">🛡️ Windows Defender</a></li>
        <li><a href="#processes">⚙️ Процессы</a></li>
        <li><a href="#services">🔧 Службы</a></li>
        <li><a href="#tasks">📅 Задачи планировщика</a></li>
        <li><a href="#disks">💾 Диски</a></li>
        <li><a href="#bitlocker">🔐 BitLocker</a></li>
        <li><a href="#usb">🖱️ USB-устройства</a></li>
        <li><a href="#unsigned">⚠️ Неподписанные драйверы</a></li>
        <li><a href="#autoruns">🚀 Автозагрузка</a></li>
        <li><a href="#netstat">🌐 Сеть (netstat)</a></li>
        <li><a href="#hosts">📡 Файл hosts</a></li>
        <li><a href="#dns">🗂 DNS-кэш</a></li>
        <li><a href="#software">📦 Установленное ПО</a></li>
        <li><a href="#portable">💼 Портативное ПО</a></li>
        <li><a href="#applocker">📜 AppLocker</a></li>
      </ul>
    </nav>
    """

    host_ip_ext = f"{overview.get('Хост', '')} — {overview.get('Внутренний IP', '')} (внешний {overview.get('Внешний IP', '')})"
    overview_html = f"""
    <div class="overview">
      <h1>Host Audit Report</h1>
      <div class="meta">
        <p><strong>Дата создания отчёта:</strong> {overview.get('Дата создания отчёта', '')}</p>
        <p><strong>Хост:</strong> {host_ip_ext}</p>
        <p><strong>Пользователь:</strong> {overview.get('Пользователь', '')}</p>
        <p><strong>ОС:</strong> {overview.get('ОС (название)', overview.get('ОС', ''))} ({overview.get('Архитектура', '')})</p>
        <p><strong>Домен:</strong> {overview.get('Домен', '')} &nbsp;|&nbsp; <strong>RDP:</strong> {rdp.get('RDP включён', '')}</p>
      </div>
    </div>
    """

    sections = []
    sections.append(f'<h2 id="sysinfo">📋 Системная информация</h2>' +
                     html_table(["Параметр", "Значение"], [{"Параметр": k, "Значение": v} for k, v in system_info.items()], "sysinfo"))
    sections.append(f'<h2 id="users">👤 Пользователи</h2>' +
                     html_table(["Пользователь", "Администратор"], users, "users"))
    sections.append(f'<h2 id="groups">👥 Группы</h2>' +
                     html_table(["Группа", "Члены"], groups, "groups"))
    defender_rows = [{"Параметр": k, "Значение": v} for k, v in defender.items()]
    sections.append(f'<h2 id="defender">🛡️ Windows Defender</h2>' +
                     html_table(["Параметр", "Значение"], defender_rows, "defender"))
    sections.append(f'<h2 id="processes">⚙️ Процессы</h2>' +
                     html_table(["PID", "Имя", "Путь", "Пользователь", "Описание", "Подпись", "SHA256"],
                                processes, "processes", process_class))
    sections.append(f'<h2 id="services">🔧 Службы</h2>' +
                     html_table(["Имя", "Отображаемое имя", "Состояние", "Тип запуска", "Путь"],
                                services, "services", service_class))
    tasks_headers = tasks[0].keys() if tasks else []
    sections.append(f'<h2 id="tasks">📅 Задачи планировщика (активные)</h2>' +
                     (html_table(tasks_headers, tasks, "tasks") if tasks else '<div class="nodata">Нет данных</div>'))
    sections.append(f'<h2 id="disks">💾 Диски</h2>' +
                     html_table(["Устройство", "Метка", "ФС", "Всего ГБ", "Свободно ГБ"], disks, "disks"))
    sections.append(f'<h2 id="bitlocker">🔐 BitLocker</h2>' +
                     html_table(["Том", "Состояние", "Метод защиты"], bitlocker, "bitlocker"))
    sections.append(f'<h2 id="usb">🖱️ USB-устройства (история подключений)</h2>' +
                     html_table(["Устройство", "Идентификатор", "Последнее подключение"], usb, "usb"))
    sections.append(f'<h2 id="unsigned">⚠️ Неподписанные драйверы</h2>' +
                     html_table(["Путь"], unsigned, "unsigned"))
    sections.append(f'<h2 id="autoruns">🚀 Автозагрузка</h2>' +
                     html_table(["Ветвь", "Раздел", "Имя", "Значение"], autoruns, "autoruns"))
    netstat_block = '<div class="netblock">' + '<br>'.join([e['Строка'] for e in netstat]) + '</div>' if netstat else '<div class="nodata">Нет данных</div>'
    sections.append(f'<h2 id="netstat">🌐 Сеть (netstat)</h2>' + netstat_block)
    hosts_block = '<div class="netblock">' + '<br>'.join([e['Запись'] for e in hosts]) + '</div>' if hosts else '<div class="nodata">Нет данных</div>'
    sections.append(f'<h2 id="hosts">📡 Файл hosts</h2>' + hosts_block)
    dns_headers = dns_cache[0].keys() if dns_cache else []
    sections.append(f'<h2 id="dns">🗂 DNS-кэш</h2>' +
                     (html_table(dns_headers, dns_cache, "dns") if dns_cache else '<div class="nodata">Нет данных</div>'))
    sections.append(f'<h2 id="software">📦 Установленное ПО</h2>' +
                     html_table(["Название", "Версия", "Издатель", "Дата установки", "Расположение"], installed, "software"))
    sections.append(f'<h2 id="portable">💼 Портативное ПО</h2>' +
                     html_table(["Название", "Версия", "Издатель", "Путь"], portable, "portable"))
    sections.append(f'<h2 id="applocker">📜 AppLocker</h2>' +
                     (html_table(["Правила"], applocker, "applocker") if applocker else '<div class="nodata">Нет данных</div>'))

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Host Audit Report</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
        font-family: 'Inter', 'Segoe UI', Tahoma, sans-serif;
        font-size: 13px;
        background: #f5f7fa;
        color: #1e293b;
        display: flex;
        min-height: 100vh;
    }}
    .sidebar {{
        width: 260px;
        background: #1e293b;
        color: #cbd5e1;
        padding: 30px 20px;
        position: fixed;
        top: 0;
        left: 0;
        bottom: 0;
        overflow-y: auto;
        box-shadow: 2px 0 12px rgba(0,0,0,0.08);
        z-index: 100;
    }}
    .sidebar .logo {{
        font-size: 20px;
        font-weight: 700;
        color: white;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        gap: 10px;
        padding-bottom: 20px;
        border-bottom: 1px solid #334155;
    }}
    .sidebar ul {{ list-style: none; }}
    .sidebar li {{ margin: 6px 0; }}
    .sidebar a {{
        color: #94a3b8;
        text-decoration: none;
        font-size: 13px;
        display: block;
        padding: 8px 12px;
        border-radius: 6px;
        transition: background 0.2s, color 0.2s;
    }}
    .sidebar a:hover {{
        background: #334155;
        color: white;
    }}
    .content {{
        margin-left: 280px;
        flex: 1;
        padding: 30px 40px;
        max-width: calc(100% - 280px);
    }}
    .container {{
        background: white;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.05);
        padding: 40px 50px;
    }}
    h1 {{
        font-size: 26px;
        font-weight: 700;
        color: #0f2b5c;
        margin-bottom: 25px;
        border-bottom: 3px solid #e9ecf1;
        padding-bottom: 15px;
    }}
    .overview {{
        background: #f8fafc;
        border-radius: 14px;
        padding: 20px 25px;
        margin-bottom: 35px;
        border: 1px solid #e2e8f0;
    }}
    .meta p {{ margin: 8px 0; font-size: 14px; }}
    h2 {{
        font-size: 18px;
        font-weight: 600;
        color: #0f2b5c;
        margin-top: 45px;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e9ecf1;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 15px 0 30px;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }}
    th {{
        background: #0f2b5c;
        color: white;
        padding: 10px 14px;
        text-align: left;
        font-weight: 600;
        font-size: 13px;
    }}
    td {{
        padding: 8px 14px;
        border-bottom: 1px solid #edf2f7;
        font-size: 12px;
        vertical-align: middle;
    }}
    tr.odd {{ background: #ffffff; }}
    tr.even {{ background: #f9fafb; }}
    tbody tr:hover {{ background-color: #eef2f6; }}
    tr.warning td {{ background-color: #fff8e1 !important; }}
    tr.running td {{ color: #2e7d32; font-weight: 500; }}
    tr.stopped td {{ color: #9e9e9e; }}
    .nodata {{
        padding: 18px;
        background: #f4f6fa;
        border-radius: 10px;
        color: #64748b;
        font-style: italic;
    }}
    .netblock {{
        background: #1e293b;
        color: #cbd5e1;
        padding: 15px;
        border-radius: 12px;
        font-family: 'Cascadia Code', monospace;
        font-size: 11px;
        max-height: 350px;
        overflow: auto;
        white-space: pre-wrap;
        margin: 15px 0 30px;
    }}
    .footer {{
        margin-top: 40px;
        text-align: center;
        color: #94a3b8;
        font-size: 11px;
        border-top: 1px solid #e2e8f0;
        padding-top: 20px;
    }}
</style>
</head>
<body>
{sidebar}
<div class="content">
<div class="container">
{overview_html}
{''.join(sections)}
<div class="footer">Отчёт создан автоматически &copy; {datetime.now().year} Host Audit Tool</div>
</div>
</div>
</body>
</html>
"""
    return html

# ================= ШИФРОВАНИЕ =================
def encrypt_data(data):
    key = PBKDF2(PASSWORD, SALT, dkLen=KEY_SIZE, count=ITERATIONS)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pad_len = 16 - len(data) % 16
    if pad_len == 0:
        pad_len = 16
    padded = data + bytes([pad_len] * pad_len)
    return iv + cipher.encrypt(padded)

# ================= ГЛАВНАЯ ФУНКЦИЯ =================
def main():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        hostname = get_hostname()
        enc_path = os.path.join(OUTPUT_DIR, f"{hostname}-report.enc")
        temp_html = os.path.join(OUTPUT_DIR, f"{hostname}-report-temp.html")

        print("Идет процесс составления отчета...")
        overview = collect_overview()
        system_info = collect_system_info()
        users, groups = collect_users_and_groups()
        rdp, netstat, hosts, dns_cache = collect_network()
        installed = collect_installed_software()
        portable = collect_portable_apps()
        autoruns = collect_autoruns()
        processes = collect_processes()
        services = collect_services()
        tasks = collect_scheduled_tasks()
        disks, bitlocker = collect_disk_encryption()
        defender = collect_windows_defender()
        usb = collect_usb_history()
        unsigned = collect_unsigned_drivers()
        applocker = collect_applocker()

        html_content = html_report(overview, system_info, users, groups, rdp, netstat, hosts, dns_cache,
                                   installed, portable, autoruns, processes, services,
                                   tasks, disks, bitlocker, usb, unsigned, applocker, defender)

        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)

        with open(temp_html, 'rb') as f:
            html_bytes = f.read()
        encrypted = encrypt_data(html_bytes)
        with open(enc_path, 'wb') as f:
            f.write(encrypted)

        os.remove(temp_html)

        print(f"Отчет успешно создан и сохранен в каталоге {OUTPUT_DIR}\\{hostname}-report.enc")
        print("Прикрепите отчет к задаче в RM")
    except Exception:
        log_and_pause()
    finally:
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
