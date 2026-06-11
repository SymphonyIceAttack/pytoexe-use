# -*- coding: utf-8 -*-
"""
阶段跳转脚本 (Phase Jumper) —— 带 GUI

功能概述:
    维护一个"当前阶段"状态机:
        初始阶段 = 0
        正常循环顺序 = 1 -> 2 -> 3 -> 4 -> 1 -> 2 -> 3 -> 4 -> ...

    按下数字键 1-4 或点击 GUI 中对应按钮:
        把当前阶段跳转到目标阶段,
        跨越 N 个阶段 => 模拟点击 JUMP_KEY (N * CLICKS_PER_PHASE) 次。
        例: 当前 1 -> 目标 3, 跨越 2 阶段, 点击 u x 4 次。

依赖:
    pip install pynput
    (tkinter 是 Python 标准库, 无需额外安装)

运行:
    python phase_jumper.py

停止:
    按 ESC 键 或 关闭 GUI 窗口。
"""

import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pynput import keyboard
from pynput.keyboard import Controller, Key, KeyCode


# ============================================================
#  配置 (可在 GUI 中动态修改, 也可以直接改这里)
# ============================================================

class Config:
    initial_phase = 0
    cycle_phases = [1, 2, 3, 4]
    jump_key = 'u'
    clicks_per_phase = 2
    click_interval = 0.05
    hold_duration = 0.02
    use_shortest_path = False
    enabled = True
    trigger_keys = {'1': 1, '2': 2, '3': 3, '4': 4}
    phase_names = {1: '长', 2: '钝', 3: '爆', 4: '雷'}
    hotkey_toggle_enabled = Key.f2
    exit_key = Key.esc
    cooldown_after_jump = 0.1


# ============================================================
#  内部状态
# ============================================================

controller = Controller()
current_phase = Config.initial_phase
_last_jump_time = 0.0
_lock = threading.Lock()
_listener = None
_gui_update_callback = None
_gui_log_callback = None


# ============================================================
#  核心逻辑
# ============================================================

def _resolve_key(k):
    if isinstance(k, (Key, KeyCode)):
        return k
    if isinstance(k, str):
        if len(k) == 1:
            return KeyCode.from_char(k)
        aliases = {
            'space': Key.space, 'tab': Key.tab, 'enter': Key.enter,
            'esc': Key.esc, 'escape': Key.esc,
            'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            'shift': Key.shift, 'ctrl': Key.ctrl, 'alt': Key.alt,
        }
        if k.lower() in aliases:
            return aliases[k.lower()]
    raise ValueError(f"无法识别的 JUMP_KEY: {k!r}")


def _click_key():
    key = _resolve_key(Config.jump_key)
    controller.press(key)
    time.sleep(Config.hold_duration)
    controller.release(key)


def _phase_distance(from_phase, to_phase):
    if from_phase == to_phase:
        return 0
    if from_phase == Config.initial_phase:
        try:
            return Config.cycle_phases.index(to_phase) + 1
        except ValueError:
            return 1
    try:
        i = Config.cycle_phases.index(from_phase)
        j = Config.cycle_phases.index(to_phase)
    except ValueError:
        return 1
    n = len(Config.cycle_phases)
    forward = (j - i) % n
    if Config.use_shortest_path:
        backward = n - forward
        return min(forward, backward)
    return forward


def phase_name(phase):
    if phase == Config.initial_phase:
        return "初始"
    return Config.phase_names.get(phase, str(phase))


def log(msg):
    print(msg)
    if _gui_log_callback:
        try:
            _gui_log_callback(msg)
        except Exception:
            pass


def update_gui_phase():
    if _gui_update_callback:
        try:
            _gui_update_callback(current_phase)
        except Exception:
            pass


def perform_jump(target_phase):
    global current_phase, _last_jump_time

    with _lock:
        now = time.time()
        if now - _last_jump_time < Config.cooldown_after_jump:
            return
        _last_jump_time = now

        if not Config.enabled:
            log(f"[跳过] 功能已关闭, 不响应 ({phase_name(current_phase)} -> {phase_name(target_phase)})")
            return

        if current_phase == target_phase:
            log(f"[跳过] 已是 {phase_name(current_phase)}, 无需跳转")
            return

        steps = _phase_distance(current_phase, target_phase)
        total_clicks = steps * Config.clicks_per_phase

        log(f"[跳转] {phase_name(current_phase)} -> {phase_name(target_phase)}  "
            f"(跨越 {steps} 把刀, 点击 {Config.jump_key} x{total_clicks})")
        for _ in range(total_clicks):
            _click_key()
            time.sleep(Config.click_interval)

        current_phase = target_phase
        update_gui_phase()


def reset_phase():
    global current_phase
    with _lock:
        current_phase = Config.initial_phase
        log(f"[重置] 回到初始")
        update_gui_phase()


def set_phase_manually(phase):
    """强制设置阶段而不触发点击(用于同步/校准)。"""
    global current_phase
    with _lock:
        current_phase = phase
        log(f"[校准] 当前设为 {phase_name(phase)}")
        update_gui_phase()


# ============================================================
#  键盘监听
# ============================================================

def _on_press(key):

    # ESC：隐藏/显示窗口，不停止后台监听
    if key == Config.exit_key:
        if _gui_update_callback:
            try:
                gui = _gui_update_callback.__self__
                root = gui.root
                if root.state() == 'withdrawn':
                    root.deiconify()
                    root.lift()
                    log("[窗口] 已显示")
                else:
                    root.withdraw()
                    log("[窗口] 已隐藏 (按 ESC 可重新显示)")
            except Exception:
                pass
        return

    # 热键：切换总开关（F2 始终可用）
    if key == Config.hotkey_toggle_enabled:
        Config.enabled = not Config.enabled
        log(f"[热键] F2 功能 = {'开' if Config.enabled else '关'}")
        if _gui_update_callback:
            try:
                _gui_update_callback.__self__.enabled_var.set(Config.enabled)
            except Exception:
                pass
        # 如果窗口是隐藏的，切换时也顺带显示
        if _gui_update_callback:
            try:
                root = _gui_update_callback.__self__.root
                if root.state() == 'withdrawn':
                    root.deiconify()
                    root.lift()
            except Exception:
                pass
        return

    if not Config.enabled:
        return

    # 解析触发键 1-4
    target = None
    try:
        char = key.char
        if char in Config.trigger_keys:
            target = Config.trigger_keys[char]
    except AttributeError:
        pass

    if target is None and isinstance(key, KeyCode) and key.vk is not None:
        if 96 <= key.vk <= 105:
            s = str(key.vk - 96)
            if s in Config.trigger_keys:
                target = Config.trigger_keys[s]

    if target is not None:
        threading.Thread(target=perform_jump, args=(target,), daemon=True).start()


def start_listener():
    global _listener
    if _listener and _listener.running:
        return
    _listener = keyboard.Listener(on_press=_on_press)
    _listener.daemon = True
    _listener.start()
    log("[监听] 键盘监听已启动 (1-4 切换忍刀, F2 总开关, ESC 隐藏/显示窗口)")


def stop_listener():
    global _listener
    if _listener and _listener.running:
        _listener.stop()
        _listener = None
        log("[监听] 键盘监听已停止")


# ============================================================
#  GUI
# ============================================================

class PhaseJumperGUI:
    def __init__(self, root):
        self.root = root
        root.title("鬼灯满月")
        root.geometry("640x560")
        root.minsize(560, 520)

        self._build_style()
        self._build_ui()
        self._update_phase_display(current_phase)

        global _gui_update_callback, _gui_log_callback
        _gui_update_callback = self._thread_safe_update_phase
        _gui_log_callback = self._thread_safe_log

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        start_listener()

    # ---- style ----
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('BigPhase.TLabel', font=('Segoe UI', 42, 'bold'))
        style.configure('Phase.TButton', font=('Segoe UI', 14, 'bold'), padding=10)
        style.configure('Action.TButton', padding=6)
        style.configure('Title.TLabel', font=('Segoe UI', 11, 'bold'))

    # ---- layout ----
    def _build_ui(self):
        pad = {'padx': 8, 'pady': 6}

        main = ttk.Frame(self.root)
        main.pack(fill='both', expand=True, padx=10, pady=10)

        # --- Phase display ---
        frame_phase = ttk.LabelFrame(main, text=" 当前忍刀 ")
        frame_phase.pack(fill='x', **pad)

        self.phase_label = ttk.Label(frame_phase, text="初始",
                                     style='BigPhase.TLabel',
                                     anchor='center')
        self.phase_label.pack(fill='x', pady=10)

        cycle_text = "循环顺序: 长 → 钝 → 爆 → 雷"
        ttk.Label(frame_phase, text=cycle_text, anchor='center').pack(fill='x', pady=(0, 8))

        # --- Phase buttons ---
        frame_btns = ttk.LabelFrame(main, text=" 切换忍刀 (点击按钮或按键盘 1-4) ")
        frame_btns.pack(fill='x', **pad)

        btns_row = ttk.Frame(frame_btns)
        btns_row.pack(fill='x', padx=10, pady=10)
        btns_row.columnconfigure((0, 1, 2, 3), weight=1)

        self.phase_buttons = {}
        for idx, phase in enumerate(Config.cycle_phases):
            b = ttk.Button(btns_row, text=f"{Config.phase_names[phase]}",
                           style='Phase.TButton',
                           command=lambda p=phase: self._on_phase_btn(p))
            b.grid(row=0, column=idx, padx=5, sticky='nsew')
            self.phase_buttons[phase] = b

        # --- Action buttons ---
        frame_action = ttk.Frame(main)
        frame_action.pack(fill='x', **pad)

        ttk.Button(frame_action, text="重置阶段", style='Action.TButton',
                   command=self._on_reset).pack(side='left', padx=4)

        ttk.Label(frame_action, text="校准阶段:").pack(side='left', padx=(20, 4))
        self.calib_var = tk.StringVar(value=str(Config.initial_phase))
        calib_entry = ttk.Entry(frame_action, textvariable=self.calib_var, width=6)
        calib_entry.pack(side='left', padx=4)
        ttk.Button(frame_action, text="应用", style='Action.TButton',
                   command=self._on_calibrate).pack(side='left', padx=4)

        ttk.Separator(frame_action, orient='vertical').pack(side='left', fill='y', padx=10)
        self.enabled_var = tk.BooleanVar(value=Config.enabled)
        ttk.Checkbutton(frame_action, text="启用 (F2)", variable=self.enabled_var,
                        command=self._on_toggle_enabled).pack(side='left', padx=4)

        ttk.Separator(frame_action, orient='vertical').pack(side='left', fill='y', padx=10)
        ttk.Button(frame_action, text="退出程序", style='Action.TButton',
                   command=self._on_quit).pack(side='left', padx=4)

        # --- Config ---
        frame_cfg = ttk.LabelFrame(main, text=" 配置 (修改后立即生效) ")
        frame_cfg.pack(fill='x', **pad)

        cfg_grid = ttk.Frame(frame_cfg)
        cfg_grid.pack(fill='x', padx=8, pady=8)
        for c in (1, 3, 5):
            cfg_grid.columnconfigure(c, weight=1)

        self.var_jump_key = tk.StringVar(value=Config.jump_key)
        self.var_clicks = tk.IntVar(value=Config.clicks_per_phase)
        self.var_interval = tk.DoubleVar(value=Config.click_interval)
        self.var_hold = tk.DoubleVar(value=Config.hold_duration)
        self.var_shortest = tk.BooleanVar(value=Config.use_shortest_path)
        self.var_cooldown = tk.DoubleVar(value=Config.cooldown_after_jump)

        row = 0
        ttk.Label(cfg_grid, text="跳转键:").grid(row=row, column=0, sticky='e', padx=4, pady=3)
        ttk.Entry(cfg_grid, textvariable=self.var_jump_key, width=8).grid(row=row, column=1, sticky='w')
        ttk.Label(cfg_grid, text="(单字符如 u / a, 或 space / tab / enter)").grid(row=row, column=2, columnspan=4, sticky='w')

        row += 1
        ttk.Label(cfg_grid, text="每阶段点击:").grid(row=row, column=0, sticky='e', padx=4, pady=3)
        ttk.Spinbox(cfg_grid, from_=1, to=20, textvariable=self.var_clicks, width=6).grid(row=row, column=1, sticky='w')
        ttk.Label(cfg_grid, text="点击间隔(秒):").grid(row=row, column=2, sticky='e', padx=4)
        ttk.Entry(cfg_grid, textvariable=self.var_interval, width=8).grid(row=row, column=3, sticky='w')
        ttk.Label(cfg_grid, text="保持时间(秒):").grid(row=row, column=4, sticky='e', padx=4)
        ttk.Entry(cfg_grid, textvariable=self.var_hold, width=8).grid(row=row, column=5, sticky='w')

        row += 1
        ttk.Checkbutton(cfg_grid, text="使用最短路径(环形)",
                        variable=self.var_shortest).grid(row=row, column=0, columnspan=3, sticky='w', padx=4, pady=3)
        ttk.Label(cfg_grid, text="冷却(秒):").grid(row=row, column=3, sticky='e', padx=4)
        ttk.Entry(cfg_grid, textvariable=self.var_cooldown, width=8).grid(row=row, column=4, sticky='w')

        ttk.Button(cfg_grid, text="应用配置", command=self._on_apply_config).grid(row=row, column=5, padx=6)

        # --- Log ---
        frame_log = ttk.LabelFrame(main, text=" 日志 ")
        frame_log.pack(fill='both', expand=True, **pad)

        self.log_text = scrolledtext.ScrolledText(frame_log, height=8,
                                                   font=('Consolas', 9),
                                                   wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=6, pady=6)

    # ---- actions ----
    def _on_phase_btn(self, phase):
        self._apply_config_from_gui()
        threading.Thread(target=perform_jump, args=(phase,), daemon=True).start()

    def _on_reset(self):
        reset_phase()

    def _on_calibrate(self):
        try:
            p = int(self.calib_var.get())
        except ValueError:
            messagebox.showerror("错误", "校准阶段必须是整数")
            return
        set_phase_manually(p)

    def _on_toggle_enabled(self):
        Config.enabled = self.enabled_var.get()
        log(f"[开关] F2 功能 = {'开' if Config.enabled else '关'}")

    def _apply_config_from_gui(self):
        try:
            Config.jump_key = self.var_jump_key.get().strip() or 'u'
            Config.clicks_per_phase = int(self.var_clicks.get())
            Config.click_interval = float(self.var_interval.get())
            Config.hold_duration = float(self.var_hold.get())
            Config.use_shortest_path = self.var_shortest.get()
            Config.cooldown_after_jump = float(self.var_cooldown.get())
            Config.enabled = self.enabled_var.get()
        except Exception:
            pass

    def _on_apply_config(self):
        try:
            Config.jump_key = self.var_jump_key.get().strip() or 'u'
            Config.clicks_per_phase = int(self.var_clicks.get())
            Config.click_interval = float(self.var_interval.get())
            Config.hold_duration = float(self.var_hold.get())
            Config.use_shortest_path = self.var_shortest.get()
            Config.cooldown_after_jump = float(self.var_cooldown.get())
            Config.enabled = self.enabled_var.get()
            log(f"[配置] 已更新: jump_key={Config.jump_key}, "
                f"per_phase={Config.clicks_per_phase}, "
                f"interval={Config.click_interval}s, "
                f"enabled={'开' if Config.enabled else '关'}")
        except Exception as e:
            messagebox.showerror("配置错误", str(e))

    # ---- display updates (thread-safe) ----
    def _thread_safe_update_phase(self, phase):
        self.root.after(0, lambda: self._update_phase_display(phase))

    def _update_phase_display(self, phase):
        self.phase_label.config(text=phase_name(phase))
        for p, btn in self.phase_buttons.items():
            if p == phase:
                btn.state(['active'])
            else:
                btn.state(['!active'])

    def _thread_safe_log(self, msg):
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {msg}\n")
        self.log_text.see('end')

    def _on_close(self):
        """点窗口 X - 隐藏到后台而不是退出, 按 ESC 可恢复"""
        try:
            self.root.withdraw()
            log("[窗口] 已隐藏 (按 ESC 可重新显示)")
        except Exception:
            self._on_quit()

    def _on_quit(self):
        """真正退出程序"""
        try:
            stop_listener()
        except Exception:
            pass
        log("[退出] 程序已退出")
        self.root.destroy()


# ============================================================
#  Entry
# ============================================================

def main():
    root = tk.Tk()
    PhaseJumperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
