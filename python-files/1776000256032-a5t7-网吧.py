import os
import sys
import ctypes
import time
import threading
from tkinter import *
from tkinter import messagebox
import win32gui
import win32con
import win32api
import psutil

# 禁用关闭按钮的常量
GWLP_GWLP_HWND = -8  # 修正：GWLP_HWND 的替代
GWL_STYLE = -16
WS_SYSMENU = 0x00080000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000

# 正确的十六进制值（转为字节）
VALID_BYTES = bytes([
    0x49, 0x6E, 0x74, 0x65, 0x72, 0x6E, 0x65, 0x74, 0x20, 0x63, 0x61, 0x66, 0x65, 0x20, 0x64, 0x65,
    0x64, 0x69, 0x63, 0x61, 0x74, 0x65, 0x64, 0x20, 0x55, 0x53, 0x42, 0x20, 0x6B, 0x65, 0x79, 0x20,
    0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x20, 0x49, 0x6E, 0x74, 0x65, 0x72, 0x6E, 0x65, 0x74, 0x20, 0x63,
    0x61, 0x66, 0x65
])

# 全局变量
mode = "NORMAL"  # NORMAL 或 UNLIMITED
card_no = ""
remaining_seconds = 0
timer_running = False
idle_timer = None
root = None

def is_admin():
    """检查是否管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def disable_close_button():
    """禁用窗口的关闭按钮和Alt+F4"""
    hwnd = win32gui.FindWindow(None, "网吧登录器")
    if hwnd:
        # 移除关闭按钮（保留最小化按钮）
        style = win32gui.GetWindowLong(hwnd, GWL_STYLE)
        style = style & ~WS_SYSMENU  # 移除系统菜单（关闭按钮）
        style = style | WS_MINIMIZEBOX  # 保留最小化按钮
        win32gui.SetWindowLong(hwnd, GWL_STYLE, style)
        win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

def fullscreen():
    """全屏窗口"""
    root.attributes('-fullscreen', True)
    root.focus_set()

def check_idle_time():
    """检测闲置时间，超过5分钟关机"""
    global idle_timer
    last_input = win32api.GetLastInputInfo()
    idle_seconds = (time.time() - last_input) / 1000
    
    if idle_seconds > 300:  # 5分钟 = 300秒
        # 倒计时10秒提示
        for i in range(10, 0, -1):
            msg = f"系统空闲超过5分钟，将在 {i} 秒后关机。请移动鼠标取消。"
            show_toast("即将关机", msg)
            time.sleep(1)
            # 重新检测是否还有输入
            if (time.time() - win32api.GetLastInputInfo() / 1000) < 1:
                return  # 有操作，取消关机
        os.system("shutdown /s /t 0")
    else:
        # 每30秒检测一次
        idle_timer = threading.Timer(30, check_idle_time)
        idle_timer.daemon = True
        idle_timer.start()

def show_toast(title, message, duration=3):
    """右下角弹窗提示"""
    toast = Toplevel(root)
    toast.title(title)
    toast.geometry("300x100")
    toast.attributes('-topmost', True)
    
    # 放到右下角
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = screen_width - 320
    y = screen_height - 140
    toast.geometry(f"+{x}+{y}")
    
    Label(toast, text=message, wraplength=280, font=("微软雅黑", 10)).pack(pady=20)
    toast.after(duration * 1000, toast.destroy)

def check_usb():
    """检测U盘授权"""
    import string
    for drive in string.ascii_uppercase:
        drive_path = f"{drive}:\\"
        if os.path.exists(drive_path):
            try:
                # 检查卷标
                vol_label = win32api.GetVolumeInformation(drive_path)[0]
                if vol_label == "网吧":
                    # 检查key.dll
                    key_path = os.path.join(drive_path, "key.dll")
                    if os.path.exists(key_path):
                        with open(key_path, "rb") as f:
                            content = f.read()
                            if content == VALID_BYTES:
                                return True
            except:
                continue
    return False

def start_timer(seconds):
    """开始倒计时"""
    global timer_running, remaining_seconds
    timer_running = True
    remaining_seconds = seconds
    
    def update_timer():
        global remaining_seconds, timer_running
        while remaining_seconds > 0 and timer_running:
            mins = remaining_seconds // 60
            secs = remaining_seconds % 60
            timer_label.config(text=f"剩余时间: {mins:02d}:{secs:02d}")
            root.update()
            time.sleep(1)
            remaining_seconds -= 1
        
        if remaining_seconds <= 0 and timer_running:
            timer_running = False
            messagebox.showwarning("时间到", "上机时间已到，即将锁屏")
            ctypes.windll.user32.LockWorkStation()
            # 锁屏后返回登录界面
            root.quit()
            os.system("start 网吧登录器.exe")
            sys.exit()
    
    timer_thread = threading.Thread(target=update_timer, daemon=True)
    timer_thread.start()

def login_with_card():
    """卡号密码登录"""
    global mode, remaining_seconds
    card = entry_card.get()
    pwd = entry_pwd.get()
    
    if not card or not pwd:
        messagebox.showerror("错误", "请输入卡号和密码")
        return
    
    # 这里简化处理：卡号密码任意非空即可，时长1小时
    mode = "NORMAL"
    remaining_seconds = 3600  # 1小时
    show_toast("登录成功", f"卡号 {card} 上机1小时")
    
    # 隐藏登录界面，显示计时界面
    login_frame.pack_forget()
    timer_frame.pack(expand=True, fill=BOTH)
    start_timer(remaining_seconds)
    
    # 启动闲置检测
    check_idle_time()

def login_with_usb():
    """USB授权登录"""
    global mode
    if check_usb():
        mode = "UNLIMITED"
        show_toast("无限时长", "授权U盘验证成功，本机不计时")
        
        # 隐藏登录界面，显示无限时长界面
        login_frame.pack_forget()
        unlimited_frame.pack(expand=True, fill=BOTH)
        
        # USB模式不启动闲置检测（或可选）
        # check_idle_time()
    else:
        messagebox.showerror("授权失败", "未检测到有效授权U盘\n请确保：\n1. U盘卷标为'网吧'\n2. 根目录有key.dll文件")

def minimize_window():
    """最小化窗口"""
    root.iconify()

def exit_program():
    """退出程序（需要密码）"""
    pwd = simpledialog.askstring("退出验证", "请输入管理员密码:", show='*')
    if pwd == "admin123":  # 默认密码，可以改
        os.system("shutdown /a")  # 取消关机
        if idle_timer:
            idle_timer.cancel()
        root.quit()
        sys.exit()
    else:
        messagebox.showerror("错误", "密码错误")

def on_closing():
    """禁用直接关闭"""
    pass  # 什么都不做，阻止关闭

# 创建主窗口
root = Tk()
root.title("网吧登录器")
root.geometry("800x600")
root.configure(bg='#1a1a2e')

# 全屏
fullscreen()

# 禁用关闭按钮
root.protocol("WM_DELETE_WINDOW", on_closing)
root.after(100, disable_close_button)

# 绑定Alt+F4
root.bind('<Alt-F4>', lambda e: "break")

# 设置字体
title_font = ("微软雅黑", 24, "bold")
btn_font = ("微软雅黑", 14)

# ========== 登录界面 ==========
login_frame = Frame(root, bg='#1a1a2e')
login_frame.pack(expand=True, fill=BOTH)

Label(login_frame, text="网吧登录系统", font=title_font, fg='white', bg='#1a1a2e').pack(pady=50)

# 卡号登录区域
card_frame = Frame(login_frame, bg='#1a1a2e')
card_frame.pack(pady=30)

Label(card_frame, text="卡号:", font=btn_font, fg='white', bg='#1a1a2e').grid(row=0, column=0, padx=10, pady=10)
entry_card = Entry(card_frame, font=btn_font, width=20)
entry_card.grid(row=0, column=1, padx=10, pady=10)

Label(card_frame, text="密码:", font=btn_font, fg='white', bg='#1a1a2e').grid(row=1, column=0, padx=10, pady=10)
entry_pwd = Entry(card_frame, show="*", font=btn_font, width=20)
entry_pwd.grid(row=1, column=1, padx=10, pady=10)

Button(card_frame, text="卡号登录", command=login_with_card, font=btn_font, bg='#e94560', fg='white', width=15).grid(row=2, column=0, columnspan=2, pady=20)

# USB登录按钮
Button(login_frame, text="USB授权登录", command=login_with_usb, font=btn_font, bg='#533483', fg='white', width=20).pack(pady=20)

# 退出按钮（需要密码）
Button(login_frame, text="退出系统", command=exit_program, font=btn_font, bg='#333', fg='white', width=20).pack(pady=10)

# ========== 计时界面 ==========
timer_frame = Frame(root, bg='#1a1a2e')
Label(timer_frame, text="上机中", font=title_font, fg='white', bg='#1a1a2e').pack(pady=50)
timer_label = Label(timer_frame, text="剩余时间: 00:00", font=("微软雅黑", 32), fg='#e94560', bg='#1a1a2e')
timer_label.pack(pady=30)
Button(timer_frame, text="最小化", command=minimize_window, font=btn_font, bg='#533483', fg='white', width=15).pack(pady=20)

# ========== 无限时长界面 ==========
unlimited_frame = Frame(root, bg='#1a1a2e')
Label(unlimited_frame, text="无限时长模式", font=title_font, fg='#00ff00', bg='#1a1a2e').pack(pady=50)
Label(unlimited_frame, text="授权U盘已激活，本机不计费", font=("微软雅黑", 16), fg='white', bg='#1a1a2e').pack(pady=20)
Button(unlimited_frame, text="最小化", command=minimize_window, font=btn_font, bg='#533483', fg='white', width=15).pack(pady=30)

# 启动闲置检测（仅在普通模式下启用，在USB模式下可选）
# 先不启动，等登录成功后再启动

# 运行主循环
root.mainloop()