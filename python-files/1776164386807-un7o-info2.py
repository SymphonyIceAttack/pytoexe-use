import tkinter as tk
import socket
import getpass
import sys

sys.stdout = open('output.log', 'w')
sys.stderr = open('error.log', 'w')

# Получаем данные
hostname = socket.gethostname()
username = getpass.getuser()
ip_address = socket.gethostbyname(hostname)

# Создаём главное окно
root = tk.Tk()
root.title("Информация о системе")
root.geometry("350x200")

# Вставляем текстовые метки с информацией
tk.Label(root, text="🖥️ Имя компьютера:", font=("Arial", 12)).pack(pady=5)
tk.Label(root, text=hostname, font=("Arial", 12)).pack(pady=2)

tk.Label(root, text="👤 Имя пользователя:", font=("Arial", 12)).pack(pady=5)
tk.Label(root, text=username, font=("Arial", 12)).pack(pady=2)

tk.Label(root, text="🌐 IP-адрес:", font=("Arial", 12)).pack(pady=5)
tk.Label(root, text=ip_address, font=("Arial", 12)).pack(pady=2)

# Кнопка для закрытия окна
tk.Button(root, text="Закрыть", command=root.destroy, font=("Arial", 12)).pack(pady=20)

# Запускаем окно
root.mainloop()