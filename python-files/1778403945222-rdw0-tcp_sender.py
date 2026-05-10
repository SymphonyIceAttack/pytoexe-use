#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows TCP 键盘发送器
按下任意键，立即通过 TCP Socket 发送到指定 IP:Port
"""

import socket
import sys
from pynput import keyboard

client_socket = None
connected = False

def connect_to_server(host, port):
    global client_socket, connected
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        connected = True
        print(f"[✓] 已连接到 {host}:{port} (TCP 连接成功)")
        return True
    except Exception as e:
        print(f"[✗] 连接失败: {e}")
        connected = False
        return False

def close_connection():
    global client_socket, connected
    if client_socket:
        client_socket.close()
        client_socket = None
    connected = False
    print("[ ] 连接已关闭")

def on_press(key):
    global client_socket, connected
    if not connected or client_socket is None:
        return
    try:
        if hasattr(key, 'char') and key.char is not None:
            data = key.char
        else:
            data = f"<{key.name}>"
        client_socket.sendall(data.encode('utf-8'))
        print(f"[发送] {data}")
    except Exception as e:
        print(f"[错误] 发送失败: {e}")
        close_connection()

def main():
    print("=" * 50)
    print("       Windows TCP 键盘按键发送器")
    print("   按下任意键 → 发送到指定 IP:Port")
    print("=" * 50)

    target_ip = input("请输入目标 IP 地址: ").strip()
    while True:
        try:
            target_port = int(input("请输入目标端口: ").strip())
            if 1 <= target_port <= 65535:
                break
            print("端口范围 1-65535，请重新输入")
        except ValueError:
            print("请输入有效的数字端口")

    if not connect_to_server(target_ip, target_port):
        print("无法连接到目标服务器，程序退出。")
        input("按 Enter 键退出...")
        sys.exit(1)

    print("\n[监听中] 键盘已捕获，按下任意键即可发送")
    print("提示：特殊键会以 <key_name> 形式发送，如 <enter>、<space>")
    print("按 Ctrl+C 或关闭窗口可退出程序\n")

    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    finally:
        close_connection()
        print("程序已退出")

if __name__ == "__main__":
    main()