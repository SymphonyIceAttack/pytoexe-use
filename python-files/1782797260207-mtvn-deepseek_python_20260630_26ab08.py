import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

class SpreadsheetCanvas:
    """
    Custom spreadsheet widget using tkinter.Canvas.
    Supports cell selection, editing, resizing, filtering, etc.
    """
    def __init__(self, master, rows=10, cols=30):
        self.master = master
        self.rows = rows
        self.cols = cols

        # Data
        self.data = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        self.col_names = [None] * self.cols
        self.column_widths = [80] * self.cols
        self.row_heights = [25] * self.rows
        self.hidden_rows = set()
        self.hidden_cols = set()

        # Selection
        self.active_row = None
        self.active_col = None
        self.selected_rows = set()
        self.selected_cols = set()
        self.selection_anchor = None

        # Filters
        self.search_text = ""
        self.column_filters = {}  # col -> set of allowed values
        self.filter_csm = False
        self.filter_overdue = False
        self.filter_month_year = None  # (month, year)

        # Editing
        self.editor_widget = None
        self.editing_cell = None

        # Geometry
        self.header_height = 25
        self.row_header_width = 40

        # Canvas with scrollbars
        self.canvas_frame = ttk.Frame(master)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Shift-Button-1>", self.on_shift_click)
        self.canvas.bind("<Key>", self.on_key)
        self.canvas.focus_set()

        # Resize
        self.resize_handle = None
        self.canvas.bind("<ButtonRelease-1>", self.on_resize_release)

        # Init sample data
        self.init_sample_data()
        self.render()

        # Bind clipboard
        self.master.bind("<Control-c>", self.copy_selection)
        self.master.bind("<Control-v>", self.paste_from_clipboard)

    def init_sample_data(self):
        headers = ["№", "Наименование", "Тип", "Зав.№", "Дата поверки", "Дата следующей поверки",
                   "Примечание", "Статус", "Дата в ЦСМ", "Дата возврата", "Инв.№", "Цена", "Кол-во",
                   "Ед.изм.", "Местонахождение", "Ответственный", "Телефон", "email", "Поставщик",
                   "Дата поступления", "Акт", "Заказ", "Проект", "Подразделение", "Статус (детально)"]
        for c, name in enumerate(headers):
            if c < self.cols:
                self.col_names[c] = name
                self.column_widths[c] = 100
        sample = [
            ["1", "Мультиметр", "Fluke 87V", "12345", "01.01.2025", "01.01.2026", "", "В работе", "", "", "INV-001", "5000", "1", "шт.", "Лаб.1", "Иванов", "123", "i@i.ru", "ООО", "10.01.2025", "", "", "", "", "Сдали в ЦСМ"],
            ["2", "Осциллограф", "Tektronix", "67890", "15.03.2025", "15.03.2026", "", "В ремонте", "", "", "INV-002", "12000", "1", "шт.", "Лаб.2", "Петров", "456", "p@p.ru", "ЗАО", "20.02.2025", "", "", "", "", "Отдали РЭС/СП"],
            ["3", "Источник питания", "Agilent", "11223", "20.12.2024", "20.12.2025", "", "На складе", "", "", "INV-003", "8000", "2", "шт.", "Склад", "Сидоров", "789", "s@s.ru", "", "", "", "", "", "", "Вернулся с ЦСМ"],
        ]
        for i, row in enumerate(sample):
            if i < self.rows:
                for j, val in enumerate(row):
                    if j < self.cols:
                        self.data[i][j] = val

    # ---------- Rendering ----------
    def render(self):
        self.canvas.delete("all")
        self.draw_table()

    def draw_table(self):
        # Calculate total size
        total_w = self.row_header_width
        visible_cols = [c for c in range(self.cols) if c not in self.hidden_cols]
        for c in visible_cols:
            total_w += self.column_widths[c]
        total_h = self.header_height
        visible_rows = [r for r in range(self.rows) if r not in self.hidden_rows]
        for r in visible_rows:
            total_h += self.row_heights[r]
        self.canvas.config(scrollregion=(0, 0, total_w, total_h))

        # Draw header row
        x = self.row_header_width
        for c in visible_cols:
            w = self.column_widths[c]
            # Background
            self.canvas.create_rectangle(x, 0, x+w, self.header_height, fill="#f3f3f3", outline="#d0d0d0", tags="header")
            # Column name
            display = self.get_display_name(c)
            self.canvas.create_text(x + w/2, self.header_height/2, text=display, anchor="center",
                                    font=("Segoe UI", 9, "bold"), tags="header")
            # Resize handle
            handle_x = x + w - 3
            self.canvas.create_rectangle(handle_x, 0, handle_x+6, self.header_height, fill="", outline="",
                                         tags=("resize_handle", f"col_{c}"))
            x += w

        # Draw row headers
        y = self.header_height
        for r in visible_rows:
            h = self.row_heights[r]
            self.canvas.create_rectangle(0, y, self.row_header_width, y+h, fill="#f3f3f3", outline="#d0d0d0", tags="row_header")
            self.canvas.create_text(self.row_header_width/2, y+h/2, text=str(r+1), anchor="center",
                                    font=("Segoe UI", 9), tags="row_header")
            y += h

        # Draw cells
        y = self.header_height
        for r in visible_rows:
            h = self.row_heights[r]
            x = self.row_header_width
            for c in visible_cols:
                w = self.column_widths[c]
                val = str(self.data[r][c])
                # Determine background
                bg = "white"
                if r in self.selected_rows and c in self.selected_cols:
                    bg = "#cce5ff"
                elif r == self.active_row and c == self.active_col:
                    bg = "#cce5ff"

                # Row status colors
                status_val = str(self.data[r][24]) if 24 < self.cols else ""
                if status_val == "Сдали в ЦСМ":
                    bg = self.blend(bg, "#d9f0ff", 0.3)
                elif status_val == "Вернулся с ЦСМ":
                    bg = self.blend(bg, "#ffffcc", 0.3)
                elif status_val == "Отдали РЭС/СП":
                    bg = self.blend(bg, "#ccffcc", 0.3)
                elif self.is_overdue(str(self.data[r][9])) if 9 < self.cols else False:
                    bg = self.blend(bg, "#ffd9d9", 0.3)

                # Date columns (8,9,24) - greyish
                if c in (8,9,24):
                    bg = self.blend(bg, "#e6e6e6", 0.2)

                rect = self.canvas.create_rectangle(x, y, x+w, y+h, fill=bg, outline="#d0d0d0",
                                                    tags=("cell", f"cell_{r}_{c}", f"row_{r}", f"col_{c}"))
                self.canvas.create_text(x+4, y+h/2, text=val, anchor="w",
                                        font=("Segoe UI", 9), tags=("cell_text", f"text_{r}_{c}"))
                x += w
            y += h

        # Active cell outline
        if self.active_row is not None and self.active_col is not None:
            if self.active_row not in self.hidden_rows and self.active_col not in self.hidden_cols:
                x, y = self.get_cell_coords(self.active_row, self.active_col)
                w = self.column_widths[self.active_col]
                h = self.row_heights[self.active_row]
                self.canvas.create_rectangle(x, y, x+w, y+h, outline="#1a73e8", width=2, tags="active_outline")

    def get_cell_coords(self, row, col):
        x = self.row_header_width
        for c in range(self.cols):
            if c in self.hidden_cols:
                continue
            if c == col:
                break
            x += self.column_widths[c]
        y = self.header_height
        for r in range(self.rows):
            if r in self.hidden_rows:
                continue
            if r == row:
                break
            y += self.row_heights[r]
        return x, y

    def blend(self, c1, c2, ratio):
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        c1 = c1 if c1.startswith('#') else '#ffffff'
        c2 = c2 if c2.startswith('#') else '#ffffff'
        r1,g1,b1 = hex_to_rgb(c1)
        r2,g2,b2 = hex_to_rgb(c2)
        r = int(r1 + (r2-r1)*ratio)
        g = int(g1 + (g2-g1)*ratio)
        b = int(b1 + (b2-b1)*ratio)
        return rgb_to_hex((r,g,b))

    # ---------- Utility ----------
    def get_display_name(self, col):
        letter = self.column_letter(col)
        name = self.col_names[col]
        if name and name.strip():
            return f"{letter}: {name.strip()}"
        return letter

    def column_letter(self, index):
        s = ""
        n = index + 1
        while n > 0:
            n -= 1
            s = chr(65 + (n % 26)) + s
            n //= 26
        return s

    def parse_date(self, date_str):
        if not date_str:
            return None
        parts = date_str.split(".")
        if len(parts) == 3:
            try:
                day = int(parts[0])
                month = int(parts[1]) - 1
                year = int(parts[2])
                return datetime(year, month, day)
            except:
                pass
        return None

    def is_overdue(self, date_str):
        d = self.parse_date(date_str)
        if not d:
            return False
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return d < today

    # ---------- Interaction ----------
    def on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        for item in items:
            tags = self.canvas.gettags(item)
            if "resize_handle" in tags:
                for tag in tags:
                    if tag.startswith("col_"):
                        col = int(tag.split("_")[1])
                        self.start_resize_column(col, x)
                        return
            if "cell" in tags:
                for tag in tags:
                    if tag.startswith("cell_"):
                        _, r, c = tag.split("_")
                        row = int(r)
                        col = int(c)
                        self.set_active(row, col)
                        self.canvas.focus_set()
                        return
        # Click on header? For now ignore

    def on_double_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        for item in items:
            tags = self.canvas.gettags(item)
            if "header" in tags:
                col = self.get_col_from_x(x)
                if col is not None:
                    self.edit_column_name(col)
                    return
            if "cell" in tags:
                for tag in tags:
                    if tag.startswith("cell_"):
                        _, r, c = tag.split("_")
                        row = int(r)
                        col = int(c)
                        self.start_editing(row, col)
                        return

    def on_drag(self, event):
        if self.selection_anchor:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            row = self.get_row_from_y(y)
            col = self.get_col_from_x(x)
            if row is not None and col is not None:
                anchor_row, anchor_col = self.selection_anchor
                self.select_range(anchor_row, anchor_col, row, col)
                self.render()

    def on_shift_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        row = self.get_row_from_y(y)
        col = self.get_col_from_x(x)
        if row is not None and col is not None:
            if self.active_row is not None and self.active_col is not None:
                self.select_range(self.active_row, self.active_col, row, col)
                self.render()
            else:
                self.set_active(row, col)

    def on_key(self, event):
        if self.editor_widget:
            return
        key = event.keysym
        if self.active_row is None or self.active_col is None:
            return
        new_row, new_col = self.active_row, self.active_col
        if key == "Up":
            new_row = self.find_prev_visible_row(self.active_row)
        elif key == "Down":
            new_row = self.find_next_visible_row(self.active_row)
        elif key == "Left":
            new_col = self.find_prev_visible_col(self.active_col)
        elif key == "Right":
            new_col = self.find_next_visible_col(self.active_col)
        else:
            return
        if new_row != self.active_row or new_col != self.active_col:
            self.set_active(new_row, new_col)
            self.render()

    def find_prev_visible_row(self, row):
        for r in range(row-1, -1, -1):
            if r not in self.hidden_rows:
                return r
        return row

    def find_next_visible_row(self, row):
        for r in range(row+1, self.rows):
            if r not in self.hidden_rows:
                return r
        return row

    def find_prev_visible_col(self, col):
        for c in range(col-1, -1, -1):
            if c not in self.hidden_cols:
                return c
        return col

    def find_next_visible_col(self, col):
        for c in range(col+1, self.cols):
            if c not in self.hidden_cols:
                return c
        return col

    # ---------- Selection ----------
    def set_active(self, row, col):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return
        if row in self.hidden_rows or col in self.hidden_cols:
            return
        self.active_row = row
        self.active_col = col
        self.selected_rows.clear()
        self.selected_cols.clear()
        self.selected_rows.add(row)
        self.selected_cols.add(col)
        self.selection_anchor = (row, col)
        self.render()
        self.master.event_generate("<<StatusUpdate>>")  # notify main to update status

    def select_range(self, row1, col1, row2, col2):
        min_row = min(row1, row2)
        max_row = max(row1, row2)
        min_col = min(col1, col2)
        max_col = max(col1, col2)
        self.selected_rows = set(range(min_row, max_row+1))
        self.selected_cols = set(range(min_col, max_col+1))
        # Remove hidden
        self.selected_rows = {r for r in self.selected_rows if r not in self.hidden_rows}
        self.selected_cols = {c for c in self.selected_cols if c not in self.hidden_cols}
        self.active_row = row1
        self.active_col = col1
        self.selection_anchor = (row1, col1)
        self.render()
        self.master.event_generate("<<StatusUpdate>>")

    # ---------- Editing ----------
    def start_editing(self, row, col):
        if self.editor_widget:
            self.finish_editing()
        x, y = self.get_cell_coords(row, col)
        w = self.column_widths[col]
        h = self.row_heights[row]
        val = str(self.data[row][col])

        if col == 24:  # Status column
            options = ["", "Сдали в СМ", "Отдали РЭС/СП", "Вернулся с ЦСМ", "Сдали в ЦСМ"]
            self.editor_widget = ttk.Combobox(self.canvas, values=options, state="readonly")
            self.editor_widget.set(val)
            self.editor_widget.place(x=x, y=y, width=w, height=h)
            self.editor_widget.bind("<<ComboboxSelected>>", lambda e: self.finish_editing())
        else:
            self.editor_widget = tk.Entry(self.canvas)
            self.editor_widget.insert(0, val)
            self.editor_widget.place(x=x, y=y, width=w, height=h)
            self.editor_widget.focus()
            self.editor_widget.select_range(0, tk.END)
        self.editing_cell = (row, col)
        self.editor_widget.bind("<Return>", lambda e: self.finish_editing())
        self.editor_widget.bind("<Escape>", lambda e: self.cancel_editing())
        self.editor_widget.bind("<FocusOut>", lambda e: self.finish_editing())

    def finish_editing(self, event=None):
        if not self.editor_widget:
            return
        row, col = self.editing_cell
        val = self.editor_widget.get()
        self.data[row][col] = val
        self.editor_widget.destroy()
        self.editor_widget = None
        self.editing_cell = None
        self.render()
        self.master.event_generate("<<StatusUpdate>>")
        self.apply_filters()

    def cancel_editing(self, event=None):
        if self.editor_widget:
            self.editor_widget.destroy()
            self.editor_widget = None
            self.editing_cell = None
            self.render()

    # ---------- Copy/Paste ----------
    def copy_selection(self, event=None):
        if not self.selected_rows or not self.selected_cols:
            return
        rows = sorted(self.selected_rows)
        cols = sorted(self.selected_cols)
        lines = []
        for r in rows:
            cells = []
            for c in cols:
                val = str(self.data[r][c]).replace("\t", " ").replace("\n", " ")
                cells.append(val)
            lines.append("\t".join(cells))
        text = "\n".join(lines)
        self.master.clipboard_clear()
        self.master.clipboard_append(text)

    def paste_from_clipboard(self, event=None):
        if self.active_row is None or self.active_col is None:
            messagebox.showinfo("Инфо", "Сначала выберите ячейку для вставки.")
            return
        try:
            text = self.master.clipboard_get()
        except:
            return
        lines = text.split("\n")
        row_start = self.active_row
        col_start = self.active_col
        rows_data = []
        for line in lines:
            if not line.strip():
                continue
            cells = line.split("\t")
            rows_data.append(cells)
        if not rows_data:
            return

        # Ensure rows/cols
        needed_rows = row_start + len(rows_data)
        while self.rows < needed_rows:
            self.data.append(["" for _ in range(self.cols)])
            self.row_heights.append(25)
            self.rows += 1
        max_cols = max(len(row) for row in rows_data)
        needed_cols = col_start + max_cols
        while self.cols < needed_cols:
            for r in range(self.rows):
                self.data[r].append("")
            self.col_names.append(None)
            self.column_widths.append(80)
            self.cols += 1

        for i, row_cells in enumerate(rows_data):
            r = row_start + i
            if r >= self.rows:
                break
            for j, val in enumerate(row_cells):
                c = col_start + j
                if c >= self.cols:
                    break
                self.data[r][c] = val

        self.render()
        self.master.event_generate("<<StatusUpdate>>")
        self.apply_filters()

    # ---------- Column operations ----------
    def edit_column_name(self, col):
        current = self.col_names[col] if self.col_names[col] else ""
        new_name = simpledialog.askstring("Редактировать столбец", "Введите новое название:", initialvalue=current)
        if new_name is not None:
            if new_name.strip():
                self.col_names[col] = new_name.strip()
            else:
                self.col_names[col] = None
            self.render()
            self.master.event_generate("<<StatusUpdate>>")

    def toggle_column_visibility(self, col):
        if col in self.hidden_cols:
            self.hidden_cols.remove(col)
        else:
            self.hidden_cols.add(col)
            if self.active_col == col:
                self.active_col = None
                self.active_row = None
                self.selected_cols.clear()
        self.render()
        self.master.event_generate("<<StatusUpdate>>")

    def toggle_row_visibility(self, row):
        if row in self.hidden_rows:
            self.hidden_rows.remove(row)
        else:
            self.hidden_rows.add(row)
            if self.active_row == row:
                self.active_row = None
                self.active_col = None
                self.selected_rows.clear()
        self.render()
        self.master.event_generate("<<StatusUpdate>>")

    def add_row(self):
        insert_index = self.rows
        if self.active_row is not None and 0 <= self.active_row < self.rows:
            insert_index = self.active_row + 1
        self.data.insert(insert_index, ["" for _ in range(self.cols)])
        self.row_heights.insert(insert_index, 25)
        self.rows += 1
        # Adjust hidden rows
        new_hidden = set()
        for r in self.hidden_rows:
            if r >= insert_index:
                new_hidden.add(r+1)
            else:
                new_hidden.add(r)
        self.hidden_rows = new_hidden
        # Adjust selection
        new_selected = set()
        for r in self.selected_rows:
            if r >= insert_index:
                new_selected.add(r+1)
            else:
                new_selected.add(r)
        self.selected_rows = new_selected
        self.render()
        self.set_active(insert_index, self.active_col if self.active_col is not None else 0)

    def delete_selected_rows(self):
        if not self.selected_rows:
            messagebox.showinfo("Инфо", "Нет выделенных строк для удаления.")
            return
        rows_to_delete = sorted(self.selected_rows, reverse=True)
        for r in rows_to_delete:
            if 0 <= r < len(self.data):
                del self.data[r]
                del self.row_heights[r]
        self.rows = len(self.data)
        # Adjust hidden rows
        new_hidden = set()
        for r in self.hidden_rows:
            shift = sum(1 for d in rows_to_delete if d < r)
            if r not in rows_to_delete:
                new_hidden.add(r - shift)
        self.hidden_rows = new_hidden
        self.selected_rows.clear()
        self.selected_cols.clear()
        self.active_row = None
        self.active_col = None
        self.render()
        self.master.event_generate("<<StatusUpdate>>")

    # ---------- Resize columns ----------
    def start_resize_column(self, col, x):
        self.resize_handle = (col, x, self.column_widths[col])
        self.canvas.bind("<B1-Motion>", self.on_resize_move)

    def on_resize_move(self, event):
        if not self.resize_handle:
            return
        col, start_x, start_width = self.resize_handle
        dx = self.canvas.canvasx(event.x) - start_x
        new_w = max(20, start_width + dx)
        self.column_widths[col] = new_w
        self.render()

    def on_resize_release(self, event):
        if self.resize_handle:
            self.resize_handle = None
            self.canvas.unbind("<B1-Motion>")
        self.render()

    # ---------- Filters ----------
    def apply_filters(self):
        # We'll just re-render; hidden rows are set based on filters
        # We need to update hidden_rows set according to filters
        # But we also have manual hidden rows, so we combine.
        # For simplicity, we'll set a separate set for filtered hidden rows.
        # But we already have hidden_rows for manual hiding.
        # We'll keep hidden_rows as manual only, and filters are applied during render.
        # Actually, we don't need to change hidden_rows, just render with filters.
        self.render()

    def toggle_filter_csm(self):
        self.filter_csm = not self.filter_csm
        self.apply_filters()
        self.master.event_generate("<<StatusUpdate>>")

    def toggle_filter_overdue(self):
        self.filter_overdue = not self.filter_overdue
        self.apply_filters()
        self.master.event_generate("<<StatusUpdate>>")

    def filter_by_month_year(self):
        input_str = simpledialog.askstring("Фильтр по месяцу/году",
                                           "Введите месяц и год (например: 3 2026) или оставьте пустым для сброса:")
        if input_str is None:
            return
        if input_str.strip() == "":
            self.filter_month_year = None
        else:
            parts = input_str.strip().split()
            if len(parts) == 2:
                try:
                    month = int(parts[0]) - 1
                    year = int(parts[1])
                    if 0 <= month <= 11 and year > 0:
                        self.filter_month_year = (month, year)
                    else:
                        messagebox.showerror("Ошибка", "Некорректный месяц или год.")
                        return
                except:
                    messagebox.showerror("Ошибка", "Некорректный ввод. Используйте: месяц год (числа).")
                    return
            else:
                messagebox.showerror("Ошибка", "Введите два числа через пробел.")
                return
        self.apply_filters()
        self.master.event_generate("<<StatusUpdate>>")

    def on_search(self, search_text):
        self.search_text = search_text.strip()
        self.apply_filters()

    def show_filter_popup(self, col):
        popup = tk.Toplevel(self.master)
        popup.title("Фильтр")
        popup.geometry("250x300")
        popup.transient(self.master)
        popup.grab_set()

        # Search
        search_frame = ttk.Frame(popup)
        search_frame.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # List with checkboxes
        list_frame = ttk.Frame(popup)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        canvas = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Unique values
        values = sorted(set(str(self.data[r][col]) for r in range(self.rows) if r not in self.hidden_rows))
        current_filter = self.column_filters.get(col, set())

        check_vars = {}
        for val in values:
            var = tk.BooleanVar(value=val in current_filter)
            cb = ttk.Checkbutton(scrollable_frame, text=val if val else "(пусто)", variable=var)
            cb.pack(anchor="w")
            check_vars[val] = var

        def filter_list():
            query = search_var.get().lower()
            for child in scrollable_frame.winfo_children():
                if isinstance(child, ttk.Checkbutton):
                    text = child.cget("text").lower()
                    child.pack_forget() if query and query not in text else child.pack(anchor="w")
        search_var.trace("w", lambda *args: filter_list())

        # Buttons
        btn_frame = ttk.Frame(popup)
        btn_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(btn_frame, text="Выбрать все",
                   command=lambda: [var.set(True) for var in check_vars.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Очистить",
                   command=lambda: [var.set(False) for var in check_vars.values()]).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Применить", command=lambda: self.apply_column_filter(col, check_vars, popup)).pack(
            side=tk.RIGHT, padx=2)

    def apply_column_filter(self, col, check_vars, popup):
        selected = {val for val, var in check_vars.items() if var.get()}
        if selected:
            self.column_filters[col] = selected
        else:
            self.column_filters.pop(col, None)
        popup.destroy()
        self.apply_filters()
        self.master.event_generate("<<StatusUpdate>>")

    # ---------- Helper to get row/col from coordinates ----------
    def get_row_from_y(self, y):
        y -= self.header_height
        for r in range(self.rows):
            if r in self.hidden_rows:
                continue
            if y < self.row_heights[r]:
                return r
            y -= self.row_heights[r]
        return None

    def get_col_from_x(self, x):
        x -= self.row_header_width
        for c in range(self.cols):
            if c in self.hidden_cols:
                continue
            if x < self.column_widths[c]:
                return c
            x -= self.column_widths[c]
        return None


class SpreadsheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Электронная таблица")
        self.root.geometry("1200x700")

        self.spreadsheet = SpreadsheetCanvas(root, rows=10, cols=30)

        self.create_toolbar()
        self.create_statusbar()

        # Bind status update event
        self.root.bind("<<StatusUpdate>>", lambda e: self.update_status())

        # Initial update
        self.update_status()

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        tk.Button(toolbar, text="➕ Добавить строку", command=self.spreadsheet.add_row).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="🗑️ Удалить строки", command=self.spreadsheet.delete_selected_rows).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Columns dropdown
        self.cols_menu_btn = tk.Menubutton(toolbar, text="📋 Столбцы ▼", relief=tk.RAISED)
        self.cols_menu_btn.pack(side=tk.LEFT, padx=2)
        self.cols_menu = tk.Menu(self.cols_menu_btn, tearoff=0)
        self.cols_menu_btn.config(menu=self.cols_menu)

        # Rows dropdown
        self.rows_menu_btn = tk.Menubutton(toolbar, text="📋 Строки ▼", relief=tk.RAISED)
        self.rows_menu_btn.pack(side=tk.LEFT, padx=2)
        self.rows_menu = tk.Menu(self.rows_menu_btn, tearoff=0)
        self.rows_menu_btn.config(menu=self.rows_menu)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Search
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.spreadsheet.on_search(self.search_var.get()))
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(toolbar, text="🔍").pack(side=tk.LEFT)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Quick filters - using tk.Button for relief support
        self.btn_csm = tk.Button(toolbar, text="📋 ЦСМ", command=self.spreadsheet.toggle_filter_csm)
        self.btn_csm.pack(side=tk.LEFT, padx=2)

        self.btn_overdue = tk.Button(toolbar, text="⏳ Просрочка", command=self.spreadsheet.toggle_filter_overdue)
        self.btn_overdue.pack(side=tk.LEFT, padx=2)

        self.btn_month = tk.Button(toolbar, text="📅 Месяц/год", command=self.spreadsheet.filter_by_month_year)
        self.btn_month.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        tk.Button(toolbar, text="🔽 Фильтр по колонке", command=self.show_filter_for_active_col).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Label(toolbar, text="Ctrl+C / Ctrl+V — копировать/вставить (TSV)", foreground="gray").pack(side=tk.RIGHT, padx=4)

        self.update_dropdowns()

    def show_filter_for_active_col(self):
        if self.spreadsheet.active_col is not None:
            self.spreadsheet.show_filter_popup(self.spreadsheet.active_col)

    def create_statusbar(self):
        statusbar = ttk.Frame(self.root)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.cell_info = ttk.Label(statusbar, text="Ячейка: —")
        self.cell_info.pack(side=tk.LEFT, padx=4)
        self.row_col_info = ttk.Label(statusbar, text="Строк: 0, Столбцов: 0")
        self.row_col_info.pack(side=tk.RIGHT, padx=4)

    def update_dropdowns(self):
        # Columns
        self.cols_menu.delete(0, tk.END)
        for c in range(self.spreadsheet.cols):
            hidden = c in self.spreadsheet.hidden_cols
            text = self.spreadsheet.get_display_name(c)
            label = f"{text} {'(скрыт)' if hidden else ''}"
            self.cols_menu.add_command(
                label=label,
                command=lambda col=c: self.spreadsheet.toggle_column_visibility(col)
            )
        # Rows
        self.rows_menu.delete(0, tk.END)
        for r in range(self.spreadsheet.rows):
            hidden = r in self.spreadsheet.hidden_rows
            label = f"Строка {r+1} {'(скрыта)' if hidden else ''}"
            self.rows_menu.add_command(
                label=label,
                command=lambda row=r: self.spreadsheet.toggle_row_visibility(row)
            )

    def update_status(self):
        visible_rows = self.spreadsheet.rows - len(self.spreadsheet.hidden_rows)
        visible_cols = self.spreadsheet.cols - len(self.spreadsheet.hidden_cols)
        self.row_col_info.config(text=f"Строк: {visible_rows} / {self.spreadsheet.rows}, Столбцов: {visible_cols} / {self.spreadsheet.cols}")
        if self.spreadsheet.active_row is not None and self.spreadsheet.active_col is not None:
            val = str(self.spreadsheet.data[self.spreadsheet.active_row][self.spreadsheet.active_col])
            cell = f"{self.spreadsheet.get_display_name(self.spreadsheet.active_col)}{self.spreadsheet.active_row+1}"
            self.cell_info.config(text=f'Ячейка: {cell} = "{val}"')
        else:
            self.cell_info.config(text="Ячейка: —")

        # Update filter button states
        self.btn_csm.config(relief=tk.SUNKEN if self.spreadsheet.filter_csm else tk.RAISED)
        self.btn_overdue.config(relief=tk.SUNKEN if self.spreadsheet.filter_overdue else tk.RAISED)
        if self.spreadsheet.filter_month_year:
            self.btn_month.config(text=f"📅 {self.spreadsheet.filter_month_year[0]+1}/{self.spreadsheet.filter_month_year[1]}")
            self.btn_month.config(relief=tk.SUNKEN)
        else:
            self.btn_month.config(text="📅 Месяц/год")
            self.btn_month.config(relief=tk.RAISED)

        self.update_dropdowns()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpreadsheetApp(root)
    app.run()