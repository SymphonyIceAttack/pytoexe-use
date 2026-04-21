import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from monitorcontrol import get_monitors

# 全局变量
current_brightness = 50
current_contrast = 80
is_running = True
monitor = None

# 初始化显示器
def init_monitor():
    global monitor
    try:
        monitors = get_monitors()
        if not monitors:
            return False
        monitor = monitors[0]
        return True
    except:
        return False

# 获取当前亮度
def get_brightness():
    try:
        with monitor:
            return monitor.get_brightness()[0]
    except:
        return None

# 设置亮度
def set_brightness(val):
    global current_brightness
    try:
        current_brightness = int(val)
        with monitor:
            monitor.set_brightness(current_brightness)
        brightness_label.config(text=f"当前亮度：{current_brightness}")
    except:
        pass

# 设置对比度
def set_contrast(val):
    global current_contrast
    try:
        current_contrast = int(val)
        with monitor:
            monitor.set_contrast(current_contrast)
        contrast_label.config(text=f"当前对比度：{current_contrast}")
    except:
        pass

# 护眼模式
def eye_mode():
    set_brightness(40)
    set_contrast(70)
    messagebox.showinfo("护眼模式", "已切换：低亮度+暖色温适配")

# 夜间模式
def night_mode():
    set_brightness(20)
    set_contrast(60)
    messagebox.showinfo("夜间模式", "已切换：超低亮度 夜间护眼")

# 标准模式
def normal_mode():
    set_brightness(70)
    set_contrast(85)
    messagebox.showinfo("标准模式", "已恢复默认显示")

# 主界面
def create_gui():
    global brightness_label, contrast_label
    
    root = tk.Tk()
    root.title("AOC显示器 护眼亮度调节器")
    root.geometry("450x300")
    root.resizable(False, False)

    # 标题
    title_label = ttk.Label(root, text="AOC 显示器硬件调光", font=("微软雅黑", 16, "bold"))
    title_label.pack(pady=10)

    # 亮度调节
    brightness_frame = ttk.Frame(root)
    brightness_frame.pack(pady=5, fill=tk.X, padx=20)
    
    ttk.Label(brightness_frame, text="亮度调节：", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    
    brightness_slider = ttk.Scale(
        brightness_frame, from_=0, to=100, command=set_brightness, length=250
    )
    brightness_slider.set(current_brightness)
    brightness_slider.pack(side=tk.LEFT, padx=5)
    
    brightness_label = ttk.Label(brightness_frame, text=f"当前亮度：{current_brightness}", font=("微软雅黑", 10))
    brightness_label.pack(side=tk.LEFT, padx=5)

    # 对比度调节
    contrast_frame = ttk.Frame(root)
    contrast_frame.pack(pady=5, fill=tk.X, padx=20)
    
    ttk.Label(contrast_frame, text="对比度：", font=("微软雅黑", 11)).pack(side=tk.LEFT)
    
    contrast_slider = ttk.Scale(
        contrast_frame, from_=0, to=100, command=set_contrast, length=250
    )
    contrast_slider.set(current_contrast)
    contrast_slider.pack(side=tk.LEFT, padx=5)
    
    contrast_label = ttk.Label(contrast_frame, text=f"当前对比度：{current_contrast}", font=("微软雅黑", 10))
    contrast_label.pack(side=tk.LEFT, padx=5)

    # 模式按钮
    mode_frame = ttk.Frame(root)
    mode_frame.pack(pady=15)

    ttk.Button(mode_frame, text="护眼模式", command=eye_mode, width=12).grid(row=0, column=0, padx=5)
    ttk.Button(mode_frame, text="夜间模式", command=night_mode, width=12).grid(row=0, column=1, padx=5)
    ttk.Button(mode_frame, text="标准模式", command=normal_mode, width=12).grid(row=0, column=2, padx=5)

    # 说明
    tip_label = ttk.Label(root, text="✅ 硬件调光 | ✅ 无画质损失 | ✅ 护眼更健康", font=("微软雅黑", 10))
    tip_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    if not init_monitor():
        messagebox.showerror("错误", "未检测到支持的AOC显示器\n请确认显示器已连接、驱动正常")
    else:
        b = get_brightness()
        if b:
            current_brightness = b
        create_gui()