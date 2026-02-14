import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from urllib.parse import quote_plus


def build_dork(params: dict) -> str:
    """
    Build a Yandex-compatible search query (dork) from the provided params.
    This mirrors the advanced options on https://suip.biz/ru/?act=yandex-search
    but runs locally so it can be shipped as an .exe later.
    """
    parts = []

    # Base search phrase
    if params["query"]:
        parts.append(params["query"])

    # Exact phrase
    if params["exact"]:
        parts.append(f'"{params["exact"]}"')

    # Words that must NOT appear
    if params["exclude"]:
        for word in params["exclude"].replace(",", " ").split():
            parts.append(f'-"{word}"')

    # Required in title / URL / body
    if params["intitle"]:
        parts.append(f'intitle:"{params["intitle"]}"')
    if params["inurl"]:
        parts.append(f'inurl:"{params["inurl"]}"')
    if params["intext"]:
        parts.append(f'intext:"{params["intext"]}"')

    # Domain / site scoping
    if params["site"]:
        parts.append(f'site:{params["site"]}')
    if params["domain"]:
        parts.append(f'domain:{params["domain"]}')
    if params["url"]:
        parts.append(f'url:{params["url"]}')

    # File types (support multiple)
    exts = params.get("filetypes") or []
    if isinstance(exts, str):
        exts = [exts] if exts else []
    exts = [e for e in exts if e]
    if len(exts) == 1:
        parts.append(f'filetype:{exts[0]}')
    elif len(exts) > 1:
        joined = " OR ".join([f'filetype:{e}' for e in exts])
        parts.append(f"({joined})")

    # Remove empties and join
    return " ".join(filter(None, parts)).strip()


# Предустановленные шаблоны дорков
DORK_TEMPLATES = {
    "Конфиденциальные файлы и данные": {
        "Файлы с паролями и ключами": [
            'filetype:env "{query:DB_PASSWORD}"',
            '"{query:API_KEY}" ext:txt',
            '"{query:password}" filetype:log'
        ],
        "Резервные копии (бэкапы)": [
            'filetype:bak',
            'filetype:sql',
            'inurl:"{query:backup}"',
            '"{query:backup}" ext:zip'
        ],
        "Конфигурационные файлы": [
            'filetype:config',
            'inurl:"{query:config.php}"',
            '"{query:config}" ext:yml'
        ],
        "Базы данных": [
            'filetype:mdb | ext:sqlite',
            '"{query:db}" ext:db'
        ],
        "Ключи шифрования и сертификаты": [
            'filetype:pem | ext:key | ext:pfx',
            '"{query:BEGIN RSA PRIVATE KEY}"'
        ],
        "Документы с персональными данными": [
            'filetype:xls "{query:паспорт}"',
            '"{query:сотрудники}" filetype:pdf'
        ]
    },
    "Уязвимые или открытые веб-интерфейсы": {
        "Панели администратора": [
            'intitle:"{query:admin login}"',
            'inurl:"{query:/admin/}"',
            'inurl:"{query:wp-admin}"'
        ],
        "Системы управления (CMS)": [
            'inurl:"{query:/phpmyadmin/}"',
            'intitle:"{query:WSO}"',
            '"{query:Powered by Wordpress}" inurl:{query:wp-login}'
        ],
        "Веб-интерфейсы оборудования": [
            'intitle:"{query:DVR Login}"',
            'inurl:"{query:/cgi-bin/login.cgi}"'
        ],
        "Системы мониторинга": [
            'intitle:"{query:Grafana}" "{query:login}"',
            'inurl:"{query:/zabbix/}"'
        ]
    },
    "Уязвимости в веб-приложениях": {
        "SQL-инъекции": [
            'inurl:"{query:id=}"',
            'inurl:"{query:?cat=}"',
            'inurl:"{query:page_id=}"'
        ],
        "LFI/RFI": [
            'inurl:"{query:include=}"',
            'inurl:"{query:page=}"',
            'inurl:"{query:file=}"'
        ],
        "Открытые каталоги": [
            'intitle:"index of"',
            '"parent directory" filetype:{query:mp4}'
        ],
        "Страницы с ошибками": [
            '"{query:Internal Server Error}"',
            '"{query:PHP Error}"',
            '"{query:MySQL Error}"'
        ]
    },
    "Сетевое оборудование и IoT-устройства": {
        "Веб-камеры": [
            'inurl:"{query:/view.shtml}"',
            'intitle:"{query:Live View / - AXIS}"',
            'inurl:"{query:axis-cgi/mjpg}"'
        ],
        "Принтеры, роутеры": [
            'intitle:"{query:Printer Status}"',
            'inurl:"{query:/hp/device/this.LCDispatcher}"'
        ],
        "Системы умного дома": [
            'inurl:"{query:/home.html}" intitle:"{query:Smart}"'
        ]
    },
    "Информация для OSINT": {
        "Документы организации": [
            'site:{site} filetype:docx "{query:отчёт}"'
        ],
        "Файлы с метаданными": [
            'filetype:docx "Author:{author:}" "Company:{company:}"'
        ],
        "Логи и отчеты": [
            '"{query:error}" "{query:git}" "{query:pull}" filetype:log'
        ],
        "Публичные дашборды": [
            'intitle:"Dashboard" "{query:Kibana}"',
            'intitle:"Dashboard" "{query:Power BI}"'
        ]
    },
    "Различные типы медиа-файлов": {
        "Медиафайлы": [
            'filetype:mp4 | filetype:flv | filetype:avi'
        ],
        "Прямые ссылки на изображения": [
            'filetype:jpg "{query:family}" site:{site}'
        ],
        "Файлы для скачивания": [
            'intitle:"index of" {query:*.mkv}'
        ]
    },
    "Информационные утечки": {
        "Контакты": [
            '"@{domain}" filetype:xlsx',
            '"tel:" "mailto:" site:{site}'
        ],
        "Информация для восстановления": [
            '"{query:Ваш логин:}" "{query:пароль:}"'
        ],
        "Служебная информация": [
            '"{query:TODO}" "{query:FIXME}" "{query:token}" site:{site}'
        ]
    }
}


class DorkBuilderUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yandex Dork Builder")
        self.geometry("1000x720")
        self.resizable(True, True)

        self.state = {
            "query": tk.StringVar(),
            "exact": tk.StringVar(),
            "exclude": tk.StringVar(),
            "site": tk.StringVar(),
            "url": tk.StringVar(),
            "domain": tk.StringVar(),
            "intitle": tk.StringVar(),
            "inurl": tk.StringVar(),
            "intext": tk.StringVar(),
        }
        self.filetype_options = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "json", "xml", "sql", "log", "env", "bak", "config", "mdb", "pem", "key", "pfx", "db", "sqlite", "yml", "mp4", "flv", "avi", "jpg", "mkv"]
        self.filetype_vars = {ft: tk.BooleanVar(value=False) for ft in self.filetype_options}
        self.filetype_checks = []
        self.enabled = {k: tk.BooleanVar(value=(k == "query")) for k in self.state}
        self.enabled["filetypes"] = tk.BooleanVar(value=False)
        self.inputs = {}

        # Переменные для вкладки шаблонов
        self.template_state = {
            "query": tk.StringVar(),
            "exact": tk.StringVar(),
            "exclude": tk.StringVar(),
            "site": tk.StringVar(),
            "url": tk.StringVar(),
            "domain": tk.StringVar(),
            "intitle": tk.StringVar(),
            "inurl": tk.StringVar(),
            "intext": tk.StringVar(),
        }
        self.template_filetype_vars = {ft: tk.BooleanVar(value=False) for ft in self.filetype_options}
        self.template_filetype_checks = []
        self.template_enabled = {k: tk.BooleanVar(value=False) for k in self.template_state}
        self.template_enabled["filetypes"] = tk.BooleanVar(value=False)
        self.template_inputs = {}
        self.template_dork_vars = {}  # Для чекбоксов дорков выбранной подкатегории
        self.selected_category_index = None  # Сохраняем индекс выбранной категории
        # Переменные для плейсхолдеров в шаблонах
        self.template_placeholders = {
            "site": tk.StringVar(),
            "domain": tk.StringVar(),
            "query": tk.StringVar(),
            "author": tk.StringVar(),
            "company": tk.StringVar(),
        }
        self.template_placeholder_inputs = {}  # Виджеты для ввода плейсхолдеров

        self._build_layout()
        self._bind_paste()

    # Имя тега привязок, чтобы наш Ctrl+V срабатывал раньше виджета (важно для Windows)
    PASTE_BINDTAG = "DorkPaste"

    def _bind_paste(self):
        """Привязка Ctrl+V для вставки из буфера во все поля ввода."""
        # Привязка к кастомному тегу с высоким приоритетом (обрабатывается первым)
        self.bind_class(self.PASTE_BINDTAG, "<Control-v>", self._on_paste_global)
        self.bind_class(self.PASTE_BINDTAG, "<Control-V>", self._on_paste_global)
        self.bind_class(self.PASTE_BINDTAG, "<Control-KeyPress-v>", self._on_paste_global)
        self.bind_class(self.PASTE_BINDTAG, "<Control-KeyPress-V>", self._on_paste_global)
        # Вешаем тег на все поля ввода первым в списке bindtags
        for w in self.inputs.values():
            if isinstance(w, tk.Entry):
                self._paste_bindtag_for(w)
                self._bind_context_menu(w)
        for w in self.template_inputs.values():
            if isinstance(w, tk.Entry):
                self._paste_bindtag_for(w)
                self._bind_context_menu(w)
        for w in self.template_placeholder_inputs.values():
            self._paste_bindtag_for(w)
            self._bind_context_menu(w)
        self._paste_bindtag_for(self.output)
        self._bind_context_menu(self.output)

    def _paste_bindtag_for(self, widget):
        """Ставит наш тег первым в bindtags виджета — Ctrl+V обработается до стандартного."""
        widget.bindtags((self.PASTE_BINDTAG,) + widget.bindtags())

    def _on_paste_global(self, event=None):
        """Обработчик Ctrl+V: вставка в виджет с фокусом (event.widget или focus_get)."""
        w = event.widget if event else self.focus_get()
        if w is not None and isinstance(w, (tk.Entry, tk.Text)):
            self._paste_into_widget(w)
        return "break"

    def _bind_context_menu(self, widget):
        """Привязка контекстного меню (правый клик) к виджету."""
        widget.bind("<Button-3>", self._show_paste_context_menu)

    def _show_paste_context_menu(self, event):
        """Показать контекстное меню с пунктом «Вставить»."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Вставить", command=lambda: self._paste_into_widget(event.widget))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _paste_into_widget(self, widget):
        """Вставить из буфера в указанный виджет."""
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return
        if not text:
            return
        try:
            if isinstance(widget, tk.Text):
                widget.insert(tk.INSERT, text)
            elif isinstance(widget, tk.Entry):
                widget.insert(tk.INSERT, text)
        except tk.TclError:
            pass

    def _on_paste(self, event=None):
        """Вставка текста из буфера обмена в поле ввода."""
        w = event.widget if event else self.focus_get()
        if w is None:
            return
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return
        if not text:
            return
        try:
            if isinstance(w, tk.Text):
                w.insert(tk.INSERT, text)
            elif isinstance(w, tk.Entry):
                w.insert(tk.INSERT, text)
            else:
                return
        except tk.TclError:
            return
        return "break"

    def _build_layout(self):
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Вкладка конструктора
        builder_frame = ttk.Frame(self.notebook)
        self.notebook.add(builder_frame, text="Конструктор")
        self._build_builder_tab(builder_frame)

        # Вкладка шаблонов
        templates_frame = ttk.Frame(self.notebook)
        self.notebook.add(templates_frame, text="Шаблоны")
        self._build_templates_tab(templates_frame)

        # Область вывода (общая для обеих вкладок)
        self._build_output_area()

    def _build_builder_tab(self, parent):
        pad = {"padx": 8, "pady": 6}

        # Scrollable area for field list
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        fields_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=fields_frame, anchor="nw")
        fields_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        
        # Привязываем прокрутку колёсиком мыши к canvas конструктора
        canvas.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(canvas, e))
        fields_frame.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(canvas, e))

        # Define fields meta
        meta = [
            ("query", "Базовый запрос", "text", "Обычный поиск, все слова учитываются"),
            ("exact", "Точная фраза", "text", "Поиск точного совпадения внутри кавычек"),
            ("exclude", "Исключить слова", "text", "Минус-слова через пробел/запятую"),
            ("site", "site:", "short", "Искать только на конкретном сайте"),
            ("domain", "domain:", "short", "Искать в пределах домена/поддоменов"),
            ("url", "url:", "short", "Фильтр по вхождению в URL"),
            ("filetypes", "filetype:", "filetypes", "Ограничить типы файлов (можно несколько)"),
            ("intitle", "intitle:", "short", "Слова, которые должны быть в заголовке"),
            ("inurl", "inurl:", "short", "Слова, которые должны быть в URL"),
            ("intext", "intext:", "text", "Слова, которые должны быть в тексте"),
        ]

        for idx, (key, label, kind, desc) in enumerate(meta):
            row = idx * 2  # leave space for description row
            ttk.Checkbutton(
                fields_frame,
                text="",
                variable=self.enabled[key],
                command=lambda k=key: self._toggle_state(k),
            ).grid(column=0, row=row, sticky="w", **pad)

            ttk.Label(fields_frame, text=label).grid(column=1, row=row, sticky="w", **pad)

            if kind == "filetypes":
                widget = self._filetypes_checklist(fields_frame, row)
            else:
                width = 70 if kind == "text" else 30
                widget = tk.Entry(fields_frame, textvariable=self.state[key], width=width)
                widget.grid(column=2, row=row, sticky="w", **pad)

            self.inputs[key] = widget
            self._toggle_state(key, initial=True)

            # Description line
            ttk.Label(fields_frame, text=desc, foreground="#555", wraplength=520, justify="left").grid(
                column=1, row=row + 1, columnspan=2, sticky="w", padx=8, pady=(0, 2)
            )

        # Action buttons
        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(actions, text="Собрать дорк", command=self.on_build).pack(side="left", padx=4)
        ttk.Button(actions, text="Открыть в браузере", command=self.on_open_browser).pack(side="left", padx=4)
        ttk.Button(actions, text="Копировать", command=self.on_copy).pack(side="left", padx=4)
        ttk.Button(actions, text="Очистить", command=self.on_clear).pack(side="left", padx=4)

    def _build_output_area(self):
        # Output area (общая для всех вкладок)
        output_frame = ttk.Frame(self)
        output_frame.pack(fill="both", expand=False, padx=8, pady=(0, 10))
        ttk.Label(output_frame, text="Сформированный дорк:").pack(anchor="w")
        self.output = tk.Text(output_frame, height=6, wrap="word")
        self.output.pack(fill="both", expand=True, pady=4)
        self.status = ttk.Label(output_frame, text="", foreground="green")
        self.status.pack(anchor="w")

    def _build_templates_tab(self, parent):
        # Создаем панель с категориями и редактируемым полем
        main_container = ttk.Frame(parent)
        main_container.pack(fill="both", expand=True, padx=8, pady=8)

        # Левая панель - список категорий и шаблонов
        left_panel = ttk.Frame(main_container, width=300)
        left_panel.pack(side="left", fill="both", padx=(0, 8))
        left_panel.pack_propagate(False)

        ttk.Label(left_panel, text="Категории:", font=("", 10, "bold")).pack(anchor="w", padx=4, pady=(0, 4))
        
        # Scrollable listbox для категорий
        cat_list_frame = ttk.Frame(left_panel)
        cat_list_frame.pack(fill="x", pady=(0, 8))

        scrollbar_cat = ttk.Scrollbar(cat_list_frame)
        scrollbar_cat.pack(side="right", fill="y")

        self.category_listbox = tk.Listbox(cat_list_frame, height=6, yscrollcommand=scrollbar_cat.set)
        self.category_listbox.pack(side="left", fill="x", expand=True)
        scrollbar_cat.config(command=self.category_listbox.yview)
        self.category_listbox.bind("<MouseWheel>", lambda e: self._on_listbox_scroll(self.category_listbox, e))

        # Заполняем список категорий
        self.category_names = list(DORK_TEMPLATES.keys())
        for cat in self.category_names:
            self.category_listbox.insert(tk.END, cat)

        ttk.Label(left_panel, text="Шаблоны:", font=("", 10, "bold")).pack(anchor="w", padx=4, pady=(8, 4))

        # Scrollable listbox для шаблонов
        template_list_frame = ttk.Frame(left_panel)
        template_list_frame.pack(fill="both", expand=True)

        scrollbar_templates = ttk.Scrollbar(template_list_frame)
        scrollbar_templates.pack(side="right", fill="y")

        self.template_listbox = tk.Listbox(template_list_frame, yscrollcommand=scrollbar_templates.set)
        self.template_listbox.pack(side="left", fill="both", expand=True)
        scrollbar_templates.config(command=self.template_listbox.yview)
        self.template_listbox.bind("<MouseWheel>", lambda e: self._on_listbox_scroll(self.template_listbox, e))

        # Правая панель
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side="left", fill="both", expand=True)

        # Верхняя часть - чекбоксы с дорками выбранной подкатегории
        templates_checkbox_frame = ttk.LabelFrame(right_panel, text="Дорки выбранной подкатегории")
        templates_checkbox_frame.pack(fill="x", padx=8, pady=(0, 8))

        # Canvas для чекбоксов дорков
        dorks_canvas = tk.Canvas(templates_checkbox_frame, height=120, borderwidth=0, highlightthickness=0)
        dorks_scrollbar = ttk.Scrollbar(templates_checkbox_frame, orient="vertical", command=dorks_canvas.yview)
        dorks_canvas.configure(yscrollcommand=dorks_scrollbar.set)
        dorks_scrollbar.pack(side="right", fill="y")
        dorks_canvas.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        self.template_dorks_frame = ttk.Frame(dorks_canvas)
        dorks_canvas.create_window((0, 0), window=self.template_dorks_frame, anchor="nw")
        self.template_dorks_frame.bind(
            "<Configure>",
            lambda e: dorks_canvas.configure(scrollregion=dorks_canvas.bbox("all"))
        )
        dorks_canvas.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(dorks_canvas, e))
        self.template_dorks_frame.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(dorks_canvas, e))

        self.template_dork_vars = {}  # Будет заполняться при выборе подкатегории

        # Секция для заполнения плейсхолдеров
        placeholders_frame = ttk.LabelFrame(right_panel, text="Заполнение параметров шаблонов")
        placeholders_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        self.placeholders_container = ttk.Frame(placeholders_frame)
        self.placeholders_container.pack(fill="x", padx=8, pady=8)
        
        # Создаем поля для плейсхолдеров (будут показываться/скрываться динамически)
        placeholder_labels = {
            "site": "Сайт (site:):",
            "domain": "Домен (@domain):",
            "query": "Поисковый запрос:",
            "author": "Автор (Author:):",
            "company": "Компания (Company:):"
        }
        
        self.placeholder_rows = {}
        for idx, (key, label) in enumerate(placeholder_labels.items()):
            row_frame = ttk.Frame(self.placeholders_container)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=2)
            self.placeholders_container.columnconfigure(0, weight=1)
            
            ttk.Label(row_frame, text=label, width=20).pack(side="left", padx=(0, 4))
            entry = tk.Entry(row_frame, textvariable=self.template_placeholders[key], width=40)
            entry.pack(side="left", fill="x", expand=True)
            self.template_placeholder_inputs[key] = entry
            self.placeholder_rows[key] = row_frame
            row_frame.grid_remove()  # Скрываем по умолчанию

        # Нижняя часть - поля конструктора
        constructor_frame = ttk.LabelFrame(right_panel, text="Конструктор")
        constructor_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Scrollable area for field list
        container = ttk.Frame(constructor_frame)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        template_canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        template_vsb = ttk.Scrollbar(container, orient="vertical", command=template_canvas.yview)
        template_canvas.configure(yscrollcommand=template_vsb.set)
        template_vsb.pack(side="right", fill="y")
        template_canvas.pack(side="left", fill="both", expand=True)

        template_fields_frame = ttk.Frame(template_canvas)
        template_canvas.create_window((0, 0), window=template_fields_frame, anchor="nw")
        template_fields_frame.bind(
            "<Configure>",
            lambda e: template_canvas.configure(scrollregion=template_canvas.bbox("all")),
        )
        
        # Привязываем прокрутку колёсиком мыши
        template_canvas.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(template_canvas, e))
        template_fields_frame.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(template_canvas, e))

        # Define fields meta (такие же как в конструкторе)
        meta = [
            ("query", "Базовый запрос", "text", "Обычный поиск, все слова учитываются"),
            ("exact", "Точная фраза", "text", "Поиск точного совпадения внутри кавычек"),
            ("exclude", "Исключить слова", "text", "Минус-слова через пробел/запятую"),
            ("site", "site:", "short", "Искать только на конкретном сайте"),
            ("domain", "domain:", "short", "Искать в пределах домена/поддоменов"),
            ("url", "url:", "short", "Фильтр по вхождению в URL"),
            ("filetypes", "filetype:", "filetypes", "Ограничить типы файлов (можно несколько)"),
            ("intitle", "intitle:", "short", "Слова, которые должны быть в заголовке"),
            ("inurl", "inurl:", "short", "Слова, которые должны быть в URL"),
            ("intext", "intext:", "text", "Слова, которые должны быть в тексте"),
        ]

        pad = {"padx": 8, "pady": 6}
        for idx, (key, label, kind, desc) in enumerate(meta):
            row = idx * 2  # leave space for description row
            ttk.Checkbutton(
                template_fields_frame,
                text="",
                variable=self.template_enabled[key],
                command=lambda k=key: self._toggle_template_state(k),
            ).grid(column=0, row=row, sticky="w", **pad)

            ttk.Label(template_fields_frame, text=label).grid(column=1, row=row, sticky="w", **pad)

            if kind == "filetypes":
                widget = self._template_filetypes_checklist(template_fields_frame, row)
            else:
                width = 70 if kind == "text" else 30
                widget = tk.Entry(template_fields_frame, textvariable=self.template_state[key], width=width)
                widget.grid(column=2, row=row, sticky="w", **pad)

            self.template_inputs[key] = widget
            self._toggle_template_state(key, initial=True)

            # Description line
            ttk.Label(template_fields_frame, text=desc, foreground="#555", wraplength=520, justify="left").grid(
                column=1, row=row + 1, columnspan=2, sticky="w", padx=8, pady=(0, 2)
            )

        # Кнопки действий
        templates_actions = ttk.Frame(right_panel)
        templates_actions.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(templates_actions, text="Собрать дорк", command=self.on_template_build).pack(side="left", padx=4)
        ttk.Button(templates_actions, text="Открыть в браузере", command=self.on_template_open_browser).pack(side="left", padx=4)
        ttk.Button(templates_actions, text="Копировать", command=self.on_template_copy).pack(side="left", padx=4)

        # Привязываем обработчики
        self.category_listbox.bind("<<ListboxSelect>>", self._on_category_select)
        self.template_listbox.bind("<<ListboxSelect>>", self._on_template_list_select)
        
        # Инициализируем первую категорию
        if self.category_names:
            self.selected_category_index = 0
            self.category_listbox.selection_set(0)
            self._on_category_select(None)

    def _on_category_select(self, event):
        # Очищаем список подкатегорий (шаблонов)
        self.template_listbox.delete(0, tk.END)
        self.subcategory_paths = []  # Список путей к подкатегориям (category, subcategory)

        # Получаем выбранную категорию
        selection = self.category_listbox.curselection()
        if not selection:
            return
        
        # Сохраняем индекс выбранной категории
        self.selected_category_index = selection[0]
        
        category_name = self.category_names[selection[0]]
        category_data = DORK_TEMPLATES[category_name]

        # Заполняем список подкатегорий (это и есть "Шаблоны")
        for subcategory in category_data.keys():
            self.template_listbox.insert(tk.END, subcategory)
            self.subcategory_paths.append((category_name, subcategory))

    def _template_filetypes_checklist(self, parent: ttk.Frame, row: int):
        wrap = ttk.Frame(parent)
        wrap.grid(column=2, row=row, sticky="w", padx=8, pady=6)

        canvas = tk.Canvas(wrap, width=240, height=110, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Привязываем прокрутку колёсиком мыши
        canvas.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(canvas, e))
        inner.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(canvas, e))

        for i, ft in enumerate(self.filetype_options):
            cb = ttk.Checkbutton(inner, text=ft, variable=self.template_filetype_vars[ft])
            cb.grid(column=0, row=i, sticky="w", padx=4, pady=2)
            self.template_filetype_checks.append(cb)

        return wrap

    def _toggle_template_state(self, key: str, initial: bool = False):
        active = self.template_enabled[key].get()
        widget = self.template_inputs.get(key)
        if not widget:
            return

        if key == "filetypes":
            for cb in self.template_filetype_checks:
                cb.configure(state="normal" if active else "disabled")
            if not active and not initial:
                for var in self.template_filetype_vars.values():
                    var.set(False)
            return

        if isinstance(widget, ttk.Combobox):
            widget.configure(state="readonly" if active else "disabled")
        else:
            widget.configure(state="normal" if active else "disabled")

        if not active and not initial and key in self.template_state:
            self.template_state[key].set("")

    def _get_used_placeholders(self, dorks):
        """Определяет какие плейсхолдеры используются в выбранных дорках"""
        used = set()
        import re
        for dork in dorks:
            # Ищем плейсхолдеры в формате {name} или {name:default}
            matches = re.findall(r'\{(\w+)(?::[^}]*)?\}', dork)
            for match in matches:
                used.add(match)
        return used

    def _extract_default_values(self, dorks):
        """Извлекает значения по умолчанию из плейсхолдеров в выбранных дорках"""
        import re
        defaults = {}
        for dork in dorks:
            # Ищем плейсхолдеры в формате {name:default}
            matches = re.finditer(r'\{(\w+):([^}]*)\}', dork)
            for match in matches:
                name = match.group(1)
                default_value = match.group(2)
                # Если для этого плейсхолдера еще нет значения или текущее поле пустое, сохраняем значение по умолчанию
                if name not in defaults:
                    defaults[name] = default_value
                # Если поле уже заполнено пользователем, не перезаписываем
                elif not self.template_placeholders[name].get().strip():
                    defaults[name] = default_value
        return defaults

    def _update_placeholder_visibility(self):
        """Обновляет видимость полей плейсхолдеров в зависимости от выбранных дорков и заполняет значения по умолчанию"""
        # Получаем выбранные дорки
        selected_dorks = []
        for dork, var in self.template_dork_vars.items():
            if var.get():
                selected_dorks.append(dork)
        
        # Определяем используемые плейсхолдеры
        used_placeholders = self._get_used_placeholders(selected_dorks)
        
        # Извлекаем значения по умолчанию из выбранных дорков
        default_values = self._extract_default_values(selected_dorks)
        
        # Заполняем поля значениями по умолчанию (только если поле пустое)
        for key, default_value in default_values.items():
            if key in self.template_placeholders:
                current_value = self.template_placeholders[key].get().strip()
                # Заполняем только если поле пустое
                if not current_value:
                    self.template_placeholders[key].set(default_value)
        
        # Показываем/скрываем поля
        for key, row_frame in self.placeholder_rows.items():
            if key in used_placeholders:
                row_frame.grid()
            else:
                row_frame.grid_remove()

    def _format_dork_for_display(self, dork: str) -> str:
        """Форматирует дорк для отображения, убирая плейсхолдеры и оставляя значения по умолчанию"""
        import re
        result = dork
        # Заменяем {name:значение} на просто значение (для всех плейсхолдеров с дефолтными значениями)
        result = re.sub(r'\{(\w+):([^}]*)\}', r'\2', result)
        # Заменяем {name} на понятное обозначение в квадратных скобках
        placeholder_labels = {
            "site": "[сайт]",
            "domain": "[домен]",
            "author": "[автор]",
            "company": "[компания]",
            "query": ""  # query уже обработан выше, но на всякий случай
        }
        for key, label in placeholder_labels.items():
            if label:  # Только если есть метка
                result = re.sub(rf'\{{{key}\}}', label, result)
            else:
                result = re.sub(rf'\{{{key}\}}', '', result)
        # Очищаем лишние пробелы
        result = " ".join(result.split())
        return result

    def _on_template_list_select(self, event):
        # Показываем дорки выбранной подкатегории в виде чекбоксов
        selection = self.template_listbox.curselection()
        if not selection or not hasattr(self, 'subcategory_paths'):
            return
        
        path = self.subcategory_paths[selection[0]]
        category_name, subcategory = path
        templates = DORK_TEMPLATES[category_name][subcategory]
        
        # Очищаем предыдущие чекбоксы
        for widget in self.template_dorks_frame.winfo_children():
            widget.destroy()
        self.template_dork_vars = {}
        
        # Очищаем поля плейсхолдеров при смене подкатегории
        for var in self.template_placeholders.values():
            var.set("")
        
        # Создаем чекбоксы для каждого дорка
        for idx, template in enumerate(templates):
            var = tk.BooleanVar()
            self.template_dork_vars[template] = var
            # Форматируем текст для отображения (убираем {query:...})
            display_text = self._format_dork_for_display(template)
            cb = ttk.Checkbutton(
                self.template_dorks_frame,
                text=display_text,
                variable=var,
                command=self._update_placeholder_visibility
            )
            cb.pack(anchor="w", padx=4, pady=2)
        
        # Скрываем все поля плейсхолдеров при смене подкатегории
        for row_frame in self.placeholder_rows.values():
            row_frame.grid_remove()
        
        # Восстанавливаем выделение категории после выбора шаблона
        if self.selected_category_index is not None:
            self.category_listbox.selection_clear(0, tk.END)
            self.category_listbox.selection_set(self.selected_category_index)
            self.category_listbox.see(self.selected_category_index)

    def _replace_placeholders(self, text: str) -> str:
        """Заменяет плейсхолдеры в тексте на значения из полей ввода или значения по умолчанию"""
        import re
        result = text
        
        # Находим все плейсхолдеры в формате {name} или {name:default}
        def replace_placeholder(match):
            full_match = match.group(0)  # Полное совпадение, например {query:DB_PASSWORD}
            name = match.group(1)  # Имя плейсхолдера, например query
            default = match.group(2) if match.group(2) else ""  # Значение по умолчанию, если есть
            
            # Получаем значение из поля ввода
            if name in self.template_placeholders:
                user_value = self.template_placeholders[name].get().strip()
                # Если пользователь заполнил поле - используем его значение
                if user_value:
                    return user_value
                # Если не заполнил - используем значение по умолчанию
                elif default:
                    return default
                # Если нет ни того, ни другого - удаляем плейсхолдер
                else:
                    return ""
            else:
                # Если плейсхолдер не найден - оставляем как есть
                return full_match
        
        # Заменяем все плейсхолдеры в формате {name:default} или {name}
        result = re.sub(r'\{(\w+)(?::([^}]*))?\}', replace_placeholder, result)
        
        # Очищаем лишние пробелы и пустые части
        result = " ".join(result.split())
        # Удаляем лишние пробелы вокруг операторов
        result = result.replace("  ", " ").strip()
        # Удаляем пустые кавычки
        result = result.replace('""', '').replace('" "', ' ')
        return result

    def _collect_template_params(self) -> dict:
        # Сначала собираем выбранные дорки из чекбоксов
        selected_dorks = []
        for dork, var in self.template_dork_vars.items():
            if var.get():
                selected_dorks.append(dork)
        
        # Заменяем плейсхолдеры в выбранных дорках
        processed_dorks = [self._replace_placeholders(dork) for dork in selected_dorks]
        processed_dorks = [d for d in processed_dorks if d.strip()]  # Удаляем пустые
        
        # Если есть выбранные дорки, объединяем их через OR
        query_parts = []
        if processed_dorks:
            if len(processed_dorks) == 1:
                query_parts.append(processed_dorks[0])
            else:
                query_parts.append(f"({' OR '.join([f'({d})' for d in processed_dorks])})")
        
        # Добавляем базовый запрос из полей, если он включен
        if self.template_enabled["query"].get() and self.template_state["query"].get().strip():
            query_parts.append(self.template_state["query"].get().strip())
        
        # Формируем params
        params = {}
        if query_parts:
            params["query"] = " ".join(query_parts)
        else:
            params["query"] = ""
        
        # Остальные поля
        for k in ["exact", "exclude", "site", "url", "domain", "intitle", "inurl", "intext"]:
            params[k] = (self.template_state[k].get().strip() if self.template_enabled[k].get() else "")
        
        if self.template_enabled.get("filetypes", tk.BooleanVar()).get():
            selected = [ft for ft, var in self.template_filetype_vars.items() if var.get()]
            params["filetypes"] = selected
        else:
            params["filetypes"] = []
        return params

    def on_template_build(self):
        dork = build_dork(self._collect_template_params())
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, dork if dork else "Дорк пуст — заполните поля.")
        self._set_status("Дорк собран" if dork else "Нечего собирать", error=not bool(dork))

    def on_template_open_browser(self):
        dork = build_dork(self._collect_template_params())
        if not dork:
            self._set_status("Заполните поля для поиска", error=True)
            return
        url = f"https://yandex.ru/search/?text={quote_plus(dork)}"
        webbrowser.open(url)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, dork)
        self._set_status("Открыто в браузере")

    def on_template_copy(self):
        dork = build_dork(self._collect_template_params())
        if not dork:
            self._set_status("Нечего копировать", error=True)
            return
        self.clipboard_clear()
        self.clipboard_append(dork)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, dork)
        self._set_status("Скопировано в буфер обмена")

    def _on_listbox_scroll(self, listbox, event):
        """Обработчик прокрутки колёсиком мыши для Listbox"""
        if event.delta > 0:
            listbox.yview_scroll(-1, "units")
        else:
            listbox.yview_scroll(1, "units")

    def _on_canvas_scroll(self, canvas, event):
        """Обработчик прокрутки колёсиком мыши для Canvas"""
        if event.delta > 0:
            canvas.yview_scroll(-1, "units")
        else:
            canvas.yview_scroll(1, "units")

    def _filetypes_checklist(self, parent: ttk.Frame, row: int):
        wrap = ttk.Frame(parent)
        wrap.grid(column=2, row=row, sticky="w", padx=8, pady=6)

        canvas = tk.Canvas(wrap, width=240, height=110, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Привязываем прокрутку колёсиком мыши к canvas списка типов файлов
        canvas.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(canvas, e))
        inner.bind("<MouseWheel>", lambda e: self._on_canvas_scroll(canvas, e))

        for i, ft in enumerate(self.filetype_options):
            cb = ttk.Checkbutton(inner, text=ft, variable=self.filetype_vars[ft])
            cb.grid(column=0, row=i, sticky="w", padx=4, pady=2)
            self.filetype_checks.append(cb)

        return wrap

    def _toggle_state(self, key: str, initial: bool = False):
        active = self.enabled[key].get()
        widget = self.inputs.get(key)
        if not widget:
            return

        if key == "filetypes":
            for cb in self.filetype_checks:
                cb.configure(state="normal" if active else "disabled")
            if not active and not initial:
                for var in self.filetype_vars.values():
                    var.set(False)
            return

        if isinstance(widget, ttk.Combobox):
            widget.configure(state="readonly" if active else "disabled")
        else:
            widget.configure(state="normal" if active else "disabled")

        if not active and not initial and key in self.state:
            self.state[key].set("")

    def _set_status(self, message: str, error: bool = False):
        self.status.configure(text=message, foreground="red" if error else "green")

    def _collect_params(self) -> dict:
        params = {k: (v.get().strip() if self.enabled[k].get() else "") for k, v in self.state.items()}
        if self.enabled.get("filetypes", tk.BooleanVar()).get():
            selected = [ft for ft, var in self.filetype_vars.items() if var.get()]
            params["filetypes"] = selected
        else:
            params["filetypes"] = []
        return params

    def on_build(self):
        dork = build_dork(self._collect_params())
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, dork if dork else "Дорк пуст — заполните поля.")
        self._set_status("Дорк собран" if dork else "Нечего собирать", error=not bool(dork))

    def on_copy(self):
        dork = self.output.get("1.0", tk.END).strip()
        if not dork:
            self._set_status("Нечего копировать", error=True)
            return
        self.clipboard_clear()
        self.clipboard_append(dork)
        self._set_status("Скопировано в буфер обмена")

    def on_clear(self):
        for key, var in self.state.items():
            var.set("")
            self.enabled[key].set(key == "query")
            self._toggle_state(key)
        for var in self.filetype_vars.values():
            var.set(False)
        self.enabled["filetypes"].set(False)
        self._toggle_state("filetypes")
        self.output.delete("1.0", tk.END)
        self._set_status("Очищено")

    def on_open_browser(self):
        dork = build_dork(self._collect_params())
        if not dork:
            self._set_status("Заполните поля для поиска", error=True)
            return
        url = f"https://yandex.ru/search/?text={quote_plus(dork)}"
        webbrowser.open(url)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, dork)
        self._set_status("Открыто в браузере")


if __name__ == "__main__":
    app = DorkBuilderUI()
    app.mainloop()

