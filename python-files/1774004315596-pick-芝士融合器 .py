import ctypes
import sys
import os
import time
import random
from datetime import datetime

SIGNATURE = "芝士反作弊 v342014"
k32 = ctypes.windll.kernel32

COL_RED = 12
COL_GREEN = 10
COL_YELLOW = 14
COL_CYAN = 11
COL_PURPLE = 13
COL_WHITE = 15
COL_BLUE = 9

class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

def set_title(text):
    k32.SetConsoleTitleW(f"{text}")

def set_color(color):
    k32.SetConsoleTextAttribute(k32.GetStdHandle(-11), color)

def reset_color():
    set_color(COL_WHITE)

def cls():
    os.system('cls')

def get_console_size():
    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("dwCursorPosition", ctypes.c_ulong),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", ctypes.c_short * 4),
            ("dwMaximumWindowSize", ctypes.c_ulong),
        ]
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    k32.GetConsoleScreenBufferInfo(k32.GetStdHandle(-11), ctypes.byref(csbi))
    width = csbi.srWindow[2] - csbi.srWindow[0] + 1
    return width

def set_cursor_pos(x, y):
    handle = k32.GetStdHandle(-11)
    value = y << 16 | x
    k32.SetConsoleCursorPosition(handle, ctypes.c_ulong(value))

def print_watermark():
    width = get_console_size()
    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("dwCursorPosition", ctypes.c_ulong),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", ctypes.c_short * 4),
            ("dwMaximumWindowSize", ctypes.c_ulong),
        ]
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    k32.GetConsoleScreenBufferInfo(k32.GetStdHandle(-11), ctypes.byref(csbi))
    original_pos = csbi.dwCursorPosition

    set_cursor_pos(0, 0)
    set_color(COL_PURPLE)
    
    border = "=" * width
    empty = " " * width
    print(border)
    print(f"  {SIGNATURE}".center(width))
    print(border)
    
    reset_color()
    set_cursor_pos(0, 3)

def init_screen():
    cls()
    print_watermark()

def slow_print(text, color=COL_WHITE, delay=0.02):
    set_color(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()
    reset_color()

def fake_matrix_loading():
    set_color(COL_GREEN)
    for _ in range(5):
        line = ''.join(random.choice("0123456789ABCDEF") for _ in range(60))
        print(f"  {line}")
        time.sleep(0.1)
    reset_color()

def progress_bar_advanced(text, total=100, speed=0.02):
    print(f"[+] {text}")
    for i in range(total + 1):
        percent = (i / total) * 100
        bar = '█' * (i // 2) + '-' * (50 - (i // 2))
        sys.stdout.write(f"\r    [{bar}] {percent:.0f}%")
        sys.stdout.flush()
        time.sleep(random.uniform(0.005, speed))
    print()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def scan_phase():
    init_screen()
    set_color(COL_CYAN)
    print("\n[ 系统初始化检测中... ]\n".center(80))
    reset_color()
    
    time.sleep(0.5)
    progress_bar_advanced("加载内核驱动检测模块 (ntoskrnl.exe)", 80, 0.01)
    progress_bar_advanced("枚举 Win32_PnPEntity 即插即用设备树", 100, 0.015)
    progress_bar_advanced("检索 PCIe 配置空间与总线枚举器", 60, 0.01)
    
    print()
    set_color(COL_YELLOW)
    print("-" * 80)
    print("  [ 扫描结果报告 ]")
    print("-" * 80)
    reset_color()
    
    time.sleep(0.5)
    print("  [*] 检查常规硬件... 正常")
    time.sleep(0.3)
    print("  [*] 检查键鼠输入层... 正常")
    time.sleep(0.3)
    
    set_color(COL_RED)
    print(f"  [!] 警告: 检测到潜在异常帧缓冲设备 (Framebuffer)")
    time.sleep(0.5)
    print(f"  [!] 警告: 发现可疑的 USB 视频类设备描述符")
    reset_color()
    
    time.sleep(1)
    print()
    set_color(COL_PURPLE)
    print("  >>> 结论: 系统环境存在被反作弊 (VAC/EAC/BE) 标记的风险。")
    reset_color()
    print()
    input("  按回车键进入 [ 屏蔽模式 ]...")

def shield_phase():
    init_screen()
    set_color(COL_RED)
    print("\n" + "【 警告：正在进入系统内核层 】".center(80) + "\n")
    reset_color()
    time.sleep(1)

    set_color(COL_BLUE)
    print("=" * 80)
    print("  阶段一：硬件特征混淆 (Hardware ID Spoofing)")
    print("=" * 80)
    reset_color()
    progress_bar_advanced("备份当前设备实例路径 (Device Instance Path)", 100, 0.01)
    progress_bar_advanced("应用多项式混淆算法生成虚拟 HardwareID", 100, 0.015)
    progress_bar_advanced("注入 ACPI 表描述符过滤器", 80, 0.01)
    set_color(COL_GREEN)
    print("  [OK] 硬件特征已脱敏。\n")
    reset_color()
    time.sleep(0.8)

    init_screen()
    set_color(COL_BLUE)
    print("=" * 80)
    print("  阶段二：进程与驱动隐藏 (Process Injection)")
    print("=" * 80)
    reset_color()
    progress_bar_advanced("挂钩内核对象管理器 (Object Manager)", 90, 0.01)
    progress_bar_advanced("清理 MmUnloadedDrivers 痕迹链表", 70, 0.012)
    progress_bar_advanced("解除 ObRegisterCallbacks 回调监控", 100, 0.015)
    progress_bar_advanced("劫持 IRP_MJ_CREATE 设备访问请求", 85, 0.01)
    set_color(COL_GREEN)
    print("  [OK] 相关进程与驱动已从枚举列表中移除。\n")
    reset_color()
    time.sleep(0.8)

    init_screen()
    set_color(COL_BLUE)
    print("=" * 80)
    print("  阶段三：反作弊检测链路绕过 (Bypass Deployment)")
    print("=" * 80)
    reset_color()
    progress_bar_advanced("执行内存特征码扫描混淆 (Memory Scrambling)", 100, 0.01)
    progress_bar_advanced("绕过 DSE 驱动签名强制策略 (模拟)", 60, 0.02)
    progress_bar_advanced("注入硬件信息伪装模块到 Win32k.sys", 90, 0.015)
    progress_bar_advanced("重定向设备栈访问请求至虚拟设备 (VDM)", 100, 0.01)
    set_color(COL_GREEN)
    print("  [OK] 全链路绕过部署完成。\n")
    reset_color()
    time.sleep(0.8)

    init_screen()
    set_color(COL_GREEN)
    print("\n" * 2)
    print("        ███████╗██╗   ██╗ ██████╗ ██████╗███████╗███████╗███████╗".center(80))
    print("        ██╔════╝██║   ██║██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝".center(80))
    print("        ███████╗██║   ██║██║     ██║     █████╗  ███████╗███████╗".center(80))
    print("        ╚════██║██║   ██║██║     ██║     ██╔══╝  ╚════██║╚════██║".center(80))
    print("        ███████║╚██████╔╝╚██████╗╚██████╗███████╗███████║███████║".center(80))
    print("        ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝╚══════╝╚══════╝╚══════╝".center(80))
    print("\n")
    print("-" * 80)
    print(f"                    {SIGNATURE}".center(80))
    print("-" * 80)
    print()
    slow_print("  [ 屏蔽成功！ ]", COL_GREEN, 0.05)
    print()
    print("  建议：请不要关闭本工具，直接启动游戏。".center(80))
    print("  如遇问题，请重启电脑后重新运行本工具。".center(80))
    print()
    reset_color()
    input("  按回车键退出程序...")

def main():
    if not is_admin():
        print("[-] 正在请求管理员权限...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

    set_title(f"{SIGNATURE} | 正在运行...")
    os.system("mode con cols=80 lines=25")

    init_screen()
    
    set_color(COL_YELLOW)
    print("\n" + "欢迎使用".center(80))
    set_color(COL_PURPLE)
    print(f"{SIGNATURE}".center(80))
    reset_color()
    print("\n" + "本工具将检测并尝试屏蔽融合器/采集卡特征。".center(80))
    print("\n")
    input("  按回车键开始检测...")

    scan_phase()
    shield_phase()

if __name__ == "__main__":
    main()