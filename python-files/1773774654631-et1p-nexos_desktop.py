"""
NexOS Desktop — Python/tkinter версия
======================================
Запуск:  python nexos_desktop.py
Требует: Python 3.8+, только стандартные библиотеки (tkinter встроен)

Возможности:
  - Файловый менеджер (проводник)
  - Запуск ЛЮБЫХ .exe файлов (Windows) / программ (Linux/macOS)
  - Просмотр текстовых файлов и изображений
  - Блокнот с сохранением
  - Калькулятор
  - Терминал (запуск команд)
  - Системная информация
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os, sys, subprocess, platform, shutil, threading, math, time
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════
# КОНСТАНТЫ И ТЕМА
# ══════════════════════════════════════════════════
THEME = {
    'bg':        '#0b0d17',
    'surface':   '#13151f',
    'surface2':  '#1a1d2e',
    'surface3':  '#21253a',
    'accent':    '#0078d4',
    'accent2':   '#1a8fe0',
    'text':      '#ececec',
    'text2':     '#8b91a8',
    'text3':     '#555c78',
    'red':       '#c0392b',
    'green':     '#27ae60',
    'border':    '#1e2235',
    'taskbar':   '#090b14',
}
T = THEME

IS_WIN   = platform.system() == 'Windows'
IS_MAC   = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

FONT_MAIN  = ('Segoe UI' if IS_WIN else 'SF Pro Display' if IS_MAC else 'Ubuntu', 10)
FONT_MONO  = ('Cascadia Code' if IS_WIN else 'Monaco' if IS_MAC else 'Monospace', 10)
FONT_TITLE = (FONT_MAIN[0], 11, 'bold')
FONT_SMALL = (FONT_MAIN[0], 9)


# ══════════════════════════════════════════════════
# ГЛАВНОЕ ОКНО (РАБОЧИЙ СТОЛ)
# ══════════════════════════════════════════════════
class NexOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('NexOS Desktop')
        self.root.geometry('1280x720')
        self.root.configure(bg=T['bg'])
        self.root.minsize(900, 550)

        self.windows = {}   # id -> Toplevel
        self._setup_style()
        self._build_desktop()
        self._build_taskbar()
        self._tick_clock()

        # Открыть проводник при старте
        self.root.after(300, lambda: self.open_app('explorer'))

    # ── СТИЛИ
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.',
            background=T['surface'],
            foreground=T['text'],
            fieldbackground=T['surface2'],
            troughcolor=T['surface2'],
            selectbackground=T['accent'],
            selectforeground='white',
            font=FONT_MAIN,
            borderwidth=0,
            relief='flat',
        )
        style.configure('Treeview',
            background=T['surface'],
            foreground=T['text'],
            fieldbackground=T['surface'],
            rowheight=24,
        )
        style.configure('Treeview.Heading',
            background=T['surface2'],
            foreground=T['text2'],
            font=FONT_SMALL,
        )
        style.map('Treeview', background=[('selected', T['accent'])])
        style.configure('Vertical.TScrollbar', background=T['surface2'], troughcolor=T['surface'])
        style.configure('Horizontal.TScrollbar', background=T['surface2'], troughcolor=T['surface'])

    # ── РАБОЧИЙ СТОЛ
    def _build_desktop(self):
        self.desk = tk.Frame(self.root, bg=T['bg'])
        self.desk.pack(fill='both', expand=True)

        # Иконки рабочего стола
        icons = [
            ('🗑️', 'Корзина',   lambda: self.open_app('trash')),
            ('📁', 'Проводник', lambda: self.open_app('explorer')),
            ('📄', 'Блокнот',   lambda: self.open_app('notepad')),
            ('🔢', 'Калькулятор', lambda: self.open_app('calculator')),
            ('💻', 'Терминал',  lambda: self.open_app('terminal')),
            ('ℹ️', 'Система',   lambda: self.open_app('sysinfo')),
        ]
        ico_frame = tk.Frame(self.desk, bg=T['bg'])
        ico_frame.place(x=14, y=14)
        for i, (e, name, cmd) in enumerate(icons):
            self._desk_icon(ico_frame, e, name, cmd, i)

    def _desk_icon(self, parent, emoji, name, cmd, row):
        f = tk.Frame(parent, bg=T['bg'], width=80, height=80, cursor='hand2')
        f.grid(row=row, column=0, pady=3)
        f.pack_propagate(False)
        el = tk.Label(f, text=emoji, font=(FONT_MAIN[0], 26), bg=T['bg'], fg=T['text'], cursor='hand2')
        el.pack(pady=(8, 0))
        nl = tk.Label(f, text=name, font=FONT_SMALL, bg=T['bg'], fg=T['text'],
                      wraplength=72, justify='center', cursor='hand2')
        nl.pack()
        for w in (f, el, nl):
            w.bind('<Double-Button-1>', lambda e, c=cmd: c())
            w.bind('<Enter>', lambda e, fr=f: fr.configure(bg=T['surface2']))
            w.bind('<Leave>', lambda e, fr=f: fr.configure(bg=T['bg']))

    # ── ТАСКБАР
    def _build_taskbar(self):
        self.tb = tk.Frame(self.root, bg=T['taskbar'], height=48)
        self.tb.pack(fill='x', side='bottom')
        self.tb.pack_propagate(False)

        # Кнопка Пуск
        start = tk.Button(self.tb, text='⊞', font=(FONT_MAIN[0], 18),
                          bg=T['taskbar'], fg=T['text'], relief='flat',
                          activebackground=T['surface2'], cursor='hand2',
                          command=self._start_menu, padx=10)
        start.pack(side='left', padx=(4, 0))

        # Быстрый запуск
        self.tb_apps = tk.Frame(self.tb, bg=T['taskbar'])
        self.tb_apps.pack(side='left', fill='y', padx=6)
        for ico, app in [('📁','explorer'),('📄','notepad'),('🔢','calculator'),('💻','terminal')]:
            b = tk.Button(self.tb_apps, text=ico, font=(FONT_MAIN[0], 16),
                          bg=T['taskbar'], fg=T['text'], relief='flat',
                          activebackground=T['surface2'], cursor='hand2', padx=4,
                          command=lambda a=app: self.open_app(a))
            b.pack(side='left')

        # Часы
        self.clock_var = tk.StringVar()
        self.date_var  = tk.StringVar()
        clk_frame = tk.Frame(self.tb, bg=T['taskbar'])
        clk_frame.pack(side='right', padx=14)
        tk.Label(clk_frame, textvariable=self.clock_var, font=FONT_TITLE,
                 bg=T['taskbar'], fg=T['text']).pack()
        tk.Label(clk_frame, textvariable=self.date_var,  font=FONT_SMALL,
                 bg=T['taskbar'], fg=T['text2']).pack()

        # Системный трей
        for ico in ['📶', '🔊']:
            tk.Label(self.tb, text=ico, font=(FONT_MAIN[0], 14),
                     bg=T['taskbar'], fg=T['text2']).pack(side='right', padx=4)

    def _tick_clock(self):
        now = datetime.now()
        self.clock_var.set(now.strftime('%H:%M:%S'))
        self.date_var.set(now.strftime('%d.%m.%Y'))
        self.root.after(1000, self._tick_clock)

    def _start_menu(self):
        popup = tk.Toplevel(self.root)
        popup.title('')
        popup.geometry('320x380')
        popup.configure(bg=T['surface'])
        popup.overrideredirect(True)
        # Позиция над таскбаром
        x = self.root.winfo_x() + 60
        y = self.root.winfo_y() + self.root.winfo_height() - 48 - 390
        popup.geometry(f'320x380+{x}+{y}')
        popup.focus_set()
        popup.bind('<FocusOut>', lambda e: popup.destroy())

        tk.Label(popup, text='NexOS', font=(FONT_MAIN[0], 16, 'bold'),
                 bg=T['surface'], fg=T['text']).pack(pady=14)

        apps = [('📁','Проводник','explorer'),('📄','Блокнот','notepad'),
                ('🔢','Калькулятор','calculator'),('💻','Терминал','terminal'),
                ('ℹ️','О системе','sysinfo'),('🗑️','Корзина','trash')]
        grid = tk.Frame(popup, bg=T['surface'])
        grid.pack(fill='both', expand=True, padx=10)
        for i, (e, name, app) in enumerate(apps):
            r, c = divmod(i, 3)
            f = tk.Frame(grid, bg=T['surface2'], width=90, height=80, cursor='hand2')
            f.grid(row=r, column=c, padx=4, pady=4)
            f.grid_propagate(False)
            def click(a=app, p=popup): p.destroy(); self.open_app(a)
            tk.Label(f, text=e, font=(FONT_MAIN[0], 22), bg=T['surface2'], fg=T['text'], cursor='hand2').pack(pady=(10,0))
            tk.Label(f, text=name, font=FONT_SMALL, bg=T['surface2'], fg=T['text2'], cursor='hand2').pack()
            for w in f.winfo_children(): w.bind('<Button-1>', lambda e, c=click: c())
            f.bind('<Button-1>', lambda e, c=click: c())

        sep = tk.Frame(popup, bg=T['border'], height=1)
        sep.pack(fill='x', padx=10, pady=6)
        tk.Button(popup, text='⏻  Выход', font=FONT_MAIN, bg=T['surface'], fg='#e57373',
                  relief='flat', cursor='hand2', command=self.root.quit).pack(pady=6)

    # ── ОТКРЫТИЕ ПРИЛОЖЕНИЙ
    def open_app(self, app_id, **kwargs):
        apps = {
            'explorer':   FileExplorer,
            'notepad':    Notepad,
            'calculator': Calculator,
            'terminal':   Terminal,
            'sysinfo':    SysInfo,
            'trash':      lambda root, os_ref: FileExplorer(root, os_ref, start_path=str(Path.home() / 'Trash') if IS_MAC else str(Path.home())),
        }
        if app_id not in apps:
            return
        # Если уже открыто — поднять
        if app_id in self.windows and self.windows[app_id].winfo_exists():
            self.windows[app_id].lift()
            self.windows[app_id].focus_set()
            return
        win = apps[app_id](self.root, self, **kwargs)
        self.windows[app_id] = win

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════
# БАЗОВЫЙ КЛАСС ОКНА
# ══════════════════════════════════════════════════
class AppWindow(tk.Toplevel):
    def __init__(self, root, os_ref, title='Окно', width=760, height=500, ico='📦'):
        super().__init__(root)
        self.os_ref = os_ref
        self.title(f'{ico} {title}')
        self.geometry(f'{width}x{height}')
        self.configure(bg=T['surface'])
        self.minsize(400, 300)
        # Тёмный фон заголовка (Windows)
        try:
            from ctypes import windll
            windll.dwmapi.DwmSetWindowAttribute(int(self.wm_frame()), 20, byref(c_int(1)), 4)
        except:
            pass

    def frame(self, parent=None, **kw):
        defaults = {'bg': T['surface'], 'relief': 'flat', 'bd': 0}
        defaults.update(kw)
        return tk.Frame(parent or self, **defaults)

    def label(self, parent, text='', **kw):
        defaults = {'bg': T['surface'], 'fg': T['text'], 'font': FONT_MAIN}
        defaults.update(kw)
        return tk.Label(parent, text=text, **defaults)

    def button(self, parent, text='', cmd=None, accent=False, **kw):
        defaults = {
            'bg': T['accent'] if accent else T['surface3'],
            'fg': 'white' if accent else T['text'],
            'relief': 'flat', 'cursor': 'hand2',
            'font': FONT_MAIN, 'padx': 10, 'pady': 4,
            'activebackground': T['accent2'] if accent else T['surface2'],
            'activeforeground': 'white',
        }
        defaults.update(kw)
        return tk.Button(parent, text=text, command=cmd, **defaults)

    def entry(self, parent, **kw):
        defaults = {
            'bg': T['surface2'], 'fg': T['text'],
            'insertbackground': T['text'],
            'relief': 'flat', 'font': FONT_MAIN,
            'bd': 4,
        }
        defaults.update(kw)
        return tk.Entry(parent, **defaults)

    def toolbar(self, parent, buttons):
        """Создаёт панель инструментов из списка (text, cmd) или (text, cmd, accent)"""
        tb = self.frame(parent, bg=T['surface2'])
        tb.pack(fill='x')
        sep = tk.Frame(parent, bg=T['border'], height=1)
        sep.pack(fill='x')
        for item in buttons:
            if item is None:
                tk.Frame(tb, bg=T['border'], width=1).pack(side='left', fill='y', padx=4, pady=6)
                continue
            txt, cmd = item[0], item[1]
            accent = len(item) > 2 and item[2]
            self.button(tb, txt, cmd, accent=accent).pack(side='left', padx=3, pady=5)
        return tb

    def notify(self, title, msg, kind='info'):
        self.os_ref.root.after(0, lambda: messagebox.showinfo(title, msg) if kind == 'info' else None)


# ══════════════════════════════════════════════════
# ФАЙЛОВЫЙ МЕНЕДЖЕР
# ══════════════════════════════════════════════════
class FileExplorer(AppWindow):
    def __init__(self, root, os_ref, start_path=None):
        super().__init__(root, os_ref, 'Проводник', 900, 560, '📁')
        self.cur_path = Path(start_path) if start_path else Path.home()
        self.history  = [self.cur_path]
        self.h_idx    = 0
        self.sel_item = None
        self._build()
        self._populate()

    def _build(self):
        # Тулбар навигации
        nav = self.frame(bg=T['surface2'])
        nav.pack(fill='x')
        self.btn_back = self.button(nav, '◀', self._back)
        self.btn_back.pack(side='left', padx=(6,2), pady=5)
        self.btn_fwd  = self.button(nav, '▶', self._fwd)
        self.btn_fwd.pack(side='left', padx=2, pady=5)
        self.button(nav, '↑', self._up).pack(side='left', padx=2, pady=5)
        self.path_var = tk.StringVar()
        path_entry = self.entry(nav, textvariable=self.path_var, font=FONT_MONO)
        path_entry.pack(side='left', fill='x', expand=True, padx=8, pady=5)
        path_entry.bind('<Return>', lambda e: self._nav(self.path_var.get()))
        tk.Frame(nav, bg=T['border'], height=1).pack(fill='x', side='bottom')

        # Тулбар действий
        act = self.frame(bg=T['surface2'])
        act.pack(fill='x')
        btns = [
            ('⬆ Загрузить файл',   self._upload_file,   True),
            ('📂 Загрузить папку',  self._upload_folder, True),
            None,
            ('▶ Запустить',        self._run_file),
            ('👁 Открыть',          self._open_file),
            ('💾 Скачать копию',    self._copy_file),
            ('🗑 Удалить',          self._delete_file),
            None,
            ('➕ Новая папка',      self._new_folder),
        ]
        for item in btns:
            if item is None:
                tk.Frame(act, bg=T['border'], width=1).pack(side='left', fill='y', padx=4, pady=6)
                continue
            txt, cmd = item[0], item[1]
            acc = len(item) > 2 and item[2]
            self.button(act, txt, cmd, acc).pack(side='left', padx=3, pady=5)
        tk.Frame(act, bg=T['border'], height=1).pack(fill='x', side='bottom')

        # Основная область
        main = self.frame()
        main.pack(fill='both', expand=True)

        # Сайдбар
        side = self.frame(main, bg=T['surface2'], width=160)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        tk.Frame(side, bg=T['border'], width=1).pack(side='right', fill='y')

        places = [
            ('🖥️ Рабочий стол',  Path.home() / 'Desktop'),
            ('📄 Документы',     Path.home() / 'Documents'),
            ('⬇️ Загрузки',      Path.home() / 'Downloads'),
            ('🖼️ Изображения',   Path.home() / 'Pictures'),
            ('🎵 Музыка',        Path.home() / 'Music'),
            ('🎬 Видео',         Path.home() / 'Videos'),
            ('🏠 Домашняя',      Path.home()),
        ]
        tk.Label(side, text='Быстрый доступ', font=FONT_SMALL,
                 bg=T['surface2'], fg=T['text3']).pack(anchor='w', padx=8, pady=(10,4))
        for name, path in places:
            def click(p=path):
                if p.exists(): self._navigate(p)
                else: messagebox.showwarning('Нет доступа', f'Папка не найдена:\n{p}')
            lbl = tk.Label(side, text=name, font=FONT_SMALL, bg=T['surface2'],
                           fg=T['text2'], anchor='w', cursor='hand2', padx=8)
            lbl.pack(fill='x', pady=1)
            lbl.bind('<Button-1>', lambda e, c=click: c())
            lbl.bind('<Enter>', lambda e, l=lbl: l.configure(bg=T['surface3']))
            lbl.bind('<Leave>', lambda e, l=lbl: l.configure(bg=T['surface2']))

        # Список файлов
        list_frame = self.frame(main)
        list_frame.pack(side='left', fill='both', expand=True)

        cols = ('name','type','size','modified')
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', selectmode='browse')
        self.tree.heading('name',     text='Имя',         anchor='w')
        self.tree.heading('type',     text='Тип',         anchor='w')
        self.tree.heading('size',     text='Размер',      anchor='e')
        self.tree.heading('modified', text='Изменён',     anchor='w')
        self.tree.column('name',     width=320, anchor='w')
        self.tree.column('type',     width=110, anchor='w')
        self.tree.column('size',     width=90,  anchor='e')
        self.tree.column('modified', width=140, anchor='w')

        vsb = ttk.Scrollbar(list_frame, orient='vertical',   command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient='horizontal',command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right',  fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)

        self.tree.bind('<Double-Button-1>', self._on_dblclick)
        self.tree.bind('<Button-3>',        self._on_rclick)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # Строка статуса
        self.status_var = tk.StringVar(value='Готово')
        tk.Label(self, textvariable=self.status_var, font=FONT_SMALL,
                 bg=T['surface2'], fg=T['text3'], anchor='w', padx=8).pack(fill='x')

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        self.path_var.set(str(self.cur_path))
        try:
            items = sorted(self.cur_path.iterdir(),
                           key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            messagebox.showerror('Доступ запрещён', f'Нет доступа к:\n{self.cur_path}')
            return

        count = 0
        for item in items:
            if item.name.startswith('.'):
                continue
            try:
                stat = item.stat()
                size = self._fmt_size(stat.st_size) if item.is_file() else '—'
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')
                kind = self._file_type(item)
                icon = self._file_icon(item)
                self.tree.insert('', 'end',
                                 values=(f'{icon}  {item.name}', kind, size, mtime),
                                 tags=('dir' if item.is_dir() else 'file',),
                                 iid=str(item))
                count += 1
            except:
                continue
        self.status_var.set(f'{count} объектов')

    def _navigate(self, path):
        path = Path(path)
        if not path.exists():
            messagebox.showerror('Ошибка', f'Путь не найден:\n{path}')
            return
        self.history = self.history[:self.h_idx+1]
        self.history.append(path)
        self.h_idx = len(self.history) - 1
        self.cur_path = path
        self._populate()

    def _nav(self, path_str):   self._navigate(path_str)
    def _back(self):
        if self.h_idx > 0:
            self.h_idx -= 1
            self.cur_path = self.history[self.h_idx]
            self._populate()
    def _fwd(self):
        if self.h_idx < len(self.history)-1:
            self.h_idx += 1
            self.cur_path = self.history[self.h_idx]
            self._populate()
    def _up(self):
        parent = self.cur_path.parent
        if parent != self.cur_path:
            self._navigate(parent)

    def _selected_path(self):
        sel = self.tree.selection()
        return Path(sel[0]) if sel else None

    def _on_select(self, e):
        p = self._selected_path()
        if p:
            self.sel_item = p
            size = self._fmt_size(p.stat().st_size) if p.is_file() else ''
            self.status_var.set(f'Выбран: {p.name}  {size}')

    def _on_dblclick(self, e):
        p = self._selected_path()
        if not p: return
        if p.is_dir():
            self._navigate(p)
        else:
            self._open_file()

    def _on_rclick(self, e):
        row = self.tree.identify_row(e.y)
        if row:
            self.tree.selection_set(row)
        menu = tk.Menu(self, tearoff=0, bg=T['surface2'], fg=T['text'],
                       activebackground=T['accent'], activeforeground='white',
                       relief='flat', bd=0, font=FONT_MAIN)
        menu.add_command(label='▶  Запустить (.exe)',  command=self._run_file)
        menu.add_command(label='👁  Открыть',           command=self._open_file)
        menu.add_separator()
        menu.add_command(label='💾  Скопировать в...',  command=self._copy_file)
        menu.add_command(label='✏️  Переименовать',     command=self._rename_file)
        menu.add_separator()
        menu.add_command(label='🗑  Удалить',           command=self._delete_file)
        menu.add_separator()
        menu.add_command(label='📋  Свойства',          command=self._props)
        menu.post(e.x_root, e.y_root)

    # ── ДЕЙСТВИЯ С ФАЙЛАМИ

    def _run_file(self):
        """ЗАПУСК ИСПОЛНЯЕМЫХ ФАЙЛОВ (.exe, .py, .sh, .app и др.)"""
        p = self._selected_path()
        if not p or not p.is_file():
            messagebox.showinfo('NexOS', 'Выберите файл для запуска')
            return

        ext = p.suffix.lower()
        name = p.name

        # Подтверждение для .exe
        if ext == '.exe':
            if not IS_WIN:
                run_anyway = messagebox.askyesno(
                    'NexOS — Запуск .exe',
                    f'Файл: {name}\n\n'
                    f'⚠️ Вы используете {platform.system()}, а не Windows.\n'
                    f'.exe файлы работают только на Windows.\n\n'
                    f'Попробовать запустить через Wine?'
                )
                if run_anyway:
                    self._run_with_wine(p)
                return
            # На Windows — запускаем напрямую
            ok = messagebox.askyesno(
                '▶ Запустить программу',
                f'Запустить файл?\n\n📦 {name}\n\n⚠️ Запускайте только доверенные файлы.'
            )
            if ok:
                self._launch_process(str(p))

        elif ext == '.py':
            ok = messagebox.askyesno('▶ Python скрипт', f'Запустить Python:\n\n🐍 {name}')
            if ok:
                self._launch_process(sys.executable, str(p))

        elif ext in ('.sh', '.bash', '.zsh') and not IS_WIN:
            ok = messagebox.askyesno('▶ Shell скрипт', f'Запустить скрипт:\n\n🔧 {name}')
            if ok:
                self._launch_process('bash', str(p))

        elif ext in ('.bat', '.cmd') and IS_WIN:
            ok = messagebox.askyesno('▶ Bat файл', f'Запустить:\n\n🔧 {name}')
            if ok:
                self._launch_process(str(p))

        elif ext == '.app' and IS_MAC:
            subprocess.Popen(['open', str(p)])

        else:
            # Открыть системным приложением
            self._open_system(p)

    def _launch_process(self, *args):
        """Запускает процесс и показывает результат"""
        def run():
            try:
                if IS_WIN:
                    result = subprocess.Popen(list(args), creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    result = subprocess.Popen(list(args))
                self.status_var.set(f'✅ Запущено: PID {result.pid}')
            except FileNotFoundError as e:
                self.after(0, lambda: messagebox.showerror('Ошибка запуска', f'Файл не найден:\n{e}'))
            except PermissionError as e:
                self.after(0, lambda: messagebox.showerror('Нет прав', f'Нет прав на запуск:\n{e}'))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror('Ошибка', f'Не удалось запустить:\n{e}'))
        threading.Thread(target=run, daemon=True).start()

    def _run_with_wine(self, path):
        if shutil.which('wine'):
            self._launch_process('wine', str(path))
        else:
            messagebox.showerror('Wine не найден',
                'Wine не установлен.\n\n'
                'Установите Wine:\n'
                '  Ubuntu: sudo apt install wine\n'
                '  macOS:  brew install wine-stable')

    def _open_file(self):
        p = self._selected_path()
        if not p: return
        if p.is_dir(): self._navigate(p); return
        ext = p.suffix.lower()
        # Текстовые — открыть в блокноте
        if ext in ('.txt','.md','.py','.js','.ts','.html','.css','.json','.xml','.csv','.log','.ini','.cfg','.yaml','.sh','.bat'):
            Notepad(self.master, self.os_ref, file_path=p)
        else:
            self._open_system(p)

    def _open_system(self, p):
        """Открыть файл системным приложением"""
        try:
            if IS_WIN:   os.startfile(str(p))
            elif IS_MAC: subprocess.Popen(['open', str(p)])
            else:        subprocess.Popen(['xdg-open', str(p)])
            self.status_var.set(f'Открыто: {p.name}')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось открыть:\n{e}')

    def _upload_file(self):
        paths = filedialog.askopenfilenames(
            title='Выберите файлы',
            initialdir=str(Path.home()),
        )
        if not paths: return
        dest = self.cur_path
        count = 0
        for src in paths:
            try:
                shutil.copy2(src, dest / Path(src).name)
                count += 1
            except Exception as e:
                messagebox.showerror('Ошибка', f'Не удалось скопировать {Path(src).name}:\n{e}')
        if count:
            self._populate()
            self.status_var.set(f'✅ Скопировано {count} файл(ов) в {dest}')

    def _upload_folder(self):
        src = filedialog.askdirectory(title='Выберите папку', initialdir=str(Path.home()))
        if not src: return
        src_path = Path(src)
        dest = self.cur_path / src_path.name
        try:
            shutil.copytree(str(src_path), str(dest))
            self._populate()
            self.status_var.set(f'✅ Папка скопирована: {src_path.name}')
        except Exception as e:
            messagebox.showerror('Ошибка', f'Не удалось скопировать папку:\n{e}')

    def _copy_file(self):
        p = self._selected_path()
        if not p: return
        dest_dir = filedialog.askdirectory(title='Куда скопировать?')
        if not dest_dir: return
        try:
            if p.is_dir(): shutil.copytree(str(p), str(Path(dest_dir)/p.name))
            else:          shutil.copy2(str(p), dest_dir)
            self.status_var.set(f'✅ Скопировано: {p.name}')
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))

    def _delete_file(self):
        p = self._selected_path()
        if not p: return
        if messagebox.askyesno('Удалить', f'Удалить "{p.name}"?\n\nЭто действие нельзя отменить.'):
            try:
                if p.is_dir(): shutil.rmtree(str(p))
                else:          p.unlink()
                self._populate()
            except Exception as e:
                messagebox.showerror('Ошибка', str(e))

    def _rename_file(self):
        p = self._selected_path()
        if not p: return
        win = tk.Toplevel(self); win.title('Переименовать'); win.configure(bg=T['surface']); win.geometry('320x100')
        tk.Label(win, text='Новое имя:', bg=T['surface'], fg=T['text']).pack(pady=(12,4))
        var = tk.StringVar(value=p.name)
        e = self.entry(win, textvariable=var, width=40); e.pack(padx=16)
        e.select_range(0, len(p.stem)); e.focus_set()
        def do():
            new = var.get().strip()
            if new and new != p.name:
                try: p.rename(p.parent/new); self._populate()
                except Exception as ex: messagebox.showerror('Ошибка', str(ex))
            win.destroy()
        e.bind('<Return>', lambda ev: do())
        self.button(win, 'Переименовать', do, True).pack(pady=8)

    def _new_folder(self):
        win = tk.Toplevel(self); win.title('Новая папка'); win.configure(bg=T['surface']); win.geometry('300x90')
        tk.Label(win, text='Имя папки:', bg=T['surface'], fg=T['text']).pack(pady=(12,4))
        var = tk.StringVar(value='Новая папка')
        e = self.entry(win, textvariable=var, width=36); e.pack(padx=16); e.select_range(0,'end'); e.focus_set()
        def do():
            nm = var.get().strip()
            if nm:
                try: (self.cur_path/nm).mkdir(exist_ok=True); self._populate()
                except Exception as ex: messagebox.showerror('Ошибка', str(ex))
            win.destroy()
        e.bind('<Return>', lambda ev: do())
        self.button(win, 'Создать', do, True).pack(pady=8)

    def _props(self):
        p = self._selected_path()
        if not p: return
        try:
            st = p.stat()
            info = (f'Имя: {p.name}\n'
                    f'Путь: {p}\n'
                    f'Тип: {"Папка" if p.is_dir() else p.suffix or "Файл"}\n'
                    f'Размер: {self._fmt_size(st.st_size)}\n'
                    f'Создан: {datetime.fromtimestamp(st.st_ctime).strftime("%d.%m.%Y %H:%M")}\n'
                    f'Изменён: {datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y %H:%M")}')
        except: info = f'Не удалось получить свойства: {p}'
        messagebox.showinfo(f'Свойства — {p.name}', info)

    # ── УТИЛИТЫ
    def _file_icon(self, p: Path) -> str:
        if p.is_dir(): return '📁'
        ext = p.suffix.lower()
        m = {'.exe':'📦','.msi':'📦','.dmg':'📦','.app':'📦',
             '.py':'🐍','.js':'⚙️','.ts':'⚙️','.sh':'🔧','.bat':'🔧',
             '.txt':'📄','.md':'📝','.log':'📋',
             '.jpg':'🖼️','.jpeg':'🖼️','.png':'🖼️','.gif':'🖼️','.webp':'🖼️','.svg':'🎨',
             '.mp3':'🎵','.wav':'🎵','.flac':'🎵','.ogg':'🎵',
             '.mp4':'🎬','.mkv':'🎬','.avi':'🎬','.mov':'🎬',
             '.pdf':'📕','.doc':'📘','.docx':'📘','.xls':'📗','.xlsx':'📗',
             '.zip':'🗜️','.rar':'🗜️','.7z':'🗜️','.tar':'🗜️','.gz':'🗜️',
             '.json':'📊','.xml':'📊','.csv':'📊',
             '.html':'🌐','.css':'🎨','.cpp':'⚙️','.c':'⚙️','.java':'⚙️'}
        return m.get(ext, '📄')

    def _file_type(self, p: Path) -> str:
        if p.is_dir(): return 'Папка'
        ext = p.suffix.lower()
        types = {'.exe':'Приложение','.py':'Python скрипт','.txt':'Текстовый файл',
                 '.jpg':'Изображение JPEG','.png':'Изображение PNG','.gif':'GIF',
                 '.mp3':'Аудио MP3','.mp4':'Видео MP4','.pdf':'PDF документ',
                 '.zip':'ZIP архив','.json':'JSON данные','.html':'HTML страница'}
        return types.get(ext, ext.lstrip('.').upper() + ' файл' if ext else 'Файл')

    def _fmt_size(self, b: int) -> str:
        if b < 1024: return f'{b} B'
        if b < 1024**2: return f'{b/1024:.1f} KB'
        if b < 1024**3: return f'{b/1024**2:.1f} MB'
        return f'{b/1024**3:.1f} GB'


# ══════════════════════════════════════════════════
# БЛОКНОТ
# ══════════════════════════════════════════════════
class Notepad(AppWindow):
    def __init__(self, root, os_ref, file_path=None):
        super().__init__(root, os_ref, 'Блокнот', 680, 460, '📄')
        self.file_path = file_path
        self._build()
        if file_path:
            self._load(file_path)

    def _build(self):
        self.toolbar(self, [
            ('Новый', self._new),
            ('Открыть', self._open),
            ('💾 Сохранить', self._save, True),
            ('Сохранить как', self._save_as),
            None,
            ('📋 Копировать всё', self._copy_all),
            ('Статистика', self._stats),
        ])
        # Номера строк + текст
        container = self.frame()
        container.pack(fill='both', expand=True)
        self.text = scrolledtext.ScrolledText(
            container, bg='#0d0f18', fg='#c8d0e0',
            insertbackground='#60a5fa', font=FONT_MONO,
            relief='flat', bd=0, padx=12, pady=10,
            undo=True, wrap='none',
        )
        self.text.pack(fill='both', expand=True)
        self.status_var = tk.StringVar(value='Готово')
        tk.Label(self, textvariable=self.status_var, font=FONT_SMALL,
                 bg=T['surface2'], fg=T['text3'], anchor='w', padx=8).pack(fill='x')
        self.text.bind('<<Modified>>', self._on_change)

    def _load(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', content)
            self.title(f'📄 {Path(path).name} — Блокнот')
            self.status_var.set(f'Открыт: {path}')
        except Exception as e:
            messagebox.showerror('Ошибка', str(e))

    def _new(self):
        if messagebox.askyesno('Новый', 'Создать новый документ?'):
            self.text.delete('1.0', 'end'); self.file_path=None; self.title('📄 Блокнот')
    def _open(self):
        p = filedialog.askopenfilename(filetypes=[('Текст','*.txt *.md *.py *.js *.json *.html *.css *.xml *.csv *.log'),('Все','*.*')])
        if p: self.file_path=Path(p); self._load(p)
    def _save(self):
        if not self.file_path: self._save_as(); return
        try:
            with open(self.file_path,'w',encoding='utf-8') as f: f.write(self.text.get('1.0','end-1c'))
            self.status_var.set('Сохранено ✅')
        except Exception as e: messagebox.showerror('Ошибка',str(e))
    def _save_as(self):
        p = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Текст','*.txt'),('Все','*.*')])
        if p: self.file_path=Path(p); self._save()
    def _copy_all(self):
        self.clipboard_clear(); self.clipboard_append(self.text.get('1.0','end-1c')); self.status_var.set('Скопировано ✅')
    def _stats(self):
        t=self.text.get('1.0','end-1c'); w=len(t.split()); messagebox.showinfo('Статистика',f'Символов: {len(t)}\nСлов: {w}\nСтрок: {t.count(chr(10))+1}')
    def _on_change(self, e): self.text.edit_modified(False); self.status_var.set('Изменено')


# ══════════════════════════════════════════════════
# КАЛЬКУЛЯТОР
# ══════════════════════════════════════════════════
class Calculator(AppWindow):
    def __init__(self, root, os_ref):
        super().__init__(root, os_ref, 'Калькулятор', 270, 400, '🔢')
        self.resizable(False, False)
        self.expr = ''; self.just_eq = False
        self._build()

    def _build(self):
        self.configure(bg='#0d0f18')
        disp = tk.Frame(self, bg='#080b12')
        disp.pack(fill='x')
        self.expr_var = tk.StringVar()
        self.disp_var = tk.StringVar(value='0')
        tk.Label(disp, textvariable=self.expr_var, font=(FONT_MONO[0], 10),
                 bg='#080b12', fg=T['text3'], anchor='e', padx=14).pack(fill='x', pady=(10,0))
        tk.Label(disp, textvariable=self.disp_var, font=(FONT_MONO[0], 32, 'bold'),
                 bg='#080b12', fg=T['text'], anchor='e', padx=14).pack(fill='x', pady=(0,12))

        btns = [
            [('C','clr'),('%','pct'),('±','neg'),('÷','op')],
            [('7','7'),  ('8','8'),  ('9','9'),  ('×','op')],
            [('4','4'),  ('5','5'),  ('6','6'),  ('−','op')],
            [('1','1'),  ('2','2'),  ('3','3'),('+','op')],
            [('0','0'),  ('0','0'),  ('.','dot'),('=','eq')],
        ]
        grid = tk.Frame(self, bg='#0d0f18')
        grid.pack(fill='both', expand=True)
        for r, row in enumerate(btns):
            for c, (lbl, kind) in enumerate(row):
                bg = '#1e3a5f' if kind=='eq' else '#1a1d2e' if kind=='op' else '#141620'
                fg = '#60a5fa' if kind=='op' else '#e57373' if kind in ('clr','neg','pct') else T['text']
                b = tk.Button(grid, text=lbl, font=(FONT_MONO[0],17), bg=bg, fg=fg,
                              relief='flat', cursor='hand2', bd=0,
                              activebackground='#2a2e44', activeforeground='white',
                              command=lambda l=lbl, k=kind: self._press(l, k))
                b.grid(row=r, column=c, sticky='nsew', padx=1, pady=1)
        for i in range(5): grid.rowconfigure(i, weight=1)
        for i in range(4): grid.columnconfigure(i, weight=1)
        self.bind('<Key>', self._key)

    def _press(self, lbl, kind):
        d = self.disp_var.get()
        if kind == 'clr': self.disp_var.set('0'); self.expr=''; self.expr_var.set(''); self.just_eq=False
        elif kind == 'neg': self.disp_var.set(str(-float(d)) if d!='0' else '0')
        elif kind == 'pct': self.disp_var.set(str(float(d)/100))
        elif kind == 'op':
            m = {'÷':'/','×':'*','−':'-','+':'+'}
            self.expr = (d if self.just_eq else self.expr or d) + m[lbl]
            self.expr_var.set(self.expr); self.disp_var.set('0'); self.just_eq=False
        elif kind == 'dot':
            if '.' not in d: self.disp_var.set(d+'.')
        elif kind == 'eq':
            if self.expr:
                try:
                    result = eval(self.expr + d)
                    self.expr_var.set(self.expr + d + '=')
                    self.disp_var.set(str(round(result, 10)).rstrip('0').rstrip('.') or '0')
                    self.expr=''; self.just_eq=True
                except: self.disp_var.set('Ошибка')
        else:
            cur = self.disp_var.get()
            self.disp_var.set(lbl if cur=='0' or self.just_eq else cur+lbl if len(cur)<14 else cur)
            self.just_eq=False

    def _key(self, e):
        k=e.char
        if k in '0123456789': self._press(k,k)
        elif k=='.': self._press('.','dot')
        elif k in '+-*/': m={'+':'+','-':'−','*':'×','/':'÷'}; self._press(m[k],'op')
        elif e.keysym=='Return': self._press('=','eq')
        elif e.keysym in ('BackSpace','Delete'): d=self.disp_var.get(); self.disp_var.set(d[:-1] or '0')
        elif k.lower()=='c': self._press('C','clr')


# ══════════════════════════════════════════════════
# ТЕРМИНАЛ
# ══════════════════════════════════════════════════
class Terminal(AppWindow):
    def __init__(self, root, os_ref):
        super().__init__(root, os_ref, 'Терминал', 660, 420, '💻')
        self.cwd = str(Path.home())
        self.hist = []; self.h_idx = -1
        self._build()

    def _build(self):
        self.configure(bg='#060a10')
        self.out = scrolledtext.ScrolledText(
            self, bg='#060a10', fg='#c8f0c0', insertbackground='#c8f0c0',
            font=FONT_MONO, relief='flat', bd=0, padx=10, pady=8,
            state='disabled', wrap='word',
        )
        self.out.pack(fill='both', expand=True)
        self.out.tag_config('prompt', foreground='#4fc3f7')
        self.out.tag_config('error',  foreground='#ef9a9a')
        self.out.tag_config('info',   foreground='#80cbc4')
        self.out.tag_config('cmd',    foreground='#78909c')

        inp_frame = tk.Frame(self, bg='#060a10')
        inp_frame.pack(fill='x', padx=8, pady=(4,8))
        self.prompt_var = tk.StringVar()
        self._update_prompt()
        tk.Label(inp_frame, textvariable=self.prompt_var, font=FONT_MONO,
                 bg='#060a10', fg='#4fc3f7').pack(side='left')
        self.inp = tk.Entry(inp_frame, bg='#060a10', fg='#c8f0c0',
                            insertbackground='#c8f0c0', font=FONT_MONO,
                            relief='flat', bd=0)
        self.inp.pack(side='left', fill='x', expand=True, padx=(6,0))
        self.inp.bind('<Return>',   self._run)
        self.inp.bind('<Up>',       self._hist_up)
        self.inp.bind('<Down>',     self._hist_down)
        self.inp.bind('<Tab>',      self._autocomplete)
        self.inp.focus_set()
        self._write('NexOS Terminal v2.0\n', 'info')
        self._write("'help' — список команд\n\n", 'info')

    def _update_prompt(self):
        short = self.cwd.replace(str(Path.home()), '~')
        self.prompt_var.set(f'user@nexos:{short}$ ')

    def _write(self, text, tag=None):
        self.out.configure(state='normal')
        if tag: self.out.insert('end', text, tag)
        else:   self.out.insert('end', text)
        self.out.see('end')
        self.out.configure(state='disabled')

    def _run(self, e=None):
        cmd = self.inp.get().strip()
        if not cmd: return
        self._write(f'{self.prompt_var.get()}{cmd}\n', 'cmd')
        self.hist.insert(0, cmd); self.h_idx = -1
        self.inp.delete(0, 'end')
        self._exec(cmd)

    def _exec(self, cmd):
        parts = cmd.split()
        c = parts[0] if parts else ''

        # Встроенные команды
        if c == 'help':
            help_text = (
                '  help          — эта справка\n'
                '  ls / dir      — список файлов\n'
                '  cd <path>     — сменить папку\n'
                '  pwd           — текущий путь\n'
                '  mkdir <name>  — создать папку\n'
                '  rm <file>     — удалить файл\n'
                '  cat <file>    — показать файл\n'
                '  clear         — очистить\n'
                '  echo <text>   — вывод текста\n'
                '  run <file>    — запустить файл (.exe, .py, .sh...)\n'
                '  open <file>   — открыть системным приложением\n'
                '  explorer      — открыть проводник\n'
                '  python <file> — запустить Python скрипт\n'
                '  calc <expr>   — вычислить выражение\n'
                '  sysinfo       — о системе\n'
                '  <команда>     — выполнить системную команду\n'
            )
            self._write(help_text, 'info')

        elif c in ('ls', 'dir'):
            path = Path(parts[1]) if len(parts) > 1 else Path(self.cwd)
            try:
                items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                for item in items:
                    if not item.name.startswith('.'):
                        prefix = '📁 ' if item.is_dir() else '📄 '
                        self._write(f'  {prefix}{item.name}\n')
            except Exception as ex:
                self._write(f'ls: {ex}\n', 'error')

        elif c == 'cd':
            new = Path(parts[1]).expanduser() if len(parts) > 1 else Path.home()
            if not new.is_absolute():
                new = Path(self.cwd) / new
            new = new.resolve()
            if new.is_dir(): self.cwd = str(new); self._update_prompt()
            else: self._write(f'cd: нет такой папки: {parts[1] if len(parts)>1 else ""}\n', 'error')

        elif c == 'pwd':
            self._write(self.cwd + '\n')

        elif c == 'clear':
            self.out.configure(state='normal'); self.out.delete('1.0','end'); self.out.configure(state='disabled')

        elif c == 'echo':
            self._write(' '.join(parts[1:]) + '\n')

        elif c == 'mkdir':
            if len(parts) < 2: self._write('mkdir: нужно имя папки\n','error'); return
            try: (Path(self.cwd)/parts[1]).mkdir(exist_ok=True); self._write(f'Создана папка: {parts[1]}\n','info')
            except Exception as ex: self._write(str(ex)+'\n','error')

        elif c == 'rm':
            if len(parts) < 2: self._write('rm: нужно имя файла\n','error'); return
            p = Path(self.cwd)/parts[1]
            try: p.unlink() if p.is_file() else p.rmdir(); self._write(f'Удалено: {parts[1]}\n','info')
            except Exception as ex: self._write(str(ex)+'\n','error')

        elif c == 'cat':
            if len(parts) < 2: self._write('cat: нужно имя файла\n','error'); return
            p = Path(self.cwd)/parts[1]
            try:
                with open(p,'r',encoding='utf-8',errors='replace') as f:
                    self._write(f.read() + '\n')
            except Exception as ex: self._write(str(ex)+'\n','error')

        elif c == 'calc':
            try: self._write(str(eval(' '.join(parts[1:]))) + '\n')
            except: self._write('Ошибка вычисления\n','error')

        elif c == 'run':
            if len(parts) < 2: self._write('run: нужно имя файла\n','error'); return
            p = Path(self.cwd) / parts[1]
            if not p.exists(): self._write(f'Файл не найден: {p}\n','error'); return
            self._write(f'Запуск: {p}\n','info')
            self._run_external(str(p))

        elif c == 'python':
            if len(parts) < 2: self._write('python: нужен скрипт\n','error'); return
            p = Path(self.cwd)/parts[1]
            self._run_external_output(sys.executable, str(p))

        elif c == 'open':
            if len(parts) < 2: self._write('open: нужен файл\n','error'); return
            p = Path(self.cwd)/parts[1]
            try:
                if IS_WIN:   os.startfile(str(p))
                elif IS_MAC: subprocess.Popen(['open',str(p)])
                else:        subprocess.Popen(['xdg-open',str(p)])
                self._write(f'Открыто: {p.name}\n','info')
            except Exception as ex: self._write(str(ex)+'\n','error')

        elif c == 'explorer':
            self.os_ref.open_app('explorer')
            self._write('Открываю Проводник...\n','info')

        elif c == 'sysinfo':
            self._write(
                f'  OS:       {platform.system()} {platform.release()}\n'
                f'  Machine:  {platform.machine()}\n'
                f'  Python:   {sys.version.split()[0]}\n'
                f'  CWD:      {self.cwd}\n'
                f'  Home:     {Path.home()}\n', 'info')

        else:
            # Выполнить как системную команду
            self._run_system_cmd(cmd)

    def _run_external(self, path):
        def run():
            try:
                if IS_WIN: subprocess.Popen([path], cwd=self.cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:      subprocess.Popen([path], cwd=self.cwd)
                self.after(0, lambda: self._write('✅ Запущено\n','info'))
            except Exception as ex:
                self.after(0, lambda: self._write(f'Ошибка: {ex}\n','error'))
        threading.Thread(target=run, daemon=True).start()

    def _run_external_output(self, *args):
        def run():
            try:
                result = subprocess.run(list(args), capture_output=True, text=True, timeout=30, cwd=self.cwd)
                if result.stdout: self.after(0, lambda: self._write(result.stdout))
                if result.stderr: self.after(0, lambda: self._write(result.stderr,'error'))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self._write('Таймаут (30с)\n','error'))
            except Exception as ex:
                self.after(0, lambda: self._write(f'Ошибка: {ex}\n','error'))
        threading.Thread(target=run, daemon=True).start()

    def _run_system_cmd(self, cmd):
        def run():
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=self.cwd)
                out = result.stdout + result.stderr
                self.after(0, lambda: self._write(out if out else '(нет вывода)\n'))
            except subprocess.TimeoutExpired:
                self.after(0, lambda: self._write('Таймаут\n','error'))
            except Exception as ex:
                self.after(0, lambda: self._write(f'{ex}\n','error'))
        threading.Thread(target=run, daemon=True).start()

    def _hist_up(self, e):
        self.h_idx = min(self.h_idx+1, len(self.hist)-1)
        if self.hist: self.inp.delete(0,'end'); self.inp.insert(0, self.hist[self.h_idx])
    def _hist_down(self, e):
        self.h_idx = max(self.h_idx-1, -1)
        self.inp.delete(0,'end')
        if self.h_idx >= 0: self.inp.insert(0, self.hist[self.h_idx])
    def _autocomplete(self, e):
        text = self.inp.get()
        if not text: return 'break'
        # Автодополнение файлов
        parts = text.split()
        if len(parts) >= 1:
            prefix = parts[-1] if len(parts) > 1 else ''
            base = Path(self.cwd)
            matches = [p.name for p in base.iterdir() if p.name.startswith(prefix) and not p.name.startswith('.')]
            if len(matches) == 1:
                if len(parts) > 1: self.inp.delete(0,'end'); self.inp.insert(0, ' '.join(parts[:-1]+[matches[0]]))
                else: self.inp.delete(0,'end'); self.inp.insert(0, matches[0])
            elif len(matches) > 1:
                self._write('\n  '.join([''] + matches) + '\n')
        return 'break'


# ══════════════════════════════════════════════════
# ИНФОРМАЦИЯ О СИСТЕМЕ
# ══════════════════════════════════════════════════
class SysInfo(AppWindow):
    def __init__(self, root, os_ref):
        super().__init__(root, os_ref, 'О системе', 500, 420, 'ℹ️')
        self.resizable(False, False)
        self._build()

    def _build(self):
        tk.Label(self, text='⊞  NexOS Desktop', font=(FONT_MAIN[0], 20, 'bold'),
                 bg=T['surface'], fg=T['text']).pack(pady=(24,4))
        tk.Label(self, text='Python Edition — работает на реальной ОС',
                 font=FONT_MAIN, bg=T['surface'], fg=T['text2']).pack()
        tk.Frame(self, bg=T['border'], height=1).pack(fill='x', padx=20, pady=16)

        info = [
            ('ОС',        f'{platform.system()} {platform.release()}'),
            ('Машина',    platform.machine()),
            ('Процессор', platform.processor() or 'Неизвестно'),
            ('Python',    sys.version.split()[0]),
            ('Домашняя',  str(Path.home())),
            ('Платформа', sys.platform),
        ]
        grid = tk.Frame(self, bg=T['surface'])
        grid.pack(fill='x', padx=24)
        for i, (k, v) in enumerate(info):
            tk.Label(grid, text=k+':', font=(FONT_MAIN[0], 10, 'bold'),
                     bg=T['surface'], fg=T['text2'], anchor='e', width=14).grid(row=i, column=0, sticky='e', pady=5, padx=(0,12))
            tk.Label(grid, text=v, font=FONT_MONO, bg=T['surface'], fg=T['text'], anchor='w').grid(row=i, column=1, sticky='w', pady=5)

        tk.Frame(self, bg=T['border'], height=1).pack(fill='x', padx=20, pady=16)
        note = ('💡 .exe файлы можно запускать через Проводник или Терминал\n'
                '   (команда run <файл.exe>) — только на Windows\n'
                '   На Linux/macOS используется Wine или нативные форматы')
        tk.Label(self, text=note, font=FONT_SMALL, bg=T['surface'], fg=T['text3'],
                 justify='left', wraplength=440).pack(padx=24, anchor='w')


# ══════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ══════════════════════════════════════════════════
if __name__ == '__main__':
    app = NexOS()
    app.run()
