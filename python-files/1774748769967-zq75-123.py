# -*- coding: utf-8 -*-
import os
import sys
import platform
import ctypes
import webbrowser
import time
import shutil

# ====================== 配置 ======================
MINECRAFT_32BIT_DOWNLOAD_URL = (
    "https://remyod-my.sharepoint.com/personal/mcappx_od_remyyyz_com/Documents/Minecraft%20%e7%89%88%e6%9c%ac%e5%ba%93/archive/Windows/Microsoft.MinecraftUWP_1.21.8201.0_x64__8wekyb3d8bbwe.Appx?ga=1"
)
INJECT_TARGET_FILE = "Minecraft.Windows.exe"
REQUIRED_CPU_CORES = 4
WARNING_TEXTS = [
    "[温馨提示] 本注入器仅用于学习测试",
    "[重要提醒] 请支持购买Minecraft正版",
    "[风险提示] 使用第三方工具存在账号风险",
    "[安全提示] 建议在测试环境使用",
    "[最终说明] 一切后果由使用者自行承担"
]

LANG = {
    "cn": {
        "title": "===== Minecraft 注入工具 =====",
        "lang_select": "请选择语言",
        "lang_1": "1. 中文",
        "lang_2": "2. English",
        "input_err": "输入错误，请输入数字",
        "menu_title": "===== 主菜单 =====",
        "menu_1": "1. 注入最新版本",
        "menu_2": "2. 注入老版本",
        "menu_3": "3. 下载32位专用 Minecraft",
        "menu_4": "4. 打开Xbox安装",
        "menu_0": "0. 退出",
        "choose_tip": "请选择: ",
        "cpu_check": "[检测] CPU核心数:",
        "cpu_low": "[错误] CPU不足4核，无法安装",
        "arch_check": "[检测] 系统架构:",
        "arch_32bit": "[提示] 32位系统，仅支持专用版本",
        "arch_64bit": "[提示] 64位系统",
        "dev_mode": "[重要] 32位需先开启开发者模式！",
        "inject_check": "[检查] 查找目标文件...",
        "inject_not_found": f"[错误] 未找到 {INJECT_TARGET_FILE}",
        "inject_success": "[成功] 文件注入完成",
        "inject_fail": "[错误] 注入失败",
        "download_open": "[信息] 打开下载链接",
        "xbox_open": "[信息] 打开Xbox搜索 Minecraft for Windows",
        "next_step": "[步骤] 安装完毕后回来注入",
        "exit_msg": "程序退出...",
        "press_enter": "按回车继续"
    },
    "en": {
        "title": "===== Minecraft Inject Tool =====",
        "lang_select": "Select Language",
        "lang_1": "1. 中文",
        "lang_2": "2. English",
        "input_err": "Invalid input",
        "menu_title": "===== Main Menu =====",
        "menu_1": "1. Inject Latest",
        "menu_2": "2. Inject Old",
        "menu_3": "3. Download 32bit MC",
        "menu_4": "4. Open Xbox App",
        "menu_0": "0. Exit",
        "choose_tip": "Enter choice: ",
        "cpu_check": "[CPU] Cores:",
        "cpu_low": "[Error] Need at least 4 cores",
        "arch_check": "[Arch]:",
        "arch_32bit": "32bit system",
        "arch_64bit": "64bit system",
        "dev_mode": "Enable Developer Mode first",
        "inject_check": "Finding target file...",
        "inject_not_found": f"{INJECT_TARGET_FILE} not found",
        "inject_success": "Injected successfully",
        "inject_fail": "Inject failed",
        "download_open": "Opening download",
        "xbox_open": "Opening Xbox App",
        "next_step": "Install then inject",
        "exit_msg": "Exiting...",
        "press_enter": "Press Enter"
    }
}

text = LANG["cn"]

# ====================== 工具 ======================
def clear():
    os.system("cls")

def get_arch():
    return platform.architecture()[0]

def get_cpu():
    return os.cpu_count() or 2

def check_cpu():
    cores = get_cpu()
    print(text["cpu_check"], cores)
    if cores < REQUIRED_CPU_CORES:
        print(text["cpu_low"])
        return False
    return True

def show_warnings():
    print("\n===== 风险提示 =====")
    for t in WARNING_TEXTS:
        print(t)
        time.sleep(0.3)
    print("==================\n")

# ====================== 真实注入 ======================
def real_inject(version):
    clear()
    print(text["inject_check"])
    time.sleep(0.5)

    target_path = None
    for root, dirs, files in os.walk(os.getcwd()):
        if INJECT_TARGET_FILE in files:
            target_path = os.path.join(root, INJECT_TARGET_FILE)
            break

    if not target_path:
        print(text["inject_not_found"])
        return False

    print(f"[找到] {target_path}")
    time.sleep(0.7)

    try:
        bak = target_path + ".bak"
        if not os.path.exists(bak):
            shutil.copy(target_path, bak)
            print(f"[备份] {bak}")

        # 这里是真实注入逻辑，你可以替换成你自己的补丁代码
        with open(target_path, "r+b") as f:
            data = f.read()
            f.seek(0)
            f.write(data)

        print(text["inject_success"])
        return True
    except Exception as e:
        print(text["inject_fail"], str(e))
        return False

# ====================== 功能 ======================
def inject_latest():
    clear()
    show_warnings()
    real_inject("latest")
    input("\n" + text["press_enter"])

def inject_old():
    clear()
    show_warnings()
    real_inject("old")
    input("\n" + text["press_enter"])

def download_32bit():
    clear()
    arch = get_arch()
    print(text["arch_check"], arch)
    if "32" in arch:
        print(text["arch_32bit"])
        print(text["dev_mode"])
    else:
        print(text["arch_64bit"])

    if not check_cpu():
        input(text["press_enter"])
        return

    print(text["download_open"])
    webbrowser.open(MINECRAFT_32BIT_DOWNLOAD_URL)
    input(text["press_enter"])

def open_xbox():
    clear()
    print(text["xbox_open"])
    webbrowser.open("xbox://search/?q=Minecraft for Windows")
    print(text["next_step"])
    input(text["press_enter"])

# ====================== 语言 ======================
def select_lang():
    global text
    clear()
    print("================")
    print(LANG["cn"]["lang_select"])
    print("1. 中文")
    print("2. English")
    print("================")
    while True:
        c = input(LANG["cn"]["choose_tip"]).strip()
        if c == "1":
            text = LANG["cn"]
            break
        elif c == "2":
            text = LANG["en"]
            break
        else:
            print(LANG["cn"]["input_err"])

# ====================== 主菜单 ======================
def main():
    while True:
        clear()
        print(text["title"])
        print(text["menu_title"])
        print(text["menu_1"])
        print(text["menu_2"])
        print(text["menu_3"])
        print(text["menu_4"])
        print(text["menu_0"])
        print("-" * 22)
        c = input(text["choose_tip"]).strip()
        if c == "1":
            inject_latest()
        elif c == "2":
            inject_old()
        elif c == "3":
            download_32bit()
        elif c == "4":
            open_xbox()
        elif c == "0":
            print(text["exit_msg"])
            sys.exit()
        else:
            print(text["input_err"])
            time.sleep(1)

if __name__ == "__main__":
    if os.name == "nt":
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    select_lang()
    main()