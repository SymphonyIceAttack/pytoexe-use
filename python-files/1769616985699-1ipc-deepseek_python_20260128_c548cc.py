import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from PIL import Image, ImageTk

class MetalTensileTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Диаграмма растяжения металлов - Материаловедение")
        self.root.geometry("1400x900")
        self.root.configure(bg='white')
        
        # Данные для различных металлов (условные значения)
        self.metals_data = {
            "Ст.3": {
                "предел_упругости": 200,
                "предел_текучести": 240,
                "временное_сопротивление": 400,
                "относительное_удлинение": 25,
                "цвет": "#808080",
                "тип": "сталь"
            },
            "Ст.15": {
                "предел_упругости": 220,
                "предел_текучести": 280,
                "временное_сопротивление": 450,
                "относительное_удлинение": 22,
                "цвет": "#606060",
                "тип": "сталь"
            },
            "Ст.45": {
                "предел_упругости": 300,
                "предел_текучести": 360,
                "временное_сопротивление": 600,
                "относительное_удлинение": 16,
                "цвет": "#404040",
                "тип": "сталь"
            },
            "40Х13": {
                "предел_упругости": 500,
                "предел_текучести": 550,
                "временное_сопротивление": 750,
                "относительное_удлинение": 12,
                "цвет": "#2E8B57",  # морской зеленый
                "тип": "нержавеющая сталь",
                "модуль_упругости": 215000,
                "описание": "Мартенситная нержавеющая сталь. Высокая твердость и износостойкость. Применение: режущий инструмент, детали насосов, клапаны."
            },
            "08Х18Н10Т": {
                "предел_упругости": 200,
                "предел_текучести": 250,
                "временное_сопротивление": 500,
                "относительное_удлинение": 40,
                "цвет": "#4682B4",  # стальной синий
                "тип": "нержавеющая сталь",
                "модуль_упругости": 200000,
                "описание": "Аустенитная нержавеющая сталь. Высокая коррозионная стойкость, пластичность. Применение: химическая аппаратура, пищевая промышленность."
            },
            "Алюминий": {
                "предел_упругости": 70,
                "предел_текучести": 150,
                "временное_сопротивление": 200,
                "относительное_удлинение": 25,
                "цвет": "#D0D0D0",
                "тип": "цветной"
            },
            "Медь": {
                "предел_упругости": 60,
                "предел_текучести": 200,
                "временное_сопротивление": 300,
                "относительное_удлинение": 40,
                "цвет": "#B87333",
                "тип": "цветной"
            },
            "Титан": {
                "предел_упругости": 400,
                "предел_текучести": 600,
                "временное_сопротивление": 800,
                "относительное_удлинение": 15,
                "цвет": "#878681",
                "тип": "цветной"
            },
            "Натрий": {
                "предел_упругости": 10,
                "предел_текучести": 15,
                "временное_сопротивление": 20,
                "относительное_удлинение": 50,
                "цвет": "#FFD700",
                "тип": "жидкометаллический"
            },
            "Свинец": {
                "предел_упругости": 12,
                "предел_текучести": 18,
                "временное_сопротивление": 25,
                "относительное_удлинение": 45,
                "цвет": "#808080",
                "тип": "жидкометаллический"
            },
            "Свинец-Висмут": {
                "предел_упругости": 15,
                "предел_текучести": 22,
                "временное_сопротивление": 30,
                "относительное_удлинение": 40,
                "цвет": "#A9A9A9",
                "тип": "жидкометаллический"
            },
            "Литий": {
                "предел_упругости": 8,
                "предел_текучести": 12,
                "временное_сопротивление": 18,
                "относительное_удлинение": 60,
                "цвет": "#FFFFE0",
                "тип": "жидкометаллический"
            },
            "Цезий": {
                "предел_упругости": 5,
                "предел_текучести": 8,
                "временное_сопротивление": 12,
                "относительное_удлинение": 70,
                "цвет": "#FFA500",
                "тип": "жидкометаллический"
            }
        }
        
        # Переменные для управления растяжением
        self.current_strain = 0.0
        self.max_strain = 0.5
        self.animation_running = False
        self.custom_metals = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, 
                               text="Исследование механических свойств перспективных материалов для ЯЭУ с жидкометаллическим теплоносителем", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 15))
        
        selector_frame = ttk.Frame(main_frame)
        selector_frame.pack(fill=tk.X, pady=5)
        
        left_selector = ttk.Frame(selector_frame)
        left_selector.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_selector, text="Выберите металл:").pack(side=tk.LEFT, padx=5)
        
        self.metal_var = tk.StringVar(value="Ст.3")
        metal_combo = ttk.Combobox(left_selector, 
                                  textvariable=self.metal_var,
                                  values=list(self.metals_data.keys()),
                                  state="readonly",
                                  width=15)
        metal_combo.pack(side=tk.LEFT, padx=5)
        metal_combo.bind('<<ComboboxSelected>>', self.on_metal_change)
        
        right_selector = ttk.Frame(selector_frame)
        right_selector.pack(side=tk.RIGHT)
        
        ttk.Button(right_selector, 
                  text="Добавить металл", 
                  command=self.add_custom_metal).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(right_selector, 
                  text="Редактировать", 
                  command=self.edit_metal).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(right_selector, 
                  text="Удалить", 
                  command=self.delete_metal).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(right_selector, 
                  text="Справка", 
                  command=self.show_help).pack(side=tk.LEFT, padx=2)
        
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        graph_frame = ttk.LabelFrame(content_frame, text="Диаграмма растяжения", padding="10")
        graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.fig, self.ax = plt.subplots(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        image_frame = ttk.LabelFrame(right_frame, text="Образец металла", padding="10")
        image_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.metal_canvas = tk.Canvas(image_frame, width=350, height=250, bg='white', 
                                     highlightthickness=1, highlightbackground="gray")
        self.metal_canvas.pack(pady=10)
        
        control_frame = ttk.LabelFrame(right_frame, text="Управление растяжением", padding="10")
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Деформация образца:").pack(anchor=tk.W, pady=(0, 5))
        
        self.strain_var = tk.DoubleVar(value=0.0)
        strain_scale = ttk.Scale(control_frame, 
                                from_=0, 
                                to=self.max_strain * 100,
                                variable=self.strain_var,
                                orient=tk.HORIZONTAL,
                                length=300,
                                command=self.on_strain_change)
        strain_scale.pack(fill=tk.X, pady=5)
        
        strain_value_frame = ttk.Frame(control_frame)
        strain_value_frame.pack(fill=tk.X, pady=5)
        
        self.strain_label = ttk.Label(strain_value_frame, text="Деформация: 0.0%")
        self.strain_label.pack(side=tk.LEFT)
        
        self.stress_label = ttk.Label(strain_value_frame, text="Напряжение: 0 МПа")
        self.stress_label.pack(side=tk.RIGHT)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, 
                  text="Запустить анимацию", 
                  command=self.start_animation).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, 
                  text="Сброс", 
                  command=self.reset_animation).pack(side=tk.LEFT)
        
        # Добавляем информацию о выбранном металле
        info_frame = ttk.LabelFrame(right_frame, text="Информация о металле", padding="10")
        info_frame.pack(fill=tk.X, pady=10)
        
        self.info_label = ttk.Label(info_frame, text="", wraplength=300, justify=tk.LEFT)
        self.info_label.pack(anchor=tk.W)
        
        table_frame = ttk.LabelFrame(main_frame, text="Механические свойства", padding="10")
        table_frame.pack(fill=tk.X, pady=10)
        
        self.create_table(table_frame)
        
        self.update_plot()
        self.draw_metal_specimen()
    
    def create_table(self, parent):
        columns = ("Характеристика", "Значение", "Единица измерения")
        
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", height=5)
        
        self.tree.heading("Характеристика", text="Характеристика")
        self.tree.heading("Значение", text="Значение")
        self.tree.heading("Единица измерения", text="Единица измерения")
        
        self.tree.column("Характеристика", width=250)
        self.tree.column("Значение", width=150)
        self.tree.column("Единица измерения", width=150)
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_table_double_click)
    
    def on_table_double_click(self, event):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if item:
            column = self.tree.identify_column(event.x)
            if column == "#2":
                values = self.tree.item(item, "values")
                current_value = values[1]
                
                new_value = simpledialog.askstring("Редактирование", 
                                                  f"Введите новое значение для {values[0]}:",
                                                  initialvalue=current_value)
                if new_value is not None:
                    self.tree.item(item, values=(values[0], new_value, values[2]))
                    self.update_metal_from_table()
    
    def update_metal_from_table(self):
        metal_name = self.metal_var.get()
        if metal_name in self.metals_data:
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                characteristic = values[0]
                value = float(values[1]) if values[1].replace('.', '').isdigit() else values[1]
                
                if characteristic == "Предел упругости":
                    self.metals_data[metal_name]["предел_упругости"] = value
                elif characteristic == "Предел текучести":
                    self.metals_data[metal_name]["предел_текучести"] = value
                elif characteristic == "Временное сопротивление":
                    self.metals_data[metal_name]["временное_сопротивление"] = value
                elif characteristic == "Относительное удлинение":
                    self.metals_data[metal_name]["относительное_удлинение"] = value
            
            self.update_plot()
    
    def draw_metal_specimen(self):
        self.metal_canvas.delete("all")
        
        width = 300
        height = 60
        x_center = 175
        y_center = 125
        
        stretch_factor = 1.0 + self.current_strain
        
        stretched_width = width * stretch_factor
        
        metal_data = self.metals_data.get(self.metal_var.get(), self.metals_data["Ст.3"])
        metal_color = metal_data.get("цвет", "#808080")
        
        grip_width = 40
        neck_width = max(20, 40 - self.current_strain * 30)
        
        # Левый захват
        self.metal_canvas.create_rectangle(
            x_center - stretched_width/2 - grip_width, y_center - height/2,
            x_center - stretched_width/2, y_center + height/2,
            fill="#505050",
            outline="black",
            width=2
        )
        
        # Левое плечо образца
        self.metal_canvas.create_rectangle(
            x_center - stretched_width/2, y_center - height/2,
            x_center - stretched_width/2 + 20, y_center + height/2,
            fill=metal_color,
            outline="black",
            width=1
        )
        
        # Шейка образца
        neck_length = stretched_width * 0.4
        self.metal_canvas.create_rectangle(
            x_center - neck_length/2, y_center - neck_width/2,
            x_center + neck_length/2, y_center + neck_width/2,
            fill=metal_color,
            outline="black",
            width=1
        )
        
        # Правое плечо образца
        self.metal_canvas.create_rectangle(
            x_center + stretched_width/2 - 20, y_center - height/2,
            x_center + stretched_width/2, y_center + height/2,
            fill=metal_color,
            outline="black",
            width=1
        )
        
        # Правый захват
        self.metal_canvas.create_rectangle(
            x_center + stretched_width/2, y_center - height/2,
            x_center + stretched_width/2 + grip_width, y_center + height/2,
            fill="#505050",
            outline="black",
            width=2
        )
        
        # Метки для измерения деформации
        for i in range(1, 4):
            pos = x_center - stretched_width/2 + (stretched_width * i / 4)
            self.metal_canvas.create_line(
                pos, y_center - height/2 - 5,
                pos, y_center + height/2 + 5,
                fill="red", width=1, dash=(4, 2)
            )
        
        # Текст с деформацией
        self.metal_canvas.create_text(
            x_center, 230,
            text=f"Деформация: {self.current_strain*100:.1f}%",
            font=('Arial', 10, 'bold')
        )
        
        # Стрелки нагрузки
        arrow_len = 30
        self.metal_canvas.create_line(
            x_center - stretched_width/2 - grip_width - 10, y_center,
            x_center - stretched_width/2 - grip_width - arrow_len, y_center,
            arrow=tk.FIRST, width=2
        )
        
        self.metal_canvas.create_line(
            x_center + stretched_width/2 + grip_width + 10, y_center,
            x_center + stretched_width/2 + grip_width + arrow_len, y_center,
            arrow=tk.LAST, width=2
        )
    
    def on_strain_change(self, value):
        if not self.animation_running:
            self.current_strain = float(value) / 100.0
            self.update_display()
    
    def on_metal_change(self, event=None):
        self.reset_animation()
        self.update_plot()
        self.update_metal_info()
    
    def update_metal_info(self):
        metal_name = self.metal_var.get()
        metal_data = self.metals_data.get(metal_name, {})
        
        info_text = f"Металл: {metal_name}\nТип: {metal_data.get('тип', 'не указан')}"
        
        if "описание" in metal_data:
            info_text += f"\n\nОписание:\n{metal_data['описание']}"
        
        self.info_label.config(text=info_text)
    
    def update_display(self):
        self.strain_label.config(text=f"Деформация: {self.current_strain*100:.1f}%")
        
        if hasattr(self, 'current_curve_data'):
            strain, stress = self.current_curve_data
            idx = np.abs(strain * 100 - self.current_strain * 100).argmin()
            current_stress = stress[idx]
            self.stress_label.config(text=f"Напряжение: {current_stress:.0f} МПа")
        
        self.draw_metal_specimen()
        self.update_plot_point()
    
    def update_plot_point(self):
        if hasattr(self, 'current_curve_data'):
            strain, stress = self.current_curve_data
            
            idx = np.abs(strain * 100 - self.current_strain * 100).argmin()
            current_stress = stress[idx]
            
            self.ax.clear()
            
            smooth_strain = np.linspace(0, max(strain), 500)
            smooth_stress = np.interp(smooth_strain, strain, stress)
            
            metal_data = self.metals_data[self.metal_var.get()]
            metal_color = metal_data.get("цвет", "#808080")
            
            self.ax.plot(smooth_strain * 100, smooth_stress, '-', color=metal_color, 
                        linewidth=2.5, label=self.metal_var.get(), alpha=0.8)
            
            self.ax.axhline(y=metal_data["предел_упругости"], color='r', linestyle='--', 
                           alpha=0.7, label=f'Предел упругости ({metal_data["предел_упругости"]} МПа)')
            self.ax.axhline(y=metal_data["предел_текучести"], color='g', linestyle='--', 
                           alpha=0.7, label=f'Предел текучести ({metal_data["предел_текучести"]} МПа)')
            self.ax.axhline(y=metal_data["временное_сопротивление"], color='orange', linestyle='--', 
                           alpha=0.7, label=f'Временное сопротивление ({metal_data["временное_сопротивление"]} МПа)')
            
            self.ax.plot(self.current_strain * 100, current_stress, 'ro', markersize=10, 
                        markeredgecolor='darkred', markeredgewidth=2,
                        label=f'Текущее состояние ({self.current_strain*100:.1f}%, {current_stress:.0f} МПа)')
            
            self.ax.set_xlabel('Относительное удлинение, %', fontsize=12)
            self.ax.set_ylabel('Напряжение, МПа', fontsize=12)
            self.ax.set_title(f'Диаграмма растяжения: {self.metal_var.get()}', fontsize=14, fontweight='bold')
            self.ax.grid(True, alpha=0.3)
            self.ax.legend()
            max_strain_display = max(metal_data["относительное_удлинение"] * 1.2, max(strain) * 100 + 5)
            self.ax.set_xlim(0, max_strain_display)
            
            self.canvas.draw()
    
    def generate_tensile_curve(self, metal_data):
        elastic_limit = metal_data["предел_упругости"]
        yield_strength = metal_data["предел_текучести"]
        tensile_strength = metal_data["временное_сопротивление"]
        elongation = metal_data["относительное_удлинение"]
        
        # Используем модуль упругости из данных или стандартное значение
        E = metal_data.get("модуль_упругости", 210000)
        
        elastic_strain = np.linspace(0, elastic_limit/E, 300)
        elastic_stress = elastic_strain * E
        
        yield_plateau_length = 0.002
        
        if yield_strength > elastic_limit:
            plastic_strain_1 = np.linspace(elastic_strain[-1], 
                                         elastic_strain[-1] + yield_plateau_length, 100)
            plastic_stress_1 = np.linspace(elastic_limit, yield_strength, 100)
        else:
            plastic_strain_1 = np.array([elastic_strain[-1]])
            plastic_stress_1 = np.array([yield_strength])
        
        strengthening_strain_length = elongation/100 - yield_plateau_length if yield_strength > elastic_limit else elongation/100
        strengthening_strain = np.linspace(plastic_strain_1[-1], 
                                         plastic_strain_1[-1] + strengthening_strain_length, 400)
        
        t = (strengthening_strain - strengthening_strain[0]) / (strengthening_strain[-1] - strengthening_strain[0])
        sigmoid = 1 / (1 + np.exp(-12 * (t - 0.5)))
        plastic_stress_2 = yield_strength + (tensile_strength - yield_strength) * sigmoid
        
        strain = np.concatenate([elastic_strain, plastic_strain_1, strengthening_strain])
        stress = np.concatenate([elastic_stress, plastic_stress_1, plastic_stress_2])
        
        return strain, stress
    
    def update_plot(self, event=None):
        selected_metal = self.metal_var.get()
        metal_data = self.metals_data[selected_metal]
        
        self.ax.clear()
        
        strain, stress = self.generate_tensile_curve(metal_data)
        self.current_curve_data = (strain, stress)
        
        smooth_strain = np.linspace(0, max(strain), 500)
        smooth_stress = np.interp(smooth_strain, strain, stress)
        
        metal_color = metal_data.get("цвет", "#808080")
        
        self.ax.plot(smooth_strain * 100, smooth_stress, '-', color=metal_color, 
                    linewidth=2.5, label=selected_metal, alpha=0.8)
        
        self.ax.axhline(y=metal_data["предел_упругости"], color='r', linestyle='--', 
                       alpha=0.7, label=f'Предел упругости ({metal_data["предел_упругости"]} МПа)')
        self.ax.axhline(y=metal_data["предел_текучести"], color='g', linestyle='--', 
                       alpha=0.7, label=f'Предел текучести ({metal_data["предел_текучести"]} МПа)')
        self.ax.axhline(y=metal_data["временное_сопротивление"], color='orange', linestyle='--', 
                       alpha=0.7, label=f'Временное сопротивление ({metal_data["временное_сопротивление"]} МПа)')
        
        self.ax.set_xlabel('Относительное удлинение, %', fontsize=12)
        self.ax.set_ylabel('Напряжение, МПа', fontsize=12)
        self.ax.set_title(f'Диаграмма растяжения: {selected_metal}', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        max_strain_display = max(metal_data["относительное_удлинение"] * 1.2, max(strain) * 100 + 5)
        self.ax.set_xlim(0, max_strain_display)
        
        self.update_table(metal_data)
        self.update_metal_info()
        
        self.update_display()
    
    def update_table(self, metal_data):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получаем модуль упругости из данных или используем стандартное значение
        modulus = metal_data.get("модуль_упругости", 210000)
        
        data = [
            ("Предел упругости", f"{metal_data['предел_упругости']}", "МПа"),
            ("Предел текучести", f"{metal_data['предел_текучести']}", "МПа"),
            ("Временное сопротивление", f"{metal_data['временное_сопротивление']}", "МПа"),
            ("Относительное удлинение", f"{metal_data['относительное_удлинение']}", "%"),
            ("Модуль упругости", f"{modulus}", "МПа")
        ]
        
        for item in data:
            self.tree.insert("", tk.END, values=item)
    
    def add_custom_metal(self):
        dialog = CustomMetalDialog(self.root)
        if dialog.result:
            name, properties = dialog.result
            if name and name not in self.metals_data:
                self.metals_data[name] = properties
                metal_combo = self.root.nametowidget(self.metal_var.trace_info()[0][0])
                metal_combo['values'] = list(self.metals_data.keys())
                self.metal_var.set(name)
                self.on_metal_change()
            else:
                messagebox.showerror("Ошибка", "Металл с таким именем уже существует или имя не указано")
    
    def edit_metal(self):
        metal_name = self.metal_var.get()
        if metal_name in self.metals_data:
            dialog = CustomMetalDialog(self.root, metal_name, self.metals_data[metal_name])
            if dialog.result:
                name, properties = dialog.result
                if name != metal_name and name in self.metals_data:
                    messagebox.showerror("Ошибка", "Металл с таким именем уже существует")
                else:
                    if name != metal_name:
                        del self.metals_data[metal_name]
                    
                    self.metals_data[name] = properties
                    
                    metal_combo = self.root.nametowidget(self.metal_var.trace_info()[0][0])
                    metal_combo['values'] = list(self.metals_data.keys())
                    self.metal_var.set(name)
                    self.on_metal_change()
    
    def delete_metal(self):
        metal_name = self.metal_var.get()
        standard_metals = ["Ст.3", "Ст.15", "Ст.45", "40Х13", "08Х18Н10Т", "Алюминий", "Медь", 
                          "Титан", "Натрий", "Свинец", "Свинец-Висмут", "Литий", "Цезий"]
        
        if metal_name in standard_metals:
            messagebox.showerror("Ошибка", "Нельзя удалить стандартный металл")
        elif metal_name in self.metals_data:
            if messagebox.askyesno("Подтверждение", f"Удалить металл '{metal_name}'?"):
                del self.metals_data[metal_name]
                metal_combo = self.root.nametowidget(self.metal_var.trace_info()[0][0])
                metal_combo['values'] = list(self.metals_data.keys())
                self.metal_var.set(list(self.metals_data.keys())[0])
                self.on_metal_change()
    
    def show_help(self):
        help_text = """
ФОРМУЛЫ И РАСЧЕТЫ ДИАГРАММЫ РАСТЯЖЕНИЯ

1. Закон Гука (упругая деформация):
   σ = E × ε
   где: σ - напряжение [МПа]
         E - модуль упругости (210000 МПа для стали)
         ε - относительная деформация

2. Предел упругости (σ_y):
   Максимальное напряжение, при котором материал возвращается к исходной форме после снятия нагрузки.

3. Предел текучести (σ_t):
   Напряжение, при котором материал начинает пластически деформироваться без увеличения нагрузки.

4. Временное сопротивление (σ_b):
   Максимальное напряжение, которое выдерживает материал перед разрушением.

5. Относительное удлинение (δ):
   δ = (L - L₀) / L₀ × 100%
   где: L - конечная длина образца
         L₀ - начальная длина образца

6. Условная диаграмма растяжения:
   - Упругая область: линейная зависимость
   - Пластическая область: площадка текучести
   - Область упрочнения: плавный рост напряжения
   - Образование шейки: локализация деформации

ХАРАКТЕРИСТИКИ СТАЛЕЙ:
- Ст.3: Низкоуглеродистая сталь общего назначения
- Ст.15: Углеродистая сталь с повышенной прочностью
- Ст.45: Среднеуглеродистая конструкционная сталь
- 40Х13: Мартенситная нержавеющая сталь (AISI 420). Высокая твердость и износостойкость.
- 08Х18Н10Т: Аустенитная нержавеющая сталь (AISI 321). Высокая коррозионная стойкость.

ЖИДКОМЕТАЛЛИЧЕСКИЕ ТЕПЛОНОСИТЕЛИ:
- Натрий: Высокая пластичность, низкая прочность
- Свинец: Мягкий металл с хорошей пластичностью
- Свинец-Висмут: Эвтектический сплав для ЯЭУ
- Литий: Щелочной металл с высокой пластичностью
- Цезий: Самый мягкий металл, очень высокая пластичность

ТИПЫ НЕРЖАВЕЮЩИХ СТАЛЕЙ:
1. Мартенситные (40Х13): 
   - Магнитные
   - Высокая твердость
   - Умеренная коррозионная стойкость
   - Для режущего инструмента, деталей насосов

2. Аустенитные (08Х18Н10Т):
   - Немагнитные
   - Высокая коррозионная стойкость
   - Хорошая пластичность
   - Для химической аппаратуры, пищевой промышленности
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Справка по диаграмме растяжения")
        help_window.geometry("600x500")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10, font=('Arial', 10))
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(help_window, text="Закрыть", command=help_window.destroy).pack(pady=10)
    
    def start_animation(self):
        if self.animation_running:
            return
            
        self.animation_running = True
        self.current_strain = 0.0
        
        def animate_step():
            if self.current_strain < self.max_strain and self.animation_running:
                self.current_strain += 0.002
                self.strain_var.set(self.current_strain * 100)
                self.update_display()
                self.root.after(20, animate_step)
            else:
                self.animation_running = False
        
        animate_step()
    
    def reset_animation(self):
        self.animation_running = False
        self.current_strain = 0.0
        self.strain_var.set(0.0)
        self.update_display()
    
    def run(self):
        self.root.mainloop()


class CustomMetalDialog(simpledialog.Dialog):
    def __init__(self, parent, title=None, metal_data=None):
        self.metal_data = metal_data or {}
        self.result = None
        super().__init__(parent, title=title or "Добавить металл")
    
    def body(self, master):
        ttk.Label(master, text="Название металла:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.metal_data.get("name", ""))
        self.name_entry = ttk.Entry(master, textvariable=self.name_var, width=20)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(master, text="Предел упругости (МПа):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.elastic_var = tk.StringVar(value=self.metal_data.get("предел_упругости", "200"))
        ttk.Entry(master, textvariable=self.elastic_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(master, text="Предел текучести (МПа):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.yield_var = tk.StringVar(value=self.metal_data.get("предел_текучести", "240"))
        ttk.Entry(master, textvariable=self.yield_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(master, text="Временное сопротивление (МПа):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.tensile_var = tk.StringVar(value=self.metal_data.get("временное_сопротивление", "400"))
        ttk.Entry(master, textvariable=self.tensile_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(master, text="Относительное удлинение (%):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.elongation_var = tk.StringVar(value=self.metal_data.get("относительное_удлинение", "25"))
        ttk.Entry(master, textvariable=self.elongation_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(master, text="Модуль упругости (МПа):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.modulus_var = tk.StringVar(value=self.metal_data.get("модуль_упругости", "210000"))
        ttk.Entry(master, textvariable=self.modulus_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(master, text="Цвет (hex):").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.color_var = tk.StringVar(value=self.metal_data.get("цвет", "#808080"))
        ttk.Entry(master, textvariable=self.color_var, width=10).grid(row=6, column=1, sticky=tk.W, pady=5, padx=5)
        
        return self.name_entry
    
    def validate(self):
        try:
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название металла")
                return False
            
            float(self.elastic_var.get())
            float(self.yield_var.get())
            float(self.tensile_var.get())
            float(self.elongation_var.get())
            float(self.modulus_var.get())
            
            color = self.color_var.get()
            if not color.startswith("#") or len(color) != 7:
                messagebox.showerror("Ошибка", "Цвет должен быть в формате #RRGGBB")
                return False
            
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность числовых значений")
            return False
    
    def apply(self):
        name = self.name_var.get().strip()
        properties = {
            "предел_упругости": float(self.elastic_var.get()),
            "предел_текучести": float(self.yield_var.get()),
            "временное_сопротивление": float(self.tensile_var.get()),
            "относительное_удлинение": float(self.elongation_var.get()),
            "модуль_упругости": float(self.modulus_var.get()),
            "цвет": self.color_var.get(),
            "тип": "пользовательский"
        }
        self.result = (name, properties)


if __name__ == "__main__":
    app = MetalTensileTest()
    app.run()