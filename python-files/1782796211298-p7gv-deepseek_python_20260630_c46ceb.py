import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
import re
from datetime import datetime

class SpreadsheetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Электронная таблица")
        self.root.geometry("1200x700")

        # Data
        self.rows = 10
        self.cols = 30
        self.data = [["" for _ in range(self.cols)] for _ in range(self.rows)]
        self.col_names = [None] * self.cols
        self.column_widths = [80] * self.cols
        self.hidden_rows = set()
        self.hidden_cols = set()

        self.active_row = None
        self.active_col = None
        self.selected_rows = set()
        self.selected_cols = set()

        # Filters
        self.search_text = ""
        self.column_filters = {}  # col -> set of allowed values
        self.filter_csm = False
        self.filter_overdue = False
        self.filter_month_year = None  # (month, year) or None

        # Cell editor
        self.editor = None
        self.editing_cell = None  # (row, col)

        # Build UI
        self.create_toolbar()
        self.create_table()
        self.create_statusbar()

        self.render_table()
        self.update_status()
        self.update_filter_buttons()

        # Bind events
        self.bind_events()

    # ---------- UI Creation ----------
    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Buttons
        ttk.Button(toolbar, text="➕ Добавить строку", command=self.add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Удалить строки", command=self.delete_selected_rows).pack(side=tk.LEFT, padx=2)

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
        self.search_var.trace("w", lambda *args: self.on_search())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(toolbar, text="🔍").pack(side=tk.LEFT)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Quick filters
        self.btn_csm = ttk.Button(toolbar, text="📋 ЦСМ", command=self.toggle_filter_csm)
        self.btn_csm.pack(side=tk.LEFT, padx=2)

        self.btn_overdue = ttk.Button(toolbar, text="⏳ Просрочка", command=self.toggle_filter_overdue)
        self.btn_overdue.pack(side=tk.LEFT, padx=2)

        self.btn_month = ttk.Button(toolbar, text="📅 Месяц/год", command=self.filter_by_month_year)
        self.btn_month.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        # Copy/Paste info
        ttk.Label(toolbar, text="Ctrl+C / Ctrl+V — копировать/вставить (TSV)", foreground="gray").pack(side=tk.RIGHT, padx=4)

    def create_table(self):
        # Container for table and scrollbars
        table_frame = ttk.Frame(self.root)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(table_frame, show="tree headings", selectmode="extended")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=v_scroll.set)

        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(xscrollcommand=h_scroll.set)

        # Bind events
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Shift-Button-1>", self.on_tree_shift_click)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_release)
        self.tree.bind("<Key>", self.on_tree_key)
        self.tree.bind("<FocusOut>", self.on_tree_focus_out)

        # Column resize
        self.tree.bind("<<TreeviewColumnResize>>", self.on_column_resize)

    def create_statusbar(self):
        statusbar = ttk.Frame(self.root)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.cell_info = ttk.Label(statusbar, text="Ячейка: —")
        self.cell_info.pack(side=tk.LEFT, padx=4)
        self.row_col_info = ttk.Label(statusbar, text="Строк: 0, Столбцов: 0")
        self.row_col_info.pack(side=tk.RIGHT, padx=4)

    def bind_events(self):
        self.root.bind("<Control-c>", self.copy_selection)
        self.root.bind("<Control-v>", self.paste_from_clipboard)
        self.root.bind("<Escape>", self.cancel_editing)
        self.root.bind("<Return>", self.confirm_editing)

    # ---------- Data rendering ----------
    def render_table(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Setup columns
        columns = ["row_number"] + [f"col_{i}" for i in range(self.cols)]
        self.tree["columns"] = columns
        self.tree["displaycolumns"] = [f"col_{i}" for i in range(self.cols) if i not in self.hidden_cols]

        # Column headings
        self.tree.heading("#0", text="")
        self.tree.column("#0", width=0, stretch=False)
        for i in range(self.cols):
            if i in self.hidden_cols:
                continue
            display = self.get_display_name(i)
            self.tree.heading(f"col_{i}", text=display)
            self.tree.column(f"col_{i}", width=self.column_widths[i], minwidth=20, stretch=False)

        # Insert rows
        visible_rows = [r for r in range(self.rows) if r not in self.hidden_rows]
        # Apply filters
        filtered_rows = self.apply_filters_to_rows(visible_rows)

        for r in filtered_rows:
            values = []
            for c in range(self.cols):
                if c in self.hidden_cols:
                    continue
                val = self.data[r][c]
                values.append(val)
            item_id = f"row_{r}"
            self.tree.insert("", tk.END, iid=item_id, text="", values=values, tags=(f"row_{r}",))

        # Apply row styles
        self.update_row_styles()

        # Update status
        self.update_status()
        self.update_dropdown_menus()
        self.update_filter_buttons()

    def apply_filters_to_rows(self, rows):
        # Global search
        search_text = self.search_text.lower()
        # Column filters
        col_filters = self.column_filters
        # Quick filters
        filter_csm = self.filter_csm
        filter_overdue = self.filter_overdue
        filter_month_year = self.filter_month_year

        result = []
        for r in rows:
            show = True

            # Search
            if search_text:
                found = False
                for c in range(self.cols):
                    if search_text in str(self.data[r][c]).lower():
                        found = True
                        break
                if not found:
                    show = False

            # Column filters
            if show and col_filters:
                for c, allowed_set in col_filters.items():
                    if allowed_set:
                        val = str(self.data[r][c])
                        if val not in allowed_set:
                            show = False
                            break

            # Quick filters
            if show and filter_csm:
                status_val = str(self.data[r][24]) if 24 < self.cols else ""
                if status_val != "Сдали в ЦСМ":
                    show = False

            if show and filter_overdue:
                date_val = str(self.data[r][9]) if 9 < self.cols else ""
                if not self.is_overdue(date_val):
                    show = False

            if show and filter_month_year:
                date_val = str(self.data[r][9]) if 9 < self.cols else ""
                d = self.parse_date(date_val)
                if not d:
                    show = False
                else:
                    if d.month != filter_month_year[0] or d.year != filter_month_year[1]:
                        show = False

            if show:
                result.append(r)
        return result

    def update_row_styles(self):
        # Apply tags based on status and overdue
        # We use tags on tree items
        for r in range(self.rows):
            item_id = f"row_{r}"
            if not self.tree.exists(item_id):
                continue
            # Remove existing tags
            self.tree.item(item_id, tags=())

            status_val = str(self.data[r][24]) if 24 < self.cols else ""
            if status_val == "Сдали в ЦСМ":
                tag = "csm"
            elif status_val == "Вернулся с ЦСМ":
                tag = "returned"
            elif status_val == "Отдали РЭС/СП":
                tag = "res"
            else:
                # Check overdue
                date_val = str(self.data[r][9]) if 9 < self.cols else ""
                if self.is_overdue(date_val):
                    tag = "overdue"
                else:
                    tag = "normal"

            # Set tag
            self.tree.item(item_id, tags=(tag,))

        # Configure tags
        self.tree.tag_configure("csm", background="#d9f0ff")
        self.tree.tag_configure("returned", background="#ffffcc")
        self.tree.tag_configure("res", background="#ccffcc")
        self.tree.tag_configure("overdue", background="#ffd9d9")

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

    # ---------- Status and menus ----------
    def update_status(self):
        visible_rows = self.rows - len(self.hidden_rows)
        visible_cols = self.cols - len(self.hidden_cols)
        self.row_col_info.config(text=f"Строк: {visible_rows} / {self.rows}, Столбцов: {visible_cols} / {self.cols}")
        if self.active_row is not None and self.active_col is not None:
            val = str(self.data[self.active_row][self.active_col])
            cell = f"{self.get_display_name(self.active_col)}{self.active_row+1}"
            self.cell_info.config(text=f'Ячейка: {cell} = "{val}"')
        else:
            self.cell_info.config(text="Ячейка: —")

    def update_dropdown_menus(self):
        # Columns menu
        self.cols_menu.delete(0, tk.END)
        for c in range(self.cols):
            hidden = c in self.hidden_cols
            text = self.get_display_name(c)
            label = f"{text} {'(скрыт)' if hidden else ''}"
            self.cols_menu.add_command(
                label=label,
                command=lambda col=c: self.toggle_column_visibility(col)
            )

        # Rows menu
        self.rows_menu.delete(0, tk.END)
        for r in range(self.rows):
            hidden = r in self.hidden_rows
            label = f"Строка {r+1} {'(скрыта)' if hidden else ''}"
            self.rows_menu.add_command(
                label=label,
                command=lambda row=r: self.toggle_row_visibility(row)
            )

    def update_filter_buttons(self):
        self.btn_csm.config(relief=tk.SUNKEN if self.filter_csm else tk.RAISED)
        self.btn_overdue.config(relief=tk.SUNKEN if self.filter_overdue else tk.RAISED)
        if self.filter_month_year:
            self.btn_month.config(text=f"📅 {self.filter_month_year[0]+1}/{self.filter_month_year[1]}")
            self.btn_month.config(relief=tk.SUNKEN)
        else:
            self.btn_month.config(text="📅 Месяц/год")
            self.btn_month.config(relief=tk.RAISED)

    # ---------- Column/Row operations ----------
    def toggle_column_visibility(self, col):
        if col in self.hidden_cols:
            self.hidden_cols.remove(col)
        else:
            self.hidden_cols.add(col)
            if self.active_col == col:
                self.active_col = None
                self.active_row = None
                self.selected_cols.clear()
        self.render_table()
        self.update_status()
        self.update_dropdown_menus()

    def toggle_row_visibility(self, row):
        if row in self.hidden_rows:
            self.hidden_rows.remove(row)
        else:
            self.hidden_rows.add(row)
            if self.active_row == row:
                self.active_row = None
                self.active_col = None
                self.selected_rows.clear()
        self.render_table()
        self.update_status()
        self.update_dropdown_menus()

    def add_row(self):
        insert_index = self.rows
        if self.active_row is not None and 0 <= self.active_row < self.rows:
            insert_index = self.active_row + 1
        self.data.insert(insert_index, ["" for _ in range(self.cols)])
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
        self.render_table()
        self.set_active(insert_index, self.active_col if self.active_col is not None else 0)

    def delete_selected_rows(self):
        if not self.selected_rows:
            messagebox.showinfo("Инфо", "Нет выделенных строк для удаления.")
            return
        rows_to_delete = sorted(self.selected_rows, reverse=True)
        for r in rows_to_delete:
            if 0 <= r < len(self.data):
                del self.data[r]
        self.rows = len(self.data)
        # Adjust hidden rows
        new_hidden = set()
        for r in self.hidden_rows:
            shift = sum(1 for d in rows_to_delete if d < r)
            if r not in rows_to_delete:
                new_hidden.add(r - shift)
        self.hidden_rows = new_hidden
        # Clear selections
        self.selected_rows.clear()
        self.selected_cols.clear()
        self.active_row = None
        self.active_col = None
        self.render_table()
        self.update_status()
        self.update_dropdown_menus()

    def edit_column_name(self, col):
        current = self.col_names[col] if self.col_names[col] else ""
        new_name = simpledialog.askstring("Редактировать столбец", "Введите новое название:", initialvalue=current)
        if new_name is not None:
            if new_name.strip():
                self.col_names[col] = new_name.strip()
            else:
                self.col_names[col] = None
            self.render_table()
            self.update_status()
            self.update_dropdown_menus()

    # ---------- Selection and navigation ----------
    def set_active(self, row, col):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return
        if row in self.hidden_rows or col in self.hidden_cols:
            return
        self.active_row = row
        self.active_col = col
        self.selected_rows.clear()
        self.selected_cols.clear()
        # Select the row in treeview
        item_id = f"row_{row}"
        if self.tree.exists(item_id):
            self.tree.selection_set(item_id)
            self.tree.focus(item_id)
            self.tree.see(item_id)
        self.update_status()
        self.update_row_styles()

    def select_range(self, row1, col1, row2, col2):
        min_row = min(row1, row2)
        max_row = max(row1, row2)
        min_col = min(col1, col2)
        max_col = max(col1, col2)
        self.selected_rows = set(range(min_row, max_row+1))
        self.selected_cols = set(range(min_col, max_col+1))
        self.active_row = row1
        self.active_col = col1
        # Select rows in treeview
        self.tree.selection_set([f"row_{r}" for r in self.selected_rows if r not in self.hidden_rows])
        self.update_status()
        self.update_row_styles()

    # ---------- Tree events ----------
    def on_tree_click(self, event):
        # Get clicked row/col
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            # Column header click
            col_id = self.tree.identify_column(event.x)
            if col_id and col_id != "#0":
                col_index = int(col_id.replace("col_", ""))
                # Check if filter icon clicked? Not implemented.
                # For simplicity, we treat as column selection
                self.select_column(col_index)
            elif col_id == "#0":
                pass
            return
        elif region == "cell":
            item = self.tree.identify_row(event.y)
            if not item:
                return
            row = int(item.replace("row_", ""))
            col_id = self.tree.identify_column(event.x)
            if col_id and col_id != "#0":
                col = int(col_id.replace("col_", ""))
                if col not in self.hidden_cols:
                    self.set_active(row, col)
            return
        else:
            # Tree area
            item = self.tree.identify_row(event.y)
            if item:
                row = int(item.replace("row_", ""))
                # If no modifier, select row
                if event.state & 0x0001:  # Shift
                    # Shift click - we'll handle in separate event
                    pass
                else:
                    # Select row, keep active column if possible
                    if self.active_col is not None and self.active_col not in self.hidden_cols:
                        col = self.active_col
                    else:
                        # find first visible col
                        visible = [c for c in range(self.cols) if c not in self.hidden_cols]
                        col = visible[0] if visible else 0
                    self.set_active(row, col)
            else:
                # Click on empty space, deselect
                self.tree.selection_set()

    def on_tree_shift_click(self, event):
        # Range selection with shift
        item = self.tree.identify_row(event.y)
        if not item:
            return
        row = int(item.replace("row_", ""))
        col_id = self.tree.identify_column(event.x)
        if col_id and col_id != "#0":
            col = int(col_id.replace("col_", ""))
        else:
            col = self.active_col if self.active_col is not None else 0
        if self.active_row is not None and self.active_col is not None:
            self.select_range(self.active_row, self.active_col, row, col)
        else:
            self.set_active(row, col)

    def on_tree_release(self, event):
        pass

    def on_tree_key(self, event):
        # Arrow keys navigation
        if self.active_row is None or self.active_col is None:
            return
        key = event.keysym
        new_row = self.active_row
        new_col = self.active_col
        if key == "Up":
            new_row = max(0, self.active_row - 1)
        elif key == "Down":
            new_row = min(self.rows - 1, self.active_row + 1)
        elif key == "Left":
            new_col = max(0, self.active_col - 1)
        elif key == "Right":
            new_col = min(self.cols - 1, self.active_col + 1)
        else:
            return
        # Skip hidden
        while new_row != self.active_row and (new_row in self.hidden_rows or new_row < 0 or new_row >= self.rows):
            if key == "Up":
                new_row -= 1
            else:
                new_row += 1
            if new_row < 0 or new_row >= self.rows:
                break
        while new_col != self.active_col and (new_col in self.hidden_cols or new_col < 0 or new_col >= self.cols):
            if key == "Left":
                new_col -= 1
            else:
                new_col += 1
            if new_col < 0 or new_col >= self.cols:
                break
        if new_row != self.active_row or new_col != self.active_col:
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols and new_row not in self.hidden_rows and new_col not in self.hidden_cols:
                self.set_active(new_row, new_col)
                self.tree.selection_set(f"row_{new_row}")
                self.tree.focus(f"row_{new_row}")
                self.tree.see(f"row_{new_row}")

    def on_tree_focus_out(self, event):
        # Cancel editing if any
        if self.editor:
            self.cancel_editing()

    def on_tree_double_click(self, event):
        # Edit cell
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        row = int(item.replace("row_", ""))
        col_id = self.tree.identify_column(event.x)
        if not col_id or col_id == "#0":
            return
        col = int(col_id.replace("col_", ""))
        if row in self.hidden_rows or col in self.hidden_cols:
            return
        self.start_editing(row, col)

    def on_column_resize(self, event):
        # Update column widths
        for c in range(self.cols):
            col_id = f"col_{c}"
            if col_id in self.tree.column(col_id, "width"):
                self.column_widths[c] = self.tree.column(col_id, "width")

    # ---------- Editing ----------
    def start_editing(self, row, col):
        if self.editor:
            self.cancel_editing()
        # Get cell value
        val = str(self.data[row][col])
        # Create an Entry over the cell
        # Get cell bounding box
        item = f"row_{row}"
        if not self.tree.exists(item):
            return
        bbox = self.tree.bbox(item, f"col_{col}")
        if not bbox:
            return
        x, y, width, height = bbox
        # Adjust for scroll
        x += self.tree.winfo_x()
        y += self.tree.winfo_y()

        self.editor = tk.Entry(self.root)
        self.editor.place(x=x, y=y, width=width, height=height)
        self.editor.insert(0, val)
        self.editor.focus()
        self.editor.select_range(0, tk.END)
        self.editor.bind("<Return>", lambda e: self.confirm_editing())
        self.editor.bind("<Escape>", lambda e: self.cancel_editing())
        self.editor.bind("<FocusOut>", lambda e: self.confirm_editing())
        self.editing_cell = (row, col)

    def confirm_editing(self, event=None):
        if self.editor is None:
            return
        row, col = self.editing_cell
        val = self.editor.get()
        self.data[row][col] = val
        # Update tree
        item = f"row_{row}"
        if self.tree.exists(item):
            values = list(self.tree.item(item, "values"))
            # Find column index in display columns
            display_cols = [c for c in range(self.cols) if c not in self.hidden_cols]
            try:
                idx = display_cols.index(col)
                values[idx] = val
                self.tree.item(item, values=values)
            except ValueError:
                pass
        self.destroy_editor()
        self.update_status()
        self.update_row_styles()
        # Reapply filters in case value changed
        self.render_table()

    def cancel_editing(self, event=None):
        self.destroy_editor()

    def destroy_editor(self):
        if self.editor:
            self.editor.destroy()
            self.editor = None
            self.editing_cell = None

    # ---------- Copy/Paste ----------
    def copy_selection(self, event=None):
        if not self.selected_rows and self.active_row is None:
            return
        rows_set = self.selected_rows if self.selected_rows else {self.active_row}
        cols_set = self.selected_cols if self.selected_cols else {self.active_col}
        # Filter hidden
        rows_set = {r for r in rows_set if r not in self.hidden_rows}
        cols_set = {c for c in cols_set if c not in self.hidden_cols}
        if not rows_set or not cols_set:
            return
        rows = sorted(rows_set)
        cols = sorted(cols_set)
        lines = []
        for r in rows:
            cells = []
            for c in cols:
                val = str(self.data[r][c]).replace("\t", " ").replace("\n", " ")
                cells.append(val)
            lines.append("\t".join(cells))
        text = "\n".join(lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def paste_from_clipboard(self, event=None):
        if self.active_row is None or self.active_col is None:
            messagebox.showinfo("Инфо", "Сначала выберите ячейку для вставки.")
            return
        try:
            text = self.root.clipboard_get()
        except:
            return
        lines = text.split("\n")
        row_start = self.active_row
        col_start = self.active_col
        # Parse TSV
        rows_data = []
        for line in lines:
            if not line.strip():
                continue
            cells = line.split("\t")
            rows_data.append(cells)

        if not rows_data:
            return

        # Ensure enough rows/cols
        needed_rows = row_start + len(rows_data)
        while self.rows < needed_rows:
            self.data.append(["" for _ in range(self.cols)])
            self.rows += 1

        max_cols = max(len(row) for row in rows_data)
        needed_cols = col_start + max_cols
        while self.cols < needed_cols:
            for r in range(self.rows):
                self.data[r].append("")
            self.col_names.append(None)
            self.column_widths.append(80)
            self.cols += 1

        # Insert data
        for i, row_cells in enumerate(rows_data):
            r = row_start + i
            if r >= self.rows:
                break
            for j, val in enumerate(row_cells):
                c = col_start + j
                if c >= self.cols:
                    break
                self.data[r][c] = val

        self.render_table()
        # Set active to end of paste
        self.set_active(row_start + len(rows_data) - 1, col_start + max_cols - 1)

    # ---------- Quick filters ----------
    def toggle_filter_csm(self):
        self.filter_csm = not self.filter_csm
        self.update_filter_buttons()
        self.render_table()

    def toggle_filter_overdue(self):
        self.filter_overdue = not self.filter_overdue
        self.update_filter_buttons()
        self.render_table()

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
        self.update_filter_buttons()
        self.render_table()

    def on_search(self):
        self.search_text = self.search_var.get().strip()
        self.render_table()

    # ---------- Column filter popup ----------
    def show_filter_popup(self, col, x, y):
        # We'll create a Toplevel with checkboxes
        popup = tk.Toplevel(self.root)
        popup.title("Фильтр")
        popup.geometry(f"250x300+{x}+{y}")
        popup.transient(self.root)
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

        # Search filtering
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
        self.render_table()
        self.update_status()

    # ---------- Column selection via header click ----------
    def select_column(self, col):
        if col in self.hidden_cols:
            return
        self.selected_cols.clear()
        self.selected_cols.add(col)
        self.selected_rows = set(range(self.rows))
        self.active_col = col
        # Find first visible row
        for r in range(self.rows):
            if r not in self.hidden_rows:
                self.active_row = r
                break
        self.tree.selection_set([f"row_{r}" for r in self.selected_rows if r not in self.hidden_rows])
        self.update_status()
        self.update_row_styles()

    # ---------- Filter icon click (in header) ----------
    # We'll add filter icon in column heading via custom binding? 
    # Since we cannot easily add icons to Treeview headings, we'll use a context menu on header.
    # Or we can detect right-click on header to show filter.
    # We'll add a right-click context menu on column header.
    def on_header_right_click(self, event):
        col_id = self.tree.identify_column(event.x)
        if col_id and col_id != "#0":
            col = int(col_id.replace("col_", ""))
            self.show_filter_popup(col, event.x_root, event.y_root)

    # We'll bind right-click on tree heading area
    def bind_header_events(self):
        # Treeview heading area is not directly bindable, we use a hack: bind to tree and check region
        self.tree.bind("<Button-3>", self.on_tree_right_click)

    def on_tree_right_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col_id = self.tree.identify_column(event.x)
            if col_id and col_id != "#0":
                col = int(col_id.replace("col_", ""))
                # Also allow rename on right-click? We'll show a menu with filter and rename
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Фильтр", command=lambda: self.show_filter_popup(col, event.x_root, event.y_root))
                menu.add_command(label="Переименовать", command=lambda: self.edit_column_name(col))
                menu.add_separator()
                menu.add_command(label="Скрыть столбец", command=lambda: self.toggle_column_visibility(col))
                menu.post(event.x_root, event.y_root)

    # Also we need double-click on header to rename
    def on_header_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col_id = self.tree.identify_column(event.x)
            if col_id and col_id != "#0":
                col = int(col_id.replace("col_", ""))
                self.edit_column_name(col)

    # Bind these in bind_events after tree creation
    def bind_events(self):
        self.root.bind("<Control-c>", self.copy_selection)
        self.root.bind("<Control-v>", self.paste_from_clipboard)
        self.root.bind("<Escape>", self.cancel_editing)
        self.tree.bind("<Button-3>", self.on_tree_right_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)  # already
        # We need to override double-click on heading
        # We'll capture double-click on any place, but differentiate
        # Actually, we already have on_tree_double_click, we can modify it to check region
        # Let's rebind: we'll keep on_tree_double_click and add region check
        # We'll also add a separate handler for heading double-click
        self.tree.bind("<Double-Button-1>", self.on_double_click_any)
        # Also we need to handle column resize, already bound

    def on_double_click_any(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col_id = self.tree.identify_column(event.x)
            if col_id and col_id != "#0":
                col = int(col_id.replace("col_", ""))
                self.edit_column_name(col)
        elif region == "cell":
            self.on_tree_double_click(event)

    # ---------- Main ----------
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SpreadsheetApp(root)
    app.run()