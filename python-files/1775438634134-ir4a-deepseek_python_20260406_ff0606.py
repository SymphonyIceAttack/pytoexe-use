#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNS Benchmark Plus – 最终稳定版（彻底解决打包闪退）
"""

import subprocess
import sys
import os
import importlib
import logging
import argparse
import json
import platform
import re
import shutil
import time
import threading
import traceback
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress

# ---------------------------- 异常日志记录 ---------------------------------
def setup_exception_logging():
    log_path = os.path.join(os.path.expanduser("~"), ".dns_bench_plus_error.log")
    def excepthook(typ, val, tb):
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{time.ctime()}\n{typ.__name__}: {val}\n{''.join(traceback.format_tb(tb))}\n")
        # 也输出到 stderr，如果控制台存在的话
        sys.__excepthook__(typ, val, tb)
    sys.excepthook = excepthook

setup_exception_logging()

# ---------------------------- 环境自检与自动安装（打包环境自动跳过）--------------------------------
REQUIRED_PACKAGES = {
    "dnspython": "dns",
    "tabulate": "tabulate"
}

def is_packaged_mode():
    """判断是否运行在打包后的环境中（PyInstaller/Nuitka）"""
    if getattr(sys, 'frozen', False):
        return True
    if hasattr(sys, '_MEIPASS'):
        return True
    if hasattr(sys, '__compiled__'):      # Nuitka 特有
        return True
    if getattr(sys, '_PACKAGED_MODE', False):
        return True
    if os.environ.get('DNS_BENCH_PACKAGED') == '1':
        return True
    # 检测可执行文件名
    exe_name = os.path.basename(sys.executable).lower()
    if exe_name in ('dnsbenchplus.exe', 'dns_bench_plus.exe', 'dnsbenchplus', 'dns_bench_plus'):
        return True
    return False

def install_package(package_name: str) -> bool:
    try:
        print(f"正在安装缺失的依赖: {package_name} ...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", package_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package_name} 安装失败: {e}")
        return False

def check_and_install_dependencies():
    if is_packaged_mode():
        # 打包环境：确保关键模块可用，若不可用则写入日志但不退出（因为理论上应该已包含）
        try:
            import dns.resolver
        except ImportError as e:
            log_path = os.path.join(os.path.expanduser("~"), ".dns_bench_plus_import_error.log")
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"Packaged mode: failed to import dns.resolver: {e}\n")
        return
    missing = []
    for pkg, import_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("检测到缺失依赖，正在尝试自动安装...")
        for pkg in missing:
            if not install_package(pkg):
                print(f"请手动安装: pip install {pkg}")
                sys.exit(1)
        print("所有依赖已就绪，重新启动脚本...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

check_and_install_dependencies()

# 继续正常导入
import dns.resolver
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    tabulate = None

# ---------------------------- 自动请求管理员权限 ---------------------------------
def is_admin() -> bool:
    if platform.system().lower() == "windows":
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        return os.geteuid() == 0

def request_admin_restart():
    if is_admin():
        return True
    system = platform.system().lower()
    if system == "windows":
        import ctypes
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    else:
        print("需要管理员权限，请使用 sudo 重新运行命令:")
        print(f"sudo {sys.executable} {' '.join(sys.argv)}")
        sys.exit(1)

# ---------------------------- 配置 ---------------------------------
DEFAULT_DOMAINS = ["www.google.com", "www.youtube.com", "www.github.com", "www.cloudflare.com"]
DEFAULT_QUERY_COUNT = 10
DEFAULT_TIMEOUT = 3
DEFAULT_THREADS = 20
DEFAULT_CACHE_TTL = 3600
DEFAULT_SWITCH_THRESHOLD = 0.2
DEFAULT_THEME_COLOR = "#39C5BB"
DEFAULT_WINDOW_GEOMETRY = "1100x750"

DEFAULT_DNS_LIST = [
    "1.1.1.1", "1.0.0.1",
    "8.8.8.8", "8.8.4.4",
    "9.9.9.9", "149.112.112.112",
    "208.67.222.222", "208.67.220.220",
    "114.114.114.114", "114.114.115.115",
    "223.5.5.5", "223.6.6.6",
    "180.76.76.76",
    "119.29.29.29",
]

BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".dns_bench_plus_backup")
BACKUP_FILE = os.path.join(BACKUP_DIR, "dns_backup.json")
os.makedirs(BACKUP_DIR, mode=0o700, exist_ok=True)

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".dns_bench_plus_config.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dns_bench_plus")

# ---------------------------- 数据结构 ---------------------------------
@dataclass
class DNSProbeResult:
    dns_server: str
    domain: str
    latency_ms: float
    success: bool

@dataclass
class DNSSummary:
    dns_server: str
    success_rate: float
    avg_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    stddev_ms: float
    samples: int
    ewma_latency: float = 0.0

@dataclass
class BenchmarkResult:
    timestamp: float
    summaries: List[DNSSummary]

# ---------------------------- 工具函数 ---------------------------------
def is_valid_public_ip(ip: str, allow_private: bool = False) -> bool:
    try:
        addr = ipaddress.IPv4Address(ip)
        if allow_private:
            return True
        return not (addr.is_private or addr.is_loopback or addr.is_multicast or addr.is_link_local)
    except:
        return False

def format_table(headers: List[str], rows: List[List[str]]) -> str:
    if not rows:
        return "No data to display."
    if HAS_TABULATE:
        return tabulate(rows, headers=headers, tablefmt="grid")
    col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    fmt = " | ".join(f"{{:<{w}}}" for w in col_widths)
    sep = "-+-".join("-" * w for w in col_widths)
    lines = [fmt.format(*headers), sep]
    for row in rows:
        lines.append(fmt.format(*[str(cell) for cell in row]))
    return "\n".join(lines)

# ---------------------------- 系统 DNS 操作 ---------------------------------
def get_current_system_dns() -> List[str]:
    system = platform.system().lower()
    dns_list = []
    try:
        if system == "windows":
            cmd = ["powershell", "-Command",
                   "Get-DnsClientServerAddress -AddressFamily IPv4 | Where-Object {$_.ServerAddresses} | Select-Object -ExpandProperty ServerAddresses"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            for line in result.stdout.strip().splitlines():
                ip = line.strip()
                if is_valid_public_ip(ip, allow_private=True):
                    dns_list.append(ip)
        elif system == "linux":
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    if line.startswith("nameserver"):
                        ip = line.split()[1]
                        if is_valid_public_ip(ip, allow_private=True):
                            dns_list.append(ip)
        elif system == "darwin":
            services = subprocess.run(["networksetup", "-listallnetworkservices"], capture_output=True, text=True)
            for service in services.stdout.strip().splitlines():
                if service and not service.startswith("*"):
                    out = subprocess.run(["networksetup", "-getdnsservers", service], capture_output=True, text=True)
                    if "There aren't any DNS Servers" not in out.stdout:
                        for line in out.stdout.strip().splitlines():
                            if is_valid_public_ip(line, allow_private=True):
                                dns_list.append(line)
        return list(OrderedDict.fromkeys(dns_list))
    except Exception as e:
        logger.warning(f"获取系统 DNS 失败: {e}")
        return []

def backup_system_dns() -> bool:
    if os.path.exists(BACKUP_FILE):
        logger.debug("备份文件已存在，跳过重复备份")
        return True
    config = {"type": platform.system().lower(), "data": {}}
    system = config["type"]
    try:
        if system == "windows":
            ps_cmd = "Get-DnsClientServerAddress -AddressFamily IPv4 | ConvertTo-Json"
            result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            config["data"] = data
        elif system == "linux":
            with open("/etc/resolv.conf", "r") as f:
                config["data"]["resolv.conf"] = f.read()
            manager = None
            if os.path.islink("/etc/resolv.conf"):
                target = os.readlink("/etc/resolv.conf")
                if "systemd" in target:
                    manager = "systemd-resolved"
                elif "resolvconf" in target:
                    manager = "resolvconf"
            if manager is None and shutil.which("nmcli"):
                try:
                    status = subprocess.run(["nmcli", "-t", "-f", "RUNNING", "general", "status"],
                                            capture_output=True, text=True)
                    if status.stdout.strip() == "running":
                        manager = "nmcli"
                except:
                    pass
            if manager:
                config["data"]["manager"] = manager
        elif system == "darwin":
            services = subprocess.run(["networksetup", "-listallnetworkservices"], capture_output=True, text=True)
            for service in services.stdout.strip().splitlines():
                if service and not service.startswith("*"):
                    out = subprocess.run(["networksetup", "-getdnsservers", service], capture_output=True, text=True)
                    config["data"][service] = out.stdout.strip()
        with open(BACKUP_FILE, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"DNS 配置已备份到 {BACKUP_FILE}")
        return True
    except Exception as e:
        logger.error(f"备份失败: {e}")
        return False

def restore_system_dns() -> bool:
    if not os.path.exists(BACKUP_FILE):
        logger.error("备份文件不存在，无法恢复")
        return False
    try:
        with open(BACKUP_FILE, "r") as f:
            config = json.load(f)
        system = config["type"]
        if system == "windows":
            for adapter in config["data"]:
                alias = adapter.get("InterfaceAlias")
                servers = adapter.get("ServerAddresses", [])
                if not servers:
                    continue
                subprocess.run(["netsh", "interface", "ip", "set", "dns",
                                f'name="{alias}"', "source=static", f"addr={servers[0]}"], check=True)
                if len(servers) > 1:
                    subprocess.run(["netsh", "interface", "ip", "add", "dns",
                                    f'name="{alias}"', f"addr={servers[1]}", "index=2"], check=True)
            logger.info("Windows DNS 已恢复")
        elif system == "linux":
            manager = config["data"].get("manager", "file")
            if manager == "systemd-resolved":
                target = os.path.realpath("/etc/resolv.conf")
                with open(target, "w") as f:
                    f.write(config["data"]["resolv.conf"])
                logger.info("已恢复 systemd-resolved 管理的 resolv.conf")
            elif manager == "nmcli":
                logger.warning("NetworkManager 管理，自动恢复可能不完整，将覆盖 /etc/resolv.conf")
                with open("/etc/resolv.conf", "w") as f:
                    f.write(config["data"]["resolv.conf"])
            else:
                with open("/etc/resolv.conf", "w") as f:
                    f.write(config["data"]["resolv.conf"])
            logger.info("Linux DNS 已恢复")
        elif system == "darwin":
            for service, dns_str in config["data"].items():
                if not dns_str or "There aren't any DNS Servers" in dns_str:
                    subprocess.run(["networksetup", "-setdnsservers", service, "Empty"], check=True)
                else:
                    ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', dns_str)
                    if ips:
                        subprocess.run(["networksetup", "-setdnsservers", service] + ips, check=True)
            logger.info("macOS DNS 已恢复")
        return True
    except Exception as e:
        logger.error(f"恢复失败: {e}")
        return False

def set_system_dns(dns_server: str) -> bool:
    system = platform.system().lower()
    try:
        if system == "windows":
            ps_cmd = "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object -First 1 -ExpandProperty Name"
            adapter = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, check=True).stdout.strip()
            if not adapter:
                logger.error("未找到活动网络适配器")
                return False
            subprocess.run(["netsh", "interface", "ip", "set", "dns", f'name="{adapter}"', "source=static", f"addr={dns_server}"], check=True)
            subprocess.run(["netsh", "interface", "ip", "set", "dns", f'name="{adapter}"', "source=static", "addr=none", "index=2"], check=True)
        elif system == "linux":
            if shutil.which("resolvectl"):
                interfaces = subprocess.run(["resolvectl", "status", "--no-pager"], capture_output=True, text=True)
                iface_names = re.findall(r'Link \d+ \((.+?)\)', interfaces.stdout)
                for iface in iface_names:
                    subprocess.run(["resolvectl", "dns", iface, dns_server], check=True)
            elif shutil.which("nmcli"):
                conns = subprocess.run(["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"], capture_output=True, text=True)
                for conn in conns.stdout.strip().splitlines():
                    if conn:
                        subprocess.run(["nmcli", "connection", "modify", conn, "ipv4.dns", dns_server], check=True)
                        subprocess.run(["nmcli", "connection", "up", conn], check=True)
            else:
                with open("/etc/resolv.conf", "w") as f:
                    f.write(f"nameserver {dns_server}\n")
        elif system == "darwin":
            services = subprocess.run(["networksetup", "-listallnetworkservices"], capture_output=True, text=True)
            active = None
            for line in services.stdout.strip().splitlines():
                if line and not line.startswith("*"):
                    info = subprocess.run(["networksetup", "-getinfo", line], capture_output=True, text=True)
                    if "IP address: " in info.stdout and "no" not in info.stdout.lower():
                        active = line
                        break
            if not active:
                logger.error("未找到活动网络服务")
                return False
            subprocess.run(["networksetup", "-setdnsservers", active, dns_server], check=True)
        logger.info(f"系统 DNS 已设置为 {dns_server}")
        return True
    except Exception as e:
        logger.error(f"设置 DNS 失败: {e}")
        return False

# ---------------------------- DNS 测试核心 ---------------------------------
def dns_query_worker(dns_server: str, domain: str, timeout: float) -> DNSProbeResult:
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.timeout = timeout
    resolver.lifetime = timeout
    start = time.perf_counter()
    try:
        resolver.resolve(domain, 'A')
        elapsed_ms = (time.perf_counter() - start) * 1000
        return DNSProbeResult(dns_server, domain, elapsed_ms, True)
    except Exception:
        return DNSProbeResult(dns_server, domain, -1.0, False)

def benchmark(dns_servers: List[str], domains: List[str], query_count: int, timeout: float,
              threads: int, cache_ttl: int, use_cache: bool = True, progress_callback=None) -> BenchmarkResult:
    cache_file = os.path.join(BACKUP_DIR, "benchmark_cache.json")
    if use_cache and os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if time.time() - mtime < cache_ttl:
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                summaries = [DNSSummary(**s) for s in data["summaries"]]
                logger.info("使用缓存的测试结果")
                return BenchmarkResult(data["timestamp"], summaries)
            except:
                pass

    logger.info(f"开始测试 {len(dns_servers)} 个 DNS 服务器，每个查询 {query_count} 轮，域名 {domains}")
    tasks = []
    for dns in dns_servers:
        for _ in range(query_count):
            for domain in domains:
                tasks.append((dns, domain, timeout))

    total_tasks = len(tasks)
    completed = 0
    results_per_dns: Dict[str, List[float]] = {dns: [] for dns in dns_servers}
    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_task = {executor.submit(dns_query_worker, dns, dom, to): (dns, dom) for (dns, dom, to) in tasks}
        for future in as_completed(future_to_task):
            dns, _ = future_to_task[future]
            try:
                res = future.result()
                if res.success:
                    results_per_dns[dns].append(res.latency_ms)
            except Exception as e:
                logger.debug(f"任务异常 {dns}: {e}")
            completed += 1
            if progress_callback:
                progress_callback(completed, total_tasks)

    summaries = []
    for dns in dns_servers:
        latencies = results_per_dns[dns]
        total_tasks_for_dns = len([t for t in tasks if t[0] == dns])
        success_count = len(latencies)
        success_rate = success_count / total_tasks_for_dns if total_tasks_for_dns > 0 else 0.0
        if latencies:
            latencies.sort()
            avg = sum(latencies) / len(latencies)
            median = latencies[len(latencies)//2]
            p95 = latencies[int(len(latencies)*0.95)] if len(latencies) > 0 else latencies[-1]
            variance = sum((x-avg)**2 for x in latencies) / len(latencies)
            stddev = variance**0.5
        else:
            avg = median = p95 = stddev = 0.0
        summaries.append(DNSSummary(
            dns_server=dns,
            success_rate=success_rate,
            avg_latency_ms=avg,
            median_latency_ms=median,
            p95_latency_ms=p95,
            stddev_ms=stddev,
            samples=len(latencies),
            ewma_latency=avg
        ))

    try:
        with open(cache_file, "w") as f:
            json.dump({"timestamp": time.time(), "summaries": [asdict(s) for s in summaries]}, f)
    except:
        pass
    return BenchmarkResult(time.time(), summaries)

def rank_servers(summaries: List[DNSSummary], weight_latency: float = 0.5, weight_reliability: float = 0.5) -> List[DNSSummary]:
    if not summaries:
        return []
    latencies = [s.median_latency_ms for s in summaries if s.median_latency_ms > 0]
    if not latencies:
        return summaries
    min_lat = min(latencies)
    max_lat = max(latencies)
    def norm_lat(lat):
        if max_lat == min_lat:
            return 1.0
        return 1 - (lat - min_lat) / (max_lat - min_lat)
    for s in summaries:
        latency_score = norm_lat(s.median_latency_ms) if s.median_latency_ms > 0 else 0
        reliability = s.success_rate
        s.ewma_latency = latency_score * weight_latency + reliability * weight_reliability
    return sorted(summaries, key=lambda x: x.ewma_latency, reverse=True)

def select_best_server(summaries: List[DNSSummary], current_best: Optional[str] = None,
                       switch_threshold: float = DEFAULT_SWITCH_THRESHOLD) -> Tuple[Optional[DNSSummary], bool]:
    ranked = rank_servers(summaries)
    if not ranked:
        return None, False
    best = ranked[0]
    if current_best is None:
        return best, True
    current_summary = next((s for s in summaries if s.dns_server == current_best), None)
    if current_summary is None:
        return best, True
    improvement = (best.ewma_latency - current_summary.ewma_latency) / (current_summary.ewma_latency + 1e-9)
    if improvement > switch_threshold:
        return best, True
    else:
        return current_summary, False

# ---------------------------- 图形界面 ---------------------------------
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, colorchooser
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

class DNSBenchmarkGUI:
    def __init__(self, root):
        # 写入启动日志
        start_log = os.path.join(os.path.expanduser("~"), ".dns_bench_plus_gui_start.log")
        with open(start_log, 'w', encoding='utf-8') as f:
            f.write(f"GUI starting at {time.ctime()}\n")
            f.write(f"sys.executable: {sys.executable}\n")
            f.write(f"is_packaged_mode: {is_packaged_mode()}\n")
        self.root = root
        self.root.title("DNS Benchmark Plus")
        self.root.geometry(DEFAULT_WINDOW_GEOMETRY)
        self.root.minsize(900, 650)

        # 状态变量
        self.testing = False
        self.monitoring = False
        self.monitor_thread = None
        self.stop_monitor = threading.Event()
        self.current_best_dns = None
        self.backup_performed = False

        # 参数变量
        self.dns_list_var = tk.StringVar(value="\n".join(DEFAULT_DNS_LIST))
        self.domains_var = tk.StringVar(value="\n".join(DEFAULT_DOMAINS))
        self.query_count_var = tk.IntVar(value=DEFAULT_QUERY_COUNT)
        self.timeout_var = tk.DoubleVar(value=DEFAULT_TIMEOUT)
        self.threads_var = tk.IntVar(value=DEFAULT_THREADS)
        self.switch_threshold_var = tk.DoubleVar(value=DEFAULT_SWITCH_THRESHOLD)
        self.monitor_interval_var = tk.IntVar(value=300)

        self.theme_color = DEFAULT_THEME_COLOR
        self.current_summaries = []

        self._build_ui()
        self._load_config()
        self._apply_theme()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._update_status("就绪")
        with open(start_log, 'a', encoding='utf-8') as f:
            f.write("GUI initialization completed\n")

    def _apply_theme(self):
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('TButton', background=self.theme_color, foreground='black', font=('微软雅黑', 9))
        style.map('TButton', background=[('active', self._darken_color(self.theme_color, 0.2))])
        style.configure('TLabel', font=('微软雅黑', 9))
        style.configure('TLabelframe', font=('微软雅黑', 9))
        style.configure('TLabelframe.Label', font=('微软雅黑', 9, 'bold'))
        style.configure('TEntry', font=('Consolas', 9))
        style.configure('TCombobox', font=('Consolas', 9))
        style.configure('Treeview', font=('Consolas', 9), rowheight=24)
        style.configure('Treeview.Heading', font=('微软雅黑', 9, 'bold'))
        style.configure('TProgressbar', troughcolor='#e0e0e0', background=self.theme_color)
        self.root.configure(bg='#f0f0f0')

    def _darken_color(self, hex_color, factor):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0,5))
        ttk.Label(toolbar, text="主题色:").pack(side=tk.LEFT, padx=5)
        self.theme_btn = ttk.Button(toolbar, text="更改颜色", command=self.choose_color)
        self.theme_btn.pack(side=tk.LEFT, padx=5)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.save_btn = ttk.Button(toolbar, text="保存配置", command=self._save_config)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        ttk.Label(toolbar, text="状态:").pack(side=tk.LEFT, padx=5)
        self.status_label = ttk.Label(toolbar, text="就绪", relief=tk.SUNKEN, width=30)
        self.status_label.pack(side=tk.LEFT, padx=5)

        # 左侧配置区域
        left_frame = ttk.LabelFrame(main_frame, text="配置", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(left_frame, text="DNS 服务器 (每行一个)").pack(anchor=tk.W, pady=(0,2))
        self.dns_text = tk.Text(left_frame, width=28, height=10, font=("Consolas", 9), relief=tk.FLAT, borderwidth=1)
        self.dns_text.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        ttk.Label(left_frame, text="测试域名 (每行一个)").pack(anchor=tk.W, pady=(10,2))
        self.domain_text = tk.Text(left_frame, width=28, height=6, font=("Consolas", 9), relief=tk.FLAT, borderwidth=1)
        self.domain_text.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        param_frame = ttk.LabelFrame(left_frame, text="测试参数", padding="5")
        param_frame.pack(fill=tk.X, pady=5)

        ttk.Label(param_frame, text="查询次数:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(param_frame, from_=1, to=50, textvariable=self.query_count_var, width=8).grid(row=0, column=1, padx=5)

        ttk.Label(param_frame, text="超时(秒):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(param_frame, from_=1, to=10, textvariable=self.timeout_var, width=8).grid(row=1, column=1, padx=5)

        ttk.Label(param_frame, text="线程数:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(param_frame, from_=1, to=50, textvariable=self.threads_var, width=8).grid(row=2, column=1, padx=5)

        ttk.Label(param_frame, text="切换阈值:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(param_frame, from_=0.05, to=0.5, increment=0.05, textvariable=self.switch_threshold_var, width=8).grid(row=3, column=1, padx=5)

        ttk.Label(param_frame, text="监控间隔(秒):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(param_frame, from_=30, to=3600, increment=30, textvariable=self.monitor_interval_var, width=8).grid(row=4, column=1, padx=5)

        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="开始测试", command=self.start_benchmark).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="应用最佳 DNS", command=self.apply_best_dns).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="启动监控", command=self.start_monitor).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="停止监控", command=self.stop_monitor_func).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="恢复 DNS", command=self.restore_dns).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="检测系统 DNS", command=self.detect_system_dns).pack(fill=tk.X, pady=2)

        right_frame = ttk.LabelFrame(main_frame, text="结果", padding="5")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.progress = ttk.Progressbar(right_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)

        columns = ("DNS服务器", "成功率", "中位数延迟(ms)", "平均延迟(ms)", "P95(ms)", "综合评分")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        log_frame = ttk.LabelFrame(right_frame, text="日志", padding="2")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def choose_color(self):
        color = colorchooser.askcolor(title="选择主题色", color=self.theme_color)[1]
        if color:
            self.theme_color = color
            self._apply_theme()
            self._log(f"主题色已更改为 {self.theme_color}")
            self._save_config()

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.dns_text.insert("1.0", self.dns_list_var.get())
            self.domain_text.insert("1.0", self.domains_var.get())
            return
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            dns_list = config.get("dns_list", DEFAULT_DNS_LIST)
            self.dns_text.delete("1.0", tk.END)
            self.dns_text.insert("1.0", "\n".join(dns_list))
            domains = config.get("domains", DEFAULT_DOMAINS)
            self.domain_text.delete("1.0", tk.END)
            self.domain_text.insert("1.0", "\n".join(domains))
            self.query_count_var.set(config.get("query_count", DEFAULT_QUERY_COUNT))
            self.timeout_var.set(config.get("timeout", DEFAULT_TIMEOUT))
            self.threads_var.set(config.get("threads", DEFAULT_THREADS))
            self.switch_threshold_var.set(config.get("switch_threshold", DEFAULT_SWITCH_THRESHOLD))
            self.monitor_interval_var.set(config.get("monitor_interval", 300))
            self.theme_color = config.get("theme_color", DEFAULT_THEME_COLOR)
            geometry = config.get("window_geometry", DEFAULT_WINDOW_GEOMETRY)
            if geometry:
                self.root.geometry(geometry)
            self._log("已加载保存的配置")
        except Exception as e:
            self._log(f"加载配置失败: {e}", "WARNING")
            self.dns_text.insert("1.0", self.dns_list_var.get())
            self.domain_text.insert("1.0", self.domains_var.get())

    def _save_config(self, event=None):
        try:
            config = {
                "dns_list": self._get_dns_list(),
                "domains": self._get_domains(),
                "query_count": self.query_count_var.get(),
                "timeout": self.timeout_var.get(),
                "threads": self.threads_var.get(),
                "switch_threshold": self.switch_threshold_var.get(),
                "monitor_interval": self.monitor_interval_var.get(),
                "theme_color": self.theme_color,
                "window_geometry": self.root.geometry()
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
            self._log("配置已保存")
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            self._log(f"保存配置失败: {e}", "ERROR")
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def _on_closing(self):
        if self.monitoring:
            self.stop_monitor.set()
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
        self._save_config()
        self.root.destroy()

    def _log(self, msg, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        logger.info(msg)

    def _update_status(self, msg):
        self.status_label.config(text=msg)
        self.root.update_idletasks()

    def _get_dns_list(self) -> List[str]:
        text = self.dns_text.get("1.0", tk.END).strip()
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _get_domains(self) -> List[str]:
        text = self.domain_text.get("1.0", tk.END).strip()
        return [line.strip() for line in text.splitlines() if line.strip()]

    def start_benchmark(self):
        if self.testing:
            messagebox.showwarning("提示", "测试已在运行中")
            return
        dns_list = self._get_dns_list()
        if not dns_list:
            messagebox.showerror("错误", "请至少提供一个 DNS 服务器")
            return
        domains = self._get_domains()
        if not domains:
            messagebox.showerror("错误", "请至少提供一个测试域名")
            return

        self.testing = True
        self._update_status("正在测试...")
        self.progress["value"] = 0
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._log(f"开始测试 {len(dns_list)} 个 DNS，域名: {', '.join(domains)}")

        def run_test():
            try:
                result = benchmark(
                    dns_servers=dns_list,
                    domains=domains,
                    query_count=self.query_count_var.get(),
                    timeout=self.timeout_var.get(),
                    threads=self.threads_var.get(),
                    cache_ttl=DEFAULT_CACHE_TTL,
                    use_cache=False,
                    progress_callback=self._update_progress
                )
                self.current_summaries = result.summaries
                self.root.after(0, self._display_results)
                self._log("测试完成")
                self._update_status("测试完成")
            except Exception as e:
                self.root.after(0, lambda: self._log(f"测试失败: {e}", "ERROR"))
                self._update_status("测试失败")
            finally:
                self.testing = False
                self.progress["value"] = 0

        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()

    def _update_progress(self, completed, total):
        if total > 0:
            percent = int(completed / total * 100)
            self.progress["value"] = percent
            self._update_status(f"测试中... {completed}/{total}")

    def _display_results(self):
        ranked = rank_servers(self.current_summaries)
        for s in ranked:
            self.tree.insert("", tk.END, values=(
                s.dns_server,
                f"{s.success_rate*100:.1f}%",
                f"{s.median_latency_ms:.1f}",
                f"{s.avg_latency_ms:.1f}",
                f"{s.p95_latency_ms:.1f}",
                f"{s.ewma_latency:.3f}"
            ))
        if ranked:
            best = ranked[0]
            self.current_best_dns = best.dns_server
            self._log(f"最佳 DNS: {best.dns_server} (综合评分 {best.ewma_latency:.3f})")

    def apply_best_dns(self):
        if not self.current_summaries:
            messagebox.showwarning("警告", "请先运行测试")
            return
        best = rank_servers(self.current_summaries)[0]
        if not is_admin():
            if messagebox.askyesno("权限不足", "修改 DNS 需要管理员权限。是否以管理员身份重新启动程序？"):
                request_admin_restart()
            return
        if not self.backup_performed:
            if backup_system_dns():
                self.backup_performed = True
                self._log("已备份当前 DNS 配置")
        if set_system_dns(best.dns_server):
            self._log(f"成功应用 DNS: {best.dns_server}")
            messagebox.showinfo("成功", f"DNS 已设置为 {best.dns_server}")
        else:
            self._log("应用 DNS 失败", "ERROR")
            messagebox.showerror("错误", "设置 DNS 失败，请检查权限或手动设置")

    def start_monitor(self):
        if self.monitoring:
            messagebox.showwarning("提示", "监控已在运行中")
            return
        dns_list = self._get_dns_list()
        if not dns_list:
            messagebox.showerror("错误", "请至少提供一个 DNS 服务器")
            return
        domains = self._get_domains()
        if not domains:
            messagebox.showerror("错误", "请至少提供一个测试域名")
            return
        auto_switch = messagebox.askyesno("自动切换", "是否启用自动切换最佳 DNS？\n（需要管理员权限）")
        if auto_switch and not is_admin():
            if messagebox.askyesno("权限不足", "自动切换需要管理员权限。是否以管理员身份重新启动程序？"):
                request_admin_restart()
            return

        self.monitoring = True
        self.stop_monitor.clear()
        self._log(f"启动监控模式，间隔 {self.monitor_interval_var.get()} 秒")
        self._update_status("监控运行中...")

        def monitor_worker():
            current_best = get_current_system_dns()
            current_best = current_best[0] if current_best else None
            backup_done = False
            while not self.stop_monitor.is_set():
                try:
                    result = benchmark(
                        dns_servers=dns_list,
                        domains=domains,
                        query_count=self.query_count_var.get(),
                        timeout=self.timeout_var.get(),
                        threads=self.threads_var.get(),
                        cache_ttl=DEFAULT_CACHE_TTL,
                        use_cache=False
                    )
                    best_summary, switched = select_best_server(
                        result.summaries,
                        current_best,
                        switch_threshold=self.switch_threshold_var.get()
                    )
                    if best_summary:
                        self.root.after(0, lambda r=result: self._update_monitor_result(r.summaries))
                        if auto_switch and switched and best_summary.dns_server != current_best:
                            if not backup_done:
                                backup_system_dns()
                                backup_done = True
                            if set_system_dns(best_summary.dns_server):
                                self.root.after(0, lambda: self._log(f"自动切换到 {best_summary.dns_server}"))
                                current_best = best_summary.dns_server
                            else:
                                self.root.after(0, lambda: self._log("自动切换失败", "ERROR"))
                except Exception as e:
                    self.root.after(0, lambda: self._log(f"监控异常: {e}", "ERROR"))
                for _ in range(self.monitor_interval_var.get()):
                    if self.stop_monitor.is_set():
                        break
                    time.sleep(1)
            self.root.after(0, lambda: self._update_status("监控已停止"))

        self.monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        self.monitor_thread.start()

    def _update_monitor_result(self, summaries):
        for item in self.tree.get_children():
            self.tree.delete(item)
        ranked = rank_servers(summaries)
        for s in ranked:
            self.tree.insert("", tk.END, values=(
                s.dns_server,
                f"{s.success_rate*100:.1f}%",
                f"{s.median_latency_ms:.1f}",
                f"{s.avg_latency_ms:.1f}",
                f"{s.p95_latency_ms:.1f}",
                f"{s.ewma_latency:.3f}"
            ))
        if ranked:
            self.current_best_dns = ranked[0].dns_server

    def stop_monitor_func(self):
        if self.monitoring:
            self.stop_monitor.set()
            self.monitoring = False
            self._log("监控已停止")
            self._update_status("监控已停止")
        else:
            messagebox.showinfo("提示", "监控未运行")

    def restore_dns(self):
        if not is_admin():
            if messagebox.askyesno("权限不足", "恢复 DNS 需要管理员权限。是否以管理员身份重新启动程序？"):
                request_admin_restart()
            return
        if restore_system_dns():
            self._log("DNS 已恢复至备份状态")
            messagebox.showinfo("成功", "DNS 已恢复")
            self.backup_performed = False
        else:
            self._log("恢复失败，请检查备份文件", "ERROR")
            messagebox.showerror("错误", "恢复失败")

    def detect_system_dns(self):
        dns_list = get_current_system_dns()
        if dns_list:
            msg = "当前系统 DNS:\n" + "\n".join(dns_list)
            messagebox.showinfo("系统 DNS", msg)
        else:
            messagebox.showwarning("系统 DNS", "未检测到系统 DNS")

# ---------------------------- 主入口 ---------------------------------
def main_cli():
    parser = argparse.ArgumentParser(description="DNS Benchmark Plus – 命令行工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bench_parser = subparsers.add_parser("benchmark", help="一次性测试所有 DNS")
    bench_parser.add_argument("--dns", nargs="+", help="自定义 DNS 列表")
    bench_parser.add_argument("--domains", nargs="+", default=DEFAULT_DOMAINS)
    bench_parser.add_argument("--count", type=int, default=DEFAULT_QUERY_COUNT)
    bench_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    bench_parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    bench_parser.add_argument("--no-cache", action="store_true")
    bench_parser.add_argument("--export", type=str)
    bench_parser.add_argument("--top", type=int, default=10)

    mon_parser = subparsers.add_parser("monitor", help="持续监控")
    mon_parser.add_argument("--dns", nargs="+")
    mon_parser.add_argument("--domains", nargs="+", default=DEFAULT_DOMAINS)
    mon_parser.add_argument("--count", type=int, default=5)
    mon_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    mon_parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    mon_parser.add_argument("--interval", type=int, default=300)
    mon_parser.add_argument("--auto-switch", action="store_true")
    mon_parser.add_argument("--switch-threshold", type=float, default=DEFAULT_SWITCH_THRESHOLD)

    comp_parser = subparsers.add_parser("compare", help="对比特定域名")
    comp_parser.add_argument("domain")
    comp_parser.add_argument("--dns", nargs="+")
    comp_parser.add_argument("--count", type=int, default=DEFAULT_QUERY_COUNT)
    comp_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    comp_parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)

    subparsers.add_parser("restore", help="恢复备份")
    subparsers.add_parser("detect", help="检测系统 DNS")

    args = parser.parse_args()

    if args.command == "restore":
        if not is_admin():
            print("需要管理员/root 权限")
            sys.exit(1)
        restore_system_dns()
        return
    elif args.command == "detect":
        dns_list = get_current_system_dns()
        if dns_list:
            print("当前系统 DNS:")
            for dns in dns_list:
                print(f"  {dns}")
        else:
            print("未检测到系统 DNS")
        return

    if args.dns:
        dns_servers = args.dns
    else:
        dns_servers = DEFAULT_DNS_LIST.copy()
        sys_dns = get_current_system_dns()
        for dns in sys_dns:
            if dns not in dns_servers:
                dns_servers.insert(0, dns)
    dns_servers = list(dict.fromkeys(dns_servers))

    if args.command == "benchmark":
        result = benchmark(dns_servers, args.domains, args.count, args.timeout, args.threads,
                           DEFAULT_CACHE_TTL, use_cache=not args.no_cache)
        ranked = rank_servers(result.summaries)[:args.top]
        headers = ["DNS 服务器", "成功率", "中位数延迟(ms)", "平均延迟(ms)", "P95(ms)", "综合评分"]
        rows = [
            [
                s.dns_server,
                f"{s.success_rate*100:.1f}%",
                f"{s.median_latency_ms:.1f}",
                f"{s.avg_latency_ms:.1f}",
                f"{s.p95_latency_ms:.1f}",
                f"{s.ewma_latency:.3f}"
            ]
            for s in ranked
        ]
        print(format_table(headers, rows))
        if args.export:
            with open(args.export, "w") as f:
                json.dump({"timestamp": result.timestamp, "summaries": [asdict(s) for s in result.summaries]}, f, indent=2)
    elif args.command == "monitor":
        if args.auto_switch and not is_admin():
            print("自动切换需要管理员权限，请使用 sudo 运行")
            sys.exit(1)
        print(f"监控模式，间隔 {args.interval} 秒，按 Ctrl+C 停止")
        current_best = get_current_system_dns()
        current_best = current_best[0] if current_best else None
        backup_done = False
        try:
            while True:
                result = benchmark(dns_servers, args.domains, args.count, args.timeout, args.threads,
                                   DEFAULT_CACHE_TTL, use_cache=False)
                best_summary, switched = select_best_server(result.summaries, current_best, args.switch_threshold)
                if best_summary:
                    print(f"\n最佳: {best_summary.dns_server} (评分 {best_summary.ewma_latency:.3f})")
                    if args.auto_switch and switched and best_summary.dns_server != current_best:
                        if not backup_done:
                            backup_system_dns()
                            backup_done = True
                        if set_system_dns(best_summary.dns_server):
                            print(f"已自动切换到 {best_summary.dns_server}")
                            current_best = best_summary.dns_server
                        else:
                            print("自动切换失败")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n监控停止")
    elif args.command == "compare":
        result = benchmark(dns_servers, [args.domain], args.count, args.timeout, args.threads,
                           DEFAULT_CACHE_TTL, use_cache=False)
        ranked = rank_servers(result.summaries)
        headers = ["DNS 服务器", "成功率", "中位数延迟(ms)", "平均延迟(ms)", "P95(ms)", "综合评分"]
        rows = [
            [
                s.dns_server,
                f"{s.success_rate*100:.1f}%",
                f"{s.median_latency_ms:.1f}",
                f"{s.avg_latency_ms:.1f}",
                f"{s.p95_latency_ms:.1f}",
                f"{s.ewma_latency:.3f}"
            ]
            for s in ranked
        ]
        print(format_table(headers, rows))

def main():
    if len(sys.argv) == 1:
        if not GUI_AVAILABLE:
            print("图形界面需要 tkinter 支持。请安装 python3-tk（Linux）或确保 Python 完整安装（Windows/macOS）")
            sys.exit(1)
        root = tk.Tk()
        if platform.system().lower() == "windows":
            try:
                import ctypes
                HWND = ctypes.windll.user32.GetParent(root.winfo_id())
                DWMWA_WINDOW_CORNER_PREFERENCE = 33
                DWM_WINDOW_CORNER_PREFERENCE = 2
                ctypes.windll.dwmapi.DwmSetWindowAttribute(HWND, DWMWA_WINDOW_CORNER_PREFERENCE,
                                                           ctypes.byref(ctypes.c_int(DWM_WINDOW_CORNER_PREFERENCE)),
                                                           ctypes.sizeof(ctypes.c_int))
            except:
                pass
        app = DNSBenchmarkGUI(root)
        root.mainloop()
    else:
        main_cli()

if __name__ == "__main__":
    main()