import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import traceback
import string

class PSPPlaylistCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("PSP Playlist Creator (.m3u8)")
        self.root.geometry("1200x800")
        
        # Скрываем консоль (только для Windows)
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass

        # --- Языковая конфигурация ---
        self.languages = {
            "Русский": {
                "title": "Создатель плейлистов для PSP (.m3u8)",
                "playlist_name": "Название плейлиста:",
                "save_button": "💾 СОХРАНИТЬ ПЛЕЙЛИСТ",
                "library_title": " 📂 Музыкальная библиотека (Двойной клик для ДОБАВЛЕНИЯ)",
                "playlist_title": " 🎵 Выбранные треки (Двойной клик для УДАЛЕНИЯ)",
                "footer": "Инструкция: Выберите PSP или укажите путь к MUSIC папке.",
                "success": "Плейлист успешно сохранён!",
                "empty_name": "Пожалуйста, введите название плейлиста!",
                "empty_playlist": "Плейлист пуст! Добавьте сначала несколько песен.",
                "music_folder_error": "Папка 'MUSIC' не найдена!\n\nПожалуйста выберите PSP или укажите путь к папке с музыкой.",
                "folder_error": "Не удалось создать папку назначения:\n{}",
                "file_error": "Не удалось записать файл:\n{}",
                "language": "Язык:",
                "select_psp": "Выберите PSP:",
                "refresh": "🔄 Обновить",
                "auto_detect": "Автоопределение",
                "manual": "Вручную",
                "psp_detected": "PSP обнаружена: {}",
                "no_psp": "PSP не обнаружена",
                "select_folder": "Выбрать папку вручную",
                "current_path": "Текущий путь:",
                "detect_psp": "Найти PSP",
                "tab_create": "Создать плейлист",
                "tab_edit": "Редактировать плейлист",
                "tab_rename": "Переименовать плейлист",
                "edit_open": "📂 Открыть плейлист",
                "edit_save": "💾 Сохранить",
                "edit_save_as": "💾 Сохранить как",
                "edit_new": "🆕 Новый",
                "edit_add": "➕ Добавить трек",
                "edit_remove": "➖ Удалить",
                "edit_move_up": "⬆ Вверх",
                "edit_move_down": "⬇ Вниз",
                "edit_clear": "🗑 Очистить",
                "edit_rename": "✏ Переименовать",
                "edit_path": "Путь к файлу:",
                "edit_browse": "Обзор...",
                "edit_tracks": "Треки в плейлисте:",
                "edit_playlists": "📂 Доступные плейлисты",
                "edit_current": "Текущий плейлист:",
                "edit_loading": "Загрузка...",
                "edit_saved": "Плейлист сохранён!",
                "edit_renamed": "Плейлист переименован!",
                "edit_confirm": "Подтверждение",
                "edit_confirm_clear": "Вы уверены, что хотите очистить плейлист?",
                "edit_confirm_delete": "Вы уверены, что хотите удалить плейлист?",
                "edit_no_file": "Пожалуйста, сначала откройте или создайте плейлист",
                "edit_unsaved": "Несохранённые изменения",
                "edit_unsaved_msg": "У вас есть несохранённые изменения. Сохранить?",
                "edit_error": "Ошибка",
                "edit_invalid": "Некорректный формат плейлиста",
                "file_filter": "Плейлисты PSP (*.m3u8);;Все файлы (*.*)",
                "save_location": "Сохранить в PSP",
                "save_local": "Сохранить локально",
                "edit_save_psp": "💾 Сохранить в PSP",
                "edit_save_local": "💾 Сохранить локально",
                "edit_delete": "🗑 Удалить плейлист",
                "edit_refresh": "🔄 Обновить список",
                "rename_title": "Переименование плейлиста",
                "rename_prompt": "Введите новое название плейлиста:",
                "rename_error": "Ошибка переименования",
                "rename_exists": "Плейлист с таким именем уже существует!",
                "delete_title": "Удаление плейлиста",
                "delete_prompt": "Вы уверены, что хотите удалить плейлист?"
            },
            "Українська": {
                "title": "Створювач плейлистів для PSP (.m3u8)",
                "playlist_name": "Назва плейлисту:",
                "save_button": "💾 ЗБЕРЕГТИ ПЛЕЙЛИСТ",
                "library_title": " 📂 Музична бібліотека (Подвійний клік для ДОДАВАННЯ)",
                "playlist_title": " 🎵 Вибрані треки (Подвійний клік для ВИДАЛЕННЯ)",
                "footer": "Інструкція: Виберіть PSP або вкажіть шлях до папки MUSIC.",
                "success": "Плейлист успішно збережено!",
                "empty_name": "Будь ласка, введіть назву плейлисту!",
                "empty_playlist": "Плейлист порожній! Спочатку додайте кілька пісень.",
                "music_folder_error": "Папку 'MUSIC' не знайдено!\n\nБудь ласка виберіть PSP або вкажіть шлях до папки з музикою.",
                "folder_error": "Не вдалося створити цільову папку:\n{}",
                "file_error": "Не вдалося записати файл:\n{}",
                "language": "Мова:",
                "select_psp": "Виберіть PSP:",
                "refresh": "🔄 Оновити",
                "auto_detect": "Автовизначення",
                "manual": "Вручну",
                "psp_detected": "PSP виявлено: {}",
                "no_psp": "PSP не виявлено",
                "select_folder": "Вибрати папку вручну",
                "current_path": "Поточний шлях:",
                "detect_psp": "Знайти PSP",
                "tab_create": "Створити плейлист",
                "tab_edit": "Редагувати плейлист",
                "tab_rename": "Перейменувати плейлист",
                "edit_open": "📂 Відкрити плейлист",
                "edit_save": "💾 Зберегти",
                "edit_save_as": "💾 Зберегти як",
                "edit_new": "🆕 Новий",
                "edit_add": "➕ Додати трек",
                "edit_remove": "➖ Видалити",
                "edit_move_up": "⬆ Вгору",
                "edit_move_down": "⬇ Вниз",
                "edit_clear": "🗑 Очистити",
                "edit_rename": "✏ Перейменувати",
                "edit_path": "Шлях до файлу:",
                "edit_browse": "Огляд...",
                "edit_tracks": "Треки в плейлисті:",
                "edit_playlists": "📂 Доступні плейлисти",
                "edit_current": "Поточний плейлист:",
                "edit_loading": "Завантаження...",
                "edit_saved": "Плейлист збережено!",
                "edit_renamed": "Плейлист перейменовано!",
                "edit_confirm": "Підтвердження",
                "edit_confirm_clear": "Ви впевнені, що хочете очистити плейлист?",
                "edit_confirm_delete": "Ви впевнені, що хочете видалити плейлист?",
                "edit_no_file": "Будь ласка, спочатку відкрийте або створіть плейлист",
                "edit_unsaved": "Незбережені зміни",
                "edit_unsaved_msg": "У вас є незбережені зміни. Зберегти?",
                "edit_error": "Помилка",
                "edit_invalid": "Некоректний формат плейлиста",
                "file_filter": "Плейлисти PSP (*.m3u8);;Усі файли (*.*)",
                "save_location": "Зберегти в PSP",
                "save_local": "Зберегти локально",
                "edit_save_psp": "💾 Зберегти в PSP",
                "edit_save_local": "💾 Зберегти локально",
                "edit_delete": "🗑 Видалити плейлист",
                "edit_refresh": "🔄 Оновити список",
                "rename_title": "Перейменування плейлиста",
                "rename_prompt": "Введіть нову назву плейлиста:",
                "rename_error": "Помилка перейменування",
                "rename_exists": "Плейлист з такою назвою вже існує!",
                "delete_title": "Видалення плейлиста",
                "delete_prompt": "Ви впевнені, що хочете видалити плейлист?"
            },
            "English": {
                "title": "PSP Playlist Creator (.m3u8)",
                "playlist_name": "Playlist Name:",
                "save_button": "💾 SAVE PLAYLIST",
                "library_title": " 📂 Music Library (Double-click to ADD)",
                "playlist_title": " 🎵 Selected Tracks (Double-click to REMOVE)",
                "footer": "Instruction: Select PSP or specify path to MUSIC folder.",
                "success": "Playlist saved successfully!",
                "empty_name": "Please enter a name for the playlist!",
                "empty_playlist": "The playlist is empty! Add some songs first.",
                "music_folder_error": "Folder 'MUSIC' not found!\n\nPlease select PSP or specify path to music folder.",
                "folder_error": "Could not create destination folder:\n{}",
                "file_error": "Failed to write file:\n{}",
                "language": "Language:",
                "select_psp": "Select PSP:",
                "refresh": "🔄 Refresh",
                "auto_detect": "Auto-detect",
                "manual": "Manual",
                "psp_detected": "PSP detected: {}",
                "no_psp": "PSP not detected",
                "select_folder": "Select folder manually",
                "current_path": "Current path:",
                "detect_psp": "Find PSP",
                "tab_create": "Create Playlist",
                "tab_edit": "Edit Playlist",
                "tab_rename": "Rename Playlist",
                "edit_open": "📂 Open Playlist",
                "edit_save": "💾 Save",
                "edit_save_as": "💾 Save As",
                "edit_new": "🆕 New",
                "edit_add": "➕ Add Track",
                "edit_remove": "➖ Remove",
                "edit_move_up": "⬆ Move Up",
                "edit_move_down": "⬇ Move Down",
                "edit_clear": "🗑 Clear",
                "edit_rename": "✏ Rename",
                "edit_path": "File path:",
                "edit_browse": "Browse...",
                "edit_tracks": "Tracks in playlist:",
                "edit_playlists": "📂 Available Playlists",
                "edit_current": "Current playlist:",
                "edit_loading": "Loading...",
                "edit_saved": "Playlist saved!",
                "edit_renamed": "Playlist renamed!",
                "edit_confirm": "Confirmation",
                "edit_confirm_clear": "Are you sure you want to clear the playlist?",
                "edit_confirm_delete": "Are you sure you want to delete the playlist?",
                "edit_no_file": "Please open or create a playlist first",
                "edit_unsaved": "Unsaved changes",
                "edit_unsaved_msg": "You have unsaved changes. Save?",
                "edit_error": "Error",
                "edit_invalid": "Invalid playlist format",
                "file_filter": "PSP Playlists (*.m3u8);;All files (*.*)",
                "save_location": "Save to PSP",
                "save_local": "Save locally",
                "edit_save_psp": "💾 Save to PSP",
                "edit_save_local": "💾 Save locally",
                "edit_delete": "🗑 Delete Playlist",
                "edit_refresh": "🔄 Refresh List",
                "rename_title": "Rename Playlist",
                "rename_prompt": "Enter new playlist name:",
                "rename_error": "Rename Error",
                "rename_exists": "Playlist with this name already exists!",
                "delete_title": "Delete Playlist",
                "delete_prompt": "Are you sure you want to delete the playlist?"
            }
        }
        
        self.current_lang = "Русский"
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.playlist_files = []
        self.found_psp_paths = []
        
        # Переменные для редактора
        self.current_playlist_path = None
        self.editor_modified = False
        self.editor_tracks = []
        self.current_playlist_name = ""

        # --- UI Styling ---
        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Arial", 10, "bold"))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("PSP.TLabel", font=("Arial", 10, "bold"), foreground="green")
        style.configure("NoPSP.TLabel", font=("Arial", 10, "bold"), foreground="red")

        # --- Top Control Frame ---
        self.top_frame = ttk.Frame(root, padding="5")
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)

        # Language selection
        self.lang_label = ttk.Label(self.top_frame, text=self.languages[self.current_lang]["language"], style="Bold.TLabel")
        self.lang_label.pack(side=tk.LEFT)
        
        self.lang_var = tk.StringVar(value=self.current_lang)
        self.lang_combo = ttk.Combobox(self.top_frame, textvariable=self.lang_var, 
                                  values=list(self.languages.keys()), 
                                  state="readonly", width=15)
        self.lang_combo.pack(side=tk.LEFT, padx=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        # PSP selection for both tabs
        self.psp_label = ttk.Label(self.top_frame, text=self.languages[self.current_lang]["select_psp"], style="Bold.TLabel")
        self.psp_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.psp_var = tk.StringVar()
        self.psp_combo = ttk.Combobox(self.top_frame, textvariable=self.psp_var, 
                                      state="readonly", width=30)
        self.psp_combo.pack(side=tk.LEFT, padx=5)
        self.psp_combo.bind("<<ComboboxSelected>>", self.on_psp_selected)
        
        # Detect PSP button
        self.btn_detect = ttk.Button(self.top_frame, text=self.languages[self.current_lang]["detect_psp"], 
                                     command=self.scan_for_psp, width=12)
        self.btn_detect.pack(side=tk.LEFT, padx=5)
        
        # Manual folder selection
        self.btn_manual = ttk.Button(self.top_frame, text=self.languages[self.current_lang]["select_folder"], 
                                    command=self.select_folder_manually, width=20)
        self.btn_manual.pack(side=tk.LEFT, padx=5)
        
        # PSP detection status
        self.psp_status = ttk.Label(self.top_frame, text="", style="NoPSP.TLabel")
        self.psp_status.pack(side=tk.RIGHT)

        # Current path display
        self.path_frame = ttk.Frame(root, padding="5")
        self.path_frame.pack(fill=tk.X, padx=10)
        
        self.path_label_text = ttk.Label(self.path_frame, text=self.languages[self.current_lang]["current_path"], style="Bold.TLabel")
        self.path_label_text.pack(side=tk.LEFT)
        
        self.path_label = ttk.Label(self.path_frame, text=self.base_path, foreground="blue")
        self.path_label.pack(side=tk.LEFT, padx=5)

        # --- Notebook (Tabs) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # === TAB 1: Create Playlist ===
        self.tab_create = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_create, text=self.languages[self.current_lang]["tab_create"])
        
        # Header Section (Name & Save)
        self.header_frame = ttk.Frame(self.tab_create, padding="10")
        self.header_frame.pack(fill=tk.X)
        
        self.name_label = ttk.Label(self.header_frame, text=self.languages[self.current_lang]["playlist_name"], style="Bold.TLabel")
        self.name_label.pack(side=tk.LEFT)
        
        self.entry_name = ttk.Entry(self.header_frame, width=30)
        self.entry_name.pack(side=tk.LEFT, padx=5)
        self.entry_name.insert(0, "MyFavorites")
        
        self.ext_label = ttk.Label(self.header_frame, text=".m3u8", foreground="gray")
        self.ext_label.pack(side=tk.LEFT)

        self.btn_save = ttk.Button(self.header_frame, text=self.languages[self.current_lang]["save_button"], 
                                  command=self.save_playlist)
        self.btn_save.pack(side=tk.RIGHT)

        # Main Content (Split View)
        self.paned_window = ttk.PanedWindow(self.tab_create, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # LEFT PANEL: File Explorer
        self.frame_left = ttk.LabelFrame(self.paned_window, text=self.languages[self.current_lang]["library_title"], padding="5")
        self.paned_window.add(self.frame_left, weight=1)

        self.tree = ttk.Treeview(self.frame_left)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.scroll_left = ttk.Scrollbar(self.frame_left, orient="vertical", command=self.tree.yview)
        self.scroll_left.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=self.scroll_left.set)

        # RIGHT PANEL: Playlist Preview
        self.frame_right = ttk.LabelFrame(self.paned_window, text=self.languages[self.current_lang]["playlist_title"], padding="5")
        self.paned_window.add(self.frame_right, weight=1)

        self.playlist_box = tk.Listbox(self.frame_right, bg="#f9f9f9", selectmode=tk.SINGLE, font=("Consolas", 9))
        self.playlist_box.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.scroll_right = ttk.Scrollbar(self.frame_right, orient="vertical", command=self.playlist_box.yview)
        self.scroll_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_box.configure(yscrollcommand=self.scroll_right.set)

        self.playlist_box.bind("<Double-1>", self.remove_music)
        self.tree.bind("<Double-1>", self.add_music)
        
        # === TAB 2: Edit Playlist ===
        self.tab_edit = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_edit, text=self.languages[self.current_lang]["tab_edit"])
        
        # Основной контейнер для редактора
        edit_container = ttk.PanedWindow(self.tab_edit, orient=tk.HORIZONTAL)
        edit_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # ЛЕВАЯ ПАНЕЛЬ: Список плейлистов
        left_edit_frame = ttk.LabelFrame(edit_container, text=self.languages[self.current_lang]["edit_playlists"], padding="5")
        edit_container.add(left_edit_frame, weight=1)
        
        # Панель управления списком плейлистов
        playlist_toolbar = ttk.Frame(left_edit_frame)
        playlist_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_refresh_playlists = ttk.Button(playlist_toolbar, text=self.languages[self.current_lang]["edit_refresh"],
                                               command=self.load_available_playlists, width=15)
        self.btn_refresh_playlists.pack(side=tk.LEFT, padx=2)
        
        self.btn_delete_playlist = ttk.Button(playlist_toolbar, text=self.languages[self.current_lang]["edit_delete"],
                                             command=self.delete_selected_playlist, width=15)
        self.btn_delete_playlist.pack(side=tk.LEFT, padx=2)
        
        # Список плейлистов
        self.playlists_listbox = tk.Listbox(left_edit_frame, bg="#f0f0f0", selectmode=tk.SINGLE, font=("Arial", 10))
        self.playlists_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll_playlists = ttk.Scrollbar(left_edit_frame, orient="vertical", command=self.playlists_listbox.yview)
        scroll_playlists.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlists_listbox.configure(yscrollcommand=scroll_playlists.set)
        
        self.playlists_listbox.bind("<<ListboxSelect>>", self.on_playlist_selected)
        
        # ПРАВАЯ ПАНЕЛЬ: Редактор плейлиста (как на первой вкладке)
        right_edit_frame = ttk.Frame(edit_container)
        edit_container.add(right_edit_frame, weight=2)
        
        # Заголовок текущего плейлиста
        self.current_playlist_frame = ttk.LabelFrame(right_edit_frame, text=self.languages[self.current_lang]["edit_current"], padding="5")
        self.current_playlist_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.current_playlist_label = ttk.Label(self.current_playlist_frame, text="", font=("Arial", 10, "bold"))
        self.current_playlist_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления плейлистом
        edit_buttons_frame = ttk.Frame(self.current_playlist_frame)
        edit_buttons_frame.pack(side=tk.RIGHT)
        
        self.btn_rename_playlist = ttk.Button(edit_buttons_frame, text=self.languages[self.current_lang]["edit_rename"],
                                            command=self.rename_current_playlist, width=12)
        self.btn_rename_playlist.pack(side=tk.LEFT, padx=2)
        
        self.btn_save_edit = ttk.Button(edit_buttons_frame, text=self.languages[self.current_lang]["edit_save"],
                                       command=self.save_edited_playlist, width=12)
        self.btn_save_edit.pack(side=tk.LEFT, padx=2)
        
        # Основной редактор (как на первой вкладке)
        edit_paned = ttk.PanedWindow(right_edit_frame, orient=tk.HORIZONTAL)
        edit_paned.pack(fill=tk.BOTH, expand=True)
        
        # ЛЕВАЯ ПАНЕЛЬ редактора: Музыкальная библиотека
        self.edit_library_frame = ttk.LabelFrame(edit_paned, text=self.languages[self.current_lang]["library_title"], padding="5")
        edit_paned.add(self.edit_library_frame, weight=1)
        
        self.edit_tree = ttk.Treeview(self.edit_library_frame)
        self.edit_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll_edit_left = ttk.Scrollbar(self.edit_library_frame, orient="vertical", command=self.edit_tree.yview)
        scroll_edit_left.pack(side=tk.RIGHT, fill=tk.Y)
        self.edit_tree.configure(yscrollcommand=scroll_edit_left.set)
        
        self.edit_tree.bind("<Double-1>", self.add_to_editor_playlist)
        
        # ПРАВАЯ ПАНЕЛЬ редактора: Треки в плейлисте
        self.edit_playlist_frame = ttk.LabelFrame(edit_paned, text=self.languages[self.current_lang]["edit_tracks"], padding="5")
        edit_paned.add(self.edit_playlist_frame, weight=1)
        
        # Кнопки управления треками
        track_buttons_frame = ttk.Frame(self.edit_playlist_frame)
        track_buttons_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_move_up_edit = ttk.Button(track_buttons_frame, text=self.languages[self.current_lang]["edit_move_up"],
                                          command=self.move_track_up_editor, width=10)
        self.btn_move_up_edit.pack(side=tk.LEFT, padx=2)
        
        self.btn_move_down_edit = ttk.Button(track_buttons_frame, text=self.languages[self.current_lang]["edit_move_down"],
                                            command=self.move_track_down_editor, width=10)
        self.btn_move_down_edit.pack(side=tk.LEFT, padx=2)
        
        self.btn_remove_track_edit = ttk.Button(track_buttons_frame, text=self.languages[self.current_lang]["edit_remove"],
                                               command=self.remove_from_editor_playlist, width=10)
        self.btn_remove_track_edit.pack(side=tk.LEFT, padx=2)
        
        self.btn_clear_edit = ttk.Button(track_buttons_frame, text=self.languages[self.current_lang]["edit_clear"],
                                        command=self.clear_editor_playlist, width=10)
        self.btn_clear_edit.pack(side=tk.LEFT, padx=2)
        
        # Список треков в плейлисте
        self.edit_playlist_box = tk.Listbox(self.edit_playlist_frame, bg="#f9f9f9", selectmode=tk.SINGLE, font=("Consolas", 9))
        self.edit_playlist_box.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scroll_edit_right = ttk.Scrollbar(self.edit_playlist_frame, orient="vertical", command=self.edit_playlist_box.yview)
        scroll_edit_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.edit_playlist_box.configure(yscrollcommand=scroll_edit_right.set)
        
        self.edit_playlist_box.bind("<Double-1>", self.remove_from_editor_playlist)
        
        # === TAB 3: Rename Playlist ===
        self.tab_rename = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rename, text=self.languages[self.current_lang]["tab_rename"])
        
        # Контейнер для переименования
        rename_container = ttk.Frame(self.tab_rename, padding="20")
        rename_container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(rename_container, text=self.languages[self.current_lang]["edit_playlists"], 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Список плейлистов для переименования
        rename_list_frame = ttk.Frame(rename_container)
        rename_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.rename_listbox = tk.Listbox(rename_list_frame, bg="#f0f0f0", selectmode=tk.SINGLE, 
                                        font=("Arial", 10), height=15)
        self.rename_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll_rename = ttk.Scrollbar(rename_list_frame, orient="vertical", command=self.rename_listbox.yview)
        scroll_rename.pack(side=tk.RIGHT, fill=tk.Y)
        self.rename_listbox.configure(yscrollcommand=scroll_rename.set)
        
        # Кнопка переименования
        rename_button_frame = ttk.Frame(rename_container)
        rename_button_frame.pack(fill=tk.X, pady=20)
        
        self.btn_refresh_rename = ttk.Button(rename_button_frame, text=self.languages[self.current_lang]["edit_refresh"],
                                            command=self.load_playlists_for_rename)
        self.btn_refresh_rename.pack(side=tk.LEFT, padx=5)
        
        self.btn_perform_rename = ttk.Button(rename_button_frame, text=self.languages[self.current_lang]["edit_rename"],
                                            command=self.perform_rename, width=15)
        self.btn_perform_rename.pack(side=tk.LEFT, padx=5)
        
        # --- Footer ---
        self.lbl_footer = ttk.Label(root, text=self.languages[self.current_lang]["footer"], foreground="blue")
        self.lbl_footer.pack(pady=5)
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Initial scan for PSP
        self.scan_for_psp()

    def on_tab_changed(self, event):
        """Обработчик смены вкладки"""
        selected_tab = self.notebook.index(self.notebook.select())
        
        if selected_tab == 0:  # Создание плейлиста
            # Обновляем дерево файлов
            self.populate_tree()
        elif selected_tab == 1:  # Редактирование плейлиста
            # Загружаем доступные плейлисты и дерево файлов
            self.load_available_playlists()
            self.populate_edit_tree()
        elif selected_tab == 2:  # Переименование плейлиста
            # Загружаем список плейлистов для переименования
            self.load_playlists_for_rename()

    def scan_for_psp(self):
        """Сканирует систему на наличие PSP"""
        self.found_psp_paths = []
        psp_options = []
        
        if sys.platform == "win32":
            for drive in string.ascii_uppercase:
                drive_path = f"{drive}:\\"
                if os.path.exists(drive_path):
                    if self.is_psp_path(drive_path):
                        self.found_psp_paths.append(drive_path)
                        display_name = f"PSP ({drive}:)"
                        psp_options.append(display_name)
        
        current_dir = self.base_path
        for i in range(5):
            if self.is_psp_path(current_dir):
                if current_dir not in self.found_psp_paths:
                    self.found_psp_paths.append(current_dir)
                    folder_name = os.path.basename(current_dir) if os.path.basename(current_dir) else current_dir
                    psp_options.append(f"PSP [{folder_name}]")
            current_dir = os.path.dirname(current_dir)
            if not current_dir or current_dir == os.path.dirname(current_dir):
                break
        
        user_profile = os.path.expanduser("~")
        common_locations = [
            os.path.join(user_profile, "Desktop"),
            os.path.join(user_profile, "Documents"),
            os.path.join(user_profile, "Downloads"),
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                for item in os.listdir(location):
                    item_path = os.path.join(location, item)
                    if os.path.isdir(item_path) and self.is_psp_path(item_path):
                        if item_path not in self.found_psp_paths:
                            self.found_psp_paths.append(item_path)
                            psp_options.append(f"PSP ({item})")
        
        psp_options.append(self.languages[self.current_lang]["manual"])
        
        self.psp_combo['values'] = psp_options
        
        if len(self.found_psp_paths) > 0:
            self.psp_var.set(psp_options[0])
            self.on_psp_selected()
            status_text = self.languages[self.current_lang]["psp_detected"].format(psp_options[0])
            self.psp_status.config(text=status_text, style="PSP.TLabel")
        else:
            self.psp_status.config(text=self.languages[self.current_lang]["no_psp"], style="NoPSP.TLabel")
            self.psp_var.set(self.languages[self.current_lang]["manual"])
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            self.path_label.config(text=self.base_path)
            self.populate_tree()

    def is_psp_path(self, path):
        """Проверяет, является ли путь PSP по наличию ключевых папок"""
        try:
            required_folders = ['ISO', 'PSP', 'MUSIC', 'VIDEO', 'PICTURE']
            found_folders = 0
            
            for folder in required_folders:
                folder_path = os.path.join(path, folder)
                if os.path.exists(folder_path) and os.path.isdir(folder_path):
                    found_folders += 1
            
            psp_folder = os.path.join(path, 'PSP')
            if os.path.exists(psp_folder):
                psp_subfolders = ['GAME', 'SAVEDATA']
                for subfolder in psp_subfolders:
                    subfolder_path = os.path.join(psp_folder, subfolder)
                    if os.path.exists(subfolder_path):
                        found_folders += 1
            
            return found_folders >= 3
            
        except (PermissionError, OSError):
            return False

    def on_psp_selected(self, event=None):
        """Обработчик выбора PSP"""
        selected = self.psp_var.get()
        
        if selected == self.languages[self.current_lang]["manual"]:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            self.psp_status.config(text=self.languages[self.current_lang]["manual"], style="NoPSP.TLabel")
        else:
            index = list(self.psp_combo['values']).index(selected)
            if index < len(self.found_psp_paths):
                self.base_path = self.found_psp_paths[index]
                if self.is_psp_path(self.base_path):
                    status_text = self.languages[self.current_lang]["psp_detected"].format(selected)
                    self.psp_status.config(text=status_text, style="PSP.TLabel")
                else:
                    self.psp_status.config(text=self.languages[self.current_lang]["no_psp"], style="NoPSP.TLabel")
        
        self.path_label.config(text=self.base_path)
        
        # Обновляем дерево в зависимости от активной вкладки
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab == 0:
            self.populate_tree()
        elif selected_tab == 1:
            self.populate_edit_tree()
            self.load_available_playlists()

    def select_folder_manually(self):
        """Ручной выбор папки"""
        folder = filedialog.askdirectory(
            title=self.languages[self.current_lang]["select_folder"],
            initialdir=self.base_path
        )
        
        if folder:
            self.base_path = folder
            self.psp_var.set(self.languages[self.current_lang]["manual"])
            self.path_label.config(text=self.base_path)
            
            if self.is_psp_path(folder):
                status_text = self.languages[self.current_lang]["psp_detected"].format(os.path.basename(folder))
                self.psp_status.config(text=status_text, style="PSP.TLabel")
            else:
                self.psp_status.config(text=self.languages[self.current_lang]["manual"], style="NoPSP.TLabel")
            
            selected_tab = self.notebook.index(self.notebook.select())
            if selected_tab == 0:
                self.populate_tree()
            elif selected_tab == 1:
                self.populate_edit_tree()
                self.load_available_playlists()

    def change_language(self, event=None):
        """Меняет язык интерфейса"""
        new_lang = self.lang_var.get()
        if new_lang != self.current_lang:
            old_lang = self.current_lang
            self.current_lang = new_lang
            lang_data = self.languages[self.current_lang]
            
            self.root.title(lang_data["title"])
            
            # Обновляем все текстовые метки
            self.lang_label.config(text=lang_data["language"])
            self.psp_label.config(text=lang_data["select_psp"])
            self.path_label_text.config(text=lang_data["current_path"])
            self.name_label.config(text=lang_data["playlist_name"])
            self.btn_save.config(text=lang_data["save_button"])
            self.frame_left.config(text=lang_data["library_title"])
            self.frame_right.config(text=lang_data["playlist_title"])
            self.lbl_footer.config(text=lang_data["footer"])
            self.btn_detect.config(text=lang_data["detect_psp"])
            self.btn_manual.config(text=lang_data["select_folder"])
            
            # Обновляем названия вкладок
            self.notebook.tab(0, text=lang_data["tab_create"])
            self.notebook.tab(1, text=lang_data["tab_edit"])
            self.notebook.tab(2, text=lang_data["tab_rename"])
            
            # Обновляем редактор
            self.btn_refresh_playlists.config(text=lang_data["edit_refresh"])
            self.btn_delete_playlist.config(text=lang_data["edit_delete"])
            self.btn_rename_playlist.config(text=lang_data["edit_rename"])
            self.btn_save_edit.config(text=lang_data["edit_save"])
            self.btn_move_up_edit.config(text=lang_data["edit_move_up"])
            self.btn_move_down_edit.config(text=lang_data["edit_move_down"])
            self.btn_remove_track_edit.config(text=lang_data["edit_remove"])
            self.btn_clear_edit.config(text=lang_data["edit_clear"])
            
            # Обновляем фреймы
            left_edit_frame = self.playlists_listbox.master
            left_edit_frame.config(text=lang_data["edit_playlists"])
            self.current_playlist_frame.config(text=lang_data["edit_current"])
            self.edit_library_frame.config(text=lang_data["library_title"])
            self.edit_playlist_frame.config(text=lang_data["edit_tracks"])
            
            # Обновляем вкладку переименования
            rename_label = self.rename_listbox.master.master.winfo_children()[0]
            rename_label.config(text=lang_data["edit_playlists"])
            self.btn_refresh_rename.config(text=lang_data["edit_refresh"])
            self.btn_perform_rename.config(text=lang_data["edit_rename"])
            
            # Обновляем комбобокс PSP
            current_values = list(self.psp_combo['values'])
            if current_values:
                new_values = []
                for value in current_values:
                    if value == self.languages[old_lang]["manual"]:
                        new_values.append(lang_data["manual"])
                    else:
                        new_values.append(value)
                
                self.psp_combo['values'] = new_values
                
                if self.psp_var.get() == self.languages[old_lang]["manual"]:
                    self.psp_var.set(lang_data["manual"])
            
            # Обновляем статус PSP
            current_status = self.psp_status.cget("text")
            if self.languages[old_lang]["psp_detected"].format("") in current_status:
                if self.psp_var.get() and self.psp_var.get() != lang_data["manual"]:
                    selected_psp = self.psp_var.get()
                    self.psp_status.config(text=lang_data["psp_detected"].format(selected_psp))
            elif current_status == self.languages[old_lang]["no_psp"]:
                self.psp_status.config(text=lang_data["no_psp"])
            elif current_status == self.languages[old_lang]["manual"]:
                self.psp_status.config(text=lang_data["manual"])
            
            self.lang_combo.set(new_lang)

    # ========== EDITOR FUNCTIONS ==========
    
    def load_available_playlists(self):
        """Загружает список доступных плейлистов"""
        self.playlists_listbox.delete(0, tk.END)
        
        # Ищем плейлисты в PSP/PLAYLIST/MUSIC/
        playlists_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
        
        if os.path.exists(playlists_dir):
            for file in os.listdir(playlists_dir):
                if file.lower().endswith('.m3u8'):
                    self.playlists_listbox.insert(tk.END, file)
        
        # Если нет плейлистов в PSP, ищем локально
        if self.playlists_listbox.size() == 0:
            local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
            if os.path.exists(local_dir):
                for file in os.listdir(local_dir):
                    if file.lower().endswith('.m3u8'):
                        self.playlists_listbox.insert(tk.END, file)
    
    def on_playlist_selected(self, event):
        """Обработчик выбора плейлиста из списка"""
        selection = self.playlists_listbox.curselection()
        if selection:
            playlist_name = self.playlists_listbox.get(selection[0])
            self.current_playlist_name = playlist_name
            self.current_playlist_label.config(text=playlist_name)
            
            # Загружаем плейлист
            self.load_selected_playlist(playlist_name)
    
    def load_selected_playlist(self, playlist_name):
        """Загружает выбранный плейлист в редактор"""
        # Сначала ищем в PSP
        playlists_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
        file_path = os.path.join(playlists_dir, playlist_name)
        
        if not os.path.exists(file_path):
            # Ищем локально
            local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
            file_path = os.path.join(local_dir, playlist_name)
        
        if os.path.exists(file_path):
            self.current_playlist_path = file_path
            self.load_playlist_to_editor(file_path)
    
    def load_playlist_to_editor(self, file_path):
        """Загружает плейлист в редактор"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.editor_tracks = []
            self.edit_playlist_box.delete(0, tk.END)
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#EXTM3U'):
                    self.editor_tracks.append(line)
                    # Показываем только имя файла для удобства
                    track_name = os.path.basename(line) if '/' in line or '\\' in line else line
                    self.edit_playlist_box.insert(tk.END, track_name)
            
            self.editor_modified = False
            
        except Exception as e:
            messagebox.showerror(self.languages[self.current_lang]["edit_error"], 
                                f"{self.languages[self.current_lang]['edit_invalid']}:\n{e}")
    
    def add_to_editor_playlist(self, event):
        """Добавляет песню из дерева в редактор плейлиста"""
        selected_item = self.edit_tree.selection()
        if not selected_item:
            return

        item_data = self.edit_tree.item(selected_item[0])
        
        if item_data['values'] and item_data['values'][1] == "file":
            full_path = item_data['values'][0]
            filename = item_data['text']
            
            if full_path not in self.editor_tracks:
                self.editor_tracks.append(full_path)
                self.edit_playlist_box.insert(tk.END, filename)
                self.editor_modified = True
            else:
                # Подсветка дубликата
                self.edit_playlist_box.config(bg="#ffcccc")
                self.root.after(200, lambda: self.edit_playlist_box.config(bg="#f9f9f9"))
    
    def remove_from_editor_playlist(self, event=None):
        """Удаляет трек из редактора плейлиста (двойной клик или кнопка)"""
        selection = self.edit_playlist_box.curselection()
        if selection:
            index = selection[0]
            self.edit_playlist_box.delete(index)
            self.editor_tracks.pop(index)
            self.editor_modified = True
    
    def move_track_up_editor(self):
        """Перемещает трек вверх в редакторе"""
        selection = self.edit_playlist_box.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            # Меняем местами в списке
            self.editor_tracks[index], self.editor_tracks[index-1] = self.editor_tracks[index-1], self.editor_tracks[index]
            
            # Обновляем Listbox
            track1 = self.edit_playlist_box.get(index)
            track2 = self.edit_playlist_box.get(index-1)
            self.edit_playlist_box.delete(index-1, index+1)
            self.edit_playlist_box.insert(index-1, track1)
            self.edit_playlist_box.insert(index, track2)
            
            # Выделяем перемещённый трек
            self.edit_playlist_box.selection_set(index-1)
            self.editor_modified = True
    
    def move_track_down_editor(self):
        """Перемещает трек вниз в редакторе"""
        selection = self.edit_playlist_box.curselection()
        if selection and selection[0] < len(self.editor_tracks) - 1:
            index = selection[0]
            # Меняем местами в списке
            self.editor_tracks[index], self.editor_tracks[index+1] = self.editor_tracks[index+1], self.editor_tracks[index]
            
            # Обновляем Listbox
            track1 = self.edit_playlist_box.get(index)
            track2 = self.edit_playlist_box.get(index+1)
            self.edit_playlist_box.delete(index, index+2)
            self.edit_playlist_box.insert(index, track2)
            self.edit_playlist_box.insert(index+1, track1)
            
            # Выделяем перемещённый трек
            self.edit_playlist_box.selection_set(index+1)
            self.editor_modified = True
    
    def clear_editor_playlist(self):
        """Очищает редактор плейлиста"""
        if self.editor_tracks:
            response = messagebox.askyesno(self.languages[self.current_lang]["edit_confirm"], 
                                          self.languages[self.current_lang]["edit_confirm_clear"])
            if response:
                self.edit_playlist_box.delete(0, tk.END)
                self.editor_tracks.clear()
                self.editor_modified = True
    
    def save_edited_playlist(self):
        """Сохраняет отредактированный плейлист"""
        if not self.current_playlist_name:
            messagebox.showwarning(self.languages[self.current_lang]["edit_error"], 
                                  "Сначала выберите плейлист для редактирования!")
            return
        
        if not self.editor_tracks:
            messagebox.showwarning("Warning", self.languages[self.current_lang]["empty_playlist"])
            return
        
        # Определяем путь для сохранения
        if self.is_psp_path(self.base_path):
            destination_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
        else:
            destination_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
        
        if not os.path.exists(destination_dir):
            try:
                os.makedirs(destination_dir)
            except OSError as e:
                messagebox.showerror("Error", self.languages[self.current_lang]["folder_error"].format(e))
                return
        
        file_path = os.path.join(destination_dir, self.current_playlist_name)
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for track in self.editor_tracks:
                    # Преобразуем путь для PSP
                    drive, path_without_drive = os.path.splitdrive(track)
                    psp_path = path_without_drive.replace("\\", "/")
                    
                    if "/MUSIC" in psp_path:
                        start_index = psp_path.find("/MUSIC")
                        psp_path = psp_path[start_index:]
                    elif "MUSIC/" in psp_path:
                        start_index = psp_path.find("MUSIC/")
                        psp_path = "/" + psp_path[start_index:]
                    
                    f.write(psp_path + "\n")
            
            self.editor_modified = False
            messagebox.showinfo("Success", f"{self.languages[self.current_lang]['edit_saved']}\n\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Fatal Error", self.languages[self.current_lang]["file_error"].format(e))
    
    def rename_current_playlist(self):
        """Переименовывает текущий плейлист"""
        if not self.current_playlist_name:
            messagebox.showwarning(self.languages[self.current_lang]["edit_error"], 
                                  "Сначала выберите плейлист для переименования!")
            return
        
        new_name = simpledialog.askstring(
            self.languages[self.current_lang]["rename_title"],
            self.languages[self.current_lang]["rename_prompt"],
            initialvalue=self.current_playlist_name
        )
        
        if new_name and new_name != self.current_playlist_name:
            if not new_name.endswith('.m3u8'):
                new_name += '.m3u8'
            
            # Проверяем существование файла с таким именем
            if self.is_psp_path(self.base_path):
                destination_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
            else:
                destination_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
            
            new_path = os.path.join(destination_dir, new_name)
            old_path = os.path.join(destination_dir, self.current_playlist_name)
            
            if os.path.exists(new_path):
                messagebox.showerror(self.languages[self.current_lang]["rename_error"], 
                                    self.languages[self.current_lang]["rename_exists"])
                return
            
            try:
                os.rename(old_path, new_path)
                self.current_playlist_name = new_name
                self.current_playlist_label.config(text=new_name)
                self.load_available_playlists()
                messagebox.showinfo("Success", self.languages[self.current_lang]["edit_renamed"])
            except Exception as e:
                messagebox.showerror(self.languages[self.current_lang]["rename_error"], str(e))
    
    def delete_selected_playlist(self):
        """Удаляет выбранный плейлист"""
        selection = self.playlists_listbox.curselection()
        if not selection:
            return
        
        playlist_name = self.playlists_listbox.get(selection[0])
        
        response = messagebox.askyesno(
            self.languages[self.current_lang]["delete_title"],
            f"{self.languages[self.current_lang]['delete_prompt']}\n\n{playlist_name}"
        )
        
        if response:
            # Ищем файл в PSP
            playlists_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
            file_path = os.path.join(playlists_dir, playlist_name)
            
            if not os.path.exists(file_path):
                # Ищем локально
                local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
                file_path = os.path.join(local_dir, playlist_name)
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.load_available_playlists()
                    self.edit_playlist_box.delete(0, tk.END)
                    self.editor_tracks.clear()
                    self.current_playlist_label.config(text="")
                    self.current_playlist_name = ""
                    messagebox.showinfo("Success", "Плейлист удалён!")
                except Exception as e:
                    messagebox.showerror("Error", f"Не удалось удалить плейлист:\n{e}")
    
    def load_playlists_for_rename(self):
        """Загружает список плейлистов для переименования"""
        self.rename_listbox.delete(0, tk.END)
        
        # Ищем плейлисты в PSP/PLAYLIST/MUSIC/
        playlists_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
        
        if os.path.exists(playlists_dir):
            for file in os.listdir(playlists_dir):
                if file.lower().endswith('.m3u8'):
                    self.rename_listbox.insert(tk.END, file)
        
        # Если нет плейлистов в PSP, ищем локально
        if self.rename_listbox.size() == 0:
            local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
            if os.path.exists(local_dir):
                for file in os.listdir(local_dir):
                    if file.lower().endswith('.m3u8'):
                        self.rename_listbox.insert(tk.END, file)
    
    def perform_rename(self):
        """Выполняет переименование выбранного плейлиста"""
        selection = self.rename_listbox.curselection()
        if not selection:
            messagebox.showwarning(self.languages[self.current_lang]["edit_error"], 
                                  "Сначала выберите плейлист для переименования!")
            return
        
        old_name = self.rename_listbox.get(selection[0])
        
        new_name = simpledialog.askstring(
            self.languages[self.current_lang]["rename_title"],
            self.languages[self.current_lang]["rename_prompt"],
            initialvalue=old_name
        )
        
        if new_name and new_name != old_name:
            if not new_name.endswith('.m3u8'):
                new_name += '.m3u8'
            
            # Определяем директорию
            if self.is_psp_path(self.base_path):
                destination_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
            else:
                destination_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
            
            old_path = os.path.join(destination_dir, old_name)
            new_path = os.path.join(destination_dir, new_name)
            
            if os.path.exists(new_path):
                messagebox.showerror(self.languages[self.current_lang]["rename_error"], 
                                    self.languages[self.current_lang]["rename_exists"])
                return
            
            try:
                os.rename(old_path, new_path)
                self.load_playlists_for_rename()
                messagebox.showinfo("Success", self.languages[self.current_lang]["edit_renamed"])
            except Exception as e:
                messagebox.showerror(self.languages[self.current_lang]["rename_error"], str(e))

    # ========== TREE FUNCTIONS ==========
    
    def populate_tree(self):
        """Сканирует папку 'MUSIC' и строит древовидную структуру для первой вкладки"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.playlist_box.delete(0, tk.END)
        self.playlist_files.clear()
        
        music_folder = self.find_music_folder()
        
        if not music_folder:
            self.psp_status.config(text=self.languages[self.current_lang]["no_psp"], style="NoPSP.TLabel")
            return

        try:
            folder_name = os.path.basename(music_folder) if os.path.basename(music_folder) else "MUSIC"
            root_node = self.tree.insert("", "end", text=folder_name, open=True, values=(music_folder, "dir"))
            self.process_directory(music_folder, root_node)
        except Exception as e:
            print(f"Error populating tree: {e}")
    
    def populate_edit_tree(self):
        """Сканирует папку 'MUSIC' и строит древовидную структуру для редактора"""
        for item in self.edit_tree.get_children():
            self.edit_tree.delete(item)
        
        music_folder = self.find_music_folder()
        
        if not music_folder:
            return

        try:
            folder_name = os.path.basename(music_folder) if os.path.basename(music_folder) else "MUSIC"
            root_node = self.edit_tree.insert("", "end", text=folder_name, open=True, values=(music_folder, "dir"))
            self.process_directory_for_editor(music_folder, root_node)
        except Exception as e:
            print(f"Error populating edit tree: {e}")
    
    def find_music_folder(self):
        """Находит папку с музыкой"""
        music_folder = os.path.join(self.base_path, "MUSIC")
        if os.path.exists(music_folder) and os.path.isdir(music_folder):
            return music_folder
        
        for item in os.listdir(self.base_path):
            item_path = os.path.join(self.base_path, item)
            if os.path.isdir(item_path):
                try:
                    for root_dir, dirs, files in os.walk(item_path):
                        for file in files:
                            if file.lower().endswith(('.mp3', '.m4a', '.wma', '.wav', '.flac', '.aac')):
                                return item_path
                except:
                    continue
        
        try:
            for root_dir, dirs, files in os.walk(self.base_path):
                for file in files:
                    if file.lower().endswith(('.mp3', '.m4a', '.wma', '.wav', '.flac', '.aac')):
                        return self.base_path
        except:
            pass
        
        return None
    
    def process_directory(self, parent_path, parent_node):
        """Рекурсивно читает папки и файлы для первой вкладки"""
        try:
            items = sorted(os.listdir(parent_path))
            for item in items:
                full_path = os.path.join(parent_path, item)
                
                try:
                    if os.path.isdir(full_path):
                        node = self.tree.insert(parent_node, "end", text=item, open=False, values=(full_path, "dir"))
                        self.process_directory(full_path, node)
                    
                    elif item.lower().endswith(('.mp3', '.m4a', '.wma', '.wav', '.flac', '.aac')):
                        self.tree.insert(parent_node, "end", text=item, values=(full_path, "file"))
                        
                except (PermissionError, OSError):
                    continue
                    
        except (PermissionError, OSError):
            pass
    
    def process_directory_for_editor(self, parent_path, parent_node):
        """Рекурсивно читает папки и файлы для редактора"""
        try:
            items = sorted(os.listdir(parent_path))
            for item in items:
                full_path = os.path.join(parent_path, item)
                
                try:
                    if os.path.isdir(full_path):
                        node = self.edit_tree.insert(parent_node, "end", text=item, open=False, values=(full_path, "dir"))
                        self.process_directory_for_editor(full_path, node)
                    
                    elif item.lower().endswith(('.mp3', '.m4a', '.wma', '.wav', '.flac', '.aac')):
                        self.edit_tree.insert(parent_node, "end", text=item, values=(full_path, "file"))
                        
                except (PermissionError, OSError):
                    continue
                    
        except (PermissionError, OSError):
            pass

    def add_music(self, event):
        """Добавляет песню из Treeview (слева) в Плейлист (справа) для первой вкладки"""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item_data = self.tree.item(selected_item[0])
        
        if item_data['values'] and item_data['values'][1] == "file":
            full_path = item_data['values'][0]
            filename = item_data['text']
            
            if full_path not in self.playlist_files:
                self.playlist_files.append(full_path)
                self.playlist_box.insert(tk.END, filename)
            else:
                self.playlist_box.config(bg="#ffcccc")
                self.root.after(200, lambda: self.playlist_box.config(bg="#f9f9f9"))

    def remove_music(self, event):
        """Удаляет песню из Плейлиста (справа) для первой вкладки"""
        selection = self.playlist_box.curselection()
        if selection:
            index = selection[0]
            self.playlist_box.delete(index)
            self.playlist_files.pop(index)

    def save_playlist(self):
        """Генерирует файл .m3u8 с правильными путями для PSP"""
        name = self.entry_name.get().strip()
        
        if not name:
            messagebox.showwarning("Warning", self.languages[self.current_lang]["empty_name"])
            return
        if not self.playlist_files:
            messagebox.showwarning("Warning", self.languages[self.current_lang]["empty_playlist"])
            return

        if self.is_psp_path(self.base_path):
            destination_dir = os.path.join(self.base_path, "PSP", "PLAYLIST", "MUSIC")
        else:
            destination_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PSP_PLAYLISTS")
        
        if not os.path.exists(destination_dir):
            try:
                os.makedirs(destination_dir)
            except OSError as e:
                messagebox.showerror("Error", self.languages[self.current_lang]["folder_error"].format(e))
                return

        file_path = os.path.join(destination_dir, f"{name}.m3u8")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for abs_path in self.playlist_files:
                    drive, path_without_drive = os.path.splitdrive(abs_path)
                    psp_path = path_without_drive.replace("\\", "/")
                    
                    if "/MUSIC" in psp_path:
                        start_index = psp_path.find("/MUSIC")
                        psp_path = psp_path[start_index:]
                    elif "MUSIC/" in psp_path:
                        start_index = psp_path.find("MUSIC/")
                        psp_path = "/" + psp_path[start_index:]
                    
                    f.write(psp_path + "\n")
            
            messagebox.showinfo("Success", f"{self.languages[self.current_lang]['success']}\n\nLocation:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Fatal Error", self.languages[self.current_lang]["file_error"].format(e))

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PSPPlaylistCreator(root)
        root.mainloop()
    except Exception as e:
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        messagebox.showerror("Critical Error", f"An error occurred:\n{e}\n\nSee error_log.txt for details.")