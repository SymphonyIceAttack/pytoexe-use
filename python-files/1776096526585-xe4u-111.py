#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
КСА 45Л6-1С – Оценка технического состояния
Версия 6.1 (исправленные примеры, корректные категории)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import math
import csv
from datetime import datetime
import os

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

def calculate_reliability(dn, N, t, To, m, Tvk):
    if dn <= 0 or N <= 0 or t <= 0 or To <= 0 or m <= 0 or Tvk <= 0:
        raise ValueError("Все значения >0")
    lam = dn / (N * t)
    vbr = math.exp(-lam * t)
    tvosst = Tvk / m
    kg = To / (To + tvosst)
    kog = kg * vbr
    return {'vbr': vbr, 'lam': lam, 'kg': kg, 'kog': kog}

def system_reliability(vbr_list):
    res = 1.0
    for v in vbr_list:
        res *= v
    return res

def predict_reliability(current_vbr, lam, delta_t):
    return current_vbr * math.exp(-lam * delta_t)

def get_category(vbr):
    if vbr >= 0.98:
        return ("ОТЛИЧНОЕ", "#2ecc71", "✅", "Допуск без ограничений")
    elif vbr >= 0.95:
        return ("ХОРОШЕЕ", "#3498db", "👍", "Допуск, контроль 12 ч")
    elif vbr >= 0.90:
        return ("УДОВЛЕТВОРИТЕЛЬНОЕ", "#f39c12", "⚠️", "Допуск с ограничением, внеплановое ТО")
    else:
        return ("НЕУДОВЛЕТВОРИТЕЛЬНОЕ", "#e74c3c", "❌", "НЕ ДОПУСКАТЬ, требуется ремонт")

SUBSYSTEMS = ["ЦВК", "Средства отображения", "КСПД 98Ф6", "Средства регистрации", "Средства сопряжения"]

class Database:
    def __init__(self, db_path="ksa_history.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                vbr1 REAL, vbr2 REAL, vbr3 REAL, vbr4 REAL, vbr5 REAL,
                lam1 REAL, lam2 REAL, lam3 REAL, lam4 REAL, lam5 REAL,
                kg1 REAL, kg2 REAL, kg3 REAL, kg4 REAL, kg5 REAL,
                vbr_system REAL,
                category TEXT,
                recommendation TEXT
            )
        ''')
        self.conn.commit()
    def save(self, data):
        self.cursor.execute('''
            INSERT INTO history (
                timestamp, vbr1, vbr2, vbr3, vbr4, vbr5,
                lam1, lam2, lam3, lam4, lam5,
                kg1, kg2, kg3, kg4, kg5,
                vbr_system, category, recommendation
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data['vbr1'], data['vbr2'], data['vbr3'], data['vbr4'], data['vbr5'],
            data['lam1'], data['lam2'], data['lam3'], data['lam4'], data['lam5'],
            data['kg1'], data['kg2'], data['kg3'], data['kg4'], data['kg5'],
            data['vbr_system'], data['category'], data['recommendation']
        ))
        self.conn.commit()
    def get_all(self):
        self.cursor.execute("SELECT timestamp, vbr_system, category FROM history ORDER BY id")
        return self.cursor.fetchall()
    def export_csv(self, filename):
        self.cursor.execute("SELECT * FROM history")
        rows = self.cursor.fetchall()
        if not rows:
            return False
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([desc[0] for desc in self.cursor.description])
            writer.writerows(rows)
        return True
    def close(self):
        self.conn.close()

class InputDialog(tk.Toplevel):
    def __init__(self, parent, idx, callback):
        super().__init__(parent)
        self.callback = callback
        self.idx = idx
        self.title(f"Ввод – {SUBSYSTEMS[idx-1]}")
        self.geometry("480x420")
        self.resizable(False, False)
        self.configure(bg="#f0f2f5")
        self.grab_set()
        self.vars = {}
        self._create_widgets()
    def _create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text=f"Подсистема {self.idx}: {SUBSYSTEMS[self.idx-1]}", font=("Segoe UI", 12, "bold")).pack(pady=5)
        fields = [
            ("Δn (число отказов за период)", "dn"),
            ("N (число наблюдаемых объектов)", "N"),
            ("t (время наработки, ч)", "t"),
            ("Tо (средняя наработка на отказ, ч)", "To"),
            ("m (число отказов за весь период)", "m"),
            ("Tв (среднее время восстановления, ч)", "Tv")
        ]
        frame = ttk.Frame(main)
        frame.pack(fill=tk.BOTH, expand=True, pady=10)
        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=25)
            entry.grid(row=i, column=1, pady=5, padx=5)
            self.vars[key] = var
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Рассчитать", command=self._calc).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    def _calc(self):
        try:
            dn = float(self.vars["dn"].get())
            N = float(self.vars["N"].get())
            t = float(self.vars["t"].get())
            To = float(self.vars["To"].get())
            m = float(self.vars["m"].get())
            Tv = float(self.vars["Tv"].get())
            res = calculate_reliability(dn, N, t, To, m, Tv)
            self.callback(self.idx, res)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Некорректные данные:\n{e}")

class SplashScreen:
    def __init__(self, root, callback, duration=2500):
        self.root = root
        self.callback = callback
        self.splash = tk.Toplevel(root)
        self.splash.overrideredirect(True)
        self.splash.configure(bg="#1a3d7c")
        w, h = 550, 350
        x = (self.splash.winfo_screenwidth() - w)//2
        y = (self.splash.winfo_screenheight() - h)//2
        self.splash.geometry(f"{w}x{h}+{x}+{y}")
        frame = tk.Frame(self.splash, bg="#1a3d7c")
        frame.pack(expand=True, fill=tk.BOTH)
        image = None
        if os.path.exists("splash.gif"):
            try:
                image = tk.PhotoImage(file="splash.gif")
                if image.width() > 400:
                    ratio = 400 / image.width()
                    new_w = int(image.width() * ratio)
                    new_h = int(image.height() * ratio)
                    image = image.subsample(image.width()//new_w, image.height()//new_h)
                lbl_img = tk.Label(frame, image=image, bg="#1a3d7c")
                lbl_img.image = image
                lbl_img.pack(pady=10)
            except Exception:
                image = None
        if image is None:
            tk.Label(frame, text="КСА 45Л6-1С", font=("Segoe UI", 28, "bold"), fg="white", bg="#1a3d7c").pack(pady=(40,5))
            tk.Label(frame, text="Автоматизированная оценка технического состояния", font=("Segoe UI", 11), fg="#bdc3c7", bg="#1a3d7c").pack()
        else:
            tk.Label(frame, text="КСА 45Л6-1С", font=("Segoe UI", 16, "bold"), fg="white", bg="#1a3d7c").pack()
        tk.Label(frame, text="Военная академия ВКО им. Г.К. Жукова", font=("Segoe UI", 9), fg="#7f8c8d", bg="#1a3d7c").pack(pady=(10,5))
        tk.Label(frame, text="Загрузка...", font=("Segoe UI", 9), fg="#95a5a6", bg="#1a3d7c").pack(pady=5)
        self.prog = ttk.Progressbar(frame, mode='indeterminate', length=350)
        self.prog.pack(pady=15)
        self.prog.start(10)
        self.splash.bind("<Button-1>", self._close)
        self.root.after(duration, self._close)
    def _close(self, event=None):
        if self.prog:
            self.prog.stop()
        self.splash.destroy()
        self.callback()

class UltimateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("КСА 45Л6-1С – Оценка технического состояния")
        self.root.geometry("1350x850")
        self.root.configure(bg="#f0f2f5")
        self.db = Database()
        self.subs = {i: {'vbr':0.0, 'lam':0.0, 'kg':0.0, 'kog':0.0} for i in range(1,6)}
        self.system_vbr = 0.0
        self.last_category = ""
        self.last_rec = ""
        self._setup_styles()
        self._create_menu()
        self._create_notebook()
        self._create_eval_tab()
        self._create_history_tab()
        self._create_predict_tab()
        self._create_statusbar()
        self._update_table()
        self._refresh_history()
        self._draw_graph()
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Accent.TButton", background="#2ecc71")
        style.map("Accent.TButton", background=[("active", "#27ae60")])
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#34495e", foreground="white")
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Экспорт отчёта (TXT)", command=self._export_report)
        file_menu.add_command(label="Экспорт истории (CSV)", command=self._export_csv)
        file_menu.add_command(label="Копировать отчёт в буфер", command=self._copy_report)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._about)
    def _create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    def _create_eval_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 ОЦЕНКА")
        frame_table = ttk.LabelFrame(tab, text="Показатели надёжности подсистем", padding=10)
        frame_table.pack(fill=tk.BOTH, expand=True, pady=5)
        columns = ("Подсистема", "ВБР P(t)", "λ (1/час)", "Kг", "Статус")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=5)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200 if col=="Подсистема" else 120, anchor=tk.CENTER)
        for i, name in enumerate(SUBSYSTEMS, 1):
            self.tree.insert("", tk.END, iid=i, values=(name, "—", "—", "—", "⚪ Не рассчитана"))
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self._on_row_click)
        btn_panel = tk.Frame(frame_table, bg="#f0f2f5")
        btn_panel.pack(fill=tk.X, pady=5)
        for i in range(1,6):
            btn = tk.Button(btn_panel, text=f"📌 Подсистема {i}", font=("Segoe UI", 9),
                            bg="#ecf0f1", relief=tk.RAISED, padx=8, pady=4,
                            command=lambda idx=i: self._open_input(idx))
            btn.pack(side=tk.LEFT, padx=3, expand=True, fill=tk.X)
        ctrl = ttk.Frame(tab)
        ctrl.pack(fill=tk.X, pady=10)
        ttk.Button(ctrl, text="🚀 РАССЧИТАТЬ СИСТЕМУ", command=self._calc_system, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="💾 СОХРАНИТЬ В БД", command=self._save_to_db).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="🗑 ОЧИСТИТЬ ВСЁ", command=self._clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="📄 ЭКСПОРТ ОТЧЁТА", command=self._export_report).pack(side=tk.LEFT, padx=5)
        auto_frame = ttk.Frame(tab)
        auto_frame.pack(fill=tk.X, pady=5)
        ttk.Label(auto_frame, text="Быстрое заполнение примером:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        ttk.Button(auto_frame, text="📈 Отлично (0.98+)", command=lambda: self._auto_fill("excellent")).pack(side=tk.LEFT, padx=2)
        ttk.Button(auto_frame, text="👍 Хорошо (0.95+)", command=lambda: self._auto_fill("good")).pack(side=tk.LEFT, padx=2)
        ttk.Button(auto_frame, text="⚠️ Удовл. (0.90+)", command=lambda: self._auto_fill("satisfactory")).pack(side=tk.LEFT, padx=2)
        ttk.Button(auto_frame, text="❌ Неудовл.", command=lambda: self._auto_fill("bad")).pack(side=tk.LEFT, padx=2)
        frame_rec = ttk.LabelFrame(tab, text="ЗАКЛЮЧЕНИЕ И РЕКОМЕНДАЦИИ", padding=10)
        frame_rec.pack(fill=tk.BOTH, expand=True, pady=5)
        self.result_text = tk.Text(frame_rec, wrap=tk.WORD, font=("Consolas", 10), height=10, relief=tk.FLAT)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.config(state=tk.DISABLED)
    def _create_history_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📜 ИСТОРИЯ + ГРАФИК")
        frame = ttk.Frame(tab, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Button(frame, text="Обновить", command=self._refresh_history).pack(anchor=tk.W, pady=5)
        self.history_tree = ttk.Treeview(frame, columns=("date", "vbr", "category"), show="headings", height=8)
        self.history_tree.heading("date", text="Дата/время")
        self.history_tree.heading("vbr", text="Общая ВБР")
        self.history_tree.heading("category", text="Категория")
        self.history_tree.column("date", width=180)
        self.history_tree.column("vbr", width=120)
        self.history_tree.column("category", width=150)
        self.history_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.graph_frame = ttk.Frame(frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    def _create_predict_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔮 ПРОГНОЗ")
        main = ttk.Frame(tab, padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text="Выберите подсистему:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky=tk.W)
        self.pred_subs = ttk.Combobox(main, values=[f"{i}. {name}" for i, name in enumerate(SUBSYSTEMS,1)], width=50)
        self.pred_subs.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        self.pred_subs.current(0)
        ttk.Label(main, text="Дополнительное время Δt (часы):", font=("Segoe UI", 11)).grid(row=1, column=0, sticky=tk.W)
        self.pred_time = ttk.Entry(main, width=20)
        self.pred_time.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Button(main, text="Рассчитать прогноз", command=self._do_predict).grid(row=2, column=0, columnspan=2, pady=15)
        self.pred_res = tk.Text(main, wrap=tk.WORD, font=("Consolas", 10), height=8, width=80)
        self.pred_res.grid(row=3, column=0, columnspan=2, pady=10)
    def _create_statusbar(self):
        self.status_var = tk.StringVar(value="Готов")
        status = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status.pack(side=tk.BOTTOM, fill=tk.X)
    def _on_row_click(self, event):
        item = self.tree.selection()[0]
        self._open_input(int(item))
    def _open_input(self, idx):
        InputDialog(self.root, idx, self._on_subs_calc)
    def _on_subs_calc(self, idx, res):
        self.subs[idx] = res
        self._update_table()
        self.status_var.set(f"Подсистема {idx} рассчитана: ВБР={res['vbr']:.6f}")
    def _update_table(self):
        for i in range(1,6):
            vbr = self.subs[i]['vbr']
            lam = self.subs[i]['lam']
            kg = self.subs[i]['kg']
            if vbr == 0:
                status = "⚪ Не рассчитана"
                vbr_str = "—"
                lam_str = "—"
                kg_str = "—"
            else:
                status = "✅ Рассчитана"
                vbr_str = f"{vbr:.6f}"
                lam_str = f"{lam:.8f}"
                kg_str = f"{kg:.4f}"
            self.tree.item(i, values=(SUBSYSTEMS[i-1], vbr_str, lam_str, kg_str, status))
    def _calc_system(self):
        vbrs = [self.subs[i]['vbr'] for i in range(1,6)]
        if any(v==0 for v in vbrs):
            messagebox.showwarning("Неполные данные", "Рассчитайте все пять подсистем.")
            return
        self.system_vbr = system_reliability(vbrs)
        cat, color, emoji, action = get_category(self.system_vbr)
        self.last_category = cat
        min_vbr = min(vbrs)
        weak_idx = vbrs.index(min_vbr)+1
        weak_name = SUBSYSTEMS[weak_idx-1]
        rec = f"{emoji}  ОБЩАЯ ВБР: {self.system_vbr:.6f}\n"
        rec += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        rec += f"Категория: {cat}\n"
        rec += f"Рекомендация: {action}\n"
        if self.system_vbr < 0.95:
            rec += f"\n⚠ Слабая подсистема: {weak_name} (ВБР={min_vbr:.6f})\n"
            rec += f"⚠ Требуется внеплановое ТО.\n"
        rec += "\nПодробные показатели:\n"
        for i in range(1,6):
            rec += f"  {SUBSYSTEMS[i-1][:20]}: P={self.subs[i]['vbr']:.6f}, Kг={self.subs[i]['kg']:.4f}\n"
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, rec)
        self.result_text.config(state=tk.DISABLED)
        if cat == "ОТЛИЧНОЕ":
            bg = "#d5f5e3"
        elif cat == "ХОРОШЕЕ":
            bg = "#d6eaf8"
        elif cat == "УДОВЛЕТВОРИТЕЛЬНОЕ":
            bg = "#fef5e7"
        else:
            bg = "#fadbd8"
        self.result_text.config(bg=bg)
        self.last_rec = rec
        if cat == "НЕУДОВЛЕТВОРИТЕЛЬНОЕ" and SOUND_AVAILABLE:
            winsound.Beep(1000, 500)
        self.status_var.set(f"Система рассчитана: ВБР={self.system_vbr:.6f}")
    def _save_to_db(self):
        if self.system_vbr == 0.0:
            messagebox.showwarning("Нет расчёта", "Сначала рассчитайте систему.")
            return
        data = {
            'vbr1': self.subs[1]['vbr'], 'vbr2': self.subs[2]['vbr'],
            'vbr3': self.subs[3]['vbr'], 'vbr4': self.subs[4]['vbr'],
            'vbr5': self.subs[5]['vbr'],
            'lam1': self.subs[1]['lam'], 'lam2': self.subs[2]['lam'],
            'lam3': self.subs[3]['lam'], 'lam4': self.subs[4]['lam'],
            'lam5': self.subs[5]['lam'],
            'kg1': self.subs[1]['kg'], 'kg2': self.subs[2]['kg'],
            'kg3': self.subs[3]['kg'], 'kg4': self.subs[4]['kg'],
            'kg5': self.subs[5]['kg'],
            'vbr_system': self.system_vbr,
            'category': self.last_category,
            'recommendation': self.last_rec
        }
        self.db.save(data)
        messagebox.showinfo("Сохранено", "Результат сохранён в базу данных.")
        self._refresh_history()
        self._draw_graph()
        self.status_var.set("Сохранено в БД")
    def _refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        rows = self.db.get_all()
        for ts, vbr, cat in rows:
            self.history_tree.insert("", tk.END, values=(ts, f"{vbr:.6f}", cat))
        self._draw_graph()
    def _draw_graph(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        if not MATPLOTLIB_OK:
            lbl = tk.Label(self.graph_frame, text="Matplotlib не установлен. Графики недоступны.\nУстановите: pip install matplotlib", font=("Segoe UI", 10), fg="red")
            lbl.pack(expand=True)
            return
        data = self.db.get_all()
        if len(data) < 2:
            lbl = tk.Label(self.graph_frame, text="Недостаточно данных для графика (нужно минимум 2 записи).\nСохраните несколько расчётов в БД.", font=("Segoe UI", 10), fg="gray")
            lbl.pack(expand=True)
            return
        dates = [row[0] for row in data]
        vbrs = [row[1] for row in data]
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(dates, vbrs, marker='o', linestyle='-', linewidth=2, color='#2c3e50')
        ax.set_xlabel("Дата/время", fontsize=9)
        ax.set_ylabel("Общая ВБР", fontsize=9)
        ax.set_title("Динамика надёжности КСА 45Л6-1С", fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_ylim(0, 1)
        plt.xticks(rotation=45, ha='right', fontsize=8)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    def _clear_all(self):
        for i in range(1,6):
            self.subs[i] = {'vbr':0.0, 'lam':0.0, 'kg':0.0, 'kog':0.0}
        self.system_vbr = 0.0
        self._update_table()
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.status_var.set("Все данные очищены")
    def _do_predict(self):
        try:
            idx = int(self.pred_subs.get()[0]) - 1
            dt = float(self.pred_time.get())
            if dt <= 0: raise ValueError
            data = self.subs[idx+1]
            if data['vbr'] == 0.0:
                messagebox.showwarning("Нет данных", f"Подсистема {idx+1} не рассчитана.")
                return
            pred = predict_reliability(data['vbr'], data['lam'], dt)
            self.pred_res.delete(1.0, tk.END)
            self.pred_res.insert(tk.END, f"ПРОГНОЗ ДЛЯ {SUBSYSTEMS[idx]}\n")
            self.pred_res.insert(tk.END, f"Текущая ВБР: {data['vbr']:.6f}\n")
            self.pred_res.insert(tk.END, f"λ = {data['lam']:.8f} 1/час\n")
            self.pred_res.insert(tk.END, f"Дополнительная наработка: {dt} ч\n")
            self.pred_res.insert(tk.END, f"Прогнозируемая ВБР через {dt} ч: {pred:.6f}\n")
            if pred < 0.9:
                self.pred_res.insert(tk.END, "⚠ ВНИМАНИЕ: надёжность ниже 0.90!\n")
        except:
            messagebox.showerror("Ошибка", "Введите положительное число часов.")
    def _auto_fill(self, variant):
        """Прямая установка показателей для гарантированной категории"""
        if variant == "excellent":
            vbr = 0.9965   # общая ~0.983
            lam = 0.000035
            kg = 0.9965
        elif variant == "good":
            vbr = 0.99      # общая ~0.951
            lam = 0.0001
            kg = 0.99
        elif variant == "satisfactory":
            vbr = 0.98      # общая ~0.904 (входит в 0.90-0.95)
            lam = 0.0002
            kg = 0.98
        else:  # bad
            vbr = 0.85
            lam = 0.0016
            kg = 0.85
        for i in range(1,6):
            self.subs[i] = {'vbr': vbr, 'lam': lam, 'kg': kg, 'kog': vbr * kg}
        self._update_table()
        self.status_var.set(f"Заполнен пример: {variant}. Нажмите 'Рассчитать систему'.")
    def _export_report(self):
        if self.system_vbr == 0.0:
            messagebox.showwarning("Нет данных", "Сначала рассчитайте систему.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Текстовые файлы", "*.txt")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("ОТЧЁТ ПО ОЦЕНКЕ ТЕХНИЧЕСКОГО СОСТОЯНИЯ КСА 45Л6-1С\n")
                f.write(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("="*60 + "\n")
                for i in range(1,6):
                    d = self.subs[i]
                    f.write(f"{SUBSYSTEMS[i-1]}:\n")
                    f.write(f"  ВБР = {d['vbr']:.6f}\n")
                    f.write(f"  λ = {d['lam']:.8f} 1/час\n")
                    f.write(f"  Kг = {d['kg']:.4f}\n")
                f.write(f"\nОбщая ВБР системы: {self.system_vbr:.6f}\n")
                f.write(self.result_text.get(1.0, tk.END))
            messagebox.showinfo("Экспорт", f"Отчёт сохранён в {filename}")
    def _export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV файлы", "*.csv")])
        if filename:
            if self.db.export_csv(filename):
                messagebox.showinfo("Экспорт", f"История сохранена в {filename}")
            else:
                messagebox.showwarning("Экспорт", "Нет данных для экспорта.")
    def _copy_report(self):
        if self.system_vbr == 0.0:
            messagebox.showwarning("Нет данных", "Сначала рассчитайте систему.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.result_text.get(1.0, tk.END))
        self.status_var.set("Отчёт скопирован в буфер обмена")
    def _about(self):
        msg = ("КСА 45Л6-1С – Оценка технического состояния\n"
               "Версия 6.1 (исправленные примеры)\n"
               "Разработчик: Свирко В.А.\n"
               "Военная академия ВКО им. Г.К. Жукова, 2026\n\n"
               "Функции:\n"
               "- 4 готовых примера с корректными категориями\n"
               "- Расчёт надёжности, прогноз, история, график\n"
               "- Экспорт, копирование отчёта\n"
               "- Заставка с фото (splash.gif)")
        messagebox.showinfo("О программе", msg)

def main():
    root = tk.Tk()
    root.withdraw()
    def start():
        root.deiconify()
        app = UltimateApp(root)
    splash = SplashScreen(root, start, duration=2500)
    root.mainloop()

if __name__ == "__main__":
    main()
