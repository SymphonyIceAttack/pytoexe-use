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
# Определяем папку, где находится программа
if getattr(sys, 'frozen', False):
    PROGRAM_DIR = Path(sys.executable).parent
else:
    PROGRAM_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

ROOT_DIR = PROGRAM_DIR / "MediaVault"

MEDIA_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'
}
METADATA_FILE = ".mediamanager.json"

# ==================== ФУНКЦИИ ====================
def is_media_file(filename):
    return os.path.splitext(filename)[1].lower() in MEDIA_EXTENSIONS

def get_file_size_str(filepath):
    size = filepath.stat().st_size
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} ТБ"

def open_file_with_default_app(filepath):
    if platform.system() == "Windows":
        os.startfile(filepath)
    elif platform.system() == "Darwin":
        subprocess.run(["open", filepath])
    else:
        subprocess.run(["xdg-open", filepath])

def get_metadata(folder_path):
    meta_path = folder_path / METADATA_FILE
    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"separators": []}
    return {"separators": []}

def save_metadata(folder_path, metadata):
    with open(folder_path / METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def add_separator(folder_path, caption):
    meta = get_metadata(folder_path)
    new_sep = {"id": str(datetime.now().timestamp()), "caption": caption}
    meta.setdefault("separators", []).append(new_sep)
    save_metadata(folder_path, meta)
    return meta

def delete_separator(folder_path, sep_id):
    meta = get_metadata(folder_path)
    meta["separators"] = [s for s in meta.get("separators", []) if s.get("id") != sep_id]
    save_metadata(folder_path, meta)

# ==================== ГЛАВНОЕ ОКНО ====================
class MediaManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Медиа Менеджер")
        self.geometry("1100x700")
        self.configure(bg="#f0f0f0")
        
        # Создаем папку
        try:
            ROOT_DIR.mkdir(parents=True, exist_ok=True)
        except:
            pass
        
        self.current_folder = ROOT_DIR
        
        # Создаем интерфейс
        self.setup_ui()
        self.refresh_tree()
        self.refresh_content()
    
    def setup_ui(self):
        # Верхняя панель поиска
        top_frame = tk.Frame(self, bg="#0078d4", height=60)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        search_frame = tk.Frame(top_frame, bg="#0078d4")
        search_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        tk.Label(search_frame, text="🔍", font=('Arial', 14), bg="#0078d4", fg="white").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.refresh_tree())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 11))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Button(search_frame, text="Очистить", command=self.clear_search, bg="white").pack(side=tk.LEFT, padx=5)
        
        # Панель инструментов
        toolbar = tk.Frame(self, bg="#e0e0e0", height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        buttons = [
            ("📁 Новая папка", self.create_folder),
            ("📤 Загрузить", self.upload_media),
            ("✚ Разделитель", self.add_separator_ui),
            ("🔄 Обновить", self.refresh_content),
            ("⬆ Вверх", self.go_up)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(toolbar, text=text, command=cmd, bg="#e0e0e0", relief=tk.RAISED, padx=10)
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Основная панель
        main_frame = tk.Frame(self, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - дерево папок
        left_frame = tk.LabelFrame(main_frame, text="Папки", bg="white", font=('Arial', 10, 'bold'))
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        
        tree_scroll = tk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(left_frame, yscrollcommand=tree_scroll.set, height=25)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tree_scroll.config(command=self.tree.yview)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Правая панель - содержимое
        right_frame = tk.LabelFrame(main_frame, text="Содержимое", bg="white", font=('Arial', 10, 'bold'))
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Канвас для иконок
        canvas_frame = tk.Frame(right_frame, bg="white")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов")
        status_bar = tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, bg="#f9f9f9")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def clear_search(self):
        self.search_var.set("")
        self.refresh_tree()
    
    def go_up(self):
        if self.current_folder != ROOT_DIR:
            self.current_folder = self.current_folder.parent
            self.refresh_tree()
            self.refresh_content()
    
    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        search_term = self.search_var.get().strip().lower()
        self.add_folder_node("", ROOT_DIR, search_term)
        self.tree.item(ROOT_DIR.as_posix(), open=True)
    
    def add_folder_node(self, parent, folder_path, search_term):
        show = (search_term == "") or (search_term in folder_path.name.lower())
        
        try:
            folders = sorted([p for p in folder_path.iterdir() if p.is_dir()])
        except:
            return
        
        children_match = False
        for sub in folders:
            if self.add_folder_node(folder_path.as_posix(), sub, search_term):
                children_match = True
        
        if show or children_match or folder_path == ROOT_DIR:
            label = "📁 MediaVault" if folder_path == ROOT_DIR else f"📁 {folder_path.name}"
            self.tree.insert(parent, "end", iid=folder_path.as_posix(), text=label, open=False)
            return True
        return False
    
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if selection:
            self.current_folder = Path(selection[0])
            self.refresh_content()
    
    def refresh_content(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.current_folder.exists():
            return
        
        items = []
        
        # Папки
        try:
            for item in self.current_folder.iterdir():
                if item.is_dir() and item.name != METADATA_FILE:
                    items.append(("folder", item))
        except:
            pass
        
        # Разделители
        for sep in get_metadata(self.current_folder).get("separators", []):
            items.append(("separator", sep))
        
        # Файлы
        try:
            for item in self.current_folder.iterdir():
                if item.is_file() and is_media_file(item.name):
                    items.append(("file", item))
        except:
            pass
        
        if not items:
            tk.Label(self.scrollable_frame, text="Папка пуста", font=('Arial', 16), fg="gray", bg="white").pack(expand=True, pady=50)
            return
        
        row, col = 0, 0
        max_cols = 5
        
        for item_type, data in items:
            if item_type == "folder":
                self.create_folder_icon(data, row, col)
            elif item_type == "separator":
                self.create_separator(data, row, col)
                col = 0
                row += 1
                continue
            else:
                self.create_file_icon(data, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        folder_count = len([i for i in items if i[0] == 'folder'])
        file_count = len([i for i in items if i[0] == 'file'])
        self.status_var.set(f"Папок: {folder_count}, файлов: {file_count}")
    
    def create_folder_icon(self, folder_path, row, col):
        frame = tk.Frame(self.scrollable_frame, bg="white")
        frame.grid(row=row, column=col, padx=15, pady=10)
        
        btn = tk.Button(frame, text="📁", font=('Arial', 40), bg="#FFD700", fg="#8B6914",
                       command=lambda: self.open_folder(folder_path))
        btn.pack()
        
        name = folder_path.name[:15] + "..." if len(folder_path.name) > 15 else folder_path.name
        label = tk.Label(frame, text=name, bg="white", font=('Arial', 9))
        label.pack()
        
        btn.bind("<Button-3>", lambda e: self.delete_item(folder_path, "folder"))
        label.bind("<Button-3>", lambda e: self.delete_item(folder_path, "folder"))
    
    def create_file_icon(self, file_path, row, col):
        frame = tk.Frame(self.scrollable_frame, bg="white")
        frame.grid(row=row, column=col, padx=15, pady=10)
        
        ext = os.path.splitext(file_path.name)[1].lower()
        if ext in {'.jpg', '.jpeg', '.png', '.gif'}:
            icon, color, bg = "🖼️", "#4A90D9", "#B0C4DE"
        else:
            icon, color, bg = "🎬", "#E74C3C", "#FADBD8"
        
        btn = tk.Button(frame, text=icon, font=('Arial', 40), bg=bg, fg=color,
                       command=lambda: open_file_with_default_app(file_path))
        btn.pack()
        
        name = file_path.stem[:12] + "..." if len(file_path.stem) > 12 else file_path.stem
        tk.Label(frame, text=name, bg="white", font=('Arial', 8)).pack()
        tk.Label(frame, text=get_file_size_str(file_path), bg="white", font=('Arial', 7), fg="gray").pack()
        
        btn.bind("<Button-3>", lambda e: self.delete_item(file_path, "file"))
    
    def create_separator(self, sep_data, row, col):
        frame = tk.Frame(self.scrollable_frame, bg="#8e44ad", height=35)
        frame.grid(row=row, column=0, columnspan=5, padx=10, pady=5, sticky="ew")
        frame.pack_propagate(False)
        
        tk.Label(frame, text="━" * 15, bg="#8e44ad", fg="white", font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        tk.Label(frame, text=sep_data.get("caption", "Разделитель"), bg="#8e44ad", fg="white", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=10)
        tk.Label(frame, text="━" * 15, bg="#8e44ad", fg="white", font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        
        frame.bind("<Button-3>", lambda e: self.delete_separator_item(sep_data.get("id")))
    
    def open_folder(self, folder_path):
        self.current_folder = folder_path
        self.refresh_tree()
        self.refresh_content()
    
    def delete_item(self, path, item_type):
        if messagebox.askyesno("Удалить", f"Удалить {item_type} '{path.name}'?"):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                self.refresh_content()
                self.refresh_tree()
                self.status_var.set(f"Удалено: {path.name}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def delete_separator_item(self, sep_id):
        if messagebox.askyesno("Удалить", "Удалить разделитель?"):
            delete_separator(self.current_folder, sep_id)
            self.refresh_content()
    
    def create_folder(self):
        name = simpledialog.askstring("Новая папка", "Имя папки:")
        if name and name.strip():
            name = "".join(c for c in name if c not in r'\/:*?"<>|')
            if name:
                try:
                    (self.current_folder / name).mkdir()
                    self.refresh_tree()
                    self.refresh_content()
                    self.status_var.set(f"Создана папка: {name}")
                except:
                    messagebox.showerror("Ошибка", "Не удалось создать папку")
    
    def upload_media(self):
        files = filedialog.askopenfilenames(title="Выберите файлы")
        if files:
            for src in files:
                src_path = Path(src)
                dest = self.current_folder / src_path.name
                try:
                    shutil.copy2(src_path, dest)
                except:
                    pass
            self.refresh_content()
            self.status_var.set(f"Загружено файлов: {len(files)}")
    
    def add_separator_ui(self):
        caption = simpledialog.askstring("Разделитель", "Текст:")
        if caption:
            add_separator(self.current_folder, caption)
            self.refresh_content()

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    app = MediaManagerApp()
    app.mainloop()