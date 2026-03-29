import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
from time import sleep, time
import keyboard
from mss import mss
from PIL import Image
from ctypes import windll
import gc
from collections import deque
import hashlib
from datetime import datetime, timedelta
import tempfile
import ctypes

# Trial system constants - БЕСКОНЕЧНАЯ ВЕРСИЯ
TRIAL_DAYS = 36500
TRIAL_FILE = "trial.dat"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_hwid():
    try:
        import platform
        import uuid
        system_info = f"{platform.machine()}{platform.processor()}{uuid.getnode()}"
        hwid = hashlib.sha256(system_info.encode()).hexdigest()[:16]
        return hwid
    except:
        return "default_hwid"


class UltimateTriggerbotGUI:
    def __init__(self):
        self.is_admin_user = is_admin()
        self.root = tk.Tk()
        self.root.title("🚀 ZxCycleAPI ULTIMATE - EXTREME PERFORMANCE")
        self.root.geometry("850x700")
        self.root.resizable(False, False)

        self.performance_stats = {
            'scan_times': deque(maxlen=200),
            'click_times': deque(maxlen=100),
            'total_scans': 0,
            'successful_detections': 0,
            'peak_performance': float('inf')
        }

        self.last_gc_time = time()
        self.shutdown_event = threading.Event()
        self.stats_lock = threading.Lock()

        self.setup_windows_api()
        self.setup_dark_theme()

        self.is_running = False
        self.triggerbot_thread = None
        self.stats_thread = None
        self.config = self.load_config()

        self.setup_ui()
        self.start_performance_monitoring()
        self.log_message("🚀 ULTIMATE TRIGGERBOT LOADED - БЕСКОНЕЧНАЯ ВЕРСИЯ")

    def setup_windows_api(self):
        self.user32 = windll.user32
        try:
            windll.shcore.SetProcessDpiAwareness(2)
        except:
            pass

    def setup_dark_theme(self):
        style = ttk.Style(self.root)
        bg_color = "#0d1117"
        fg_color = "#f0f6fc"
        accent_color = "#58a6ff"

        style.theme_use('clam')
        style.configure(".", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=accent_color, foreground="#ffffff", padding=10,
                        font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TButton", background=[("active", "#1f6feb")])
        style.configure("TEntry", fieldbackground="#21262d", foreground=fg_color, padding=8, insertcolor=fg_color)
        style.configure("TCombobox", fieldbackground="#21262d", foreground=fg_color, selectbackground=accent_color)
        style.configure("TLabelframe", background=bg_color, foreground=accent_color, font=("Segoe UI", 12, "bold"),
                        bordercolor="#30363d")
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_color)
        style.configure("Horizontal.TScale", background=bg_color, troughcolor="#21262d", sliderrelief="flat",
                        sliderthickness=20, bordercolor=accent_color)
        self.root.configure(bg=bg_color)

    def load_config(self):
        default_config = {
            "hotkey": "alt", "highlight_color": "purple", "mode": "hold",
            "tolerance": 15, "zone": 8, "ultra_mode": True, "reaction_time": 1
        }
        try:
            if os.path.exists("gui_config.json"):
                with open("gui_config.json", "r") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            return default_config
        except:
            return default_config

    def save_config(self):
        try:
            with open("gui_config.json", "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить конфигурацию: {e}")

    def setup_ui(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ttk.Label(header_frame, text="🚀 ZxCycleAPI ULTIMATE",
                                font=("Segoe UI", 26, "bold"), foreground="#58a6ff")
        title_label.pack(side="left")

        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side="right")

        trial_label = ttk.Label(info_frame, text="ЛИЦЕНЗИЯ: ∞ (Бесконечно)",
                                font=("Segoe UI", 10, "bold"), foreground="#3fb950")
        trial_label.pack()

        admin_status = "🔐 ADMIN" if self.is_admin_user else "⚠️ USER"
        admin_color = "#58a6ff" if self.is_admin_user else "#f85149"
        admin_label = ttk.Label(info_frame, text=admin_status, font=("Segoe UI", 9, "bold"), foreground=admin_color)
        admin_label.pack()

        self.create_settings_frame()
        self.create_performance_frame()
        self.create_control_frame()
        self.create_log_frame()

    def create_settings_frame(self):
        settings_frame = ttk.Labelframe(self.root, text=" ⚙️ ULTRA SETTINGS ")
        settings_frame.pack(fill="x", padx=20, pady=10, ipady=10)

        settings_grid = tk.Frame(settings_frame, bg="#0d1117")
        settings_grid.pack(fill="x", padx=15, pady=15)

        tk.Label(settings_grid, text="🔥 Горячая клавиша:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.hotkey_var = tk.StringVar(value=self.config["hotkey"])
        hotkey_entry = ttk.Entry(settings_grid, textvariable=self.hotkey_var, width=15, font=("Segoe UI", 11))
        hotkey_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(settings_grid, text="🎯 Цвет цели:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=2, sticky="w", padx=10, pady=10)
        self.color_var = tk.StringVar(value=self.config["highlight_color"])
        color_menu = ttk.Combobox(settings_grid, textvariable=self.color_var,
                                  values=["red", "purple", "blue", "green", "yellow", "orange", "pink"],
                                  width=12, state="readonly", font=("Segoe UI", 11))
        color_menu.grid(row=0, column=3, padx=10, pady=10)

        tk.Label(settings_grid, text="⚡ Режим:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.mode_var = tk.StringVar(value=self.config["mode"])
        mode_menu = ttk.Combobox(settings_grid, textvariable=self.mode_var,
                                 values=["hold", "toggle", "auto"], width=12, state="readonly", font=("Segoe UI", 11))
        mode_menu.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(settings_grid, text="🔍 Толерантность:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 11, "bold")).grid(row=1, column=2, sticky="w", padx=10, pady=10)
        self.tolerance_var = tk.IntVar(value=self.config["tolerance"])
        tolerance_slider = ttk.Scale(settings_grid, from_=1, to=50, variable=self.tolerance_var,
                                     orient='horizontal', length=120, command=self.update_tolerance_label)
        tolerance_slider.grid(row=1, column=3, padx=10, pady=10)
        self.tolerance_label = tk.Label(settings_grid, text=str(self.config["tolerance"]),
                                        bg="#0d1117", fg="#58a6ff", font=("Segoe UI", 11, "bold"))
        self.tolerance_label.grid(row=1, column=4, padx=5, pady=10)

        tk.Label(settings_grid, text="📡 Зона сканирования:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.zone_var = tk.IntVar(value=self.config["zone"])
        zone_slider = ttk.Scale(settings_grid, from_=3, to=30, variable=self.zone_var,
                                orient='horizontal', length=120, command=self.update_zone_label)
        zone_slider.grid(row=2, column=1, padx=10, pady=10)
        self.zone_label = tk.Label(settings_grid, text=str(self.config["zone"]),
                                   bg="#0d1117", fg="#58a6ff", font=("Segoe UI", 11, "bold"))
        self.zone_label.grid(row=2, column=2, padx=5, pady=10)

        tk.Label(settings_grid, text="⚡ Время реакции (мс):", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 11, "bold")).grid(row=2, column=3, sticky="w", padx=10, pady=10)
        self.reaction_var = tk.IntVar(value=self.config.get("reaction_time", 1))
        reaction_slider = ttk.Scale(settings_grid, from_=1, to=10, variable=self.reaction_var,
                                    orient='horizontal', length=120, command=self.update_reaction_label)
        reaction_slider.grid(row=2, column=4, padx=10, pady=10)
        self.reaction_label = tk.Label(settings_grid, text=str(self.config.get("reaction_time", 1)),
                                       bg="#0d1117", fg="#58a6ff", font=("Segoe UI", 11, "bold"))
        self.reaction_label.grid(row=2, column=5, padx=5, pady=10)

        self.ultra_mode_var = tk.BooleanVar(value=self.config.get("ultra_mode", True))
        ultra_check = tk.Checkbutton(settings_grid, text="🚀 ULTRA MODE (Максимальная производительность)",
                                     variable=self.ultra_mode_var, bg="#0d1117", fg="#3fb950",
                                     selectcolor="#21262d", activebackground="#0d1117", activeforeground="#3fb950",
                                     font=("Segoe UI", 11, "bold"))
        ultra_check.grid(row=3, column=0, columnspan=6, sticky="w", padx=10, pady=15)

    def create_performance_frame(self):
        perf_frame = ttk.Labelframe(self.root, text=" 📊 ULTRA PERFORMANCE MONITOR ")
        perf_frame.pack(fill="x", padx=20, pady=10, ipady=10)

        perf_grid = tk.Frame(perf_frame, bg="#0d1117")
        perf_grid.pack(fill="x", padx=15, pady=15)

        tk.Label(perf_grid, text="⚡ Скорость сканирования:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.scan_speed_label = tk.Label(perf_grid, text="0.0 мс", bg="#0d1117", fg="#3fb950",
                                         font=("Segoe UI", 10, "bold"))
        self.scan_speed_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        tk.Label(perf_grid, text="🎯 Время реакции:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="w", padx=10, pady=5)
        self.reaction_time_label = tk.Label(perf_grid, text="0.0 мс", bg="#0d1117", fg="#3fb950",
                                            font=("Segoe UI", 10, "bold"))
        self.reaction_time_label.grid(row=0, column=3, sticky="w", padx=10, pady=5)

        tk.Label(perf_grid, text="🔍 Всего сканирований:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.total_scans_label = tk.Label(perf_grid, text="0", bg="#0d1117", fg="#58a6ff",
                                          font=("Segoe UI", 10, "bold"))
        self.total_scans_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        tk.Label(perf_grid, text="🎯 Обнаружений:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 10, "bold")).grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self.detections_label = tk.Label(perf_grid, text="0", bg="#0d1117", fg="#3fb950", font=("Segoe UI", 10, "bold"))
        self.detections_label.grid(row=1, column=3, sticky="w", padx=10, pady=5)

        tk.Label(perf_grid, text="🚀 Пиковая производительность:", bg="#0d1117", fg="#f0f6fc",
                 font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.peak_perf_label = tk.Label(perf_grid, text="∞ мс", bg="#0d1117", fg="#f85149",
                                        font=("Segoe UI", 10, "bold"))
        self.peak_perf_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)

    def create_control_frame(self):
        control_frame = ttk.Labelframe(self.root, text=" 🎮 ULTRA CONTROL ")
        control_frame.pack(fill="x", padx=20, pady=10, ipady=10)

        buttons_frame = tk.Frame(control_frame, bg="#0d1117")
        buttons_frame.pack(pady=15)

        self.start_button = ttk.Button(buttons_frame, text="🚀 ЗАПУСТИТЬ ULTRA MODE",
                                       command=self.toggle_triggerbot, width=25)
        self.start_button.pack(side="left", padx=10)

        save_button = ttk.Button(buttons_frame, text="💾 Сохранить", command=self.save_settings, width=15)
        save_button.pack(side="left", padx=10)

        reset_button = ttk.Button(buttons_frame, text="🔄 Сбросить", command=self.reset_settings, width=15)
        reset_button.pack(side="left", padx=10)

        clear_stats_button = ttk.Button(buttons_frame, text="🗑️ Очистить статистику", command=self.clear_stats,
                                        width=20)
        clear_stats_button.pack(side="left", padx=10)

    def create_log_frame(self):
        log_frame = ttk.Labelframe(self.root, text=" 📝 ULTRA LOGS ")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20), ipady=10)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=("Consolas", 9), wrap=tk.WORD,
                                                  bg="#21262d", fg="#f0f6fc", insertbackground="#f0f6fc",
                                                  padx=15, pady=15, selectbackground="#58a6ff",
                                                  selectforeground="#ffffff")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

        clear_button_frame = tk.Frame(log_frame, bg="#0d1117")
        clear_button_frame.pack(fill="x", padx=10, pady=(0, 10))

        clear_logs_button = ttk.Button(clear_button_frame, text="🗑️ Очистить логи", command=self.clear_logs)
        clear_logs_button.pack(side="right")

    def update_tolerance_label(self, value):
        self.tolerance_label.config(text=str(int(float(value))))

    def update_zone_label(self, value):
        self.zone_label.config(text=str(int(float(value))))

    def update_reaction_label(self, value):
        self.reaction_label.config(text=str(int(float(value))))

    def log_message(self, message):
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            lines = int(self.log_text.index('end-1c').split('.')[0])
            if lines > 500:
                self.log_text.delete(1.0, "100.0")

        if threading.current_thread() == threading.main_thread():
            _log()
        else:
            self.root.after(0, _log)

    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log_message("🗑️ Логи очищены")

    def clear_stats(self):
        with self.stats_lock:
            self.performance_stats = {
                'scan_times': deque(maxlen=200),
                'click_times': deque(maxlen=100),
                'total_scans': 0,
                'successful_detections': 0,
                'peak_performance': float('inf')
            }
        self.log_message("📊 Статистика производительности очищена")

    def save_settings(self):
        self.config.update({
            "hotkey": self.hotkey_var.get(),
            "highlight_color": self.color_var.get(),
            "mode": self.mode_var.get(),
            "tolerance": self.tolerance_var.get(),
            "zone": self.zone_var.get(),
            "ultra_mode": self.ultra_mode_var.get(),
            "reaction_time": self.reaction_var.get()
        })
        self.save_config()
        self.log_message("💾 Настройки сохранены")
        messagebox.showinfo("Успех", "⚡ Настройки сохранены!")

    def reset_settings(self):
        if messagebox.askyesno("Подтверждение", "🔄 Сбросить все настройки?"):
            if os.path.exists("gui_config.json"):
                os.remove("gui_config.json")
            self.config = self.load_config()
            self.hotkey_var.set(self.config["hotkey"])
            self.color_var.set(self.config["highlight_color"])
            self.mode_var.set(self.config["mode"])
            self.tolerance_var.set(self.config["tolerance"])
            self.zone_var.set(self.config["zone"])
            self.ultra_mode_var.set(self.config.get("ultra_mode", True))
            self.reaction_var.set(self.config.get("reaction_time", 1))
            self.log_message("🔄 Настройки сброшены")
            messagebox.showinfo("Успех", "🔄 Настройки сброшены!")

    def toggle_triggerbot(self):
        if not self.is_running:
            self.start_triggerbot()
        else:
            self.stop_triggerbot()

    def start_triggerbot(self):
        self.is_running = True
        self.shutdown_event.clear()
        self.start_button.config(text="🛑 ОСТАНОВИТЬ ULTRA MODE")
        self.log_message("🚀 ULTRA TRIGGERBOT АКТИВИРОВАН!")
        self.triggerbot_thread = threading.Thread(target=self.ultra_triggerbot_worker, daemon=True)
        self.triggerbot_thread.start()

    def stop_triggerbot(self):
        self.is_running = False
        self.shutdown_event.set()
        self.start_button.config(text="🚀 ЗАПУСТИТЬ ULTRA MODE")
        self.log_message("🛑 ULTRA TRIGGERBOT ДЕАКТИВИРОВАН")

    def start_performance_monitoring(self):
        self.stats_thread = threading.Thread(target=self.ultra_performance_monitor, daemon=True)
        self.stats_thread.start()

    def ultra_performance_monitor(self):
        while True:
            try:
                if self.shutdown_event.wait(0.5):
                    break
                with self.stats_lock:
                    scan_times = list(self.performance_stats['scan_times'])
                    avg_scan_time = sum(scan_times) / len(scan_times) if scan_times else 0
                    click_times = list(self.performance_stats['click_times'])
                    avg_click_time = sum(click_times) / len(click_times) if click_times else 0
                    total_scans = self.performance_stats['total_scans']
                    detections = self.performance_stats['successful_detections']
                    if scan_times:
                        min_scan_time = min(scan_times)
                        if min_scan_time < self.performance_stats['peak_performance']:
                            self.performance_stats['peak_performance'] = min_scan_time

                def update_ui():
                    self.scan_speed_label.config(text=f"{avg_scan_time:.2f} мс")
                    self.reaction_time_label.config(text=f"{avg_click_time:.2f} мс")
                    self.total_scans_label.config(text=str(total_scans))
                    self.detections_label.config(text=str(detections))
                    peak_text = f"{self.performance_stats['peak_performance']:.2f} мс" if self.performance_stats[
                                                                                              'peak_performance'] != float(
                        'inf') else "∞ мс"
                    self.peak_perf_label.config(text=peak_text)

                self.root.after(0, update_ui)
            except Exception as e:
                print(f"Performance monitor error: {e}")

    def get_color_rgb(self, color_name):
        color_map = {
            "red": (152, 20, 37), "purple": (250, 100, 250), "blue": (0, 100, 255),
            "green": (0, 255, 0), "yellow": (255, 255, 0), "orange": (255, 165, 0), "pink": (255, 192, 203)
        }
        return color_map.get(color_name, (250, 100, 250))

    def ultra_triggerbot_worker(self):
        try:
            hotkey = self.hotkey_var.get()
            color = self.color_var.get()
            mode = self.mode_var.get()
            tolerance = self.tolerance_var.get()
            zone = self.zone_var.get()
            ultra_mode = self.ultra_mode_var.get()
            reaction_time = self.reaction_var.get() / 1000.0

            target_r, target_g, target_b = self.get_color_rgb(color)

            WIDTH = self.user32.GetSystemMetrics(0)
            HEIGHT = self.user32.GetSystemMetrics(1)

            half_zone = zone
            center_x, center_y = WIDTH // 2, HEIGHT // 2
            GRAB_ZONE = {'left': center_x - half_zone, 'top': center_y - half_zone,
                         'width': half_zone * 2, 'height': half_zone * 2}

            self.log_message(f"🚀 ULTRA TRIGGERBOT АКТИВИРОВАН!")
            self.log_message(f"🎯 Цель: {color} | Зона: {zone}px | Толерантность: {tolerance}")
            self.log_message(f"⚡ Горячая клавиша: {hotkey} | Режим: {mode}")

            toggled = False
            sct = mss()
            scan_step = 1 if ultra_mode else 2
            base_delay = 0.0001 if ultra_mode else 0.001

            while self.is_running and not self.shutdown_event.is_set():
                try:
                    scan_start = time()
                    active = False
                    if mode == 'toggle':
                        if keyboard.is_pressed(hotkey):
                            toggled = not toggled
                            self.log_message(f"⚡ Режим переключен: {'🟢 ВКЛ' if toggled else '🔴 ВЫКЛ'}")
                            sleep(0.1)
                        active = toggled
                    elif mode == 'auto':
                        active = True
                    else:
                        active = keyboard.is_pressed(hotkey)

                    if active:
                        detection_start = time()
                        found = self.ultra_scan_and_click(sct, target_r, target_g, target_b,
                                                          tolerance, GRAB_ZONE, scan_step, ultra_mode)
                        if found:
                            click_time = (time() - detection_start) * 1000
                            with self.stats_lock:
                                self.performance_stats['successful_detections'] += 1
                                self.performance_stats['click_times'].append(click_time)
                            if reaction_time > 0:
                                sleep(reaction_time)

                        scan_time = (time() - scan_start) * 1000
                        with self.stats_lock:
                            self.performance_stats['scan_times'].append(scan_time)
                            self.performance_stats['total_scans'] += 1

                        sleep(base_delay)

                        if time() - self.last_gc_time > 60:
                            gc.collect()
                            self.last_gc_time = time()
                except Exception as e:
                    self.log_message(f"❌ Ошибка в ULTRA цикле: {e}")
                    sleep(0.01)
        except Exception as e:
            self.log_message(f"💥 Критическая ошибка ULTRA режима: {e}")
        finally:
            if 'sct' in locals():
                sct.close()

    def ultra_scan_and_click(self, sct, target_r, target_g, target_b, tolerance, grab_zone, scan_step, ultra_mode):
        try:
            img = sct.grab(grab_zone)
            pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            width, height = pil_img.size

            if ultra_mode:
                center_x, center_y = width // 2, height // 2
                max_radius = min(center_x, center_y)
                for radius in range(0, max_radius, scan_step):
                    for offset in range(-radius, radius + 1, scan_step):
                        positions = [(center_x + offset, center_y - radius),
                                     (center_x + offset, center_y + radius),
                                     (center_x - radius, center_y + offset),
                                     (center_x + radius, center_y + offset)]
                        for x, y in positions:
                            if 0 <= x < width and 0 <= y < height:
                                try:
                                    pixel = pil_img.getpixel((x, y))
                                    if isinstance(pixel, tuple) and len(pixel) >= 3:
                                        r, g, b = pixel[0], pixel[1], pixel[2]
                                        if (abs(r - target_r) <= tolerance and
                                                abs(g - target_g) <= tolerance and
                                                abs(b - target_b) <= tolerance):
                                            self.ultra_click()
                                            return True
                                except:
                                    continue
            else:
                for y in range(0, height, scan_step):
                    for x in range(0, width, scan_step):
                        try:
                            pixel = pil_img.getpixel((x, y))
                            if isinstance(pixel, tuple) and len(pixel) >= 3:
                                r, g, b = pixel[0], pixel[1], pixel[2]
                                if (abs(r - target_r) <= tolerance and
                                        abs(g - target_g) <= tolerance and
                                        abs(b - target_b) <= tolerance):
                                    self.ultra_click()
                                    return True
                        except:
                            continue
            return False
        except Exception as e:
            self.log_message(f"❌ Ошибка ULTRA сканирования: {e}")
            return False

    def ultra_click(self):
        try:
            hwnd = self.user32.GetForegroundWindow()
            if hwnd:
                self.user32.PostMessageW(hwnd, 0x0201, 0x0001, 0)
                self.user32.PostMessageW(hwnd, 0x0202, 0x0000, 0)
                return True
        except:
            return False

    def cleanup(self):
        self.shutdown_event.set()
        self.is_running = False
        if self.triggerbot_thread and self.triggerbot_thread.is_alive():
            self.triggerbot_thread.join(timeout=3)
        if self.stats_thread and self.stats_thread.is_alive():
            self.stats_thread.join(timeout=3)
        gc.collect()

    def run(self):
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.log_message("🚀 ULTRA TRIGGERBOT готов к работе!")
            self.root.mainloop()
        except Exception as e:
            self.log_message(f"❌ Ошибка ULTRA GUI: {e}")
        finally:
            self.cleanup()

    def on_closing(self):
        if self.is_running:
            self.stop_triggerbot()
        self.log_message("👋 ULTRA TRIGGERBOT завершает работу...")
        self.cleanup()
        self.root.destroy()


if __name__ == "__main__":
    try:
        app = UltimateTriggerbotGUI()
        app.run()
    except Exception as e:
        print(f"ULTRA TRIGGERBOT ERROR: {e}")
        input("Press Enter to exit...")