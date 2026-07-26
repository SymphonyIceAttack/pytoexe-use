import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from functools import lru_cache
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ========== ЯДРО КОМБИНАТОРНЫХ ФУНКЦИЙ ==========
@lru_cache(maxsize=None)
def fact(n):
    if n < 0:
        raise ValueError("n >= 0")
    if n == 0:
        return 1
    return n * fact(n-1)

def perm(n, k):
    if k > n:
        return 0
    return fact(n) // fact(n-k)

def comb(n, k):
    if k > n:
        return 0
    return fact(n) // (fact(k) * fact(n-k))

def comb_with_repetition(n, k):
    if n == 0 and k == 0:
        return 1
    return comb(n + k - 1, k)

def perm_with_repetition(n, counts):
    denom = 1
    for c in counts:
        denom *= fact(c)
    return fact(n) // denom

def probability_choose(n_total, k_total, n_success, k_success):
    if k_success > n_success or k_total - k_success > n_total - n_success:
        return 0.0
    favorable = comb(n_success, k_success) * comb(n_total - n_success, k_total - k_success)
    total = comb(n_total, k_total)
    return favorable / total

def probability_at_least(n_total, k_total, n_success, min_success):
    prob = 0.0
    max_k = min(k_total, n_success)
    for k in range(min_success, max_k + 1):
        prob += probability_choose(n_total, k_total, n_success, k)
    return prob

def get_full_distribution(n_total, k_total, n_success):
    dist = {}
    max_k = min(k_total, n_success)
    for k in range(max_k + 1):
        p = probability_choose(n_total, k_total, n_success, k)
        if p > 0:
            dist[k] = p
    return dist

# ========== КЛАСС ДЛЯ ПОДСКАЗОК ==========
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event):
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9), wraplength=300)
        label.pack()

    def hide_tip(self, event):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# ========== ОСНОВНОЕ ПРИЛОЖЕНИЕ ==========
class CombinatoricsApp:
    def __init__(self, root):
        self.root = root
        self.current_distribution = None
        self.current_mode = None

        # Настройка окна
        self.root.title("🌈 Комбинаторный калькулятор вероятностей")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg='#f0f4f8')

        # Основной контейнер
        self.main_frame = tk.Frame(self.root, bg='#f0f4f8')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель – фиксированная ширина
        self.left_frame = tk.Frame(self.main_frame, bg='#ffffff', bd=2, relief=tk.GROOVE, width=400)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=5, pady=5)
        self.left_frame.pack_propagate(False)

        # Правая панель – расширяется
        self.right_frame = tk.Frame(self.main_frame, bg='#f0f4f8')
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ---------- ЛЕВАЯ ПАНЕЛЬ ----------
        # Заголовок
        self.title_label = tk.Label(self.left_frame, text="🌈 Комбинаторный калькулятор",
                                    font=("Segoe UI", 14, "bold"), fg='#3498db', bg='#ffffff')
        self.title_label.pack(pady=(5,2))
        self.subtitle_label = tk.Label(self.left_frame, text="Вероятности, перестановки, сочетания",
                                       font=("Segoe UI", 9), fg='#7f8c8d', bg='#ffffff')
        self.subtitle_label.pack(pady=(0,8))

        # Режимы
        self.mode_frame = tk.LabelFrame(self.left_frame, text="⚙️ Режим работы",
                                        font=("Segoe UI", 9, "bold"), bg='#ffffff',
                                        relief=tk.RIDGE, bd=2)
        self.mode_frame.pack(fill=tk.X, padx=3, pady=3)

        self.mode_var = tk.StringVar(value="probability")
        modes = [
            ("🎯 Вероятность (ровно K)", "probability"),
            ("📈 Вероятность (≥ K)", "at_least"),
            ("🔢 Сочетания C(n,k)", "comb"),
            ("🔀 Размещения A(n,k)", "perm"),
            ("❗ Перестановки P(n)", "fact"),
            ("🔄 Сочетания с повтор. C(n+k-1,k)", "comb_rep"),
            ("🌀 Перестановки с повтор.", "perm_rep"),
        ]
        for text, mode in modes:
            rb = tk.Radiobutton(self.mode_frame, text=text, variable=self.mode_var,
                                value=mode, command=self.update_inputs,
                                font=("Segoe UI", 8), bg='#ffffff',
                                selectcolor='#d4e6f1', activebackground='#d4e6f1',
                                fg='#2c3e50')
            rb.pack(anchor=tk.W, padx=8, pady=1)

        # Параметры
        self.input_frame = tk.LabelFrame(self.left_frame, text="📊 Параметры",
                                         font=("Segoe UI", 9, "bold"), bg='#ffffff',
                                         relief=tk.RIDGE, bd=2)
        self.input_frame.pack(fill=tk.X, padx=3, pady=3)

        self.var_n_total = tk.IntVar(value=52)
        self.var_k_total = tk.IntVar(value=5)
        self.var_n_success = tk.IntVar(value=4)
        self.var_k_success = tk.IntVar(value=2)
        self.var_min_success = tk.IntVar(value=2)
        self.var_counts = tk.StringVar(value="2,1,1")

        self.sliders = {}
        self.entries = {}
        self.build_inputs()

        # Флажок CDF
        self.cdf_var = tk.IntVar(value=0)
        cdf_cb = tk.Checkbutton(self.left_frame, text="📊 Показать CDF (накопленную вероятность)",
                                variable=self.cdf_var, command=self.on_cdf_toggle,
                                bg='#ffffff', font=("Segoe UI", 8))
        cdf_cb.pack(anchor=tk.W, padx=8, pady=2)

        # Кнопки
        btn_frame = tk.Frame(self.left_frame, bg='#ffffff')
        btn_frame.pack(fill=tk.X, padx=3, pady=3)

        self.calc_btn = tk.Button(btn_frame, text="✅ ВЫЧИСЛИТЬ", command=self.calculate,
                                  font=("Segoe UI", 9, "bold"), bg='#3498db',
                                  fg='white', relief=tk.RAISED, bd=2, padx=8, pady=3)
        self.calc_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,3))

        self.plot_btn = tk.Button(btn_frame, text="📊 ГРАФИК", command=self.plot_distribution,
                                  font=("Segoe UI", 9, "bold"), bg='#9b59b6',
                                  fg='white', relief=tk.RAISED, bd=2, padx=8, pady=3)
        self.plot_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3,0))

        # Результат – увеличенная высота
        self.result_frame = tk.LabelFrame(self.left_frame, text="📝 Результат",
                                          font=("Segoe UI", 9, "bold"), bg='#ffffff',
                                          relief=tk.RIDGE, bd=2)
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        self.result_text = tk.Text(self.result_frame, height=20, font=("Courier New", 9),
                                   bg='#fef9e7', fg='#2c3e50', wrap=tk.WORD,
                                   relief=tk.SUNKEN, bd=2)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        scrollbar = tk.Scrollbar(self.result_text, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ---------- ПРАВАЯ ПАНЕЛЬ (ГРАФИК) ----------
        self.figure = plt.Figure(figsize=(6, 5), dpi=100, facecolor='#34495e')
        self.ax = self.figure.add_subplot(111, facecolor='#2c3e50')
        self.ax.set_xlabel("Число успехов (k)", fontsize=10, color='white')
        self.ax.set_ylabel("Вероятность", fontsize=10, color='white')
        self.ax.set_title("📊 Распределение вероятностей", fontsize=12, color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3, color='white')

        self.canvas = FigureCanvasTkAgg(self.figure, self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Меню
        self.create_menu()

        # Инициализация
        self.update_inputs()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📁 Экспорт результата", command=self.export_result)
        file_menu.add_command(label="💾 Сохранить график", command=self.save_plot)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Меню Примеры с подробными описаниями
        examples_menu = tk.Menu(menubar, tearoff=0)
        examples_menu.add_command(
            label="🃏 Тузы в колоде (52 карты, выборка 5, 4 туза, ровно 2 туза)",
            command=lambda: self.load_example('aces')
        )
        examples_menu.add_command(
            label="🔧 Бракованные детали (партия 10, 3 брака, выборка 4, ровно 2 брака)",
            command=lambda: self.load_example('defective')
        )
        examples_menu.add_command(
            label="🎰 Лотерея (6 из 49, все 6 чисел угаданы)",
            command=lambda: self.load_example('lottery')
        )
        menubar.add_cascade(label="📚 Примеры", menu=examples_menu)

        self.root.config(menu=menubar)

    def build_inputs(self):
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        self.sliders.clear()
        self.entries.clear()

        mode = self.mode_var.get()
        row = 0

        tooltips = {
            "N (n_total)": "Общее количество элементов в совокупности (N).\nПример: для колоды карт N=52.",
            "K (k_total)": "Размер выборки (K). Сколько элементов извлекается.\nПример: в покере K=5.",
            "M (n_success)": "Количество «успешных» элементов среди N (M).\nПример: в колоде 4 туза – M=4.",
            "k (k_success)": "Сколько успешных элементов должно быть в выборке.\nПример: ровно 2 туза из 5 карт.",
            "k_min": "Минимальное число успешных элементов в выборке.\nПример: как минимум 2 туза.",
            "n (факториал)": "Число, для которого вычисляется факториал n!",
            "k (сочетания)": "Число элементов в сочетании (размещении).",
            "Количества (через запятую)": "Числа для каждого типа повторяющихся элементов.\nПример: 2,1,1 означает два одинаковых элемента первого типа, по одному второго и третьего."
        }

        if mode in ["probability", "at_least", "comb", "perm", "comb_rep"]:
            self.add_slider("N (общее)", "var_n_total", row, from_=1, to=100,
                            tooltip=tooltips["N (n_total)"])
            row += 1
        if mode in ["probability", "at_least", "comb", "perm"]:
            self.add_slider("K (выборка)", "var_k_total", row, from_=0, to=50,
                            tooltip=tooltips["K (k_total)"])
            row += 1
        if mode in ["probability", "at_least"]:
            self.add_slider("M (успешных)", "var_n_success", row, from_=0, to=50,
                            tooltip=tooltips["M (n_success)"])
            row += 1
        if mode == "probability":
            self.add_slider("k (успешных в выборке)", "var_k_success", row, from_=0, to=20,
                            tooltip=tooltips["k (k_success)"])
            row += 1
        if mode == "at_least":
            self.add_slider("k_min (минимум)", "var_min_success", row, from_=0, to=20,
                            tooltip=tooltips["k_min"])
            row += 1
        if mode == "fact":
            self.add_slider("n (число)", "var_n_total", row, from_=0, to=20,
                            tooltip=tooltips["n (факториал)"])
            row += 1
        if mode == "comb_rep":
            self.add_slider("k (выборка)", "var_k_total", row, from_=0, to=20,
                            tooltip=tooltips["k (сочетания)"])
            row += 1
        if mode == "perm_rep":
            lbl = tk.Label(self.input_frame, text="Количества (через запятую):",
                           font=("Segoe UI", 8), bg='#ffffff', fg='#2c3e50')
            lbl.grid(row=row, column=0, sticky=tk.W, padx=3, pady=3)
            entry = tk.Entry(self.input_frame, textvariable=self.var_counts,
                             font=("Segoe UI", 9), bg='white', fg='#2c3e50',
                             relief=tk.SUNKEN, bd=1, width=12)
            entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)
            self.entries['counts'] = entry
            ToolTip(entry, tooltips["Количества (через запятую)"])
            row += 1

        self.input_frame.columnconfigure(0, weight=0)
        self.input_frame.columnconfigure(1, weight=1)

        self.after_id = None

    def add_slider(self, label, var_name, row, from_, to, tooltip=""):
        lbl = tk.Label(self.input_frame, text=label, font=("Segoe UI", 8),
                       bg='#ffffff', fg='#2c3e50')
        lbl.grid(row=row, column=0, sticky=tk.W, padx=3, pady=2)
        var = getattr(self, var_name)
        slider = tk.Scale(self.input_frame, from_=from_, to=to, orient=tk.HORIZONTAL,
                          variable=var, length=120, bg='#ffffff', highlightthickness=0,
                          command=self.on_slider_change)
        slider.grid(row=row, column=1, sticky=tk.W, padx=3, pady=2)
        self.sliders[var_name] = slider
        if tooltip:
            ToolTip(slider, tooltip)

    def on_slider_change(self, event=None):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.after_id = self.root.after(300, self.auto_calculate)

    def auto_calculate(self):
        self.after_id = None
        self.calculate()

    def get_int_var(self, var, name):
        try:
            return var.get()
        except:
            messagebox.showerror("Ошибка", f"Некорректное значение {name}")
            return None

    def get_counts_list(self):
        try:
            s = self.var_counts.get().strip()
            if not s:
                return []
            return [int(x.strip()) for x in s.split(',') if x.strip()]
        except:
            return None

    def calculate(self):
        mode = self.mode_var.get()
        self.current_mode = mode
        self.result_text.delete(1.0, tk.END)

        n_total = self.get_int_var(self.var_n_total, "N") if hasattr(self, 'var_n_total') else None
        k_total = self.get_int_var(self.var_k_total, "K") if hasattr(self, 'var_k_total') else None
        n_success = self.get_int_var(self.var_n_success, "M") if hasattr(self, 'var_n_success') else None
        k_success = self.get_int_var(self.var_k_success, "k") if hasattr(self, 'var_k_success') else None
        min_success = self.get_int_var(self.var_min_success, "k_min") if hasattr(self, 'var_min_success') else None

        try:
            result_str = ""
            dist = None

            if mode == "probability":
                if None in (n_total, k_total, n_success, k_success):
                    return
                if k_total > n_total:
                    self.result_text.insert(tk.END, "❌ Ошибка: K > N\n")
                    return
                p = probability_choose(n_total, k_total, n_success, k_success)
                self.show_prob_result(p, f"ровно {k_success} успешных")
                dist = get_full_distribution(n_total, k_total, n_success)

            elif mode == "at_least":
                if None in (n_total, k_total, n_success, min_success):
                    return
                if k_total > n_total:
                    self.result_text.insert(tk.END, "❌ Ошибка: K > N\n")
                    return
                p = probability_at_least(n_total, k_total, n_success, min_success)
                self.show_prob_result(p, f"как минимум {min_success} успешных")
                dist = get_full_distribution(n_total, k_total, n_success)

            elif mode == "comb":
                if None in (n_total, k_total):
                    return
                if k_total > n_total:
                    self.result_text.insert(tk.END, "❌ Ошибка: k > n\n")
                    return
                res = comb(n_total, k_total)
                result_str = f"🔹 C({n_total}, {k_total}) = {res:,}\n≈ {res:.3e}"

            elif mode == "perm":
                if None in (n_total, k_total):
                    return
                if k_total > n_total:
                    self.result_text.insert(tk.END, "❌ Ошибка: k > n\n")
                    return
                res = perm(n_total, k_total)
                result_str = f"🔹 A({n_total}, {k_total}) = {res:,}\n≈ {res:.3e}"

            elif mode == "fact":
                if n_total is None:
                    return
                res = fact(n_total)
                result_str = f"🔹 {n_total}! = {res:,}\n≈ {res:.3e}"

            elif mode == "comb_rep":
                if None in (n_total, k_total):
                    return
                res = comb_with_repetition(n_total, k_total)
                result_str = f"🔹 C({n_total}+{k_total}-1, {k_total}) = {res:,}\n≈ {res:.3e}"

            elif mode == "perm_rep":
                counts = self.get_counts_list()
                if counts is None:
                    messagebox.showerror("Ошибка", "Введите корректные количества через запятую")
                    return
                if not counts:
                    messagebox.showerror("Ошибка", "Список количеств не может быть пустым")
                    return
                n_total = sum(counts)
                res = perm_with_repetition(n_total, counts)
                result_str = f"🔹 Перестановки с повторениями: {res:,}\n≈ {res:.3e}"

            if result_str:
                self.result_text.insert(tk.END, result_str)

            self.current_distribution = dist
            if dist is not None and len(dist) > 0:
                self.plot_distribution()

        except Exception as e:
            messagebox.showerror("Ошибка", f"При вычислении произошла ошибка:\n{str(e)}")

    def show_prob_result(self, p, description):
        self.result_text.tag_configure('header', foreground='#2980b9', font=('Segoe UI', 10, 'bold'))
        self.result_text.tag_configure('value', foreground='#2c3e50', font=('Courier New', 9))
        self.result_text.tag_configure('zero', foreground='#e74c3c', font=('Segoe UI', 10, 'bold'))
        self.result_text.tag_configure('one', foreground='#27ae60', font=('Segoe UI', 10, 'bold'))

        if p == 0:
            self.result_text.insert(tk.END, f"⚠️ Вероятность = 0 (невозможное событие)\n", 'zero')
        elif p == 1:
            self.result_text.insert(tk.END, f"✅ Вероятность = 1 (достоверное событие)\n", 'one')
        else:
            self.result_text.insert(tk.END, f"🎯 Вероятность {description}:\n", 'header')
            self.result_text.insert(tk.END, f"   P = {p:.10f}\n", 'value')
            self.result_text.insert(tk.END, f"   P = {p*100:.4f}%\n", 'value')
            if p < 1 and p > 0:
                self.result_text.insert(tk.END, f"   ≈ 1/{round(1/p):,} (примерно 1 к {round(1/p):,})\n", 'value')

    def plot_distribution(self):
        if self.current_distribution is None or not self.current_distribution:
            self.clear_plot()
            self.ax.text(0.5, 0.5, "Нет данных для построения\n(все вероятности равны 0)",
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='white')
            self.canvas.draw()
            return

        self.ax.clear()
        x = sorted(self.current_distribution.keys())
        y = [self.current_distribution[k] for k in x]

        if self.cdf_var.get():
            cum = 0
            cdf_y = []
            for val in y:
                cum += val
                cdf_y.append(cum)
            self.ax.step(x, cdf_y, where='mid', color='#ff9999', linewidth=2, label='CDF')
            self.ax.fill_between(x, 0, cdf_y, step='mid', alpha=0.3, color='#ff9999')
            self.ax.set_ylabel("Накопленная вероятность", fontsize=10, color='white')
            self.ax.set_title("📊 Кумулятивная функция распределения (CDF)", fontsize=12, color='white')
        else:
            colors = ['#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6']
            bars = self.ax.bar(x, y, color=colors[:len(x)], edgecolor='white', alpha=0.8, width=0.6)
            for bar, val in zip(bars, y):
                height = bar.get_height()
                self.ax.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                            f'{val:.3f}', ha='center', va='bottom', fontsize=9, color='white')
            self.ax.set_ylabel("Вероятность", fontsize=10, color='white')
            self.ax.set_title("📊 Распределение вероятностей (PMF)", fontsize=12, color='white')

        self.ax.set_facecolor('#2c3e50')
        self.ax.set_xlabel("Число успехов (k)", fontsize=10, color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3, color='white')
        self.ax.set_xticks(x)
        if len(x) > 1:
            self.ax.set_xlim(min(x)-0.5, max(x)+0.5)
        self.canvas.draw()

    def on_cdf_toggle(self):
        self.plot_distribution()

    def clear_plot(self):
        self.ax.clear()
        self.ax.set_facecolor('#2c3e50')
        self.ax.set_xlabel("Число успехов (k)", fontsize=10, color='white')
        self.ax.set_ylabel("Вероятность", fontsize=10, color='white')
        self.ax.set_title("📊 Распределение вероятностей", fontsize=12, color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.3, color='white')
        self.canvas.draw()

    def update_inputs(self):
        self.build_inputs()
        self.result_text.delete(1.0, tk.END)
        self.clear_plot()
        self.current_distribution = None

    # ----- Экспорт и сохранение -----
    def export_result(self):
        content = self.result_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showinfo("Информация", "Нет результатов для экспорта")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
                if self.current_distribution:
                    f.write("\n\nПолное распределение:\n")
                    for k, p in sorted(self.current_distribution.items()):
                        f.write(f"k={k}: {p:.10f}\n")
            messagebox.showinfo("Успех", "Результат сохранён")

    def save_plot(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png",
                                                filetypes=[("PNG", "*.png"), ("SVG", "*.svg"), ("All files", "*.*")])
        if filename:
            self.figure.savefig(filename, dpi=150, bbox_inches='tight')
            messagebox.showinfo("Успех", "График сохранён")

    # ----- Примеры -----
    def load_example(self, name):
        examples = {
            'aces': {'mode':'probability', 'N':52, 'K':5, 'M':4, 'k':2},
            'defective': {'mode':'probability', 'N':10, 'K':4, 'M':3, 'k':2},
            'lottery': {'mode':'probability', 'N':49, 'K':6, 'M':6, 'k':6},
        }
        ex = examples.get(name)
        if not ex:
            return
        self.mode_var.set(ex['mode'])
        self.var_n_total.set(ex['N'])
        self.var_k_total.set(ex['K'])
        self.var_n_success.set(ex['M'])
        self.var_k_success.set(ex['k'])
        self.update_inputs()
        self.calculate()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = CombinatoricsApp(root)
    root.mainloop()
