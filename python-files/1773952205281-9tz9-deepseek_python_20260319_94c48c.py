import sys
import os
import traceback

# Перехватываем все исключения и пишем в error.log
try:
    import sqlite3
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog, simpledialog
    import csv
    from datetime import datetime

    # ==================== Конфигурация ====================
    DB_NAME = 'database.db'
    ADMIN_PASSWORD = 'admin'

    # ==================== База данных ====================
    def init_db():
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS groups
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT UNIQUE NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS teachers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      full_name TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS subjects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS rooms
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      number TEXT UNIQUE NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS lessons
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      day_of_week INTEGER NOT NULL,
                      time_start TEXT NOT NULL,
                      time_end TEXT NOT NULL,
                      group_id INTEGER NOT NULL,
                      teacher_id INTEGER NOT NULL,
                      subject_id INTEGER NOT NULL,
                      room_id INTEGER NOT NULL,
                      FOREIGN KEY(group_id) REFERENCES groups(id),
                      FOREIGN KEY(teacher_id) REFERENCES teachers(id),
                      FOREIGN KEY(subject_id) REFERENCES subjects(id),
                      FOREIGN KEY(room_id) REFERENCES rooms(id))''')
        
        c.execute("SELECT COUNT(*) FROM groups")
        if c.fetchone()[0] == 0:
            groups = [('ИС-41',), ('ИС-42',), ('ПИ-31',), ('ПИ-32',), ('БИ-21',)]
            c.executemany("INSERT INTO groups (name) VALUES (?)", groups)
            
            teachers = [('Иванов И.И.',), ('Петрова П.П.',), ('Сидоров С.С.',), 
                        ('Козлова Е.А.',), ('Морозов Д.В.',)]
            c.executemany("INSERT INTO teachers (full_name) VALUES (?)", teachers)
            
            subjects = [
                ('Математика',), ('Программирование',), ('Базы данных',),
                ('Физика',), ('Химия',), ('История',), ('Русский язык',),
                ('Английский язык',), ('Экономика',), ('Философия',)
            ]
            c.executemany("INSERT INTO subjects (name) VALUES (?)", subjects)
            
            rooms = [('101',), ('102',), ('103',), ('201',), ('202',)]
            c.executemany("INSERT INTO rooms (number) VALUES (?)", rooms)
            
            sample = [
                (0, '09:00', '10:30', 'ИС-41', 'Иванов И.И.', 'Математика', '101'),
                (0, '10:40', '12:10', 'ИС-41', 'Петрова П.П.', 'Программирование', '102'),
                (1, '09:00', '10:30', 'ИС-42', 'Сидоров С.С.', 'Базы данных', '103'),
            ]
            for day, t_start, t_end, g_name, t_name, s_name, r_num in sample:
                c.execute("SELECT id FROM groups WHERE name=?", (g_name,))
                g_id = c.fetchone()[0]
                c.execute("SELECT id FROM teachers WHERE full_name=?", (t_name,))
                t_id = c.fetchone()[0]
                c.execute("SELECT id FROM subjects WHERE name=?", (s_name,))
                s_id = c.fetchone()[0]
                c.execute("SELECT id FROM rooms WHERE number=?", (r_num,))
                r_id = c.fetchone()[0]
                c.execute('''INSERT INTO lessons 
                            (day_of_week, time_start, time_end, group_id, teacher_id, subject_id, room_id)
                            VALUES (?,?,?,?,?,?,?)''',
                          (day, t_start, t_end, g_id, t_id, s_id, r_id))
        
        conn.commit()
        conn.close()

    # ==================== Вспомогательные функции ====================
    def is_valid_time(t):
        if len(t) != 5 or t[2] != ':':
            return False
        try:
            hh = int(t[:2])
            mm = int(t[3:])
            if hh < 0 or hh > 23 or mm < 0 or mm > 59:
                return False
            total_minutes = hh * 60 + mm
            if total_minutes < 8*60 or total_minutes > 20*60:
                return False
            return True
        except ValueError:
            return False

    def check_conflict(day, start, end, group_id, teacher_id, room_id, exclude_lesson_id=None):
        conflicts = []
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        query = '''
            SELECT l.id, g.name, l.time_start, l.time_end
            FROM lessons l
            JOIN groups g ON l.group_id = g.id
            WHERE l.day_of_week = ? AND l.group_id = ?
            AND NOT (l.time_end <= ? OR l.time_start >= ?)
        '''
        params = [day, group_id, start, end]
        if exclude_lesson_id:
            query += " AND l.id != ?"
            params.append(exclude_lesson_id)
        c.execute(query, params)
        for row in c.fetchall():
            conflicts.append(f"Группа {row[1]} уже занята в это время ({row[2]}-{row[3]})")
        
        query = '''
            SELECT l.id, t.full_name, l.time_start, l.time_end
            FROM lessons l
            JOIN teachers t ON l.teacher_id = t.id
            WHERE l.day_of_week = ? AND l.teacher_id = ?
            AND NOT (l.time_end <= ? OR l.time_start >= ?)
        '''
        params = [day, teacher_id, start, end]
        if exclude_lesson_id:
            query += " AND l.id != ?"
            params.append(exclude_lesson_id)
        c.execute(query, params)
        for row in c.fetchall():
            conflicts.append(f"Преподаватель {row[1]} уже занят в это время ({row[2]}-{row[3]})")
        
        query = '''
            SELECT l.id, r.number, l.time_start, l.time_end
            FROM lessons l
            JOIN rooms r ON l.room_id = r.id
            WHERE l.day_of_week = ? AND l.room_id = ?
            AND NOT (l.time_end <= ? OR l.time_start >= ?)
        '''
        params = [day, room_id, start, end]
        if exclude_lesson_id:
            query += " AND l.id != ?"
            params.append(exclude_lesson_id)
        c.execute(query, params)
        for row in c.fetchall():
            conflicts.append(f"Аудитория {row[1]} уже занята в это время ({row[2]}-{row[3]})")
        
        conn.close()
        return conflicts

    # ==================== Основной класс приложения ====================
    class TimetableApp:
        def __init__(self, root):
            self.root = root
            self.root.title("Электронное расписание")
            self.root.geometry("950x700")
            
            self.style = ttk.Style()
            self.style.theme_use('clam')
            self.style.configure('TButton', font=('Arial', 10))
            self.style.configure('TLabel', font=('Arial', 10))
            self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
            
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Файл", menu=file_menu)
            file_menu.add_command(label="Выход", command=self.root.quit)
            
            role_frame = ttk.Frame(self.root, padding="10")
            role_frame.pack(fill=tk.X)
            
            ttk.Button(role_frame, text="👩‍🎓 Студент", command=self.open_student_window).pack(side=tk.LEFT, padx=5)
            ttk.Button(role_frame, text="👨‍🏫 Преподаватель", command=self.open_teacher_window).pack(side=tk.LEFT, padx=5)
            ttk.Button(role_frame, text="⚙ Администратор", command=self.check_admin_password).pack(side=tk.LEFT, padx=5)
            
            self.main_frame = ttk.Frame(self.root, padding="10")
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            
            self.label = ttk.Label(self.main_frame, text="Выберите роль для начала работы", style='Header.TLabel')
            self.label.pack(expand=True)
        
        def check_admin_password(self):
            password = simpledialog.askstring("Авторизация", "Введите пароль администратора:", show='*')
            if password == ADMIN_PASSWORD:
                self.open_admin_window()
            elif password is not None:
                messagebox.showerror("Ошибка", "Неверный пароль")
        
        def clear_main_frame(self):
            for widget in self.main_frame.winfo_children():
                widget.destroy()
        
        # ---------- Студент ----------
        def open_student_window(self):
            self.clear_main_frame()
            ttk.Label(self.main_frame, text="📘 Просмотр расписания для группы", style='Header.TLabel').pack(pady=10)
            
            control_frame = ttk.Frame(self.main_frame)
            control_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(control_frame, text="Группа:").pack(side=tk.LEFT, padx=5)
            self.student_group_var = tk.StringVar()
            self.student_group_combo = ttk.Combobox(control_frame, textvariable=self.student_group_var, state="readonly", width=15)
            self.student_group_combo.pack(side=tk.LEFT, padx=5)
            self.load_groups_to_combo(self.student_group_combo)
            
            ttk.Button(control_frame, text="🔍 Показать", command=self.show_student_timetable).pack(side=tk.LEFT, padx=5)
            ttk.Button(control_frame, text="📥 Экспорт CSV", command=self.export_student_csv).pack(side=tk.LEFT, padx=20)
            
            columns = ('day', 'time', 'subject', 'teacher', 'room')
            self.student_tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', height=18)
            self.student_tree.heading('day', text='День')
            self.student_tree.heading('time', text='Время')
            self.student_tree.heading('subject', text='Предмет')
            self.student_tree.heading('teacher', text='Преподаватель')
            self.student_tree.heading('room', text='Аудитория')
            self.student_tree.column('day', width=80, anchor='center')
            self.student_tree.column('time', width=100, anchor='center')
            self.student_tree.column('subject', width=200)
            self.student_tree.column('teacher', width=200)
            self.student_tree.column('room', width=80, anchor='center')
            
            scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.student_tree.yview)
            self.student_tree.configure(yscrollcommand=scrollbar.set)
            self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def load_groups_to_combo(self, combo):
            groups = self.get_groups()
            combo['values'] = [f"{g[0]}:{g[1]}" for g in groups]
            if groups:
                combo.current(0)
        
        def get_groups(self):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, name FROM groups ORDER BY name")
            rows = c.fetchall()
            conn.close()
            return rows
        
        def show_student_timetable(self):
            selection = self.student_group_var.get()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите группу")
                return
            group_id = int(selection.split(':')[0])
            for row in self.student_tree.get_children():
                self.student_tree.delete(row)
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                SELECT l.day_of_week, l.time_start, l.time_end,
                       s.name, t.full_name, r.number
                FROM lessons l
                JOIN subjects s ON l.subject_id = s.id
                JOIN teachers t ON l.teacher_id = t.id
                JOIN rooms r ON l.room_id = r.id
                WHERE l.group_id = ?
                ORDER BY l.day_of_week, l.time_start
            ''', (group_id,))
            rows = c.fetchall()
            conn.close()
            
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            for row in rows:
                day_str = days[row[0]] if 0 <= row[0] < 7 else str(row[0])
                time_str = f"{row[1]}–{row[2]}"
                self.student_tree.insert('', tk.END, values=(day_str, time_str, row[3], row[4], row[5]))
        
        def export_student_csv(self):
            selection = self.student_group_var.get()
            if not selection:
                messagebox.showwarning("Предупреждение", "Сначала выберите группу")
                return
            group_name = selection.split(':')[1]
            data = []
            for child in self.student_tree.get_children():
                values = self.student_tree.item(child)['values']
                data.append(values)
            if not data:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
                return
            filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                    filetypes=[("CSV files", "*.csv")],
                                                    initialfile=f"расписание_{group_name}.csv")
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['День', 'Время', 'Предмет', 'Преподаватель', 'Аудитория'])
                    writer.writerows(data)
                messagebox.showinfo("Экспорт", f"Данные сохранены в {filename}")
        
        # ---------- Преподаватель ----------
        def open_teacher_window(self):
            self.clear_main_frame()
            ttk.Label(self.main_frame, text="📋 Просмотр расписания для преподавателя", style='Header.TLabel').pack(pady=10)
            
            control_frame = ttk.Frame(self.main_frame)
            control_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(control_frame, text="Преподаватель:").pack(side=tk.LEFT, padx=5)
            self.teacher_var = tk.StringVar()
            self.teacher_combo = ttk.Combobox(control_frame, textvariable=self.teacher_var, state="readonly", width=25)
            self.teacher_combo.pack(side=tk.LEFT, padx=5)
            self.load_teachers_to_combo(self.teacher_combo)
            
            ttk.Button(control_frame, text="🔍 Показать", command=self.show_teacher_timetable).pack(side=tk.LEFT, padx=5)
            ttk.Button(control_frame, text="📥 Экспорт CSV", command=self.export_teacher_csv).pack(side=tk.LEFT, padx=20)
            
            columns = ('day', 'time', 'group', 'subject', 'room')
            self.teacher_tree = ttk.Treeview(self.main_frame, columns=columns, show='headings', height=18)
            self.teacher_tree.heading('day', text='День')
            self.teacher_tree.heading('time', text='Время')
            self.teacher_tree.heading('group', text='Группа')
            self.teacher_tree.heading('subject', text='Предмет')
            self.teacher_tree.heading('room', text='Аудитория')
            self.teacher_tree.column('day', width=80, anchor='center')
            self.teacher_tree.column('time', width=100, anchor='center')
            self.teacher_tree.column('group', width=100)
            self.teacher_tree.column('subject', width=200)
            self.teacher_tree.column('room', width=80, anchor='center')
            
            scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.teacher_tree.yview)
            self.teacher_tree.configure(yscrollcommand=scrollbar.set)
            self.teacher_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def load_teachers_to_combo(self, combo):
            teachers = self.get_teachers()
            combo['values'] = [f"{t[0]}:{t[1]}" for t in teachers]
            if teachers:
                combo.current(0)
        
        def get_teachers(self):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, full_name FROM teachers ORDER BY full_name")
            rows = c.fetchall()
            conn.close()
            return rows
        
        def show_teacher_timetable(self):
            selection = self.teacher_var.get()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите преподавателя")
                return
            teacher_id = int(selection.split(':')[0])
            for row in self.teacher_tree.get_children():
                self.teacher_tree.delete(row)
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                SELECT l.day_of_week, l.time_start, l.time_end,
                       g.name, s.name, r.number
                FROM lessons l
                JOIN groups g ON l.group_id = g.id
                JOIN subjects s ON l.subject_id = s.id
                JOIN rooms r ON l.room_id = r.id
                WHERE l.teacher_id = ?
                ORDER BY l.day_of_week, l.time_start
            ''', (teacher_id,))
            rows = c.fetchall()
            conn.close()
            
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            for row in rows:
                day_str = days[row[0]] if 0 <= row[0] < 7 else str(row[0])
                time_str = f"{row[1]}–{row[2]}"
                self.teacher_tree.insert('', tk.END, values=(day_str, time_str, row[3], row[4], row[5]))
        
        def export_teacher_csv(self):
            selection = self.teacher_var.get()
            if not selection:
                messagebox.showwarning("Предупреждение", "Сначала выберите преподавателя")
                return
            teacher_name = selection.split(':')[1]
            data = []
            for child in self.teacher_tree.get_children():
                values = self.teacher_tree.item(child)['values']
                data.append(values)
            if not data:
                messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
                return
            filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                    filetypes=[("CSV files", "*.csv")],
                                                    initialfile=f"расписание_{teacher_name}.csv")
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['День', 'Время', 'Группа', 'Предмет', 'Аудитория'])
                    writer.writerows(data)
                messagebox.showinfo("Экспорт", f"Данные сохранены в {filename}")
        
        # ---------- Администратор ----------
        def open_admin_window(self):
            self.clear_main_frame()
            notebook = ttk.Notebook(self.main_frame)
            notebook.pack(fill=tk.BOTH, expand=True)
            
            self.create_groups_tab(notebook)
            self.create_teachers_tab(notebook)
            self.create_subjects_tab(notebook)
            self.create_rooms_tab(notebook)
            self.create_lessons_tab(notebook)
        
        # ----- Группы -----
        def create_groups_tab(self, notebook):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Группы")
            
            add_frame = ttk.Frame(frame, padding="5")
            add_frame.pack(fill=tk.X)
            ttk.Label(add_frame, text="Название группы:").pack(side=tk.LEFT)
            self.group_entry = ttk.Entry(add_frame, width=30)
            self.group_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(add_frame, text="➕ Добавить", command=self.add_group).pack(side=tk.LEFT)
            
            columns = ('id', 'name')
            self.groups_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
            self.groups_tree.heading('id', text='ID')
            self.groups_tree.heading('name', text='Название')
            self.groups_tree.column('id', width=50, anchor='center')
            self.groups_tree.column('name', width=250)
            self.groups_tree.pack(fill=tk.BOTH, expand=True, pady=5)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=5)
            ttk.Button(btn_frame, text="✏ Редактировать", command=self.edit_group).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_group).pack(side=tk.LEFT, padx=5)
            
            self.refresh_groups_list()
        
        def add_group(self):
            name = self.group_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название группы")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO groups (name) VALUES (?)", (name,))
                conn.commit()
                self.group_entry.delete(0, tk.END)
                self.refresh_groups_list()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Группа с таким названием уже существует")
            finally:
                conn.close()
        
        def edit_group(self):
            selected = self.groups_tree.selection()
            if not selected:
                messagebox.showwarning("Предупреждение", "Выберите группу")
                return
            item = self.groups_tree.item(selected[0])
            group_id, old_name = item['values']
            new_name = simpledialog.askstring("Редактирование", "Новое название группы:", initialvalue=old_name)
            if new_name and new_name.strip():
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                try:
                    c.execute("UPDATE groups SET name=? WHERE id=?", (new_name.strip(), group_id))
                    conn.commit()
                    self.refresh_groups_list()
                except sqlite3.IntegrityError:
                    messagebox.showerror("Ошибка", "Группа с таким названием уже существует")
                finally:
                    conn.close()
        
        def delete_group(self):
            selected = self.groups_tree.selection()
            if not selected:
                messagebox.showwarning("Предупреждение", "Выберите группу")
                return
            item = self.groups_tree.item(selected[0])
            group_id = item['values'][0]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM lessons WHERE group_id=?", (group_id,))
            if c.fetchone()[0] > 0:
                messagebox.showerror("Ошибка", "Нельзя удалить группу, для которой есть занятия")
                conn.close()
                return
            c.execute("DELETE FROM groups WHERE id=?", (group_id,))
            conn.commit()
            conn.close()
            self.refresh_groups_list()
        
        def refresh_groups_list(self):
            for row in self.groups_tree.get_children():
                self.groups_tree.delete(row)
            groups = self.get_groups()
            for g in groups:
                self.groups_tree.insert('', tk.END, values=g)
        
        # ----- Преподаватели -----
        def create_teachers_tab(self, notebook):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Преподаватели")
            add_frame = ttk.Frame(frame, padding="5")
            add_frame.pack(fill=tk.X)
            ttk.Label(add_frame, text="ФИО преподавателя:").pack(side=tk.LEFT)
            self.teacher_entry = ttk.Entry(add_frame, width=40)
            self.teacher_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(add_frame, text="➕ Добавить", command=self.add_teacher).pack(side=tk.LEFT)
            
            columns = ('id', 'name')
            self.teachers_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
            self.teachers_tree.heading('id', text='ID')
            self.teachers_tree.heading('name', text='ФИО')
            self.teachers_tree.column('id', width=50, anchor='center')
            self.teachers_tree.column('name', width=350)
            self.teachers_tree.pack(fill=tk.BOTH, expand=True, pady=5)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=5)
            ttk.Button(btn_frame, text="✏ Редактировать", command=self.edit_teacher).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_teacher).pack(side=tk.LEFT, padx=5)
            self.refresh_teachers_list()
        
        def add_teacher(self):
            name = self.teacher_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите ФИО")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO teachers (full_name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            self.teacher_entry.delete(0, tk.END)
            self.refresh_teachers_list()
        
        def edit_teacher(self):
            selected = self.teachers_tree.selection()
            if not selected:
                return
            item = self.teachers_tree.item(selected[0])
            tid, old = item['values']
            new = simpledialog.askstring("Редактировать", "Новое ФИО:", initialvalue=old)
            if new and new.strip():
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("UPDATE teachers SET full_name=? WHERE id=?", (new.strip(), tid))
                conn.commit()
                conn.close()
                self.refresh_teachers_list()
        
        def delete_teacher(self):
            selected = self.teachers_tree.selection()
            if not selected:
                return
            item = self.teachers_tree.item(selected[0])
            tid = item['values'][0]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM lessons WHERE teacher_id=?", (tid,))
            if c.fetchone()[0] > 0:
                messagebox.showerror("Ошибка", "Нельзя удалить преподавателя, у которого есть занятия")
                conn.close()
                return
            c.execute("DELETE FROM teachers WHERE id=?", (tid,))
            conn.commit()
            conn.close()
            self.refresh_teachers_list()
        
        def refresh_teachers_list(self):
            for row in self.teachers_tree.get_children():
                self.teachers_tree.delete(row)
            teachers = self.get_teachers()
            for t in teachers:
                self.teachers_tree.insert('', tk.END, values=t)
        
        # ----- Предметы -----
        def create_subjects_tab(self, notebook):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Предметы")
            add_frame = ttk.Frame(frame, padding="5")
            add_frame.pack(fill=tk.X)
            ttk.Label(add_frame, text="Название предмета:").pack(side=tk.LEFT)
            self.subject_entry = ttk.Entry(add_frame, width=40)
            self.subject_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(add_frame, text="➕ Добавить", command=self.add_subject).pack(side=tk.LEFT)
            
            columns = ('id', 'name')
            self.subjects_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
            self.subjects_tree.heading('id', text='ID')
            self.subjects_tree.heading('name', text='Название')
            self.subjects_tree.column('id', width=50, anchor='center')
            self.subjects_tree.column('name', width=350)
            self.subjects_tree.pack(fill=tk.BOTH, expand=True, pady=5)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=5)
            ttk.Button(btn_frame, text="✏ Редактировать", command=self.edit_subject).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_subject).pack(side=tk.LEFT, padx=5)
            self.refresh_subjects_list()
        
        def add_subject(self):
            name = self.subject_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()
            self.subject_entry.delete(0, tk.END)
            self.refresh_subjects_list()
        
        def edit_subject(self):
            selected = self.subjects_tree.selection()
            if not selected:
                return
            item = self.subjects_tree.item(selected[0])
            sid, old = item['values']
            new = simpledialog.askstring("Редактировать", "Новое название:", initialvalue=old)
            if new and new.strip():
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("UPDATE subjects SET name=? WHERE id=?", (new.strip(), sid))
                conn.commit()
                conn.close()
                self.refresh_subjects_list()
        
        def delete_subject(self):
            selected = self.subjects_tree.selection()
            if not selected:
                return
            item = self.subjects_tree.item(selected[0])
            sid = item['values'][0]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM lessons WHERE subject_id=?", (sid,))
            if c.fetchone()[0] > 0:
                messagebox.showerror("Ошибка", "Нельзя удалить предмет, который используется в занятиях")
                conn.close()
                return
            c.execute("DELETE FROM subjects WHERE id=?", (sid,))
            conn.commit()
            conn.close()
            self.refresh_subjects_list()
        
        def refresh_subjects_list(self):
            for row in self.subjects_tree.get_children():
                self.subjects_tree.delete(row)
            subjects = self.get_subjects()
            for s in subjects:
                self.subjects_tree.insert('', tk.END, values=s)
        
        def get_subjects(self):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, name FROM subjects ORDER BY name")
            rows = c.fetchall()
            conn.close()
            return rows
        
        # ----- Аудитории -----
        def create_rooms_tab(self, notebook):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Аудитории")
            add_frame = ttk.Frame(frame, padding="5")
            add_frame.pack(fill=tk.X)
            ttk.Label(add_frame, text="Номер аудитории:").pack(side=tk.LEFT)
            self.room_entry = ttk.Entry(add_frame, width=20)
            self.room_entry.pack(side=tk.LEFT, padx=5)
            ttk.Button(add_frame, text="➕ Добавить", command=self.add_room).pack(side=tk.LEFT)
            
            columns = ('id', 'number')
            self.rooms_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
            self.rooms_tree.heading('id', text='ID')
            self.rooms_tree.heading('number', text='Номер')
            self.rooms_tree.column('id', width=50, anchor='center')
            self.rooms_tree.column('number', width=150)
            self.rooms_tree.pack(fill=tk.BOTH, expand=True, pady=5)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=5)
            ttk.Button(btn_frame, text="✏ Редактировать", command=self.edit_room).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_room).pack(side=tk.LEFT, padx=5)
            self.refresh_rooms_list()
        
        def add_room(self):
            number = self.room_entry.get().strip()
            if not number:
                messagebox.showwarning("Ошибка", "Введите номер")
                return
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO rooms (number) VALUES (?)", (number,))
                conn.commit()
                self.room_entry.delete(0, tk.END)
                self.refresh_rooms_list()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Аудитория с таким номером уже существует")
            finally:
                conn.close()
        
        def edit_room(self):
            selected = self.rooms_tree.selection()
            if not selected:
                return
            item = self.rooms_tree.item(selected[0])
            rid, old = item['values']
            new = simpledialog.askstring("Редактировать", "Новый номер:", initialvalue=old)
            if new and new.strip():
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                try:
                    c.execute("UPDATE rooms SET number=? WHERE id=?", (new.strip(), rid))
                    conn.commit()
                    self.refresh_rooms_list()
                except sqlite3.IntegrityError:
                    messagebox.showerror("Ошибка", "Аудитория с таким номером уже существует")
                finally:
                    conn.close()
        
        def delete_room(self):
            selected = self.rooms_tree.selection()
            if not selected:
                return
            item = self.rooms_tree.item(selected[0])
            rid = item['values'][0]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM lessons WHERE room_id=?", (rid,))
            if c.fetchone()[0] > 0:
                messagebox.showerror("Ошибка", "Нельзя удалить аудиторию, которая используется в занятиях")
                conn.close()
                return
            c.execute("DELETE FROM rooms WHERE id=?", (rid,))
            conn.commit()
            conn.close()
            self.refresh_rooms_list()
        
        def refresh_rooms_list(self):
            for row in self.rooms_tree.get_children():
                self.rooms_tree.delete(row)
            rooms = self.get_rooms()
            for r in rooms:
                self.rooms_tree.insert('', tk.END, values=r)
        
        def get_rooms(self):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, number FROM rooms ORDER BY number")
            rows = c.fetchall()
            conn.close()
            return rows
        
        # ----- Занятия -----
        def create_lessons_tab(self, notebook):
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Занятия")
            
            add_frame = ttk.LabelFrame(frame, text="Добавить занятие", padding="10")
            add_frame.pack(fill=tk.X, pady=5)
            
            row1 = ttk.Frame(add_frame)
            row1.pack(fill=tk.X, pady=2)
            ttk.Label(row1, text="День:").pack(side=tk.LEFT, padx=5)
            self.lesson_day = ttk.Combobox(row1, values=['Пн','Вт','Ср','Чт','Пт','Сб','Вс'], state="readonly", width=8)
            self.lesson_day.pack(side=tk.LEFT)
            self.lesson_day.current(0)
            
            ttk.Label(row1, text="Начало:").pack(side=tk.LEFT, padx=5)
            self.lesson_start = ttk.Entry(row1, width=8)
            self.lesson_start.pack(side=tk.LEFT)
            self.lesson_start.insert(0, "09:00")
            
            ttk.Label(row1, text="Конец:").pack(side=tk.LEFT, padx=5)
            self.lesson_end = ttk.Entry(row1, width=8)
            self.lesson_end.pack(side=tk.LEFT)
            self.lesson_end.insert(0, "10:30")
            
            row2 = ttk.Frame(add_frame)
            row2.pack(fill=tk.X, pady=2)
            ttk.Label(row2, text="Группа:").pack(side=tk.LEFT, padx=5)
            self.lesson_group = ttk.Combobox(row2, state="readonly", width=15)
            self.lesson_group.pack(side=tk.LEFT)
            ttk.Label(row2, text="Преподаватель:").pack(side=tk.LEFT, padx=5)
            self.lesson_teacher = ttk.Combobox(row2, state="readonly", width=20)
            self.lesson_teacher.pack(side=tk.LEFT)
            
            row3 = ttk.Frame(add_frame)
            row3.pack(fill=tk.X, pady=2)
            ttk.Label(row3, text="Предмет:").pack(side=tk.LEFT, padx=5)
            self.lesson_subject = ttk.Combobox(row3, state="readonly", width=20)
            self.lesson_subject.pack(side=tk.LEFT)
            ttk.Label(row3, text="Аудитория:").pack(side=tk.LEFT, padx=5)
            self.lesson_room = ttk.Combobox(row3, state="readonly", width=10)
            self.lesson_room.pack(side=tk.LEFT)
            
            ttk.Button(add_frame, text="✅ Добавить занятие", command=self.add_lesson).pack(pady=5)
            
            columns = ('id', 'day', 'time', 'group', 'teacher', 'subject', 'room')
            self.lessons_tree = ttk.Treeview(frame, columns=columns, show='headings', height=12)
            self.lessons_tree.heading('id', text='ID')
            self.lessons_tree.heading('day', text='День')
            self.lessons_tree.heading('time', text='Время')
            self.lessons_tree.heading('group', text='Группа')
            self.lessons_tree.heading('teacher', text='Преподаватель')
            self.lessons_tree.heading('subject', text='Предмет')
            self.lessons_tree.heading('room', text='Аудитория')
            self.lessons_tree.column('id', width=40, anchor='center')
            self.lessons_tree.column('day', width=60, anchor='center')
            self.lessons_tree.column('time', width=90, anchor='center')
            self.lessons_tree.column('group', width=100)
            self.lessons_tree.column('teacher', width=180)
            self.lessons_tree.column('subject', width=150)
            self.lessons_tree.column('room', width=70, anchor='center')
            
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.lessons_tree.yview)
            self.lessons_tree.configure(yscrollcommand=scrollbar.set)
            self.lessons_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=5)
            ttk.Button(btn_frame, text="❌ Удалить выбранное", command=self.delete_lesson).pack(side=tk.LEFT, padx=5)
            
            self.refresh_lesson_combos()
            self.refresh_lessons_list()
        
        def refresh_lesson_combos(self):
            groups = self.get_groups()
            self.lesson_group['values'] = [f"{g[0]}:{g[1]}" for g in groups]
            if groups:
                self.lesson_group.current(0)
            
            teachers = self.get_teachers()
            self.lesson_teacher['values'] = [f"{t[0]}:{t[1]}" for t in teachers]
            if teachers:
                self.lesson_teacher.current(0)
            
            subjects = self.get_subjects()
            self.lesson_subject['values'] = [f"{s[0]}:{s[1]}" for s in subjects]
            if subjects:
                self.lesson_subject.current(0)
            
            rooms = self.get_rooms()
            self.lesson_room['values'] = [f"{r[0]}:{r[1]}" for r in rooms]
            if rooms:
                self.lesson_room.current(0)
        
        def add_lesson(self):
            try:
                group_id = int(self.lesson_group.get().split(':')[0])
                teacher_id = int(self.lesson_teacher.get().split(':')[0])
                subject_id = int(self.lesson_subject.get().split(':')[0])
                room_id = int(self.lesson_room.get().split(':')[0])
            except:
                messagebox.showerror("Ошибка", "Не удалось получить ID. Проверьте справочники.")
                return
            
            day_map = {'Пн':0, 'Вт':1, 'Ср':2, 'Чт':3, 'Пт':4, 'Сб':5, 'Вс':6}
            day = day_map.get(self.lesson_day.get(), 0)
            start = self.lesson_start.get().strip()
            end = self.lesson_end.get().strip()
            
            if not is_valid_time(start) or not is_valid_time(end):
                messagebox.showerror("Ошибка", "Время должно быть в формате ЧЧ:ММ и в пределах 08:00-20:00")
                return
            
            if start >= end:
                messagebox.showerror("Ошибка", "Время начала должно быть раньше времени окончания")
                return
            
            conflicts = check_conflict(day, start, end, group_id, teacher_id, room_id)
            if conflicts:
                msg = "Обнаружены конфликты:\n" + "\n".join(conflicts)
                messagebox.showerror("Конфликт", msg)
                return
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                INSERT INTO lessons (day_of_week, time_start, time_end, group_id, teacher_id, subject_id, room_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (day, start, end, group_id, teacher_id, subject_id, room_id))
            conn.commit()
            conn.close()
            self.refresh_lessons_list()
            messagebox.showinfo("Успех", "Занятие добавлено")
        
        def delete_lesson(self):
            selected = self.lessons_tree.selection()
            if not selected:
                messagebox.showwarning("Предупреждение", "Выберите занятие для удаления")
                return
            item = self.lessons_tree.item(selected[0])
            lesson_id = item['values'][0]
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM lessons WHERE id=?", (lesson_id,))
            conn.commit()
            conn.close()
            self.refresh_lessons_list()
        
        def refresh_lessons_list(self):
            for row in self.lessons_tree.get_children():
                self.lessons_tree.delete(row)
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''
                SELECT l.id, l.day_of_week, l.time_start, l.time_end,
                       g.name, t.full_name, s.name, r.number
                FROM lessons l
                JOIN groups g ON l.group_id = g.id
                JOIN teachers t ON l.teacher_id = t.id
                JOIN subjects s ON l.subject_id = s.id
                JOIN rooms r ON l.room_id = r.id
                ORDER BY l.day_of_week, l.time_start
            ''')
            rows = c.fetchall()
            conn.close()
            days = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс']
            for row in rows:
                day_str = days[row[1]] if 0 <= row[1] < 7 else str(row[1])
                time_str = f"{row[2]}–{row[3]}"
                self.lessons_tree.insert('', tk.END, values=(row[0], day_str, time_str, row[4], row[5], row[6], row[7]))

    # ==================== Запуск ====================
    if __name__ == "__main__":
        if not os.path.exists(DB_NAME):
            init_db()
        else:
            init_db()
        
        root = tk.Tk()
        app = TimetableApp(root)
        root.mainloop()

except Exception:
    with open("error.log", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
    # Показываем окно с ошибкой, чтобы пользователь знал
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Ошибка", "Произошла ошибка. Подробности в файле error.log")
    raise