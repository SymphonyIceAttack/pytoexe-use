#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import re
import os
import argparse
import tkinter as tk
from tkinter import filedialog

# ---------- 配置 ----------
# 默认网段选项（可以任意增加或修改）
SEGMENT_OPTIONS = {
    "0": "10.81.0",
    "1": "10.81.1",
    "2": "10.81.2",
    "3": "10.81.3",
    "4": "10.81.4",
    "5": "10.81.5",
    "6": "10.81.6",
    "7": "10.81.7",
    "8": "10.81.8",
    # 添加更多： "4": "10.81.7", ...
}

# DNS 服务器（主/备）
PRIMARY_DNS = "10.101.21.31"
SECONDARY_DNS = "10.101.21.32"

# 子网掩码
SUBNET_MASK = "255.255.255.0"

# 默认网卡名称（如果无法自动获取则使用此名称）
DEFAULT_NIC_NAME = "本地连接"


def is_admin() -> bool:
    """检查是否以管理员权限运行"""
    try:
        return subprocess.run(
            ["net", "session"],
            capture_output=True,
            text=True,
            check=False
        ).returncode == 0
    except:
        return False

def get_mac_address() -> str:
    """通过 ipconfig /all 获取本机 MAC 地址（小写连字符格式）"""
    try:
        output = subprocess.run(
            ["ipconfig", "/all"],
            capture_output=True,
            text=True,
            encoding="gbk",
            check=True
        ).stdout

        # 匹配物理地址行（支持中英文）
        pattern = re.compile(r"Physical Address[.\s]*:[\s]*([0-9A-F-]+)", re.IGNORECASE)
        match = pattern.search(output)
        if not match:
            pattern = re.compile(r"物理地址[.\s]*:[\s]*([0-9A-F-]+)", re.IGNORECASE)
            match = pattern.search(output)

        if match:
            mac = match.group(1).strip().lower()
            return mac
        else:
            raise ValueError("未找到 MAC 地址")
    except Exception as e:
        print(f"获取 MAC 地址失败: {e}")
        sys.exit(1)


def choose_mapping_file_gui() -> str:
    """
    弹出文件选择窗口，让用户选择映射表文件。
    返回选择的文件路径，如果用户取消则返回 None。
    """
    # 创建一个临时的 tkinter 根窗口，并隐藏
    root = tk.Tk()
    root.withdraw()
    # 确保窗口在最前
    root.lift()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="选择映射表文件",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
    )
    root.destroy()
    return file_path if file_path else None


def load_mapping_from_file(file_path: str) -> dict:
    """
    从文件读取 MAC->IP 映射表。
    文件格式：每行 "MAC地址 IP地址"，空格或制表符分隔。
    例如：
        2c-f0-5d-c1-de-ab 10.81.4.38
        2c-f0-5d-c1-df-e0 10.81.4.39
    """
    if not os.path.exists(file_path):
        print(f"错误：映射表文件不存在: {file_path}")
        sys.exit(1)

    mapping = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                print(f"警告：第 {line_num} 行格式错误，已跳过: {line}")
                continue
            mac = parts[0].strip().lower()
            ip = parts[1].strip()
            if mac in mapping:
                print(f"警告：MAC {mac} 重复出现，使用最后一条")
            mapping[mac] = ip
    if not mapping:
        print("错误：映射表文件未读取到任何有效条目")
        sys.exit(1)
    return mapping


def get_active_nic_name() -> str:
    """获取当前活动网卡的名称（第一个已连接的以太网卡）"""
    try:
        output = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True,
            text=True,
            encoding="gbk",
            check=True
        ).stdout

        for line in output.splitlines():
            if "已连接" in line or "Connected" in line:
                if "以太网" in line or "Ethernet" in line:
                    parts = line.split()
                    if parts:
                        nic_name = parts[-1]
                        if nic_name and not nic_name.isdigit():
                            return nic_name
        return DEFAULT_NIC_NAME
    except:
        return DEFAULT_NIC_NAME


def set_static_ip(nic_name: str, ip: str, gateway: str) -> bool:
    """使用 netsh 设置静态 IP"""
    cmd = f'netsh interface ip set address name="{nic_name}" static {ip} {SUBNET_MASK} {gateway}'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0


def set_dns(nic_name: str, primary: str, secondary: str) -> bool:
    """设置主 DNS 和备用 DNS"""
    cmd_primary = f'netsh interface ip set dns name="{nic_name}" static {primary}'
    ret1 = subprocess.run(cmd_primary, shell=True, capture_output=True)
    # 删除可能已存在的备用 DNS，然后添加
    cmd_del = f'netsh interface ip delete dns name="{nic_name}" {secondary}'
    subprocess.run(cmd_del, shell=True, capture_output=True)
    cmd_secondary = f'netsh interface ip add dns name="{nic_name}" {secondary} index=2'
    ret2 = subprocess.run(cmd_secondary, shell=True, capture_output=True)
    return ret1.returncode == 0 and ret2.returncode == 0


def replace_ip_segment(ip: str, new_segment: str) -> str:
    """将 IP 地址的前三段替换为新网段"""
    parts = ip.split('.')
    if len(parts) != 4:
        return ip
    new_parts = new_segment.split('.')
    if len(new_parts) != 3:
        return ip
    return f"{new_parts[0]}.{new_parts[1]}.{new_parts[2]}.{parts[3]}"


def generate_bat_file(mapping: dict, segment: str, output_path: str = "auto_ip.bat"):
    """生成批处理文件，使用新网段"""
    gateway = f"{segment}.254"
    lines = []
    lines.append("@echo off")
    lines.append("")
    lines.append("echo 正在注册开机任务...")
    lines.append("")
    lines.append('set "self=%~f0"')
    lines.append("")
    lines.append('schtasks /create /tn "AutoIP" /tr "\\"%self%\\"" /sc onstart /ru SYSTEM /f')
    lines.append("")
    lines.append("echo 完成！")
    lines.append("")
    lines.append("setlocal enabledelayedexpansion")
    lines.append("")
    lines.append(":: 获取本机 MAC")
    lines.append('for /f "tokens=2 delims=:" %%i in (\'ipconfig /all ^| findstr /i "Physical Address 物理地址"\') do (')
    lines.append('    set "raw=%%i"')
    lines.append('    set "mac=!raw: =!"')
    lines.append('    goto :got_mac')
    lines.append(")")
    lines.append(":got_mac")
    lines.append('echo 本机 MAC: %mac%')
    lines.append("")
    lines.append(":: 映射表（MAC → IP）")
    for mac, original_ip in mapping.items():
        new_ip = replace_ip_segment(original_ip, segment)
        lines.append(f'if /i "%mac%"=="{mac}" set ip={new_ip}')
    lines.append("")
    lines.append('if "%ip%"=="" (')
    lines.append('    echo 未匹配到 IP，请检查 MAC 是否正确')
    lines.append('    pause')
    lines.append('    exit /b')
    lines.append(")")
    lines.append("")
    lines.append(f'echo 匹配到 IP: %ip%')
    lines.append(f':: 设置静态 IP（网关固定为 {gateway}）')
    lines.append(f'netsh interface ip set address name="本地连接" static %ip% {SUBNET_MASK} {gateway}')
    lines.append("")
    lines.append(f':: 设置 DNS（{PRIMARY_DNS} 和 {SECONDARY_DNS}）')
    lines.append(f'netsh interface ip set dns name="本地连接" static {PRIMARY_DNS}')
    lines.append(f'netsh interface ip add dns name="本地连接" {SECONDARY_DNS} index=2')
    lines.append("")
    lines.append("echo IP 和 DNS 设置完成")
    lines.append("ipconfig /all | findstr /i \"IPv4 DNS\"")
    lines.append("pause")

    with open(output_path, 'w', encoding='gbk') as f:
        f.write('\n'.join(lines))

    print(f"批处理文件已生成: {os.path.abspath(output_path)}")


def main():
    parser = argparse.ArgumentParser(description="根据 MAC 地址自动配置静态 IP 和 DNS（支持外部映射表和数字选网段）")
    parser.add_argument("--segment", type=str, help="直接指定网段（如 10.81.5），跳过数字菜单")
    parser.add_argument("--generate-bat", action="store_true", help="仅生成批处理文件，不执行本机设置")
    parser.add_argument("--bat-output", type=str, default="auto_ip.bat", help="生成的批处理文件名")
    parser.add_argument("--mapping-file", type=str, help="映射表文件路径，如果不指定则弹出 GUI 选择")
    args = parser.parse_args()

    # 检查管理员权限（如果执行本机设置）
    if not args.generate_bat and not is_admin():
        print("错误：修改 IP 需要管理员权限。请以管理员身份运行此脚本。")
        print("可以右键点击脚本 -> 以管理员身份运行")
        sys.exit(1)

    # 获取映射表文件路径
    mapping_file = args.mapping_file
    if not mapping_file:
        # 没有通过命令行指定，则弹出 GUI 选择
        mapping_file = choose_mapping_file_gui()
        if not mapping_file:
            print("未选择映射表文件，程序退出。")
            sys.exit(0)
        print(f"已选择映射表文件: {mapping_file}")
    else:
        print(f"使用命令行指定的映射表文件: {mapping_file}")

    # 1. 加载映射表
    mapping = load_mapping_from_file(mapping_file)
    print(f"已加载 {len(mapping)} 条 MAC-IP 映射")

    # 2. 获取本机 MAC
    mac = get_mac_address()
    print(f"本机 MAC: {mac}")

    # 3. 查找原始 IP
    original_ip = mapping.get(mac)
    if not original_ip:
        print(f"错误：未找到 MAC {mac} 对应的 IP，请检查映射表文件")
        sys.exit(1)
    print(f"原始匹配 IP: {original_ip}")

    # 4. 确定目标网段
    if args.segment:
        new_segment = args.segment
    else:
        # 显示数字菜单
        print("\n请选择目标网段：")
        for key, seg in SEGMENT_OPTIONS.items():
            print(f"  {key}. {seg}.x")
        print("  q. 退出")
        choice = input("请输入数字: ").strip()
        if choice.lower() == 'q':
            sys.exit(0)
        if choice not in SEGMENT_OPTIONS:
            print("无效选择，退出")
            sys.exit(1)
        new_segment = SEGMENT_OPTIONS[choice]

    # 验证网段格式
    if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$", new_segment):
        print(f"错误：网段格式不正确 -> {new_segment}")
        sys.exit(1)

    # 5. 计算新 IP 和网关
    new_ip = replace_ip_segment(original_ip, new_segment)
    gateway = f"{new_segment}.254"
    print(f"目标网段: {new_segment}")
    print(f"目标 IP: {new_ip}")
    print(f"网关: {gateway}")
    print(f"DNS 主: {PRIMARY_DNS}, 备: {SECONDARY_DNS}")

    # 6. 生成批处理文件（始终生成）
    generate_bat_file(mapping, new_segment, args.bat_output)

    # 7. 执行本机设置（除非 --generate-bat）
    if not args.generate_bat:
        nic = get_active_nic_name()
        print(f"使用的网卡: {nic}")

        print("正在设置静态 IP...")
        if not set_static_ip(nic, new_ip, gateway):
            print("设置 IP 失败，请检查网卡名称或权限。")
            sys.exit(1)

        print("正在设置 DNS...")
        if not set_dns(nic, PRIMARY_DNS, SECONDARY_DNS):
            print("设置 DNS 失败。")
            sys.exit(1)

        print("✅ 设置完成！当前网络配置：")
        subprocess.run("ipconfig | findstr \"IPv4\"", shell=True, check=False)
    else:
        print("已根据要求生成批处理文件，未对本机进行任何修改。")


if __name__ == "__main__":
    main()