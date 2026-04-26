# ========== 后端中转服务端（唯一中枢，所有用户端连接这里） ==========
import socket
import threading
import json
import time

# 基础配置
BIND_HOST = "0.0.0.0"
BIND_PORT = 55555  # FRP只需要穿透这一个端口
BUFFER_SIZE = 1024 * 16

# 全局设备池：存放所有在线用户设备
device_list = []
device_lock = threading.Lock()

class DeviceNode:
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.is_share = False   # 是否开启屏幕共享
        self.target_addr = None # 要控制的目标设备

def broadcast_device_list():
    """广播在线设备列表给所有客户端"""
    with device_lock:
        online_dev = [
            {"ip":str(d.addr[0]), "port":str(d.addr[1]), "share":d.is_share}
            for d in device_list
        ]
    data = json.dumps({"type":"device_list","data":online_dev}).encode("utf-8")
    with device_lock:
        for d in device_list:
            try:
                d.sock.send(data)
            except:
                pass

def handle_client(sock, addr):
    """处理单个用户端连接"""
    node = DeviceNode(sock, addr)
    with device_lock:
        device_list.append(node)
    print(f"[+] 新设备接入：{addr}，当前在线：{len(device_list)}")
    broadcast_device_list()

    try:
        while True:
            raw = sock.recv(BUFFER_SIZE)
            if not raw:
                break
            try:
                msg = json.loads(raw.decode("utf-8"))
                msg_type = msg.get("type")

                # 1. 用户开启/关闭屏幕共享
                if msg_type == "set_share":
                    node.is_share = msg.get("status", False)
                    broadcast_device_list()

                # 2. 屏幕画面数据 → 转发给指定控制端
                elif msg_type == "screen_data":
                    target_ip = msg.get("target_ip")
                    with device_lock:
                        for d in device_list:
                            if d.addr[0] == target_ip:
                                try:
                                    d.sock.send(raw)
                                except:
                                    pass

                # 3. 控制指令/鼠标/键盘/CMD/留言 → 转发给目标
                elif msg_type in ["mouse","keyboard","cmd","msg"]:
                    target_ip = msg.get("target_ip")
                    with device_lock:
                        for d in device_list:
                            if d.addr[0] == target_ip:
                                try:
                                    d.sock.send(raw)
                                except:
                                    pass
            except Exception as e:
                continue
    except:
        pass

    # 设备下线
    with device_lock:
        if node in device_list:
            device_list.remove(node)
    print(f"[-] 设备下线：{addr}，当前在线：{len(device_list)}")
    broadcast_device_list()
    sock.close()

def main_server():
    """启动后端中转服务"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((BIND_HOST, BIND_PORT))
    server.listen(100)
    print("="*50)
    print("✅ 屏幕共享平台 后端中转服务已启动")
    print(f"监听端口：{BIND_PORT}")
    print("⚠️ 搭配FRP内网穿透，映射 55555 端口")
    print("="*50)

    while True:
        cli_sock, cli_addr = server.accept()
        t = threading.Thread(target=handle_client, args=(cli_sock, cli_addr), daemon=True)
        t.start()

if __name__ == "__main__":
    main_server()