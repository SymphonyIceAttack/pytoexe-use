import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from fpdf import FPDF
from datetime import datetime
import os
import sys
import hashlib


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def setup_styles():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background='#2c3e50')
    style.configure('TLabel', background='#2c3e50', foreground='#ecf0f1', font=('Segoe UI', 10))
    style.configure('TLabelframe', background='#2c3e50', foreground='#ecf0f1', font=('Segoe UI', 10, 'bold'))
    style.configure('TLabelframe.Label', background='#2c3e50', foreground='#ecf0f1', font=('Segoe UI', 10, 'bold'))
    style.configure('Treeview', background='#ecf0f1', foreground='#2c3e50', fieldbackground='#ecf0f1',
                    font=('Segoe UI', 9))
    style.configure('Treeview.Heading', background='#bdc3c7', foreground='#2c3e50', font=('Segoe UI', 9, 'bold'))
    style.map('Treeview', background=[('selected', '#3498db')])


def init_db():
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            patronymic TEXT,
            position TEXT NOT NULL,
            salary REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def add_employee_to_db(emp_data):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO employees (last_name, first_name, patronymic, position, salary)
        VALUES (?, ?, ?, ?, ?)
    ''', emp_data)
    conn.commit()
    conn.close()


def get_all_employees():
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, last_name, first_name, patronymic, position, salary FROM employees ORDER BY last_name')
    employees = cursor.fetchall()
    conn.close()
    return employees


def update_employee_in_db(emp_id, emp_data):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE employees
        SET last_name=?, first_name=?, patronymic=?, position=?, salary=?
        WHERE id=?
    ''', (*emp_data, emp_id))
    conn.commit()
    conn.close()


def delete_employee_from_db(emp_id):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM employees WHERE id=?', (emp_id,))
    conn.commit()
    conn.close()


def search_employees(search_term):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    like_term = f'%{search_term}%'
    cursor.execute('''
        SELECT id, last_name, first_name, patronymic, position, salary
        FROM employees
        WHERE last_name LIKE ? OR position LIKE ?
        ORDER BY last_name
    ''', (like_term, like_term))
    results = cursor.fetchall()
    conn.close()
    return results


def filter_employees_by_salary(min_salary, max_salary):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, last_name, first_name, patronymic, position, salary
        FROM employees
        WHERE salary BETWEEN ? AND ?
        ORDER BY last_name
    ''', (min_salary, max_salary))
    results = cursor.fetchall()
    conn.close()
    return results


def get_employee_by_id(emp_id):
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_name, first_name, patronymic, position, salary FROM employees WHERE id=?', (emp_id,))
    employee = cursor.fetchone()
    conn.close()
    return employee


def create_pdf_with_font():
    font_filename = 'TimesNewRomanPSMT.ttf'
    font_path = resource_path(font_filename)
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(font_path):
        pdf.add_font('TimesNewRoman', '', font_path, uni=True)
        pdf.set_font('TimesNewRoman', size=12)
    else:
        pdf.set_font('Helvetica', size=12)
        pdf.set_text_color(255, 0, 0)
        pdf.cell(200, 10, 'Шрифт TimesNewRomanPSMT.ttf не найден! Кириллица может отображаться некорректно.', ln=True,
                 align='C')
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
    return pdf


def generate_salary_certificate(employee_data):
    last_name, first_name, patronymic, position, salary = employee_data
    full_name = f'{last_name} {first_name} {patronymic}'.strip()
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{reports_dir}/Справка_о_зарплате_{last_name}_{first_name}_{timestamp}.pdf'
    pdf = create_pdf_with_font()
    pdf.set_font_size(16)
    pdf.cell(200, 10, 'СПРАВКА О ЗАРАБОТНОЙ ПЛАТЕ', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font_size(12)
    pdf.cell(200, 10, f'Фамилия, Имя, Отчество: {full_name}', ln=True)
    pdf.cell(200, 10, f'Должность: {position}', ln=True)
    pdf.cell(200, 10, f'Месячный оклад: {salary:.2f} руб.', ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, f'Дата выдачи: {datetime.now().strftime("%d.%m.%Y")}', ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, 'Главный бухгалтер __________________', ln=True)
    pdf.output(filename)
    messagebox.showinfo('Успех', f'Справка о зарплате сохранена в папку "{reports_dir}"')


def generate_bank_income_certificate(employee_data):
    last_name, first_name, patronymic, position, salary = employee_data
    full_name = f'{last_name} {first_name} {patronymic}'.strip()
    months_count = 6
    total_income = salary * months_count
    avg_income = salary
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{reports_dir}/Справка_для_банка_{last_name}_{first_name}_{timestamp}.pdf'
    pdf = create_pdf_with_font()
    pdf.set_font_size(16)
    pdf.cell(200, 10, 'СПРАВКА О ДОХОДАХ ДЛЯ БАНКА', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font_size(12)
    pdf.cell(200, 10, f'ФИО сотрудника: {full_name}', ln=True)
    pdf.cell(200, 10, f'Должность: {position}', ln=True)
    pdf.cell(200, 10, f'Среднемесячный доход: {avg_income:.2f} руб.', ln=True)
    pdf.cell(200, 10, f'Общий доход за последние {months_count} месяцев: {total_income:.2f} руб.', ln=True)
    pdf.ln(10)
    pdf.cell(200, 10, f'Дата выдачи: {datetime.now().strftime("%d.%m.%Y")}', ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, 'Главный бухгалтер __________________', ln=True)
    pdf.output(filename)
    messagebox.showinfo('Успех', f'Справка для банка сохранена в папку "{reports_dir}"')


def generate_character_reference(employee_data):
    last_name, first_name, patronymic, position, salary = employee_data
    full_name = f'{last_name} {first_name} {patronymic}'.strip()
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{reports_dir}/Характеристика_{last_name}_{first_name}_{timestamp}.pdf'
    pdf = create_pdf_with_font()
    pdf.set_font_size(16)
    pdf.cell(200, 10, 'ХАРАКТЕРИСТИКА (РЕКОМЕНДАТЕЛЬНОЕ ПИСЬМО)', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font_size(12)
    pdf.cell(200, 10, f'Сотрудник: {full_name}', ln=True)
    pdf.cell(200, 10, f'Должность: {position}', ln=True)
    pdf.cell(200, 10, f'Стаж работы в компании: 3 года', ln=True)
    pdf.ln(5)
    text = f"""За время работы в компании зарекомендовал(а) себя как высококвалифицированный(ая) специалист(ка). 

К профессиональным качествам можно отнести: глубокое знание бухгалтерского учёта, налогового законодательства, уверенное владение специализированными программами, внимательность к деталям, аналитический склад ума.

Личные качества: ответственность, пунктуальность, честность, коммуникабельность, нацеленность на результат.

Рекомендую {full_name} как ценного сотрудника."""
    pdf.multi_cell(200, 10, text)
    pdf.ln(10)
    pdf.cell(200, 10, f'Дата выдачи: {datetime.now().strftime("%d.%m.%Y")}', ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, 'Руководитель организации __________________', ln=True)
    pdf.output(filename)
    messagebox.showinfo('Успех', f'Характеристика сохранена в папку "{reports_dir}"')


def show_document_selection(employee_data):
    selection_window = tk.Toplevel()
    selection_window.title('Выбор документа')
    selection_window.geometry('400x250')
    selection_window.resizable(False, False)
    selection_window.configure(bg='#2c3e50')
    tk.Label(selection_window, text='Выберите тип документа для формирования:', bg='#2c3e50', fg='#ecf0f1',
             font=('Segoe UI', 12)).pack(pady=20)

    def on_select(doc_type):
        selection_window.destroy()
        if doc_type == 'salary':
            generate_salary_certificate(employee_data)
        elif doc_type == 'bank':
            generate_bank_income_certificate(employee_data)
        elif doc_type == 'character':
            generate_character_reference(employee_data)

    btn_frame = tk.Frame(selection_window, bg='#2c3e50')
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text='Справка о зарплате', command=lambda: on_select('salary'), bg='#3498db', fg='white',
              font=('Segoe UI', 10), width=25, padx=5).pack(pady=5)
    tk.Button(btn_frame, text='Справка для банка (о доходах)', command=lambda: on_select('bank'), bg='#2ecc71',
              fg='white', font=('Segoe UI', 10), width=25, padx=5).pack(pady=5)
    tk.Button(btn_frame, text='Характеристика (рекомендательное письмо)', command=lambda: on_select('character'),
              bg='#e67e22', fg='white', font=('Segoe UI', 10), width=25, padx=5).pack(pady=5)


class SalaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Автоматизация отдела бухгалтерии')
        self.root.geometry('1000x600')
        self.root.configure(bg='#2c3e50')
        self.current_employee_id = None
        setup_styles()
        init_db()
        self.create_widgets()
        self.refresh_table()

    def create_widgets(self):
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill='both', expand=True, padx=15, pady=15)
        input_frame = tk.LabelFrame(main_container, text='Данные сотрудника', font=('Segoe UI', 11, 'bold'),
                                    bg='#34495e', fg='#ecf0f1', padx=10, pady=10)
        input_frame.pack(fill='x', pady=(0, 10))
        tk.Label(input_frame, text='Фамилия:', bg='#34495e', fg='#ecf0f1', font=('Segoe UI', 10)).grid(row=0, column=0,
                                                                                                       sticky='w',
                                                                                                       padx=5, pady=5)
        self.last_name_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=20, bg='#ecf0f1')
        self.last_name_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(input_frame, text='Имя:', bg='#34495e', fg='#ecf0f1', font=('Segoe UI', 10)).grid(row=0, column=2,
                                                                                                   sticky='w', padx=5,
                                                                                                   pady=5)
        self.first_name_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=20, bg='#ecf0f1')
        self.first_name_entry.grid(row=0, column=3, padx=5, pady=5)
        tk.Label(input_frame, text='Отчество:', bg='#34495e', fg='#ecf0f1', font=('Segoe UI', 10)).grid(row=0, column=4,
                                                                                                        sticky='w',
                                                                                                        padx=5, pady=5)
        self.patronymic_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=20, bg='#ecf0f1')
        self.patronymic_entry.grid(row=0, column=5, padx=5, pady=5)
        tk.Label(input_frame, text='Должность:', bg='#34495e', fg='#ecf0f1', font=('Segoe UI', 10)).grid(row=1,
                                                                                                         column=0,
                                                                                                         sticky='w',
                                                                                                         padx=5, pady=5)
        self.position_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=50, bg='#ecf0f1')
        self.position_entry.grid(row=1, column=1, columnspan=5, sticky='ew', padx=5, pady=5)
        tk.Label(input_frame, text='Оклад (руб.):', bg='#34495e', fg='#ecf0f1', font=('Segoe UI', 10)).grid(row=2,
                                                                                                            column=0,
                                                                                                            sticky='w',
                                                                                                            padx=5,
                                                                                                            pady=5)
        self.salary_entry = tk.Entry(input_frame, font=('Segoe UI', 10), width=15, bg='#ecf0f1')
        self.salary_entry.grid(row=2, column=1, padx=5, pady=5)
        btn_frame = tk.Frame(input_frame, bg='#34495e')
        btn_frame.grid(row=3, column=0, columnspan=6, pady=10)
        self.add_btn = tk.Button(btn_frame, text='Добавить', command=self.add_employee, bg='#2ecc71', fg='white',
                                 font=('Segoe UI', 9, 'bold'), padx=10, pady=4)
        self.add_btn.pack(side='left', padx=5)
        self.edit_btn = tk.Button(btn_frame, text='Изменить', command=self.update_employee, bg='#f39c12', fg='white',
                                  font=('Segoe UI', 9, 'bold'), padx=10, pady=4)
        self.edit_btn.pack(side='left', padx=5)
        self.clear_btn = tk.Button(btn_frame, text='Очистить', command=self.clear_input_fields, bg='#95a5a6',
                                   fg='white', font=('Segoe UI', 9, 'bold'), padx=10, pady=4)
        self.clear_btn.pack(side='left', padx=5)
        search_frame = tk.LabelFrame(main_container, text='Поиск и фильтрация', font=('Segoe UI', 11, 'bold'),
                                     bg='#34495e', fg='#ecf0f1', padx=10, pady=10)
        search_frame.pack(fill='x', pady=(0, 10))
        tk.Label(search_frame, text='Поиск (ФИО/Должность):', bg='#34495e', fg='#ecf0f1').grid(row=0, column=0,
                                                                                               sticky='w', padx=5)
        self.search_entry = tk.Entry(search_frame, font=('Segoe UI', 10), width=30, bg='#ecf0f1')
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_btn = ttk.Button(search_frame, text='Найти', command=self.search_employees)
        self.search_btn.grid(row=0, column=2, padx=5)
        self.reset_btn = ttk.Button(search_frame, text='Сброс', command=self.refresh_table)
        self.reset_btn.grid(row=0, column=3, padx=5)
        tk.Label(search_frame, text='Оклад от:', bg='#34495e', fg='#ecf0f1').grid(row=0, column=4, sticky='w', padx=5)
        self.min_salary_entry = tk.Entry(search_frame, width=10, bg='#ecf0f1')
        self.min_salary_entry.grid(row=0, column=5, padx=5)
        tk.Label(search_frame, text='до:', bg='#34495e', fg='#ecf0f1').grid(row=0, column=6, sticky='w', padx=5)
        self.max_salary_entry = tk.Entry(search_frame, width=10, bg='#ecf0f1')
        self.max_salary_entry.grid(row=0, column=7, padx=5)
        self.filter_btn = ttk.Button(search_frame, text='Применить фильтр', command=self.filter_employees)
        self.filter_btn.grid(row=0, column=8, padx=5)
        table_frame = tk.LabelFrame(main_container, text='Список сотрудников', font=('Segoe UI', 11, 'bold'),
                                    bg='#34495e', fg='#ecf0f1', padx=10, pady=10)
        table_frame.pack(fill='both', expand=True, pady=(0, 10))
        columns = ('id', 'last_name', 'first_name', 'patronymic', 'position', 'salary')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('last_name', text='Фамилия')
        self.tree.heading('first_name', text='Имя')
        self.tree.heading('patronymic', text='Отчество')
        self.tree.heading('position', text='Должность')
        self.tree.heading('salary', text='Оклад (руб.)')
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('last_name', width=120)
        self.tree.column('first_name', width=100)
        self.tree.column('patronymic', width=100)
        self.tree.column('position', width=250)
        self.tree.column('salary', width=100, anchor='e')
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        bottom_frame = tk.Frame(main_container, bg='#2c3e50')
        bottom_frame.pack(fill='x')
        self.delete_btn = tk.Button(bottom_frame, text='Удалить', command=self.delete_employee, bg='#e74c3c',
                                    fg='white', font=('Segoe UI', 9, 'bold'), padx=15, pady=5)
        self.delete_btn.pack(side='left', padx=5)
        self.pdf_btn = tk.Button(bottom_frame, text='Сформировать справку', command=self.generate_document_for_selected,
                                 bg='#3498db', fg='white', font=('Segoe UI', 9, 'bold'), padx=15, pady=5)
        self.pdf_btn.pack(side='left', padx=5)
        self.status_label = tk.Label(main_container, text='Готово', bg='#2c3e50', fg='#bdc3c7', anchor='w')
        self.status_label.pack(fill='x', pady=(5, 0))

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for emp in get_all_employees():
            self.tree.insert('', 'end', values=emp)
        self.clear_input_fields()
        self.status_label.config(text=f'Загружено {len(get_all_employees())} записей')

    def add_employee(self):
        data = self.get_input_data()
        if data:
            add_employee_to_db(data)
            messagebox.showinfo('Успех', 'Сотрудник добавлен')
            self.refresh_table()

    def update_employee(self):
        if self.current_employee_id is None:
            messagebox.showwarning('Предупреждение', 'Выберите сотрудника')
            return
        data = self.get_input_data()
        if data:
            update_employee_in_db(self.current_employee_id, data)
            messagebox.showinfo('Успех', 'Данные обновлены')
            self.refresh_table()

    def delete_employee(self):
        if self.current_employee_id is None:
            messagebox.showwarning('Предупреждение', 'Выберите сотрудника')
            return
        if messagebox.askyesno('Подтверждение', 'Удалить выбранного сотрудника?'):
            delete_employee_from_db(self.current_employee_id)
            self.refresh_table()

    def search_employees(self):
        term = self.search_entry.get().strip()
        if not term:
            self.refresh_table()
            return
        results = search_employees(term)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for emp in results:
            self.tree.insert('', 'end', values=emp)
        self.status_label.config(text=f'Найдено {len(results)} записей')

    def filter_employees(self):
        try:
            min_sal = float(self.min_salary_entry.get()) if self.min_salary_entry.get() else 0
            max_sal = float(self.max_salary_entry.get()) if self.max_salary_entry.get() else float('inf')
        except ValueError:
            messagebox.showerror('Ошибка', 'Введите корректные числа')
            return
        results = filter_employees_by_salary(min_sal, max_sal)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for emp in results:
            self.tree.insert('', 'end', values=emp)
        self.status_label.config(text=f'Отфильтровано {len(results)} сотрудников')

    def generate_document_for_selected(self):
        if self.current_employee_id is None:
            messagebox.showwarning('Предупреждение', 'Выберите сотрудника')
            return
        emp = get_employee_by_id(self.current_employee_id)
        if emp:
            show_document_selection(emp)
        else:
            messagebox.showerror('Ошибка', 'Сотрудник не найден')

    def get_input_data(self):
        last = self.last_name_entry.get().strip()
        first = self.first_name_entry.get().strip()
        patron = self.patronymic_entry.get().strip()
        pos = self.position_entry.get().strip()
        salary_str = self.salary_entry.get().strip()
        if not last or not first or not pos or not salary_str:
            messagebox.showerror('Ошибка', 'Заполните все обязательные поля')
            return None
        try:
            salary = float(salary_str)
            if salary <= 0:
                raise ValueError
        except:
            messagebox.showerror('Ошибка', 'Оклад должен быть положительным числом')
            return None
        return (last, first, patron, pos, salary)

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        if not values:
            return
        self.current_employee_id = values[0]
        self.last_name_entry.delete(0, tk.END)
        self.last_name_entry.insert(0, values[1])
        self.first_name_entry.delete(0, tk.END)
        self.first_name_entry.insert(0, values[2])
        self.patronymic_entry.delete(0, tk.END)
        self.patronymic_entry.insert(0, values[3] if values[3] else '')
        self.position_entry.delete(0, tk.END)
        self.position_entry.insert(0, values[4])
        self.salary_entry.delete(0, tk.END)
        self.salary_entry.insert(0, values[5])
        self.status_label.config(text=f'Выбран сотрудник: {values[1]} {values[2]}')

    def clear_input_fields(self):
        self.last_name_entry.delete(0, tk.END)
        self.first_name_entry.delete(0, tk.END)
        self.patronymic_entry.delete(0, tk.END)
        self.position_entry.delete(0, tk.END)
        self.salary_entry.delete(0, tk.END)
        self.current_employee_id = None
        self.status_label.config(text='Поля очищены')


if __name__ == '__main__':
    root = tk.Tk()
    app = SalaryApp(root)
    root.mainloop()