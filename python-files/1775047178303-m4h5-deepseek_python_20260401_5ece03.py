import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class PoolJournal:
    def __init__(self, root):
        self.root = root
        self.root.title("Журнал обслуживания бассейна")
        self.root.geometry("800x500")
        self.root.resizable(True, True)

        # Подключение к БД
        self.conn = sqlite3.connect('pool_service.db')
        self.cursor = self.conn.cursor()
        self.create_table()

        # Виджеты
        self.create_widgets()
        self.load_data()

    def create_table(self):
        """Создаёт таблицу, если её нет"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                service_type TEXT NOT NULL,
                notes TEXT
            )
        ''')
        self.conn.commit()

    def create_widgets(self):
        # Фрейм для ввода данных
        input_frame = ttk.LabelFrame(self.root, text="Добавить / Редактировать", padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=15)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)
        # Подставляем сегодняшнюю дату
        self.date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))

        ttk.Label(input_frame, text="Тип обслуживания:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.type_entry = ttk.Entry(input_frame, width=25)
        self.type_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="Комментарий:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.notes_entry = ttk.Entry(input_frame, width=60)
        self.notes_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='ew')

        # Кнопки действий
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        self.add_btn = ttk.Button(btn_frame, text="Добавить", command=self.add_record)
        self.add_btn.pack(side='left', padx=5)

        self.edit_btn = ttk.Button(btn_frame, text="Редактировать", command=self.edit_record, state='disabled')
        self.edit_btn.pack(side='left', padx=5)

        self.delete_btn = ttk.Button(btn_frame, text="Удалить", command=self.delete_record, state='disabled')
        self.delete_btn.pack(side='left', padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="Очистить форму", command=self.clear_form)
        self.clear_btn.pack(side='left', padx=5)

        # Поиск
        search_frame = ttk.LabelFrame(self.root, text="Поиск", padding=5)
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text="Искать:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_records())

        ttk.Button(search_frame, text="Сброс", command=self.load_data).pack(side='left', padx=5)

        # Таблица записей
        columns = ('id', 'date', 'service_type', 'notes')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings', height=15)
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        # Заголовки
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Дата')
        self.tree.heading('service_type', text='Тип обслуживания')
        self.tree.heading('notes', text='Комментарий')

        self.tree.column('id', width=40, anchor='center')
        self.tree.column('date', width=100, anchor='center')
        self.tree.column('service_type', width=200)
        self.tree.column('notes', width=400)

        # Обработка выбора записи
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(self.root, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

    def load_data(self, search_text=''):
        """Загружает данные в таблицу"""
        # Очищаем текущие строки
        for row in self.tree.get_children():
            self.tree.delete(row)

        if search_text:
            query = "SELECT * FROM services WHERE date LIKE ? OR service_type LIKE ? OR notes LIKE ? ORDER BY date DESC"
            like = f'%{search_text}%'
            self.cursor.execute(query, (like, like, like))
        else:
            self.cursor.execute("SELECT * FROM services ORDER BY date DESC")
        rows = self.cursor.fetchall()

        for row in rows:
            self.tree.insert('', 'end', values=row)

    def search_records(self):
        """Выполняет поиск по введённому тексту"""
        search_text = self.search_var.get()
        self.load_data(search_text)

    def on_select(self, event):
        """При выборе записи активируем кнопки редактирования/удаления и заполняем форму"""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item['values']
        if values:
            self.edit_btn.config(state='normal')
            self.delete_btn.config(state='normal')
            # Заполняем поля для редактирования
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, values[1])
            self.type_entry.delete(0, tk.END)
            self.type_entry.insert(0, values[2])
            self.notes_entry.delete(0, tk.END)
            self.notes_entry.insert(0, values[3] if values[3] else '')
            # Сохраняем ID выбранной записи
            self.selected_id = values[0]
        else:
            self.clear_form()

    def add_record(self):
        """Добавляет новую запись"""
        date = self.date_entry.get().strip()
        service_type = self.type_entry.get().strip()
        notes = self.notes_entry.get().strip()

        if not date or not service_type:
            messagebox.showwarning("Не хватает данных", "Заполните дату и тип обслуживания.")
            return

        try:
            # Проверка формата даты
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД (например, 2025-03-30)")
            return

        self.cursor.execute(
            "INSERT INTO services (date, service_type, notes) VALUES (?, ?, ?)",
            (date, service_type, notes)
        )
        self.conn.commit()
        self.load_data()
        self.clear_form()
        messagebox.showinfo("Успех", "Запись добавлена.")

    def edit_record(self):
        """Редактирует выбранную запись"""
        if not hasattr(self, 'selected_id'):
            messagebox.showwarning("Нет выбора", "Выберите запись для редактирования.")
            return

        date = self.date_entry.get().strip()
        service_type = self.type_entry.get().strip()
        notes = self.notes_entry.get().strip()

        if not date or not service_type:
            messagebox.showwarning("Не хватает данных", "Заполните дату и тип обслуживания.")
            return

        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
            return

        self.cursor.execute(
            "UPDATE services SET date=?, service_type=?, notes=? WHERE id=?",
            (date, service_type, notes, self.selected_id)
        )
        self.conn.commit()
        self.load_data()
        self.clear_form()
        messagebox.showinfo("Успех", "Запись обновлена.")

    def delete_record(self):
        """Удаляет выбранную запись с подтверждением"""
        if not hasattr(self, 'selected_id'):
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            self.cursor.execute("DELETE FROM services WHERE id=?", (self.selected_id,))
            self.conn.commit()
            self.load_data()
            self.clear_form()
            messagebox.showinfo("Успех", "Запись удалена.")

    def clear_form(self):
        """Очищает поля ввода и снимает выделение"""
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.type_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        self.edit_btn.config(state='disabled')
        self.delete_btn.config(state='disabled')
        if hasattr(self, 'selected_id'):
            del self.selected_id
        # Снимаем выделение в таблице
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def __del__(self):
        """Закрываем соединение с БД при завершении"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = PoolJournal(root)
    root.mainloop()