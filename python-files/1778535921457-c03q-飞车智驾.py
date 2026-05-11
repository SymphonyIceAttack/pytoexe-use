import os
import shutil
import tkinter as tk
from tkinter import messagebox, ttk

# ---------- 全局配置 ----------
APP_TITLE = "飞车智驾"
VALID_KEY_PERM = "639285710046"
VALID_KEY_7D = "729510384621"
VALID_KEY_30D = "936285710524"

SRC_YUN = "云淡风清"
SRC_MIRL = "mirl"
C_TARGET = "C:\\云淡风清"
GAME_BOOT = "QQSpeed_loader.exe"
CONFIG_FILE = "pz.ini"

# 默认键位（按你给的DIK表）
DEFAULT_KEYS = {
    "左": 203,
    "右": 205,
    "上": 200,
    "下": 208,
    "漂移": 42,
    "放气": 29,
    "复位": 19,
    "小喷": 17
}

# DIK键码映射（部分常用键，按你的表）
DIK_MAP = {
    "ESC":1, "F1":59, "F2":60, "F3":61, "F4":62, "F5":63, "F6":64, "F7":65, "F8":66, "F9":67, "F10":68, "F11":87, "F12":88,
    "`~":41, "1":2, "2":3, "3":4, "4":5, "5":6, "6":7, "7":8, "8":9, "9":10, "0":11, "-":12, "=":13, "Backspace":14,
    "Tab":15, "Q":16, "W":17, "E":18, "R":19, "T":20, "Y":21, "U":22, "I":23, "O":24, "P":25, "[":26, "]":27, "Enter":28,
    "LCtrl":29, "A":30, "S":31, "D":32, "F":33, "G":34, "H":35, "J":36, "K":37, "L":38, ";":39, "'":40, "Caps":58,
    "LShift":42, "\\":43, "Z":44, "X":45, "C":46, "V":47, "B":48, "N":49, "M":50, ",":51, ".":52, "/":53, "RShift":54,
    "LAlt":56, "LWin":219, "Space":57, "RAlt":184, "RWin":220, "Apps":221, "RCtrl":157,
    "Up":200, "Left":203, "Down":208, "Right":205,
    "NumLk":69, "Num/":181, "Num*":55, "Num-":74,
    "Num7":71, "Num8":72, "Num9":73, "Num+":78,
    "Num4":75, "Num5":76, "Num6":77, "NumEnt":156,
    "Insert":210, "Home":199, "PgUp":201, "Delete":211, "End":207, "PgDn":209
}
# 反向映射：根据码找键名
CODE_TO_KEY = {v:k for k,v in DIK_MAP.items()}
# ----------------------------

def find_qq_speed():
    drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    for drive in drives:
        for path, _, files in os.walk(drive):
            if GAME_BOOT in files:
                return path
    return None

def clear_files():
    if os.path.exists(C_TARGET):
        shutil.rmtree(C_TARGET, ignore_errors=True)
    game_path = find_qq_speed()
    if game_path:
        p64 = os.path.join(os.path.dirname(game_path), "Releasephysx27_64")
        mirl_p = os.path.join(p64, SRC_MIRL)
        if os.path.exists(mirl_p):
            shutil.rmtree(mirl_p, ignore_errors=True)

def save_pz_ini(key_config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("[key]\n")
        for name, code in key_config.items():
            f.write(f"{name}={code}\n")
    messagebox.showinfo("配置保存", "键位配置已保存！")

def deploy_files():
    game_path = find_qq_speed()
    if not game_path:
        messagebox.showerror("提示", "未检测到QQ飞车！")
        return False
    p_parent = os.path.dirname(game_path)
    p_64 = os.path.join(p_parent, "Releasephysx27_64")
    os.makedirs(p_64, exist_ok=True)
    try:
        if os.path.exists(SRC_YUN):
            shutil.copytree(SRC_YUN, C_TARGET, dirs_exist_ok=True)
        if os.path.exists(SRC_MIRL):
            shutil.copytree(SRC_MIRL, os.path.join(p_64, SRC_MIRL), dirs_exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            shutil.copy(CONFIG_FILE, os.path.join(p_64, CONFIG_FILE))
        return True
    except Exception as e:
        print(e)
        clear_files()
        messagebox.showerror("失败", "部署失败，已自动清理文件")
        return False

def check_and_deploy():
    key = entry.get().strip()
    ok_keys = {VALID_KEY_PERM, VALID_KEY_7D, VALID_KEY_30D}
    if key not in ok_keys:
        messagebox.showerror("错误", "卡密无效！")
        return
    # 先保存当前键位配置
    current_keys = {k:int(v.get()) for k,v in key_vars.items()}
    save_pz_ini(current_keys)
    # 部署文件
    if deploy_files():
        messagebox.showinfo("成功", "部署完成！可正常启动游戏")

# ---------------- 界面 ----------------
root = tk.Tk()
root.title(APP_TITLE)
root.geometry("450x400")
root.resizable(False, False)

# 卡密输入区
frame_key = ttk.LabelFrame(root, text="卡密验证")
frame_key.pack(fill="x", padx=10, pady=10)
tk.Label(frame_key, text="请输入卡密：").pack(side="left", padx=5)
entry = ttk.Entry(frame_key, width=30)
entry.pack(side="left", padx=5)

# 改键配置区
frame_keys = ttk.LabelFrame(root, text="自定义键位配置（DIK十进制）")
frame_keys.pack(fill="both", expand=True, padx=10, pady=10)

key_vars = {}
key_names = ["左", "右", "上", "下", "漂移", "放气", "复位", "小喷"]
for i, name in enumerate(key_names):
    tk.Label(frame_keys, text=f"{name}：").grid(row=i//2, column=(i%2)*2, padx=5, pady=5, sticky="w")
    var = tk.StringVar(value=str(DEFAULT_KEYS[name]))
    entry_key = ttk.Entry(frame_keys, textvariable=var, width=10)
    entry_key.grid(row=i//2, column=(i%2)*2+1, padx=5, pady=5, sticky="w")
    key_vars[name] = var

# 按钮区
frame_btn = ttk.Frame(root)
frame_btn.pack(pady=10)
ttk.Button(frame_btn, text="一键部署", command=check_and_deploy, width=15).pack(side="left", padx=10)
ttk.Button(frame_btn, text="恢复默认键位", command=lambda: [v.set(str(DEFAULT_KEYS[k])) for k,v in key_vars.items()], width=15).pack(side="left", padx=10)

root.mainloop()