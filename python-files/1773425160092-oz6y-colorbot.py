"""
ColorBot — Real Screen Pixel Trigger Bot
Reads actual screen pixels at cursor center, fires real keypresses system-wide.
Works in any app, game, or window.

Build to .exe:
    pip install mss pynput Pillow pyinstaller
    pyinstaller --onefile --noconsole --name ColorBot colorbot.py
"""

import tkinter as tk
from tkinter import ttk, colorchooser
import threading
import time
import math
import mss
import mss.tools
from PIL import Image, ImageDraw
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
import ctypes
import sys
import os

# ── Hi-DPI awareness (Windows) ─────────────────────────────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

keyboard_ctrl = KeyboardController()
mouse_ctrl = MouseController()

# ── Color math ──────────────────────────────────────────────────────────────
def hex_to_rgb(hex_color: str):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def color_distance(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def rgb_to_hex(r, g, b):
    return f'#{r:02X}{g:02X}{b:02X}'

# ── Special key map ─────────────────────────────────────────────────────────
SPECIAL_KEYS = {
    'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
    'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
    'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
    'shift': Key.shift, 'ctrl': Key.ctrl, 'alt': Key.alt,
    'space': Key.space, 'enter': Key.enter, 'tab': Key.tab,
    'caps_lock': Key.caps_lock, 'esc': Key.esc,
    'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
    'insert': Key.insert, 'delete': Key.delete,
    'home': Key.home, 'end': Key.end, 'page_up': Key.page_up, 'page_down': Key.page_down,
}

MOUSE_BUTTON_MAP = {
    'lmb': Button.left,
    'rmb': Button.right,
    'mmb': Button.middle,
    'mb4': Button.x1,
    'mb5': Button.x2,
}

# ── Main App ─────────────────────────────────────────────────────────────────
class ColorBot:
    DARK_BG     = '#0d0f12'
    PANEL       = '#13161b'
    PANEL2      = '#191d24'
    BORDER      = '#1f2530'
    ACCENT      = '#00e5ff'
    ACCENT2     = '#ff3c6e'
    GREEN       = '#00ff88'
    AMBER       = '#ffb800'
    TEXT        = '#e8ecf0'
    MUTED       = '#5a6478'
    FONT_MONO   = ('Consolas', 10)
    FONT_MONO_L = ('Consolas', 13, 'bold')
    FONT_MONO_S = ('Consolas', 8)

    PRESETS = [
        '#FF0000','#FF6600','#FFFF00','#00FF00',
        '#00FFFF','#0088FF','#AA00FF','#FF00AA',
        '#FFFFFF','#FF3C6E',
    ]

    def __init__(self, root):
        self.root = root
        self.root.title('ColorBot')
        self.root.configure(bg=self.DARK_BG)
        self.root.resizable(False, False)
        self.root.geometry('480x720')

        # State
        self.active         = False
        self.target_color   = (255, 0, 0)
        self.tolerance      = 15
        self.bound_key      = 'f'
        self.bound_key_disp = 'F'
        self.bound_type     = 'key'   # 'key' or 'mouse'
        self.is_listening   = False
        self.trigger_count  = 0
        self.cps_buffer     = 0
        self.last_cps_time  = time.time()
        self.scan_thread    = None
        self.scan_active    = False
        self.last_trigger   = 0
        self.cooldown_ms    = 100   # ms between triggers

        # Keybind listeners
        self._kb_listener   = None
        self._ms_listener   = None

        self._build_ui()
        self._start_cps_updater()

    # ── UI BUILD ────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = {'padx': 10, 'pady': 0}

        # Header
        hdr = tk.Frame(self.root, bg=self.DARK_BG)
        hdr.pack(fill='x', padx=14, pady=(14, 0))

        logo = tk.Label(hdr, text='CB', bg='#00b8cc', fg='#000000',
                        font=('Consolas', 12, 'bold'), width=3, relief='flat')
        logo.pack(side='left')

        tk.Label(hdr, text='  ColorBot', bg=self.DARK_BG, fg=self.TEXT,
                 font=('Consolas', 14, 'bold')).pack(side='left')
        tk.Label(hdr, text='  PIXEL TRIGGER SYSTEM', bg=self.DARK_BG, fg=self.MUTED,
                 font=self.FONT_MONO_S).pack(side='left', pady=(4,0))

        self.status_label = tk.Label(hdr, text='● INACTIVE', bg=self.DARK_BG,
                                     fg=self.MUTED, font=self.FONT_MONO)
        self.status_label.pack(side='right')

        self._sep()

        # Stats bar
        stats_frame = tk.Frame(self.root, bg=self.DARK_BG)
        stats_frame.pack(fill='x', padx=14, pady=(6, 0))
        for col in range(3):
            stats_frame.columnconfigure(col, weight=1)

        self.stat_triggers = self._stat_box(stats_frame, 'TRIGGERS', '0', self.GREEN, 0)
        self.stat_cps      = self._stat_box(stats_frame, 'CHECKS/S', '0', self.ACCENT, 1)
        self.stat_key      = self._stat_box(stats_frame, 'BOUND KEY', 'F', self.AMBER, 2)

        self._sep()

        # Color card
        self._card_label('◈  TARGET COLOR')
        color_frame = tk.Frame(self.root, bg=self.PANEL, bd=0)
        color_frame.pack(fill='x', padx=14, pady=(0, 2))

        row = tk.Frame(color_frame, bg=self.PANEL)
        row.pack(fill='x', padx=10, pady=10)

        self.color_btn = tk.Button(row, text='   ', bg='#FF0000', relief='flat',
                                   width=4, height=2, cursor='hand2',
                                   command=self._pick_color, bd=0,
                                   highlightbackground=self.BORDER, highlightthickness=1)
        self.color_btn.pack(side='left', padx=(0, 10))

        info = tk.Frame(row, bg=self.PANEL)
        info.pack(side='left', fill='x', expand=True)
        self.hex_label = tk.Label(info, text='#FF0000', bg=self.PANEL, fg=self.TEXT,
                                  font=('Consolas', 18, 'bold'), anchor='w')
        self.hex_label.pack(fill='x')
        self.rgb_label = tk.Label(info, text='rgb(255, 0, 0)', bg=self.PANEL,
                                  fg=self.MUTED, font=self.FONT_MONO_S, anchor='w')
        self.rgb_label.pack(fill='x')

        # Tolerance slider
        tol_row = tk.Frame(color_frame, bg=self.PANEL)
        tol_row.pack(fill='x', padx=10, pady=(0, 6))
        tk.Label(tol_row, text='TOLERANCE', bg=self.PANEL, fg=self.MUTED,
                 font=self.FONT_MONO_S).pack(side='left')
        self.tol_val_label = tk.Label(tol_row, text='15', bg=self.PANEL,
                                      fg=self.ACCENT, font=self.FONT_MONO, width=3)
        self.tol_val_label.pack(side='right')
        self.tol_slider = ttk.Scale(tol_row, from_=0, to=80, orient='horizontal',
                                    command=self._on_tolerance)
        self.tol_slider.set(15)
        self.tol_slider.pack(side='left', fill='x', expand=True, padx=8)

        # Cooldown slider
        cd_row = tk.Frame(color_frame, bg=self.PANEL)
        cd_row.pack(fill='x', padx=10, pady=(0, 8))
        tk.Label(cd_row, text='COOLDOWN MS', bg=self.PANEL, fg=self.MUTED,
                 font=self.FONT_MONO_S).pack(side='left')
        self.cd_val_label = tk.Label(cd_row, text='100', bg=self.PANEL,
                                     fg=self.ACCENT, font=self.FONT_MONO, width=4)
        self.cd_val_label.pack(side='right')
        self.cd_slider = ttk.Scale(cd_row, from_=50, to=1000, orient='horizontal',
                                   command=self._on_cooldown)
        self.cd_slider.set(100)
        self.cd_slider.pack(side='left', fill='x', expand=True, padx=8)

        # Preset swatches
        sw_frame = tk.Frame(color_frame, bg=self.PANEL)
        sw_frame.pack(fill='x', padx=10, pady=(0, 10))
        tk.Label(sw_frame, text='PRESETS  ', bg=self.PANEL, fg=self.MUTED,
                 font=self.FONT_MONO_S).pack(side='left')
        for hex_c in self.PRESETS:
            b = tk.Button(sw_frame, bg=hex_c, relief='flat', width=2, height=1,
                          cursor='hand2', bd=0,
                          highlightbackground=self.BORDER, highlightthickness=1,
                          command=lambda h=hex_c: self._set_color(h))
            b.pack(side='left', padx=2)

        self._sep()

        # Keybind card
        self._card_label('⌨  TRIGGER KEY')
        kb_frame = tk.Frame(self.root, bg=self.PANEL)
        kb_frame.pack(fill='x', padx=14, pady=(0, 2))

        self.keybind_btn = tk.Button(kb_frame, text='[ F ]  — click to rebind',
                                     bg=self.PANEL2, fg=self.TEXT,
                                     font=('Consolas', 13, 'bold'),
                                     relief='flat', bd=0, cursor='hand2',
                                     activebackground=self.PANEL,
                                     activeforeground=self.ACCENT,
                                     highlightbackground=self.BORDER,
                                     highlightthickness=1,
                                     pady=14, command=self._start_listen)
        self.keybind_btn.pack(fill='x', padx=10, pady=10)

        self._sep()

        # Scan area label
        self._card_label('◎  SCAN REGION  (center pixel of your screen)')
        scan_info = tk.Frame(self.root, bg=self.PANEL)
        scan_info.pack(fill='x', padx=14, pady=(0, 2))
        self.scan_info_label = tk.Label(
            scan_info,
            text='Scanning 1×1 px at screen center.  Move your crosshair/cursor to the target.',
            bg=self.PANEL, fg=self.MUTED, font=self.FONT_MONO_S,
            wraplength=420, justify='left', pady=8, padx=10
        )
        self.scan_info_label.pack(fill='x')

        # Scan size selector (1x1, 3x3, 5x5)
        sz_frame = tk.Frame(self.root, bg=self.PANEL)
        sz_frame.pack(fill='x', padx=14, pady=(0, 2))
        tk.Label(sz_frame, text='SAMPLE SIZE', bg=self.PANEL, fg=self.MUTED,
                 font=self.FONT_MONO_S, padx=10).pack(side='left')
        self.sample_var = tk.StringVar(value='1×1')
        for opt in ['1×1', '3×3', '5×5']:
            rb = tk.Radiobutton(sz_frame, text=opt, variable=self.sample_var, value=opt,
                                bg=self.PANEL, fg=self.TEXT,
                                selectcolor=self.PANEL2,
                                activebackground=self.PANEL,
                                font=self.FONT_MONO, indicatoron=True)
            rb.pack(side='left', padx=6, pady=4)

        self._sep()

        # Toggle button
        self.toggle_btn = tk.Button(self.root,
                                    text='▷   START TRIGGER BOT',
                                    bg='#121820', fg=self.MUTED,
                                    font=('Consolas', 13, 'bold'),
                                    relief='flat', bd=0, cursor='hand2',
                                    activebackground='#0d1a10',
                                    activeforeground=self.GREEN,
                                    highlightbackground=self.BORDER,
                                    highlightthickness=1,
                                    pady=16,
                                    command=self._toggle)
        self.toggle_btn.pack(fill='x', padx=14, pady=6)

        self._sep()

        # Log
        self._card_label('≡  EVENT LOG')
        log_frame = tk.Frame(self.root, bg=self.PANEL)
        log_frame.pack(fill='x', padx=14, pady=(0, 10))

        self.log_text = tk.Text(log_frame, height=8, bg=self.PANEL2, fg=self.MUTED,
                                font=('Consolas', 9), relief='flat', bd=0,
                                state='disabled', wrap='word',
                                highlightbackground=self.BORDER, highlightthickness=1)
        self.log_text.pack(fill='x', padx=0, pady=0)
        self.log_text.tag_config('hit',  foreground=self.GREEN)
        self.log_text.tag_config('sys',  foreground=self.ACCENT)
        self.log_text.tag_config('warn', foreground=self.AMBER)
        self.log_text.tag_config('err',  foreground=self.ACCENT2)

        self._apply_ttk_style()
        self._log('ColorBot initialized — v2.0', 'sys')
        self._log('Set target color, bind a key, then hit START', 'sys')

    def _apply_ttk_style(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Horizontal.TScale',
                        background=self.PANEL,
                        troughcolor=self.BORDER,
                        sliderthickness=14,
                        sliderrelief='flat')

    def _sep(self):
        tk.Frame(self.root, bg=self.BORDER, height=1).pack(fill='x', padx=14, pady=5)

    def _card_label(self, text):
        tk.Label(self.root, text=text, bg=self.DARK_BG, fg=self.MUTED,
                 font=self.FONT_MONO_S, anchor='w').pack(fill='x', padx=14, pady=(4, 2))

    def _stat_box(self, parent, label, value, color, col):
        frame = tk.Frame(parent, bg=self.PANEL2, bd=0,
                         highlightbackground=self.BORDER, highlightthickness=1)
        frame.grid(row=0, column=col, sticky='ew', padx=(0 if col == 0 else 4, 0), pady=2)
        tk.Label(frame, text=label, bg=self.PANEL2, fg=self.MUTED,
                 font=self.FONT_MONO_S).pack(pady=(6,0))
        val = tk.Label(frame, text=value, bg=self.PANEL2, fg=color,
                       font=('Consolas', 20, 'bold'))
        val.pack(pady=(0, 6))
        return val

    # ── Color ────────────────────────────────────────────────────────────────
    def _set_color(self, hex_color: str):
        rgb = hex_to_rgb(hex_color)
        self.target_color = rgb
        self.color_btn.configure(bg=hex_color)
        self.hex_label.configure(text=hex_color.upper())
        self.rgb_label.configure(text=f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]})')

    def _pick_color(self):
        init = rgb_to_hex(*self.target_color)
        result = colorchooser.askcolor(color=init, title='Pick Target Color')
        if result and result[1]:
            self._set_color(result[1].upper())

    def _on_tolerance(self, val):
        self.tolerance = int(float(val))
        self.tol_val_label.configure(text=str(self.tolerance))

    def _on_cooldown(self, val):
        self.cooldown_ms = int(float(val))
        self.cd_val_label.configure(text=str(self.cooldown_ms))

    # ── Keybind ──────────────────────────────────────────────────────────────
    def _start_listen(self):
        if self.is_listening:
            self._stop_listen()
            return
        self.is_listening = True
        self.keybind_btn.configure(text='[ PRESS ANY KEY OR MOUSE BUTTON... ]',
                                   fg=self.ACCENT2,
                                   highlightbackground=self.ACCENT2)
        self._log('Waiting for keybind input — press ESC to cancel', 'warn')

        # Keyboard listener
        def on_press(key):
            if not self.is_listening:
                return False
            try:
                name = key.char.lower() if hasattr(key, 'char') and key.char else key.name.lower()
            except Exception:
                name = str(key)
            if name == 'esc':
                self.root.after(0, self._stop_listen)
                self._log('Keybind cancelled', 'warn')
                return False
            self.bound_key      = name
            self.bound_key_disp = name.upper()
            self.bound_type     = 'key'
            self.root.after(0, self._apply_keybind)
            return False

        # Mouse listener
        def on_click(x, y, button, pressed):
            if not self.is_listening or not pressed:
                return False
            btn_name = button.name.upper()
            btn_map  = {'left': 'LMB', 'right': 'RMB', 'middle': 'MMB',
                        'x1': 'MB4', 'x2': 'MB5'}
            self.bound_key      = btn_map.get(button.name, btn_name).lower()
            self.bound_key_disp = btn_map.get(button.name, btn_name)
            self.bound_type     = 'mouse'
            self.root.after(0, self._apply_keybind)
            return False

        self._kb_listener = pynput_keyboard.Listener(on_press=on_press)
        self._ms_listener = pynput_mouse.Listener(on_click=on_click)
        self._kb_listener.start()
        self._ms_listener.start()

    def _stop_listen(self):
        self.is_listening = False
        if self._kb_listener:
            try: self._kb_listener.stop()
            except: pass
        if self._ms_listener:
            try: self._ms_listener.stop()
            except: pass
        self.keybind_btn.configure(
            text=f'[ {self.bound_key_disp} ]  — click to rebind',
            fg=self.TEXT, highlightbackground=self.BORDER)

    def _apply_keybind(self):
        self._stop_listen()
        self.stat_key.configure(text=self.bound_key_disp)
        self.keybind_btn.configure(
            text=f'[ {self.bound_key_disp} ]  — click to rebind',
            fg=self.TEXT, highlightbackground=self.BORDER)
        self._log(f'Keybind set → [{self.bound_key_disp}]', 'sys')

    # ── Toggle bot ───────────────────────────────────────────────────────────
    def _toggle(self):
        if not self.active:
            self._start_bot()
        else:
            self._stop_bot()

    def _start_bot(self):
        self.active = True
        self.scan_active = True
        self.toggle_btn.configure(text='■   STOP TRIGGER BOT', fg=self.GREEN,
                                  bg='#0d1a10', highlightbackground='#00ff8844')
        self.status_label.configure(text='● ACTIVE', fg=self.GREEN)
        self._log(f'Bot started — targeting color {rgb_to_hex(*self.target_color)}'
                  f' tol={self.tolerance}', 'sys')
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()

    def _stop_bot(self):
        self.active = False
        self.scan_active = False
        self.toggle_btn.configure(text='▷   START TRIGGER BOT', fg=self.MUTED,
                                  bg='#121820', highlightbackground=self.BORDER)
        self.status_label.configure(text='● INACTIVE', fg=self.MUTED)
        self._log('Bot stopped', 'warn')

    # ── Scan loop (runs in thread) ───────────────────────────────────────────
    def _scan_loop(self):
        with mss.mss() as sct:
            while self.scan_active:
                try:
                    # Get primary monitor dimensions
                    mon = sct.monitors[1]
                    sw, sh = mon['width'], mon['height']
                    cx, cy = sw // 2, sh // 2

                    # Sample size
                    sz_map = {'1×1': 1, '3×3': 3, '5×5': 5}
                    sz = sz_map.get(self.sample_var.get(), 1)
                    half = sz // 2

                    region = {
                        'left':   cx - half + mon['left'],
                        'top':    cy - half + mon['top'],
                        'width':  sz,
                        'height': sz,
                    }

                    shot = sct.grab(region)
                    img = Image.frombytes('RGB', shot.size, shot.bgra, 'raw', 'BGRX')
                    pixels = list(img.getdata())

                    # Average color of sample
                    r = sum(p[0] for p in pixels) // len(pixels)
                    g = sum(p[1] for p in pixels) // len(pixels)
                    b = sum(p[2] for p in pixels) // len(pixels)
                    detected = (r, g, b)

                    self.cps_buffer += 1

                    dist = color_distance(detected, self.target_color)
                    if dist <= self.tolerance * 2.2:
                        now_ms = time.time() * 1000
                        if now_ms - self.last_trigger >= self.cooldown_ms:
                            self.last_trigger = now_ms
                            self._fire(detected)

                    time.sleep(0.008)  # ~120 checks/sec

                except Exception as e:
                    self.root.after(0, lambda err=e: self._log(f'Scan error: {err}', 'err'))
                    time.sleep(0.1)

    def _fire(self, detected_color):
        # Press key/button
        try:
            if self.bound_type == 'mouse':
                btn = MOUSE_BUTTON_MAP.get(self.bound_key.lower())
                if btn:
                    mouse_ctrl.press(btn)
                    mouse_ctrl.release(btn)
            else:
                key = SPECIAL_KEYS.get(self.bound_key.lower())
                if key:
                    keyboard_ctrl.press(key)
                    keyboard_ctrl.release(key)
                elif len(self.bound_key) == 1:
                    keyboard_ctrl.press(self.bound_key)
                    keyboard_ctrl.release(self.bound_key)
        except Exception as e:
            self.root.after(0, lambda err=e: self._log(f'Key error: {err}', 'err'))
            return

        hex_det = rgb_to_hex(*detected_color)
        self.trigger_count += 1
        self.root.after(0, self._update_trigger_ui, hex_det)

    def _update_trigger_ui(self, hex_det):
        self.stat_triggers.configure(text=str(self.trigger_count))
        self._log(f'HIT  {hex_det} → [{self.bound_key_disp}] fired  (#{self.trigger_count})', 'hit')
        # Flash window title briefly
        self.root.title('ColorBot  ★ TRIGGERED')
        self.root.after(150, lambda: self.root.title('ColorBot'))

    # ── CPS updater (runs every 500ms) ──────────────────────────────────────
    def _start_cps_updater(self):
        def update():
            now = time.time()
            elapsed = now - self.last_cps_time
            if elapsed >= 0.5:
                cps = int(self.cps_buffer / elapsed)
                self.cps_buffer = 0
                self.last_cps_time = now
                self.stat_cps.configure(text=str(cps))
            self.root.after(500, update)
        self.root.after(500, update)

    # ── Log ──────────────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = ''):
        ts = time.strftime('%H:%M:%S')
        self.log_text.configure(state='normal')
        self.log_text.insert('1.0', f'{ts}  {msg}\n', tag or '')
        # Keep log under 200 lines
        line_count = int(self.log_text.index('end-1c').split('.')[0])
        if line_count > 200:
            self.log_text.delete(f'{line_count}.0', 'end')
        self.log_text.configure(state='disabled')


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = ColorBot(root)
    root.mainloop()

if __name__ == '__main__':
    main()
