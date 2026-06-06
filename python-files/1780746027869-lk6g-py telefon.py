
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import re

class ContactApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Контакты")
        self.root.geometry("500x700")
        self.root.configure(bg='#F5F5F5')
        self.root.resizable(False, False)
        
        # Инициализация базы данных
        self.init_database()
        
        # Переменные
        self.search_var = tk.StringVar()
        self.fio_var = tk.StringVar()
        self.phone1_var = tk.StringVar()
        self.phone2_var = tk.StringVar()
        self.phone3_var = tk.StringVar()
        self.work_var = tk.StringVar()
        self.birth_var = tk.StringVar()
        
        self.current_id = None
        
        self.setup_ui()
        self.load_contacts()
    
    def init_database(self):
        self.conn = sqlite3.connect('contacts.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                phone1 TEXT,
                phone2 TEXT,
                phone3 TEXT,
                work TEXT,
                birth TEXT
            )
        ''')
        self.conn.commit()
    
    def setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg='#4A90D9', height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="Контакты", font=('Segoe UI', 24, 'bold'), 
                bg='#4A90D9', fg='white').pack(pady=20)
        
        # Поиск
        search_frame = tk.Frame(self.root, bg='#F5F5F5')
        search_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                               font=('Segoe UI', 12), relief='flat', bg='white',
                               fg='#333333')
        search_entry.pack(side='left', fill='x', expand=True, ipady=8)
        search_entry.insert(0, "🔍 Поиск...")
        
        search_entry.bind('<FocusIn>', self.on_search_focus_in)
        search_entry.bind('<FocusOut>', self.on_search_focus_out)
        search_entry.bind('<KeyRelease>', self.on_search)
        
        # Список контактов
        list_frame = tk.Frame(self.root, bg='white', relief='flat', bd=0)
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.contacts_listbox = tk.Listbox(list_frame, font=('Segoe UI', 11),
                                           bg='white', fg='#333333', relief='flat',
                                           selectbackground='#4A90D9', selectforeground='white',
                                           height=10, bd=0, highlightthickness=0)
        self.contacts_listbox.pack(side='left', fill='both', expand=True)
        self.contacts_listbox.bind('<<ListboxSelect>>', self.on_select_contact)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', 
                                 command=self.contacts_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.contacts_listbox.config(yscrollcommand=scrollbar.set)
        
        # Форма редактирования
        form_frame = tk.Frame(self.root, bg='#F5F5F5')
        form_frame.pack(fill='x', padx=20, pady=10)
        
        fields = [
            ("ФИО", self.fio_var),
            ("Телефон 1", self.phone1_var),
            ("Телефон 2", self.phone2_var),
            ("Телефон 3", self.phone3_var),
            ("Место работы", self.work_var),
            ("Дата рождения", self.birth_var)
        ]
        
        self.entries = {}
        
        for i, (label, var) in enumerate(fields):
            frame = tk.Frame(form_frame, bg='#F5F5F5')
            frame.pack(fill='x', pady=3)
            
            tk.Label(frame, text=label, font=('Segoe UI', 10), 
                    bg='#F5F5F5', fg='#888888', anchor='w', width=12).pack(side='left')
            
            entry = tk.Entry(frame, textvariable=var, font=('Segoe UI', 11),
                           relief='flat', bg='white', fg='#333333')
            entry.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 5))
            self.entries[label] = entry
        
        # Кнопки
        buttons_frame = tk.Frame(self.root, bg='#F5F5F5')
        buttons_frame.pack(fill='x', padx=20, pady=15)
        
        # Кнопка Добавить
        add_btn = tk.Button(buttons_frame, text="+ Добавить", command=self.add_contact,
                           font=('Segoe UI', 11, 'bold'), bg='#4CAF50', fg='white',
                           relief='flat', cursor='hand2')
        add_btn.pack(side='left', padx=(0, 5), ipadx=10, ipady=8)
        
        # Кнопка Обновить
        update_btn = tk.Button(buttons_frame, text="✎ Обновить", command=self.update_contact,
                              font=('Segoe UI', 11, 'bold'), bg='#2196F3', fg='white',
                              relief='flat', cursor='hand2')
        update_btn.pack(side='left', padx=5, ipadx=10, ipady=8)
        
        # Кнопка Удалить
        delete_btn = tk.Button(buttons_frame, text="✕ Удалить", command=self.delete_contact,
                              font=('Segoe UI', 11, 'bold'), bg='#F44336', fg='white',
                              relief='flat', cursor='hand2')
        delete_btn.pack(side='left', padx=5, ipadx=10, ipady=8)
        
        # Кнопка Очистить
        clear_btn = tk.Button(buttons_frame, text="↺ Очистить", command=self.clear_form,
                             font=('Segoe UI', 11, 'bold'), bg='#9E9E9E', fg='white',
                             relief='flat', cursor='hand2')
        clear_btn.pack(side='left', padx=5, ipadx=10, ipady=8)
        
        # Кнопка Выход
        exit_btn = tk.Button(self.root, text="Выход", command=self.exit_app,
                            font=('Segoe UI', 12, 'bold'), bg='#607D8B', fg='white',
                            relief='flat', cursor='hand2')
        exit_btn.pack(side='bottom', fill='x', padx=20, pady=15, ipady=10)
        
        # Применяем стили для кнопок при наведении
        for btn in [add_btn, update_btn, delete_btn, clear_btn, exit_btn]:
            self.apply_hover_effect(btn)
    
    def apply_hover_effect(self, button):
        original_color = button.cget('bg')
        hover_color = self.darken_color(original_color)
        
        def on_enter(event):
            button.config(bg=hover_color)
        
        def on_leave(event):
            button.config(bg=original_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def darken_color(self, hex_color):
        """Затемняет цвет для эффекта наведения"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 30)
        g = max(0, g - 30)
        b = max(0, b - 30)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def on_search_focus_in(self, event):
        if self.search_var.get() == "🔍 Поиск...":
            self.search_var.set("")
    
    def on_search_focus_out(self, event):
        if not self.search_var.get():
            self.search_var.set("🔍 Поиск...")
    
    def on_search(self, event):
        search_text = self.search_var.get()
        if search_text and search_text != "🔍 Поиск...":
            self.search_contacts(search_text)
        else:
            self.load_contacts()
    
    def load_contacts(self):
        self.contacts_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT id, fio FROM contacts ORDER BY fio")
        contacts = self.cursor.fetchall()
        
        for contact_id, fio in contacts:
            self.contacts_listbox.insert(tk.END, f"{fio}")
            # Сохраняем ID в атрибуте элемента
            self.contacts_listbox.set(self.contacts_listbox.size() - 1, contact_id)
    
    def search_contacts(self, search_text):
        self.contacts_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT id, fio FROM contacts WHERE fio LIKE ? ORDER BY fio", 
                           (f'%{search_text}%',))
        contacts = self.cursor.fetchall()
        
        for contact_id, fio in contacts:
            self.contacts_listbox.insert(tk.END, f"{fio}")
    
    def on_select_contact(self, event):
        selection = self.contacts_listbox.curselection()
        if not selection:
            return
        
        selected_text = self.contacts_listbox.get(selection[0])
        
        # Поиск контакта по ФИО
        self.cursor.execute("SELECT * FROM contacts WHERE fio = ?", (selected_text,))
        contact = self.cursor.fetchone()
        
        if contact:
            self.current_id = contact[0]
            self.fio_var.set(contact[1])
            self.phone1_var.set(contact[2] if contact[2] else "")
            self.phone2_var.set(contact[3] if contact[3] else "")
            self.phone3_var.set(contact[4] if contact[4] else "")
            self.work_var.set(contact[5] if contact[5] else "")
            self.birth_var.set(contact[6] if contact[6] else "")
    
    def validate_form(self):
        if not self.fio_var.get().strip():
            messagebox.showwarning("Предупреждение", "Поле ФИО обязательно для заполнения!")
            return False
        return True
    
    def add_contact(self):
        if not self.validate_form():
            return
        
        try:
            self.cursor.execute('''
                INSERT INTO contacts (fio, phone1, phone2, phone3, work, birth)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.fio_var.get().strip(),
                self.phone1_var.get().strip(),
                self.phone2_var.get().strip(),
                self.phone3_var.get().strip(),
                self.work_var.get().strip(),
                self.birth_var.get().strip()
            ))
            self.conn.commit()
            messagebox.showinfo("Успех", "Контакт добавлен!")
            self.clear_form()
            self.load_contacts()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить контакт: {str(e)}")
    
    def update_contact(self):
        if not self.current_id:
            messagebox.showwarning("Предупреждение", "Выберите контакт для редактирования!")
            return
        
        if not self.validate_form():
            return
        
        try:
            self.cursor.execute('''
                UPDATE contacts 
                SET fio=?, phone1=?, phone2=?, phone3=?, work=?, birth=?
                WHERE id=?
            ''', (
                self.fio_var.get().strip(),
                self.phone1_var.get().strip(),
                self.phone2_var.get().strip(),
                self.phone3_var.get().strip(),
                self.work_var.get().strip(),
                self.birth_var.get().strip(),
                self.current_id
            ))
            self.conn.commit()
            messagebox.showinfo("Успех", "Контакт обновлен!")
            self.clear_form()
            self.load_contacts()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить контакт: {str(e)}")
    
    def delete_contact(self):
        if not self.current_id:
            messagebox.showwarning("Предупреждение", "Выберите контакт для удаления!")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот контакт?"):
            try:
                self.cursor.execute("DELETE FROM contacts WHERE id=?", (self.current_id,))
                self.conn.commit()
                messagebox.showinfo("Успех", "Контакт удален!")
                self.clear_form()
                self.load_contacts()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить контакт: {str(e)}")
    
    def clear_form(self):
        self.current_id = None
        self.fio_var.set("")
        self.phone1_var.set("")
        self.phone2_var.set("")
        self.phone3_var.set("")
        self.work_var.set("")
        self.birth_var.set("")
        self.contacts_listbox.selection_clear(0, tk.END)
    
    def exit_app(self):
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.conn.close()
            self.root.quit()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    root = tk.Tk()
    
    # Настройка стиля приложения
    style = ttk.Style()
    style.theme_use('clam')
    
    app = ContactApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()