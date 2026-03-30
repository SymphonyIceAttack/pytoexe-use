import os
import re
import socket
import telnetlib
import time
from pathlib import Path

# ================= 配置区域 =================
# 【关键】如果你的电脑有多个 IP，请在这里手动指定！
# 留空 "" 表示自动获取（可能会选错网卡）
# 例如手动指定：MANUAL_IP = "192.168.1.100"
MANUAL_IP = "" 

# 接收文件用的端口，默认即可
RECV_PORT = 9999 
# =============================================

def get_local_ip():
    """获取本机 IP，优先使用手动指定的 IP"""
    if MANUAL_IP:
        return MANUAL_IP
        
    # 自动获取逻辑（使用 UDP 连接法，比 gethostname 更准）
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 这里的 IP 不需要真实连通，只是为了获取网卡 IP
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def clean_filename(name):
    """清洗文件名，去除特殊字符"""
    return re.sub(r'[^a-zA-Z0-9_]', '', name)

def main():
    my_ip = get_local_ip()
    print(f"当前使用的本机 IP: {my_ip}")
    if not MANUAL_IP:
        print("提示: 如果此 IP 错误，请在代码第 13 行手动指定 MANUAL_IP")
    print("-" * 30)

    # 遍历所有 .apjp 文件
    for apjp_file in Path('.').rglob('*.apjp'):
        try:
            # 提取 IP
            content = apjp_file.read_text(encoding='utf-8')
            ip_match = re.search(r'curip=\"([^\"]+)\"', content)
            if not ip_match:
                continue
                
            ip_target = ip_match.group(1) # 设备的 IP
            device_name = clean_filename(apjp_file.stem)
            save_name = f"{device_name}.txt"
            
            print(f"\n[任务] {device_name} -> {ip_target}")
            
            # 1. 开启监听 (作为服务器)
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 允许端口复用
            server_socket.bind(('0.0.0.0', RECV_PORT))
            server_socket.listen(1)
            server_socket.settimeout(15) # 增加超时时间，防止设备太慢
            
            # 2. 连 Telnet 发指令
            try:
                print(f"   -> 正在连接设备...")
                tn = telnetlib.Telnet(ip_target, 23, timeout=10)
                tn.read_until(b'login:', timeout=5)
                tn.write(b'root\n')
                tn.read_until(b'Password:', timeout=5)
                tn.write(b'NRuapc2013++\n')
                tn.read_until(b'#', timeout=5)
                
                # 发送 nc 指令
                # 注意：这里使用的是上面确定的 my_ip
                cmd = f"nc {my_ip} {RECV_PORT} < setting.txt\n"
                print(f"   -> 发送指令: {cmd.strip()}")
                tn.write(cmd.encode())
                
                # 3. 接收数据
                print(f"   -> 等待设备连接...")
                conn, addr = server_socket.accept()
                conn.settimeout(10)
                data = b""
                
                print(f"   -> 正在接收数据...")
                while True:
                    try:
                        d = conn.recv(4096)
                        if not d: break
                        data += d
                    except: break
                
                # 4. 保存
                if data:
                    with open(save_name, 'wb') as f:
                        f.write(data)
                    print(f"   -> 成功接收: {save_name} ({len(data)} 字节)")
                else:
                    print(f"   -> 接收为空，可能文件不存在或权限不足")
                
                # 清理 Telnet
                try:
                    tn.write(b'exit\n')
                    tn.close()
                except: pass
                conn.close()
                
            except Exception as e:
                print(f"   -> 错误: {e}")
            finally:
                server_socket.close()

        except Exception as e:
            print(f"   -> 文件处理异常: {e}")

    print("\n所有任务结束。")
    input("按回车退出...")

if __name__ == "__main__":
    main()