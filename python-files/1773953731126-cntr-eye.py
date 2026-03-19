import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class CamouflageDatabase:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Список Выходов")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a2f1a')
        
        # Камуфляжная цветовая палитра
        self.colors = {
            'dark_green': '#2d5016',
            'medium_green': '#556b2f',
            'light_green': '#8fbc8f',
            'brown': '#8b4513',
            'tan': '#d2b48c',
            'dark_brown': '#654321',
            'background': '#1a2f1a',
            'text_light': '#f5f5dc'
        }
        
        # Подключение к базе данных
        self.db_path = 'выходы.db'
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
        
        self.current_id = None
        self.create_widgets()
        self.load_data()
    
    def create_table(self):
        """Создание таблицы если не существует"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT,
                description TEXT,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def create_widgets(self):
        """Создание элементов интерфейса с камуфляжным дизайном"""
        
        # Главный фрейм
        main_frame = tk.Frame(self.root, bg=self.colors['background'])
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Заголовок
        title_label = tk.Label(
            main_frame,
            text="🎯 Список Выходов",
            font=('Arial', 18, 'bold'),
            bg=self.colors['background'],
            fg=self.colors['text_light'],
            pady=15
        )
        title_label.pack(fill='x')
        
        # Фрейм поиска
        search_frame = tk.Frame(main_frame, bg=self.colors['medium_green'], bd=2, relief='groove', padx=10, pady=10)
        search_frame.pack(fill='x', pady=10)
        
        tk.Label(
            search_frame,
            text="🔍 ПОИСК:",
            font=('Arial', 10, 'bold'),
            bg=self.colors['medium_green'],
            fg=self.colors['text_light']
        ).pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 11),
            width=35,
            bg=self.colors['tan'],
            fg=self.colors['dark_green'],
            insertbackground=self.colors['dark_green']
        )
        self.search_entry.pack(side='left', padx=10)
        self.search_entry.bind('<KeyRelease>', self.search_data)
        
        # Фрейм для ввода данных
        input_frame = tk.Frame(
            main_frame,
            bg=self.colors['dark_green'],
            bd=2,
            relief='groove',
            padx=15,
            pady=15
        )
        input_frame.pack(fill='x', pady=10)
        
        # Заголовок формы
        form_title = tk.Label(
            input_frame,
            text="ДОБАВИТЬ НОВЫЙ ЭЛЕМЕНТ:",
            font=('Arial', 11, 'bold'),
            bg=self.colors['dark_green'],
            fg=self.colors['text_light']
        )
        form_title.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 10))
        
        # Поля для ввода
        fields = [
            ("Название:", "name", 50),
            ("Категория:", "category", 40),
            ("Описание:", "description", 60)
        ]
        
        self.entries = {}
        for i, (label_text, field_name, width) in enumerate(fields):
            # Метка
            label = tk.Label(
                input_frame,
                text=label_text,
                font=('Arial', 9, 'bold'),
                bg=self.colors['dark_green'],
                fg=self.colors['text_light'],
                width=12,
                anchor='w'
            )
            label.grid(row=i+1, column=0, sticky='w', padx=5, pady=8)
            
            # Поле ввода
            entry = tk.Entry(
                input_frame,
                font=('Arial', 10),
                width=width,
                bg=self.colors['tan'],
                fg=self.colors['dark_green'],
                insertbackground=self.colors['dark_green']
            )
            entry.grid(row=i+1, column=1, padx=5, pady=8, sticky='w')
            self.entries[field_name] = entry
        
        # Фрейм для кнопок действий
        button_frame = tk.Frame(main_frame, bg=self.colors['background'])
        button_frame.pack(fill='x', pady=15)
        
        # Кнопки действий
        action_buttons = [
            ("➕ ДОБАВИТЬ", self.add_item, self.colors['medium_green']),
            ("✏️ РЕДАКТИРОВАТЬ", self.edit_item, self.colors['brown']),
            ("🔄 ОБНОВИТЬ", self.update_item, self.colors['dark_brown']),
            ("❌ УДАЛИТЬ", self.delete_item, '#8b0000'),
            ("🗑️ ОЧИСТИТЬ", self.clear_form, '#696969'),
            ("🔄 ОБНОВИТЬ ТАБЛИЦУ", self.load_data, '#2d5016')
        ]
        
        for i, (text, command, color) in enumerate(action_buttons):
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=('Arial', 9, 'bold'),
                padx=12,
                pady=6,
                bd=0,
                relief='raised',
                cursor='hand2'
            )
            btn.grid(row=0, column=i, padx=3)
        
        # Фрейм для таблицы
        table_frame = tk.Frame(main_frame, bg=self.colors['background'])
        table_frame.pack(fill='both', expand=True, pady=10)
        
        # Заголовок таблицы
        table_title = tk.Label(
            table_frame,
            text="СПИСОК ЭЛЕМЕНТОВ:",
            font=('Arial', 11, 'bold'),
            bg=self.colors['background'],
            fg=self.colors['text_light']
        )
        table_title.pack(anchor='w')
        
        # Создание Treeview с камуфляжным стилем
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Camouflage.Treeview",
                        background=self.colors['light_green'],
                        foreground=self.colors['dark_green'],
                        fieldbackground=self.colors['tan'],
                        font=('Arial', 9))
        
        style.configure("Camouflage.Treeview.Heading",
                        background=self.colors['dark_green'],
                        foreground=self.colors['text_light'],
                        font=('Arial', 9, 'bold'))
        
        # Таблица
        columns = ('ID', 'Название', 'Категория', 'Описание', 'Дата создания')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=12,
            style="Camouflage.Treeview"
        )
        
        # Настройка колонок
        column_widths = [40, 150, 120, 250, 120]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        # Scrollbar для таблицы
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Привязка события выбора
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)
        self.tree.bind('<Double-1>', self.on_double_click)
    
    def add_item(self):
        """Добавление нового элемента"""
        name = self.entries['name'].get().strip()
        
        if not name:
            messagebox.showwarning("Внимание", "Пожалуйста, введите название!")
            return
        
        category = self.entries['category'].get().strip()
        description = self.entries['description'].get().strip()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO items (name, category, description)
                VALUES (?, ?, ?)
            ''', (name, category, description))
            self.conn.commit()
            
            self.clear_form()
            self.load_data()
            messagebox.showinfo("Успех", f"Элемент '{name}' успешно добавлен!")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Элемент с таким названием уже существует!")
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {e}")
    
    def search_data(self, event=None):
        """Поиск данных в базе"""
        search_term = self.search_var.get().strip().lower()
        
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        cursor = self.conn.cursor()
        
        if search_term:
            # Поиск по всем текстовым полям
            cursor.execute('''
                SELECT id, name, category, description, date_created 
                FROM items 
                WHERE LOWER(name) LIKE ? OR LOWER(category) LIKE ? OR LOWER(description) LIKE ?
                ORDER BY name
            ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        else:
            # Если поиск пустой, показываем все записи
            cursor.execute('''
                SELECT id, name, category, description, date_created 
                FROM items 
                ORDER BY name
            ''')
        
        for row in cursor.fetchall():
            # Форматирование даты
            date_str = row[4].split(' ')[0] if row[4] else ''
            self.tree.insert('', 'end', values=(row[0], row[1], row[2], row[3], date_str))
    
    def load_data(self):
        """Загрузка всех данных в таблицу"""
        self.search_var.set("")  # Очищаем поиск
        self.search_data()
    
    def on_item_select(self, event):
        """Обработка выбора элемента в таблице"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.current_id = item['values'][0]
    
    def on_double_click(self, event):
        """Редактирование при двойном клике"""
        self.edit_item()
    
    def edit_item(self):
        """Редактирование выбранного элемента"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите элемент для редактирования!")
            return
        
        item = self.tree.item(selection[0])
        item_id = item['values'][0]
        
        self.current_id = item_id
        
        # Заполнение формы данными
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, category, description FROM items WHERE id = ?', (item_id,))
        item_data = cursor.fetchone()
        
        if item_data:
            self.clear_form()
            
            self.entries['name'].insert(0, item_data[0])
            self.entries['category'].insert(0, item_data[1] if item_data[1] else '')
            self.entries['description'].insert(0, item_data[2] if item_data[2] else '')
    
    def update_item(self):
        """Обновление элемента"""
        if not self.current_id:
            messagebox.showwarning("Внимание", "Сначала выберите элемент для редактирования!")
            return
        
        name = self.entries['name'].get().strip()
        if not name:
            messagebox.showwarning("Внимание", "Название не может быть пустым!")
            return
        
        category = self.entries['category'].get().strip()
        description = self.entries['description'].get().strip()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE items 
                SET name = ?, category = ?, description = ?
                WHERE id = ?
            ''', (name, category, description, self.current_id))
            self.conn.commit()
            
            self.clear_form()
            self.load_data()
            self.current_id = None
            messagebox.showinfo("Успех", "Элемент успешно обновлен!")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Элемент с таким названием уже существует!")
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {e}")
    
    def delete_item(self):
        """Удаление выбранного элемента"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите элемент для удаления!")
            return
        
        item = self.tree.item(selection[0])
        item_name = item['values'][1]
        item_id = item['values'][0]
        
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить '{item_name}'?"):
            try:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
                self.conn.commit()
                
                self.clear_form()
                self.load_data()
                self.current_id = None
                messagebox.showinfo("Успех", "Элемент успешно удален!")
                
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")
    
    def clear_form(self):
        """Очистка формы"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.current_id = None
    
    def __del__(self):
        """Закрытие соединения с БД"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    root = tk.Tk()
    app = CamouflageDatabase(root)
    root.mainloop()

if __name__ == "__main__":
    main()