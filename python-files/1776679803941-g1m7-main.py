import tkinter as tk
from tkinter import messagebox, simpledialog
import os, shutil, sys
from datetime import datetime

# --- 系統路徑與基礎設定 ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.join(BASE_PATH, "user")
SYS_DIR = os.path.join(BASE_PATH, "system")
for d in [USER_DIR, SYS_DIR]: os.makedirs(d, exist_ok=True)

def get_now():
    return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

class AbsoluteTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("OKRASYS_CMD_v29")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="black")
        self.sys_auth = False
        
        # 黑色螢幕區
        self.display = tk.Text(root, bg="black", fg="#39ff14", font=("Consolas", 12), 
                               insertbackground="white", bd=0, padx=20, pady=20)
        self.display.pack(fill=tk.BOTH, expand=True)
        
        # 初始提示 (依照您的要求改為中文)
        self.display.insert(tk.END, "如未知指令請輸入 help 來獲得\n")
        self.display.insert(tk.END, f"{get_now()} 系統已準備就緒。\n")
        self.display.config(state=tk.DISABLED)

        # 指令輸入區
        self.cmd_frame = tk.Frame(root, bg="black")
        self.cmd_frame.pack(fill=tk.X)
        tk.Label(self.cmd_frame, text="root@okrasys:~# ", bg="black", fg="#39ff14", font=("Consolas", 12)).pack(side=tk.LEFT)
        self.entry = tk.Entry(self.cmd_frame, bg="black", fg="white", font=("Consolas", 12), bd=0, insertbackground="white")
        self.entry.pack(fill=tk.X, side=tk.LEFT)
        self.entry.focus_set()
        self.entry.bind("<Return>", self.run_command)

    def print_to_screen(self, msg):
        self.display.config(state=tk.NORMAL)
        self.display.insert(tk.END, f"{get_now()} {msg}\n")
        self.display.see(tk.END)
        self.display.config(state=tk.DISABLED)

    def run_command(self, event):
        cmd = self.entry.get().strip().lower()
        self.print_to_screen(f"EXEC: {cmd}")
        
        # 核心指令邏輯
        if cmd == "help":
            self.print_to_screen("指令列表: help, edit system, bus, mines, calc, paint, cls, exit")
        elif cmd == "edit system":
            self.sys_auth = True
            self.print_to_screen("ACCESS GRANTED: 開啟系統核心...")
            self.open_file_manager(SYS_DIR)
        elif cmd == "bus":
            self.open_bus_sign()
        elif cmd == "mines":
            self.open_mines()
        elif cmd == "calc":
            os.system("calc") if sys.platform == "win32" else messagebox.showinfo("系統", "啟動計算機")
        elif cmd == "paint":
            os.system("mspaint") if sys.platform == "win32" else messagebox.showinfo("系統", "啟動小畫家")
        elif cmd == "cls":
            self.display.config(state=tk.NORMAL)
            self.display.delete("1.0", tk.END)
            self.display.insert(tk.END, "如未知指令請輸入 help 來獲得\n")
            self.display.config(state=tk.DISABLED)
        elif cmd == "exit":
            self.root.destroy()
        else:
            self.print_to_screen(f"未知指令: '{cmd}'")
            
        self.entry.delete(0, tk.END)

    # --- 巴士電牌：補回備註與英文 ---
    def open_bus_sign(self):
        b = tk.Toplevel(self.root)
        b.title("巴士電牌系統")
        tk.Label(b, text="備註 (如特快/暫停服務):").pack()
        note = tk.Entry(b); note.pack(); note.insert(0, "特快 EXPRESS")
        tk.Label(b, text="目的地 (中文):").pack()
        zh = tk.Entry(b); zh.pack(); zh.insert(0, "香港仔")
        tk.Label(b, text="目的地 (英文):").pack()
        en = tk.Entry(b); en.pack(); en.insert(0, "ABERDEEN")
        tk.Label(b, text="路線編號:").pack()
        num = tk.Entry(b); num.pack(); num.insert(0, "970X")
        
        cv = tk.Canvas(b, bg="black", width=600, height=200)
        cv.pack(pady=10)
        
        def render():
            cv.delete("all")
            cv.create_text(300, 30, text=note.get(), fill="#ff9f43", font=("Arial", 15))
            cv.create_text(200, 100, text=zh.get(), fill="#ff9f43", font=("微軟正黑體", 50, "bold"))
            cv.create_text(200, 160, text=en.get(), fill="#ff9f43", font=("Arial", 25, "bold"))
            cv.create_text(500, 110, text=num.get(), fill="#ff9f43", font=("Arial", 70, "bold"))
            
        tk.Button(b, text="渲染電牌", command=render).pack()
        render()

    # --- 文件管理：保留所有功能 ---
    def open_file_manager(self, path):
        fm = tk.Toplevel(self.root)
        fm.title(f"管理: {path}")
        lb = tk.Listbox(fm, width=50, height=20)
        lb.pack(padx=10, pady=10)
        
        def refresh():
            lb.delete(0, tk.END)
            for i in os.listdir(path): lb.insert(tk.END, i)
            
        bar = tk.Frame(fm)
        bar.pack(fill=tk.X, pady=5)
        tk.Button(bar, text="📄 新建檔案", command=lambda: [open(os.path.join(path, "new.txt"), 'w').close(), refresh()]).pack(side=tk.LEFT, padx=5)
        tk.Button(bar, text="📁 新資料夾", command=lambda: [os.makedirs(os.path.join(path, "new_dir"), exist_ok=True), refresh()]).pack(side=tk.LEFT, padx=5)
        tk.Button(bar, text="🗑️ 刪除", fg="red", command=lambda: [os.remove(os.path.join(path, lb.get(tk.ACTIVE))) if lb.get(tk.ACTIVE) else None, refresh()]).pack(side=tk.LEFT, padx=5)
        tk.Button(bar, text="🔄 刷新", command=refresh).pack(side=tk.RIGHT, padx=5)
        refresh()

    def open_mines(self):
        m = tk.Toplevel(self.root); m.title("排雷")
        for r in range(5):
            for c in range(5):
                tk.Button(m, text="?", width=4, command=lambda: messagebox.showinfo("OK", "安全")).grid(row=r, column=c)

if __name__ == "__main__":
    root = tk.Tk()
    app = AbsoluteTerminal(root)
    root.mainloop()
