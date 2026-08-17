import os
import json
import fnmatch
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Pro File Manager"
SETTINGS_FILE = "settings.json"
LOGO_CANDIDATES = [
    "logo.png",
    "logo.jpg",
    os.path.join("assets", "logo.png"),
    os.path.join("assets", "logo.jpg"),
]


class ProFileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1180x720")
        self.root.minsize(1100, 680)

        self.source_dir = tk.StringVar()
        self.target_dir = tk.StringVar()
        self.mask_var = tk.StringVar(value="*.*")
        self.target_search_var = tk.StringVar(value="")
        self.target_recursive_var = tk.BooleanVar(value=True)
        self.zero_size_target_var = tk.BooleanVar(value=False)
        self.backup_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Готово")

        self.all_files = []
        self.filtered_files = []
        self.selected_files = set()
        self.item_to_path = {}
        self.path_to_item = {}
        self.settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SETTINGS_FILE)
        self.logo_image = None
        self.last_found_zero_files = []
        self.last_replace_matches = {}
        self.replace_selection_vars = {}

        self.setup_style()
        self.build_ui()
        self.load_settings()
        self.refresh_tree_if_possible()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

    def build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 6))
        ttk.Label(header, text="Профессиональный менеджер замены файлов", font=("Arial", 13, "bold")).pack(side="left", anchor="w")
        self.logo_label = ttk.Label(header)
        self.logo_label.pack(side="right", anchor="ne")
        self.load_logo()

        src_frame = ttk.LabelFrame(main, text="Источник", padding=8)
        src_frame.pack(fill="x", pady=(0, 6))
        ttk.Entry(src_frame, textvariable=self.source_dir, width=95).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ttk.Button(src_frame, text="Выбрать", command=self.choose_source).grid(row=0, column=1, sticky="e")
        src_frame.columnconfigure(0, weight=1)

        filter_frame = ttk.LabelFrame(main, text="Фильтр", padding=8)
        filter_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(filter_frame, text="Маска:").grid(row=0, column=0, sticky="w")
        ttk.Entry(filter_frame, textvariable=self.mask_var, width=26).grid(row=0, column=1, padx=(6, 8), sticky="w")
        ttk.Button(filter_frame, text="Применить", command=self.apply_filter).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(filter_frame, text="Сбросить", command=self.reset_filter).grid(row=0, column=3)

        actions_frame = ttk.Frame(main)
        actions_frame.pack(fill="x", pady=(0, 6))
        ttk.Button(actions_frame, text="Обновить", command=self.refresh_tree_if_possible).pack(side="left")
        ttk.Button(actions_frame, text="Выбрать все", command=self.select_all).pack(side="left", padx=(6, 0))
        ttk.Button(actions_frame, text="Снять все", command=self.unselect_all).pack(side="left", padx=(6, 0))
        ttk.Button(actions_frame, text="Инвертировать", command=self.invert_selection).pack(side="left", padx=(6, 0))
        ttk.Button(actions_frame, text="Выбрать совпадения", command=self.show_replace_matches_window).pack(side="left", padx=(6, 0))

        center = ttk.Frame(main)
        center.pack(fill="both", expand=True, pady=(0, 6))
        center.columnconfigure(0, weight=3)
        center.columnconfigure(1, weight=2)
        center.rowconfigure(0, weight=1)

        tree_frame = ttk.LabelFrame(center, text="Файлы источника", padding=6)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        columns = ("selected", "type", "size", "relative_path")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=16)
        self.tree.heading("#0", text="Имя")
        self.tree.heading("selected", text="Статус")
        self.tree.heading("type", text="Тип")
        self.tree.heading("size", text="Размер")
        self.tree.heading("relative_path", text="Путь")
        self.tree.column("#0", width=180, anchor="w")
        self.tree.column("selected", width=70, anchor="center")
        self.tree.column("type", width=70, anchor="center")
        self.tree.column("size", width=90, anchor="e")
        self.tree.column("relative_path", width=260, anchor="w")
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        right_panel = ttk.Frame(center)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.rowconfigure(2, weight=1)
        right_panel.columnconfigure(0, weight=1)

        dst_frame = ttk.LabelFrame(right_panel, text="Назначение", padding=8)
        dst_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Entry(dst_frame, textvariable=self.target_dir, width=50).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ttk.Button(dst_frame, text="Выбрать", command=self.choose_target).grid(row=0, column=1, sticky="e")
        ttk.Checkbutton(dst_frame, text="Искать во всех вложенных папках", variable=self.target_recursive_var, command=self.update_status).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(dst_frame, text="Поиск:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(dst_frame, textvariable=self.target_search_var, width=28).grid(row=2, column=0, padx=(52, 0), sticky="w", pady=(6, 0))
        ttk.Button(dst_frame, text="Найти", command=self.search_in_target).grid(row=2, column=1, sticky="e", pady=(6, 0))
        ttk.Checkbutton(dst_frame, text="Только файлы 0 байт", variable=self.zero_size_target_var, command=self.update_status).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(dst_frame, text="Удалить найденные 0-байтные", command=self.delete_found_zero_files).grid(row=4, column=1, sticky="e", pady=(6, 0))
        dst_frame.columnconfigure(0, weight=1)

        options_frame = ttk.LabelFrame(right_panel, text="Замена", padding=8)
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        ttk.Checkbutton(options_frame, text="Резервная копия (.bak)", variable=self.backup_var).grid(row=0, column=0, sticky="w")
        ttk.Button(options_frame, text="Выбрать совпадения", command=self.show_replace_matches_window).grid(row=0, column=1, padx=(10, 0), sticky="e")
        ttk.Button(options_frame, text="Запустить замену", command=self.run_replacement).grid(row=1, column=1, padx=(10, 0), sticky="e", pady=(6, 0))
        options_frame.columnconfigure(1, weight=1)

        log_frame = ttk.LabelFrame(right_panel, text="Лог", padding=6)
        log_frame.grid(row=2, column=0, sticky="nsew")
        self.log_text = tk.Text(log_frame, height=14, wrap="word")
        self.log_text.pack(fill="both", expand=True)

        status_frame = ttk.Frame(main)
        status_frame.pack(fill="x")
        ttk.Label(status_frame, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x")

    def load_logo(self):
        for candidate in LOGO_CANDIDATES:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), candidate)
            if os.path.exists(path):
                try:
                    img = tk.PhotoImage(file=path)
                    factor = max(1, int(max(img.width() / 120, img.height() / 60)))
                    if factor > 1:
                        img = img.subsample(factor, factor)
                    self.logo_image = img
                    self.logo_label.configure(image=self.logo_image)
                    return
                except Exception:
                    pass
        self.logo_label.configure(text="LOGO", foreground="#777777")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def human_size(self, size):
        units = ["B", "KB", "MB", "GB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
            value /= 1024

    def parse_masks(self):
        raw = self.mask_var.get().strip()
        if not raw:
            return ["*.*"]
        masks = [m.strip() for m in raw.split(";") if m.strip()]
        return masks or ["*.*"]

    def file_matches_masks(self, file_name):
        return any(fnmatch.fnmatch(file_name.lower(), mask.lower()) for mask in self.parse_masks())

    def choose_source(self):
        folder = filedialog.askdirectory(title="Выберите папку-источник")
        if folder:
            self.source_dir.set(folder)
            self.refresh_tree_if_possible()

    def choose_target(self):
        folder = filedialog.askdirectory(title="Выберите папку назначения")
        if folder:
            self.target_dir.set(folder)
            self.update_status()

    def refresh_tree_if_possible(self):
        source = self.source_dir.get().strip()
        if not source:
            self.clear_tree()
            self.all_files = []
            self.filtered_files = []
            self.update_status()
            return
        if not os.path.isdir(source):
            messagebox.showerror("Ошибка", "Папка-источник не найдена.")
            self.clear_tree()
            self.all_files = []
            self.filtered_files = []
            self.update_status()
            return
        self.scan_files()
        self.apply_filter()

    def scan_files(self):
        source = self.source_dir.get().strip()
        files = []
        try:
            for name in sorted(os.listdir(source)):
                full_path = os.path.join(source, name)
                if os.path.isfile(full_path):
                    rel_path = os.path.relpath(full_path, source)
                    files.append({
                        "name": name,
                        "full_path": full_path,
                        "relative_path": rel_path,
                        "size": os.path.getsize(full_path),
                        "ext": os.path.splitext(name)[1].lower() or "[без расширения]"
                    })
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сканирования:\n{e}")
            self.log(f"Ошибка сканирования: {e}")
            self.all_files = []
            return
        self.all_files = files
        self.log(f"Найдено файлов в источнике: {len(self.all_files)}")

    def apply_filter(self):
        self.filtered_files = [f for f in self.all_files if self.file_matches_masks(f['name'])]
        self.build_tree()
        self.update_status()

    def reset_filter(self):
        self.mask_var.set("*.*")
        self.apply_filter()

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_to_path.clear()
        self.path_to_item.clear()

    def build_tree(self):
        self.clear_tree()
        for file_info in self.filtered_files:
            rel_path = file_info['relative_path']
            selected_mark = "Да" if file_info['full_path'] in self.selected_files else "Нет"
            node = self.tree.insert("", "end", text=file_info['name'], values=(selected_mark, file_info['ext'], self.human_size(file_info['size']), rel_path))
            self.item_to_path[node] = file_info['full_path']
            self.path_to_item[file_info['full_path']] = node

    def on_tree_double_click(self, event):
        item = self.tree.focus()
        if item not in self.item_to_path:
            return
        file_path = self.item_to_path[item]
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
        else:
            self.selected_files.add(file_path)
        self.refresh_selection_marks()
        self.update_status()

    def refresh_selection_marks(self):
        for path, item in self.path_to_item.items():
            if self.tree.exists(item):
                values = list(self.tree.item(item, 'values'))
                values[0] = "Да" if path in self.selected_files else "Нет"
                self.tree.item(item, values=values)

    def select_all(self):
        self.selected_files = {f['full_path'] for f in self.filtered_files}
        self.refresh_selection_marks()
        self.update_status()

    def unselect_all(self):
        self.selected_files.clear()
        self.refresh_selection_marks()
        self.update_status()

    def invert_selection(self):
        current_filtered = {f['full_path'] for f in self.filtered_files}
        new_selection = set(self.selected_files)
        for path in current_filtered:
            if path in new_selection:
                new_selection.remove(path)
            else:
                new_selection.add(path)
        self.selected_files = new_selection
        self.refresh_selection_marks()
        self.update_status()

    def walk_target_files(self, target_root, force_recursive=False):
        recursive = force_recursive or self.target_recursive_var.get()
        if recursive:
            for root_dir, dirnames, filenames in os.walk(target_root):
                dirnames.sort()
                filenames.sort()
                for existing_name in filenames:
                    yield os.path.join(root_dir, existing_name)
        else:
            for existing_name in sorted(os.listdir(target_root)):
                full_path = os.path.join(target_root, existing_name)
                if os.path.isfile(full_path):
                    yield full_path

    def search_in_target(self):
        target = self.target_dir.get().strip()
        query = self.target_search_var.get().strip().lower()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Ошибка", "Выберите корректную папку назначения.")
            return
        if not query and not self.zero_size_target_var.get():
            messagebox.showerror("Ошибка", "Введите имя файла или включите поиск файлов 0 байт.")
            return
        found = 0
        self.last_found_zero_files = []
        for full_path in self.walk_target_files(target, force_recursive=self.zero_size_target_var.get()):
            try:
                size = os.path.getsize(full_path)
                name = os.path.basename(full_path).lower()
                if self.zero_size_target_var.get():
                    if size != 0:
                        continue
                    if query and query not in name:
                        continue
                    self.last_found_zero_files.append(full_path)
                else:
                    if query not in name:
                        continue
                found += 1
                self.log(f"Найдено в назначении: {full_path}")
            except Exception as e:
                self.log(f"Ошибка поиска в назначении: {full_path} -> {e}")
        messagebox.showinfo("Поиск завершён", f"Найдено файлов в назначении: {found}")
        self.update_status()

    def delete_found_zero_files(self):
        if not self.last_found_zero_files:
            messagebox.showinfo("Информация", "Сначала выполните поиск 0-байтных файлов.")
            return
        self.show_zero_files_delete_window()

    def show_zero_files_delete_window(self):
        win = tk.Toplevel(self.root)
        win.title("Удаление 0-байтных файлов")
        win.geometry("860x430")
        vars_map = []
        ttk.Label(win, text="Отметьте файлы 0 байт для удаления:", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=10)
        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for path in self.last_found_zero_files:
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(inner, text=path, variable=var).pack(anchor="w", fill="x", pady=2)
            vars_map.append((var, path))

        def delete_selected():
            deleted = 0
            errors = 0
            for var, path in vars_map:
                if var.get():
                    try:
                        if os.path.exists(path) and os.path.getsize(path) == 0:
                            os.remove(path)
                            deleted += 1
                            self.log(f"Удалён 0-байтный файл: {path}")
                    except Exception as e:
                        errors += 1
                        self.log(f"Ошибка удаления файла: {path} -> {e}")
            messagebox.showinfo("Готово", f"Удалено файлов: {deleted}\nОшибок: {errors}")
            win.destroy()

        ttk.Button(win, text="Удалить отмеченные", command=delete_selected).pack(anchor="e", padx=10, pady=(0, 10))

    def find_same_name_targets(self, target_root, file_name):
        matches = []
        for full_path in self.walk_target_files(target_root, force_recursive=True):
            try:
                existing_name = os.path.basename(full_path)
                if existing_name.lower() == file_name.lower():
                    if self.zero_size_target_var.get() and os.path.getsize(full_path) != 0:
                        continue
                    matches.append(full_path)
            except Exception as e:
                self.log(f"Ошибка анализа файла назначения: {full_path} -> {e}")
        return matches

    def collect_replace_matches(self):
        target = self.target_dir.get().strip()
        result = {}
        if not target or not os.path.isdir(target):
            return result
        for src_file in sorted(self.selected_files):
            file_name = os.path.basename(src_file)
            result[src_file] = self.find_same_name_targets(target, file_name)
        self.last_replace_matches = result
        return result

    def show_replace_matches_window(self):
        if not self.selected_files:
            messagebox.showinfo("Информация", "Сначала выберите файлы источника.")
            return
        target = self.target_dir.get().strip()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Ошибка", "Сначала выберите папку назначения.")
            return
        matches = self.collect_replace_matches()
        self.replace_selection_vars = {}
        win = tk.Toplevel(self.root)
        win.title("Выбор совпадений для замены")
        win.geometry("980x520")
        ttk.Label(win, text="Отметьте совпадения, которые нужно заменить", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=10)
        top_btns = ttk.Frame(win)
        top_btns.pack(fill="x", padx=10, pady=(0, 6))
        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        total = 0
        all_vars = []
        for src, found_list in matches.items():
            ttk.Label(inner, text=f"Источник: {src}", font=("Arial", 10, "bold")).pack(anchor="w", pady=(6, 2))
            if found_list:
                for path in found_list:
                    var = tk.BooleanVar(value=True)
                    chk = ttk.Checkbutton(inner, text=path, variable=var)
                    chk.pack(anchor="w", fill="x", pady=1)
                    self.replace_selection_vars[(src, path)] = var
                    all_vars.append(var)
                    total += 1
            else:
                ttk.Label(inner, text="Совпадений не найдено", foreground="#666666").pack(anchor="w", pady=(0, 4))

        def mark_all():
            for var in all_vars:
                var.set(True)

        def unmark_all():
            for var in all_vars:
                var.set(False)

        ttk.Button(top_btns, text="Отметить все", command=mark_all).pack(side="left")
        ttk.Button(top_btns, text="Снять все", command=unmark_all).pack(side="left", padx=(6, 0))

        def save_selection():
            messagebox.showinfo("Готово", "Выбор совпадений сохранён. Теперь нажмите 'Запустить замену'.")
            win.destroy()

        bottom = ttk.Frame(win)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(bottom, text=f"Всего найдено совпадений: {total}").pack(side="left")
        ttk.Button(bottom, text="Сохранить выбор", command=save_selection).pack(side="right")

    def run_replacement(self):
        target = self.target_dir.get().strip()
        if not target or not os.path.isdir(target):
            messagebox.showerror("Ошибка", "Выберите корректную папку назначения.")
            return
        if not self.selected_files:
            messagebox.showerror("Ошибка", "Не выбрано ни одного файла источника.")
            return

        if not self.replace_selection_vars:
            self.collect_replace_matches()
            for src_file, found_list in self.last_replace_matches.items():
                for path in found_list:
                    self.replace_selection_vars[(src_file, path)] = tk.BooleanVar(value=True)

        replaced = 0
        skipped = 0
        errors = 0
        any_selected_match = False

        for src_file in sorted(self.selected_files):
            file_name = os.path.basename(src_file)
            dst_files = self.find_same_name_targets(target, file_name)
            if not dst_files:
                skipped += 1
                self.log(f"Пропущено: {file_name} — совпадения во вложенных папках назначения не найдены")
                continue

            for dst_file in dst_files:
                var = self.replace_selection_vars.get((src_file, dst_file))
                if var is not None and not var.get():
                    self.log(f"Пропущено пользователем: {dst_file}")
                    continue
                any_selected_match = True
                try:
                    if os.path.exists(dst_file):
                        if self.backup_var.get():
                            shutil.copy2(dst_file, dst_file + '.bak')
                            self.log(f"Создана резервная копия: {dst_file}.bak")
                        shutil.copy2(src_file, dst_file)
                        replaced += 1
                        self.log(f"Заменён файл: {src_file} -> {dst_file}")
                except PermissionError:
                    errors += 1
                    self.log(f"Ошибка доступа: {dst_file}")
                except Exception as e:
                    errors += 1
                    self.log(f"Ошибка замены: {src_file} -> {dst_file} -> {e}")

        if not any_selected_match:
            messagebox.showwarning("Нет выбранных совпадений", "Нет отмеченных совпадений для замены.")
            return

        self.update_status()
        messagebox.showinfo("Готово", f"Замена завершена.\n\nЗаменено: {replaced}\nПропущено: {skipped}\nОшибок: {errors}")

    def update_status(self):
        found = len(self.filtered_files)
        filtered_paths = {f['full_path'] for f in self.filtered_files}
        selected = len(self.selected_files.intersection(filtered_paths)) if filtered_paths else len(self.selected_files)
        target_recursive = "Вложенные папки назначения: Да" if self.target_recursive_var.get() else "Вложенные папки назначения: Нет"
        zero_target = "0 байт: Да" if self.zero_size_target_var.get() else "0 байт: Нет"
        self.status_var.set(f"Найдено: {found} | Выбрано: {selected} | Режим: только замена | {target_recursive} | {zero_target}")

    def load_settings(self):
        if not os.path.exists(self.settings_path):
            return
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.source_dir.set(data.get('source_dir', ''))
            self.target_dir.set(data.get('target_dir', ''))
            self.mask_var.set(data.get('mask', '*.*'))
            self.target_recursive_var.set(data.get('target_recursive', True))
            self.zero_size_target_var.set(data.get('zero_size_target', False))
            self.target_search_var.set(data.get('target_search', ''))
            self.backup_var.set(data.get('backup', True))
            self.log("Настройки загружены")
        except Exception as e:
            self.log(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        data = {
            'source_dir': self.source_dir.get().strip(),
            'target_dir': self.target_dir.get().strip(),
            'mask': self.mask_var.get().strip(),
            'target_recursive': self.target_recursive_var.get(),
            'zero_size_target': self.zero_size_target_var.get(),
            'target_search': self.target_search_var.get().strip(),
            'backup': self.backup_var.get(),
        }
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"Ошибка сохранения настроек: {e}")

    def on_close(self):
        self.save_settings()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = ProFileManagerApp(root)
    root.mainloop()
