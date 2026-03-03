import tkinter as tk
from tkinter import ttk
import math
import threading
import time
import random
import os

class TramwayClimateSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Climat-Manager reBUILD_32.03.2026")
        self.root.geometry("1920x1080")
        self.root.minsize(1400, 900)
        
        # Установка иконки для окна и панели задач
        self.set_icon()
        
        # Параметры ШИМ (управление вентиляцией/кондиционером)
        self.ac_duty = 0.0  # скважность ШИМ для кондиционера
        self.fan_duty = 0.0  # скважность ШИМ для вентилятора
        self.fan_angle = 0
        self.ac_compressor_angle = 0  # для анимации компрессора
        self.running = True
        self.time_counter = 0
        
        # Параметры гистерезиса
        self.temp_hysteresis = 1.0  # гистерезис температуры в градусах
        self.co2_hysteresis = 50    # гистерезис CO2 в ppm
        self.last_ac_state = 0       # последнее состояние кондиционера (для гистерезиса)
        self.last_fan_state = 0      # последнее состояние вентилятора (для гистерезиса)
        self.ac_trend = 0            # тренд изменения температуры
        self.co2_trend = 0           # тренд изменения CO2
        
        # История для графиков
        self.ac_history = [0] * 100
        self.fan_history = [0] * 100
        
        # Исходные данные из ТЗ
        self.route_length = 12  # км
        self.passenger_flow_peak = 150  # чел/час
        self.outside_temp = 30  # °С
        self.current_passengers = 0
        self.target_passengers = 0  # плавное целевое значение
        
        # Датчики
        self.current_temp = 25.0  # температура салона
        self.target_temp = 22.0   # целевая температура
        self.current_co2 = 450     # CO2 в салоне
        self.co2_history = [450] * 100
        self.temp_history = [25] * 100
        self.passenger_history = [0] * 100
        
        # Параметры для расчета
        self.energy_saved = 0.0    # экономия энергии (%)
        self.total_energy = 0.0     # общее потребление
        self.baseline_energy = 0.0  # базовое потребление (без оптимизации)
        
        # Физические параметры трамвая
        self.tram_volume = 80  # м³ (примерно)
        self.heat_capacity = 1.2  # кДж/(м³·К)
        self.ac_power = 15  # кВт (мощность кондиционера)
        self.fan_power = 2  # кВт (мощность вентилятора)
        self.co2_per_person = 0.3  # л/час на человека
        self.heat_per_person = 100  # Вт тепла от человека
        self.thermal_resistance = 0.5  # сопротивление теплопередаче
        
        # Параметры гетеродина (для имитации дребезга)
        self.heterodyne_freq = 0.5
        self.heterodyne_phase = 0
        self.modulation_depth = 0.1
        
        # Режимы работы
        self.auto_mode = True
        self.optimization_enabled = True
        self.dragging_ac = False
        self.dragging_fan = False
        
        self.root.configure(bg='#1e1e28')
        self.create_widgets()
        
        # Привязка событий
        self.root.bind("<Configure>", self.on_window_resize)
        
        # Потоки
        self.animation_thread = threading.Thread(target=self.animate_fan, daemon=True)
        self.animation_thread.start()
        
        self.simulation_thread = threading.Thread(target=self.simulate_tramway, daemon=True)
        self.simulation_thread.start()

    def set_icon(self):
        """Установка иконки для окна и панели задач"""
        try:
            # Проверяем существование файла иконки
            icon_path = "CM_LOGO.ico"
            
            if os.path.exists(icon_path):
                # Устанавливаем иконку для окна
                self.root.iconbitmap(icon_path)
                
                # Для Windows также устанавливаем иконку в панели задач
                try:
                    # Это помогает с отображением в панели задач Windows
                    self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
                except:
                    # Если iconphoto не работает, используем альтернативный метод
                    pass
                    
                print(f"Иконка успешно загружена: {icon_path}")
            else:
                print(f"Файл иконки не найден: {icon_path}")
                
        except Exception as e:
            print(f"Ошибка при загрузке иконки: {e}")

    def create_widgets(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Левая панель с прокруткой для графиков
        left_container = tk.Frame(main_frame, bg='#1e1e28', width=1000)
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_container.pack_propagate(False)
        
        # Canvas с прокруткой для левой панели
        left_canvas = tk.Canvas(left_container, bg='#1e1e28', highlightthickness=0)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        left_scrollbar = tk.Scrollbar(left_container, orient=tk.VERTICAL, command=left_canvas.yview)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        # Внутренний фрейм для графиков
        left_panel = tk.Frame(left_canvas, bg='#1e1e28')
        left_canvas.create_window((0, 0), window=left_panel, anchor='nw', width=left_canvas.winfo_width())
        
        def configure_left_scroll(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        
        left_panel.bind("<Configure>", configure_left_scroll)
        
        def configure_left_canvas_width(event):
            left_canvas.itemconfig("all", width=event.width)
        
        left_canvas.bind("<Configure>", configure_left_canvas_width)
        
        # График 1 - ШИМ кондиционера
        ac_pwm_frame = self.create_frame(left_panel, "Широтно-импульсная модуляция (кондиционирование)")
        ac_pwm_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        self.ac_pwm_canvas = tk.Canvas(
            ac_pwm_frame, bg='#000000', highlightthickness=1, 
            highlightbackground='#4a4a55', height=200
        )
        self.ac_pwm_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # График 2 - ШИМ вентилятора
        fan_pwm_frame = self.create_frame(left_panel, "Широтно-импульсная модуляция (вентиляция)")
        fan_pwm_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        self.fan_pwm_canvas = tk.Canvas(
            fan_pwm_frame, bg='#000000', highlightthickness=1, 
            highlightbackground='#4a4a55', height=200
        )
        self.fan_pwm_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # График 3 - Температура
        temp_frame = self.create_frame(left_panel, "Температура салона (°C)")
        temp_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        self.temp_canvas = tk.Canvas(
            temp_frame, bg='#14141c', highlightthickness=1, 
            highlightbackground='#4a4a55', height=200
        )
        self.temp_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # График 4 - CO2
        co2_frame = self.create_frame(left_panel, "Концентрация CO2 (ppm)")
        co2_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20), padx=5)
        
        self.co2_canvas = tk.Canvas(
            co2_frame, bg='#14141c', highlightthickness=1, 
            highlightbackground='#4a4a55', height=200
        )
        self.co2_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Правая панель с прокруткой
        right_container = tk.Frame(main_frame, bg='#1e1e28', width=500)
        right_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        right_container.pack_propagate(False)
        
        # Canvas с прокруткой для правой панели
        right_canvas = tk.Canvas(right_container, bg='#1e1e28', highlightthickness=0)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_scrollbar = tk.Scrollbar(right_container, orient=tk.VERTICAL, command=right_canvas.yview)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        right_canvas.configure(yscrollcommand=right_scrollbar.set)
        
        # Внутренний фрейм для содержимого правой панели
        right_panel = tk.Frame(right_canvas, bg='#1e1e28')
        right_canvas.create_window((0, 0), window=right_panel, anchor='nw', width=right_canvas.winfo_width())
        
        def configure_right_scroll(event):
            right_canvas.configure(scrollregion=right_canvas.bbox("all"))
        
        right_panel.bind("<Configure>", configure_right_scroll)
        
        def configure_right_canvas_width(event):
            right_canvas.itemconfig("all", width=event.width)
        
        right_canvas.bind("<Configure>", configure_right_canvas_width)
        
        # Фрейм для анимаций (вентилятор и кондиционер рядом)
        animations_frame = tk.Frame(right_panel, bg='#1e1e28')
        animations_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        # Вентилятор (слева)
        fan_frame = self.create_frame(animations_frame, "Вентилятор")
        fan_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.fan_canvas = tk.Canvas(
            fan_frame, bg='#2a2a35', highlightthickness=2, 
            highlightbackground='#3a3a45', height=180, width=200
        )
        self.fan_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кондиционер (справа)
        ac_anim_frame = self.create_frame(animations_frame, "Кондиционер")
        ac_anim_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.ac_canvas = tk.Canvas(
            ac_anim_frame, bg='#2a2a35', highlightthickness=2, 
            highlightbackground='#3a3a45', height=180, width=200
        )
        self.ac_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Фрейм для параметров гистерезиса
        hysteresis_frame = self.create_frame(right_panel, "Параметры гистерезиса")
        hysteresis_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        hysteresis_content = tk.Frame(hysteresis_frame, bg='#1a1a22')
        hysteresis_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Температурный гистерезис
        temp_hyst_frame = tk.Frame(hysteresis_content, bg='#1a1a22')
        temp_hyst_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(temp_hyst_frame, text="Гистерезис температуры:", font=('Arial', 10),
                fg='#88ccff', bg='#1a1a22').pack(side=tk.LEFT)
        
        self.temp_hyst_label = tk.Label(temp_hyst_frame, text=f"{self.temp_hysteresis:.1f}°C", 
                                       font=('Arial', 10, 'bold'), fg='#ffff99', bg='#1a1a22')
        self.temp_hyst_label.pack(side=tk.RIGHT)
        
        # Ползунок для температурного гистерезиса
        temp_hyst_slider = tk.Scale(hysteresis_content, from_=0.2, to=2.0, resolution=0.1,
                                   orient=tk.HORIZONTAL, length=200,
                                   bg='#2a2a35', fg='#f0f0f0', troughcolor='#3a3a45',
                                   activebackground='#4a4a55', highlightbackground='#4a4a55',
                                   command=self.on_temp_hysteresis_change)
        temp_hyst_slider.set(self.temp_hysteresis)
        temp_hyst_slider.pack(pady=5)
        
        # CO2 гистерезис
        co2_hyst_frame = tk.Frame(hysteresis_content, bg='#1a1a22')
        co2_hyst_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(co2_hyst_frame, text="Гистерезис CO2:", font=('Arial', 10),
                fg='#88ccff', bg='#1a1a22').pack(side=tk.LEFT)
        
        self.co2_hyst_label = tk.Label(co2_hyst_frame, text=f"{self.co2_hysteresis} ppm", 
                                      font=('Arial', 10, 'bold'), fg='#ffff99', bg='#1a1a22')
        self.co2_hyst_label.pack(side=tk.RIGHT)
        
        # Ползунок для CO2 гистерезиса
        co2_hyst_slider = tk.Scale(hysteresis_content, from_=10, to=200, resolution=10,
                                  orient=tk.HORIZONTAL, length=200,
                                  bg='#2a2a35', fg='#f0f0f0', troughcolor='#3a3a45',
                                  activebackground='#4a4a55', highlightbackground='#4a4a55',
                                  command=self.on_co2_hysteresis_change)
        co2_hyst_slider.set(self.co2_hysteresis)
        co2_hyst_slider.pack(pady=5)
        
        # Информация о трендах
        trend_frame = tk.Frame(hysteresis_content, bg='#1a1a22')
        trend_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(trend_frame, text="Тренд температуры:", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').pack(side=tk.LEFT)
        
        self.temp_trend_label = tk.Label(trend_frame, text="0.0°C/с", 
                                        font=('Arial', 10, 'bold'), fg='#a0ffa0', bg='#1a1a22')
        self.temp_trend_label.pack(side=tk.RIGHT)
        
        trend_frame2 = tk.Frame(hysteresis_content, bg='#1a1a22')
        trend_frame2.pack(fill=tk.X, pady=5)
        
        tk.Label(trend_frame2, text="Тренд CO2:", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').pack(side=tk.LEFT)
        
        self.co2_trend_label = tk.Label(trend_frame2, text="0 ppm/с", 
                                       font=('Arial', 10, 'bold'), fg='#a0ffa0', bg='#1a1a22')
        self.co2_trend_label.pack(side=tk.RIGHT)
        
        # Информация о маршруте
        route_frame = self.create_frame(right_panel, "Информация о маршруте")
        route_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        route_content = tk.Frame(route_frame, bg='#1a1a22')
        route_content.pack(fill=tk.X, padx=10, pady=10)
        
        info_grid = tk.Frame(route_content, bg='#1a1a22')
        info_grid.pack(fill=tk.X)
        
        # Строка 1
        tk.Label(info_grid, text="Длина маршрута:", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').grid(row=0, column=0, sticky='w', pady=2)
        tk.Label(info_grid, text=f"{self.route_length} км", font=('Arial', 10, 'bold'),
                fg='#ffff99', bg='#1a1a22').grid(row=0, column=1, sticky='e', pady=2)
        
        # Строка 2
        tk.Label(info_grid, text="Пассажиропоток (пик):", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').grid(row=1, column=0, sticky='w', pady=2)
        tk.Label(info_grid, text=f"{self.passenger_flow_peak} чел/ч", font=('Arial', 10, 'bold'),
                fg='#ffff99', bg='#1a1a22').grid(row=1, column=1, sticky='e', pady=2)
        
        # Строка 3
        tk.Label(info_grid, text="Температура снаружи:", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').grid(row=2, column=0, sticky='w', pady=2)
        tk.Label(info_grid, text=f"{self.outside_temp}°C", font=('Arial', 10, 'bold'),
                fg='#ffff99', bg='#1a1a22').grid(row=2, column=1, sticky='e', pady=2)
        
        # Текущие пассажиры
        tk.Label(info_grid, text="Пассажиров сейчас:", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').grid(row=3, column=0, sticky='w', pady=2)
        self.passenger_label = tk.Label(info_grid, text="0", font=('Arial', 10, 'bold'),
                fg='#a0ffa0', bg='#1a1a22')
        self.passenger_label.grid(row=3, column=1, sticky='e', pady=2)
        
        # Индикаторы
        indicators_frame = self.create_frame(right_panel, "Текущие показатели")
        indicators_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        indicators_content = tk.Frame(indicators_frame, bg='#1a1a22')
        indicators_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Температура
        temp_display = tk.Frame(indicators_content, bg='#1a1a22')
        temp_display.pack(fill=tk.X, pady=5)
        
        tk.Label(temp_display, text="Температура салона:", font=('Arial', 11),
                fg='#c0c0c0', bg='#1a1a22').pack()
        
        self.temp_label = tk.Label(
            temp_display, text=f"{self.current_temp:.1f}°C",
            font=('Arial', 24, 'bold'), fg='#a0ffa0', bg='#1a1a22'
        )
        self.temp_label.pack()
        
        self.temp_bar = tk.Canvas(temp_display, height=20, bg='#2a2a35', 
                                  highlightthickness=1, highlightbackground='#4a4a55')
        self.temp_bar.pack(fill=tk.X, pady=5)
        
        # CO2
        co2_display = tk.Frame(indicators_content, bg='#1a1a22')
        co2_display.pack(fill=tk.X, pady=5)
        
        tk.Label(co2_display, text="CO2 в салоне:", font=('Arial', 11),
                fg='#c0c0c0', bg='#1a1a22').pack()
        
        self.co2_label = tk.Label(
            co2_display, text=f"{self.current_co2} ppm",
            font=('Arial', 24, 'bold'), fg='#a0ffa0', bg='#1a1a22'
        )
        self.co2_label.pack()
        
        self.co2_bar = tk.Canvas(co2_display, height=20, bg='#2a2a35', 
                                 highlightthickness=1, highlightbackground='#4a4a55')
        self.co2_bar.pack(fill=tk.X, pady=5)
        
        # Экономия энергии
        energy_frame = self.create_frame(right_panel, "Энергоэффективность")
        energy_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        energy_content = tk.Frame(energy_frame, bg='#1a1a22')
        energy_content.pack(fill=tk.X, padx=10, pady=10)
        
        self.energy_label = tk.Label(
            energy_content, text="0%", font=('Arial', 32, 'bold'),
            fg='#ffaa00', bg='#1a1a22'
        )
        self.energy_label.pack(pady=10)
        
        tk.Label(energy_content, text="Экономия энергии", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').pack()
        
        # Управление
        control_frame = self.create_frame(right_panel, "Управление")
        control_frame.pack(fill=tk.X, pady=(0, 20), padx=5)
        
        control_content = tk.Frame(control_frame, bg='#1a1a22')
        control_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопки режимов
        btn_frame = tk.Frame(control_content, bg='#1a1a22')
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.mode_button = tk.Button(
            btn_frame, text="Автоматический режим", 
            command=self.toggle_mode,
            bg='#2a5a2a', fg='white', font=('Arial', 11), 
            padx=10, pady=5, cursor='hand2'
        )
        self.mode_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.opt_button = tk.Button(
            btn_frame, text="Оптимизация ВКЛ", 
            command=self.toggle_optimization,
            bg='#2a5a2a', fg='white', font=('Arial', 11), 
            padx=10, pady=5, cursor='hand2'
        )
        self.opt_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)
        
        # Два ползунка в ряд
        sliders_row = tk.Frame(control_content, bg='#1a1a22')
        sliders_row.pack(fill=tk.X, pady=10)
        
        # Ползунок кондиционера (левый)
        ac_slider_frame = tk.Frame(sliders_row, bg='#1a1a22')
        ac_slider_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        tk.Label(ac_slider_frame, text="Кондиционер:", font=('Arial', 10),
                fg='#88ccff', bg='#1a1a22').pack()
        
        self.ac_label = tk.Label(
            ac_slider_frame, text=f"{int(self.ac_duty)}%",
            font=('Arial', 18, 'bold'), fg='#88ccff', bg='#1a1a22'
        )
        self.ac_label.pack()
        
        ac_container = tk.Frame(ac_slider_frame, bg='#1a1a22', height=150)
        ac_container.pack(fill=tk.X, pady=5)
        ac_container.pack_propagate(False)
        
        self.ac_slider = tk.Scale(
            ac_container, from_=100, to=0, orient=tk.VERTICAL,
            length=130, width=25, sliderlength=25,
            bg='#2a2a35', fg='#f0f0f0', troughcolor='#3a3a45',
            activebackground='#4a4a55', highlightbackground='#4a4a55',
            font=('Arial', 9), command=self.on_ac_slider_change,
            state=tk.DISABLED, cursor='hand2',
            showvalue=0, borderwidth=2, relief=tk.SUNKEN
        )
        self.ac_slider.pack(expand=True)
        
        # Ползунок вентилятора (правый)
        fan_slider_frame = tk.Frame(sliders_row, bg='#1a1a22')
        fan_slider_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        tk.Label(fan_slider_frame, text="Вентилятор:", font=('Arial', 10),
                fg='#ffff99', bg='#1a1a22').pack()
        
        self.fan_label = tk.Label(
            fan_slider_frame, text=f"{int(self.fan_duty)}%",
            font=('Arial', 18, 'bold'), fg='#ffff99', bg='#1a1a22'
        )
        self.fan_label.pack()
        
        fan_container = tk.Frame(fan_slider_frame, bg='#1a1a22', height=150)
        fan_container.pack(fill=tk.X, pady=5)
        fan_container.pack_propagate(False)
        
        self.fan_slider = tk.Scale(
            fan_container, from_=100, to=0, orient=tk.VERTICAL,
            length=130, width=25, sliderlength=25,
            bg='#2a2a35', fg='#f0f0f0', troughcolor='#3a3a45',
            activebackground='#4a4a55', highlightbackground='#4a4a55',
            font=('Arial', 9), command=self.on_fan_slider_change,
            state=tk.DISABLED, cursor='hand2',
            showvalue=0, borderwidth=2, relief=tk.SUNKEN
        )
        self.fan_slider.pack(expand=True)
        
        # Кнопки +/-
        button_row = tk.Frame(control_content, bg='#1a1a22')
        button_row.pack(fill=tk.X, pady=5)
        
        # Кнопки для кондиционера
        ac_button_frame = tk.Frame(button_row, bg='#1a1a22')
        ac_button_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        tk.Label(ac_button_frame, text="Кондиционер:", font=('Arial', 9),
                fg='#88ccff', bg='#1a1a22').pack(side=tk.LEFT, padx=2)
        
        self.ac_minus = tk.Button(
            ac_button_frame, text="-", font=('Arial', 14, 'bold'),
            bg='#3a3a45', fg='white', width=3,
            command=self.decrease_ac, state=tk.DISABLED,
            cursor='hand2'
        )
        self.ac_minus.pack(side=tk.LEFT, padx=2)
        
        self.ac_plus = tk.Button(
            ac_button_frame, text="+", font=('Arial', 14, 'bold'),
            bg='#3a3a45', fg='white', width=3,
            command=self.increase_ac, state=tk.DISABLED,
            cursor='hand2'
        )
        self.ac_plus.pack(side=tk.LEFT, padx=2)
        
        # Кнопки для вентилятора
        fan_button_frame = tk.Frame(button_row, bg='#1a1a22')
        fan_button_frame.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        
        tk.Label(fan_button_frame, text="Вентилятор:", font=('Arial', 9),
                fg='#ffff99', bg='#1a1a22').pack(side=tk.LEFT, padx=2)
        
        self.fan_minus = tk.Button(
            fan_button_frame, text="-", font=('Arial', 14, 'bold'),
            bg='#3a3a45', fg='white', width=3,
            command=self.decrease_fan, state=tk.DISABLED,
            cursor='hand2'
        )
        self.fan_minus.pack(side=tk.LEFT, padx=2)
        
        self.fan_plus = tk.Button(
            fan_button_frame, text="+", font=('Arial', 14, 'bold'),
            bg='#3a3a45', fg='white', width=3,
            command=self.increase_fan, state=tk.DISABLED,
            cursor='hand2'
        )
        self.fan_plus.pack(side=tk.LEFT, padx=2)
        
        # Дребезг
        self.heterodyne_label = tk.Label(
            control_content, text="Дребезг: 0.0%", 
            font=('Arial', 10), fg='#ffaa00', bg='#1a1a22'
        )
        self.heterodyne_label.pack(pady=5)
        
        # Целевая температура
        target_frame = tk.Frame(control_content, bg='#1a1a22')
        target_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(target_frame, text="Эталонная температура:", font=('Arial', 10),
                fg='#c0c0c0', bg='#1a1a22').pack()
        
        self.target_temp_label = tk.Label(
            target_frame, text=f"{self.target_temp}°C",
            font=('Arial', 16, 'bold'), fg='#a0ffa0', bg='#1a1a22'
        )
        self.target_temp_label.pack()
        
        # Привязка событий для ползунков
        self.ac_slider.bind("<ButtonPress-1>", self.start_drag_ac)
        self.ac_slider.bind("<ButtonRelease-1>", self.stop_drag_ac)
        self.ac_slider.bind("<B1-Motion>", self.on_drag_ac)
        self.ac_slider.bind("<MouseWheel>", self.on_mousewheel_ac)
        
        self.fan_slider.bind("<ButtonPress-1>", self.start_drag_fan)
        self.fan_slider.bind("<ButtonRelease-1>", self.stop_drag_fan)
        self.fan_slider.bind("<B1-Motion>", self.on_drag_fan)
        self.fan_slider.bind("<MouseWheel>", self.on_mousewheel_fan)
        
        # Привязка колесика мыши для прокрутки
        def on_mousewheel_left(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def on_mousewheel_right(event):
            right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        left_canvas.bind("<MouseWheel>", on_mousewheel_left)
        right_canvas.bind("<MouseWheel>", on_mousewheel_right)
    
    def create_frame(self, parent, title):
        frame = tk.Frame(parent, bg='#1a1a22', highlightthickness=2, 
                        highlightbackground='#3a3a45')
        
        title_label = tk.Label(
            frame, text=title, font=('Arial', 12, 'bold'),
            fg='#f0f0f0', bg='#1a1a22'
        )
        title_label.pack(pady=(5, 0))
        
        return frame
    
    def on_temp_hysteresis_change(self, value):
        """Изменение температурного гистерезиса"""
        self.temp_hysteresis = float(value)
        self.temp_hyst_label.config(text=f"{self.temp_hysteresis:.1f}°C")
    
    def on_co2_hysteresis_change(self, value):
        """Изменение гистерезиса CO2"""
        self.co2_hysteresis = int(float(value))
        self.co2_hyst_label.config(text=f"{self.co2_hysteresis} ppm")
    
    def simulate_tramway(self):
        """Основной поток симуляции трамвая"""
        last_time = time.time()
        route_progress = 0
        last_temp = self.current_temp
        last_co2 = self.current_co2
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            dt = min(dt, 0.1)
            
            # Расчет трендов
            self.temp_trend = (self.current_temp - last_temp) / dt if dt > 0 else 0
            self.co2_trend = (self.current_co2 - last_co2) / dt if dt > 0 else 0
            
            last_temp = self.current_temp
            last_co2 = self.current_co2
            
            # Симуляция движения по маршруту
            route_progress += dt * 5
            if route_progress > self.route_length:
                route_progress = 0
            
            # Симуляция пассажиропотока
            self.simulate_passengers_smooth(route_progress, dt)
            
            # Расчет теплового баланса
            self.calculate_thermal_dynamics(dt)
            
            # Расчет CO2
            self.calculate_co2_dynamics(dt)
            
            # Расчет энергопотребления
            self.calculate_energy_consumption(dt)
            
            # Управление в автоматическом режиме с гистерезисом
            if self.auto_mode:
                self.update_control_with_hysteresis()
            
            # Сохранение истории
            self.temp_history.append(self.current_temp)
            self.co2_history.append(self.current_co2)
            self.passenger_history.append(self.current_passengers)
            self.ac_history.append(self.ac_duty)
            self.fan_history.append(self.fan_duty)
            
            if len(self.temp_history) > 100:
                self.temp_history.pop(0)
                self.co2_history.pop(0)
                self.passenger_history.pop(0)
                self.ac_history.pop(0)
                self.fan_history.pop(0)
            
            time.sleep(0.1)
    
    def update_control_with_hysteresis(self):
        """Управление на основе показаний датчиков с гистерезисом"""
        temp_error = self.current_temp - self.target_temp
        co2_error = self.current_co2 - 800
        
        # Определяем направление изменения
        temp_direction = 1 if self.temp_trend > 0 else -1 if self.temp_trend < 0 else 0
        co2_direction = 1 if self.co2_trend > 0 else -1 if self.co2_trend < 0 else 0
        
        if self.optimization_enabled:
            # Оптимизированное управление с гистерезисом
            
            # Кондиционер с гистерезисом
            if temp_error > self.temp_hysteresis:
                # Слишком жарко - включаем кондиционер сильнее
                base_ac = 60 + temp_error * 8
                self.last_ac_state = 1
            elif temp_error < -self.temp_hysteresis:
                # Слишком холодно - уменьшаем кондиционер
                base_ac = 10
                self.last_ac_state = -1
            elif abs(temp_error) <= self.temp_hysteresis:
                # В зоне гистерезиса - сохраняем предыдущее состояние с учетом тренда
                if self.last_ac_state == 1 and temp_direction > 0:
                    # Было жарко и температура растет - продолжаем охлаждение
                    base_ac = 40 + temp_error * 4
                elif self.last_ac_state == -1 and temp_direction < 0:
                    # Было холодно и температура падает - продолжаем нагрев
                    base_ac = 20 + temp_error * 4
                else:
                    # В зоне комфорта - минимальная мощность
                    base_ac = 20 + temp_error * 4
            
            passenger_factor = min(1, self.current_passengers / 100)
            
            # Вентилятор с гистерезисом
            if co2_error > self.co2_hysteresis:
                # CO2 слишком высокий - включаем вентиляцию
                base_fan = 70 + passenger_factor * 10
                self.last_fan_state = 1
            elif co2_error < -self.co2_hysteresis:
                # CO2 низкий - уменьшаем вентиляцию
                base_fan = 15 + passenger_factor * 5
                self.last_fan_state = -1
            else:
                # В зоне гистерезиса
                if self.last_fan_state == 1 and co2_direction > 0:
                    base_fan = 50 + passenger_factor * 10
                elif self.last_fan_state == -1 and co2_direction < 0:
                    base_fan = 30 + passenger_factor * 10
                else:
                    base_fan = 30 + passenger_factor * 10
        else:
            # Без оптимизации - простое управление
            base_ac = 50 + temp_error * 15
            base_fan = 40 + co2_error * 0.08 + self.current_passengers * 0.2
        
        base_ac = max(5, min(95, base_ac))
        base_fan = max(5, min(95, base_fan))
        
        self.heterodyne_phase += 0.03
        heterodyne = math.sin(self.heterodyne_phase * self.heterodyne_freq) * self.modulation_depth * 5
        
        self.ac_duty = base_ac + heterodyne * 0.3
        self.fan_duty = base_fan + heterodyne * 0.5
        
        self.ac_duty = max(0, min(100, self.ac_duty))
        self.fan_duty = max(0, min(100, self.fan_duty))
    
    def simulate_passengers_smooth(self, progress, dt):
        """Плавная симуляция пассажиропотока"""
        peak_factor = (math.sin(progress / self.route_length * math.pi - math.pi/2) + 1) / 2
        base_target = self.passenger_flow_peak * peak_factor
        
        if random.random() < 0.01:
            variation = random.gauss(0, 8)
            self.target_passengers = max(0, int(base_target + variation))
        
        diff = self.target_passengers - self.current_passengers
        self.current_passengers += diff * dt * 0.2
        self.current_passengers = max(0, min(self.passenger_flow_peak * 1.2, 
                                            self.current_passengers))
    
    def calculate_thermal_dynamics(self, dt):
        """Расчет теплового баланса салона"""
        passenger_heat = self.current_passengers * self.heat_per_person / 1000
        temp_diff = self.outside_temp - self.current_temp
        external_heat = temp_diff / self.thermal_resistance * self.tram_volume / 1000
        cooling_power = self.ac_duty * self.ac_power / 100
        ventilation_effect = self.fan_duty / 100 * 0.5 * temp_diff
        
        total_heat = passenger_heat + external_heat - cooling_power + ventilation_effect
        temp_change = total_heat / (self.tram_volume * self.heat_capacity) * dt * 5
        
        self.current_temp += temp_change
        self.current_temp = max(18, min(35, self.current_temp))
    
    def calculate_co2_dynamics(self, dt):
        """Расчет концентрации CO2"""
        co2_production = self.current_passengers * self.co2_per_person / 3600 * 800
        fresh_air = self.fan_duty / 100 * 0.2
        co2_change = (co2_production - fresh_air * (self.current_co2 - 400)) * dt * 0.5
        
        self.current_co2 += co2_change
        self.current_co2 = max(350, min(2000, self.current_co2))
    
    def calculate_energy_consumption(self, dt):
        """Расчет энергопотребления и экономии"""
        current_power = (self.ac_duty * self.ac_power / 100 + 
                        self.fan_duty * self.fan_power / 100) * dt / 3600
        
        baseline_power = (50 * self.ac_power / 100 + 50 * self.fan_power / 100) * dt / 3600
        
        self.total_energy += current_power
        self.baseline_energy += baseline_power
        
        if self.baseline_energy > 0:
            self.energy_saved = ((self.baseline_energy - self.total_energy) / 
                                self.baseline_energy * 100)
            self.energy_saved = max(0, min(100, self.energy_saved))
    
    def draw_pwm_signal(self, canvas, duty, title, color_on='#ffff00', color_off='#00aaff'):
        """Универсальная отрисовка ШИМ сигнала"""
        canvas.delete("all")
        
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        margin = 30
        y_high = margin
        y_low = h - margin
        
        # Сетка
        for i in range(0, w, 50):
            canvas.create_line(i, 0, i, h, fill='#1a4a1a', width=1)
        for i in range(0, h, 30):
            canvas.create_line(0, i, w, i, fill='#1a4a1a', width=1)
        
        # Подписи
        canvas.create_text(10, y_high-5, text="HIGH", fill='#62be91', 
                          font=('Arial', 8), anchor='w')
        canvas.create_text(10, y_low+10, text="LOW", fill='#ed696d', 
                          font=('Arial', 8), anchor='w')
        
        # Генерация сигнала
        num_periods = 8
        if w > 40:
            period_width = (w - 40) // num_periods
            pulse_duration = period_width * duty / 100 if duty > 0 else 0
            
            self.time_counter += 1
            start_x = 20 - (self.time_counter % period_width) if period_width > 0 else 20
            
            points = []
            for i in range(num_periods + 2):
                x_period_start = start_x + i * period_width
                x_pulse_start = x_period_start
                x_pulse_end = x_period_start + pulse_duration
                
                if duty == 0:
                    points.append((x_period_start, y_low))
                    points.append((x_period_start + period_width, y_low))
                else:
                    points.append((x_period_start, y_low))
                    points.append((x_period_start, y_high))
                    points.append((x_pulse_end, y_high))
                    points.append((x_pulse_end, y_low))
            
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                
                if (x1 < w - 10 or x2 < w - 10) and (x1 > 10 or x2 > 10):
                    if duty == 0:
                        color = color_off
                    elif y1 == y_high and y2 == y_high:
                        color = color_on
                    elif y1 == y_low and y2 == y_low:
                        color = color_off
                    else:
                        color = '#ffaa00'
                    
                    canvas.create_line(
                        max(10, min(x1, w-10)), y1,
                        max(10, min(x2, w-10)), y2,
                        fill=color, width=2
                    )
        
        # Информация
        if duty > 0:
            canvas.create_text(
                w//2, 20, text=f"{title}: {duty:.1f}%",
                fill='#ffff99', font=('Arial', 10, 'bold')
            )
        else:
            canvas.create_text(
                w//2, 20, text=f"{title} NO POWER SUPPLY",
                fill='#dc373b', font=('Arial', 10, 'bold')
            )
    
    def draw_temp_graph(self):
        """Отрисовка графика температуры"""
        self.temp_canvas.delete("all")
        
        w = self.temp_canvas.winfo_width()
        h = self.temp_canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        # Цветовые зоны комфорта с учетом гистерезиса
        zones = [
            (18, self.target_temp - self.temp_hysteresis, '#3a4a8a'),  # Холодно
            (self.target_temp - self.temp_hysteresis, self.target_temp + self.temp_hysteresis, '#3a8a3a'),  # Зона гистерезиса
            (self.target_temp + self.temp_hysteresis, 26, '#8a8a3a'),  # Тепло
            (26, 35, '#8a3a3a')   # Жарко
        ]
        
        for low, high, color in zones:
            if low < high:  # Проверяем, что зона имеет положительную ширину
                y1 = h - h * (low - 15) / 20
                y2 = h - h * (high - 15) / 20
                if y1 > y2:
                    y1, y2 = y2, y1
                self.temp_canvas.create_rectangle(0, y1, w, y2, fill=color, outline='')
        
        # Сетка
        for i in range(0, w, 50):
            self.temp_canvas.create_line(i, 0, i, h, fill='#2a4a4a', width=1)
        for i in range(0, h, 30):
            self.temp_canvas.create_line(0, i, w, i, fill='#2a4a4a', width=1)
        
        # Линии гистерезиса
        upper_hyst_y = h - h * (self.target_temp + self.temp_hysteresis - 15) / 20
        lower_hyst_y = h - h * (self.target_temp - self.temp_hysteresis - 15) / 20
        
        self.temp_canvas.create_line(0, upper_hyst_y, w, upper_hyst_y, 
                                     fill='#ffff99', width=1, dash=(3, 3))
        self.temp_canvas.create_line(0, lower_hyst_y, w, lower_hyst_y, 
                                     fill='#ffff99', width=1, dash=(3, 3))
        
        # Линия целевой температуры
        target_y = h - h * (self.target_temp - 15) / 20
        self.temp_canvas.create_line(0, target_y, w, target_y, 
                                     fill='#ffffff', width=2, dash=(5, 5))
        
        # График
        if len(self.temp_history) > 1:
            points = []
            for i, temp in enumerate(self.temp_history):
                x = 5 + (i * (w - 10) / (len(self.temp_history) - 1))
                y = h - 10 - ((temp - 15) / 20) * (h - 20)
                y = max(10, min(h-10, y))
                points.append((x, y))
            
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.temp_canvas.create_line(x1, y1, x2, y2, fill='#ffaa00', width=2)
        
        # Текущее значение
        self.temp_canvas.create_text(
            w-60, 20, text=f"{self.current_temp:.1f}°C",
            fill='white', font=('Arial', 10, 'bold')
        )
    
    def draw_co2_graph(self):
        """Отрисовка графика CO2"""
        self.co2_canvas.delete("all")
        
        w = self.co2_canvas.winfo_width()
        h = self.co2_canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        # Цветовые зоны CO2 с учетом гистерезиса
        zones = [
            (350, 800 - self.co2_hysteresis, '#1a3a1a'),  # Отличный
            (800 - self.co2_hysteresis, 800 + self.co2_hysteresis, '#2a4a2a'),  # Зона гистерезиса
            (800 + self.co2_hysteresis, 1000, '#3a3a1a'), # Средний
            (1000, 1400, '#3a2a1a'),# Плохой
            (1400, 2000, '#3a1a1a') # Вредный
        ]
        
        for low, high, color in zones:
            if low < high:  # Проверяем, что зона имеет положительную ширину
                y1 = h - h * (low - 350) / 1650
                y2 = h - h * (high - 350) / 1650
                if y1 > y2:
                    y1, y2 = y2, y1
                self.co2_canvas.create_rectangle(0, y1, w, y2, fill=color, outline='')
        
        # Сетка
        for i in range(0, w, 50):
            self.co2_canvas.create_line(i, 0, i, h, fill='#2a4a2a', width=1)
        for i in range(0, h, 30):
            self.co2_canvas.create_line(0, i, w, i, fill='#2a4a2a', width=1)
        
        # Линии гистерезиса
        upper_hyst_y = h - h * (800 + self.co2_hysteresis - 350) / 1650
        lower_hyst_y = h - h * (800 - self.co2_hysteresis - 350) / 1650
        
        self.co2_canvas.create_line(0, upper_hyst_y, w, upper_hyst_y, 
                                    fill='#ffff99', width=1, dash=(3, 3))
        self.co2_canvas.create_line(0, lower_hyst_y, w, lower_hyst_y, 
                                    fill='#ffff99', width=1, dash=(3, 3))
        
        # График
        if len(self.co2_history) > 1:
            points = []
            for i, co2 in enumerate(self.co2_history):
                x = 5 + (i * (w - 10) / (len(self.co2_history) - 1))
                y = h - 10 - ((co2 - 350) / 1650) * (h - 20)
                y = max(10, min(h-10, y))
                points.append((x, y))
            
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                self.co2_canvas.create_line(x1, y1, x2, y2, fill='#ffaa00', width=2)
        
        # Текущее значение
        self.co2_canvas.create_text(
            w-60, 20, text=f"{int(self.current_co2)} ppm",
            fill='white', font=('Arial', 10, 'bold')
        )
    
    def draw_fan(self):
        """Отрисовка вентилятора"""
        self.fan_canvas.delete("all")
        
        w = self.fan_canvas.winfo_width()
        h = self.fan_canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        center_x, center_y = w//2, h//2
        radius = min(w, h) * 0.3
        blade_length = radius * 0.6
        
        # Внешний круг
        self.fan_canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline='#c8c8dc', width=3, fill=''
        )
        
        # Лопасти
        for i in range(4):
            blade_angle = math.radians(self.fan_angle + i * 90)
            
            end_x = center_x + blade_length * math.cos(blade_angle)
            end_y = center_y + blade_length * math.sin(blade_angle)
            
            self.fan_canvas.create_line(
                center_x, center_y, end_x, end_y,
                fill='#6495ff', width=int(radius*0.15), capstyle=tk.ROUND
            )
            
            tip_x = center_x + (blade_length + radius*0.1) * math.cos(blade_angle)
            tip_y = center_y + (blade_length + radius*0.1) * math.sin(blade_angle)
            
            self.fan_canvas.create_oval(
                tip_x - radius*0.08, tip_y - radius*0.08,
                tip_x + radius*0.08, tip_y + radius*0.08,
                fill='#6495ff', outline=''
            )
        
        # Центр
        self.fan_canvas.create_oval(
            center_x - radius*0.15, center_y - radius*0.15,
            center_x + radius*0.15, center_y + radius*0.15,
            fill='#4a4a55', outline='#c8c8dc', width=2
        )
        
        # Текст скорости - вынесен на один уровень с кондиционером
        fan_bottom_y = center_y + radius + 25
        if self.fan_duty > 0:
            self.fan_canvas.create_text(
                center_x, fan_bottom_y,
                text=f"{int(self.fan_duty)}%",
                fill='#ffff99', font=('Arial', 14, 'bold')
            )
        else:
            self.fan_canvas.create_text(
                center_x, center_y,
                text="OFF",
                fill='#ff5555', font=('Arial', 14, 'bold')
            )
    
    def draw_ac(self):
        """Отрисовка анимации кондиционера"""
        self.ac_canvas.delete("all")
        
        w = self.ac_canvas.winfo_width()
        h = self.ac_canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
        
        center_x, center_y = w//2, h//2
        
        # Рисуем корпус кондиционера (прямоугольник)
        width = w * 0.7
        height = h * 0.5
        rect_x1 = center_x - width/2
        rect_y1 = center_y - height/2
        rect_x2 = center_x + width/2
        rect_y2 = center_y + height/2
        
        self.ac_canvas.create_rectangle(
            rect_x1, rect_y1, rect_x2, rect_y2,
            outline='#88ccff', width=3, fill='#2a2a35'
        )
        
        # Вентиляционные решетки
        grill_count = 5
        grill_spacing = width / (grill_count + 1)
        for i in range(1, grill_count + 1):
            x = rect_x1 + i * grill_spacing
            self.ac_canvas.create_line(
                x, rect_y1 + 5, x, rect_y2 - 5,
                fill='#88ccff', width=2
            )
        
        # Анимация вращающегося вентилятора внутри (если кондиционер работает)
        if self.ac_duty > 0:
            # Рисуем вращающиеся лопасти
            blade_length = width * 0.15
            for i in range(3):  # 3 лопасти
                angle = math.radians(self.ac_compressor_angle + i * 120)
                
                # Центр вращения - внутри корпуса
                fan_center_x = center_x
                fan_center_y = center_y
                
                # Конец лопасти
                end_x = fan_center_x + blade_length * math.cos(angle)
                end_y = fan_center_y + blade_length * math.sin(angle)
                
                self.ac_canvas.create_line(
                    fan_center_x, fan_center_y, end_x, end_y,
                    fill='#88ccff', width=4, capstyle=tk.ROUND
                )
                
                # Кружок на конце лопасти
                self.ac_canvas.create_oval(
                    end_x - 5, end_y - 5, end_x + 5, end_y + 5,
                    fill='#88ccff', outline=''
                )
            
            # Центральная ступица
            self.ac_canvas.create_oval(
                fan_center_x - 8, fan_center_y - 8,
                fan_center_x + 8, fan_center_y + 8,
                fill='#4a4a55', outline='#88ccff', width=2
            )
            
            # Индикация холодного воздуха
            if self.ac_duty > 30:
                # Рисуем "холодные" волны
                for j in range(3):
                    offset = j * 10
                    self.ac_canvas.create_line(
                        rect_x2 + 5 + offset, center_y - 20,
                        rect_x2 + 15 + offset, center_y,
                        fill='#88ccff', width=2, dash=(2, 2)
                    )
                    self.ac_canvas.create_line(
                        rect_x2 + 5 + offset, center_y,
                        rect_x2 + 15 + offset, center_y + 20,
                        fill='#88ccff', width=2, dash=(2, 2)
                    )
        
        # Текст процентов - на одном уровне с вентилятором
        ac_bottom_y = rect_y2 + 25
        self.ac_canvas.create_text(
            center_x, ac_bottom_y,
            text=f"{int(self.ac_duty)}%",
            fill='#88ccff', font=('Arial', 14, 'bold')
        )
        
        # Если кондиционер выключен
        if self.ac_duty == 0:
            self.ac_canvas.create_text(
                center_x, center_y,
                text="OFF",
                fill='#ff5555', font=('Arial', 14, 'bold')
            )
    
    def update_ui(self):
        """Обновление интерфейса"""
        # Обновление меток
        self.temp_label.config(text=f"{self.current_temp:.1f}°C")
        self.co2_label.config(text=f"{int(self.current_co2)} ppm")
        self.ac_label.config(text=f"{int(self.ac_duty)}%")
        self.fan_label.config(text=f"{int(self.fan_duty)}%")
        self.passenger_label.config(text=f"{int(self.current_passengers)}")
        self.energy_label.config(text=f"{self.energy_saved:.1f}%")
        
        # Обновление трендов
        self.temp_trend_label.config(text=f"{self.temp_trend:.2f}°C/с")
        self.co2_trend_label.config(text=f"{self.co2_trend:.1f} ppm/с")
        
        # Цвет температуры с учетом гистерезиса
        if abs(self.current_temp - self.target_temp) < self.temp_hysteresis:
            self.temp_label.config(fg='#a0ffa0')
        elif abs(self.current_temp - self.target_temp) < 2:
            self.temp_label.config(fg='#ffffa0')
        else:
            self.temp_label.config(fg='#ffa0a0')
        
        # Цвет CO2 с учетом гистерезиса
        if abs(self.current_co2 - 800) < self.co2_hysteresis:
            self.co2_label.config(fg='#a0ffa0')
        elif self.current_co2 < 1000:
            self.co2_label.config(fg='#ffffa0')
        elif self.current_co2 < 1400:
            self.co2_label.config(fg='#ffa0a0')
        else:
            self.co2_label.config(fg='#ff5555')
        
        # Цвет экономии
        if self.energy_saved > 30:
            self.energy_label.config(fg='#a0ffa0')
        elif self.energy_saved > 15:
            self.energy_label.config(fg='#ffffa0')
        else:
            self.energy_label.config(fg='#ffa0a0')
        
        # Обновление баров
        w = self.temp_bar.winfo_width()
        if w > 10:
            self.temp_bar.delete("all")
            fill_width = w * ((self.current_temp - 15) / 15)
            fill_width = max(0, min(w, fill_width))
            
            self.temp_bar.create_rectangle(0, 0, w, 20, fill='#2a2a35', outline='')
            self.temp_bar.create_rectangle(0, 0, fill_width, 20, fill='#ffaa00', outline='')
            
            # Отметки гистерезиса
            upper_hyst_x = w * ((self.target_temp + self.temp_hysteresis - 15) / 15)
            lower_hyst_x = w * ((self.target_temp - self.temp_hysteresis - 15) / 15)
            
            if 0 < upper_hyst_x < w:
                self.temp_bar.create_line(upper_hyst_x, 0, upper_hyst_x, 20, fill='#ffff99', width=1, dash=(2, 2))
            if 0 < lower_hyst_x < w:
                self.temp_bar.create_line(lower_hyst_x, 0, lower_hyst_x, 20, fill='#ffff99', width=1, dash=(2, 2))
            
            target_x = w * ((self.target_temp - 15) / 15)
            if 0 < target_x < w:
                self.temp_bar.create_line(target_x, 0, target_x, 20, fill='white', width=2)
        
        w = self.co2_bar.winfo_width()
        if w > 10:
            self.co2_bar.delete("all")
            fill_width = w * ((self.current_co2 - 350) / 1650)
            fill_width = max(0, min(w, fill_width))
            
            self.co2_bar.create_rectangle(0, 0, w, 20, fill='#2a2a35', outline='')
            self.co2_bar.create_rectangle(0, 0, fill_width, 20, fill='#ffaa00', outline='')
            
            # Отметки гистерезиса
            upper_hyst_x = w * ((800 + self.co2_hysteresis - 350) / 1650)
            lower_hyst_x = w * ((800 - self.co2_hysteresis - 350) / 1650)
            
            if 0 < upper_hyst_x < w:
                self.co2_bar.create_line(upper_hyst_x, 0, upper_hyst_x, 20, fill='#ffff99', width=1, dash=(2, 2))
            if 0 < lower_hyst_x < w:
                self.co2_bar.create_line(lower_hyst_x, 0, lower_hyst_x, 20, fill='#ffff99', width=1, dash=(2, 2))
            
            for threshold in [600, 800, 1000, 1400]:
                x = w * ((threshold - 350) / 1650)
                if 0 < x < w:
                    self.co2_bar.create_line(x, 0, x, 20, fill='white', width=1)
        
        # Гетеродин
        beat_effect = math.sin(self.heterodyne_phase) * self.modulation_depth * 5
        self.heterodyne_label.config(text=f"Модуляция: {beat_effect:+.1f}%")
        
        if not self.auto_mode:
            self.ac_slider.set(self.ac_duty)
            self.fan_slider.set(self.fan_duty)
    
    # Методы для кондиционера
    def decrease_ac(self):
        if not self.auto_mode:
            new_duty = max(0, self.ac_duty - 5)
            self.ac_duty = new_duty
            self.ac_slider.set(new_duty)
            self.ac_label.config(text=f"{int(new_duty)}%")
    
    def increase_ac(self):
        if not self.auto_mode:
            new_duty = min(100, self.ac_duty + 5)
            self.ac_duty = new_duty
            self.ac_slider.set(new_duty)
            self.ac_label.config(text=f"{int(new_duty)}%")
    
    # Методы для вентилятора
    def decrease_fan(self):
        if not self.auto_mode:
            new_duty = max(0, self.fan_duty - 5)
            self.fan_duty = new_duty
            self.fan_slider.set(new_duty)
            self.fan_label.config(text=f"{int(new_duty)}%")
    
    def increase_fan(self):
        if not self.auto_mode:
            new_duty = min(100, self.fan_duty + 5)
            self.fan_duty = new_duty
            self.fan_slider.set(new_duty)
            self.fan_label.config(text=f"{int(new_duty)}%")
    
    # События для ползунка кондиционера
    def start_drag_ac(self, event):
        self.dragging_ac = True
    
    def stop_drag_ac(self, event):
        self.dragging_ac = False
    
    def on_drag_ac(self, event):
        if self.dragging_ac and not self.auto_mode:
            self.ac_duty = float(self.ac_slider.get())
            self.ac_label.config(text=f"{int(self.ac_duty)}%")
    
    def on_mousewheel_ac(self, event):
        if not self.auto_mode:
            if event.delta > 0:
                self.ac_duty = min(100, self.ac_duty + 2)
            else:
                self.ac_duty = max(0, self.ac_duty - 2)
            self.ac_slider.set(self.ac_duty)
            self.ac_label.config(text=f"{int(self.ac_duty)}%")
    
    def on_ac_slider_change(self, value):
        if not self.auto_mode:
            self.ac_duty = float(value)
            self.ac_label.config(text=f"{int(self.ac_duty)}%")
    
    # События для ползунка вентилятора
    def start_drag_fan(self, event):
        self.dragging_fan = True
    
    def stop_drag_fan(self, event):
        self.dragging_fan = False
    
    def on_drag_fan(self, event):
        if self.dragging_fan and not self.auto_mode:
            self.fan_duty = float(self.fan_slider.get())
            self.fan_label.config(text=f"{int(self.fan_duty)}%")
    
    def on_mousewheel_fan(self, event):
        if not self.auto_mode:
            if event.delta > 0:
                self.fan_duty = min(100, self.fan_duty + 2)
            else:
                self.fan_duty = max(0, self.fan_duty - 2)
            self.fan_slider.set(self.fan_duty)
            self.fan_label.config(text=f"{int(self.fan_duty)}%")
    
    def on_fan_slider_change(self, value):
        if not self.auto_mode:
            self.fan_duty = float(value)
            self.fan_label.config(text=f"{int(self.fan_duty)}%")
    
    def toggle_mode(self):
        """Переключение между автоматическим и ручным режимом"""
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.mode_button.config(text="Автоматический режим", bg='#2a5a2a')
            self.ac_slider.config(state=tk.DISABLED)
            self.fan_slider.config(state=tk.DISABLED)
            self.ac_minus.config(state=tk.DISABLED)
            self.ac_plus.config(state=tk.DISABLED)
            self.fan_minus.config(state=tk.DISABLED)
            self.fan_plus.config(state=tk.DISABLED)
        else:
            self.mode_button.config(text="Ручной режим", bg='#5a2a2a')
            self.ac_slider.config(state=tk.NORMAL)
            self.fan_slider.config(state=tk.NORMAL)
            self.ac_minus.config(state=tk.NORMAL)
            self.ac_plus.config(state=tk.NORMAL)
            self.fan_minus.config(state=tk.NORMAL)
            self.fan_plus.config(state=tk.NORMAL)
    
    def toggle_optimization(self):
        """Включение/выключение оптимизации"""
        self.optimization_enabled = not self.optimization_enabled
        if self.optimization_enabled:
            self.opt_button.config(text="Оптимизация ВКЛ", bg='#2a5a2a')
        else:
            self.opt_button.config(text="Оптимизация ВЫКЛ", bg='#5a2a2a')
    
    def on_window_resize(self, event):
        pass
    
    def animate_fan(self):
        while self.running:
            try:
                self.fan_angle += self.fan_duty * 0.3
                self.ac_compressor_angle += self.ac_duty * 0.5  # Компрессор вращается быстрее
                
                if self.fan_angle > 360:
                    self.fan_angle -= 360
                if self.ac_compressor_angle > 360:
                    self.ac_compressor_angle -= 360
                
                self.root.after(0, self.draw_fan)
                self.root.after(0, self.draw_ac)
                self.root.after(0, lambda: self.draw_pwm_signal(self.ac_pwm_canvas, self.ac_duty, "Скважность", '#88ccff', '#3366cc'))
                self.root.after(0, lambda: self.draw_pwm_signal(self.fan_pwm_canvas, self.fan_duty, "Скважность", '#ffff99', '#cc8800'))
                self.root.after(0, self.draw_temp_graph)
                self.root.after(0, self.draw_co2_graph)
                self.root.after(0, self.update_ui)
                
                time.sleep(0.05)
            except Exception as e:
                print(f"Error in animation: {e}")
                break
    
    def on_closing(self):
        self.running = False
        time.sleep(0.2)
        self.root.destroy()

def main():
    root = tk.Tk()
    app = TramwayClimateSimulator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()