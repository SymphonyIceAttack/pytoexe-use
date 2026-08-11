# -*- coding: utf-8 -*-
"""
Организатор скриншотов
=======================
Программа для Windows:
- Базовая папка "Администрация" создаётся на Рабочем столе автоматически.
- Слева - дерево папок (можно создавать вложенные подпапки любой глубины,
  переименовывать, удалять, открывать в проводнике, копировать путь, искать).
- Справа - зона приёма скриншота (Ctrl+V из буфера или перетаскивание файла)
  и сохранение с именем, включающим указанную причину.
"""

import os
import re
import shutil
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from PIL import Image, ImageGrab, ImageTk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


BASE_FOLDER_NAME = "Администрация"
PREVIEW_MAX_SIZE = (340, 200)
DUMMY_TAG = "__dummy__"


def get_desktop_path() -> str:
    userprofile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop = os.path.join(userprofile, "Desktop")
    if os.path.isdir(desktop):
        return desktop
    return os.path.expanduser("~/Desktop")


def sanitize_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(" .") or "Без_названия"


class ScreenshotOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Организатор скриншотов — Администрация")
        self.root.geometry("920x560")
        self.root.minsize(760, 460)

        self.base_dir = os.path.join(get_desktop_path(), BASE_FOLDER_NAME)
        os.makedirs(self.base_dir, exist_ok=True)

        self.active_folder = None
        self.current_image = None
        self.preview_photo = None
        self.search_var = tk.StringVar()

        self._build_ui()
        self._build_context_menu()
        self._reload_tree()

    # ================================================================= UI
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(1, weight=1)

        # ---------------------------------------------------- Левая панель
        left = ttk.Frame(main)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text=f"Базовая папка: {self.base_dir}",
                  foreground="#555", wraplength=460).grid(row=0, column=0, sticky="w")

        toolbar = ttk.Frame(left)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(6, 4))

        ttk.Button(toolbar, text="Новая папка", command=self._create_folder).pack(side="left")
        ttk.Button(toolbar, text="Переименовать", command=self._rename_folder).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Удалить", command=self._delete_folder).pack(side="left")
        ttk.Button(toolbar, text="Открыть в проводнике", command=self._open_in_explorer).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Копировать путь", command=self._copy_path).pack(side="left")
        ttk.Button(toolbar, text="Обновить", command=self._reload_tree).pack(side="left", padx=4)

        search_frame = ttk.Frame(left)
        search_frame.grid(row=2, column=0, sticky="new")
        search_frame.columnconfigure(1, weight=1)
        ttk.Label(search_frame, text="Поиск:").grid(row=0, column=0, sticky="w")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        search_entry.bind("<KeyRelease>", lambda e: self._reload_tree())
        ttk.Button(search_frame, text="✕", width=3,
                   command=lambda: (self.search_var.set(""), self._reload_tree())).grid(row=0, column=2, padx=(4, 0))

        tree_frame = ttk.Frame(left)
        tree_frame.grid(row=3, column=0, sticky="nsew", pady=(6, 0))
        left.rowconfigure(3, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vscroll.set)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        self.tree.bind("<Button-3>", self._on_tree_right_click)

        hint = ttk.Label(left, foreground="#888",
                          text="Клик — выбрать активную папку. ПКМ — контекстное меню.")
        hint.grid(row=4, column=0, sticky="w", pady=(4, 0))

        # --------------------------------------------------- Правая панель
        right = ttk.Frame(main)
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.active_label_var = tk.StringVar(value="Активная папка: не выбрана")
        ttk.Label(right, textvariable=self.active_label_var,
                  font=("Segoe UI", 10, "bold"), wraplength=380).grid(row=0, column=0, sticky="w", pady=(0, 8))

        drop_border = tk.Frame(right, bg="#999999")
        drop_border.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        drop_border.rowconfigure(0, weight=1)
        drop_border.columnconfigure(0, weight=1)

        self.drop_area = tk.Label(
            drop_border,
            text="Сюда можно перетащить картинку\nили нажать здесь и вставить Ctrl+V",
            bg="#f4f4f4", fg="#666666", justify="center"
        )
        self.drop_area.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.drop_area.bind("<Button-1>", lambda e: self.drop_area.focus_set())

        self.root.bind_all("<Control-v>", self._paste_from_clipboard)

        if DND_AVAILABLE:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self._on_file_drop)
        else:
            self.drop_area.configure(
                text=self.drop_area.cget("text") +
                "\n\n(перетаскивание недоступно: нет пакета tkinterdnd2)"
            )

        bottom = ttk.Frame(right)
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, text="Причина:").grid(row=0, column=0, sticky="w")
        self.reason_var = tk.StringVar()
        reason_entry = ttk.Entry(bottom, textvariable=self.reason_var)
        reason_entry.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        reason_entry.bind("<Return>", lambda e: self._save_screenshot())

        ttk.Button(bottom, text="Сохранить скриншот",
                   command=self._save_screenshot).grid(row=1, column=1, padx=(6, 0))

        self.status_var = tk.StringVar(value="Готово.")
        ttk.Label(right, textvariable=self.status_var, foreground="#0a6",
                  wraplength=380).grid(row=3, column=0, sticky="w", pady=(6, 0))

    def _build_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Новая подпапка", command=self._create_folder)
        self.context_menu.add_command(label="Переименовать", command=self._rename_folder)
        self.context_menu.add_command(label="Удалить", command=self._delete_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Открыть в проводнике", command=self._open_in_explorer)
        self.context_menu.add_command(label="Копировать путь", command=self._copy_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Сделать активной для скриншота",
                                       command=self._set_active_from_selection)

    # ============================================================ Дерево
    def _reload_tree(self):
        self.tree.delete(*self.tree.get_children(""))
        query = self.search_var.get().strip().lower()

        if query:
            self._populate_filtered(self.base_dir, "", query)
            self._expand_all()
        else:
            self._populate_lazy(self.base_dir, "")

        if self.active_folder and os.path.isdir(self.active_folder):
            self._select_path_in_tree(self.active_folder)

    def _populate_lazy(self, path, parent_iid):
        try:
            entries = sorted(
                e for e in os.listdir(path)
                if os.path.isdir(os.path.join(path, e))
            )
        except FileNotFoundError:
            entries = []
        for name in entries:
            full = os.path.join(path, name)
            node = self.tree.insert(parent_iid, "end", iid=full, text=name, open=False)
            if self._has_subdirs(full):
                self.tree.insert(node, "end", iid=full + "\\" + DUMMY_TAG, text="")

    def _populate_filtered(self, path, parent_iid, query):
        try:
            entries = sorted(
                e for e in os.listdir(path)
                if os.path.isdir(os.path.join(path, e))
            )
        except FileNotFoundError:
            entries = []
        for name in entries:
            full = os.path.join(path, name)
            child_has_match = self._subtree_has_match(full, query)
            self_match = query in name.lower()
            if self_match or child_has_match:
                node = self.tree.insert(parent_iid, "end", iid=full, text=name, open=True)
                self._populate_filtered(full, node, query)

    def _subtree_has_match(self, path, query):
        try:
            entries = os.listdir(path)
        except FileNotFoundError:
            return False
        for name in entries:
            full = os.path.join(path, name)
            if os.path.isdir(full):
                if query in name.lower() or self._subtree_has_match(full, query):
                    return True
        return False

    def _has_subdirs(self, path):
        try:
            return any(os.path.isdir(os.path.join(path, e)) for e in os.listdir(path))
        except FileNotFoundError:
            return False

    def _on_tree_open(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)
        if len(children) == 1 and children[0].endswith(DUMMY_TAG):
            self.tree.delete(children[0])
            self._populate_lazy(node, node)

    def _expand_all(self):
        def expand(node):
            self.tree.item(node, open=True)
            for child in self.tree.get_children(node):
                expand(child)
        for top in self.tree.get_children(""):
            expand(top)

    def _select_path_in_tree(self, path):
        parts = []
        cur = path
        while cur and cur != self.base_dir and len(cur) >= len(self.base_dir):
            parts.append(cur)
            cur = os.path.dirname(cur)
        for p in reversed(parts):
            if self.tree.exists(p):
                self.tree.item(p, open=True)
        if self.tree.exists(path):
            self.tree.selection_set(path)
            self.tree.see(path)

    def _selected_path(self):
        sel = self.tree.selection()
        if not sel:
            return None
        path = sel[0]
        if path.endswith(DUMMY_TAG):
            return None
        return path

    # ======================================================= Действия с ПКМ
    def _on_tree_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and not iid.endswith(DUMMY_TAG):
            self.tree.selection_set(iid)
        self.context_menu.post(event.x_root, event.y_root)

    def _on_tree_select(self, event):
        path = self._selected_path()
        if path:
            self._set_active(path)

    def _set_active_from_selection(self):
        path = self._selected_path()
        if path:
            self._set_active(path)

    def _set_active(self, path):
        self.active_folder = path
        rel = os.path.relpath(path, self.base_dir)
        self.active_label_var.set(f"Активная папка: {rel}")
        self.status_var.set(f"Выбрана папка «{rel}» для сохранения скриншотов.")

    # ============================================================ CRUD папок
    def _create_folder(self):
        parent = self._selected_path() or self.base_dir
        name = simpledialog.askstring("Новая папка", f"Название новой папки внутри:\n{parent}")
        if not name:
            return
        name = sanitize_filename(name)
        new_path = os.path.join(parent, name)
        if os.path.exists(new_path):
            messagebox.showwarning("Уже существует", "Папка с таким именем уже есть.")
            return
        try:
            os.makedirs(new_path)
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))
            return
        self._reload_tree()
        self._select_path_in_tree(new_path)
        self._set_active(new_path)
        self.status_var.set(f"Папка «{name}» создана.")

    def _rename_folder(self):
        path = self._selected_path()
        if not path or path == self.base_dir:
            messagebox.showinfo("Переименование", "Выберите папку для переименования.")
            return
        old_name = os.path.basename(path)
        new_name = simpledialog.askstring("Переименовать", "Новое имя папки:", initialvalue=old_name)
        if not new_name or new_name == old_name:
            return
        new_name = sanitize_filename(new_name)
        new_path = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(new_path):
            messagebox.showwarning("Уже существует", "Папка с таким именем уже есть.")
            return
        try:
            os.rename(path, new_path)
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))
            return
        was_active = (self.active_folder == path)
        self._reload_tree()
        self._select_path_in_tree(new_path)
        if was_active:
            self._set_active(new_path)
        self.status_var.set(f"Папка переименована в «{new_name}».")

    def _delete_folder(self):
        path = self._selected_path()
        if not path or path == self.base_dir:
            messagebox.showinfo("Удаление", "Выберите папку для удаления.")
            return
        name = os.path.basename(path)
        if not messagebox.askyesno(
            "Подтверждение удаления",
            f"Удалить папку «{name}» и всё её содержимое безвозвратно?"
        ):
            return
        try:
            shutil.rmtree(path)
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))
            return
        if self.active_folder == path:
            self.active_folder = None
            self.active_label_var.set("Активная папка: не выбрана")
        self._reload_tree()
        self.status_var.set(f"Папка «{name}» удалена.")

    def _open_in_explorer(self):
        path = self._selected_path() or self.base_dir
        try:
            os.startfile(path)  # доступно только в Windows
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))

    def _copy_path(self):
        path = self._selected_path() or self.base_dir
        self.root.clipboard_clear()
        self.root.clipboard_append(path)
        self.status_var.set("Путь скопирован в буфер обмена.")

    # ==================================================== Приём изображения
    def _paste_from_clipboard(self, event=None):
        try:
            content = ImageGrab.grabclipboard()
        except Exception as ex:
            self.status_var.set(f"Ошибка чтения буфера обмена: {ex}")
            return

        if content is None:
            self.status_var.set("В буфере обмена нет изображения.")
            return

        if isinstance(content, list):
            image_paths = [p for p in content if os.path.splitext(p)[1].lower()
                            in (".png", ".jpg", ".jpeg", ".bmp", ".gif")]
            if not image_paths:
                self.status_var.set("В буфере обмена нет файлов-изображений.")
                return
            self._load_image_from_path(image_paths[0])
            return

        if isinstance(content, Image.Image):
            self.current_image = content
            self._update_preview()
            self.status_var.set("Изображение вставлено из буфера обмена.")
            return

        self.status_var.set("Не удалось распознать содержимое буфера обмена.")

    def _on_file_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        image_paths = [p for p in paths if os.path.splitext(p)[1].lower()
                        in (".png", ".jpg", ".jpeg", ".bmp", ".gif")]
        if not image_paths:
            self.status_var.set("Перетащенный файл не является изображением.")
            return
        self._load_image_from_path(image_paths[0])

    def _load_image_from_path(self, path):
        try:
            img = Image.open(path)
            img.load()
        except Exception as ex:
            self.status_var.set(f"Не удалось открыть файл: {ex}")
            return
        self.current_image = img
        self._update_preview()
        self.status_var.set(f"Изображение загружено: {os.path.basename(path)}")

    def _update_preview(self):
        if self.current_image is None:
            return
        preview = self.current_image.copy()
        preview.thumbnail(PREVIEW_MAX_SIZE)
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.drop_area.configure(image=self.preview_photo, text="")

    # ========================================================== Сохранение
    def _save_screenshot(self):
        if self.active_folder is None:
            messagebox.showwarning("Нет активной папки",
                                    "Сначала выберите или создайте папку слева.")
            return
        if self.current_image is None:
            messagebox.showwarning("Нет изображения",
                                    "Сначала вставьте (Ctrl+V) или перетащите скриншот.")
            return

        reason_raw = self.reason_var.get()
        reason = sanitize_filename(reason_raw) if reason_raw.strip() else "Без_причины"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{reason}_{timestamp}.png"
        dest_path = os.path.join(self.active_folder, filename)

        try:
            img = self.current_image
            img = img.convert("RGBA") if img.mode in ("RGBA", "P") else img.convert("RGB")
            img.save(dest_path, "PNG")
        except Exception as ex:
            messagebox.showerror("Ошибка сохранения", str(ex))
            return

        self.status_var.set(f"Сохранено: {filename}")
        self.reason_var.set("")
        self.current_image = None
        self.drop_area.configure(
            image="", text="Сюда можно перетащить картинку\nили нажать здесь и вставить Ctrl+V"
        )
        self.preview_photo = None


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ScreenshotOrganizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()