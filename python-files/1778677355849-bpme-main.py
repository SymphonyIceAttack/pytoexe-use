import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def disable_browsers():
    # Полная блокировка Chrome через реестр
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\chrome.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    
    # Блокировка Edge
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\msedge.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    
    # Блокировка Firefox
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\firefox.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    
    # Блокировка Opera
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\opera.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\launcher.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    
    # Блокировка Yandex
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\browser.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\yandex.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    
    # Блокировка Copilot
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\Copilot.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\WindowsCopilot.exe" /v Debugger /t REG_SZ /d "cmd.exe" /f')
    
    # Блокировка через AppInit_DLLs (запрет запуска)
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows" /v AppInit_DLLs /t REG_SZ /d "block.dll" /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows" /v LoadAppInit_DLLs /t REG_DWORD /d 1 /f')
    
    # Блокировка через Software Restriction Policies
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Safer\\CodeIdentifiers" /v DefaultLevel /t REG_DWORD /d 0 /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Safer\\CodeIdentifiers\\0\\Paths\\{1}" /v ItemData /t REG_SZ /d "chrome.exe" /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Safer\\CodeIdentifiers\\0\\Paths\\{1}" /v SaferFlags /t REG_DWORD /d 0 /f')
    
    # Политика запрета запуска
    browsers = ["chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "browser.exe", "Copilot.exe"]
    for i, browser in enumerate(browsers):
        os.system(f'reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\DisallowRun" /v {i+1} /t REG_SZ /d "{browser}" /f')
    os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v DisallowRun /t REG_DWORD /d 1 /f')
    
    # Запрет через AppLocker
    os.system('reg add "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\AppIDSvc" /v Start /t REG_DWORD /d 2 /f')
    
    print("[+] ВСЕ браузеры и Copilot полностью заблокированы через реестр")
    print("[+] Любая попытка запуска будет выдавать ошибку")
    print("[+] Перезагрузка через 3 секунды...")
    os.system("timeout /t 3 /nobreak")
    os.system("shutdown /r /f /t 0")

def restore_system():
    # Удаляем все блокировки
    browsers_to_remove = [
        "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", 
        "launcher.exe", "browser.exe", "yandex.exe", "Copilot.exe", "WindowsCopilot.exe"
    ]
    
    for browser in browsers_to_remove:
        os.system(f'reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\{browser}" /f 2>nul')
    
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows" /v AppInit_DLLs /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Windows" /v LoadAppInit_DLLs /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\Safer" /f 2>nul')
    os.system('reg delete "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer\\DisallowRun" /f 2>nul')
    os.system('reg delete "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v DisallowRun /f 2>nul')
    
    print("[+] Все блокировки удалены")
    print("[+] Перезагрузка через 3 секунды...")
    os.system("timeout /t 3 /nobreak")
    os.system("shutdown /r /f /t 0")

if __name__ == "__main__":
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    if os.path.exists("restore.flag"):
        os.remove("restore.flag")
        restore_system()
    else:
        with open("restore.flag", "w") as f:
            f.write("1")
        disable_browsers()