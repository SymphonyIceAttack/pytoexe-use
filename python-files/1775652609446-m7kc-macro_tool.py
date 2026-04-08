import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk

# 自动安装依赖
try:
    from pynput import keyboard, mouse
    import serial
    import serial.tools.list_ports
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput", "pyserial"])
    from pynput import keyboard, mouse
    import serial
    import serial.tools.list_ports

class MacroRecorder:
    def __init__(self, parent, save_path):
        self.parent = parent
        self.save_path = save_path
        self.recording = False
        self.events = []
        self.start_time = 0
        self.key1_presses = []
        
        self.window = tk.Toplevel(parent)
        self.window.title("宏录制中")
        self.window.geometry("300x200")
        
        tk.Label(self.window, text="🔴 正在录制宏", font=("Arial", 14), fg="red").pack(pady=20)
        self.time_label = tk.Label(self.window, text="录制时长: 0.0 秒")
        self.time_label.pack()
        
        self.stop_btn = tk.Button(self.window, text="停止录制", command=self.stop_recording,
                                  bg="red", fg="white", width=15)
        self.stop_btn.pack(pady=20)
        
        tk.Label(self.window, text="快速按3次数字1也可停止", font=("Arial", 8), fg="gray").pack()
        
        self.window.after(500, self.start_recording)
        
    def start_recording(self):
        self.recording = True
        self.start_time = time.time()
        self.key1_presses = []
        
        self.k_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.m_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click)
        self.k_listener.start()
        self.m_listener.start()
        self.update_status()
        
    def on_press(self, key):
        if not self.recording: return
        t = time.time() - self.start_time
        try:
            if hasattr(key, 'char') and key.char == '1':
                now = time.time()
                self.key1_presses.append(now)
                self.key1_presses = [ts for ts in self.key1_presses if now - ts <= 2.0]
                if len(self.key1_presses) >= 3:
                    self.window.after(0, self.stop_recording)
                    return
                key_name = '1'
            elif hasattr(key, 'name'):
                key_name = key.name
            else:
                key_name = str(key)
            self.events.append({"type": "key_press", "key": key_name, "time": t})
        except: pass
        
    def on_release(self, key):
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
        except: pass
    
    def on_move(self, x, y):
        if self.recording:
            t = time.time() - self.start_time
            self.events.append({"type": "mouse_move", "x": x, "y": y, "time": t})
    
    def on_click(self, x, y, button, pressed):
        if self.recording:
            t = time.time() - self.start_time
            self.events.append({"type": "mouse_click", "button": str(button).split('.')[-1], 
                               "pressed": pressed, "time": t})
    
    def update_status(self):
        if self.recording:
            duration = time.time() - self.start_time
            self.time_label.config(text=f"录制时长: {duration:.1f} 秒")
            self.window.after(100, self.update_status)
    
    def stop_recording(self):
        if not self.recording: return
        self.recording = False
        self.k_listener.stop()
        self.m_listener.stop()
        self.save_macro()
    
    def save_macro(self):
        if not self.events:
            self.window.destroy()
            return
        playback = []
        prev_time = 0
        for ev in self.events:
            delay = ev["time"] - prev_time
            prev_time = ev["time"]
            if ev["type"] == "mouse_move":
                playback.append({"type": "mouse_move", "dx": ev["x"], "dy": ev["y"], "delay": delay})
            else:
                playback.append({"type": ev["type"], "key": ev.get("key", ""), 
                               "button": ev.get("button", ""), "pressed": ev.get("pressed", False), 
                               "delay": delay})
        with open(self.save_path, "w", encoding='utf-8') as f:
            json.dump(playback, f)
        self.window.destroy()
        messagebox.showinfo("完成", f"宏已保存！\n事件数: {len(playback)}")

class PlaybackController:
    def __init__(self, parent):
        self.parent = parent
        self.serial_port = None
        self.connected = False
        self.key2_presses = []
        
        self.window = tk.Toplevel(parent)
        self.window.title("宏回放")
        self.window.geometry("300x200")
        
        self.status_label = tk.Label(self.window, text="等待设备...", font=("Arial", 12), fg="orange")
        self.status_label.pack(pady=30)
        
        self.progress = ttk.Progressbar(self.window, mode='indeterminate', length=200)
        self.progress.pack()
        self.progress.start()
        
        tk.Label(self.window, text="快速按2次数字2暂停\n快速按3次数字2停止", 
                font=("Arial", 9), fg="gray").pack(pady=20)
        
        self.start_hotkey_listener()
        self.check_connection()
    
    def check_connection(self):
        if not self.connected:
            if self.find_rp2040():
                self.connected = True
                self.status_label.config(text="已连接 - 正在回放", fg="green")
                self.progress.stop()
                self.progress.pack_forget()
                self.send_command("START")
        if not self.connected:
            self.window.after(1000, self.check_connection)
    
    def find_rp2040(self):
        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if any(x in str(port.description) for x in ["RP2040", "CircuitPython", "Pico", "USB Serial"]):
                    self.serial_port = serial.Serial(port.device, 115200, timeout=1)
                    return True
        except: pass
        return False
    
    def send_command(self, cmd):
        if self.serial_port:
            try:
                self.serial_port.write(f"{cmd}\n".encode())
                return True
            except: pass
        return False
    
    def toggle_pause(self):
        self.send_command("PAUSE")
    
    def stop_playback(self):
        if messagebox.askyesno("确认", "停止回放？"):
            self.send_command("STOP")
            self.window.destroy()
    
    def start_hotkey_listener(self):
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char == '2':
                    now = time.time()
                    self.key2_presses.append(now)
                    self.key2_presses = [ts for ts in self.key2_presses if now - ts <= 2.0]
                    if len(self.key2_presses) == 2:
                        self.window.after(0, self.toggle_pause)
                    elif len(self.key2_presses) >= 3:
                        self.window.after(0, self.stop_playback)
            except: pass
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()

class MacroLauncher:
    def __init__(self):
        self.drive_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.macro_file = os.path.join(self.drive_path, "macro.json")
        self.has_macro = os.path.exists(self.macro_file)
        
        self.root = tk.Tk()
        self.root.title("智能宏工具")
        self.root.geometry("350x300")
        
        tk.Label(self.root, text="智能宏录制/回放工具", font=("Arial", 14, "bold")).pack(pady=20)
        
        if self.has_macro:
            try:
                with open(self.macro_file, 'r') as f:
                    data = json.load(f)
                tk.Label(self.root, text=f"已有宏文件 ({len(data)} 个事件)", fg="green").pack()
            except:
                self.has_macro = False
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=30)
        
        tk.Button(btn_frame, text="录制新宏", command=self.start_record,
                 bg="green", fg="white", width=12, height=2).pack(side=tk.LEFT, padx=10)
        
        if self.has_macro:
            tk.Button(btn_frame, text="回放宏", command=self.start_playback,
                     bg="blue", fg="white", width=12, height=2).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="删除宏", command=self.delete_macro,
                     bg="orange", fg="white", width=12, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(self.root, text="退出", command=self.root.quit, width=10).pack(pady=20)
    
    def start_record(self):
        self.root.withdraw()
        recorder = MacroRecorder(self.root, self.macro_file)
        def check():
            if recorder.window.winfo_exists():
                self.root.after(100, check)
            else:
                self.root.deiconify()
                self.root.destroy()
                MacroLauncher().run()
        check()
    
    def start_playback(self):
        self.root.withdraw()
        controller = PlaybackController(self.root)
        def check():
            if controller.window.winfo_exists():
                self.root.after(100, check)
            else:
                self.root.deiconify()
        check()
    
    def delete_macro(self):
        if messagebox.askyesno("确认", "删除宏文件？"):
            os.remove(self.macro_file)
            messagebox.showinfo("完成", "已删除")
            self.root.destroy()
            MacroLauncher().run()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    app = MacroLauncher()
    app.run()