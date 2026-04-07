import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import datetime
import os

class TachographDB:
    def __init__(self, root):
        self.root = root
        self.root.title("Учёт тахографов и зарплата")
        self.root.geometry("1300x700")
        
        # Создаём базу
        self.init_db()
        
        # Создаём интерфейс
        self.create_notebook()
        self.create_tachograph_tab()
        self.create_salary_tab()
        
        # Загружаем данные
        self.load_tachographs()
        self.load_works()
        self.calc_salary()
    
    def init_db(self):
        """Создаёт базу данных если её нет"""
        self.conn = sqlite3.connect('tachograph.db')
        self.cursor = self.conn.cursor()
        
        # Таблица тахографов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tachographs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                vin TEXT,
                license_plate TEXT,
                skzi TEXT,
                serial_number TEXT,
                factory_number TEXT,
                notes TEXT
            )
        ''')
        
        # Таблица работ
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                monitoring INTEGER DEFAULT 0,
                cards INTEGER DEFAULT 0,
                photos INTEGER DEFAULT 0,
                nkm INTEGER DEFAULT 0,
                activation INTEGER DEFAULT 0,
                calibration INTEGER DEFAULT 0,
                verification INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')
        
        self.conn.commit()
    
    def create_notebook(self):
        """Создаёт вкладки"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tab_tachographs = ttk.Frame(self.notebook)
        self.tab_salary = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_tachographs, text="📟 Установка тахографов")
        self.notebook.add(self.tab_salary, text="💰 Зарплата и работы")
    
    # ==================== ВКЛАДКА ТАХОГРАФОВ ====================
    
    def create_tachograph_tab(self):
        # Форма ввода
        form_frame = ttk.LabelFrame(self.tab_tachographs, text="Добавить установку", padding=10)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        row = 0
        ttk.Label(form_frame, text="Дата установки:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.t_date = ttk.Entry(form_frame, width=15)
        self.t_date.grid(row=row, column=1, padx=5, pady=5)
        self.t_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(form_frame, text="VIN номер:").grid(row=row, column=2, sticky='w', padx=5, pady=5)
        self.t_vin = ttk.Entry(form_frame, width=25)
        self.t_vin.grid(row=row, column=3, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Гос номер:").grid(row=row, column=4, sticky='w', padx=5, pady=5)
        self.t_plate = ttk.Entry(form_frame, width=15)
        self.t_plate.grid(row=row, column=5, padx=5, pady=5)
        
        row = 1
        ttk.Label(form_frame, text="Номер СКЗИ:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.t_skzi = ttk.Entry(form_frame, width=25)
        self.t_skzi.grid(row=row, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Сер. номер тахографа:").grid(row=row, column=2, sticky='w', padx=5, pady=5)
        self.t_serial = ttk.Entry(form_frame, width=25)
        self.t_serial.grid(row=row, column=3, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Зав. номер:").grid(row=row, column=4, sticky='w', padx=5, pady=5)
        self.t_factory = ttk.Entry(form_frame, width=15)
        self.t_factory.grid(row=row, column=5, padx=5, pady=5)
        
        row = 2
        ttk.Label(form_frame, text="Примечания:").grid(row=row, column=0, sticky='w', padx=5, pady=5)
        self.t_notes = ttk.Entry(form_frame, width=80)
        self.t_notes.grid(row=row, column=1, columnspan=4, padx=5, pady=5, sticky='ew')
        
        ttk.Button(form_frame, text="➕ Добавить", command=self.add_tachograph).grid(row=row, column=5, padx=5, pady=5)
        
        # Таблица
        table_frame = ttk.Frame(self.tab_tachographs)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('id', 'date', 'vin', 'plate', 'skzi', 'serial', 'factory', 'notes')
        self.tree_tachographs = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        self.tree_tachographs.heading('id', text='ID')
        self.tree_tachographs.heading('date', text='Дата')
        self.tree_tachographs.heading('vin', text='VIN номер')
        self.tree_tachographs.heading('plate', text='Гос номер')
        self.tree_tachographs.heading('skzi', text='СКЗИ')
        self.tree_tachographs.heading('serial', text='Сер. номер')
        self.tree_tachographs.heading('factory', text='Зав. номер')
        self.tree_tachographs.heading('notes', text='Примечания')
        
        self.tree_tachographs.column('id', width=40)
        self.tree_tachographs.column('date', width=100)
        self.tree_tachographs.column('vin', width=150)
        self.tree_tachographs.column('plate', width=80)
        self.tree_tachographs.column('skzi', width=150)
        self.tree_tachographs.column('serial', width=150)
        self.tree_tachographs.column('factory', width=120)
        self.tree_tachographs.column('notes', width=200)
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree_tachographs.yview)
        self.tree_tachographs.configure(yscrollcommand=scrollbar.set)
        
        self.tree_tachographs.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Кнопка удаления
        ttk.Button(self.tab_tachographs, text="🗑️ Удалить выбранное", command=self.delete_tachograph).pack(pady=5)
    
    def add_tachograph(self):
        if not self.t_vin.get() or not self.t_plate.get():
            messagebox.showwarning("Ошибка", "Заполните VIN и гос номер")
            return
        
        self.cursor.execute('''
            INSERT INTO tachographs (date, vin, license_plate, skzi, serial_number, factory_number, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.t_date.get(),
            self.t_vin.get(),
            self.t_plate.get(),
            self.t_skzi.get(),
            self.t_serial.get(),
            self.t_factory.get(),
            self.t_notes.get()
        ))
        self.conn.commit()
        
        # Очищаем форму
        self.t_vin.delete(0, tk.END)
        self.t_plate.delete(0, tk.END)
        self.t_skzi.delete(0, tk.END)
        self.t_serial.delete(0, tk.END)
        self.t_factory.delete(0, tk.END)
        self.t_notes.delete(0, tk.END)
        
        self.load_tachographs()
        messagebox.showinfo("Успех", "Запись добавлена")
    
    def load_tachographs(self):
        for row in self.tree_tachographs.get_children():
            self.tree_tachographs.delete(row)
        
        self.cursor.execute('SELECT id, date, vin, license_plate, skzi, serial_number, factory_number, notes FROM tachographs ORDER BY date DESC')
        for row in self.cursor.fetchall():
            self.tree_tachographs.insert('', 'end', values=row)
    
    def delete_tachograph(self):
        selected = self.tree_tachographs.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            item = self.tree_tachographs.item(selected[0])
            id = item['values'][0]
            self.cursor.execute('DELETE FROM tachographs WHERE id = ?', (id,))
            self.conn.commit()
            self.load_tachographs()
    
    # ==================== ВКЛАДКА ЗАРПЛАТЫ ====================
    
    def create_salary_tab(self):
        # Информационная панель
        info_frame = ttk.LabelFrame(self.tab_salary, text="💰 Итого за период", padding=10)
        info_frame.pack(fill='x', padx=10, pady=10)
        
        self.total_label = ttk.Label(info_frame, text="Общая сумма: 0 ₽", font=('Arial', 16, 'bold'))
        self.total_label.pack()
        
        # Форма ввода работ
        form_frame = ttk.LabelFrame(self.tab_salary, text="Добавить работы", padding=10)
        form_frame.pack(fill='x', padx=10, pady=10)
        
        row = 0
        ttk.Label(form_frame, text="Дата:").grid(row=row, column=0, padx=5, pady=5)
        self.w_date = ttk.Entry(form_frame, width=12)
        self.w_date.grid(row=row, column=1, padx=5, pady=5)
        self.w_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(form_frame, text="Объекты мониторинга:").grid(row=row, column=2, padx=5, pady=5)
        self.w_monitoring = ttk.Entry(form_frame, width=8)
        self.w_monitoring.grid(row=row, column=3, padx=5, pady=5)
        self.w_monitoring.insert(0, "0")
        
        ttk.Label(form_frame, text="Карты тахографа:").grid(row=row, column=4, padx=5, pady=5)
        self.w_cards = ttk.Entry(form_frame, width=8)
        self.w_cards.grid(row=row, column=5, padx=5, pady=5)
        self.w_cards.insert(0, "0")
        
        row = 1
        ttk.Label(form_frame, text="Фото:").grid(row=row, column=0, padx=5, pady=5)
        self.w_photos = ttk.Entry(form_frame, width=8)
        self.w_photos.grid(row=row, column=1, padx=5, pady=5)
        self.w_photos.insert(0, "0")
        
        ttk.Label(form_frame, text="Замена блока НКМ:").grid(row=row, column=2, padx=5, pady=5)
        self.w_nkm = ttk.Entry(form_frame, width=8)
        self.w_nkm.grid(row=row, column=3, padx=5, pady=5)
        self.w_nkm.insert(0, "0")
        
        ttk.Label(form_frame, text="Активация:").grid(row=row, column=4, padx=5, pady=5)
        self.w_activation = ttk.Entry(form_frame, width=8)
        self.w_activation.grid(row=row, column=5, padx=5, pady=5)
        self.w_activation.insert(0, "0")
        
        row = 2
        ttk.Label(form_frame, text="Калибровка:").grid(row=row, column=0, padx=5, pady=5)
        self.w_calibration = ttk.Entry(form_frame, width=8)
        self.w_calibration.grid(row=row, column=1, padx=5, pady=5)
        self.w_calibration.insert(0, "0")
        
        ttk.Label(form_frame, text="Поверка:").grid(row=row, column=2, padx=5, pady=5)
        self.w_verification = ttk.Entry(form_frame, width=8)
        self.w_verification.grid(row=row, column=3, padx=5, pady=5)
        self.w_verification.insert(0, "0")
        
        ttk.Label(form_frame, text="Примечания:").grid(row=row, column=4, padx=5, pady=5)
        self.w_notes = ttk.Entry(form_frame, width=30)
        self.w_notes.grid(row=row, column=5, padx=5, pady=5)
        
        row = 3
        ttk.Button(form_frame, text="➕ Добавить работы", command=self.add_work).grid(row=row, column=0, columnspan=3, pady=10)
        ttk.Button(form_frame, text="🔄 Пересчитать", command=self.calc_salary).grid(row=row, column=3, columnspan=3, pady=10)
        
        # Таблица работ
        table_frame = ttk.Frame(self.tab_salary)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('id', 'date', 'monitoring', 'cards', 'photos', 'nkm', 'activation', 'calibration', 'verification', 'total', 'notes')
        self.tree_works = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        self.tree_works.heading('id', text='ID')
        self.tree_works.heading('date', text='Дата')
        self.tree_works.heading('monitoring', text='Мониторинг')
        self.tree_works.heading('cards', text='Карты')
        self.tree_works.heading('photos', text='Фото')
        self.tree_works.heading('nkm', text='НКМ')
        self.tree_works.heading('activation', text='Активация')
        self.tree_works.heading('calibration', text='Калибровка')
        self.tree_works.heading('verification', text='Поверка')
        self.tree_works.heading('total', text='Сумма, ₽')
        self.tree_works.heading('notes', text='Примечания')
        
        self.tree_works.column('id', width=40)
        self.tree_works.column('date', width=90)
        self.tree_works.column('monitoring', width=80)
        self.tree_works.column('cards', width=60)
        self.tree_works.column('photos', width=60)
        self.tree_works.column('nkm', width=60)
        self.tree_works.column('activation', width=70)
        self.tree_works.column('calibration', width=70)
        self.tree_works.column('verification', width=70)
        self.tree_works.column('total', width=100)
        self.tree_works.column('notes', width=200)
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree_works.yview)
        self.tree_works.configure(yscrollcommand=scrollbar.set)
        
        self.tree_works.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        ttk.Button(self.tab_salary, text="🗑️ Удалить выбранное", command=self.delete_work).pack(pady=5)
    
    def add_work(self):
        prices = {
            'monitoring': 500,
            'cards': 300,
            'photos': 100,
            'nkm': 2000,
            'activation': 1500,
            'calibration': 2500,
            'verification': 3000
        }
        
        self.cursor.execute('''
            INSERT INTO works (date, monitoring, cards, photos, nkm, activation, calibration, verification, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.w_date.get(),
            int(self.w_monitoring.get() or 0),
            int(self.w_cards.get() or 0),
            int(self.w_photos.get() or 0),
            int(self.w_nkm.get() or 0),
            int(self.w_activation.get() or 0),
            int(self.w_calibration.get() or 0),
            int(self.w_verification.get() or 0),
            self.w_notes.get()
        ))
        self.conn.commit()
        
        # Очищаем
        self.w_monitoring.delete(0, tk.END)
        self.w_monitoring.insert(0, "0")
        self.w_cards.delete(0, tk.END)
        self.w_cards.insert(0, "0")
        self.w_photos.delete(0, tk.END)
        self.w_photos.insert(0, "0")
        self.w_nkm.delete(0, tk.END)
        self.w_nkm.insert(0, "0")
        self.w_activation.delete(0, tk.END)
        self.w_activation.insert(0, "0")
        self.w_calibration.delete(0, tk.END)
        self.w_calibration.insert(0, "0")
        self.w_verification.delete(0, tk.END)
        self.w_verification.insert(0, "0")
        self.w_notes.delete(0, tk.END)
        
        self.load_works()
        self.calc_salary()
        messagebox.showinfo("Успех", "Работы добавлены")
    
    def load_works(self):
        for row in self.tree_works.get_children():
            self.tree_works.delete(row)
        
        self.cursor.execute('SELECT id, date, monitoring, cards, photos, nkm, activation, calibration, verification, notes FROM works ORDER BY date DESC')
        
        prices = {'monitoring': 500, 'cards': 300, 'photos': 100, 'nkm': 2000, 'activation': 1500, 'calibration': 2500, 'verification': 3000}
        
        for row in self.cursor.fetchall():
            total = (row[2] * prices['monitoring'] + 
                    row[3] * prices['cards'] + 
                    row[4] * prices['photos'] + 
                    row[5] * prices['nkm'] + 
                    row[6] * prices['activation'] + 
                    row[7] * prices['calibration'] + 
                    row[8] * prices['verification'])
            values = list(row[:9]) + [total] + [row[9]]
            self.tree_works.insert('', 'end', values=values)
    
    def calc_salary(self):
        self.cursor.execute('SELECT monitoring, cards, photos, nkm, activation, calibration, verification FROM works')
        prices = {'monitoring': 500, 'cards': 300, 'photos': 100, 'nkm': 2000, 'activation': 1500, 'calibration': 2500, 'verification': 3000}
        
        total = 0
        for row in self.cursor.fetchall():
            total += (row[0] * prices['monitoring'] + 
                     row[1] * prices['cards'] + 
                     row[2] * prices['photos'] + 
                     row[3] * prices['nkm'] + 
                     row[4] * prices['activation'] + 
                     row[5] * prices['calibration'] + 
                     row[6] * prices['verification'])
        
        self.total_label.config(text=f"💰 Общая зарплата: {total:,.0f} ₽")
    
    def delete_work(self):
        selected = self.tree_works.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную запись?"):
            item = self.tree_works.item(selected[0])
            id = item['values'][0]
            self.cursor.execute('DELETE FROM works WHERE id = ?', (id,))
            self.conn.commit()
            self.load_works()
            self.calc_salary()

if __name__ == "__main__":
    root = tk.Tk()
    app = TachographDB(root)
    root.mainloop()