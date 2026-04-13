import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk

# ========== 请求管理员权限 ==========
import ctypes
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# ========== 继续正常导入 ==========
from pynput import keyboard, mouse

# ========== 录制器 ==========
class RecorderWindow:
    def __init__(self, parent, save_path, on_close):
        self.parent = parent
        self.save_path = save_path
        self.on_close = on_close
        
        self.recording = False
        self.events = []
        self.start_time = 0
        self.key1_presses = []
        
        self.win = tk.Toplevel(parent)
        self.win.title("录制中")
        self.win.geometry("320x200")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        
        tk.Label(self.win, text="🔴 录制中", font=("微软雅黑", 14), fg="red").pack(pady=15)
        self.time_lbl = tk.Label(self.win, text="时长: 0 秒", font=("微软雅黑", 10))
        self.time_lbl.pack()
        self.event_lbl = tk.Label(self.win, text="事件: 0", font=("微软雅黑", 10))
        self.event_lbl.pack(pady=5)
        
        self.btn = tk.Button(self.win, text="停止录制", command=self.stop, bg="#f44336", fg="white", width=15, height=1)
        self.btn.pack(pady=15)
        tk.Label(self.win, text="快速按3次数字1停止", font=("微软雅黑", 8), fg="gray").pack()
        
        self.k_listener = None
        self.m_listener = None
        
        self.win.after(100, self.start)
    
    def start(self):
        self.recording = True
        self.events = []
        self.start_time = time.time()
        self.key1_presses = []
        
        self.k_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.m_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        self.k_listener.start()
        self.m_listener.start()
        
        self._update()
    
    def _on_press(self, key):
        if not self.recording: return
        t = time.time() - self.start_time
        try:
            if hasattr(key, 'char') and key.char == '1':
                now = time.time()
                self.key1_presses.append(now)
                self.key1_presses = [ts for ts in self.key1_presses if now - ts <= 2.0]
                key_name = '1'
            elif hasattr(key, 'name'):
                key_name = key.name
            else:
                key_name = str(key)
            self.events.append({"type": "key_press", "key": key_name, "time": t})
        except:
            pass
    
    def _on_release(self, key):
        if not self.recording: return
        t = time.time() - self.start_time
        try:
            if hasattr(key, 'char') and key.char == '1':
                key_name = '1'
            elif hasattr(key, 'name'):
                key_name = key.name
            else:
                key_name = str(key)
            self.events.append({"type": "key_release", "key": key_name, "time": t})
        except:
            pass
    
    def _on_move(self, x, y):
        if not self.recording: return
        t = time.time() - self.start_time
        self.events.append({"type": "mouse_move", "x": x, "y": y, "time": t})
    
    def _on_click(self, x, y, button, pressed):
        if not self.recording: return
        t = time.time() - self.start_time
        self.events.append({"type": "mouse_click", "button": str(button).split('.')[-1], "pressed": pressed, "time": t})
    
    def _update(self):
        if self.recording:
            self.time_lbl.config(text=f"时长: {int(time.time()-self.start_time)} 秒")
            self.event_lbl.config(text=f"事件: {len(self.events)}")
            if len(self.key1_presses) >= 3:
                self.stop()
            else:
                self.win.after(200, self._update)
    
    def stop(self):
        if not self.recording: return
        self.recording = False
        if self.k_listener: self.k_listener.stop()
        if self.m_listener: self.m_listener.stop()
        self.btn.config(state="disabled", text="保存中...")
        self._save()
    
    def _save(self):
        if self.events:
            playback, prev = [], 0
            for e in self.events:
                delay = e["time"] - prev
                prev = e["time"]
                if e["type"] == "mouse_move":
                    playback.append({"type": "mouse_move", "dx": e["x"], "dy": e["y"], "delay": delay})
                else:
                    playback.append({"type": e["type"], "key": e.get("key", ""), "button": e.get("button", ""), "pressed": e.get("pressed", False), "delay": delay})
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(playback, f)
            messagebox.showinfo("完成", f"已保存 {len(playback)} 个事件")
        self.win.destroy()
        self.on_close()
    
    def _on_close(self):
        if self.recording:
            self.stop()
        else:
            self.win.destroy()
            self.on_close()

# ========== 回放器 ==========
class PlayerWindow:
    def __init__(self, parent, on_close):
        self.parent = parent
        self.on_close = on_close
        self.serial = None
        self.connected = False
        
        self.win = tk.Toplevel(parent)
        self.win.title("回放中")
        self.win.geometry("280x150")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.status = tk.Label(self.win, text="等待设备...", font=("微软雅黑", 11), fg="orange")
        self.status.pack(pady=30)
        self.progress = ttk.Progressbar(self.win, mode="indeterminate", length=200)
        self.progress.pack()
        self.progress.start()
        
        self._check()
    
    def _check(self):
        if not self.connected:
            try:
                import serial.tools.list_ports
                for p in serial.tools.list_ports.comports():
                    if any(x in str(p.description) for x in ("RP2040", "CircuitPython", "Pico", "USB Serial")):
                        import serial
                        self.serial = serial.Serial(p.device, 115200, timeout=1)
                        self.connected = True
                        self.status.config(text="已连接 - 回放中", fg="green")
                        self.progress.stop()
                        self.progress.pack_forget()
                        self.serial.write(b"START\n")
                        self.win.after(2000, self._done)
                        return
            except:
                pass
        if not self.connected:
            self.win.after(1000, self._check)
    
    def _done(self):
        self.win.destroy()
        self.on_close()
    
    def _on_close(self):
        if self.connected:
            try:
                self.serial.write(b"STOP\n")
                self.serial.close()
            except:
                pass
        self.win.destroy()
        self.on_close()

# ========== 主界面 ==========
class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("智能宏工具")
        self.root.geometry("320x230")
        self.drive = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.macro_file = os.path.join(self.drive, "macro.json")
        self.has_macro = os.path.exists(self.macro_file)
        self._build()
    
    def _build(self):
        tk.Label(self.root, text="智能宏工具", font=("微软雅黑", 14, "bold")).pack(pady=15)
        
        if self.has_macro:
            try:
                with open(self.macro_file, "r") as f:
                    cnt = len(json.load(f))
                tk.Label(self.root, text=f"✅ 已有宏 ({cnt} 事件)", fg="green").pack()
            except:
                self.has_macro = False
        
        frm = tk.Frame(self.root)
        frm.pack(pady=20)
        tk.Button(frm, text="🎬 录制", command=self._record, bg="#4CAF50", fg="white", width=10, height=2).pack(side=tk.LEFT, padx=5)
        if self.has_macro:
            tk.Button(frm, text="▶ 回放", command=self._play, bg="#2196F3", fg="white", width=10, height=2).pack(side=tk.LEFT, padx=5)
            tk.Button(frm, text="🗑️ 删除", command=self._delete, bg="#FF9800", fg="white", width=10, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.root, text="录制: 按3次1停止", font=("微软雅黑", 8), fg="gray").pack(pady=10)
        tk.Button(self.root, text="退出", command=self.root.quit, width=8).pack()
    
    def _record(self):
        self.root.withdraw()
        RecorderWindow(self.root, self.macro_file, self._refresh)
    
    def _play(self):
        self.root.withdraw()
        PlayerWindow(self.root, self._refresh)
    
    def _delete(self):
        if messagebox.askyesno("确认", "删除宏文件？"):
            os.remove(self.macro_file)
            self._refresh()
    
    def _refresh(self):
        self.root.deiconify()
        for w in self.root.winfo_children():
            w.destroy()
        self.has_macro = os.path.exists(self.macro_file)
        self._build()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    MainApp().run()