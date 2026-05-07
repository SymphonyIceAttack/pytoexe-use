import customtkinter as ctk
import tkinter as tk
import random
import math
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Program(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Интегральная функция распределения")
        self.geometry("1000x700")

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left_panel = ctk.CTkFrame(self, width=320)
        left_panel.grid(row=0, column=0, sticky="ns", padx=10, pady=10)
        left_panel.grid_propagate(False)

        param_frame = ctk.CTkFrame(left_panel)
        param_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(param_frame, text="Количество значений:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.n_entry = ctk.CTkEntry(param_frame, width=80)
        self.n_entry.grid(row=0, column=1, padx=5, pady=2)
        self.n_entry.insert(0, "5")

        ctk.CTkLabel(param_frame, text="Мин. значение x:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        self.min_entry = ctk.CTkEntry(param_frame, width=80)
        self.min_entry.grid(row=1, column=1, padx=5, pady=2)
        self.min_entry.insert(0, "1")

        ctk.CTkLabel(param_frame, text="Макс. значение x:").grid(row=2, column=0, padx=5, pady=2, sticky="e")
        self.max_entry = ctk.CTkEntry(param_frame, width=80)
        self.max_entry.grid(row=2, column=1, padx=5, pady=2)
        self.max_entry.insert(0, "10")

        self.generate_btn = ctk.CTkButton(param_frame, text="Сгенерировать", command=self.generate)
        self.generate_btn.grid(row=0, column=2, rowspan=3, padx=10)


        self.dist_text = ctk.CTkTextbox(left_panel, width=300)
        self.dist_text.pack(fill="both", expand=True, padx=5, pady=5)

        calc_frame = ctk.CTkFrame(left_panel)
        calc_frame.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(calc_frame, text="x =").pack(side="left", padx=5)
        self.x_entry = ctk.CTkEntry(calc_frame, width=100)
        self.x_entry.pack(side="left", padx=5)
        self.calc_btn = ctk.CTkButton(calc_frame, text="Вычислить F(x)", command=self.calc_F)
        self.calc_btn.pack(side="left", padx=5)

        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=0)
        right_panel.grid_columnconfigure(0, weight=1)


        self.graph_frame = ctk.CTkFrame(right_panel)
        self.graph_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5,2))


        stats_frame = ctk.CTkFrame(right_panel)
        stats_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(2,5))

        self.stats_label = ctk.CTkLabel(stats_frame, text="M[X] = -,   D[X] = -,   σ = -", font=ctk.CTkFont(size=16))
        self.stats_label.pack(side="left", padx=5)

        self.result_label = ctk.CTkLabel(stats_frame, text="", font=ctk.CTkFont(size=16))
        self.result_label.pack(side="right", padx=10)

        # Данные распределения
        self.x_unique = []
        self.probs = []
        self.fig = None
        self.ax = None
        self.canvas = None
        self.scatter_point = None

        # Инициализация пустого графика
        self.init_plot()

    def init_plot(self):
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Интегральная функция распределения F(x)")
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("F(x)")
        self.ax.grid(alpha=0.3)
        self.ax.set_xlim(-1, 11)
        self.ax.set_ylim(-0.05, 1.1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()

    def generate(self):
        n = int(self.n_entry.get())
        x_min = int(self.min_entry.get())
        x_max = int(self.max_entry.get())

        # Генерация случайных значений и вероятностей
        raw_x = [random.randint(x_min, x_max) for _ in range(n)]
        weights = [random.random() for _ in range(n)]
        total_w = sum(weights)
        raw_p = [w / total_w for w in weights]

        # Группировка одинаковых x
        dist_dict = {}
        for x, p in zip(raw_x, raw_p):
            dist_dict[x] = dist_dict.get(x, 0.0) + p

        sorted_items = sorted(dist_dict.items())
        self.x_unique = [item[0] for item in sorted_items]
        probs = [item[1] for item in sorted_items]

        # Накопленные вероятности
        self.probs = []
        cumulative = 0.0
        for p in probs:
            cumulative += p
            self.probs.append(cumulative)

        # Таблица в левой панели
        self.dist_text.delete("1.0", "end")
        table = " Значение x   |   P(X=x)   |   F(x)\n"
        table += "-"*40 + "\n"
        for x, p, fx in zip(self.x_unique, probs, self.probs):
            table += f" {x:>10}    |   {p:.4f}    |   {fx:.4f}\n"
        self.dist_text.insert("1.0", table)

        # Характеристики
        M = sum(x * p for x, p in zip(self.x_unique, probs))
        M2 = sum(x * x * p for x, p in zip(self.x_unique, probs))
        D = M2 - M*M
        sigma = math.sqrt(D)
        self.stats_label.configure(text=f"M[X] = {M:.4f}   D[X] = {D:.4f}   σ = {sigma:.4f}")
        self.result_label.configure(text="")

        # Обновляем график
        self.update_plot()

    def update_plot(self):
        self.ax.clear()

        if not self.x_unique:
            self.canvas.draw()
            return

        x_min, x_max = self.x_unique[0], self.x_unique[-1]

        # Левая граница
        self.ax.hlines(y=0, xmin=x_min-1, xmax=x_min, colors='gray', linestyles='--')
        # Правая граница
        self.ax.hlines(y=1, xmin=x_max, xmax=x_max+1, colors='gray', linestyles='--')

        # Ступенчатая функция
        step_x = [x_min] + self.x_unique + [x_max + 1]
        step_y = [0] + self.probs + [1]
        self.ax.step(step_x, step_y, where='post', color='blue', linewidth=2, label='F(x)')

        # Точки скачков
        self.ax.scatter(self.x_unique, [0] + self.probs[:-1],
                        color='white', edgecolor='blue', s=50, zorder=5)
        self.ax.scatter(self.x_unique, self.probs,
                        color='blue', s=40, zorder=5)

        # Оформление
        self.ax.set_title("Интегральная функция распределения F(x)")
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("F(x)")
        self.ax.grid(alpha=0.3)
        self.ax.set_xlim(x_min-1, x_max+1)
        self.ax.set_ylim(-0.05, 1.1)
        self.ax.legend()

        self.scatter_point = None
        self.canvas.draw()

    def calc_F(self):
        if not self.x_unique:
            self.result_label.configure(text="Сначала сгенерируйте распределение!!!!")
            return
        try:
            x = float(self.x_entry.get())
        except ValueError:
            self.result_label.configure(text="Введите число!")
            return

        probs = [self.probs[0]]
        for i in range(1, len(self.probs)):
            probs.append(self.probs[i] - self.probs[i-1])

        F_val = 0.0
        for xi, p in zip(self.x_unique, probs):
            if xi <= x:
                F_val += p
            else:
                break

        self.result_label.configure(text=f"F({x}) = {F_val:.4f}")

        if self.scatter_point is not None:
            self.scatter_point.remove()
            self.scatter_point = None
        self.scatter_point = self.ax.scatter(x, F_val, color='red', s=100,
                                             zorder=10, edgecolors='darkred')
        self.canvas.draw()


if __name__ == "__main__":
    app = Program()
    app.mainloop()
