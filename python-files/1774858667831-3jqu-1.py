import os
import re
import socket
import threading
import telnetlib
import time
from pathlib import Path

# ================= 配置区域 =================
# 这里设置一个临时端口用来接收文件，默认 9999 即可
RECV_PORT = 9999 
# =============================================

def get_local_ip():
    """自动获取本机局域网 IP"""
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

def start_server_and_send_cmd(ip, port, save_filename):
    """
    1. 开启一个临时服务器监听端口
    2. 连接 Telnet 并命令设备向该端口发送数据
    3. 接收数据并保存
    """
    received_data = b""
    server_socket = None
    
    try:
        # --- 第一步：开启监听 ---
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(1)
        server_socket.settimeout(10) # 设置超时，防止一直卡着
        
        # --- 第二步：通过 Telnet 发送指令 ---
        # 使用 nc (netcat) 命令，这是嵌入式设备最通用的网络工具
        # 指令含义：把 setting.txt 的内容发送到 [本机IP] 的 [端口]
        cmd = f"nc {ip} {port} < setting.txt\n"
        
        tn = telnetlib.Telnet(ip_target, 23, timeout=5) # 注意：这里 ip_target 是外部传入的，稍后修正
        # 修正：上面的变量名写错了，应该是 ip 参数，但为了逻辑清晰，我们在主函数里调用
        
        # 重新整理 Telnet 逻辑
        tn = telnetlib.Telnet(ip, 23, timeout=10)
        tn.read_until(b'login:', timeout=5)
        tn.write(b'root\n')
        tn.read_until(b'Password:', timeout=5)
        tn.write(b'NRuapc2013++\n')
        tn.read_until(b'#', timeout=5)
        
        print(f"   -> 正在发送指令: nc {ip} {port} < setting.txt")
        tn.write(cmd.encode())
        
        # --- 第三步：接收文件数据 ---
        # 接受设备的连接
        conn, addr = server_socket.accept()
        conn.settimeout(10)
        print(f"   -> 设备已连接，正在接收数据...")
        
        while True:
            try:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                received_data += chunk
            except socket.timeout:
                break
        
        # --- 第四步：保存文件 ---
        with open(save_filename, 'wb') as f:
            f.write(received_data)
            
        print(f"   -> 成功！已保存 {len(received_data)} 字节")
        
        # 清理
        conn.close()
        tn.write(b'exit\n')
        tn.close()
        
    except Exception as e:
        print(f"   -> 失败: {str(e)}")
    finally:
        if server_socket:
            server_socket.close()

def main():
    my_ip = get_local_ip()
    print(f"本机 IP: {my_ip} (请确保设备能 Ping 通此 IP)")
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
            
            print(f"\n[任务] {device_name}")
            
            # 调用核心函数
            # 注意：这里我们需要把 ip_target 传进去，为了配合函数内部逻辑，稍微调整一下调用方式
            # 为了避免函数内部变量混淆，我们直接把逻辑写在 main 循环里或者传参要非常小心
            # 这里为了简单，直接在循环里写核心逻辑的变体，或者修正上面的函数
            
            # 修正后的直接调用逻辑（为了代码可读性，这里简化为直接执行）
            
            # 1. 开启监听
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(('0.0.0.0', RECV_PORT))
            server_socket.listen(1)
            server_socket.settimeout(10)
            
            # 2. 连 Telnet 发指令
            try:
                tn = telnetlib.Telnet(ip_target, 23, timeout=10)
                tn.read_until(b'login:', timeout=5)
                tn.write(b'root\n')
                tn.read_until(b'Password:', timeout=5)
                tn.write(b'NRuapc2013++\n')
                tn.read_until(b'#', timeout=5)
                
                # 发送 nc 指令
                cmd = f"nc {my_ip} {RECV_PORT} < setting.txt\n"
                tn.write(cmd.encode())
                
                # 3. 接收数据
                conn, addr = server_socket.accept()
                conn.settimeout(10)
                data = b""
                while True:
                    try:
                        d = conn.recv(4096)
                        if not d: break
                        data += d
                    except: break
                
                # 4. 保存
                with open(save_name, 'wb') as f:
                    f.write(data)
                print(f"   -> 成功接收: {save_name} ({len(data)} 字节)")
                
                tn.write(b'exit\n')
                tn.close()
                conn.close()
                
            except Exception as e:
                print(f"   -> 错误: {e}")
            finally:
                server_socket.close()

        except Exception as e:
            print(f"   -> 文件处理异常: {e}")

    print("\n所有任务结束。")

if __name__ == "__main__":
    main()