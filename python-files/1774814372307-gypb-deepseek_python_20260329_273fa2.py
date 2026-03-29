import socket
import threading
import tkinter as tk
from tkinter import messagebox

class TelegramStyleClient:
    def __init__(self):
        self.client_socket = None
        self.nickname = None
        self.running = True
        self.receiving_history = False

        self.window = tk.Tk()
        self.window.title("Telegram-like Chat")
        self.window.geometry("500x600")
        self.window.configure(bg='#17212b')
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Заголовок
        self.header = tk.Frame(self.window, bg='#2a6bb0', height=50)
        self.header_label = tk.Label(self.header, text="Чат", fg='white', bg='#2a6bb0',
                                     font=('Segoe UI', 14, 'bold'))
        self.header_label.pack(pady=10)

        # Область сообщений
        self.chat_frame = tk.Frame(self.window, bg='#17212b')
        self.chat_area = tk.Text(self.chat_frame, wrap=tk.WORD, state='disabled',
                                 bg='#17212b', fg='white', font=('Segoe UI', 10),
                                 borderwidth=0, highlightthickness=0)
        self.chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_area.config(yscrollcommand=scrollbar.set)

        # Стили
        self.chat_area.tag_configure('my_message', background='#2b5278',
                                      foreground='white', justify='right',
                                      font=('Segoe UI', 10), spacing3=5, lmargin1=50, rmargin=10)
        self.chat_area.tag_configure('other_message', background='#18222d',
                                      foreground='white', justify='left',
                                      font=('Segoe UI', 10), spacing3=5, lmargin1=10, rmargin=50)
        self.chat_area.tag_configure('system', background='#17212b',
                                      foreground='#6c7883', justify='center',
                                      font=('Segoe UI', 9, 'italic'))
        self.chat_area.tag_configure('private', background='#3e2a4b',
                                      foreground='#e0b0ff', justify='left',
                                      font=('Segoe UI', 10, 'italic'), spacing3=5)

        # Панель ввода
        self.input_frame = tk.Frame(self.window, bg='#17212b')
        self.msg_entry = tk.Entry(self.input_frame, bg='#242f3e', fg='white',
                                  font=('Segoe UI', 10), borderwidth=0, highlightthickness=0)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.msg_entry.bind('<Return>', lambda e: self.send_message())

        self.send_btn = tk.Button(self.input_frame, text="Отправить", bg='#2a6bb0',
                                  fg='white', font=('Segoe UI', 10), borderwidth=0,
                                  command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)

        # Форма входа
        self.login_frame = tk.Frame(self.window, bg='#17212b')
        self.login_frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(self.login_frame, text="Ваше имя:", bg='#17212b', fg='white',
                 font=('Segoe UI', 12)).pack(pady=10)
        self.nick_entry = tk.Entry(self.login_frame, bg='#242f3e', fg='white',
                                   font=('Segoe UI', 12), width=30)
        self.nick_entry.pack(pady=5)

        tk.Label(self.login_frame, text="IP сервера:", bg='#17212b', fg='white',
                 font=('Segoe UI', 12)).pack(pady=10)
        self.ip_entry = tk.Entry(self.login_frame, bg='#242f3e', fg='white',
                                 font=('Segoe UI', 12), width=30)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=5)

        tk.Label(self.login_frame, text="Порт:", bg='#17212b', fg='white',
                 font=('Segoe UI', 12)).pack(pady=10)
        self.port_entry = tk.Entry(self.login_frame, bg='#242f3e', fg='white',
                                   font=('Segoe UI', 12), width=30)
        self.port_entry.insert(0, "12345")
        self.port_entry.pack(pady=5)

        self.connect_btn = tk.Button(self.login_frame, text="Подключиться",
                                     bg='#2a6bb0', fg='white', font=('Segoe UI', 10),
                                     command=self.connect)
        self.connect_btn.pack(pady=20)

        self.header.pack_forget()
        self.chat_frame.pack_forget()
        self.input_frame.pack_forget()

    def connect(self):
        self.nickname = self.nick_entry.get().strip()
        if not self.nickname:
            messagebox.showerror("Ошибка", "Введите имя!")
            return

        host = self.ip_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Ошибка", "Порт должен быть числом!")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.client_socket.send(self.nickname.encode('utf-8'))

            self.login_frame.pack_forget()
            self.header.pack(fill=tk.X)
            self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.input_frame.pack(fill=tk.X, padx=10, pady=10)

            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            self.msg_entry.focus()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к {host}:{port}\n{str(e)}")
            if self.client_socket:
                self.client_socket.close()
                self.client_socket = None

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    self.window.after(0, self.display_message, "Соединение с сервером потеряно.")
                    self.window.after(0, self.disable_chat)
                    break
                lines = data.split('\n')
                for line in lines:
                    if line.strip():
                        self.window.after(0, self.process_incoming_line, line)
            except Exception as e:
                self.window.after(0, self.display_message, "Ошибка соединения.")
                self.window.after(0, self.disable_chat)
                break

    def process_incoming_line(self, line):
        if line == "=== ИСТОРИЯ ЧАТА ===":
            self.receiving_history = True
            self.display_message("--- Начало истории ---", 'system')
            return
        if line == "=== КОНЕЦ ИСТОРИИ ===":
            self.receiving_history = False
            self.display_message("--- Конец истории ---", 'system')
            return
        if self.receiving_history:
            self.display_message(line, 'system')
            return
        self.display_message(line)

    def display_message(self, raw_message, forced_tag=None):
        if forced_tag:
            self.chat_area.config(state='normal')
            self.chat_area.insert(tk.END, raw_message + "\n", forced_tag)
            self.chat_area.see(tk.END)
            self.chat_area.config(state='disabled')
            return

        if raw_message.startswith("Сервер:"):
            tag = 'system'
        elif raw_message.startswith("[Приватно от ") or raw_message.startswith("[Приватно для "):
            tag = 'private'
        elif raw_message.startswith("Вы:"):
            tag = 'my_message'
        elif ": " in raw_message:
            name, text = raw_message.split(": ", 1)
            if name == self.nickname:
                tag = 'my_message'
                raw_message = text
            else:
                tag = 'other_message'
        else:
            tag = 'system'

        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, raw_message + "\n", tag)
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def disable_chat(self):
        self.send_btn.config(state='disabled')
        self.msg_entry.config(state='disabled')

    def send_message(self):
        if not self.client_socket:
            return
        message = self.msg_entry.get().strip()
        if not message:
            return
        if message.startswith('/msg ') or message.startswith('/users'):
            try:
                self.client_socket.send(message.encode('utf-8'))
                self.msg_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось отправить: {e}")
            return
        self.display_message(f"Вы: {message}")
        try:
            self.client_socket.send(message.encode('utf-8'))
            self.msg_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить: {e}")

    def on_closing(self):
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.window.destroy()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    client = TelegramStyleClient()
    client.run()