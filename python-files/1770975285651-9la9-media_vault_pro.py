import os
import sys
import shutil
import hashlib
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path

from PIL import Image, ImageTk
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# ------------------------------------------------------------
#  Базовые настройки (с поддержкой .exe)
# ------------------------------------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEDIA_DIR = os.path.join(BASE_DIR, "encrypted_media")
PASSWORD_FILE = os.path.join(BASE_DIR, "password.hash")
KEY_FILE = os.path.join(BASE_DIR, "key.enc")
SALT_FILE = os.path.join(BASE_DIR, "salt.bin")
DEFAULT_PASSWORD = "1234"

SUPPORTED_IMAGES = (".jpg", ".jpeg", ".png", ".gif", ".bmp")
SUPPORTED_VIDEOS = (".mp4", ".avi", ".mov", ".mkv", ".webm")

# ------------------------------------------------------------
#  Функции безопасности (без изменений)
# ------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_security():
    Path(MEDIA_DIR).mkdir(exist_ok=True)
    if not os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "w") as f:
            f.write(hash_password(DEFAULT_PASSWORD))
    if not os.path.exists(KEY_FILE) or not os.path.exists(SALT_FILE):
        salt = os.urandom(8)
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
        key = Fernet.generate_key()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        pwd_key = base64.urlsafe_b64encode(kdf.derive(DEFAULT_PASSWORD.encode()))
        f = Fernet(pwd_key)
        encrypted_key = f.encrypt(key)
        with open(KEY_FILE, "wb") as f_out:
            f_out.write(encrypted_key)

def verify_password(password):
    with open(PASSWORD_FILE, "r") as f:
        stored_hash = f.read().strip()
    return hash_password(password) == stored_hash

def change_password(old_pwd, new_pwd):
    if not verify_password(old_pwd):
        return False, "Неверный старый пароль"
    key = load_fernet_key(old_pwd)
    with open(SALT_FILE, "rb") as f:
        salt = f.read()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    new_pwd_key = base64.urlsafe_b64encode(kdf.derive(new_pwd.encode()))
    f = Fernet(new_pwd_key)
    encrypted_key = f.encrypt(key)
    with open(KEY_FILE, "wb") as f_out:
        f_out.write(encrypted_key)
    with open(PASSWORD_FILE, "w") as f_out:
        f_out.write(hash_password(new_pwd))
    return True, "Пароль успешно изменён"

def load_fernet_key(master_password):
    with open(SALT_FILE, "rb") as f:
        salt = f.read()
    with open(KEY_FILE, "rb") as f:
        encrypted_key = f.read()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    pwd_key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    f = Fernet(pwd_key)
    return f.decrypt(encrypted_key)

def encrypt_file(key, input_path, output_path):
    fernet = Fernet(key)
    with open(input_path, "rb") as f_in:
        data = f_in.read()
    encrypted = fernet.encrypt(data)
    with open(output_path, "wb") as f_out:
        f_out.write(encrypted)

def decrypt_file(key, input_path, output_path):
    fernet = Fernet(key)
    with open(input_path, "rb") as f_in:
        encrypted = f_in.read()
    decrypted = fernet.decrypt(encrypted)
    with open(output_path, "wb") as f_out:
        f_out.write(decrypted)

# ------------------------------------------------------------
#  Кастомные темы (ttk.Style + рекурсивная окраска)
# ------------------------------------------------------------
class AppStyle:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.current_theme = 'light'

    def set_theme(self, theme):
        self.current_theme = theme
        colors = {
            'light': {
                'bg': '#f5f5f5', 'fg': '#000000', 'select': '#0078d7',
                'select_fg': 'white', 'entry': '#ffffff', 'button': '#e1e1e1',
                'frame': '#f0f0f0', 'tree_bg': '#ffffff', 'tree_fg': '#000000',
            },
            'dark': {
                'bg': '#2d2d2d', 'fg': '#ffffff', 'select': '#404040',
                'select_fg': '#ffffff', 'entry': '#3c3c3c', 'button': '#3c3c3c',
                'frame': '#252525', 'tree_bg': '#1e1e1e', 'tree_fg': '#ffffff',
            }
        }
        c = colors[theme]
        self.root.configure(bg=c['bg'])
        self.style.configure('.', background=c['bg'], foreground=c['fg'], fieldbackground=c['entry'])
        self.style.configure('TLabel', background=c['bg'], foreground=c['fg'])
        self.style.configure('TFrame', background=c['bg'])
        self.style.configure('TLabelframe', background=c['bg'], foreground=c['fg'])
        self.style.configure('TButton', background=c['button'], foreground=c['fg'], borderwidth=1)
        self.style.map('TButton', background=[('active', '#505050' if theme == 'dark' else '#c0c0c0')])
        self.style.configure('TEntry', fieldbackground=c['entry'], foreground=c['fg'])
        self.style.configure('Treeview', background=c['tree_bg'], foreground=c['tree_fg'],
                             fieldbackground=c['tree_bg'])
        self.style.configure('Treeview.Heading', background=c['button'], foreground=c['fg'])
        for widget in self.root.winfo_children():
            self._update_widget_colors(widget, c)

    def _update_widget_colors(self, parent, colors):
        for child in parent.winfo_children():
            if isinstance(child, tk.Listbox):
                child.configure(bg=colors['tree_bg'], fg=colors['tree_fg'],
                                selectbackground=colors['select'], selectforeground=colors['select_fg'])
            elif isinstance(child, tk.Entry):
                child.configure(bg=colors['entry'], fg=colors['fg'])
            elif isinstance(child, tk.Text):
                child.configure(bg=colors['entry'], fg=colors['fg'])
            elif isinstance(child, tk.Canvas):
                child.configure(bg=colors['bg'])
            elif isinstance(child, tk.Frame):
                child.configure(bg=colors['bg'])
            elif isinstance(child, tk.Label):
                child.configure(bg=colors['bg'], fg=colors['fg'])
            elif isinstance(child, tk.Button):
                child.configure(bg=colors['button'], fg=colors['fg'],
                                activebackground='#505050' if self.current_theme == 'dark' else '#c0c0c0')
            self._update_widget_colors(child, colors)

# ------------------------------------------------------------
#  Окно входа
# ------------------------------------------------------------
class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Вход в SecureMedia")
        self.root.geometry("350x200")
        self.root.resizable(False, False)
        self.style_manager = AppStyle(self.root)
        self.style_manager.set_theme('light')
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="SecureMedia", font=("Segoe UI", 16, "bold")).pack(pady=(0,20))
        ttk.Label(main_frame, text="Введите пароль:").pack(anchor=tk.W)
        self.entry_pass = ttk.Entry(main_frame, show="*", width=30)
        self.entry_pass.pack(fill=tk.X, pady=(5,10))
        self.entry_pass.bind("<Return>", lambda e: self.check_password())
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        self.btn_login = ttk.Button(btn_frame, text="Войти", command=self.check_password)
        self.btn_login.pack(side=tk.LEFT, padx=(0,5))
        self.lbl_error = ttk.Label(main_frame, text="", foreground="red")
        self.lbl_error.pack(pady=(10,0))
        self.root.mainloop()

    def check_password(self):
        password = self.entry_pass.get()
        if verify_password(password):
            self.root.destroy()
            MainWindow(password)
        else:
            self.lbl_error.config(text="Неверный пароль!")
            self.entry_pass.delete(0, tk.END)

# ------------------------------------------------------------
#  Главное окно (с поддержкой папок и экспорта)
# ------------------------------------------------------------
class MainWindow:
    def __init__(self, master_password):
        self.master_password = master_password
        self.fernet_key = load_fernet_key(master_password)

        self.root = tk.Tk()
        self.root.title("SecureMedia — Медиа-хранилище с шифрованием")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.style_manager = AppStyle(self.root)
        self.style_manager.set_theme('light')
        self.current_theme = 'light'

        self.create_widgets()
        self.refresh_tree()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def create_widgets(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель — дерево папок и файлов
        left_frame = ttk.Frame(main_pane, width=350)
        main_pane.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Медиатека", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0,10))

        # Treeview с прокруткой
        tree_container = ttk.Frame(left_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            tree_container,
            columns=("type",),
            displaycolumns=[],
            yscrollcommand=scrollbar.set,
            selectmode=tk.BROWSE
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Настройка отображения
        self.tree.heading("#0", text="Имя", anchor=tk.W)
        self.tree.column("#0", width=300, stretch=True)

        # Теги для иконок (можно добавить позже)
        self.tree.tag_configure('file', foreground='black')
        self.tree.tag_configure('folder', foreground='black')

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_double_click)  # для открытия папок

        # Кнопки управления
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(15,0))

        ttk.Button(btn_frame, text="➕ Добавить", command=self.add_file).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="📁 Новая папка", command=self.create_folder).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="🗑️ Удалить", command=self.delete_item).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="📥 Скачать", command=self.download_file).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="🌓 Тема", command=self.toggle_theme).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(btn_frame, text="🔑 Сменить пароль", command=self.change_password_dialog).pack(side=tk.LEFT)

        # Правая панель — предпросмотр
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)

        ttk.Label(right_frame, text="Предпросмотр", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0,10))

        self.preview_area = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=1)
        self.preview_area.pack(fill=tk.BOTH, expand=True)

        self.preview_label = ttk.Label(self.preview_area, text="Выберите файл из списка", anchor=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    #  Работа с деревом папок и файлов
    # ------------------------------------------------------------------
    def refresh_tree(self, parent_node='', fs_path=None):
        """Рекурсивно обновляет дерево, начиная с parent_node ('' = корень)."""
        # Очищаем дочерние элементы parent_node
        for child in self.tree.get_children(parent_node):
            self.tree.delete(child)

        if fs_path is None:
            fs_path = MEDIA_DIR

        try:
            items = sorted(os.listdir(fs_path))
        except FileNotFoundError:
            return

        for item in items:
            full_path = os.path.join(fs_path, item)
            rel_path = os.path.relpath(full_path, MEDIA_DIR).replace('\\', '/')
            node_id = rel_path if rel_path != '.' else ''

            if os.path.isdir(full_path):
                # Вставляем папку
                node = self.tree.insert(parent_node, 'end', iid=node_id, text=item,
                                        tags=('folder',), open=False)
                # Рекурсивно добавляем содержимое (закрытое)
                self.refresh_tree(node, full_path)
            else:
                # Файл — проверяем расширение
                ext = os.path.splitext(item)[1].lower()
                if ext in SUPPORTED_IMAGES:
                    icon = "🖼️"
                elif ext in SUPPORTED_VIDEOS:
                    icon = "🎬"
                else:
                    icon = "📄"
                display_name = f"{icon} {item}"
                self.tree.insert(parent_node, 'end', iid=rel_path, text=display_name,
                                 tags=('file',))

    def get_selected_path(self):
        """Возвращает полный путь к выбранному элементу (файл или папка)."""
        selection = self.tree.selection()
        if not selection:
            return None
        iid = selection[0]
        if iid == '':
            return MEDIA_DIR  # корень
        return os.path.join(MEDIA_DIR, iid.replace('/', os.sep))

    def get_selected_parent_path(self):
        """Возвращает путь к папке, в которую будет добавлен новый файл/папка."""
        selection = self.tree.selection()
        if not selection:
            return MEDIA_DIR
        iid = selection[0]
        full_path = os.path.join(MEDIA_DIR, iid.replace('/', os.sep))
        if os.path.isfile(full_path):
            # Выделен файл — берём его родительскую папку
            return os.path.dirname(full_path)
        else:
            # Выделена папка или корень
            return full_path

    # ------------------------------------------------------------------
    #  Обработчики событий
    # ------------------------------------------------------------------
    def on_tree_select(self, event):
        """Показ предпросмотра при выборе файла."""
        path = self.get_selected_path()
        if not path:
            return
        if os.path.isfile(path):
            self.show_preview(path)
        else:
            # Папка — очищаем предпросмотр
            for widget in self.preview_area.winfo_children():
                widget.destroy()
            ttk.Label(self.preview_area, text=f"📁 {os.path.basename(path)}", anchor=tk.CENTER).pack(expand=True)

    def on_double_click(self, event):
        """Двойной клик по папке — раскрыть/закрыть."""
        path = self.get_selected_path()
        if path and os.path.isdir(path):
            selection = self.tree.selection()
            if selection:
                iid = selection[0]
                if self.tree.item(iid, 'open'):
                    self.tree.item(iid, open=False)
                else:
                    self.tree.item(iid, open=True)

    def show_preview(self, filepath):
        """Отображает изображение или информацию о видео."""
        for widget in self.preview_area.winfo_children():
            widget.destroy()

        ext = os.path.splitext(filepath)[1].lower()
        if ext in SUPPORTED_IMAGES:
            try:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                    tmp_path = tmp.name
                decrypt_file(self.fernet_key, filepath, tmp_path)

                img = Image.open(tmp_path)
                max_size = (self.preview_area.winfo_width() or 500,
                            self.preview_area.winfo_height() or 400)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                label = ttk.Label(self.preview_area, image=photo)
                label.image = photo
                label.pack(fill=tk.BOTH, expand=True)

                os.unlink(tmp_path)
            except Exception as e:
                ttk.Label(self.preview_area, text=f"Ошибка загрузки:\n{e}").pack()

        elif ext in SUPPORTED_VIDEOS:
            info_frame = ttk.Frame(self.preview_area)
            info_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(info_frame, text="🎬", font=("Segoe UI", 48)).pack(pady=20)
            ttk.Label(info_frame, text=os.path.basename(filepath), font=("Segoe UI", 12)).pack(pady=5)
            ttk.Label(info_frame, text="Видеофайл (зашифрован)", font=("Segoe UI", 10)).pack(pady=5)

            btn_play = ttk.Button(info_frame, text="▶ Воспроизвести",
                                  command=lambda: self.play_video(filepath))
            btn_play.pack(pady=10)
        else:
            ttk.Label(self.preview_area, text="Неподдерживаемый формат файла").pack()

    def play_video(self, encrypted_path):
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
            decrypt_file(self.fernet_key, encrypted_path, tmp_path)

            if os.name == 'nt':
                os.startfile(tmp_path)
            else:
                import subprocess
                if sys.platform == 'darwin':
                    subprocess.run(['open', tmp_path])
                else:
                    subprocess.run(['xdg-open', tmp_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть видео:\n{e}")

    # ------------------------------------------------------------------
    #  Операции с файлами и папками
    # ------------------------------------------------------------------
    def add_file(self):
        """Добавить новый файл в текущую выбранную папку."""
        parent_path = self.get_selected_parent_path()
        filetypes = [
            ("Медиафайлы", " *.jpg *.jpeg *.png *.gif *.bmp *.mp4 *.avi *.mov *.mkv *.webm"),
            ("Все файлы", "*.*")
        ]
        src_path = filedialog.askopenfilename(title="Выберите файл", filetypes=filetypes)
        if not src_path:
            return

        dest_filename = os.path.basename(src_path)
        dest_path = os.path.join(parent_path, dest_filename)

        # Разрешение конфликтов имён
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(dest_filename)
            counter = 1
            while os.path.exists(os.path.join(parent_path, f"{base}_{counter}{ext}")):
                counter += 1
            dest_filename = f"{base}_{counter}{ext}"
            dest_path = os.path.join(parent_path, dest_filename)

        encrypt_file(self.fernet_key, src_path, dest_path)
        self.refresh_tree()

        # Раскрываем родительскую папку, чтобы увидеть новый файл
        rel_parent = os.path.relpath(parent_path, MEDIA_DIR)
        if rel_parent == '.':
            rel_parent = ''
        self.tree.item(rel_parent, open=True)

    def create_folder(self):
        """Создать новую подпапку в текущей выбранной папке."""
        parent_path = self.get_selected_parent_path()
        folder_name = simpledialog.askstring("Новая папка", "Введите имя папки:",
                                             parent=self.root)
        if not folder_name:
            return
        # Проверка на недопустимые символы
        folder_name = folder_name.strip().replace('/', '_').replace('\\', '_')
        if not folder_name:
            messagebox.showwarning("Ошибка", "Имя папки не может быть пустым.")
            return

        new_folder_path = os.path.join(parent_path, folder_name)
        if os.path.exists(new_folder_path):
            messagebox.showwarning("Ошибка", "Папка с таким именем уже существует.")
            return

        os.makedirs(new_folder_path)
        self.refresh_tree()

        # Раскрываем родительскую папку
        rel_parent = os.path.relpath(parent_path, MEDIA_DIR)
        if rel_parent == '.':
            rel_parent = ''
        self.tree.item(rel_parent, open=True)

    def delete_item(self):
        """Удалить выбранный файл или папку."""
        path = self.get_selected_path()
        if not path:
            messagebox.showwarning("Внимание", "Выберите элемент для удаления.")
            return

        name = os.path.basename(path) if path != MEDIA_DIR else "Корневая папка"
        if path == MEDIA_DIR:
            messagebox.showwarning("Ошибка", "Нельзя удалить корневую папку.")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить {name}?"):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
                self.refresh_tree()
                # Очистить предпросмотр
                for widget in self.preview_area.winfo_children():
                    widget.destroy()
                ttk.Label(self.preview_area, text="Элемент удалён").pack()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить:\n{e}")

    def download_file(self):
        """Расшифровать и сохранить выбранный файл в указанное место."""
        path = self.get_selected_path()
        if not path:
            messagebox.showwarning("Внимание", "Выберите файл для скачивания.")
            return
        if not os.path.isfile(path):
            messagebox.showwarning("Внимание", "Выберите файл, а не папку.")
            return

        # Предложить место сохранения
        save_path = filedialog.asksaveasfilename(
            title="Сохранить расшифрованный файл",
            defaultextension=os.path.splitext(path)[1],
            initialfile=os.path.basename(path)
        )
        if not save_path:
            return

        try:
            decrypt_file(self.fernet_key, path, save_path)
            messagebox.showinfo("Успех", f"Файл сохранён:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось расшифровать файл:\n{e}")

    # ------------------------------------------------------------------
    #  Прочее (тема, смена пароля, завершение)
    # ------------------------------------------------------------------
    def toggle_theme(self):
        new_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.style_manager.set_theme(new_theme)
        self.current_theme = new_theme

    def change_password_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Смена пароля")
        dialog.geometry("350x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Старый пароль:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        old_entry = ttk.Entry(frame, show="*", width=30)
        old_entry.grid(row=1, column=0, pady=(0,10))

        ttk.Label(frame, text="Новый пароль:").grid(row=2, column=0, sticky=tk.W, pady=(0,5))
        new_entry = ttk.Entry(frame, show="*", width=30)
        new_entry.grid(row=3, column=0, pady=(0,10))

        ttk.Label(frame, text="Подтвердите пароль:").grid(row=4, column=0, sticky=tk.W, pady=(0,5))
        confirm_entry = ttk.Entry(frame, show="*", width=30)
        confirm_entry.grid(row=5, column=0, pady=(0,15))

        result_label = ttk.Label(frame, text="", foreground="red")
        result_label.grid(row=6, column=0, pady=(0,10))

        def on_change():
            old_pwd = old_entry.get()
            new_pwd = new_entry.get()
            confirm_pwd = confirm_entry.get()

            if not old_pwd or not new_pwd or not confirm_pwd:
                result_label.config(text="Все поля обязательны")
                return
            if new_pwd != confirm_pwd:
                result_label.config(text="Новые пароли не совпадают")
                return
            if len(new_pwd) < 4:
                result_label.config(text="Пароль должен быть минимум 4 символа")
                return

            success, msg = change_password(old_pwd, new_pwd)
            if success:
                self.master_password = new_pwd
                self.fernet_key = load_fernet_key(new_pwd)
                messagebox.showinfo("Успех", msg)
                dialog.destroy()
            else:
                result_label.config(text=msg)

        ttk.Button(frame, text="Изменить пароль", command=on_change).grid(row=7, column=0)

    def on_closing(self):
        self.root.destroy()

# ------------------------------------------------------------
#  Запуск
# ------------------------------------------------------------
if __name__ == "__main__":
    init_security()
    LoginWindow()