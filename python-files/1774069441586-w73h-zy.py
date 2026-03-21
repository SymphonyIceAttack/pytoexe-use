import socket
import threading

# 配置：监听 3002 端口，不解析数据，直接打印
HOST = '0.0.0.0'  # 监听所有网卡
PORT = 3002       # 监听端口

def handle_client(client_socket, client_address):
    """处理仪器连接，打印所有原始数据，不解析"""
    print(f"\n[仪器已连接] {client_address}")
    
    try:
        # 持续接收数据
        while True:
            # 一次最多接收 4096 字节，可根据仪器调整
            data = client_socket.recv(4096)
            
            # 没有数据 = 断开连接
            if not data:
                break
            
            # 直接打印原始信息（不解析）
            print(f"[{client_address}] 收到原始数据：{data}")

    except Exception as e:
        print(f"[异常] {client_address} 断开：{str(e)}")
    finally:
        client_socket.close()
        print(f"[仪器断开] {client_address}\n")

def start_server():
    """启动监听服务"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(10)  # 最多排队 10 个连接
    
    print(f"===== 生化仪器监听服务已启动 =====")
    print(f"监听地址：{HOST}:{PORT}")
    print(f"模式：仅打印原始数据，不解析\n")

    # 持续接受连接
    while True:
        client_sock, addr = server.accept()
        # 用线程处理，支持多台仪器同时连接
        client_thread = threading.Thread(
            target=handle_client,
            args=(client_sock, addr)
        )
        client_thread.daemon = True
        client_thread.start()

if __name__ == '__main__':
    start_server()