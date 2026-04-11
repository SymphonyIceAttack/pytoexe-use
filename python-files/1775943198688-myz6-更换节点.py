import os
import re
import platform
import subprocess

# 节点字典：代号 → (区域名称, IP地址)（完全匹配您提供的节点列表）
nodes = {
    "hb1": ("华北1", "47.92.219.134"),
    "hb2": ("华北2", "123.56.106.49"),
    "hd1": ("华东1", "118.178.147.98"),
    "hd2": ("华东2", "47.102.212.49"),
    "hd3": ("华东3", "101.133.133.237"),
    "hz1": ("华中1", "160.202.238.51"),
    "hn1": ("华南1", "8.134.155.69"),
    "xn1": ("西南1", "47.108.25.114"),
    "xn2": ("西南2", "220.167.103.154"),
    "hk1": ("香港1", "45.113.1.197"),
    "hk2": ("香港2", "38.76.201.180")
}

def test_ping(ip: str) -> float | None:
    """测试到目标IP的ping延迟（单位：毫秒），失败返回None"""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", ip]
    try:
        output = subprocess.run(
            command, capture_output=True, text=True, timeout=10
        ).stdout
        # 解析延迟（适配Windows/Linux/macOS输出）
        if platform.system().lower() == "windows":
            match = re.search(r"时间=(\d+)ms", output)
        else:
            match = re.search(r"time=(\d+\.?\d*) ms", output)
        return float(match.group(1)) if match else None
    except (subprocess.TimeoutExpired, Exception):
        return None

def modify_hosts(domain: str, ip: str, node_name: str, code: str):
    """修改hosts文件：添加/更新「IP+域名」条目，清理旧记录"""
    # 1. 确定hosts文件路径（跨平台）
    hosts_path = (
        r"C:\Windows\System32\drivers\etc\hosts"
        if platform.system().lower() == "windows"
        else "/etc/hosts"
    )
    
    # 2. 检查文件权限（需管理员/sudo）
    if not os.access(hosts_path, os.W_OK):
        raise PermissionError(f"无权限修改{hosts_path}，请以管理员身份运行！")
    
    # 3. 读取原hosts内容，移除旧域名记录
    with open(hosts_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_lines = []
    pattern = re.compile(rf"^\s*\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\s+{re.escape(domain)}\s*(#.*)?$")
    for line in lines:
        if not pattern.match(line.strip()):
            new_lines.append(line)
    
    # 4. 添加新记录（带注释说明）
    new_line = f"{ip} {domain}  # 自动设置：{node_name}({code})\n"
    new_lines.append(new_line)
    
    # 5. 写入文件
    with open(hosts_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def main():
    # 1. 询问需绑定的域名
    domain = input("请输入要更改hosts的域名（例如：example.com）：").strip()
    if not domain:
        print("错误：域名不能为空！")
        return
    
    # 2. 测试所有节点延迟并展示
    print("\n正在测试所有节点延迟...")
    node_results = {}  # 代号→(区域名, IP, 延迟)
    for code, (name, ip) in nodes.items():
        print(f"测试 {name}({code}, {ip})...")
        delay = test_ping(ip)
        if delay is not None:
            node_results[code] = (name, ip, delay)
            print(f"  → 延迟：{delay:.2f} ms")
        else:
            node_results[code] = (name, ip, float("inf"))
            print(f"  → 无法连接（延迟无穷大）")
    
    # 展示所有节点结果
    print("\n===== 所有节点延迟结果 =====")
    for code, (name, ip, delay) in node_results.items():
        status = f"{delay:.2f} ms" if delay != float("inf") else "无法连接"
        print(f"{code}({name}): {ip} → {status}")
    print("=============================\n")
    
    # 3. 选择节点（自动/手动）
    auto_select = input("是否自动选择最快节点？(y/n，默认n)：").strip().lower()
    selected_code = None
    
    if auto_select == "y":
        # 自动选延迟最小的节点
        min_delay = float("inf")
        for code, (name, ip, delay) in node_results.items():
            if delay < min_delay:
                min_delay = delay
                selected_code = code
        if selected_code is None or min_delay == float("inf"):
            print("错误：无可用节点！")
            return
        name, ip, _ = node_results[selected_code]
        print(f"自动选择最快节点：{name}({selected_code}, {ip})，延迟{min_delay:.2f} ms")
    else:
        # 手动输入代号
        print("可用代号：" + ", ".join(nodes.keys()))
        while True:
            selected_code = input("请输入节点代号（例如：hd1）：").strip()
            if selected_code in nodes:
                break
            print(f"错误：代号{selected_code}无效，请重新输入！")
        name, ip, delay = node_results[selected_code]
        status = f"{delay:.2f} ms" if delay != float("inf") else "无法连接"
        print(f"已选节点：{name}({selected_code}, {ip})，延迟{status}")
    
    # 4. 执行hosts修改
    name, ip, _ = node_results[selected_code]
    try:
        modify_hosts(domain, ip, name, selected_code)
        print(f"\n成功：已将{domain}指向{ip}（节点：{name}）")
        # 提示刷新DNS缓存
        if platform.system().lower() == "windows":
            print("提示：请执行「ipconfig /flushdns」刷新DNS缓存")
        elif platform.system().lower() == "darwin":
            print("提示：请执行「dscacheutil -flushcache」刷新DNS缓存")
        else:
            print("提示：请执行「systemctl restart systemd-resolved」刷新DNS缓存")
    except PermissionError as e:
        print(f"错误：{e}")
    except Exception as e:
        print(f"错误：修改hosts失败→{str(e)}")

if __name__ == "__main__":
    main()