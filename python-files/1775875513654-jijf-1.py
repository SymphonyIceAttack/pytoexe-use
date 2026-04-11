import socket
import threading

def handle(conn):
    while True:
        data = conn.recv(1024).decode('gbk', 'ignore')
        if not data: break
        print('收到:', data.strip())

        if data.startswith('93'):
            conn.send(b'941AYAZ')
        elif data.startswith('63'):
            conn.send(b'64              AA123456|AYAZ')
        elif data.startswith('17'):
            conn.send(b'20Y|AB123456789|AYAZ')
        elif data.startswith('99'):
            conn.send(b'98YYYY|AYAZ')
        else:
            conn.send(b'AYAZ')

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 6001))
s.listen(5)
print('SIP2测试服务已启动：0.0.0.0:6001')

while True:
    conn, addr = s.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()