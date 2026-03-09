import pyautogui
import ctypes
import sys
import threading
import time
import psutil  # 用于检测系统进程
from pynput import keyboard, mouse

# ===================== 自定义配置区 =====================
TRIGGER_KEY = mouse.Button.x1  # 鼠标侧键Mouse4触发缩放
DELAY = 0.2  # 防重复触发延迟（秒）
MAGNIFY_CHECK_INTERVAL = 1  # 检测放大镜进程的间隔（秒）
# ========================================================

# 状态变量
zoom_in_next = True
last_trigger_time = 0
magnify_check_thread = None  # 放大镜检测线程
is_running = True  # 程序运行状态标记

# ---------------------- 窗口最小化核心代码 ----------------------
def minimize_console_window():
    """将程序窗口最小化到任务栏（保留任务栏图标）"""
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            # SW_MINIMIZE = 6：最小化窗口（保留任务栏图标），区别于SW_HIDE(0)完全隐藏
            ctypes.windll.user32.ShowWindow(hwnd, 6)

# ---------------------- 放大镜进程检测 ----------------------
def check_magnify_process():
    """定时检测放大镜进程，若关闭则退出程序"""
    global is_running
    while is_running:
        # 检测magnify.exe是否在运行
        magnify_running = any(
            proc.name().lower() == "magnify.exe" 
            for proc in psutil.process_iter(['name'])
        )
        # 若放大镜已关闭，停止程序
        if not magnify_running:
            print("检测到Windows放大镜已关闭，程序即将退出...")
            # 停止所有监听器并退出
            is_running = False
            # 终止键鼠监听器（通过全局状态标记）
            mouse_listener.stop()
            keyboard_listener.stop()
            sys.exit(0)
        time.sleep(MAGNIFY_CHECK_INTERVAL)

# ---------------------- 缩放功能核心代码 ----------------------
def trigger_zoom():
    """触发缩放操作（Win+加号 或 Win+减号）"""
    global zoom_in_next, last_trigger_time
    current_time = time.time()
    
    # 防重复触发
    if current_time - last_trigger_time < DELAY:
        return
    last_trigger_time = current_time

    try:
        if zoom_in_next:
            pyautogui.keyDown('win')
            pyautogui.press('+')
            pyautogui.keyUp('win')
        else:
            pyautogui.keyDown('win')
            pyautogui.press('-')
            pyautogui.keyUp('win')
        zoom_in_next = not zoom_in_next
    except Exception as e:
        print(f"缩放操作出错：{e}")

# ---------------------- 监听与退出逻辑 ----------------------
def on_key_press(key):
    """键盘监听（ESC手动退出）"""
    global is_running
    try:
        if key == keyboard.Key.esc:
            is_running = False
            mouse_listener.stop()
            return False  # 停止键盘监听器
    except Exception as e:
        pass

def on_mouse_click(x, y, button, pressed):
    """鼠标侧键触发缩放"""
    if pressed and button == TRIGGER_KEY and is_running:
        trigger_zoom()

if __name__ == "__main__":
    # 1. 安装psutil提示（若未安装）
    try:
        import psutil
    except ImportError:
        print("缺少psutil库，请先执行：pip install psutil")
        input("按回车键退出...")
        sys.exit(1)

    # 2. 窗口最小化（保留任务栏图标）
    minimize_console_window()

    # 3. 启动键鼠监听器
    mouse_listener = mouse.Listener(on_click=on_mouse_click)
    keyboard_listener = keyboard.Listener(on_press=on_key_press)
    mouse_listener.start()
    keyboard_listener.start()

    # 4. 启动放大镜进程检测线程（后台运行）
    magnify_check_thread = threading.Thread(target=check_magnify_process, daemon=True)
    magnify_check_thread.start()

    print("程序已最小化到任务栏！")
    print("1. 点击鼠标侧键(Mouse4)触发Win+±缩放")
    print("2. 关闭Windows放大镜后程序会自动退出")
    print("3. 按ESC键可手动退出程序")

    # 5. 保持主线程运行
    keyboard_listener.join()
    is_running = False
    mouse_listener.stop()
    print("程序已退出")
