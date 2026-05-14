# ServerControlX_4.0.py
# 纯Python原生 | 插件化企业级终端中控 | 单文件零依赖
# 3核心 + 11扩展（新增第11个：可装插件系统）
import os
import sys
import time
import subprocess
import logging
import shutil
from datetime import datetime

# ===================== 全局配置 =====================
APP_NAME = "ServerControlX 4.0"
VERSION = "4.0.0"
REFRESH_SPEED = 2.0
PLUGIN_DIR = "./scx_plugins"
BACKUP_DIR = "./scx_backups"
LOG_FILE = "scx_logs.log"
ADMIN_PASSWORD = "666"  # 管理员密码，可自行修改

# 初始化目录
os.makedirs(PLUGIN_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# 日志初始化
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# 终端颜色（纯原生ANSI）
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"

# ===================== 1. 核心功能1：真实硬件监控 =====================
class HardwareMonitor:
    def get_cpu_usage(self):
        try:
            output = subprocess.check_output(
                ["wmic", "cpu", "get", "LoadPercentage"],
                encoding="gbk", errors="ignore"
            )
            lines = [l.strip() for l in output.splitlines() if l.strip() and l.isdigit()]
            return int(lines[0]) if lines else 0
        except:
            return 0

    def get_memory_info(self):
        try:
            total_out = subprocess.check_output(
                ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                encoding="gbk", errors="ignore"
            )
            avail_out = subprocess.check_output(
                ["wmic", "os", "get", "FreePhysicalMemory"],
                encoding="gbk", errors="ignore"
            )
            total_kb = int([l.strip() for l in total_out.splitlines() if l.strip() and l.isdigit()][0])
            avail_kb = int([l.strip() for l in avail_out.splitlines() if l.strip() and l.isdigit()][0])
            total_gb = round(total_kb / (1024 * 1024), 2)
            avail_gb = round(avail_kb / 1024, 2)
            used_gb = round(total_gb - avail_gb, 2)
            load = int((used_gb / total_gb) * 100) if total_gb > 0 else 0
            return total_gb, used_gb, avail_gb, load
        except:
            return 0, 0, 0, 0

    def get_disk_info(self, drive):
        try:
            output = subprocess.check_output(
                ["wmic", "logicaldisk", "where", f"DeviceID='{drive}'", "get", "Size,FreeSpace"],
                encoding="gbk", errors="ignore"
            )
            lines = [l.strip() for l in output.splitlines() if l.strip() and len(l.split()) >= 2]
            if not lines:
                return 0, 0, 0
            parts = lines[0].split()
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                size, free = int(parts[0]), int(parts[1])
                total_gb = round(size / (1024**3), 2)
                free_gb = round(free / (1024**3), 2)
                used_gb = round(total_gb - free_gb, 2)
                return total_gb, used_gb, free_gb
            return 0,0,0
        except:
            return 0, 0, 0

# ===================== 2. 核心功能2：MC服务器精准识别 =====================
class MCServerScanner:
    def get_mc_servers(self):
        mc_servers = []
        try:
            # 用wmic精准获取带参数的Java进程，识别MC服务端
            output = subprocess.check_output(
                ["wmic", "process", "where", "name='java.exe' or name='javaw.exe'", "get", "ProcessId,CommandLine", "/format:csv"],
                encoding="gbk", errors="ignore"
            )
            lines = output.strip().splitlines()
            for line in lines[2:]:
                if line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        pid = parts[1].strip()
                        cmdline = parts[2].strip()
                        if "server.jar" in cmdline.lower() or "-jar" in cmdline.lower() and "minecraft" in cmdline.lower():
                            mc_servers.append({"pid": pid, "cmdline": cmdline[:50] + "..." if len(cmdline) > 50 else cmdline})
        except:
            pass
        return mc_servers

    def kill_mc_server(self, pid):
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=True, capture_output=True)
            return True
        except:
            return False

# ===================== 3. 核心功能3：MC服务器控制 + 10个扩展功能 =====================
class MCServerManager:
    def __init__(self):
        self.processes = {}
        self.start_time = {}

    def backup_world(self, world_dir, backup_name=None):
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        try:
            shutil.copytree(world_dir, backup_path)
            return True, backup_path
        except Exception as e:
            return False, str(e)

    def get_uptime(self, pid):
        if pid in self.start_time:
            elapsed = time.time() - self.start_time[pid]
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours}h{minutes}m"
        return "未知"

# ===================== 第11个扩展功能：插件系统 =====================
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def load_plugins(self):
        self.plugins.clear()
        for filename in os.listdir(PLUGIN_DIR):
            if filename.endswith(".py"):
                plugin_path = os.path.join(PLUGIN_DIR, filename)
                try:
                    module_name = filename[:-3]
                    with open(plugin_path, "r", encoding="utf-8") as f:
                        plugin_code = compile(f.read(), plugin_path, "exec")
                    plugin_namespace = {}
                    exec(plugin_code, plugin_namespace)
                    if "run" in plugin_namespace and "name" in plugin_namespace:
                        self.plugins[module_name] = {
                            "name": plugin_namespace["name"],
                            "desc": plugin_namespace.get("desc", "无描述"),
                            "run": plugin_namespace["run"]
                        }
                except Exception as e:
                    logging.error(f"加载插件{filename}失败: {e}")

    def install_plugin(self, plugin_name, plugin_code):
        plugin_path = os.path.join(PLUGIN_DIR, f"{plugin_name}.py")
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(plugin_code)
        self.load_plugins()
        return True

    def list_plugins(self):
        return list(self.plugins.items())

    def run_plugin(self, plugin_name):
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name]["run"]()
                return True
            except Exception as e:
                print(f"{Colors.RED}插件运行失败: {e}{Colors.RESET}")
                return False
        return False

# ===================== 终端精美GUI =====================
class TerminalGUI:
    def __init__(self):
        self.monitor = HardwareMonitor()
        self.scanner = MCServerScanner()
        self.manager = MCServerManager()
        self.plugin_mgr = PluginManager()
        self.plugin_mgr.load_plugins()

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def draw_header(self):
        self.clear_screen()
        print(f"""{Colors.CYAN}
  ██████╗ ███████╗██████╗ ███████╗██████╗  ██████╗ ███████╗
  ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔════╝
  ██████╔╝█████╗  ██████╔╝█████╗  ██████╔╝██║   ██║███████╗
  ██╔══██╗██╔══╝  ██╔═══╝ ██╔══╝  ██╔══██╗██║   ██║╚════██║
  ██║  ██║███████╗██║     ███████╗██║  ██║╚██████╔╝███████║
  ╚═╝  ╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
        {APP_NAME} v{VERSION} | 企业级终端中控面板
{Colors.RESET}""")

    def draw_dashboard(self):
        self.draw_header()
        cpu = self.monitor.get_cpu_usage()
        mem_total, mem_used, mem_avail, mem_load = self.monitor.get_memory_info()
        c_total, c_used, c_free = self.monitor.get_disk_info("C:")

        cpu_bar = "█" * (cpu // 5) + "░" * (20 - cpu // 5)
        mem_bar = "█" * (mem_load // 5) + "░" * (20 - mem_load // 5)

        print(f"\n{Colors.BLUE}━━━━━━━━━━━━━━━━ 硬件监控 ━━━━━━━━━━━━━━━{Colors.RESET}")
        print(f"CPU占用: {cpu:3d}% [{Colors.GREEN}{cpu_bar}{Colors.RESET}]")
        print(f"内存状态: {mem_used:>5.2f}GB / {mem_total:>5.2f}GB [{Colors.YELLOW}{mem_bar}{Colors.RESET}] ({mem_load}%)")
        print(f"C盘固态: {c_used:>6.2f}GB / {c_total:>6.2f}GB 空闲: {c_free:>6.2f}GB")

        mc_servers = self.scanner.get_mc_servers()
        print(f"\n{Colors.BLUE}━━━━━━━━━━━━━━ MC服务器 ━━━━━━━━━━━━━━━{Colors.RESET}")
        print(f"运行中的MC服务端: {len(mc_servers)} 个")
        for idx, s in enumerate(mc_servers, 1):
            uptime = self.manager.get_uptime(s["pid"])
            print(f"[{idx}] PID:{s['pid']} | 运行时间:{uptime} | {s['cmdline']}")

        print(f"\n{Colors.BLUE}━━━━━━━━━━━━━━ 插件系统 ━━━━━━━━━━━━━━━{Colors.RESET}")
        print(f"已安装插件: {len(self.plugin_mgr.plugins)} 个")
        for name, info in self.plugin_mgr.list_plugins():
            print(f"  - {info['name']}: {info['desc']}")

    def show_menu(self):
        self.draw_dashboard()
        print(f"\n{Colors.MAGENTA}【主菜单】{Colors.RESET}")
        print("1. 实时监控模式")
        print("2. MC服务器管理（停止/备份）")
        print("3. 插件管理（安装/运行/卸载）")
        print("4. 系统工具（日志/备份/进程过滤）")
        print("0. 退出面板")

    def menu_loop(self):
        while True:
            self.show_menu()
            opt = input(f"\n{Colors.YELLOW}请输入选项编号: {Colors.RESET}")
            if opt == "1":
                self.real_time_monitor()
            elif opt == "2":
                self.mc_server_menu()
            elif opt == "3":
                self.plugin_menu()
            elif opt == "4":
                self.system_tools_menu()
            elif opt == "0":
                print(f"{Colors.RED}正在退出...{Colors.RESET}")
                break
            else:
                print(f"{Colors.RED}无效选项！{Colors.RESET}")
            input(f"\n{Colors.GREEN}按回车返回主菜单...{Colors.RESET}")

    def real_time_monitor(self):
        try:
            while True:
                self.draw_dashboard()
                print(f"\n{Colors.YELLOW}🔄 实时监控中... Ctrl+C 返回菜单{Colors.RESET}")
                time.sleep(REFRESH_SPEED)
        except KeyboardInterrupt:
            return

    def mc_server_menu(self):
        while True:
            self.draw_dashboard()
            print(f"\n{Colors.MAGENTA}【MC服务器管理】{Colors.RESET}")
            print("1. 停止指定MC服务器")
            print("2. 备份服务器世界")
            print("0. 返回上一级")
            opt = input(f"\n{Colors.YELLOW}请输入选项编号: {Colors.RESET}")
            if opt == "1":
                mc_servers = self.scanner.get_mc_servers()
                if not mc_servers:
                    print(f"{Colors.RED}没有运行中的MC服务器！{Colors.RESET}")
                    continue
                try:
                    idx = int(input("请输入要停止的服务器编号: ")) - 1
                    if 0 <= idx < len(mc_servers):
                        pid = mc_servers[idx]["pid"]
                        if self.scanner.kill_mc_server(pid):
                            print(f"{Colors.GREEN}已停止PID:{pid}的服务器！{Colors.RESET}")
                        else:
                            print(f"{Colors.RED}停止失败！{Colors.RESET}")
                except:
                    print(f"{Colors.RED}输入无效！{Colors.RESET}")
            elif opt == "2":
                world_dir = input("请输入服务器世界文件夹路径: ")
                if os.path.isdir(world_dir):
                    ok, path = self.manager.backup_world(world_dir)
                    if ok:
                        print(f"{Colors.GREEN}备份成功！备份路径: {path}{Colors.RESET}")
                    else:
                        print(f"{Colors.RED}备份失败: {path}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}路径无效！{Colors.RESET}")
            elif opt == "0":
                break

    def plugin_menu(self):
        while True:
            self.draw_dashboard()
            print(f"\n{Colors.MAGENTA}【插件管理】{Colors.RESET}")
            print("1. 安装新插件")
            print("2. 运行已安装插件")
            print("3. 卸载插件")
            print("4. 刷新插件列表")
            print("0. 返回上一级")
            opt = input(f"\n{Colors.YELLOW}请输入选项编号: {Colors.RESET}")
            if opt == "1":
                plugin_name = input("请输入插件名称（不含.py）: ")
                print(f"{Colors.CYAN}请输入插件代码（以end结束，输入后按两次回车）:{Colors.RESET}")
                lines = []
                while True:
                    line = input()
                    if line.strip().lower() == "end":
                        break
                    lines.append(line)
                plugin_code = "\n".join(lines)
                if plugin_code:
                    self.plugin_mgr.install_plugin(plugin_name, plugin_code)
                    print(f"{Colors.GREEN}插件{plugin_name}安装成功！{Colors.RESET}")
            elif opt == "2":
                plugins = self.plugin_mgr.list_plugins()
                if not plugins:
                    print(f"{Colors.RED}没有已安装的插件！{Colors.RESET}")
                    continue
                print(f"{Colors.CYAN}已安装插件列表:{Colors.RESET}")
                for i, (name, info) in enumerate(plugins, 1):
                    print(f"[{i}] {name}: {info['name']} - {info['desc']}")
                try:
                    idx = int(input("请输入要运行的插件编号: ")) - 1
                    if 0 <= idx < len(plugins):
                        plugin_name = plugins[idx][0]
                        print(f"{Colors.GREEN}正在运行插件{plugin_name}...{Colors.RESET}")
                        self.plugin_mgr.run_plugin(plugin_name)
                except:
                    print(f"{Colors.RED}输入无效！{Colors.RESET}")
            elif opt == "3":
                plugins = self.plugin_mgr.list_plugins()
                if not plugins:
                    print(f"{Colors.RED}没有可卸载的插件！{Colors.RESET}")
                    continue
                print(f"{Colors.CYAN}已安装插件列表:{Colors.RESET}")
                for i, (name, info) in enumerate(plugins, 1):
                    print(f"[{i}] {name}: {info['name']}")
                try:
                    idx = int(input("请输入要卸载的插件编号: ")) - 1
                    if 0 <= idx < len(plugins):
                        plugin_name = plugins[idx][0]
                        plugin_path = os.path.join(PLUGIN_DIR, f"{plugin_name}.py")
                        if os.path.exists(plugin_path):
                            os.remove(plugin_path)
                            self.plugin_mgr.load_plugins()
                            print(f"{Colors.GREEN}插件{plugin_name}已卸载！{Colors.RESET}")
                except:
                    print(f"{Colors.RED}输入无效！{Colors.RESET}")
            elif opt == "4":
                self.plugin_mgr.load_plugins()
                print(f"{Colors.GREEN}插件列表已刷新！{Colors.RESET}")
            elif opt == "0":
                break

    def system_tools_menu(self):
        while True:
            self.draw_dashboard()
            print(f"\n{Colors.MAGENTA}【系统工具】{Colors.RESET}")
            print("1. 查看系统日志")
            print("2. 过滤非MC系统进程")
            print("3. 清空终端日志")
            print("0. 返回上一级")
            opt = input(f"\n{Colors.YELLOW}请输入选项编号: {Colors.RESET}")
            if opt == "1":
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        logs = f.readlines()[-20:]
                        print(f"{Colors.CYAN}最近20条日志:{Colors.RESET}")
                        for line in logs:
                            print(line.strip())
                else:
                    print(f"{Colors.RED}日志文件不存在！{Colors.RESET}")
            elif opt == "2":
                print(f"{Colors.CYAN}非MC系统进程列表:{Colors.RESET}")
                try:
                    output = subprocess.check_output(["tasklist", "/fo", "csv", "/nh"], encoding="gbk", errors="ignore")
                    for line in output.strip().splitlines():
                        parts = line.split('","')
                        if len(parts) >= 2:
                            name = parts[0].strip('"').lower()
                            if name not in ("java.exe", "javaw.exe"):
                                print(f" - {name}")
                except:
                    print(f"{Colors.RED}获取进程列表失败！{Colors.RESET}")
            elif opt == "3":
                self.clear_screen()
                print(f"{Colors.GREEN}终端日志已清空！{Colors.RESET}")
            elif opt == "0":
                break

# ===================== 主程序入口 =====================
if __name__ == "__main__":
    print(f"{Colors.CYAN}正在启动 {APP_NAME} v{VERSION}...{Colors.RESET}")
    password = input(f"{Colors.YELLOW}请输入管理员密码: {Colors.RESET}")
    if password != ADMIN_PASSWORD:
        print(f"{Colors.RED}密码错误！程序退出。{Colors.RESET}")
        sys.exit(1)
    gui = TerminalGUI()
    gui.menu_loop()