import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def disable_browsers():
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Google\\Chrome" /v BlockThirdPartyCookies /t REG_DWORD /d 1 /f')
    os.system('reg add "HKEY_CURRENT_USER\\Software\\Policies\\Google\\Chrome" /v BrowserLaptopModeEnabled /t REG_DWORD /d 0 /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Yandex\\YandexBrowser" /v Disabled /t REG_DWORD /d 1 /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Opera" /v InstallEnabled /t REG_DWORD /d 0 /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Mozilla\\Firefox" /v DisableAppUpdate /t REG_DWORD /d 1 /f')
    os.system('reg add "HKEY_CURRENT_USER\\Software\\Policies\\Mozilla\\Firefox" /v NoDefaultBrowserCheck /t REG_DWORD /d 1 /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Edge" /v AllowPrelaunch /t REG_DWORD /d 0 /f')
    os.system('reg add "HKEY_CURRENT_USER\\Software\\Policies\\Microsoft\\Edge" /v StartupBoostEnabled /t REG_DWORD /d 0 /f')
    os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v DisableCopilot /t REG_DWORD /d 1 /f')
    os.system('reg add "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /v TurnOffWindowsCopilot /t REG_DWORD /d 1 /f')
    
    browsers_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files\\Yandex\\YandexBrowser\\browser.exe",
        "C:\\Program Files\\Opera\\launcher.exe",
        "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    ]
    
    for path in browsers_paths:
        if os.path.exists(path):
            os.system(f'icacls "{path}" /deny Everyone:F')
    
    with open(r"C:\Windows\System32\drivers\etc\hosts", "a") as hosts:
        hosts.write("\n127.0.0.1 copilot.microsoft.com")
        hosts.write("\n127.0.0.1 bing.com/copilot")
    
    print("[+] Браузеры и Copilot заблокированы")
    print("[+] Перезагрузка через 5 секунд...")
    os.system("timeout /t 5 /nobreak")
    os.system("shutdown /r /f /t 0")

def restore_system():
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Google" /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Yandex" /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Opera" /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Mozilla" /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Edge" /f 2>nul')
    os.system('reg delete "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot" /f 2>nul')
    os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v DisableCopilot /t REG_DWORD /d 0 /f')
    
    with open(r"C:\Windows\System32\drivers\etc\hosts", "r") as hosts:
        lines = hosts.readlines()
    with open(r"C:\Windows\System32\drivers\etc\hosts", "w") as hosts:
        for line in lines:
            if "copilot.microsoft.com" not in line and "bing.com/copilot" not in line:
                hosts.write(line)
    
    browsers_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files\\Yandex\\YandexBrowser\\browser.exe",
        "C:\\Program Files\\Opera\\launcher.exe",
        "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
        "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
    ]
    
    for path in browsers_paths:
        if os.path.exists(path):
            os.system(f'icacls "{path}" /remove:d Everyone')
    
    print("[+] Система восстановлена")
    print("[+] Перезагрузка через 5 секунд...")
    os.system("timeout /t 5 /nobreak")
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