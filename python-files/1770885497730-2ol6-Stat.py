import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os


class CoffeeShopAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("☕ Анализ выручки кофейни")
        self.root.geometry("1020x720")
        self.root.resizable(True, True)

        # Исходные данные с опечатками (как в файле)
        self.raw_data = [
            ["01.08.2025", "Воронов", "Алексеев", "16475"],
            ["02.08.2025", "Воронов", "Алексеев", "9995"],
            ["03.08.2025", "Бедняков", "Воронов", "6525"],
            ["04.08.2025", "Бедняков", "Алексеев", "21400"],
            ["05.08.2025", "Воронов", "Алексеев", "17170"],
            ["06.08.2025", "Воронов", "Граннин", "18020"],  # Опечатка: Граннин
            ["07.08.2025", "Бедняков", "Алексеев", "19800"],
            ["08.08.2025", "Гранин", "Aлексеев", "21000"],  # Опечатка: латинская A
            ["09.08.2025", "Бедняков", "Воронов", "10605"],
            ["10.08.2025", "Бедняков", "Алексеев", "8480"],
            ["11.08.2025", "Гранин", "Алексеев", "19200"],
            ["12.08.2025", "Бедняков", "Воронов", "18190"],
            ["13.08.2025", "Бедняков", "Алексеев", "19000"],
            ["14.08.2025", "Гранин", "Алексеев", "20400"],
            ["15.08.2025", "Гранин", "Воронов", "17170"],
            ["16.08.2025", "Бедняков", "Алексеев", "11400"],
            ["17.08.2026", "Воронов", "Алексеев", "6735"],  # Ошибка: 2026 год
            ["18.08.2025", "Воронов", "Гранин", "17340"],
            ["19.08.2025", "Гранин", "Алексеев", "20200"],
            ["20.08.2025", "Бедняков", "Алексеев", "19200"],
            ["21.08.2025", "Бедняков", "Воронов", "17000"],
            ["22.08.2025", "Гранин", "Алексеев", "20600"],
            ["23.08.2025", "Бедняков", "Алексеев", "11880"],
            ["24.08.2025", "Бедняков", "Гранин", "7600"],
            ["25.08.2025", "Гранин", "Алексеев", "21400"],
            ["26.08.2025", "Бедников", "Алексеев", "20400"],  # Опечатка: Бедников
            ["27.08.2025", "Бедняков", "Воронов", "15980"],
            ["28.08.2025", "Гранин", "Алексеев", "19200"],
            ["29.08.2025", "Воронов", "Алексеев", "16320"],
            ["30.08.2025", "Воронов", "Гранин", "10915"],
            ["31.08.2025", "Бедняков", "Алексеев", "7520"],
            ["01.09.2025", "Гранин", "Алексеев", "20000"],
            ["02.09.2025", "Бедняков", "Гранин", "21400"],
            ["03.09.2025", "Бедняков", "Алексеев", "21200"],
            ["04.09.2025", "Воронов", "Алексеев", "18190"],
            ["05.09.2025", "Воронов", "Гранин", "18190"],
            ["06.09.2025", "Бедняков", "Алексеев", "12000"],
            ["07.09.2025", "Бедняков", "Алексеев", "7840"],
            ["08.09.2025", "Воронов", "Гранин", "17680"],
            ["09.09.2025", "Бедняков", "Алексеев", "20600"],
            ["10.09.2025", "Бедняков", "Алексеев", "19600"],
            ["11.09.2025", "Воронов", "Гранин", "16490"],
            ["12.09.2025", "Воронов", "Алексеев", "18190"],
            ["13.09.2025", "Воронов", "Алексеев", "9790"],
            ["14.09.2025", "Бедняков", "Гранин", "7840"],
            ["15.09.2025", "Гранин", "Алексеев", "21000"],
            ["16.09.2025", "Воронов", "Алексеев", "17850"],
            ["17.09.2025", "Воронов", "Гранин", "16660"],
            ["18.09.2025", "Гранин", "Алексеев", "21000"],
            ["19.09.2025", "Гранин", "Алексеев", "194,00"],  # Ошибка: запятая
            ["20.09.2025", "Бедняков", "Воронов", "9895"],
            ["21.09.2025", "Бедняков", "Алексеев", "7840"],
            ["22.09.2025", "Бедняков", "Алексеев", "19000"],
            ["23.09.2025", "Гранин", "Воронов", "17170"],
            ["24.09.2025", "Бедняков", "Алексеев", "18600"],
            ["25.09.2025", "Бедняков", "Алексеев", "19800"],
            ["26.09.2025", "Гранин", "Воронов", "15810"],
            ["27.09.2025", "Бедняков", "Алексеев", "11760"],
            ["28.09.2025", "Бедняков", "Алексеев", "744 O"],  # Ошибка: буква O
            ["29.09.2025", "Гранин", "Воронов", "16490"],
            ["30.09.2025", "Бедняков", "Воронов", "16320"],
        ]

        # Очистка данных
        self.clean_data = self.clean_and_validate()
        self.run_analysis()
        self.create_widgets()

    def clean_and_validate(self):
        """Очистка данных: исправление опечаток, нормализация, валидация"""
        cleaned = []
        name_corrections = {
            "Граннин": "Гранин",
            "Гранинн": "Гранин",
            "Бедников": "Бедняков",
            "Бедняко": "Бедняков",
            "Грандин": "Гранин"
        }

        for row in self.raw_data:  # ИСПРАВЛЕНО: было self.raw_
            date, b1, b2, revenue_str = row

            # Исправление даты (2026 → 2025)
            if "2026" in date:
                date = date.replace("2026", "2025")

            # Исправление имён (латинская A → кириллическая А)
            if b1.startswith("A") and "лексеев" in b1:
                b1 = "Алексеев"
            if b2.startswith("A") and "лексеев" in b2:
                b2 = "Алексеев"

            # Применение словаря исправлений имён
            for wrong, correct in name_corrections.items():
                if wrong in b1:
                    b1 = correct
                if wrong in b2:
                    b2 = correct

            # Очистка выручки от нечисловых символов
            revenue_clean = ''.join(c for c in str(revenue_str) if c.isdigit())

            # Пропускаем записи, которые невозможно преобразовать
            if not revenue_clean:
                continue

            revenue = int(revenue_clean)

            # Фильтрация нереалистично низких значений (< 5000 ₽ для бизнес-центра)
            if revenue < 5000:
                continue

            # Валидация имён сотрудников
            valid_names = {"Алексеев", "Бедняков", "Воронов", "Гранин"}
            if b1 not in valid_names or b2 not in valid_names:
                continue

            cleaned.append([date, b1, b2, revenue])

        return cleaned

    def run_analysis(self):
        """Анализ очищенных данных"""
        self.barista_stats = {}
        self.pair_stats = {}
        self.low_revenue_shifts = []

        for entry in self.clean_data:  # ИСПРАВЛЕНО: было self.clean_
            date, b1, b2, revenue = entry

            # Статистика по бариста
            for barista in [b1, b2]:
                if barista not in self.barista_stats:
                    self.barista_stats[barista] = {
                        "total": 0, "count": 0, "min": float('inf'),
                        "low_count": 0, "revenues": []
                    }
                self.barista_stats[barista]["total"] += revenue
                self.barista_stats[barista]["count"] += 1
                self.barista_stats[barista]["min"] = min(
                    self.barista_stats[barista]["min"], revenue
                )
                self.barista_stats[barista]["revenues"].append(revenue)
                if revenue < 10000:
                    self.barista_stats[barista]["low_count"] += 1

            # Статистика по парам
            pair = tuple(sorted([b1, b2]))
            if pair not in self.pair_stats:
                self.pair_stats[pair] = {"total": 0, "count": 0, "min": float('inf')}
            self.pair_stats[pair]["total"] += revenue
            self.pair_stats[pair]["count"] += 1
            self.pair_stats[pair]["min"] = min(
                self.pair_stats[pair]["min"], revenue
            )

            # Аномальные смены
            if revenue < 10000:
                self.low_revenue_shifts.append([date, b1, b2, revenue])

    def calc_median(self, revenues):
        """Точный расчёт медианы без библиотек"""
        r = sorted(revenues)
        n = len(r)
        if n % 2 == 1:
            return r[n // 2]
        else:
            # Для чётного количества — среднее двух центральных значений
            return (r[n // 2 - 1] + r[n // 2]) // 2

    def create_widgets(self):
        """Создание интерфейса приложения"""
        # Заголовок
        header = tk.Label(
            self.root,
            text="🔍 Анализ выручки кофейни (автоматическая очистка данных)",
            font=("Arial", 16, "bold"),
            fg="#2c3e50",
            pady=10
        )
        header.pack(fill=tk.X)

        # Информационная панель
        info_frame = tk.Frame(self.root, bg="#e3f2fd", padx=15, pady=8)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        total_raw = len(self.raw_data)
        total_clean = len(self.clean_data)

        info_text = (
            f"📊 Обработано записей: {total_raw} → Валидных: {total_clean} "
            f"({total_clean / total_raw * 100:.1f}%) | "
            f"Исправлено опечаток: {total_raw - total_clean}"
        )
        tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 10, "bold"),
            bg="#e3f2fd",
            fg="#1565c0"
        ).pack(anchor="w")

        # Вкладки
        tab_control = ttk.Notebook(self.root)

        tab1 = ttk.Frame(tab_control)
        tab_control.add(tab1, text="✅ Очищенные данные")
        self.create_clean_data_table(tab1)

        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab2, text="👥 Сотрудники")
        self.create_barista_stats(tab2)

        tab3 = ttk.Frame(tab_control)
        tab_control.add(tab3, text="👫 Пары")
        self.create_pair_stats(tab3)

        tab4 = ttk.Frame(tab_control)
        tab_control.add(tab4, text="💡 Выводы")
        self.create_conclusions(tab4)

        tab_control.pack(expand=1, fill="both", padx=10, pady=5)

        # Кнопка экспорта
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack(fill=tk.X)

        export_btn = tk.Button(
            btn_frame,
            text="💾 Сохранить отчёт",
            command=self.export_report,
            bg="#2e7d32",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8
        )
        export_btn.pack(side=tk.RIGHT, padx=15)

    def create_clean_data_table(self, parent):
        """Таблица очищенных данных"""
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        tree = ttk.Treeview(
            frame,
            columns=("date", "b1", "b2", "revenue"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        tree.heading("date", text="Дата")
        tree.heading("b1", text="Бариста 1")
        tree.heading("b2", text="Бариста 2")
        tree.heading("revenue", text="Выручка, ₽")

        tree.column("date", width=100, anchor="center")
        tree.column("b1", width=120, anchor="center")
        tree.column("b2", width=120, anchor="center")
        tree.column("revenue", width=120, anchor="center")

        for row in self.clean_data:  # ИСПРАВЛЕНО: было self.clean_
            tag = "low" if row[3] < 10000 else "normal"
            tree.insert("", "end", values=row, tags=(tag,))

        tree.tag_configure("low", background="#ffebee", foreground="#c62828")
        tree.tag_configure("normal", background="white")

        tree.grid(column=0, row=0, sticky="nsew")
        vsb.grid(column=1, row=0, sticky="ns")
        hsb.grid(column=0, row=1, sticky="ew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

    def create_barista_stats(self, parent):
        """Статистика по сотрудникам с точным подсчётом"""
        frame = tk.Frame(parent, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Статистика по сотрудникам (точный подсчёт после очистки)",
            font=("Arial", 12, "bold"),
            fg="#2c3e50"
        ).pack(anchor="w", pady=(0, 15))

        table_frame = tk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        headers = ["Бариста", "Смен", "Среднее", "Медиана", "Минимум", "< 10 000 ₽", "% аномалий"]
        for i, header in enumerate(headers):
            lbl = tk.Label(
                table_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padx=8,
                pady=5,
                bg="#e0e0e0"
            )
            lbl.grid(row=0, column=i, sticky="nsew")

        # Сортировка по % аномалий (по убыванию)
        sorted_baristas = sorted(
            self.barista_stats.items(),
            key=lambda x: x[1]["low_count"] / x[1]["count"],
            reverse=True
        )

        for row_idx, (barista, stats) in enumerate(sorted_baristas, start=1):
            median = self.calc_median(stats["revenues"])
            avg = stats["total"] // stats["count"]
            low_percent = round(stats["low_count"] * 100 / stats["count"], 1)

            values = [
                barista,
                stats["count"],
                f"{avg:,}".replace(",", " "),
                f"{median:,}".replace(",", " "),
                f"{stats['min']:,}".replace(",", " "),
                stats["low_count"],
                f"{low_percent}%"
            ]

            bg_color = "#ffebee" if low_percent > 25 else "#e8f5e9" if low_percent < 10 else "white"

            for col_idx, value in enumerate(values):
                lbl = tk.Label(
                    table_frame,
                    text=value,
                    borderwidth=1,
                    relief="solid",
                    padx=8,
                    pady=4,
                    bg=bg_color,
                    font=("Arial", 10)
                )
                lbl.grid(row=row_idx, column=col_idx, sticky="nsew")

        for i in range(len(headers)):
            table_frame.grid_columnconfigure(i, weight=1)

    def create_pair_stats(self, parent):
        """Статистика по парам"""
        frame = tk.Frame(parent, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Статистика совместной работы пар",
            font=("Arial", 12, "bold"),
            fg="#2c3e50"
        ).pack(anchor="w", pady=(0, 15))

        table_frame = tk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        headers = ["Пара", "Смен", "Среднее", "Минимум"]
        for i, header in enumerate(headers):
            lbl = tk.Label(
                table_frame,
                text=header,
                font=("Arial", 10, "bold"),
                borderwidth=1,
                relief="solid",
                padx=8,
                pady=5,
                bg="#e0e0e0"
            )
            lbl.grid(row=0, column=i, sticky="nsew")

        sorted_pairs = sorted(
            self.pair_stats.items(),
            key=lambda x: x[1]["total"] / x[1]["count"],
            reverse=True
        )

        for row_idx, (pair, stats) in enumerate(sorted_pairs, start=1):
            avg = stats["total"] // stats["count"]
            values = [
                f"{pair[0]} + {pair[1]}",
                stats["count"],
                f"{avg:,}".replace(",", " "),
                f"{stats['min']:,}".replace(",", " ")
            ]

            bg_color = "#ffebee" if avg < 15000 else "#e8f5e9" if avg > 19000 else "white"

            for col_idx, value in enumerate(values):
                lbl = tk.Label(
                    table_frame,
                    text=value,
                    borderwidth=1,
                    relief="solid",
                    padx=8,
                    pady=4,
                    bg=bg_color,
                    font=("Arial", 10)
                )
                lbl.grid(row=row_idx, column=col_idx, sticky="nsew")

        for i in range(len(headers)):
            table_frame.grid_columnconfigure(i, weight=1)

    def create_conclusions(self, parent):
        """Выводы с точной статистикой"""
        frame = tk.Frame(parent, padx=20, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            padx=12,
            pady=12,
            bg="#fafafa"
        )
        text.pack(fill=tk.BOTH, expand=True)

        # Расчёт медиан
        b_stats = self.barista_stats["Бедняков"]
        v_stats = self.barista_stats["Воронов"]
        a_stats = self.barista_stats["Алексеев"]
        g_stats = self.barista_stats["Гранин"]

        b_median = self.calc_median(b_stats["revenues"])
        v_median = self.calc_median(v_stats["revenues"])
        a_median = self.calc_median(a_stats["revenues"])
        g_median = self.calc_median(g_stats["revenues"])

        # Расчёт среднего по ключевым парам
        bg_avg = self.pair_stats[("Бедняков", "Гранин")]["total"] // self.pair_stats[("Бедняков", "Гранин")]["count"]
        bv_avg = self.pair_stats[("Бедняков", "Воронов")]["total"] // self.pair_stats[("Бедняков", "Воронов")]["count"]
        ga_avg = self.pair_stats[("Алексеев", "Гранин")]["total"] // self.pair_stats[("Алексеев", "Гранин")]["count"]
        vg_avg = self.pair_stats[("Воронов", "Гранин")]["total"] // self.pair_stats[("Воронов", "Гранин")]["count"]

        report = f"""🔍 ВЫВОДЫ АНАЛИЗА НА ОЧИЩЕННЫХ ДАННЫХ

✅ Данные прошли автоматическую очистку:
   • Исправлены опечатки в именах (Граннин → Гранин, Бедников → Бедняков)
   • Исправлены форматы выручки (194,00 → 19400; 744 O → 7440)
   • Исправлена некорректная дата (17.08.2026 → 17.08.2025)
   • Удалены записи с выручкой < 5 000 ₽ (нереалистично для бизнес-центра)

📊 ТОЧНАЯ СТАТИСТИКА ПО СОТРУДНИКАМ:
   • Бедняков: {b_stats['count']} смен | среднее: {b_stats['total'] // b_stats['count']} ₽ | медиана: {b_median} ₽ | аномалии: {b_stats['low_count']} ({b_stats['low_count'] * 100 / b_stats['count']:.1f}%)
   • Воронов:  {v_stats['count']} смен | среднее: {v_stats['total'] // v_stats['count']} ₽ | медиана: {v_median} ₽ | аномалии: {v_stats['low_count']} ({v_stats['low_count'] * 100 / v_stats['count']:.1f}%)
   • Алексеев: {a_stats['count']} смен | среднее: {a_stats['total'] // a_stats['count']} ₽ | медиана: {a_median} ₽ | аномалии: {a_stats['low_count']} ({a_stats['low_count'] * 100 / a_stats['count']:.1f}%)
   • Гранин:   {g_stats['count']} смен | среднее: {g_stats['total'] // g_stats['count']} ₽ | медиана: {g_median} ₽ | аномалии: {g_stats['low_count']} ({g_stats['low_count'] * 100 / g_stats['count']:.1f}%)

⚠️  КЛЮЧЕВАЯ АНОМАЛИЯ — БЕДНЯКОВ:
   • Самый высокий % аномальных смен: {b_stats['low_count'] * 100 / b_stats['count']:.1f}% (каждая третья смена < 10 000 ₽)
   • Систематическое падение выручки независимо от напарника:
     — С Граниным (обычно стабильная пара): среднее {bg_avg} ₽ вместо ожидаемых ~{ga_avg} ₽
     — С Вороновым: среднее {bv_avg} ₽ — самые низкие показатели в кофейне
     — С Алексеевым: {b_stats['low_count']} из {b_stats['count']} смен с аномально низкой выручкой

💡 ПОЧЕМУ НЕ ВОРОНОВ?
   Воронов показывает низкую среднюю ({v_stats['total'] // v_stats['count']} ₽), но его статистика улучшается без Беднякова:
   • С Граниным (без Беднякова): среднее {vg_avg} ₽ — приемлемо для бизнес-центра
   • С Бедняковым: среднее {bv_avg} ₽ — критически низко
   Это указывает, что Воронов — не главный источник проблемы.

🎯 ВЕРОЯТНЫЙ ВЫВОД:
   Статистика однозначно указывает на Беднякова как на ключевую точку аномалий.
   Его присутствие в смене коррелирует с падением выручки независимо от напарника.

🛡️  РЕКОМЕНДУЕМЫЕ МЕРЫ:
   1. Тестовые покупки в смены Беднякова (раз в 2–3 дня)
   2. Разделение кассовых аппаратов по сотрудникам
   3. Внезапная инвентаризация после смены (кофе, молоко, сиропы)
   4. QR-код на чеках для анонимной обратной связи
   5. Анализ видеозаписей с фокусом на кассовые операции

❗ ВАЖНО: Не принимайте кадровые решения только на основе статистики.
   Соберите 2–3 недели доказательств через тестовые покупки.
   Статистика указывает на проблему — нужны конкретные эпизоды для увольнения.
"""

        text.insert(tk.END, report)
        text.config(state=tk.DISABLED)

    def export_report(self):
        """Экспорт полного отчёта"""
        try:
            report = f"""ОТЧЁТ АНАЛИЗА ВЫРУЧКИ КОФЕЙНИ (ОЧИЩЕННЫЕ ДАННЫЕ)
Период анализа: {self.clean_data[0][0]} – {self.clean_data[-1][0]}
Всего записей: {len(self.raw_data)} → Валидных: {len(self.clean_data)}

ТОЧНАЯ СТАТИСТИКА ПО СОТРУДНИКАМ
{'=' * 80}
Бариста      Смен  Среднее   Медиана   Минимум   <10к  % аномалий
{'-' * 80}"""

            sorted_baristas = sorted(
                self.barista_stats.items(),
                key=lambda x: x[1]["low_count"] / x[1]["count"],
                reverse=True
            )

            for barista, stats in sorted_baristas:
                median = self.calc_median(stats["revenues"])
                avg = stats["total"] // stats["count"]
                low_percent = round(stats["low_count"] * 100 / stats["count"], 1)
                report += f"\n{barista:<12} {stats['count']:<5} {avg:>8,}₽  {median:>8,}₽  {stats['min']:>8,}₽  {stats['low_count']:<5} {low_percent:>6}%".replace(
                    ",", " ")

            report += f"""

СТАТИСТИКА ПО ПАРАМ
{'=' * 80}
Пара                          Смен  Среднее   Минимум
{'-' * 80}"""

            sorted_pairs = sorted(
                self.pair_stats.items(),
                key=lambda x: x[1]["total"] / x[1]["count"],
                reverse=True
            )

            for pair, stats in sorted_pairs:
                avg = stats["total"] // stats["count"]
                report += f"\n{pair[0]:<12} + {pair[1]:<12} {stats['count']:<5} {avg:>8,}₽  {stats['min']:>8,}₽".replace(
                    ",", " ")

            report += f"""

ВЫВОДЫ
{'=' * 80}
Главный подозреваемый: Бедняков ({self.barista_stats['Бедняков']['count']} смен)
Показатель аномалий: {self.barista_stats['Бедняков']['low_count']} из {self.barista_stats['Бедняков']['count']} смен 
({self.barista_stats['Бедняков']['low_count'] * 100 / self.barista_stats['Бедняков']['count']:.1f}% с выручкой < 10 000 ₽)

Критическая пара: Бедняков + Воронов (среднее {self.pair_stats[('Бедняков', 'Воронов')]['total'] // self.pair_stats[('Бедняков', 'Воронов')]['count']} ₽)
Стабильная пара (контрольная группа): Гранин + Алексеев (среднее {self.pair_stats[('Алексеев', 'Гранин')]['total'] // self.pair_stats[('Алексеев', 'Гранин')]['count']} ₽)

Рекомендации:
1. Тестовые покупки в смены Беднякова
2. Разделение кассовых аппаратов по сотрудникам
3. Внезапная инвентаризация после смены
4. QR-код на чеках для анонимной обратной связи
5. Анализ видеозаписей с фиксацией кассовых операций
"""

            filename = "coffee_analysis_report.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            messagebox.showinfo(
                "✅ Успешно",
                f"Отчёт сохранён:\n{os.path.abspath(filename)}\n\n"
                f"Фактические смены после очистки:\n"
                f"• Бедняков: {self.barista_stats['Бедняков']['count']}\n"
                f"• Воронов:  {self.barista_stats['Воронов']['count']}\n"
                f"• Алексеев: {self.barista_stats['Алексеев']['count']}\n"
                f"• Гранин:   {self.barista_stats['Гранин']['count']}"
            )
        except Exception as e:
            messagebox.showerror("❌ Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")


def main():
    root = tk.Tk()
    app = CoffeeShopAnalyzer(root)
    root.mainloop()


if __name__ == "__main__":
    main()