# il2cpp_editor.py
# Полноценный редактор IL2CPP-сборок
# Работает с играми на Unity IL2CPP

import os
import sys
import json
import struct
import tempfile
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ---------- СТРУКТУРЫ ДЛЯ IL2CPP ----------
@dataclass
class IL2CPPClass:
    name: str
    namespace: str
    method_count: int = 0
    field_count: int = 0
    methods: List[Dict] = field(default_factory=list)
    fields: List[Dict] = field(default_factory=list)
    offset: int = 0

@dataclass
class IL2CPPMethod:
    name: str
    signature: str
    rva: int  # относительный виртуальный адрес
    code_size: int
    is_static: bool = False

@dataclass
class IL2CPPField:
    name: str
    type: str
    offset: int
    is_static: bool = False

# ---------- ПАРСЕР IL2CPP ----------
class IL2CPPParser:
    def __init__(self, game_path: str):
        self.game_path = Path(game_path)
        self.il2cpp_dir = self.game_path / "il2cpp_data"
        self.global_metadata = None
        self.code_regions = []
        self.classes: Dict[str, IL2CPPClass] = {}
        
    def extract_il2cpp_data(self) -> bool:
        """Извлекает IL2CPP данные из игры"""
        # Ищем файлы
        exe_files = list(self.game_path.glob("*.exe"))
        if not exe_files:
            return False
        
        self.exe_path = exe_files[0]
        
        # Создаём папку для извлечения
        self.il2cpp_dir.mkdir(exist_ok=True)
        
        # Извлекаем метаданные (используем il2cppdumper)
        print("[*] Извлечение IL2CPP данных...")
        
        # Проверяем наличие il2cppdumper
        il2cppdumper = shutil.which("Il2CppDumper")
        if not il2cppdumper:
            print("[!] Установи Il2CppDumper: https://github.com/Perfare/Il2CppDumper")
            return False
        
        # Запускаем дампер
        cmd = [
            il2cppdumper,
            str(self.exe_path),
            str(self.game_path / "GameAssembly.dll"),
            str(self.il2cpp_dir)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except:
            return False
        
        # Загружаем дамп
        dump_path = self.il2cpp_dir / "dump.json"
        if not dump_path.exists():
            return False
        
        with open(dump_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._parse_classes(data)
        
        return True
    
    def _parse_classes(self, data: dict):
        """Разбирает структуру классов"""
        for class_data in data.get("classes", []):
            class_name = class_data.get("name", "Unknown")
            namespace = class_data.get("namespace", "")
            full_name = f"{namespace}.{class_name}" if namespace else class_name
            
            cls = IL2CPPClass(
                name=class_name,
                namespace=namespace,
                offset=class_data.get("offset", 0)
            )
            
            # Методы
            for method in class_data.get("methods", []):
                cls.methods.append({
                    "name": method.get("name", "unknown"),
                    "signature": method.get("signature", ""),
                    "rva": method.get("rva", 0),
                    "code_size": method.get("code_size", 0),
                    "is_static": method.get("is_static", False)
                })
            
            # Поля
            for field in class_data.get("fields", []):
                cls.fields.append({
                    "name": field.get("name", "field"),
                    "type": field.get("type", "void"),
                    "offset": field.get("offset", 0),
                    "is_static": field.get("is_static", False)
                })
            
            cls.method_count = len(cls.methods)
            cls.field_count = len(cls.fields)
            self.classes[full_name] = cls

# ---------- ДИЗАССЕМБЛЕР ----------
class IL2CPPDissassembler:
    @staticmethod
    def disassemble_method(il2cpp_dir: Path, method_rva: int, code_size: int) -> str:
        """Дизассемблирует метод в читаемый ASM + псевдокод"""
        code_path = il2cpp_dir / "code.bin"
        if not code_path.exists():
            return "Код не найден"
        
        with open(code_path, 'rb') as f:
            f.seek(method_rva)
            code = f.read(code_size)
        
        # Простейший дизассемблер (для демонстрации)
        output = []
        output.append(f"; Метод: 0x{method_rva:08X}")
        output.append(f"; Размер: {code_size} байт")
        output.append("")
        
        # Декодируем инструкции (упрощённо)
        # В реальности нужен полноценный дизассемблер (Capstone/BeaEngine)
        # Здесь я показываю структуру, а дальше ты можешь подключить Capstone
        
        i = 0
        while i < len(code):
            opcode = code[i]
            if opcode == 0x48:  # REX
                if i + 1 < len(code):
                    output.append(f"  0x{i:04X}:  {code[i:i+2].hex()}  ; REX + {code[i+1]:02X}")
                    i += 2
                else:
                    output.append(f"  0x{i:04X}:  {opcode:02X}")
                    i += 1
            elif opcode == 0xE8:  # CALL
                if i + 4 < len(code):
                    target = int.from_bytes(code[i+1:i+5], 'little')
                    output.append(f"  0x{i:04X}:  E8 {target:08X}  ; CALL 0x{target:08X}")
                    i += 5
                else:
                    i += 1
            elif opcode == 0xC3:  # RET
                output.append(f"  0x{i:04X}:  C3  ; RET")
                i += 1
            else:
                # Пропускаем неизвестные
                i += 1
        
        return '\n'.join(output)

# ---------- GUI ----------
class IL2CPPEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IL2CPP Editor - Unity Modding Tool")
        self.root.geometry("1200x700")
        self.root.configure(bg='#0a0a0a')
        
        # Состояние
        self.game_path = tk.StringVar()
        self.parser = None
        self.selected_class = None
        self.selected_method = None
        self.edited_code = ""
        
        self.setup_styles()
        self.create_widgets()
        
        self.root.resizable(True, True)
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.bg = '#0a0a0a'
        self.fg = '#00ff88'
        self.bg_entry = '#1a1a2e'
        self.bg_button = '#16213e'
        
        style.configure('TFrame', background=self.bg)
        style.configure('TLabel', background=self.bg, foreground=self.fg, font=('Consolas', 10))
        style.configure('TButton', background=self.bg_button, foreground=self.fg, font=('Consolas', 10))
        style.configure('TEntry', fieldbackground=self.bg_entry, foreground=self.fg, insertcolor=self.fg)
        style.configure('TLabelframe', background=self.bg, foreground=self.fg)
        style.configure('TLabelframe.Label', background=self.bg, foreground=self.fg)
    
    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель (выбор игры)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(top_frame, text="Игра:").pack(side=tk.LEFT)
        entry = ttk.Entry(top_frame, textvariable=self.game_path, width=60)
        entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(top_frame, text="Обзор...", command=self.browse_game)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        load_btn = ttk.Button(top_frame, text="Загрузить IL2CPP", command=self.load_game)
        load_btn.pack(side=tk.LEFT, padx=5)
        
        # Основная область (дерево + код)
        mid_frame = ttk.Frame(main_frame)
        mid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель: дерево классов
        left_frame = ttk.LabelFrame(mid_frame, text="Классы", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        self.tree = ttk.Treeview(left_frame, selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_class_select)
        
        # Правая панель: метод + код
        right_frame = ttk.Frame(mid_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Список методов
        methods_frame = ttk.LabelFrame(right_frame, text="Методы", padding=5)
        methods_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.method_listbox = tk.Listbox(methods_frame, height=6, bg='#1a1a2e', fg='#00ff88', font=('Consolas', 9))
        self.method_listbox.pack(fill=tk.X, expand=True)
        self.method_listbox.bind('<<ListboxSelect>>', self.on_method_select)
        
        # Редактор кода
        code_frame = ttk.LabelFrame(right_frame, text="Код (ASM / Псевдокод)", padding=5)
        code_frame.pack(fill=tk.BOTH, expand=True)
        
        self.code_editor = scrolledtext.ScrolledText(
            code_frame,
            bg='#0a0a0a',
            fg='#88ffbb',
            font=('Consolas', 9),
            insertbackground='#00ff88',
            wrap=tk.NONE,
            height=15
        )
        self.code_editor.pack(fill=tk.BOTH, expand=True)
        
        # Панель действий
        actions_frame = ttk.Frame(right_frame)
        actions_frame.pack(fill=tk.X, pady=(5, 0))
        
        apply_btn = ttk.Button(actions_frame, text="Применить изменения", command=self.apply_changes)
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        revert_btn = ttk.Button(actions_frame, text="Отменить", command=self.revert_changes)
        revert_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(actions_frame, text="Сохранить в игру", command=self.save_to_game)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
    
    def browse_game(self):
        """Выбор папки с игрой"""
        folder = filedialog.askdirectory(title="Выберите папку с игрой")
        if folder:
            self.game_path.set(folder)
    
    def load_game(self):
        """Загрузка IL2CPP данных"""
        path = self.game_path.get()
        if not path:
            messagebox.showerror("Ошибка", "Выберите папку с игрой")
            return
        
        self.status_var.set("Загрузка...")
        self.root.update()
        
        try:
            self.parser = IL2CPPParser(path)
            if self.parser.extract_il2cpp_data():
                self.populate_tree()
                self.status_var.set(f"Загружено {len(self.parser.classes)} классов")
            else:
                messagebox.showerror("Ошибка", "Не удалось загрузить IL2CPP данные")
                self.status_var.set("Ошибка загрузки")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self.status_var.set("Ошибка")
    
    def populate_tree(self):
        """Заполнение дерева классов"""
        # Очищаем
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Группировка по пространствам имён
        namespaces = {}
        for full_name, cls in self.parser.classes.items():
            ns = cls.namespace or "Без пространства"
            if ns not in namespaces:
                namespaces[ns] = []
            namespaces[ns].append(cls)
        
        # Добавляем в дерево
        for ns, classes in sorted(namespaces.items()):
            ns_node = self.tree.insert("", "end", text=ns, open=True)
            for cls in sorted(classes, key=lambda x: x.name):
                self.tree.insert(ns_node, "end", text=cls.name, values=(cls,))
    
    def on_class_select(self, event):
        """Выбор класса"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return
        
        self.selected_class = values[0]
        self.populate_methods(self.selected_class)
    
    def populate_methods(self, cls: IL2CPPClass):
        """Заполнение списка методов"""
        self.method_listbox.delete(0, tk.END)
        
        for method in cls.methods:
            prefix = "[static] " if method["is_static"] else ""
            text = f"{prefix}{method['name']} : {method['signature']}"
            self.method_listbox.insert(tk.END, text)
    
    def on_method_select(self, event):
        """Выбор метода"""
        selection = self.method_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if not self.selected_class:
            return
        
        method_data = self.selected_class.methods[index]
        method_rva = method_data.get("rva", 0)
        method_size = method_data.get("code_size", 0)
        
        # Дизассемблируем
        if self.parser and method_rva:
            code = IL2CPPDissassembler.disassemble_method(
                self.parser.il2cpp_dir,
                method_rva,
                method_size
            )
            self.code_editor.delete('1.0', tk.END)
            self.code_editor.insert('1.0', code)
            self.edited_code = code
    
    def apply_changes(self):
        """Применение изменений к коду"""
        new_code = self.code_editor.get('1.0', tk.END).strip()
        if not new_code:
            return
        
        self.edited_code = new_code
        self.status_var.set("Изменения применены (только в редакторе)")
    
    def revert_changes(self):
        """Отмена изменений"""
        if self.selected_method:
            self.on_method_select(None)
    
    def save_to_game(self):
        """Сохранение изменений в игру"""
        if not self.edited_code:
            messagebox.showinfo("Инфо", "Нет изменений для сохранения")
            return
        
        # Здесь логика патчинга бинарника
        # В реальности нужно:
        # 1. Конвертировать изменения в байт-код
        # 2. Найти RVA метода
        # 3. Записать новые инструкции
        # 4. Обновить метаданные (если нужно)
        
        messagebox.showinfo("Инфо", 
            "Сохранение в игру пока в разработке.\n"
            "Для реального патчинга нужно:\n"
            "1. Ассемблировать изменённый код\n"
            "2. Записать в GameAssembly.dll по RVA\n"
            "3. Обновить чек-суммы\n"
            "4. Перепаковать .exe (если нужно)"
        )

# ---------- ТОЧКА ВХОДА ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = IL2CPPEditorApp(root)
    
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()