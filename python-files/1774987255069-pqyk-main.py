import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Режимы модели СОСОМО
modes = {
    "Обычный": {"c1": 3.2, "c2": 2.5, "p1": 1.05, "p2": 0.38, "test_size": 30, "help": "< 50 KLOC"},
    "Промежуточный": {"c1": 3.0, "c2": 2.5, "p1": 1.12, "p2": 0.35, "test_size": 300, "help": "50-500 KLOC"},
    "Встроенный": {"c1": 2.8, "c2": 2.5, "p1": 1.2, "p2": 0.32, "test_size": 700, "help": "> 500 KLOC"},
}

def from_size_to_mode(kloc):
    if kloc < 50:
        return modes["Обычный"]
    if kloc > 500:
        return modes["Встроенный"]
    return modes["Промежуточный"]


def solver(driver_values, kloc):
    """
    Функция, которая вычисляет трудоёмкость по модели COCOMO.
    
    Аргументы:
        driver_values (dict): Словарь вида {id_драйвера: значение}
        kloc (float): Размер проекта в тысячах строк кода
    
    Возвращает:
        tuple: (EAF, трудоёмкость в человеко-месяцах)
    """
    # Вычисляем EAF
    eaf = 1.0
    for _, value in driver_values.items():
        eaf *= value

    # Получение из KLOC => с1, с2, р1, р2
    mode = from_size_to_mode(kloc)
    
    # Трудозатраты
    labor_costs = mode["c1"] * eaf * kloc**mode["p1"]
    
    # Время
    time = mode["c2"] * labor_costs**mode["p2"]
    
    return eaf, labor_costs, time


def get_value_from_scale(scale_value, min_val, max_val):
    """
    Преобразует значение слайдера (0-100) в коэффициент драйвера.
    Для драйверов с "обратной" шкалой (где высокое значение = меньший коэффициент)
    используется линейная интерполяция между min и max.
    """
    # Нормализуем значение от 0 до 1
    t = scale_value / 100.0
    
    # Линейная интерполяция
    value = min_val + t * (max_val - min_val)
    return value


def calculate_distribution(effort, salary=60):
    """
    Рассчитывает распределение трудозатрат и бюджета по видам деятельности.
    
    Аргументы:
        effort (float): Общая трудоёмкость в человеко-месяцах
        salary (float): Средняя зарплата в тыс. рублей (по умолчанию 60)
    
    Возвращает:
        list: Список словарей с данными для таблицы
    """
    # Данные о распределении бюджета по видам деятельности (%)
    distribution = [
        ("Анализ требований", 4),
        ("Проектирование продукта", 12),
        ("Программирование", 44),
        ("Тестирование", 6),
        ("Верификация и аттестация", 14),
        ("Канцелярия проекта", 7),
        ("Управление конфигурацией и QA", 7),
        ("Создание руководств", 6),
    ]
    
    results = []
    for activity, percent in distribution:
        person_months = effort * (percent / 100)
        cost = person_months * salary
        results.append({
            "activity": activity,
            "percent": percent,
            "person_months": person_months,
            "cost": cost
        })
    
    return results


# Собираем значения драйверов в словарь и вызываем функцию solver
def get_drivers_value_and_call_solver(kloc, driver_values = {}):

    # Собираем значения драйверов в словарь
    for driver_id, info in driver_scales.items():

        if driver_id in driver_values:
            continue

        scale_value = info["scale"].get()
        min_val = info["min"]
        max_val = info["max"]
            
        # Преобразуем значение слайдера в коэффициент
        coeff = get_value_from_scale(scale_value, min_val, max_val)
        driver_values[driver_id] = coeff
        
    # Вызываем функцию solver
    return solver(driver_values, kloc)


def on_solve():
    """Собирает значения из всех слайдеров и поля KLOC, передаёт их в функцию solver"""
    try:
        # Получаем значение KLOC
        kloc_str = kloc_var.get().strip()
        if not kloc_str:
            messagebox.showerror("Ошибка", "Пожалуйста, введите размер проекта (KLOC)")
            return
        
        kloc = float(kloc_str)
        if kloc <= 0:
            messagebox.showerror("Ошибка", "Размер проекта должен быть положительным числом")
            return
        
        # Собираем значения драйверов в словарь и вызываем функцию solver
        eaf, labor_costs, time = get_drivers_value_and_call_solver(kloc)
        
        # Показываем сообщение с результатами
        res_label.config(text = f"EAF = {eaf:.2f}; Трудоёмкость = {labor_costs:.2f} чел.-мес.; Время = {time:.2f} мес.")

        # Обновляем таблицу распределения работ
        update_work_distribution_table(labor_costs)
        
        # Обновляем таблицу стадий жизненного цикла
        update_lifecycle_table(labor_costs, time)

        # Обновляем график
        update_graph()
    
    except ValueError:
        messagebox.showerror(
            "Ошибка",
            "Пожалуйста, введите корректное числовое значение для KLOC"
        )
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")


def on_search():
    # СБОР ДАННЫХ
    factor = factor_var.get()
    mode = selected_mode.get()
    step_percent = step_search_var.get()

    kloc = modes[mode]["test_size"]

    min_factor_value = drivers_data[factor][1]
    max_factor_value = drivers_data[factor][2]

    step = (max_factor_value - min_factor_value) * step_percent / 100

    factor_values = []
    while min_factor_value <= max_factor_value:
        factor_values += [min_factor_value]
        min_factor_value += step

    res_times = []
    res_efforts = []

    # ЗАМЕРЫ
    for factor_value in factor_values:
        _, effort, time = get_drivers_value_and_call_solver(kloc, driver_values = {factor: factor_value})
        res_times += [time]
        res_efforts += [effort]

    # ПОСТРОЕНИЕ ГРАФИКОВ
    # Очищаем фрейм для графиков
    for widget in search_graph_frame.winfo_children():
        widget.destroy()
        
    # Создаём фигуру с двумя подграфиками
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 2))
        
    # График 1: Зависимость трудоёмкости от фактора
    ax1.plot(factor_values, res_efforts, 'b-o', linewidth=2, markersize=4)
    ax1.set_xlabel(f'Значение фактора {factor}', fontsize=8)
    ax1.set_ylabel('Трудоёмкость (чел.-мес.)', fontsize=8)
    ax1.set_title(f'Зависимость трудоёмкости от {factor}', fontsize=10, pad=20)
    ax1.grid(True, alpha=0.3)
        
    # Добавляем значения на график
    offset_points_step = 1 + (step_percent < 7) * (7 - step_percent)

    i = -1
    for x, y in zip(factor_values, res_efforts):
        i += 1
        if offset_points_step == 1 or i % offset_points_step == 0:
            ax1.plot(x, y, 'bo', markersize=6, markeredgecolor='darkblue', markeredgewidth=1)
            ax1.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                        xytext=(0, 5), ha='center', fontsize=7)
        
    # График 2: Зависимость времени от фактора
    ax2.plot(factor_values, res_times, 'r-s', linewidth=2, markersize=4)
    ax2.set_xlabel(f'Значение фактора {factor}', fontsize=8)
    ax2.set_ylabel('Время разработки (мес.)', fontsize=8)
    ax2.set_title(f'Зависимость времени от {factor}', fontsize=10, pad=20)
    ax2.grid(True, alpha=0.3)
        
    # Добавляем значения на график
    i = -1
    for x, y in zip(factor_values, res_times):
        i += 1
        if offset_points_step == 1 or i % offset_points_step == 0:
            ax2.plot(x, y, 'rs', markersize=6, markeredgecolor='darkred', markeredgewidth=1)
            ax2.annotate(f'{y:.1f}', (x, y), textcoords="offset points", 
                        xytext=(0, 5), ha='center', fontsize=7)
            
    plt.tight_layout()
        
    # Встраиваем графики
    canvas = FigureCanvasTkAgg(fig, master=search_graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
        
    plt.close(fig)


def update_value_label(driver_id):
    """Обновляет текстовую метку с текущим значением драйвера"""
    info = driver_scales[driver_id]
    scale_value = info["scale"].get()
    min_val = info["min"]
    max_val = info["max"]
    
    coeff = get_value_from_scale(scale_value, min_val, max_val)
    info["label_value"].config(text=f"{coeff:.3f}")


def update_graph():
    """Обновляет график на основе данных из таблицы"""
    # Собираем данные из таблицы
    stages = []
    workers = []
    
    for item in lifecycle_table.get_children():
        values = lifecycle_table.item(item)["values"]
        if values and values[0] not in ["Итого", "Итого + планирование"]:
            stages.append(values[0])
            workers.append(float(values[5]))
    
    # Очищаем предыдущий график
    for widget in graph_frame.winfo_children():
        widget.destroy()
    
    if not stages:
        return
    
    # Создаём простой чёрно-белый график
    fig, ax = plt.subplots(figsize=(1.8, 1.8))
    
    # Рисуем столбцы без цвета (только контур)
    x = list(range(1, len(stages) + 1))
    bars = ax.bar(x, workers, color='white', edgecolor='black', linewidth=1)

    ax.set_xticks(x)
    ax.set_xticklabels(x)

    ax.set_ylabel('Число сотрудников', fontsize=8)
    ax.set_title('График по числу сотрудников\nна стадиях жизненного цикла', fontsize=8, pad=5)

    # Добавляем значения над столбцами
    for bar, value in zip(bars, workers):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(value)}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    # Встраиваем график
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    plt.close(fig) 


def update_work_distribution_table(effort):
    """Обновляет таблицу распределения работ"""
    # Очищаем таблицу
    for row in work_table.get_children():
        work_table.delete(row)
    
    # Рассчитываем распределение
    distribution = calculate_distribution(effort)
    
    # Заполняем таблицу
    total_person_months = 0
    total_cost = 0
    
    for item in distribution:
        work_table.insert("", "end", values=(
            item["activity"],
            f"{item['percent']}%",
            f"{item['person_months']:.2f}",
            f"{item['cost']:.2f}"
        ), tags=("other",))
        total_person_months += item["person_months"]
        total_cost += item["cost"]
    
    # Добавляем итоговую строку
    work_table.insert("", "end", values=(
        "Итого",
        "100%",
        f"{total_person_months:.2f}",
        f"{total_cost:.2f}"
    ), tags=("total",))
    
    # Стили для строк
    work_table.tag_configure("total", font=("Arial", 10, "bold"))
    work_table.tag_configure("other", font=("Arial", 10))


def update_lifecycle_table(effort, time):
    """Обновляет таблицу стадий жизненного цикла"""
    # Очищаем таблицу
    for row in lifecycle_table.get_children():
        lifecycle_table.delete(row)
    
    # Данные о распределении по стадиям жизненного цикла
    lifecycle_data = [
        ("1. Планирование и определение требований", 8, 36),
        ("2. Проектирование продукта", 18, 36),
        ("3. Детальное проектирование", 25, 18),
        ("4. Кодирование и тестирование отдельных модулей", 26, 18),
        ("5. Интеграция и тестирование", 31, 28),
    ]
    
    # Рассчитываем трудоёмкость (как процент от общей)
    total_person_months = 0
    total_time = 0
    all_count_workers = 0

    is_first = True
    first_labor_months = None
    first_time_months = None
    first_count_workers = None
    
    for stage, labor_percent, time_percent in lifecycle_data:
        labor_months = effort * (labor_percent / 100)
        time_months = time * (time_percent / 100)
        count_workers = round(labor_months / time_months)
        
        lifecycle_table.insert("", "end", values=(
            stage,
            f"{labor_percent}%",
            f"{labor_months:.2f}",
            f"{time_percent}%",
            f"{time_months:.2f}",
            f"{count_workers}"
        ))

        if is_first:
            first_labor_months = labor_months
            first_time_months = time_months
            first_count_workers = count_workers
            is_first = False
        else:
            total_person_months += labor_months
            total_time += time_months
            all_count_workers += count_workers
    
    # Добавляем итоговую строку
    lifecycle_table.insert("", "end", values=(
        "Итого",
        "100%",
        f"{total_person_months:.2f}",
        "100%",
        f"{total_time:.2f}",
        f"{all_count_workers}"
    ), tags=("total",))

    # Добавляем итоговую + планирование строку
    lifecycle_table.insert("", "end", values=(
        "Итого + планирование",
        f"{100 + lifecycle_data[0][1]:.2f}%",
        f"{total_person_months + first_labor_months:.2f}",
        f"{100 + lifecycle_data[0][2]:.2f}%",
        f"{total_time + first_time_months:.2f}",
        f"{all_count_workers + first_count_workers}"
    ), tags=("total",))
    
    lifecycle_table.tag_configure("total", font=("Arial", 10, "bold"))


# Создаём главное окно
root = tk.Tk()
root.title("Лабораторная работа №6 по ЭПИ (COCOMO)")
root.geometry("1540x907")

# Запрет изменения размера
root.resizable(False, False)

# Создаём основную область с прокруткой
canvas = tk.Canvas(root)
main_frame = ttk.Frame(canvas)

main_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=main_frame, anchor="nw")
canvas.pack(side="left", fill="both", expand=True)

# Словарь для хранения информации о слайдерах
driver_scales = {}

# Данные о драйверах: (название, минимальное значение, максимальное значение, значение по умолчанию в %)
# Значение по умолчанию 50% соответствует середине диапазона
drivers_data = {
    # Атрибуты программного продукта
    "RELY": ("Требуемая надежность", 0.75, 1.40, 50),
    "DATA": ("Размер базы данных", 0.94, 1.16, 50),
    "CPLX": ("Сложность продукта", 0.70, 1.65, 50),
    
    # Атрибуты компьютера
    "TIME": ("Ограничение времени выполнения", 1.00, 1.66, 50),
    "STOR": ("Ограничение объема основной памяти", 1.00, 1.56, 50),
    "VIRT": ("Изменчивость виртуальной машины", 0.87, 1.30, 50),
    "TURN": ("Время реакции компьютера", 0.87, 1.15, 50),
    
    # Атрибуты персонала
    "ACAP": ("Способности аналитика", 1.46, 0.71, 50),
    "AEXP": ("Знание приложений", 1.29, 0.82, 50),
    "PCAP": ("Способности программиста", 1.42, 0.70, 50),
    "VEXP": ("Знание виртуальной машины", 1.21, 0.90, 50),
    "LEXP": ("Знание языка программирования", 1.14, 0.95, 50),
    
    # Атрибуты проекта
    "MODP": ("Использование современных методов", 1.24, 0.82, 50),
    "TOOL": ("Использование программных инструментов", 1.24, 0.83, 50),
    "SCED": ("Требуемые сроки разработки", 1.23, 1.10, 50),
}

# Секции для группировки
sections = {
    "Атрибуты программного продукта": ["RELY", "DATA", "CPLX"],
    "Атрибуты компьютера": ["TIME", "STOR", "VIRT", "TURN"],
    "Атрибуты персонала": ["ACAP", "AEXP", "PCAP", "VEXP", "LEXP"],
    "Атрибуты проекта": ["MODP", "TOOL", "SCED"]
}


# Создаём интерфейс
row = 0

# Добавляем поле для ввода размера проекта вверху
kloc_frame = ttk.LabelFrame(main_frame, text="Параметры проекта", padding=10)
kloc_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
row += 1

kloc_label = ttk.Label(kloc_frame, text="Размер проекта (KLOC):", font=("Arial", 10, "bold"))
kloc_label.grid(row=0, column=0, sticky="w", padx=5)

kloc_var = tk.StringVar(value="100.0")
kloc_entry = ttk.Entry(kloc_frame, textvariable=kloc_var, width=15, font=("Arial", 10))
kloc_entry.grid(row=0, column=1, sticky="w", padx=5)

kloc_info = ttk.Label(
    kloc_frame, 
    text="(тысячи строк кода)",
    font=("Arial", 9),
    foreground="gray"
)
kloc_info.grid(row=0, column=2, sticky="w", padx=5)

# Настраиваем колонки внутри kloc_frame
kloc_frame.columnconfigure(1, weight=1)

# Добавляем разделитель
separator = ttk.Separator(main_frame, orient="horizontal")
separator.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
row += 1

# Создаём слайдеры для драйверов
for section_name, driver_ids in sections.items():
    # Заголовок секции
    section_label = ttk.Label(
        main_frame,
        text=section_name,
        font=("Arial", 12, "bold")
    )
    section_label.grid(row=row, column=0, sticky="w", pady=(15, 5))

    # Подсказка: низко - высоко
    help_label = ttk.Label(
        main_frame,
        text="низко" + " " * (58 - 13) + "высоко",
        font=("Arial", 8),
        foreground="gray"
    )
    help_label.grid(row=row, column=1, sticky="we", pady=(15, 5))

    row += 1
    
    # Создаём слайдеры для каждого драйвера в секции
    for driver_id in driver_ids:
        driver_name, min_val, max_val, default_pct = drivers_data[driver_id]
        
        # Метка с названием драйвера
        label = ttk.Label(
            main_frame,
            text=f"{driver_id} - {driver_name}:",
            font=("Arial", 10)
        )
        label.grid(row=row, column=0, sticky="w", padx=10, pady=5)

        # Текущее значение драйвера (справа от слайдера)
        value_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 10, "bold"),
            width=8,
            anchor="e"
        )
        value_label.grid(row=row, column=2, sticky="e", padx=10, pady=5)
        
        # Слайдер
        scale = ttk.Scale(
            main_frame,
            from_=0,
            to=100,
            orient="horizontal",
            length=200,
            value=default_pct
        )
        scale.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        
        # Сохраняем информацию о слайдере
        driver_scales[driver_id] = {
            "scale": scale,
            "label_value": value_label,
            "min": min_val,
            "max": max_val,
            "name": driver_name
        }
        
        # Функция обновления для этого конкретного драйвера
        def make_update_func(did):
            return lambda event=None: update_value_label(did)
        
        scale.configure(command=make_update_func(driver_id))
        
        # Инициализируем значение
        update_value_label(driver_id)
        
        row += 1


result_right_frame = ttk.LabelFrame(main_frame, text="Вычисление оценки основных работ и сроков", padding=10)
result_right_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

# Кнопка для отправки данных в solver
solve_btn = tk.Button(
    result_right_frame,
    text="Вычислить трудоёмкость",
    command=on_solve,
    width=23,
    height=2,
    font=("Arial", 9, "bold"),
    bg="light gray"
)
solve_btn.grid(row=0, column=0, pady=5)

res_label = ttk.Label(
    result_right_frame, 
    text="",
    font=("Arial", 9),
    foreground="red"
)
res_label.grid(row=0, column=1, sticky="w", padx=10)


row = 0

# Таблица стадий жизненного цикла
lifecycle_label = ttk.Label(main_frame, text="Распределение работ и времени по стадиям жизненного цикла", font=("Arial", 12, "bold"))
lifecycle_label.grid(row=row, column=3, sticky="w", pady=(40, 2), padx = 10)
row += 1

lifecycle_columns = ("stage", "labor_percent", "labor_months", "time_percent", "time_months", "count_workers")
lifecycle_table = ttk.Treeview(main_frame, columns=lifecycle_columns, show="headings", height=8)
lifecycle_table.heading("stage", text="Вид деятельности")
lifecycle_table.heading("labor_percent", text="Трудозатрат(%)")
lifecycle_table.heading("labor_months", text="Чел.-Месяцы")
lifecycle_table.heading("time_percent", text="Время(%)")
lifecycle_table.heading("time_months", text="Месяцы")
lifecycle_table.heading("count_workers", text="Число работников")
lifecycle_table.column("stage", width=300)
lifecycle_table.column("labor_percent", width=110)
lifecycle_table.column("labor_months", width=110)
lifecycle_table.column("time_percent", width=110)
lifecycle_table.column("time_months", width=110)
lifecycle_table.column("count_workers", width=130)
lifecycle_table.grid(row=row, column=3, rowspan=6, columnspan=2, sticky="ew", padx=10, pady=5)
row += 6


# Таблица распределения работ (Декомпозиция работ)
work_label = ttk.Label(main_frame, text="Декомпозиция работ по созданию ПО", font=("Arial", 12, "bold"))
work_label.grid(row=row, column=3, sticky="w", pady=(10, 2), padx=10)

# Создаём таблицу (Treeview) для работ
work_columns = ("activity", "percent", "person_months", "cost")
work_table = ttk.Treeview(main_frame, columns=work_columns, show="headings", height=10)
work_table.heading("activity", text="Вид деятельности")
work_table.heading("percent", text="Бюджет (%)")
work_table.heading("person_months", text="Чел.-Месяцы")
work_table.heading("cost", text="Затраты (тыс. руб.)")
work_table.column("activity", width=120)
work_table.column("percent", width=30)
work_table.column("person_months", width=30)
work_table.column("cost", width=50)
work_table.grid(row=row + 1, column=3, rowspan=7, sticky="ew", padx=10, pady=5)

# Фрейм для графика справа от таблицы
graph_frame = ttk.Frame(main_frame)
graph_frame.grid(row=row, column=4, rowspan=8, sticky="nsew", padx=(2, 0), pady=2)

row += 7 + 1


# Построение графиков для исследований
search_frame = ttk.Frame(main_frame)
search_frame.grid(row=row, column=3, rowspan=8, columnspan=2, sticky="nsew", padx=(10, 0), pady=2)

search_label = ttk.Label(search_frame, text="Построение графиков\nзависимостей от факторов", font=("Arial", 12, "bold"))
search_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(2, 2))

factor_label = ttk.Label(search_frame, text="Варьируемый фактор:", font=("Arial", 10))
factor_label.grid(row=1, column=0, sticky="w", pady=(5, 5))

# выбор варьируемого фактора
factors = [*drivers_data]

factor_var = tk.StringVar(value=factors[0])

factor_combo = ttk.Combobox(
    search_frame,
    textvariable=factor_var,
    values=factors,
    state="readonly",  # чтобы нельзя было вводить руками
    width=10
)
factor_combo.grid(row=1, column=1, sticky="w", padx=5, pady=(5, 5))


# Переменная для хранения выбранного значения режима
first_mode = list(modes.keys())[0]
selected_mode = tk.StringVar(value=first_mode)  # значение по умолчанию

# Создаём радиокнопки
mode_frame = ttk.LabelFrame(search_frame, text="Выберите режим COCOMO:", padding=10)
mode_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 5))

for mode in modes.keys():
    ttk.Radiobutton(mode_frame, text=mode + " (" + modes[mode]["help"] + ")", variable=selected_mode, value=mode).pack(anchor="w")


# Слайдер для ввода шага измерений (от 1 до 100)
step_search_slider_frame = ttk.LabelFrame(search_frame, text="Выберите шаг варьирования фактора:", padding=5)
step_search_slider_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 5))

# Переменная для хранения значения
step_search_var = tk.IntVar(value=10)  # значение по умолчанию

# Создаём слайдер
step_search_slider = ttk.Scale(
    step_search_slider_frame,
    from_=1,
    to=100,
    orient="horizontal",
    variable=step_search_var,
    length=150
)
step_search_slider.grid(row=0, column=1, sticky="w", padx=5, pady=(5, 5))

# Метка для отображения текущего значения
step_search_label = ttk.Label(step_search_slider_frame, text=f"{step_search_var.get()}%")
step_search_label.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 5))

# Функция обновления метки
def update_step_search_label(*args):
    step_search_label.config(text=f"{step_search_var.get()}%")

# Привязываем обновление к изменению переменной
step_search_var.trace("w", update_step_search_label)


# Кнопка для отправки данных в searcher
search_btn = tk.Button(
    search_frame,
    text="Построить графики",
    command=on_search,
    width=32,
    height=2,
    font=("Arial", 9, "bold"),
    bg="light gray"
)
search_btn.grid(row=4, column=0, columnspan=2, pady=5)


# Фрейм для графиков

# Фрейм для графиков внутри search_frame
search_graph_frame = ttk.LabelFrame(search_frame, text="Графики зависимостей", padding=5)
search_graph_frame.grid(row=0, column=2, rowspan=5, sticky="nsew", pady=2, padx=15)

# Настраиваем вес колонок для правильного растяжения
main_frame.columnconfigure(1, weight=1)

# Запускаем главный цикл
root.mainloop()