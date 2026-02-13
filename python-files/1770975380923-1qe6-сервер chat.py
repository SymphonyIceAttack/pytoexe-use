Python 3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import socket
import threading

# Настройки сервера
HOST = '0.0.0.0'  # Слушаем все интерфейсы
PORT = 9090

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
nicknames = []

... # Функция рассылки сообщений всем клиентам
... def broadcast(message):
...     for client in clients:
...         client.send(message)
... 
... # Обработка сообщений от конкретного клиента
... def handle(client):
...     while True:
...         try:
...             message = client.recv(1024)
...             broadcast(message)
...         except:
...             index = clients.index(client)
...             clients.remove(client)
...             client.close()
...             nickname = nicknames[index]
...             broadcast(f'{nickname} покинул чат!'.encode('utf-8'))
...             nicknames.remove(nickname)
...             break
... 
... # Прием новых подключений
... def receive():
...     while True:
...         client, address = server.accept()
...         print(f"Подключен {str(address)}")
... 
...         client.send('NICK'.encode('utf-8'))
...         nickname = client.recv(1024).decode('utf-8')
...         nicknames.append(nickname)
...         clients.append(client)
... 
...         print(f"Никнейм клиента: {nickname}")
...         broadcast(f"{nickname} присоединился к чату!".encode('utf-8'))
...         client.send('Вы подключились к серверу!'.encode('utf-8'))
... 
...         thread = threading.Thread(target=handle, args=(client,))
...         thread.start()
... 
... print("Сервер запущен...")
