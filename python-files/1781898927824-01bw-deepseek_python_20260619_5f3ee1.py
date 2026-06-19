import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkinter import font as tkfont
import pyperclip

class PasswordManager:
    """Класс для управления паролями с шифрованием"""
    
    def __init__(self, master_password):
        self.master_password = master_password
        self.key = self.generate_key(master_password)
        self.cipher = Fernet(self.key)
        self.data_file = "remote_access_data.enc"
        self.connections = []
        
    def generate_key(self, password):
        """Генерация ключа шифрования на основе мастер-пароля"""
        password_bytes = password.encode('utf-8')
        salt = b'salt_remote_access_2024'  # В реальном приложении используйте случайную соль
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def save_data(self):
        """Сохранение данных в зашифрованный файл"""
        try:
            json_data = json.dumps(self.connections, ensure_ascii=False)
            encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))
            
            with open(self.data_file, 'wb') as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False
    
    def load_data(self):
        """Загрузка и расшифровка данных"""
        try:
            if not os.path.exists(self.data_file):
                return True
                
            with open(self.data_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            self.connections = json.loads(decrypted_data.decode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False
    
    def add_connection(self, name, address, username, password, app_type, notes):
        """Добавление нового подключения"""
        connection = {
            'id': len(self.connections) + 1,
            'name': name,
            'address': address,
            'username': username,
            'password': password,
            'app_type': app_type,
            'notes': notes
        }
        self.connections.append(connection)
        return self.save_data()
    
    def delete_connection(self, index):
        """Удаление подключения"""
        if 0 <= index < len(self.connections):
            del self.connections[index]
            return self.save_data()
        return False
    
    def update_connection(self, index, name, address, username, password, app_type, notes):
        """Обновление подключения"""
        if 0 <= index < len(self.connections):
            self.connections[index] = {
                'id': index + 1,
                'name': name,
                'address': address,
                'username': username,
                'password': password,
                'app_type': app_type,
                'notes': notes
            }
            return self.save_data()
        return False
    
    def search_connections(self, query):
        """Поиск подключений"""
        query = query.lower()
        results = []
        for conn in self.connections:
            if (query in conn['name'].lower() or 
                query in conn['address'].lower() or
                query in conn['app_type'].lower()):
                results.append(conn)
        return results

class RemoteAccessApp:
    """Главное приложение"""
    
    def __init__(self, master_password):
        self.master_password = master_password
        self.manager = PasswordManager(master_password)
        self.current_view = "all"  # all, search
        self.search_results = []
        
        # Загрузка данных
        if not self.manager.load_data():
            messagebox.showerror("Ошибка", "Не удалось загрузить данные. Проверьте мастер-пароль.")
            return
        
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.window = tk.Tk()
        self.window.title("Менеджер удаленных доступов")
        self.window.geometry("1000x650")
        
        # Стили
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной контейнер
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_font = tkfont.Font(family="Arial", size=16, weight="bold")
        title_label = ttk.Label(main_frame, text="🔐 Менеджер удаленных доступов", font=title_font)
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky=tk.W)
        
        # Панель поиска
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        ttk.Button(search_frame, text="🔍 Найти", command=self.on_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(search_frame, text="🔄 Сбросить", command=self.reset_search).pack(side=tk.LEFT)
        
        # Панель кнопок действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="➕ Добавить", command=self.show_add_dialog).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="✏️ Редактировать", command=self.show_edit_dialog).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🗑️ Удалить", command=self.delete_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📋 Копировать пароль", command=self.copy_password).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📤 Экспорт CSV", command=self.export_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 Обновить", command=self.refresh_list).pack(side=tk.LEFT)
        
        # Таблица подключений
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Создание таблицы
        columns = ('ID', 'Название', 'Адрес', 'Приложение', 'Логин', 'Примечание')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Настройка заголовков
        self.tree.heading('ID', text='ID')
        self.tree.heading('Название', text='Название')
        self.tree.heading('Адрес', text='Адрес')
        self.tree.heading('Приложение', text='Приложение')
        self.tree.heading('Логин', text='Логин')
        self.tree.heading('Примечание', text='Примечание')
        
        # Настройка ширины колонок
        self.tree.column('ID', width=50, anchor=tk.CENTER)
        self.tree.column('Название', width=150)
        self.tree.column('Адрес', width=150)
        self.tree.column('Приложение', width=120)
        self.tree.column('Логин', width=130)
        self.tree.column('Примечание', width=300)
        
        # Скроллбары
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Размещение таблицы
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Настройка веса для таблицы
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Статусная строка
        self.status_label = ttk.Label(main_frame, text="Готово")
        self.status_label.grid(row=4, column=0, columnspan=4, sticky=tk.W)
        
        # Настройка основного окна
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Загрузка данных
        self.refresh_list()
        
        # Закрытие окна
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def refresh_list(self):
        """Обновление списка подключений"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Определение данных для отображения
        data_to_show = self.search_results if self.current_view == "search" else self.manager.connections
        
        # Добавление данных
        for conn in data_to_show:
            self.tree.insert('', tk.END, values=(
                conn['id'],
                conn['name'],
                conn['address'],
                conn['app_type'],
                conn['username'],
                conn['notes'][:50] + ('...' if len(conn['notes']) > 50 else '')
            ))
        
        # Обновление статуса
        count = len(data_to_show)
        self.status_label.config(text=f"Всего подключений: {count}")
    
    def on_search(self, event=None):
        """Поиск подключений"""
        query = self.search_var.get().strip()
        if query:
            self.search_results = self.manager.search_connections(query)
            self.current_view = "search"
            self.refresh_list()
        else:
            self.reset_search()
    
    def reset_search(self):
        """Сброс поиска"""
        self.search_var.set("")
        self.current_view = "all"
        self.search_results = []
        self.refresh_list()
    
    def get_selected_connection(self):
        """Получение выбранного подключения"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите подключение")
            return None
        
        # Получение индекса
        item = selected[0]
        index = self.tree.index(item)
        
        # Определение источника данных
        if self.current_view == "search":
            if index < len(self.search_results):
                conn = self.search_results[index]
                # Найти индекс в основном списке
                for i, c in enumerate(self.manager.connections):
                    if c['id'] == conn['id']:
                        return i, conn
            return None, None
        else:
            if index < len(self.manager.connections):
                return index, self.manager.connections[index]
            return None, None
    
    def show_add_dialog(self):
        """Показать диалог добавления"""
        dialog = AddEditDialog(self.window, self)
        self.window.wait_window(dialog.dialog)
        self.refresh_list()
    
    def show_edit_dialog(self):
        """Показать диалог редактирования"""
        result = self.get_selected_connection()
        if result and result[0] is not None:
            index, conn = result
            dialog = AddEditDialog(self.window, self, conn, index)
            self.window.wait_window(dialog.dialog)
            self.refresh_list()
    
    def delete_selected(self):
        """Удаление выбранного подключения"""
        result = self.get_selected_connection()
        if result and result[0] is not None:
            index, conn = result
            if messagebox.askyesno("Подтверждение", f"Удалить подключение '{conn['name']}'?"):
                if self.manager.delete_connection(index):
                    self.refresh_list()
                    messagebox.showinfo("Успех", "Подключение удалено")
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить подключение")
    
    def copy_password(self):
        """Копирование пароля в буфер обмена"""
        result = self.get_selected_connection()
        if result and result[0] is not None:
            _, conn = result
            pyperclip.copy(conn['password'])
            messagebox.showinfo("Успех", "Пароль скопирован в буфер обмена")
    
    def export_csv(self):
        """Экспорт данных в CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Сохранить как CSV"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['ID', 'Название', 'Адрес', 'Приложение', 'Логин', 'Пароль', 'Примечание']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for conn in self.manager.connections:
                        writer.writerow({
                            'ID': conn['id'],
                            'Название': conn['name'],
                            'Адрес': conn['address'],
                            'Приложение': conn['app_type'],
                            'Логин': conn['username'],
                            'Пароль': conn['password'],
                            'Примечание': conn['notes']
                        })
                
                messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {e}")
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.window.destroy()
    
    def run(self):
        """Запуск приложения"""
        self.window.mainloop()

class AddEditDialog:
    """Диалог добавления/редактирования подключения"""
    
    def __init__(self, parent, app, connection=None, index=None):
        self.parent = parent
        self.app = app
        self.connection = connection
        self.index = index
        self.dialog = tk.Toplevel(parent)
        
        if connection:
            self.dialog.title("Редактирование подключения")
        else:
            self.dialog.title("Добавление подключения")
        
        self.dialog.geometry("500x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        
        if connection:
            self.load_data()
    
    def setup_ui(self):
        """Настройка UI диалога"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поля ввода
        fields = [
            ("Название *:", "name"),
            ("Адрес *:", "address"),
            ("Логин:", "username"),
            ("Пароль:", "password"),
            ("Тип приложения:", "app_type")
        ]
        
        self.entries = {}
        
        for i, (label, key) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            
            if key == "app_type":
                self.entries[key] = ttk.Combobox(main_frame, values=["AnyDesk", "RDP", "TeamViewer", "VNC", "Ассистент", "Другое"])
                self.entries[key].grid(row=i, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
            else:
                self.entries[key] = ttk.Entry(main_frame, width=40)
                self.entries[key].grid(row=i, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
            
            # Установка фокуса
            if key == "name":
                self.entries[key].focus()
        
        # Примечание
        ttk.Label(main_frame, text="Примечание:").grid(row=len(fields), column=0, sticky=tk.W, pady=5)
        self.entries["notes"] = scrolledtext.ScrolledText(main_frame, height=6, width=40)
        self.entries["notes"].grid(row=len(fields), column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Настройка веса
        main_frame.columnconfigure(1, weight=1)
    
    def load_data(self):
        """Загрузка данных для редактирования"""
        self.entries["name"].insert(0, self.connection['name'])
        self.entries["address"].insert(0, self.connection['address'])
        self.entries["username"].insert(0, self.connection['username'])
        self.entries["password"].insert(0, self.connection['password'])
        self.entries["app_type"].set(self.connection['app_type'])
        self.entries["notes"].insert("1.0", self.connection['notes'])
    
    def save(self):
        """Сохранение данных"""
        # Получение данных
        name = self.entries["name"].get().strip()
        address = self.entries["address"].get().strip()
        username = self.entries["username"].get().strip()
        password = self.entries["password"].get().strip()
        app_type = self.entries["app_type"].get().strip()
        notes = self.entries["notes"].get("1.0", tk.END).strip()
        
        # Проверка обязательных полей
        if not name or not address:
            messagebox.showwarning("Предупреждение", "Название и адрес обязательны для заполнения")
            return
        
        if not app_type:
            app_type = "Другое"
        
        # Сохранение
        if self.connection is not None and self.index is not None:
            # Редактирование
            if self.app.manager.update_connection(self.index, name, address, username, password, app_type, notes):
                messagebox.showinfo("Успех", "Подключение обновлено")
                self.dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить подключение")
        else:
            # Добавление
            if self.app.manager.add_connection(name, address, username, password, app_type, notes):
                messagebox.showinfo("Успех", "Подключение добавлено")
                self.dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить подключение")

def start_app():
    """Запуск приложения с запросом мастер-пароля"""
    
    def verify_password():
        password = password_entry.get()
        if password:
            try:
                app = RemoteAccessApp(password)
                password_window.destroy()
                app.run()
            except Exception as e:
                messagebox.showerror("Ошибка", "Неверный мастер-пароль или повреждены данные")
        else:
            messagebox.showwarning("Предупреждение", "Введите мастер-пароль")
    
    # Окно ввода мастер-пароля
    password_window = tk.Tk()
    password_window.title("Вход в менеджер паролей")
    password_window.geometry("400x200")
    password_window.resizable(False, False)
    
    main_frame = ttk.Frame(password_window, padding="30")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(main_frame, text="🔐 Введите мастер-пароль", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    password_entry = ttk.Entry(main_frame, show="*", width=30)
    password_entry.pack(pady=10)
    password_entry.focus()
    password_entry.bind('<Return>', lambda e: verify_password())
    
    ttk.Button(main_frame, text="Войти", command=verify_password).pack(pady=10)
    
    # Информация
    info_frame = ttk.Frame(main_frame)
    info_frame.pack(pady=(10, 0))
    ttk.Label(info_frame, text="При первом запуске файл с паролями будет создан автоматически", 
              font=("Arial", 8), foreground="gray").pack()
    ttk.Label(info_frame, text="Внимание: пароль должен быть одинаковым при каждом входе!", 
              font=("Arial", 8), foreground="red").pack()
    
    password_window.mainloop()

if __name__ == "__main__":
    try:
        start_app()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")