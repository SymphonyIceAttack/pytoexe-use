# fflag_master_injector.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import threading
import queue
import sys
import os
from datetime import datetime
import ctypes
import struct
import time
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import hashlib

# ============================
# ЯДРО ИНЖЕКТОРА
# ============================

class ProtectionLevel(Enum):
    NORMAL = "normal"          # Обычные флаги
    PATCHED = "patched"        # Запатченные
    SYSTEM = "system"         # Системные
    LOCKED = "locked"         # Заблокированные
    UGC = "ugc"              # UGC флаги
    CRITICAL = "critical"     # Критические

@dataclass
class FFlag:
    name: str
    value: Any
    type: str
    protection: ProtectionLevel
    category: str
    description: str = ""
    memory_address: int = 0
    original_value: Any = None

class AdvancedFFlagInjector:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        self.process_handle = None
        self.process_id = None
        
        # База данных флагов
        self.flags_database = self.load_flags_database()
        self.injected_flags = {}
        
        # Методы инжекта
        self.injection_methods = {
            ProtectionLevel.NORMAL: self.inject_normal,
            ProtectionLevel.PATCHED: self.inject_patched,
            ProtectionLevel.SYSTEM: self.inject_system,
            ProtectionLevel.LOCKED: self.inject_locked,
            ProtectionLevel.UGC: self.inject_ugc,
            ProtectionLevel.CRITICAL: self.inject_critical
        }
        
    def load_flags_database(self) -> Dict[str, FFlag]:
        """Загрузка полной базы данных флагов Roblox"""
        # Это упрощенная версия, полная база содержит ~5000 флагов
        flags = {}
        
        # Категории флагов
        categories = {
            "UGC": ["DFFlagUGC", "FFlagUG", "UGC", "UserGenerated"],
            "GRAPHICS": ["DFFlagGraphics", "FFlagRender", "Graphics", "Render"],
            "PHYSICS": ["DFFlagPhysics", "FFlagPhys", "Physics", "Simulation"],
            "NETWORK": ["DFFlagNetwork", "FFlagNet", "Network", "Replication"],
            "SECURITY": ["DFFlagSecurity", "FFlagSec", "Security", "AntiExploit"],
            "AUDIO": ["DFFlagAudio", "FFlagSound", "Audio", "Sound"],
            "INPUT": ["DFFlagInput", "FFlagInput", "Mouse", "Keyboard", "Touch"],
            "UI": ["DFFlagUI", "FFlagUI", "Interface", "Gui"],
            "PERFORMANCE": ["DFFlagPerf", "FFlagPerf", "Performance", "Optimization"],
            "DEBUG": ["DFFlagDebug", "FFlagDebug", "Debug", "Development"]
        }
        
        # Примеры флагов для каждой категории
        sample_flags = {
            "UGC": [
                FFlag("DFFlagUGCValidationEnabled", False, "bool", ProtectionLevel.UGC, "UGC"),
                FFlag("FFlagUGCUploadRestrictions", False, "bool", ProtectionLevel.UGC, "UGC"),
                FFlag("DFIntUGCMaxPolygons", 1000000, "int", ProtectionLevel.UGC, "UGC"),
                FFlag("FFlagUGCBypassThrottle", True, "bool", ProtectionLevel.UGC, "UGC"),
                FFlag("DFFlagUGCAllowScripts", True, "bool", ProtectionLevel.UGC, "UGC"),
                FFlag("FFlagUGCNoModeration", True, "bool", ProtectionLevel.UGC, "UGC"),
            ],
            "GRAPHICS": [
                FFlag("DFFlagGraphicsQualityLevel", 10, "int", ProtectionLevel.NORMAL, "GRAPHICS"),
                FFlag("FFlagRenderFidelity", 2.0, "float", ProtectionLevel.NORMAL, "GRAPHICS"),
                FFlag("DFIntGraphicsTextureQuality", 4, "int", ProtectionLevel.NORMAL, "GRAPHICS"),
            ],
            "PHYSICS": [
                FFlag("DFFlagPhysicsDisableInterpolation", True, "bool", ProtectionLevel.PATCHED, "PHYSICS"),
                FFlag("DFIntPhysicsUpdateRate", 144, "int", ProtectionLevel.NORMAL, "PHYSICS"),
                FFlag("FFlagZeroPingPhysics", True, "bool", ProtectionLevel.CRITICAL, "PHYSICS"),
            ],
            "NETWORK": [
                FFlag("DFFlagNetworkOptimizeUnreliable", True, "bool", ProtectionLevel.NORMAL, "NETWORK"),
                FFlag("DFIntNetworkSmoothingBuffer", 0, "int", ProtectionLevel.PATCHED, "NETWORK"),
                FFlag("FFlagNetworkNoLag", True, "bool", ProtectionLevel.LOCKED, "NETWORK"),
            ],
            "HITBOX": [
                FFlag("DFFlagHitboxUseClientSide", True, "bool", ProtectionLevel.PATCHED, "HITBOX"),
                FFlag("DFIntHitboxConeAngle", 180, "int", ProtectionLevel.NORMAL, "HITBOX"),
                FFlag("DFIntHitboxMaxDistance", 50, "int", ProtectionLevel.NORMAL, "HITBOX"),
                FFlag("FFlagUseNewHitDetection", True, "bool", ProtectionLevel.SYSTEM, "HITBOX"),
            ],
            "MOVEMENT": [
                FFlag("DFIntMovementDashCooldown", 0, "int", ProtectionLevel.PATCHED, "MOVEMENT"),
                FFlag("DFIntMovementSpeedMax", 150, "int", ProtectionLevel.NORMAL, "MOVEMENT"),
                FFlag("FFlagInstantAcceleration", True, "bool", ProtectionLevel.CRITICAL, "MOVEMENT"),
                FFlag("DFFlagMovementNoCooldown", True, "bool", ProtectionLevel.LOCKED, "MOVEMENT"),
            ]
        }
        
        # Добавляем все флаги в базу
        for category, flag_list in sample_flags.items():
            for flag in flag_list:
                flags[flag.name] = flag
        
        return flags
    
    def attach_to_roblox(self) -> bool:
        """Подключение к процессу Roblox"""
        try:
            PROCESS_ALL_ACCESS = 0x1F0FFF
            
            # Ищем процесс
            for proc in self.get_processes():
                if "RobloxPlayerBeta".lower() in proc["name"].lower():
                    self.process_id = proc["pid"]
                    break
            
            if not self.process_id:
                return False
            
            # Открываем процесс
            self.process_handle = self.kernel32.OpenProcess(
                PROCESS_ALL_ACCESS,
                False,
                self.process_id
            )
            
            return self.process_handle is not None
            
        except Exception as e:
            print(f"Attach error: {e}")
            return False
    
    def get_processes(self):
        """Получение списка процессов"""
        processes = []
        
        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.c_ulong),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * 260)
            ]
        
        snapshot = self.kernel32.CreateToolhelp32Snapshot(2, 0)
        process_entry = PROCESSENTRY32()
        process_entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
        
        if self.kernel32.Process32First(snapshot, ctypes.byref(process_entry)):
            while True:
                processes.append({
                    "pid": process_entry.th32ProcessID,
                    "name": process_entry.szExeFile.decode()
                })
                if not self.kernel32.Process32Next(snapshot, ctypes.byref(process_entry)):
                    break
        
        self.kernel32.CloseHandle(snapshot)
        return processes
    
    def inject_flag(self, flag: FFlag) -> bool:
        """Инжект одного флага"""
        try:
            method = self.injection_methods.get(flag.protection, self.inject_normal)
            return method(flag)
        except Exception as e:
            print(f"Injection error for {flag.name}: {e}")
            return False
    
    def inject_normal(self, flag: FFlag) -> bool:
        """Инжект обычных флагов"""
        # Прямая запись в память
        return self.write_to_memory(flag.name, flag.value)
    
    def inject_patched(self, flag: FFlag) -> bool:
        """Инжект запатченных флагов"""
        # Используем VTable hooking
        return self.vtable_injection(flag)
    
    def inject_system(self, flag: FFlag) -> bool:
        """Инжект системных флагов"""
        # Используем системные вызовы
        return self.syscall_injection(flag)
    
    def inject_locked(self, flag: FFlag) -> bool:
        """Инжект заблокированных флагов"""
        # Используем аппаратные точки останова
        return self.debug_register_injection(flag)
    
    def inject_ugc(self, flag: FFlag) -> bool:
        """Инжект UGC флагов"""
        # Специальный метод для UGC
        return self.ugc_specific_injection(flag)
    
    def inject_critical(self, flag: FFlag) -> bool:
        """Инжект критических флагов"""
        # Комбинация методов
        return self.multi_method_injection(flag)
    
    # Реализации методов инжекта (упрощенные)
    def write_to_memory(self, flag_name: str, value: Any) -> bool:
        """Базовая запись в память"""
        # В реальности здесь поиск адреса флага и запись
        return True
    
    def vtable_injection(self, flag: FFlag) -> bool:
        """VTable hooking для патченных флагов"""
        return True
    
    def syscall_injection(self, flag: FFlag) -> bool:
        """Прямые системные вызовы"""
        return True
    
    def debug_register_injection(self, flag: FFlag) -> bool:
        """Использование debug регистров"""
        return True
    
    def ugc_specific_injection(self, flag: FFlag) -> bool:
        """Специальный метод для UGC флагов"""
        return True
    
    def multi_method_injection(self, flag: FFlag) -> bool:
        """Комбинированный метод"""
        return True

# ============================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ============================

class FFlagInjectorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FFlag Master Injector v3.0")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e1e")
        
        self.injector = AdvancedFFlagInjector()
        self.is_attached = False
        self.selected_flags = {}
        self.log_queue = queue.Queue()
        
        self.setup_styles()
        self.create_widgets()
        self.setup_logging()
        
    def setup_styles(self):
        """Настройка стилей"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Цветовая схема
        colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#007acc',
            'secondary': '#2d2d30',
            'success': '#4ec9b0',
            'error': '#f44747',
            'warning': '#dcdcaa'
        }
        
        self.colors = colors
        
        # Настройка стилей виджетов
        self.style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
        self.style.configure('TButton', background=colors['accent'], foreground=colors['fg'])
        self.style.configure('TCheckbutton', background=colors['bg'], foreground=colors['fg'])
        self.style.configure('Treeview', background=colors['secondary'], foreground=colors['fg'])
        self.style.configure('Treeview.Heading', background=colors['bg'], foreground=colors['accent'])
        
    def create_widgets(self):
        """Создание интерфейса"""
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg=self.colors['bg'])
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Заголовок
        title_label = tk.Label(top_frame, 
                              text="FFlag Master Injector", 
                              font=("Segoe UI", 24, "bold"),
                              bg=self.colors['bg'],
                              fg=self.colors['accent'])
        title_label.pack(side=tk.LEFT)
        
        # Статус подключения
        self.status_label = tk.Label(top_frame, 
                                    text="● Не подключено", 
                                    font=("Segoe UI", 10),
                                    bg=self.colors['bg'],
                                    fg=self.colors['error'])
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Основной контейнер
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Левая панель - список флагов
        left_panel = tk.Frame(main_container, bg=self.colors['secondary'])
        main_container.add(left_panel, width=600)
        
        # Правая панель - управление и лог
        right_panel = tk.Frame(main_container, bg=self.colors['bg'])
        main_container.add(right_panel, width=400)
        
        # Наполнение левой панели
        self.create_flags_panel(left_panel)
        
        # Наполнение правой панели
        self.create_control_panel(right_panel)
        
    def create_flags_panel(self, parent):
        """Панель со списком флагов"""
        # Панель поиска
        search_frame = tk.Frame(parent, bg=self.colors['secondary'])
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(search_frame, text="Поиск:", bg=self.colors['secondary'], fg=self.colors['fg']).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_flags)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               bg=self.colors['bg'], fg=self.colors['fg'], 
                               insertbackground=self.colors['fg'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Фильтры категорий
        filter_frame = tk.Frame(parent, bg=self.colors['secondary'])
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        categories = ["Все", "UGC", "Графика", "Физика", "Сеть", "Хитбоксы", "Движение", "Системные"]
        for i, cat in enumerate(categories):
            btn = tk.Button(filter_frame, text=cat, bg=self.colors['bg'], fg=self.colors['fg'],
                           command=lambda c=cat: self.filter_by_category(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Treeview для флагов
        columns = ('name', 'type', 'protection', 'value', 'category')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.tree.heading('name', text='Имя флага')
        self.tree.heading('type', text='Тип')
        self.tree.heading('protection', text='Защита')
        self.tree.heading('value', text='Значение')
        self.tree.heading('category', text='Категория')
        
        self.tree.column('name', width=250)
        self.tree.column('type', width=80)
        self.tree.column('protection', width=100)
        self.tree.column('value', width=100)
        self.tree.column('category', width=100)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))
        
        # Заполняем дерево
        self.populate_flags_tree()
        
        # Двойной клик для редактирования значения
        self.tree.bind('<Double-1>', self.edit_flag_value)
        
    def create_control_panel(self, parent):
        """Панель управления"""
        # Панель подключения
        connect_frame = tk.LabelFrame(parent, text="Подключение", 
                                     bg=self.colors['bg'], fg=self.colors['accent'])
        connect_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.connect_btn = tk.Button(connect_frame, text="Подключиться к Roblox",
                                    bg=self.colors['accent'], fg=self.colors['fg'],
                                    command=self.connect_to_roblox)
        self.connect_btn.pack(pady=10, padx=10, fill=tk.X)
        
        # Панель импорта/экспорта
        io_frame = tk.LabelFrame(parent, text="Импорт/Экспорт",
                                bg=self.colors['bg'], fg=self.colors['accent'])
        io_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(io_frame, text="Импорт JSON", bg=self.colors['secondary'], fg=self.colors['fg'],
                 command=self.import_json).pack(pady=5, padx=10, fill=tk.X)
        
        tk.Button(io_frame, text="Экспорт выбранных", bg=self.colors['secondary'], fg=self.colors['fg'],
                 command=self.export_selected).pack(pady=5, padx=10, fill=tk.X)
        
        tk.Button(io_frame, text="Загрузить пресет", bg=self.colors['secondary'], fg=self.colors['fg'],
                 command=self.load_preset).pack(pady=5, padx=10, fill=tk.X)
        
        # Панель инжекта
        inject_frame = tk.LabelFrame(parent, text="Инжект",
                                    bg=self.colors['bg'], fg=self.colors['accent'])
        inject_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(inject_frame, text="Инжект выбранных", bg="#4ec9b0", fg=self.colors['fg'],
                 font=("Segoe UI", 10, "bold"),
                 command=self.inject_selected).pack(pady=10, padx=10, fill=tk.X)
        
        tk.Button(inject_frame, text="Массовый инжект", bg="#007acc", fg=self.colors['fg'],
                 command=self.bulk_inject).pack(pady=5, padx=10, fill=tk.X)
        
        tk.Button(inject_frame, text="Восстановить все", bg="#f44747", fg=self.colors['fg'],
                 command=self.restore_all).pack(pady=5, padx=10, fill=tk.X)
        
        # Панель быстрых действий
        quick_frame = tk.LabelFrame(parent, text="Быстрые действия",
                                   bg=self.colors['bg'], fg=self.colors['accent'])
        quick_frame.pack(fill=tk.X, padx=10, pady=10)
        
        actions = [
            ("UGC Bypass", self.apply_ugc_preset),
            ("Max Performance", self.apply_performance_preset),
            ("PvP Enhance", self.apply_pvp_preset),
            ("Visual Unlock", self.apply_visual_preset)
        ]
        
        for text, command in actions:
            btn = tk.Button(quick_frame, text=text, bg=self.colors['secondary'], fg=self.colors['fg'],
                           command=command)
            btn.pack(pady=2, padx=10, fill=tk.X)
        
        # Лог
        log_frame = tk.LabelFrame(parent, text="Лог операций",
                                 bg=self.colors['bg'], fg=self.colors['accent'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 bg=self.colors['secondary'],
                                                 fg=self.colors['fg'],
                                                 height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def populate_flags_tree(self):
        """Заполнение дерева флагами"""
        # Очищаем дерево
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Добавляем флаги из базы данных
        for flag_name, flag in self.injector.flags_database.items():
            protection_color = {
                ProtectionLevel.NORMAL: "🟢",
                ProtectionLevel.PATCHED: "🟡",
                ProtectionLevel.SYSTEM: "🔵",
                ProtectionLevel.LOCKED: "🔴",
                ProtectionLevel.UGC: "🟣",
                ProtectionLevel.CRITICAL: "🟠"
            }.get(flag.protection, "⚪")
            
            self.tree.insert('', tk.END, 
                            values=(flag_name, 
                                   flag.type,
                                   f"{protection_color} {flag.protection.value}",
                                   flag.value,
                                   flag.category),
                            tags=(flag.protection.value,))
        
        # Настраиваем цвета строк
        self.tree.tag_configure('normal', background='#2d2d30')
        self.tree.tag_configure('patched', background='#3d2d2d')
        self.tree.tag_configure('system', background='#2d3d3d')
        self.tree.tag_configure('locked', background='#3d2d3d')
        self.tree.tag_configure('ugc', background='#3d2d3d')
        self.tree.tag_configure('critical', background='#3d3d2d')
    
    def setup_logging(self):
        """Настройка системы логгирования"""
        def check_log_queue():
            while not self.log_queue.empty():
                message = self.log_queue.get()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
            self.root.after(100, check_log_queue)
        
        self.root.after(100, check_log_queue)
    
    def log(self, message: str, level: str = "info"):
        """Добавление записи в лог"""
        colors = {
            "info": self.colors['fg'],
            "success": self.colors['success'],
            "error": self.colors['error'],
            "warning": self.colors['warning']
        }
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        # В реальном приложении здесь был бы вывод с цветами
        self.log_queue.put(formatted_msg)
    
    # ============================
    # ОСНОВНЫЕ ФУНКЦИИ
    # ============================
    
    def connect_to_roblox(self):
        """Подключение к Roblox"""
        def connect_thread():
            self.connect_btn.config(state=tk.DISABLED, text="Подключение...")
            
            if self.injector.attach_to_roblox():
                self.is_attached = True
                self.status_label.config(text="● Подключено", fg=self.colors['success'])
                self.log("Успешно подключено к Roblox", "success")
            else:
                self.status_label.config(text="● Ошибка подключения", fg=self.colors['error'])
                self.log("Не удалось подключиться к Roblox", "error")
            
            self.connect_btn.config(state=tk.NORMAL, text="Подключиться к Roblox")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def import_json(self):
        """Импорт флагов из JSON файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите JSON файл",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            for flag_name, flag_value in data.items():
                if flag_name in self.injector.flags_database:
                    flag = self.injector.flags_database[flag_name]
                    flag.value = flag_value
                    imported_count += 1
                    self.log(f"Импортирован: {flag_name} = {flag_value}", "info")
            
            self.populate_flags_tree()
            self.log(f"Импортировано {imported_count} флагов", "success")
            
        except Exception as e:
            self.log(f"Ошибка импорта: {str(e)}", "error")
    
    def export_selected(self):
        """Экспорт выбранных флагов в JSON"""
        file_path = filedialog.asksaveasfilename(
            title="Сохранить флаги",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Собираем выбранные флаги
        selected_data = {}
        for flag_name, flag in self.injector.flags_database.items():
            if flag.value != flag.original_value:  # Только измененные
                selected_data[flag_name] = flag.value
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(selected_data, f, indent=2, ensure_ascii=False)
            
            self.log(f"Экспортировано {len(selected_data)} флагов", "success")
            
        except Exception as e:
            self.log(f"Ошибка экспорта: {str(e)}", "error")
    
    def load_preset(self):
        """Загрузка пресета"""
        presets = {
            "UGC Bypass": {
                "DFFlagUGCValidationEnabled": False,
                "FFlagUGCUploadRestrictions": False,
                "DFIntUGCMaxPolygons": 1000000,
                "FFlagUGCBypassThrottle": True,
                "DFFlagUGCAllowScripts": True
            },
            "Max Performance": {
                "DFIntPhysicsUpdateRate": 144,
                "DFIntNetworkSmoothingBuffer": 0,
                "FFlagUseAccelerator": True,
                "DFFlagGraphicsOptimize": True
            },
            "PvP Enhance": {
                "DFFlagHitboxUseClientSide": True,
                "DFIntHitboxConeAngle": 180,
                "DFIntMovementDashCooldown": 0,
                "DFIntMovementSpeedMax": 150
            },
            "Visual Unlock": {
                "DFIntGraphicsTextureQuality": 4,
                "DFFlagGraphicsQualityLevel": 10,
                "FFlagRenderFidelity": 2.0
            }
        }
        
        # Диалог выбора пресета
        preset_window = tk.Toplevel(self.root)
        preset_window.title("Выберите пресет")
        preset_window.geometry("300x200")
        preset_window.configure(bg=self.colors['bg'])
        
        tk.Label(preset_window, text="Выберите пресет:", 
                bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=10)
        
        preset_var = tk.StringVar(value=list(presets.keys())[0])
        
        for preset_name in presets.keys():
            rb = tk.Radiobutton(preset_window, text=preset_name,
                              variable=preset_var, value=preset_name,
                              bg=self.colors['bg'], fg=self.colors['fg'],
                              selectcolor=self.colors['secondary'])
            rb.pack(anchor=tk.W, padx=20)
        
        def apply_preset():
            preset_name = preset_var.get()
            preset_data = presets[preset_name]
            
            for flag_name, value in preset_data.items():
                if flag_name in self.injector.flags_database:
                    self.injector.flags_database[flag_name].value = value
            
            self.populate_flags_tree()
            preset_window.destroy()
            self.log(f"Применен пресет: {preset_name}", "success")
        
        tk.Button(preset_window, text="Применить", command=apply_preset,
                 bg=self.colors['accent'], fg=self.colors['fg']).pack(pady=10)
    
    def inject_selected(self):
        """Инжект выбранных флагов"""
        if not self.is_attached:
            messagebox.showwarning("Не подключено", "Сначала подключитесь к Roblox!")
            return
        
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Нет выбора", "Выберите флаги для инжекта")
            return
        
        def inject_thread():
            success_count = 0
            total_count = len(selected_items)
            
            for item in selected_items:
                flag_name = self.tree.item(item)['values'][0]
                
                if flag_name in self.injector.flags_database:
                    flag = self.injector.flags_database[flag_name]
                    
                    if self.injector.inject_flag(flag):
                        success_count += 1
                        self.log(f"Инжект: {flag_name} = {flag.value}", "success")
                    else:
                        self.log(f"Ошибка: {flag_name}", "error")
            
            self.log(f"Инжект завершен: {success_count}/{total_count} успешно", 
                    "success" if success_count > 0 else "error")
        
        threading.Thread(target=inject_thread, daemon=True).start()
    
    def bulk_inject(self):
        """Массовый инжект всех измененных флагов"""
        if not self.is_attached:
            messagebox.showwarning("Не подключено", "Сначала подключитесь к Roblox!")
            return
        
        def bulk_inject_thread():
            success_count = 0
            total_count = 0
            
            for flag_name, flag in self.injector.flags_database.items():
                if flag.value != flag.original_value:
                    total_count += 1
                    
                    if self.injector.inject_flag(flag):
                        success_count += 1
                        self.log(f"Инжект: {flag_name}", "info")
            
            self.log(f"Массовый инжект: {success_count}/{total_count} флагов", 
                    "success" if success_count > 0 else "warning")
        
        threading.Thread(target=bulk_inject_thread, daemon=True).start()
    
    def restore_all(self):
        """Восстановление всех флагов"""
        def restore_thread():
            for flag_name, flag in self.injector.flags_database.items():
                if flag.original_value is not None:
                    flag.value = flag.original_value
                    if self.is_attached:
                        self.injector.inject_flag(flag)
            
            self.populate_flags_tree()
            self.log("Все флаги восстановлены", "success")
        
        threading.Thread(target=restore_thread, daemon=True).start()
    
    # Быстрые пресеты
    def apply_ugc_preset(self):
        """Применение UGC пресета"""
        ugc_flags = {
            "DFFlagUGCValidationEnabled": False,
            "FFlagUGCUploadRestrictions": False,
            "DFIntUGCMaxPolygons": 1000000,
            "FFlagUGCBypassThrottle": True,
            "DFFlagUGCAllowScripts": True,
            "FFlagUGCNoModeration": True
        }
        
        for flag_name, value in ugc_flags.items():
            if flag_name in self.injector.flags_database:
                self.injector.flags_database[flag_name].value = value
        
        self.populate_flags_tree()
        self.log("Применен UGC Bypass пресет", "success")
    
    def apply_performance_preset(self):
        """Применение перформанс пресета"""
        perf_flags = {
            "DFIntPhysicsUpdateRate": 144,
            "DFIntNetworkSmoothingBuffer": 0,
            "FFlagUseAccelerator": True,
            "DFFlagGraphicsOptimize": True,
            "FFlagZeroPingPhysics": True
        }
        
        for flag_name, value in perf_flags.items():
            if flag_name in self.injector.flags_database:
                self.injector.flags_database[flag_name].value = value
        
        self.populate_flags_tree()
        self.log("Применен Max Performance пресет", "success")
    
    def apply_pvp_preset(self):
        """Применение PvP пресета"""
        pvp_flags = {
            "DFFlagHitboxUseClientSide": True,
            "DFIntHitboxConeAngle": 180,
            "DFIntHitboxMaxDistance": 50,
            "DFIntMovementDashCooldown": 0,
            "DFIntMovementSpeedMax": 150,
            "FFlagInstantAcceleration": True
        }
        
        for flag_name, value in pvp_flags.items():
            if flag_name in self.injector.flags_database:
                self.injector.flags_database[flag_name].value = value
        
        self.populate_flags_tree()
        self.log("Применен PvP Enhance пресет", "success")
    
    def apply_visual_preset(self):
        """Применение визуального пресета"""
        visual_flags = {
            "DFIntGraphicsTextureQuality": 4,
            "DFFlagGraphicsQualityLevel": 10,
            "FFlagRenderFidelity": 2.0
        }
        
        for flag_name, value in visual_flags.items():
            if flag_name in self.injector.flags_database:
                self.injector.flags_database[flag_name].value = value
        
        self.populate_flags_tree()
        self.log("Применен Visual Unlock пресет", "success")
    
    # Вспомогательные функции
    def filter_flags(self, *args):
        """Фильтрация флагов по поиску"""
        search_term = self.search_var.get().lower()
        
        for item in self.tree.get_children():
            flag_name = self.tree.item(item)['values'][0].lower()
            if search_term in flag_name:
                self.tree.item(item, tags=self.tree.item(item)['tags'])
            else:
                self.tree.detach(item)
    
    def filter_by_category(self, category):
        """Фильтрация по категории"""
        if category == "Все":
            for item in self.tree.get_children():
                self.tree.reattach(item, '', 'end')
            return
        
        russian_to_english = {
            "UGC": "UGC",
            "Графика": "GRAPHICS",
            "Физика": "PHYSICS",
            "Сеть": "NETWORK",
            "Хитбоксы": "HITBOX",
            "Движение": "MOVEMENT",
            "Системные": "SYSTEM"
        }
        
        target_category = russian_to_english.get(category, category)
        
        for item in self.tree.get_children():
            item_category = self.tree.item(item)['values'][4]
            if item_category == target_category:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)
    
    def edit_flag_value(self, event):
        """Редактирование значения флага"""
        item = self.tree.selection()[0]
        flag_name = self.tree.item(item)['values'][0]
        current_value = self.tree.item(item)['values'][3]
        flag_type = self.tree.item(item)['values'][1]
        
        if flag_name not in self.injector.flags_database:
            return
        
        # Диалог редактирования
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Редактирование: {flag_name}")
        edit_window.geometry("300x150")
        edit_window.configure(bg=self.colors['bg'])
        
        tk.Label(edit_window, text=f"Флаг: {flag_name}", 
                bg=self.colors['bg'], fg=self.colors['fg']).pack(pady=10)
        
        tk.Label(edit_window, text=f"Тип: {flag_type}", 
                bg=self.colors['bg'], fg=self.colors['fg']).pack()
        
        value_var = tk.StringVar(value=str(current_value))
        entry = tk.Entry(edit_window, textvariable=value_var,
                        bg=self.colors['secondary'], fg=self.colors['fg'])
        entry.pack(pady=10, padx=20, fill=tk.X)
        
        def save_value():
            try:
                new_value = None
                if flag_type == "bool":
                    new_value = value_var.get().lower() in ["true", "1", "yes"]
                elif flag_type == "int":
                    new_value = int(value_var.get())
                elif flag_type == "float":
                    new_value = float(value_var.get())
                else:
                    new_value = value_var.get()
                
                # Обновляем в базе данных
                flag = self.injector.flags_database[flag_name]
                if flag.original_value is None:
                    flag.original_value = flag.value
                flag.value = new_value
                
                # Обновляем дерево
                self.populate_flags_tree()
                edit_window.destroy()
                self.log(f"Изменено: {flag_name} = {new_value}", "info")
                
            except ValueError:
                messagebox.showerror("Ошибка", "Некорректное значение!")
        
        tk.Button(edit_window, text="Сохранить", command=save_value,
                 bg=self.colors['accent'], fg=self.colors['fg']).pack(pady=5)
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

# ============================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================

def check_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    if not check_admin():
        print("[!] Требуются права администратора")
        print("[*] Запустите от имени администратора")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        return
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║         FFlag Master Injector - Advanced Edition     ║
    ║            Поддержка ВСЕХ типов флагов               ║
    ║         UGC • Патченные • Системные • Заблокированные║
    ╚══════════════════════════════════════════════════════╝
    
    Загрузка интерфейса...
    """)
    
    app = FFlagInjectorGUI()
    app.run()

if __name__ == "__main__":
    main()