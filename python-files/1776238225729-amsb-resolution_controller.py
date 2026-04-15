import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk
import json
import os
import sys

# 定义 Windows API 常量
SW_RESTORE = 9

# 定义回调函数类型
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("窗口分辨率控制器")
        self.root.geometry("500x400")
        self.setup_ui()
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 窗口选择
        window_frame = ttk.LabelFrame(main_frame, text="选择窗口", padding="10")
        window_frame.pack(fill=tk.X, pady=5)
        
        self.window_var = tk.StringVar()
        self.window_combobox = ttk.Combobox(window_frame, textvariable=self.window_var, state="readonly")
        self.window_combobox.pack(fill=tk.X, pady=5)
        
        ttk.Button(window_frame, text="刷新窗口列表", command=self.refresh_windows).pack(pady=5)
        
        # 分辨率设置
        resolution_frame = ttk.LabelFrame(main_frame, text="设置分辨率", padding="10")
        resolution_frame.pack(fill=tk.X, pady=5)
        
        # 宽度输入
        width_frame = ttk.Frame(resolution_frame)
        width_frame.pack(fill=tk.X, pady=5)
        ttk.Label(width_frame, text="宽度:").pack(side=tk.LEFT, padx=5)
        self.width_var = tk.StringVar(value="1920")
        ttk.Entry(width_frame, textvariable=self.width_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 高度输入
        height_frame = ttk.Frame(resolution_frame)
        height_frame.pack(fill=tk.X, pady=5)
        ttk.Label(height_frame, text="高度:").pack(side=tk.LEFT, padx=5)
        self.height_var = tk.StringVar(value="1080")
        ttk.Entry(height_frame, textvariable=self.height_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 常用分辨率
        presets_frame = ttk.LabelFrame(main_frame, text="常用分辨率", padding="10")
        presets_frame.pack(fill=tk.X, pady=5)
        
        presets = [
            ("1920x1080", 1920, 1080),
            ("1600x900", 1600, 900),
            ("1366x768", 1366, 768),
            ("1280x720", 1280, 720),
            ("1024x768", 1024, 768)
        ]
        
        preset_frame = ttk.Frame(presets_frame)
        preset_frame.pack(fill=tk.X)
        
        for preset_name, width, height in presets:
            ttk.Button(preset_frame, text=preset_name, command=lambda w=width, h=height: self.set_preset(w, h)).pack(side=tk.LEFT, padx=5)
        
        # 应用按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="应用", command=self.apply_resolution).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # 初始刷新窗口列表
        self.refresh_windows()
    
    def refresh_windows(self):
        windows = self.get_windows()
        window_titles = [title for title, hwnd in windows]
        self.window_combobox['values'] = window_titles
        if window_titles:
            self.window_var.set(window_titles[0])
    
    def get_windows(self):
        windows = []
        
        def callback(hwnd, lParam):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
                    title = buffer.value
                    if title:
                        windows.append((title, hwnd))
            return True
        
        ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), 0)
        return windows
    
    def set_preset(self, width, height):
        self.width_var.set(str(width))
        self.height_var.set(str(height))
    
    def apply_resolution(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            selected_title = self.window_var.get()
            if not selected_title:
                self.show_message("请选择一个窗口!")
                return
            
            windows = self.get_windows()
            target_hwnd = None
            for title, hwnd in windows:
                if title == selected_title:
                    target_hwnd = hwnd
                    break
            
            if not target_hwnd:
                self.show_message("找不到选中的窗口!")
                return
            
            # 恢复窗口（如果最小化）
            ctypes.windll.user32.ShowWindow(target_hwnd, SW_RESTORE)
            
            # 设置窗口大小
            # 获取窗口当前位置
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(target_hwnd, ctypes.byref(rect))
            
            # 计算新的窗口位置（保持中心）
            new_left = rect.left
            new_top = rect.top
            
            # 设置窗口大小
            result = ctypes.windll.user32.MoveWindow(target_hwnd, new_left, new_top, width, height, True)
            
            if result:
                self.show_message(f"窗口分辨率设置成功: {width} x {height}")
            else:
                self.show_message("窗口分辨率设置失败!")
                
        except ValueError:
            self.show_message("请输入有效的分辨率!")
        except Exception as e:
            self.show_message(f"错误: {str(e)}")
    
    def show_message(self, message):
        # 创建消息窗口
        msg_window = tk.Toplevel(self.root)
        msg_window.title("消息")
        msg_window.geometry("300x100")
        msg_window.transient(self.root)
        msg_window.grab_set()
        
        ttk.Label(msg_window, text=message, padding=10).pack()
        ttk.Button(msg_window, text="确定", command=msg_window.destroy).pack(pady=5)

def run_as_admin():
    # 检查是否以管理员身份运行
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        # 重新以管理员身份运行
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        return True
    return False

if __name__ == "__main__":
    if run_as_admin():
        sys.exit()
    
    root = tk.Tk()
    app = App(root)
    root.mainloop()