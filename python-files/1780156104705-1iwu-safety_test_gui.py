import tkinter as tk
from tkinter import ttk, messagebox
import random
from datetime import datetime

# Все 75 вопросов (без изменений)
questions = [
    # Тема 1: Электробезопасность
    {"q": "1. Безопасное расстояние до частей под напряжением до 1000 В?", "t": "single", "o": ["0.35 м", "0.6 м", "1 м", "1.5 м"], "a": "1"},
    {"q": "2. Знак 'Осторожно! Электрическое напряжение'?", "t": "single", "o": ["Запрет курения", "Электричество", "Пожарный кран", "Выход"], "a": "1"},
    {"q": "3. Первое действие при поражении током?", "t": "single", "o": ["Искусственное дыхание", "Освободить от тока", "Позвать помощь", "Дать воды"], "a": "1"},
    {"q": "4. Основные средства защиты до 1000 В (выберите два)?", "t": "multi", "o": ["Перчатки", "Указатели напряжения", "Штанги", "Галоши", "Очки"], "a": ["0", "1"]},
    {"q": "5. Что запрещено в электроустановках (два)?", "t": "multi", "o": ["Работать в каске", "Работать один без допуска", "Трогать кабель без проверки", "Использовать изолированный инструмент"], "a": ["1", "2"]},
    {"q": "6. Опасное напряжение переменного тока (два)?", "t": "multi", "o": ["12 В", "36 В", "42 В", "110 В"], "a": ["2", "3"]},
    {"q": "7. Документ по организации работ в электроустановках?", "t": "text", "a": "Правила устройства электроустановок"},
    {"q": "8. Что такое 'шаговое напряжение'?", "t": "text", "a": "Напряжение между точками на земле"},
    {"q": "9. Для чего защитное заземление?", "t": "text", "a": "Для защиты от поражения током"},
    {"q": "10. Порядок помощи при поражении током:", "t": "order", "o": ["Определить пульс", "Вызвать скорую", "Освободить от тока", "Начать реанимацию", "Уложить"], "a": [2, 4, 0, 3, 1]},
    {"q": "11. Порядок подготовки рабочего места:", "t": "order", "o": ["Отключить", "Вывесить плакаты", "Проверить напряжение", "Установить заземления", "Оградить"], "a": [0, 1, 2, 3, 4]},
    {"q": "12. Порядок освобождения от тока на высоте:", "t": "order", "o": ["Обесточить", "Защитить от падения", "Спустить", "Оказать помощь"], "a": [0, 1, 2, 3]},
    {"q": "13. НЕ причина поражения током?", "t": "single", "o": ["Прикосновение к частям под напряжением", "Напряжение на металле", "Шаговое напряжение", "Работа в перчатках"], "a": "3"},
    {"q": "14. НЕ запрещающий плакат?", "t": "single", "o": ["'Не включать'", "'Работать здесь'", "'Не открывать'", "'Не влезай'"], "a": "1"},
    {"q": "15. НЕВЕРНО про группы электробезопасности?", "t": "single", "o": ["I группу присваивает специалист", "II группу - после обучения", "Стажировка для IV-V групп", "I группа только для электротехников"], "a": "3"},

    # Тема 2: Пожарная безопасность
    {"q": "16. Что такое 'пожар'?", "t": "single", "o": ["Неконтролируемое горение", "Контролируемое горение", "Любой огонь", "Задымление"], "a": "0"},
    {"q": "17. Номер пожарной охраны?", "t": "single", "o": ["01 или 101", "02 или 102", "03 или 103", "112"], "a": "0"},
    {"q": "18. Огнетушитель для электроустановок до 1000 В?", "t": "single", "o": ["Водный", "Воздушно-пенный", "Порошковый", "Углекислотный"], "a": "2"},
    {"q": "19. Горючие материалы (два)?", "t": "multi", "o": ["Древесина", "Песок", "Бензин", "Вода"], "a": ["0", "2"]},
    {"q": "20. Что запрещено при пожаре (два)?", "t": "multi", "o": ["Открывать окна", "Пользоваться лифтом", "Звонить 101", "Пытаться тушить"], "a": ["0", "1"]},
    {"q": "21. Треугольник огня (три)?", "t": "multi", "o": ["Горючее вещество", "Катализатор", "Кислород", "Источник зажигания"], "a": ["0", "2", "3"]},
    {"q": "22. Три способа прекращения горения?", "t": "text", "a": "охлаждение изоляция флегматизация"},
    {"q": "23. Что такое АУПТ?", "t": "text", "a": "Автоматическая установка пожаротушения"},
    {"q": "24. Назначение пожарного гидранта?", "t": "text", "a": "Для забора воды на тушение"},
    {"q": "25. Порядок при обнаружении пожара:", "t": "order", "o": ["Позвонить 101", "Начать тушить", "Оповестить людей", "Начать эвакуацию", "Встретить пожарных"], "a": [2, 0, 1, 3, 4]},
    {"q": "26. Порядок использования углекислотного огнетушителя:", "t": "order", "o": ["Сорвать пломбу", "Направить раструб", "Подойти", "Нажать рычаг"], "a": [0, 2, 1, 3]},
    {"q": "27. Порядок эвакуации из задымленного помещения:", "t": "order", "o": ["Закрыть дверь", "Накрыться тканью", "Идти к выходу", "Дышать через ткань"], "a": [1, 3, 2, 0]},
    {"q": "28. НЕ ЛВЖ?", "t": "single", "o": ["Ацетон", "Дизельное топливо", "Керосин", "Вода"], "a": "3"},
    {"q": "29. НЕ для тушения электрооборудования?", "t": "single", "o": ["Углекислотный", "Порошковый", "Воздушно-пенный", "Асбестовое полотно"], "a": "2"},
    {"q": "30. НЕВЕРНО про противопожарный режим?", "t": "single", "o": ["Курить в отведенных местах", "Держать выходы свободными", "Оставлять оборудование включенным", "Работы по наряду"], "a": "2"},

    # Тема 3: Охрана труда
    {"q": "31. Что такое охрана труда?", "t": "single", "o": ["Система сохранения жизни", "Медобслуживание", "Выдача спецодежды", "Контроль дисциплины"], "a": "0"},
    {"q": "32. Кто проводит вводный инструктаж?", "t": "single", "o": ["Руководитель", "Специалист по ОТ", "Профсоюз", "Инспектор"], "a": "1"},
    {"q": "33. Периодичность повторного инструктажа?", "t": "single", "o": ["Раз в год", "Раз в 3 месяца", "Раз в 5 лет", "Раз в полгода"], "a": "0"},
    {"q": "34. Обязательные инструктажи (3 и более)?", "t": "multi", "o": ["Вводный", "Первичный", "Повторный", "Внеплановый", "Очередной"], "a": ["0", "1", "2", "3"]},
    {"q": "35. Обязанности работодателя (2 и более)?", "t": "multi", "o": ["Обеспечить СИЗ", "Провести СОУТ", "Застраховать жизнь", "Обучить работников"], "a": ["0", "1", "3"]},
    {"q": "36. Когда внеплановый инструктаж (2 и более)?", "t": "multi", "o": ["Новые нормативы", "По расписанию", "Нарушение ОТ", "Перерыв 60 дней"], "a": ["0", "2"]},
    {"q": "37. Три принципа госполитики в ОТ?", "t": "text", "a": "приоритет жизни социальное партнерство госуправление"},
    {"q": "38. Что такое СИЗ?", "t": "text", "a": "Средства индивидуальной защиты"},
    {"q": "39. Кто может остановить работы при угрозе?", "t": "text", "a": "работник специалист профсоюз"},
    {"q": "40. Порядок при несчастном случае:", "t": "order", "o": ["Оказать помощь", "Сохранить обстановку", "Сообщить органам", "Создать комиссию"], "a": [0, 1, 3, 2]},
    {"q": "41. Порядок первичного инструктажа:", "t": "order", "o": ["Рассказать об условиях", "Показать приемы", "Ознакомить с инструкцией", "Объяснить СИЗ", "Проверить знания"], "a": [0, 2, 3, 1, 4]},
    {"q": "42. Порядок при неисправности оборудования:", "t": "order", "o": ["Остановить работу", "Сообщить руководителю", "Вывесить табличку", "Не начинать работу"], "a": [0, 1, 2, 3]},
    {"q": "43. НЕ обязательный документ по ОТ?", "t": "single", "o": ["Положение СУОТ", "Журналы", "Инструкции", "Финансовый отчет"], "a": "3"},
    {"q": "44. НЕВЕРНО про СИЗ?", "t": "single", "o": ["Выдают бесплатно", "Обязаны использовать", "Должны подходить по размеру", "Списывают если грязные"], "a": "3"},
    {"q": "45. НЕ вредный фактор?", "t": "single", "o": ["Шум", "Стресс", "Работа на высоте", "Компьютер"], "a": "3"},

    # Тема 4: Антитеррористическая безопасность
    {"q": "46. Что такое теракт?", "t": "single", "o": ["Взрыв для воздействия на власть", "Нарушение порядка", "Проникновение", "Экстремистские слова"], "a": "0"},
    {"q": "47. Единый номер экстренных служб?", "t": "single", "o": ["01", "02", "03", "112"], "a": "3"},
    {"q": "48. При обнаружении подозрительного предмета?", "t": "single", "o": ["Осмотреть", "Сообщить в полицию", "Выбросить", "Обезвредить"], "a": "1"},
    {"q": "49. Признаки взрывного устройства (2 и более)?", "t": "multi", "o": ["Провода", "Необычное место", "Запах", "Наклейка с адресом"], "a": ["0", "1", "2"]},
    {"q": "50. При телефонной угрозе (2 и более)?", "t": "multi", "o": ["Записать разговор", "Бросить трубку", "Определить голос", "Сообщить начальству"], "a": ["0", "2", "3"]},
    {"q": "51. Цель антитеррористических мер (2 и более)?", "t": "multi", "o": ["Затруднить теракт", "Предотвратить всё", "Подготовить персонал", "Запретить вход"], "a": ["0", "2"]},
    {"q": "52. Что такое 'Нетерпимость' к терроризму?", "t": "text", "a": "Неприятие идеологии терроризма"},
    {"q": "53. Кто глава антитеррористической комиссии?", "t": "text", "a": "Руководитель организации"},
    {"q": "54. Что такое 'контролируемая территория'?", "t": "text", "a": "Территория с пропускным режимом"},
    {"q": "55. Порядок при телефонной угрозе:", "t": "order", "o": ["Не вешать трубку", "Записать", "Заметить особенности", "Сообщить", "Засечь время"], "a": [4, 0, 1, 2, 3]},
    {"q": "56. Порядок при подозрительном предмете:", "t": "order", "o": ["Сообщить", "Не трогать", "Отключить связь", "Отойти", "Помочь эвакуации"], "a": [1, 2, 0, 3, 4]},
    {"q": "57. Порядок эвакуации:", "t": "order", "o": ["Объявить", "Остановить работу", "Идти к выходам", "Взять вещи", "Помочь коллегам"], "a": [0, 1, 3, 2, 4]},
    {"q": "58. Что НЕ должно вызывать подозрения?", "t": "single", "o": ["Портфель под столом", "Телефон на столе", "Коробка с проводами", "Пакет у двери"], "a": "1"},
    {"q": "59. НЕВЕРНО при захвате заложников?", "t": "single", "o": ["Выполнять требования", "Бежать не глядя", "Не спорить", "Запомнить террористов"], "a": "1"},
    {"q": "60. НЕ задача антитеррористической комиссии?", "t": "single", "o": ["Паспорт безопасности", "Контроль мероприятий", "Расследование несчастных случаев", "Обучение персонала"], "a": "2"},

    # Тема 5: Гражданская оборона и ЧС
    {"q": "61. Что такое ЧС?", "t": "single", "o": ["Обстановка после аварии", "Отклонение от процесса", "С полицией", "Отключение света"], "a": "0"},
    {"q": "62. Сигнал 'Внимание всем!'?", "t": "single", "o": ["Сирена 3 минуты", "Гудки", "Звонки", "Музыка"], "a": "0"},
    {"q": "63. При сигнале 'Внимание всем!'?", "t": "single", "o": ["Работать дальше", "Уйти", "Включить телевизор", "Собрать вещи"], "a": "2"},
    {"q": "64. ЧС природного характера (2 и более)?", "t": "multi", "o": ["Землетрясение", "Авария на заводе", "Наводнение", "Беспорядки"], "a": ["0", "2"]},
    {"q": "65. Задачи ГО (2 и более)?", "t": "multi", "o": ["Обучать население", "Эвакуировать", "Спасательные работы", "Культурные мероприятия"], "a": ["0", "1", "2"]},
    {"q": "66. Что в аптечке (2 и более)?", "t": "multi", "o": ["Бинт", "Жгут", "Антибиотики", "Обезболивающие"], "a": ["0", "1"]},
    {"q": "67. Что такое СИЗ в ГО?", "t": "text", "a": "Средства индивидуальной защиты"},
    {"q": "68. Основной способ защиты населения?", "t": "text", "a": "Укрытие в защитных сооружениях"},
    {"q": "69. Сооружение для защиты от ЧС?", "t": "text", "a": "Убежище"},
    {"q": "70. Порядок при 'Химической тревоге':", "t": "order", "o": ["Надеть противогаз", "Закрыть окна", "Загерметизировать", "Включить радио"], "a": [0, 1, 2, 3]},
    {"q": "71. Порядок заполнения убежища:", "t": "order", "o": ["Пустить женщин", "Разместить", "Выключить свет", "Зарегистрировать", "Закрыть двери"], "a": [3, 0, 1, 4, 2]},
    {"q": "72. Порядок эвакуации из зоны ЧС:", "t": "order", "o": ["Взять документы", "Выключить всё", "Закрыть квартиру", "Прийти на пункт", "Следовать указаниям"], "a": [0, 1, 2, 3, 4]},
    {"q": "73. НЕ фактор ядерного взрыва?", "t": "single", "o": ["Ударная волна", "Свет", "Радиация", "Влажность"], "a": "3"},
    {"q": "74. НЕВЕРНО про защиту дыхания?", "t": "single", "o": ["Повязка защищает", "Противогаз надежен", "Можно мокрую ткань", "Маска не от ОВ"], "a": "0"},
    {"q": "75. НЕ рекомендуется при наводнении?", "t": "single", "o": ["На крышу", "Самому уплыть", "Ждать помощи", "Выключить свет"], "a": "1"}
]

class SafetyTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Тест по безопасности")
        self.root.geometry("900x650")
        self.root.configure(bg="#F0F2F5")
        self.root.resizable(False, False)
        self.root.eval('tk::PlaceWindow . center')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#F0F2F5', font=('Segoe UI', 11))
        style.configure('SubHeader.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#4A4A4A', background='#F0F2F5')
        style.configure('Question.TLabel', font=('Segoe UI', 13, 'bold'), foreground='#2B2B2B', background='#FFFFFF', wraplength=700)
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8, borderwidth=0, relief='flat')
        style.configure('Primary.TButton', background='#1F3A6E', foreground='white')
        style.map('Primary.TButton', background=[('active', '#2A4B8C'), ('!active', '#1F3A6E')])
        style.configure('Danger.TButton', background='#C0392B', foreground='white')
        style.configure('Success.TButton', background='#27AE60', foreground='white')
        style.configure('TProgressbar', thickness=20, background='#1F3A6E', troughcolor='#E0E0E0')

        self.name = tk.StringVar()
        self.current = 0
        self.errors = 0
        self.max_errors = 2
        self.questions = []
        self.answers = []
        self.vars = []
        self.failed = False

        self.main_menu()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def main_menu(self):
        self.clear()

        main_content = tk.Frame(self.root, bg='#F0F2F5')
        main_content.pack(fill='both', expand=True)

        canvas = tk.Canvas(main_content, bg='#F0F2F5', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_content, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#F0F2F5')

        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", on_canvas_configure)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        name_frame = tk.Frame(scrollable_frame, bg='#F0F2F5')
        name_frame.pack(pady=(20, 10))
        ttk.Label(name_frame, text="Ф.И.О. сотрудника:", style='SubHeader.TLabel').pack(anchor='w')
        entry_name = ttk.Entry(name_frame, textvariable=self.name, font=('Segoe UI', 13), width=40)
        entry_name.pack(ipady=4, pady=5)

        ttk.Label(scrollable_frame, text="Выберите раздел:", style='SubHeader.TLabel').pack(pady=(15, 5))
        topics = [
            ("Все темы", 0),
            ("Электробезопасность", 1),
            ("Пожарная безопасность", 2),
            ("Охрана труда", 3),
            ("Антитеррористическая безопасность", 4),
            ("Гражданская оборона", 5)
        ]
        btn_container = tk.Frame(scrollable_frame, bg='#F0F2F5')
        btn_container.pack(pady=5)
        for t, n in topics:
            ttk.Button(btn_container, text=t, command=lambda tn=n: self.start(tn), width=40).pack(pady=4)

        rules_frame = tk.Frame(scrollable_frame, bg='#FFFFFF', relief='solid', bd=1)
        rules_frame.pack(pady=(20, 10), fill='x', ipady=10, padx=20)
        ttk.Label(rules_frame, text="ПРАВИЛА ТЕСТИРОВАНИЯ", font=('Segoe UI', 12, 'bold'),
                  foreground='#C0392B', background='#FFFFFF').pack(pady=(10, 5))
        ttk.Label(rules_frame, text="• Тест состоит из 15 случайных вопросов из выбранной темы",
                  background='#FFFFFF').pack(anchor='w', padx=30)
        ttk.Label(rules_frame, text="• Допускается 0 или 1 ошибка (при 2-х ошибках тест считается не сданным)",
                  background='#FFFFFF').pack(anchor='w', padx=30)
        ttk.Label(rules_frame, text="• Внимательно читайте вопросы, выбирайте ответы и следуйте указаниям",
                  background='#FFFFFF').pack(anchor='w', padx=30)

    def start(self, topic):
        if not self.name.get().strip():
            messagebox.showwarning("Предупреждение", "Введите фамилию и инициалы!")
            return

        all_q = questions if topic == 0 else questions[(topic-1)*15:(topic-1)*15+15]
        self.questions = random.sample(all_q, min(15, len(all_q)))
        self.current = 0
        self.errors = 0
        self.failed = False
        self.answers = [None] * len(self.questions)
        self.vars = []
        self.show()

    def show(self):
        self.clear()
        if self.failed or self.current >= len(self.questions):
            self.results()
            return

        q = self.questions[self.current]

        top_panel = tk.Frame(self.root, bg='#FFFFFF', relief='solid', bd=1)
        top_panel.pack(fill='x', padx=10, pady=(10, 0))

        progress = ttk.Progressbar(top_panel, orient='horizontal', length=400, mode='determinate',
                                   value=((self.current)/len(self.questions))*100)
        progress.pack(side='left', padx=20, pady=15, fill='x', expand=True)
        progress_label = ttk.Label(top_panel, text=f"Вопрос {self.current+1} из {len(self.questions)}",
                                   background='#FFFFFF', font=('Segoe UI', 10, 'bold'))
        progress_label.pack(side='left', padx=10)

        error_frame = tk.Frame(top_panel, bg='#FFFFFF')
        error_frame.pack(side='right', padx=20, pady=10)
        ttk.Label(error_frame, text="Ошибки:", background='#FFFFFF', font=('Segoe UI', 10)).pack(side='left')
        for i in range(self.max_errors + 1):
            if i < self.errors:
                color = '#C0392B'
                symbol = '✗'
            elif i == self.max_errors:
                color = '#E67E22'
                symbol = '✗'
            else:
                color = '#BDC3C7'
                symbol = '○'
            lbl = ttk.Label(error_frame, text=symbol, foreground=color, font=('Segoe UI', 12, 'bold'),
                            background='#FFFFFF')
            lbl.pack(side='left', padx=3)

        question_frame = tk.Frame(self.root, bg='#FFFFFF', relief='solid', bd=1)
        question_frame.pack(fill='both', expand=True, padx=10, pady=10)

        q_label = tk.Label(question_frame, text=q["q"], font=('Segoe UI', 13, 'bold'), fg='#2B2B2B',
                           bg='#FFFFFF', wraplength=750, justify='left')
        q_label.pack(pady=15, padx=25, anchor='w')

        answer_frame = tk.Frame(question_frame, bg='#FFFFFF')
        answer_frame.pack(fill='both', expand=True, padx=25, pady=5)

        self.vars = []
        if q["t"] == "single":
            v = tk.StringVar()
            self.vars.append(v)
            for i, o in enumerate(q["o"]):
                rb = ttk.Radiobutton(answer_frame, text=o, variable=v, value=str(i))
                rb.pack(anchor='w', pady=5)

        elif q["t"] == "multi":
            for i, o in enumerate(q["o"]):
                var = tk.BooleanVar()
                self.vars.append(var)
                cb = ttk.Checkbutton(answer_frame, text=o, variable=var)
                cb.pack(anchor='w', pady=4)

        elif q["t"] == "text":
            v = tk.StringVar()
            self.vars.append(v)
            ttk.Label(answer_frame, text="Введите ответ:", background='#FFFFFF',
                      font=('Segoe UI', 10)).pack(anchor='w', pady=(5, 0))
            entry = ttk.Entry(answer_frame, textvariable=v, font=('Segoe UI', 12), width=60)
            entry.pack(ipady=4, pady=10, fill='x')

        elif q["t"] == "order":
            ttk.Label(answer_frame, text="Укажите последовательность (цифры 1,2,3…):",
                      background='#FFFFFF', font=('Segoe UI', 10)).pack(anchor='w', pady=(5, 10))
            for i, o in enumerate(q["o"]):
                row = tk.Frame(answer_frame, bg='#FFFFFF')
                row.pack(anchor='w', pady=4, fill='x')
                var = tk.StringVar(value="")
                self.vars.append(var)
                ttk.Entry(row, textvariable=var, width=4, font=('Segoe UI', 11)).pack(side='left', padx=(0, 10))
                ttk.Label(row, text=o, background='#FFFFFF', font=('Segoe UI', 11)).pack(side='left')

        bottom_panel = tk.Frame(self.root, bg='#F0F2F5')
        bottom_panel.pack(fill='x', padx=10, pady=(0, 15))

        if self.current > 0:
            ttk.Button(bottom_panel, text="◀ Назад", command=self.prev, style='TButton').pack(side='left', padx=20)

        ttk.Button(bottom_panel, text="Проверить ответ", command=self.next,
                   style='Primary.TButton').pack(side='right', padx=20)

    def get_answer(self):
        q = self.questions[self.current]
        if not self.vars:
            return None

        if q["t"] == "single":
            return self.vars[0].get() if self.vars[0].get() else None
        elif q["t"] == "multi":
            return [str(i) for i, v in enumerate(self.vars) if v.get()]
        elif q["t"] == "text":
            return self.vars[0].get()
        elif q["t"] == "order":
            order = []
            for v in self.vars:
                val = v.get().strip()
                if val.isdigit():
                    order.append(int(val)-1)
            return order
        return None

    def check(self, q, ans):
        if ans is None or ans == "":
            return False
        if q["t"] in ["single", "multi"]:
            cor = q.get("a", [])
            if isinstance(ans, list):
                return sorted([str(a) for a in ans]) == sorted([str(c) for c in cor])
            return str(ans) in [str(c) for c in cor]
        elif q["t"] == "text":
            cor = set(q["a"].lower().split())
            usr = set(str(ans).lower().split())
            return len(usr & cor) >= len(cor)*0.6
        elif q["t"] == "order":
            return ans == q.get("a", [])
        return False

    def save(self):
        a = self.get_answer()
        if a is not None:
            self.answers[self.current] = a

    def next(self):
        self.save()

        if not self.check(self.questions[self.current], self.answers[self.current]):
            self.errors += 1
            messagebox.showwarning("Ошибка", f"Ответ неверный!\nОшибок: {self.errors} из {self.max_errors}")

            if self.errors >= self.max_errors:
                self.failed = True
                self.results()
                return

        self.current += 1
        if self.current < len(self.questions):
            self.show()
        else:
            self.results()

    def prev(self):
        self.save()
        self.current -= 1
        self.show()

    def results(self):
        self.clear()
        header_frame = tk.Frame(self.root, bg='#1F3A6E', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        ttk.Label(header_frame, text="РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ", font=('Segoe UI', 16, 'bold'),
                  foreground='white', background='#1F3A6E').pack(expand=True)

        res_frame = tk.Frame(self.root, bg='#FFFFFF', relief='solid', bd=1)
        res_frame.pack(fill='both', expand=True, padx=30, pady=30)

        if not self.failed:
            self.errors = 0
            for q, a in zip(self.questions, self.answers):
                if a is None or not self.check(q, a):
                    self.errors += 1

        ttk.Label(res_frame, text="Сведения о сотруднике", font=('Segoe UI', 14, 'bold'),
                  background='#FFFFFF', foreground='#1F3A6E').pack(pady=(20, 10))
        info_frame = tk.Frame(res_frame, bg='#FFFFFF')
        info_frame.pack(pady=5)
        ttk.Label(info_frame, text="Ф.И.О.:", background='#FFFFFF',
                  font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, sticky='e', padx=10, pady=4)
        ttk.Label(info_frame, text=self.name.get(), background='#FFFFFF',
                  font=('Segoe UI', 12)).grid(row=0, column=1, sticky='w')
        ttk.Label(info_frame, text="Дата:", background='#FFFFFF',
                  font=('Segoe UI', 12, 'bold')).grid(row=1, column=0, sticky='e', padx=10, pady=4)
        ttk.Label(info_frame, text=datetime.now().strftime('%d.%m.%Y %H:%M'),
                  background='#FFFFFF', font=('Segoe UI', 12)).grid(row=1, column=1, sticky='w')
        ttk.Label(info_frame, text="Количество ошибок:", background='#FFFFFF',
                  font=('Segoe UI', 12, 'bold')).grid(row=2, column=0, sticky='e', padx=10, pady=4)
        ttk.Label(info_frame, text=f"{self.errors} из {self.max_errors} допустимых",
                  background='#FFFFFF', font=('Segoe UI', 12)).grid(row=2, column=1, sticky='w')

        if self.errors >= self.max_errors:
            result_text = "ТЕСТ НЕ СДАН"
            color = '#C0392B'
            comment = "Допущено критическое количество ошибок. Необходима пересдача."
        else:
            result_text = "ТЕСТ СДАН УСПЕШНО"
            color = '#27AE60'
            comment = "Поздравляем! Вы успешно прошли проверку знаний."

        ttk.Label(res_frame, text=result_text, font=('Segoe UI', 18, 'bold'),
                  foreground=color, background='#FFFFFF').pack(pady=(20, 5))
        ttk.Label(res_frame, text=comment, font=('Segoe UI', 11),
                  foreground='#4A4A4A', background='#FFFFFF').pack(pady=(0, 20))

        btn_frame = tk.Frame(self.root, bg='#F0F2F5')
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Сохранить результат", command=self.save_res,
                   style='Success.TButton').pack(side='left', padx=15)
        ttk.Button(btn_frame, text="Пройти заново", command=self.main_menu,
                   style='TButton').pack(side='left', padx=15)
        ttk.Button(btn_frame, text="Выход", command=self.root.quit,
                   style='Danger.TButton').pack(side='left', padx=15)

    def save_res(self):
        fn = f"{self.name.get()}_тест_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        try:
            with open(fn, "w", encoding="utf-8") as f:
                f.write(f"ПРОВЕРКА ЗНАНИЙ ПО БЕЗОПАСНОСТИ\n{'='*50}\n")
                f.write(f"Ф.И.О.: {self.name.get()}\nДата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write(f"Всего вопросов: {len(self.questions)}\nКоличество ошибок: {self.errors}\nДопустимо ошибок: {self.max_errors-1}\n")
                f.write(f"РЕЗУЛЬТАТ: {'НЕ СДАН' if self.errors >= self.max_errors else 'СДАН'}\n{'='*50}\n\n")
                for i,(q,a) in enumerate(zip(self.questions, self.answers),1):
                    cor = self.check(q,a) if a else False
                    f.write(f"{i}. {q['q']}\nВаш ответ: {a}\nРезультат: {'✓' if cor else '✗'}\n")
                    if q["t"]=="single":
                        f.write(f"Правильно: {q['o'][int(q['a'])]}\n")
                    elif q["t"]=="multi":
                        f.write(f"Правильно: {', '.join(q['o'][int(i)] for i in q['a'])}\n")
                    elif q["t"]=="text":
                        f.write(f"Правильно: {q['a']}\n")
                    elif q["t"]=="order":
                        f.write(f"Правильно: {' -> '.join(q['o'][i] for i in q['a'])}\n")
                    f.write("-"*40+"\n")
            messagebox.showinfo("Сохранено", f"Результаты сохранены в файл:\n{fn}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SafetyTestApp(root)
    root.mainloop()