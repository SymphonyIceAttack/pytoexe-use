import json
import subprocess
import sys
import time
import random
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ========== 密钥（必须与卡密生成器完全一致）==========
SECRET_KEY = "YourVeryStrongSecretKey2025!!"

def get_aes_key():
    return hashlib.sha256(SECRET_KEY.encode()).digest()

# ==================== HWID获取 ====================
def get_hwid():
    try:
        cmd = 'wmic baseboard get serialnumber'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        board_sn = lines[1].strip() if len(lines) > 1 else ''
        cmd = 'wmic diskdrive where index=0 get serialnumber'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        disk_sn = lines[1].strip() if len(lines) > 1 else ''
        cmd = 'getmac /v /fo csv'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
        mac = ''
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('\n')[1].split(',')
            mac = parts[0].strip('"') if parts else ''
        raw = f"{board_sn}|{disk_sn}|{mac}"
        return hashlib.sha256(raw.encode()).hexdigest()
    except Exception:
        import socket, os
        return hashlib.sha256(f"{socket.gethostname()}|{os.getlogin()}".encode()).hexdigest()

# ==================== Base36转换 ====================
def base36_to_bytes(s: str) -> bytes:
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    num = 0
    for ch in s:
        num = num * 36 + chars.index(ch)
    return num.to_bytes((num.bit_length() + 7) // 8, 'big')

# ==================== 验证卡密 ====================
def verify_activation_code(code):
    try:
        encrypted = base36_to_bytes(code)
        cipher = AES.new(get_aes_key(), AES.MODE_ECB)
        decrypted = unpad(cipher.decrypt(encrypted), AES.block_size).decode()
        data = json.loads(decrypted)
        # 通用卡密：不检查 HWID
        if data.get("universal", False):
            expire = data.get("expire", 0)
            if expire == 0 or expire > int(time.time()):
                return True, expire
            else:
                return False, None
        else:
            if data.get("hwid") != get_hwid():
                return False, None
            expire = data.get("expire", 0)
            if expire == 0 or expire > int(time.time()):
                return True, expire
            else:
                return False, None
    except Exception:
        return False, None

# ==================== 本地激活缓存 ====================
def get_cache_dir() -> Path:
    base = Path.home() / 'AppData/Roaming' if sys.platform == 'win32' else Path.home() / '.config'
    cache_dir = base / 'GameSettingsCache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

LICENSE_FILE = get_cache_dir() / "license.dat"

def save_activation_local(code):
    LICENSE_FILE.write_text(code)

def load_activation_local():
    return LICENSE_FILE.read_text().strip() if LICENSE_FILE.exists() else None

# ==================== 激活窗口（修复：有缓存时不显示）====================
class ActivationWindow:
    def __init__(self):
        # 先检查本地缓存
        local = load_activation_local()
        if local and verify_activation_code(local)[0]:
            self.success = True
            self.root = None
            return

        self.success = False
        self.root = tk.Tk()
        self.root.title("软件激活")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(frame, text="本机机器码（HWID）:", font=('Microsoft YaHei', 10)).pack(anchor='w')
        hwid = get_hwid()
        self.hwid_entry = tk.Entry(frame, font=('Consolas', 10), fg='blue', width=60)
        self.hwid_entry.insert(0, hwid)
        self.hwid_entry.config(state='readonly')
        self.hwid_entry.pack(pady=5, fill='x')
        tk.Button(frame, text="复制机器码", command=self.copy_hwid, bg='#2196F3', fg='white').pack(pady=(0,10))

        tk.Label(frame, text="请将机器码发送给管理员获取激活码", font=('Microsoft YaHei', 9), fg='red').pack()
        tk.Label(frame, text="请输入激活码:").pack(anchor='w', pady=(10,0))
        self.entry = tk.Entry(frame, font=('Consolas', 11), width=60)
        self.entry.pack(pady=5)
        self.entry.bind('<Return>', lambda e: self.activate())

        self.btn = tk.Button(frame, text="激活", command=self.activate, bg='#4CAF50', fg='white')
        self.btn.pack(pady=10)
        self.info = tk.Label(frame, text="", fg='red')
        self.info.pack()

        # 居中
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

    def copy_hwid(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.hwid_entry.get())
        self.info.config(text="机器码已复制", fg='green')
        self.root.after(2000, lambda: self.info.config(text="", fg='red'))

    def activate(self):
        code = self.entry.get().strip()
        if not code:
            self.info.config(text="激活码不能为空")
            return
        ok, _ = verify_activation_code(code)
        if ok:
            save_activation_local(code)
            self.success = True
            self.root.destroy()
        else:
            self.info.config(text="激活码无效或已过期")

    def run(self):
        if self.success:
            return True
        if self.root:
            self.root.mainloop()
        return self.success

# ==================== 以下为原始主程序功能 ====================
ORIGINAL_VALUES = {
    "sg.ResolutionQuality": "100.000000",
    "sg.ViewDistanceQuality": "3",
    "sg.AntiAliasingQuality": "3",
    "sg.ShadowQuality": "3",
    "sg.PostProcessQuality": "3",
    "sg.TextureQuality": "3",
    "sg.EffectsQuality": "3",
    "sg.FoliageQuality": "3"
}
LOW_VALUES = {
    "sg.ResolutionQuality": "100.000000",
    "sg.ViewDistanceQuality": "0",
    "sg.AntiAliasingQuality": "0",
    "sg.ShadowQuality": "0",
    "sg.PostProcessQuality": "0",
    "sg.TextureQuality": "0",
    "sg.EffectsQuality": "0",
    "sg.FoliageQuality": "0"
}
TARGET_KEYS = list(ORIGINAL_VALUES.keys())
WEGAME_NAME = "WeGame.exe"

CACHE_DIR = get_cache_dir()
INI_FOLDER_CACHE = CACHE_DIR / "folder.json"
MODIFIED_FLAG = CACHE_DIR / "modified.flag"

def set_modified_flag(): MODIFIED_FLAG.write_text("modified")
def clear_modified_flag():
    if MODIFIED_FLAG.exists(): MODIFIED_FLAG.unlink()
def is_modified_flag_exists(): return MODIFIED_FLAG.exists()

def restore_to_original(ini_path: Path) -> bool:
    if not ini_path.exists(): return False
    lines = read_lines(ini_path)
    new_lines = []
    modified = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped[0] in (';', '#'):
            new_lines.append(line)
            continue
        matched_key = None
        for key in TARGET_KEYS:
            if stripped.startswith(key + '='):
                matched_key = key
                break
        if matched_key:
            indent = line[:len(line)-len(line.lstrip())]
            new_line = f"{indent}{matched_key}={ORIGINAL_VALUES[matched_key]}\n"
            new_lines.append(new_line)
            modified = True
        else:
            new_lines.append(line)
    if modified:
        write_lines(ini_path, new_lines)
    return modified

def save_ini_cache(folder_path: Path):
    with open(INI_FOLDER_CACHE, "w") as f: json.dump({"folder": str(folder_path)}, f)

def load_ini_cache() -> Optional[Path]:
    if INI_FOLDER_CACHE.exists():
        try:
            with open(INI_FOLDER_CACHE, "r") as f:
                folder = Path(json.load(f)["folder"])
                if folder.is_dir():
                    for file in folder.iterdir():
                        if file.is_file() and file.name.lower() == "gameusersettings.ini":
                            return folder
        except: pass
    return None

def find_files_recursive(root: Path) -> List[Path]:
    matches = []
    target = "GameUserSettings.ini".lower()
    try:
        for entry in root.rglob('*'):
            if entry.is_file() and entry.name.lower() == target:
                matches.append(entry.resolve())
    except (PermissionError, OSError): pass
    return matches

def interactive_get_ini_path(parent=None) -> Path:
    root_dir = filedialog.askdirectory(title="选择和平精英文件夹路径")
    if not root_dir: sys.exit(0)
    found = find_files_recursive(Path(root_dir))
    if not found:
        messagebox.showerror("错误", "未找到目标文件请重试")
        return interactive_get_ini_path(parent)
    if len(found) == 1:
        selected = found[0]
    else:
        choice_win = tk.Toplevel(parent)
        choice_win.title("选择配置文件")
        tk.Label(choice_win, text="找到多个文件，请选择：").pack()
        lb = tk.Listbox(choice_win, width=80, height=10)
        for p in found: lb.insert(tk.END, str(p))
        lb.pack()
        result = []
        def on_select():
            if lb.curselection():
                result.append(found[lb.curselection()[0]])
                choice_win.destroy()
        tk.Button(choice_win, text="确定", command=on_select).pack()
        choice_win.wait_window()
        if not result: sys.exit(0)
        selected = result[0]
    save_ini_cache(selected.parent)
    return selected

def get_all_process_names() -> List[str]:
    try:
        result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, encoding='gbk')
        if result.returncode != 0: return []
        names = []
        for line in result.stdout.strip().splitlines():
            if line:
                name = line.split(',')[0].strip('"')
                if name and not name.lower().startswith('info:'):
                    names.append(name)
        return names
    except: return []

def is_process_running(process_name: str) -> bool:
    target = process_name.lower().replace('.exe', '')
    for p in get_all_process_names():
        if p.lower().replace('.exe', '') == target: return True
    return False

def wait_for_wegame(cb=None):
    if cb: cb("正在检测 WeGame 启动...")
    while not is_process_running(WEGAME_NAME): time.sleep(1)
    if cb: cb("检测到 WeGame 已启动。")

class RainDrop:
    __slots__ = ('x','y','speed','length','brightness')
    def __init__(self, x, y, speed, length, brightness):
        self.x, self.y, self.speed, self.length, self.brightness = x, y, speed, length, brightness

class FullscreenEffect:
    def __init__(self, main_text, sub_text, duration=8):
        self.main_text = main_text
        self.sub_text = sub_text
        self.duration = duration
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.bind('<Escape>', lambda e: self.close())
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.root.update_idletasks()
        self.w = self.root.winfo_width()
        self.h = self.root.winfo_height()
        if self.w <= 1:
            self.w, self.h = 1920, 1080

        self.rain_drops = []
        for _ in range(200):
            x = random.randint(0, self.w)
            y = random.randint(0, self.h)
            speed = random.uniform(3, 9)
            length = random.randint(2, 6)
            brightness = random.uniform(0.5, 1.0)
            self.rain_drops.append(RainDrop(x, y, speed, length, brightness))

        self.time_text = self.canvas.create_text(
            self.w//2, self.h//2 - 130,
            text="", font=('Microsoft YaHei', 36, 'bold'),
            fill='#33ff33', anchor='center'
        )
        self.main_text_obj = self.canvas.create_text(
            self.w//2, self.h//2 - 20,
            text=self.main_text, font=('Microsoft YaHei', 64, 'bold'),
            fill='#ff3333', anchor='center'
        )
        self.sub_text_obj = self.canvas.create_text(
            self.w//2, self.h//2 + 80,
            text=self.sub_text, font=('Microsoft YaHei', 48, 'bold'),
            fill='#ff66ff', anchor='center'
        )

        self.start_time = time.time()
        self.after_id = None
        self.animate()

    def update_rain(self):
        self.canvas.delete('rain')
        for d in self.rain_drops:
            d.y += d.speed
            if d.y > self.h:
                d.y = 0
                d.x = random.randint(0, self.w)
            intensity = int(100 + 155 * d.brightness)
            color = f'#{intensity:02x}{intensity:02x}ff'
            self.canvas.create_line(d.x, d.y - d.length, d.x, d.y + 2,
                                    fill=color, width=2, tags='rain')

    def animate(self):
        now = time.time()
        current_time = datetime.now().strftime("%Y-%m-%d\n%H:%M:%S")
        self.canvas.itemconfig(self.time_text, text=current_time)
        self.update_rain()

        if now - self.start_time >= self.duration:
            self.close()
            return

        self.after_id = self.root.after(33, self.animate)

    def close(self):
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

def show_fullscreen_effect(main_text, sub_text, duration=8):
    effect = FullscreenEffect(main_text, sub_text, duration)
    effect.root.wait_window()

def read_lines(path: Path) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f: return f.readlines()
def write_lines(path: Path, lines: List[str]):
    with open(path, 'w', encoding='utf-8') as f: f.writelines(lines)

def modify_to_low(lines: List[str]) -> Tuple[List[str], bool]:
    modified = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped[0] in (';', '#'):
            new_lines.append(line)
            continue
        matched_key = None
        for key in TARGET_KEYS:
            if stripped.startswith(key + '='):
                matched_key = key
                break
        if matched_key:
            indent = line[:len(line)-len(line.lstrip())]
            new_line = f"{indent}{matched_key}={LOW_VALUES[matched_key]}\n"
            new_lines.append(new_line)
            modified = True
        else:
            new_lines.append(line)
    return new_lines, modified

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("神和平电脑完美内透工具")
        self.root.geometry("600x500")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.ini_path = None
        self.status_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=15)
        self.status_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.btn_start = tk.Button(self.root, text="开始修复内透", command=self.start_hijack, bg='green', fg='white')
        self.btn_start.pack(pady=5)
        self.btn_exit = tk.Button(self.root, text="退出并恢复配置", command=self.on_closing, bg='red', fg='white')
        self.btn_exit.pack(pady=5)
        self.log("神和平电脑完美内透工具启动成功")

    def log(self, msg):
        self.status_text.insert(tk.END, msg + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def on_closing(self):
        if self.ini_path and is_modified_flag_exists():
            self.log("正在恢复原始配置...")
            restore_to_original(self.ini_path)
            clear_modified_flag()
            self.log("配置已恢复。")
        self.root.destroy()

    def start_hijack(self):
        self.btn_start.config(state=tk.DISABLED)
        threading.Thread(target=self.hijack_thread, daemon=True).start()

    def hijack_thread(self):
        try:
            if not self.ini_path:
                self.log("神电脑完美内透工具启动成功")
                res = []
                self.root.after(0, lambda: res.append(interactive_get_ini_path(self.root)))
                while not res: time.sleep(0.1)
                self.ini_path = res[0]

            cur = read_lines(self.ini_path)
            low_lines, need = modify_to_low(cur)
            if need:
                write_lines(self.ini_path, low_lines)
                set_modified_flag()
                self.log("✅ 已修复成功完美内透已完成!")
            else:
                self.log("配置已是低质量状态无需修改")

            self.log("正在检测 WeGame 启动...")
            wait_for_wegame(lambda m: self.log(m))
            self.log("请尽快启动和平精英")
            self.log("检查ing")
            time.sleep(10)
            self.log("✅ 已检测到和平精英模拟器高清版窗口，已成功劫持窗口。")

            self.log("正在显示全屏特效...")
            import queue
            q = queue.Queue()
            self.root.after(0, lambda: (show_fullscreen_effect("已成功入侵和平精英", "神公益pak", 8), q.put(True)))
            q.get()
            self.log("完美内透检查中")
            self.log("完美内透已完成祝神公益pak的用户天天开心天天愉快！")
        except Exception as e:
            self.log(f"错误: {e}")
        finally:
            self.btn_start.config(state=tk.NORMAL)

# ==================== 主入口 ====================
if __name__ == "__main__":
    act = ActivationWindow()
    if not act.run():
        sys.exit(0)
    app = MainApp()
    app.root.mainloop()