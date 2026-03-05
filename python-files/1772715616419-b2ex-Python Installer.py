#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python Installer
直接双击运行进入命令行分页界面，使用 --gui 参数启动图形界面。
"""

import sys
import os
import subprocess
import zipfile
import datetime
import argparse
import shutil
import time
import tempfile
from pathlib import Path

# ====================== 平台相关初始化 ======================
try:
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 0x0004 | 0x0001 | 0x0002 | 0x0008)
except:
    pass

# 颜色定义（CLI）
GREEN = '\033[92m'
RESET = '\033[0m'

# 全局常量
DATA_FILE = Path(__file__).parent / "PyIn.wzt"       # 数据文件（ZIP 格式，带 .wzt 后缀）
TEMP_DIR = Path(tempfile.gettempdir()) / "wzt_cache" # 临时目录位于系统临时文件夹下

# 方块阴影风格 WZT
WZT_ART = [
    "██╗    ██╗███████╗████████╗",
    "██║    ██║╚══███╔╝╚══██╔══╝",
    "██║ █╗ ██║  ███╔╝    ██║   ",
    "██║███╗██║ ███╔╝     ██║   ",
    "╚███╔███╔╝███████╗   ██║   ",
    " ╚══╝╚══╝ ╚══════╝   ╚═╝   "
]

# ====================== 公用工具函数 ======================

def extract_wzt():
    """解压 PyIn.wzt 文件到临时目录，返回安装包文件列表（处理 Python Installer 文件夹）"""
    if not DATA_FILE.exists():
        print("错误：未找到数据文件 'PyIn.wzt'，请将其放在程序同目录下。")
        return []

    # 清空并重建临时目录
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(DATA_FILE, 'r') as zf:
            zf.extractall(TEMP_DIR)
    except Exception as e:
        print(f"解压失败：{e}")
        return []

    # 查找临时目录下的 Python Installer 文件夹
    installer_dir = TEMP_DIR / "Python Installer"
    if not installer_dir.exists():
        # 兼容可能多出一层的情况（例如解压后得到一个文件夹，其内部有 Python Installer）
        for item in TEMP_DIR.iterdir():
            if item.is_dir():
                potential = item / "Python Installer"
                if potential.exists():
                    installer_dir = potential
                    break
        else:
            print("警告：未找到预期的目录结构 'Python Installer'")
            return []

    installers = []
    for ext in ('.exe', '.msi'):
        installers.extend(installer_dir.glob(f'*{ext}'))
    return sorted(installers)

def get_version_display(path):
    return path.stem

def wait_for_pid(pid):
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        SYNCHRONIZE = 0x00100000
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
            kernel32.CloseHandle(handle)
    except:
        while True:
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                    capture_output=True, text=True)
            if str(pid) not in result.stdout:
                break
            time.sleep(1)

def launch_installer_and_exit(installer_path):
    proc = subprocess.Popen([str(installer_path)], shell=True)
    pid = proc.pid

    subprocess.Popen([
        sys.executable, __file__,
        '--wait-pid', str(pid),
        '--temp-dir', str(TEMP_DIR)
    ])

    sys.exit(0)

def show_thanks_and_cleanup(temp_dir):
    # 清屏，让用户看到干净的感谢信息
    os.system('cls' if os.name == 'nt' else 'clear')
    year = datetime.datetime.now().year
    print("\n感谢使用 Python Installer！我们有缘再见～")
    print(f"Copyright WZT {year}")
    if temp_dir and Path(temp_dir).exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    input("\n按 Enter 键退出...")

# ====================== 命令行分页界面 ======================

def cli_main():
    pages = [page_welcome, page_ask_gui, page_ask_winget, page_choose_version]
    current = 0
    while 0 <= current < len(pages):
        current = pages[current]()

def page_welcome():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("欢迎来到 Python Installer！")
    print("这个程序将帮助您下载许多版本的 Python！\n")
    for line in WZT_ART:
        print(GREEN + line + RESET)
    input("\n按 Enter 键进入下一页...")
    return 1

def page_ask_gui():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("是否使用图形界面（GUI）下载？")
    print("1. 是（启动 GUI 版本）")
    print("2. 否（继续使用命令行）")
    choice = input("请选择 (1/2)：").strip()
    if choice == '1':
        subprocess.Popen([sys.executable, __file__, '--gui'])
        sys.exit(0)
    else:
        return 2

def page_ask_winget():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("为了更好地使用体验，你可以使用 Python 官方的 Python Install Manager。")
    print("需要安装吗？(winget install 9NQ7512CXL7T)")
    print("1. 是（启动 winget 安装，本程序退出）")
    print("2. 否（继续选择本地版本）")
    choice = input("请选择 (1/2)：").strip()
    if choice == '1':
        if sys.platform == 'win32':
            os.system('start cmd /k winget install 9NQ7512CXL7T')
        else:
            print("winget 仅支持 Windows，按任意键返回...")
            input()
            return 2
        sys.exit(0)
    else:
        return 3

def page_choose_version():
    os.system('cls' if os.name == 'nt' else 'clear')
    installers = extract_wzt()
    if not installers:
        print("未找到任何安装包，请检查 PyIn.wzt 文件内容。")
        input("按 Enter 键返回上一页...")
        return 2

    print("可用的 Python 版本：")
    for idx, inst in enumerate(installers, 1):
        print(f"{idx}. {get_version_display(inst)}")
    print("0. 返回上一页")

    choice = input("请选择版本编号：").strip()
    if choice == '0':
        return 2
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(installers):
            launch_installer_and_exit(installers[idx])
        else:
            print("无效选择，请重试。")
            input()
            return 3
    except ValueError:
        print("请输入数字。")
        input()
        return 3

# ====================== GUI 界面 ======================

def gui_main():
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except ImportError:
        print("错误：当前环境不支持 tkinter，无法启动 GUI。")
        sys.exit(1)

    root = tk.Tk()
    root.title("Python Installer")
    root.geometry("650x450")
    root.resizable(False, False)

    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    pages = {}

    def show_page(page_name):
        # 隐藏所有页面
        for f in pages.values():
            f.pack_forget()
        # 显示目标页面
        pages[page_name].pack(fill="both", expand=True)

    # 创建页面（仅创建并存储，不pack）
    create_page_welcome(container, pages, show_page)
    create_page_ask_winget(container, pages, show_page)
    create_page_choose_version(container, pages, show_page)

    show_page("Welcome")
    root.mainloop()

def create_page_welcome(parent, pages, show_page):
    import tkinter as tk
    from tkinter import ttk
    frame = ttk.Frame(parent)
    pages["Welcome"] = frame

    ttk.Label(frame, text="欢迎来到 Python Installer！",
              font=("Arial", 16)).pack(pady=30)
    ttk.Label(frame, text="这个程序将帮助您下载许多版本的 Python！").pack(pady=10)

    art_frame = ttk.Frame(frame)
    art_frame.pack(pady=20)
    for line in WZT_ART:
        lbl = tk.Label(art_frame, text=line, fg="green",
                       font=("Courier New", 12, "bold"))
        lbl.pack()

    ttk.Button(frame, text="下一页",
               command=lambda: show_page("AskWinget")).pack(pady=30)

def create_page_ask_winget(parent, pages, show_page):
    import tkinter as tk
    from tkinter import ttk, messagebox
    frame = ttk.Frame(parent)
    pages["AskWinget"] = frame

    ttk.Label(frame, text="使用 Python 官方 Install Manager？",
              font=("Arial", 14)).pack(pady=30)
    ttk.Label(frame, text="winget install 9NQ7512CXL7T",
              foreground="blue").pack(pady=10)

    def install_winget():
        if sys.platform == 'win32':
            os.system('start cmd /k winget install 9NQ7512CXL7T')
            frame.winfo_toplevel().quit()
        else:
            messagebox.showerror("错误", "winget 仅支持 Windows")

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=20)
    ttk.Button(btn_frame, text="是，安装", command=install_winget).pack(side="left", padx=10)
    ttk.Button(btn_frame, text="否，手动选择版本",
               command=lambda: show_page("ChooseVersion")).pack(side="left", padx=10)

    ttk.Button(frame, text="上一步",
               command=lambda: show_page("Welcome")).pack(pady=30)

def create_page_choose_version(parent, pages, show_page):
    import tkinter as tk
    from tkinter import ttk, messagebox
    frame = ttk.Frame(parent)
    pages["ChooseVersion"] = frame

    ttk.Label(frame, text="选择要下载的 Python 版本",
              font=("Arial", 14)).pack(pady=10)

    list_frame = ttk.Frame(frame)
    list_frame.pack(pady=10, padx=20, fill="both", expand=True)

    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side="right", fill="y")

    listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                         height=12, selectmode="single")
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)

    def refresh_list():
        installers = extract_wzt()
        listbox.delete(0, tk.END)
        if not installers:
            listbox.insert(tk.END, "未找到安装包，请检查 PyIn.wzt 文件")
            listbox.config(state=tk.DISABLED)
            return
        for inst in installers:
            listbox.insert(tk.END, get_version_display(inst))
        listbox.installers = installers
        listbox.config(state=tk.NORMAL)

    refresh_list()

    def on_download():
        if not listbox.curselection():
            messagebox.showwarning("提示", "请先选择一个版本")
            return
        idx = listbox.curselection()[0]
        installers = getattr(listbox, 'installers', [])
        if 0 <= idx < len(installers):
            launch_installer_and_exit(installers[idx])

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="下载所选版本", command=on_download).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="刷新列表", command=refresh_list).pack(side="left", padx=5)

    ttk.Button(frame, text="上一步",
               command=lambda: show_page("AskWinget")).pack(pady=10)

# ====================== 等待进程模式 ======================

def wait_mode(pid, temp_dir):
    wait_for_pid(pid)
    show_thanks_and_cleanup(temp_dir)

# ====================== 主入口 ======================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Python Installer")
    parser.add_argument('--gui', action='store_true', help="启动图形界面")
    parser.add_argument('--wait-pid', type=int, help="内部使用：等待指定 PID 的进程结束")
    parser.add_argument('--temp-dir', type=str, help="内部使用：临时目录路径")
    args = parser.parse_args()

    if args.wait_pid:
        wait_mode(args.wait_pid, args.temp_dir)
        sys.exit(0)

    if args.gui:
        gui_main()
    else:
        cli_main()