# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import threading
import time
import hmac
import hashlib
import base64
import requests
from itertools import cycle
import os
import json

# ========== 固定进入密钥 ==========
ACCESS_PASSWORD = "chenchenzixun"
# ==================================

CONFIG_FOLDER = "robot_configs"
ding_cycle = None
feishu_cycle = None
local_img_path = ""
current_config = "默认配置"

if not os.path.exists(CONFIG_FOLDER):
    os.mkdir(CONFIG_FOLDER)

def get_config_list():
    files = [f.replace(".json", "") for f in os.listdir(CONFIG_FOLDER) if f.endswith(".json")]
    return files if files else ["默认配置"]

def get_config_path(name):
    return os.path.join(CONFIG_FOLDER, f"{name}.json")

def save_config(name=None):
    global current_config
    if not name:
        name = current_config
    current_config = name
    config = {
        "remark": remark_entry.get("1.0", tk.END).strip(),
        "ding_robots": entry_ding.get("1.0", tk.END).strip(),
        "feishu_robots": entry_feishu.get("1.0", tk.END).strip()
    }
    try:
        with open(get_config_path(name), "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        update_config_list()
        log(f"配置「{name}」已保存")
    except Exception as e:
        log(f"保存失败：{str(e)}")

def load_config(name):
    global current_config
    path = get_config_path(name)
    if not os.path.exists(path):
        messagebox.showwarning("提示", "配置不存在")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        remark_entry.delete("1.0", tk.END)
        entry_ding.delete("1.0", tk.END)
        entry_feishu.delete("1.0", tk.END)
        remark_entry.insert("1.0", cfg.get("remark", ""))
        entry_ding.insert("1.0", cfg.get("ding_robots", ""))
        entry_feishu.insert("1.0", cfg.get("feishu_robots", ""))
        current_config = name
        update_config_list()
        log(f"已加载配置「{name}」")
    except Exception as e:
        log(f"加载失败：{str(e)}")

def delete_config(name):
    if name == "默认配置":
        messagebox.showwarning("提示", "默认配置不能删除")
        return
    if not messagebox.askyesno("确认", f"确定要删除配置「{name}」吗？"):
        return
    try:
        os.remove(get_config_path(name))
        update_config_list()
        load_config("默认配置")
        log(f"配置「{name}」已删除")
    except Exception as e:
        log(f"删除失败：{str(e)}")

def update_config_list():
    config_list = get_config_list()
    combo_config["values"] = config_list
    if current_config in config_list:
        combo_config.set(current_config)
    else:
        combo_config.set("默认配置")

def new_config():
    name = simpledialog.askstring("新建配置", "输入配置名称：")
    if not name:
        return
    if name in get_config_list():
        messagebox.showwarning("提示", "配置名已存在")
        return
    save_config(name)

def get_ding_sign(secret):
    timestamp = str(round(time.time() * 1000))
    data = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
    return timestamp, base64.b64encode(hmac_code).decode()

def get_feishu_sign(secret):
    timestamp = int(time.time())
    data = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
    return timestamp, base64.b64encode(hmac_code).decode()

def upload_local_image(file_path):
    try:
        url = "https://imgchr.com/api/upload"
        files = {"source": open(file_path, "rb")}
        res = requests.post(url, files=files, timeout=15).json()
        if res.get("success"):
            return res["data"]["url"]
    except Exception as e:
        log(f"图片上传失败: {str(e)}")
    return None

def init_robots(ding_txt, feishu_txt):
    global ding_cycle, feishu_cycle
    ding_list = []
    for line in [l.strip() for l in ding_txt.splitlines() if l.strip()]:
        if "#" in line:
            h, s = line.split("#", 1)
            ding_list.append({"hook": h.strip(), "secret": s.strip()})
        else:
            ding_list.append({"hook": line.strip(), "secret": ""})
    ding_cycle = cycle(ding_list) if ding_list else None

    feishu_list = []
    for line in [l.strip() for l in feishu_txt.splitlines() if l.strip()]:
        if "#" in line:
            h, s = line.split("#", 1)
            feishu_list.append({"hook": h.strip(), "secret": s.strip()})
        else:
            feishu_list.append({"hook": line.strip(), "secret": ""})
    feishu_cycle = cycle(feishu_list) if feishu_list else None

def send_ding_text(msg):
    if not ding_cycle:
        return
    try:
        bot = next(ding_cycle)
        hook = bot["hook"]
        sec = bot["secret"]
        data = {"msgtype": "text", "text": {"content": msg}}
        if sec:
            t, sign = get_ding_sign(sec)
            url = f"{hook}&timestamp={t}&sign={sign}"
        else:
            url = hook
        requests.post(url, json=data, timeout=8)
    except:
        pass

def send_ding_img(img_url):
    if not ding_cycle:
        return
    try:
        bot = next(ding_cycle)
        hook = bot["hook"]
        sec = bot["secret"]
        data = {"msgtype": "image", "image": {"pic_url": img_url}}
        if sec:
            t, sign = get_ding_sign(sec)
            url = f"{hook}&timestamp={t}&sign={sign}"
        else:
            url = hook
        requests.post(url, json=data, timeout=10)
    except:
        pass

def send_feishu_text(msg):
    if not feishu_cycle:
        return
    try:
        bot = next(feishu_cycle)
        hook = bot["hook"]
        sec = bot["secret"]
        payload = {"msg_type": "text", "content": {"text": msg}}
        if sec:
            t, sign = get_feishu_sign(sec)
            payload["timestamp"] = t
            payload["sign"] = sign
        requests.post(hook, json=payload, timeout=8)
    except:
        pass

def send_feishu_img(img_url):
    if not feishu_cycle:
        return
    try:
        bot = next(feishu_cycle)
        hook = bot["hook"]
        sec = bot["secret"]
        payload = {"msg_type": "image", "content": {"image_key": img_url}}
        if sec:
            t, sign = get_feishu_sign(sec)
            payload["timestamp"] = t
            payload["sign"] = sign
        requests.post(hook, json=payload, timeout=10)
    except:
        pass

def select_local_image():
    global local_img_path
    path = filedialog.askopenfilename(title="选择图片", filetypes=[("图片", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
    if path:
        local_img_path = path
        img_label.config(text=f"已选择：{os.path.basename(path)}")

def clear_image():
    global local_img_path
    local_img_path = ""
    img_label.config(text="未选择图片")

def send_current_config():
    msg = text_msg.get("1.0", tk.END).strip()
    net_img = entry_net_img.get().strip()
    ding_txt = entry_ding.get("1.0", tk.END).strip()
    feishu_txt = entry_feishu.get("1.0", tk.END).strip()

    save_config()

    if not msg and not net_img and not local_img_path:
        messagebox.showwarning("提示", "请输入文字或选择图片")
        return

    init_robots(ding_txt, feishu_txt)
    log(f"正在发送【{current_config}】...")

    def run():
        if msg:
            send_ding_text(msg)
            send_feishu_text(msg)
        if net_img:
            send_ding_img(net_img)
            send_feishu_img(net_img)
        if local_img_path:
            log("正在上传本地图片...")
            online_url = upload_local_image(local_img_path)
            if online_url:
                log(f"上传成功：{online_url}")
                send_ding_img(online_url)
                send_feishu_img(online_url)
            else:
                log("上传失败")
        log(f"【{current_config}】发送完成！")

    threading.Thread(target=run, daemon=True).start()

def log(text):
    log_box.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
    log_box.see(tk.END)

def on_close():
    save_config()
    root.destroy()

def check_password():
    pwd = simpledialog.askstring("请验证身份", "请输入进入密钥：", show='*')
    if pwd is None:
        root.quit()
        exit()
    if pwd != ACCESS_PASSWORD:
        messagebox.showerror("错误", "密钥不正确，无法使用工具！")
        root.quit()
        exit()
    messagebox.showinfo("验证成功", "密钥正确，欢迎使用！")

# ==================== 界面 ====================
root = tk.Tk()
root.title("钉钉飞书群发工具")
root.geometry("740x850")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_close)

check_password()

frame_top = tk.Frame(root)
frame_top.pack(fill=tk.X, padx=10, pady=5)
tk.Label(frame_top, text="配置文件：").pack(side=tk.LEFT, padx=5)
combo_config = ttk.Combobox(frame_top, width=18, state="readonly")
combo_config.pack(side=tk.LEFT, padx=5)
ttk.Button(frame_top, text="加载", command=lambda: load_config(combo_config.get())).pack(side=tk.LEFT, padx=3)
ttk.Button(frame_top, text="保存", command=lambda: save_config()).pack(side=tk.LEFT, padx=3)
ttk.Button(frame_top, text="新建", command=new_config).pack(side=tk.LEFT, padx=3)
ttk.Button(frame_top, text="删除", command=lambda: delete_config(combo_config.get())).pack(side=tk.LEFT, padx=3)

frame_remark = tk.Frame(root)
frame_remark.pack(fill=tk.X, padx=10, pady=3)
tk.Label(frame_remark, text="配置备注（可修改标记用途）：", fg="red", font=("",10,"bold")).pack(anchor="w")
remark_entry = tk.Text(frame_remark, width=100, height=2)
remark_entry.pack(fill=tk.X, pady=2)

frame_robots = tk.Frame(root)
frame_robots.pack(fill=tk.X, padx=10, pady=5)

frame_ding = tk.Frame(frame_robots)
frame_ding.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)
tk.Label(frame_ding, text="钉钉机器人（webhook#密钥 一行一个）", fg="#0070E0", font=("",9,"bold")).pack(anchor="w")
entry_ding = tk.Text(frame_ding, width=42, height=10)
entry_ding.pack(fill=tk.BOTH, expand=True, pady=3)

frame_feishu = tk.Frame(frame_robots)
frame_feishu.pack(side=tk.RIGHT, padx=5, fill=tk.BOTH, expand=True)
tk.Label(frame_feishu, text="飞书机器人（webhook#密钥 一行一个）", fg="#00B570", font=("",9,"bold")).pack(anchor="w")
entry_feishu = tk.Text(frame_feishu, width=42, he