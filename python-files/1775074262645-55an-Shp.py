import tkinter as tk
from tkinter import ttk, messagebox
import math

class StudConnectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчет шпилечного соединения по ГОСТ")
        self.root.geometry("1200x750")
        self.root.resizable(True, True)
        self.root.minsize(1000, 650)

        self.center_window()
        self.setup_style()

        # Стандартные длины шпилек (ГОСТ 22032-76 и др.)
        self.standard_lengths = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90,
                                  95, 100, 105, 110, 115, 120, 130, 140, 150, 160, 170, 180,
                                  190, 200, 220, 240, 260, 280, 300]

        # Диаметры резьбы
        self.thread_diameters = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 42, 45, 48, 52, 56, 60]

        # Шаг резьбы
        self.thread_pitch = {
            6: 1.0, 8: 1.25, 10: 1.5, 12: 1.75, 14: 2.0, 16: 2.0,
            18: 2.5, 20: 2.5, 22: 2.5, 24: 3.0, 27: 3.0, 30: 3.5,
            33: 3.5, 36: 4.0, 39: 4.0, 42: 4.5, 45: 4.5, 48: 5.0,
            52: 5.0, 56: 5.5, 60: 5.5
        }

        # Материалы базовой детали и коэффициент длины ввинчивания
        self.screw_in_coeff = {
            "Сталь, бронза, латунь": 1.0,
            "Серый чугун": 1.25,
            "Ковкий чугун": 1.6,
            "Легкие сплавы (алюминий)": 2.0
        }

        # Классы прочности (σт, МПа)
        self.strength_classes = {
            "3.6": 180, "4.6": 240, "4.8": 320, "5.6": 300, "5.8": 400,
            "6.6": 360, "6.8": 480, "8.8": 640, "9.8": 720, "10.9": 900,
            "12.9": 1080
        }

        # Коэффициент запаса по типу нагрузки
        self.safety_factors = {
            "Статическая": 1.5,
            "Динамическая": 2.0,
            "Ударная": 3.0
        }

        # Допускаемые напряжения смятия для материалов детали (МПа)
        self.bearing_allowable = {
            "Сталь": 200,
            "Чугун": 130,
            "Алюминий": 80
        }

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w == 1 or h == 1:
            w, h = 1200, 750
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='navy')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='darkblue')

    def create_widgets(self):
        # Заголовок
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(title_frame, text="🔩 РАСЧЕТ ШПИЛЕЧНОГО СОЕДИНЕНИЯ", style='Title.TLabel').pack()
        ttk.Label(title_frame, text="ГОСТ 22032-76, ГОСТ 22034-76, ГОСТ 22036-76, ГОСТ 22038-76",
                  font=('Arial', 10)).pack()

        # Основной контейнер
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

        # Кнопки внизу
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
        row = 0

        # Диаметр резьбы
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
        ttk.Combobox(parent, textvariable=self.class_var,
                     values=list(self.strength_classes.keys()),
                     state='readonly', width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Материал базовой детали (для длины ввинчивания)
        ttk.Label(parent, text="Материал базовой детали:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.base_material_var = tk.StringVar(value="Сталь, бронза, латунь")
        ttk.Combobox(parent, textvariable=self.base_material_var,
                     values=list(self.screw_in_coeff.keys()),
                     state='readonly', width=20).grid(row=row, column=1, columnspan=2, sticky='w', padx=10, pady=5)
        row += 1

        # Толщина присоединяемой детали H
        ttk.Label(parent, text="Толщина присоединяемой детали H (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.thickness_var = tk.StringVar(value="20")
        ttk.Entry(parent, textvariable=self.thickness_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Рабочая нагрузка
        ttk.Label(parent, text="Рабочая нагрузка F (Н):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.force_var = tk.StringVar(value="5000")
        ttk.Entry(parent, textvariable=self.force_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Количество шпилек
        ttk.Label(parent, text="Количество шпилек:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
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

        # Тип соединения (подвижное/неподвижное) – влияет на запас
        ttk.Label(parent, text="Тип соединения:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.conn_type_var = tk.StringVar(value="Неподвижное")
        frame_conn = ttk.Frame(parent)
        frame_conn.grid(row=row, column=1, columnspan=2, sticky='w', pady=5)
        ttk.Radiobutton(frame_conn, text="Неподвижное", variable=self.conn_type_var,
                       value="Неподвижное").pack(side='left', padx=2)
        ttk.Radiobutton(frame_conn, text="Подвижное", variable=self.conn_type_var,
                       value="Подвижное").pack(side='left', padx=2)
        row += 1

        # Материал детали (для смятия)
        ttk.Label(parent, text="Материал детали (для смятия):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.material_var = tk.StringVar(value="Сталь")
        frame_mat = ttk.Frame(parent)
        frame_mat.grid(row=row, column=1, columnspan=2, sticky='w', pady=5)
        for mat in self.bearing_allowable.keys():
            ttk.Radiobutton(frame_mat, text=mat, variable=self.material_var,
                           value=mat).pack(side='left', padx=2)
        row += 1

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
            H = float(self.thickness_var.get())
            base_mat = self.base_material_var.get()
            coeff = self.screw_in_coeff.get(base_mat, 1.0)
            l1 = coeff * d
            m = 0.8 * d
            S = 0.15 * d
            protrusion = 0.3 * d
            L_calc = H + l1 + m + S + protrusion
            L_std = min(self.standard_lengths, key=lambda x: abs(x - L_calc))
            messagebox.showinfo("Подбор длины",
                               f"Расчетная длина шпильки: {L_calc:.1f} мм\n"
                               f"Стандартная длина по ГОСТ: {L_std} мм\n"
                               f"Длина ввинчиваемого конца l1: {l1:.1f} мм\n"
                               f"Высота гайки: {m:.1f} мм\n"
                               f"Толщина шайбы: {S:.1f} мм")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подобрать длину:\n{str(e)}")

    def create_results_area(self, parent):
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        self.result_text = tk.Text(text_frame, height=20, width=60,
                                   font=('Courier', 10), wrap='word')
        self.result_text.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.result_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.tag_configure('header', foreground='navy', font=('Courier', 11, 'bold'))
        self.result_text.tag_configure('good', foreground='green')
        self.result_text.tag_configure('bad', foreground='red')
        self.result_text.tag_configure('warning', foreground='orange')
        self.result_text.tag_configure('value', foreground='blue')

    def calculate(self):
        try:
            # Получаем данные
            d = float(self.diameter_var.get())
            p = float(self.pitch_var.get())
            strength_class = self.class_var.get()
            base_mat = self.base_material_var.get()
            H = float(self.thickness_var.get())
            force = float(self.force_var.get())
            n_studs = self.count_var.get()
            load_type = self.load_type_var.get()
            conn_type = self.conn_type_var.get()
            material = self.material_var.get()

            # Коэффициент длины ввинчивания
            coeff = self.screw_in_coeff.get(base_mat, 1.0)
            l1 = coeff * d

            # Геометрия шпильки
            m = 0.8 * d          # высота гайки
            S = 0.15 * d         # толщина шайбы
            protrusion = 0.3 * d # запас резьбы + фаска

            L_calc = H + l1 + m + S + protrusion
            L_std = min(self.standard_lengths, key=lambda x: abs(x - L_calc))

            # Прочностной расчёт
            d1 = d - 1.22687 * p
            area = math.pi * (d1/2) ** 2

            sigma_t = self.strength_classes.get(strength_class, 240)

            # Коэффициент запаса с учётом типа соединения
            base_safety = self.safety_factors.get(load_type, 1.5)
            if conn_type == "Подвижное":
                safety_norm = base_safety * 1.3
            else:
                safety_norm = base_safety

            allowable_stress = sigma_t / safety_norm

            force_per_stud = force / n_studs
            tensile_stress = force_per_stud / area if area > 0 else 0
            safety_factor_tension = allowable_stress / tensile_stress if tensile_stress > 0 else 0

            # Срез (условно по стержню)
            shear_area = math.pi * (d/2) ** 2
            shear_stress = force_per_stud / shear_area if shear_area > 0 else 0
            allowable_shear = 0.6 * allowable_stress
            safety_factor_shear = allowable_shear / shear_stress if shear_stress > 0 else 0

            # Смятие (по присоединяемой детали)
            bearing_area = d * H
            bearing_stress = force_per_stud / bearing_area if bearing_area > 0 else 0
            bearing_allowable = self.bearing_allowable.get(material, 100)
            safety_factor_bearing = bearing_allowable / bearing_stress if bearing_stress > 0 else 0

            # Оценка прочности
            is_safe = (safety_factor_tension >= safety_norm and
                       safety_factor_shear >= 1.0 and
                       safety_factor_bearing >= 1.0)

            self.result_text.delete(1.0, tk.END)

            self.result_text.insert(tk.END, "="*70 + "\n", 'header')
            self.result_text.insert(tk.END, "           РАСЧЕТ ШПИЛЕЧНОГО СОЕДИНЕНИЯ\n", 'header')
            self.result_text.insert(tk.END, "="*70 + "\n\n", 'header')

            self.result_text.insert(tk.END, "📌 ГЕОМЕТРИЧЕСКИЕ ПАРАМЕТРЫ:\n", 'header')
            self.result_text.insert(tk.END, f"   Шпилька М{d}×{L_std}\n")
            self.result_text.insert(tk.END, f"   Гайка М{d} ГОСТ 5915-70\n")
            self.result_text.insert(tk.END, f"   Шайба {d} ГОСТ 11371-78\n")
            self.result_text.insert(tk.END, f"   Длина ввинчиваемого конца l1: {l1:.1f} мм (для {base_mat})\n")
            self.result_text.insert(tk.END, f"   Высота гайки m: {m:.1f} мм\n")
            self.result_text.insert(tk.END, f"   Толщина шайбы S: {S:.1f} мм\n")
            self.result_text.insert(tk.END, f"   Запас резьбы + фаска: {protrusion:.1f} мм\n")
            self.result_text.insert(tk.END, f"   Расчетная длина: {L_calc:.1f} мм\n")
            self.result_text.insert(tk.END, f"   Стандартная длина по ГОСТ: {L_std} мм\n\n")

            self.result_text.insert(tk.END, "🔧 ПАРАМЕТРЫ РЕЗЬБЫ:\n", 'header')
            self.result_text.insert(tk.END, f"   Наружный диаметр d: {d} мм\n")
            self.result_text.insert(tk.END, f"   Внутренний диаметр d1: {d1:.2f} мм\n")
            self.result_text.insert(tk.END, f"   Шаг резьбы P: {p} мм\n")
            self.result_text.insert(tk.END, f"   Площадь сечения (по резьбе): {area:.2f} мм²\n\n")

            self.result_text.insert(tk.END, "📊 ПРОЧНОСТНЫЕ ХАРАКТЕРИСТИКИ:\n", 'header')
            self.result_text.insert(tk.END, f"   Класс прочности: {strength_class}\n")
            self.result_text.insert(tk.END, f"   Предел текучести σт: {sigma_t} МПа\n")
            self.result_text.insert(tk.END, f"   Количество шпилек: {n_studs}\n")
            self.result_text.insert(tk.END, f"   Нагрузка на 1 шпильку: {force_per_stud:.0f} Н\n")
            self.result_text.insert(tk.END, f"   Тип нагрузки: {load_type}\n")
            self.result_text.insert(tk.END, f"   Тип соединения: {conn_type}\n")
            self.result_text.insert(tk.END, f"   Нормативный запас: {safety_norm:.2f}\n\n")

            self.result_text.insert(tk.END, "   РАСТЯЖЕНИЕ:\n")
            self.result_text.insert(tk.END, f"   • Напряжение σр: {tensile_stress:.2f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   • Допускаемое [σр]: {allowable_stress:.2f} МПа\n")
            self.result_text.insert(tk.END, f"   • Запас прочности: {safety_factor_tension:.2f}\n")
            if safety_factor_tension >= safety_norm:
                self.result_text.insert(tk.END, "   → Условие прочности выполнено\n", 'good')
            else:
                self.result_text.insert(tk.END, "   → Условие прочности НЕ выполнено\n", 'bad')

            self.result_text.insert(tk.END, "\n   СРЕЗ:\n")
            self.result_text.insert(tk.END, f"   • Напряжение τ: {shear_stress:.2f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   • Допускаемое [τ]: {allowable_shear:.2f} МПа\n")
            self.result_text.insert(tk.END, f"   • Запас прочности: {safety_factor_shear:.2f}\n")
            if safety_factor_shear >= 1.0:
                self.result_text.insert(tk.END, "   → Условие прочности выполнено\n", 'good')
            else:
                self.result_text.insert(tk.END, "   → Условие прочности НЕ выполнено\n", 'bad')

            self.result_text.insert(tk.END, f"\n   СМЯТИЕ (в материале детали – {material}):\n")
            self.result_text.insert(tk.END, f"   • Напряжение σсм: {bearing_stress:.2f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   • Допускаемое [σсм]: {bearing_allowable} МПа\n")
            self.result_text.insert(tk.END, f"   • Запас прочности: {safety_factor_bearing:.2f}\n")
            if safety_factor_bearing >= 1.0:
                self.result_text.insert(tk.END, "   → Условие прочности выполнено\n", 'good')
            else:
                self.result_text.insert(tk.END, "   → Условие прочности НЕ выполнено\n", 'bad')

            self.result_text.insert(tk.END, "\n" + "="*70 + "\n", 'header')
            if is_safe:
                self.result_text.insert(tk.END, "   ✅ СОЕДИНЕНИЕ ПРОЧНОЕ\n", 'good')
            else:
                self.result_text.insert(tk.END, "   ❌ СОЕДИНЕНИЕ НЕ ПРОЧНОЕ\n", 'bad')
                self.result_text.insert(tk.END, "      Рекомендации:\n", 'bad')
                if safety_factor_tension < safety_norm:
                    self.result_text.insert(tk.END, "      • Увеличить диаметр или класс прочности шпильки\n", 'bad')
                if safety_factor_shear < 1.0:
                    self.result_text.insert(tk.END, "      • Увеличить диаметр шпильки\n", 'bad')
                if safety_factor_bearing < 1.0:
                    self.result_text.insert(tk.END, "      • Увеличить толщину присоединяемой детали или количество шпилек\n", 'bad')
                    self.result_text.insert(tk.END, "      • Использовать материал детали с большей прочностью\n", 'bad')
            self.result_text.insert(tk.END, "="*70 + "\n", 'header')

        except Exception as e:
            messagebox.showerror("Ошибка расчета", f"Проверьте ввод:\n{str(e)}")

    def clear_results(self):
        self.result_text.delete(1.0, tk.END)

    def on_closing(self):
        if messagebox.askokcancel("Выход", "Закрыть программу?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudConnectionApp(root)
    root.mainloop()