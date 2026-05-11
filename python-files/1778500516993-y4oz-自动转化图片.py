import os
import sys
import time
import gc
import logging
import queue
import threading
import ctypes
import subprocess
import win32api
import win32con
import win32gui
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# -------------------------- 版本检查 --------------------------
if sys.version_info < (3, 6):
    print("❌ 错误：本程序需要 Python 3.6 或更高版本运行")
    sys.exit(1)

# -------------------------- 核心配置 --------------------------
MONITOR_PATHS = [
    {"source": r"D:\MMCD_结果", "target": r"D:\MMCD_结果2"},
    {"source": r"E:\MMCD_结果", "target": r"E:\MMCD_结果2"}
]

# ====================== 压缩参数 ======================
JPG_QUALITY = 75
CHROMA_SUBSAMPLING = 2
OPTIMIZE = True
PROGRESSIVE = False
# ======================================================

# ====================== 自动清理配置 ======================
AUTO_CLEAN_ENABLED = True  # 是否启用图片自动清理
CLEAN_DAYS = 90  # 清理超过多少天的图片（90天=3个月）
CLEAN_HOUR = 2  # 每天几点运行图片清理（默认凌晨2点）
CLEAN_ON_STARTUP = False  # 程序启动时是否立即运行一次图片清理

# 日志自动清理配置
LOG_MAX_SIZE_MB = 10  # 单个日志文件最大大小
LOG_BACKUP_COUNT = 3  # 最多保留多少个日志备份
LOG_KEEP_DAYS = 30  # 自动删除超过多少天的日志文件
# ======================================================

# 低资源占用配置
SCAN_EXISTING_ON_STARTUP = False
MAX_QUEUE_SIZE = 50
PROCESS_INTERVAL = 0.2
MEMORY_CHECK_INTERVAL = 30
MEMORY_THRESHOLD_MB = 100

# 自重启配置
RESTART_DELAY_SECONDS = 3
MAX_RESTARTS = 0  # 0=无限重启

# 开机自启配置
AUTO_START_ON_FIRST_RUN = True
STARTUP_SHORTCUT_NAME = "PNG2JPGMonitor.lnk"

# -------------------------- 日志配置（带自动清理） --------------------------
from logging.handlers import RotatingFileHandler


def clean_old_logs():
    """自动删除超过指定天数的日志文件"""
    log_dir = os.path.dirname(os.path.abspath(__file__))
    cutoff_time = time.time() - (LOG_KEEP_DAYS * 24 * 3600)

    deleted_count = 0
    for file in os.listdir(log_dir):
        if file.startswith("png_to_jpg_monitor") and file.endswith(".log"):
            file_path = os.path.join(log_dir, file)
            try:
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
            except Exception:
                pass

    if deleted_count > 0:
        print(f"已删除 {deleted_count} 个超过 {LOG_KEEP_DAYS} 天的旧日志文件")


# 先清理旧日志
clean_old_logs()

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = RotatingFileHandler(
    "png_to_jpg_monitor.log",
    maxBytes=LOG_MAX_SIZE_MB * 1024 * 1024,
    backupCount=LOG_BACKUP_COUNT,
    encoding="utf-8"
)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# -------------------------- 全局变量 --------------------------
task_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
stop_event = threading.Event()
converted_count = 0
child_process = None
hwnd = None
icon_green = None
icon_red = None


# -------------------------- 工具函数 --------------------------
def set_low_priority():
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        process_handle = kernel32.GetCurrentProcess()
        kernel32.SetPriorityClass(process_handle, 0x00004000)  # BELOW_NORMAL
    except Exception:
        pass


def create_startup_shortcut():
    try:
        import winshell
        startup = winshell.startup()
        shortcut_path = os.path.join(startup, STARTUP_SHORTCUT_NAME)

        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)

        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = sys.executable
            shortcut.arguments = "" if getattr(sys, 'frozen', False) else __file__
            shortcut.working_directory = os.path.dirname(sys.executable) if getattr(sys, 'frozen',
                                                                                    False) else os.path.dirname(
                os.path.abspath(__file__))
            shortcut.description = "PNG转JPG实时监控程序"

        logger.info("✅ 已创建开机启动快捷方式")
        return True
    except Exception as e:
        logger.warning("⚠️ 无法创建开机启动快捷方式：%s", str(e))
        return False


def create_icon(color):
    img = Image.new('RGB', (16, 16), color=(0, 0, 0))
    pixels = img.load()
    for x in range(16):
        for y in range(16):
            dx = x - 8
            dy = y - 8
            if dx * dx + dy * dy <= 7 * 7:
                pixels[x, y] = color
    return img


def save_icon_to_temp(img, filename):
    temp_path = os.path.join(os.environ['TEMP'], filename)
    img.save(temp_path, "BMP")
    return temp_path


def open_log_file():
    log_path = os.path.abspath("png_to_jpg_monitor.log")
    if os.path.exists(log_path):
        subprocess.Popen(["notepad.exe", log_path])


def show_message_box(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1000)


# -------------------------- 自动清理功能 --------------------------
def clean_old_files():
    """清理目标目录中超过指定天数的JPG文件"""
    if not AUTO_CLEAN_ENABLED:
        return

    logger.info("🔍 开始清理超过%d天的旧图片", CLEAN_DAYS)

    total_deleted = 0
    total_size = 0
    cutoff_time = time.time() - (CLEAN_DAYS * 24 * 3600)

    for path_pair in MONITOR_PATHS:
        target_dir = path_pair["target"]

        if not os.path.exists(target_dir):
            continue

        logger.info("📂 正在扫描目录：%s", target_dir)

        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.lower().endswith(".jpg"):
                    file_path = os.path.join(root, file)

                    try:
                        file_mtime = os.path.getmtime(file_path)

                        if file_mtime < cutoff_time:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            total_deleted += 1
                            total_size += file_size
                            logger.debug("🗑️  删除过期图片：%s", file_path)
                    except Exception as e:
                        logger.warning("⚠️ 无法删除图片 %s：%s", file_path, str(e))

    # 清理空目录
    for path_pair in MONITOR_PATHS:
        target_dir = path_pair["target"]
        if os.path.exists(target_dir):
            for root, dirs, files in os.walk(target_dir, topdown=False):
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            logger.debug("🗑️  删除空目录：%s", dir_path)
                    except Exception as e:
                        logger.warning("⚠️ 无法删除空目录 %s：%s", dir_path, str(e))

    # 同时清理旧日志
    clean_old_logs()

    logger.info("✅ 清理完成，共删除 %d 个图片，释放 %.2f MB 空间",
                total_deleted, total_size / (1024 * 1024))


def auto_clean_thread():
    """自动清理线程，每天指定时间运行"""
    if not AUTO_CLEAN_ENABLED:
        return

    logger.info("⏰ 自动清理功能已启用，每天%d点清理超过%d天的图片", CLEAN_HOUR, CLEAN_DAYS)
    logger.info("⏰ 日志自动清理已启用，保留最近%d天的日志", LOG_KEEP_DAYS)

    if CLEAN_ON_STARTUP:
        try:
            clean_old_files()
        except Exception as e:
            logger.error("❌ 启动时清理失败：%s", str(e))

    while not stop_event.is_set():
        try:
            now = time.localtime()

            next_run = time.mktime((
                now.tm_year, now.tm_mon, now.tm_mday,
                CLEAN_HOUR, 0, 0,
                now.tm_wday, now.tm_yday, now.tm_isdst
            ))

            if next_run < time.time():
                next_run += 24 * 3600

            wait_time = next_run - time.time()
            logger.info("⏰ 下次自动清理时间：%s", time.ctime(next_run))

            while wait_time > 0 and not stop_event.is_set():
                sleep_time = min(wait_time, 60)
                time.sleep(sleep_time)
                wait_time -= sleep_time

            if not stop_event.is_set():
                clean_old_files()

        except Exception as e:
            logger.error("❌ 自动清理线程出错：%s", str(e))
            time.sleep(3600)


# -------------------------- 内存监控 --------------------------
def memory_monitor():
    try:
        import psutil
        process = psutil.Process(os.getpid())

        while not stop_event.is_set():
            try:
                memory_usage = process.memory_info().rss / (1024 * 1024)
                if memory_usage > MEMORY_THRESHOLD_MB:
                    gc.collect()
                time.sleep(MEMORY_CHECK_INTERVAL)
            except Exception:
                time.sleep(MEMORY_CHECK_INTERVAL)
    except ImportError:
        pass


# -------------------------- 转换函数 --------------------------
def convert_png_to_jpg(source_png_path, source_root, target_root):
    global converted_count
    try:
        if not os.path.exists(source_png_path):
            return

        rel_path = os.path.relpath(source_png_path, source_root)
        rel_jpg_path = os.path.splitext(rel_path)[0] + ".jpg"
        target_jpg_path = os.path.join(target_root, rel_jpg_path)

        if os.path.exists(target_jpg_path):
            return

        target_dir = os.path.dirname(target_jpg_path)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # 等待文件写入完成
        start_time = time.time()
        while time.time() - start_time < 5:
            try:
                os.rename(source_png_path, source_png_path)
                break
            except (OSError, IOError, PermissionError):
                time.sleep(0.5)
        else:
            return

        source_size = os.path.getsize(source_png_path) / 1024  # KB

        with Image.open(source_png_path) as img:
            if img.mode == "L":
                img.save(
                    target_jpg_path,
                    "JPEG",
                    quality=JPG_QUALITY,
                    subsampling=CHROMA_SUBSAMPLING,
                    optimize=OPTIMIZE,
                    progressive=PROGRESSIVE,
                    dct_method="INTEGER_FAST"
                )
            else:
                if img.mode in ("RGBA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "RGBA":
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(
                    target_jpg_path,
                    "JPEG",
                    quality=JPG_QUALITY,
                    subsampling=CHROMA_SUBSAMPLING,
                    optimize=OPTIMIZE,
                    progressive=PROGRESSIVE
                )

        del img
        gc.collect()

        target_size = os.path.getsize(target_jpg_path) / 1024  # KB
        ratio = source_size / target_size

        converted_count += 1
        logger.info("✅ 转换成功：%.1fK → %.1fK (压缩比%.1f:1) %s",
                    source_size, target_size, ratio, source_png_path)

    except Exception as e:
        logger.error("❌ 转换失败 %s：%s", source_png_path, str(e))
    finally:
        if 'img' in locals():
            del img
        gc.collect()


# -------------------------- 工作线程 --------------------------
def worker_thread():
    while not stop_event.is_set():
        try:
            source_png_path, source_root, target_root = task_queue.get(timeout=1)
            convert_png_to_jpg(source_png_path, source_root, target_root)
            task_queue.task_done()
            time.sleep(PROCESS_INTERVAL)
        except queue.Empty:
            continue
        except Exception as e:
            logger.error("❌ 工作线程出错：%s", str(e))
            time.sleep(1)


# -------------------------- 文件事件处理器 --------------------------
class LowResourceHandler(FileSystemEventHandler):
    def __init__(self, source_root, target_root):
        self.source_root = source_root
        self.target_root = target_root
        os.makedirs(self.target_root, exist_ok=True)
        logger.info("✅ 已启动监控：%s → %s", self.source_root, self.target_root)

    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".png"):
            return

        try:
            task_queue.put_nowait((event.src_path, self.source_root, self.target_root))
        except queue.Full:
            logger.warning("⚠️ 任务队列已满，跳过文件：%s", event.src_path)


# -------------------------- 主程序逻辑（子进程运行） --------------------------
def main_program():
    set_low_priority()

    # 启动内存监控
    memory_thread = threading.Thread(target=memory_monitor, daemon=True)
    memory_thread.start()

    # 启动自动清理线程
    clean_thread = threading.Thread(target=auto_clean_thread, daemon=True)
    clean_thread.start()

    # 启动工作线程
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()

    # 启动文件监控
    observers = []
    for path_pair in MONITOR_PATHS:
        source = path_pair["source"]
        target = path_pair["target"]

        if not os.path.exists(source):
            logger.warning("⚠️ 源目录不存在，跳过监控：%s", source)
            continue

        event_handler = LowResourceHandler(source, target)
        observer = Observer()
        observer.schedule(event_handler, path=source, recursive=True)
        observer.start()
        observers.append(observer)

    if not observers:
        logger.error("❌ 没有可监控的目录，程序退出")
        show_message_box("错误", "没有找到可监控的目录：\nD:\\MMCD_结果\nE:\\MMCD_结果\n\n程序将退出。")
        return

    logger.info("🚀 PNG转JPG监控程序已启动")
    logger.info("⚙️ 当前压缩参数：质量=%d，子采样=%d", JPG_QUALITY, CHROMA_SUBSAMPLING)
    logger.info("⚙️ 图片自动清理：%s，保留%d天，每天%d点运行",
                "已启用" if AUTO_CLEAN_ENABLED else "已禁用", CLEAN_DAYS, CLEAN_HOUR)
    logger.info("⚙️ 日志自动清理：保留最近%d天，单个文件最大%dMB",
                LOG_KEEP_DAYS, LOG_MAX_SIZE_MB)

    # 主循环
    try:
        while not stop_event.is_set():
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
        logger.info("🛑 程序已停止")


# -------------------------- 系统托盘功能 --------------------------
def create_tray_icon():
    global hwnd, icon_green, icon_red

    green_img = create_icon((0, 255, 0))
    red_img = create_icon((255, 0, 0))
    green_path = save_icon_to_temp(green_img, "png2jpg_green.bmp")
    red_path = save_icon_to_temp(red_img, "png2jpg_red.bmp")

    icon_green = win32gui.LoadImage(0, green_path, win32con.IMAGE_BITMAP, 16, 16, win32con.LR_LOADFROMFILE)
    icon_red = win32gui.LoadImage(0, red_path, win32con.IMAGE_BITMAP, 16, 16, win32con.LR_LOADFROMFILE)

    wc = win32gui.WNDCLASS()
    wc.hInstance = win32api.GetModuleHandle(None)
    wc.lpszClassName = "PNG2JPGMonitorTray"
    wc.lpfnWndProc = wnd_proc
    class_atom = win32gui.RegisterClass(wc)

    hwnd = win32gui.CreateWindow(
        class_atom,
        "PNG2JPGMonitor",
        0,
        0, 0, 0, 0,
        0, 0, wc.hInstance, None
    )

    nid = (
        hwnd,
        0,
        win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
        win32con.WM_USER + 1,
        icon_green,
        "PNG转JPG监控 (运行中)"
    )
    win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

    nid_info = (
        hwnd,
        0,
        win32gui.NIF_INFO,
        0,
        0,
        "",
        "PNG转JPG监控程序已启动",
        2000,
        "日志保留{}天，图片保留{}天".format(LOG_KEEP_DAYS, CLEAN_DAYS)
    )
    win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid_info)

    win32gui.PumpMessages()


def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_USER + 1:
        if lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()

            win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_GRAYED, 1,
                                "已转换: {} 个".format(converted_count))
            win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_GRAYED, 5, "压缩质量: Q={}".format(JPG_QUALITY))
            win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_GRAYED, 6, "图片保留: {}天".format(CLEAN_DAYS))
            win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_GRAYED, 8,
                                "日志保留: {}天".format(LOG_KEEP_DAYS))
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 7, "立即清理旧文件")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 2, "查看日志")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 3, "重启服务")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 4, "退出程序")

            pos = win32gui.GetCursorPos()

            win32gui.SetForegroundWindow(hwnd)
            win32gui.TrackPopupMenu(
                menu,
                win32con.TPM_BOTTOMALIGN | win32con.TPM_LEFTALIGN,
                pos[0], pos[1],
                0, hwnd, None
            )
            win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)

        elif lparam == win32con.WM_LBUTTONDBLCLK:
            open_log_file()

    elif msg == win32con.WM_COMMAND:
        menu_id = win32api.LOWORD(wparam)
        if menu_id == 2:
            open_log_file()
        elif menu_id == 3:
            global child_process
            if child_process and child_process.poll() is None:
                child_process.terminate()
                child_process.wait()
            logger.info("🔄 用户手动重启服务")
        elif menu_id == 4:
            stop_event.set()
            if child_process and child_process.poll() is None:
                child_process.terminate()
                child_process.wait()

            nid = (hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)

            win32gui.DestroyWindow(hwnd)

            logger.info("👋 用户退出程序")
            sys.exit(0)
        elif menu_id == 7:
            logger.info("🔄 用户手动触发清理")
            threading.Thread(target=clean_old_files, daemon=True).start()

    elif msg == win32con.WM_DESTROY:
        win32gui.PostQuitMessage(0)

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)


# -------------------------- 父进程监控逻辑 --------------------------
def run_monitor():
    global child_process
    restart_count = 0

    logger.info("👀 监控进程已启动，PID: %d", os.getpid())

    if AUTO_START_ON_FIRST_RUN:
        create_startup_shortcut()

    def monitor_thread():
        nonlocal restart_count
        while True:
            if MAX_RESTARTS > 0 and restart_count >= MAX_RESTARTS:
                logger.error("❌ 达到最大重启次数，程序退出")
                break

            logger.info("▶️ 启动工作进程，第%d次重启", restart_count)

            if getattr(sys, 'frozen', False):
                child_process = subprocess.Popen([sys.executable, "--child"])
            else:
                child_process = subprocess.Popen([sys.executable, __file__, "--child"])

            child_process.wait()
            exit_code = child_process.returncode

            if exit_code == 0:
                logger.info("✅ 程序正常退出")
                win32gui.PostMessage(hwnd, win32con.WM_COMMAND, win32api.MAKELONG(4, 0), 0)
                break

            logger.warning("⚠️ 工作进程异常退出，退出码: %d，%d秒后重启", exit_code, RESTART_DELAY_SECONDS)

            time.sleep(RESTART_DELAY_SECONDS)
            restart_count += 1

    threading.Thread(target=monitor_thread, daemon=True).start()

    create_tray_icon()


# -------------------------- 主入口 --------------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        main_program()
    else:
        run_monitor()