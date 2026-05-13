import os
import shutil
import subprocess
import sys
import winreg
from pathlib import Path

def force_remove_app(app_name):
    """
    Полное удаление приложения и всех его следов
    """
    print(f"[*] Начинаем уничтожение: {app_name}")
    
    # 1. Поиск установленных приложений через реестр
    uninstall_paths = []
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    
    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if app_name.lower() in display_name.lower():
                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0] if winreg.QueryValueEx(subkey, "InstallLocation") else None
                                uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0] if winreg.QueryValueEx(subkey, "UninstallString") else None
                                uninstall_paths.append({
                                    "name": display_name,
                                    "path": install_location,
                                    "uninstall": uninstall_string
                                })
                        except:
                            pass
        except:
            pass
    
    # 2. Запускаем деинсталлятор если есть
    for app in uninstall_paths:
        if app["uninstall"]:
            print(f"[+] Запуск деинсталляции: {app['name']}")
            try:
                subprocess.run(app["uninstall"], shell=True, timeout=30)
            except:
                pass
    
    # 3. Ищем и удаляем все папки с именем приложения
    drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    
    for drive in drives:
        for root, dirs, files in os.walk(drive):
            for dir_name in dirs:
                if app_name.lower() in dir_name.lower():
                    target_path = os.path.join(root, dir_name)
                    print(f"[+] Удаляем: {target_path}")
                    try:
                        shutil.rmtree(target_path, ignore_errors=False)
                    except:
                        try:
                            subprocess.run(f'rmdir /s /q "{target_path}"', shell=True)
                        except:
                            pass
    
    # 4. Поиск и удаление файлов приложения во всех временных папках
    temp_paths = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        r"C:\Windows\Temp",
        os.path.expanduser("~\\AppData\\Local\\Temp"),
        os.path.expanduser("~\\AppData\\Local"),
        os.path.expanduser("~\\AppData\\Roaming"),
        os.path.expanduser("~\\AppData\\LocalLow")
    ]
    
    for temp_path in temp_paths:
        if os.path.exists(temp_path):
            for root, dirs, files in os.walk(temp_path):
                for item in dirs + files:
                    if app_name.lower() in item.lower():
                        full_path = os.path.join(root, item)
                        print(f"[+] Уничтожаем след: {full_path}")
                        try:
                            if os.path.isfile(full_path):
                                os.remove(full_path)
                            else:
                                shutil.rmtree(full_path)
                        except:
                            pass
    
    # 5. Удаление ключей реестра
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"SOFTWARE\\{app_name}")
    except:
        pass
    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, f"SOFTWARE\\{app_name}")
    except:
        pass
    
    # 6. Очистка кэша установщика
    installer_cache = r"C:\Windows\Installer"
    if os.path.exists(installer_cache):
        for file in os.listdir(installer_cache):
            if app_name.lower() in file.lower():
                try:
                    os.remove(os.path.join(installer_cache, file))
                except:
                    pass
    
    print("[✓] Готово. Приложение уничтожено со всеми корнями.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        app_to_kill = " ".join(sys.argv[1:])
    else:
        app_to_kill = input("Введите название приложения для полного удаления: ")
    
    force_remove_app(app_to_kill)