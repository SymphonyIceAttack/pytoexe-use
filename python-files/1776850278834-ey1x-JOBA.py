import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk
import tkinter.font as tkFont
import os
import threading
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib import rcParams
    rcParams['font.family'] = 'DejaVu Sans'
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from sklearn.tree import DecisionTreeClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ============================================================
# НАСТРОЙКИ
# ============================================================

API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"

SYSTEM_PROMPT = """Сен — UniBot атты университеттік AI-көмекшісің.
Студенттер мен оқытушыларға стипендия есептеу жүйесін түсінуге көмектесесің.

Есептеу ережелері:
- Қорытынды балл = (семестр балы × 0.6) + (емтихан балы × 0.4)
- Емтихан балы < 25 → Жазғы семестр
- Емтихан балы < 50 → Қайта тапсыру
- Қорытынды < 70 → Стипендиясыз
- Қорытынды 70–89.9 → Кәдімгі стипендия
- Қорытынды ≥ 90 → Жоғарылатылған стипендия

Қысқаша, нақты, қазақ тілінде жауап бер. Мейірімді бол."""

COLORS = {
    "bg_dark":   "#0f1117",
    "bg_card":   "#1a1d2e",
    "bg_input":  "#252836",
    "accent":    "#6c63ff",
    "accent2":   "#00d4aa",
    "danger":    "#ff4757",
    "warning":   "#ffa502",
    "success":   "#2ed573",
    "info":      "#1e90ff",
    "text":      "#e8e8f0",
    "text_dim":  "#8888aa",
    "border":    "#2d2f45",
}

ROW_COLORS = {
    "Жазғы":          {"bg": "#3d1a1a", "fg": "#ff6b6b", "tag": "jazgy"},
    "Қайта тапсыру":  {"bg": "#3d2e10", "fg": "#ffa502", "tag": "qayta"},
    "Стипендиясыз":   {"bg": "#2a1a2e", "fg": "#cc88ff", "tag": "nostipen"},
    "Кәдімгі":        {"bg": "#0f2d1a", "fg": "#2ed573", "tag": "kadimgi"},
    "Жоғарылатылған": {"bg": "#1a1a3d", "fg": "#6c63ff", "tag": "jogarylat"},
}

# ============================================================
# ИНИЦИАЛИЗАЦИЯ ИИ
# ============================================================
ai_available = False
claude_client = None
chat_history = []

if ANTHROPIC_AVAILABLE and API_KEY != "YOUR_ANTHROPIC_API_KEY_HERE":
    try:
        claude_client = anthropic.Anthropic(api_key=API_KEY)
        ai_available = True
    except Exception:
        ai_available = False

# ============================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================
file_path = ""
model = None
df_global = None
possible_features = ['GPA', 'Extracurricular', 'Sports', 'Volunteering']

# ============================================================
# ЛОГИКА РАСЧЁТОВ
# ============================================================

def calculate_verdict(sem_score, exam_score):
    total = (sem_score * 0.6) + (exam_score * 0.4)
    total = round(total, 1)
    if exam_score < 25:
        return total, "ЖАЗҒЫ СЕМЕСТР", COLORS["danger"]
    elif exam_score < 50:
        return total, "ҚАЙТА ТАПСЫРУ", COLORS["warning"]
    elif total < 70:
        return total, "СТИПЕНДИЯСЫЗ", COLORS["danger"]
    elif total >= 89.9:
        return total, "ЖОҒАРЫЛАТЫЛҒАН СТИПЕНДИЯ", COLORS["accent"]
    else:
        return total, "КӘДІМГІ СТИПЕНДИЯ", COLORS["success"]

def get_verdict_label(score):
    s = round(score * 25, 1) if score <= 5 else round(score, 1)
    if s < 25:  return "Жазғы"
    if s < 50:  return "Қайта тапсыру"
    if s < 70:  return "Стипендиясыз"
    if s >= 89.9: return "Жоғарылатылған"
    return "Кәдімгі"

# ============================================================
# ТОСТ-УВЕДОМЛЕНИЯ
# ============================================================

class ToastManager:
    STYLES = {
        "success": {"bg": "#1a3d2a", "fg": "#2ed573", "icon": "✓", "border": "#2ed573"},
        "error":   {"bg": "#3d1a1a", "fg": "#ff4757", "icon": "✕", "border": "#ff4757"},
        "warning": {"bg": "#3d2e10", "fg": "#ffa502", "icon": "⚠", "border": "#ffa502"},
        "info":    {"bg": "#1a2a3d", "fg": "#1e90ff", "icon": "i", "border": "#1e90ff"},
    }
    DURATION  = 3500
    FADE_STEP = 0.05
    FADE_MS   = 30
    OFFSET_Y  = 20
    SPACING   = 10

    def __init__(self, root: tk.Tk):
        self.root   = root
        self._stack = []

    def show(self, message: str, kind: str = "info", duration: int = None):
        self.root.after(0, lambda: self._create(message, kind, duration or self.DURATION))

    def _create(self, message, kind, duration):
        st = self.STYLES.get(kind, self.STYLES["info"])
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.0)
        win.configure(bg=st["border"])
        inner = tk.Frame(win, bg=st["bg"], padx=14, pady=10)
        inner.pack(padx=1, pady=1)
        tk.Label(inner, text=st["icon"], font=("Arial", 13, "bold"),
                 bg=st["bg"], fg=st["fg"], width=2).pack(side="left", padx=(0, 8))
        tk.Label(inner, text=message, font=("Arial", 10),
                 bg=st["bg"], fg="#e8e8f0", justify="left",
                 wraplength=280, anchor="w").pack(side="left", fill="x", expand=True)
        close = tk.Label(inner, text="×", font=("Arial", 14),
                         bg=st["bg"], fg=COLORS["text_dim"], cursor="hand2")
        close.pack(side="right", padx=(8, 0))
        close.bind("<Button-1>", lambda e: self._start_fade(win))
        win.update_idletasks()
        self._stack.append(win)
        self._reposition_all()
        self._fade_in(win, 0.0)
        win.after(duration, lambda: self._start_fade(win))

    def _reposition_all(self):
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()
        y = ry + rh - self.OFFSET_Y
        for win in reversed(self._stack):
            if not win.winfo_exists(): continue
            win.update_idletasks()
            tw = win.winfo_reqwidth()
            th = win.winfo_reqheight()
            x  = rx + rw - tw - 20
            y -= th
            win.geometry(f"+{x}+{y}")
            y -= self.SPACING

    def _fade_in(self, win, alpha):
        if not win.winfo_exists(): return
        alpha = min(alpha + self.FADE_STEP * 2, 0.95)
        win.attributes("-alpha", alpha)
        if alpha < 0.95:
            win.after(self.FADE_MS, lambda: self._fade_in(win, alpha))

    def _start_fade(self, win):
        if win.winfo_exists(): self._fade_out(win, 0.95)

    def _fade_out(self, win, alpha):
        if not win.winfo_exists(): return
        alpha -= self.FADE_STEP
        if alpha <= 0:
            if win in self._stack: self._stack.remove(win)
            win.destroy()
            self._reposition_all()
        else:
            win.attributes("-alpha", alpha)
            win.after(self.FADE_MS, lambda: self._fade_out(win, alpha))


# ============================================================
# ДИАЛОГ РЕДАКТИРОВАНИЯ СТУДЕНТА
# ============================================================

class EditStudentDialog(tk.Toplevel):
    """
    Модальное окно для редактирования данных студента.
    Возвращает обновлённые данные через self.result.
    """
    def __init__(self, parent, row_data: dict, colors: dict):
        super().__init__(parent)
        self.title("✏️  Студентті өзгерту")
        self.geometry("420x360")
        self.configure(bg=colors["bg_dark"])
        self.resizable(False, False)
        self.grab_set()   # модальность

        self.result = None
        self._colors = colors
        self._row = row_data

        font_h = tkFont.Font(family="Arial", size=12, weight="bold")
        font_b = tkFont.Font(family="Arial", size=10)

        # Шапка
        hdr = tk.Frame(self, bg=colors["accent"], height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"✏️  Студентті өзгерту",
                 font=font_h, bg=colors["accent"], fg="white").pack(padx=16, pady=12)

        body = tk.Frame(self, bg=colors["bg_card"])
        body.pack(fill="both", expand=True, padx=16, pady=16)
        body.columnconfigure(1, weight=1)

        def lbl(row, text):
            tk.Label(body, text=text, font=font_b,
                     bg=colors["bg_card"], fg=colors["text"],
                     anchor="w").grid(row=row, column=0, sticky="w", pady=7, padx=(0,12))

        def ent(row, value):
            e = tk.Entry(body, font=font_b, bg=colors["bg_input"],
                         fg=colors["text"], insertbackground=colors["text"],
                         relief="flat", bd=6)
            e.grid(row=row, column=1, sticky="ew", pady=7)
            e.insert(0, str(value))
            return e

        lbl(0, "Аты-жөні:")
        self.e_name = ent(0, row_data.get("name", ""))

        lbl(1, "Семестр балы (0–100):")
        self.e_sem  = ent(1, row_data.get("sem", ""))

        lbl(2, "Емтихан балы (0–100):")
        self.e_exam = ent(2, row_data.get("exam", ""))

        # Живой предпросмотр
        self._prev_frame = tk.Frame(body, bg=colors["bg_input"])
        self._prev_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        self._lbl_prev_score   = tk.Label(self._prev_frame, text="Қорытынды: —",
            font=tkFont.Font(family="Arial", size=13, weight="bold"),
            bg=colors["bg_input"], fg=colors["text_dim"])
        self._lbl_prev_score.pack(pady=(8, 2))

        self._lbl_prev_verdict = tk.Label(self._prev_frame, text="Балдарды енгізіңіз",
            font=font_b, bg=colors["bg_input"], fg=colors["text_dim"])
        self._lbl_prev_verdict.pack(pady=(0, 8))

        for e in (self.e_sem, self.e_exam):
            e.bind("<KeyRelease>", self._update_preview)
        self._update_preview()

        # Кнопки
        btn_row = tk.Frame(self, bg=colors["bg_dark"])
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        tk.Button(btn_row, text="💾  Сақтау", font=font_b,
                  bg=colors["accent"], fg="white", activebackground=colors["accent"],
                  activeforeground="white", bd=0, padx=16, pady=8, cursor="hand2",
                  command=self._save).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(btn_row, text="Болдырмау", font=font_b,
                  bg=colors["bg_input"], fg=colors["text_dim"],
                  activebackground=colors["bg_input"], activeforeground=colors["text"],
                  bd=0, padx=16, pady=8, cursor="hand2",
                  command=self.destroy).pack(side="left")

        # Центрировать относительно родителя
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2 - self.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{px}+{py}")
        self.wait_window()

    def _update_preview(self, event=None):
        try:
            sem  = float(self.e_sem.get().strip())
            exam = float(self.e_exam.get().strip())
            if not (0 <= sem <= 100 and 0 <= exam <= 100):
                raise ValueError
            total, verdict, color = calculate_verdict(sem, exam)
            self._lbl_prev_score.configure(text=f"Қорытынды: {total}", fg=color)
            self._lbl_prev_verdict.configure(text=verdict, fg=color)
        except Exception:
            self._lbl_prev_score.configure(text="Қорытынды: —",
                                           fg=self._colors["text_dim"])
            self._lbl_prev_verdict.configure(text="Балдарды енгізіңіз",
                                             fg=self._colors["text_dim"])

    def _save(self):
        name = self.e_name.get().strip()
        if not name:
            messagebox.showwarning("Қате", "Студент атын енгізіңіз!", parent=self)
            return
        try:
            sem  = float(self.e_sem.get().strip())
            exam = float(self.e_exam.get().strip())
            if not (0 <= sem <= 100 and 0 <= exam <= 100):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Қате", "Балдар 0–100 аралығында болуы керек!", parent=self)
            return

        total, _, _ = calculate_verdict(sem, exam)
        verdict = get_verdict_label(total)
        self.result = {
            **self._row,
            "name":    name,
            "sem":     sem,
            "exam":    exam,
            "total":   total,
            "verdict": verdict,
        }
        self.destroy()


# ============================================================
# ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ============================================================

class UniversityApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎓 AI Университетті басқару жүйесі")
        self.root.geometry("1200x860")
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.resizable(True, True)

        self._sort_col     = None
        self._sort_reverse = False
        self._table_data: list[dict] = []
        self._undo_stack:  list[list] = []   # для отмены удалений

        self._setup_fonts()
        self._setup_treeview_style()
        self._build_ui()
        self.toast = ToastManager(self.root)
        self._show_welcome_message()

    # ----------------------------------------------------------
    # ШРИФТЫ И СТИЛИ
    # ----------------------------------------------------------

    def _setup_fonts(self):
        self.font_title   = tkFont.Font(family="Arial", size=18, weight="bold")
        self.font_header  = tkFont.Font(family="Arial", size=12, weight="bold")
        self.font_body    = tkFont.Font(family="Arial", size=10)
        self.font_small   = tkFont.Font(family="Arial", size=9)
        self.font_large   = tkFont.Font(family="Arial", size=14, weight="bold")
        self.font_mono    = tkFont.Font(family="Courier", size=10)

    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview",
            background=COLORS["bg_input"], foreground=COLORS["text"],
            fieldbackground=COLORS["bg_input"], rowheight=32,
            font=("Arial", 10), borderwidth=0)
        style.configure("Dark.Treeview.Heading",
            background=COLORS["bg_card"], foreground=COLORS["text"],
            font=("Arial", 10, "bold"), relief="flat", borderwidth=0)
        style.map("Dark.Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "white")])
        style.map("Dark.Treeview.Heading",
            background=[("active", COLORS["accent"])],
            foreground=[("active", "white")])

    # ----------------------------------------------------------
    # ПОСТРОЕНИЕ UI
    # ----------------------------------------------------------

    def _build_ui(self):
        self._build_header()

        nb_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        nb_frame.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        style = ttk.Style()
        style.configure("Dark.TNotebook", background=COLORS["bg_dark"], borderwidth=0)
        style.configure("Dark.TNotebook.Tab",
            background=COLORS["bg_card"], foreground=COLORS["text_dim"],
            font=("Arial", 10), padding=[14, 7], borderwidth=0)
        style.map("Dark.TNotebook.Tab",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "white")])

        self.notebook = ttk.Notebook(nb_frame, style="Dark.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        tab_main  = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        tab_table = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        tab_add   = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        tab_stats = tk.Frame(self.notebook, bg=COLORS["bg_dark"])

        self.notebook.add(tab_main,  text="  🏠 Басты бет  ")
        self.notebook.add(tab_table, text="  📋 Студенттер тізімі  ")
        self.notebook.add(tab_add,   text="  ➕ Студент қосу  ")
        self.notebook.add(tab_stats, text="  📊 Статистика  ")

        self._build_main_tab(tab_main)
        self._build_table_tab(tab_table)
        self._build_add_student_tab(tab_add)
        self._build_stats_tab(tab_stats)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=COLORS["accent"], height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎓  AI Университетті басқару жүйесі",
                 font=self.font_title, bg=COLORS["accent"], fg="white"
                 ).pack(side="left", padx=20, pady=10)
        self.lbl_time = tk.Label(hdr, text="", font=self.font_small,
                                  bg=COLORS["accent"], fg="#ddd")
        self.lbl_time.pack(side="right", padx=20)
        self._update_clock()

        status_bar = tk.Frame(self.root, bg=COLORS["bg_card"], height=30)
        status_bar.pack(fill="x")
        status_bar.pack_propagate(False)
        self.lbl_status = tk.Label(status_bar,
            text="⚪  Файл таңдалмады  |  Талдау үшін CSV жүктеңіз",
            font=self.font_small, bg=COLORS["bg_card"], fg=COLORS["text_dim"])
        self.lbl_status.pack(side="left", padx=15, pady=5)
        ai_text  = "🟢 Claude AI белсенді" if ai_available else "🔴 Офлайн режим"
        ai_color = COLORS["success"] if ai_available else COLORS["danger"]
        tk.Label(status_bar, text=ai_text, font=self.font_small,
                 bg=COLORS["bg_card"], fg=ai_color).pack(side="right", padx=15)

    # ---------- Главная вкладка ----------

    def _build_main_tab(self, parent):
        main = tk.Frame(parent, bg=COLORS["bg_dark"])
        main.pack(fill="both", expand=True, padx=10, pady=10)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=COLORS["bg_dark"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = tk.Frame(main, bg=COLORS["bg_dark"])
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._build_file_section(left)
        self._build_calculator_section(left)
        self._build_chat_section(right)

    def _build_file_section(self, parent):
        card = self._make_card(parent, "📁  Деректерді жүктеу")
        self.btn_load = self._make_button(card, "  CSV файлын таңдау",
                                          self.select_file, COLORS["accent"])
        self.btn_load.pack(fill="x", padx=12, pady=(8, 4))
        self.btn_analyze = self._make_button(card, "  Толық тізімді талдау",
                                             self.process_full_dataset,
                                             COLORS["accent2"], state="disabled")
        self.btn_analyze.pack(fill="x", padx=12, pady=(4, 12))

    def _build_calculator_section(self, parent):
        card = self._make_card(parent, "🧮  Жеке есептеу")
        fields = tk.Frame(card, bg=COLORS["bg_card"])
        fields.pack(fill="x", padx=12, pady=8)
        fields.columnconfigure(1, weight=1)

        tk.Label(fields, text="Семестр балы:", font=self.font_body,
                 bg=COLORS["bg_card"], fg=COLORS["text"]).grid(row=0, column=0, sticky="w", pady=4)
        self.entry_semester = self._make_entry(fields)
        self.entry_semester.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)
        self.entry_semester.insert(0, "0–100")
        self.entry_semester.bind("<FocusIn>", lambda e: self._clear_placeholder(e, "0–100"))

        tk.Label(fields, text="Емтихан балы:", font=self.font_body,
                 bg=COLORS["bg_card"], fg=COLORS["text"]).grid(row=1, column=0, sticky="w", pady=4)
        self.entry_session = self._make_entry(fields)
        self.entry_session.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)
        self.entry_session.insert(0, "0–100")
        self.entry_session.bind("<FocusIn>", lambda e: self._clear_placeholder(e, "0–100"))

        self._make_button(card, "  Есептеу", self.predict_manual,
                          COLORS["accent"]).pack(fill="x", padx=12, pady=(0, 8))

        self.result_frame = tk.Frame(card, bg=COLORS["bg_input"])
        self.result_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.lbl_result_score = tk.Label(self.result_frame, text="—",
            font=self.font_large, bg=COLORS["bg_input"], fg=COLORS["text_dim"])
        self.lbl_result_score.pack(pady=(10, 2))
        self.lbl_result_verdict = tk.Label(self.result_frame,
            text="Есептеу үшін балдарды енгізіңіз",
            font=self.font_body, bg=COLORS["bg_input"], fg=COLORS["text_dim"])
        self.lbl_result_verdict.pack(pady=(0, 10))

    # ---------- Вкладка таблицы (ОБНОВЛЕНА) ----------

    def _build_table_tab(self, parent):
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="Барлығы")

        # ---- Панель инструментов ----
        toolbar = tk.Frame(parent, bg=COLORS["bg_card"], height=48)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="🔍", font=self.font_body,
                 bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(side="left", padx=(12, 4))
        self.entry_search = tk.Entry(toolbar, textvariable=self.search_var,
            font=self.font_body, bg=COLORS["bg_input"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=6, width=25)
        self.entry_search.pack(side="left", ipady=4, pady=8)
        self.entry_search.insert(0, "Студент атын іздеу...")
        self.entry_search.bind("<FocusIn>",
            lambda e: self._clear_placeholder(e, "Студент атын іздеу..."))
        self.search_var.trace("w", self._on_search_change)

        tk.Label(toolbar, text="Сүзгі:", font=self.font_small,
                 bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(side="left", padx=(16, 4))
        filter_opts = ["Барлығы", "Жазғы", "Қайта тапсыру",
                       "Стипендиясыз", "Кәдімгі", "Жоғарылатылған"]
        ttk.Combobox(toolbar, textvariable=self.filter_var, values=filter_opts,
                     state="readonly", font=self.font_small, width=18
                     ).pack(side="left", pady=8)
        self.filter_var.trace("w", lambda *a: self._apply_filters())

        self.lbl_count = tk.Label(toolbar, text="Студенттер: 0",
            font=self.font_small, bg=COLORS["bg_card"], fg=COLORS["text_dim"])
        self.lbl_count.pack(side="right", padx=16)

        self._make_button(toolbar, "💾 CSV экспорт", self._export_table,
                          COLORS["accent2"]).pack(side="right", padx=8, pady=8)

        # ---- Панель действий (НОВАЯ) ----
        action_bar = tk.Frame(parent, bg=COLORS["bg_dark"])
        action_bar.pack(fill="x", padx=10, pady=(6, 0))

        # Подсказка
        tk.Label(action_bar,
            text="✏️ Двойной клик — редактировать   |   Del / ПКМ — удалить   |   Ctrl+Z — отменить удаление",
            font=self.font_small, bg=COLORS["bg_dark"], fg=COLORS["text_dim"]
        ).pack(side="left")

        # Кнопка «Отменить удаление»
        self.btn_undo = self._make_button(action_bar, "↩ Болдырмау",
                                          self._undo_delete,
                                          COLORS["bg_input"], state="disabled")
        self.btn_undo.pack(side="right", padx=4)

        # Кнопка «Удалить выбранных»
        self._make_button(action_bar, "🗑 Таңдалғанды өшіру",
                          self._delete_selected_rows,
                          COLORS["danger"]).pack(side="right", padx=4)

        # Кнопка «Редактировать»
        self._make_button(action_bar, "✏️ Өзгерту",
                          self._edit_selected_row,
                          COLORS["accent"]).pack(side="right", padx=4)

        # ---- Легенда ----
        legend_frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        legend_frame.pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(legend_frame, text="Белгілер: ", font=self.font_small,
                 bg=COLORS["bg_dark"], fg=COLORS["text_dim"]).pack(side="left")
        for verdict, clr in ROW_COLORS.items():
            tk.Label(legend_frame, text=f"  {verdict}  ",
                     font=self.font_small, bg=clr["bg"], fg=clr["fg"],
                     padx=6, pady=2).pack(side="left", padx=3)

        # ---- Treeview ----
        table_frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        table_frame.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        columns = ("#", "Аты-жөні", "Семестр балы", "Емтихан балы", "Қорытынды", "Вердикт")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", style="Dark.Treeview",
                                  selectmode="extended")   # multiple select

        col_widths = {"#": 50, "Аты-жөні": 200, "Семестр балы": 130,
                      "Емтихан балы": 130, "Қорытынды": 120, "Вердикт": 200}
        for col in columns:
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort_by_column(c))
            self.tree.column(col, width=col_widths.get(col, 120),
                             anchor="center", stretch=True)
        self.tree.column("Аты-жөні", anchor="w")

        for verdict, clr in ROW_COLORS.items():
            self.tree.tag_configure(clr["tag"],
                background=clr["bg"], foreground=clr["fg"])
        self.tree.tag_configure("odd_default",
            background=COLORS["bg_input"], foreground=COLORS["text"])
        self.tree.tag_configure("even_default",
            background=COLORS["bg_card"], foreground=COLORS["text"])

        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Привязки
        self.tree.bind("<Double-1>",     self._on_double_click)
        self.tree.bind("<Delete>",       lambda e: self._delete_selected_rows())
        self.tree.bind("<Button-3>",     self._show_context_menu)
        self.root.bind("<Control-z>",    lambda e: self._undo_delete())

        # Контекстное меню
        self._ctx_menu = tk.Menu(self.root, tearoff=0,
                                  bg=COLORS["bg_card"], fg=COLORS["text"],
                                  activebackground=COLORS["accent"],
                                  activeforeground="white",
                                  font=self.font_body, bd=0)
        self._ctx_menu.add_command(label="✏️  Өзгерту",       command=self._edit_selected_row)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(label="🗑  Өшіру",          command=self._delete_selected_rows)
        self._ctx_menu.add_command(label="↩  Болдырмау (Ctrl+Z)", command=self._undo_delete)

    # ---------- Вкладка ручного ввода ----------

    def _build_add_student_tab(self, parent):
        pane = tk.Frame(parent, bg=COLORS["bg_dark"])
        pane.pack(fill="both", expand=True, padx=10, pady=10)
        pane.columnconfigure(0, weight=1)
        pane.columnconfigure(1, weight=2)
        pane.rowconfigure(0, weight=1)

        left  = tk.Frame(pane, bg=COLORS["bg_dark"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = tk.Frame(pane, bg=COLORS["bg_dark"])
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Форма
        form_card = self._make_card(left, "✏️  Жаңа студент қосу")
        form = tk.Frame(form_card, bg=COLORS["bg_card"])
        form.pack(fill="x", padx=16, pady=10)
        form.columnconfigure(1, weight=1)

        def field(row, label, placeholder):
            tk.Label(form, text=label, font=self.font_body,
                     bg=COLORS["bg_card"], fg=COLORS["text"],
                     anchor="w").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 12))
            e = self._make_entry(form)
            e.grid(row=row, column=1, sticky="ew", pady=6)
            e.insert(0, placeholder)
            e.bind("<FocusIn>",  lambda ev, ph=placeholder: self._clear_placeholder(ev, ph))
            e.bind("<FocusOut>", lambda ev, ph=placeholder: self._restore_placeholder(ev, ph))
            return e

        self.add_entry_name  = field(0, "Аты-жөні:",    "Мысалы: Айгерім Назарова")
        self.add_entry_group = field(1, "Тобы:",         "Мысалы: ИС-22-1")
        self.add_entry_sem   = field(2, "Семестр балы:", "0 – 100")
        self.add_entry_exam  = field(3, "Емтихан балы:", "0 – 100")

        preview_frame = tk.Frame(form_card, bg=COLORS["bg_input"])
        preview_frame.pack(fill="x", padx=16, pady=(4, 8))
        self.add_lbl_preview_score = tk.Label(preview_frame, text="Қорытынды: —",
            font=self.font_large, bg=COLORS["bg_input"], fg=COLORS["text_dim"])
        self.add_lbl_preview_score.pack(pady=(8, 2))
        self.add_lbl_preview_verdict = tk.Label(preview_frame, text="Балдарды енгізіңіз",
            font=self.font_body, bg=COLORS["bg_input"], fg=COLORS["text_dim"])
        self.add_lbl_preview_verdict.pack(pady=(0, 8))

        for e in (self.add_entry_sem, self.add_entry_exam):
            e.bind("<KeyRelease>", self._update_add_preview)

        btn_row = tk.Frame(form_card, bg=COLORS["bg_card"])
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        self._make_button(btn_row, "➕  Тізімге қосу", self._add_student_to_list,
                          COLORS["accent"]).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._make_button(btn_row, "🗑  Тазарту", self._clear_add_form,
                          COLORS["bg_input"]).pack(side="left")

        tk.Frame(left, height=1, bg=COLORS["border"]).pack(fill="x", pady=6)

        export_card = self._make_card(left, "💾  Экспорт")
        tk.Label(export_card,
            text="Қосылған студенттерді CSV файлына\nсақтап, негізгі тізімге жүктей аласыз.",
            font=self.font_small, bg=COLORS["bg_card"], fg=COLORS["text_dim"],
            justify="left").pack(anchor="w", padx=16, pady=(4, 10))
        exp_btns = tk.Frame(export_card, bg=COLORS["bg_card"])
        exp_btns.pack(fill="x", padx=16, pady=(0, 14))
        self._make_button(exp_btns, "📥  CSV-ге сақтау", self._export_manual_list,
                          COLORS["accent2"]).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._make_button(exp_btns, "📋  Тізімге жіберу", self._send_to_main_table,
                          COLORS["accent"]).pack(side="left", fill="x", expand=True)

        # Правая колонка: мини-список
        list_card = self._make_card(right, "📋  Қосылған студенттер")
        list_card.pack_configure(fill="both", expand=True)

        list_toolbar = tk.Frame(list_card, bg=COLORS["bg_card"])
        list_toolbar.pack(fill="x", padx=12, pady=(4, 0))
        self.add_lbl_count = tk.Label(list_toolbar, text="Жазбалар: 0",
            font=self.font_small, bg=COLORS["bg_card"], fg=COLORS["text_dim"])
        self.add_lbl_count.pack(side="left")
        self._make_button(list_toolbar, "🗑 Барлығын өшіру",
                          self._clear_all_manual, COLORS["danger"]).pack(side="right")

        mini_frame = tk.Frame(list_card, bg=COLORS["bg_dark"])
        mini_frame.pack(fill="both", expand=True, padx=12, pady=(6, 12))

        mini_cols = ("№", "Аты-жөні", "Тобы", "Семестр", "Емтихан", "Қорытынды", "Вердикт")
        self.add_tree = ttk.Treeview(mini_frame, columns=mini_cols,
                                     show="headings", style="Dark.Treeview",
                                     selectmode="browse", height=18)
        mini_widths = {"№": 40, "Аты-жөні": 170, "Тобы": 80,
                       "Семестр": 80, "Емтихан": 80, "Қорытынды": 90, "Вердикт": 160}
        for col in mini_cols:
            self.add_tree.heading(col, text=col)
            self.add_tree.column(col, width=mini_widths.get(col, 90),
                                 anchor="center", stretch=True)
        self.add_tree.column("Аты-жөні", anchor="w")
        for verdict, clr in ROW_COLORS.items():
            self.add_tree.tag_configure(clr["tag"],
                background=clr["bg"], foreground=clr["fg"])

        add_vsb = ttk.Scrollbar(mini_frame, orient="vertical",   command=self.add_tree.yview)
        add_hsb = ttk.Scrollbar(mini_frame, orient="horizontal", command=self.add_tree.xview)
        self.add_tree.configure(yscrollcommand=add_vsb.set, xscrollcommand=add_hsb.set)
        add_vsb.pack(side="right",  fill="y")
        add_hsb.pack(side="bottom", fill="x")
        self.add_tree.pack(fill="both", expand=True)

        self.add_tree.bind("<Button-3>", self._delete_manual_row)
        self.add_tree.bind("<Delete>",   lambda e: self._delete_selected_manual())
        self._manual_data: list[dict] = []

    # ---------- Вкладка статистики ----------

    def _build_stats_tab(self, parent):
        self.stats_card = tk.Frame(parent, bg=COLORS["bg_dark"])
        self.stats_card.pack(fill="both", expand=True, padx=10, pady=10)
        if MATPLOTLIB_AVAILABLE:
            self.lbl_no_data = tk.Label(self.stats_card,
                text="Графиктерді көру үшін\nCSV жүктеңіз",
                font=self.font_body, bg=COLORS["bg_dark"],
                fg=COLORS["text_dim"], justify="center")
            self.lbl_no_data.pack(pady=60)
        else:
            tk.Label(self.stats_card,
                text="Графиктер үшін matplotlib орнатыңыз:\npip install matplotlib",
                font=self.font_mono, bg=COLORS["bg_dark"],
                fg=COLORS["warning"], justify="center").pack(pady=60)

    def _build_chart(self, verdict_counts):
        if not MATPLOTLIB_AVAILABLE: return
        for w in self.stats_card.winfo_children(): w.destroy()
        colors_pie = {
            "Жазғы":         COLORS["danger"],
            "Қайта тапсыру": COLORS["warning"],
            "Стипендиясыз":  "#ff6b81",
            "Кәдімгі":       COLORS["success"],
            "Жоғарылатылған": COLORS["accent"],
        }
        fig, axes = plt.subplots(1, 2, figsize=(9, 4))
        fig.patch.set_facecolor(COLORS["bg_dark"])
        labels = list(verdict_counts.keys())
        values = list(verdict_counts.values())
        pie_colors = [colors_pie.get(l, "#aaa") for l in labels]
        wedges, texts, autotexts = axes[0].pie(
            values, labels=None, autopct='%1.0f%%', colors=pie_colors,
            startangle=90, wedgeprops=dict(edgecolor=COLORS["bg_dark"], linewidth=2),
            pctdistance=0.75)
        for at in autotexts: at.set_color("white"); at.set_fontsize(9)
        axes[0].set_facecolor(COLORS["bg_dark"])
        axes[0].set_title("Бөлу", color=COLORS["text"], fontsize=11, pad=8)
        patches = [mpatches.Patch(color=pie_colors[i],
                                   label=f"{labels[i]} ({values[i]})")
                   for i in range(len(labels))]
        axes[0].legend(handles=patches, loc='lower center',
                       bbox_to_anchor=(0.5, -0.3), fontsize=8,
                       frameon=False, labelcolor=COLORS["text"], ncol=2)
        bars = axes[1].bar(range(len(labels)), values, color=pie_colors,
                           edgecolor=COLORS["bg_dark"], linewidth=1)
        axes[1].set_facecolor(COLORS["bg_input"])
        axes[1].set_xticks(range(len(labels)))
        axes[1].set_xticklabels([l[:9] for l in labels], rotation=25,
                                  ha="right", fontsize=8, color=COLORS["text_dim"])
        axes[1].tick_params(axis='y', colors=COLORS["text_dim"], labelsize=8)
        axes[1].spines[:].set_color(COLORS["border"])
        axes[1].set_title("Саны", color=COLORS["text"], fontsize=11, pad=8)
        for bar, val in zip(bars, values):
            axes[1].text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + 0.15, str(val),
                         ha='center', va='bottom', fontsize=9, color=COLORS["text"])
        fig.tight_layout(pad=2)
        canvas = FigureCanvasTkAgg(fig, master=self.stats_card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def _build_chat_section(self, parent):
        card = self._make_card(parent, "🤖  UniBot AI-мен чат")
        card.pack_configure(expand=True, fill="both")

        msg_frame = tk.Frame(card, bg=COLORS["bg_input"])
        msg_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self.chat_text = tk.Text(msg_frame, state=tk.DISABLED, wrap=tk.WORD,
            font=self.font_body, bg=COLORS["bg_input"], fg=COLORS["text"],
            bd=0, relief="flat", padx=10, pady=10, cursor="arrow")
        scrollbar = tk.Scrollbar(msg_frame, bg=COLORS["bg_input"])
        scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.chat_text.yview)

        self.chat_text.tag_configure("user_bubble", background=COLORS["accent"],
            foreground="white", font=self.font_body, spacing1=4, spacing3=4,
            lmargin1=80, lmargin2=80, rmargin=10)
        self.chat_text.tag_configure("ai_bubble", background=COLORS["bg_card"],
            foreground=COLORS["text"], font=self.font_body, spacing1=4, spacing3=4,
            lmargin1=10, lmargin2=10, rmargin=80)
        self.chat_text.tag_configure("label_user", foreground=COLORS["accent"],
            font=self.font_small, justify="right")
        self.chat_text.tag_configure("label_ai",   foreground=COLORS["accent2"],
            font=self.font_small)
        self.chat_text.tag_configure("typing",     foreground=COLORS["text_dim"],
            font=self.font_small, lmargin1=10)

        input_frame = tk.Frame(card, bg=COLORS["bg_card"])
        input_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.entry_chat = tk.Entry(input_frame, font=self.font_body,
            bg=COLORS["bg_input"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=8)
        self.entry_chat.pack(side="left", fill="x", expand=True, ipady=6)
        self.entry_chat.bind("<Return>", lambda e: self.send_message())
        self.entry_chat.insert(0, "UniBot-қа сұрақ қойыңыз...")
        self.entry_chat.bind("<FocusIn>",
            lambda e: self._clear_placeholder(e, "UniBot-қа сұрақ қойыңыз..."))
        self._make_button(input_frame, "Жіберу ➤", self.send_message,
                          COLORS["accent"], width=10).pack(side="right", padx=(8, 0))

        quick_frame = tk.Frame(card, bg=COLORS["bg_card"])
        quick_frame.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(quick_frame, text="Жылдам сұрақтар:", font=self.font_small,
                 bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(side="left", padx=(0, 8))
        for q_text in ["Стипендия қалай есептеледі?",
                        "Жазғы семестр дегеніміз не?",
                        "Стипендияны қалай көтеруге болады?"]:
            tk.Button(quick_frame, text=q_text, font=self.font_small,
                bg=COLORS["bg_input"], fg=COLORS["text_dim"],
                activebackground=COLORS["accent"], activeforeground="white",
                bd=0, padx=6, pady=3, cursor="hand2",
                command=lambda t=q_text: self._quick_question(t)
            ).pack(side="left", padx=3)

    # ----------------------------------------------------------
    # ВСПОМОГАТЕЛЬНЫЕ UI МЕТОДЫ
    # ----------------------------------------------------------

    def _make_card(self, parent, title):
        outer = tk.Frame(parent, bg=COLORS["border"], bd=1)
        outer.pack(fill="x", pady=(0, 10))
        card = tk.Frame(outer, bg=COLORS["bg_card"])
        card.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(card, text=title, font=self.font_header,
                 bg=COLORS["bg_card"], fg=COLORS["text"]).pack(anchor="w", padx=12, pady=(10, 5))
        tk.Frame(card, height=1, bg=COLORS["border"]).pack(fill="x", padx=12)
        return card

    def _make_button(self, parent, text, command, color, state="normal", width=None):
        kw = dict(text=text, command=command, font=self.font_body,
                  bg=color, fg="white", activebackground=color, activeforeground="white",
                  bd=0, padx=14, pady=8, cursor="hand2", state=state, relief="flat")
        if width: kw["width"] = width
        return tk.Button(parent, **kw)

    def _make_entry(self, parent):
        return tk.Entry(parent, font=self.font_body, bg=COLORS["bg_input"],
                        fg=COLORS["text"], insertbackground=COLORS["text"],
                        relief="flat", bd=6)

    def _clear_placeholder(self, event, placeholder):
        if event.widget.get() == placeholder:
            event.widget.delete(0, tk.END)
            event.widget.configure(fg=COLORS["text"])

    def _restore_placeholder(self, event, placeholder):
        if event.widget.get().strip() == "":
            event.widget.delete(0, tk.END)
            event.widget.insert(0, placeholder)
            event.widget.configure(fg=COLORS["text_dim"])

    def _update_clock(self):
        now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
        self.lbl_time.configure(text=now)
        self.root.after(1000, self._update_clock)

    # ----------------------------------------------------------
    # ТАБЛИЦА: заполнение, поиск, сортировка
    # ----------------------------------------------------------

    def _populate_table(self, df, name_col, score_col):
        self._table_data = []
        for i, row in df.iterrows():
            name    = str(row.get(name_col, f"Студент {i+1}"))
            score   = row[score_col]
            verdict = get_verdict_label(score)
            sem     = round(float(score), 1)
            exam    = round(float(score), 1)
            total   = round(float(score), 1)
            self._table_data.append({
                "name": name, "sem": sem, "exam": exam,
                "total": total, "verdict": verdict,
            })
        self._apply_filters()

    def _apply_filters(self):
        search_text     = self.search_var.get().strip().lower()
        if search_text == "студент атын іздеу...": search_text = ""
        filter_verdict  = self.filter_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        count = 0
        for i, row in enumerate(self._table_data):
            if search_text and search_text not in row["name"].lower(): continue
            if filter_verdict != "Барлығы" and row["verdict"] != filter_verdict: continue
            count += 1
            tag = ROW_COLORS.get(row["verdict"], {}).get("tag", "odd_default")
            self.tree.insert("", "end", iid=str(i), tags=(tag,),
                values=(count, row["name"], row["sem"], row["exam"],
                        row["total"], row["verdict"]))

        self.lbl_count.configure(text=f"Студенттер: {count}")
        self.notebook.select(1)

    def _on_search_change(self, *args):
        self._apply_filters()

    def _sort_by_column(self, col):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col     = col
            self._sort_reverse = False

        col_map = {
            "#": None, "Аты-жөні": "name", "Семестр балы": "sem",
            "Емтихан балы": "exam", "Қорытынды": "total", "Вердикт": "verdict",
        }
        key = col_map.get(col)
        if not key: return
        self._table_data.sort(key=lambda r: r[key], reverse=self._sort_reverse)
        self._apply_filters()
        for c in self.tree["columns"]:
            label = f"{c} {'↑' if not self._sort_reverse else '↓'}" if c == col else c
            self.tree.heading(c, text=label)

    # ----------------------------------------------------------
    # ✏️  РЕДАКТИРОВАНИЕ (НОВОЕ)
    # ----------------------------------------------------------

    def _on_double_click(self, event):
        """Двойной клик по строке → открыть диалог редактирования."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        self._edit_selected_row()

    def _edit_selected_row(self):
        """Открыть диалог редактирования для выбранной строки."""
        selected = self.tree.selection()
        if not selected:
            self.toast.show("Алдымен студентті таңдаңыз", kind="warning")
            return
        if len(selected) > 1:
            self.toast.show("Өзгерту үшін бір студентті таңдаңыз", kind="warning")
            return

        iid      = selected[0]
        orig_idx = int(iid)
        row_data = self._table_data[orig_idx]

        # Открываем диалог (блокирующий)
        dlg = EditStudentDialog(self.root, row_data, COLORS)
        if dlg.result is None:
            return   # пользователь нажал «Отмена»

        # Сохраняем изменения
        old_name    = self._table_data[orig_idx]["name"]
        old_verdict = self._table_data[orig_idx]["verdict"]
        self._table_data[orig_idx] = dlg.result
        new_verdict = dlg.result["verdict"]

        self._apply_filters()

        # Обновить статистику
        self._refresh_stats()

        changed = []
        if old_name != dlg.result["name"]:
            changed.append("аты")
        if dlg.result["sem"] != row_data["sem"]:
            changed.append(f"семестр→{dlg.result['sem']}")
        if dlg.result["exam"] != row_data["exam"]:
            changed.append(f"емтихан→{dlg.result['exam']}")
        if old_verdict != new_verdict:
            changed.append(f"вердикт: {new_verdict}")

        self.toast.show(
            f"✓ {dlg.result['name']} жаңартылды"
            + (f" ({', '.join(changed)})" if changed else ""),
            kind="success"
        )

    # ----------------------------------------------------------
    # 🗑  УДАЛЕНИЕ (НОВОЕ)
    # ----------------------------------------------------------

    def _delete_selected_rows(self):
        """Удалить все выбранные строки с подтверждением."""
        selected = self.tree.selection()
        if not selected:
            self.toast.show("Алдымен студентті таңдаңыз", kind="warning")
            return

        # Собрать индексы (iid = строковый индекс в _table_data)
        indices = sorted([int(iid) for iid in selected], reverse=True)
        count   = len(indices)

        if count == 1:
            name = self._table_data[indices[0]]["name"]
            msg  = f"«{name}» студентін тізімнен өшіру?"
        else:
            msg = f"{count} студентті өшіру?"

        if not messagebox.askyesno("Растау", msg,
                                   icon="warning", parent=self.root):
            return

        # Сохраняем снимок для undo
        snapshot = [dict(r) for r in self._table_data]
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > 10:
            self._undo_stack.pop(0)
        self.btn_undo.configure(state="normal")

        # Удаляем (с конца, чтобы не сбивать индексы)
        deleted_names = []
        for idx in indices:
            deleted_names.append(self._table_data[idx]["name"])
            del self._table_data[idx]

        self._apply_filters()
        self._refresh_stats()

        if count == 1:
            self.toast.show(f"🗑 «{deleted_names[0]}» өшірілді  |  Ctrl+Z — болдырмау",
                            kind="info", duration=5000)
        else:
            self.toast.show(f"🗑 {count} студент өшірілді  |  Ctrl+Z — болдырмау",
                            kind="info", duration=5000)

    def _undo_delete(self):
        """Отменить последнее удаление."""
        if not self._undo_stack:
            self.toast.show("Болдырмайтын ештеңе жоқ", kind="warning")
            return
        self._table_data = self._undo_stack.pop()
        if not self._undo_stack:
            self.btn_undo.configure(state="disabled")
        self._apply_filters()
        self._refresh_stats()
        self.toast.show("↩ Өшіру болдырылмады", kind="success")

    def _show_context_menu(self, event):
        """Контекстное меню по правому клику."""
        row = self.tree.identify_row(event.y)
        if row:
            # Если строка не выбрана — выбрать её
            if row not in self.tree.selection():
                self.tree.selection_set(row)
            try:
                self._ctx_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._ctx_menu.grab_release()

    def _refresh_stats(self):
        """Обновить диаграмму статистики после изменения данных."""
        if not self._table_data: return
        counts = {}
        for row in self._table_data:
            v = row["verdict"]
            counts[v] = counts.get(v, 0) + 1
        self._build_chart(counts)

    # ----------------------------------------------------------
    # ДЕТАЛИ СТУДЕНТА (двойной клик — теперь через редактирование)
    # ----------------------------------------------------------

    # Убираем старый метод _show_student_details и заменяем редактированием

    # ----------------------------------------------------------
    # ФОРМА РУЧНОГО ВВОДА
    # ----------------------------------------------------------

    def _update_add_preview(self, event=None):
        try:
            sem_raw  = self.add_entry_sem.get().strip()
            exam_raw = self.add_entry_exam.get().strip()
            if sem_raw in ("", "0 – 100") or exam_raw in ("", "0 – 100"): raise ValueError
            sem  = float(sem_raw)
            exam = float(exam_raw)
            if not (0 <= sem <= 100 and 0 <= exam <= 100): raise ValueError
            total, verdict, color = calculate_verdict(sem, exam)
            self.add_lbl_preview_score.configure(text=f"Қорытынды: {total}", fg=color)
            self.add_lbl_preview_verdict.configure(text=verdict, fg=color)
        except Exception:
            self.add_lbl_preview_score.configure(text="Қорытынды: —", fg=COLORS["text_dim"])
            self.add_lbl_preview_verdict.configure(text="Балдарды енгізіңіз", fg=COLORS["text_dim"])

    def _add_student_to_list(self):
        name  = self.add_entry_name.get().strip()
        group = self.add_entry_group.get().strip()
        if name in {"Мысалы: Айгерім Назарова", ""}:
            self.toast.show("Студент атын енгізіңіз!", kind="warning")
            self.add_entry_name.focus_set()
            return
        if group in {"Мысалы: ИС-22-1", ""}: group = "—"
        try:
            sem_raw  = self.add_entry_sem.get().strip()
            exam_raw = self.add_entry_exam.get().strip()
            if sem_raw in ("", "0 – 100") or exam_raw in ("", "0 – 100"):
                raise ValueError("empty")
            sem  = float(sem_raw)
            exam = float(exam_raw)
            if not (0 <= sem <= 100 and 0 <= exam <= 100): raise ValueError("range")
        except ValueError as e:
            if "range" in str(e):
                self.toast.show("Балдар 0–100 аралығында болуы керек!", kind="error")
            else:
                self.toast.show("Семестр және емтихан балдарын енгізіңіз!", kind="warning")
            return

        total, verdict_full, color = calculate_verdict(sem, exam)
        verdict_short = get_verdict_label(total)
        record = {"name": name, "group": group, "sem": sem, "exam": exam,
                  "total": total, "verdict": verdict_short}
        self._manual_data.append(record)
        self._refresh_manual_tree()
        self.toast.show(f"✓  {name} тізімге қосылды — {verdict_full}", kind="success")
        self._clear_add_form(keep_group=True)

    def _refresh_manual_tree(self):
        for item in self.add_tree.get_children(): self.add_tree.delete(item)
        for i, rec in enumerate(self._manual_data):
            tag = ROW_COLORS.get(rec["verdict"], {}).get("tag", "odd_default")
            self.add_tree.insert("", "end", iid=str(i), tags=(tag,),
                values=(i + 1, rec["name"], rec["group"],
                        rec["sem"], rec["exam"], rec["total"], rec["verdict"]))
        self.add_lbl_count.configure(text=f"Жазбалар: {len(self._manual_data)}")

    def _clear_add_form(self, keep_group=False):
        for entry, ph in [
            (self.add_entry_name, "Мысалы: Айгерім Назарова"),
            (self.add_entry_sem,  "0 – 100"),
            (self.add_entry_exam, "0 – 100"),
        ]:
            entry.delete(0, tk.END); entry.insert(0, ph)
            entry.configure(fg=COLORS["text_dim"])
        if not keep_group:
            self.add_entry_group.delete(0, tk.END)
            self.add_entry_group.insert(0, "Мысалы: ИС-22-1")
            self.add_entry_group.configure(fg=COLORS["text_dim"])
        self.add_lbl_preview_score.configure(text="Қорытынды: —", fg=COLORS["text_dim"])
        self.add_lbl_preview_verdict.configure(text="Балдарды енгізіңіз", fg=COLORS["text_dim"])
        self.add_entry_name.focus_set()

    def _delete_manual_row(self, event):
        item = self.add_tree.identify_row(event.y)
        if item:
            self.add_tree.selection_set(item)
            self._delete_selected_manual()

    def _delete_selected_manual(self):
        selected = self.add_tree.selection()
        if not selected: return
        idx  = int(selected[0])
        name = self._manual_data[idx]["name"]
        del self._manual_data[idx]
        self._refresh_manual_tree()
        self.toast.show(f"{name} тізімнен өшірілді", kind="info")

    def _clear_all_manual(self):
        if not self._manual_data:
            self.toast.show("Тізім қазірдің өзінде бос", kind="warning"); return
        count = len(self._manual_data)
        self._manual_data.clear()
        self._refresh_manual_tree()
        self.toast.show(f"{count} жазба өшірілді", kind="info")

    def _export_manual_list(self):
        if not self._manual_data:
            self.toast.show("Алдымен студенттерді қосыңыз!", kind="warning"); return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile="manual_students.csv")
        if not path: return
        rows = [{"Аты-жөні": r["name"], "Тобы": r["group"],
                 "Семестр балы": r["sem"], "Емтихан балы": r["exam"],
                 "Қорытынды": r["total"], "Вердикт": r["verdict"]}
                for r in self._manual_data]
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
        self.toast.show(f"Сақталды: {os.path.basename(path)}", kind="success")

    def _send_to_main_table(self):
        if not self._manual_data:
            self.toast.show("Алдымен студенттерді қосыңыз!", kind="warning"); return
        added = 0
        for rec in self._manual_data:
            if not any(r["name"] == rec["name"] for r in self._table_data):
                self._table_data.append(rec); added += 1
        self._apply_filters()
        if added:
            self.toast.show(f"{added} студент негізгі тізімге қосылды!", kind="success", duration=4000)
        else:
            self.toast.show("Бұл студенттер тізімде бар", kind="warning")

    # ----------------------------------------------------------
    # ЭКСПОРТ ТАБЛИЦЫ
    # ----------------------------------------------------------

    def _export_table(self):
        if not self._table_data:
            self.toast.show("Экспорт үшін алдымен CSV жүктеңіз!", kind="warning"); return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile="students_export.csv")
        if not path: return
        rows = [{"Аты-жөні": r["name"], "Семестр балы": r["sem"],
                 "Емтихан балы": r["exam"], "Қорытынды": r["total"],
                 "Вердикт": r["verdict"]} for r in self._table_data]
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
        self.toast.show(f"Файл сақталды: {os.path.basename(path)}", kind="success")

    # ----------------------------------------------------------
    # ЗАГРУЗКА ФАЙЛА И АНАЛИЗ
    # ----------------------------------------------------------

    def select_file(self):
        global file_path, model, df_global
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path: return
        try:
            df = pd.read_csv(path)
            file_path = path; df_global = df
            existing_features = [c for c in possible_features if c in df.columns]

            if SKLEARN_AVAILABLE and existing_features and 'GradeClass' in df.columns:
                model = DecisionTreeClassifier(criterion='entropy', max_depth=5)
                model.fit(df[existing_features], df['GradeClass'])
                mode_text = "ML моделі оқытылды"
            else:
                model = None; mode_text = "Формулалар режимі"

            name = os.path.basename(path)
            rows = len(df)
            self.lbl_status.configure(
                text=f"✅  {name}  |  {rows} жазба  |  {mode_text}",
                fg=COLORS["success"])
            self.btn_analyze.configure(state="normal")

            score_col = next((c for c in df.columns if any(
                t in c.upper() for t in ['GPA', 'GRADE', 'SCORE', 'БАЛЛ', 'ИТОГ'])), None)
            name_col  = next((c for c in df.columns if any(
                t in c.upper() for t in ['NAME', 'ФИО', 'STUDENT', 'ИМЯ'])), None)

            if score_col:
                df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
                df = df.dropna(subset=[score_col])
                df['_verdict'] = df[score_col].apply(get_verdict_label)
                counts = df['_verdict'].value_counts().to_dict()
                self._build_chart(counts)
                effective_name_col = name_col if name_col else df.columns[0]
                self._populate_table(df, effective_name_col, score_col)
                self._undo_stack.clear()
                self.btn_undo.configure(state="disabled")

        except Exception as e:
            self.toast.show(f"Файлды жүктеу мүмкін болмады: {e}", kind="error")

    def predict_manual(self):
        try:
            sem  = self.entry_semester.get().strip()
            sess = self.entry_session.get().strip()
            if sem in ("", "0–100") or sess in ("", "0–100"): raise ValueError("empty")
            sem  = float(sem); sess = float(sess)
            if not (0 <= sem <= 100 and 0 <= sess <= 100): raise ValueError("range")
            total, verdict, color = calculate_verdict(sem, sess)
            self.lbl_result_score.configure(text=f"Қорытынды балл: {total}", fg=color)
            emoji_map = {
                "ЖАЗҒЫ СЕМЕСТР": "🛑", "ҚАЙТА ТАПСЫРУ": "⚠️",
                "СТИПЕНДИЯСЫЗ": "❌", "КӘДІМГІ СТИПЕНДИЯ": "✅",
                "ЖОҒАРЫЛАТЫЛҒАН СТИПЕНДИЯ": "🌟",
            }
            self.lbl_result_verdict.configure(
                text=f"{emoji_map.get(verdict, '')}  {verdict}",
                fg=color, font=self.font_header)
        except ValueError as e:
            if "empty" in str(e):
                self.toast.show("Екі балды да енгізіңіз", kind="warning")
            elif "range" in str(e):
                self.toast.show("Балдар 0-ден 100-ге дейін болуы керек", kind="error")
            else:
                self.toast.show("Сандарды енгізіңіз (мысалы: 75 және 80)", kind="error")

    def process_full_dataset(self):
        global file_path
        if not file_path:
            self.toast.show("Алдымен файлды таңдаңыз!", kind="warning"); return
        try:
            df = pd.read_csv(file_path)
            score_col = next((c for c in df.columns if any(
                t in c.upper() for t in ['GPA', 'GRADE', 'SCORE', 'БАЛЛ', 'ИТОГ'])), None)
            if not score_col:
                score_col = simpledialog.askstring("Баптау",
                    "Балдары бар бағанның атауын енгізіңіз:")
            name_col = next((c for c in df.columns if any(
                t in c.upper() for t in ['NAME', 'ФИО', 'STUDENT', 'ИМЯ'])), None)
            if not name_col:
                name_col = simpledialog.askstring("Баптау",
                    "Есімдері бар бағанның атауын енгізіңіз:")
            if not score_col or not name_col: return

            df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
            df = df.dropna(subset=[score_col])
            df['Scholarship_Verdict'] = df[score_col].apply(get_verdict_label)

            out_path = file_path.replace(".csv", "_analysis.csv")
            df.to_csv(out_path, index=False)

            stats   = df['Scholarship_Verdict'].value_counts()
            total   = len(df)
            max_v   = df[score_col].max()
            min_v   = df[score_col].min()
            avg_v   = round(df[score_col].mean(), 1)
            best    = df[df[score_col] == max_v][name_col].astype(str).tolist()
            worst   = df[df[score_col] == min_v][name_col].astype(str).tolist()

            self._build_chart(stats.to_dict())
            self._populate_table(df, name_col, score_col)
            self._undo_stack.clear()
            self.btn_undo.configure(state="disabled")

            self.toast.show(
                f"Талдау аяқталды! {total} студент | Орташа балл: {avg_v}",
                kind="success", duration=5000)
            self.root.after(400, lambda: self.toast.show(
                f"Сақталды: {os.path.basename(out_path)}", kind="info"))

        except Exception as e:
            self.toast.show(f"Өңдеу қатесі: {e}", kind="error")

    # ----------------------------------------------------------
    # ЧАТ
    # ----------------------------------------------------------

    def send_message(self):
        user_text = self.entry_chat.get().strip()
        if not user_text or user_text == "UniBot-қа сұрақ қойыңыз...": return
        self.entry_chat.delete(0, tk.END)
        self._append_chat_message("user", user_text)
        self._show_typing()
        threading.Thread(target=self._get_ai_response,
                         args=(user_text,), daemon=True).start()

    def _get_ai_response(self, user_text):
        global chat_history, claude_client, ai_available
        try:
            if ai_available and claude_client:
                chat_history.append({"role": "user", "content": user_text})
                response = claude_client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=chat_history,
                )
                reply = response.content[0].text
                chat_history.append({"role": "assistant", "content": reply})
                if len(chat_history) > 20: chat_history = chat_history[-20:]
            else:
                reply = self._offline_response(user_text)
        except Exception:
            reply = self._offline_response(user_text)
        self.root.after(0, self._remove_typing)
        self.root.after(100, lambda: self._append_chat_message("ai", reply))

    def _offline_response(self, text):
        t = text.lower()
        if any(w in t for w in ['стипенд', 'есептеу', 'формул']):
            return ("Стипендия мына формула бойынша есептеледі:\n"
                    "Қорытынды = (Семестр × 0.6) + (Емтихан × 0.4)\n\n"
                    "• ≥ 90 → Жоғарылатылған стипендия 🌟\n"
                    "• 70–89.9 → Кәдімгі стипендия ✅\n"
                    "• < 70 → Стипендиясыз ❌")
        elif any(w in t for w in ['жазғ', 'қайта тапсыру']):
            return ("Жазғы семестр емтихан балы < 25 болған жағдайда тағайындалады.\n"
                    "Қайта тапсыру — емтихан балы 25–49 болса.")
        elif any(w in t for w in ['көтеру', 'жоғарылат']):
            return ("Жоғарылатылған стипендия үшін қорытынды балл ≥ 90 болуы керек.\n"
                    "Мысалы: семестр 95, емтихан 85 → қорытынды = 91 ✅")
        else:
            return ("Мен UniBot — стипендия бойынша көмекшімін. Менен сұраңыз:\n"
                    "• Стипендия қалай есептеледі?\n"
                    "• Жазғы семестр дегеніміз не?\n"
                    "• Стипендияны қалай көтеруге болады?\n\n"
                    "(Қазір офлайн-режимде жұмыс істеп тұрмын)")

    def _append_chat_message(self, role, text):
        self.chat_text.configure(state=tk.NORMAL)
        if role == "user":
            self.chat_text.insert(tk.END, "  Сіз\n", "label_user")
            self.chat_text.insert(tk.END, f"  {text}  \n\n", "user_bubble")
        else:
            self.chat_text.insert(tk.END, "🤖 UniBot\n", "label_ai")
            self.chat_text.insert(tk.END, f"  {text}  \n\n", "ai_bubble")
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.yview(tk.END)

    def _show_typing(self):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, "⏳ UniBot теріп жатыр...\n", "typing")
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.yview(tk.END)

    def _remove_typing(self):
        self.chat_text.configure(state=tk.NORMAL)
        content = self.chat_text.get("1.0", tk.END)
        if "⏳ UniBot теріп жатыр..." in content:
            idx  = content.rfind("⏳ UniBot теріп жатыр...")
            line = content[:idx].count('\n') + 1
            self.chat_text.delete(f"{line}.0", f"{line}.end+1c")
        self.chat_text.configure(state=tk.DISABLED)

    def _quick_question(self, text):
        self.entry_chat.delete(0, tk.END)
        self.entry_chat.insert(0, text)
        self.send_message()

    def _show_welcome_message(self):
        welcome = ("Сәлем! Мен UniBot — сіздің AI-көмекшіңіз 🎓\n\n"
                   "Мен сізге көмектесемін:\n"
                   "• Студенттің стипендиясын есептеу\n"
                   "• CSV деректерін талдау\n"
                   "• Студенттер тізімін кестеде көру\n"
                   "• Балдар туралы сұрақтарға жауап беру\n\n"
                   "✏️ Студентті өзгерту: екі рет шертіңіз\n"
                   "🗑 Өшіру: Del немесе тінтуірдің оң жақ түймесі\n"
                   "↩ Болдырмау: Ctrl+Z\n\n"
                   "CSV файлын жүктеңіз немесе сол жақтағы\n"
                   "жеке калькуляторды қолданыңыз!")
        self._append_chat_message("ai", welcome)

    def run(self):
        self.root.mainloop()


# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    app = UniversityApp()
    app.run()