import os
import winreg as reg

exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Collapse.exe")

if os.path.exists(exe_path):
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
    reg.SetValueEx(key, "Collapse", 0, reg.REG_SZ, f'"{exe_path}"')
    reg.CloseKey(key)