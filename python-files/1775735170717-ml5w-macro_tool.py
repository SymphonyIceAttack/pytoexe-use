import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk
import ctypes
from ctypes import wintypes

# 使用 Windows API 实现键盘鼠标监听，不依赖 pynput
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 全局变量
recording = False
events = []
start_time = 0
key1_presses = []
max_events = 50000

# 键盘钩子句柄
keyboard_hook = None
mouse_hook = None

# 定义钩子类型
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEMOVE = 0x0200

def keyboard_proc(nCode, wParam, lParam):
    global recording, events, key1_presses
    if nCode >= 0 and recording:
        vkCode = ctypes.cast(lParam, ctypes.POINTER(wintypes.DWORD))[0]
        t = time.time() - start_time
        
        if vkCode == 49:  # 数字1
            if wParam == WM_KEYDOWN:
                now = time.time()
                key1_presses.append(now)
                key1_presses = [ts for ts in key1_presses if now - ts <= 2.0]
        
        event_type = "key_press" if wParam == WM_KEYDOWN else "key_release"
        events.append({
            "type": event_type,
            "key": str(vkCode),
            "time": t
        })
        
        if len(events) > max_events:
            recording = False
    return user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)

def mouse_proc(nCode, wParam, lParam):
    global recording, events
    if nCode >= 0 and recording:
        t = time.time() - start_time
        pt = ctypes.cast(lParam, ctypes.POINTER(wintypes.POINT))[0]
        
        if wParam == WM_MOUSEMOVE:
            events.append({
                "type": "mouse_move",
                "x": pt.x,
                "y": pt.y,
                "time": t
            })
        elif wParam in [WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN, WM_RBUTTONUP]:
            pressed = wParam in [WM_LBUTTONDOWN, WM_RBUTTONDOWN]
            button = "left" if wParam in [WM_LBUTTONDOWN, WM_LBUTTONUP] else "right"
            events.append({
                "type": "mouse_click",
                "button": button,
                "pressed": pressed,
                "time": t
            })
        
        if len(events) > max_events:
            recording = False
    return user32.CallNextHookEx(mouse_hook, nCode, wParam, lParam)

class MacroRecorder:
    def __init__(self, parent, save_path, on_close_callback):
        global recording, events, start_time, key1_presses, keyboard_hook, mouse_hook
        
        self.parent = parent
        self.save_path = save_path
        self.on_close_callback = on_close_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("宏录制中")
        self.window.geometry("320x220")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_gui()
        
        recording = False
        events = []
        key1_presses = []
        
        self.window.after(500, self.start_recording)
        
    def setup_gui(self):
        tk.Label(self.window, text="🔴 正在录制宏", 
                font=("微软雅黑", 14, "bold"), fg="red").pack(pady=15)
        
        self.time_label = tk.Label(self.window, text="录制时长: 0 秒", font=("微软雅黑", 10))
        self.time_label.pack()
        
        self.event_label = tk.Label(self.window, text="事件数量: 0", font=("微软雅黑", 10))
        self.event_label.pack(pady=5)
        
        tk.Label(self.window, text="停止方式:", font=("微软雅黑", 10, "bold")).pack(pady=(15,5))
        tk.Label(self.window, text="• 点击下方按钮", fg="gray").pack()
        tk.Label(self.window, text="• 快速按 3 次数字键 1", fg="gray").pack()
        
        self.stop_btn = tk.Button(self.window, text="停止录制", 
                                  command=self.stop_recording,
                                  bg="#f44336", fg="white",
                                  width=15, height=2)
        self.stop_btn.pack(pady=15)
        
    def start_recording(self):
        global recording, start_time, keyboard_hook, mouse_hook
        
        recording = True
        start_time = time.time()
        
        module = kernel32.GetModuleHandleW(None)
        keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_proc, module, 0)
        mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc, module, 0)
        
        self.update_status()
        
    def update_status(self):
        global recording, events, key1_presses
        
        if recording:
            duration = int(time.time() - start_time)
            self.time_label.config(text=f"录制时长: {duration} 秒")
            self.event_label.config(text=f"事件数量: {len(events)}")
            
            if len(key1_presses) >= 3:
                self.stop_recording()
                return
                
            self.window.after(200, self.update_status)
    
    def stop_recording(self):
        global recording, keyboard_hook, mouse_hook
        
        if not recording:
            return
            
        recording = False
        
        if keyboard_hook:
            user32.UnhookWindowsHookEx(keyboard_hook)
        if mouse_hook:
            user32.UnhookWindowsHookEx(mouse_hook)
        
        self.stop_btn.config(state="disabled", text="保存中...")
        self.save_macro()
    
    def save_macro(self):
        global events
        
        if not events:
            self.window.destroy()
            return
            
        playback = []
        prev_time = 0
        
        for ev in events:
            delay = ev["time"] - prev_time
            prev_time = ev["time"]
            
            if ev["type"] == "mouse_move":
                playback.append({
                    "type": "mouse_move",
                    "dx": ev["x"],
                    "dy": ev["y"],
                    "delay": delay
                })
            else:
                playback.append({
                    "type": ev["type"],
                    "key": ev.get("key", ""),
                    "button": ev.get("button", ""),
                    "pressed": ev.get("pressed", False),
                    "delay": delay
                })
        
        try:
            with open(self.save_path, "w", encoding='utf-8') as f:
                json.dump(playback, f)
            messagebox.showinfo("录制完成", f"宏已保存！\n事件数量: {len(playback)}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
        
        self.window.destroy()
    
    def on_close(self):
        global recording
        if recording:
            self.stop_recording()
        else:
            self.window.destroy()
        
        if self.on_close_callback:
            self.on_close_callback()


class PlaybackController:
    def __init__(self, parent, on_close_callback):
        try:
            import serial
            import serial.tools.list_ports
            self.serial = serial
        except ImportError:
            messagebox.showerror("错误", "缺少串口组件")
            on_close_callback()
            return
        
        self.parent = parent
        self.on_close_callback = on_close_callback
        self.serial_port = None
        self.connected = False
        
        self.window = tk.Toplevel(parent)
        self.window.title("宏回放")
        self.window.geometry("300x180")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.status_label = tk.Label(self.window, text="等待设备连接...", 
                                     font=("微软雅黑", 11), fg="orange")
        self.status_label.pack(pady=30)
        
        self.progress = ttk.Progressbar(self.window, mode='indeterminate', length=200)
        self.progress.pack()
        self.progress.start()
        
        tk.Label(self.window, text="等待RP2040设备...", 
                font=("微软雅黑", 9), fg="gray").pack(pady=20)
        
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
            ports = self.serial.tools.list_ports.comports()
            for port in ports:
                if any(x in str(port.description) for x in ["RP2040", "CircuitPython", "Pico", "USB Serial"]):
                    self.serial_port = self.serial.Serial(port.device, 115200, timeout=1)
                    return True
        except:
            pass
        return False
    
    def send_command(self, cmd):
        if self.serial_port:
            try:
                self.serial_port.write(f"{cmd}\n".encode())
                return True
            except:
                pass
        return False
    
    def on_close(self):
        if self.connected:
            self.send_command("STOP")
        self.window.destroy()
        if self.on_close_callback:
            self.on_close_callback()


class MacroLauncher:
    def __init__(self):
        self.drive_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.macro_file = os.path.join(self.drive_path, "macro.json")
        self.has_macro = os.path.exists(self.macro_file)
        
        self.root = tk.Tk()
        self.root.title("智能宏工具")
        self.root.geometry("350x280")
        
        self.setup_gui()
        
    def setup_gui(self):
        tk.Label(self.root, text="智能宏录制/回放工具", 
                font=("微软雅黑", 14, "bold")).pack(pady=20)
        
        if self.has_macro:
            try:
                with open(self.macro_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                tk.Label(self.root, text=f"✅ 已有宏文件 ({len(data)} 个事件)", 
                        fg="green", font=("微软雅黑", 10)).pack()
            except:
                self.has_macro = False
                tk.Label(self.root, text="📝 暂无宏文件", fg="gray").pack()
        else:
            tk.Label(self.root, text="📝 暂无宏文件", fg="gray").pack()
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=25)
        
        tk.Button(btn_frame, text="🎬 录制新宏", command=self.start_record,
                 bg="#4CAF50", fg="white", font=("微软雅黑", 11),
                 width=12, height=2).pack(side=tk.LEFT, padx=8)
        
        if self.has_macro:
            tk.Button(btn_frame, text="▶ 回放宏", command=self.start_playback,
                     bg="#2196F3", fg="white", font=("微软雅黑", 11),
                     width=12, height=2).pack(side=tk.LEFT, padx=8)
            
            tk.Button(btn_frame, text="🗑️ 删除宏", command=self.delete_macro,
                     bg="#FF9800", fg="white", font=("微软雅黑", 11),
                     width=12, height=2).pack(side=tk.LEFT, padx=8)
        
        tk.Label(self.root, text="录制: 按3次1停止", 
                font=("微软雅黑", 8), fg="gray").pack(pady=15)
        
        tk.Button(self.root, text="退出", command=self.root.quit,
                 width=10).pack()
    
    def refresh_ui(self):
        self.has_macro = os.path.exists(self.macro_file)
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_gui()
    
    def start_record(self):
        self.root.withdraw()
        self.recorder = MacroRecorder(self.root, self.macro_file, self.on_recorder_close)
    
    def on_recorder_close(self):
        self.root.deiconify()
        self.refresh_ui()
    
    def start_playback(self):
        self.root.withdraw()
        self.controller = PlaybackController(self.root, self.on_controller_close)
    
    def on_controller_close(self):
        self.root.deiconify()
        self.refresh_ui()
    
    def delete_macro(self):
        if messagebox.askyesno("确认", "删除宏文件？"):
            try:
                os.remove(self.macro_file)
                messagebox.showinfo("完成", "已删除")
                self.refresh_ui()
            except Exception as e:
                messagebox.showerror("错误", str(e))
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MacroLauncher()
    app.run()