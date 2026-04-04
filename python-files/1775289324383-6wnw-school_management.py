import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
from datetime import datetime
import tempfile
import os
import subprocess
from PIL import Image, ImageTk  # Required for logo support

# ================= SCHOOL NAME =================
SCHOOL_NAME = "Faiz Ul Quran High School Shinka"

# ================= LOGO HANDLING =================
def load_logo():
    """Load logo from file or return None if not found"""
    logo_paths = [
        "logo.png",
        "school_logo.png",
        "logo.jpg",
        "school_logo.jpg",
        os.path.join(os.path.dirname(__file__), "logo.png"),
    ]
    for path in logo_paths:
        try:
            img = Image.open(path)
            img = img.resize((60 , 60), Image.Resampling.LANCZOS)
            logo = ImageTk.PhotoImage(img)
            return logo
        except:
            continue
    return None

DEFAULT_LOGO_TEXT = "🏫"

# ================= PRINT HELPER =================
def open_print_window(content, title="Print Preview"):
    """Display content in a new window with options to save or open for printing."""
    win = tk.Toplevel()
    win.title(title)
    win.geometry("600x500")
    
    text_widget = tk.Text(win, wrap=tk.WORD)
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_widget.insert(tk.END, content)
    text_widget.config(state=tk.DISABLED)
    
    button_frame = tk.Frame(win)
    button_frame.pack(pady=5)
    
    def save_to_file():
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Content saved to {file_path}")
    
    def open_for_printing():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_file = f.name
        try:
            os.startfile(temp_file)
        except AttributeError:
            try:
                subprocess.run(["xdg-open", temp_file])
            except:
                messagebox.showerror("Error", "Unable to open file. Please save manually.")
    
    tk.Button(button_frame, text="Save as Text", command=save_to_file).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Open for Printing", command=open_for_printing).pack(side=tk.LEFT, padx=5)

# ================= DATABASE SETUP =================
conn = sqlite3.connect("school.db")
cursor = conn.cursor()

# Students table with all columns
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    father TEXT NOT NULL,
    form_b TEXT,
    contact TEXT,
    roll TEXT UNIQUE,
    class TEXT,
    status TEXT DEFAULT 'active',
    leave_date TEXT,
    leave_reason TEXT,
    completion_date TEXT
)
""")

# Ensure new columns exist (for existing databases)
for col, type_ in [('status', 'TEXT DEFAULT "active"'),
                   ('leave_date', 'TEXT'),
                   ('leave_reason', 'TEXT'),
                   ('completion_date', 'TEXT')]:
    try:
        cursor.execute(f"ALTER TABLE students ADD COLUMN {col} {type_}")
    except sqlite3.OperationalError:
        pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS exam_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    exam_type TEXT,
    subject TEXT,
    marks_obtained INTEGER,
    total_marks INTEGER,
    date TEXT,
    FOREIGN KEY(student_id) REFERENCES students(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS class_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    old_class TEXT,
    new_class TEXT,
    date TEXT
)
""")

conn.commit()

# ================= LOGIN =================
USERNAME = "Usman Aziz"
PASSWORD = "FQHS1552"

def login():
    if user_entry.get() == USERNAME and pass_entry.get() == PASSWORD:
        login_win.destroy()
        dashboard()
    else:
        messagebox.showerror("Error", "Wrong Login")

# ================= PASSING CRITERIA =================
def has_passed_exam(student_id, exam_type='examination'):
    cursor.execute("""
        SELECT SUM(marks_obtained), SUM(total_marks)
        FROM exam_results
        WHERE student_id=? AND exam_type=?
    """, (student_id, exam_type))
    total_obtained, total_max = cursor.fetchone()
    if total_obtained is None or total_max == 0:
        return False
    percentage = (total_obtained / total_max) * 100
    return percentage >= 33

def can_promote(student_id, current_class):
    return current_class == '1' and has_passed_exam(student_id)

# ================= DASHBOARD (SCROLLING VERTICAL LAYOUT) =================
def dashboard():
    root = tk.Tk()
    root.title("School Management System")
    root.geometry("1300x800")
    root.configure(bg='#f0f0f0')
    
    # Create main canvas with scrollbar
    main_canvas = tk.Canvas(root, bg='#f0f0f0', highlightthickness=0)
    main_scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
    main_canvas.configure(yscrollcommand=main_scrollbar.set)
    
    main_canvas.pack(side="left", fill="both", expand=True)
    main_scrollbar.pack(side="right", fill="y")
    
    # Create frame inside canvas that will scroll
    scrollable_frame = tk.Frame(main_canvas, bg='#f0f0f0')
    scrollable_frame.bind(
        "<Configure>",
        lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )
    
    canvas_window = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=main_canvas.winfo_width())
    
    def configure_canvas(event):
        main_canvas.itemconfig(canvas_window, width=event.width)
    
    main_canvas.bind('<Configure>', configure_canvas)
    
    # Mouse wheel scrolling
    def on_mousewheel(event):
        main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_mousewheel_linux(event):
        main_canvas.yview_scroll(int(-1*event.num), "units")
    
    main_canvas.bind_all("<MouseWheel>", on_mousewheel)
    main_canvas.bind_all("<Button-4>", on_mousewheel_linux)
    main_canvas.bind_all("<Button-5>", on_mousewheel_linux)
    
    # ---------- Top Frame (Logo & School Name) ----------
    top_frame = tk.Frame(scrollable_frame, bg='#2c3e50', height=80)
    top_frame.pack(fill=tk.X, pady=(0, 10))
    top_frame.pack_propagate(False)

    logo_img = load_logo()
    if logo_img:
        logo_label = tk.Label(top_frame, image=logo_img, bg='#2c3e50')
        logo_label.image = logo_img
        logo_label.pack(side=tk.LEFT, padx=10, pady=10)
    else:
        logo_label = tk.Label(top_frame, text=DEFAULT_LOGO_TEXT, font=("Arial", 40), bg='#2c3e50', fg='white')
        logo_label.pack(side=tk.LEFT, padx=20)

    school_name_label = tk.Label(top_frame, text=SCHOOL_NAME, font=("Arial", 20, "bold"),
                                 bg='#2c3e50', fg='white')
    school_name_label.pack(side=tk.LEFT, padx=10, pady=10)
    
    # ================= MAIN CONTENT (All in one vertical flow) =================
    main_frame = tk.Frame(scrollable_frame, bg='#f0f0f0')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    # ================= REGISTER STUDENT SECTION =================
    register_frame = tk.LabelFrame(main_frame, text="📝 Register New Student", 
                                   font=("Arial", 14, "bold"), bg='white', padx=15, pady=15)
    register_frame.pack(fill=tk.X, pady=(0, 15))
    
    reg_left = tk.Frame(register_frame, bg='white')
    reg_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    
    reg_right = tk.Frame(register_frame, bg='white')
    reg_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    
    entries = {}
    
    # Left column fields
    left_fields = [
        ("Name *", "entry_name"),
        ("Father Name *", "entry_father"),
        ("Form-B", "entry_formb")
    ]
    
    for i, (label, key) in enumerate(left_fields):
        tk.Label(reg_left, text=label, bg='white', font=("Arial", 10)).grid(row=i, column=0, sticky='e', pady=5, padx=5)
        entry = tk.Entry(reg_left, width=25, font=("Arial", 10))
        entry.grid(row=i, column=1, pady=5, padx=5)
        entries[key] = entry
    
    # Right column fields (Contact and Roll)
    right_fields = [
        ("Contact", "entry_contact"),
        ("Roll Number", "entry_roll"),
    ]
    
    for i, (label, key) in enumerate(right_fields):
        tk.Label(reg_right, text=label, bg='white', font=("Arial", 10)).grid(row=i, column=0, sticky='e', pady=5, padx=5)
        entry = tk.Entry(reg_right, width=25, font=("Arial", 10))
        entry.grid(row=i, column=1, pady=5, padx=5)
        entries[key] = entry
    
    # Class combobox
    tk.Label(reg_right, text="Class *", bg='white', font=("Arial", 10)).grid(row=2, column=0, sticky='e', pady=5, padx=5)
    class_combo_reg = ttk.Combobox(reg_right, width=22)
    class_combo_reg['values'] = ['Nursery', 'Prep'] + [str(i) for i in range(1, 11)]
    class_combo_reg.grid(row=2, column=1, pady=5, padx=5)
    entries['entry_class'] = class_combo_reg
    
    # Save function
    def save_student():
        name = entries['entry_name'].get().strip()
        father = entries['entry_father'].get().strip()
        roll = entries['entry_roll'].get().strip()
        student_class = entries['entry_class'].get().strip()
        
        if not name or not father:
            messagebox.showwarning("⚠️ Validation Error", "Name and Father Name are required!")
            entries['entry_name'].focus()
            return
        if not roll:
            messagebox.showwarning("⚠️ Validation Error", "Roll Number is required!")
            entries['entry_roll'].focus()
            return
        if not student_class:
            messagebox.showwarning("⚠️ Validation Error", "Class is required!")
            entries['entry_class'].focus()
            return
        
        try:
            cursor.execute("""
                INSERT INTO students (name, father, form_b, contact, roll, class, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (name, father, 
                  entries['entry_formb'].get().strip(),
                  entries['entry_contact'].get().strip(),
                  roll, student_class))
            conn.commit()
            messagebox.showinfo("✅ Success", f"Student {name} registered successfully!\nRoll No: {roll}\nClass: {student_class}")
            for entry in entries.values():
                if isinstance(entry, tk.Entry):
                    entry.delete(0, tk.END)
                elif isinstance(entry, ttk.Combobox):
                    entry.set('')
            entries['entry_name'].focus()
            if current_class.get() == student_class:
                show_class_details(student_class)
        except sqlite3.IntegrityError:
            messagebox.showerror("❌ Error", f"Roll number '{roll}' already exists!\nPlease use a unique roll number.")
            entries['entry_roll'].select_range(0, tk.END)
            entries['entry_roll'].focus()
    
    save_button_frame = tk.Frame(register_frame, bg='white')
    save_button_frame.pack(pady=10)
    save_btn = tk.Button(save_button_frame, text="💾 Save Student (Enter)", command=save_student, 
                         bg='#27ae60', fg='white', font=("Arial", 11, "bold"), padx=30, pady=5, cursor="hand2")
    save_btn.pack()
    shortcut_label = tk.Label(register_frame, text="⌨️ Press 'Enter' to save | Ctrl+S also works", 
                              bg='#ffffe0', font=("Arial", 8), fg='#7f8c8d')
    shortcut_label.pack(pady=2)
    
    def on_enter_key(event):
        save_student()
        return "break"
    def on_ctrl_s(event):
        save_student()
        return "break"
    
    for entry in entries.values():
        if isinstance(entry, (tk.Entry, ttk.Combobox)):
            entry.bind('<Return>', on_enter_key)
            entry.bind('<Control-s>', on_ctrl_s)
            entry.bind('<Control-S>', on_ctrl_s)
    root.bind('<Control-s>', on_ctrl_s)
    root.bind('<Control-S>', on_ctrl_s)
    
    # ================= EXAM ENTRY SECTION =================
    exam_frame = tk.LabelFrame(main_frame, text="📊 Enter Examination Results", 
                               font=("Arial", 14, "bold"), bg='white', padx=15, pady=15)
    exam_frame.pack(fill=tk.X, pady=(0, 15))
    
    search_exam_frame = tk.Frame(exam_frame, bg='white')
    search_exam_frame.pack(fill=tk.X, pady=5)
    
    tk.Label(search_exam_frame, text="Class:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    class_var = tk.StringVar()
    class_combo = ttk.Combobox(search_exam_frame, textvariable=class_var, width=10)
    class_combo['values'] = ['Nursery', 'Prep'] + [str(i) for i in range(1, 11)]
    class_combo.pack(side=tk.LEFT, padx=5)
    
    tk.Label(search_exam_frame, text="Roll No:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
    roll_entry = tk.Entry(search_exam_frame, width=12)
    roll_entry.pack(side=tk.LEFT, padx=5)
    
    exam_type = tk.StringVar(value="examination")
    tk.Radiobutton(search_exam_frame, text="Exam", variable=exam_type,
                   value="examination", bg='white').pack(side=tk.LEFT, padx=2)
    tk.Radiobutton(search_exam_frame, text="Monthly Test", variable=exam_type,
                   value="monthly_test", bg='white').pack(side=tk.LEFT, padx=2)
    
    student_info_label = tk.Label(exam_frame, text="", bg='white', font=("Arial", 9, "bold"), fg='green')
    student_info_label.pack(pady=5)
    
    subjects_container = tk.Frame(exam_frame, bg='white')
    subjects_container.pack(fill=tk.BOTH, expand=True, pady=5)
    
    subjects_canvas = tk.Canvas(subjects_container, bg='white', height=120, highlightthickness=0)
    subjects_scrollbar = ttk.Scrollbar(subjects_container, orient=tk.VERTICAL, command=subjects_canvas.yview)
    subjects_scrollable = tk.Frame(subjects_canvas, bg='white')
    
    subjects_scrollable.bind("<Configure>", lambda e: subjects_canvas.configure(scrollregion=subjects_canvas.bbox("all")))
    subjects_canvas.create_window((0, 0), window=subjects_scrollable, anchor="nw")
    subjects_canvas.configure(yscrollcommand=subjects_scrollbar.set)
    
    subjects_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    subjects_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    subject_rows = []
    
    def add_subject_row():
        row_frame = tk.Frame(subjects_scrollable, bg='white')
        row_frame.pack(fill=tk.X, pady=2)
        tk.Label(row_frame, text="Subject:", bg='white', font=("Arial", 8)).pack(side=tk.LEFT)
        sub_entry = tk.Entry(row_frame, width=12)
        sub_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(row_frame, text="Marks:", bg='white', font=("Arial", 8)).pack(side=tk.LEFT)
        marks_entry = tk.Entry(row_frame, width=6)
        marks_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(row_frame, text="/", bg='white').pack(side=tk.LEFT)
        total_entry = tk.Entry(row_frame, width=6)
        total_entry.pack(side=tk.LEFT, padx=2)
        
        def remove_row():
            row_frame.destroy()
            subject_rows.remove((sub_entry, marks_entry, total_entry))
        
        tk.Button(row_frame, text="✖", command=remove_row, bg='red', fg='white',
                  font=("Arial", 7), width=2).pack(side=tk.LEFT, padx=5)
        subject_rows.append((sub_entry, marks_entry, total_entry))
    
    add_subject_row()
    
    btn_frame_exam = tk.Frame(exam_frame, bg='white')
    btn_frame_exam.pack(pady=5)
    
    def search_student_exam():
        cls = class_var.get()
        roll = roll_entry.get().strip()
        if not cls or not roll:
            messagebox.showwarning("Error", "Please enter Class and Roll Number")
            return
        cursor.execute("SELECT id, name, father FROM students WHERE class=? AND roll=? AND status='active'", (cls, roll))
        student = cursor.fetchone()
        if student:
            student_info_label.config(text=f"✓ {student[1]} (Father: {student[2]})", fg='green')
            student_info_label.sid = student[0]
        else:
            messagebox.showerror("Error", "Student not found")
            student_info_label.config(text="✗ Student not found", fg='red')
            student_info_label.sid = None
    
    def save_exam_results():
        if not hasattr(student_info_label, 'sid') or student_info_label.sid is None:
            messagebox.showwarning("Error", "Please search a student first")
            return
        sid = student_info_label.sid
        exam = exam_type.get()
        saved_count = 0
        for sub_entry, marks_entry, total_entry in subject_rows:
            subject = sub_entry.get().strip()
            marks_str = marks_entry.get().strip()
            total_str = total_entry.get().strip()
            if not subject or not marks_str or not total_str:
                continue
            try:
                marks = int(marks_str)
                total = int(total_str)
                if marks < 0 or total <= 0 or marks > total:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", f"Invalid marks for '{subject}'")
                return
            cursor.execute("""
                INSERT INTO exam_results (student_id, exam_type, subject, marks_obtained, total_marks, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sid, exam, subject, marks, total, datetime.now().isoformat()))
            saved_count += 1
        conn.commit()
        messagebox.showinfo("Saved", f"{saved_count} subject(s) saved!")
        for sub_entry, marks_entry, total_entry in subject_rows:
            sub_entry.delete(0, tk.END)
            marks_entry.delete(0, tk.END)
            total_entry.delete(0, tk.END)
    
    tk.Button(btn_frame_exam, text="🔍 Search", command=search_student_exam, 
              bg='#2980b9', fg='white').pack(side=tk.LEFT, padx=2)
    tk.Button(btn_frame_exam, text="+ Add Subject", command=add_subject_row, 
              bg='#3498db', fg='white').pack(side=tk.LEFT, padx=2)
    tk.Button(btn_frame_exam, text="💾 Save Results", command=save_exam_results, 
              bg='#27ae60', fg='white').pack(side=tk.LEFT, padx=2)
    
    # ================= TOP BUTTONS ROW =================
    top_buttons_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=2)
    top_buttons_frame.pack(fill=tk.X, pady=(0, 15))
    buttons_container = tk.Frame(top_buttons_frame, bg='white')
    buttons_container.pack(pady=10)
    
    def open_search_window():
        win = tk.Toplevel(root)
        win.title("Search Student")
        win.geometry("500x400")
        tk.Label(win, text="Enter Name or Roll Number:", font=("Arial", 10)).pack(pady=5)
        entry = tk.Entry(win, width=40, font=("Arial", 10))
        entry.pack(pady=5)
        listbox = tk.Listbox(win, width=70, height=15, font=("Arial", 9))
        listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        student_ids = []
        def perform_search():
            keyword = entry.get().strip()
            cursor.execute("""
                SELECT id, name, father, roll, class FROM students
                WHERE (name LIKE ? OR roll LIKE ?) AND status='active'
            """, ('%' + keyword + '%', '%' + keyword + '%'))
            rows = cursor.fetchall()
            listbox.delete(0, tk.END)
            student_ids.clear()
            for row in rows:
                listbox.insert(tk.END, f"{row[0]}: {row[1]} (Father: {row[2]}, Roll: {row[3]}, Class: {row[4]})")
                student_ids.append(row[0])
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                sid = student_ids[idx]
                student_profile(sid)
        listbox.bind("<Double-Button-1>", on_double_click)
        tk.Button(win, text="Search", command=perform_search, bg='#3498db', fg='white').pack(pady=5)
        perform_search()
    
    def show_class_results():
        win = tk.Toplevel(root)
        win.title("Class-wise Results")
        win.geometry("600x500")
        tk.Label(win, text="Select Class:", font=("Arial", 10)).pack(pady=5)
        class_cb = ttk.Combobox(win, values=['Nursery', 'Prep'] + [str(i) for i in range(1, 11)], width=15)
        class_cb.pack()
        tk.Label(win, text="Exam Type:", font=("Arial", 10)).pack(pady=5)
        exam_cb = ttk.Combobox(win, values=['examination', 'monthly_test'], width=15)
        exam_cb.pack()
        tree = ttk.Treeview(win, columns=('Name', 'Total', 'Percentage', 'Remarks'), show='headings', height=15)
        tree.heading('Name', text='Name')
        tree.heading('Total', text='Total Obtained')
        tree.heading('Percentage', text='Percentage')
        tree.heading('Remarks', text='Remarks')
        tree.column('Name', width=150)
        tree.column('Total', width=100)
        tree.column('Percentage', width=100)
        tree.column('Remarks', width=80)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        def load_results():
            cls = class_cb.get()
            exam = exam_cb.get()
            if not cls or not exam:
                messagebox.showwarning("Error", "Select class and exam type")
                return
            cursor.execute("SELECT id, name FROM students WHERE class=? AND status='active'", (cls,))
            students = cursor.fetchall()
            tree.delete(*tree.get_children())
            for sid, name in students:
                cursor.execute("""
                    SELECT SUM(marks_obtained), SUM(total_marks)
                    FROM exam_results
                    WHERE student_id=? AND exam_type=?
                """, (sid, exam))
                total_obtained, total_max = cursor.fetchone()
                if total_obtained is None:
                    total_obtained = 0
                    total_max = 0
                percent = (total_obtained / total_max * 100) if total_max > 0 else 0
                remarks = "✅ PASS" if percent >= 33 else "❌ FAIL"
                tree.insert('', tk.END, values=(name, f"{total_obtained}/{total_max}", f"{percent:.1f}%", remarks))
        tk.Button(win, text="Load Results", command=load_results, bg='#3498db', fg='white').pack(pady=5)
    
    tk.Button(buttons_container, text="🔍 Search Student", command=open_search_window,
              bg='#3498db', fg='white', font=("Arial", 10), padx=15).pack(side=tk.LEFT, padx=2)
    tk.Button(buttons_container, text="📊 Class-wise Report", command=show_class_results,
              bg='#f39c12', fg='white', font=("Arial", 10), padx=15).pack(side=tk.LEFT, padx=2)
    
    # ================= CLASS SELECTION BUTTONS =================
    class_select_frame = tk.LabelFrame(main_frame, text="📚 Select Class", 
                                       font=("Arial", 12, "bold"), bg='white', padx=10, pady=10)
    class_select_frame.pack(fill=tk.X, pady=(0, 15))
    class_buttons_frame = tk.Frame(class_select_frame, bg='white')
    class_buttons_frame.pack(fill=tk.X, pady=5)
    classes = ['Nursery', 'Prep'] + [str(i) for i in range(1, 11)]
    current_class = tk.StringVar()
    row_frame = tk.Frame(class_buttons_frame, bg='white')
    row_frame.pack()
    for i, cls in enumerate(classes):
        if i > 0 and i % 6 == 0:
            row_frame = tk.Frame(class_buttons_frame, bg='white')
            row_frame.pack()
        btn = tk.Button(row_frame, text=cls, width=8, bg='#ecf0f1',
                       command=lambda c=cls: show_class_details(c))
        btn.pack(side=tk.LEFT, padx=2, pady=2)
    
    def print_class_list():
        cls = current_class.get()
        if not cls:
            messagebox.showinfo("No Class", "Please select a class first.")
            return
        content = get_class_list_content(cls)
        open_print_window(content, f"Class List - {cls}")
    tk.Button(class_select_frame, text="🖨️ Print Class List", command=print_class_list,
              bg='#95a5a6', fg='white', font=("Arial", 9), padx=15).pack(pady=5)
    
    # ================= STUDENT MANAGEMENT SECTION =================
    management_frame = tk.LabelFrame(main_frame, text="📋 Student Management", 
                                     font=("Arial", 12, "bold"), bg='white', padx=10, pady=10)
    management_frame.pack(fill=tk.X, pady=(0, 15))
    mgmt_buttons_frame = tk.Frame(management_frame, bg='white')
    mgmt_buttons_frame.pack(pady=5)
    
    def show_students_by_status(status, title):
        win = tk.Toplevel(root)
        win.title(title)
        win.geometry("700x400")
        tree = ttk.Treeview(win, show='headings', height=15)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        if status == 'left':
            columns = ('ID', 'Name', 'Father', 'Roll', 'Class', 'Leave Date')
            tree['columns'] = columns
            cursor.execute("SELECT id, name, father, roll, class, leave_date FROM students WHERE status='left'")
        else:
            columns = ('ID', 'Name', 'Father', 'Roll', 'Class', 'Completion Date')
            tree['columns'] = columns
            cursor.execute("SELECT id, name, father, roll, class, completion_date FROM students WHERE status='completed'")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        for row in cursor.fetchall():
            tree.insert('', tk.END, values=row)
        def on_double_click(event):
            item = tree.selection()[0]
            sid = tree.item(item, 'values')[0]
            student_profile(sid)
        tree.bind("<Double-Button-1>", on_double_click)
    
    def show_alumni():
        win = tk.Toplevel(root)
        win.title("Alumni")
        win.geometry("700x400")
        columns = ('ID', 'Name', 'Father', 'Roll', 'Class', 'Completion Year')
        tree = ttk.Treeview(win, columns=columns, show='headings', height=15)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        cursor.execute("SELECT id, name, father, roll, class, completion_date FROM students WHERE status='completed'")
        for row in cursor.fetchall():
            year = row[5][:4] if row[5] else ''
            tree.insert('', tk.END, values=(row[0], row[1], row[2], row[3], row[4], year))
        def on_double_click(event):
            item = tree.selection()[0]
            sid = tree.item(item, 'values')[0]
            student_profile(sid)
        tree.bind("<Double-Button-1>", on_double_click)
    
    def bulk_promotion():
        if current_class.get() != '1':
            messagebox.showinfo("Info", "Bulk promotion is only available for Class 1.")
            return
        cursor.execute("SELECT id, name FROM students WHERE class='1' AND status='active'")
        students = cursor.fetchall()
        promoted = []
        for sid, name in students:
            if has_passed_exam(sid):
                cursor.execute("UPDATE students SET class='2' WHERE id=?", (sid,))
                cursor.execute("INSERT INTO class_history (student_id, old_class, new_class, date) VALUES (?, '1', '2', ?)",
                               (sid, datetime.now().isoformat()))
                promoted.append(name)
        conn.commit()
        if promoted:
            messagebox.showinfo("Bulk Promotion", f"Promoted: {', '.join(promoted)}")
            if current_class.get() == '1':
                show_class_details('1')
        else:
            messagebox.showinfo("Bulk Promotion", "No eligible students found.")
    
    def show_notifications():
        cursor.execute("SELECT id, name FROM students WHERE class='1' AND status='active'")
        students = cursor.fetchall()
        pending = []
        for sid, name in students:
            if has_passed_exam(sid):
                pending.append(name)
        if pending:
            messagebox.showinfo("Notifications", f"Students in Class 1 who have passed but not yet promoted:\n{', '.join(pending)}")
        else:
            messagebox.showinfo("Notifications", "No pending promotions.")
    
    btn_left = tk.Button(mgmt_buttons_frame, text="Left Students", width=14,
                        command=lambda: show_students_by_status('left', "Students who left school"),
                        bg='#e67e22', fg='white')
    btn_left.grid(row=0, column=0, padx=2, pady=2)
    btn_completed = tk.Button(mgmt_buttons_frame, text="Completed Students", width=14,
                              command=lambda: show_students_by_status('completed', "Students who completed school"),
                              bg='#2ecc71', fg='white')
    btn_completed.grid(row=0, column=1, padx=2, pady=2)
    btn_alumni = tk.Button(mgmt_buttons_frame, text="Alumni", width=14,
                           command=show_alumni, bg='#9b59b6', fg='white')
    btn_alumni.grid(row=0, column=2, padx=2, pady=2)
    btn_bulk = tk.Button(mgmt_buttons_frame, text="Bulk Promotion", width=14,
                         command=bulk_promotion, bg='#1abc9c', fg='white')
    btn_bulk.grid(row=1, column=0, padx=2, pady=2)
    btn_notify = tk.Button(mgmt_buttons_frame, text="Notifications", width=14,
                           command=show_notifications, bg='#e74c3c', fg='white')
    btn_notify.grid(row=1, column=1, padx=2, pady=2)
    btn_refresh = tk.Button(mgmt_buttons_frame, text="Refresh", width=14,
                            command=lambda: show_class_details(current_class.get()) if current_class.get() else None,
                            bg='#3498db', fg='white')
    btn_refresh.grid(row=1, column=2, padx=2, pady=2)
    
    # ================= STUDENT LIST DISPLAY AREA =================
    display_frame = tk.LabelFrame(main_frame, text="👨‍🎓 Student List", 
                                  font=("Arial", 12, "bold"), bg='white', padx=10, pady=10)
    display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    strength_label = tk.Label(display_frame, text="Class Strength: 0", bg='white', 
                              font=("Arial", 10, "bold"), fg='#2c3e50')
    strength_label.pack(anchor='w', pady=5)
    tree_frame = tk.Frame(display_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True)
    columns = ('ID', 'Name', 'Father', 'Roll', 'Contact')
    student_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
    v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=student_tree.yview)
    h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=student_tree.xview)
    student_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    student_tree.grid(row=0, column=0, sticky='nsew')
    v_scrollbar.grid(row=0, column=1, sticky='ns')
    h_scrollbar.grid(row=1, column=0, sticky='ew')
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)
    for col in columns:
        student_tree.heading(col, text=col)
        student_tree.column(col, width=100)
    
    def show_profile(event):
        item = student_tree.selection()[0]
        sid = student_tree.item(item, 'values')[0]
        student_profile(sid)
    student_tree.bind("<Double-Button-1>", show_profile)
    
    def show_class_details(cls):
        current_class.set(cls)
        cursor.execute("SELECT COUNT(*) FROM students WHERE class=? AND status='active'", (cls,))
        count = cursor.fetchone()[0]
        strength_label.config(text=f"🏫 Class Strength: {count} student(s)")
        for row in student_tree.get_children():
            student_tree.delete(row)
        cursor.execute("SELECT id, name, father, roll, contact FROM students WHERE class=? AND status='active' ORDER BY roll", (cls,))
        for row in cursor.fetchall():
            student_tree.insert('', tk.END, values=row)
    
    # Helper Functions
    def get_class_list_content(cls):
        cursor.execute("SELECT id, name, father, roll, contact FROM students WHERE class=? AND status='active' ORDER BY roll", (cls,))
        rows = cursor.fetchall()
        content = f"{SCHOOL_NAME}\n\n"
        content += f"CLASS: {cls}\n"
        content += f"Total Students: {len(rows)}\n\n"
        content += "STUDENT LIST\n"
        content += "=" * 70 + "\n"
        content += f"{'ID':<5} {'Name':<20} {'Father':<20} {'Roll':<10} {'Contact':<15}\n"
        content += "-" * 70 + "\n"
        for row in rows:
            content += f"{row[0]:<5} {row[1]:<20} {row[2]:<20} {row[3]:<10} {row[4]:<15}\n"
        return content
    
    def get_profile_content(sid):
        cursor.execute("SELECT * FROM students WHERE id=?", (sid,))
        data = cursor.fetchone()
        if not data:
            return "Student not found"
        content = f"{SCHOOL_NAME}\n\n"
        content += "STUDENT PROFILE\n"
        content += "=" * 40 + "\n\n"
        content += f"ID: {data[0]}\n"
        content += f"Name: {data[1]}\n"
        content += f"Father: {data[2]}\n"
        content += f"Form-B: {data[3]}\n"
        content += f"Contact: {data[4]}\n"
        content += f"Roll: {data[5]}\n"
        content += f"Class: {data[6]}\n"
        content += f"Status: {data[7]}\n"
        if data[7] == 'left':
            content += f"Left on: {data[8]}\nReason: {data[9]}\n"
        elif data[7] == 'completed':
            content += f"Completed on: {data[10]}\n"
        content += "\nEXAM RESULTS\n"
        content += "=" * 40 + "\n"
        cursor.execute("SELECT exam_type, subject, marks_obtained, total_marks, date FROM exam_results WHERE student_id=? ORDER BY date DESC", (sid,))
        rows = cursor.fetchall()
        if not rows:
            content += "No exam results recorded.\n"
        else:
            for exam_type, subject, marks, total, date in rows:
                content += f"{exam_type} - {subject}: {marks}/{total} ({date[:10]})\n"
        return content
    
    def student_profile(sid):
        win = tk.Toplevel(root)
        win.title("Student Profile")
        win.geometry("800x600")
        cursor.execute("SELECT * FROM students WHERE id=?", (sid,))
        data = cursor.fetchone()
        if not data:
            messagebox.showerror("Error", "Student not found")
            win.destroy()
            return
        
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info Tab
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="Student Info")
        info_text = f"""
ID: {data[0]}
Name: {data[1]}
Father: {data[2]}
Form-B: {data[3]}
Contact: {data[4]}
Roll: {data[5]}
Class: {data[6]}
Status: {data[7]}
"""
        if data[7] == 'left':
            info_text += f"Left on: {data[8]}\nReason: {data[9]}\n"
        elif data[7] == 'completed':
            info_text += f"Completed on: {data[10]}\n"
        tk.Label(info_tab, text=info_text, font=("Courier", 10), justify=tk.LEFT).pack(pady=20)
        
        # Results Tab
        results_tab = ttk.Frame(notebook)
        notebook.add(results_tab, text="Exam Results")
        results_tree = ttk.Treeview(results_tab, columns=('Exam', 'Subject', 'Obtained', 'Total', 'Date'), show='headings', height=15)
        for col in results_tree['columns']:
            results_tree.heading(col, text=col)
            results_tree.column(col, width=100)
        results_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cursor.execute("SELECT exam_type, subject, marks_obtained, total_marks, date FROM exam_results WHERE student_id=? ORDER BY date DESC", (sid,))
        for row in cursor.fetchall():
            results_tree.insert('', tk.END, values=row)
        
        # History Tab (Class transfers)
        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="Class History")
        history_tree = ttk.Treeview(history_tab, columns=('Old Class', 'New Class', 'Date'), show='headings', height=10)
        history_tree.heading('Old Class', text='Old Class')
        history_tree.heading('New Class', text='New Class')
        history_tree.heading('Date', text='Transfer Date')
        history_tree.column('Old Class', width=100)
        history_tree.column('New Class', width=100)
        history_tree.column('Date', width=150)
        history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        cursor.execute("SELECT old_class, new_class, date FROM class_history WHERE student_id=? ORDER BY date DESC", (sid,))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                history_tree.insert('', tk.END, values=row)
        else:
            tk.Label(history_tab, text="No class transfer history available", font=("Arial", 10), fg='gray').pack(pady=20)
        
        # Buttons Frame
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)
        
        # Edit function (comprehensive)
        def edit_student():
            edit_win = tk.Toplevel(win)
            edit_win.title("Edit Student - " + data[1])
            edit_win.geometry("400x500")
            edit_win.configure(bg='white')
            
            # Scrollable canvas for edit window
            edit_canvas = tk.Canvas(edit_win, bg='white', highlightthickness=0)
            edit_scrollbar = ttk.Scrollbar(edit_win, orient="vertical", command=edit_canvas.yview)
            edit_canvas.configure(yscrollcommand=edit_scrollbar.set)
            edit_canvas.pack(side="left", fill="both", expand=True)
            edit_scrollbar.pack(side="right", fill="y")
            edit_scrollable = tk.Frame(edit_canvas, bg='white')
            edit_scrollable.bind("<Configure>", lambda e: edit_canvas.configure(scrollregion=edit_canvas.bbox("all")))
            edit_canvas.create_window((0, 0), window=edit_scrollable, anchor="nw")
            
            tk.Label(edit_scrollable, text="✏️ EDIT STUDENT RECORD", font=("Arial", 14, "bold"), bg='white', fg='#2c3e50').pack(pady=10)
            tk.Label(edit_scrollable, text="Student ID: " + str(data[0]), font=("Arial", 10), bg='white', fg='gray').pack(pady=5)
            
            fields_frame = tk.Frame(edit_scrollable, bg='white')
            fields_frame.pack(pady=10, padx=20)
            
            # Name
            tk.Label(fields_frame, text="Name *", bg='white', font=("Arial", 10, "bold")).grid(row=0, column=0, sticky='e', pady=8, padx=5)
            name_entry = tk.Entry(fields_frame, width=30, font=("Arial", 10))
            name_entry.insert(0, data[1])
            name_entry.grid(row=0, column=1, pady=8, padx=5)
            
            # Father
            tk.Label(fields_frame, text="Father Name *", bg='white', font=("Arial", 10, "bold")).grid(row=1, column=0, sticky='e', pady=8, padx=5)
            father_entry = tk.Entry(fields_frame, width=30, font=("Arial", 10))
            father_entry.insert(0, data[2])
            father_entry.grid(row=1, column=1, pady=8, padx=5)
            
            # Form-B
            tk.Label(fields_frame, text="Form-B", bg='white', font=("Arial", 10, "bold")).grid(row=2, column=0, sticky='e', pady=8, padx=5)
            formb_entry = tk.Entry(fields_frame, width=30, font=("Arial", 10))
            formb_entry.insert(0, data[3] if data[3] else "")
            formb_entry.grid(row=2, column=1, pady=8, padx=5)
            
            # Contact
            tk.Label(fields_frame, text="Contact", bg='white', font=("Arial", 10, "bold")).grid(row=3, column=0, sticky='e', pady=8, padx=5)
            contact_entry = tk.Entry(fields_frame, width=30, font=("Arial", 10))
            contact_entry.insert(0, data[4] if data[4] else "")
            contact_entry.grid(row=3, column=1, pady=8, padx=5)
            
            # Roll
            tk.Label(fields_frame, text="Roll Number *", bg='white', font=("Arial", 10, "bold")).grid(row=4, column=0, sticky='e', pady=8, padx=5)
            roll_entry = tk.Entry(fields_frame, width=30, font=("Arial", 10))
            roll_entry.insert(0, data[5])
            roll_entry.grid(row=4, column=1, pady=8, padx=5)
            
            # Class
            tk.Label(fields_frame, text="Class *", bg='white', font=("Arial", 10, "bold")).grid(row=5, column=0, sticky='e', pady=8, padx=5)
            class_var_edit = tk.StringVar(value=data[6])
            class_combo_edit = ttk.Combobox(fields_frame, textvariable=class_var_edit, width=27)
            class_combo_edit['values'] = ['Nursery', 'Prep'] + [str(i) for i in range(1, 11)]
            class_combo_edit.grid(row=5, column=1, pady=8, padx=5)
            
            # Status
            tk.Label(fields_frame, text="Status", bg='white', font=("Arial", 10, "bold")).grid(row=6, column=0, sticky='e', pady=8, padx=5)
            status_var = tk.StringVar(value=data[7])
            status_combo = ttk.Combobox(fields_frame, textvariable=status_var, width=27)
            status_combo['values'] = ['active', 'left', 'completed']
            status_combo.grid(row=6, column=1, pady=8, padx=5)
            
            # Status-specific fields
            status_fields_frame = tk.Frame(fields_frame, bg='white')
            status_fields_frame.grid(row=7, column=0, columnspan=2, pady=10)
            leave_date_entry = None
            leave_reason_entry = None
            completion_date_entry = None
            
            def update_status_fields(*args):
                for widget in status_fields_frame.winfo_children():
                    widget.destroy()
                status = status_var.get()
                if status == 'left':
                    tk.Label(status_fields_frame, text="Leave Date:", bg='white', font=("Arial", 9)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
                    nonlocal leave_date_entry
                    leave_date_entry = tk.Entry(status_fields_frame, width=25)
                    leave_date_entry.grid(row=0, column=1, padx=5, pady=5)
                    leave_date_entry.insert(0, data[8][:10] if data[8] else datetime.now().strftime("%Y-%m-%d"))
                    tk.Label(status_fields_frame, text="Reason:", bg='white', font=("Arial", 9)).grid(row=1, column=0, sticky='e', padx=5, pady=5)
                    nonlocal leave_reason_entry
                    leave_reason_entry = tk.Entry(status_fields_frame, width=25)
                    leave_reason_entry.grid(row=1, column=1, padx=5, pady=5)
                    if data[9]:
                        leave_reason_entry.insert(0, data[9])
                elif status == 'completed':
                    tk.Label(status_fields_frame, text="Completion Date:", bg='white', font=("Arial", 9)).grid(row=0, column=0, sticky='e', padx=5, pady=5)
                    nonlocal completion_date_entry
                    completion_date_entry = tk.Entry(status_fields_frame, width=25)
                    completion_date_entry.grid(row=0, column=1, padx=5, pady=5)
                    completion_date_entry.insert(0, data[10][:10] if data[10] else datetime.now().strftime("%Y-%m-%d"))
            
            status_var.trace('w', update_status_fields)
            update_status_fields()
            
            def update_student():
                name = name_entry.get().strip()
                father = father_entry.get().strip()
                roll = roll_entry.get().strip()
                student_class = class_var_edit.get().strip()
                if not name or not father:
                    messagebox.showwarning("Error", "Name and Father Name are required!")
                    return
                if not roll:
                    messagebox.showwarning("Error", "Roll Number is required!")
                    return
                if not student_class:
                    messagebox.showwarning("Error", "Class is required!")
                    return
                try:
                    cursor.execute("SELECT id FROM students WHERE roll=? AND id!=?", (roll, sid))
                    if cursor.fetchone():
                        messagebox.showerror("Error", f"Roll number '{roll}' already used by another student!")
                        return
                    cursor.execute("""
                        UPDATE students 
                        SET name=?, father=?, form_b=?, contact=?, roll=?, class=?, status=?
                        WHERE id=?
                    """, (name, father, formb_entry.get().strip(), contact_entry.get().strip(), 
                          roll, student_class, status_var.get(), sid))
                    status = status_var.get()
                    if status == 'left':
                        cursor.execute("UPDATE students SET leave_date=?, leave_reason=? WHERE id=?",
                                     (leave_date_entry.get() if leave_date_entry else None,
                                      leave_reason_entry.get() if leave_reason_entry else None, sid))
                    elif status == 'completed':
                        cursor.execute("UPDATE students SET completion_date=? WHERE id=?",
                                     (completion_date_entry.get() if completion_date_entry else None, sid))
                    else:
                        cursor.execute("UPDATE students SET leave_date=NULL, leave_reason=NULL, completion_date=NULL WHERE id=?", (sid,))
                    conn.commit()
                    messagebox.showinfo("Success", "Student record updated successfully!")
                    edit_win.destroy()
                    win.destroy()
                    if current_class.get() == student_class:
                        show_class_details(student_class)
                    elif current_class.get() == data[6]:
                        show_class_details(data[6])
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Database error occurred!")
            
            button_frame = tk.Frame(edit_scrollable, bg='white')
            button_frame.pack(pady=20)
            tk.Button(button_frame, text="💾 Save Changes", command=update_student, 
                      bg='#27ae60', fg='white', font=("Arial", 10, "bold"), padx=20, pady=5).pack(side=tk.LEFT, padx=10)
            tk.Button(button_frame, text="❌ Cancel", command=edit_win.destroy, 
                      bg='#e74c3c', fg='white', font=("Arial", 10, "bold"), padx=20, pady=5).pack(side=tk.LEFT, padx=10)
            edit_win.bind('<Return>', lambda e: update_student())
        
        def delete_student():
            if messagebox.askyesno("Confirm", "Delete this student and all related records?"):
                cursor.execute("DELETE FROM students WHERE id=?", (sid,))
                cursor.execute("DELETE FROM exam_results WHERE student_id=?", (sid,))
                cursor.execute("DELETE FROM class_history WHERE student_id=?", (sid,))
                conn.commit()
                messagebox.showinfo("Deleted", "Student removed")
                win.destroy()
                if current_class.get():
                    show_class_details(current_class.get())
        
        def transfer_class():
            transfer_win = tk.Toplevel(win)
            transfer_win.title(f"Transfer Student - {data[1]}")
            transfer_win.geometry("350x250")
            transfer_win.configure(bg='white')
            tk.Label(transfer_win, text="🔄 TRANSFER STUDENT", font=("Arial", 12, "bold"), bg='white', fg='#2c3e50').pack(pady=10)
            tk.Label(transfer_win, text=f"Student: {data[1]}", bg='white', font=("Arial", 10)).pack(pady=5)
            tk.Label(transfer_win, text=f"Current Class: {data[6]}", bg='white', font=("Arial", 10, "bold"), fg='blue').pack(pady=5)
            tk.Label(transfer_win, text="Select New Class:", bg='white', font=("Arial", 10)).pack(pady=10)
            new_class_var = tk.StringVar()
            class_combo_transfer = ttk.Combobox(transfer_win, textvariable=new_class_var, width=20)
            class_combo_transfer['values'] = ['Nursery', 'Prep'] + [str(i) for i in range(1, 11)]
            class_combo_transfer.pack(pady=5)
            def confirm_transfer():
                new_class = new_class_var.get().strip()
                if not new_class:
                    messagebox.showwarning("Error", "Please select a class")
                    return
                if new_class == data[6]:
                    messagebox.showinfo("Info", "Student is already in this class")
                    transfer_win.destroy()
                    return
                if messagebox.askyesno("Confirm Transfer", f"Transfer {data[1]} from {data[6]} to {new_class}?\n\nThis will update the student's class record."):
                    cursor.execute("UPDATE students SET class=? WHERE id=?", (new_class, sid))
                    cursor.execute("INSERT INTO class_history (student_id, old_class, new_class, date) VALUES (?, ?, ?, ?)",
                                   (sid, data[6], new_class, datetime.now().isoformat()))
                    conn.commit()
                    messagebox.showinfo("Success", f"Student transferred from {data[6]} to {new_class}")
                    transfer_win.destroy()
                    win.destroy()
                    if current_class.get() == data[6] or current_class.get() == new_class:
                        show_class_details(current_class.get())
            tk.Button(transfer_win, text="✓ Confirm Transfer", command=confirm_transfer,
                      bg='#3498db', fg='white', font=("Arial", 10, "bold"), padx=20, pady=5).pack(pady=10)
            tk.Button(transfer_win, text="Cancel", command=transfer_win.destroy,
                      bg='#95a5a6', fg='white', padx=20).pack(pady=5)
        
        def mark_left():
            reason = simpledialog.askstring("Reason", "Reason for leaving:")
            if reason is not None:
                cursor.execute("UPDATE students SET status='left', leave_date=?, leave_reason=? WHERE id=?",
                             (datetime.now().isoformat(), reason, sid))
                conn.commit()
                messagebox.showinfo("Updated", "Student marked as left.")
                win.destroy()
                if current_class.get() == data[6]:
                    show_class_details(current_class.get())
        
        def mark_completed():
            if messagebox.askyesno("Confirm Completion", f"Mark {data[1]} as completed?\n\nThis means the student has finished their education at this school."):
                cursor.execute("UPDATE students SET status='completed', completion_date=? WHERE id=?",
                             (datetime.now().isoformat(), sid))
                conn.commit()
                messagebox.showinfo("Success", f"{data[1]} marked as completed.")
                win.destroy()
                if current_class.get() == data[6]:
                    show_class_details(current_class.get())
        
        def promote_student():
            if can_promote(sid, data[6]):
                cursor.execute("UPDATE students SET class='2' WHERE id=?", (sid,))
                cursor.execute("INSERT INTO class_history (student_id, old_class, new_class, date) VALUES (?, ?, ?, ?)",
                               (sid, data[6], '2', datetime.now().isoformat()))
                conn.commit()
                messagebox.showinfo("Promotion", f"{data[1]} promoted to Class 2.")
                win.destroy()
                if current_class.get() == '1':
                    show_class_details('1')
            else:
                messagebox.showerror("Cannot Promote", "Student has not passed the examination.")
        
        def print_certificate():
            cert = f"{SCHOOL_NAME}\n\n"
            cert += "CERTIFICATE OF COMPLETION\n"
            cert += "========================\n\n"
            cert += f"This is to certify that {data[1]}, son/daughter of {data[2]},\n"
            cert += f"has successfully completed his/her education at this school.\n"
            cert += f"Date: {data[10]}\n"
            cert += f"Roll No: {data[5]}\n\n"
            cert += "Signed: ___________________\n"
            cert += "Headmaster"
            open_print_window(cert, f"Certificate - {data[1]}")
        
        # Buttons
        tk.Button(btn_frame, text="✏️ Edit", command=edit_student, bg='#3498db', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🔄 Transfer", command=transfer_class, bg='#f39c12', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Delete", command=delete_student, bg='#e74c3c', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🖨️ Print Profile", 
                 command=lambda: open_print_window(get_profile_content(sid), f"Profile - {data[1]}"), 
                 bg='#95a5a6', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        
        if data[7] == 'active' and data[6] == '1':
            tk.Button(btn_frame, text="⭐ Promote to Class 2", command=promote_student,
                     bg='#1abc9c', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        
        if data[7] == 'active':
            tk.Button(btn_frame, text="🚪 Mark as Left", command=mark_left,
                     bg='#e67e22', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="✓ Mark as Completed", command=mark_completed,
                     bg='#2ecc71', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
        
        if data[7] == 'completed':
            tk.Button(btn_frame, text="📜 Print Certificate", command=print_certificate,
                     bg='#9b59b6', fg='white', padx=10).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()

# ================= LOGIN UI =================
login_win = tk.Tk()
login_win.title("Login - School Management System")
login_win.geometry("350x250")
login_win.configure(bg='#ecf0f1')

logo_img = load_logo()
if logo_img:
    logo_label = tk.Label(login_win, image=logo_img, bg='#ecf0f1')
    logo_label.image = logo_img
    logo_label.pack(pady=10)
else:
    tk.Label(login_win, text=DEFAULT_LOGO_TEXT, font=("Arial", 40), bg='#ecf0f1').pack(pady=10)

tk.Label(login_win, text="School Management System", font=("Arial", 12, "bold"), 
         bg='#ecf0f1').pack(pady=5)
tk.Label(login_win, text="Username", bg='#ecf0f1').pack(pady=5)
user_entry = tk.Entry(login_win, font=("Arial", 10))
user_entry.pack(pady=5)

tk.Label(login_win, text="Password", bg='#ecf0f1').pack(pady=5)
pass_entry = tk.Entry(login_win, show="*", font=("Arial", 10))
pass_entry.pack(pady=5)

tk.Button(login_win, text="Login", command=login, bg='#3498db', fg='white', 
          font=("Arial", 10, "bold"), padx=20).pack(pady=10)

login_win.mainloop()
conn.close()
