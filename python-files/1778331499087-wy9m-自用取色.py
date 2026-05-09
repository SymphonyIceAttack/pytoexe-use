# -*- coding: utf-8 -*-
"""
回合制游戏自动化宏 - 支持随机延迟 + 停止条件（区域匹配）
可定义步骤序列，支持区域截图自动裁剪模板，后台按键，配置导入导出。
增加停止条件：可自定义搜索区域，在该区域内任意位置匹配到指定图标即停止宏。
"""

import sys
import os
import ctypes
import subprocess
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import json
import traceback

# ================== 自动提权 ==================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    try:
        script = sys.executable
        params = ' '.join(sys.argv)
        if getattr(sys, 'frozen', False) and '--elevated' not in sys.argv:
            params += ' --elevated'
        ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)
        return True
    except:
        return False

if not is_admin():
    if '--elevated' in sys.argv:
        print("需要管理员权限才能正常运行，请以管理员身份运行本程序。")
        input("按 Enter 键退出...")
        sys.exit(1)
    else:
        run_as_admin()
        sys.exit(0)
# =============================================

# ================== 自动安装依赖 ==================
REQUIRED_PACKAGES = [
    'opencv-python',
    'psutil',
    'pywin32',
    'Pillow',
    'numpy',
]

def install_and_import(packages):
    if isinstance(packages, str):
        packages = [packages]
    imported = {}
    for package in packages:
        try:
            if package == 'opencv-python':
                imported['cv2'] = __import__('cv2')
                print(f"✓ cv2 已安装")
            elif package == 'pywin32':
                imported['win32api'] = __import__('win32api')
                imported['win32gui'] = __import__('win32gui')
                imported['win32con'] = __import__('win32con')
                imported['win32process'] = __import__('win32process')
                print(f"✓ pywin32 已安装")
            elif package == 'Pillow':
                imported['PIL'] = __import__('PIL')
                print(f"✓ Pillow 已安装")
            else:
                imported[package] = __import__(package)
                print(f"✓ {package} 已安装")
        except ImportError:
            print(f"✗ {package} 未安装，正在自动安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            if package == 'opencv-python':
                imported['cv2'] = __import__('cv2')
            elif package == 'pywin32':
                imported['win32api'] = __import__('win32api')
                imported['win32gui'] = __import__('win32gui')
                imported['win32con'] = __import__('win32con')
                imported['win32process'] = __import__('win32process')
            elif package == 'Pillow':
                imported['PIL'] = __import__('PIL')
            else:
                imported[package] = __import__(package)
            print(f"✓ {package} 安装成功")
    return imported

print("正在检查并安装所需依赖...")
imports = install_and_import(REQUIRED_PACKAGES)

cv2 = imports.get('cv2')
psutil = imports.get('psutil')
win32api = imports.get('win32api')
win32gui = imports.get('win32gui')
win32con = imports.get('win32con')
win32process = imports.get('win32process')
PIL = imports.get('PIL')
numpy = imports.get('numpy')

from PIL import Image, ImageTk, ImageGrab
import numpy as np
# =============================================

# ================== 配置 ==================
CONFIG_FILE = "macro_config.json"
DEFAULT_INTERVAL = 1.0
DEFAULT_INTERVAL_RANDOM_ENABLE = False
DEFAULT_INTERVAL_RANDOM_MIN = 0.5
DEFAULT_INTERVAL_RANDOM_MAX = 1.5
DEFAULT_GLOBAL_TIMEOUT = 0
DEFAULT_ONCE_PER_ROUND = True
DEFAULT_KEY_DELAY_ENABLE = False
DEFAULT_KEY_DELAY_MIN = 0.1
DEFAULT_KEY_DELAY_MAX = 0.3
# 停止条件默认值
DEFAULT_STOP_ENABLE = False
DEFAULT_STOP_TEMPLATE_PATH = ""
DEFAULT_STOP_REGION = [0, 0, 0, 0]   # [x, y, w, h]
DEFAULT_STOP_THRESHOLD = 0.7

TARGET_PROCESS_NAME = "NRC-Win64-Shipping.exe"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "macro_templates")
os.makedirs(TEMPLATE_DIR, exist_ok=True)

KEY_MAP = {
    '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75, 'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79,
    'F11': 0x7A, 'F12': 0x7B,
    'Space': 0x20, 'Enter': 0x0D, 'Tab': 0x09, 'Escape': 0x1B,
    'Up': 0x26, 'Down': 0x28, 'Left': 0x25, 'Right': 0x27,
    'Ctrl': 0x11, 'Alt': 0x12, 'Shift': 0x10,
}
def get_key_code(key_str):
    key_str = key_str.strip()
    if key_str in KEY_MAP:
        return KEY_MAP[key_str]
    try:
        return int(key_str)
    except:
        return None

def random_delay(min_sec, max_sec, log_func=None):
    if min_sec <= 0 or max_sec <= 0 or min_sec > max_sec:
        return
    delay = random.uniform(min_sec, max_sec)
    if log_func:
        log_func(f"随机延迟 {delay:.2f} 秒")
    time.sleep(delay)

# ================== 游戏窗口操作 ==================
def capture_window_client_screen(hwnd):
    try:
        window_rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = window_rect
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return None
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        client_point = win32gui.ClientToScreen(hwnd, (0, 0))
        offset_x = client_point[0] - left
        offset_y = client_point[1] - top
        client_rect = win32gui.GetClientRect(hwnd)
        client_w = client_rect[2]
        client_h = client_rect[3]
        img = img[offset_y:offset_y+client_h, offset_x:offset_x+client_w]
        return img
    except Exception as e:
        print(f"截图失败: {e}")
        return None

def capture_window_region_screen(hwnd, region):
    img = capture_window_client_screen(hwnd)
    if img is None:
        return None
    x, y, w, h = region
    if w <= 0 or h <= 0:
        return None  # 无效区域
    if x < 0 or y < 0 or x+w > img.shape[1] or y+h > img.shape[0]:
        # 区域超出边界，返回整个图像
        return img
    return img[y:y+h, x:x+w]

def match_template_in_region(img, template, region, threshold):
    """
    在图像的指定区域中匹配模板（全区域扫描，返回最佳匹配值）
    region: [x, y, w, h] 如果 w<=0 或 h<=0 则使用全图
    """
    if img is None or template is None:
        return False, 0
    # 截取搜索区域
    if region[2] > 0 and region[3] > 0:
        x, y, w, h = region
        if x < 0 or y < 0 or x+w > img.shape[1] or y+h > img.shape[0]:
            roi = img
        else:
            roi = img[y:y+h, x:x+w]
    else:
        roi = img
    if roi.shape[0] < template.shape[0] or roi.shape[1] < template.shape[1]:
        return False, 0
    result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= threshold, max_val

def find_target_window(process_name, window_title):
    if window_title:
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd and win32gui.IsWindowVisible(hwnd):
            return hwnd
    target_pid = None
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == process_name:
                target_pid = proc.info['pid']
                break
        except:
            continue
    if not target_pid:
        return None
    def enum_callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pid == target_pid:
                    hwnd_list.append(hwnd)
            except:
                pass
        return True
    hwnd_list = []
    win32gui.EnumWindows(enum_callback, hwnd_list)
    return hwnd_list[0] if hwnd_list else None

def send_key(hwnd, key_str, log_func, key_delay_enable=False, key_delay_min=0.1, key_delay_max=0.3):
    key_code = get_key_code(key_str)
    if key_code is None:
        log_func(f"无效的按键: {key_str}", is_error=True)
        return False
    try:
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
        time.sleep(0.05)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)
        if key_delay_enable:
            random_delay(key_delay_min, key_delay_max, log_func)
        return True
    except Exception as e:
        log_func(f"发送按键失败: {e}", is_error=True)
        return False

# ================== 步骤数据结构 ==================
class Step:
    def __init__(self, index):
        self.index = index
        self.name = f"步骤{index+1}"
        self.enabled = True
        self.region = [0,0,0,0]      # [x,y,w,h]
        self.template_path = ""
        self.threshold = 0.7
        self.on_match_action = {"type": "key", "value": "1"}   # "key", "delay", "random_delay", "goto", "none"
        self.on_match_delay = 0.0
        self.on_match_random_min = 0.0
        self.on_match_random_max = 0.0
        self.on_match_goto = -1
        self.on_mismatch_action = {"type": "none"}
        self.on_mismatch_delay = 0.0
        self.on_mismatch_random_min = 0.0
        self.on_mismatch_random_max = 0.0
        self.on_mismatch_goto = -1
        self.continue_after_match = True

    def to_dict(self):
        return {
            "name": self.name,
            "enabled": self.enabled,
            "region": self.region,
            "template_path": self.template_path,
            "threshold": self.threshold,
            "on_match_action": self.on_match_action,
            "on_match_delay": self.on_match_delay,
            "on_match_random_min": self.on_match_random_min,
            "on_match_random_max": self.on_match_random_max,
            "on_match_goto": self.on_match_goto,
            "on_mismatch_action": self.on_mismatch_action,
            "on_mismatch_delay": self.on_mismatch_delay,
            "on_mismatch_random_min": self.on_mismatch_random_min,
            "on_mismatch_random_max": self.on_mismatch_random_max,
            "on_mismatch_goto": self.on_mismatch_goto,
            "continue_after_match": self.continue_after_match
        }

    def from_dict(self, data, idx):
        self.index = idx
        self.name = data.get("name", f"步骤{idx+1}")
        self.enabled = data.get("enabled", True)
        self.region = data.get("region", [0,0,0,0])
        self.template_path = data.get("template_path", "")
        self.threshold = data.get("threshold", 0.7)
        self.on_match_action = data.get("on_match_action", {"type": "key", "value": "1"})
        self.on_match_delay = data.get("on_match_delay", 0.0)
        self.on_match_random_min = data.get("on_match_random_min", 0.0)
        self.on_match_random_max = data.get("on_match_random_max", 0.0)
        self.on_match_goto = data.get("on_match_goto", -1)
        self.on_mismatch_action = data.get("on_mismatch_action", {"type": "none"})
        self.on_mismatch_delay = data.get("on_mismatch_delay", 0.0)
        self.on_mismatch_random_min = data.get("on_mismatch_random_min", 0.0)
        self.on_mismatch_random_max = data.get("on_mismatch_random_max", 0.0)
        self.on_mismatch_goto = data.get("on_mismatch_goto", -1)
        self.continue_after_match = data.get("continue_after_match", True)

# ================== 步骤编辑窗口（同上，未修改）==================
class StepEditDialog:
    def __init__(self, parent, step, index, template_dir, on_save):
        self.parent = parent
        self.step = step
        self.index = index
        self.template_dir = template_dir
        self.on_save = on_save
        self.window = tk.Toplevel(parent)
        self.window.title(f"编辑步骤 {index+1}")
        self.window.geometry("750x700")
        self.window.resizable(False, False)
        self.create_widgets()
        self.load_data()
        self.window.grab_set()

    def create_widgets(self):
        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="步骤名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="启用该步骤", variable=self.enabled_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5)

        region_frame = ttk.LabelFrame(frame, text="检测区域", padding=5)
        region_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        self.region_label = ttk.Label(region_frame, text="未设置", foreground="blue")
        self.region_label.pack(anchor=tk.W)
        ttk.Button(region_frame, text="从游戏窗口选择区域", command=self.select_region).pack(anchor=tk.W, pady=2)

        ttk.Label(frame, text="匹配阈值 (0.5~0.95):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.threshold_var = tk.DoubleVar(value=0.7)
        scale = ttk.Scale(frame, from_=0.5, to=0.95, orient=tk.HORIZONTAL, variable=self.threshold_var, length=150)
        scale.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(frame, textvariable=self.threshold_var, width=5).grid(row=3, column=2, sticky=tk.W)

        match_frame = ttk.LabelFrame(frame, text="匹配成功时执行", padding=5)
        match_frame.grid(row=4, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        self.match_action_type = tk.StringVar(value="key")
        ttk.Radiobutton(match_frame, text="按下按键", variable=self.match_action_type, value="key").grid(row=0, column=0, padx=5)
        self.match_key_var = tk.StringVar(value="1")
        ttk.Entry(match_frame, textvariable=self.match_key_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(match_frame, text="固定延迟 (秒)", variable=self.match_action_type, value="delay").grid(row=1, column=0, padx=5)
        self.match_delay_var = tk.DoubleVar(value=0.5)
        ttk.Entry(match_frame, textvariable=self.match_delay_var, width=10).grid(row=1, column=1, padx=5)
        ttk.Radiobutton(match_frame, text="随机延迟 (秒)", variable=self.match_action_type, value="random_delay").grid(row=2, column=0, padx=5)
        rand_frame = ttk.Frame(match_frame)
        rand_frame.grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(rand_frame, text="最小").pack(side=tk.LEFT)
        self.match_random_min_var = tk.DoubleVar(value=0.3)
        ttk.Entry(rand_frame, textvariable=self.match_random_min_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(rand_frame, text="最大").pack(side=tk.LEFT)
        self.match_random_max_var = tk.DoubleVar(value=0.8)
        ttk.Entry(rand_frame, textvariable=self.match_random_max_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(match_frame, text="跳转到步骤", variable=self.match_action_type, value="goto").grid(row=3, column=0, padx=5)
        self.match_goto_var = tk.IntVar(value=-1)
        ttk.Spinbox(match_frame, from_=-1, to=100, textvariable=self.match_goto_var, width=10).grid(row=3, column=1, padx=5)
        ttk.Radiobutton(match_frame, text="无动作", variable=self.match_action_type, value="none").grid(row=4, column=0, padx=5)

        mismatch_frame = ttk.LabelFrame(frame, text="匹配失败时执行", padding=5)
        mismatch_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        self.mismatch_action_type = tk.StringVar(value="none")
        ttk.Radiobutton(mismatch_frame, text="按下按键", variable=self.mismatch_action_type, value="key").grid(row=0, column=0, padx=5)
        self.mismatch_key_var = tk.StringVar(value="")
        ttk.Entry(mismatch_frame, textvariable=self.mismatch_key_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(mismatch_frame, text="固定延迟 (秒)", variable=self.mismatch_action_type, value="delay").grid(row=1, column=0, padx=5)
        self.mismatch_delay_var = tk.DoubleVar(value=0.5)
        ttk.Entry(mismatch_frame, textvariable=self.mismatch_delay_var, width=10).grid(row=1, column=1, padx=5)
        ttk.Radiobutton(mismatch_frame, text="随机延迟 (秒)", variable=self.mismatch_action_type, value="random_delay").grid(row=2, column=0, padx=5)
        rand_frame2 = ttk.Frame(mismatch_frame)
        rand_frame2.grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(rand_frame2, text="最小").pack(side=tk.LEFT)
        self.mismatch_random_min_var = tk.DoubleVar(value=0.3)
        ttk.Entry(rand_frame2, textvariable=self.mismatch_random_min_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(rand_frame2, text="最大").pack(side=tk.LEFT)
        self.mismatch_random_max_var = tk.DoubleVar(value=0.8)
        ttk.Entry(rand_frame2, textvariable=self.mismatch_random_max_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(mismatch_frame, text="跳转到步骤", variable=self.mismatch_action_type, value="goto").grid(row=3, column=0, padx=5)
        self.mismatch_goto_var = tk.IntVar(value=-1)
        ttk.Spinbox(mismatch_frame, from_=-1, to=100, textvariable=self.mismatch_goto_var, width=10).grid(row=3, column=1, padx=5)
        ttk.Radiobutton(mismatch_frame, text="无动作", variable=self.mismatch_action_type, value="none").grid(row=4, column=0, padx=5)

        self.continue_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="执行动作后继续扫描后续步骤（若不勾选，则本轮停止扫描）", variable=self.continue_var).grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        self.name_var.set(self.step.name)
        self.enabled_var.set(self.step.enabled)
        self.threshold_var.set(self.step.threshold)
        if self.step.region[2] > 0:
            self.region_label.config(text=f"({self.step.region[0]}, {self.step.region[1]}) {self.step.region[2]}x{self.step.region[3]}")
        self.match_action_type.set(self.step.on_match_action.get("type", "key"))
        if self.match_action_type.get() == "key":
            self.match_key_var.set(self.step.on_match_action.get("value", "1"))
        elif self.match_action_type.get() == "delay":
            self.match_delay_var.set(self.step.on_match_delay)
        elif self.match_action_type.get() == "random_delay":
            self.match_random_min_var.set(self.step.on_match_random_min)
            self.match_random_max_var.set(self.step.on_match_random_max)
        elif self.match_action_type.get() == "goto":
            self.match_goto_var.set(self.step.on_match_goto if self.step.on_match_goto != -1 else -1)
        self.mismatch_action_type.set(self.step.on_mismatch_action.get("type", "none"))
        if self.mismatch_action_type.get() == "key":
            self.mismatch_key_var.set(self.step.on_mismatch_action.get("value", ""))
        elif self.mismatch_action_type.get() == "delay":
            self.mismatch_delay_var.set(self.step.on_mismatch_delay)
        elif self.mismatch_action_type.get() == "random_delay":
            self.mismatch_random_min_var.set(self.step.on_mismatch_random_min)
            self.mismatch_random_max_var.set(self.step.on_mismatch_random_max)
        elif self.mismatch_action_type.get() == "goto":
            self.mismatch_goto_var.set(self.step.on_mismatch_goto if self.step.on_mismatch_goto != -1 else -1)
        self.continue_var.set(self.step.continue_after_match)

    def select_region(self):
        proc_name = app.process_name_var.get().strip()
        win_title = app.window_title_var.get().strip()
        hwnd = find_target_window(proc_name, win_title)
        if not hwnd:
            messagebox.showerror("错误", "未找到游戏窗口")
            return
        img_full = capture_window_client_screen(hwnd)
        if img_full is None:
            messagebox.showerror("错误", "截图失败，请确保窗口未最小化")
            return
        selector = RegionSelector(self.window, img_full, f"选择区域 - {self.name_var.get()}")
        region = selector.select()
        if not region:
            return
        x, y, w, h = region
        region_img = img_full[y:y+h, x:x+w]
        if region_img.size == 0:
            messagebox.showerror("错误", "区域无效")
            return
        default_name = f"{self.name_var.get()}_template.png"
        file_path = filedialog.asksaveasfilename(
            title="保存模板图片",
            initialdir=self.template_dir,
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png")]
        )
        if file_path:
            cv2.imwrite(file_path, region_img)
            self.step.region = [x, y, w, h]
            self.step.template_path = file_path
            self.region_label.config(text=f"({x}, {y}) {w}x{h}")
            messagebox.showinfo("成功", "区域和模板已保存")

    def save(self):
        self.step.name = self.name_var.get()
        self.step.enabled = self.enabled_var.get()
        self.step.threshold = self.threshold_var.get()
        self.step.on_match_action = {"type": self.match_action_type.get()}
        if self.match_action_type.get() == "key":
            self.step.on_match_action["value"] = self.match_key_var.get()
        elif self.match_action_type.get() == "delay":
            self.step.on_match_delay = self.match_delay_var.get()
        elif self.match_action_type.get() == "random_delay":
            self.step.on_match_random_min = self.match_random_min_var.get()
            self.step.on_match_random_max = self.match_random_max_var.get()
        elif self.match_action_type.get() == "goto":
            self.step.on_match_goto = self.match_goto_var.get()
        self.step.on_mismatch_action = {"type": self.mismatch_action_type.get()}
        if self.mismatch_action_type.get() == "key":
            self.step.on_mismatch_action["value"] = self.mismatch_key_var.get()
        elif self.mismatch_action_type.get() == "delay":
            self.step.on_mismatch_delay = self.mismatch_delay_var.get()
        elif self.mismatch_action_type.get() == "random_delay":
            self.step.on_mismatch_random_min = self.mismatch_random_min_var.get()
            self.step.on_mismatch_random_max = self.mismatch_random_max_var.get()
        elif self.mismatch_action_type.get() == "goto":
            self.step.on_mismatch_goto = self.mismatch_goto_var.get()
        self.step.continue_after_match = self.continue_var.get()
        self.on_save(self.step)
        self.window.destroy()

class RegionSelector:
    def __init__(self, parent, img_bgr, title):
        self.parent = parent
        self.img = img_bgr
        self.title = title
        self.rect = None
        self.root = None

    def select(self):
        self.root = tk.Toplevel(self.parent)
        self.root.title(self.title)
        img_rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas = tk.Canvas(self.root, width=self.img.shape[1], height=self.img.shape[0], cursor="cross")
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.wait_window()
        return self.rect

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def on_drag(self, event):
        if self.start_x is not None:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2
            )

    def on_release(self, event):
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        w = x2 - x1
        h = y2 - y1
        if w > 0 and h > 0:
            self.rect = (x1, y1, w, h)
        self.root.destroy()

# ================== 主程序 ==================
class App:
    def __init__(self, root):
        self.root = root
        root.title("回合制游戏自动化宏 - 支持随机延迟 + 停止条件")
        root.geometry("1200x850")
        root.resizable(True, True)

        self.process_name_var = tk.StringVar(value=TARGET_PROCESS_NAME)
        self.window_title_var = tk.StringVar(value="")
        self.interval_var = tk.DoubleVar(value=DEFAULT_INTERVAL)
        self.global_timeout_var = tk.IntVar(value=DEFAULT_GLOBAL_TIMEOUT)
        self.once_per_round_var = tk.BooleanVar(value=DEFAULT_ONCE_PER_ROUND)
        self.interval_random_enable_var = tk.BooleanVar(value=DEFAULT_INTERVAL_RANDOM_ENABLE)
        self.interval_random_min_var = tk.DoubleVar(value=DEFAULT_INTERVAL_RANDOM_MIN)
        self.interval_random_max_var = tk.DoubleVar(value=DEFAULT_INTERVAL_RANDOM_MAX)
        self.key_delay_enable_var = tk.BooleanVar(value=DEFAULT_KEY_DELAY_ENABLE)
        self.key_delay_min_var = tk.DoubleVar(value=DEFAULT_KEY_DELAY_MIN)
        self.key_delay_max_var = tk.DoubleVar(value=DEFAULT_KEY_DELAY_MAX)

        # 停止条件变量
        self.stop_enable_var = tk.BooleanVar(value=DEFAULT_STOP_ENABLE)
        self.stop_template_path = tk.StringVar(value=DEFAULT_STOP_TEMPLATE_PATH)
        self.stop_region = DEFAULT_STOP_REGION.copy()
        self.stop_threshold_var = tk.DoubleVar(value=DEFAULT_STOP_THRESHOLD)

        self.steps = []
        self.step_frames = []
        self.running = False
        self.stop_event = threading.Event()
        self.worker_thread = None

        self.create_widgets()
        self.load_config()
        self.log("程序启动 | 支持随机延迟、停止条件（区域匹配）")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：步骤列表
        left_frame = ttk.LabelFrame(main_frame, text="步骤列表（按顺序执行）", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.steps_canvas = tk.Canvas(left_frame, highlightthickness=0)
        self.steps_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.steps_canvas.yview)
        self.steps_scrollable_frame = ttk.Frame(self.steps_canvas)
        self.steps_scrollable_frame.bind("<Configure>", lambda e: self.steps_canvas.configure(scrollregion=self.steps_canvas.bbox("all")))
        self.steps_canvas.create_window((0, 0), window=self.steps_scrollable_frame, anchor="nw")
        self.steps_canvas.configure(yscrollcommand=self.steps_scrollbar.set)
        self.steps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.steps_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧：控制面板
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
        right_frame.pack_propagate(False)

        # 全局设置
        settings_frame = ttk.LabelFrame(right_frame, text="全局设置", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)

        ttk.Label(settings_frame, text="目标进程名:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(settings_frame, textvariable=self.process_name_var, width=20).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(settings_frame, text="窗口标题(可选):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(settings_frame, textvariable=self.window_title_var, width=20).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(settings_frame, text="每轮结束后等待(秒):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(settings_frame, textvariable=self.interval_var, width=10).grid(row=2, column=1, padx=5, pady=2)
        self.interval_random_cb = ttk.Checkbutton(settings_frame, text="随机化轮间等待", variable=self.interval_random_enable_var)
        self.interval_random_cb.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5)
        rand_interval_frame = ttk.Frame(settings_frame)
        rand_interval_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5)
        ttk.Label(rand_interval_frame, text="最小").pack(side=tk.LEFT)
        ttk.Entry(rand_interval_frame, textvariable=self.interval_random_min_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(rand_interval_frame, text="最大").pack(side=tk.LEFT)
        ttk.Entry(rand_interval_frame, textvariable=self.interval_random_max_var, width=6).pack(side=tk.LEFT, padx=2)

        self.key_delay_cb = ttk.Checkbutton(settings_frame, text="按键后随机延迟", variable=self.key_delay_enable_var)
        self.key_delay_cb.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(5,0))
        key_delay_frame = ttk.Frame(settings_frame)
        key_delay_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5)
        ttk.Label(key_delay_frame, text="最小").pack(side=tk.LEFT)
        ttk.Entry(key_delay_frame, textvariable=self.key_delay_min_var, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(key_delay_frame, text="最大").pack(side=tk.LEFT)
        ttk.Entry(key_delay_frame, textvariable=self.key_delay_max_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Label(settings_frame, text="全局超时(秒,0=无限):").grid(row=7, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(settings_frame, textvariable=self.global_timeout_var, width=10).grid(row=7, column=1, padx=5, pady=2)

        self.once_per_round_cb = ttk.Checkbutton(settings_frame, text="每轮仅执行一个动作", variable=self.once_per_round_var)
        self.once_per_round_cb.grid(row=8, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # 停止条件设置
        stop_frame = ttk.LabelFrame(right_frame, text="停止条件", padding=10)
        stop_frame.pack(fill=tk.X, pady=5)

        self.stop_enable_cb = ttk.Checkbutton(stop_frame, text="启用停止条件", variable=self.stop_enable_var)
        self.stop_enable_cb.grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5)

        ttk.Label(stop_frame, text="停止图标模板:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        template_entry = ttk.Entry(stop_frame, textvariable=self.stop_template_path, width=25)
        template_entry.grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(stop_frame, text="浏览", command=self.select_stop_template).grid(row=1, column=2, padx=2)

        ttk.Label(stop_frame, text="搜索区域:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.stop_region_label = ttk.Label(stop_frame, text="未设置", foreground="blue")
        self.stop_region_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Button(stop_frame, text="选择区域", command=self.select_stop_region).grid(row=2, column=2, padx=2)

        ttk.Label(stop_frame, text="匹配阈值:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        scale_stop = ttk.Scale(stop_frame, from_=0.5, to=0.95, orient=tk.HORIZONTAL, variable=self.stop_threshold_var, length=100)
        scale_stop.grid(row=3, column=1, sticky=tk.W, padx=5)
        ttk.Label(stop_frame, textvariable=self.stop_threshold_var, width=5).grid(row=3, column=2, sticky=tk.W)

        # 步骤控制按钮
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="+ 添加步骤", command=self.add_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="导入配置", command=self.import_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="导出配置", command=self.export_config).pack(side=tk.LEFT, padx=2)

        # 执行控制
        exec_frame = ttk.Frame(right_frame)
        exec_frame.pack(fill=tk.X, pady=10)
        self.start_btn = ttk.Button(exec_frame, text="开始执行宏", command=self.start_macro)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(exec_frame, text="停止", command=self.stop_macro, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="空闲")
        ttk.Label(exec_frame, textvariable=self.status_var, foreground="blue").pack(side=tk.LEFT, padx=20)

        # 日志
        log_frame = ttk.LabelFrame(right_frame, text="日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def select_stop_template(self):
        path = filedialog.askopenfilename(
            title="选择停止图标模板",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")]
        )
        if path:
            self.stop_template_path.set(path)
            self.save_config()
            self.log(f"停止图标模板已加载: {path}")

    def select_stop_region(self):
        # 获取游戏窗口并截图
        proc_name = self.process_name_var.get().strip()
        win_title = self.window_title_var.get().strip()
        hwnd = find_target_window(proc_name, win_title)
        if not hwnd:
            messagebox.showerror("错误", "未找到游戏窗口")
            return
        img_full = capture_window_client_screen(hwnd)
        if img_full is None:
            messagebox.showerror("错误", "截图失败，请确保窗口未最小化")
            return
        selector = RegionSelector(self.root, img_full, "选择停止条件搜索区域")
        region = selector.select()
        if region:
            x, y, w, h = region
            self.stop_region = [x, y, w, h]
            self.stop_region_label.config(text=f"({x},{y}) {w}x{h}")
            self.save_config()
            self.log(f"停止条件搜索区域已设置: ({x},{y}) {w}x{h}")

    def refresh_step_list(self):
        for widget in self.steps_scrollable_frame.winfo_children():
            widget.destroy()
        self.step_frames.clear()
        for i, step in enumerate(self.steps):
            frame = ttk.Frame(self.steps_scrollable_frame, relief=tk.RIDGE, borderwidth=1)
            frame.pack(fill=tk.X, pady=2, padx=2)
            enabled_var = tk.BooleanVar(value=step.enabled)
            def toggle_enabled(idx, var):
                self.steps[idx].enabled = var.get()
                self.save_config()
            cb = ttk.Checkbutton(frame, variable=enabled_var, command=lambda idx=i, var=enabled_var: toggle_enabled(idx, var))
            cb.pack(side=tk.LEFT, padx=5)
            name_label = ttk.Label(frame, text=step.name, width=20, anchor=tk.W)
            name_label.pack(side=tk.LEFT, padx=5)
            region_text = f"({step.region[0]},{step.region[1]}) {step.region[2]}x{step.region[3]}" if step.region[2]>0 else "无区域"
            ttk.Label(frame, text=region_text, foreground="blue").pack(side=tk.LEFT, padx=5)
            action = step.on_match_action
            if action.get("type") == "key":
                ttk.Label(frame, text=f"按 {action.get('value','')}").pack(side=tk.LEFT, padx=5)
            elif action.get("type") == "delay":
                ttk.Label(frame, text=f"固定延迟 {step.on_match_delay}s").pack(side=tk.LEFT, padx=5)
            elif action.get("type") == "random_delay":
                ttk.Label(frame, text=f"随机延迟 {step.on_match_random_min}-{step.on_match_random_max}s").pack(side=tk.LEFT, padx=5)
            elif action.get("type") == "goto":
                ttk.Label(frame, text=f"跳转到步骤{step.on_match_goto+1}").pack(side=tk.LEFT, padx=5)
            ttk.Button(frame, text="编辑", command=lambda idx=i: self.edit_step(idx)).pack(side=tk.RIGHT, padx=2)
            ttk.Button(frame, text="↑", command=lambda idx=i: self.move_step_up(idx)).pack(side=tk.RIGHT, padx=2)
            ttk.Button(frame, text="↓", command=lambda idx=i: self.move_step_down(idx)).pack(side=tk.RIGHT, padx=2)
            ttk.Button(frame, text="删除", command=lambda idx=i: self.delete_step(idx)).pack(side=tk.RIGHT, padx=2)
            self.step_frames.append(frame)

    def add_step(self):
        new_index = len(self.steps)
        step = Step(new_index)
        self.steps.append(step)
        self.refresh_step_list()
        self.edit_step(new_index)
        self.save_config()

    def edit_step(self, index):
        def on_save(step):
            step.index = index
            self.steps[index] = step
            self.refresh_step_list()
            self.save_config()
        StepEditDialog(self.root, self.steps[index], index, TEMPLATE_DIR, on_save)

    def delete_step(self, index):
        if messagebox.askyesno("确认", f"删除步骤 {self.steps[index].name}？"):
            del self.steps[index]
            for i, step in enumerate(self.steps):
                step.index = i
            self.refresh_step_list()
            self.save_config()

    def move_step_up(self, index):
        if index > 0:
            self.steps[index], self.steps[index-1] = self.steps[index-1], self.steps[index]
            for i, step in enumerate(self.steps):
                step.index = i
            self.refresh_step_list()
            self.save_config()

    def move_step_down(self, index):
        if index < len(self.steps)-1:
            self.steps[index], self.steps[index+1] = self.steps[index+1], self.steps[index]
            for i, step in enumerate(self.steps):
                step.index = i
            self.refresh_step_list()
            self.save_config()

    def save_config(self):
        data = {
            "global": {
                "process_name": self.process_name_var.get(),
                "window_title": self.window_title_var.get(),
                "interval": self.interval_var.get(),
                "global_timeout": self.global_timeout_var.get(),
                "once_per_round": self.once_per_round_var.get(),
                "interval_random_enable": self.interval_random_enable_var.get(),
                "interval_random_min": self.interval_random_min_var.get(),
                "interval_random_max": self.interval_random_max_var.get(),
                "key_delay_enable": self.key_delay_enable_var.get(),
                "key_delay_min": self.key_delay_min_var.get(),
                "key_delay_max": self.key_delay_max_var.get()
            },
            "stop_condition": {
                "enabled": self.stop_enable_var.get(),
                "template_path": self.stop_template_path.get(),
                "region": self.stop_region,
                "threshold": self.stop_threshold_var.get()
            },
            "steps": [step.to_dict() for step in self.steps]
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"保存配置失败: {e}", is_error=True)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            global_data = data.get("global", {})
            self.process_name_var.set(global_data.get("process_name", TARGET_PROCESS_NAME))
            self.window_title_var.set(global_data.get("window_title", ""))
            self.interval_var.set(global_data.get("interval", DEFAULT_INTERVAL))
            self.global_timeout_var.set(global_data.get("global_timeout", DEFAULT_GLOBAL_TIMEOUT))
            self.once_per_round_var.set(global_data.get("once_per_round", DEFAULT_ONCE_PER_ROUND))
            self.interval_random_enable_var.set(global_data.get("interval_random_enable", DEFAULT_INTERVAL_RANDOM_ENABLE))
            self.interval_random_min_var.set(global_data.get("interval_random_min", DEFAULT_INTERVAL_RANDOM_MIN))
            self.interval_random_max_var.set(global_data.get("interval_random_max", DEFAULT_INTERVAL_RANDOM_MAX))
            self.key_delay_enable_var.set(global_data.get("key_delay_enable", DEFAULT_KEY_DELAY_ENABLE))
            self.key_delay_min_var.set(global_data.get("key_delay_min", DEFAULT_KEY_DELAY_MIN))
            self.key_delay_max_var.set(global_data.get("key_delay_max", DEFAULT_KEY_DELAY_MAX))

            stop_data = data.get("stop_condition", {})
            self.stop_enable_var.set(stop_data.get("enabled", DEFAULT_STOP_ENABLE))
            self.stop_template_path.set(stop_data.get("template_path", DEFAULT_STOP_TEMPLATE_PATH))
            self.stop_region = stop_data.get("region", DEFAULT_STOP_REGION)
            if self.stop_region[2] > 0:
                self.stop_region_label.config(text=f"({self.stop_region[0]},{self.stop_region[1]}) {self.stop_region[2]}x{self.stop_region[3]}")
            self.stop_threshold_var.set(stop_data.get("threshold", DEFAULT_STOP_THRESHOLD))

            steps_data = data.get("steps", [])
            self.steps.clear()
            for i, sdata in enumerate(steps_data):
                step = Step(i)
                step.from_dict(sdata, i)
                self.steps.append(step)
            self.refresh_step_list()
        except Exception as e:
            self.log(f"加载配置失败: {e}", is_error=True)
        if not self.steps:
            self.add_step()

    def import_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON配置", "*.json"), ("所有文件", "*.*")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.process_name_var.set(data.get("global", {}).get("process_name", TARGET_PROCESS_NAME))
                self.window_title_var.set(data.get("global", {}).get("window_title", ""))
                self.interval_var.set(data.get("global", {}).get("interval", DEFAULT_INTERVAL))
                self.global_timeout_var.set(data.get("global", {}).get("global_timeout", DEFAULT_GLOBAL_TIMEOUT))
                self.once_per_round_var.set(data.get("global", {}).get("once_per_round", DEFAULT_ONCE_PER_ROUND))
                self.interval_random_enable_var.set(data.get("global", {}).get("interval_random_enable", DEFAULT_INTERVAL_RANDOM_ENABLE))
                self.interval_random_min_var.set(data.get("global", {}).get("interval_random_min", DEFAULT_INTERVAL_RANDOM_MIN))
                self.interval_random_max_var.set(data.get("global", {}).get("interval_random_max", DEFAULT_INTERVAL_RANDOM_MAX))
                self.key_delay_enable_var.set(data.get("global", {}).get("key_delay_enable", DEFAULT_KEY_DELAY_ENABLE))
                self.key_delay_min_var.set(data.get("global", {}).get("key_delay_min", DEFAULT_KEY_DELAY_MIN))
                self.key_delay_max_var.set(data.get("global", {}).get("key_delay_max", DEFAULT_KEY_DELAY_MAX))
                stop_data = data.get("stop_condition", {})
                self.stop_enable_var.set(stop_data.get("enabled", DEFAULT_STOP_ENABLE))
                self.stop_template_path.set(stop_data.get("template_path", DEFAULT_STOP_TEMPLATE_PATH))
                self.stop_region = stop_data.get("region", DEFAULT_STOP_REGION)
                if self.stop_region[2] > 0:
                    self.stop_region_label.config(text=f"({self.stop_region[0]},{self.stop_region[1]}) {self.stop_region[2]}x{self.stop_region[3]}")
                self.stop_threshold_var.set(stop_data.get("threshold", DEFAULT_STOP_THRESHOLD))
                self.steps.clear()
                for i, sdata in enumerate(data.get("steps", [])):
                    step = Step(i)
                    step.from_dict(sdata, i)
                    self.steps.append(step)
                self.refresh_step_list()
                self.save_config()
                self.log("配置导入成功")
            except Exception as e:
                self.log(f"导入失败: {e}", is_error=True)

    def export_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON配置", "*.json")])
        if path:
            self.save_config()
            try:
                import shutil
                shutil.copy(CONFIG_FILE, path)
                self.log(f"配置已导出到 {path}")
            except Exception as e:
                self.log(f"导出失败: {e}", is_error=True)

    def log(self, msg, is_error=False):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = "[ERROR] " if is_error else ""
        self.log_text.insert(tk.END, f"[{timestamp}] {prefix}{msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_macro(self):
        if self.running:
            return
        valid = any(s.enabled and s.region[2]>0 and s.region[3]>0 and s.template_path and os.path.exists(s.template_path) for s in self.steps)
        if not valid:
            messagebox.showerror("错误", "没有有效的步骤（需要设置区域和模板）")
            return
        self.running = True
        self.stop_event.clear()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("运行中")
        self.log("开始执行宏...")
        self.worker_thread = threading.Thread(target=self.macro_loop, daemon=True)
        self.worker_thread.start()

    def stop_macro(self):
        if not self.running:
            return
        self.running = False
        self.stop_event.set()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("空闲")
        self.log("宏已停止")

    def macro_loop(self):
        proc_name = self.process_name_var.get().strip()
        win_title = self.window_title_var.get().strip()
        interval = self.interval_var.get()
        interval_random = self.interval_random_enable_var.get()
        interval_min = self.interval_random_min_var.get()
        interval_max = self.interval_random_max_var.get()
        once_per_round = self.once_per_round_var.get()
        global_timeout = self.global_timeout_var.get()
        key_delay_enable = self.key_delay_enable_var.get()
        key_delay_min = self.key_delay_min_var.get()
        key_delay_max = self.key_delay_max_var.get()
        stop_enable = self.stop_enable_var.get()
        stop_template_path = self.stop_template_path.get()
        stop_region = self.stop_region
        stop_threshold = self.stop_threshold_var.get()

        start_time = time.time()

        # 预加载步骤模板
        step_data = []
        for s in self.steps:
            if s.enabled and s.region[2] > 0 and s.template_path and os.path.exists(s.template_path):
                tmpl = cv2.imread(s.template_path, cv2.IMREAD_COLOR)
                if tmpl is not None:
                    step_data.append((s, tmpl))
                else:
                    self.log(f"步骤 {s.name} 模板加载失败，跳过", is_error=True)
        if not step_data:
            self.log("没有有效的步骤，宏终止", is_error=True)
            self.stop_macro()
            return

        # 预加载停止模板
        stop_template = None
        if stop_enable and stop_template_path and os.path.exists(stop_template_path):
            stop_template = cv2.imread(stop_template_path, cv2.IMREAD_COLOR)
            if stop_template is None:
                self.log("停止图标模板加载失败，停止条件将无效", is_error=True)
                stop_enable = False

        self.log(f"宏启动，共 {len(step_data)} 个有效步骤，停止条件: {'启用' if stop_enable else '禁用'}")

        while self.running and not self.stop_event.is_set():
            # 检查全局超时
            if global_timeout > 0 and (time.time() - start_time) > global_timeout:
                self.log("全局超时，停止宏")
                break

            hwnd = find_target_window(proc_name, win_title)
            if not hwnd:
                self.log("未找到游戏窗口，等待3秒...")
                time.sleep(3)
                continue

            # ---------- 检查停止条件 ----------
            if stop_enable and stop_template is not None:
                # 获取整个客户区图像（因为停止搜索区域可能很大）
                full_img = capture_window_client_screen(hwnd)
                if full_img is not None:
                    matched, max_val = match_template_in_region(full_img, stop_template, stop_region, stop_threshold)
                    if matched:
                        self.log(f"⚠️ 检测到停止图标 (匹配度 {max_val:.2f})，立即停止宏")
                        self.stop_macro()
                        break
                else:
                    self.log("停止条件截图失败，跳过本次检查")

            # 执行技能步骤扫描
            action_executed = False
            for step, tmpl in step_data:
                if not step.enabled:
                    continue
                # 截图区域（技能检测区域通常较小，使用原有函数）
                img = capture_window_region_screen(hwnd, step.region)
                if img is None:
                    self.log(f"步骤 {step.name} 截图失败，跳过")
                    continue
                matched, max_val = match_template_in_region(img, tmpl, [0,0,0,0], step.threshold)  # 全区域匹配
                if matched:
                    self.log(f"✅ 步骤 {step.name} 匹配成功 (相似度 {max_val:.2f})")
                    action = step.on_match_action
                    act_type = action.get("type")
                    if act_type == "key":
                        key = action.get("value", "")
                        if key:
                            send_key(hwnd, key, self.log, key_delay_enable, key_delay_min, key_delay_max)
                            self.log(f"按下按键: {key}")
                            action_executed = True
                    elif act_type == "delay":
                        delay = step.on_match_delay
                        if delay > 0:
                            self.log(f"固定延迟 {delay} 秒")
                            time.sleep(delay)
                            action_executed = True
                    elif act_type == "random_delay":
                        min_d = step.on_match_random_min
                        max_d = step.on_match_random_max
                        if min_d > 0 and max_d > 0 and min_d <= max_d:
                            delay = random.uniform(min_d, max_d)
                            self.log(f"随机延迟 {delay:.2f} 秒")
                            time.sleep(delay)
                            action_executed = True
                    elif act_type == "goto":
                        target = step.on_match_goto
                        if 0 <= target < len(self.steps):
                            self.log(f"跳转到步骤 {target+1}")
                            # 简单处理：跳出循环，下一轮从头开始
                            break
                    elif act_type == "none":
                        action_executed = True
                    if not step.continue_after_match:
                        self.log("步骤设置了执行后停止本轮扫描")
                        action_executed = True
                        break
                else:
                    # 匹配失败动作
                    action = step.on_mismatch_action
                    act_type = action.get("type")
                    if act_type == "key":
                        key = action.get("value", "")
                        if key:
                            send_key(hwnd, key, self.log, key_delay_enable, key_delay_min, key_delay_max)
                            self.log(f"（失败）按下按键: {key}")
                            action_executed = True
                    elif act_type == "delay":
                        delay = step.on_mismatch_delay
                        if delay > 0:
                            self.log(f"（失败）固定延迟 {delay} 秒")
                            time.sleep(delay)
                            action_executed = True
                    elif act_type == "random_delay":
                        min_d = step.on_mismatch_random_min
                        max_d = step.on_mismatch_random_max
                        if min_d > 0 and max_d > 0 and min_d <= max_d:
                            delay = random.uniform(min_d, max_d)
                            self.log(f"（失败）随机延迟 {delay:.2f} 秒")
                            time.sleep(delay)
                            action_executed = True
                    elif act_type == "goto":
                        target = step.on_mismatch_goto
                        if 0 <= target < len(self.steps):
                            self.log(f"（失败）跳转到步骤 {target+1}")
                            break
                if once_per_round and action_executed:
                    self.log("每轮仅执行一个动作，本轮停止扫描")
                    break

            # 等待下一轮
            if interval_random and interval_min > 0 and interval_max >= interval_min:
                wait = random.uniform(interval_min, interval_max)
                self.log(f"随机等待 {wait:.2f} 秒后下一轮")
                time.sleep(wait)
            else:
                self.log(f"等待 {interval} 秒后下一轮")
                time.sleep(interval)
        self.stop_macro()

def main():
    root = tk.Tk()
    global app
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_macro(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()