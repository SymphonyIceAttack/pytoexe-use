import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

# ------------------------------------------------------------
# 1. Функции расчёта вероятностей
# ------------------------------------------------------------

def prob_geometric_catch(s, d):
    if s < d:
        return 1 - (s / d) ** 2
    else:
        return 0.0

def prob_net_hold(m, v_ms, sigma, d_net, S_contact, eps):
    F_max=sigma*d_net*S_contact
    s_deform = eps*0.5
    W_net = F_max*s_deform
    E_kin = 0.5 * m * v_ms ** 2
    if E_kin <= 0: return 1.0
    ratio = W_net/E_kin 
    return 1/(1 + math.exp(-5*(ratio-1.0)))

def prob_initiation_by_pressure(m_VV, R):
    P_pik = 0.084 + 0.27 * ((m_VV ** (1/3)) / R) ** 2 + 0.7 * ((m_VV ** (1/3)) / R) ** 3
    P_crit = 0.45
    beta = 3.0
    return math.exp(-(P_pik / P_crit) ** beta)

def pressure_after_gabion(m_VV, R, H):
    P_pik = 0.084 + 0.27 * ((m_VV ** (1/3)) / R) ** 2 + 0.7 * ((m_VV ** (1/3)) / R) ** 3
    k = 0.035 * (m_VV ** (1/3)) + 0.42
    P_udar = P_pik * (0.15 + 0.85 * math.exp(-k * (H / R)))
    return P_udar

def prob_pressure_survival(P_after, P_crit=0.3, beta=4.0):
    if P_after <= 0:
        return 1.0
    return 1 - math.exp(-(P_crit / P_after) ** beta)

def prob_non_penetration(t_gab, m_oskl, v_oskl, angle_deg, S_oskl, material):
    if material == 'gravel':
        K = 1.5e8
    elif material == 'sand':
        K = 1.2e8
    else:
        K = 0.8e8
    angle_rad = math.radians(angle_deg)
    t_req = (m_oskl * v_oskl ** 2 * math.sin(angle_rad)) / (2 * K * S_oskl)
    if t_req <= 0:
        return 1.0
    beta = 2.0
    return math.exp(-(t_req / t_gab) ** beta)

def prob_gabion_protection(m_VV, R, H, t_gab, material, P_crit_object=0.3,
                           m_oskl=0.002, v_oskl=1800, angle_deg=90, S_oskl=1e-4):
    P_after = pressure_after_gabion(m_VV, R, H)
    P_pressure = prob_pressure_survival(P_after, P_crit=P_crit_object)
    P_non_pen = prob_non_penetration(t_gab, m_oskl, v_oskl, angle_deg, S_oskl, material)
    return P_pressure * P_non_pen

def compute_combination(bpla, net, gab, R_gab=3.0, P_crit_object=0.3):
    m_bpla = bpla[1]
    v_bpla_ms = bpla[2] / 3.6
    wingspan = bpla[3]
    m_VV = bpla[4]
    m_oskl = bpla[5]
    v_oskl = bpla[6]
    S_oskl = bpla[7]

    cell_size = net[1]
    d_net = net[2]
    sigma = net[3]
    eps = net[4]
    S_contact = net[5]

    H_gab = gab[1]
    t_gab = gab[2]
    material = gab[3]

    
    P_geom = prob_geometric_catch(cell_size, wingspan)
    P_hold = prob_net_hold(m_bpla, v_bpla_ms, sigma, d_net, S_contact, eps)
    P_init = prob_initiation_by_pressure(m_VV, R=5.0)
    P_set = P_geom * P_hold + (1 - P_geom * P_hold) * P_init

    P_gab = prob_gabion_protection(m_VV, R_gab, H_gab, t_gab, material,
                                   P_crit_object=P_crit_object,
                                   m_oskl=m_oskl, v_oskl=v_oskl,
                                   angle_deg=90, S_oskl=S_oskl)

    E_pass = P_set + (1 - P_set) * P_gab
    return E_pass

def compute_combination_with_mass(bpla, net, gab, m_VV, R_gab=3.0, P_crit_object=0.3):
    bpla_copy = bpla.copy()
    bpla_copy[4] = m_VV
    return compute_combination(bpla_copy, net, gab, R_gab, P_crit_object)

# ------------------------------------------------------------
# 2. Данные
# ------------------------------------------------------------
Bpla_data = [
    ["Лютий",        300,  41.7, 6.7, 75,   0.002, 1800, 1e-4],
    ["UJ-22 Airborne",85,  43.0, 4.4, 15,   0.002, 1800, 1e-4],
    ["UJ-26 Beaver", 150, 41.7, 3.5, 20,   0.002, 1800, 1e-4],
    ["Hero 900",      97, 33.3, 4.5, 20,   0.002, 1800, 1e-4],
    ["FPV-дрон",      1.5, 25.0, 0.3, 0.5, 0.002, 1800, 1e-4],
    ["СИЧ",           8.5, 22.2, 3.0, 4.0, 0.002, 1800, 1e-4]
]

Net_data = [
    ["Рабица",   0.045, 0.002,  3.0e8, 0.010,0.05],
    ["Дарвин",   0.118, 0.004,  2.5e8, 0.100, 0.15],  # название, размер ячейки, толщина нити, предел прочности, крит. деформация, площадь контакта
    ["Ловушка",  0.050, 0.003,  4.0e8, 0.012, 0.04],
    ["3D Забор", 0.035, 0.0025, 5.0e8, 0.015, 0.06],
    ["Режущая",  0.091, 0.0015, 2e5,   0.008, 0.03]
]

Gabion_data = [
    ["Габион h=0.5м", 0.5, 1.0, "gravel"],
    ["Габион h=1м",   1.0, 1.5, "sand"],
    ["Габион h=2м",   2.0, 2.0, "clay"],
    ["Габион h=3м",   3.0, 3.0, "gravel"]
]

# ------------------------------------------------------------
# 3. Класс приложения
# ------------------------------------------------------------
class ProtectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчёт эффективности габионной защиты от БпЛА")
        self.root.geometry("950x720")
        self.root.resizable(True, True)

        # Переменные ТОЛЬКО для числовых полей
        self.R_gab_var = tk.DoubleVar(value=3.0)      # расстояние до габиона
        self.R_net_var = tk.DoubleVar(value=5.0)      # расстояние от сети до объекта (НОВОЕ)
        self.P_crit_var = tk.DoubleVar(value=0.3)     # критическое давление объекта
        self.angle_var = tk.DoubleVar(value=90.0)     # угол встречи осколка

        self.comparison_list = []  # список кортежей для графика

        self.create_widgets()
        self.plot_default()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(main_frame, text="Выбор параметров", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # БпЛА
        ttk.Label(left_frame, text="БпЛА:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.bpla_combo = ttk.Combobox(left_frame, values=[b[0] for b in Bpla_data], state="readonly", width=25)
        self.bpla_combo.grid(row=0, column=1, pady=2)
        self.bpla_combo.current(0)
        self.bpla_combo.bind("<<ComboboxSelected>>", self.on_param_change)

        # Сетка
        ttk.Label(left_frame, text="Защитная сетка:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.net_combo = ttk.Combobox(left_frame, values=[n[0] for n in Net_data], state="readonly", width=25)
        self.net_combo.grid(row=1, column=1, pady=2)
        self.net_combo.current(0)
        self.net_combo.bind("<<ComboboxSelected>>", self.on_param_change)

        # Габион
        ttk.Label(left_frame, text="Габион:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.gab_combo = ttk.Combobox(left_frame, values=[g[0] for g in Gabion_data], state="readonly", width=25)
        self.gab_combo.grid(row=2, column=1, pady=2)
        self.gab_combo.current(0)
        self.gab_combo.bind("<<ComboboxSelected>>", self.on_param_change)

        ttk.Separator(left_frame, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        # Числовые параметры
        ttk.Label(left_frame, text="Расстояние до габиона R_габ (м):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(left_frame, textvariable=self.R_gab_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=2)

        ttk.Label(left_frame, text="Расстояние от сети до объекта R_сеть (м):").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Entry(left_frame, textvariable=self.R_net_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=2)

        ttk.Label(left_frame, text="Критическое давление P_crit (МПа):").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Entry(left_frame, textvariable=self.P_crit_var, width=10).grid(row=6, column=1, sticky=tk.W, pady=2)

        ttk.Label(left_frame, text="Угол встречи осколка (град):").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Entry(left_frame, textvariable=self.angle_var, width=10).grid(row=7, column=1, sticky=tk.W, pady=2)

        self.calc_btn = ttk.Button(left_frame, text="Рассчитать вероятность", command=self.calculate)
        self.calc_btn.grid(row=8, column=0, columnspan=2, pady=15)

        self.result_label = ttk.Label(left_frame, text="Вероятность защиты: ---", font=('Arial', 12, 'bold'))
        self.result_label.grid(row=9, column=0, columnspan=2, pady=5)

        self.add_btn = ttk.Button(left_frame, text="Добавить кривую на график", command=self.add_to_plot)
        self.add_btn.grid(row=10, column=0, columnspan=2, pady=5)

        self.clear_btn = ttk.Button(left_frame, text="Очистить график", command=self.clear_plot)
        self.clear_btn.grid(row=11, column=0, columnspan=2, pady=5)

        right_frame = ttk.LabelFrame(main_frame, text="График зависимости от массы ВВ", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.figure = plt.Figure(figsize=(7,5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def on_param_change(self, event=None):
        self.result_label.config(text="Вероятность защиты: ---")
        self.status_var.set("Параметры изменены, нажмите 'Рассчитать вероятность'")

    def calculate(self):
        try:
            bpla_idx = self.bpla_combo.current()
            net_idx = self.net_combo.current()
            gab_idx = self.gab_combo.current()
            R_gab = float(self.R_gab_var.get())
            R_net = float(self.R_net_var.get())  # Новое поле
            P_crit = float(self.P_crit_var.get())
            angle = float(self.angle_var.get())

            if -1 in (bpla_idx, net_idx, gab_idx):
                messagebox.showwarning("Внимание", "Пожалуйста, выберите все параметры из списков.")
                return

            bpla = Bpla_data[bpla_idx]
            net = Net_data[net_idx]
            gab = Gabion_data[gab_idx]

            def prob_non_pen_local(t_gab, m_oskl, v_oskl, angle_deg, S_oskl, material):
                if material == 'gravel': K = 1.5e8
                elif material == 'sand': K = 1.2e8
                else: K = 0.8e8
                angle_rad = math.radians(angle_deg)
                t_req = (m_oskl * v_oskl ** 2 * math.sin(angle_rad)) / (2 * K * S_oskl)
                if t_req <= 0: return 1.0
                return math.exp(-(t_req / t_gab) ** 2.0)

            def prob_gabion_local(m_VV, R, H, t_gab, material, P_crit_object, m_oskl, v_oskl, angle_deg, S_oskl):
                P_after = pressure_after_gabion(m_VV, R, H)
                P_pressure = prob_pressure_survival(P_after, P_crit=P_crit_object)
                P_non_pen = prob_non_pen_local(t_gab, m_oskl, v_oskl, angle_deg, S_oskl, material)
                return P_pressure * P_non_pen

            m_bpla = bpla[1]; v_bpla_ms = bpla[2] / 3.6; wingspan = bpla[3]; m_VV = bpla[4]
            m_oskl = bpla[5]; v_oskl = bpla[6]; S_oskl = bpla[7]
            cell_size = net[1]; d_net = net[2]; sigma = net[3]; eps = net[4]; S_contact = net[5]
            H_gab = gab[1]; t_gab = gab[2]; material = gab[3]

            P_geom = prob_geometric_catch(cell_size, wingspan)
            P_hold = prob_net_hold(m_bpla, v_bpla_ms, sigma, d_net, S_contact, eps)
            P_init = prob_initiation_by_pressure(m_VV, R=R_net)
            P_set = P_geom * P_hold + (1 - P_geom * P_hold) * P_init

            P_gab = prob_gabion_local(m_VV, R_gab, H_gab, t_gab, material, P_crit, m_oskl, v_oskl, angle, S_oskl)
            prob = P_set + (1 - P_set) * P_gab

            self.result_label.config(text=f"Вероятность защиты: {prob:.4f} ({prob*100:.2f}%)")
            self.status_var.set(f"Расчёт выполнен. P = {prob:.4f}")
            
        except ValueError as ve:
            messagebox.showerror("Ошибка ввода", f"В числовых полях допустимы только числа.\n{ve}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить расчёт:\n{str(e)}")
            self.status_var.set("Ошибка расчёта")

    def add_to_plot(self):
        try:
            bpla_idx = self.bpla_combo.current()
            net_idx = self.net_combo.current()
            gab_idx = self.gab_combo.current()
            R_gab = float(self.R_gab_var.get())
            R_net = float(self.R_net_var.get())  # Новое поле
            P_crit = float(self.P_crit_var.get())
            angle = float(self.angle_var.get())

            if -1 in (bpla_idx, net_idx, gab_idx):
                messagebox.showwarning("Внимание", "Пожалуйста, выберите все параметры из списков.")
                return

            bpla = Bpla_data[bpla_idx]
            net = Net_data[net_idx]
            gab = Gabion_data[gab_idx]
            label = f"{bpla[0]} | {net[0]} + {gab[0]}"
            m_vv_selected = bpla[4]

            # Сохраняем R_net в список сравнения
            self.comparison_list.append((bpla_idx, net_idx, gab_idx, label, R_gab, R_net, P_crit, angle, m_vv_selected))
            self.redraw_plot()
            self.status_var.set(f"Добавлена кривая: {label}")
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Проверьте числовые поля перед добавлением на график.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить кривую:\n{str(e)}")

    def redraw_plot(self):
        self.ax.clear()
        m_vv_range = np.linspace(0.5, 100, 200)

        for item in self.comparison_list:
            bpla_idx, net_idx, gab_idx, label, R_gab, R_net, P_crit, angle, m_vv_selected = item
            bpla = Bpla_data[bpla_idx]
            net = Net_data[net_idx]
            gab = Gabion_data[gab_idx]

            def prob_for_mass(m_VV):
                bpla_copy = bpla.copy()
                bpla_copy[4] = m_VV
                
                m_bpla = bpla_copy[1]; v_bpla_ms = bpla_copy[2] / 3.6; wingspan = bpla_copy[3]
                m_oskl = bpla_copy[5]; v_oskl = bpla_copy[6]; S_oskl = bpla_copy[7]
                cell_size = net[1]; d_net = net[2]; sigma = net[3]; eps = net[4]; S_contact = net[5]
                H_gab = gab[1]; t_gab = gab[2]; material = gab[3]

                P_geom = prob_geometric_catch(cell_size, wingspan)
                P_hold = prob_net_hold(m_bpla, v_bpla_ms, sigma, d_net, S_contact, eps)
                # 🔹 Используем R_net из текущей комбинации
                P_init = prob_initiation_by_pressure(m_VV, R=R_net)
                P_set = P_geom * P_hold + (1 - P_geom * P_hold) * P_init

                if material == 'gravel': K = 1.5e8
                elif material == 'sand': K = 1.2e8
                else: K = 0.8e8
                angle_rad = math.radians(angle)
                t_req = (m_oskl * v_oskl ** 2 * math.sin(angle_rad)) / (2 * K * S_oskl)
                P_non_pen = math.exp(-(t_req / t_gab) ** 2.0) if t_req > 0 else 1.0
                
                P_after = pressure_after_gabion(m_VV, R_gab, H_gab)
                P_pressure = prob_pressure_survival(P_after, P_crit=P_crit)
                
                return P_set + (1 - P_set) * (P_pressure * P_non_pen)

            y_vals = [prob_for_mass(m) for m in m_vv_range]
            self.ax.plot(m_vv_range, y_vals, linewidth=2, label=label)
            
            if 0.5 <= m_vv_selected <= 100:
                self.ax.axvline(x=m_vv_selected, color='gray', linestyle='--', linewidth=1, alpha=0.7)
                self.ax.text(m_vv_selected + 1, 0.95, f'● {bpla[0]}\n(m={m_vv_selected} кг)', 
                            fontsize=8, color='gray', va='top', ha='left',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

        self.ax.set_xlabel('Масса ВВ БпЛА, кг', fontsize=10)
        self.ax.set_ylabel('Вероятность защиты', fontsize=10)
        self.ax.set_title('Зависимость эффективности от массы заряда', fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.legend(loc='lower right', fontsize=8)
        self.ax.set_ylim(0, 1.05)
        self.ax.set_xlim(0.5, 100)
        self.canvas.draw()

    def clear_plot(self):
        self.comparison_list.clear()
        self.plot_default()
        self.status_var.set("График очищен")

    def plot_default(self):
        self.ax.clear()
        self.ax.set_xlabel('Масса ВВ БпЛА, кг', fontsize=10)
        self.ax.set_ylabel('Вероятность защиты', fontsize=10)
        self.ax.set_title('Зависимость эффективности от массы заряда', fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_ylim(0, 1.05)
        self.ax.set_xlim(0.5, 100)
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProtectionApp(root)
    root.mainloop()