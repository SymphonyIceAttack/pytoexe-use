import socket
import threading
from utils import send_alert, check_system
import config

clients = {}

def handle_client(client_socket, address):
    print(f"تم الاتصال من {address}")
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message == "ping":
                client_socket.send("pong".encode())
            elif message.startswith("alert"):
                send_alert(message)
            elif message == "system":
                cpu, ram = check_system()
                client_socket.send(f"CPU:{cpu}%, RAM:{ram}%".encode())
        except:
            print(f"انقطع الاتصال مع {address}")
            break

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((config.SERVER_HOST, config.SERVER_PORT))
    server.listen(5)
    print("السيرفر جاهز للاتصالات...")
    
    while True:
        client_socket, addr = server.accept()
        clients[addr[0]] = client_socket
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
