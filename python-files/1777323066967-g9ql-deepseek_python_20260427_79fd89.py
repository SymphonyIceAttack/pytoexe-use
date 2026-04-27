# КОНТАКТЫ v1.0 - Простая программа
# Сохраните этот файл и запустите двойным щелчком

import json
import os
from tkinter import *
from tkinter import ttk, messagebox, filedialog

class ContactsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📇 Мои контакты")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # Файл для хранения
        self.data_file = "my_contacts.json"
        self.contacts = self.load_contacts()
        
        # Интерфейс
        self.setup_ui()
        self.refresh_list()
    
    def load_contacts(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_contacts(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.contacts, f, ensure_ascii=False, indent=2)
    
    def setup_ui(self):
        # Верхняя панель
        top = Frame(self.root)
        top.pack(fill=X, padx=10, pady=5)
        
        Label(top, text="Имя:").pack(side=LEFT, padx=5)
        self.name_entry = Entry(top, width=20)
        self.name_entry.pack(side=LEFT, padx=5)
        
        Label(top, text="Телефон:").pack(side=LEFT, padx=5)
        self.phone_entry = Entry(top, width=20)
        self.phone_entry.pack(side=LEFT, padx=5)
        
        Button(top, text="➕ Добавить", command=self.add_contact, bg="#4CAF50", fg="white").pack(side=LEFT, padx=5)
        Button(top, text="📂 Импорт", command=self.import_file, bg="#2196F3", fg="white").pack(side=LEFT, padx=5)
        Button(top, text="💾 Экспорт", command=self.export_file, bg="#FF9800", fg="white").pack(side=LEFT, padx=5)
        
        # Поиск
        search_frame = Frame(self.root)
        search_frame.pack(fill=X, padx=10, pady=5)
        
        Label(search_frame, text="🔍 Поиск:").pack(side=LEFT)
        self.search_entry = Entry(search_frame, width=40)
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.refresh_list())
        
        # Список контактов
        self.tree = ttk.Treeview(self.root, columns=("name", "phone"), show="headings", height=20)
        self.tree.heading("name", text="Имя")
        self.tree.heading("phone", text="Телефон")
        self.tree.column("name", width=300)
        self.tree.column("phone", width=200)
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Кнопки управления
        bottom = Frame(self.root)
        bottom.pack(fill=X, padx=10, pady=5)
        
        Button(bottom, text="✏️ Редактировать", command=self.edit_contact, bg="#FFC107").pack(side=LEFT, padx=5)
        Button(bottom, text="🗑️ Удалить", command=self.delete_contact, bg="#f44336", fg="white").pack(side=LEFT, padx=5)
        Button(bottom, text="📋 Копировать телефон", command=self.copy_phone, bg="#9C27B0", fg="white").pack(side=LEFT, padx=5)
        
        Label(bottom, text="", relief=SUNKEN, anchor=W).pack(side=RIGHT, fill=X, expand=True)
        
        # Статус
        self.status_var = StringVar(value="Готов к работе")
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)
    
    def refresh_list(self):
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Фильтруем по поиску
        search = self.search_entry.get().lower()
        filtered = [c for c in self.contacts if search in c['name'].lower() or search in c['phone']]
        
        # Добавляем в список
        for contact in filtered:
            self.tree.insert("", END, values=(contact['name'], contact['phone']))
        
        self.status_var.set(f"📊 Всего: {len(filtered)} из {len(self.contacts)} контактов")
    
    def add_contact(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        
        if not name or not phone:
            messagebox.showwarning("Внимание", "Заполните имя и телефон")
            return
        
        # Проверка на дубликат
        for c in self.contacts:
            if c['phone'] == phone:
                if messagebox.askyesno("Дубликат", f"Номер {phone} уже есть в базе. Обновить имя?"):
                    c['name'] = name
                    self.save_contacts()
                    self.refresh_list()
                return
        
        self.contacts.append({'name': name, 'phone': phone})
        self.save_contacts()
        self.name_entry.delete(0, END)
        self.phone_entry.delete(0, END)
        self.refresh_list()
        messagebox.showinfo("Успех", "Контакт добавлен")
    
    def edit_contact(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите контакт")
            return
        
        old_name, old_phone = self.tree.item(selected[0])['values']
        
        dialog = Toplevel(self.root)
        dialog.title("Редактирование")
        dialog.geometry("300x150")
        
        Label(dialog, text="Имя:").pack(pady=5)
        name_entry = Entry(dialog, width=30)
        name_entry.insert(0, old_name)
        name_entry.pack()
        
        Label(dialog, text="Телефон:").pack(pady=5)
        phone_entry = Entry(dialog, width=30)
        phone_entry.insert(0, old_phone)
        phone_entry.pack()
        
        def save():
            new_name = name_entry.get()
            new_phone = phone_entry.get()
            
            # Обновляем в списке
            for c in self.contacts:
                if c['phone'] == old_phone:
                    c['name'] = new_name
                    c['phone'] = new_phone
                    break
            
            self.save_contacts()
            self.refresh_list()
            dialog.destroy()
            messagebox.showinfo("Успех", "Контакт обновлён")
        
        Button(dialog, text="Сохранить", command=save).pack(pady=10)
    
    def delete_contact(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите контакт")
            return
        
        name, phone = self.tree.item(selected[0])['values']
        
        if messagebox.askyesno("Удаление", f"Удалить контакт {name} ({phone})?"):
            self.contacts = [c for c in self.contacts if c['phone'] != phone]
            self.save_contacts()
            self.refresh_list()
    
    def copy_phone(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите контакт")
            return
        
        phone = self.tree.item(selected[0])['values'][1]
        self.root.clipboard_clear()
        self.root.clipboard_append(phone)
        messagebox.showinfo("Скопировано", f"Номер {phone} скопирован в буфер")
    
    def import_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
                    for item in imported:
                        if 'name' in item and 'phone' in item:
                            self.contacts.append(item)
            else:
                # Пробуем импортировать Excel
                import pandas as pd
                df = pd.read_excel(filepath)
                
                # Ищем колонки с именем и телефоном
                name_col = None
                phone_col = None
                
                for col in df.columns:
                    col_lower = col.lower()
                    if 'имя' in col_lower or 'name' in col_lower or 'фио' in col_lower:
                        name_col = col
                    if 'телефон' in col_lower or 'phone' in col_lower or 'тел' in col_lower:
                        phone_col = col
                
                if name_col and phone_col:
                    for _, row in df.iterrows():
                        name = str(row[name_col]) if pd.notna(row[name_col]) else ""
                        phone = str(row[phone_col]) if pd.notna(row[phone_col]) else ""
                        if name and phone and name != 'nan' and phone != 'nan':
                            self.contacts.append({'name': name, 'phone': phone})
                else:
                    messagebox.showerror("Ошибка", "Не найдены колонки с именем и телефоном")
                    return
            
            self.save_contacts()
            self.refresh_list()
            messagebox.showinfo("Успех", f"Импортировано контактов: {len(self.contacts)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать: {str(e)}")
    
    def export_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.json'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            
            elif filepath.endswith('.xlsx'):
                import pandas as pd
                df = pd.DataFrame(self.contacts)
                df.to_excel(filepath, index=False)
            
            elif filepath.endswith('.csv'):
                import pandas as pd
                df = pd.DataFrame(self.contacts)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("Успех", f"Экспортировано в {filepath}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {str(e)}")

if __name__ == "__main__":
    root = Tk()
    app = ContactsApp(root)
    root.mainloop()