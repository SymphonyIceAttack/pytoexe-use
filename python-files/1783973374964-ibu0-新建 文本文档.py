import sys
import os
import json
import threading
import tkinter as tk
from tkinter import ttk
from pynput import mouse, keyboard
import pystray
from PIL import Image, ImageDraw

# ========== 全局变量 ==========
is_running = True
mouse_listener = None
keyboard_ctrl = keyboard.Controller()
trigger_key_name = "alt_l"          # 默认触发键（左 Alt）
trigger_key_obj = keyboard.Key.alt_l

CONFIG_FILE = "trigger_config.json"

# ========== 键名映射 ==========
# 显示名 -> 内部名（用于存储和查找）
KEY_OPTIONS = [
    ("Left Alt", "alt_l"),
    ("Right Alt", "alt_r"),
    ("Left Ctrl", "ctrl_l"),
    ("Right Ctrl", "ctrl_r"),
    ("Left Shift", "shift_l"),
    ("Right Shift", "shift_r"),
    ("Space", "space"),
    ("Enter", "enter"),
    ("Tab", "tab"),
    ("Escape", "esc"),
    ("Backspace", "backspace"),
    ("Delete", "delete"),
    ("Home", "home"),
    ("End", "end"),
    ("Page Up", "page_up"),
    ("Page Down", "page_down"),
    ("Up", "up"),
    ("Down", "down"),
    ("Left", "left"),
    ("Right", "right"),
    ("F1", "f1"), ("F2", "f2"), ("F3", "f3"), ("F4", "f4"),
    ("F5", "f5"), ("F6", "f6"), ("F7", "f7"), ("F8", "f8"),
    ("F9", "f9"), ("F10", "f10"), ("F11", "f11"), ("F12", "f12"),
]
# 字母 A-Z
for i in range(26):
    ch = chr(ord('A') + i)
    KEY_OPTIONS.append((ch, ch.lower()))
# 数字 0-9
for d in range(10):
    KEY_OPTIONS.append((str(d), str(d)))

# 内部名 -> pynput Key 对象
def get_key_object(internal_name):
    # 字母、数字 -> KeyCode
    if len(internal_name) == 1 and internal_name.isalnum():
        return keyboard.KeyCode.from_char(internal_name)
    # 功能键
    key_map = {
        "alt_l": keyboard.Key.alt_l,
        "alt_r": keyboard.Key.alt_r,
        "ctrl_l": keyboard.Key.ctrl_l,
        "ctrl_r": keyboard.Key.ctrl_r,
        "shift_l": keyboard.Key.shift_l,
        "shift_r": keyboard.Key.shift_r,
        "space": keyboard.Key.space,
        "enter": keyboard.Key.enter,
        "tab": keyboard.Key.tab,
        "esc": keyboard.Key.esc,
        "backspace": keyboard.Key.backspace,
        "delete": keyboard.Key.delete,
        "home": keyboard.Key.home,
        "end": keyboard.Key.end,
        "page_up": keyboard.Key.page_up,
        "page_down": keyboard.Key.page_down,
        "up": keyboard.Key.up,
        "down": keyboard.Key.down,
        "left": keyboard.Key.left,
        "right": keyboard.Key.right,
        "f1": keyboard.Key.f1,
        "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5,
        "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7,
        "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11,
        "f12": keyboard.Key.f12,
    }
    return key_map.get(internal_name)

# ========== 配置读写 ==========
def load_config():
    global trigger_key_name, trigger_key_obj
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                name = data.get("trigger_key", "alt_l")
                # 验证是否有效
                obj = get_key_object(name)
                if obj is not None:
                    trigger_key_name = name
                    trigger_key_obj = obj
                else:
                    trigger_key_name = "alt_l"
                    trigger_key_obj = keyboard.Key.alt_l
        else:
            trigger_key_name = "alt_l"
            trigger_key_obj = keyboard.Key.alt_l
    except Exception:
        trigger_key_name = "alt_l"
        trigger_key_obj = keyboard.Key.alt_l

def save_config(name):
    global trigger_key_name, trigger_key_obj
    obj = get_key_object(name)
    if obj is None:
        return False
    trigger_key_name = name
    trigger_key_obj = obj
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"trigger_key": name}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# ========== 托盘图标 ==========
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_tray_icon():
    try:
        ico_path = get_resource_path("game.ico")
        if os.path.exists(ico_path):
            return Image.open(ico_path)
    except:
        pass
    # 默认绿色圆点
    img = Image.new('RGB', (64, 64), (40, 40, 40))
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill=(0, 255, 0))
    return img

def on_quit(icon, item, root=None):
    global is_running
    is_running = False
    # 释放可能卡住的按键
    keyboard_ctrl.release(trigger_key_obj)
    if mouse_listener is not None:
        mouse_listener.stop()
    icon.stop()
    if root:
        root.quit()
    sys.exit(0)

# ========== 鼠标事件处理 ==========
def on_click(x, y, button, pressed):
    try:
        if button == mouse.Button.right:
            if pressed:
                keyboard_ctrl.press(trigger_key_obj)
            else:
                keyboard_ctrl.release(trigger_key_obj)
    except Exception as e:
        print(f"鼠标事件错误: {e}")

# ========== 设置窗口（Tkinter） ==========
settings_window = None

def create_settings_window(root):
    global settings_window, trigger_key_name
    if settings_window is not None and settings_window.winfo_exists():
        settings_window.lift()
        return

    settings_window = tk.Toplevel(root)
    settings_window.title("触发键设置")
    settings_window.geometry("300x150")
    settings_window.resizable(False, False)

    # 当前显示
    tk.Label(settings_window, text="选择长按鼠标右键时触发的按键：").pack(pady=10)

    # 下拉列表
    var = tk.StringVar()
    # 显示名列表
    display_names = [opt[0] for opt in KEY_OPTIONS]
    # 找出当前内部名对应的显示名
    current_display = None
    for disp, intern in KEY_OPTIONS:
        if intern == trigger_key_name:
            current_display = disp
            break
    if current_display is None:
        current_display = display_names[0]  # fallback

    var.set(current_display)
    combobox = ttk.Combobox(settings_window, textvariable=var, values=display_names, state="readonly")
    combobox.pack(pady=5)

    # 保存按钮
    def save_and_close():
        selected_display = var.get()
        # 找到对应的内部名
        selected_internal = None
        for disp, intern in KEY_OPTIONS:
            if disp == selected_display:
                selected_internal = intern
                break
        if selected_internal and save_config(selected_internal):
            # 更新全局对象
            global trigger_key_obj
            trigger_key_obj = get_key_object(selected_internal)
            # 更新状态栏提示（可选）
            status_var.set(f"当前触发键: {selected_display}")
            settings_window.destroy()
        else:
            tk.messagebox.showerror("错误", "保存配置失败，请重试。")

    btn_frame = tk.Frame(settings_window)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="保存", command=save_and_close, width=10).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="取消", command=settings_window.destroy, width=10).pack(side=tk.LEFT, padx=5)

    # 状态提示（在窗口底部）
    status_var = tk.StringVar()
    status_var.set(f"当前触发键: {current_display}")
    status_label = tk.Label(settings_window, textvariable=status_var, fg="gray")
    status_label.pack(side=tk.BOTTOM, pady=5)

# ========== 主程序 ==========
def main():
    global mouse_listener, trigger_key_obj

    # 加载配置
    load_config()
    trigger_key_obj = get_key_object(trigger_key_name)

    # 创建 Tk 根窗口（隐藏）
    root = tk.Tk()
    root.withdraw()
    root.title("右键长按触发键设置")

    # 鼠标监听器
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()

    # 托盘图标
    tray_icon = pystray.Icon(
        "RightClickTrigger",
        icon=create_tray_icon(),
        menu=pystray.Menu(
            pystray.MenuItem("设置触发键", lambda: root.after(0, lambda: create_settings_window(root))),
            pystray.MenuItem("退出程序", lambda: root.after(0, lambda: on_quit(tray_icon, None, root)))
        )
    )
    threading.Thread(target=tray_icon.run, daemon=True).start()

    print("程序已启动。按住鼠标右键将模拟按下当前设置的触发键，松开则释放。")
    print("可通过托盘图标修改触发键。")

    # 进入 Tk 主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        on_quit(tray_icon, None, root)
    finally:
        if mouse_listener is not None and mouse_listener.is_alive():
            mouse_listener.stop()
        if tray_icon is not None:
            tray_icon.stop()

if __name__ == "__main__":
    main()