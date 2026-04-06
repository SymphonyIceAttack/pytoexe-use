# -*- coding: utf-8 -*-
import subprocess
import sys
import ctypes
import os
import threading
import tkinter as tk
from tkinter import messagebox
import platform

WINDOW_WIDTH = 400  # Увеличил ширину для новых кнопок
BASE_WINDOW_HEIGHT = 320  # Увеличил высоту для новых кнопок

# Отключаем DPI awareness для совместимости с Win7 32bit
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Запрос прав администратора при запуске"""
    try:
        script_path = os.path.abspath(sys.argv[0])
        
        params = f'"{script_path}"'
        for arg in sys.argv[1:]:
            params += f' "{arg}"'
        
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        
        if result < 32:
            error_codes = {
                0: "Операционной системе не хватает памяти или ресурсов",
                2: "Файл не найден",
                3: "Путь не найден",
                5: "Доступ запрещен",
                8: "Недостаточно памяти",
                10: "Неправильная версия Windows",
                11: "Приложение несовместимо",
                31: "Нет связанной программы"
            }
            error_msg = error_codes.get(result, f"Неизвестная ошибка (код {result})")
            print(f"Ошибка: {error_msg}")
            sys.exit(1)
        
        sys.exit(0)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        sys.exit(1)


# Если нет прав администратора, сразу запрашиваем
if not is_admin():
    run_as_admin()


class CustomWindow(tk.Toplevel):
    def __init__(self, parent, title="", width=WINDOW_WIDTH, height=BASE_WINDOW_HEIGHT):
        super().__init__(parent)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")
        
        try:
            self.attributes('-alpha', 0.95)
            # Окно всегда поверх всех окон
            self.attributes('-topmost', True)
        except:
            pass
            
        self.overrideredirect(True)
        
        self._width = width
        self._height = height
        
        self.create_titlebar(title)
        
        self.content_frame = tk.Frame(self, bg="#1e1e1e")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))
        
    def center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self._width) // 2
        y = (screen_height - self._height) // 2
        self.geometry(f"+{x}+{y}")
        
    def create_titlebar(self, title_text):
        titlebar = tk.Frame(self, bg="#2d2d30", height=24)
        titlebar.pack(fill=tk.X, padx=2, pady=(2, 0))
        
        title_label = tk.Label(titlebar, text=title_text, 
                              bg="#2d2d30", fg="#ffffff",
                              font=("Segoe UI", 9))
        title_label.pack(side=tk.LEFT, padx=(8, 0))
        
        button_frame = tk.Frame(titlebar, bg="#2d2d30")
        button_frame.pack(side=tk.RIGHT, padx=(0, 5))
        
        # Кнопка закрытия
        close_btn = tk.Button(button_frame, text="✕", command=self.destroy_window,
                             bg="#2d2d30", fg="#ffffff", activebackground="#c42b1c",
                             activeforeground="#ffffff", bd=0, width=2,
                             font=("Segoe UI", 9))
        close_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        titlebar.bind("<ButtonPress-1>", self.start_move)
        titlebar.bind("<B1-Motion>", self.on_move)
        title_label.bind("<ButtonPress-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.on_move)
        
    def start_move(self, event):
        self._x = event.x
        self._y = event.y
        
    def on_move(self, event):
        deltax = event.x - self._x
        deltay = event.y - self._y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")
        
    def destroy_window(self):
        self.destroy()
        self.quit()


class CustomButton(tk.Canvas):
    def __init__(self, parent, text="", command=None, width=50, height=22, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bd=0, bg="#2d2d30")
        
        self.command = command
        self.default_bg = kwargs.get('bg', "#3e3e42")
        self.hover_bg = kwargs.get('hover_bg', "#505050")
        self.click_bg = kwargs.get('click_bg', "#007acc")
        self.text_color = kwargs.get('text_color', "#ffffff")
        self.state = tk.NORMAL
        
        self.rect = self.create_rounded_rect(2, 2, width-2, height-2, 5, fill=self.default_bg)
        self.text_id = self.create_text(width//2, height//2, text=text, 
                                       fill=self.text_color, font=("Segoe UI", 9))
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)
    
    def on_enter(self, event):
        if self.state != tk.DISABLED:
            self.itemconfig(self.rect, fill=self.hover_bg)
        
    def on_leave(self, event):
        if self.state != tk.DISABLED:
            self.itemconfig(self.rect, fill=self.default_bg)
        
    def on_click(self, event):
        if self.state != tk.DISABLED:
            self.itemconfig(self.rect, fill=self.click_bg)
        
    def on_release(self, event):
        if self.state != tk.DISABLED:
            self.itemconfig(self.rect, fill=self.default_bg)
            if self.command:
                self.command()
    
    def config(self, **kwargs):
        if 'state' in kwargs:
            self.state = kwargs['state']
            if self.state == tk.DISABLED:
                self.itemconfig(self.rect, fill="#2d2d30")
                self.itemconfig(self.text_id, fill="#888888")
            else:
                self.itemconfig(self.rect, fill=self.default_bg)
                self.itemconfig(self.text_id, fill=self.text_color)


class FirewallApp:
    def __init__(self, root):
        self.root = root
        self.window = CustomWindow(root, "Настройка ТС ПИоТ от evgen11112 Ver. 1.0", WINDOW_WIDTH, BASE_WINDOW_HEIGHT)
        self.window.center_window()
        
        self.ports = [50063]
        self.protocols = ["tcp", "udp"]
        self.directions = [
            {"name": "входящие", "dir": "in"},
            {"name": "исходящие", "dir": "out"}
        ]
        
        # Пути к сертификатам
        self.ca_cert_path = r"C:\ProgramData\ESP\ESM\um\ca.crt"
        self.server_cert_path = r"C:\ProgramData\ESP\ESM\um\server.crt"
        
        self.system_arch = platform.machine()
        self.update_timer = None
        self._setup_ui()
        self._check_admin_status()
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _check_admin_status(self):
        if is_admin():
            self._update_status("Администратор", "#6a9955")
        else:
            self._update_status("Нет прав", "#f48771")
    
    def _setup_ui(self):
        # Поле ввода портов
        ports_frame = tk.Frame(self.window.content_frame, bg="#1e1e1e")
        ports_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        tk.Label(ports_frame, text="Порты (через пробел):",
                bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 9)).pack(anchor=tk.W)
        
        self.ports_entry = tk.Entry(ports_frame, bg="#3e3e42", fg="#ffffff",
                                   insertbackground="#ffffff", font=("Segoe UI", 10))
        self.ports_entry.pack(fill=tk.X, pady=(2, 0))
        self.ports_entry.insert(0, "50063")
        
        # Привязываем события для автоматического обновления
        self.ports_entry.bind('<KeyRelease>', self._on_ports_change)
        self.ports_entry.bind('<FocusOut>', self._on_ports_change)
        
        # Информация
        info_frame = tk.Frame(self.window.content_frame, bg="#252526", relief=tk.FLAT, bd=1)
        info_frame.pack(fill=tk.X, padx=15, pady=5)
        
        tk.Label(info_frame, text="TCP / UDP | входящие / исходящие",
                bg="#252526", fg="#cccccc", font=("Segoe UI", 9)).pack(anchor=tk.W, padx=10, pady=5)
        
        separator1 = tk.Frame(self.window.content_frame, bg="#3e3e42", height=1)
        separator1.pack(fill=tk.X, padx=15, pady=5)
        
        # Кнопки брандмауэра
        firewall_label = tk.Label(self.window.content_frame, text="Брандмауэр Windows",
                                 bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 9, "bold"))
        firewall_label.pack(anchor=tk.W, padx=15, pady=(5, 0))
        
        btn_frame1 = tk.Frame(self.window.content_frame, bg="#1e1e1e")
        btn_frame1.pack(fill=tk.X, padx=15, pady=5)
        
        # Все кнопки брандмауэра зеленые
        self.add_btn = CustomButton(btn_frame1, text="Добавить порты", 
                                   command=self._add_ports_thread,
                                   width=110, height=28,
                                   bg="#6a9955", hover_bg="#7fb06d", click_bg="#5a8b4a")
        self.add_btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        self.remove_btn = CustomButton(btn_frame1, text="Удалить порты", 
                                      command=self._remove_rules_thread,
                                      width=110, height=28,
                                      bg="#6a9955", hover_bg="#7fb06d", click_bg="#5a8b4a")
        self.remove_btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        self.open_btn = CustomButton(btn_frame1, text="Брандмауэр", 
                                    command=self._open_firewall,
                                    width=110, height=28,
                                    bg="#6a9955", hover_bg="#7fb06d", click_bg="#5a8b4a")
        self.open_btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        separator2 = tk.Frame(self.window.content_frame, bg="#3e3e42", height=1)
        separator2.pack(fill=tk.X, padx=15, pady=5)
        
        # Кнопки сертификатов
        cert_label = tk.Label(self.window.content_frame, text="Сертификаты",
                             bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 9, "bold"))
        cert_label.pack(anchor=tk.W, padx=15, pady=(5, 0))
        
        btn_frame2 = tk.Frame(self.window.content_frame, bg="#1e1e1e")
        btn_frame2.pack(fill=tk.X, padx=15, pady=5)
        
        # Все кнопки сертификатов тоже зеленые
        self.install_ca_btn = CustomButton(btn_frame2, text="Установить CA", 
                                          command=self._install_ca_cert_thread,
                                          width=110, height=28,
                                          bg="#6a9955", hover_bg="#7fb06d", click_bg="#5a8b4a")
        self.install_ca_btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        self.install_server_btn = CustomButton(btn_frame2, text="Установить Server", 
                                              command=self._install_server_cert_thread,
                                              width=110, height=28,
                                              bg="#6a9955", hover_bg="#7fb06d", click_bg="#5a8b4a")
        self.install_server_btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        self.check_certs_btn = CustomButton(btn_frame2, text="Проверить", 
                                           command=self._check_certificates,
                                           width=110, height=28,
                                           bg="#6a9955", hover_bg="#7fb06d", click_bg="#5a8b4a")
        self.check_certs_btn.pack(side=tk.LEFT, padx=2, expand=True)
        
        separator3 = tk.Frame(self.window.content_frame, bg="#3e3e42", height=1)
        separator3.pack(fill=tk.X, padx=15, pady=5)
        
        # СТАТУС НАД КНОПКАМИ
        status_frame = tk.Frame(self.window.content_frame, bg="#1e1e1e")
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        
        # Метка "Статус:"
        tk.Label(status_frame, text="Статус:", 
                bg="#1e1e1e", fg="#cccccc", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.status_label = tk.Label(status_frame, text="Готов", 
                                    bg="#1e1e1e", fg="#888888", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Прогресс (порты) справа
        self.progress_label = tk.Label(status_frame, text="", 
                                      bg="#1e1e1e", fg="#6a9955", font=("Segoe UI", 9))
        self.progress_label.pack(side=tk.RIGHT)
    
    def _check_certificates(self):
        """Проверка наличия файлов сертификатов"""
        ca_exists = os.path.exists(self.ca_cert_path)
        server_exists = os.path.exists(self.server_cert_path)
        
        if ca_exists and server_exists:
            self._update_status("✓ Файлы сертификатов найдены", "#6a9955")
            self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
        elif ca_exists:
            self._update_status("⚠ Найден только CA сертификат", "#ffcc00")
            self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
        elif server_exists:
            self._update_status("⚠ Найден только Server сертификат", "#ffcc00")
            self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
        else:
            self._update_status("✗ Файлы сертификатов не найдены", "#f48771")
            self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
    
    def _install_certificate(self, cert_path, store_name):
        """Установка сертификата в указанное хранилище"""
        if not os.path.exists(cert_path):
            return False, f"Файл не найден: {cert_path}"
        
        try:
            # Используем certutil для установки сертификата
            command = f'certutil -addstore "{store_name}" "{cert_path}"'
            result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='cp866')
            
            if result.returncode == 0:
                return True, "Успешно установлен"
            else:
                return False, f"Ошибка: {result.stderr}"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def _install_ca_cert_thread(self):
        if not is_admin():
            self._update_status("Ошибка: нужны права администратора!", "#f48771")
            return
        
        thread = threading.Thread(target=self._install_ca_cert_work, daemon=True)
        thread.start()
    
    def _install_ca_cert_work(self):
        self._disable_cert_buttons(True)
        self._update_status("Установка CA сертификата...", "#6a9955")
        
        success, message = self._install_certificate(self.ca_cert_path, "Root")
        
        if success:
            self._update_status(f"✓ CA сертификат установлен", "#6a9955")
        else:
            self._update_status(f"✗ Ошибка CA: {message[:50]}", "#f48771")
        
        self._disable_cert_buttons(False)
        self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
    
    def _install_server_cert_thread(self):
        if not is_admin():
            self._update_status("Ошибка: нужны права администратора!", "#f48771")
            return
        
        thread = threading.Thread(target=self._install_server_cert_work, daemon=True)
        thread.start()
    
    def _install_server_cert_work(self):
        self._disable_cert_buttons(True)
        self._update_status("Установка Server сертификата...", "#6a9955")
        
        success, message = self._install_certificate(self.server_cert_path, "My")
        
        if success:
            self._update_status(f"✓ Server сертификат установлен", "#6a9955")
        else:
            self._update_status(f"✗ Ошибка Server: {message[:50]}", "#f48771")
        
        self._disable_cert_buttons(False)
        self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
    
    def _disable_cert_buttons(self, disabled):
        """Включение/выключение кнопок сертификатов"""
        state = tk.DISABLED if disabled else tk.NORMAL
        self.install_ca_btn.config(state=state)
        self.install_server_btn.config(state=state)
        self.check_certs_btn.config(state=state)
    
    def _on_ports_change(self, event=None):
        """Автоматическое обновление портов при изменении текста"""
        if self.update_timer:
            self.window.after_cancel(self.update_timer)
        self.update_timer = self.window.after(500, self._update_ports_from_entry)
    
    def _update_ports_from_entry(self):
        """Обновление списка портов из поля ввода"""
        try:
            ports_text = self.ports_entry.get().strip()
            
            if not ports_text:
                self.ports = []
                self._update_ports_display()
                return
            
            # Разделяем по пробелам
            port_list = []
            for p in ports_text.split():
                if p.isdigit():
                    port = int(p)
                    if 1 <= port <= 65535:
                        port_list.append(port)
            
            if port_list:
                # Удаляем дубликаты
                port_list = list(dict.fromkeys(port_list))
                self.ports = port_list
                self._update_ports_display()
                self._update_status(f"Портов: {len(self.ports)}", "#6a9955")
            else:
                if ports_text:
                    self._update_status("Ошибка в портах", "#f48771")
                    
        except Exception as e:
            self._update_status(f"Ошибка", "#f48771")
    
    def _update_ports_display(self):
        """Обновление отображения портов"""
        if self.ports:
            ports_str = ' '.join(str(p) for p in self.ports[:5])
            if len(self.ports) > 5:
                ports_str += f"... (+{len(self.ports)-5})"
            self.progress_label.config(text=ports_str, fg="#6a9955")
        else:
            self.progress_label.config(text="нет портов", fg="#f48771")
    
    def _open_firewall(self):
        """Открытие оснастки брандмауэра Windows wf.msc"""
        try:
            subprocess.Popen('wf.msc', shell=True)
            self._update_status("Брандмауэр открыт", "#6a9955")
            self.window.after(2000, lambda: self._update_status("Готов", "#888888"))
        except Exception as e:
            self._update_status("Ошибка открытия", "#f48771")
    
    def _update_status(self, message, color="#ffffff"):
        self.status_label.config(text=message, fg=color)
        self.window.update()
    
    def _update_progress(self, text, color="#6a9955"):
        self.progress_label.config(text=text, fg=color)
        self.window.update()
    
    def _run_netsh_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding='cp866'
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except Exception as e:
            return -1, "", str(e)
    
    def _get_rule_name(self, port, protocol, direction):
        return f"PIOT_{port}_{protocol}_{direction}"
    
    def _check_rule_exists(self, port, protocol, direction):
        """Проверка существования правила"""
        rule_name = self._get_rule_name(port, protocol, direction)
        command = f'netsh advfirewall firewall show rule name="{rule_name}"'
        returncode, stdout, _ = self._run_netsh_command(command)
        return returncode == 0
    
    def _add_rule(self, port, protocol, direction):
        rule_name = self._get_rule_name(port, protocol, direction)
        command = f'netsh advfirewall firewall add rule name="{rule_name}" dir={direction} action=allow protocol={protocol} localport={port} enable=yes'
        returncode, _, _ = self._run_netsh_command(command)
        return returncode == 0
    
    def _remove_rule(self, port, protocol, direction):
        rule_name = self._get_rule_name(port, protocol, direction)
        command = f'netsh advfirewall firewall delete rule name="{rule_name}"'
        returncode, _, _ = self._run_netsh_command(command)
        return returncode == 0
    
    def _get_missing_rules(self):
        """Получение списка недостающих правил"""
        missing = []
        for direction_info in self.directions:
            direction = direction_info["dir"]
            for port in self.ports:
                for protocol in self.protocols:
                    if not self._check_rule_exists(port, protocol, direction):
                        missing.append((port, protocol, direction))
        return missing
    
    def _add_ports_thread(self):
        if not is_admin():
            self._update_status("Ошибка: нет прав!", "#f48771")
            return
        
        if not self.ports:
            self._update_status("Ошибка: порты не указаны", "#f48771")
            return
        
        thread = threading.Thread(target=self._add_ports_work, daemon=True)
        thread.start()
    
    def _add_ports_work(self):
        self.add_btn.config(state=tk.DISABLED)
        self.remove_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        
        # Проверяем существующие правила
        self._update_status("Проверка существующих правил...", "#6a9955")
        missing_rules = self._get_missing_rules()
        
        total = len(self.ports) * len(self.protocols) * len(self.directions)
        existing = total - len(missing_rules)
        
        if existing > 0:
            self._update_status(f"Найдено {existing} существующих правил", "#6a9955")
            # Небольшая пауза для чтения сообщения
            import time
            time.sleep(1)
        
        if not missing_rules:
            self._update_status(f"✓ Все правила уже существуют ({total}/{total})", "#6a9955")
            self._update_progress(f"{total}/{total}", "#6a9955")
            self.add_btn.config(state=tk.NORMAL)
            self.remove_btn.config(state=tk.NORMAL)
            self.open_btn.config(state=tk.NORMAL)
            # Сброс через 3 секунды
            self.window.after(3000, lambda: self._update_status("Готов", "#888888"))
            self.window.after(3000, lambda: self._update_progress("", "#6a9955"))
            return
        
        # Добавляем только недостающие правила
        self._update_status(f"Добавление {len(missing_rules)} правил...", "#6a9955")
        success = 0
        
        for port, protocol, direction in missing_rules:
            if self._add_rule(port, protocol, direction):
                success += 1
            self.window.update()
        
        result_text = f"{existing + success}/{total}"
        
        if success == len(missing_rules):
            self._update_status(f"✓ Добавлено {success} правил", "#6a9955")
            self._update_progress(result_text, "#6a9955")
        else:
            self._update_status(f"⚠ Добавлено {success}/{len(missing_rules)} правил", "#ffcc00")
            self._update_progress(result_text, "#ffcc00")
        
        self.add_btn.config(state=tk.NORMAL)
        self.remove_btn.config(state=tk.NORMAL)
        self.open_btn.config(state=tk.NORMAL)
        
        # Сброс прогресса через 4 секунды
        self.window.after(4000, lambda: self._update_progress("", "#6a9955"))
        self.window.after(4000, lambda: self._update_status("Готов", "#888888"))
    
    def _remove_rules_thread(self):
        if not is_admin():
            self._update_status("Ошибка: нет прав!", "#f48771")
            return
        
        if not self.ports:
            self._update_status("Ошибка: порты не указаны", "#f48771")
            return
        
        thread = threading.Thread(target=self._remove_rules_work, daemon=True)
        thread.start()
    
    def _remove_rules_work(self):
        self.add_btn.config(state=tk.DISABLED)
        self.remove_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        
        total = len(self.ports) * len(self.protocols) * len(self.directions)
        removed = 0
        
        self._update_status("Удаление правил...", "#6a9955")
        
        for direction_info in self.directions:
            direction = direction_info["dir"]
            
            for port in self.ports:
                for protocol in self.protocols:
                    if self._remove_rule(port, protocol, direction):
                        removed += 1
                    
                    self.window.update()
        
        result_text = f"{removed}/{total}"
        
        if removed == total:
            self._update_status(f"✓ Удалено {removed} правил", "#6a9955")
        else:
            self._update_status(f"⚠ Удалено {removed}/{total} правил", "#ffcc00")
        
        self._update_progress(result_text, "#6a9955")
        
        self.add_btn.config(state=tk.NORMAL)
        self.remove_btn.config(state=tk.NORMAL)
        self.open_btn.config(state=tk.NORMAL)
        
        # Сброс через 4 секунды
        self.window.after(4000, lambda: self._update_progress("", "#6a9955"))
        self.window.after(4000, lambda: self._update_status("Готов", "#888888"))
    
    def _on_closing(self):
        self.window.destroy_window()
        self.root.quit()
        self.root.destroy()
        os._exit(0)


def main():
    # Скрываем консоль
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    root = tk.Tk()
    root.withdraw()
    
    app = FirewallApp(root)
    root.protocol("WM_DELETE_WINDOW", app._on_closing)
    
    try:
        root.mainloop()
    except:
        pass
    finally:
        os._exit(0)


if __name__ == "__main__":
    main()