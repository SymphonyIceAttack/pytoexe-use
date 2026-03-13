
# ============================================
# АРИНА - AI ПОМОЩНИК С ГРАФИЧЕСКИМ ИНТЕРФЕЙСОМ
# ИСПРАВЛЕННАЯ ВЕРСИЯ
# ============================================

import os
import sys
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import google.generativeai as genai

class ArinaGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("🤖 Арина - AI Помощник")
        self.window.geometry("900x600")

        # Переменные
        self.api_key = None
        self.model = None
        self.reminders = []
        self.notes = []
        self.data_file = "arina_data.json"

        # Сначала создаем интерфейс
        self.create_widgets()

        # Потом загружаем данные
        self.load_data()

        # Показываем окно входа
        self.show_login()

    def create_widgets(self):
        """Создание интерфейса"""
        # Статус бар (создаем ДО всего)
        self.status_bar = ttk.Label(self.window, text="Загрузка...", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Главное меню
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Сохранить данные", command=self.save_data)
        file_menu.add_command(label="Загрузить данные", command=self.load_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.window.quit)

        # Меню Помощь
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Как получить API ключ", command=self.show_api_help)

        # Основной контейнер с вкладками
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Вкладка Чат
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="💬 Чат")
        self.setup_chat_tab()

        # Вкладка Напоминания
        self.reminder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reminder_frame, text="⏰ Напоминания")
        self.setup_reminder_tab()

        # Вкладка Заметки
        self.notes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.notes_frame, text="📚 Заметки")
        self.setup_notes_tab()

        # Вкладка Настройки
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="⚙️ Настройки")
        self.setup_settings_tab()

        self.update_status("Интерфейс загружен")

    def setup_chat_tab(self):
        """Настройка вкладки чата"""
        # Область для сообщений
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Arial", 10)
        )
        self.chat_display.pack(fill='both', expand=True, padx=5, pady=5)

        # Нижняя панель с вводом
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill='x', padx=5, pady=5)

        self.chat_input = ttk.Entry(input_frame, font=("Arial", 10))
        self.chat_input.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', lambda e: self.send_message())

        self.send_btn = ttk.Button(
            input_frame,
            text="Отправить",
            command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT)

    def setup_reminder_tab(self):
        """Настройка вкладки напоминаний"""
        # Список напоминаний
        self.reminder_listbox = tk.Listbox(
            self.reminder_frame,
            height=15,
            font=("Arial", 10)
        )
        self.reminder_listbox.pack(fill='both', expand=True, padx=5, pady=5)

        # Кнопки управления
        btn_frame = ttk.Frame(self.reminder_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(
            btn_frame,
            text="➕ Добавить",
            command=self.add_reminder_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="❌ Удалить",
            command=self.delete_reminder
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="🔄 Обновить",
            command=self.update_reminder_list
        ).pack(side=tk.LEFT, padx=2)

    def setup_notes_tab(self):
        """Настройка вкладки заметок"""
        # Левая панель - список заметок
        left_frame = ttk.Frame(self.notes_frame)
        left_frame.pack(side=tk.LEFT, fill='y', padx=(5, 2), pady=5)

        ttk.Label(left_frame, text="Заметки:", font=("Arial", 10, "bold")).pack()

        self.notes_listbox = tk.Listbox(
            left_frame,
            height=20,
            width=30,
            font=("Arial", 10)
        )
        self.notes_listbox.pack(fill='y', expand=True, pady=5)
        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)

        # Правая панель - просмотр/редактирование
        right_frame = ttk.Frame(self.notes_frame)
        right_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=(2, 5), pady=5)

        ttk.Label(right_frame, text="Содержание:", font=("Arial", 10, "bold")).pack()

        self.note_content = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            height=20,
            font=("Arial", 10)
        )
        self.note_content.pack(fill='both', expand=True, pady=5)

        # Кнопки для заметок
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill='x', pady=5)

        ttk.Button(
            btn_frame,
            text="➕ Новая",
            command=self.add_note_dialog
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="💾 Сохранить",
            command=self.save_note
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="❌ Удалить",
            command=self.delete_note
        ).pack(side=tk.LEFT, padx=2)

    def setup_settings_tab(self):
        """Настройка вкладки настроек"""
        # API ключ
        api_frame = ttk.LabelFrame(self.settings_frame, text="Настройки API", padding=10)
        api_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(api_frame, text="API ключ:").grid(row=0, column=0, sticky='w', pady=5)

        self.api_key_var = tk.StringVar(value=self.api_key if self.api_key else "")
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(
            api_frame,
            text="Проверить ключ",
            command=self.check_api_key
        ).grid(row=0, column=2, padx=5, pady=5)

        # Информация
        info_frame = ttk.LabelFrame(self.settings_frame, text="Информация", padding=10)
        info_frame.pack(fill='x', padx=10, pady=10)

        info_text = """
        🤖 Арина - ваш персональный AI помощник

        Возможности:
        • 💬 Общение с AI (требуется API ключ)
        • ⏰ Управление напоминаниями
        • 📚 Заметки и конспекты
        • 💾 Автоматическое сохранение

        Для получения API ключа:
        1. Перейдите на https://makersuite.google.com/app/apikey
        2. Войдите в аккаунт Google
        3. Нажмите "Create API Key"
        4. Скопируйте ключ и вставьте выше
        """

        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack()

    def show_login(self):
        """Показывает окно входа"""
        login_window = tk.Toplevel(self.window)
        login_window.title("Вход в Арина AI")
        login_window.geometry("500x300")
        login_window.transient(self.window)
        login_window.grab_set()

        ttk.Label(
            login_window,
            text="🤖 Добро пожаловать в Арина AI!",
            font=("Arial", 14, "bold")
        ).pack(pady=20)

        ttk.Label(
            login_window,
            text="Для работы необходим API ключ Google AI Studio",
            font=("Arial", 10)
        ).pack(pady=10)

        key_link = ttk.Label(
            login_window,
            text="https://makersuite.google.com/app/apikey",
            foreground="blue",
            cursor="hand2"
        )
        key_link.pack(pady=5)
        key_link.bind("<Button-1>", lambda e: os.system("start https://makersuite.google.com/app/apikey"))

        ttk.Label(login_window, text="Введите API ключ:").pack(pady=10)

        api_entry = ttk.Entry(login_window, width=50, show="*")
        api_entry.pack(pady=5)

        def save_key():
            key = api_entry.get().strip()
            if key:
                self.api_key = key
                self.init_model()
                login_window.destroy()
                self.update_status("API ключ установлен")
            else:
                messagebox.showerror("Ошибка", "Введите API ключ")

        ttk.Button(login_window, text="Подключиться", command=save_key).pack(pady=20)

    def init_model(self):
        """Инициализация модели AI"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.update_status("✅ AI модель готова к работе")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось инициализировать AI: {e}")

    def send_message(self):
        """Отправка сообщения в чат"""
        if not self.model:
            messagebox.showwarning("Внимание", "Сначала введите API ключ в настройках")
            return

        message = self.chat_input.get().strip()
        if not message:
            return

        # Отображаем сообщение пользователя
        self.chat_display.insert(tk.END, f"
👤 Вы: {message}
", "user")
        self.chat_display.see(tk.END)
        self.chat_input.delete(0, tk.END)

        # Отправляем в отдельном потоке
        def get_response():
            try:
                response = self.model.generate_content(message)
                self.window.after(0, self.display_response, response.text)
            except Exception as e:
                self.window.after(0, self.display_response, f"Ошибка: {e}")

        threading.Thread(target=get_response, daemon=True).start()

    def display_response(self, text):
        """Отображение ответа AI"""
        self.chat_display.insert(tk.END, f"
🤖 Арина: {text}
", "ai")
        self.chat_display.see(tk.END)

    def add_reminder_dialog(self):
        """Диалог добавления напоминания"""
        text = simpledialog.askstring("Новое напоминание", "Что нужно сделать?")
        if not text:
            return

        time = simpledialog.askstring("Новое напоминание", "Когда? (например: завтра 15:00)")
        if not time:
            return

        self.reminders.append({
            'text': text,
            'time': time,
            'created': datetime.now().strftime("%d.%m.%Y %H:%M")
        })
        self.update_reminder_list()
        self.save_data()

    def delete_reminder(self):
        """Удаление напоминания"""
        selection = self.reminder_listbox.curselection()
        if selection:
            if messagebox.askyesno("Подтверждение", "Удалить напоминание?"):
                del self.reminders[selection[0]]
                self.update_reminder_list()
                self.save_data()

    def update_reminder_list(self):
        """Обновление списка напоминаний"""
        self.reminder_listbox.delete(0, tk.END)
        for r in self.reminders:
            self.reminder_listbox.insert(tk.END, f"{r['text']} - {r['time']}")

    def add_note_dialog(self):
        """Диалог добавления заметки"""
        title = simpledialog.askstring("Новая заметка", "Заголовок:")
        if not title:
            return

        content = simpledialog.askstring("Новая заметка", "Содержание:")
        if not content:
            return

        self.notes.append({
            'title': title,
            'content': content,
            'date': datetime.now().strftime("%d.%m.%Y")
        })
        self.update_notes_list()
        self.save_data()

    def on_note_select(self, event):
        """Обработка выбора заметки"""
        selection = self.notes_listbox.curselection()
        if selection:
            note = self.notes[selection[0]]
            self.note_content.delete(1.0, tk.END)
            self.note_content.insert(1.0, note['content'])

    def save_note(self):
        """Сохранение текущей заметки"""
        selection = self.notes_listbox.curselection()
        if selection:
            content = self.note_content.get(1.0, tk.END).strip()
            self.notes[selection[0]]['content'] = content
            self.save_data()
            messagebox.showinfo("Успех", "Заметка сохранена")

    def delete_note(self):
        """Удаление заметки"""
        selection = self.notes_listbox.curselection()
        if selection:
            if messagebox.askyesno("Подтверждение", "Удалить заметку?"):
                del self.notes[selection[0]]
                self.update_notes_list()
                self.note_content.delete(1.0, tk.END)
                self.save_data()

    def update_notes_list(self):
        """Обновление списка заметок"""
        self.notes_listbox.delete(0, tk.END)
        for n in self.notes:
            self.notes_listbox.insert(tk.END, f"{n['title']} ({n['date']})")

    def check_api_key(self):
        """Проверка API ключа"""
        key = self.api_key_var.get().strip()
        if key:
            self.api_key = key
            self.init_model()

    def save_data(self):
        """Сохранение данных в файл"""
        try:
            data = {
                'reminders': self.reminders,
                'notes': self.notes
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.update_status("Данные сохранены")
        except Exception as e:
            self.update_status(f"Ошибка сохранения: {e}")

    def load_data(self):
        """Загрузка данных из файла"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.reminders = data.get('reminders', [])
                    self.notes = data.get('notes', [])
                self.update_status("Данные загружены")
                self.update_reminder_list()
                self.update_notes_list()
        except Exception as e:
            self.update_status(f"Ошибка загрузки: {e}")

    def update_status(self, text):
        """Обновление строки статуса"""
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=f"📌 {text}")

    def show_about(self):
        """О программе"""
        about_text = """
        🤖 Арина AI Помощник
        Версия 2.0

        Персональный AI ассистент
        с функциями чата, напоминаний и заметок

        Создано с любовью для Арины 💕
        """
        messagebox.showinfo("О программе", about_text)

    def show_api_help(self):
        """Помощь по API ключу"""
        help_text = """
        Как получить API ключ:

        1. Перейдите на https://makersuite.google.com/app/apikey
        2. Войдите в свой аккаунт Google
        3. Нажмите "Create API Key"
        4. Выберите или создайте проект
        5. Скопируйте полученный ключ

        Ключ выглядит как длинная строка букв и цифр
        """
        messagebox.showinfo("API ключ", help_text)

    def run(self):
        """Запуск приложения"""
        self.window.mainloop()

# Запуск приложения
if __name__ == "__main__":
    app = ArinaGUI()
    app.run()
