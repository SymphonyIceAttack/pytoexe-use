import tkinter as tk
from tkinter import ttk, messagebox
import openpyxl
from openpyxl.utils import get_column_letter

# --- Данные по ГОСТ 21.208 ---
MEASURE_CODES = {
    "температура": "T", "давление": "P", "расход": "F", "уровень": "L",
    "влажность": "M", "концентрация": "Q", "плотность": "D", "вязкость": "V",
    "pH": "H", "окислительно-восстановительный потенциал": "R",
    "электрическая величина": "E", "механическая величина": "G"
}

FUNCTION_CODES = {
    "показывающий": "I", "регистрирующий": "R", "регулирующий": "C",
    "сигнализирующий": "A", "бесшкальный": "S", "интегрирующий": "Q",
    "преобразующий": "T", "дистанционная передача": "T"
}

LOCATION_OPTIONS = ["по_месту", "на_щите"]


def generate_symbol(measure, functions, loop_number):
    """Генерация кода по ГОСТ"""
    if measure not in MEASURE_CODES:
        return None
    base = MEASURE_CODES[measure]

    func_letters = []
    seen = set()
    for f in functions:
        if f in FUNCTION_CODES:
            code = FUNCTION_CODES[f]
            if code not in seen:
                func_letters.append(code)
                seen.add(code)

    func_part = "".join(func_letters) if func_letters else ""
    return f"{base}{func_part}-{loop_number:03d}"


class KIPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор обозначений КИПиА (ГОСТ 21.208)")
        self.root.geometry("900x650")

        self.records = []  # Хранилище данных

        # --- Верхняя панель: Цех и Место установки ---
        top_frame = ttk.LabelFrame(root, text="Общие данные", padding=10)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Цех:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_shop = ttk.Entry(top_frame, width=15)
        self.entry_shop.insert(0, "1")  # Значение по умолчанию
        self.entry_shop.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top_frame, text="Место установки:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.combo_location = ttk.Combobox(top_frame, values=LOCATION_OPTIONS, state="readonly", width=12)
        self.combo_location.set(LOCATION_OPTIONS[0])
        self.combo_location.grid(row=0, column=3, padx=5, pady=5)

        # --- Панель ввода прибора ---
        input_frame = ttk.LabelFrame(root, text="Параметры прибора", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Величина
        ttk.Label(input_frame, text="Величина:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.combo_measure = ttk.Combobox(input_frame, values=list(MEASURE_CODES.keys()), state="readonly", width=20)
        self.combo_measure.grid(row=0, column=1, padx=5, pady=5)

        # Функции (множественный выбор через чекбоксы лучше, но для простоты сделаем комбо с мульти-выбором или список)
        # Здесь реализуем выбор через Listbox с возможностью выбора нескольких строк
        ttk.Label(input_frame, text="Функции:").grid(row=0, column=2, padx=5, pady=5, sticky="ne")
        self.listbox_func = tk.Listbox(input_frame, selectmode="multiple", height=4, width=25)
        for func in FUNCTION_CODES.keys():
            self.listbox_func.insert(tk.END, func)
        self.listbox_func.grid(row=0, column=3, padx=5, pady=5, rowspan=2)

        # Номер контура
        ttk.Label(input_frame, text="Номер контура:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_loop = ttk.Entry(input_frame, width=15)
        self.entry_loop.grid(row=1, column=1, padx=5, pady=5)

        # Примечание
        ttk.Label(input_frame, text="Примечание:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_note = ttk.Entry(input_frame, width=40)
        self.entry_note.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

        # Кнопки действий
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)

        self.btn_add = ttk.Button(btn_frame, text="Добавить прибор", command=self.add_record)
        self.btn_add.pack(side="left", padx=10)

        self.btn_export = ttk.Button(btn_frame, text="Выгрузить в Excel", command=self.export_to_excel)
        self.btn_export.pack(side="left", padx=10)

        self.btn_clear = ttk.Button(btn_frame, text="Очистить список", command=self.clear_list)
        self.btn_clear.pack(side="left", padx=10)

        # --- Таблица результатов ---
        table_frame = ttk.LabelFrame(root, text="Список приборов", padding=5)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("Цех", "Величина", "Функции", "Место", "Контур", "Обозначение", "Примечание")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        # Настройка заголовков
        self.tree.heading("Цех", text="Цех")
        self.tree.heading("Величина", text="Величина")
        self.tree.heading("Функции", text="Функции")
        self.tree.heading("Место", text="Место")
        self.tree.heading("Контур", text="Контур")
        self.tree.heading("Обозначение", text="Обозначение")
        self.tree.heading("Примечание", text="Примечание")

        # Настройка ширины колонок
        self.tree.column("Цех", width=50, anchor="center")
        self.tree.column("Величина", width=100)
        self.tree.column("Функции", width=180)
        self.tree.column("Место", width=80, anchor="center")
        self.tree.column("Контур", width=70, anchor="center")
        self.tree.column("Обозначение", width=100, anchor="center")
        self.tree.column("Примечание", width=150)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def add_record(self):
        shop = self.entry_shop.get().strip()
        measure = self.combo_measure.get()
        location = self.combo_location.get()
        
        try:
            loop_num = int(self.entry_loop.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Номер контура должен быть целым числом!")
            return

        if not shop or not measure:
            messagebox.showwarning("Внимание", "Заполните номер цеха и измеряемую величину!")
            return

        # Получаем выбранные функции
        selected_indices = self.listbox_func.curselection()
        functions = [self.listbox_func.get(i) for i in selected_indices]
        
        if not functions:
            # Если ничего не выбрано, можно добавить дефолтную функцию или предупредить
            # Здесь просто добавим "показывающий", если список пуст, чтобы код был валидным
            functions = ["показывающий"] 

        symbol = generate_symbol(measure, functions, loop_num)
        if not symbol:
            messagebox.showerror("Ошибка", "Не удалось сгенерировать код. Проверьте данные.")
            return

        note = self.entry_note.get().strip()

        record = [shop, measure, ", ".join(functions), location, loop_num, symbol, note]
        self.records.append(record)

        # Добавляем в таблицу
        self.tree.insert("", "end", values=record)
        
        # Очистка полей ввода (кроме цеха)
        self.entry_loop.delete(0, tk.END)
        self.entry_note.delete(0, tk.END)
        self.combo_measure.set("")
        # Сброс выделения в списке функций
        for i in range(self.listbox_func.size()):
            self.listbox_func.selection_clear(i)
        
        messagebox.showinfo("Успех", f"Прибор {symbol} добавлен!")

    def export_to_excel(self):
        if not self.records:
            messagebox.showwarning("Внимание", "Список приборов пуст. Нечего выгружать.")
            return

        filename = f"kip_equipment_shop_{self.entry_shop.get()}.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "КИПиА"

        headers = ["Цех", "Величина", "Функции", "Место установки", "Номер контура", "Обозначение", "Примечание"]
        ws.append(headers)

        for row in self.records:
            ws.append(row)

        # Автоширина
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column].width = adjusted_width

        try:
            wb.save(filename)
            messagebox.showinfo("Готово", f"Файл успешно сохранён: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка записи", str(e))

    def clear_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.records = []
        messagebox.showinfo("Очистка", "Список очищен.")


if __name__ == "__main__":
    root = tk.Tk()
    app = KIPApp(root)
    root.mainloop()
