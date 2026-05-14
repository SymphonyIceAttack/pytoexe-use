import time
import threading
import random
import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
import json
from pynput import keyboard
from pynput.keyboard import Key, Controller

# ==================== 配置文件 ====================
CONFIG_FILE = "typer_config.json"
# ==================== 全局配置（默认） ====================
TRIGGER_KEY = Key.f8
FILE_PATH = "text.txt"
DATA_PATH = "data.dat"
DEFAULT_CONFIG = {
    "base_delay_min": 0.042,
    "base_delay_max": 0.15,
    "punct_pause": 2.0,
    "key_press_min": 0.004,
    "key_press_max": 0.04,
    "accuracy": 1.0,
    "default_duration": 20.0
}
config = DEFAULT_CONFIG.copy()

# ==================== 配置保存/加载 ====================
def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except:
        pass

def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                config.update(loaded)
    except:
        config = DEFAULT_CONFIG.copy()

# ==================== 全局变量 ====================
is_running = False
kb = Controller()
listener = None
max_total_seconds = config["default_duration"]
content_data = {}

# ==================== data.dat 解析 ====================
def load_data_dat():
    global content_data
    content_data = {}
    if not os.path.exists(DATA_PATH):
        messagebox.showerror("错误", f"未找到 {DATA_PATH}！")
        return
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = f.read()
        pattern = re.compile(r'<([^>]+)>(.*?)<\1>', re.DOTALL)
        matches = pattern.findall(data)
        for name, content in matches:
            content_data[name.strip()] = content.strip()
        content_data["自定义 text.txt"] = ""
    except:
        messagebox.showerror("错误", "data.dat 解析失败")

def get_selected_content():
    selected = content_combo.get()
    if selected == "自定义 text.txt":
        return read_text_file()
    return content_data.get(selected, "")

# ==================== 文件操作 ====================
def read_text_file():
    if not os.path.exists(FILE_PATH):
        check_and_create_text()
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def check_and_create_text():
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write("在这里写入自定义输入内容")
    try:
        os.startfile(FILE_PATH)
    except:
        pass

def open_text_file():
    check_and_create_text()

# ==================== 优质随机工具 ====================
def uniform_between(a, b):
    """稳定均匀随机"""
    return a + (b - a) * random.random()

def random_human_delay():
    """人类输入节奏：随机快慢混合"""
    min_d = config["base_delay_min"]
    max_d = config["base_delay_max"]
    # 70%概率正常速度，20%快，10%慢，模拟自然节奏
    r = random.random()
    if r < 0.7:
        return uniform_between(min_d, max_d)
    elif r < 0.9:
        return uniform_between(min_d * 0.3, min_d * 0.9)
    else:
        return uniform_between(max_d * 1.1, max_d * 1.8)

# ==================== 打字核心（新版随机快慢 + 总时长±5s） ====================
def human_press_char(char):
    t = uniform_between(config["key_press_min"], config["key_press_max"])
    kb.press(char)
    time.sleep(t)
    kb.release(char)

def type_human_like():
    global is_running
    if is_running:
        return
    content = get_selected_content()
    if not content:
        messagebox.showwarning("提示", "无内容可输入")
        return

    is_running = True
    status_label.config(text="正在输入...")
    char_list = list(content)
    total_chars = len(char_list)
    start_time = time.perf_counter()

    # 总时长允许范围：目标 ±5 秒
    target_duration = max_total_seconds
    min_total = max(0.1, target_duration - 5.0)
    max_total = target_duration + 5.0

    # 预分配总延迟预算（排除按键本身耗时）
    base_budget = uniform_between(min_total, max_total)
    used_delay = 0.0

    wrong_chars = "abcdefghijklmnopqrstuvwxyz0123456789;',./[]<>?!@#$%^&*()"

    for i, c in enumerate(char_list):
        if not is_running:
            break

        # 随机错字
        if random.random() > config["accuracy"] and c.isprintable():
            human_press_char(random.choice(wrong_chars))
            used_delay += uniform_between(config["base_delay_min"], config["base_delay_max"])

        # 输入当前字符
        if c == "\n":
            human_press_char(Key.enter)
        else:
            human_press_char(c)

        # 计算当前应停顿的延迟（随机快慢）
        current_delay = random_human_delay()

        # 标点加长停顿
        if c in "。，、；：？！,.?!\n":
            current_delay *= config["punct_pause"]

        # 剩余字符与剩余预算
        remaining_chars = total_chars - i - 1
        remaining_budget = max(0.0, base_budget - used_delay)

        # 动态平衡：保证最后不爆、不提前结束
        if remaining_chars > 0:
            avg_per_char = remaining_budget / remaining_chars
            current_delay = min(current_delay, avg_per_char * 1.8)
            current_delay = max(current_delay, avg_per_char * 0.3)
        else:
            current_delay = remaining_budget

        current_delay = max(current_delay, 0.001)
        used_delay += current_delay
        time.sleep(current_delay)

    # 最终兜底，严格锁在目标±5s
    real_elapsed = time.perf_counter() - start_time
    if real_elapsed < min_total:
        time.sleep(min_total - real_elapsed)
    elif real_elapsed > max_total:
        pass

    # 结束
    is_running = False
    final_real = time.perf_counter() - start_time
    status_label.config(text=f"完成 | 实际用时{final_real:.2f}s")
    threading.Timer(1.5, lambda: status_label.config(text="✅ 就绪，按F8触发")).start()

# ==================== 键盘监听 ====================
def on_press(key):
    global is_running
    try:
        if key == TRIGGER_KEY and not is_running:
            threading.Thread(target=type_human_like, daemon=True).start()
    except:
        pass

def run_listener():
    global listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    listener.join()

# ==================== 高级设置 ====================
def open_advanced():
    adv = tk.Toplevel()
    adv.title("高级设置")
    adv.geometry("460x460")
    adv.resizable(0,0)

    ttk.Label(adv, text="正确率").pack(pady=4)
    acc_frame = ttk.Frame(adv)
    acc_frame.pack(fill="x", padx=30)
    acc_var = tk.DoubleVar(value=config["accuracy"]*100)
    acc_spin = ttk.Spinbox(
        acc_frame, from_=0.001, to=100.0, increment=0.001,
        textvariable=acc_var, font=("Consolas",11)
    )
    acc_spin.pack(fill="x", pady=2)
    ttk.Label(acc_frame, text="%").pack(side="right", padx=5)

    ttk.Label(adv, text="基础最大延迟（越小越快）").pack(pady=4)
    bd_var = tk.DoubleVar(value=config["base_delay_max"])
    bd_spin = ttk.Spinbox(adv, from_=0.01, to=0.8, increment=0.005, textvariable=bd_var)
    bd_spin.pack(fill="x", padx=30, pady=2)

    ttk.Label(adv, text="标点停顿倍数").pack(pady=4)
    pt_var = tk.DoubleVar(value=config["punct_pause"])
    pt_spin = ttk.Spinbox(adv, from_=1.0, to=5.0, increment=0.1, textvariable=pt_var)
    pt_spin.pack(fill="x", padx=30, pady=2)

    ttk.Label(adv, text="按键按下最大时长").pack(pady=4)
    kp_var = tk.DoubleVar(value=config["key_press_max"])
    kp_spin = ttk.Spinbox(adv, from_=0.002, to=0.15, increment=0.001, textvariable=kp_var)
    kp_spin.pack(fill="x", padx=30, pady=2)

    def apply():
        try:
            config["accuracy"] = float(acc_var.get()) / 100.0
            config["base_delay_max"] = float(bd_var.get())
            config["base_delay_min"] = config["base_delay_max"] * 0.5
            config["punct_pause"] = float(pt_var.get())
            config["key_press_max"] = float(kp_var.get())
            config["key_press_min"] = config["key_press_max"] * 0.4
            save_config()
            messagebox.showinfo("成功", "设置已保存！")
            adv.destroy()
        except:
            messagebox.showerror("错误", "输入无效")

    ttk.Button(adv, text="保存并应用", command=apply).pack(pady=20)
    adv.mainloop()

# ==================== 主控制 ====================
def start_listen():
    global listener, max_total_seconds
    try:
        max_total_seconds = float(duration_entry.get())
        if max_total_seconds < 0.1:
            max_total_seconds = 0.1
            duration_entry.delete(0, tk.END)
            duration_entry.insert(0, "0.1")
        config["default_duration"] = max_total_seconds
        save_config()
    except:
        messagebox.showwarning("警告", "请输入有效数字")
        return

    if listener is None or not listener.running:
        status_label.config(text=f"已启动 | {max_total_seconds:.2f}秒内完成")
        start_btn.config(state=tk.DISABLED)
        stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=run_listener, daemon=True).start()

def stop_listen():
    global listener, is_running
    is_running = False
    if listener and listener.running:
        listener.stop()
    listener = None
    start_btn.config(state=tk.NORMAL)
    stop_btn.config(state=tk.DISABLED)
    status_label.config(text="已停止")

def show_guide():
    g = tk.Toplevel()
    g.title("使用教程")
    g.geometry("580x460")
    t = tk.Text(g, font=("微软雅黑",11), wrap="word")
    t.pack(fill="both", expand=1, padx=10, pady=10)
    t.insert("end","""
Tops打字竞速工具 使用教程
1. 软件自动读取同目录 data.dat 内的所有代码模块
2. 可选择预设模块 或 使用自定义 text.txt 文本
3. 设置总时长（最低0.1秒，严格控制误差≤5秒）
4. 点击启动监听，切换到输入页面按 F8 开始输入
5. 高级设置可调节：正确率(0.001%精度)、打字速度、按键时长
6. 所有设置自动本地保存，下次打开自动恢复
""")
    t.config(state="disabled")

# ==================== 主界面 ====================
load_config()
root = tk.Tk()
root.title("Tops打字竞速工具")
root.geometry("425x250")
root.resizable(0,0)

padx = 12
pady = 8

ttk.Label(root, text="选择内容：").grid(row=0,column=0,padx=padx,pady=pady,sticky="e")
content_combo = ttk.Combobox(root, width=28, font=("微软雅黑",9), state="readonly")
content_combo.grid(row=0,column=1,columnspan=3,padx=padx,pady=pady)

ttk.Label(root, text="总时长(秒)：").grid(row=1,column=0,padx=padx,pady=pady,sticky="e")
duration_entry = ttk.Entry(root, width=10)
duration_entry.grid(row=1,column=1,padx=padx,pady=pady)
duration_entry.insert(0, f"{config['default_duration']:.2f}")

start_btn   = ttk.Button(root, text="启动监听", width=12, command=start_listen)
stop_btn    = ttk.Button(root, text="停止监听", width=12, command=stop_listen, state=tk.DISABLED)
guide_btn   = ttk.Button(root, text="使用教程", width=12, command=show_guide)
adv_btn     = ttk.Button(root, text="高级设置", width=12, command=open_advanced)

start_btn.grid(row=2,column=0,padx=6,pady=14)
stop_btn.grid(row=2,column=1,padx=6,pady=14)
guide_btn.grid(row=2,column=2,padx=6,pady=14)
adv_btn.grid(row=2,column=3,padx=6,pady=14)

file_btn = ttk.Button(root, text="打开自定义文档", width=28, command=open_text_file)
file_btn.grid(row=3,column=0,columnspan=4,pady=6)

status_label = ttk.Label(root, text="✅ 就绪，按F8触发", font=("微软雅黑",12), foreground="#0066cc")
status_label.grid(row=4,column=0,columnspan=4,pady=16)

load_data_dat()
content_combo.config(values=list(content_data.keys()))
if content_data:
    content_combo.current(0)

root.protocol("WM_DELETE_WINDOW", lambda: (stop_listen(), save_config(), root.destroy()))
root.mainloop()
