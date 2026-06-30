import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import sys
from datetime import datetime

class SpreadsheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Электронная таблица")
        self.root.geometry("1200x700")

        # Определение пути для сохранения данных (рядом с exe/py)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.base_dir, 'spreadsheet_data.json')

        self.rows = 10
        self.cols = 30
        self.data = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        self.col_names = [f"Столбец {i+1}" for i in range(self.cols)]
        
        # Состояния фильтров
        self.filter_csm = tk.BooleanVar(value=False)
        self.filter_overdue = tk.BooleanVar(value=False)
        self.search_text = tk.StringVar()
        self.search_text.trace("w", lambda name, index, mode: self.apply_filters())

        self.load_data()
        self.setup_ui()
        self.apply_filters()

    def setup_ui(self):
        # --- Панель инструментов ---
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED, padx=5, pady=5)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(toolbar, text="➕ Добавить строку", command=self.add_row).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="🗑️ Удалить строку", command=self.delete_row).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="💾 Сохранить", command=self.save_data).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        tk.Label(toolbar, text="🔍 Поиск:").pack(side=tk.LEFT, padx=2)
        tk.Entry(toolbar, textvariable=self.search_text, width=20).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        tk.Checkbutton(toolbar, text="📋 ЦСМ", variable=self.filter_csm, command=self.apply_filters, indicatoron=0, selectcolor="#cce5ff").pack(side=tk.LEFT, padx=2)
        tk.Checkbutton(toolbar, text="⏳ Просрочка", variable=self.filter_overdue, command=self.apply_filters, indicatoron=0, selectcolor="#ffcdd2").pack(side=tk.LEFT, padx=2)
        
        tk.Label(toolbar, text="Ctrl+C / Ctrl+V — копировать/вставить", fg="gray").pack(side=tk.RIGHT, padx=10)

        # --- Таблица ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Скроллбары
        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

        columns = [str(i) for i in range(self.cols)]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, selectmode="extended")
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        for i in range(self.cols):
            self.tree.heading(str(i), text=self.col_names[i])
            self.tree.column(str(i), width=80, minwidth=50, stretch=False)

        # Теги для цветов
        self.tree.tag_configure("csm", background="#e3f2fd")       # Голубой
        self.tree.tag_configure("returned", background="#fff9c4")  # Желтый
        self.tree.tag_configure("res", background="#e8f5e9")       # Зеленый
        self.tree.tag_configure("overdue", background="#ffebee")   # Красный

        # Бинды событий
        self.tree.bind("<Double-1>", self.on_double_click)
        self.root.bind("<Control-c>", self.copy_to_clipboard)
        self.root.bind("<Control-v>", self.paste_from_clipboard)

        # --- Статус бар ---
        self.status = tk.Label(self.root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Логика Данных ---
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    self.data = saved_data.get("data", self.data)
                    self.col_names = saved_data.get("col_names", self.col_names)
                    self.rows = len(self.data)
                    self.cols = len(self.col_names)
            except Exception as e:
                print(f"Ошибка загрузки: {e}")

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({"data": self.data, "col_names": self.col_names}, f, ensure_ascii=False, indent=2)
            self.status.config(text=f"Данные сохранены в {self.data_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    # --- Фильтры и Рендер ---
    def is_overdue(self, date_str):
        if not date_str:
            return False
        try:
            day, month, year = map(int, date_str.split('.'))
            d = datetime(year, month, day)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return d < today
        except:
            return False

    def apply_filters(self, *args):
        # Очистка дерева
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_q = self.search_text.get().lower()
        filter_csm_active = self.filter_csm.get()
        filter_overdue_active = self.filter_overdue.get()

        visible_count = 0
        for r_idx, row in enumerate(self.data):
            # 1. Поиск
            if search_q and not any(search_q in str(cell).lower() for cell in row):
                continue
            
            # 2. Фильтр ЦСМ (Колонка 24 по индексу - 25-я по счету)
            status_val = row[24] if 24 < len(row) else ""
            if filter_csm_active and status_val != "Сдали в ЦСМ":
                continue

            # 3. Фильтр Просрочка (Колонка 9 по индексу - 10-я по счету)
            date_val = row[9] if 9 < len(row) else ""
            if filter_overdue_active and not self.is_overdue(date_val):
                continue

            # Определяем цвет строки
            tags = ()
            if status_val == "Сдали в ЦСМ":
                tags = ("csm",)
            elif status_val == "Вернулся с ЦСМ":
                tags = ("returned",)
            elif status_val == "Отдали РЭС/СП":
                tags = ("res",)
            elif self.is_overdue(date_val):
                tags = ("overdue",)

            self.tree.insert("", "end", iid=str(r_idx), values=row, tags=tags)
            visible_count += 1
        
        self.status.config(text=f"Отображено строк: {visible_count} из {self.rows}")

    # --- Редактирование ---
    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        item = self.tree.identify_row(event.x, event.y)
        column = self.tree.identify_column(event.x, event.y)
        if not item or not column: return

        r_idx = int(item)
        c_idx = int(column.replace("#", "")) - 1

        x, y, width, height = self.tree.bbox(item, column)
        current_val = self.data[r_idx][c_idx]

        # Для статусов делаем выпадающий список
        if c_idx == 24:
            editor = ttk.Combobox(self.tree, values=["", "Сдали в СМ", "Отдали РЭС/СП", "Вернулся с ЦСМ", "Сдали в ЦСМ"])
            editor.set(current_val)
        else:
            editor = tk.Entry(self.tree)
            editor.insert(0, current_val)

        editor.place(x=x, y=y, width=width, height=height)
        editor.focus_set()

        def save_edit(event=None):
            new_val = editor.get()
            self.data[r_idx][c_idx] = new_val
            editor.destroy()
            self.apply_filters() # Перерисовка для обновления стилей

        def cancel_edit(event=None):
            editor.destroy()

        editor.bind("<Return>", save_edit)
        editor.bind("<Escape>", cancel_edit)
        if isinstance(editor, ttk.Combobox):
            editor.bind("<<ComboboxSelected>>", save_edit)
        else:
            editor.bind("<FocusOut>", save_edit)

    # --- Копирование / Вставка ---
    def copy_to_clipboard(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        lines = []
        for item in selected_items:
            r_idx = int(item)
            row = self.data[r_idx]
            lines.append("\t".join(row))
        
        clipboard_text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_text)
        self.status.config(text="Скопировано строк: " + str(len(selected_items)))

    def paste_from_clipboard(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Информация", "Выберите строку для вставки")
            return
            
        start_row = int(selected_items[0])
        try:
            clipboard_text = self.root.clipboard_get()
        except:
            return

        lines = clipboard_text.strip().split("\n")
        for i, line in enumerate(lines):
            r_idx = start_row + i
            if r_idx >= self.rows:
                self.add_row() # Автоматически расширяем таблицу, если не хватает места
            
            cells = line.split("\t")
            for j, cell in enumerate(cells):
                if j < self.cols:
                    self.data[r_idx][j] = cell
        
        self.apply_filters()
        self.status.config(text="Вставлено строк: " + str(len(lines)))

    # --- Управление строками ---
    def add_row(self):
        self.data.append(["" for _ in range(self.cols)])
        self.rows += 1
        self.apply_filters()

    def delete_row(self):
        selected_items = self.tree.selection()
        if not selected_items: return
        
        # Удаляем с конца, чтобы не сбить индексы
        indexes = sorted([int(i) for i in selected_items], reverse=True)
        for r_idx in indexes:
            del self.data[r_idx]
            self.rows -= 1
            
        self.apply_filters()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpreadsheetApp(root)
    root.mainloop()
