# Poppy Playtime 1-5章 启动器
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import configparser
import os

CONFIG_PATH = "PoppyLauncher_Config.ini"
config = configparser.ConfigParser()
CHAPTERS = ["第一章", "第二章", "第三章", "第四章", "第五章"]

def load_all_path():
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding="utf-8")

def save_chapter_path(chap_name, path):
    if "PATHS" not in config.sections():
        config.add_section("PATHS")
    config.set("PATHS", chap_name, path)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        config.write(f)

def get_chap_path(chap_name):
    return config.get("PATHS", chap_name, fallback="")

def select_chapter(chap_name, entry_widget):
    file_path = filedialog.askopenfilename(
        title=f"选择 {chap_name} 游戏EXE",
        filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
    )
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)
        save_chapter_path(chap_name, file_path)
        status_label.config(text=f"✅ {chap_name} 路径已保存", fg="green")

def launch_chapter(chap_name, entry_widget):
    game_path = entry_widget.get().strip()
    if not game_path:
        messagebox.showerror("提示", f"请先设置 {chap_name} 游戏路径！")
        return
    if not os.path.exists(game_path):
        messagebox.showerror("错误", f"{chap_name} 路径不存在，请重新选择！")
        return
    if not game_path.endswith(".exe"):
        messagebox.showerror("错误", "请选择 .exe 游戏程序！")
        return
    try:
        subprocess.Popen(
            [game_path],
            cwd=os.path.dirname(game_path),
            shell=False
        )
        status_label.config(text=f"🎮 {chap_name} 启动成功！", fg="green")
    except Exception as e:
        messagebox.showerror("启动失败", f"{chap_name} 启动失败：\n{str(e)}")

root = tk.Tk()
root.title("Poppy Playtime 1~5章 启动器")
root.geometry("620x330")
root.resizable(False, False)
load_all_path()

tk.Label(root, text="Poppy Playtime 1~5章 启动器", font=("微软雅黑", 16, "bold")).pack(pady=8)
entry_list = []

for chap in CHAPTERS:
    frame = tk.Frame(root)
    frame.pack(pady=3, padx=15, fill=tk.X)
    tk.Label(frame, text=chap, width=8, font=("微软雅黑", 10)).pack(side=tk.LEFT)
    ent = tk.Entry(frame, font=("微软雅黑", 9))
    ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
    ent.insert(0, get_chap_path(chap))
    entry_list.append(ent)
    tk.Button(frame, text="选择", font=("微软雅黑", 9),
              command=lambda c=chap, e=ent: select_chapter(c, e)).pack(side=tk.LEFT, padx=2)
    tk.Button(frame, text="启动", font=("微软雅黑", 9), bg="#2196F3", fg="white",
              command=lambda c=chap, e=ent: launch_chapter(c, e)).pack(side=tk.LEFT, padx=2)

status_label = tk.Label(root, text="ℹ️ 先选各章节路径，再点启动", font=("微软雅黑", 10), fg="gray")
status_label.pack(pady=10)

root.mainloop()
