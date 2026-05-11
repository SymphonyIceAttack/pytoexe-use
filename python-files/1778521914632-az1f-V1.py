import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import socket
import threading
import time
from collections import OrderedDict
from pynput import keyboard
import queue

# ================== 网络发送器（无额外字符） ==================
class AsyncSender:
    def __init__(self):
        self.sock = None
        self.send_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        # 频率限制
        self.max_rate = 0
        self.min_interval = 0.0
        self.last_sent_time = 0.0
        self.rate_lock = threading.Lock()
        # 静默期
        self.silent_until = 0.0
        self.silent_lock = threading.Lock()
        self.discard_callback = None
        self.success_callback = None

    def set_rate_limit(self, rate_per_sec):
        with self.rate_lock:
            if rate_per_sec > 0:
                self.max_rate = rate_per_sec
                self.min_interval = 1.0 / rate_per_sec
            else:
                self.max_rate = 0
                self.min_interval = 0.0

    def set_silent_period(self, duration_sec):
        with self.silent_lock:
            self.silent_until = time.time() + duration_sec
        if self.discard_callback:
            self.discard_callback(f"[静默] 接下来 {duration_sec} 秒内不发送")

    def is_silent(self):
        with self.silent_lock:
            return time.time() < self.silent_until

    def connect(self, ip, port):
        self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3)
            self.sock.connect((ip, port))
            self.sock.setblocking(True)
            self.running = True
            self.worker_thread = threading.Thread(target=self._sender_worker, daemon=True)
            self.worker_thread.start()
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {e}"

    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=0.5)

    def send(self, data: str):
        if not (self.running and self.sock):
            return
        if self.is_silent():
            if self.discard_callback:
                self.discard_callback(f"[静默丢弃] {data}")
            return
        self.send_queue.put(data)

    def _sender_worker(self):
        while self.running and self.sock:
            try:
                data = self.send_queue.get(timeout=0.1)
                if self.max_rate > 0:
                    now = time.time()
                    with self.rate_lock:
                        elapsed = now - self.last_sent_time
                        if elapsed < self.min_interval:
                            if self.discard_callback:
                                self.discard_callback(f"[限频丢弃] {data}")
                            continue
                        self.last_sent_time = now
                try:
                    self.sock.sendall(data.encode('utf-8'))
                    if self.success_callback:
                        self.success_callback(data)
                except Exception as e:
                    if self.discard_callback:
                        self.discard_callback(f"[网络错误] {e}")
                    self.running = False
            except queue.Empty:
                continue

# ================== 键盘监听核心（支持组合键发送） ==================
class KeyboardForwarder:
    ALLOWED_SPECIAL_KEYS = {
        'space': 'Space', 'enter': 'Enter', 'tab': 'Tab',
        'backspace': 'Backspace', 'delete': 'Delete',
        'up': 'Up', 'down': 'Down', 'left': 'Left', 'right': 'Right',
        'home': 'Home', 'end': 'End', 'page_up': 'PageUp', 'page_down': 'PageDown',
        'insert': 'Insert', 'escape': 'Escape',
        'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4',
        'f5': 'F5', 'f6': 'F6', 'f7': 'F7', 'f8': 'F8',
        'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12',
    }

    def __init__(self, async_sender, status_callback, log_callback):
        self.sender = async_sender
        self.status_callback = status_callback
        self.log_callback = log_callback
        self.listener = None
        self.current_keys = OrderedDict()
        self.keys_lock = threading.Lock()
        self.long_press_active = False
        self.long_press_thread = None
        self.long_press_stop = threading.Event()
        self.last_sent_combined = None      # 上次发送的组合字符串
        self.last_sent_normal_key = None    # 保留用于单个键去重（兼容）
        self.running = False
        self.idle_timer = None

        self.sender.discard_callback = self._on_discard

    def _on_discard(self, msg):
        self.log_callback(msg)

    def _get_combined_keys(self):
        """获取当前所有按下的键组合成的字符串（按按下顺序）"""
        with self.keys_lock:
            return ''.join(self.current_keys.keys())

    def start(self):
        if self.listener and self.listener.is_alive():
            return
        self.running = True
        try:
            self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self.listener.start()
        except Exception as e:
            self.log_callback(f"[错误] 键盘监听启动失败: {e}")
            self.running = False
            return
        self._start_idle_check()
        self.status_callback("键盘监听已启动")

    def stop(self):
        self.running = False
        if self.listener:
            try:
                self.listener.stop()
            except:
                pass
        self._stop_long_press()
        if self.idle_timer:
            self.idle_timer.cancel()
            self.idle_timer = None
        self.status_callback("已停止")

    # ---------- 长按处理（发送组合字符串） ----------
    def _start_long_press(self):
        self._stop_long_press()
        self.long_press_active = True
        self.long_press_stop.clear()

        def worker():
            while self.long_press_active and self.running and not self.long_press_stop.is_set():
                combined = self._get_combined_keys()
                if combined:  # 有按键按下
                    # 组合可能变化，每次都发送（频率限制会控制实际发送速率）
                    self.sender.send(combined)
                else:
                    break
                time.sleep(0.005)
            self.long_press_active = False

        self.long_press_thread = threading.Thread(target=worker, daemon=True)
        self.long_press_thread.start()

    def _stop_long_press(self):
        self.long_press_active = False
        self.long_press_stop.set()
        if self.long_press_thread and self.long_press_thread.is_alive():
            self.long_press_thread.join(timeout=0.2)
        self.long_press_thread = None

    # ---------- 空闲检测 ----------
    def _start_idle_check(self):
        def check():
            if not self.running:
                return
            with self.keys_lock:
                is_idle = (len(self.current_keys) == 0)
            if is_idle and not self.sender.is_silent():
                self.sender.send("12345678")
            if self.running:
                self.idle_timer = threading.Timer(0.3, check)
                self.idle_timer.start()

        if self.idle_timer:
            self.idle_timer.cancel()
        self.idle_timer = threading.Timer(0.3, check)
        self.idle_timer.start()

    # ---------- 键盘按下 ----------
    def _on_press(self, key):
        if not self.running:
            return
        key_str = self._safe_key_to_str(key)
        if key_str is None:
            return

        with self.keys_lock:
            if key_str in self.current_keys:
                self.current_keys.move_to_end(key_str)  # 已按下则移到末尾
            else:
                self.current_keys[key_str] = None
            combined = ''.join(self.current_keys.keys())

        # 发送组合字符串（仅当变化时）
        if combined != self.last_sent_combined:
            self.sender.send(combined)
            self.last_sent_combined = combined

        # 长按检测：无论组合键数量，只要还有按键按下就启动长按线程（若未启动）
        if not self.long_press_active and len(self.current_keys) > 0:
            # 延迟0.2秒启动长按（避免短按误触发长按）
            if hasattr(self, '_long_timer'):
                self._long_timer.cancel()
            self._long_timer = threading.Timer(0.2, self._on_long_press_detected)
            self._long_timer.start()

    def _on_long_press_detected(self):
        # 检测时若还有按键按下且长按未激活，则启动
        if self.running and not self.long_press_active and len(self.current_keys) > 0:
            self._start_long_press()

    # ---------- 键盘松开 ----------
    def _on_release(self, key):
        if not self.running:
            return
        key_str = self._safe_key_to_str(key)
        if key_str is None:
            return

        with self.keys_lock:
            if key_str in self.current_keys:
                del self.current_keys[key_str]
            combined = ''.join(self.current_keys.keys())

        # 发送组合字符串（变化时）
        if combined != self.last_sent_combined:
            self.sender.send(combined)
            self.last_sent_combined = combined

        # 如果没有任何按键，停止长按并清空记录
        if len(self.current_keys) == 0:
            self._stop_long_press()
            self.last_sent_combined = None
            if hasattr(self, '_long_timer'):
                self._long_timer.cancel()

    # ---------- 按键安全转换 ----------
    def _safe_key_to_str(self, key):
        try:
            if hasattr(key, 'char') and key.char is not None:
                ch = key.char
                if ch and (32 <= ord(ch) <= 126 or ord(ch) >= 160):
                    return ch
                return None
            if hasattr(key, 'name'):
                name = key.name.lower()
                if name in self.ALLOWED_SPECIAL_KEYS:
                    return self.ALLOWED_SPECIAL_KEYS[name]
                return None
            return None
        except:
            return None

# ================== GUI 界面（保持不变） ==================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("键盘转发器 - 组合键发送")
        self.root.geometry("580x550")
        self.root.resizable(True, True)

        self.sender = AsyncSender()
        self.forwarder = KeyboardForwarder(self.sender, self.update_status, self.log)

        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._check_permissions()

    def _create_widgets(self):
        frame_conn = tk.LabelFrame(self.root, text="目标服务器", padx=5, pady=5)
        frame_conn.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_conn, text="IP:").grid(row=0, column=0, sticky=tk.W)
        self.ip_entry = tk.Entry(frame_conn, width=12)
        self.ip_entry.grid(row=0, column=1, padx=2)
        self.ip_entry.insert(0, "127.0.0.1")

        tk.Label(frame_conn, text="端口:").grid(row=0, column=2, sticky=tk.W)
        self.port_entry = tk.Entry(frame_conn, width=6)
        self.port_entry.grid(row=0, column=3, padx=2)
        self.port_entry.insert(0, "8888")

        self.connect_btn = tk.Button(frame_conn, text="连接", command=self.do_connect, bg="#4CAF50", fg="white")
        self.connect_btn.grid(row=0, column=4, padx=5)

        self.status_label = tk.Label(frame_conn, text="未连接", fg="red")
        self.status_label.grid(row=0, column=5, padx=5)

        frame_rate = tk.LabelFrame(self.root, text="频率限制", padx=5, pady=5)
        frame_rate.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_rate, text="发送次数/秒:").grid(row=0, column=0, sticky=tk.W)
        self.rate_spin = tk.Spinbox(frame_rate, from_=0, to=1000, width=8)
        self.rate_spin.grid(row=0, column=1, padx=5)
        self.rate_spin.delete(0, tk.END)
        self.rate_spin.insert(0, "50")
        tk.Label(frame_rate, text="(0 表示无限制)").grid(row=0, column=2, sticky=tk.W)

        self.apply_rate_btn = tk.Button(frame_rate, text="应用", command=self.apply_rate, bg="#FF9800", fg="white")
        self.apply_rate_btn.grid(row=0, column=3, padx=5)

        frame_custom = tk.LabelFrame(self.root, text="自定义消息（发送后静默3秒）", padx=5, pady=5)
        frame_custom.pack(fill=tk.X, padx=10, pady=5)

        self.custom_entry = tk.Entry(frame_custom)
        self.custom_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.send_custom_btn = tk.Button(frame_custom, text="发送并静默3秒", command=self.send_custom, bg="#2196F3", fg="white")
        self.send_custom_btn.pack(side=tk.RIGHT, padx=2)

        frame_ctrl = tk.Frame(self.root)
        frame_ctrl.pack(fill=tk.X, padx=10, pady=5)
        self.start_btn = tk.Button(frame_ctrl, text="启动键盘监听", command=self.start_forward, bg="#008CBA", fg="white", width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(frame_ctrl, text="停止监听", command=self.stop_forward, bg="#f44336", fg="white", width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        frame_log = tk.LabelFrame(self.root, text="发送日志", padx=5, pady=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(frame_log, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        tip = "提示：按住多个键时，发送组合字符串（如'ab'）。长按时持续发送当前组合。空闲时发送'12345678'。"
        tk.Label(self.root, text=tip, fg="gray", font=("Arial", 9)).pack(side=tk.BOTTOM, pady=2)

    def apply_rate(self):
        try:
            rate = int(self.rate_spin.get())
            if rate < 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入非负整数（0表示无限制）")
            return
        self.sender.set_rate_limit(rate)
        self.log(f"频率限制已设置为 {rate} 次/秒" + ("（无限制）" if rate == 0 else ""))

    def update_status(self, msg):
        self.root.after(0, lambda: self.status_label.config(text=msg))

    def log(self, msg):
        def _log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _log)

    def do_connect(self):
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        if not ip or not port_str:
            messagebox.showerror("错误", "请填写IP和端口")
            return
        try:
            port = int(port_str)
        except:
            messagebox.showerror("错误", "端口必须是整数")
            return
        ok, msg = self.sender.connect(ip, port)
        if ok:
            self.update_status(f"已连接 {ip}:{port}")
            self.connect_btn.config(bg="#45a049", text="已连接", state=tk.DISABLED)
        else:
            self.update_status("连接失败")
            messagebox.showerror("连接错误", msg)

    def send_custom(self):
        msg = self.custom_entry.get().strip()
        if not msg:
            messagebox.showwarning("警告", "自定义消息不能为空")
            return
        if not self.sender.running:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        self.sender.send(msg)
        self.log(f"自定义发送: {msg} (之后静默3秒)")
        self.sender.set_silent_period(3.0)

    def start_forward(self):
        if not self.sender.running:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        if self.forwarder.running:
            return
        try:
            rate = int(self.rate_spin.get())
            if rate < 0:
                rate = 0
        except:
            rate = 50
        self.sender.set_rate_limit(rate)
        self.forwarder.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_forward(self):
        if self.forwarder.running:
            self.forwarder.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("键盘监听已停止")

    def _check_permissions(self):
        import platform
        if platform.system() == "Linux" or platform.system() == "Darwin":
            self.log("[提示] 在 Linux/macOS 上，如果键盘监听无效，请使用 sudo 运行本程序")
        elif platform.system() == "Windows":
            self.log("[提示] 如果键盘监听无效，请以管理员身份运行")

    def on_closing(self):
        self.stop_forward()
        self.sender.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    try:
        import pynput
    except ImportError:
        print("缺少依赖库 pynput，请执行: pip install pynput")
        import sys
        sys.exit(1)

    root = tk.Tk()
    app = App(root)
    root.mainloop()