# Улучшенный мессенджер с защищёнными каналами и приватными чатами

## messenger_secure_gui.py - Полнофункциональное приложение

```python
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import socket
import threading
import json
import base64
import hashlib
from datetime import datetime
import os

# ============= КЛАССЫ БЕЗОПАСНОСТИ =============

class SecureChannel:
    """Защищённый канал с паролем и шифрованием"""
    def __init__(self, name: str, password: str = None, encrypted: bool = True):
        self.name = name
        self.password_hash = hashlib.sha256(password.encode()).hexdigest() if password else None
        self.encrypted = encrypted
        self.members = []
        self.messages = []
        self.owner = None
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def verify_password(self, password: str) -> bool:
        if not self.password_hash:
            return True
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
    
    def add_member(self, username: str) -> bool:
        if username not in self.members:
            self.members.append(username)
            return True
        return False
    
    def remove_member(self, username: str):
        if username in self.members:
            self.members.remove(username)
    
    def add_message(self, sender: str, text: str, encrypted_text: str = None):
        message = {
            'sender': sender,
            'text': text,
            'encrypted_text': encrypted_text,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        self.messages.append(message)
    
    def is_member(self, username: str) -> bool:
        return username in self.members
    
    def get_messages(self, limit: int = 50):
        return self.messages[-limit:]


class PrivateChat:
    """Приватный чат между двумя пользователями"""
    def __init__(self, user1: str, user2: str):
        self.participants = sorted([user1, user2])
        self.messages = []
        self.chat_id = f"{self.participants[0]}-{self.participants[1]}"
    
    def add_message(self, sender: str, text: str):
        if sender not in self.participants:
            return False
        message = {
            'sender': sender,
            'text': text,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        self.messages.append(message)
        return True
    
    def is_participant(self, username: str) -> bool:
        return username in self.participants
    
    def get_messages(self, limit: int = 50):
        return self.messages[-limit:]


class MessageEncryption:
    """Шифрование сообщений"""
    @staticmethod
    def encrypt(text: str, key: str = "default") -> str:
        try:
            key_bytes = key.encode()
            text_bytes = text.encode()
            key_repeated = (key_bytes * (len(text_bytes) // len(key_bytes) + 1))[:len(text_bytes)]
            encrypted = bytes(a ^ b for a, b in zip(text_bytes, key_repeated))
            return base64.b64encode(encrypted).decode()
        except:
            return text
    
    @staticmethod
    def decrypt(encrypted: str, key: str = "default") -> str:
        try:
            key_bytes = key.encode()
            encrypted_bytes = base64.b64decode(encrypted.encode())
            key_repeated = (key_bytes * (len(encrypted_bytes) // len(key_bytes) + 1))[:len(encrypted_bytes)]
            decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_repeated))
            return decrypted.decode()
        except:
            return encrypted


# ============= ОСНОВНОЕ GUI ПРИЛОЖЕНИЕ =============

class SecureMessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Защищённый Мессенджер")
        self.root.geometry("900x600")
        
        # Параметры
        self.host = self.get_local_ip()
        self.port = 5555
        self.username = ""
        self.current_channel = None
        self.current_private_chat = None
        self.running = False
        
        # Хранилище данных
        self.channels = {}
        self.private_chats = {}
        self.server_socket = None
        self.encryption_key = "default"
        
        self.create_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def create_ui(self):
        """Создание интерфейса с табами"""
        # Топ-панель
        info_frame = tk.Frame(self.root, bg="#f0f0f0", height=50)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="IP: " + self.host, bg="#f0f0f0", 
                font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(info_frame, text="Не подключен", 
                                    bg="#f0f0f0", fg="red", font=("Arial", 9))
        self.status_label.pack(side=tk.RIGHT, padx=5)
        
        # Кнопки управления
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Button(button_frame, text="Запустить сервер", 
                 command=self.start_server, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Новый канал", 
                 command=self.create_channel_dialog, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Приватный чат", 
                 command=self.start_private_chat_dialog, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Очистить", 
                 command=self.clear_messages).pack(side=tk.LEFT, padx=2)
        
        # Основной контейнер с табами
        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - список каналов и чатов
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        
        tk.Label(left_frame, text="Каналы", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.channels_listbox = tk.Listbox(left_frame, height=10, width=25)
        self.channels_listbox.pack(fill=tk.BOTH, expand=True)
        self.channels_listbox.bind('<<ListboxSelect>>', self.on_channel_select)
        
        tk.Label(left_frame, text="Приватные чаты", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.private_chats_listbox = tk.Listbox(left_frame, height=8, width=25)
        self.private_chats_listbox.pack(fill=tk.BOTH, expand=True)
        self.private_chats_listbox.bind('<<ListboxSelect>>', self.on_private_chat_select)
        
        # Правая панель - сообщения
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.current_title = tk.Label(right_frame, text="Выберите канал", 
                                     font=("Arial", 11, "bold"), fg="#2196F3")
        self.current_title.pack(anchor=tk.W)
        
        self.message_display = scrolledtext.ScrolledText(right_frame, height=18, width=60, 
                                                        state=tk.DISABLED, wrap=tk.WORD)
        self.message_display.pack(fill=tk.BOTH, expand=True)
        
        # Нижняя панель - ввод
        input_frame = tk.Frame(self.root)
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text="Имя:").pack(side=tk.LEFT)
        self.username_entry = tk.Entry(input_frame, width=15)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Установить", 
                 command=self.set_username).pack(side=tk.LEFT, padx=2)
        
        tk.Label(input_frame, text="Сообщение:").pack(side=tk.LEFT, padx=(20, 0))
        self.input_field = tk.Entry(input_frame)
        self.input_field.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        tk.Button(input_frame, text="Отправить", 
                 command=self.send_message, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
    
    def set_username(self):
        """Установить имя пользователя"""
        name = self.username_entry.get().strip()
        if name:
            self.username = name
            self.username_entry.delete(0, tk.END)
            self.add_system_message(f"[СИСТЕМА] Ваше имя: {self.username}")
    
    def start_server(self):
        """Запустить сервер"""
        if not self.username:
            messagebox.showwarning("Ошибка", "Установите имя перед запуском сервера")
            return
        
        if self.running:
            messagebox.showwarning("Предупреждение", "Сервер уже запущен")
            return
        
        self.running = True
        self.status_label.config(text="Сервер работает", fg="green")
        self.add_system_message(f"[СЕРВЕР] Запущен на {self.host}:{self.port}")
        
        server_thread = threading.Thread(target=self.server_loop, daemon=True)
        server_thread.start()
    
    def server_loop(self):
        """Основной цикл сервера"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, addr = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                except socket.timeout:
                    continue
                except:
                    break
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def handle_client(self, client_socket, addr):
        """Обработка клиента"""
        try:
            self.add_system_message(f"[ПОДКЛЮЧЕНИЕ] {addr[0]}:{addr[1]}")
            
            while self.running:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                
                try:
                    message = json.loads(data)
                    channel = message.get('channel')
                    
                    if channel and channel in self.channels:
                        self.channels[channel].add_message(
                            message.get('sender'),
                            message.get('text'),
                            message.get('encrypted_text')
                        )
                        self.refresh_display()
                    
                    client_socket.send("OK".encode())
                except:
                    pass
        finally:
            self.add_system_message(f"[ОТКЛЮЧЕНИЕ] {addr[0]}:{addr[1]}")
            client_socket.close()
    
    def create_channel_dialog(self):
        """Диалог создания канала"""
        if not self.username:
            messagebox.showwarning("Ошибка", "Установите имя пользователя")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Новый канал")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Имя канала:").pack(anchor=tk.W, padx=10, pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(padx=10, pady=5)
        
        tk.Label(dialog, text="Пароль (опционально):").pack(anchor=tk.W, padx=10, pady=5)
        password_entry = tk.Entry(dialog, width=30, show="*")
        password_entry.pack(padx=10, pady=5)
        
        encrypt_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dialog, text="Шифровать сообщения", variable=encrypt_var).pack(padx=10, pady=5)
        
        def create():
            name = name_entry.get().strip()
            password = password_entry.get() or None
            
            if not name:
                messagebox.showwarning("Ошибка", "Введите имя канала")
                return
            
            if name in self.channels:
                messagebox.showwarning("Ошибка", "Канал уже существует")
                return
            
            channel = SecureChannel(name, password, encrypt_var.get())
            channel.owner = self.username
            channel.add_member(self.username)
            self.channels[name] = channel
            
            self.update_channel_list()
            self.add_system_message(f"[КАНАЛ] '{name}' создан")
            dialog.destroy()
        
        tk.Button(dialog, text="Создать", command=create, bg="#4CAF50", 
                 fg="white", width=20).pack(pady=10)
    
    def start_private_chat_dialog(self):
        """Диалог создания приватного чата"""
        if not self.username:
            messagebox.showwarning("Ошибка", "Установите имя пользователя")
            return
        
        username = simpledialog.askstring("Приватный чат", "Имя пользователя:")
        if not username or username == self.username:
            return
        
        chat_id = f"{min(self.username, username)}-{max(self.username, username)}"
        
        if chat_id not in self.private_chats:
            self.private_chats[chat_id] = PrivateChat(self.username, username)
            self.add_system_message(f"[ЧАТ] Приватный чат с {username}")
        
        self.update_private_chat_list()
        self.current_private_chat = chat_id
        self.on_private_chat_select(None)
    
    def on_channel_select(self, event):
        """Выбран канал"""
        selection = self.channels_listbox.curselection()
        if selection:
            channel_name = self.channels_listbox.get(selection[0])
            channel = self.channels[channel_name]
            
            # Проверка доступа
            if not channel.is_member(self.username):
                password = simpledialog.askstring("Защищённый канал", 
                                                  "Введите пароль канала:")
                if not channel.verify_password(password or ""):
                    messagebox.showerror("Ошибка", "Неверный пароль")
                    return
            
            channel.add_member(self.username)
            self.current_channel = channel_name
            self.current_private_chat = None
            self.load_channel_messages()
    
    def on_private_chat_select(self, event):
        """Выбран приватный чат"""
        selection = self.private_chats_listbox.curselection()
        if selection:
            chat_id = self.private_chats_listbox.get(selection[0])
            self.current_private_chat = chat_id
            self.current_channel = None
            self.load_private_messages()
    
    def load_channel_messages(self):
        """Загрузить сообщения канала"""
        if not self.current_channel:
            return
        
        channel = self.channels[self.current_channel]
        self.current_title.config(text=f"📢 {self.current_channel} "
                                      f"({len(channel.members)} участников)")
        
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete(1.0, tk.END)
        
        for msg in channel.get_messages(50):
            text = msg['text']
            if msg.get('encrypted_text'):
                text = MessageEncryption.decrypt(msg['encrypted_text'], self.encryption_key)
            
            line = f"{msg['sender']} [{msg['timestamp']}]: {text}\n"
            self.message_display.insert(tk.END, line)
        
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def load_private_messages(self):
        """Загрузить сообщения приватного чата"""
        if not self.current_private_chat:
            return
        
        chat = self.private_chats[self.current_private_chat]
        other_user = [u for u in chat.participants if u != self.username][0]
        
        self.current_title.config(text=f"💬 {other_user}")
        
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete(1.0, tk.END)
        
        for msg in chat.get_messages(50):
            line = f"{msg['sender']}: {msg['text']}\n"
            self.message_display.insert(tk.END, line)
        
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def send_message(self):
        """Отправить сообщение"""
        if not self.username:
            messagebox.showwarning("Ошибка", "Установите имя пользователя")
            return
        
        text = self.input_field.get().strip()
        if not text:
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if self.current_channel:
            channel = self.channels[self.current_channel]
            encrypted_text = None
            display_text = text
            
            if channel.encrypted:
                encrypted_text = MessageEncryption.encrypt(text, self.encryption_key)
                display_text = "[ЗАШИФРОВАНО]"
            
            channel.add_message(self.username, display_text, encrypted_text)
            self.load_channel_messages()
        
        elif self.current_private_chat:
            chat = self.private_chats[self.current_private_chat]
            chat.add_message(self.username, text)
            self.load_private_messages()
        
        else:
            messagebox.showwarning("Ошибка", "Выберите канал или чат")
            return
        
        self.input_field.delete(0, tk.END)
    
    def update_channel_list(self):
        """Обновить список каналов"""
        self.channels_listbox.delete(0, tk.END)
        for name in self.channels:
            self.channels_listbox.insert(tk.END, name)
    
    def update_private_chat_list(self):
        """Обновить список приватных чатов"""
        self.private_chats_listbox.delete(0, tk.END)
        for chat_id, chat in self.private_chats.items():
            other_user = [u for u in chat.participants if u != self.username][0]
            self.private_chats_listbox.insert(tk.END, other_user)
    
    def refresh_display(self):
        """Обновить текущий дисплей"""
        if self.current_channel:
            self.load_channel_messages()
        elif self.current_private_chat:
            self.load_private_messages()
    
    def add_system_message(self, text):
        """Добавить системное сообщение"""
        self.root.after(0, lambda: self._add_message(text))
    
    def _add_message(self, text):
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, text + "\n")
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def clear_messages(self):
        """Очистить сообщения"""
        self.message_display.config(state=tk.NORMAL)
        self.message_display.delete(1.0, tk.END)
        self.message_display.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Закрытие приложения"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecureMessengerApp(root)
    root.mainloop()
```

---

## ОСНОВНЫЕ ВОЗМОЖНОСТИ

✅ **Защищённые каналы:**
- Пароль доступа (SHA256)
- Шифрование сообщений (XOR + Base64)
- Управление участниками
- История сообщений

✅ **Приватные чаты:**
- Один-на-один общение
- Автоматическое создание
- Полная история

✅ **Интерфейс:**
- Список доступных каналов слева
- Список приватных чатов
- История сообщений справа
- Быстрая отправка (Enter)

✅ **Безопасность:**
- Проверка доступа
- Хеширование паролей
- Опциональное шифрование
- Отделение открытых/закрытых каналов

---

## ИСПОЛЬЗОВАНИЕ

1. Запустить приложение
2. Установить имя пользователя
3. Создать канал или приватный чат
4. Отправлять сообщения через интерфейс
