# client.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, font
from datetime import datetime
import sys

class HDMIMessenger:
    def __init__(self):
        self.client = None
        self.nickname = None
        self.running = True
        
        # Настройки подключения
        self.host = '127.0.0.1'
        self.port = 7879
        
        self.setup_gui()
        
    def setup_gui(self):
        self.window = tk.Tk()
        self.window.title("HDMI Messenger")
        self.window.geometry("800x600")
        self.window.configure(bg='#1a1a1a')
        
        # Устанавливаем иконку (можно заменить на свою)
        try:
            self.window.iconbitmap('hdmi_icon.ico')
        except:
            pass
        
        # Центрируем окно
        self.center_window(800, 600)
        
        # Стили
        self.colors = {
            'bg': '#1a1a1a',
            'secondary': '#2a2a2a',
            'accent': '#ff6b4a',  # Оранжево-красный цвет HDMI
            'text': '#ffffff',
            'text_secondary': '#b0b0b0',
            'input_bg': '#333333',
            'system_msg': '#808080'
        }
        
        # Настройка шрифтов
        self.title_font = font.Font(family='Segoe UI', size=16, weight='bold')
        self.text_font = font.Font(family='Segoe UI', size=11)
        self.system_font = font.Font(family='Segoe UI', size=10, slant='italic')
        
        # Создаем виджеты
        self.create_header()
        self.create_chat_area()
        self.create_input_area()
        self.create_status_bar()
        
        # Привязываем обработчик закрытия окна
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Показываем диалог входа
        self.show_login_dialog()
        
    def center_window(self, width, height):
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_header(self):
        header_frame = tk.Frame(self.window, bg=self.colors['accent'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Заголовок
        title = tk.Label(
            header_frame,
            text="HDMI MESSENGER",
            font=self.title_font,
            bg=self.colors['accent'],
            fg='#ffffff'
        )
        title.pack(side=tk.LEFT, padx=20, pady=15)
        
        # Статус подключения
        self.connection_status = tk.Label(
            header_frame,
            text="● Не в сети",
            font=self.system_font,
            bg=self.colors['accent'],
            fg='#ffffff'
        )
        self.connection_status.pack(side=tk.RIGHT, padx=20, pady=15)
        
    def create_chat_area(self):
        # Основная область чата
        chat_frame = tk.Frame(self.window, bg=self.colors['bg'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 10))
        
        # Поле для отображения сообщений
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=self.text_font,
            bg=self.colors['secondary'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=self.colors['accent'],
            highlightbackground=self.colors['input_bg']
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Настройка тегов для разных типов сообщений
        self.chat_display.tag_config('system', foreground=self.colors['system_msg'])
        self.chat_display.tag_config('user_message', foreground=self.colors['text'])
        self.chat_display.tag_config('my_message', foreground=self.colors['accent'])
        self.chat_display.tag_config('timestamp', foreground=self.colors['system_msg'], font=self.system_font)
        
        # Отключаем редактирование
        self.chat_display.config(state=tk.DISABLED)
        
    def create_input_area(self):
        input_frame = tk.Frame(self.window, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Поле ввода сообщения
        self.message_input = tk.Text(
            input_frame,
            height=3,
            font=self.text_font,
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=self.colors['accent'],
            highlightbackground=self.colors['input_bg'],
            wrap=tk.WORD
        )
        self.message_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Привязываем Enter для отправки
        self.message_input.bind('<Return>', self.send_message_event)
        self.message_input.bind('<Shift-Return>', lambda e: None)  # Разрешаем Shift+Enter для новой строки
        
        # Кнопка отправки
        send_button = tk.Button(
            input_frame,
            text="Отправить ⏎",
            font=self.text_font,
            bg=self.colors['accent'],
            fg='#ffffff',
            borderwidth=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.send_message
        )
        send_button.pack(side=tk.RIGHT)
        
        # Эффект при наведении на кнопку
        send_button.bind('<Enter>', lambda e: send_button.configure(bg='#ff8a6a'))
        send_button.bind('<Leave>', lambda e: send_button.configure(bg=self.colors['accent']))
        
    def create_status_bar(self):
        status_frame = tk.Frame(self.window, bg=self.colors['secondary'], height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="Готов к подключению",
            font=self.system_font,
            bg=self.colors['secondary'],
            fg=self.colors['text_secondary']
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
    def show_login_dialog(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Вход в HDMI Messenger")
        dialog.geometry("350x200")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Центрируем диалог
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 350) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f'+{x}+{y}')
        
        # Заголовок
        title = tk.Label(
            dialog,
            text="Вход в чат",
            font=self.title_font,
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        title.pack(pady=20)
        
        # Поле для ника
        nickname_frame = tk.Frame(dialog, bg=self.colors['bg'])
        nickname_frame.pack(pady=10)
        
        nickname_label = tk.Label(
            nickname_frame,
            text="Ваш никнейм:",
            font=self.text_font,
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        nickname_label.pack()
        
        nickname_entry = tk.Entry(
            nickname_frame,
            font=self.text_font,
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=self.colors['accent'],
            width=30
        )
        nickname_entry.pack(pady=5)
        nickname_entry.focus()
        
        # Кнопка входа
        def login():
            nickname = nickname_entry.get().strip()
            if nickname:
                dialog.destroy()
                self.connect_to_server(nickname)
            else:
                messagebox.showwarning("Ошибка", "Введите никнейм!")
        
        nickname_entry.bind('<Return>', lambda e: login())
        
        login_button = tk.Button(
            dialog,
            text="Войти в чат",
            font=self.text_font,
            bg=self.colors['accent'],
            fg='#ffffff',
            borderwidth=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=login
        )
        login_button.pack(pady=20)
        
    def connect_to_server(self, nickname):
        self.nickname = nickname
        
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
            
            # Обновляем статус
            self.connection_status.config(text="● В сети", fg='#90ee90')
            self.status_label.config(text=f"Подключен как {nickname}")
            
            # Запускаем поток для получения сообщений
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.add_system_message(f"Добро пожаловать в чат, {nickname}!")
            
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к серверу: {e}")
            self.window.quit()
            
    def receive_messages(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                
                if message == "NICK":
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    # Отображаем сообщение
                    self.window.after(0, self.display_message, message)
                    
            except Exception as e:
                if self.running:
                    self.window.after(0, self.handle_disconnect)
                break
                
    def send_message(self, event=None):
        message = self.message_input.get("1.0", tk.END).strip()
        
        if message:
            try:
                full_message = f"{self.nickname}: {message}"
                self.client.send(full_message.encode('utf-8'))
                
                # Очищаем поле ввода
                self.message_input.delete("1.0", tk.END)
                
                # Возвращаем фокус на поле ввода
                self.message_input.focus()
                
            except Exception as e:
                self.add_system_message("Ошибка отправки сообщения")
                
    def send_message_event(self, event):
        if not event.state & 0x1:  # Проверяем, не зажат ли Shift
            self.send_message()
            return 'break'  # Предотвращаем добавление новой строки
            
    def display_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        
        # Добавляем временную метку
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        
        # Определяем тип сообщения
        if message.startswith(f"{self.nickname}:"):
            # Моё сообщение
            self.chat_display.insert(tk.END, message + '\n', 'my_message')
        elif "присоединился к чату" in message or "покинул чат" in message:
            # Системное сообщение
            self.chat_display.insert(tk.END, message + '\n', 'system')
        else:
            # Сообщение другого пользователя
            self.chat_display.insert(tk.END, message + '\n', 'user_message')
            
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def add_system_message(self, message):
        self.chat_display.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.chat_display.insert(tk.END, message + '\n', 'system')
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def handle_disconnect(self):
        self.add_system_message("Отключен от сервера")
        self.connection_status.config(text="● Не в сети", fg='#ff6b4a')
        self.status_label.config(text="Соединение потеряно")
        self.running = False
        
    def on_closing(self):
        self.running = False
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.window.quit()
        self.window.destroy()
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = HDMIMessenger()
    app.run()