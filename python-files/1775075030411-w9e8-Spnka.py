import tkinter as tk
from tkinter import ttk, messagebox
import math

class KeyConnectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Расчет шпоночного соединения по ГОСТ")
        self.root.geometry("1200x750")
        self.root.resizable(True, True)
        self.root.minsize(1000, 650)

        self.center_window()
        self.setup_style()

        # Словарь размеров шпонок по ГОСТ (диапазон диаметров: (b, h, t1, t2))
        self.key_sizes = {
            (6, 8): (2, 2, 1.2, 1.0),
            (8, 10): (3, 3, 1.8, 1.4),
            (10, 12): (4, 4, 2.5, 1.8),
            (12, 17): (5, 5, 3.0, 2.3),
            (17, 22): (6, 6, 3.5, 2.8),
            (22, 30): (8, 7, 4.0, 3.3),
            (30, 38): (10, 8, 5.0, 3.3),
            (38, 44): (12, 8, 5.0, 3.3),
            (44, 50): (14, 9, 5.5, 3.8),
            (50, 58): (16, 10, 6.0, 4.3),
            (58, 65): (18, 11, 7.0, 4.4),
            (65, 75): (20, 12, 7.5, 4.9),
            (75, 85): (22, 14, 9.0, 5.4),
            (85, 95): (25, 14, 9.0, 5.4),
            (95, 110): (28, 16, 10.0, 6.4),
        }

        # Допускаемые напряжения для материалов шпонки и ступицы (МПа)
        self.stress_values = {
            "Сталь 45": 120,
            "Сталь 40Х": 150,
            "Сталь 20": 100,
            "Сталь 3": 80,
            "Чугун СЧ20": 60,
            "Алюминий Д16": 40
        }

        # Коэффициенты неравномерности нагрузки для разного количества шпонок
        self.load_coeffs = {
            1: 1.0,
            2: 0.9,   # для симметричного расположения (180°)
            3: 0.8,   # для равномерного по окружности (120°)
            4: 0.75   # для 90°
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
        style.configure('SubHeader.TLabel', font=('Arial', 10, 'bold'), foreground='purple')

    def create_widgets(self):
        # Заголовок
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(title_frame, text="🔧 РАСЧЕТ ШПОНОЧНОГО СОЕДИНЕНИЯ", style='Title.TLabel').pack()
        ttk.Label(title_frame, text="ГОСТ 23360-78 - Шпонки призматические", font=('Arial', 10)).pack()

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

        # Кнопки внизу
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=20, pady=10)

        self.calc_btn = tk.Button(button_frame, text="РАССЧИТАТЬ", bg='#4CAF50', fg='white',
                                   font=('Arial', 12, 'bold'), command=self.calculate, padx=20, pady=5)
        self.calc_btn.pack(side='left', padx=5)

        self.clear_btn = tk.Button(button_frame, text="ОЧИСТИТЬ", bg='#f44336', fg='white',
                                    font=('Arial', 10), command=self.clear_results, padx=15, pady=5)
        self.clear_btn.pack(side='left', padx=5)

        self.gost_btn = tk.Button(button_frame, text="ПОДОБРАТЬ ПО ГОСТ", bg='#2196F3', fg='white',
                                   font=('Arial', 10), command=self.suggest_gost_size, padx=15, pady=5)
        self.gost_btn.pack(side='left', padx=5)

    def create_input_fields(self, parent):
        row = 0

        # Диаметр вала
        ttk.Label(parent, text="Диаметр вала d (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.diameter_var = tk.StringVar(value="30")
        self.diameter_entry = ttk.Entry(parent, textvariable=self.diameter_var, width=10)
        self.diameter_entry.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        self.diameter_entry.bind('<KeyRelease>', self.update_key_sizes)
        row += 1

        # Размеры шпонки (b×h)
        ttk.Label(parent, text="Сечение шпонки b×h (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.key_size_var = tk.StringVar(value="8×7")
        ttk.Entry(parent, textvariable=self.key_size_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Глубина паза в валу
        ttk.Label(parent, text="Глубина паза в валу t1 (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.t1_var = tk.StringVar(value="4.0")
        ttk.Entry(parent, textvariable=self.t1_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Глубина паза в ступице
        ttk.Label(parent, text="Глубина паза в ступице t2 (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.t2_var = tk.StringVar(value="3.3")
        ttk.Entry(parent, textvariable=self.t2_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Количество шпонок
        ttk.Label(parent, text="Количество шпонок:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.key_count_var = tk.IntVar(value=1)
        spinbox = tk.Spinbox(parent, from_=1, to=4, textvariable=self.key_count_var, width=5)
        spinbox.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Схема расположения (для >1 шпонки)
        ttk.Label(parent, text="Схема расположения:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.layout_var = tk.StringVar(value="Симметрично (180°)")
        self.layout_combo = ttk.Combobox(parent, textvariable=self.layout_var,
                                         values=["Симметрично (180°)", "Под 90°", "Под 120°", "Рядом (0°)"],
                                         state='readonly', width=20)
        self.layout_combo.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Длина шпонки
        ttk.Label(parent, text="Длина шпонки l (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.length_var = tk.StringVar(value="50")
        ttk.Entry(parent, textvariable=self.length_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Длина ступицы
        ttk.Label(parent, text="Длина ступицы Lст (мм):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.hub_length_var = tk.StringVar(value="60")
        ttk.Entry(parent, textvariable=self.hub_length_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Крутящий момент
        ttk.Label(parent, text="Крутящий момент T (Н·м):", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.torque_var = tk.StringVar(value="200")
        ttk.Entry(parent, textvariable=self.torque_var, width=10).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Материал шпонки
        ttk.Label(parent, text="Материал шпонки:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.material_var = tk.StringVar(value="Сталь 45")
        ttk.Combobox(parent, textvariable=self.material_var,
                     values=list(self.stress_values.keys()),
                     state='readonly', width=15).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

        # Материал ступицы
        ttk.Label(parent, text="Материал ступицы:", style='Header.TLabel').grid(row=row, column=0, sticky='w', pady=5)
        self.hub_material_var = tk.StringVar(value="Сталь 45")
        hub_materials = list(self.stress_values.keys()) + ["Чугун", "Бронза", "Дюралюминий"]
        ttk.Combobox(parent, textvariable=self.hub_material_var,
                     values=hub_materials,
                     state='readonly', width=15).grid(row=row, column=1, sticky='w', padx=10, pady=5)
        row += 1

    def update_key_sizes(self, event=None):
        try:
            d = float(self.diameter_var.get())
            for (d_min, d_max), (b, h, t1, t2) in self.key_sizes.items():
                if d_min <= d < d_max:
                    self.key_size_var.set(f"{b}×{h}")
                    self.t1_var.set(str(t1))
                    self.t2_var.set(str(t2))
                    return
            # если диаметр вне таблицы, оставляем введённые значения
        except:
            pass

    def suggest_gost_size(self):
        try:
            d = float(self.diameter_var.get())
            for (d_min, d_max), (b, h, t1, t2) in self.key_sizes.items():
                if d_min <= d < d_max:
                    self.key_size_var.set(f"{b}×{h}")
                    self.t1_var.set(str(t1))
                    self.t2_var.set(str(t2))
                    messagebox.showinfo("Подбор по ГОСТ", f"Рекомендуемая шпонка {b}×{h}")
                    return
            messagebox.showwarning("Подбор по ГОСТ", "Нет точного соответствия. Введите размеры вручную.")
        except:
            messagebox.showerror("Ошибка", "Введите корректный диаметр")

    def create_results_area(self, parent):
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill='both', expand=True)

        self.result_text = tk.Text(text_frame, height=18, width=60,
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
            d = float(self.diameter_var.get())
            b, h = map(int, self.key_size_var.get().split('×'))
            t1 = float(self.t1_var.get())
            t2 = float(self.t2_var.get())
            key_count = self.key_count_var.get()
            layout = self.layout_var.get()
            l = float(self.length_var.get())
            L_hub = float(self.hub_length_var.get())
            T = float(self.torque_var.get())
            material = self.material_var.get()
            hub_material = self.hub_material_var.get()

            # Коэффициент неравномерности в зависимости от количества и расположения
            if key_count == 1:
                load_factor = 1.0
            elif key_count == 2:
                if "180°" in layout:
                    load_factor = 0.9
                elif "90°" in layout:
                    load_factor = 0.75
                else:
                    load_factor = 0.6
            elif key_count == 3:
                if "120°" in layout:
                    load_factor = 0.8
                else:
                    load_factor = 0.6
            else:  # 4 шпонки
                if "90°" in layout:
                    load_factor = 0.75
                else:
                    load_factor = 0.6

            # Рабочая длина
            lp = l - b
            if lp <= 0:
                messagebox.showerror("Ошибка", "Длина шпонки должна быть больше ширины")
                return

            # Рабочая высота шпонки (высота площадки смятия)
            h_work = h - t1
            if h_work <= 0:
                h_work = h / 2  # запас на случай ошибки ввода

            # Напряжение смятия (одна шпонка)
            stress_crush_one = (2 * T * 1000) / (d * h_work * lp) if lp > 0 else 0
            # Суммарное с учётом количества и неравномерности
            stress_crush = stress_crush_one / (key_count * load_factor)

            # Напряжение среза (одна шпонка)
            stress_shear_one = (2 * T * 1000) / (d * b * lp) if lp > 0 else 0
            stress_shear = stress_shear_one / (key_count * load_factor)

            # Допускаемые напряжения
            allow_crush = self.stress_values.get(material, 100)  # для смятия
            allow_shear = 0.6 * allow_crush  # для среза (ориентировочно)

            # Корректировка по материалу ступицы (если он менее прочен)
            hub_factor = 1.0
            if "Чугун" in hub_material:
                hub_factor = 0.7
            elif "Бронза" in hub_material:
                hub_factor = 0.8
            elif "Дюралюминий" in hub_material:
                hub_factor = 0.5
            else:
                hub_factor = self.stress_values.get(hub_material, 100) / allow_crush
                hub_factor = min(1.0, hub_factor)

            allow_crush_final = allow_crush * hub_factor
            allow_shear_final = allow_shear * hub_factor

            # Коэффициенты запаса
            safety_crush = allow_crush_final / stress_crush if stress_crush > 0 else 0
            safety_shear = allow_shear_final / stress_shear if stress_shear > 0 else 0

            # Очистка и вывод
            self.result_text.delete(1.0, tk.END)

            self.result_text.insert(tk.END, "="*70 + "\n", 'header')
            self.result_text.insert(tk.END, "           РАСЧЕТ ШПОНОЧНОГО СОЕДИНЕНИЯ\n", 'header')
            self.result_text.insert(tk.END, "="*70 + "\n\n", 'header')

            self.result_text.insert(tk.END, "📌 ГЕОМЕТРИЧЕСКИЕ ПАРАМЕТРЫ:\n", 'header')
            self.result_text.insert(tk.END, f"   Диаметр вала: {d} мм\n")
            self.result_text.insert(tk.END, f"   Шпонка: {b}×{h}×{l} мм (ГОСТ 23360-78)\n")
            self.result_text.insert(tk.END, f"   Количество шпонок: {key_count}\n")
            self.result_text.insert(tk.END, f"   Схема расположения: {layout}\n")
            self.result_text.insert(tk.END, f"   Длина ступицы: {L_hub} мм\n")
            self.result_text.insert(tk.END, f"   Глубина паза в валу t1: {t1} мм\n")
            self.result_text.insert(tk.END, f"   Глубина паза в ступице t2: {t2} мм\n")
            self.result_text.insert(tk.END, f"   Рабочая длина одной шпонки: {lp:.1f} мм\n\n")

            self.result_text.insert(tk.END, "📊 ПРОЧНОСТНЫЕ ХАРАКТЕРИСТИКИ:\n", 'header')
            self.result_text.insert(tk.END, f"   Материал шпонки: {material}\n")
            self.result_text.insert(tk.END, f"   Материал ступицы: {hub_material}\n")
            self.result_text.insert(tk.END, f"   Крутящий момент T: {T} Н·м\n")
            self.result_text.insert(tk.END, f"   Коэффициент неравномерности: {load_factor:.2f}\n\n")

            self.result_text.insert(tk.END, f"   Напряжение смятия (расчетное): {stress_crush:.1f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   Допускаемое напряжение смятия: {allow_crush_final:.1f} МПа\n")
            self.result_text.insert(tk.END, f"   Запас прочности по смятию: {safety_crush:.2f}\n")
            if safety_crush >= 1:
                self.result_text.insert(tk.END, "   → Прочность на смятие обеспечена\n", 'good')
            else:
                self.result_text.insert(tk.END, "   → Прочность на смятие НЕ обеспечена\n", 'bad')

            self.result_text.insert(tk.END, f"\n   Напряжение среза (расчетное): {stress_shear:.1f} МПа\n", 'value')
            self.result_text.insert(tk.END, f"   Допускаемое напряжение среза: {allow_shear_final:.1f} МПа\n")
            self.result_text.insert(tk.END, f"   Запас прочности по срезу: {safety_shear:.2f}\n")
            if safety_shear >= 1:
                self.result_text.insert(tk.END, "   → Прочность на срез обеспечена\n", 'good')
            else:
                self.result_text.insert(tk.END, "   → Прочность на срез НЕ обеспечена\n", 'bad')

            # Общая оценка
            self.result_text.insert(tk.END, "\n" + "="*70 + "\n", 'header')
            if safety_crush >= 1 and safety_shear >= 1:
                self.result_text.insert(tk.END, "   ✅ СОЕДИНЕНИЕ ПРОЧНОЕ\n", 'good')
            else:
                self.result_text.insert(tk.END, "   ❌ СОЕДИНЕНИЕ НЕ ПРОЧНОЕ\n", 'bad')
                if safety_crush < 1:
                    self.result_text.insert(tk.END, "      Увеличьте длину шпонки или количество шпонок\n", 'bad')
                if safety_shear < 1:
                    self.result_text.insert(tk.END, "      Увеличьте сечение шпонки\n", 'bad')

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
    app = KeyConnectionApp(root)
    root.mainloop()