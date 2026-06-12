# motor_control_gui_v16_ui_refactor.py

import json
import os
import serial
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# -----------------------
# Constants / defaults
# -----------------------
SETTINGS_FILE = "settings.json"
DEFAULTS = {
    "com": "COM3",
    "baud": 38400,
    "slave": 1,
    "comm_timeout": 2.0,
    "cycle": 3,
    "movement": 1.5,       # Auto movement base time
    "interval": 0.2,
    "up_scale": 0.95,
    "manual_mode": "jog",  # Default modified to jog as requested
    "manual_time": 5.0     # Separate Manual timed duration
}

# -----------------------
# Modbus helpers (UNTOUCHED)
# -----------------------
def modbus_crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def build_write_multiple_coils_frame(slave_addr: int, start_channel: int, quantity: int, data_bytes: bytes) -> bytes:
    frame = bytearray()
    frame.append(slave_addr & 0xFF)
    frame.append(0x0F)
    start_addr = (start_channel - 1) & 0xFFFF
    frame += start_addr.to_bytes(2, byteorder='big')
    frame += (quantity & 0xFFFF).to_bytes(2, byteorder='big')
    frame.append(len(data_bytes))
    frame += data_bytes
    frame += modbus_crc16(bytes(frame))
    return bytes(frame)

def build_write_single_register_frame(slave_addr: int, register_addr: int, value: int) -> bytes:
    frame = bytearray()
    frame.append(slave_addr & 0xFF)
    frame.append(0x06)
    frame += (register_addr & 0xFFFF).to_bytes(2, byteorder='big')
    frame += (value & 0xFFFF).to_bytes(2, byteorder='big')
    frame += modbus_crc16(bytes(frame))
    return bytes(frame)

def build_read_holding_registers_frame(slave_addr: int, register_addr: int, count: int) -> bytes:
    frame = bytearray()
    frame.append(slave_addr & 0xFF)
    frame.append(0x03)
    frame += (register_addr & 0xFFFF).to_bytes(2, byteorder='big')
    frame += (count & 0xFFFF).to_bytes(2, byteorder='big')
    frame += modbus_crc16(bytes(frame))
    return bytes(frame)

def states_to_bytes(states: dict, start_channel: int, quantity: int) -> bytes:
    byte_count = (quantity + 7) // 8
    arr = [0] * byte_count
    for ch, val in states.items():
        if ch < start_channel or ch >= start_channel + quantity:
            continue
        bit_index = ch - start_channel
        byte_index = bit_index // 8
        bit_pos = bit_index % 8
        if val:
            arr[byte_index] |= (1 << bit_pos)
        else:
            arr[byte_index] &= ~(1 << bit_pos)
    return bytes(arr)

def describe_changes(prev: dict, new: dict):
    turned_on = []
    turned_off = []
    for ch in sorted(set(prev.keys()) | set(new.keys())):
        pv = bool(prev.get(ch, False))
        nv = bool(new.get(ch, False))
        if pv != nv:
            if nv:
                turned_on.append(ch)
            else:
                turned_off.append(ch)
    return turned_on, turned_off

# -----------------------
# Motor mapping (UNTOUCHED)
# -----------------------
# 7 and 8 are reserved for Contactors
MOTOR_CHANNELS = {
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [9, 10, 11],
    'D': [12, 13, 14],
}
DEFAULT_START_CHANNEL = 1
DEFAULT_QUANTITY = 16

def motor_up_states(motor):
    ch = MOTOR_CHANNELS[motor]
    return {ch[0]: True, ch[1]: True, ch[2]: False}

def motor_down_states(motor):
    ch = MOTOR_CHANNELS[motor]
    return {ch[0]: False, ch[1]: True, ch[2]: True}

def motor_stop_states(motor):
    ch = MOTOR_CHANNELS[motor]
    return {ch[0]: False, ch[1]: False, ch[2]: False}

# -----------------------
# Serial wrapper (UNTOUCHED)
# -----------------------
class ModbusSerial:
    def __init__(self, port, baudrate, timeout=0.2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.lock = threading.Lock()

    def open(self):
        if self.ser and getattr(self.ser, "is_open", False):
            return
        self.ser = serial.Serial(self.port, self.baudrate, bytesize=8, parity='N', stopbits=1, timeout=self.timeout)

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    def send_frame(self, frame: bytes):
        with self.lock:
            if not self.ser or not getattr(self.ser, "is_open", False):
                self.open()
            self.ser.write(frame)
            time.sleep(0.02)
            resp = b""
            try:
                resp = self.ser.read(self.ser.in_waiting or 1)
            except Exception:
                pass
            return resp

# -----------------------
# Settings persistence (UNTOUCHED)
# -----------------------
def load_settings():
    cfg = DEFAULTS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in cfg:
                if k in data:
                    cfg[k] = data[k]
        except Exception:
            pass
    return cfg

def save_settings(cfg):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# -----------------------
# GUI application
# -----------------------
class MotorControlApp:
    def __init__(self, root):
        self.root = root
        root.title("Relay Controller - Unified V16")
        self.settings = load_settings()

        #Add threading lock (UNTOUCHED from 48514.py)
        self.serial_lock = threading.Lock()

        # State tracking
        self.mb = None
        self.current_states = {i: False for i in range(1, 17)}
        self.last_comm_time = time.time()
        
        # Threading events
        self.x_thread = None
        self.x_stop = threading.Event()
        self.y_thread = None
        self.y_stop = threading.Event()

        # Timed mode active tracking
        self.active_timers = {} # motor -> bool
        
        # [NEW] Checkbox variables for motor selection
        self.motor_select_vars = {
            'A': tk.BooleanVar(value=False),
            'B': tk.BooleanVar(value=False),
            'C': tk.BooleanVar(value=False),
            'D': tk.BooleanVar(value=False)
        }
        # [NEW] UI State for Timed Mode Locking
        self.manual_timed_running = False

        self._init_gui()
        
        # Apply initial bindings
        self.update_manual_bindings()

        # Start keepalive
        self.root.after(200, self._keepalive_check)

    def _init_gui(self):
        # 1. Comm Settings (UNTOUCHED)
        comm_frame = ttk.LabelFrame(self.root, text="Comm Settings")
        comm_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=6)

        ttk.Label(comm_frame, text="COM:").grid(row=0, column=0)
        self.com_var = tk.StringVar(value=self.settings.get("com", DEFAULTS["com"]))
        self.com_entry = ttk.Entry(comm_frame, textvariable=self.com_var, width=8)
        self.com_entry.grid(row=0, column=1)

        ttk.Label(comm_frame, text="Baud:").grid(row=0, column=2)
        self.baud_var = tk.IntVar(value=self.settings.get("baud", DEFAULTS["baud"]))
        self.baud_entry = ttk.Entry(comm_frame, textvariable=self.baud_var, width=7)
        self.baud_entry.grid(row=0, column=3)

        ttk.Label(comm_frame, text="ID:").grid(row=0, column=4)
        self.slave_var = tk.IntVar(value=self.settings.get("slave", DEFAULTS["slave"]))
        self.slave_entry = ttk.Entry(comm_frame, textvariable=self.slave_var, width=4)
        self.slave_entry.grid(row=0, column=5)

        ttk.Label(comm_frame, text="T/O(s):").grid(row=0, column=6)
        self.comm_timeout_var = tk.DoubleVar(value=self.settings.get("comm_timeout", DEFAULTS["comm_timeout"]))
        self.comm_timeout_entry = ttk.Entry(comm_frame, textvariable=self.comm_timeout_var, width=5)
        self.comm_timeout_entry.grid(row=0, column=7)

        ttk.Label(comm_frame, text="UpScale:").grid(row=0, column=8)
        self.up_scale_var = tk.DoubleVar(value=self.settings.get("up_scale", DEFAULTS["up_scale"]))
        self.up_scale_entry = ttk.Entry(comm_frame, textvariable=self.up_scale_var, width=5)
        self.up_scale_entry.grid(row=0, column=9)

        self.open_btn = ttk.Button(comm_frame, text="Open", command=self.open_serial, width=6)
        self.open_btn.grid(row=0, column=10, padx=2)
        self.close_btn = ttk.Button(comm_frame, text="Close", command=self.close_serial, width=6)
        self.close_btn.grid(row=0, column=11, padx=2)

        # -------------------------------------------------------------
        # [MODIFIED] 2. Unified Manual Control Frame
        # -------------------------------------------------------------
        manual_frame = ttk.LabelFrame(self.root, text="Unified Manual Control")
        manual_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        
        # --- A. Motor Selection (Checkboxes) ---
        sel_frame = ttk.Frame(manual_frame)
        sel_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(sel_frame, text="Select Motors:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Checkboxes for A, B, C, D
        self.chk_a = ttk.Checkbutton(sel_frame, text="Motor A", variable=self.motor_select_vars['A'])
        self.chk_a.pack(side=tk.LEFT, padx=10)
        self.chk_b = ttk.Checkbutton(sel_frame, text="Motor B", variable=self.motor_select_vars['B'])
        self.chk_b.pack(side=tk.LEFT, padx=10)
        self.chk_c = ttk.Checkbutton(sel_frame, text="Motor C", variable=self.motor_select_vars['C'])
        self.chk_c.pack(side=tk.LEFT, padx=10)
        self.chk_d = ttk.Checkbutton(sel_frame, text="Motor D", variable=self.motor_select_vars['D'])
        self.chk_d.pack(side=tk.LEFT, padx=10)

        # --- B. Mode Selection & Time ---
        mode_frame = ttk.Frame(manual_frame)
        mode_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(mode_frame, text="Mode:").pack(side=tk.LEFT, padx=5)
        self.manual_mode_var = tk.StringVar(value=self.settings.get("manual_mode", "jog"))
        
        # Only Jog and Timed
        self.rb_jog = ttk.Radiobutton(mode_frame, text="Jog (Hold to Run)", variable=self.manual_mode_var, value="jog", command=self.update_manual_bindings)
        self.rb_jog.pack(side=tk.LEFT, padx=10)
        self.rb_timed = ttk.Radiobutton(mode_frame, text="Timed (Click)", variable=self.manual_mode_var, value="timed", command=self.update_manual_bindings)
        self.rb_timed.pack(side=tk.LEFT, padx=10)

        # Time Entry
        ttk.Label(mode_frame, text="Time(s):").pack(side=tk.LEFT, padx=(20, 5))
        self.manual_time_var = tk.DoubleVar(value=self.settings.get("manual_time", 5.0))
        self.manual_time_entry = ttk.Entry(mode_frame, textvariable=self.manual_time_var, width=6)
        self.manual_time_entry.pack(side=tk.LEFT)
        
        # --- C. Big Control Buttons ---
        btn_frame = ttk.Frame(manual_frame)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        # Using larger fonts for easier touch/click
        self.man_up_btn = ttk.Button(btn_frame, text="UP (▲)")
        self.man_up_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5, ipady=10)
        
        self.man_stop_btn = ttk.Button(btn_frame, text="STOP (■)", command=self.manual_stop_all)
        self.man_stop_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5, ipady=10)
        
        self.man_down_btn = ttk.Button(btn_frame, text="DOWN (▼)")
        self.man_down_btn.pack(side=tk.LEFT, expand=True, fill="x", padx=5, ipady=10)

        # Countdown Label (Shared)
        self.lbl_countdown = ttk.Label(manual_frame, text=" ", foreground="red", font=("Consolas", 12, "bold"))
        self.lbl_countdown.pack(pady=2)

        # [REMOVED] Old Group Controls (Row 2 in original) because they are now merged into Manual.
        # [REMOVED] Old "Motor Buttons" loop.

        # 4. Automatic Control (Row 3 -> Row 2) (UNTOUCHED LOGIC)
        auto_frame = ttk.LabelFrame(self.root, text="Automatic Control")
        auto_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=6)
        
        f_params = ttk.Frame(auto_frame)
        f_params.pack(fill="x", pady=2)
        
        ttk.Label(f_params, text="Cycles:").pack(side=tk.LEFT, padx=2)
        self.cycle_var = tk.IntVar(value=self.settings.get("cycle", DEFAULTS["cycle"]))
        self.cycle_entry = ttk.Entry(f_params, textvariable=self.cycle_var, width=5)
        self.cycle_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(f_params, text="Auto Move(s):").pack(side=tk.LEFT, padx=(10, 2))
        self.move_var = tk.DoubleVar(value=self.settings.get("movement", DEFAULTS["movement"]))
        self.move_entry = ttk.Entry(f_params, textvariable=self.move_var, width=5)
        self.move_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(f_params, text="Interval(s):").pack(side=tk.LEFT, padx=(10, 2))
        self.interval_var = tk.DoubleVar(value=self.settings.get("interval", DEFAULTS["interval"]))
        self.interval_entry = ttk.Entry(f_params, textvariable=self.interval_var, width=5)
        self.interval_entry.pack(side=tk.LEFT, padx=2)

        f_btns = ttk.Frame(auto_frame)
        f_btns.pack(fill="x", pady=4)
        self.start_x_btn = ttk.Button(f_btns, text="Start X (C-D)", command=self.start_x_axis)
        self.stop_x_btn = ttk.Button(f_btns, text="Stop X", command=self.stop_x_axis)
        self.start_y_btn = ttk.Button(f_btns, text="Start Y (B-C)", command=self.start_y_axis)
        self.stop_y_btn = ttk.Button(f_btns, text="Stop Y", command=self.stop_y_axis)

        self.start_x_btn.pack(side=tk.LEFT, padx=5, expand=True)
        self.stop_x_btn.pack(side=tk.LEFT, padx=5, expand=True)
        self.start_y_btn.pack(side=tk.LEFT, padx=5, expand=True)
        self.stop_y_btn.pack(side=tk.LEFT, padx=5, expand=True)

        # 5. Log (Row 4 -> Row 3)
        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=6)
        self.root.grid_rowconfigure(3, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.log = scrolledtext.ScrolledText(log_frame, height=10)
        self.log.pack(fill="both", expand=True)

        # Group controls for locking
        self.controls_to_disable = [
            self.com_entry, self.baud_entry, self.slave_entry, 
            self.open_btn, self.close_btn,
            self.start_x_btn, self.start_y_btn,
            self.chk_a, self.chk_b, self.chk_c, self.chk_d,
            self.rb_jog, self.rb_timed, self.manual_time_entry,
            self.man_up_btn, self.man_down_btn 
        ]

    # -----------------------------------------------------------
    # [NEW] Unified Manual Control Logic
    # -----------------------------------------------------------
    def update_manual_bindings(self):
        """Rebind the main UP/DOWN buttons based on mode."""
        mode = self.manual_mode_var.get()
        
        # Clear old bindings
        self.man_up_btn.unbind('<Button-1>')
        self.man_up_btn.unbind('<ButtonRelease-1>')
        self.man_down_btn.unbind('<Button-1>')
        self.man_down_btn.unbind('<ButtonRelease-1>')
        self.man_up_btn.configure(command=lambda: None)
        self.man_down_btn.configure(command=lambda: None)

        if mode == "timed":
            self.manual_time_entry.configure(state='normal')
            # Timed: Click to start
            self.man_up_btn.configure(command=lambda: self.start_manual_timed('up'))
            self.man_down_btn.configure(command=lambda: self.start_manual_timed('down'))
        else:
            self.manual_time_entry.configure(state='disabled')
            # Jog: Press to start, Release to stop
            self.man_up_btn.bind('<Button-1>', lambda e: self.start_jog('up'))
            self.man_up_btn.bind('<ButtonRelease-1>', lambda e: self.stop_jog())
            self.man_down_btn.bind('<Button-1>', lambda e: self.start_jog('down'))
            self.man_down_btn.bind('<ButtonRelease-1>', lambda e: self.stop_jog())

    def get_selected_motors(self):
        """Return list of currently selected motors ['A', 'C']"""
        selected = []
        for m, var in self.motor_select_vars.items():
            if var.get():
                selected.append(m)
        return selected

    def manual_stop_all(self):
        """Universal Stop Button: Stops everything (Manual & Auto)"""
        # 1. Stop Auto if running
        if self._is_auto_running():
            self.stop_x_axis() # Signals stop
            self.stop_y_axis()
        
        # 2. Cancel Manual Timer if running
        self.manual_timed_running = False
        
        # 3. Send Stop to ALL motors (Safe stop)
        self.all_stop()
        
        # 4. Reset UI
        self._reset_manual_ui()
        self._unlock_controls()

    def start_jog(self, direction):
        """Jog: Run selected motors while holding"""
        if self._is_auto_running() or self.manual_timed_running: return
        
        targets = self.get_selected_motors()
        if not targets:
            self.log_write("No motors selected!")
            return
            
        self._send_multi_motor_action(targets, direction)

    def stop_jog(self):
        """Jog: Stop selected motors on release"""
        if self._is_auto_running() or self.manual_timed_running: return
        
        targets = self.get_selected_motors()
        if targets:
            self._send_multi_motor_action(targets, 'stop')

    def start_manual_timed(self, direction):
        """Timed: Run selected motors for X seconds, then stop"""
        if self._is_auto_running():
            self.log_write("Blocked: Auto running")
            return
        if self.manual_timed_running:
            return 

        targets = self.get_selected_motors()
        if not targets:
            self.log_write("No motors selected!")
            return

        try:
            duration = self.manual_time_var.get()
            if duration <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Invalid manual time")
            return

        # Start Motion
        self._send_multi_motor_action(targets, direction)
        
        # Lock UI
        self.manual_timed_running = True
        self._lock_controls()
        
        # Start Countdown
        end_time = time.time() + duration
        self._manual_timed_countdown(end_time, targets)

    def _manual_timed_countdown(self, end_time, targets):
        # Check if cancelled (e.g. by STOP button)
        if not self.manual_timed_running:
            self._reset_manual_ui()
            return

        remaining = end_time - time.time()
        
        if remaining <= 0:
            # Time over
            self._send_multi_motor_action(targets, 'stop')
            self.manual_timed_running = False
            self._reset_manual_ui()
            self._unlock_controls() # Re-enable UI
        else:
            self.lbl_countdown.configure(text=f"Running: {remaining:.1f}s")
            self.root.after(100, lambda: self._manual_timed_countdown(end_time, targets))

    def _reset_manual_ui(self):
        self.lbl_countdown.configure(text=" ")

    def _send_multi_motor_action(self, motors, direction):
        """Helper to build map for multiple motors and send"""
        mapping = {}
        for m in motors:
            if direction == 'up':
                mapping.update(motor_up_states(m))
            elif direction == 'down':
                mapping.update(motor_down_states(m))
            else:
                mapping.update(motor_stop_states(m))
        self.send_states_region(mapping)

    # -----------------------
    # Serial Operations (UNTOUCHED)
    # -----------------------
    def open_serial(self):
        port = self.com_var.get().strip()
        try:
            baud = int(self.baud_var.get())
        except:
            return
        try:
            if self.mb: self.mb.close()
            self.mb = ModbusSerial(port, baud)
            self.mb.open()
            self.log_write(f"Opened serial {port}")
            self.write_comm_timeout_register()
            self.last_comm_time = time.time()
            # Turn ON Contactors (7 & 8)
            self.set_contactors(True)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def close_serial(self):
        try:
            # Turn OFF Contactors (7 & 8)
            if self.mb:
                self.set_contactors(False)
                self.mb.close()
                self.mb = None
            self.log_write("Closed serial")
        except Exception as e:
            self.log_write(f"Close error: {e}")
            

    def set_contactors(self, state: bool):
        """ Control Relays 7 and 8 specifically """
        if not self.mb: return
        mapping = {7: state, 8: state}
        self.send_states_region(mapping)
        self.log_write(f"Contactors (7,8) -> {'ON' if state else 'OFF'}")

    def write_comm_timeout_register(self):
        if not self.mb: return
        try:
            val = float(self.comm_timeout_var.get())
            N = int(round(val * 10))
            frame = build_write_single_register_frame(self.slave_var.get(), 0x0030, N)
            self.mb.send_frame(frame)
        except:
            pass

    def _keepalive_check(self):
        try:
            if self.mb and getattr(self.mb.ser, "is_open", False):
                t_out = float(self.comm_timeout_var.get())
                if (time.time() - self.last_comm_time) > (t_out / 2.0):
                    frame = build_read_holding_registers_frame(self.slave_var.get(), 0x0000, 1)
                    self.mb.send_frame(frame)
                    self.last_comm_time = time.time()
        except:
            pass
        self.root.after(200, self._keepalive_check)

    # -----------------------
    # Core Control (UNTOUCHED)
    # -----------------------
    def send_states_region(self, desired_states: dict):
        if not self.mb or not getattr(self.mb.ser, "is_open", False):
            self.log_write("Ignored: Serial not connected")
            return

        prev_states = dict(self.current_states)
        merged = dict(prev_states)
        merged.update(desired_states)

        start_ch = DEFAULT_START_CHANNEL
        qty = DEFAULT_QUANTITY
        data = states_to_bytes(merged, start_ch, qty)
        frame = build_write_multiple_coils_frame(self.slave_var.get(), start_ch, qty, data)
        
        turned_on, turned_off = describe_changes(prev_states, merged)
        if turned_on or turned_off:
            on_s = ",".join(str(x) for x in turned_on) if turned_on else "-"
            off_s = ",".join(str(x) for x in turned_off) if turned_off else "-"
            self.log_write(f"Set -> ON:[{on_s}] OFF:[{off_s}]")

        with self.serial_lock:
            try:
                self.mb.send_frame(frame)
                self.current_states.update(merged)
                self.last_comm_time = time.time()
            except Exception as e:
                self.log_write(f"Send Error: {e}")

    def motor_action(self, motor, action):
        if self._is_auto_running(): return
        
        if action == 'up': st = motor_up_states(motor)
        elif action == 'down': st = motor_down_states(motor)
        elif action == 'stop': st = motor_stop_states(motor)
        else: return
        
        mapping = {k: bool(v) for k, v in st.items()}
        self.send_states_region(mapping)

    def all_up(self):
        if self._is_auto_running(): return
        mapping = {}
        for m in MOTOR_CHANNELS: mapping.update(motor_up_states(m))
        self.send_states_region(mapping)

    def all_down(self):
        if self._is_auto_running(): return
        mapping = {}
        for m in MOTOR_CHANNELS: mapping.update(motor_down_states(m))
        self.send_states_region(mapping)

    def all_stop(self):
        # Stop all motors (keep 7/8 intact)
        # Cancel any manual timers
        for m in self.active_timers: self.active_timers[m] = False
        
        mapping = {}
        for m in MOTOR_CHANNELS: mapping.update(motor_stop_states(m))
        self.send_states_region(mapping)

    # -----------------------
    # Auto Routines (UNTOUCHED LOGIC)
    # -----------------------
    def start_x_axis(self):
        self._start_auto_thread('X')
    def stop_x_axis(self):
        self.x_stop.set()
    def start_y_axis(self):
        self._start_auto_thread('Y')
    def stop_y_axis(self):
        self.y_stop.set()

    def _start_auto_thread(self, axis):
        try:
            N = self.cycle_var.get()
            mv = self.move_var.get() # Auto Movement Time
            iv = self.interval_var.get()
            sc = self.up_scale_var.get()
        except:
            return
        
        self.all_stop()
        self._lock_controls()
        
        if axis == 'X':
            if self.x_thread and self.x_thread.is_alive(): return
            self.x_stop.clear()
            self.x_thread = threading.Thread(target=self._x_axis_worker, args=(N, mv, iv, sc), daemon=True)
            self.x_thread.start()
        else:
            if self.y_thread and self.y_thread.is_alive(): return
            self.y_stop.clear()
            self.y_thread = threading.Thread(target=self._y_axis_worker, args=(N, mv, iv, sc), daemon=True)
            self.y_thread.start()

    def _x_axis_worker(self, N, move_time, interval_time, up_scale):
        # Auto Logic uses up_scale
        self._generic_axis_worker('X', ['C','D'], N, move_time, interval_time, up_scale, self.x_stop)

    def _y_axis_worker(self, N, move_time, interval_time, up_scale):
        # Auto Logic uses up_scale
        self._generic_axis_worker('Y', ['B','C'], N, move_time, interval_time, up_scale, self.y_stop)

    def _generic_axis_worker(self, name, motors, N, move_t, int_t, up_scale, stop_evt):
        try:
            # Apply up_scale for Auto Mode only
            up_t = move_t * up_scale
            down_t = move_t
            
            others = [m for m in MOTOR_CHANNELS if m not in motors]
            
            def set_state(direction):
                mp = {}
                for o in others: mp.update(motor_stop_states(o))
                for m in motors:
                    if direction == 'up': mp.update(motor_up_states(m))
                    elif direction == 'down': mp.update(motor_down_states(m))
                    else: mp.update(motor_stop_states(m))
                self.send_states_region(mp)

            self.log_write(f"Auto {name} Start: {N} cyc, Up={up_t:.2f}s, Dn={down_t:.2f}s")
            
            # 1. First Half UP
            if stop_evt.is_set(): return
            set_state('up')
            self._sleep_interruptible(up_t / 2.0, stop_evt)
            if int_t > 0:
                set_state('stop')
                self._sleep_interruptible(int_t, stop_evt)

            # 2. Loop
            for cycle in range(1, N + 1):
                if stop_evt.is_set(): break
                
                # Phase DOWN (Full)
                set_state('down')
                self._sleep_interruptible(down_t, stop_evt)
                if int_t > 0:
                    set_state('stop')
                    self._sleep_interruptible(int_t, stop_evt)

                if stop_evt.is_set(): break

                if cycle < N:
                    # Phase UP (Full)
                    set_state('up')
                    self._sleep_interruptible(up_t, stop_evt)
                    if int_t > 0:
                        set_state('stop')
                        self._sleep_interruptible(int_t, stop_evt)
                else:
                #Final Half UP (Return to zero)
                    set_state('up')
                    self._sleep_interruptible(up_t / 2.0, stop_evt)
            
            set_state('stop')
            self.log_write(f"Auto {name} Done")
            
        except Exception as e:
            self.log_write(f"Auto {name} Error: {e}")

        finally:
            self._finish_auto_cleanup(motors)
            self.root.after(0, self._unlock_controls)
        if name == 'X':
                self.x_stop.clear()
        else:
                self.y_stop.clear()

    def _sleep_interruptible(self, duration, evt):
        if duration <= 0: return
        end = time.time() + duration
        while time.time() < end:
            if evt.is_set(): return
            time.sleep(0.05)

    def _finish_auto_cleanup(self, motors):
        mp = {}
        for m in motors: mp.update(motor_stop_states(m))
        self.send_states_region(mp)

    def _is_auto_running(self):
        return (self.x_thread and self.x_thread.is_alive()) or \
               (self.y_thread and self.y_thread.is_alive())

    def _lock_controls(self):
        for w in self.controls_to_disable:
            try: w.configure(state='disabled')
            except: pass
        # Replaced old widget loop with specific widget list

    def _unlock_controls(self):
        for w in self.controls_to_disable:
            try: w.configure(state='normal')
            except: pass
        self.update_manual_bindings()

    def log_write(self, text):
        ts = time.strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{ts}] {text}\n")
        if int(self.log.index('end-1c').split('.')[0]) > 500:
            self.log.delete('1.0', '2.0')
        self.log.see(tk.END)

    def save_current_settings(self):
        cfg = {
            "com": self.com_var.get(),
            "baud": self.baud_var.get(),
            "slave": self.slave_var.get(),
            "comm_timeout": self.comm_timeout_var.get(),
            "cycle": self.cycle_var.get(),
            "movement": self.move_var.get(),
            "interval": self.interval_var.get(),
            "up_scale": self.up_scale_var.get(),
            "manual_mode": self.manual_mode_var.get(),
            "manual_time": self.manual_time_var.get()
        }
        save_settings(cfg)

    def on_close_request(self):
        if messagebox.askyesno("Exit", "Confirm exit? Relays will stop."):
            self.x_stop.set()
            self.y_stop.set()
            self.all_stop()
            self.set_contactors(False) 
            self.save_current_settings()
            if self.mb: self.mb.close()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = MotorControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close_request)
    root.geometry("1000x700")
    root.mainloop()

if __name__ == "__main__":
    main()