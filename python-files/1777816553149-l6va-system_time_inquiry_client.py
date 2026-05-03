import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = input("Input Target address: ")
server_addr = (ip, 12000)
client_socket.connect(server_addr)
print(f"Connected to {server_addr}.")

while True:
    cmd = input("Input command (Time/Exit): ")
    if cmd == 'Time':
        client_socket.send(cmd.encode())
        time_msg = client_socket.recv(1024).decode()
        print(f"Received: {time_msg}")
    elif cmd == 'Exit':
        client_socket.send(cmd.encode())
        bye_msg = client_socket.recv(1024).decode()
        print(f"Received: {bye_msg}")
        break
    else:
        print("Error Command")

client_socket.close()