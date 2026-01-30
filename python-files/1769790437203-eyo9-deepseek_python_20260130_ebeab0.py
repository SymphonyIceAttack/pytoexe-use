"""
===========================================
МЕССЕНДЖЕР PRO - DESKTOP APPLICATION
===========================================

Инструкция по установке и запуску:

1. Установите Python 3.8 или новее: https://www.python.org/downloads/

2. Установите библиотеку PyQt5:
   pip install PyQt5

3. Сохраните этот файл как: messenger_app.py

4. Запустите:
   python messenger_app.py

5. Для создания EXE файла:
   pip install pyinstaller
   pyinstaller --onefile --windowed --name "MessengerPro" messenger_app.py
   
   EXE файл появится в папке dist/

===========================================
"""

import sys
import json
import random
import string
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QTextEdit, QListWidget, QListWidgetItem, QStackedWidget,
                             QDialog, QMessageBox, QScrollArea, QFrame, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon


class Database:
    """Улучшенная база данных с защитой от конфликтов"""
    
    def __init__(self, user_id=None):
        # Создаем папку для данных, если её нет
        if not os.path.exists('messenger_data'):
            os.makedirs('messenger_data')
        
        self.users_file = 'messenger_data/messenger_users.json'
        self.messages_file = 'messenger_data/messenger_messages.json'
        self.contacts_file = 'messenger_data/messenger_contacts.json'
        self.activity_file = 'messenger_data/messenger_activity.json'
        self.user_id = user_id
        
        # Инициализация файлов, если они не существуют
        self.init_files()
    
    def init_files(self):
        files = [
            (self.users_file, {}),
            (self.messages_file, {}),
            (self.contacts_file, {}),
            (self.activity_file, {})
        ]
        
        for file_path, default_data in files:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def load(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save(self, filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения в {filename}: {e}")
            return False
    
    def get_users(self):
        return self.load(self.users_file)
    
    def save_users(self, users):
        return self.save(self.users_file, users)
    
    def get_messages(self):
        return self.load(self.messages_file)
    
    def save_messages(self, messages):
        return self.save(self.messages_file, messages)
    
    def get_contacts(self, user_id=None):
        user_id = user_id or self.user_id
        contacts = self.load(self.contacts_file)
        return contacts.get(user_id, [])
    
    def save_contacts(self, user_id, contact_list):
        contacts = self.load(self.contacts_file)
        contacts[user_id] = contact_list
        return self.save(self.contacts_file, contacts)
    
    def add_contact_mutual(self, user_id, contact_id):
        """Взаимное добавление контактов"""
        # Добавляем контакт к текущему пользователю
        user_contacts = self.get_contacts(user_id)
        if contact_id not in user_contacts:
            user_contacts.append(contact_id)
            self.save_contacts(user_id, user_contacts)
        
        # Добавляем текущего пользователя к контакту
        contact_contacts = self.get_contacts(contact_id)
        if user_id not in contact_contacts:
            contact_contacts.append(user_id)
            self.save_contacts(contact_id, contact_contacts)
        
        return True
    
    def get_activity(self):
        return self.load(self.activity_file)
    
    def save_activity(self, activity):
        return self.save(self.activity_file, activity)
    
    def update_user_activity(self, user_id):
        activity = self.get_activity()
        activity[user_id] = datetime.now().timestamp()
        return self.save_activity(activity)
    
    def is_user_online(self, user_id):
        activity = self.get_activity()
        if user_id not in activity:
            return False
        last_seen = activity[user_id]
        return (datetime.now().timestamp() - last_seen) < 30


class LoginWindow(QWidget):
    """Окно входа и регистрации"""
    
    login_success = pyqtSignal(str)
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Мессенджер Pro - Вход')
        self.setFixedSize(400, 500)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Заголовок
        title = QLabel('💬 Мессенджер Pro')
        title.setFont(QFont('Arial', 24, QFont.Bold))
        title.setStyleSheet('color: white;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(30)
        
        # Форма в белом контейнере
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 15px;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
            QPushButton {
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #667eea;
            }
        """)
        form_widget.setFixedWidth(350)
        
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # Поля входа
        self.login_id_input = QLineEdit()
        self.login_id_input.setPlaceholderText('ID пользователя')
        form_layout.addWidget(self.login_id_input)
        
        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText('Пароль')
        self.login_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.login_password_input)
        
        login_btn = QPushButton('Войти')
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)
        
        form_layout.addSpacing(20)
        
        # Разделитель
        separator = QLabel('или')
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet('color: #666; font-size: 12px;')
        form_layout.addWidget(separator)
        
        form_layout.addSpacing(10)
        
        # Поля регистрации
        self.register_name_input = QLineEdit()
        self.register_name_input.setPlaceholderText('Ваше имя')
        form_layout.addWidget(self.register_name_input)
        
        self.register_password_input = QLineEdit()
        self.register_password_input.setPlaceholderText('Придумайте пароль')
        self.register_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.register_password_input)
        
        register_btn = QPushButton('Зарегистрироваться')
        register_btn.clicked.connect(self.register)
        form_layout.addWidget(register_btn)
        
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
    
    def generate_id(self):
        return 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    
    def register(self):
        name = self.register_name_input.text().strip()
        password = self.register_password_input.text()
        
        if not name or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля!')
            return
        
        if len(password) < 4:
            QMessageBox.warning(self, 'Ошибка', 'Пароль должен быть минимум 4 символа!')
            return
        
        user_id = self.generate_id()
        users = self.db.get_users()
        
        # Проверяем, что имя не занято
        for uid, user_data in users.items():
            if user_data['name'].lower() == name.lower():
                QMessageBox.warning(self, 'Ошибка', 'Это имя уже занято!')
                return
        
        users[user_id] = {
            'id': user_id,
            'name': name,
            'password': password,
            'created': datetime.now().timestamp()
        }
        
        if self.db.save_users(users):
            # Создаем пустой список контактов для нового пользователя
            self.db.save_contacts(user_id, [])
            
            QMessageBox.information(self, 'Успех!', 
                f'✓ Регистрация успешна!\n\nВаш ID: {user_id}\nИмя: {name}\n\nСкопируйте ID для входа!')
            
            self.login_id_input.setText(user_id)
            self.login_password_input.setText(password)
            self.register_name_input.clear()
            self.register_password_input.clear()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось сохранить данные!')
    
    def login(self):
        user_id = self.login_id_input.text().strip()
        password = self.login_password_input.text()
        
        if not user_id or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля!')
            return
        
        users = self.db.get_users()
        
        if user_id not in users:
            QMessageBox.warning(self, 'Ошибка', 'Пользователь не найден!')
            return
        
        if users[user_id]['password'] != password:
            QMessageBox.warning(self, 'Ошибка', 'Неверный пароль!')
            return
        
        # Обновляем активность пользователя
        self.db.update_user_activity(user_id)
        
        self.login_success.emit(user_id)


class MessengerWindow(QMainWindow):
    """Главное окно мессенджера"""
    
    def __init__(self, db, user_id):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.selected_contact = None
        self.unread_messages = {}  # Хранит количество непрочитанных сообщений
        
        self.init_ui()
        
        # Таймер для обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)
        
        self.update_activity()
        self.load_contacts()
        
        # Устанавливаем заголовок
        self.update_window_title()
    
    def init_ui(self):
        self.update_window_title()
        self.showMaximized()  # Открыть на весь экран
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Боковая панель
        self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Область чата
        self.create_chat_area()
        main_layout.addWidget(self.chat_area)
        
        central_widget.setLayout(main_layout)
        
        self.apply_styles()
    
    def update_window_title(self):
        users = self.db.get_users()
        user = users.get(self.user_id, {'name': 'Пользователь'})
        unread_total = sum(self.unread_messages.values())
        
        if unread_total > 0:
            self.setWindowTitle(f'💬 Мессенджер Pro - {user["name"]} ({unread_total})')
        else:
            self.setWindowTitle(f'💬 Мессенджер Pro - {user["name"]}')
    
    def create_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(400)
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Заголовок
        header = QWidget()
        header.setObjectName('sidebar_header')
        header_layout = QVBoxLayout()
        
        users = self.db.get_users()
        user = users.get(self.user_id, {'name': 'Пользователь'})
        
        user_info = QLabel(f"👤 {user['name']}\nID: {self.user_id[:10]}...")
        user_info.setStyleSheet('color: white; font-size: 14px; padding: 10px;')
        header_layout.addWidget(user_info)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ По ID')
        add_btn.clicked.connect(self.add_by_id)
        actions_layout.addWidget(add_btn)
        
        random_btn = QPushButton('🎲 Случайный')
        random_btn.clicked.connect(self.add_random)
        actions_layout.addWidget(random_btn)
        
        refresh_btn = QPushButton('🔄 Обновить')
        refresh_btn.clicked.connect(self.refresh_data)
        actions_layout.addWidget(refresh_btn)
        
        header_layout.addLayout(actions_layout)
        
        logout_btn = QPushButton('Выйти')
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        
        header.setLayout(header_layout)
        sidebar_layout.addWidget(header)
        
        # Поиск
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 Поиск...')
        self.search_input.textChanged.connect(self.load_contacts)
        sidebar_layout.addWidget(self.search_input)
        
        # Список контактов
        self.contacts_list = QListWidget()
        self.contacts_list.itemClicked.connect(self.select_contact)
        sidebar_layout.addWidget(self.contacts_list)
        
        self.sidebar.setLayout(sidebar_layout)
    
    def create_chat_area(self):
        self.chat_area = QWidget()
        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Заголовок чата
        self.chat_header = QLabel('Выберите чат')
        self.chat_header.setObjectName('chat_header')
        self.chat_header.setFixedHeight(60)
        chat_layout.addWidget(self.chat_header)
        
        # Область сообщений
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        chat_layout.addWidget(self.messages_area)
        
        # Ввод сообщения
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('Введите сообщение...')
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton('➤')
        send_btn.setFixedWidth(50)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        chat_layout.addLayout(input_layout)
        
        self.chat_area.setLayout(chat_layout)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: white;
            }
            #sidebar_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            #sidebar_header QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            #sidebar_header QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                margin: 10px;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
            QListWidget {
                background: #f8f9fa;
                border: none;
                padding: 5px;
            }
            QListWidget::item {
                background: white;
                padding: 15px;
                margin: 2px;
                border-radius: 8px;
            }
            QListWidget::item:hover {
                background: #f0f0ff;
            }
            QListWidget::item:selected {
                background: #667eea;
                color: white;
            }
            #chat_header {
                background: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QTextEdit {
                background: #f8f9fa;
                border: none;
                padding: 10px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #667eea;
            }
        """)
    
    def update_activity(self):
        self.db.update_user_activity(self.user_id)
    
    def is_online(self, user_id):
        return self.db.is_user_online(user_id)
    
    def load_contacts(self):
        try:
            self.contacts_list.clear()
            
            contacts = self.db.get_contacts(self.user_id)
            users = self.db.get_users()
            search = self.search_input.text().lower()
            
            if not contacts:
                item = QListWidgetItem('👥 Нет контактов\nДобавьте друзей!')
                item.setFlags(Qt.NoItemFlags)
                self.contacts_list.addItem(item)
                return
            
            for contact_id in contacts:
                if contact_id not in users:
                    continue
                
                user = users[contact_id]
                if search and search not in user['name'].lower():
                    continue
                
                online = '🟢' if self.is_online(contact_id) else '⚫'
                
                # Подсчет непрочитанных сообщений
                unread_count = self.unread_messages.get(contact_id, 0)
                unread_badge = f" ({unread_count})" if unread_count > 0 else ""
                
                item = QListWidgetItem(f"{online} {user['name']}{unread_badge}")
                item.setData(Qt.UserRole, contact_id)
                self.contacts_list.addItem(item)
        except Exception as e:
            print(f"Ошибка загрузки контактов: {e}")
    
    def select_contact(self, item):
        contact_id = item.data(Qt.UserRole)
        if not contact_id:
            return
        
        self.selected_contact = contact_id
        users = self.db.get_users()
        user = users.get(contact_id, {'name': 'Пользователь'})
        
        online = '🟢 В сети' if self.is_online(contact_id) else '⚫ Не в сети'
        self.chat_header.setText(f"{user['name']} - {online}")
        
        self.load_messages()
        self.mark_as_read()
        self.message_input.setFocus()
        
        # Сбрасываем счетчик непрочитанных
        if contact_id in self.unread_messages:
            self.unread_messages[contact_id] = 0
            self.load_contacts()
    
    def load_messages(self):
        if not self.selected_contact:
            return
        
        messages = self.db.get_messages()
        chat_key = '_'.join(sorted([self.user_id, self.selected_contact]))
        chat_messages = messages.get(chat_key, [])
        
        users = self.db.get_users()
        
        html = '<div style="padding: 10px;">'
        
        if not chat_messages:
            html += '<div style="text-align: center; color: #666; padding: 40px;">'
            html += '✉️ Нет сообщений<br><small>Напишите что-нибудь!</small>'
            html += '</div>'
        
        for msg in chat_messages:
            is_own = msg['from'] == self.user_id
            sender = users.get(msg['from'], {'name': 'Пользователь'})['name']
            time_str = datetime.fromtimestamp(msg['time']).strftime('%H:%M %d.%m')
            
            align = 'right' if is_own else 'left'
            bg_color = '#667eea' if is_own else 'white'
            text_color = 'white' if is_own else 'black'
            
            html += f'''
            <div style="text-align: {align}; margin: 10px 0;">
                <div style="display: inline-block; max-width: 60%; background: {bg_color}; 
                    color: {text_color}; padding: 10px 15px; border-radius: 15px;">
                    {msg['text']}
                    <div style="font-size: 10px; opacity: 0.7; margin-top: 5px;">
                        {time_str} • {sender}
                    </div>
                </div>
            </div>
            '''
        
        html += '</div>'
        
        self.messages_area.setHtml(html)
        
        # Прокрутка вниз
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def mark_as_read(self):
        if not self.selected_contact:
            return
        
        messages = self.db.get_messages()
        chat_key = '_'.join(sorted([self.user_id, self.selected_contact]))
        
        if chat_key in messages:
            for msg in messages[chat_key]:
                if msg['from'] == self.selected_contact:
                    msg['read'] = True
            self.db.save_messages(messages)
    
    def send_message(self):
        if not self.selected_contact:
            QMessageBox.warning(self, 'Ошибка', 'Выберите контакт для отправки сообщения!')
            return
        
        text = self.message_input.text().strip()
        if not text:
            return
        
        # Проверяем, есть ли контакт в списке
        contacts = self.db.get_contacts(self.user_id)
        if self.selected_contact not in contacts:
            # Добавляем взаимно
            self.db.add_contact_mutual(self.user_id, self.selected_contact)
            QMessageBox.information(self, 'Инфо', 
                f'Контакт добавлен! Теперь вы оба видите друг друга в списке.')
        
        messages = self.db.get_messages()
        chat_key = '_'.join(sorted([self.user_id, self.selected_contact]))
        
        if chat_key not in messages:
            messages[chat_key] = []
        
        messages[chat_key].append({
            'from': self.user_id,
            'to': self.selected_contact,
            'text': text,
            'time': datetime.now().timestamp(),
            'read': False
        })
        
        if self.db.save_messages(messages):
            self.message_input.clear()
            self.load_messages()
            self.load_contacts()  # Обновляем список контактов
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось отправить сообщение!')
    
    def add_by_id(self):
        contact_id, ok = QInputDialog.getText(self, 'Добавить контакт', 
            'Введите ID пользователя:')
        
        if not ok or not contact_id:
            return
        
        contact_id = contact_id.strip()
        users = self.db.get_users()
        
        if contact_id not in users:
            QMessageBox.warning(self, 'Ошибка', 'Пользователь не найден!')
            return
        
        if contact_id == self.user_id:
            QMessageBox.warning(self, 'Ошибка', 'Нельзя добавить самого себя!')
            return
        
        contacts = self.db.get_contacts(self.user_id)
        
        if contact_id in contacts:
            QMessageBox.information(self, 'Инфо', 'Контакт уже добавлен!')
            return
        
        # Добавляем взаимно
        if self.db.add_contact_mutual(self.user_id, contact_id):
            QMessageBox.information(self, 'Успех', 
                f"✓ {users[contact_id]['name']} добавлен в контакты!\n\nТеперь вы оба видите друг друга.")
            
            self.load_contacts()
            
            # Предлагаем написать сообщение
            reply = QMessageBox.question(self, 'Написать сообщение?',
                f'Хотите написать сообщение {users[contact_id]["name"]}?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # Ищем контакт в списке
                for i in range(self.contacts_list.count()):
                    item = self.contacts_list.item(i)
                    if item.data(Qt.UserRole) == contact_id:
                        self.contacts_list.setCurrentItem(item)
                        self.select_contact(item)
                        self.message_input.setFocus()
                        break
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось добавить контакт!')
    
    def add_random(self):
        users = self.db.get_users()
        contacts = self.db.get_contacts(self.user_id)
        
        # Исключаем себя и уже добавленных
        available = [uid for uid in users.keys() 
                    if uid != self.user_id and uid not in contacts]
        
        if not available:
            QMessageBox.information(self, 'Инфо', 
                'Нет доступных пользователей для добавления!')
            return
        
        random_id = random.choice(available)
        
        # Добавляем взаимно
        if self.db.add_contact_mutual(self.user_id, random_id):
            QMessageBox.information(self, 'Успех', 
                f"✓ {users[random_id]['name']} добавлен случайно!\n\nТеперь вы оба видите друг друга.")
            
            self.load_contacts()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось добавить контакт!')
    
    def check_new_messages(self):
        """Проверяет новые сообщения от всех пользователей"""
        messages = self.db.get_messages()
        users = self.db.get_users()
        
        # Сбрасываем счетчики
        new_unread = {}
        
        for chat_key, chat_messages in messages.items():
            if self.user_id in chat_key:
                # Получаем ID собеседника
                user_ids = chat_key.split('_')
                other_id = user_ids[0] if user_ids[1] == self.user_id else user_ids[1]
                
                # Считаем непрочитанные сообщения
                unread_count = sum(1 for msg in chat_messages 
                                 if msg['from'] == other_id and not msg.get('read', False))
                
                if unread_count > 0:
                    new_unread[other_id] = unread_count
        
        # Обновляем счетчики
        self.unread_messages = new_unread
        
        # Проверяем, есть ли новые сообщения от пользователей не в контактах
        contacts = self.db.get_contacts(self.user_id)
        for other_id in new_unread.keys():
            if other_id not in contacts:
                # Автоматически добавляем в контакты
                self.db.add_contact_mutual(self.user_id, other_id)
                user_name = users.get(other_id, {'name': 'Пользователь'})['name']
        
        return len(new_unread) > 0
    
    def refresh_data(self):
        try:
            self.update_activity()
            
            # Проверяем новые сообщения
            has_new_messages = self.check_new_messages()
            
            if self.selected_contact:
                self.load_messages()
            
            # Обновляем список контактов если есть изменения
            self.load_contacts()
            
            # Обновляем заголовок окна
            self.update_window_title()
                
        except Exception as e:
            print(f"Ошибка обновления данных: {e}")
    
    def logout(self):
        reply = QMessageBox.question(self, 'Выход', 
            'Вы уверены, что хотите выйти?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.timer.stop()
            self.close()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('Messenger Pro')
    
    # Создаем базу данных
    db = Database()
    
    login_window = LoginWindow(db)
    
    def on_login_success(user_id):
        try:
            login_window.hide()
            messenger_window = MessengerWindow(db, user_id)
            messenger_window.show()
            
            # При закрытии окна мессенджера показываем окно входа
            def on_messenger_closed():
                login_window.show()
            
            messenger_window.destroyed.connect(on_messenger_closed)
            
        except Exception as e:
            QMessageBox.critical(None, 'Ошибка', f'Ошибка при входе:\n{str(e)}')
            login_window.show()
    
    login_window.login_success.connect(on_login_success)
    login_window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()