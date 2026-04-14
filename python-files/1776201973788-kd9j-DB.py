import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import sys
import os

def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу, работает и для разработки, и для PyInstaller """
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CountrySearchApp:
    """
    Приложение для поиска информации о странах по базе данных Excel.
    Поддерживает поиск по названию страны, двухбуквенному, трёхбуквенному,
    цифровому коду или телефонному коду с возможностью точного или частичного совпадения.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Справочник международных телефонных кодов и кодов стран")
        self.root.geometry("1000x650")
        self.root.minsize(900, 500)

        # Путь к файлу Excel (предполагается, что файл лежит рядом со скриптом)
        self.excel_file = resource_path("Международные коды.xlsx")
        self.df = None
        self.load_data()

        # Настройка стилей
        self.setup_styles()
        # Создание интерфейса
        self.create_widgets()

    def load_data(self):
        """Загрузка данных из Excel-файла с обработкой возможных ошибок."""
        try:
            if not os.path.exists(self.excel_file):
                raise FileNotFoundError(f"Файл '{self.excel_file}' не найден в папке с программой.")

            # Читаем лист, пропуская первые 2 строки (пустую и сложный заголовок)
            # header=None означает, что у нас нет заголовков, мы зададим их сами
            self.df = pd.read_excel(
                self.excel_file,
                sheet_name="Алф. порядок",
                skiprows=2,        # пропускаем строки 0 и 1
                header=None
            )
            # Задаём осмысленные имена столбцов
            self.df.columns = ["Наименование", "Код_2букв", "Код_3букв", "Код_цифр", "Тел_код"]

            # Удаляем первую строку данных — она содержит текст "2-букв.", "3-букв." и т.д.
            # Это можно сделать, проверив, что в колонке "Наименование" пусто или NaN
            self.df = self.df[self.df["Наименование"].notna()]
            # Дополнительно удалим строку, где "Наименование" == "2-букв." на всякий случай
            self.df = self.df[~self.df["Наименование"].astype(str).str.contains("2-букв", na=False)]

            # Сбрасываем индекс после удаления строк
            self.df.reset_index(drop=True, inplace=True)

            # Приводим все строковые столбцы к строковому типу для корректного поиска
            for col in ["Наименование", "Код_2букв", "Код_3букв", "Тел_код"]:
                self.df[col] = self.df[col].astype(str)
            # Цифровой код тоже как строка, чтобы можно было искать по подстроке
            self.df["Код_цифр"] = self.df["Код_цифр"].astype(str)

        except Exception as e:
            messagebox.showerror("Ошибка загрузки данных", f"Не удалось загрузить файл:\n{e}")
            self.root.destroy()
            sys.exit(1)

    def setup_styles(self):
        """Настройка визуальных стилей ttk."""
        style = ttk.Style()
        style.theme_use("clam")  # Современная тема
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TCombobox", font=("Segoe UI", 10), padding=4)
        style.configure("TEntry", font=("Segoe UI", 10), padding=4)
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 9, "italic"))

    def create_widgets(self):
        """Создание всех элементов интерфейса."""
        # Заголовок
        header = ttk.Label(self.root, text="Поиск по странам и кодам", style="Header.TLabel")
        header.pack(pady=(15, 5))

        # Фрейм для элементов управления поиском
        search_frame = ttk.LabelFrame(self.root, text="Параметры поиска", padding=10)
        search_frame.pack(fill="x", padx=15, pady=10)

        # Первая строка: поле ввода и кнопка
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill="x", pady=5)

        ttk.Label(input_frame, text="Запрос:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(input_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        self.search_entry.focus_set()

        self.search_btn = ttk.Button(input_frame, text="🔍 Найти", command=self.perform_search)
        self.search_btn.pack(side="left", padx=5)

        self.clear_btn = ttk.Button(input_frame, text="🗑️ Очистить", command=self.clear_search)
        self.clear_btn.pack(side="left", padx=5)

        # Вторая строка: выбор категории и режима поиска
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill="x", pady=8)

        ttk.Label(options_frame, text="Искать в столбце:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.category_var = tk.StringVar(value="Наименование")
        categories = ["Наименование", "Код_2букв", "Код_3букв", "Код_цифр", "Тел_код"]
        self.category_combo = ttk.Combobox(options_frame, textvariable=self.category_var,
                                          values=categories, state="readonly", width=20)
        self.category_combo.grid(row=0, column=1, sticky="w", padx=(0, 20))

        # Чекбокс точного совпадения
        self.exact_var = tk.BooleanVar(value=False)
        self.exact_check = ttk.Checkbutton(options_frame, text="Точное совпадение",
                                          variable=self.exact_var)
        self.exact_check.grid(row=0, column=2, sticky="w", padx=5)

        # Чекбокс учёта регистра (по умолчанию не учитываем)
        self.case_var = tk.BooleanVar(value=False)
        self.case_check = ttk.Checkbutton(options_frame, text="Учитывать регистр",
                                         variable=self.case_var)
        self.case_check.grid(row=0, column=3, sticky="w", padx=5)

        # Фрейм для таблицы результатов
        result_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding=5)
        result_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        # Таблица (Treeview) с прокрутками
        columns = ("№", "Страна", "2-букв.", "3-букв.", "Цифр.", "Тел. код")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)

        # Настройка заголовков и ширины столбцов
        self.tree.heading("№", text="№")
        self.tree.column("№", width=40, anchor="center")
        self.tree.heading("Страна", text="Наименование страны")
        self.tree.column("Страна", width=250)
        self.tree.heading("2-букв.", text="2-букв.")
        self.tree.column("2-букв.", width=70, anchor="center")
        self.tree.heading("3-букв.", text="3-букв.")
        self.tree.column("3-букв.", width=70, anchor="center")
        self.tree.heading("Цифр.", text="Цифр.")
        self.tree.column("Цифр.", width=70, anchor="center")
        self.tree.heading("Тел. код", text="Тел. код")
        self.tree.column("Тел. код", width=120, anchor="center")

        # Полосы прокрутки
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Размещение таблицы и прокруток
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # Статусная строка
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.status_label = ttk.Label(status_frame, text="Готов к поиску. Введите запрос и нажмите Enter или кнопку.",
                                     style="Status.TLabel")
        self.status_label.pack(side="left")
        self.count_label = ttk.Label(status_frame, text="", style="Status.TLabel")
        self.count_label.pack(side="right")

    def perform_search(self):
        """Выполнение поиска по заданным параметрам."""
        query = self.search_var.get().strip()
        if not query:
            self.update_status("Введите поисковый запрос.", "orange")
            return

        category = self.category_var.get()
        exact = self.exact_var.get()
        case_sensitive = self.case_var.get()

        # Копируем DataFrame для поиска
        df_search = self.df.copy()

        # Приводим запрос и данные к нужному регистру, если не учитываем регистр
        if not case_sensitive:
            query_compare = query.lower()
            df_search[category] = df_search[category].str.lower()
        else:
            query_compare = query

        try:
            if exact:
                # Точное совпадение
                mask = df_search[category] == query_compare
            else:
                # Частичное совпадение (содержит подстроку)
                mask = df_search[category].str.contains(query_compare, na=False, regex=False)
        except Exception as e:
            messagebox.showerror("Ошибка поиска", f"Некорректный запрос или данные:\n{e}")
            return

        result_df = self.df[mask].copy()  # Берем оригинальные данные для отображения
        self.display_results(result_df)

        # Обновление статуса
        count = len(result_df)
        if count == 0:
            self.update_status(f"По запросу '{query}' ничего не найдено.", "red")
        else:
            self.update_status(f"Найдено записей: {count}", "green")

    def display_results(self, df):
        """Отображение DataFrame в Treeview."""
        # Очистка предыдущих результатов
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df.empty:
            self.count_label.config(text="")
            return

        # Добавление строк
        for idx, row in enumerate(df.itertuples(), start=1):
            # Обработка возможных NaN значений
            country = str(row.Наименование) if pd.notna(row.Наименование) else ""
            code2 = str(row.Код_2букв) if pd.notna(row.Код_2букв) else ""
            code3 = str(row.Код_3букв) if pd.notna(row.Код_3букв) else ""
            code_digit = str(row.Код_цифр) if pd.notna(row.Код_цифр) else ""
            phone = str(row.Тел_код) if pd.notna(row.Тел_код) else ""

            self.tree.insert("", "end", values=(idx, country, code2, code3, code_digit, phone))

        self.count_label.config(text=f"Всего: {len(df)}")

    def clear_search(self):
        """Очистка поля поиска и результатов."""
        self.search_var.set("")
        self.display_results(pd.DataFrame())
        self.update_status("Готов к поиску. Введите запрос.", "black")
        self.search_entry.focus_set()

    def update_status(self, message, color="black"):
        """Обновление текста и цвета статусной строки."""
        self.status_label.config(text=message, foreground=color)


def main():
    root = tk.Tk()
    app = CountrySearchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
