import socket
import time

host = "192.168.56.1"
port = 5555

print(f"Пытаюсь подключиться к {host}:{port}...")

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))
    print("✅ ПОДКЛЮЧЕНИЕ УСТАНОВЛЕНО!")
    sock.close()
except Exception as e:
    print(f"❌ Ошибка: {e}")

input("Нажми Enter для выхода...")