import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

class SolarCalculator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Калькулятор эффективности ФЭМ")
        self.root.geometry("1100x800")
        self.root.configure(bg="#4A6572")
        
        matplotlib.rcParams.update({
            'font.size': 9,
            'axes.titlesize': 11,
            'axes.labelsize': 10,
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            'legend.fontsize': 9,
            'figure.titlesize': 12
        })
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#4A6572', foreground='#ECF0F1', font=('Arial', 10))
        style.configure('TFrame', background='#4A6572')
        style.configure('TButton', font=('Arial', 10, 'bold'))
        style.configure('TLabelframe', background='#4A6572', foreground='#ECF0F1')
        style.configure('TLabelframe.Label', font=('Arial', 10, 'bold'), background='#4A6572', foreground='#F1C40F')
        style.configure('TNotebook', background='#4A6572')
        style.configure('TNotebook.Tab', background='#3498DB', foreground='white')
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.main_frame = ttk.Frame(self.notebook)
        self.viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text='Основной расчет')
        self.notebook.add(self.viz_frame, text='Визуализация')
        
        self.insolation_data = {
            "Санкт-Петербург": 2.8, "Москва": 2.63, "Казань": 3.06,
            "Ростов-на-Дону": 3.45, "Нижний Новгород": 2.91,
            "Екатеринбург": 2.87, "Новосибирск": 2.91,
            "Хабаровск": 3.64, "Краснодар": 4.02
        }
        
        self.tariff_data = {
            "Москва": 7.87, "Санкт-Петербург": 6.97, "Краснодар": 12.00,
            "Екатеринбург": 7.64, "Новосибирск": 4.12, "Нижний Новгород": 5.47,
            "Хабаровск": 7.57, "Ростов-на-Дону": 7.87, "Казань": 5.94
        }
        
        self.panel_types = {
            "Монокристаллические": {"price": 60000, "lifetime": 25, "efficiency": 0.22, "color": "#E74C3C"},
            "Поликристаллические": {"price": 45000, "lifetime": 20, "efficiency": 0.18, "color": "#3498DB"},
            "Тонкоплёночные": {"price": 35000, "lifetime": 15, "efficiency": 0.15, "color": "#2ECC71"}
        }
        
        self.calculation_results = {}
        self.create_main_tab()
        self.create_viz_tab()
    
    def create_main_tab(self):
        main_frame = ttk.Frame(self.main_frame, padding="15")
        main_frame.pack(fill='both', expand=True)
        
        title_frame = tk.Frame(main_frame, bg="#4A6572")
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky='ew')
        
        title = tk.Label(title_frame, text="КАЛЬКУЛЯТОР ЭФФЕКТИВНОСТИ ФЭМ", 
                        font=("Arial", 16, "bold"), bg="#4A6572", fg="#F1C40F")
        title.pack()
        
        subtitle = tk.Label(title_frame, text="Расчет экономической эффективности фотоэлектрических модулей", 
                           font=("Arial", 10), bg="#4A6572", fg="#ECF0F1")
        subtitle.pack(pady=(5, 0))
        
        container = tk.Frame(main_frame, bg="#4A6572")
        container.grid(row=1, column=0, columnspan=3, sticky='nsew', pady=(0, 10))
        
        left_frame = tk.Frame(container, bg="#4A6572")
        left_frame.pack(side='left', fill='both', expand=False, padx=(0, 15))
        
        right_frame = tk.Frame(container, bg="#4A6572")
        right_frame.pack(side='right', fill='both', expand=True)
        
        input_frame = ttk.LabelFrame(left_frame, text="ВХОДНЫЕ ПАРАМЕТРЫ", padding="15")
        input_frame.pack(fill='both', expand=True)
        
        # ПОМЕНЯЛ МЕСТАМИ "Тип панелей" и "Мощность системы"
        inputs = [
            ("Регион:", "region_var", "combobox", list(self.insolation_data.keys()), self.update_insolation),
            ("Инсоляция (кВт·ч/м²/день):", "insolation_var", "entry", None, None),
            ("Тариф (руб/кВт·ч):", "tariff_var", "combobox", [f"{k}: {v}" for k,v in self.tariff_data.items()], self.update_tariff),
            ("Мощность системы (кВт):", "power_var", "entry", "1.0", None),  # Перемещено выше
            ("Тип панелей:", "panel_var", "combobox", list(self.panel_types.keys()), self.update_panel_info),  # Перемещено ниже
            ("Стоимость системы (руб):", "cost_var", "entry", None, None)
        ]
        
        for i, (label, var_name, widget_type, values, callback) in enumerate(inputs):
            row_frame = tk.Frame(input_frame, bg="#4A6572")
            row_frame.pack(fill='x', pady=8)
            
            lbl = tk.Label(row_frame, text=label, font=("Arial", 10), 
                          bg="#4A6572", fg="#ECF0F1", width=25, anchor='w')
            lbl.pack(side='left', padx=(0, 10))
            
            setattr(self, var_name, tk.StringVar())
            
            if widget_type == "combobox":
                combo = ttk.Combobox(row_frame, textvariable=getattr(self, var_name), 
                                    values=values, state="readonly", width=25)
                combo.pack(side='left', fill='x', expand=True)
                if callback: 
                    combo.bind('<<ComboboxSelected>>', callback)
            else:
                entry = ttk.Entry(row_frame, textvariable=getattr(self, var_name), width=25)
                entry.pack(side='left', fill='x', expand=True)
                if values: 
                    getattr(self, var_name).set(values)
        
        button_frame = tk.Frame(left_frame, bg="#4A6572")
        button_frame.pack(fill='x', pady=(15, 0))
        
        calc_btn = tk.Button(button_frame, text="РАССЧИТАТЬ", command=self.calculate,
                            font=("Arial", 12, "bold"), bg="#3498DB", fg="white",
                            activebackground="#2980B9", activeforeground="white",
                            relief="raised", bd=2, padx=30, pady=12, cursor="hand2")
        calc_btn.pack(fill='x')
        
        results_frame = ttk.LabelFrame(right_frame, text="РЕЗУЛЬТАТЫ РАСЧЕТА", padding="15")
        results_frame.pack(fill='both', expand=True)
        
        results_inner = tk.Frame(results_frame, bg="#ECF0F1")
        results_inner.pack(fill='both', expand=True, padx=2, pady=2)
        
        text_frame = tk.Frame(results_inner, bg="#ECF0F1")
        text_frame.pack(fill='both', expand=True)
        
        self.results_text = tk.Text(text_frame, height=16, width=60,
                                   bg="#ECF0F1", fg="#2C3E50", 
                                   font=("Courier New", 10), wrap=tk.WORD,
                                   relief="flat", bd=0, spacing2=3)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.results_text.pack(side="left", fill="both", expand=True)
        self.results_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.results_text.yview)
        
        footer_frame = tk.Frame(main_frame, bg="#4A6572")
        footer_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        footer = tk.Label(footer_frame, text="Школа №1502 «Энергия» • Проект «Спектр»", 
                         font=("Arial", 9), bg="#4A6572", fg="#BDC3C7")
        footer.pack()
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
    
    def create_viz_tab(self):
        viz_frame = ttk.Frame(self.viz_frame, padding="10")
        viz_frame.pack(fill='both', expand=True)
        
        title_frame = tk.Frame(viz_frame, bg="#4A6572")
        title_frame.pack(fill='x', pady=(0, 15))
        
        title = tk.Label(title_frame, text="ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ", 
                        font=("Arial", 16, "bold"), bg="#4A6572", fg="#F1C40F")
        title.pack()
        
        canvas_frame = tk.Frame(viz_frame, bg="#4A6572")
        canvas_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        self.viz_figure = plt.Figure(figsize=(10, 12), facecolor='#4A6572', dpi=100)
        self.viz_canvas = FigureCanvasTkAgg(self.viz_figure, canvas_frame)
        self.viz_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def update_insolation(self, event=None):
        region = self.region_var.get()
        if region in self.insolation_data:
            self.insolation_var.set(str(self.insolation_data[region]))
    
    def update_tariff(self, event=None):
        selection = self.tariff_var.get()
        if selection:
            tariff_value = selection.split(": ")[1]
            self.tariff_var.set(tariff_value)
    
    def update_panel_info(self, event=None):
        panel_type = self.panel_var.get()
        if panel_type in self.panel_types:
            power = float(self.power_var.get() or 1.0)
            system_cost = self.panel_types[panel_type]["price"] * power
            self.cost_var.set(str(int(system_cost)))
    
    def calculate_energy(self, power, insolation, efficiency):
        return power * insolation * 365 * efficiency
    
    def calculate(self):
        try:
            power = float(self.power_var.get())
            insolation = float(self.insolation_var.get())
            tariff = float(self.tariff_var.get())
            system_cost = float(self.cost_var.get())
            panel_type = self.panel_var.get()
            
            if panel_type not in self.panel_types:
                messagebox.showerror("Ошибка", "Выберите тип панелей")
                return
            
            panel = self.panel_types[panel_type]
            efficiency = panel["efficiency"]
            lifetime = panel["lifetime"]
            
            annual_energy = self.calculate_energy(power, insolation, efficiency)
            annual_savings = annual_energy * tariff
            payback_period = system_cost / annual_savings if annual_savings > 0 else float('inf')
            total_savings = annual_savings * lifetime - system_cost
            
            # Определяем, окупается ли проект
            is_profitable = total_savings > 0
            profitability_status = "Проект ОКУПАЕТСЯ ✅" if is_profitable else "Проект НЕ окупается ❌"
            
            self.calculation_results = {
                'power': power, 'insolation': insolation, 'tariff': tariff,
                'system_cost': system_cost, 'efficiency': efficiency,
                'lifetime': lifetime, 'annual_energy': annual_energy,
                'annual_savings': annual_savings, 'payback_period': payback_period,
                'total_savings': total_savings, 'panel_type': panel_type,
                'panel_color': panel["color"], 'is_profitable': is_profitable
            }
            
            result_text = f"""РЕЗУЛЬТАТЫ РАСЧЕТА:

Годовая выработка энергии: {annual_energy:.2f} кВт·ч
Годовая экономия: {annual_savings:.2f} руб
Срок окупаемости: {payback_period:.2f} лет
Общая экономика за {lifetime} лет: {total_savings:.2f} руб
{profitability_status}

ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ:
Тип панелей: {panel_type}
Мощность системы: {power} кВт
Уровень инсоляции: {insolation} кВт·ч/м²/день
КПД системы: {efficiency*100:.1f}%
Тариф на электроэнергию: {tariff} руб/кВт·ч
Стоимость системы: {system_cost:.2f} руб

ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
• Ежедневная выработка: {annual_energy/365:.2f} кВт·ч
• Ежемесячная экономия: {annual_savings/12:.2f} руб
• Рентабельность: {(total_savings/system_cost*100 if system_cost > 0 else 0):.1f}%
• Срок службы панелей: {lifetime} лет"""
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, result_text)
            
            # Цвет для общей экономики
            result_color = "#27AE60" if total_savings > 0 else "#E74C3C"
            self.results_text.tag_configure("result", foreground=result_color, font=("Courier New", 10, "bold"))
            
            # Цвет для строки окупаемости проекта
            profitability_color = "#27AE60" if is_profitable else "#E74C3C"
            self.results_text.tag_configure("profitability", foreground=profitability_color, 
                                           font=("Courier New", 10, "bold"))
            
            # Находим и выделяем строки
            lines = result_text.split('\n')
            for i, line in enumerate(lines):
                if "Общая экономика" in line:
                    start_idx = f"{i+1}.0"
                    end_idx = f"{i+1}.end"
                    self.results_text.tag_add("result", start_idx, end_idx)
                elif "Проект" in line and ("ОКУПАЕТСЯ" in line or "НЕ окупается" in line):
                    start_idx = f"{i+1}.0"
                    end_idx = f"{i+1}.end"
                    self.results_text.tag_add("profitability", start_idx, end_idx)
            
            # Обновляем визуализацию
            self.plot_visualizations()
            # УБРАНО автоматическое переключение на вкладку "Визуализация"
            # self.notebook.select(1)  # Эту строку удаляем
            
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность введенных данных")
    
    def plot_visualizations(self):
        if not self.calculation_results: 
            return
        
        res = self.calculation_results
        self.viz_figure.clear()
        
        gs = self.viz_figure.add_gridspec(2, 2, hspace=0.45, wspace=0.35, 
                                         left=0.1, right=0.95, top=0.91, bottom=0.09)
        
        ax1 = self.viz_figure.add_subplot(gs[0, 0], facecolor='#FFFFFF')
        ax2 = self.viz_figure.add_subplot(gs[0, 1], facecolor='#FFFFFF')
        ax3 = self.viz_figure.add_subplot(gs[1, 0], facecolor='#FFFFFF')
        ax4 = self.viz_figure.add_subplot(gs[1, 1], facecolor='#FFFFFF')
        
        # График 1: Структура затрат
        labels = ['Инвестиции', 'Годовая экономия']
        values = [res['system_cost'], res['annual_savings']]
        colors = ['#E74C3C', '#3498DB']
        
        wedges, texts, autotexts = ax1.pie(values, labels=labels, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        
        for text in texts:
            text.set_fontsize(9)
            text.set_color('#000000')
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax1.set_title('Структура затрат и экономии', fontweight='bold', 
                     color='#000000', pad=20, fontsize=11)
        
        # График 2: Сравнение панелей
        panel_names = list(self.panel_types.keys())
        efficiencies = [self.panel_types[p]['efficiency']*100 for p in panel_names]
        panel_colors = [self.panel_types[p]['color'] for p in panel_names]
        
        bars = ax2.bar(panel_names, efficiencies, color=panel_colors, alpha=0.8, edgecolor='white', linewidth=1.5)
        
        for i, name in enumerate(panel_names):
            if name == res['panel_type']:
                bars[i].set_alpha(1.0)
                bars[i].set_linewidth(2)
                bars[i].set_edgecolor('#F1C40F')
        
        ax2.set_ylabel('КПД, %', fontsize=10, color='#000000')
        ax2.set_title('Сравнение КПД различных типов панелей', fontweight='bold', 
                     color='#000000', pad=20, fontsize=11)
        ax2.tick_params(axis='x', labelrotation=15, colors='#000000')
        ax2.tick_params(axis='y', colors='#000000')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, eff in zip(bars, efficiencies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1.0,
                    f'{eff:.1f}%', ha='center', va='bottom', 
                    fontsize=9, fontweight='bold', color='#000000')
        
        # График 3: Динамика окупаемости
        years = list(range(int(res['lifetime']) + 1))
        cumulative = [-res['system_cost']]
        for year in range(1, len(years)):
            cumulative.append(res['annual_savings'] * year - res['system_cost'])
        
        line_color = '#27AE60' if cumulative[-1] > 0 else '#E74C3C'
        ax3.plot(years, cumulative, color=line_color, linewidth=2.5, marker='o', markersize=5)
        ax3.axhline(y=0, color='#000000', linestyle='--', alpha=0.7, linewidth=1.5)
        
        ax3.fill_between(years, cumulative, 0, where=[c >= 0 for c in cumulative], 
                         color='#ABEBC6', alpha=0.4, label='Прибыль')
        ax3.fill_between(years, cumulative, 0, where=[c < 0 for c in cumulative], 
                         color='#FADBD8', alpha=0.4, label='Убыток')
        
        payback_year = next((i for i, val in enumerate(cumulative) if val >= 0), None)
        if payback_year:
            ax3.plot(payback_year, cumulative[payback_year], 'o', 
                    markersize=8, color='#F1C40F', markeredgecolor='#000000',
                    markeredgewidth=2, label=f'Окупаемость: {payback_year} лет')
            ax3.legend(fontsize=9, loc='lower right', facecolor='white', edgecolor='black', labelcolor='#000000')
        
        ax3.set_xlabel('Годы', fontsize=10, color='#000000')
        ax3.set_ylabel('Накопленная экономия, руб', fontsize=10, color='#000000')
        ax3.set_title('Динамика окупаемости инвестиций', fontweight='bold', 
                     color='#000000', pad=20, fontsize=11)
        ax3.tick_params(axis='x', colors='#000000')
        ax3.tick_params(axis='y', colors='#000000')
        ax3.grid(True, alpha=0.3, linestyle='--')
        
        # График 4: Сравнение регионов
        regions = list(self.insolation_data.keys())[:6]
        insolation_vals = [self.insolation_data[r] for r in regions]
        reg_colors = ['#BDC3C7' for _ in regions]
        
        if res['insolation'] in insolation_vals:
            idx = insolation_vals.index(res['insolation'])
            reg_colors[idx] = res['panel_color']
        
        bars_reg = ax4.barh(regions, insolation_vals, color=reg_colors, alpha=0.8, 
                           edgecolor='white', linewidth=1.5)
        
        ax4.set_xlabel('Инсоляция, кВт·ч/м²/день', fontsize=10, color='#000000')
        ax4.set_title('Сравнение уровня инсоляции по регионам', fontweight='bold', 
                     color='#000000', pad=20, fontsize=11)
        ax4.tick_params(axis='x', colors='#000000')
        ax4.tick_params(axis='y', colors='#000000')
        
        for bar, val in zip(bars_reg, insolation_vals):
            width = bar.get_width()
            ax4.text(width + 0.08, bar.get_y() + bar.get_height()/2,
                    f'{val:.2f}', ha='left', va='center', 
                    fontsize=9, fontweight='bold', color='#000000')
        
        self.viz_canvas.draw()

def main():
    app = SolarCalculator()
    app.root.mainloop()

if __name__ == "__main__":
    main()
