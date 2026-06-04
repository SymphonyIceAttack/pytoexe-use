import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import shutil
import json
import subprocess
import platform
import sys
from pathlib import Path
from datetime import datetime

# ==================== КОНФИГУРАЦИЯ ====================
# Определяем папку, где находится программа (работает и для .py, и для .exe)
if getattr(sys, 'frozen', False):
    # Запущено как собранный .exe файл
    PROGRAM_DIR = Path(sys.executable).parent
else:
    # Запущено как .py скрипт
    PROGRAM_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Папка для хранения файлов (в той же директории, где программа)
ROOT_DIR = PROGRAM_DIR / "MediaVault"

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'
}
METADATA_FILE = ".mediamanager.json"

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def is_media_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in MEDIA_EXTENSIONS

def get_file_size_str(filepath: Path) -> str:
    size = filepath.stat().st_size
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} ТБ"

def open_file_with_default_app(filepath: Path):
    if platform.system() == "Windows":
        os.startfile(filepath)
    elif platform.system() == "Darwin":
        subprocess.run(["open", filepath])
    else:
        subprocess.run(["xdg-open", filepath])

def get_metadata(folder_path: Path) -> dict:
    meta_path = folder_path / METADATA_FILE
    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"separators": []}
    return {"separators": []}

def save_metadata(folder_path: Path, metadata: dict):
    meta_path = folder_path / METADATA_FILE
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def add_separator(folder_path: Path, caption: str) -> dict:
    meta = get_metadata(folder_path)
    new_sep = {
        "id": str(datetime.now().timestamp()),
        "caption": caption,
        "created": datetime.now().isoformat()
    }
    meta.setdefault("separators", []).append(new_sep)
    save_metadata(folder_path, meta)
    return meta

def delete_separator(folder_path: Path, sep_id: str):
    meta = get_metadata(folder_path)
    meta["separators"] = [s for s in meta.get("separators", []) if s.get("id") != sep_id]
    save_metadata(folder_path, meta)

# ==================== ГЛАВНОЕ ПРИЛОЖЕНИЕ ====================
class MediaManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Медиа Менеджер - Файловый менеджер")
        self.geometry("1200x750")
        self.minsize(900, 550)
        
        # Цветовая схема
        self.configure(bg="#f0f0f0")
        self.colors = {
            'bg': '#f0f0f0',
            'sidebar': '#ffffff',
            'accent': '#0078d4',
            'hover': '#e5e5e5',
            'text': '#202124',
            'separator': '#8e44ad'
        }
        
        # Создаём корневую папку в той же директории, где программа
        try:
            if not ROOT_DIR.exists():
                ROOT_DIR.mkdir(parents=True, exist_ok=True)
                print(f"✅ Создана папка: {ROOT_DIR}")
            else:
                print(f"📁 Папка уже существует: {ROOT_DIR}")
        except Exception as e:
            # Если не можем создать в текущей директории, создаём в домашней
            alternative_dir = Path.home() / "MediaVault"
            global ROOT_DIR
            ROOT_DIR = alternative_dir
            ROOT_DIR.mkdir(parents=True, exist_ok=True)
            print(f"⚠️ Используем альтернативную папку: {ROOT_DIR}")
        
        self.current_folder = ROOT_DIR
        
        # Создаём интерфейс
        self.create_widgets()
        self.refresh_tree()
        self.refresh_content()
        
        # Показываем путь в заголовке окна
        self.title(f"Медиа Менеджер - {ROOT_DIR}")
        
        self.bind("<Configure>", self.on_resize)
    
    def create_widgets(self):
        # ========== ВЕРХНЯЯ ПАНЕЛЬ ПОИСКА ==========
        top_frame = tk.Frame(self, bg=self.colors['accent'], height=70)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.pack_propagate(False)
        
        search_frame = tk.Frame(top_frame, bg=self.colors['accent'])
        search_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)
        
        # Иконка поиска
        tk.Label(search_frame, text="🔍", font=('Segoe UI', 18), 
                bg=self.colors['accent'], fg="white").pack(side=tk.LEFT, padx=(0, 10))
        
        # Поле поиска
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_tree())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                font=('Segoe UI', 12), bg="white", fg="black",
                                relief=tk.FLAT, highlightthickness=0)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        
        # Кнопка очистки
        clear_btn = tk.Button(search_frame, text="✖", font=('Segoe UI', 12, 'bold'),
                              bg=self.colors['accent'], fg="white", relief=tk.FLAT,
                              command=self.clear_search, cursor="hand2")
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Показываем путь к папке
        path_frame = tk.Frame(search_frame, bg=self.colors['accent'])
        path_frame.pack(side=tk.LEFT, padx=(20, 0))
        path_label = tk.Label(path_frame, text=f"📁 {ROOT_DIR}", 
                              font=('Segoe UI', 9), bg=self.colors['accent'], 
                              fg="#e0e0e0")
        path_label.pack()
        
        # ========== ОСНОВНАЯ ОБЛАСТЬ ==========
        main_paned = tk.PanedWindow(self, bg=self.colors['bg'], bd=0, sashwidth=5)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== ЛЕВАЯ ПАНЕЛЬ (ДЕРЕВО ПАПОК) ==========
        left_frame = tk.Frame(main_paned, bg=self.colors['sidebar'], relief=tk.FLAT, bd=1)
        main_paned.add(left_frame, width=250)
        
        tk.Label(left_frame, text="📁 ПАПКИ", font=('Segoe UI', 11, 'bold'),
                bg=self.colors['sidebar'], fg=self.colors['text']).pack(anchor=tk.W, padx=15, pady=10)
        
        tree_frame = tk.Frame(left_frame, bg=self.colors['sidebar'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, 
                                 selectmode='browse')
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # ========== ПРАВАЯ ПАНЕЛЬ (СОДЕРЖИМОЕ В ВИДЕ ИКОНОК) ==========
        right_frame = tk.Frame(main_paned, bg=self.colors['bg'])
        main_paned.add(right_frame, width=800)
        
        # Панель инструментов
        toolbar = tk.Frame(right_frame, bg=self.colors['bg'], height=45)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        toolbar.pack_propagate(False)
        
        buttons = [
            ("📁 Новая папка", self.create_folder),
            ("📤 Загрузить медиа", self.upload_media),
            ("✚ Разделитель", self.add_separator_ui),
            ("🔄 Обновить", self.refresh_content),
            ("⬆ На уровень вверх", self.go_up),
            ("📂 Открыть папку в проводнике", self.open_in_explorer)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(toolbar, text=text, font=('Segoe UI', 9),
                           bg="white", relief=tk.RAISED, bd=1, padx=10, pady=4,
                           command=cmd, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.colors['hover']))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="white"))
        
        # Область с иконками (скроллируемая)
        canvas_frame = tk.Frame(right_frame, bg=self.colors['bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['bg'])
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Колесико мыши
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # ========== СТАТУС БАР ==========
        self.status_var = tk.StringVar()
        self.status_var.set("✅ Готов")
        status_bar = tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, 
                             anchor=tk.W, font=('Segoe UI', 9), bg="#f9f9f9")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_in_explorer(self):
        """Открыть текущую папку в проводнике"""
        if platform.system() == "Windows":
            os.startfile(self.current_folder)
        elif platform.system() == "Darwin":
            subprocess.run(["open", self.current_folder])
        else:
            subprocess.run(["xdg-open", self.current_folder])
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def clear_search(self):
        self.search_var.set("")
        self.refresh_tree()
    
    def go_up(self):
        """Подняться на уровень вверх"""
        if self.current_folder != ROOT_DIR:
            self.current_folder = self.current_folder.parent
            self.refresh_tree()
            self.refresh_content()
            try:
                self.tree.selection_set(self.current_folder.as_posix())
                self.tree.see(self.current_folder.as_posix())
            except:
                pass
            self.status_var.set(f"📂 Переход в: {self.current_folder.name if self.current_folder != ROOT_DIR else 'MediaVault'}")
    
    def refresh_tree(self):
        selected = self.current_folder
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().strip().lower()
        self._insert_folder_node("", ROOT_DIR, search_term)
        self.tree.item(ROOT_DIR.as_posix(), open=True)
        if selected and selected != ROOT_DIR:
            try:
                self.tree.selection_set(selected.as_posix())
                self.tree.see(selected.as_posix())
            except:
                pass
    
    def _insert_folder_node(self, parent, folder_path: Path, search_term: str):
        show = (search_term == "") or (search_term in folder_path.name.lower())
        children_match = False
        try:
            items = sorted([p for p in folder_path.iterdir() if p.is_dir()])
        except PermissionError:
            return
        
        child_nodes = []
        for sub in items:
            if self._insert_folder_node(folder_path.as_posix(), sub, search_term):
                children_match = True
                child_nodes.append(sub)
        
        if show or children_match or folder_path == ROOT_DIR:
            node_id = folder_path.as_posix()
            if folder_path == ROOT_DIR:
                label = "📁 MediaVault (главная)"
            else:
                label = f"📁 {folder_path.name}"
            self.tree.insert(parent, "end", iid=node_id, text=label, open=False)
            return True
        return False
    
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if selection:
            path_str = selection[0]
            self.current_folder = Path(path_str)
            self.refresh_content()
            self.status_var.set(f"📂 Текущая папка: {self.current_folder.name if self.current_folder != ROOT_DIR else 'MediaVault'}")
    
    def refresh_content(self):
        """Обновить содержимое правой панели (иконки)"""
        # Очищаем фрейм
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.current_folder.exists():
            return
        
        # Собираем все элементы
        items = []
        
        # Папки
        try:
            for item in self.current_folder.iterdir():
                if item.is_dir() and item.name != METADATA_FILE:
                    items.append(("folder", item))
        except:
            pass
        
        # Разделители
        meta = get_metadata(self.current_folder)
        for sep in meta.get("separators", []):
            items.append(("separator", sep))
        
        # Медиафайлы
        try:
            for item in self.current_folder.iterdir():
                if item.is_file() and is_media_file(item.name):
                    items.append(("media", item))
        except:
            pass
        
        # Если ничего нет - показываем сообщение
        if not items:
            empty_label = tk.Label(self.scrollable_frame, 
                                   text="📭 Папка пуста\n\nНажмите 'Загрузить медиа' или 'Новая папка'",
                                   font=('Segoe UI', 14), fg="gray", bg=self.colors['bg'])
            empty_label.pack(expand=True, pady=50)
            return
        
        # Отображаем в виде сетки
        row = 0
        col = 0
        max_cols = 6
        
        for item_type, data in items:
            if item_type == "folder":
                self.create_folder_widget(data, row, col)
            elif item_type == "separator":
                self.create_separator_widget(data, row, col)
                col = 0
                row += 1
                continue
            else:
                self.create_media_widget(data, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Обновляем статус
        folder_count = len([i for i in items if i[0] == 'folder'])
        media_count = len([i for i in items if i[0] == 'media'])
        self.status_var.set(f"📁 {folder_count} папок, 🖼️ {media_count} файлов")
    
    def create_folder_widget(self, folder_path: Path, row, col):
        """Создает виджет папки с большой иконкой-символом"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg'])
        frame.grid(row=row, column=col, padx=20, pady=15, sticky="n")
        
        # Кнопка-иконка папки
        icon_btn = tk.Button(frame, text="📁", font=('Segoe UI', 48),
                            bg='#FFD700', fg='#8B6914', relief=tk.FLAT,
                            activebackground='#FFC107', cursor="hand2",
                            command=lambda: self.open_folder(folder_path))
        icon_btn.pack()
        
        # Название папки
        name = folder_path.name
        if len(name) > 20:
            name = name[:17] + "..."
        
        name_label = tk.Label(frame, text=name, font=('Segoe UI', 9, 'bold'),
                              bg=self.colors['bg'], fg=self.colors['text'],
                              cursor="hand2")
        name_label.pack(pady=(5, 0))
        name_label.bind("<Double-1>", lambda e, p=folder_path: self.open_folder(p))
        
        # Контекстное меню
        for w in [icon_btn, name_label, frame]:
            w.bind("<Button-3>", lambda e, p=folder_path: self.show_context_menu(e, p, "folder"))
    
    def create_media_widget(self, file_path: Path, row, col):
        """Создает виджет медиафайла"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg'])
        frame.grid(row=row, column=col, padx=20, pady=15, sticky="n")
        
        # Определяем иконку по типу
        ext = os.path.splitext(file_path.name)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
            icon = "🖼️"
            color = '#4A90D9'
            bg_color = '#B0C4DE'
        else:
            icon = "🎬"
            color = '#E74C3C'
            bg_color = '#FADBD8'
        
        # Кнопка-иконка
        icon_btn = tk.Button(frame, text=icon, font=('Segoe UI', 48),
                            bg=bg_color, fg=color, relief=tk.FLAT,
                            activebackground='#E8E8E8', cursor="hand2",
                            command=lambda: open_file_with_default_app(file_path))
        icon_btn.pack()
        
        # Название файла
        name = file_path.stem
        if len(name) > 15:
            name = name[:12] + "..."
        
        name_label = tk.Label(frame, text=name, font=('Segoe UI', 9),
                              bg=self.colors['bg'], fg=self.colors['text'],
                              cursor="hand2")
        name_label.pack(pady=(5, 0))
        name_label.bind("<Double-1>", lambda e, p=file_path: open_file_with_default_app(p))
        
        # Размер файла
        size_label = tk.Label(frame, text=get_file_size_str(file_path),
                              font=('Segoe UI', 8), fg="gray", bg=self.colors['bg'])
        size_label.pack()
        
        # Контекстное меню
        for w in [icon_btn, name_label, size_label, frame]:
            w.bind("<Button-3>", lambda e, p=file_path: self.show_context_menu(e, p, "file"))
    
    def create_separator_widget(self, sep_data, row, col):
        """Создает виджет разделителя на всю ширину"""
        frame = tk.Frame(self.scrollable_frame, bg=self.colors['separator'], height=40)
        frame.grid(row=row, column=0, columnspan=6, padx=10, pady=5, sticky="ew")
        frame.pack_propagate(False)
        
        sep_text = sep_data.get("caption", "Разделитель")
        
        tk.Label(frame, text="━" * 20, font=('Segoe UI', 10),
                bg=self.colors['separator'], fg="white").pack(side=tk.LEFT, padx=15)
        tk.Label(frame, text=f"⭐ {sep_text} ⭐", font=('Segoe UI', 10, 'bold'),
                bg=self.colors['separator'], fg="white").pack(side=tk.LEFT, padx=15)
        tk.Label(frame, text="━" * 20, font=('Segoe UI', 10),
                bg=self.colors['separator'], fg="white").pack(side=tk.LEFT, padx=15)
        
        frame.bind("<Button-3>", lambda e, sid=sep_data.get("id"): 
                  self.show_context_menu(e, sid, "separator"))
    
    def open_folder(self, folder_path: Path):
        self.current_folder = folder_path
        self.refresh_tree()
        self.refresh_content()
        try:
            self.tree.selection_set(folder_path.as_posix())
            self.tree.see(folder_path.as_posix())
        except:
            pass
    
    def show_context_menu(self, event, item, item_type):
        menu = tk.Menu(self, tearoff=0)
        if item_type == "folder":
            menu.add_command(label="🗑 Удалить папку", 
                           command=lambda: self.delete_file_or_folder(item))
            menu.add_command(label="📂 Открыть", 
                           command=lambda: self.open_folder(item))
        elif item_type == "file":
            menu.add_command(label="🗑 Удалить файл", 
                           command=lambda: self.delete_file_or_folder(item))
            menu.add_command(label="▶ Открыть", 
                           command=lambda: open_file_with_default_app(item))
        elif item_type == "separator":
            menu.add_command(label="❌ Удалить разделитель", 
                           command=lambda: self.delete_separator_item(item))
        
        menu.post(event.x_root, event.y_root)
    
    def create_folder(self):
        name = simpledialog.askstring("Новая папка", "Введите название папки:", parent=self)
        if not name or not name.strip():
            return
        
        # Убираем недопустимые символы
        invalid_chars = r'\/:*?"<>|'
        name = "".join(c for c in name if c not in invalid_chars)
        if not name:
            messagebox.showerror("Ошибка", "Недопустимое имя папки")
            return
        
        new_path = self.current_folder / name
        try:
            new_path.mkdir(exist_ok=False)
            self.status_var.set(f"✅ Папка создана: {name}")
            self.refresh_tree()
            self.refresh_content()
        except FileExistsError:
            messagebox.showerror("Ошибка", "Папка уже существует")
        except PermissionError:
            messagebox.showerror("Ошибка", "Нет прав для создания папки")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать папку: {str(e)}")
    
    def upload_media(self):
        filetypes = [
            ("Медиа файлы", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
            ("Все файлы", "*.*")
        ]
        files = filedialog.askopenfilenames(title="Выберите медиа файлы", filetypes=filetypes)
        if not files:
            return
        
        copied = 0
        for src in files:
            src_path = Path(src)
            dest = self.current_folder / src_path.name
            if dest.exists():
                if not messagebox.askyesno("Файл существует", f"{dest.name} уже существует. Перезаписать?"):
                    continue
            try:
                shutil.copy2(src_path, dest)
                copied += 1
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось скопировать {src_path.name}: {e}")
        
        self.status_var.set(f"✅ Загружено {copied} файлов")
        self.refresh_content()
    
    def add_separator_ui(self):
        caption = simpledialog.askstring("Добавить разделитель", "Текст разделителя:", parent=self)
        if caption is None:
            return
        if caption.strip() == "":
            caption = "Разделитель"
        add_separator(self.current_folder, caption.strip())
        self.refresh_content()
        self.status_var.set(f"✨ Разделитель добавлен: {caption}")
    
    def delete_separator_item(self, sep_id):
        if messagebox.askyesno("Подтверждение", "Удалить разделитель?"):
            delete_separator(self.current_folder, sep_id)
            self.refresh_content()
            self.status_var.set("🗑 Разделитель удален")
    
    def delete_file_or_folder(self, path: Path):
        if path.is_dir():
            if messagebox.askyesno("Подтверждение", f"Удалить папку '{path.name}' и всё её содержимое?"):
                try:
                    shutil.rmtree(path)
                    self.status_var.set(f"🗑 Папка удалена: {path.name}")
                    if self.current_folder == path:
                        self.current_folder = path.parent
                    self.refresh_tree()
                    self.refresh_content()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить папку: {e}")
        else:
            if messagebox.askyesno("Подтверждение", f"Удалить файл '{path.name}'?"):
                try:
                    path.unlink()
                    self.status_var.set(f"🗑 Файл удален: {path.name}")
                    self.refresh_content()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить файл: {e}")
    
    def on_resize(self, event):
        if event.widget == self:
            self.after(100, self.refresh_content)


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    app = MediaManagerApp()
    app.mainloop()