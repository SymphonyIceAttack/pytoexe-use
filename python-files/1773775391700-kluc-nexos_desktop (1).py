"""
NexOS Desktop — Python Edition v3
===================================
Запуск:
    python nexos_desktop.py

Зависимости (только при первом запуске установятся автоматически):
    pip install tkinterweb pillow

Особенности:
  ✦ Все окна открываются ВНУТРИ рабочего стола (не как Toplevel)
  ✦ Встроенный браузер с Google (через tkinterweb + HtmlFrame)
  ✦ Перетаскивание окон мышью
  ✦ Изменение размера (уголок)
  ✦ Минимизация / Максимизация / Закрытие
  ✦ Z-порядок (клик поднимает окно)
  ✦ Файловый менеджер с запуском .exe
  ✦ Блокнот, Калькулятор, Терминал
"""

import sys, os, subprocess, threading, platform, shutil, math
from pathlib import Path
from datetime import datetime

# ── Автоустановка зависимостей ──────────────────────────────────────
def ensure(pkg, import_name=None):
    import_name = import_name or pkg
    try:
        __import__(import_name)
    except ImportError:
        print(f"[NexOS] Устанавливаю {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure("pillow", "PIL")

# Tkinterweb для браузера — необязательный, без него браузер ограничен
try:
    ensure("tkinterweb")
    from tkinterweb import HtmlFrame
    HAS_WEB = True
except Exception:
    HAS_WEB = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font as tkfont

IS_WIN  = platform.system() == "Windows"
IS_MAC  = platform.system() == "Darwin"

# ══════════════════════════════════════════════════
# ТЕМА
# ══════════════════════════════════════════════════
C = {
    "desk":    "#0a0c15",
    "tb":      "#07090f",
    "win":     "#12141f",
    "win2":    "#1a1c28",
    "win3":    "#22253a",
    "title":   "#0f1120",
    "ac":      "#0078d4",
    "ac2":     "#1a90e8",
    "tx":      "#eaeaea",
    "tx2":     "#7a82a0",
    "tx3":     "#454c66",
    "bd":      "#1e2133",
    "red":     "#c0392b",
    "green":   "#27ae60",
    "sel":     "#0c3d6e",
}

FONT      = lambda s=10, w="normal": ("Segoe UI" if IS_WIN else "Helvetica Neue" if IS_MAC else "Ubuntu", s, w)
MONO      = lambda s=10: ("Cascadia Code" if IS_WIN else "Monaco" if IS_MAC else "DejaVu Sans Mono", s)
TITLE_H   = 32   # высота заголовка окна
MIN_W, MIN_H = 280, 180


# ══════════════════════════════════════════════════
# ОКОННЫЙ МЕНЕДЖЕР (внутри Canvas)
# ══════════════════════════════════════════════════
class WindowManager:
    """Управляет окнами-фреймами внутри одного Canvas рабочего стола."""

    def __init__(self, canvas: tk.Canvas, taskbar):
        self.canvas   = canvas
        self.taskbar  = taskbar
        self.windows  = {}   # id -> WinFrame
        self._z_top   = 1
        self._win_cnt = 0

    def open(self, win_id: str, title: str, icon: str, builder_fn,
             w=700, h=460, x=None, y=None):
        """Открыть окно. builder_fn(body_frame) строит содержимое."""
        if win_id in self.windows:
            self.raise_win(win_id)
            return self.windows[win_id]

        cw = self.canvas.winfo_width()  or 1200
        ch = self.canvas.winfo_height() or 700
        n  = self._win_cnt
        if x is None: x = max(20, min((cw - w) // 2 + n % 6 * 24, cw - w - 20))
        if y is None: y = max(10, min((ch - h) // 2 + n % 6 * 24, ch - h - 10))

        win = WinFrame(self, win_id, title, icon, w, h, x, y, builder_fn)
        self.windows[win_id] = win
        self._win_cnt += 1
        self.taskbar.add(win_id, icon, title)
        self.raise_win(win_id)
        return win

    def close(self, win_id: str):
        if win_id in self.windows:
            self.windows[win_id].destroy_self()
            del self.windows[win_id]
            self.taskbar.remove(win_id)

    def raise_win(self, win_id: str):
        if win_id not in self.windows: return
        self._z_top += 1
        w = self.windows[win_id]
        w.frame.lift()
        w.minimized = False
        w.frame.place(x=w.x, y=w.y)
        self.taskbar.set_active(win_id)

    def toggle(self, win_id: str):
        if win_id not in self.windows: return
        w = self.windows[win_id]
        if w.minimized:
            w.minimized = False
            w.frame.place(x=w.x, y=w.y)
            self.raise_win(win_id)
        else:
            w.minimized = True
            w.frame.place_forget()
            self.taskbar.set_active(None)


# ══════════════════════════════════════════════════
# ОКНО-ФРЕЙМ
# ══════════════════════════════════════════════════
class WinFrame:
    def __init__(self, wm: WindowManager, win_id, title, icon, w, h, x, y, builder_fn):
        self.wm       = wm
        self.win_id   = win_id
        self.title    = title
        self.icon     = icon
        self.w        = w
        self.h        = h
        self.x        = x
        self.y        = y
        self.minimized= False
        self.maximized= False
        self._prev    = None   # сохранённые размеры до max

        parent = wm.canvas
        self.frame = tk.Frame(parent, bg=C["win"],
                              bd=0, highlightthickness=1,
                              highlightbackground=C["bd"],
                              highlightcolor=C["ac"])
        self.frame.place(x=x, y=y, width=w, height=h)

        self._build_titlebar()
        self._build_body(builder_fn)
        self._build_resize_handle()

        # Поднять при клике в любом месте
        self.frame.bind("<ButtonPress-1>", self._on_click, add="+")

    # ── Заголовок
    def _build_titlebar(self):
        tb = tk.Frame(self.frame, bg=C["title"], height=TITLE_H, cursor="fleur")
        tb.pack(fill="x")
        tb.pack_propagate(False)

        # Иконка + заголовок
        tk.Label(tb, text=self.icon, font=FONT(13),
                 bg=C["title"], fg=C["tx"]).pack(side="left", padx=(10,4))
        self.title_lbl = tk.Label(tb, text=self.title, font=FONT(10),
                                   bg=C["title"], fg=C["tx"])
        self.title_lbl.pack(side="left", fill="x", expand=True)

        # Кнопки управления
        btn_frame = tk.Frame(tb, bg=C["title"])
        btn_frame.pack(side="right")
        self._wbtn(btn_frame, "─", self._minimize, C["win3"])
        self._wbtn(btn_frame, "□", self._toggle_max, C["win3"])
        self._wbtn(btn_frame, "✕", lambda: self.wm.close(self.win_id), C["red"])

        # Разделитель
        tk.Frame(self.frame, bg=C["bd"], height=1).pack(fill="x")

        # Перетаскивание
        self._drag_x = self._drag_y = 0
        for w in (tb, self.title_lbl):
            w.bind("<ButtonPress-1>",   self._drag_start)
            w.bind("<B1-Motion>",       self._drag_move)
            w.bind("<Double-Button-1>", self._toggle_max)

    def _wbtn(self, parent, txt, cmd, hover_bg):
        b = tk.Label(parent, text=txt, font=FONT(11), bg=C["title"], fg=C["tx2"],
                     width=4, cursor="hand2")
        b.pack(side="left")
        b.bind("<Button-1>", lambda e: cmd())
        b.bind("<Enter>",    lambda e, h=hover_bg: b.configure(bg=h, fg=C["tx"]))
        b.bind("<Leave>",    lambda e: b.configure(bg=C["title"], fg=C["tx2"]))

    # ── Тело окна
    def _build_body(self, builder_fn):
        self.body = tk.Frame(self.frame, bg=C["win"])
        self.body.pack(fill="both", expand=True)
        builder_fn(self.body)

    # ── Ручка изменения размера
    def _build_resize_handle(self):
        rh = tk.Frame(self.frame, bg=C["win3"], width=14, height=14, cursor="size_nw_se")
        rh.place(relx=1.0, rely=1.0, anchor="se")
        rh.bind("<ButtonPress-1>",  self._res_start)
        rh.bind("<B1-Motion>",      self._res_move)

    # ── Drag
    def _drag_start(self, e):
        self._drag_x = e.x_root - self.x
        self._drag_y = e.y_root - self.y
        self._on_click(e)

    def _drag_move(self, e):
        if self.maximized: return
        self.x = max(0, e.x_root - self._drag_x)
        self.y = max(0, e.y_root - self._drag_y)
        self.frame.place(x=self.x, y=self.y)

    # ── Resize
    def _res_start(self, e):
        self._res_sx = e.x_root
        self._res_sy = e.y_root
        self._res_sw = self.w
        self._res_sh = self.h

    def _res_move(self, e):
        if self.maximized: return
        self.w = max(MIN_W, self._res_sw + e.x_root - self._res_sx)
        self.h = max(MIN_H, self._res_sh + e.y_root - self._res_sy)
        self.frame.place(width=self.w, height=self.h)

    # ── Max / Min
    def _minimize(self):
        self.wm.toggle(self.win_id)

    def _toggle_max(self, e=None):
        if self.maximized:
            self.maximized = False
            px, py, pw, ph = self._prev
            self.x, self.y, self.w, self.h = px, py, pw, ph
            self.frame.config(highlightthickness=1)
        else:
            self._prev = (self.x, self.y, self.w, self.h)
            cw = self.wm.canvas.winfo_width()
            ch = self.wm.canvas.winfo_height()
            self.x, self.y, self.w, self.h = 0, 0, cw, ch
            self.maximized = True
            self.frame.config(highlightthickness=0)
        self.frame.place(x=self.x, y=self.y, width=self.w, height=self.h)

    def _on_click(self, e):
        self.wm.raise_win(self.win_id)

    def destroy_self(self):
        self.frame.destroy()


# ══════════════════════════════════════════════════
# ТАСКБАР
# ══════════════════════════════════════════════════
class Taskbar:
    def __init__(self, root, wm_ref_fn):
        self.root     = root
        self.wm_ref   = wm_ref_fn   # callable → WindowManager
        self._buttons = {}
        self._active  = None

        self.bar = tk.Frame(root, bg=C["tb"], height=48)
        self.bar.pack(fill="x", side="bottom")
        self.bar.pack_propagate(False)

        # Кнопка Пуск
        self._start_btn = tk.Label(self.bar, text="⊞", font=FONT(20),
                                    bg=C["tb"], fg=C["tx"], cursor="hand2", padx=14)
        self._start_btn.pack(side="left")
        self._start_btn.bind("<Button-1>", lambda e: self._show_start())

        # Сепаратор
        tk.Frame(self.bar, bg=C["bd"], width=1).pack(side="left", fill="y", pady=8)

        # Область кнопок приложений
        self.apps_frame = tk.Frame(self.bar, bg=C["tb"])
        self.apps_frame.pack(side="left", fill="y", padx=6)

        # Системный трей
        tray = tk.Frame(self.bar, bg=C["tb"])
        tray.pack(side="right", padx=12)
        for ico in ["📶", "🔊"]:
            tk.Label(tray, text=ico, font=FONT(13), bg=C["tb"],
                     fg=C["tx2"]).pack(side="left", padx=3)

        # Часы
        self._clock_t = tk.StringVar()
        self._clock_d = tk.StringVar()
        clk = tk.Frame(tray, bg=C["tb"])
        clk.pack(side="left", padx=(6, 0))
        tk.Label(clk, textvariable=self._clock_t, font=FONT(11, "bold"),
                 bg=C["tb"], fg=C["tx"]).pack(anchor="e")
        tk.Label(clk, textvariable=self._clock_d, font=FONT(8),
                 bg=C["tb"], fg=C["tx2"]).pack(anchor="e")
        self._tick()

    def _tick(self):
        now = datetime.now()
        self._clock_t.set(now.strftime("%H:%M:%S"))
        self._clock_d.set(now.strftime("%d.%m.%Y"))
        self.root.after(1000, self._tick)

    def add(self, win_id, icon, title):
        btn = tk.Label(self.apps_frame, text=f"{icon}", font=FONT(16),
                       bg=C["tb"], fg=C["tx"], cursor="hand2",
                       padx=6, pady=2, relief="flat")
        btn.pack(side="left", padx=2)
        btn.bind("<Button-1>", lambda e: self.wm_ref().toggle(win_id))
        btn.bind("<Enter>", lambda e: self._tooltip(btn, title))
        btn.bind("<Leave>", lambda e: self._hide_tip())
        self._buttons[win_id] = btn
        self._underline(win_id, True)

    def remove(self, win_id):
        if win_id in self._buttons:
            self._buttons[win_id].destroy()
            del self._buttons[win_id]

    def set_active(self, win_id):
        self._active = win_id
        for wid, btn in self._buttons.items():
            active = wid == win_id
            btn.configure(
                bg=C["sel"] if active else C["tb"],
                fg=C["tx"] if active else C["tx2"],
            )

    def _underline(self, win_id, on):
        pass  # визуальный индикатор через цвет кнопки

    def _tooltip(self, widget, text):
        self._tip = tk.Toplevel(self.root)
        self._tip.wm_overrideredirect(True)
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() - 28
        self._tip.geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=text, font=FONT(9), bg="#1e2133",
                 fg=C["tx"], relief="flat", padx=8, pady=3).pack()

    def _hide_tip(self):
        try: self._tip.destroy()
        except: pass

    def _show_start(self):
        wm = self.wm_ref()
        pop = tk.Toplevel(self.root)
        pop.wm_overrideredirect(True)
        pop.configure(bg=C["win2"])
        pop.attributes("-topmost", True)
        bx = self._start_btn.winfo_rootx()
        by = self._start_btn.winfo_rooty() - 360
        pop.geometry(f"280x360+{bx}+{by}")
        pop.focus_set()
        pop.bind("<FocusOut>", lambda e: pop.destroy())

        tk.Label(pop, text="NexOS", font=FONT(16, "bold"),
                 bg=C["win2"], fg=C["tx"]).pack(pady=14)
        tk.Frame(pop, bg=C["bd"], height=1).pack(fill="x", padx=10)

        APPS = [
            ("📁", "Проводник",    "explorer"),
            ("🌐", "Браузер",      "browser"),
            ("📄", "Блокнот",      "notepad"),
            ("🔢", "Калькулятор",  "calculator"),
            ("💻", "Терминал",     "terminal"),
            ("⚙️", "Параметры",   "settings"),
        ]
        grid = tk.Frame(pop, bg=C["win2"])
        grid.pack(fill="both", expand=True, padx=8, pady=8)
        for i, (ico, name, app_id) in enumerate(APPS):
            r, c = divmod(i, 3)
            f = tk.Frame(grid, bg=C["win3"], width=78, height=72, cursor="hand2")
            f.grid(row=r, column=c, padx=4, pady=4)
            f.grid_propagate(False)
            def click(a=app_id, p=pop):
                p.destroy(); open_app(wm, a)
            tk.Label(f, text=ico, font=FONT(22), bg=C["win3"],
                     fg=C["tx"], cursor="hand2").pack(pady=(10, 0))
            tk.Label(f, text=name, font=FONT(8), bg=C["win3"],
                     fg=C["tx2"], cursor="hand2").pack()
            for w in f.winfo_children(): w.bind("<Button-1>", lambda e, c=click: c())
            f.bind("<Button-1>", lambda e, c=click: c())
            f.bind("<Enter>", lambda e, fr=f: fr.configure(bg=C["ac"]))
            f.bind("<Leave>", lambda e, fr=f: fr.configure(bg=C["win3"]))

        tk.Frame(pop, bg=C["bd"], height=1).pack(fill="x", padx=10)
        tk.Button(pop, text="⏻  Выключить", font=FONT(10),
                  bg=C["win2"], fg="#e57373", relief="flat", cursor="hand2",
                  command=self.root.quit).pack(pady=8)


# ══════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ ОТКРЫТИЯ ПРИЛОЖЕНИЙ
# ══════════════════════════════════════════════════
def open_app(wm: WindowManager, app_id: str, **kw):
    meta = {
        "explorer":   ("📁", "Проводник",    700, 500, build_explorer),
        "browser":    ("🌐", "Браузер",      900, 620, build_browser),
        "notepad":    ("📄", "Блокнот",      640, 440, build_notepad),
        "calculator": ("🔢", "Калькулятор",  270, 400, build_calculator),
        "terminal":   ("💻", "Терминал",     640, 420, build_terminal),
        "settings":   ("⚙️", "Параметры",  580, 460, build_settings),
    }
    if app_id not in meta: return
    ico, title, w, h, builder = meta[app_id]
    wm.open(app_id, title, ico, lambda body: builder(body, wm), w, h)


# ══════════════════════════════════════════════════
# ПРИЛОЖЕНИЯ — СТРОИТЕЛИ
# ══════════════════════════════════════════════════

# ── Утилиты ─────────────────────────────────────
def lbl(parent, text="", size=10, color=None, **kw):
    kw.setdefault("bg", parent.cget("bg"))
    return tk.Label(parent, text=text, font=FONT(size),
                    fg=color or C["tx"], **kw)

def btn(parent, text, cmd, accent=False, danger=False, **kw):
    bg = C["ac"] if accent else C["red"] if danger else C["win3"]
    fg = C["tx"]
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, font=FONT(9),
                  relief="flat", cursor="hand2",
                  activebackground=C["ac2"] if accent else C["win2"],
                  activeforeground=C["tx"],
                  padx=10, pady=4, **kw)
    return b

def toolbar(parent, items):
    tb = tk.Frame(parent, bg=C["win2"])
    tb.pack(fill="x")
    tk.Frame(parent, bg=C["bd"], height=1).pack(fill="x")
    for item in items:
        if item is None:
            tk.Frame(tb, bg=C["bd"], width=1).pack(side="left", fill="y", padx=3, pady=5)
        else:
            txt, cmd = item[0], item[1]
            acc = len(item) > 2 and item[2]
            btn(tb, txt, cmd, accent=acc).pack(side="left", padx=3, pady=5)
    return tb

def entry_w(parent, **kw):
    kw.setdefault("bg", C["win3"])
    kw.setdefault("fg", C["tx"])
    kw.setdefault("insertbackground", C["tx"])
    kw.setdefault("relief", "flat")
    kw.setdefault("font", FONT(10))
    kw.setdefault("bd", 4)
    return tk.Entry(parent, **kw)

def sep(parent):
    tk.Frame(parent, bg=C["bd"], height=1).pack(fill="x")


# ── ФАЙЛОВЫЙ МЕНЕДЖЕР ────────────────────────────
def build_explorer(body, wm):
    state = {"path": Path.home(), "hist": [Path.home()], "hidx": 0, "sel": None}
    SIDEBAR = [
        ("🖥️", "Рабочий стол", Path.home() / "Desktop"),
        ("📄", "Документы",    Path.home() / "Documents"),
        ("⬇️", "Загрузки",    Path.home() / "Downloads"),
        ("🖼️", "Изображения",  Path.home() / "Pictures"),
        ("🎵", "Музыка",       Path.home() / "Music"),
        ("🎬", "Видео",        Path.home() / "Videos"),
        ("🏠", "Домашняя",     Path.home()),
    ]

    def navigate(p, push=True):
        p = Path(p)
        if not p.exists(): messagebox.showerror("Ошибка", f"Путь не найден:\n{p}"); return
        if push and state["hist"][state["hidx"]] != p:
            state["hist"] = state["hist"][:state["hidx"]+1] + [p]
            state["hidx"] = len(state["hist"]) - 1
        state["path"] = p; state["sel"] = None
        populate()

    def populate():
        tree.delete(*tree.get_children())
        path_var.set(str(state["path"]))
        try:
            items = sorted(state["path"].iterdir(),
                           key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            messagebox.showerror("Нет доступа", str(state["path"])); return
        for item in items:
            if item.name.startswith("."): continue
            try:
                st = item.stat()
                ico = file_icon(item)
                sz  = fmt_size(st.st_size) if item.is_file() else "—"
                mt  = datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y %H:%M")
                kind = file_type(item)
                tree.insert("", "end", iid=str(item),
                            values=(f"{ico}  {item.name}", kind, sz, mt))
            except: continue
        status_var.set(f"{len(tree.get_children())} объектов  |  {state['path']}")

    def on_dbl(e):
        sel = tree.selection()
        if not sel: return
        p = Path(sel[0])
        if p.is_dir(): navigate(p)
        else: open_file(p)

    def on_sel(e):
        sel = tree.selection()
        state["sel"] = Path(sel[0]) if sel else None

    def open_file(p=None):
        p = p or state["sel"]
        if not p: return
        ext = p.suffix.lower()
        if ext in ('.txt','.md','.py','.js','.json','.html','.css','.log','.sh','.bat','.xml','.csv','.ts','.ini','.cfg'):
            # Открыть в блокноте в том же рабочем столе
            def build_np(body): build_notepad(body, wm, file_path=p)
            wm.open(f"notepad_{p.name}", f"📄 {p.name}", "📄",
                    lambda b, fn=build_np: fn(b), 640, 440)
        else:
            open_system(p)

    def run_file():
        p = state["sel"]
        if not p or not p.is_file():
            messagebox.showinfo("NexOS", "Выберите файл"); return
        ext = p.suffix.lower()
        if ext == ".exe" and not IS_WIN:
            if messagebox.askyesno("Wine?", f"Запустить {p.name} через Wine?"):
                if shutil.which("wine"): launch(["wine", str(p)])
                else: messagebox.showerror("Wine не найден", "Установите Wine:\n  sudo apt install wine")
        elif ext == ".exe" and IS_WIN:
            if messagebox.askyesno("Запустить?", f"▶ Запустить:\n{p.name}\n\n⚠️ Только доверенные файлы!"):
                launch([str(p)])
        elif ext == ".py":
            if messagebox.askyesno("Python?", f"Запустить скрипт:\n{p.name}"):
                launch([sys.executable, str(p)])
        elif ext in (".sh", ".bash") and not IS_WIN:
            if messagebox.askyesno("Shell?", f"Запустить:\n{p.name}"):
                launch(["bash", str(p)])
        elif ext in (".bat", ".cmd") and IS_WIN:
            if messagebox.askyesno("Bat?", f"Запустить:\n{p.name}"):
                launch([str(p)])
        else:
            open_system(p)

    def launch(args):
        def run():
            try:
                kw = {"creationflags": subprocess.CREATE_NEW_CONSOLE} if IS_WIN else {}
                proc = subprocess.Popen(args, **kw)
                body.after(0, lambda: status_var.set(f"✅ Запущено PID {proc.pid}"))
            except Exception as ex:
                body.after(0, lambda: messagebox.showerror("Ошибка", str(ex)))
        threading.Thread(target=run, daemon=True).start()

    def open_system(p):
        try:
            if IS_WIN:   os.startfile(str(p))
            elif IS_MAC: subprocess.Popen(["open", str(p)])
            else:        subprocess.Popen(["xdg-open", str(p)])
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))

    def upload_files():
        paths = filedialog.askopenfilenames(initialdir=str(state["path"]))
        if not paths: return
        for src in paths:
            try: shutil.copy2(src, state["path"] / Path(src).name)
            except Exception as ex: messagebox.showerror("Ошибка", str(ex))
        populate()

    def upload_folder():
        src = filedialog.askdirectory(initialdir=str(Path.home()))
        if not src: return
        try:
            shutil.copytree(src, state["path"] / Path(src).name)
            populate()
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))

    def delete_file():
        p = state["sel"]
        if not p: return
        if messagebox.askyesno("Удалить?", f"Удалить «{p.name}»?"):
            try:
                shutil.rmtree(str(p)) if p.is_dir() else p.unlink()
                populate()
            except Exception as ex: messagebox.showerror("Ошибка", str(ex))

    def new_folder():
        d = tk.Toplevel(); d.title("Папка"); d.configure(bg=C["win"]); d.geometry("280x80")
        v = tk.StringVar(value="Новая папка")
        e = entry_w(d, textvariable=v, width=30); e.pack(padx=12, pady=(12,4)); e.select_range(0, "end"); e.focus_set()
        def do():
            nm = v.get().strip()
            if nm:
                try: (state["path"]/nm).mkdir(exist_ok=True); populate()
                except Exception as ex: messagebox.showerror("Ошибка", str(ex))
            d.destroy()
        e.bind("<Return>", lambda ev: do())
        btn(d, "Создать", do, True).pack(pady=4)

    # ── Навигация
    nav = tk.Frame(body, bg=C["win2"]); nav.pack(fill="x")
    btn(nav, "◀", lambda: navigate(state["hist"][max(0, state["hidx"]-1)], False) or state.update({"hidx": max(0, state["hidx"]-1)})).pack(side="left", padx=(5,2), pady=4)
    btn(nav, "▶", lambda: navigate(state["hist"][min(len(state["hist"])-1, state["hidx"]+1)], False) or state.update({"hidx": min(len(state["hist"])-1, state["hidx"]+1)})).pack(side="left", padx=2, pady=4)
    btn(nav, "↑", lambda: navigate(state["path"].parent)).pack(side="left", padx=2, pady=4)
    path_var = tk.StringVar(value=str(state["path"]))
    pe = entry_w(nav, textvariable=path_var); pe.pack(side="left", fill="x", expand=True, padx=6, pady=4)
    pe.bind("<Return>", lambda e: navigate(path_var.get()))
    tk.Frame(body, bg=C["bd"], height=1).pack(fill="x")

    # ── Тулбар
    tb2 = tk.Frame(body, bg=C["win2"]); tb2.pack(fill="x")
    btn(tb2, "⬆ Загрузить файлы",  upload_files,  True).pack(side="left", padx=3, pady=5)
    btn(tb2, "📂 Загрузить папку", upload_folder, True).pack(side="left", padx=2, pady=5)
    tk.Frame(tb2, bg=C["bd"], width=1).pack(side="left", fill="y", padx=4, pady=5)
    btn(tb2, "▶ Запустить",    run_file).pack(side="left", padx=2, pady=5)
    btn(tb2, "👁 Открыть",      open_file).pack(side="left", padx=2, pady=5)
    btn(tb2, "🗑 Удалить",      delete_file).pack(side="left", padx=2, pady=5)
    btn(tb2, "➕ Папка",        new_folder).pack(side="left", padx=2, pady=5)
    sep(body)

    # ── Основная зона
    main = tk.Frame(body, bg=C["win"]); main.pack(fill="both", expand=True)

    # Сайдбар
    side = tk.Frame(main, bg=C["win2"], width=155); side.pack(side="left", fill="y"); side.pack_propagate(False)
    tk.Frame(side, bg=C["bd"], width=1).pack(side="right", fill="y")
    lbl(side, "БЫСТРЫЙ ДОСТУП", 8, C["tx3"]).pack(anchor="w", padx=8, pady=(10,4))
    for ico, name, path in SIDEBAR:
        def mk_click(p=path):
            return lambda e: navigate(p) if p.exists() else None
        l = tk.Label(side, text=f"{ico} {name}", font=FONT(9), bg=C["win2"],
                     fg=C["tx2"], anchor="w", cursor="hand2", padx=10)
        l.pack(fill="x", pady=1)
        l.bind("<Button-1>", mk_click())
        l.bind("<Enter>", lambda e, w=l: w.configure(bg=C["win3"]))
        l.bind("<Leave>", lambda e, w=l: w.configure(bg=C["win2"]))

    # Список файлов
    lf = tk.Frame(main, bg=C["win"]); lf.pack(fill="both", expand=True)
    cols = ("name", "type", "size", "modified")
    tree = ttk.Treeview(lf, columns=cols, show="headings", selectmode="browse")
    for col, w, anc, hdr in [("name",320,"w","Имя"),("type",110,"w","Тип"),("size",80,"e","Размер"),("modified",140,"w","Изменён")]:
        tree.heading(col, text=hdr, anchor=anc)
        tree.column(col, width=w, anchor=anc)
    vsb = ttk.Scrollbar(lf, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)
    tree.bind("<Double-Button-1>", on_dbl)
    tree.bind("<<TreeviewSelect>>", on_sel)

    status_var = tk.StringVar()
    tk.Label(body, textvariable=status_var, font=FONT(8), bg=C["win2"],
             fg=C["tx3"], anchor="w", padx=8).pack(fill="x")

    populate()


# ── БРАУЗЕР ─────────────────────────────────────
def build_browser(body, wm):
    URL_HOME = "https://www.google.com"

    nav = tk.Frame(body, bg=C["win2"]); nav.pack(fill="x")
    btn(nav, "◀", lambda: go_back()).pack(side="left", padx=(5,2), pady=4)
    btn(nav, "▶", lambda: go_fwd()).pack(side="left", padx=2, pady=4)
    btn(nav, "🏠", lambda: load(URL_HOME)).pack(side="left", padx=2, pady=4)
    btn(nav, "🔄", lambda: reload_page()).pack(side="left", padx=2, pady=4)

    url_var = tk.StringVar(value=URL_HOME)
    ue = entry_w(nav, textvariable=url_var)
    ue.pack(side="left", fill="x", expand=True, padx=6, pady=4)
    ue.bind("<Return>", lambda e: load(url_var.get()))

    btn(nav, "→", lambda: load(url_var.get()), True).pack(side="right", padx=4, pady=4)
    sep(body)

    content = tk.Frame(body, bg=C["win"]); content.pack(fill="both", expand=True)

    if HAS_WEB:
        # Реальный браузер через tkinterweb
        hf = HtmlFrame(content, messages_enabled=False)
        hf.pack(fill="both", expand=True)

        def load(url):
            url = url.strip()
            if not url.startswith("http"):
                # поиск Google
                from urllib.parse import quote
                url = f"https://www.google.com/search?q={quote(url)}"
            url_var.set(url)
            hf.load_url(url)

        def go_back():  hf.go_back()
        def go_fwd():   hf.go_forward()
        def reload_page(): hf.load_url(url_var.get())

        hf.on_url_change(lambda url: url_var.set(url))
        load(URL_HOME)

    else:
        # Fallback — информация об установке
        msg_frame = tk.Frame(content, bg=C["win"]); msg_frame.pack(expand=True)
        tk.Label(msg_frame, text="🌐", font=FONT(48), bg=C["win"], fg=C["tx2"]).pack(pady=(30,8))
        tk.Label(msg_frame, text="Браузер недоступен", font=FONT(16, "bold"),
                 bg=C["win"], fg=C["tx"]).pack()
        tk.Label(msg_frame,
                 text="Для работы браузера установите tkinterweb:\n\n  pip install tkinterweb\n\nЗатем перезапустите NexOS.",
                 font=FONT(11), bg=C["win"], fg=C["tx2"], justify="center").pack(pady=12)

        def install_now():
            subprocess.Popen([sys.executable, "-m", "pip", "install", "tkinterweb"])
            messagebox.showinfo("Установка", "Установка запущена.\nПерезапустите NexOS после завершения.")

        btn(msg_frame, "Установить автоматически", install_now, True).pack(pady=8)

        def go_back(): pass
        def go_fwd(): pass
        def reload_page(): pass


# ── БЛОКНОТ ──────────────────────────────────────
def build_notepad(body, wm, file_path=None):
    state = {"path": file_path}

    toolbar(body, [
        ("Новый",      lambda: new_doc()),
        ("📂 Открыть", lambda: open_doc()),
        ("💾 Сохранить",lambda: save_doc(), True),
        ("Сохранить как", lambda: save_as()),
        None,
        ("📋 Копировать всё", lambda: copy_all()),
        ("Статистика", lambda: show_stats()),
    ])

    text = scrolledtext.ScrolledText(
        body, bg="#0c0e18", fg="#c8d0e0",
        insertbackground="#60a5fa", font=MONO(10),
        relief="flat", bd=0, padx=14, pady=10,
        undo=True, wrap="none",
    )
    text.pack(fill="both", expand=True)
    status_var = tk.StringVar(value="Готово")
    tk.Label(body, textvariable=status_var, font=FONT(8),
             bg=C["win2"], fg=C["tx3"], anchor="w", padx=8).pack(fill="x")

    def load(path):
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            text.delete("1.0", "end")
            text.insert("1.0", content)
            status_var.set(f"Открыт: {path}")
        except Exception as ex:
            messagebox.showerror("Ошибка", str(ex))

    def new_doc():
        if messagebox.askyesno("Новый", "Создать новый документ?"):
            text.delete("1.0", "end"); state["path"] = None; status_var.set("Новый документ")

    def open_doc():
        p = filedialog.askopenfilename(
            filetypes=[("Текст", "*.txt *.md *.py *.js *.json *.html *.css *.xml *.log"), ("Все", "*.*")])
        if p: state["path"] = Path(p); load(p)

    def save_doc():
        if not state["path"]: save_as(); return
        try:
            Path(state["path"]).write_text(text.get("1.0", "end-1c"), encoding="utf-8")
            status_var.set("Сохранено ✅")
        except Exception as ex: messagebox.showerror("Ошибка", str(ex))

    def save_as():
        p = filedialog.asksaveasfilename(defaultextension=".txt")
        if p: state["path"] = Path(p); save_doc()

    def copy_all():
        body.clipboard_clear(); body.clipboard_append(text.get("1.0", "end-1c")); status_var.set("Скопировано ✅")

    def show_stats():
        t = text.get("1.0", "end-1c")
        messagebox.showinfo("Статистика",
                            f"Символов: {len(t)}\nСлов: {len(t.split())}\nСтрок: {t.count(chr(10))+1}")

    if file_path:
        load(file_path)

    body.bind_all("<Control-s>", lambda e: save_doc())
    body.bind_all("<Control-o>", lambda e: open_doc())


# ── КАЛЬКУЛЯТОР ──────────────────────────────────
def build_calculator(body, wm):
    body.configure(bg="#0d0f18")
    state = {"expr": "", "disp": "0", "just_eq": False}

    expr_var = tk.StringVar()
    disp_var = tk.StringVar(value="0")

    disp_f = tk.Frame(body, bg="#080b12"); disp_f.pack(fill="x")
    tk.Label(disp_f, textvariable=expr_var, font=MONO(9),
             bg="#080b12", fg=C["tx3"], anchor="e", padx=14).pack(fill="x", pady=(10, 0))
    tk.Label(disp_f, textvariable=disp_var, font=MONO(30, "bold"),
             bg="#080b12", fg=C["tx"], anchor="e", padx=14).pack(fill="x", pady=(0, 12))

    def press(lbl, kind):
        d = disp_var.get()
        if kind == "clr":
            disp_var.set("0"); state["expr"] = ""; expr_var.set(""); state["just_eq"] = False
        elif kind == "neg":
            try: disp_var.set(str(-float(d)))
            except: pass
        elif kind == "pct":
            try: disp_var.set(str(float(d)/100))
            except: pass
        elif kind == "op":
            m = {"÷": "/", "×": "*", "−": "-", "+": "+"}
            state["expr"] = (d if state["just_eq"] else state["expr"] or d) + m[lbl]
            expr_var.set(state["expr"]); disp_var.set("0"); state["just_eq"] = False
        elif kind == "dot":
            if "." not in d: disp_var.set(d + ".")
        elif kind == "eq":
            if state["expr"]:
                try:
                    result = eval(state["expr"] + disp_var.get())
                    expr_var.set(state["expr"] + disp_var.get() + "=")
                    disp_var.set(str(round(result, 10)).rstrip("0").rstrip(".") or "0")
                    state["expr"] = ""; state["just_eq"] = True
                except: disp_var.set("Ошибка")
        else:
            cur = disp_var.get()
            disp_var.set(lbl if cur == "0" or state["just_eq"] else cur + lbl if len(cur) < 14 else cur)
            state["just_eq"] = False

    BTNS = [
        [("C","clr"), ("%","pct"), ("±","neg"), ("÷","op")],
        [("7","7"),   ("8","8"),   ("9","9"),   ("×","op")],
        [("4","4"),   ("5","5"),   ("6","6"),   ("−","op")],
        [("1","1"),   ("2","2"),   ("3","3"),   ("+","op")],
        [("0","0"),   ("0","0"),   (".","dot"),  ("=","eq")],
    ]
    grid = tk.Frame(body, bg="#0d0f18"); grid.pack(fill="both", expand=True)
    for r, row in enumerate(BTNS):
        for c, (lbl_t, kind) in enumerate(row):
            bg = "#1e3a5f" if kind=="eq" else "#1a1d2e" if kind=="op" else "#141620"
            fg = "#60a5fa" if kind=="op" else "#e57373" if kind in ("clr","neg","pct") else C["tx"]
            b = tk.Button(grid, text=lbl_t, font=MONO(17), bg=bg, fg=fg,
                          relief="flat", cursor="hand2", bd=0,
                          activebackground="#2a2e44", activeforeground="white",
                          command=lambda l=lbl_t, k=kind: press(l, k))
            b.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
    for i in range(5): grid.rowconfigure(i, weight=1)
    for i in range(4): grid.columnconfigure(i, weight=1)


# ── ТЕРМИНАЛ ─────────────────────────────────────
def build_terminal(body, wm):
    body.configure(bg="#060a10")
    state = {"cwd": str(Path.home()), "hist": [], "hidx": -1}

    out = scrolledtext.ScrolledText(
        body, bg="#060a10", fg="#c8f0c0",
        insertbackground="#c8f0c0", font=MONO(10),
        relief="flat", bd=0, padx=10, pady=8,
        state="disabled", wrap="word",
    )
    out.pack(fill="both", expand=True)
    out.tag_config("p",   foreground="#4fc3f7")
    out.tag_config("err", foreground="#ef9a9a")
    out.tag_config("ok",  foreground="#80cbc4")
    out.tag_config("cmd", foreground="#78909c")

    inp_f = tk.Frame(body, bg="#060a10"); inp_f.pack(fill="x", padx=8, pady=(4,8))
    prompt_var = tk.StringVar()

    def upd_prompt():
        short = state["cwd"].replace(str(Path.home()), "~")
        prompt_var.set(f"user@nexos:{short}$ ")

    upd_prompt()
    tk.Label(inp_f, textvariable=prompt_var, font=MONO(10),
             bg="#060a10", fg="#4fc3f7").pack(side="left")
    inp = tk.Entry(inp_f, bg="#060a10", fg="#c8f0c0",
                   insertbackground="#c8f0c0", font=MONO(10), relief="flat", bd=0)
    inp.pack(side="left", fill="x", expand=True, padx=(6, 0))

    def write(text, tag=None):
        out.configure(state="normal")
        out.insert("end", text, tag or "")
        out.see("end")
        out.configure(state="disabled")

    write("NexOS Terminal v3.0\n", "ok")
    write("'help' — список команд | 'run <файл.exe>' — запуск программы\n\n", "ok")

    def run_cmd(e=None):
        cmd = inp.get().strip()
        write(f"{prompt_var.get()}{cmd}\n", "cmd")
        if cmd: state["hist"].insert(0, cmd); state["hidx"] = -1
        inp.delete(0, "end")
        exec_cmd(cmd)

    def hist_up(e):
        state["hidx"] = min(state["hidx"]+1, len(state["hist"])-1)
        if state["hist"]: inp.delete(0,"end"); inp.insert(0, state["hist"][state["hidx"]])

    def hist_down(e):
        state["hidx"] = max(state["hidx"]-1, -1)
        inp.delete(0,"end")
        if state["hidx"] >= 0: inp.insert(0, state["hist"][state["hidx"]])

    inp.bind("<Return>", run_cmd)
    inp.bind("<Up>", hist_up)
    inp.bind("<Down>", hist_down)
    inp.focus_set()

    def exec_cmd(cmd):
        if not cmd: return
        parts = cmd.split(); c = parts[0]
        cwd = Path(state["cwd"])

        if c == "help":
            write(
                "  help               — эта справка\n"
                "  ls / dir           — список файлов\n"
                "  cd <path>          — сменить папку\n"
                "  pwd                — текущий путь\n"
                "  mkdir <name>       — создать папку\n"
                "  rm <file>          — удалить файл\n"
                "  cat <file>         — показать содержимое\n"
                "  clear              — очистить экран\n"
                "  echo <text>        — вывод текста\n"
                "  run <file>         — ЗАПУСТИТЬ ФАЙЛ (.exe, .py, .sh)\n"
                "  open <file>        — открыть системным приложением\n"
                "  python <script>    — запустить Python и вывести результат\n"
                "  calc <expr>        — вычислить выражение\n"
                "  sysinfo            — информация о системе\n"
                "  <любая команда>    — выполнить в shell\n",
                "ok")

        elif c in ("ls", "dir"):
            p = cwd / parts[1] if len(parts) > 1 else cwd
            try:
                items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in items:
                    if not item.name.startswith("."):
                        write(f"  {'📁' if item.is_dir() else '📄'} {item.name}\n")
            except Exception as ex: write(f"ls: {ex}\n", "err")

        elif c == "cd":
            new = (cwd / parts[1]).resolve() if len(parts) > 1 else Path.home()
            if new.is_dir(): state["cwd"] = str(new); upd_prompt()
            else: write(f"cd: нет папки: {parts[1] if len(parts)>1 else ''}\n", "err")

        elif c == "pwd":
            write(state["cwd"] + "\n")

        elif c == "clear":
            out.configure(state="normal"); out.delete("1.0","end"); out.configure(state="disabled")

        elif c == "echo":
            write(" ".join(parts[1:]) + "\n")

        elif c == "mkdir":
            if len(parts) < 2: write("mkdir: нужно имя\n","err"); return
            try: (cwd/parts[1]).mkdir(exist_ok=True); write(f"Создана: {parts[1]}\n","ok")
            except Exception as ex: write(str(ex)+"\n","err")

        elif c == "rm":
            if len(parts) < 2: write("rm: нужен файл\n","err"); return
            p = cwd/parts[1]
            try: p.unlink() if p.is_file() else shutil.rmtree(str(p)); write(f"Удалено: {parts[1]}\n","ok")
            except Exception as ex: write(str(ex)+"\n","err")

        elif c == "cat":
            if len(parts) < 2: write("cat: нужен файл\n","err"); return
            try: write((cwd/parts[1]).read_text(encoding="utf-8",errors="replace")+"\n")
            except Exception as ex: write(str(ex)+"\n","err")

        elif c == "calc":
            try: write(str(eval(" ".join(parts[1:]))) + "\n")
            except: write("Ошибка выражения\n","err")

        elif c == "run":
            if len(parts) < 2: write("run: нужен файл\n","err"); return
            p = cwd/parts[1]
            if not p.exists(): write(f"Файл не найден: {p}\n","err"); return
            ext = p.suffix.lower()
            write(f"▶ Запускаю: {p.name}\n","ok")
            def do():
                try:
                    kw = {"creationflags": subprocess.CREATE_NEW_CONSOLE} if IS_WIN and ext==".exe" else {}
                    args = ["wine", str(p)] if not IS_WIN and ext==".exe" and shutil.which("wine") else \
                           [sys.executable, str(p)] if ext==".py" else \
                           ["bash", str(p)] if ext in (".sh",".bash") else [str(p)]
                    proc = subprocess.Popen(args, cwd=str(cwd), **kw)
                    body.after(0, lambda: write(f"✅ PID {proc.pid}\n","ok"))
                except Exception as ex:
                    body.after(0, lambda: write(f"Ошибка: {ex}\n","err"))
            threading.Thread(target=do, daemon=True).start()

        elif c == "open":
            if len(parts) < 2: return
            p = cwd/parts[1]
            try:
                if IS_WIN:   os.startfile(str(p))
                elif IS_MAC: subprocess.Popen(["open",str(p)])
                else:        subprocess.Popen(["xdg-open",str(p)])
                write(f"Открыто: {p.name}\n","ok")
            except Exception as ex: write(str(ex)+"\n","err")

        elif c == "python":
            if len(parts) < 2: write("python: нужен скрипт\n","err"); return
            def do():
                try:
                    r = subprocess.run([sys.executable, str(cwd/parts[1])],
                                       capture_output=True, text=True, timeout=30)
                    if r.stdout: body.after(0, lambda: write(r.stdout))
                    if r.stderr: body.after(0, lambda: write(r.stderr,"err"))
                except Exception as ex: body.after(0, lambda: write(str(ex)+"\n","err"))
            threading.Thread(target=do, daemon=True).start()

        elif c == "sysinfo":
            write(
                f"  OS:      {platform.system()} {platform.release()}\n"
                f"  Arch:    {platform.machine()}\n"
                f"  Python:  {sys.version.split()[0]}\n"
                f"  Home:    {Path.home()}\n"
                f"  CWD:     {state['cwd']}\n", "ok")

        else:
            # Системная команда
            def do():
                try:
                    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                       timeout=30, cwd=state["cwd"])
                    out_text = (r.stdout or "") + (r.stderr or "")
                    body.after(0, lambda: write(out_text if out_text else "(нет вывода)\n"))
                except subprocess.TimeoutExpired:
                    body.after(0, lambda: write("Таймаут (30с)\n","err"))
                except Exception as ex:
                    body.after(0, lambda: write(str(ex)+"\n","err"))
            threading.Thread(target=do, daemon=True).start()


# ── ПАРАМЕТРЫ ────────────────────────────────────
def build_settings(body, wm):
    lbl(body, "⚙️  Параметры NexOS", 14, C["tx"]).pack(pady=(18,4))
    lbl(body, "Python Edition v3.0", 10, C["tx2"]).pack()
    tk.Frame(body, bg=C["bd"], height=1).pack(fill="x", padx=20, pady=14)

    info = [
        ("ОС",       f"{platform.system()} {platform.release()}"),
        ("Машина",   platform.machine()),
        ("Python",   sys.version.split()[0]),
        ("Браузер",  "tkinterweb ✅" if HAS_WEB else "❌ pip install tkinterweb"),
        ("Домашняя", str(Path.home())),
    ]
    grid = tk.Frame(body, bg=C["win"]); grid.pack(padx=24)
    for i, (k, v) in enumerate(info):
        tk.Label(grid, text=k+":", font=FONT(10,"bold"), bg=C["win"],
                 fg=C["tx2"], anchor="e", width=12).grid(row=i, column=0, sticky="e", pady=6, padx=(0,12))
        tk.Label(grid, text=v, font=MONO(9), bg=C["win"],
                 fg=C["tx"], anchor="w").grid(row=i, column=1, sticky="w", pady=6)

    tk.Frame(body, bg=C["bd"], height=1).pack(fill="x", padx=20, pady=14)
    note = ("💡 Запуск .exe:\n"
            "  • Windows: через Проводник или  run <файл.exe>  в терминале\n"
            "  • Linux/macOS: через Wine (sudo apt install wine)")
    tk.Label(body, text=note, font=FONT(9), bg=C["win"], fg=C["tx3"],
             justify="left", wraplength=480).pack(padx=24, anchor="w")

    if not HAS_WEB:
        tk.Frame(body, bg=C["bd"], height=1).pack(fill="x", padx=20, pady=10)
        btn(body, "📦 Установить tkinterweb (браузер)",
            lambda: subprocess.Popen([sys.executable, "-m", "pip", "install", "tkinterweb"]),
            True).pack(pady=4)


# ── Утилиты для иконок / типов файлов ────────────
def file_icon(p: Path) -> str:
    if p.is_dir(): return "📁"
    m = {".exe":"📦",".msi":"📦",".py":"🐍",".js":"⚙️",".ts":"⚙️",".sh":"🔧",".bat":"🔧",
         ".txt":"📄",".md":"📝",".log":"📋",".json":"📊",".xml":"📊",".csv":"📊",
         ".jpg":"🖼️",".jpeg":"🖼️",".png":"🖼️",".gif":"🖼️",".svg":"🎨",".webp":"🖼️",
         ".mp3":"🎵",".wav":"🎵",".flac":"🎵",".ogg":"🎵",
         ".mp4":"🎬",".mkv":"🎬",".avi":"🎬",".mov":"🎬",
         ".pdf":"📕",".doc":"📘",".docx":"📘",".xls":"📗",".xlsx":"📗",
         ".zip":"🗜️",".rar":"🗜️",".7z":"🗜️",".tar":"🗜️",".gz":"🗜️",
         ".html":"🌐",".css":"🎨",".cpp":"⚙️",".c":"⚙️",".java":"⚙️",".rs":"⚙️"}
    return m.get(p.suffix.lower(), "📄")

def file_type(p: Path) -> str:
    if p.is_dir(): return "Папка"
    types = {".exe":"Приложение",".py":"Python",".txt":"Текст",
             ".jpg":"JPEG",".png":"PNG",".mp3":"MP3",".mp4":"MP4",
             ".pdf":"PDF",".zip":"ZIP",".json":"JSON",".html":"HTML"}
    return types.get(p.suffix.lower(), p.suffix.lstrip(".").upper() or "Файл")

def fmt_size(b: int) -> str:
    if b < 1024:    return f"{b} B"
    if b < 1<<20:   return f"{b/1024:.1f} KB"
    if b < 1<<30:   return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.1f} GB"


# ══════════════════════════════════════════════════
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ══════════════════════════════════════════════════
class NexOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NexOS Desktop v3")
        self.root.geometry("1280x760")
        self.root.configure(bg=C["desk"])
        self.root.minsize(960, 580)
        self._setup_style()

        # Таскбар (создаём первым — внизу)
        self.taskbar = Taskbar(self.root, lambda: self.wm)

        # Рабочий стол (Canvas для размещения окон)
        self.canvas = tk.Canvas(self.root, bg=C["desk"],
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        # Правый клик на рабочем столе
        self.canvas.bind("<Button-3>", self._desk_rclick)

        # Оконный менеджер
        self.wm = WindowManager(self.canvas, self.taskbar)

        # Иконки на рабочем столе
        self._desk_icons()

        # Открыть проводник при старте
        self.root.after(400, lambda: open_app(self.wm, "explorer"))

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=C["win"], foreground=C["tx"],
                        fieldbackground=C["win2"], troughcolor=C["win2"],
                        selectbackground=C["ac"], selectforeground="white",
                        font=FONT(10), borderwidth=0, relief="flat")
        style.configure("Treeview", background=C["win"], foreground=C["tx"],
                        fieldbackground=C["win"], rowheight=24)
        style.configure("Treeview.Heading", background=C["win2"],
                        foreground=C["tx2"], font=FONT(9))
        style.map("Treeview", background=[("selected", C["sel"])])

    def _desk_icons(self):
        ICONS = [
            ("🗑️", "Корзина",    "explorer"),
            ("📁", "Проводник",  "explorer"),
            ("🌐", "Браузер",    "browser"),
            ("📄", "Блокнот",    "notepad"),
            ("🔢", "Калькулятор","calculator"),
            ("💻", "Терминал",   "terminal"),
        ]
        for i, (e, name, app_id) in enumerate(ICONS):
            x, y = 22, 14 + i * 86
            # Рисуем на canvas
            self.canvas.create_text(x+37, y+22, text=e, font=FONT(28), fill=C["tx"], tags=f"ico_{i}")
            self.canvas.create_text(x+37, y+58, text=name, font=FONT(9), fill=C["tx"],
                                    width=72, justify="center", tags=f"ico_{i}")
            # Невидимый прямоугольник для клика
            rect = self.canvas.create_rectangle(x, y, x+74, y+74, fill="", outline="", tags=f"ico_{i}")
            self.canvas.tag_bind(f"ico_{i}", "<Double-Button-1>",
                                 lambda e, a=app_id: open_app(self.wm, a))
            self.canvas.tag_bind(f"ico_{i}", "<Enter>",
                                 lambda e, i=i: self.canvas.itemconfig(f"ico_{i}", fill=C["ac"]))
            self.canvas.tag_bind(f"ico_{i}", "<Leave>",
                                 lambda e, i=i: self.canvas.itemconfig(f"ico_{i}", fill=C["tx"]))

    def _desk_rclick(self, e):
        menu = tk.Menu(self.root, tearoff=0, bg=C["win2"], fg=C["tx"],
                       activebackground=C["ac"], activeforeground="white",
                       relief="flat", bd=0, font=FONT(10))
        menu.add_command(label="📁  Открыть проводник", command=lambda: open_app(self.wm, "explorer"))
        menu.add_command(label="🌐  Браузер",            command=lambda: open_app(self.wm, "browser"))
        menu.add_command(label="📄  Блокнот",            command=lambda: open_app(self.wm, "notepad"))
        menu.add_separator()
        menu.add_command(label="⚙️  Параметры",         command=lambda: open_app(self.wm, "settings"))
        menu.post(e.x_root, e.y_root)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = NexOS()
    app.run()
