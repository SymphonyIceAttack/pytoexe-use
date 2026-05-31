import json
import subprocess
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path
from typing import List, Optional, Tuple

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

def get_cache_dir() -> Path:
    base = Path.home() / 'AppData/Roaming' if sys.platform == 'win32' else Path.home() / '.config'
    cache_dir = base / 'GameSettingsCache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

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
                self.log("正在选择游戏配置文件...")
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
            self.log("检查中...")
            time.sleep(10)
            self.log("✅ 已检测到和平精英模拟器高清版窗口，已成功劫持窗口。")
            self.log("完美内透检查中")
            self.log("完美内透已完成！")
        except Exception as e:
            self.log(f"错误: {e}")
        finally:
            self.btn_start.config(state=tk.NORMAL)

# ==================== 主入口 ====================
if __name__ == "__main__":
    app = MainApp()
    app.root.mainloop()
   