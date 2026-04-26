#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import ipaddress
import threading
import queue
import re
import sys
import socket

# ========== 配置 ==========
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
}

THREADS = 64
TIMEOUT_MS = 200

# ========== 函数定义 ==========

def ping_ip(ip_str: str, q: queue.Queue):
    cmd = ["ping", "-n", "1", "-w", str(TIMEOUT_MS), ip_str]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        q.put(ip_str)
    except:
        pass

def get_mac_from_arp(ip_str: str) -> str or None:
    try:
        output = subprocess.run(["arp", "-a", ip_str], capture_output=True, text=True, encoding="gbk").stdout
        pattern = re.compile(rf"{re.escape(ip_str)}\s+([0-9a-fA-F\-]+)", re.IGNORECASE)
        m = pattern.search(output)
        if m:
            mac = m.group(1).strip().lower()
            if len(mac) == 17 and mac.count('-') == 5:
                return mac
    except:
        pass
    return None

def get_self_mac() -> str or None:
    """获取本机主网卡的 MAC 地址（小写连字符）"""
    try:
        output = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding="gbk").stdout
        # 匹配物理地址
        pattern = re.compile(r"Physical Address[.\s]*:[\s]*([0-9A-F-]+)", re.IGNORECASE)
        match = pattern.search(output)
        if not match:
            pattern = re.compile(r"物理地址[.\s]*:[\s]*([0-9A-F-]+)", re.IGNORECASE)
            match = pattern.search(output)
        if match:
            return match.group(1).strip().lower()
    except:
        pass
    return None

def get_ip_from_mac(target_mac: str) -> str or None:
    """根据 MAC 地址从 ipconfig 中查找对应的 IPv4 地址"""
    try:
        output = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding="gbk").stdout
        # 按网卡段落分割
        sections = re.split(r"\n\s*\n", output)
        for sec in sections:
            if target_mac.lower() in sec.lower():
                # 查找 IPv4 地址
                ip_pattern = re.compile(r"IPv4 地址[.\s]*:[\s]*(\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
                ip_match = ip_pattern.search(sec)
                if ip_match:
                    return ip_match.group(1).strip()
                # 备用英文
                ip_pattern2 = re.compile(r"IPv4 Address[.\s]*:[\s]*(\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
                ip_match2 = ip_pattern2.search(sec)
                if ip_match2:
                    return ip_match2.group(1).strip()
    except:
        pass
    return None

def scan_network(network_cidr: str):
    net = ipaddress.ip_network(network_cidr, strict=False)
    ips = [str(ip) for ip in net.hosts()]
    print(f"正在扫描 {network_cidr}，共 {len(ips)} 个地址...")

    q = queue.Queue()
    threads = []
    for ip in ips:
        t = threading.Thread(target=ping_ip, args=(ip, q))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    alive_ips = []
    while not q.empty():
        alive_ips.append(q.get())

    print(f"发现 {len(alive_ips)} 个活跃主机，正在获取 MAC...")

    mapping = {}
    for ip in alive_ips:
        mac = get_mac_from_arp(ip)
        if mac:
            mapping[ip] = mac
            print(f"  {ip} -> {mac}")
        else:
            print(f"  {ip} -> 未获取到 MAC")
    return mapping

def add_self_to_mapping(mapping: dict):
    """获取本机信息，加入映射表（如果本机 IP 属于扫描的子网则添加，否则也添加但提示）"""
    self_mac = get_self_mac()
    if not self_mac:
        print("警告：无法获取本机 MAC，跳过添加本机")
        return
    self_ip = get_ip_from_mac(self_mac)
    if not self_ip:
        print("警告：无法获取本机 IP，跳过添加本机")
        return

    # 检查 IP 是否已在 mapping 中（可能扫描时已经包含？通常本机不会出现在扫描结果中）
    if self_ip in mapping:
        # 如果已有但 MAC 不同，更新为本机的 MAC（信任本机）
        if mapping[self_ip] != self_mac:
            print(f"更新本机条目: {self_ip} 原MAC {mapping[self_ip]} -> {self_mac}")
            mapping[self_ip] = self_mac
    else:
        mapping[self_ip] = self_mac
        print(f"添加本机: {self_ip} -> {self_mac}")

def save_mapping(mapping: dict, filename: str):
    with open(filename, "w", encoding="gbk") as f:  # ANSI 编码（简体中文 GBK）
        for ip, mac in mapping.items():
            mac = mac.replace(':', '-').lower()
            f.write(f"{mac} {ip}\n")
    print(f"✅ 映射表已保存到 {filename}")

def main():
    print("===== 局域网 IP-MAC 扫描工具 =====")
    print("请选择要扫描的网段：")
    for key, seg in SEGMENT_OPTIONS.items():
        print(f"  {key}. {seg}.0/24")
    print("  q. 退出")

    choice = input("请输入数字: ").strip()
    if choice.lower() == 'q':
        sys.exit(0)
    if choice not in SEGMENT_OPTIONS:
        print("无效选择")
        sys.exit(1)

    segment_prefix = SEGMENT_OPTIONS[choice]
    network_cidr = f"{segment_prefix}.0/24"
    mapping = scan_network(network_cidr)

    # 添加本机信息到映射表
    add_self_to_mapping(mapping)

    if mapping:
        filename = f"{choice}.txt"
        save_mapping(mapping, filename)
        print(f"映射表共 {len(mapping)} 条记录（包含本机）")
    else:
        print("未发现任何主机，请检查网络或防火墙设置。")

if __name__ == "__main__":
    main()