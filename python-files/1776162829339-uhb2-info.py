import socket
import getpass
import platform

hostname = socket.gethostname()
username = getpass.getuser()
ip_address = socket.gethostbyname(hostname)

print(f"🖥️ Имя компьютера: {hostname}")
print(f"👤 Имя пользователя: {username}")
print(f"🌐 IP-адрес: {ip_address}")

input("Нажмите Enter, чтобы закрыть окно...")