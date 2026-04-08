import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk

# 延迟导入
keyboard = None
mouse = None
serial = None

class MacroRecorder:
    def __init__(self, parent, save_path, on_close_callback):
        global keyboard, mouse
        try:
            from pynput import keyboard as kb, mouse as ms
            keyboard = kb
            mouse = ms
        except ImportError:
            messagebox.showerror("错误", "缺少必要组件")
            on_close_callback()
            return
        
        self.parent = parent
        self.save_path = save_path
        self.on_close_callback = on_close_callback
        self.recording = False
        self.events = []
        self.start_time = 0
        self.key1_presses = []
        self.max_events = 50000
        
        self.window = tk.Toplevel(parent)
        self.window.title("宏录制中")
        self.window.geometry("320x220")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_gui()
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
        self.recording = True
        self.start_time = time.time()
        self.key1_presses = []
        
        self.k_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.m_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click
        )
        self.k_listener.start()
        self.m_listener.start()
        
        self.update_status()
        
    def on_press(self, key):
        if not self.recording:
            return
        
        if len(self.events) > self.max_events:
            self.window.after(0, self.stop_recording)
            return
        
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
                return
                
            self.events.append({
                "type": "key_press",
                "key": key_name,
                "time": t
            })
        except:
            pass
        
    def on_release(self, key):
        if not self.recording:
            return
        
        if len(self.events) > self.max_events:
            self.window.after(0, self.stop_recording)
            return
        
        t = time.time() - self.start_time
        
        try:
            if hasattr(key, 'char') and key.char == '1':
                key_name = '1'
            elif hasattr(key, 'name'):
                key_name = key.name
            else:
                return
                
            self.events.append({
                "type": "key_release",
                "key": key_name,
                "time": t
            })
        except:
            pass
    
    def on_move(self, x, y):
        if not self.recording:
            return
        
        if len(self.events) > self.max_events:
            self.window.after(0, self.stop_recording)
            return
        
        t = time.time() - self.start_time
        
        if self.events and self.events[-1]["type"] == "mouse_move":
            last = self.events[-1]
            if abs(last["x"] - x) < 5 and abs(last["y"] - y) < 5:
                return
        
        self.events.append({
            "type": "mouse_move",
            "x": x,
            "y": y,
            "time": t
        })
    
    def on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        
        if len(self.events) > self.max_events:
            self.window.after(0, self.stop_recording)
            return
        
        t = time.time() - self.start_time
        self.events.append({
            "type": "mouse_click",
            "button": str(button).split('.')[-1],
            "pressed": pressed,
            "time": t
        })
    
    def update_status(self):
        if self.recording:
            duration = int(time.time() - self.start_time)
            self.time_label.config(text=f"录制时长: {duration} 秒")
            self.event_label.config(text=f"事件数量: {len(self.events)}")
            self.window.after(200, self.update_status)
    
    def stop_recording(self):
        if not self.recording:
            return
            
        self.recording = False
        try:
            self.k_listener.stop()
            self.m_listener.stop()
        except:
            pass
        
        self.stop_btn.config(state="disabled", text="保存中...")
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
        if self.recording:
            self.stop_recording()
        else:
            self.window.destroy()
        
        # 调用回调而不是递归重建
        if self.on_close_callback:
            self.on_close_callback()


class PlaybackController:
    def __init__(self, parent, on_close_callback):
        global serial
        try:
            import serial as ser
            import serial.tools.list_ports
            serial = ser
        except ImportError:
            messagebox.showerror("错误", "缺少串口组件")
            on_close_callback()
            return
        
        self.parent = parent
        self.on_close_callback = on_close_callback
        self.serial_port = None
        self.connected = False
        self.key2_presses = []
        
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
        
        tk.Label(self.window, text="快速按2次数字2暂停 / 3次停止", 
                font=("微软雅黑", 9), fg="gray").pack(pady=20)
        
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
    
    def toggle_pause(self):
        self.send_command("PAUSE")
        current = self.status_label.cget("text")
        if "暂停" in current:
            self.status_label.config(text="已连接 - 正在回放", fg="green")
        else:
            self.status_label.config(text="已暂停", fg="orange")
    
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
                        self.key2_presses = []
            except:
                pass
        
        try:
            from pynput import keyboard as kb
            listener = kb.Listener(on_press=on_press)
            listener.daemon = True
            listener.start()
        except:
            pass
    
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
        
        tk.Label(self.root, text="录制: 按3次1停止 | 回放: 按2次2暂停/3次停止", 
                font=("微软雅黑", 8), fg="gray").pack(pady=15)
        
        tk.Button(self.root, text="退出", command=self.root.quit,
                 width=10).pack()
    
    def refresh_ui(self):
        """刷新主界面，而不是重新创建实例"""
        self.has_macro = os.path.exists(self.macro_file)
        # 销毁所有子控件
        for widget in self.root.winfo_children():
            widget.destroy()
        # 重新构建界面
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