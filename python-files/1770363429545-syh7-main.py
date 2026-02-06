import subprocess
import sys
import os
import tkinter as tk
import threading
import winreg
import time
import ctypes
from tkinter import messagebox, ttk
import json

test_path = os.path.join(os.path.dirname(__file__), "test.py")  # 获取test.py的完整路径
# 终端输出同步类
class StdoutRedirector:
    def __init__(self):
        self.original_stdout = sys.stdout
    
    def write(self, text):
        if text.strip():
            try:
                send_log(text.strip())
            except:
                pass
        self.original_stdout.write(text)
        self.original_stdout.flush()
    
    def flush(self):
        self.original_stdout.flush()

# 重定向stdout
sys.stdout = StdoutRedirector()# 启动 test.py 并打开 stdin 管道
test_proc = subprocess.Popen([sys.executable, test_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

def send_log(msg):
    try:
        if test_proc.stdin:
            test_proc.stdin.write(msg + "\n")
            test_proc.stdin.flush()
    except Exception:
        pass
    import sys
    sys.stdout.flush()

root = tk.Tk()
root.title("TXZDMM工具 - 文件关联保护")
root.geometry("800x500")
root.configure(bg="#2d2d2d")

main_frame = tk.Frame(root, bg="#2d2d2d")
main_frame.pack(fill="both", expand=True)

top_buttons_frame = tk.Frame(main_frame, bg="#2d2d2d")
top_buttons_frame.pack(side="top", fill="x", pady=5)

row_frame = tk.Frame(top_buttons_frame, bg="#2d2d2d")
row_frame.pack(side="top", anchor="w", padx=5)

top_buttons = []

scrollable_frame = tk.Frame(main_frame, bg="#2d2d2d")
scrollable_frame.pack_forget()

frame_layout = tk.Frame(scrollable_frame, bg="#2d2d2d")
frame_layout.pack(fill="x", padx=10, pady=5)

layout_divider = tk.Frame(frame_layout, height=2, bg="#4a4a4a")
layout_divider.pack(fill="x", pady=5)

def on_about_btn_click(event):
    about_window = tk.Toplevel(root)
    about_window.title("关于")
    about_window.geometry("250x120")
    about_window.configure(bg="#2d2d2d")
    about_window.transient(root)
    about_window.geometry(f"+{root.winfo_x()+root.winfo_width()//2-125}+{root.winfo_y()+root.winfo_height()//2-60}")
    about_window.resizable(False, False)
    tk.Label(about_window, text="TXZDMM工具", bg="#2d2d2d", fg="#ffffff", font=("微软雅黑", 14, "bold")).pack(pady=10)
    tk.Label(about_window, text="文件关联保护系统", bg="#2d2d2d", fg="#aaaaaa", font=("微软雅黑", 10)).pack()
    tk.Label(about_window, text="版本 1.0.0", bg="#2d2d2d", fg="#888888", font=("微软雅黑", 9)).pack(pady=5)
    about_window.grab_set()

def show_settings():
    scrollable_frame.pack(pady=5, padx=10, fill="both", expand=True)
    for btn in top_buttons:
        btn.configure(bg="#455a64")

def hide_settings():
    scrollable_frame.pack_forget()
    for btn in top_buttons:
        btn.configure(bg="#607d8b")

def on_other_btn_click(event):
    btn_text = event.widget.cget('text')
    if btn_text == "文件保护":
        show_file_protection()
    else:
        hide_settings()
        send_log(f"按钮被点击: {btn_text}")

def on_settings_click(event):
    if scrollable_frame.winfo_ismapped():
        hide_settings()
    else:
        show_settings()

button_configs = [
    ("文件保护", on_other_btn_click),
    ("Btn2", on_other_btn_click),
    ("Btn3", on_other_btn_click),
    ("Btn4", on_other_btn_click),
    ("Btn5", on_other_btn_click),
    ("Btn6", on_other_btn_click),
    ("关于", on_about_btn_click),
    ("设置", on_settings_click)
]

for idx, (btn_text, click_handler) in enumerate(button_configs):
    if btn_text == "文件保护":
        btn_color = "#4CAF50"
    else:
        btn_color = "#607d8b"
    
    btn = tk.Button(
        row_frame,
        text=btn_text,
        bg=btn_color,
        fg="#ffffff",
        activebackground="#455a64",
        font=("微软雅黑", 10),
        width=10,
        relief="flat"
    )
    btn.pack(side="left", padx=3, pady=3)
    btn.bind("<Button-1>", click_handler)
    top_buttons.append(btn)

tk.Label(frame_layout, text="窗口设置", bg="#2d2d2d", fg="#ffffff", font=("微软雅黑", 12, "bold")).pack(anchor="w", pady=5)

width_row = tk.Frame(frame_layout, bg="#2d2d2d")
tk.Label(width_row, text="窗口宽度:", bg="#2d2d2d", fg="#cccccc", font=("微软雅黑", 10)).pack(side="left", padx=5)
entry_width = tk.Entry(width_row, width=10, bg="#404040", fg="#ffffff")
entry_width.pack(side="left", padx=5)
tk.Button(width_row, text="应用", bg="#4a90e2", fg="#ffffff", font=("微软雅黑", 9),
         command=lambda: apply_width()).pack(side="left", padx=5)
width_row.pack(anchor="w", pady=2)

height_row = tk.Frame(frame_layout, bg="#2d2d2d")
tk.Label(height_row, text="窗口高度:", bg="#2d2d2d", fg="#cccccc", font=("微软雅黑", 10)).pack(side="left", padx=5)
entry_height = tk.Entry(height_row, width=10, bg="#404040", fg="#ffffff")
entry_height.pack(side="left", padx=5)
tk.Button(height_row, text="应用", bg="#4a90e2", fg="#ffffff", font=("微软雅黑", 9),
         command=lambda: apply_height()).pack(side="left", padx=5)
height_row.pack(anchor="w", pady=2)

fixed_var = tk.BooleanVar()
tk.Checkbutton(frame_layout, text="固定窗口大小", variable=fixed_var, bg="#2d2d2d", fg="#cccccc",
              font=("微软雅黑", 10)).pack(anchor="w", pady=5)

title_var = tk.StringVar(value="TXZDMM工具")
title_row = tk.Frame(frame_layout, bg="#2d2d2d")
tk.Label(title_row, text="窗口标题:", bg="#2d2d2d", fg="#cccccc", font=("微软雅黑", 10)).pack(side="left", padx=5)
entry_title = tk.Entry(title_row, textvariable=title_var, width=25, bg="#404040", fg="#ffffff")
entry_title.pack(side="left", padx=5)
tk.Button(title_row, text="应用", bg="#607d8b", fg="#ffffff", font=("微软雅黑", 9),
         command=lambda: apply_title()).pack(side="left", padx=5)
title_row.pack(anchor="w", pady=5)

def apply_width():
    try:
        w = int(entry_width.get())
        h = root.winfo_height()
        root.geometry(f"{w}x{h}")
    except:
        pass

def apply_height():
    try:
        w = root.winfo_width()
        h = int(entry_height.get())
        root.geometry(f"{w}x{h}")
    except:
        pass

def apply_title():
    try:
        new_title = title_var.get().strip()
        if new_title:
            root.title(new_title)
    except:
        pass

bottom_frame = tk.Frame(main_frame, bg="#1a1a1a", height=25)
bottom_frame.pack(side="bottom", fill="x")

status_var = tk.StringVar(value="就绪")
bottom_label = tk.Label(bottom_frame, textvariable=status_var, fg="#ffffff", bg="#1a1a1a", 
                        anchor="w", font=("微软雅黑", 9))
bottom_label.pack(side="left", fill="both", expand=True, padx=10)

class FileProtectionSystem:
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.backup_file = "file_protection_backup.json"
        self.log_file = "tampering_logs.json"
        self.alert_window = None
        self.startup_enabled = False
        
        self.protected_extensions = [
            '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
            '.csv', '.rtf', '.odt', '.ods', '.odp',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp', '.svg',
            '.mp3', '.wav', '.flac', '.aac', '.wma', '.m4a', '.ogg',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.html', '.htm', '.xml', '.json', '.css', '.js',
            '.lnk', '.url', '.ini', '.cfg', '.inf', '.sys', '.bat', '.cmd',
            '.eml', '.msg', '.vcf',
            '.exe', '.msi', '.dll', '.fon', '.ttf'
        ]
        
        self.protected_protocols = ['http', 'https', 'ftp', 'mailto', 'tel']
        
        self.load_protected_list()
        self.check_startup()
        
    def load_protected_list(self):
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved_exts = data.get('protected_extensions', [])
                    saved_protos = data.get('protected_protocols', [])
                    if saved_exts:
                        self.protected_extensions = saved_exts
                    if saved_protos:
                        self.protected_protocols = saved_protos
        except Exception as e:
            send_log(f"加载保护列表失败: {str(e)}")
    
    def save_protected_list(self):
        try:
            data = {
                'protected_extensions': self.protected_extensions,
                'protected_protocols': self.protected_protocols
            }
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            send_log(f"保存保护列表失败: {str(e)}")
    
    def get_current_default(self, ext):
        try:
            if ext.startswith('.'):
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  f"Software\\Classes\\{ext}") as key:
                    value, _ = winreg.QueryValueEx(key, "")
                    return value
        except:
            pass
        return None
    
    def backup_current_settings(self):
        try:
            backup = {}
            count = 0
            for ext in self.protected_extensions:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                      f"Software\\Classes\\{ext}") as key:
                        value, _ = winreg.QueryValueEx(key, "")
                        backup[ext] = value
                        count += 1
                except:
                    backup[ext] = None
            
            backup['_backup_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup, f, ensure_ascii=False, indent=2)
            
            send_log(f"已备份 {count} 个文件格式")
            return True
        except Exception as e:
            send_log(f"备份失败: {str(e)}")
            return False
    
    def restore_single_extension(self, ext, original_value):
        try:
            if not ext.startswith('.'):
                ext = '.' + ext
            
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                f"Software\\Classes\\{ext}") as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, original_value)
            
            try:
                ext_key = f"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts\\{ext}"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, ext_key, 0, winreg.KEY_ALL_ACCESS) as key:
                    winreg.DeleteKey(key, "UserChoice")
            except:
                pass
            
            return True
        except Exception as e:
            send_log(f"恢复 {ext} 失败: {str(e)}")
            return False
    
    def restore_all_extensions(self):
        try:
            if not os.path.exists(self.backup_file):
                send_log("未找到备份文件")
                return False
            
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            
            restored = 0
            backup_time = backup.pop('_backup_time', None)
            
            for ext, original_value in backup.items():
                if original_value and self.restore_single_extension(ext, original_value):
                    restored += 1
            
            send_log(f"成功恢复 {restored} 个文件格式")
            return True
        except Exception as e:
            send_log(f"恢复失败: {str(e)}")
            return False
    
    def add_protected_extension(self, ext):
        if not ext.startswith('.'):
            ext = '.' + ext
        if ext not in self.protected_extensions:
            self.protected_extensions.append(ext)
            self.save_protected_list()
            send_log(f"已添加保护: {ext}")
            return True
        return False
    
    def remove_protected_extension(self, ext):
        if not ext.startswith('.'):
            ext = '.' + ext
        if ext in self.protected_extensions:
            self.protected_extensions.remove(ext)
            self.save_protected_list()
            send_log(f"已移除保护: {ext}")
            return True
        return False
    
    def log_tampering(self, ext, original_value, new_value, action="blocked"):
        try:
            log_entry = {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'extension': ext,
                'original_value': original_value,
                'new_value': new_value,
                'action': action
            }
            
            logs = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    pass
            
            logs.append(log_entry)
            
            if len(logs) > 100:
                logs = logs[-100:]
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            send_log(f"记录篡改日志失败: {str(e)}")
    
    def get_tampering_logs(self, limit=20):
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                return logs[-limit:]
        except:
            pass
        return []
    
    def set_startup(self, enable):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_path = sys.executable
            
            if enable:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                    winreg.SetValueEx(key, "FileProtection", 0, winreg.REG_SZ, f'"{app_path}"')
                self.startup_enabled = True
                send_log("已开启开机自启")
            else:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                        winreg.DeleteValue(key, "FileProtection")
                    self.startup_enabled = False
                    send_log("已关闭开机自启")
                except:
                    pass
            return True
        except Exception as e:
            send_log(f"设置开机自启失败: {str(e)}")
            return False
    
    def check_startup(self):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, "FileProtection")
                    self.startup_enabled = True
                except:
                    self.startup_enabled = False
        except:
            self.startup_enabled = False
    
    def show_alert(self, ext, original, new_value):
        try:
            if self.alert_window and self.alert_window.winfo_exists():
                self.alert_window.destroy()
            
            self.alert_window = tk.Toplevel(root)
            self.alert_window.title("安全警告 - 文件关联被篡改")
            self.alert_window.geometry("400x200")
            self.alert_window.configure(bg="#2d2d2d")
            self.alert_window.transient(root)
            self.alert_window.resizable(False, False)
            
            x = root.winfo_x() + (root.winfo_width() - 400) // 2
            y = root.winfo_y() + (root.winfo_height() - 200) // 2
            self.alert_window.geometry(f"+{x}+{y}")
            
            tk.Label(self.alert_window, text="检测到文件关联被篡改", bg="#2d2d2d", fg="#ff4444",
                    font=("微软雅黑", 14, "bold")).pack(pady=15)
            
            info_text = f"文件格式: {ext}\n原打开方式: {original}\n被篡改为: {new_value}\n\n已自动恢复原始设置"
            tk.Label(self.alert_window, text=info_text, bg="#2d2d2d", fg="#ffffff",
                    font=("微软雅黑", 10)).pack(pady=10)
            
            tk.Button(self.alert_window, text="确定", bg="#4CAF50", fg="#ffffff",
                     font=("微软雅黑", 10), command=self.alert_window.destroy).pack(pady=10)
            
            self.alert_window.after(5000, self.alert_window.destroy)
            
            self.alert_window.grab_set()
            
        except Exception as e:
            send_log(f"显示警告失败: {str(e)}")
    
    def start_monitoring(self):
        if self.monitoring:
            return False
        
        self.monitoring = True
        self.backup_current_settings()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        send_log("文件关联保护已启动 - 实时监控中")
        return True
    
    def stop_monitoring(self):
        if not self.monitoring:
            return False
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        send_log("文件关联保护已停止")
        return True
    
    def _monitor_loop(self):
        send_log("开始实时监控文件关联变化...")
        check_count = 0
        
        while self.monitoring:
            try:
                check_count += 1
                
                current_backup = {}
                if os.path.exists(self.backup_file):
                    try:
                        with open(self.backup_file, 'r', encoding='utf-8') as f:
                            current_backup = json.load(f)
                    except:
                        pass
                
                for ext in self.protected_extensions:
                    try:
                        current_value = self.get_current_default(ext)
                        
                        if current_value is None:
                            continue
                        
                        backup_value = current_backup.get(ext)
                        
                        if backup_value and current_value != backup_value:
                            send_log(f"检测到 {ext} 被篡改: {backup_value} -> {current_value}")
                            
                            self.restore_single_extension(ext, backup_value)
                            
                            self.log_tampering(ext, backup_value, current_value)
                            
                            self.show_alert(ext, backup_value, current_value)
                            
                            send_log(f"已自动恢复 {ext}")
                        
                    except Exception as e:
                        continue
                
                if check_count % 20 == 0:
                    self.backup_current_settings()
                
                time.sleep(3)
                
            except Exception as e:
                send_log(f"监控出错: {str(e)}")
                time.sleep(10)
    
    def get_status(self):
        return {
            'monitoring': self.monitoring,
            'extensions_count': len(self.protected_extensions),
            'protocols_count': len(self.protected_protocols),
            'startup_enabled': self.startup_enabled
        }

protection = FileProtectionSystem()

protection_window = None

def show_file_protection():
    global protection_window
    
    if protection_window and protection_window.winfo_exists():
        protection_window.lift()
        return
    
    protection_window = tk.Toplevel(root)
    protection_window.title("文件关联保护系统")
    protection_window.geometry("700x450")
    protection_window.configure(bg="#2d2d2d")
    protection_window.transient(root)
    
    main_frame = tk.Frame(protection_window, bg="#2d2d2d")
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    tk.Label(main_frame, text="文件关联保护系统", bg="#2d2d2d", fg="#4CAF50",
            font=("微软雅黑", 16, "bold")).pack(pady=(0, 10))
    
    status_frame = tk.Frame(main_frame, bg="#3d3d3d", relief="solid", bd=1)
    status_frame.pack(fill="x", pady=5)
    
    def update_status():
        try:
            status = protection.get_status()
            status_text = f"监控: {'运行中' if status['monitoring'] else '已停止'} | "
            status_text += f"保护格式: {status['extensions_count']} 个 | "
            status_text += f"开机自启: {'开启' if status['startup_enabled'] else '关闭'}"
            status_label.config(text=status_text)
        except:
            pass
        status_frame.after(2000, update_status)
    
    status_label = tk.Label(status_frame, text="", bg="#3d3d3d", fg="#ffffff", font=("微软雅黑", 9), pady=5)
    status_label.pack(fill="x", padx=10)
    update_status()
    
    content = tk.Frame(main_frame, bg="#2d2d2d")
    content.pack(fill="both", expand=True, pady=10)
    
    left = tk.Frame(content, bg="#2d2d2d")
    left.pack(side="left", fill="both", expand=True, padx=(0, 5))
    
    tk.Label(left, text="受保护的文件格式", bg="#2d2d2d", fg="#ffffff", font=("微软雅黑", 10, "bold")).pack(anchor="w")
    
    list_frame = tk.Frame(left, bg="#2d2d2d")
    list_frame.pack(fill="both", expand=True, pady=5)
    
    ext_listbox = tk.Listbox(list_frame, bg="#3d3d3d", fg="#ffffff", font=("微软雅黑", 9))
    ext_listbox.pack(side="left", fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(list_frame, command=ext_listbox.yview)
    scrollbar.pack(side="right", fill="y")
    ext_listbox.config(yscrollcommand=scrollbar.set)
    
    btn_row = tk.Frame(left, bg="#2d2d2d")
    btn_row.pack(fill="x", pady=5)
    
    add_entry = tk.Entry(btn_row, bg="#404040", fg="#ffffff", width=10)
    add_entry.pack(side="left", padx=(0, 5))
    add_entry.insert(0, ".新格式")
    
    def add_ext():
        ext = add_entry.get().strip()
        if ext:
            protection.add_protected_extension(ext)
            refresh_list()
            add_entry.delete(0, tk.END)
    
    def remove_ext():
        selection = ext_listbox.curselection()
        if selection:
            ext = ext_listbox.get(selection[0])
            protection.remove_protected_extension(ext)
            refresh_list()
    
    tk.Button(btn_row, text="添加", bg="#4CAF50", fg="#ffffff", font=("微软雅黑", 9), command=add_ext).pack(side="left", padx=2)
    tk.Button(btn_row, text="移除", bg="#f44336", fg="#ffffff", font=("微软雅黑", 9), command=remove_ext).pack(side="left", padx=2)
    
    right = tk.Frame(content, bg="#2d2d2d")
    right.pack(side="right", fill="both", expand=True, padx=(5, 0))
    
    btn_frame = tk.Frame(right, bg="#2d2d2d")
    btn_frame.pack(fill="x", pady=(0, 5))
    
    def toggle_monitoring():
        if protection.monitoring:
            protection.stop_monitoring()
            toggle_btn.config(text="启动保护", bg="#4CAF50")
        else:
            protection.start_monitoring()
            toggle_btn.config(text="停止保护", bg="#f44336")
        refresh_list()
    
    toggle_btn = tk.Button(btn_frame, text="启动保护", bg="#4CAF50", fg="#ffffff",
                          font=("微软雅黑", 10), command=toggle_monitoring, width=12)
    toggle_btn.pack(side="left", padx=2)
    
    tk.Button(btn_frame, text="立即备份", bg="#2196F3", fg="#ffffff", font=("微软雅黑", 10),
             command=lambda: (protection.backup_current_settings(), send_log("立即备份完成"))).pack(side="left", padx=2)
    
    tk.Button(btn_frame, text="一键恢复", bg="#FF9800", fg="#ffffff", font=("微软雅黑", 10),
             command=lambda: (protection.restore_all_extensions(), send_log("一键恢复完成"))).pack(side="left", padx=2)
    
    def toggle_startup():
        new_state = not protection.startup_enabled
        protection.set_startup(new_state)
        startup_btn.config(text=f"{'关闭自启' if new_state else '开启自启'}")
        send_log(f"{'已开启' if new_state else '已关闭'}开机自启")
    
    startup_btn = tk.Button(btn_row, text=f"{'关闭自启' if protection.startup_enabled else '开启自启'}",
                           bg="#9C27B0", fg="#ffffff", font=("微软雅黑", 9), command=toggle_startup)
    
    tk.Label(right, text="篡改日志", bg="#2d2d2d", fg="#ffffff", font=("微软雅黑", 10, "bold")).pack(anchor="w")
    
    log_frame = tk.Frame(right, bg="#2d2d2d")
    log_frame.pack(fill="both", expand=True)
    
    log_text = tk.Text(log_frame, bg="#1a1a1a", fg="#00ff00", font=("Consolas", 9), height=8, state="normal")
    log_text.pack(side="left", fill="both", expand=True)
    
    log_scroll = tk.Scrollbar(log_frame, command=log_text.yview)
    log_scroll.pack(side="right", fill="y")
    log_text.config(yscrollcommand=log_scroll.set)
    
    def refresh_list():
        ext_listbox.delete(0, tk.END)
        for ext in sorted(protection.protected_extensions):
            ext_listbox.insert(tk.END, ext)
    
    def refresh_log():
        log_text.delete(1.0, tk.END)
        logs = protection.get_tampering_logs(10)
        if logs:
            for log in logs:
                log_text.insert(tk.END, f"[{log['timestamp']}] {log['extension']}\n")
                log_text.insert(tk.END, f"  {log['original_value']} -> {log['new_value']}\n")
                log_text.insert(tk.END, f"  操作: {log['action']}\n\n")
        else:
            log_text.insert(tk.END, "暂无篡改记录")
    
    tk.Button(btn_frame, text="刷新日志", bg="#607D8B", fg="#ffffff", font=("微软雅黑", 10),
             command=refresh_log).pack(side="left", padx=2)
    
    refresh_list()
    refresh_log()
    
    protection_window.protocol("WM_DELETE_WINDOW", lambda: protection_window.destroy())

def stdin_monitor():
    try:
        for line in iter(test_proc.stdout.readline, ''):
            if line:
                if 'log' in line.lower():
                    try:
                        root.after(0, lambda l=line: [output.config(state='normal'),
                                                       output.insert(tk.END, l),
                                                       output.see(tk.END),
                                                       output.config(state='disabled')])
                    except:
                        pass
            else:
                break
    except:
        pass

threading.Thread(target=stdin_monitor, daemon=True).start()

def show_startup_tip():
    send_log("文件关联保护系统已就绪 - 点击文件保护开始使用")
    status_var.set("就绪 - 点击文件保护开始使用")

root.after(1000, show_startup_tip)

root.mainloop()
