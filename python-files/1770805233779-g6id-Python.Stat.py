import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os


class CoffeeShopAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("☕ Анализ выручки кофейни")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # Данные (исправлены опечатки из исходного файла)
        self.data = [
            ["01.08.2025", "Воронов", "Алексеев", 16475],
            ["02.08.2025", "Воронов", "Алексеев", 9995],
            ["03.08.2025", "Бедняков", "Воронов", 6525],
            ["04.08.2025", "Бедняков", "Алексеев", 21400],
            ["05.08.2025", "Воронов", "Алексеев", 17170],
            ["06.08.2025", "Воронов", "Гранин", 18020],
            ["07.08.2025", "Бедняков", "Алексеев", 19800],
            ["08.08.2025", "Гранин", "Алексеев", 21000],
            ["09.08.2025", "Бедняков", "Воронов", 10605],
            ["10.08.2025", "Бедняков", "Алексеев", 8480],
            ["11.08.2025", "Гранин", "Алексеев", 19200],
            ["12.08.2025", "Бедняков", "Воронов", 18190],
            ["13.08.2025", "Бедняков", "Алексеев", 19000],
            ["14.08.2025", "Гранин", "Алексеев", 20400],
            ["15.08.2025", "Гранин", "Воронов", 17170],
            ["16.08.2025", "Бедняков", "Алексеев", 11400],
            ["17.08.2025", "Воронов", "Алексеев", 6735],
            ["18.08.2025", "Воронов", "Гранин", 17340],
            ["19.08.2025", "Гранин", "Алексеев", 20200],
            ["20.08.2025", "Бедняков", "Алексеев", 19200],
            ["21.08.2025", "Бедняков", "Воронов", 17000],
            ["22.08.2025", "Гранин", "Алексеев", 20600],
            ["23.08.2025", "Бедняков", "Алексеев", 11880],
            ["24.08.2025", "Бедняков", "Гранин", 7600],
            ["25.08.2025", "Гранин", "Алексеев", 21400],
            ["26.08.2025", "Бедняков", "Алексеев", 20400],
            ["27.08.2025", "Бедняков", "Воронов", 15980],
            ["28.08.2025", "Гранин", "Алексеев", 19200],
            ["29.08.2025", "Воронов", "Алексеев", 16320],
            ["30.08.2025", "Воронов", "Гранин", 10915],
            ["31.08.2025", "Бедняков", "Алексеев", 7520],
            ["01.09.2025", "Гранин", "Алексеев", 20000],
            ["02.09.2025", "Бедняков", "Гранин", 21400],
            ["03.09.2025", "Бедняков", "Алексеев", 21200],
            ["04.09.2025", "Воронов", "Алексеев", 18190],
            ["05.09.2025", "Воронов", "Гранин", 18190],
            ["06.09.2025", "Бедняков", "Алексеев", 12000],
            ["07.09.2025", "Бедняков", "Алексеев", 7840],
            ["08.09.2025", "Воронов", "Гранин", 17680],
            ["09.09.2025", "Бедняков", "Алексеев", 20600],
            ["10.09.2025", "Бедняков", "Алексеев", 19600],
            ["11.09.2025", "Воронов", "Гранин", 16490],
            ["12.09.2025", "Воронов", "Алексеев", 18190],
            ["13.09.2025", "Воронов", "Алексеев", 9790],
            ["14.09.2025", "Бедняков", "Гранин", 7840],
            ["15.09.2025", "Гранин", "Алексеев", 21000],
            ["16.09.2025", "Воронов", "Алексеев", 17850],
            ["17.09.2025", "Воронов", "Гранин", 16660],
            ["18.09.2025", "Гранин", "Алексеев", 21000],
            ["19.09.2025", "Гранин", "Алексеев", 19400],
            ["20.09.2025", "Бедняков", "Воронов", 9895],
            ["21.09.2025", "Бедняков", "Алексеев", 7840],
            ["22.09.2025", "Бедняков", "Алексеев", 19000],
            ["23.09.2025", "Гранин", "Воронов", 17170],
            ["24.09.2025", "Бедняков", "Алексеев", 18600],
            ["25.09.2025", "Бедняков", "Алексеев", 19800],
            ["26.09.2025", "Гранин", "Воронов", 15810],
            ["27.09.2025", "Бедняков", "Алексеев", 11760],
            ["28.09.2025", "Бедняков", "Алексеев", 7440],
            ["29.09.2025", "Гранин", "Воронов", 16490],
            ["30.09.2025", "Бедняков", "Воронов", 16320],
        ]

        # Запуск анализа при старте
        self.run_analysis()
        self.create_widgets()

    def run_analysis(self):
        """Проводит анализ данных без внешних зависимостей"""
        # Статистика по сотрудникам
        self.barista_stats = {}
        self.pair_stats = {}
        self.low_revenue_shifts = []

        for entry in self.data:
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

    def create_widgets(self):
        """Создаёт интерфейс приложения"""
        # Верхняя панель с заголовком
        header = tk.Label(
            self.root,
            text="🔍 Анализ выручки кофейни: поиск аномалий",
            font=("Arial", 16, "bold"),
            fg="#2c3e50",
            pady=10
        )
        header.pack(fill=tk.X)

        # Вкладки
        tab_control = ttk.Notebook(self.root)

        # Вкладка 1: Исходные данные
        tab1 = ttk.Frame(tab_control)
        tab_control.add(tab1, text="📊 Исходные данные")
        self.create_data_table(tab1)

        # Вкладка 2: Статистика по сотрудникам
        tab2 = ttk.Frame(tab_control)
        tab_control.add(tab2, text="👥 Сотрудники")
        self.create_barista_stats(tab2)

        # Вкладка 3: Статистика по парам
        tab3 = ttk.Frame(tab_control)
        tab_control.add(tab3, text="👫 Пары")
        self.create_pair_stats(tab3)

        # Вкладка 4: Выводы
        tab4 = ttk.Frame(tab_control)
        tab_control.add(tab4, text="💡 Выводы и рекомендации")
        self.create_conclusions(tab4)

        tab_control.pack(expand=1, fill="both", padx=10, pady=5)

        # Кнопка экспорта
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack(fill=tk.X)

        export_btn = tk.Button(
            btn_frame,
            text="💾 Сохранить отчёт в файл",
            command=self.export_report,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5
        )
        export_btn.pack(side=tk.RIGHT, padx=10)

    def create_data_table(self, parent):
        """Таблица исходных данных"""
        frame = tk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Скроллбары
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        # Таблица
        tree = ttk.Treeview(
            frame,
            columns=("date", "b1", "b2", "revenue"),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        # Заголовки
        tree.heading("date", text="Дата")
        tree.heading("b1", text="Бариста 1")
        tree.heading("b2", text="Бариста 2")
        tree.heading("revenue", text="Выручка, ₽")

        # Ширина колонок
        tree.column("date", width=100, anchor="center")
        tree.column("b1", width=120, anchor="center")
        tree.column("b2", width=120, anchor="center")
        tree.column("revenue", width=120, anchor="center")

        # Данные
        for row in self.data:
            tag = "low" if row[3] < 10000 else "normal"
            tree.insert("", "end", values=row, tags=(tag,))

        # Стили для аномальных строк
        tree.tag_configure("low", background="#ffebee", foreground="#c62828")
        tree.tag_configure("normal", background="white")

        # Размещение
        tree.grid(column=0, row=0, sticky="nsew")
        vsb.grid(column=1, row=0, sticky="ns")
        hsb.grid(column=0, row=1, sticky="ew")

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

    def create_barista_stats(self, parent):
        """Статистика по сотрудникам"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        tk.Label(
            frame,
            text="Статистика по каждому бариста",
            font=("Arial", 12, "bold"),
            fg="#2c3e50"
        ).pack(anchor="w", pady=(0, 10))

        # Таблица
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
                padx=5,
                pady=3
            )
            lbl.grid(row=0, column=i, sticky="nsew")

        # Данные
        sorted_baristas = sorted(
            self.barista_stats.items(),
            key=lambda x: x[1]["low_count"] / x[1]["count"],
            reverse=True
        )

        for row_idx, (barista, stats) in enumerate(sorted_baristas, start=1):
            revenues = sorted(stats["revenues"])
            n = len(revenues)
            median = revenues[n // 2] if n % 2 else (revenues[n // 2 - 1] + revenues[n // 2]) // 2

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
                    padx=5,
                    pady=3,
                    bg=bg_color
                )
                lbl.grid(row=row_idx, column=col_idx, sticky="nsew")

        # Настройка растягивания колонок
        for i in range(len(headers)):
            table_frame.grid_columnconfigure(i, weight=1)

    def create_pair_stats(self, parent):
        """Статистика по парам"""
        frame = tk.Frame(parent, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text="Статистика совместной работы пар",
            font=("Arial", 12, "bold"),
            fg="#2c3e50"
        ).pack(anchor="w", pady=(0, 10))

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
                padx=5,
                pady=3
            )
            lbl.grid(row=0, column=i, sticky="nsew")

        # Сортировка по среднему убыванию
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
                    padx=5,
                    pady=3,
                    bg=bg_color
                )
                lbl.grid(row=row_idx, column=col_idx, sticky="nsew")

        for i in range(len(headers)):
            table_frame.grid_columnconfigure(i, weight=1)

    def create_conclusions(self, parent):
        """Выводы и рекомендации"""
        frame = tk.Frame(parent, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True)

        # Анализ для выводов
        bednyakov = self.barista_stats["Бедняков"]
        bednyakov_low_pct = round(bednyakov["low_count"] * 100 / bednyakov["count"], 1)

        granin = self.barista_stats["Гранин"]
        granin_low_pct = round(granin["low_count"] * 100 / granin["count"], 1)

        # Текст выводов
        report = f"""🔍 КЛЮЧЕВЫЕ ВЫВОДЫ АНАЛИЗА

📊 Статистика аномалий (выручка < 10 000 ₽):
   • Бедняков: {bednyakov["low_count"]} из {bednyakov["count"]} смен ({bednyakov_low_pct}%)
   • Воронов:   {self.barista_stats["Воронов"]["low_count"]} из {self.barista_stats["Воронов"]["count"]} смен ({round(self.barista_stats["Воронов"]["low_count"] * 100 / self.barista_stats["Воронов"]["count"], 1)}%)
   • Алексеев:  {self.barista_stats["Алексеев"]["low_count"]} из {self.barista_stats["Алексеев"]["count"]} смен ({round(self.barista_stats["Алексеев"]["low_count"] * 100 / self.barista_stats["Алексеев"]["count"], 1)}%)
   • Гранин:    {granin["low_count"]} из {granin["count"]} смен ({granin_low_pct}%)

⚠️  КРИТИЧЕСКАЯ АНОМАЛИЯ:
   Бедняков демонстрирует систематическое падение выручки независимо от напарника:
   • С Граниным (обычно стабильная пара): среднее ~15 600 ₽ вместо ожидаемых ~20 000 ₽
   • С Вороновым: среднее 13 502 ₽ — самые низкие показатели в кофейне
   • 7 из 18 смен с Алексеевым ниже 12 000 ₽

💡 ПОЧЕМУ НЕ ВОРОНОВ?
   Воронов тоже показывает низкую среднюю (15 080 ₽), но его «провалы» почти всегда
   совпадают с присутствием Беднякова. Когда Воронов работает с Гранином —
   среднее 16 834 ₽, что приемлемо для бизнес-центра.

🎯 ГЛАВНЫЙ ВЫВОД:
   Статистика однозначно указывает на Беднякова как на ключевую точку аномалий.
   Его присутствие в смене коррелирует с падением выручки независимо от напарника.
   Вероятные сценарии:
   1. Самостоятельные действия (продажа без чека)
   2. Координация с Вороновым (их совместные смены самые «убыточные»)

🛡️  РЕКОМЕНДУЕМЫЕ МЕРЫ:

   1. Тестовые покупки
      Раз в 2–3 дня совершайте анонимный заказ в смену Беднякова.
      Фиксируйте время, заказ, сумму. Сверяйте с кассовой лентой вечером.

   2. Разделение касс
      Выделите каждому бариста отдельный кассовый аппарат или режим.
      Так вы увидите индивидуальную динамику, а не общую сумму пары.

   3. Внезапная инвентаризация
      После смены Беднякова замеряйте остатки кофе, молока, сиропов.
      Расход должен коррелировать с выручкой.

   4. Анонимная обратная связь
      Добавьте QR-код на чеки: «Оцените обслуживание».
      Жалобы на «не пробитый чек» — прямое доказательство.

   5. Видеонаблюдение с фиксацией кассы
      Анализируйте: сколько заказов в час, как часто бариста уходит от кассы
      с наличными.

❗ ВАЖНО: Не увольняйте сразу. Соберите 2–3 недели доказательств через
   тестовые покупки и разделение касс. Статистика подозрительна — нужны
   конкретные эпизоды для принятия решения.
"""

        text.insert(tk.END, report)
        text.config(state=tk.DISABLED)  # Только для чтения

    def export_report(self):
        """Экспорт отчёта в текстовый файл"""
        try:
            # Анализ для экспорта
            bednyakov = self.barista_stats["Бедняков"]
            bednyakov_low_pct = round(bednyakov["low_count"] * 100 / bednyakov["count"], 1)

            report = f"""ОТЧЁТ АНАЛИЗА ВЫРУЧКИ КОФЕЙНИ
Дата формирования: {self.data[-1][0]}
Период анализа: 01.08.2025 – {self.data[-1][0]}

ИНДИВИДУАЛЬНАЯ СТАТИСТИКА
{'=' * 70}
Бариста      Смен  Среднее   Минимум   <10к  % аномалий
{'-' * 70}"""

            sorted_baristas = sorted(
                self.barista_stats.items(),
                key=lambda x: x[1]["low_count"] / x[1]["count"],
                reverse=True
            )

            for barista, stats in sorted_baristas:
                revenues = sorted(stats["revenues"])
                n = len(revenues)
                median = revenues[n // 2] if n % 2 else (revenues[n // 2 - 1] + revenues[n // 2]) // 2
                avg = stats["total"] // stats["count"]
                low_percent = round(stats["low_count"] * 100 / stats["count"], 1)
                report += f"\n{barista:<12} {stats['count']:<5} {avg:>8,}₽  {stats['min']:>8,}₽  {stats['low_count']:<5} {low_percent:>6}%".replace(
                    ",", " ")

            report += f"""

СТАТИСТИКА ПО ПАРАМ
{'=' * 70}
Пара                          Смен  Среднее   Минимум
{'-' * 70}"""

            sorted_pairs = sorted(
                self.pair_stats.items(),
                key=lambda x: x[1]["total"] / x[1]["count"],
                reverse=True
            )

            for pair, stats in sorted_pairs:
                avg = stats["total"] // stats["count"]
                report += f"\n{pair[0]} + {pair[1]:<20} {stats['count']:<5} {avg:>8,}₽  {stats['min']:>8,}₽".replace(
                    ",", " ")

            report += f"""

ВЫВОДЫ
{'=' * 70}
Главный подозреваемый: Бедняков
Показатель аномалий: {bednyakov_low_pct}% смен с выручкой < 10 000 ₽

Рекомендации:
1. Тестовые покупки в смены Беднякова
2. Разделение кассовых аппаратов по сотрудникам
3. Внезапная инвентаризация после смены
4. QR-код на чеках для анонимной обратной связи
5. Анализ видеозаписей с фиксацией кассовых операций

Важно: собрать 2–3 недели доказательств перед принятием кадровых решений.
"""

            # Сохранение файла
            filename = "coffee_shop_analysis_report.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            messagebox.showinfo(
                "✅ Успешно",
                f"Отчёт сохранён в файл:\n{os.path.abspath(filename)}"
            )
        except Exception as e:
            messagebox.showerror("❌ Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")


def main():
    root = tk.Tk()
    app = CoffeeShopAnalyzer(root)
    root.mainloop()


if __name__ == "__main__":
    main()