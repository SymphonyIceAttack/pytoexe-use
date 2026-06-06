import os
import hashlib
import shutil
import json
import threading
import time
import random
import winreg  # Windows注册表，用于启动项管理
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 全局路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
VIRUS_DB_PATH = os.path.join(BASE_DIR, "virus_db.json")

def load_config():
    """加载配置文件，不存在则创建默认配置"""
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "scan": {
                "default_paths": ["C:\\", "D:\\"],
                "quick_scan_paths": [
                    os.path.expanduser("~\\AppData\\Local\\Temp"),
                    "C:\\Windows\\Temp",
                    "C:\\Windows\\System32",
                    os.path.expanduser("~\\Downloads")
                ],
                "exclude_paths": []
            },
            "real_time_protection": {
                "enabled": False,
                "watch_paths": [os.path.expanduser("~"), "C:\\"]
            },
            "quarantine": {
                "path": os.path.join(BASE_DIR, "quarantine"),
                "max_size": 1024 * 1024 * 100
            },
            "white_list": [],
            "log": {
                "path": os.path.join(BASE_DIR, "antivirus.log")
            },
            "virus_db_path": VIRUS_DB_PATH
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config
    else:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

def load_virus_db():
    """加载病毒库，不存在则创建默认病毒库"""
    if not os.path.exists(VIRUS_DB_PATH):
        # 默认病毒库，包含EICAR测试文件特征
        default_db = {
            "version": "1.0.0",
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "signatures": {
                # EICAR测试文件的SHA256，用于测试杀毒功能
                "f5643635472030586116102351ea0ffb93c566310822020a20d3c50122691f39": {
                    "name": "EICAR-Test-File",
                    "level": "Test",
                    "description": "杀毒软件标准测试文件，非真实病毒"
                }
            }
        }
        # 确保隔离区目录存在
        config = load_config()
        os.makedirs(config["quarantine"]["path"], exist_ok=True)
        with open(VIRUS_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(default_db, f, indent=4, ensure_ascii=False)
        return default_db
    else:
        with open(VIRUS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

def get_file_sha256(file_path):
    """计算文件的SHA256哈希值，分块处理大文件"""
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None

def heuristic_scan(file_path):
    """基础启发式扫描，检测可疑字符串特征"""
    suspicious_strings = [
        b"CreateRemoteThread",
        b"VirtualAlloc",
        b"WriteProcessMemory",
        b"WinExec",
        b"ShellExecute",
        b"rundll32.exe",
        b"powershell -enc",
        b"cmd.exe /c",
        b"reg add",
        b"bitcoin",
        b"ransomware",
        b"wannacry"
    ]
    try:
        # 仅对10MB以下的文件做启发式扫描，提升性能
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            return False, None
        with open(file_path, "rb") as f:
            content = f.read()
            for s in suspicious_strings:
                if s in content:
                    return True, f"发现可疑字符串: {s.decode('utf-8', errors='ignore')}"
        return False, None
    except Exception:
        return False, None

def scan_file(file_path, config, virus_db):
    """扫描单个文件，检查是否为威胁"""
    # 检查白名单
    if file_path in config["white_list"]:
        return False, None, None
    if os.path.isdir(file_path):
        return False, None, None
    # 检查排除路径
    for exclude in config["scan"]["exclude_paths"]:
        if file_path.startswith(exclude):
            return False, None, None
    
    # 特征码扫描
    file_hash = get_file_sha256(file_path)
    if not file_hash:
        return False, None, None
    if file_hash in virus_db["signatures"]:
        sig = virus_db["signatures"][file_hash]
        return True, sig["name"], sig["description"]
    
    # 启发式扫描
    heu_result, heu_msg = heuristic_scan(file_path)
    if heu_result:
        return True, "Heuristic-Suspicious", heu_msg
    
    return False, None, None

def scan_directory(path, config, virus_db):
    """扫描整个目录，返回发现的威胁列表"""
    threats = []
    total_files = 0
    scanned_files = 0

    # 统计总文件数
    print("正在统计文件数量...")
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in config["scan"]["exclude_paths"]]
        total_files += len(files)
    print(f"共发现 {total_files} 个文件，开始扫描...")

    # 开始扫描
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in config["scan"]["exclude_paths"]]
        for file in files:
            file_path = os.path.join(root, file)
            if file_path in config["white_list"]:
                scanned_files += 1
                continue
            
            is_threat, name, desc = scan_file(file_path, config, virus_db)
            scanned_files += 1
            if is_threat:
                threats.append({
                    "path": file_path,
                    "name": name,
                    "description": desc
                })
                print(f"[!] 发现威胁: {file_path} - {name}")
            
            # 显示进度
            if total_files > 0 and scanned_files % 100 == 0:
                progress = (scanned_files / total_files) * 100
                print(f"扫描进度: {scanned_files}/{total_files} ({progress:.1f}%)")
    
    return threats

def quarantine_file(file_path, config):
    """将威胁文件移动到隔离区"""
    quarantine_path = config["quarantine"]["path"]
    os.makedirs(quarantine_path, exist_ok=True)
    
    filename = os.path.basename(file_path)
    new_name = f"{int(time.time())}_{filename}"
    dest_path = os.path.join(quarantine_path, new_name)
    
    try:
        shutil.move(file_path, dest_path)
        # 保存原始路径信息，用于恢复
        info_path = dest_path + ".info"
        info = {
            "original_path": file_path,
            "quarantine_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=4)
        print(f"[+] 文件已隔离: {file_path} -> {dest_path}")
        return True
    except Exception as e:
        print(f"[-] 隔离失败: {e}")
        return False

class RealTimeHandler(FileSystemEventHandler):
    """实时文件监控事件处理器"""
    def __init__(self, config, virus_db):
        self.config = config
        self.virus_db = virus_db
        super().__init__()
    
    def on_created(self, event):
        if not event.is_directory:
            print(f"\n[实时监控] 检测到新文件: {event.src_path}")
            is_threat, name, desc = scan_file(event.src_path, self.config, self.virus_db)
            if is_threat:
                print(f"[!] 实时防护发现威胁: {event.src_path} - {name}: {desc}")
                quarantine_file(event.src_path, self.config)
    
    def on_modified(self, event):
        if not event.is_directory:
            is_threat, name, desc = scan_file(event.src_path, self.config, self.virus_db)
            if is_threat:
                print(f"\n[!] 实时防护发现威胁(修改后): {event.src_path} - {name}: {desc}")
                quarantine_file(event.src_path, self.config)

def start_real_time_protection(config, virus_db):
    """启动实时防护"""
    event_handler = RealTimeHandler(config, virus_db)
    observer = Observer()
    
    for path in config["real_time_protection"]["watch_paths"]:
        if os.path.exists(path):
            observer.schedule(event_handler, path, recursive=True)
            print(f"[+] 开始监控路径: {path}")
    
    observer.start()
    print("[+] 实时防护已启动，按回车停止...")
    try:
        input()
    except KeyboardInterrupt:
        pass
    observer.stop()
    observer.join()
    print("[-] 实时防护已停止")

def clean_junk_files(config):
    """清理系统垃圾文件"""
    junk_paths = [
        os.path.expanduser("~\\AppData\\Local\\Temp"),
        "C:\\Windows\\Temp",
        os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\Explorer\\Recent")
    ]
    total_cleaned = 0
    cleaned_files = 0
    
    print("正在扫描垃圾文件...")
    for path in junk_paths:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_cleaned += size
                    cleaned_files += 1
                except:
                    pass
    
    total_cleaned_mb = total_cleaned / (1024 * 1024)
    print(f"[+] 垃圾清理完成，共清理 {cleaned_files} 个文件，释放 {total_cleaned_mb:.2f} MB 空间")

def manage_startup_items():
    """启动项管理"""
    startup_reg_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]
    startup_items = []
    
    print("正在加载启动项...")
    for hkey, path in startup_reg_paths:
        try:
            key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, type_ = winreg.EnumValue(key, i)
                    startup_items.append({
                        "name": name,
                        "path": value,
                        "hive": hkey,
                        "key_path": path
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[-] 读取注册表失败: {path}, {e}")
    
    print("\n当前启动项:")
    for idx, item in enumerate(startup_items, 1):
        print(f"{idx}. {item['name']}: {item['path']}")
    
    choice = input("输入要禁用的启动项编号(输入0返回): ")
    if choice == "0":
        return
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(startup_items):
            item = startup_items[idx]
            key = winreg.OpenKey(item["hive"], item["key_path"], 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, item["name"])
            winreg.CloseKey(key)
            print(f"[+] 已禁用启动项: {item['name']}")
        else:
            print("[-] 无效的编号")
    except Exception as e:
        print(f"[-] 操作失败: {e}")

def shred_file(file_path):
    """文件粉碎，多次覆盖防止恢复"""
    if not os.path.exists(file_path):
        print("[-] 文件不存在")
        return
    if os.path.isdir(file_path):
        print("[-] 不支持目录粉碎，请输入文件路径")
        return
    
    try:
        size = os.path.getsize(file_path)
        print(f"正在粉碎文件: {file_path}, 大小: {size/1024/1024:.2f} MB")
        
        # 3次覆盖，符合基础粉碎标准
        with open(file_path, "rb+") as f:
            for pass_num in range(3):
                print(f"粉碎进度: {pass_num+1}/3")
                f.seek(0)
                f.write(random.randbytes(size))
                f.flush()
                os.fsync(f)
        
        os.remove(file_path)
        print(f"[+] 文件粉碎完成，无法恢复")
    except Exception as e:
        print(f"[-] 粉碎失败: {e}")

def manage_white_list(config):
    """白名单管理"""
    print("\n当前白名单:")
    for idx, path in enumerate(config["white_list"], 1):
        print(f"{idx}. {path}")
    
    print("\n选项: 1.添加 2.删除 0.返回")
    choice = input("请选择: ")
    if choice == "0":
        return
    elif choice == "1":
        path = input("输入要添加到白名单的文件/路径: ")
        if os.path.exists(path):
            if path not in config["white_list"]:
                config["white_list"].append(path)
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                print(f"[+] 已添加到白名单: {path}")
            else:
                print("[-] 该路径已在白名单中")
        else:
            print("[-] 路径不存在")
    elif choice == "2":
        idx = input("输入要删除的白名单编号: ")
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(config["white_list"]):
                path = config["white_list"].pop(idx)
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                print(f"[+] 已从白名单移除: {path}")
            else:
                print("[-] 无效的编号")
        except:
            print("[-] 输入错误")
    else:
        print("[-] 无效的选项")

def manage_quarantine(config):
    """隔离区管理"""
    quarantine_path = config["quarantine"]["path"]
    os.makedirs(quarantine_path, exist_ok=True)
    quarantined_files = []
    
    print("正在加载隔离区文件...")
    for file in os.listdir(quarantine_path):
        if file.endswith(".info"):
            continue
        info_file = file + ".info"
        info_path = os.path.join(quarantine_path, info_file)
        if os.path.exists(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                info = json.load(f)
                quarantined_files.append({
                    "file_name": file,
                    "original_path": info["original_path"],
                    "quarantine_time": info["quarantine_time"]
                })
    
    print("\n隔离区文件:")
    for idx, item in enumerate(quarantined_files, 1):
        print(f"{idx}. {item['original_path']} - 隔离时间: {item['quarantine_time']}")
    
    print("\n选项: 1.恢复文件 2.删除文件 0.返回")
    choice = input("请选择: ")
    if choice == "0":
        return
    elif choice == "1":
        idx = input("输入要恢复的文件编号: ")
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(quarantined_files):
                item = quarantined_files[idx]
                file_path = os.path.join(quarantine_path, item["file_name"])
                info_path = file_path + ".info"
                shutil.move(file_path, item["original_path"])
                os.remove(info_path)
                print(f"[+] 已恢复文件到: {item['original_path']}")
            else:
                print("[-] 无效的编号")
        except Exception as e:
            print(f"[-] 恢复失败: {e}")
    elif choice == "2":
        idx = input("输入要删除的文件编号: ")
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(quarantined_files):
                item = quarantined_files[idx]
                file_path = os.path.join(quarantine_path, item["file_name"])
                info_path = file_path + ".info"
                os.remove(file_path)
                os.remove(info_path)
                print(f"[+] 已删除隔离文件: {item['original_path']}")
            else:
                print("[-] 无效的编号")
        except Exception as e:
            print(f"[-] 删除失败: {e}")
    else:
        print("[-] 无效的选项")

def main_menu():
    """主菜单"""
    print("\n" + "="*50)
    print("Python简易杀毒软件 (仿照火绒/360安全功能)")
    print("版本: 1.0.0")
    print("="*50)
    print("1. 病毒扫描")
    print("2. 实时防护")
    print("3. 垃圾清理")
    print("4. 启动项管理")
    print("5. 文件粉碎")
    print("6. 白名单管理")
    print("7. 隔离区管理")
    print("0. 退出")
    print("="*50)
    choice = input("请选择功能: ")
    return choice

def scan_menu(config, virus_db):
    """扫描子菜单"""
    print("\n病毒扫描选项:")
    print("1. 快速扫描 (系统关键目录)")
    print("2. 全盘扫描")
    print("3. 自定义目录扫描")
    print("0. 返回")
    choice = input("请选择: ")
    threats = []
    
    if choice == "1":
        print("开始快速扫描...")
        for path in config["scan"]["quick_scan_paths"]:
            if os.path.exists(path):
                print(f"扫描路径: {path}")
                threats.extend(scan_directory(path, config, virus_db))
    elif choice == "2":
        print("开始全盘扫描...")
        for path in config["scan"]["default_paths"]:
            if os.path.exists(path):
                threats.extend(scan_directory(path, config, virus_db))
    elif choice == "3":
        path = input("输入要扫描的目录路径: ")
        if os.path.exists(path):
            print(f"开始扫描: {path}")
            threats = scan_directory(path, config, virus_db)
        else:
            print("[-] 路径不存在")
            return
    elif choice == "0":
        return
    else:
        print("[-] 无效的选项")
        return
    
    print("\n扫描完成!")
    if len(threats) == 0:
        print("未发现任何威胁，您的系统很安全!")
        return
    
    print(f"共发现 {len(threats)} 个威胁:")
    for idx, t in enumerate(threats, 1):
        print(f"{idx}. {t['path']} - {t['name']}: {t['description']}")
    
    action = input("是否自动隔离所有威胁? (y/n): ")
    if action.lower() == "y":
        for t in threats:
            quarantine_file(t["path"], config)
        print("[+] 所有威胁已隔离!")

def main():
    print("正在加载配置...")
    config = load_config()
    print("正在加载病毒库...")
    virus_db = load_virus_db()
    print("加载完成!")
    
    while True:
        choice = main_menu()
        if choice == "1":
            scan_menu(config, virus_db)
        elif choice == "2":
            start_real_time_protection(config, virus_db)
        elif choice == "3":
            clean_junk_files(config)
        elif choice == "4":
            manage_startup_items()
        elif choice == "5":
            path = input("输入要粉碎的文件路径: ")
            shred_file(path)
        elif choice == "6":
            manage_white_list(config)
        elif choice == "7":
            manage_quarantine(config)
        elif choice == "0":
            print("感谢使用，再见!")
            break
        else:
            print("[-] 无效的选项，请重新输入!")
        input("\n按回车继续...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序已退出")
    except Exception as e:
        print(f"程序出错: {e}")
        input("按回车退出...")
