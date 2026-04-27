# КОНТАКТЫ С EXCEL - РАБОЧАЯ ВЕРСИЯ
import json
import os
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

# ПРОВЕРКА И УСТАНОВКА БИБЛИОТЕК
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    # Показываем инструкцию по установке
    import subprocess
    import sys
    
    def install_pandas():
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"])
            messagebox.showinfo("Установка", "Библиотеки успешно установлены! Перезапустите программу.")
            return True
        except:
            messagebox.showerror("Ошибка", 
                "Не удалось установить библиотеки.\n\n"
                "Установите вручную:\n"
                "Откройте командную строку (Win+R → cmd)\n"
                "Введите: pip install pandas openpyxl")
            return False

class ContactsApp:
    def __init__(self):
        self.root = Tk()
        self.root.title("📇 База контактов с Excel")
        self.root.geometry("900x600")
        
        self.data_file = "contacts.xlsx"  # Теперь сохраняем в Excel
        self.load_contacts()
        self.setup_ui()
        self.refresh_list()
        
        self.root.mainloop()
    
    def load_contacts(self):
        """Загружает контакты из Excel файла"""
        if PANDAS_AVAILABLE and os.path.exists(self.data_file):
            try:
                df = pd.read_excel(self.data_file)
                self.contacts = df.to_dict('records')
            except:
                self.contacts = []
        else:
            self.contacts = []
    
    def save_contacts(self):
        """Сохраняет контакты в Excel файл"""
        if PANDAS_AVAILABLE:
            df = pd.DataFrame(self.contacts)
            df.to_excel(self.data_file, index=False)
        else:
            # Если pandas нет, сохраняем в JSON
            with open("contacts_backup.json", 'w', encoding='utf-8') as f:
                json.dump(self.contacts, f, ensure_ascii=False, indent=2)
    
    def setup_ui(self):
        # Верхняя панель
        top = Frame(self.root)
        top.pack(pady=10, padx=10, fill=X)
        
        # Кнопки управления
        btn_frame = Frame(top)
        btn_frame.pack(fill=X)
        
        Button(btn_frame, text="📂 Импорт Excel", command=self.import_excel,
               bg="#2196F3", fg="white", font=("Arial", 10), padx=15, pady=5).pack(side=LEFT, padx=5)
        
        Button(btn_frame, text="💾 Сохранить в Excel", command=self.save_contacts,
               bg="#4CAF50", fg="white", font=("Arial", 10), padx=15, pady=5).pack(side=LEFT, padx=5)
        
        Button(btn_frame, text="📤 Экспорт", command=self.export_menu,
               bg="#FF9800", fg="white", font=("Arial", 10), padx=15, pady=5).pack(side=LEFT, padx=5)
        
        if not PANDAS_AVAILABLE:
            Button(btn_frame, text="⚠️ Установить библиотеки", command=install_pandas,
                   bg="#f44336", fg="white", font=("Arial", 9), padx=10, pady=5).pack(side=LEFT, padx=5)
        
        # Форма добавления
        add_frame = LabelFrame(self.root, text="Добавление контакта", font=("Arial", 10, "bold"))
        add_frame.pack(pady=10, padx=10, fill=X)
        
        Label(add_frame, text="Имя:", font=("Arial", 10)).pack(side=LEFT, padx=5)
        self.name_entry = Entry(add_frame, width=25, font=("Arial", 10))
        self.name_entry.pack(side=LEFT, padx=5)
        
        Label(add_frame, text="Телефон:", font=("Arial", 10)).pack(side=LEFT, padx=5)
        self.phone_entry = Entry(add_frame, width=25, font=("Arial", 10))
        self.phone_entry.pack(side=LEFT, padx=5)
        
        Label(add_frame, text="Регион:", font=("Arial", 10)).pack(side=LEFT, padx=5)
        self.region_entry = Entry(add_frame, width=15, font=("Arial", 10))
        self.region_entry.pack(side=LEFT, padx=5)
        
        Button(add_frame, text="➕ Добавить", command=self.add_contact,
               bg="#4CAF50", fg="white", font=("Arial", 10), padx=10).pack(side=LEFT, padx=10)
        
        # Поиск
        search_frame = Frame(self.root)
        search_frame.pack(pady=5, padx=10, fill=X)
        
        Label(search_frame, text="🔍 Поиск:", font=("Arial", 10)).pack(side=LEFT)
        self.search_var = StringVar()
        self.search_entry = Entry(search_frame, textvariable=self.search_var, width=50, font=("Arial", 10))
        self.search_entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        self.search_var.trace('w', lambda *args: self.refresh_list())
        
        # Таблица
        table_frame = Frame(self.root)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        scroll_y = Scrollbar(table_frame)
        scroll_y.pack(side=RIGHT, fill=Y)
        
        scroll_x = Scrollbar(table_frame, orient=HORIZONTAL)
        scroll_x.pack(side=BOTTOM, fill=X)
        
        self.tree = ttk.Treeview(table_frame, columns=("name", "phone", "region", "date"), 
                                  show="headings", 
                                  yscrollcommand=scroll_y.set,
                                  xscrollcommand=scroll_x.set)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        self.tree.heading("name", text="Имя")
        self.tree.heading("phone", text="Телефон")
        self.tree.heading("region", text="Регион")
        self.tree.heading("date", text="Дата добавления")
        
        self.tree.column("name", width=250)
        self.tree.column("phone", width=150)
        self.tree.column("region", width=150)
        self.tree.column("date", width=150)
        
        self.tree.pack(fill=BOTH, expand=True)
        
        # Кнопки управления
        bottom = Frame(self.root)
        bottom.pack(pady=10, padx=10, fill=X)
        
        Button(bottom, text="✏️ Редактировать", command=self.edit_contact,
               bg="#FFC107", font=("Arial", 10), padx=10).pack(side=LEFT, padx=5)
        
        Button(bottom, text="🗑️ Удалить", command=self.delete_contact,
               bg="#f44336", fg="white", font=("Arial", 10), padx=10).pack(side=LEFT, padx=5)
        
        Button(bottom, text="📋 Копировать телефон", command=self.copy_phone,
               bg="#9C27B0", fg="white", font=("Arial", 10), padx=10).pack(side=LEFT, padx=5)
        
        # Статус
        self.status_var = StringVar()
        status_bar = Label(self.root, textvariable=self.status_var, 
                          bd=1, relief=SUNKEN, anchor=W, font=("Arial", 9))
        status_bar.pack(side=BOTTOM, fill=X)
        
        # Показываем статус pandas
        if PANDAS_AVAILABLE:
            self.status_var.set("✅ Excel поддержка включена | Готов к работе")
        else:
            self.status_var.set("⚠️ Excel не доступен. Нажмите 'Установить библиотеки'")
    
    def import_excel(self):
        """Импорт Excel файла"""
        if not PANDAS_AVAILABLE:
            if messagebox.askyesno("Требуется установка", 
                                   "Для работы с Excel нужно установить библиотеки. Установить сейчас?"):
                install_pandas()
            return
        
        filepath = filedialog.askopenfilename(
            title="Выберите Excel файл",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Читаем Excel
            df = pd.read_excel(filepath)
            
            # Автоматически определяем колонки
            name_col = None
            phone_col = None
            region_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if any(word in col_lower for word in ['имя', 'name', 'фио', 'клиент']):
                    name_col = col
                if any(word in col_lower for word in ['телефон', 'phone', 'тел', 'моб', 'mobile']):
                    phone_col = col
                if any(word in col_lower for word in ['регион', 'region', 'город', 'city']):
                    region_col = col
            
            if name_col is None or phone_col is None:
                # Показываем диалог выбора колонок
                self.select_columns_dialog(df, filepath)
                return
            
            # Импортируем
            imported = 0
            updated = 0
            
            for _, row in df.iterrows():
                name = str(row[name_col]) if pd.notna(row[name_col]) else ""
                phone = str(row[phone_col]) if pd.notna(row[phone_col]) else ""
                region = str(row[region_col]) if region_col and pd.notna(row[region_col]) else ""
                
                if name and phone and name != 'nan' and phone != 'nan':
                    # Проверка на дубликат
                    exists = False
                    for contact in self.contacts:
                        if contact.get('phone') == phone:
                            exists = True
                            # Обновляем имя если оно короче
                            if len(contact.get('name', '')) < len(name):
                                contact['name'] = name
                            if region and not contact.get('region'):
                                contact['region'] = region
                            updated += 1
                            break
                    
                    if not exists:
                        self.contacts.append({
                            'name': name,
                            'phone': phone,
                            'region': region,
                            'date': datetime.now().strftime("%d.%m.%Y %H:%M")
                        })
                        imported += 1
            
            self.save_contacts()
            self.refresh_list()
            
            messagebox.showinfo("Успех", 
                f"Импорт завершён!\n\n"
                f"➕ Новых: {imported}\n"
                f"🔄 Обновлено: {updated}\n"
                f"📊 Всего в базе: {len(self.contacts)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{str(e)}")
    
    def select_columns_dialog(self, df, filepath):
        """Диалог выбора колонок вручную"""
        dialog = Toplevel(self.root)
        dialog.title("Выбор колонок")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        Label(dialog, text=f"Файл: {os.path.basename(filepath)}", 
              font=("Arial", 10, "bold")).pack(pady=10)
        
        Label(dialog, text="Выберите колонку с ИМЕНЕМ:", font=("Arial", 10)).pack(pady=5)
        name_var = StringVar()
        name_combo = ttk.Combobox(dialog, textvariable=name_var, values=list(df.columns), width=30)
        name_combo.pack(pady=5)
        
        Label(dialog, text="Выберите колонку с ТЕЛЕФОНОМ:", font=("Arial", 10)).pack(pady=5)
        phone_var = StringVar()
        phone_combo = ttk.Combobox(dialog, textvariable=phone_var, values=list(df.columns), width=30)
        phone_combo.pack(pady=5)
        
        Label(dialog, text="Выберите колонку с РЕГИОНОМ (необязательно):", font=("Arial", 10)).pack(pady=5)
        region_var = StringVar()
        region_combo = ttk.Combobox(dialog, textvariable=region_var, values=[""] + list(df.columns), width=30)
        region_combo.pack(pady=5)
        
        def import_with_columns():
            name_col = name_var.get()
            phone_col = phone_var.get()
            region_col = region_var.get() if region_var.get() else None
            
            if not name_col or not phone_col:
                messagebox.showwarning("Внимание", "Выберите обе обязательные колонки")
                return
            
            imported = 0
            for _, row in df.iterrows():
                name = str(row[name_col]) if pd.notna(row[name_col]) else ""
                phone = str(row[phone_col]) if pd.notna(row[phone_col]) else ""
                region = str(row[region_col]) if region_col and pd.notna(row[region_col]) else ""
                
                if name and phone and name != 'nan' and phone != 'nan':
                    exists = False
                    for contact in self.contacts:
                        if contact.get('phone') == phone:
                            exists = True
                            break
                    
                    if not exists:
                        self.contacts.append({
                            'name': name,
                            'phone': phone,
                            'region': region,
                            'date': datetime.now().strftime("%d.%m.%Y %H:%M")
                        })
                        imported += 1
            
            self.save_contacts()
            self.refresh_list()
            dialog.destroy()
            messagebox.showinfo("Успех", f"Импортировано {imported} контактов")
        
        Button(dialog, text="Импортировать", command=import_with_columns,
               bg="#4CAF50", fg="white", font=("Arial", 10), padx=20).pack(pady=20)
    
    def export_menu(self):
        """Меню экспорта"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("JSON files", "*.json")
            ]
        )
        
        if not filepath:
            return
        
        try:
            if filepath.endswith('.xlsx') and PANDAS_AVAILABLE:
                df = pd.DataFrame(self.contacts)
                df.to_excel(filepath, index=False)
            elif filepath.endswith('.csv'):
                import csv
                with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                    if self.contacts:
                        writer = csv.DictWriter(f, fieldnames=self.contacts[0].keys())
                        writer.writeheader()
                        writer.writerows(self.contacts)
            elif filepath.endswith('.json'):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("Успех", f"Экспортировано в {filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def add_contact(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        region = self.region_entry.get().strip()
        
        if not name or not phone:
            messagebox.showwarning("Внимание", "Заполните имя и телефон")
            return
        
        # Проверка дубликата
        for contact in self.contacts:
            if contact['phone'] == phone:
                if messagebox.askyesno("Дубликат", f"Номер {phone} уже есть. Обновить имя?"):
                    contact['name'] = name
                    if region:
                        contact['region'] = region
                    self.save_contacts()
                    self.refresh_list()
                return
        
        self.contacts.append({
            'name': name,
            'phone': phone,
            'region': region,
            'date': datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        
        self.save_contacts()
        self.name_entry.delete(0, END)
        self.phone_entry.delete(0, END)
        self.region_entry.delete(0, END)
        self.refresh_list()
        messagebox.showinfo("Успех", "Контакт добавлен")
    
    def edit_contact(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите контакт")
            return
        
        values = self.tree.item(selected[0])['values']
        old_name, old_phone, old_region, old_date = values
        
        dialog = Toplevel(self.root)
        dialog.title("Редактирование")
        dialog.geometry("300x250")
        
        Label(dialog, text="Имя:").pack(pady=5)
        name_entry = Entry(dialog, width=30)
        name_entry.insert(0, old_name)
        name_entry.pack()
        
        Label(dialog, text="Телефон:").pack(pady=5)
        phone_entry = Entry(dialog, width=30)
        phone_entry.insert(0, old_phone)
        phone_entry.pack()
        
        Label(dialog, text="Регион:").pack(pady=5)
        region_entry = Entry(dialog, width=30)
        region_entry.insert(0, old_region)
        region_entry.pack()
        
        def save():
            for contact in self.contacts:
                if contact['phone'] == old_phone:
                    contact['name'] = name_entry.get()
                    contact['phone'] = phone_entry.get()
                    contact['region'] = region_entry.get()
                    break
            
            self.save_contacts()
            self.refresh_list()
            dialog.destroy()
            messagebox.showinfo("Успех", "Контакт обновлён")
        
        Button(dialog, text="Сохранить", command=save, bg="#4CAF50", fg="white").pack(pady=10)
    
    def delete_contact(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите контакт")
            return
        
        name, phone, _, _ = self.tree.item(selected[0])['values']
        
        if messagebox.askyesno("Удаление", f"Удалить {name} ({phone})?"):
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
        messagebox.showinfo("Скопировано", f"Номер {phone} скопирован")
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        search = self.search_var.get().lower()
        filtered = self.contacts
        
        if search:
            filtered = [c for c in self.contacts 
                       if search in c.get('name', '').lower() or 
                          search in c.get('phone', '').lower() or
                          search in c.get('region', '').lower()]
        
        for contact in filtered:
            self.tree.insert("", END, values=(
                contact.get('name', ''),
                contact.get('phone', ''),
                contact.get('region', ''),
                contact.get('date', '')
            ))
        
        self.status_var.set(f"📊 Всего: {len(filtered)} из {len(self.contacts)} контактов")

# Запуск
if __name__ == "__main__":
    app = ContactsApp()