#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import ctypes
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard

# ---------------------------- 配置文件 ----------------------------
def get_config_path():
    """获取配置文件路径（支持 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "unlocker_config.json")

CONFIG_FILE = get_config_path()

# ---------------------------- 键盘模拟（Windows API）--------------------
VK_RETURN = 0x0D
KEYEVENTF_KEYUP = 0x0002
user32 = ctypes.windll.user32

def key_down(vk_code):
    user32.keybd_event(vk_code, 0, 0, 0)

def key_up(vk_code):
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def type_string(text):
    """
    模拟输入字符串（支持 ASCII 字符及常见符号，自动处理 Shift）
    注意：不支持中文等非 ASCII 字符，Windows 密码很少使用中文。
    """
    for ch in text:
        # 获取虚拟键码和 Shift 状态
        vk = user32.VkKeyScanA(ord(ch))
        if vk == 0xFFFF:
            continue   # 无法映射的字符跳过
        vk_code = vk & 0xFF
        shift = (vk >> 8) & 0x1
        if shift:
            key_down(0x10)   # VK_SHIFT
        key_down(vk_code)
        key_up(vk_code)
        if shift:
            key_up(0x10)
        time.sleep(0.02)     # 短暂延迟，防止输入过快

def send_enter():
    key_down(VK_RETURN)
    key_up(VK_RETURN)

# ---------------------------- 全局变量与监听 ----------------------------
current_password = ""
password_lock = threading.Lock()
listener = None
last_enter_time = 0
DOUBLE_CLICK_THRESHOLD = 0.5   # 秒

def on_press(key):
    global last_enter_time
    if key == keyboard.Key.enter:
        now = time.time()
        if now - last_enter_time <= DOUBLE_CLICK_THRESHOLD:
            with password_lock:
                pwd = current_password
            if pwd:
                print("检测到两次回车，开始输入密码...")
                type_string(pwd)
                send_enter()
            else:
                print("密码为空，请先在 GUI 中设置密码。")
            last_enter_time = 0   # 防止连续触发
        else:
            last_enter_time = now

def start_listener():
    global listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def stop_listener():
    if listener and listener.running:
        listener.stop()

# ---------------------------- GUI 界面 ----------------------------
class UnlockerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 自动解锁助手")
        self.root.geometry("420x220")
        self.root.resizable(False, False)

        # 加载已保存的密码
        self.saved_password = self.load_password_from_file()
        # 更新全局密码
        with password_lock:
            global current_password
            current_password = self.saved_password

        # 界面控件
        tk.Label(root, text="Windows 登录密码：", font=("微软雅黑", 12)).pack(pady=15)
        self.pwd_entry = tk.Entry(root, show="*", font=("微软雅黑", 12), width=28)
        self.pwd_entry.pack(pady=5)
        self.pwd_entry.insert(0, self.saved_password)

        self.save_btn = tk.Button(root, text="保存密码并启用", command=self.save_password,
                                  font=("微软雅黑", 10), bg="#4CAF50", fg="white", width=22)
        self.save_btn.pack(pady=15)

        self.status_label = tk.Label(root, text="", font=("微软雅黑", 9))
        self.status_label.pack()
        self.update_status()

        # 提示信息
        tip = tk.Label(root, text="提示：连续按两次回车（间隔 ≤ 0.5 秒）将自动输入密码并解锁。\n程序已在后台监听，关闭窗口会停止服务。",
                       font=("微软雅黑", 8), fg="blue", justify=tk.LEFT)
        tip.pack(side=tk.BOTTOM, pady=10)

    def load_password_from_file(self):
        """从配置文件读取密码"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("password", "")
            except Exception as e:
                print(f"读取配置文件失败: {e}")
        return ""

    def save_password(self):
        """保存密码到文件并更新全局变量"""
        new_pwd = self.pwd_entry.get()
        if not new_pwd:
            if not messagebox.askyesno("确认", "密码为空，将无法自动解锁。是否继续？"):
                return
        # 保存到 JSON 文件
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"password": new_pwd}, f, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败：{e}")
            return

        # 更新全局密码
        with password_lock:
            global current_password
            current_password = new_pwd
        self.update_status()
        messagebox.showinfo("成功", "密码已保存，现在可以在锁屏界面连续按两次回车自动解锁。")

    def update_status(self):
        """更新状态标签"""
        with password_lock:
            if current_password:
                self.status_label.config(text=f"✓ 已设置密码（长度 {len(current_password)} 位）", fg="green")
            else:
                self.status_label.config(text="✗ 未设置密码，请先保存密码", fg="red")

# ---------------------------- 管理员权限检查 ----------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员权限重新启动当前脚本"""
    script = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)

# ---------------------------- 主程序 ----------------------------
def main():
    # 检查并申请管理员权限
    if not is_admin():
        print("当前不是管理员权限，正在请求提升...")
        run_as_admin()
        sys.exit(0)

    # 启动后台键盘监听
    start_listener()

    # 创建 GUI 窗口
    root = tk.Tk()
    app = UnlockerGUI(root)

    # 窗口关闭事件：停止监听并退出
    def on_closing():
        if messagebox.askokcancel("退出", "关闭窗口后，自动解锁服务将停止。确定退出吗？"):
            stop_listener()
            root.destroy()
            sys.exit(0)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()