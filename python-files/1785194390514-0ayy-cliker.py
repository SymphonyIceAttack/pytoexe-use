import sys
import os

# Фикс для PyInstaller + PyTorch
if getattr(sys, 'frozen', False):
    # Распаковываем временные файлы
    import ctypes
    # Добавляем путь к DLL
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import pyautogui
import time
import threading
import sys
import os
from PIL import Image, ImageDraw, ImageTk
import easyocr
import numpy as np
from fuzzywuzzy import fuzz
import warnings
import datetime

# Подавляем предупреждения от PyTorch/EasyOCR
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

pyautogui.FAILSAFE = True


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


reader = easyocr.Reader(['ru', 'en'], gpu=False)


class RegionCapture:
    def __init__(self, callback):
        self.callback = callback
        self.window = tk.Toplevel()
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-alpha', 0.3)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='black')
        self.window.focus_force()
        self.window.grab_set()
        self.canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.is_drawing = False
        self.instruction_text = self.canvas.create_text(
            self.window.winfo_screenwidth() // 2, 30,
            text="Зажмите левую кнопку мыши и выделите прямоугольную область\nНажмите ПКМ для отмены",
            fill='white', font=('Arial', 16, 'bold'), justify='center'
        )
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.window.bind('<Button-3>', self.on_cancel)
        self.closed = False

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.is_drawing = True
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='#00FF00', width=3, dash=(5, 5)
        )

    def on_mouse_drag(self, event):
        if self.is_drawing and self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
            width = abs(event.x - self.start_x)
            height = abs(event.y - self.start_y)
            self.canvas.itemconfig(self.instruction_text,
                                   text=f"Выделите область (ширина: {width}, высота: {height})\nОтпустите кнопку для подтверждения | ПКМ для отмены")

    def on_mouse_up(self, event):
        if not self.is_drawing or self.closed:
            return
        self.is_drawing = False
        if self.start_x is not None and self.start_y is not None:
            x1 = min(self.start_x, event.x)
            y1 = min(self.start_y, event.y)
            x2 = max(self.start_x, event.x)
            y2 = max(self.start_y, event.y)
            if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
                self.canvas.itemconfig(self.instruction_text,
                                       text="Область слишком маленькая! Минимальный размер 10x10 пикселей\nПопробуйте снова или нажмите ПКМ для отмены",
                                       fill='#FF5252')
                self.canvas.delete(self.rect)
                self.rect = None
                self.start_x = None
                self.start_y = None
                return
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            self.canvas.create_oval(center_x - 5, center_y - 5, center_x + 5, center_y + 5,
                                    fill='#FF5252', outline='white', width=2)
            self.canvas.create_text(center_x, center_y - 20, text=f"Центр: ({center_x}, {center_y})",
                                    fill='yellow', font=('Arial', 12, 'bold'))
            self.window.after(500, lambda: self.complete_capture(x1, y1, x2, y2, center_x, center_y))

    def complete_capture(self, x1, y1, x2, y2, center_x, center_y):
        if not self.closed:
            self.closed = True
            self.window.grab_release()
            self.callback(x1, y1, x2, y2, center_x, center_y)
            self.window.destroy()

    def on_cancel(self, event=None):
        if not self.closed:
            self.closed = True
            self.window.grab_release()
            self.window.destroy()


class PointCapture:
    def __init__(self, callback):
        self.callback = callback
        self.window = tk.Toplevel()
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-alpha', 0.7)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='#1a1a1a')
        self.window.focus_force()
        self.window.grab_set()
        self.canvas = tk.Canvas(self.window, bg='#1a1a1a', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.crosshair_size = 30
        self.crosshair_color = '#00FF00'
        self.canvas.create_text(
            self.window.winfo_screenwidth() // 2, 50,
            text="Наведите прицел на нужное место и кликните левой кнопкой мыши\nНажмите ПКМ для отмены",
            fill='#e0e0e0', font=('Arial', 14), justify='center'
        )
        self.window.bind('<Motion>', self.on_mouse_move)
        self.window.bind('<Button-1>', self.on_click)
        self.window.bind('<Button-3>', self.on_cancel)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Button-3>', self.on_cancel)
        self.window.config(cursor='none')
        self.closed = False

    def on_mouse_move(self, event):
        self.canvas.delete('crosshair')
        x, y = event.x, event.y
        self.canvas.create_line(x - self.crosshair_size, y, x + self.crosshair_size, y,
                                fill=self.crosshair_color, width=2, tags='crosshair')
        self.canvas.create_line(x, y - self.crosshair_size, x, y + self.crosshair_size,
                                fill=self.crosshair_color, width=2, tags='crosshair')
        r = self.crosshair_size // 3
        self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=self.crosshair_color, width=2, tags='crosshair')
        self.canvas.create_text(x + 40, y - 20, text=f"X: {x}, Y: {y}", fill='yellow',
                                font=('Arial', 10, 'bold'), tags='crosshair')

    def on_click(self, event):
        if not self.closed:
            self.closed = True
            self.window.grab_release()
            self.callback(event.x, event.y)
            self.window.destroy()

    def on_cancel(self, event=None):
        if not self.closed:
            self.closed = True
            self.window.grab_release()
            self.window.destroy()


class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", color='#888888', **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._on_focus_out()

    def _on_focus_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color

    def _on_focus_out(self, *args):
        if not self.get():
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color


class CenteredEntry(tk.Entry):
    """Entry с выравниванием текста по центру"""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, justify='center', **kwargs)


class StatusIndicator(tk.Frame):
    STATUS_COLORS = {
        "Очередь": "#4CAF50",
        "Никого": "#f44336",
        "Отсрочка": "#FF9800",
        "default": "#FFD700"
    }

    def __init__(self, master, width=80, height=24, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.config(bg="#2b2b2b")
        self.pack_propagate(False)
        self.label = tk.Label(self, text="───", bg="#FFD700", fg="#1a1a1a",
                              font=('Arial', 9, 'bold'), width=12, height=1)
        self.label.pack(fill="both", expand=True)

    def set_status(self, status_text):
        color = self.STATUS_COLORS.get(status_text, self.STATUS_COLORS["default"])
        self.label.config(text=status_text, bg=color)

    def reset(self):
        self.label.config(text="───", bg=self.STATUS_COLORS["default"])


class AutoClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("ZRouteViceClicker")
        self.root.geometry("660x550")
        self.root.resizable(False, False)

        self.bg_dark = "#2b2b2b"
        self.bg_frame = "#333333"
        self.bg_entry = "#404040"
        self.fg_text = "#e0e0e0"
        self.fg_label = "#cccccc"

        self.root.configure(bg=self.bg_dark)
        self.set_window_icon()

        self.running = False
        self.capture_window = None
        self.log_cleanup_timer = None

        self.main_actions_active = [True, True, True, True]
        self.main_entries = []
        self.common_entries = []
        self.saved_main_values = {}
        self.saved_common_values = {}

        self.timers = {}
        self.timer_threads = {}
        self.status_indicators = {}
        self.ocr_regions = {}
        self.previous_status = {}
        self.first_run = {}
        self.last_confirm_times = {}

        self.terminal = None

        # --- Заголовок ---
        tk.Label(root, text="ZRoute-кликер V2.3", font=("Arial", 14, "bold"),
                 bg=self.bg_dark, fg=self.fg_text).pack(pady=5)

        # --- Notebook компактный ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=5, padx=15, fill="x")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.bg_frame, foreground=self.fg_text,
                        padding=[15, 3], font=('Arial', 9, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#1976D2')], foreground=[('selected', 'white')])
        style.configure('TFrame', background=self.bg_dark)

        # --- Вкладка Основные действия ---
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Основные действия")

        main_frame = tk.Frame(self.main_tab, bg=self.bg_dark)
        main_frame.pack(pady=5, padx=5, fill="x")

        header_main = tk.Frame(main_frame, bg=self.bg_dark)
        header_main.pack(fill="x", pady=(0, 3))
        # Увеличенные ширины заголовков (в 1.5 раза)
        for text, width in [("Действие", 13), ("   X", 6), ("   Y", 6), ("  Цикл(с)", 9), ("Отсрочка(с)", 10), ("Проверка(с)", 10),
                            ("🔍", 3), (" ⏱", 9), ("  Статус", 11)]:
            tk.Label(header_main, text=text, width=width, bg=self.bg_dark, fg=self.fg_label,
                     font=('Arial', 9, 'bold')).pack(side="left", padx=2)

        self.main_actions_frame = tk.Frame(main_frame, bg=self.bg_dark)
        self.main_actions_frame.pack(fill="x")

        self.main_actions = [
            ("🏗️ Стройка", "#1a2733", "#64B5F6", "60", "60", "1"),
            ("🔬 Исследования", "#2a1a33", "#CE93D8", "60", "60", "1"),
            ("🛡️ Оборона", "#331a1a", "#EF9A9A", "60", "60", "1"),
            ("👥 Гражданка", "#332b1a", "#FFD54F", "60", "60", "1"),
        ]

        # --- Вкладка Общие действия ---
        self.common_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.common_tab, text="Общие действия")

        common_frame = tk.Frame(self.common_tab, bg=self.bg_dark)
        common_frame.pack(pady=5, padx=5, fill="x")

        header_common = tk.Frame(common_frame, bg=self.bg_dark)
        header_common.pack(fill="x", pady=(0, 3))
        for text, width in [("Действие", 18), ("X", 6), ("Y", 6), ("Задержка", 9), ("🎯", 4)]:
            tk.Label(header_common, text=text, width=width, bg=self.bg_dark, fg=self.fg_label,
                     font=('Arial', 9, 'bold')).pack(side="left", padx=2)

        self.common_actions_frame = tk.Frame(common_frame, bg=self.bg_dark)
        self.common_actions_frame.pack(fill="x")

        self.common_actions = [
            ("❌ Закрыть", "#2a2a2a", "#e0e0e0", "1", False),
            ("✓ Подтвердить", "#2a2a2a", "#e0e0e0", "1", False),
            ("📋 Список", "#2a2a2a", "#e0e0e0", "1", False),
            ("☑ Галка", "#2a2a2a", "#e0e0e0", "1", True),
            ("✕ Крестик", "#2a2a2a", "#e0e0e0", "1", True),
        ]

        for i, (name, bg_color, text_color, default_delay, double_click) in enumerate(self.common_actions):
            self._create_common_row(self.common_actions_frame, i, name, bg_color, text_color, default_delay,
                                    double_click)

        # --- Кнопки ---
        control_frame = tk.Frame(root, bg=self.bg_dark)
        control_frame.pack(pady=5)

        self.status_label = tk.Label(control_frame, text="● Остановлен", fg="#EF5350", bg=self.bg_dark,
                                     font=("Arial", 10))
        self.status_label.pack(side="left", padx=10)

        self.start_btn = tk.Button(control_frame, text="▶ Запустить", bg="#4CAF50", fg="white",
                                   width=17, command=self.start, font=("Arial", 9))
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(control_frame, text="⏹ Остановить", bg="#f44336", fg="white",
                                  width=17, command=self.stop, font=("Arial", 9))
        self.stop_btn.pack(side="left", padx=5)

        # --- Терминал ---
        term_frame = tk.LabelFrame(root, text="Лог", padx=5, pady=5, bg=self.bg_dark, fg=self.fg_text,
                                   font=('Arial', 9, 'bold'))
        term_frame.pack(pady=5, padx=15, fill="both", expand=True)

        self.terminal = scrolledtext.ScrolledText(term_frame, height=8, bg="#1a1a1a", fg="#00FF00",
                                                  font=('Consolas', 9), insertbackground='white')
        self.terminal.pack(fill="both", expand=True)
        self.terminal.config(state='disabled')

        self._setup_terminal()

        hotkey_label = tk.Label(root, text="Вопросы по кликеру к альянсу UCO S37",
                                bg=self.bg_dark, fg="#888888", font=("Arial", 8))
        hotkey_label.pack()

        self.update_mode_display()

        self._start_log_cleanup()

    def _setup_terminal(self):
        import builtins
        original_print = builtins.print

        def terminal_print(*args, **kwargs):
            original_print(*args, **kwargs)
            if self.terminal and self.terminal.winfo_exists():
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                text = " ".join(str(arg) for arg in args)
                self.terminal.config(state='normal')
                self.terminal.insert(tk.END, f"[{timestamp}] {text}\n")
                self.terminal.see(tk.END)
                self.terminal.config(state='disabled')

        builtins.print = terminal_print

    def _start_log_cleanup(self):
        self._cleanup_log()
        self.log_cleanup_timer = self.root.after(300000, self._start_log_cleanup)

    def _cleanup_log(self):
        if self.terminal and self.terminal.winfo_exists():
            self.terminal.config(state='normal')
            all_lines = self.terminal.get("1.0", tk.END).splitlines()
            if len(all_lines) > 100:
                self.terminal.delete("1.0", tk.END)
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.terminal.insert(tk.END, f"[{timestamp}] 🧹 Лог очищен (оставлены последние 100 строк)\n")
                for line in all_lines[-100:]:
                    if line.strip():
                        self.terminal.insert(tk.END, line + "\n")
                self.terminal.see(tk.END)
            self.terminal.config(state='disabled')

    def set_window_icon(self):
        try:
            icon_path = resource_path('window_icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass

    def toggle_main_action(self, index):
        self.main_actions_active[index] = not self.main_actions_active[index]
        if not self.main_actions_active[index]:
            self.stop_and_reset_timer(index)
        self.update_mode_display()

    def update_mode_display(self):
        self._save_current_values()
        for widget in self.main_actions_frame.winfo_children():
            widget.pack_forget()
        self.main_entries = []

        for i, (name, bg_color, text_color, default_cycle, default_delay, default_check) in enumerate(
                self.main_actions):
            self._create_main_row(self.main_actions_frame, i, name, bg_color, text_color, default_cycle, default_delay,
                                  default_check,
                                  is_main=True, main_index=i, show_timer=True)

        self._restore_saved_values()

    def _save_current_values(self):
        self.saved_main_values = {}
        for i, entry in enumerate(self.main_entries):
            if entry['x_entry'].winfo_exists():
                x_val = entry['x_entry'].get()
                y_val = entry['y_entry'].get()
                cycle_val = entry['cycle_entry'].get()
                delay_val = entry['delay_entry'].get()
                check_val = entry['check_entry'].get()
                if x_val:
                    self.saved_main_values[i] = {
                        'x': x_val, 'y': y_val,
                        'cycle': cycle_val if entry['cycle_entry']['fg'] != '#888888' else '',
                        'delay': delay_val if entry['delay_entry']['fg'] != '#888888' else '',
                        'check': check_val if entry['check_entry']['fg'] != '#888888' else ''
                    }

        self.saved_common_values = {}
        for i, entry in enumerate(self.common_entries):
            if entry['x_entry'].winfo_exists():
                x_val = entry['x_entry'].get()
                y_val = entry['y_entry'].get()
                common_delay = entry['delay_entry'].get()
                if x_val:
                    self.saved_common_values[i] = {
                        'x': x_val, 'y': y_val,
                        'delay': common_delay if entry['delay_entry']['fg'] != '#888888' else ''
                    }

    def _restore_saved_values(self):
        for i, entry in enumerate(self.main_entries):
            if i in self.saved_main_values and entry['x_entry'].winfo_exists():
                saved = self.saved_main_values[i]
                if entry['x_entry']['state'] != 'disabled':
                    entry['x_entry'].delete(0, tk.END)
                    if saved['x']: entry['x_entry'].insert(0, saved['x'])
                    entry['y_entry'].delete(0, tk.END)
                    if saved['y']: entry['y_entry'].insert(0, saved['y'])
                    if saved['cycle']:
                        entry['cycle_entry'].delete(0, tk.END)
                        entry['cycle_entry'].insert(0, saved['cycle'])
                        entry['cycle_entry']['fg'] = entry['cycle_entry'].default_fg_color
                    if saved['delay']:
                        entry['delay_entry'].delete(0, tk.END)
                        entry['delay_entry'].insert(0, saved['delay'])
                        entry['delay_entry']['fg'] = entry['delay_entry'].default_fg_color
                    if saved['check']:
                        entry['check_entry'].delete(0, tk.END)
                        entry['check_entry'].insert(0, saved['check'])
                        entry['check_entry']['fg'] = entry['check_entry'].default_fg_color

        for i, entry in enumerate(self.common_entries):
            if i in self.saved_common_values and entry['x_entry'].winfo_exists():
                saved = self.saved_common_values[i]
                if entry['x_entry']['state'] != 'disabled':
                    entry['x_entry'].delete(0, tk.END)
                    if saved['x']: entry['x_entry'].insert(0, saved['x'])
                    entry['y_entry'].delete(0, tk.END)
                    if saved['y']: entry['y_entry'].insert(0, saved['y'])
                    if saved['delay']:
                        entry['delay_entry'].delete(0, tk.END)
                        entry['delay_entry'].insert(0, saved['delay'])
                        entry['delay_entry']['fg'] = entry['delay_entry'].default_fg_color

    def _create_main_row(self, parent_frame, index, name, bg_color, text_color, default_cycle, default_delay,
                         default_check,
                         is_main=False, main_index=None, show_timer=False):
        is_active = self.main_actions_active[main_index] if main_index is not None else True

        if is_active:
            current_bg = bg_color
            current_text = text_color
            entry_state = "normal"
            label_font = ('Arial', 10, 'bold')
        else:
            current_bg = "#1a1a1a"
            current_text = "#555555"
            entry_state = "disabled"
            label_font = ('Arial', 10, 'overstrike')

        frame = tk.Frame(parent_frame, bg=current_bg)
        frame.pack(fill="x", pady=2, ipady=2)

        cmd = lambda idx=main_index: self.toggle_main_action(idx)
        name_label = tk.Label(frame, text=name, width=13, bg=current_bg, fg=current_text,
                              font=label_font, anchor="w", cursor="hand2")
        name_label.pack(side="left", padx=2)
        name_label.bind("<Button-1>", lambda e, c=cmd: c())

        # Увеличенные поля ввода с центрированием
        x_entry = CenteredEntry(frame, width=6, font=('Arial', 10), bg=self.bg_entry,
                                fg=self.fg_text if is_active else "#555555", insertbackground=self.fg_text,
                                state=entry_state)
        x_entry.pack(side="left", padx=2)

        y_entry = CenteredEntry(frame, width=6, font=('Arial', 10), bg=self.bg_entry,
                                fg=self.fg_text if is_active else "#555555", insertbackground=self.fg_text,
                                state=entry_state)
        y_entry.pack(side="left", padx=2)

        cycle_entry = PlaceholderEntry(frame, placeholder=default_cycle, width=9, font=('Arial', 10))
        cycle_entry.pack(side="left", padx=2)
        cycle_entry.config(bg=self.bg_entry, fg=self.fg_text if is_active else "#555555",
                           insertbackground=self.fg_text, state=entry_state)
        cycle_entry.config(justify='center')

        delay_entry = PlaceholderEntry(frame, placeholder=default_delay, width=9, font=('Arial', 10))
        delay_entry.pack(side="left", padx=2)
        delay_entry.config(bg=self.bg_entry, fg=self.fg_text if is_active else "#555555",
                           insertbackground=self.fg_text, state=entry_state)
        delay_entry.config(justify='center')

        check_entry = PlaceholderEntry(frame, placeholder=default_check, width=9, font=('Arial', 10))
        check_entry.pack(side="left", padx=2)
        check_entry.config(bg=self.bg_entry, fg=self.fg_text if is_active else "#555555",
                           insertbackground=self.fg_text, state=entry_state)
        check_entry.config(justify='center')

        btn_capture = tk.Button(frame, text="🔍", width=4,
                                command=lambda idx=index: self.capture_region(idx),
                                bg="#E65100" if is_active else "#444444",
                                fg="white" if is_active else "#888888", font=('Arial', 9),
                                state="normal" if is_active else "disabled")
        btn_capture.pack(side="left", padx=2)

        timer_label = None
        if show_timer:
            timer_label = tk.Label(frame, text="00:00", width=9, bg=current_bg, fg="#FFEB3B",
                                   font=('Arial', 10, 'bold'))
            timer_label.pack(side="left", padx=2)
            self.timers[index] = [0, False, timer_label]
            self.timer_threads[index] = None

        status_indicator = StatusIndicator(frame, width=95, height=26)
        status_indicator.pack(side="left", padx=2)
        self.status_indicators[index] = status_indicator

        self.main_entries.append({
            'x_entry': x_entry, 'y_entry': y_entry,
            'cycle_entry': cycle_entry, 'delay_entry': delay_entry, 'check_entry': check_entry,
            'name': name, 'is_active': is_active,
            'timer_label': timer_label, 'show_timer': show_timer, 'index': index
        })

    def _create_common_row(self, parent_frame, index, name, bg_color, text_color, default_delay, double_click=False):
        frame = tk.Frame(parent_frame, bg=bg_color)
        frame.pack(fill="x", pady=2, ipady=2)

        tk.Label(frame, text=name, width=18, bg=bg_color, fg=text_color, font=('Arial', 10, 'bold'), anchor="w").pack(
            side="left", padx=2)

        x_entry = CenteredEntry(frame, width=6, font=('Arial', 10), bg=self.bg_entry, fg=self.fg_text,
                                insertbackground=self.fg_text)
        x_entry.pack(side="left", padx=2)

        y_entry = CenteredEntry(frame, width=6, font=('Arial', 10), bg=self.bg_entry, fg=self.fg_text,
                                insertbackground=self.fg_text)
        y_entry.pack(side="left", padx=2)

        delay_entry = PlaceholderEntry(frame, placeholder=default_delay, width=9, font=('Arial', 10))
        delay_entry.pack(side="left", padx=2)
        delay_entry.config(bg=self.bg_entry, fg=self.fg_text, insertbackground=self.fg_text, justify='center')

        btn_capture = tk.Button(frame, text="🎯", width=4, command=lambda idx=index: self.capture_point(idx),
                                bg="#1976D2", fg="white", font=('Arial', 9))
        btn_capture.pack(side="left", padx=2)

        if double_click:
            tk.Label(frame, text="x2", bg=bg_color, fg="#FF5722", font=('Arial', 10, 'bold')).pack(side="left", padx=2)

        self.common_entries.append({
            'x_entry': x_entry, 'y_entry': y_entry, 'delay_entry': delay_entry,
            'double_click': double_click, 'name': name, 'index': index
        })

    def get_delay_for_index(self, index):
        for entry in self.main_entries:
            if entry['index'] == index:
                delay_text = entry['delay_entry'].get()
                if delay_text and entry['delay_entry']['fg'] != '#888888':
                    try:
                        delay = float(delay_text)
                        if delay > 0: return delay
                    except:
                        pass
                try:
                    return float(entry['delay_entry'].placeholder)
                except:
                    return 60.0
        return 60.0

    def get_cycle_delay_for_index(self, index):
        for entry in self.main_entries:
            if entry['index'] == index:
                cycle_text = entry['cycle_entry'].get()
                if cycle_text and entry['cycle_entry']['fg'] != '#888888':
                    try:
                        delay = float(cycle_text)
                        if delay <= 0: raise ValueError
                        return delay
                    except:
                        pass
                try:
                    return float(entry['cycle_entry'].placeholder)
                except:
                    return 60.0
        return 60.0

    def get_check_interval_for_index(self, index):
        for entry in self.main_entries:
            if entry['index'] == index:
                check_text = entry['check_entry'].get()
                if check_text and entry['check_entry']['fg'] != '#888888':
                    try:
                        interval = int(check_text)
                        if 1 <= interval <= 10: return interval
                    except:
                        pass
                try:
                    return int(entry['check_entry'].placeholder)
                except:
                    return 1
        return 1

    def set_status(self, index, status_text):
        if index in self.status_indicators:
            self.status_indicators[index].set_status(status_text)

    def reset_all_statuses(self):
        for indicator in self.status_indicators.values():
            indicator.reset()

    def capture_region(self, index):
        if self.capture_window and not self.capture_window.closed:
            self.capture_window.on_cancel()
        self.capture_window = RegionCapture(
            lambda x1, y1, x2, y2, cx, cy: self.set_region_coords(index, x1, y1, x2, y2, cx, cy))

    def capture_point(self, index):
        if self.capture_window and not self.capture_window.closed:
            self.capture_window.on_cancel()
        self.capture_window = PointCapture(lambda x, y: self.set_common_coords(index, x, y))

    def set_region_coords(self, index, x1, y1, x2, y2, center_x, center_y):
        self.ocr_regions[index] = (x1, y1, x2, y2)
        for entry in self.main_entries:
            if entry['index'] == index:
                if entry['x_entry']['state'] != 'disabled':
                    entry['x_entry'].config(state='normal')
                    entry['y_entry'].config(state='normal')
                    entry['x_entry'].delete(0, tk.END)
                    entry['x_entry'].insert(0, str(center_x))
                    entry['y_entry'].delete(0, tk.END)
                    entry['y_entry'].insert(0, str(center_y))
                    print(f"✓ {entry['name']}: центр({center_x}, {center_y}), OCR({x1},{y1})-({x2},{y2})")
                break

    def set_common_coords(self, index, x, y):
        if index < len(self.common_entries):
            entry = self.common_entries[index]
            entry['x_entry'].delete(0, tk.END)
            entry['x_entry'].insert(0, str(x))
            entry['y_entry'].delete(0, tk.END)
            entry['y_entry'].insert(0, str(y))
            print(f"✓ {entry['name']}: ({x}, {y})")

    def check_ocr_for_index(self, index):
        if index not in self.ocr_regions:
            return True

        x1, y1, x2, y2 = self.ocr_regions[index]
        try:
            screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
            result_text = reader.readtext(np.array(screenshot), detail=0)
            full_text = " ".join(result_text).lower()

            target_variants = [
                "не назначен", "неназначен", "he назначен", "не назнaчен",
                "нe назначен", "не назначeн", "неназначeн"
            ]

            for variant in target_variants:
                if variant in full_text:
                    return False

            words = full_text.split()
            for word in words:
                if len(word) >= 5:
                    if fuzz.ratio(word, "неназначен") >= 65:
                        return False
            return True
        except Exception as e:
            print(f"⚠ Ошибка OCR [{index}]: {e}")
            return True

    def get_points_with_delays(self):
        all_points = {}
        for main_idx in range(4):
            if not self.main_actions_active[main_idx]:
                continue

            main_entry = None
            for entry in self.main_entries:
                if entry['index'] == main_idx and entry['is_active']:
                    main_entry = entry
                    break

            if main_entry:
                try:
                    x = int(main_entry['x_entry'].get())
                    y = int(main_entry['y_entry'].get())
                    cycle_delay = self.get_cycle_delay_for_index(main_idx)
                    postpone_delay = self.get_delay_for_index(main_idx)
                    check_interval = self.get_check_interval_for_index(main_idx)

                    points_for_action = [{
                        'x': x, 'y': y, 'delay': 1.0, 'double_click': False,
                        'name': main_entry['name'], 'is_confirm': False, 'is_main_action': True,
                        'main_index': main_idx, 'cycle_delay': cycle_delay,
                        'postpone_delay': postpone_delay, 'check_interval': check_interval
                    }]

                    for common_entry in self.common_entries:
                        try:
                            cx = int(common_entry['x_entry'].get())
                            cy = int(common_entry['y_entry'].get())
                            delay_text = common_entry['delay_entry'].get()
                            delay = float(delay_text) if delay_text and common_entry['delay_entry'][
                                'fg'] != '#888888' else 1.0
                            if delay < 0: raise ValueError

                            points_for_action.append({
                                'x': cx, 'y': cy, 'delay': delay,
                                'double_click': common_entry['double_click'],
                                'name': common_entry['name'],
                                'is_confirm': common_entry['name'] == "✓ Подтвердить",
                                'is_main_action': False, 'main_index': main_idx,
                                'cycle_delay': cycle_delay, 'postpone_delay': postpone_delay,
                                'check_interval': check_interval
                            })
                        except ValueError:
                            messagebox.showerror("Ошибка", f"Проверьте координаты для '{common_entry['name']}'!")
                            return None

                    all_points[main_idx] = points_for_action
                except ValueError:
                    messagebox.showerror("Ошибка", f"Проверьте координаты для '{main_entry['name']}'!")
                    return None
        return all_points

    def start(self):
        if self.running: return

        all_points = self.get_points_with_delays()
        if all_points is None: return
        if not all_points:
            messagebox.showwarning("Внимание", "Нет активных действий!")
            return

        self.running = True
        self.last_confirm_times = {}
        self.previous_status = {}
        self.first_run = {}
        self.status_label.config(text="● Работает", fg="#4CAF50")
        self.start_btn.config(state="disabled")
        self.reset_all_statuses()

        print("=" * 40)
        print("🚀 КЛИКЕР ЗАПУЩЕН")
        print("=" * 40)

        self.threads = []
        for main_idx, points in all_points.items():
            self.first_run[main_idx] = True
            thread = threading.Thread(target=self.action_loop, args=(main_idx, points), daemon=True)
            thread.start()
            self.threads.append(thread)

    def stop(self):
        self.running = False
        self.status_label.config(text="● Остановлен", fg="#EF5350")
        self.start_btn.config(state="normal")
        self._reset_all_timers()
        self.reset_all_statuses()
        if self.log_cleanup_timer:
            self.root.after_cancel(self.log_cleanup_timer)
        print("🛑 Кликер остановлен")

    def _reset_all_timers(self):
        for index in self.timers:
            self.timers[index][1] = True
            self.timers[index][0] = 0
            self._update_timer_ui(index)

    def _update_timer_ui(self, index):
        if index in self.timers:
            timer_label = self.timers[index][2]
            if timer_label and timer_label.winfo_exists():
                timer_label.config(text="00:00", fg="#FFEB3B")

    def wait_with_ocr_check(self, main_index, action_name, total_seconds, check_interval):
        print(f"  ⏳ {action_name}: ожидание {total_seconds}с, проверка каждые {check_interval}с")
        if main_index in self.timers:
            self.start_timer(main_index)

        last_check_time = 0
        for sec in range(total_seconds):
            if not self.running:
                return False

            if sec - last_check_time >= check_interval:
                print(f"  🔍 {action_name}: Проверка очереди...")
                if self.check_ocr_for_index(main_index):
                    print(f"  ⚡ {action_name}: очередь появилась! Немедленный переход к отсрочке!")
                    self.stop_and_reset_timer(main_index)
                    return True
                last_check_time = sec

            time.sleep(1)

        self.stop_and_reset_timer(main_index)
        return False

    def action_loop(self, main_index, points):
        cycle_delay = points[0]['cycle_delay']
        postpone_delay = points[0]['postpone_delay']
        check_interval = points[0]['check_interval']
        action_name = points[0]['name']
        is_first_run = self.first_run.get(main_index, False)

        print(f"▶ {action_name}: Цикл={cycle_delay}с, Отсрочка={postpone_delay}с, Проверка={check_interval}с")

        if is_first_run:
            print(f"  🔍 {action_name}: Проверка очереди (первый запуск)...")
            phrase_not_found = self.check_ocr_for_index(main_index)

            if phrase_not_found:
                print(f"  🔄 {action_name}: первый запуск, очередь есть → отсрочка {postpone_delay}с")
                self.root.after(0, lambda: self.set_status(main_index, "Отсрочка"))
                if main_index in self.timers:
                    self.start_timer(main_index)

                for _ in range(int(postpone_delay)):
                    if not self.running: return
                    time.sleep(1)
                if postpone_delay % 1 > 0 and self.running:
                    time.sleep(postpone_delay % 1)

                self.stop_and_reset_timer(main_index)
                print(f"  ✅ {action_name}: отсрочка завершена")

                self.root.after(0, lambda: self.set_status(main_index, "Очередь"))
                self.previous_status[main_index] = "not_found"
                self.first_run[main_index] = False

                self._run_click_cycle(main_index, points)
            else:
                print(f"  ⛔ {action_name}: первый запуск, никого → ожидание")
                self.root.after(0, lambda: self.set_status(main_index, "Никого"))
                self.previous_status[main_index] = "found"
                self.last_confirm_times[main_index] = time.time()
                self.first_run[main_index] = False

                self.wait_with_ocr_check(main_index, action_name, 60, check_interval)

        while self.running:
            if main_index in self.last_confirm_times:
                elapsed = time.time() - self.last_confirm_times[main_index]
                if elapsed < cycle_delay:
                    remaining = cycle_delay - elapsed
                    for _ in range(int(remaining)):
                        if not self.running: return
                        time.sleep(1)
                    if remaining % 1 > 0 and self.running:
                        time.sleep(remaining % 1)

            if not self.running: break

            print(f"  🔍 {action_name}: Проверка очереди...")
            phrase_not_found = self.check_ocr_for_index(main_index)
            prev = self.previous_status.get(main_index, None)

            if phrase_not_found:
                if prev == "found":
                    print(f"  ⚠ {action_name}: было 'Никого' → отсрочка {postpone_delay}с")
                    self.root.after(0, lambda: self.set_status(main_index, "Отсрочка"))
                    if main_index in self.timers:
                        self.start_timer(main_index)

                    for _ in range(int(postpone_delay)):
                        if not self.running: return
                        time.sleep(1)
                    if postpone_delay % 1 > 0 and self.running:
                        time.sleep(postpone_delay % 1)

                    self.stop_and_reset_timer(main_index)

                    print(f"  🔍 {action_name}: Проверка очереди после отсрочки...")
                    phrase_not_found = self.check_ocr_for_index(main_index)

                    if not phrase_not_found:
                        print(f"  ⛔ {action_name}: после отсрочки снова 'Никого'")
                        self.root.after(0, lambda: self.set_status(main_index, "Никого"))
                        self.previous_status[main_index] = "found"
                        self.last_confirm_times[main_index] = time.time()

                        self.wait_with_ocr_check(main_index, action_name, 60, check_interval)
                        continue

                    print(f"  ✅ {action_name}: отсрочка завершена, запуск цикла")

                self.root.after(0, lambda: self.set_status(main_index, "Очередь"))
                self.previous_status[main_index] = "not_found"
                print(f"  ▶ {action_name}: запуск цикла (Очередь)")

                self._run_click_cycle(main_index, points)

            else:
                print(f"  ⛔ {action_name}: Никого")
                self.root.after(0, lambda: self.set_status(main_index, "Никого"))
                self.previous_status[main_index] = "found"
                self.last_confirm_times[main_index] = time.time()

                self.wait_with_ocr_check(main_index, action_name, 60, check_interval)

    def _run_click_cycle(self, main_index, points):
        for i, point in enumerate(points):
            if not self.running: return
            x, y, delay = point['x'], point['y'], point['delay']
            double_click = point['double_click']
            is_confirm = point.get('is_confirm', False)

            pyautogui.click(x, y)
            if double_click:
                print(f"    Двойной клик: {point['name']} ({x}, {y})")
                time.sleep(1)
                if not self.running: return
                pyautogui.click(x, y)
            else:
                print(f"    Клик: {point['name']} ({x}, {y})")

            if is_confirm:
                if main_index in self.timers:
                    self.start_timer(main_index)
                    print(f"    ⏱ Таймер запущен")
                self.last_confirm_times[main_index] = time.time()

            if i < len(points) - 1:
                for _ in range(int(delay)):
                    if not self.running: return
                    time.sleep(1)
                if delay % 1 > 0 and self.running:
                    time.sleep(delay % 1)

    def stop_and_reset_timer(self, index):
        if index in self.timers:
            self.timers[index][1] = True
            self.timers[index][0] = 0
            self._update_timer_ui(index)

    def start_timer(self, index):
        if index not in self.timers: return
        timer_data = self.timers[index]
        timer_data[1] = False
        timer_data[0] = 0
        if self.timer_threads.get(index) and self.timer_threads[index].is_alive(): return

        def timer_loop():
            while not timer_data[1] and self.running:
                current_time = timer_data[0]
                try:
                    self.root.after(0, lambda t=current_time, idx=index: self.update_timer_label(idx, t))
                except:
                    pass
                time.sleep(1)
                if not timer_data[1] and self.running:
                    timer_data[0] += 1

        self.timer_threads[index] = threading.Thread(target=timer_loop, daemon=True)
        self.timer_threads[index].start()

    def update_timer_label(self, index, seconds):
        if index in self.timers:
            text = f"{seconds // 60:02d}:{seconds % 60:02d}"
            timer_label = self.timers[index][2]
            if timer_label and timer_label.winfo_exists():
                timer_label.config(text=text)


def main():
    root = tk.Tk()
    try:
        icon_path = resource_path('window_icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass

    app = AutoClicker(root)

    def on_closing():
        app.stop()
        if app.log_cleanup_timer:
            app.root.after_cancel(app.log_cleanup_timer)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    try:
        import pyautogui
        from PIL import Image, ImageDraw, ImageTk
    except ImportError:
        print("pip install pyautogui pillow easyocr fuzzywuzzy python-Levenshtein")
        exit(1)
    main()