import pandas as pd
import os
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil
from datetime import datetime

class ContactDatabase:
    def __init__(self, db_path='contacts.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_table()
    
    def create_table(self):
        """Создание таблицы контактов"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                source_file TEXT,
                date_added TIMESTAMP,
                UNIQUE(name, phone)
            )
        ''')
        self.conn.commit()
    
    def import_excel_files(self, folder_path):
        """Импорт всех Excel файлов из папки"""
        excel_extensions = ['*.xlsx', '*.xls']
        imported_count = 0
        error_files = []
        
        for ext in excel_extensions:
            for file_path in Path(folder_path).glob(ext):
                try:
                    df = pd.read_excel(file_path)
                    
                    # Определяем колонки с именем и телефоном
                    name_col = None
                    phone_col = None
                    
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(word in col_lower for word in ['имя', 'name', 'фио', 'fio']):
                            name_col = col
                        elif any(word in col_lower for word in ['телефон', 'phone', 'тел', 'номер', 'number']):
                            phone_col = col
                    
                    if name_col is None or phone_col is None:
                        # Если не найдено, берем первые две колонки
                        name_col = df.columns[0]
                        phone_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                    
                    cursor = self.conn.cursor()
                    for _, row in df.iterrows():
                        name = str(row[name_col]) if pd.notna(row[name_col]) else ''
                        phone = str(row[phone_col]) if pd.notna(row[phone_col]) else ''
                        
                        if name and phone:
                            try:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO contacts (name, phone, source_file, date_added)
                                    VALUES (?, ?, ?, ?)
                                ''', (name.strip(), phone.strip(), file_path.name, datetime.now()))
                                imported_count += cursor.rowcount
                            except:
                                pass
                    
                    self.conn.commit()
                    
                except Exception as e:
                    error_files.append((file_path.name, str(e)))
        
        return imported_count, error_files
    
    def search_contacts(self, search_term=''):
        """Поиск контактов"""
        cursor = self.conn.cursor()
        if search_term:
            query = '''
                SELECT id, name, phone, source_file, date_added
                FROM contacts
                WHERE name LIKE ? OR phone LIKE ?
                ORDER BY name
            '''
            cursor.execute(query, (f'%{search_term}%', f'%{search_term}%'))
        else:
            cursor.execute('SELECT id, name, phone, source_file, date_added FROM contacts ORDER BY name')
        
        return cursor.fetchall()
    
    def add_contact(self, name, phone, source='manual'):
        """Добавление нового контакта"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO contacts (name, phone, source_file, date_added)
                VALUES (?, ?, ?, ?)
            ''', (name, phone, source, datetime.now()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update_contact(self, contact_id, name, phone):
        """Обновление контакта"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE contacts
            SET name = ?, phone = ?
            WHERE id = ?
        ''', (name, phone, contact_id))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_contact(self, contact_id):
        """Удаление контакта"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def export_to_excel(self, filename):
        """Экспорт всех контактов в Excel"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, phone, source_file, date_added FROM contacts ORDER BY name')
        data = cursor.fetchall()
        
        df = pd.DataFrame(data, columns=['Имя', 'Телефон', 'Источник', 'Дата добавления'])
        df.to_excel(filename, index=False)
        return len(data)
    
    def get_statistics(self):
        """Получение статистики"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM contacts')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT source_file) FROM contacts WHERE source_file != "manual"')
        files_count = cursor.fetchone()[0]
        
        return total, files_count
    
    def close(self):
        """Закрытие соединения"""
        self.conn.close()

class ContactApp:
    def __init__(self, root):
        self.root = root
        self.root.title("База данных контактов")
        self.root.geometry("1000x600")
        
        self.db = ContactDatabase()
        
        # Создание интерфейса
        self.create_widgets()
        self.refresh_table()
    
    def create_widgets(self):
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill='x')
        
        tk.Button(top_frame, text="Импорт папки с Excel", command=self.import_folder,
                 bg='lightgreen', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(top_frame, text="Добавить контакт", command=self.add_contact,
                 bg='lightblue', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(top_frame, text="Экспорт всех контактов", command=self.export_all,
                 bg='lightyellow', font=('Arial', 10)).pack(side='left', padx=5)
        
        tk.Button(top_frame, text="Статистика", command=self.show_stats,
                 bg='lightgray', font=('Arial', 10)).pack(side='left', padx=5)
        
        # Панель поиска
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(search_frame, text="Поиск:", font=('Arial', 10)).pack(side='left', padx=5)
        self.search_entry = tk.Entry(search_frame, font=('Arial', 10), width=40)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.refresh_table())
        
        tk.Button(search_frame, text="Очистить", command=self.clear_search,
                 font=('Arial', 10)).pack(side='left', padx=5)
        
        # Таблица с контактами
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Создание таблицы
        columns = ('id', 'name', 'phone', 'source', 'date')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Имя')
        self.tree.heading('phone', text='Телефон')
        self.tree.heading('source', text='Источник')
        self.tree.heading('date', text='Дата добавления')
        
        self.tree.column('id', width=50)
        self.tree.column('name', width=250)
        self.tree.column('phone', width=150)
        self.tree.column('source', width=200)
        self.tree.column('date', width=150)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Редактировать", command=self.edit_contact)
        self.context_menu.add_command(label="Удалить", command=self.delete_contact)
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        # Панель статуса
        self.status_bar = tk.Label(self.root, text="Готов", relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')
    
    def refresh_table(self):
        """Обновление таблицы"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Поиск контактов
        search_term = self.search_entry.get()
        contacts = self.db.search_contacts(search_term)
        
        # Заполнение таблицы
        for contact in contacts:
            self.tree.insert('', 'end', values=contact)
        
        self.status_bar.config(text=f"Найдено контактов: {len(contacts)}")
    
    def import_folder(self):
        """Импорт папки с файлами"""
        folder = filedialog.askdirectory(title="Выберите папку с Excel файлами")
        if folder:
            count, errors = self.db.import_excel_files(folder)
            messagebox.showinfo("Импорт завершен", 
                               f"Импортировано новых контактов: {count}\n"
                               f"Ошибок в файлах: {len(errors)}")
            self.refresh_table()
    
    def add_contact(self):
        """Диалог добавления контакта"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление контакта")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        tk.Label(dialog, text="Имя:", font=('Arial', 10)).pack(pady=10)
        name_entry = tk.Entry(dialog, font=('Arial', 10), width=40)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Телефон:", font=('Arial', 10)).pack(pady=10)
        phone_entry = tk.Entry(dialog, font=('Arial', 10), width=40)
        phone_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            if name and phone:
                if self.db.add_contact(name, phone):
                    messagebox.showinfo("Успех", "Контакт добавлен")
                    dialog.destroy()
                    self.refresh_table()
                else:
                    messagebox.showerror("Ошибка", "Такой контакт уже существует")
            else:
                messagebox.showwarning("Предупреждение", "Заполните все поля")
        
        tk.Button(dialog, text="Сохранить", command=save, bg='lightgreen', 
                 font=('Arial', 10)).pack(pady=20)
    
    def edit_contact(self):
        """Редактирование контакта"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите контакт для редактирования")
            return
        
        contact = self.tree.item(selected[0])['values']
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование контакта")
        dialog.geometry("400x200")
        dialog.grab_set()
        
        tk.Label(dialog, text="Имя:", font=('Arial', 10)).pack(pady=10)
        name_entry = tk.Entry(dialog, font=('Arial', 10), width=40)
        name_entry.insert(0, contact[1])
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Телефон:", font=('Arial', 10)).pack(pady=10)
        phone_entry = tk.Entry(dialog, font=('Arial', 10), width=40)
        phone_entry.insert(0, contact[2])
        phone_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            if name and phone:
                self.db.update_contact(contact[0], name, phone)
                messagebox.showinfo("Успех", "Контакт обновлен")
                dialog.destroy()
                self.refresh_table()
            else:
                messagebox.showwarning("Предупреждение", "Заполните все поля")
        
        tk.Button(dialog, text="Сохранить", command=save, bg='lightgreen', 
                 font=('Arial', 10)).pack(pady=20)
    
    def delete_contact(self):
        """Удаление контакта"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите контакт для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранный контакт?"):
            contact = self.tree.item(selected[0])['values']
            self.db.delete_contact(contact[0])
            self.refresh_table()
            messagebox.showinfo("Успех", "Контакт удален")
    
    def export_all(self):
        """Экспорт всех контактов"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Сохранить как"
        )
        if filename:
            count = self.db.export_to_excel(filename)
            messagebox.showinfo("Экспорт завершен", f"Экспортировано контактов: {count}")
    
    def show_stats(self):
        """Показ статистики"""
        total, files = self.db.get_statistics()
        messagebox.showinfo("Статистика", 
                           f"Всего контактов в базе: {total}\n"
                           f"Импортировано из файлов: {files}\n"
                           f"База данных: {self.db.db_path}")
    
    def clear_search(self):
        """Очистка поиска"""
        self.search_entry.delete(0, tk.END)
        self.refresh_table()
    
    def show_context_menu(self, event):
        """Показ контекстного меню"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def on_closing(self):
        """Закрытие приложения"""
        self.db.close()
        self.root.destroy()

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = ContactApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()