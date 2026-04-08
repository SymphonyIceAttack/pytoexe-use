import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import time

# ------------------------------------------------------------
#  Функции для работы с профилями
# ------------------------------------------------------------

def generate_naca_profile(t, num_points=100):
    """Генерация симметричного профиля NACA 00xx по толщине t."""
    x_upper = np.linspace(0, 1, num_points//2)
    yt = 5 * t * (0.2969 * np.sqrt(x_upper) - 0.1260 * x_upper - 0.3516 * x_upper**2 +
                  0.2843 * x_upper**3 - 0.1015 * x_upper**4)
    y_upper = yt
    y_lower = -yt
    x_upper_rev = x_upper[::-1]
    y_upper_rev = y_upper[::-1]
    x_lower = x_upper
    y_lower = y_lower
    x = np.concatenate([x_upper_rev, x_lower[1:]])
    y = np.concatenate([y_upper_rev, y_lower[1:]])
    return x, y

def build_contour_from_parts(upper_points, lower_points):
    """
    Строит замкнутый контур (x,y) из двух отдельных поверхностей:
    верхняя (x от 0 до 1, y > 0) и нижняя (x от 0 до 1, y < 0 или меньше верхней).
    Возвращает массивы, пригодные для split_upper_lower.
    """
    # Сортировка по x (на всякий случай)
    upper = sorted(upper_points, key=lambda p: p[0])
    lower = sorted(lower_points, key=lambda p: p[0])
    x_up = np.array([p[0] for p in upper])
    y_up = np.array([p[1] for p in upper])
    x_low = np.array([p[0] for p in lower])
    y_low = np.array([p[1] for p in lower])

    # Формируем замкнутый контур: от x=1 до x=0 по верхней, затем от x=0 до x=1 по нижней
    x_contour = np.concatenate([x_up[::-1], x_low[1:]])
    y_contour = np.concatenate([y_up[::-1], y_low[1:]])
    return x_contour, y_contour

def parse_coordinate_block(block_str):
    """Преобразует многострочную строку с двумя числами в строке в список пар (x,y)."""
    lines = block_str.strip().split('\n')
    points = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            x = float(parts[0])
            y = float(parts[1])
            points.append((x, y))
    return points

# ------------------------------------------------------------
#  Данные для вариантов (заданные координаты)
# ------------------------------------------------------------

# Вариант 2
variant2_upper_str = """
0.000000  0.000000
0.012500  0.019300
0.025000  0.031700
0.050000  0.051300
0.075000  0.066400
0.100000  0.078000
0.150000  0.093400
0.200000  0.101300
0.250000  0.104400
0.300000  0.104800
0.400000  0.100200
0.500000  0.090500
0.600000  0.077100
0.700000  0.061000
0.800000  0.042800
0.900000  0.022900
0.950000  0.012400
1.000000  0.001600
"""
variant2_lower_str = """
0.000000  0.000000
0.012500 -0.005000
0.025000 -0.004200
0.050000 -0.001000
0.075000  0.002800
0.100000  0.006800
0.150000  0.014500
0.200000  0.021700
0.250000  0.028200
0.300000  0.033300
0.400000  0.038500
0.500000  0.038600
0.600000  0.035000
0.700000  0.028600
0.800000  0.020200
0.900000  0.010000
0.950000  0.004400
1.000000 -0.001600
"""

# Вариант 4
variant4_upper_str = """
0.0000000 0.0000000
0.0005000 0.0017762
0.0010000 0.0026712
0.0020000 0.0039826
0.0040000 0.0059651
0.0080000 0.0093775
0.0120000 0.0126235
0.0200000 0.0165502
0.0300000 0.0201909
0.0400000 0.0243663
0.0500000 0.0283931
0.0600000 0.0316763
0.0800000 0.0368998
0.1000000 0.0414470
0.1200000 0.0451368
0.1400000 0.0481068
0.1600000 0.0505979
0.1800000 0.0527383
0.2000000 0.0545539
0.2200000 0.0560793
0.2400000 0.0573984
0.2600000 0.0586036
0.2800000 0.0597119
0.3000000 0.0606677
0.3200000 0.0614255
0.3400000 0.0619894
0.3600000 0.0623757
0.3800000 0.0626003
0.4000000 0.0626795
0.4200000 0.0626219
0.4400000 0.0624084
0.4600000 0.0620130
0.4800000 0.0614093
0.5000000 0.0605710
0.5200000 0.0594744
0.5400000 0.0581322
0.5600000 0.0565812
0.5800000 0.0548590
0.6000000 0.0530032
0.6200000 0.0510426
0.6400000 0.0489701
0.6600000 0.0467699
0.6800000 0.0444259
0.7000000 0.0419222
0.7200000 0.0392571
0.7400000 0.0364864
0.7600000 0.0336812
0.7800000 0.0309114
0.8000000 0.0282480
0.8200000 0.0257350
0.8400000 0.0233138
0.8600000 0.0209021
0.8800000 0.0184162
0.9000000 0.0157729
0.9200000 0.0129100
0.9400000 0.0098530
0.9600000 0.0066502
0.9700000 0.0050090
0.9800000 0.0033495
0.9900000 0.0016777
1.0000000 0.0000000
"""
variant4_lower_str = """
0.0000000 0.0000000
0.0005000 -0.0027391
0.0010000 -0.0037318
0.0020000 -0.0051549
0.0040000 -0.0070820
0.0080000 -0.0090008
0.0120000 -0.0095219
0.0200000 -0.0101876
0.0300000 -0.0109695
0.0400000 -0.0114902
0.0500000 -0.0119380
0.0600000 -0.0124717
0.0800000 -0.0136395
0.1000000 -0.0146775
0.1200000 -0.0156764
0.1400000 -0.0167361
0.1600000 -0.0179398
0.1800000 -0.0192399
0.2000000 -0.0204561
0.2200000 -0.0214592
0.2400000 -0.0223472
0.2600000 -0.0232692
0.2800000 -0.0242397
0.3000000 -0.0251365
0.3200000 -0.0258576
0.3400000 -0.0264065
0.3600000 -0.0268131
0.3800000 -0.0271073
0.4000000 -0.0273189
0.4200000 -0.0274668
0.4400000 -0.0275250
0.4600000 -0.0274563
0.4800000 -0.0272236
0.5000000 -0.0267894
0.5200000 -0.0261207
0.5400000 -0.0252416
0.5600000 -0.0242160
0.5800000 -0.0231082
0.6000000 -0.0219837
0.6200000 -0.0208931
0.6400000 -0.0198331
0.6600000 -0.0187862
0.6800000 -0.0177353
0.7000000 -0.0166627
0.7200000 -0.0155566
0.7400000 -0.0144264
0.7600000 -0.0132873
0.7800000 -0.0121541
0.8000000 -0.0110418
0.8200000 -0.0099608
0.8400000 -0.0089020
0.8600000 -0.0078516
0.8800000 -0.0067959
0.9000000 -0.0057209
0.9200000 -0.0046164
0.9400000 -0.0034854
0.9600000 -0.0023346
0.9700000 -0.0017538
0.9800000 -0.0011706
0.9900000 -0.0005857
1.0000000 0.0000000
"""

# Вариант 6
variant6_upper_str = """
0.0000000 0.0000000
0.0041977 0.0095700
0.0100356 0.0154241
0.0200350 0.0227665
0.0348482 0.0311300
0.0540182 0.0397400
0.0764527 0.0479203
0.1011350 0.0553181
0.1273392 0.0618114
0.1546283 0.0674128
0.1826904 0.0721660
0.2113082 0.0761239
0.2403358 0.0793401
0.2696742 0.0818597
0.2992332 0.0837195
0.3289599 0.0849515
0.3588182 0.0855796
0.3887731 0.0856308
0.4187877 0.0851351
0.4488457 0.0841175
0.4789282 0.0826078
0.5089862 0.0806341
0.5389917 0.0782224
0.5689247 0.0753936
0.5987790 0.0721627
0.6285808 0.0685028
0.6583750 0.0644109
0.6882508 0.0599010
0.7182678 0.0550003
0.7484503 0.0497218
0.7787921 0.0441214
0.8092952 0.0382822
0.8399634 0.0322472
0.8707898 0.0260833
0.9016322 0.0199055
0.9315834 0.0139837
0.9574376 0.0089976
0.9758121 0.0055268
0.9891618 0.0030357
0.9999979 0.0010000
"""
variant6_lower_str = """
0.0000000 0.0000000
0.0001209 -0.0014656
0.0010059 -0.0040753
0.0027994 -0.0064104
0.0060276 -0.0085090
0.0119707 -0.0105878
0.0227109 -0.0126946
0.0403478 -0.0145033
0.0642490 -0.0156413
0.0918984 -0.0160685
0.1213212 -0.0159319
0.1515756 -0.0154033
0.1822458 -0.0145914
0.2131627 -0.0135661
0.2442524 -0.0123857
0.2754751 -0.0110962
0.3068076 -0.0097325
0.3382381 -0.0083288
0.3697316 -0.0069239
0.4011892 -0.0055351
0.4326007 -0.0041804
0.4639783 -0.0028737
0.4953260 -0.0016220
0.5266438 -0.0004364
0.5579286 0.0006722
0.5891795 0.0016938
0.6203865 0.0026153
0.6515426 0.0034188
0.6826429 0.0040872
0.7136883 0.0045996
0.7446840 0.0049369
0.7756378 0.0050861
0.8065398 0.0050393
0.8373671 0.0047795
0.8681286 0.0042725
0.8989804 0.0034777
0.9298645 0.0023879
0.9565697 0.0012247
0.9753916 0.0002834
0.9889824 -0.0004325
1.0000000 -0.0010000
"""

# Вариант 8 – уже замкнутый контур
variant8_contour_str = """
1.00000  0.00000
0.99645  0.00066
0.98625  0.00282
0.97030  0.00660
0.94932  0.01158
0.92361  0.01723
0.89325  0.02333
0.85854  0.02995
0.82000  0.03705
0.77819  0.04450
0.73369  0.05217
0.68712  0.05988
0.63910  0.06741
0.59028  0.07452
0.54130  0.08087
0.49264  0.08604
0.44460  0.08973
0.39748  0.09175
0.35154  0.09203
0.30704  0.09055
0.26419  0.08742
0.22332  0.08289
0.18486  0.07717
0.14920  0.07039
0.11671  0.06271
0.08772  0.05430
0.06250  0.04532
0.04128  0.03597
0.02427  0.02648
0.01161  0.01710
0.00344  0.00823
0.00002  0.00051
0.00258 -0.00625
0.01115 -0.01296
0.02471 -0.01953
0.04311 -0.02564
0.06616 -0.03113
0.09366 -0.03588
0.12534 -0.03979
0.16091 -0.04281
0.19999 -0.04489
0.24219 -0.04597
0.28702 -0.04602
0.33398 -0.04483
0.38286 -0.04210
0.43379 -0.03799
0.48643 -0.03314
0.54007 -0.02801
0.59395 -0.02289
0.64730 -0.01799
0.69937 -0.01350
0.74940 -0.00954
0.79665 -0.00620
0.84043 -0.00353
0.88005 -0.00156
0.91489 -0.00024
0.94441  0.00051
0.96813  0.00076
0.98561  0.00060
0.99636  0.00021
1.00000  0.00000
"""

# Варианты 10 и 12 (данные одинаковы)
variant10_upper_str = """
0.0000100 0.0004400
0.0001500 0.0022100
0.0004600 0.0040900
0.0013600 0.0070600
0.0048000 0.0141400
0.0136400 0.0255600
0.0267400 0.0374800
0.0439500 0.0495100
0.0651100 0.0612900
0.0900100 0.0725400
0.1184300 0.0830100
0.1500900 0.0924600
0.1846800 0.1007000
0.2218700 0.1075000
0.2612600 0.1126700
0.3024400 0.1159300
0.3451200 0.1169300
0.3892400 0.1153000
0.4350600 0.1110600
0.4825900 0.1047800
0.5313400 0.0970300
0.5807900 0.0882000
0.6303600 0.0786800
0.6793900 0.0688400
0.7272300 0.0590200
0.7731800 0.0495100
0.8165100 0.0405600
0.8565500 0.0323400
0.8926200 0.0249800
0.9241101 0.0185400
0.9504901 0.0130100
0.9712700 0.0082500
0.9865200 0.0040500
0.9964100 0.0010400
1.0000000 0.0000000
"""
variant10_lower_str = """
0.0000100 0.0004400
0.0000300 -0.0004000
0.0001100 -0.0012100
0.0002700 -0.0019700
0.0005300 -0.0027100
0.0013300 -0.0042200
0.0024200 -0.0057500
0.0037700 -0.0073200
0.0062300 -0.0097100
0.0095400 -0.0124000
0.0230000 -0.0205300
0.0414500 -0.0285500
0.0645700 -0.0362400
0.0920500 -0.0434200
0.1235200 -0.0500100
0.1585600 -0.0558700
0.1966800 -0.0608300
0.2373700 -0.0646900
0.2801200 -0.0672000
0.3243800 -0.0679100
0.3700600 -0.0662000
0.4175000 -0.0618800
0.4669900 -0.0553900
0.5183800 -0.0475300
0.5710600 -0.0390200
0.6243200 -0.0304100
0.6773500 -0.0222200
0.7292700 -0.0148400
0.7791500 -0.0086000
0.8260400 -0.0037300
0.8689900 -0.0003100
0.9070700 0.0016900
0.9394600 0.0024300
0.9654500 0.0022200
0.9844800 0.0014100
0.9961000 0.0004500
1.0000000 0.0000000
"""

# ------------------------------------------------------------
#  Функции численного интегрирования (оставлены без изменений)
# ------------------------------------------------------------

def split_upper_lower(x, y):
    i_min = np.argmin(x)
    x_up_raw = x[:i_min+1]
    y_up_raw = y[:i_min+1]
    x_upper = x_up_raw[::-1]
    y_upper = y_up_raw[::-1]
    x_lower = x[i_min+1:]
    y_lower = y[i_min+1:]
    if x_lower[0] != 0.0:
        x_lower = np.insert(x_lower, 0, 0.0)
        y_lower = np.insert(y_lower, 0, 0.0)
    return x_upper, y_upper, x_lower, y_lower

def interpolate_to_common_grid(x_upper, y_upper, x_lower, y_lower):
    x_common = np.unique(np.concatenate([x_upper, x_lower]))
    y_upper_grid = np.interp(x_common, x_upper, y_upper)
    y_lower_grid = np.interp(x_common, x_lower, y_lower)
    return x_common, y_upper_grid, y_lower_grid

def trapezoid_area(x, y_upper, y_lower):
    h = np.diff(x)
    y_diff = y_upper - y_lower
    return np.sum(h * (y_diff[:-1] + y_diff[1:]) / 2)

def simpson_area(x, y_upper, y_lower):
    h = np.diff(x)
    if not np.allclose(h, h[0], rtol=1e-3, atol=1e-3):
        print("Предупреждение: шаг по x не равномерный. Результат Симпсона приблизительный.")
    dx = np.mean(h)
    n = len(x) - 1
    y_diff = y_upper - y_lower
    if n % 2 == 0:
        area = (dx/3) * (y_diff[0] + y_diff[-1] +
                          4 * np.sum(y_diff[1:n:2]) +
                          2 * np.sum(y_diff[2:n-1:2]))
    else:
        m = n - 3
        area_13 = (dx/3) * (y_diff[0] + y_diff[m] +
                             4 * np.sum(y_diff[1:m:2]) +
                             2 * np.sum(y_diff[2:m-1:2]))
        area_38 = (3*dx/8) * (y_diff[m] + 3*y_diff[m+1] + 3*y_diff[m+2] + y_diff[m+3])
        area = area_13 + area_38
    return area

def curve_length(x, y):
    dx = np.diff(x)
    dy = np.diff(y)
    return np.sum(np.sqrt(dx**2 + dy**2))

def moment_x_trap(x, y_upper, y_lower):
    h = np.diff(x)
    f = x * (y_upper - y_lower)
    return np.sum(h * (f[:-1] + f[1:]) / 2)

def moment_x_simp(x, y_upper, y_lower):
    h = np.diff(x)
    dx = np.mean(h)
    n = len(x) - 1
    f = x * (y_upper - y_lower)
    if n % 2 == 0:
        return (dx/3) * (f[0] + f[-1] +
                         4 * np.sum(f[1:n:2]) +
                         2 * np.sum(f[2:n-1:2]))
    else:
        m = n - 3
        area_13 = (dx/3) * (f[0] + f[m] +
                             4 * np.sum(f[1:m:2]) +
                             2 * np.sum(f[2:m-1:2]))
        area_38 = (3*dx/8) * (f[m] + 3*f[m+1] + 3*f[m+2] + f[m+3])
        return area_13 + area_38

def moment_y_trap(x, y_upper, y_lower):
    h = np.diff(x)
    f = y_upper**2 - y_lower**2
    return np.sum(h * (f[:-1] + f[1:]) / 2)

def moment_y_simp(x, y_upper, y_lower):
    h = np.diff(x)
    dx = np.mean(h)
    n = len(x) - 1
    f = y_upper**2 - y_lower**2
    if n % 2 == 0:
        return (dx/3) * (f[0] + f[-1] +
                         4 * np.sum(f[1:n:2]) +
                         2 * np.sum(f[2:n-1:2]))
    else:
        m = n - 3
        area_13 = (dx/3) * (f[0] + f[m] +
                             4 * np.sum(f[1:m:2]) +
                             2 * np.sum(f[2:m-1:2]))
        area_38 = (3*dx/8) * (f[m] + 3*f[m+1] + 3*f[m+2] + f[m+3])
        return area_13 + area_38

# ------------------------------------------------------------
#  Главный класс приложения
# ------------------------------------------------------------

class AirfoilApp:
    def __init__(self, root, x_data, y_data, variant_name):
        self.root = root
        self.root.title(f"Расчёт профиля крыла - {variant_name}")
        self.root.geometry("1000x800")

        # Таймер
        self.start_time = time.time()
        self.timer_label = ttk.Label(self.root, text="00:00:00", font=('Arial', 10))
        self.timer_label.pack(anchor='ne', padx=10, pady=5)
        self.update_timer()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.x_data = x_data
        self.y_data = y_data

        self.x_up, self.y_up, self.x_low, self.y_low = split_upper_lower(x_data, y_data)
        self.x_common, self.y_up_common, self.y_low_common = interpolate_to_common_grid(
            self.x_up, self.y_up, self.x_low, self.y_low)

        # Вычисления
        self.area_trap = trapezoid_area(self.x_common, self.y_up_common, self.y_low_common)
        self.area_simp = simpson_area(self.x_common, self.y_up_common, self.y_low_common)
        self.length_upper = curve_length(self.x_up, self.y_up)
        self.length_lower = curve_length(self.x_low, self.y_low)

        Mx_trap = moment_x_trap(self.x_common, self.y_up_common, self.y_low_common)
        Mx_simp = moment_x_simp(self.x_common, self.y_up_common, self.y_low_common)
        My_trap = moment_y_trap(self.x_common, self.y_up_common, self.y_low_common)
        My_simp = moment_y_simp(self.x_common, self.y_up_common, self.y_low_common)

        self.xc_trap = Mx_trap / self.area_trap
        self.xc_simp = Mx_simp / self.area_simp
        self.yc_trap = 0.5 * My_trap / self.area_trap
        self.yc_simp = 0.5 * My_simp / self.area_simp

        self.M2, self.M4 = self.estimate_derivatives_fd()

        self.create_widgets()

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        self.timer_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.root.after(1000, self.update_timer)

    def on_closing(self):
        self.root.destroy()
        sys.exit()

    def estimate_derivatives_fd(self):
        x = self.x_common
        f = self.y_up_common - self.y_low_common
        f1 = np.gradient(f, x, edge_order=2)
        f2 = np.gradient(f1, x, edge_order=2)
        M2 = np.max(np.abs(f2))
        f3 = np.gradient(f2, x, edge_order=2)
        f4 = np.gradient(f3, x, edge_order=2)
        M4 = np.max(np.abs(f4))
        return M2, M4

    def get_current_error(self, method):
        a, b = 0, 1
        L = b - a
        n = len(self.x_common) - 1
        if method == "trapezoid":
            return self.M2 * L**3 / (6 * n**2)
        else:
            return self.M4 * L**5 / (90 * n**4)

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True)

        self.frame_theory = ttk.Frame(notebook)
        self.frame_tasks1 = ttk.Frame(notebook)
        self.frame_tasks2 = ttk.Frame(notebook)
        self.frame_tasks3 = ttk.Frame(notebook)
        self.frame_plot = ttk.Frame(notebook)

        notebook.add(self.frame_theory, text="Теория")
        notebook.add(self.frame_tasks1, text="Задания 1 (площадь)")
        notebook.add(self.frame_tasks2, text="Задания 2 (длина кромок)")
        notebook.add(self.frame_tasks3, text="Задания 3 (центр масс фигуры)")
        notebook.add(self.frame_plot, text="График")

        self.create_theory_tab()
        self.create_tasks1_tab()
        self.create_tasks2_tab()
        self.create_tasks3_tab()
        self.create_plot_tab()

    # ---------- Вкладка Теория (чтение из файла + результаты) ----------
    def create_theory_tab(self):
        main_frame = ttk.Frame(self.frame_theory)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Текстовое поле для теории
        self.theory_text = tk.Text(main_frame, wrap='word', font=('Arial', 11))
        self.theory_text.pack(fill='both', expand=True)

        # Пытаемся загрузить файл theory.txt
        try:
            with open('theory.txt', 'r', encoding='utf-8') as f:
                theory_content = f.read()
        except FileNotFoundError:
            theory_content = "[Файл theory.txt не найден. Показана стандартная информация.]\n\n"
            theory_content += "МЕТОДЫ ЧИСЛЕННОГО ИНТЕГРИРОВАНИЯ ДЛЯ ПРОФИЛЯ КРЫЛА\n\n"
            theory_content += "1. Площадь профиля: S = ∫ (y_верх - y_низ) dx\n"
            theory_content += "2. Длина дуги: L = ∫ √(1 + (dy/dx)²) dx\n"
            theory_content += "3. Центр масс плоской фигуры: x_c = (1/S)∫ x·(y_верх-y_низ) dx, "
            theory_content += "y_c = (1/(2S))∫ (y_верх² - y_низ²) dx\n"
            theory_content += "4. Оценка погрешности по правилу Рунге или через производные.\n"

        # Добавляем численные результаты для текущего профиля
        results = "\n\n" + "="*60 + "\n"
        results += f"РЕЗУЛЬТАТЫ ДЛЯ ТЕКУЩЕГО ПРОФИЛЯ:\n"
        results += f"Площадь (трапеции): {self.area_trap:.6f}\n"
        results += f"Площадь (Симпсон):  {self.area_simp:.6f}\n"
        results += f"Длина верхней кромки: {self.length_upper:.6f}\n"
        results += f"Длина нижней кромки: {self.length_lower:.6f}\n"
        results += f"Центр масс (трапеции): x = {self.xc_trap:.6f}, y = {self.yc_trap:.6f}\n"
        results += f"Центр масс (Симпсон):  x = {self.xc_simp:.6f}, y = {self.yc_simp:.6f}\n"
        results += f"Оценка погрешности площади (трапеции): {self.get_current_error('trapezoid'):.3e}\n"
        results += f"Оценка погрешности площади (Симпсон):  {self.get_current_error('simpson'):.3e}\n"
        results += "="*60

        self.theory_text.insert('1.0', theory_content + results)
        self.theory_text.config(state='disabled')

    # ---------- Задание 1 (площадь) ----------
    def create_tasks1_tab(self):
        input_frame = ttk.LabelFrame(self.frame_tasks1, text="Задание 1: площадь профиля")
        input_frame.pack(fill='both', padx=20, pady=10, ipadx=10, ipady=10)

        ttk.Label(input_frame, text="Профиль: заданный вариант", font=('Arial', 12, 'bold')).pack(pady=5)
        ttk.Label(input_frame, text="Вычислите площадь профиля.\nВыберите метод и введите ваш ответ.", font=('Arial', 11)).pack(pady=5)

        self.method_var1 = tk.StringVar(value="trapezoid")
        method_frame = ttk.Frame(input_frame)
        method_frame.pack(pady=5)
        ttk.Radiobutton(method_frame, text="Метод трапеций", variable=self.method_var1, value="trapezoid").pack(side='left', padx=10)
        ttk.Radiobutton(method_frame, text="Метод Симпсона", variable=self.method_var1, value="simpson").pack(side='left', padx=10)

        ttk.Label(input_frame, text="Введите ваш ответ (площадь):").pack(pady=5)
        self.answer_var1 = tk.StringVar()
        self.answer_entry1 = ttk.Entry(input_frame, textvariable=self.answer_var1, width=20, font=('Arial', 12))
        self.answer_entry1.pack(pady=5)

        self.check_button1 = ttk.Button(input_frame, text="Проверить площадь", command=self.check_answer1)
        self.check_button1.pack(pady=10)

        result_frame = ttk.LabelFrame(self.frame_tasks1, text="Результат проверки площади")
        result_frame.pack(fill='both', padx=20, pady=10, ipadx=10, ipady=10)
        self.result_label1 = ttk.Label(result_frame, text="", font=('Arial', 12))
        self.result_label1.pack(pady=10)

        # Кнопка показа ответа – изначально disabled
        self.show_answer_button1 = ttk.Button(result_frame, text="Показать правильный ответ для выбранного метода",
                                              command=self.show_true_area, state='disabled')
        self.show_answer_button1.pack(pady=5)

        # Блок оценки погрешности
        error_frame = ttk.LabelFrame(self.frame_tasks1, text="Проверка оценки погрешности (метод конечных разностей)")
        error_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(error_frame, text="Введите вашу оценку погрешности:").pack(anchor='w', padx=10, pady=5)
        self.error_answer_var = tk.StringVar()
        self.error_answer_entry = ttk.Entry(error_frame, textvariable=self.error_answer_var, width=20, font=('Arial', 12))
        self.error_answer_entry.pack(anchor='w', padx=10, pady=5)

        self.check_error_button = ttk.Button(error_frame, text="Проверить оценку погрешности", command=self.check_error_estimate)
        self.check_error_button.pack(anchor='w', padx=10, pady=5)

        self.show_error_button = ttk.Button(error_frame, text="Показать правильную погрешность",
                                            command=self.show_true_error, state='disabled')
        self.show_error_button.pack(anchor='w', padx=10, pady=5)

        self.error_result_label = ttk.Label(error_frame, text="", font=('Arial', 10))
        self.error_result_label.pack(anchor='w', padx=10, pady=5)

    def check_error_estimate(self):
        user_input = self.error_answer_var.get().strip()
        if not user_input:
            messagebox.showwarning("Предупреждение", "Введите число!")
            return
        try:
            user_error = float(user_input)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числа. Используйте точку как десятичный разделитель.")
            return

        method = self.method_var1.get()
        true_error = self.get_current_error(method)
        method_name = "трапеций" if method == "trapezoid" else "Симпсона"
        if abs(true_error) > 1e-12:
            rel_diff = abs(user_error - true_error) / abs(true_error)
            if rel_diff <= 0.03:
                self.error_result_label.config(
                    text=f"✅ Правильно! Погрешность метода {method_name} = {true_error:.3e}",
                    foreground='green'
                )
            else:
                self.error_result_label.config(
                    text=f"❌ Неправильно. Отличие = {rel_diff*100:.2f}% (>3%)\nПопробуйте ещё раз.",
                    foreground='red'
                )
        else:
            if abs(user_error - true_error) <= 1e-4:
                self.error_result_label.config(
                    text=f"✅ Правильно! Погрешность метода {method_name} = {true_error:.3e}",
                    foreground='green'
                )
            else:
                self.error_result_label.config(
                    text=f"❌ Неправильно. Отличие = {abs(user_error - true_error):.3e}\nПопробуйте ещё раз.",
                    foreground='red'
                )
        # Активируем кнопку показа правильной погрешности
        self.show_error_button.config(state='normal')

    def show_true_error(self):
        method = self.method_var1.get()
        true_error = self.get_current_error(method)
        method_name = "трапеций" if method == "trapezoid" else "Симпсона"
        messagebox.showinfo("Правильная погрешность",
                            f"Погрешность метода {method_name}: {true_error:.3e}")

    def get_selected_area(self):
        return self.area_trap if self.method_var1.get() == "trapezoid" else self.area_simp

    def check_answer1(self):
        user_input = self.answer_var1.get().strip()
        if not user_input:
            messagebox.showwarning("Предупреждение", "Введите число!")
            return
        try:
            user_answer = float(user_input)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числа. Используйте точку как десятичный разделитель.")
            return

        true_area = self.get_selected_area()
        method_name = "трапеций" if self.method_var1.get() == "trapezoid" else "Симпсона"

        if abs(true_area) > 1e-12:
            rel_diff = abs(user_answer - true_area) / abs(true_area)
            if rel_diff <= 0.03:
                self.result_label1.config(text=f"✅ Правильно! Площадь методом {method_name} = {true_area:.6f}", foreground='green')
            else:
                self.result_label1.config(text=f"❌ Неправильно. Отличие = {rel_diff*100:.2f}% (>3%)\nПопробуйте ещё раз.", foreground='red')
        else:
            if abs(user_answer - true_area) <= 1e-4:
                self.result_label1.config(text=f"✅ Правильно! Площадь методом {method_name} = {true_area:.6f}", foreground='green')
            else:
                self.result_label1.config(text=f"❌ Неправильно. Отличие = {abs(user_answer - true_area):.6f}\nПопробуйте ещё раз.", foreground='red')

        # Активируем кнопку показа правильного ответа
        self.show_answer_button1.config(state='normal')

    def show_true_area(self):
        true_area = self.get_selected_area()
        method_name = "трапеций" if self.method_var1.get() == "trapezoid" else "Симпсона"
        messagebox.showinfo("Правильный ответ", f"Площадь методом {method_name}: {true_area:.6f}")

    # ---------- Задание 2 (длина кромок) ----------
    def create_tasks2_tab(self):
        input_frame = ttk.LabelFrame(self.frame_tasks2, text="Задание 2: длина кромок профиля")
        input_frame.pack(fill='both', padx=20, pady=20, ipadx=10, ipady=10)

        ttk.Label(input_frame, text="Вычислите длину верхней и/или нижней поверхности.\nВведите ответы и нажмите 'Проверить'.", font=('Arial', 11)).pack(pady=5)

        self.answer_upper = tk.StringVar()
        self.answer_lower = tk.StringVar()

        upper_frame = ttk.Frame(input_frame)
        upper_frame.pack(fill='x', pady=10)
        ttk.Label(upper_frame, text="Длина верхней поверхности:", font=('Arial', 10, 'bold')).pack(side='left', padx=10)
        ttk.Entry(upper_frame, textvariable=self.answer_upper, width=15, font=('Arial', 12)).pack(side='left', padx=5)

        lower_frame = ttk.Frame(input_frame)
        lower_frame.pack(fill='x', pady=10)
        ttk.Label(lower_frame, text="Длина нижней поверхности:", font=('Arial', 10, 'bold')).pack(side='left', padx=10)
        ttk.Entry(lower_frame, textvariable=self.answer_lower, width=15, font=('Arial', 12)).pack(side='left', padx=5)

        self.check_button2 = ttk.Button(input_frame, text="Проверить", command=self.check_answer2)
        self.check_button2.pack(pady=15)

        result_frame = ttk.LabelFrame(self.frame_tasks2, text="Результат")
        result_frame.pack(fill='both', padx=20, pady=20, ipadx=10, ipady=10)
        self.result_label2 = ttk.Label(result_frame, text="", font=('Arial', 12))
        self.result_label2.pack(pady=10)

        self.show_answer_button2 = ttk.Button(result_frame, text="Показать правильные ответы",
                                              command=self.show_true_lengths, state='disabled')
        self.show_answer_button2.pack(pady=5)

    def check_answer2(self):
        upper_str = self.answer_upper.get().strip()
        lower_str = self.answer_lower.get().strip()

        messages = []
        if upper_str:
            try:
                user_upper = float(upper_str)
                true_upper = self.length_upper
                if abs(true_upper) > 1e-12:
                    rel_diff = abs(user_upper - true_upper) / abs(true_upper)
                    if rel_diff <= 0.03:
                        messages.append(f"✅ Верхняя кромка: {true_upper:.6f}")
                    else:
                        messages.append(f"❌ Верхняя кромка: отличие {rel_diff*100:.2f}% (>3%)")
                else:
                    if abs(user_upper - true_upper) <= 1e-4:
                        messages.append(f"✅ Верхняя кромка: {true_upper:.6f}")
                    else:
                        messages.append(f"❌ Верхняя кромка: отличие {abs(user_upper - true_upper):.6f}")
            except ValueError:
                messages.append("❌ Верхняя кромка: неверный формат числа")
        if lower_str:
            try:
                user_lower = float(lower_str)
                true_lower = self.length_lower
                if abs(true_lower) > 1e-12:
                    rel_diff = abs(user_lower - true_lower) / abs(true_lower)
                    if rel_diff <= 0.03:
                        messages.append(f"✅ Нижняя кромка: {true_lower:.6f}")
                    else:
                        messages.append(f"❌ Нижняя кромка: отличие {rel_diff*100:.2f}% (>3%)")
                else:
                    if abs(user_lower - true_lower) <= 1e-4:
                        messages.append(f"✅ Нижняя кромка: {true_lower:.6f}")
                    else:
                        messages.append(f"❌ Нижняя кромка: отличие {abs(user_lower - true_lower):.6f}")
            except ValueError:
                messages.append("❌ Нижняя кромка: неверный формат числа")
        if not upper_str and not lower_str:
            messages.append("Введите хотя бы одно значение.")

        self.result_label2.config(text="\n".join(messages))
        # Активируем кнопку показа ответов
        self.show_answer_button2.config(state='normal')

    def show_true_lengths(self):
        messagebox.showinfo("Правильные ответы",
                            f"Длина верхней кромки: {self.length_upper:.6f}\n"
                            f"Длина нижней кромки: {self.length_lower:.6f}")

    # ---------- Задание 3 (центр масс) ----------
    def create_tasks3_tab(self):
        input_frame = ttk.LabelFrame(self.frame_tasks3, text="Задание 3: центр масс профиля (плоская фигура)")
        input_frame.pack(fill='both', padx=20, pady=20, ipadx=10, ipady=10)

        ttk.Label(input_frame, text="Вычислите координаты центра масс плоской фигуры (профиля).\nВыберите метод и введите x_c, y_c.", font=('Arial', 11)).pack(pady=5)

        method_frame = ttk.Frame(input_frame)
        method_frame.pack(pady=5)
        ttk.Label(method_frame, text="Метод:").pack(side='left', padx=5)
        self.method_var3 = tk.StringVar(value="trapezoid")
        ttk.Radiobutton(method_frame, text="Трапеций", variable=self.method_var3, value="trapezoid").pack(side='left', padx=5)
        ttk.Radiobutton(method_frame, text="Симпсона", variable=self.method_var3, value="simpson").pack(side='left', padx=5)

        coord_frame = ttk.Frame(input_frame)
        coord_frame.pack(pady=10)

        ttk.Label(coord_frame, text="x_c:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.xc_answer_var = tk.StringVar()
        xc_entry = ttk.Entry(coord_frame, textvariable=self.xc_answer_var, width=15, font=('Arial', 12))
        xc_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(coord_frame, text="y_c:", font=('Arial', 10, 'bold')).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.yc_answer_var = tk.StringVar()
        yc_entry = ttk.Entry(coord_frame, textvariable=self.yc_answer_var, width=15, font=('Arial', 12))
        yc_entry.grid(row=1, column=1, padx=5, pady=5)

        self.check_button3 = ttk.Button(input_frame, text="Проверить", command=self.check_answer3)
        self.check_button3.pack(pady=15)

        result_frame = ttk.LabelFrame(self.frame_tasks3, text="Результат проверки центра масс")
        result_frame.pack(fill='both', padx=20, pady=20, ipadx=10, ipady=10)
        self.result_label3 = ttk.Label(result_frame, text="", font=('Arial', 12))
        self.result_label3.pack(pady=10)

        self.show_answer_button3 = ttk.Button(result_frame, text="Показать правильные ответы для выбранного метода",
                                              command=self.show_true_cm, state='disabled')
        self.show_answer_button3.pack(pady=5)

    def get_selected_cm(self):
        if self.method_var3.get() == "trapezoid":
            return self.xc_trap, self.yc_trap
        else:
            return self.xc_simp, self.yc_simp

    def check_answer3(self):
        xc_str = self.xc_answer_var.get().strip()
        yc_str = self.yc_answer_var.get().strip()

        if not xc_str or not yc_str:
            messagebox.showwarning("Предупреждение", "Введите оба значения (x_c и y_c)!")
            return

        try:
            user_xc = float(xc_str)
            user_yc = float(yc_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат числа. Используйте точку как десятичный разделитель.")
            return

        true_xc, true_yc = self.get_selected_cm()
        method_name = "трапеций" if self.method_var3.get() == "trapezoid" else "Симпсона"

        def check_one(user, true, name):
            if abs(true) > 1e-12:
                rel = abs(user - true) / abs(true)
                if rel <= 0.03:
                    return True, None
                else:
                    return False, f"{name}: отличие {rel*100:.2f}% (>3%)"
            else:
                if abs(user - true) <= 1e-4:
                    return True, None
                else:
                    return False, f"{name}: отличие {abs(user - true):.3e}"

        ok_x, msg_x = check_one(user_xc, true_xc, "x_c")
        ok_y, msg_y = check_one(user_yc, true_yc, "y_c")

        if ok_x and ok_y:
            self.result_label3.config(
                text=f"✅ Правильно! Метод {method_name}:\n x_c = {true_xc:.6f}, y_c = {true_yc:.6f}",
                foreground='green'
            )
        else:
            errors = [f"❌ Неправильно для метода {method_name}:"]
            if not ok_x:
                errors.append(msg_x)
            if not ok_y:
                errors.append(msg_y)
            errors.append("Попробуйте ещё раз.")
            self.result_label3.config(text="\n".join(errors), foreground='red')

        # Активируем кнопку показа ответа
        self.show_answer_button3.config(state='normal')

    def show_true_cm(self):
        true_xc, true_yc = self.get_selected_cm()
        method_name = "трапеций" if self.method_var3.get() == "trapezoid" else "Симпсона"
        messagebox.showinfo("Правильный ответ",
                            f"Метод {method_name}:\n"
                            f"x_c = {true_xc:.6f}\n"
                            f"y_c = {true_yc:.6f}")

    # ---------- Вкладка График ----------
    def create_plot_tab(self):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(self.x_up, self.y_up, 'b-', linewidth=2, label='Верхняя поверхность')
        ax.plot(self.x_low, self.y_low, 'r-', linewidth=2, label='Нижняя поверхность')
        ax.plot(self.xc_trap, self.yc_trap, 'ko', markersize=8, label='Центр масс (трапеции)')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('Профиль крыла')
        ax.legend()
        ax.grid(True)
        ax.axis('equal')
        canvas = FigureCanvasTkAgg(fig, master=self.frame_plot)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

# ------------------------------------------------------------
#  Окно выбора варианта
# ------------------------------------------------------------

def choose_variant():
    choice_win = tk.Tk()
    choice_win.title("Лабораторная работа")
    choice_win.geometry("800x600")

    ttk.Label(choice_win, text="Выберите номер варианта (1-20):", font=('Arial', 25)).pack(pady=20)

    buttons_frame = ttk.Frame(choice_win)
    buttons_frame.pack(expand=True)

    def load_variant(var):
        # Загрузка данных в зависимости от варианта
        if var == 2:
            upper_pts = parse_coordinate_block(variant2_upper_str)
            lower_pts = parse_coordinate_block(variant2_lower_str)
            x, y = build_contour_from_parts(upper_pts, lower_pts)
            name = f"Вариант {var} (заданные координаты)"
        elif var == 4:
            upper_pts = parse_coordinate_block(variant4_upper_str)
            lower_pts = parse_coordinate_block(variant4_lower_str)
            x, y = build_contour_from_parts(upper_pts, lower_pts)
            name = f"Вариант {var} (заданные координаты)"
        elif var == 6:
            upper_pts = parse_coordinate_block(variant6_upper_str)
            lower_pts = parse_coordinate_block(variant6_lower_str)
            x, y = build_contour_from_parts(upper_pts, lower_pts)
            name = f"Вариант {var} (заданные координаты)"
        elif var == 8:
            pts = parse_coordinate_block(variant8_contour_str)
            x = np.array([p[0] for p in pts])
            y = np.array([p[1] for p in pts])
            name = f"Вариант {var} (заданные координаты)"
        elif var == 10:
            upper_pts = parse_coordinate_block(variant10_upper_str)
            lower_pts = parse_coordinate_block(variant10_lower_str)
            x, y = build_contour_from_parts(upper_pts, lower_pts)
            name = f"Вариант {var} (заданные координаты)"
        elif var == 12:
            upper_pts = parse_coordinate_block(variant10_upper_str)   # те же данные, что и для 10
            lower_pts = parse_coordinate_block(variant10_lower_str)
            x, y = build_contour_from_parts(upper_pts, lower_pts)
            name = f"Вариант {var} (заданные координаты)"
        else:
            t = 0.08 + (var - 1) * 0.01
            x, y = generate_naca_profile(t, num_points=100)
            name = f"Вариант {var} (NACA 00{int(t*100):02d})"

        choice_win.destroy()
        root = tk.Tk()
        app = AirfoilApp(root, x, y, name)
        root.mainloop()

    # Создаём сетку кнопок 4x5
    for i in range(20):
        row = i // 5
        col = i % 5
        btn = ttk.Button(buttons_frame, text=str(i+1), width=20,
                         command=lambda v=i+1: load_variant(v))
        btn.grid(row=row, column=col, padx=10, pady=20)

    choice_win.mainloop()

if __name__ == "__main__":
    choose_variant()
print(open('theory.txt', 'r', encoding='utf-8'))