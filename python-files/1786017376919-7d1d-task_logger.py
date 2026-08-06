#!/usr/bin/env python3
"""
Task Logger v1.8 — Учёт задач с надёжной подсветкой дней.
tkcalendar заменён на кастомный Tkinter-календарь для 100% кроссплатформенности.
"""

import json
import os
import sys
import calendar as cal_mod
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

try:
    import pyperclip
except ImportError:
    print("Ошибка: pip3 install pyperclip")
    sys.exit(1)

# ─── Конфигурация ────────────────────────────────────────────────
VERSION = "1.8"
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "task_logger.json")
CLEANUP_DAYS = 90
MAX_RECENT_TASKS = 10

COLOR_YELLOW = "#fff3cd"  # 1-7 часов
COLOR_GREEN  = "#d4edda"  # >= 8 часов
COLOR_SEL    = "#4a90d9"  # Выбранная дата
COLOR_TEXT   = "#000000"
COLOR_TEXT_SEL = "#ffffff"

# ─── Работа с данными ────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cleanup_old_entries(data):
    cutoff = (datetime.now() - timedelta(days=CLEANUP_DAYS)).strftime("%Y-%m-%d")
    to_remove = [k for k in data if k != "recent_tasks" and k < cutoff]
    for k in to_remove:
        del data[k]
    if to_remove:
        save_data(data)

def update_task_history(data, task_name):
    if not task_name or not task_name.strip():
        return
    history = data.get("recent_tasks", [])
    name = task_name.strip()
    history = [t for t in history if t.lower() != name.lower()]
    history.insert(0, name)
    history = history[:MAX_RECENT_TASKS]
    data["recent_tasks"] = history
    save_data(data)

def get_total_hours(data, date_str):
    return sum(t.get("hours", 0) for t in data.get(date_str, []))

# ─── Кастомный Календарь ─────────────────────────────────────────
class SimpleCalendar:
    def __init__(self, master, year, month, day, on_select):
        self.master = master
        self.year = year
        self.month = month
        self.day = day
        self.on_select = on_select
        self.current_date = f"{year}-{month:02d}-{day:02d}"
        self.day_btns = {}
        self._build()

    def _build(self):
        self.frame = tk.Frame(self.master, bg="#ffffff")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Шапка: < Месяц Год >
        hdr = tk.Frame(self.frame, bg="#ffffff")
        hdr.pack(fill=tk.X, pady=(2, 4))
        tk.Button(hdr, text="◀", width=2, command=self._prev_month, bg="#f0f0f0", fg="#333", 
                  font=("Segoe UI", 9), relief="flat", cursor="hand2", bd=0).pack(side=tk.LEFT, padx=4)
        self.lbl_month = tk.Label(hdr, text="", font=("Segoe UI", 10, "bold"), fg="#222", bg="#ffffff")
        self.lbl_month.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(hdr, text="▶", width=2, command=self._next_month, bg="#f0f0f0", fg="#333",
                  font=("Segoe UI", 9), relief="flat", cursor="hand2", bd=0).pack(side=tk.RIGHT, padx=4)

        # Дни недели
        wd_frame = tk.Frame(self.frame, bg="#ffffff")
        wd_frame.pack(fill=tk.X, pady=(0, 2))
        for d in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]:
            tk.Label(wd_frame, text=d, width=3, font=("Segoe UI", 8, "bold"), 
                     fg="#666", bg="#ffffff").pack(side=tk.LEFT, expand=True)

        # Сетка дней
        self.grid_frame = tk.Frame(self.frame, bg="#ffffff")
        self.grid_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        self._draw_grid()

    def _draw_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.day_btns.clear()
        
        first_wd, days_in = cal_mod.monthrange(self.year, self.month)  # 0=Пн
        months_ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                     "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        self.lbl_month.config(text=f"{months_ru[self.month-1]} {self.year}")

        row, col = 0, 0
        # Пустые ячейки до начала месяца
        for _ in range(first_wd):
            tk.Frame(self.grid_frame, width=1, height=1, bg="#ffffff").grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
            col += 1

        for d in range(1, days_in + 1):
            btn = tk.Button(self.grid_frame, text=str(d), width=3, height=1,
                            bg="#ffffff", fg=COLOR_TEXT, font=("Segoe UI", 10),
                            relief="flat", bd=0, cursor="hand2", takefocus=False)
            btn.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
            btn.bind("<Button-1>", lambda e, y=self.year, m=self.month, dd=d: self._select(y, m, dd))
            self.day_btns[d] = btn
            col += 1
            if col == 7: col = 0; row += 1

        # Растягиваем сетку
        for i in range(7): self.grid_frame.columnconfigure(i, weight=1)
        for i in range(6): self.grid_frame.rowconfigure(i, weight=1)

    def _select(self, y, m, d):
        self.year, self.month, self.day = y, m, d
        self.current_date = f"{y}-{m:02d}-{d:02d}"
        self._draw_grid()
        self.on_select(self.current_date)

    def _prev_month(self):
        if self.month == 1: self.month = 12; self.year -= 1
        else: self.month -= 1
        self._draw_grid()

    def _next_month(self):
        if self.month == 12: self.month = 1; self.year += 1
        else: self.month += 1
        self._draw_grid()

    def highlight_days(self, data):
        """Обновляет цвета ячеек на основе данных"""
        for d, btn in self.day_btns.items():
            date_str = f"{self.year}-{self.month:02d}-{d:02d}"
            hours = get_total_hours(data, date_str)
            
            if d == self.day and self.month == datetime.now().month and self.year == datetime.now().year:
                # Выбранная дата всегда синяя
                btn.config(bg=COLOR_SEL, fg=COLOR_TEXT_SEL)
            else:
                if hours >= 8:
                    btn.config(bg=COLOR_GREEN, fg=COLOR_TEXT)
                elif hours > 0:
                    btn.config(bg=COLOR_YELLOW, fg=COLOR_TEXT)
                else:
                    btn.config(bg="#ffffff", fg=COLOR_TEXT)

# ─── GUI ─────────────────────────────────────────────────────────
class TaskLoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Task Logger v{VERSION}")
        self.root.geometry("1100x720")
        self.root.minsize(950, 650)

        self.data = load_data()
        cleanup_old_entries(self.data)
        self.editing_index = None

        self._setup_styles()
        self._build_ui()
        self._update_autocomplete()
        self._check_inputs()
        self._go_today()

    def _setup_styles(self):
        self.s = ttk.Style()
        self.s.theme_use('clam')
        self.font_base = ("Segoe UI", 11)
        self.font_title = ("Segoe UI", 12, "bold")
        self.font_btn = ("Segoe UI", 10, "bold")

        for name, bg, fg, active in [
            ("Gen", "#27ae60", "white", "#2ecc71"),
            ("Edit", "#2980b9", "white", "#3498db"),
            ("Del", "#c0392b", "white", "#e74c3c"),
            ("Today", "#f39c12", "white", "#d68910"),
            ("Add", "#ccc", "#444", "#bbb"),
            ("AddOk", "#2ecc71", "white", "#27ae60"),
            ("Save", "#d35400", "white", "#e67e22")
        ]:
            self.s.configure(f'{name}.TButton', background=bg, foreground=fg, font=self.font_btn)
            self.s.map(f'{name}.TButton', 
                       background=[('active', active), ('disabled', '#ddd')], 
                       foreground=[('disabled', '#888')])

        self.s.configure('Treeview', font=self.font_base, rowheight=28, background="white")
        self.s.configure('Treeview.Heading', font=self.font_title, background="#f0f0f0", foreground="black")

    def _add_ctx_menu(self, widget):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Вырезать (Cut)", command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Копировать (Copy)", command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Вставить (Paste)", command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="Очистить (Clear)", command=lambda: widget.delete(0, tk.END))
        
        def show(event):
            menu.tk_popup(event.x_root, event.y_root)
        widget.bind("<Button-3>", show)
        widget.bind("<Button-2>", show)

    def _hours_validate(self, event):
        if event.char and not event.char.isdigit() and event.keysym not in ('BackSpace', 'Delete', 'Left', 'Right', 'Tab', 'Return'):
            return "break"

    def _build_ui(self):
        main = tk.Frame(self.root, padx=14, pady=14)
        main.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main, width=320, height=320)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        left.pack_propagate(False)

        tk.Label(left, text="📅 Выберите дату", font=self.font_title).pack(pady=(0, 6))
        
        self.btn_today = ttk.Button(left, text="📅 Сегодня", command=self._go_today, style='Today.TButton')
        self.btn_today.pack(pady=(0, 8))

        # Кастомный календарь
        today = datetime.now()
        self.calendar = SimpleCalendar(left, today.year, today.month, today.day, self._on_date_selected)

        right = tk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        title_fr = tk.Frame(right)
        title_fr.pack(fill=tk.X, pady=(0, 12))
        self.date_label = tk.Label(title_fr, text="", font=("Segoe UI", 14, "bold"), fg="#333")
        self.date_label.pack(side=tk.LEFT)
        self.count_label = tk.Label(title_fr, text="", font=self.font_base, fg="#777")
        self.count_label.pack(side=tk.RIGHT)

        form = tk.LabelFrame(right, text="➕ Новая задача", font=self.font_title, padx=12, pady=12, relief="groove")
        form.pack(fill=tk.X, pady=(0, 12))

        tk.Label(form, text="Задача:", font=self.font_base).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_task = ttk.Combobox(form, width=25, font=self.font_base)
        self.entry_task.grid(row=0, column=1, padx=5, pady=(4,4), sticky=tk.EW)

        tk.Label(form, text="Часы:", font=self.font_base).grid(row=0, column=2, sticky=tk.W, pady=5)
        self.entry_hours = ttk.Entry(form, width=10, font=self.font_base)
        self.entry_hours.grid(row=0, column=3, padx=5, pady=(4,4), sticky=tk.W)
        self.entry_hours.bind("<Key>", self._hours_validate)

        tk.Label(form, text="Описание:", font=self.font_base).grid(row=1, column=0, sticky=tk.NW, pady=(5, 0))
        self.entry_desc = ttk.Entry(form, width=50, font=self.font_base)
        self.entry_desc.grid(row=1, column=1, columnspan=2, padx=5, pady=(4,4), sticky=tk.EW)

        self.btn_add = ttk.Button(form, text="Добавить (Enter)", command=self._submit_task, style='Add.TButton')
        self.btn_add.grid(row=1, column=3, padx=5, pady=(4,4), sticky=tk.E)
        form.columnconfigure(1, weight=1)

        self._add_ctx_menu(self.entry_task)
        self._add_ctx_menu(self.entry_hours)
        self._add_ctx_menu(self.entry_desc)

        self.entry_desc.bind('<Return>', self._on_enter_add)
        self.entry_hours.bind('<Return>', lambda e: self.entry_desc.focus_set())
        for w in [self.entry_task, self.entry_hours, self.entry_desc]:
            w.bind('<KeyRelease>', self._check_inputs)

        list_fr = tk.LabelFrame(right, text="📋 Задачи на день", font=self.font_title, padx=6, pady=6, relief="groove")
        list_fr.pack(fill=tk.BOTH, expand=True)

        cols = ("idx", "task", "hours", "desc")
        self.tree = ttk.Treeview(list_fr, columns=cols, show="headings", height=12)
        self.tree.heading("idx", text="№")
        self.tree.heading("task", text="Задача")
        self.tree.heading("hours", text="Часы")
        self.tree.heading("desc", text="Описание")
        self.tree.column("idx", width=40, anchor=tk.CENTER)
        self.tree.column("task", width=200, anchor=tk.W)
        self.tree.column("hours", width=80, anchor=tk.CENTER)
        self.tree.column("desc", width=500, anchor=tk.W)

        scr = ttk.Scrollbar(list_fr, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scr.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scr.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._update_button_states)
        self.tree.bind("<Double-1>", self._start_edit)

        bot = tk.Frame(right, pady=10)
        bot.pack(fill=tk.X)

        self.btn_generate = ttk.Button(bot, text="📋 Сгенерировать в буфер", command=self._generate, style='Gen.TButton')
        self.btn_generate.pack(side=tk.LEFT, padx=5)

        self.btn_edit = ttk.Button(bot, text="✏️ Редактировать", command=self._start_edit, style='Edit.TButton', state=tk.DISABLED)
        self.btn_edit.pack(side=tk.LEFT, padx=5)

        self.btn_delete = ttk.Button(bot, text="🗑 Удалить", command=self._delete_selected, style='Del.TButton', state=tk.DISABLED)
        self.btn_delete.pack(side=tk.LEFT, padx=5)

    # ─── Логика ──────────────────────────────────────────────────
    def _check_inputs(self, event=None):
        task = self.entry_task.get().strip()
        hours = self.entry_hours.get().strip()
        desc = self.entry_desc.get().strip()
        ok = False
        if task and hours and desc:
            try:
                float(hours)
                ok = True
            except ValueError:
                pass
        self.btn_add.configure(style='AddOk.TButton' if ok else 'Add.TButton')

    def _on_enter_add(self, event):
        if self.btn_add.cget('style') == 'AddOk.TButton':
            self._submit_task()
        return "break"

    def _update_button_states(self, event=None):
        sel = self.tree.selection()
        st = tk.NORMAL if sel else tk.DISABLED
        self.btn_edit.configure(state=st)
        self.btn_delete.configure(state=st)

    def _update_autocomplete(self):
        self.entry_task["values"] = self.data.get("recent_tasks", [])

    def _on_date_selected(self, date_str):
        self.current_date = date_str
        self._update_date_label()
        self._refresh_task_list()
        self.calendar.highlight_days(self.data)

    def _update_date_label(self):
        dt = datetime.strptime(self.current_date, "%Y-%m-%d")
        days_ru = {"Monday": "Пн", "Tuesday": "Вт", "Wednesday": "Ср", "Thursday": "Чт",
                   "Friday": "Пт", "Saturday": "Сб", "Sunday": "Вс"}
        self.date_label.config(text=f"{dt.strftime('%d.%m.%Y')} ({days_ru.get(dt.strftime('%A'), '')})")

    def _refresh_task_list(self):
        tasks = self.data.get(self.current_date, [])
        self.tree.delete(*self.tree.get_children())
        total = 0
        for i, t in enumerate(tasks, 1):
            self.tree.insert("", tk.END, values=(i, t["task"], t["hours"], t["description"]))
            total += t["hours"]
        self.count_label.config(text=f"{len(tasks)} задач, {total} ч.")
        self._update_autocomplete()
        self._update_button_states()

    def _start_edit(self, event=None):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Инфо", "Выберите задачу для редактирования.")
            return
        item = self.tree.item(sel[0])
        self.editing_index = int(item["values"][0]) - 1
        self.entry_task.set(item["values"][1])
        self.entry_hours.delete(0, tk.END)
        self.entry_hours.insert(0, str(item["values"][2]))
        self.entry_desc.delete(0, tk.END)
        self.entry_desc.insert(0, item["values"][3])
        self.btn_add.configure(text="💾 Сохранить", style='Save.TButton')
        self.entry_task.focus()

    def _submit_task(self):
        task = self.entry_task.get().strip()
        hours_str = self.entry_hours.get().strip()
        desc = self.entry_desc.get().strip()
        if not task or not hours_str or not desc:
            messagebox.showwarning("Внимание", "Заполните все поля!")
            return
        try:
            hours = float(hours_str)
            if hours < 0: raise ValueError
            hours = int(hours) if hours == int(hours) else hours
        except ValueError:
            messagebox.showwarning("Ошибка", "Часы должны быть числом!")
            return

        tasks = self.data.setdefault(self.current_date, [])
        if self.editing_index is not None:
            tasks[self.editing_index] = {"task": task, "hours": hours, "description": desc}
            self.editing_index = None
            self.btn_add.configure(text="Добавить (Enter)", style='AddOk.TButton')
        else:
            tasks.append({"task": task, "hours": hours, "description": desc})
            update_task_history(self.data, task)

        save_data(self.data)
        self._refresh_task_list()
        self.calendar.highlight_days(self.data)
        self.entry_task.set("")
        self.entry_hours.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.entry_task.focus()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel: return
        idx = int(self.tree.item(sel[0])["values"][0]) - 1
        if messagebox.askyesno("Удаление", f"Удалить «{self.tree.item(sel[0])['values'][1]}»?"):
            tasks = self.data.get(self.current_date, [])
            tasks.pop(idx)
            if not tasks: del self.data[self.current_date]
            save_data(self.data)
            self._refresh_task_list()
            self.calendar.highlight_days(self.data)

    def _generate(self):
        tasks = self.data.get(self.current_date, [])
        if not tasks:
            messagebox.showinfo("Инфо", "Нет задач.")
            return
        dt = datetime.strptime(self.current_date, "%Y-%m-%d")
        short = dt.strftime("%d.%m.%y")
        lines = [f"{t['task']} {t['hours']} [{short}] {t['description']}" for t in tasks]
        pyperclip.copy("\n".join(lines))
        messagebox.showinfo("✅ Готово", "Скопировано в буфер обмена.")

    def _go_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.calendar._select(*map(int, today.split("-")))
        self.calendar.highlight_days(self.data)

# ─── Запуск ──────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = TaskLoggerApp(root)
    root.mainloop()