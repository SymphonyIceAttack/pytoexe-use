import os
import re
import socket
import telnetlib
import time
from pathlib import Path

# ================= 配置区域 =================
RECV_PORT = 9999 
# =============================================

def get_all_ips():
    """获取本机所有 IPv4 地址"""
    hostname = socket.gethostname()
    ip_list = []
    # 获取所有网卡信息
    try:
        # 这种方法能获取到大部分网卡IP
        addrs = socket.getaddrinfo(hostname, None)
        for item in addrs:
            if item[0] == socket.AF_INET: # 只要 IPv4
                ip = item[4][0]
                # 过滤掉回环地址
                if not ip.startswith('127.'):
                    if ip not in ip_list:
                        ip_list.append(ip)
    except:
        pass
    
    # 如果上面没获取到，尝试一种更底层的备用方案（可选）
    # 但通常 getaddrinfo 对 Windows 够用了
    
    return ip_list

def clean_filename(name):
    """清洗文件名，去除特殊字符"""
    return re.sub(r'[^a-zA-Z0-9_]', '', name)

def main():
    # --- 第一步：IP 选择菜单 ---
    all_ips = get_all_ips()
    
    if not all_ips:
        print("错误：未检测到任何网络 IP 地址，请检查网卡设置。")
        input("按回车退出...")
        return

    print("检测到本机有以下 IP 地址：")
    print("-" * 30)
    for i, ip in enumerate(all_ips):
        print(f" {i + 1}. {ip}")
    print("-" * 30)
    
    # 让用户选择
    while True:
        try:
            choice = input(f"请输入要使用的 IP 序号 (1-{len(all_ips)}): ")
            choice_num = int(choice)
            if 1 <= choice_num <= len(all_ips):
                my_ip = all_ips[choice_num - 1]
                break
            else:
                print("输入的序号无效，请重试。")
        except ValueError:
            print("请输入数字！")
            
    print(f"已选择 IP: {my_ip} (请确保设备能 Ping 通此 IP)")
    print("-" * 30)

    # --- 第二步：开始任务 ---
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
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 绑定到用户选择的特定 IP，而不是 0.0.0.0，这样更安全准确
            server_socket.bind((my_ip, RECV_PORT))
            server_socket.listen(1)
            server_socket.settimeout(15) 
            
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
                    print(f"   -> 接收为空，可能文件不存在")
                
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