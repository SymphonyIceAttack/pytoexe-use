import socket
import getpass
import platform

# Имя компьютера
hostname = socket.gethostname()

# Имя пользователя
username = getpass.getuser()

# IP-адрес (основной)
ip_address = socket.gethostbyname(hostname)

# Вывод информации
print(f"🖥️ Имя компьютера: {hostname}")
print(f"👤 Имя пользователя: {username}")
print(f"🌐 IP-адрес: {ip_address}")