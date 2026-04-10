import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes

# 全局变量
recording = False
events = []
start_time = 0
key1_presses = []
max_events = 50000
keyboard_hook = None
mouse_hook = None

# Windows API 常量
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def keyboard_proc(nCode, wParam, lParam):
    global recording, events, key1_presses
    if nCode >= 0 and recording:
        vkCode = ctypes.cast(lParam, ctypes.POINTER(wintypes.DWORD))[0]
        t = time.time() - start_time
        
        if vkCode == 49:
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
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("宏录制器")
        self.root.geometry("320x220")
        
        self.save_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "macro.json")
        
        self.setup_gui()
        
    def setup_gui(self):
        tk.Label(self.root, text="🔴 宏录制器", font=("微软雅黑", 14, "bold"), fg="red").pack(pady=15)
        
        self.time_label = tk.Label(self.root, text="录制时长: 0 秒", font=("微软雅黑", 10))
        self.time_label.pack()
        
        self.event_label = tk.Label(self.root, text="事件数量: 0", font=("微软雅黑", 10))
        self.event_label.pack(pady=5)
        
        tk.Label(self.root, text="停止方式: 点击按钮 或 快速按3次数字键1", 
                font=("微软雅黑", 9), fg="gray").pack(pady=15)
        
        self.stop_btn = tk.Button(self.root, text="开始录制", 
                                  command=self.start_recording,
                                  bg="#4CAF50", fg="white",
                                  width=15, height=2)
        self.stop_btn.pack(pady=10)
        
        tk.Button(self.root, text="退出", command=self.root.quit, width=10).pack()
        
    def start_recording(self):
        global recording, start_time, keyboard_hook, mouse_hook, events, key1_presses
        
        recording = True
        events = []
        key1_presses = []
        start_time = time.time()
        
        self.stop_btn.config(text="停止录制", command=self.stop_recording, bg="#f44336")
        
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
                
            self.root.after(200, self.update_status)
    
    def stop_recording(self):
        global recording, keyboard_hook, mouse_hook
        
        recording = False
        
        if keyboard_hook:
            user32.UnhookWindowsHookEx(keyboard_hook)
        if mouse_hook:
            user32.UnhookWindowsHookEx(mouse_hook)
        
        self.stop_btn.config(text="开始录制", command=self.start_recording, bg="#4CAF50")
        self.save_macro()
    
    def save_macro(self):
        global events
        
        if not events:
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
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MacroRecorder()
    app.run()