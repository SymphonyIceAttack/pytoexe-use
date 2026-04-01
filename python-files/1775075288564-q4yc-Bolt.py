import tkinter as tk
from tkinter import ttk, messagebox
import math

class BoltConnectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчет болтового соединения по ГОСТ")
        self.root.geometry("1200x750")
        self.root.resizable(True, True)
        self.root.minsize(1000, 650)

        # Центрируем окно
        self.center_window()

        # Настраиваем стиль
        self.setup_style()

        # Словарь стандартных длин болтов по ГОСТ 7798-70 (мм)
        self.standard_lengths = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90,
                                  95, 100, 105, 110, 115, 120, 130, 140, 150, 160, 170, 180,
                                  190, 200, 220, 240, 260, 280, 300]

        # Диаметры резьбы (метрическая)
        self.thread_diameters = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 42, 45, 48, 52, 56, 60]

        # Шаг резьбы для стандартной метрической резьбы
        self.thread_pitch = {
            6: 1.0, 8: 1.25, 10: 1.5, 12: 1.75, 14: 2.0, 16: 2.0,
            18: 2.5, 20: 2.5, 22: 2.5, 24: 3.0, 27: 3.0, 30: 3.5,
            33: 3.5, 36: 4.0, 39: 4.0, 42: 4.5, 45: 4.5, 48: 5.0,
            52: 5.0, 56: 5.5, 60: 5.5
        }

        # Классы прочности болтов (предел текучести, МПа)
        self.strength_classes = {
            "3.6": 180, "4.6": 240, "4.8": 320, "5.6": 300, "5.8": 400,
            "6.6": 360, "6.8": 480, "8.8": 640, "9.8": 720, "10.9": 900,
            "12.9": 1080
        }

        # Коэффициент запаса в зависимости от типа нагрузки и соединения
        self.safety_factors = {
            ("Статическая", "Неподвижное"): 1.5,
            ("Статическая", "Подвижное"): 2.0,
            ("Динамическая", "Неподвижное"): 2.0,
            ("Динамическая", "Подвижное"): 2.5,
            ("Ударная", "Неподвижное"): 2.5,
            ("Ударная", "Подвижное"): 3.0
        }

        # Создаем интерфейс
        self.create_widgets()

        # Устанавливаем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        if width == 1 or height == 1:
            width, height = 1200, 750
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='navy')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='darkblue')

    def create_widgets(self):
        # Верхний заголовок (общий)
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(title_frame, text="🔩 РАСЧЕТ БОЛТОВОГО СОЕДИНЕНИЯ", style='Title.TLabel').pack()
        ttk.Label(title_frame, text="ГОСТ 7798-70 - Болты с шестигранной головкой", font=('Arial', 10)).pack()

        # Основной контейнер (горизонтальный)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Левая панель – поля ввода
        left_frame = ttk.LabelFrame(main_frame, text=" Введите исходные данные ", padding=15)
        left_frame.pack(side='left', fill='both', expand=False, padx=(0, 10))

        self.create_input_fields(left_frame)

        # Правая панель – результаты
        right_frame = ttk.LabelFrame(main_frame, text=" Результаты расчета ", padding=10)
        right_frame.pack(side='right', fill='both', expand=True)

        self.create_results_area(right_frame)

        # Кнопки внизу (общие)
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=20, pady=10)

        self.calc_btn = tk.Button(button_frame, text="РАССЧИТАТЬ", bg='#4CAF50', fg='white',
                                   font=('Arial', 12, 'bold'), command=self.calculate, padx=20, pady=5)
        self.calc_btn.pack(side='left', padx=5)

        self.clear_btn = tk.Button(button_frame, text="ОЧИСТИТЬ", bg='#f44336', fg='white',
                                    font=('Arial', 10), command=self.clear_results, padx=15, pady=5)
        self.clear_btn.pack(side='left', padx=5)

        self.gost_btn = tk.Button(button_frame, text="ПОДОБРАТЬ ДЛИНУ", bg='#2196F3', fg='white',
                                   font=('Arial', 10), command=self.suggest_length, padx=15, pady=5)
        self.gost_btn.pack(side='left', padx=5)

    def create_input_fields(self, parent):
        # Сетка для полей ввода
        row = 0

        # Диаметр болта
        ttk.Label(parent, text="Диаметр резьбы d (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.diameter_var = tk.StringVar(value="16")
        self.diameter_combo = ttk.Combobox(parent, textvariable=self.diameter_var,
                                           values=self.thread_diameters, state='normal', width=10)
        self.diameter_combo.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        self.diameter_combo.bind('<KeyRelease>', self.update_pitch)
        self.diameter_combo.bind('<<ComboboxSelected>>', self.update_pitch)
        ttk.Label(parent, text="мм").grid(row=row, column=2, sticky='w', pady=5)
        row += 1

        # Шаг резьбы
        ttk.Label(parent, text="Шаг резьбы P (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.pitch_var = tk.StringVar(value="2.0")
        ttk.Entry(parent, textvariable=self.pitch_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Класс прочности
        ttk.Label(parent, text="Класс прочности:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.class_var = tk.StringVar(value="8.8")
        ttk.Combobox(parent, textvariable=self.class_var, values=list(self.strength_classes.keys()),
                     state='readonly', width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Толщина первой детали
        ttk.Label(parent, text="Толщина детали 1 (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.thick1_var = tk.StringVar(value="20")
        ttk.Entry(parent, textvariable=self.thick1_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Толщина второй детали
        ttk.Label(parent, text="Толщина детали 2 (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.thick2_var = tk.StringVar(value="15")
        ttk.Entry(parent, textvariable=self.thick2_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Рабочая нагрузка
        ttk.Label(parent, text="Рабочая нагрузка F (Н):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.force_var = tk.StringVar(value="5000")
        ttk.Entry(parent, textvariable=self.force_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Количество болтов
        ttk.Label(parent, text="Количество болтов:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.count_var = tk.IntVar(value=1)
        spinbox = tk.Spinbox(parent, from_=1, to=12, textvariable=self.count_var, width=5)
        spinbox.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Тип нагрузки
        ttk.Label(parent, text="Тип нагрузки:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.load_type_var = tk.StringVar(value="Статическая")
        frame_load = ttk.Frame(parent)
        frame_load.grid(row=row, column=1, columnspan=2, sticky='w', pady=5)
        ttk.Radiobutton(frame_load, text="Статическая", variable=self.load_type_var,
                       value="Статическая").pack(side='left', padx=2)
        ttk.Radiobutton(frame_load, text="Динамическая", variable=self.load_type_var,
                       value="Динамическая").pack(side='left', padx=2)
        ttk.Radiobutton(frame_load, text="Ударная", variable=self.load_type_var,
                       value="Ударная").pack(side='left', padx=2)
        row += 1

        # Тип соединения
        ttk.Label(parent, text="Тип соединения:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.conn_type_var = tk.StringVar(value="Неподвижное")
        frame_conn = ttk.Frame(parent)
        frame_conn.grid(row=row, column=1, columnspan=2, sticky='w', pady=5)
        ttk.Radiobutton(frame_conn, text="Неподвижное", variable=self.conn_type_var,
                       value="Неподвижное").pack(side='left', padx=2)
        ttk.Radiobutton(frame_conn, text="Подвижное", variable=self.conn_type_var,
                       value="Подвижное").pack(side='left', padx=2)
        row += 1

        # Контроль затяжки
        self.torque_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="Контролировать момент затяжки",
                       variable=self.torque_var).grid(row=row, column=0, columnspan=2, sticky='w', pady=5)

    def update_pitch(self, event=None):
        try:
            d = float(self.diameter_var.get())
            if d in self.thread_pitch:
                self.pitch_var.set(str(self.thread_pitch[d]))
        except:
            pass

    def suggest_length(self):
        try:
            d = float(self.diameter_var.get())
            h1 = float(self.thick1_var.get())
            h2 = float(self.thick2_var.get())
            # Параметры головки и гайки по ГОСТ
            head_height = 0.7 * d  # высота головки
            nut_height = 0.8 * d    # высота гайки
            washer_thick = 0.15 * d  # толщина шайбы
            protrusion = 0.3 * d      # выступающий конец
            L_calc = h1 + h2 + head_height + nut_height + 2 * washer_thick + protrusion
            L_std = min(self.standard_lengths, key=lambda x: abs(x - L_calc))
            messagebox.showinfo("Подбор длины",
                               f"Расчетная длина болта: {L_calc:.1f} мм\n"
                               f"Стандартная длина по ГОСТ: {L_std} мм")
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте ввод толщин и диаметра")

    def create_results_area(self, parent):
        # Создаем текстовое поле с прокруткой
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        self.result_text = tk.Text(text_frame, height=20, width=60,
                                   font=('Courier', 10), wrap='word')
        self.result_text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.result_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.result_text.configure(yscrollcommand=scrollbar.set)

        # Теги для цвета
        self.result_text.tag_configure('header', foreground='navy', font=('Courier', 11, 'bold'))
        self.result_text.tag_configure('good', foreground='green')
        self.result_text.tag_configure('bad', foreground='red')
        self.result_text.tag_configure('warning', foreground='orange')
        self.result_text.tag_configure('value', foreground='blue')

    def calculate(self):
        try:
            d = float(self.diameter_var.get())
            p = float(self.pitch_var.get())
            strength_class = self.class_var.get()
            h1 = float(self.thick1_var.get())
            h2 = float(self.thick2_var.get())
            force = float(self.force_var.get())
            n_bolts = self.count_var.get()
            load_type = self.load_type_var.get()
            conn_type = self.conn_type_var.get()
            torque_control = self.torque_var.get()

            # Геометрические параметры по ГОСТ
            head_diam = 2.0 * d
            head_height = 0.7 * d
            nut_diam = 2.0 * d
            nut_height = 0.8 * d
            washer_diam = 2.2 * d
            washer_thick = 0.15 * d
            protrusion = 0.3 * d

            # Расчетная длина болта
            L_calc = h1 + h2 + head_height + nut_height + 2 * washer_thick + protrusion
            L_std = min(self.standard_lengths, key=lambda x: abs(x - L_calc))

            # Прочностной расчет
            d1 = d - 1.22687 * p  # внутренний диаметр резьбы
            area = math.pi * (d1/2) ** 2  # площадь сечения в мм²

            sigma_t = self.strength_classes.get(strength_class, 240)

            safety_key = (load_type, conn_type)
            safety_norm = self.safety_factors.get(safety_key, 1.5)

            allowable_stress = sigma_t / safety_norm
            stress = force / (area * n_bolts)
            safety_factor = allowable_stress / stress if stress > 0 else 0

            if torque_control:
                preload = 0.7 * sigma_t * area / 1000  # кН
                torque = 0.2 * d * preload  # Н·м
            else:
                preload = torque = 0

            self.result_text.delete(1.0, tk.END)

            self.result_text.insert(tk.END, "="*70 + "\n", 'header')
            self.result_text.insert(tk.END, "           РАСЧЕТ БОЛТОВОГО СОЕДИНЕНИЯ\n", 'header')
            self.result_text.insert(tk.END, "="*70 + "\n\n", 'header')

            self.result_text.insert(tk.END, "📌 ГЕОМЕТРИЧЕСКИЕ ПАРАМЕТРЫ:\n", 'header')
            self.result_text.insert(tk.END, f"   Болт М{d}×{L_std} ГОСТ 7798-70\n")
            self.result_text.insert(tk.END, f"   Гайка М{d} ГОСТ 5915-70\n")
            self.result_text.insert(tk.END, f"   Шайба {d} ГОСТ 11371-78\n")
            self.result_text.insert(tk.END, f"   Размер под ключ: {nut_diam:.1f} мм\n")
            self.result_text.insert(tk.END, f"   Длина болта: {L_std} мм\n")
            self.result_text.insert(tk.END, f"   Выступающий конец: {protrusion:.1f} мм\n\n")

            self.result_text.insert(tk.END, "🔧 ПАРАМЕТРЫ РЕЗЬБЫ:\n", 'header')
            self.result_text.insert(tk.END, f"   Наружный диаметр d: {d} мм\n")
            self.result_text.insert(tk.END, f"   Внутренний диаметр d1: {d1:.2f} мм\n")
            self.result_text.insert(tk.END, f"   Шаг резьбы P: {p} мм\n")
            self.result_text.insert(tk.END, f"   Площадь сечения: {area:.2f} мм²\n\n")

            self.result_text.insert(tk.END, "📊 ПРОЧНОСТНЫЕ ХАРАКТЕРИСТИКИ:\n", 'header')
            self.result_text.insert(tk.END, f"   Класс прочности: {strength_class}\n")
            self.result_text.insert(tk.END, f"   Предел текучести σт: {sigma_t} МПа\n")
            self.result_text.insert(tk.END, f"   Количество болтов: {n_bolts}\n")
            self.result_text.insert(tk.END, f"   Нагрузка на 1 болт: {force/n_bolts:.0f} Н\n")
            self.result_text.insert(tk.END, f"   Напряжение σр: {stress:.2f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   Допускаемое напряжение [σ]: {allowable_stress:.2f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   Коэффициент запаса: {safety_factor:.2f}\n", 'value')

            if safety_factor >= safety_norm:
                self.result_text.insert(tk.END, "   ОЦЕНКА: ✅ Прочность обеспечена\n", 'good')
                if safety_factor > 1.5 * safety_norm:
                    self.result_text.insert(tk.END, "      (запас большой)\n", 'good')
                elif safety_factor < 1.1 * safety_norm:
                    self.result_text.insert(tk.END, "      (запас минимальный)\n", 'warning')
            else:
                self.result_text.insert(tk.END, "   ОЦЕНКА: ❌ Прочность НЕ обеспечена\n", 'bad')
                self.result_text.insert(tk.END, "      Увеличьте диаметр, класс прочности или количество болтов\n", 'bad')

            if torque_control:
                self.result_text.insert(tk.END, "\n🔧 РЕКОМЕНДАЦИИ ПО ЗАТЯЖКЕ:\n", 'header')
                self.result_text.insert(tk.END, f"   Усилие предварительной затяжки: {preload:.1f} кН\n")
                self.result_text.insert(tk.END, f"   Момент затяжки: {torque:.1f} Н·м\n")
                self.result_text.insert(tk.END, f"   Использовать динамометрический ключ\n")

            self.result_text.insert(tk.END, "\n" + "="*70 + "\n", 'header')

        except Exception as e:
            messagebox.showerror("Ошибка расчета", f"Проверьте данные:\n{str(e)}")

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)

    def on_closing(self):
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BoltConnectionApp(root)
    root.mainloop()