# -*- coding: utf-8 -*-
# File: HieuCheat_Mod_V5.py
# Chức năng: Mod đồ họa Free Fire - Giao diện Style SNOWCHEATS
# Đóng gói: pyinstaller --onefile --windowed --add-data "bg.jpg;." --name="HieuCheat_Mod_V5" HieuCheat_Mod_V5.py

import tkinter as tk
from tkinter import messagebox
import psutil
import platform
import os
import sys
import re
import subprocess
from PIL import Image, ImageTk

# ==================== CẤU HÌNH ====================
KEY = "hieumod1"
VERSION = "5.1"
TIEU_DE = "HieuCheat Mod V5 - FF MOD TOOL"

CONFIG_PATHS = [
    r"C:\ProgramData\BlueStacks_nxt\Engine\UserData\Android\data\com.dts.freefireth\shared_prefs\com.dts.freefireth.v2.playerprefs.xml",
    r"C:\ProgramData\BlueStacks\Engine\UserData\Android\data\com.dts.freefireth\shared_prefs\com.dts.freefireth.v2.playerprefs.xml",
    r"C:\Users\{username}\AppData\Roaming\XuanZhi\LDPlayer\userdata\shared_prefs\com.dts.freefireth.v2.playerprefs.xml",
    r"C:\Program Files\Microvirt\MEmu\data\shared_prefs\com.dts.freefireth.v2.playerprefs.xml",
]

# ==================== PHÁT HIỆN GIẢ LẬP ====================
def detect_emulator():
    emulators = {
        "BlueStacks": ["BlueStacksApp.exe", "HD-Player.exe", "BstkSvc.exe"],
        "LDPlayer": ["LDPlayer.exe", "LDMultiPlayer.exe"],
        "MEmu": ["MEmu.exe", "MEmuConsole.exe"],
        "Nox": ["Nox.exe", "NoxVMHandle.exe"],
        "MuMu": ["MuMuPlayer.exe"],
        "Droid4X": ["Droid4X.exe"],
        "Genymotion": ["Genymotion.exe"],
        "SmartGaGa": ["SmartGaGa.exe"]
    }
    try:
        for name, procs in emulators.items():
            for p in procs:
                # Sử dụng subprocess thay vì os.system để tránh lỗi
                result = subprocess.run(f'tasklist /FI "IMAGENAME eq {p}"', capture_output=True, text=True, shell=True)
                if p in result.stdout:
                    return name
    except:
        pass
    return "Không xác định"

# ==================== LỚP CHÍNH ====================
class HieuCheatTool:
    def __init__(self, root):
        self.root = root
        self.root.title(TIEU_DE)
        self.root.geometry("420x720")
        self.root.resizable(False, False)
        self.root.configure(bg="#0a0a12")
        self.root.overrideredirect(True)
        
        # Biến trạng thái
        self.authenticated = False
        self.config_path = None
        self.current_mode = None
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
        # Lấy thông tin hệ thống
        self.system_info = self.get_system_info()
        self.emulator = detect_emulator()
        
        # Tải ảnh nền
        self.bg_image = self.load_bg()
        
        # Tạo giao diện
        self.create_title_bar()
        self.create_login()
        self.create_main()
        self.show_login()
    
    # ==================== TIÊU ĐỀ ====================
    def create_title_bar(self):
        self.title_bar = tk.Frame(self.root, bg="#1a1a2e", height=35)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)
        
        tk.Label(self.title_bar, text="❄ HieuCheat Mod V5", font=("Arial", 11, "bold"), fg="#00d4ff", bg="#1a1a2e").pack(side="left", padx=15)
        
        btn_close = tk.Button(self.title_bar, text="✕", font=("Arial", 11, "bold"), bg="#1a1a2e", fg="#ff6b6b", bd=0, relief="flat", command=self.root.quit, cursor="hand2")
        btn_close.pack(side="right", padx=10)
        btn_min = tk.Button(self.title_bar, text="─", font=("Arial", 11, "bold"), bg="#1a1a2e", fg="#ffd93d", bd=0, relief="flat", command=self.minimize, cursor="hand2")
        btn_min.pack(side="right", padx=5)
        
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.drag_window)
    
    def start_drag(self, e):
        self.dragging = True
        self.offset_x = e.x
        self.offset_y = e.y
    
    def drag_window(self, e):
        if self.dragging:
            x = self.root.winfo_x() + e.x - self.offset_x
            y = self.root.winfo_y() + e.y - self.offset_y
            self.root.geometry(f"+{x}+{y}")
    
    def minimize(self):
        self.root.iconify()
    
    # ==================== ẢNH NỀN ====================
    def load_bg(self):
        try:
            if os.path.exists("bg.jpg"):
                img = Image.open("bg.jpg").resize((420, 720), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except:
            pass
        return None
    
    # ==================== LẤY THÔNG TIN HỆ THỐNG ====================
    def get_system_info(self):
        try:
            cpu = platform.processor() or "Không xác định"
            cores = psutil.cpu_count(logical=True)
            ram = round(psutil.virtual_memory().total / (1024**3), 2)
            os_name = platform.system() + " " + platform.release()
            gpu = self.get_gpu_info()
            return {"cpu": cpu, "cores": cores, "ram": ram, "os": os_name, "gpu": gpu}
        except Exception as e:
            return {"cpu": "Lỗi đọc", "cores": 0, "ram": 0, "os": "Lỗi đọc", "gpu": "Lỗi đọc"}
    
    def get_gpu_info(self):
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}")
            for i in range(50):
                try:
                    sub = winreg.OpenKey(key, str(i))
                    desc = winreg.QueryValueEx(sub, "DriverDesc")[0]
                    if desc:
                        return desc
                except:
                    continue
            return "Không xác định"
        except:
            return "Không đọc được"
    
    # ==================== LOGIN ====================
    def create_login(self):
        self.login_frame = tk.Frame(self.root, bg="#0f0f1a", bd=2, relief="groove")
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=280)
        
        if self.bg_image:
            bg = tk.Label(self.login_frame, image=self.bg_image, bg="#0f0f1a")
            bg.place(relx=0, rely=0, relwidth=1, relheight=1)
            bg.image = self.bg_image
        
        tk.Label(self.login_frame, text="❄ HieuCheat Mod V5", font=("Arial", 18, "bold"), fg="#00d4ff", bg="#0f0f1a").pack(pady=(20,0))
        tk.Label(self.login_frame, text="by Nguyễn Hiếu", font=("Arial", 10), fg="#aaa", bg="#0f0f1a").pack()
        
        f = tk.Frame(self.login_frame, bg="#0f0f1a")
        f.pack(pady=15)
        tk.Label(f, text="🔑 KEY", font=("Arial", 10, "bold"), fg="#ffd93d", bg="#0f0f1a").pack(anchor="w")
        self.key_entry = tk.Entry(f, font=("Arial", 14), width=24, show="•", bg="#1a1a3e", fg="white", relief="flat", bd=3)
        self.key_entry.pack(pady=5)
        self.key_entry.bind("<Return>", lambda e: self.verify())
        tk.Button(f, text="▶ KÍCH HOẠT", font=("Arial", 11, "bold"), bg="#00d4ff", fg="white", command=self.verify, padx=30, pady=5, relief="flat", bd=0).pack(pady=8)
        self.login_status = tk.Label(self.login_frame, text="💫 Nhập key để kích hoạt", font=("Arial", 9), fg="#aaa", bg="#0f0f1a")
        self.login_status.pack()
    
    # ==================== MAIN ====================
    def create_main(self):
        self.main_frame = tk.Frame(self.root, bg="#0a0a12")
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        if self.bg_image:
            bg = tk.Label(self.main_frame, image=self.bg_image, bg="#0a0a12")
            bg.place(relx=0, rely=0, relwidth=1, relheight=1)
            bg.image = self.bg_image
        
        # Header
        h = tk.Frame(self.main_frame, bg="#1a1a2e", height=40)
        h.pack(fill="x")
        h.pack_propagate(False)
        tk.Label(h, text="❄ HieuCheat Mod V5", font=("Arial", 14, "bold"), fg="#00d4ff", bg="#1a1a2e").pack(side="left", padx=15)
        tk.Label(h, text="v5.1", font=("Arial", 9), fg="#ffd93d", bg="#1a1a2e").pack(side="left", padx=5)
        
        # System Info
        info_frame = tk.LabelFrame(self.main_frame, text="🖥️ SYSTEM INFO", font=("Arial", 9, "bold"), fg="#00d4ff", bg="#12122a", padx=8, pady=5, bd=2, relief="ridge")
        info_frame.pack(fill="x", padx=10, pady=6)
        info_text = f"""CPU: {self.system_info['cpu']} ({self.system_info['cores']} nhân)
RAM: {self.system_info['ram']} GB
HĐH: {self.system_info['os']}
GPU: {self.system_info['gpu']}
📱 Giả lập: {self.emulator}"""
        info_label = tk.Label(info_frame, text=info_text, font=("Courier", 8), fg="#aaa", bg="#12122a", justify="left", anchor="w")
        info_label.pack(fill="x", padx=5, pady=2)
        
        # Chức năng
        func_frame = tk.Frame(self.main_frame, bg="#0a0a12")
        func_frame.pack(pady=8, padx=10, fill="both", expand=True)
        
        self.func_vars = {}
        func_list = [
            ("⛏️ MINECRAFT", "minecraft"),
            ("📉 CỰC THẤP", "cuc_thap"),
            ("📉 THẤP", "thap"),
            ("📈 TRUNG BÌNH", "trung_binh"),
            ("🔄 KHÔI PHỤC", "reset"),
            ("⚡ ÁP DỤNG", "apply"),
        ]
        
        for i, (text, key) in enumerate(func_list):
            row = i // 2
            col = i % 2
            frame = tk.Frame(func_frame, bg="#0a0a12")
            frame.grid(row=row, column=col, padx=5, pady=4, sticky="w")
            
            if key in ["apply", "reset"]:
                btn = tk.Button(frame, text=text, font=("Arial", 10, "bold"),
                               bg="#1a1a3e" if key=="reset" else "#00d4ff",
                               fg="white", command=lambda k=key: self.action(k),
                               width=14, height=1, relief="raised", bd=2, cursor="hand2")
                btn.pack(pady=2)
            else:
                var = tk.StringVar(value="0")
                self.func_vars[key] = var
                rb = tk.Radiobutton(frame, text=text, variable=var, value=key,
                                   font=("Arial", 9), bg="#0a0a12", fg="#00d4ff",
                                   selectcolor="#0a0a12", cursor="hand2", anchor="w")
                rb.pack(anchor="w")
                if key in ["minecraft", "cuc_thap", "thap", "trung_binh"]:
                    rb.config(command=lambda k=key: self.select_mode(k))
        
        # Trạng thái
        self.status_label = tk.Label(self.main_frame, text="💡 Chọn chế độ rồi bấm ÁP DỤNG", font=("Arial", 9), fg="#aaa", bg="#0a0a12")
        self.status_label.pack(pady=4)
        
        # Footer
        ft = tk.Frame(self.main_frame, bg="#1a1a2e", height=25)
        ft.pack(side="bottom", fill="x")
        ft.pack_propagate(False)
        tk.Label(ft, text="🔒 Tool học tập - by Nguyễn Hiếu", font=("Arial", 8), fg="#555", bg="#1a1a2e").pack()
        
        self.main_frame.place_forget()
    
    # ==================== XỬ LÝ ====================
    def show_login(self):
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.main_frame.place_forget()
    
    def show_main(self):
        self.login_frame.place_forget()
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    
    def verify(self):
        key = self.key_entry.get().strip()
        if key == KEY:
            self.authenticated = True
            self.login_status.config(text="✅ KÍCH HOẠT THÀNH CÔNG!", fg="#00ff00")
            self.root.after(300, self.show_main)
        else:
            self.login_status.config(text="❌ KEY KHÔNG HỢP LỆ!", fg="#ff0000")
            self.key_entry.delete(0, tk.END)
    
    def select_mode(self, mode):
        self.current_mode = mode
        self.status_label.config(text=f"✅ Đã chọn: {mode.upper()}", fg="#00d4ff")
        for k, v in self.func_vars.items():
            if k != mode and k in ["minecraft", "cuc_thap", "thap", "trung_binh"]:
                v.set("0")
    
    def action(self, key):
        if not self.authenticated:
            messagebox.showerror("Lỗi", "Chưa kích hoạt key!")
            return
        if key == "apply":
            self.apply_graphics()
        elif key == "reset":
            self.reset_graphics()
    
    def find_config(self):
        for p in CONFIG_PATHS:
            if "{username}" in p:
                p = p.replace("{username}", os.getlogin())
            if os.path.exists(p):
                self.config_path = p
                return True
        return False
    
    def apply_graphics(self):
        if self.current_mode is None:
            self.status_label.config(text="❌ Chưa chọn chế độ!", fg="#ff0000")
            return
        self.status_label.config(text=f"⏳ Đang áp dụng: {self.current_mode}...", fg="#ffaa00")
        self.root.update()
        if not self.find_config():
            self.status_label.config(text="❌ Không tìm thấy config! Mở game trước.", fg="#ff0000")
            return
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                c = f.read()
            vals = {
                "resolution_scale": "0.08",
                "lod_distance": "0.02",
                "texture_quality": "0",
                "shadow_quality": "0",
                "graphics_quality": "0",
                "particle_quality": "0",
                "post_process": "0",
                "antialiasing": "0"
            }
            if self.current_mode == "cuc_thap":
                vals.update({"resolution_scale": "0.15", "lod_distance": "0.08"})
            elif self.current_mode == "thap":
                vals.update({"resolution_scale": "0.25", "lod_distance": "0.15"})
            elif self.current_mode == "trung_binh":
                vals.update({"resolution_scale": "0.5", "lod_distance": "0.5", "graphics_quality": "1"})
            # Minecraft giữ nguyên cực thấp
            for k, v in vals.items():
                pattern = f'<.*? name="{k}".*?>.*?</.*?>'
                replacement = f'<string name="{k}">{v}</string>'
                c = re.sub(pattern, replacement, c)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(c)
            try:
                os.chmod(self.config_path, 0o444)
            except:
                pass
            self.status_label.config(text=f"✅ Áp dụng {self.current_mode} thành công!", fg="#00ff00")
            messagebox.showinfo("Thành công", f"✅ Đã áp dụng chế độ {self.current_mode}!\nThoát game và vào lại.")
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {str(e)}", fg="#ff0000")
    
    def reset_graphics(self):
        if not self.find_config():
            messagebox.showerror("Lỗi", "Không tìm thấy file config!")
            return
        try:
            os.chmod(self.config_path, 0o666)
            os.remove(self.config_path)
            self.status_label.config(text="✅ Khôi phục mặc định thành công!", fg="#00ff00")
            messagebox.showinfo("Thành công", "✅ Đã khôi phục cài đặt gốc.")
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {str(e)}", fg="#ff0000")

# ==================== KHỞI CHẠY ====================
if __name__ == "__main__":
    # Kiểm tra thư viện
    try:
        import psutil
        import PIL
    except ImportError as e:
        print(f"Lỗi thiếu thư viện: {e}")
        print("Chạy lệnh: pip install psutil pillow")
        input("Nhấn Enter để thoát...")
        sys.exit(1)
    
    root = tk.Tk()
    app = HieuCheatTool(root)
    root.mainloop()