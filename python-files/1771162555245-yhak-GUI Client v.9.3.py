
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import socket
import threading
import queue
import datetime
import hashlib
import os
import time
from playsound import playsound

# --- НАСТРОЙКИ ---
SERVER_HOST = '127.0.0.1' 
SERVER_PORT = 55555
SOUND_FILE = 'notification.mp3'
SOUND_INTERVAL = 15
ADMIN_NAME = "Админ"
ADMIN_COLOR_GUI = "#00ffff"

last_sound_time = 0
sound_lock = threading.Lock()
INITIAL_SOUND_EXISTS = os.path.exists(SOUND_FILE)

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        self.base_title = "Python Chat Client"
        master.title(self.base_title)
        master.geometry("950x650")

        self.client_socket = None
        self.is_connected = False
        self.nickname = ""
        self.my_nick_color = "#FFFFFF"
        self._sound_functional = INITIAL_SOUND_EXISTS

        self.message_queue = queue.Queue()
        self.outgoing_queue = queue.Queue()

        # --- ГЛАВНЫЙ КОНТЕЙНЕР ДЛЯ ПРАВОЙ ПАНЕЛИ ---
        self.sidebar = tk.Frame(master, width=220, bg='#d0d0d0')
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        # 1. Список пользователей (Сверху в сайдбаре)
        tk.Label(self.sidebar, text="В СЕТИ:", bg='#d0d0d0', font=('Arial', 10, 'bold')).pack(pady=(10, 0))
        self.users_listbox = tk.Listbox(self.sidebar, bg='#f0f0f0', font=('Arial', 10))
        self.users_listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # 2. Контейнер для кнопок (Снизу в сайдбаре)
        self.controls_frame = tk.Frame(self.sidebar, bg='#d0d0d0')
        self.controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)

        self.status_label = tk.Label(self.controls_frame, text="Disconnected", bg='#ffaaaa', font=('Arial', 9, 'bold'))
        self.status_label.pack(pady=5, fill=tk.X)

        self.conn_btn = tk.Button(self.controls_frame, text="Подключиться", command=self.connect_to_server, bg='#aaffaa')
        self.conn_btn.pack(pady=2, fill=tk.X)

        self.disconn_btn = tk.Button(self.controls_frame, text="Отключиться", command=self.disconnect, state=tk.DISABLED)
        self.disconn_btn.pack(pady=2, fill=tk.X)

        self.sound_enabled_var = tk.BooleanVar(value=INITIAL_SOUND_EXISTS)
        self.sound_chk = tk.Checkbutton(self.controls_frame, text="Звук", variable=self.sound_enabled_var, bg='#d0d0d0')
        self.sound_chk.pack(pady=5)

        # --- ЦЕНТРАЛЬНАЯ ЧАСТЬ ---
        self.input_frame = tk.Frame(master)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        self.message_entry = tk.Entry(self.input_frame, font=('Arial', 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.message_entry.bind("<Return>", lambda e: self.enqueue_message())
        self.send_btn = tk.Button(self.input_frame, text="Отправить", command=self.enqueue_message, width=15, bg='#00ff00')
        self.send_btn.pack(side=tk.RIGHT, padx=5)

        self.chat_history = scrolledtext.ScrolledText(master, state='disabled', wrap='word', font=('Arial', 11), bg='#ffffff')
        self.chat_history.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Тэги
        self.chat_history.tag_configure("system", foreground="orange", font=("Arial", 11, "bold"))
        self.chat_history.tag_configure("admin_nick", foreground=ADMIN_COLOR_GUI, font=("Arial", 11, "bold"))
        self.chat_history.tag_configure("self_nick", font=("Arial", 11, "bold"))
        self.chat_history.tag_configure("other_nick", foreground="lightblue", font=("Arial", 11, "bold"))

        self.master.after(100, self.poll_messages)

    def play_sound_alert(self):
        global last_sound_time
        if not self._sound_functional or not self.sound_enabled_var.get(): return
        now = time.time()
        with sound_lock:
            if now - last_sound_time >= SOUND_INTERVAL:
                try:
                    playsound(SOUND_FILE)
                    last_sound_time = now
                except: self._sound_functional = False

    def append_message(self, message):
        # Обработка обновления списка пользователей из системных сообщений
        if "[СИСТЕМА]" in message:
            if "вошел в чат!" in message:
                nick = message.split("]: ")[1].split(" вошел")[0]
                if nick not in self.users_listbox.get(0, tk.END):
                    self.users_listbox.insert(tk.END, nick)
            elif "покинул чат." in message:
                nick = message.split("]: ")[1].split(" покинул")[0]
                try:
                    idx = self.users_listbox.get(0, tk.END).index(nick)
                    self.users_listbox.delete(idx)
                except: pass

        self.chat_history.config(state='normal')
        if message.startswith("[СИСТЕМА]"):
            self.chat_history.insert(tk.END, message + "\n", "system")
        else:
            time_end = message.find("] ")
            if time_end != -1:
                self.chat_history.insert(tk.END, message[:time_end+2])
                rest = message[time_end+2:]
                nick_sep = rest.find(":")
                if nick_sep != -1:
                    nick = rest[:nick_sep]
                    msg_text = rest[nick_sep:]
                    if nick == self.nickname:
                        self.chat_history.tag_configure("self_nick", foreground=self.my_nick_color)
                        self.chat_history.insert(tk.END, nick, "self_nick")
                    elif nick == ADMIN_NAME:
                        self.chat_history.insert(tk.END, nick, "admin_nick")
                    else:
                        self.chat_history.insert(tk.END, nick, "other_nick")
                    self.chat_history.insert(tk.END, msg_text + "\n")
                else: self.chat_history.insert(tk.END, rest + "\n")
            else: self.chat_history.insert(tk.END, message + "\n")

        self.chat_history.yview(tk.END)
        self.chat_history.config(state='disabled')
        
        if self.is_connected and f"{self.nickname}:" not in message and "[СИСТЕМА]: Вы" not in message:
            threading.Thread(target=self.play_sound_alert, daemon=True).start()

    def connect_to_server(self):
        nick = simpledialog.askstring("Login", "Ник:")
        if not nick: return
        pwd = simpledialog.askstring("Login", "Пароль:", show='*')
        if not pwd: return

        pwd_hash = hashlib.sha256(pwd.strip().encode()).hexdigest()

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            self.client_socket.send(f"{nick.strip()}:{pwd_hash}".encode('utf-8'))

            resp = self.client_socket.recv(1024).decode('utf-8')
            if resp.startswith("AUTH_SUCCESS"):
                self.client_socket.settimeout(None)
                _, self.nickname, self.my_nick_color = resp.split(':')
                self.is_connected = True
                
                # Обновляем заголовок и UI
                self.master.title(f"{self.base_title} - Аккаунт: {self.nickname}")
                self.status_label.config(text=f"Connected: {self.nickname}", bg='#aaffaa')
                self.conn_btn.config(state=tk.DISABLED)
                self.disconn_btn.config(state=tk.NORMAL)
                self.append_message(f"[СИСТЕМА]: Вы вошли как {self.nickname}")
                
                # Добавляем себя в список
                self.users_listbox.delete(0, tk.END)
                self.users_listbox.insert(tk.END, self.nickname)

                threading.Thread(target=self.receive_messages, daemon=True).start()
                threading.Thread(target=self.send_messages, daemon=True).start()
            else:
                messagebox.showerror("Ошибка", "Отказ в авторизации")
                self.client_socket.close()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Нет связи: {e}")

    def disconnect(self):
        self.is_connected = False
        if self.client_socket: self.client_socket.close()
        self.master.title(self.base_title)
        self.status_label.config(text="Disconnected", bg='#ffaaaa')
        self.conn_btn.config(state=tk.NORMAL)
        self.disconn_btn.config(state=tk.DISABLED)
        self.users_listbox.delete(0, tk.END)
        self.append_message("[СИСТЕМА]: Соединение разорвано.")

    def receive_messages(self):
        while self.is_connected:
            try:
                msg = self.client_socket.recv(1024).decode('utf-8')
                if not msg: break
                
                # Специальная обработка списка пользователей
                if msg.startswith("USER_LIST:"):
                    users = msg.split(":", 1)[1].split(",")
                    for u in users:
                        if u and u not in self.users_listbox.get(0, tk.END):
                            self.users_listbox.insert(tk.END, u)
                else:
                    self.message_queue.put(msg)
            except: break
        self.disconnect()

    def send_messages(self):
        while self.is_connected:
            try:
                msg = self.outgoing_queue.get(timeout=1)
                self.client_socket.send(msg.encode('utf-8'))
            except queue.Empty: continue
            except: break

    def enqueue_message(self):
        text = self.message_entry.get().strip()
        if text and self.is_connected:
            ts = datetime.datetime.now().strftime('%H:%M:%S')
            self.outgoing_queue.put(f"[{ts}] {self.nickname}: {text}")
            self.message_entry.delete(0, tk.END)

    def poll_messages(self):
        while not self.message_queue.empty():
            self.append_message(self.message_queue.get())
        self.master.after(100, self.poll_messages)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()
