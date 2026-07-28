import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyautogui
import cv2
import numpy as np
import time
import threading
import json
import os
from PIL import Image
import keyboard

# ==================== 全局配置默认值 ====================
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "template_path": "",
    "watch_region": [100, 100, 400, 300],
    "match_threshold": 0.75,
    "check_interval": 0.5,
    "action_keys": ["space"],
    "repeat_count": 1,
    "random_delay": True,
    "min_delay": 0.05,
    "max_delay": 0.25,
    "repeat_mode": "loop",
    "cooldown": 3.0,
    "hotkey_start": "f8",
    "hotkey_stop": "f9"
}

config = DEFAULT_CONFIG.copy()
running = False
template_img = None
last_trigger_time = 0

# ==================== 图像处理 ====================
def load_template(path):
    global template_img
    if not path or not os.path.exists(path):
        template_img = None
        return False
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return False
    template_img = img
    return True

def region_screenshot(region):
    """截取指定区域，返回BGR格式的numpy数组"""
    x, y, w, h = region
    pil_img = pyautogui.screenshot(region=(x, y, w, h))
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def match_template(screenshot, threshold):
    """多尺度模板匹配"""
    if template_img is None:
        return False, None
    
    gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    
    h, w = gray_template.shape
    
    # 多尺度匹配
    scales = [0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
    best_val = 0
    best_loc = None
    
    for scale in scales:
        if scale != 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            if new_w <= 0 or new_h <= 0 or new_w > gray_screen.shape[1] or new_h > gray_screen.shape[0]:
                continue
            resized = cv2.resize(gray_template, (new_w, new_h))
        else:
            resized = gray_template
        
        try:
            result = cv2.matchTemplate(gray_screen, resized, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
        except cv2.error:
            continue
    
    return best_val >= threshold, best_loc

# ==================== 动作执行 ====================
def do_actions():
    keys = config["action_keys"]
    repeat = config["repeat_count"]
    
    for _ in range(repeat):
        for key in keys:
            if not key:
                continue
            pyautogui.press(key)
            if config["random_delay"]:
                delay = np.random.uniform(config["min_delay"], config["max_delay"])
                time.sleep(delay)
            else:
                time.sleep(0.1)

# ==================== 主监控循环 ====================
def monitor_loop():
    global running, last_trigger_time
    
    region = tuple(config["watch_region"])
    mode = config["repeat_mode"]
    cooldown = config["cooldown"]
    
    log_message("[*] 监控已启动")
    
    while running:
        try:
            # 检查停止热键
            if keyboard.is_pressed(config["hotkey_stop"]):
                running = False
                log_message("[-] 监控已停止（热键）")
                update_status("已停止")
                break
            
            # 冷却检查
            if mode == "cooldown" and (time.time() - last_trigger_time) < cooldown:
                time.sleep(config["check_interval"])
                continue
            
            screenshot = region_screenshot(region)
            matched, loc = match_template(screenshot, config["match_threshold"])
            
            if matched:
                log_message(f"[+] 检测到目标！执行动作")
                do_actions()
                last_trigger_time = time.time()
                
                if mode == "once":
                    running = False
                    log_message("[-] 单次模式完成，已停止")
                    update_status("已停止")
                    break
            
            time.sleep(config["check_interval"])
            
        except Exception as e:
            log_message(f"[!] 错误: {str(e)}")
            time.sleep(1)
    
    update_status("已停止")

# ==================== 线程启动 ====================
def start_monitor():
    global running
    if template_img is None:
        messagebox.showwarning("警告", "请先加载模板图片！")
        return
    if not config["action_keys"] or all(not k for k in config["action_keys"]):
        messagebox.showwarning("警告", "请至少设置一个按键动作！")
        return
    
    running = True
    update_status("运行中...")
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()

def stop_monitor():
    global running
    running = False
    log_message("[-] 监控已停止")
    update_status("已停止")

# ==================== 配置保存/加载 ====================
def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        log_message("[*] 配置已保存")
    except Exception as e:
        log_message(f"[!] 保存配置失败: {e}")

def load_config_file():
    global config
    if not os.path.exists(CONFIG_FILE):
        return
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            config.update(loaded)
        log_message("[*] 配置已加载")
        refresh_ui_from_config()
    except Exception as e:
        log_message(f"[!] 加载配置失败: {e}")

# ==================== GUI ====================
root = tk.Tk()
root.title("图像触发按键工具 v1.0")
root.geometry("580x520")
root.resizable(False, False)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=5, pady=5)

# ---------- 标签页1：模板与区域 ----------
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="模板与区域")

template_path_var = tk.StringVar()
ttk.Label(tab1, text="模板图片路径:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
ttk.Entry(tab1, textvariable=template_path_var, width=45).grid(row=0, column=1, padx=5)
def browse_template():
    path = filedialog.askopenfilename(
        title="选择模板图片",
        filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp")]
    )
    if path:
        template_path_var.set(path)
        config["template_path"] = path
        if load_template(path):
            log_message(f"[*] 模板加载成功: {os.path.basename(path)}")
        else:
            log_message("[!] 模板加载失败")
ttk.Button(tab1, text="浏览", command=browse_template).grid(row=0, column=2, padx=5)

ttk.Label(tab1, text="监控区域 (x, y, w, h):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
region_frame = ttk.Frame(tab1)
region_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)
region_vars = [tk.IntVar(value=100), tk.IntVar(value=100), tk.IntVar(value=400), tk.IntVar(value=300)]
for i, var in enumerate(region_vars):
    ttk.Entry(region_frame, textvariable=var, width=8).pack(side="left", padx=2)

def pick_region():
    messagebox.showinfo("提示", "3秒后将进入区域选择模式，请把鼠标移到区域左上角，然后等待截图")
    time.sleep(3)
    x1, y1 = pyautogui.position()
    messagebox.showinfo("提示", f"已记录左上角 ({x1}, {y1})，3秒后记录右下角")
    time.sleep(3)
    x2, y2 = pyautogui.position()
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    region_vars[0].set(min(x1, x2))
    region_vars[1].set(min(y1, y2))
    region_vars[2].set(w)
    region_vars[3].set(h)
    config["watch_region"] = [min(x1, x2), min(y1, y2), w, h]
    log_message(f"[*] 区域已设置为: ({min(x1, x2)}, {min(y1, y2)}, {w}, {h})")
ttk.Button(tab1, text="鼠标拾取区域", command=pick_region).grid(row=2, column=1, sticky="w", padx=5, pady=5)

ttk.Label(tab1, text="匹配阈值 (0.1-1.0):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
threshold_var = tk.DoubleVar(value=0.75)
ttk.Scale(tab1, from_=0.1, to=1.0, variable=threshold_var, orient="horizontal", length=200).grid(row=3, column=1, sticky="w", padx=5)
threshold_label = ttk.Label(tab1, text="0.75")
threshold_label.grid(row=3, column=2, sticky="w")
def update_threshold_label(*args):
    val = round(threshold_var.get(), 2)
    threshold_label.config(text=str(val))
    config["match_threshold"] = val
threshold_var.trace_add("write", update_threshold_label)

ttk.Label(tab1, text="检测间隔 (秒):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
interval_var = tk.DoubleVar(value=0.5)
ttk.Entry(tab1, textvariable=interval_var, width=10).grid(row=4, column=1, sticky="w", padx=5)
def update_interval():
    config["check_interval"] = interval_var.get()
interval_var.trace_add("write", lambda *a: update_interval())

# ---------- 标签页2：按键动作 ----------
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="按键动作")

keys_frame = ttk.Frame(tab2)
keys_frame.pack(padx=10, pady=10, anchor="w")
key_vars = []
for i in range(5):
    ttk.Label(keys_frame, text=f"按键{i+1}:").grid(row=i, column=0, sticky="w", pady=2)
    var = tk.StringVar()
    key_vars.append(var)
    entry = ttk.Entry(keys_frame, textvariable=var, width=15)
    entry.grid(row=i, column=1, pady=2, padx=5)
    def make_update(idx):
        def update():
            keys = [v.get().strip() for v in key_vars if v.get().strip()]
            config["action_keys"] = keys
        return update
    var.trace_add("write", lambda *a, f=i: [make_update(j)() for j in range(5)])

ttk.Label(tab2, text="每个按键重复次数:").pack(anchor="w", padx=10, pady=(10, 2))
repeat_var = tk.IntVar(value=1)
ttk.Entry(tab2, textvariable=repeat_var, width=10).pack(anchor="w", padx=10)
def update_repeat():
    config["repeat_count"] = repeat_var.get()
repeat_var.trace_add("write", lambda *a: update_repeat())

ttk.Label(tab2, text="重复模式:").pack(anchor="w", padx=10, pady=(10, 2))
mode_var = tk.StringVar(value="loop")
mode_frame = ttk.Frame(tab2)
mode_frame.pack(anchor="w", padx=10)
ttk.Radiobutton(mode_frame, text="循环检测", variable=mode_var, value="loop").pack(side="left", padx=5)
ttk.Radiobutton(mode_frame, text="单次触发后停止", variable=mode_var, value="once").pack(side="left", padx=5)
ttk.Radiobutton(mode_frame, text="冷却模式", variable=mode_var, value="cooldown").pack(side="left", padx=5)
def update_mode():
    config["repeat_mode"] = mode_var.get()
mode_var.trace_add("write", lambda *a: update_mode())

ttk.Label(tab2, text="冷却时间(秒，仅冷却模式):").pack(anchor="w", padx=10, pady=(5, 2))
cooldown_var = tk.DoubleVar(value=3.0)
ttk.Entry(tab2, textvariable=cooldown_var, width=10).pack(anchor="w", padx=10)
def update_cooldown():
    config["cooldown"] = cooldown_var.get()
cooldown_var.trace_add("write", lambda *a: update_cooldown())

# ---------- 标签页3：高级选项 ----------
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="高级选项")

random_delay_var = tk.BooleanVar(value=True)
ttk.Checkbutton(tab3, text="启用随机延迟（更像真人）", variable=random_delay_var).pack(anchor="w", padx=10, pady=10)
def update_random_delay():
    config["random_delay"] = random_delay_var.get()
random_delay_var.trace_add("write", lambda *a: update_random_delay())

delay_frame = ttk.Frame(tab3)
delay_frame.pack(anchor="w", padx=10)
ttk.Label(delay_frame, text="最小延迟(秒):").pack(side="left")
min_delay_var = tk.DoubleVar(value=0.05)
ttk.Entry(delay_frame, textvariable=min_delay_var, width=6).pack(side="left", padx=5)
ttk.Label(delay_frame, text="最大延迟(秒):").pack(side="left", padx=(10, 0))
max_delay_var = tk.DoubleVar(value=0.25)
ttk.Entry(delay_frame, textvariable=max_delay_var, width=6).pack(side="left", padx=5)
def update_delays():
    config["min_delay"] = min_delay_var.get()
    config["max_delay"] = max_delay_var.get()
min_delay_var.trace_add("write", lambda *a: update_delays())
max_delay_var.trace_add("write", lambda *a: update_delays())

ttk.Label(tab3, text="启动热键:").pack(anchor="w", padx=10, pady=(15, 2))
hotkey_start_var = tk.StringVar(value="f8")
ttk.Entry(tab3, textvariable=hotkey_start_var, width=10).pack(anchor="w", padx=10)
def update_hotkey_start():
    config["hotkey_start"] = hotkey_start_var.get()
hotkey_start_var.trace_add("write", lambda *a: update_hotkey_start())

ttk.Label(tab3, text="停止热键:").pack(anchor="w", padx=10, pady=(10, 2))
hotkey_stop_var = tk.StringVar(value="f9")
ttk.Entry(tab3, textvariable=hotkey_stop_var, width=10).pack(anchor="w", padx=10)
def update_hotkey_stop():
    config["hotkey_stop"] = hotkey_stop_var.get()
hotkey_stop_var.trace_add("write", lambda *a: update_hotkey_stop())

# ---------- 底部控制栏 ----------
control_frame = ttk.Frame(root)
control_frame.pack(fill="x", padx=5, pady=5)

status_label = ttk.Label(control_frame, text="状态: 未启动", foreground="gray")
status_label.pack(side="left", padx=10)

def update_status(text):
    color = "green" if text == "运行中..." else "red" if text == "已停止" else "orange"
    status_label.config(text=f"状态: {text}", foreground=color)

ttk.Button(control_frame, text="▶ 启动 (F8)", command=start_monitor).pack(side="right", padx=5)
ttk.Button(control_frame, text="■ 停止 (F9)", command=stop_monitor).pack(side="right", padx=5)
ttk.Button(control_frame, text="保存配置", command=save_config).pack(side="right", padx=5)
ttk.Button(control_frame, text="加载配置", command=load_config_file).pack(side="right", padx=5)

# ---------- 日志区 ----------
log_frame = ttk.LabelFrame(root, text="运行日志")
log_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
log_text = tk.Text(log_frame, height=6, width=70, font=("Consolas", 9))
log_scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
log_text.config(yscrollcommand=log_scrollbar.set)
log_scrollbar.pack(side="right", fill="y")
log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)

def log_message(msg):
    timestamp = time.strftime("%H:%M:%S")
    log_text.insert("end", f"[{timestamp}] {msg}\n")
    log_text.see("end")
    log_text.update()

def refresh_ui_from_config():
    template_path_var.set(config.get("template_path", ""))
    region = config.get("watch_region", [100, 100, 400, 300])
    for i, val in enumerate(region):
        region_vars[i].set(val)
    threshold_var.set(config.get("match_threshold", 0.75))
    interval_var.set(config.get("check_interval", 0.5))
    keys = config.get("action_keys", ["space"])
    for i, var in enumerate(key_vars):
        var.set(keys[i] if i < len(keys) else "")
    repeat_var.set(config.get("repeat_count", 1))
    mode_var.set(config.get("repeat_mode", "loop"))
    cooldown_var.set(config.get("cooldown", 3.0))
    random_delay_var.set(config.get("random_delay", True))
    min_delay_var.set(config.get("min_delay", 0.05))
    max_delay_var.set(config.get("max_delay", 0.25))
    hotkey_start_var.set(config.get("hotkey_start", "f8"))
    hotkey_stop_var.set(config.get("hotkey_stop", "f9"))

# ---------- 启动 ----------
def on_closing():
    global running
    running = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
load_config_file()
log_message("[*] 程序已启动，按 F8 开始监控，F9 停止")
update_status("未启动")
root.mainloop()