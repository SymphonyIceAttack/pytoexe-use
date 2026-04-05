import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, colorchooser
import json
import os
from PIL import Image, ImageTk, ImageDraw

# -------------------------- НАСТРОЙКИ ТЕМ --------------------------
THEMES = {
    "dark": {
        "bg": "#0a0a0a",
        "fg": "#d4d4d4",
        "frame_bg": "#121212",
        "entry_bg": "#1e1e1e",
        "button_bg": "#0e639c",
        "button_fg": "white",
        "accent": "#007acc",
        "select_bg": "#264f78",
        "text_bg": "#1e1e1e",
        "text_fg": "#d4d4d4",
        "canvas_bg": "#1e1e1e"
    },
    "light": {
        "bg": "#f3f3f3",
        "fg": "#333333",
        "frame_bg": "#e5e5e5",
        "entry_bg": "white",
        "button_bg": "#0066b8",
        "button_fg": "white",
        "accent": "#0066b8",
        "select_bg": "#cce5ff",
        "text_bg": "white",
        "text_fg": "#333333",
        "canvas_bg": "#ffffff"
    }
}

class Settings:
    def __init__(self):
        self.config_file = "zakulisie_settings.json"
        self.current_theme = "dark"
        self.keys = {"next_page": "s", "prev_page": "w"}
        self.slides_per_page = 9
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.current_theme = data.get("theme", "dark")
                    self.keys = data.get("keys", self.keys)
                    self.slides_per_page = data.get("slides_per_page", 9)
            except:
                pass

    def save(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"theme": self.current_theme, "keys": self.keys, "slides_per_page": self.slides_per_page}, f)
        except:
            pass

settings = Settings()

# -------------------------- МОДЕЛЬ СЛАЙДА --------------------------
class Slide:
    def __init__(self, title="Новый слайд", text="Текст слайда...", image_path=""):
        self.title = title
        self.text = text
        self.image_path = image_path

    def to_dict(self):
        return {"title": self.title, "text": self.text, "image_path": self.image_path}

    @classmethod
    def from_dict(cls, data):
        return cls(data["title"], data["text"], data["image_path"])

# -------------------------- ОКНО ПРОЕКТОРА (без текста "нет изображения") --------------------------
class ProjectorWindow:
    def __init__(self, master, get_image_path_callback):
        self.master = master
        self.get_image_path = get_image_path_callback
        self.window = None
        self.canvas = None
        self.current_photo = None
        self.image_id = None

    def open(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        self.window = tk.Toplevel(self.master)
        self.window.title("Проектор — Закулисье")
        self.window.configure(bg="black")
        self.window.attributes("-fullscreen", False)
        self.window.geometry("1024x768")
        self.window.bind("<Escape>", lambda e: self.close())
        self.window.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.window.bind("<Configure>", lambda e: self._resize_image())

        self.canvas = tk.Canvas(self.window, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._update_image()
        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def _toggle_fullscreen(self):
        self.window.attributes("-fullscreen", not self.window.attributes("-fullscreen"))
        self._resize_image()

    def close(self):
        if self.window:
            self.window.destroy()
            self.window = None

    def _update_image(self):
        if not self.window:
            return
        self.current_path = self.get_image_path()
        self._resize_image()

    def _resize_image(self):
        if not self.window or not self.canvas:
            return
        path = self.current_path
        # Очищаем канвас
        self.canvas.delete("all")
        if path and os.path.exists(path):
            try:
                w = max(10, self.canvas.winfo_width())
                h = max(10, self.canvas.winfo_height())
                img = Image.open(path)
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                self.current_photo = ImageTk.PhotoImage(img)
                x = (w - img.width) // 2
                y = (h - img.height) // 2
                self.image_id = self.canvas.create_image(max(0, x), max(0, y), anchor=tk.NW, image=self.current_photo)
            except Exception:
                pass  # не показываем текст, просто чёрный экран
        # иначе ничего не рисуем – чёрный экран

# -------------------------- РЕДАКТОР СЛАЙДА --------------------------
class SlideEditor:
    def __init__(self, parent, callback, slide=None, index=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Редактор слайда — Закулисье")
        self.window.geometry("700x600")
        self.callback = callback
        self.slide = slide if slide else Slide()
        self.index = index

        self.title_var = tk.StringVar(value=self.slide.title)
        self.image_path_var = tk.StringVar(value=self.slide.image_path)

        self._create_widgets()
        self._apply_theme()
        self._update_preview()

    def _create_widgets(self):
        main = tk.Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        tk.Label(main, text="Название слайда:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.title_entry = tk.Entry(main, textvariable=self.title_var, font=("Segoe UI", 10))
        self.title_entry.pack(fill=tk.X, pady=(0,10))

        tk.Label(main, text="Текст слайда:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.text_area = scrolledtext.ScrolledText(main, wrap=tk.WORD, height=10, font=("Consolas", 10))
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(0,10))
        self.text_area.insert(1.0, self.slide.text)

        img_frame = tk.Frame(main)
        img_frame.pack(fill=tk.X, pady=5)
        tk.Label(img_frame, text="Изображение:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.img_entry = tk.Entry(img_frame, textvariable=self.image_path_var, font=("Segoe UI", 10))
        self.img_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(img_frame, text="Обзор...", command=self._browse).pack(side=tk.RIGHT)

        self.preview = tk.Label(main, text="Предпросмотр", relief="sunken", height=10)
        self.preview.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="Сохранить", command=self._save, bg="#2e7d32", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy, bg="#8b0000", fg="white").pack(side=tk.LEFT, padx=5)

        self.image_path_var.trace_add("write", lambda *a: self._update_preview())

    def _apply_theme(self):
        theme = THEMES[settings.current_theme]
        self.window.configure(bg=theme["bg"])
        for child in self.window.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=theme["bg"])
        self.title_entry.configure(bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        self.text_area.configure(bg=theme["text_bg"], fg=theme["text_fg"])
        self.img_entry.configure(bg=theme["entry_bg"], fg=theme["fg"])
        self.preview.configure(bg=theme["frame_bg"], fg=theme["fg"])

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if path:
            self.image_path_var.set(path)

    def _update_preview(self):
        path = self.image_path_var.get()
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                img.thumbnail((500, 300))
                photo = ImageTk.PhotoImage(img)
                self.preview.config(image=photo, text="")
                self.preview.image = photo
            except:
                self.preview.config(image="", text="Ошибка загрузки")
        else:
            self.preview.config(image="", text="Нет изображения")

    def _save(self):
        self.slide.title = self.title_var.get()
        self.slide.text = self.text_area.get("1.0", tk.END).rstrip("\n")
        self.slide.image_path = self.image_path_var.get()
        self.callback(self.slide, self.index)
        self.window.destroy()

# -------------------------- РЕДАКТОР ПОРЯДКА СЛАЙДОВ --------------------------
class OrderEditor:
    def __init__(self, parent, slides, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Порядок слайдов — Закулисье")
        self.window.geometry("400x500")
        self.slides = slides[:]
        self.callback = callback
        self._create_widgets()
        self._apply_theme()

    def _create_widgets(self):
        tk.Label(self.window, text="Переместите слайды вверх/вниз:", font=("Segoe UI", 10)).pack(pady=5)
        self.listbox = tk.Listbox(self.window, font=("Segoe UI", 10), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for s in self.slides:
            self.listbox.insert(tk.END, s.title)
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="▲ Вверх", command=self._move_up, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="▼ Вниз", command=self._move_down, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сохранить", command=self._save, bg="green", fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def _apply_theme(self):
        theme = THEMES[settings.current_theme]
        self.window.configure(bg=theme["bg"])
        self.listbox.configure(bg=theme["entry_bg"], fg=theme["fg"], selectbackground=theme["select_bg"])

    def _move_up(self):
        sel = self.listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            item = self.slides.pop(idx)
            self.slides.insert(idx-1, item)
            self._refresh()
            self.listbox.selection_set(idx-1)

    def _move_down(self):
        sel = self.listbox.curselection()
        if sel and sel[0] < len(self.slides)-1:
            idx = sel[0]
            item = self.slides.pop(idx)
            self.slides.insert(idx+1, item)
            self._refresh()
            self.listbox.selection_set(idx+1)

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for s in self.slides:
            self.listbox.insert(tk.END, s.title)

    def _save(self):
        self.callback(self.slides)
        self.window.destroy()

# -------------------------- РЕДАКТОР ИЗОБРАЖЕНИЙ (PAINT) --------------------------
class PaintEditor:
    def __init__(self, parent, image_path, save_callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Редактор изображений — Закулисье")
        self.window.geometry("1000x700")
        self.image_path = image_path
        self.save_callback = save_callback
        self.current_image = None
        self.tk_image = None
        self.canvas = None
        self.drawing = False
        self.last_x, self.last_y = None, None
        self.pen_color = "#ff0000"
        self.pen_width = 3
        self.tool = "pen"
        self._load_image()
        self._create_widgets()
        self._apply_theme()

    def _load_image(self):
        if self.image_path and os.path.exists(self.image_path):
            self.current_image = Image.open(self.image_path).convert("RGBA")
        else:
            self.current_image = Image.new("RGBA", (800, 600), (255,255,255,255))
        self._update_display()

    def _create_widgets(self):
        toolbar = tk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        tools = [("Кисть", "pen"), ("Ластик", "eraser")]
        for name, cmd in tools:
            tk.Button(toolbar, text=name, command=lambda c=cmd: self._set_tool(c)).pack(side=tk.LEFT, padx=2)

        tk.Label(toolbar, text="Цвет:").pack(side=tk.LEFT, padx=(10,2))
        self.color_btn = tk.Button(toolbar, bg=self.pen_color, width=3, command=self._choose_color)
        self.color_btn.pack(side=tk.LEFT)

        tk.Label(toolbar, text="Толщина:").pack(side=tk.LEFT, padx=(10,2))
        self.width_spin = tk.Spinbox(toolbar, from_=1, to=20, width=3, command=self._update_width)
        self.width_spin.delete(0, tk.END)
        self.width_spin.insert(0, str(self.pen_width))
        self.width_spin.pack(side=tk.LEFT)

        tk.Button(toolbar, text="Очистить", command=self._clear).pack(side=tk.LEFT, padx=10)
        tk.Button(toolbar, text="Сохранить", command=self._save, bg="green", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Отмена", command=self.window.destroy).pack(side=tk.LEFT, padx=2)

        self.canvas = tk.Canvas(self.window, bg="gray", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Configure>", lambda e: self._update_display())

    def _apply_theme(self):
        theme = THEMES[settings.current_theme]
        self.window.configure(bg=theme["bg"])

    def _set_tool(self, tool):
        self.tool = tool

    def _choose_color(self):
        color = colorchooser.askcolor(color=self.pen_color)[1]
        if color:
            self.pen_color = color
            self.color_btn.config(bg=color)

    def _update_width(self):
        self.pen_width = int(self.width_spin.get())

    def _update_display(self):
        if not self.canvas:
            return
        self.canvas.update_idletasks()
        w = max(100, self.canvas.winfo_width())
        h = max(100, self.canvas.winfo_height())
        img_copy = self.current_image.copy()
        img_copy.thumbnail((w, h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(img_copy)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def _on_mouse_down(self, event):
        self.drawing = True
        self.last_x = self.canvas.canvasx(event.x)
        self.last_y = self.canvas.canvasy(event.y)

    def _on_mouse_move(self, event):
        if not self.drawing:
            return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if self.last_x is not None:
            scale_x = self.current_image.width / self.tk_image.width() if self.tk_image else 1
            scale_y = self.current_image.height / self.tk_image.height() if self.tk_image else 1
            x1, y1 = int(self.last_x * scale_x), int(self.last_y * scale_y)
            x2, y2 = int(x * scale_x), int(y * scale_y)
            draw = ImageDraw.Draw(self.current_image)
            if self.tool == "pen":
                draw.line([x1, y1, x2, y2], fill=self.pen_color, width=self.pen_width)
            elif self.tool == "eraser":
                draw.line([x1, y1, x2, y2], fill=(255,255,255,255), width=self.pen_width)
        self.last_x, self.last_y = x, y
        self._update_display()

    def _on_mouse_up(self, event):
        self.drawing = False
        self.last_x = None

    def _clear(self):
        self.current_image = Image.new("RGBA", self.current_image.size, (255,255,255,255))
        self._update_display()

    def _save(self):
        if not self.image_path:
            self.image_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if not self.image_path:
                return
        self.current_image.save(self.image_path)
        self.save_callback(self.image_path)
        messagebox.showinfo("Сохранено", f"Изображение сохранено")
        self.window.destroy()

# -------------------------- ДИАЛОГ НАСТРОЕК СТРАНИЦ --------------------------
class PageConfigDialog:
    def __init__(self, parent, current_value, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Параметры страниц — Закулисье")
        self.window.geometry("350x200")
        self.callback = callback
        self._create_widgets(current_value)
        self._apply_theme()

    def _create_widgets(self, current_value):
        main = tk.Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(main, text="Слайдов на странице:", font=("Segoe UI", 10)).pack(anchor="w", pady=(0,5))
        self.spin = tk.Spinbox(main, from_=1, to=50, width=10, font=("Segoe UI", 10))
        self.spin.delete(0, tk.END)
        self.spin.insert(0, str(current_value))
        self.spin.pack(anchor="w", pady=(0,20))

        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Применить", command=self._save, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def _apply_theme(self):
        theme = THEMES[settings.current_theme]
        self.window.configure(bg=theme["bg"])
        self.spin.configure(bg=theme["entry_bg"], fg=theme["fg"], buttonbackground=theme["button_bg"])

    def _save(self):
        try:
            val = int(self.spin.get())
            if val < 1:
                val = 1
            self.callback(val)
        except:
            pass
        self.window.destroy()

# -------------------------- ГЛАВНОЕ ПРИЛОЖЕНИЕ --------------------------
class ZakulisieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Закулисье — D&D Slide Master")
        self.root.geometry("1200x850")
        self.root.minsize(800, 600)

        self.slides = []
        self.current_index = -1
        self.projector = None
        self.page = 0  # текущая страница предпросмотра

        self._create_menu()
        self._create_notebook()
        self._bind_keys()
        self._load_last_project()
        self._apply_theme()

    # ---------- ТЕМА ----------
    def _apply_theme(self):
        theme = THEMES[settings.current_theme]
        self.root.configure(bg=theme["bg"])
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=theme["frame_bg"], foreground=theme["fg"], padding=[10,5])
        style.map("TNotebook.Tab", background=[("selected", theme["accent"])])
        self._refresh_preview_panel()

    def _toggle_theme(self):
        settings.current_theme = "light" if settings.current_theme == "dark" else "dark"
        settings.save()
        self._apply_theme()
        self._update_current_display()

    # ---------- НАСТРОЙКИ КЛАВИШ ----------
    def _open_key_settings(self):
        def save_keys(new_keys):
            settings.keys = new_keys
            settings.save()
            self._bind_keys()
        KeyConfigDialog(self.root, settings.keys, save_keys)

    # ---------- НАСТРОЙКИ СТРАНИЦ ----------
    def _open_page_settings(self):
        def save_per_page(val):
            settings.slides_per_page = val
            settings.save()
            # Пересчитываем текущую страницу, чтобы текущий слайд оставался видимым
            if self.slides:
                new_page = self.current_index // settings.slides_per_page if self.current_index >= 0 else 0
                self.page = new_page
            else:
                self.page = 0
            self._refresh_preview_panel()
        PageConfigDialog(self.root, settings.slides_per_page, save_per_page)

    # ---------- ПРИНУДИТЕЛЬНОЕ СОЗДАНИЕ НОВОЙ СТРАНИЦЫ ----------
    def _add_new_page(self):
        """Добавляет slides_per_page пустых слайдов в конец списка."""
        count = settings.slides_per_page
        start_index = len(self.slides)
        for i in range(count):
            new_slide = Slide(title=f"Слайд {start_index + i + 1}", text="", image_path="")
            self.slides.append(new_slide)
        # Переключаемся на первый добавленный слайд
        if self.slides:
            self.current_index = start_index
            # Корректируем страницу
            self.page = self.current_index // settings.slides_per_page
            self._update_current_display()
            self._update_projector()
            self._refresh_preview_panel()
            messagebox.showinfo("Страница создана", f"Добавлено {count} новых слайдов.\nТеперь у вас {len(self.slides)} слайдов.")

    # ---------- МЕНЮ ----------
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Новый проект", command=self._new_project)
        file_menu.add_command(label="Открыть проект...", command=self._open_project)
        file_menu.add_command(label="Сохранить проект", command=self._save_project)
        file_menu.add_command(label="Сохранить как...", command=self._save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        slide_menu = tk.Menu(menubar, tearoff=0)
        slide_menu.add_command(label="Добавить слайд", command=self._add_slide)
        slide_menu.add_command(label="Редактировать текущий слайд", command=self._edit_current_slide)
        slide_menu.add_command(label="Удалить текущий слайд", command=self._delete_current_slide)
        slide_menu.add_command(label="Порядок слайдов", command=self._reorder_slides)
        slide_menu.add_separator()
        slide_menu.add_command(label="Создать новую страницу", command=self._add_new_page)
        menubar.add_cascade(label="Слайд", menu=slide_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Показать на проекторе", command=self._open_projector)
        menubar.add_cascade(label="Вид", menu=view_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Тёмная тема" if settings.current_theme == "light" else "Светлая тема", command=self._toggle_theme)
        settings_menu.add_command(label="Настройки клавиш", command=self._open_key_settings)
        settings_menu.add_command(label="Параметры страниц", command=self._open_page_settings)
        menubar.add_cascade(label="Настройки", menu=settings_menu)

        self.root.config(menu=menubar)

    # ---------- ВКЛАДКИ ----------
    def _create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.view_frame = tk.Frame(self.notebook)
        self.notebook.add(self.view_frame, text="📖 Просмотр")
        self._build_view_tab()

        self.paint_frame = tk.Frame(self.notebook)
        self.notebook.add(self.paint_frame, text="🎨 Редактор")
        self._build_paint_tab()

    def _build_view_tab(self):
        self.title_label = tk.Label(self.view_frame, font=("Segoe UI", 18, "bold"))
        self.title_label.pack(pady=(10,5))

        img_container = tk.Frame(self.view_frame)
        img_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(img_container, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll = ttk.Scrollbar(img_container, orient=tk.VERTICAL, command=self.canvas.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=v_scroll.set)

        self.text_area = scrolledtext.ScrolledText(self.view_frame, wrap=tk.WORD, font=("Consolas", 11))
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5,10))
        self.text_area.config(state=tk.DISABLED)

        preview_container = tk.Frame(self.view_frame)
        preview_container.pack(fill=tk.X, padx=10, pady=5)
        self.preview_canvas = tk.Canvas(preview_container, height=60, highlightthickness=0)
        self.preview_scrollbar = ttk.Scrollbar(preview_container, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        self.preview_canvas.configure(xscrollcommand=self.preview_scrollbar.set)
        self.preview_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.preview_canvas.pack(side=tk.TOP, fill=tk.X)
        self.preview_frame = tk.Frame(self.preview_canvas)
        self.preview_canvas.create_window((0,0), window=self.preview_frame, anchor=tk.NW)
        self.preview_frame.bind("<Configure>", self._on_preview_configure)
        self.preview_canvas.bind("<Configure>", self._on_preview_canvas_configure)

        page_nav_frame = tk.Frame(self.view_frame)
        page_nav_frame.pack(fill=tk.X, pady=2)
        self.page_label = tk.Label(page_nav_frame, text="", font=("Segoe UI", 9))
        self.page_label.pack(side=tk.LEFT, padx=5)
        self.prev_page_btn = tk.Button(page_nav_frame, text="◀ Пред. страница", command=self._prev_page, width=15)
        self.prev_page_btn.pack(side=tk.LEFT, padx=2)
        self.next_page_btn = tk.Button(page_nav_frame, text="След. страница ▶", command=self._next_page, width=15)
        self.next_page_btn.pack(side=tk.LEFT, padx=2)

        nav_frame = tk.Frame(self.view_frame)
        nav_frame.pack(pady=5)
        self.prev_btn = tk.Button(nav_frame, text="◀ Предыдущий слайд", command=self._prev_slide, width=15)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        self.next_btn = tk.Button(nav_frame, text="Следующий слайд ▶", command=self._next_slide, width=15)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        self.slide_info = tk.Label(self.view_frame, font=("Segoe UI", 10))
        self.slide_info.pack(pady=2)

        hint = tk.Label(self.view_frame, text="💡 Цифры 1-9 для выбора слайда на текущей странице, S/W для смены страницы, стрелки влево/вправо", font=("Segoe UI", 9))
        hint.pack(pady=2)

    def _build_paint_tab(self):
        tk.Label(self.paint_frame, text="Редактор изображений", font=("Segoe UI", 14)).pack(pady=20)
        tk.Label(self.paint_frame, text="Откройте текущее изображение слайда для рисования.", wraplength=500).pack()
        self.paint_btn = tk.Button(self.paint_frame, text="Открыть редактор для текущего слайда", command=self._open_paint_editor, bg="#0e639c", fg="white", padx=10, pady=5)
        self.paint_btn.pack(pady=20)

    # ---------- ПАНЕЛЬ ПРЕДПРОСМОТРА ----------
    def _update_page_controls(self):
        total_pages = (len(self.slides) + settings.slides_per_page - 1) // settings.slides_per_page if self.slides else 1
        self.page_label.config(text=f"Страница {self.page+1} из {max(1, total_pages)}")
        self.prev_page_btn.config(state=tk.NORMAL if self.page > 0 else tk.DISABLED)
        self.next_page_btn.config(state=tk.NORMAL if (self.page+1)*settings.slides_per_page < len(self.slides) else tk.DISABLED)

    def _refresh_preview_panel(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()
        theme = THEMES[settings.current_theme]
        self.preview_frame.configure(bg=theme["bg"])
        start = self.page * settings.slides_per_page
        end = min(start + settings.slides_per_page, len(self.slides))
        for idx in range(start, end):
            slide = self.slides[idx]
            text = f"{idx+1}. {slide.title[:25]}{'...' if len(slide.title)>25 else ''}"
            btn = tk.Button(self.preview_frame, text=text, command=lambda i=idx: self._go_to_slide(i+1),
                            bg=theme["button_bg"], fg=theme["button_fg"], padx=5, pady=2)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        self._update_page_controls()
        self._on_preview_configure()

    def _next_page(self):
        if (self.page + 1) * settings.slides_per_page < len(self.slides):
            self.page += 1
            self._refresh_preview_panel()

    def _prev_page(self):
        if self.page > 0:
            self.page -= 1
            self._refresh_preview_panel()

    def _on_preview_configure(self, event=None):
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def _on_preview_canvas_configure(self, event):
        self.preview_canvas.itemconfig(1, width=event.width)

    # ---------- НАВИГАЦИЯ И ОТОБРАЖЕНИЕ ----------
    def _bind_keys(self):
        self.root.unbind_all("<Key>")
        self.root.bind_all("<Key>", self._on_key)

    def _on_key(self, event):
        if event.char.isdigit():
            num = int(event.char)
            start = self.page * settings.slides_per_page
            if 1 <= num <= settings.slides_per_page and start + num - 1 < len(self.slides):
                self._go_to_slide(start + num)
            return
        if event.keysym == "Right":
            self._next_slide()
        elif event.keysym == "Left":
            self._prev_slide()
        if event.char == settings.keys["next_page"]:
            self._next_page()
        elif event.char == settings.keys["prev_page"]:
            self._prev_page()

    def _go_to_slide(self, number):
        self.current_index = number - 1
        self._update_current_display()
        self._update_projector()

    def _next_slide(self):
        if self.current_index + 1 < len(self.slides):
            self.current_index += 1
            self._update_current_display()
            self._update_projector()

    def _prev_slide(self):
        if self.current_index - 1 >= 0:
            self.current_index -= 1
            self._update_current_display()
            self._update_projector()

    def _update_current_display(self):
        if not self.slides or self.current_index < 0:
            self._clear_display()
            return
        slide = self.slides[self.current_index]
        self.title_label.config(text=slide.title)
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, slide.text)
        self.text_area.config(state=tk.DISABLED)
        self._show_image(slide.image_path)
        self.slide_info.config(text=f"Слайд {self.current_index+1} из {len(self.slides)}")
        self.root.title(f"Закулисье — {slide.title}")
        self.prev_btn.config(state=tk.NORMAL if self.current_index>0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index<len(self.slides)-1 else tk.DISABLED)
        self._refresh_preview_panel()

    def _show_image(self, path):
        if hasattr(self, "image_on_canvas") and self.image_on_canvas:
            self.canvas.delete(self.image_on_canvas)
        if path and os.path.exists(path):
            self.current_image_path = path
            self.root.after(50, self._load_and_scale)
        else:
            # ничего не рисуем – просто чёрный фон
            pass

    def _load_and_scale(self):
        if not self.canvas.winfo_exists():
            return
        w = max(100, self.canvas.winfo_width())
        h = max(100, self.canvas.winfo_height())
        try:
            img = Image.open(self.current_image_path)
            img.thumbnail((w, h), Image.Resampling.LANCZOS)
            self.current_photo = ImageTk.PhotoImage(img)
            self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass  # не показываем текст

    def _clear_display(self):
        self.title_label.config(text="Нет слайдов")
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Добавьте слайды через меню 'Слайд -> Добавить слайд'")
        self.text_area.config(state=tk.DISABLED)
        if hasattr(self, "image_on_canvas") and self.image_on_canvas:
            self.canvas.delete(self.image_on_canvas)
        self.slide_info.config(text="Слайд 0 из 0")
        self.root.title("Закулисье")

    # ---------- ПРОЕКТОР ----------
    def _open_projector(self):
        if not self.slides:
            messagebox.showinfo("Нет слайдов", "Сначала добавьте слайд.")
            return
        if self.projector is None or not self.projector.window:
            self.projector = ProjectorWindow(self.root, self._get_current_image_path)
        self.projector.open()
        self._update_projector()

    def _get_current_image_path(self):
        if self.slides and 0 <= self.current_index < len(self.slides):
            return self.slides[self.current_index].image_path
        return ""

    def _update_projector(self):
        if self.projector and self.projector.window:
            self.projector._update_image()

    # ---------- РЕДАКТОР ИЗОБРАЖЕНИЙ ----------
    def _open_paint_editor(self):
        if not self.slides or self.current_index < 0:
            messagebox.showinfo("Нет слайда", "Выберите слайд для редактирования.")
            return
        slide = self.slides[self.current_index]
        def after_save(new_path):
            slide.image_path = new_path
            self._update_current_display()
            self._save_project()
        PaintEditor(self.root, slide.image_path, after_save)

    # ---------- УПРАВЛЕНИЕ СЛАЙДАМИ ----------
    def _add_slide(self, slide=None, index=None):
        def callback(new_slide, idx):
            if idx is None:
                self.slides.append(new_slide)
                self.current_index = len(self.slides)-1
            else:
                self.slides[idx] = new_slide
                self.current_index = idx
            # Корректируем страницу, чтобы текущий слайд был виден
            page_needed = self.current_index // settings.slides_per_page if self.current_index >= 0 else 0
            if page_needed != self.page:
                self.page = page_needed
            self._update_current_display()
            self._update_projector()
        SlideEditor(self.root, callback, slide, index)

    def _edit_current_slide(self):
        if not self.slides:
            return
        self._add_slide(self.slides[self.current_index], self.current_index)

    def _delete_current_slide(self):
        if not self.slides:
            return
        if messagebox.askyesno("Удалить", f"Удалить слайд '{self.slides[self.current_index].title}'?"):
            del self.slides[self.current_index]
            if not self.slides:
                self.current_index = -1
                self._clear_display()
            else:
                if self.current_index >= len(self.slides):
                    self.current_index = len(self.slides)-1
                self._update_current_display()
            self._update_projector()

    def _reorder_slides(self):
        if not self.slides:
            return
        def callback(new_order):
            self.slides = new_order
            self.current_index = 0
            self.page = 0
            self._update_current_display()
            self._update_projector()
        OrderEditor(self.root, self.slides, callback)

    # ---------- ФАЙЛЫ ----------
    def _save_to_file(self, filename):
        try:
            data = [s.to_dict() for s in self.slides]
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.current_file = filename
            messagebox.showinfo("Сохранено", f"Проект сохранён в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _load_from_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.slides = [Slide.from_dict(d) for d in data]
            self.current_index = 0 if self.slides else -1
            self.current_file = filename
            self.page = self.current_index // settings.slides_per_page if self.current_index >= 0 else 0
            self._update_current_display()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            self._create_demo_slides()

    def _create_demo_slides(self):
        self.slides = [
            Slide("Добро пожаловать в «Закулисье»",
                  "Нажмите 'Слайд → Добавить слайд' чтобы создать презентацию.\n\nПоддерживаются PNG, JPG, GIF.\n\nИспользуйте 'Вид → Показать на проекторе'.\n\nМеняйте порядок слайдов и рисуйте в редакторе.\n\nВ настройках можно изменить количество слайдов на странице.", ""),
            Slide("Пример слайда", "Здесь может быть описание сцены, текст приключения или заметки.", "")
        ]
        self.current_index = 0
        self.page = 0
        self._update_current_display()

    def _load_last_project(self):
        if os.path.exists("last_project.json"):
            self._load_from_file("last_project.json")
        else:
            self._create_demo_slides()

    def _save_project(self):
        if hasattr(self, "current_file") and self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._save_project_as()

    def _save_project_as(self):
        f = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if f:
            self._save_to_file(f)

    def _open_project(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if f:
            self._load_from_file(f)

    def _new_project(self):
        if messagebox.askyesno("Новый проект", "Потерять текущие слайды?"):
            self.slides = []
            self.current_index = -1
            self.page = 0
            self._clear_display()
            if self.projector:
                self.projector.close()

# -------------------------- ДИАЛОГ НАСТРОЕК КЛАВИШ --------------------------
class KeyConfigDialog:
    def __init__(self, parent, current_keys, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Настройки клавиш — Закулисье")
        self.window.geometry("400x250")
        self.current_keys = current_keys.copy()
        self.callback = callback
        self._create_widgets()
        self._apply_theme()

    def _create_widgets(self):
        main = tk.Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(main, text="Следующая страница слайдов (S):", font=("Segoe UI", 10)).pack(anchor="w")
        self.next_entry = tk.Entry(main, width=5, justify="center", font=("Segoe UI", 10))
        self.next_entry.insert(0, self.current_keys["next_page"])
        self.next_entry.pack(anchor="w", pady=(0,10))

        tk.Label(main, text="Предыдущая страница слайдов (W):", font=("Segoe UI", 10)).pack(anchor="w")
        self.prev_entry = tk.Entry(main, width=5, justify="center", font=("Segoe UI", 10))
        self.prev_entry.insert(0, self.current_keys["prev_page"])
        self.prev_entry.pack(anchor="w", pady=(0,20))

        btn_frame = tk.Frame(main)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Сохранить", command=self._save, bg="green", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def _apply_theme(self):
        theme = THEMES[settings.current_theme]
        self.window.configure(bg=theme["bg"])
        self.next_entry.configure(bg=theme["entry_bg"], fg=theme["fg"])
        self.prev_entry.configure(bg=theme["entry_bg"], fg=theme["fg"])

    def _save(self):
        new_keys = {
            "next_page": self.next_entry.get().strip().lower(),
            "prev_page": self.prev_entry.get().strip().lower()
        }
        if new_keys["next_page"] and new_keys["prev_page"]:
            self.callback(new_keys)
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ZakulisieApp(root)
    root.mainloop()