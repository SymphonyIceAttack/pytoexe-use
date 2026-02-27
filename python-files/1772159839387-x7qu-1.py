# -*- coding: utf-8 -*-
import sys
import os
import time
import json
import winreg
import configparser
import logging
import stat
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ---------------------------- 配置日志 ----------------------------
log_file = os.path.join(os.path.dirname(sys.argv[0]), 'unlocker.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ---------------------------- 获取程序所在目录 ----------------------------
APP_PATH = os.path.abspath(sys.argv[0])
DIR_PATH = os.path.dirname(APP_PATH)

# ---------------------------- 读取配置文件 ----------------------------
config = configparser.ConfigParser()
config_path = os.path.join(DIR_PATH, 'config.ini')
if not os.path.exists(config_path):
    logging.error("配置文件 config.ini 不存在，请将配置文件放置于程序同目录下")
    sys.exit(1)
config.read(config_path, encoding='utf-8')

# ---------------------------- 获取微信文件保存目录 ----------------------------
def get_wechat_save_path():
    """从注册表获取微信文件保存根目录"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat") as key:
            user_documents_path, _ = winreg.QueryValueEx(key, "FileSavePath")
    except FileNotFoundError:
        logging.error("未找到微信安装信息，请确认微信已安装")
        sys.exit(1)

    if user_documents_path == "MyDocument:":
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                user_documents_path, _ = winreg.QueryValueEx(key, "Personal")
        except FileNotFoundError:
            logging.error("无法获取用户文档路径")
            sys.exit(1)

    return os.path.join(user_documents_path, "WeChat Files")

# ---------------------------- 解除文件只读 ----------------------------
def remove_readonly(file_path):
    """移除文件的只读属性，成功返回 True，失败返回 False"""
    try:
        current_mode = os.stat(file_path).st_mode
        if not current_mode & stat.S_IWRITE:
            os.chmod(file_path, current_mode | stat.S_IWRITE)
            logging.info(f"解除只读: {file_path}")
            return True
    except Exception as e:
        logging.error(f"解除只读失败 {file_path}: {e}")
    return False

# ---------------------------- 事件处理器 ----------------------------
class FileEventHandler(FileSystemEventHandler):
    def __init__(self, processed_files, lock):
        self.processed_files = processed_files
        self.lock = lock

    def _handle(self, file_path):
        """统一处理新增或移动过来的文件"""
        if not os.path.isfile(file_path):
            return
        with self.lock:
            if file_path in self.processed_files:
                return
            if remove_readonly(file_path):
                self.processed_files[file_path] = True

    def on_created(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle(event.dest_path)

# ---------------------------- 开机自启管理 ----------------------------
def set_startup(enable):
    """设置或取消开机自启"""
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            if enable:
                winreg.SetValueEx(key, "WeChatFileUnlocker", 0, winreg.REG_SZ, APP_PATH)
                logging.info("已设置开机自启")
            else:
                try:
                    winreg.DeleteValue(key, "WeChatFileUnlocker")
                    logging.info("已取消开机自启")
                except FileNotFoundError:
                    pass
    except Exception as e:
        logging.error(f"设置开机自启失败: {e}")

# ---------------------------- 主函数 ----------------------------
def main():
    # 1. 获取微信文件根目录
    parent_folder = get_wechat_save_path()
    logging.info(f"微信文件根目录: {parent_folder}")

    # 2. 收集所有 wxid 文件夹下的 FileStorage\File 目录
    target_folders = []
    for root, dirs, _ in os.walk(parent_folder):
        for d in dirs:
            if d.startswith('wxid'):
                target = os.path.join(root, d, 'FileStorage', 'File')
                if os.path.exists(target):
                    target_folders.append(target)
    if not target_folders:
        logging.warning("未找到任何 wxid 目录，请确认微信文件保存位置是否正确")
    else:
        logging.info(f"目标文件夹: {target_folders}")

    # 3. 加载已处理文件记录
    json_path = os.path.join(DIR_PATH, 'processed_files.json')
    processed_files = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                processed_files = json.load(f)
        except Exception as e:
            logging.error(f"加载记录文件失败: {e}")

    # 4. 初次遍历，解除已有文件的只读状态
    lock = threading.Lock()
    for folder in target_folders:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                with lock:
                    if file_path in processed_files:
                        continue
                if remove_readonly(file_path):
                    with lock:
                        processed_files[file_path] = True

    # 5. 保存处理记录
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(processed_files, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存记录失败: {e}")

    # 6. 设置开机自启
    auto_start = config.getboolean('AUTO_STARTUP', 'enabled', fallback=False)
    set_startup(auto_start)

    # 7. 启动文件系统监听
    event_handler = FileEventHandler(processed_files, lock)
    observer = Observer()
    for folder in target_folders:
        observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    logging.info("开始监听文件夹...")

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    logging.info("程序退出")

if __name__ == '__main__':
    main()