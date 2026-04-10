import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk
import ctypes
from ctypes import wintypes

# ========== 全局变量 ==========
recording = False
events = []
start_time = 0
key1_presses = []
keyboard_hook = None
mouse_hook = None
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Windows API 常量
WH_KEYBOARD_LL, WH_MOUSE_LL = 13, 14
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0201, 0x0202
WM_RBUTTONDOWN, WM_RBUTTONUP = 0x0204, 0x0205
WM_MOUSEMOVE = 0x0200

def keyboard_proc(nCode, wParam, lParam):
    global recording, events, key1_presses
    if nCode >= 0 and recording:
        vkCode = ctypes.cast(lParam, ctypes.POINTER(wintypes.DWORD))[0]
        t = time.time() - start_time
        if vkCode == 49 and wParam == WM_KEYDOWN:
            now = time.time()
            key1_presses.append(now)
            key1_presses = [ts for ts in key1_presses if now - ts <= 2.0]
        events.append({"type": "key_press" if wParam == WM_KEYDOWN else "key_release", "key": str(vkCode), "time": t})
        if len(events) > 50000:
            recording = False
    return user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)

def mouse_proc(nCode, wParam, lParam):
    global recording, events
    if nCode >= 0 and recording:
        t = time.time() - start_time
        pt = ctypes.cast(lParam, ctypes.POINTER(wintypes.POINT))[0]
        if wParam == WM_MOUSEMOVE:
            events.append({"type": "mouse_move", "x": pt.x, "y": pt.y, "time": t})
        elif wParam in (WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN, WM_RBUTTONUP):
            events.append({"type": "mouse_click", "button": "left" if wParam in (WM_LBUTTONDOWN, WM_LBUTTONUP) else "right", "pressed": wParam in (WM_LBUTTONDOWN, WM_RBUTTONDOWN), "time": t})
        if len(events) > 50000:
            recording = False
    return user32.CallNextHookEx(mouse_hook, nCode, wParam, lParam)

# ========== 录制窗口 ==========
class RecorderWindow:
    def __init__(self, parent, save_path, on_close):
        self.parent = parent
        self.save_path = save_path
        self.on_close = on_close
        self.win = tk.Toplevel(parent)
        self.win.title("录制中")
        self.win.geometry("300x200")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)
        
        tk.Label(self.win, text="🔴 录制中", font=("微软雅黑", 14), fg="red").pack(pady=15)
        self.time_lbl = tk.Label(self.win, text="时长: 0 秒")
        self.time_lbl.pack()
        self.event_lbl = tk.Label(self.win, text="事件: 0")
        self.event_lbl.pack(pady=5)
        
        self.btn = tk.Button(self.win, text="停止录制", command=self.stop, bg="#f44336", fg="white", width=15)
        self.btn.pack(pady=15)
        tk.Label(self.win, text="按3次数字1停止", font=("微软雅黑", 8), fg="gray").pack()
        
        self.win.after(500, self.start)
    
    def start(self):
        global recording, start_time, events, key1_presses, keyboard_hook, mouse_hook
        recording = True
        events, key1_presses = [], []
        start_time = time.time()
        module = kernel32.GetModuleHandleW(None)
        keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, keyboard_proc, module, 0)
        mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc, module, 0)
        self._update()
    
    def _update(self):
        if recording:
            self.time_lbl.config(text=f"时长: {int(time.time()-start_time)} 秒")
            self.event_lbl.config(text=f"事件: {len(events)}")
            if len(key1_presses) >= 3:
                self.stop()
            else:
                self.win.after(200, self._update)
    
    def stop(self):
        global recording, keyboard_hook, mouse_hook
        if not recording:
            return
        recording = False
        if keyboard_hook:
            user32.UnhookWindowsHookEx(keyboard_hook)
        if mouse_hook:
            user32.UnhookWindowsHookEx(mouse_hook)
        self.btn.config(state="disabled", text="保存中...")
        self._save()
    
    def _save(self):
        if events:
            playback, prev = [], 0
            for e in events:
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
        if recording:
            self.stop()
        else:
            self.win.destroy()
            self.on_close()

# ========== 回放窗口 ==========
class PlayerWindow:
    def __init__(self, parent, on_close):
        self.parent = parent
        self.on_close = on_close
        self.serial = None
        self.connected = False
        
        self.win = tk.Toplevel(parent)
        self.win.title("回放中")
        self.win.geometry("280x160")
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
        self.root.geometry("320x250")
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