
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os

class ExcelSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск в Excel таблицах")
        self.root.geometry("950x650")
        self.root.resizable(True, True)

        # Переменные
        self.file_path = tk.StringVar()
        self.sheet_names = []
        self.selected_sheet = tk.StringVar()
        self.search_text = tk.StringVar()
        self.case_sensitive = tk.BooleanVar(value=False)
        self.exact_match = tk.BooleanVar(value=False)
        self.all_sheets = None   # словарь {имя_листа: DataFrame}
        self.results = []        # список найденных кортежей

        self.create_widgets()

    def create_widgets(self):
        # --- Рамка выбора файла ---
        file_frame = ttk.LabelFrame(self.root, text="1. Выберите Excel файл", padding=5)
        file_frame.pack(fill="x", padx=10, pady=5)

        ttk.Entry(file_frame, textvariable=self.file_path, width=60).pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(file_frame, text="Обзор...", command=self.select_file).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Загрузить", command=self.load_file).pack(side="left", padx=5)

        # --- Рамка выбора листа ---
        sheet_frame = ttk.LabelFrame(self.root, text="2. Выберите лист (или оставьте 'Все листы')", padding=5)
        sheet_frame.pack(fill="x", padx=10, pady=5)

        self.sheet_combo = ttk.Combobox(sheet_frame, textvariable=self.selected_sheet, state="readonly", width=50)
        self.sheet_combo.pack(side="left", padx=5, fill="x", expand=True)

        # --- Рамка поискового запроса ---
        search_frame = ttk.LabelFrame(self.root, text="3. Поисковый запрос и параметры", padding=5)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Слово / словосочетание:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(search_frame, textvariable=self.search_text, width=50).grid(row=0, column=1, sticky="we", padx=5, pady=5)

        ttk.Checkbutton(search_frame, text="Учитывать регистр", variable=self.case_sensitive).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Checkbutton(search_frame, text="Точное совпадение (целиком)", variable=self.exact_match).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        ttk.Button(search_frame, text="🔍 Найти", command=self.start_search).grid(row=2, column=0, columnspan=2, pady=10)

        # --- Рамка результатов ---
        results_frame = ttk.LabelFrame(self.root, text="Результаты поиска", padding=5)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Лист", "Строка", "Столбец", "Значение")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180)

        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        # --- Кнопки управления ---
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(control_frame, text="Очистить результаты", command=self.clear_results).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Сохранить в CSV", command=self.save_to_csv).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Сохранить в Excel", command=self.save_to_excel).pack(side="left", padx=5)

        # --- Статусная строка ---
        self.status_var = tk.StringVar()
        self.status_var.set("Готов. Выберите файл и нажмите 'Загрузить'.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=10, pady=(0,5))

    # ---------- Работа с файлом ----------
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.load_file()

    def load_file(self):
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Ошибка", "Файл не существует")
            return

        self.status_var.set("Загрузка файла...")
        self.root.update()

        try:
            ext = os.path.splitext(path)[1].lower()
            engine = 'xlrd' if ext == '.xls' else 'openpyxl'

            # Получаем имена листов
            excel_file = pd.ExcelFile(path, engine=engine)
            self.sheet_names = excel_file.sheet_names
            sheet_list = ["Все листы"] + self.sheet_names
            self.sheet_combo['values'] = sheet_list
            self.selected_sheet.set("Все листы")

            # Загружаем все листы
            self.all_sheets = pd.read_excel(path, sheet_name=None, engine=engine)

            self.status_var.set(f"Файл загружен. Листы: {', '.join(self.sheet_names)}")
            self.clear_results()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
            self.status_var.set("Ошибка загрузки")
            self.all_sheets = None

    # ---------- Поиск ----------
    def start_search(self):
        if self.all_sheets is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите Excel файл")
            return

        search_term = self.search_text.get().strip()
        if not search_term:
            messagebox.showwarning("Предупреждение", "Введите слово или словосочетание для поиска")
            return

        self.clear_results()

        selected = self.selected_sheet.get()
        if selected == "Все листы":
            sheets_to_search = self.sheet_names
        else:
            sheets_to_search = [selected]

        self.status_var.set("Поиск...")
        self.root.config(cursor="watch")
        self.root.update()

        try:
            results = []
            for sheet in sheets_to_search:
                df = self.all_sheets[sheet]
                self.search_in_dataframe(df, sheet, search_term, results)
            self.display_results(results)
            self.status_var.set(f"Поиск завершён. Найдено {len(results)} совпадений.")
            if len(results) == 0:
                messagebox.showinfo("Результаты", "Ничего не найдено.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при поиске:\n{str(e)}")
        finally:
            self.root.config(cursor="")

    def search_in_dataframe(self, df, sheet_name, search_term, results):
        """Поиск в DataFrame по всем ячейкам"""
        # Заменяем NaN на пустую строку и приводим к строке
        df_str = df.astype(str).fillna('')
        case = self.case_sensitive.get()
        exact = self.exact_match.get()

        term = search_term if case else search_term.lower()

        for row_idx in range(len(df_str)):
            row = df_str.iloc[row_idx]
            for col_idx, col_name in enumerate(df.columns):
                cell_value = row.iloc[col_idx]
                if cell_value == '':
                    continue

                if not case:
                    cell_lower = cell_value.lower()
                    if exact:
                        match = (cell_lower == term)
                    else:
                        match = (term in cell_lower)
                else:
                    if exact:
                        match = (cell_value == term)
                    else:
                        match = (term in cell_value)

                if match:
                    excel_row = row_idx + 1  # Excel строки с 1
                    results.append((sheet_name, excel_row, col_name, cell_value))

    def display_results(self, results):
        self.results = results
        for res in results:
            self.tree.insert("", "end", values=res)

    def clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []

    # ---------- Сохранение ----------
    def save_to_csv(self):
        if not self.results:
            messagebox.showinfo("Информация", "Нет результатов для сохранения")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            df = pd.DataFrame(self.results, columns=["Лист", "Строка", "Столбец", "Значение"])
            try:
                df.to_csv(file_path, index=False, encoding="utf-8-sig")
                messagebox.showinfo("Успех", f"Результаты сохранены в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def save_to_excel(self):
        if not self.results:
            messagebox.showinfo("Информация", "Нет результатов для сохранения")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            df = pd.DataFrame(self.results, columns=["Лист", "Строка", "Столбец", "Значение"])
            try:
                df.to_excel(file_path, index=False, engine="openpyxl")
                messagebox.showinfo("Успех", f"Результаты сохранены в {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelSearchApp(root)
    root.mainloop()
