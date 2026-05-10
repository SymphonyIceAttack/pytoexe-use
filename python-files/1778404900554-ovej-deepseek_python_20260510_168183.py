#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows TCP 键盘发送器
- F1 : 更改目标 IP 和端口
- F2 : 连接目标
- F3 : 断开连接
- F4 : 修改备注（自动保存）
- ESC: 退出程序
"""

import socket
import sys
import os
import time
from pynput import keyboard

# ========== 全局变量 ==========
client_socket = None
connected = False
target_ip = ""
target_port = 0

CONFIG_FILE = "remark_config.txt"

def load_remark():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except:
            pass
    return "可用 F4 修改备注 (自动保存)"

def save_remark(remark_text):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(remark_text)
    except:
        pass

remark = load_remark()

# 日志记录（最多保留 20 条，界面只显示 5 行）
log_lines = []

# ========== ANSI 控制码 ==========
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def move_cursor(row, col):
    print(f"\033[{row};{col}H", end='')

def hide_cursor():
    print("\033[?25l", end='')

def show_cursor():
    print("\033[?25h", end='')

# ========== TCP 连接管理 ==========
def connect_to_server(host, port):
    global client_socket, connected
    try:
        if client_socket:
            client_socket.close()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(3)
        client_socket.connect((host, port))
        client_socket.settimeout(None)
        connected = True
        return True
    except Exception as e:
        connected = False
        return False

def disconnect():
    """断开当前连接"""
    global client_socket, connected
    if client_socket:
        client_socket.close()
        client_socket = None
    connected = False
    add_log("已断开连接")

# ========== 界面绘制 ==========
def draw_ui():
    clear_screen()
    hide_cursor()
    
    print("=" * 60)
    print("         Windows TCP 键盘发送器 (F1~F4 控制)")
    print("=" * 60)
    
    status_color = "\033[92m" if connected else "\033[91m"
    status_text = "● 已连接" if connected else "○ 未连接"
    print(f"状态: {status_color}{status_text}\033[0m")
    print(f"目标: {target_ip}:{target_port}")
    print(f"\n📝 备注: \033[93m{remark}\033[0m    (按 F4 修改)")
    
    print("\n操作说明:")
    print("  • F1 键 : 更改目标 IP 和端口")
    print("  • F2 键 : 连接当前目标")
    print("  • F3 键 : 断开当前连接")
    print("  • F4 键 : 修改备注 (自动保存)")
    print("  • ESC 键: 退出程序")
    print("-" * 60)
    
    print("【最近发送记录】(最多5行)")
    if not log_lines:
        print("  (暂无)")
    else:
        for line in log_lines[-5:]:
            print(f"  {line}")
    
    print("-" * 60)
    print("等待按键... (焦点在此窗口)")
    move_cursor(20, 1)

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_lines.append(f"[{timestamp}] {msg}")
    while len(log_lines) > 20:
        log_lines.pop(0)
    draw_ui()

# ========== F1: 更改目标 IP 和端口 ==========
def change_target():
    global target_ip, target_port
    show_cursor()
    clear_screen()
    print("========== 更改目标服务器 (F2 连接) ==========")
    new_ip = input("新的目标 IP 地址: ").strip()
    while True:
        try:
            new_port = int(input("新的目标端口: ").strip())
            if 1 <= new_port <= 65535:
                break
            print("端口范围 1-65535，请重新输入")
        except ValueError:
            print("请输入有效数字")
    
    target_ip = new_ip
    target_port = new_port
    add_log(f"目标已更改为 {target_ip}:{target_port} (未连接，请按 F2)")
    draw_ui()
    hide_cursor()

# ========== F2: 连接 ==========
def do_connect():
    global target_ip, target_port, connected
    if not target_ip or not target_port:
        add_log("请先按 F1 设置目标 IP 和端口")
        return
    # 如果已连接，先断开
    if connected:
        disconnect()
    if connect_to_server(target_ip, target_port):
        add_log(f"连接成功: {target_ip}:{target_port}")
    else:
        add_log(f"连接失败: {target_ip}:{target_port}")

# ========== F3: 断开连接 ==========
def do_disconnect():
    if connected:
        disconnect()
    else:
        add_log("当前未连接，无需断开")

# ========== F4: 修改备注 ==========
def change_remark():
    global remark
    show_cursor()
    clear_screen()
    print("========== 修改备注 ==========")
    new_remark = input("请输入新的备注内容: ").strip()
    if new_remark:
        remark = new_remark
        save_remark(remark)
        add_log(f"备注已修改为: {remark} (已保存)")
    else:
        add_log("备注未作修改")
    draw_ui()
    hide_cursor()

# ========== 发送按键值 ==========
def send_key(key_str):
    global connected, client_socket
    if not connected or client_socket is None:
        add_log(f"未连接，无法发送 \"{key_str}\"")
        return
    try:
        client_socket.sendall(key_str.encode('utf-8'))
        add_log(f"发送 -> {key_str}")
    except Exception as e:
        add_log(f"发送失败: {e}")
        disconnect()
        draw_ui()

# ========== 键盘回调 ==========
def on_press(key):
    # F1: 更改目标
    if key == keyboard.Key.f1:
        change_target()
        return
    # F2: 连接
    if key == keyboard.Key.f2:
        do_connect()
        return
    # F3: 断开
    if key == keyboard.Key.f3:
        do_disconnect()
        return
    # F4: 修改备注
    if key == keyboard.Key.f4:
        change_remark()
        return
    # ESC: 退出程序
    if key == keyboard.Key.esc:
        show_cursor()
        clear_screen()
        print("程序已退出")
        os._exit(0)
    
    # 其他键: 发送
    try:
        if hasattr(key, 'char') and key.char is not None:
            data = key.char
        else:
            data = f"<{key.name}>"
        send_key(data)
    except Exception as e:
        add_log(f"按键处理异常: {e}")

# ========== 主程序 ==========
def main():
    global target_ip, target_port, connected
    
    clear_screen()
    print("首次运行设置 (按 F1 可随时更改)")
    target_ip = input("请输入目标 IP 地址: ").strip()
    while True:
        try:
            target_port = int(input("请输入目标端口: ").strip())
            if 1 <= target_port <= 65535:
                break
            print("端口范围 1-65535，请重新输入")
        except ValueError:
            print("请输入有效数字")
    
    add_log(f"目标已设置为 {target_ip}:{target_port}，按 F2 连接")
    draw_ui()
    
    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        pass
    finally:
        disconnect()
        show_cursor()
        clear_screen()
        print("程序已退出")

if __name__ == "__main__":
    main()