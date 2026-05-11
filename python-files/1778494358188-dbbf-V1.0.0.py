import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import socket
import threading
import time
from collections import OrderedDict, deque
from pynput import keyboard
import queue
import sys

# ================== 网络发送器 ==================
class AsyncSender:
    def __init__(self):
        self.sock = None
        self.send_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.max_rate = None
        self.min_interval = 0.0
        self.last_sent_time = 0.0
        self.rate_lock = threading.Lock()
        self.silent_until = 0.0
        self.silent_lock = threading.Lock()
        self.discard_callback = None
        self.success_callback = None

    def set_rate_limit(self, enabled, rate_per_sec):
        with self.rate_lock:
            if enabled and rate_per_sec > 0:
                self.max_rate = rate_per_sec
                self.min_interval = 1.0 / rate_per_sec
            else:
                self.max_rate = None
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
        self.send_queue.put(data + "\n")

    def _sender_worker(self):
        while self.running and self.sock:
            try:
                data = self.send_queue.get(timeout=0.1)
                if self.max_rate is not None:
                    now = time.time()
                    with self.rate_lock:
                        elapsed = now - self.last_sent_time
                        if elapsed < self.min_interval:
                            if self.discard_callback:
                                self.discard_callback(f"[限频丢弃] {data.strip()}")
                            continue
                        self.last_sent_time = now
                try:
                    self.sock.sendall(data.encode('utf-8'))
                    if self.success_callback:
                        self.success_callback(data.strip())
                except Exception as e:
                    if self.discard_callback:
                        self.discard_callback(f"[网络错误] {e}")
                    self.running = False
            except queue.Empty:
                continue

# ================== 键盘监听核心 ==================
class KeyboardForwarder:
    def __init__(self, async_sender, status_callback, log_callback):
        self.sender = async_sender
        self.status_callback = status_callback
        self.log_callback = log_callback
        self.listener = None
        self.current_keys = OrderedDict()
        self.long_press_active = False
        self.long_press_thread = None
        self.long_press_stop = threading.Event()
        self.last_sent_normal_key = None
        self.idle_timer = None
        self.running = False
        self.sender.discard_callback = self._on_discard

    def _on_discard(self, msg):
        self.log_callback(msg)

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
            self.listener.stop()
        self._stop_long_press()
        if self.idle_timer:
            self.idle_timer.cancel()
        self.status_callback("已停止")

    def _start_long_press(self, key_value):
        self._stop_long_press()
        self.long_press_active = True
        self.long_press_stop.clear()

        def worker():
            while self.long_press_active and self.running and not self.long_press_stop.is_set():
                if self.current_keys:
                    latest = next(reversed(self.current_keys))
                    self.sender.send(latest)
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

    def _start_idle_check(self):
        def check():
            if not self.running:
                return
            # 只有在没有按键按下且不处于静默期时，才发送空字符
            if not self.current_keys and not self.sender.is_silent():
                self.sender.send("")
            if self.running:
                self.idle_timer = threading.Timer(0.3, check)
                self.idle_timer.start()

        if self.idle_timer:
            self.idle_timer.cancel()
        self.idle_timer = threading.Timer(0.3, check)
        self.idle_timer.start()

    def _on_press(self, key):
        if not self.running:
            return
        key_str = self._key_to_str(key)
        if not key_str:
            return

        if key_str in self.current_keys:
            self.current_keys.move_to_end(key_str)
        else:
            self.current_keys[key_str] = None

        if key_str != self.last_sent_normal_key:
            self.sender.send(key_str)
            self.last_sent_normal_key = key_str

        if hasattr(self, '_long_timer'):
            self._long_timer.cancel()
        self._long_timer = threading.Timer(0.2, lambda: self._on_long_detected(key_str))
        self._long_timer.start()

    def _on_long_detected(self, key_str):
        if self.running and key_str in self.current_keys and not self.long_press_active:
            self._start_long_press(key_str)

    def _on_release(self, key):
        if not self.running:
            return
        key_str = self._key_to_str(key)
        if not key_str:
            return

        if key_str in self.current_keys:
            del self.current_keys[key_str]

        if not self.current_keys:
            self._stop_long_press()
            self.last_sent_normal_key = None
            if hasattr(self, '_long_timer'):
                self._long_timer.cancel()

    @staticmethod
    def _key_to_str(key):
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            else:
                return str(key).replace('Key.', '')
        except:
            return None

# ================== GUI ==================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("键盘转发器 - 可配置静默时间")
        self.root.geometry("640x650")
        self.root.resizable(True, True)

        self.sender = AsyncSender()
        self.forwarder = KeyboardForwarder(self.sender, self.update_status, self.log)

        self.recent_sent = deque(maxlen=10)
        self.sender.success_callback = self.record_sent

        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self._check_permissions()

    def _create_widgets(self):
        # 连接区
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

        # 频率限制区
        frame_rate = tk.LabelFrame(self.root, text="频率限制", padx=5, pady=5)
        frame_rate.pack(fill=tk.X, padx=10, pady=5)
        self.rate_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(frame_rate, text="启用", variable=self.rate_enabled, command=self._toggle_rate).grid(row=0, column=0)
        tk.Label(frame_rate, text="次/秒:").grid(row=0, column=1)
        self.rate_spin = tk.Spinbox(frame_rate, from_=1, to=1000, width=6)
        self.rate_spin.grid(row=0, column=2)
        self.rate_spin.delete(0, tk.END)
        self.rate_spin.insert(0, "50")
        tk.Button(frame_rate, text="应用", command=self.apply_rate, bg="#FF9800", fg="white").grid(row=0, column=3, padx=5)

        # 自定义消息区域（含静默时间选择）
        frame_custom = tk.LabelFrame(self.root, text="自定义消息发送", padx=5, pady=5)
        frame_custom.pack(fill=tk.X, padx=10, pady=5)

        # 第一行：消息输入
        row0 = tk.Frame(frame_custom)
        row0.pack(fill=tk.X, pady=2)
        tk.Label(row0, text="消息内容:").pack(side=tk.LEFT)
        self.custom_entry = tk.Entry(row0)
        self.custom_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # 第二行：静默时间选择 + 发送按钮
        row1 = tk.Frame(frame_custom)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="静默时间:").pack(side=tk.LEFT)
        self.silent_time_var = tk.IntVar(value=3)
        # 提供下拉选择常见值，同时也允许手动输入
        self.silent_combo = ttk.Combobox(row1, textvariable=self.silent_time_var, values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30], width=5)
        self.silent_combo.pack(side=tk.LEFT, padx=2)
        tk.Label(row1, text="秒").pack(side=tk.LEFT)
        # 发送按钮
        self.send_custom_btn = tk.Button(row1, text="发送并静默", command=self.send_custom, bg="#2196F3", fg="white")
        self.send_custom_btn.pack(side=tk.RIGHT, padx=2)

        # 控制区
        frame_ctrl = tk.Frame(self.root)
        frame_ctrl.pack(fill=tk.X, padx=10, pady=5)
        self.start_btn = tk.Button(frame_ctrl, text="启动键盘监听", command=self.start_forward, bg="#008CBA", fg="white", width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(frame_ctrl, text="停止监听", command=self.stop_forward, bg="#f44336", fg="white", width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 最近发送记录
        frame_recent = tk.LabelFrame(self.root, text="最近发送记录（最多10条）", padx=5, pady=5)
        frame_recent.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        self.recent_listbox = tk.Listbox(frame_recent, height=10, font=("Courier", 10))
        self.recent_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 详细日志
        frame_log = tk.LabelFrame(self.root, text="详细日志", padx=5, pady=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(frame_log, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 提示
        tip = "提示：可自定义静默时间（1-30秒），发送自定义消息后期间不发送任何数据（包括空闲空字符）。"
        tk.Label(self.root, text=tip, fg="gray", font=("Arial", 9)).pack(side=tk.BOTTOM, pady=2)

    def _toggle_rate(self):
        self.rate_spin.config(state="normal" if self.rate_enabled.get() else "disabled")

    def apply_rate(self):
        enabled = self.rate_enabled.get()
        try:
            rate = int(self.rate_spin.get())
            if rate <= 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入1-1000的整数")
            return
        self.sender.set_rate_limit(enabled, rate)
        self.log(f"频率限制: {'启用' if enabled else '禁用'}, {rate}次/秒")

    def update_status(self, msg):
        self.root.after(0, lambda: self.status_label.config(text=msg))

    def log(self, msg):
        def _log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _log)

    def record_sent(self, content):
        display = content if content != "" else "<空行>"
        self.recent_sent.append(display)
        self._update_recent_listbox()

    def _update_recent_listbox(self):
        def _update():
            self.recent_listbox.delete(0, tk.END)
            for item in self.recent_sent:
                self.recent_listbox.insert(tk.END, item)
        self.root.after(0, _update)

    def do_connect(self):
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        if not ip or not port_str:
            messagebox.showerror("错误", "填写IP和端口")
            return
        try:
            port = int(port_str)
        except:
            messagebox.showerror("错误", "端口必须为整数")
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
            messagebox.showwarning("警告", "消息不能为空")
            return
        if not self.sender.running:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        # 获取用户选择的静默时间（默认3秒）
        try:
            silent_sec = self.silent_time_var.get()
            if silent_sec <= 0:
                silent_sec = 1
        except:
            silent_sec = 3
        # 发送自定义消息
        self.sender.send(msg)
        self.log(f"自定义发送: {msg} (之后静默 {silent_sec} 秒)")
        self.sender.set_silent_period(silent_sec)

    def start_forward(self):
        if not self.sender.running:
            messagebox.showwarning("警告", "请先连接服务器")
            return
        if self.forwarder.running:
            return
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

    def on_closing(self):
        self.stop_forward()
        self.sender.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    try:
        import pynput
    except ImportError:
        print("缺少依赖库 pynput，请执行: pip install pynput")
        sys.exit(1)

    root = tk.Tk()
    app = App(root)
    root.mainloop()