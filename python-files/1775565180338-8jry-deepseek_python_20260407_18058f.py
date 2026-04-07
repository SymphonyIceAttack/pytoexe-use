import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import pyautogui
from pynput import keyboard, mouse
import json
import os
from datetime import datetime

class AutoClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("OP Auto Clicker 3.0")
        self.root.geometry("520680")
        self.root.resizable(False, False)
        
        # Переменные состояния
        self.running = False
        self.click_thread = None
        self.clicks_count = 0
        self.recording = False
        self.recorded_actions = []
        self.recording_start_time = 0
        self.current_config_file = None
        self.current_theme = "base"  # base, dark, purple, red
        
        # Создаём папку для конфигов
        self.config_dir = "autoclicker_configs"
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Настройки по умолчанию
        self.config = {
            'name': 'Default',
            'hours': 0,
            'mins': 0,
            'secs': 0,
            'milliseconds': 100,
            'mouse_button': 'Left',
            'click_type': 'Single',
            'location_type': 'Current',
            'fixed_x': 0,
            'fixed_y': 0,
            'hotkey': 'F6',
            'theme': 'base'
        }
        
        # Определяем темы
        self.themes = {
            "base": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "frame_bg": "#f0f0f0",
                "frame_fg": "#000000",
                "button_bg": "#e0e0e0",
                "button_fg": "#000000",
                "start_bg": "#4CAF50",
                "stop_bg": "#f44336",
                "entry_bg": "white",
                "status_bg": "#e0e0e0",
                "alpha": 1.0
            },
            "dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "frame_bg": "#2d2d2d",
                "frame_fg": "#ffffff",
                "button_bg": "#3d3d3d",
                "button_fg": "#ffffff",
                "start_bg": "#4CAF50",
                "stop_bg": "#f44336",
                "entry_bg": "#3d3d3d",
                "status_bg": "#2d2d2d",
                "alpha": 0.7
            },
            "purple": {
                "bg": "#2d1b4e",
                "fg": "#ffffff",
                "frame_bg": "#3d2b5e",
                "frame_fg": "#e0b0ff",
                "button_bg": "#4d3b6e",
                "button_fg": "#ffffff",
                "start_bg": "#9b59b6",
                "stop_bg": "#e74c3c",
                "entry_bg": "#4d3b6e",
                "status_bg": "#3d2b5e",
                "alpha": 0.7
            },
            "red": {
                "bg": "#4a0000",
                "fg": "#000000",
                "frame_bg": "#5a1010",
                "frame_fg": "#000000",
                "button_bg": "#6a2020",
                "button_fg": "#000000",
                "start_bg": "#ff6b6b",
                "stop_bg": "#cc0000",
                "entry_bg": "#ffcccc",
                "status_bg": "#5a1010",
                "alpha": 0.7
            }
        }
        
        # Применяем прозрачность (только для Windows)
        try:
            from ctypes import windll
            windll.user32.SetWindowLongW(self.root.winfo_id(), -20, windll.user32.GetWindowLongW(self.root.winfo_id(), -20) | 0x00080000)
            self.root.attributes('-alpha', self.themes[self.current_theme]["alpha"])
        except:
            pass
        
        # Создаём интерфейс
        self.create_widgets()
        
        # Загружаем список конфигов
        self.load_config_list()
        
        # Запускаем слушатель горячих клавиш
        self.start_hotkey_listener()
        
        # Обновление позиции мыши
        self.update_mouse_position()
        
        # Защита от случайного закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def apply_theme(self):
        """Применение выбранной темы"""
        theme = self.themes[self.current_theme]
        
        # Применяем прозрачность
        try:
            self.root.attributes('-alpha', theme["alpha"])
        except:
            pass
        
        # Применяем цвета ко всем виджетам
        self.root.configure(bg=theme["bg"])
        
        # Обновляем все фреймы
        for widget in self.root.winfo_children():
            self.update_widget_colors(widget, theme)
    
    def update_widget_colors(self, widget, theme):
        """Рекурсивное обновление цветов виджетов"""
        try:
            if isinstance(widget, (tk.Frame, tk.LabelFrame, tk.Label, tk.Button, 
                                   tk.Radiobutton, tk.Checkbutton, tk.Toplevel)):
                if isinstance(widget, tk.LabelFrame):
                    widget.configure(bg=theme["frame_bg"], fg=theme["frame_fg"])
                elif isinstance(widget, tk.Label) and widget.cget('text').startswith('●'):
                    pass  # Статус-лейбл не меняем
                elif isinstance(widget, tk.Label):
                    widget.configure(bg=theme["bg"], fg=theme["fg"])
                elif isinstance(widget, tk.Button):
                    if widget.cget('text') == "Start (F6)":
                        widget.configure(bg=theme["start_bg"], fg="white")
                    elif widget.cget('text') == "Stop (F6)":
                        widget.configure(bg=theme["stop_bg"], fg="white")
                    else:
                        widget.configure(bg=theme["button_bg"], fg=theme["button_fg"])
                elif isinstance(widget, tk.Radiobutton):
                    widget.configure(bg=theme["bg"], fg=theme["fg"], 
                                   activebackground=theme["bg"], selectcolor=theme["bg"])
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg=theme["bg"])
            elif isinstance(widget, ttk.Combobox):
                widget.configure(style="TCombobox")
        except:
            pass
        
        # Рекурсивно обновляем дочерние виджеты
        for child in widget.winfo_children():
            self.update_widget_colors(child, theme)
    
    def create_theme_selector(self, parent):
        """Создание селектора тем"""
        theme_frame = tk.LabelFrame(parent, text=" Theme ", font=('Arial', 9, 'bold'),
                                    bg=self.themes[self.current_theme]["frame_bg"],
                                    fg=self.themes[self.current_theme]["frame_fg"])
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        
        theme_buttons_frame = tk.Frame(theme_frame, bg=self.themes[self.current_theme]["bg"])
        theme_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        themes = [
            ("⚪ Base", "base", "#f0f0f0"),
            ("🌙 Dark", "dark", "#1e1e1e"),
            ("🟣 Purple", "purple", "#2d1b4e"),
            ("🔴 Red", "red", "#4a0000")
        ]
        
        for text, theme_name, color in themes:
            btn = tk.Button(theme_buttons_frame, text=text, command=lambda t=theme_name: self.change_theme(t),
                          bg=color, fg="white" if theme_name != "red" else "black",
                          relief=tk.RAISED, bd=1, width=12, padx=5, pady=2)
            btn.pack(side=tk.LEFT, padx=5)
    
    def change_theme(self, theme_name):
        """Смена темы"""
        self.current_theme = theme_name
        self.config['theme'] = theme_name
        self.apply_theme()
        
        # Пересоздаём интерфейс для обновления всех цветов
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()
    
    def create_widgets(self):
        theme = self.themes[self.current_theme]
        
        # Основной контейнер
        main_container = tk.Frame(self.root, bg=theme["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Селектор тем
        self.create_theme_selector(main_container)
        
        # ========== CLICK INTERVAL ==========
        interval_frame = tk.LabelFrame(main_container, text=" Click interval ", font=('Arial', 10, 'bold'),
                                       bg=theme["frame_bg"], fg=theme["frame_fg"], padx=10, pady=10)
        interval_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Часы
        hours_frame = tk.Frame(interval_frame, bg=theme["frame_bg"])
        hours_frame.pack(fill=tk.X, pady=3)
        tk.Label(hours_frame, text="Hours:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=10, anchor='w').pack(side=tk.LEFT)
        self.hours_var = tk.IntVar(value=self.config['hours'])
        hours_spin = tk.Spinbox(hours_frame, from_=0, to=23, width=10, textvariable=self.hours_var,
                                command=self.update_config, bg=theme["entry_bg"], fg=theme["fg"],
                                relief=tk.SUNKEN, bd=1)
        hours_spin.pack(side=tk.LEFT, padx=5)
        tk.Label(hours_frame, text="hours", bg=theme["frame_bg"], fg=theme["frame_fg"]).pack(side=tk.LEFT, padx=5)
        
        # Минуты
        mins_frame = tk.Frame(interval_frame, bg=theme["frame_bg"])
        mins_frame.pack(fill=tk.X, pady=3)
        tk.Label(mins_frame, text="Minutes:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=10, anchor='w').pack(side=tk.LEFT)
        self.mins_var = tk.IntVar(value=self.config['mins'])
        mins_spin = tk.Spinbox(mins_frame, from_=0, to=59, width=10, textvariable=self.mins_var,
                               command=self.update_config, bg=theme["entry_bg"], fg=theme["fg"],
                               relief=tk.SUNKEN, bd=1)
        mins_spin.pack(side=tk.LEFT, padx=5)
        tk.Label(mins_frame, text="mins", bg=theme["frame_bg"], fg=theme["frame_fg"]).pack(side=tk.LEFT, padx=5)
        
        # Секунды
        secs_frame = tk.Frame(interval_frame, bg=theme["frame_bg"])
        secs_frame.pack(fill=tk.X, pady=3)
        tk.Label(secs_frame, text="Seconds:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=10, anchor='w').pack(side=tk.LEFT)
        self.secs_var = tk.IntVar(value=self.config['secs'])
        secs_spin = tk.Spinbox(secs_frame, from_=0, to=59, width=10, textvariable=self.secs_var,
                               command=self.update_config, bg=theme["entry_bg"], fg=theme["fg"],
                               relief=tk.SUNKEN, bd=1)
        secs_spin.pack(side=tk.LEFT, padx=5)
        tk.Label(secs_frame, text="secs", bg=theme["frame_bg"], fg=theme["frame_fg"]).pack(side=tk.LEFT, padx=5)
        
        # Миллисекунды
        ms_frame = tk.Frame(interval_frame, bg=theme["frame_bg"])
        ms_frame.pack(fill=tk.X, pady=3)
        tk.Label(ms_frame, text="Milliseconds:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=10, anchor='w').pack(side=tk.LEFT)
        self.ms_var = tk.IntVar(value=self.config['milliseconds'])
        ms_spin = tk.Spinbox(ms_frame, from_=0, to=999, width=10, textvariable=self.ms_var,
                             command=self.update_config, bg=theme["entry_bg"], fg=theme["fg"],
                             relief=tk.SUNKEN, bd=1)
        ms_spin.pack(side=tk.LEFT, padx=5)
        tk.Label(ms_frame, text="milliseconds", bg=theme["frame_bg"], fg=theme["frame_fg"]).pack(side=tk.LEFT, padx=5)
        
        # ========== CLICK OPTIONS ==========
        options_frame = tk.LabelFrame(main_container, text=" Click options ", font=('Arial', 10, 'bold'),
                                      bg=theme["frame_bg"], fg=theme["frame_fg"], padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mouse button
        mouse_frame = tk.Frame(options_frame, bg=theme["frame_bg"])
        mouse_frame.pack(fill=tk.X, pady=5)
        tk.Label(mouse_frame, text="Mouse button:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=12, anchor='w').pack(side=tk.LEFT)
        self.mouse_button = tk.StringVar(value=self.config['mouse_button'])
        tk.Radiobutton(mouse_frame, text="Left", variable=self.mouse_button, value="Left",
                       command=self.update_config, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mouse_frame, text="Right", variable=self.mouse_button, value="Right",
                       command=self.update_config, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mouse_frame, text="Middle", variable=self.mouse_button, value="Middle",
                       command=self.update_config, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT, padx=5)
        
        # Click type
        click_frame = tk.Frame(options_frame, bg=theme["frame_bg"])
        click_frame.pack(fill=tk.X, pady=5)
        tk.Label(click_frame, text="Click type:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=12, anchor='w').pack(side=tk.LEFT)
        self.click_type = tk.StringVar(value=self.config['click_type'])
        tk.Radiobutton(click_frame, text="Single", variable=self.click_type, value="Single",
                       command=self.update_config, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(click_frame, text="Repeat until stopped", variable=self.click_type, value="Repeat until stopped",
                       command=self.update_config, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT, padx=5)
        
        # ========== CURSOR POSITION ==========
        cursor_frame = tk.LabelFrame(main_container, text=" Cursor position ", font=('Arial', 10, 'bold'),
                                     bg=theme["frame_bg"], fg=theme["frame_fg"], padx=10, pady=10)
        cursor_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Current location
        self.location_type = tk.StringVar(value=self.config['location_type'])
        current_loc_frame = tk.Frame(cursor_frame, bg=theme["frame_bg"])
        current_loc_frame.pack(fill=tk.X, pady=2)
        tk.Radiobutton(current_loc_frame, text="Current location", variable=self.location_type, value="Current",
                       command=self.on_location_change, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT)
        
        # Pick location
        pick_loc_frame = tk.Frame(cursor_frame, bg=theme["frame_bg"])
        pick_loc_frame.pack(fill=tk.X, pady=2)
        tk.Radiobutton(pick_loc_frame, text="Pick location", variable=self.location_type, value="Pick",
                       command=self.on_location_change, bg=theme["frame_bg"], fg=theme["frame_fg"],
                       activebackground=theme["frame_bg"], selectcolor=theme["frame_bg"]).pack(side=tk.LEFT)
        self.pick_btn = tk.Button(pick_loc_frame, text="Pick location", command=self.pick_location,
                                  bg=theme["button_bg"], fg=theme["button_fg"],
                                  relief=tk.RAISED, bd=1, width=12)
        self.pick_btn.pack(side=tk.RIGHT, padx=5)
        
        # Координаты X, Y
        coords_frame = tk.Frame(cursor_frame, bg=theme["frame_bg"])
        coords_frame.pack(fill=tk.X, pady=5)
        
        x_frame = tk.Frame(coords_frame, bg=theme["frame_bg"])
        x_frame.pack(side=tk.LEFT, padx=(20, 20))
        tk.Label(x_frame, text="X:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=3, anchor='w').pack(side=tk.LEFT)
        self.x_var = tk.IntVar(value=self.config['fixed_x'])
        self.x_entry = tk.Entry(x_frame, textvariable=self.x_var, width=8, bg=theme["entry_bg"],
                               fg=theme["fg"], relief=tk.SUNKEN, bd=1)
        self.x_entry.pack(side=tk.LEFT, padx=2)
        self.x_entry.bind('<KeyRelease>', self.update_config)
        
        y_frame = tk.Frame(coords_frame, bg=theme["frame_bg"])
        y_frame.pack(side=tk.LEFT)
        tk.Label(y_frame, text="Y:", bg=theme["frame_bg"], fg=theme["frame_fg"], width=3, anchor='w').pack(side=tk.LEFT)
        self.y_var = tk.IntVar(value=self.config['fixed_y'])
        self.y_entry = tk.Entry(y_frame, textvariable=self.y_var, width=8, bg=theme["entry_bg"],
                               fg=theme["fg"], relief=tk.SUNKEN, bd=1)
        self.y_entry.pack(side=tk.LEFT, padx=2)
        self.y_entry.bind('<KeyRelease>', self.update_config)
        
        # ========== КНОПКИ УПРАВЛЕНИЯ ==========
        buttons_frame = tk.Frame(main_container, bg=theme["bg"])
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = tk.Button(buttons_frame, text="Start (F6)", command=self.start_clicker,
                                   bg=theme["start_bg"], fg="white", font=('Arial', 10, 'bold'),
                                   relief=tk.RAISED, bd=2, width=14, height=1)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(buttons_frame, text="Stop (F6)", command=self.stop_clicker,
                                  bg=theme["stop_bg"], fg="white", font=('Arial', 10, 'bold'),
                                  relief=tk.RAISED, bd=2, width=14, height=1, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        hotkey_btn = tk.Button(buttons_frame, text="Hotkey setting", command=self.hotkey_settings,
                               bg=theme["button_bg"], fg=theme["button_fg"],
                               relief=tk.RAISED, bd=1, width=14)
        hotkey_btn.pack(side=tk.LEFT, padx=5)
        
        # ========== RECORD & PLAYBACK ==========
        record_frame = tk.LabelFrame(main_container, text=" Record & Playback ", font=('Arial', 10, 'bold'),
                                     bg=theme["frame_bg"], fg=theme["frame_fg"], padx=10, pady=10)
        record_frame.pack(fill=tk.X, pady=(0, 10))
        
        record_buttons_frame = tk.Frame(record_frame, bg=theme["frame_bg"])
        record_buttons_frame.pack(fill=tk.X)
        
        self.record_btn = tk.Button(record_buttons_frame, text="● Record", command=self.toggle_recording,
                                    bg="#ff9800", fg="white", font=('Arial', 9, 'bold'),
                                    relief=tk.RAISED, bd=1, width=12)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.playback_btn = tk.Button(record_buttons_frame, text="▶ Play", command=self.play_recording,
                                      bg="#2196F3", fg="white", font=('Arial', 9, 'bold'),
                                      relief=tk.RAISED, bd=1, width=12, state=tk.DISABLED)
        self.playback_btn.pack(side=tk.LEFT, padx=5)
        
        clear_record_btn = tk.Button(record_buttons_frame, text="Clear", command=self.clear_recording,
                                     bg=theme["button_bg"], fg=theme["button_fg"],
                                     relief=tk.RAISED, bd=1, width=10)
        clear_record_btn.pack(side=tk.LEFT, padx=5)
        
        # ========== CONFIGURATION MANAGER ==========
        config_frame = tk.LabelFrame(main_container, text=" Configuration Manager ", font=('Arial', 10, 'bold'),
                                     bg=theme["frame_bg"], fg=theme["frame_fg"], padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_top = tk.Frame(config_frame, bg=theme["frame_bg"])
        config_top.pack(fill=tk.X, pady=5)
        
        tk.Label(config_top, text="Config:", bg=theme["frame_bg"], fg=theme["frame_fg"]).pack(side=tk.LEFT, padx=(0, 5))
        self.config_combo = ttk.Combobox(config_top, state="readonly", width=20)
        self.config_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.config_combo.bind('<<ComboboxSelected>>', self.on_config_select)
        
        load_btn = tk.Button(config_top, text="Load", command=self.load_config,
                            bg=theme["button_bg"], fg=theme["button_fg"],
                            relief=tk.RAISED, bd=1, width=8)
        load_btn.pack(side=tk.LEFT, padx=2)
        
        save_btn = tk.Button(config_top, text="Save", command=self.save_config_dialog,
                            bg=theme["button_bg"], fg=theme["button_fg"],
                            relief=tk.RAISED, bd=1, width=8)
        save_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = tk.Button(config_top, text="Delete", command=self.delete_config,
                              bg=theme["button_bg"], fg=theme["button_fg"],
                              relief=tk.RAISED, bd=1, width=8)
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        # ========== СТАТУС БАР ==========
        status_frame = tk.Frame(main_container, bg=theme["status_bg"], relief=tk.SUNKEN, bd=1)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = tk.Label(status_frame, text="● STOPPED", bg=theme["status_bg"], fg='red',
                                     anchor='w', padx=5, font=('Arial', 9, 'bold'))
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.clicks_label = tk.Label(status_frame, text="Clicks: 0", bg=theme["status_bg"], fg=theme["fg"],
                                     anchor='e', padx=5, font=('Arial', 9))
        self.clicks_label.pack(side=tk.RIGHT)
        
        # Нижний статус бар
        bottom_status = tk.Frame(main_container, bg=theme["bg"])
        bottom_status.pack(fill=tk.X, pady=(5, 0))
        
        self.pos_label = tk.Label(bottom_status, text="Mouse position: ---", bg=theme["bg"], fg=theme["fg"],
                                  anchor='w', font=('Arial', 8))
        self.pos_label.pack(side=tk.LEFT)
        
        self.config_label = tk.Label(bottom_status, text=f"Config: {self.config['name']}", bg=theme["bg"], fg=theme["fg"],
                                     anchor='e', font=('Arial', 8))
        self.config_label.pack(side=tk.RIGHT)
        
        # Инициализация состояния полей
        self.on_location_change()
    
    def on_location_change(self):
        """Обработка изменения типа позиции"""
        theme = self.themes[self.current_theme]
        if self.location_type.get() == "Pick":
            self.x_entry.config(state=tk.NORMAL)
            self.y_entry.config(state=tk.NORMAL)
        else:
            self.x_entry.config(state=tk.DISABLED)
            self.y_entry.config(state=tk.DISABLED)
        self.update_config()
    
    def update_config(self, event=None):
        """Обновление текущего конфига из интерфейса"""
        self.config.update({
            'hours': self.hours_var.get(),
            'mins': self.mins_var.get(),
            'secs': self.secs_var.get(),
            'milliseconds': self.ms_var.get(),
            'mouse_button': self.mouse_button.get(),
            'click_type': self.click_type.get(),
            'location_type': self.location_type.get(),
            'fixed_x': self.x_var.get(),
            'fixed_y': self.y_var.get(),
            'theme': self.current_theme
        })
    
    def get_interval_seconds(self):
        """Получение интервала в секундах"""
        total = (self.config['hours'] * 3600) + (self.config['mins'] * 60) + self.config['secs'] + (self.config['milliseconds'] / 1000.0)
        return max(total, 0.001)
    
    def load_config_list(self):
        """Загрузка списка сохранённых конфигов"""
        configs = []
        if os.path.exists(self.config_dir):
            for file in os.listdir(self.config_dir):
                if file.endswith('.json'):
                    configs.append(file.replace('.json', ''))
        
        self.config_combo['values'] = configs
        if configs:
            self.config_combo.set(configs[0])
            self.load_config_by_name(configs[0])
        else:
            # Создаём конфиг по умолчанию
            self.save_config("Default")
    
    def on_config_select(self, event):
        """Обработка выбора конфига из списка"""
        name = self.config_combo.get()
        if name:
            self.load_config_by_name(name)
    
    def load_config_by_name(self, name):
        """Загрузка конфига по имени"""
        file_path = os.path.join(self.config_dir, f"{name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
                self.config['name'] = name
                self.current_theme = self.config.get('theme', 'base')
                self.apply_config_to_ui()
                self.current_config_file = file_path
                self.config_label.config(text=f"Config: {name}")
                
                # Меняем тему если нужно
                if self.current_theme != self.config.get('theme', 'base'):
                    self.change_theme(self.current_theme)
    
    def apply_config_to_ui(self):
        """Применение конфига к интерфейсу"""
        self.hours_var.set(self.config.get('hours', 0))
        self.mins_var.set(self.config.get('mins', 0))
        self.secs_var.set(self.config.get('secs', 0))
        self.ms_var.set(self.config.get('milliseconds', 100))
        self.mouse_button.set(self.config.get('mouse_button', 'Left'))
        self.click_type.set(self.config.get('click_type', 'Single'))
        self.location_type.set(self.config.get('location_type', 'Current'))
        self.x_var.set(self.config.get('fixed_x', 0))
        self.y_var.set(self.config.get('fixed_y', 0))
        self.on_location_change()
        self.update_config()
    
    def save_config_dialog(self):
        """Диалог сохранения конфига"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Configuration")
        dialog.geometry("350x150")
        dialog.resizable(False, False)
        dialog.configure(bg=self.themes[self.current_theme]["bg"])
        
        tk.Label(dialog, text="Configuration name:", bg=self.themes[self.current_theme]["bg"],
                fg=self.themes[self.current_theme]["fg"], font=('Arial', 10)).pack(pady=20)
        name_var = tk.StringVar(value=self.config_combo.get() or "Default")
        name_entry = tk.Entry(dialog, textvariable=name_var, width=30,
                             bg=self.themes[self.current_theme]["entry_bg"],
                             fg=self.themes[self.current_theme]["fg"],
                             relief=tk.SUNKEN, bd=1)
        name_entry.pack(pady=5)
        
        def save():
            new_name = name_var.get().strip()
            if new_name:
                self.save_config(new_name)
                dialog.destroy()
                self.load_config_list()
                self.config_combo.set(new_name)
        
        tk.Button(dialog, text="Save", command=save, bg='#4CAF50', fg='white',
                 relief=tk.RAISED, bd=1, width=10).pack(pady=10)
    
    def save_config(self, name):
        """Сохранение конфига в файл"""
        self.update_config()
        self.config['name'] = name
        self.config['saved_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.config['theme'] = self.current_theme
        
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        file_path = os.path.join(self.config_dir, f"{name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        
        messagebox.showinfo("Success", f"Configuration '{name}' saved!")
        self.config_label.config(text=f"Config: {name}")
    
    def load_config(self):
        """Загрузка выбранного конфига"""
        name = self.config_combo.get()
        if name:
            self.load_config_by_name(name)
            messagebox.showinfo("Success", f"Configuration '{name}' loaded!")
    
    def delete_config(self):
        """Удаление текущего конфига"""
        name = self.config_combo.get()
        if not name or name == "Default":
            messagebox.showwarning("Warning", "Cannot delete Default config!")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete configuration '{name}'?"):
            file_path = os.path.join(self.config_dir, f"{name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                messagebox.showinfo("Success", f"Configuration '{name}' deleted!")
                self.load_config_list()
    
    def pick_location(self):
        """Выбор позиции клика"""
        self.root.iconify()
        self.root.update()
        
        # Показываем сообщение
        msg = tk.Toplevel(self.root)
        msg.title("Pick Location")
        msg.geometry("300x100")
        msg.configure(bg=self.themes[self.current_theme]["bg"])
        tk.Label(msg, text="Move mouse to desired position...\nWaiting 2 seconds...",
                bg=self.themes[self.current_theme]["bg"], fg=self.themes[self.current_theme]["fg"],
                font=('Arial', 10)).pack(expand=True)
        
        self.root.after(2000, lambda: self.capture_position(msg))
    
    def capture_position(self, msg_window):
        """Захват позиции мыши"""
        x, y = pyautogui.position()
        self.x_var.set(x)
        self.y_var.set(y)
        self.update_config()
        msg_window.destroy()
        self.root.deiconify()
        messagebox.showinfo("Position picked", f"Position saved: X={x}, Y={y}")
    
    def get_click_position(self):
        """Получение позиции для клика"""
        if self.config['location_type'] == "Current":
            return pyautogui.position()
        else:
            return (self.config['fixed_x'], self.config['fixed_y'])
    
    def start_clicker(self):
        """Запуск автокликера"""
        if self.running:
            return
        
        self.running = True
        self.clicks_count = 0
        self.clicks_label.config(text="Clicks: 0")
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="● RUNNING", fg='green')
        
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
    
    def stop_clicker(self):
        """Остановка автокликера"""
        self.running =