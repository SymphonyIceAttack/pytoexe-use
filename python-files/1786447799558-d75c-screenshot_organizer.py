# -*- coding: utf-8 -*-
"""
Организатор скриншотов
=======================
Программа для Windows:
- Базовая папка "Администрация" создаётся на Рабочем столе автоматически.
- Внутри неё можно создавать/выбирать подпапки (темы), например "Dev_Test".
- В выбранную (активную) папку можно добавить скриншот двумя способами:
    1) Ctrl+V - вставка картинки из буфера обмена (после Win+Shift+S / PrtScn)
    2) Перетаскивание файла картинки мышкой в окно программы
- Перед сохранением нужно ввести "Причину" - она станет частью имени файла.

Автор структуры: сгенерировано по ТЗ пользователя.
"""

import os
import re
import sys
import shutil
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageGrab, ImageTk

# Для drag-and-drop нужен пакет tkinterdnd2 (pip install tkinterdnd2)
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


BASE_FOLDER_NAME = "Администрация"
PREVIEW_MAX_SIZE = (360, 220)


def get_desktop_path() -> str:
    """Возвращает путь к Рабочему столу пользователя в Windows."""
    # Стандартный путь для большинства систем Windows
    userprofile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop = os.path.join(userprofile, "Desktop")
    if os.path.isdir(desktop):
        return desktop
    # На случай, если Рабочий стол переопределён (OneDrive и т.п.)
    return os.path.expanduser("~/Desktop")


def sanitize_filename(name: str) -> str:
    """Убирает символы, недопустимые в именах файлов/папок Windows."""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip(" .") or "Без_названия"


class ScreenshotOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Организатор скриншотов — Администрация")
        self.root.geometry("760x480")
        self.root.minsize(680, 440)

        self.base_dir = os.path.join(get_desktop_path(), BASE_FOLDER_NAME)
        os.makedirs(self.base_dir, exist_ok=True)

        self.active_folder = None          # полный путь к активной теме
        self.current_image = None          # PIL.Image, ожидающий сохранения
        self.current_image_path_hint = None  # если пришло из файла (drag&drop)
        self.preview_photo = None          # ссылка на PhotoImage, чтобы не удалился GC

        self._build_ui()
        self._refresh_topic_list()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(1, weight=1)

        # --- Левая колонка: темы ---
        left = ttk.Frame(main)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text=f"Базовая папка:\n{self.base_dir}",
                  wraplength=250, foreground="#555").grid(row=0, column=0, sticky="w", pady=(0, 8))

        new_topic_frame = ttk.Frame(left)
        new_topic_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        new_topic_frame.columnconfigure(0, weight=1)

        self.new_topic_var = tk.StringVar()
        self.new_topic_entry = ttk.Entry(new_topic_frame, textvariable=self.new_topic_var)
        self.new_topic_entry.grid(row=0, column=0, sticky="ew")
        self.new_topic_entry.bind("<Return>", lambda e: self._create_or_select_topic())

        ttk.Button(new_topic_frame, text="Создать/выбрать",
                   command=self._create_or_select_topic).grid(row=0, column=1, padx=(6, 0))

        ttk.Label(left, text="Существующие темы:").grid(row=2, column=0, sticky="sw")

        list_frame = ttk.Frame(left)
        list_frame.grid(row=3, column=0, sticky="nsew", pady=(2, 0))
        left.rowconfigure(3, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        self.topics_listbox = tk.Listbox(list_frame, exportselection=False)
        self.topics_listbox.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.topics_listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.topics_listbox.configure(yscrollcommand=scroll.set)
        self.topics_listbox.bind("<<ListboxSelect>>", self._on_topic_selected)

        ttk.Button(left, text="Обновить список",
                   command=self._refresh_topic_list).grid(row=4, column=0, sticky="ew", pady=(6, 0))

        # --- Правая колонка: активная тема + скриншот ---
        right = ttk.Frame(main)
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.active_label_var = tk.StringVar(value="Активная тема: не выбрана")
        ttk.Label(right, textvariable=self.active_label_var,
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))

        drop_border = tk.Frame(right, bg="#999999", bd=0)
        drop_border.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        drop_border.rowconfigure(0, weight=1)
        drop_border.columnconfigure(0, weight=1)

        self.drop_area = tk.Label(
            drop_border,
            text="Сюда можно перетащить картинку\nили нажать здесь и вставить Ctrl+V",
            bg="#f4f4f4", fg="#666666", justify="center",
            relief="flat", bd=1
        )
        self.drop_area.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)

        # Клик по зоне даёт ей фокус, чтобы Ctrl+V сработал
        self.drop_area.bind("<Button-1>", lambda e: self.drop_area.focus_set())
        self.drop_area.focus_set()

        # Горячая клавиша вставки — вешаем на всё окно, чтобы работало всегда
        self.root.bind_all("<Control-v>", self._paste_from_clipboard)

        if DND_AVAILABLE:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self._on_file_drop)
        else:
            self.drop_area.configure(
                text=self.drop_area.cget("text") +
                "\n\n(перетаскивание недоступно: не установлен пакет tkinterdnd2)"
            )

        # --- причина + сохранить ---
        bottom = ttk.Frame(right)
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, text="Причина:").grid(row=0, column=0, sticky="w")
        self.reason_var = tk.StringVar()
        self.reason_entry = ttk.Entry(bottom, textvariable=self.reason_var)
        self.reason_entry.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.reason_entry.bind("<Return>", lambda e: self._save_screenshot())

        self.save_button = ttk.Button(bottom, text="Сохранить скриншот",
                                       command=self._save_screenshot)
        self.save_button.grid(row=1, column=1, padx=(6, 0))

        self.status_var = tk.StringVar(value="Готово.")
        ttk.Label(right, textvariable=self.status_var, foreground="#0a6").grid(
            row=3, column=0, sticky="w", pady=(6, 0))

    # ------------------------------------------------------------ Темы
    def _refresh_topic_list(self):
        self.topics_listbox.delete(0, tk.END)
        try:
            entries = sorted(
                e for e in os.listdir(self.base_dir)
                if os.path.isdir(os.path.join(self.base_dir, e))
            )
        except FileNotFoundError:
            entries = []
        for e in entries:
            self.topics_listbox.insert(tk.END, e)

        # если активная папка всё ещё существует — подсветим её в списке
        if self.active_folder:
            name = os.path.basename(self.active_folder)
            if name in entries:
                idx = entries.index(name)
                self.topics_listbox.selection_set(idx)

    def _create_or_select_topic(self):
        raw_name = self.new_topic_var.get()
        if not raw_name.strip():
            messagebox.showwarning("Тема не указана", "Введите название темы.")
            return
        name = sanitize_filename(raw_name)
        folder = os.path.join(self.base_dir, name)
        os.makedirs(folder, exist_ok=True)
        self.active_folder = folder
        self.active_label_var.set(f"Активная тема: {name}")
        self.status_var.set(f"Папка «{name}» создана/выбрана как активная.")
        self.new_topic_var.set("")
        self._refresh_topic_list()

    def _on_topic_selected(self, event):
        selection = self.topics_listbox.curselection()
        if not selection:
            return
        name = self.topics_listbox.get(selection[0])
        self.active_folder = os.path.join(self.base_dir, name)
        self.active_label_var.set(f"Активная тема: {name}")
        self.status_var.set(f"Выбрана папка «{name}».")

    # ------------------------------------------------------ Приём картинки
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
            # Буфер содержит пути к файлам (например, скопирован файл в проводнике)
            image_paths = [p for p in content if os.path.splitext(p)[1].lower()
                            in (".png", ".jpg", ".jpeg", ".bmp", ".gif")]
            if not image_paths:
                self.status_var.set("В буфере обмена нет файлов-изображений.")
                return
            self._load_image_from_path(image_paths[0])
            return

        if isinstance(content, Image.Image):
            self.current_image = content
            self.current_image_path_hint = None
            self._update_preview()
            self.status_var.set("Изображение вставлено из буфера обмена.")
            return

        self.status_var.set("Не удалось распознать содержимое буфера обмена.")

    def _on_file_drop(self, event):
        # event.data может содержать несколько путей в фигурных скобках
        raw = event.data
        paths = self.root.tk.splitlist(raw)
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
        self.current_image_path_hint = path
        self._update_preview()
        self.status_var.set(f"Изображение загружено: {os.path.basename(path)}")

    def _update_preview(self):
        if self.current_image is None:
            return
        preview = self.current_image.copy()
        preview.thumbnail(PREVIEW_MAX_SIZE)
        self.preview_photo = ImageTk.PhotoImage(preview)
        self.drop_area.configure(image=self.preview_photo, text="")

    # ---------------------------------------------------------- Сохранение
    def _save_screenshot(self):
        if self.active_folder is None:
            messagebox.showwarning("Нет активной темы",
                                    "Сначала создайте или выберите папку темы слева.")
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
            # Если изображение пришло из файла и это уже PNG — можно просто скопировать,
            # но проще и надёжнее всегда пересохранить через PIL.
            rgb_image = self.current_image
            if rgb_image.mode in ("RGBA", "P"):
                rgb_image = rgb_image.convert("RGBA")
            else:
                rgb_image = rgb_image.convert("RGB")
            rgb_image.save(dest_path, "PNG")
        except Exception as ex:
            messagebox.showerror("Ошибка сохранения", str(ex))
            return

        self.status_var.set(f"Сохранено: {filename}")
        self.reason_var.set("")
        self.current_image = None
        self.current_image_path_hint = None
        self.drop_area.configure(
            image="",
            text="Сюда можно перетащить картинку\nили нажать здесь и вставить Ctrl+V"
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
