# -*- coding: utf-8 -*-
import sys
import socket
import time
import win32gui
import win32process
import psutil
import ctypes
from pynput.keyboard import Controller, Key
import threading
import json
import traceback

# 初始化键盘控制器
keyboard = Controller()

# 键映射表
KEY_MAP = {
    'f1': Key.f1,
    'f2': Key.f2,
    'f3': Key.f3,
    'f4': Key.f4,
    'f5': Key.f5,
    'f6': Key.f6,
    'f7': Key.f7,
    'f8': Key.f8,
    'f9': Key.f9,
    'f10': Key.f10,
    'f11': Key.f11,
    'f12': Key.f12,
    'shift': Key.shift,
    'ctrl': Key.ctrl,
    'alt': Key.alt,
    'esc': Key.esc,
    'enter': Key.enter,
    'space': Key.space,
    'backspace': Key.backspace,
    'tab': Key.tab,
    'caps_lock': Key.caps_lock,
    'num_lock': Key.num_lock,
    'scroll_lock': Key.scroll_lock,
    'insert': Key.insert,
    'delete': Key.delete,
    'home': Key.home,
    'end': Key.end,
    'page_up': Key.page_up,
    'page_down': Key.page_down,
    'up': Key.up,
    'down': Key.down,
    'left': Key.left,
    'right': Key.right,
    'menu': Key.menu,
    'print_screen': Key.print_screen,
    'pause': Key.pause,
}

class ReloadModsConfig(object):
    lock = threading.Lock()
    mods_change = False
    # 要监听的程序名称
    target_process = None
    # 要按下的键 (list of Key or single-char strings)
    press_keys = [Key.f10]


def send_key_combination(press_keys):
    try:
        # press all
        for key in press_keys:
            keyboard.press(key)
        time.sleep(0.08)
        # release all in reverse order may be safer for combos
        for key in reversed(press_keys):
            keyboard.release(key)
    except Exception as e:
        print(f"[send_key_combination] error: {e}")
        traceback.print_exc()


def active_window_process_is_target_process():
    """判断当前聚焦窗口是否为指定程序。异常时返回 False"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return False
        try:
            process = psutil.Process(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

        if ReloadModsConfig.target_process is not None:
            # 进程名比较，忽略大小写
            try:
                return process.name().lower() == ReloadModsConfig.target_process.lower()
            except Exception:
                return False
        else:
            return False
    except Exception as e:
        # 捕获 win32/psutil 以外的异常，防止崩溃
        print(f"[active_window_process_is_target_process] exception: {e}")
        traceback.print_exc()
        return False


class ReloadModsThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.daemon = True

    def run(self):
        while self.running:
            try:
                with ReloadModsConfig.lock:
                    if ReloadModsConfig.mods_change and active_window_process_is_target_process():
                        send_key_combination(ReloadModsConfig.press_keys)
                        # 发送一次后清空标志
                        ReloadModsConfig.mods_change = False
            except Exception as e:
                print(f"[ReloadModsThread] exception in loop: {e}")
                traceback.print_exc()
            time.sleep(0.5)

    def stop(self):
        self.running = False


def is_admin():
    """检查当前进程是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def parse_press_keys_string(s: str):
    """
    将字符串如 "F10 ctrl" 或 "f10" 或 "a" 解析为 pynput Key 或字符列表
    返回 list
    """
    result = []
    for key in s.split():
        if not key:
            continue
        k = key.lower()
        if k in KEY_MAP:
            result.append(KEY_MAP[k])
        elif len(key) == 1 and key.isprintable():
            result.append(key)
        else:
            # 无法识别，忽略
            print(f"[parse_press_keys_string] unknown key: {key}")
    return result


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("usage: reload_mods.py <host> <port>")
        sys.exit(2)

    host = sys.argv[1]
    try:
        port = int(sys.argv[2])
    except Exception:
        print("port must be integer")
        sys.exit(2)

    thread = ReloadModsThread()
    thread.start()

    client_socket = None
    file_obj = None
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.connect((host, port))
        # makefile binary mode for readline
        file_obj = client_socket.makefile('rwb', newline=b'\n')

        while True:
            # 阻塞读取一行
            line = file_obj.readline()
            if not line:
                # 对端关闭或 EOF -> 退出循环
                print("[main] remote closed connection or EOF")
                break

            try:
                message = line.decode('utf-8', errors='ignore').strip()
            except Exception:
                message = line.decode('utf-8', 'ignore').strip()

            if not message:
                # 空行，继续等待
                continue

            if message == "exit":
                print("[main] received exit command")
                break

            if message.startswith("reload"):
                payload = message[len("reload"):].strip()
                try:
                    if payload:
                        data = json.loads(payload)
                    else:
                        print("[main] reload command missing payload")
                        continue
                except Exception as e:
                    print(f"[main] failed to parse JSON payload: {e} payload={payload}")
                    continue

                # 解析并校验字段
                try:
                    target_proc = data.get("target_process")
                    press_keys_raw = data.get("press_keys", "")

                    with ReloadModsConfig.lock:
                        if isinstance(target_proc, str):
                            ReloadModsConfig.target_process = target_proc
                        else:
                            # ignore invalid
                            ReloadModsConfig.target_process = None

                        if isinstance(press_keys_raw, str):
                            parsed = parse_press_keys_string(press_keys_raw)
                            if parsed:
                                ReloadModsConfig.press_keys = parsed
                        # 标记需要重载
                        ReloadModsConfig.mods_change = True
                except Exception as e:
                    print(f"[main] error applying reload config: {e}")
                    traceback.print_exc()
            else:
                print(f"[main] unknown message: {message}")

    except KeyboardInterrupt:
        print("[main] interrupted by user")
    except Exception as e:
        print(f"[main] exception: {e}")
        traceback.print_exc()
    finally:
        # 清理
        try:
            if file_obj:
                try:
                    file_obj.close()
                except Exception:
                    pass
            if client_socket:
                try:
                    client_socket.close()
                except Exception:
                    pass
        except Exception:
            pass

        # 停止线程并等待
        try:
            thread.stop()
            thread.join(timeout=2.0)
        except Exception:
            pass

    print("[main] exiting reload_mods process")